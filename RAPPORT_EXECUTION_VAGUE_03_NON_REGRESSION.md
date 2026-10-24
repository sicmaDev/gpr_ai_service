# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné

**Date d'exécution** : 2026-10-16 23:59:17 UTC  
**Nombre de questions traitées** : 24  

## Synthèse des Résultats

| N° | Question | Statut | Mode | Query ID | Durée | SQL Exécuté |
|---|---|---|---|---|---|---|
| 1 | Taux de respect des délais SLA par agence en 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-8748240C` | 191783.03 ms | `SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resol...` |
| 2 | Top 3 des agences avec le plus grand nombre de réclamations | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-C353D78A` | 7269.94 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |
| 3 | Délai moyen de traitement des réclamations par canal en 2026 | ❌ Échec | `FAILED` | `-` | 13559.08 ms | `-` |
| 4 | Taux de satisfaction des usagers par canal de collecte | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-5C3C9B60` | 24549.42 ms | `SELECT cc.libelle AS channel, ROUND((COUNT(CASE WHEN c.statu...` |
| 5 | Pourcentage de respect des SLA pour les réclamations de l'Agence Abidjan | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-DBDFE322` | 25727.72 ms | `SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resol...` |
| 6 | Top 5 des motifs de réclamations les plus fréquents en 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-4ABF0AD7` | 10318.92 ms | `SELECT o.libelle AS object, COUNT(CASE WHEN c.claim_type = '...` |
| 7 | Délai moyen de résolution des dossiers pour l'Agence Bouaké | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-AA79C17C` | 40971.93 ms | `SELECT AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_pro...` |
| 8 | Taux de respect des délais SLA par niveau de risque | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-213AC432` | 13885.15 ms | `SELECT c.risk_level AS risk_level, ROUND((COUNT(CASE WHEN (c...` |
| 9 | Classement des agences par délai moyen de traitement en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-A2CA757D` | 69878.23 ms | `SELECT sp.libelle AS agency, AVG(DATEDIFF(c.resolved_at, c.r...` |
| 10 | Taux de satisfaction des réclamations pour le canal WEB | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-5DD82973` | 30740.7 ms | `WITH filtered AS ( SELECT c.status, cc.libelle AS channel FR...` |
| 11 | Top 3 des canaux de collecte avec le plus fort volume de réclamations | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-A0D23DA7` | 11640.73 ms | `SELECT cc.libelle AS channel, COUNT(CASE WHEN c.claim_type =...` |
| 12 | Nombre moyen de jours de traitement des réclamations reçues en août 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-91832FA0` | 21520.24 ms | `SELECT AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_pro...` |
| 13 | Taux de respect SLA pour les réclamations enregistrées en juillet 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-SLA-ADHERENCE-RATE` | 7894.23 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 14 | Top 3 des agences ayant le meilleur taux de respect SLA en 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-8748240C` | 32296.39 ms | `SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resol...` |
| 15 | Délai moyen de traitement des plaintes graves en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-0A783EB9` | 38063.99 ms | `SELECT AVG(DATEDIFF(resolved_at, receipt_at)) AS avg_process...` |
| 16 | Taux de satisfaction global des réclamations en 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-SATISFACTION-RATE` | 5503.92 ms | `SELECT ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 ...` |
| 17 | Classement des canaux de collecte selon le taux de satisfaction usagers | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-5C3C9B60` | 12933.71 ms | `SELECT cc.libelle AS channel, ROUND((COUNT(CASE WHEN c.statu...` |
| 18 | Top 5 des dossiers avec le délai de traitement le plus long | ✅ Succès | `VALIDATION_BLOCKED` | `-` | 42372.12 ms | `SELECT COUNT(processing_time) AS processing_time FROM ( SELE...` |
| 19 | Taux de respect des SLA pour les réclamations reçues via le canal AGENCE | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-984502C0` | 29653.96 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 20 | Délai moyen de traitement des réclamations par agence en 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-A2CA757D` | 8078.98 ms | `SELECT sp.libelle AS agency, AVG(DATEDIFF(c.resolved_at, c.r...` |
| 21 | Taux de satisfaction des usagers pour l'Agence Korhogo en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-FF4292AE` | 20022.13 ms | `SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN c.status...` |
| 22 | Top 3 des motifs de dénonciations enregistrées en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-BE94E1EA` | 27000.79 ms | `SELECT o.libelle AS object, COUNT(CASE WHEN c.claim_type IN ...` |
| 23 | Taux de respect des délais SLA pour les dossiers de niveau de risque moyen | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-26FBC799` | 24513.1 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 24 | Classement des agences par volume total de réclamations traitées | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-C353D78A` | 13104.14 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |

## Détail des Réponses formulées

### 1. « Taux de respect des délais SLA par agence en 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : sla_adherence_rate par agency
```sql
SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' AND c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY sp.libelle ORDER BY sla_adherence_rate DESC
```

### 2. « Top 3 des agences avec le plus grand nombre de réclamations »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_service_point sp LEFT JOIN reporting_claim c ON c.service_point_id = sp.id GROUP BY sp.libelle ORDER BY reclamation_count DESC;
```

### 3. « Délai moyen de traitement des réclamations par canal en 2026 »
- **Mode** : `FAILED`
- **Synthèse** : Erreur d'exécution : int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

### 4. « Taux de satisfaction des usagers par canal de collecte »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : satisfaction_rate par channel
```sql
SELECT cc.libelle AS channel, ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 END) * 100.0) / NULLIF(COUNT(CASE WHEN c.status IN ('SATISFIED','UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY cc.libelle ORDER BY satisfaction_rate DESC;
```

### 5. « Pourcentage de respect des SLA pour les réclamations de l'Agence Abidjan »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate par agency
```sql
SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' GROUP BY sp.libelle ORDER BY sla_adherence_rate DESC
```

### 6. « Top 5 des motifs de réclamations les plus fréquents en 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par object
```sql
SELECT o.libelle AS object, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_objet o ON c.objet_id = o.id WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' GROUP BY o.libelle ORDER BY reclamation_count DESC
```

### 7. « Délai moyen de résolution des dossiers pour l'Agence Bouaké »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : avg_processing_time
```sql
SELECT AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_processing_time FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE sp.libelle = 'Bouaké' AND c.risk_level = 'MOYEN' AND c.claim_type IN ('CLAIM', 'DENUNCIATION') AND c.status = 'SATISFIED' AND c.resolved_at IS NOT NULL AND c.receipt_at IS NOT NULL;
```

### 8. « Taux de respect des délais SLA par niveau de risque »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : sla_adherence_rate par risk_level
```sql
SELECT c.risk_level AS risk_level, ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c WHERE c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY c.risk_level ORDER BY sla_adherence_rate DESC;
```

### 9. « Classement des agences par délai moyen de traitement en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : avg_processing_time par agency
```sql
SELECT sp.libelle AS agency, AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_processing_time FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MOYEN' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' AND c.resolved_at IS NOT NULL GROUP BY sp.libelle ORDER BY avg_processing_time DESC
```

### 10. « Taux de satisfaction des réclamations pour le canal WEB »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : satisfaction_rate par channel
```sql
WITH filtered AS (
  SELECT c.status, cc.libelle AS channel
  FROM reporting_claim c
  LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id
  WHERE c.claim_type = 'CLAIM'
    AND cc.libelle = 'WEB'
)
SELECT
  channel,
  ROUND(
    (COUNT(CASE WHEN status = 'SATISFIED' THEN 1 END) * 100.0) /
    NULLIF(COUNT(CASE WHEN status IN ('SATISFIED','UNSATISFIED') THEN 1 END), 0)
  , 2) AS satisfaction_rate
FROM filtered
GROUP BY channel
ORDER BY satisfaction_rate DESC;
```

### 11. « Top 3 des canaux de collecte avec le plus fort volume de réclamations »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par channel
```sql
SELECT cc.libelle AS channel, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY reclamation_count DESC;
```

### 12. « Nombre moyen de jours de traitement des réclamations reçues en août 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : avg_processing_time
```sql
SELECT AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_processing_time FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MOYEN' AND c.status = 'SATISFIED' AND c.receipt_at >= '2026-08-01 00:00:00' AND c.receipt_at < '2026-08-31 00:00:00'
```

### 13. « Taux de respect SLA pour les réclamations enregistrées en juillet 2026 »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= '2026-07-01 00:00:00' AND c.receipt_at < '2026-07-31 00:00:00'
```

### 14. « Top 3 des agences ayant le meilleur taux de respect SLA en 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : sla_adherence_rate par agency
```sql
SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' AND c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY sp.libelle ORDER BY sla_adherence_rate DESC
```

### 15. « Délai moyen de traitement des plaintes graves en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : avg_processing_time
```sql
SELECT AVG(DATEDIFF(resolved_at, receipt_at)) AS avg_processing_time FROM reporting_claim WHERE risk_level = 'GRAVE' AND receipt_at >= '2026-01-01 00:00:00' AND receipt_at < '2027-01-01 00:00:00' ORDER BY avg_processing_time DESC;
```

### 16. « Taux de satisfaction global des réclamations en 2026 »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : satisfaction_rate
```sql
SELECT ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 END) * 100.0) / NULLIF(COUNT(CASE WHEN c.status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00'
```

### 17. « Classement des canaux de collecte selon le taux de satisfaction usagers »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : satisfaction_rate par channel
```sql
SELECT cc.libelle AS channel, ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 END) * 100.0) / NULLIF(COUNT(CASE WHEN c.status IN ('SATISFIED','UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY cc.libelle ORDER BY satisfaction_rate DESC;
```

### 18. « Top 5 des dossiers avec le délai de traitement le plus long »
- **Mode** : `VALIDATION_BLOCKED`
- **Synthèse** : Requête non conforme
```sql
SELECT COUNT(processing_time) AS processing_time FROM ( SELECT TIMESTAMPDIFF(SECOND, receipt_at, resolved_at) AS processing_time FROM reporting_claim WHERE claim_type IN ('CLAIM', 'DENUNCIATION') UNION ALL SELECT NULL AS processing_time FROM reporting_suggestion ) AS combined;
```

### 19. « Taux de respect des SLA pour les réclamations reçues via le canal AGENCE »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.claim_type = 'CLAIM' AND cc.libelle = 'AGENCE'
```

### 20. « Délai moyen de traitement des réclamations par agence en 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : avg_processing_time par agency
```sql
SELECT sp.libelle AS agency, AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_processing_time FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MOYEN' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' AND c.resolved_at IS NOT NULL GROUP BY sp.libelle ORDER BY avg_processing_time DESC
```

### 21. « Taux de satisfaction des usagers pour l'Agence Korhogo en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : satisfaction_rate par agency
```sql
SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 END) * 100.0) / NULLIF(COUNT(CASE WHEN c.status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' GROUP BY sp.libelle ORDER BY satisfaction_rate DESC
```

### 22. « Top 3 des motifs de dénonciations enregistrées en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count par object
```sql
SELECT o.libelle AS object, COUNT(CASE WHEN c.claim_type IN ('DENUNCIATION', 'DENUNCIACION') THEN 1 END) AS denonciation_count FROM reporting_claim c LEFT JOIN reporting_objet o ON c.objet_id = o.id WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' GROUP BY o.libelle ORDER BY denonciation_count DESC
```

### 23. « Taux de respect des délais SLA pour les dossiers de niveau de risque moyen »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c WHERE c.risk_level = 'MOYEN' AND c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION')
```

### 24. « Classement des agences par volume total de réclamations traitées »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_service_point sp LEFT JOIN reporting_claim c ON c.service_point_id = sp.id GROUP BY sp.libelle ORDER BY reclamation_count DESC;
```
