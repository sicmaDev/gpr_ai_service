"""
Tests de persistance MySQL/SQLite et gouvernance ACID pour le Query Catalog et les Métriques Métier (Step 11).

Ce module valide :
1. L'auto-seed automatique des 8 requêtes homologuées de référence dans reporting_certified_queries si table vide.
2. L'auto-seed automatique des 10 métriques métier dans reporting_business_metrics si table vide.
3. La persistance synchrone et transactionnelle du cycle de vie (propose, approve, reject, deprecate).
4. La persistance de l'auto-promotion (QC-AUTO-) et des métriques inédites créées dynamiquement.
5. La mise à jour des statistiques d'exécution Fast-Path (execution_count, last_executed_at) en base.
6. La persistance immédiate des retours utilisateurs (/reporting/feedback) en base de données.
7. La synchronisation et résilience multi-instances (rechargement de la mémoire depuis la base).
"""

from datetime import date, datetime
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import ReportingBusinessMetric, ReportingCertifiedQuery
from app.db.session import Base, get_db
from app.reporting.business_catalog import (
    get_business_catalog,
    register_custom_metric,
    reset_business_metrics,
    sync_metrics_with_db,
)
from app.reporting.catalog_manager import (
    approve_query,
    auto_promote_executed_query,
    deprecate_query,
    propose_query_candidate,
    reject_query,
    submit_user_feedback,
)
from app.reporting.query_catalog import (
    get_certified_queries,
    get_query_by_id,
    register_query_entry,
    reset_certified_queries,
    sync_queries_with_db,
)
from app.reporting.router import router as reporting_router
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    CandidateParameter,
    IntentDimension,
    IntentEntity,
    IntentMeasure,
    IntentTime,
    MetricDefinition,
    QueryApprovalPayload,
    QueryDeprecationPayload,
    QueryRejectionPayload,
    TextToSQLIntent,
    UserFeedbackPayload,
)


