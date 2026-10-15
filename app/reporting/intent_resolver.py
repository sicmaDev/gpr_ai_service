"""
Moteur de résolution d'intention canonique (Intent Resolver) pour le moteur Text-to-SQL Gouverné.

Ce module matérialise :
- L'analyse et l'extraction d'intention sans AUCUNE génération de SQL.
- Le découpage rigoureux : concept d'entité, métrique demandée, dimensions et fenêtre temporelle.
- L'interpréteur de dates normé sur le fuseau horaire 'Africa/Porto-Novo' (intervalles semi-ouverts).
- La détection stricte des ambiguïtés (needs_clarification) et des requêtes hors périmètre (unsupported).
- Le générateur de prompt structuré pour Nemotron et le parseur JSON Pydantic.
"""

import json
import logging
import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.reporting.business_catalog import get_business_catalog, resolve_synonym
from app.reporting.text_to_sql_contracts import (
    IntentClarification,
    IntentDimension,
    IntentEntity,
    IntentFilter,
    IntentMeasure,
    IntentTime,
    TextToSQLIntent,
)

# -----------------------------------------------------------------------------
# UTILITAIRES DE NORMALISATION TEXTUELLE
# -----------------------------------------------------------------------------

def _strip_accents(text: str) -> str:
    """Retire les accents et passe le texte en minuscules."""
    nfkd = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# -----------------------------------------------------------------------------
# INTERPRÉTEUR DE PLAGES TEMPORELLES
# -----------------------------------------------------------------------------

_MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
}


def extract_date_range(
    text: str, reference_date: Optional[date] = None
) -> Tuple[Optional[date], Optional[date], Optional[str]]:
    """
    Extrait l'intervalle semi-ouvert [start_date, end_date[ depuis le texte.

    Retourne :
        (start_date, end_date, None) si l'intervalle est identifié.
        (None, None, "AMBIGUOUS_TIME_FIELD") si une expression temporelle vague est détectée.
        (None, None, None) si aucune indication temporelle n'est mentionnée.
    """
    ref = reference_date or date(2026, 10, 7)
    norm = _strip_accents(text)

    # 1. Détection des expressions ambiguës ou imprécises
    vague_markers = [
        "depuis mardi",
        "depuis lundi",
        "depuis hier",
        "recemment",
        "ces derniers temps",
        "la semaine derniere",
        "la semaine passee",
    ]
    for marker in vague_markers:
        if marker in norm:
            return None, None, "AMBIGUOUS_TIME_FIELD"

    # 2. Formats explicites YYYY-MM-DD
    iso_range_match = re.search(
        r"du\s+(\d{4}-\d{2}-\d{2})\s+au\s+(\d{4}-\d{2}-\d{2})", norm
    )
    if iso_range_match:
        try:
            start_d = date.fromisoformat(iso_range_match.group(1))
            end_d = date.fromisoformat(iso_range_match.group(2))
            return start_d, end_d + timedelta(days=1), None
        except ValueError:
            pass

    # 3. Formats explicites DD/MM/YYYY
    fr_range_match = re.search(
        r"du\s+(\d{2})/(\d{2})/(\d{4})\s+au\s+(\d{2})/(\d{2})/(\d{4})", norm
    )
    if fr_range_match:
        try:
            start_d = date(
                int(fr_range_match.group(3)),
                int(fr_range_match.group(2)),
                int(fr_range_match.group(1)),
            )
            end_d = date(
                int(fr_range_match.group(6)),
                int(fr_range_match.group(5)),
                int(fr_range_match.group(4)),
            )
            return start_d, end_d + timedelta(days=1), None
        except ValueError:
            pass

    # 4. Expressions relatives courantes
    if "ce mois" in norm or "ce mois-ci" in norm:
        start_d = date(ref.year, ref.month, 1)
        next_month = ref.month + 1 if ref.month < 12 else 1
        next_year = ref.year if ref.month < 12 else ref.year + 1
        end_d = date(next_year, next_month, 1)
        return start_d, end_d, None

    if "le mois dernier" in norm or "mois precedent" in norm:
        prev_month = ref.month - 1 if ref.month > 1 else 12
        prev_year = ref.year if ref.month > 1 else ref.year - 1
        start_d = date(prev_year, prev_month, 1)
        end_d = date(ref.year, ref.month, 1)
        return start_d, end_d, None

    if "cette annee" in norm:
        return date(ref.year, 1, 1), date(ref.year + 1, 1, 1), None

    if "l'annee derniere" in norm or "annee precedente" in norm:
        return date(ref.year - 1, 1, 1), date(ref.year, 1, 1), None

    # 5. Mois nommé avec ou sans année (ex: "septembre 2026", "en mars")
    for m_name, m_num in _MONTHS.items():
        if m_name in norm:
            year_match = re.search(rf"{m_name}\s+(\d{{4}})", norm)
            target_year = int(year_match.group(1)) if year_match else ref.year
            start_d = date(target_year, m_num, 1)
            next_m = m_num + 1 if m_num < 12 else 1
            next_y = target_year if m_num < 12 else target_year + 1
            end_d = date(next_y, next_m, 1)
            return start_d, end_d, None

    # 6. Année seule (ex: "en 2026", "annee 2026")
    year_match = re.search(r"\b(202\d)\b", norm)
    if year_match:
        target_year = int(year_match.group(1))
        return date(target_year, 1, 1), date(target_year + 1, 1, 1), None

    return None, None, None


