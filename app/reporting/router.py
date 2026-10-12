import logging
from uuid import uuid4

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.reporting.catalog_manager import submit_user_feedback
from app.reporting.text_to_sql_contracts import UserFeedbackPayload
from .service import answer_query, build_dashboard
from .schemas import (
    DashboardResponse,
    ReportingFilters,
    ReportingQueryRequest,
    ReportingQueryResponse,
)
from .trace_logging import trace_info

router = APIRouter(prefix="/reporting", tags=["Reporting IA"])

logger = logging.getLogger(__name__)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Retourner le dashboard Reporting IA",
    description=(
        "Retourne les KPI, graphiques, risques, alertes et recommandations "
        "pour les reclamations et denonciations filtrees."
    ),
    responses={
        422: {"description": "Filtres invalides"},
    },
)
async def get_dashboard(
    start_date: date | None = Query(default=None, description="Date de debut incluse"),
    end_date: date | None = Query(default=None, description="Date de fin incluse"),
    claim_type: str | None = Query(default=None),
    agency: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    category: str | None = Query(default=None),
    product: str | None = Query(default=None),
    team: str | None = Query(default=None),
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    filters = ReportingFilters(
        start_date=start_date,
        end_date=end_date,
        claim_type=claim_type,
        agency=agency,
        channel=channel,
        category=category,
        product=product,
        team=team,
        status=status,
        risk_level=risk_level,
    )
    return build_dashboard(db, filters)


@router.post(
    "/query",
    response_model=ReportingQueryResponse,
    summary="Interroger le reporting en langage naturel",
    description=(
        "Analyse une question, valide son intention puis retournera une "
        "reponse et une visualisation compatibles avec le front React."
    ),
    responses={
        422: {"description": "Question ou filtres invalides"},
    },
)
async def query_reporting(
    request: ReportingQueryRequest,
    db: Session = Depends(get_db),
):
    trace_id = uuid4().hex[:12]
    trace_info(
        logger,
        trace_id,
        "reporting.http.received",
        method="POST",
        path="/reporting/query",
    )
    response = answer_query(db, request.question, request.filters, trace_id)
    if response.summary in {"Analyse non supportee", "Analyse non supportée"}:

        trace_info(
            logger,
            trace_id,
            "reporting.http.completed",
            status=422,
            visualization=False,
            comparison=False,
        )
        raise HTTPException(status_code=422, detail=response.answer)
    trace_info(
        logger,
        trace_id,
        "reporting.http.completed",
        status=200,
        visualization=response.visualization is not None,
        comparison=response.comparison is not None,
    )
    return response


@router.post(
    "/feedback",
    summary="Soumettre un retour utilisateur sur une requête analytique",
    description=(
        "Permet à un utilisateur habilité de valider une requête ou de signaler une "
        "incohérence par son identifiant unique query_id. Un signalement négatif retire "
        "immédiatement la requête du circuit Fast-Path et crée un anti-pattern d'apprentissage."
    ),
    responses={
        404: {"description": "Requête introuvable dans le catalogue"},
        422: {"description": "Format de feedback invalide"},
    },
)
async def post_user_feedback(
    feedback: UserFeedbackPayload,
):
    try:
        updated_entry = submit_user_feedback(feedback)
        return {
            "status": "success",
            "query_id": updated_entry.id,
            "approval_status": updated_entry.status.value,
            "message": (
                "Feedback positif pris en compte."
                if feedback.is_positive
                else "Signalement enregistré. La requête a été invalidée du circuit rapide."
            ),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

