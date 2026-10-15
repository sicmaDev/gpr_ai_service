"""
Tests unitaires et d'intégration pour le cycle de vie PENDING / APPROVED / REJECTED (Step 12).
"""

from datetime import date, datetime
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import ReportingCertifiedQuery
from app.db.session import Base, get_db
from app.reporting.catalog_manager import (
    approve_query,
    get_rejected_anti_patterns_for_intent,
    list_catalog_entries,
    reject_query,
)
from app.reporting.query_catalog import (
    get_certified_queries,
    match_intent_in_catalog,
    reset_certified_queries,
    sync_queries_with_db,
)
from app.reporting.router import router as reporting_router
from app.reporting.sql_generator import parse_candidate_response
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    CandidateParameter,
    IntentEntity,
    IntentMeasure,
    QueryApprovalPayload,
    QueryRejectionPayload,
    TextToSQLCandidate,
    TextToSQLIntent,
)
from app.reporting.text_to_sql_pipeline import execute_text_to_sql_pipeline


class TestStep12PendingLifecycle(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()

        Base.metadata.create_all(self.engine)

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS reporting_suggestion ("
                    "id INTEGER PRIMARY KEY, "
                    "reference VARCHAR(64)"
                    ")"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO reporting_claim (id, source_claim_id, source_code, claim_type, receipt_at, created_at, synced_at) "
                    "VALUES (1, 101, 'REC-001', 'CLAIM', '2026-01-01 00:00:00', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.commit()

        app = FastAPI()
        app.include_router(reporting_router)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        reset_certified_queries()
        sync_queries_with_db(self.session)

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        reset_certified_queries()

    def test_parameter_source_sanitization(self):
        """Vérifie que CandidateParameter et parse_candidate_response tolèrent 'source': ''."""
        raw_json = (
            '{\n'
            '  "contract_version": "1.0",\n'
            '  "sql": "SELECT COUNT(*) AS plainte_count FROM reporting_claim",\n'
            '  "parameters": {\n'
            '    "start_date": {"type": "datetime", "source": ""},\n'
            '    "end_date": {"type": "datetime", "source": ""}\n'
            '  },\n'
            '  "used_schema": ["reporting_claim"],\n'
            '  "result_columns": [{"name": "plainte_count", "concept_id": "plainte_count", "role": "measure", "data_type": "integer"}],\n'
            '  "assumptions": []\n'
            '}'
        )
        candidate = parse_candidate_response(raw_json)
        self.assertIsInstance(candidate, TextToSQLCandidate)
        self.assertEqual(candidate.parameters["start_date"].source, "intent.time.start_date")
        self.assertEqual(candidate.parameters["end_date"].source, "intent.time.end_date")

    def test_candidate_registration_is_pending(self):
        """Vérifie qu'une nouvelle requête exécutée est enregistrée avec statut PENDING."""
        question = "Nombre de réclamations globales"

        def mock_llm_sql(prompt: str) -> str:
            if "SOUS-SCHÉMA" in prompt or "génération de requêtes SQL" in prompt:
                return (
                    '{\n'
                    '  "contract_version": "1.0",\n'
                    '  "sql": "SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE claim_type = \'CLAIM\'",\n'
                    '  "parameters": {},\n'
                    '  "used_schema": ["reporting_claim"],\n'
                    '  "result_columns": [{"name": "reclamation_count", "concept_id": "reclamation_count", "role": "measure", "data_type": "integer"}],\n'
                    '  "assumptions": []\n'
                    '}'
                )
            return (
                '{\n'
                '  "contract_version": "1.0",\n'
                '  "status": "ready",\n'
                '  "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": false},\n'
                '  "measure": {"concept_id": "reclamation_count", "operation": "count", "target_concept": "plainte", "label": "Total"},\n'
                '  "dimensions": [],\n'
                '  "filters": [],\n'
                '  "time": null\n'
                '}'
            )

        resp = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            use_llm=True,
            llm_callable=mock_llm_sql,
        )

        self.assertIsNotNone(resp.query_id)
        self.assertTrue(resp.query_id.startswith("QC-PEND-"))

        # Vérification en base de données
        row = self.session.query(ReportingCertifiedQuery).filter_by(id=resp.query_id).first()
        self.assertIsNotNone(row)
        self.assertEqual(row.status, "PENDING")
        self.assertIsNone(row.approved_by)

    def test_deterministic_reuse_of_pending_query(self):
        """Vérifie que la répétition de la même question réutilise la requête PENDING sans appel LLM."""
        question = "Nombre de réclamations globales"
        llm_call_count = [0]

        def mock_llm_sql(prompt: str) -> str:
            llm_call_count[0] += 1
            if "SOUS-SCHÉMA" in prompt or "génération de requêtes SQL" in prompt:
                return (
                    '{\n'
                    '  "contract_version": "1.0",\n'
                    '  "sql": "SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE claim_type = \'CLAIM\'",\n'
                    '  "parameters": {},\n'
                    '  "used_schema": ["reporting_claim"],\n'
                    '  "result_columns": [{"name": "reclamation_count", "concept_id": "reclamation_count", "role": "measure", "data_type": "integer"}],\n'
                    '  "assumptions": []\n'
                    '}'
                )
            return (
                '{\n'
                '  "contract_version": "1.0",\n'
                '  "status": "ready",\n'
                '  "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": false},\n'
                '  "measure": {"concept_id": "reclamation_count", "operation": "count", "target_concept": "plainte", "label": "Total"},\n'
                '  "dimensions": [],\n'
                '  "filters": [],\n'
                '  "time": null\n'
                '}'
            )

        # 1er appel -> Génération LLM et statut PENDING
        resp1 = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            use_llm=True,
            llm_callable=mock_llm_sql,
        )
        self.assertGreaterEqual(llm_call_count[0], 1)
        pending_id = resp1.query_id

        # 2ème appel avec la même question -> Réutilisation immédiate
        resp2 = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            use_llm=True,
            llm_callable=mock_llm_sql,
        )

        # Le générateur SQL ne doit pas avoir été réinvoqué
        self.assertEqual(resp2.query_id, pending_id)
        self.assertEqual(resp2.execution_mode, "CANDIDATE_PENDING")

    def test_http_approve_endpoint(self):
        """Vérifie que l'endpoint POST /reporting/catalog/queries/{id}/approve promeut la requête au statut APPROVED."""
        question = "Nombre de réclamations globales"

        def mock_llm_sql(prompt: str) -> str:
            if "SOUS-SCHÉMA" in prompt or "génération de requêtes SQL" in prompt:
                return (
                    '{\n'
                    '  "contract_version": "1.0",\n'
                    '  "sql": "SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE claim_type = \'CLAIM\'",\n'
                    '  "parameters": {},\n'
                    '  "used_schema": ["reporting_claim"],\n'
                    '  "result_columns": [{"name": "reclamation_count", "concept_id": "reclamation_count", "role": "measure", "data_type": "integer"}],\n'
                    '  "assumptions": []\n'
                    '}'
                )
            return (
                '{\n'
                '  "contract_version": "1.0",\n'
                '  "status": "ready",\n'
                '  "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": false},\n'
                '  "measure": {"concept_id": "reclamation_count", "operation": "count", "target_concept": "plainte", "label": "Total"},\n'
                '  "dimensions": [],\n'
                '  "filters": [],\n'
                '  "time": null\n'
                '}'
            )

        resp = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            use_llm=True,
            llm_callable=mock_llm_sql,
        )
        q_id = resp.query_id

        # Appel HTTP d'approbation
        http_res = self.client.post(
            f"/reporting/catalog/queries/{q_id}/approve",
            json={"approver": "data_officer", "comment": "Requête validée pour production"},
        )
        self.assertEqual(http_res.status_code, 200)
        body = http_res.json()
        self.assertEqual(body["approval_status"], "APPROVED")

        # Vérification en base
        row = self.session.query(ReportingCertifiedQuery).filter_by(id=q_id).first()
        self.assertEqual(row.status, "APPROVED")
        self.assertEqual(row.approved_by, "data_officer")

    def test_http_reject_endpoint_and_anti_pattern(self):
        """Vérifie que le rejet HTTP marque la requête REJECTED et l'injecte dans les anti-patterns."""
        question = "Nombre de réclamations globales"

        def mock_llm_sql(prompt: str) -> str:
            if "SOUS-SCHÉMA" in prompt or "génération de requêtes SQL" in prompt:
                return (
                    '{\n'
                    '  "contract_version": "1.0",\n'
                    '  "sql": "SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE risk_level = \'UNKNOWN\'",\n'
                    '  "parameters": {},\n'
                    '  "used_schema": ["reporting_claim"],\n'
                    '  "result_columns": [{"name": "reclamation_count", "concept_id": "reclamation_count", "role": "measure", "data_type": "integer"}],\n'
                    '  "assumptions": []\n'
                    '}'
                )
            return (
                '{\n'
                '  "contract_version": "1.0",\n'
                '  "status": "ready",\n'
                '  "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": false},\n'
                '  "measure": {"concept_id": "reclamation_count", "operation": "count", "target_concept": "plainte", "label": "Total"},\n'
                '  "dimensions": [],\n'
                '  "filters": [],\n'
                '  "time": null\n'
                '}'
            )

        resp = execute_text_to_sql_pipeline(
            question=question,
            db_session=self.session,
            use_llm=True,
            llm_callable=mock_llm_sql,
        )
        q_id = resp.query_id

        # Appel HTTP de rejet
        http_res = self.client.post(
            f"/reporting/catalog/queries/{q_id}/reject",
            json={"approver": "expert_metier", "rejection_reason": "Le niveau UNKNOWN n'existe pas"},
        )
        self.assertEqual(http_res.status_code, 200)
        body = http_res.json()
        self.assertEqual(body["approval_status"], "REJECTED")

        # Vérification en base
        row = self.session.query(ReportingCertifiedQuery).filter_by(id=q_id).first()
        self.assertEqual(row.status, "REJECTED")
        self.assertEqual(row.rejection_reason, "Le niveau UNKNOWN n'existe pas")

        # Vérification anti-patterns
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(concept_id="reclamation_count", operation="count", target_concept="plainte", label="Total"),
        )
        anti_pats = get_rejected_anti_patterns_for_intent(intent, db_session=self.session)
        self.assertTrue(any("UNKNOWN" in ap["bad_sql"] for ap in anti_pats))

    def test_http_list_queries_with_status_filter(self):
        """Vérifie le listing des requêtes du catalogue avec filtre de statut."""
        res_all = self.client.get("/reporting/catalog/queries")
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.json()
        self.assertGreaterEqual(data_all["count"], 8)

        res_approved = self.client.get("/reporting/catalog/queries?status=APPROVED")
        self.assertEqual(res_approved.status_code, 200)
        data_approved = res_approved.json()
        self.assertTrue(all(q["status"] == "APPROVED" for q in data_approved["queries"]))


if __name__ == "__main__":
    unittest.main()
