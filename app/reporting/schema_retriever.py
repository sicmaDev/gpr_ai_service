"""
Extracteur dynamique de sous-schéma minimal (Schema Retriever) pour le moteur Text-to-SQL Gouverné.

Ce module garantit :
- L'isolation stricte des seules tables nécessaires pour répondre à l'intention canonique (TextToSQLIntent).
- L'injection automatique des tables passerelles (bridge tables) nécessaires aux jointures complexes.
- L'exclusion absolue et irréversible de toute colonne sensible (is_sensitive=True).
- L'optimisation du contexte LLM pour minimiser la consommation de tokens et éliminer les hallucinations.
"""

from typing import List, Set, Tuple

from app.reporting.business_catalog import get_business_catalog
from app.reporting.schema_catalog import get_minimal_subschema, get_schema_catalog
from app.reporting.text_to_sql_contracts import TextToSQLIntent

# -----------------------------------------------------------------------------
# TABLE DES TABLES PASSERELLES (BRIDGE TABLES)
# -----------------------------------------------------------------------------

# Déclare les dépendances de jointures intermédiaires :
# Si une table cible est requise depuis une table de base donnée, quelles tables
# intermédiaires doivent obligatoirement être ajoutées au sous-schéma ?
_BRIDGE_DEPENDENCIES = {
    # Pour atteindre reporting_categorie_objet depuis reporting_claim ou suggestion,
    # il faut impérativement passer par reporting_objet
    "reporting_categorie_objet": ["reporting_objet"],
    # Pour atteindre reporting_poste depuis reporting_claim, il faut passer par reporting_user
    "reporting_poste": ["reporting_user"],
    # Pour atteindre reporting_satisfaction_measure depuis reporting_claim, il faut passer par reporting_solution
    "reporting_satisfaction_measure": ["reporting_solution"],
}


def resolve_required_tables(intent: TextToSQLIntent) -> List[str]:
    """
    Détermine dynamiquement la liste minimale et ordonnée des tables nécessaires
    pour satisfaire une intention canonique donnée.

    Analyse :
    1. Les tables de faits exigées par le concept de l'entité et par la métrique.
    2. Les tables de dimensions exigées par les axes de découpage demandés.
    3. Les tables exigées par d'éventuels filtres dimensionnels.
    4. Les tables passerelles (bridge tables) requises pour former un chemin de jointure valide.
    """
    if intent.status != "ready" or intent.entity is None or intent.measure is None:
        return []

    catalog_b = get_business_catalog()
    catalog_s = get_schema_catalog()
    selected_tables: Set[str] = set()

    # 1. Résolution des tables depuis la métrique
    metric_id = intent.measure.concept_id
    if metric_id in catalog_b.metrics:
        metric_def = catalog_b.metrics[metric_id]
        selected_tables.update(metric_def.required_tables)

    # 2. Résolution des tables depuis l'entité si non déjà couverte
    if intent.entity.concept_id == "treatment":
        selected_tables.add("reporting_historique_affectations")
    elif intent.entity.include_all_types:
        selected_tables.add("reporting_claim")
        selected_tables.add("reporting_suggestion")
    else:
        types_set = set(intent.entity.types)
        if "CLAIM" in types_set or "DENUNCIATION" in types_set:
            selected_tables.add("reporting_claim")
        if "SUGGESTION" in types_set:
            selected_tables.add("reporting_suggestion")

    # 3. Résolution des tables de dimensions
    for dim in intent.dimensions:
        if dim.concept_id in catalog_b.dimensions:
            dim_def = catalog_b.dimensions[dim.concept_id]
            if dim_def.source_table in catalog_s.tables:
                selected_tables.add(dim_def.source_table)

    # 4. Résolution des tables de filtres
    for flt in intent.filters:
        if flt.concept_id in catalog_b.dimensions:
            dim_def = catalog_b.dimensions[flt.concept_id]
            if dim_def.source_table in catalog_s.tables:
                selected_tables.add(dim_def.source_table)

    # 5. Injection automatique des tables passerelles (Bridge Tables)
    # Ex: Si reporting_categorie_objet est sélectionnée, injecter reporting_objet
    for target_table, bridges in _BRIDGE_DEPENDENCIES.items():
        if target_table in selected_tables:
            for bridge in bridges:
                selected_tables.add(bridge)

    # 6. Ordonnancement logique des tables :
    # Tables de faits d'abord, puis tables de workflow, puis dimensions
    def _table_priority(tbl_name: str) -> int:
        tbl_meta = catalog_s.tables.get(tbl_name)
        if not tbl_meta:
            return 99
        if tbl_meta.table_type == "fact":
            return 1
        if tbl_meta.table_type == "workflow":
            return 2
        if tbl_meta.table_type == "dimension":
            return 3
        return 4

    sorted_tables = sorted(
        [t for t in selected_tables if t in catalog_s.tables],
        key=lambda t: (_table_priority(t), t),
    )

    return sorted_tables


def retrieve_minimal_subschema(intent: TextToSQLIntent) -> Tuple[List[str], str]:
    """
    Extrait la liste des tables et génère le sous-schéma textuel minimal strict
    destiné à être injecté dans le prompt de génération de Nemotron.

    GARANTIE DE SÉCURITÉ ABSOLUE :
    Toute colonne marquée `is_sensitive=True` est systématiquement masquée par
    `get_minimal_subschema()`. Le LLM ne reçoit aucune donnée personnelle.
    """
    required_tables = resolve_required_tables(intent)
    subschema_text = get_minimal_subschema(required_tables)
    return required_tables, subschema_text
