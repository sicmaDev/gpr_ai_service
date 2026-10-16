import logging
import os
from datetime import datetime, timezone
from typing import Any, Iterable

import requests
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    ReportingCategorieObjet,
    ReportingClaim,
    ReportingCollectionChannel,
    ReportingHistoriqueAffectation,
    ReportingObjet,
    ReportingPoste,
    ReportingProduct,
    ReportingSatisfactionMeasure,
    ReportingServicePoint,
    ReportingSolution,
    ReportingSuggestion,
    ReportingSyncState,
    ReportingUser,
)
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
JAVA_EXPORT_AFFECTATIONS_URL = os.getenv(
    "JAVA_EXPORT_AFFECTATIONS_URL",
    "http://localhost:8020/api/v1/ai/export-affectations",
)
JAVA_EXPORT_REFERENTIELS_URL = os.getenv(
    "JAVA_EXPORT_REFERENTIELS_URL",
    "http://localhost:8020/api/v1/ai/export-referentiels",
)
JAVA_EXPORT_SOLUTIONS_URL = os.getenv(
    "JAVA_EXPORT_SOLUTIONS_URL",
    "http://localhost:8020/api/v1/ai/export-solutions",
)
SYNC_NAME = "spring_boot_claims"
SYNC_SUGGESTIONS_NAME = "spring_boot_suggestions"
SYNC_AFFECTATIONS_NAME = "spring_boot_affectations"
SYNC_REFERENTIELS_NAME = "spring_boot_referentiels"
SYNC_SOLUTIONS_NAME = "spring_boot_solutions"
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


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def affectation_values(row: dict[str, Any], synced_at: datetime | None = None) -> dict[str, Any]:
    source_id = row.get("id")
    if source_id is None:
        raise ValueError("Affectation source sans id")

    date_affectation = parse_source_datetime(row.get("dateAffectation") or row.get("date_affectation"))
    date_fin_affectation = parse_source_datetime(row.get("dateFinAffectation") or row.get("date_fin_affectation"))
    last_notification = parse_source_datetime(row.get("lastNotification") or row.get("last_notification"))

    return {
        "id": int(source_id),
        "reclamation_id": _int_or_none(row.get("reclamationId") if row.get("reclamationId") is not None else row.get("reclamation_id")),
        "suggestion_id": _int_or_none(row.get("suggestionId") if row.get("suggestionId") is not None else row.get("suggestion_id")),
        "code_plainte": _text(row.get("codePlainte") or row.get("code_plainte")),
        "type_plainte": _text(row.get("typePlainte") or row.get("type_plainte")),
        "nom_agent": _text(row.get("nomAgent") or row.get("nom_agent")),
        "email_agent": _text(row.get("emailAgent") or row.get("email_agent")),
        "affecteur_id": _int_or_none(row.get("affecteurId") if row.get("affecteurId") is not None else row.get("affecteur_id")),
        "nom_affecteur": _text(row.get("nomAffecteur") or row.get("nom_affecteur")),
        "email_affecteur": _text(row.get("emailAffecteur") or row.get("email_affecteur")),
        "date_affectation": date_affectation,
        "delai_jours": _int_or_none(row.get("delaiJours") if row.get("delaiJours") is not None else row.get("delai_jours")) or 2,
        "date_fin_affectation": date_fin_affectation,
        "affectation_precedente_id": _int_or_none(row.get("affectationPrecedenteId") if row.get("affectationPrecedenteId") is not None else row.get("affectation_precedente_id")),
        "last_notification": last_notification,
        "mail_envoye": bool(row.get("mailEnvoye") or row.get("mail_envoye") or False),
        "sms_envoye": bool(row.get("smsEnvoye") or row.get("sms_envoye") or False),
    }


def upsert_affectations(
    db: Session,
    rows: Iterable[dict[str, Any]],
    synced_at: datetime | None = None,
) -> int:
    return upsert_affectations_with_metrics(db, rows, synced_at)["processed"]


