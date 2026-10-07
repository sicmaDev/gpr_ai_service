# Reporting IA - plan d'implementation du backend

## 1. Objectif

Implementer le backend du Reporting IA en alimentant le front React avec des
donnees reelles, persistantes, filtrables et calculables de maniere
deterministe.

Le perimetre comprend :

- l'export des dossiers depuis Spring Boot ;
- la synchronisation incrementale vers une base de reporting dediee ;
- les endpoints FastAPI consommes par le front ;
- les agregations, graphiques, risques, anomalies, alertes et recommandations ;
- l'assistant de requetes en langage naturel ;
- la securite, les tests et la validation de bout en bout.

## 2. Etat actuel

### Front React

Le front consomme :

```text
GET  /reporting/dashboard
POST /reporting/query
```

Le dashboard transmet les filtres suivants :

```text
start_date
end_date
claim_type
agency
channel
category
risk_level
```

Les fichiers de reference sont :

- `gpr_client_sicma_new_version/src/pages/Rapports/AiReporting.js`
- `gpr_client_sicma_new_version/src/pages/Rapports/AiReportingCharts.jsx`
- `gpr_client_sicma_new_version/src/apis/IA/AiReportingApi.js`
- `gpr_client_sicma_new_version/src/apis/IA/AiReportingMock.js`

### FastAPI

Le service existant contient deja :

- `/analyze` pour l'analyse NLP ;
- `/search` pour la recherche semantique et le RAG ;
- `/transcribe` pour la transcription ;
- un debut de module reporting dans `app/routers/reporting.py` ;
- une logique partielle dans `app/services/reporting_service.py` ;
- une synchronisation complete vers ChromaDB dans
  `app/services/sync_service.py`.

Le routeur reporting est maintenant active dans `main.py` et les endpoints
`/reporting/dashboard` et `/reporting/query` correspondent au contrat attendu
par React. Les anciens endpoints (`/reporting/nl-query` et
`/reporting/insights`) restent disponibles pour compatibilite.

### Spring Boot

L'endpoint actuel :

```text
GET /api/v1/ai/export-claims
```

charge toutes les reclamations avec `findAll()`, filtre certains statuts et
enrichit chaque dossier. Il ne gere pas encore :

- la pagination ;
- le filtre `updatedAt` ;
- la synchronisation incrementale ;
- tous les champs necessaires au reporting ;
- l'optimisation des chargements relationnels.

## 3. Architecture cible

### Decision d'architecture

La cible evolue vers une architecture de Text-to-SQL assistee par catalogues.
Nemotron genere une requete SQL candidate a partir de la question, d'un
sous-schema pertinent et des regles metier versionnees. Le backend valide et
execute cette requete sur la seule base de reporting, avec un compte SQL en
lecture seule et des limites d'execution.

Cette decision remplace, pour les nouvelles requetes naturelles, la cible
precedente ou le LLM choisissait uniquement parmi des primitives et
indicateurs codes en dur. Le moteur analytique hybride actuel reste disponible
pendant la migration pour compatibilite et fallback controle ; il n'est plus
la cible d'extension du chatbot.

Le changement concerne d'abord `POST /reporting/query`. Le dashboard fixe,
ses KPI certifies et ses graphiques predefinis restent inchanges pendant la
transition. Ils repondent a un contrat produit existant et n'ont pas besoin
d'etre remplaces par du SQL genere a chaque chargement.

### Pipeline cible des requetes naturelles

```text
Question utilisateur
  -> Nemotron : intention canonique pour rechercher une requete approuvee
  -> Query Catalog : correspondance avec controle des versions
       -> trouve : appliquer les parametres dynamiques et executer la requete approuvee
       -> absent :
            Schema Catalog + Business Catalog
              -> Schema Retriever : sous-schema minimal autorise
              -> Nemotron : SQL candidat parametre
              -> validation syntaxique, securite, droits et cout
              -> execution en lecture seule sur la base Reporting
              -> reponse, sans sauvegarde automatique
              -> approbation humaine avant ajout au Query Catalog
  -> backend : tableau/visualisation construits depuis les resultats SQL
```

Une requete nouvelle peut etre executee apres controles automatiques stricts ;
une validation humaine est requise uniquement avant sa promotion dans le
catalogue reutilisable. L'execution ne constitue pas en elle-meme une
approbation de l'exactitude metier du SQL.

### Catalogues a construire

1. **Schema Catalog** : tables/vues exposees au Reporting, colonnes, types,
   cles et relations, descriptions, champs sensibles, version et provenance.
   Il est derive uniquement du schema analytique autorise, et non de
   l'integralite de la base operationnelle.
2. **Business Catalog** : concepts, synonymes valides, definitions de dates,
   mesures, statuts, regles d'inclusion/exclusion et relations approuvees.
   Les metadonnees seules ne determinent pas le sens metier ; ces definitions
   necessitent validation.
3. **Query Catalog** : requetes approuvees, exemples de formulations,
   parametres dynamiques, empreinte de l'intention, versions des schemas et
   regles, auteur/approbateur, statut et historique. Les requetes devenues
   incompatibles doivent etre desactivees, jamais rejouees silencieusement.

Le schema complet reste cote backend. Seul le sous-schema necessaire a la
question est transmis au modele. Les lignes clients, donnees personnelles et
resultats de requete ne sont pas inclus dans le contexte de generation SQL.

### Controles obligatoires avant execution

- Executer uniquement contre `gpr_ai_reporting`, jamais directement contre
  `gpr_sicma_online`.
- Utiliser un compte SQL dedie sans droits d'ecriture ni droits
  d'administration.
- Accepter une seule instruction de lecture (`SELECT`, et CTE en lecture si
  le validateur le confirme) ; refuser ecriture, commandes, multi-instruction,
  fonctions interdites et acces aux metadonnees/systemes.
- Valider l'arbre SQL, les tables, colonnes, relations et fonctions par
  rapport au Schema Catalog et a la liste globale des elements autorises.
  L'application est mono-institution et n'applique pas de filtre de donnees
  par utilisateur. Une simple recherche textuelle de mots interdits ne suffit
  pas.
- Fournir les valeurs comme parametres lies ; ne jamais interpoler les
  valeurs de l'utilisateur dans le SQL.
- Appliquer limites de lignes, timeout, concurrence et annulation. Les seuils
  seront mesures et configures avant activation.
- Exclure du Schema Catalog les champs personnels ou non autorises.
- Journaliser les versions, l'empreinte SQL, les decisions du validateur, la
  duree et le statut sans journaliser de valeurs sensibles.
- Refuser explicitement les questions ambigues, non supportees ou impossibles
  avec les donnees disponibles.

```text
React
  |
  | GET /reporting/dashboard
  | POST /reporting/query
  v
FastAPI - module reporting
  |                    \
  |                    ChromaDB
  |                    recherche semantique uniquement
  v
gpr_ai_reporting
base SQL analytique
  ^
  |
synchronisation incrementale
  |
Spring Boot /api/v1/ai/export-claims
  ^
  |
gpr_sicma_online
base operationnelle
```

Regles communes :

- SQL est la source des metriques et agregations ;
- ChromaDB est reservee aux embeddings et a la recherche semantique ;
- les valeurs retournees par le LLM ne constituent jamais des chiffres de
  reference ;
