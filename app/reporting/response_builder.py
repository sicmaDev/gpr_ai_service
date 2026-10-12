"""
Module de construction de réponse et restitution graphique Chart.js (Step 9).

Ce module transforme le résultat d'exécution SQL (SqlExecutionResult) en un contrat
public d'interface ReportingQueryResponse rigoureusement conforme, directement exploitable
par le composant Front React AiReportingCharts :
1. Sélection automatique du type de graphique approprié (bar, line, pie, None).
2. Formatage des structures Chart.js (labels et datasets numériques réels sans hallucination).
3. Synthèse textuelle en langage naturel basée strictement sur les chiffres calculés.
4. Propagation de l'identifiant unique query_id pour permettre le feedback en direct.
"""

from typing import Any, Dict, List, Optional

from app.reporting.schemas import ChartDataset, ReportingQueryResponse, Visualization
from app.reporting.text_to_sql_contracts import (
    ExecutionStatus,
    SqlExecutionResult,
    TextToSQLIntent,
)

# Palette de couleurs professionnelle conforme à la charte GPR Banque
PRIMARY_BLUE = "#003366"
PRIMARY_GOLD = "#D4AF37"
COLOR_PALETTE = [
    "#003366",  # Bleu Banque
    "#D4AF37",  # Or
    "#00A86B",  # Vert Succès
    "#E63946",  # Rouge Alerte
    "#457B9D",  # Bleu Moyen
    "#6C757D",  # Gris Neutre
    "#F4A261",  # Orange Pastel
    "#2A9D8F",  # Sarcelle
]


def select_chart_type(intent: TextToSQLIntent, row_count: int) -> Optional[str]:
    """
    Détermine le type de graphique optimal pour visualiser les résultats.

    Règles :
    - 0 ligne : Aucun graphique (None).
    - Mesure scalaire unique (aucune dimension de regroupement) : None (restitution texte / KPI).
    - Dimension temporelle (period, month, receipt_date, etc.) : "line".
    - Dimension discrète avec distribution <= 5 modalités (ex: canal, catégorie) : "pie".
    - Regroupement standard catégoriel (agences, produits, etc.) : "bar".
    """
    if row_count == 0:
        return None

    if not intent.dimensions:
        return None

    primary_dim = intent.dimensions[0].concept_id.lower()

    # Dimension temporelle -> Ligne
    if primary_dim in {"period", "month", "year", "receipt_date", "day", "date"}:
        return "line"

    # Répartition de parts limitées (<= 5) sur canal, catégorie ou risque -> Camembert
    if primary_dim in {"channel", "category", "risk_level", "status", "claim_type"} and row_count <= 5:
        return "pie"

    # Par défaut pour les regroupements (agences, canaux nombreux, etc.) -> Barres
    return "bar"


def _extract_column_keys(
    intent: TextToSQLIntent,
    columns: List[str],
    rows: List[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str]]:
    """
    Identifie la clé de dimension (labels) et la clé de métrique (valeurs) dans les enregistrements.
    """
    if not rows:
        dim_key = intent.dimensions[0].concept_id if intent.dimensions else None
        meas_key = intent.measure.concept_id if intent.measure else None
        return dim_key, meas_key

    first_row = rows[0]
    available_keys = list(first_row.keys())

    # Recherche de la colonne de dimension
    dim_key = None
    if intent.dimensions:
        preferred_dim = intent.dimensions[0].concept_id
        for k in available_keys:
            if preferred_dim in k.lower() or k.lower() in preferred_dim:
                dim_key = k
                break

    if not dim_key:
        for k, v in first_row.items():
            if isinstance(v, str):
                dim_key = k
                break

    # Recherche de la colonne de métrique
    meas_key = None
    if intent.measure:
        preferred_meas = intent.measure.concept_id
        for k in available_keys:
            if preferred_meas in k.lower() or k.lower() in preferred_meas:
                meas_key = k
                break

    if not meas_key:
        for k, v in first_row.items():
            if k != dim_key and isinstance(v, (int, float)):
                meas_key = k
                break

    # Fallbacks si non résolu
    if not dim_key and len(available_keys) > 0:
        dim_key = available_keys[0]
    if not meas_key and len(available_keys) > 1:
        meas_key = available_keys[-1]
    elif not meas_key and len(available_keys) == 1:
        meas_key = available_keys[0]

    return dim_key, meas_key


def format_chartjs_visualization(
    intent: TextToSQLIntent,
    columns: List[str],
    rows: List[Dict[str, Any]],
    title: Optional[str] = None,
) -> Optional[Visualization]:
    """
    Construit un objet Visualization conforme au standard Chart.js consommé par le front React.
    Les chiffres proviennent exclusivement des résultats SQL bruts (zéro hallucination).
    """
    chart_type = select_chart_type(intent, len(rows))
    if chart_type is None and len(rows) > 0:
        return None

    # Si rows est vide mais qu'un type bar est demandé pour structure
    if len(rows) == 0:
        if not intent.dimensions:
            return None
        return Visualization(
            type="bar",
            title=title or "Visualisation",
            labels=[],
            datasets=[
                ChartDataset(
                    label=intent.measure.label if intent.measure else "Valeur",
                    data=[],
                    backgroundColor=PRIMARY_BLUE,
                    borderColor=PRIMARY_BLUE,
                )
            ],
        )

    dim_key, meas_key = _extract_column_keys(intent, columns, rows)

    labels: List[str] = []
    data_values: List[float] = []

    for r in rows:
        label_val = str(r.get(dim_key, "N/A")) if dim_key else "Total"
        raw_val = r.get(meas_key, 0)
        try:
            num_val = float(raw_val) if raw_val is not None else 0.0
        except (ValueError, TypeError):
            num_val = 0.0

        labels.append(label_val)
        data_values.append(num_val)

    # Configuration des couleurs selon le type de graphique
    dataset_label = intent.measure.label if intent.measure else "Valeur"
    effective_title = title or (
        f"{intent.measure.label} par {intent.dimensions[0].label}"
        if (intent.measure and intent.dimensions)
        else (intent.measure.label if intent.measure else "Visualisation")
    )

    if chart_type in {"pie", "doughnut"}:
        colors = COLOR_PALETTE[: len(labels)]
        dataset = ChartDataset(
            label=dataset_label,
            data=data_values,
            backgroundColor=colors,
            borderColor="#FFFFFF",
        )
    elif chart_type == "line":
        dataset = ChartDataset(
            label=dataset_label,
            data=data_values,
            backgroundColor="rgba(0, 51, 102, 0.1)",
            borderColor=PRIMARY_BLUE,
            fill=True,
        )
    else:  # bar
        dataset = ChartDataset(
            label=dataset_label,
            data=data_values,
            backgroundColor=PRIMARY_BLUE,
            borderColor=PRIMARY_BLUE,
        )

    return Visualization(
        type=chart_type,
        title=effective_title,
        labels=labels,
        datasets=[dataset],
    )


