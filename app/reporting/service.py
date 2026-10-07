from datetime import date, datetime, time, timedelta, timezone
import json
import logging
from time import perf_counter
import unicodedata
from typing import Any

from sqlalchemy import and_, case, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import ReportingAlert, ReportingClaim

from .constants import INCLUDED_CLAIM_TYPES, IN_PROGRESS_EXCLUDED_STATUSES, SEVERE_URGENCY
from .catalog import TARGETS, condition_expression
from .llm import formulate_answer, interpret_question
from .trace_logging import trace_info

logger = logging.getLogger(__name__)
from .schemas import (
    Alert,
    ChartData,
    ChartDataset,
    DashboardDetails,
    DashboardMetrics,
    DashboardResponse,
    FilterOption,
    FilterOptions,
    Period,
    Recommendation,
    ReportingFilters,
    ReportingQueryResponse,
    ReportingComparisonResult,
    RiskLegend,
    RiskMatrixRow,
    RiskSummary,
    Visualization,
)


def _date_bounds(filters: ReportingFilters) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(filters.start_date, time.min) if filters.start_date else None
    end = (
        datetime.combine(filters.end_date + timedelta(days=1), time.min)
        if filters.end_date
        else None
    )
    return start, end


def _conditions(filters: ReportingFilters) -> list[Any]:
    start, end = _date_bounds(filters)
    conditions: list[Any] = [
        ReportingClaim.claim_type.in_(INCLUDED_CLAIM_TYPES),
        or_(
            ReportingClaim.status.is_(None),
            ReportingClaim.status != "TEMP_SAVED",
        ),
    ]
    if start:
        conditions.append(func.coalesce(ReportingClaim.created_at, ReportingClaim.receipt_at) >= start)
    if end:
        conditions.append(func.coalesce(ReportingClaim.created_at, ReportingClaim.receipt_at) < end)
    for column, value in (
        (ReportingClaim.claim_type, filters.claim_type),
        (ReportingClaim.agency, filters.agency),
        (ReportingClaim.channel, filters.channel),
        (ReportingClaim.category, filters.category),
        (ReportingClaim.product, filters.product),
        (ReportingClaim.team, filters.team),
        (ReportingClaim.status, filters.status),
        (ReportingClaim.risk_level, filters.risk_level),
        (ReportingClaim.motif, filters.motif),
        (ReportingClaim.service_point, filters.service_point),
        (ReportingClaim.satisfaction_status, filters.satisfaction_status),
    ):
        if value:
            conditions.append(column == value)
    return conditions


