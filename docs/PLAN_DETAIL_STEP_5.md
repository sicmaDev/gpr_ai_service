# Plan Détaillé Step 5 : Schema Retriever & Génération SQL Nemotron (Sous-schéma Minimal & Zéro Fuite de Données)

> **Document officiel de référence — Step 5 (Text-to-SQL Gouverné)**  
> **Conformité** : Point 5 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests validés).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests validés).  
> • Résolution d'intention & Fast-Path : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py) et [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py) (19 tests validés).

---

## 1. Objectif Fondamental du Step 5

Lorsque l'appariement direct du **Step 4** ne trouve aucune requête pré-approuvée homologuée dans le `QueryCatalog` (**Fast-Path MISS**), la demande bascule sur le **circuit génératif supervisé**.

Le **Step 5** résout le défi central de la sécurité et de la précision de cette génération :
1. **Éviter la saturation du contexte LLM et le risque d'hallucination** :
   * Ne **jamais** envoyer les 13 tables et la centaine de colonnes de la base au modèle.
   * Le **Schema Retriever** isole dynamiquement le **sous-ensemble minimal strict** de tables et de colonnes nécessaires pour répondre à l'intention canonique (`TextToSQLIntent`).
2. **Garantir l'étanchéité absolue des données sensibles** :
   * Aucune colonne marquée `is_sensitive=True` (`client_code`, `content`, `solution`, `email`, `description`, etc.) ne doit être injectée dans le prompt Nemotron.
3. **Encadrer formellement la génération SQL candidate** :
   * Construire un prompt Nemotron strict imposant :
     * L'instruction `SELECT` exclusive.
     * Des paramètres liés (`:param`) obligatoires (aucune concaténation de texte ou de dates).
     * Des jointures autorisées limitées au graphe officiel du `SchemaCatalog`.
     * Une sortie au format JSON pur désérialisée en un contrat Pydantic typé **`TextToSQLCandidate`** (prêt à être audité par le Validateur AST au Step 6).

---

## 2. Architecture & Organisation des Fichiers

```text
app/reporting/
├── text_to_sql_contracts.py          # Step 2 : Contrats Pydantic (Validé - 15 tests)
├── schema_catalog.py                 # Step 3 : Cartographie des 13 tables & 15 jointures (Validé)
├── business_catalog.py               # Step 3 : Métriques, concepts, dimensions & synonymes (Validé)
├── query_catalog.py                  # Step 4 : Requêtes certifiées & Fast-Path Matching (Validé)
├── intent_resolver.py                # Step 4 : Résolveur d'intention canonique (Validé)
│
├── schema_retriever.py               # NOUVEAU (Step 5) : Extracteur dynamique de sous-schéma minimal
│   ├── resolve_required_tables()     # Identification des tables (faits, dimensions, passerelles)
│   └── retrieve_minimal_subschema()  # Extraction textuelle du sous-schéma sans données sensibles
│
├── sql_generator.py                  # NOUVEAU (Step 5) : Générateur de requêtes SQL candidates
│   ├── build_sql_generation_prompt() # Prompt Nemotron strict (sous-schéma minimal + règles :param)
│   ├── parse_candidate_response()    # Désérialisation et validation Pydantic en TextToSQLCandidate
│   └── generate_candidate_fallback() # Générateur déterministe hors-ligne (mode test/fallback)
│
tests/
├── test_text_to_sql_contracts.py     # Tests Step 2 (15 tests)
├── test_schema_and_business_catalogs.py # Tests Step 3 (14 tests)
├── test_step_4_intent_and_query_catalog.py # Tests Step 4 (19 tests)
└── test_step_5_schema_retriever_and_sql_generator.py # NOUVEAU (Step 5) : Tests Retriever & Générateur
```

---

## 3. Détail du Fichier `schema_retriever.py`

Le composant analyse l'objet `TextToSQLIntent` résolu au Step 4 pour déterminer l'ensemble exact des tables utiles :

### 3.1. Algorithme de Résolution des Tables (`resolve_required_tables`)

1. **Tables requises par la métrique (`intent.measure.concept_id`)** :
   * Consultation de `BUSINESS_CATALOG.metrics[metric_id].required_tables`.
   * *Exemples* :
     * `reclamation_count` $\rightarrow$ `["reporting_claim"]`
     * `plainte_count` $\rightarrow$ `["reporting_claim", "reporting_suggestion"]`
     * `suggestion_count` $\rightarrow$ `["reporting_suggestion"]`
     * `reaffectation_count` $\rightarrow$ `["reporting_historique_affectations"]`
2. **Tables requises par les dimensions (`intent.dimensions`)** :
   * Consultation de `BUSINESS_CATALOG.dimensions[dim_id].source_table`.
   * *Exemples* :
     * `agency` $\rightarrow$ `reporting_service_point`
     * `channel` $\rightarrow$ `reporting_collection_channel`
     * `product` $\rightarrow$ `reporting_product`
     * `object` $\rightarrow$ `reporting_objet`
     * `category` $\rightarrow$ `reporting_categorie_objet`
