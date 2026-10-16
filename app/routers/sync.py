import os
import logging
from uuid import uuid4
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReportingSyncState
from app.db.session import get_db
from app.services.vector_service import vector_db

router = APIRouter(prefix="/sync", tags=["Synchronisation"])
logger = logging.getLogger(__name__)


class MotifData(BaseModel):
    libelle: str
    description: Optional[str] = None
    gravite: Optional[str] = None


class CategorieData(BaseModel):
    description: Optional[str] = None
    motifs: List[MotifData]


class CategoriesSyncRequest(BaseModel):
    categories_motifs: Dict[str, CategorieData]


class InstitutionDocument(BaseModel):
    document_id: str
    title: str
    content: str
    document_type: str
    category: Optional[str] = None
    version: str = "1"
    source: str = "INSTITUTIONAL"
    status: str = "ACTIVE"
    validated: bool = False
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None


class InstitutionSyncRequest(BaseModel):
    documents: List[InstitutionDocument]


@router.post("/categories")
def sync_categories(
    request: CategoriesSyncRequest,
    x_correlation_id: Optional[str] = Header(default=None),
):
    """Synchronize the catalogue only when its content has changed."""
    indexed = vector_db.index_categories_motifs(request.categories_motifs)
    metadata = vector_db.categories_collection.metadata or {}
    correlation_id = x_correlation_id or str(uuid4())
    logger.info(
        "categories_sync correlation_id=%s indexed=%s catalog_hash=%s indexed_count=%s",
        correlation_id,
        indexed,
        metadata.get("catalog_hash"),
        vector_db.categories_collection.count(),
    )
    return {
        "status": "success",
        "correlation_id": correlation_id,
        "indexed": indexed,
        "catalog_hash": metadata.get("catalog_hash"),
        "indexed_count": vector_db.categories_collection.count(),
    }


@router.post("/institution")
def sync_institution(
    request: InstitutionSyncRequest,
    x_correlation_id: Optional[str] = Header(default=None),
):
    """Synchronize versioned institutional knowledge documents."""
    indexed = vector_db.index_institution_documents(request.documents)
    metadata = vector_db.institution_collection.metadata or {}
    correlation_id = x_correlation_id or str(uuid4())
    logger.info(
        "institution_sync correlation_id=%s indexed=%s documents_hash=%s indexed_count=%s",
        correlation_id,
        indexed,
        metadata.get("documents_hash"),
        vector_db.institution_collection.count(),
    )
    return {
        "status": "success",
        "correlation_id": correlation_id,
        "indexed": indexed,
        "documents_hash": metadata.get("documents_hash"),
        "indexed_count": vector_db.institution_collection.count(),
    }