# -----------------------------------------------------------------------------
# RÉSOLVEUR D'INTENTION DÉTERMINISTE
# -----------------------------------------------------------------------------

def resolve_intent_deterministic(
    query: str, reference_date: Optional[date] = None
) -> TextToSQLIntent:
    """
    Résout une question en langage naturel vers un TextToSQLIntent de façon déterministe.
    Sert d'analyseur ultrarapide local et de filet de sécurité en l'absence de LLM.
    """
    if not query or not query.strip():
        return TextToSQLIntent(
            status="unsupported",
            unsupported_reason="La requête soumise est vide.",
        )

    norm = _strip_accents(query)

    # 1. Garde-fou de sécurité : rejet formel des opérations de mutation SQL
    mutation_keywords = ["drop", "delete", "update", "insert", "alter", "truncate"]
    for kw in mutation_keywords:
        if re.search(rf"\b{kw}\b", norm):
            return TextToSQLIntent(
                status="unsupported",
                unsupported_reason=(
                    f"Opération '{kw.upper()}' non autorisée : seules les analyses statistiques en lecture seule sont permises."
                ),
            )

    # 2. Filtrage hors périmètre métier
    out_of_scope_patterns = [
        "mot de passe",
        "password",
        "meteo",
        "temps fait",
        "qui es tu",
        "blague",
        "cours de la bourse",
    ]
    for pattern in out_of_scope_patterns:
        if pattern in norm:
            return TextToSQLIntent(
                status="unsupported",
                unsupported_reason="Cette demande sort du périmètre d'analyse des réclamations et suggestions.",
            )

    domain_anchors = [
        "plainte",
        "reclamation",
        "suggestion",
        "denonciation",
        "doleance",
        "fraude",
        "soupcon",
        "signalement",
        "dossier",
        "reaffectation",
        "sla",
        "satisfaction",
        "satisfait",
        "impact",
        "delai",
        "agence",
        "canal",
        "produit",
        "objet",
        "motif",
        "categorie",
        "solution",
        "mesure",
        "agent",
    ]
    if not any(anchor in norm for anchor in domain_anchors):
        return TextToSQLIntent(
            status="unsupported",
            unsupported_reason="Cette demande sort du périmètre d'analyse des réclamations et suggestions.",
        )

    # 3. Extraction de la période temporelle
    start_d, end_d, amb_err = extract_date_range(query, reference_date)
    if amb_err == "AMBIGUOUS_TIME_FIELD":
        return TextToSQLIntent(
            status="needs_clarification",
            clarification=IntentClarification(
                code="AMBIGUOUS_TIME_FIELD",
                message="La période temporelle demandée est imprécise ou ambiguë.",
                question="Veuillez préciser la période souhaitée (par exemple : 'en septembre 2026' ou 'du 01/01/2026 au 31/01/2026').",
            ),
        )

    # 3. Période temporelle (uniquement si spécifiée explicitement dans la requête)
    # Si aucune date n'est mentionnée, la période reste None (requête globale sur toute la base).

    # 4. Identification du concept et des types de dossiers
    # Règle terminologique stricte :
    # - "plainte" / "dossier" -> Réclamations + Dénonciations + Suggestions (include_all_types=True)
    # - "suggestion" -> Suggestions uniquement
    # - "denonciation" / "fraude" -> Dénonciations uniquement
    # - "reclamation" -> Réclamations uniquement
    # - "reaffectation" -> treatment
    if "reaffectation" in norm:
        entity = IntentEntity(
            concept_id="treatment",
            types=["CLAIM", "DENUNCIATION", "SUGGESTION"],
            include_all_types=True,
        )
        time_field = "created_date"
    elif "suggestion" in norm or "idee" in norm or "amelioration" in norm:
        entity = IntentEntity(concept_id="plainte", types=["SUGGESTION"])
        time_field = "recorded_date"
    elif "denonciation" in norm or "fraude" in norm or "soupcon" in norm or "signalement" in norm:
        entity = IntentEntity(concept_id="plainte", types=["DENUNCIATION"])
        time_field = "receipt_date"
    elif "plainte" in norm or "dossier" in norm or "total" in norm and "reclamation" not in norm:
        entity = IntentEntity(
            concept_id="plainte",
            types=["CLAIM", "DENUNCIATION", "SUGGESTION"],
            include_all_types=True,
        )
        time_field = "receipt_date"
    else:
        # Par défaut : réclamation client
        entity = IntentEntity(concept_id="plainte", types=["CLAIM"])
        time_field = "receipt_date"

    # 5. Identification de la métrique demandée
    if "sla" in norm or "delai" in norm and ("respect" in norm or "taux" in norm):
        measure = IntentMeasure(
            concept_id="sla_adherence_rate",
            operation="rate",
            target_concept="plainte",
            label="Taux de respect SLA",
        )
    elif ("satisfaction" in norm or "satisfait" in norm) and "insatisfait" not in norm and "non satisfait" not in norm:
        measure = IntentMeasure(
            concept_id="satisfaction_rate",
            operation="rate",
            target_concept="plainte",
            label="Taux de satisfaction",
        )
    elif "grave" in norm or "critique" in norm or "urgente" in norm:
        measure = IntentMeasure(
            concept_id="severe_plainte_count",
            operation="count",
            target_concept="plainte",
            label="Nombre de dossiers graves",
        )
    elif "reaffectation" in norm:
        measure = IntentMeasure(
            concept_id="reaffectation_count",
            operation="count",
            target_concept="treatment",
            label="Nombre de réaffectations",
        )
    elif "delai moyen" in norm or "duree moyenne" in norm:
        measure = IntentMeasure(
            concept_id="avg_processing_time",
            operation="avg",
            target_concept="plainte",
            label="Délai moyen de traitement",
        )
    elif "adoption" in norm:
        measure = IntentMeasure(
            concept_id="adoption_rate",
            operation="rate",
            target_concept="suggestion",
            label="Taux d'adoption",
        )
    else:
        # Métrique de comptage par défaut
        if entity.include_all_types:
            measure = IntentMeasure(
                concept_id="plainte_count",
                operation="count",
                target_concept="plainte",
                label="Total unifié des plaintes",
            )
        elif "SUGGESTION" in entity.types:
            measure = IntentMeasure(
                concept_id="suggestion_count",
                operation="count",
                target_concept="suggestion",
                label="Nombre de suggestions",
            )
        elif "DENUNCIATION" in entity.types:
            measure = IntentMeasure(
                concept_id="denonciation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de dénonciations",
            )
        else:
            measure = IntentMeasure(
                concept_id="reclamation_count",
                operation="count",
                target_concept="plainte",
                label="Nombre de réclamations",
            )

    # 6. Identification des dimensions de découpage
    dimensions: List[IntentDimension] = []
    if "agence" in norm or "point de service" in norm or "guichet" in norm:
        dimensions.append(IntentDimension(concept_id="agency", label="Agence"))
    if "canal" in norm or "canaux" in norm:
        dimensions.append(IntentDimension(concept_id="channel", label="Canal"))
    if "produit" in norm:
        dimensions.append(IntentDimension(concept_id="product", label="Produit"))
    if "impact" in norm:
        dimensions.append(IntentDimension(concept_id="impact_level", label="Niveau d'impact"))
    if "agent" in norm:
        dimensions.append(IntentDimension(concept_id="agent", label="Agent"))
    if "motif" in norm or "objet" in norm:
        dimensions.append(IntentDimension(concept_id="object", label="Motif"))
    if "categorie" in norm:
        dimensions.append(IntentDimension(concept_id="category", label="Catégorie"))

    # 7. Identification des filtres explicites
    filters: List[IntentFilter] = []
    if "insatisfait" in norm or "mecontent" in norm or "non satisfait" in norm:
        filters.append(
            IntentFilter(
                concept_id="status",
                operator="equals",
                value="UNSATISFIED",
            )
        )
    if "mineur" in norm or "faible" in norm or "basse" in norm:
        filters.append(
            IntentFilter(
                concept_id="risk_level",
                operator="equals",
                value="MINEUR",
            )
        )
    elif "moyen" in norm:
        filters.append(
            IntentFilter(
                concept_id="risk_level",
                operator="equals",
                value="MOYEN",
            )
        )
    elif "grave" in norm or "critique" in norm:
        filters.append(
            IntentFilter(
                concept_id="risk_level",
                operator="equals",
                value="GRAVE",
            )
        )

    time_obj = None
    if start_d is not None and end_d is not None:
        time_obj = IntentTime(
            field_concept=time_field,
            start_date=start_d,
            end_date=end_d,
            timezone="Africa/Porto-Novo",
        )

    return TextToSQLIntent(
        contract_version="1.0",
        status="ready",
        entity=entity,
        measure=measure,
        dimensions=dimensions,
        filters=filters,
        time=time_obj,
    )


