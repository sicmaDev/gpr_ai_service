# Plan Détaillé Step 10 : Bascule Définitive sur le Text-to-SQL Gouverné & Nettoyage de l'Ancien Moteur

> **Document officiel de référence — Step 10 (Text-to-SQL Gouverné)**  
> **Conformité** : Section 11, Section 12 et Point 10 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés (Steps 1 à 9 + Boucle d'auto-promotion)** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests validés).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests validés).  
> • Résolution d'intention & Fast-Path : [`PLAN_DETAIL_STEP_4.md`](./PLAN_DETAIL_STEP_4.md), [`app/reporting/query_catalog.py`](../app/reporting/query_catalog.py) et [`app/reporting/intent_resolver.py`](../app/reporting/intent_resolver.py) (19 tests validés).  
> • Schema Retriever & Générateur SQL : [`PLAN_DETAIL_STEP_5.md`](./PLAN_DETAIL_STEP_5.md), [`app/reporting/schema_retriever.py`](../app/reporting/schema_retriever.py) et [`app/reporting/sql_generator.py`](../app/reporting/sql_generator.py) (12 tests validés).  
> • Validateur AST SQL sqlglot : [`PLAN_DETAIL_STEP_6.md`](./PLAN_DETAIL_STEP_6.md) et [`app/reporting/sql_validator.py`](../app/reporting/sql_validator.py) (22 tests validés).  
> • Exécuteur Read-Only & Audit : [`PLAN_DETAIL_STEP_7.md`](./PLAN_DETAIL_STEP_7.md), [`app/reporting/sql_executor.py`](../app/reporting/sql_executor.py) et [`app/reporting/audit_service.py`](../app/reporting/audit_service.py) (14 tests validés).  
> • Approbation Humaine & Query Catalog : [`PLAN_DETAIL_STEP_8.md`](./PLAN_DETAIL_STEP_8.md) et [`app/reporting/catalog_manager.py`](../app/reporting/catalog_manager.py) (9 tests validés).  
> • Auto-Promotion & Boucle de Feedback : [`PLAN_DETAIL_FEEDBACK_AUTO_LEARNING.md`](./PLAN_DETAIL_FEEDBACK_AUTO_LEARNING.md) (7 tests validés).  
> • Restitution Front React & Pipeline Unifié : [`PLAN_DETAIL_STEP_9.md`](./PLAN_DETAIL_STEP_9.md), [`app/reporting/response_builder.py`](../app/reporting/response_builder.py) et [`app/reporting/text_to_sql_pipeline.py`](../app/reporting/text_to_sql_pipeline.py) (14 tests validés).  
> **Suite de tests actuelle** : 126 tests unitaires validés à 100% en 0.62s.

---

## 1. Objectif Fondamental du Step 10 : Bascule Officielle & Simplification

Le projet étant en phase active de développement, maintenir une double exécution (*shadow mode / dual-run*) générerait une complexité inutile et une dette technique prématurée.

L'objectif de ce Step 10 est donc :
1. **Remplacement direct de l'ancien moteur** :
   * L'endpoint officiel `POST /reporting/query` est branché directement sur [`execute_text_to_sql_pipeline`](../app/reporting/text_to_sql_pipeline.py).
   * Les réponses retournées au Front React contiennent immédiatement le `query_id`, les visualisations Chart.js construites sur les données réelles et le Fast-Path certifié.
2. **Nettoyage et élimination de la dette technique** :
   * Dépréciation/remplacement de l'ancien moteur `answer_query` monolithique de `service.py`.
   * Maintien d'un alias propre pour `answer_query` redirigeant vers `execute_text_to_sql_pipeline` pour garantir une rétrocompatibilité absolue.
3. **Sanctuarisation du Dashboard fixe** :
   * La fonction `build_dashboard` dans `service.py` et la route `GET /reporting/dashboard` restent 100% intactes pour alimenter les KPI, la matrice des risques et les alertes.
4. **Validation E2E HTTP de l'API** :
   * Création d'une suite de tests d'intégration complète vérifiant le bon fonctionnement de l'API FastAPI de bout en bout.

---

## 2. Modifications Architecturales

```text
app/reporting/
├── text_to_sql_pipeline.py   # Moteur Text-to-SQL officiel gouverné
├── response_builder.py       # Restitution Chart.js sans hallucination
├── router.py                 # Routeur FastAPI : POST /query branché directement sur le pipeline
├── service.py                # Conservé pour build_dashboard() ; answer_query redirigé vers le pipeline
```

---

## 3. Plan de Tests Unitaires & d'Intégration (`tests/test_step_10_final_integration.py`)

1. **`test_post_reporting_query_fast_path`** :
   * Appel HTTP `POST /reporting/query` sur une question certifiée (ex: "Nombre de réclamations par agence en 2026").
   * Vérifie le code HTTP 200, la présence de `query_id="QC-CLAIM-COUNT-BY-AGENCY"`, les `sources` et le graphique `bar`.
2. **`test_post_reporting_query_supervised_auto_promotion`** :
   * Appel HTTP `POST /reporting/query` sur une question inédite.
   * Vérifie l'exécution réussie, l'auto-promotion et la génération d'un `query_id="QC-AUTO-..."`.
3. **`test_post_reporting_query_with_filters`** :
   * Appel HTTP `POST /reporting/query` avec passage de filtres temporels et de structure.
4. **`test_post_reporting_query_clarification_response`** :
   * Question temporelle ambiguë $\rightarrow$ réponse 200 avec message clair de demande de précision.
5. **`test_post_reporting_query_security_unsupported`** :
   * Tentative de mutation SQL ou question hors périmètre $\rightarrow$ blocage propre avec message explicatif.
6. **`test_get_dashboard_non_regression`** :
   * Vérifie que l'endpoint `GET /reporting/dashboard` continue de fonctionner parfaitement.
7. **`test_answer_query_alias_backward_compatibility`** :
   * Vérifie que l'appel direct à `answer_query(db, question, filters)` fonctionne en déléguant au nouveau pipeline.

---

## 4. Critères d'Acceptation de l'Étape 10

* [x] `app/reporting/router.py` achemine `POST /reporting/query` directement vers `execute_text_to_sql_pipeline`.
* [x] `app/reporting/service.py` délégue `answer_query` au nouveau pipeline pour zéro rupture de code.
* [x] `GET /reporting/dashboard` est sanctuarisé et 100% fonctionnel.
* [x] Aucune régression sur les 126 tests unitaires existants.
* [x] La nouvelle suite `tests/test_step_10_final_integration.py` passe à 100% (8/8 tests).
* [x] Le document maître `PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md` est mis à jour pour déclarer les 10 étapes achevées et le système prêt pour la production.