def _periods(filters: ReportingFilters) -> list[Period]:
    today = date.today()
    if filters.start_date and filters.end_date:
        return [
            Period(
                value="custom",
                label="Periode selectionnee",
                start_date=filters.start_date,
                end_date=filters.end_date,
                default=True,
            )
        ]
    end = filters.end_date or today
    start = filters.start_date or (end - timedelta(days=29))
    quarter_start = date(end.year, ((end.month - 1) // 3) * 3 + 1, 1)
    return [
        Period(value="last_7_days", label="7 derniers jours", start_date=end - timedelta(days=6), end_date=end),
        Period(value="last_30_days", label="30 derniers jours", start_date=start, end_date=end, default=True),
        Period(value="quarter", label="Trimestre", start_date=quarter_start, end_date=end),
        Period(value="year", label="Annee", start_date=date(end.year, 1, 1), end_date=end),
        Period(
            value="previous_30_days",
            label="30 jours precedents",
            start_date=start - timedelta(days=30),
            end_date=start - timedelta(days=1),
        ),
    ]


def _period_filters(filters: ReportingFilters, start: date, end: date) -> ReportingFilters:
    if hasattr(filters, "model_copy"):
        return filters.model_copy(update={"start_date": start, "end_date": end})
    return filters.copy(update={"start_date": start, "end_date": end})


def _previous_period(filters: ReportingFilters) -> ReportingFilters | None:
    if not filters.start_date or not filters.end_date:
        end = date.today() - timedelta(days=30)
        return _period_filters(filters, end - timedelta(days=29), end)
    duration = filters.end_date - filters.start_date + timedelta(days=1)
    previous_end = filters.start_date - timedelta(days=1)
    return _period_filters(filters, previous_end - duration + timedelta(days=1), previous_end)


def _overdue_condition(now: datetime) -> Any:
    return and_(
        or_(
            ReportingClaim.status.is_(None),
            ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
        ),
        ReportingClaim.sla_due_at.is_not(None),
        ReportingClaim.sla_due_at < now,
        or_(
            ReportingClaim.resolved_at.is_(None),
            ReportingClaim.resolved_at >= ReportingClaim.sla_due_at,
        ),
    )


def _risk_score_expression(now: datetime) -> Any:
    base_score = case(
        (ReportingClaim.risk_level == "MINEUR", 20),
        (ReportingClaim.risk_level == "MOYEN", 50),
        (ReportingClaim.risk_level == "GRAVE", 80),
        else_=None,
    )
    adjustments = (
        case(
            (
                func.upper(func.coalesce(ReportingClaim.ai_sentiment, "")).in_(
                    ("NEGATIVE", "NEGATIF", "NEGATIVE_SENTIMENT")
                ),
                10,
            ),
            else_=0,
        )
        + case((ReportingClaim.claim_type == "DENUNCIACION", 5), else_=0)
        + case(
            (
                or_(
                    ReportingClaim.status.is_(None),
                    ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
                ),
                5,
            ),
            else_=0,
        )
        + case((_overdue_condition(now), 10), else_=0)
    )
    total_score = base_score + adjustments
    return case(
        (base_score.is_(None), None),
        (total_score > 100, 100),
        else_=total_score,
    )


def _metric_values(db: Session, filters: ReportingFilters) -> tuple[int, int, int, int, float]:
    conditions = _conditions(filters)
    total = _count(db, conditions)
    severe = _count(db, conditions, ReportingClaim.risk_level == SEVERE_URGENCY)
    active = _count(
        db, conditions,
        or_(
            ReportingClaim.status.is_(None),
            ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
        ),
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overdue = _count(db, conditions, _overdue_condition(now))
    average = db.scalar(select(func.avg(_risk_score_expression(now))).where(*conditions))
    return total, severe, overdue, active, round(float(average or 0), 1)


def _detail_rows(db: Session, conditions: list[Any], extra: Any = None) -> list[dict[str, Any]]:
    query = select(ReportingClaim).where(*conditions)
    if extra is not None:
        query = query.where(extra)
    rows = db.scalars(query.order_by(ReportingClaim.created_at.desc()).limit(50)).all()
    return [
        {
            "id": claim.source_code or claim.source_claim_id,
            "source_claim_id": claim.source_claim_id,
            "category": claim.category or "Non classe",
            "agency": claim.agency,
            "status": claim.status,
            "risk": claim.risk_level or "Non evalue",
            "detected_at": claim.source_updated_at or claim.created_at,
        }
        for claim in rows
    ]


def _count(db: Session, conditions: list[Any], extra: Any = None) -> int:
    query = select(func.count(ReportingClaim.id)).where(*conditions)
    if extra is not None:
        query = query.where(extra)
    return int(db.scalar(query) or 0)


def _percent_change(current: int | float, previous: int | float) -> float | None:
    if previous == 0:
        return None if current == 0 else 100.0
    return round((current - previous) * 100 / previous, 1)


def _analysis_summary(value: float, analysis: Any, metric_label: str) -> str:
    if analysis and analysis.kind == "business_metric":
        if analysis.name == "sla_compliance_rate":
            return (
                f"Taux de conformite SLA : {value}% des dossiers clotures "
                "avec une echeance valide ont ete resolus dans les delais."
            )
        if analysis.name == "average_resolution_time":
            return f"Duree moyenne de resolution : {value} jour(s) calendaire(s)."
        if analysis.name == "risk_distribution":
            return f"{value} dossier(s) avec un niveau de risque evalue."
    if analysis and analysis.operation == "ratio":
        return f"{value}% des dossiers satisfont la condition {analysis.condition}."
    return f"{value} dossier(s) {metric_label}."


def _copy_filters(filters: ReportingFilters, **updates: Any) -> ReportingFilters:
    if hasattr(filters, "model_copy"):
        return filters.model_copy(update=updates)
    return filters.copy(update=updates)


def _query_metric_value(
    db: Session,
    filters: ReportingFilters,
    metric: str,
) -> float:
    conditions = _conditions(filters)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if metric == "count_overdue":
        return float(_count(db, conditions, _overdue_condition(now)))
    if metric == "count_severe":
        return float(_count(db, conditions, ReportingClaim.risk_level == SEVERE_URGENCY))
    if metric == "count_active":
        return float(
            _count(
                db,
                conditions,
                or_(
                    ReportingClaim.status.is_(None),
                    ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
                ),
            )
        )
    if metric == "average_risk_score":
        value = db.scalar(select(func.avg(_risk_score_expression(now))).where(*conditions))
        return round(float(value or 0), 1)
    return float(_count(db, conditions))


def _analysis_expression(analysis: Any, now: datetime) -> Any:
    if analysis.kind == "business_metric":
        raise ValueError(
            f"L'indicateur specialise {analysis.name} ne se calcule pas comme une operation simple."
        )
    if analysis.operation == "ratio":
        return func.count(ReportingClaim.id)
    target = TARGETS[analysis.target]
    if analysis.operation == "count":
        return func.count(ReportingClaim.id) if analysis.target == "claim" else func.count(target)
    if analysis.operation == "count_distinct":
        return func.count(distinct(target))
    if analysis.operation == "sum":
        return func.sum(target)
    if analysis.operation == "average":
        return func.avg(target)
    if analysis.operation == "min":
        return func.min(target)
    if analysis.operation == "max":
        return func.max(target)
    if analysis.operation == "trend":
        return func.count(ReportingClaim.id)
    raise ValueError(f"Operation analytique non executable : {analysis.operation}")


def _grouping_column(db: Session, group_by: str) -> tuple[Any, Any | None]:
    if group_by != "month":
        return TARGETS[group_by], None
    date_column = func.coalesce(ReportingClaim.created_at, ReportingClaim.receipt_at)
    group_column = (
        func.strftime("%Y-%m", date_column)
        if db.bind is not None and db.bind.dialect.name == "sqlite"
        else func.date_format(date_column, "%Y-%m")
    )
    return group_column, date_column


def _resolution_days(db: Session, conditions: list[Any]) -> float:
    rows = db.execute(
        select(ReportingClaim.receipt_at, ReportingClaim.resolved_at)
        .where(*conditions)
        .where(
            ReportingClaim.receipt_at.is_not(None),
            ReportingClaim.resolved_at.is_not(None),
            ReportingClaim.resolved_at >= ReportingClaim.receipt_at,
        )
    ).all()
    if not rows:
        return 0.0
    durations = [
        (resolved_at - receipt_at).total_seconds() / 86400
        for receipt_at, resolved_at in rows
    ]
    return round(sum(durations) / len(durations), 1)


def _specialized_value(db: Session, filters: ReportingFilters, name: str) -> float:
    conditions = _conditions(filters)
    if name == "average_resolution_time":
        return _resolution_days(db, conditions)
    if name == "sla_compliance_rate":
        closed_with_sla = and_(
            ReportingClaim.resolved_at.is_not(None),
            ReportingClaim.sla_due_at.is_not(None),
        )
        denominator = _count(db, conditions, closed_with_sla)
        if not denominator:
            return 0.0
        numerator = _count(
            db,
            conditions,
            and_(closed_with_sla, ReportingClaim.resolved_at <= ReportingClaim.sla_due_at),
        )
        return round(numerator * 100 / denominator, 1)
    if name == "risk_distribution":
        return float(_count(db, conditions, ReportingClaim.risk_level.is_not(None)))
    raise ValueError(f"Indicateur specialise non executable : {name}")


def _specialized_group_values(
    db: Session,
    filters: ReportingFilters,
    analysis: Any,
    group_by: str,
) -> dict[str, float]:
    conditions = _conditions(filters)
    group_column, date_column = _grouping_column(db, group_by)
    if date_column is not None:
        conditions.append(date_column.is_not(None))

    if analysis.name == "risk_distribution":
        rows = db.execute(
            select(group_column, func.count(ReportingClaim.id))
            .where(*conditions, group_column.is_not(None))
            .group_by(group_column)
        ).all()
        return {str(row[0]): float(row[1]) for row in rows if row[0] is not None}

    if analysis.name == "average_resolution_time":
        rows = db.execute(
            select(group_column, ReportingClaim.receipt_at, ReportingClaim.resolved_at)
            .where(*conditions, group_column.is_not(None))
            .where(
                ReportingClaim.receipt_at.is_not(None),
                ReportingClaim.resolved_at.is_not(None),
                ReportingClaim.resolved_at >= ReportingClaim.receipt_at,
            )
        ).all()
        durations: dict[str, list[float]] = {}
        for group, receipt_at, resolved_at in rows:
            durations.setdefault(str(group), []).append(
                (resolved_at - receipt_at).total_seconds() / 86400
            )
        return {
            group: round(sum(values) / len(values), 1)
            for group, values in durations.items()
            if values
        }

    if analysis.name == "sla_compliance_rate":
        closed_with_sla = and_(
            ReportingClaim.resolved_at.is_not(None),
            ReportingClaim.sla_due_at.is_not(None),
        )
        rows = db.execute(
            select(
                group_column,
                func.sum(
                    case(
                        (
                            ReportingClaim.resolved_at <= ReportingClaim.sla_due_at,
                            1,
                        ),
                        else_=0,
                    )
                ),
                func.count(ReportingClaim.id),
            )
            .where(*conditions, group_column.is_not(None), closed_with_sla)
            .group_by(group_column)
        ).all()
        return {
            str(row[0]): round(float(row[1] or 0) * 100 / row[2], 1)
            for row in rows
            if row[0] is not None and row[2]
        }
    raise ValueError(f"Indicateur specialise non executable : {analysis.name}")


def _query_analysis_value(
    db: Session,
    filters: ReportingFilters,
    analysis: Any,
) -> float:
    conditions = _conditions(filters)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if analysis.kind == "business_metric":
        return _specialized_value(db, filters, analysis.name)
    if analysis.operation == "ratio":
        denominator = _count(db, conditions)
        if not denominator:
            return 0.0
        numerator = _count(
            db, conditions, condition_expression(analysis.condition, now)
        )
        return round(numerator * 100 / denominator, 1)
    extra = condition_expression(analysis.condition, now)
    expression = _analysis_expression(analysis, now)
    value = db.scalar(select(expression).where(*conditions, *([extra] if extra is not None else [])))
    return round(float(value or 0), 1)


def _group_analysis_chart(
    db: Session,
    filters: ReportingFilters,
    analysis: Any,
    group_by: str,
    limit: int,
) -> ChartData:
    values = _group_analysis_values(db, filters, analysis, group_by)
    if group_by == "month":
        labels = sorted(values)
    else:
        labels = sorted(values, key=lambda key: (-values[key], key))[:limit]
    if analysis.kind == "business_metric":
        label = {
            "sla_compliance_rate": "Taux de conformite SLA (%)",
            "average_resolution_time": "Duree moyenne de resolution (jours)",
            "risk_distribution": "Dossiers",
        }[analysis.name]
    elif analysis.operation == "ratio":
        label = f"Part des dossiers {analysis.condition} (%)"
    else:
        label = {
            "count": "Dossiers" if analysis.target == "claim" else f"Nombre de {analysis.target}",
            "count_distinct": f"{analysis.target} distincts",
            "sum": f"Somme {analysis.target}",
            "average": f"Moyenne {analysis.target}",
            "min": f"Minimum {analysis.target}",
            "max": f"Maximum {analysis.target}",
            "trend": "Dossiers",
        }[analysis.operation]
    return ChartData(
        labels=labels,
        datasets=[ChartDataset(label=label, data=[values[key] for key in labels])],
    )


def _group_analysis_values(
    db: Session,
    filters: ReportingFilters,
    analysis: Any,
    group_by: str,
) -> dict[str, float]:
    conditions = _conditions(filters)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if analysis.kind == "business_metric":
        return _specialized_group_values(db, filters, analysis, group_by)
    if analysis.operation == "ratio":
        group_column, date_column = _grouping_column(db, group_by)
        if date_column is not None:
            conditions.append(date_column.is_not(None))
        denominator_rows = db.execute(
            select(group_column, func.count(ReportingClaim.id))
            .where(*conditions, group_column.is_not(None))
            .group_by(group_column)
        ).all()
        denominators = {str(row[0]): int(row[1]) for row in denominator_rows}
        numerator_rows = db.execute(
            select(group_column, func.count(ReportingClaim.id))
            .where(
                *conditions,
                group_column.is_not(None),
                condition_expression(analysis.condition, now),
            )
            .group_by(group_column)
        ).all()
        numerators = {str(row[0]): int(row[1]) for row in numerator_rows}
        return {
            group: round(numerators.get(group, 0) * 100 / denominator, 1)
            for group, denominator in denominators.items()
            if denominator
        }
    extra = condition_expression(analysis.condition, now)
    expression = _analysis_expression(analysis, now)
    group_column, date_column = _grouping_column(db, group_by)
    if date_column is not None:
        conditions.append(date_column.is_not(None))
    query = (
        select(group_column, expression)
        .where(*conditions, group_column.is_not(None))
        .group_by(group_column)
    )
    if extra is not None:
        query = query.where(extra)
    return {
        str(row[0]): round(float(row[1] or 0), 1)
        for row in db.execute(query).all()
        if row[0] is not None
    }


def _group_comparison_chart(
    db: Session,
    filters: ReportingFilters,
    analysis: Any,
    group_by: str,
    comparison: Any,
    limit: int,
) -> tuple[ChartData, list[dict[str, Any]]]:
    current_filters = _copy_filters(
        filters,
        start_date=comparison.current_start_date,
        end_date=comparison.current_end_date,
    )
    previous_filters = _copy_filters(
        filters,
        start_date=comparison.previous_start_date,
        end_date=comparison.previous_end_date,
    )
    current_values = _group_analysis_values(db, current_filters, analysis, group_by)
    previous_values = _group_analysis_values(db, previous_filters, analysis, group_by)
    labels = sorted(current_values, key=lambda key: (-current_values[key], key))[:limit]
    rows = [
        {
            "label": label,
            "current_value": current_values[label],
            "previous_value": previous_values.get(label, 0.0),
            "change": round(current_values[label] - previous_values.get(label, 0.0), 1),
            "change_percent": _percent_change(
                current_values[label], previous_values.get(label, 0.0)
            ),
        }
        for label in labels
    ]
    if analysis.kind == "business_metric":
        operation_label = {
            "sla_compliance_rate": "Taux de conformite SLA (%)",
            "average_resolution_time": "Duree moyenne de resolution (jours)",
            "risk_distribution": "Dossiers",
        }[analysis.name]
    elif analysis.operation == "ratio":
        operation_label = f"Part des dossiers {analysis.condition} (%)"
    else:
        operation_label = {
            "count": "Dossiers",
            "count_distinct": "Valeurs distinctes",
            "sum": "Somme",
            "average": "Moyenne",
            "min": "Minimum",
            "max": "Maximum",
            "trend": "Dossiers",
        }[analysis.operation]
    chart = ChartData(
        labels=labels,
        datasets=[
            ChartDataset(label="Periode actuelle", data=[row["current_value"] for row in rows]),
            ChartDataset(label="Periode precedente", data=[row["previous_value"] for row in rows]),
        ],
    )
    if analysis.condition:
        condition_labels = {
            "overdue": "en retard",
            "active": "en cours",
            "severe": "graves",
            "within_sla": "dans les delais SLA",
            "has_sla": "avec SLA",
            "satisfied": "satisfaits",
            "evaluated": "evalues",
        }
        operation_label = f"{operation_label} {condition_labels[analysis.condition]}"
    chart.datasets[0].label = f"{operation_label} - periode actuelle"
    chart.datasets[1].label = f"{operation_label} - periode precedente"
    return chart, rows


def _concentration_anomalies(
    db: Session,
    conditions: list[Any],
    total: int,
) -> list[tuple[str, str, int, float]]:
    if total < 3:
        return []
    anomalies: list[tuple[str, str, int, float]] = []
    for label, column in (
        ("categorie", ReportingClaim.category),
        ("canal", ReportingClaim.channel),
    ):
        row = db.execute(
            select(column, func.count(ReportingClaim.id))
            .where(*conditions)
            .where(column.is_not(None))
            .group_by(column)
            .order_by(func.count(ReportingClaim.id).desc(), column)
            .limit(1)
        ).first()
        if row is None:
            continue
        count = int(row[1])
        share = count / total
        if share >= 0.6:
            anomalies.append((label, str(row[0]), count, round(share * 100, 1)))
    return anomalies


def _moving_average_anomaly(
    db: Session,
    conditions: list[Any],
) -> tuple[int, float] | None:
    date_column = func.coalesce(ReportingClaim.created_at, ReportingClaim.receipt_at)
    if db.bind is not None and db.bind.dialect.name == "sqlite":
        period_column = func.strftime("%Y-%m", date_column)
    else:
        period_column = func.date_format(date_column, "%Y-%m")
    rows = db.execute(
        select(period_column, func.count(ReportingClaim.id))
        .where(*conditions)
        .where(date_column.is_not(None))
        .group_by(period_column)
        .order_by(period_column)
    ).all()
    if len(rows) < 3:
        return None
    current = int(rows[-1][1])
    baseline = sum(int(row[1]) for row in rows[-3:-1]) / 2
    if baseline <= 0 or current < baseline * 1.5:
        return None
    return current, round(baseline, 1)


def _filter_options(db: Session, conditions: list[Any]) -> FilterOptions:
    def option(column: Any, label: str, empty_label: str) -> FilterOption:
        values = db.scalars(
            select(distinct(column)).where(*conditions).where(column.is_not(None)).order_by(column)
        ).all()
        return FilterOption(
            label=label,
            empty_label=empty_label,
            options=[[str(value), str(value)] for value in values if str(value).strip()],
        )

    return FilterOptions(
        claim_type=option(ReportingClaim.claim_type, "Type", "Tous les types"),
        agency=option(ReportingClaim.agency, "Agence", "Toutes les agences"),
        channel=option(ReportingClaim.channel, "Canal", "Tous les canaux"),
        category=option(ReportingClaim.category, "Categorie", "Toutes les categories"),
        risk_level=option(ReportingClaim.risk_level, "Risque", "Tous les risques"),
    )


def _persist_alerts(db: Session, alerts: list[Alert], detected_at: datetime) -> None:
    for alert in alerts:
        if not alert.id:
            continue
        existing = db.scalar(
            select(ReportingAlert).where(ReportingAlert.source_key == alert.id)
        )
        if existing is None:
            db.add(
                ReportingAlert(
                    source_key=alert.id,
                    alert_type=alert.id,
                    severity=alert.severity,
                    title=alert.title,
                    message=alert.message,
                    subtitle=alert.subtitle,
                    status=alert.status,
                    owner=alert.owner,
                    detected_at=alert.detected_at or detected_at,
                    source_rule=alert.id,
                    action=alert.action,
                    evidence=json.dumps(
                        {
                            "detected_at": (alert.detected_at or detected_at).isoformat(),
                            "message": alert.message,
                        },
                        ensure_ascii=False,
                    ),
                )
            )
            continue
        existing.severity = alert.severity
        existing.title = alert.title
        existing.message = alert.message
        existing.subtitle = alert.subtitle
        existing.action = alert.action
        existing.evidence = json.dumps(
            {
                "detected_at": (alert.detected_at or detected_at).isoformat(),
                "message": alert.message,
            },
            ensure_ascii=False,
        )
    db.flush()


def _group_chart(db: Session, conditions: list[Any], column: Any, label: str, limit: int = 10) -> ChartData:
    rows = db.execute(
        select(column, func.count(ReportingClaim.id))
        .where(*conditions)
        .where(column.is_not(None))
        .group_by(column)
        .order_by(func.count(ReportingClaim.id).desc(), column)
        .limit(limit)
    ).all()
    return ChartData(
        labels=[str(row[0]) for row in rows],
        datasets=[ChartDataset(label=label, data=[float(row[1]) for row in rows])],
    )


def _group_metric_chart(
    db: Session,
    conditions: list[Any],
    column: Any,
    label: str,
    extra: Any,
    limit: int = 10,
) -> ChartData:
    return _group_chart_with_expression(
        db, conditions, column, func.count(ReportingClaim.id), label, extra, limit
    )


def _group_chart_with_expression(
    db: Session,
    conditions: list[Any],
    column: Any,
    expression: Any,
    label: str,
    extra: Any = None,
    limit: int = 10,
) -> ChartData:
    query = (
        select(column, expression)
        .where(*conditions)
        .where(column.is_not(None))
        .group_by(column)
        .order_by(expression.desc(), column)
        .limit(limit)
    )
    if extra is not None:
        query = query.where(extra)
    rows = db.execute(query).all()
    return ChartData(
        labels=[str(row[0]) for row in rows],
        datasets=[ChartDataset(label=label, data=[round(float(row[1]), 1) for row in rows])],
    )


def _group_average_score_chart(
    db: Session,
    conditions: list[Any],
    column: Any,
    limit: int = 10,
) -> ChartData:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return _group_chart_with_expression(
        db,
        conditions,
        column,
        func.avg(_risk_score_expression(now)),
        "Score moyen",
        limit=limit,
    )


def _trend_chart(db: Session, conditions: list[Any]) -> ChartData:
    date_column = func.coalesce(ReportingClaim.created_at, ReportingClaim.receipt_at)
    if db.bind is not None and db.bind.dialect.name == "sqlite":
        period_column = func.strftime("%Y-%m", date_column)
    else:
        period_column = func.date_format(date_column, "%Y-%m")
    rows = db.execute(
        select(period_column, func.count(ReportingClaim.id))
        .where(*conditions)
        .where(func.coalesce(ReportingClaim.created_at, ReportingClaim.receipt_at).is_not(None))
        .group_by(period_column)
        .order_by(period_column)
    ).all()
    return ChartData(
        labels=[str(row[0]) for row in rows],
        datasets=[ChartDataset(label="Dossiers", data=[float(row[1]) for row in rows])],
    )


def build_dashboard(db: Session, filters: ReportingFilters) -> DashboardResponse:
    conditions = _conditions(filters)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    current_total, high_risk, overdue, active, risk_score = _metric_values(db, filters)
    previous = _previous_period(filters)
    previous_values = _metric_values(db, previous) if previous else None
    concentration_anomalies = _concentration_anomalies(db, conditions, current_total)
    moving_average_anomaly = _moving_average_anomaly(db, conditions)
    volume_change = (
        _percent_change(current_total, previous_values[0])
        if previous_values
        else None
    )

    charts = {
        "trend": _trend_chart(db, conditions),
        "channels": _group_chart(db, conditions, ReportingClaim.channel, "Dossiers"),
        "categories": _group_chart(db, conditions, ReportingClaim.category, "Dossiers"),
        "products": _group_chart(db, conditions, ReportingClaim.product, "Dossiers"),
        "risk": _group_chart(db, conditions, ReportingClaim.risk_level, "Dossiers"),
        "team_performance": _group_chart(
            db,
            conditions,
            func.coalesce(ReportingClaim.team, "Non assignee"),
            "Dossiers",
        ),
    }
    metrics = DashboardMetrics(
        total_claims=current_total,
        in_progress_claims=active,
        overdue_claims=overdue,
        severe_claims=high_risk,
        high_risk_claims=high_risk,
        anomalies=overdue,
        active_alerts=high_risk,
        risk_score=risk_score,
        total_claims_change=_percent_change(current_total, previous_values[0]) if previous_values else None,
        high_risk_claims_change=_percent_change(high_risk, previous_values[1]) if previous_values else None,
        anomalies_change=_percent_change(overdue, previous_values[2]) if previous_values else None,
        active_alerts_change=_percent_change(overdue, previous_values[2]) if previous_values else None,
        risk_score_change=_percent_change(risk_score, previous_values[4]) if previous_values else None,
    )
    alerts = []
    recommendations = []
    if overdue:
        alerts.append(
            Alert(
                id="overdue-claims",
                severity="high",
                title="Dossiers en retard",
                message=f"{overdue} dossier(s) ont depasse le SLA.",
                status="new",
                detected_at=now,
            )
        )
        recommendations.append(
            Recommendation(
                id="overdue-follow-up",
                title="Suivre les dossiers en retard",
                message="Prioriser les dossiers dont la date SLA est depassee.",
                priority="high",
            )
        )
    if volume_change is not None and volume_change >= 50:
        alerts.append(
            Alert(
                id="volume-increase",
                severity="medium",
                title="Hausse inhabituelle du volume",
                message=f"Le volume a augmente de {volume_change}% par rapport a la periode precedente.",
                status="new",
                detected_at=now,
                action="Verifier les causes de la hausse",
            )
        )
        recommendations.append(
            Recommendation(
                id="volume-increase-review",
                title="Analyser la hausse du volume",
                message="Verifier les categories, canaux et agences a l'origine de cette variation.",
                priority="medium",
            )
        )
    for dimension, value, count, share in concentration_anomalies:
        alerts.append(
            Alert(
                id=f"concentration-{dimension}",
                severity="medium",
                title=f"Concentration inhabituelle par {dimension}",
                message=f"{value} represente {share}% des dossiers ({count}/{current_total}).",
                status="new",
                detected_at=now,
                action=f"Verifier la concentration par {dimension}",
            )
        )
        recommendations.append(
            Recommendation(
                id=f"concentration-{dimension}-review",
                title=f"Analyser la concentration par {dimension}",
                message=f"Examiner les dossiers de la valeur {value} et verifier s'il existe une cause recurrente.",
                priority="medium",
            )
        )
    current_severe_rate = high_risk / current_total if current_total else 0
    previous_severe_rate = (
        previous_values[1] / previous_values[0]
        if previous_values and previous_values[0]
        else 0
    )
    severe_rate_change = current_severe_rate - previous_severe_rate
    if current_total >= 3 and severe_rate_change >= 0.2:
        alerts.append(
            Alert(
                id="severe-rate-increase",
                severity="high",
                title="Hausse du taux de dossiers graves",
                message=(
                    f"Le taux de dossiers graves est passe de "
                    f"{round(previous_severe_rate * 100, 1)}% a "
                    f"{round(current_severe_rate * 100, 1)}%."
                ),
                status="new",
                detected_at=now,
                action="Analyser les motifs des dossiers graves",
            )
        )
        recommendations.append(
            Recommendation(
                id="severe-rate-review",
                title="Analyser la hausse des dossiers graves",
                message="Examiner les motifs et canaux qui contribuent a cette hausse.",
                priority="high",
            )
        )
    if moving_average_anomaly is not None:
        current_month, baseline = moving_average_anomaly
        alerts.append(
            Alert(
                id="moving-average-increase",
                severity="medium",
                title="Depassement de la moyenne glissante",
                message=(
                    f"Le dernier mois compte {current_month} dossiers, "
                    f"contre une moyenne precedente de {baseline}."
                ),
                status="new",
                detected_at=now,
                action="Verifier la tendance mensuelle",
            )
        )
        recommendations.append(
            Recommendation(
                id="moving-average-review",
                title="Verifier la tendance mensuelle",
                message="Rechercher la cause du depassement de la moyenne des deux mois precedents.",
                priority="medium",
            )
        )
    _persist_alerts(db, alerts, now)
    db.commit()
    return DashboardResponse(
        periods=_periods(filters),
        filter_options=_filter_options(db, conditions),
        metrics=metrics,
        risk_summary=RiskSummary(
            scored_count=_count(
                db,
                conditions,
                or_(
                    ReportingClaim.risk_level.is_not(None),
                ),
            ),
            caption="Repartition des dossiers par niveau de risque",
            legends=[
                RiskLegend(label="Mineur", tone="success"),
                RiskLegend(label="Moyen", tone="warning"),
                RiskLegend(label="Grave", tone="danger"),
            ],
        ),
        risk_matrix=[
            RiskMatrixRow(label="Mineur", count=_count(db, conditions, ReportingClaim.risk_level == "MINEUR"), action="Traitement standard", tone="minor"),
            RiskMatrixRow(label="Moyen", count=_count(db, conditions, ReportingClaim.risk_level == "MOYEN"), action="Surveiller", tone="medium"),
            RiskMatrixRow(label="Grave", count=high_risk, action="Traiter en priorite", tone="danger"),
            RiskMatrixRow(label="En retard", count=overdue, action="Relancer le traitement", tone="warning"),
        ],
        charts=charts,
        recommendations=recommendations,
        alerts=alerts,
        details=DashboardDetails(
            risk=_detail_rows(db, conditions, ReportingClaim.risk_level == "GRAVE"),
            anomalies=_detail_rows(db, conditions, _overdue_condition(now)),
            alerts=_detail_rows(db, conditions, _overdue_condition(now)),
            total=_detail_rows(db, conditions),
            in_progress=_detail_rows(
                db,
                conditions,
                or_(
                    ReportingClaim.status.is_(None),
                    ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
                ),
            ),
            severe=_detail_rows(db, conditions, ReportingClaim.risk_level == "GRAVE"),
        ),
        generated_at=now,
    )


def answer_query(
    db: Session,
    question: str,
    filters: ReportingFilters,
    trace_id: str | None = None,
) -> ReportingQueryResponse:
    trace = trace_id or "-"
    started_at = perf_counter()
    trace_info(
        logger,
        trace,
        "reporting.query.received",
        question=question,
        request_filters=(
            filters.model_dump()
            if hasattr(filters, "model_dump")
            else filters.dict()
        ),
    )
    parsed_intent = interpret_question(question, filters, trace)
    if not parsed_intent.supported or parsed_intent.intent is None:
        logger.info("[%s] reporting.query.unsupported", trace)
        return ReportingQueryResponse(
            answer=parsed_intent.reason or "Cette analyse n'est pas disponible.",
            summary="Analyse non supportee",
            sources=["catalogue des intentions Reporting IA"],
        )
    intent = parsed_intent.intent
    filters = intent.filters
    if intent.comparison:
        filters = _copy_filters(
            filters,
            start_date=intent.comparison.current_start_date,
            end_date=intent.comparison.current_end_date,
        )
    trace_info(
        logger,
        trace,
        "reporting.filters.applied",
        claim_type=filters.claim_type,
        agency=filters.agency,
        channel=filters.channel,
        category=filters.category,
        product=filters.product,
        team=filters.team,
        status=filters.status,
        risk_level=filters.risk_level,
        period=f"{filters.start_date}..{filters.end_date}",
    )
    normalized = unicodedata.normalize("NFKD", question.lower()).encode(
        "ascii", "ignore"
    ).decode("ascii")
    conditions = _conditions(filters)
    analysis = intent.analysis
    metric = intent.metric or "count"
    trace_info(
        logger,
        trace,
        "reporting.aggregation.selected",
        metric=metric,
        group_by=intent.group_by,
        comparison=bool(intent.comparison),
    )

    is_trend = (analysis.operation == "trend" if analysis else metric == "trend") or any(
        word in normalized for word in ("evolution", "tendance", "par mois")
    )
    if analysis and analysis.kind == "business_metric":
        metric_label = {
            "sla_compliance_rate": "de conformite SLA",
            "average_resolution_time": "jours de resolution en moyenne",
            "risk_distribution": "avec un niveau de risque evalue",
        }[analysis.name]
    elif analysis and analysis.operation == "ratio":
        metric_label = f"de dossiers {analysis.condition}"
    elif analysis:
        metric_label = {
            "count": "dossiers" if analysis.target == "claim" else analysis.target,
            "count_distinct": f"{analysis.target} distincts",
            "sum": f"somme de {analysis.target}",
            "average": f"moyenne de {analysis.target}",
            "min": f"minimum de {analysis.target}",
            "max": f"maximum de {analysis.target}",
            "trend": "dans le temps",
        }.get(analysis.operation, analysis.name or "resultat")
        if analysis.target == "claim":
            metric_label = {
                "overdue": "en retard",
                "active": "en cours",
                "severe": "graves",
            }.get(analysis.condition, metric_label)
            if analysis.condition == "overdue" and filters.risk_level == SEVERE_URGENCY:
                metric_label = "graves en retard"
    else:
        metric_label = {
            "count_overdue": "en retard",
            "count_severe": "graves",
            "count_active": "en cours",
            "average_risk_score": "avec score moyen",
            "trend": "dans le temps",
        }.get(metric, "correspondant aux filtres demandes")
    grouped_comparison_data = None
    if analysis and intent.group_by and intent.comparison:
        chart, grouped_comparison_data = _group_comparison_chart(
            db,
            filters,
            analysis,
            intent.group_by,
            intent.comparison,
            intent.limit,
        )
        title = f"Comparaison par {intent.group_by}"
    elif analysis and intent.group_by:
        chart = _group_analysis_chart(
            db, filters, analysis, intent.group_by, intent.limit
        )
        if analysis.kind == "business_metric" and analysis.name == "sla_compliance_rate":
            chart_label = "Taux de conformite SLA (%)"
            if chart.datasets:
                chart.datasets[0].label = chart_label
        elif analysis.kind == "business_metric" and analysis.name == "average_resolution_time":
            if chart.datasets:
                chart.datasets[0].label = "Duree moyenne de resolution (jours)"
        elif analysis.kind == "business_metric" and analysis.name == "risk_distribution":
            if chart.datasets:
                chart.datasets[0].label = "Dossiers"
        elif analysis.operation == "ratio" and chart.datasets:
            chart.datasets[0].label = f"Part des dossiers {analysis.condition} (%)"
        elif analysis.target == "claim":
            chart_label = {
                "overdue": "Dossiers graves en retard"
                if filters.risk_level == SEVERE_URGENCY
                else "Dossiers en retard",
                "active": "Dossiers en cours",
                "severe": "Dossiers graves",
            }.get(analysis.condition)
            if chart_label and chart.datasets:
                chart.datasets[0].label = chart_label
        title = f"Analyse par {intent.group_by}"
    elif analysis and intent.group_by is None:
        chart = ChartData(
            labels=["Total"],
            datasets=[
                ChartDataset(
                    label=metric_label,
                    data=[_query_analysis_value(db, filters, analysis)],
                )
            ],
        )
        title = "Resultat global"
    elif is_trend:
        chart = _trend_chart(db, conditions)
        title = "Evolution des dossiers dans le temps"
    elif intent.group_by is None:
        chart = ChartData(
            labels=["Total"],
            datasets=[
                ChartDataset(
                    label=metric_label,
                    data=[_query_metric_value(db, filters, metric)],
                )
            ],
        )
        title = "Resultat global"
    else:
        groupings = (
            ("channel", ReportingClaim.channel, "Repartition des dossiers par canal"),
            ("category", ReportingClaim.category, "Repartition des dossiers par categorie"),
            ("motif", ReportingClaim.motif, "Repartition des dossiers par motif"),
            ("agency", ReportingClaim.agency, "Repartition des dossiers par agence"),
            ("team", ReportingClaim.team, "Repartition des dossiers par equipe"),
            ("product", ReportingClaim.product, "Repartition des dossiers par produit"),
            ("risk_level", ReportingClaim.risk_level, "Repartition des dossiers par risque"),
        )
        grouping = next(
            (item for item in groupings if item[0] == intent.group_by),
            None,
        )
        column = grouping[1]
        title = grouping[2]
        if metric == "count_overdue":
            extra = _overdue_condition(datetime.now(timezone.utc).replace(tzinfo=None))
            if "grave" in normalized or "haut risque" in normalized:
                extra = and_(extra, ReportingClaim.risk_level == SEVERE_URGENCY)
                metric_label = "graves en retard"
                value_label = "Dossiers graves en retard"
            else:
                metric_label = "en retard"
                value_label = "Dossiers en retard"
            chart = _group_metric_chart(db, conditions, column, value_label, extra)
        elif metric == "count_severe":
            chart = _group_metric_chart(
                db, conditions, column, "Dossiers graves",
                ReportingClaim.risk_level == SEVERE_URGENCY,
            )
        elif metric == "count_active":
            chart = _group_metric_chart(
                db, conditions, column, "Dossiers en cours",
                or_(
                    ReportingClaim.status.is_(None),
                    ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
                ),
            )
        elif metric == "average_risk_score":
            chart = _group_average_score_chart(db, conditions, column)
        else:
            chart = _group_chart(db, conditions, column, "Dossiers")
    if chart is None:
        trace_info(
            logger,
            trace,
            "reporting.visualization.skipped",
            reason="group_by_absent",
        )
    else:
        trace_info(
            logger,
            trace,
            "reporting.visualization.created",
            type="line" if is_trend else "bar",
            group_by=intent.group_by,
            grouped=intent.group_by is not None,
            labels=len(chart.labels),
            dataset=chart.datasets[0].label if chart.datasets else None,
        )
    value_for_filters = (
        (lambda selected_filters: _query_analysis_value(db, selected_filters, analysis))
        if analysis
        else (lambda selected_filters: _query_metric_value(db, selected_filters, metric))
    )
    total = value_for_filters(filters)
    comparison = None
    if intent.comparison:
        current_filters = _copy_filters(
            filters,
            start_date=intent.comparison.current_start_date,
            end_date=intent.comparison.current_end_date,
        )
        previous_filters = _copy_filters(
            filters,
            start_date=intent.comparison.previous_start_date,
            end_date=intent.comparison.previous_end_date,
        )
        current_value = value_for_filters(current_filters)
        previous_value = value_for_filters(previous_filters)
        comparison = ReportingComparisonResult(
            current_value=current_value,
            previous_value=previous_value,
            change_percent=_percent_change(current_value, previous_value),
        )
        trace_info(
            logger,
            trace,
            "reporting.comparison.completed",
            current=comparison.current_value,
            previous=comparison.previous_value,
            change_percent=comparison.change_percent,
        )
        direction = (
            "hausse" if comparison.change_percent is not None and comparison.change_percent > 0
            else "baisse" if comparison.change_percent is not None and comparison.change_percent < 0
            else "variation nulle"
        )
        answer = (
            f"{_analysis_summary(total, analysis, metric_label)} "
            f"Comparaison : {direction} de "
            f"{abs(comparison.change_percent or 0)}% par rapport a la periode precedente."
        )
    else:
        answer = _analysis_summary(total, analysis, metric_label)
    trace_info(
        logger,
        trace,
        "reporting.response.deterministic",
        answer=answer,
    )
    data = grouped_comparison_data or (
        [
            {"label": label, "value": value}
            for label, value in zip(chart.labels, chart.datasets[0].data)
        ]
        if chart is not None
        else []
    )
    logger.info(
        "[trace_id=%s] reporting.sql.results total=%s rows=%s",
        trace,
        total,
        len(data),
    )
    final_answer = formulate_answer(question, answer, data, trace)
    response = ReportingQueryResponse(
        answer=final_answer,
        summary=title,
        sources=["reporting_claim"],
        visualization=(
            Visualization(
                type="line" if is_trend else "bar",
                title=title,
                labels=chart.labels,
                datasets=chart.datasets,
            )
            if chart is not None
            else None
        ),
        data=data,
        comparison=comparison,
    )
    trace_info(
        logger,
        trace,
        "reporting.query.completed",
        duration_ms=round((perf_counter() - started_at) * 1000, 1),
        final_answer=response.answer,
    )
    return response