def formulate_natural_answer(
    question: str,
    intent: TextToSQLIntent,
    rows: List[Dict[str, Any]],
    total_value: Optional[float] = None,
) -> str:
    """
    Rédige une synthèse textuelle fluide et factuelle en français à destination de l'utilisateur.
    """
    if not rows:
        return "Aucun enregistrement ne correspond aux critères demandés pour cette période."

    meas_label = intent.measure.label if intent.measure else "dossiers"

    # Cas 1 : Valeur scalaire unique
    if len(rows) == 1 and len(rows[0]) == 1:
        val = list(rows[0].values())[0]
        formatted_val = f"{val:,}".replace(",", " ") if isinstance(val, (int, float)) else str(val)
        return (
            f"Pour la période demandée, le résultat pour {meas_label.lower()} est de {formatted_val}."
        )

    # Cas 2 : Répartition selon dimensions
    dim_key, meas_key = _extract_column_keys(intent, list(rows[0].keys()), rows)
    dim_label = intent.dimensions[0].label if intent.dimensions else "critère"

    total = total_value
    if total is None:
        total = sum(float(r.get(meas_key, 0) or 0) for r in rows if meas_key)

    formatted_total = (
        int(total) if total == int(total) else round(total, 2)
    )

    # Top 5 des modalités pour le résumé textuel
    breakdown_parts: List[str] = []
    for r in rows[:5]:
        lbl = str(r.get(dim_key, "N/A"))
        val = r.get(meas_key, 0)
        formatted_sub = int(val) if val == int(val) else round(val, 1)
        breakdown_parts.append(f"{lbl} ({formatted_sub})")

    breakdown_str = ", ".join(breakdown_parts)
    if len(rows) > 5:
        breakdown_str += f", et {len(rows) - 5} autre(s)..."

    return (
        f"Pour la période demandée, un total de {formatted_total} {meas_label.lower()} a été enregistré, "
        f"avec la répartition suivante par {dim_label.lower()} : {breakdown_str}."
    )


def build_reporting_query_response(
    execution_result: SqlExecutionResult,
    intent: TextToSQLIntent,
    natural_language_query: str,
    sources: Optional[List[str]] = None,
    query_id: Optional[str] = None,
    sql_query: Optional[str] = None,
    execution_mode: Optional[str] = None,
) -> ReportingQueryResponse:
    """
    Assemble le contrat final ReportingQueryResponse pour le Front React.
    Garantit l'intégrité des données, la présence du query_id, du SQL exécuté et la sérialisation Pydantic.
    """
    effective_sql = sql_query or execution_result.sql_executed

    # Gestion des erreurs d'exécution ou de validation
    if execution_result.status != ExecutionStatus.SUCCESS:
        if execution_result.status == ExecutionStatus.VALIDATION_FAILED:
            answer = (
                f"La requête demandée ne respecte pas les critères de sécurité et d'intégrité analytique : "
                f"{execution_result.error_message or 'règle non respectée'}."
            )
            summary = "Requête non conforme"
        elif execution_result.status == ExecutionStatus.TIMEOUT:
            answer = "L'exécution de la requête a dépassé le délai limite de traitement autorisé (3.0s)."
            summary = "Délai d'exécution dépassé"
        else:
            answer = (
                f"Une erreur technique est survenue lors de l'exécution : "
                f"{execution_result.error_message or 'erreur SQL'}."
            )
            summary = "Erreur d'exécution SQL"

        return ReportingQueryResponse(
            answer=answer,
            summary=summary,
            query_id=query_id,
            sql_query=effective_sql,
            execution_mode=execution_mode,
            sources=[],
            visualization=None,
            data=[],
        )

    # Cas nominal : succès d'exécution
    effective_sources = sources or ["reporting_claim"]
    summary_title = (
        f"{intent.measure.label} par {intent.dimensions[0].label}"
        if (intent.measure and intent.dimensions)
        else (intent.measure.label if intent.measure else "Résultat de reporting")
    )

    vis = format_chartjs_visualization(
        intent=intent,
        columns=execution_result.columns,
        rows=execution_result.rows,
        title=summary_title,
    )

    answer_text = formulate_natural_answer(
        question=natural_language_query,
        intent=intent,
        rows=execution_result.rows,
    )

    return ReportingQueryResponse(
        answer=answer_text,
        summary=summary_title,
        query_id=query_id,
        sql_query=effective_sql,
        execution_mode=execution_mode,
        sources=effective_sources,
        visualization=vis,
        data=execution_result.rows,
    )

