from types import MappingProxyType
from typing import Any, Mapping

from sqlalchemy import and_, func, or_

from app.db.models import ReportingClaim

from .constants import IN_PROGRESS_EXCLUDED_STATUSES, SEVERE_URGENCY

CATALOG_VERSION = "1.1.0"

TARGETS: Mapping[str, Any] = MappingProxyType(
    {
        "claim": ReportingClaim.id,
        "agency": ReportingClaim.agency,
        "category": ReportingClaim.category,
        "motif": ReportingClaim.motif,
        "product": ReportingClaim.product,
        "channel": ReportingClaim.channel,
        "team": ReportingClaim.team,
        "risk_level": ReportingClaim.risk_level,
        "service_point": ReportingClaim.service_point,
        "risk_score": ReportingClaim.ai_risk_score,
    }
)

DIMENSIONS = frozenset(
    {
        "agency",
        "category",
        "motif",
        "product",
        "channel",
        "team",
        "risk_level",
        "service_point",
        "month",
    }
)

FILTER_FIELDS = frozenset(
    {
        "start_date",
        "end_date",
        "claim_type",
        "agency",
        "channel",
        "category",
        "motif",
        "product",
        "team",
        "status",
        "risk_level",
        "service_point",
        "satisfaction_status",
    }
)

BUSINESS_CONDITIONS = frozenset(
    {"overdue", "active", "severe", "within_sla", "has_sla", "satisfied", "evaluated"}
)

SPECIALIZED_METRICS = MappingProxyType(
    {
        "sla_compliance_rate": MappingProxyType(
            {"group_by": DIMENSIONS, "requires_group_by": False}
        ),
        "average_resolution_time": MappingProxyType(
            {"group_by": DIMENSIONS, "requires_group_by": False}
        ),
        "risk_distribution": MappingProxyType(
            {"group_by": frozenset({"risk_level"}), "requires_group_by": True}
        ),
    }
)

_COUNT_TARGETS = frozenset(TARGETS)
_NUMERIC_TARGETS = frozenset({"risk_score"})
ANALYTIC_CATALOG = MappingProxyType(
    {
        "count": MappingProxyType({"targets": _COUNT_TARGETS, "conditions": BUSINESS_CONDITIONS}),
        "count_distinct": MappingProxyType(
            {"targets": _COUNT_TARGETS, "conditions": BUSINESS_CONDITIONS}
        ),
        "sum": MappingProxyType(
            {"targets": _NUMERIC_TARGETS, "conditions": BUSINESS_CONDITIONS}
        ),
        "average": MappingProxyType(
            {"targets": _NUMERIC_TARGETS, "conditions": BUSINESS_CONDITIONS}
        ),
        "min": MappingProxyType(
            {"targets": _NUMERIC_TARGETS, "conditions": BUSINESS_CONDITIONS}
        ),
        "max": MappingProxyType(
            {"targets": _NUMERIC_TARGETS, "conditions": BUSINESS_CONDITIONS}
        ),
        "ratio": MappingProxyType(
            {"targets": frozenset({"claim"}), "conditions": BUSINESS_CONDITIONS}
        ),
        "trend": MappingProxyType(
            {"targets": frozenset({"claim"}), "conditions": BUSINESS_CONDITIONS}
        ),
    }
)


def validate_grouping(
    kind: str,
    operation: str | None,
    target: str | None,
    name: str | None,
    group_by: str | None,
) -> str | None:
    if group_by is None:
        if kind == "business_metric" and SPECIALIZED_METRICS[name]["requires_group_by"]:
            return f"{name} exige le regroupement {next(iter(SPECIALIZED_METRICS[name]['group_by']))}."
        return None
    if group_by not in DIMENSIONS:
        return f"Dimension de regroupement non autorisee : {group_by}."
    if kind == "business_metric":
        if group_by not in SPECIALIZED_METRICS[name]["group_by"]:
            return f"{name} ne peut pas etre regroupe par {group_by}."
        return None
    if operation == "trend" and group_by != "month":
        return "trend exige group_by=month."
    return None


def condition_expression(name: str | None, now: Any) -> Any | None:
    if name is None:
        return None
    if name == "overdue":
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
    if name == "active":
        return or_(
            ReportingClaim.status.is_(None),
            ~ReportingClaim.status.in_(IN_PROGRESS_EXCLUDED_STATUSES),
        )
    if name == "severe":
        return ReportingClaim.risk_level == SEVERE_URGENCY
    if name == "has_sla":
        return ReportingClaim.sla_due_at.is_not(None)
    if name == "within_sla":
        return and_(
            ReportingClaim.sla_due_at.is_not(None),
            ReportingClaim.resolved_at.is_not(None),
            ReportingClaim.resolved_at <= ReportingClaim.sla_due_at,
        )
    if name == "satisfied":
        return func.upper(ReportingClaim.satisfaction_status).in_(
            ("SATISFIED", "SATISFAIT", "SATISFAITE")
        )
    if name == "evaluated":
        return ReportingClaim.satisfaction_status.is_not(None)
    raise ValueError(f"Condition metier non autorisee : {name}")


def validate_analysis(
    kind: str,
    operation: str | None,
    target: str | None,
    condition: str | None,
    name: str | None,
) -> str | None:
    if kind == "business_metric":
        if name not in SPECIALIZED_METRICS:
            return "Indicateur metier specialise non autorise."
        if any(value is not None for value in (operation, target, condition)):
            return "Un indicateur metier specialise ne doit pas definir operation, target ou condition."
        return None
    if kind != "primitive":
        return "Type d'analyse inconnu."
    if name is not None:
        return "name n'est autorise que pour une analyse business_metric."
    if operation not in ANALYTIC_CATALOG or target not in TARGETS:
        return "Operation ou cible absente du catalogue autorise."
    operation_definition = ANALYTIC_CATALOG[operation]
    if target not in operation_definition["targets"]:
        if operation in {"sum", "average", "min", "max"}:
            return f"{operation} exige une cible numerique autorisee : risk_score."
        return f"La cible {target} n'est pas autorisee pour {operation}."
    if condition is not None and condition not in operation_definition["conditions"]:
        return f"La condition {condition} n'est pas autorisee pour {operation}."
    if operation == "ratio" and condition is None:
        return "ratio exige une condition metier servant de numerateur."
    return None


def legacy_metric(
    operation: str | None,
    target: str | None,
    condition: str | None,
) -> str | None:
    if operation == "trend":
        return "trend"
    if operation == "average" and target == "risk_score":
        return "average_risk_score"
    if operation == "count" and target == "claim":
        if condition == "overdue":
            return "count_overdue"
        if condition == "severe":
            return "count_severe"
        if condition == "active":
            return "count_active"
        return "count"
    return None
