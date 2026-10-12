# Architecture Cible et Plan d'Implantation — Reporting IA (Text-to-SQL Gouverné)

> **Document de référence officiel**  
> Ce document formalise l'**architecture cible validée** et son plan d'implantation par étapes, en conformité intégrale avec le schéma directeur validé (`mermaid-diagram.svg`) et [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md).

---

## 1. L'Architecture Cible Validée

Voici le schéma officiel et complet du flux de traitement d'une question dans le Reporting IA :

```mermaid
flowchart TD
    Q["Question utilisateur"] --> INT["Nemotron : Intention canonique (concepts, mesures, dimensions, dates)"]
    INT --> QC{"Query Catalog\n(Requête approuvée ?)"}
    
    QC -- "Oui" --> EXEC["Application des paramètres & Exécution SQL (Read-Only)"]
    
    QC -- "Non" --> SCH["Schema Retriever : Sous-schéma minimal pertinent\n(Schema & Business Catalogs)"]
    SCH --> CAND["Génération SQL candidat paramétré (:param)"]
    CAND --> AST{"Validateur AST SQL\n(SELECT seul, tables/colonnes whitelistées, aucun DROP/INSERT/etc.)"}
    
    AST -- "Valide" --> EXEC
    AST -- "Invalide / Hors périmètre" --> REF["Refus ou demande de clarification"]
    
    EXEC --> RESP["FastAPI : Construction de ReportingQueryResponse\n(Chiffres réels + Datasets Chart.js)"]
    RESP --> REACT["Front React (AiQueryVisualization.jsx)"]
    
    EXEC -.-> REV["Revue humaine optionnelle avant promotion dans Query Catalog"]
```

---

## 2. Explication Détaillée des Composants de l'Architecture Cible

### 2.1. Entrée & Interprétation
1. **Question utilisateur** :
   * Posée depuis le chatbot du Front React ([`AiQueryVisualization.jsx`](../../gpr_client_sicma_new_version/src/pages/Rapports/AiQueryVisualization.jsx)).
2. **Nemotron : Intention canonique** :
   * Le modèle LLM n'écrit pas de SQL à cette étape.
   * Il extrait la structure formelle de la demande : entité (`case`), mesure (`case_count`), dimensions demandées (`agency`, `channel`, etc.), filtres et période temporelle (convertie en intervalle semi-ouvert `[début, fin[` selon le fuseau horaire `Africa/Porto-Novo`).
   * Si la question est incomplète ou ambiguë (ex: "depuis lundi"), le statut est marqué comme demandant clarification.

### 2.2. Le double circuit : Requête Approuvée vs Génération Contrôlée
3. **Query Catalog (Requête approuvée ?)** :
   * **Branche OUI (Circuit Rapide & Certifié)** :
     * Si l'intention canonique correspond à une requête déjà validée et enregistrée dans le catalogue, **aucun LLM n'est sollicité pour générer du SQL**.
     * Le backend injecte simplement les paramètres dynamiques (dates, valeurs de filtres) dans la requête pré-approuvée et passe immédiatement à l'exécution.
   * **Branche NON (Circuit Génératif Supervisé)** :
     * La question est nouvelle ou inédite. On enclenche alors le sous-système de génération contrôlée.

4. **Schema Retriever (Schema & Business Catalogs)** :
   * Le LLM ne reçoit **jamais** l'intégralité de la base de données ni de données sensibles/personnelles.
   * Le *Schema Retriever* extrait du *Schema Catalog* et du *Business Catalog* uniquement le **sous-schéma minimal pertinent** pour répondre à l'intention (tables et colonnes strictement nécessaires).

5. **Génération SQL candidat paramétré (`:param`)** :
   * Le LLM produit une requête SQL candidate contenant des **paramètres liés** (ex: `:start_date`, `:agency_param`), sans aucune concaténation directe de valeurs textuelles.

