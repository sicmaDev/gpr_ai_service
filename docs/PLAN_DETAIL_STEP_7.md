# Plan Détaillé Step 7 : Exécution Read-Only Sécurisée, Bind Params, Quotas & Audit

> **Document officiel de référence — Step 7 (Text-to-SQL Gouverné)**  
> **Conformité** : Sections 11, 12 et Point 7 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests validés).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests validés).  
> • Résolution d'intention & Fast-Path : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py) et [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py) (19 tests validés).  
> • Schema Retriever & Générateur SQL : [`PLAN_DETAIL_STEP_5.md`](./PLAN_DETAIL_STEP_5.md), [`app/reporting/schema_retriever.py`](../app/reporting/schema_retriever.py) et [`app/reporting/sql_generator.py`](../app/reporting/sql_generator.py) (12 tests validés).  
> • Validateur AST SQL sqlglot : [`PLAN_DETAIL_STEP_6.md`](./PLAN_DETAIL_STEP_6.md) et [`app/reporting/sql_validator.py`](../app/reporting/sql_validator.py) (22 tests validés).  
> **Suite de tests actuelle** : 82 tests unitaires validés à 100% en 0.082s.

---

## 1. Objectif Fondamental du Step 7 : L'Exécution Sécurisée et Contrôlée

Le **Step 7** est le point de convergence de l'architecture Text-to-SQL :
* Soit la requête provient du **Fast-Path certifié** du `QueryCatalog` (Step 4) ;
* Soit la requête provient de la **génération LLM supervisée** (Step 5) ayant franchi avec succès le **Validateur AST SQL** (Step 6).

Dans les deux cas, le moteur d'exécution SQL applique une politique de sécurité et de contrôle des ressources sans compromis :
1. **Liaison Stricte des Paramètres (`Bind Parameters`)** :
   * Les placeholders `:param` (ex: `:start_date`, `:end_date`, `:agency`) ne sont **jamais** substitués par injection textuelle ou interpolation de format (`f-strings`, `%s`).
   * Ils sont typés, validés et liés nativement via le mécanisme de bind parameters de SQLAlchemy (`text(sql).bindparams(...)`).
2. **Exécution Transactionnelle en Lecture Seule (`Read-Only`)** :
   * Exécution sous transaction isolée avec drapeau lecture seule.
   * `session.rollback()` systématique en fin d'exécution (`try...finally`) afin de garantir qu'aucune écriture résiduelle n'est persistée.
   * Compte utilisateur MySQL dédié avec droits restreints (`SELECT` uniquement sur `gpr_ai_reporting`, aucun accès à la base opérationnelle `gpr_sicma_online`).
3. **Quotas de Ressources & Protection DoS** :
   * **Timeout strict** : 3.0 secondes maximum par requête (interruption immédiate si une requête analytique est trop lente).
   * **Plafond de lignes** : `LIMIT 500` forcé. Si la requête n'a pas de `LIMIT`, un plafond de 500 est automatiquement injecté par le moteur ; si elle en a un supérieur à 500, il est ramené à 500.
4. **Traces d'Audit Exhaustives (`Audit Trail`)** :
   * Chaque exécution (succès, timeout, erreur SQL) est enregistrée avec : timestamp, identifiant unique, durée en millisecondes, SQL exécuté, paramètres assainis, nombre de lignes, et statut.
   * Ces métriques alimentent également le compteur d'exécutions et le temps moyen (`avg_execution_time_ms`) dans le `QueryCatalog`.

---

## 2. Architecture & Organisation des Fichiers