def upsert_affectations_with_metrics(
    db: Session,
    rows: Iterable[dict[str, Any]],
    synced_at: datetime | None = None,
) -> dict[str, int]:
    metrics = {"processed": 0, "inserted": 0, "updated": 0, "ignored": 0}
    for row in rows:
        values = affectation_values(row, synced_at)
        existing = db.scalar(
            select(ReportingHistoriqueAffectation).where(
                ReportingHistoriqueAffectation.id == values["id"]
            )
        )
        if existing is None:
            db.add(ReportingHistoriqueAffectation(**values))
            metrics["inserted"] += 1
        else:
            for key, value in values.items():
                setattr(existing, key, value)
            metrics["updated"] += 1
        metrics["processed"] += 1
    return metrics


def solution_values(row: dict[str, Any]) -> dict[str, Any]:
    raw_id = row.get("id")
    if raw_id is None:
        raise ValueError("L'identifiant de la solution est obligatoire")
    claim_id = row.get("claimId") if row.get("claimId") is not None else row.get("claim_id")
    if claim_id is None:
        raise ValueError(f"L'identifiant de claim pour la solution {raw_id} est obligatoire")

    approved_at = parse_source_datetime(row.get("approvedAt") or row.get("approved_at"))
    unapproved_at = parse_source_datetime(row.get("unapprovedAt") or row.get("unapproved_at"))

    commentaire = _text(row.get("commentaire") or row.get("content"))
    motif = _text(row.get("motifDesaprobation") or row.get("motif_desaprobation"))
    author_id = _int_or_none(row.get("authorId") if row.get("authorId") is not None else row.get("author_id"))
    approver_id = _int_or_none(row.get("approverId") if row.get("approverId") is not None else row.get("approver_id"))
    status = _text(row.get("status")) or "APPROVED"
    is_ai_proposed = bool(row.get("isAiProposed") or row.get("is_ai_proposed") or False)
    ai_selected = _text(row.get("aiSelectedSolution") or row.get("ai_selected_solution"))

    return {
        "id": int(raw_id),
        "claim_id": int(claim_id),
        "author_id": author_id,
        "status": status,
        "commentaire": commentaire,
        "motif_desaprobation": motif,
        "approver_id": approver_id,
        "approved_at": approved_at,
        "unapproved_at": unapproved_at,
        "is_ai_proposed": is_ai_proposed,
        "ai_selected_solution": ai_selected,
    }


def satisfaction_measure_values(row: dict[str, Any], solution_id: int) -> dict[str, Any]:
    raw_id = row.get("id")
    if raw_id is None:
        raise ValueError("L'identifiant de la mesure de satisfaction est obligatoire")
    measurer_id = _int_or_none(row.get("measurerId") if row.get("measurerId") is not None else row.get("measurer_id"))
    status = _text(row.get("status")) or "SATISFIED"
    commentaire = _text(row.get("commentaire"))
    measure_date_time = parse_source_datetime(row.get("measureDateTime") or row.get("measure_date_time")) or datetime.now(timezone.utc).replace(tzinfo=None)

    return {
        "id": int(raw_id),
        "solution_id": solution_id,
        "measurer_id": measurer_id,
        "status": status,
        "commentaire": commentaire,
        "measure_date_time": measure_date_time,
    }


