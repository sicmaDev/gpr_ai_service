import json
import logging
import os
import re
import unicodedata
from datetime import date, datetime
from time import perf_counter
from typing import Any
from zoneinfo import ZoneInfo

from .catalog import (
    CATALOG_VERSION,
    DIMENSIONS,
    FILTER_FIELDS,
    validate_analysis,
    validate_grouping,
)
from .periods import SUPPORTED_PERIODS, resolve_period
from .query import extract_question_filters, parse_intent
from .schemas import (
    ReportingAnalysis,
    ReportingComparison,
    ReportingDateRange,
    ReportingFilters,
    ReportingIntent,
    ReportingIntentResult,
)
from .trace_logging import trace_info

logger = logging.getLogger(__name__)
REPORTING_LLM_ENABLED = os.getenv("REPORTING_LLM_ENABLED", "false").lower() == "true"
REPORTING_INTENT_MODE = os.getenv(
    "REPORTING_INTENT_MODE",
    "hybrid" if REPORTING_LLM_ENABLED else "deterministic",
).strip().lower()
if REPORTING_INTENT_MODE not in {"llm_only", "hybrid", "deterministic"}:
    raise ValueError("REPORTING_INTENT_MODE doit etre llm_only, hybrid ou deterministic")
REPORTING_LLM_FORMULATION_ENABLED = (
    os.getenv("REPORTING_LLM_FORMULATION_ENABLED", "false").lower() == "true"
)
REPORTING_TIMEZONE = os.getenv("REPORTING_TIMEZONE", "Africa/Abidjan")


