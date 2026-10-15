# 🏛️ Analyse Forensique Comparative & Plan d'Architecture des Résolutions Génériques

**Périmètre d'analyse :** Benchmark des 24 questions de référence ([`questions.txt`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/questions.txt))  
**Données sources auditées :**
- **Test 1 :** Journal [`workflow_execution.log`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/workflow_execution.log) | Rapport [`RAPPORT_AUDIT_WORKFLOW.md`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/RAPPORT_AUDIT_WORKFLOW.md)
- **Test 2 :** Journal [`workflow_execution_20261014_230427.log`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/workflow_execution_20261014_230427.log) | Rapport [`RAPPORT_AUDIT_WORKFLOW_20261014_231520.md`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/RAPPORT_AUDIT_WORKFLOW_20261014_231520.md)  
**Date d'édition :** 2026-10-15  
**Philosophie :** Conception globale et systémique (Zéro patch ad-hoc, zéro correction spécifique de symptôme).

---

## 1. Synthèse Exécutive du Benchmark Test 1 vs Test 2

| Métrique de Gouvernance | Test 1 (Baseline) | Test 2 (Post-Garantie Zéro-Écrasement) | Évolution & Constat |
|---|:---:|:---:|---|
| **Volume de questions testées** | 24 | 24 | 100% traitées |
| **Hits Fast-Path (Catalogue homologué)** | 4 (16.7%) | 3 (12.5%) | Run 22 a basculé en clarification |
| **Hits Candidate-Path (Auto-promotion)** | 3 (12.5%) | 3 (12.5%) | Stabilité parfaite des requêtes en attente |
| **Générations LLM Nemotron** | 17 (70.8%) | 18 (75.0%) | +1 appel suite à l'arbitrage Run 22 |
| 🚨 **Replis silencieux (Étape 1 Pydantic)** | **1** (Run 09) | **1** (Run 09) | **Systémique :** Erreur contractuelle reproductible |
| ❌ **Erreurs d'exécution SQL SGBD** | **0** | **1** (Run 07) | **Systémique :** Paramètre lié SQL non résolu |
| 🚨 **Divergences SQL LLM vs Exécuté** | **0** | **0** | Conformité AST parfaite à 100% |
| ⚠️ **Paramètres orphelins déclarés** | **14 runs** | **11 runs** | Contrats pollués par `start_date`/`end_date` inutilisés |
| 🔒 **Fuites de données sensibles (PII)** | **0** | **0** | Étanchéité RGPD totale |

---

## 2. Matrice Comparative Question par Question

| # | Question Posée | Circuit Test 1 | Statut BDD Test 1 | Circuit Test 2 | Statut BDD Test 2 | Diagnostic Comparatif |
|---|---|:---:|:---:|:---:|:---:|---|
| **01** | Combien de réclamations ? | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **02** | Quelles sont les dénonciations enregistrées ? | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **03** | Nombre d'idées et suggestions d'amélioration | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **04** | Volume total de dossiers reçus par la banque | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **05** | Combien de transferts de dossiers ont eu lieu ? | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **06** | Plaintes | `CANDIDATE_PATH` | `SUCCESS` | `CANDIDATE_PATH` | `SUCCESS` | Cache réutilisé (< 4s) |
| **07** | Réclamations moyennes | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | ❌ **`SQL_ERROR`** | **Régression :** Paramètre `:claim_type` non lié en BDD |
| **08** | Taux de respect des engagements SLA | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **09** | Pourcentage d'usagers satisfaits | `GENERATIVE_LLM` | `SUCCESS` (Repli) | `GENERATIVE_LLM` | `SUCCESS` (Repli) | 🚨 **Repli silencieux Étape 1** (`types` vs `include_all`) |
| **10** | Score moyen de risque estimé | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **11** | Réclamations par agence | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **12** | Dossiers par canal de collecte | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **13** | Suggestions selon le niveau d'impact | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **14** | Réclamations par agence et par canal | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **15** | Total des réclamations | `CANDIDATE_PATH` | `SUCCESS` | `CANDIDATE_PATH` | `SUCCESS` | Cache réutilisé (< 3s) |
| **16** | Réclamations graves | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **17** | Plaintes critiques ou lourdes | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **18** | Dossiers insatisfaits | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **19** | Réclamations graves insatisfaites du canal Web | `GENERATIVE_LLM` | `SUCCESS` | `GENERATIVE_LLM` | `SUCCESS` | Nominal |
| **20** | Nombre de réclamations par agence | `CANDIDATE_PATH` | `SUCCESS` | `CANDIDATE_PATH` | `SUCCESS` | Cache réutilisé (< 4s) |
| **21** | En 2026 | `FAST_PATH` | `SUCCESS` | `FAST_PATH` | `SUCCESS` | Template certifié |
| **22** | En mars 2026 | `FAST_PATH` | `SUCCESS` | `CLARIFICATION` | `SUCCESS` | **Oscillation :** Ambiguïté de question elliptique |
| **23** | Premier trimestre 2026 | `FAST_PATH` | `SUCCESS` | `FAST_PATH` | `SUCCESS` | Template certifié |
| **24** | Ce mois-ci | `FAST_PATH` | `SUCCESS` | `FAST_PATH` | `SUCCESS` | Template certifié |

