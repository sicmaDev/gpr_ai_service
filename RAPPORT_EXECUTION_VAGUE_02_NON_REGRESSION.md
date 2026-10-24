# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné

**Date d'exécution** : 2026-10-16 23:26:45 UTC  
**Nombre de questions traitées** : 24  

## Synthèse des Résultats

| N° | Question | Statut | Mode | Query ID | Durée | SQL Exécuté |
|---|---|---|---|---|---|---|
| 1 | Nombre de réclamations en cours au premier trimestre 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-D82B0457` | 84641.42 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 2 | Réclamations graves reçues en mars 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-C22BE3ED` | 42993.69 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 3 | Dossiers de réclamation par agence pour le canal Guichet | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-E912E503` | 32859.26 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type = ...` |
| 4 | Répartition des réclamations par catégorie de produit en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-5C04D32B` | 45800.58 ms | `SELECT p.libelle AS product, COUNT(CASE WHEN c.claim_type = ...` |
| 5 | Nombre de réclamations traitées et satisfaites par agence | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-CFC120FE` | 20804.14 ms | `SELECT sp.libelle AS agency, COUNT(*) AS reclamation_count F...` |
| 6 | Réclamations urgentes ou critiques de l'Agence Littoral | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-B4DA9AAA` | 23250.52 ms | `SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS...` |
| 7 | Volume de dénonciations par statut en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-61FAAE41` | 23096.78 ms | `SELECT c.status AS status, COUNT(*) AS denonciation_count FR...` |
| 8 | Suggestions d'amélioration adoptées par catégorie d'impact | ✅ Succès | `GENERATIVE_LLM` | `-` | 29959.39 ms | `SELECT s.impact_level AS impact_level, COUNT(*) AS custom_ad...` |
| 9 | Réclamations reçues entre le 01/01/2026 et le 30/06/2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-03373507` | 105820.53 ms | `SELECT COUNT(*) AS reclamation_count FROM reporting_claim WH...` |
| 10 | Nombre de dossiers en souffrance ou en cours par agence | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-5F128CF6` | 38946.14 ms | `SELECT sp.libelle AS agency, COUNT(*) AS plainte_count FROM ...` |
| 11 | Réclamations par agence avec statut CLOTURE | ✅ Succès | `CANDIDATE_PENDING` | `QC-PEND-CFC120FE` | 21677.15 ms | `SELECT sp.libelle AS agency, COUNT(*) AS reclamation_count F...` |
| 12 | Doléances par canal de collecte pour les réclamations moyennes | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-9431903D` | 23874.05 ms | `SELECT cc.libelle AS channel, COUNT(c.id) AS custom_avg_recl...` |
| 13 | Suggestions selon le statut au premier semestre 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-35099CED` | 40540.59 ms | `SELECT s.status AS status, COUNT(s.id) AS suggestion_count F...` |
| 14 | Nombre de réclamations graves par canal en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-25286439` | 53035.83 ms | `SELECT cc.libelle AS channel, COUNT(CASE WHEN c.risk_level =...` |
| 15 | Dénonciations selon le niveau de risque en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-EC9917EF` | 24887.89 ms | `SELECT c.risk_level AS risk_level, COUNT(*) AS denonciation_...` |
| 16 | Réclamations non satisfaites par agence | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-BAB83689` | 52278.32 ms | `SELECT sp.libelle AS agency, COUNT(*) AS reclamation_count F...` |
| 17 | Volume de dossiers reçus par le canal Mobile en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-5E96BF13` | 43367.44 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim c JOIN reporti...` |
| 18 | Plaintes avec statut AFFECTED au premier trimestre 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-0E4E11EF` | 35808.63 ms | `SELECT ((SELECT COUNT(*) FROM reporting_claim c WHERE c.stat...` |
| 19 | Nombre de litiges par objet et par agence | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-942DEC20` | 56614.5 ms | `SELECT COALESCE(o.libelle, 'N/A') AS object, COALESCE(sp.lib...` |
| 20 | Suggestions par canal de collecte | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-93F0BFC8` | 18862.86 ms | `SELECT cc.libelle AS channel, COUNT(s.id) AS suggestion_coun...` |
| 21 | Réclamations fermées ou résolues en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-8851DAA6` | 24061.71 ms | `SELECT COUNT(*) AS reclamation_count FROM reporting_claim c ...` |
| 22 | Dénonciations enregistrées par l'Agence Atlantique | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-29944692` | 54667.01 ms | `SELECT sp.libelle AS agency, COUNT(CASE WHEN c.claim_type IN...` |
| 23 | Réclamations mineures reçues en février 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-22E5488E` | 32600.34 ms | `SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS r...` |
| 24 | Taux de respect SLA par agence en 2026 | ✅ Succès | `GENERATIVE_LLM` | `QC-PEND-8748240C` | 45132.04 ms | `SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resol...` |

## Détail des Réponses formulées

### 1. « Nombre de réclamations en cours au premier trimestre 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c WHERE c.receipt_at BETWEEN '2026-01-01 00:00:00' AND '2026-03-31 00:00:00' AND c.status <> 'SATISFIED' AND c.claim_type = 'CLAIM'
```

### 2. « Réclamations graves reçues en mars 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim c WHERE c.risk_level = 'GRAVE' AND c.receipt_at >= '2026-03-01 00:00:00' AND c.receipt_at < '2026-03-31 00:00:00' ORDER BY reclamation_count DESC
```

### 3. « Dossiers de réclamation par agence pour le canal Guichet »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency,
       COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
FROM reporting_claim c
LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id
LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id
WHERE cc.libelle = 'AGENCE'
GROUP BY sp.libelle
ORDER BY reclamation_count DESC;
```

### 4. « Répartition des réclamations par catégorie de produit en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par product
```sql
SELECT p.libelle AS product,
       COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
FROM reporting_claim c
LEFT JOIN reporting_product p ON c.product_id = p.id
WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00'
GROUP BY p.libelle
ORDER BY reclamation_count DESC;
```

### 5. « Nombre de réclamations traitées et satisfaites par agence »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(*) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.status = 'SATISFIED' GROUP BY sp.libelle ORDER BY reclamation_count DESC;
```

### 6. « Réclamations urgentes ou critiques de l'Agence Littoral »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN c.claim_type = 'CLAIM' THEN 1 END) AS reclamation_count
FROM `reporting_claim` AS c
LEFT JOIN `reporting_service_point` AS sp ON c.service_point_id = sp.id
WHERE c.risk_level = 'GRAVE'
  AND sp.libelle = 'Littoral'
  AND c.claim_type = 'CLAIM';
```

### 7. « Volume de dénonciations par statut en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count par status
```sql
SELECT c.status AS status,
       COUNT(*) AS denonciation_count
FROM reporting_claim c
WHERE c.claim_type IN ('DENUNCIATION','DENUNCIACION')
  AND c.receipt_at >= '2026-01-01 00:00:00'
  AND c.receipt_at < '2027-01-01 00:00:00'
GROUP BY c.status
ORDER BY denonciation_count DESC;
```

### 8. « Suggestions d'amélioration adoptées par catégorie d'impact »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : Erreur d'exécution SQL
```sql
SELECT s.impact_level AS impact_level, COUNT(*) AS custom_adopted_suggestion_count FROM reporting_suggestion s WHERE s.status = :status GROUP BY s.impact_level ORDER BY custom_adopted_suggestion_count DESC
```

### 9. « Réclamations reçues entre le 01/01/2026 et le 30/06/2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(*) AS reclamation_count FROM reporting_claim WHERE claim_type = 'CLAIM' AND receipt_at >= '2026-01-01 00:00:00' AND receipt_at < '2026-06-30 00:00:00' ORDER BY reclamation_count DESC;
```

### 10. « Nombre de dossiers en souffrance ou en cours par agence »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(*) AS plainte_count FROM (SELECT service_point_id FROM reporting_claim WHERE status != 'SATISFIED' UNION ALL SELECT service_point_id FROM reporting_suggestion WHERE status != 'SATISFIED') u LEFT JOIN reporting_service_point sp ON u.service_point_id = sp.id GROUP BY sp.libelle ORDER BY plainte_count DESC;
```

### 11. « Réclamations par agence avec statut CLOTURE »
- **Mode** : `CANDIDATE_PENDING`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(*) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.status = 'SATISFIED' GROUP BY sp.libelle ORDER BY reclamation_count DESC;
```

### 12. « Doléances par canal de collecte pour les réclamations moyennes »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : custom_avg_reclamation_count par channel
```sql
SELECT cc.libelle AS channel, COUNT(c.id) AS custom_avg_reclamation_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.claim_type = 'CLAIM' AND c.risk_level = 'MOYEN' GROUP BY cc.libelle ORDER BY custom_avg_reclamation_count DESC;
```

### 13. « Suggestions selon le statut au premier semestre 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count par status
```sql
SELECT s.status AS status, COUNT(s.id) AS suggestion_count FROM reporting_suggestion s WHERE s.recorded_at >= '2026-01-01 00:00:00' AND s.recorded_at < '2026-06-30 00:00:00' GROUP BY s.status ORDER BY suggestion_count DESC;
```

### 14. « Nombre de réclamations graves par canal en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : severe_plainte_count par channel
```sql
SELECT cc.libelle AS channel,
       COUNT(CASE WHEN c.risk_level = 'GRAVE' THEN 1 END) AS severe_plainte_count
FROM reporting_claim c
LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id
WHERE c.claim_type = 'CLAIM'
  AND c.receipt_at >= '2026-01-01 00:00:00'
  AND c.receipt_at < '2027-01-01 00:00:00'
GROUP BY cc.libelle
ORDER BY severe_plainte_count DESC;
```

### 15. « Dénonciations selon le niveau de risque en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count par risk_level
```sql
SELECT c.risk_level AS risk_level, COUNT(*) AS denonciation_count FROM reporting_claim c WHERE c.claim_type IN ('DENUNCIATION','DENUNCIACION') AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' GROUP BY c.risk_level ORDER BY denonciation_count DESC;
```

### 16. « Réclamations non satisfaites par agence »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count par agency
```sql
SELECT sp.libelle AS agency, COUNT(*) AS reclamation_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.status != 'SATISFIED' GROUP BY sp.libelle ORDER BY reclamation_count DESC;
```

### 17. « Volume de dossiers reçus par le canal Mobile en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim c JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE cc.libelle = 'MOBILE' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion s JOIN reporting_collection_channel cc2 ON s.collection_channel_id = cc2.id WHERE cc2.libelle = 'MOBILE' AND s.recorded_at >= '2026-01-01 00:00:00' AND s.recorded_at < '2027-01-01 00:00:00')) AS plainte_count
```

### 18. « Plaintes avec statut AFFECTED au premier trimestre 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count
```sql
SELECT ((SELECT COUNT(*) FROM reporting_claim c WHERE c.status = 'AFFECTED' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2026-03-31 00:00:00') + (SELECT COUNT(*) FROM reporting_suggestion s WHERE s.status = 'AFFECTED' AND s.recorded_at >= '2026-01-01 00:00:00' AND s.recorded_at < '2026-03-31 00:00:00')) AS plainte_count
```

### 19. « Nombre de litiges par objet et par agence »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : plainte_count par object
```sql
SELECT COALESCE(o.libelle, 'N/A') AS object, COALESCE(sp.libelle, 'N/A') AS agency, COUNT(*) AS plainte_count FROM (SELECT c.objet_id AS objet_id, c.service_point_id AS service_point_id FROM reporting_claim c UNION ALL SELECT s.objet_id AS objet_id, s.service_point_id AS service_point_id FROM reporting_suggestion s) u LEFT JOIN reporting_objet o ON o.id = u.objet_id LEFT JOIN reporting_service_point sp ON sp.id = u.service_point_id GROUP BY o.libelle, sp.libelle ORDER BY plainte_count DESC;
```

### 20. « Suggestions par canal de collecte »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : suggestion_count par channel
```sql
SELECT cc.libelle AS channel, COUNT(s.id) AS suggestion_count FROM reporting_suggestion s LEFT JOIN reporting_collection_channel cc ON s.collection_channel_id = cc.id GROUP BY cc.libelle ORDER BY suggestion_count DESC;
```

### 21. « Réclamations fermées ou résolues en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(*) AS reclamation_count FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.status = 'SATISFIED' AND c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00';
```

### 22. « Dénonciations enregistrées par l'Agence Atlantique »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : denonciation_count par agency
```sql
SELECT sp.libelle AS agency,
       COUNT(CASE WHEN c.claim_type IN ('DENUNCIATION','DENUNCIACION') THEN 1 END) AS denonciation_count
FROM reporting_claim c
LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id
WHERE sp.libelle = 'Agence Atlantique'
GROUP BY sp.libelle
ORDER BY denonciation_count DESC;
```

### 23. « Réclamations mineures reçues en février 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : reclamation_count
```sql
SELECT COUNT(CASE WHEN claim_type = 'CLAIM' THEN 1 END) AS reclamation_count FROM reporting_claim WHERE risk_level = 'MINEUR' AND receipt_at >= '2026-02-01 00:00:00' AND receipt_at < '2026-02-28 00:00:00';
```

### 24. « Taux de respect SLA par agence en 2026 »
- **Mode** : `GENERATIVE_LLM`
- **Synthèse** : sla_adherence_rate par agency
```sql
SELECT sp.libelle AS agency, ROUND((COUNT(CASE WHEN (c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_due_at) OR (c.resolved_at IS NULL AND c.sla_due_at >= NOW()) THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS sla_adherence_rate FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.receipt_at >= '2026-01-01 00:00:00' AND c.receipt_at < '2027-01-01 00:00:00' AND c.claim_type IN ('CLAIM','DENUNCIATION','SUGGESTION') GROUP BY sp.libelle ORDER BY sla_adherence_rate DESC
```