- les graphiques du dashboard sont construits automatiquement par le backend
  a partir des agregations SQL ; le LLM ne dessine pas les graphiques et ne
  choisit pas les valeurs ;
- la synchronisation doit etre idempotente et reprise apres erreur.

### Comment les graphiques sont generes automatiquement

Il existe deux cas distincts :

1. **Graphiques fixes du dashboard** : le backend execute une aggregation SQL
   connue, par exemple le nombre de dossiers par mois, canal ou categorie.
   Il transforme ensuite le resultat en objet compatible avec Chart.js :

   ```json
   {
     "labels": ["Web", "Telephone", "Agence"],
     "datasets": [
       {
         "label": "Dossiers",
         "data": [120, 80, 45]
       }
     ]
   }
   ```

   Le front React affiche automatiquement cet objet dans
   `AiReportingCharts.jsx`. Aucun appel au LLM n'est necessaire pour ces
   graphiques.

2. **Graphique d'une question en langage naturel** : dans la cible Text-to-SQL,
   le LLM peut produire une requete candidate, mais le backend valide puis
   execute le SQL. Il construit lui-meme `labels` et `datasets` a partir des
   resultats. Le LLM ne choisit ni les chiffres ni la structure finale du
   graphique.

   Exemple de flux :

   ```text
   "Quels produits generent le plus de reclamations ?"
        -> intention et recherche de requete approuvee
        -> SQL approuve reutilise ou SQL candidat genere puis valide
        -> execution SQL limitee
        -> labels + datasets generes par FastAPI
        -> reponse Chart.js envoyee a React
   ```

Ainsi, Nemotron peut proposer la requete, tandis que le backend controle son
execution et demeure l'autorite sur les chiffres et la visualisation.

### Premier increment implemente

Le moteur analytique hybride et son parseur controle constituent l'etat
actuel du backend. Ils restent disponibles pendant la migration :

- `/reporting/query` accepte maintenant `analysis` (`kind`, `operation`,
  `target`, `condition`), `group_by`, les filtres, les bornes de periode,
  la comparaison et la limite ;
- les operations, cibles, dimensions, filtres et conditions sont controlees
  par une liste blanche ; les agregations supportees sont executees par
  SQLAlchemy, sans SQL libre ;
- les trois modes `REPORTING_INTENT_MODE` sont disponibles :
  `llm_only` n'utilise jamais le parseur et refuse toute panne ou intention
  invalide ; `hybrid` n'utilise le parseur qu'en cas de panne technique ;
  `deterministic` utilise volontairement le parseur historique ;
- si aucun mode n'est configure, `REPORTING_LLM_ENABLED=true` selectionne
  `hybrid`, sinon le mode historique `deterministic` est conserve ;
- une intention non supportee est exposee comme erreur HTTP 422. Le LLM de
  formulation est desactive par defaut et se configure separement avec
  `REPORTING_LLM_FORMULATION_ENABLED`.

Les ratios et les indicateurs specialises sont maintenant pris en charge avec
des definitions bornees :

- `ratio` calcule en pourcentage les dossiers qui satisfont la condition
  indiquee, sur l'ensemble des dossiers correspondant aux filtres ;
- `sla_compliance_rate` compte les dossiers clotures disposant d'une echeance
  SLA valide ; le numerateur est ceux resolus avant ou a l'echeance ;
- `average_resolution_time` calcule la moyenne entre `receipt_at` et
  `resolved_at`, en jours calendaires, et exclut les dates manquantes ou
  incoherentes ;
- `risk_distribution` compte les dossiers par niveau de risque.

Pour une comparaison groupee, la reponse contient les valeurs de la periode
actuelle et precedente, l'ecart absolu et l'ecart en pourcentage. Le top N est
classe d'apres la valeur de la periode actuelle. L'interface rend ces colonnes
avec des entetes lisibles, en plus du graphique a deux series.

La validation semantique compare egalement les filtres nommes extraits de la
question (agence, canal, categorie, motif, produit, equipe, point de service,
statut, statut de satisfaction, type de dossier et risque) aux filtres
retournes par le LLM ; une valeur absente ou differente est refusee.

Pour les periodes, le LLM recoit une date de reference et un fuseau horaire,
puis retourne des bornes de dates. Le backend valide leur format, leur ordre
et leur coherence avant execution. Le LLM ne genere ni SQL ni formule.

Le parseur deterministe n'est pas l'interpretation principale. Il est limite
au controle de coherence et au fallback technique explicite selon le mode
configure. Il ne doit jamais corriger silencieusement une intention LLM
incomplete.

Les operations, cibles, conditions, dimensions et filtres sont des catalogues
metier en liste blanche ; aucune colonne ou operation SQL libre n'est choisie
par le LLM. Chaque filtre valide ajoute une condition SQLAlchemy,
`operation` et `target` determinent l'agregation autorisee, et `group_by`
selectionne une dimension autorisee.

### Catalogue analytique versionne 1.1.0

Chaque intention hybride inclut `catalog_version`. Le backend refuse une
version absente ou differente de la version supportee et journalise la version
utilisee. Le prompt LLM est genere a partir de cette version. Les definitions
runtime sont immuables ; les changements de contrat ou de sens metier
necessitent une nouvelle version. Un ajout compatible augmente la version
mineure ; une correction non compatible augmente la version majeure.

La matrice primitive autorisee est :

| Operation | Cibles | Conditions applicables | Regroupements |
|---|---|---|---|
| `count` | toutes les cibles du catalogue | toutes les conditions metier | toutes les dimensions autorisees |
| `count_distinct` | toutes les cibles du catalogue | toutes les conditions metier | toutes les dimensions autorisees |
| `sum`, `average`, `min`, `max` | `risk_score` | toutes les conditions metier | toutes les dimensions autorisees |
| `ratio` | `claim` | condition obligatoire parmi les conditions metier | toutes les dimensions autorisees |
| `trend` | `claim` | toutes les conditions metier | `month` obligatoire |

Une condition est appliquee comme filtre sur les dossiers avant l'agregation.
Les operations numeriques utilisent la colonne `ai_risk_score`. Les dimensions
exposees sont `agency`, `category`, `motif`, `product`, `channel`, `team`,
`risk_level`, `service_point` et `month`.

Les indicateurs specialises acceptes et leurs regroupements sont :

| Indicateur | Definition | Regroupements autorises |
|---|---|---|
| `sla_compliance_rate` | Dossiers clotures avec SLA valide resolus avant ou a l'echeance / dossiers clotures avec SLA valide, en pourcentage | Toutes les dimensions |
| `average_resolution_time` | Moyenne de `resolved_at - receipt_at`, en jours calendaires | Toutes les dimensions |
| `risk_distribution` | Nombre de dossiers ayant un niveau de risque par valeur `risk_level` | `risk_level` obligatoire |

La suite de tests parcourt exhaustivement les operation/cible/condition de la
matrice et execute chaque combinaison autorisee contre SQLite ; elle verifie
egalement les regles de regroupement et le refus de versions inconnues.

La visualisation respecte strictement l'intention :

- `group_by` present : agregation `GROUP BY` et graphique correspondant ;
- `group_by` absent : resultat numerique principal uniquement, sans
  regroupement automatique par categorie ;
