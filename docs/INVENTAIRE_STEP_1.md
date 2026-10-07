# Inventaire Step 1 : Projection `gpr_ai_reporting`, Données Sensibles, Règles d'Accès et Dialecte SQL

> **Document officiel — Step 1 de la Phase 7 (Text-to-SQL Gouverné)**  
> Ce document consigne l'inventaire préalable requis par le point 1 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) avant toute implémentation ou exécution de requêtes SQL générées.

---

## 1. Inventaire de la Projection `gpr_ai_reporting`

La base de données miroir `gpr_ai_reporting` est une projection analytique dédiée, alimentée par la synchronisation incrémentale depuis Spring Boot.

### 1.1. Table Principale : `reporting_claim`

Issue du modèle SQLAlchemy [`ReportingClaim`](../app/db/models.py) et de la migration SQL [`001_create_reporting_claim.sql`](../app/db/migrations/001_create_reporting_claim.sql) :

| # | Colonne | Type SQL (MySQL) | Index / Contrainte | Rôle & Classification Métier |
| :-: | :--- | :--- | :--- | :--- |
| 1 | **`id`** | `BIGINT` | `PRIMARY KEY`, Auto-incrément | Identifiant technique interne de la ligne de reporting. |
| 2 | **`source_claim_id`** | `BIGINT` | `UNIQUE CONSTRAINT` | Identifiant du dossier dans la base opérationnelle source (`gpr_sicma_online`). |
| 3 | **`source_code`** | `VARCHAR(255)` | — | Référence métier du dossier (ex. `REC-2026-001`). |
| 4 | **`client_code`** | `VARCHAR(255)` | — | 🔴 **DONNÉE SENSIBLE** (Identifiant client). |
| 5 | **`claim_type`** | `VARCHAR(40)` | Indexé (`ix_..._claim_type`) | Dimension type : `CLAIM`, `DENUNCIACION`, `SUGGESTION`. |
| 6 | **`status`** | `VARCHAR(40)` | Indexé (`ix_..._status`) | Dimension statut : `SAVED`, `AFFECTED`, `TREAT`, `SATISFIED`, etc. *(Brouillon `TEMP_SAVED` exclu de la synchro)*. |
| 7 | **`category`** | `VARCHAR(255)` | Indexé (`ix_..._category`) | Dimension catégorie (ex. `MONETIQUE`, `FRAIS_BANCAIRES`, `CREDIT`). |
| 8 | **`motif`** | `VARCHAR(255)` | — | Dimension motif précis de la réclamation. |
| 9 | **`product`** | `VARCHAR(255)` | — | Dimension produit bancaire rattaché. |
| 10 | **`service_point`** | `VARCHAR(255)` | — | Dimension point de service / guichet d'enregistrement. |
| 11 | **`agency`** | `VARCHAR(255)` | Indexé (`ix_..._agency`) | Dimension agence bancaire de rattachement. |
| 12 | **`channel`** | `VARCHAR(255)` | Indexé (`ix_..._channel`) | Dimension canal de réception (`WEB`, `AGENCE`, `WHATSAPP`, `COURRIER`). |
| 13 | **`team`** | `VARCHAR(255)` | — | Dimension équipe responsable du traitement. |
| 14 | **`content`** | `TEXT` | — | 🔴 **DONNÉE SENSIBLE** (Texte brut saisi ou transcrit de la plainte). |
| 15 | **`solution`** | `TEXT` | — | 🔴 **DONNÉE SENSIBLE** (Texte libre de la réponse ou solution apportée). |
| 16 | **`ai_urgency`** | `VARCHAR(40)` | — | Niveau d'urgence détecté : `MINEUR`, `MOYEN`, `GRAVE`. |
| 17 | **`ai_sentiment`** | `VARCHAR(40)` | — | Sentiment détecté : `neutre`, `negatif`, `tres_negatif`. |
| 18 | **`risk_level`** | `VARCHAR(40)` | Indexé (`ix_..._risk_level`) | Niveau de risque métier du motif (`gps_objet.risqueLevel`) : `MINEUR`, `MOYEN`, `GRAVE`. |
| 19 | **`ai_risk_score`** | `DOUBLE` | — | Score de risque numérique calculé (0 à 100). |
| 20 | **`ai_summary`** | `TEXT` | — | Résumé concis de la demande produit par l'IA. |
| 21 | **`created_at`** | `DATETIME` | Indexé (`ix_..._created_at`) | Date et heure de création initiale de l'enregistrement. |
| 22 | **`receipt_at`** | `DATETIME` | — | **Date de référence métier pivot** (date de réception effective du dossier). |
| 23 | **`source_updated_at`** | `DATETIME` | Indexé (`ix_..._source_updated_at`) | Horodatage de mise à jour source (curseur de synchronisation incrémentale). |
| 24 | **`affected_at`** | `DATETIME` | — | Date d'affectation du dossier à un agent ou une équipe. |
| 25 | **`resolved_at`** | `DATETIME` | — | Date de résolution effective du dossier. |
| 26 | **`sla_due_at`** | `DATETIME` | — | Échéance SLA calculée selon la durée du motif (`receipt_at + processingTime`). |
| 27 | **`satisfaction_status`** | `VARCHAR(40)` | — | Statut de satisfaction client (`SATISFIED`, `UNSATISFIED`). |
| 28 | **`synced_at`** | `DATETIME` | — | Horodatage d'insertion/mise à jour dans `gpr_ai_reporting`. |

