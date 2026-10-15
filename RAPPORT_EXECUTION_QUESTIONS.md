# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné

**Date d'exécution** : 2026-10-14 22:36:02 UTC  
**Nombre de questions traitées** : 24  

## Synthèse des Résultats

| N° | Question | Statut | Mode | Query ID | Durée | SQL Exécuté |
|---|---|---|---|---|---|---|
| 1 | Combien de réclamations ? | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-8C936F86` | 112639.38 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 2 | Quelles sont les dénonciations enregistrées ? | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-1E32053F` | 9424.51 ms | `SELECT COUNT(CASE WHEN claim_type = 'DENUNCIATION' THEN 1 EN...` |
| 3 | Nombre d'idées et suggestions d'amélioration | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-6AF83385` | 25011.53 ms | `SELECT COUNT(reporting_suggestion.id) AS suggestion_count FR...` |
| 4 | Volume total de dossiers reçus par la banque | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-437500D2` | 9513.93 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...` |
| 5 | Combien de transferts de dossiers ont eu lieu ? | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-A1CE3781` | 22435.66 ms | `SELECT COUNT(CASE WHEN affectation_precedente_id IS NOT NULL...` |
| 6 | Plaintes | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-437500D2` | 4067.61 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...` |
| 7 | Réclamations moyennes | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-142E5CFC` | 16156.13 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 8 | Taux de respect des engagements SLA | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-27A64E58` | 23295.48 ms | `SELECT AVG(CASE WHEN resolved_at <= sla_due_at THEN 100.0 EL...` |
| 9 | Pourcentage d'usagers satisfaits | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-BD16F96B` | 11883.52 ms | `SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THE...` |
| 10 | Score moyen de risque estimé | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-8DDF3F5A` | 22290.65 ms | `SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM repo...` |
| 11 | Réclamations par agence | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-FC1867EB` | 10505.22 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |
| 12 | Dossiers par canal de collecte | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-83290F94` | 18026.11 ms | `SELECT cc.libelle AS channel, COUNT(*) AS plainte_count FROM...` |
| 13 | Suggestions selon le niveau d'impact | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-232E1218` | 11454.26 ms | `SELECT impact_level AS impact_level, COUNT(id) AS suggestion...` |
| 14 | Réclamations par agence et par canal | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-283479FE` | 14930.67 ms | `SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(CA...` |
| 15 | Total des réclamations | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-8C936F86` | 2773.52 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 16 | Réclamations graves | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-ACD52C4E` | 8918.57 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 17 | Plaintes critiques ou lourdes | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-A7083450` | 25621.0 ms | `SELECT (SELECT COUNT(*) FROM reporting_claim WHERE risk_leve...` |
| 18 | Dossiers insatisfaits | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-4FB7184D` | 29759.1 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE satisfac...` |
| 19 | Réclamations graves insatisfaites du canal Web | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-17E0DEFC` | 23152.42 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 20 | Nombre de réclamations par agence | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-FC1867EB` | 3468.6 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |
| 21 | En 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 5621.11 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 22 | En mars 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 8466.54 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 23 | Premier trimestre 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 5727.47 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 24 | Ce mois-ci | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 8976.83 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |

## Détail des Réponses formulées

### 1. « Combien de réclamations ? »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim;
```

### 2. « Quelles sont les dénonciations enregistrées ? »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'DENUNCIATION' THEN 1 END) AS denonciation_count FROM reporting_claim;
```

### 3. « Nombre d'idées et suggestions d'amélioration »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count
```sql
SELECT COUNT(reporting_suggestion.id) AS suggestion_count FROM reporting_suggestion;
```

### 4. « Volume total de dossiers reçus par la banque »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;
```

### 5. « Combien de transferts de dossiers ont eu lieu ? »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reaffectation_count
```sql
SELECT COUNT(CASE WHEN affectation_precedente_id IS NOT NULL THEN 1 END) AS reaffectation_count FROM reporting_historique_affectations;
```

### 6. « Plaintes »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;
```

### 7. « Réclamations moyennes »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'MOYEN';
```

### 8. « Taux de respect des engagements SLA »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT AVG(CASE WHEN resolved_at <= sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate FROM reporting_claim WHERE claim_type = 'CLAIM';
```

### 9. « Pourcentage d'usagers satisfaits »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : Taux de satisfaction
```sql
SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' ORDER BY satisfaction_rate DESC;
```

### 10. « Score moyen de risque estimé »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : custom_avg_risk_score
```sql
SELECT AVG(ai_risk_score) AS custom_avg_risk_score FROM reporting_claim WHERE risk_level = 'MOYEN' ORDER BY custom_avg_risk_score DESC;
```

### 11. « Réclamations par agence »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency,
       COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
FROM reporting_service_point sp
LEFT JOIN reporting_claim c ON c.service_point_id = sp.id
GROUP BY sp.libelle
ORDER BY reclamation_count DESC;
```

### 12. « Dossiers par canal de collecte »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count par channel
```sql
SELECT cc.libelle AS channel, COUNT(*) AS plainte_count FROM (SELECT collection_channel_id FROM reporting_claim UNION ALL SELECT collection_channel_id FROM reporting_suggestion) u JOIN reporting_collection_channel cc ON u.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY plainte_count DESC;
```

### 13. « Suggestions selon le niveau d'impact »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count par impact_level
```sql
SELECT impact_level AS impact_level, COUNT(id) AS suggestion_count FROM reporting_suggestion GROUP BY impact_level ORDER BY suggestion_count DESC;
```

### 14. « Réclamations par agence et par canal »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id GROUP BY agency, channel ORDER BY reclamation_count DESC;
```

### 15. « Total des réclamations »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim;
```

### 16. « Réclamations graves »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'GRAVE' ORDER BY reclamation_count DESC
```

### 17. « Plaintes critiques ou lourdes »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT (SELECT COUNT(*) FROM reporting_claim WHERE risk_level = 'GRAVE') AS plainte_count
```

### 18. « Dossiers insatisfaits »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE satisfaction_status = 'UNSATISFIED') + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count;
```

### 19. « Réclamations graves insatisfaites du canal Web »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.risk_level = 'GRAVE' AND c.satisfaction_status = 'UNSATISFIED' AND cc.libelle = 'WEB' ORDER BY reclamation_count DESC
```

### 20. « Nombre de réclamations par agence »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency,
       COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
FROM reporting_service_point sp
LEFT JOIN reporting_claim c ON c.service_point_id = sp.id
GROUP BY sp.libelle
ORDER BY reclamation_count DESC;
```

### 21. « En 2026 »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026-01-01 00:00:00' AND receipt_at < '2027-01-01 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= '2026-01-01 00:00:00' AND recorded_at < '2027-01-01 00:00:00')) AS plainte_count
```

### 22. « En mars 2026 »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026-03-01 00:00:00' AND receipt_at < '2026-03-31 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= '2026-03-01 00:00:00' AND recorded_at < '2026-03-31 00:00:00')) AS plainte_count
```

### 23. « Premier trimestre 2026 »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026-01-01 00:00:00' AND receipt_at < '2026-03-31 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= '2026-01-01 00:00:00' AND recorded_at < '2026-03-31 00:00:00')) AS plainte_count
```

### 24. « Ce mois-ci »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026-10-01 00:00:00' AND receipt_at < '2026-10-31 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= '2026-10-01 00:00:00' AND recorded_at < '2026-10-31 00:00:00')) AS plainte_count
```
