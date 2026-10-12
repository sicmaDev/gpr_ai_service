# Plan Détaillé Step 8 : Approbation Humaine, Cycle de Vie & Gestion du Query Catalog

> **Document officiel de référence — Step 8 (Text-to-SQL Gouverné)**  
> **Conformité** : Section 11 et Point 8 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests validés).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests validés).  
> • Résolution d'intention & Fast-Path : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py) et [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py) (19 tests validés).  
> • Schema Retriever & Générateur SQL : [`PLAN_DETAIL_STEP_5.md`](./PLAN_DETAIL_STEP_5.md), [`app/reporting/schema_retriever.py`](../app/reporting/schema_retriever.py) et [`app/reporting/sql_generator.py`](../app/reporting/sql_generator.py) (12 tests validés).  
> • Validateur AST SQL sqlglot : [`PLAN_DETAIL_STEP_6.md`](./PLAN_DETAIL_STEP_6.md) et [`app/reporting/sql_validator.py`](../app/reporting/sql_validator.py) (22 tests validés).  
> • Exécuteur Read-Only & Audit : [`PLAN_DETAIL_STEP_7.md`](./PLAN_DETAIL_STEP_7.md), [`app/reporting/sql_executor.py`](../app/reporting/sql_executor.py) et [`app/reporting/audit_service.py`](../app/reporting/audit_service.py) (14 tests validés).  
> **Suite de tests actuelle** : 96 tests unitaires validés à 100% en 0.116s.

---

## 1. Objectif Fondamental du Step 8 : Gouvernance Humaine & Boucle d'Apprentissage

Dans l'architecture Text-to-SQL gouvernée, **l'approbation humaine est la clé de voûte de l'apprentissage continu et de la certification métier** :
1. **Séparation nette entre exécution ponctuelle et promotion au catalogue** :
   * Une requête candidate générée par le LLM (Step 5) ayant franchi le validateur AST (Step 6) est immédiatement exécutée pour l'utilisateur (Step 7). L'approbation humaine **n'est pas bloquante** pour répondre à l'utilisateur.
   * En revanche, l'entrée dans le **Query Catalog** (éligibilité au Fast-Path court-circuit sans appel LLM pour tous les utilisateurs futurs) **exige une revue humaine formelle**.
2. **Cycle de vie maîtrisé (`ApprovalStatus`)** :
   * `PENDING` : requête candidate soumise à homologation après génération/exécution réussie.
   * `APPROVED` : certifiée par un administrateur métier / data analyst, active dans le Fast-Path.
   * `REJECTED` : rejetée lors de la revue (ex: SQL fonctionnel mais sémantique métier inadéquate).
   * `DEPRECATED` : désactivée manuellement ou automatiquement suite à une évolution du schéma ou des définitions métier.
3. **Garantie d'intégrité avant promotion** :
   * Aucune requête ne peut passer à l'état `APPROVED` si elle ne satisfait pas l'ensemble des règles de sécurité AST du Step 6 (`validate_raw_sql`).
4. **Gestion de l'évolution et de l'obsolescence (Schema Versioning)** :
   * Lorsque le `SchemaCatalog` évolue (ex: passage de la version `1.0.0` à `1.1.0`), les requêtes du catalogue associées à l'ancienne version doivent être vérifiées ou dépréciées automatiquement afin d'éviter toute rupture ou régression.

---

## 2. Architecture & Organisation des Fichiers

```text
app/reporting/
├── text_to_sql_contracts.py          # Step 2 & 7 : Contrats de base, approbation, audit
├── schema_catalog.py                 # Step 3 : Schema Catalog (13 tables)
├── business_catalog.py               # Step 3 : Business Catalog (concepts, dimensions)
├── query_catalog.py                  # Step 4 : Requêtes certifiées initiales & matching
├── intent_resolver.py                # Step 4 : Résolveur d'intention canonique
├── schema_retriever.py               # Step 5 : Extraction du sous-schéma minimal
├── sql_generator.py                  # Step 5 : Générateur SQL candidat
├── sql_validator.py                  # Step 6 : Validateur AST SQL (sqlglot)
├── sql_executor.py                   # Step 7 : Moteur d'exécution Read-Only sécurisé
├── audit_service.py                  # Step 7 : Service d'audit et métriques
│
├── catalog_manager.py                # NOUVEAU (Step 8) : Gestionnaire du cycle de vie des requêtes
│   ├── propose_query_candidate()     # Soumission d'une requête générée au statut PENDING
│   ├── approve_query()               # Promotion au statut APPROVED (avec validation AST préalable)
│   ├── reject_query()                # Passage au statut REJECTED avec motif
│   ├── deprecate_query()             # Désactivation / passage au statut DEPRECATED
│   ├── list_catalog_entries()        # Consultation filtrée par statut (PENDING, APPROVED, etc.)
│   └── sync_on_schema_evolution()    # Invalidation / dépréciation sur changement de version de schéma
│
tests/
├── test_text_to_sql_contracts.py     # 15 tests
├── test_schema_and_business_catalogs.py # 14 tests
├── test_step_4_intent_and_query_catalog.py # 19 tests
├── test_step_5_schema_retriever_and_sql_generator.py # 12 tests
├── test_step_6_sql_validator.py      # 22 tests
├── test_step_7_sql_executor_and_audit.py # 14 tests
└── test_step_8_catalog_manager.py    # NOUVEAU (Step 8) : Tests Approbation & Cycle de Vie
```

---

## 3. Modèles de Données & Contrats du Step 8

