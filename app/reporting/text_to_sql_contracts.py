from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    constr,
    field_validator,
    model_validator,
)

NonEmptyString = constr(strip_whitespace=True, min_length=1)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ==============================================================================
# BRIQUE 1 : Contrats d'Intention Canonique (CanonicalIntent / TextToSQLIntent)
# ==============================================================================

# Entité unique centrale 'plainte' (avec 'case', 'treatment', 'metrics' autorisés)
IntentConceptId = Literal["plainte", "case", "treatment", "metrics"]
IntentClaimType = Literal["CLAIM", "DENUNCIATION", "DENUNCIACION", "SUGGESTION"]


class IntentEntity(ContractModel):
    concept_id: IntentConceptId = "plainte"
    types: List[IntentClaimType] = Field(default_factory=list)
    include_all_types: bool = False

    @model_validator(mode="after")
    def validate_types(self) -> "IntentEntity":
        if self.include_all_types:
            # Quand include_all_types est True, soit types est vide soit il contient l'ensemble des 3 types
            valid_full_sets = [
                {"CLAIM", "DENUNCIATION", "SUGGESTION"},
                {"CLAIM", "DENUNCIACION", "SUGGESTION"},
            ]
            if len(self.types) > 0 and set(self.types) not in valid_full_sets:
                raise ValueError("types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true")
        else:
            if not self.types:
                raise ValueError("types doit contenir au moins un type de dossier lorsque include_all_types vaut false")
        return self


MeasureConceptId = Literal[
    "plainte_count",
    "reclamation_count",
    "denonciation_count",
    "case_count",
    "suggestion_count",
    "avg_processing_time",
    "sla_adherence_rate",
    "satisfaction_rate",
    "severe_plainte_count",
    "reaffectation_count",
    "adoption_rate",
]

MeasureOperation = Literal["count", "avg", "rate", "sum"]


class IntentMeasure(ContractModel):
    concept_id: MeasureConceptId = "plainte_count"
    operation: MeasureOperation = "count"
    target_concept: Literal["plainte", "case", "suggestion", "treatment"] = "plainte"
    label: NonEmptyString


DimensionConceptId = Literal[
    "claim_type",
    "type_plainte",
    "status",
    "agency",
    "channel",
    "category",
    "object",
    "product",
    "impact_level",
    "risk_level",
    "agent",
    "period",
]


class IntentDimension(ContractModel):
    concept_id: DimensionConceptId
    label: NonEmptyString


FilterOperator = Literal["equals", "in", "greater_than", "less_than", "between"]


class IntentFilter(ContractModel):
    concept_id: DimensionConceptId
    operator: FilterOperator
    value: Optional[Any] = None
    values: Optional[List[Any]] = None

    @model_validator(mode="after")
    def validate_filter_values(self) -> "IntentFilter":
        if self.operator == "in":
            if self.value is not None or not self.values or len(self.values) == 0:
                raise ValueError("L'operateur 'in' exige une liste 'values' non vide et 'value' a None")
        elif self.operator == "between":
            if self.value is not None or not self.values or len(self.values) != 2:
                raise ValueError("L'operateur 'between' exige 'values' contenant exactement 2 bornes [debut, fin] et 'value' a None")
        else:
            # equals, greater_than, less_than
            if self.value is None or self.values is not None:
                raise ValueError(f"L'operateur '{self.operator}' exige 'value' defini et 'values' a None")
        return self


TimeFieldConcept = Literal["receipt_date", "recorded_date", "resolved_date", "created_date"]


class IntentTime(ContractModel):
    field_concept: TimeFieldConcept = "receipt_date"
    start_date: date
    end_date: date
    timezone: Literal["Africa/Porto-Novo"] = "Africa/Porto-Novo"

    @model_validator(mode="after")
    def validate_range(self) -> "IntentTime":
        if self.start_date > self.end_date:
            raise ValueError("start_date doit etre anterieure ou egale a end_date")
        return self


