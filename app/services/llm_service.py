import os
import re
import json
import logging
from dotenv import load_dotenv
from ollama import Client
from app.services.vector_service import vector_db

load_dotenv()

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
DEFAULT_MODEL = os.getenv("LLM_MODEL_NAME", "")

headers = {}
if LLM_API_KEY:
    headers["Authorization"] = f"Bearer {LLM_API_KEY}"

# Création du client Ollama (Local ou Cloud)
ollama_client = Client(host=LLM_BASE_URL, headers=headers)

def generate_solution_from_history(current_complaint_text: str, similar_historic_solutions: list) -> str:
    """
    Génère 3 propositions de solutions formatées en se basant sur la plainte actuelle
    et un échantillon des meilleures solutions passées.
    """
    if not similar_historic_solutions:
        return "Aucune solution historique trouvée pour formuler une recommandation."

    # 1. Construction du contexte (Les solutions passées)
    context_text = "\n".join([f"- Historique {i+1} : {sol}" for i, sol in enumerate(similar_historic_solutions)])

    # 2. Construction du Prompt Système (Les instructions strictes pour l'IA)
    system_prompt = """
    Tu es un assistant expert pour le service client de GPR (Gestion des Réclamations).
    Ton rôle est d'analyser une plainte actuelle et les solutions historiques fournies.
    Tu dois rédiger EXACTEMENT 3 propositions distinctes, numérotées 1, 2 et 3.
    Chaque proposition doit être composée d'une SOLUTION (ce qu'on fait) et d'un COMMENTAIRE court (justification pour l'agent), séparés par le caractère '|'.
    
    Règles strictes :
    - Propose 3 options variées basées sur les données fournies.
    - Format par ligne : "N. [Solution] | [Commentaire]"
    - Reste courtois et professionnel (vouvoiement).
    - Ne mentionne pas que tu es une IA.
    - Exemple : "1. Rembourser les frais | Le client a été débité deux fois par erreur."
    """

    # 3. Construction de la requête utilisateur (La tâche)
    user_prompt = f"""
    Plainte actuelle du client :
    "{current_complaint_text}"

    Voici comment des plaintes similaires ont été résolues par nos agents par le passé :
    {context_text}

    Rédige maintenant les 3 propositions (Solution | Commentaire) idéales pour cette plainte.
    """

    try:
        logger.info(f"Appel au modèle LLM local '{DEFAULT_MODEL}' via Ollama...")
        
        response = ollama_client.chat(model=DEFAULT_MODEL, messages=[
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ], options={'temperature': 0})
        
        generated_text = response['message']['content']
        logger.info("Génération LLM réussie.")
        return generated_text.strip()

    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Ollama : {e}")
        return "Erreur : Impossible de générer une solution. Veuillez vérifier que Ollama est bien lancé en arrière-plan."

def generate_solution_from_history_stream(current_complaint_text: str, similar_historic_solutions: list):
    """
    Génère 3 propositions de solutions en stream.
    Yields chunks de texte.
    """
    if not similar_historic_solutions:
        yield "Aucune solution historique trouvée pour formuler une recommandation."
        return

    context_text = "\n".join([f"- Historique {i+1} : {sol}" for i, sol in enumerate(similar_historic_solutions)])

    system_prompt = """
    Tu es un assistant expert pour le service client de GPR (Gestion des Réclamations).
    Ton rôle est d'analyser une plainte actuelle et les solutions historiques fournies.
    
    Règles strictes :
    - Rédige d'abord une courte analyse (raisonnement) en 1 ou 2 phrases de la situation, préfixée EXACTEMENT par "RAISONNEMENT :".
    - Ensuite, propose EXACTEMENT 3 options variées basées sur les données fournies, numérotées 1, 2 et 3.
    - Format par ligne pour chaque proposition : "N. [Solution] | [Commentaire]"
    - Reste courtois et professionnel (vouvoiement).
    - Ne mentionne pas que tu es une IA.
    
    Exemple de réponse attendue :
    RAISONNEMENT : Le client a subi un prélèvement injustifié suite à une erreur technique du système. Les solutions historiques privilégient un remboursement rapide.
    1. Rembourser les frais | Le client a été débité deux fois par erreur.
    2. ...
    """

    user_prompt = f"""
    Plainte actuelle du client :
    "{current_complaint_text}"

    Voici comment des plaintes similaires ont été résolues par nos agents par le passé :
    {context_text}

    Rédige maintenant les 3 propositions (Solution | Commentaire) idéales pour cette plainte.
    """

    try:
        logger.info(f"Appel au modèle LLM local '{DEFAULT_MODEL}' via Ollama en STREAM...")
        
        response_stream = ollama_client.chat(model=DEFAULT_MODEL, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ], options={'temperature': 0}, stream=True)
        
        for chunk in response_stream:
            content = chunk['message'].get('content', '')
            if content:
                yield content

    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Ollama stream : {e}")
        yield f"Erreur de génération : {e}"

