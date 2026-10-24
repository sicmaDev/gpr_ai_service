"""
Tests unitaires pour le Step 5 : Schema Retriever & Génération SQL Nemotron.

Vérifie :
1. La sélection dynamique minimale des tables requises par le Schema Retriever.
2. L'injection automatique des tables passerelles (bridge tables) nécessaires aux jointures.
3. L'étanchéité absolue : aucune donnée sensible dans le sous-schéma transmis au LLM.
4. La construction du prompt Nemotron avec les conventions métier informatives.
5. Le parseur et validateur Pydantic de la réponse candidate (TextToSQLCandidate).
6. Le générateur déterministe hors-ligne (mode test et fallback de résilience).
"""

import unittest
from datetime import date

from pydantic import ValidationError

from app.reporting.schema_retriever import (
    resolve_required_tables,
    retrieve_minimal_subschema,
)
from app.reporting.sql_generator import (
    build_sql_generation_prompt,
    generate_candidate_fallback,
    generate_sql_candidate,
    parse_candidate_response,
)
from app.reporting.text_to_sql_contracts import (
    IntentDimension,
    IntentEntity,
    IntentFilter,
    IntentMeasure,
    IntentTime,
    TextToSQLCandidate,
    TextToSQLIntent,
)


class TestSchemaRetriever(unittest.TestCase):
    def setUp(self):
        self.default_time = IntentTime(
            field_concept="receipt_date",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 1),
            timezone="Africa/Porto-Novo",
        )

    def test_resolve_tables_for_agency_claims(self):
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
            time=self.default_time,
        )

        tables = resolve_required_tables(intent)
        self.assertIn("reporting_claim", tables)
        self.assertIn("reporting_service_point", tables)
        self.assertNotIn("reporting_suggestion", tables)
        self.assertNotIn("reporting_product", tables)

    def test_resolve_tables_injects_bridge_table_for_category(self):
        # Pour ventiler par catégorie, la table passerelle reporting_objet doit être injectée
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[IntentDimension(concept_id="category", label="Catégorie")],
            time=self.default_time,
        )

        tables = resolve_required_tables(intent)
        self.assertIn("reporting_claim", tables)
        self.assertIn("reporting_categorie_objet", tables)
        # TABLE PASSERELLE OBLIGATOIRE
        self.assertIn(
            "reporting_objet",
            tables,
            "La table passerelle reporting_objet DOIT être injectée pour joindre reporting_categorie_objet",
        )

    def test_resolve_tables_for_unified_plaintes(self):
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
            time=self.default_time,
        )

        tables = resolve_required_tables(intent)
        self.assertIn("reporting_claim", tables)
        self.assertIn("reporting_suggestion", tables)

    def test_resolve_tables_for_treatment(self):
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(
                concept_id="treatment",
                types=["CLAIM", "DENUNCIATION", "SUGGESTION"],
                include_all_types=True,
            ),
            measure=IntentMeasure(
                concept_id="reaffectation_count",
                operation="count",
                target_concept="treatment",
                label="Réaffectations",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="created_date",
                start_date=date(2026, 1, 1),
                end_date=date(2027, 1, 1),
                timezone="Africa/Porto-Novo",
            ),
        )

        tables = resolve_required_tables(intent)
        self.assertIn("reporting_historique_affectations", tables)

    def test_retrieve_minimal_subschema_zero_sensitive_data_leak(self):
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
            dimensions=[IntentDimension(concept_id="agency", label="Agence")],
            time=self.default_time,
        )

        tables, subschema_str = retrieve_minimal_subschema(intent)

        self.assertIn("TABLE `reporting_claim`", subschema_str)
        self.assertIn("TABLE `reporting_suggestion`", subschema_str)
        self.assertIn("TABLE `reporting_service_point`", subschema_str)

        # Vérification formelle d'exclusion de toutes les colonnes sensibles
        forbidden_columns = [
            "- `client_code`",
            "- `client_name`",
            "- `phone`",
            "- `evaluator_notes`",
            "- `commentaire`",
            "- `motif_desaprobation`",
            "- `ai_selected_solution`",
        ]
        for col in forbidden_columns:
            self.assertNotIn(
                col,
                subschema_str,
                f"SÉCURITÉ VIOLÉE : la colonne confidentielle {col} apparaît dans le sous-schéma LLM !",
            )


