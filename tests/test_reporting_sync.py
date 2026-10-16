import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from unittest.mock import MagicMock, patch

from app.db.models import (
    ReportingCategorieObjet,
    ReportingClaim,
    ReportingCollectionChannel,
    ReportingHistoriqueAffectation,
    ReportingObjet,
    ReportingPoste,
    ReportingProduct,
    ReportingSatisfactionMeasure,
    ReportingServicePoint,
    ReportingSolution,
    ReportingSuggestion,
    ReportingSyncState,
    ReportingUser,
)
from app.db.session import Base
from app.services.sync_service import (
    affectation_values,
    claim_values,
    fetch_affectation_pages,
    fetch_referentiels,
    fetch_solution_pages,
    perform_sync,
    satisfaction_measure_values,
    solution_values,
    suggestion_values,
    upsert_affectations,
    upsert_affectations_with_metrics,
    upsert_claims,
    upsert_claims_with_metrics,
    upsert_referentiels_with_metrics,
    upsert_solutions_with_metrics,
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

    def test_affectation_values_maps_payload(self):
        values = affectation_values(
            {
                "id": 88,
                "reclamationId": 12,
                "suggestionId": None,
                "codePlainte": "REC-2026-001",
                "typePlainte": "RECLAMATION",
                "nomAgent": "Jean Dupont",
                "emailAgent": "jean.dupont@banque.ci",
                "affecteurId": 4,
                "nomAffecteur": "Directeur Agence",
                "emailAffecteur": "dir@banque.ci",
                "dateAffectation": "2026-09-14T08:30:00Z",
                "delaiJours": 3,
                "dateFinAffectation": "2026-09-17T18:00:00Z",
                "affectationPrecedenteId": 55,
                "lastNotification": "2026-09-15T10:00:00Z",
                "mailEnvoye": True,
                "smsEnvoye": False,
            }
        )
        self.assertEqual(values["id"], 88)
        self.assertEqual(values["reclamation_id"], 12)
        self.assertIsNone(values["suggestion_id"])
        self.assertEqual(values["code_plainte"], "REC-2026-001")
        self.assertEqual(values["type_plainte"], "RECLAMATION")
        self.assertEqual(values["nom_agent"], "Jean Dupont")
        self.assertEqual(values["email_agent"], "jean.dupont@banque.ci")
        self.assertEqual(values["affecteur_id"], 4)
        self.assertEqual(values["nom_affecteur"], "Directeur Agence")
        self.assertEqual(values["email_affecteur"], "dir@banque.ci")
        self.assertEqual(values["date_affectation"], datetime(2026, 9, 14, 8, 30))
        self.assertEqual(values["delai_jours"], 3)
        self.assertEqual(values["date_fin_affectation"], datetime(2026, 9, 17, 18, 0))
        self.assertEqual(values["affectation_precedente_id"], 55)
        self.assertEqual(values["last_notification"], datetime(2026, 9, 15, 10, 0))
        self.assertTrue(values["mail_envoye"])
        self.assertFalse(values["sms_envoye"])

    def test_upsert_affectations_creates_and_updates(self):
        with Session(self.engine) as session:
            first = upsert_affectations_with_metrics(
                session,
                [
                    {
                        "id": 1,
                        "codePlainte": "REC-01",
                        "nomAgent": "Agent Initial",
                        "dateAffectation": "2026-09-14T10:00:00Z",
                    }
                ],
            )
            session.commit()
            self.assertEqual(first, {"processed": 1, "inserted": 1, "updated": 0, "ignored": 0})
            self.assertEqual(session.query(ReportingHistoriqueAffectation).count(), 1)

            second = upsert_affectations_with_metrics(
                session,
                [
                    {
                        "id": 1,
                        "codePlainte": "REC-01",
                        "nomAgent": "Agent Réaffecté",
                        "affectationPrecedenteId": 99,
                        "dateAffectation": "2026-09-15T10:00:00Z",
                    }
                ],
            )
            session.commit()
            self.assertEqual(second, {"processed": 1, "inserted": 0, "updated": 1, "ignored": 0})
            aff = session.scalar(
                select(ReportingHistoriqueAffectation).where(ReportingHistoriqueAffectation.id == 1)
            )
            self.assertEqual(aff.nom_agent, "Agent Réaffecté")
            self.assertEqual(aff.affectation_precedente_id, 99)

    def test_fetch_affectation_pages_handles_404(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response

        res = fetch_affectation_pages(mock_session)
        self.assertEqual(res, [])

    def test_fetch_referentiels_handles_404(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response

        res = fetch_referentiels(mock_session)
        self.assertEqual(res, {})

    def test_upsert_referentiels_creates_and_updates(self):
        payload = {
            "postes": [{"id": 10, "libelle": "Chargé Clientèle", "description": "Gestion relation client"}],
            "servicePoints": [
                {
                    "id": 20,
                    "libelle": "Agence Plateau",
                    "description": "Siège",
                    "type": "AGENCE",
                    "isPrincipalAgence": True,
                    "directionId": 1,
                }
            ],
            "collectionChannels": [{"id": 30, "libelle": "Application Mobile", "description": "Canal digital"}],
            "products": [
                {
                    "id": 40,
                    "libelle": "Compte Épargne",
                    "description": "Épargne rémunérée",
                    "isDeleted": False,
                }
            ],
            "categories": [{"id": 50, "libelle": "Opérations Bancaires", "description": "Virements et chèques"}],
            "objets": [
                {
                    "id": 60,
                    "categorieId": 50,
                    "libelle": "Erreur virement",
                    "risqueLevel": "ELEVE",
                    "processingTime": 3,
                }
            ],
            "users": [
                {
                    "id": 70,
                    "code": "USR-070",
                    "firstandlastname": "Kouassi Yao",
                    "email": "kyao@banque.ci",
                    "additionalrole": "GESTIONNAIRE",
                    "servicePointId": 20,
                    "posteId": 10,
                }
            ],
        }

        with Session(self.engine) as session:
            first_metrics = upsert_referentiels_with_metrics(session, payload)
            session.commit()

            self.assertEqual(first_metrics["received"], 7)
            self.assertEqual(first_metrics["inserted"], 7)
            self.assertEqual(first_metrics["updated"], 0)

            self.assertEqual(session.query(ReportingPoste).count(), 1)
            self.assertEqual(session.query(ReportingServicePoint).count(), 1)
            self.assertEqual(session.query(ReportingCollectionChannel).count(), 1)
            self.assertEqual(session.query(ReportingProduct).count(), 1)
            self.assertEqual(session.query(ReportingCategorieObjet).count(), 1)
            self.assertEqual(session.query(ReportingObjet).count(), 1)
            self.assertEqual(session.query(ReportingUser).count(), 1)

            # Test update on existing dimensions
            update_payload = {
                "servicePoints": [
                    {
                        "id": 20,
                        "libelle": "Agence Plateau Rénovée",
                        "description": "Nouveau siège",
                        "type": "DIRECTION",
                        "isPrincipalAgence": False,
                    }
                ],
                "products": [
                    {
                        "id": 40,
                        "libelle": "Compte Épargne Pro",
                        "description": "Épargne pro",
                        "isDeleted": True,
                    }
                ],
            }
            second_metrics = upsert_referentiels_with_metrics(session, update_payload)
            session.commit()

            self.assertEqual(second_metrics["received"], 2)
            self.assertEqual(second_metrics["inserted"], 0)
            self.assertEqual(second_metrics["updated"], 2)

            sp = session.scalar(select(ReportingServicePoint).where(ReportingServicePoint.id == 20))
            self.assertEqual(sp.libelle, "Agence Plateau Rénovée")
            self.assertEqual(sp.type, "DIRECTION")
            self.assertFalse(sp.is_principal_agence)

            prod = session.scalar(select(ReportingProduct).where(ReportingProduct.id == 40))
            self.assertEqual(prod.libelle, "Compte Épargne Pro")
            self.assertTrue(prod.is_deleted)

    def test_solution_values_maps_payload(self):
        values = solution_values(
            {
                "id": 10,
                "claimId": 100,
                "authorId": 20,
                "approverId": 30,
                "status": "APPROVED",
                "commentaire": "Solution validée",
                "motifDesaprobation": None,
                "approvedAt": "2026-09-20T15:00:00Z",
                "isAiProposed": True,
                "aiSelectedSolution": "SOLUTION_1",
            }
        )
        self.assertEqual(values["id"], 10)
        self.assertEqual(values["claim_id"], 100)
        self.assertEqual(values["author_id"], 20)
        self.assertEqual(values["approver_id"], 30)
        self.assertEqual(values["status"], "APPROVED")
        self.assertEqual(values["commentaire"], "Solution validée")
        self.assertTrue(values["is_ai_proposed"])
        self.assertEqual(values["ai_selected_solution"], "SOLUTION_1")
        self.assertEqual(values["approved_at"], datetime(2026, 9, 20, 15, 0))

    def test_fetch_solution_pages_handles_404(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response

        res = fetch_solution_pages(mock_session)
        self.assertEqual(res, [])

    def test_upsert_solutions_creates_and_updates(self):
        with Session(self.engine) as session:
            # Create prerequisite claim and user
            claim = ReportingClaim(
                id=1,
                source_claim_id=100,
                claim_type="CLAIM",
                status="TREAT",
                synced_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            author = ReportingUser(
                id=200,
                code="USR-200",
                firstandlastname="Agent A",
            )
            measurer = ReportingUser(
                id=300,
                code="USR-300",
                firstandlastname="Client C",
            )
            session.add_all([claim, author, measurer])
            session.commit()

            # Insert solution with satisfaction measure
            payload = [
                {
                    "id": 10,
                    "claimId": 100,
                    "authorId": 200,
                    "status": "APPROVED",
                    "commentaire": "Remboursement effectué",
                    "approvedAt": "2026-09-20T15:00:00Z",
                    "isAiProposed": True,
                    "aiSelectedSolution": "REMB_AUTO",
                    "satisfactionMeasure": {
                        "id": 50,
                        "measurerId": 300,
                        "status": "SATISFIED",
                        "commentaire": "Très satisfait du dénouement",
                        "measureDateTime": "2026-09-20T16:00:00Z",
                    },
                }
            ]
            first_metrics = upsert_solutions_with_metrics(session, payload)
            session.commit()

            self.assertEqual(first_metrics["processed"], 1)
            self.assertEqual(first_metrics["inserted"], 1)
            self.assertEqual(first_metrics["updated"], 0)
            self.assertEqual(session.query(ReportingSolution).count(), 1)
            self.assertEqual(session.query(ReportingSatisfactionMeasure).count(), 1)

            sol = session.scalar(select(ReportingSolution).where(ReportingSolution.id == 10))
            self.assertEqual(sol.claim_id, 1)  # Resolved to claim.id
            self.assertEqual(sol.author_id, 200)
            self.assertEqual(sol.status, "APPROVED")
            self.assertTrue(sol.is_ai_proposed)

            sm = session.scalar(select(ReportingSatisfactionMeasure).where(ReportingSatisfactionMeasure.id == 50))
            self.assertEqual(sm.solution_id, 10)
            self.assertEqual(sm.measurer_id, 300)
            self.assertEqual(sm.status, "SATISFIED")

            # Test update on existing solution
            update_payload = [
                {
                    "id": 10,
                    "claimId": 100,
                    "authorId": 200,
                    "status": "REJECTED",
                    "motifDesaprobation": "Montant erroné",
                }
            ]
            second_metrics = upsert_solutions_with_metrics(session, update_payload)
            session.commit()

            self.assertEqual(second_metrics["processed"], 1)
            self.assertEqual(second_metrics["inserted"], 0)
            self.assertEqual(second_metrics["updated"], 1)

            sol = session.scalar(select(ReportingSolution).where(ReportingSolution.id == 10))
            self.assertEqual(sol.status, "REJECTED")
            self.assertEqual(sol.motif_desaprobation, "Montant erroné")

    def test_upsert_solutions_ignores_missing_claim(self):
        with Session(self.engine) as session:
            payload = [
                {
                    "id": 99,
                    "claimId": 99999,  # does not exist
                    "status": "APPROVED",
                }
            ]
            metrics = upsert_solutions_with_metrics(session, payload)
            session.commit()

            self.assertEqual(metrics["ignored"], 1)
            self.assertEqual(metrics["inserted"], 0)
            self.assertEqual(session.query(ReportingSolution).count(), 0)

    @patch("app.services.sync_service.fetch_solution_pages")
    @patch("app.services.sync_service.fetch_referentiels")
    @patch("app.services.sync_service.fetch_claim_pages")
    @patch("app.services.sync_service.fetch_suggestion_pages")
    @patch("app.services.sync_service.fetch_affectation_pages")
    def test_perform_sync_targets(
        self, mock_fetch_aff, mock_fetch_sugg, mock_fetch_claims, mock_fetch_ref, mock_fetch_sol
    ):
        mock_fetch_ref.return_value = {
            "postes": [{"id": 1, "libelle": "Directeur Agence"}],
        }
        mock_fetch_claims.return_value = [
            {"id": 10, "claimType": "CLAIM", "statut_final": "TREAT", "updatedAt": "2026-09-14T10:00:00Z"}
        ]
        mock_fetch_sugg.return_value = [
            {"id": 20, "content": "Amélioration accueil", "status": "PENDING", "updatedAt": "2026-09-14T10:00:00Z"}
        ]
        mock_fetch_aff.return_value = [
            {"id": 30, "codePlainte": "REC-10", "nomAgent": "Agent A", "dateAffectation": "2026-09-14T10:00:00Z"}
        ]
        mock_fetch_sol.return_value = [
            {"id": 40, "claimId": 10, "status": "APPROVED", "updatedAt": "2026-09-14T10:00:00Z"}
        ]

        with Session(self.engine) as session:
            # Sync referentiels only
            res_ref = perform_sync(db=session, target="referentiels")
            self.assertEqual(res_ref["target"], "referentiels")
            self.assertEqual(res_ref["received"], 1)
            self.assertEqual(res_ref["inserted"], 1)

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

            # Sync affectations only
            res_aff = perform_sync(db=session, target="affectations")
            self.assertEqual(res_aff["target"], "affectations")
            self.assertEqual(res_aff["received"], 1)
            self.assertEqual(res_aff["inserted"], 1)

            # Sync solutions only (claim 10 exists from claims sync)
            res_sol = perform_sync(db=session, target="solutions")
            self.assertEqual(res_sol["target"], "solutions")
            self.assertEqual(res_sol["received"], 1)
            self.assertEqual(res_sol["inserted"], 1)

            # Sync all
            res_all = perform_sync(db=session, target="all")
            self.assertEqual(res_all["target"], "all")
            self.assertIn("referentiels", res_all)
            self.assertIn("claims", res_all)
            self.assertIn("suggestions", res_all)
            self.assertIn("affectations", res_all)
            self.assertIn("solutions", res_all)
            self.assertEqual(res_all["received"], 5)


if __name__ == "__main__":
    unittest.main()


