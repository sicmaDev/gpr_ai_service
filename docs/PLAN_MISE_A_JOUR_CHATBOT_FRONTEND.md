# 📋 Plan d'Implémentation : Mise à Jour du Chatbot Décisionnel (Priorité Interface - Phase 1)

> **Document de Cadrage Opérationnel**  
> **Cible** : Interface Frontend du Chatbot de Reporting ([`AiReporting.js`](../../gpr_client_sicma_new_version/src/pages/Rapports/AiReporting.js), [`AiQueryVisualization.jsx`](../../gpr_client_sicma_new_version/src/pages/Rapports/AiQueryVisualization.jsx), [`AiReportingApi.js`](../../gpr_client_sicma_new_version/src/apis/IA/AiReportingApi.js)).  
> **Conformité** : Section 5 de [`INTERFACE_REPORTING_IA.md`](./INTERFACE_REPORTING_IA.md) et contrats validés du moteur Text-to-SQL Gouverné (`POST /reporting/query`, `POST /reporting/feedback`).

---

## 1. 🎯 Objectifs de la Phase 1 (Interface Frontend)

L'interface du Chatbot existe déjà dans la branche `develop-v1.5.0-ai-rapport` (`AiReporting.js` avec dialogue modal, saisie vocale et rendu Chart.js).  
L'objectif de cette **Phase 1** est de **mettre à jour ce composant existant** pour le connecter aux fonctionnalités avancées du nouveau moteur Text-to-SQL Gouverné :

1. **Intégration du Feedback Utilisateur (👍 / 👎)** :
   * Prise en compte du `query_id` retourné par le backend.
   * Ajout des boutons de vote d'utilité pour actionner la boucle d'auto-apprentissage continu.
2. **Connexion API `POST /reporting/feedback`** :
   * Implémentation de `sendReportingFeedback()` dans `AiReportingApi.js`.
3. **Badges de Traçabilité et Certification** :
   * Distinguer visuellement les requêtes *Fast-Path Homologuées* (`QC-CLAIM-...`) des requêtes *Auto-Apprises* (`QC-AUTO-...`).
4. **Gestion Ergonomique des Retours de Clarification & Sécurité** :
   * Rendu visuel soigné lorsque l'IA demande une précision temporelle ou bloque une tentative non autorisée.
5. **Alignement des Suggestions Rapides** :
   * Mise à jour des questions suggérées avec le catalogue réel homologué.

---

## 2. 🗂️ Fichiers Concernés

```text
gpr_client_sicma_new_version/ (branche develop-v1.5.0-ai-rapport)
├── src/apis/IA/
│   └── AiReportingApi.js           # Ajout de sendReportingFeedback(queryId, rating, comment)
└── src/pages/Rapports/
    ├── AiReporting.js              # Mise à jour de la carte réponse (Feedback 👍/👎, badges, statuts)
    ├── AiQueryVisualization.jsx   # Préservation du sélecteur de graphiques et Chart.js
    └── aiReportingUtils.js         # Normalisation des nouveaux champs (query_id, status)
```

---

## 3. 📝 Découpage Détaillé des Tâches (Phase 1)

### Étape 1.1 : Service API Frontend (`src/apis/IA/AiReportingApi.js`)
* Ajouter la méthode :
  ```javascript
  export const sendReportingFeedback = async (queryId, rating, comment = null) => {
      const response = await axios.post(
          `${AI_SERVICE_URL}/reporting/feedback`,
          { query_id: queryId, rating, comment },
          { headers: authHeaders(), timeout: 15000 }
      );
      return response.data;
  };
  ```

### Étape 1.2 : Normalisation & État Local (`src/pages/Rapports/aiReportingUtils.js` & `AiReporting.js`)
* Adapter `normalizeQueryResponse(data)` pour extraire :
  * `query_id` (identifiant unique de la requête pour le feedback).
  * `isClarification` (détection si la réponse est une demande de précision).
* Ajouter dans l'état de `AiReporting.js` :
  * `feedbackSubmitted` : booléen pour mémoriser si l'utilisateur a voté sur la réponse courante.
  * `feedbackLoading` : état de chargement pendant l'appel API de feedback.

### Étape 1.3 : Carte de Réponse Enrichie dans `AiReporting.js`
* **Badge de Certification** au-dessus de la réponse :
  * Si `query_id` commence par `QC-AUTO-` : `<Chip label="Requête Auto-Apprise" color="info" size="small" />`
  * Si `query_id` est homologué : `<Chip label="Requête Certifiée (Fast-Path)" color="success" size="small" />`
* **Zone d'Évaluation (Pouce Haut / Pouce Bas)** sous le graphique :
  ```jsx
  {answer.query_id && (
      <Box sx={{ mt: 2, pt: 1.5, borderTop: "1px solid #e2e8f0", display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
              Cette réponse vous a-t-elle été utile ?
          </Typography>
          <IconButton size="small" onClick={() => handleFeedback("POSITIVE")} disabled={feedbackSubmitted || feedbackLoading} color={userRating === "POSITIVE" ? "primary" : "default"}>
              <ThumbUpIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" onClick={() => handleFeedback("NEGATIVE")} disabled={feedbackSubmitted || feedbackLoading} color={userRating === "NEGATIVE" ? "error" : "default"}>
              <ThumbDownIcon fontSize="small" />
          </IconButton>
          {feedbackSubmitted && (
              <Typography variant="caption" color="success.main" sx={{ ml: 1 }}>
                  ✓ Merci pour votre retour !
              </Typography>
          )}
      </Box>
  )}
  ```

### Étape 1.4 : Actualisation des Suggestions Rapides
* Mettre à jour `questionSuggestions` dans `AiReporting.js` :
  * *« Nombre de réclamations par agence en 2026 »*
  * *« Répartition des réclamations par canal »*
  * *« Taux de respect des délais de traitement »*
  * *« Combien de plaintes graves enregistrées ? »*
  * *« Quels produits génèrent le plus de réclamations ? »*

---

## 4. 🔄 Phases Ultérieures (Rappel)

* **Phase 2 (Backend)** : Connexion de la génération de la synthèse textuelle `answer` par le LLM (Nemotron) à partir des données SQL réelles dans `response_builder.py`.
* **Phase 3 (Validation E2E)** : Recette bout en bout (Question front $\rightarrow$ SQL FastAPI $\rightarrow$ Affichage graphique $\rightarrow$ Feedback 👍/👎 $\rightarrow$ Audit).

---

## 5. ✅ Critères d'Acceptation de la Phase 1

1. Le chatbot existant (`AiReporting.js`) transmet correctement la question à `POST /reporting/query`.
2. Le `query_id` est capturé et conservé dans l'état de la réponse.
3. Le badge de certification de la requête s'affiche correctement.
4. Les boutons d'évaluation 👍 / 👎 appellent `sendReportingFeedback()` vers `POST /reporting/feedback`.
5. Un message de remerciement confirme la prise en compte du vote et empêche les doubles votes.
6. L'affichage des graphiques Chart.js et la saisie vocale continuent de fonctionner sans aucune régression.
