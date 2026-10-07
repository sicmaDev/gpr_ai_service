# Reporting IA - plan et avancement

## Architecture retenue

Le front React appelle directement le microservice FastAPI pour les fonctions
IA. Spring Boot reste le serveur metier et la source des donnees GPR.

La cible de donnees est une base logique dediee `gpr_ai_reporting`, distincte
de la base operationnelle `gpr_sicma_online`. Elle pourra partager la meme
instance MySQL au demarrage, puis etre migree vers une instance separee si la
charge augmente. ChromaDB reste reservee a la recherche semantique et aux
embeddings.

## Avancements realises

- Creation du sous-menu `Reporting IA` dans la rubrique Rapports.
- Creation de la route front `/rapports/ia`.
- Creation d'une page independante du reporting classique.
- Ajout des filtres de periode.
- Ajout des cartes KPI :
  - dossiers analyses ;
  - dossiers a risque eleve ;
  - anomalies detectees ;
  - alertes actives.
- Ajout des graphiques IA avec donnees temporaires :
  - evolution des indicateurs ;
  - repartition des dossiers ;
  - categories a surveiller.
- Ajout des blocs de recommandations et d'alertes.
- Ajout d'une zone de requete en langage naturel.
- Creation du client API FastAPI avec les endpoints prevus :
  - `GET /reporting/dashboard`
  - `POST /reporting/query`
- Compilation React validee avec `npm run build`.

## Ce qui doit suivre

### Front-end

1. Remplacer les donnees temporaires par le contrat FastAPI definitif.
2. Ajouter les graphiques de risques, anomalies et alertes detaillees.
3. Ajouter les filtres de perimetre : type, agence, canal et categorie.
4. Ajouter les vues detaillees et les sources des indicateurs.
5. Ajouter l'export des rapports IA.
6. Ajouter les traductions et les etats UX complets.

### Back-end FastAPI

1. Creer le module `reporting` independant des modules analyse, recherche et
   transcription.
2. Implementer `/reporting/dashboard` et `/reporting/query`.
3. Definir les schemas Pydantic et le format `metrics/charts/alerts`.
4. Connecter FastAPI a `gpr_ai_reporting` avec un compte SQL dedie.
5. Implementer les agregations deterministes avant la generation LLM.
6. Implementer recommandations, alertes, scoring de risque et anomalies.

### Spring Boot

1. Enrichir `/api/v1/ai/export-claims` avec les champs necessaires au reporting.
2. Ajouter pagination et synchronisation incrementale basee sur `updatedAt`.
3. Alimenter la base `gpr_ai_reporting` sans requetes analytiques lourdes sur
   la base operationnelle.

### Validation

- Tester le contrat Spring Boot -> base de reporting -> FastAPI -> React.
- Tester les filtres, erreurs, timeout et indisponibilite du service IA.
- Verifier CORS, authentification, droits SQL et protection des donnees.
- Mesurer les temps de reponse et la charge pendant la synchronisation.
