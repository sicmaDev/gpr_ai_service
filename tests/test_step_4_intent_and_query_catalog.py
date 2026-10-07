"""
Tests unitaires pour le Step 4 : Résolution d'Intention & Query Catalog (Fast-Path).

Vérifie :
1. L'intégrité des 8 requêtes certifiées initiales (statut APPROVED, schéma de paramètres).
2. L'appariement précis du circuit rapide (Fast-Path match) et la liaison des paramètres.
3. Le comportement en cas d'intention inédite (Fast-Path miss retournant None).
4. La résolution d'intention déterministe pour les formulations en langage naturel.
5. La détection des demandes nécessitant clarification (needs_clarification) et hors périmètre (unsupported).
6. Le constructeur de prompt Nemotron et le parseur de réponse JSON Pydantic.
"""

import json
import unittest
from datetime import date

from app.reporting.intent_resolver import (
    build_intent_prompt,
    extract_date_range,
    parse_intent_response,
    resolve_intent,
    resolve_intent_deterministic,
)
from app.reporting.query_catalog import (
    get_certified_queries,
    get_query_by_id,
    match_intent_in_catalog,
)
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    IntentDimension,
    IntentEntity,
    IntentMeasure,
    IntentTime,
    TextToSQLIntent,
)


class TestQueryCatalog(unittest.TestCase):
    def test_certified_queries_registry_count(self):
        queries = get_certified_queries()
        self.assertEqual(len(queries), 8)

    def test_all_certified_queries_are_approved(self):
        queries = get_certified_queries()
        for q_id, entry in queries.items():
            self.assertEqual(
                entry.status,
                ApprovalStatus.APPROVED,
                f"La requête certifiée {q_id} doit être au statut APPROVED",
            )
            self.assertEqual(entry.contract_version, "1.0")
            self.assertIn(":start_date", entry.parameterized_sql)
            self.assertIn("start_date", entry.parameters_schema)
            self.assertIn("end_date", entry.parameters_schema)

    def test_get_query_by_id(self):
        entry = get_query_by_id("QC-CLAIM-COUNT-BY-AGENCY")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.id, "QC-CLAIM-COUNT-BY-AGENCY")

        missing = get_query_by_id("QC-INEXISTANT-999")
        self.assertIsNone(missing)

    def test_fast_path_exact_match_for_agency_claims(self):
        intent = TextToSQLIntent(
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
                start_date=date(2026, 9, 1),
                end_date=date(2026, 10, 1),
                timezone="Africa/Porto-Novo",
            ),
        )

        match_res = match_intent_in_catalog(intent)
        self.assertIsNotNone(match_res)
        entry, bound_params = match_res

        self.assertEqual(entry.id, "QC-CLAIM-COUNT-BY-AGENCY")
        self.assertEqual(bound_params["start_date"], "2026-09-01 00:00:00")
        self.assertEqual(bound_params["end_date"], "2026-10-01 00:00:00")

    def test_fast_path_exact_match_for_unified_plaintes(self):
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(
                concept_id="plainte",
                types=["CLAIM", "DENUNCIATION", "SUGGESTION"],
                include_all_types=True,
            ),
            measure=IntentMeasure(
                concept_id="plainte_count",
                operation="count",
                target_concept="plainte",
                label="Total unifié des plaintes",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2027, 1, 1),
                timezone="Africa/Porto-Novo",
            ),
        )

        match_res = match_intent_in_catalog(intent)
        self.assertIsNotNone(match_res)
        entry, bound_params = match_res

        self.assertEqual(entry.id, "QC-UNIFIED-PLAINTES-TOTAL")
        self.assertEqual(bound_params["start_date"], "2026-01-01 00:00:00")

    def test_fast_path_miss_for_novel_intent(self):
        # Intention inédite non présente dans le catalogue pré-approuvé (ex: réclamations par produit)
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[IntentDimension(concept_id="product", label="Produit")],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                timezone="Africa/Porto-Novo",
            ),
        )

        match_res = match_intent_in_catalog(intent)
        self.assertIsNone(match_res, "Une intention inédite doit retourner None pour déclencher le Step 5")


