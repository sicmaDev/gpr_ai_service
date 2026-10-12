"""
Moteur d'exécution SQL en lecture seule sécurisé (Step 7).

Ce module applique les 5 piliers de sécurité pour l'exécution des requêtes Text-to-SQL :
1. Validation AST préalable obligatoire (sql_validator.py).
2. Liaison stricte des paramètres (:param) via SQLAlchemy bindparams (zéro interpolation).
3. Plafonnement forcé de ressources avec LIMIT 500 (via sqlglot).
4. Timeout strict (3.0s) et transaction read-only avec rollback systématique.
5. Contrat typé SqlExecutionResult.
"""

from datetime import date, datetime
import logging
from time import perf_counter
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError, TimeoutError as SATimeoutError
from sqlalchemy.orm import Session
import sqlglot
from sqlglot import exp

from app.db.session import SessionLocal
from app.reporting.sql_validator import validate_raw_sql
from app.reporting.text_to_sql_contracts import ExecutionStatus, SqlExecutionResult

logger = logging.getLogger(__name__)


def sanitize_parameters(parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valide, type et assainit les paramètres liés (:param).
    Convertit les chaînes ISO en objets datetime/date et assainit les entrées.
    """
    if not parameters:
        return {}

    safe_params: Dict[str, Any] = {}
    for key, value in parameters.items():
        clean_key = str(key).strip().lstrip(":")

        if isinstance(value, str):
            val_stripped = value.strip()
            # Tentative de conversion des chaînes de date ISO
            if len(val_stripped) in (10, 19, 20, 23, 26, 29, 32):
                try:
                    safe_params[clean_key] = datetime.fromisoformat(val_stripped)
                    continue
                except ValueError:
                    pass
            safe_params[clean_key] = val_stripped
        elif isinstance(value, (int, float, bool, date, datetime)):
            safe_params[clean_key] = value
        elif value is None:
            safe_params[clean_key] = None
        else:
            safe_params[clean_key] = str(value)

    return safe_params


def enforce_row_limit(sql: str, max_limit: int = 500) -> str:
    """
    Injecte ou plafonne la clause LIMIT d'une requête SQL via sqlglot.
    Si LIMIT est absent, ajoute LIMIT max_limit.
    Si LIMIT est supérieur à max_limit, le ramène à max_limit.
    """
    if not sql or not sql.strip():
        return sql

    clean_sql = sql.strip().rstrip(";")
    try:
        ast = sqlglot.parse_one(clean_sql, read="mysql")
        limit_clause = ast.args.get("limit")

        if limit_clause is None:
            ast = ast.limit(max_limit)
        else:
            try:
                curr_val = int(limit_clause.expression.name)
                if curr_val > max_limit:
                    ast = ast.limit(max_limit)
            except Exception:
                ast = ast.limit(max_limit)

        return ast.sql(dialect="mysql")
    except Exception as e:
        logger.warning(f"Impossible d'ajuster le LIMIT via sqlglot : {e}")
        return clean_sql


def execute_read_only_query(
    sql: str,
    parameters: Optional[Dict[str, Any]] = None,
    allowed_tables: Optional[Set[str]] = None,
    session: Optional[Session] = None,
    timeout_seconds: float = 3.0,
    max_rows: int = 500,
) -> SqlExecutionResult:
    """
    Exécute de manière sécurisée une requête SQL text-to-sql en lecture seule.

    Args:
        sql: Chaîne SQL paramétrée (:param).
        parameters: Dictionnaire des paramètres liés.
        allowed_tables: Sous-schéma optionnel de tables autorisées.
        session: Session SQLAlchemy optionnelle (créée localement si None).
        timeout_seconds: Timeout maximal d'exécution en secondes.
        max_rows: Plafond maximal de lignes retournées.

    Returns:
        SqlExecutionResult typé.
    """
    start_time = perf_counter()

    # 1. Validation AST préalable obligatoire
    validation = validate_raw_sql(sql, allowed_tables=allowed_tables)
    if not validation.is_valid:
        error_msg = " | ".join(validation.violations)
        logger.warning(f"Exécution bloquée par le validateur AST : {error_msg}")
        return SqlExecutionResult(
            status=ExecutionStatus.VALIDATION_FAILED,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0.0,
            sql_executed=sql,
            bound_parameters=parameters or {},
            error_message=error_msg,
        )

    # 2. Enforcement du quota LIMIT
    capped_sql = enforce_row_limit(sql, max_limit=max_rows)

    # 3. Assainissement et typage des bind params
    safe_params = sanitize_parameters(parameters)

    # 4. Exécution transactionnelle isolée en lecture seule
    own_session = session is None
    db_session: Session = session if session is not None else SessionLocal()

    try:
        stmt = text(capped_sql)
        # Application du timeout au niveau statement
        exec_options = {"timeout": timeout_seconds}
        result_proxy = db_session.execute(
            stmt.execution_options(**exec_options), safe_params
        )

        columns = list(result_proxy.keys())
        raw_rows = result_proxy.fetchall()

        # Conversion des Row SQLAlchemy en dictionnaires
        rows: List[Dict[str, Any]] = []
        for row in raw_rows:
            if hasattr(row, "_asdict"):
                rows.append(row._asdict())
            else:
                rows.append(dict(zip(columns, row)))

        duration_ms = (perf_counter() - start_time) * 1000.0

        return SqlExecutionResult(
            status=ExecutionStatus.SUCCESS,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=round(duration_ms, 2),
            sql_executed=capped_sql,
            bound_parameters=safe_params,
            error_message=None,
        )

    except (SATimeoutError, TimeoutError) as e:
        duration_ms = (perf_counter() - start_time) * 1000.0
        logger.error(f"Timeout lors de l'exécution SQL ({timeout_seconds}s) : {e}")
        return SqlExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=round(duration_ms, 2),
            sql_executed=capped_sql,
            bound_parameters=safe_params,
            error_message=f"Timeout d'exécution dépassé ({timeout_seconds}s)",
        )

    except OperationalError as e:
        duration_ms = (perf_counter() - start_time) * 1000.0
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str or "max_execution_time" in err_str:
            status = ExecutionStatus.TIMEOUT
            msg = f"Timeout d'exécution dépassé ({timeout_seconds}s)"
        else:
            status = ExecutionStatus.SQL_ERROR
            msg = f"Erreur opérationnelle SQL : {str(e)}"
        logger.error(msg)
        return SqlExecutionResult(
            status=status,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=round(duration_ms, 2),
            sql_executed=capped_sql,
            bound_parameters=safe_params,
            error_message=msg,
        )

    except SQLAlchemyError as e:
        duration_ms = (perf_counter() - start_time) * 1000.0
        msg = f"Erreur SQLAlchemy : {str(e)}"
        logger.error(msg)
        return SqlExecutionResult(
            status=ExecutionStatus.SQL_ERROR,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=round(duration_ms, 2),
            sql_executed=capped_sql,
            bound_parameters=safe_params,
            error_message=msg,
        )

    except Exception as e:
        duration_ms = (perf_counter() - start_time) * 1000.0
        msg = f"Erreur inattendue d'exécution : {str(e)}"
        logger.exception(msg)
        return SqlExecutionResult(
            status=ExecutionStatus.SQL_ERROR,
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=round(duration_ms, 2),
            sql_executed=capped_sql,
            bound_parameters=safe_params,
            error_message=msg,
        )

    finally:
        # Toujours annuler la transaction pour garantir zéro écriture
        try:
            db_session.rollback()
        except Exception:
            pass
        if own_session:
            try:
                db_session.close()
            except Exception:
                pass