6. **Validateur AST SQL (Le Bouclier de Sécurité)** :
   * Analyse structurelle de l'arbre syntaxique abstrait (AST) :
     * Vérification de l'instruction : uniquement `SELECT` (ou CTE read-only).
     * Whitelist stricte des tables : uniquement les tables analytiques autorisées de `gpr_ai_reporting` inventoriées au Step 1 (`reporting_claim`, `reporting_suggestion`, `reporting_historique_affectations`, `reporting_solution`, `reporting_product`, `reporting_service_point`, etc.).
     * Whitelist stricte des colonnes autorisées (exclusion formelle des colonnes sensibles : `client_code`, `content`, `solution`, mots de passe, etc.).
     * Whitelist stricte des jointures : uniquement `INNER JOIN` et `LEFT JOIN` sur les clés primaires/étrangères déclarées dans le Schema Catalog.
     * Rejet absolu de tout mot-clé de mutation (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.) ou de fonction suspecte (`SLEEP`, `BENCHMARK`, etc.).
   * **Si Invalide / Hors périmètre** : Rejet immédiat ou demande de clarification. Aucune requête n'est envoyée à la base.
   * **Si Valide** : Passage à l'exécution.

### 2.3. Exécution & Restitution
7. **Application des paramètres & Exécution SQL (Read-Only)** :
   * Point de convergence des deux branches (requête approuvée OU requête candidate validée par l'AST).
   * Exécution sous compte restreint en lecture seule sur la base miroir `gpr_ai_reporting` avec timeout strict de 3s et quota `LIMIT 500`.

8. **Restitution & Gouvernance** :
   * **Vers l'utilisateur** : FastAPI lit les lignes SQL retournées par la base et construit la réponse structurée `ReportingQueryResponse` (chiffres réels + `labels`/`datasets` pour Chart.js), puis la transmet au Front React.
   * **Vers la gouvernance (boucle d'apprentissage continu)** : Une requête candidate qui a été exécutée avec succès peut faire l'objet d'une **revue humaine optionnelle** par les administrateurs pour être promue dans le *Query Catalog* et servir pour les futures questions similaires.

---

## 3. Feuille de Route d'Implantation Séquentielle (10 Steps)

Conformément à la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md), l'implantation suit 10 étapes séquentielles sans aucun court-circuit :

```mermaid
flowchart TD
    S1["Step 1 : Inventaire gpr_ai_reporting, données sensibles, dialecte\n[TERMINÉ - INVENTAIRE_STEP_1.md]"] --> S2["Step 2 : Contrats versionnés (Intention, Schema, Business, SQL, Approbation)\n[TERMINÉ - PLAN_DETAIL_STEP_2.md & text_to_sql_contracts.py]"]
    S2 --> S3["Step 3 : Construction Schema Catalog & Business Catalog\n[TERMINÉ - PLAN_DETAIL_STEP_3.md, schema_catalog.py, business_catalog.py]"]
    S3 --> S4["Step 4 : Résolution d'intention & Query Catalog (Exact/Sémantique)\n[TERMINÉ - PLAN_DETAIL_STEP_4.md, query_catalog.py, intent_resolver.py]"]
    S4 --> S5["Step 5 : Schema Retriever & Prompt Nemotron minimal\n[TERMINÉ - PLAN_DETAIL_STEP_5.md, schema_retriever.py, sql_generator.py]"]
    S5 --> S6["Step 6 : Validateur AST SQL & Bloqueur de requêtes\n[TERMINÉ - PLAN_DETAIL_STEP_6.md, sql_validator.py]"]
    S6 --> S7["Step 7 : Exécution Read-Only, Bind Params & Audit\n[TERMINÉ - PLAN_DETAIL_STEP_7.md, sql_executor.py, audit_service.py]"]
    S7 --> S8["Step 8 : Approbation humaine & Gestion du Query Catalog\n[TERMINÉ - PLAN_DETAIL_STEP_8.md, catalog_manager.py]"]
    S8 --> S9["Step 9 : Contrats de réponse & Validation Front React\n[TERMINÉ - PLAN_DETAIL_STEP_9.md, response_builder.py, text_to_sql_pipeline.py]"]
    S9 --> S10["Step 10 : Bascule Définitive sur Text-to-SQL & Nettoyage Ancien Moteur\n[TERMINÉ - PLAN_DETAIL_STEP_10.md, router.py, service.py]"]
```

---

### Détail des Étapes et Jalons de Réalisation :

| Étape | Intitulé & Livrables Clés | Statut |
| :--- | :--- | :--- |
| **Step 1** | **Inventaire complet de `gpr_ai_reporting`** :<br>• Cartographie des 12 tables (Dossiers réclamations/dénonciations, suggestions, traitement, référentiels, suivi).<br>• Matrice d'exclusion des données sensibles.<br>• Règles d'accès lecture seule et dialecte MySQL 8.0.<br>📄 *Livrable : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)* | ✅ **Terminé** |
| **Step 2** | **Contrats versionnés d'intention, catalogues, SQL candidat et approbation** :<br>• Modèles Pydantic pour `CanonicalIntent` (réclamations, dénonciations, suggestions, traitement, filtres, temps).<br>• Modèles Pydantic pour `SchemaCatalog` et `BusinessCatalog`.<br>• Modèles pour `SqlCandidate` (SQL paramétré `:param`) et `SqlValidationResult`.<br>• Modèles d'approbation et statut dans le `QueryCatalog`.<br>• 15 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md), [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py)* | ✅ **Terminé** |
| **Step 3** | **Construction du Schema Catalog & Business Catalog** :<br>• Définition statique et persistante des 13 tables analytiques et de gestion + 2 tables d'administration.<br>• Marquage strict `is_sensitive=True` et filtre de sous-schéma sans données confidentielles.<br>• Graphe des 15 jointures officielles autorisées (`LEFT JOIN` / `INNER JOIN`).<br>• Dictionnaire métier : 5 concepts, 10 métriques (dont `plainte_count` unifié), 10 dimensions et résolveur lexical insensible aux accents.<br>• 14 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py), [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py)* | ✅ **Terminé** |
| **Step 4** | **Résolution d'intention & Query Catalog (Recherche exacte / sémantique)** :<br>• Résolveur d'intention canonique en langage naturel (contrat `TextToSQLIntent`).<br>• Prompt Nemotron d'extraction d'intention stricte (format JSON pur, zéro SQL généré).<br>• Catalogue initial des 8 requêtes certifiées homologuées (`status=ApprovalStatus.APPROVED`).<br>• Moteur de matching direct sur le catalogue (Fast-Path court-circuit immédiat avec liaison des paramètres).<br>• 19 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py), [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py)* | ✅ **Terminé** |
| **Step 5** | **Schema Retriever & Prompt Nemotron de génération SQL** :<br>• Sélection ciblée et automatique du sous-schéma minimal pertinent selon l'intention canonique.<br>• Résolution automatique des tables passerelles (bridge tables) nécessaires aux jointures.<br>• Prompt de génération SQL candidat pour Nemotron restreint au sous-schéma extrait (zéro fuite sensible).<br>• Validation et désérialisation Pydantic conforme au contrat `TextToSQLCandidate`.<br>• 12 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_5.md`](./PLAN_DETAIL_STEP_5.md), [`app/reporting/schema_retriever.py`](../app/reporting/schema_retriever.py), [`app/reporting/sql_generator.py`](../app/reporting/sql_generator.py)* | ✅ **Terminé** |
| **Step 6** | **Validateur AST SQL & Sécurité (Bouclier avec sqlglot)** :<br>• Parseur AST SQL (avec `sqlglot` MySQL 8) : validation structurelle `SELECT` exclusif, whitelists tables/colonnes/joins, blocage absolu de toute injection ou mutation.<br>• Exclusion impérative des données sensibles (`client_code`, `content`, `solution`, etc.).<br>• 22 tests unitaires de sécurité exhaustifs (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_6.md`](./PLAN_DETAIL_STEP_6.md), [`app/reporting/sql_validator.py`](../app/reporting/sql_validator.py)* | ✅ **Terminé** |
| **Step 7** | **Exécution Read-Only & Audit** :<br>• Exécuteur sécurisé avec paramètres liés (`:param`), quota `LIMIT 500`, timeout 3 secondes.<br>• Journalisation d'audit des requêtes exécutées avec masquage des données sensibles et mise à jour des statistiques QueryCatalog.<br>• 14 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_7.md`](./PLAN_DETAIL_STEP_7.md), [`app/reporting/sql_executor.py`](../app/reporting/sql_executor.py), [`app/reporting/audit_service.py`](../app/reporting/audit_service.py)* | ✅ **Terminé** |
| **Step 8** | **Approbation humaine & Cycle de vie des requêtes** :<br>• Gestionnaire du cycle de vie des requêtes (`catalog_manager.py`).<br>• Soumission de candidate (`PENDING`), promotion (`APPROVED`), rejet (`REJECTED`), dépréciation (`DEPRECATED`).<br>• Auto-promotion immédiate des requêtes exécutées avec succès et boucle de feedback utilisateur.<br>• Vérification AST bloquante obligatoire avant promotion.<br>• Invalidation / dépréciation automatique sur évolution du schéma.<br>• 16 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_8.md`](./PLAN_DETAIL_STEP_8.md), [`PLAN_DETAIL_FEEDBACK_AUTO_LEARNING.md`](./PLAN_DETAIL_FEEDBACK_AUTO_LEARNING.md), [`app/reporting/catalog_manager.py`](../app/reporting/catalog_manager.py)* | ✅ **Terminé** |
| **Step 9** | **Contrats de réponse & Validation Front React** :<br>• Constructeur de réponse (`response_builder.py`) : génération `labels` et `datasets` Chart.js depuis les lignes SQL réelles (zéro hallucination de chiffres).<br>• Orchestrateur Text-to-SQL unifié (`text_to_sql_pipeline.py`) reliant les briques 4 à 9 (Fast-Path, anti-patterns, AST shield, auto-promotion, audit).<br>• Conformité stricte avec le contrat public `ReportingQueryResponse` (support du champ `query_id`).<br>• Endpoint FastAPI `POST /reporting/feedback` pour le retour utilisateur.<br>• 14 tests unitaires validés (100% succès).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_9.md`](./PLAN_DETAIL_STEP_9.md), [`app/reporting/response_builder.py`](../app/reporting/response_builder.py), [`app/reporting/text_to_sql_pipeline.py`](../app/reporting/text_to_sql_pipeline.py), [`tests/test_step_9_response_builder.py`](../tests/test_step_9_response_builder.py)* | ✅ **Terminé** |
| **Step 10** | **Bascule Définitive sur le Text-to-SQL Gouverné & Nettoyage** :<br>• Remplacement direct de l'ancien moteur monolithique `answer_query` dans `service.py`.<br>• Branchage direct de `POST /reporting/query` sur `execute_text_to_sql_pipeline`.<br>• Sanctuarisation de `build_dashboard` (`GET /reporting/dashboard`).<br>• Alias rétrocompatible `answer_query` redirigeant vers le pipeline gouverné.<br>• Suite d'intégration E2E FastAPI (8/8 tests validés, 134 tests cumulés au total).<br>📄 *Livrables : [`PLAN_DETAIL_STEP_10.md`](./PLAN_DETAIL_STEP_10.md), [`app/reporting/router.py`](../app/reporting/router.py), [`app/reporting/service.py`](../app/reporting/service.py), [`tests/test_step_10_final_integration.py`](../tests/test_step_10_final_integration.py)* | ✅ **Terminé** |



