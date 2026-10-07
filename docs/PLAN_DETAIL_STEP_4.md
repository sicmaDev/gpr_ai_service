# Plan Détaillé Step 4 : Résolution d'Intention & Query Catalog (Fast-Path Court-Circuit)

> **Document officiel de référence — Step 4 (Text-to-SQL Gouverné)**  
> **Conformité** : Point 4 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests unitaires validés).  
> • Catalogues Schéma & Métier : [`PLAN_DETAIL_STEP_3.md`](./PLAN_DETAIL_STEP_3.md), [`app/reporting/schema_catalog.py`](../app/reporting/schema_catalog.py) et [`app/reporting/business_catalog.py`](../app/reporting/business_catalog.py) (14 tests unitaires validés).

---

## 1. Objectif Fondamental du Step 4

Le **Step 4** met en place le premier filtre intelligent et sécurisé du pipeline analytique : **la compréhension de la demande usager et le court-circuit par requêtes pré-approuvées**.

Au lieu de faire générer du code SQL à un modèle d'IA pour chaque question (ce qui consomme des ressources, engendre de la latence et présente des risques d'hallucination), l'architecture sépare nettement deux responsabilités :

1. **Résolution d'Intention Canonique (`TextToSQLIntent`)** :
   * Transformer la question en langage naturel (ex: *"Combien de réclamations avons-nous eues par agence le mois dernier ?"*) en une structure formelle typée **SANS AUCUN SQL**.
   * Identifier avec certitude : le concept (`reclamation`), la métrique demandée (`reclamation_count`), les dimensions de regroupement (`agency`), les filtres éventuels et la fenêtre temporelle normée (fuseau horaire `Africa/Porto-Novo`).
   * Gérer formellement les ambiguïtés (`needs_clarification`) et les demandes hors périmètre (`unsupported`).

2. **Recherche dans le `QueryCatalog` (Fast-Path Court-Circuit)** :
   * Vérifier si cette intention canonique exacte correspond à un modèle de requête SQL déjà **validé, audité et approuvé par les administrateurs** (`status=ApprovalStatus.APPROVED`).
   * **Si OUI (Court-Circuit Immédiat)** :
     * La requête SQL certifiée est immédiatement réutilisée.
     * Les paramètres temporels et dimensionnels de l'intention (`:start_date`, `:end_date`, etc.) sont liés dynamiquement.
     * **Aucun modèle LLM n'est sollicité pour générer du SQL** $\rightarrow$ exécution directe instantanée, coût zéro, risque d'hallucination zéro.
   * **Si NON (Requête inédite)** :
     * L'intention canonique validée est transmise aux étapes suivantes (**Step 5** : Schema Retriever puis **Step 6** : Génération Nemotron & Validateur AST).

---

## 2. Architecture & Organisation des Fichiers

```text
app/reporting/
├── text_to_sql_contracts.py          # Step 2 : Contrats Pydantic (Validé - 15 tests)
├── schema_catalog.py                 # Step 3 : Cartographie des 13 tables & 15 jointures (Validé)
├── business_catalog.py               # Step 3 : Métriques, concepts, dimensions & synonymes (Validé)
│
├── query_catalog.py                  # NOUVEAU (Step 4) : Catalogue des requêtes certifiées (APPROVED)
│   ├── CERTIFIED_QUERIES             # Dictionnaire des requêtes pré-approuvées de référence
│   ├── get_certified_queries()       # Accesseur au catalogue
│   ├── get_query_by_id(query_id)     # Recherche unitaire
│   └── match_intent_in_catalog()     # Moteur de matching structurel & extraction de paramètres
│
├── intent_resolver.py                # NOUVEAU (Step 4) : Moteur de résolution d'intention
│   ├── resolve_intent(nl_query)      # Résolveur hybride (déterministe + LLM-ready)
│   ├── build_intent_prompt()         # Prompt Nemotron strict (JSON pur, INTERDICTION DE SQL)
│   ├── parse_intent_response()       # Désérialisation et validation Pydantic de la réponse
│   └── extract_date_range()          # Interpréteur temporel ('mois dernier', 'cette annee')
│
tests/
├── test_text_to_sql_contracts.py     # Tests Step 2 (15 tests)
├── test_schema_and_business_catalogs.py # Tests Step 3 (14 tests)
└── test_step_4_intent_and_query_catalog.py # NOUVEAU (Step 4) : Tests d'intention & Query Catalog
```

