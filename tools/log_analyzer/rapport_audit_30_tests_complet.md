# 🏛️ Rapport d'Audit Exhaustif du Workflow Text-to-SQL Gouverné
**Fichier audité :** `04-finCWINDOWSsystem32cmd.exe - .venvScriptspython.exe  -m uvicorn mainapp --port 8005 --reload.txt`

## 1. Tableau de Bord Exécutif & Indicateurs de Risque
- **Nombre total de requêtes auditées :** 30
- **Hits Fast-Path (Catalogue Homologué) :** 4
- **Hits Candidate-Path (Requêtes en Attente) :** 14
- **Générations LLM Nemotron :** 12
- 🚨 **Replis silencieux (Failures Pydantic) :** 3 (Étape 1: 1, Étape 4: 2)
- 🚨 **Divergences SQL Brut LLM vs SQL Exécuté :** 2
- 🚨 **Incohérences sémantiques dans la synthèse :** 1
- ⚠️ **Désynchronisations temporelles (Candidate-Path) :** 4
- ⚠️ **Requêtes avec paramètres orphelins :** 9
- 🔒 **Fuites potentielles de données sensibles (PII) :** 0
- ❌ **Erreurs d'exécution base de données :** 0

## 2. Matrice Récapitulative des Requêtes

| # | Question | Circuit | Query ID | SQL Divergent ? | Repli Silencieux ? | Alerte Temporelle ? | Statut BDD |
|---|---|---|---|---|---|---|---|
| 01 | Combien de réclamations ? | `CANDIDATE_PATH_PENDING` | `QC-PEND-7F42ED05` | Non | Non | Non | SUCCESS |
| 02 | Combien de denonciation? | `CANDIDATE_PATH_PENDING` | `QC-PEND-9641EE89` | Non | Non | Non | SUCCESS |
| 03 | Combien de suggestion? | `GENERATIVE_LLM` | `QC-PEND-2FF7F0BB` | Non | Non | Non | SUCCESS |
| 04 | Quelles sont les dénonciations enregistrées ? | `CANDIDATE_PATH_PENDING` | `QC-PEND-9641EE89` | Non | Non | Non | SUCCESS |
| 05 | Quelles sont les sugestionenregistrées ? | `GENERATIVE_LLM` | `QC-PEND-2FF7F0BB` | Non | Non | Non | SUCCESS |
| 06 | Quelles sont les reclationenregistrées ? | `CANDIDATE_PATH_PENDING` | `QC-PEND-7F42ED05` | Non | Non | Non | SUCCESS |
| 07 | Nombre d'idées et suggestions d'amélioration | `GENERATIVE_LLM` | `QC-PEND-F641C06A` | Non | Non | Non | SUCCESS |
| 08 | Volume total de dossiers reçus par la banque | `FAST_PATH_HOMOLOGATED` | `QC-AUTO-572FF510` | Non | Non | Non | SUCCESS |
| 09 | Volume de dossiers reçus par la banque | `FAST_PATH_HOMOLOGATED` | `QC-AUTO-572FF510` | Non | Non | Non | SUCCESS |
| 10 | Combien de transferts de dossiers ont eu lieu ? | `CANDIDATE_PATH_PENDING` | `QC-PEND-97A0C00A` | Non | Non | Non | SUCCESS |
| 11 | Plaintes | `FAST_PATH_HOMOLOGATED` | `QC-AUTO-572FF510` | Non | Non | Non | SUCCESS |
| 12 | Réclamations moyennes | `GENERATIVE_LLM` | `QC-PEND-F11CD1EA` | Non | Non | Non | SUCCESS |
| 13 | Taux de respect des engagements SLA | `FAST_PATH_HOMOLOGATED` | `QC-AUTO-DCFB5C69` | Non | Non | Non | SUCCESS |
| 14 | Pourcentage d'usagers satisfaits | `GENERATIVE_LLM` | `QC-PEND-AF217D8A` | Non | Non | Non | SUCCESS |
| 15 | Score moyen de risque estimé | `GENERATIVE_LLM` | `QC-AUTO-572FF510` | 🚨 OUI | 🚨 OUI | Non | SUCCESS |
| 16 | Réclamations par agence | `CANDIDATE_PATH_PENDING` | `QC-PEND-CA4F2CB4` | Non | Non | Non | SUCCESS |
| 17 | Dossiers par canal de collecte | `GENERATIVE_LLM` | `QC-PEND-96F3D64F` | Non | Non | Non | SUCCESS |
| 18 | Suggestions selon le niveau d'impact | `CANDIDATE_PATH_PENDING` | `QC-PEND-6EBA969F` | Non | Non | Non | SUCCESS |
| 19 | Réclamations par agence et par canal | `CANDIDATE_PATH_PENDING` | `QC-PEND-F08016E5` | Non | Non | Non | SUCCESS |
| 20 | Total des réclamations | `CANDIDATE_PATH_PENDING` | `QC-PEND-7F42ED05` | Non | Non | Non | SUCCESS |
| 21 | Réclamations graves | `GENERATIVE_LLM` | `QC-PEND-226DBA67` | Non | Non | Non | SUCCESS |
| 22 | Plaintes critiques ou lourdes | `GENERATIVE_LLM` | `QC-AUTO-572FF510` | 🚨 OUI | 🚨 OUI | Non | SUCCESS |
| 23 | Dossiers insatisfaits | `GENERATIVE_LLM` | `QC-PEND-E3EDFC99` | Non | 🚨 OUI | Non | SUCCESS |
| 24 | Dossiers insatisfaits | `GENERATIVE_LLM` | `QC-PEND-A299EBC2` | Non | Non | Non | SUCCESS |
| 25 | Réclamations graves insatisfaites du canal Web | `GENERATIVE_LLM` | `QC-PEND-C3EECB8A` | Non | Non | Non | SUCCESS |
| 26 | Nombre de réclamations par agence | `CANDIDATE_PATH_PENDING` | `QC-PEND-CA4F2CB4` | Non | Non | Non | SUCCESS |
| 27 | Nombre de réclamations par agence en 2026 | `CANDIDATE_PATH_PENDING` | `QC-PEND-CA4F2CB4` | Non | Non | ⚠️ OUI | SUCCESS |
| 28 | Nombre de réclamations par agence en mars 2026 | `CANDIDATE_PATH_PENDING` | `QC-PEND-CA4F2CB4` | Non | Non | ⚠️ OUI | SUCCESS |
| 29 | Nombre de réclamations par agence en premier trimestre 2026 | `CANDIDATE_PATH_PENDING` | `QC-PEND-CA4F2CB4` | Non | Non | ⚠️ OUI | SUCCESS |
| 30 | Nombre de réclamations par agence ce mois ci | `CANDIDATE_PATH_PENDING` | `QC-PEND-CA4F2CB4` | Non | Non | ⚠️ OUI | SUCCESS |

