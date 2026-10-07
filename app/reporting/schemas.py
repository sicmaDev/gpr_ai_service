from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .constants import CHART_TYPES, RISK_LEVELS


class ReportingFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    claim_type: Optional[str] = None
    agency: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None
    team: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    motif: Optional[str] = None
    service_point: Optional[str] = None
    satisfaction_status: Optional[str] = None

    @validator(
        "claim_type",
        "agency",
        "channel",
        "category",
        "product",
        "team",
        "status",
        "risk_level",
        "motif",
        "service_point",
        "satisfaction_status",
    )
    def normalize_filter_value(cls, value):
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @validator("claim_type")
    def validate_claim_type(cls, value):
        if value is not None and value.upper() not in {"CLAIM", "DENUNCIACION"}:
            raise ValueError("claim_type doit être CLAIM ou DENUNCIACION")
        return value.upper() if value else value

    @validator("status")
    def normalize_status(cls, value):
        return value.upper() if value else value

    @validator("risk_level")
    def validate_risk_level(cls, value):
        if value is not None and value.upper() not in RISK_LEVELS:
            raise ValueError("risk_level doit être MINEUR, MOYEN ou GRAVE")
        return value.upper() if value else value

    @validator("end_date")
    def validate_date_range(cls, value, values):
        start_date = values.get("start_date")
        if value and start_date and start_date > value:
            raise ValueError("start_date doit être antérieure ou égale à end_date")
        return value


class Period(BaseModel):
    value: str
    label: str
    start_date: date
    end_date: date
    default: bool = False


class FilterOption(BaseModel):
    label: str
    empty_label: str
    options: List[List[str]] = Field(default_factory=list)


class FilterOptions(BaseModel):
    claim_type: Optional[FilterOption] = None
    agency: Optional[FilterOption] = None
    channel: Optional[FilterOption] = None
    category: Optional[FilterOption] = None
    risk_level: Optional[FilterOption] = None


class DashboardMetrics(BaseModel):
    total_claims: int = 0
    in_progress_claims: int = 0
    overdue_claims: int = 0
    severe_claims: int = 0
    high_risk_claims: int = 0
    anomalies: int = 0
    active_alerts: int = 0
    risk_score: float = 0
    total_claims_change: Optional[float] = None
    high_risk_claims_change: Optional[float] = None
    anomalies_change: Optional[float] = None
    active_alerts_change: Optional[float] = None
    risk_score_change: Optional[float] = None


class RiskLegend(BaseModel):
    label: str
    tone: str


class RiskSummary(BaseModel):
    scored_count: int = 0
    caption: str = ""
    legends: List[RiskLegend] = Field(default_factory=list)
    note: str = ""


class RiskMatrixRow(BaseModel):
    label: str
    count: int = 0
    change: str = ""
    action: str = ""
    tone: str


class ChartDataset(BaseModel):
    label: Optional[str] = None
    data: List[float] = Field(default_factory=list)
    backgroundColor: Optional[Any] = None
    borderColor: Optional[Any] = None
    fill: Optional[bool] = None


class ChartData(BaseModel):
    labels: List[str] = Field(default_factory=list)
    datasets: List[ChartDataset] = Field(default_factory=list)


class Recommendation(BaseModel):
    id: Optional[str] = None
    title: str
    message: Optional[str] = None
    priority: Optional[str] = None
    code: Optional[str] = None
    data: Optional[str] = None
    impact: Optional[str] = None
    action: Optional[str] = None


class Alert(BaseModel):
    id: Optional[str] = None
    severity: str
    title: str
    message: Optional[str] = None
    subtitle: Optional[str] = None
    status: str
    detected_at: Optional[datetime] = None
    owner: Optional[str] = None
    action: Optional[str] = None


class DashboardDetails(BaseModel):
    total: List[Dict[str, Any]] = Field(default_factory=list)
    in_progress: List[Dict[str, Any]] = Field(default_factory=list)
    severe: List[Dict[str, Any]] = Field(default_factory=list)
    risk: List[Dict[str, Any]] = Field(default_factory=list)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    periods: List[Period] = Field(default_factory=list)
    filter_options: FilterOptions = Field(default_factory=FilterOptions)
    metrics: DashboardMetrics = Field(default_factory=DashboardMetrics)
    risk_summary: RiskSummary = Field(default_factory=RiskSummary)
    risk_matrix: List[RiskMatrixRow] = Field(default_factory=list)
    charts: Dict[str, ChartData] = Field(default_factory=dict)
    recommendations: List[Recommendation] = Field(default_factory=list)
    alerts: List[Alert] = Field(default_factory=list)
    details: DashboardDetails = Field(default_factory=DashboardDetails)
    generated_at: datetime


class ReportingQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    filters: ReportingFilters = Field(default_factory=ReportingFilters)

    @validator("question")
    def normalize_question(cls, value):
        normalized = value.strip()
        if not normalized:
            raise ValueError("question ne peut pas être vide")
        return normalized


class ReportingComparison(BaseModel):
    current_start_date: date
    current_end_date: date
    previous_start_date: date
    previous_end_date: date

    @validator("current_end_date")
    def validate_current_range(cls, value, values):
        start_date = values.get("current_start_date")
        if start_date and start_date > value:
            raise ValueError("current_start_date doit precéder current_end_date")
        return value

    @validator("previous_end_date")
    def validate_previous_range(cls, value, values):
        start_date = values.get("previous_start_date")
        if start_date and start_date > value:
            raise ValueError("previous_start_date doit precéder previous_end_date")
        return value


class ReportingDateRange(BaseModel):
    start_date: date
    end_date: date

    @validator("end_date")
    def validate_range(cls, value, values):
        start_date = values.get("start_date")
        if start_date and start_date > value:
            raise ValueError("start_date doit etre anterieure ou egale a end_date")
        return value


class ReportingAnalysis(BaseModel):
    kind: str = "primitive"
    operation: Optional[str] = None
    target: Optional[str] = None
    condition: Optional[str] = None
    name: Optional[str] = None


class ReportingIntent(BaseModel):
    catalog_version: Optional[str] = None
    metric: Optional[str] = None
    analysis: Optional[ReportingAnalysis] = None
    group_by: Optional[str] = None
    filters: ReportingFilters = Field(default_factory=ReportingFilters)
    period: Optional[Union[str, ReportingDateRange]] = None
    limit: int = Field(default=10, ge=1, le=50)
    comparison: Optional[ReportingComparison] = None


class ReportingIntentResult(BaseModel):
    supported: bool
    intent: Optional[ReportingIntent] = None
    reason: Optional[str] = None


class ReportingComparisonResult(BaseModel):
    current_value: float
    previous_value: float
    change_percent: Optional[float] = None


class Visualization(BaseModel):
    type: str
    title: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    datasets: List[ChartDataset] = Field(default_factory=list)

    @validator("type")
    def validate_type(cls, value):
        normalized = value.strip().lower()
        if normalized not in CHART_TYPES:
            raise ValueError("type de visualisation non pris en charge")
        return normalized


class ReportingQueryResponse(BaseModel):
    answer: str
    summary: str = ""
    sources: List[str] = Field(default_factory=list)
    visualization: Optional[Visualization] = None
    data: List[Dict[str, Any]] = Field(default_factory=list)
    comparison: Optional[ReportingComparisonResult] = None
