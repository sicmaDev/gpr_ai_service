# Plan Détaillé Step 9 : Contrats de Réponse & Validation Front React

> **Document officiel de référence — Step 9 (Text-to-SQL Gouverné)**  
> **Conformité** : Section 12 et Point 9 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests validés).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests validés).  
> • Résolution d'intention & Fast-Path : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py) et [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py) (19 tests validés).  
> • Schema Retriever & Générateur SQL : [`PLAN_DETAIL_STEP_5.md`](./PLAN_DETAIL_STEP_5.md), [`app/reporting/schema_retriever.py`](../app/reporting/schema_retriever.py) et [`app/reporting/sql_generator.py`](../app/reporting/sql_generator.py) (12 tests validés).  
> • Validateur AST SQL sqlglot : [`PLAN_DETAIL_STEP_6.md`](./PLAN_DETAIL_STEP_6.md) et [`app/reporting/sql_validator.py`](../app/reporting/sql_validator.py) (22 tests validés).  
> • Exécuteur Read-Only & Audit : [`PLAN_DETAIL_STEP_7.md`](./PLAN_DETAIL_STEP_7.md), [`app/reporting/sql_executor.py`](../app/reporting/sql_executor.py) et [`app/reporting/audit_service.py`](../app/reporting/audit_service.py) (14 tests validés).  
> • Approbation Humaine & Query Catalog : [`PLAN_DETAIL_STEP_8.md`](./PLAN_DETAIL_STEP_8.md) et [`app/reporting/catalog_manager.py`](../app/reporting/catalog_manager.py) (9 tests validés).  
> • Auto-Promotion & Boucle de Feedback : [`PLAN_DETAIL_FEEDBACK_AUTO_LEARNING.md`](./PLAN_DETAIL_FEEDBACK_AUTO_LEARNING.md) (7 tests validés).  
> **Suite de tests actuelle** : 112 tests unitaires validés à 100% en 0.28s.

---

## 1. Objectif Fondamental du Step 9 : Restitution Standardisée & Intégration Front-End

L'objectif du Step 9 est de relier la sortie du moteur d'exécution SQL ([`SqlExecutionResult`](../app/reporting/text_to_sql_contracts.py)) au contrat d'interface officiel [`ReportingQueryResponse`](../app/reporting/schemas.py) consommé par le Front React :

1. **Autorité stricte du Backend sur les chiffres et les graphiques** :
   * Le LLM ne choisit **jamais** les valeurs numériques des graphiques.
   * Le backend extrait les données brutes retournées par la requête SQL et formate lui-même les structures `labels` et `datasets` compatibles avec **Chart.js**.
