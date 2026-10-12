# Plan Détaillé Step 6 : Validateur AST SQL & Bloqueur de Requêtes (Bouclier de Sécurité avec sqlglot)

> **Document officiel de référence — Step 6 (Text-to-SQL Gouverné)**  
> **Conformité** : Section 11 et Point 6 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (`SqlValidationResult`, `TextToSQLCandidate` validés par 15 tests).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests validés).  
> • Résolution d'intention & Fast-Path : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py) et [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py) (19 tests validés).  
> • Schema Retriever & Générateur SQL : [`PLAN_DETAIL_STEP_5.md`](./PLAN_DETAIL_STEP_5.md), [`app/reporting/schema_retriever.py`](../app/reporting/schema_retriever.py) et [`app/reporting/sql_generator.py`](../app/reporting/sql_generator.py) (12 tests validés).

---

## 1. Objectif Fondamental du Step 6 : Le Bouclier de Sécurité

Dans l'architecture de reporting Text-to-SQL gouverné, **aucun code SQL généré par un LLM n'est jamais exécuté aveuglément**. 
Entre la génération du candidat au Step 5 et l'exécution SQL au Step 7, le **Validateur AST SQL** constitue l'ultime rempart de sécurité.

Il remplit une mission critique :
1. **Dépassement du filtrage textuel naïf** :
   * Ne jamais se contenter de simples expressions régulières (`regex`) ou de listes de mots-clés qui sont triviales à contourner par obfuscation SQL (ex: commentaires en ligne `/* ... */`, sauts de ligne, concaténations, encodages hexadécimaux).
   * Analyser l'**Arbre Syntaxique Abstrait (AST)** complet de la requête avec un parseur SQL robuste.
2. **Garantie du mode Read-Only absolu** :
   * Refuser toute requête qui n'est pas strictement un `SELECT` (ou une CTE en lecture seule).
   * Bloquer immédiatement toute instruction de mutation (DML/DDL) ou d'administration.
3. **Application de la Whitelist de Données & Zéro Fuite de Données Sensibles** :
   * Vérifier que toutes les tables interrogées font partie de la liste blanche de `gpr_ai_reporting`.
   * **Bloquer formellement tout accès aux colonnes confidentielles** identifiées au Step 1 et marquées `is_sensitive=True` dans le Schema Catalog (`client_code`, `content`, `solution`, `email`, `description`, etc.).
4. **Vérification de l'intégrité relationnelle** :
   * Valider que les jointures (`JOIN`) s'appuient uniquement sur des relations autorisées dans le graphe officiel du `SchemaCatalog`.
5. **Neutralisation des injections et attaques par temporisation** :
   * Bannir toute fonction malveillante (`SLEEP`, `BENCHMARK`, `LOAD_FILE`, `INTO OUTFILE`).
   * Interdire les requêtes multiples (*multi-statement injections*).

---

## 2. Choix Technologique : `sqlglot`

