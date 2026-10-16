#!/usr/bin/env python3
"""
Générateur Multi-Vagues de l'Oracle de Vérité Terrain (Ground Truth Oracle).
Couvre l'ensemble des cohortes de tests : Vague 01, Vague 02, Vague 03 et Vague 04.

Ce script exécute les requêtes de référence canoniques sur la base MariaDB gpr_ai_reporting
et sérialise les résultats attendus exacts dans tests/fixtures/ground_truth_vague_XX.json.
Ces résultats servent d'oracle objectif pour l'évaluation de l'Axe 1 (Exactitude Métier).
"""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys

# Encodage console UTF-8 Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ORACLE_DEFINITIONS_VAGUE_01 = [
    {
        "id": 1,
        "question": "Combien de réclamations ?",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE claim_type = 'CLAIM'",
        "metric_type": "scalar",
        "description": "Comptage des réclamations",
    },
    {
        "id": 2,
        "question": "Quelles sont les dénonciations enregistrées ?",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION')",
        "metric_type": "scalar",
        "description": "Comptage des dénonciations",
    },
    {
        "id": 3,
        "question": "Nombre d'idées et suggestions d'amélioration",
        "sql": "SELECT COUNT(*) AS total FROM reporting_suggestion",
        "metric_type": "scalar",
        "description": "Comptage des suggestions",
    },
    {
        "id": 4,
        "question": "Volume total de dossiers reçus par la banque",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim",
        "metric_type": "scalar",
        "description": "Volume total tous dossiers reçus",
    },
    {
        "id": 5,
        "question": "Combien de transferts de dossiers ont eu lieu ?",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE status = 'TRANSFER'",
        "metric_type": "scalar",
        "description": "Transferts / réaffectations",
    },
    {
        "id": 6,
        "question": "Plaintes",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim",
        "metric_type": "scalar",
        "description": "Total unifié plainte_count",
    },
    {
        "id": 7,
        "question": "Réclamations moyennes",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE claim_type = 'CLAIM' AND (risk_level = 'MOYEN' OR ai_urgency = 'MOYEN')",
        "metric_type": "scalar",
        "description": "Réclamations de risque moyen",
    },
    {
        "id": 8,
        "question": "Taux de respect des engagements SLA",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate FROM reporting_claim WHERE claim_type = 'CLAIM'"
        ),
        "metric_type": "rate",
        "description": "Taux SLA global réclamations",
    },
    {
        "id": 9,
        "question": "Pourcentage d'usagers satisfaits",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim"
        ),
        "metric_type": "rate",
        "description": "Taux de satisfaction global",
    },
    {
        "id": 10,
        "question": "Score moyen de risque estimé",
        "sql": "SELECT ROUND(AVG(ai_risk_score), 2) AS avg_score FROM reporting_claim WHERE ai_risk_score IS NOT NULL",
        "metric_type": "scalar",
        "description": "Score moyen de risque IA",
    },
    {
        "id": 11,
        "question": "Réclamations par agence",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations ventilées par agence",
    },
    {
        "id": 12,
        "question": "Dossiers par canal de collecte",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, COUNT(*) AS total "
            "FROM reporting_claim GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Dossiers ventilés par canal",
    },
    {
        "id": 13,
        "question": "Suggestions selon le niveau d'impact",
        "sql": (
            "SELECT COALESCE(impact_level, 'Non spécifié') AS impact_level, COUNT(*) AS total "
            "FROM reporting_suggestion GROUP BY COALESCE(impact_level, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Suggestions par impact",
    },
    {
        "id": 14,
        "question": "Réclamations par agence et par canal",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "COALESCE(channel, 'Non spécifié') AS channel_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié'), COALESCE(channel, 'Non spécifié') "
            "ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations croisées agence x canal",
    },
    {
        "id": 15,
        "question": "Total des réclamations",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE claim_type = 'CLAIM'",
        "metric_type": "scalar",
        "description": "Total des réclamations",
    },
    {
        "id": 16,
        "question": "Réclamations graves",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE')"
        ),
        "metric_type": "scalar",
        "description": "Réclamations graves / élevées",
    },
    {
        "id": 17,
        "question": "Plaintes critiques ou lourdes",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE')"
        ),
        "metric_type": "scalar",
        "description": "Plaintes globales graves",
    },
    {
        "id": 18,
        "question": "Dossiers insatisfaits",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE status = 'UNSATISFIED'",
        "metric_type": "scalar",
        "description": "Dossiers au statut insatisfait",
    },
    {
        "id": 19,
        "question": "Réclamations graves insatisfaites du canal Web",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND status = 'UNSATISFIED' AND channel = 'WEB'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations graves insatisfaites WEB",
    },
    {
        "id": 20,
        "question": "Nombre de réclamations par agence",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations ventilées par agence",
    },
    {
        "id": 21,
        "question": "En 2026",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'",
        "metric_type": "scalar",
        "description": "Volume dossiers 2026",
    },
    {
        "id": 22,
        "question": "En mars 2026",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE receipt_at >= '2026-03-01' AND receipt_at < '2026-04-01'",
        "metric_type": "scalar",
        "description": "Volume dossiers mars 2026",
    },
    {
        "id": 23,
        "question": "Premier trimestre 2026",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE receipt_at >= '2026-01-01' AND receipt_at < '2026-04-01'",
        "metric_type": "scalar",
        "description": "Volume dossiers T1 2026",
    },
    {
        "id": 24,
        "question": "Ce mois-ci",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE receipt_at >= '2026-10-01' AND receipt_at < '2026-11-01'",
        "metric_type": "scalar",
        "description": "Volume dossiers octobre 2026",
    },
]

