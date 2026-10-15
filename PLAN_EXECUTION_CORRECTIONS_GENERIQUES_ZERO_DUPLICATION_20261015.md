# 📋 Plan d'Exécution Sécurisé : Corrections Génériques Zéro-Duplication

**Cadre Méthodologique :** Skill [`safe-code-change`](file:///C:/Users/HP/.gemini/config/skills/safe-code-change/SKILL.md)  
**Objectif :** Résoudre de manière générique et pérenne les 3 classes d'anomalies détectées lors des benchmarks (Test 1 et Test 2) **sans créer aucun nouveau fichier dans le code source** et **sans aucune duplication de code**.  
**Date d'édition :** 2026-10-15  
**Fichiers cibles modifiés :** Exactement 3 fichiers existants dans `app/reporting/`.

---

## 1. 🛡️ Principes Directeurs & Sanctuarisation de l'Existant

1. **Zéro Nouveau Fichier / Zéro Dispersion :**
   - Aucune création de module utilitaire annexe (`payload_normalizer.py`, `parameter_reconciler.py`, etc.).
   - Utilisation exclusive des points d'extension déjà prévus dans l'architecture existante.
2. **Zéro Bricolage Ad-Hoc :**
   - Interdiction formelle de coder des patchs spécifiques à une question ou à un concept unique (ex: interdiction d'écrire un simple `if param == 'claim_type'`).
   - Implémentation d'algorithmes génériques capables d'opérer sur n'importe quel concept, filtre, dimension ou placeholder SQL futur.
3. **Non-Régression Stricte :**
   - Préservation intégrale des contrats d'API existants (`TextToSQLIntent`, `TextToSQLCandidate`, `ReportingResponse`).
   - Maintien au vert des 118 tests unitaires existants.

---

## 2. 🔍 Analyse d'Impact & Cartographie des Modifications

```
                              ┌──────────────────────────────────────────────┐
                              │     FLUX EXISTANT DANS APP/REPORTING/        │
                              └──────────────────────────────────────────────┘
                                                     │
      ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐
      ▼                                              ▼                                              ▼
[FICHIER 1 : text_to_sql_contracts.py]       [FICHIER 2 : sql_generator.py]                 [FICHIER 3 : text_to_sql_pipeline.py]
• Classe IntentEntity existante              • build_sql_generation_prompt() existant        • execute_text_to_sql_pipeline() existant
• Ajout : @model_validator(mode="before")    • coerce_candidate_payload() existant          • Remplacement des lignes 502-532
  pour l'invariant booléen vs sous-ensemble    • Suppression du biais few-shot temporel       • Algorithme générique de liaison des
• Résout : Repli silencieux Run 09             • Élagage automatique paramètres orphelins      paramètres SQL (:param)
                                             • Résout : 11-14 alertes paramètres orphelins  • Résout : Crash SQL Run 07 (:claim_type)
```

---

## 3. 🛠️ Plan Détaillé des Modifications par Fichier Existant

### Modification N° 1 : Normalisation Générique des Invariants dans `text_to_sql_contracts.py`
- **Fichier cible :** [`app/reporting/text_to_sql_contracts.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/text_to_sql_contracts.py)
- **Localisation :** Dans la classe existante `IntentEntity` (lignes 30-50).
- **Problème résolu :** Le LLM renvoie souvent `include_all_types: true` avec une liste restreinte comme `types: ["CLAIM"]`. Le validateur Pydantic actuel rejette l'objet et provoque un repli silencieux vers le résolveur heuristique par mots-clés (Run 09).
- **Changement chirurgical :**
  Ajout d'un validateur générique `@model_validator(mode="before")` qui arbitre l'invariant :
  ```python
  @model_validator(mode="before")
  @classmethod
  def normalize_types_invariant(cls, data: Any) -> Any:
      if isinstance(data, dict):
          types = data.get("types") or []
          include_all = data.get("include_all_types", False)
          valid_full_sets = [
              {"CLAIM", "DENUNCIATION", "SUGGESTION"},
              {"CLAIM", "DENUNCIACION", "SUGGESTION"},
          ]
          # Si un sous-ensemble strict est fourni avec include_all=True,
          # l'intention restrictive explicite prime sur le drapeau global.
          if include_all and len(types) > 0 and set(types) not in valid_full_sets:
              data["include_all_types"] = False
          # Si la liste contient l'ensemble exhaustif des types, normaliser
          elif set(types) in valid_full_sets:
              data["include_all_types"] = True
              data["types"] = []
      return data
  ```

---

### Modification N° 2 : Nettoyage du Prompt & Élagage des Paramètres dans `sql_generator.py`
- **Fichier cible :** [`app/reporting/sql_generator.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/sql_generator.py)
- **Localisation 1 :** Dans `build_sql_generation_prompt()` (lignes 144-147).
  - **Action :** L'exemple JSON dans le prompt injectait systématiquement `start_date` et `end_date`, incitant le LLM à déclarer ces paramètres même en l'absence de contrainte de date. L'exemple sera dynamique : si `intent.time` est absent, l'exemple montre un dictionnaire `"parameters": {}` ou des paramètres de filtres métiers.
- **Localisation 2 :** Dans la fonction existante `coerce_candidate_payload()` (lignes 216-235).
  - **Action :** Ajouter une étape d'élagage automatique dans le coerciteur déjà en place :
  ```python
  # Élagage automatique des paramètres orphelins :
  # Ne conserver dans data["parameters"] que les clés effectivement référencées dans data["sql"]
  raw_sql = data.get("sql", "")
  if raw_sql and isinstance(data.get("parameters"), dict):
      required_placeholders = set(re.findall(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)", raw_sql))
      data["parameters"] = {
          p_name: p_meta
          for p_name, p_meta in data["parameters"].items()
          if p_name in required_placeholders
      }
  ```
- **Problème résolu :** Élimination définitive des 11 à 14 alertes `ORPHAN_PARAMETERS` dès la sortie du LLM, sans aucune surcouche externe.

---

### Modification N° 3 : Liaison Universelle et Réflexive des Paramètres dans `text_to_sql_pipeline.py`
- **Fichier cible :** [`app/reporting/text_to_sql_pipeline.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/text_to_sql_pipeline.py)
- **Localisation :** Section `e. Liaison des paramètres` (lignes 502-532).
- **Problème résolu :** Crash SQL du Run 07 (`InvalidRequestError: A value is required for bind parameter 'claim_type'`) causé par le fait que la liaison actuelle ne regarde jamais `intent.entity.types` et dépend de conditions `if` hardcodées.
- **Changement chirurgical :**
  Remplacer le bloc manuel par une fonction d'aide locale et générique `_build_bound_parameters(candidate_sql, intent, candidate_parameters)` :
  1. **Extraction de tous les placeholders requis par le SQL :**
     `required_params = set(re.findall(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)", candidate_sql))`
  2. **Construction du réservoir de valeurs universel :**
     - Temps : `start_date`, `end_date`.
     - Entité : si `intent.entity.types`, lier automatiquement `claim_type = types[0]`, `type = types[0]`, `entity_type = types[0]`.
     - Filtres : pour chaque `flt.concept_id`, lier sa valeur directe et ses variantes.
     - Paramètres candidats : si une source explicite est déclarée dans `candidate.parameters`, résoudre le chemin.
  3. **Liaison sécurisée :** Pour chaque placeholder extrait du SQL, injecter la valeur correspondante depuis le réservoir.

---

## 4. 🧪 Protocole de Validation & Non-Régression

Conformément à `/safe-code-change`, la validation se déroulera selon les étapes suivantes :

### Étape 1 : Tests Unitaires Locaux
1. Exécution de `python -m unittest tests/test_file_utils.py` (5 tests).
2. Exécution du banc complet `python -m unittest discover -s tests -p "test_step_*.py"` (118 tests existants).
3. Ajout de tests ciblés dans un fichier de test existant (`tests/test_step_5_schema_retriever_and_sql_generator.py`) pour certifier :
   - Que `claim_type` est correctement lié lorsqu'il est présent dans le SQL.
   - Que `include_all_types = True` combiné à `["CLAIM"]` est auto-corrigé sans lever de `ValidationError`.
   - Que les paramètres orphelins sont élagués automatiquement.

### Étape 2 : Test d'Intégration Réel sur les 24 Questions
Exécution de la commande officielle avec la garantie zéro-écrasement :
```powershell
python run_questions.py questions.txt --report RAPPORT_EXECUTION_QUESTIONS.md --audit
```

### Étape 3 : Audit Forensique Automatique via `/gpr-ai-audit-log`
Vérification des 4 indicateurs formels dans le rapport d'audit généré :
- ✅ **0 erreur d'exécution SQL SGBD** (Le Run 07 doit passer avec succès).
- ✅ **0 repli silencieux** (Le Run 09 doit être résolu directement par le LLM sans repli par mots-clés).
- ✅ **0 paramètre orphelin** (Tous les contrats doivent être nettoyés).
- ✅ **0 divergence SQL LLM vs Exécuté**.

---

## 5. 📦 Commandes Git Proposées pour l'Utilisateur

Aucune commande Git ne sera exécutée automatiquement. Les commandes suivantes seront fournies à l'utilisateur pour validation :

```bash
git status
git add app/reporting/text_to_sql_contracts.py app/reporting/sql_generator.py app/reporting/text_to_sql_pipeline.py
git commit -m "fix(reporting): resolution generique de liaison SQL et normalisation des invariants pydantic"
```