```text
app/reporting/
├── text_to_sql_contracts.py          # Step 2 : Contrats de base + SqlExecutionResult & ExecutionAuditLog
├── schema_catalog.py                 # Step 3 : Schema Catalog (13 tables)
├── business_catalog.py               # Step 3 : Business Catalog (concepts, dimensions)
├── query_catalog.py                  # Step 4 : Requêtes certifiées
├── intent_resolver.py                # Step 4 : Résolveur d'intention canonique
├── schema_retriever.py               # Step 5 : Sous-schéma minimal pertinent
├── sql_generator.py                  # Step 5 : Générateur SQL candidat paramétré
├── sql_validator.py                  # Step 6 : Validateur AST SQL (sqlglot)
│
├── sql_executor.py                   # NOUVEAU (Step 7) : Moteur d'exécution Read-Only sécurisé
│   ├── sanitize_and_bind_params()    # Validation et liaison des paramètres typés (:param)
│   ├── enforce_query_limits()        # Contrôle et injection automatique du LIMIT 500
│   ├── execute_read_only_query()     # Exécution SQLAlchemy sécurisée (timeout 3s, rollback)
│   └── format_result_rows()          # Transformation des Row SQLAlchemy en listes de dictionnaires
│
├── audit_service.py                  # NOUVEAU (Step 7) : Journalisation et métriques d'audit
│   ├── log_execution_audit()         # Persistance du log d'audit d'une exécution
│   ├── get_audit_trail()             # Consultation filtrée des traces d'audit
│   └── get_performance_summary()    # Statistiques d'exécution (temps moyen, taux d'erreur)
│
tests/
├── test_text_to_sql_contracts.py     # 15 tests
├── test_schema_and_business_catalogs.py # 14 tests
├── test_step_4_intent_and_query_catalog.py # 19 tests
├── test_step_5_schema_retriever_and_sql_generator.py # 12 tests
├── test_step_6_sql_validator.py      # 22 tests
└── test_step_7_sql_executor_and_audit.py # NOUVEAU (Step 7) : Tests Exécuteur & Audit
```

---

## 3. Spécification des Contrats Formels (Pydantic)

Deux nouveaux contrats Pydantic sont introduits pour structurer l'exécution et l'audit :

### 3.1. Contrat `SqlExecutionResult`
```python
class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    SQL_ERROR = "SQL_ERROR"
    VALIDATION_FAILED = "VALIDATION_FAILED"

class SqlExecutionResult(ContractModel):
    status: ExecutionStatus
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    sql_executed: str
    bound_parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
```

### 3.2. Contrat `ExecutionAuditLog`
```python
class QuerySource(str, Enum):
    FAST_PATH_CERTIFIED = "FAST_PATH_CERTIFIED"
    GENERATIVE_SUPERVISED = "GENERATIVE_SUPERVISED"

class ExecutionAuditLog(ContractModel):
    audit_id: str                          # UUID v4
    timestamp: datetime                    # Horodatage UTC
    query_source: QuerySource              # Origine (Certifiée vs Générative)
    query_id: Optional[str] = None         # Identifiant du QueryCatalog si applicable
    natural_language_query: Optional[str] = None # Question originale
    sql_executed: str                      # SQL avec paramètres
    sanitized_parameters: Dict[str, Any]   # Paramètres masqués si sensibles
    execution_time_ms: float               # Durée mesurée
    row_count: int                         # Nombre de lignes retournées
    status: ExecutionStatus                # Résultat
    error_message: Optional[str] = None    # Message d'erreur si échec
```

---

## 4. Les 5 Piliers d'Exécution Sécurisée

### Pilier 1 : Porte de Sécurité AST Pré-Exécution Obligatoire
* Avant d'envoyer la moindre requête au moteur de base de données, la fonction `execute_read_only_query()` appelle obligatoirement le validateur `validate_raw_sql` du Step 6.
* Si `is_valid == False`, l'exécution est bloquée net : aucun appel réseau, aucun accès SQLAlchemy. Le résultat renvoie immédiatement `status=VALIDATION_FAILED` avec la liste des violations.

### Pilier 2 : Liaison Typée des Paramètres (`Bind Parameters`)
* Les paramètres sont convertis vers les types Python attendus :
  * `datetime` / `date` : conversion des chaînes ISO `YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM:SS` en objets Python natifs.
  * `string` : assainissement et strip des espaces superflus.
  * `integer` / `decimal` : casting strict empêchant les injections.
* Les paramètres sont passés au statement SQLAlchemy :
  ```python
  stmt = text(normalized_sql).bindparams(**safe_params)
  ```

### Pilier 3 : Plafonnement Automatique de Ressources (`LIMIT 500`)
* Les requêtes analytiques mal dimensionnées peuvent saturer la mémoire du serveur ou du navigateur.
* Le moteur inspecte l'AST :
  * S'il n'y a pas de clause `LIMIT`, il ajoute automatiquement `LIMIT 500`.
  * Si un `LIMIT N` est présent mais dépasse 500 (ex: `LIMIT 10000`), il est ramené à 500.

### Pilier 4 : Timeout Strict (3.0s) & Transaction Read-Only
* Le moteur applique un timeout strict de 3 secondes :
  * Option SQLAlchemy : `execution_options(timeout=3.0)`.
  * Directive de session MySQL si disponible : `SET max_execution_time=3000`.