ORACLE_DEFINITIONS_VAGUE_02 = [
    {
        "id": 1,
        "question": "Nombre de réclamations en cours au premier trimestre 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status != 'SATISFIED' "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2026-04-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations non résolues T1 2026",
    },
    {
        "id": 2,
        "question": "Réclamations graves reçues en mars 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND receipt_at >= '2026-03-01' AND receipt_at < '2026-04-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations graves mars 2026",
    },
    {
        "id": 3,
        "question": "Dossiers de réclamation par agence pour le canal Guichet",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND channel IN ('GUICHET', 'AGENCE', 'Physique') "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations canal physique par agence",
    },
    {
        "id": 4,
        "question": "Répartition des réclamations par catégorie de produit en 2026",
        "sql": (
            "SELECT COALESCE(product, category, 'Non spécifié') AS product_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(product, category, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations par produit 2026",
    },
    {
        "id": 5,
        "question": "Nombre de réclamations traitées et satisfaites par agence",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status = 'SATISFIED' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations satisfaites par agence",
    },
    {
        "id": 6,
        "question": "Réclamations urgentes ou critiques de l'Agence Littoral",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND (agency LIKE '%Littoral%' OR service_point LIKE '%Littoral%')"
        ),
        "metric_type": "scalar",
        "description": "Réclamations urgentes Agence Littoral",
    },
    {
        "id": 7,
        "question": "Volume de dénonciations par statut en 2026",
        "sql": (
            "SELECT COALESCE(status, 'Non spécifié') AS status_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(status, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Dénonciations par statut en 2026",
    },
    {
        "id": 8,
        "question": "Suggestions d'amélioration adoptées par catégorie d'impact",
        "sql": (
            "SELECT COALESCE(impact_level, 'Non spécifié') AS impact_level, COUNT(*) AS total "
            "FROM reporting_suggestion "
            "WHERE status IN ('APPROVED', 'ADOPTED', 'VALIDATED') "
            "GROUP BY COALESCE(impact_level, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Suggestions adoptées par impact",
    },
    {
        "id": 9,
        "question": "Réclamations reçues entre le 01/01/2026 et le 30/06/2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at <= '2026-06-30 23:59:59'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations du premier semestre 2026",
    },
    {
        "id": 10,
        "question": "Nombre de dossiers en souffrance ou en cours par agence",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE status != 'SATISFIED' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Dossiers non clôturés par agence",
    },
    {
        "id": 11,
        "question": "Réclamations par agence avec statut CLOTURE",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status IN ('CLOTURE', 'SATISFIED', 'CLOSED') "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations clôturées par agence",
    },
    {
        "id": 12,
        "question": "Doléances par canal de collecte pour les réclamations moyennes",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level = 'MOYEN' OR ai_urgency = 'MOYEN') "
            "GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations moyennes par canal",
    },
    {
        "id": 13,
        "question": "Suggestions selon le statut au premier semestre 2026",
        "sql": (
            "SELECT COALESCE(status, 'Non spécifié') AS status_name, COUNT(*) AS total "
            "FROM reporting_suggestion "
            "WHERE recorded_at >= '2026-01-01' AND recorded_at < '2026-07-01' "
            "GROUP BY COALESCE(status, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Suggestions par statut S1 2026",
    },
    {
        "id": 14,
        "question": "Nombre de réclamations graves par canal en 2026",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations graves par canal 2026",
    },
    {
        "id": 15,
        "question": "Dénonciations selon le niveau de risque en 2026",
        "sql": (
            "SELECT COALESCE(risk_level, 'Non spécifié') AS risk_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(risk_level, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Dénonciations par risque 2026",
    },
    {
        "id": 16,
        "question": "Réclamations non satisfaites par agence",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status = 'UNSATISFIED' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Réclamations insatisfaites par agence",
    },
    {
        "id": 17,
        "question": "Volume de dossiers reçus par le canal Mobile en 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE (channel LIKE '%MOBILE%' OR channel LIKE '%APP%') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Dossiers canal Mobile 2026",
    },
    {
        "id": 18,
        "question": "Plaintes avec statut AFFECTED au premier trimestre 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE status = 'AFFECTED' AND receipt_at >= '2026-01-01' AND receipt_at < '2026-04-01'"
        ),
        "metric_type": "scalar",
        "description": "Plaintes affectées T1 2026",
    },
    {
        "id": 19,
        "question": "Nombre de litiges par objet et par agence",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "COALESCE(motif, category, 'Non spécifié') AS motif_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié'), COALESCE(motif, category, 'Non spécifié') "
            "ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Litiges croisés agence x motif",
    },
    {
        "id": 20,
        "question": "Suggestions par canal de collecte",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, COUNT(*) AS total "
            "FROM reporting_suggestion "
            "GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Suggestions par canal",
    },
    {
        "id": 21,
        "question": "Réclamations fermées ou résolues en 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status IN ('SATISFIED', 'CLOTURE', 'CLOSED') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations résolues / fermées 2026",
    },
    {
        "id": 22,
        "question": "Dénonciations enregistrées par l'Agence Atlantique",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND (agency LIKE '%Atlantique%' OR service_point LIKE '%Atlantique%')"
        ),
        "metric_type": "scalar",
        "description": "Dénonciations Agence Atlantique",
    },
    {
        "id": 23,
        "question": "Réclamations mineures reçues en février 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('MINEUR', 'FAIBLE') OR ai_urgency = 'MINEUR') "
            "AND receipt_at >= '2026-02-01' AND receipt_at < '2026-03-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations mineures février 2026",
    },
    {
        "id": 24,
        "question": "Taux de respect SLA par agence en 2026",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY sla_rate DESC"
        ),
        "metric_type": "breakdown",
        "description": "Taux SLA par agence en 2026",
    },
]

