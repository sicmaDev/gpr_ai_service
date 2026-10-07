"""
Catalogue officiel des métriques et concepts métiers (Business Catalog) pour le moteur Text-to-SQL Gouverné.

Ce module matérialise :
- L'entité unificatrice centrale 'plainte' couvrant réclamations, dénonciations et suggestions.
- Les concepts métiers analytiques ('reclamation', 'denonciation', 'suggestion', 'treatment').
- Les 10 métriques certifiées avec leurs formules de calcul SQL de référence.
- Les dimensions officielles d'agrégation et de filtrage.
- Le dictionnaire exhaustif de synonymes en langue naturelle et son résolveur insensible aux accents.
"""

import unicodedata
from typing import Dict, List, Optional

from app.reporting.text_to_sql_contracts import (
    BusinessCatalog,
    BusinessConcept,
    DimensionDefinition,
    MetricDefinition,
)

# -----------------------------------------------------------------------------
# DÉFINITION DES CONCEPTS MÉTIERS
# -----------------------------------------------------------------------------

_CONCEPTS: Dict[str, BusinessConcept] = {
    "plainte": BusinessConcept(
        concept_id="plainte",
        label="Plaintes globales",
        description=(
            "Concept chapeau unifiant l'ensemble des dossiers enregistrés : "
            "Réclamations (CLAIM), Dénonciations (DENUNCIATION) et Suggestions (SUGGESTION)."
        ),
        target_table="reporting_claim",
        target_columns=["id", "claim_type", "status", "receipt_at"],
    ),
    "reclamation": BusinessConcept(
        concept_id="reclamation",
        label="Réclamations",
        description="Dossiers formels de doléance ou mécontentement usager avec engagement SLA (claim_type = 'CLAIM').",
        target_table="reporting_claim",
        target_columns=["id", "source_code", "claim_type", "status", "receipt_at", "sla_due_at"],
    ),
    "denonciation": BusinessConcept(
        concept_id="denonciation",
        label="Dénonciations",
        description="Signalements d'irrégularités, fraudes ou alertes éthiques, souvent anonymes (claim_type = 'DENUNCIATION').",
        target_table="reporting_claim",
        target_columns=["id", "source_code", "claim_type", "status", "receipt_at"],
    ),
    "suggestion": BusinessConcept(
        concept_id="suggestion",
        label="Suggestions",
        description="Idées, retours constructifs et propositions d'amélioration de la qualité de service ou des offres.",
        target_table="reporting_suggestion",
        target_columns=["id", "reference", "title", "status", "impact_level", "recorded_at"],
    ),
    "treatment": BusinessConcept(
        concept_id="treatment",
        label="Processus de traitement",
        description="Parcours opérationnel complet : affectations successives, solutions formulées et validations managériales.",
        target_table="reporting_historique_affectations",
        target_columns=["id", "nom_agent", "nom_affecteur", "date_affectation", "delai_jours"],
    ),
}

# -----------------------------------------------------------------------------
# DÉFINITION DES MÉTRIQUES CERTIFIÉES
# -----------------------------------------------------------------------------

