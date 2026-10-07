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
import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.reporting.business_catalog import resolve_synonym
from app.reporting.text_to_sql_contracts import (
    IntentClarification,
    IntentDimension,
    IntentEntity,
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

    # Si aucune date n'est mentionnée, on applique l'année de référence par défaut
    ref = reference_date or date(2026, 10, 7)
    if start_d is None or end_d is None:
        start_d = date(ref.year, 1, 1)
        end_d = date(ref.year + 1, 1, 1)

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
    elif "satisfaction" in norm or "satisfait" in norm:
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
        filters=[],
        time=time_obj,
    )


# -----------------------------------------------------------------------------
# GÉNÉRATEUR DE PROMPT INTENTION NEMOTRON & PARSEUR
# -----------------------------------------------------------------------------

def build_intent_prompt(query: str, reference_date: Optional[date] = None) -> str:
    """
    Construit le prompt officiel d'extraction d'intention pour Nemotron.

    RÈGLE ABSOLUE DE SÉCURITÉ :
    Le prompt interdit formellement à Nemotron de produire du SQL à cette étape.
    La réponse doit être un objet JSON valide conforme au contrat TextToSQLIntent.
    """
    ref_str = (reference_date or date(2026, 10, 7)).isoformat()

    return f"""Tu es l'analyseur d'intention canonique du moteur analytique de la banque.
Date de référence du système : {ref_str} (Fuseau horaire : Africa/Porto-Novo).

CONSIGNE STRICTE DE SÉCURITÉ :
- Tu ne dois JAMAIS générer de requête SQL ni de fragment SQL.
- Tu dois EXCLUSIVEMENT produire un objet JSON valide correspondant au schéma TextToSQLIntent.

CONCEPTS ET RÈGLES TERMINOLOGIQUES :
- Le mot 'plainte' ou 'dossier' englobe l'ensemble : Réclamations (CLAIM), Dénonciations (DENUNCIATION) et Suggestions (SUGGESTION) -> entity.concept_id='plainte', types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'], include_all_types=true.
- Le mot 'réclamation' concerne uniquement les réclamations -> types=['CLAIM'].
- Le mot 'dénonciation' ou 'fraude' concerne uniquement les dénonciations -> types=['DENUNCIATION'].
- Le mot 'suggestion' ou 'idée' concerne uniquement les suggestions -> types=['SUGGESTION'].

MÉTRIQUES AUTORISÉES (measure.concept_id) :
- plainte_count, reclamation_count, denonciation_count, suggestion_count
- sla_adherence_rate, avg_processing_time, satisfaction_rate, severe_plainte_count, adoption_rate, reaffectation_count

DIMENSIONS AUTORISÉES (dimensions[].concept_id) :
- agency, channel, product, category, object, status, risk_level, impact_level, agent, period

STATUTS POSSIBLES :
- 'ready' : demande claire avec entité, mesure et dates compréhensibles.
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
    En cas d'erreur du LLM ou par défaut, exécute le résolveur déterministe local.
    """
    if use_llm and llm_callable is not None:
        try:
            prompt = build_intent_prompt(query, reference_date)
            response = llm_callable(prompt)
            return parse_intent_response(response)
        except Exception:
            # Replantage sécurisé sur le résolveur déterministe
            pass

    return resolve_intent_deterministic(query, reference_date)
