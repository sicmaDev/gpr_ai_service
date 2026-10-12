"""
Tests unitaires pour le Step 7 : Exécution Read-Only Sécurisée, Bind Params, Quotas et Audit.
"""

from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.reporting.audit_service import AUDIT_SERVICE, AuditService, mask_sensitive_params
from app.reporting.query_catalog import get_query_by_id
from app.reporting.sql_executor import (
    enforce_row_limit,
    execute_read_only_query,
    sanitize_parameters,
)
from app.reporting.text_to_sql_contracts import (
    ExecutionAuditLog,
    ExecutionStatus,
    QuerySource,
    SqlExecutionResult,
)

TestBase = declarative_base()


class MockReportingClaim(TestBase):
    __tablename__ = "reporting_claim"

    id = Column(Integer, primary_key=True)
    claim_type = Column(String(50))
    status = Column(String(50))
    created_at = Column(DateTime)
    receipt_at = Column(DateTime)


class TestStep7SqlExecutorAndAudit(unittest.TestCase):
    """Suite de tests unitaires pour l'exécuteur SQL et le service d'audit."""

    @classmethod
    def setUpClass(cls):
        # Configuration d'une base SQLite en mémoire pour tester l'exécution SQL
        cls.engine = create_engine("sqlite:///:memory:")
        TestBase.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

        # Insertion de quelques données de test
        with cls.Session() as session:
            session.add_all([
                MockReportingClaim(
                    id=1,
                    claim_type="CLAIM",
                    status="EN_COURS",
                    created_at=datetime(2026, 10, 1, 10, 0, 0),
                    receipt_at=datetime(2026, 10, 1, 10, 0, 0),
                ),
                MockReportingClaim(
                    id=2,
                    claim_type="CLAIM",
                    status="RESOLU",
                    created_at=datetime(2026, 10, 2, 11, 0, 0),
                    receipt_at=datetime(2026, 10, 2, 11, 0, 0),
                ),
                MockReportingClaim(
                    id=3,
                    claim_type="DENUNCIATION",
                    status="EN_COURS",
                    created_at=datetime(2026, 10, 3, 12, 0, 0),
                    receipt_at=datetime(2026, 10, 3, 12, 0, 0),
                ),
            ])
            session.commit()

    def setUp(self):
        AUDIT_SERVICE.clear_history()

    # --------------------------------------------------------------------------
    # 1. Tests d'assainissement et de typage des paramètres (sanitize_parameters)
    # --------------------------------------------------------------------------

    def test_sanitize_parameters_conversions(self):
        raw = {
            ":start_date": "2026-10-01T00:00:00",
            "end_date": "2026-10-31T23:59:59",
            "agency": "  Cotonou  ",
            "limit_num": 10,
            "is_active": True,
            "none_val": None,
        }
        sanitized = sanitize_parameters(raw)

        self.assertIn("start_date", sanitized)
        self.assertNotIn(":start_date", sanitized)
        self.assertIsInstance(sanitized["start_date"], datetime)
        self.assertEqual(sanitized["start_date"], datetime(2026, 10, 1, 0, 0, 0))

        self.assertIsInstance(sanitized["end_date"], datetime)
        self.assertEqual(sanitized["agency"], "Cotonou")
        self.assertEqual(sanitized["limit_num"], 10)
        self.assertTrue(sanitized["is_active"])
        self.assertIsNone(sanitized["none_val"])

    def test_sanitize_parameters_empty(self):
        self.assertEqual(sanitize_parameters(None), {})
        self.assertEqual(sanitize_parameters({}), {})

    # --------------------------------------------------------------------------
    # 2. Tests du plafonnement de ressources (enforce_row_limit)
    # --------------------------------------------------------------------------

    def test_enforce_row_limit_adds_default_500(self):
        sql = "SELECT id, status FROM reporting_claim"
        capped = enforce_row_limit(sql, max_limit=500)
        self.assertIn("LIMIT 500", capped.upper())

    def test_enforce_row_limit_caps_excessive_limit(self):
        sql = "SELECT id, status FROM reporting_claim LIMIT 2000"
        capped = enforce_row_limit(sql, max_limit=500)
        self.assertIn("LIMIT 500", capped.upper())
        self.assertNotIn("2000", capped)

    def test_enforce_row_limit_preserves_smaller_limit(self):
        sql = "SELECT id, status FROM reporting_claim LIMIT 25"
        capped = enforce_row_limit(sql, max_limit=500)
        self.assertIn("LIMIT 25", capped.upper())
        self.assertNotIn("500", capped)

    # --------------------------------------------------------------------------
    # 3. Tests du verrou de sécurité AST avant exécution (Block on Invalid)
    # --------------------------------------------------------------------------

    def test_execute_blocks_mutation_queries(self):
        dangerous_sql = "DROP TABLE reporting_claim"
        res = execute_read_only_query(dangerous_sql)
        self.assertEqual(res.status, ExecutionStatus.VALIDATION_FAILED)
        self.assertEqual(res.row_count, 0)
        self.assertIn("seules les requetes SELECT", res.error_message)

    def test_execute_blocks_sensitive_columns(self):
        sensitive_sql = "SELECT client_code FROM reporting_claim"
        res = execute_read_only_query(sensitive_sql)
        self.assertEqual(res.status, ExecutionStatus.VALIDATION_FAILED)
        self.assertIn("colonne sensible", res.error_message)

    def test_execute_blocks_wildcard_star(self):
        star_sql = "SELECT * FROM reporting_claim"
        res = execute_read_only_query(star_sql)
        self.assertEqual(res.status, ExecutionStatus.VALIDATION_FAILED)
        self.assertIn("Projection wildcard '*'", res.error_message)

    # --------------------------------------------------------------------------
    # 4. Tests d'exécution nominale en lecture seule avec Bind Params
    # --------------------------------------------------------------------------

    def test_execute_read_only_nominal(self):
        sql = """
        SELECT c.claim_type, COUNT(c.id) AS total_count
        FROM reporting_claim c
        WHERE c.created_at >= :start_date AND c.created_at < :end_date
        GROUP BY c.claim_type
        ORDER BY total_count DESC
        """
        params = {
            "start_date": "2026-10-01T00:00:00",
            "end_date": "2026-10-05T00:00:00",
        }

        with self.Session() as session:
            res = execute_read_only_query(
                sql=sql,
                parameters=params,
                session=session,
            )

        self.assertEqual(res.status, ExecutionStatus.SUCCESS)
        self.assertIsNone(res.error_message)
        self.assertGreater(res.execution_time_ms, 0.0)
        self.assertEqual(res.row_count, 2)
        self.assertIn("claim_type", res.columns)
        self.assertIn("total_count", res.columns)

        # CLAIM (2 dossiers) et DENUNCIATION (1 dossier)
        row_map = {r["claim_type"]: r["total_count"] for r in res.rows}
        self.assertEqual(row_map["CLAIM"], 2)
        self.assertEqual(row_map["DENUNCIATION"], 1)


    def test_execute_read_only_ensures_rollback(self):
        # Vérification qu'un rollback est systématiquement déclenché
        mock_session = MagicMock()
        mock_session.execute.return_value.keys.return_value = ["cnt"]
        mock_session.execute.return_value.fetchall.return_value = [(10,)]

        sql = "SELECT COUNT(c.id) AS cnt FROM reporting_claim c"
        res = execute_read_only_query(sql, session=mock_session)

        self.assertEqual(res.status, ExecutionStatus.SUCCESS)
        mock_session.rollback.assert_called_once()

    # --------------------------------------------------------------------------
    # 5. Tests de journalisation d'audit (AuditService)
    # --------------------------------------------------------------------------

    def test_audit_service_logging(self):
        mock_result = SqlExecutionResult(
            status=ExecutionStatus.SUCCESS,
            columns=["agency", "cnt"],
            rows=[{"agency": "Cotonou", "cnt": 5}],
            row_count=1,
            execution_time_ms=12.5,
            sql_executed="SELECT agency, COUNT(id) FROM reporting_claim GROUP BY agency LIMIT 500",
            bound_parameters={"start_date": "2026-10-01", "client_code": "CLI-999"},
        )

        audit_entry = AUDIT_SERVICE.log_execution(
            query_source=QuerySource.GENERATIVE_SUPERVISED,
            sql_executed=mock_result.sql_executed,
            bound_parameters=mock_result.bound_parameters,
            result=mock_result,
            natural_language_query="Combien de plaintes par agence ?",
        )

        self.assertIsInstance(audit_entry, ExecutionAuditLog)
        self.assertEqual(audit_entry.status, ExecutionStatus.SUCCESS)
        self.assertEqual(audit_entry.row_count, 1)
        self.assertEqual(audit_entry.execution_time_ms, 12.5)

        # Vérification du masquage de données sensibles dans l'audit
        self.assertEqual(audit_entry.sanitized_parameters["client_code"], "[MASQUÉ]")
        self.assertEqual(audit_entry.sanitized_parameters["start_date"], "2026-10-01")

        # Vérification de la présence dans l'historique
        recent = AUDIT_SERVICE.get_recent_audits(10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].audit_id, audit_entry.audit_id)

    def test_audit_service_updates_query_catalog_stats(self):
        query_id = "QC-CLAIM-COUNT-BY-AGENCY"
        cert_query = get_query_by_id(query_id)
        self.assertIsNotNone(cert_query)

        initial_count = cert_query.execution_count

        mock_result = SqlExecutionResult(
            status=ExecutionStatus.SUCCESS,
            columns=["agency", "case_count"],
            rows=[],
            row_count=0,
            execution_time_ms=8.0,
            sql_executed=cert_query.parameterized_sql,
            bound_parameters={},
        )

        AUDIT_SERVICE.log_execution(
            query_source=QuerySource.FAST_PATH_CERTIFIED,
            sql_executed=cert_query.parameterized_sql,
            bound_parameters={},
            result=mock_result,
            query_id=query_id,
        )

        # L'entrée dans le catalogue doit être mise à jour
        self.assertEqual(cert_query.execution_count, initial_count + 1)
        self.assertIsNotNone(cert_query.last_executed_at)
        self.assertIsNotNone(cert_query.avg_execution_time_ms)

        # Vérification via la méthode get_stats_for_query
        stats = AUDIT_SERVICE.get_stats_for_query(query_id)
        self.assertEqual(stats["execution_count"], cert_query.execution_count)

    def test_execute_blocks_unauthorized_table(self):
        # Table inconnue ou table transactionnelle gps_claims
        sql = "SELECT id FROM gps_claims"
        res = execute_read_only_query(sql)
        self.assertEqual(res.status, ExecutionStatus.VALIDATION_FAILED)
        self.assertIn("non autorisee ou inconnue", res.error_message)

    def test_execute_handles_operational_error(self):
        # Simulation d'une session fermée provoquant une OperationalError / SQLAlchemyError
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Simulated DB connection lost")

        sql = "SELECT c.id FROM reporting_claim c"
        res = execute_read_only_query(sql, session=mock_session)

        self.assertEqual(res.status, ExecutionStatus.SQL_ERROR)
        self.assertIn("Simulated DB connection lost", res.error_message)
        mock_session.rollback.assert_called_once()

    @classmethod
    def tearDownClass(cls):
        TestBase.metadata.drop_all(cls.engine)
        cls.engine.dispose()


if __name__ == "__main__":
    unittest.main()