class TestStep11DBPersistence(unittest.TestCase):
    def setUp(self):
        # Base SQLite mémoire partagée
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()

        Base.metadata.create_all(self.engine)

        # Réinitialiser les états mémoires
        reset_certified_queries()
        reset_business_metrics()

        # Application de test FastAPI
        self.app = FastAPI()
        self.app.include_router(reporting_router)

        def override_get_db():
            try:
                yield self.session
            finally:
                pass

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self):
        self.session.close()
        reset_certified_queries()
        reset_business_metrics()

    def _sample_intent(self) -> TextToSQLIntent:
        return TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[IntentDimension(concept_id="agency", label="Agence")],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                timezone="Africa/Porto-Novo",
            ),
        )

    def test_auto_seed_initial_catalog_and_metrics(self):
        """Vérifie que sync_queries_with_db peuple les tables si elles sont vides."""
        # Initialement vide
        self.assertEqual(self.session.query(ReportingCertifiedQuery).count(), 0)
        self.assertEqual(self.session.query(ReportingBusinessMetric).count(), 0)

        # Synchronisation
        sync_queries_with_db(self.session)

        # Vérification 8 requêtes initiales
        queries_in_db = self.session.query(ReportingCertifiedQuery).all()
        self.assertEqual(len(queries_in_db), 8)
        agency_q = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-CLAIM-COUNT-BY-AGENCY").first()
        self.assertIsNotNone(agency_q)
        self.assertEqual(agency_q.status, "APPROVED")
        self.assertEqual(agency_q.created_by, "admin")
        self.assertIn("start_date", agency_q.parameters_schema)

        # Vérification 10 métriques de référence
        metrics_in_db = self.session.query(ReportingBusinessMetric).all()
        self.assertEqual(len(metrics_in_db), 10)
        plainte_m = self.session.query(ReportingBusinessMetric).filter_by(metric_id="plainte_count").first()
        self.assertIsNotNone(plainte_m)
        self.assertFalse(plainte_m.is_custom)

    def test_propose_and_approve_lifecycle_persistence(self):
        """Vérifie que propose_query_candidate et approve_query mettent à jour la base de données."""
        sync_queries_with_db(self.session)

        intent = self._sample_intent()
        sql = "SELECT c.id FROM reporting_claim c WHERE c.id = 1"

        # 1. Proposer une candidate
        candidate = propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Requête test candidate",
            created_by="auditor_test",
            query_id="QC-TEST-PERSIST-01",
            db_session=self.session,
        )

        row = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-TEST-PERSIST-01").first()
        self.assertIsNotNone(row)
        self.assertEqual(row.status, "PENDING")
        self.assertEqual(row.created_by, "auditor_test")

        # 2. Homologuer la requête
        approve_query(
            QueryApprovalPayload(
                query_id="QC-TEST-PERSIST-01",
                approver="admin_validateur",
                comment="Validé pour production",
            ),
            db_session=self.session,
        )

        self.session.expire_all()
        row_approved = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-TEST-PERSIST-01").first()
        self.assertEqual(row_approved.status, "APPROVED")
        self.assertEqual(row_approved.approved_by, "admin_validateur")
        self.assertEqual(row_approved.approval_comment, "Validé pour production")

    def test_reject_and_deprecate_lifecycle_persistence(self):
        """Vérifie la persistance du rejet et de la dépréciation en base."""
        sync_queries_with_db(self.session)

        # Rejet
        reject_query(
            QueryRejectionPayload(
                query_id="QC-CLAIM-COUNT-BY-AGENCY",
                approver="risk_manager",
                rejection_reason="Mauvais filtre métier",
            ),
            db_session=self.session,
        )

        self.session.expire_all()
        row_rejected = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-CLAIM-COUNT-BY-AGENCY").first()
        self.assertEqual(row_rejected.status, "REJECTED")
        self.assertEqual(row_rejected.rejection_reason, "Mauvais filtre métier")

        # Dépréciation
        deprecate_query(
            QueryDeprecationPayload(
                query_id="QC-CLAIM-COUNT-BY-CHANNEL",
                reason="Migration vers v2",
            ),
            db_session=self.session,
        )

        self.session.expire_all()
        row_deprecated = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-CLAIM-COUNT-BY-CHANNEL").first()
        self.assertEqual(row_deprecated.status, "DEPRECATED")
        self.assertEqual(row_deprecated.deprecation_reason, "Migration vers v2")

    def test_auto_promotion_with_custom_metric_persistence(self):
        """Vérifie l'auto-promotion d'une requête et la persistance d'une métrique personnalisée."""
        sync_queries_with_db(self.session)

        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="custom_taux_recouvrement",
                operation="avg",
                target_concept="plainte",
                label="Taux de recouvrement",
            ),
            dimensions=[],
            time=None,
        )
        sql = "SELECT AVG(c.ai_risk_score) AS avg_score FROM reporting_claim c"

        entry = auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Score de risque moyen",
            user_id="analyste_credit",
            db_session=self.session,
        )

        # Vérifie la présence de la requête en base
        self.session.expire_all()
        q_row = self.session.query(ReportingCertifiedQuery).filter_by(id=entry.id).first()
        self.assertIsNotNone(q_row)
        self.assertEqual(q_row.status, "PENDING")
        self.assertEqual(q_row.execution_count, 1)

        # Vérifie la présence de la nouvelle métrique personnalisée en base
        m_row = self.session.query(ReportingBusinessMetric).filter_by(metric_id="custom_taux_recouvrement").first()
        self.assertIsNotNone(m_row)
        self.assertTrue(m_row.is_custom)
        self.assertEqual(m_row.created_by, "analyste_credit")
        self.assertEqual(m_row.label, "Taux de recouvrement")

    def test_post_user_feedback_api_db_persistence(self):
        """Vérifie que l'endpoint POST /reporting/feedback persiste le signalement en base."""
        sync_queries_with_db(self.session)

        # Signalement négatif par un utilisateur
        payload = {
            "query_id": "QC-SUGGESTIONS-BY-IMPACT",
            "is_positive": False,
            "feedback_reason": "Incohérence sur le comptage des statuts",
            "user_id": "auditeur_gpr",
        }
        res = self.client.post("/reporting/feedback", json=payload)
        self.assertEqual(res.status_code, 200)

        # Vérifie la mise à jour immédiate en base de données
        self.session.expire_all()
        row = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-SUGGESTIONS-BY-IMPACT").first()
        self.assertIsNotNone(row)
        self.assertEqual(row.status, "REJECTED")
        self.assertEqual(row.rejection_reason, "Incohérence sur le comptage des statuts")
        self.assertEqual(row.approved_by, "auditeur_gpr")

    def test_multi_instance_cache_reloading(self):
        """Vérifie que vider la RAM et rappeler sync_queries_with_db restaure tout depuis la base."""
        sync_queries_with_db(self.session)

        # Ajouter une requête personnalisée en base
        intent = self._sample_intent()
        sql = "SELECT 1"
        propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Requête isolée",
            created_by="admin",
            query_id="QC-RESTORE-TEST",
            db_session=self.session,
        )

        # Simuler un redémarrage à chaud de service (RAM vidée)
        reset_certified_queries()
        self.assertIsNone(get_query_by_id("QC-RESTORE-TEST"))

        # Re-synchronisation depuis la base
        sync_queries_with_db(self.session)
        restored = get_query_by_id("QC-RESTORE-TEST")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.status, ApprovalStatus.PENDING)

    def test_intent_hash_direct_db_lookup_and_indexing(self):
        """Vérifie l'indexation de intent_hash en base et le matching direct O(1) via db_session."""
        from app.reporting.query_catalog import match_intent_in_catalog

        sync_queries_with_db(self.session)

        # 1. Vérification que les requêtes auto-seedées en base possèdent un intent_hash non vide
        queries_in_db = self.session.query(ReportingCertifiedQuery).all()
        for q in queries_in_db:
            self.assertIsNotNone(q.intent_hash)
            self.assertTrue(len(q.intent_hash) >= 8)

        # 2. Matching direct O(1) via db_session
        sample_intent = self._sample_intent()
        match_res = match_intent_in_catalog(sample_intent, db_session=self.session)
        self.assertIsNotNone(match_res)
        entry, bound_params = match_res
        self.assertEqual(entry.id, "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertIsNotNone(entry.intent_hash)

        # 3. Vérification avec propose_query_candidate et candidate matching en base
        custom_intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["SUGGESTION"]),
            measure=IntentMeasure(concept_id="suggestion_count", operation="count", target_concept="plainte", label="Suggestions"),
            dimensions=[IntentDimension(concept_id="category", label="Catégorie")],
        )
        propose_query_candidate(
            canonical_intent=custom_intent,
            parameterized_sql="SELECT COUNT(*) AS suggestion_count FROM reporting_claim WHERE claim_type = 'SUGGESTION'",
            natural_language_query="Nombre de suggestions par catégorie",
            created_by="tester",
            query_id="QC-TEST-HASH-01",
            db_session=self.session,
        )

        row = self.session.query(ReportingCertifiedQuery).filter_by(id="QC-TEST-HASH-01").first()
        self.assertIsNotNone(row)
        self.assertIsNotNone(row.intent_hash)

        # match_intent_in_catalog avec include_pending=True et db_session
        pending_match = match_intent_in_catalog(custom_intent, include_pending=True, db_session=self.session)
        self.assertIsNotNone(pending_match)
        p_entry, _ = pending_match
        self.assertEqual(p_entry.id, "QC-TEST-HASH-01")
        self.assertEqual(p_entry.status, ApprovalStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
