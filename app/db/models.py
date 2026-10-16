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
    objet_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    service_point_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    collection_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    collector_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ReportingSuggestion(Base):
    __tablename__ = "reporting_suggestion"
    __table_args__ = (
        UniqueConstraint("source_suggestion_id", name="uq_reporting_suggestion_source_id"),
        Index("ix_reporting_suggestion_status", "status"),
        Index("ix_reporting_suggestion_impact_level", "impact_level"),
        Index("ix_reporting_suggestion_recorded_at", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_suggestion_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    client_code: Mapped[Optional[str]] = mapped_column(String(255))
    client_name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    channel: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[Optional[str]] = mapped_column(String(40))
    impact_level: Mapped[Optional[str]] = mapped_column(String(40))
    origine: Mapped[Optional[str]] = mapped_column(String(100))
    objet_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    service_point_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    collection_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    enregistre_par_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    evaluator_notes: Mapped[Optional[str]] = mapped_column(Text)
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ReportingHistoriqueAffectation(Base):
    __tablename__ = "reporting_historique_affectations"
    __table_args__ = (
        Index("ix_reporting_hist_aff_date", "date_affectation"),
        Index("ix_reporting_hist_aff_prev", "affectation_precedente_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reclamation_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    suggestion_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    code_plainte: Mapped[Optional[str]] = mapped_column(String(255))
    type_plainte: Mapped[Optional[str]] = mapped_column(String(40))
    nom_agent: Mapped[Optional[str]] = mapped_column(String(255))
    email_agent: Mapped[Optional[str]] = mapped_column(String(255))
    affecteur_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    nom_affecteur: Mapped[Optional[str]] = mapped_column(String(255))
    email_affecteur: Mapped[Optional[str]] = mapped_column(String(255))
    date_affectation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delai_jours: Mapped[Optional[int]] = mapped_column(Integer, default=2)
    date_fin_affectation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    affectation_precedente_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_notification: Mapped[Optional[datetime]] = mapped_column(DateTime)
    mail_envoye: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    sms_envoye: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)


class ReportingPoste(Base):
    __tablename__ = "reporting_poste"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)


class ReportingServicePoint(Base):
    __tablename__ = "reporting_service_point"
    __table_args__ = (
        Index("ix_reporting_sp_libelle", "libelle"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(String(50), default="AGENCE")
    is_principal_agence: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    direction_id: Mapped[Optional[int]] = mapped_column(BigInteger)


class ReportingCollectionChannel(Base):
    __tablename__ = "reporting_collection_channel"
    __table_args__ = (
        Index("ix_reporting_cc_libelle", "libelle"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)


class ReportingProduct(Base):
    __tablename__ = "reporting_product"
    __table_args__ = (
        Index("ix_reporting_prod_libelle", "libelle"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)


class ReportingCategorieObjet(Base):
    __tablename__ = "reporting_categorie_objet"
    __table_args__ = (
        Index("ix_reporting_cat_libelle", "libelle"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)


class ReportingObjet(Base):
    __tablename__ = "reporting_objet"
    __table_args__ = (
        Index("ix_reporting_obj_libelle", "libelle"),
        Index("ix_reporting_obj_categorie", "categorie_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    categorie_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    risque_level: Mapped[Optional[str]] = mapped_column(String(40))
    processing_time: Mapped[Optional[int]] = mapped_column(Integer, default=2)


class ReportingUser(Base):
    __tablename__ = "reporting_user"
    __table_args__ = (
        Index("ix_reporting_user_code", "code"),
        Index("ix_reporting_user_email", "email"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    firstandlastname: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    additionalrole: Mapped[Optional[str]] = mapped_column(String(255))
    service_point_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    poste_id: Mapped[Optional[int]] = mapped_column(BigInteger)


class ReportingSolution(Base):
    __tablename__ = "reporting_solution"
    __table_args__ = (
        Index("ix_reporting_sol_claim", "claim_id"),
        Index("ix_reporting_sol_status", "status"),
        Index("ix_reporting_sol_author", "author_id"),
        Index("ix_reporting_sol_approver", "approver_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    claim_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    commentaire: Mapped[Optional[str]] = mapped_column(Text)
    motif_desaprobation: Mapped[Optional[str]] = mapped_column(Text)
    approver_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    unapproved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_ai_proposed: Mapped[Optional[bool]] = mapped_column(Boolean)
    ai_selected_solution: Mapped[Optional[str]] = mapped_column(Text)


class ReportingSatisfactionMeasure(Base):
    __tablename__ = "reporting_satisfaction_measure"
    __table_args__ = (
        Index("ix_reporting_sat_solution", "solution_id"),
        Index("ix_reporting_sat_measurer", "measurer_id"),
        Index("ix_reporting_sat_status", "status"),
        Index("ix_reporting_sat_date", "measure_date_time"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    solution_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    measurer_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    commentaire: Mapped[Optional[str]] = mapped_column(Text)
    measure_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)


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
