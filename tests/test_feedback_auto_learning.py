"""
Tests unitaires pour le module d'Auto-Promotion et d'Apprentissage par Feedback Utilisateur GPR.

Vérifie :
1. L'auto-promotion immédiate d'une requête candidate exécutée avec succès (statut APPROVED, Fast-Path actif).
2. L'incrémentation de l'execution_count sur ré-exécutions successives.
3. Le signalement d'incohérence par un utilisateur habilité (statut REJECTED + retrait immédiat du Fast-Path).
4. La confirmation positive d'un utilisateur renforçant la confiance de la requête.
5. L'extraction ciblée des anti-patterns (requêtes rejetées et motifs) pour une intention donnée.
6. L'injection dynamique des anti-patterns dans le prompt de génération Nemotron.
7. La propreté du prompt lorsqu'aucun rejet n'est enregistré.
"""

from datetime import date
import unittest

from app.reporting.catalog_manager import (
    auto_promote_executed_query,
    get_rejected_anti_patterns_for_intent,
    submit_user_feedback,
)
from app.reporting.query_catalog import (
    get_query_by_id,
    match_intent_in_catalog,
    reset_certified_queries,
)
from app.reporting.sql_generator import build_sql_generation_prompt
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    IntentDimension,
    IntentEntity,
    IntentMeasure,
    IntentTime,
    TextToSQLIntent,
    UserFeedbackPayload,
)


