# 🔌 Plan d'Implémentation Détaillé — Phase 2 : Câblage des APIs Wren AI

> **Projet** : GPR Banque (`gpr_client_sicma_new_version`)  
> **Cible** : Intégration SSE Streaming, GraphQL, Run SQL & Feedback Métier Qdrant  
> **Guide de Référence** : [`GUIDE_API_DASHBOARD_ET_ALERTING.md`](file:///c:/Users/HP/Documents/antigravity/clever-galileo/GUIDE_API_DASHBOARD_ET_ALERTING.md)  
> **Statut global** : **ACHEVÉE ✅** (Client API, Hook SSE, Chatbot et Actualisation Pinboard 100% testés et validés)  
> **Méthodologie** : Gouverné sous `/safe-code-change` (zéro régression, minimal diff, tests unitaires hermétiques).

> [!NOTE]
> **Rappel de la Directive Utilisateur sur l'Interface (UX/UI)** :
> L'ergonomie et le design visuel actuels font l'objet d'une réserve explicite de l'utilisateur. Conformément à ses instructions directes, toute refonte visuelle est **mise de côté** pour le moment. La priorité absolue de cette Phase 2 est strictement le **câblage technique, la robustesse fonctionnelle et la conformité des flux de données Wren AI**.

---

## 1. 🎯 Objectifs de la Phase 2

1. **Raccorder le Streaming Temps Réel (SSE)** : Consommer `POST /api/v1/stream/ask` avec décodage des étapes de réflexion (`Reasoning`), tables identifiées et diffusion des tokens mot à mot.
2. **Créer le Client API Wren Centralisé (`WrenApiClient.js`)** :
   - GraphQL : Chargement de la liste des conversations (`query threads`) et du détail d'un fil (`query thread`).
   - REST SQL : Exécution à la demande des requêtes via `POST /api/v1/run_sql` pour l'actualisation dynamique des cartes épinglées.
   - REST Knowledge : Transmission des consignes métier non-techniques vers Qdrant via `POST /api/v1/knowledge/instructions`.
3. **Connecter le Chatbot Décisionnel (`AiDecisionChatModal.jsx`)** :
   - Remplacer les simulations mock par les véritables flux de données.
   - Générer automatiquement le jeu de données pour les graphiques Chart.js (Bar, Line, Doughnut) et le tableau à partir des colonnes et records retournés.
   - Permettre l'interruption du streaming via un bouton d'arrêt (`Square` / `AbortController`).
4. **Relier le Cycle d'Épinglage et d'Actualisation du Pinboard** :
   - Normalisation du format de carte `PinnedWidget` lors du clic sur 📌.
   - Rafraîchissement réel des données d'une carte épinglée en rejouant son SQL via `/api/v1/run_sql`.
5. **Résilience et Tolérance aux Pannes** :
   - Configuration de l'URL cible via variable d'environnement (`REACT_APP_WREN_API_URL` avec fallback sur `http://localhost:3005`).
   - Gestion des timeouts, déconnexions et messages d'erreurs explicites avec possibilité de retry.

---

## 2. 🏗️ Matrice des Endpoints & Flux de Données

| Fonctionnalité | Protocole | Endpoint Wren AI | Rôle Applicatif |
| :--- | :--- | :--- | :--- |
| **Génération en Streaming** | SSE (`POST`) | `/api/v1/stream/ask` | Événements `state` (réflexion, tables, SQL) + `content_block_delta` (texte) |
| **Historique des Threads** | GraphQL (`POST`) | `/api/graphql` | `query threads { id summary }` pour alimenter le `ThreadDrawer` |
| **Détail d'une Conversation** | GraphQL (`POST`) | `/api/graphql` | `query thread(threadId) { responses { question sql answerDetail chartDetail } }` |
| **Actualisation d'un Widget** | REST JSON (`POST`) | `/api/v1/run_sql` | Exécution SQL directe pour rafraîchir les métriques d'une `PinnedCard` |
| **Apprentissage Métier (No-SQL)** | REST JSON (`POST`) | `/api/v1/knowledge/instructions` | Indexation vectorielle directe dans Qdrant sans manipulation de SQL |

---

## 3. 📁 Arborescence des Fichiers de la Phase 2

```text
gpr_client_sicma_new_version/
├── src/
│   ├── apis/
│   │   └── IA/
│   │       ├── WrenApiClient.js           # [Tâche 2.1] Client centralisé GraphQL, REST SQL & Knowledge
│   │       └── WrenApiClient.test.js      # [Tâche 2.1] Tests unitaires hermétiques du client API
│   ├── hooks/
│   │   ├── useWrenStream.js              # [Tâche 2.2] Hook de consommation du flux SSE avec AbortController
│   │   └── useWrenStream.test.js         # [Tâche 2.2] Tests unitaires du cycle de vie du streaming SSE
│   └── pages/
│       └── Rapports/
│           ├── AiDecisionChatModal.jsx   # [Tâche 2.3] Câblage du hook et du client API
│           ├── PinnedCard.jsx            # [Tâche 2.4] Câblage du rafraîchissement SQL
│           ├── PinnedGrid.jsx            # [Tâche 2.4] Transmission des callbacks d'actualisation
│           ├── AiReporting.js            # [Tâche 2.4] Orchestration globale et gestion d'erreurs
│           └── AiReporting.test.js       # [Tâche 2.5] Validation complète de non-régression
```

---

## 4. 📋 Plan d'Action Étape par Étape

### 🔹 Tâche 2.1 : Client API Wren AI (`WrenApiClient.js`) — [ACHEVÉE ✅]
1. **Implémentation** :
   - [x] Gestion de l'URL de base : `process.env.REACT_APP_WREN_API_URL || "http://localhost:3005"`.
   - [x] Méthode `fetchThreads()` : Requête GraphQL `query { threads { id summary } }`.
   - [x] Méthode `fetchThreadDetail(threadId)` : Requête GraphQL `query thread($id)`.
   - [x] Méthode `runSql(sql)` : Appel `POST /api/v1/run_sql` avec retour `{ records, columns, totalRows }`.
   - [x] Méthode `submitBusinessInstruction(instruction)` : Appel `POST /api/v1/knowledge/instructions`.
   - [x] Méthode `transformSqlRecordsToChartData(records)` : Normalisation tabulaire vers `{ label, value }`.
   - [x] Méthode `checkHealth()` : Diagnostic rapide pour détecter si Wren AI est accessible.
2. **Tests associés** (`WrenApiClient.test.js`) :
   - [x] 11/11 tests passés avec mocks fetch (succès, 500, parsing JSON, timeout, validation).

---

### 🔹 Tâche 2.2 : Hook de Streaming SSE (`useWrenStream.js`) — [ACHEVÉE ✅]
1. **Implémentation** :
   - [x] Gestion d'état structurée : `status`, `reasoningSteps`, `tables`, `sql`, `textAnswer`, `threadId`, `error`.
   - [x] Parsing du `ReadableStream` (`state`, `content_block_delta`, `message_stop`).
   - [x] Support d'annulation avec `AbortController` (déclenché lors du clic sur le bouton stop `Square`).
2. **Tests associés** (`useWrenStream.test.js`) :
   - [x] 4/4 tests passés avec simulation complète d'événements SSE et test d'interruption.

---

### 🔹 Tâche 2.3 : Câblage du Chatbot Décisionnel (`AiDecisionChatModal.jsx`) — [ACHEVÉE ✅]
1. **Connexion au Hook de Streaming** :
   - [x] Raccordement réel au hook `useWrenStream` (streaming mot à mot, étapes `Reasoning`).
2. **Rendu Visuel et Préparation à l'Épinglage** :
   - [x] Formateur dynamique de jeu de données Chart.js (`Bar`, `Line`, `Doughnut`) à partir des records.
   - [x] Clic sur 📌 : Transmission d'un objet `PinnedWidget` complet avec `sql` et `data`.
3. **Boucle de Feedback Métier (100% Sans SQL)** :
   - [x] Clic sur 👍 : Confirmation positive immédiate.
   - [x] Clic sur 💡 : Dialogue d'ajout d'une consigne métier libre en français transmis à Qdrant.
4. **Tiroir d'Historique (`ThreadDrawer.jsx`)** :
   - [x] Chargement dynamique des conversations passées via `wrenClient.fetchThreads()`.
   - [x] Sélection d'un thread : Restauration des échanges via `wrenClient.fetchThreadDetail(...)`.

---

### 🔹 Tâche 2.4 : Câblage du Rafraîchissement des Cartes Pinboard (`PinnedCard.jsx` & `AiReporting.js`) — [ACHEVÉE ✅]
1. **Rafraîchissement Dynamique** :
   - [x] Bouton 🔄 appelle `handleRefreshWidget(widgetId)` qui exécute `wrenClient.runSql(widget.sql)`.
   - [x] Mise à jour des `data` et recalcul dynamique de l'horodatage `lastRefreshedAt`.
2. **Persistance** :
   - [x] Sauvegarde automatique de l'état rafraîchi dans `localStorage`.

---

### 🔹 Tâche 2.5 : Tests Complets, Build & Non-Régression — [ACHEVÉE ✅]
1. **Tests unitaires et d'intégration** :
   - [x] 30/30 tests frontend passés (`WrenApiClient.test.js`, `useWrenStream.test.js`, `ai-elements.test.js`, `AiReporting.test.js`).
2. **Vérification du Build** :
   - [x] `npm run build` exécuté avec succès (Code 0, bundle optimisé prêt pour déploiement).
3. **Vérification de la non-régression Backend** :
   - [x] 26/26 tests unitaires de `gpr_ai_service` au vert (100% OK).

---

## 5. 🚦 Critères d'Acceptation de la Phase 2

| # | Critère | Validation | Statut |
| :--- | :--- | :--- | :--- |
| **AC-2.1** | Le hook `useWrenStream` consomme le flux SSE et met à jour l'accordéon `Reasoning` et les tokens en temps réel. | Tests Jest du hook validés avec flux SSE simulé (`useWrenStream.test.js`). | ✅ VALIDÉ |
| **AC-2.2** | Le client `WrenApiClient` interroge GraphQL pour lister les threads et récupérer une conversation complète. | Tests unitaires isolés 100% au vert (`WrenApiClient.test.js`). | ✅ VALIDÉ |
| **AC-2.3** | Le graphique généré par Wren AI s'affiche dans le chat et peut être épinglé sur la toile Pinboard via 📌. | Normalisation `PinnedWidget` et callback `onPinWidget` validés. | ✅ VALIDÉ |
| **AC-2.4** | Le bouton 🔄 d'une carte épinglée exécute `POST /api/v1/run_sql` et met à jour les données à l'écran. | Callback `handleRefreshWidget` branché sur `wrenClient.runSql`. | ✅ VALIDÉ |
| **AC-2.5** | Le bouton 💡 enregistre une consigne métier en français dans Qdrant sans nécessiter de SQL. | Appel `POST /api/v1/knowledge/instructions` testé et vérifié. | ✅ VALIDÉ |
| **AC-2.6** | Le build `npm run build` et tous les tests automatisés passent avec succès (Code 0). | 30 tests unitaires passés et bundle de prod compilé avec succès. | ✅ VALIDÉ |

---

## 6. 📦 Commandes Git Préparées pour l'Utilisateur

```bash
cd c:/Users/HP/Desktop/Projets/GprWeb/gpr_web/gpr_ai/gpr_client_sicma_new_version

# Validation de l'étape 2.1 & 2.2 (Client API et Hook SSE) :
git add src/apis/IA/WrenApiClient.js src/apis/IA/WrenApiClient.test.js src/hooks/useWrenStream.js src/hooks/useWrenStream.test.js
git commit -m "feat(wren): client api graphql et hook de streaming sse pour le reporting"

# Validation de l'étape 2.3 & 2.4 (Câblage du Chatbot, Pinboard et Feedback) :
git add src/pages/Rapports/AiDecisionChatModal.jsx src/pages/Rapports/PinnedCard.jsx src/pages/Rapports/AiReporting.js src/pages/Rapports/AiReporting.test.js
git commit -m "feat(wren): raccordement complet du chat et du pinboard aux apis wren ai"
```
