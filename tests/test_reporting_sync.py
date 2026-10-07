import unittest
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models import ReportingClaim, ReportingSyncState
from app.db.session import Base
from app.services.sync_service import claim_values, upsert_claims, upsert_claims_with_metrics


class ReportingSyncTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_claim_values_maps_spring_payload(self):
        values = claim_values(
            {
                "id": 42,
                "claimType": "CLAIM",
                "statut_final": "TREAT",
                "date_creation": "2026-09-14T10:00:00Z",
                "updatedAt": "2026-09-14T11:00:00+01:00",
                "objet_categorie": "MONETIQUE",
                "texte_plainte": "Carte bloquée",
            },
            datetime(2026, 9, 14, 10, 0),
        )
        self.assertEqual(values["source_claim_id"], 42)
        self.assertEqual(values["claim_type"], "CLAIM")
        self.assertEqual(values["category"], "MONETIQUE")
        self.assertEqual(values["source_updated_at"], datetime(2026, 9, 14, 10, 0))

    def test_upsert_updates_existing_claim(self):
        with Session(self.engine) as session:
            first = {"id": 42, "claimType": "CLAIM", "statut_final": "TREAT"}
            second = {"id": 42, "claimType": "CLAIM", "statut_final": "SATISFIED"}
            upsert_claims(session, [first], datetime(2026, 9, 14, 10, 0))
            session.commit()
            upsert_claims(session, [second], datetime(2026, 9, 14, 11, 0))
            session.commit()
            claim = session.scalar(
                select(ReportingClaim).where(ReportingClaim.source_claim_id == 42)
            )
            self.assertEqual(claim.status, "SATISFIED")
            self.assertEqual(session.query(ReportingClaim).count(), 1)

    def test_upsert_excludes_temp_saved_claims(self):
        with Session(self.engine) as session:
            count = upsert_claims(
                session,
                [
                    {"id": 1, "claimType": "CLAIM", "statut_final": "TEMP_SAVED"},
                    {"id": 2, "claimType": "CLAIM", "statut_final": "TREAT"},
                ],
                datetime(2026, 9, 14, 10, 0),
            )
            session.commit()
            self.assertEqual(count, 1)
            self.assertEqual(session.query(ReportingClaim).count(), 1)
            self.assertEqual(
                session.scalar(
                    select(ReportingClaim).where(
                        ReportingClaim.source_claim_id == 2
                    )
                ).status,
                "TREAT",
            )

    def test_upsert_reports_insert_update_and_ignore_counts(self):
        with Session(self.engine) as session:
            first = upsert_claims_with_metrics(
                session,
                [
                    {"id": 1, "claimType": "CLAIM", "statut_final": "TREAT"},
                    {"id": 2, "claimType": "CLAIM", "statut_final": "TEMP_SAVED"},
                ],
                datetime(2026, 9, 14, 10, 0),
            )
            session.commit()
            second = upsert_claims_with_metrics(
                session,
                [{"id": 1, "claimType": "CLAIM", "statut_final": "SATISFIED"}],
                datetime(2026, 9, 14, 11, 0),
            )

            self.assertEqual(first, {"processed": 1, "inserted": 1, "updated": 0, "ignored": 1})
            self.assertEqual(second, {"processed": 1, "inserted": 0, "updated": 1, "ignored": 0})

    def test_sync_state_is_part_of_database_model(self):
        with Session(self.engine) as session:
            state = ReportingSyncState(
                sync_name="spring_boot_claims",
                updated_at=datetime(2026, 9, 14, 10, 0),
            )
            session.add(state)
            session.commit()
            self.assertIsNotNone(state.id)


if __name__ == "__main__":
    unittest.main()