ORACLE_DEFINITIONS_VAGUE_03 = [
    {
        "id": 1,
        "question": "Taux de respect des délais SLA par agence en 2026",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY sla_rate DESC"
        ),
        "metric_type": "breakdown",
        "description": "Taux SLA par agence 2026",
    },
    {
        "id": 2,
        "question": "Top 3 des agences avec le plus grand nombre de réclamations",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC LIMIT 3"
        ),
        "metric_type": "breakdown",
        "description": "Top 3 agences volume réclamations",
    },
    {
        "id": 3,
        "question": "Délai moyen de traitement des réclamations par canal en 2026",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, "
            "ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND resolved_at IS NOT NULL "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY avg_days DESC"
        ),
        "metric_type": "breakdown",
        "description": "Délai moyen traitement par canal 2026",
    },
    {
        "id": 4,
        "question": "Taux de satisfaction des usagers par canal de collecte",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, "
            "ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY satisfaction_rate DESC"
        ),
        "metric_type": "breakdown",
        "description": "Satisfaction par canal de collecte",
    },
    {
        "id": 5,
        "question": "Pourcentage de respect des SLA pour les réclamations de l'Agence Abidjan",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (agency LIKE '%Abidjan%' OR service_point LIKE '%Abidjan%')"
        ),
        "metric_type": "rate",
        "description": "Respect SLA Agence Abidjan",
    },
    {
        "id": 6,
        "question": "Top 5 des motifs de réclamations les plus fréquents en 2026",
        "sql": (
            "SELECT COALESCE(motif, category, 'Non spécifié') AS motif_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(motif, category, 'Non spécifié') ORDER BY total DESC LIMIT 5"
        ),
        "metric_type": "breakdown",
        "description": "Top 5 motifs réclamations 2026",
    },
    {
        "id": 7,
        "question": "Délai moyen de résolution des dossiers pour l'Agence Bouaké",
        "sql": (
            "SELECT ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE (agency LIKE '%Bouaké%' OR service_point LIKE '%Bouaké%') AND resolved_at IS NOT NULL"
        ),
        "metric_type": "scalar",
        "description": "Délai moyen de résolution Agence Bouaké",
    },
    {
        "id": 8,
        "question": "Taux de respect des délais SLA par niveau de risque",
        "sql": (
            "SELECT COALESCE(risk_level, 'Non spécifié') AS risk_level, "
            "ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(risk_level, 'Non spécifié') ORDER BY sla_rate DESC"
        ),
        "metric_type": "breakdown",
        "description": "Taux SLA par risque",
    },
    {
        "id": 9,
        "question": "Classement des agences par délai moyen de traitement en 2026",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND resolved_at IS NOT NULL "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY avg_days ASC"
        ),
        "metric_type": "breakdown",
        "description": "Classement agences délai moyen 2026",
    },
    {
        "id": 10,
        "question": "Taux de satisfaction des réclamations pour le canal WEB",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim WHERE channel = 'WEB'"
        ),
        "metric_type": "rate",
        "description": "Satisfaction client canal WEB",
    },
    {
        "id": 11,
        "question": "Top 3 des canaux de collecte avec le plus fort volume de réclamations",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, COUNT(*) AS total "
            "FROM reporting_claim WHERE claim_type = 'CLAIM' "
            "GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY total DESC LIMIT 3"
        ),
        "metric_type": "breakdown",
        "description": "Top 3 canaux collecte réclamations",
    },
    {
        "id": 12,
        "question": "Nombre moyen de jours de traitement des réclamations reçues en août 2026",
        "sql": (
            "SELECT ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-08-01' AND receipt_at < '2026-09-01' "
            "AND resolved_at IS NOT NULL"
        ),
        "metric_type": "scalar",
        "description": "Délai moyen réclamations août 2026",
    },
    {
        "id": 13,
        "question": "Taux de respect SLA pour les réclamations enregistrées en juillet 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-07-01' AND receipt_at < '2026-08-01'"
        ),
        "metric_type": "rate",
        "description": "Taux SLA réclamations juillet 2026",
    },
    {
        "id": 14,
        "question": "Top 3 des agences ayant le meilleur taux de respect SLA en 2026",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY sla_rate DESC LIMIT 3"
        ),
        "metric_type": "breakdown",
        "description": "Top 3 agences respect SLA 2026",
    },
    {
        "id": 15,
        "question": "Délai moyen de traitement des plaintes graves en 2026",
        "sql": (
            "SELECT ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' AND resolved_at IS NOT NULL"
        ),
        "metric_type": "scalar",
        "description": "Délai moyen dossiers graves 2026",
    },
    {
        "id": 16,
        "question": "Taux de satisfaction global des réclamations en 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "rate",
        "description": "Satisfaction globale réclamations 2026",
    },
    {
        "id": 17,
        "question": "Classement des canaux de collecte selon le taux de satisfaction usagers",
        "sql": (
            "SELECT COALESCE(channel, 'Non spécifié') AS channel_name, "
            "ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim GROUP BY COALESCE(channel, 'Non spécifié') ORDER BY satisfaction_rate DESC"
        ),
        "metric_type": "breakdown",
        "description": "Classement canaux par satisfaction",
    },
    {
        "id": 18,
        "question": "Top 5 des dossiers avec le délai de traitement le plus long",
        "sql": (
            "SELECT id, source_code, DATEDIFF(resolved_at, receipt_at) AS days "
            "FROM reporting_claim WHERE resolved_at IS NOT NULL ORDER BY days DESC LIMIT 5"
        ),
        "metric_type": "breakdown",
        "description": "Top 5 dossiers délai résolution le plus long",
    },
    {
        "id": 19,
        "question": "Taux de respect des SLA pour les réclamations reçues via le canal AGENCE",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND channel IN ('AGENCE', 'Physique', 'GUICHET')"
        ),
        "metric_type": "rate",
        "description": "Respect SLA canal agence",
    },
    {
        "id": 20,
        "question": "Délai moyen de traitement des réclamations par agence en 2026",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, "
            "ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND resolved_at IS NOT NULL "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY avg_days ASC"
        ),
        "metric_type": "breakdown",
        "description": "Délai moyen traitement par agence 2026",
    },
    {
        "id": 21,
        "question": "Taux de satisfaction des usagers pour l'Agence Korhogo en 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim "
            "WHERE (agency LIKE '%Korhogo%' OR service_point LIKE '%Korhogo%') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "rate",
        "description": "Satisfaction usagers Korhogo 2026",
    },
    {
        "id": 22,
        "question": "Top 3 des motifs de dénonciations enregistrées en 2026",
        "sql": (
            "SELECT COALESCE(motif, category, 'Non spécifié') AS motif_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY COALESCE(motif, category, 'Non spécifié') ORDER BY total DESC LIMIT 3"
        ),
        "metric_type": "breakdown",
        "description": "Top 3 motifs dénonciations 2026",
    },
    {
        "id": 23,
        "question": "Taux de respect des délais SLA pour les dossiers de niveau de risque moyen",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE (risk_level = 'MOYEN' OR ai_urgency = 'MOYEN')"
        ),
        "metric_type": "rate",
        "description": "Respect SLA risque moyen",
    },
    {
        "id": 24,
        "question": "Classement des agences par volume total de réclamations traitées",
        "sql": (
            "SELECT COALESCE(agency, service_point, 'Non spécifié') AS agency_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status IN ('TREAT', 'SATISFIED', 'UNSATISFIED') "
            "GROUP BY COALESCE(agency, service_point, 'Non spécifié') ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Classement agences volume réclamations traitées",
    },
]