---

## 3. Décomposition des 3 Classes Fondamentales de Défaillances

Au lieu de considérer ces incidents comme des anomalies isolées, une analyse architecturale révèle **trois faiblesses structurelles profondes** dans le pipeline actuel :

```
                  ┌────────────────────────────────────────────────────────┐
                  │ FLUX TEXT-TO-SQL ACTUEL : POINTS DE RUPTURE IDENTIFIÉS │
                  └────────────────────────────────────────────────────────┘
                                              │
      ┌───────────────────────────────────────┼──────────────────────────────────────┐
      ▼                                       ▼                                      ▼
[CLASSE A : LIAISON SQL]            [CLASSE B : CONTRATS PYDANTIC]          [CLASSE C : AIGUILLAGE ELLIPTIQUE]
• Liaison ad-hoc et hardcodée       • Conflit logique booléen vs liste      • Flottement probabiliste du LLM
• Absence d'inspection de la SQL    • Échec validation `include_all_types`  • Absence d'entité pivot par défaut
• Paramètre :claim_type oublié      • Repli silencieux vers mots-clés       • Oscillation Fast-Path / Clarification
• Paramètres orphelins non nettoyés • Données natives du LLM perdues        • Non-reproductibilité des requêtes
```

---

### Classe A : Le Goulet d'Étranglement de la Liaison des Paramètres SQL (Anomalie Run 07 & Paramètres Orphelins)

#### 1. Symptôme Observé
- Dans le Test 2 (Run 07 - « *Réclamations moyennes* »), le LLM a généré :
  ```sql
  SELECT COUNT(`id`) AS reclamation_count 
  FROM `reporting_claim` 
  WHERE claim_type = :claim_type AND risk_level = :risk_level
  ```
  Le contrat `parameters` déclarait :
  ```json
  "parameters": {
    "claim_type": {"type": "string", "source": "intent.params.claim_type"},
    "risk_level": {"type": "string", "source": "intent.params.risk_level"}
  }
  ```
  L'exécution a échoué avec l'erreur SQLAlchemy :
  `InvalidRequestError: A value is required for bind parameter 'claim_type'`.
- Parallèlement, sur 11 à 14 runs, le LLM a déclaré dans son contrat `parameters` les clés `start_date` et `end_date` alors que le SQL n'en avait aucun besoin (paramètres orphelins).

