# Plan front Reporting IA

## Objectif

Construire et stabiliser l’interface front de Reporting IA sans modifier le backend Spring Boot ni le microservice FastAPI. L’objectif est d’avoir une page fiable, cohérente et utilisable avant la mise en production du contrat IA final.

## Phase 1 — Stabiliser la structure existante

### Fichiers concernés
- src/pages/Rapports/AiReporting.js
- src/apis/IA/AiReportingApi.js
- src/pages/Rapports/AiReportingCharts.js

### Travaux
- Vérifier la gestion du token d’authentification.
- Centraliser les messages d’erreur.
- Gérer les états suivants :
  - chargement initial ;
  - actualisation ;
  - données vides ;
  - erreur API ;
  - timeout ;
- Empêcher les requêtes simultanées inutiles.
- Ajouter une validation cohérente des dates.
- Conserver les filtres lors d’une actualisation.

### Résultat attendu
La page reste fonctionnelle même si le service IA est indisponible ou si la réponse est vide.

---

## Phase 2 — Définir le contrat d’affichage front

### Format attendu côté front

```js
{
  metrics: {
    total_claims: 0,
    high_risk_claims: 0,
    anomalies: 0,
    active_alerts: 0
  },
  charts: {
    evolution: [],
    distribution: [],
    categories: [],
    risks: []
  },
  recommendations: [],
  alerts: [],
  generated_at: null
}
```

### Travaux
- Créer des fonctions de normalisation front, par exemple :
  - normalizeDashboardResponse
  - normalizeMetric
  - normalizeChartData
  - normalizeAlert
  - normalizeRecommendation
- Accepter proprement :
  - valeurs absentes ;
  - valeurs nulles ;
  - réponses incomplètes ;
  - petits écarts de format côté API.

---

## Phase 3 — Améliorer les filtres

### Filtres prioritaires
- date de début ;
- date de fin ;
- type de dossier ;
- agence ;
- canal ;
- catégorie ;
- niveau de risque.

### Interface recommandée
- filtres principaux visibles directement ;
- filtres avancés dans un panneau repliable ;
- boutons :
  - Appliquer ;
  - Réinitialiser ;
- affichage des filtres actifs sous forme de chips.

### Comportement
Les filtres ne doivent pas déclencher une requête à chaque frappe. La requête doit être lancée uniquement après clic sur Appliquer.

---

## Phase 4 — Revoir les cartes KPI

### Objectif
Améliorer la lisibilité et fournir du contexte métier.

### Cartes à prévoir
- Dossiers analysés ;
- Dossiers à risque élevé ;
- Anomalies détectées ;
- Alertes actives.

### Améliorations suggérées
- titre ;
- valeur principale ;
- icône ;
- couleur selon le type d’indicateur ;
- évolution par rapport à la période précédente ;
- description courte ;
- éventuellement un lien vers le détail.

### Couleurs recommandées
- bleu : volume ;
- rouge : risque ;
- orange : anomalie ;
- violet / jaune : alerte.

---

## Phase 5 — Compléter les graphiques

### Graphiques à prévoir
1. Évolution des dossiers dans le temps
2. Répartition par statut
3. Répartition par canal
4. Répartition par catégorie
5. Évolution des risques
6. Nombre d’anomalies par période
7. Top des catégories à surveiller

### Améliorations UX
- légendes claires ;
- tooltips avec valeurs formatées ;
- message lorsqu’il n’y a aucune donnée ;
- mode responsive ;
- bouton pour masquer/afficher une série ;
- titre et source de chaque indicateur.

---

## Phase 6 — Ajouter les vues détaillées

### Objectif
Permettre à l’utilisateur de comprendre les chiffres affichés.

### À ajouter
- bouton Voir le détail sur les KPI ;
- tableau des alertes ;
- tableau des anomalies ;
- détail d’une catégorie ;
- détail des dossiers à risque élevé ;
- filtres appliqués dans chaque vue.

### Format conseillé
- Dialog Material UI ;
- ou panneau latéral ;
- ou vue secondaire dédiée.

---

## Phase 7 — Améliorer les recommandations et alertes

### Recommandations
Chaque recommandation doit afficher :
- titre ;
- description ;
- niveau de priorité ;
- catégorie concernée ;
- indicateur source ;
- date de génération ;
- statut : nouvelle, consultée ou traitée.

### Alertes
Chaque alerte doit afficher :
- gravité ;
- titre ;
- description ;
- date ;
- source ;
- action recommandée ;
- bouton Voir les dossiers concernés.

### Niveaux recommandés
- critical
- high
- medium
- low

---

## Phase 8 — Améliorer la requête en langage naturel

### Interface
Ajouter :
- exemples de questions ;
- indicateur de traitement ;
- historique des dernières questions ;
- possibilité de vider la réponse ;
- affichage des filtres utilisés pour la question ;
- réponse structurée.