2. **Conformité stricte au contrat `ReportingQueryResponse`** :
   * `answer` : Réponse rédigée en langage naturel résumant fidèlement les résultats réels.
   * `summary` : Titre ou résumé synthétique de l'analyse (ex: *"Nombre de réclamations par agence"*).
   * `query_id` : Identifiant unique de la requête dans le catalogue pour permettre le feedback utilisateur direct (pouce levé / signalement d'incohérence).
   * `sources` : Liste des tables analytiques réelles consultées (ex: `["reporting_claim", "reporting_service_point"]`).
   * `visualization` : Objet optionnel `Visualization` (`type`, `title`, `labels`, `datasets`).
   * `data` : Liste des enregistrements sous forme tabulaire pour affichage dans la table de données de l'interface.
   * `comparison` : Résultats comparatifs de périodes le cas échéant.

3. **Sélection intelligente du type de graphique (`Visualization.type`)** :
   * Dimension temporelle (`period`, `month`, `receipt_date`) $\rightarrow$ Graphique linéaire (`"line"`).
   * Dimensions catégorielles discrètes (`agency`, `channel`, `category`, `product`, `status`) $\rightarrow$ Graphique en barres (`"bar"`).
   * Répartition de parts limitées (<= 5 catégories) $\rightarrow$ Graphique circulaire (`"pie"` ou `"doughnut"`).
   * Mesure scalaire unique (valeur simple sans dimension) $\rightarrow$ Restitution textuelle directe ou KPI card.
4. **Assemblage du Pipeline Text-to-SQL Unifié (`text_to_sql_pipeline.py`)** :
   * Intégration de l'enchaînement complet : Résolution d'intention (Step 4) $\rightarrow$ Circuit Fast-Path (Step 4 & 8) $\rightarrow$ Sinon Génération supervisée (Step 5, avec apprentissage des anti-patterns rejetés) $\rightarrow$ Bouclier AST (Step 6) $\rightarrow$ Exécution Read-Only (Step 7) $\rightarrow$ Journalisation Audit (Step 7) $\rightarrow$ Restitution Front (Step 9).

---

## 2. Architecture & Organisation des Modules

```text
app/reporting/
├── text_to_sql_contracts.py          # Contrats internes gouvernés (Steps 2, 7, 8)
├── schemas.py                        # Contrat public API : ReportingQueryResponse, Visualization
├── schema_catalog.py                 # Catalogue de schéma (Step 3)
├── business_catalog.py               # Dictionnaire métier & synonymes (Step 3)
├── query_catalog.py                  # Registre Fast-Path & requêtes homologuées (Step 4 & 8)
├── intent_resolver.py                # Résolution canonique (Step 4)
├── schema_retriever.py               # Extraction sous-schéma minimal (Step 5)
├── sql_generator.py                  # Génération SQL candidate & Few-Shots (Step 5)
├── sql_validator.py                  # Bouclier AST sqlglot (Step 6)
├── sql_executor.py                   # Moteur d'exécution Read-Only (Step 7)
├── audit_service.py                  # Audit et métriques d'exécution (Step 7)
├── catalog_manager.py                # Cycle de vie et approbation (Step 8)
│
├── response_builder.py               # NOUVEAU (Step 9) : Constructeur de ReportingQueryResponse
│   ├── build_reporting_query_response()  # Transformation SqlExecutionResult -> ReportingQueryResponse
│   ├── format_chartjs_visualization()    # Construction labels & datasets Chart.js
│   ├── select_chart_type()               # Détection du type de graphique approprié
│   └── formulate_natural_answer()        # Synthèse textuelle basée sur les chiffres réels
│
├── text_to_sql_pipeline.py           # NOUVEAU (Step 9) : Orchestrateur du pipeline complet
│   └── execute_text_to_sql_pipeline()    # Entrée unifiée recevant la question et les filtres
│
tests/
├── test_text_to_sql_contracts.py     # 15 tests
├── test_schema_and_business_catalogs.py # 14 tests
├── test_step_4_intent_and_query_catalog.py # 19 tests
├── test_step_5_schema_retriever_and_sql_generator.py # 12 tests
├── test_step_6_sql_validator.py      # 22 tests
├── test_step_7_sql_executor_and_audit.py # 14 tests
├── test_step_8_catalog_manager.py    # 9 tests
└── test_step_9_response_builder.py   # NOUVEAU (Step 9) : Tests transformation & pipeline
```

---

## 3. Spécification des Fonctions de `response_builder.py`

### 3.1. `select_chart_type(intent: TextToSQLIntent, row_count: int) -> Optional[str]`
* Détecte si une visualisation graphique a du sens :
  * Si aucune dimension n'est demandée (mesure scalaire unique, ex: "Quel est le total ?") $\rightarrow$ `None` ou `"bar"` à valeur unique.
  * Si la dimension principale est temporelle (`receipt_date`, `month`, `year`) $\rightarrow$ `"line"`.
  * Si la dimension est discrète avec peu de modalités ($\le 5$) et une intention de répartition $\rightarrow$ `"pie"`.
  * Par défaut pour les regroupements (agences, canaux, catégories, etc.) $\rightarrow$ `"bar"`.

### 3.2. `format_chartjs_visualization(intent, columns, rows) -> Optional[Visualization]`
* Extrait les labels : valeurs de la colonne dimension (ex: `sp.libelle` $\rightarrow$ `["Agence Littoral", "Agence Atlantique"]`).
* Extrait les datasets : valeurs numériques réelles converties en `float`/`int` (ex: `[120, 85]`).
* Assigne le libellé de série depuis `intent.measure.label` (ex: `"Nombre de réclamations"`).
* Retourne l'instance Pydantic `Visualization` rigoureusement typée.

### 3.3. `formulate_natural_answer(question, intent, rows, total_value) -> str`
* Rédige un message clair, concis et factuel pour l'utilisateur.
* Exemple pour une ventilation par agence :  
  *"Pour la période demandée, un total de 205 réclamations a été enregistré, avec la répartition suivante par agence : Agence Littoral (120), Agence Atlantique (85)."*
* Exemple pour un résultat vide (0 ligne) :  
  *"Aucun enregistrement ne correspond aux critères demandés pour cette période."*

### 3.4. `build_reporting_query_response(execution_result, intent, natural_language_query, sources) -> ReportingQueryResponse`
* Assemble tous les blocs : `answer`, `summary`, `sources`, `visualization`, `data`, `comparison`.
* Garantit la sérialisation JSON immédiate pour l'API REST FastAPI.

---

## 4. Spécification de l'Orchestrateur `text_to_sql_pipeline.py`

Fonction principale : `execute_text_to_sql_pipeline(question: str, db_session: Session, user_filters: Optional[ReportingFilters] = None) -> ReportingQueryResponse`

1. **Étape 1 : Résolution d'intention** ([`resolve_intent`](../app/reporting/intent_resolver.py)).
   * Si non supportée ou demande de clarification : retourne immédiatement un `ReportingQueryResponse` poli invitant l'utilisateur à préciser sa demande.
2. **Étape 2 : Tentative Fast-Path** ([`match_intent_in_catalog`](../app/reporting/query_catalog.py)).
   * Si match trouvé : exécution directe de la requête homologuée avec les paramètres liés.
3. **Étape 3 : Génération supervisée (si Fast-Path miss)** :
   * Extraction du sous-schéma minimal ([`retrieve_minimal_schema`](../app/reporting/schema_retriever.py)).
   * Injection des Few-Shots positifs et des **anti-patterns rejetés** (Step 8 feedback).
   * Génération de la requête SQL candidate ([`generate_candidate_sql`](../app/reporting/sql_generator.py)).
4. **Étape 4 : Bouclier de Sécurité AST** ([`validate_candidate_sql`](../app/reporting/sql_validator.py)).
   * Si violation : blocage immédiat sans toucher la base de données.
5. **Étape 5 : Exécution Read-Only sécurisée** ([`execute_read_only_query`](../app/reporting/sql_executor.py)).
6. **Étape 6 : Traces d'Audit** ([`record_execution_audit`](../app/reporting/audit_service.py)).
7. **Étape 7 : Construction de la Réponse** ([`build_reporting_query_response`](./response_builder.py)).
   * Renvoi de l'objet `ReportingQueryResponse` directement consommable par le composant React `AiReportingCharts.jsx`.

---

## 5. Plan de Tests Unitaires (`tests/test_step_9_response_builder.py`)

1. **`test_select_chart_type`** :
   * Dimension temporelle $\rightarrow$ type `"line"`.
   * Dimension agence $\rightarrow$ type `"bar"`.
   * Sans dimension $\rightarrow$ `None` ou KPI card.
2. **`test_format_chartjs_visualization_bar`** :
   * Vérifie la structure `labels` et `datasets[0].data` sur des données d'agence.
3. **`test_format_chartjs_visualization_empty_rows`** :
   * Vérifie le comportement gracieux si la requête ne retourne aucune ligne (labels vides, datasets vides, pas de crash).
4. **`test_build_reporting_query_response_structure`** :
   * Valide que l'objet retourné est une instance de `ReportingQueryResponse` conforme au schéma Pydantic public.
5. **`test_pipeline_fast_path_end_to_end`** :
   * Exécute une question couverte par le catalogue homologué (Fast-Path) et valide le `ReportingQueryResponse` final complet.
6. **`test_pipeline_supervised_candidate_end_to_end`** :
   * Exécute une question inédite via le générateur simulé + validateur AST + exécuteur + response builder.
7. **`test_pipeline_ast_rejection_error_response`** :
   * Vérifie qu'en cas de tentative d'injection ou d'erreur AST, le pipeline retourne un message clair sans exposer de détails techniques internes.

---

## 6. Critères d'Acceptation de l'Étape 9

* [x] Le module `app/reporting/response_builder.py` est implémenté et strictement typé.
* [x] Le pipeline `app/reporting/text_to_sql_pipeline.py` orchestre proprement les briques 4 à 9.
* [x] La réponse est 100% compatible avec le schéma Pydantic `ReportingQueryResponse`.
* [x] Aucune régression sur les 112 tests unitaires existants (Steps 2 à 8 + Auto-learning).
* [x] La nouvelle suite `tests/test_step_9_response_builder.py` passe à 100% (14 nouveaux tests, 126 tests cumulés au total).
* [x] Le plan d'implantation maître `PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md` est mis à jour pour acter le passage au Step 10.


