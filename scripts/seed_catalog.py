#!/usr/bin/env python3
"""
Script d'amorçage indépendant du catalogue de requêtes certifiées et des métriques métier.

Ce script extrait la définition des requêtes homologuées de référence hors du code source Python.
Il peuple ou synchronise directement la table `reporting_certified_queries` et `reporting_business_metrics`
dans MySQL (ou SQLite) avec calcul automatique des intent_hash.

Usage :
    python scripts/seed_catalog.py
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import sys
from typing import Any, Dict

# Encodage console UTF-8 Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Ajouter la racine du projet au sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.models import ReportingCertifiedQuery, ReportingBusinessMetric
from app.db.session import SessionLocal, engine
from app.reporting.text_to_sql_contracts import (
    ApprovalStatus,
    CandidateParameter,
    QueryCatalogEntry,
    TextToSQLIntent,
)
from app.reporting.query_catalog import compute_canonical_intent_hash

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# DÉFINITIONS CANONIQUES DES 8 REQUÊTES HOMOLOGUÉES DE RÉFÉRENCE
# -----------------------------------------------------------------------------

INITIAL_CERTIFIED_QUERIES_DATA = [
    {
        "id": "QC-UNIFIED-PLAINTES-TOTAL",
        "contract_version": "1.0",
        "natural_language_query": "Volume total unifié des plaintes (réclamations, dénonciations, suggestions)",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["CLAIM", "DENUNCIATION", "SUGGESTION"], "include_all_types": True},
            "measure": {"concept_id": "plainte_count", "operation": "count", "target_concept": "plainte", "label": "Total unifié des plaintes"},
            "dimensions": [],
            "filters": [],
            "time": {"field_concept": "receipt_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= :start_date AND receipt_at < :end_date) + "
            "(SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= :start_date AND recorded_at < :end_date)) "
            "AS plainte_count"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-CLAIM-COUNT-BY-AGENCY",
        "contract_version": "1.0",
        "natural_language_query": "Nombre de réclamations par agence sur une période",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": False},
            "measure": {"concept_id": "reclamation_count", "operation": "count", "target_concept": "plainte", "label": "Nombre de réclamations"},
            "dimensions": [{"concept_id": "agency", "label": "Agence"}],
            "filters": [],
            "time": {"field_concept": "receipt_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle "
            "ORDER BY case_count DESC"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-CLAIM-COUNT-BY-CHANNEL",
        "contract_version": "1.0",
        "natural_language_query": "Nombre de réclamations par canal de collecte",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": False},
            "measure": {"concept_id": "reclamation_count", "operation": "count", "target_concept": "plainte", "label": "Nombre de réclamations"},
            "dimensions": [{"concept_id": "channel", "label": "Canal"}],
            "filters": [],
            "time": {"field_concept": "receipt_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT cc.libelle AS channel, COUNT(c.id) AS case_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id "
            "WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY cc.libelle "
            "ORDER BY case_count DESC"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-SEVERE-PLAINTES-BY-AGENCY",
        "contract_version": "1.0",
        "natural_language_query": "Nombre de réclamations graves par agence",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": False},
            "measure": {"concept_id": "severe_plainte_count", "operation": "count", "target_concept": "plainte", "label": "Plaintes graves"},
            "dimensions": [{"concept_id": "agency", "label": "Agence"}],
            "filters": [],
            "time": {"field_concept": "receipt_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT sp.libelle AS agency, COUNT(c.id) AS severe_count "
            "FROM reporting_claim c "
            "LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id "
            "WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'GRAVE' "
            "AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "GROUP BY sp.libelle "
            "ORDER BY severe_count DESC"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-SATISFACTION-RATE",
        "contract_version": "1.0",
        "natural_language_query": "Taux de satisfaction global des usagers",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": False},
            "measure": {"concept_id": "satisfaction_rate", "operation": "rate", "target_concept": "plainte", "label": "Taux de satisfaction"},
            "dimensions": [],
            "filters": [],
            "time": {"field_concept": "receipt_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate "
            "FROM reporting_claim c "
            "WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "AND c.satisfaction_status IS NOT NULL"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-SLA-ADHERENCE-RATE",
        "contract_version": "1.0",
        "natural_language_query": "Taux global de respect des délais SLA",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["CLAIM"], "include_all_types": False},
            "measure": {"concept_id": "sla_adherence_rate", "operation": "rate", "target_concept": "plainte", "label": "Taux de respect SLA"},
            "dimensions": [],
            "filters": [],
            "time": {"field_concept": "receipt_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT AVG(CASE WHEN c.resolved_at <= c.sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate "
            "FROM reporting_claim c "
            "WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date "
            "AND c.resolved_at IS NOT NULL"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-SUGGESTIONS-BY-IMPACT",
        "contract_version": "1.0",
        "natural_language_query": "Nombre de suggestions par niveau d'impact",
        "canonical_intent": {
            "entity": {"concept_id": "plainte", "types": ["SUGGESTION"], "include_all_types": False},
            "measure": {"concept_id": "suggestion_count", "operation": "count", "target_concept": "suggestion", "label": "Nombre de suggestions"},
            "dimensions": [{"concept_id": "impact_level", "label": "Niveau d'impact"}],
            "filters": [],
            "time": {"field_concept": "recorded_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT s.impact_level, COUNT(s.id) AS suggestion_count "
            "FROM reporting_suggestion s "
            "WHERE s.recorded_at >= :start_date AND s.recorded_at < :end_date "
            "GROUP BY s.impact_level "
            "ORDER BY suggestion_count DESC"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
    {
        "id": "QC-REAFFECTATION-COUNT",
        "contract_version": "1.0",
        "natural_language_query": "Nombre de réaffectations de dossiers",
        "canonical_intent": {
            "entity": {"concept_id": "treatment", "types": ["CLAIM", "DENUNCIATION", "SUGGESTION"], "include_all_types": True},
            "measure": {"concept_id": "reaffectation_count", "operation": "count", "target_concept": "treatment", "label": "Nombre de réaffectations"},
            "dimensions": [],
            "filters": [],
            "time": {"field_concept": "created_date", "start_date": "2026-01-01", "end_date": "2026-12-31", "timezone": "Africa/Porto-Novo"},
            "status": "ready",
        },
        "parameterized_sql": (
            "SELECT COUNT(h.id) AS reaffectation_count "
            "FROM reporting_historique_affectations h "
            "WHERE h.affectation_precedente_id IS NOT NULL "
            "AND h.date_affectation >= :start_date AND h.date_affectation < :end_date"
        ),
        "parameters_schema": {
            "start_date": {"type": "datetime", "source": "intent.time.start_date"},
            "end_date": {"type": "datetime", "source": "intent.time.end_date"},
        },
        "status": "APPROVED",
        "created_by": "system",
        "approved_by": "admin",
        "approved_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "schema_version": "1.0.0",
    },
]


def seed_certified_queries(db: Any) -> int:
    """Insère ou met à jour les 8 requêtes de référence homologuées avec calcul d'intent_hash."""
    count = 0
    for q_data in INITIAL_CERTIFIED_QUERIES_DATA:
        intent_obj = TextToSQLIntent(**q_data["canonical_intent"])
        intent_hash = compute_canonical_intent_hash(intent_obj)

        row = db.query(ReportingCertifiedQuery).filter_by(id=q_data["id"]).first()
        if not row:
            row = ReportingCertifiedQuery(
                id=q_data["id"],
                intent_hash=intent_hash,
                contract_version=q_data["contract_version"],
                natural_language_query=q_data["natural_language_query"],
                canonical_intent=q_data["canonical_intent"],
                parameterized_sql=q_data["parameterized_sql"],
                parameters_schema=q_data["parameters_schema"],
                status=q_data["status"],
                created_by=q_data["created_by"],
                approved_by=q_data["approved_by"],
                approved_at=q_data["approved_at"],
                schema_version=q_data["schema_version"],
            )
            db.add(row)
            count += 1
        else:
            row.intent_hash = intent_hash
            row.canonical_intent = q_data["canonical_intent"]
            row.parameterized_sql = q_data["parameterized_sql"]
            row.parameters_schema = q_data["parameters_schema"]
            row.status = q_data["status"]
            count += 1

    db.commit()
    logger.info(f"✅ {count} requêtes certifiées de référence synchronisées avec intent_hash.")
    return count


def main():
    logger.info("🚀 Démarrage du script d'amorçage indépendant du catalogue...")
    session = SessionLocal()
    try:
        from app.reporting.business_catalog import sync_metrics_with_db
        logger.info("1. Synchronisation des métriques métier...")
        sync_metrics_with_db(session)

        logger.info("2. Amorçage des 8 requêtes certifiées de référence...")
        seed_certified_queries(session)

        logger.info("✨ Amorçage du catalogue terminé avec succès.")
    except Exception as e:
        logger.error(f"❌ Échec de l'amorçage : {e}")
        db.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
