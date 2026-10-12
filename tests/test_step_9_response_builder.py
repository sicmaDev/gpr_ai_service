"""
Tests unitaires pour le Step 9 : Contrats de Réponse & Validation Front React.

Ce fichier teste de manière exhaustive :
1. La sélection du type de graphique (select_chart_type).
2. La construction des visualisations Chart.js (format_chartjs_visualization : bar, line, pie, vide).
3. La formulation naturelle textuelle factuelle (formulate_natural_answer).
4. La construction du contrat ReportingQueryResponse (build_reporting_query_response).
5. L'exécution de bout en bout du pipeline Text-to-SQL (Fast-Path et Supervisé).
6. Le bouclier AST et les réponses gracieuses d'erreur / clarification / hors périmètre.
7. L'endpoint REST FastAPI POST /reporting/feedback pour la boucle d'apprentissage.
"""

from datetime import date, datetime
import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.reporting.router import router as reporting_router


from app.reporting.audit_service import AUDIT_SERVICE
from app.reporting.constants import CHART_TYPES
from app.reporting.query_catalog import (
    get_query_by_id,
    reset_certified_queries,
)
from app.reporting.response_builder import (
    build_reporting_query_response,
    format_chartjs_visualization,
    formulate_natural_answer,
    select_chart_type,
)
from app.reporting.schemas import ReportingQueryResponse
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    ExecutionStatus,
    IntentDimension,
    IntentEntity,
    IntentMeasure,
    IntentTime,
    QuerySource,
    SqlExecutionResult,
    TextToSQLIntent,
    UserFeedbackPayload,
)
from app.reporting.text_to_sql_pipeline import execute_text_to_sql_pipeline