- une ventilation secondaire eventuelle doit etre explicitement identifiee
  comme non demandee.

Pour une comparaison groupee, le contrat porte les periodes comparees, la
dimension et la limite. Les groupes sont classes selon la valeur de la periode
courante ; l'API renvoie les deux valeurs et leurs ecarts, calcules depuis SQL.

## 4. Phase 0 - validation du contrat metier

### Etat d'avancement

La phase 0 est validee pour la premiere version. Le contrat technique a ete
releve depuis le front React et le mock existant, puis confirme avec les
regles metier retenues. Les decisions ci-dessous sont maintenant appliquees
dans Spring Boot, FastAPI et la base de reporting.

Le SLA ne doit pas etre calcule avec une duree globale fixe. Chaque motif
possede sa propre duree de traitement. L'echeance doit etre calculee a partir
de la date de reception du dossier et de la duree associee a son motif.
Spring Boot devra donc exposer la duree ou l'echeance calculee afin que le
reporting puisse determiner les retards sans inventer de valeur.

### Proposition de definitions

| Cle front | Definition a confirmer |
|---|---|
| `total_claims` | Nombre total de dossiers de la periode |
| `high_risk_claims` | Nombre de dossiers en cours de traitement : tous les statuts sauf `SATISFIED`, `CLASSED` et `TEMP_SAVED` |
| `anomalies` | Nombre de dossiers actifs dont l'echeance definie par le motif est depassee |
| `active_alerts` | Nombre de dossiers dont la gravite metier est `GRAVE` |
| `risk_score` | Score moyen des dossiers scores sur la periode, de 0 a 100 |

Les libelles metier confirmes sont :

- `total_claims` : « Total plaintes » ;
- `high_risk_claims` : « En cours » ;
- `anomalies` : « En retard » ;
- `active_alerts` : « Plaintes graves ».

Les noms techniques sont conserves pour rester compatibles avec le front
existant. Le niveau de risque reste disponible dans `risk_summary`,
`risk_matrix` et les graphiques dedies.

### Valeurs proposees par defaut

En l'absence d'une regle metier contraire, le backend utilisera :

- les reclamations et denonciations ; les suggestions sont exclues du
  scoring de risque tant que leur modele metier n'est pas confirme ;
- `created_at` comme date de rattachement a une periode ;
- `updated_at` comme curseur de synchronisation ;
- la timezone `Africa/Porto-Novo` (Benin), configurable par variable
  d'environnement ;
- les niveaux de risque `MINEUR`, `MOYEN`, `GRAVE` dans les réponses API,
  la matrice et les graphiques ;
- gravite metier `GRAVE` uniquement pour le KPI « Plaintes graves » ;
- le niveau de risque est celui du motif (`gps_objet.risqueLevel`) et ne doit
  pas etre calcule par l'IA ;
- `TEMP_SAVED` est un brouillon exclu de la synchronisation et du reporting ;
- les statuts `SATISFIED`, `CLASSED` et `TEMP_SAVED` sont exclus du calcul
  des retards ;
- le SLA est calcule par Spring Boot avec
  `receiptDateTime + gps_objet.processingTime` et expose sous `slaDueAt` ;
- les statuts d'alerte `new`, `in_progress`, `resolved`, `dismissed`.

### Decisions confirmees

- types de dossiers inclus : reclamations et denonciations ;
- suggestions exclues du reporting IA pour la premiere version.
- definitions des quatre cartes KPI alignees sur les libelles metier actuels.
- statuts Spring Boot pris en compte : `SAVED`, `TEMP_SAVED`, `AFFECTED`,
  `TO_APPROUVED`, `DESAPPROUVED`, `TREAT`, `SATISFIED`, `UNSATISFIED`,
  `PARTIAL_SATISFIED`, `LITIGATION`, `CLASSED`, `TRANSMITTED`.
- dossiers « En cours » : tous les statuts sauf `SATISFIED`, `CLASSED` et
  `TEMP_SAVED`.
- plaintes graves : dossiers dont `ai_urgency` vaut `GRAVE`.
- dossiers « En retard » : depassement de l'echeance du motif ;
- echeance : `receiptDateTime + gps_objet.processingTime`, exposee par Spring
  Boot sous `slaDueAt` ;
- dossiers sans motif ou sans date de reception : echeance nulle, donc non
  consideres comme en retard tant que la donnee metier manque.

Le contrat fonctionnel minimal est valide pour commencer la premiere
implementation. Les definitions et valeurs retenues devront etre reprises
dans les schemas Pydantic, les migrations SQL et les tests du module
reporting.

### Points de gouvernance restant a confirmer

La gouvernance correspond ici aux regles metier et d'exploitation qui doivent
etre validees par l'organisation. Ce ne sont pas des fonctionnalites IA :
elles determinent comment les donnees sont interpretees, comparees et
conservees.

#### 1. Agence, point de service et equipe

Ces trois notions peuvent representer des niveaux differents dans GPR :

- **Agence** : unite organisationnelle ou entite de rattachement, par exemple
  « Agence Nord » ou « Siege » ;
- **Point de service** : lieu ou canal operationnel precis ayant recueilli la
  plainte, par exemple un guichet, une agence physique, le site web ou le
  service client telephonique ;
- **Equipe** : groupe responsable du traitement du dossier, par exemple une
  equipe regionale ou une equipe du service reclamations.

Cette distinction est importante pour les filtres et les graphiques. Sans
regle claire, un meme dossier pourrait etre compte simultanement dans une
agence, un point de service et une equipe, ou bien les valeurs pourraient
etre melangees. Le contrat devra donc preciser :

- le champ source utilise pour chaque notion ;
- la hierarchie entre agence et point de service ;
- l'equipe responsable a retenir lorsque plusieurs utilisateurs sont lies au
  dossier ;
- la valeur a utiliser lorsqu'une information est absente.

#### 2. Timezone des periodes et des dates

La timezone definit le jour auquel un dossier appartient. Elle est importante
pour les filtres, les periodes, les delais SLA et les synchronisations. Par
exemple, un dossier cree a `23:30 UTC` peut appartenir au jour suivant selon
la timezone metier.

Le backend doit utiliser une timezone unique pour :

- `start_date` et `end_date` ;
- les regroupements par jour, semaine ou mois ;
- le calcul du SLA de 3 jours ;
- `generated_at` et les dates d'alertes ;
- le curseur `updatedAfter` de synchronisation.

Le fuseau metier retenu est `Africa/Porto-Novo` (Benin), configurable par
variable d'environnement. Il est utilise pour interpreter les jours et
periodes demandes, les echeances et les horodatages affiches. Les dates
stockees en UTC sont converties vers ce fuseau pour les calculs de calendrier.

#### 3. Duree de conservation des donnees

La retention indique combien de temps les donnees sont conservees dans
`gpr_ai_reporting`. Elle concerne notamment :

- les dossiers synchronises ;
- les scores de risque ;
- les anomalies ;
- les alertes ;
- les recommandations et leurs sources.

Cette decision doit prendre en compte les obligations reglementaires, les
besoins d'audit, le volume de la base et la possibilite de supprimer ou
anonymiser les donnees personnelles. Elle doit preciser :