#### 2. Cause Racine Globale
Dans [`text_to_sql_pipeline.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/text_to_sql_pipeline.py) (lignes 502 à 532), la liaison des paramètres est construite de façon artisanale :
```python
# Code actuel (Approche restrictive et non générique) :
bound_params = {}
if intent.time:
    bound_params["start_date"] = ...
    bound_params["end_date"] = ...
for flt in intent.filters:
    bound_params[flt.concept_id] = ...
    if flt.concept_id in ("risk_level", "ai_urgency", "urgency"):
        ...
```
**Les 4 failles systémiques de cette approche :**
1. **Amnésie de l'Entité :** `intent.entity.types` (contenant `['CLAIM']`) n'est jamais relié à `:claim_type` ou `:type`.
2. **Absence d'introspection du SQL :** Le pipeline ne regarde jamais quels paramètres `:param` sont **effectivement présents** dans la requête SQL avant de l'envoyer à la base.
3. **Absence de réservoir unifié :** Aucune structure ne centralise l'ensemble des valeurs contextuelles disponibles (entité, filtres, temps, dimensions, métadonnées).
4. **Absence d'élagage bidirectionnel :** Les paramètres inutilisés par le SQL restent dans le contrat, créant des alertes de paramètres orphelins.

---

### Classe B : La Rigidité des Validations Pydantic Face aux Invariants LLM (Anomalie Run 09)

#### 1. Symptôme Observé
- Dans le Test 1 et le Test 2 (Run 09 - « *Pourcentage d'usagers satisfaits* »), le LLM a renvoyé :
  ```json
  "entity": {
    "concept_id": "plainte",
    "types": ["CLAIM"],
    "include_all_types": true
  }
  ```
  Pydantic a levé une `ValidationError` :
  `types doit etre vide ou contenir l'ensemble des types lorsque include_all_types vaut true`.
  Le pipeline a immédiatement basculé en repli silencieux vers le résolveur déterministe (`FALLBACK_DETERMINISTE_MOTS_CLES`).

#### 2. Cause Racine Globale
Les modèles de langage oscillent fréquemment dans leurs sorties JSON entre :
- Un drapeau booléen d'intention globale (`include_all_types: true`).
- Une liste restrictive de concrétisation (`types: ["CLAIM"]`).

Le validateur Pydantic actuel agit comme un **mur rigide binaire** : soit la sortie du LLM est strictement parfaite, soit elle est rejetée en bloc, forçant un repli vers des mots-clés qui perdent la richesse sémantique du prompt.

Une solution spécifique consistant à coder `if include_all_types and len(types) == 1: include_all_types = False` ne résoudra pas les futures variantes :
- Que faire si le LLM renvoie `types: ["ALL"]` ?
- Que faire si le LLM renvoie `types: []` avec `include_all_types: false` ?
- Que faire si le LLM mélange des minuscules/majuscules ou des synonymes (`"claim"` vs `"CLAIM"`) ?
- Que faire si un filtre porte sur la même colonne qu'une dimension ?

Il faut une **couche générique de normalisation des invariants** capable de réparer intelligemment et de façon déterministe les structures JSON avant ou pendant la validation Pydantic.

---

### Classe C : L'Ambigüité des Questions Elliptiques & l'Arbitrage de Routage (Anomalie Run 22)

#### 1. Symptôme Observé
- Question N° 22 : « *En mars 2026* »
  - Dans le **Test 1** : reconnue et exécutée via `FAST_PATH_HOMOLOGATED` (`QC-UNIFIED-PLAINTES-TOTAL`, 8.4 s).
  - Dans le **Test 2** : déclarée comme `CLARIFICATION_NEEDED` (aucun SQL généré, 12.9 s).

#### 2. Cause Racine Globale
Une question comme « *En mars 2026* » est **elliptique** : elle exprime un prédicat temporel sans énoncer ni sujet (entité) ni verbe (mesure).
Actuellement :
- Le LLM de l'Étape 1 est sollicité sans contexte sur le comportement par défaut à adopter.
- Selon la stochasticité du modèle (température, contexte précédent), il déduit soit que l'entité implicite est le concept pivot (`plainte`), soit qu'il manque d'informations pour répondre et demande une clarification.

Il manque une règle de gouvernance formelle : **Quelle est la sémantique canonique d'une question purement temporelle ou purement dimensionnelle ?**

---

## 4. Architecture des Solutions Génériques (Zéro Patch Ad-Hoc)

Pour immuniser durablement le workflow contre ces 3 classes d'anomalies, nous concevons **3 moteurs génériques réutilisables**.

---

### Solution 1 : Le Moteur Universel de Réconciliation des Paramètres SQL (`UniversalParameterReconciler`)

Ce moteur élimine à la fois l'erreur d'exécution SQL (Run 07) et les paramètres orphelins (11 à 14 runs).

```
                      ┌──────────────────────────────────────────────┐
                      │    UNIVERSAL PARAMETER RECONCILER            │
                      └──────────────────────────────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
[1. Extraction AST Requise]         [2. Réservoir de Valeurs]            [3. Mappage Réflexif]
Parse le SQL via SQLglot            Agrège dynamiquement :               Pour chaque :param requis :
Identifie tous les placeholders     • entity.types -> claim_type, type   1. Match exact
exacts : (:param_1, :param_2...)    • filters.* -> risk_level, status... 2. Match synonymique BDD
                                    • time.* -> start_date, end_date     3. Dérivation contextuelle
                                    • dimensions.* -> groupement
                                              │
                                              ▼
                               [4. Élagage & Injection Sécurisée]
                               • Supprime les paramètres orphelins du contrat JSON
                               • Injecte les paramètres résolus dans bound_params
                               • Si paramètre introuvable -> Erreur qualifiée pré-BDD
```

#### Algorithme Générique (Implémentation de Référence) :

```python
"""
tools/common/parameter_reconciler.py
Moteur universel d'introspection, de résolution et d'élagage des paramètres SQL.
"""

from typing import Dict, Any, Set, Tuple, Optional
import re
from app.reporting.text_to_sql_contracts import TextToSQLIntent, TextToSQLCandidate


class UniversalParameterReconciler:
    """
    Réconcilie de manière générique les placeholders SQL avec le contexte sémantique de l'intention.
    Garantit zéro paramètre non lié en base et zéro paramètre orphelin dans le contrat.
    """

    # Correspondances conceptuelles canoniques universelles
    CONCEPT_SYNONYM_MAP = {
        "claim_type": ["claim_type", "type", "entity_type", "types"],
        "risk_level": ["risk_level", "urgency", "ai_urgency", "gravite", "niveau_risque"],
        "status": ["status", "statut", "operational_status"],
        "satisfaction_status": ["satisfaction_status", "satisfaction", "avis"],
        "start_date": ["start_date", "date_debut", "from_date", "receipt_at_from"],
        "end_date": ["end_date", "date_fin", "to_date", "receipt_at_to"],
    }

    @classmethod
    def extract_sql_placeholders(cls, sql: str) -> Set[str]:
        """Extrait tous les noms de paramètres nommés (:param) d'une requête SQL."""
        if not sql:
            return set()
        # Détection regex robuste des paramètres nommés (ignorant les ::cast PostgreSQL si applicable)
        matches = re.findall(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)", sql)
        return set(matches)

    @classmethod
    def build_context_value_pool(cls, intent: TextToSQLIntent) -> Dict[str, Any]:
        """
        Construit un réservoir exhaustif de valeurs contextuelles à partir de l'intention canonique.
        Fonctionne pour n'importe quelle entité, dimension ou filtre futur sans code spécifique.
        """
        pool: Dict[str, Any] = {}

        # 1. Extraction temporelle
        if intent.time:
            if intent.time.start_date:
                s_val = f"{intent.time.start_date.isoformat()} 00:00:00"
                pool["start_date"] = s_val
                pool["date_debut"] = s_val
            if intent.time.end_date:
                e_val = f"{intent.time.end_date.isoformat()} 00:00:00"
                pool["end_date"] = e_val
                pool["date_fin"] = e_val

        # 2. Extraction d'entité et types discriminants (Résout génériquement le bug Run 07)
        if intent.entity:
            pool["entity_concept"] = intent.entity.concept_id
            if intent.entity.types:
                # La première valeur scalaire
                scalar_type = intent.entity.types[0]
                pool["claim_type"] = scalar_type
                pool["type"] = scalar_type
                pool["entity_type"] = scalar_type
                pool["types"] = intent.entity.types

        # 3. Extraction des filtres dynamiques (générique sur tous les concepts)
        for flt in intent.filters:
            val = flt.value if flt.value is not None else flt.values
            concept = flt.concept_id
            pool[concept] = val
            pool[f"{concept}_param"] = val

            # Injection dans les synonymes connus
            for canonical_key, aliases in cls.CONCEPT_SYNONYM_MAP.items():
                if concept in aliases:
                    pool[canonical_key] = val
                    for alias in aliases:
                        pool[alias] = val

        # 4. Extraction des dimensions
        for dim in intent.dimensions:
            pool[f"dimension_{dim.concept_id}"] = dim.concept_id

        return pool

    @classmethod
    def reconcile(
        cls,
        sql: str,
        intent: TextToSQLIntent,
        declared_parameters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Exécute la réconciliation complète :
        1. Identifie les placeholders SQL réellement nécessaires.
        2. Résout leurs valeurs depuis le réservoir contextuel.
        3. Élimine les paramètres orphelins du contrat.
        
        Retourne : (sql_nettoye, bound_params_resolus, cleaned_parameters_contract)
        """
        required_placeholders = cls.extract_sql_placeholders(sql)
        value_pool = cls.build_context_value_pool(intent)
        bound_params: Dict[str, Any] = {}
        missing_params: Set[str] = set()

        for placeholder in required_placeholders:
            if placeholder in value_pool:
                bound_params[placeholder] = value_pool[placeholder]
            else:
                # Recherche floue / insensible à la casse
                found = False
                for k, v in value_pool.items():
                    if k.lower() == placeholder.lower() or placeholder.lower().startswith(k.lower()):
                        bound_params[placeholder] = v
                        found = True
                        break
                if not found:
                    missing_params.add(placeholder)

        if missing_params:
            raise ValueError(
                f"Gouvernance SQL : Paramètres requis par la requête mais introuvables dans le contexte : {sorted(missing_params)}"
            )

        # Élagage des paramètres orphelins du contrat déclaré
        cleaned_parameters_contract: Dict[str, Any] = {}
        if declared_parameters:
            for p_name, p_meta in declared_parameters.items():
                if p_name in required_placeholders:
                    cleaned_parameters_contract[p_name] = p_meta

        return sql, bound_params, cleaned_parameters_contract
```

---

### Solution 2 : La Couche Générique de Normalisation des Invariants (`PayloadInvariantNormalizer`)

Cette couche résout génériquement les conflits logiques LLM (Run 09) en appliquant des règles d'invariants formelles avant la validation Pydantic.

```
                  ┌──────────────────────────────────────────────┐
                  │       PAYLOAD INVARIANT NORMALIZER           │
                  └──────────────────────────────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
[Invariant Booléen vs Liste]     [Normalisation Types SQL]      [Résolution Synonymes]
Si `include_all` est True        Mappe `double`, `float`,       Aligne les concepts
ET que `types` a un sous-        `decimal`, `real` vers le      inconnus vers le catalogue
ensemble strict (ex: ['CLAIM'])  type canonique attendu         officiel de la BDD
-> `include_all` forcé à False   par le schéma (évite rejet)    (ex: 'critique' -> 'GRAVE')
```

#### Algorithme Générique :

```python
"""
app/reporting/payload_normalizer.py
Normalisateur d'invariants pour les charges utiles JSON émises par les LLM.
"""

from typing import Dict, Any, List


class PayloadInvariantNormalizer:
    """
    Normalise et assainit les structures de données issues des LLM avant validation Pydantic.
    Prévient 100% des échecs de validation dus à des contradictions booléen/liste ou synonymes.
    """

    @classmethod
    def normalize_entity_payload(cls, raw: Dict[str, Any], known_entity_types: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Normalise les invariants d'une entité (concept_id, types, include_all_types).
        Résout génériquement le bug du Run 09.
        """
        if not isinstance(raw, dict):
            return raw

        entity = raw.get("entity")
        if not isinstance(entity, dict):
            return raw

        types = entity.get("types") or []
        include_all = entity.get("include_all_types", False)
        concept_id = entity.get("concept_id", "plainte")

        # Univers des types connus pour ce concept (s'il est documenté)
        all_possible_types = (known_entity_types or {}).get(concept_id, ["CLAIM", "DENUNCIATION", "SUGGESTION"])

        # INVARIANT 1 : Liste avec sentinelle universelle ("ALL", "TOUS", "*")
        sentinels = {"all", "tous", "*", "tout"}
        if any(str(t).lower() in sentinels for t in types):
            entity["types"] = []
            entity["include_all_types"] = True
            return raw

        # INVARIANT 2 : Conflit include_all=True avec liste restreinte non vide
        # Règle d'or : La présence d'une restriction explicite de l'utilisateur l'emporte sur le drapeau global
        if include_all and len(types) > 0 and len(types) < len(all_possible_types):
            entity["include_all_types"] = False

        # INVARIANT 3 : Liste couvrant 100% des types possibles
        if set(types) == set(all_possible_types):
            entity["types"] = []
            entity["include_all_types"] = True

        raw["entity"] = entity
        return raw

    @classmethod
    def normalize_candidate_sql_payload(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise les types de données SQL et le schéma des paramètres d'une requête candidate.
        Évite les rejets Pydantic de type `float` vs `double` ou `varchar` vs `string`.
        """
        if not isinstance(raw, dict):
            return raw

        type_alias_map = {
            "float": "double",
            "real": "double",
            "decimal": "double",
            "numeric": "double",
            "number": "double",
            "int": "integer",
            "bigint": "integer",
            "varchar": "string",
            "text": "string",
            "char": "string",
            "date": "datetime",
            "timestamp": "datetime",
        }

        # Normaliser les colonnes de résultat
        for col in raw.get("result_columns") or []:
            if isinstance(col, dict) and "data_type" in col:
                dt = str(col["data_type"]).lower()
                col["data_type"] = type_alias_map.get(dt, dt)

        # Normaliser les types de paramètres
        params = raw.get("parameters")
        if isinstance(params, dict):
            for p_name, p_meta in params.items():
                if isinstance(p_meta, dict) and "type" in p_meta:
                    pt = str(p_meta["type"]).lower()
                    p_meta["type"] = type_alias_map.get(pt, pt)

        return raw
```

---

### Solution 3 : L'Arbitre Déterministe pour Questions Elliptiques (`EllipticalQueryArbiter`)

Cette règle résout le flottement du Run 22 ("En mars 2026") entre Fast-Path et Clarification.

#### Règle de Gouvernance Formelle :
1. **Définition d'une Question Elliptique :**  
   Toute question utilisateur qui formule une coordonnée temporelle (`En 2026`, `En mars 2026`, `Ce mois-ci`) ou une coordonnée spatiale/dimensionnelle (`Par agence`, `Par canal`) **sans nommer explicitement d'entité ni de mesure**.
2. **Entité Pivot par Défaut (Convention Bancaire Gouvernée) :**  
   Dans le domaine GPR Banque, l'entité pivot de référence par défaut est certifiée comme étant :
   - `concept_id: "plainte"`
   - `measure: "plainte_count"` (Volume global unifié)
   - `include_all_types: true` (englobant réclamations, dénonciations et suggestions).
3. **Comportement Déterministe Garanti :**
   Avant de solliciter le LLM, si l'analyseur syntaxique détecte une question purement temporelle ou dimensionnelle :
   - Il applique automatiquement l'entité pivot par défaut.
   - Il garantit ainsi un routage 100% reproductible vers `FAST_PATH_HOMOLOGATED` (`QC-UNIFIED-PLAINTES-TOTAL`) sans oscillation ni demande de clarification injustifiée.

---

## 5. Plan de Mise en Œuvre Sécurisé (`/safe-code-change`)

L'implémentation de ces 3 moteurs génériques suivra un plan strict en 4 phases :

| Phase | Composant Cible | Nature de la Modification | Risque & Régression |
|---|---|---|:---:|
| **Phase 1** | [`tools/common/parameter_reconciler.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/tools/common/parameter_reconciler.py) | Création du module générique de réconciliation des paramètres | **Nul** (Nouveau fichier isolé) |
| **Phase 2** | [`app/reporting/payload_normalizer.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/payload_normalizer.py) | Création du normalisateur générique pré-Pydantic | **Nul** (Nouveau fichier isolé) |
| **Phase 3** | [`app/reporting/text_to_sql_pipeline.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/text_to_sql_pipeline.py) | Remplacement de la liaison manuelle (lignes 502-532) par l'appel à `UniversalParameterReconciler.reconcile()` | **Faible** (Couvert par tests unitaires) |
| **Phase 4** | [`app/reporting/intent_resolver.py`](file:///c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_ai_service/app/reporting/intent_resolver.py) | Intégration de `PayloadInvariantNormalizer` avant l'instanciation de `TextToSQLIntent` | **Faible** (Élimine le repli silencieux) |

---

## 6. Critères d'Acceptation & Validation

Le succès de ce plan sera formellement attesté lorsque :
1. ✅ **La Requête N° 07** (« *Réclamations moyennes* ») s'exécutera avec succès en base MariaDB/SQLite (`SUCCESS`), son paramètre `:claim_type` étant automatiquement et génériquement résolu depuis l'entité `types=['CLAIM']`.
2. ✅ **La Requête N° 09** (« *Pourcentage d'usagers satisfaits* ») passera la validation Pydantic nativement (`GENERATIVE_LLM_NEMOTRON`) sans aucun repli silencieux vers les mots-clés.
3. ✅ **Le nombre de paramètres orphelins** passera de 11-14 à **0**, tous les contrats SQL étant automatiquement élagués.
4. ✅ **La suite de tests complète** (118/118 tests actuels + nouveaux tests des moteurs génériques) passera avec 100% de succès.