class IntentClarification(ContractModel):
    code: NonEmptyString
    message: NonEmptyString
    question: NonEmptyString


class TextToSQLIntent(ContractModel):
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["ready", "needs_clarification", "unsupported"]
    entity: Optional[IntentEntity] = None
    measure: Optional[IntentMeasure] = None
    dimensions: List[IntentDimension] = Field(default_factory=list)
    filters: List[IntentFilter] = Field(default_factory=list)
    time: Optional[IntentTime] = None
    clarification: Optional[IntentClarification] = None
    unsupported_reason: Optional[NonEmptyString] = None

    @model_validator(mode="after")
    def validate_status_contract(self) -> "TextToSQLIntent":
        if self.status == "ready":
            if self.entity is None or self.measure is None:
                raise ValueError("ready exige entity et measure")
            if self.clarification is not None:
                raise ValueError("ready ne doit pas contenir de clarification")
            if self.unsupported_reason is not None:
                raise ValueError("ready ne doit pas contenir unsupported_reason")
        else:
            if self.entity is not None or self.measure is not None:
                raise ValueError(f"{self.status} exige entity et measure a null")
            if len(self.dimensions) > 0 or len(self.filters) > 0 or self.time is not None:
                raise ValueError(f"{self.status} ne doit pas contenir de champs executables")
            if self.status == "needs_clarification":
                if self.clarification is None:
                    raise ValueError("needs_clarification exige clarification")
                if self.unsupported_reason is not None:
                    raise ValueError("needs_clarification ne doit pas contenir unsupported_reason")
            elif self.status == "unsupported":
                if self.unsupported_reason is None:
                    raise ValueError("unsupported exige unsupported_reason")
                if self.clarification is not None:
                    raise ValueError("unsupported ne doit pas contenir clarification")
        return self


# ==============================================================================
# BRIQUE 2 : Contrats du Schema Catalog (SchemaCatalog)
# ==============================================================================

SQLDataType = Literal[
    "BIGINT", "VARCHAR", "DATETIME", "DATE", "INT", "DOUBLE", "BOOLEAN", "TEXT"
]


class ColumnMetadata(ContractModel):
    name: NonEmptyString
    data_type: SQLDataType
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references_table: Optional[NonEmptyString] = None
    references_column: Optional[NonEmptyString] = None
    is_nullable: bool = True
    is_indexed: bool = False
    is_sensitive: bool = False
    description: NonEmptyString

    @model_validator(mode="after")
    def validate_foreign_key(self) -> "ColumnMetadata":
        if self.is_foreign_key and (not self.references_table or not self.references_column):
            raise ValueError("Une cle etrangere doit specifier references_table et references_column")
        if not self.is_foreign_key and (self.references_table or self.references_column):
            raise ValueError("references_table et references_column exigent is_foreign_key=True")
        return self


TableType = Literal["fact", "dimension", "workflow", "admin"]


class TableMetadata(ContractModel):
    name: NonEmptyString
    table_type: TableType
    primary_key: NonEmptyString
    description: NonEmptyString
    columns: Dict[NonEmptyString, ColumnMetadata]

    @model_validator(mode="after")
    def validate_primary_key(self) -> "TableMetadata":
        if self.primary_key not in self.columns:
            raise ValueError(f"La cle primaire '{self.primary_key}' doit exister dans les colonnes de la table '{self.name}'")
        return self


JoinType = Literal["INNER JOIN", "LEFT JOIN"]


class RelationshipMetadata(ContractModel):
    name: NonEmptyString
    source_table: NonEmptyString
    source_column: NonEmptyString
    target_table: NonEmptyString
    target_column: NonEmptyString
    join_type: JoinType = "INNER JOIN"
    description: NonEmptyString


class SchemaCatalog(ContractModel):
    schema_version: NonEmptyString = "1.0.0"
    database_name: NonEmptyString = "gpr_ai_reporting"
    tables: Dict[NonEmptyString, TableMetadata]
    relationships: List[RelationshipMetadata] = Field(default_factory=list)


