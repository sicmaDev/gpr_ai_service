"""
Tests unitaires pour le Schema Catalog et le Business Catalog (Step 3).

Vérifie :
1. L'intégrité structurelle et relationnelle du Schema Catalog (13 tables + 2 admin).
2. Le marquage strict de toutes les colonnes sensibles.
3. L'exclusion absolue des données sensibles dans le sous-schéma minimal (get_minimal_subschema).
4. La cohérence des clés étrangères et des relations autorisées.
5. La complétude du Business Catalog (10 métriques, dimensions, concepts).
6. La résolution robuste des synonymes en langue naturelle avec gestion des accents.
"""

import unittest

from app.reporting.business_catalog import (
    BUSINESS_CATALOG,
    get_business_catalog,
    resolve_synonym,
)
from app.reporting.schema_catalog import (
    SCHEMA_CATALOG,
    get_minimal_subschema,
    get_schema_catalog,
)


class TestSchemaCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = get_schema_catalog()

    def test_schema_catalog_identity(self):
        self.assertEqual(self.catalog.schema_version, "1.0.0")
        self.assertEqual(self.catalog.database_name, "gpr_ai_reporting")
        self.assertIs(self.catalog, SCHEMA_CATALOG)

    def test_all_expected_tables_are_registered(self):
        expected_tables = {
            # Tables de faits
            "reporting_claim",
            "reporting_suggestion",
            # Tables de workflow
            "reporting_historique_affectations",
            "reporting_solution",
            "reporting_satisfaction_measure",
            # Tables de dimensions
            "reporting_existing_solution",
            "reporting_product",
            "reporting_service_point",
            "reporting_categorie_objet",
            "reporting_objet",
            "reporting_collection_channel",
            "reporting_user",
            "reporting_poste",
            # Tables d'administration
            "reporting_sync_state",
            "reporting_alert",
        }
        actual_tables = set(self.catalog.tables.keys())
        self.assertTrue(expected_tables.issubset(actual_tables))

    def test_primary_keys_declared_and_valid(self):
        for table_name, table in self.catalog.tables.items():
            self.assertIn(
                table.primary_key,
                table.columns,
                f"La clé primaire {table.primary_key} de {table_name} doit être dans ses colonnes",
            )
            pk_col = table.columns[table.primary_key]
            self.assertTrue(
                pk_col.is_primary_key,
                f"La colonne {table.primary_key} de {table_name} doit avoir is_primary_key=True",
            )
            self.assertFalse(
                pk_col.is_nullable,
                f"La clé primaire {table.primary_key} de {table_name} ne peut pas être nullable",
            )

    def test_sensitive_columns_marked_strictly(self):
        # 1. reporting_claim
        claim_sensitive = {"client_code", "content", "solution"}
        for col_name in claim_sensitive:
            self.assertIn(col_name, self.catalog.tables["reporting_claim"].columns)
            self.assertTrue(
                self.catalog.tables["reporting_claim"].columns[col_name].is_sensitive,
                f"reporting_claim.{col_name} DOIT être marquée sensible",
            )

        # 2. reporting_suggestion
        suggestion_sensitive = {
            "client_code",
            "client_name",
            "phone",
            "email",
            "description",
            "evaluator_notes",
        }
        for col_name in suggestion_sensitive:
            self.assertIn(col_name, self.catalog.tables["reporting_suggestion"].columns)
            self.assertTrue(
                self.catalog.tables["reporting_suggestion"].columns[col_name].is_sensitive,
                f"reporting_suggestion.{col_name} DOIT être marquée sensible",
            )

        # 3. reporting_solution
        solution_sensitive = {"commentaire", "motif_desaprobation", "ai_selected_solution"}
        for col_name in solution_sensitive:
            self.assertIn(col_name, self.catalog.tables["reporting_solution"].columns)
            self.assertTrue(
                self.catalog.tables["reporting_solution"].columns[col_name].is_sensitive,
                f"reporting_solution.{col_name} DOIT être marquée sensible",
            )

        # 4. reporting_satisfaction_measure
        self.assertTrue(
            self.catalog.tables["reporting_satisfaction_measure"].columns["commentaire"].is_sensitive,
            "reporting_satisfaction_measure.commentaire DOIT être marquée sensible",
        )

    def test_relationships_referential_integrity(self):
        self.assertGreaterEqual(len(self.catalog.relationships), 15)

        for rel in self.catalog.relationships:
            # Source
            self.assertIn(
                rel.source_table,
                self.catalog.tables,
                f"Relation {rel.name} : table source {rel.source_table} inexistante",
            )
            self.assertIn(
                rel.source_column,
                self.catalog.tables[rel.source_table].columns,
                f"Relation {rel.name} : colonne source {rel.source_column} inexistante dans {rel.source_table}",
            )
            # Target
            self.assertIn(
                rel.target_table,
                self.catalog.tables,
                f"Relation {rel.name} : table cible {rel.target_table} inexistante",
            )
            self.assertIn(
                rel.target_column,
                self.catalog.tables[rel.target_table].columns,
                f"Relation {rel.name} : colonne cible {rel.target_column} inexistante dans {rel.target_table}",
            )
            # Join Type
            self.assertIn(rel.join_type, ["INNER JOIN", "LEFT JOIN"])

    def test_minimal_subschema_never_contains_sensitive_columns(self):
        # 1. Vérification par table spécifique
        claim_subschema = get_minimal_subschema(["reporting_claim"])
        for token in ["- `client_code`", "- `content`", "- `solution`"]:
            self.assertNotIn(
                token,
                claim_subschema,
                f"FUITE DE SÉCURITÉ : {token} apparaît dans le sous-schéma de reporting_claim !",
            )

        suggestion_subschema = get_minimal_subschema(["reporting_suggestion"])
        for token in [
            "- `client_code`",
            "- `client_name`",
            "- `phone`",
            "- `email`",
            "- `description`",
            "- `evaluator_notes`",
        ]:
            self.assertNotIn(
                token,
                suggestion_subschema,
                f"FUITE DE SÉCURITÉ : {token} apparaît dans le sous-schéma de reporting_suggestion !",
            )

        solution_subschema = get_minimal_subschema(["reporting_solution"])
        for token in ["- `commentaire`", "- `motif_desaprobation`", "- `ai_selected_solution`"]:
            self.assertNotIn(
                token,
                solution_subschema,
                f"FUITE DE SÉCURITÉ : {token} apparaît dans le sous-schéma de reporting_solution !",
            )

        satisfaction_subschema = get_minimal_subschema(["reporting_satisfaction_measure"])
        self.assertNotIn(
            "- `commentaire`",
            satisfaction_subschema,
            "FUITE DE SÉCURITÉ : - `commentaire` apparaît dans reporting_satisfaction_measure !",
        )

        # 2. Vérification sur le sous-schéma global
        subschema = get_minimal_subschema()
        global_forbidden = [
            "- `client_code`",
            "- `client_name`",
            "- `phone`",
            "- `evaluator_notes`",
            "- `commentaire`",
            "- `motif_desaprobation`",
            "- `ai_selected_solution`",
        ]
        for token in global_forbidden:
            self.assertNotIn(
                token,
                subschema,
                f"FUITE DE SÉCURITÉ : {token} apparaît dans le sous-schéma global !",
            )

        # Vérification de la présence des colonnes publiques autorisées
        allowed_tokens = [
            "- `source_code`",
            "- `claim_type`",
            "- `status`",
            "- `receipt_at`",
            "- `sla_due_at`",
            "- `risk_level`",
            "- `impact_level`",
            "- `title`",
            "- `recorded_at`",
        ]
        for token in allowed_tokens:
            self.assertIn(
                token,
                subschema,
                f"La colonne analytique attendue {token} doit être présente dans le sous-schéma",
            )

    def test_minimal_subschema_targeted_selection(self):
        # Sous-schéma restreint à reporting_claim et reporting_service_point
        subschema = get_minimal_subschema(["reporting_claim", "reporting_service_point"])

        self.assertIn("TABLE `reporting_claim`", subschema)
        self.assertIn("TABLE `reporting_service_point`", subschema)
        self.assertNotIn("TABLE `reporting_suggestion`", subschema)
        self.assertNotIn("TABLE `reporting_product`", subschema)
        # Jointure attendue entre ces deux tables
        self.assertIn("claim_to_agency", subschema)


class TestBusinessCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = get_business_catalog()

    def test_business_catalog_identity(self):
        self.assertEqual(self.catalog.catalog_version, "1.0.0")
        self.assertIs(self.catalog, BUSINESS_CATALOG)

    def test_all_10_certified_metrics_are_registered(self):
        expected_metrics = [
            "plainte_count",
            "reclamation_count",
            "denonciation_count",
            "suggestion_count",
            "sla_adherence_rate",
            "avg_processing_time",
            "satisfaction_rate",
            "severe_plainte_count",
            "adoption_rate",
            "reaffectation_count",
        ]
        for metric_id in expected_metrics:
            self.assertIn(metric_id, self.catalog.metrics)
            metric = self.catalog.metrics[metric_id]
            self.assertTrue(len(metric.required_tables) > 0)
            self.assertTrue(len(metric.aggregation_sql_template) > 0)

    def test_unified_plainte_count_requires_claims_and_suggestions(self):
        unified_metric = self.catalog.metrics["plainte_count"]
        self.assertIn("reporting_claim", unified_metric.required_tables)
        self.assertIn("reporting_suggestion", unified_metric.required_tables)
        self.assertIn("reporting_claim", unified_metric.aggregation_sql_template)
        self.assertIn("reporting_suggestion", unified_metric.aggregation_sql_template)

    def test_all_10_dimensions_are_registered(self):
        expected_dimensions = [
            "agency",
            "channel",
            "product",
            "category",
            "object",
            "status",
            "risk_level",
            "impact_level",
            "agent",
            "period",
        ]
        for dim_id in expected_dimensions:
            self.assertIn(dim_id, self.catalog.dimensions)
            dim = self.catalog.dimensions[dim_id]
            self.assertTrue(len(dim.source_table) > 0)
            self.assertTrue(len(dim.source_column) > 0)

    def test_all_5_business_concepts_are_registered(self):
        expected_concepts = [
            "plainte",
            "reclamation",
            "denonciation",
            "suggestion",
            "treatment",
        ]
        for c_id in expected_concepts:
            self.assertIn(c_id, self.catalog.concepts)
            concept = self.catalog.concepts[c_id]
            self.assertTrue(len(concept.target_table) > 0)

    def test_resolve_synonyms_exact_and_variations(self):
        # Concepts et entités
        self.assertEqual(resolve_synonym("plainte"), "plainte")
        self.assertEqual(resolve_synonym("plaintes"), "plainte")
        self.assertEqual(resolve_synonym("dossiers"), "plainte")
        self.assertEqual(resolve_synonym("requêtes"), "plainte")

        # Sous-types de plaintes
        self.assertEqual(resolve_synonym("réclamation"), "reclamation")
        self.assertEqual(resolve_synonym("réclamations"), "reclamation")
        self.assertEqual(resolve_synonym("doleances"), "reclamation")
        self.assertEqual(resolve_synonym("dénonciation"), "denonciation")
        self.assertEqual(resolve_synonym("dénonciations"), "denonciation")
        self.assertEqual(resolve_synonym("fraudes"), "denonciation")
        self.assertEqual(resolve_synonym("signalements"), "denonciation")
        self.assertEqual(resolve_synonym("suggestion"), "suggestion")
        self.assertEqual(resolve_synonym("idées"), "suggestion")
        self.assertEqual(resolve_synonym("propositions"), "suggestion")

        # Dimensions & métriques
        self.assertEqual(resolve_synonym("agence"), "agency")
        self.assertEqual(resolve_synonym("agences"), "agency")
        self.assertEqual(resolve_synonym("guichet"), "agency")
        self.assertEqual(resolve_synonym("canal"), "channel")
        self.assertEqual(resolve_synonym("canaux"), "channel")
        self.assertEqual(resolve_synonym("respect sla"), "sla_adherence_rate")
        self.assertEqual(resolve_synonym("satisfaction"), "satisfaction_rate")
        self.assertEqual(resolve_synonym("grave"), "severe")
        self.assertEqual(resolve_synonym("critiques"), "severe")

    def test_resolve_synonyms_edge_cases(self):
        self.assertIsNone(resolve_synonym(""))
        self.assertIsNone(resolve_synonym("terme_completement_inconnu_xyz"))
        self.assertEqual(resolve_synonym("  RÉCLAMATIONS  "), "reclamation")


if __name__ == "__main__":
    unittest.main()