---

## 3. Détail du Fichier `query_catalog.py`

Le fichier implémente le catalogue initial des requêtes homologuées et le moteur d'appariement d'intention.

### 3.1. Les 8 Requêtes Certifiées Initiales (`CERTIFIED_QUERIES`)

Chaque entrée est une instance valide de `QueryCatalogEntry` avec `status=ApprovalStatus.APPROVED` :

| ID Requête | Question Cible | Mesure & Dimensions | Modèle SQL Paramétré (`:param`) |
| :--- | :--- | :--- | :--- |
| **`QC-CLAIM-COUNT-BY-AGENCY`** | Réclamations par agence sur une période | `reclamation_count`<br>dim: `agency` | `SELECT sp.libelle AS agency, COUNT(c.id) AS case_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY sp.libelle ORDER BY case_count DESC` |
| **`QC-CLAIM-COUNT-BY-CHANNEL`** | Réclamations par canal de collecte | `reclamation_count`<br>dim: `channel` | `SELECT cc.libelle AS channel, COUNT(c.id) AS case_count FROM reporting_claim c LEFT JOIN reporting_collection_channel cc ON c.collection_channel_id = cc.id WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY cc.libelle ORDER BY case_count DESC` |
| **`QC-UNIFIED-PLAINTES-TOTAL`** | Total unifié des dossiers (plaintes globales) | `plainte_count`<br>dim: *aucune* | `SELECT ((SELECT COUNT(*) FROM reporting_claim WHERE receipt_at >= :start_date AND receipt_at < :end_date) + (SELECT COUNT(*) FROM reporting_suggestion WHERE recorded_at >= :start_date AND recorded_at < :end_date)) AS plainte_count` |
| **`QC-SLA-ADHERENCE-RATE`** | Taux global de respect des délais SLA | `sla_adherence_rate`<br>dim: *aucune* | `SELECT AVG(CASE WHEN c.resolved_at <= c.sla_due_at THEN 100.0 ELSE 0.0 END) AS sla_adherence_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date AND c.resolved_at IS NOT NULL` |
| **`QC-SATISFACTION-RATE`** | Taux de satisfaction usagers | `satisfaction_rate`<br>dim: *aucune* | `SELECT AVG(CASE WHEN c.satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END) AS satisfaction_rate FROM reporting_claim c WHERE c.claim_type = 'CLAIM' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date AND c.satisfaction_status IS NOT NULL` |
| **`QC-SEVERE-PLAINTES-BY-AGENCY`**| Répartition des dossiers graves par agence | `severe_plainte_count`<br>dim: `agency` | `SELECT sp.libelle AS agency, COUNT(c.id) AS severe_count FROM reporting_claim c LEFT JOIN reporting_service_point sp ON c.service_point_id = sp.id WHERE c.claim_type = 'CLAIM' AND c.ai_urgency = 'GRAVE' AND c.receipt_at >= :start_date AND c.receipt_at < :end_date GROUP BY sp.libelle ORDER BY severe_count DESC` |
| **`QC-SUGGESTIONS-BY-IMPACT`** | Nombre de suggestions par niveau d'impact | `suggestion_count`<br>dim: `impact_level` | `SELECT s.impact_level, COUNT(s.id) AS suggestion_count FROM reporting_suggestion s WHERE s.recorded_at >= :start_date AND s.recorded_at < :end_date GROUP BY s.impact_level ORDER BY suggestion_count DESC` |
| **`QC-REAFFECTATION-COUNT`** | Nombre de réaffectations de dossiers | `reaffectation_count`<br>dim: *aucune* | `SELECT COUNT(h.id) AS reaffectation_count FROM reporting_historique_affectations h WHERE h.affectation_precedente_id IS NOT NULL AND h.date_affectation >= :start_date AND h.date_affectation < :end_date` |

### 3.2. Moteur d'Appariement d'Intention (`match_intent_in_catalog`)

L'algorithme compare la structure canonique de l'intention sans dépendre de la formulation textuelle exacte :
1. **Égalité du concept & des types** : `intent.entity.concept_id` et ensemble de `intent.entity.types`.
2. **Égalité de la mesure** : `intent.measure.concept_id`.
3. **Égalité des dimensions** : les concepts des dimensions demandées doivent correspondre exactement.
4. **Extraction et liaison des paramètres** :
   * Si une correspondance est trouvée, extraction de `:start_date` et `:end_date` depuis `intent.time`.
   * Association de toute valeur de filtre dynamique (`:agency_id`, etc.).
   * Retourne un tuple `(QueryCatalogEntry, bound_parameters: Dict[str, Any])`.