Les contrats sont déjà définis dans [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) :
```python
class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"

class QueryCatalogEntry(ContractModel):
    id: NonEmptyString
    contract_version: NonEmptyString = "1.0"
    natural_language_query: NonEmptyString
    canonical_intent: TextToSQLIntent
    parameterized_sql: NonEmptyString
    parameters_schema: Dict[NonEmptyString, CandidateParameter] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_by: NonEmptyString
    approved_by: Optional[NonEmptyString] = None
    approved_at: Optional[datetime] = None
    schema_version: NonEmptyString = "1.0.0"
    execution_count: int = 0
    avg_execution_time_ms: Optional[float] = None
    last_executed_at: Optional[datetime] = None
```

Nouveaux DTO d'actions administratives :
```python
class QueryApprovalPayload(ContractModel):
    query_id: NonEmptyString
    approver: NonEmptyString
    comment: Optional[str] = None

class QueryRejectionPayload(ContractModel):
    query_id: NonEmptyString
    approver: NonEmptyString
    rejection_reason: NonEmptyString

class QueryDeprecationPayload(ContractModel):
    query_id: NonEmptyString
    reason: NonEmptyString
```

---

## 4. Spécification des Fonctions de `app/reporting/catalog_manager.py`

### 4.1. Soumission d'une Candidate (`propose_query_candidate`)
* Reçoit une intention `TextToSQLIntent`, un SQL candidat `str`, les paramètres et l'auteur.
* Vérifie immédiatement la conformité AST via `validate_raw_sql`.
* Génère un identifiant unique (ex: `QC-CANDIDATE-{uuid[:8]}`).
* Enregistre l'entrée dans le catalogue avec `status = ApprovalStatus.PENDING`.

### 4.2. Homologation Administrative (`approve_query`)
* Reçoit `query_id` et l'identifiant de l'administrateur `approver`.
* **Vérification de sécurité bloquante** : revalide le SQL via `validate_raw_sql`. Si invalide, refus d'approbation avec exception explicite.
* Met à jour :
  * `status = ApprovalStatus.APPROVED`
  * `approved_by = approver`
  * `approved_at = datetime.now(timezone.utc)`
* Dès cet instant, la requête devient immédiatement accessible par `match_intent_in_catalog()`.

### 4.3. Rejet d'une Candidate (`reject_query`)
* Reçoit `query_id`, `approver` et `rejection_reason`.
* Met à jour :
  * `status = ApprovalStatus.REJECTED`
* La requête n'est pas supprimée afin de conserver l'historique d'audit et d'empêcher de réapprouver par inadvertance une mauvaise requête.

### 4.4. Dépréciation & Retrait du Fast-Path (`deprecate_query`)
* Reçoit `query_id` et un motif de dépréciation.
* Met à jour :
  * `status = ApprovalStatus.DEPRECATED`
* La requête est immédiatement exclue du Fast-Path. Les futures questions similaires rebasculeront sur la génération supervisée.

### 4.5. Gestion de l'Évolution de Schéma (`sync_on_schema_evolution`)
* Reçoit la nouvelle version du schéma (ex: `"1.1.0"`).
* Parcourt toutes les requêtes actives (`APPROVED`).
* Pour chaque requête, teste sa compatibilité AST avec le nouveau schéma :
  * Si la requête référence une table ou colonne modifiée/retirée, ou si sa version est obsolète : passage automatique à `DEPRECATED` avec notification d'audit.
* Retourne la liste des identifiants invalidés.

---

## 5. Plan de Tests Unitaires (`tests/test_step_8_catalog_manager.py`)

1. **Soumission de Candidate** :
   * Soumission d'une requête valide $\rightarrow$ création au statut `PENDING`.
   * Tentative de soumettre une requête non conforme à l'AST $\rightarrow$ rejetée immédiatement.
2. **Approbation Administrative** :
   * Approbation d'une candidate $\rightarrow$ passage à `APPROVED`, renseignement de `approved_by` et `approved_at`.
   * Vérification que la requête nouvellement approuvée est désormais reconnue par `match_intent_in_catalog`.
3. **Rejet Administratif** :
   * Rejet d'une candidate $\rightarrow$ passage à `REJECTED`.
   * Vérification que la requête rejetée n'est **jamais** servie par le Fast-Path.
4. **Dépréciation de Requête** :
   * Dépréciation d'une requête précédemment approuvée $\rightarrow$ passage à `DEPRECATED`.
   * Vérification qu'elle est immédiatement ignorée par `match_intent_in_catalog`.
5. **Filtrage et Consultation** :
   * Lister toutes les requêtes par statut (`APPROVED`, `PENDING`, `DEPRECATED`, `REJECTED`).
6. **Évolution de Schéma & Invalidation Automatique** :
   * Test de dépréciation automatique des requêtes incompatibles lors d'un changement de version de schéma.

---

## 6. Critères d'Acceptation de l'Étape 8

* [x] Les DTO d'actions administratives (`QueryApprovalPayload`, etc.) sont intégrés aux contrats.
* [x] Le module `app/reporting/catalog_manager.py` est implémenté et typé avec rigueur.
* [x] L'intégration avec `query_catalog.py` permet le cycle de vie dynamique complet (`PENDING` $\rightarrow$ `APPROVED` $\rightarrow$ `DEPRECATED`).
* [x] Aucune régression sur les 96 tests existants (Steps 2 à 7).
* [x] La nouvelle suite `tests/test_step_8_catalog_manager.py` passe à 100% (9 tests validés en ~0.09s).
* [x] Le document maître `PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md` est mis à jour pour acter la transition vers le Step 9.

