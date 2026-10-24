from typing import FrozenSet

INCLUDED_CLAIM_TYPES: FrozenSet[str] = frozenset({"CLAIM", "DENUNCIACION"})
IN_PROGRESS_EXCLUDED_STATUSES: FrozenSet[str] = frozenset(
    {"SATISFIED", "CLASSED", "TEMP_SAVED"}
)
RISK_LEVELS: FrozenSet[str] = frozenset({"MINEUR", "MOYEN", "GRAVE"})
SEVERE_URGENCY = "GRAVE"
DEFAULT_SLA_DAYS = 3
DEFAULT_TIMEZONE = "Africa/Abidjan"
ALERT_STATUSES: FrozenSet[str] = frozenset(
    {"new", "in_progress", "resolved", "dismissed"}
)
CHART_TYPES: FrozenSet[str] = frozenset(
    {"bar", "line", "area", "doughnut", "pie"}
)
SUPPORTED_CHART_KEYS: FrozenSet[str] = frozenset(
    {
        "trend",
        "distribution",
        "channels",
        "categories",
        "products",
        "team_performance",
        "risk",
    }
)
