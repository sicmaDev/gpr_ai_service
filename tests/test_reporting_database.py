import unittest
from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.db.models import ReportingClaim
from app.db.session import Base


class ReportingDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_reporting_claim_table_has_expected_indexes(self):
        indexes = {
            index["name"]
            for index in inspect(self.engine).get_indexes("reporting_claim")
        }
        self.assertIn("ix_reporting_claim_created_at", indexes)
        self.assertIn("ix_reporting_claim_risk_level", indexes)

    def test_reporting_claim_source_id_is_unique(self):
        with Session(self.engine) as session:
            claim = ReportingClaim(
                source_claim_id=1,
                claim_type="CLAIM",
                synced_at=datetime(2026, 9, 14),
            )
            session.add(claim)
            session.commit()
            self.assertEqual(session.query(ReportingClaim).count(), 1)


if __name__ == "__main__":
    unittest.main()