================================================================================

## 3. Détail Exhaustif des 7 Contrats par Question

### [Requête N° 01] "Combien de réclamations ?"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-7F42ED05` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "time": null,
  "dimensions": [],
  "filters": [],
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-7F42ED05`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `17.06 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 43."
--------------------------------------------------------------------------------

### [Requête N° 02] "Combien de denonciation?"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-9641EE89` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['DENUNCIATION'])` | **Mesure :** `denonciation_count (libelle: "denonciation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "DENUNCIATION"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "denonciation_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-9641EE89`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `4.81 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour denonciation_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 03] "Combien de suggestion?"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-2FF7F0BB` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['SUGGESTION'])` | **Mesure :** `suggestion_count (libelle: "suggestion_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "SUGGESTION"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "suggestion_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-2FF7F0BB`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion ORDER BY suggestion_count DESC;",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": "intent.time.start_date"
    },
    "end_date": {
      "type": "datetime",
      "source": "intent.time.end_date"
    }
  },
  "used_schema": [
    "reporting_suggestion"
  ],
  "result_columns": [
    {
      "name": "suggestion_count",
      "concept_id": "suggestion_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "Aggregation is performed over the entire reporting_suggestion table without any temporal filters, as no date range was specified by the user."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion ORDER BY suggestion_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `3.07 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour suggestion_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 04] "Quelles sont les dénonciations enregistrées ?"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-9641EE89` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['DENUNCIATION'])` | **Mesure :** `denonciation_count (libelle: "denonciation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "DENUNCIATION"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "denonciation_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-9641EE89`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `2.46 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour denonciation_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 05] "Quelles sont les sugestionenregistrées ?"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-2FF7F0BB` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['SUGGESTION'])` | **Mesure :** `suggestion_count (libelle: "suggestion_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "SUGGESTION"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "suggestion_count"
  },
  "time": null,
  "filters": [],
  "dimensions": [],
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-2FF7F0BB`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion ORDER BY suggestion_count DESC;",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": "none"
    },
    "end_date": {
      "type": "datetime",
      "source": "none"
    }
  },
  "used_schema": [
    "reporting_suggestion"
  ],
  "result_columns": [
    {
      "name": "suggestion_count",
      "concept_id": "suggestion_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "Each row in reporting_suggestion corresponds to a single suggestion; we count all rows regardless of status, origin, or any other attribute to obtain the total suggestion count."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion ORDER BY suggestion_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `1.94 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour suggestion_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 06] "Quelles sont les reclationenregistrées ?"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-7F42ED05` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-7F42ED05`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `2.89 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 43."
--------------------------------------------------------------------------------

### [Requête N° 07] "Nombre d'idées et suggestions d'amélioration"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-F641C06A` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['SUGGESTION'])` | **Mesure :** `suggestion_count (libelle: "suggestion_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "SUGGESTION"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "suggestion_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-F641C06A`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion ORDER BY suggestion_count DESC",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": null
    },
    "end_date": {
      "type": "datetime",
      "source": null
    }
  },
  "used_schema": [
    "reporting_suggestion"
  ],
  "result_columns": [
    {
      "name": "suggestion_count",
      "concept_id": "suggestion_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": []
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion ORDER BY suggestion_count DESC
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `7.24 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour suggestion_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 08] "Volume total de dossiers reçus par la banque"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-AUTO-572FF510` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-AUTO-572FF510`
- **Libellé métier homologué :** "Le nombre de plainte en retard de traitement"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `8.66 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 09] "Volume de dossiers reçus par la banque"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-AUTO-572FF510` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-AUTO-572FF510`
- **Libellé métier homologué :** "Le nombre de plainte en retard de traitement"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `11.84 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 10] "Combien de transferts de dossiers ont eu lieu ?"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-97A0C00A` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `treatment (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `reaffectation_count (libelle: "reaffectation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "treatment",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "reaffectation_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-97A0C00A`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `5.89 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reaffectation_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 11] "Plaintes"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-AUTO-572FF510` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-AUTO-572FF510`
- **Libellé métier homologué :** "Le nombre de plainte en retard de traitement"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `7.60 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 12] "Réclamations moyennes"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-F11CD1EA` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['risk_level=MOYEN']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-F11CD1EA`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = :risk_level",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": null
    },
    "end_date": {
      "type": "datetime",
      "source": null
    },
    "risk_level": {
      "type": "string",
      "source": "intent.filters.risk_level"
    }
  },
  "used_schema": [
    "reporting_claim"
  ],
  "result_columns": [
    {
      "name": "reclamation_count",
      "concept_id": "reclamation_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": []
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'MOYEN'
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `5.84 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 17."
--------------------------------------------------------------------------------

### [Requête N° 13] "Taux de respect des engagements SLA"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-AUTO-DCFB5C69` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `sla_adherence_rate (libelle: "sla_adherence_rate")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "sla_adherence_rate"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-AUTO-DCFB5C69`
- **Libellé métier homologué :** "Taux de respect des délais de traitement"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT AVG(CASE WHEN c.resolved_at <= c.sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate FROM reporting_claim c  WHERE c.resolved_at IS NOT NULL
```
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `10.26 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour sla_adherence_rate est de None."
--------------------------------------------------------------------------------

### [Requête N° 14] "Pourcentage d'usagers satisfaits"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-AF217D8A` | **Statut Cycle de Vie :** `PENDING`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `satisfaction_rate (libelle: "satisfaction_rate")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['status=SATISFIED']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "satisfaction_rate"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-AF217D8A`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT AVG(CASE WHEN satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate FROM reporting_claim WHERE status = 'SATISFIED'",
  "parameters": {},
  "used_schema": [
    "reporting_claim"
  ],
  "result_columns": [
    {
      "name": "satisfaction_rate",
      "concept_id": "satisfaction_rate",
      "role": "measure",
      "data_type": "decimal"
    }
  ],
  "assumptions": [
    "Only the reporting_claim table contains the satisfaction_status column; reporting_suggestion lacks satisfaction feedback and is therefore excluded from the calculation."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT AVG(CASE WHEN satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate FROM reporting_claim WHERE status = 'SATISFIED'
```
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `5.55 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour satisfaction_rate est de 0.00000."
--------------------------------------------------------------------------------

### [Requête N° 15] "Score moyen de risque estimé"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-AUTO-572FF510` | **Statut Cycle de Vie :** `APPROVED`

#### 🚨 Alertes & Anomalies Détectées :
- 🚨 **[Étape 4 (Générateur SQL)] SILENT_FALLBACK_CANDIDATE** : Échec de validation Pydantic TextToSQLCandidate (1 validation error for TextToSQLCandidate
result_columns.0.data_type
  Input should be 'string', 'integer', 'decimal', 'boolean', 'date' or 'datetime' [type=literal_error, input_value='double', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error). Repli silencieux vers le générateur déterministe.
- 🚨 **[Étape 4 (Générateur SQL)] RAW_VS_CANDIDATE_SQL_DIVERGENCE** : Le LLM a proposé une requête spécifique mais le système a exécuté le fallback global 'plainte_count' ! (Proposé: SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM repo... | Exécuté: SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...)
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']
- 🚨 **[Étape 7 (Restitution)] SEMANTIC_SYNTHESIS_CORRUPTED** : Incohérence sémantique majeure : La synthèse formule 'Pour la période demandée, le résultat pour custom_avg_risk_score est de 52.' sur la base d'un comptage brut (52) issu du fallback déterministe.

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `custom_avg_risk_score (libelle: "custom_avg_risk_score")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['risk_level=MOYEN']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "custom_avg_risk_score"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-AUTO-572FF510`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM reporting_claim WHERE risk_level = :risk_level AND claim_type IN ('CLAIM', 'DENUNCIATION') ORDER BY custom_avg_risk_score DESC;",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": "intent.time.start_date"
    },
    "end_date": {
      "type": "datetime",
      "source": "intent.time.end_date"
    }
  },
  "result_columns": [
    {
      "name": "custom_avg_risk_score",
      "concept_id": "custom_avg_risk_score",
      "role": "measure",
      "data_type": "double"
    }
  ],
  "used_schema": [
    "reporting_claim"
  ],
  "assumptions": [
    "The reporting_suggestion table does not contain an ai_risk_score column, therefore suggestions areexcluded from the custom average risk score calculation; only CLAIM and DENUNCIATION rows from reporting_claim are considered."
  ]
}
```
> ❌ **Erreur Pydantic Candidate** : `1 validation error for TextToSQLCandidate
result_columns.0.data_type
  Input should be 'string', 'integer', 'decimal', 'boolean', 'date' or 'datetime' [type=literal_error, input_value='double', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error`
> ⚠️ **Action Système** : Repli silencieux immédiat vers le générateur déterministe (`generate_candidate_fallback`) !
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `8.54 ms`
- **Cycle de vie :** `APPROVED`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour custom_avg_risk_score est de 52."
> 🚨 **INCOHÉRENCE SÉMANTIQUE DÉTECTÉE** : Un comptage brut de dossiers a été présenté sous l'intitulé d'une métrique différente !

--------------------------------------------------------------------------------

### [Requête N° 16] "Réclamations par agence"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-CA4F2CB4` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    }
  ],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-CA4F2CB4`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `16.06 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 17] "Dossiers par canal de collecte"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-96F3D64F` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['channel']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "dimensions": [
    {
      "concept_id": "channel"
    }
  ],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-96F3D64F`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion', 'reporting_collection_channel']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT cc.libelle AS channel, COUNT(*) AS plainte_count FROM (SELECT collection_channel_id FROM reporting_claim UNION ALL SELECT collection_channel_id FROM reporting_suggestion) u LEFT JOIN reporting_collection_channel cc ON u.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY plainte_count DESC;",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": null
    },
    "end_date": {
      "type": "datetime",
      "source": null
    }
  },
  "used_schema": [
    "reporting_claim",
    "reporting_suggestion",
    "reporting_collection_channel"
  ],
  "result_columns": [
    {
      "name": "channel",
      "concept_id": "channel",
      "role": "dimension",
      "data_type": "string"
    },
    {
      "name": "plainte_count",
      "concept_id": "plainte_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "Les dossiers sans canal de collecte (collection_channel_id NULL) sont regroupés sous une valeur NULL de la colonne channel."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT cc.libelle AS channel, COUNT(*) AS plainte_count FROM (SELECT collection_channel_id FROM reporting_claim UNION ALL SELECT collection_channel_id FROM reporting_suggestion) u LEFT JOIN reporting_collection_channel cc ON u.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY plainte_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `14.35 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `pie`
- **Synthèse formulée :** "Pour la période demandée, un total de 52 plainte_count a été enregistré, avec la répartition suivante par channel : AGEN..."
--------------------------------------------------------------------------------

### [Requête N° 18] "Suggestions selon le niveau d'impact"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-6EBA969F` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['SUGGESTION'])` | **Mesure :** `suggestion_count (libelle: "suggestion_count")`
- **Dimensions :** `['impact_level']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "SUGGESTION"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "suggestion_count"
  },
  "dimensions": [
    {
      "concept_id": "impact_level"
    }
  ],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-6EBA969F`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `0` | **Durée :** `7.92 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Aucun enregistrement ne correspond aux critères demandés pour cette période."
--------------------------------------------------------------------------------

### [Requête N° 19] "Réclamations par agence et par canal"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-F08016E5` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency', 'channel']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    },
    {
      "concept_id": "channel"
    }
  ],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-F08016E5`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `19.41 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 20] "Total des réclamations"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-7F42ED05` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-7F42ED05`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `7.01 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 43."
--------------------------------------------------------------------------------

### [Requête N° 21] "Réclamations graves"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-226DBA67` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['risk_level=GRAVE']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [],
  "filters": [
    {
      "concept_id": "risk_level",
      "operator": "equals",
      "value": "GRAVE"
    }
  ],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-226DBA67`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE claim_type = 'CLAIM' AND risk_level = 'GRAVE' ORDER BY reclamation_count DESC",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": ""
    },
    "end_date": {
      "type": "datetime",
      "source": ""
    }
  },
  "used_schema": [
    "reporting_claim"
  ],
  "result_columns": [
    {
      "name": "reclamation_count",
      "concept_id": "reclamation_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "Le comptage considère uniquement les enregistrements de type 'CLAIM' avec un risque réglementaire 'GRAVE'. Aucune contrainte temporelle n'est appliquée, donc l'ensemble de l'historique est inclus."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE claim_type = 'CLAIM' AND risk_level = 'GRAVE' ORDERBY reclamation_count DESC
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `9.76 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 19."
--------------------------------------------------------------------------------