3. **Résolution automatique des tables passerelles (Bridge Tables)** :
   * Si une dimension cible ne se joint pas directement à la table de faits principale, la table intermédiaire doit être automatiquement ajoutée au sous-schéma.
   * *Cas d'usage concret* :
     * Pour ventiler les réclamations par catégorie de motif (`category`), la jointure s'effectue via `reporting_objet` :  
       `reporting_claim.objet_id = reporting_objet.id` puis `reporting_objet.categorie_id = reporting_categorie_objet.id`.  
       $\rightarrow$ `reporting_objet` est automatiquement injectée même si l'utilisateur ne l'a pas explicitement demandée.
4. **Tables requises par les filtres (`intent.filters`)** :
   * Ajout des tables contenant les colonnes cibles des filtres actifs.

### 3.2. Extraction du Sous-Schéma Textuel (`retrieve_minimal_subschema`)

* Appel de `get_minimal_subschema(selected_tables)` défini au Step 3.
* **Garantie de non-régression et de sécurité** :
  * Seules les tables identifiées sont décrites.
  * Seules les jointures reliant ces tables sont documentées.
  * **Toutes les colonnes marquées `is_sensitive=True` sont automatiquement masquées**.

---

## 4. Détail du Fichier `sql_generator.py`

Le composant orchestre la construction du prompt Nemotron et garantit que toute sortie produite est conforme au contrat strict `TextToSQLCandidate`.

### 4.1. Règles Imposées dans le Prompt Nemotron

1. **Dialecte & Syntaxe** : MySQL 8.0 / SQLite compatible ANSI.
2. **Paramètres Liés Obligatoires (`:param`)** :
   * Interdiction de concaténer des dates en dur (*ex: `WHERE receipt_at >= '2026-09-01'` $\rightarrow$ INTERDIT*).
   * Obligation d'écrire : `WHERE receipt_at >= :start_date AND receipt_at < :end_date`.
3. **Instruction `SELECT` Exclusive** :
   * Aucune mutation (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc.).
4. **Jointures Strictement Autorisées** :
   * Uniquement les relations listées dans la section `RELATIONS & JOINTURES AUTORISÉES` du sous-schéma.
5. **Format de Sortie Exclusif** :
   * Bloc JSON strict correspondant au contrat `TextToSQLCandidate` :
     ```json
     {
       "contract_version": "1.0",
       "sql": "SELECT sp.libelle AS agency, COUNT(c.id) AS case_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY sp.libelle ORDER BY case_count DESC",
       "parameters": {
         "start_date": {"type": "datetime", "source": "intent.time.start_date"},
         "end_date": {"type": "datetime", "source": "intent.time.end_date"}
       },
       "used_schema": ["reporting_claim", "reporting_service_point"],
       "result_columns": [
         {"name": "agency", "concept_id": "agency", "role": "dimension", "data_type": "string"},
         {"name": "case_count", "concept_id": "case_count", "role": "measure", "data_type": "integer"}
       ],
       "assumptions": ["Exclusion des dossiers brouillons par construction"]
     }
     ```

### 4.2. Mode Déterministe Hors-Ligne (Fallback & Tests)

Pour assurer une fiabilité continue même en cas de coupure réseau ou d'indisponibilité du service Nemotron :
* [`generate_candidate_fallback(intent)`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/sql_generator.py) construit une requête SQL candidate paramétrée valide à partir des métadonnées du `BusinessCatalog` et du `SchemaCatalog`.

---

## 5. Tests Unitaires du Step 5 (`tests/test_step_5_schema_retriever_and_sql_generator.py`)

1. **Test de sélection minimale des tables** :
   * Pour une intention `reclamation_count` par `agency` $\rightarrow$ tables sélectionnées = `['reporting_claim', 'reporting_service_point']` exactement.
   * Pour une intention `plainte_count` $\rightarrow$ inclusion conjointe de `reporting_claim` et `reporting_suggestion`.
2. **Test de détection des tables passerelles** :
   * Pour une dimension `category` sur `reporting_claim` $\rightarrow$ inclusion obligatoire de `reporting_objet` pour rendre la jointure possible.
3. **Test d'étanchéité absolue aux données sensibles** :
   * Vérification systématique que le sous-schéma généré pour Nemotron ne contient ni `client_code`, ni `content`, ni `solution`, ni `email`.
4. **Test de formatage du prompt Nemotron** :
   * Présence du sous-schéma textuel et des consignes formelles `:param` et `SELECT`.
5. **Test du parseur `TextToSQLCandidate`** :
   * Validation de désérialisation d'un JSON valide.
   * Rejet si `result_columns` est vide ou comporte des colonnes en doublon (règle Pydantic Step 2).
6. **Test du générateur déterministe de fallback** :
   * Production d'un `TextToSQLCandidate` 100% valide avec liaisons `:start_date` / `:end_date`.
7. **Non-régression totale** :
   * Maintien des 48 tests unitaires précédents (Steps 2, 3 et 4) au vert.

---

## 6. Critères de Réussite du Step 5

* [ ] `app/reporting/schema_retriever.py` est implémenté et isole fidèlement le sous-schéma minimal.
* [ ] `app/reporting/sql_generator.py` est implémenté et produit des candidats conformes à `TextToSQLCandidate`.
* [ ] Aucune colonne sensible n'apparaît dans les données transmises au LLM.
* [ ] La suite de tests unitaires `test_step_5_schema_retriever_and_sql_generator.py` passe avec 100% de succès.
* [ ] La suite globale (Steps 2, 3, 4 et 5) passe sans aucune régression.
* [ ] Le système est prêt pour le **Step 6** (Validateur AST SQL avec `sqlglot`).
