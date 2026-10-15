# Outil d'Interrogation du Workflow de Reporting IA (Text-to-SQL Gouverné)

Cet outil permet d'interroger le service de reporting analytique question par question, de tester unitairement ou par lot l'ensemble des scénarios de test (P1.1 à P1.5), et d'auditer l'intégralité du pipeline Text-to-SQL (Intention canonique, Fast-Path, Génération SQL, Validation AST, Exécution et Restitution).

---

## 🚀 Modes d'Utilisation

### 1. Mode Interactif Pas-à-Pas (Recommandé pour les tests manuels)
Permet de naviguer question par question avec un prompt à chaque étape :
```bash
python tools/workflow_interrogator/cli.py
```
Options disponibles à chaque question :
- `[Entrée]` : Exécuter la question courante
- `[s]` : Sauter la question
- `[c]` : Saisir une question personnalisée à la volée
- `[q]` : Quitter la session

---

### 2. Exécution d'un Sous-Step Spécifique
Pour cibler un sous-step particulier du plan de test :
```bash
# Tester uniquement le mappage d'entité (P1.1-A à P1.1-E)
python tools/workflow_interrogator/cli.py --scenario P1.1

# Tester la déduction de mesure (P1.2)
python tools/workflow_interrogator/cli.py --scenario P1.2

# Tester les dimensions (P1.3)
python tools/workflow_interrogator/cli.py --scenario P1.3

# Tester les filtres explicites (P1.4)
python tools/workflow_interrogator/cli.py --scenario P1.4

# Tester les périodes temporelles (P1.5)
python tools/workflow_interrogator/cli.py --scenario P1.5
```

---

### 3. Exécution d'une Seule Question Spécifique
Par son numéro d'identifiant (1 à 24) :
```bash
python tools/workflow_interrogator/cli.py --id 7
```

Ou en passant une question en langage naturel libre :
```bash
python tools/workflow_interrogator/cli.py --question "Réclamations graves par agence en mars 2026"
```

---

### 4. Exécution Complète avec Génération de Rapport
Exécute les 24 questions à la suite et génère un rapport Markdown complet :
```bash
python tools/workflow_interrogator/cli.py --all --report rapport_complet.md --json resultats.json
```

---

## ⚙️ Options et Paramètres

| Option | Description | Exemple |
| :--- | :--- | :--- |
| `--all` | Exécute toutes les 24 questions du catalogue | `python tools/workflow_interrogator/cli.py --all` |
| `--scenario <PREFIX>` | Filtre par scénario (`P1.1`, `P1.2`, `P1.3`, `P1.4`, `P1.5`) | `--scenario P1.3` |
| `--id <N>` | Exécute la question numéro N | `--id 1` |
| `--question "<TEXTE>"` | Question personnalisée libre | `--question "Total des plaintes"` |
| `--sqlite` | Force une base SQLite en mémoire isolée avec données d'essai | `--sqlite` |
| `--http <URL>` | Interroge via l'API HTTP FastAPI (plutôt qu'en interne) | `--http http://localhost:8000` |
| `--no-llm` | Désactive le LLM pour tester le repli supervisé déterministe | `--no-llm` |
| `--report <PATH.md>` | Exporte un rapport Markdown détaillé | `--report audit_run.md` |
| `--json <PATH.json>` | Exporte les résultats bruts au format JSON | `--json run.json` |

---

## 📊 Informations Affichées par Question

Pour chaque question exécutée, l'outil affiche :
1. **🎯 Intention Canonique Résolue** : Concept d'entité, types de dossiers, mesure demandée, dimensions, filtres, verrou temporel.
2. **⚡ Circuit & Performance** : Mode d'exécution (`FAST_PATH_HOMOLOGATED`, `CANDIDATE_PENDING`, `GENERATIVE_LLM`, `SUPERVISED_FALLBACK`), Query ID persistant, lignes retournées, temps d'exécution en ms.
3. **📜 Requête SQL Exécutée** : Requête SQL exacte exécutée sur la base de données.
4. **💬 Synthèse de Restitution** : Réponse analytique formulée pour l'utilisateur.