def _build_tree_text(categories_motifs: dict) -> str:
    if not categories_motifs:
        return ""
    tree_text = ""
    for cat_name, cat_data in categories_motifs.items():
        cat_desc = ""
        motifs = []
        if hasattr(cat_data, "description"):
            cat_desc = cat_data.description
            motifs = cat_data.motifs
        elif isinstance(cat_data, dict):
            cat_desc = cat_data.get("description", "")
            motifs = cat_data.get("motifs", [])
            
        desc_text = f" (Description: {cat_desc})" if cat_desc else ""
        tree_text += f"- Catégorie '{cat_name}'{desc_text} contient les motifs suivants :\n"
        
        for motif in motifs:
            m_libelle = ""
            m_desc = ""
            m_gravite = ""
            if hasattr(motif, "libelle"):
                m_libelle = motif.libelle
                m_desc = motif.description
                m_gravite = motif.gravite
            elif isinstance(motif, dict):
                m_libelle = motif.get("libelle", "")
                m_desc = motif.get("description", "")
                m_gravite = motif.get("gravite", "")
                
            details = []
            if m_desc: details.append(f"Description: {m_desc}")
            if m_gravite: details.append(f"Gravité: {m_gravite}")
            
            details_text = f" -> {', '.join(details)}" if details else ""
            tree_text += f"    * Motif: '{m_libelle}'{details_text}\n"
    return tree_text

def check_urgency_with_llm(text: str, categories_motifs: dict = None, nature_dossier: str = 'RECLAMATION', definition_nature: str = '') -> str:
    """
    Demande rapidement à Llama si la plainte nécessite un traitement urgent (GRAVE, MOYEN ou MINEUR).
    """
    system_prompt = """
    Tu es un assistant expert pour le service client d'une institution financière.
    Ton rôle est d'analyser la plainte d'un client et d'évaluer son niveau d'urgence afin d'aider l'agent à prioriser le traitement.
    
    Règles :
    - Répond UNIQUEMENT avec un objet JSON valide.
    - L'urgence doit être EXACTEMENT : GRAVE, MOYEN ou MINEUR.
    - Pour comprendre ce que l'institution considère comme GRAVE, MOYEN ou MINEUR, réfère-toi aux descriptions et aux niveaux de gravité des catégories/motifs fournis dans le contexte.
    - Rédige d'abord une courte 'analyse_du_probleme' (1 phrase) expliquant ton choix avant de donner l'urgence.
    """
    
    tree_text = _build_tree_text(categories_motifs) if categories_motifs else ""
    
    user_prompt = f"""
    Nature du dossier : '{nature_dossier}'
    Définition de cette nature : '{definition_nature}'
    Texte soumis : '{text}'
    
    Contexte de l'institution (Catégories, Motifs et Gravité) :
    {tree_text}
    
    Format de réponse attendu : {{"analyse_du_probleme": "...", "urgence": "..."}}
    """
    
    try:
        logger.info("\n--- SYSTEM PROMPT (Urgence) ---")
        logger.info(system_prompt.strip())
        logger.info("--- USER PROMPT (Urgence) ---")
        logger.info(user_prompt.strip())
        
        response = ollama_client.chat(
            model=DEFAULT_MODEL, 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            format='json',
            options={'temperature': 0}
        )
        raw_content = response['message']['content']
        result_json = json.loads(raw_content)
        
        urgence = result_json.get("urgence", "MINEUR").strip().upper()
        raisonnement = result_json.get("analyse_du_probleme", "Aucune explication")
        
        logger.info(f"Urgence LLM : {urgence} | Raisonnement : {raisonnement}")
        
        if "GRAVE" in urgence: return "GRAVE"
        if "MOYEN" in urgence: return "MOYEN"
        return "MINEUR"
    except Exception as e:
        logger.error(f"Erreur urgence LLM : {e}")
        return "MINEUR"

