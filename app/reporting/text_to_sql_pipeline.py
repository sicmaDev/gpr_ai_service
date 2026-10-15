"""
Pipeline Orchestrateur Text-to-SQL Unifié (Step 9).

Ce module centralise et orchestre le flux complet de traitement d'une question analytique :
1. Résolution d'intention canonique (Intent Resolver - Step 4).
2. Court-circuit Fast-Path dans le catalogue homologué (Query Catalog - Step 4 & 8).
3. En cas de Fast-Path miss :
   a. Extraction du sous-schéma minimal (Schema Retriever - Step 5).
   b. Récupération des anti-patterns (Feedbacks négatifs enregistrés - Step 8 / Feedback Loop).
   c. Génération de requête candidate (SQL Generator - Step 5).
   d. Validation de sécurité AST sqlglot bloquante (SQL Validator - Step 6).
   e. Exécution en lecture seule sécurisée avec timeout et quota (SQL Executor - Step 7).
   f. Auto-promotion immédiate en cas de succès au statut APPROVED (Catalog Manager - Step 8).
4. Journalisation systématique des traces d'audit (Audit Service - Step 7).
5. Construction de la réponse typée pour le Front React (Response Builder - Step 9).
"""

from datetime import date, datetime, timezone
import logging
import re
from typing import Callable, List, Optional
from sqlalchemy.orm import Session

from app.reporting.audit_service import AUDIT_SERVICE
from app.reporting.catalog_manager import (
    auto_promote_executed_query,
    get_rejected_anti_patterns_for_intent,
)
from app.reporting.intent_resolver import resolve_intent
from app.reporting.query_catalog import match_intent_in_catalog, sync_queries_with_db
from app.reporting.response_builder import build_reporting_query_response
from app.reporting.schema_retriever import retrieve_minimal_subschema
from app.reporting.schemas import ReportingFilters, ReportingQueryResponse
from app.reporting.sql_executor import execute_read_only_query, format_executable_sql
from app.reporting.sql_generator import generate_sql_candidate
from app.reporting.sql_validator import validate_raw_sql
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    ExecutionStatus,
    IntentTime,
    QuerySource,
    SqlExecutionResult,
)

import os

logger = logging.getLogger(__name__)


def _print_workflow_header(question: str):
    print("\n" + "=" * 80)
    print(">>> [WORKFLOW TEXT-TO-SQL GOUVERNE] TRAITEMENT D'UNE QUESTION ANALYTIQUE")
    print("=" * 80)
    print(f"  * Question posee       : \"{question}\"")


def _print_workflow_step_1(intent):
    print("\n[ETAPE 1 : RESOLUTION D'INTENTION CANONIQUE]")
    print(f"  * Statut resolu        : {intent.status}")
    if intent.entity:
        print(f"  * Entite cible         : {intent.entity.concept_id} (types={intent.entity.types})")
    if intent.measure:
        print(f"  * Mesure calculee      : {intent.measure.concept_id} (libelle: \"{intent.measure.label}\")")
    dims = [d.concept_id for d in intent.dimensions] if intent.dimensions else ["aucune (global)"]
    print(f"  * Dimensions demandees : {dims}")
    if intent.time:
        print(f"  * Periode temporelle   : {intent.time.start_date} -> {intent.time.end_date} (champ={intent.time.field_concept})")
    else:
        print("  * Periode temporelle   : aucune (global sur toute la base)")
    if intent.filters:
        flts = [f"{f.concept_id}={f.value or f.values}" for f in intent.filters]
        print(f"  * Filtres appliques    : {flts}")



