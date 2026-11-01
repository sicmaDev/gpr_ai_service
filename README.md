# GPR AI Service

Micro-service d'Intelligence Artificielle pour la **Gestion des Plaintes et Réclamations (GPR)**. Il expose une API REST permettant d'analyser automatiquement des plaintes clients et de générer des propositions de solutions via un pipeline RAG (Retrieval-Augmented Generation).

---

## Fonctionnalités

- **Analyse NLP** : détection du sentiment, du niveau d'urgence et des mots-clés sensibles dans un texte de plainte
- **Recherche sémantique** : retrouve les plaintes historiques les plus similaires grâce à FAISS et des embeddings multilingues
- **Génération de solution** : produit une réponse personnalisée en s'appuyant sur les solutions historiques, via un LLM local (Ollama)

---

## Stack technique

| Composant | Technologie |
|---|---|
| Framework API | FastAPI + Uvicorn |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (SentenceTransformers) |
| Index vectoriel | FAISS (IndexFlatL2) |
| Analyse sentiment | TextBlob |
| LLM local | Ollama — modèle `llama3.2:1b` |
| Validation données | Pydantic |

---

## Prérequis

- Python 3.10+
- [Ollama](https://ollama.com/) installé et en cours d'exécution
- Le modèle LLM téléchargé :

```bash
ollama pull llama3.2:1b
```

---

## Installation

```bash
# Cloner le projet
git clone <url-du-repo>
cd gpr_ai_service

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Installer les dépendances
pip install -r requirements.txt
```

---

## Lancement

```bash
python main.py
```

Le service démarre localement sur `http://localhost:8001` et est déployé en ligne sur `https://ai.gprsicma.gprserver.com`.

Pour vérifier que tout fonctionne :

```bash
# En local :
curl http://localhost:8001/
# En production :
curl https://ai.gprsicma.gprserver.com/
```

Réponse attendue :

```json
{
  "status": "ok",
  "service": "GPR Web IA Service",
  "version": "1.0.0"
}
```

---

## Endpoints

### `POST /analyze/`

Analyse NLP d'un texte de plainte.

**Corps de la requête :**

```json
{
  "texte": "Bonjour, je constate des frais injustifiés sur mon compte depuis trois mois !"
}
```

**Réponse :**

```json
{
  "urgence": "MOYEN",
  "sentiment": "negatif",
  "mots_cles_detectes": ["fraude", "urgence"],
  "resume": "Constatation de frais injustifiés depuis trois mois."
}
```

| Champ | Valeurs possibles |
|---|---|
| `urgence` | `MINEUR`, `MOYEN`, `GRAVE` |
| `sentiment` | `neutre`, `negatif`, `tres_negatif` |

---

### `POST /search/`

Recherche sémantique dans l'historique et génération d'une solution via le LLM.

**Corps de la requête :**

```json
{
  "texte_actuel": "Mon virement n'est toujours pas arrivé après 5 jours.",
  "categorie": "Frais bancaires"
}
```

> `categorie` est optionnel. Si fourni, les résultats sont filtrés par catégorie.

**Réponse :**

```json
{
  "message": "Nous avons bien pris note de votre situation...",
  "resultats_trouves": 3,
  "similar_claims": [
    {
      "score_similarite": 0.12,
      "id_historique": 1003,
      "categorie": "Frais bancaires",
      "statut": "SATISFIED",
      "texte_original": "...",
      "solution_suggeree": "..."
    }
  ]
}
```

> Note : le `score_similarite` est une distance L2 — **plus il est bas, plus la similarité est élevée**.

---

## Structure du projet

```
gpr_ai_service/
├── main.py                        # Point d'entrée FastAPI
├── requirements.txt
└── app/
    ├── routers/
    │   ├── analyze.py             # Route POST /analyze/
    │   └── search.py              # Route POST /search/
    ├── services/
    │   ├── nlp_service.py         # Analyse sentiment, urgence, résumé
    │   ├── vector_service.py      # FAISS : indexation et recherche
    │   └── llm_service.py         # Génération via Ollama
    └── data/
        └── plaintes_fictives.json # Données de test (10+ plaintes mockées)
```

---

## Données de test

Le fichier `app/data/plaintes_fictives.json` contient des plaintes fictives couvrant plusieurs catégories :

- Frais bancaires
- Fraude / Carte Bancaire
- Assurance / Sinistre
- Application Mobile
- Crédit Immobilier
- Service Client / Agence
- Moyen de paiement

Ces données alimentent l'index FAISS au démarrage du service. Pour utiliser de vraies données, remplacez ce fichier en respectant le schéma suivant :

```json
{
  "id": 1001,
  "date_creation": "2024-01-15T10:30:00Z",
  "objet_categorie": "Frais bancaires",
  "texte_plainte": "...",
  "texte_solution": "...",
  "statut_final": "SATISFIED",
  "niveau_urgence": "MINEUR"
}
```

---

## Notes pour le développement

- **CORS** : actuellement ouvert à toutes les origines. À restreindre avant une mise en production.
- **LLM** : Ollama doit tourner en local. Si indisponible, l'endpoint `/search/` retourne un message d'erreur explicite sans planter.
- **`.pyc`** : ajouter un `.gitignore` avec `__pycache__/` pour ne pas versionner les fichiers compilés Python.
- **Pas de base de données** : l'index FAISS est recréé en mémoire à chaque démarrage. Une intégration avec la base Java Spring Boot est prévue.
