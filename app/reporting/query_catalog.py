"""
Catalogue officiel des requêtes SQL homologuées (Query Catalog) pour le moteur Text-to-SQL Gouverné.

Ce module matérialise le circuit rapide (Fast-Path Court-Circuit) :
- Les requêtes certifiées de référence (status=ApprovalStatus.APPROVED).
- L'algorithme d'appariement d'intention canonique (matching structurel).
- L'extraction et la liaison dynamique des paramètres liés (:start_date, :end_date).
- L'évitement complet d'appels LLM pour les questions répétitives ou standardisées.
"""

import copy
from datetime import date, datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    CandidateParameter,
    IntentDimension,
    IntentEntity,
    IntentMeasure,
    IntentTime,
    QueryCatalogEntry,
    TextToSQLIntent,
)

# -----------------------------------------------------------------------------
# MOTEUR 3 : EMPREINTE D'IDEMPOTENCE ET VERROU TEMPOREL (CANONICAL MATCHING)
# -----------------------------------------------------------------------------

def compute_canonical_intent_hash(intent: TextToSQLIntent) -> str:
    """
    Moteur 3 : Calcule l'empreinte canonique SHA-256 d'une intention analytique.
    Garantit l'isomorphisme strict des intentions (entité, types, mesure, dimensions, filtres, verrou temporel).
    Deux intentions ne peuvent partager une empreinte que si leurs structures temporelles et filtrantes sont strictement identiques.
    """
    if intent.status != "ready" or not intent.entity or not intent.measure:
        return ""

    entity_str = intent.entity.concept_id
    types_str = ",".join(sorted(intent.entity.types))
    include_all = str(intent.entity.include_all_types)
    measure_str = intent.measure.concept_id
    dims_str = ",".join(sorted(d.concept_id for d in intent.dimensions))

    filters_repr = []
    for f in sorted(intent.filters, key=lambda x: x.concept_id):
        val_str = str(sorted(f.values)) if f.values else str(f.value)
        filters_repr.append(f"{f.concept_id}:{f.operator}:{val_str}")
    filters_str = ";".join(filters_repr)

    has_time = intent.time is not None
    time_field = intent.time.field_concept if intent.time else "none"

    composite_key = f"{entity_str}|{types_str}|{include_all}|{measure_str}|{dims_str}|{filters_str}|time:{has_time}:{time_field}"
    return hashlib.sha256(composite_key.encode("utf-8")).hexdigest()[:16]


# -----------------------------------------------------------------------------
# LES 8 REQUÊTES CERTIFIÉES INITIALES (HOMOLOGUÉES / APPROVED)
# -----------------------------------------------------------------------------

_DEFAULT_START = date(2026, 1, 1)
_DEFAULT_END = date(2026, 12, 31)

