import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.db.models import ReportingAlert, ReportingClaim
from app.db.session import Base
from app.reporting.schemas import (
    ReportingAnalysis,
    ReportingComparison,
    ReportingFilters,
    ReportingIntent,
    ReportingIntentResult,
)
from app.reporting.service import answer_query, build_dashboard
from app.reporting.service import _group_analysis_values, _query_analysis_value
from app.reporting.catalog import ANALYTIC_CATALOG


class ReportingServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add_all(
                [
                    ReportingClaim(
                        source_claim_id=1,
                        claim_type="CLAIM",
                        status="TREAT",
                        category="MONETIQUE",
                        channel="WEB",
                        agency="ABIDJAN",
                        risk_level="GRAVE",
                        ai_urgency="GRAVE",
                        ai_risk_score=80,
                        created_at=datetime(2026, 9, 10, 10),
                        sla_due_at=datetime(2026, 9, 12, 10),
                        synced_at=datetime(2026, 9, 14, 10),
                    ),
                    ReportingClaim(
                        source_claim_id=2,
                        claim_type="DENUNCIACION",
                        status="SATISFIED",
                        category="SERVICE",
                        channel="AGENCE",
                        agency="BOUAKE",
                        risk_level="MINEUR",
                        ai_risk_score=10,
                        created_at=datetime(2026, 9, 11, 10),
                        synced_at=datetime(2026, 9, 14, 10),
                    ),
                    ReportingClaim(
                        source_claim_id=3,
                        claim_type="CLAIM",
                        status="TEMP_SAVED",
                        category="BROUILLON",
                        channel="WEB",
                        agency="ABIDJAN",
                        risk_level="GRAVE",
                        ai_urgency="GRAVE",
                        ai_risk_score=95,
                        created_at=datetime(2026, 9, 12, 10),
                        synced_at=datetime(2026, 9, 14, 10),
                    ),
                    ReportingClaim(
                        source_claim_id=4,
                        claim_type="CLAIM",
                        status="CLASSED",
                        category="SERVICE",
                        created_at=datetime(2026, 9, 10, 10),
                        sla_due_at=datetime(2026, 9, 12, 10),
                        synced_at=datetime(2026, 9, 14, 10),
                    ),
                ]
            )
            session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_dashboard_aggregates_claims(self):
        with Session(self.engine) as session:
            response = build_dashboard(session, ReportingFilters())

        self.assertEqual(response.metrics.total_claims, 3)
        self.assertEqual(response.metrics.high_risk_claims, 1)
        self.assertEqual(response.metrics.anomalies, 1)
        self.assertEqual(response.metrics.active_alerts, 1)
        self.assertEqual(response.metrics.risk_score, 60.0)
        self.assertEqual(set(response.charts["channels"].labels), {"WEB", "AGENCE"})
        self.assertNotIn("BROUILLON", response.charts["categories"].labels)
        self.assertTrue(
            any(alert.id == "concentration-categorie" for alert in response.alerts)
        )
        self.assertTrue(
            any(recommendation.id == "concentration-categorie-review"
                for recommendation in response.recommendations)
        )
        with Session(self.engine) as session:
            persisted = session.query(ReportingAlert).filter_by(
                source_key="concentration-categorie"
            ).one()
            self.assertEqual(persisted.status, "new")
            persisted.status = "in_progress"
            session.commit()

        with Session(self.engine) as session:
            build_dashboard(session, ReportingFilters())
            persisted = session.query(ReportingAlert).filter_by(
                source_key="concentration-categorie"
            ).one()
            self.assertEqual(persisted.status, "in_progress")
        self.assertEqual(response.details.anomalies, response.details.alerts)
        self.assertTrue(
            all(row["status"] not in {"SATISFIED", "CLASSED", "TEMP_SAVED"}
                for row in response.details.anomalies)
        )

    def test_temp_saved_claims_are_excluded_from_all_reporting_data(self):
        with Session(self.engine) as session:
            response = build_dashboard(session, ReportingFilters())

        self.assertEqual(response.metrics.total_claims, 3)
        self.assertEqual(response.metrics.severe_claims, 1)
        self.assertEqual(len(response.details.total), 3)
        self.assertTrue(
            all(row["status"] != "TEMP_SAVED" for row in response.details.total)
        )

    def test_query_returns_controlled_visualization(self):
        with Session(self.engine) as session:
            response = answer_query(
                session,
                "Quels sont les canaux ?",
                ReportingFilters(),
            )

        self.assertEqual(response.visualization.type, "bar")
        self.assertEqual(
            {item["label"] for item in response.data},
            {"WEB", "AGENCE"},
        )

    def test_query_supports_controlled_metric_and_grouping(self):
        with Session(self.engine) as session:
            response = answer_query(
                session,
                "Combien de dossiers graves en retard par agence ?",
                ReportingFilters(),
            )

        self.assertEqual(response.visualization.type, "bar")
        self.assertEqual(
            response.visualization.datasets[0].label,
            "Dossiers graves en retard",
        )
        self.assertEqual(response.data, [{"label": "ABIDJAN", "value": 1.0}])
        self.assertIn("graves", response.answer)

    def test_query_returns_single_total_chart_without_grouping(self):
        with Session(self.engine) as session:
            response = answer_query(
                session,
                "Quel est le nombre de dossiers ?",
                ReportingFilters(),
            )

        self.assertIsNotNone(response.visualization)
        self.assertEqual(response.visualization.labels, ["Total"])
        self.assertEqual(response.data, [{"label": "Total", "value": 3.0}])

    def test_query_executes_generic_count_distinct_analysis(self):
        intent = ReportingIntent(
            analysis=ReportingAnalysis(
                kind="primitive",
                operation="count_distinct",
                target="agency",
            ),
            filters=ReportingFilters(claim_type="CLAIM"),
        )
        with Session(self.engine) as session, patch(
            "app.reporting.service.interpret_question",
            return_value=ReportingIntentResult(supported=True, intent=intent),
        ):
            response = answer_query(
                session,
                "Combien d'agences ont reçu des plaintes ?",
                ReportingFilters(),
            )

        self.assertEqual(response.visualization.labels, ["Total"])
        self.assertEqual(response.data, [{"label": "Total", "value": 1.0}])

    def test_query_returns_grouped_comparison_values_and_deltas(self):
        with Session(self.engine) as session:
            session.add(
                ReportingClaim(
                    source_claim_id=5,
                    claim_type="CLAIM",
                    status="TREAT",
                    agency="ABIDJAN",
                    created_at=datetime(2026, 8, 10, 10),
                    sla_due_at=datetime(2026, 8, 12, 10),
                    synced_at=datetime(2026, 8, 14, 10),
                )
            )
            session.commit()

            intent = ReportingIntent(
                analysis=ReportingAnalysis(
                    kind="primitive",
                    operation="count",
                    target="claim",
                    condition="overdue",
                ),
                group_by="agency",
                filters=ReportingFilters(claim_type="CLAIM"),
                comparison=ReportingComparison(
                    current_start_date=datetime(2026, 9, 1).date(),
                    current_end_date=datetime(2026, 9, 30).date(),
                    previous_start_date=datetime(2026, 8, 1).date(),
                    previous_end_date=datetime(2026, 8, 31).date(),
                ),
                limit=3,
            )
            with patch(
                "app.reporting.service.interpret_question",
                return_value=ReportingIntentResult(supported=True, intent=intent),
            ):
                response = answer_query(
                    session,
                    "Compare les plaintes en retard par agence, top 3.",
                    ReportingFilters(),
                )

        self.assertEqual(response.visualization.labels, ["ABIDJAN"])
        self.assertEqual(
            [dataset.label for dataset in response.visualization.datasets],
            [
                "Dossiers en retard - periode actuelle",
                "Dossiers en retard - periode precedente",
            ],
        )
        self.assertEqual(
            response.data,
            [
                {
                    "label": "ABIDJAN",
                    "current_value": 1.0,
                    "previous_value": 1.0,
                    "change": 0.0,
                    "change_percent": 0.0,
                }
            ],
        )

    def test_query_executes_specialized_sla_rate_and_resolution_time(self):
        with Session(self.engine) as session:
            session.add_all(
                [
                    ReportingClaim(
                        source_claim_id=6,
                        claim_type="CLAIM",
                        status="SATISFIED",
                        agency="ABIDJAN",
                        risk_level="MOYEN",
                        receipt_at=datetime(2026, 9, 1, 10),
                        created_at=datetime(2026, 9, 1, 10),
                        sla_due_at=datetime(2026, 9, 5, 10),
                        resolved_at=datetime(2026, 9, 4, 10),
                        synced_at=datetime(2026, 9, 6, 10),
                    ),
                    ReportingClaim(
                        source_claim_id=7,
                        claim_type="CLAIM",
                        status="SATISFIED",
                        agency="ABIDJAN",
                        risk_level="GRAVE",
                        receipt_at=datetime(2026, 9, 1, 10),
                        created_at=datetime(2026, 9, 1, 10),
                        sla_due_at=datetime(2026, 9, 5, 10),
                        resolved_at=datetime(2026, 9, 11, 10),
                        synced_at=datetime(2026, 9, 12, 10),
                    ),
                    ReportingClaim(
                        source_claim_id=8,
                        claim_type="CLAIM",
                        status="TREAT",
                        agency="ABIDJAN",
                        risk_level="MINEUR",
                        receipt_at=datetime(2026, 9, 1, 10),
                        created_at=datetime(2026, 9, 1, 10),
                        sla_due_at=datetime(2026, 9, 5, 10),
                        synced_at=datetime(2026, 9, 12, 10),
                    ),
                ]
            )
            session.commit()

            metric_intents = (
                (
                    ReportingAnalysis(
                        kind="business_metric",
                        name="sla_compliance_rate",
                    ),
                    "Taux SLA",
                    50.0,
                ),
                (
                    ReportingAnalysis(
                        kind="business_metric",
                        name="average_resolution_time",
                    ),
                    "Duree moyenne",
                    6.5,
                ),
            )
            for analysis, question, expected in metric_intents:
                intent = ReportingIntent(
                    analysis=analysis,
                    filters=ReportingFilters(claim_type="CLAIM"),
                )
                with patch(
                    "app.reporting.service.interpret_question",
                    return_value=ReportingIntentResult(supported=True, intent=intent),
                ):
                    response = answer_query(
                        session,
                        question,
                        ReportingFilters(),
                    )
                self.assertEqual(response.data, [{"label": "Total", "value": expected}])

    def test_query_executes_ratio_as_percentage_of_filtered_population(self):
        intent = ReportingIntent(
            analysis=ReportingAnalysis(
                kind="primitive",
                operation="ratio",
                target="claim",
                condition="overdue",
            ),
            filters=ReportingFilters(claim_type="CLAIM"),
        )
        with Session(self.engine) as session, patch(
            "app.reporting.service.interpret_question",
            return_value=ReportingIntentResult(supported=True, intent=intent),
        ):
            response = answer_query(
                session,
                "Quelle part des plaintes est en retard ?",
                ReportingFilters(),
            )

        self.assertEqual(response.data, [{"label": "Total", "value": 50.0}])

    def test_query_returns_risk_distribution_by_risk_level(self):
        intent = ReportingIntent(
            analysis=ReportingAnalysis(
                kind="business_metric",
                name="risk_distribution",
            ),
            group_by="risk_level",
            filters=ReportingFilters(),
        )
        with Session(self.engine) as session, patch(
            "app.reporting.service.interpret_question",
            return_value=ReportingIntentResult(supported=True, intent=intent),
        ):
            response = answer_query(
                session,
                "Répartition des dossiers par risque",
                ReportingFilters(),
            )

        self.assertEqual(response.data[0], {"label": "GRAVE", "value": 1.0})
        self.assertEqual(response.data[1], {"label": "MINEUR", "value": 1.0})

    def test_specialized_metrics_group_by_agency(self):
        with Session(self.engine) as session:
            session.add_all(
                [
                    ReportingClaim(
                        source_claim_id=9,
                        claim_type="CLAIM",
                        status="SATISFIED",
                        agency="ABIDJAN",
                        risk_level="MOYEN",
                        receipt_at=datetime(2026, 9, 1),
                        resolved_at=datetime(2026, 9, 2),
                        sla_due_at=datetime(2026, 9, 3),
                        created_at=datetime(2026, 9, 1),
                        synced_at=datetime(2026, 9, 4),
                    ),
                    ReportingClaim(
                        source_claim_id=10,
                        claim_type="CLAIM",
                        status="SATISFIED",
                        agency="BOUAKE",
                        risk_level="MINEUR",
                        receipt_at=datetime(2026, 9, 1),
                        resolved_at=datetime(2026, 9, 5),
                        sla_due_at=datetime(2026, 9, 3),
                        created_at=datetime(2026, 9, 1),
                        synced_at=datetime(2026, 9, 6),
                    ),
                ]
            )
            session.commit()
            expected_by_metric = {
                "sla_compliance_rate": {"ABIDJAN": 100.0, "BOUAKE": 0.0},
                "average_resolution_time": {"ABIDJAN": 1.0, "BOUAKE": 4.0},
            }
            for name, expected in expected_by_metric.items():
                with self.subTest(name=name):
                    values = _group_analysis_values(
                        session,
                        ReportingFilters(claim_type="CLAIM"),
                        ReportingAnalysis(kind="business_metric", name=name),
                        "agency",
                    )
                    self.assertEqual(values, expected)

    def test_specialized_metrics_handle_missing_and_invalid_sla_dates(self):
        with Session(self.engine) as session:
            session.add_all(
                [
                    ReportingClaim(
                        source_claim_id=11,
                        claim_type="CLAIM",
                        status="SATISFIED",
                        agency="ABIDJAN",
                        receipt_at=datetime(2026, 9, 2),
                        resolved_at=datetime(2026, 9, 1),
                        synced_at=datetime(2026, 9, 3),
                    ),
                    ReportingClaim(
                        source_claim_id=12,
                        claim_type="CLAIM",
                        status="SATISFIED",
                        agency="BOUAKE",
                        resolved_at=datetime(2026, 9, 3),
                        synced_at=datetime(2026, 9, 5),
                    ),
                ]
            )
            session.commit()
            filters = ReportingFilters(claim_type="CLAIM")
            sla_rate = _query_analysis_value(
                session,
                filters,
                ReportingAnalysis(kind="business_metric", name="sla_compliance_rate"),
            )
            resolution_time = _query_analysis_value(
                session,
                filters,
                ReportingAnalysis(
                    kind="business_metric", name="average_resolution_time"
                ),
            )

        self.assertEqual(sla_rate, 0.0)
        self.assertEqual(resolution_time, 0.0)

    def test_sql_engine_executes_every_catalogued_primitive_combination(self):
        with Session(self.engine) as session:
            for operation, definition in ANALYTIC_CATALOG.items():
                for target in definition["targets"]:
                    for condition in (None, *definition["conditions"]):
                        if operation == "ratio" and condition is None:
                            continue
                        analysis = ReportingAnalysis(
                            kind="primitive",
                            operation=operation,
                            target=target,
                            condition=condition,
                        )
                        with self.subTest(
                            operation=operation, target=target, condition=condition
                        ):
                            value = _query_analysis_value(
                                session, ReportingFilters(), analysis
                            )
                            grouped = _group_analysis_values(
                                session,
                                ReportingFilters(),
                                analysis,
                                "agency",
                            )
                            self.assertIsInstance(value, float)
                            self.assertIsInstance(grouped, dict)

    def test_query_supports_product_filter(self):
        with Session(self.engine) as session:
            response = answer_query(
                session,
                "Quels sont les dossiers par categorie ?",
                ReportingFilters(product="Carte"),
            )

        self.assertEqual(response.data, [])

    def test_query_returns_controlled_period_comparison(self):
        with Session(self.engine) as session:
            response = answer_query(
                session,
                "Compare le volume des dossiers par canal avec le mois dernier",
                ReportingFilters(),
            )

        self.assertIsNotNone(response.comparison)
        self.assertEqual(response.comparison.current_value, 3.0)
        self.assertEqual(response.comparison.previous_value, 0.0)
        self.assertEqual(response.comparison.change_percent, 100.0)
        self.assertIn("Comparaison", response.answer)

    def test_query_returns_controlled_period_comparison(self):
        with Session(self.engine) as session:
            response = answer_query(
                session,
                "Compare le volume de septembre par rapport au mois dernier",
                ReportingFilters(),
            )

        self.assertIsNotNone(response.comparison)
        self.assertEqual(response.comparison.current_value, 3.0)
        self.assertEqual(response.comparison.previous_value, 0.0)
        self.assertEqual(response.comparison.change_percent, 100.0)
        self.assertIn("Comparaison", response.answer)

    def test_dashboard_returns_periods_changes_and_details(self):
        with Session(self.engine) as session:
            response = build_dashboard(
                session,
                ReportingFilters(start_date="2026-09-10", end_date="2026-09-14"),
            )

        self.assertEqual(
            [period.value for period in response.periods],
            ["custom"],
        )
        self.assertIsNotNone(response.metrics.total_claims_change)
        self.assertEqual(len(response.details.risk), 1)


if __name__ == "__main__":
    unittest.main()
