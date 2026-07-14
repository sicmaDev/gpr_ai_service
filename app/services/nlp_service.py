import re
import logging
from textblob import TextBlob
from app.services.llm_service import check_urgency_with_llm, classify_with_llm, classify_with_llm_stream, check_urgency_with_llm_stream

logger = logging.getLogger(__name__)

# Service d'analyse NLP

# Dictionnaire de mots sensibles métier qui rehaussent automatiquement l'urgence
MOTS_SENSIBLES = [
    "fraude", "arnaque", "piratage", "vol", "police", "tribunal",
    "avocat", "presse", "bceao", "cima", "médiateur", "huissier",
    "inadmissible", "honte", "urgence", "plainte", "scandale",
    "bloquer", "bloqué", "perdu", "perte"
]

# Mapping Catégories suggérées basées sur les mots-clés
MAPPING_CATEGORIES = {
    "FINANCIER": ["argent", "sous", "fcfa", "euro", "virement", "frais", "commission", "solde", "compte"],
    "TECHNIQUE": ["dab", "distributeur", "carte", "code", "pin", "lent", "bloqué", "machine", "guichet"],
    "RELATIONNEL": ["accueil", "gentil", "attente", "reçu", "bonjour", "agent", "chef", "politesse"]
}

def analyze_sentiment_and_urgency(text: str, categories_motifs: dict = None, nature_dossier: str = "RECLAMATION", definition_nature: str = "") -> tuple[str, str, list[str], str, str, str]:
    """
    Analyse le texte pour déterminer le niveau de gravité,
    une tonalité globale, les mots sensibles et la catégorie suggérée.
    """
    text_lower = text.lower()
    
    # 1. Détection des mots-clés métier
    detected_keywords = []
    for mot in MOTS_SENSIBLES:
        pattern = rf"\b{mot}(é|ée|er|es|s)?\b"
        if re.search(pattern, text_lower):
            detected_keywords.append(mot)
    
    # 2. Analyse basique du sentiment
    mots_colere = ["honte", "scandale", "inadmissible", "voleur", "arnaqueur", "inacceptable"]
    has_anger = any(m in text_lower for m in mots_colere)
    
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    sentiment = "neutre"
    if polarity < -0.3 or has_anger:
        sentiment = "tres_negatif"
    elif polarity < 0:
        sentiment = "negatif"
    
    # 3. Règles de calcul du niveau d'urgence
    # On laisse l'IA décider de l'urgence grâce au Chain of Thought, sauf si le texte est trop court
    gravity = "MINEUR"
    
    if len(text.split()) > 4:
        gravity = check_urgency_with_llm(text, categories_motifs, nature_dossier, definition_nature)
    else:
        # Fallback basique par mots-clés si le texte est très court
        mots_critiques = ["fraude", "vol", "police", "avocat", "tribunal", "bceao", "bloquer", "bloqué", "perte", "piratage"]
        has_critical_word = any(mot in text_lower for mot in mots_critiques)
        if has_critical_word:
            gravity = "GRAVE"
        elif len(detected_keywords) >= 2 or polarity <= -0.5 or has_anger or text.count('!') >= 2:
            gravity = "MOYEN"
        else:
            gravity = "MINEUR"
        
    # 4. Suggestion de catégorie et motif (Bug 6 + Données réelles)
    suggested_cat = "AUTRE"
    suggested_motif = "AUTRE"

    raisonnement_classification = "Aucune explication"
    
    if categories_motifs:
        logger.info(f"Début de la classification LLM ({len(categories_motifs)} catégories fournies avec leurs motifs)")
        llm_result = classify_with_llm(text, categories_motifs, nature_dossier, definition_nature)
        suggested_cat = llm_result.get("category", "AUTRE")
        suggested_motif = llm_result.get("motif", "AUTRE")
        raisonnement_classification = llm_result.get("raisonnement", "Aucune explication")
        logger.info(f"Classification LLM réussie : {suggested_cat} > {suggested_motif}")
    else:
        logger.warning("Aucune liste de catégories ou motifs fournie pour la classification LLM")
        # Fallback sur le mapping par mots-clés si aucune liste n'est fournie
        max_matches = 0
        for cat, keywords in MAPPING_CATEGORIES.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                suggested_cat = cat
        
    return gravity, sentiment, detected_keywords, suggested_cat, suggested_motif, raisonnement_classification

def generate_short_summary(text: str) -> str:
    sentences = text.split('.')
    if len(sentences) > 2:
        return f"{sentences[0].strip()}. [...] {sentences[-2].strip()}."
    return text[:200] + ("..." if len(text)>200 else "")

def analyze_sentiment_and_urgency_stream(text: str, categories_motifs: dict = None, nature_dossier: str = "RECLAMATION", definition_nature: str = ""):
    text_lower = text.lower()
    
    # 1. Détection des mots-clés
    detected_keywords = [word for word in MOTS_SENSIBLES if word in text_lower]
    
    # 2. Analyse basique du sentiment
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity < -0.4:
        sentiment = "tres_negatif"
    elif polarity < 0:
        sentiment = "negatif"
    elif polarity > 0.3:
        sentiment = "positif"
    else:
        sentiment = "neutre"
        
    # 3. Résumé
    resume = generate_short_summary(text)
    
    # Envoi de l'événement d'initialisation de base
    yield {"type": "init_base", "sentiment": sentiment, "mots_cles_detectes": detected_keywords, "resume": resume}
    
    # 4. Streaming du calcul d'urgence
    logger.info("Début du calcul d'urgence LLM Stream")
    gravity = "MINEUR"
    if categories_motifs:
        for event in check_urgency_with_llm_stream(text, categories_motifs, nature_dossier, definition_nature):
            if event["type"] == "urgence_final":
                gravity = event["urgence"]
                yield {"type": "init_urgence", "urgence": gravity, "raisonnement_urgence": event["raisonnement"]}
            else:
                yield event
    else:
        gravity = check_urgency_with_llm(text, categories_motifs, nature_dossier, definition_nature)
        yield {"type": "init_urgence", "urgence": gravity, "raisonnement_urgence": "Calcul d'urgence par défaut"}
    
    # 5. Streaming du raisonnement et de la classification finale
    if categories_motifs:
        logger.info(f"Début de la classification LLM Stream ({len(categories_motifs)} catégories fournies)")
        for event in classify_with_llm_stream(text, categories_motifs, nature_dossier, definition_nature):
            yield event
    else:
        logger.warning("Aucune liste de catégories ou motifs fournie pour la classification LLM Stream")
        suggested_cat = "AUTRE"
        max_matches = 0
        for cat, keywords in MAPPING_CATEGORIES.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                suggested_cat = cat
        yield {"type": "final", "result": {"category": suggested_cat, "motif": "AUTRE", "raisonnement": "Classification par mots-clés par défaut"}}
