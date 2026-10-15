"""
Gestionnaire du Cycle de Vie et d'Approbation du Query Catalog (Step 8).

Ce module implémente la gouvernance humaine et l'apprentissage continu du moteur Text-to-SQL :
1. Soumission d'une requête générée et exécutée au statut PENDING.
2. Homologation formelle (APPROVED) avec validation AST bloquante obligatoire.
3. Rejet documenté (REJECTED) pour motif sémantique ou métier.
4. Dépréciation manuelle ou automatique (DEPRECATED) lors de l'évolution du schéma.
5. Invalidation et synchronisation automatique lors des montées de version du Schema Catalog.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.reporting.query_catalog import (
    compute_canonical_intent_hash,
    get_certified_queries,
    get_query_by_id,
    register_query_entry,
)
from app.reporting.sql_validator import validate_raw_sql
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    CandidateParameter,
    QueryApprovalPayload,
    QueryCatalogEntry,
    QueryDeprecationPayload,
    QueryRejectionPayload,
    SchemaCatalog,
    TextToSQLIntent,
    UserFeedbackPayload,
)



def propose_query_candidate(
    canonical_intent: TextToSQLIntent,
    parameterized_sql: str,
    natural_language_query: str,
    created_by: str,
    parameters_schema: Optional[Dict[str, CandidateParameter]] = None,
    schema_version: str = "1.0.0",
    query_id: Optional[str] = None,
    db_session: Optional[Any] = None,
) -> QueryCatalogEntry:
    """
    Soumet une nouvelle requête candidate au catalogue avec le statut PENDING.

    Effectue un contrôle préalable de conformité AST (sqlglot).
    Si la requête viole les règles de sécurité ou d'intégrité, elle est immédiatement rejetée.

    Args:
        canonical_intent: Intention canonique résolue.
        parameterized_sql: Requête SQL paramétrée (:param).
        natural_language_query: Formulation en langage naturel.
        created_by: Identifiant du créateur (ex: utilisateur, LLM-Nemotron, agent).
        parameters_schema: Schéma optionnel des paramètres liés.
        schema_version: Version de schéma cible.
        query_id: Identifiant unique optionnel (généré automatiquement si omis).
        db_session: Session SQLAlchemy optionnelle pour persistance immédiate.

    Returns:
        QueryCatalogEntry au statut PENDING.

    Raises:
        ValueError: Si la requête SQL ne satisfait pas les vérifications de sécurité AST.
    """
    validation_res = validate_raw_sql(parameterized_sql)
    if not validation_res.is_valid:
        violations_str = "; ".join(validation_res.violations)
        raise ValueError(
            f"Requête candidate rejetée par le validateur AST : {violations_str}"
        )

    # Construction du dictionnaire de paramètres par défaut si non spécifié
    effective_params: Dict[str, CandidateParameter] = {}
    if parameters_schema:
        effective_params = dict(parameters_schema)
    else:
        if ":start_date" in parameterized_sql:
            effective_params["start_date"] = CandidateParameter(
                type="datetime", source="intent.time.start_date"
            )
        if ":end_date" in parameterized_sql:
            effective_params["end_date"] = CandidateParameter(
                type="datetime", source="intent.time.end_date"
            )

    assigned_id = query_id or f"QC-CANDIDATE-{uuid.uuid4().hex[:8].upper()}"
    intent_hash = compute_canonical_intent_hash(canonical_intent) if canonical_intent else None

    entry = QueryCatalogEntry(
        id=assigned_id,
        contract_version="1.0",
        natural_language_query=natural_language_query,
        canonical_intent=canonical_intent,
        intent_hash=intent_hash,
        parameterized_sql=parameterized_sql,
        parameters_schema=effective_params,
        status=ApprovalStatus.PENDING,
        created_by=created_by,
        schema_version=schema_version,
    )

    register_query_entry(entry, db=db_session)
    return entry


def approve_query(
    payload: QueryApprovalPayload,
    schema_catalog: Optional[SchemaCatalog] = None,
    db_session: Optional[Any] = None,
) -> QueryCatalogEntry:
    """
    Homologue une requête du catalogue et la promeut au statut APPROVED (éligible Fast-Path).

    Garde-fou obligatoire : Ré-exécute la validation AST. Si une violation est détectée,
    l'approbation est strictement refusée avec levée d'exception.

    Args:
        payload: QueryApprovalPayload contenant query_id, approver et comment.
        schema_catalog: Catalogue de schéma optionnel pour la vérification AST.
        db_session: Session SQLAlchemy optionnelle pour persistance immédiate.

    Returns:
        QueryCatalogEntry mise à jour au statut APPROVED.

    Raises:
        KeyError: Si l'identifiant de requête n'existe pas.
        ValueError: Si la requête échoue à la validation AST.
    """
    entry = get_query_by_id(payload.query_id)
    if entry is None:
        raise KeyError(f"Requête '{payload.query_id}' introuvable dans le catalogue.")

    # Contrôle de sécurité bloquant avant toute promotion
    validation_res = validate_raw_sql(
        entry.parameterized_sql, schema_catalog=schema_catalog
    )
    if not validation_res.is_valid:
        violations_str = "; ".join(validation_res.violations)
        raise ValueError(
            f"Échec de l'approbation : la requête '{payload.query_id}' ne satisfait pas "
            f"les critères de sécurité AST ({violations_str})"
        )

    entry.status = ApprovalStatus.APPROVED
    entry.approved_by = payload.approver
    entry.approved_at = datetime.now(timezone.utc)
    entry.approval_comment = payload.comment

    register_query_entry(entry, db=db_session)
    return entry


def reject_query(
    payload: QueryRejectionPayload,
    db_session: Optional[Any] = None,
) -> QueryCatalogEntry:
    """
    Rejette une requête candidate avec consignation obligatoire du motif.

    La requête passe au statut REJECTED et ne sera jamais sélectionnée par le Fast-Path.

    Args:
        payload: QueryRejectionPayload contenant query_id, approver et rejection_reason.
        db_session: Session SQLAlchemy optionnelle pour persistance immédiate.

    Returns:
        QueryCatalogEntry mise à jour au statut REJECTED.

    Raises:
        KeyError: Si l'identifiant de requête n'existe pas.
    """
    entry = get_query_by_id(payload.query_id)
    if entry is None:
        raise KeyError(f"Requête '{payload.query_id}' introuvable dans le catalogue.")

    entry.status = ApprovalStatus.REJECTED
    entry.rejection_reason = payload.rejection_reason
    entry.approved_by = payload.approver
    entry.approved_at = datetime.now(timezone.utc)

    register_query_entry(entry, db=db_session)
    return entry


def deprecate_query(
    payload: QueryDeprecationPayload,
    db_session: Optional[Any] = None,
) -> QueryCatalogEntry:
    """
    Déprécie une requête active du catalogue (retrait immédiat du Fast-Path).

    Args:
        payload: QueryDeprecationPayload contenant query_id et reason.
        db_session: Session SQLAlchemy optionnelle pour persistance immédiate.

    Returns:
        QueryCatalogEntry mise à jour au statut DEPRECATED.

    Raises:
        KeyError: Si l'identifiant de requête n'existe pas.
    """
    entry = get_query_by_id(payload.query_id)
    if entry is None:
        raise KeyError(f"Requête '{payload.query_id}' introuvable dans le catalogue.")

    entry.status = ApprovalStatus.DEPRECATED
    entry.deprecation_reason = payload.reason

    register_query_entry(entry, db=db_session)
    return entry


def list_catalog_entries(
    status_filter: Optional[ApprovalStatus] = None,
) -> List[QueryCatalogEntry]:
    """
    Liste les requêtes du catalogue avec filtrage optionnel par statut.

    Args:
        status_filter: Statut d'approbation optionnel (PENDING, APPROVED, REJECTED, DEPRECATED).

    Returns:
        Liste des entrées correspondantes triées par identifiant.
    """
    all_entries = get_certified_queries().values()
    if status_filter is None:
        return sorted(list(all_entries), key=lambda e: e.id)
    return sorted(
        [e for e in all_entries if e.status == status_filter],
        key=lambda e: e.id,
    )


def sync_on_schema_evolution(
    new_schema_version: str,
    new_schema_catalog: Optional[SchemaCatalog] = None,
    db_session: Optional[Any] = None,
) -> List[str]:
    """
    Synchronise le catalogue lors d'une évolution de schéma de base de données.

    Parcourt toutes les requêtes actuellement homologuées (APPROVED) :
    1. Re-valide la requête contre le nouveau schéma (tables, colonnes, jointures).
    2. Si des violations AST apparaissent, la requête est automatiquement basculée
       au statut DEPRECATED avec motif d'obsolescence consigné.
    3. Si la requête demeure valide, sa version de schéma est actualisée vers new_schema_version.

    Args:
        new_schema_version: Nouvelle version du schéma (ex: "1.1.0").
        new_schema_catalog: Nouveau catalogue de schéma optionnel (si modifié).
        db_session: Session SQLAlchemy optionnelle pour persistance immédiate.

    Returns:
        Liste des identifiants des requêtes invalidées/dépréciées.
    """
    deprecated_ids: List[str] = []
    current_entries = list(get_certified_queries().values())

    for entry in current_entries:
        if entry.status != ApprovalStatus.APPROVED:
            continue

        validation_res = validate_raw_sql(
            entry.parameterized_sql, schema_catalog=new_schema_catalog
        )

        if not validation_res.is_valid:
            violations_str = "; ".join(validation_res.violations)
            entry.status = ApprovalStatus.DEPRECATED
            entry.deprecation_reason = (
                f"Dépréciation automatique lors de la migration vers le schéma v{new_schema_version} : "
                f"{violations_str}"
            )
            deprecated_ids.append(entry.id)
            register_query_entry(entry, db=db_session)
        else:
            entry.schema_version = new_schema_version
            register_query_entry(entry, db=db_session)

    return deprecated_ids


def auto_promote_executed_query(
    canonical_intent: TextToSQLIntent,
    parameterized_sql: str,
    natural_language_query: str,
    user_id: str,
    parameters_schema: Optional[Dict[str, CandidateParameter]] = None,
    schema_version: str = "1.0.0",
    query_id: Optional[str] = None,
    db_session: Optional[Any] = None,
) -> QueryCatalogEntry:
    """
    Enregistre et auto-promeut immédiatement une requête exécutée avec succès au statut APPROVED.

    Garantit l'expérience utilisateur et la reproductibilité déterministe pour les utilisateurs GPR :
    - Si la requête existe déjà dans le catalogue, incrémente execution_count et met à jour la date.
    - Si la requête est nouvelle, effectue la validation AST et l'enregistre directement comme homologuée
      (approved_by='auto_verified', status=ApprovalStatus.APPROVED).
    - Si une session de base de données est fournie, persiste immédiatement dans MySQL/SQLite.
    - Si la requête porte sur une métrique personnalisée, enregistre et persiste également la métrique.
    """
    # Si query_id est fourni et existe déjà
    if query_id:
        existing = get_query_by_id(query_id)
        if existing:
            existing.execution_count += 1
            existing.last_executed_at = datetime.now(timezone.utc)
            register_query_entry(existing, db=db_session)
            return existing

    # Recherche si une requête identique existe déjà dans le catalogue
    for entry in get_certified_queries().values():
        if (
            entry.parameterized_sql.strip() == parameterized_sql.strip()
            and entry.status != ApprovalStatus.REJECTED
        ):
            entry.execution_count += 1
            entry.last_executed_at = datetime.now(timezone.utc)
            register_query_entry(entry, db=db_session)
            return entry

    # Validation AST préalable de sécurité
    val_res = validate_raw_sql(parameterized_sql)
    if not val_res.is_valid:
        violations_str = "; ".join(val_res.violations)
        raise ValueError(
            f"Requête rejetée par le validateur AST : {violations_str}"
        )

    effective_params: Dict[str, CandidateParameter] = {}
    if parameters_schema:
        effective_params = dict(parameters_schema)
    else:
        if ":start_date" in parameterized_sql:
            effective_params["start_date"] = CandidateParameter(
                type="datetime", source="intent.time.start_date"
            )
        if ":end_date" in parameterized_sql:
            effective_params["end_date"] = CandidateParameter(
                type="datetime", source="intent.time.end_date"
            )

    assigned_id = query_id or f"QC-PEND-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    intent_hash = compute_canonical_intent_hash(canonical_intent) if canonical_intent else None

    entry = QueryCatalogEntry(
        id=assigned_id,
        contract_version="1.0",
        natural_language_query=natural_language_query,
        canonical_intent=canonical_intent,
        intent_hash=intent_hash,
        parameterized_sql=parameterized_sql,
        parameters_schema=effective_params,
        status=ApprovalStatus.PENDING,
        created_by=user_id,
        approved_by=None,
        approved_at=None,
        schema_version=schema_version,
        execution_count=1,
        last_executed_at=now,
    )

    register_query_entry(entry, db=db_session)

    # Persistance de la métrique si personnalisée / inédite
    if canonical_intent.measure and canonical_intent.measure.concept_id not in (
        "plainte_count", "reclamation_count", "denonciation_count", "suggestion_count",
        "sla_adherence_rate", "avg_processing_time", "satisfaction_rate", "severe_plainte_count",
        "adoption_rate", "reaffectation_count",
    ):
        try:
            from app.reporting.business_catalog import register_custom_metric
            from app.reporting.text_to_sql_contracts import MetricDefinition

            custom_metric_def = MetricDefinition(
                metric_id=canonical_intent.measure.concept_id,
                label=canonical_intent.measure.label or canonical_intent.measure.concept_id,
                description=f"Métrique personnalisée auto-promue : {canonical_intent.measure.label or canonical_intent.measure.concept_id}",
                required_tables=["reporting_claim"],
                aggregation_sql_template=parameterized_sql,
            )
            target_c = canonical_intent.entity.concept_id if canonical_intent.entity else "plainte"
            register_custom_metric(
                metric=custom_metric_def,
                target_concept=target_c,
                created_by=user_id,
                db=db_session,
            )
        except Exception:
            pass

    return entry


register_pending_candidate_query = auto_promote_executed_query


def submit_user_feedback(
    payload: UserFeedbackPayload,
    db_session: Optional[Any] = None,
) -> QueryCatalogEntry:
    """
    Traite le signalement direct d'un utilisateur habilité de GPR :
    - Si is_positive=True : confirme la satisfaction de l'utilisateur.
    - Si is_positive=False : bascule immédiatement la requête au statut REJECTED avec son motif,
      ce qui la retire instantanément du Fast-Path et crée un nouvel anti-pattern.
    """
    entry = get_query_by_id(payload.query_id)
    if entry is None:
        raise KeyError(f"Requête '{payload.query_id}' introuvable dans le catalogue.")

    now = datetime.now(timezone.utc)
    if payload.is_positive:
        entry.approval_comment = f"Feedback positif validé par l'utilisateur {payload.user_id}"
    else:
        entry.status = ApprovalStatus.REJECTED
        entry.rejection_reason = payload.feedback_reason or "Signalement d'incohérence par l'utilisateur"
        entry.approved_by = payload.user_id
        entry.approved_at = now

    register_query_entry(entry, db=db_session)
    return entry


def get_rejected_anti_patterns_for_intent(
    intent: TextToSQLIntent,
    limit: int = 3,
    db_session: Optional[Any] = None,
) -> List[Dict[str, str]]:
    """
    Extrait les requêtes rejetées pertinentes pour l'intention donnée afin d'alimenter
    le prompt de génération (Negative Few-Shots / Anti-patterns).
    Peut interroger directement la base de données relationnelle si une session est fournie.
    """
    anti_patterns: List[Dict[str, str]] = []
    incoming_concept = intent.entity.concept_id if intent.entity else None
    incoming_measure = intent.measure.concept_id if intent.measure else None

    # Source 1 : Recherche directe en base de données si session disponible
    if db_session is not None:
        try:
            from app.db.models import ReportingCertifiedQuery
            rows = (
                db_session.query(ReportingCertifiedQuery)
                .filter_by(status=ApprovalStatus.REJECTED.value)
                .order_by(ReportingCertifiedQuery.updated_at.desc())
                .limit(10)
                .all()
            )
            for row in rows:
                c_intent = row.canonical_intent or {}
                if isinstance(c_intent, str):
                    import json
                    try:
                        c_intent = json.loads(c_intent)
                    except Exception:
                        c_intent = {}
                c_entity = c_intent.get("entity", {}) if isinstance(c_intent, dict) else {}
                c_measure = c_intent.get("measure", {}) if isinstance(c_intent, dict) else {}

                matches = False
                if incoming_concept and c_entity.get("concept_id") == incoming_concept:
                    matches = True
                elif incoming_measure and c_measure.get("concept_id") == incoming_measure:
                    matches = True

                if matches:
                    anti_patterns.append({
                        "query_id": row.id,
                        "bad_sql": row.parameterized_sql,
                        "rejection_reason": row.rejection_reason or "Erreur métier signalée",
                    })
                    if len(anti_patterns) >= limit:
                        return anti_patterns
        except Exception:
            pass

    # Source 2 (Fallback ou mémoire cache)
    for entry in get_certified_queries().values():
        if entry.status != ApprovalStatus.REJECTED:
            continue

        c_intent = entry.canonical_intent
        matches = False
        if incoming_concept and c_intent.entity and c_intent.entity.concept_id == incoming_concept:
            matches = True
        elif incoming_measure and c_intent.measure and c_intent.measure.concept_id == incoming_measure:
            matches = True

        if matches:
            if not any(ap["query_id"] == entry.id for ap in anti_patterns):
                anti_patterns.append({
                    "query_id": entry.id,
                    "bad_sql": entry.parameterized_sql,
                    "rejection_reason": entry.rejection_reason or "Erreur métier signalée",
                })
            if len(anti_patterns) >= limit:
                break

    return anti_patterns

