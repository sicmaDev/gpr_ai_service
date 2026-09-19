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
    categories_metadata = vector_db.categories_collection.metadata or {}

    return {
        "claims": {
            "last_sync_at": state.updated_at.isoformat() if state else None,
            "last_cursor": (
                state.last_successful_sync_at.isoformat()
                if state and state.last_successful_sync_at
                else None
            ),
            "indexed_count": vector_db.collection.count(),
            "status": "healthy" if state else "not_initialized",
            "rag_sync_enabled": os.getenv(
                "REPORTING_ENABLE_RAG_SYNC", "false"
            ).lower()
            == "true",
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
