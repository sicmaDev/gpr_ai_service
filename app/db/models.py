from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .session import Base


class ReportingClaim(Base):
    __tablename__ = "reporting_claim"
    __table_args__ = (
        UniqueConstraint("source_claim_id", name="uq_reporting_claim_source_id"),
        Index("ix_reporting_claim_source_updated_at", "source_updated_at"),
        Index("ix_reporting_claim_created_at", "created_at"),
        Index("ix_reporting_claim_claim_type", "claim_type"),
        Index("ix_reporting_claim_status", "status"),
        Index("ix_reporting_claim_category", "category"),
        Index("ix_reporting_claim_agency", "agency"),
        Index("ix_reporting_claim_channel", "channel"),
        Index("ix_reporting_claim_risk_level", "risk_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_claim_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_code: Mapped[Optional[str]] = mapped_column(String(255))
    client_code: Mapped[Optional[str]] = mapped_column(String(255))
    claim_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(40))
    category: Mapped[Optional[str]] = mapped_column(String(255))
    motif: Mapped[Optional[str]] = mapped_column(String(255))
    product: Mapped[Optional[str]] = mapped_column(String(255))
    service_point: Mapped[Optional[str]] = mapped_column(String(255))
    agency: Mapped[Optional[str]] = mapped_column(String(255))
    channel: Mapped[Optional[str]] = mapped_column(String(255))
    team: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    solution: Mapped[Optional[str]] = mapped_column(Text)
    ai_urgency: Mapped[Optional[str]] = mapped_column(String(40))
    ai_sentiment: Mapped[Optional[str]] = mapped_column(String(40))
    risk_level: Mapped[Optional[str]] = mapped_column(String(40))
    ai_risk_score: Mapped[Optional[float]] = mapped_column(Float)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    receipt_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    source_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    affected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    satisfaction_status: Mapped[Optional[str]] = mapped_column(String(40))
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ReportingSyncState(Base):
    __tablename__ = "reporting_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    last_successful_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    last_received_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_ignored_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_deleted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_indexed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)


class ReportingAlert(Base):
    __tablename__ = "reporting_alert"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_reporting_alert_source_key"),
        Index("ix_reporting_alert_status", "status"),
        Index("ix_reporting_alert_detected_at", "detected_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_key: Mapped[str] = mapped_column(String(150), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    subtitle: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new")
    owner: Mapped[Optional[str]] = mapped_column(String(255))
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    source_rule: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[Optional[str]] = mapped_column(Text)


class ReportingCertifiedQuery(Base):
    __tablename__ = "reporting_certified_queries"
    __table_args__ = (
        Index("ix_certified_queries_status", "status"),
        Index("ix_certified_queries_schema_version", "schema_version"),
        Index("ix_certified_queries_intent_hash", "intent_hash"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    intent_hash: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contract_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    natural_language_query: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_intent: Mapped[dict] = mapped_column(JSON, nullable=False)
    parameterized_sql: Mapped[str] = mapped_column(Text, nullable=False)
    parameters_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="APPROVED")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deprecation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    execution_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportingBusinessMetric(Base):
    __tablename__ = "reporting_business_metrics"
    __table_args__ = (
        Index("ix_business_metrics_target_concept", "target_concept"),
    )

    metric_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_concept: Mapped[str] = mapped_column(String(64), nullable=False, default="plainte")
    required_tables: Mapped[list] = mapped_column(JSON, nullable=False)
    aggregation_sql_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