def upsert_solutions_with_metrics(
    db: Session,
    rows: Iterable[dict[str, Any]],
    synced_at: datetime | None = None,
) -> dict[str, int]:
    metrics = {"processed": 0, "inserted": 0, "updated": 0, "ignored": 0}
    for row in rows:
        try:
            s_values = solution_values(row)
        except ValueError as exc:
            logger.warning("Ligne de solution invalide ignorée: %s", exc)
            metrics["ignored"] += 1
            continue

        claim_exists = db.scalar(
            select(ReportingClaim.id).where(ReportingClaim.id == s_values["claim_id"])
        )
        if claim_exists is None:
            claim_id_match = db.scalar(
                select(ReportingClaim.id).where(ReportingClaim.source_claim_id == s_values["claim_id"])
            )
            if claim_id_match is not None:
                s_values["claim_id"] = claim_id_match
            else:
                logger.warning(
                    "Solution %s ignorée car la réclamation associée (ID %s) n'existe pas dans reporting_claim",
                    s_values["id"],
                    s_values["claim_id"],
                )
                metrics["ignored"] += 1
                continue

        if s_values["author_id"] is not None:
            if not db.scalar(select(ReportingUser.id).where(ReportingUser.id == s_values["author_id"])):
                s_values["author_id"] = None
        if s_values["approver_id"] is not None:
            if not db.scalar(select(ReportingUser.id).where(ReportingUser.id == s_values["approver_id"])):
                s_values["approver_id"] = None

        existing_sol = db.scalar(
            select(ReportingSolution).where(ReportingSolution.id == s_values["id"])
        )
        if existing_sol is None:
            db.add(ReportingSolution(**s_values))
            metrics["inserted"] += 1
        else:
            for k, v in s_values.items():
                setattr(existing_sol, k, v)
            metrics["updated"] += 1
        metrics["processed"] += 1
        db.flush()

        sm_row = row.get("satisfactionMeasure") or row.get("satisfaction_measure")
        if isinstance(sm_row, dict) and sm_row.get("id") is not None:
            try:
                sm_values = satisfaction_measure_values(sm_row, s_values["id"])
                if sm_values["measurer_id"] is not None:
                    if not db.scalar(select(ReportingUser.id).where(ReportingUser.id == sm_values["measurer_id"])):
                        sm_values["measurer_id"] = None

                existing_sm = db.scalar(
                    select(ReportingSatisfactionMeasure).where(
                        ReportingSatisfactionMeasure.id == sm_values["id"]
                    )
                )
                if existing_sm is None:
                    db.add(ReportingSatisfactionMeasure(**sm_values))
                else:
                    for k, v in sm_values.items():
                        setattr(existing_sm, k, v)
                db.flush()
            except ValueError as exc:
                logger.warning("Mesure de satisfaction invalide ignorée: %s", exc)

    return metrics


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


