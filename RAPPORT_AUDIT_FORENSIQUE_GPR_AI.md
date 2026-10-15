# 🏛️ Rapport d'Audit Exhaustif du Workflow Text-to-SQL Gouverné
**Fichier audité :** `workflow_execution.log`

## 1. Tableau de Bord Exécutif & Indicateurs de Risque
- **Nombre total de requêtes auditées :** 24
- **Hits Fast-Path (Catalogue Homologué) :** 4
- **Hits Candidate-Path (Requêtes en Attente) :** 3
- **Générations LLM Nemotron :** 17
- 🚨 **Replis silencieux (Failures Pydantic) :** 1 (Étape 1: 1, Étape 4: 0)
- 🚨 **Divergences SQL Brut LLM vs SQL Exécuté :** 0
- 🚨 **Incohérences sémantiques dans la synthèse :** 0
- ⚠️ **Désynchronisations temporelles (Candidate-Path) :** 0
- ⚠️ **Requêtes avec paramètres orphelins :** 14
- 🔒 **Fuites potentielles de données sensibles (PII) :** 0
- ❌ **Erreurs d'exécution base de données :** 0

## 2. Matrice Récapitulative des Requêtes

| # | Question | Circuit | Query ID | SQL Divergent ? | Repli Silencieux ? | Alerte Temporelle ? | Statut BDD |
|---|---|---|---|---|---|---|---|
| 01 | Combien de réclamations ? | `GENERATIVE_LLM` | `QC-PEND-8C936F86` | Non | Non | Non | SUCCESS |
| 02 | Quelles sont les dénonciations enregistrées ? | `GENERATIVE_LLM` | `QC-PEND-1E32053F` | Non | Non | Non | SUCCESS |
| 03 | Nombre d'idées et suggestions d'amélioration | `GENERATIVE_LLM` | `QC-PEND-6AF83385` | Non | Non | Non | SUCCESS |
| 04 | Volume total de dossiers reçus par la banque | `GENERATIVE_LLM` | `QC-PEND-437500D2` | Non | Non | Non | SUCCESS |
| 05 | Combien de transferts de dossiers ont eu lieu ? | `GENERATIVE_LLM` | `QC-PEND-A1CE3781` | Non | Non | Non | SUCCESS |
| 06 | Plaintes | `CANDIDATE_PATH_PENDING` | `QC-PEND-437500D2` | Non | Non | Non | SUCCESS |
| 07 | Réclamations moyennes | `GENERATIVE_LLM` | `QC-PEND-142E5CFC` | Non | Non | Non | SUCCESS |
| 08 | Taux de respect des engagements SLA | `GENERATIVE_LLM` | `QC-PEND-27A64E58` | Non | Non | Non | SUCCESS |
| 09 | Pourcentage d'usagers satisfaits | `GENERATIVE_LLM` | `QC-PEND-BD16F96B` | Non | 🚨 OUI | Non | SUCCESS |
| 10 | Score moyen de risque estimé | `GENERATIVE_LLM` | `QC-PEND-8DDF3F5A` | Non | Non | Non | SUCCESS |
| 11 | Réclamations par agence | `GENERATIVE_LLM` | `QC-PEND-FC1867EB` | Non | Non | Non | SUCCESS |
| 12 | Dossiers par canal de collecte | `GENERATIVE_LLM` | `QC-PEND-83290F94` | Non | Non | Non | SUCCESS |
| 13 | Suggestions selon le niveau d'impact | `GENERATIVE_LLM` | `QC-PEND-232E1218` | Non | Non | Non | SUCCESS |
| 14 | Réclamations par agence et par canal | `GENERATIVE_LLM` | `QC-PEND-283479FE` | Non | Non | Non | SUCCESS |
| 15 | Total des réclamations | `CANDIDATE_PATH_PENDING` | `QC-PEND-8C936F86` | Non | Non | Non | SUCCESS |
| 16 | Réclamations graves | `GENERATIVE_LLM` | `QC-PEND-ACD52C4E` | Non | Non | Non | SUCCESS |
| 17 | Plaintes critiques ou lourdes | `GENERATIVE_LLM` | `QC-PEND-A7083450` | Non | Non | Non | SUCCESS |
| 18 | Dossiers insatisfaits | `GENERATIVE_LLM` | `QC-PEND-4FB7184D` | Non | Non | Non | SUCCESS |
| 19 | Réclamations graves insatisfaites du canal Web | `GENERATIVE_LLM` | `QC-PEND-17E0DEFC` | Non | Non | Non | SUCCESS |
| 20 | Nombre de réclamations par agence | `CANDIDATE_PATH_PENDING` | `QC-PEND-FC1867EB` | Non | Non | Non | SUCCESS |
| 21 | En 2026 | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | Non | Non | Non | SUCCESS |
| 22 | En mars 2026 | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | Non | Non | Non | SUCCESS |
| 23 | Premier trimestre 2026 | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | Non | Non | Non | SUCCESS |
| 24 | Ce mois-ci | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | Non | Non | Non | SUCCESS |