def classify_with_llm(text: str, categories_motifs: dict, nature_dossier: str = 'RECLAMATION', definition_nature: str = '') -> dict:
    """
    Classification stricte via LLM avec température 0 et hiérarchie conservée.
    """
    system_prompt = """
    Tu es un assistant expert pour le service client d'une institution financière.
    Ton rôle est d'analyser la plainte d'un client et de la classifier automatiquement pour aider l'agent.
    Tu dois choisir la CATÉGORIE principale et le MOTIF spécifique le plus approprié à la situation.
    Attention : Un MOTIF appartient toujours à une CATÉGORIE précise. Tu dois respecter cette hiérarchie.
    
    Règles Strictes :
    - Tu dois lire et comparer la plainte avec TOUS les motifs disponibles (leurs descriptions et leur niveau de gravité) avant de faire ton choix.
    - Si la plainte ne correspond à aucune des catégories et motifs listés dans le contexte, ou s'il s'agit d'une demande hors sujet, tu dois impérativement renvoyer "AUTRE" pour la category et "AUTRE" pour le motif.
    - Répond UNIQUEMENT avec un objet JSON valide.
    - Rédige d'abord une courte 'analyse_du_probleme' (1 ou 2 phrases expliquant pourquoi tu choisis ce motif plutôt qu'un autre, ou pourquoi la plainte est classée en AUTRE si aucun motif ne correspond) avant de donner ton choix final.
    """
    
    tree_text = _build_tree_text(categories_motifs)
        
    user_prompt = f"""
    Nature du dossier : '{nature_dossier}'
    Définition de cette nature : '{definition_nature}'
    Texte soumis : "{text}"
    
    Hiérarchie des Catégories et Motifs disponibles :
    {tree_text}
    
    Format de réponse attendu : {{"analyse_du_probleme": "...", "category": "...", "motif": "..."}}
    """
    
    try:
        logger.info("\n--- SYSTEM PROMPT (Classification) ---")
        logger.info(system_prompt.strip())
        logger.info("--- USER PROMPT (Classification) ---")
        logger.info(user_prompt.strip())
        
        response = ollama_client.chat(
            model=DEFAULT_MODEL, 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ], 
            format='json',
            options={'temperature': 0}
        )
        
        raw_content = response['message']['content']
        raw_json = json.loads(raw_content)
        
        cat = raw_json.get('category') or raw_json.get('Category') or raw_json.get('catégorie') or raw_json.get('Categorie') or 'AUTRE'
        mot = raw_json.get('motif') or raw_json.get('Motif') or 'AUTRE'
        raison = raw_json.get('analyse_du_probleme') or raw_json.get('analyse') or raw_json.get('raisonnement') or 'Aucune explication'
        
        result = {"category": cat, "motif": mot, "raisonnement": raison}
        logger.info(f"Classification LLM : {result.get('category')} > {result.get('motif')} | Raisonnement : {result.get('raisonnement', 'Aucune explication')}")
        return result
    except Exception as e:
        logger.error(f"Erreur classification LLM : {e}")
        return {"category": "AUTRE", "motif": "AUTRE"}

