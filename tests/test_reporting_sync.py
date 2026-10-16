import unittest
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from unittest.mock import MagicMock, patch

from app.db.models import ReportingClaim, ReportingSuggestion, ReportingSyncState
from app.db.session import Base
from app.services.sync_service import (
    claim_values,
    perform_sync,
    suggestion_values,
    upsert_claims,
    upsert_claims_with_metrics,
    upsert_suggestions,
    upsert_suggestions_with_metrics,
)


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

    def test_claim_values_foreign_keys(self):
        values = claim_values(
            {
                "id": 101,
                "claimType": "CLAIM",
                "statut_final": "TREAT",
                "objetId": 12,
                "productId": 34,
                "servicePointId": 56,
                "collectionChannelId": 78,
                "collectorId": 90,
            },
            datetime(2026, 9, 14, 10, 0),
        )
        self.assertEqual(values["objet_id"], 12)
        self.assertEqual(values["product_id"], 34)
        self.assertEqual(values["service_point_id"], 56)
        self.assertEqual(values["collection_channel_id"], 78)
        self.assertEqual(values["collector_id"], 90)

    def test_suggestion_values_maps_payload(self):
        values = suggestion_values(
            {
                "id": 501,
                "code": "SUG-2026-001",
                "content": "Installer un distributeur automatique supplémentaire",
                "codeClient": "CLI-888",
                "clientFirstAndLastName": "Koffi Aya",
                "tel": "+2250102030405",
                "canal": "WEB",
                "status": "APPROVED",
                "impactLevel": "FORT",
                "createdAt": "2026-08-10T14:30:00Z",
                "updatedAt": "2026-08-11T09:00:00Z",
                "objetId": 15,
                "servicePointId": 3,
            },
            datetime(2026, 8, 12, 10, 0),
        )
        self.assertEqual(values["source_suggestion_id"], 501)
        self.assertEqual(values["reference"], "SUG-2026-001")
        self.assertEqual(values["title"], "Installer un distributeur automatique supplémentaire")
        self.assertEqual(values["client_code"], "CLI-888")
        self.assertEqual(values["channel"], "WEB")
        self.assertEqual(values["status"], "APPROVED")
        self.assertEqual(values["impact_level"], "FORT")
        self.assertEqual(values["objet_id"], 15)
        self.assertEqual(values["service_point_id"], 3)
        self.assertEqual(values["created_at"], datetime(2026, 8, 10, 14, 30))

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

    def test_upsert_suggestions_creates_and_updates(self):
        with Session(self.engine) as session:
            first = upsert_suggestions_with_metrics(
                session,
                [
                    {"id": 1, "content": "Idée 1", "status": "PENDING"},
                    {"id": 2, "content": "Brouillon", "statut_final": "TEMP_SAVED"},
                ],
                datetime(2026, 9, 14, 10, 0),
            )
            session.commit()
            self.assertEqual(first, {"processed": 1, "inserted": 1, "updated": 0, "ignored": 1})
            self.assertEqual(session.query(ReportingSuggestion).count(), 1)

            second = upsert_suggestions_with_metrics(
                session,
                [{"id": 1, "content": "Idée 1 modifiée", "status": "APPROVED"}],
                datetime(2026, 9, 14, 11, 0),
            )
            session.commit()
            self.assertEqual(second, {"processed": 1, "inserted": 0, "updated": 1, "ignored": 0})
            sugg = session.scalar(
                select(ReportingSuggestion).where(ReportingSuggestion.source_suggestion_id == 1)
            )
            self.assertEqual(sugg.status, "APPROVED")
            self.assertEqual(sugg.title, "Idée 1 modifiée")

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

    @patch("app.services.sync_service.fetch_claim_pages")
    @patch("app.services.sync_service.fetch_suggestion_pages")
    def test_perform_sync_targets(self, mock_fetch_sugg, mock_fetch_claims):
        mock_fetch_claims.return_value = [
            {"id": 10, "claimType": "CLAIM", "statut_final": "TREAT", "updatedAt": "2026-09-14T10:00:00Z"}
        ]
        mock_fetch_sugg.return_value = [
            {"id": 20, "content": "Amélioration accueil", "status": "PENDING", "updatedAt": "2026-09-14T10:00:00Z"}
        ]

        with Session(self.engine) as session:
            # Sync claims only
            res_claims = perform_sync(db=session, target="claims")
            self.assertEqual(res_claims["target"], "claims")
            self.assertEqual(res_claims["received"], 1)
            self.assertEqual(res_claims["inserted"], 1)

            # Sync suggestions only
            res_sugg = perform_sync(db=session, target="suggestions")
            self.assertEqual(res_sugg["target"], "suggestions")
            self.assertEqual(res_sugg["received"], 1)
            self.assertEqual(res_sugg["inserted"], 1)

            # Sync all
            res_all = perform_sync(db=session, target="all")
            self.assertEqual(res_all["target"], "all")
            self.assertIn("claims", res_all)
            self.assertIn("suggestions", res_all)
            self.assertEqual(res_all["received"], 2)


if __name__ == "__main__":
    unittest.main()

