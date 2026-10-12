"""
Tests unitaires pour le Step 8 : Approbation Humaine, Cycle de Vie & Gestion du Query Catalog.

Vérifie :
1. La proposition de requêtes candidates (statut PENDING) et l'exclusion immédiate du Fast-Path.
2. Le blocage immédiat à la proposition en cas de violation AST (sécurité, mutations, données sensibles).
3. L'approbation administrative formelle (statut APPROVED) et l'activation instantanée du Fast-Path.
4. Le refus d'approbation si la sécurité AST est compromise.
5. Le rejet documenté avec motif (statut REJECTED) et l'interdiction d'accès Fast-Path.
6. La dépréciation administrative (statut DEPRECATED) et le retrait immédiat du Fast-Path.
7. Le filtrage et l'audit des requêtes par statut dans le catalogue.
8. La dépréciation et synchronisation automatique lors de l'évolution du schéma de base de données.
"""

from copy import deepcopy
from datetime import date
import unittest

from app.reporting.catalog_manager import (
    approve_query,
    deprecate_query,
    list_catalog_entries,
    propose_query_candidate,
    reject_query,
    sync_on_schema_evolution,
)
from app.reporting.query_catalog import (
    get_query_by_id,
    match_intent_in_catalog,
    reset_certified_queries,
)
from app.reporting.schema_catalog import SCHEMA_CATALOG
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    IntentDimension,
    IntentEntity,
    IntentMeasure,
    IntentTime,
    QueryApprovalPayload,
    QueryDeprecationPayload,
    QueryRejectionPayload,
    SchemaCatalog,
    TextToSQLIntent,
)


