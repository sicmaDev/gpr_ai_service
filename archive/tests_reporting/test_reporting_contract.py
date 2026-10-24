import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.reporting.schemas import (
    ChartDataset,
    DashboardMetrics,
    DashboardResponse,
    ReportingFilters,
    ReportingComparison,
    ReportingQueryRequest,
    Visualization,
)
from app.reporting.query import parse_intent
from app.reporting.llm import _validated_payload, interpret_question
from app.reporting.catalog import (
    ANALYTIC_CATALOG,
    BUSINESS_CONDITIONS,
    CATALOG_VERSION,
    TARGETS,
    validate_analysis,
    validate_grouping,
)
from app.reporting.periods import resolve_period


class ReportingContractTests(unittest.TestCase):
    def test_filters_normalize_values_and_dates(self):
        filters = ReportingFilters(
            start_date="2026-09-01",
            end_date="2026-09-03",
            claim_type=" claim ",
            risk_level="grave",
        )

        self.assertEqual(filters.claim_type, "CLAIM")
        self.assertEqual(filters.risk_level, "GRAVE")
        self.assertEqual(filters.start_date, date(2026, 9, 1))

    def test_filters_reject_invalid_date_range(self):
        with self.assertRaises(ValidationError):
            ReportingFilters(start_date="2026-09-04", end_date="2026-09-03")

    def test_filters_reject_unsupported_values(self):
        with self.assertRaises(ValidationError):
            ReportingFilters(claim_type="SUGGESTION")
        with self.assertRaises(ValidationError):
            ReportingFilters(risk_level="high")

    def test_query_normalizes_question(self):
        request = ReportingQueryRequest(question="  Quels produits ?  ")
        self.assertEqual(request.question, "Quels produits ?")

    def test_visualization_accepts_front_chart_types(self):
        visualization = Visualization(
            type="BAR",
            labels=["Web"],
            datasets=[ChartDataset(label="Dossiers", data=[1])],
        )
        self.assertEqual(visualization.type, "bar")

    def test_dashboard_response_serializes_contract(self):
        response = DashboardResponse(
            metrics=DashboardMetrics(total_claims=1),
            generated_at=datetime(2026, 9, 14, 10, 0),
        )
        self.assertEqual(response.metrics.total_claims, 1)

    def test_query_intent_is_serializable_and_extracts_filters(self):
        result = parse_intent(
            "Combien de dossiers graves en retard par agence de ABIDJAN ?",
            today=date(2026, 9, 21),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.metric, "count_overdue")
        self.assertEqual(result.intent.group_by, "agency")
        self.assertEqual(result.intent.filters.risk_level, "GRAVE")
        self.assertEqual(result.intent.filters.agency, "ABIDJAN")
        serialized = (
            result.intent.model_dump()
            if hasattr(result.intent, "model_dump")
            else result.intent.dict()
        )
        self.assertEqual(serialized["metric"], "count_overdue")

    def test_query_intent_rejects_unsupported_analysis(self):
        result = parse_intent("Supprime les alertes du mois prochain")

        self.assertFalse(result.supported)
        self.assertIsNone(result.intent)
        self.assertIn("non supportee", result.reason)

    def test_query_intent_extracts_named_month(self):
        result = parse_intent(
            "Combien de dossiers en septembre 2026 ?",
            today=date(2026, 9, 21),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.filters.start_date, date(2026, 9, 1))
        self.assertEqual(result.intent.filters.end_date, date(2026, 9, 30))

    def test_query_intent_extracts_current_month_and_plainte(self):
        result = parse_intent(
            "Quel est le nombre de plainte ce moi ci ?",
            today=date(2026, 9, 24),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.metric, "count")
        self.assertEqual(result.intent.filters.claim_type, "CLAIM")
        self.assertEqual(result.intent.filters.start_date, date(2026, 9, 1))
        self.assertEqual(result.intent.filters.end_date, date(2026, 9, 24))

    def test_semantic_current_month_is_resolved_by_backend(self):
        self.assertEqual(
            resolve_period("current_month", date(2026, 9, 24)),
            (date(2026, 9, 1), date(2026, 9, 24)),
        )

    def test_query_intent_extracts_explicit_date_interval(self):
        result = parse_intent(
            "Combien de dossiers du 1 au 15 septembre 2026 ?",
            today=date(2026, 9, 21),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.filters.start_date, date(2026, 9, 1))
        self.assertEqual(result.intent.filters.end_date, date(2026, 9, 15))

    def test_query_intent_compares_named_months(self):
        result = parse_intent(
            "Compare septembre 2026 avec août 2026 par agence",
            today=date(2026, 9, 21),
        )

        comparison = result.intent.comparison
        self.assertTrue(result.supported)
        self.assertEqual(result.intent.group_by, "agency")
        self.assertEqual(comparison.current_start_date, date(2026, 9, 1))
        self.assertEqual(comparison.current_end_date, date(2026, 9, 30))
        self.assertEqual(comparison.previous_start_date, date(2026, 8, 1))
        self.assertEqual(comparison.previous_end_date, date(2026, 8, 31))

    def test_query_intent_does_not_treat_comparison_period_as_agency(self):
        result = parse_intent(
            "Compare le nombre de dossiers graves en retard par agence entre septembre 2026 et août 2026.",
            today=date(2026, 9, 21),
        )

        self.assertTrue(result.supported)
        self.assertIsNone(result.intent.filters.agency)
        self.assertEqual(result.intent.group_by, "agency")

    def test_query_intent_compares_explicit_date_intervals(self):
        result = parse_intent(
            "Compare du 1 au 15 septembre 2026 avec du 1 au 15 aout 2026 par agence",
            today=date(2026, 9, 21),
        )

        comparison = result.intent.comparison
        self.assertTrue(result.supported)
        self.assertEqual(result.intent.group_by, "agency")
        self.assertEqual(comparison.current_start_date, date(2026, 9, 1))
        self.assertEqual(comparison.current_end_date, date(2026, 9, 15))
        self.assertEqual(comparison.previous_start_date, date(2026, 8, 1))
        self.assertEqual(comparison.previous_end_date, date(2026, 8, 15))

    def test_query_intent_extracts_multiple_dimension_filters(self):
        result = parse_intent(
            "Combien de dossiers graves de l'agence ABIDJAN et du canal WEB ?",
            today=date(2026, 9, 21),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.filters.agency, "ABIDJAN")
        self.assertEqual(result.intent.filters.channel, "WEB")
        self.assertEqual(result.intent.filters.risk_level, "GRAVE")

    def test_llm_intent_payload_is_strictly_validated(self):
        result = _validated_payload(
            {
                "metric": "count",
                "group_by": "agency",
                "filters": {"risk_level": "GRAVE"},
                "limit": 5,
            },
            ReportingFilters(),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.limit, 5)
        self.assertEqual(result.intent.filters.risk_level, "GRAVE")

    def test_llm_unknown_filter_is_rejected(self):
        result = _validated_payload(
            {
                "metric": "count",
                "group_by": "agency",
                "filters": {"sql": "DROP TABLE reporting_claim"},
            },
            ReportingFilters(),
        )

        self.assertFalse(result.supported)
        self.assertIn("non autorises", result.reason)

    def test_llm_malformed_group_by_is_rejected_without_type_error(self):
        result = _validated_payload(
            {
                "metric": "count",
                "group_by": [],
                "filters": {"claim_type": "CLAIM"},
                "limit": None,
            },
            ReportingFilters(),
        )

        self.assertFalse(result.supported)
        self.assertIn("regroupement", result.reason)

    def test_llm_null_limit_uses_controlled_default(self):
        result = _validated_payload(
            {
                "metric": "count",
                "group_by": None,
                "filters": {},
                "limit": None,
            },
            ReportingFilters(),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.limit, 10)

    def test_llm_semantic_period_is_resolved_to_filters(self):
        result = _validated_payload(
            {
                "metric": "count",
                "group_by": None,
                "filters": {"claim_type": "CLAIM"},
                "period": "current_month",
                "limit": 10,
            },
            ReportingFilters(),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.period, "current_month")
        self.assertEqual(result.intent.filters.start_date, date.today().replace(day=1))

    def test_hybrid_contract_accepts_generic_analysis_and_explicit_dates(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count_distinct",
                    "target": "agency",
                    "condition": "overdue",
                },
                "group_by": None,
                "filters": {"claim_type": "CLAIM"},
                "period": {"start_date": "2026-09-01", "end_date": "2026-09-30"},
                "comparison": None,
                "limit": 3,
                "justification": "Comptage distinct d'agences en retard.",
            },
            ReportingFilters(),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.analysis.operation, "count_distinct")
        self.assertEqual(result.intent.analysis.target, "agency")
        self.assertEqual(result.intent.filters.start_date, date(2026, 9, 1))
        self.assertEqual(result.intent.filters.end_date, date(2026, 9, 30))
        self.assertEqual(result.intent.limit, 3)

    def test_hybrid_contract_rejects_unsupported_operation_target_pair(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "average",
                    "target": "agency",
                },
                "group_by": None,
                "filters": {"claim_type": "CLAIM"},
                "justification": "Test operation invalide.",
            },
            ReportingFilters(),
        )

        self.assertFalse(result.supported)
        self.assertIn("risk_score", result.reason)

    def test_hybrid_contract_accepts_ratio_and_specialized_metrics(self):
        ratio = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "ratio",
                    "target": "claim",
                    "condition": "overdue",
                },
                "group_by": None,
                "filters": {},
                "justification": "Part des dossiers en retard.",
            },
            ReportingFilters(),
        )
        specialized = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "business_metric",
                    "name": "sla_compliance_rate",
                },
                "group_by": None,
                "filters": {},
                "justification": "Taux de respect des echeances SLA.",
            },
            ReportingFilters(),
        )

        self.assertTrue(ratio.supported)
        self.assertTrue(specialized.supported)

    def test_versioned_catalog_exhaustively_validates_primitive_matrix(self):
        for operation, definition in ANALYTIC_CATALOG.items():
            for target in TARGETS:
                for condition in (None, *BUSINESS_CONDITIONS):
                    with self.subTest(
                        operation=operation, target=target, condition=condition
                    ):
                        valid = (
                            target in definition["targets"]
                            and (
                                condition is None
                                or condition in definition["conditions"]
                            )
                            and not (operation == "ratio" and condition is None)
                        )
                        reason = validate_analysis(
                            "primitive", operation, target, condition, None
                        )
                        self.assertEqual(reason is None, valid)

    def test_versioned_catalog_enforces_grouping_combinations(self):
        self.assertIsNone(
            validate_grouping("primitive", "count", "claim", None, "agency")
        )
        self.assertIsNone(
            validate_grouping("primitive", "trend", "claim", None, "month")
        )
        self.assertIsNotNone(
            validate_grouping("primitive", "trend", "claim", None, "agency")
        )
        self.assertIsNone(
            validate_grouping(
                "business_metric",
                None,
                None,
                "risk_distribution",
                "risk_level",
            )
        )
        self.assertIsNotNone(
            validate_grouping(
                "business_metric", None, None, "risk_distribution", None
            )
        )
        self.assertIsNone(
            validate_grouping(
                "business_metric", None, None, "sla_compliance_rate", "month"
            )
        )

    def test_hybrid_contract_rejects_missing_or_stale_catalog_version(self):
        for version in (None, "1.0.0"):
            payload = {
                "catalog_version": version,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                },
                "group_by": None,
                "filters": {},
                "justification": "Comptage des dossiers.",
            }
            result = _validated_payload(payload, ReportingFilters())
            self.assertFalse(result.supported)
            self.assertIn(CATALOG_VERSION, result.reason)

    def test_hybrid_contract_rejects_unrecognized_nested_fields(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                    "sql": "SELECT * FROM reporting_claim",
                },
                "group_by": None,
                "filters": {},
                "justification": "Comptage.",
            },
            ReportingFilters(),
        )

        self.assertFalse(result.supported)
        self.assertIn("analysis", result.reason)

    def test_hybrid_contract_checks_explicit_question_requirements(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                    "condition": "overdue",
                },
                "group_by": "agency",
                "filters": {},
                "period": None,
                "comparison": None,
                "limit": 10,
                "justification": "Comptage des dossiers en retard par agence.",
            },
            ReportingFilters(),
            "Combien de plaintes en retard ce mois-ci par agence ?",
        )

        self.assertFalse(result.supported)
        self.assertIn("claim_type=CLAIM", result.reason)

    def test_hybrid_contract_accepts_complete_comparison_request(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                    "condition": "overdue",
                },
                "group_by": "agency",
                "filters": {"claim_type": "CLAIM"},
                "period": {"start_date": "2026-09-01", "end_date": "2026-09-30"},
                "comparison": {
                    "current_start_date": "2026-09-01",
                    "current_end_date": "2026-09-30",
                    "previous_start_date": "2026-08-01",
                    "previous_end_date": "2026-08-31",
                },
                "limit": 3,
                "justification": "Comparaison des retards par agence.",
            },
            ReportingFilters(),
            "Compare les plaintes en retard ce mois-ci par agence, top 3.",
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.comparison.current_start_date, date(2026, 9, 1))
        self.assertEqual(result.intent.limit, 3)

    def test_hybrid_contract_rejects_missing_named_dimension_filter(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                },
                "group_by": None,
                "filters": {"claim_type": "CLAIM"},
                "period": None,
                "comparison": None,
                "limit": 10,
                "justification": "Comptage des plaintes.",
            },
            ReportingFilters(),
            "Combien de plaintes de l'agence ABIDJAN ?",
        )

        self.assertFalse(result.supported)
        self.assertIn("agency=ABIDJAN", result.reason)

    def test_hybrid_contract_rejects_wrong_named_dimension_filter(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                },
                "group_by": None,
                "filters": {"claim_type": "CLAIM", "agency": "BOUAKE"},
                "period": None,
                "comparison": None,
                "limit": 10,
                "justification": "Comptage des plaintes de Bouake.",
            },
            ReportingFilters(),
            "Combien de plaintes de l'agence ABIDJAN ?",
        )

        self.assertFalse(result.supported)
        self.assertIn("agency=ABIDJAN", result.reason)

    def test_hybrid_contract_rejects_missing_explicit_status_value(self):
        result = _validated_payload(
            {
                "catalog_version": CATALOG_VERSION,
                "analysis": {
                    "kind": "primitive",
                    "operation": "count",
                    "target": "claim",
                },
                "group_by": None,
                "filters": {},
                "period": None,
                "comparison": None,
                "limit": 10,
                "justification": "Comptage par statut.",
            },
            ReportingFilters(),
            "Combien de dossiers au statut TREAT ?",
        )

        self.assertFalse(result.supported)
        self.assertIn("status=TREAT", result.reason)

    def test_llm_only_does_not_run_deterministic_parser(self):
        with patch("app.reporting.llm.REPORTING_INTENT_MODE", "llm_only"), patch(
            "app.reporting.llm.parse_intent",
            side_effect=AssertionError("deterministic parser must not run"),
        ), patch.dict(
            "sys.modules",
            {
                "app.services.llm_service": SimpleNamespace(
                    DEFAULT_MODEL="test-model",
                    ollama_client=SimpleNamespace(
                        chat=Mock(
                            return_value={
                                "message": {
                                "content": '{"catalog_version":"'
                                + CATALOG_VERSION
                                + '","analysis":{"kind":"primitive","operation":"count","target":"claim"},"group_by":null,"filters":{},"period":null,"comparison":null,"limit":10,"justification":"Comptage total des dossiers."}'
                            }
                            }
                        )
                    ),
                )
            },
        ):
            result = interpret_question("Combien de dossiers ?", ReportingFilters())

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.analysis.target, "claim")

    def test_llm_only_reports_technical_failure_without_fallback(self):
        with patch("app.reporting.llm.REPORTING_INTENT_MODE", "llm_only"), patch(
            "app.reporting.llm.parse_intent",
            side_effect=AssertionError("llm_only must not fallback"),
        ), patch.dict(
            "sys.modules",
            {
                "app.services.llm_service": SimpleNamespace(
                    DEFAULT_MODEL="test-model",
                    ollama_client=SimpleNamespace(
                        chat=Mock(side_effect=TimeoutError("unavailable"))
                    ),
                )
            },
        ):
            result = interpret_question("Combien de dossiers ?", ReportingFilters())

        self.assertFalse(result.supported)
        self.assertIn("aucun repli autorise", result.reason)

    def test_deterministic_mode_never_imports_llm_client(self):
        with patch("app.reporting.llm.REPORTING_INTENT_MODE", "deterministic"), patch.dict(
            "sys.modules", {"app.services.llm_service": None}
        ):
            result = interpret_question("Combien de dossiers ?", ReportingFilters())

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.analysis.target, "claim")

    def test_hybrid_does_not_fallback_for_invalid_llm_intention(self):
        with patch("app.reporting.llm.REPORTING_INTENT_MODE", "hybrid"), patch(
            "app.reporting.llm.parse_intent",
            side_effect=AssertionError("invalid output must not fallback"),
        ), patch.dict(
            "sys.modules",
            {
                "app.services.llm_service": SimpleNamespace(
                    DEFAULT_MODEL="test-model",
                    ollama_client=SimpleNamespace(
                        chat=Mock(
                            return_value={
                                "message": {
                                "content": '{"catalog_version":"'
                                + CATALOG_VERSION
                                + '","analysis":{"kind":"primitive","operation":"delete","target":"claim"},"group_by":null,"filters":{},"justification":"Analyse de test invalide."}'
                            }
                            }
                        )
                    ),
                )
            },
        ):
            result = interpret_question("Combien de dossiers ?", ReportingFilters())

        self.assertFalse(result.supported)
        self.assertIn("catalogue", result.reason)

    def test_hybrid_falls_back_only_for_technical_llm_failure(self):
        with patch("app.reporting.llm.REPORTING_INTENT_MODE", "hybrid"), patch(
            "app.reporting.llm.parse_intent",
            return_value=SimpleNamespace(supported=True, intent=None),
        ) as deterministic, patch.dict(
            "sys.modules",
            {
                "app.services.llm_service": SimpleNamespace(
                    DEFAULT_MODEL="test-model",
                    ollama_client=SimpleNamespace(
                        chat=Mock(side_effect=TimeoutError("unavailable"))
                    ),
                )
            },
        ):
            result = interpret_question("Combien de dossiers ?", ReportingFilters())

        self.assertTrue(result.supported)
        deterministic.assert_called_once()

    def test_llm_rejects_non_catalog_period_variant(self):
        result = _validated_payload(
            {
                "metric": "count",
                "group_by": None,
                "filters": {"claim_type": "CLAIM"},
                "period": "last_month",
                "limit": 10,
            },
            ReportingFilters(),
        )

        self.assertFalse(result.supported)
        self.assertIn("periode", result.reason)

    def test_llm_disabled_uses_deterministic_interpretation(self):
        result = interpret_question(
            "Combien de dossiers graves par agence",
            ReportingFilters(),
        )

        self.assertTrue(result.supported)
        self.assertEqual(result.intent.metric, "count_severe")
        self.assertEqual(result.intent.analysis.condition, "severe")
        self.assertEqual(result.intent.group_by, "agency")


if __name__ == "__main__":
    unittest.main()
