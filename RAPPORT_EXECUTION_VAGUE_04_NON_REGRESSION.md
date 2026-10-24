# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné

**Date d'exécution** : 2026-10-17 00:28:30 UTC  
**Nombre de questions traitées** : 24  

## Synthèse des Résultats

| N° | Question | Statut | Mode | Query ID | Durée | SQL Exécuté |
|---|---|---|---|---|---|---|
| 1 | Quels sont les dossiers en cours qui ne sont toujours pas résolus ? | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-B808C8D1` | 159284.0 ms | `WITH claim_cnt AS ( SELECT COUNT(*) AS cnt FROM reporting_cl...` |
| 2 | Réclamations des clients mécontents reçues hors agence physique | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-F9B17B7E` | 43165.24 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 3 | Nombre de dossiers critiques ou graves en attente de traitement | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-9623DED2` | 45808.3 ms | `SELECT COUNT(*) AS severe_plainte_count FROM reporting_claim...` |
| 4 | Taux de respect des délais pour les réclamations de niveau critique en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-25BAB115` | 30469.82 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 5 | Signalements de fraudes et irrégularités enregistrés sans passer par le guichet | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-4AF84FE9` | 39026.07 ms | `SELECT COUNT(*) AS denonciation_count FROM reporting_claim c...` |
| 6 | Délai moyen de résolution des dossiers traités pour les clients insatisfaits | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-27696ED6` | 29411.11 ms | `SELECT AVG(DATEDIFF(resolved_at, receipt_at)) AS avg_process...` |
| 7 | Total des réclamations reçues sur le canal téléphonique au cours de l'été 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-37BC3E65` | 62178.23 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 8 | Propositions d'amélioration et suggestions enregistrées en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-5A5A40C8` | 30995.22 ms | `SELECT COUNT(*) AS suggestion_count FROM reporting_suggestio...` |
| 9 | Taux de satisfaction des usagers pour les dossiers résolus hors délai | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-82150224` | 46834.54 ms | `SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THE...` |
| 10 | Dossiers de réclamations mineures enregistrés pour l'Agence Bouaké | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-7651B154` | 35718.96 ms | `SELECT COUNT(*) AS reclamation_count FROM reporting_claim c ...` |
| 11 | Pourcentage de respect des SLA pour les signalements graves en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-93EA9045` | 42315.81 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 12 | Nombre de réclamations ouvertes et non clôturées à ce jour en 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-D82B0457` | 27219.95 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 13 | Répartition des dossiers mécontents par motif au troisième trimestre 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-D7A172B2` | 61361.24 ms | `WITH claim_counts AS ( SELECT ob.id AS objet_id, COUNT(*) AS...` |
| 14 | Taux de respect des engagements de délai pour l'Agence Korhogo en 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-8748240C` | 41565.34 ms | `SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resol...` |
| 15 | Nombre de dénonciations anonymes ou signalements traités en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-E7ACE72F` | 45540.65 ms | `SELECT COUNT(CASE WHEN `c`.`claim_type` IN ('DENUNCIATION','...` |
| 16 | Dossiers urgents transmis via le canal web en septembre 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-2ED7041A` | 92695.99 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim c JOIN reporti...` |
| 17 | Taux de satisfaction des clients ayant déposé une plainte via le téléphone | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-6522B720` | 104988.5 ms | `SELECT ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 ...` |
| 18 | Réclamations traitées avec succès avant échéance pour l'Agence Abidjan | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-5A882C7A` | 35286.58 ms | `SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND...` |
| 19 | Délai moyen de clôture des dossiers de réclamation en septembre 2026 | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-91832FA0` | 22208.56 ms | `SELECT AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_pro...` |
| 20 | Nombre total de doléances clients enregistrées sur toute l'année 2026 | ✅ Succès | `FAST_PATH_HOMOLOGATED` | `QC-UNIFIED-PLAINTES-TOTAL` | 24661.78 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_...` |
| 21 | Taux de respect SLA pour les réclamations reçues par voie digitale en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-D3989EB9` | 46550.31 ms | `SELECT cc.libelle AS channel, ROUND((COUNT(CASE WHEN (c.reso...` |
| 22 | Dossiers avec niveau de risque moyen clôturés avec satisfaction | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-040EC5A8` | 61298.62 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE risk_lev...` |
| 23 | Proportion de réclamations respectant le délai imparti par canal en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-FAC5C542` | 67290.59 ms | `SELECT cc.libelle AS channel, ROUND( (COUNT(CASE WHEN (c.res...` |
| 24 | Volume global de dossiers de réclamation non satisfaits en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-20F38EFB` | 143495.44 ms | `SELECT COUNT(c.id) AS case_count FROM reporting_claim c WHER...` |

## Détail des Réponses formulées

### 1. « Quels sont les dossiers en cours qui ne sont toujours pas résolus ? »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
WITH claim_cnt AS (
    SELECT COUNT(*) AS cnt
    FROM reporting_claim
    WHERE claim_type IN ('CLAIM', 'DENUNCIATION')
      AND status != 'SATISFIED'
), sugg_cnt AS (
    SELECT COUNT(*) AS cnt
    FROM reporting_suggestion
    WHERE status != 'SATISFIED'
)
SELECT (claim_cnt.cnt + sugg_cnt.cnt) AS plainte_count
FROM claim_cnt, sugg_cnt;
```

### 2. « Réclamations des clients mécontents reçues hors agence physique »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
FROM `reporting_claim` c
LEFT JOIN `reporting_collection_channel` cc ON c.collection_channel_id = cc.id
WHERE c.satisfaction_status = 'UNSATISFIED'
  AND cc.libelle NOT IN ('AGENCE','Physique');
```

### 3. « Nombre de dossiers critiques ou graves en attente de traitement »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : severe_plainte_count
```sql
SELECT COUNT(*) AS severe_plainte_count FROM reporting_claim WHERE risk_level = 'GRAVE' AND status != 'SATISFIED';
```

### 4. « Taux de respect des délais pour les réclamations de niveau critique en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'GRAVE' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00';
```

### 5. « Signalements de fraudes et irrégularités enregistrés sans passer par le guichet »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count
```sql
SELECT COUNT(*) AS denonciation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel ch ON c.collection_channel_id = ch.id WHERE c.claim_type IN ('DENUNCIATION','DENUNCIACION') AND ch.libelle NOT IN ('AGENCE','Physique')
```

### 6. « Délai moyen de résolution des dossiers traités pour les clients insatisfaits »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : avg_processing_time
```sql
SELECT AVG(DATEDIFF(resolved_at, receipt_at)) AS avg_processing_time FROM reporting_claim WHERE claim_type IN ('CLAIM', 'DENUNCIATION', 'SUGGESTION') AND status = 'UNSATISFIED' AND risk_level = 'MOYEN' ORDER BY avg_processing_time DESC
```

### 7. « Total des réclamations reçues sur le canal téléphonique au cours de l'été 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel ch ON c.collection_channel_id = ch.id WHERE ch.libelle = 'TELEPHONE' AND c.claim_type = 'CLAIM' AND c.receipt_at >= '2026-06-01 00:00:00' AND c.receipt_at <= '2026-08-31 00:00:00' ORDER BY reclamation_count DESC
```

### 8. « Propositions d'amélioration et suggestions enregistrées en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count
```sql
SELECT COUNT(*) AS suggestion_count FROM reporting_suggestion WHERE recorded_at >= '2026-01-01 00:00:00' AND recorded_at < '2027-01-01 00:00:00'
```

### 9. « Taux de satisfaction des usagers pour les dossiers résolus hors délai »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : custom_satisfaction_rate_delayed
```sql
SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 1.0 ELSE 0 END) AS custom_satisfaction_rate_delayed FROM reporting_claim c WHERE c.resolved_at > c.sla_due_at AND c.resolved_at IS NOT NULL AND c.sla_due_at IS NOT NULL
```

### 10. « Dossiers de réclamations mineures enregistrés pour l'Agence Bouaké »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(*) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MINEUR' AND sp.libelle = 'Bouaké' ORDER BY reclamation_count DESC
```

### 11. « Pourcentage de respect des SLA pour les signalements graves en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate
FROM reporting_claim c
WHERE c.claim_type = 'DENUNCIATION'
  AND c.risk_level = 'GRAVE'
  AND c.receipt_at >= '2026-01-01 00:00:00'
  AND c.receipt_at < '2027-01-01 00:00:00';
```

### 12. « Nombre de réclamations ouvertes et non clôturées à ce jour en 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c WHERE c.receipt_at BETWEEN '2026-01-01 00:00:00' AND '2026-10-17 00:00:00' AND c.status <> 'SATISFIED' AND c.claim_type = 'CLAIM'
```

### 13. « Répartition des dossiers mécontents par motif au troisième trimestre 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count par object
```sql
WITH claim_counts AS (
  SELECT ob.id AS objet_id, COUNT(*) AS cnt
  FROM reporting_claim c
  JOIN reporting_objet ob ON c.objet_id = ob.id
  WHERE c.satisfaction_status = 'UNSATISFIED'
    AND c.receipt_at >= '2026-07-01 00:00:00' AND c.receipt_at < '2026-09-30 00:00:00'
  GROUP BY ob.id
),
suggestion_counts AS (
  SELECT ob.id AS objet_id, COUNT(*) AS cnt
  FROM reporting_suggestion s
  JOIN reporting_objet ob ON s.objet_id = ob.id
  WHERE s.status = 'UNSATISFIED'
    AND s.recorded_at >= '2026-07-01 00:00:00' AND s.recorded_at < '2026-09-30 00:00:00'
  GROUP BY ob.id
)
SELECT ob.libelle AS object, SUM(c.cnt) AS plainte_count
FROM (
  SELECT objet_id, cnt FROM claim_counts
  UNION ALL
  SELECT objet_id, cnt FROM suggestion_counts
) c
JOIN reporting_objet ob ON c.objet_id = ob.id
GROUP BY ob.libelle
ORDER BY plainte_count DESC;
```

### 14. « Taux de respect des engagements de délai pour l'Agence Korhogo en 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : sla_adherence_rate par agency
```sql
SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' AND c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY sp.libelle ORDER BY sla_adherence_rate DESC
```

### 15. « Nombre de dénonciations anonymes ou signalements traités en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count
```sql
SELECT COUNT(CASE WHEN `c`.`claim_type` IN ('DENUNCIATION','DENUNCIACION') THEN 1 END) AS `denonciation_count` FROM `reporting_claim` AS `c` WHERE `c`.`receipt_at` >= '2026-01-01 00:00:00' AND `c`.`receipt_at` < '2027-01-01 00:00:00';
```

### 16. « Dossiers urgents transmis via le canal web en septembre 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim c JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.risk_level = 'GRAVE' AND cc.libelle = 'WEB' AND c.receipt_at >= '2026-09-01 00:00:00' AND c.receipt_at < '2026-09-30 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion s JOIN reporting_collection_channel cc2 ON s.collection_channel_id = cc2.id WHERE cc2.libelle = 'WEB' AND s.recorded_at >= '2026-09-01 00:00:00' AND s.recorded_at < '2026-09-30 00:00:00')) AS plainte_count
```

### 17. « Taux de satisfaction des clients ayant déposé une plainte via le téléphone »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : satisfaction_rate
```sql
SELECT ROUND((COUNT(CASE WHEN c.status = 'SATISFIED' THEN 1 END) * 100.0) / NULLIF(COUNT(CASE WHEN c.status IN ('SATISFIED', 'UNSATISFIED') THEN 1 END), 0), 2) AS satisfaction_rate FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE cc.libelle = 'TELEPHONE' AND c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION');
```

### 18. « Réclamations traitées avec succès avant échéance pour l'Agence Abidjan »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate
```sql
SELECT ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND sp.libelle = 'Abidjan';
```

### 19. « Délai moyen de clôture des dossiers de réclamation en septembre 2026 »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : avg_processing_time
```sql
SELECT AVG(DATEDIFF(c.resolved_at, c.receipt_at)) AS avg_processing_time FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MOYEN' AND c.status = 'SATISFIED' AND c.receipt_at >= '2026-09-01 00:00:00' AND c.receipt_at < '2026-09-30 00:00:00'
```

### 20. « Nombre total de doléances clients enregistrées sur toute l'année 2026 »
- **Mode** : `FAST_PATH_HOMOLOGATED`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= '2026-01-01 00:00:00' AND receipt_at < '2027-01-01 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= '2026-01-01 00:00:00' AND recorded_at < '2027-01-01 00:00:00')) AS plainte_count
```

### 21. « Taux de respect SLA pour les réclamations reçues par voie digitale en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate par channel
```sql
SELECT cc.libelle AS channel,
       ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate
FROM reporting_claim c
LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id
WHERE c.claim_type = 'CLAIM'
  AND c.receipt_at >= '2026-01-01 00:00:00'
  AND c.receipt_at < '2027-01-01 00:00:00'
  AND cc.libelle NOT IN ('AGENCE', 'Physique')
GROUP BY cc.libelle
ORDER BY sla_adherence_rate DESC;
```

### 22. « Dossiers avec niveau de risque moyen clôturés avec satisfaction »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE risk_level = 'MOYEN' AND status = 'SATISFIED') + (SELECT COUNT(*) FROM reporting_suggestion WHERE 1 = 0)) AS plainte_count
```

### 23. « Proportion de réclamations respectant le délai imparti par canal en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate par channel
```sql
SELECT
  cc.libelle AS channel,
  ROUND(
    (COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0)
    / NULLIF(COUNT(*), 0)
  , 2) AS sla_adherence_rate
FROM reporting_claim c
LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id
WHERE c.claim_type = 'CLAIM'
  AND c.receipt_at >= '2026-01-01 00:00:00'
  AND c.receipt_at < '2027-01-01 00:00:00'
GROUP BY cc.libelle
ORDER BY sla_adherence_rate DESC;
```

### 24. « Volume global de dossiers de réclamation non satisfaits en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(c.id) AS case_count FROM reporting_claim c  WHERE c.claim_type = 'CLAIM' AND c.satisfaction_status = 'UNSATISFIED' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00'
```