def _parse_json(content: str) -> dict[str, Any] | None:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def _validated_payload(
    payload: dict[str, Any],
    filters: ReportingFilters,
    question: str | None = None,
) -> ReportingIntentResult:
    allowed_fields = {
        "analysis",
        "catalog_version",
        "metric",
        "group_by",
        "filters",
        "period",
        "comparison",
        "limit",
        "justification",
    }
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        return ReportingIntentResult(
            supported=False,
            reason=f"Champs d'intention non autorises : {sorted(unknown_fields)}",
        )
    group_by = payload.get("group_by")
    if group_by is not None and (
        not isinstance(group_by, str) or group_by not in DIMENSIONS
    ):
        return ReportingIntentResult(
            supported=False,
            reason="Le regroupement produit par le LLM est hors catalogue.",
        )

    candidate_filters = payload.get("filters", {})
    if not isinstance(candidate_filters, dict):
        return ReportingIntentResult(
            supported=False, reason="Les filtres produits par le LLM sont invalides."
        )
    unknown_fields = set(candidate_filters) - FILTER_FIELDS
    if unknown_fields:
        return ReportingIntentResult(
            supported=False,
            reason=f"Filtres LLM non autorises : {sorted(unknown_fields)}",
        )

    analysis_payload = payload.get("analysis")
    legacy_metric = payload.get("metric")
    analysis = None
    if analysis_payload is not None:
        supplied_catalog_version = payload.get("catalog_version")
        if supplied_catalog_version != CATALOG_VERSION:
            return ReportingIntentResult(
                supported=False,
                reason=(
                    "Version du catalogue absente ou incompatible : "
                    f"attendue {CATALOG_VERSION}."
                ),
            )
        justification = payload.get("justification")
        if not isinstance(justification, str) or not justification.strip():
            return ReportingIntentResult(
                supported=False,
                reason="La justification de l'intention hybride est absente ou invalide.",
            )
        if not isinstance(analysis_payload, dict):
            return ReportingIntentResult(
                supported=False, reason="La definition analysis est invalide."
            )
        unknown_analysis_fields = set(analysis_payload) - {
            "kind",
            "operation",
            "target",
            "condition",
            "name",
        }
        if unknown_analysis_fields:
            return ReportingIntentResult(
                supported=False,
                reason=(
                    "Champs analysis non autorises : "
                    f"{sorted(unknown_analysis_fields)}"
                ),
            )
        try:
            analysis = ReportingAnalysis(**analysis_payload)
        except (TypeError, ValueError) as exc:
            return ReportingIntentResult(
                supported=False, reason=f"La definition analysis est invalide : {exc}"
            )
        reason = validate_analysis(
            analysis.kind,
            analysis.operation,
            analysis.target,
            analysis.condition,
            analysis.name,
        )
        if reason:
            return ReportingIntentResult(supported=False, reason=reason)
        if analysis.kind == "primitive" and analysis.operation == "trend" and group_by is None:
            group_by = "month"
        grouping_reason = validate_grouping(
            analysis.kind,
            analysis.operation,
            analysis.target,
            analysis.name,
            group_by,
        )
        if grouping_reason:
            return ReportingIntentResult(supported=False, reason=grouping_reason)
        from .catalog import legacy_metric as map_legacy_metric

        legacy_metric = map_legacy_metric(
            analysis.operation, analysis.target, analysis.condition
        )
        if legacy_metric is None:
            legacy_metric = "count"
    else:
        allowed_metrics = {
            "count",
            "count_active",
            "count_overdue",
            "count_severe",
            "average_risk_score",
            "trend",
        }
        if not isinstance(legacy_metric, str) or legacy_metric not in allowed_metrics:
            return ReportingIntentResult(
                supported=False,
                reason="Le LLM n'a pas fourni une analyse ou une metrique valide.",
            )

    period = payload.get("period")
    if isinstance(period, dict):
        unknown_period_fields = set(period) - {"start_date", "end_date"}
        if unknown_period_fields:
            return ReportingIntentResult(
                supported=False,
                reason=(
                    "Champs period non autorises : "
                    f"{sorted(unknown_period_fields)}"
                ),
            )
        try:
            date_range = ReportingDateRange(**period)
        except (TypeError, ValueError) as exc:
            return ReportingIntentResult(
                supported=False, reason=f"Les bornes de periode sont invalides : {exc}"
            )
        candidate_filters = {
            **candidate_filters,
            "start_date": date_range.start_date,
            "end_date": date_range.end_date,
        }
    elif period is not None:
        if not isinstance(period, str) or period not in SUPPORTED_PERIODS:
            return ReportingIntentResult(
                supported=False, reason="La periode produite par le LLM est invalide."
            )
        try:
            start_date, end_date = resolve_period(period, date.today())
        except ValueError as exc:
            return ReportingIntentResult(supported=False, reason=str(exc))
        candidate_filters = {
            **candidate_filters,
            "start_date": start_date,
            "end_date": end_date,
        }

    comparison_payload = payload.get("comparison")
    comparison = None
    if comparison_payload is not None:
        if not isinstance(comparison_payload, dict):
            return ReportingIntentResult(
                supported=False, reason="La comparaison produite par le LLM est invalide."
            )
        unknown_comparison_fields = set(comparison_payload) - {
            "current_start_date",
            "current_end_date",
            "previous_start_date",
            "previous_end_date",
        }
        if unknown_comparison_fields:
            return ReportingIntentResult(
                supported=False,
                reason=(
                    "Champs comparison non autorises : "
                    f"{sorted(unknown_comparison_fields)}"
                ),
            )
        try:
            comparison = ReportingComparison(**comparison_payload)
        except (TypeError, ValueError) as exc:
            return ReportingIntentResult(
                supported=False, reason=f"La comparaison produite par le LLM est invalide : {exc}"
            )

    limit = payload.get("limit", 10)
    if limit is None:
        limit = 10
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        return ReportingIntentResult(
            supported=False, reason="La limite produite par le LLM doit etre entre 1 et 50."
        )
    try:
        if hasattr(filters, "model_copy"):
            merged = filters.model_copy(update=candidate_filters)
        else:
            merged = filters.copy(update=candidate_filters)
        # Revalidate merged data instead of trusting Pydantic's copy(update=...).
        merged_data = (
            merged.model_dump() if hasattr(merged, "model_dump") else merged.dict()
        )
        merged = ReportingFilters(**merged_data)
        intent = ReportingIntent(
            catalog_version=(
                supplied_catalog_version if analysis_payload is not None else CATALOG_VERSION
            ),
            metric=legacy_metric,
            analysis=analysis,
            group_by=group_by,
            filters=merged,
            period=period if isinstance(period, str) else None,
            limit=limit,
            comparison=comparison,
        )
    except (TypeError, ValueError) as exc:
        return ReportingIntentResult(
            supported=False, reason=f"Les filtres produits par le LLM sont invalides : {exc}"
        )
    if question:
        reason = _validate_explicit_constraints(question, intent)
        if reason:
            return ReportingIntentResult(supported=False, reason=reason)
    return _normalize_legacy_intent(
        ReportingIntentResult(supported=True, intent=intent)
    )


def _normalize_question(question: str) -> str:
    return unicodedata.normalize("NFKD", question.lower()).encode(
        "ascii", "ignore"
    ).decode("ascii")