class TestSQLGenerator(unittest.TestCase):
    def setUp(self):
        self.default_intent = TextToSQLIntent(
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

    def test_build_sql_generation_prompt_structure(self):
        _, subschema_str = retrieve_minimal_subschema(self.default_intent)
        prompt = build_sql_generation_prompt(self.default_intent, subschema_str)

        # Vérification des composantes essentielles du prompt
        self.assertIn("INTENTION ANALYTIQUE DE L'UTILISATEUR", prompt)
        self.assertIn("SOUS-SCHÉMA STRICT DE RÉFÉRENCE", prompt)
        self.assertIn("CONSIGNES STRICTES D'ÉCRITURE SQL", prompt)
        self.assertIn("UNIQUEMENT une requête `SELECT`", prompt)
        self.assertIn(":start_date", prompt)
        self.assertIn(":end_date", prompt)
        self.assertIn("TextToSQLCandidate", prompt)
        self.assertIn("CONVENTIONS DE CALCUL MÉTIER DE RÉFÉRENCE", prompt)

    def test_parse_candidate_response_valid_markdown_json(self):
        fake_llm_output = """```json
{
  "contract_version": "1.0",
  "sql": "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY sp.libelle ORDER BY case_count DESC",
  "parameters": {
    "start_date": {"type": "datetime", "source": "intent.time.start_date"},
    "end_date": {"type": "datetime", "source": "intent.time.end_date"}
  },
  "used_schema": ["reporting_claim", "reporting_service_point"],
  "result_columns": [
    {"name": "agency", "concept_id": "agency", "role": "dimension", "data_type": "string"},
    {"name": "case_count", "concept_id": "case_count", "role": "measure", "data_type": "integer"}
  ],
  "assumptions": ["Filtre automatique sur les réclamations validées"]
}
```"""
        candidate = parse_candidate_response(fake_llm_output)
        self.assertIsInstance(candidate, TextToSQLCandidate)
        self.assertEqual(candidate.contract_version, "1.0")
        self.assertIn(":start_date", candidate.sql)
        self.assertEqual(len(candidate.result_columns), 2)
        self.assertEqual(candidate.result_columns[0].name, "agency")
        self.assertEqual(candidate.result_columns[1].name, "case_count")

    def test_parse_candidate_response_rejects_duplicate_result_columns(self):
        invalid_json = """```json
{
  "contract_version": "1.0",
  "sql": "SELECT sp.libelle AS agency, COUNT(c.id) AS agency FROM reporting_claim c",
  "parameters": {},
  "used_schema": ["reporting_claim"],
  "result_columns": [
    {"name": "agency", "concept_id": "agency", "role": "dimension", "data_type": "string"},
    {"name": "agency", "concept_id": "case_count", "role": "measure", "data_type": "integer"}
  ],
  "assumptions": []
}
```"""
        with self.assertRaises(ValidationError):
            parse_candidate_response(invalid_json)

    def test_generate_candidate_fallback_agency_claims(self):
        candidate = generate_candidate_fallback(self.default_intent)

        self.assertIsInstance(candidate, TextToSQLCandidate)
        self.assertIn("SELECT sp.libelle AS agency, COUNT(c.id) AS case_count", candidate.sql)
        self.assertIn("reporting_claim", candidate.used_schema)
        self.assertIn("reporting_service_point", candidate.used_schema)
        self.assertIn("start_date", candidate.parameters)
        self.assertIn("end_date", candidate.parameters)
        self.assertEqual(len(candidate.result_columns), 2)

    def test_generate_candidate_fallback_category_with_joins(self):
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[IntentDimension(concept_id="category", label="Catégorie")],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2027, 1, 1),
                timezone="Africa/Porto-Novo",
            ),
        )

        candidate = generate_candidate_fallback(intent)
        self.assertIn("cat.libelle AS category", candidate.sql)
        self.assertIn("reporting_objet", candidate.used_schema)
        self.assertIn("reporting_categorie_objet", candidate.used_schema)

    def test_generate_candidate_fallback_sla_rate(self):
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="sla_adherence_rate",
                operation="rate",
                target_concept="plainte",
                label="Taux de respect SLA",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=date(2026, 1, 1),
                end_date=date(2027, 1, 1),
                timezone="Africa/Porto-Novo",
            ),
        )

        candidate = generate_candidate_fallback(intent)
        self.assertIn("sla_adherence_rate", candidate.sql)
        self.assertIn("AVG(CASE WHEN c.resolved_at <= c.sla_due_at", candidate.sql)
        self.assertEqual(candidate.result_columns[0].data_type, "decimal")

    def test_generate_sql_candidate_unified_entrypoint(self):
        # Test sans LLM (mode déterministe par défaut)
        candidate = generate_sql_candidate(self.default_intent, use_llm=False)
        self.assertIsInstance(candidate, TextToSQLCandidate)

        # Test avec LLM mocké
        def mock_llm_callable(prompt: str) -> str:
            return """```json
{
  "contract_version": "1.0",
  "sql": "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY sp.libelle ORDER BY case_count DESC",
  "parameters": {
    "start_date": {"type": "datetime", "source": "intent.time.start_date"},
    "end_date": {"type": "datetime", "source": "intent.time.end_date"}
  },
  "used_schema": ["reporting_claim", "reporting_service_point"],
  "result_columns": [
    {"name": "agency", "concept_id": "agency", "role": "dimension", "data_type": "string"},
    {"name": "case_count", "concept_id": "case_count", "role": "measure", "data_type": "integer"}
  ],
  "assumptions": ["Mock generation success"]
}
```"""

        candidate_llm = generate_sql_candidate(
            self.default_intent, use_llm=True, llm_callable=mock_llm_callable
        )
        self.assertIn("Mock generation success", candidate_llm.assumptions)

    def test_generate_candidate_fallback_without_date_and_with_urgency(self):
        intent = TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[],
            filters=[IntentFilter(concept_id="risk_level", operator="equals", value="MINEUR")],
            time=None,
        )
        candidate = generate_candidate_fallback(intent)
        self.assertNotIn(":start_date", candidate.sql)
        self.assertNotIn(":end_date", candidate.sql)
        self.assertIn("c.risk_level = 'MINEUR'", candidate.sql)
    def test_parse_candidate_with_escaped_newlines(self):
        raw_json = (
            '{\n'
            '  "contract_version": "1.0",\n'
            '  "sql": "WITH claim_cnt AS (SELECT COUNT(*) AS cnt FROM reporting_claim),\\\\nsug_cnt AS (SELECT COUNT(*) AS cnt FROM reporting_suggestion)\\\\nSELECT (claim_cnt.cnt + sug_cnt.cnt) AS plainte_count\\\\nFROM claim_cnt, sug_cnt;",\n'
            '  "parameters": {},\n'
            '  "used_schema": ["reporting_claim", "reporting_suggestion"],\n'
            '  "result_columns": [{"name": "plainte_count", "concept_id": "plainte_count", "role": "measure", "data_type": "integer"}],\n'
            '  "assumptions": []\n'
            '}'
        )
        candidate = parse_candidate_response(raw_json)
        self.assertNotIn("\\n", candidate.sql)
        self.assertIn("\n", candidate.sql)
        self.assertIn("WITH claim_cnt", candidate.sql)


if __name__ == "__main__":
    unittest.main()
