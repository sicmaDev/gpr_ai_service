"""
Bouclier de Sécurité AST SQL pour le Reporting Text-to-SQL Gouverné (Step 6).

Ce module analyse l'arbre syntaxique abstrait (AST) de toute requête SQL candidate
produite par le LLM (Nemotron) ou issue du catalogue avec sqlglot (dialecte MySQL 8.0).
Il applique 6 politiques de sécurité strictes avant toute transmission à la base de données :
1. Instruction SELECT / CTE read-only exclusive (rejet de INSERT, UPDATE, DELETE, DROP, etc., et multi-statements).
2. Whitelist stricte des tables du Schema Catalog (rejet de tables système ou non analytiques).
3. Whitelist des colonnes et bouclier données sensibles (rejet des colonnes confidentielles et wildcard '*').
4. Intégrité des jointures selon le graphe officiel des relations du Schema Catalog.
5. Détection et blocage des fonctions dangereuses (SLEEP, BENCHMARK, LOAD_FILE, INTO OUTFILE, USER, VERSION, etc.).
6. Normalisation et production d'un contrat typé SqlValidationResult.
"""

from typing import Dict, List, Optional, Set, Tuple, Union
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

from app.reporting.schema_catalog import SCHEMA_CATALOG
from app.reporting.text_to_sql_contracts import (
    SchemaCatalog,
    SqlValidationResult,
    TextToSQLCandidate,
)

# Fonctions formellement interdites (sécurité, temporisation, exfiltration, système)
FORBIDDEN_FUNCTIONS: Set[str] = {
    "sleep",
    "benchmark",
    "load_file",
    "into_outfile",
    "outfile",
    "into_dumpfile",
    "dumpfile",
    "user",
    "system_user",
    "session_user",
    "current_user",
    "version",
    "database",
    "schema",
    "prepare",
    "execute",
    "deallocate",
    "get_lock",
    "release_lock",
    "char",
    "unhex",
    "export_set",
    "sys_exec",
    "sys_eval",
}

# Classes d'expressions sqlglot pour les fonctions système / d'environnement
FORBIDDEN_EXPRESSION_TYPES = (
    exp.CurrentVersion,
    exp.CurrentSchema,
    exp.CurrentUser,
    exp.CurrentDatabase,
    exp.SessionUser,
)

# Tables système et schémas réservés
FORBIDDEN_SCHEMAS: Set[str] = {
    "information_schema",
    "mysql",
    "performance_schema",
    "sys",
}

# Instructions non autorisées (toute mutation DML/DDL ou commande système)
MUTATION_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Create,
    exp.Command,
    exp.Grant,
    exp.Revoke,
    exp.Use,
    exp.Kill,
    exp.Set,
    exp.Show,
    exp.Describe,
    exp.Pragma,
)


def _build_allowed_relationships_set(
    schema_catalog: Optional[SchemaCatalog] = None,
) -> Set[Tuple[str, str, str, str]]:
    """
    Construit l'ensemble des relations autorisées (bidirectionnel) depuis SCHEMA_CATALOG ou un schéma spécifié.
    Retourne des tuples normalisés en minuscules : (table1, col1, table2, col2).
    """
    catalog = schema_catalog if schema_catalog is not None else SCHEMA_CATALOG
    rel_set: Set[Tuple[str, str, str, str]] = set()
    for rel in catalog.relationships:
        s_t = rel.source_table.lower()
        s_c = rel.source_column.lower()
        t_t = rel.target_table.lower()
        t_c = rel.target_column.lower()
        rel_set.add((s_t, s_c, t_t, t_c))
        rel_set.add((t_t, t_c, s_t, s_c))
    return rel_set


def _get_sensitive_columns_map(
    schema_catalog: Optional[SchemaCatalog] = None,
) -> Tuple[Set[str], Set[str]]:
    """
    Extrait les colonnes confidentielles depuis SCHEMA_CATALOG ou un schéma spécifié.
    Retourne :
    - full_sensitive : ensemble des 'nom_table.nom_colonne'
    - sensitive_names : ensemble des 'nom_colonne' sensibles
    """
    catalog = schema_catalog if schema_catalog is not None else SCHEMA_CATALOG
    full_sensitive: Set[str] = set()
    sensitive_names: Set[str] = set()
    for table_name, table_meta in catalog.tables.items():
        for col_name, col_meta in table_meta.columns.items():
            if col_meta.is_sensitive:
                full_sensitive.add(f"{table_name.lower()}.{col_name.lower()}")
                sensitive_names.add(col_name.lower())
    return full_sensitive, sensitive_names



