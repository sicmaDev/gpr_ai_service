from typing import Optional

from fastapi import APIRouter, Query

from app.services.vector_service import vector_db

router = APIRouter(prefix="/knowledge", tags=["Base de connaissances"])


@router.get("/search")
def search_institution_knowledge(
    query: str = Query(min_length=1),
    top_k: int = Query(default=5, ge=1, le=20),
    category: Optional[str] = None,
):
    """Retrieve active institutional context relevant to a query."""
    return {
        "query": query,
        "results": vector_db.search_institution_context(
            query=query,
            top_k=top_k,
            category=category,
        ),
    }
