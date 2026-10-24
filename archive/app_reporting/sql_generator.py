"""
Générateur de requêtes SQL candidates (SQL Generator) pour le moteur Text-to-SQL Gouverné.

Ce module matérialise :
- La construction du prompt Nemotron pour la génération SQL à partir du sous-schéma minimal.
- L'injection du guide métier et des conventions de référence comme information d'aide au LLM.
- Les contraintes strictes : SELECT exclusif, paramètres liés (:param), respect des jointures.
- Le parseur et validateur Pydantic de la réponse candidate (TextToSQLCandidate).
- Le générateur déterministe hors-ligne (mode test et fallback de résilience).
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional

from app.reporting.business_catalog import get_business_catalog
from app.reporting.schema_retriever import retrieve_minimal_subschema
from app.reporting.text_to_sql_contracts import (
    CandidateParameter,
    CandidateResultColumn,
    TextToSQLCandidate,
    TextToSQLIntent,
)

# -----------------------------------------------------------------------------
# CONSTRUCTEUR DE PROMPT POUR NEMOTRON
# -----------------------------------------------------------------------------

def build_sql_generation_prompt(
    intent: TextToSQLIntent,
    subschema_str: str,
    anti_patterns: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Construit le prompt de génération de requête SQL candidate pour Nemotron.

    Fournit :
    1. L'intention canonique résolue (concept, métrique, dimensions, période).
    2. Le sous-schéma minimal strict extrait par le Schema Retriever (zéro donnée sensible).
    3. Les conventions de calcul métier de référence à titre d'information d'aide.
    4. Les pièges métier et anti-patterns passés signalés par les utilisateurs (le cas échéant).
    5. Les exigences formelles : SELECT pur, paramètres liés (:param), sortie JSON TextToSQLCandidate.
    """
    catalog_b = get_business_catalog()

    # Extraction du guide métier pour la métrique si disponible
    metric_info = ""
    if intent.measure and intent.measure.concept_id in catalog_b.metrics:
        m_def = catalog_b.metrics[intent.measure.concept_id]
        metric_info = (
            f"\nCONVENTIONS DE CALCUL MÉTIER DE RÉFÉRENCE (Guide informatif) :\n"
            f"- Métrique : {m_def.label} (`{m_def.metric_id}`)\n"
            f"- Description : {m_def.description}\n"
            f"- Formule SQL certifiée de référence : `{m_def.aggregation_sql_template}`\n"
        )
    elif intent.measure:
        metric_info = (
            f"\nCONVENTIONS DE CALCUL MÉTIER (Métrique Inédite / Personnalisée) :\n"
            f"- Métrique personnalisée demandée : {intent.measure.label} (`{intent.measure.concept_id}`)\n"
            f"- Consigne : Formule l'agrégation SQL optimale (COUNT, AVG, SUM, etc.) en exploitant directement les colonnes pertinentes du sous-schéma ci-dessous.\n"
        )

    dims_str = ", ".join(d.concept_id for d in intent.dimensions) or "aucune (agrégation globale)"
    types_str = ", ".join(intent.entity.types) if intent.entity and intent.entity.types else "tous types"
    time_str = "non spécifiée (interroger l'ensemble de la base sans filtre temporel)"
    if intent.time:
        time_str = f"du {intent.time.start_date.isoformat()} au {intent.time.end_date.isoformat()} (champ: {intent.time.field_concept})"

    filters_parts = []
    for f in (intent.filters or []):
        if f.operator == "not_equals":
            filters_parts.append(f"{f.concept_id} != '{f.value}'")
        elif f.operator == "not_in":
            filters_parts.append(f"{f.concept_id} NOT IN ({f.values})")
        elif f.operator == "in":
            filters_parts.append(f"{f.concept_id} IN ({f.values})")
        elif f.operator == "between":
            filters_parts.append(f"{f.concept_id} BETWEEN {f.values[0]} AND {f.values[1]}")
        else:
            filters_parts.append(f"{f.concept_id} = '{f.value}'")
    filters_str = ", ".join(filters_parts) if filters_parts else "aucun filtre spécifique"

    # Section des anti-patterns / pièges à éviter (Negative Few-Shots)
    anti_patterns_section = ""
    if anti_patterns:
        anti_lines = []
        for i, ap in enumerate(anti_patterns, 1):
            bad_sql = ap.get("bad_sql", "").strip()
            reason = ap.get("rejection_reason", "").strip()
            anti_lines.append(
                f"{i}. REQUÊTE REJETÉE : `{bad_sql}`\n"
                f"   MOTIF DU SIGNALEMENT : {reason}"
            )
        anti_patterns_section = (
            "\nPIÈGES MÉTIER ET ERREURS À ÉVITER (SIGNALEMENTS UTILISATEURS PASSÉS) :\n"
            "Les approches suivantes ont été FORMELLEMENT REJETÉES suite à des signalements d'utilisateurs habilités :\n"
            + "\n".join(anti_lines)
            + "\nCONSIGNE STRICTE : Tiens compte impérativement de ces retours et ne reproduis AUCUNE de ces erreurs.\n"
        )

    if intent.time:
        time_rule = (
            "2. Paramètres de dates liés obligatoires (:param) :\n"
            "   - N'inclus JAMAIS de dates en dur dans le SQL.\n"
            "   - Utilise impérativement `:start_date` pour la date de début et `:end_date` pour la date de fin.\n"
            f"   - Exemple : `WHERE c.{intent.time.field_concept if intent.time.field_concept == 'receipt_at' else 'receipt_at'} >= :start_date AND c.{intent.time.field_concept if intent.time.field_concept == 'receipt_at' else 'receipt_at'} < :end_date`."
        )
    else:
        time_rule = (
            "2. PÉRIODE TEMPORELLE ABSENTE (AUCUN FILTRE DE DATE) :\n"
            "   - L'utilisateur n'a spécifié AUCUNE date. N'utilise PAS :start_date ni :end_date.\n"
            "   - N'ajoute AUCUNE condition WHERE de restriction temporelle (interroge tout l'historique)."
        )

    intent_json_str = intent.model_dump_json(indent=2)

    return f"""Tu es l'expert en génération de requêtes SQL analytiques du système bancaire GPR.
Ton rôle est de générer une requête SQL paramétrée et optimisée pour répondre précisément à la demande analytique de l'utilisateur.

# CONTRAT D'INTENTION STRUCTURE (INTENTION ANALYTIQUE DE L'UTILISATEUR) :
```json
{intent_json_str}
```
CONSIGNE IMPERATIVE DE FIDELITE SEMANTIQUE :
La requête SQL générée DOIT IMPÉRATIVEMENT et INTÉGRALEMENT implémenter chaque contrainte, filtre (opérateurs equals, not_equals, in, not_in, between), dimension et entité spécifiés dans ce contrat d'intention JSON.

SYNTHESE DE L'INTENTION :
- Entité / Concept : {intent.entity.concept_id if intent.entity else 'plainte'} (Types : {types_str})
- Mesure demandée : {intent.measure.concept_id if intent.measure else 'plainte_count'} ({intent.measure.label if intent.measure else ''})
- Dimensions de regroupement : {dims_str}
- Filtres demandés : {filters_str}
- Période temporelle : {time_str}
{metric_info}
SOUS-SCHÉMA STRICT DE RÉFÉRENCE :
{subschema_str}

CONSIGNES STRICTES D'ÉCRITURE SQL :
1. Type d'instruction : UNIQUEMENT une requête `SELECT` (ou CTE avec `WITH`).
   Toute requête DOIT IMPÉRATIVEMENT débuter par le mot-clé `SELECT ` (ou `WITH `).
   Ne commence JAMAIS directement par une parenthèse `(` ou une opération arithmétique.
   Si tu dois additionner des sous-requêtes, écris : `SELECT ((SELECT ...) + (SELECT ...)) AS plainte_count;`.
   Si tu utilises des CTEs (`WITH cte1 AS (...), cte2 AS (...)`), le `SELECT` final DOIT impérativement inclure la clause `FROM` référençant ces CTEs (ex: `SELECT (c1.cnt + c2.cnt) AS plainte_count FROM cte1, cte2;`).
   Toute mutation (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) est STRICTEMENT INTERDITE.
{time_rule}
3. Respect des jointures :
   - Utilise UNIQUEMENT les tables et jointures listées dans le sous-schéma (`LEFT JOIN` / `INNER JOIN`).
   - Ne fais aucune jointure sur des tables absentes du sous-schéma.
4. Clauses de regroupement :
   - Inclus `GROUP BY` sur toutes les dimensions sélectionnées.
   - Inclus `ORDER BY` sur la mesure calculée (généralement `DESC`).
5. Nommage des colonnes :
   - Donne des alias clairs aux colonnes sélectionnées (`AS agency`, `AS case_count`, etc.).
6. Règles Métier de Filtrage et de Statuts :
   - Clôture & Résolution : Un dossier est clôturé et résolu si et seulement si `c.status = 'SATISFIED'`.
   - Dossiers en cours / non résolus : Tout dossier où `c.status != 'SATISFIED'` est considéré comme en cours de traitement (incluant SAVED, AFFECTED, TREAT, CLASSED et UNSATISFIED).
   - Dénonciations & Fraudes : Utilise TOUJOURS `c.claim_type IN ('DENUNCIATION', 'DENUNCIACION')` pour interroger les dénonciations en base.
   - Canaux sans guichet / hors agence physique : Les canaux physiques en base sont 'AGENCE' et 'Physique'. Pour une demande "hors agence physique" ou "sans guichet", utilise : `c.channel NOT IN ('AGENCE', 'Physique')` (qui conserve 'TELEPHONE' et 'WEB').
   - Satisfaction client : Évaluée sur `c.status = 'SATISFIED'` parmi les dossiers ayant un avis exprimé (`c.status IN ('SATISFIED', 'UNSATISFIED')`).
   - Taux de respect SLA :
     `ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2)`.
{anti_patterns_section}
FORMAT DE SORTIE ATTENDU :
Réponds EXCLUSIVEMENT avec un bloc JSON valide respectant rigoureusement le contrat TextToSQLCandidate :
```json
{{
  "contract_version": "1.0",
  "sql": "SELECT ... FROM ... WHERE ... GROUP BY ... ORDER BY ...",
  "parameters": {{""" + (
      """\n    "start_date": {"type": "datetime", "source": "intent.time.start_date"},\n    "end_date": {"type": "datetime", "source": "intent.time.end_date"}\n  """
      if intent.time else ""
  ) + """}},
  "used_schema": ["nom_table_1", "nom_table_2"],
  "result_columns": [
    {{"name": "nom_colonne_dimension", "concept_id": "concept_dimension", "role": "dimension", "data_type": "string"}},
    {{"name": "nom_colonne_mesure", "concept_id": "concept_mesure", "role": "measure", "data_type": "integer"}}
  ],
  "assumptions": ["Hypothèse explicative éventuelle"]
}}
```"""