- la duree de conservation des donnees detaillees ;
- la duree de conservation des alertes et recommandations ;
- la procedure d'archivage ou de suppression ;
- les champs a anonymiser ;
- les roles autorises a consulter l'historique.

Pour demarrer techniquement, une retention de 24 mois peut etre utilisee
comme valeur provisoire, mais elle ne doit pas etre consideree comme une
regle reglementaire sans validation metier et juridique.

## 5. Phase 1 - schemas et contrat FastAPI

### Etat d'avancement

La phase 1 est demarree dans le service `gpr_ai_service`. Le contrat
Pydantic initial est en place dans :

```text
app/reporting/schemas.py
app/reporting/router.py
app/reporting/__init__.py
```

Les routes suivantes sont maintenant declarees :

```text
GET  /reporting/dashboard
POST /reporting/query
```

Les schemas valident deja les filtres, les dates, la longueur des questions,
les KPI, les graphiques, les alertes, les recommandations et les details.
Les endpoints avaient initialement retourne `501` afin d'eviter de fournir des
donnees fictives au front. Ils sont maintenant branches sur le service SQL
de reporting de la phase 5.

La phase 1 est maintenant complete sur son perimetre de contrat :

- constantes metier centralisees dans `app/reporting/constants.py` ;
- validation des types de dossiers et niveaux de risque ;
- interfaces internes dans `app/reporting/interfaces.py` pour le repository,
  le service dashboard et le service de requetes ;
- documentation OpenAPI des deux routes ;
- six tests de contrat dans `tests/test_reporting_contract.py`.

La valeur `501` n'est plus utilisee pour le dashboard et les requetes
Reporting IA.

Creer un module reporting independant :

```text
app/reporting/
  __init__.py
  router.py
  schemas.py
  filters.py
  metrics.py
  charts.py
  alerts.py
  recommendations.py
  query.py
app/repositories/
  reporting_repository.py
app/db/
  session.py
  models.py
```

### Schemas principaux

Definir au minimum :

- `ReportingFilters` ;
- `Period` ;
- `FilterOptions` ;
- `DashboardMetrics` ;
- `RiskSummary` ;
- `RiskMatrixRow` ;
- `ChartData` ;
- `Recommendation` ;
- `Alert` ;
- `DashboardDetails` ;
- `DashboardResponse` ;
- `ReportingQueryRequest` ;
- `ReportingQueryResponse`.

### Endpoints

Implementer :

```text
GET /reporting/dashboard
POST /reporting/query
```

Le dashboard doit retourner :

```json
{
  "periods": [],
  "filter_options": {},
  "metrics": {},
  "risk_summary": {},
  "risk_matrix": [],
  "charts": {},
  "recommendations": [],
  "alerts": [],
  "details": {},
  "generated_at": "2026-09-14T00:00:00Z"
}
```

Conserver eventuellement les anciens endpoints comme compatibilite
temporaire, mais ne pas les utiliser comme contrat principal du front.

## 6. Phase 2 - base `gpr_ai_reporting`

### Etat d'avancement

La fondation SQL de la phase 2 est en place dans le service FastAPI :

- `app/db/session.py` configure SQLAlchemy et `REPORTING_DATABASE_URL` ;
- `app/db/models.py` definit le modele `ReportingClaim` ;
- `app/db/migrations/001_create_reporting_claim.sql` contient la migration
  MySQL explicite ;
- `app/db/__init__.py` expose le moteur, la session et la base declarative.

La base MySQL dediee a ete creee localement et la migration a ete executee :

```text
gpr_ai_reporting.reporting_claim
```

La connexion FastAPI utilise par defaut MySQL en local :

```text
REPORTING_DATABASE_URL=mysql+pymysql://root@localhost:3306/gpr_ai_reporting?charset=utf8mb4
```

La production devra fournir une URL MySQL dediee avec un compte SQL
reporting sans droits d'administration.
La synchronisation, les `upsert` et les aggregations sont implementes dans
les phases suivantes. La migration n'est pas executee automatiquement au
demarrage afin d'eviter toute modification implicite de la base.

La connexion SQLAlchemy et le modele ont ete verifies avec SQLite en memoire
pour les tests, tandis que la migration reelle a ete verifiee sur MySQL.
Les dependances `SQLAlchemy` et `PyMySQL` sont ajoutees au fichier
`requirements.txt`.

Creer une base logique dediee, distincte de `gpr_sicma_online`.
Elle peut partager la meme instance MySQL au demarrage.

### Table principale : `reporting_claim`

Champs recommandes :

```text
id
source_claim_id
source_code
client_code
claim_type
status
category
motif
product
service_point
agency
channel
team
content
solution
ai_urgency
ai_sentiment
ai_risk_level
ai_risk_score
ai_summary
created_at
receipt_at
updated_at
affected_at
resolved_at
sla_due_at
satisfaction_status
source_created_at
source_updated_at
synced_at
```

### Tables complementaires

Creer si necessaire :

```text
reporting_sync_state
reporting_risk_score
reporting_anomaly
reporting_alert
reporting_recommendation
```

### Index

Ajouter des index sur :

```text
source_claim_id
source_updated_at
created_at
claim_type
status
category
agency
channel
risk_level
```

`source_claim_id` doit etre unique afin de permettre les `upsert`.

## 7. Phase 3 - evolution de Spring Boot

### Etat d'avancement

L'endpoint Spring Boot `/api/v1/ai/export-claims` supporte maintenant :

- `page` avec une valeur par defaut de `0` ;
- `size` avec une valeur par defaut de `500` et un maximum de `1000` ;
- `updatedAfter` pour la synchronisation incrementale ;
- `updatedBefore` pour borner une fenetre de synchronisation ;
- `includeMedia=false` et `includeAudio=false` pour eviter les requetes
  relationnelles couteuses par defaut ;
- un tri stable par `updatedAt ASC, id ASC`.

La reponse est maintenant paginee :

```json
{
  "content": [],
  "page": 0,
  "size": 500,
  "totalElements": 1200,
  "totalPages": 3,
  "hasNext": true,
  "lastSyncAt": "2026-09-14T00:00:00"
}
```

L'export inclut desormais les reclamations et denonciations, quel que soit
leur statut, afin d'alimenter les KPI « En cours », « En retard » et
« Plaintes graves ». Les champs de classification IA, les dates metier et
les informations d'agence, point de service et equipe sont egalement
exposes lorsqu'ils existent.

La compilation Maven du backend Spring Boot a ete validee.

### Synchronisation incrementale FastAPI

La synchronisation vers MySQL est maintenant implementee dans
`app/services/sync_service.py` :

- lecture du curseur dans `reporting_sync_state` ;
- appel page par page de Spring Boot avec `updatedAfter` ;
- conversion des dates ISO en UTC naive pour MySQL ;
- `upsert` idempotent sur `source_claim_id` ;
- mise a jour du curseur uniquement apres validation et commit du lot ;
- rollback SQL en cas d'erreur ;
- mode `full=True` disponible pour une reconstruction complete.

La table de suivi est creee par :

```text
app/db/migrations/002_create_reporting_sync_state.sql
```

Une synchronisation interrompue ne valide donc pas son nouveau curseur et
pourra reprendre depuis le dernier traitement confirme.

### API paginee et incrementale

Faire evoluer `/api/v1/ai/export-claims` avec :

