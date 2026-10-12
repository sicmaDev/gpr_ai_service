"""
Tests unitaires de sécurité et de validation AST pour le Step 6 : Validateur AST SQL (sqlglot).
"""

import unittest
from typing import Set

from app.reporting.query_catalog import get_certified_queries
from app.reporting.sql_validator import (
    get_ast_digest,
    validate_candidate_sql,
    validate_raw_sql,
)
from app.reporting.text_to_sql_contracts import (
    CandidateParameter,
    CandidateResultColumn,
    TextToSQLCandidate,
)


class TestStep6SqlValidator(unittest.TestCase):
    """Suite de tests de sécurité et de conformité du validateur AST."""

    # --------------------------------------------------------------------------
    # 1. Tests des requêtes vides et erreurs de syntaxe
    # --------------------------------------------------------------------------

    def test_empty_or_whitespace_sql(self):
        res = validate_raw_sql("")
        self.assertFalse(res.is_valid)
        self.assertIn("La requete SQL est vide", res.violations)

        res2 = validate_raw_sql("   \n\t  ")
        self.assertFalse(res2.is_valid)
        self.assertIn("La requete SQL est vide", res2.violations)

    def test_syntax_error_sql(self):
        res = validate_raw_sql("SELECT FROM WHERE ;;; INVALID SYNTAX")
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Erreur de syntaxe" in v for v in res.violations))

    # --------------------------------------------------------------------------
    # 2. Tests de multi-statements et injections
    # --------------------------------------------------------------------------

    def test_multi_statement_rejection(self):
        sql = "SELECT count(*) FROM reporting_claim; DROP TABLE reporting_claim;"
        res = validate_raw_sql(sql)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Multi-statements" in v for v in res.violations))

    # --------------------------------------------------------------------------
    # 3. Tests de rejet des mutations DML / DDL / Admin
    # --------------------------------------------------------------------------

    def test_mutation_dml_rejection(self):
        mutations = [
            ("INSERT", "INSERT INTO reporting_claim (id) VALUES (1)"),
            ("UPDATE", "UPDATE reporting_claim SET status = 'RESOLU' WHERE id = 1"),
            ("DELETE", "DELETE FROM reporting_claim WHERE id = 1"),
        ]
        for name, sql in mutations:
            with self.subTest(mutation=name):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(
                    any("seules les requetes SELECT" in v or "interdite" in v for v in res.violations),
                    f"Échec de blocage pour {name}",
                )

    def test_mutation_ddl_rejection(self):
        ddl = [
            ("DROP", "DROP TABLE reporting_claim"),
            ("ALTER", "ALTER TABLE reporting_claim ADD COLUMN test INT"),
            ("TRUNCATE", "TRUNCATE TABLE reporting_claim"),
            ("CREATE", "CREATE TABLE hacked (id INT)"),
        ]
        for name, sql in ddl:
            with self.subTest(ddl=name):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(
                    any("seules les requetes SELECT" in v or "interdite" in v for v in res.violations),
                    f"Échec de blocage pour {name}",
                )

    def test_admin_commands_rejection(self):
        commands = [
            ("GRANT", "GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%'"),
            ("REVOKE", "REVOKE ALL PRIVILEGES ON *.* FROM 'user'@'%'"),
            ("USE", "USE information_schema"),
            ("SET", "SET @hacked = 1"),
            ("SHOW", "SHOW TABLES"),
        ]
        for name, sql in commands:
            with self.subTest(command=name):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)

    # --------------------------------------------------------------------------
    # 4. Tests de restriction des tables (Système, Inconnues, Non-analytiques)
    # --------------------------------------------------------------------------

    def test_system_schemas_rejection(self):
        system_queries = [
            "SELECT table_name FROM information_schema.tables",
            "SELECT user, host FROM mysql.user",
            "SELECT * FROM performance_schema.threads",
            "SELECT * FROM sys.processlist",
        ]
        for sql in system_queries:
            with self.subTest(sql=sql):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(any("systeme" in v or "interdit" in v for v in res.violations))

    def test_unauthorized_production_tables(self):
        prod_tables = [
            "SELECT count(*) FROM gps_claims",
            "SELECT count(*) FROM gps_users",
            "SELECT count(*) FROM users",
        ]
        for sql in prod_tables:
            with self.subTest(sql=sql):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(any("non autorisee ou inconnue" in v for v in res.violations))

    def test_allowed_tables_enforcement(self):
        sql = "SELECT c.id, sp.libelle FROM reporting_claim c JOIN reporting_service_point sp ON c.service_point_id = sp.id"
        # Autoriser uniquement reporting_claim (sans service_point)
        res = validate_raw_sql(sql, allowed_tables={"reporting_claim"})
        self.assertFalse(res.is_valid)
        self.assertTrue(any("hors du sous-schema minimal" in v for v in res.violations))

    # --------------------------------------------------------------------------
    # 5. Tests de protection des colonnes confidentielles et wildcards
    # --------------------------------------------------------------------------

    def test_sensitive_columns_direct(self):
        sensitive_queries = [
            ("client_code", "SELECT client_code FROM reporting_claim"),
            ("content", "SELECT content FROM reporting_claim"),
            ("solution", "SELECT solution FROM reporting_claim"),
            ("email", "SELECT email FROM reporting_suggestion"),
            ("evaluator_notes", "SELECT evaluator_notes FROM reporting_suggestion"),
        ]
        for col_name, sql in sensitive_queries:
            with self.subTest(col=col_name):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(
                    any("colonne sensible" in v for v in res.violations),
                    f"La colonne sensible {col_name} n'a pas été bloquée",
                )

    def test_sensitive_columns_with_table_prefix(self):
        sql = "SELECT c.id, c.content FROM reporting_claim c"
        res = validate_raw_sql(sql)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("reporting_claim.content" in v for v in res.violations))

    def test_wildcard_star_rejection(self):
        queries = [
            "SELECT * FROM reporting_claim",
            "SELECT c.* FROM reporting_claim c",
            "SELECT 1, * FROM reporting_claim",
        ]
        for sql in queries:
            with self.subTest(sql=sql):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(any("Projection wildcard '*'" in v for v in res.violations))

    def test_wildcard_star_allowed_in_count(self):
        sql = "SELECT COUNT(*) AS total FROM reporting_claim WHERE claim_type = 'CLAIM'"
        res = validate_raw_sql(sql)
        self.assertTrue(res.is_valid, f"Violations inattendues : {res.violations}")
        self.assertEqual(len(res.violations), 0)

    # --------------------------------------------------------------------------
    # 6. Tests des fonctions interdites
    # --------------------------------------------------------------------------

    def test_forbidden_functions(self):
        functions = [
            ("SLEEP", "SELECT count(*) FROM reporting_claim WHERE SLEEP(5) = 0"),
            ("BENCHMARK", "SELECT count(*) FROM reporting_claim WHERE BENCHMARK(1000000, 1) = 0"),
            ("USER", "SELECT USER(), count(*) FROM reporting_claim"),
            ("VERSION", "SELECT VERSION(), count(*) FROM reporting_claim"),
            ("DATABASE", "SELECT DATABASE(), count(*) FROM reporting_claim"),
        ]
        for name, sql in functions:
            with self.subTest(func=name):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertTrue(
                    any("Fonction interdite" in v for v in res.violations),
                    f"Fonction {name} non détectée",
                )

    # --------------------------------------------------------------------------
    # 7. Tests d'intégrité des jointures (Join Integrity)
    # --------------------------------------------------------------------------

    def test_join_types_restriction(self):
        illegal_joins = [
            ("RIGHT", "SELECT c.id FROM reporting_claim c RIGHT JOIN reporting_service_point sp ON c.service_point_id = sp.id"),
            ("CROSS", "SELECT c.id FROM reporting_claim c CROSS JOIN reporting_service_point sp"),
        ]
        for name, sql in illegal_joins:
            with self.subTest(join=name):
                res = validate_raw_sql(sql)
                self.assertFalse(res.is_valid)
                self.assertFalse(res.join_integrity_checked)

    def test_join_integrity_valid_relationships(self):
        valid_joins = [
            "SELECT c.id, sp.libelle FROM reporting_claim c INNER JOIN reporting_service_point sp ON c.service_point_id = sp.id",
            "SELECT c.id, cc.libelle FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id",
            "SELECT c.id, p.libelle FROM reporting_claim c LEFT JOIN reporting_product p ON c.product_id = p.id",
            "SELECT c.id, o.libelle FROM reporting_claim c LEFT JOIN reporting_objet o ON c.objet_id = o.id",
        ]
        for sql in valid_joins:
            with self.subTest(sql=sql):
                res = validate_raw_sql(sql)
                self.assertTrue(res.is_valid, f"Violations inattendues pour jointure valide : {res.violations}")
                self.assertTrue(res.join_integrity_checked)

    def test_join_integrity_invalid_relationship(self):
        # Jointure arbitraire inexistante : reporting_claim et reporting_poste
        sql = "SELECT c.id FROM reporting_claim c JOIN reporting_poste p ON c.id = p.id"
        res = validate_raw_sql(sql)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.join_integrity_checked)
        self.assertTrue(any("Jointure non autorisee" in v for v in res.violations))

    # --------------------------------------------------------------------------
    # 8. Tests CTEs et Sous-requêtes read-only
    # --------------------------------------------------------------------------

    def test_cte_read_only_allowed(self):
        sql = """
        WITH agency_stats AS (
            SELECT c.service_point_id, COUNT(c.id) AS total_count
            FROM reporting_claim c
            WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date
            GROUP BY c.service_point_id
        )
        SELECT sp.libelle AS agency, ast.total_count
        FROM agency_stats ast
        JOIN reporting_service_point sp ON ast.service_point_id = sp.id
        ORDER BY ast.total_count DESC
        """
        res = validate_raw_sql(sql)
        self.assertTrue(res.is_valid, f"Violations pour CTE valide : {res.violations}")

    # --------------------------------------------------------------------------
    # 9. Validation intégrale des 8 requêtes certifiées de QueryCatalog
    # --------------------------------------------------------------------------

    def test_all_8_certified_queries_pass_validation(self):
        queries = get_certified_queries()
        self.assertEqual(len(queries), 8)
        for qid, q in queries.items():
            with self.subTest(query_id=qid):
                res = validate_raw_sql(q.parameterized_sql)
                self.assertTrue(
                    res.is_valid,
                    f"Requête certifiée {qid} rejetée par le validateur AST : {res.violations}",
                )
                self.assertIsNotNone(res.ast_digest)
                self.assertTrue(len(res.allowed_tables_checked) > 0)

    # --------------------------------------------------------------------------
    # 10. Tests de validate_candidate_sql avec TextToSQLCandidate
    # --------------------------------------------------------------------------

    def test_candidate_sql_validation_success(self):
        candidate = TextToSQLCandidate(
            sql="SELECT sp.libelle AS agency, COUNT(c.id) AS case_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY sp.libelle ORDER BY case_count DESC",
            parameters={
                "start_date": CandidateParameter(type="datetime", source="time.start"),
                "end_date": CandidateParameter(type="datetime", source="time.end"),
            },
            used_schema=["reporting_claim.service_point_id", "reporting_service_point.libelle"],
            result_columns=[
                CandidateResultColumn(name="agency", concept_id="agency", role="dimension", data_type="string"),
                CandidateResultColumn(name="case_count", concept_id="reclamation_count", role="measure", data_type="integer"),
            ],
            assumptions=[],
        )
        res = validate_candidate_sql(candidate)
        self.assertTrue(res.is_valid, f"Violations : {res.violations}")
        self.assertEqual(len(res.violations), 0)

    def test_candidate_sql_validation_missing_parameter(self):
        # Le SQL contient :end_date mais le contrat ne déclare que start_date
        candidate = TextToSQLCandidate(
            sql="SELECT COUNT(c.id) AS total FROM reporting_claim c WHERE c.receipt_at >= :start_date AND c.receipt_at < :end_date",
            parameters={
                "start_date": CandidateParameter(type="datetime", source="time.start"),
            },
            used_schema=["reporting_claim.receipt_at"],
            result_columns=[
                CandidateResultColumn(name="total", concept_id="reclamation_count", role="measure", data_type="integer"),
            ],
            assumptions=[],
        )
        res = validate_candidate_sql(candidate)
        self.assertFalse(res.is_valid)
        self.assertTrue(any(":end_date" in v for v in res.violations))

    def test_ast_digest_utility(self):
        digest = get_ast_digest("SELECT count(*) FROM reporting_claim WHERE id = 1;")
        self.assertEqual(digest, "SELECT COUNT(*) FROM reporting_claim WHERE id = 1")

        invalid_digest = get_ast_digest("SELECT FROM WHERE")
        self.assertEqual(invalid_digest, "INVALID_AST")


if __name__ == "__main__":
    unittest.main()