* Transaction isolée :
  * Exécution dans une session éphémère.
  * Appel systématique à `session.rollback()` dans le bloc `finally` pour garantir une imperméabilité totale vis-à-vis des écritures.

### Pilier 5 : Audit Systématique & Apprentissage Continu
* Chaque exécution enregistre une entrée d'audit via `AuditService`.
* En cas d'exécution répétée d'une requête certifiée du `QueryCatalog`, les métriques `execution_count`, `avg_execution_time_ms` et `last_executed_at` de l'entrée du catalogue sont mises à jour dynamiquement.

---

## 5. Spécification des Fonctions de `app/reporting/sql_executor.py`

```python
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
    1. Valide l'AST via sql_validator.py.
    2. Valide et lie les paramètres typés.
    3. Force le quota LIMIT max_rows.
    4. Exécute avec timeout strict et rollback systématique.
    5. Retourne un SqlExecutionResult typé.
    """

def enforce_row_limit(sql: str, max_limit: int = 500) -> str:
    """
    Injecte ou plafonne la clause LIMIT d'une requête SQL via sqlglot.
    """

def sanitize_parameters(
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Valide, type et assainit les paramètres liés (:param).
    """
```

---

## 6. Spécification du Service d'Audit `app/reporting/audit_service.py`

```python
class AuditService:
    """
    Gestionnaire centralisé des traces d'audit d'exécution des requêtes Text-to-SQL.
    Supporte le stockage en mémoire (tests/dev) et l'enregistrement persistant.
    """
    def log_execution(self, audit: ExecutionAuditLog) -> None:
        """Enregistre une trace d'audit."""

    def get_recent_audits(self, limit: int = 50) -> List[ExecutionAuditLog]:
        """Retourne les dernières traces d'audit."""

    def get_stats_for_query(self, query_id: str) -> Dict[str, Any]:
        """Retourne les statistiques de performance d'une requête du QueryCatalog."""
```

---

## 7. Plan de Tests Unitaires (`tests/test_step_7_sql_executor_and_audit.py`)

La suite de tests couvrira exhaustivement les scénarios d'exécution et d'audit :

1. **Exécution réussie avec Bind Parameters** :
   * Exécution d'une requête certifiée avec paramètres `:start_date`, `:end_date`.
   * Vérification de la conversion correcte des types et du format des lignes retournées.
2. **Plafonnement et Injection de LIMIT 500** :
   * Requête sans `LIMIT` $\rightarrow$ injection automatique de `LIMIT 500`.
   * Requête avec `LIMIT 1000` $\rightarrow$ plafonnement automatique à `LIMIT 500`.
   * Requête avec `LIMIT 10` $\rightarrow$ conservation de `LIMIT 10`.
3. **Blocage des Requêtes Invalides (Court-Circuit Sécurité)** :
   * Tentative d'exécuter `DROP TABLE reporting_claim` $\rightarrow$ bloqué par le validateur avec statut `VALIDATION_FAILED` (aucun appel DB).
   * Tentative d'accès à une colonne sensible $\rightarrow$ bloqué avec statut `VALIDATION_FAILED`.
4. **Gestion des Erreurs et Timeouts** :
   * Simulation d'un timeout $\rightarrow$ capture propre et statut `TIMEOUT`.
   * Simulation d'une erreur SQL $\rightarrow$ capture propre et statut `SQL_ERROR`.
   * Vérification que `rollback()` est systématiquement appelé en cas d'erreur.
5. **Vérification du Service d'Audit** :
   * Enregistrement correct du log d'audit avec durée d'exécution `execution_time_ms > 0`.
   * Masquage des paramètres sensibles dans le log d'audit.
   * Mise à jour des compteurs d'exécution dans le `QueryCatalog`.

---

## 8. Critères d'Acceptation de l'Étape 7

* [x] Les contrats `SqlExecutionResult` et `ExecutionAuditLog` sont définis dans `text_to_sql_contracts.py`.
* [x] Le module `app/reporting/sql_executor.py` est implémenté avec validation AST préalable, bind params, `LIMIT 500`, timeout et rollback.
* [x] Le service d'audit `app/reporting/audit_service.py` est implémenté et journalise chaque exécution (avec masquage et métriques QueryCatalog).
* [x] Aucune régression sur les 82 tests existants (Steps 2 à 6 validés à 100%).
* [x] La nouvelle suite `tests/test_step_7_sql_executor_and_audit.py` passe à 100% (14 tests validés en 0.063s).
* [x] Le document maître `PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md` est mis à jour pour acter la transition vers le Step 8.