```text
page
size
updatedAfter
updatedBefore
includeMedia
includeAudio
```

Exemple :

```text
GET /api/v1/ai/export-claims?page=0&size=500&updatedAfter=2026-09-13T00:00:00
```

Retourner une enveloppe paginee :

```json
{
  "content": [],
  "page": 0,
  "size": 500,
  "totalElements": 1200,
  "totalPages": 3,
  "hasNext": true,
  "lastSyncAt": "2026-09-14T00:00:00Z"
}
```

### Enrichissement du DTO

Enrichir `ExportClaimDto` avec :

- `updatedAt` ;
- `receiptDateTime` ;
- `affectedAt` ;
- la date de resolution disponible ;
- `aiUrgency` ;
- `aiSentiment` ;
- `aiSuggestedCategory` ;
- `aiSuggestedMotif` ;
- `aiSummary` ;
- `aiRiskScore` et `aiRiskLevel` si disponibles ;
- l'agence et le point de service ;
- l'equipe responsable ;
- le statut detaille ;
- les informations SLA utiles.

### Performance

- remplacer `findAll()` par une requete paginee ;
- trier par `updatedAt` puis par identifiant ;
- eviter les medias et audios par defaut ;
- utiliser des projections ou DTO queries ;
- eviter les chargements N+1 ;
- ne jamais effectuer de requetes analytiques lourdes sur la base
  operationnelle.

## 8. Phase 4 - synchronisation FastAPI

### Etat d'avancement

La synchronisation incrementale est implementee dans
`app/services/sync_service.py`. Elle lit le curseur, recupere les pages
Spring Boot, effectue les `upsert` MySQL et ne valide le nouveau curseur
qu'apres le commit. Le scheduler de `main.py` appelle ce service chaque jour
a 02:00 en environnement de deploiement. Le mode `full=True` permet une
reconstruction complete.

### Synchronisation incrementale

1. Lire `last_successful_sync_at`.
2. Appeler Spring Boot avec `updatedAfter`.
3. Traiter les pages dans l'ordre.
4. Valider les lots avec Pydantic.
5. Effectuer les `upsert` dans `reporting_claim`.
6. Mettre a jour l'etat uniquement apres succes.
7. Conserver le dernier curseur valide en cas d'erreur.
8. Journaliser les creations, mises a jour, erreurs et durees.

### Synchronisation initiale

Prevoir une commande de reconstitution complete :

```text
python -m app.commands.sync_reporting --full
```

### Scheduler

Le scheduler actuel appelle desormais le service SQL de synchronisation. Le
rafraichissement ChromaDB ne doit concerner que les dossiers nouveaux ou
modifies et ne doit plus servir de source aux metriques.

## 9. Phase 5 - dashboard et agregations

### Etat d'avancement

Les agregations SQL sont branchees dans `app/reporting/service.py`. Le
dashboard calcule les KPI, les retards SLA, le score de risque, les options de
filtres et les graphiques de tendance, canaux, categories, produits et risques.
La route `/reporting/query` utilise uniquement des regroupements predefinis
et ne permet pas au LLM ou au client d'executer du SQL libre.

Les variations des KPI par rapport a la periode precedente, les periodes
de 7 jours, 30 jours, trimestre et annee, ainsi que les listes detaillees des
dossiers graves et en retard sont maintenant retournees par le dashboard.
Les niveaux de risque anglais fournis par les donnees historiques sont
normalises vers `MINEUR`, `MOYEN` et `GRAVE` lors de la synchronisation.

Les dossiers au statut `TEMP_SAVED` sont exclus de la synchronisation et
supprimes de la table de reporting s'ils y etaient deja presents. Ils sont
donc absents des KPI, graphiques, filtres, alertes, recommandations, requetes
et listes de details.

La synchronisation ChromaDB est egalement reconnectable via
`REPORTING_ENABLE_RAG_SYNC=true`. Elle reste desactivee par defaut afin de ne
pas charger le modele d'embeddings dans les executions SQL et les tests.

Implementer les agregations SQL pour :

- le volume total ;
- les dossiers en cours ;
- les dossiers en retard ;
- les dossiers graves ;
- le score de risque ;
- les variations par rapport a la periode precedente ;
- les anomalies ;
- les alertes actives.

Appliquer tous les filtres cote serveur :

```text
start_date
end_date
claim_type
agency
channel
category
risk_level
```

Retourner au minimum les periodes :

- 7 jours ;
- 30 jours ;
- trimestre ;
- annee.

Les graphiques doivent etre directement compatibles avec
`AiReportingCharts.jsx` :

```json
{
  "labels": ["Web", "Telephone"],
  "datasets": [
    {
      "label": "Dossiers",
      "data": [120, 80]
    }
  ]
}
```

Clés attendues :

```text
trend
distribution
channels
categories
products
team_performance
risk
```

## 10. Phase 6 - risques, anomalies, alertes et recommandations

### Etat d'avancement

La phase 6 est partiellement implementee : normalisation des niveaux de
risque, matrice de risque, listes de details, exclusion des brouillons
`TEMP_SAVED`, alertes deterministes de retard, score numerique deterministe
et anomalies deterministes sont en place. Les alertes sont persistees de
maniere idempotente dans MySQL avec conservation de leur statut. Les anomalies couvrent maintenant
la concentration, la variation de volume, le depassement de la moyenne des
deux mois precedents et la hausse du taux de dossiers graves. Le niveau de risque metier est
recupere depuis `gps_objet.risqueLevel`; il est distinct du score numerique.

### Scoring de risque

Le premier scoring deterministe et explicable est maintenant calcule a la
volee par le reporting, sur une echelle de 0 a 100 :

- base du motif : `MINEUR=20`, `MOYEN=50`, `GRAVE=80` ;
- `+10` pour un sentiment negatif ;
- `+5` pour une denonciation ;
- `+5` pour un dossier actif ;
- `+10` pour un retard SLA ;
- plafonnement a 100 ;
- les dossiers sans `riskLevel` restent non scores.

Ce score est distinct de `ai_risk_score` et ne remplace pas le niveau
metier du motif. Il est recalcule dynamiquement pour tenir compte du statut
et du retard actuels. Une persistance pourra etre ajoutee si le besoin
d'historisation est confirme.

### Anomalies

Les premieres regles explicites sont maintenant actives :

- hausse d'au moins 50 % par rapport a la periode precedente ;
- concentration d'au moins 60 % des dossiers dans une categorie ou un
  canal, avec au moins trois dossiers.

Elles produisent une alerte et une recommandation deterministes avec les
faits justificatifs (dimension, valeur, volume et pourcentage).

Les anomalies SLA et de concentration sont egalement retournees dans les
alertes et recommandations. Les alertes deterministes sont maintenant persistees dans `reporting_alert`
avec une cle de regle stable, un statut, les dates, l'action et les faits
justificatifs. La mise a jour est idempotente et conserve le statut metier
existant. L'analyse de concentration par agence et l'historisation complete
des anomalies restent a implementer.

Le LLM peut expliquer une anomalie, mais ne doit pas etre la seule source de
decision.

### Alertes

La table `reporting_alert` et la migration `003_create_reporting_alert.sql`
sont maintenant en place. Les alertes generees par le dashboard sont
upsertees avec une cle stable et les statuts existants ne sont pas ecrases.

