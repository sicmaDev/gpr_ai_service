"""
Moteur d'exécution des questions pour l'interrogation du Workflow Text-to-SQL Gouverné.
Permet l'exécution en mode direct (in-process via SQLAlchemy) ou via l'API HTTP FastAPI.
"""

from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, Optional

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, SessionLocal
from app.reporting.intent_resolver import resolve_intent
from app.reporting.query_catalog import sync_queries_with_db
from app.reporting.text_to_sql_pipeline import execute_text_to_sql_pipeline

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """
    Exécuteur de questions pour le service de reporting analytique GPR.
    """

    def __init__(
        self,
        use_sqlite: bool = False,
        http_base_url: Optional[str] = None,
        use_llm: bool = True,
    ):
        self.use_sqlite = use_sqlite
        self.http_base_url = http_base_url.rstrip("/") if http_base_url else None
        self.use_llm = use_llm
        self.db_session: Optional[Session] = None
        self.db_engine: Optional[Any] = None

        if not self.http_base_url:
            self._init_database()

    def _init_database(self) -> None:
        """Initialise la session de base de données (MySQL obligatoire par défaut, SQLite uniquement si explicitement demandé)."""
        if not self.use_sqlite:
            try:
                # Test de connexion MySQL
                session = SessionLocal()
                session.execute(text("SELECT 1"))
                sync_queries_with_db(session)
                self.db_session = session
                logger.info("Connexion établie avec succès à la base MySQL (Unique Source de Vérité).")
                return
            except Exception as e:
                # Jamais de repli silencieux vers SQLite : lever une erreur explicite
                logger.error(f"Échec critique de connexion à MySQL : {e}")
                raise RuntimeError(
                    f"Impossible de se connecter à la base MySQL 'gpr_ai_reporting' : {e}. "
                    "Le repli silencieux vers SQLite a été désactivé par la gouvernance."
                )

        # Création et peuplement d'une base SQLite mémoire isolée avec jeu d'essai (uniquement si use_sqlite=True)
        logger.warning("WorkflowRunner: Mode SQLite mémoire explicite activé pour tests isolés.")
        self.db_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.db_engine)

        with self.db_engine.connect() as conn:
            # Création des tables de dimensions annexes
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS reporting_service_point ("
                    "id INTEGER PRIMARY KEY, libelle VARCHAR(100))"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS reporting_collection_channel ("
                    "id INTEGER PRIMARY KEY, libelle VARCHAR(100))"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS reporting_suggestion ("
                    "id INTEGER PRIMARY KEY, reference VARCHAR(64), impact_level VARCHAR(32))"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS reporting_historique_affectations ("
                    "id INTEGER PRIMARY KEY, date_affectation DATETIME, affectation_precedente_id INTEGER)"
                )
            )

            # Ajout des colonnes de jointure si nécessaire
            try:
                conn.execute(text("ALTER TABLE reporting_claim ADD COLUMN service_point_id INTEGER"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE reporting_claim ADD COLUMN collection_channel_id INTEGER"))
            except Exception:
                pass

            # Données de référence
            conn.execute(
                text(
                    "INSERT INTO reporting_service_point (id, libelle) VALUES "
                    "(1, 'Agence Littoral'), (2, 'Agence Atlantique'), (3, 'Agence Ouémé')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO reporting_collection_channel (id, libelle) VALUES "
                    "(1, 'Guichet'), (2, 'Application Mobile'), (3, 'Web')"
                )
            )

            # Données de réclamations analytiques
            conn.execute(
                text(
                    "INSERT INTO reporting_claim ("
                    "id, source_claim_id, source_code, claim_type, status, "
                    "service_point_id, collection_channel_id, risk_level, ai_urgency, "
                    "ai_risk_score, satisfaction_status, created_at, receipt_at, synced_at"
                    ") VALUES "
                    "(1, 101, 'REC-2026-001', 'CLAIM', 'EN_COURS', 1, 1, 'MINEUR', 'FAIBLE', 20.0, 'SATISFIED', '2026-03-01 10:00:00', '2026-03-01 10:00:00', '2026-03-01 10:00:00'), "
                    "(2, 102, 'REC-2026-002', 'CLAIM', 'TRAITE', 1, 3, 'GRAVE', 'GRAVE', 90.0, 'UNSATISFIED', '2026-03-05 11:00:00', '2026-03-05 11:00:00', '2026-03-05 11:00:00'), "
                    "(3, 103, 'DEN-2026-001', 'DENUNCIATION', 'CLOTURE', 2, 2, 'GRAVE', 'GRAVE', 85.0, 'SATISFIED', '2026-03-10 12:00:00', '2026-03-10 12:00:00', '2026-03-10 12:00:00'), "
                    "(4, 104, 'REC-2026-003', 'CLAIM', 'EN_COURS', 2, 3, 'MOYEN', 'MOYEN', 50.0, 'UNSATISFIED', '2026-03-15 14:00:00', '2026-03-15 14:00:00', '2026-03-15 14:00:00')"
                )
            )

            conn.commit()

        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.db_engine)
        self.db_session = session_factory()
        sync_queries_with_db(self.db_session)

    def execute_question(self, question: str) -> Dict[str, Any]:
        """
        Exécute une question à travers le Workflow Text-to-SQL Gouverné.
        Retourne un dictionnaire complet des métadonnées, étapes et résultats.
        """
        start_time = time.perf_counter()

        # 1. Mode HTTP si URL fournie
        if self.http_base_url:
            return self._execute_via_http(question, start_time)

        # 2. Mode In-Process direct
        return self._execute_in_process(question, start_time)

    def _execute_in_process(self, question: str, start_time: float) -> Dict[str, Any]:
        """Exécution directe in-process avec traçabilité complète des étapes."""
        # Étape 1 : Analyse préliminaire d'intention canonique
        intent = resolve_intent(question, use_llm=self.use_llm)

        # Exécution du pipeline complet
        try:
            resp = execute_text_to_sql_pipeline(
                question=question,
                db_session=self.db_session,
                use_llm=self.use_llm,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            intent_dump = intent.model_dump(mode="json") if intent else {}

            return {
                "question": question,
                "is_success": True,
                "status": intent.status if intent else "unknown",
                "execution_mode": resp.execution_mode,
                "query_id": resp.query_id,
                "sql_query": resp.sql_query,
                "intent": intent_dump,
                "row_count": len(resp.data) if resp.data else 0,
                "execution_time_ms": round(elapsed_ms, 2),
                "summary": resp.summary,
                "answer": resp.answer,
                "visualization": resp.visualization.model_dump(mode="json") if resp.visualization else None,
                "error_message": None,
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "question": question,
                "is_success": False,
                "status": intent.status if intent else "failed",
                "execution_mode": "FAILED",
                "query_id": None,
                "sql_query": None,
                "intent": intent.model_dump(mode="json") if intent else {},
                "row_count": 0,
                "execution_time_ms": round(elapsed_ms, 2),
                "summary": f"Erreur d'exécution : {exc}",
                "answer": str(exc),
                "visualization": None,
                "error_message": str(exc),
            }

    def _execute_via_http(self, question: str, start_time: float) -> Dict[str, Any]:
        """Exécution via l'endpoint HTTP POST /reporting/query."""
        url = f"{self.http_base_url}/reporting/query"
        payload = {"question": question, "filters": {}}

        try:
            r = requests.post(url, json=payload, timeout=30)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if r.status_code == 200:
                body = r.json()
                return {
                    "question": question,
                    "is_success": True,
                    "status": "ready",
                    "execution_mode": body.get("execution_mode", "HTTP_API"),
                    "query_id": body.get("query_id"),
                    "sql_query": body.get("sql_query"),
                    "intent": {},
                    "row_count": len(body.get("data", [])),
                    "execution_time_ms": round(elapsed_ms, 2),
                    "summary": body.get("summary"),
                    "answer": body.get("answer"),
                    "visualization": body.get("visualization"),
                    "error_message": None,
                }
            else:
                return {
                    "question": question,
                    "is_success": False,
                    "status": "http_error",
                    "execution_mode": "HTTP_ERROR",
                    "query_id": None,
                    "sql_query": None,
                    "intent": {},
                    "row_count": 0,
                    "execution_time_ms": round(elapsed_ms, 2),
                    "summary": f"Erreur HTTP {r.status_code}",
                    "answer": r.text,
                    "visualization": None,
                    "error_message": r.text,
                }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "question": question,
                "is_success": False,
                "status": "connection_error",
                "execution_mode": "CONNECTION_FAILED",
                "query_id": None,
                "sql_query": None,
                "intent": {},
                "row_count": 0,
                "execution_time_ms": round(elapsed_ms, 2),
                "summary": f"Échec de connexion HTTP : {exc}",
                "answer": str(exc),
                "visualization": None,
                "error_message": str(exc),
            }

    def close(self) -> None:
        """Libère les ressources de base de données."""
        if self.db_session:
            try:
                self.db_session.close()
            except Exception:
                pass
        if self.db_engine:
            try:
                self.db_engine.dispose()
            except Exception:
                pass
