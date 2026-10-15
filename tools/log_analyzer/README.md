# 🏛️ Analyseur de Logs & Détecteur d'Anomalies du Workflow Text-to-SQL

Cet outil autonome permet d'analyser, auditer et extraire automatiquement les **7 contrats formels** du Workflow Text-to-SQL Gouverné à partir des journaux d'exécution (fichiers de logs générés par `uvicorn` ou sessions de test).

Il est associé au **Skill Antigravity** [`gpr-ai-audit-log`](file:///C:/Users/HP/.gemini/config/skills/gpr-ai-audit-log/SKILL.md) et déclenchable via la commande slash :
```text
/gpr-ai-audit-log
```

---

## 🎯 Objectifs & Capacités

Pour chaque question utilisateur et chaque requête SQL traitée, l'outil extrait et contrôle rigoureusement :

1. **Étape 1 : Résolution d'Intention Canonique (`TextToSQLIntent`)**
   - Extraction du contrat JSON complet : `status`, `entity`, `measure`, `dimensions`, `filters`, `time`.
   - Détection des **replis silencieux** causés par des erreurs Pydantic (`SILENT_FALLBACK_INTENT`).
   - Contrôle d'amnésie ou d'hallucination temporelle.

2. **Étape 2 : Circuit Fast-Path & Candidate-Path**
   - Aiguillage formel : `FAST_PATH_HOMOLOGATED`, `CANDIDATE_PATH_PENDING`, ou `GENERATIVE_LLM`.
   - Détection des **désynchronisations temporelles** (`TEMPORAL_MISMATCH_CANDIDATE`) : réutilisation de requêtes en attente sans dates pour des questions spécifiant une période.
   - Cohérence du libellé métier homologué par rapport à la question posée.

3. **Étape 3 : Extraction du Sous-Schéma Minimal**
   - Tables autorisées minimales injectées dans le prompt.
   - Contrôle strict anti-fuite de données personnelles (`PII_LEAK_IN_PROMPT`) : exclusion garantie de `client_code`, `content`, `solution`, `motif_rejet`.

4. **Étape 4 : Générateur SQL Gouverné (`TextToSQLCandidate`)**
   - Contrat JSON brut émis par le modèle Nemotron.
   - Détection des **replis silencieux** vers le fallback déterministe (`SILENT_FALLBACK_CANDIDATE`) suite aux erreurs Pydantic (ex: types SQL `double`, `varchar` non autorisés).
   - **Détection des divergences SQL** entre le SQL proposé par le LLM et le SQL réellement compilé/exécuté (`RAW_VS_CANDIDATE_SQL_DIVERGENCE`).
   - Identification des **paramètres orphelins** (`ORPHAN_PARAMETERS`) déclarés dans le contrat mais omis dans la clause SQL.
   - Anti-patterns et requêtes rejetées passées injectées dans le prompt.

5. **Étape 5 : Bouclier de Sécurité AST SQLglot (`SqlValidationResult`)**
   - Validation syntaxique et sécurité AST (`AST_VALIDATION_FAILED`) : `SELECT` pur, projection stricte, aucune mutation (`INSERT`, `UPDATE`, `DELETE`, `DROP`).

6. **Étape 6 : Exécution SQL Sécurisée & Cycle de Vie**
   - Statut d'exécution MariaDB/MySQL (`SUCCESS` vs erreurs BDD).
   - Cardinalité (nombre de lignes) et latence d'exécution (ms).
   - Enregistrement dans le catalogue avec son empreinte SHA256 et statut du cycle de vie (`PENDING`, `APPROVED`).

7. **Étape 7 : Restitution, Synthèse & Payload Frontend (`ReportingResponse`)**
   - Type de visualisation (`stat`, `bar`, `pie`, `line`).
   - Synthèse textuelle en français.
   - Détection des **incohérences sémantiques** (`SEMANTIC_SYNTHESIS_CORRUPTED`) : alerte si un comptage brut issu d'un fallback est restitué sous le nom d'une autre métrique.

---

## 🚀 Utilisation en Ligne de Commande (CLI)

Depuis le dossier racine `gpr_ai_service` :

```powershell
# 1. Audit complet avec génération du rapport Markdown détaillé et export JSON
python tools/log_analyzer/cli.py "chemin/vers/fichier_de_logs.txt" --report tools/log_analyzer/rapport_audit.md --json tools/log_analyzer/audit_data.json

# 2. Filtrer uniquement les requêtes ayant des divergences ou des anomalies critiques
python tools/log_analyzer/cli.py "chemin/vers/fichier_de_logs.txt" --divergences-only

# 3. Inspecter en détail l'intégralité des 7 contrats pour une requête spécifique (ex: Run 15)
python tools/log_analyzer/cli.py "chemin/vers/fichier_de_logs.txt" --run 15
```

---

## 📂 Architecture des Fichiers

```text
tools/log_analyzer/
├── __init__.py           # Point d'entrée package
├── analyzer.py           # Moteur d'extraction regex et logique de détection des 7 contrats
├── cli.py                # Interface en ligne de commande (supporte --run, --report, --json, --divergences-only)
└── README.md             # Documentation et guide d'extension
```

Le skill associé est installé dans :
- [`C:\Users\HP\.gemini\config\skills\gpr-workflow-audit\SKILL.md`](file:///C:/Users/HP/.gemini/config/skills/gpr-workflow-audit/SKILL.md)