================================================================================

## 3. Détail Exhaustif des 7 Contrats par Question

### [Requête N° 01] "Combien de réclamations ?"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-8C936F86` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-8C936F86`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim;",
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
    "Tous les enregistrements de la table reporting_claim sont pris en compte, aucun filtre de statut ou de date n'est appliqué."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `4.46 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 43."
--------------------------------------------------------------------------------

### [Requête N° 02] "Quelles sont les dénonciations enregistrées ?"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-1E32053F` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-1E32053F`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN claim_type = 'DENUNCIATION' THEN 1 END) AS denonciation_count FROM reporting_claim;",
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
    "reporting_claim"
  ],
  "result_columns": [
    {
      "name": "denonciation_count",
      "concept_id": "denonciation_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "No temporal filter specified; the query counts all denunciations across the entire reporting_claim table."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(CASE WHEN claim_type = 'DENUNCIATION' THEN 1 END) AS denonciation_count FROM reporting_claim;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `13.49 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour denonciation_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 03] "Nombre d'idées et suggestions d'amélioration"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-6AF83385` | **Statut Cycle de Vie :** `PENDING`

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
- **Query ID associé :** `QC-PEND-6AF83385`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion;",
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
    "Aggregates all suggestions across the entire history as no temporal filter was specified."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `11.82 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour suggestion_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 04] "Volume total de dossiers reçus par la banque"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-437500D2` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-437500D2`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;",
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
    "No temporal filter applied; the query counts all historical records across both reclamations/dénonciations and suggestions."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `5.80 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 05] "Combien de transferts de dossiers ont eu lieu ?"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-A1CE3781` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `treatment (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `reaffectation_count (libelle: "reaffectation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "treatment",
    "include_all_types": true,
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ]
  },
  "measure": {
    "concept_id": "reaffectation_count"
  },
  "time": null,
  "filters": [],
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-A1CE3781`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_historique_affectations']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN affectation_precedente_id IS NOT NULL THEN 1 END) AS reaffectation_count FROM reporting_historique_affectations;",
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
    "reporting_historique_affectations"
  ],
  "result_columns": [
    {
      "name": "reaffectation_count",
      "concept_id": "reaffectation_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "The query aggregates over the entire history of the table, applying no temporal filter. It counts each row where an affectation_precedente_id exists, indicating a reassignment or transfer."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(CASE WHEN affectation_precedente_id IS NOT NULL THEN 1 END) AS reaffectation_count FROM reporting_historique_affectations;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `10.12 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reaffectation_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 06] "Plaintes"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-437500D2` | **Statut Cycle de Vie :** `N/A`

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
- **Circuit retenu :** `CANDIDATE_PATH_PENDING`
- **Query ID associé :** `QC-PEND-437500D2`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `21.09 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 07] "Réclamations moyennes"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-142E5CFC` | **Statut Cycle de Vie :** `PENDING`

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
- **Query ID associé :** `QC-PEND-142E5CFC`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = :risk_level;",
  "parameters": {
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
  "assumptions": [
    "The risk_level filter ('MOYEN') is supplied via the :risk_level parameter.",
    "Only rows with claim_type = 'CLAIM' are counted, as this corresponds to a réclamation per the business definition."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'MOYEN';
```
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `14.42 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 17."
--------------------------------------------------------------------------------

### [Requête N° 08] "Taux de respect des engagements SLA"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-27A64E58` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-27A64E58`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT AVG(CASE WHEN resolved_at <= sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate FROM reporting_claim WHERE claim_type = 'CLAIM';",
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
    "reporting_claim"
  ],
  "result_columns": [
    {
      "name": "sla_adherence_rate",
      "concept_id": "sla_adherence_rate",
      "role": "measure",
      "data_type": "double"
    }
  ],
  "assumptions": [
    "NULL values in resolved_at or sla_due_at are treated as non‑adherent (contribute 0 to the average). No temporal filter is applied; the query considers the entire history of claims."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT AVG(CASE WHEN resolved_at <= sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate FROM reporting_claim WHERE claim_type = 'CLAIM';
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `5.14 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour sla_adherence_rate est de 0.00000."
--------------------------------------------------------------------------------