@router.get("/status")
def sync_status(db: Session = Depends(get_db)):
    """Expose the persisted synchronisation and index state."""
    state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == "spring_boot_claims"
        )
    )
    sugg_state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == "spring_boot_suggestions"
        )
    )
    aff_state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == "spring_boot_affectations"
        )
    )
    ref_state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == "spring_boot_referentiels"
        )
    )
    sol_state = db.scalar(
        select(ReportingSyncState).where(
            ReportingSyncState.sync_name == "spring_boot_solutions"
        )
    )
    categories_metadata = vector_db.categories_collection.metadata or {}

    return {
        "referentiels": {
            "last_sync_at": ref_state.updated_at.isoformat() if ref_state else None,
            "received_count": ref_state.last_received_count if ref_state else 0,
            "inserted_count": ref_state.last_inserted_count if ref_state else 0,
            "updated_count": ref_state.last_updated_count if ref_state else 0,
            "last_started_at": ref_state.last_started_at.isoformat() if ref_state and ref_state.last_started_at else None,
            "last_completed_at": ref_state.last_completed_at.isoformat() if ref_state and ref_state.last_completed_at else None,
            "last_duration_ms": ref_state.last_duration_ms if ref_state else None,
            "error_count": ref_state.last_error_count if ref_state else 0,
            "last_error": ref_state.last_error if ref_state else None,
            "status": "healthy" if ref_state else "not_initialized",
        },
        "claims": {
            "last_sync_at": state.updated_at.isoformat() if state else None,
            "last_cursor": (
                state.last_successful_sync_at.isoformat()
                if state and state.last_successful_sync_at
                else None
            ),
            "indexed_count": vector_db.collection.count(),
            "received_count": state.last_received_count if state else 0,
            "inserted_count": state.last_inserted_count if state else 0,
            "updated_count": state.last_updated_count if state else 0,
            "ignored_count": state.last_ignored_count if state else 0,
            "deleted_count": state.last_deleted_count if state else 0,
            "last_indexed_count": state.last_indexed_count if state else 0,
            "last_started_at": state.last_started_at.isoformat() if state and state.last_started_at else None,
            "last_completed_at": state.last_completed_at.isoformat() if state and state.last_completed_at else None,
            "last_duration_ms": state.last_duration_ms if state else None,
            "error_count": state.last_error_count if state else 0,
            "last_error": state.last_error if state else None,
            "status": "healthy" if state else "not_initialized",
            "rag_sync_enabled": os.getenv(
                "REPORTING_ENABLE_RAG_SYNC", "false"
            ).lower()
            == "true",
        },
        "suggestions": {
            "last_sync_at": sugg_state.updated_at.isoformat() if sugg_state else None,
            "last_cursor": (
                sugg_state.last_successful_sync_at.isoformat()
                if sugg_state and sugg_state.last_successful_sync_at
                else None
            ),
            "received_count": sugg_state.last_received_count if sugg_state else 0,
            "inserted_count": sugg_state.last_inserted_count if sugg_state else 0,
            "updated_count": sugg_state.last_updated_count if sugg_state else 0,
            "ignored_count": sugg_state.last_ignored_count if sugg_state else 0,
            "deleted_count": sugg_state.last_deleted_count if sugg_state else 0,
            "last_started_at": sugg_state.last_started_at.isoformat() if sugg_state and sugg_state.last_started_at else None,
            "last_completed_at": sugg_state.last_completed_at.isoformat() if sugg_state and sugg_state.last_completed_at else None,
            "last_duration_ms": sugg_state.last_duration_ms if sugg_state else None,
            "error_count": sugg_state.last_error_count if sugg_state else 0,
            "last_error": sugg_state.last_error if sugg_state else None,
            "status": "healthy" if sugg_state else "not_initialized",
        },
        "affectations": {
            "last_sync_at": aff_state.updated_at.isoformat() if aff_state else None,
            "last_cursor": (
                aff_state.last_successful_sync_at.isoformat()
                if aff_state and aff_state.last_successful_sync_at
                else None
            ),
            "received_count": aff_state.last_received_count if aff_state else 0,
            "inserted_count": aff_state.last_inserted_count if aff_state else 0,
            "updated_count": aff_state.last_updated_count if aff_state else 0,
            "ignored_count": aff_state.last_ignored_count if aff_state else 0,
            "deleted_count": aff_state.last_deleted_count if aff_state else 0,
            "last_started_at": aff_state.last_started_at.isoformat() if aff_state and aff_state.last_started_at else None,
            "last_completed_at": aff_state.last_completed_at.isoformat() if aff_state and aff_state.last_completed_at else None,
            "last_duration_ms": aff_state.last_duration_ms if aff_state else None,
            "error_count": aff_state.last_error_count if aff_state else 0,
            "last_error": aff_state.last_error if aff_state else None,
            "status": "healthy" if aff_state else "not_initialized",
        },
        "solutions": {
            "last_sync_at": sol_state.updated_at.isoformat() if sol_state else None,
            "last_cursor": (
                sol_state.last_successful_sync_at.isoformat()
                if sol_state and sol_state.last_successful_sync_at
                else None
            ),
            "received_count": sol_state.last_received_count if sol_state else 0,
            "inserted_count": sol_state.last_inserted_count if sol_state else 0,
            "updated_count": sol_state.last_updated_count if sol_state else 0,
            "ignored_count": sol_state.last_ignored_count if sol_state else 0,
            "deleted_count": sol_state.last_deleted_count if sol_state else 0,
            "last_started_at": sol_state.last_started_at.isoformat() if sol_state and sol_state.last_started_at else None,
            "last_completed_at": sol_state.last_completed_at.isoformat() if sol_state and sol_state.last_completed_at else None,
            "last_duration_ms": sol_state.last_duration_ms if sol_state else None,
            "error_count": sol_state.last_error_count if sol_state else 0,
            "last_error": sol_state.last_error if sol_state else None,
            "status": "healthy" if sol_state else "not_initialized",
        },
        "categories": {
            "catalog_hash": categories_metadata.get("catalog_hash"),
            "indexed_count": vector_db.categories_collection.count(),
            "last_sync_at": categories_metadata.get("catalog_synced_at"),
            "status": (
                "healthy"
                if categories_metadata.get("catalog_hash")
                else "not_initialized"
            ),
        },
        "institution": {
            "documents_hash": (
                vector_db.institution_collection.metadata or {}
            ).get("documents_hash"),
            "indexed_count": vector_db.institution_collection.count(),
            "last_sync_at": (
                vector_db.institution_collection.metadata or {}
            ).get("documents_synced_at"),
            "status": (
                "healthy"
                if (
                    vector_db.institution_collection.metadata or {}
                ).get("documents_hash")
                else "not_initialized"
            ),
        },
    }
