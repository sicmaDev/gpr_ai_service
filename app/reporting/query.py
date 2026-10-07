import calendar
import re
import unicodedata
from datetime import date, timedelta

from .schemas import (
    ReportingComparison,
    ReportingFilters,
    ReportingIntent,
    ReportingIntentResult,
)

GROUP_ALIASES = {
    "agence": "agency",
    "agences": "agency",
    "canal": "channel",
    "canaux": "channel",
    "categorie": "category",
    "categories": "category",
    "motif": "motif",
    "motifs": "motif",
    "produit": "product",
    "produits": "product",
    "equipe": "team",
    "equipes": "team",
    "risque": "risk_level",
    "risques": "risk_level",
    "mois": "month",
}
MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
}


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKD", value.lower()).encode(
        "ascii", "ignore"
    ).decode("ascii")


def _extract_value(text: str, labels: tuple[str, ...]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"\b(?:{label_pattern})\s+(?:de\s+|du\s+|d['’]\s+|:?\s*)([^,.!?;]+)",
        text,
    )
    if not match:
        return None
    raw_value = re.sub(
        r"^(?:entre|par|dans|sur|pour)\s+",
        "",
        match.group(1).strip(),
    )
    if raw_value.startswith(("septembre ", "aout ", "juillet ", "juin ")):
        return None
    value = re.split(
        r"\s+(?:et|en|avec|pour|ce|cette|cet|sur|entre|du|de|a|au|aux)\s+",
        raw_value,
        maxsplit=1,
    )[0].strip()
    return value.upper() or None


def _extract_filters(question: str, base: ReportingFilters) -> ReportingFilters:
    text = _normalize(question)
    values = {
        "agency": _extract_value(text, ("agence", "agences")),
        "channel": _extract_value(text, ("canal", "canaux")),
        "category": _extract_value(text, ("categorie", "categories")),
        "motif": _extract_value(text, ("motif", "motifs")),
        "product": _extract_value(text, ("produit", "produits")),
        "team": _extract_value(text, ("equipe", "equipes")),
        "service_point": _extract_value(
            text, ("point de service", "points de service")
        ),
        "status": _extract_value(text, ("statut", "statuts")),
        "satisfaction_status": _extract_value(
            text, ("statut de satisfaction", "statut satisfaction")
        ),
    }
    if "denonciation" in text:
        values["claim_type"] = "DENUNCIACION"
    elif "reclamation" in text or "plainte" in text or "plaintes" in text:
        values["claim_type"] = "CLAIM"
    if "grave" in text:
        values["risk_level"] = "GRAVE"
    elif "moyen" in text:
        values["risk_level"] = "MOYEN"
    elif "mineur" in text:
        values["risk_level"] = "MINEUR"
    updates = {key: value for key, value in values.items() if value}
    if hasattr(base, "model_copy"):
        return base.model_copy(update=updates)
    return base.copy(update=updates)


def extract_question_filters(question: str) -> ReportingFilters:
    return _extract_filters(question, ReportingFilters())


def _extract_group(text: str) -> str | None:
    for alias, group in GROUP_ALIASES.items():
        if group == "month":
            if re.search(rf"\bpar\s+{re.escape(alias)}\b", text):
                return group
            continue
        if re.search(rf"\b(?:par\s+)?{re.escape(alias)}\b", text):
            return group
    return None