### [Requête N° 09] "Pourcentage d'usagers satisfaits"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-BD16F96B` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- 🚨 **[Étape 1 (Intention)] SILENT_FALLBACK_INTENT** : Échec de validation Pydantic de l'intention LLM (1 validation error for TextToSQLIntent
entity
  Value error, types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true [type=value_error, input_value={'concept_id': 'plainte',...nclude_all_types': True}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/value_error). Repli silencieux vers le résolveur déterministe.
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `FALLBACK_DETERMINISTE_MOTS_CLES`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `satisfaction_rate (libelle: "Taux de satisfaction")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "types": [],
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
> ❌ **Échec Pydantic Étape 1** : `1 validation error for TextToSQLIntent
entity
  Value error, types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true [type=value_error, input_value={'concept_id': 'plainte',...nclude_all_types': True}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/value_error`

#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-BD16F96B`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' ORDER BY satisfaction_rate DESC;",
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
    "Le taux de satisfaction est calculé sur l'ensemble des réclamations (claim_type = 'CLAIM') indépendamment de leur statut opérationnel ou de toute période temporelle.",
    "Les valeurs possibles de satisfaction_status sont 'SATISFIED', 'UNSATISFIED' et 'PARTIAL_SATISFIED'; seules 'SATISFIED' contribuent à 100 dans la moyenne."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' ORDER BY satisfaction_rate DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `13.02 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour taux de satisfaction est de 0.00000."
--------------------------------------------------------------------------------

### [Requête N° 10] "Score moyen de risque estimé"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-8DDF3F5A` | **Statut Cycle de Vie :** `PENDING`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `custom_avg_risk_score (libelle: "custom_avg_risk_score")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['risk_level=MOYEN']` | **Période :** `aucune (global sur toute la base)`
```json
{
  "entity": {
    "concept_id": "plainte",
    "include_all_types": true,
    "types": [
      "CLAIM",
      "DENUNCIATION",
      "SUGGESTION"
    ]
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
- **Query ID associé :** `QC-PEND-8DDF3F5A`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM reporting_claim WHERE risk_level = :risk_level ORDER BY custom_avg_risk_score DESC;",
  "parameters": {},
  "used_schema": [
    "reporting_claim"
  ],
  "result_columns": [
    {
      "name": "custom_avg_risk_score",
      "concept_id": "custom_avg_risk_score",
      "role": "measure",
      "data_type": "double"
    }
  ],
  "assumptions": [
    "Only the reporting_claim table contains the risk_level column; reporting_suggestion does not have this field, so suggestions are excluded from the calculation."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM reporting_claim WHERE risk_level = 'MOYEN' ORDER BY custom_avg_risk_score DESC;
```
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `5.74 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Aucune donnée disponible pour les critères et la période demandés."
--------------------------------------------------------------------------------

### [Requête N° 11] "Réclamations par agence"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-FC1867EB` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-FC1867EB`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_service_point']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT sp.libelle AS agency,\n       COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count\nFROM reporting_service_point sp\nLEFT JOIN reporting_claim c ON c.service_point_id = sp.id\nGROUP BY sp.libelle\nORDER BY reclamation_count DESC;",
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
    "reporting_service_point"
  ],
  "result_columns": [
    {
      "name": "agency",
      "concept_id": "agency",
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
    "Counts all rows where claim_type = 'CLAIM' regardless of status or other attributes.",
    "Uses a LEFT JOIN from agency to claim to preserve agencies with zero reclamations."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT sp.libelle AS agency,
           COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
    FROM reporting_service_point sp
    LEFT JOIN reporting_claim c ON c.service_point_id = sp.id
    GROUP BY sp.libelle
    ORDER BY reclamation_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `98.46 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 12] "Dossiers par canal de collecte"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-83290F94` | **Statut Cycle de Vie :** `PENDING`

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
- **Query ID associé :** `QC-PEND-83290F94`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion', 'reporting_collection_channel']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT cc.libelle AS channel, COUNT(*) AS plainte_count FROM (SELECT collection_channel_id FROM reporting_claim UNION ALL SELECT collection_channel_id FROM reporting_suggestion) u JOIN reporting_collection_channel cc ON u.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY plainte_count DESC;",
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
    "We count all rows in reporting_claim and reporting_suggestion irrespective of status, as per the unified plainte_count definition."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT cc.libelle AS channel, COUNT(*) AS plainte_count FROM (SELECT collection_channel_id FROM reporting_claim UNION ALL SELECT collection_channel_id FROM reporting_suggestion) u JOIN reporting_collection_channel cc ON u.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY plainte_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `24.46 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `pie`
- **Synthèse formulée :** "Pour la période demandée, un total de 52 plainte_count a été enregistré, avec la répartition suivante par channel : AGEN..."
--------------------------------------------------------------------------------

### [Requête N° 13] "Suggestions selon le niveau d'impact"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-232E1218` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-232E1218`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT impact_level AS impact_level, COUNT(id) AS suggestion_count FROM reporting_suggestion GROUP BY impact_level ORDER BY suggestion_count DESC;",
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
      "name": "impact_level",
      "concept_id": "impact_level",
      "role": "dimension",
      "data_type": "string"
    },
    {
      "name": "suggestion_count",
      "concept_id": "suggestion_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "Aucun filtre temporel appliqué ; l'agrégation porte sur l'ensemble de l'historique des suggestions."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT impact_level AS impact_level, COUNT(id) AS suggestion_count FROM reporting_suggestion GROUP BY impact_level ORDER BY suggestion_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `0` | **Durée :** `15.17 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `bar`
- **Synthèse formulée :** "Aucun enregistrement ne correspond aux critères demandés pour cette période."
--------------------------------------------------------------------------------

### [Requête N° 14] "Réclamations par agence et par canal"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-283479FE` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

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
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-283479FE`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_collection_channel', 'reporting_service_point']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id GROUP BY agency, channel ORDER BY reclamation_count DESC;",
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
    "reporting_service_point",
    "reporting_collection_channel"
  ],
  "result_columns": [
    {
      "name": "agency",
      "concept_id": "agency",
      "role": "dimension",
      "data_type": "string"
    },
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
    "No temporal filter applied; query includes entire history of claims.",
    "LEFT JOIN ensures agencies and channels are included even if no claims exist (count will be zero)."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id GROUP BY agency, channel ORDER BY reclamation_count DESC;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `11.43 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 15] "Total des réclamations"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-8C936F86` | **Statut Cycle de Vie :** `N/A`

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
- **Query ID associé :** `QC-PEND-8C936F86`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `16.76 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 43."
--------------------------------------------------------------------------------

### [Requête N° 16] "Réclamations graves"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-ACD52C4E` | **Statut Cycle de Vie :** `PENDING`

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
- **Query ID associé :** `QC-PEND-ACD52C4E`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'GRAVE' ORDER BY reclamation_count DESC",
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
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'GRAVE' ORDER BY reclamation_count DESC
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `4.21 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 19."
--------------------------------------------------------------------------------

### [Requête N° 17] "Plaintes critiques ou lourdes"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-A7083450` | **Statut Cycle de Vie :** `PENDING`

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
- **Query ID associé :** `QC-PEND-A7083450`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT (SELECT COUNT(*) FROM reporting_claim WHERE risk_level = :risk_level) AS plainte_count",
  "parameters": {
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
      "name": "plainte_count",
      "concept_id": "plainte_count",
      "role": "measure",
      "data_type": "integer"
    }
  ],
  "assumptions": [
    "The risk_level attribute exists only in the reporting_claim table; reporting_suggestion does not have a risk_level column, therefore suggestions cannot satisfy the risk_level = 'GRAVE' filter and are excluded from this metric."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT (SELECT COUNT(*) FROM reporting_claim WHERE risk_level = 'GRAVE') AS plainte_count
```
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `2.74 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 24."
--------------------------------------------------------------------------------

### [Requête N° 18] "Dossiers insatisfaits"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-4FB7184D` | **Statut Cycle de Vie :** `PENDING`

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
  "dimensions": [],
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
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-4FB7184D`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_suggestion']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED') + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;",
  "parameters": {
    "start_date": {
      "type": "datetime",
      "source": "null"
    },
    "end_date": {
      "type": "datetime",
      "source": "null"
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
    "The filter status='UNSATISFIED' is interpreted as filtering on the satisfaction_status column in reporting_claim (values: SATISFIED, UNSATISFIED, PARTIAL_SATISFIED). The reporting_suggestion table does not have a satisfaction_status column, so all suggestions are counted regardless of status."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED') + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `11.53 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 19] "Réclamations graves insatisfaites du canal Web"
**Aiguillage Global :** `GENERATIVE_LLM` | **Query ID Final :** `QC-PEND-17E0DEFC` | **Statut Cycle de Vie :** `PENDING`

#### 🚨 Alertes & Anomalies Détectées :
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM'])` | **Mesure :** `reclamation_count (libelle: "reclamation_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `['risk_level=GRAVE', 'status=UNSATISFIED', 'channel=WEB']` | **Période :** `aucune (global sur toute la base)`
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
    },
    {
      "concept_id": "status",
      "operator": "equals",
      "value": "UNSATISFIED"
    },
    {
      "concept_id": "channel",
      "operator": "equals",
      "value": "WEB"
    }
  ],
  "time": null,
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `GENERATIVE_LLM`
- **Query ID associé :** `QC-PEND-17E0DEFC`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** `['reporting_claim', 'reporting_collection_channel']`
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
**Contrat JSON Brut émis par le LLM (Nemotron) :**
```json
{
  "contract_version": "1.0",
  "sql": "SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.risk_level = 'GRAVE' AND c.satisfaction_status = 'UNSATISFIED' AND cc.libelle = 'WEB' ORDER BY reclamation_count DESC",
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
    "reporting_collection_channel"
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
    "Le filtre sur le statut 'UNSATISFIED' a été appliqué sur la colonne satisfaction_status conformément à la règle de distinction des statuts."
  ]
}
```
```sql
-- REQUÊTE SQL CANDIDATE RETENUE :
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.risk_level = 'GRAVE' AND c.satisfaction_status = 'UNSATISFIED' AND cc.libelle = 'WEB' ORDER BY reclamation_count DESC
```
- ⚠️ **Paramètres orphelins déclarés :** `['start_date', 'end_date']`
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[VALIDE]`
- **Contrôles validés :** SELECT pur, aucune ecriture, aucune fuite sensible, projection stricte

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `1` | **Durée :** `11.10 ms`
- **Cycle de vie :** `PENDING`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `GENERATIVE_LLM` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour reclamation_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 20] "Nombre de réclamations par agence"
**Aiguillage Global :** `CANDIDATE_PATH_PENDING` | **Query ID Final :** `QC-PEND-FC1867EB` | **Statut Cycle de Vie :** `N/A`

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
- **Query ID associé :** `QC-PEND-FC1867EB`
#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]
- **Tables autorisées :** ``
- **Étanchéité PII / RGPD :** ✅ Strictement respectée (aucune colonne sensible)

#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]
#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]
- **Validation syntaxique :** `[NON_EVALUE]`
- **Contrôles validés :** Contrôles nominaux

#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]
- **Statut d'exécution BDD :** `SUCCESS`
- **Lignes retournées :** `4` | **Durée :** `12.68 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `CANDIDATE_PENDING` | **Visualisation :** `bar`
- **Synthèse formulée :** "Pour la période demandée, un total de 43 reclamation_count a été enregistré, avec la répartition suivante par agency : A..."
--------------------------------------------------------------------------------