def _validate_explicit_constraints(
    question: str,
    intent: ReportingIntent,
) -> str | None:
    text = _normalize_question(question)
    analysis = intent.analysis
    operation = analysis.operation if analysis else None
    condition = analysis.condition if analysis else None
    metric = intent.metric
    filters = intent.filters

    lexical_filters = extract_question_filters(question)
    for field in (
        "agency",
        "channel",
        "category",
        "motif",
        "product",
        "team",
        "service_point",
        "status",
        "satisfaction_status",
        "claim_type",
        "risk_level",
    ):
        expected_value = getattr(lexical_filters, field)
        if expected_value is None:
            continue
        actual_value = getattr(filters, field)
        if actual_value is None or _normalize_question(actual_value) != _normalize_question(
            expected_value
        ):
            return (
                f"L'intention ne reprend pas le filtre explicite "
                f"{field}={expected_value}."
            )

    if re.search(r"\b(?:plainte|plaintes|reclamation|reclamations)\b", text):
        if filters.claim_type != "CLAIM":
            return "L'intention omet le filtre claim_type=CLAIM explicitement demande."
    if re.search(r"\b(?:denonciation|denonciations)\b", text):
        if filters.claim_type != "DENUNCIACION":
            return "L'intention omet le filtre claim_type=DENUNCIACION explicitement demande."

    groups = {
        "agency": r"\b(?:par\s+(?:les?\s+)?agences?|agences?\s+les\s+plus)\b",
        "channel": r"\bpar\s+(?:les?\s+)?canaux?\b",
        "category": r"\bpar\s+(?:les?\s+)?categories?\b",
        "motif": r"\bpar\s+(?:les?\s+)?motifs?\b",
        "product": r"\bpar\s+(?:les?\s+)?produits?\b",
        "team": r"\bpar\s+(?:les?\s+)?equipes?\b",
        "risk_level": r"\bpar\s+(?:les?\s+)?risques?\b",
        "service_point": r"\bpar\s+(?:les?\s+)?points?\s+de\s+service\b",
        "month": r"\bpar\s+mois\b",
    }
    for group, pattern in groups.items():
        if re.search(pattern, text) and intent.group_by != group:
            return f"L'intention omet le regroupement group_by={group} explicitement demande."

    if re.search(r"\b(?:retard|retards|depasse|depassee|depassees|sla)\b", text):
        if condition != "overdue" and metric != "count_overdue":
            return "L'intention omet la condition overdue explicitement demandee."
    if re.search(r"\b(?:grave|graves)\b", text):
        if condition != "severe" and filters.risk_level != "GRAVE":
            return "L'intention omet la condition severe explicitement demandee."
    if re.search(r"\b(?:en cours|actif|actifs|active|actives)\b", text):
        if condition != "active" and metric != "count_active":
            return "L'intention omet la condition active explicitement demandee."
    if re.search(r"\b(?:score moyen|moyenne du score)\b", text):
        if not (
            operation == "average" and analysis.target == "risk_score"
        ) and metric != "average_risk_score":
            return "L'intention omet l'operation average sur risk_score."

    has_period_request = bool(
        re.search(
            r"\b(?:aujourd'hui|hier|cette semaine|semaine derniere|ce mois-ci|ce mois ci|"
            r"mois en cours|mois dernier|mois precedent|ce trimestre|trimestre dernier|"
            r"cette annee|annee derniere|du \d{1,2}\s+au\s+\d{1,2})\b",
            text,
        )
        or re.search(
            r"\b(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|"
            r"octobre|novembre|decembre)\s*(?:20\d{2})?\b",
            text,
        )
    )
    if has_period_request and not (
        filters.start_date and filters.end_date and filters.start_date <= filters.end_date
    ) and intent.comparison is None:
        return "L'intention omet les bornes de la periode explicitement demandee."

    if re.search(r"\b(?:compare|comparaison|comparer|par rapport)\b", text):
        if intent.comparison is None:
            return "L'intention omet la comparaison explicitement demandee."

    top_match = re.search(r"\b(?:top|trois|troisieme)\s*(\d+)?\b", text)
    if top_match:
        requested_limit = int(top_match.group(1)) if top_match.group(1) else (
            3 if "trois" in top_match.group(0) else None
        )
        if requested_limit and intent.limit != requested_limit:
            return f"L'intention omet la limite top {requested_limit} explicitement demandee."
    return None