### Réponse multimodale obligatoire
L'analyse IA ne doit pas être limitée à une réponse textuelle. Selon la question,
elle doit pouvoir retourner automatiquement une visualisation adaptée :

- courbe (`line`) pour une évolution temporelle ;
- barres (`bar`) pour une comparaison ;
- anneau ou camembert (`doughnut` / `pie`) pour une répartition ;
- éventuellement aire (`area`) pour une tendance cumulée.

Le contrat d'affichage attendu côté front peut prendre la forme suivante :

```js
{
  answer: "Les réclamations augmentent depuis trois mois.",
  summary: "Hausse principalement portée par les moyens de paiement.",
  visualization: {
    type: "line",
    title: "Évolution mensuelle des réclamations",
    labels: ["Janvier", "Février", "Mars"],
    datasets: [
      {
        label: "Réclamations",
        data: [120, 145, 180]
      }
    ]
  },
  data: [],
  sources: [],
  filters_used: {}
}
```

Créer un composant front dédié, par exemple `AiQueryVisualization`, qui :

- valide la structure de `visualization` ;
- sélectionne automatiquement le composant Chart.js approprié ;
- affiche le graphique sous la réponse textuelle ;
- affiche le tableau de données en complément si nécessaire ;
- fournit un état vide pour une visualisation absente ou invalide ;
- ne bloque pas l'affichage de la réponse textuelle si le graphique ne peut pas être rendu.

### Données à afficher
Chaque réponse peut fournir :
- réponse textuelle ;
- résumé ;
- graphique généré automatiquement ;
- tableau complémentaire ;
- données sources ;
- filtres appliqués.

---

## Phase 9 — Ajouter l’export front

### Formats possibles
- CSV ;
- Excel ;
- PDF ;
- image des graphiques.

### Priorité recommandée
1. export CSV des tableaux ;
2. export PDF du rapport ;
3. export image des graphiques.

### Règles
- respecter les filtres actifs ;
- respecter la période sélectionnée ;
- afficher la date de génération ;
- exporter les indicateurs visibles.

---

## Phase 10 — Internationalisation et responsive design

### Travaux
- déplacer les textes dans les fichiers de traduction ;
- prévoir français et anglais ;
- vérifier l’affichage sur :
  - grand écran ;
  - tablette ;
  - mobile ;
- éviter les tableaux illisibles sur petits écrans ;
- vérifier les contrastes et les tailles de texte.

---

## Ordre de réalisation recommandé

### Sprint 1 — Fiabilité
- états de chargement, erreur et vide ;
- normalisation des réponses ;
- correction du client API ;
- validation des filtres.

### Sprint 2 — Filtres et KPI
- filtres avancés ;
- application manuelle des filtres ;
- nouvelles cartes KPI ;
- tendances et couleurs.

### Sprint 3 — Graphiques
- risques ;
- anomalies ;
- canaux ;
- catégories ;
- responsive design.

### Sprint 4 — Détails
- tableaux détaillés ;
- dialogues ;
- alertes enrichies ;
- recommandations enrichies.

### Sprint 5 — Interaction IA
- requêtes naturelles améliorées ;
- exemples de questions ;
- historique ;
- réponses structurées.

### Sprint 5.1 — Visualisations IA dynamiques
- définir le contrat `visualization` ;
- créer le composant `AiQueryVisualization` ;
- prendre en charge les types `line`, `bar`, `doughnut`, `pie` et `area` ;
- afficher automatiquement les graphiques retournés par l'analyse IA ;
- afficher les données tabulaires en complément ;
- ajouter des données mock avec plusieurs types de graphiques ;
- gérer les visualisations absentes, invalides ou incomplètes ;
- vérifier le responsive des graphiques dans les réponses.

### Sprint 6 — Finalisation
- exports ;
- traductions ;
- accessibilité ;
- tests ;
- build de production.

---

## Refonte visuelle selon les maquettes

### Objectif

Faire évoluer le Reporting IA vers un dashboard de pilotage décisionnel
professionnel, avec une présentation claire des indicateurs, risques, alertes,
anomalies et recommandations.

### Principes visuels

- fond gris très clair et cartes blanches ;
- bordures fines, coins arrondis et ombres discrètes ;
- grille responsive et espacements réguliers ;
- couleur principale bleu/violet ;
- vert pour les situations mineures ou résolues ;
- orange pour les risques moyens et la surveillance ;
- rouge/rose pour les situations graves ou critiques ;
- titres lisibles, sous-titres secondaires et valeurs KPI mises en avant.

### Nouvelle structure du dashboard

1. En-tête et période analysée ;
2. filtres globaux ;
3. cartes KPI ;
4. évolution des plaintes ;
5. répartition par canal et produit ;
6. performance des traitements ;
7. score et matrice de risque ;
8. centre d'alertes intelligentes ;
9. détection d'anomalies ;
10. recommandations stratégiques IA ;
11. assistant IA flottant.

### Composants visuels réutilisables

Créer et réutiliser les composants suivants :