### [Requête N° 22] "Plaintes critiques ou lourdes"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-AUTO-572FF510` | **Statut Cycle de Vie :** `APPROVED`

#### 🚨 Alertes & Anomalies Détectées :
- 🚨 **[Étape 4 (Générateur SQL)] SILENT_FALLBACK_CANDIDATE** : Échec de validation Pydantic TextToSQLCandidate (1 validation error for TextToSQLCandidate
parameters.risk_level.type
  Input should be 'date', 'datetime', 'string', 'integer', 'decimal' or 'boolean' [type=literal_error, input_value='varchar', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error). Repli silencieux vers le générateur déterministe.
- ⚠️ **[Étape 4 (Générateur SQL)] SQL_STRUCTURAL_DIFF** : Différence structurelle entre le SQL brut du LLM et le SQL candidat exécuté. (Proposé: SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE risk_lev... | Exécuté: SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...)

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['risk_level=GRAVE']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "dimensions": [],
  "filters": [
    {
      "concept_id": "risk_level",
      "operator": "equals",
      "value": "GRAVE"
    }
  ],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-AUTO-572FF510`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE risk_level = :risk_level) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;",
  "parameters": {
    "risk_level": {
      "type": "varchar",
      "source": "intent.filters.risk_level"
    }
  },
  "used_schema": [
    "reporting_claim",
    "reporting_suggestion"
  ],
  "result_columns": [
    {
      "name": "plainte_count",
      "concept_id": "plainte_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "The risk_level filter is applied only to reporting_claim because reporting_suggestion does not have a risk_level column; all suggestions are counted regardless of risk."
  ]
}
```
> ❌ **Erreur Pydantic Candidate** : `1 validation error for TextToSQLCandidate
parameters.risk_level.type
  Input should be 'date', 'datetime', 'string', 'integer', 'decimal' or 'boolean' [type=literal_error, input_value='varchar', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error`
> ⚠️ **Action Système** : Repli silencieux immédiat vers le générateur déterministe (`generate_candidate_fallback`) !
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `17.25 ms`
- **Cycle de vie :** `APPROVED`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 23] "Dossiers insatisfaits"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-E3EDFC99` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- 🚨 **[Étape 1 (Intention)] SILENT_FALLBACK_INTENT** : Échec de validation Pydantic de l'intention LLM (1 validation error for TextToSQLIntent
entity
  Value error, types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true [type=value_error, input_value={'concept_id': 'plainte',...rue, 'types': ['CLAIM']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/value_error). Repli silencieux vers le résolveur déterministe.
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `FALLBACK_DETERMINISTE_MOTS_CLES`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "Total unifié des plaintes")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['status=UNSATISFIED']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "filters": [
    {
      "concept_id": "status",
      "operator": "equals",
      "value": "UNSATISFIED"
    }
  ],
  "time": null,
  "status": "ready"
}
```
> ❌ **Échec Pydantic Étape 1** : `1 validation error for TextToSQLIntent
entity
  Value error, types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true [type=value_error, input_value={'concept_id': 'plainte',...rue, 'types': ['CLAIM']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/value_error`

