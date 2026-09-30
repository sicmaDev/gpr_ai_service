from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
from app.services.nlp_service import analyze_sentiment_and_urgency, generate_short_summary, analyze_sentiment_and_urgency_stream

router = APIRouter(prefix="/analyze", tags=["NLP Analysis"])

class MotifData(BaseModel):
    libelle: str
    description: Optional[str] = None
    gravite: Optional[str] = None

class CategorieData(BaseModel):
    description: Optional[str] = None
    motifs: List[MotifData]

class TextRequest(BaseModel):
    texte: str
    categories_motifs: Optional[Dict[str, CategorieData]] = None
    nature_dossier: Optional[str] = "RECLAMATION"
    definition_nature: Optional[str] = ""

import logging
from uuid import uuid4
logger = logging.getLogger(__name__)

@router.post("/")
async def analyze_text(request: TextRequest, x_correlation_id: Optional[str] = Header(default=None)):
    # Appel de la logique du service NLP avec les listes de données réelles
    texte = request.texte
    correlation_id = x_correlation_id or str(uuid4())
    logger.info("--- NOUVELLE ANALYSE correlation_id=%s ---", correlation_id)
    logger.info(f"Texte : {texte[:100]}...")
    
    result = analyze_sentiment_and_urgency(
        texte, 
        request.categories_motifs,
        request.nature_dossier,
        request.definition_nature
    )
    
    # Si le résultat a été mis à jour pour renvoyer le raisonnement ou non
    if len(result) == 5:
        gravity, sentiment, mots_cles, suggested_cat, suggested_motif = result
        raisonnement = "Aucune explication"
    else:
        gravity, sentiment, mots_cles, suggested_cat, suggested_motif, raisonnement = result
        
    resume = generate_short_summary(texte)
    
    logger.info(f"Résultats IA : Gravité={gravity}, Sentiment={sentiment}, Catégorie={suggested_cat}, Motif={suggested_motif}")
    
    return {
        "urgence": gravity, 
        "sentiment": sentiment,
        "mots_cles_detectes": mots_cles,
        "resume": resume,
        "categorie_suggeree": suggested_cat,
        "motif_suggere": suggested_motif,
        "raisonnement": raisonnement,
        "correlation_id": correlation_id
    }

@router.post("/stream")
async def analyze_text_stream(request: TextRequest, x_correlation_id: Optional[str] = Header(default=None)):
    texte = request.texte
    correlation_id = x_correlation_id or str(uuid4())
    logger.info(f"--- NOUVELLE ANALYSE STREAM ---")
    logger.info(f"Texte : {texte[:100]}...")
    
    # categories_motifs peut être un dict d'objets CategorieData qu'il faut convertir en dict pur si nécessaire
    # Pydantic convertit request.categories_motifs en dict d'objets CategorieData
    # Assurons-nous de passer un dictionnaire pur si attendu par nlp_service / llm_service
    cat_dict = None
    if request.categories_motifs:
        cat_dict = {k: v.dict() for k, v in request.categories_motifs.items()}
        
    def event_generator():
        yield f"data: {json.dumps({'type': 'correlation', 'correlation_id': correlation_id})}\n\n"
        for event in analyze_sentiment_and_urgency_stream(texte, cat_dict, request.nature_dossier, request.definition_nature):
            event["correlation_id"] = correlation_id
            yield f"data: {json.dumps(event)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