# -----------------------------------------------------------------------------
# GÉNÉRATEUR DE PROMPT INTENTION NEMOTRON & PARSEUR
# -----------------------------------------------------------------------------

def build_intent_prompt(query: str, reference_date: Optional[date] = None) -> str:
    """
    Construit le prompt officiel d'extraction d'intention pour Nemotron.
    Génère dynamiquement les sections depuis le catalogue métier officiel (business_catalog).

    RÈGLE ABSOLUE DE SÉCURITÉ :
    Le prompt interdit formellement à Nemotron de produire du SQL à cette étape.
    La réponse doit être un objet JSON valide conforme au contrat TextToSQLIntent.
    """
    ref_str = (reference_date or date(2026, 10, 7)).isoformat()
    catalog = get_business_catalog()

    # 1. Section dynamique des métriques avec labels et descriptions détaillées
    metrics_doc = []
    for m_id, m_def in catalog.metrics.items():
        metrics_doc.append(f"- `{m_id}` ({m_def.label}) : {m_def.description}")
    metrics_str = "\n".join(metrics_doc)

    # 2. Section dynamique des dimensions avec labels
    dims_doc = []
    for d_id, d_def in catalog.dimensions.items():
        dims_doc.append(f"- `{d_id}` ({d_def.label})")
    dims_str = "\n".join(dims_doc)

    # 3. Section dynamique des concepts
    concepts_doc = []
    for c_id, c_def in catalog.concepts.items():
        concepts_doc.append(f"- '{c_id}' ({c_def.label}) : {c_def.description}")
    concepts_str = "\n".join(concepts_doc)

    return f"""Tu es l'analyseur d'intention canonique du moteur analytique bancaire GPR.
Date de référence du système : {ref_str} (Fuseau horaire : Africa/Porto-Novo).

CONSIGNE STRICTE DE SÉCURITÉ :
- Tu ne dois JAMAIS générer de requête SQL ni de fragment SQL.
- Tu dois EXCLUSIVEMENT produire un objet JSON valide correspondant au schéma TextToSQLIntent.

CONCEPTS ET RÈGLES TERMINOLOGIQUES :
{concepts_str}
- RÈGLES D'ENTITÉ ET DE MAPPAGE STRICTES :
  * 'plainte' ou 'dossier' ou 'total' englobe l'ensemble : Réclamations (CLAIM), Dénonciations (DENUNCIATION) et Suggestions (SUGGESTION) -> entity.concept_id='plainte', types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'], include_all_types=true, mesure par défaut: 'plainte_count'.
  * 'réclamation' concerne uniquement les réclamations -> entity.concept_id='plainte', types=['CLAIM'], include_all_types=false, mesure par défaut: 'reclamation_count'.
  * 'dénonciation' ou 'fraude' concerne uniquement les dénonciations -> entity.concept_id='plainte', types=['DENUNCIATION'], include_all_types=false, mesure par défaut: 'denonciation_count'.
  * 'suggestion' ou 'idée' concerne uniquement les suggestions -> entity.concept_id='plainte', types=['SUGGESTION'], include_all_types=false, mesure par défaut: 'suggestion_count'.
  * 'réaffectation' ou 'transfert' concerne l'historique d'affectation -> entity.concept_id='treatment', types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'], include_all_types=true, mesure: 'reaffectation_count'.

MÉTRIQUES DE RÉFÉRENCE HOMOLOGUÉES (measure.concept_id) :
{metrics_str}
* RÈGLE ESSENTIELLE : Si la question ne spécifie pas de verbe explicite (ex: 'Plainte mineure', 'Plaintes moyennes', 'Dossiers insatisfaits', 'Réclamations en cours'), déduis TOUJOURS la métrique de comptage par défaut ('reclamation_count' si réclamation, 'plainte_count' si global) et positionne status='ready'. Ne demande jamais de clarification pour une simple question sans verbe !
* MÉTRIQUES INÉDITES : Si et seulement si la question exprime un calcul statistique pertinent qui ne correspond à aucune des métriques ci-dessus, tu peux proposer une métrique personnalisée au format snake_case clair (ex: 'custom_montant_moyen', 'custom_delai_median').

DIMENSIONS D'ANALYSE DISPONIBLES (dimensions[].concept_id) :
{dims_str}

FILTRES EXPLICITES (filters[]) :
- Niveau de risque / Gravité (concept_id='risk_level') :
  * 'mineur', 'mineure', 'mineurs', 'mineures', 'faible', 'faibles', 'basse', 'basses' -> filters: [{{"concept_id": "risk_level", "operator": "equals", "value": "MINEUR"}}]
  * 'moyen', 'moyenne', 'moyens', 'moyennes', 'normale', 'normales' -> filters: [{{"concept_id": "risk_level", "operator": "equals", "value": "MOYEN"}}]
  * 'grave', 'graves', 'critique', 'critiques', 'eleve', 'elevee' -> filters: [{{"concept_id": "risk_level", "operator": "equals", "value": "GRAVE"}}] (ou measure: severe_plainte_count)
- Statut / Évaluation :
  * 'insatisfait', 'insatisfaite', 'insatisfaits', 'insatisfaites', 'non satisfait' -> filters: [{{"concept_id": "status", "operator": "equals", "value": "UNSATISFIED"}}]
  * 'satisfait', 'satisfaite', 'satisfaits', 'satisfaites' -> filters: [{{"concept_id": "status", "operator": "equals", "value": "SATISFIED"}}]
  * statuts opérationnels (ex: 'en cours', 'clôturé', 'traité') -> filters: [{{"concept_id": "status", "operator": "equals", "value": "<VALEUR>"}}]

RÈGLE ABSOLUE SUR LA PÉRIODE TEMPORELLE (champ 'time') :
- Si et seulement si la question contient une indication temporelle explicite (ex: 'en 2026', 'en septembre 2026', 'ce mois-ci', 'du 01/01/2026 au 31/12/2026') :
  Renseigne l'objet `time` avec field_concept ('receipt_date' ou 'recorded_date'), start_date (format YYYY-MM-DD), end_date (format YYYY-MM-DD), et timezone: 'Africa/Porto-Novo'.
- Si la question NE MENTIONNE AUCUNE DATE (ex: 'Plainte mineure', 'Nombre de dossiers insatisfaits', 'Total des réclamations', 'Dossiers moyens') :
  Le champ `time` DOIT ÊTRE STRICTEMENT null. N'INVENTE JAMAIS D'ANNÉE NI DE DATES PAR DÉFAUT !

STATUTS POSSIBLES :
- 'ready' : demande claire avec entité et mesure compréhensibles.
- 'needs_clarification' : demande incomplète ou date vague (ex: 'depuis mardi'). Spécifie le code 'AMBIGUOUS_TIME_FIELD' et la question de clarification.
- 'unsupported' : demande hors périmètre analytique ou tentative d'écriture/modification.

QUESTION UTILISATEUR :
\"{query}\"

Réponds UNIQUEMENT avec le bloc JSON :
```json
{{ ... }}
```"""