#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-E3EDFC99`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED') + (SELECT COUNT(*)FROM reporting_suggestion)) AS plainte_count",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": "intent.time.start_date"
    },
    "end_date": {
      "type": "datetime",
      "source": "intent.time.end_date"
    }
  },
  "used_schema": [
    "reporting_claim",
    "reporting_suggestion"
  ],
  "result_columns": [
    {
      "name": "plainte_count",
      "concept_id": "plainte_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "The filter status = 'UNSATISFIED' is applied to the satisfaction_status column in reporting_claim; reporting_suggestion does not have a satisfaction status field, so all suggestions are counted."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED') + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `7.48 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour total unifié des plaintes est de 0."
--------------------------------------------------------------------------------

### [Requête N° 24] "Dossiers insatisfaits"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-A299EBC2` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['status=UNSATISFIED']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ],
    "include_all_types": true
  },
  "measure": {
    "concept_id": "plainte_count"
  },
  "filters": [
    {
      "concept_id": "status",
      "operator": "equals",
      "value": "UNSATISFIED"
    }
  ],
  "dimensions": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-A299EBC2`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "WITH unioned AS (SELECT 1 FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED' UNION ALL SELECT 1FROM reporting_suggestion) SELECT COUNT(*) AS plainte_count FROM unioned;",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": "intent.time.start_date"
    },
    "end_date": {
      "type": "datetime",
      "source": "intent.time.end_date"
    }
  },
  "used_schema": [
    "reporting_claim",
    "reporting_suggestion"
  ],
  "result_columns": [
    {
      "name": "plainte_count",
      "concept_id": "plainte_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "The satisfaction_status filter applies only to reporting_claim; reporting_suggestion rows are counted regardless of their status as they represent complaints/suggestions."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
WITH unioned AS (SELECT 1 FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED' UNION ALL SELECT 1 FROM reporting_suggestion) SELECT COUNT(*) AS plainte_count FROM unioned;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `7.45 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 25] "Réclamations graves insatisfaites du canal Web"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-C3EECB8A` | **Statut Cycle de Vie :** `PENDING`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['channel']` | **Filtres :** `['risk_level=GRAVE', 'status=UNSATISFIED', 'channel=Web']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "channel"
    }
  ],
  "filters": [
    {
      "concept_id": "risk_level",
      "operator": "equals",
      "value": "GRAVE"
    },
    {
      "concept_id": "status",
      "operator": "equals",
      "value": "UNSATISFIED"
    },
    {
      "concept_id": "channel",
      "operator": "equals",
      "value": "Web"
    }
  ],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-C3EECB8A`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_collection_channel']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT rcc.libelle AS channel, COUNT(CASE WHEN rc.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim rc LEFT JOIN reporting_collection_channel rcc ON rc.collection_channel_id = rcc.id WHERE rc.risk_level= 'GRAVE' AND rc.status = 'UNSATISFIED' AND rc.claim_type = 'CLAIM' AND rcc.libelle = 'Web' GROUP BY rcc.libelle ORDER BY reclamation_count DESC;",
  "parameters": {},
  "used_schema": [
    "reporting_claim",
    "reporting_collection_channel"
  ],
  "result_columns": [
    {
      "name": "channel",
      "concept_id": "channel",
      "role": "dimension",
      "data_type": "string"
    },
    {
      "name": "reclamation_count",
      "concept_id": "reclamation_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "Filter on claim_type='CLAIM' applied for performance; the measure definition already restricts to CLAIM via CASEWHEN."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT rcc.libelle AS channel, COUNT(CASE WHEN rc.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim rc LEFT JOIN reporting_collection_channel rcc ON rc.collection_channel_id = rcc.id WHERE rc.risk_level = 'GRAVE' AND rc.status = 'UNSATISFIED' AND rc.claim_type = 'CLAIM' AND rcc.libelle = 'Web' GROUP BY rcc.libelle ORDER BY reclamation_count DESC;
```
- **Anti-patterns injectés dans le prompt (3) :**
  * 1. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
  * 2. REQUÊTE REJETÉE : `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `0` | **Durée :** `21.61 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `bar`
- **Synthèse formulée :** "Aucun enregistrement ne correspond aux critères demandés pour cette période."
--------------------------------------------------------------------------------

### [Requête N° 26] "Nombre de réclamations par agence"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-CA4F2CB4` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    }
  ],
  "filters": [],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-CA4F2CB4`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `13.44 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 27] "Nombre de réclamations par agence en 2026"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-CA4F2CB4` | **Statut Cycle de Vie :** `N/A`

#### 🚨 Alertes & Anomalies Détectées :
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-01-01 -> 2027-01-01 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency']` | **Filtres :** `aucun` | **Période :** `2026-01-01 -> 2027-01-01 (champ=receipt_date)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    }
  ],
  "time": {
    "field_concept": "receipt_date",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "timezone": "Africa/Porto-Novo"
  },
  "filters": [],
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-CA4F2CB4`
> ⚠️ **Désynchronisation Temporelle** : Requête réutilisée sans filtre temporel alors que la question précisait une date !

