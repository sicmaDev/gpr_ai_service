# Plan Détaillé : Auto-Promotion à l'Usage & Apprentissage par Feedback Utilisateur (GPR Auto-Learning)

> **Document officiel de référence — Module d'Apprentissage Autonome GPR**  
> **Conformité** : Alignement opérationnel avec l'architecture d'authentification native de GPR (utilisateurs habilités sans back-office d'administration externe) et l'architecture Text-to-SQL Gouvernée.  
> **Prérequis validés** :  
> • Steps 1 à 8 complétés et validés (105 tests unitaires à 100% de succès).  
> • Bouclier de Sécurité AST fonctionnel ([`sql_validator.py`](../app/reporting/sql_validator.py)).  
> • Exécuteur Read-Only et Bind Params validés ([`sql_executor.py`](../app/reporting/sql_executor.py)).  
> • Gestion du cycle de vie du catalogue ([`catalog_manager.py`](../app/reporting/catalog_manager.py)).

---

## 1. Contexte & Problématique Opérationnelle

Dans le système GPR :
1. **Tous les utilisateurs connectés sont déjà authentifiés et habilités** par le socle applicatif de la banque. Il n'existe pas de comité d'administration externe manuel pour valider chaque requête générée au fil de l'eau.
2. **Le besoin de consistance absolue** : Si un utilisateur obtient un bon résultat lundi sans signaler d'erreur, il s'attend impérativement à obtenir exactement le même résultat mardi pour la même question. Le LLM ne doit pas réinventer une requête différente au hasard.
3. **Le feedback négatif comme levier d'apprentissage** : Si un utilisateur signale une incohérence dans le résultat, ce signalement et son explication doivent devenir un **anti-pattern** interdisant au modèle de répéter l'erreur lors des futures générations.

---

## 2. Architecture & Composants Cibles

```text
app/reporting/
├── text_to_sql_contracts.py          # Extension : DTO UserFeedbackPayload
├── catalog_manager.py                # Fonctions : auto_promote_executed_query, submit_user_feedback, get_rejected_anti_patterns_for_intent
├── sql_generator.py                  # Enrichissement : build_candidate_prompt avec section Anti-patterns
├── query_catalog.py                  # Registre QueryCatalog
│
tests/
└── test_feedback_auto_learning.py    # Suite de tests dédiée
```

---

## 3. Spécifications Détaillées des Fonctions

### 3.1. DTO `UserFeedbackPayload` ([`text_to_sql_contracts.py`](../app/reporting/text_to_sql_contracts.py))
```python
class UserFeedbackPayload(ContractModel):
    query_id: NonEmptyString
    user_id: NonEmptyString
    is_positive: bool = True
    feedback_reason: Optional[str] = None
```

### 3.2. Auto-Promotion après exécution réussie (`auto_promote_executed_query`)
* **Signature** :
  ```python
  def auto_promote_executed_query(
      canonical_intent: TextToSQLIntent,
      parameterized_sql: str,
      natural_language_query: str,
      user_id: str,
      parameters_schema: Optional[Dict[str, CandidateParameter]] = None,
      schema_version: str = "1.0.0",
      query_id: Optional[str] = None,
  ) -> QueryCatalogEntry
  ```
* **Comportement** :
  * Si la requête existe déjà dans le catalogue : incrémente `execution_count` et actualise `last_executed_at`.
  * Si la requête est nouvelle : l'enregistre immédiatement au statut `ApprovalStatus.APPROVED` avec `approved_by="auto_verified"`, `approved_at=now()`.
  * **Conséquence** : La requête devient immédiatement active dans le Fast-Path.

### 3.3. Prise en compte du signalement utilisateur (`submit_user_feedback`)
* **Signature** :
  ```python
  def submit_user_feedback(payload: UserFeedbackPayload) -> QueryCatalogEntry
  ```
* **Comportement** :
  * Si `is_positive == True` : valide la satisfaction, incrémente les indicateurs de confiance.
  * Si `is_positive == False` :
    * Bascule `status = ApprovalStatus.REJECTED`.
    * Enregistre `rejection_reason = payload.feedback_reason`.
    * Enregistre `approved_by = payload.user_id` et `approved_at = now()`.
    * **Conséquence immédiate** : Retirée instantanément du Fast-Path.

### 3.4. Extraction des anti-patterns (`get_rejected_anti_patterns_for_intent`)
* **Signature** :
  ```python
  def get_rejected_anti_patterns_for_intent(
      intent: TextToSQLIntent,
      limit: int = 3,
  ) -> List[Dict[str, str]]
  ```
* **Comportement** :
  * Parcourt les requêtes du catalogue au statut `REJECTED`.
  * Filtre celles correspondant à la même entité (`concept_id`) ou métrique.
  * Retourne une liste de dictionnaires : `{"bad_sql": ..., "rejection_reason": ...}`.

### 3.5. Injection dans le prompt de génération ([`sql_generator.py`](../app/reporting/sql_generator.py))
* `build_candidate_prompt(...)` accepte un argument optionnel `anti_patterns: Optional[List[Dict[str, str]]] = None`.
* Si des anti-patterns sont présents, ajoute la section explicite :
  ```text
  === PIÈGES MÉTIER ET ERREURS À ÉVITER (SIGNALEMENTS UTILISATEURS PASSÉS) ===
  Les requêtes suivantes ont été FORMELLEMENT REJETÉES suite à des signalements d'utilisateurs habilités :
  - SQL ERRONÉ : SELECT ...
    MOTIF DU SIGNALEMENT : "..."
  CONSIGNE STRICTE : Tiens compte impérativement de ce retour et ne reproduis pas cette erreur.
  ```

---

## 4. Plan de Tests Unitaires (`tests/test_feedback_auto_learning.py`)

1. `test_auto_promote_executed_query_success` : Vérifie qu'une requête exécutée avec succès est auto-promue `APPROVED` et matchée par le Fast-Path.
2. `test_auto_promote_increments_count` : Vérifie l'incrémentation de `execution_count` sur exécutions répétées.
3. `test_user_feedback_rejection_removes_fast_path` : Vérifie que le signalement négatif retire la requête du Fast-Path.
4. `test_get_rejected_anti_patterns_for_intent` : Vérifie l'extraction des anti-patterns pertinents.
5. `test_prompt_injects_anti_patterns` : Vérifie la présence de la section anti-patterns dans le prompt Nemotron.
6. `test_prompt_clean_when_no_rejections` : Vérifie l'absence de section superflue lorsqu'il n'y a aucun rejet.