ORACLE_DEFINITIONS_VAGUE_04 = [
    {
        "id": 1,
        "question": "Quels sont les dossiers en cours qui ne sont toujours pas résolus ?",
        "sql": "SELECT COUNT(*) AS total FROM reporting_claim WHERE status != 'SATISFIED'",
        "metric_type": "scalar",
        "description": "Tous les dossiers avec status != 'SATISFIED' (AFFECTED, SAVED, TREAT, CLASSED, UNSATISFIED)",
    },
    {
        "id": 2,
        "question": "Réclamations des clients mécontents reçues hors agence physique",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status = 'UNSATISFIED' "
            "AND channel NOT IN ('AGENCE', 'Physique')"
        ),
        "metric_type": "scalar",
        "description": "Réclamations avec status='UNSATISFIED' hors AGENCE/Physique",
    },
    {
        "id": 3,
        "question": "Nombre de dossiers critiques ou graves en attente de traitement",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND status != 'SATISFIED'"
        ),
        "metric_type": "scalar",
        "description": "Dossiers graves/critiques non clôturés",
    },
    {
        "id": 4,
        "question": "Taux de respect des délais pour les réclamations de niveau critique en 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "rate",
        "description": "Taux de respect SLA pour réclamations critiques en 2026",
    },
    {
        "id": 5,
        "question": "Signalements de fraudes et irrégularités enregistrés sans passer par le guichet",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND channel NOT IN ('AGENCE', 'Physique')"
        ),
        "metric_type": "scalar",
        "description": "Dénonciations hors canaux physiques",
    },
    {
        "id": 6,
        "question": "Délai moyen de résolution des dossiers traités pour les clients insatisfaits",
        "sql": (
            "SELECT ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE status = 'UNSATISFIED' AND resolved_at IS NOT NULL"
        ),
        "metric_type": "scalar",
        "description": "Délai moyen en jours pour les dossiers résolus insatisfaits",
    },
    {
        "id": 7,
        "question": "Total des réclamations reçues sur le canal téléphonique au cours de l'été 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND channel = 'TELEPHONE' "
            "AND receipt_at >= '2026-06-01' AND receipt_at < '2026-09-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations téléphoniques de l'été 2026 (juin à août inclus)",
    },
    {
        "id": 8,
        "question": "Propositions d'amélioration et suggestions enregistrées en 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_suggestion "
            "WHERE recorded_at >= '2026-01-01' AND recorded_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Suggestions enregistrées en 2026",
    },
    {
        "id": 9,
        "question": "Taux de satisfaction des usagers pour les dossiers résolus hors délai",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim "
            "WHERE resolved_at IS NOT NULL AND resolved_at > sla_due_at"
        ),
        "metric_type": "rate",
        "description": "Satisfaction sur dossiers résolus en retard",
    },
    {
        "id": 10,
        "question": "Dossiers de réclamations mineures enregistrés pour l'Agence Bouaké",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (risk_level IN ('MINEUR', 'FAIBLE') OR ai_urgency = 'MINEUR') "
            "AND (agency LIKE '%Bouaké%' OR service_point LIKE '%Bouaké%')"
        ),
        "metric_type": "scalar",
        "description": "Réclamations mineures à l'Agence Bouaké",
    },
    {
        "id": 11,
        "question": "Pourcentage de respect des SLA pour les signalements graves en 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND (risk_level IN ('GRAVE', 'ELEVE') OR ai_urgency = 'GRAVE') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "rate",
        "description": "Respect SLA sur dénonciations graves",
    },
    {
        "id": 12,
        "question": "Nombre de réclamations ouvertes et non clôturées à ce jour en 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status != 'SATISFIED' "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations ouvertes (status != 'SATISFIED') en 2026",
    },
    {
        "id": 13,
        "question": "Répartition des dossiers mécontents par motif au troisième trimestre 2026",
        "sql": (
            "SELECT COALESCE(motif, category, 'Non spécifié') AS motif_name, COUNT(*) AS total "
            "FROM reporting_claim "
            "WHERE status = 'UNSATISFIED' "
            "AND receipt_at >= '2026-07-01' AND receipt_at < '2026-10-01' "
            "GROUP BY COALESCE(motif, category, 'Non spécifié') "
            "ORDER BY total DESC"
        ),
        "metric_type": "breakdown",
        "description": "Répartition par motif des clients insatisfaits au T3 2026",
    },
    {
        "id": 14,
        "question": "Taux de respect des engagements de délai pour l'Agence Korhogo en 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE (agency LIKE '%Korhogo%' OR service_point LIKE '%Korhogo%') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "rate",
        "description": "Respect SLA à Korhogo en 2026",
    },
    {
        "id": 15,
        "question": "Nombre de dénonciations anonymes ou signalements traités en 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type IN ('DENUNCIATION', 'DENUNCIACION') "
            "AND status IN ('TREAT', 'SATISFIED', 'UNSATISFIED') "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Dénonciations traitées (TREAT, SATISFIED, UNSATISFIED) en 2026",
    },
    {
        "id": 16,
        "question": "Dossiers urgents transmis via le canal web en septembre 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE channel = 'WEB' AND (ai_urgency = 'GRAVE' OR risk_level IN ('GRAVE', 'ELEVE')) "
            "AND receipt_at >= '2026-09-01' AND receipt_at < '2026-10-01'"
        ),
        "metric_type": "scalar",
        "description": "Dossiers urgents WEB en septembre 2026",
    },
    {
        "id": 17,
        "question": "Taux de satisfaction des clients ayant déposé une plainte via le téléphone",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(CASE WHEN status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate "
            "FROM reporting_claim "
            "WHERE channel = 'TELEPHONE'"
        ),
        "metric_type": "rate",
        "description": "Satisfaction client canal téléphonique",
    },
    {
        "id": 18,
        "question": "Réclamations traitées avec succès avant échéance pour l'Agence Abidjan",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND (agency LIKE '%Abidjan%' OR service_point LIKE '%Abidjan%') "
            "AND status = 'SATISFIED' AND resolved_at <= sla_due_at"
        ),
        "metric_type": "scalar",
        "description": "Réclamations résolues dans les délais à Abidjan",
    },
    {
        "id": 19,
        "question": "Délai moyen de clôture des dossiers de réclamation en septembre 2026",
        "sql": (
            "SELECT ROUND(AVG(DATEDIFF(resolved_at, receipt_at)), 2) AS avg_days "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status = 'SATISFIED' "
            "AND receipt_at >= '2026-09-01' AND receipt_at < '2026-10-01'"
        ),
        "metric_type": "scalar",
        "description": "Délai moyen de clôture en septembre 2026",
    },
    {
        "id": 20,
        "question": "Nombre total de doléances clients enregistrées sur toute l'année 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Volume total des réclamations en 2026",
    },
    {
        "id": 21,
        "question": "Taux de respect SLA pour les réclamations reçues par voie digitale en 2026",
        "sql": (
            "SELECT ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND channel = 'WEB' "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "rate",
        "description": "Taux SLA voie digitale (WEB) en 2026",
    },
    {
        "id": 22,
        "question": "Dossiers avec niveau de risque moyen clôturés avec satisfaction",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE (risk_level = 'MOYEN' OR ai_urgency = 'MOYEN') AND status = 'SATISFIED'"
        ),
        "metric_type": "scalar",
        "description": "Dossiers de risque moyen clôturés satisfaits",
    },
    {
        "id": 23,
        "question": "Proportion de réclamations respectant le délai imparti par canal en 2026",
        "sql": (
            "SELECT channel, ROUND(COUNT(CASE WHEN (resolved_at IS NOT NULL AND resolved_at <= sla_due_at) "
            "OR (resolved_at IS NULL AND sla_due_at >= '2026-10-15') THEN 1 END) * 100.0 / "
            "NULLIF(COUNT(*), 0), 2) AS sla_rate "
            "FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01' "
            "GROUP BY channel "
            "ORDER BY sla_rate DESC"
        ),
        "metric_type": "breakdown",
        "description": "Respect SLA par canal pour les réclamations 2026",
    },
    {
        "id": 24,
        "question": "Volume global de dossiers de réclamation non satisfaits en 2026",
        "sql": (
            "SELECT COUNT(*) AS total FROM reporting_claim "
            "WHERE claim_type = 'CLAIM' AND status = 'UNSATISFIED' "
            "AND receipt_at >= '2026-01-01' AND receipt_at < '2027-01-01'"
        ),
        "metric_type": "scalar",
        "description": "Réclamations non satisfaites en 2026",
    },
]