---

## 4. Détail du Fichier `intent_resolver.py`

Le fichier assure la traduction robuste d'une question en langage naturel vers un objet `TextToSQLIntent`.

### 4.1. Double Approche de Résolution
1. **Résolveur Déterministe (Fast & Local)** :
   * Analyse lexicale basée sur [`business_catalog.resolve_synonym`](../app/reporting/business_catalog.py#L318).
   * Extraction déterministe des dates relatives et absolues (ex: "ce mois", "le mois dernier", "en 2026", "du 01/01/2026 au 31/01/2026").
   * Fournit une exécution instantanée en local pour les requêtes types et les tests automatisés sans nécessiter d'appel réseau ou de token LLM.
2. **Résolveur LLM Nemotron (Généraliste)** :
   * Prompt strict contraignant le LLM à répondre **EXCLUSIVEMENT** par un objet JSON respectant le schéma de `TextToSQLIntent`.
   * **RÈGLE DE SÉCURITÉ FORMELLE** : Le prompt d'intention **INTERDIT FORMELLEMENT À NEMOTRON DE PRODUIRE DU SQL**. Il lui est seulement demandé de classifier l'intention, la mesure et les dimensions.

### 4.2. Gestion des Cas Limites
* **Demande incomplète ou ambiguë** $\rightarrow$ `status="needs_clarification"` :
  * Exemple : *"Combien de réclamations depuis mardi ?"* sans date de référence explicite.
  * Retourne `clarification = IntentClarification(code="AMBIGUOUS_TIME_FIELD", message="...", question="...")`.
* **Demande hors périmètre ou malveillante** $\rightarrow$ `status="unsupported"` :
  * Exemple : *"Donne-moi le mot de passe de l'admin"* ou *"Supprime les réclamations de l'agence X"*.
  * Retourne `unsupported_reason = "Demande hors du périmètre analytique en lecture seule."`.

---

## 5. Tests Unitaires du Step 4 (`tests/test_step_4_intent_and_query_catalog.py`)

La suite de tests vérifie les aspects clés du circuit rapide :

1. **Intégrité du Catalogue Initial** :
   * Les 8 requêtes initiales sont validées par le modèle Pydantic `QueryCatalogEntry`.
   * Toutes ont le statut `ApprovalStatus.APPROVED`.
   * Leurs requêtes SQL respectent la syntaxe des paramètres liés `:param`.
2. **Appariement d'Intention Réussi (Fast-Path Match)** :
   * Une intention de comptage par agence matche `QC-CLAIM-COUNT-BY-AGENCY`.
   * Les paramètres de date sont correctement extraits et formatés.
3. **Absence d'Appariement pour Requête Inédite** :
   * Une intention inédite retourne `None`, indiquant que le pipeline doit basculer sur le Step 5.
4. **Résolution d'Intention Déterministe** :
   * "Nombre de réclamations par agence en septembre 2026" $\rightarrow$ `reclamation_count`, dimension `agency`, dates `[2026-09-01, 2026-10-01[`.
   * "Combien de plaintes au total ce mois-ci ?" $\rightarrow$ `plainte_count`, tous types de dossiers.
5. **Gestion des Clarifications & Rejets** :
   * Question ambiguë $\rightarrow$ `status="needs_clarification"`.
   * Question hors périmètre $\rightarrow$ `status="unsupported"`.
6. **Non-régression Totale** :
   * Vérification que les 15 tests du Step 2 et les 14 tests du Step 3 restent à 100% au vert.

---

## 6. Critères de Réussite du Step 4

* [ ] `app/reporting/query_catalog.py` est implémenté et contient les 8 requêtes certifiées avec leur fonction de matching.
* [ ] `app/reporting/intent_resolver.py` est implémenté et produit des instances conformes de `TextToSQLIntent`.
* [ ] La suite de tests unitaires `test_step_4_intent_and_query_catalog.py` passe avec 100% de succès :
  ```bash
  python -m unittest tests/test_step_4_intent_and_query_catalog.py
  ```
* [ ] Les 29 tests existants (Step 2 + Step 3) restent au vert sans régression.
* [ ] Le pipeline dispose du circuit rapide (Fast-Path) prêt pour le **Step 5** (Schema Retriever).
