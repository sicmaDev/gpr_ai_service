import unittest

from pydantic import ValidationError

from app.reporting.text_to_sql_contracts import TextToSQLCandidate, TextToSQLIntent


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


if __name__ == "__main__":
    unittest.main()