# -----------------------------------------------------------------------------
# MOTEUR 1 : COERCITEUR POLYMORPHIQUE DE TYPES LLM (UNIVERSAL TYPE COERCER)
# -----------------------------------------------------------------------------

CANONICAL_TYPE_MAPPING: Dict[str, str] = {
    # Famille numérique à virgule (decimal)
    "double": "decimal",
    "float": "decimal",
    "decimal": "decimal",
    "numeric": "decimal",
    "real": "decimal",
    "number": "decimal",
    "double precision": "decimal",
    # Famille textuelle (string)
    "varchar": "string",
    "text": "string",
    "char": "string",
    "str": "string",
    "string": "string",
    "character varying": "string",
    # Famille entière (integer)
    "int": "integer",
    "int2": "integer",
    "int4": "integer",
    "int8": "integer",
    "integer": "integer",
    "bigint": "integer",
    "smallint": "integer",
    "tinyint": "integer",
    # Famille temporelle
    "timestamp": "datetime",
    "timestamptz": "datetime",
    "datetime": "datetime",
    "date": "date",
    "time": "datetime",
    # Famille booléenne
    "bool": "boolean",
    "boolean": "boolean",
}


def coerce_candidate_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coerciteur polymorphique de types (Moteur 1).
    Assainit et réduit canoniquement les types de données SQL et paramètres retournés par le LLM
    pour garantir la conformité stricte au contrat Pydantic TextToSQLCandidate.
    """
    if not isinstance(data, dict):
        return data

    # 1. Normalisation du contrat
    if not data.get("contract_version"):
        data["contract_version"] = "1.0"

    # 2. Déduplication de used_schema en préservant l'ordre
    if "used_schema" in data and isinstance(data["used_schema"], list):
        data["used_schema"] = list(dict.fromkeys(data["used_schema"]))

    # 3. Assainissement des paramètres
    raw_params = data.get("parameters")
    if isinstance(raw_params, dict):
        cleaned_params = {}
        for p_name, p_val in raw_params.items():
            if isinstance(p_val, dict):
                src = p_val.get("source")
                if not src or not str(src).strip():
                    p_val["source"] = "intent.time.start_date" if "start" in p_name else ("intent.time.end_date" if "end" in p_name else "custom")
                raw_t = str(p_val.get("type", "")).strip().lower()
                p_val["type"] = CANONICAL_TYPE_MAPPING.get(raw_t, "datetime" if "date" in p_name else "string")
                cleaned_params[p_name] = p_val
            elif isinstance(p_val, str):
                raw_t = p_val.strip().lower()
                p_type = CANONICAL_TYPE_MAPPING.get(raw_t, "datetime" if "date" in p_name else "string")
                cleaned_params[p_name] = {"type": p_type, "source": "custom"}

        data["parameters"] = cleaned_params
    elif raw_params is None:
        data["parameters"] = {}


    # 4. Normalisation des colonnes résultantes (result_columns)
    raw_columns = data.get("result_columns")
    if isinstance(raw_columns, list):
        cleaned_cols = []
        for col in raw_columns:
            if isinstance(col, dict):
                c_role = col.get("role", "measure")
                if c_role not in ("dimension", "measure"):
                    c_role = "dimension" if col.get("name") in ("agency", "channel", "product", "category", "object", "status") else "measure"
                col["role"] = c_role

                raw_t = str(col.get("data_type", "")).strip().lower()
                if raw_t in CANONICAL_TYPE_MAPPING:
                    col["data_type"] = CANONICAL_TYPE_MAPPING[raw_t]
                else:
                    col_name = str(col.get("name", "")).lower()
                    if c_role == "measure":
                        if any(kw in col_name for kw in ("avg", "rate", "taux", "ratio", "score", "percent", "pourcent")):
                            col["data_type"] = "decimal"
                        elif any(kw in col_name for kw in ("count", "nb", "nombre", "total", "sum")):
                            col["data_type"] = "integer"
                        else:
                            col["data_type"] = "decimal"
                    else:
                        col["data_type"] = "string"
                cleaned_cols.append(col)
        data["result_columns"] = cleaned_cols

    return data


# -----------------------------------------------------------------------------
# DÉSÉRIALISATION ET VALIDATION DE LA RÉPONSE CANDIDATE
# -----------------------------------------------------------------------------

def parse_candidate_response(raw_llm_output: str) -> TextToSQLCandidate:
    """
    Extrait et valide le JSON candidat retourné par le modèle Nemotron.
    Garantit la conformité stricte au contrat Pydantic TextToSQLCandidate.
    """
    raw = raw_llm_output.strip()
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        payload_str = json_match.group(1)
    else:
        start_idx = raw.find("{")
        end_idx = raw.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            payload_str = raw[start_idx : end_idx + 1]
        else:
            payload_str = raw

    data = json.loads(payload_str)

    # Normalisation syntaxique : nettoyer les échappements littéraux et s'assurer que la requête débute par une instruction SELECT valide
    sql = data.get("sql", "").strip()
    while "\\n" in sql:
        sql = sql.replace("\\n", "\n")
    while "\\t" in sql:
        sql = sql.replace("\\t", " ")

    if sql.startswith("(") and not sql.upper().startswith(("SELECT", "WITH")):
        measure_alias = "plainte_count"
        if data.get("result_columns") and len(data["result_columns"]) > 0:
            measure_alias = data["result_columns"][0].get("name", "plainte_count")
        sql_clean = sql.rstrip(";").strip()
        sql = f"SELECT ({sql_clean}) AS {measure_alias}"

    data["sql"] = sql

    # Application du Coerciteur Polymorphique Universel (Moteur 1)
    data = coerce_candidate_payload(data)

    return TextToSQLCandidate(**data)


# -----------------------------------------------------------------------------
# GÉNÉRATEUR DÉTERMINISTE HORS-LIGNE (FALLBACK & MODE TEST)
# -----------------------------------------------------------------------------

def generate_candidate_fallback(intent: TextToSQLIntent) -> TextToSQLCandidate:
    """
    Générateur SQL déterministe pour tests locaux rapides et solution de secours
    en cas d'indisponibilité du service LLM distant.

    Assemble mathématiquement la requête SQL candidate à partir des métadonnées
    officielles du Schema Catalog et du Business Catalog.
    """
    if intent.status != "ready" or intent.entity is None or intent.measure is None:
        raise ValueError("Impossible de générer un SQL candidat pour une intention non 'ready'.")

    # 1. Sélection de la table de faits pivot
    is_unified = intent.entity.include_all_types
    is_suggestion = "SUGGESTION" in intent.entity.types and not is_unified
    is_treatment = intent.entity.concept_id == "treatment"

    select_parts: List[str] = []
    join_parts: List[str] = []
    group_parts: List[str] = []
    where_parts: List[str] = []
    used_schema: List[str] = []
    result_columns: List[CandidateResultColumn] = []

    # 2. Construction des dimensions
    for dim in intent.dimensions:
        if dim.concept_id == "agency":
            select_parts.append("sp.libelle AS agency")
            join_parts.append("LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id")
            group_parts.append("sp.libelle")
            used_schema.append("reporting_service_point")
            result_columns.append(
                CandidateResultColumn(
                    name="agency", concept_id="agency", role="dimension", data_type="string"
                )
            )
        elif dim.concept_id == "channel":
            select_parts.append("cc.libelle AS channel")
            join_parts.append("LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id")
            group_parts.append("cc.libelle")
            used_schema.append("reporting_collection_channel")
            result_columns.append(
                CandidateResultColumn(
                    name="channel", concept_id="channel", role="dimension", data_type="string"
                )
            )
        elif dim.concept_id == "product":
            select_parts.append("p.libelle AS product")
            join_parts.append("LEFT JOIN reporting_product p ON c.product_id = p.id")
            group_parts.append("p.libelle")
            used_schema.append("reporting_product")
            result_columns.append(
                CandidateResultColumn(
                    name="product", concept_id="product", role="dimension", data_type="string"
                )
            )
        elif dim.concept_id == "category":
            select_parts.append("cat.libelle AS category")
            join_parts.append("LEFT JOIN reporting_objet o ON c.objet_id = o.id")
            join_parts.append("LEFT JOIN reporting_categorie_objet cat ON o.categorie_id = cat.id")
            group_parts.append("cat.libelle")
            used_schema.extend(["reporting_objet", "reporting_categorie_objet"])
            result_columns.append(
                CandidateResultColumn(
                    name="category", concept_id="category", role="dimension", data_type="string"
                )
            )
        elif dim.concept_id == "object":
            select_parts.append("o.libelle AS object")
            join_parts.append("LEFT JOIN reporting_objet o ON c.objet_id = o.id")
            group_parts.append("o.libelle")
            used_schema.append("reporting_objet")
            result_columns.append(
                CandidateResultColumn(
                    name="object", concept_id="object", role="dimension", data_type="string"
                )
            )
        elif dim.concept_id == "impact_level":
            select_parts.append("s.impact_level AS impact_level")
            group_parts.append("s.impact_level")
            result_columns.append(
                CandidateResultColumn(
                    name="impact_level",
                    concept_id="impact_level",
                    role="dimension",
                    data_type="string",
                )
            )

    # 3. Construction de la mesure
    measure_id = intent.measure.concept_id

    # Moteur 2 : Théorème d'Invariance Métier (Protocole Fail-Closed)
    # Le fallback déterministe ne peut calculer QUE des métriques certifiées.
    # Interdiction formelle de substituer une métrique non supportée par plainte_count.
    SUPPORTED_FALLBACK_MEASURES = {
        "plainte_count",
        "reclamation_count",
        "denonciation_count",
        "suggestion_count",
        "sla_adherence_rate",
        "avg_processing_time",
        "satisfaction_rate",
        "severe_plainte_count",
        "reaffectation_count",
        "case_count",
    }
    if measure_id not in SUPPORTED_FALLBACK_MEASURES:
        raise ValueError(
            f"Métrique '{measure_id}' non supportée par le fallback déterministe (fail-closed)."
        )

    if is_unified and len(intent.dimensions) == 0:
        if measure_id not in ("plainte_count", "reclamation_count", "case_count"):
            raise ValueError(
                f"Métrique unifiée '{measure_id}' non supportée en mode déterministe."
            )
        # Requête unifiée globale (réclamations + suggestions)
        if intent.time:
            sql = (
                "SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= :start_date AND receipt_at < :end_date) + "
                "(SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= :start_date AND recorded_at < :end_date)) "
                "AS plainte_count"
            )
        else:
            sql = (
                "SELECT ((SELECT COUNT(*) FROM reporting_claim) + "
                "(SELECT COUNT(*) FROM reporting_suggestion)) "
                "AS plainte_count"
            )
        used_schema.extend(["reporting_claim", "reporting_suggestion"])
        result_columns.append(
            CandidateResultColumn(
                name="plainte_count",
                concept_id="plainte_count",
                role="measure",
                data_type="integer",
            )
        )
    elif is_treatment:
        used_schema.append("reporting_historique_affectations")
        select_parts.append("COUNT(h.id) AS reaffectation_count")
        result_columns.append(
            CandidateResultColumn(
                name="reaffectation_count",
                concept_id="reaffectation_count",
                role="measure",
                data_type="integer",
            )
        )
        from_clause = "FROM reporting_historique_affectations h"
        where_parts.append("h.affectation_precedente_id IS NOT NULL")
        if intent.time:
            where_parts.append("h.date_affectation >= :start_date AND h.date_affectation < :end_date")
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        sql = f"SELECT {', '.join(select_parts)} {from_clause} {where_clause}".strip()
    elif is_suggestion:
        used_schema.append("reporting_suggestion")
        select_parts.append("COUNT(s.id) AS suggestion_count")
        result_columns.append(
            CandidateResultColumn(
                name="suggestion_count",
                concept_id="suggestion_count",
                role="measure",
                data_type="integer",
            )
        )
        from_clause = "FROM reporting_suggestion s"
        if intent.time:
            where_parts.append("s.recorded_at >= :start_date AND s.recorded_at < :end_date")
        joins = " ".join(join_parts)
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        group_by = f"GROUP BY {', '.join(group_parts)}" if group_parts else ""
        order_by = "ORDER BY suggestion_count DESC" if group_parts else ""
        sql = f"SELECT {', '.join(select_parts)} {from_clause} {joins} {where_clause} {group_by} {order_by}".strip()
    else:
        # Table pivot principale : reporting_claim
        used_schema.append("reporting_claim")
        from_clause = "FROM reporting_claim c"

        if measure_id == "sla_adherence_rate":
            select_parts.append(
                "AVG(CASE WHEN c.resolved_at <= c.sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate"
            )
            result_columns.append(
                CandidateResultColumn(
                    name="sla_adherence_rate",
                    concept_id="sla_adherence_rate",
                    role="measure",
                    data_type="decimal",
                )
            )
            where_parts.append("c.resolved_at IS NOT NULL")
        elif measure_id == "satisfaction_rate":
            select_parts.append(
                "AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate"
            )
            result_columns.append(
                CandidateResultColumn(
                    name="satisfaction_rate",
                    concept_id="satisfaction_rate",
                    role="measure",
                    data_type="decimal",
                )
            )
            where_parts.append("c.satisfaction_status IS NOT NULL")
        elif measure_id == "severe_plainte_count":
            select_parts.append("COUNT(c.id) AS severe_count")
            result_columns.append(
                CandidateResultColumn(
                    name="severe_count",
                    concept_id="severe_plainte_count",
                    role="measure",
                    data_type="integer",
                )
            )
            where_parts.append("c.risk_level = 'GRAVE'")
        elif measure_id == "denonciation_count" or ("DENUNCIATION" in intent.entity.types and not is_unified):
            select_parts.append("COUNT(c.id) AS denonciation_count")
            result_columns.append(
                CandidateResultColumn(
                    name="denonciation_count",
                    concept_id="denonciation_count",
                    role="measure",
                    data_type="integer",
                )
            )
            where_parts.append("c.claim_type = 'DENUNCIATION'")
        else:
            select_parts.append("COUNT(c.id) AS case_count")
            result_columns.append(
                CandidateResultColumn(
                    name="case_count",
                    concept_id="case_count",
                    role="measure",
                    data_type="integer",
                )
            )
            where_parts.append("c.claim_type = 'CLAIM'")

        # Prise en compte des filtres explicites (urgence, statut, etc.)
        for flt in intent.filters:
            if flt.concept_id in ("risk_level", "urgency", "ai_urgency"):
                where_parts.append(f"c.risk_level = '{flt.value}'")
            elif flt.concept_id == "status":
                s_val = str(flt.value).upper() if flt.value is not None else ""
                if flt.operator == "not_equals":
                    where_parts.append(f"c.status != '{flt.value}'")
                elif s_val in ("UNSATISFIED", "INSATISFAIT"):
                    where_parts.append("c.satisfaction_status = 'UNSATISFIED'")
                elif s_val in ("SATISFIED", "SATISFAIT"):
                    # Moteur 4 : Garde-fou anti-tautologie (ne pas filtrer le dénominateur sur la mesure)
                    if measure_id != "satisfaction_rate":
                        where_parts.append("c.status = 'SATISFIED'")
                else:
                    where_parts.append(f"c.status = '{flt.value}'")
            elif flt.concept_id == "channel":
                if flt.operator == "not_in" and flt.values:
                    quoted = ", ".join(f"'{v}'" for v in flt.values)
                    where_parts.append(f"c.channel NOT IN ({quoted})")
                elif flt.operator == "in" and flt.values:
                    quoted = ", ".join(f"'{v}'" for v in flt.values)
                    where_parts.append(f"c.channel IN ({quoted})")
                elif flt.value:
                    where_parts.append(f"c.channel = '{flt.value}'")

        if intent.time:
            where_parts.append("c.receipt_at >= :start_date AND c.receipt_at < :end_date")

        joins = " ".join(join_parts)
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        group_by = f"GROUP BY {', '.join(group_parts)}" if group_parts else ""
        order_by = f"ORDER BY {result_columns[-1].name} DESC" if group_parts else ""
        sql = f"SELECT {', '.join(select_parts)} {from_clause} {joins} {where_clause} {group_by} {order_by}".strip()

    # Nettoyage des doublons dans used_schema tout en préservant l'ordre
    unique_schema = list(dict.fromkeys(used_schema))

    parameters: Dict[str, CandidateParameter] = {}
    if intent.time:
        parameters["start_date"] = CandidateParameter(type="datetime", source="intent.time.start_date")
        parameters["end_date"] = CandidateParameter(type="datetime", source="intent.time.end_date")


    return TextToSQLCandidate(
        contract_version="1.0",
        sql=sql,
        parameters=parameters,
        used_schema=unique_schema,
        result_columns=result_columns,
        assumptions=["Exclusion automatique des dossiers en brouillon (TEMP_SAVED)"],
    )


# -----------------------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL DU GÉNÉRATEUR SQL
# -----------------------------------------------------------------------------

def generate_sql_candidate(
    intent: TextToSQLIntent,
    use_llm: bool = False,
    llm_callable: Optional[Callable[[str], str]] = None,
    anti_patterns: Optional[List[Dict[str, str]]] = None,
) -> TextToSQLCandidate:
    """
    Point d'entrée du Step 5 pour produire un TextToSQLCandidate à partir d'un TextToSQLIntent.

    Si use_llm est activé avec un callable LLM :
    - Extrait le sous-schéma minimal strict sans colonnes sensibles.
    - Construit le prompt avec le guide métier informatif et les anti-patterns passés.
    - Appelle le LLM et désérialise le JSON retourné.
    - En cas d'erreur réseau/LLM, bascule automatiquement sur le générateur déterministe.
    """
    if use_llm and llm_callable is not None:
        try:
            _, subschema_text = retrieve_minimal_subschema(intent)
            prompt = build_sql_generation_prompt(intent, subschema_text, anti_patterns=anti_patterns)
            llm_output = llm_callable(prompt)
            return parse_candidate_response(llm_output)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Échec de parsing candidat LLM ({exc}), repli sur le générateur supervisé.")
            print(f"  [ATTENTION] Échec de parsing candidat LLM ({exc}) -> repli sur le générateur supervisé.")

    return generate_candidate_fallback(intent)