def _print_workflow_step_2_fast_path(hit: bool, catalog_entry=None, bound_params=None, executable_sql=None):
    print("\n[ETAPE 2 : CIRCUIT FAST-PATH (CATALOGUE HOMOLOGUE)]")
    if hit and catalog_entry:
        print(f"  * Resultat Fast-Path   : [HIT] (Requete certifiee et pre-validee par la gouvernance)")
        print(f"  * Identifiant Query    : {catalog_entry.id}")
        print(f"  * Libelle Metier       : \"{catalog_entry.natural_language_query}\"")
        sql_to_show = executable_sql or catalog_entry.parameterized_sql
        print("  * REQUETE VALIDEE SELECTIONNEE (SQL EXECUTABLE DIRECTEMENT) :")
        print("  " + "-" * 76)
        for line in sql_to_show.split("\n"):
            print(f"    {line}")
        print("  " + "-" * 76)
        print(f"  * Parametres lies      : {bound_params}")
        print("  * Appel LLM            : Aucun (Court-circuit Fast-Path : zero latence, zero hallucination)")
    else:
        print(f"  * Resultat Fast-Path   : [MISS] (Aucun template homologue correspondant)")
        print(f"  * Action               : Bascule vers le moteur generatif / supervise")


def _print_workflow_step_3_schema(allowed_tables: List[str], subschema_text: Optional[str] = None):
    print("\n[ETAPE 3 : EXTRACTION DU SOUS-SCHEMA MINIMAL (SCHEMA RETRIEVER)]")
    print(f"  * Tables autorisees    : {allowed_tables}")
    print("  * Securite donnees     : Donnees sensibles (client_code, content, etc.) strictement exclues")
    if subschema_text:
        print("  * SCHEMA DE LA BASE DE DONNEES FOURNI AU LLM :")
        print("  " + "-" * 76)
        for line in subschema_text.strip().split("\n"):
            print(f"    {line}")
        print("  " + "-" * 76)


def _print_workflow_step_4_generation(mode: str, sql: str, executable_sql: Optional[str] = None):
    print(f"\n[ETAPE 4 : GENERATION DE LA REQUETE CANDIDATE ({mode})]")
    sql_to_show = executable_sql or sql
    print("  * REQUETE SQL CANDIDATE GENEREE (EXECUTABLE DIRECTEMENT) :")
    print("  " + "-" * 76)
    for line in sql_to_show.strip().split("\n"):
        print(f"    {line}")
    print("  " + "-" * 76)


def _print_workflow_step_5_ast(is_valid: bool, violations: List[str]):
    print("\n[ETAPE 5 : BOUCLIER DE SECURITE AST SQLGLOT (SQL VALIDATOR)]")
    if is_valid:
        print("  * Validation syntaxique: [VALIDE] (0 violation detectee)")
        print("  * Controles valides    : SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte")
    else:
        print(f"  * Validation syntaxique: [BLOQUE] ({len(violations)} violation(s))")
        for v in violations:
            print(f"    - {v}")


def _print_workflow_step_6_execution(exec_result):
    print("\n[ETAPE 6 : EXECUTION SQL EN LECTURE SEULE (SQL EXECUTOR)]")
    print(f"  * Statut execution     : {exec_result.status.value}")
    print(f"  * Lignes retournees    : {exec_result.row_count}")
    print(f"  * Duree d'execution    : {exec_result.execution_time_ms:.2f} ms")
    if exec_result.error_message:
        print(f"  * Erreur rencontree    : {exec_result.error_message}")


def _print_workflow_step_7_restitution(response):
    print("\n[ETAPE 7 : RESTITUTION & CONSTRUCTION DE LA REPONSE]")
    print(f"  * Mode d'execution     : {response.execution_mode}")
    print(f"  * Query ID final       : {response.query_id or 'aucun'}")
    vis_type = response.visualization.type if response.visualization else "aucune"
    print(f"  * Type Visualisation   : {vis_type}")
    ans_sample = response.answer[:120].replace("\n", " ") if response.answer else ""
    print(f"  * Synthese formulee    : \"{ans_sample}{'...' if len(response.answer) > 120 else ''}\"")
    print("=" * 80 + "\n")



