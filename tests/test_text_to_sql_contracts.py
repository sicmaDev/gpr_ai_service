import unittest

from pydantic import ValidationError

from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    BusinessCatalog,
    BusinessConcept,
    ColumnMetadata,
    DimensionDefinition,
    MetricDefinition,
    QueryCatalogEntry,
    RelationshipMetadata,
    SchemaCatalog,
    SqlValidationResult,
    TableMetadata,
    TextToSQLCandidate,
    TextToSQLIntent,
)


def ready_intent():
    return {
        "contract_version": "1.0",
        "status": "ready",
        "entity": {
            "concept_id": "case",
            "types": ["CLAIM"],
            "include_all_types": False,
        },
        "measure": {
            "concept_id": "case_count",
            "operation": "count",
            "target_concept": "case",
            "label": "Nombre de dossiers",
        },
        "dimensions": [{"concept_id": "agency", "label": "Agence"}],
        "filters": [
            {
                "concept_id": "status",
                "operator": "equals",
                "value": "TREAT",
                "values": None,
            }
        ],
        "time": {
            "field_concept": "receipt_date",
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "timezone": "Africa/Porto-Novo",
        },
        "clarification": None,
        "unsupported_reason": None,
    }


class TextToSQLContractTests(unittest.TestCase):
    def test_valid_ready_intent(self):
        intent = TextToSQLIntent(**ready_intent())

        self.assertEqual(intent.status, "ready")
        self.assertEqual(intent.time.start_date.isoformat(), "2026-09-01")

    def test_valid_clarification_response(self):
        intent = TextToSQLIntent(
            contract_version="1.0",
            status="needs_clarification",
            entity=None,
            measure=None,
            dimensions=[],
            filters=[],
            time=None,
            clarification={
                "code": "AMBIGUOUS_TIME_FIELD",
                "message": "La date de la mesure n'est pas precisee.",
                "question": "Quelle date souhaitez-vous utiliser ?",
            },
            unsupported_reason=None,
        )

        self.assertEqual(intent.clarification.code, "AMBIGUOUS_TIME_FIELD")

    def test_rejects_unsupported_dimensions(self):
        payload = ready_intent()
        payload["dimensions"][0]["concept_id"] = "team"

        with self.assertRaises(ValidationError):
            TextToSQLIntent(**payload)

    def test_rejects_invalid_filter_shape(self):
        payload = ready_intent()
        payload["filters"][0].update(
            {"operator": "in", "value": "TREAT", "values": ["TREAT"]}
        )

        with self.assertRaises(ValidationError):
            TextToSQLIntent(**payload)

    def test_rejects_invalid_time_range(self):
        payload = ready_intent()
        payload["time"].update(
            {"start_date": "2026-09-30", "end_date": "2026-09-01"}
        )

        with self.assertRaises(ValidationError):
            TextToSQLIntent(**payload)

    def test_rejects_ready_intent_without_measure(self):
        payload = ready_intent()
        payload["measure"] = None

        with self.assertRaises(ValidationError):
            TextToSQLIntent(**payload)

    def test_valid_sql_candidate_contract(self):
        candidate = TextToSQLCandidate(
            contract_version="1.0",
            sql=(
                "SELECT agency, COUNT(*) AS case_count "
                "FROM reporting_claim WHERE receipt_at >= :start_date "
                "GROUP BY agency"
            ),
            parameters={
                "start_date": {"type": "datetime", "source": "intent.time.start_date"}
            },
            used_schema=["reporting_claim.agency", "reporting_claim.receipt_at"],
            result_columns=[
                {
                    "name": "agency",
                    "concept_id": "agency",
                    "role": "dimension",
                    "data_type": "string",
                },
                {
                    "name": "case_count",
                    "concept_id": "case_count",
                    "role": "measure",
                    "data_type": "integer",
                },
            ],
            assumptions=[],
        )

        self.assertEqual(candidate.parameters["start_date"].type, "datetime")

    def test_rejects_duplicate_result_aliases(self):
        payload = {
            "contract_version": "1.0",
            "sql": "SELECT 1",
            "parameters": {},
            "used_schema": [],
            "result_columns": [
                {
                    "name": "value",
                    "concept_id": "first",
                    "role": "measure",
                    "data_type": "integer",
                },
                {
                    "name": "value",
                    "concept_id": "second",
                    "role": "measure",
                    "data_type": "integer",
                },
            ],
            "assumptions": [],
        }

        with self.assertRaises(ValidationError):
            TextToSQLCandidate(**payload)

    def test_plainte_all_types_intent(self):
        payload = ready_intent()
        payload["entity"] = {
            "concept_id": "plainte",
            "types": ["CLAIM", "DENUNCIATION", "SUGGESTION"],
            "include_all_types": True,
        }
        payload["measure"]["concept_id"] = "plainte_count"
        payload["measure"]["target_concept"] = "plainte"
        intent = TextToSQLIntent(**payload)

        self.assertTrue(intent.entity.include_all_types)
        self.assertEqual(len(intent.entity.types), 3)
        self.assertEqual(intent.measure.concept_id, "plainte_count")

    def test_suggestion_specific_intent(self):
        payload = ready_intent()
        payload["entity"] = {
            "concept_id": "plainte",
            "types": ["SUGGESTION"],
            "include_all_types": False,
        }
        payload["measure"]["concept_id"] = "suggestion_count"
        payload["dimensions"] = [{"concept_id": "impact_level", "label": "Niveau d'impact"}]
        intent = TextToSQLIntent(**payload)

        self.assertFalse(intent.entity.include_all_types)
        self.assertEqual(intent.entity.types, ["SUGGESTION"])
        self.assertEqual(intent.dimensions[0].concept_id, "impact_level")

    def test_filter_between_operator(self):
        payload = ready_intent()
        payload["filters"] = [
            {
                "concept_id": "risk_level",
                "operator": "between",
                "value": None,
                "values": ["MINEUR", "GRAVE"],
            }
        ]
        intent = TextToSQLIntent(**payload)
        self.assertEqual(intent.filters[0].operator, "between")
        self.assertEqual(len(intent.filters[0].values), 2)

    def test_schema_catalog_validation_and_sensitive_column(self):
        col_id = ColumnMetadata(
            name="id",
            data_type="BIGINT",
            is_primary_key=True,
            description="Identifiant technique interne",
        )
        col_client = ColumnMetadata(
            name="client_code",
            data_type="VARCHAR",
            is_sensitive=True,
            description="Identifiant client nominatif protege",
        )
        table = TableMetadata(
            name="reporting_claim",
            table_type="fact",
            primary_key="id",
            description="Table pivot des réclamations et dénonciations",
            columns={"id": col_id, "client_code": col_client},
        )
        rel = RelationshipMetadata(
            name="claim_to_service_point",
            source_table="reporting_claim",
            source_column="service_point_id",
            target_table="reporting_service_point",
            target_column="id",
            join_type="LEFT JOIN",
            description="Liaison vers l'agence bancaire",
        )
        catalog = SchemaCatalog(
            schema_version="1.0.0",
            database_name="gpr_ai_reporting",
            tables={"reporting_claim": table},
            relationships=[rel],
        )

        self.assertEqual(catalog.schema_version, "1.0.0")
        self.assertTrue(catalog.tables["reporting_claim"].columns["client_code"].is_sensitive)
        self.assertEqual(catalog.relationships[0].join_type, "LEFT JOIN")

    def test_business_catalog_definition(self):
        metric = MetricDefinition(
            metric_id="claim_count",
            label="Nombre total de réclamations",
            description="Comptage exhaustif des dossiers hors brouillons",
            required_tables=["reporting_claim"],
            aggregation_sql_template="COUNT(reporting_claim.id)",
        )
        dimension = DimensionDefinition(
            dimension_id="agency",
            label="Agence bancaire",
            source_table="reporting_service_point",
            source_column="libelle",
            join_path="reporting_claim.service_point_id = reporting_service_point.id",
        )
        concept = BusinessConcept(
            concept_id="plainte",
            label="Plaintes globales",
            description="Ensemble unifié des dossiers (réclamations, dénonciations, suggestions)",
            target_table="reporting_claim",
            target_columns=["id", "claim_type", "status"],
        )
        catalog = BusinessCatalog(
            catalog_version="1.0.0",
            metrics={"claim_count": metric},
            dimensions={"agency": dimension},
            synonyms={"plaintes": ["dossiers", "requetes"]},
        )

        self.assertIn("claim_count", catalog.metrics)
        self.assertEqual(catalog.dimensions["agency"].source_column, "libelle")

    def test_sql_validation_result_contract(self):
        result = SqlValidationResult(
            is_valid=True,
            ast_digest="SELECT agency, COUNT(*) FROM reporting_claim GROUP BY agency",
            allowed_tables_checked=["reporting_claim"],
            allowed_columns_checked=["agency"],
            join_integrity_checked=True,
            violations=[],
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.violations), 0)

    def test_query_catalog_lifecycle(self):
        intent = TextToSQLIntent(**ready_intent())
        entry = QueryCatalogEntry(
            id="QC-TEST-001",
            contract_version="1.0",
            natural_language_query="Combien de réclamations par agence en septembre ?",
            canonical_intent=intent,
            parameterized_sql="SELECT agency, COUNT(*) FROM reporting_claim GROUP BY agency",
            parameters_schema={},
            status=ApprovalStatus.PENDING,
            created_by="Nemotron",
            schema_version="1.0.0",
        )
        self.assertEqual(entry.status, ApprovalStatus.PENDING)

        entry.status = ApprovalStatus.APPROVED
        entry.approved_by = "admin_supervisor"
        self.assertEqual(entry.status, ApprovalStatus.APPROVED)
        self.assertEqual(entry.approved_by, "admin_supervisor")


if __name__ == "__main__":
    unittest.main()
