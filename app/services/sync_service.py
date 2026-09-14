import logging
import os
from datetime import datetime, timezone
from typing import Any, Iterable

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReportingClaim, ReportingSyncState
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

JAVA_API_URL = os.getenv(
    "JAVA_EXPORT_CLAIMS_URL",
    "http://localhost:8020/api/v1/ai/export-claims",
)
SYNC_NAME = "spring_boot_claims"
PAGE_SIZE = 500
ENABLE_RAG_SYNC = os.getenv("REPORTING_ENABLE_RAG_SYNC", "false").lower() == "true"


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
        "risk_level": _risk_level(row.get("riskLevel") or row.get("aiUrgency")),
        "ai_risk_score": row.get("aiRiskScore"),
        "ai_summary": _text(row.get("aiSummary")),
        "created_at": created_at,
        "receipt_at": parse_source_datetime(row.get("receiptDateTime")),
        "source_updated_at": source_updated_at,
        "affected_at": parse_source_datetime(row.get("affectedAt")),
        "resolved_at": parse_source_datetime(row.get("resolvedAt")),
        "sla_due_at": parse_source_datetime(row.get("slaDueAt")),
        "satisfaction_status": _text(row.get("satisfactionStatus")),
        "synced_at": synced_at,
    }


def upsert_claims(db: Session, rows: Iterable[dict[str, Any]], synced_at: datetime) -> int:
    count = 0
    for row in rows:
        values = claim_values(row, synced_at)
        existing = db.scalar(
            select(ReportingClaim).where(
                ReportingClaim.source_claim_id == values["source_claim_id"]
            )
        )
        if existing is None:
            db.add(ReportingClaim(**values))
        else:
            for key, value in values.items():
                setattr(existing, key, value)
        count += 1
    return count


def sync_claims_to_rag(rows: Iterable[dict[str, Any]]) -> None:
    """Index synchronized claims in Chroma only when explicitly enabled."""
    from app.services.vector_service import vector_db

    vector_rows = list(rows)
    if vector_rows:
        vector_db.build_index_from_data(vector_rows)


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


def perform_sync(
    db: Session | None = None,
    http_session: requests.Session | None = None,
    full: bool = False,
) -> dict[str, Any]:
    owns_db = db is None
    db = db or SessionLocal()
    http_session = http_session or requests.Session()
    try:
        state = db.scalar(
            select(ReportingSyncState).where(
                ReportingSyncState.sync_name == SYNC_NAME
            )
        )
        cursor = None if full or state is None else state.last_successful_sync_at
        claims = fetch_claim_pages(http_session, updated_after=cursor)
        synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
        processed = upsert_claims(db, claims, synced_at)
        updated_dates = [
            parsed
            for parsed in (
                parse_source_datetime(row.get("updatedAt")) for row in claims
            )
            if parsed is not None
        ]
        latest = max(updated_dates, default=cursor)
        if state is None:
            state = ReportingSyncState(sync_name=SYNC_NAME)
            db.add(state)
        state.last_successful_sync_at = latest
        state.updated_at = synced_at
        db.commit()
        if ENABLE_RAG_SYNC:
            sync_claims_to_rag(claims)
        return {
            "processed": processed,
            "cursor_before": cursor,
            "cursor_after": latest,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_db:
            db.close()