def _call_llm_for_intent(prompt: str) -> str:
    """Appel au modèle LLM Nemotron via ollama_client pour la résolution d'intention (Étape 1)."""
    from app.services.llm_service import DEFAULT_MODEL, ollama_client
    if not DEFAULT_MODEL:
        raise RuntimeError("Aucun modèle LLM configuré (LLM_MODEL_NAME est vide)")

    system_content = (
        "Tu es l'analyseur d'intention canonique du moteur analytique bancaire GPR. "
        "Tu ne dois JAMAIS générer de requête SQL ni de fragment SQL. "
        "Génère impérativement et exclusivement un objet JSON valide conforme au schéma TextToSQLIntent."
    )

    print("\n  " + "=" * 76)
    print(f"  >>> [PROMPT TRANSMIS AU LLM (ETAPE 1 : INTENTION) - {DEFAULT_MODEL}]")
    print("  " + "=" * 76)
    print("  [MESSAGE SYSTEME] :")
    print(f"  {system_content}")
    print("\n  [MESSAGE UTILISATEUR] :")
    for line in prompt.strip().split("\n"):
        print(f"  {line}")
    print("  " + "=" * 76)

    response = ollama_client.chat(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0},
    )
    raw_content = response["message"]["content"]

    print("\n  " + "=" * 76)
    print(f"  >>> [REPONSE BRUTE RECUE DU LLM (ETAPE 1 : INTENTION) - {DEFAULT_MODEL}]")
    print("  " + "=" * 76)
    for line in raw_content.strip().split("\n"):
        print(f"  {line}")
    print("  " + "=" * 76 + "\n")

    return raw_content


def _call_llm_for_sql(prompt: str) -> str:
    """Appel au modèle LLM Nemotron via ollama_client pour la génération Text-to-SQL (Étape 4)."""
    from app.services.llm_service import DEFAULT_MODEL, ollama_client
    if not DEFAULT_MODEL:
        raise RuntimeError("Aucun modèle LLM configuré (LLM_MODEL_NAME est vide)")

    system_content = (
        "Tu es un expert Text-to-SQL bancaire pour MySQL. "
        "Génère impérativement un JSON valide conforme au contrat TextToSQLCandidate. "
        "Utilise exclusivement des requêtes SELECT sans wildcard *, avec paramètres liés :param."
    )

    print("\n  " + "=" * 76)
    print(f"  >>> [PROMPT TRANSMIS AU LLM (ETAPE 4 : GENERATION SQL) - {DEFAULT_MODEL}]")
    print("  " + "=" * 76)
    print("  [MESSAGE SYSTEME] :")
    print(f"  {system_content}")
    print("\n  [MESSAGE UTILISATEUR (AVEC SCHEMA DE BASE ET CONSIGNES)] :")
    for line in prompt.strip().split("\n"):
        print(f"  {line}")
    print("  " + "=" * 76)

    response = ollama_client.chat(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0},
    )
    raw_content = response["message"]["content"]

    print("\n  " + "=" * 76)
    print(f"  >>> [REPONSE BRUTE RECUE DU LLM (ETAPE 4 : GENERATION SQL) - {DEFAULT_MODEL}]")
    print("  " + "=" * 76)
    for line in raw_content.strip().split("\n"):
        print(f"  {line}")
    print("  " + "=" * 76 + "\n")

    return raw_content


_default_llm_caller = _call_llm_for_sql