def classify_with_llm_stream(text: str, categories_motifs: dict, nature_dossier: str = 'RECLAMATION', definition_nature: str = ''):
    """
    Classification via LLM en mode streaming pour renvoyer le raisonnement au fur et à mesure.
    """
    system_prompt = """
    Tu es un assistant expert pour le service client d'une institution financière.
    Ton rôle est d'analyser la plainte d'un client et de la classifier automatiquement pour aider l'agent.
    Tu dois choisir la CATÉGORIE principale et le MOTIF spécifique le plus approprié à la situation.
    Attention : Un MOTIF appartient toujours à une CATÉGORIE précise. Tu dois respecter cette hiérarchie.
    
    Règles Strictes :
    - Tu dois lire et comparer la plainte avec TOUS les motifs disponibles (leurs descriptions et leur niveau de gravité) avant de faire ton choix.
    - Si la plainte ne correspond à aucune des catégories et motifs listés dans le contexte, ou s'il s'agit d'une demande hors sujet, tu dois impérativement renvoyer "AUTRE" pour la category et "AUTRE" pour le motif.
    - Répond UNIQUEMENT avec un objet JSON valide.
    - Rédige d'abord une courte 'analyse_du_probleme' (1 ou 2 phrases expliquant pourquoi tu choisis ce motif plutôt qu'un autre, ou pourquoi la plainte est classée en AUTRE si aucun motif ne correspond) avant de donner ton choix final.
    """
    
    # --- RAG : Vectorisation et filtrage sémantique ---
    # 1. Mise à jour de l'index avec toutes les catégories reçues du frontend
    vector_db.index_categories_motifs(categories_motifs)
    # 2. Recherche sémantique du Top 15 des éléments pertinents par rapport au texte de la plainte
    filtered_categories_motifs, top_matches = vector_db.search_relevant_motifs(text, categories_motifs, top_k=15)
    # 3. On génère le texte de l'arbre uniquement pour les catégories retenues
    tree_text = _build_tree_text(filtered_categories_motifs if filtered_categories_motifs else categories_motifs)
    
    yield {"type": "rag_matches", "matches": top_matches}
    yield {"type": "rag_context", "categories": list(filtered_categories_motifs.keys()) if filtered_categories_motifs else list(categories_motifs.keys())}
        
    user_prompt = f"""
    Nature du dossier : '{nature_dossier}'
    Définition de cette nature : '{definition_nature}'
    Texte soumis : "{text}"
    
    Hiérarchie des Catégories et Motifs disponibles :
    {tree_text}
    
    Format de réponse attendu : {{"analyse_du_probleme": "...", "category": "...", "motif": "..."}}
    """
    
    try:
        logger.info("\n--- SYSTEM PROMPT (Classification Stream) ---")
        logger.info(system_prompt.strip())
        logger.info("--- USER PROMPT (Classification Stream) ---")
        logger.info(user_prompt.strip())
        
        response = ollama_client.chat(
            model=DEFAULT_MODEL, 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ], 
            format='json',
            options={'temperature': 0},
            stream=True
        )
        
        buffer = ""
        state = 0 # 0: waiting for start of raisonnement, 1: inside raisonnement, 2: after raisonnement
        last_yielded_len = 0
        
        # Regex robuste (insensible à la casse) pour attraper la clé d'analyse
        regex_start = re.compile(r'"(?:analyse_du_probleme|analyse|raisonnement)"\s*:\s*"', re.IGNORECASE)
        
        for chunk in response:
            content = chunk['message'].get('content', '')
            buffer += content
            
            if state == 0:
                match = regex_start.search(buffer)
                if match:
                    state = 1
                    start_idx = match.end()
                    val_str = buffer[start_idx:]
                    end_match = re.search(r'(?<!\\)"', val_str)
                    if end_match:
                        clean_text = val_str[:end_match.start()]
                        if clean_text:
                            yield {"type": "raisonnement_chunk", "content": clean_text}
                        last_yielded_len = len(clean_text)
                        state = 2
                    else:
                        if val_str:
                            yield {"type": "raisonnement_chunk", "content": val_str}
                        last_yielded_len = len(val_str)
            elif state == 1:
                match = regex_start.search(buffer)
                start_idx = match.end()
                val_str = buffer[start_idx:]
                end_match = re.search(r'(?<!\\)"', val_str)
                if end_match:
                    clean_text = val_str[:end_match.start()]
                    new_part = clean_text[last_yielded_len:]
                    if new_part:
                        yield {"type": "raisonnement_chunk", "content": new_part}
                    state = 2
                else:
                    new_part = val_str[last_yielded_len:]
                    if new_part:
                        yield {"type": "raisonnement_chunk", "content": new_part}
                        last_yielded_len = len(val_str)
            elif state == 2:
                pass
                
        try:
            result = json.loads(buffer)
            # Extraction robuste avec fallbacks pour gérer la sensibilité à la casse (LLaMa3 1B)
            cat = result.get('category') or result.get('Category') or result.get('catégorie') or result.get('Categorie') or 'AUTRE'
            mot = result.get('motif') or result.get('Motif') or 'AUTRE'
            raison = result.get('analyse_du_probleme') or result.get('analyse') or result.get('raisonnement') or 'Aucune explication'
            
            yield {"type": "final", "result": {"category": cat, "motif": mot, "raisonnement": raison}}
        except Exception as e:
            logger.error(f"Erreur parsing JSON final stream : {e}")
            yield {"type": "final", "result": {"category": "AUTRE", "motif": "AUTRE", "raisonnement": "Erreur de flux"}}
            
    except Exception as e:
        logger.error(f"Erreur classification LLM Stream : {e}")
        yield {"type": "final", "result": {"category": "AUTRE", "motif": "AUTRE", "raisonnement": "Erreur LLM"}}