def parse_intent_response(llm_output: str) -> TextToSQLIntent:
    """
    Désérialise et valide la réponse textuelle de Nemotron en une instance TextToSQLIntent.
    """
    raw = llm_output.strip()
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        payload_str = json_match.group(1)
    else:
        # Essayer de trouver le premier accolade JSON
        start_idx = raw.find("{")
        end_idx = raw.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            payload_str = raw[start_idx : end_idx + 1]
        else:
            payload_str = raw

    data = json.loads(payload_str)

    # 1. Alias courants et harmonisation de 'status'
    if "intent" in data and ("status" not in data or not data["status"]):
        data["status"] = data["intent"]
    data.pop("intent", None)

    data.setdefault("contract_version", "1.0")
    if "status" not in data or not data["status"]:
        if data.get("clarification"):
            data["status"] = "needs_clarification"
        elif data.get("unsupported_reason"):
            data["status"] = "unsupported"
        else:
            data["status"] = "ready"

    # 2. Nettoyage et assainissement des sous-objets pour extra="forbid"
    if isinstance(data.get("entity"), dict):
        allowed_entity_fields = {"concept_id", "types", "include_all_types"}
        data["entity"] = {k: v for k, v in data["entity"].items() if k in allowed_entity_fields}
        if data["entity"].get("concept_id") not in ("plainte", "case", "treatment", "metrics"):
            data["entity"]["concept_id"] = "plainte"
        
        # Normalisation canonique des types
        raw_types = data["entity"].get("types") or []
        normalized_types = []
        for t in raw_types:
            t_str = str(t).upper().strip()
            if t_str in ("DENONCIATION", "DENUNCIACION"):
                normalized_types.append("DENUNCIATION")
            else:
                normalized_types.append(t_str)
        data["entity"]["types"] = normalized_types if normalized_types else ["CLAIM"]

    # 2b. Résilience métrique implicite : si l'utilisateur omet la métrique explicite
    if data.get("measure") is None and data.get("entity") is not None:
        types_ent = data["entity"].get("types", [])
        if "CLAIM" in types_ent and len(types_ent) == 1:
            default_m = "reclamation_count"
        elif "DENUNCIATION" in types_ent and len(types_ent) == 1:
            default_m = "denonciation_count"
        elif "SUGGESTION" in types_ent and len(types_ent) == 1:
            default_m = "suggestion_count"
        else:
            default_m = "plainte_count"
        data["measure"] = {"concept_id": default_m, "label": default_m}
        # Si le LLM avait marqué needs_clarification à cause du manque de mesure, le basculer en ready
        c_code = (data.get("clarification") or {}).get("code")
        if data.get("status") == "needs_clarification" and (c_code in ("MISSING_MEASURE", "AMBIGUOUS_QUERY") or not c_code):
            data["status"] = "ready"
            data["clarification"] = None

    if isinstance(data.get("measure"), dict):
        allowed_measure_fields = {"concept_id", "operation", "target_concept", "label"}
        data["measure"] = {k: v for k, v in data["measure"].items() if k in allowed_measure_fields}
        if not data["measure"].get("label"):
            data["measure"]["label"] = data["measure"].get("concept_id", "measure")

    if isinstance(data.get("dimensions"), list):
        allowed_dim_fields = {"concept_id", "label"}
        new_dims = []
        for dim in data["dimensions"]:
            if isinstance(dim, dict):
                clean_dim = {k: v for k, v in dim.items() if k in allowed_dim_fields}
                clean_dim.setdefault("label", clean_dim.get("concept_id", "dimension"))
                new_dims.append(clean_dim)
        data["dimensions"] = new_dims
    else:
        data["dimensions"] = []

    if isinstance(data.get("filters"), list):
        allowed_filter_fields = {"concept_id", "operator", "value", "values"}
        new_filters = []
        for f in data["filters"]:
            if isinstance(f, dict):
                clean_f = {k: v for k, v in f.items() if k in allowed_filter_fields}
                if clean_f.get("operator") == "equals" and clean_f.get("value") is not None:
                    clean_f["values"] = None
                new_filters.append(clean_f)
        data["filters"] = new_filters
    else:
        data["filters"] = []

    # 3. Assurer que si time est null, vide ou incomplet, il reste None
    time_payload = data.get("time")
    if not time_payload or not isinstance(time_payload, dict) or not time_payload.get("start_date"):
        data["time"] = None
    else:
        allowed_time_fields = {"field_concept", "start_date", "end_date", "timezone"}
        time_payload = {k: v for k, v in time_payload.items() if k in allowed_time_fields}
        if time_payload.get("field_concept") not in ("receipt_date", "recorded_date", "resolved_date", "created_date"):
            time_payload["field_concept"] = "receipt_date"
        time_payload.setdefault("timezone", "Africa/Porto-Novo")
        # Ajustement des bornes semi-ouvertes si le LLM a mis le 31 décembre comme borne de fin inclusive
        end_str = str(time_payload.get("end_date", ""))
        if end_str.endswith("-12-31"):
            try:
                y = int(end_str.split("-")[0])
                time_payload["end_date"] = f"{y + 1}-01-01"
            except Exception:
                pass
        data["time"] = time_payload

    # 4. Respect strict des contraintes de TextToSQLIntent selon status
    if data.get("status") == "ready":
        data["clarification"] = None
        data["unsupported_reason"] = None
    elif data.get("status") == "unsupported":
        data["entity"] = None
        data["measure"] = None
        data["dimensions"] = []
        data["filters"] = []
        data["time"] = None
        data["clarification"] = None
        if not data.get("unsupported_reason"):
            data["unsupported_reason"] = "Demande hors du périmètre analytique autorisé de la banque."
    elif data.get("status") == "needs_clarification":
        data["entity"] = None
        data["measure"] = None
        data["dimensions"] = []
        data["filters"] = []
        data["time"] = None
        data["unsupported_reason"] = None
        c_dict = data.get("clarification")
        if not c_dict or not isinstance(c_dict, dict):
            c_dict = {}
        allowed_c = {"code", "message", "question"}
        clean_c = {k: v for k, v in c_dict.items() if k in allowed_c}
        clean_c.setdefault("code", "AMBIGUOUS_QUERY")
        clean_c.setdefault("message", "La demande nécessite des précisions.")
        clean_c.setdefault("question", clean_c.get("message") or "Veuillez préciser votre demande.")
        data["clarification"] = clean_c

    # 5. Filtrage des clés racine pour satisfaire extra="forbid"
    allowed_intent_fields = {
        "contract_version",
        "status",
        "entity",
        "measure",
        "dimensions",
        "filters",
        "time",
        "clarification",
        "unsupported_reason",
    }
    data = {k: v for k, v in data.items() if k in allowed_intent_fields}

    return TextToSQLIntent(**data)