def get_ast_digest(sql: str) -> str:
    """
    Retourne l'empreinte SQL normalisée de l'arbre syntaxique abstrait (AST).
    Si l'AST ne peut être parsé, retourne 'INVALID_AST'.
    """
    if not sql or not sql.strip():
        return "EMPTY_AST"
    try:
        parsed = sqlglot.parse_one(sql.strip().rstrip(";"), read="mysql")
        return parsed.sql(dialect="mysql")
    except Exception:
        return "INVALID_AST"


def validate_raw_sql(
    sql: str,
    allowed_tables: Optional[Set[str]] = None,
    schema_catalog: Optional[SchemaCatalog] = None,
) -> SqlValidationResult:
    """
    Valide une requête SQL brute via l'AST sqlglot (MySQL 8.0).

    Args:
        sql: Chaîne SQL paramétrée (:param).
        allowed_tables: Sous-ensemble optionnel de tables autorisées pour cette requête.
        schema_catalog: Schéma optionnel de référence (par défaut SCHEMA_CATALOG).

    Returns:
        SqlValidationResult conforme au contrat Pydantic (Step 2).
    """
    catalog = schema_catalog if schema_catalog is not None else SCHEMA_CATALOG

    if not sql or not sql.strip():
        return SqlValidationResult(
            is_valid=False,
            ast_digest="EMPTY",
            allowed_tables_checked=[],
            allowed_columns_checked=[],
            join_integrity_checked=False,
            violations=["La requete SQL est vide"],
        )

    clean_sql = sql.strip().rstrip(";")

    violations: List[str] = []
    join_integrity_ok = True
    tables_checked: List[str] = []
    columns_checked: List[str] = []

    # 1. Parsing AST avec sqlglot (MySQL 8.0)
    try:
        statements = sqlglot.parse(clean_sql, read="mysql")
    except Exception as e:
        return SqlValidationResult(
            is_valid=False,
            ast_digest="PARSE_ERROR",
            allowed_tables_checked=[],
            allowed_columns_checked=[],
            join_integrity_checked=False,
            violations=[f"Erreur de syntaxe SQL AST : {str(e)}"],
        )

    valid_stmts = [s for s in statements if s is not None]
    if len(valid_stmts) == 0:
        return SqlValidationResult(
            is_valid=False,
            ast_digest="EMPTY",
            allowed_tables_checked=[],
            allowed_columns_checked=[],
            join_integrity_checked=False,
            violations=["Aucune instruction SQL valide n'a pu etre extraite"],
        )

    if len(valid_stmts) > 1:
        return SqlValidationResult(
            is_valid=False,
            ast_digest="MULTI_STATEMENT",
            allowed_tables_checked=[],
            allowed_columns_checked=[],
            join_integrity_checked=False,
            violations=[
                "Multi-statements detecte : les requetes multiples separees par ';' sont formellement interdites"
            ],
        )

    root = valid_stmts[0]

    # 2. Instruction SELECT ou UNION exclusive
    if not isinstance(root, (exp.Select, exp.Union)):
        violations.append(
            f"Instruction non autorisee '{type(root).__name__}' : seules les requetes SELECT (ou CTE en lecture seule) sont permises"
        )

    # 3. Vérification des mutations DDL/DML dans tout l'arbre
    for node in root.walk():
        if isinstance(node, MUTATION_EXPRESSION_TYPES):
            violations.append(
                f"Operation interdite detectee : '{type(node).__name__}'"
            )

    # 4. Détection des CTEs et alias dérivés
    cte_names = {cte.alias.lower() for cte in root.find_all(exp.CTE) if cte.alias}
    cte_aliases = {
        t.alias.lower()
        for t in root.find_all(exp.Table)
        if t.name.lower() in cte_names and t.alias
    }
    subquery_aliases = {
        sq.alias.lower() for sq in root.find_all(exp.Subquery) if sq.alias
    }
    all_virtual_tables = cte_names | cte_aliases | subquery_aliases

    # 5. Whitelist des tables
    referenced_tables: Set[str] = set()
    for t in root.find_all(exp.Table):
        t_name = t.name.lower()
        t_db = t.db.lower() if t.db else None

        # Rejet des schémas / tables système
        if (
            t_db in FORBIDDEN_SCHEMAS
            or t_name in FORBIDDEN_SCHEMAS
            or any(t_name.startswith(f"{s}.") for s in FORBIDDEN_SCHEMAS)
        ):
            violations.append(f"Table systeme interdite : '{t.sql()}'")
            continue

        # Les CTEs ou sous-requêtes dérivées ne sont pas des tables physiques
        if t_name in all_virtual_tables:
            continue

        # Table inconnue ou hors périmètre de reporting
        if t_name not in catalog.tables:
            violations.append(
                f"Table non autorisee ou inconnue dans le schema de reporting : '{t_name}'"
            )
            continue

        tables_checked.append(t_name)
        referenced_tables.add(t_name)

        # Contrôle du sous-schéma minimal si fourni
        if allowed_tables is not None:
            allowed_lower = {tbl.lower() for tbl in allowed_tables}
            if t_name not in allowed_lower:
                violations.append(
                    f"Table '{t_name}' hors du sous-schema minimal autorise ({', '.join(sorted(allowed_lower))})"
                )

    # 6. Projections Wildcard et exclusion stricte des données sensibles
    for star in root.find_all(exp.Star):
        if not isinstance(star.parent, exp.Count):
            violations.append(
                "Projection wildcard '*' non autorisee : les colonnes doivent etre explicitement specifiees pour empecher toute fuite de donnees confidentielles"
            )

    # Table de correspondance alias -> table réelle
    alias_map: Dict[str, str] = {}
    for t in root.find_all(exp.Table):
        t_name = t.name.lower()
        if t_name in catalog.tables:
            alias_map[t_name] = t_name
            if t.alias:
                alias_map[t.alias.lower()] = t_name

    select_aliases = {a.alias.lower() for a in root.find_all(exp.Alias) if a.alias}
    full_sensitive, sensitive_names = _get_sensitive_columns_map(schema_catalog=catalog)

    for col in root.find_all(exp.Column):
        c_name = col.name.lower()
        t_ref = col.table.lower() if col.table else None

        # Alias défini dans SELECT (ex: GROUP BY agence_nom)
        if not t_ref and c_name in select_aliases:
            continue

        if t_ref:
            # Référence à une CTE ou sous-requête dérivée
            if t_ref in all_virtual_tables:
                continue
            if t_ref in alias_map:
                actual_table = alias_map[t_ref]
                col_full_ref = f"{actual_table}.{c_name}"
                columns_checked.append(col_full_ref)

                if c_name not in catalog.tables[actual_table].columns:
                    violations.append(
                        f"Colonne inconnue '{c_name}' pour la table '{actual_table}'"
                    )
                elif catalog.tables[actual_table].columns[c_name].is_sensitive:
                    violations.append(
                        f"Acces interdit a la colonne sensible '{col_full_ref}'"
                    )
            else:
                violations.append(
                    f"Alias ou table non reconnue pour la colonne : '{col.sql()}'"
                )
        else:
            # Colonne sans préfixe de table
            if c_name in sensitive_names:
                violations.append(f"Acces interdit a la colonne sensible '{c_name}'")
            else:
                found_in_tables = [
                    tbl
                    for tbl in referenced_tables
                    if c_name in catalog.tables[tbl].columns
                ]
                if not found_in_tables and referenced_tables:
                    violations.append(
                        f"Colonne inconnue '{c_name}' dans les tables referencees ({', '.join(sorted(referenced_tables))})"
                    )
                else:
                    for tbl in found_in_tables:
                        col_full_ref = f"{tbl}.{c_name}"
                        columns_checked.append(col_full_ref)
                        if catalog.tables[tbl].columns[c_name].is_sensitive:
                            violations.append(
                                f"Acces interdit a la colonne sensible '{col_full_ref}'"
                            )

    # 7. Intégrité des Jointures (Join Integrity)
    allowed_rel_set = _build_allowed_relationships_set(schema_catalog=catalog)

    for join in root.find_all(exp.Join):
        side = (join.side or "").upper().strip()
        kind = (join.kind or "").upper().strip()

        if side in ("RIGHT", "FULL"):
            violations.append(
                f"Type de jointure non autorise '{side} JOIN' : seuls INNER JOIN et LEFT JOIN sont acceptes"
            )
            join_integrity_ok = False
        if kind == "CROSS":
            violations.append("CROSS JOIN non autorise")
            join_integrity_ok = False

        on_clause = join.args.get("on")
        if on_clause:
            for eq in on_clause.find_all(exp.EQ):
                left = eq.this
                right = eq.expression
                if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                    t1_ref = left.table.lower() if left.table else None
                    c1_name = left.name.lower()
                    t2_ref = right.table.lower() if right.table else None
                    c2_name = right.name.lower()

                    t1_actual = alias_map.get(t1_ref, t1_ref)
                    t2_actual = alias_map.get(t2_ref, t2_ref)

                    # Si une des branches est une CTE ou table dérivée
                    if t1_actual in all_virtual_tables or t2_actual in all_virtual_tables:
                        continue

                    if t1_actual and t2_actual:
                        if (
                            t1_actual,
                            c1_name,
                            t2_actual,
                            c2_name,
                        ) not in allowed_rel_set:
                            violations.append(
                                f"Jointure non autorisee : la relation entre '{t1_actual}.{c1_name}' et '{t2_actual}.{c2_name}' n'est pas repertoriee dans le Schema Catalog"
                            )
                            join_integrity_ok = False

    # 8. Fonctions interdites et dangereuses
    for node in root.walk():
        if isinstance(node, FORBIDDEN_EXPRESSION_TYPES):
            violations.append(
                f"Fonction interdite (environnement) detectee : '{type(node).__name__}'"
            )
        elif isinstance(node, (exp.Func, exp.Anonymous)):
            fn_name = (node.name or "").lower()
            if fn_name in FORBIDDEN_FUNCTIONS:
                violations.append(
                    f"Fonction interdite ou potentiellement dangereuse detectee : '{node.name}'"
                )

    is_valid = len(violations) == 0
    raw_digest = root.sql(dialect="mysql") if root is not None else None
    ast_digest = (
        raw_digest
        if (raw_digest and raw_digest.strip())
        else "DIGEST_UNAVAILABLE"
    )

    return SqlValidationResult(
        is_valid=is_valid,
        ast_digest=ast_digest,
        allowed_tables_checked=sorted(list(set(tables_checked))),
        allowed_columns_checked=sorted(list(set(columns_checked))),
        join_integrity_checked=join_integrity_ok,
        violations=violations,
    )


