import calendar
from datetime import date, timedelta


SUPPORTED_PERIODS = {
    "today",
    "yesterday",
    "current_week",
    "previous_week",
    "current_month",
    "previous_month",
    "current_quarter",
    "previous_quarter",
    "current_year",
    "previous_year",
}


def resolve_period(period: str, reference_date: date) -> tuple[date, date]:
    if period not in SUPPORTED_PERIODS:
        raise ValueError(f"Periode semantique non autorisee : {period}")
    if period == "today":
        return reference_date, reference_date
    if period == "yesterday":
        previous = reference_date - timedelta(days=1)
        return previous, previous
    if period in {"current_week", "previous_week"}:
        current_start = reference_date - timedelta(days=reference_date.weekday())
        if period == "previous_week":
            current_start -= timedelta(days=7)
        return current_start, current_start + timedelta(days=6)
    if period in {"current_month", "previous_month"}:
        month = reference_date.month
        year = reference_date.year
        if period == "previous_month":
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day)
        if period == "current_month":
            end = reference_date
        return start, end
    quarter = (reference_date.month - 1) // 3
    if period == "previous_quarter":
        quarter -= 1
        if quarter < 0:
            quarter = 3
            year = reference_date.year - 1
        else:
            year = reference_date.year
    else:
        year = reference_date.year
    start_month = quarter * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    end = date(year, end_month, calendar.monthrange(year, end_month)[1])
    if period == "current_quarter":
        end = reference_date
    return start, end