Le modele persiste :

```text
id
type
severity
title
message
subtitle
status
owner
detected_at
resolved_at
source_rule
action
```

Statuts recommandes :

```text
new
in_progress
resolved
dismissed
```

### Recommandations

Pipeline :

1. calculer les faits ;
2. selectionner les faits significatifs ;
3. demander au LLM une formulation ;
4. valider la reponse ;
5. retourner la recommandation avec ses donnees justificatives.

## 11. Phase 7 - requetes en langage naturel

### Etat d'avancement

`POST /reporting/query` execute actuellement des intentions validees par le
contrat hybride et des agregations SQLAlchemy controlees. Le catalogue
analytique versionne, les modes `llm_only`, `hybrid` et `deterministic`, les
filtres, comparaisons, indicateurs specialises et visualisations existent
deja ; ils constituent le systeme historique a migrer, pas la nouvelle cible.

La phase 7 est donc reorientee vers Text-to-SQL gouverne. Elle est en cours ;
la generation SQL, les catalogues de schema/requetes et leur interface
d'approbation ne sont pas encore implementees.

### Contrats d'echange cibles

Le premier appel LLM produit une intention de recherche, pas du SQL :

```json
{
  "entity": "claim",
  "measure": {"operation": "count", "target": "claim"},
  "dimensions": ["agency"],
  "filters": [],
  "time": {
    "field": "receipt_date",
    "start_date": "2026-10-01",
    "end_date": "2026-10-31",
    "timezone": "Africa/Porto-Novo"
  },
  "comparison": null,
  "ambiguities": []
}
```

Le premier appel recoit la date de reference courante et le fuseau
`Africa/Porto-Novo`. Le LLM a le droit de retourner des dates absolues
calculees ou extraites de la question, pas seulement un alias comme
`current_month`. Le contrat de temps couvre trois cas :

| Demande | Valeurs d'intention attendues |
|---|---|
| « ce mois-ci » | bornes exactes du mois courant selon la date de reference et le fuseau |
| « le 15 septembre 2026 » | `start_date=2026-09-15`, `end_date=2026-09-15` |
| « du 1er au 15 septembre inclus » | `start_date=2026-09-01`, `end_date=2026-09-15` |

Le backend verifie que les dates sont valides, ordonnees et coherentes avec
la question, puis les convertit en bornes SQL. Pour des dates inclusives, la
borne basse est le debut du premier jour local et la borne haute est le debut
du jour suivant le dernier jour demande (intervalle `[debut, fin[`). Ainsi,
une colonne horodatee peut etre filtree sans perdre les dossiers de la
derniere journee. Si la question est ambigue (par exemple « depuis lundi »
sans date de reference interpretable) ou si le modele retourne des bornes qui
ne correspondent pas a la demande, le backend demande une precision ou refuse
la requete ; il ne devine pas.

Le backend valide l'intention et recherche une requete approuvee. Si aucune
correspondance exacte de l'intention canonique et compatible avec les filtres,
dates, droits et versions n'existe, il recupere le Schema Catalog et les
definitions metier pertinents, puis un second appel LLM propose le SQL :

```json
{
  "sql": "SELECT ... WHERE receipt_at >= :start_date AND receipt_at < :end_date",
  "parameters": {
    "start_date": "time.start",
    "end_date": "time.end"
  },
  "used_schema": ["reporting_claim.agency", "reporting_claim.receipt_at"],
  "assumptions": []
}
```

Le SQL utilise des **parametres lies** : `:start_date` et `:end_date` sont des
emplacements, et non du texte concatene dans la requete. Le backend leur
associe les dates validees a part. Cela empeche qu'une valeur saisie par
l'utilisateur soit interpretee comme une instruction SQL, facilite la
conversion des types (date, nombre, texte) et permet de reutiliser la meme
structure SQL avec des periodes differentes. Dans le cas d'une date explicite,
le LLM l'extrait du texte ; pour une periode relative, il la calcule a partir
de la date de reference transmise. Dans les deux cas, le backend valide puis
lie la valeur.

Les champs `used_schema` et `assumptions` servent au diagnostic ; ils ne
remplacent pas la validation du parseur SQL par le backend.

### Choix du type et du nombre de graphiques

Le LLM ne decide pas librement des graphiques et ne retourne pas des donnees
Chart.js. FastAPI choisit a partir de l'intention validee (mesure, dimension
de regroupement, periode/comparaison) et de la forme des resultats SQL. Le
fait qu'une question n'ait pas de regroupement ne signifie donc pas qu'aucune
visualisation n'est possible. Le systeme actuel retourne deja une visualisation
pour un resultat global, avec un seul point etiquete `Total` ; l'interface peut
le representer avec un graphique a une valeur. Dans l'implementation actuelle,
FastAPI donne `bar` par defaut aux resultats globaux ou groupes et `line` aux
tendances ; dans le composant React, l'utilisateur peut ensuite choisir parmi
les types proposes. Un graphique circulaire avec une seule valeur n'est
cependant pas informatif. Pour une valeur unique, une carte KPI serait souvent
plus lisible qu'un graphique, mais cela demande un type d'affichage adapte
dans le contrat/API et le front.

Regles de presentation :

- resultat scalaire sans regroupement : afficher la valeur comme resultat
  principal et, si utile, comme point unique ; preferer une carte KPI lorsque
  le type de visualisation correspondant est disponible ;
- regroupement par une dimension categorielle (agence, produit, statut, etc.) :
  un graphique en barres par defaut ;
- regroupement temporel (jour, mois, annee) : un graphique en ligne par defaut ;
- comparaison de periodes par categorie : un graphique comparatif avec une
  serie par periode, si les resultats ont les memes dimensions ;
- demande explicite de parts/proportions : un graphique circulaire peut etre
  choisi seulement si le resultat est une repartition categorielle adaptee ;
  sinon le backend conserve le graphique en barres.

Le nombre de graphiques depend des series analytiques distinctes demandees et
des donnees disponibles, pas uniquement de la presence de `group_by`. Le
contrat actuel de `/reporting/query` renvoie au plus une visualisation par
question ; les comparaisons peuvent toutefois contenir plusieurs series dans
ce meme graphique (par exemple une serie par periode). FastAPI ne fabrique pas
de ventilation qui n'a pas ete demandee. Si les resultats ne se pretent pas a
un graphique honnete, elle retourne les donnees tabulaires et la valeur
principale. Une future demande de plusieurs graphiques independants devra etre
explicite et le contrat API/front devra accepter une liste de visualisations.
Un affichage de type carte KPI pour un scalaire est une amelioration de
presentation, et non une nouvelle mesure.

### Termes utilises dans cette phase

- **Schema Catalog** : inventaire cote backend des tables, colonnes et
  relations que le Reporting a le droit d'interroger.
- **Business Catalog** : definitions metier validees, par exemple ce que
  signifient « agence », « date de reception » ou « en retard ».
- **Query Catalog** : registre des requetes examinees par une personne et
  approuvees pour reutilisation.
- **Sous-schema** : petit extrait du Schema Catalog necessaire a une question,
  transmis au LLM au lieu de l'inventaire complet.
