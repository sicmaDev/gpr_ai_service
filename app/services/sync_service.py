import logging
import os
from datetime import datetime, timezone
from typing import Any, Iterable

import requests
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import ReportingClaim, ReportingSuggestion, ReportingSyncState
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

JAVA_API_URL = os.getenv(
    "JAVA_EXPORT_CLAIMS_URL",
    "http://localhost:8020/api/v1/ai/export-claims",
)
JAVA_EXPORT_SUGGESTIONS_URL = os.getenv(
    "JAVA_EXPORT_SUGGESTIONS_URL",
    "http://localhost:8020/api/v1/ai/export-suggestions",
)
SYNC_NAME = "spring_boot_claims"
SYNC_SUGGESTIONS_NAME = "spring_boot_suggestions"
PAGE_SIZE = 500
ENABLE_RAG_SYNC = os.getenv("REPORTING_ENABLE_RAG_SYNC", "false").lower() == "true"
EXCLUDED_STATUSES = frozenset({"TEMP_SAVED"})


def parse_source_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError(f"Date source invalide: {value!r}")
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _risk_level(value: Any) -> str | None:
    normalized = _text(value)
    if not normalized:
        return None
    return {
        "LOW": "MINEUR",
        "FAIBLE": "MINEUR",
        "MINOR": "MINEUR",
        "MINEUR": "MINEUR",
        "MEDIUM": "MOYEN",
        "MOYEN": "MOYEN",
        "HIGH": "GRAVE",
        "ÉLEVÉ": "GRAVE",
        "ELEVE": "GRAVE",
        "GRAVE": "GRAVE",
    }.get(normalized.strip().upper(), normalized.strip().upper())


def _is_excluded(row: dict[str, Any]) -> bool:
    status = _text(row.get("statut_final"))
    return bool(status and status.strip().upper() in EXCLUDED_STATUSES)


def claim_values(row: dict[str, Any], synced_at: datetime) -> dict[str, Any]:
    source_id = row.get("id")
    if source_id is None:
        raise ValueError("Dossier source sans id")

    source_updated_at = parse_source_datetime(row.get("updatedAt"))
    created_at = parse_source_datetime(row.get("date_creation"))
    return {
        "source_claim_id": int(source_id),
        "source_code": _text(row.get("code")),
        "client_code": _text(row.get("codeClient")),
        "claim_type": _text(row.get("claimType")) or "",
        "status": _text(row.get("statut_final")),
        "category": _text(row.get("aiSuggestedCategory") or row.get("objet_categorie")),
        "motif": _text(row.get("aiSuggestedMotif") or row.get("motif_reclamation")),
        "product": _text(row.get("produit_service")),
        "service_point": _text(row.get("point_service_indexe")),
        "agency": _text(row.get("agence") or row.get("point_service_indexe")),
        "channel": _text(row.get("modalite_depot")),
        "team": _text(row.get("equipe")),
        "content": _text(row.get("texte_plainte")),
        "solution": _text(row.get("texte_solution")),
        "ai_urgency": _risk_level(row.get("aiUrgency")),
        "ai_sentiment": _text(row.get("aiSentiment")),
        # The risk level is defined by the claim motif in gps_objet. AI urgency
        # remains only a backward-compatible fallback for older exports.
        "risk_level": _risk_level(row.get("riskLevel") or row.get("aiUrgency")),
        "ai_risk_score": row.get("aiRiskScore"),
        "ai_summary": _text(row.get("aiSummary")),
        "created_at": created_at,
        "receipt_at": parse_source_datetime(row.get("receiptDateTime")),
        "source_updated_at": source_updated_at,
        "affected_at": parse_source_datetime(row.get("affectedAt") or row.get("affected_at")),
        "resolved_at": parse_source_datetime(row.get("resolvedAt") or row.get("resolved_at")),
        "sla_due_at": parse_source_datetime(row.get("slaDueAt") or row.get("sla_due_at")),
        "satisfaction_status": _text(row.get("satisfactionStatus") or row.get("satisfaction_status")),
        "objet_id": row.get("objetId") if row.get("objetId") is not None else row.get("objet_id"),
        "product_id": row.get("productId") if row.get("productId") is not None else row.get("product_id"),
        "service_point_id": row.get("servicePointId") if row.get("servicePointId") is not None else row.get("service_point_id"),
        "collection_channel_id": row.get("collectionChannelId") if row.get("collectionChannelId") is not None else row.get("collection_channel_id"),
        "collector_id": row.get("collectorId") if row.get("collectorId") is not None else row.get("collector_id"),
        "synced_at": synced_at,
    }


