"""
Catalogue officiel des requêtes SQL homologuées (Query Catalog) pour le moteur Text-to-SQL Gouverné.

Ce module matérialise le circuit rapide (Fast-Path Court-Circuit) :
- Les requêtes certifiées de référence (status=ApprovalStatus.APPROVED).
- L'algorithme d'appariement d'intention canonique (matching structurel).
- L'extraction et la liaison dynamique des paramètres liés (:start_date, :end_date).
- L'évitement complet d'appels LLM pour les questions répétitives ou standardisées.
"""

from datetime import date, datetime
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
            "WHERE c.claim_type = 'CLAIM' AND c.ai_urgency = 'GRAVE' "
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


# -----------------------------------------------------------------------------
# FONCTIONS D'ACCÈS ET D'APPARIEMENT (MATCHING FAST-PATH)
# -----------------------------------------------------------------------------

def get_certified_queries() -> Dict[str, QueryCatalogEntry]:
    """Retourne l'ensemble des requêtes certifiées actives."""
    return _CERTIFIED_QUERIES


def get_query_by_id(query_id: str) -> Optional[QueryCatalogEntry]:
    """Récupère une entrée du catalogue par son identifiant unique."""
    return _CERTIFIED_QUERIES.get(query_id)


def match_intent_in_catalog(
    intent: TextToSQLIntent,
) -> Optional[Tuple[QueryCatalogEntry, Dict[str, Any]]]:
    """
    Vérifie si une intention canonique correspond exactement à une requête certifiée homologuée.

    Retourne :
        (QueryCatalogEntry, bound_parameters) si une correspondance est trouvée.
        None si la requête est inédite (nécessite le circuit génératif contrôlé du Step 5 & 6).
    """
    if intent.status != "ready" or intent.entity is None or intent.measure is None:
        return None

    incoming_entity = intent.entity
    incoming_measure = intent.measure
    incoming_dims = {d.concept_id for d in intent.dimensions}
    incoming_filters = {f.concept_id for f in intent.filters}

    for entry in _CERTIFIED_QUERIES.values():
        if entry.status != ApprovalStatus.APPROVED:
            continue

        c_intent = entry.canonical_intent
        if c_intent.entity is None or c_intent.measure is None:
            continue

        # 1. Vérification du concept d'entité et des types de dossiers
        if c_intent.entity.concept_id != incoming_entity.concept_id:
            continue
        if c_intent.entity.include_all_types != incoming_entity.include_all_types:
            continue
        if set(c_intent.entity.types) != set(incoming_entity.types):
            continue

        # 2. Vérification de la métrique demandée
        if c_intent.measure.concept_id != incoming_measure.concept_id:
            continue

        # 3. Vérification des dimensions de regroupement
        catalog_dims = {d.concept_id for d in c_intent.dimensions}
        if catalog_dims != incoming_dims:
            continue

        # 4. Vérification des filtres appliqués
        catalog_filters = {f.concept_id for f in c_intent.filters}
        if catalog_filters != incoming_filters:
            continue

        # HIT ! Correspondance structurelle certifiée trouvée.
        # Liaison dynamique des paramètres
        bound_params: Dict[str, Any] = {}
        if intent.time is not None:
            # Formatage semi-ouvert MySQL / SQLite : [start_date, end_date[
            bound_params["start_date"] = f"{intent.time.start_date.isoformat()} 00:00:00"
            bound_params["end_date"] = f"{intent.time.end_date.isoformat()} 00:00:00"

        for flt in intent.filters:
            param_key = f"{flt.concept_id}_param"
            if flt.value is not None:
                bound_params[param_key] = flt.value
            elif flt.values is not None:
                bound_params[param_key] = flt.values

        return entry, bound_params

    return None