- **AST SQL** : arbre syntaxique abstrait ; le validateur analyse la structure
  reelle de la requete pour verifier qu'il s'agit d'une lecture autorisee,
  plutot que de chercher seulement des mots interdits dans une chaine.
- **Feature flag** : option de configuration permettant d'activer le nouveau
  pipeline progressivement ou de revenir temporairement a l'ancien.
- **Mode observation** : le nouveau pipeline est execute pour comparer ses
  resultats, mais sa reponse n'est pas encore celle presentee a l'utilisateur.

### Catalogue des requetes validees

Une entree est creee uniquement apres revue humaine et comprend au minimum :

- un identifiant stable et le statut (`candidate`, `approved`, `disabled`) ;
- une ou plusieurs formulations naturelles approuvees ;
- l'intention canonique et les parametres dynamiques ;
- le SQL normalise et les parametres lies attendus ;
- les versions du Schema Catalog et du Business Catalog ;
- l'approbateur, les dates de creation/revue et l'historique ;
- les tests de non-regression et les limites d'execution.

Une requete approuvee ne matche que si l'intention canonique, les filtres, les
bornes de periode et les versions sont compatibles. La recherche
semantique peut proposer des candidates, mais le backend compare ensuite ces
elements de facon structurelle. Si aucune candidate ne correspond exactement,
le systeme genere une nouvelle requete ; si l'intention elle-meme reste
ambigue, il demande une clarification au lieu de reutiliser une requete
approximativement similaire.

### Migration et compatibilite

Le changement est incremental et porte d'abord sur `/reporting/query`. Les
endpoints, le contrat de reponse React, les graphiques et les KPI fixes du
dashboard sont preserves. Une bascule par configuration/feature flag permet
de comparer le nouveau pipeline au moteur courant avant de le rendre
principal.

Les modes actuels sont conserves pendant la transition :

```text
llm_only      : interpretation/generation LLM obligatoire ; erreur explicite
                si le modele, le schema ou les controles ne permettent pas
                une reponse valide.
hybrid        : repli vers l'ancien parseur uniquement en cas de panne
                technique, jamais pour completer une intention incomplete.
deterministic : ancien pipeline controle, explicitement selectionne pour
                compatibilite et comparaison.
```

Le SQL generatif n'est jamais un fallback silencieux lorsque l'intention est
ambigue ou non supportee. Ces cas demandent une clarification ou renvoient une
erreur explicite.

### Etapes de la phase 7 reorientees

1. Formaliser les concepts, definitions, donnees sensibles du perimetre
   reporting actuel ; definir les contrats d'intention, de requete
   candidate et d'approbation.
2. Construire un Schema Catalog versionne depuis les tables/vues de
   `gpr_ai_reporting`, avec cles, relations, types et descriptions, sans
   introspection de la base operationnelle a l'execution.
3. Construire le Business Catalog et le Schema Retriever : selectionner les
   concepts et tables pertinentes via vocabulaire valide, relation et
   filtres, puis limiter le contexte transmis au modele.
4. Implementer la generation SQL candidate et un validateur AST SQL ; ne pas
   executer de SQL brut ou valide par expression reguliere seulement.
5. Executer sous compte SQL en lecture seule, dans une transaction, avec
   parametres lies, timeout et limite de lignes. L'application est
   mono-institution et ne filtre pas les lignes par utilisateur.
6. Transformer les resultats au contrat `ReportingQueryResponse` existant ;
   ne faire produire ni chiffres ni datasets par le LLM.
7. Ajouter le Query Catalog avec revue/approbation humaine, versionnement,
   desactivation sur changement de schema et audit.
8. Ajouter des tests de securite, de semantique, d'equivalence, de charge et
   de regression API ; activer progressivement derriere un feature flag.
9. Retirer les metriques codees en dur du chemin chatbot seulement apres
   equivalence, surveillance et validation metier. Conserver les calculs
   certifies du dashboard tant qu'ils sont requis par son contrat.
10. Apres stabilisation de cette premiere version Text-to-SQL, ajouter le
    tool calling pour que Nemotron sollicite des outils backend explicitement
    autorises au lieu de devoir recevoir toutes les informations dans un seul
    prompt.

### Mesure des benefices et criteres de bascule

Comparer le pipeline actuel et le nouveau sur un corpus versionne de
questions reelles : exactitude de l'intention, exactitude des resultats,
taux de refus correct, latence, cout modele, taux d'erreur SQL, requetes
bloquees par les controles et succes selon chaque source. Aucun seuil de
bascule n'est presume ici ; il sera defini avant activation generale.

### Evolution prevue apres la premiere version : Tool calling

Le tool calling est retenu comme evolution prioritaire apres la premiere
version gouvernee. Il permettra au modele de demander des actions de contexte
limite, par exemple :

- rechercher une requete approuvee correspondant a l'intention ;
- recuperer un sous-schema autorise pour les concepts identifies ;
- demander une clarification ou verifier une definition du Business Catalog.

Les outils exposent des fonctions backend nommees et bornees. Ils ne donnent
pas au modele un acces direct a la base et ne lui permettent pas d'executer
du SQL arbitraire. La generation d'un SQL candidat puis ses controles et son
execution restent sous le controle de FastAPI. Le tool calling sera active
seulement apres mesure de la compatibilite du modele Nemotron, de l'endpoint
Ollama utilise et du comportement des appels d'outils ; en cas d'echec, le
pipeline v1 conserve son parcours sans outils.

### Autres evolutions avancees differees

Les capacites Ollama ci-dessous restent optionnelles pour le pipeline
Text-to-SQL et leur adoption doit etre precedee d'un test de compatibilite
avec le modele et l'endpoint configures (notamment Ollama Cloud).

| Capacite | Utilite envisagee | Limite / condition |
|---|---|---|
| Instructor | Simplifier le parsing, la validation Pydantic et les retries controles. | Verifier le support par le client Ollama et mesurer le cout des appels de correction. |
| Thinking | Aider au diagnostic de l'interpretation. | Facultatif, potentiellement plus lent ; ne remplace ni la justification ni la validation. |
| Streaming | Afficher progressivement la generation et ameliorer la perception de latence. | Ne reduit pas necessairement le temps de calcul total ; la requete SQL attend une intention exploitable. |
| Structured Outputs avec JSON Schema | Contraindre le format de l'intention. | Verifier la prise en charge par le fournisseur ; la documentation Ollama indique que les schemas ne sont pas supportes par Ollama Cloud. |

Les gains attendus doivent etre mesures separement : fiabilite du contrat,
temps de developpement, nombre d'appels LLM, latence totale et taux de
fallback. Par defaut, privilegier une seule requete LLM d'interpretation ;
la formulation des reponses chiffrees reste deterministe afin d'eviter un
appel distant supplementaire.

Reponse attendue par React :

```json
{
  "answer": "Les moyens de paiement representent le principal volume.",
  "summary": "Les moyens de paiement arrivent en tete.",
  "sources": [
    "Base de reporting GPR",
    "Periode du 1er juillet au 12 septembre 2026"
  ],
  "visualization": {
    "type": "bar",
    "title": "Dossiers par categorie",
    "labels": ["Moyens de paiement", "Frais"],
    "datasets": [
      {
        "label": "Dossiers",
        "data": [48, 36]
      }
    ]
  },
  "data": [
    {
      "categorie": "Moyens de paiement",
      "dossiers": 48
    }
  ]
}
```

