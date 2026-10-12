"""
Service de journalisation et métriques d'audit des requêtes Text-to-SQL (Step 7).

Ce module centralise la traçabilité des exécutions de requêtes SQL :
- Enregistrement structuré conforme au contrat ExecutionAuditLog.
- Masquage des paramètres sensibles.
- Mise à jour automatique des statistiques d'exécution dans le QueryCatalog.
- Historique d'audit glissant consultable.
"""

from collections import deque
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.reporting.query_catalog import _CERTIFIED_QUERIES
from app.reporting.text_to_sql_contracts import (
    ExecutionAuditLog,
    ExecutionStatus,
    QuerySource,
    SqlExecutionResult,
)

logger = logging.getLogger(__name__)

SENSITIVE_PARAM_KEYWORDS = {
    "password", "secret", "token", "code", "client_code", "email", "phone"
}


def mask_sensitive_params(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Masque les valeurs des paramètres susceptibles de contenir des données sensibles
    avant enregistrement dans l'audit.
    """
    masked: Dict[str, Any] = {}
    for k, v in parameters.items():
        k_lower = str(k).lower()
        if any(keyword in k_lower for keyword in SENSITIVE_PARAM_KEYWORDS):
            masked[k] = "[MASQUÉ]"
        elif isinstance(v, datetime):
            masked[k] = v.isoformat()
        else:
            masked[k] = v
    return masked


class AuditService:
    """
    Gestionnaire en mémoire des traces d'audit et des métriques d'exécution.
    """

    def __init__(self, max_history: int = 1000):
        self._history: deque[ExecutionAuditLog] = deque(maxlen=max_history)

    def log_execution(
        self,
        query_source: QuerySource,
        sql_executed: str,
        bound_parameters: Dict[str, Any],
        result: SqlExecutionResult,
        query_id: Optional[str] = None,
        natural_language_query: Optional[str] = None,
    ) -> ExecutionAuditLog:
        """
        Crée et enregistre une entrée d'audit à partir du résultat d'exécution.
        """
        audit_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        sanitized_params = mask_sensitive_params(bound_parameters)

        audit_entry = ExecutionAuditLog(
            audit_id=audit_id,
            timestamp=now,
            query_source=query_source,
            query_id=query_id,
            natural_language_query=natural_language_query,
            sql_executed=sql_executed,
            sanitized_parameters=sanitized_params,
            execution_time_ms=result.execution_time_ms,
            row_count=result.row_count,
            status=result.status,
            error_message=result.error_message,
        )

        self._history.appendleft(audit_entry)

        # Mise à jour des métriques dans le QueryCatalog si applicable
        if query_id and query_id in _CERTIFIED_QUERIES:
            entry = _CERTIFIED_QUERIES[query_id]
            entry.execution_count += 1
            entry.last_executed_at = now
            if entry.avg_execution_time_ms is None:
                entry.avg_execution_time_ms = result.execution_time_ms
            else:
                entry.avg_execution_time_ms = round(
                    (
                        entry.avg_execution_time_ms * (entry.execution_count - 1)
                        + result.execution_time_ms
                    )
                    / entry.execution_count,
                    2,
                )

        logger.info(
            f"Audit [{audit_id[:8]}] - Source: {query_source} - Statut: {result.status} - "
            f"Durée: {result.execution_time_ms}ms - Lignes: {result.row_count}"
        )
        return audit_entry

    def get_recent_audits(self, limit: int = 50) -> List[ExecutionAuditLog]:
        """
        Retourne la liste des traces d'audit récentes (les plus récentes en premier).
        """
        return list(self._history)[:limit]

    def get_stats_for_query(self, query_id: str) -> Dict[str, Any]:
        """
        Retourne les métriques de performance cumulées pour une requête donnée.
        """
        if query_id in _CERTIFIED_QUERIES:
            entry = _CERTIFIED_QUERIES[query_id]
            return {
                "query_id": entry.id,
                "status": entry.status.value,
                "execution_count": entry.execution_count,
                "avg_execution_time_ms": entry.avg_execution_time_ms,
                "last_executed_at": entry.last_executed_at,
            }

        # Calcul sur les logs en mémoire si non répertorié
        matching = [log for log in self._history if log.query_id == query_id]
        if not matching:
            return {"query_id": query_id, "execution_count": 0, "avg_execution_time_ms": None}

        total_time = sum(m.execution_time_ms for m in matching)
        return {
            "query_id": query_id,
            "execution_count": len(matching),
            "avg_execution_time_ms": round(total_time / len(matching), 2),
            "last_executed_at": matching[0].timestamp,
        }

    def clear_history(self) -> None:
        """Réinitialise l'historique d'audit (utile pour les tests)."""
        self._history.clear()


# Instance singleton globale
AUDIT_SERVICE = AuditService()
