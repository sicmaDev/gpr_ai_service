from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging
from app.services.reporting_service import nl_query_to_chart, generate_insights

router = APIRouter(prefix="/reporting", tags=["Reporting & Analyse"])
logger = logging.getLogger(__name__)

class NLQueryRequest(BaseModel):
    query: str

class InsightsRequest(BaseModel):
    days: Optional[int] = 30

@router.post("/nl-query")
async def handle_nl_query(request: NLQueryRequest):
    """
    Transforme une question en langage naturel en une configuration de graphique ECharts.
    """
    logger.info(f"--- REQUÊTE NATURELLE REPORTING ---")
    logger.info(f"Question: {request.query}")
    
    chart_config = nl_query_to_chart(request.query)
    
    return {
        "status": "success",
        "chart_config": chart_config
    }

@router.post("/insights")
async def handle_insights(request: InsightsRequest):
    """
    Génère des recommandations stratégiques et des alertes basées sur les réclamations récentes.
    """
    logger.info(f"--- GÉNÉRATION INSIGHTS ---")
    logger.info(f"Période: {request.days} jours")
    
    insights = generate_insights(days=request.days)
    
    return {
        "status": "success",
        "data": insights
    }