---

### 1.2. Tables Annexes dans `gpr_ai_reporting`

* **`reporting_sync_state`** (migration `002_create_reporting_sync_state.sql`) :  
  Assure le suivi technique et transactionnel des synchronisations incrémentales :
  * `sync_name`, `last_successful_sync_at`, `updated_at`, `last_started_at`, `last_completed_at`, `last_duration_ms`.
  * Compteurs : `last_received_count`, `last_inserted_count`, `last_updated_count`, `last_ignored_count`, `last_deleted_count`, `last_error_count`, `last_error`.
* **`reporting_alert`** (migration `003_create_reporting_alert.sql`) :  
  Persistance des alertes et anomalies détectées de façon idempotente :
  * `source_key`, `alert_type`, `severity`, `title`, `message`, `subtitle`, `status` (`new`, `in_progress`, `resolved`, `dismissed`), `owner`, `detected_at`, `resolved_at`, `source_rule`, `action`, `evidence`.

---

## 2. Inventaire des Données Sensibles (Règles d'Exclusion)

Trois colonnes de la table `reporting_claim` présentent un risque pour la confidentialité bancaire et la protection des données personnelles :

| Champ sensible | Nature de la donnée | Risque associé | Règle d'exclusion formelle |
| :--- | :--- | :--- | :--- |
| **`client_code`** | Identifiant unique du client bancaire | Ré-identification d'un client. | **Exclusion absolue** du Schema Catalog transmis au LLM. Aucun filtrage ou affichage nominatif. |
| **`content`** | Texte brut rédigé par le client ou transcrit d'un appel | Risque élevé de divulgation de données personnelles (nom, téléphone, adresse, RIB, montants, situation privée). | **Exclusion absolue** du contexte LLM pour la génération de requêtes analytiques. Interdiction de projection `SELECT content` par le Text-to-SQL. |
| **`solution`** | Texte de résolution rédigé par l'agent bancaire | Informations confidentielles sur la stratégie bancaire ou gestes commerciaux. | **Exclusion absolue** du contexte LLM et des requêtes du chatbot analytique. |

> **Sanctuarisation** :  
> Le moteur Text-to-SQL et son Schema Retriever opèrent **exclusivement sur les métadonnées de classification et d'agrégation** (`claim_type`, `status`, `agency`, `channel`, `category`, `receipt_at`, etc.).  
> Toute tentative d'interroger `content`, `client_code` ou `solution` doit être bloquée par le validateur AST.