def _technical_failure(reason: str, mode: str, question: str, filters, trace_id):
    trace_info(
        logger,
        trace_id,
        "reporting.intent.technical_failure",
        mode=mode,
        reason=reason,
    )
    if mode == "hybrid":
        fallback = parse_intent(question, filters)
        if fallback.supported:
            fallback = _normalize_legacy_intent(fallback)
            trace_info(
                logger,
                trace_id,
                "reporting.intent.selected",
                intent_source="deterministic_fallback",
                catalog_version=(
                    fallback.intent.catalog_version if fallback.intent else None
                ),
            )
            return fallback
        return ReportingIntentResult(
            supported=False,
            reason=(
                f"Interpreteur LLM indisponible ({reason}); "
                f"le repli deterministe n'a pas reconnu la question : {fallback.reason}"
            ),
        )
    return ReportingIntentResult(
        supported=False,
        reason=(
            f"Interpreteur LLM indisponible ({reason}); "
            f"aucun repli autorise en mode {mode}."
        ),
    )


def _normalize_legacy_intent(result: ReportingIntentResult) -> ReportingIntentResult:
    intent = result.intent
    if not result.supported or intent is None or intent.analysis is not None:
        return result
    mapping = {
        "count": ("count", "claim", None),
        "count_active": ("count", "claim", "active"),
        "count_overdue": ("count", "claim", "overdue"),
        "count_severe": ("count", "claim", "severe"),
        "trend": ("trend", "claim", None),
    }
    mapped = mapping.get(intent.metric)
    if mapped is None:
        return result
    analysis = ReportingAnalysis(
        kind="primitive",
        operation=mapped[0],
        target=mapped[1],
        condition=mapped[2],
    )
    normalized_intent = (
        intent.model_copy(
            update={"analysis": analysis, "catalog_version": CATALOG_VERSION}
        )
        if hasattr(intent, "model_copy")
        else intent.copy(
            update={"analysis": analysis, "catalog_version": CATALOG_VERSION}
        )
    )
    return ReportingIntentResult(supported=True, intent=normalized_intent)


