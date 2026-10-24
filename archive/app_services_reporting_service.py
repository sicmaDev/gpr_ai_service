import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from app.services.llm_service import ollama_client, DEFAULT_MODEL
from app.services.vector_service import vector_db
from app.models.schema import get_schema_for_prompt, validate_and_correct_llm_output, populate_allowed_values_from_db

logger = logging.getLogger(__name__)

def parse_llm_json(content: str) -> dict:
    """Tente de parser le JSON retourné par le LLM de manière robuste."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                return json.loads(content[start:end+1])
        except Exception:
            pass
    return None

def nl_query_to_chart(query: str) -> dict:
    """
    1. Demande au LLM de comprendre la question (filtres, dimension de groupement).
    2. Récupère les métadonnées depuis ChromaDB.
    3. Aggrège les données en Python.
    4. Demande au LLM de formater ces données en configuration de graphique.
    """
    
    # Remplissage dynamique des valeurs depuis ChromaDB
    populate_allowed_values_from_db(vector_db)
    
    # Etape 1: Comprendre l'intention en se basant STRICTEMENT sur le schéma
    schema_str = get_schema_for_prompt()
    
    intent_prompt = f"""
    Tu es un assistant analytique. Un utilisateur pose une question sur des données de réclamations.
    Tu dois extraire les filtres et la dimension de regroupement.
    
    RÈGLE ABSOLUE : Tu dois utiliser UNIQUEMENT les clés de champ définies dans le dictionnaire de données ci-dessous. 
    Tu ne dois JAMAIS inventer un nom de champ. Si l'utilisateur mentionne un "alias" (ex: "ville"), tu dois utiliser 
    la clé officielle correspondante (ex: "agence").
    Si un champ a des "valeurs_autorisees_strictes", tu dois t'assurer d'utiliser l'une de ces valeurs.
    
    --- DICTIONNAIRE DE DONNÉES (SCHEMA) ---
    {schema_str}
    ----------------------------------------
    
    Réponds UNIQUEMENT avec un objet JSON strict de cette forme :
    {{
        "filters": {{"type": "plainte", "statut": "en cours"}}, // laisse vide {{}} si aucun filtre applicable
        "group_by": "categorie" // Le champ OFFICIEL (clé) par lequel grouper les données
    }}
    """
    
    try:
        response = ollama_client.chat(
            model=DEFAULT_MODEL,
            messages=[
                {'role': 'system', 'content': intent_prompt},
                {'role': 'user', 'content': f"Question: {query}"}
            ],
            format='json',
            options={'temperature': 0}
        )
        
        intent = parse_llm_json(response['message']['content'])
        if not intent:
            intent = {"filters": {}, "group_by": "categorie"}
            
    except Exception as e:
        logger.error(f"Erreur NLP reporting intent: {e}")
        intent = {"filters": {}, "group_by": "categorie"}

    # VALIDATION PYTHON STRICTE DU SCHÉMA
    validated_intent = validate_and_correct_llm_output(intent)
    
    # Etape 2: Récupération des données
    filters = validated_intent.get("filters", {})
    group_by = validated_intent.get("group_by", "categorie")
    
    chroma_filters = {}
    if isinstance(filters, dict):
        for k, v in filters.items():
            if v and isinstance(v, str):
                chroma_filters[k] = v.lower()
                
    where_clause = None
    if len(chroma_filters) > 1:
        where_clause = {"$and": [{k: v} for k, v in chroma_filters.items()]}
    elif len(chroma_filters) == 1:
        where_clause = chroma_filters

    metadata_list = vector_db.get_filtered_claims_metadata(filters=where_clause)
    
    # Etape 3: Aggrégation des données
    if not metadata_list:
        return {
            "title": {"text": "Aucune donnée trouvée"},
            "series": []
        }
        
    counts = Counter()
    for meta in metadata_list:
        val = meta.get(group_by, "Inconnu")
        if not val: val = "Inconnu"
        counts[str(val)] += 1
        
    aggregated_data = dict(counts)
    
    chart_prompt = """
    Tu es un expert en visualisation de données avec Chart.js (v3).
    Ton rôle est de générer une configuration complète (JSON) pour le composant <Chart> ou <Bar> de react-chartjs-2.
    
    Règles TRES STRICTES :
    - Réponds UNIQUEMENT avec un objet JSON valide. Aucun texte avant ou après.
    - Le JSON doit avoir la structure exacte attendue par Chart.js :
      {
        "type": "bar", // ou "line", "pie", "doughnut"
        "data": {
          "labels": ["Label1", "Label2"],
          "datasets": [
            {
              "label": "Titre de la série",
              "data": [10, 20],
              "backgroundColor": ["#36A2EB", "#FF6384"]
            }
          ]
        },
        "options": {
          "responsive": true,
          "plugins": {
            "title": { "display": true, "text": "Titre du graphique" }
          }
        }
      }
    - Ne fais pas d'hallucination, utilise EXACTEMENT les données fournies.
    """
    
    user_prompt = f"""
    Question initiale: {query}
    Dimension analysée: {group_by}
    Données à visualiser: {json.dumps(aggregated_data)}
    """
    
    try:
        response_chart = ollama_client.chat(
            model=DEFAULT_MODEL,
            messages=[
                {'role': 'system', 'content': chart_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            format='json',
            options={'temperature': 0}
        )
        
        chart_config = parse_llm_json(response_chart['message']['content'])
        if not chart_config:
            raise ValueError("LLM n'a pas renvoyé de JSON valide.")
            
        return chart_config
            
    except Exception as e:
        logger.error(f"Erreur génération ECharts: {e}")
        # Fallback de base (Bar chart par défaut)
        labels = list(aggregated_data.keys())
        values = list(aggregated_data.values())
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": query,
                    "data": values,
                    "backgroundColor": "#36A2EB"
                }]
            },
            "options": {
                "responsive": true,
                "plugins": {
                    "title": { "display": true, "text": query }
                }
            }
        }

def generate_insights(days: int = 30) -> dict:
    """
    Récupère les réclamations et génère des alertes et recommandations stratégiques.
    """
    all_metadata = vector_db.get_filtered_claims_metadata(limit=200)
    
    if not all_metadata:
        return {"alertes": [], "recommandations": ["Aucune donnée disponible pour l'analyse."]}
        
    # Aggrégation rapide pour nourrir le LLM
    cat_counts = Counter(m.get('categorie', 'Inconnu') for m in all_metadata)
    mot_counts = Counter(m.get('motif_reclamation', 'Inconnu') for m in all_metadata)
    
    top_categories = dict(cat_counts.most_common(3))
    top_motifs = dict(mot_counts.most_common(5))
    total_claims = len(all_metadata)
    
    summary = {
        "periode_jours": days,
        "total_reclamations_echantillon": total_claims,
        "top_categories": top_categories,
        "top_motifs": top_motifs
    }
    
    system_prompt = """
    Tu es un directeur de la qualité dans une institution financière (projet GPR IA).
    Ton rôle est d'analyser le résumé des réclamations récentes et de formuler des "Insights".
    
    Règles STRICTES:
    - Réponds UNIQUEMENT avec un JSON contenant deux listes de chaînes de caractères : "alertes" et "recommandations".
    - "alertes": Situations critiques, volumes anormaux, points de douleur urgents. (Max 3)
    - "recommandations": Actions stratégiques pour améliorer les processus ou les produits. (Max 3)
    - Ne fais pas d'hallucination sur des données non fournies. Sois très professionnel.
    """
    
    user_prompt = f"Voici le résumé des données récentes :\n{json.dumps(summary, indent=2)}"
    
    try:
        response = ollama_client.chat(
            model=DEFAULT_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            format='json',
            options={'temperature': 0.3}
        )
        
        insights = parse_llm_json(response['message']['content'])
        if insights and "alertes" in insights and "recommandations" in insights:
            return insights
        else:
            return {"alertes": ["Analyse générique impossible"], "recommandations": ["Vérifiez vos données."]}
            
    except Exception as e:
        logger.error(f"Erreur Insights: {e}")
        return {"alertes": ["Erreur lors de la génération des alertes."], "recommandations": ["Erreur lors de la génération des recommandations."]}
