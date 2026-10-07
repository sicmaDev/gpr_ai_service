from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, StrictInt, constr, root_validator, validator

NonEmptyString = constr(strict=True, strip_whitespace=True, min_length=1)


class ContractModel(BaseModel):
    class Config:
        extra = "forbid"


class IntentEntity(ContractModel):
    concept_id: Literal["case"]
    types: List[Literal["CLAIM", "DENUNCIACION", "SUGGESTION"]]
    include_all_types: bool

    @root_validator(skip_on_failure=True)
    def validate_types(cls, values):
        if values.get("include_all_types") and values.get("types"):
            raise ValueError("types doit etre vide lorsque include_all_types vaut true")
        if not values.get("include_all_types") and not values.get("types"):
            raise ValueError("types doit contenir au moins un type de dossier")
        return values


class IntentMeasure(ContractModel):
    concept_id: Literal["case_count"]
    operation: Literal["count"]
    target_concept: Literal["case"]
    label: NonEmptyString


class IntentDimension(ContractModel):
    concept_id: Literal["claim_type", "status", "agency", "channel", "category"]
    label: NonEmptyString


class IntentFilter(ContractModel):
    concept_id: Literal["claim_type", "status", "agency", "channel", "category"]
    operator: Literal["equals", "in"]
    value: Optional[Any]
    values: Optional[List[Any]]

    @root_validator(skip_on_failure=True)
    def validate_filter_values(cls, values):
        if values.get("operator") == "in":
            if values.get("value") is not None or not values.get("values"):
                raise ValueError("in exige values et value a null")
        elif values.get("value") is None or values.get("values") is not None:
            raise ValueError("equals exige value et values a null")
        return values


class IntentTime(ContractModel):
    field_concept: Literal["receipt_date"]
    start_date: date
    end_date: date
    timezone: Literal["Africa/Porto-Novo"]

    @root_validator(skip_on_failure=True)
    def validate_range(cls, values):
        if values.get("start_date") and values.get("end_date"):
            if values["start_date"] > values["end_date"]:
                raise ValueError("start_date doit etre anterieure ou egale a end_date")
        return values


class IntentClarification(ContractModel):
    code: NonEmptyString
    message: NonEmptyString
    question: NonEmptyString


class TextToSQLIntent(ContractModel):
    contract_version: Literal["1.0"]
    status: Literal["ready", "needs_clarification", "unsupported"]
    entity: Optional[IntentEntity]
    measure: Optional[IntentMeasure]
    dimensions: List[IntentDimension]
    filters: List[IntentFilter]
    time: Optional[IntentTime]
    clarification: Optional[IntentClarification]
    unsupported_reason: Optional[NonEmptyString]

    @root_validator(skip_on_failure=True)
    def validate_status_contract(cls, values):
        status = values.get("status")
        if status == "ready":
            if values.get("entity") is None or values.get("measure") is None:
                raise ValueError("ready exige entity et measure")
            if values.get("clarification") is not None:
                raise ValueError("ready ne doit pas contenir de clarification")
            if values.get("unsupported_reason") is not None:
                raise ValueError("ready ne doit pas contenir unsupported_reason")
        else:
            if values.get("entity") is not None or values.get("measure") is not None:
                raise ValueError(f"{status} exige entity et measure a null")
            if values.get("dimensions") or values.get("filters") or values.get("time"):
                raise ValueError(f"{status} ne doit pas contenir de champs executables")
            if status == "needs_clarification":
                if values.get("clarification") is None:
                    raise ValueError("needs_clarification exige clarification")
                if values.get("unsupported_reason") is not None:
                    raise ValueError("needs_clarification ne doit pas contenir unsupported_reason")
            if status == "unsupported":
                if values.get("unsupported_reason") is None:
                    raise ValueError("unsupported exige unsupported_reason")
                if values.get("clarification") is not None:
                    raise ValueError("unsupported ne doit pas contenir clarification")
        return values


class CandidateParameter(ContractModel):
    type: Literal["date", "datetime", "string", "integer", "decimal", "boolean"]
    source: NonEmptyString


class CandidateResultColumn(ContractModel):
    name: NonEmptyString
    concept_id: NonEmptyString
    role: Literal["dimension", "measure"]
    data_type: Literal["string", "integer", "decimal", "boolean", "date", "datetime"]


class TextToSQLCandidate(ContractModel):
    contract_version: Literal["1.0"]
    sql: NonEmptyString
    parameters: Dict[NonEmptyString, CandidateParameter]
    used_schema: List[NonEmptyString]
    result_columns: List[CandidateResultColumn]
    assumptions: List[NonEmptyString]

    @validator("result_columns")
    def validate_result_columns(cls, value):
        if not value:
            raise ValueError("result_columns doit contenir au moins une colonne")
        names = [column.name for column in value]
        if len(names) != len(set(names)):
            raise ValueError("les noms de result_columns doivent etre uniques")
        return value