## 12. Phase 8 - securite et exploitation

### Etat d'avancement

La phase 8 n'est pas finalisee. CORS est configurable par environnement et
les secrets peuvent etre fournis par variables d'environnement, mais
l'authentification des routes reporting et synchronisation, le compte SQL
dedie, la supervision et le durcissement de production restent a faire.

### Authentification

Le token transmis par le front doit etre valide cote FastAPI. Les endpoints
de reporting et de synchronisation doivent verifier les droits necessaires.

### CORS

Configurer les origines par environnement via `CORS_ALLOWED_ORIGINS`.
Ne pas conserver une configuration permissive en production.

### SQL

Utiliser un compte dedie avec :

- acces a `gpr_ai_reporting` uniquement ;
- aucun droit d'ecriture sur `gpr_sicma_online` ;
- aucun droit d'administration ;
- secrets injectes par variables d'environnement.

Les secrets presents ou ayant ete exposes dans les fichiers `.env` doivent
etre retires, revoques et renouveles.

## 13. Phase 9 - tests et validation

### Etat d'avancement

Les tests unitaires FastAPI du reporting et de la synchronisation couvrent
les contrats principaux, les agregations, les dates, les upserts, l'exclusion
`TEMP_SAVED` et les retards des statuts resolus. La compilation Python et
Spring Boot a ete validee. Les tests Spring Boot, les tests d'integration
bout en bout, l'authentification, les erreurs d'infrastructure et le test de
charge restent a completer.

### Tests FastAPI

Tester :

- validation des filtres ;
- dates invalides ;
- absence de donnees ;
- periodes ;
- agregations ;
- variations ;
- scoring ;
- anomalies ;
- alertes ;
- recommandations ;
- `/reporting/query` ;
- indisponibilite du LLM ;
- timeout ;
- erreur SQL ;
- authentification et CORS.

### Tests Spring Boot

Tester :

- pagination ;
- `updatedAfter` ;
- tri stable ;
- reponse vide ;
- champs facultatifs ;
- chargement sans N+1.

### Test bout en bout

```text
Spring Boot
  -> export pagine
  -> synchronisation FastAPI
  -> gpr_ai_reporting
  -> /reporting/dashboard
  -> React
```

Scenario minimal :

1. creer ou modifier un dossier ;
2. lancer la synchronisation ;
3. verifier l'upsert dans la base de reporting ;
4. appeler `/reporting/dashboard` ;
5. verifier la metrique dans React ;
6. poser une question via `/reporting/query`.

## 14. Ordre de livraison

### Lot 1 - Fondations

- valider le contrat metier ;
- creer les schemas Pydantic ;
- configurer la connexion SQL ;
- definir les migrations ;
- fixer les valeurs officielles.

### Lot 2 - Synchronisation

- enrichir `ExportClaimDto` ;
- ajouter pagination et `updatedAfter` ;
- creer `reporting_claim` ;
- implementer la synchronisation complete ;
- implementer la synchronisation incrementale.

### Lot 3 - Dashboard

- activer le routeur reporting ;
- implementer `/reporting/dashboard` ;
- implementer les filtres ;
- implementer les metriques ;
- implementer les graphiques ;
- implementer les details.

### Lot 4 - Intelligence metier

- implementer le score numerique deterministe, distinct du risque du motif ;
- implementer les anomalies ;
- persister les alertes ;
- generer les recommandations.

### Lot 5 - Assistant IA

- construire les catalogues de schema, metier et requetes ;
- implementer le retriever de sous-schema ;
- generer et valider les requetes SQL candidates ;
- executer sous controles stricts en lecture seule ;
- ajouter le parcours d'approbation des requetes reutilisables ;
- conserver le contrat API et les visualisations Chart.js.

### Lot 6 - Durcissement

- authentification des routes reporting et synchronisation ;
- CORS ;
- compte SQL dedie ;
- rotation des secrets ;
- tests d'integration ;
- test de charge ;
- supervision et alertes techniques.

## 15. Priorite immediate

Cette priorite suit la decision de migrer le chatbot vers Text-to-SQL gouverne
(section 11). L'ordre de livraison est :

1. inventorier la projection `gpr_ai_reporting`, les donnees sensibles, les
   regles d'acces et le dialecte SQL reel ;
2. definir les contrats versionnes d'intention, Schema Catalog, Business
   Catalog, SQL candidate et approbation ;
3. construire le Schema Catalog et le Business Catalog depuis la seule base
   analytique autorisee ;
4. implementer la resolution d'intention et la recherche exacte/semantique
   dans le Query Catalog ;
5. construire le Schema Retriever et le prompt de generation Nemotron pour
   transmettre uniquement le sous-schema requis ;
6. choisir et tester un parseur AST SQL, puis bloquer toute requete qui ne
   respecte pas les listes d'autorisation et les politiques de securite ;
7. implementer l'execution en lecture seule, les parametres lies, les limites
   de ressources et les traces d'audit ;
8. ajouter l'approbation humaine et le versionnement/desactivation des
   requetes reutilisables ;
9. valider les contrats de reponse et l'interface React sans regression du
   dashboard ;
10. effectuer une comparaison en mode observation avec le moteur actuel,
    puis activer progressivement le nouveau pipeline derriere un feature flag.

Ne pas retirer le moteur SQLAlchemy actuel avant que les tests de securite,
les tests de non-regression et les criteres de bascule de la phase 7 soient
atteints. L'approbation humaine porte sur l'ajout au Query Catalog ; elle
n'est pas exigee pour chaque execution candidate ayant passe les controles
automatiques.

Les autres chantiers de la plateforme restent egalement a suivre : qualite des
donnees sources, score et alertes avancees, recommandations, authentification,
compte SQL dedie, supervision et tests bout en bout Spring Boot.

## 16. Jeu de donnees de developpement

Un seeder Spring Boot reproductible est disponible dans
`configuration/DevelopmentDataSeeder.java`. Il est strictement active par
le profil `seed` et n'est donc jamais execute lors d'un demarrage normal.
Lorsqu'il est lance, il reinitialise les tables `gps_*` de la base metier de
developpement, recree les referentiels et genere :

- cinq motifs avec risques `MINEUR`, `MOYEN` et `GRAVE` ;
- des delais SLA differents par motif ;
- categories, produits, canaux et agences ;
- 39 dossiers analytiques avec plusieurs statuts, types, periodes, risques
  et equipes ;
- six dossiers `TEMP_SAVED` ;
- des textes accentues en UTF-8 ;
- un compte administrateur `admin@gpr.com` avec le mot de passe de
  developpement communique hors du code source.

Le lancement est volontairement explicite :

```powershell
$env:GPR_SERVER_MYSQL_DSN="jdbc:mysql://localhost:3306/gpr_sicma_online?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Africa/Porto-Novo&useUnicode=true&characterEncoding=UTF-8"
$env:GPR_SERVER_MYSQL_USERNAME="root"
$env:GPR_SERVER_MYSQL_PASSWORD="<mot-de-passe-local>"
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=seed
```

Cette operation est destructive et reservee a la base de developpement.
Apres le seeding, une synchronisation complete FastAPI doit etre lancee pour
reconstruire `gpr_ai_reporting`.