```text
AiDashboardCard
AiMetricCard
AiChartCard
AiRiskScore
AiRiskMatrix
AiAlertCard
AiAnomalyCard
AiRecommendationCard
AiAssistantPanel
AiFilterBar
AiStatusBadge
AiEmptyState
```

### Blocs fonctionnels à intégrer

#### KPI

Ajouter les indicateurs suivants :

- total des plaintes ;
- plaintes graves ;
- plaintes résolues ;
- délai moyen de traitement ;
- score de satisfaction ;
- anomalies détectées ;
- alertes actives.

Chaque carte doit afficher le libellé, l'icône, la valeur, l'évolution,
la comparaison avec la période précédente et une couleur métier.

#### Évolution des plaintes

Afficher un graphique en courbes ou en aire avec :

- volume total ;
- plaintes graves ;
- plaintes résolues ;
- évolution hebdomadaire ou mensuelle ;
- tooltips et légende.

#### Répartitions

- graphique en anneau pour les canaux : agence, mobile, email, web et téléphone ;
- barres horizontales triées pour les produits : crédit, épargne, cartes,
  mobile banking et assurance ;
- affichage des valeurs et pourcentages dans les légendes ou tooltips.

#### Performance des traitements

Ajouter un graphique en barres groupées par équipe avec :

- dossiers reçus ;
- dossiers résolus ;
- taux de résolution ;
- équipe la plus performante ;
- équipe en dépassement.

#### Risques

Ajouter :

- score de risque global sous forme d'anneau ;
- répartition mineur, moyen et grave ;
- matrice de risque avec volume, évolution et action recommandée ;
- mention obligatoire : « Le score IA est indicatif et les cas sensibles
  nécessitent une validation humaine. »

#### Alertes intelligentes

Remplacer les alertes simples par des cartes comprenant :

- icône et gravité ;
- statut ;
- date et heure ;
- titre et description ;
- cause probable ;
- action recommandée ;
- responsable ;
- bouton « Voir les dossiers ».

Prévoir les actions `Ignorer`, `Marquer comme traitée` et `Affecter`.

#### Détection d'anomalies

Afficher des cartes de rupture de tendance avec :

- date de début ;
- amplitude ;
- produit ou canal concerné ;
- facteurs possibles ;
- historique comparable ;
- recommandation IA ;
- bouton d'action.

#### Recommandations stratégiques

Chaque recommandation doit afficher :

- priorité ;
- identifiant ;
- titre ;
- données utilisées ;
- impact estimé ;
- recommandation ;
- actions `Ignorer` et `Valider l'action`.

#### Assistant IA flottant

Remplacer le bloc fixe par un bouton `Demander à l'IA` ouvrant un panneau ou
une fenêtre contenant :

- saisie naturelle et éventuellement microphone ;
- questions suggérées ;
- historique ;
- réponse texte ;
- graphique généré ;
- sources et filtres utilisés.

Le changement de type de graphique déjà livré doit rester disponible.

### Responsive et accessibilité

- grand écran : grille complète et assistant flottant ;
- tablette : grille à deux colonnes ;
- mobile : une colonne, filtres repliables et assistant en plein écran ;
- tableaux transformés en cartes sur petits écrans ;
- navigation clavier, labels explicites, contrastes suffisants et résumé
  textuel des graphiques.

### Découpage des sprints visuels

#### Sprint visuel 1 — Structure et design system

- nouvelle grille du dashboard ;
- couleurs et espacements ;
- composants de cartes ;
- en-tête ;
- filtres.

#### Sprint visuel 2 — KPI et graphiques principaux

- nouvelles cartes KPI ;
- évolution des plaintes ;
- canal ;
- produit ;
- performance des équipes.

#### Sprint visuel 3 — Risques

- score de risque ;
- matrice de risque ;
- statuts et couleurs métier ;
- avertissement de validation humaine.

#### Sprint visuel 4 — Alertes et anomalies

- centre d'alertes ;
- cartes d'anomalies ;
- responsables et actions ;
- vues détaillées.

#### Sprint visuel 5 — Recommandations et assistant IA

- recommandations stratégiques ;
- assistant flottant ;
- questions suggérées ;
- réponses texte et graphiques ;
- historique.

#### Sprint visuel 6 — Finalisation visuelle

- responsive ;
- accessibilité ;
- exports ;
- traductions ;
- tests visuels ;
- validation avec les données mock.

---

## Priorité immédiate

La prochaine étape la plus utile est :
1. stabiliser la page et le contrat de données ;
2. appliquer le sprint visuel 1 sur la structure et les composants ;
3. refaire les KPI et les graphiques principaux ;
4. intégrer les risques, alertes et anomalies ;
5. déplacer l'assistant IA dans une fenêtre flottante ;
6. finaliser responsive, accessibilité, traductions et exports.

Cela permet de construire le reste de l’interface sur une base fiable, même avant que le contrat FastAPI définitif soit disponible.