Conformément à la feuille de route validée :
* **Bibliothèque** : [`sqlglot`](https://github.com/tobymao/sqlglot)
* **Dialecte cible** : `mysql` (version MySQL 8.0)
* **Atouts déterminants** :
  * Pure Python : installation immédiate sans dépendance binaire C/C++ ni compilation externe.
  * Analyse syntaxique complète et typage fin des nœuds AST (`exp.Select`, `exp.Table`, `exp.Column`, `exp.Join`, `exp.Anonymous`, `exp.Command`, etc.).
  * Transpilation et normalisation déterministe (`sqlglot.transpile`).
  * Dépendance déclarée : `sqlglot>=25.0.0` dans `requirements.txt`.

---

## 3. Architecture & Organisation des Fichiers

```text
app/reporting/
├── text_to_sql_contracts.py          # Step 2 : SqlValidationResult, TextToSQLCandidate
├── schema_catalog.py                 # Step 3 : Tables, colonnes (is_sensitive), relations autorisées
├── business_catalog.py               # Step 3 : Concepts, métriques, dimensions
├── query_catalog.py                  # Step 4 : Requêtes certifiées
├── intent_resolver.py                # Step 4 : Résolveur d'intention canonique
├── schema_retriever.py               # Step 5 : Sous-schéma minimal pertinent
├── sql_generator.py                  # Step 5 : Générateur SQL candidat paramétré
│
├── sql_validator.py                  # NOUVEAU (Step 6) : Bouclier de Sécurité AST
│   ├── parse_sql_ast()               # Parse en AST MySQL 8 via sqlglot
│   ├── check_statement_type()        # Règle 1 : SELECT / CTE exclusif
│   ├── check_allowed_tables()        # Règle 2 : Whitelist tables du Schema Catalog
│   ├── check_column_permissions()    # Règle 3 : Whitelist colonnes & exclusion sensibles
│   ├── check_join_integrity()        # Règle 4 : Validation des jointures selon le graphe
│   ├── check_forbidden_functions()   # Règle 5 : Blocage SLEEP, BENCHMARK, INTO OUTFILE, etc.
│   └── validate_candidate_sql()      # Point d'entrée principal retournant SqlValidationResult
│
tests/
├── test_text_to_sql_contracts.py     # 15 tests (Step 2)
├── test_schema_and_business_catalogs.py # 14 tests (Step 3)
├── test_step_4_intent_and_query_catalog.py # 19 tests (Step 4)
├── test_step_5_schema_retriever_and_sql_generator.py # 12 tests (Step 5)
└── test_step_6_sql_validator.py      # NOUVEAU (Step 6) : Suite de tests de sécurité et d'AST
```

---

## 4. Les 6 Règles de Validation et Politiques de Sécurité

### Règle 1 : Instruction `SELECT` / CTE Read-Only Exclusive
* La requête doit parser en un arbre dont la racine est strictement `exp.Select` (ou un conteneur d'expressions ne contenant que des `exp.Select` et `exp.CTE`).
* **Rejet absolu** de toute commande DML : `INSERT`, `UPDATE`, `DELETE`, `REPLACE`.
* **Rejet absolu** de toute commande DDL : `CREATE`, `DROP`, `ALTER`, `TRUNCATE`, `RENAME`.
* **Rejet absolu** de toute commande d'administration : `GRANT`, `REVOKE`, `USE`, `SET`, `SHOW`, `CALL`, `KILL`.
* **Rejet strict du multi-statements** : Présence de point-virgule `;` avec multiples instructions. L'AST ne doit contenir qu'une seule instruction SQL.

### Règle 2 : Whitelist des Tables Autorisées
* Parcours de tous les nœuds `exp.Table` dans l'AST.
* Chaque table référencée doit être formellement répertoriée dans `SCHEMA_CATALOG.tables` :
  * Tables de faits : `reporting_claim`, `reporting_suggestion`, `reporting_historique_affectations`, `reporting_reclamation_traitements`, `reporting_solution`.
  * Tables de dimensions : `reporting_product`, `reporting_service_point`, `reporting_collection_channel`, `reporting_objet`, `reporting_categorie_objet`.
* Si un paramètre optionnel `allowed_tables` est fourni (extrait par le `SchemaRetriever` au Step 5), la requête ne peut utiliser que les tables autorisées pour cette intention spécifique.
* **Blocage strict des tables système** (`information_schema.*`, `mysql.*`, `sys.*`, `performance_schema.*`).
* **Blocage strict des tables transactionnelles non reporting** (`gps_claims`, `gps_users`, etc.).

### Règle 3 : Whitelist des Colonnes et Exclusion des Données Sensibles
* Parcours de tous les nœuds `exp.Column` dans l'AST.
* Chaque colonne doit être valide pour sa table dans `SCHEMA_CATALOG.tables[table].columns`.
* **Bouclier Données Confidentielles** :
  * Si une colonne a l'attribut `is_sensitive=True` dans le `SchemaCatalog` (`client_code`, `content`, `solution`, `email`, `description`, `evaluator_notes`, `commentaire`, `motif_desaprobation`, `ai_selected_solution`), la requête est **immédiatement rejetée** avec une violation explicite.
* Rejet de `SELECT *` sans projection de colonnes explicites afin d'éviter la fuite accidentelle de colonnes sensibles nouvellement ajoutées en base.

### Règle 4 : Intégrité des Jointures (Join Integrity)
* Parcours des nœuds `exp.Join` dans l'AST.
* Types autorisés : `INNER JOIN` et `LEFT JOIN` uniquement (pas de `RIGHT JOIN`, `FULL OUTER JOIN` ou `CROSS JOIN` dangereux).
* La condition de jointure (`ON ...`) doit relier des colonnes correspondant à une relation enregistrée dans `SCHEMA_CATALOG.relationships`.

### Règle 5 : Fonctions Interdites & Neutralisation d'Injections
* Parcours des nœuds de fonctions (`exp.Anonymous`, `exp.Func`).
* Liste noire impérative :
  * Fonctions d'évasion temporelle (Time-based SQL injection) : `SLEEP`, `BENCHMARK`.
  * Fonctions de lecture / écriture de fichiers : `LOAD_FILE`, `INTO OUTFILE`, `INTO DUMPFILE`.
  * Fonctions de découverte d'environnement : `USER`, `SYSTEM_USER`, `SESSION_USER`, `CURRENT_USER`, `VERSION`, `DATABASE`, `SCHEMA`.
  * Exécution dynamique : `PREPARE`, `EXECUTE`, `DEALLOCATE`.
* Clauses bloquées : `UNION` (sauf si expressément sans risque entre tables autorisées, rejeté par précaution pour bloquer les attaques `UNION SELECT`).

### Règle 6 : Normalisation et Contrat Pydantic `SqlValidationResult`
* En cas de succès :
  * `is_valid = True`
  * `ast_digest` : chaîne normalisée représentant la signature de l'arbre.
  * `allowed_tables_checked` : liste des tables validées.
  * `allowed_columns_checked` : liste des colonnes validées.
  * `join_integrity_checked = True`
  * `violations = []`
* En cas d'échec :
  * `is_valid = False`
  * `violations` : liste détaillée de chaque manquement constaté (ex: `"Instruction non autorisée : DROP"`, `"Accès à la colonne sensible interdit : 'reporting_claim.client_code'"`).

---

## 5. Spécification des Fonctions de `app/reporting/sql_validator.py`

```python
def validate_candidate_sql(
    candidate: TextToSQLCandidate,
    allowed_tables: Optional[Set[str]] = None
) -> SqlValidationResult:
    """
    Valide un candidat SQL text-to-sql via l'AST sqlglot contre toutes les règles
    de sécurité, les tables autorisées et l'exclusion des colonnes sensibles.
    """

def validate_raw_sql(
    sql: str,
    allowed_tables: Optional[Set[str]] = None
) -> SqlValidationResult:
    """
    Valide une chaîne SQL brute via l'AST sqlglot (utilisable pour tester
    directement des requêtes ad-hoc ou les requêtes du Query Catalog).
    """

def get_ast_digest(sql: str) -> str:
    """
    Retourne une signature canonique et normalisée de l'AST SQL.
    """
```

---

## 6. Plan de Tests Unitaires (`tests/test_step_6_sql_validator.py`)

La suite de tests couvrira exhaustivement tous les scénarios nominaux et d'attaque :

1. **Cas nominaux valides** :
   * Requête d'agrégation simple (`COUNT(*)`, `SUM`, `AVG`) avec filtre WHERE et paramètre `:param`.
   * Requête ventilée avec `GROUP BY` et `ORDER BY`.
   * Requête multi-tables avec `INNER JOIN` ou `LEFT JOIN` autorisé (ex: `reporting_claim` et `reporting_service_point`).
   * Requête avec CTE (`WITH ... AS (SELECT ... ) SELECT ...`).
2. **Cas d'attaque & mutations (DML / DDL)** :
   * Détection et blocage de `DELETE FROM reporting_claim`.
   * Détection et blocage de `UPDATE reporting_claim SET status = 'RESOLU'`.
   * Détection et blocage de `INSERT INTO reporting_claim ...`.
   * Détection et blocage de `DROP TABLE reporting_claim`.
   * Détection et blocage de `ALTER TABLE reporting_claim ...`.
   * Détection et blocage de `TRUNCATE TABLE reporting_claim`.
3. **Cas d'injection SQL & Multi-statements** :
   * Tentative de multi-statement : `SELECT count(*) FROM reporting_claim; DROP TABLE reporting_claim;`.
   * Tentative d'injection `UNION SELECT password FROM users`.
4. **Cas de colonnes sensibles interdites** :
   * Tentative de sélectionner `client_code` (donnée confidentielle du plaignant).
   * Tentative de sélectionner `content` (texte brut confidentiel de la réclamation).
   * Tentative de filtrer sur une colonne sensible `WHERE email = '...'`.
   * Tentative d'utiliser `SELECT * FROM reporting_claim` (rejet de wildcard risqué).
5. **Cas de tables interdites ou hors périmètre** :
   * Requête sur `information_schema.tables`.
   * Requête sur table métier interne `gps_claims` ou `gps_users`.
   * Requête sur table fictive ou inconnue.
   * Requête utilisant une table hors du sous-schéma autorisé transmis.
6. **Cas de fonctions malveillantes** :
   * Appel à `SLEEP(5)` ou `BENCHMARK(...)`.
   * Appel à `LOAD_FILE('/etc/passwd')`.
   * Tentative de `INTO OUTFILE '/tmp/dump.csv'`.
   * Appel à `USER()`, `VERSION()`, etc.
7. **Intégration avec `TextToSQLCandidate` du Step 5** :
   * Validation directe d'un objet `TextToSQLCandidate` généré.

---

## 7. Critères d'Acceptation de l'Étape 6

* [x] `sqlglot` est ajouté aux dépendances du projet (`requirements.txt`) et installé (v30.21.0 installée dans l'environnement et le venv).
* [x] Le module `app/reporting/sql_validator.py` est implémenté et typé avec rigueur (contrat `SqlValidationResult`, validation AST MySQL 8.0, 6 règles de sécurité).
* [x] Aucune régression sur les 60 tests existants (Steps 2, 3, 4 et 5 validés à 100% en 0.014s).
* [x] La nouvelle suite `tests/test_step_6_sql_validator.py` passe à 100% avec couverture complète des cas nominaux et d'attaque (22 tests validés en 0.102s).
* [x] Le document maître `PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md` est mis à jour pour acter la transition vers le Step 7.