class TestIntentResolver(unittest.TestCase):
    def setUp(self):
        self.ref_date = date(2026, 10, 7)

    def test_extract_date_range_named_month(self):
        start, end, err = extract_date_range("en septembre 2026", self.ref_date)
        self.assertIsNone(err)
        self.assertEqual(start, date(2026, 9, 1))
        self.assertEqual(end, date(2026, 10, 1))

    def test_extract_date_range_relative_expressions(self):
        start, end, err = extract_date_range("ce mois-ci", self.ref_date)
        self.assertIsNone(err)
        self.assertEqual(start, date(2026, 10, 1))
        self.assertEqual(end, date(2026, 11, 1))

        start_last, end_last, err = extract_date_range("le mois dernier", self.ref_date)
        self.assertIsNone(err)
        self.assertEqual(start_last, date(2026, 9, 1))
        self.assertEqual(end_last, date(2026, 10, 1))

    def test_extract_date_range_ambiguous_phrase(self):
        start, end, err = extract_date_range("combien de réclamations depuis mardi ?", self.ref_date)
        self.assertEqual(err, "AMBIGUOUS_TIME_FIELD")
        self.assertIsNone(start)

    def test_resolve_deterministic_claims_by_agency(self):
        intent = resolve_intent_deterministic(
            "Combien de réclamations avons-nous par agence en septembre 2026 ?",
            self.ref_date,
        )
        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.entity.concept_id, "plainte")
        self.assertEqual(intent.entity.types, ["CLAIM"])
        self.assertEqual(intent.measure.concept_id, "reclamation_count")
        self.assertEqual(len(intent.dimensions), 1)
        self.assertEqual(intent.dimensions[0].concept_id, "agency")
        self.assertEqual(intent.time.start_date, date(2026, 9, 1))
        self.assertEqual(intent.time.end_date, date(2026, 10, 1))

    def test_resolve_deterministic_unified_plaintes(self):
        intent = resolve_intent_deterministic(
            "Quel est le total de toutes les plaintes en 2026 ?",
            self.ref_date,
        )
        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.entity.concept_id, "plainte")
        self.assertTrue(intent.entity.include_all_types)
        self.assertEqual(intent.measure.concept_id, "plainte_count")

    def test_resolve_deterministic_sla_rate(self):
        intent = resolve_intent_deterministic(
            "Quel est le taux de respect des délais SLA ce mois ?",
            self.ref_date,
        )
        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.measure.concept_id, "sla_adherence_rate")

    def test_resolve_deterministic_suggestions_by_impact(self):
        intent = resolve_intent_deterministic(
            "Combien de suggestions selon le niveau d'impact en 2026 ?",
            self.ref_date,
        )
        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.entity.types, ["SUGGESTION"])
        self.assertEqual(intent.measure.concept_id, "suggestion_count")
        self.assertEqual(intent.dimensions[0].concept_id, "impact_level")

    def test_resolve_ambiguous_triggers_needs_clarification(self):
        intent = resolve_intent_deterministic(
            "Donne-moi les réclamations reçues depuis mardi",
            self.ref_date,
        )
        self.assertEqual(intent.status, "needs_clarification")
        self.assertIsNotNone(intent.clarification)
        self.assertEqual(intent.clarification.code, "AMBIGUOUS_TIME_FIELD")
        self.assertIsNone(intent.entity)
        self.assertIsNone(intent.measure)

    def test_resolve_malicious_mutation_triggers_unsupported(self):
        intent = resolve_intent_deterministic(
            "DELETE FROM reporting_claim WHERE id = 1",
            self.ref_date,
        )
        self.assertEqual(intent.status, "unsupported")
        self.assertIn("Opération 'DELETE' non autorisée", intent.unsupported_reason)

    def test_resolve_out_of_scope_triggers_unsupported(self):
        intent = resolve_intent_deterministic(
            "Quel temps fait-il aujourd'hui à Cotonou ?",
            self.ref_date,
        )
        self.assertEqual(intent.status, "unsupported")
        self.assertIn("sort du périmètre", intent.unsupported_reason)

    def test_build_intent_prompt_structure(self):
        prompt = build_intent_prompt("Nombre de réclamations par agence en 2026")
        self.assertIn("Tu ne dois JAMAIS générer de requête SQL", prompt)
        self.assertIn("TextToSQLIntent", prompt)
        self.assertIn("plainte_count", prompt)
        self.assertIn("reclamation_count", prompt)

    def test_parse_intent_response_markdown_json(self):
        fake_llm_json = """```json
{
    "contract_version": "1.0",
    "status": "ready",
    "entity": {
        "concept_id": "plainte",
        "types": ["CLAIM"],
        "include_all_types": false
    },
    "measure": {
        "concept_id": "reclamation_count",
        "operation": "count",
        "target_concept": "plainte",
        "label": "Nombre de réclamations"
    },
    "dimensions": [
        {"concept_id": "agency", "label": "Agence"}
    ],
    "filters": [],
    "time": {
        "field_concept": "receipt_date",
        "start_date": "2026-09-01",
        "end_date": "2026-10-01",
        "timezone": "Africa/Porto-Novo"
    }
}
```"""
        intent = parse_intent_response(fake_llm_json)
        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.measure.concept_id, "reclamation_count")
        self.assertEqual(intent.dimensions[0].concept_id, "agency")
        self.assertEqual(intent.time.start_date, date(2026, 9, 1))

    def test_resolve_intent_unified_entrypoint(self):
        intent = resolve_intent(
            "Nombre de réclamations par canal en 2026",
            self.ref_date,
            use_llm=False,
        )
        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.dimensions[0].concept_id, "channel")


if __name__ == "__main__":
    unittest.main()
