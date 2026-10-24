# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné

**Date d'exécution** : 2026-10-16 23:07:45 UTC  
**Nombre de questions traitées** : 24  

## Synthèse des Résultats

| N° | Question | Statut | Mode | Query ID | Durée | SQL Exécuté |
|---|---|---|---|---|---|---|
| 1 | Combien de réclamations ? | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-08AF689F` | 54566.42 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 2 | Quelles sont les dénonciations enregistrées ? | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-A73CF5E9` | 28748.23 ms | `SELECT COUNT(CASE WHEN c.claim_type IN ('DENUNCIATION', 'DEN...` |
| 3 | Nombre d'idées et suggestions d'amélioration | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-AB367C5F` | 11967.16 ms | `SELECT COUNT(id) AS suggestion_count FROM reporting_suggesti...` |
| 4 | Volume total de dossiers reçus par la banque | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-AUTO-572FF510` | 5696.53 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...` |
| 5 | Combien de transferts de dossiers ont eu lieu ? | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-06829A4F` | 20599.81 ms | `SELECT COUNT(CASE WHEN affectation_precedente_id IS NOT NULL...` |
| 6 | Plaintes | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-AUTO-572FF510` | 17566.81 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COU...` |
| 7 | Réclamations moyennes | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-38C950EB` | 24474.04 ms | `SELECT COUNT(c.id) AS custom_avg_reclamation_count FROM repo...` |
| 8 | Taux de respect des engagements SLA | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-A03BA23A` | 30540.56 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 9 | Pourcentage d'usagers satisfaits | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-EB470A15` | 36834.37 ms | `SELECT COUNT(*) AS satisfaction_rate FROM reporting_claim WH...` |
| 10 | Score moyen de risque estimé | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-3E9F6784` | 55136.82 ms | `SELECT COUNT(*) AS custom_avg_risk_score FROM reporting_clai...` |
| 11 | Réclamations par agence | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-C353D78A` | 23809.21 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |
| 12 | Dossiers par canal de collecte | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-E264D924` | 62739.55 ms | `WITH unioned AS (SELECT cc.libelle AS channel FROM reporting...` |
| 13 | Suggestions selon le niveau d'impact | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-A25C8055` | 19677.71 ms | `SELECT s.impact_level AS impact_level, COUNT(s.id) AS sugges...` |
| 14 | Réclamations par agence et par canal | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-73105368` | 17926.41 ms | `SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(CA...` |
| 15 | Total des réclamations | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-08AF689F` | 6990.74 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 16 | Réclamations graves | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-67F2E367` | 20555.88 ms | `SELECT COUNT(*) AS reclamation_count FROM reporting_claim c ...` |
| 17 | Plaintes critiques ou lourdes | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-026DCB61` | 37199.45 ms | `SELECT COUNT(CASE WHEN risk_level = 'GRAVE' THEN 1 END) AS s...` |
| 18 | Dossiers insatisfaits | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-62FF582E` | 45209.98 ms | `WITH c1 AS (SELECT COUNT(*) AS cnt FROM reporting_claim WHER...` |
| 19 | Réclamations graves insatisfaites du canal Web | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-E64C1702` | 24006.24 ms | `SELECT COUNT(*) AS reclamation_count FROM reporting_claim c ...` |
| 20 | Nombre de réclamations par agence | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-C353D78A` | 9318.08 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |
| 21 | En 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 11340.5 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 22 | En mars 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 26129.4 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 23 | Premier trimestre 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 14717.33 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 24 | Ce mois-ci | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 12885.74 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |

## Détail des Réponses formulées

### 1. « Combien de réclamations ? »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim;
```

### 2. « Quelles sont les dénonciations enregistrées ? »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type IN ('DENUNCIATION', 'DENUNCIACION') THEN 1 END) AS denonciation_count FROM reporting_claim c
```

### 3. « Nombre d'idées et suggestions d'amélioration »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count
```sql
SELECT COUNT(id) AS suggestion_count FROM reporting_suggestion
```

### 4. « Volume total de dossiers reçus par la banque »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```

### 5. « Combien de transferts de dossiers ont eu lieu ? »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reaffectation_count
```sql
SELECT COUNT(CASE WHEN affectation_precedente_id IS NOT NULL THEN 1 END) AS reaffectation_count FROM reporting_historique_affectations WHERE type_plainte IN ('CLAIM','DENUNCIATION','SUGGESTION');
```

### 6. « Plaintes »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)) AS plainte_count
```

### 7. « Réclamations moyennes »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : custom_avg_reclamation_count
```sql
SELECT COUNT(c.id) AS custom_avg_reclamation_count FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MOYEN' ORDER BY custom_avg_reclamation_count DESC;
```

### 8. « Taux de respect des engagements SLA »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c WHERE c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION');
```

### 9. « Pourcentage d'usagers satisfaits »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : satisfaction_rate
```sql
SELECT COUNT(*) AS satisfaction_rate FROM reporting_claim WHERE status = 'SATISFIED' AND claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION')
```

### 10. « Score moyen de risque estimé »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : custom_avg_risk_score
```sql
SELECT COUNT(*) AS custom_avg_risk_score FROM reporting_claim c WHERE c.risk_level = 'MOYEN' AND c.claim_type IN ('CLAIM','DENUNCIATION') ORDER BY custom_avg_risk_score DESC;
```

### 11. « Réclamations par agence »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_service_point sp LEFT JOIN reporting_claim c ON c.service_point_id = sp.id GROUP BY sp.libelle ORDER BY reclamation_count DESC;
```

### 12. « Dossiers par canal de collecte »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count par channel
```sql
WITH unioned AS (SELECT cc.libelle AS channel FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id UNION ALL SELECT cc.libelle AS channel FROM reporting_suggestion s LEFT JOIN reporting_collection_channel cc ON s.collection_channel_id = cc.id) SELECT COALESCE(channel, 'INCONNU') AS channel, COUNT(1) AS plainte_count FROM unioned GROUP BY channel ORDER BY plainte_count DESC;
```

### 13. « Suggestions selon le niveau d'impact »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count par impact_level
```sql
SELECT s.impact_level AS impact_level, COUNT(s.id) AS suggestion_count FROM reporting_suggestion s GROUP BY s.impact_level ORDER BY suggestion_count DESC;
```

### 14. « Réclamations par agence et par canal »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, cc.libelle AS channel, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id GROUP BY sp.libelle, cc.libelle ORDER BY reclamation_count DESC
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
SELECT COUNT(*) AS reclamation_count FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'GRAVE';
```

### 17. « Plaintes critiques ou lourdes »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : severe_plainte_count
```sql
SELECT COUNT(CASE WHEN risk_level = 'GRAVE' THEN 1 END) AS severe_plainte_count FROM reporting_claim WHERE claim_type IN ('CLAIM', 'DENUNCIATION', 'SUGGESTION');
```

### 18. « Dossiers insatisfaits »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
WITH c1 AS (SELECT COUNT(*) AS cnt FROM reporting_claim WHERE status = 'UNSATISFIED' AND claim_type IN ('CLAIM','DENUNCIATION')), c2 AS (SELECT COUNT(*) AS cnt FROM reporting_suggestion WHERE status = 'UNSATISFIED') SELECT (c1.cnt + c2.cnt) AS plainte_count FROM c1, c2;
```

### 19. « Réclamations graves insatisfaites du canal Web »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(*) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'GRAVE' AND c.status = 'UNSATISFIED' AND cc.libelle = 'WEB'
```

### 20. « Nombre de réclamations par agence »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_service_point sp LEFT JOIN reporting_claim c ON c.service_point_id = sp.id GROUP BY sp.libelle ORDER BY reclamation_count DESC;
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