class TestStep9ResponseBuilder(unittest.TestCase):
    def setUp(self):
        reset_certified_queries()
        AUDIT_SERVICE.clear_history()

        # Base SQLite mémoire pour simuler les exécutions réelles
        self.engine = create_engine("sqlite:///:memory:")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

        with self.engine.connect() as conn:
            conn.execute(
                __import__("sqlalchemy").text(
                    "CREATE TABLE reporting_claim ("
                    "id INTEGER PRIMARY KEY, "
                    "claim_type VARCHAR(50), "
                    "agency VARCHAR(100), "
                    "channel VARCHAR(100), "
                    "service_point_id INTEGER, "
                    "collection_channel_id INTEGER, "
                    "receipt_at DATETIME, "
                    "resolved_at DATETIME, "
                    "sla_due_at DATETIME, "
                    "ai_urgency VARCHAR(50), "
                    "satisfaction_status VARCHAR(50)"
                    ")"
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    "CREATE TABLE reporting_service_point ("
                    "id INTEGER PRIMARY KEY, "
                    "libelle VARCHAR(100)"
                    ")"
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    "CREATE TABLE reporting_collection_channel ("
                    "id INTEGER PRIMARY KEY, "
                    "libelle VARCHAR(100)"
                    ")"
                )
            )
            # Données de test
            conn.execute(
                __import__("sqlalchemy").text(
                    "INSERT INTO reporting_service_point (id, libelle) VALUES (1, 'Agence Littoral'), (2, 'Agence Atlantique')"
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    "INSERT INTO reporting_collection_channel (id, libelle) VALUES (1, 'Guichet'), (2, 'Application Mobile')"
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    "INSERT INTO reporting_claim (id, claim_type, agency, channel, service_point_id, collection_channel_id, receipt_at, ai_urgency) "
                    "VALUES "
                    "(1, 'CLAIM', 'Agence Littoral', 'Guichet', 1, 1, '2026-03-10 10:00:00', 'FAIBLE'), "
                    "(2, 'CLAIM', 'Agence Littoral', 'Application Mobile', 1, 2, '2026-03-11 11:00:00', 'MOYEN'), "
                    "(3, 'CLAIM', 'Agence Atlantique', 'Guichet', 2, 1, '2026-03-12 12:00:00', 'GRAVE')"
                )
            )
            conn.commit()

        test_app = FastAPI()
        test_app.include_router(reporting_router)
        self.client = TestClient(test_app)


    def tearDown(self):
        self.session.close()
        self.engine.dispose()
        reset_certified_queries()
        AUDIT_SERVICE.clear_history()

    def _create_intent(
        self,
        measure_id="reclamation_count",
        measure_label="Nombre de réclamations",
        dimension_id=None,
        dimension_label=None,
    ) -> TextToSQLIntent:
        dims = []
        if dimension_id:
            dims.append(IntentDimension(concept_id=dimension_id, label=dimension_label or dimension_id))

        return TextToSQLIntent(
            contract_version="1.0",
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id=measure_id,
                operation="count",
                target_concept="plainte",
                label=measure_label,
            ),
            dimensions=dims,
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                timezone="Africa/Porto-Novo",
            ),
        )

    # -------------------------------------------------------------------------
    # 1. Tests de la sélection du type de graphique
    # -------------------------------------------------------------------------

    def test_select_chart_type(self):
        # Temporel -> line
        intent_line = self._create_intent(dimension_id="period", dimension_label="Période")
        self.assertEqual(select_chart_type(intent_line, 12), "line")


        # Catégoriel standard (> 5 ou agences) -> bar
        intent_agency = self._create_intent(dimension_id="agency", dimension_label="Agence")
        self.assertEqual(select_chart_type(intent_agency, 10), "bar")
        self.assertEqual(select_chart_type(intent_agency, 2), "bar")

        # Répartition sur canal / risque <= 5 -> pie
        intent_channel = self._create_intent(dimension_id="channel", dimension_label="Canal")
        self.assertEqual(select_chart_type(intent_channel, 3), "pie")
        self.assertEqual(select_chart_type(intent_channel, 7), "bar")

        # Sans dimension (scalaire) -> None
        intent_scalar = self._create_intent(dimension_id=None)
        self.assertIsNone(select_chart_type(intent_scalar, 1))

        # 0 ligne -> None
        self.assertIsNone(select_chart_type(intent_agency, 0))

    # -------------------------------------------------------------------------
    # 2. Tests de formatage Chart.js
    # -------------------------------------------------------------------------

    def test_format_chartjs_visualization_bar(self):
        intent = self._create_intent(dimension_id="agency", dimension_label="Agence")
        columns = ["agency", "case_count"]
        rows = [
            {"agency": "Agence Littoral", "case_count": 120},
            {"agency": "Agence Atlantique", "case_count": 85},
        ]

        vis = format_chartjs_visualization(intent, columns, rows)
        self.assertIsNotNone(vis)
        self.assertEqual(vis.type, "bar")
        self.assertEqual(vis.labels, ["Agence Littoral", "Agence Atlantique"])
        self.assertEqual(len(vis.datasets), 1)
        self.assertEqual(vis.datasets[0].data, [120.0, 85.0])
        self.assertEqual(vis.datasets[0].label, "Nombre de réclamations")
        self.assertIn("par Agence", vis.title)

    def test_format_chartjs_visualization_line(self):
        intent = self._create_intent(dimension_id="period", dimension_label="Mois")
        columns = ["period", "case_count"]
        rows = [
            {"period": "2026-01", "case_count": 50},
            {"period": "2026-02", "case_count": 65},
        ]

        vis = format_chartjs_visualization(intent, columns, rows)
        self.assertIsNotNone(vis)
        self.assertEqual(vis.type, "line")
        self.assertEqual(vis.labels, ["2026-01", "2026-02"])
        self.assertEqual(vis.datasets[0].data, [50.0, 65.0])
        self.assertTrue(vis.datasets[0].fill)

    def test_format_chartjs_visualization_pie(self):
        intent = self._create_intent(dimension_id="channel", dimension_label="Canal")
        columns = ["channel", "case_count"]
        rows = [
            {"channel": "Guichet", "case_count": 70},
            {"channel": "Mobile", "case_count": 30},
        ]

        vis = format_chartjs_visualization(intent, columns, rows)
        self.assertIsNotNone(vis)
        self.assertEqual(vis.type, "pie")
        self.assertEqual(vis.labels, ["Guichet", "Mobile"])
        self.assertEqual(vis.datasets[0].data, [70.0, 30.0])
        self.assertIsInstance(vis.datasets[0].backgroundColor, list)

    def test_format_chartjs_visualization_empty_rows(self):
        intent = self._create_intent(dimension_id="agency", dimension_label="Agence")
        vis = format_chartjs_visualization(intent, ["agency", "case_count"], [])
        self.assertIsNotNone(vis)
        self.assertEqual(vis.labels, [])
        self.assertEqual(vis.datasets[0].data, [])

        # Sans dimension et sans lignes
        intent_scalar = self._create_intent(dimension_id=None)
        vis_scalar = format_chartjs_visualization(intent_scalar, ["case_count"], [])
        self.assertIsNone(vis_scalar)

    # -------------------------------------------------------------------------
    # 3. Tests de formulation en langage naturel
    # -------------------------------------------------------------------------

    def test_formulate_natural_answer(self):
        intent = self._create_intent(dimension_id="agency", dimension_label="Agence")

        # Résultat vide
        msg_empty = formulate_natural_answer("Combien ?", intent, [])
        self.assertEqual(
            msg_empty,
            "Aucun enregistrement ne correspond aux critères demandés pour cette période.",
        )

        # Scalaire unique
        scalar_intent = self._create_intent(dimension_id=None)
        msg_scalar = formulate_natural_answer("Total ?", scalar_intent, [{"case_count": 42}])
        self.assertIn("42", msg_scalar)
        self.assertIn("nombre de réclamations", msg_scalar.lower())

        # Groupement
        rows = [
            {"agency": "Agence Littoral", "case_count": 12},
            {"agency": "Agence Atlantique", "case_count": 8},
        ]
        msg_grouped = formulate_natural_answer("Par agence ?", intent, rows)
        self.assertIn("total de 20", msg_grouped)
        self.assertIn("Agence Littoral (12)", msg_grouped)
        self.assertIn("Agence Atlantique (8)", msg_grouped)

    # -------------------------------------------------------------------------
    # 4. Tests de build_reporting_query_response
    # -------------------------------------------------------------------------

    def test_build_reporting_query_response_structure(self):
        intent = self._create_intent(dimension_id="agency", dimension_label="Agence")
        exec_res = SqlExecutionResult(
            status=ExecutionStatus.SUCCESS,
            columns=["agency", "case_count"],
            rows=[{"agency": "Agence Littoral", "case_count": 2}],
            row_count=1,
            execution_time_ms=15.2,
            sql_executed="SELECT ...",
        )

        response = build_reporting_query_response(
            execution_result=exec_res,
            intent=intent,
            natural_language_query="Réclamations par agence",
            sources=["reporting_claim", "reporting_service_point"],
            query_id="QC-CLAIM-COUNT-BY-AGENCY",
        )

        self.assertIsInstance(response, ReportingQueryResponse)
        self.assertEqual(response.query_id, "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertEqual(response.sources, ["reporting_claim", "reporting_service_point"])
        self.assertIsNotNone(response.visualization)
        self.assertEqual(response.visualization.type, "bar")
        self.assertEqual(len(response.data), 1)
        self.assertIn("total de 2", response.answer)

    def test_build_reporting_query_response_error_statuses(self):
        intent = self._create_intent()

        # Validation failed
        exec_val_fail = SqlExecutionResult(
            status=ExecutionStatus.VALIDATION_FAILED,
            columns=[],
            rows=[],
            sql_executed="DROP TABLE t",
            error_message="Instruction interdite",
        )
        res_val = build_reporting_query_response(exec_val_fail, intent, "Drop ?")
        self.assertEqual(res_val.summary, "Requête non conforme")
        self.assertIn("sécurité et d'intégrité", res_val.answer)
        self.assertIsNone(res_val.visualization)

        # Timeout
        exec_timeout = SqlExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            columns=[],
            rows=[],
            sql_executed="SELECT ...",
            error_message="Timeout",
        )
        res_time = build_reporting_query_response(exec_timeout, intent, "Lent ?")
        self.assertEqual(res_time.summary, "Délai d'exécution dépassé")

        # SQL Error
        exec_sql_err = SqlExecutionResult(
            status=ExecutionStatus.SQL_ERROR,
            columns=[],
            rows=[],
            sql_executed="SELECT bad",
            error_message="Table introuvable",
        )
        res_err = build_reporting_query_response(exec_sql_err, intent, "Erreur ?")
        self.assertEqual(res_err.summary, "Erreur d'exécution SQL")

    # -------------------------------------------------------------------------
    # 5. Tests de bout en bout du pipeline Text-to-SQL
    # -------------------------------------------------------------------------

    def test_pipeline_fast_path_end_to_end(self):
        question = "Nombre de réclamations par agence en 2026"

        response = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            user_id="analyste_1",
            reference_date=date(2026, 6, 1),
        )

        self.assertIsInstance(response, ReportingQueryResponse)
        self.assertEqual(response.query_id, "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertIn("reporting_claim", response.sources)
        self.assertIsNotNone(response.visualization)
        self.assertEqual(response.visualization.type, "bar")
        self.assertEqual(len(response.data), 2)  # Agence Littoral (2), Agence Atlantique (1)

        # Vérification des traces d'audit
        audits = AUDIT_SERVICE.get_recent_audits(10)
        self.assertGreaterEqual(len(audits), 1)
        self.assertEqual(audits[0].query_source, QuerySource.FAST_PATH_CERTIFIED)
        self.assertEqual(audits[0].query_id, "QC-CLAIM-COUNT-BY-AGENCY")

    def test_pipeline_supervised_candidate_end_to_end(self):
        # Question inédite non présente dans les 8 requêtes initiales :
        # "Total des dossiers graves en 2026"
        question = "Nombre de réclamations graves en 2026"

        response = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            user_id="directeur_agence",
            reference_date=date(2026, 6, 1),
        )

        self.assertIsInstance(response, ReportingQueryResponse)
        # La requête a été auto-promue avec succès !
        self.assertIsNotNone(response.query_id)
        self.assertTrue(response.query_id.startswith("QC-AUTO-"))

        # Vérifie qu'elle est bien enregistrée au statut APPROVED dans le catalogue
        entry = get_query_by_id(response.query_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.status, ApprovalStatus.APPROVED)
        self.assertEqual(entry.created_by, "directeur_agence")

        # Vérification des traces d'audit
        audits = AUDIT_SERVICE.get_recent_audits(10)
        self.assertEqual(audits[0].query_source, QuerySource.GENERATIVE_SUPERVISED)
        self.assertEqual(audits[0].query_id, response.query_id)

    def test_pipeline_needs_clarification_response(self):
        question = "Nombre de réclamations depuis mardi"  # Temporel ambigu

        response = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            reference_date=date(2026, 6, 1),
        )

        self.assertEqual(response.summary, "Précision requise")
        self.assertIn("Veuillez préciser", response.answer)
        self.assertIsNone(response.visualization)
        self.assertEqual(response.data, [])

    def test_pipeline_unsupported_response(self):
        # Cas 1 : Tentative de mutation
        question_mutation = "DELETE FROM reporting_claim WHERE id = 1"
        res_mut = execute_text_to_sql_pipeline(
            question=question_mutation,
            db_session=self.session,
        )
        self.assertEqual(res_mut.summary, "Analyse non supportée")
        self.assertIn("Opération 'DELETE' non autorisée", res_mut.answer)

        # Cas 2 : Question hors domaine
        question_weather = "Quel temps fait-il aujourd'hui à Cotonou ?"
        res_weather = execute_text_to_sql_pipeline(
            question=question_weather,
            db_session=self.session,
        )
        self.assertEqual(res_weather.summary, "Analyse non supportée")
        self.assertIn("sort du périmètre", res_weather.answer)
        self.assertIsNone(res_weather.visualization)

    def test_pipeline_ast_rejection_error_response(self):
        from app.reporting.text_to_sql_contracts import CandidateResultColumn, TextToSQLCandidate
        bad_candidate = TextToSQLCandidate(
            contract_version="1.0",
            sql="SELECT * FROM reporting_claim WHERE receipt_at >= :start_date AND receipt_at < :end_date",
            parameters={},
            used_schema=["reporting_claim"],
            result_columns=[
                CandidateResultColumn(name="id", concept_id="plainte", role="measure", data_type="integer")
            ],
        )


        with patch("app.reporting.text_to_sql_pipeline.generate_sql_candidate", return_value=bad_candidate):
            response = execute_text_to_sql_pipeline(
                question="Nombre de réclamations par motif en 2026",
                db_session=self.session,
                reference_date=date(2026, 6, 1),
            )

            self.assertEqual(response.summary, "Requête non conforme")
            self.assertIn("sécurité et d'intégrité", response.answer)
            self.assertIsNone(response.visualization)
            self.assertEqual(response.data, [])


    # -------------------------------------------------------------------------
    # 6. Tests de l'endpoint FastAPI /reporting/feedback
    # -------------------------------------------------------------------------

    def test_router_feedback_positive_and_negative(self):
        # 1. Feedback positif sur une requête existante
        query_id = "QC-CLAIM-COUNT-BY-AGENCY"
        payload_pos = {
            "query_id": query_id,
            "user_id": "auditeur_gpr",
            "is_positive": True,
        }
        res_pos = self.client.post("/reporting/feedback", json=payload_pos)
        self.assertEqual(res_pos.status_code, 200)
        data_pos = res_pos.json()
        self.assertEqual(data_pos["status"], "success")
        self.assertEqual(data_pos["approval_status"], "APPROVED")

        # 2. Feedback négatif (signalement d'incohérence)
        payload_neg = {
            "query_id": query_id,
            "user_id": "auditeur_gpr",
            "is_positive": False,
            "feedback_reason": "Le comptage ne prend pas en compte le nouveau service",
        }
        res_neg = self.client.post("/reporting/feedback", json=payload_neg)
        self.assertEqual(res_neg.status_code, 200)
        data_neg = res_neg.json()
        self.assertEqual(data_neg["status"], "success")
        self.assertEqual(data_neg["approval_status"], "REJECTED")

        # Vérifie que la requête est immédiatement basculée au statut REJECTED dans le catalogue
        entry = get_query_by_id(query_id)
        self.assertEqual(entry.status, ApprovalStatus.REJECTED)

        # 3. Requête inexistante
        payload_not_found = {
            "query_id": "QC-INEXISTANT-999",
            "user_id": "auditeur_gpr",
            "is_positive": True,
        }
        res_404 = self.client.post("/reporting/feedback", json=payload_not_found)
        self.assertEqual(res_404.status_code, 404)


if __name__ == "__main__":
    unittest.main()
