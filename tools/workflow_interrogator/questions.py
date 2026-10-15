"""
Catalogue des questions de test pour le Workflow Text-to-SQL Gouverné.
Couvre l'intégralité des sous-étapes P1.1 à P1.5 du plan de test.
"""

from typing import Any, Dict, List

QUESTIONS_CATALOG: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # Sous-step P1.1 : Mappage du Concept d'Entité (entity)
    # -------------------------------------------------------------------------
    {
        "id": 1,
        "scenario": "P1.1-A",
        "category": "Mappage Entité",
        "title": "Simple - Réclamations pures",
        "question": "Combien de réclamations ?",
        "expected": {
            "entity": "plainte",
            "types": ["CLAIM"],
            "include_all_types": False,
        },
    },
    {
        "id": 2,
        "scenario": "P1.1-B",
        "category": "Mappage Entité",
        "title": "Moyen - Dénonciations enregistrées",
        "question": "Quelles sont les dénonciations enregistrées ?",
        "expected": {
            "entity": "plainte",
            "types": ["DENUNCIATION"],
        },
    },
    {
        "id": 3,
        "scenario": "P1.1-C",
        "category": "Mappage Entité",
        "title": "Avancé - Idées et suggestions",
        "question": "Nombre d'idées et suggestions d'amélioration",
        "expected": {
            "entity": "plainte",
            "types": ["SUGGESTION"],
        },
    },
    {
        "id": 4,
        "scenario": "P1.1-D",
        "category": "Mappage Entité",
        "title": "Global - Volume total unifié",
        "question": "Volume total de dossiers reçus par la banque",
        "expected": {
            "entity": "plainte",
            "types": ["CLAIM", "DENUNCIATION", "SUGGESTION"],
            "include_all_types": True,
        },
    },
    {
        "id": 5,
        "scenario": "P1.1-E",
        "category": "Mappage Entité",
        "title": "Spécifique - Transferts de dossiers",
        "question": "Combien de transferts de dossiers ont eu lieu ?",
        "expected": {
            "entity": "treatment",
        },
    },

    # -------------------------------------------------------------------------
    # Sous-step P1.2 : Déduction de la Mesure Statistique (measure)
    # -------------------------------------------------------------------------
    {
        "id": 6,
        "scenario": "P1.2-A",
        "category": "Déduction Mesure",
        "title": "Simple sans verbe - Plaintes",
        "question": "Plaintes",
        "expected": {
            "measure": "plainte_count",
            "operation": "count",
        },
    },
    {
        "id": 7,
        "scenario": "P1.2-B",
        "category": "Déduction Mesure",
        "title": "Simple sans verbe - Réclamations moyennes",
        "question": "Réclamations moyennes",
        "expected": {
            "measure": "reclamation_count",
            "filter_risk_level": "MOYEN",
        },
    },
    {
        "id": 8,
        "scenario": "P1.2-C",
        "category": "Déduction Mesure",
        "title": "Moyen - Ratio SLA",
        "question": "Taux de respect des engagements SLA",
        "expected": {
            "measure": "sla_adherence_rate",
            "operation": "rate",
        },
    },
    {
        "id": 9,
        "scenario": "P1.2-D",
        "category": "Déduction Mesure",
        "title": "Moyen - Satisfaction client",
        "question": "Pourcentage d'usagers satisfaits",
        "expected": {
            "measure": "satisfaction_rate",
            "operation": "rate",
        },
    },
    {
        "id": 10,
        "scenario": "P1.2-E",
        "category": "Déduction Mesure",
        "title": "Avancé - Métrique personnalisée",
        "question": "Score moyen de risque estimé",
        "expected": {
            "measure": "custom_avg_risk_score",
            "operation": "avg",
        },
    },

    # -------------------------------------------------------------------------
    # Sous-step P1.3 : Extraction des Dimensions de Regroupement (dimensions)
    # -------------------------------------------------------------------------
    {
        "id": 11,
        "scenario": "P1.3-A",
        "category": "Dimensions",
        "title": "Simple - Par agence",
        "question": "Réclamations par agence",
        "expected": {
            "dimensions": ["agency"],
        },
    },
    {
        "id": 12,
        "scenario": "P1.3-B",
        "category": "Dimensions",
        "title": "Simple - Par canal",
        "question": "Dossiers par canal de collecte",
        "expected": {
            "dimensions": ["channel"],
        },
    },
    {
        "id": 13,
        "scenario": "P1.3-C",
        "category": "Dimensions",
        "title": "Moyen - Par impact",
        "question": "Suggestions selon le niveau d'impact",
        "expected": {
            "dimensions": ["impact_level"],
        },
    },
    {
        "id": 14,
        "scenario": "P1.3-D",
        "category": "Dimensions",
        "title": "Avancé - Multi-dimensions agence + canal",
        "question": "Réclamations par agence et par canal",
        "expected": {
            "dimensions": ["agency", "channel"],
        },
    },
    {
        "id": 15,
        "scenario": "P1.3-E",
        "category": "Dimensions",
        "title": "Sans dimension - Total",
        "question": "Total des réclamations",
        "expected": {
            "dimensions": [],
        },
    },

    # -------------------------------------------------------------------------
    # Sous-step P1.4 : Extraction des Filtres Explicites (filters)
    # -------------------------------------------------------------------------
    {
        "id": 16,
        "scenario": "P1.4-A",
        "category": "Filtres Explicites",
        "title": "Filtre gravité directe",
        "question": "Réclamations graves",
        "expected": {
            "filters": [{"concept_id": "risk_level", "value": "GRAVE"}],
        },
    },
    {
        "id": 17,
        "scenario": "P1.4-B",
        "category": "Filtres Explicites",
        "title": "Filtre synonyme gravité critique",
        "question": "Plaintes critiques ou lourdes",
        "expected": {
            "filters": [{"concept_id": "risk_level", "value": "GRAVE"}],
        },
    },
    {
        "id": 18,
        "scenario": "P1.4-C",
        "category": "Filtres Explicites",
        "title": "Filtre statut insatisfait",
        "question": "Dossiers insatisfaits",
        "expected": {
            "filters": [{"concept_id": "status", "value": "UNSATISFIED"}],
        },
    },
    {
        "id": 19,
        "scenario": "P1.4-D",
        "category": "Filtres Explicites",
        "title": "Multi-filtres combinés (gravité + statut + canal)",
        "question": "Réclamations graves insatisfaites du canal Web",
        "expected": {
            "filters": [
                {"concept_id": "risk_level", "value": "GRAVE"},
                {"concept_id": "status", "value": "UNSATISFIED"},
                {"concept_id": "channel", "value": "Web"},
            ],
        },
    },

    # -------------------------------------------------------------------------
    # Sous-step P1.5 : Période Temporelle (time)
    # -------------------------------------------------------------------------
    {
        "id": 20,
        "scenario": "P1.5-A",
        "category": "Période Temporelle",
        "title": "Absence de date explicite",
        "question": "Nombre de réclamations par agence",
        "expected": {
            "time": None,
        },
    },
    {
        "id": 21,
        "scenario": "P1.5-B",
        "category": "Période Temporelle",
        "title": "Année civile complète",
        "question": "En 2026",
        "expected": {
            "time_start": "2026-01-01",
            "time_end": "2027-01-01",
        },
    },
    {
        "id": 22,
        "scenario": "P1.5-C",
        "category": "Période Temporelle",
        "title": "Mois explicite nommé",
        "question": "En mars 2026",
        "expected": {
            "time_start": "2026-03-01",
            "time_end": "2026-04-01",
        },
    },
    {
        "id": 23,
        "scenario": "P1.5-D",
        "category": "Période Temporelle",
        "title": "Trimestre",
        "question": "Premier trimestre 2026",
        "expected": {
            "time_start": "2026-01-01",
            "time_end": "2026-04-01",
        },
    },
    {
        "id": 24,
        "scenario": "P1.5-E",
        "category": "Période Temporelle",
        "title": "Expression relative (ce mois-ci)",
        "question": "Ce mois-ci",
        "expected": {
            "time_relative": True,
        },
    },
]