class TestStep8CatalogManager(unittest.TestCase):
    def setUp(self):
        # Toujours démarrer avec un catalogue propre dans son état homologué initial
        reset_certified_queries()

    def tearDown(self):
        # Toujours restaurer le catalogue après chaque test pour garantir l'isolation
        reset_certified_queries()

    def _build_sample_intent(self) -> TextToSQLIntent:
        """Construit une intention de test unique pour les réclamations par agence et canal."""
        return TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[
                IntentDimension(concept_id="agency", label="Agence"),
                IntentDimension(concept_id="channel", label="Canal de collecte"),
            ],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 6, 30),
                timezone="Africa/Porto-Novo",
            ),
        )

    def test_propose_candidate_success(self):
        """Une requête valide est enregistrée au statut PENDING et ignorée par le Fast-Path."""
        intent = self._build_sample_intent()
        sql = (
            "SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle, cc.libelle"
        )

        entry = propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Nombre de réclamations par agence et par canal",
            created_by="analyst_test",
            query_id="QC-TEST-CANDIDATE-01",
        )

        self.assertEqual(entry.id, "QC-TEST-CANDIDATE-01")
        self.assertEqual(entry.status, ApprovalStatus.PENDING)
        self.assertIn("start_date", entry.parameters_schema)
        self.assertIn("end_date", entry.parameters_schema)

        # Vérification dans le catalogue
        stored = get_query_by_id("QC-TEST-CANDIDATE-01")
        self.assertIsNotNone(stored)
        self.assertEqual(stored.status, ApprovalStatus.PENDING)

        # Le Fast-Path NE DOIT PAS matcher une requête au statut PENDING
        match_result = match_intent_in_catalog(intent)
        self.assertIsNone(match_result)

    def test_propose_candidate_ast_rejection(self):
        """Une candidate violant la sécurité AST (mutation ou donnée sensible) est rejetée dès la soumission."""
        intent = self._build_sample_intent()

        # 1. Tentative avec une mutation DELETE
        sql_mutation = (
            "DELETE FROM reporting_claim WHERE receipt_at >= :start_date"
        )
        with self.assertRaises(ValueError) as ctx:
            propose_query_candidate(
                canonical_intent=intent,
                parameterized_sql=sql_mutation,
                natural_language_query="Suppression de données",
                created_by="malicious_user",
                query_id="QC-ATTACK-01",
            )
        self.assertIn("validateur AST", str(ctx.exception))
        self.assertIsNone(get_query_by_id("QC-ATTACK-01"))

        # 2. Tentative avec accès à une colonne sensible (client_code)
        sql_sensitive = (
            "SELECT c.client_code, COUNT(c.id) "
            "FROM reporting_claim c "
            "WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY c.client_code"
        )
        with self.assertRaises(ValueError) as ctx:
            propose_query_candidate(
                canonical_intent=intent,
                parameterized_sql=sql_sensitive,
                natural_language_query="Fuite données confidentielles",
                created_by="careless_user",
                query_id="QC-LEAK-01",
            )
        self.assertIn("client_code", str(ctx.exception))
        self.assertIsNone(get_query_by_id("QC-LEAK-01"))

    def test_approve_query_promotes_to_fast_path(self):
        """L'approbation homologue la requête et l'active immédiatement dans le Fast-Path."""
        intent = self._build_sample_intent()
        sql = (
            "SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle, cc.libelle"
        )

        entry = propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Nombre de réclamations par agence et par canal",
            created_by="analyst_test",
            query_id="QC-TEST-CANDIDATE-02",
        )
        self.assertEqual(entry.status, ApprovalStatus.PENDING)

        # Avant approbation : Fast-Path négatif
        self.assertIsNone(match_intent_in_catalog(intent))

        # Action d'approbation administrative
        approval_payload = QueryApprovalPayload(
            query_id="QC-TEST-CANDIDATE-02",
            approver="admin_dg_audit",
            comment="Validation formelle après revue de code SQL",
        )
        approved_entry = approve_query(approval_payload)

        self.assertEqual(approved_entry.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved_entry.approved_by, "admin_dg_audit")
        self.assertIsNotNone(approved_entry.approved_at)
        self.assertEqual(
            approved_entry.approval_comment,
            "Validation formelle après revue de code SQL",
        )

        # Après approbation : HIT immédiat sur le Fast-Path !
        match_res = match_intent_in_catalog(intent)
        self.assertIsNotNone(match_res)
        matched_entry, bound_params = match_res
        self.assertEqual(matched_entry.id, "QC-TEST-CANDIDATE-02")
        self.assertEqual(bound_params["start_date"], "2026-01-01 00:00:00")
        self.assertEqual(bound_params["end_date"], "2026-06-30 00:00:00")

    def test_approve_query_not_found(self):
        """Tenter d'approuver une requête inconnue lève un KeyError explicite."""
        with self.assertRaises(KeyError) as ctx:
            approve_query(
                QueryApprovalPayload(
                    query_id="QC-NON-EXISTENT",
                    approver="admin",
                )
            )
        self.assertIn("QC-NON-EXISTENT", str(ctx.exception))

    def test_approve_query_fails_if_ast_invalid(self):
        """Si la requête altérée échoue au contrôle AST lors de l'approbation, celle-ci est refusée."""
        intent = self._build_sample_intent()
        sql = (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle"
        )
        entry = propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence",
            created_by="user_test",
            query_id="QC-CORRUPTED-01",
        )

        # Altération simulée de la requête dans le catalogue pour introduire un DROP
        entry.parameterized_sql = "DROP TABLE reporting_claim"

        with self.assertRaises(ValueError) as ctx:
            approve_query(
                QueryApprovalPayload(
                    query_id="QC-CORRUPTED-01",
                    approver="admin",
                )
            )
        self.assertIn("ne satisfait pas les critères de sécurité AST", str(ctx.exception))

    def test_reject_query_blocks_fast_path(self):
        """Le rejet passe le statut à REJECTED et empêche toute utilisation Fast-Path."""
        intent = self._build_sample_intent()
        sql = (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle"
        )
        entry = propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence",
            created_by="user_test",
            query_id="QC-REJECT-01",
        )

        rejected = reject_query(
            QueryRejectionPayload(
                query_id="QC-REJECT-01",
                approver="lead_data_gov",
                rejection_reason="Indicateur non aligné avec la définition légale",
            )
        )

        self.assertEqual(rejected.status, ApprovalStatus.REJECTED)
        self.assertEqual(
            rejected.rejection_reason,
            "Indicateur non aligné avec la définition légale",
        )

        # Doit être ignorée par le Fast-Path
        self.assertIsNone(match_intent_in_catalog(intent))

    def test_deprecate_query_removes_from_fast_path(self):
        """La dépréciation d'une requête homologuée la retire instantanément du Fast-Path."""
        intent = self._build_sample_intent()
        sql = (
            "SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle, cc.libelle"
        )
        propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence et canal",
            created_by="analyst",
            query_id="QC-DEPRECATE-01",
        )
        approve_query(
            QueryApprovalPayload(
                query_id="QC-DEPRECATE-01",
                approver="admin",
            )
        )

        # Vérification qu'elle est bien active
        self.assertIsNotNone(match_intent_in_catalog(intent))

        # Dépréciation
        depr_entry = deprecate_query(
            QueryDeprecationPayload(
                query_id="QC-DEPRECATE-01",
                reason="Remplacée par une version plus performante avec index dédié",
            )
        )
        self.assertEqual(depr_entry.status, ApprovalStatus.DEPRECATED)
        self.assertEqual(
            depr_entry.deprecation_reason,
            "Remplacée par une version plus performante avec index dédié",
        )

        # Le Fast-Path doit désormais l'ignorer
        self.assertIsNone(match_intent_in_catalog(intent))

    def test_list_catalog_entries_filtering(self):
        """La fonction list_catalog_entries permet le filtrage strict par statut."""
        # Au départ : 8 requêtes certifiées APPROVED
        initial_approved = list_catalog_entries(status_filter=ApprovalStatus.APPROVED)
        self.assertEqual(len(initial_approved), 8)

        # Ajout d'une candidate PENDING
        intent = self._build_sample_intent()
        sql = (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle"
        )
        propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence",
            created_by="user",
            query_id="QC-FILTER-PENDING",
        )

        pending_list = list_catalog_entries(status_filter=ApprovalStatus.PENDING)
        self.assertEqual(len(pending_list), 1)
        self.assertEqual(pending_list[0].id, "QC-FILTER-PENDING")

        # Liste sans filtre : 8 APPROVED + 1 PENDING = 9 entrées
        all_list = list_catalog_entries()
        self.assertEqual(len(all_list), 9)

    def test_sync_on_schema_evolution(self):
        """Simulation d'une évolution de schéma : invalidation automatique des requêtes non compatibles."""
        # Création d'un clone du Schema Catalog pour simuler la version 2.0.0
        new_catalog_data = deepcopy(SCHEMA_CATALOG.model_dump())
        new_catalog_data["schema_version"] = "2.0.0"

        # Simulation : suppression de la table 'reporting_collection_channel' dans le nouveau schéma
        del new_catalog_data["tables"]["reporting_collection_channel"]

        # Mise à jour des relations pour retirer celles touchant reporting_collection_channel
        new_catalog_data["relationships"] = [
            rel
            for rel in new_catalog_data["relationships"]
            if rel["source_table"] != "reporting_collection_channel"
            and rel["target_table"] != "reporting_collection_channel"
        ]

        evolved_schema = SchemaCatalog(**new_catalog_data)

        # Ajout et approbation d'une requête utilisant 'reporting_collection_channel'
        intent = self._build_sample_intent()
        sql_with_channel = (
            "SELECT cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY cc.libelle"
        )
        propose_query_candidate(
            canonical_intent=intent,
            parameterized_sql=sql_with_channel,
            natural_language_query="Volume par canal",
            created_by="analyst",
            query_id="QC-CHAN-EVOL-01",
        )
        approve_query(
            QueryApprovalPayload(
                query_id="QC-CHAN-EVOL-01",
                approver="admin",
            )
        )

        # Exécution de la synchronisation d'évolution de schéma
        deprecated_ids = sync_on_schema_evolution(
            new_schema_version="2.0.0",
            new_schema_catalog=evolved_schema,
        )

        # La requête utilisant la table disparue doit être invalidée
        self.assertIn("QC-CHAN-EVOL-01", deprecated_ids)
        invalidated_entry = get_query_by_id("QC-CHAN-EVOL-01")
        self.assertEqual(invalidated_entry.status, ApprovalStatus.DEPRECATED)
        self.assertIn("reporting_collection_channel", invalidated_entry.deprecation_reason)

        # Les requêtes certifiées n'utilisant pas la table disparue doivent être migrées en version 2.0.0
        agency_query = get_query_by_id("QC-CLAIM-COUNT-BY-AGENCY")
        self.assertEqual(agency_query.status, ApprovalStatus.APPROVED)
        self.assertEqual(agency_query.schema_version, "2.0.0")


if __name__ == "__main__":
    unittest.main()