def _extract_comparison(text: str, today: date) -> ReportingComparison | None:
    intervals = _extract_intervals(text, today)
    if len(intervals) >= 2 and any(
        word in text for word in ("compare", "comparaison", "par rapport", "entre")
    ):
        current_start, current_end = intervals[0]
        previous_start, previous_end = intervals[1]
        return ReportingComparison(
            current_start_date=current_start,
            current_end_date=current_end,
            previous_start_date=previous_start,
            previous_end_date=previous_end,
        )
    month_matches = list(re.finditer(
        r"\b(" + "|".join(MONTHS) + r")\s*(20\d{2})?\b",
        text,
    ))
    if len(month_matches) >= 2 and any(
        word in text for word in ("compare", "comparaison", "par rapport", "entre")
    ):
        current = _month_range(
            MONTHS[month_matches[0].group(1)],
            int(month_matches[0].group(2) or today.year),
        )
        previous = _month_range(
            MONTHS[month_matches[1].group(1)],
            int(month_matches[1].group(2) or today.year),
        )
        return ReportingComparison(
            current_start_date=current[0],
            current_end_date=current[1],
            previous_start_date=previous[0],
            previous_end_date=previous[1],
        )
    if not any(word in text for word in ("compare", "comparaison", "par rapport", "mois dernier")):
        return None
    current_start = today.replace(day=1)
    previous_end = current_start - timedelta(days=1)
    return ReportingComparison(
        current_start_date=current_start,
        current_end_date=today,
        previous_start_date=previous_end.replace(day=1),
        previous_end_date=previous_end,
    )


def _month_range(month: int, year: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def _extract_intervals(text: str, today: date) -> list[tuple[date, date]]:
    intervals: list[tuple[date, date]] = []
    pattern = (
        r"\bdu\s+(\d{1,2})\s+(?:au|a)\s+(\d{1,2})\s+("
        + "|".join(MONTHS)
        + r")(?:\s+(20\d{2}))?\b"
    )
    for match in re.finditer(pattern, text):
        month = MONTHS[match.group(3)]
        year = int(match.group(4) or today.year)
        start = date(year, month, int(match.group(1)))
        end = date(year, month, int(match.group(2)))
        if start <= end:
            intervals.append((start, end))
    return intervals


def _extract_period(text: str, today: date) -> tuple[date, date] | None:
    intervals = _extract_intervals(text, today)
    if intervals:
        return intervals[0]
    month = re.search(
        r"\b(?:en|du|de|pour)\s+(" + "|".join(MONTHS) + r")(?:\s+(20\d{2}))?\b",
        text,
    )
    if month:
        return _month_range(
            MONTHS[month.group(1)],
            int(month.group(2) or today.year),
        )
    if re.search(r"\bce\s+moi?s?\s+ci\b|\bmois\s+en\s+cours\b", text):
        return date(today.year, today.month, 1), today
    return None


def parse_intent(
    question: str,
    filters: ReportingFilters | None = None,
    today: date | None = None,
) -> ReportingIntentResult:
    text = _normalize(question)
    reference_date = today or date.today()
    extracted_filters = _extract_filters(question, filters or ReportingFilters())
    period = _extract_period(text, reference_date)
    if period:
        updates = {"start_date": period[0], "end_date": period[1]}
        if hasattr(extracted_filters, "model_copy"):
            extracted_filters = extracted_filters.model_copy(update=updates)
        else:
            extracted_filters = extracted_filters.copy(update=updates)
    group_by = _extract_group(text)
    if any(word in text for word in ("retard", "retards", "depasse", "sla")):
        metric = "count_overdue"
    elif "score moyen" in text or "moyenne du score" in text:
        metric = "average_risk_score"
    elif "grave" in text or "graves" in text:
        metric = "count_severe"
    elif any(word in text for word in ("en cours", "actifs", "actif")):
        metric = "count_active"
    elif any(word in text for word in ("evolution", "tendance", "historique", "par mois")):
        metric = "trend"
        group_by = group_by or "month"
    elif any(word in text for word in ("volume", "nombre", "combien", "total")):
        metric = "count"
    elif group_by:
        metric = "count"
    else:
        return ReportingIntentResult(
            supported=False,
            reason=(
                "Analyse non supportee. Utilisez une metrique de volume, "
                "dossiers en cours, en retard, graves, score moyen ou tendance."
            ),
        )
    return ReportingIntentResult(
        supported=True,
        intent=ReportingIntent(
            metric=metric,
            group_by=group_by,
            filters=extracted_filters,
            comparison=_extract_comparison(text, reference_date),
        ),
    )