---

## 3. Inventaire des Règles d'Accès

### 3.1. Périmètre Organisationnel
* **Architecture Mono-Institution** : L'application GPR est déployée pour un établissement bancaire unique.
* **Pas de cloisonnement multi-tenant SQL** : Les requêtes d'agrégation portent sur l'ensemble des données de l'institution, sans qu'un filtre utilisateur `tenant_id` ou `user_id` ne soit nécessaire dans chaque requête.

### 3.2. Habilitations du Compte SQL Reporting
* **Lecture Seule Stricte** :
  * Le compte MySQL utilisé par FastAPI pour le Text-to-SQL dispose **uniquement du privilège `SELECT`** sur la base `gpr_ai_reporting`.
  * **Interdiction absolue** des privilèges DML/DDL : `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `RENAME`.
  * **Interdiction absolue** des privilèges administratifs : `GRANT`, `REVOKE`, `SUPER`, `PROCESS`, `FILE`.
* **Cloisonnement Réseau & Bases** :
  * Aucun accès n'est accordé à ce compte sur la base opérationnelle `gpr_sicma_online`.
  * Aucun accès aux bases systèmes : `information_schema`, `mysql`, `performance_schema`, `sys`.

### 3.3. Limites de Ressources & Garde-Fous
* **Quota de lignes obligatoire** : Toute requête doit comporter une clause `LIMIT` maximale de sécurité (ex. `LIMIT 500`).
* **Timeout d'exécution** : Toute requête SQL excédant 3 secondes doit être automatiquement annulée.
* **Rollback systématique** : Chaque session de requête se termine par un rollback pour garantir l'absence totale d'effets de bord.

---

## 4. Inventaire du Dialecte SQL Réel

### 4.1. Dialecte Cible Opérationnel : MySQL 8.0 (`utf8mb4`)
* **Encodage** : `utf8mb4` complet pour la prise en charge des caractères accentués et emojis.
* **Format des Horodatages** : Types `DATETIME` stockés au format standard `YYYY-MM-DD HH:MM:SS`.
* **Fuseau Horaire de Référence** : `Africa/Porto-Novo` (UTC+1, heure locale du Bénin).
* **Gestion des Périodes Inclusives** :
  * Les bornes de dates doivent être interprétées sous la forme d'un intervalle semi-ouvert `[début_jour, début_lendemain[` afin d'englober tous les dossiers de la dernière journée jusqu'à `23:59:59` :
    ```sql
    WHERE receipt_at >= :start_date AND receipt_at < :end_date
    ```
* **Paramètres Liés Obligatoires** :
  * Syntaxe nommée `:param_name` (liaison SQLAlchemy / PyMySQL).
  * **Zéro interpolation** : Aucune valeur textuelle utilisateur n'est concaténée directement dans la chaîne SQL.

### 4.2. Dialecte de Test Automatisé : SQLite (en mémoire)
* Utilisé pour exécuter les tests unitaires et d'intégration rapide sans dépendre d'un serveur MySQL actif.
* Les requêtes candidates générées doivent respecter le standard **ANSI SQL** (compatible MySQL et SQLite) pour les clauses fondamentales (`SELECT`, `FROM`, `WHERE`, `GROUP BY`, `ORDER BY`, `COUNT`).

---

## 5. Bilan de Clôture du Step 1

Cet inventaire formalise :
1. La cartographie complète des 28 colonnes de la projection analytique `reporting_claim`.
2. L'exclusion stricte des 3 colonnes sensibles (`client_code`, `content`, `solution`).
3. Les règles d'accès en lecture seule sans multi-tenant.
4. Les spécifications du dialecte MySQL 8.0 et du fuseau horaire `Africa/Porto-Novo`.

Ce document acte la réalisation complète du **Step 1** (Point 1 de la section 15 du plan backend).