def validate_candidate_sql(
    candidate: TextToSQLCandidate,
    allowed_tables: Optional[Set[str]] = None,
    schema_catalog: Optional[SchemaCatalog] = None,
) -> SqlValidationResult:
    """
    Valide un candidat SQL text-to-sql typé TextToSQLCandidate.
    Vérifie la syntaxe, la sécurité AST et la cohérence entre les paramètres
    déclarés dans le contrat et les placeholders (:param) présents dans la requête.
    """
    result = validate_raw_sql(
        candidate.sql,
        allowed_tables=allowed_tables,
        schema_catalog=schema_catalog,
    )


    # Si déjà invalide au niveau AST, retourner directement le résultat
    if not result.is_valid:
        return result

    # Vérification de cohérence des paramètres déclarés vs placeholders SQL
    try:
        parsed = sqlglot.parse_one(candidate.sql.strip().rstrip(";"), read="mysql")
        sql_placeholders = {
            p.name.lower() for p in parsed.find_all(exp.Placeholder) if p.name
        }
        declared_params = {p.lower() for p in candidate.parameters.keys()}

        # Détection de placeholders dans le SQL non déclarés dans candidate.parameters
        undeclared = sql_placeholders - declared_params
        if undeclared:
            result.is_valid = False
            for p_name in sorted(list(undeclared)):
                result.violations.append(
                    f"Parametre lié ':{p_name}' present dans le SQL mais absent du contrat de parametres"
                )
    except Exception:
        pass

    return result