#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `12.45 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 28] "Nombre de réclamations par agence en mars 2026"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-CA4F2CB4` | **Statut Cycle de Vie :** `N/A`

#### 🚨 Alertes & Anomalies Détectées :
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-03-01 -> 2026-03-31 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency']` | **Filtres :** `aucun` | **Période :** `2026-03-01 -> 2026-03-31 (champ=receipt_date)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    }
  ],
  "time": {
    "field_concept": "receipt_date",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31",
    "timezone": "Africa/Porto-Novo"
  },
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-CA4F2CB4`
> ⚠️ **Désynchronisation Temporelle** : Requête réutilisée sans filtre temporel alors que la question précisait une date !

#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `12.16 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 29] "Nombre de réclamations par agence en premier trimestre 2026"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-CA4F2CB4` | **Statut Cycle de Vie :** `N/A`

#### 🚨 Alertes & Anomalies Détectées :
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-01-01 -> 2026-03-31 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency']` | **Filtres :** `aucun` | **Période :** `2026-01-01 -> 2026-03-31 (champ=receipt_date)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    }
  ],
  "filters": [],
  "time": {
    "field_concept": "receipt_date",
    "start_date": "2026-01-01",
    "end_date": "2026-03-31",
    "timezone": "Africa/Porto-Novo"
  },
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-CA4F2CB4`
> ⚠️ **Désynchronisation Temporelle** : Requête réutilisée sans filtre temporel alors que la question précisait une date !

#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `8.85 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 30] "Nombre de réclamations par agence ce mois ci"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-CA4F2CB4` | **Statut Cycle de Vie :** `N/A`

#### 🚨 Alertes & Anomalies Détectées :
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-10-01 -> 2026-10-31 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['agency']` | **Filtres :** `aucun` | **Période :** `2026-10-01 -> 2026-10-31 (champ=receipt_date)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [
      "CLAIM"
    ],
    "include_all_types": false
  },
  "measure": {
    "concept_id": "reclamation_count"
  },
  "dimensions": [
    {
      "concept_id": "agency"
    }
  ],
  "filters": [],
  "time": {
    "field_concept": "receipt_date",
    "start_date": "2026-10-01",
    "end_date": "2026-10-31",
    "timezone": "Africa/Porto-Novo"
  },
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-CA4F2CB4`
> ⚠️ **Désynchronisation Temporelle** : Requête réutilisée sans filtre temporel alors que la question précisait une date !

#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `16.75 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------
