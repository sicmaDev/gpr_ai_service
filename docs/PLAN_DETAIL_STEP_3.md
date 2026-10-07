# Plan Détaillé Step 3 : Construction du Schema Catalog et du Business Catalog

> **Document officiel de référence — Step 3 (Text-to-SQL Gouverné)**  
> **Conformité** : Point 3 de la section 15 de [`REPORTING_IA_BACKEND_PLAN.md`](./REPORTING_IA_BACKEND_PLAN.md) et architecture cible de [`PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md`](./PLAN_IMPLANTATION_REPORTING_TEXT_TO_SQL.md).  
> **Prérequis validés** :  
> • Inventaire de référence : [`INVENTAIRE_STEP_1.md`](./INVENTAIRE_STEP_1.md)  
> • Contrats formels Pydantic : [`PLAN_DETAIL_STEP_2.md`](./PLAN_DETAIL_STEP_2.md) et [`app/reporting/text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py) (15 tests unitaires validés).

---

## 1. Objectif du Step 3

Le **Step 3** consiste à matérialiser les **deux catalogues fondamentaux** du moteur analytique sous la forme de **modules Python dédiés, typés et validés par les contrats Pydantic du Step 2** :

1. 📄 **`app/reporting/schema_catalog.py`** :  
   Instancie le **`SchemaCatalog`** officiel de `gpr_ai_reporting` : cartographie statique exhaustive des 12 tables, typage SQL réel (MySQL 8), marquage strict des colonnes sensibles (`is_sensitive=True`), et graphe officiel des relations autorisées pour les jointures `INNER JOIN` / `LEFT JOIN`.
2. 📄 **`app/reporting/business_catalog.py`** :  
   Instancie le **`BusinessCatalog`** officiel : concepts métiers (avec l'entité unifiée `plainte`), définitions certifiées des métriques (volumes, SLA, satisfaction, gravité), dimensions lisibles, et dictionnaire de synonymes en langue naturelle.
3. 📄 **`tests/test_schema_and_business_catalogs.py`** :  
   Suite de tests unitaires garantissant l'intégrité, la non-exposition des données sensibles et la validité des relations.

---

## 2. Architecture & Organisation des Fichiers

```text
app/reporting/
├── text_to_sql_contracts.py          # Modèles Pydantic stricts (Step 2 - Validé)
│
├── schema_catalog.py                 # NOUVEAU (Step 3) : Données du Schema Catalog
│   ├── SCHEMA_CATALOG                # Instance SchemaCatalog complète des 12 tables
│   ├── get_schema_catalog()          # Accesseur validé
│   └── get_minimal_subschema(tables) # Extracteur de sous-schéma pour le prompt LLM
│
└── business_catalog.py               # NOUVEAU (Step 3) : Données du Business Catalog
    ├── BUSINESS_CATALOG              # Instance BusinessCatalog complète
    ├── get_business_catalog()        # Accesseur validé
    └── resolve_synonym(term)         # Résolveur lexical de synonymes
```

---

## 3. Détail du Fichier `schema_catalog.py`

Le fichier implémente l'instance globale **`SCHEMA_CATALOG`** couvrant les 12 tables inventoriées :

### 3.1. Les 12 Tables Analytiques déclarées
1. **`reporting_claim`** (`fact`) :
   * Clé primaire : `id` (`BIGINT`).
   * Colonnes opérationnelles : `source_claim_id`, `source_code`, `claim_type` (`CLAIM`, `DENUNCIATION`), `status`, `receipt_at`, `created_at`, `source_updated_at`, `sla_due_at`, `resolved_at`, `risk_level`, `ai_urgency`, `ai_risk_score`, `objet_id`, `product_id`, `service_point_id`, `collection_channel_id`, `collector_id`.
   * **Colonnes sensibles marquées `is_sensitive=True`** : `client_code`, `content`, `solution`.
2. **`reporting_suggestion`** (`fact`) :
   * Clé primaire : `id` (`BIGINT`).
   * Colonnes opérationnelles : `source_suggestion_id`, `reference`, `title`, `status`, `impact_level`, `origine`, `recorded_at`, `created_at`, `updated_at`, `objet_id`, `product_id`, `service_point_id`, `collection_channel_id`, `enregistre_par_id`, `motif_rejet_soumission`.
   * **Colonnes sensibles marquées `is_sensitive=True`** : `client_code`, `client_name`, `phone`, `email`, `description`, `evaluator_notes`.
3. **`reporting_historique_affectations`** (`workflow`) :
   * Traçabilité des mouvements d'affectation : `reclamation_id`, `suggestion_id`, `type_plainte`, `nom_agent`, `email_agent`, `nom_affecteur`, `email_affecteur`, `date_affectation`, `delai_jours`, `date_fin_affectation`, `affectation_precedente_id`, `last_notification`, `mail_envoye`, `sms_envoye`.
4. **`reporting_solution`** (`workflow`) :
   * Cycle de validation de réponse : `claim_id`, `author_id`, `status`, `approver_id`, `approved_at`, `unapproved_at`, `is_ai_proposed`.
   * **Colonnes sensibles marquées `is_sensitive=True`** : `commentaire`, `motif_desaprobation`, `ai_selected_solution`.
5. **`reporting_existing_solution`** (`dimension`) :
   * Base de connaissances : `objet_id`, `content`, `compteur`.
6. **`reporting_satisfaction_measure`** (`workflow`) :
   * Évaluations clients post-clôture : `solution_id`, `measurer_id`, `status`, `measure_date_time`.
   * **Colonne sensible marquée `is_sensitive=True`** : `commentaire`.
7. **`reporting_product`** (`dimension`) :
   * Catalogue des produits : `id`, `libelle`, `description`, `is_deleted`.
8. **`reporting_service_point`** (`dimension`) :
   * Réseau d'agences : `id`, `libelle`, `description`, `type`, `is_principal_agence`, `direction_id`.
9. **`reporting_categorie_objet`** (`dimension`) :
   * Grandes familles de motifs : `id`, `libelle`, `description`.
10. **`reporting_objet`** (`dimension`) :
    * Motifs précis et contraintes SLA : `id`, `categorie_id`, `libelle`, `risque_level`, `processing_time`.
11. **`reporting_collection_channel`** (`dimension`) :
    * Canaux de collecte : `id`, `libelle`, `description`.
12. **`reporting_user`** & **`reporting_poste`** (`dimension`) :
    * Utilisateurs : `id`, `code`, `firstandlastname`, `email`, `service_point_id`, `poste_id`.
    * Postes : `id`, `libelle`, `description`.

### 3.2. Le Graphe Officiel des Relations (`relationships`)
Déclaration stricte des jointures autorisées (whitelist vérifiée par le parseur AST) :
* `claim_to_agency` : `reporting_claim.service_point_id = reporting_service_point.id` (`LEFT JOIN`)
* `claim_to_channel` : `reporting_claim.collection_channel_id = reporting_collection_channel.id` (`LEFT JOIN`)
* `claim_to_product` : `reporting_claim.product_id = reporting_product.id` (`LEFT JOIN`)
* `claim_to_object` : `reporting_claim.objet_id = reporting_objet.id` (`LEFT JOIN`)
* `object_to_category` : `reporting_objet.categorie_id = reporting_categorie_objet.id` (`LEFT JOIN`)
* `suggestion_to_agency` : `reporting_suggestion.service_point_id = reporting_service_point.id` (`LEFT JOIN`)
* `suggestion_to_channel` : `reporting_suggestion.collection_channel_id = reporting_collection_channel.id` (`LEFT JOIN`)
* `suggestion_to_product` : `reporting_suggestion.product_id = reporting_product.id` (`LEFT JOIN`)
* `suggestion_to_object` : `reporting_suggestion.objet_id = reporting_objet.id` (`LEFT JOIN`)
* `claim_to_affectations` : `reporting_claim.source_claim_id = reporting_historique_affectations.reclamation_id` (`LEFT JOIN`)
* `suggestion_to_affectations` : `reporting_suggestion.source_suggestion_id = reporting_historique_affectations.suggestion_id` (`LEFT JOIN`)
* `claim_to_solutions` : `reporting_claim.id = reporting_solution.claim_id` (`LEFT JOIN`)
* `solution_to_satisfaction` : `reporting_solution.id = reporting_satisfaction_measure.solution_id` (`LEFT JOIN`)
* `user_to_service_point` : `reporting_user.service_point_id = reporting_service_point.id` (`LEFT JOIN`)
* `user_to_poste` : `reporting_user.poste_id = reporting_poste.id` (`LEFT JOIN`)

### 3.3. Fonction utilitaire d'extraction de sous-schéma
* **`get_minimal_subschema(table_names: List[str]) -> str`** :  
  Génère une représentation textuelle ultra-compacte du schéma, **excluant automatiquement toute colonne où `is_sensitive == True`**, prête à être injectée dans le prompt Nemotron.

---

## 4. Détail du Fichier `business_catalog.py`

Le fichier implémente l'instance globale **`BUSINESS_CATALOG`** :

### 4.1. Concepts Métier Déclarés
* **`plainte`** : Concept chapeau unificateur (Réclamations, Dénonciations, Suggestions).
* **`reclamation`** : Sous-type `CLAIM` dans `reporting_claim`.
* **`denonciation`** : Sous-type `DENUNCIATION` dans `reporting_claim`.
* **`suggestion`** : Idée d'amélioration dans `reporting_suggestion`.
* **`treatment`** : Processus d'affectation et de validation.

### 4.2. Métriques Officielles Déclarées (`metrics`)
| Identifiant Métrique | Libellé | Formule Métier & SQL Template |
| :--- | :--- | :--- |
| **`plainte_count`** | Total unifié des plaintes (tous types) | `(SELECT COUNT(*) FROM reporting_claim) + (SELECT COUNT(*) FROM reporting_suggestion)` *(englobe Réclamations + Dénonciations + Suggestions)* |
| **`reclamation_count`** | Total des réclamations | `COUNT(reporting_claim.id)` avec `WHERE claim_type = 'CLAIM'` |
| **`denonciation_count`** | Total des dénonciations | `COUNT(reporting_claim.id)` avec `WHERE claim_type = 'DENUNCIATION'` |
| **`suggestion_count`** | Total des suggestions | `COUNT(reporting_suggestion.id)` |
| **`sla_adherence_rate`** | Taux de respect du délai SLA | `AVG(CASE WHEN resolved_at <= sla_due_at THEN 100.0 ELSE 0.0 END)` |
| **`avg_processing_time`** | Délai moyen de traitement | `AVG(DATEDIFF(resolved_at, receipt_at))` (en jours) |
| **`satisfaction_rate`** | Taux de satisfaction usagers | `AVG(CASE WHEN satisfaction_status = 'SATISFIED' THEN 100.0 ELSE 0.0 END)` |
| **`severe_plainte_count`** | Plaintes graves | `COUNT(reporting_claim.id)` avec `WHERE ai_urgency = 'GRAVE'` |
| **`adoption_rate`** | Taux d'adoption des suggestions | `AVG(CASE WHEN status = 'ADOPTEE' THEN 100.0 ELSE 0.0 END)` |
| **`reaffectation_count`**| Nombre de réaffectations | `COUNT(reporting_historique_affectations.id)` avec `affectation_precedente_id IS NOT NULL` |

### 4.3. Dimensions Déclarées (`dimensions`)
* `agency` $\rightarrow$ `reporting_service_point.libelle`
* `channel` $\rightarrow$ `reporting_collection_channel.libelle`
* `product` $\rightarrow$ `reporting_product.libelle`
* `category` $\rightarrow$ `reporting_categorie_objet.libelle`
* `object` $\rightarrow$ `reporting_objet.libelle`
* `status` $\rightarrow$ `reporting_claim.status` / `reporting_suggestion.status`
* `risk_level` $\rightarrow$ `reporting_claim.risk_level`
* `impact_level` $\rightarrow$ `reporting_suggestion.impact_level`
* `agent` $\rightarrow$ `reporting_user.firstandlastname`
* `period` $\rightarrow$ Année (`YEAR()`), Mois (`DATE_FORMAT('%Y-%m')`), Jour (`DATE()`)

### 4.4. Dictionnaire Exhaustif des Synonymes (`synonyms`)
* `plainte` $\rightarrow$ `["plainte", "plaintes", "dossier", "dossiers", "requete", "requetes"]`
* `reclamation` $\rightarrow$ `["reclamation", "reclamations", "doleance", "doleances", "mecontentement", "litige", "litiges"]`
* `denonciation` $\rightarrow$ `["denonciation", "denonciations", "fraude", "fraudes", "soupcon", "soupcons", "signalement", "signalements"]`
* `suggestion` $\rightarrow$ `["suggestion", "suggestions", "idee", "idees", "proposition", "propositions", "amelioration", "ameliorations"]`
* `agency` $\rightarrow$ `["agence", "agences", "guichet", "guichets", "point de vente", "point de service", "succursale"]`
* `channel` $\rightarrow$ `["canal", "canaux", "moyen", "source", "voie"]`
* `sla_adherence_rate` $\rightarrow$ `["respect sla", "delai legal", "delai contractuel", "taux de respect", "dans les delais"]`
* `satisfaction_rate` $\rightarrow$ `["satisfaction", "satisfait", "avis client", "contentement"]`
* `severe` $\rightarrow$ `["grave", "graves", "critique", "critiques", "urgent", "urgents", "alerte"]`

---

## 5. Tests Unitaires du Step 3 (`tests/test_schema_and_business_catalogs.py`)

1. **Test d'exhaustivité du Schema Catalog** :
   * Vérifie que les 12 tables sont présentes.
   * Vérifie que les clés primaires sont correctement déclarées.
   * Vérifie que les colonnes sensibles (`client_code`, `content`, `solution`, etc.) sont bien marquées `is_sensitive=True`.
2. **Test du filtre de sous-schéma sécurisé** :
   * Vérifie que `get_minimal_subschema()` ne contient jamais aucun nom de colonne sensible.
3. **Test d'intégrité des relations** :
   * Vérifie que chaque relation déclarée dans `SCHEMA_CATALOG.relationships` pointe vers des tables et colonnes existantes.
4. **Test du Business Catalog** :
   * Vérifie la présence de toutes les métriques et de leurs formules modèles.
   * Vérifie la résolution correcte des synonymes ("plaintes" $\rightarrow$ `plainte`, "fraudes" $\rightarrow$ `denonciation`, etc.).

---

## 6. Critères de Validation du Step 3

* [ ] Les fichiers `schema_catalog.py` et `business_catalog.py` sont créés et instancient sans erreur les modèles Pydantic.
* [ ] Aucune colonne sensible n'est omise dans la liste d'exclusion.
* [ ] La suite de tests unitaires passe à 100% :
  ```bash
  python -m unittest tests/test_schema_and_business_catalogs.py
  ```
* [ ] Les catalogues sont prêts pour le **Step 4** (Résolution d'intention & Query Catalog).
