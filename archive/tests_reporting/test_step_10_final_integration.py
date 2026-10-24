"""
Tests d'intégration finale de bout en bout pour le Step 10.

Ce fichier valide :
1. L'acheminement direct de POST /reporting/query vers le moteur Text-to-SQL gouverné.
2. Le retour conforme du contrat ReportingQueryResponse avec query_id, sources, data et Chart.js.
3. Le Fast-Path certifié en conditions réelles HTTP.
4. L'auto-promotion d'une requête supervisée inédite via l'API REST.
5. La gestion gracieuse des filtres temporels utilisateur.
6. La restitution des demandes de clarification.
7. Le blocage propre (HTTP 422) des tentatives de mutation ou questions hors périmètre.
8. La rétrocompatibilité de l'alias answer_query().
9. La non-régression absolue de GET /reporting/dashboard.
"""

from datetime import date, datetime
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.reporting.query_catalog import get_query_by_id, reset_certified_queries
from app.reporting.router import router as reporting_router
from app.reporting.schemas import ReportingFilters, ReportingQueryResponse
from app.reporting.service import answer_query
from app.reporting.text_to_sql_contracts import ApprovalStatus


class TestStep10FinalIntegration(unittest.TestCase):
    def setUp(self):
        reset_certified_queries()

        # Base SQLite mémoire pour l'intégration complète avec StaticPool multi-thread
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()


        import app.db.models
        from app.db.session import Base

        Base.metadata.create_all(self.engine)

        with self.engine.connect() as conn:
            conn.execute(
                __import__("sqlalchemy").text(
                    "ALTER TABLE reporting_claim ADD COLUMN service_point_id INTEGER"
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    "ALTER TABLE reporting_claim ADD COLUMN collection_channel_id INTEGER"
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
                    "INSERT INTO reporting_claim ("
                    "id, source_claim_id, claim_type, status, category, channel, agency, "
                    "service_point_id, collection_channel_id, risk_level, ai_urgency, "
                    "ai_risk_score, created_at, receipt_at, synced_at"
                    ") VALUES "
                    "(1, 101, 'CLAIM', 'EN_COURS', 'CARTE', 'Guichet', 'Agence Littoral', 1, 1, 'MINEUR', 'FAIBLE', 20.0, '2026-03-10 10:00:00', '2026-03-10 10:00:00', '2026-03-10 10:00:00'), "
                    "(2, 102, 'CLAIM', 'EN_COURS', 'VIREMENT', 'Mobile', 'Agence Littoral', 1, 2, 'MOYEN', 'MOYEN', 50.0, '2026-03-11 11:00:00', '2026-03-11 11:00:00', '2026-03-11 11:00:00'), "
                    "(3, 103, 'CLAIM', 'CLOTURE', 'CREDIT', 'Guichet', 'Agence Atlantique', 2, 1, 'GRAVE', 'GRAVE', 90.0, '2026-03-12 12:00:00', '2026-03-12 12:00:00', '2026-03-12 12:00:00')"
                )
            )
            conn.commit()


        # Application de test FastAPI avec surcharge de la session DB
        self.app = FastAPI()
        self.app.include_router(reporting_router)

        def _override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()


        self.app.dependency_overrides[get_db] = _override_get_db
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.session.close()
        self.engine.dispose()
        reset_certified_queries()

    # -------------------------------------------------------------------------
    # 1. Tests POST /reporting/query via HTTP
    # -------------------------------------------------------------------------

    def test_post_reporting_query_fast_path(self):
        """Vérifie qu'une question couverte par le catalogue homologué emprunte le Fast-Path."""
        payload = {
            "question": "Nombre de réclamations par agence en 2026",
            "filters": {},
        }
        res = self.client.post("/reporting/query", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["query_id"], "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertIn("reporting_claim", data["sources"])
        self.assertIsNotNone(data["visualization"])
        self.assertEqual(data["visualization"]["type"], "bar")
        self.assertEqual(len(data["data"]), 2)
        self.assertIn("Agence Littoral", str(data["data"]))
        self.assertIn("total de 3", data["answer"])

    def test_post_reporting_query_supervised_auto_promotion(self):
        """Vérifie qu'une question inédite est générée, exécutée et auto-promue avec succès."""
        payload = {
            "question": "Nombre de réclamations graves en 2026",
            "filters": {},
        }
        res = self.client.post("/reporting/query", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIsNotNone(data["query_id"])
        self.assertTrue(data["query_id"].startswith("QC-PEND-") or data["query_id"].startswith("QC-AUTO-"))

        # Vérifie la présence effective dans le catalogue
        entry = get_query_by_id(data["query_id"])
        self.assertIsNotNone(entry)
        self.assertEqual(entry.status, ApprovalStatus.PENDING)

    def test_post_reporting_query_with_filters(self):
        """Vérifie la prise en compte des filtres utilisateur explicites."""
        payload = {
            "question": "Nombre de réclamations par agence",
            "filters": {
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
            },
        }
        res = self.client.post("/reporting/query", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["query_id"], "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertEqual(len(data["data"]), 2)

    def test_post_reporting_query_clarification_response(self):
        """Vérifie la réponse informative lorsqu'une clarification de date est requise."""
        payload = {
            "question": "Nombre de réclamations reçues depuis mardi",
            "filters": {},
        }
        res = self.client.post("/reporting/query", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["summary"], "Précision requise")
        self.assertIn("Veuillez préciser", data["answer"])
        self.assertIsNone(data["visualization"])
        self.assertEqual(data["data"], [])

    def test_post_reporting_query_security_unsupported(self):
        """Vérifie que les tentatives d'écriture sont bloquées avec une erreur 422."""
        payload = {
            "question": "DELETE FROM reporting_claim WHERE id = 1",
            "filters": {},
        }
        res = self.client.post("/reporting/query", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("DELETE", res.json()["detail"])

    def test_post_reporting_query_out_of_scope_unsupported(self):
        """Vérifie que les questions hors domaine bancaire sont rejetées avec une erreur 422."""
        payload = {
            "question": "Quel temps fait-il aujourd'hui à Cotonou ?",
            "filters": {},
        }
        res = self.client.post("/reporting/query", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("périmètre", res.json()["detail"].lower())

    # -------------------------------------------------------------------------
    # 2. Rétrocompatibilité de l'alias answer_query
    # -------------------------------------------------------------------------

    def test_answer_query_alias_backward_compatibility(self):
        """Vérifie que tout code legacy appelant answer_query continue de fonctionner."""
        resp = answer_query(
            db=self.session,
            question="Nombre de réclamations par agence en 2026",
            filters=ReportingFilters(),
        )
        self.assertIsInstance(resp, ReportingQueryResponse)
        self.assertEqual(resp.query_id, "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertEqual(len(resp.data), 2)

    # -------------------------------------------------------------------------
    # 3. Sanctuarisation du Dashboard (GET /reporting/dashboard)
    # -------------------------------------------------------------------------

    def test_get_dashboard_endpoint_non_regression(self):
        """Vérifie que le dashboard fixe continue de répondre à 100% sans perturbation."""
        res = self.client.get("/reporting/dashboard")
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("periods", data)
        self.assertIn("metrics", data)
        self.assertIn("charts", data)
        self.assertEqual(data["metrics"]["total_claims"], 3)


if __name__ == "__main__":
    unittest.main()