# ==============================================================================
# BRIQUE 3 : Contrats du Business Catalog (BusinessCatalog)
# ==============================================================================


class MetricDefinition(ContractModel):
    metric_id: NonEmptyString
    label: NonEmptyString
    description: NonEmptyString
    required_tables: List[NonEmptyString]
    aggregation_sql_template: NonEmptyString


class DimensionDefinition(ContractModel):
    dimension_id: NonEmptyString
    label: NonEmptyString
    source_table: NonEmptyString
    source_column: NonEmptyString
    join_path: Optional[NonEmptyString] = None


class BusinessConcept(ContractModel):
    concept_id: NonEmptyString
    label: NonEmptyString
    description: NonEmptyString
    target_table: NonEmptyString
    target_columns: List[NonEmptyString] = Field(default_factory=list)


class BusinessCatalog(ContractModel):
    catalog_version: NonEmptyString = "1.0.0"
    concepts: Dict[NonEmptyString, BusinessConcept] = Field(default_factory=dict)
    metrics: Dict[NonEmptyString, MetricDefinition]
    dimensions: Dict[NonEmptyString, DimensionDefinition]
    synonyms: Dict[NonEmptyString, List[NonEmptyString]] = Field(default_factory=dict)


# ==============================================================================
# BRIQUE 4 : Contrats du SQL Candidat & Validation AST
# ==============================================================================

ParameterType = Literal["date", "datetime", "string", "integer", "decimal", "boolean"]


class CandidateParameter(ContractModel):
    type: ParameterType
    source: NonEmptyString


ColumnRole = Literal["dimension", "measure"]
ResultDataType = Literal["string", "integer", "decimal", "boolean", "date", "datetime"]


class CandidateResultColumn(ContractModel):
    name: NonEmptyString
    concept_id: NonEmptyString
    role: ColumnRole
    data_type: ResultDataType


class TextToSQLCandidate(ContractModel):
    contract_version: Literal["1.0"] = "1.0"
    sql: NonEmptyString
    parameters: Dict[NonEmptyString, CandidateParameter] = Field(default_factory=dict)
    used_schema: List[NonEmptyString] = Field(default_factory=list)
    result_columns: List[CandidateResultColumn]
    assumptions: List[NonEmptyString] = Field(default_factory=list)

    @field_validator("result_columns")
    @classmethod
    def validate_result_columns(cls, value: List[CandidateResultColumn]) -> List[CandidateResultColumn]:
        if not value or len(value) == 0:
            raise ValueError("result_columns doit contenir au moins une colonne")
        names = [column.name for column in value]
        if len(names) != len(set(names)):
            raise ValueError("les noms de result_columns doivent etre uniques")
        return value


class SqlValidationResult(ContractModel):
    is_valid: bool
    ast_digest: Optional[NonEmptyString] = None
    allowed_tables_checked: List[NonEmptyString] = Field(default_factory=list)
    allowed_columns_checked: List[NonEmptyString] = Field(default_factory=list)
    join_integrity_checked: bool = True
    violations: List[NonEmptyString] = Field(default_factory=list)


# ==============================================================================
# BRIQUE 5 : Contrats d'Approbation & Query Catalog
# ==============================================================================


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"


class QueryCatalogEntry(ContractModel):
    id: NonEmptyString
    contract_version: NonEmptyString = "1.0"
    natural_language_query: NonEmptyString
    canonical_intent: TextToSQLIntent
    parameterized_sql: NonEmptyString
    parameters_schema: Dict[NonEmptyString, CandidateParameter] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_by: NonEmptyString
    approved_by: Optional[NonEmptyString] = None
    approved_at: Optional[datetime] = None
    schema_version: NonEmptyString = "1.0.0"
    execution_count: int = 0
    avg_execution_time_ms: Optional[float] = None
    last_executed_at: Optional[datetime] = None