def execute_text_to_sql_pipeline(
    question: str,
    db_session: Optional[Session] = None,
    user_id: str = "system",
    user_filters: Optional[ReportingFilters] = None,
    use_llm: Optional[bool] = None,
    llm_callable: Optional[Callable[[str], str]] = None,
    reference_date: Optional[date] = None,
) -> ReportingQueryResponse:
    """
    Exécute le pipeline text-to-sql gouverné de bout en bout avec traçabilité complète.
    """
    # Résolution de l'activation LLM
    if use_llm is None:
        use_llm = os.getenv("REPORTING_LLM_ENABLED", "false").lower() == "true"

    intent_caller = _call_llm_for_intent if (use_llm and llm_callable is None) else llm_callable
    sql_caller = _call_llm_for_sql if (use_llm and llm_callable is None) else llm_callable

    # Synchronisation préalable avec la base de données (si session fournie)
    if db_session is not None:
        try:
            sync_queries_with_db(db_session)
        except Exception as e:
            logger.warning(f"Pipeline: Échec de synchronisation du catalogue avec la base : {e}")

    _print_workflow_header(question)

    # -------------------------------------------------------------------------
    # 1. Étape 1 : Résolution d'intention canonique (100% LLM via Nemotron si actif)
    # -------------------------------------------------------------------------
    intent = resolve_intent(
        question,
        reference_date=reference_date,
        use_llm=use_llm,
        llm_callable=intent_caller,
    )
    _print_workflow_step_1(intent)

    # Gestion des besoins de clarification
    if intent.status == "needs_clarification":
        clarif_msg = (
            intent.clarification.question
            if intent.clarification
            else "Veuillez préciser votre demande avec une période ou un périmètre temporel."
        )
        print("  -> Interruption : Demande de clarification utilisateur.")
        return ReportingQueryResponse(
            answer=clarif_msg,
            summary="Précision requise",
            execution_mode="CLARIFICATION_NEEDED",
            sources=[],
            visualization=None,
            data=[],
        )

    # Gestion des demandes hors périmètre
    if intent.status == "unsupported":
        reason_msg = (
            intent.unsupported_reason
            or "Cette question ne relève pas du périmètre analytique autorisé de la banque."
        )
        print("  -> Interruption : Question hors périmètre supporté.")
        return ReportingQueryResponse(
            answer=reason_msg,
            summary="Analyse non supportée",
            execution_mode="UNSUPPORTED",
            sources=[],
            visualization=None,
            data=[],
        )

    # Application des filtres utilisateur s'ils sont fournis et non vides
    if user_filters:
        if user_filters.start_date and user_filters.end_date:
            if intent.time is None:
                intent.time = IntentTime(
                    field_concept="receipt_date",
                    start_date=user_filters.start_date,
                    end_date=user_filters.end_date,
                    timezone="Africa/Porto-Novo",
                )
            else:
                intent.time.start_date = user_filters.start_date
                intent.time.end_date = user_filters.end_date
        elif intent.time:
            if user_filters.start_date:
                intent.time.start_date = user_filters.start_date
            if user_filters.end_date:
                intent.time.end_date = user_filters.end_date

    # -------------------------------------------------------------------------
    # 2. Étape 2 : Circuit Fast-Path (Catalogue de requêtes homologuées APPROVED)
    # -------------------------------------------------------------------------
    fast_path_match = match_intent_in_catalog(intent, include_pending=False, db_session=db_session)
    if fast_path_match is not None:
        catalog_entry, bound_params = fast_path_match
        executable_sql = format_executable_sql(catalog_entry.parameterized_sql, bound_params)
        _print_workflow_step_2_fast_path(True, catalog_entry, bound_params, executable_sql=executable_sql)
        logger.info(f"Pipeline: HIT Fast-Path homologué pour query_id='{catalog_entry.id}'")

        exec_result = execute_read_only_query(
            sql=catalog_entry.parameterized_sql,
            parameters=bound_params,
            session=db_session,
        )
        _print_workflow_step_6_execution(exec_result)

        catalog_entry.execution_count += 1
        catalog_entry.last_executed_at = datetime.now(timezone.utc)
        if db_session is not None:
            try:
                from app.reporting.query_catalog import register_query_entry
                register_query_entry(catalog_entry, db=db_session)
            except Exception as e:
                logger.warning(f"Pipeline: Échec de mise à jour des stats : {e}")

        AUDIT_SERVICE.log_execution(
            query_source=QuerySource.FAST_PATH_CERTIFIED,
            sql_executed=executable_sql,
            bound_parameters=bound_params,
            result=exec_result,
            query_id=catalog_entry.id,
            natural_language_query=question,
        )

        sources = ["reporting_claim"]
        if "reporting_service_point" in catalog_entry.parameterized_sql:
            sources.append("reporting_service_point")
        if "reporting_collection_channel" in catalog_entry.parameterized_sql:
            sources.append("reporting_collection_channel")

        response = build_reporting_query_response(
            execution_result=exec_result,
            intent=intent,
            natural_language_query=question,
            sources=sources,
            query_id=catalog_entry.id,
            sql_query=executable_sql,
            execution_mode="FAST_PATH_HOMOLOGATED",
        )
        _print_workflow_step_7_restitution(response)
        return response

    # -------------------------------------------------------------------------
    # 2b. Candidate-Path Déterministe (Requête PENDING déjà existante en base)
    # -------------------------------------------------------------------------
    pending_match = match_intent_in_catalog(intent, include_pending=True, db_session=db_session)
    if pending_match is not None:
        catalog_entry, bound_params = pending_match
        executable_sql = format_executable_sql(catalog_entry.parameterized_sql, bound_params)
        print(f"\n[ETAPE 2 : CANDIDATE-PATH EN ATTENTE]")
        print(f"  * Requête candidate déjà existante en base (query_id='{catalog_entry.id}', status='PENDING')")
        print(f"  * Réutilisation déterministe immédiate pour cohérence utilisateur.")
        logger.info(f"Pipeline: HIT Candidate-Path PENDING pour query_id='{catalog_entry.id}'")

        exec_result = execute_read_only_query(
            sql=catalog_entry.parameterized_sql,
            parameters=bound_params,
            session=db_session,
        )
        _print_workflow_step_6_execution(exec_result)

        catalog_entry.execution_count += 1
        catalog_entry.last_executed_at = datetime.now(timezone.utc)
        if db_session is not None:
            try:
                from app.reporting.query_catalog import register_query_entry
                register_query_entry(catalog_entry, db=db_session)
            except Exception as e:
                logger.warning(f"Pipeline: Échec de mise à jour des stats : {e}")

        AUDIT_SERVICE.log_execution(
            query_source=QuerySource.GENERATIVE_SUPERVISED,
            sql_executed=executable_sql,
            bound_parameters=bound_params,
            result=exec_result,
            query_id=catalog_entry.id,
            natural_language_query=question,
        )

        sources = ["reporting_claim"]
        if "reporting_service_point" in catalog_entry.parameterized_sql:
            sources.append("reporting_service_point")
        if "reporting_collection_channel" in catalog_entry.parameterized_sql:
            sources.append("reporting_collection_channel")

        response = build_reporting_query_response(
            execution_result=exec_result,
            intent=intent,
            natural_language_query=question,
            sources=sources,
            query_id=catalog_entry.id,
            sql_query=executable_sql,
            execution_mode="CANDIDATE_PENDING",
        )
        _print_workflow_step_7_restitution(response)
        return response

    # -------------------------------------------------------------------------
    # 3. Étape 3 : Circuit Supervisé Contrôlé (Fast-Path miss)
    # -------------------------------------------------------------------------
    _print_workflow_step_2_fast_path(False)
    logger.info("Pipeline: Fast-Path miss. Activation du circuit supervisé contrôlé.")

    # a. Extraction des anti-patterns passés pour cette intention
    anti_patterns = get_rejected_anti_patterns_for_intent(intent, db_session=db_session)

    # b. Sous-schéma minimal strict
    allowed_tables, subschema_text = retrieve_minimal_subschema(intent)
    _print_workflow_step_3_schema(allowed_tables, subschema_text)

    # c. Génération candidate
    generation_mode = "LLM Nemotron" if use_llm else "Supervisé Déterministe"
    try:
        candidate = generate_sql_candidate(
            intent=intent,
            use_llm=use_llm,
            llm_callable=sql_caller,
            anti_patterns=anti_patterns,
        )
    except Exception as exc:
        print(f"  [ATTENTION] Exception lors de la generation ({exc}), repli sur le generateur supervise")
        try:
            candidate = generate_sql_candidate(
                intent=intent,
                use_llm=False,
                anti_patterns=anti_patterns,
            )
            generation_mode = "Supervise Deterministe (Fallback)"
        except Exception as fallback_exc:
            # Moteur 2 : Protocole Fail-Closed Invariant (pas de mutation ni de crash)
            print(f"  [ERREUR] Repli deterministe impossible ({fallback_exc}). Activation du protocole fail-closed.")
            exec_fail = SqlExecutionResult(
                status=ExecutionStatus.VALIDATION_FAILED,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=0.0,
                sql_executed="-- Génération SQL impossible pour cette métrique",
                bound_parameters={},
                error_message=f"Impossible de générer une requête certifiée pour cette métrique : {fallback_exc}",
            )
            AUDIT_SERVICE.log_execution(
                query_source=QuerySource.GENERATIVE_SUPERVISED,
                sql_executed="-- Génération SQL impossible",
                bound_parameters={},
                result=exec_fail,
                natural_language_query=question,
            )
            response = build_reporting_query_response(
                execution_result=exec_fail,
                intent=intent,
                natural_language_query=question,
                sources=[],
                sql_query=None,
                execution_mode="GENERATION_FAILED",
            )
            _print_workflow_step_7_restitution(response)
            return response

    # e. Liaison des paramètres et réconciliation réflexive avec le SQL
    bound_params = {}

    # 1. Réservoir contextuel temporel
    if intent.time:
        if intent.time.start_date:
            bound_params["start_date"] = f"{intent.time.start_date.isoformat()} 00:00:00"
        if intent.time.end_date:
            bound_params["end_date"] = f"{intent.time.end_date.isoformat()} 00:00:00"

    # 2. Réservoir contextuel d'entité (résout génériquement :claim_type, :type, :entity_type)
    if intent.entity and intent.entity.types:
        scalar_type = intent.entity.types[0]
        bound_params["claim_type"] = scalar_type
        bound_params["claim_type_param"] = scalar_type
        bound_params["type"] = scalar_type
        bound_params["entity_type"] = scalar_type
        bound_params["type_plainte"] = scalar_type

    # 3. Réservoir contextuel des filtres (générique sur tous les concepts du reporting)
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

    # 4. Résolution explicite via les métadonnées de source du candidat
    if hasattr(candidate, "parameters") and candidate.parameters:
        for p_name, p_meta in candidate.parameters.items():
            if p_name not in bound_params:
                src = getattr(p_meta, "source", None) or ""
                if src == "intent.time.start_date" and intent.time and intent.time.start_date:
                    bound_params[p_name] = f"{intent.time.start_date.isoformat()} 00:00:00"
                elif src == "intent.time.end_date" and intent.time and intent.time.end_date:
                    bound_params[p_name] = f"{intent.time.end_date.isoformat()} 00:00:00"
                elif "intent.filters." in src:
                    target_concept = src.split("intent.filters.")[-1]
                    for flt in intent.filters:
                        if flt.concept_id in (target_concept, f"ai_{target_concept}"):
                            bound_params[p_name] = flt.value if flt.value is not None else flt.values
                elif "claim_type" in src or p_name in ("claim_type", "type"):
                    if intent.entity and intent.entity.types:
                        bound_params[p_name] = intent.entity.types[0]
                else:
                    for flt in intent.filters:
                        val = flt.value if flt.value is not None else flt.values
                        cid = flt.concept_id
                        syns = filter_synonyms_map.get(cid, [cid])
                        if p_name in syns or any(p_name.startswith(f"{syn}_") or p_name.endswith(f"_{syn}") for syn in syns):
                            bound_params[p_name] = val
                            break

    # 5. Réconciliation proactive des placeholders SQL avec les filtres existants
    sql_placeholders = set(re.findall(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)", candidate.sql))
    for ph in sql_placeholders:
        if ph not in bound_params:
            for flt in intent.filters:
                val = flt.value if flt.value is not None else flt.values
                cid = flt.concept_id
                syns = filter_synonyms_map.get(cid, [cid])
                if ph in syns or any(ph.startswith(f"{syn}_") or ph.endswith(f"_{syn}") for syn in syns):
                    bound_params[ph] = val
                    break

    # 6. Élagage universel des paramètres orphelins :
    # Ne conserver dans candidate.parameters que les paramètres effectivement référencés dans candidate.sql
    if hasattr(candidate, "parameters") and candidate.parameters:
        candidate.parameters = {
            k: v for k, v in candidate.parameters.items()
            if k in sql_placeholders
        }

    _print_workflow_step_4_generation(generation_mode, candidate.sql)

    # d. Bouclier AST préalable de sécurité
    ast_check = validate_raw_sql(candidate.sql, allowed_tables=allowed_tables)
    _print_workflow_step_5_ast(ast_check.is_valid, ast_check.violations)

    if not ast_check.is_valid:
        error_msg = " | ".join(ast_check.violations)
        logger.warning(f"Pipeline: Requête candidate bloquée par l'AST : {error_msg}")
        exec_fail = SqlExecutionResult(
            status=ExecutionStatus.VALIDATION_FAILED,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0.0,
            sql_executed=candidate.sql,
            bound_parameters=bound_params,
            error_message=error_msg,
        )
        AUDIT_SERVICE.log_execution(
            query_source=QuerySource.GENERATIVE_SUPERVISED,
            sql_executed=candidate.sql,
            bound_parameters=bound_params,
            result=exec_fail,
            natural_language_query=question,
        )
        response = build_reporting_query_response(
            execution_result=exec_fail,
            intent=intent,
            natural_language_query=question,
            sources=candidate.used_schema,
            sql_query=candidate.sql,
            execution_mode="VALIDATION_BLOCKED",
        )
        _print_workflow_step_7_restitution(response)
        return response

    # f. Exécution Read-Only
    exec_result = execute_read_only_query(
        sql=candidate.sql,
        parameters=bound_params,
        allowed_tables=allowed_tables,
        session=db_session,
    )
    _print_workflow_step_6_execution(exec_result)

    # g. Enregistrement de la requête candidate au statut PENDING
    assigned_query_id = None
    if exec_result.status == ExecutionStatus.SUCCESS:
        saved_entry = auto_promote_executed_query(
            canonical_intent=intent,
            parameterized_sql=candidate.sql,
            natural_language_query=question,
            user_id=user_id,
            parameters_schema=candidate.parameters,
            db_session=db_session,
        )
        assigned_query_id = saved_entry.id
        status_lbl = saved_entry.status.value
        print(f"  * Cycle de vie         : [{status_lbl}] Requête candidate enregistrée avec query_id='{assigned_query_id}'")


    # h. Traçabilité d'audit
    AUDIT_SERVICE.log_execution(
        query_source=QuerySource.GENERATIVE_SUPERVISED,
        sql_executed=candidate.sql,
        bound_parameters=bound_params,
        result=exec_result,
        query_id=assigned_query_id,
        natural_language_query=question,
    )

    exec_mode = "GENERATIVE_LLM" if "LLM" in generation_mode else "SUPERVISED_FALLBACK"

    # i. Restitution finale
    response = build_reporting_query_response(
        execution_result=exec_result,
        intent=intent,
        natural_language_query=question,
        sources=candidate.used_schema,
        query_id=assigned_query_id,
        sql_query=candidate.sql,
        execution_mode=exec_mode,
    )
    _print_workflow_step_7_restitution(response)
    return response