_METRICS: Dict[str, MetricDefinition] = {
    "plainte_count": MetricDefinition(
        metric_id="plainte_count",
        label="Total unifié des plaintes",
        description="Comptage exhaustif unifié de l'ensemble des dossiers (réclamations, dénonciations et suggestions hors brouillons).",
        required_tables=["reporting_claim", "reporting_suggestion"],
        aggregation_sql_template="(SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)",
    ),
    "reclamation_count": MetricDefinition(
        metric_id="reclamation_count",
        label="Total des réclamations",
        description="Nombre total de réclamations client formellement enregistrées.",
        required_tables=["reporting_claim"],
        aggregation_sql_template="COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END)",
    ),
    "denonciation_count": MetricDefinition(
        metric_id="denonciation_count",
        label="Total des dénonciations",
        description="Nombre total de dénonciations et signalements de fraudes ou d'irrégularités.",
        required_tables=["reporting_claim"],
        aggregation_sql_template="COUNT(CASE WHEN claim_type = 'DENUNCIATION' THEN 1 END)",
    ),
    "suggestion_count": MetricDefinition(
        metric_id="suggestion_count",
        label="Total des suggestions",
        description="Nombre total de propositions d'amélioration et idées enregistrées.",
        required_tables=["reporting_suggestion"],
        aggregation_sql_template="COUNT(reporting_suggestion.id)",
    ),
    "sla_adherence_rate": MetricDefinition(
        metric_id="sla_adherence_rate",
        label="Taux de respect des délais SLA",
        description="Pourcentage de réclamations résolues avant ou à la date limite SLA contractuelle.",
        required_tables=["reporting_claim"],
        aggregation_sql_template="AVG(CASE WHEN resolved_at <= sla_due_at THEN 100.0 ELSE 0.0 END)",
    ),
    "avg_processing_time": MetricDefinition(
        metric_id="avg_processing_time",
        label="Délai moyen de traitement",
        description="Nombre moyen de jours calendaires écoulés entre la date de réception du dossier et sa résolution.",
        required_tables=["reporting_claim"],
        aggregation_sql_template="AVG(DATEDIFF(resolved_at, receipt_at))",
    ),
    "satisfaction_rate": MetricDefinition(
        metric_id="satisfaction_rate",
        label="Taux de satisfaction usagers",
        description="Pourcentage d'usagers ayant formulé un avis favorable ('SATISFIED') post-résolution.",
        required_tables=["reporting_claim"],
        aggregation_sql_template="AVG(CASE WHEN satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END)",
    ),
    "severe_plainte_count": MetricDefinition(
        metric_id="severe_plainte_count",
        label="Nombre de plaintes graves",
        description="Nombre de dossiers qualifiés de gravité urgente ou critique par l'analyse automatique d'urgence.",
        required_tables=["reporting_claim"],
        aggregation_sql_template="COUNT(CASE WHEN ai_urgency = 'GRAVE' THEN 1 END)",
    ),
    "adoption_rate": MetricDefinition(
        metric_id="adoption_rate",
        label="Taux d'adoption des suggestions",
        description="Pourcentage des suggestions enregistrées ayant été validées et adoptées.",
        required_tables=["reporting_suggestion"],
        aggregation_sql_template="AVG(CASE WHEN status = 'ADOPTEE' THEN 100.0 ELSE 0.0 END)",
    ),
    "reaffectation_count": MetricDefinition(
        metric_id="reaffectation_count",
        label="Nombre de réaffectations",
        description="Nombre total de réaffectations et transferts successifs de dossiers entre agents.",
        required_tables=["reporting_historique_affectations"],
        aggregation_sql_template="COUNT(CASE WHEN affectation_precedente_id IS NOT NULL THEN 1 END)",
    ),
}

# -----------------------------------------------------------------------------
# DÉFINITION DES DIMENSIONS
# -----------------------------------------------------------------------------

_DIMENSIONS: Dict[str, DimensionDefinition] = {
    "agency": DimensionDefinition(
        dimension_id="agency",
        label="Agence bancaire",
        source_table="reporting_service_point",
        source_column="libelle",
        join_path="reporting_claim.service_point_id = reporting_service_point.id",
    ),
    "channel": DimensionDefinition(
        dimension_id="channel",
        label="Canal de collecte",
        source_table="reporting_collection_channel",
        source_column="libelle",
        join_path="reporting_claim.collection_channel_id = reporting_collection_channel.id",
    ),
    "product": DimensionDefinition(
        dimension_id="product",
        label="Produit ou service bancaire",
        source_table="reporting_product",
        source_column="libelle",
        join_path="reporting_claim.product_id = reporting_product.id",
    ),
    "category": DimensionDefinition(
        dimension_id="category",
        label="Catégorie de motif",
        source_table="reporting_categorie_objet",
        source_column="libelle",
        join_path="reporting_objet.categorie_id = reporting_categorie_objet.id",
    ),
    "object": DimensionDefinition(
        dimension_id="object",
        label="Motif précis du dossier",
        source_table="reporting_objet",
        source_column="libelle",
        join_path="reporting_claim.objet_id = reporting_objet.id",
    ),
    "status": DimensionDefinition(
        dimension_id="status",
        label="Statut du cycle de traitement",
        source_table="reporting_claim",
        source_column="status",
        join_path=None,
    ),
    "risk_level": DimensionDefinition(
        dimension_id="risk_level",
        label="Niveau de risque réglementaire",
        source_table="reporting_claim",
        source_column="risk_level",
        join_path=None,
    ),
    "impact_level": DimensionDefinition(
        dimension_id="impact_level",
        label="Niveau d'impact suggestion",
        source_table="reporting_suggestion",
        source_column="impact_level",
        join_path=None,
    ),
    "agent": DimensionDefinition(
        dimension_id="agent",
        label="Agent déclarant ou traitant",
        source_table="reporting_user",
        source_column="firstandlastname",
        join_path="reporting_claim.collector_id = reporting_user.id",
    ),
    "period": DimensionDefinition(
        dimension_id="period",
        label="Période temporelle de référence",
        source_table="reporting_claim",
        source_column="receipt_at",
        join_path=None,
    ),
}