def check_urgency_with_llm_stream(text: str, categories_motifs: dict, nature_dossier: str = 'RECLAMATION', definition_nature: str = ''):
    """
    Calcul d'urgence via LLM en mode streaming pour renvoyer le raisonnement au fur et à mesure.
    """
    system_prompt = """
    Tu es un assistant expert pour le service client d'une institution financière.
    Ton rôle est d'analyser la plainte d'un client et d'évaluer son niveau d'urgence afin d'aider l'agent à prioriser le traitement.
    
    Règles :
    - Répond UNIQUEMENT avec un objet JSON valide.
    - L'urgence doit être EXACTEMENT : GRAVE, MOYEN ou MINEUR.
    - Pour comprendre ce que l'institution considère comme GRAVE, MOYEN ou MINEUR, réfère-toi aux descriptions et aux niveaux de gravité des catégories/motifs fournis dans le contexte.
    - Rédige d'abord une courte 'analyse_du_probleme' (1 phrase) expliquant ton choix avant de donner l'urgence.
    """
    
    # --- RAG : Vectorisation et filtrage sémantique ---
    if categories_motifs:
        vector_db.index_categories_motifs(categories_motifs)
        filtered_categories_motifs, top_matches = vector_db.search_relevant_motifs(text, categories_motifs, top_k=15)
        tree_text = _build_tree_text(filtered_categories_motifs if filtered_categories_motifs else categories_motifs)
    else:
        tree_text = ""
    
    user_prompt = f"""
    Nature du dossier : '{nature_dossier}'
    Définition de cette nature : '{definition_nature}'
    Texte soumis : '{text}'
    
    Contexte de l'institution (Catégories, Motifs et Gravité) :
    {tree_text}
    
    Format de réponse attendu : {{"analyse_du_probleme": "...", "urgence": "..."}}
    """
    
    try:
        logger.info("\n--- SYSTEM PROMPT (Urgence Stream) ---")
        logger.info(system_prompt.strip())
        logger.info("--- USER PROMPT (Urgence Stream) ---")
        logger.info(user_prompt.strip())
        
        response = ollama_client.chat(
            model=DEFAULT_MODEL, 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            format='json',
            options={'temperature': 0},
            stream=True
        )
        
        buffer = ""
        state = 0
        last_yielded_len = 0
        
        regex_start = re.compile(r'"(?:analyse_du_probleme|analyse|raisonnement)"\s*:\s*"', re.IGNORECASE)
        
        for chunk in response:
            content = chunk['message']['content']
            buffer += content
            
            if state == 0:
                match = regex_start.search(buffer)
                if match:
                    state = 1
                    start_idx = match.end()
                    val_str = buffer[start_idx:]
                    end_match = re.search(r'(?<!\\)"', val_str)
                    if end_match:
                        clean_text = val_str[:end_match.start()]
                        if clean_text:
                            yield {"type": "raisonnement_urgence_chunk", "content": clean_text}
                        last_yielded_len = len(clean_text)
                        state = 2
                    else:
                        if val_str:
                            yield {"type": "raisonnement_urgence_chunk", "content": val_str}
                        last_yielded_len = len(val_str)
            elif state == 1:
                match = regex_start.search(buffer)
                start_idx = match.end()
                val_str = buffer[start_idx:]
                end_match = re.search(r'(?<!\\)"', val_str)
                if end_match:
                    clean_text = val_str[:end_match.start()]
                    new_part = clean_text[last_yielded_len:]
                    if new_part:
                        yield {"type": "raisonnement_urgence_chunk", "content": new_part}
                    state = 2
                else:
                    new_part = val_str[last_yielded_len:]
                    if new_part:
                        yield {"type": "raisonnement_urgence_chunk", "content": new_part}
                        last_yielded_len = len(val_str)
            elif state == 2:
                pass
                
        try:
            result_json = json.loads(buffer)
            urgence = result_json.get("urgence", "MINEUR").strip().upper()
            raisonnement = result_json.get("analyse_du_probleme", "Aucune explication")
            if "GRAVE" in urgence: urgence_final = "GRAVE"
            elif "MOYEN" in urgence: urgence_final = "MOYEN"
            else: urgence_final = "MINEUR"
            yield {"type": "urgence_final", "urgence": urgence_final, "raisonnement": raisonnement}
        except Exception as e:
            logger.error(f"Erreur parsing JSON final urgence stream : {e}")
            yield {"type": "urgence_final", "urgence": "MINEUR", "raisonnement": "Erreur de flux urgence"}
            
    except Exception as e:
        logger.error(f"Erreur urgence LLM Stream : {e}")
        yield {"type": "urgence_final", "urgence": "MINEUR", "raisonnement": "Erreur LLM urgence"}