WAVES_MAP = {
    "01": ("Vague 01", ORACLE_DEFINITIONS_VAGUE_01, "ground_truth_vague_01.json"),
    "02": ("Vague 02", ORACLE_DEFINITIONS_VAGUE_02, "ground_truth_vague_02.json"),
    "03": ("Vague 03", ORACLE_DEFINITIONS_VAGUE_03, "ground_truth_vague_03.json"),
    "04": ("Vague 04", ORACLE_DEFINITIONS_VAGUE_04, "ground_truth_vague_04.json"),
}


def generate_single_wave(wave_key: str, db, fixtures_dir: Path):
    title, definitions, out_filename = WAVES_MAP[wave_key]
    out_file = fixtures_dir / out_filename
    oracle_data = []

    print("\n" + "=" * 80)
    print(f"CALCUL DE L'ORACLE DE VÉRITÉ TERRAIN SUR MARIADB ({title.upper()})")
    print("=" * 80)

    for item in definitions:
        res = db.execute(text(item["sql"])).fetchall()

        if item["metric_type"] in ("scalar", "rate"):
            val = res[0][0] if res and res[0] else None
            expected_val = float(val) if val is not None else None
        else:
            # breakdown table
            clean_rows = []
            for row in res:
                d = {}
                for k, v in row._mapping.items():
                    if hasattr(v, "to_eng_string") or type(v).__name__ == "Decimal":
                        d[k] = float(v)
                    else:
                        d[k] = v
                clean_rows.append(d)
            expected_val = clean_rows

        entry = {
            "id": item["id"],
            "question": item["question"],
            "metric_type": item["metric_type"],
            "description": item["description"],
            "reference_sql": item["sql"],
            "expected_result": expected_val,
        }
        oracle_data.append(entry)
        print(f"[{item['id']:02d}] {item['question']}")
        print(f"     -> Résultat attendu : {expected_val}")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(oracle_data, f, indent=2, ensure_ascii=False)

    print("-" * 80)
    logger.info(f"✅ Oracle {title} généré avec succès dans : {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Générateur d'Oracle de Vérité Terrain Multi-Vagues")
    parser.add_argument(
        "--wave",
        "-w",
        type=str,
        default="all",
        choices=["01", "02", "03", "04", "all", "1", "2", "3", "4"],
        help="Vague cible (01, 02, 03, 04 ou all)",
    )
    args = parser.parse_args()

    wave_arg = args.wave.zfill(2) if args.wave != "all" else "all"

    db = SessionLocal()
    fixtures_dir = PROJECT_ROOT / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    try:
        if wave_arg == "all":
            for w in ["01", "02", "03", "04"]:
                generate_single_wave(w, db, fixtures_dir)
        else:
            generate_single_wave(wave_arg, db, fixtures_dir)
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("🎯 TOUS LES ORACLES DEMANDÉS ONT ÉTÉ CALCULÉS AVEC SUCCÈS")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