def suggestion_values(row: dict[str, Any], synced_at: datetime) -> dict[str, Any]:
    source_id = row.get("id")
    if source_id is None:
        raise ValueError("Suggestion source sans id")

    source_updated_at = parse_source_datetime(row.get("updatedAt") or row.get("updated_at"))
    created_at = parse_source_datetime(row.get("createdAt") or row.get("created_at") or row.get("date_creation"))
    receipt_at = parse_source_datetime(row.get("receiptDateTime") or row.get("receipt_at"))
    recorded_at = receipt_at or created_at

    content = _text(row.get("content") or row.get("description") or row.get("texte_suggestion"))
    title = _text(row.get("title") or (content[:250] if content else "Suggestion"))

    return {
        "source_suggestion_id": int(source_id),
        "reference": _text(row.get("code") or row.get("reference")),
        "title": title,
        "description": content,
        "client_code": _text(row.get("codeClient") or row.get("client_code")),
        "client_name": _text(row.get("clientFirstAndLastName") or row.get("client_name")),
        "phone": _text(row.get("tel") or row.get("phone")),
        "email": _text(row.get("email")),
        "channel": _text(row.get("canal") or row.get("channel")),
        "status": _text(row.get("status") or row.get("statut")),
        "impact_level": _text(row.get("impactLevel") or row.get("impact_level") or "MOYEN"),
        "origine": _text(row.get("origine") or "EXTERNE"),
        "objet_id": row.get("objetId") if row.get("objetId") is not None else row.get("objet_id"),
        "product_id": row.get("productId") if row.get("productId") is not None else row.get("product_id"),
        "service_point_id": row.get("servicePointId") if row.get("servicePointId") is not None else row.get("service_point_id"),
        "collection_channel_id": row.get("collectionChannelId") if row.get("collectionChannelId") is not None else row.get("collection_channel_id"),
        "enregistre_par_id": row.get("collectorId") if row.get("collectorId") is not None else row.get("enregistre_par_id"),
        "evaluator_notes": _text(row.get("commentaire") or row.get("evaluator_notes")),
        "recorded_at": recorded_at,
        "created_at": created_at,
        "updated_at": source_updated_at,
        "synced_at": synced_at,
    }


def upsert_claims(db: Session, rows: Iterable[dict[str, Any]], synced_at: datetime) -> int:
    return upsert_claims_with_metrics(db, rows, synced_at)["processed"]


def upsert_suggestions(db: Session, rows: Iterable[dict[str, Any]], synced_at: datetime) -> int:
    return upsert_suggestions_with_metrics(db, rows, synced_at)["processed"]


def upsert_suggestions_with_metrics(
    db: Session,
    rows: Iterable[dict[str, Any]],
    synced_at: datetime,
) -> dict[str, int]:
    metrics = {"processed": 0, "inserted": 0, "updated": 0, "ignored": 0}
    for row in rows:
        if _is_excluded(row):
            metrics["ignored"] += 1
            continue
        values = suggestion_values(row, synced_at)
        existing = db.scalar(
            select(ReportingSuggestion).where(
                ReportingSuggestion.source_suggestion_id == values["source_suggestion_id"]
            )
        )
        if existing is None:
            db.add(ReportingSuggestion(**values))
            metrics["inserted"] += 1
        else:
            for key, value in values.items():
                setattr(existing, key, value)
            metrics["updated"] += 1
        metrics["processed"] += 1
    return metrics


def upsert_claims_with_metrics(
    db: Session,
    rows: Iterable[dict[str, Any]],
    synced_at: datetime,
) -> dict[str, int]:
    metrics = {"processed": 0, "inserted": 0, "updated": 0, "ignored": 0}
    for row in rows:
        if _is_excluded(row):
            metrics["ignored"] += 1
            continue
        values = claim_values(row, synced_at)
        existing = db.scalar(
            select(ReportingClaim).where(
                ReportingClaim.source_claim_id == values["source_claim_id"]
            )
        )
        if existing is None:
            db.add(ReportingClaim(**values))
            metrics["inserted"] += 1
        else:
            for key, value in values.items():
                setattr(existing, key, value)
            metrics["updated"] += 1
        metrics["processed"] += 1
    return metrics


