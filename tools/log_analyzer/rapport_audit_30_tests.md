# Rapport d'Audit Automatique du Workflow Text-to-SQL
**Fichier audité :** `04-finCWINDOWSsystem32cmd.exe - .venvScriptspython.exe  -m uvicorn mainapp --port 8005 --reload.txt`

## 1. Tableau de Bord Synthétique des Risques
- **Total des requêtes analysées :** 30
- **Hits Fast-Path (Homologués) :** 4
- **Hits Candidate-Path (En attente) :** 14
- **Générations LLM Nemotron :** 12
- 🚨 **Replis silencieux détectés :** 3 (Étape 1: 1, Étape 4: 2)
- 🚨 **Divergences SQL Brut LLM vs Exécuté :** 2
- ⚠️ **Désynchronisations temporelles Candidate-Path :** 4
- ⚠️ **Paramètres orphelins :** 9
- 🔒 **Fuites PII :** 0
- ❌ **Erreurs d'exécution SQL :** 0

## 2. Anomalies Critiques Détectées par Requête

### [Run 03] "Combien de suggestion?"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-2FF7F0BB` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 05] "Quelles sont les sugestionenregistrées ?"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-2FF7F0BB` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 07] "Nombre d'idées et suggestions d'amélioration"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-F641C06A` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 12] "Réclamations moyennes"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-F11CD1EA` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 15] "Score moyen de risque estimé"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-AUTO-572FF510` | **Cycle de vie :** `APPROVED`
- 🚨 **[Étape 4 (Générateur SQL)] SILENT_FALLBACK_CANDIDATE** : Échec de validation Pydantic TextToSQLCandidate (1 validation error for TextToSQLCandidate
result_columns.0.data_type
  Input should be 'string', 'integer', 'decimal', 'boolean', 'date' or 'datetime' [type=literal_error, input_value='double', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error). Repli silencieux vers le générateur déterministe.
- 🚨 **[Étape 4 (Générateur SQL)] RAW_VS_CANDIDATE_SQL_DIVERGENCE** : Le LLM a proposé une requête spécifique mais le système a exécuté le fallback global 'plainte_count' ! (Proposé: SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM repo... | Exécuté: SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...)
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']
- 🚨 **[Étape 7 (Restitution)] SEMANTIC_SYNTHESIS_CORRUPTED** : Incohérence sémantique majeure : La synthèse formule 'Pour la période demandée, le résultat pour custom_avg_risk_score est de 52.' sur la base d'un comptage brut (52) issu du fallback déterministe.
  ```sql
  -- PROPOSÉ PAR LE LLM :
  SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM reporting_claim WHERE risk_level = :risk_level AND claim_type IN ('CLAIM', 'DENUNCIATION') ORDER BY custom_avg_risk_score DESC;
  -- RÉELLEMENT EXÉCUTÉ (FALLBACK) :
  SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
  ```

### [Run 17] "Dossiers par canal de collecte"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-96F3D64F` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 21] "Réclamations graves"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-226DBA67` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 22] "Plaintes critiques ou lourdes"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-AUTO-572FF510` | **Cycle de vie :** `APPROVED`
- 🚨 **[Étape 4 (Générateur SQL)] SILENT_FALLBACK_CANDIDATE** : Échec de validation Pydantic TextToSQLCandidate (1 validation error for TextToSQLCandidate
parameters.risk_level.type
  Input should be 'date', 'datetime', 'string', 'integer', 'decimal' or 'boolean' [type=literal_error, input_value='varchar', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/literal_error). Repli silencieux vers le générateur déterministe.
- ⚠️ **[Étape 4 (Générateur SQL)] SQL_STRUCTURAL_DIFF** : Différence structurelle entre le SQL brut du LLM et le SQL candidat exécuté. (Proposé: SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE risk_lev... | Exécuté: SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...)
  ```sql
  -- PROPOSÉ PAR LE LLM :
  SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE risk_level = :risk_level) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;
  -- RÉELLEMENT EXÉCUTÉ (FALLBACK) :
  SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
  ```

### [Run 23] "Dossiers insatisfaits"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-E3EDFC99` | **Cycle de vie :** `PENDING`
- 🚨 **[Étape 1 (Intention)] SILENT_FALLBACK_INTENT** : Échec de validation Pydantic LLM (1 validation error for TextToSQLIntent
entity
  Value error, types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true [type=value_error, input_value={'concept_id': 'plainte',...rue, 'types': ['CLAIM']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/value_error). Repli silencieux vers le résolveur déterministe.
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 24] "Dossiers insatisfaits"
- **Routage :** `GENERATIVE_LLM` | **Query ID :** `QC-PEND-A299EBC2` | **Cycle de vie :** `PENDING`
- ℹ️ **[Étape 4 (Générateur SQL)] ORPHAN_PARAMETERS** : Paramètres déclarés dans le contrat mais absents de la clause SQL : ['start_date', 'end_date']

### [Run 27] "Nombre de réclamations par agence en 2026"
- **Routage :** `CANDIDATE_PATH_PENDING` | **Query ID :** `QC-PEND-CA4F2CB4` | **Cycle de vie :** `N/A`
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-01-01 -> 2027-01-01 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

### [Run 28] "Nombre de réclamations par agence en mars 2026"
- **Routage :** `CANDIDATE_PATH_PENDING` | **Query ID :** `QC-PEND-CA4F2CB4` | **Cycle de vie :** `N/A`
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-03-01 -> 2026-03-31 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

### [Run 29] "Nombre de réclamations par agence en premier trimestre 2026"
- **Routage :** `CANDIDATE_PATH_PENDING` | **Query ID :** `QC-PEND-CA4F2CB4` | **Cycle de vie :** `N/A`
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-01-01 -> 2026-03-31 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

### [Run 30] "Nombre de réclamations par agence ce mois ci"
- **Routage :** `CANDIDATE_PATH_PENDING` | **Query ID :** `QC-PEND-CA4F2CB4` | **Cycle de vie :** `N/A`
- ⚠️ **[Étape 2 (Candidate-Path)] TEMPORAL_MISMATCH_CANDIDATE** : Désynchronisation temporelle : L'intention exige une période temporelle (2026-10-01 -> 2026-10-31 (champ=receipt_date)), mais le Candidate-Path a réutilisé la requête en attente (QC-PEND-CA4F2CB4) sans valider la présence de filtre temporel.

## 3. Matrice Exhaustive des 30 Runs

| # | Question | Routage | Query ID | SQL Divergent ? | Repli Silencieux ? | Statut BDD |
|---|---|---|---|---|---|---|
| 01 | Combien de réclamations ? | CANDIDATE_PATH_PENDING | `QC-PEND-7F42ED05` | Non | Non | SUCCESS |
| 02 | Combien de denonciation? | CANDIDATE_PATH_PENDING | `QC-PEND-9641EE89` | Non | Non | SUCCESS |
| 03 | Combien de suggestion? | GENERATIVE_LLM | `QC-PEND-2FF7F0BB` | Non | Non | SUCCESS |
| 04 | Quelles sont les dénonciations enregistrées ? | CANDIDATE_PATH_PENDING | `QC-PEND-9641EE89` | Non | Non | SUCCESS |
| 05 | Quelles sont les sugestionenregistrées ? | GENERATIVE_LLM | `QC-PEND-2FF7F0BB` | Non | Non | SUCCESS |
| 06 | Quelles sont les reclationenregistrées ? | CANDIDATE_PATH_PENDING | `QC-PEND-7F42ED05` | Non | Non | SUCCESS |
| 07 | Nombre d'idées et suggestions d'amélioration | GENERATIVE_LLM | `QC-PEND-F641C06A` | Non | Non | SUCCESS |
| 08 | Volume total de dossiers reçus par la banque | FAST_PATH_HOMOLOGATED | `QC-AUTO-572FF510` | Non | Non | SUCCESS |
| 09 | Volume de dossiers reçus par la banque | FAST_PATH_HOMOLOGATED | `QC-AUTO-572FF510` | Non | Non | SUCCESS |
| 10 | Combien de transferts de dossiers ont eu lieu ? | CANDIDATE_PATH_PENDING | `QC-PEND-97A0C00A` | Non | Non | SUCCESS |
| 11 | Plaintes | FAST_PATH_HOMOLOGATED | `QC-AUTO-572FF510` | Non | Non | SUCCESS |
| 12 | Réclamations moyennes | GENERATIVE_LLM | `QC-PEND-F11CD1EA` | Non | Non | SUCCESS |
| 13 | Taux de respect des engagements SLA | FAST_PATH_HOMOLOGATED | `QC-AUTO-DCFB5C69` | Non | Non | SUCCESS |
| 14 | Pourcentage d'usagers satisfaits | GENERATIVE_LLM | `QC-PEND-AF217D8A` | Non | Non | SUCCESS |
| 15 | Score moyen de risque estimé | GENERATIVE_LLM | `QC-AUTO-572FF510` | 🚨 OUI | 🚨 OUI | SUCCESS |
| 16 | Réclamations par agence | CANDIDATE_PATH_PENDING | `QC-PEND-CA4F2CB4` | Non | Non | SUCCESS |
| 17 | Dossiers par canal de collecte | GENERATIVE_LLM | `QC-PEND-96F3D64F` | Non | Non | SUCCESS |
| 18 | Suggestions selon le niveau d'impact | CANDIDATE_PATH_PENDING | `QC-PEND-6EBA969F` | Non | Non | SUCCESS |
| 19 | Réclamations par agence et par canal | CANDIDATE_PATH_PENDING | `QC-PEND-F08016E5` | Non | Non | SUCCESS |
| 20 | Total des réclamations | CANDIDATE_PATH_PENDING | `QC-PEND-7F42ED05` | Non | Non | SUCCESS |
| 21 | Réclamations graves | GENERATIVE_LLM | `QC-PEND-226DBA67` | Non | Non | SUCCESS |
| 22 | Plaintes critiques ou lourdes | GENERATIVE_LLM | `QC-AUTO-572FF510` | 🚨 OUI | 🚨 OUI | SUCCESS |
| 23 | Dossiers insatisfaits | GENERATIVE_LLM | `QC-PEND-E3EDFC99` | Non | 🚨 OUI | SUCCESS |
| 24 | Dossiers insatisfaits | GENERATIVE_LLM | `QC-PEND-A299EBC2` | Non | Non | SUCCESS |
| 25 | Réclamations graves insatisfaites du canal Web | GENERATIVE_LLM | `QC-PEND-C3EECB8A` | Non | Non | SUCCESS |
| 26 | Nombre de réclamations par agence | CANDIDATE_PATH_PENDING | `QC-PEND-CA4F2CB4` | Non | Non | SUCCESS |
| 27 | Nombre de réclamations par agence en 2026 | CANDIDATE_PATH_PENDING | `QC-PEND-CA4F2CB4` | Non | Non | SUCCESS |
| 28 | Nombre de réclamations par agence en mars 2026 | CANDIDATE_PATH_PENDING | `QC-PEND-CA4F2CB4` | Non | Non | SUCCESS |
| 29 | Nombre de réclamations par agence en premier trimestre 2026 | CANDIDATE_PATH_PENDING | `QC-PEND-CA4F2CB4` | Non | Non | SUCCESS |
| 30 | Nombre de réclamations par agence ce mois ci | CANDIDATE_PATH_PENDING | `QC-PEND-CA4F2CB4` | Non | Non | SUCCESS |