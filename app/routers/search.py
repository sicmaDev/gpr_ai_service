from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
from app.services.vector_service import vector_db
from app.services.llm_service import generate_solution_from_history, generate_solution_from_history_stream

router = APIRouter(prefix="/search", tags=["RAG Search"])

class SearchRequest(BaseModel):
    texte_actuel: str
    categorie: Optional[str] = None
    motif: Optional[str] = None
    gravite_max: Optional[str] = None
    claimType: Optional[str] = None

@router.post("/")
def search_similar(request: SearchRequest):
    # 1. Recherche Sémantique Faiss
    results = vector_db.search_similar(
        query=request.texte_actuel,
        top_k=3,
        category_filter=request.categorie,
        motif_filter=request.motif,
        claim_type_filter=request.claimType
    )
    
    # 2. Génération de solution via LLM (Ollama)
    # Extraire uniquement les textes des solutions de l'historique pour le prompt
    historic_solutions_text = [res["solution_suggeree"] for res in results]
    
    # Si des résultats existent, on demande à Llama de rédiger une réponse
    generated_solution = "Aucune similarité trouvée."
    if historic_solutions_text:
        generated_solution = generate_solution_from_history(request.texte_actuel, historic_solutions_text)

    # 3. Réponse finale combinée (Génératif + Sources historiques)
    return {
        "message": generated_solution, # Solution générée pour la Section A du Front-end
        "resultats_trouves": len(results),
        "similar_claims": results      # Sources historiques pour la Section B du Front-end
    }

@router.post("/stream")
async def search_similar_stream(request: SearchRequest):
    print("=== REQUÊTE SEARCH REÇUE ===")
    print(f"Texte: {request.texte_actuel}")
    print(f"Categorie: {request.categorie}")
    print(f"Motif: {request.motif}")
    print("============================")
    # 1. Recherche Sémantique Faiss (Rapide)
    results = vector_db.search_similar(
        query=request.texte_actuel,
        top_k=3,
        category_filter=request.categorie,
        motif_filter=request.motif,
        claim_type_filter=request.claimType
    )
    
    historic_solutions_text = [res["solution_suggeree"] for res in results]
    
    def event_generator():
        # Envoyer d'abord les sources trouvées
        yield f"data: {json.dumps({'type': 'sources', 'similar_claims': results})}\n\n"
        
        if not historic_solutions_text:
            yield f"data: {json.dumps({'type': 'chunk', 'content': 'Aucune similarité trouvée dans l\'historique.'})}\n\n"
            yield f"data: {json.dumps({'type': 'final', 'content': 'Aucune similarité trouvée.'})}\n\n"
            return
            
        full_text = ""
        for chunk in generate_solution_from_history_stream(request.texte_actuel, historic_solutions_text):
            full_text += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
        yield f"data: {json.dumps({'type': 'final', 'content': full_text})}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")