def fetch_affectation_pages(
    session: requests.Session,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[dict[str, Any]]:
    all_affectations: list[dict[str, Any]] = []
    page = 0
    params: dict[str, Any] = {"size": PAGE_SIZE}
    if updated_after:
        params["updatedAfter"] = updated_after.isoformat()
    if updated_before:
        params["updatedBefore"] = updated_before.isoformat()

    while True:
        params["page"] = page
        response = session.get(JAVA_EXPORT_AFFECTATIONS_URL, params=params, timeout=30)
        if response.status_code == 404:
            logger.warning(
                "Endpoint affectations (%s) introuvable (404). Backend Java pas encore mis à jour.",
                JAVA_EXPORT_AFFECTATIONS_URL,
            )
            return []
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            all_affectations.extend(payload)
            break
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
            raise ValueError("Réponse API Java affectations invalide : content manquant")
        all_affectations.extend(payload["content"])
        if not payload.get("hasNext", False):
            break
        page += 1
    return all_affectations


def fetch_referentiels(session: requests.Session) -> dict[str, Any]:
    response = session.get(JAVA_EXPORT_REFERENTIELS_URL, timeout=30)
    if response.status_code == 404:
        logger.warning(
            "Endpoint referentiels (%s) introuvable (404). Backend Java pas encore mis à jour.",
            JAVA_EXPORT_REFERENTIELS_URL,
        )
        return {}
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Réponse API Java référentiels invalide")
    return payload


def fetch_solution_pages(
    session: requests.Session,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[dict[str, Any]]:
    all_solutions: list[dict[str, Any]] = []
    page = 0
    params: dict[str, Any] = {"size": PAGE_SIZE}
    if updated_after:
        params["updatedAfter"] = updated_after.isoformat()
    if updated_before:
        params["updatedBefore"] = updated_before.isoformat()

    while True:
        params["page"] = page
        response = session.get(JAVA_EXPORT_SOLUTIONS_URL, params=params, timeout=30)
        if response.status_code == 404:
            logger.warning(
                "Endpoint solutions (%s) introuvable (404). Backend Java pas encore mis à jour.",
                JAVA_EXPORT_SOLUTIONS_URL,
            )
            return []
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            all_solutions.extend(payload)
            break
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
            raise ValueError("Réponse API Java solutions invalide : content manquant")
        all_solutions.extend(payload["content"])
        if not payload.get("hasNext", False):
            break
        page += 1
    return all_solutions


def _upsert_dimension_items(db: Session, model_cls: Any, items: list[dict[str, Any]]) -> tuple[int, int]:
    inserted = 0
    updated = 0
    for item in items:
        source_id = item.get("id")
        if source_id is None:
            continue
        existing = db.scalar(select(model_cls).where(model_cls.id == int(source_id)))
        if existing is not None:
            for k, v in item.items():
                setattr(existing, k, v)
            updated += 1
        else:
            if hasattr(model_cls, "libelle") and item.get("libelle"):
                legacy = db.scalar(select(model_cls).where(model_cls.libelle == item["libelle"]))
                if legacy is not None:
                    db.delete(legacy)
                    db.flush()
            elif hasattr(model_cls, "code") and item.get("code"):
                legacy = db.scalar(select(model_cls).where(model_cls.code == item["code"]))
                if legacy is not None:
                    db.delete(legacy)
                    db.flush()
            db.add(model_cls(**item))
            inserted += 1
    return inserted, updated


def upsert_referentiels_with_metrics(
    db: Session,
    payload: dict[str, Any],
) -> dict[str, int]:
    metrics = {"processed": 0, "inserted": 0, "updated": 0, "ignored": 0, "received": 0}
    if not payload:
        return metrics

    # 1. Postes
    postes = [
        {"id": int(p["id"]), "libelle": _text(p.get("libelle")), "description": _text(p.get("description"))}
        for p in payload.get("postes", []) if p.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingPoste, postes)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(postes)

    # 2. Service Points
    service_points = [
        {
            "id": int(sp["id"]),
            "libelle": _text(sp.get("libelle")),
            "description": _text(sp.get("description")),
            "type": _text(sp.get("type")) or "AGENCE",
            "is_principal_agence": bool(sp.get("isPrincipalAgence") or False),
            "direction_id": _int_or_none(sp.get("directionId")),
        }
        for sp in payload.get("servicePoints", []) if sp.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingServicePoint, service_points)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(service_points)

    # 3. Collection Channels
    collection_channels = [
        {"id": int(cc["id"]), "libelle": _text(cc.get("libelle")), "description": _text(cc.get("description"))}
        for cc in payload.get("collectionChannels", []) if cc.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingCollectionChannel, collection_channels)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(collection_channels)

    # 4. Products
    products = [
        {
            "id": int(pr["id"]),
            "libelle": _text(pr.get("libelle")),
            "description": _text(pr.get("description")),
            "is_deleted": bool(pr.get("isDeleted") or False),
        }
        for pr in payload.get("products", []) if pr.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingProduct, products)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(products)

    # 5. Categorie Objet
    categories = [
        {"id": int(cat["id"]), "libelle": _text(cat.get("libelle")), "description": _text(cat.get("description"))}
        for cat in payload.get("categories", []) if cat.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingCategorieObjet, categories)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(categories)

    # 6. Objets (depend on categories)
    objets = [
        {
            "id": int(obj["id"]),
            "categorie_id": _int_or_none(obj.get("categorieId")),
            "libelle": _text(obj.get("libelle")),
            "risque_level": _risk_level(obj.get("risqueLevel")),
            "processing_time": _int_or_none(obj.get("processingTime")) or 2,
        }
        for obj in payload.get("objets", []) if obj.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingObjet, objets)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(objets)

    # 7. Users (depend on service_points and postes)
    users = [
        {
            "id": int(u["id"]),
            "code": _text(u.get("code")),
            "firstandlastname": _text(u.get("firstandlastname")),
            "email": _text(u.get("email")),
            "additionalrole": _text(u.get("additionalrole")),
            "service_point_id": _int_or_none(u.get("servicePointId")),
            "poste_id": _int_or_none(u.get("posteId")),
        }
        for u in payload.get("users", []) if u.get("id") is not None
    ]
    ins, upd = _upsert_dimension_items(db, ReportingUser, users)
    metrics["inserted"] += ins
    metrics["updated"] += upd
    metrics["received"] += len(users)

    metrics["processed"] = metrics["inserted"] + metrics["updated"]
    return metrics


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


def perform_sync_affectations(
    db: Session,
    http_session: requests.Session,
    full: bool = False,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == SYNC_AFFECTATIONS_NAME
        )
    )
    cursor = None if full or state is None else state.last_successful_sync_at
    if state is None:
        state = ReportingSyncState(sync_name=SYNC_AFFECTATIONS_NAME, updated_at=started_at)
        db.add(state)
        db.flush()
    state.last_started_at = started_at
    state.last_error = None
    state.last_error_count = 0
    affectations = fetch_affectation_pages(http_session, updated_after=cursor)
    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = upsert_affectations_with_metrics(db, affectations, synced_at)
    updated_dates = [
        parsed
        for parsed in (
            parse_source_datetime(
                row.get("updatedAt")
                or row.get("updated_at")
                or row.get("dateAffectation")
                or row.get("date_affectation")
            )
            for row in affectations
        )
        if parsed is not None
    ]
    latest = max(updated_dates, default=cursor)
    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state.last_successful_sync_at = latest
    state.updated_at = completed_at
    state.last_completed_at = completed_at
    state.last_duration_ms = int(
        (completed_at - started_at).total_seconds() * 1000
    )
    state.last_received_count = len(affectations)
    state.last_inserted_count = metrics["inserted"]
    state.last_updated_count = metrics["updated"]
    state.last_ignored_count = metrics["ignored"]
    state.last_deleted_count = 0
    state.last_indexed_count = 0
    return {
        **metrics,
        "received": len(affectations),
        "deleted": 0,
        "indexed": 0,
        "cursor_before": cursor,
        "cursor_after": latest,
    }


def perform_sync_referentiels(
    db: Session,
    http_session: requests.Session,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == SYNC_REFERENTIELS_NAME
        )
    )
    if state is None:
        state = ReportingSyncState(sync_name=SYNC_REFERENTIELS_NAME, updated_at=started_at)
        db.add(state)
        db.flush()
    state.last_started_at = started_at
    state.last_error = None
    state.last_error_count = 0
    payload = fetch_referentiels(http_session)
    metrics = upsert_referentiels_with_metrics(db, payload)
    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state.last_successful_sync_at = completed_at
    state.updated_at = completed_at
    state.last_completed_at = completed_at
    state.last_duration_ms = int(
        (completed_at - started_at).total_seconds() * 1000
    )
    state.last_received_count = metrics["received"]
    state.last_inserted_count = metrics["inserted"]
    state.last_updated_count = metrics["updated"]
    state.last_ignored_count = metrics["ignored"]
    state.last_deleted_count = 0
    state.last_indexed_count = 0
    return {
        **metrics,
        "deleted": 0,
        "indexed": 0,
        "cursor_before": None,
        "cursor_after": completed_at,
    }