class TestFeedbackAutoLearning(unittest.TestCase):
    def setUp(self):
        # Réinitialisation étanche du catalogue avant chaque test
        reset_certified_queries()

    def tearDown(self):
        # Restauration étanche après chaque test
        reset_certified_queries()

    def _build_test_intent(self) -> TextToSQLIntent:
        """Construit une intention de test canonique pour les réclamations par agence et canal."""
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
                IntentDimension(concept_id="channel", label="Canal"),
            ],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 6, 30),
                timezone="Africa/Porto-Novo",
            ),
        )

    def test_auto_promote_executed_query_success(self):
        """Une requête candidate exécutée avec succès est auto-promue APPROVED et active dans le Fast-Path."""
        intent = self._build_test_intent()
        sql = (
            "SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle, cc.libelle"
        )

        entry = auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume de réclamations par agence et canal",
            user_id="charge_clientele_01",
            query_id="QC-AUTO-TEST-01",
        )

        self.assertEqual(entry.id, "QC-AUTO-TEST-01")
        self.assertEqual(entry.status, ApprovalStatus.APPROVED)
        self.assertEqual(entry.approved_by, "auto_verified")
        self.assertEqual(entry.execution_count, 1)
        self.assertIsNotNone(entry.last_executed_at)

        # Vérification immédiate sur le Fast-Path : le lendemain, la même question donne le même résultat !
        match_result = match_intent_in_catalog(intent)
        self.assertIsNotNone(match_result)
        matched_entry, bound_params = match_result
        self.assertEqual(matched_entry.id, "QC-AUTO-TEST-01")
        self.assertEqual(bound_params["start_date"], "2026-01-01 00:00:00")
        self.assertEqual(bound_params["end_date"], "2026-06-30 00:00:00")

    def test_auto_promote_increments_count(self):
        """Ré-exécuter une requête déjà présente incrémente execution_count sans doublon."""
        intent = self._build_test_intent()
        sql = (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle"
        )

        # 1ère exécution
        e1 = auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence",
            user_id="user_1",
            query_id="QC-COUNT-INC-01",
        )
        self.assertEqual(e1.execution_count, 1)

        # 2ème exécution avec le même SQL
        e2 = auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence",
            user_id="user_2",
            query_id="QC-COUNT-INC-01",
        )
        self.assertEqual(e2.execution_count, 2)

    def test_user_feedback_rejection_removes_fast_path(self):
        """Un signalement d'incohérence par l'utilisateur bascule la requête en REJECTED et la sort du Fast-Path."""
        intent = self._build_test_intent()
        sql = (
            "SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle, cc.libelle"
        )

        # La requête a été auto-promue lors d'une première exécution
        auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume réclamations",
            user_id="agent_direction",
            query_id="QC-REJECT-FEEDBACK-01",
        )
        self.assertIsNotNone(match_intent_in_catalog(intent))

        # L'utilisateur signale que le résultat ne correspond pas à son attente métier
        feedback_payload = UserFeedbackPayload(
            query_id="QC-REJECT-FEEDBACK-01",
            user_id="agent_direction",
            is_positive=False,
            feedback_reason="Le canal web doit être exclu car traité par une autre entité",
        )
        updated = submit_user_feedback(feedback_payload)

        self.assertEqual(updated.status, ApprovalStatus.REJECTED)
        self.assertEqual(
            updated.rejection_reason,
            "Le canal web doit être exclu car traité par une autre entité",
        )
        self.assertEqual(updated.approved_by, "agent_direction")

        # La requête est IMMÉDIATEMENT retirée du Fast-Path
        self.assertIsNone(match_intent_in_catalog(intent))

    def test_user_feedback_positive_reinforcement(self):
        """Un signalement positif renforce l'approbation sans altérer le Fast-Path."""
        intent = self._build_test_intent()
        sql = (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle"
        )
        auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql,
            natural_language_query="Volume agence",
            user_id="user_test",
            query_id="QC-POS-01",
        )

        feedback_payload = UserFeedbackPayload(
            query_id="QC-POS-01",
            user_id="user_test",
            is_positive=True,
        )
        updated = submit_user_feedback(feedback_payload)

        self.assertEqual(updated.status, ApprovalStatus.APPROVED)
        self.assertIn("user_test", updated.approval_comment)
        # Reste active dans le Fast-Path
        entry = get_query_by_id("QC-POS-01")
        self.assertEqual(entry.status, ApprovalStatus.APPROVED)

    def test_get_rejected_anti_patterns_for_intent(self):
        """L'extracteur d'anti-patterns retrouve les requêtes rejetées liées au même concept ou à la même mesure."""
        intent = self._build_test_intent()
        sql_bad = (
            "SELECT c.id, c.status FROM reporting_claim c WHERE c.receipt_at >= :start_date"
        )


        # Enregistrement d'une requête rejetée
        auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=sql_bad,
            natural_language_query="Test mauvais format",
            user_id="user_1",
            query_id="QC-BAD-01",
        )
        submit_user_feedback(
            UserFeedbackPayload(
                query_id="QC-BAD-01",
                user_id="auditeur_qualite",
                is_positive=False,
                feedback_reason="Ne jamais projeter les identifiants techniques bruts sans agrégation",
            )
        )

        # Extraction des anti-patterns
        anti_patterns = get_rejected_anti_patterns_for_intent(intent)
        self.assertGreaterEqual(len(anti_patterns), 1)
        found = next((ap for ap in anti_patterns if ap["query_id"] == "QC-BAD-01"), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["bad_sql"], sql_bad)
        self.assertEqual(
            found["rejection_reason"],
            "Ne jamais projeter les identifiants techniques bruts sans agrégation",
        )

    def test_prompt_injects_anti_patterns(self):
        """Le prompt de génération pour Nemotron intègre la section anti-patterns avec le SQL et le motif."""
        intent = self._build_test_intent()
        anti_patterns = [
            {
                "query_id": "QC-REJECT-01",
                "bad_sql": "SELECT c.id FROM reporting_claim c",
                "rejection_reason": "Ne pas utiliser d'extraction ligne par ligne pour un volume global",
            }
        ]

        prompt = build_sql_generation_prompt(
            intent=intent,
            subschema_str="TABLE reporting_claim (id BIGINT, claim_type VARCHAR)",
            anti_patterns=anti_patterns,
        )

        self.assertIn("PIÈGES MÉTIER ET ERREURS À ÉVITER", prompt)
        self.assertIn("SELECT c.id FROM reporting_claim c", prompt)
        self.assertIn(
            "Ne pas utiliser d'extraction ligne par ligne pour un volume global", prompt
        )
        self.assertIn("CONSIGNE STRICTE", prompt)

    def test_prompt_clean_when_no_rejections(self):
        """Le prompt de génération reste concis et propre lorsqu'aucun anti-pattern n'est spécifié."""
        intent = self._build_test_intent()
        prompt = build_sql_generation_prompt(
            intent=intent,
            subschema_str="TABLE reporting_claim (id BIGINT)",
            anti_patterns=None,
        )

        self.assertNotIn("PIÈGES MÉTIER ET ERREURS À ÉVITER", prompt)


if __name__ == "__main__":
    unittest.main()