# -----------------------------------------------------------------------------
# DICTIONNAIRE DES SYNONYMES EN LANGUE NATURELLE
# -----------------------------------------------------------------------------

_SYNONYMS: Dict[str, List[str]] = {
    "plainte": [
        "plainte",
        "plaintes",
        "dossier",
        "dossiers",
        "requete",
        "requetes",
        "incident",
        "incidents",
    ],
    "reclamation": [
        "reclamation",
        "reclamations",
        "doleance",
        "doleances",
        "mecontentement",
        "mecontentements",
        "litige",
        "litiges",
        "plainte client",
        "plaintes clients",
    ],
    "denonciation": [
        "denonciation",
        "denonciations",
        "fraude",
        "fraudes",
        "soupcon",
        "soupcons",
        "signalement",
        "signalements",
        "alerte ethique",
    ],
    "suggestion": [
        "suggestion",
        "suggestions",
        "idee",
        "idees",
        "proposition",
        "propositions",
        "amelioration",
        "ameliorations",
        "avis positif",
    ],
    "agency": [
        "agence",
        "agences",
        "guichet",
        "guichets",
        "point de vente",
        "points de vente",
        "point de service",
        "points de service",
        "succursale",
        "succursales",
        "bureau",
        "bureaux",
    ],
    "channel": [
        "canal",
        "canaux",
        "moyen",
        "moyens",
        "source",
        "sources",
        "voie",
        "voies",
    ],
    "sla_adherence_rate": [
        "respect sla",
        "delai legal",
        "delai contractuel",
        "taux de respect",
        "dans les delais",
        "respect des delais",
        "conformite sla",
    ],
    "satisfaction_rate": [
        "satisfaction",
        "satisfait",
        "satisfaits",
        "avis client",
        "contentement",
        "taux de satisfaction",
    ],
    "severe": [
        "grave",
        "graves",
        "critique",
        "critiques",
        "urgent",
        "urgents",
        "alerte",
        "alertes",
    ],
}

# -----------------------------------------------------------------------------
# INSTANCE GLOBALE DU BUSINESS CATALOG
# -----------------------------------------------------------------------------

BUSINESS_CATALOG: BusinessCatalog = BusinessCatalog(
    catalog_version="1.0.0",
    concepts=_CONCEPTS,
    metrics=_METRICS,
    dimensions=_DIMENSIONS,
    synonyms=_SYNONYMS,
)


def get_business_catalog() -> BusinessCatalog:
    """Retourne l'instance officielle et validée du BusinessCatalog."""
    return BUSINESS_CATALOG


def _normalize_token(text: str) -> str:
    """Nettoie une chaîne : minuscules, suppression des accents et des espaces superflus."""
    nfkd = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def resolve_synonym(term: str) -> Optional[str]:
    """
    Résout un terme ou une expression en langue naturelle vers l'identifiant canonique correspondant.

    Prend en compte :
    - L'égalité exacte avec une clé canonique (ex: 'plainte', 'reclamation', 'agency').
    - L'appartenance à la liste des synonymes associés (ex: 'plaintes' -> 'plainte', 'doleances' -> 'reclamation').
    - L'insensibilité à la casse et aux accents ('réclamations' -> 'reclamation').
    """
    if not term:
        return None

    normalized_input = _normalize_token(term)
    catalog = get_business_catalog()

    # 1. Correspondance directe avec une clé de concept ou métrique ou dimension
    if normalized_input in catalog.concepts:
        return normalized_input
    if normalized_input in catalog.metrics:
        return normalized_input
    if normalized_input in catalog.dimensions:
        return normalized_input
    if normalized_input in catalog.synonyms:
        return normalized_input

    # 2. Recherche dans le dictionnaire des synonymes
    for canonical_key, synonyms_list in catalog.synonyms.items():
        for syn in synonyms_list:
            if _normalize_token(syn) == normalized_input:
                return canonical_key

    return None