def perform_sync_solutions(
    db: Session,
    http_session: requests.Session,
    full: bool = False,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == SYNC_SOLUTIONS_NAME
        )
    )
    cursor = None if full or state is None else state.last_successful_sync_at
    if state is None:
        state = ReportingSyncState(sync_name=SYNC_SOLUTIONS_NAME, updated_at=started_at)
        db.add(state)
        db.flush()
    state.last_started_at = started_at
    state.last_error = None
    state.last_error_count = 0
    solutions = fetch_solution_pages(http_session, updated_after=cursor)
    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = upsert_solutions_with_metrics(db, solutions, synced_at)
    updated_dates = [
        parsed
        for parsed in (
            parse_source_datetime(row.get("updatedAt") or row.get("createdAt")) for row in solutions
        )
        if parsed is not None
    ]
    latest = max(updated_dates, default=cursor)
    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state.last_successful_sync_at = latest or completed_at
    state.updated_at = completed_at
    state.last_completed_at = completed_at
    state.last_duration_ms = int(
        (completed_at - started_at).total_seconds() * 1000
    )
    state.last_received_count = len(solutions)
    state.last_inserted_count = metrics["inserted"]
    state.last_updated_count = metrics["updated"]
    state.last_ignored_count = metrics["ignored"]
    state.last_deleted_count = 0
    state.last_indexed_count = 0
    return {
        **metrics,
        "received": len(solutions),
        "deleted": 0,
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
        referentiels_result: dict[str, Any] | None = None
        claims_result: dict[str, Any] | None = None
        suggestions_result: dict[str, Any] | None = None
        affectations_result: dict[str, Any] | None = None
        solutions_result: dict[str, Any] | None = None

        if normalized_target in ("all", "referentiels"):
            referentiels_result = perform_sync_referentiels(db, http_session)
        if normalized_target in ("all", "claims"):
            claims_result = perform_sync_claims(db, http_session, full=full)
        if normalized_target in ("all", "suggestions"):
            suggestions_result = perform_sync_suggestions(db, http_session, full=full)
        if normalized_target in ("all", "affectations"):
            affectations_result = perform_sync_affectations(db, http_session, full=full)
        if normalized_target in ("all", "solutions"):
            solutions_result = perform_sync_solutions(db, http_session, full=full)

        db.commit()

        if normalized_target == "referentiels":
            return {"target": "referentiels", **(referentiels_result or {})}
        if normalized_target == "claims":
            return {"target": "claims", **(claims_result or {})}
        if normalized_target == "suggestions":
            return {"target": "suggestions", **(suggestions_result or {})}
        if normalized_target == "affectations":
            return {"target": "affectations", **(affectations_result or {})}
        if normalized_target == "solutions":
            return {"target": "solutions", **(solutions_result or {})}

        ref_res = referentiels_result or {
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
        aff_res = affectations_result or {
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
        sol_res = solutions_result or {
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
            "referentiels": ref_res,
            "claims": claims_res,
            "suggestions": sugg_res,
            "affectations": aff_res,
            "solutions": sol_res,
            "processed": ref_res["processed"] + claims_res["processed"] + sugg_res["processed"] + aff_res["processed"] + sol_res["processed"],
            "inserted": ref_res["inserted"] + claims_res["inserted"] + sugg_res["inserted"] + aff_res["inserted"] + sol_res["inserted"],
            "updated": ref_res["updated"] + claims_res["updated"] + sugg_res["updated"] + aff_res["updated"] + sol_res["updated"],
            "ignored": ref_res["ignored"] + claims_res["ignored"] + sugg_res["ignored"] + aff_res["ignored"] + sol_res["ignored"],
            "received": ref_res["received"] + claims_res["received"] + sugg_res["received"] + aff_res["received"] + sol_res["received"],
            "deleted": claims_res["deleted"] + sugg_res["deleted"] + aff_res["deleted"] + sol_res.get("deleted", 0),
            "indexed": claims_res.get("indexed", 0),
            "cursor_before": claims_res.get("cursor_before"),
            "cursor_after": claims_res.get("cursor_after"),
        }
    except Exception as exc:
        db.rollback()
        completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if normalized_target == "claims":
            target_keys = [SYNC_NAME]
        elif normalized_target == "suggestions":
            target_keys = [SYNC_SUGGESTIONS_NAME]
        elif normalized_target == "affectations":
            target_keys = [SYNC_AFFECTATIONS_NAME]
        elif normalized_target == "referentiels":
            target_keys = [SYNC_REFERENTIELS_NAME]
        elif normalized_target == "solutions":
            target_keys = [SYNC_SOLUTIONS_NAME]
        else:
            target_keys = [SYNC_REFERENTIELS_NAME, SYNC_NAME, SYNC_SUGGESTIONS_NAME, SYNC_AFFECTATIONS_NAME, SYNC_SOLUTIONS_NAME]

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