def sync_claims_to_rag(rows: Iterable[dict[str, Any]]) -> int:
    """Index synchronized claims in Chroma only when explicitly enabled."""
    from app.services.vector_service import vector_db

    vector_rows = list(rows)
    if vector_rows:
        return vector_db.build_index_from_data(vector_rows)
    return 0


def fetch_claim_pages(
    session: requests.Session,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[dict[str, Any]]:
    all_claims: list[dict[str, Any]] = []
    page = 0
    params: dict[str, Any] = {"size": PAGE_SIZE}
    if updated_after:
        params["updatedAfter"] = updated_after.isoformat()
    if updated_before:
        params["updatedBefore"] = updated_before.isoformat()

    while True:
        params["page"] = page
        response = session.get(JAVA_API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            all_claims.extend(payload)
            break
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
            raise ValueError("Réponse API Java invalide : content manquant")
        all_claims.extend(payload["content"])
        if not payload.get("hasNext", False):
            break
        page += 1
    return all_claims


def fetch_suggestion_pages(
    session: requests.Session,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[dict[str, Any]]:
    all_suggestions: list[dict[str, Any]] = []
    page = 0
    params: dict[str, Any] = {"size": PAGE_SIZE}
    if updated_after:
        params["updatedAfter"] = updated_after.isoformat()
    if updated_before:
        params["updatedBefore"] = updated_before.isoformat()

    while True:
        params["page"] = page
        response = session.get(JAVA_EXPORT_SUGGESTIONS_URL, params=params, timeout=30)
        if response.status_code == 404:
            logger.warning(
                "Endpoint suggestions (%s) introuvable (404). Backend Java pas encore mis à jour.",
                JAVA_EXPORT_SUGGESTIONS_URL,
            )
            return []
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            all_suggestions.extend(payload)
            break
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
            raise ValueError("Réponse API Java suggestions invalide : content manquant")
        all_suggestions.extend(payload["content"])
        if not payload.get("hasNext", False):
            break
        page += 1
    return all_suggestions


def perform_sync_claims(
    db: Session,
    http_session: requests.Session,
    full: bool = False,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == SYNC_NAME
        )
    )
    cursor = None if full or state is None else state.last_successful_sync_at
    if state is None:
        state = ReportingSyncState(sync_name=SYNC_NAME, updated_at=started_at)
        db.add(state)
        db.flush()
    state.last_started_at = started_at
    state.last_error = None
    state.last_error_count = 0
    claims = fetch_claim_pages(http_session, updated_after=cursor)
    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = upsert_claims_with_metrics(db, claims, synced_at)
    updated_dates = [
        parsed
        for parsed in (
            parse_source_datetime(row.get("updatedAt")) for row in claims
        )
        if parsed is not None
    ]
    latest = max(updated_dates, default=cursor)
    deleted_count = db.execute(
        delete(ReportingClaim).where(
            ReportingClaim.status.in_(EXCLUDED_STATUSES)
        )
    ).rowcount or 0
    indexed_count = 0
    if ENABLE_RAG_SYNC:
        indexed_count = sync_claims_to_rag(
            row for row in claims if not _is_excluded(row)
        )
    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state.last_successful_sync_at = latest
    state.updated_at = completed_at
    state.last_completed_at = completed_at
    state.last_duration_ms = int(
        (completed_at - started_at).total_seconds() * 1000
    )
    state.last_received_count = len(claims)
    state.last_inserted_count = metrics["inserted"]
    state.last_updated_count = metrics["updated"]
    state.last_ignored_count = metrics["ignored"]
    state.last_deleted_count = deleted_count
    state.last_indexed_count = indexed_count
    return {
        **metrics,
        "received": len(claims),
        "deleted": deleted_count,
        "indexed": indexed_count,
        "cursor_before": cursor,
        "cursor_after": latest,
    }


def perform_sync_suggestions(
    db: Session,
    http_session: requests.Session,
    full: bool = False,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == SYNC_SUGGESTIONS_NAME
        )
    )
    cursor = None if full or state is None else state.last_successful_sync_at
    if state is None:
        state = ReportingSyncState(sync_name=SYNC_SUGGESTIONS_NAME, updated_at=started_at)
        db.add(state)
        db.flush()
    state.last_started_at = started_at
    state.last_error = None
    state.last_error_count = 0
    suggestions = fetch_suggestion_pages(http_session, updated_after=cursor)
    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = upsert_suggestions_with_metrics(db, suggestions, synced_at)
    updated_dates = [
        parsed
        for parsed in (
            parse_source_datetime(row.get("updatedAt") or row.get("updated_at"))
            for row in suggestions
        )
        if parsed is not None
    ]
    latest = max(updated_dates, default=cursor)
    deleted_count = db.execute(
        delete(ReportingSuggestion).where(
            ReportingSuggestion.status.in_(EXCLUDED_STATUSES)
        )
    ).rowcount or 0
    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state.last_successful_sync_at = latest
    state.updated_at = completed_at
    state.last_completed_at = completed_at
    state.last_duration_ms = int(
        (completed_at - started_at).total_seconds() * 1000
    )
    state.last_received_count = len(suggestions)
    state.last_inserted_count = metrics["inserted"]
    state.last_updated_count = metrics["updated"]
    state.last_ignored_count = metrics["ignored"]
    state.last_deleted_count = deleted_count
    state.last_indexed_count = 0
    return {
        **metrics,
        "received": len(suggestions),
        "deleted": deleted_count,
        "indexed": 0,
        "cursor_before": cursor,
        "cursor_after": latest,
    }


def perform_sync(
    db: Session | None = None,
    http_session: requests.Session | None = None,
    full: bool = False,
    target: str = "all",
) -> dict[str, Any]:
    owns_db = db is None
    db = db or SessionLocal()
    http_session = http_session or requests.Session()
    normalized_target = (target or "all").strip().lower()
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        claims_result: dict[str, Any] | None = None
        suggestions_result: dict[str, Any] | None = None

        if normalized_target in ("all", "claims"):
            claims_result = perform_sync_claims(db, http_session, full=full)
        if normalized_target in ("all", "suggestions"):
            suggestions_result = perform_sync_suggestions(db, http_session, full=full)

        db.commit()

        if normalized_target == "claims":
            return {"target": "claims", **(claims_result or {})}
        if normalized_target == "suggestions":
            return {"target": "suggestions", **(suggestions_result or {})}

        claims_res = claims_result or {
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "ignored": 0,
            "received": 0,
            "deleted": 0,
            "indexed": 0,
            "cursor_before": None,
            "cursor_after": None,
        }
        sugg_res = suggestions_result or {
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "ignored": 0,
            "received": 0,
            "deleted": 0,
            "indexed": 0,
            "cursor_before": None,
            "cursor_after": None,
        }

        return {
            "target": "all",
            "claims": claims_res,
            "suggestions": sugg_res,
            "processed": claims_res["processed"] + sugg_res["processed"],
            "inserted": claims_res["inserted"] + sugg_res["inserted"],
            "updated": claims_res["updated"] + sugg_res["updated"],
            "ignored": claims_res["ignored"] + sugg_res["ignored"],
            "received": claims_res["received"] + sugg_res["received"],
            "deleted": claims_res["deleted"] + sugg_res["deleted"],
            "indexed": claims_res.get("indexed", 0),
            "cursor_before": claims_res.get("cursor_before"),
            "cursor_after": claims_res.get("cursor_after"),
        }
    except Exception as exc:
        db.rollback()
        completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        target_keys = (
            [SYNC_NAME]
            if normalized_target == "claims"
            else [SYNC_SUGGESTIONS_NAME]
            if normalized_target == "suggestions"
            else [SYNC_NAME, SYNC_SUGGESTIONS_NAME]
        )
        for sync_key in target_keys:
            st = db.scalar(
                select(ReportingSyncState).where(
                    ReportingSyncState.sync_name == sync_key
                )
            )
            if st is None:
                st = ReportingSyncState(sync_name=sync_key, updated_at=completed_at)
                db.add(st)
            st.last_started_at = started_at
            st.last_completed_at = completed_at
            st.last_duration_ms = int(
                (completed_at - started_at).total_seconds() * 1000
            )
            st.last_error_count = (st.last_error_count or 0) + 1
            st.last_error = str(exc)[:4000]
            st.updated_at = completed_at
        db.commit()
        logger.exception("Reporting sync failed for target=%s", normalized_target)
        raise
    finally:
        if owns_db:
            db.close()

