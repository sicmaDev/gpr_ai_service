# Plan d'Implémentation : Synchronisation Opérationnelle et Oracles Multi-Vagues

> **Méthodologie** : `safe-code-change` (Sanctuarisation des acquis, minimalisme, non-régression stricte).  
> **Date de rédaction** : 16 Octobre 2026  
> **Composants cibles** :
> - Backend Java Spring Boot : `gpr_server_sicma_new_version`
> - Micro-service IA Python : `gpr_ai_service`
> - Base de données analytique : MariaDB `gpr_ai_reporting`

---

## 1. Contexte et Objectifs

Suite aux audits forensiques et aux améliorations validées sur le moteur de reporting Text-to-SQL Gouverné, deux chantiers structurants doivent être menés :

1. **Généralisation des Oracles et Scorecards Multi-Vagues** : Étendre le système d'évaluation sur 8 axes aux 4 vagues de questions historiques (Vagues 01, 02, 03 et 04) avec des oracles de vérité terrain vérifiés.
2. **Mise à niveau de la Synchronisation ETL (Java $\rightarrow$ MariaDB)** : Combler les 4 écarts majeurs identifiés entre le flux opérationnel Spring Boot et le lac de données analytique (ingestion des suggestions, clés étrangères, historique d'affectation et planificateur autonome).

---

## 2. Volet 1 : Oracles de Vérité Terrain et Évaluation Multi-Vagues

### 2.1. Analyse Comparative des 4 Vagues d'Évaluation

Chaque vague interroge 24 questions analytiques selon une complexité graduelle :

| Vague | Périmètre Fonctionnel | Rôle dans l'Homologation | Fichier Source |
| :--- | :--- | :--- | :--- |
| **Vague 01** | **Fondations & Granularités** | Mesure la fidélité sur les requêtes simples : comptages élémentaires, détection unifiée des 3 entités (`CLAIM`, `DENUNCIATION`, `SUGGESTION`). | `questions_vague_01_20261015_095606.txt` |
| **Vague 02** | **Filtres Combinatoires** | Évalue la robustesse sur les fenêtres temporelles (trimestres, mois), les niveaux de risque (`MINEUR`, `MOYEN`, `GRAVE`) et croisements agence/canal. | `questions_vague_02_20261015_192500.txt` |
| **Vague 03** | **Agrégations Avancées & Ratios** | Valide les calculs complexes : Taux de respect SLA, Délais moyens de traitement, Tops agences et classements ordonnés. | `questions_vague_03_20261015_211523.txt` |
| **Vague 04** | **Cas Limites & Gouvernance** | Évalue les pièges métier : Dossiers en cours (`status != 'SATISFIED'`), canaux sans guichet, suggestions 2026 et satisfaction sur avis exprimés. | `questions_vague_04_20261015_214111.txt` |

### 2.2. Livrables Oracles à Produire

Généralisation du script `scripts/generate_ground_truth_oracle.py` pour produire les 4 fixtures standardisées :
- `tests/fixtures/ground_truth_vague_01.json`
- `tests/fixtures/ground_truth_vague_02.json`
- `tests/fixtures/ground_truth_vague_03.json`
- `tests/fixtures/ground_truth_vague_04.json` *(déjà finalisé et validé)*

Le moteur `tools/evaluate_wave_quality.py` prendra en charge l'évaluation comparative instantanée :
```bash
python tools/evaluate_wave_quality.py --audit <chemin_audit.json> --oracle tests/fixtures/ground_truth_vague_01.json --wave-name "Vague 01"
```

---

## 3. Volet 2 : Diagnostic de la Synchronisation Actuelle

### 3.1. État Actuel du Flux ETL

L'état persisté dans la table `reporting_sync_state` de MariaDB indique :
- **Dernier sync réussi** : `2026-09-26 00:24:10` (curseur : `2026-09-23 10:04:05`).
- **Volume traité** : 46 dossiers reçus (0 insérés, 39 mis à jour).
- **Statut opérationnel** : Actuellement en pause (serveur Java 8020 non démarré en local ; Cron désactivé en mode `development`).

### 3.2. Matrice des Écarts Identifiés

| Composant | État Actuel | Exigence Cible | Impact Métier |
| :--- | :--- | :--- | :--- |
| **Suggestions** | Aucun flux d'export Java (`findReportingClaims` uniquement). Table `reporting_suggestion` non alimentée par l'ETL. | Endpoint Java `/export-suggestions` + ingestion Python dans `reporting_suggestion`. | Les requêtes unifiées sur les suggestions dépendent d'insertions manuelles. |
| **Clés Étrangères (IDs)** | L'export Java n'envoie que des libellés (`produit_service`, `point_service_indexe`). Les colonnes `objet_id`, `product_id`, `service_point_id`, `collection_channel_id` restent `NULL`. | Transmission des identifiants techniques dans `ExportClaimDto` et mapping direct en base. | Impossibilité d'effectuer des jointures relationnelles normalisées strictes. |
| **Réaffectations** | Aucune réplication de la table `reporting_historique_affectations`. | Export des transferts de dossiers entre agents. | La métrique `reaffectation_count` ne peut pas être alimentée depuis le système source. |
| **Date de Résolution** | Le champ `resolved_at` n'est pas transmis par le backend Java. | Renseignement de `resolved_at` dès qu'un dossier atteint le statut `SATISFIED`. | Calculs d'adhérence SLA et de durée de cycle basés sur des dates estimées. |
| **Planificateur Cron** | APScheduler conditionné strictement à `APP_ENV=production`. Inactif en environnement local de qualification. | Paramétrage via `REPORTING_ENABLE_SCHEDULER=true`. | Les environnements de recette et démo ne synchronisent pas automatiquement. |

---

## 4. Plan d'Implémentation Détaillé (`safe-code-change`)

### Phase 1 : Backend Java Spring Boot (`gpr_server_sicma_new_version`)

#### 1.1. Enrichissement du DTO des Réclamations
- **Fichier** : `src/main/java/com/sicmagroup/gpr/domain/dto/ai/ExportClaimDto.java`
- **Actions** :
  - Ajouter les champs optionnels :
    ```java
    private Long objetId;
    private Long productId;
    private Long servicePointId;
    private Long collectionChannelId;
    private Long collectorId;
    private LocalDateTime resolvedAt;
    ```
- **Garantie rétro-compatibilité** : Tous les champs existants sont préservés ; les consommateurs existants ne subissent aucune régression.

#### 1.2. DTO et Réponse d'Export des Suggestions
- **Fichiers à créer** :
  - `src/main/java/com/sicmagroup/gpr/domain/dto/ai/ExportSuggestionDto.java`
  - `src/main/java/com/sicmagroup/gpr/domain/dto/ai/ExportSuggestionsResponse.java`
- **Champs exposés** :
  - `id`, `code`, `codeClient`, `clientFirstAndLastName`, `content`, `status`, `canal` (libellé + id), `serviceIndexe` (libellé + id), `produit` (libellé + id), `collecteur` (id), `receiptDateTime`, `createdAt`, `updatedAt`.

#### 1.3. Requête Paginée dans `SuggestionRepository`
- **Fichier** : `src/main/java/com/sicmagroup/gpr/repository/SuggestionRepository.java`
- **Signature** :
  ```java
  @Query("SELECT s FROM Suggestion s WHERE (:updatedAfter IS NULL OR s.updatedAt > :updatedAfter)")
  Page<Suggestion> findReportingSuggestions(@Param("updatedAfter") LocalDateTime updatedAfter, Pageable pageable);
  ```

#### 1.4. Contrôleur REST `AiController.java`
- **Fichier** : `src/main/java/com/sicmagroup/gpr/api/ai/AiController.java`
- **Actions** :
  - Enrichir `toExportDto()` pour mapper les identifiants techniques et `resolvedAt`.
  - Ajouter l'endpoint `@GetMapping("/export-suggestions")` avec pagination (`page`, `size` max 1000) et curseur `updatedAfter`.

---

### Phase 2 : Pipeline ETL Python (`gpr_ai_service`)

#### 2.1. Mapping des Identifiants Techniques dans `claim_values()`
- **Fichier** : `app/services/sync_service.py`
- **Actions** :
  - Récupérer les nouveaux champs :
    ```python
    "objet_id": row.get("objetId"),
    "product_id": row.get("productId"),
    "service_point_id": row.get("servicePointId"),
    "collection_channel_id": row.get("collectionChannelId"),
    "collector_id": row.get("collectorId"),
    "resolved_at": parse_source_datetime(row.get("resolvedAt")),
    ```
  - Fallback gracieux si absent (rétro-compatibilité avec les versions antérieures de l'export).

#### 2.2. Ingestion des Suggestions (`sync_suggestions`)
- **Fichier** : `app/services/sync_service.py`
- **Nouvelles fonctions** :
  - `suggestion_values(row: dict, synced_at: datetime) -> dict` : Normalisation vers `ReportingSuggestion`.
  - `upsert_suggestions_with_metrics(db, rows, synced_at) -> dict` : Upsert incrémental par `source_suggestion_id`.
  - `fetch_suggestion_pages(session, updated_after) -> list` : Appel paginé vers `/api/v1/ai/export-suggestions`.
  - `perform_sync_suggestions(db, http_session, full=False) -> dict` : Orchestration avec curseur dédié `spring_boot_suggestions`.

#### 2.3. Orchestration Unifiée
- **Fonction** : `perform_sync(db, target="all", full=False)`
  - `target="claims"` : Uniquement réclamations.
  - `target="suggestions"` : Uniquement suggestions.
  - `target="all"` : Exécution séquentielle des deux flux avec commit transactionnel distinct.

---

### Phase 3 : Exposition API FastAPI et Ordonnanceur

#### 3.1. Routeur de Synchronisation
- **Fichier** : `app/routers/sync.py`
- **Actions** :
  - Enrichir `GET /sync/status` pour retourner le bloc complet `"suggestions"` aux côtés de `"claims"` :
    - `last_sync_at`, `last_cursor`, `received_count`, `inserted_count`, `updated_count`, `error_count`.

#### 3.2. Planificateur Configurable (`main.py`)
- **Fichier** : `main.py`
- **Actions** :
  - Assouplir la condition de démarrage du scheduler :
    ```python
    ENABLE_SCHEDULER = IS_DEPLOYMENT or os.getenv("REPORTING_ENABLE_SCHEDULER", "false").lower() == "true"
    if ENABLE_SCHEDULER:
        scheduler = BackgroundScheduler()
        scheduler.add_job(lambda: perform_sync(target="all"), 'cron', hour=2, minute=0)
        scheduler.start()
    ```
  - Mettre à jour l'endpoint `GET /sync` avec le paramètre `target: str = "all"`.

---

### Phase 4 : Oracles de Vérité Terrain (Vagues 01, 02 et 03)

#### 4.1. Extension du Générateur d'Oracles
- **Fichier** : `scripts/generate_ground_truth_oracle.py`
- **Paramétrage CLI** :
  ```bash
  python scripts/generate_ground_truth_oracle.py --wave 1 --output tests/fixtures/ground_truth_vague_01.json
  python scripts/generate_ground_truth_oracle.py --wave 2 --output tests/fixtures/ground_truth_vague_02.json
  python scripts/generate_ground_truth_oracle.py --wave 3 --output tests/fixtures/ground_truth_vague_03.json
  ```
- **Validation** : Vérification manuelle des formules SQL et des totaux attendus contre MariaDB.

---

### Phase 5 : Protocole de Validation et Non-Régression

1. **Tests Unitaires Ciblés** :
   - Enrichir `tests/test_reporting_sync.py` :
     - `test_claim_values_maps_foreign_key_ids` : Vérifie la capture de `objetId`, `productId`, etc.
     - `test_suggestion_values_maps_spring_payload` : Vérifie la transformation des suggestions.
     - `test_upsert_suggestions_with_metrics` : Valide les métriques d'insertion/mise à jour.
     - `test_sync_status_endpoint_returns_suggestions_block` : Valide la réponse de l'API FastAPI.
2. **Rejeu de la Suite Complète** :
   - Exécution des 73 tests du catalogue et du moteur Text-to-SQL (`OK in < 2s`).
3. **Audit Git Diff** :
   - Contrôle strict de la non-altération des fichiers non concernés.

---

## 5. Matrice des Responsabilités & Ordre d'Exécution Recommandé

| Étape | Composant | Fichiers Touchés | Risque Régression |
| :---: | :--- | :--- | :---: |
| **1** | Python | `scripts/generate_ground_truth_oracle.py` (Oracles V1, V2, V3) | **Nul** (outillage pur) |
| **2** | Python | `app/services/sync_service.py` (support suggestions & clés étrangères) | **Très faible** (fallback gracieux) |
| **3** | Python | `tests/test_reporting_sync.py` (couverture unitaire ETL) | **Nul** (tests) |
| **4** | Python | `app/routers/sync.py` & `main.py` (API et scheduler) | **Faible** (optionnel via variable env) |
| **5** | Java | `ExportClaimDto`, `AiController`, `SuggestionRepository` | **Faible** (ajouts sans suppression) |