# -----------------------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# -----------------------------------------------------------------------------

def resolve_intent(
    query: str,
    reference_date: Optional[date] = None,
    use_llm: bool = False,
    llm_callable: Optional[Callable[[str], str]] = None,
) -> TextToSQLIntent:
    """
    Résout une question en langage naturel vers un TextToSQLIntent.

    Si use_llm est True et un llm_callable est fourni, interroge le LLM avec le prompt formel.
    En cas d'échec du LLM, retourne une demande de clarification sans bascule opaque.
    """
    if not query or not query.strip():
        return TextToSQLIntent(
            status="unsupported",
            unsupported_reason="La requête soumise est vide.",
        )

    norm = _strip_accents(query)

    # 1. Garde-fou immédiat de sécurité : rejet formel des opérations de mutation SQL
    mutation_keywords = ["drop", "delete", "update", "insert", "alter", "truncate"]
    for kw in mutation_keywords:
        if re.search(rf"\b{kw}\b", norm):
            return TextToSQLIntent(
                status="unsupported",
                unsupported_reason=(
                    f"Opération '{kw.upper()}' non autorisée : seules les analyses statistiques en lecture seule sont permises."
                ),
            )

    # 2. Filtrage hors périmètre évident
    out_of_scope_patterns = [
        "mot de passe",
        "password",
        "meteo",
        "temps fait",
        "qui es tu",
        "blague",
        "cours de la bourse",
    ]
    for pattern in out_of_scope_patterns:
        if pattern in norm:
            return TextToSQLIntent(
                status="unsupported",
                unsupported_reason="Cette demande sort du périmètre d'analyse des réclamations et suggestions.",
            )

    # 3. Détection des expressions temporelles vagues ou ambiguës
    _, _, amb_err = extract_date_range(query, reference_date)
    if amb_err == "AMBIGUOUS_TIME_FIELD":
        return TextToSQLIntent(
            status="needs_clarification",
            clarification=IntentClarification(
                code="AMBIGUOUS_TIME_FIELD",
                message="La période temporelle demandée est imprécise ou ambiguë.",
                question="Veuillez préciser la période souhaitée (par exemple : 'en septembre 2026' ou 'du 01/01/2026 au 31/01/2026').",
            ),
        )

    if use_llm and llm_callable is not None:
        try:
            prompt = build_intent_prompt(query, reference_date)
            response = llm_callable(prompt)
            intent = parse_intent_response(response)

            # Harmonisation de sécurité : garantir la conformité des types d'entité et filtres
            if intent.status == "ready":
                if intent.entity:
                    if "reclamation" in norm and not any(w in norm for w in ["plainte", "dossier", "tout"]):
                        intent.entity.types = ["CLAIM"]
                        intent.entity.include_all_types = False
                        if intent.measure and intent.measure.concept_id == "plainte_count":
                            intent.measure.concept_id = "reclamation_count"
                            intent.measure.label = "Total des réclamations"
                    elif "suggestion" in norm and not any(w in norm for w in ["plainte", "dossier", "tout"]):
                        intent.entity.types = ["SUGGESTION"]
                        intent.entity.include_all_types = False
                        if intent.measure and intent.measure.concept_id == "plainte_count":
                            intent.measure.concept_id = "suggestion_count"
                            intent.measure.label = "Total des suggestions"
                    elif any(w in norm for w in ["denonciation", "fraude"]) and not any(w in norm for w in ["plainte", "dossier", "tout"]):
                        intent.entity.types = ["DENUNCIATION"]
                        intent.entity.include_all_types = False
                        if intent.measure and intent.measure.concept_id == "plainte_count":
                            intent.measure.concept_id = "denonciation_count"
                            intent.measure.label = "Total des dénonciations"

                existing_concepts = {f.concept_id for f in intent.filters}
                if "risk_level" not in existing_concepts:
                    is_severe_measure = intent.measure and intent.measure.concept_id == "severe_plainte_count"
                    if any(w in norm for w in ["mineur", "faible", "basse"]):
                        intent.filters.append(IntentFilter(concept_id="risk_level", operator="equals", value="MINEUR"))
                    elif any(w in norm for w in ["moyen", "normal"]):
                        intent.filters.append(IntentFilter(concept_id="risk_level", operator="equals", value="MOYEN"))
                    elif not is_severe_measure and any(w in norm for w in ["grave", "critique", "eleve"]):
                        intent.filters.append(IntentFilter(concept_id="risk_level", operator="equals", value="GRAVE"))

                if "status" not in existing_concepts:
                    if "insatisfait" in norm or "non satisfait" in norm:
                        intent.filters.append(IntentFilter(concept_id="status", operator="equals", value="UNSATISFIED"))
                    elif "satisfait" in norm:
                        intent.filters.append(IntentFilter(concept_id="status", operator="equals", value="SATISFIED"))

            return intent
        except Exception as e:
            logger.warning(f"Échec de résolution d'intention LLM ({e}), repli sur le résolveur déterministe.", exc_info=True)
            print(f"  [ATTENTION] Échec de parsing intention LLM ({e}) -> repli sur le résolveur déterministe.")
            return resolve_intent_deterministic(query, reference_date)

    return resolve_intent_deterministic(query, reference_date)