### [Requête N° 21] "En 2026"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-UNIFIED-PLAINTES-TOTAL` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `2026-01-01 -> 2027-01-01 (champ=receipt_date)`
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
  "time": {
    "field_concept": "receipt_date",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "timezone": "Africa/Porto-Novo"
  },
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-UNIFIED-PLAINTES-TOTAL`
- **Libellé métier homologué :** "Volume total unifié des plaintes (réclamations, dénonciations, suggestions)"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026
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
- **Lignes retournées :** `1` | **Durée :** `12.20 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 52."
--------------------------------------------------------------------------------

### [Requête N° 22] "En mars 2026"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-UNIFIED-PLAINTES-TOTAL` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `2026-03-01 -> 2026-03-31 (champ=receipt_date)`
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
  "time": {
    "field_concept": "receipt_date",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31",
    "timezone": "Africa/Porto-Novo"
  },
  "dimensions": [],
  "filters": [],
  "status": "ready"
}
```
#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-UNIFIED-PLAINTES-TOTAL`
- **Libellé métier homologué :** "Volume total unifié des plaintes (réclamations, dénonciations, suggestions)"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026
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
- **Lignes retournées :** `1` | **Durée :** `16.63 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 23] "Premier trimestre 2026"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-UNIFIED-PLAINTES-TOTAL` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `2026-01-01 -> 2026-03-31 (champ=receipt_date)`
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
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-UNIFIED-PLAINTES-TOTAL`
- **Libellé métier homologué :** "Volume total unifié des plaintes (réclamations, dénonciations, suggestions)"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026
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
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 0."
--------------------------------------------------------------------------------

### [Requête N° 24] "Ce mois-ci"
**Aiguillage Global :** `FAST_PATH_HOMOLOGATED` | **Query ID Final :** `QC-UNIFIED-PLAINTES-TOTAL` | **Statut Cycle de Vie :** `N/A`

#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]
- **Source de résolution :** `GENERATIVE_LLM_NEMOTRON`
- **Statut résolu :** `ready` | **Entité :** `plainte (types=['CLAIM', 'DENUNCIATION', 'SUGGESTION'])` | **Mesure :** `plainte_count (libelle: "plainte_count")`
- **Dimensions :** `['aucune (global)']` | **Filtres :** `aucun` | **Période :** `2026-10-01 -> 2026-10-31 (champ=receipt_date)`
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
- **Circuit retenu :** `FAST_PATH_HOMOLOGATED`
- **Query ID associé :** `QC-UNIFIED-PLAINTES-TOTAL`
- **Libellé métier homologué :** "Volume total unifié des plaintes (réclamations, dénonciations, suggestions)"
```sql
-- SQL DU TEMPLATE HOMOLOGUÉ :
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026
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
- **Lignes retournées :** `1` | **Durée :** `26.33 ms`
- **Cycle de vie :** `N/A`

#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]
- **Mode d'exécution :** `FAST_PATH_HOMOLOGATED` | **Visualisation :** `aucune`
- **Synthèse formulée :** "Pour la période demandée, le résultat pour plainte_count est de 0."
--------------------------------------------------------------------------------