def interpret_question(
    question: str,
    filters: ReportingFilters,
    trace_id: str | None = None,
) -> ReportingIntentResult:
    trace = trace_id or "-"
    mode = REPORTING_INTENT_MODE
    if mode == "deterministic":
        result = parse_intent(question, filters)
        result = _normalize_legacy_intent(result)
        trace_info(
            logger,
            trace,
            "reporting.intent.selected",
            mode=mode,
            intent_source="deterministic",
            catalog_version=result.intent.catalog_version if result.intent else None,
            supported=result.supported,
            metric=result.intent.metric if result.intent else None,
        )
        return result

    try:
        from app.services.llm_service import DEFAULT_MODEL, ollama_client
    except Exception as exc:
        logger.exception("[%s] reporting.llm.interpretation client_initialization_failed", trace)
        return _technical_failure(type(exc).__name__, mode, question, filters, trace)

    if not DEFAULT_MODEL:
        return _technical_failure("model_missing", mode, question, filters, trace)

    system_prompt = """
Tu es l'interpréteur du Reporting IA GPR. Convertis la question en intention JSON,
sans SQL et sans calculer de résultat. Retourne exactement les champs:
{"catalog_version":"__CATALOG_VERSION__",
"analysis":{"kind":"primitive","operation":"count","target":"claim","condition":null},
"group_by":null,"filters":{},"period":null,"comparison":null,"limit":10,
"justification":"Courte explication de l'intention."}

OPERATIONS: count, count_distinct, sum, average, min, max, ratio, trend.
CIBLES: claim, agency, category, motif, product, channel, team, risk_level,
service_point, risk_score.
CONDITIONS: overdue, active, severe, within_sla, has_sla, satisfied, evaluated.
INDICATEURS SPECIALISES: sla_compliance_rate (pourcentage de dossiers clotures
avec SLA resolus avant ou a leur echeance, parmi les dossiers clotures avec
echeance SLA valide), average_resolution_time (duree moyenne entre receipt_at
et resolved_at, en jours calendaires), risk_distribution (repartition des
dossiers par risk_level).
GROUP_BY: null, agency, category, motif, product, channel, team, risk_level,
service_point, month.
Pour risk_distribution, utilise obligatoirement group_by=risk_level.
FILTERS: start_date, end_date, claim_type, agency, channel, category, motif,
product, team, status, risk_level, service_point, satisfaction_status.
claim_type vaut CLAIM ou DENUNCIACION. Utilise count_distinct pour compter des valeurs distinctes; count avec target=claim
compte les dossiers. sum/average/min/max ne sont autorises que pour risk_score;
trend uniquement pour claim. ratio avec target=claim et condition calcule le
pourcentage de dossiers qui satisfont cette condition dans la population
filtrée. Pour les ratios SLA et les indicateurs spécialisés, utilise
kind=business_metric et name dans les indicateurs spécialisés.
Une période doit etre retournee sous la forme {"start_date":"YYYY-MM-DD",
"end_date":"YYYY-MM-DD"}, calculée avec la date de référence courante.
Une comparaison doit inclure current_start_date, current_end_date,
previous_start_date et previous_end_date au format YYYY-MM-DD.
N'invente jamais les dates, filtres ou regroupements. limit est un entier de 1 a 50.
Si aucun groupement n'est demande, group_by=null, sauf pour trend qui exige
group_by=month. justification courte, sans raisonnement interne détaillé.
Pas d'autres clés.
""".strip()
    system_prompt = system_prompt.replace("__CATALOG_VERSION__", CATALOG_VERSION)
    try:
        reference_date = datetime.now(ZoneInfo(REPORTING_TIMEZONE)).date()
    except (KeyError, ValueError) as exc:
        logger.exception("[%s] reporting.reference_timezone.invalid", trace)
        return ReportingIntentResult(
            supported=False,
            reason=f"Fuseau horaire Reporting invalide : {REPORTING_TIMEZONE}",
        )
    user_prompt = (
        f"Date de référence : {reference_date.isoformat()}\n"
        f"Fuseau horaire : {REPORTING_TIMEZONE}\nQuestion : {question}"
    )
    trace_info(
        logger,
        trace,
        "reporting.llm.interpretation.started",
        model=DEFAULT_MODEL,
        mode=mode,
    )
    started_at = perf_counter()
    try:
        response = ollama_client.chat(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            format="json",
            options={"temperature": 0},
        )
    except Exception as exc:
        logger.exception("[%s] reporting.llm.interpretation request_failed", trace)
        return _technical_failure(type(exc).__name__, mode, question, filters, trace)

    if not isinstance(response, dict) or not isinstance(response.get("message"), dict):
        return ReportingIntentResult(
            supported=False, reason="La reponse du fournisseur LLM est malformee."
        )
    content = response["message"].get("content", "")
    if not isinstance(content, str):
        return ReportingIntentResult(
            supported=False, reason="Le contenu retourne par le fournisseur LLM est invalide."
        )
    payload = _parse_json(content)
    trace_info(
        logger,
        trace,
        "reporting.llm.interpretation.response",
        elapsed_ms=round((perf_counter() - started_at) * 1000, 1),
        raw_response=content,
        parsed_payload=payload,
        justification=payload.get("justification") if payload else None,
    )
    if payload is None:
        return ReportingIntentResult(
            supported=False, reason="La reponse LLM n'est pas un objet JSON valide."
        )
    validated = _validated_payload(payload, filters, question)
    trace_info(
        logger,
        trace,
        "reporting.intent.selected",
        mode=mode,
        intent_source="llm",
        catalog_version=(
            validated.intent.catalog_version if validated.intent else None
        ),
        supported=validated.supported,
        metric=validated.intent.metric if validated.intent else None,
        analysis=(
            (
                validated.intent.analysis.model_dump()
                if hasattr(validated.intent.analysis, "model_dump")
                else validated.intent.analysis.dict()
            )
            if validated.intent and validated.intent.analysis
            else None
        ),
        rejection_reason=validated.reason,
    )
    return validated


def formulate_answer(
    question: str,
    answer: str,
    results: list[dict[str, Any]],
    trace_id: str | None = None,
) -> str:
    if not REPORTING_LLM_FORMULATION_ENABLED:
        logger.info(
            "[trace_id=%s] reporting.llm.formulation disabled fallback=deterministic",
            trace_id or "-",
        )
        return answer
    try:
        from app.services.llm_service import DEFAULT_MODEL, ollama_client

        if not DEFAULT_MODEL:
            raise RuntimeError("REPORTING_LLM_FORMULATION_ENABLED est actif sans modele LLM.")
        response = ollama_client.chat(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Reformule en francais clair la reponse analytique fournie. "
                        "Ne change aucun chiffre et n'ajoute aucune information."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"question": question, "answer": answer, "results": results},
                        ensure_ascii=False,
                    ),
                },
            ],
            options={"temperature": 0},
        )
        content = response.get("message", {}).get("content", "").strip()
        return content or answer
    except Exception:
        logger.exception("[%s] reporting.llm.formulation failed", trace_id or "-")
        raise