_CERTIFIED_QUERIES: Dict[str, QueryCatalogEntry] = {
    # 1. Volume de réclamations par agence
    "QC-CLAIM-COUNT-BY-AGENCY": QueryCatalogEntry(
        id="QC-CLAIM-COUNT-BY-AGENCY",
        contract_version="1.0",
        natural_language_query="Nombre de réclamations par agence sur une période",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[IntentDimension(concept_id="agency", label="Agence")],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle ORDER BY case_count DESC"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 2. Volume de réclamations par canal de collecte
    "QC-CLAIM-COUNT-BY-CHANNEL": QueryCatalogEntry(
        id="QC-CLAIM-COUNT-BY-CHANNEL",
        contract_version="1.0",
        natural_language_query="Nombre de réclamations par canal de collecte",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            ),
            dimensions=[IntentDimension(concept_id="channel", label="Canal")],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY cc.libelle ORDER BY case_count DESC"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 3. Total unifié des plaintes (réclamations, dénonciations, suggestions)
    "QC-UNIFIED-PLAINTES-TOTAL": QueryCatalogEntry(
        id="QC-UNIFIED-PLAINTES-TOTAL",
        contract_version="1.0",
        natural_language_query="Volume total unifié des plaintes (réclamations, dénonciations, suggestions)",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(
                concept_id="plainte",
                types=["CLAIM", "DENUNCIATION", "SUGGESTION"],
                include_all_types=True,
            ),
            measure=IntentMeasure(
                concept_id="plainte_count",
                operation="count",
                target_concept="plainte",
                label="Total unifié des plaintes",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= :start_date AND receipt_at < :end_date) + "
            "(SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= :start_date AND recorded_at < :end_date)) "
            "AS plainte_count"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 4. Taux de respect des délais SLA
    "QC-SLA-ADHERENCE-RATE": QueryCatalogEntry(
        id="QC-SLA-ADHERENCE-RATE",
        contract_version="1.0",
        natural_language_query="Taux global de respect des délais SLA",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="sla_adherence_rate",
                operation="rate",
                target_concept="plainte",
                label="Taux de respect SLA",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT AVG(CASE WHEN c.resolved_at <= c.sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate "
            "FROM reporting_claim c "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "AND c.resolved_at IS NOT NULL"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 5. Taux de satisfaction globale des clients
    "QC-SATISFACTION-RATE": QueryCatalogEntry(
        id="QC-SATISFACTION-RATE",
        contract_version="1.0",
        natural_language_query="Taux de satisfaction global des usagers",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="satisfaction_rate",
                operation="rate",
                target_concept="plainte",
                label="Taux de satisfaction",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate "
            "FROM reporting_claim c "
            "WHERE c.claim_type = 'CLAIM' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "AND c.satisfaction_status IS NOT NULL"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 6. Répartition des dossiers graves par agence
    "QC-SEVERE-PLAINTES-BY-AGENCY": QueryCatalogEntry(
        id="QC-SEVERE-PLAINTES-BY-AGENCY",
        contract_version="1.0",
        natural_language_query="Nombre de réclamations graves par agence",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["CLAIM"]),
            measure=IntentMeasure(
                concept_id="severe_plainte_count",
                operation="count",
                target_concept="plainte",
                label="Plaintes graves",
            ),
            dimensions=[IntentDimension(concept_id="agency", label="Agence")],
            time=IntentTime(
                field_concept="receipt_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT sp.libelle AS agency, COUNT(c.id) AS severe_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'GRAVE' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle ORDER BY severe_count DESC"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 7. Suggestions par niveau d'impact
    "QC-SUGGESTIONS-BY-IMPACT": QueryCatalogEntry(
        id="QC-SUGGESTIONS-BY-IMPACT",
        contract_version="1.0",
        natural_language_query="Nombre de suggestions par niveau d'impact",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(concept_id="plainte", types=["SUGGESTION"]),
            measure=IntentMeasure(
                concept_id="suggestion_count",
                operation="count",
                target_concept="suggestion",
                label="Nombre de suggestions",
            ),
            dimensions=[IntentDimension(concept_id="impact_level", label="Niveau d'impact")],
            time=IntentTime(
                field_concept="recorded_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT s.impact_level, COUNT(s.id) AS suggestion_count "
            "FROM reporting_suggestion s "
            "WHERE s.recorded_at >= :start_date AND s.recorded_at < :end_date "
            "GROUP BY s.impact_level ORDER BY suggestion_count DESC"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),

    # 8. Nombre de réaffectations de dossiers
    "QC-REAFFECTATION-COUNT": QueryCatalogEntry(
        id="QC-REAFFECTATION-COUNT",
        contract_version="1.0",
        natural_language_query="Nombre de réaffectations de dossiers",
        canonical_intent=TextToSQLIntent(
            status="ready",
            entity=IntentEntity(
                concept_id="treatment",
                types=["CLAIM", "DENUNCIATION", "SUGGESTION"],
                include_all_types=True,
            ),
            measure=IntentMeasure(
                concept_id="reaffectation_count",
                operation="count",
                target_concept="treatment",
                label="Nombre de réaffectations",
            ),
            dimensions=[],
            time=IntentTime(
                field_concept="created_date",
                start_date=_DEFAULT_START,
                end_date=_DEFAULT_END,
                timezone="Africa/Porto-Novo",
            ),
        ),
        parameterized_sql=(
            "SELECT COUNT(h.id) AS reaffectation_count "
            "FROM reporting_historique_affectations h "
            "WHERE h.affectation_precedente_id IS NOT NULL "
            "AND h.date_affectation >= :start_date AND h.date_affectation < :end_date"
        ),
        parameters_schema={
            "start_date": CandidateParameter(type="datetime", source="intent.time.start_date"),
            "end_date": CandidateParameter(type="datetime", source="intent.time.end_date"),
        },
        status=ApprovalStatus.APPROVED,
        created_by="admin",
        approved_by="system",
        approved_at=datetime(2026, 1, 1, 0, 0, 0),
        schema_version="1.0.0",
    ),
}

# Calcul et assignation systématique de l'intent_hash canonique pour chaque requête certifiée
for _entry in _CERTIFIED_QUERIES.values():
    if not _entry.intent_hash and _entry.canonical_intent:
        _entry.intent_hash = compute_canonical_intent_hash(_entry.canonical_intent)

# Copie de sauvegarde pour la restauration lors des tests et réinitialisations
_INITIAL_CERTIFIED_QUERIES: Dict[str, QueryCatalogEntry] = copy.deepcopy(_CERTIFIED_QUERIES)


# -----------------------------------------------------------------------------
# FONCTIONS D'ACCÈS, DE GESTION ET D'APPARIEMENT (MATCHING FAST-PATH)
# -----------------------------------------------------------------------------

def get_certified_queries() -> Dict[str, QueryCatalogEntry]:
    """Retourne l'ensemble des requêtes certifiées actives."""
    return _CERTIFIED_QUERIES


def get_query_by_id(query_id: str) -> Optional[QueryCatalogEntry]:
    """Récupère une entrée du catalogue par son identifiant unique."""
    return _CERTIFIED_QUERIES.get(query_id)


def register_query_entry(entry: QueryCatalogEntry, db: Optional[Any] = None) -> None:
    """
    Enregistre ou met à jour une entrée dans le registre du catalogue de requêtes.
    Si une session de base de données est fournie, persiste immédiatement dans reporting_certified_queries.
    """
    if not entry.intent_hash and entry.canonical_intent:
        entry.intent_hash = compute_canonical_intent_hash(entry.canonical_intent)
    _CERTIFIED_QUERIES[entry.id] = entry

    if db is not None:
        try:
            from app.db.models import ReportingCertifiedQuery

            row = db.query(ReportingCertifiedQuery).filter_by(id=entry.id).first()
            if row:
                row.contract_version = entry.contract_version
                row.natural_language_query = entry.natural_language_query
                row.canonical_intent = entry.canonical_intent.model_dump(mode="json")
                row.intent_hash = entry.intent_hash
                row.parameterized_sql = entry.parameterized_sql
                row.parameters_schema = (
                    {k: v.model_dump(mode="json") for k, v in entry.parameters_schema.items()}
                    if entry.parameters_schema
                    else None
                )
                row.status = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
                row.created_by = entry.created_by
                row.approved_by = entry.approved_by
                row.approved_at = entry.approved_at
                row.approval_comment = entry.approval_comment
                row.rejection_reason = entry.rejection_reason
                row.deprecation_reason = entry.deprecation_reason
                row.schema_version = entry.schema_version
                row.execution_count = entry.execution_count
                row.avg_execution_time_ms = entry.avg_execution_time_ms
                row.last_executed_at = entry.last_executed_at
                row.updated_at = datetime.now(timezone.utc)
            else:
                db.add(entry_to_db_model(entry))
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass


def remove_query_entry(query_id: str, db: Optional[Any] = None) -> bool:
    """Supprime une entrée du catalogue par son identifiant unique."""
    deleted = False
    if query_id in _CERTIFIED_QUERIES:
        del _CERTIFIED_QUERIES[query_id]
        deleted = True

    if db is not None:
        try:
            from app.db.models import ReportingCertifiedQuery

            row = db.query(ReportingCertifiedQuery).filter_by(id=query_id).first()
            if row:
                db.delete(row)
                db.commit()
                deleted = True
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
    return deleted


def reset_certified_queries(db: Optional[Any] = None) -> None:
    """Restaure le catalogue à son état initial homologué (8 requêtes de référence)."""
    _CERTIFIED_QUERIES.clear()
    _CERTIFIED_QUERIES.update(copy.deepcopy(_INITIAL_CERTIFIED_QUERIES))

    if db is not None:
        try:
            from app.db.models import ReportingCertifiedQuery

            db.query(ReportingCertifiedQuery).delete()
            for entry in _INITIAL_CERTIFIED_QUERIES.values():
                db.add(entry_to_db_model(entry))
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass


def entry_to_db_model(entry: QueryCatalogEntry) -> Any:
    """Convertit un QueryCatalogEntry en modèle SQLAlchemy ReportingCertifiedQuery."""
    from app.db.models import ReportingCertifiedQuery

    return ReportingCertifiedQuery(
        id=entry.id,
        contract_version=entry.contract_version,
        natural_language_query=entry.natural_language_query,
        canonical_intent=entry.canonical_intent.model_dump(mode="json"),
        intent_hash=entry.intent_hash or (compute_canonical_intent_hash(entry.canonical_intent) if entry.canonical_intent else None),
        parameterized_sql=entry.parameterized_sql,
        parameters_schema=(
            {k: v.model_dump(mode="json") for k, v in entry.parameters_schema.items()}
            if entry.parameters_schema
            else None
        ),
        status=entry.status.value if hasattr(entry.status, "value") else str(entry.status),
        created_by=entry.created_by,
        approved_by=entry.approved_by,
        approved_at=entry.approved_at,
        approval_comment=entry.approval_comment,
        rejection_reason=entry.rejection_reason,
        deprecation_reason=entry.deprecation_reason,
        schema_version=entry.schema_version,
        execution_count=entry.execution_count,
        avg_execution_time_ms=entry.avg_execution_time_ms,
        last_executed_at=entry.last_executed_at,
    )


def db_model_to_entry(row: Any) -> QueryCatalogEntry:
    """Convertit une ligne ReportingCertifiedQuery en contrat Pydantic QueryCatalogEntry."""
    canonical_intent = TextToSQLIntent(**row.canonical_intent)
    return QueryCatalogEntry(
        id=row.id,
        contract_version=row.contract_version,
        natural_language_query=row.natural_language_query,
        canonical_intent=canonical_intent,
        intent_hash=getattr(row, "intent_hash", None) or compute_canonical_intent_hash(canonical_intent),
        parameterized_sql=row.parameterized_sql,
        parameters_schema=(
            {k: CandidateParameter(**v) for k, v in row.parameters_schema.items()}
            if row.parameters_schema
            else {}
        ),
        status=ApprovalStatus(row.status),
        created_by=row.created_by,
        approved_by=row.approved_by,
        approved_at=row.approved_at,
        approval_comment=row.approval_comment,
        rejection_reason=row.rejection_reason,
        deprecation_reason=row.deprecation_reason,
        schema_version=row.schema_version,
        execution_count=row.execution_count,
        avg_execution_time_ms=row.avg_execution_time_ms,
        last_executed_at=row.last_executed_at,
    )


def sync_queries_with_db(db: Any) -> None:
    """
    Synchronise le catalogue en mémoire (_CERTIFIED_QUERIES) avec la table reporting_certified_queries.
    - Si la table est vide, insère automatiquement les 8 requêtes de référence homologuées.
    - Synchronise également les métriques métier via sync_metrics_with_db(db).
    - Charge toutes les entrées présentes en base dans la mémoire vive.
    """
    try:
        from app.db.models import ReportingCertifiedQuery
        from app.reporting.business_catalog import sync_metrics_with_db

        # 1. Synchronisation préalable des métriques métier
        sync_metrics_with_db(db)

        # 2. Vérification et initialisation automatique si la table est vide
        existing_rows = db.query(ReportingCertifiedQuery).all()
        if not existing_rows:
            for entry in _INITIAL_CERTIFIED_QUERIES.values():
                db_row = entry_to_db_model(entry)
                db.add(db_row)
            db.commit()
            existing_rows = db.query(ReportingCertifiedQuery).all()
        else:
            # Backfill intent_hash si absent
            updated_any = False
            for row in existing_rows:
                if not getattr(row, "intent_hash", None) and row.canonical_intent:
                    try:
                        c_intent = TextToSQLIntent(**row.canonical_intent)
                        row.intent_hash = compute_canonical_intent_hash(c_intent)
                        updated_any = True
                    except Exception:
                        pass
            if updated_any:
                db.commit()

        # 3. Synchronisation de la mémoire cache
        for row in existing_rows:
            entry = db_model_to_entry(row)
            _CERTIFIED_QUERIES[entry.id] = entry
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


# -----------------------------------------------------------------------------
# MOTEUR 3 : APPARIEMENT FAST-PATH & CANDIDATE-PATH (INDEXÉ O(1))
# -----------------------------------------------------------------------------

def _bind_catalog_parameters(
    entry: QueryCatalogEntry,
    intent: TextToSQLIntent,
) -> Tuple[QueryCatalogEntry, Dict[str, Any]]:
    """
    Lie dynamiquement les paramètres temporels, d'entités et de filtres à l'entrée de catalogue.
    Réconcilie de façon réflexive les placeholders SQL (:param) avec l'intention canonique.
    """
    import re

    bound_params: Dict[str, Any] = {}
    if intent.time is not None:
        if intent.time.start_date:
            bound_params["start_date"] = f"{intent.time.start_date.isoformat()} 00:00:00"
        if intent.time.end_date:
            bound_params["end_date"] = f"{intent.time.end_date.isoformat()} 00:00:00"

    # Liaison universelle des types d'entité
    if intent.entity and intent.entity.types:
        scalar_type = intent.entity.types[0]
        bound_params["claim_type"] = scalar_type
        bound_params["claim_type_param"] = scalar_type
        bound_params["type"] = scalar_type
        bound_params["entity_type"] = scalar_type
        bound_params["type_plainte"] = scalar_type

    # Synonymes fréquents de filtres
    filter_synonyms_map = {
        "status": ["status", "status_param", "satisfaction_status", "satisfaction_status_param", "satisfaction", "avis"],
        "satisfaction_status": ["status", "status_param", "satisfaction_status", "satisfaction_status_param", "satisfaction", "avis"],
        "satisfaction": ["status", "status_param", "satisfaction_status", "satisfaction_status_param", "satisfaction", "avis"],
        "avis": ["status", "status_param", "satisfaction_status", "satisfaction_status_param", "satisfaction", "avis"],
        "risk_level": ["risk_level", "risk_level_param", "urgency", "urgency_param", "ai_urgency", "ai_urgency_param", "gravite"],
        "ai_urgency": ["risk_level", "risk_level_param", "urgency", "urgency_param", "ai_urgency", "ai_urgency_param", "gravite"],
        "urgency": ["risk_level", "risk_level_param", "urgency", "urgency_param", "ai_urgency", "ai_urgency_param", "gravite"],
        "channel": ["channel", "channel_param", "canal", "canal_param", "collection_channel"],
        "agency": ["agency", "agency_param", "agence", "agence_param", "service_point"],
        "product": ["product", "product_param", "produit", "produit_param"],
        "category": ["category", "category_param", "categorie", "categorie_param"],
        "object": ["object", "object_param", "objet", "objet_param", "motif"],
    }

    for flt in intent.filters:
        val = flt.value if flt.value is not None else flt.values
        cid = flt.concept_id
        bound_params[cid] = val
        bound_params[f"{cid}_param"] = val
        for syn in filter_synonyms_map.get(cid, []):
            bound_params[syn] = val

    # Réconciliation réflexive avec les placeholders SQL réels de l'entrée de catalogue
    if entry.parameterized_sql:
        sql_placeholders = set(re.findall(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)", entry.parameterized_sql))
        for ph in sql_placeholders:
            if ph not in bound_params:
                for flt in intent.filters:
                    cid = flt.concept_id
                    syns = filter_synonyms_map.get(cid, [cid])
                    is_match = ph in syns or any(ph.startswith(syn) or ph.endswith(f"_{syn}") for syn in syns)
                    if is_match:
                        val = flt.value if flt.value is not None else flt.values
                        if isinstance(val, (list, tuple)):
                            num_m = re.search(r"(\d+)$", ph)
                            if num_m:
                                idx = int(num_m.group(1)) - 1
                                if 0 <= idx < len(val):
                                    bound_params[ph] = val[idx]
                                else:
                                    bound_params[ph] = val[0]
                            else:
                                bound_params[ph] = val
                        else:
                            bound_params[ph] = val
                        break

        # Élagage des paramètres orphelins non présents dans le SQL paramétré
        bound_params = {k: v for k, v in bound_params.items() if k in sql_placeholders}

    return entry, bound_params


def match_intent_in_catalog(
    intent: TextToSQLIntent,
    include_pending: bool = False,
    db_session: Optional[Any] = None,
) -> Optional[Tuple[QueryCatalogEntry, Dict[str, Any]]]:
    """
    Vérifie si une intention canonique correspond exactement à une requête certifiée homologuée.
    Si db_session est fournie, effectue une recherche directe indexée O(1) sur intent_hash en base MySQL/SQLite.
    Sinon, effectue la recherche en mémoire cache (_CERTIFIED_QUERIES).

    Retourne :
        (QueryCatalogEntry, bound_parameters) si une correspondance est trouvée.
        None si la requête est inédite (nécessite le circuit génératif contrôlé du Step 5 & 6).
    """
    if intent.status != "ready" or intent.entity is None or intent.measure is None:
        return None

    incoming_target_hash = compute_canonical_intent_hash(intent)

    # Priorité 1 : Recherche directe en base de données O(1) par intent_hash si db_session est active
    if db_session is not None and incoming_target_hash:
        try:
            from app.db.models import ReportingCertifiedQuery

            query = db_session.query(ReportingCertifiedQuery).filter(
                ReportingCertifiedQuery.intent_hash == incoming_target_hash
            )
            if not include_pending:
                query = query.filter(ReportingCertifiedQuery.status == ApprovalStatus.APPROVED.value)
            else:
                query = query.filter(
                    ReportingCertifiedQuery.status.in_([
                        ApprovalStatus.APPROVED.value,
                        ApprovalStatus.PENDING.value,
                    ])
                )

            rows = query.all()
            if rows:
                # Priorité : APPROVED en premier, puis le plus grand nombre d'exécutions
                sorted_rows = sorted(
                    rows,
                    key=lambda r: (
                        0 if r.status == ApprovalStatus.APPROVED.value else 1,
                        -(r.execution_count or 0),
                    ),
                )
                best_entry = db_model_to_entry(sorted_rows[0])
                return _bind_catalog_parameters(best_entry, intent)
        except Exception:
            # Repli sécurisé en mémoire
            pass

    # Priorité 2 : Recherche en mémoire (_CERTIFIED_QUERIES)
    incoming_entity = intent.entity
    incoming_measure = intent.measure
    incoming_dims = {d.concept_id for d in intent.dimensions}
    incoming_filters = {f.concept_id for f in intent.filters}

    def _matches_entry(entry: QueryCatalogEntry) -> bool:
        if incoming_target_hash and entry.intent_hash:
            return entry.intent_hash == incoming_target_hash

        c_intent = entry.canonical_intent
        if c_intent.entity is None or c_intent.measure is None:
            return False

        # 1. Vérification du concept d'entité et des types de dossiers
        if c_intent.entity.concept_id != incoming_entity.concept_id:
            return False
        if c_intent.entity.include_all_types != incoming_entity.include_all_types:
            return False
        if set(c_intent.entity.types) != set(incoming_entity.types):
            return False

        # 2. Vérification de la métrique demandée
        if c_intent.measure.concept_id != incoming_measure.concept_id:
            return False

        # 3. Vérification des dimensions de regroupement
        catalog_dims = {d.concept_id for d in c_intent.dimensions}
        if catalog_dims != incoming_dims:
            return False

        # 4. Vérification des filtres appliqués
        catalog_filters = {f.concept_id for f in c_intent.filters}
        if catalog_filters != incoming_filters:
            return False

        # 5. Cohérence temporelle stricte et bidirectionnelle (Moteur 3 : Verrou Temporel) :
        # - Si la requête exige start_date/end_date mais que l'intention n'a pas de temps -> REJET.
        # - Si l'intention a un filtre temporel mais que la requête N'A PAS de clause de date -> REJET.
        has_query_time = (
            ":start_date" in entry.parameterized_sql
            or "start_date" in entry.parameters_schema
            or (entry.canonical_intent and entry.canonical_intent.time is not None)
        )
        has_intent_time = (intent.time is not None)
        if has_query_time != has_intent_time:
            return False

        return True

    # Priorité 1 : Recherche parmi les requêtes homologuées APPROVED (Fast-Path)
    matched_entry: Optional[QueryCatalogEntry] = None
    for entry in _CERTIFIED_QUERIES.values():
        if entry.status == ApprovalStatus.APPROVED and _matches_entry(entry):
            matched_entry = entry
            break

    # Priorité 2 : Recherche parmi les requêtes en attente PENDING (Candidate-Path déterministe)
    if matched_entry is None and include_pending:
        for entry in _CERTIFIED_QUERIES.values():
            if entry.status == ApprovalStatus.PENDING and _matches_entry(entry):
                matched_entry = entry
                break

    if matched_entry is None:
        return None

    return _bind_catalog_parameters(matched_entry, intent)
