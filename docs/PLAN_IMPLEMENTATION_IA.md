# Plan d'implementation recommande du service AI GPR

## Objectif

Permettre au service AI de s'ameliorer progressivement sans commencer directement
par le fine-tuning.

Le systeme doit d'abord connaitre le contexte de l'institution, appliquer les
regles metier, consulter une base de connaissances fiable, reutiliser les
reclamations validees et apprendre des corrections humaines. Le fine-tuning
interviendra ensuite, de maniere periodique et controlee.

## Principes directeurs

1. Les requetes `/analyze/` et `/search/` utilisent les index existants.
2. Une requete ne doit pas reconstruire un index complet.
3. Les donnees nouvelles sont synchronisees et indexees de maniere incrementale.
4. Les categories et motifs sont reindexees uniquement lorsqu'une version change.
5. Les connaissances institutionnelles sont separees des plaintes historiques.
6. Les donnees non validees ne doivent pas devenir des references fiables.
7. Le RAG sert a consulter des informations actualisees.
8. Le fine-tuning sert principalement a apprendre un comportement, un format et
   un style de classification ou de reponse.
9. Toute evolution du modele doit etre mesuree avant son deploiement.
10. Toutes les donnees, decisions, synchronisations et evolutions doivent etre
    auditables de bout en bout.

## Architecture cible

```text
Contexte institutionnel
    +
Regles metier
    +
Procedures et documents
    +
Exemples synthetiques
    +
Reclamations reelles validees
          |
          v
Synchronisation versionnee
          |
          v
Base SQL locale + index RAG ChromaDB
          |
          v
Analyse de la nouvelle reclamation
          |
          v
Recherche du contexte et des cas pertinents
          |
          v
Proposition du modele AI
          |
          v
Validation ou correction par un agent
          |
          +--> Mise a jour du RAG
          |
          +--> Dataset de fine-tuning periodique
```

## Les niveaux de connaissances de l'assistant

### Niveau 1 : instructions systeme

Informations courtes et critiques :

- role de l'assistant ;
- limites de son perimetre ;
- consignes de securite et de confidentialite ;
- obligation de ne pas inventer une information ;
- comportement lorsqu'une information est absente.

### Niveau 2 : contexte institutionnel

Informations relativement stables :

- identite et activites de l'institution ;
- pays, langues et devise ;
- produits et services ;
- canaux de contact ;
- organisation et equipes ;
- vocabulaire metier ;
- horaires et contraintes generales ;
- perimetre des demandes traitees.

### Niveau 3 : regles metier

Regles decisionnelles structurees :

- conditions de classification ;
- niveaux d'urgence ;
- regles d'escalade ;
- service responsable ;
- informations obligatoires ;
- actions interdites ;
- delais de traitement ;
- regles de confidentialite.

### Niveau 4 : documents et procedures

Documents consultables par RAG :

- procedures internes ;
- guides operationnels ;
- FAQ ;
- fiches produits ;
- modeles de reponses ;
- conditions generales ;
- notes de service ;
- regles reglementaires.

### Niveau 5 : exemples metier

Exemples synthetiques ou reels :

- plainte ;
- categorie ;
- motif ;
- urgence ;
- action recommandee ;
- solution ;
- source ;
- statut de validation.

### Niveau 6 : historique des reclamations

Reclamations et solutions reelles, indexees uniquement lorsqu'elles sont
eligibles et suffisamment fiables.

## Phase 0 - Audit et stabilisation de l'existant

### Objectifs

- verifier les donnees presentes dans ChromaDB ;
- distinguer les collections de reclamations et de categories ;
- verifier la coherence entre la base SQL, ChromaDB et le backend Java ;
- identifier les index obsoletes ou incomplets.

### Actions

1. Auditer les collections `claims` et `categories_motifs`.
2. Verifier les champs utilises pour les filtres :
   `categorie`, `motif_reclamation`, `claim_type`, `statut` et
   `satisfaction_status`.
3. Verifier les champs fournis par le backend Java :
   `id`, `updatedAt`, `statut_final`, `texte_solution`,
   `aiSuggestedCategory`, `aiSuggestedMotif` et `satisfactionStatus`.
4. Verifier la stabilite des identifiants utilises par ChromaDB.
5. Corriger les incoherences de nommage et de metadonnees.
6. Exclure les dossiers temporaires, incomplets ou non valides.

### Resultat attendu

Les donnees utilisees par l'AI sont identifiables, coherentes et tracables.

## Phase 1 - Formaliser le contexte institutionnel de base

### Objectif

Permettre a l'assistant de connaitre l'institution avant l'arrivee des plaintes
reelles.

### Referentiels a creer

#### `institution_profile`

- nom et role de l'institution ;
- secteur d'activite ;
- pays, langues et devise ;
- produits et services ;
- canaux disponibles ;
- horaires ;
- services internes ;
- limites du perimetre de l'assistant.

#### `business_rules`

- condition ;
- action attendue ;
- niveau de priorite ;
- niveau d'urgence ;
- service responsable ;
- conditions d'escalade ;
- version et date d'effet.

#### `categories_motifs`

- categorie ;
- motif ;
- description ;
- gravite ;
- exemples ;
- version du catalogue.

#### `procedures`

- categorie concernee ;
- etapes de traitement ;
- documents requis ;
- service responsable ;
- delai ;
- conditions d'escalade ;
- version et statut.

### Regles de gouvernance

Chaque connaissance doit avoir :

- une source ;
- un statut (`DRAFT`, `ACTIVE`, `ARCHIVED`) ;
- une version ;
- une date de debut d'effet ;
- une date de fin eventuelle ;
- un responsable ou validateur ;
- une date de mise a jour.

Chaque modification doit laisser une trace d'audit comprenant au minimum
l'auteur ou le systeme a l'origine de la modification, la date et l'heure,
l'ancienne et la nouvelle version, le motif du changement et la validation
associee lorsqu'elle est requise.

### Resultat attendu

L'institution dispose d'un referentiel de base valide, meme sans plaintes
reelles.

## Phase 2 - Ajouter les connaissances institutionnelles au RAG

### Objectif

Rendre les procedures et regles consultables sans modifier les poids du modele.

### Collection recommandee

```text
institution_context
```

Chaque document peut contenir :

```text
document_id
title
content
document_type
category
version
source
status
priority
effective_from
effective_until
validated
updated_at
```

### Fonctionnement

```text
Question ou plainte
    |
Recherche des passages pertinents
    |
Filtrage par statut, version et date d'effet
    |
Ajout du contexte au prompt
    |
Reponse du LLM
```

Les documents archives ou non valides ne doivent pas etre utilises comme
references actives.

### Resultat attendu

Le modele peut appliquer les informations de l'institution sans reentrainement
apres chaque changement de procedure.

## Phase 3 - Creer des exemples synthetiques de base

### Objectif

Demarrer le systeme avant de disposer d'un historique reel suffisant.

### Exemple

```text
Plainte : J'ai perdu ma carte bancaire.
Categorie : Carte bancaire
Motif : Carte perdue
Urgence : GRAVE
Action : Bloquer la carte et appliquer la procedure de remplacement.
```

Creer au minimum des exemples pour :

- chaque categorie ;
- chaque motif ;
- chaque niveau d'urgence ;
- les demandes hors perimetre ;
- les formulations courtes ;
- les fautes d'orthographe ;
- les cas ambigus ;
- les cas contenant plusieurs problemes.

### Regles

Les exemples synthetiques doivent etre marques :

```text
source = SYNTHETIC
validated = false
```

Ils peuvent servir au test et au demarrage du RAG, mais ne doivent pas etre
consideres comme des verites metier definitives sans validation.

### Resultat attendu

Le pipeline peut etre teste et demarre avec des connaissances de base sans
attendre les plaintes reelles.

## Phase 4 - Revoir la synchronisation des reclamations

### Fonctionnement cible

```text
Backend Java
    |
Recuperation incrementale avec updatedAt
    |
Mise a jour de reporting_claim
    |
Selection des dossiers eligibles au RAG
    |
Upsert des dossiers modifies uniquement
    |
Suppression des dossiers devenus invalides
```

### Regles de synchronisation

Utiliser :

- `source_claim_id` comme identifiant stable ;
- `source_updated_at` comme curseur de modification ;
- `last_successful_sync_at` comme etat de synchronisation.

Pour chaque dossier :

- nouveau dossier : insertion SQL et RAG ;
- dossier modifie : mise a jour SQL et RAG ;
- solution corrigee : remplacement du document et des metadonnees ;
- dossier rejete : suppression ou desactivation dans le RAG ;
- dossier supprime cote Java : suppression si l'API le signale.

L'option `REPORTING_ENABLE_RAG_SYNC` doit etre activee uniquement apres
validation des regles d'eligibilite et de qualite.

### Resultat attendu

Une modification du backend Java devient disponible dans le RAG apres la
prochaine synchronisation, sans reconstruire toute la collection.

## Phase 5 - Separer la synchronisation des requetes

### Endpoint `/search/`

```text
Plainte actuelle
    |
Embedding de la plainte
    |
Recherche dans ChromaDB
    |
Recuperation des solutions fiables
    |
Generation par le LLM
```

Cet endpoint ne doit pas :

- appeler le backend Java ;
- synchroniser la base SQL ;
- reconstruire un index ;
- recalculer les embeddings historiques.

### Endpoint `/analyze/`

```text
Plainte actuelle
    |
Utilisation de l'index categories_motifs existant
    |
Recherche des categories pertinentes
    |
Classification par le LLM
```

L'indexation du catalogue ne doit pas etre executee systematiquement a chaque
analyse.

### Resultat attendu

Les requetes sont rapides, previsibles et sans effet de bord global sur les
index.

## Phase 6 - Versionner les categories et motifs

### Probleme a corriger

Le catalogue `categories_motifs` est actuellement vide puis reconstruit lors
des classifications qui recoivent un catalogue. Ce comportement est couteux
et peut provoquer des conflits lors de requetes concurrentes.

### Fonctionnement recommande

1. Normaliser le catalogue recu.
2. Calculer une empreinte SHA-256.
3. Comparer l'empreinte a celle enregistree.
4. Ne reindexer que si l'empreinte a change.
5. Enregistrer la nouvelle version apres succes.

```text
Hash identique  -> reutiliser l'index existant
Hash different  -> reindexer et enregistrer le nouvel etat
```

### Etat a conserver

- `collection_name` ;
- `catalog_version` ;
- `catalog_hash` ;
- `last_synced_at` ;
- `vector_count` ;
- `sync_status`.

La table `reporting_sync_state` existante peut etre etendue ou completee par
une table dediee au catalogue.

### Endpoint recommande

```http
POST /sync/categories
```

Les analyses utilisent ensuite uniquement le catalogue versionne deja prepare.

### Resultat attendu

Les categories et motifs ne sont reindexees que lorsqu'ils ont reellement
change.

## Phase 7 - Rendre l'etat de synchronisation observable

### Endpoint recommande

```http
GET /sync/status
```

### Informations a exposer

- derniere synchronisation ;
- dernier curseur ;
- nombre recu ;
- nombre insere ;
- nombre mis a jour ;
- nombre supprime ;
- nombre indexe ;
- nombre en attente ;
- version et hash du catalogue ;
- statut et derniere erreur.

### Exemple

```json
{
  "claims": {
    "last_sync_at": "2026-09-16T20:00:00",
    "last_cursor": "2026-09-16T19:55:00",
    "indexed_count": 1450,
    "status": "healthy"
  },
  "categories": {
    "catalog_version": "v2026.09.16",
    "catalog_hash": "sha256:...",
    "indexed_count": 35,
    "status": "healthy"
  }
}
```

### Resultat attendu

L'equipe peut verifier si le RAG est a jour et diagnostiquer les echecs.

## Exigence transverse - Auditabilite de bout en bout

Tout le systeme doit etre auditable : donnees institutionnelles, documents,
regles, synchronisations, indexations, requetes, reponses AI, validations
humaines, datasets et versions de modeles.

### Traces a conserver

Pour chaque requete `/analyze/` ou `/search/`, conserver selon les exigences de
confidentialite :

- identifiant de correlation ;
- date et heure avec fuseau explicite ;
- identifiant du dossier ou de la session ;
- reference anonymisee de la requete ;
- version du prompt ;
- version du modele et parametres importants ;
- contexte institutionnel et regles utilises ;
- documents et exemples RAG recuperes ;
- scores de pertinence ;
- reponse produite ;
- erreurs, avertissements et duree de traitement.

Pour chaque synchronisation ou indexation, conserver :

- source et destination ;
- debut, fin et resultat ;
- curseur avant et apres ;
- version ou hash des donnees ;
- nombres recus, inseres, mis a jour, supprimes, ignores et indexes ;
- identifiants des elements concernes ou identifiant de lot ;
- utilisateur, service ou tache a l'origine ;
- details d'erreur en cas d'echec.

Pour chaque connaissance institutionnelle, conserver :

- identifiant stable ;
- source et empreinte d'integrite ;
- version et statut ;
- auteur et validateur ;
- dates de creation, de modification et d'effet ;
- historique des changements ;
- justification du remplacement ou de l'archivage.

Pour chaque feedback humain, conserver :

- prediction initiale ;
- correction ou decision finale ;
- role ou identifiant de l'agent ;
- date et heure ;
- justification lorsque necessaire ;
- statut avant et apres ;
- version du modele, du contexte et des regles.

Pour chaque modele ou dataset, conserver :

- identifiant et version ;
- origine et filtres des donnees ;
- hash de l'artefact ;
- date et responsable ;
- parametres d'entrainement ;
- resultats d'evaluation ;
- approbation et date de mise en production ;
- historique des remplacements ;
- possibilite de retour a la version precedente.

### Regles de protection

1. Utiliser un identifiant de correlation commun entre le backend Java, le
   service AI, la synchronisation et les actions de l'agent.
2. Separer les journaux techniques des journaux d'audit metier.
3. Proteger les traces contre les modifications non autorisees, avec un
   stockage append-only ou un mecanisme d'integrite.
4. Restreindre l'acces aux traces selon les roles.
5. Definir une duree de conservation et une procedure d'archivage.
6. Anonymiser ou proteger les donnees personnelles presentes dans les traces.
7. Journaliser les succes, les echecs et les changements, pas seulement les
   erreurs.

### Consultation d'un audit

Prevoir un endpoint autorise de consultation :

```http
GET /audit/{correlation_id}
```

Il doit permettre de reconstituer la chaine suivante :

```text
requete
    -> contexte et regles utilises
    -> documents RAG recuperes
    -> reponse AI
    -> validation ou correction humaine
    -> synchronisation
    -> version finale indexee
```

### Resultat attendu

Pour toute reponse, synchronisation ou evolution, une equipe autorisee peut
expliquer quelles donnees et versions ont ete utilisees, quelle decision a ete
produite, qui l'a validee et quelles modifications ont suivi.

## Phase 8 - Ajouter le feedback humain

### Objectif

Enregistrer les validations et corrections des agents pour distinguer les
predictions fiables des erreurs.

### Donnees a enregistrer

- identifiant du dossier ;
- prediction de categorie ;
- prediction de motif ;
- prediction d'urgence ;
- solution proposee ;
- categorie finale ;
- motif final ;
- urgence finale ;
- solution retenue ;
- statut de validation ;
- agent ;
- date de validation ;
- satisfaction client.

### Statuts recommandes

```text
PENDING
VALIDATED
CORRECTED
REJECTED
```

### Endpoints possibles

```http
POST /feedback
GET  /feedback/{claim_id}
PUT  /feedback/{feedback_id}
POST /feedback/{feedback_id}/validate
POST /feedback/{feedback_id}/reject
```

### Resultat attendu

Chaque correction devient traçable et exploitable pour le RAG et le dataset de
fine-tuning.

## Phase 9 - Controler la qualite des donnees du RAG

### A indexer en priorite

- dossiers clotures ;
- solutions renseignees ;
- categories confirmees ;
- motifs confirmes ;
- solutions validees par un agent ;
- dossiers satisfaits ;
- corrections recentes.

### A exclure

- `TEMP_SAVED` ;
- dossiers incomplets ;
- solutions vides ;
- predictions non verifiees ;
- reponses rejetees ;
- procedures archivees.

### Metadonnees recommandees

- `feedback_status` ;
- `is_agent_validated` ;
- `satisfaction_status` ;
- `validation_date` ;
- `quality_score` ;
- `source_updated_at` ;
- `catalog_version` ;
- `source` (`SYNTHETIC`, `REAL`, `INSTITUTIONAL`).

### Score de qualite initial

```text
+1 categorie validee
+1 motif valide
+1 solution validee
+1 client satisfait
-1 reponse rejetee
-1 dossier non resolu
```

Les resultats RAG doivent combiner :

- similarite semantique ;
- qualite de la solution ;
- validation humaine ;
- recurrence ;
- recence ;
- compatibilite avec le contexte institutionnel.

### Resultat attendu

Le LLM recoit en priorite des references fiables et pertinentes.

## Phase 10 - Evaluer le systeme actuel

### Jeu de test

Constituer un jeu de donnees independant avec :

- cas simples ;
- cas ambigus ;
- cas hors perimetre ;
- fautes d'orthographe ;
- formulations courtes ;
- plusieurs problemes ;
- exemples synthetiques valides ;
- exemples reels anonymises lorsqu'ils seront disponibles.

### Indicateurs de classification

- precision de la categorie ;
- precision du motif ;
- precision de l'urgence ;
- taux de correction agent ;
- taux de reponses `AUTRE`.

### Indicateurs de generation

- taux de solutions validees ;
- taux de rejet ;
- satisfaction ;
- respect du format ;
- informations inventees ;
- temps de reponse.

### Indicateurs de synchronisation

- delai entre modification Java et indexation ;
- donnees non indexees ;
- echecs de synchronisation ;
- reindexations completes ;
- upserts incrementaux ;
- suppressions correctement appliquees.

### Resultat attendu

Une reference mesurable existe avant chaque evolution.

## Phase 11 - Preparer le dataset de fine-tuning

Le dataset doit contenir principalement des exemples :

- valides par un agent ;
- corriges explicitement ;
- anonymises ;
- dedoublonnes ;
- suffisamment representatifs ;
- equilibres entre categories et motifs.

Les donnees synthetiques peuvent etre incluses si elles ont ete validees.

### Format de classification

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Tu es un assistant expert en classification des reclamations GPR."
    },
    {
      "role": "user",
      "content": "Plainte : Le client constate un prelevement inconnu."
    },
    {
      "role": "assistant",
      "content": "{\"category\":\"Fraude\",\"motif\":\"Prelevement non autorise\",\"urgence\":\"GRAVE\"}"
    }
  ]
}
```

### Separation des donnees

```text
80 % entrainement
10 % validation
10 % test
```

Un meme dossier ou une variante quasi identique ne doit pas apparaitre dans
plusieurs ensembles.

## Phase 12 - Realiser un fine-tuning cible

Commencer par une seule tache :

1. classification categorie/motif ;
2. niveau d'urgence ;
3. sortie JSON ;
4. generation de solution.

La classification est recommandee en premier car elle est plus facile a
mesurer.

Comparer :

```text
modele actuel sans RAG
modele actuel avec RAG
modele fine-tune avec RAG
```

Le fine-tuning ne doit etre conserve que s'il apporte une amelioration
mesurable sans augmenter les hallucinations ni degrader les cas rares.

Le fine-tuning ne remplace pas le RAG :

- le modele apprend le comportement et le format ;
- le RAG fournit les informations actualisees ;
- les regles critiques restent controlees par des donnees versionnees.

## Phase 13 - Valider et deployer progressivement

1. Tester hors production.
2. Comparer au modele actuel.
3. Executer les deux modeles en parallele.
4. Deployer aupres d'un groupe limite d'agents ou de categories.
5. Generaliser seulement si les indicateurs sont meilleurs ou equivalents.

Conserver pour chaque modele :

- version ;
- dataset utilise ;
- date d'entrainement ;
- parametres ;
- resultats d'evaluation ;
- statut de production.

Prevoir un retour vers la version precedente.

## Phase 14 - Mettre en place l'amelioration continue

```text
Dossier cree
    |
Prediction AI
    |
Correction ou validation humaine
    |
Synchronisation SQL
    |
Reindexation RAG incrementale
    |
Mise a jour des metriques
    |
Selection des meilleurs exemples
    |
Fine-tuning periodique
    |
Evaluation
    |
Deploiement si amelioration
```

### Frequences recommandees

| Operation | Frequence |
|---|---|
| Synchronisation des reclamations | Quotidienne ou incrementale |
| Reindexation apres validation | Immediate ou planifiee |
| Synchronisation des categories | A chaque changement de version |
| Synchronisation des documents institutionnels | A chaque nouvelle version |
| Evaluation qualite | Hebdomadaire |
| Nettoyage des donnees | Mensuel |
| Fine-tuning | Mensuel ou trimestriel |

## Decoupage des responsabilites

### Backend Java

- conserver les donnees metier ;
- gerer les versions du catalogue ;
- enregistrer les corrections et validations ;
- enregistrer la satisfaction ;
- exposer les donnees synchronisables ;
- signaler les changements et suppressions.

### Service Python AI

- analyser les reclamations ;
- consulter le contexte institutionnel ;
- gerer le RAG ;
- recevoir les feedbacks ;
- indexer les donnees eligibles ;
- exposer l'etat de synchronisation ;
- preparer et evaluer les datasets ;
- servir le modele selectionne.

### ChromaDB

- stocker le contexte institutionnel ;
- stocker les procedures actives ;
- stocker les categories et motifs versionnes ;
- stocker les exemples et reclamations eligibles ;
- retrouver les references pertinentes.

## Priorites d'implementation

### Priorite 1 - Fondations et synchronisation

1. Formaliser le contexte institutionnel.
2. Structurer les regles, categories, motifs et procedures.
3. Ajouter la collection `institution_context`.
4. Separer synchronisation et traitement des requetes.
5. Implementer la synchronisation incrementale des reclamations.
6. Versionner les categories et motifs.
7. Ajouter `/sync/status`.

### Priorite 2 - Qualite et feedback

8. Creer des exemples synthetiques de base.
9. Enregistrer les predictions.
10. Ajouter les validations et corrections agent.
11. Indexer uniquement les donnees fiables.
12. Ajouter un score de qualite.

### Priorite 3 - Evaluation

13. Creer le jeu de test.
14. Mesurer les performances actuelles.
15. Mesurer la qualite de la synchronisation.
16. Definir les criteres de reussite.

### Priorite 4 - Fine-tuning

17. Constituer le dataset valide.
18. Fine-tuner d'abord la classification.
19. Comparer avec le modele actuel.
20. Tester en parallele.
21. Deployer progressivement.
22. Planifier les entrainements periodiques.

## Criteres de reussite

Le systeme doit :

- appliquer correctement le contexte institutionnel ;
- utiliser les procedures actives et versionnees ;
- ne pas utiliser les documents archives ;
- ne pas reindexer a chaque requete ;
- repercuter les modifications Java de maniere incrementale ;
- conserver un etat de synchronisation observable ;
- reduire les corrections manuelles ;
- ameliorer la pertinence des solutions ;
- respecter le format attendu ;
- ne pas augmenter les hallucinations ;
- conserver un retour arriere possible pour chaque version de modele ;
- permettre un audit complet d'une reponse, d'une synchronisation, d'une
  correction humaine et d'une evolution de modele ;
- proteger les traces d'audit contre les modifications non autorisees ;
- respecter les regles de confidentialite, d'acces et de conservation.

## Plan resume

```text
1. Formaliser le contexte institutionnel
2. Structurer les regles et procedures
3. Ajouter le contexte au RAG
4. Creer des exemples synthetiques valides
5. Stabiliser la synchronisation des donnees
6. Separer synchronisation et requetes
7. Versionner les categories et motifs
8. Ajouter le suivi de synchronisation
9. Rendre les donnees et decisions auditables
10. Ajouter le feedback humain
11. Reindexer uniquement les donnees fiables
12. Mesurer les performances
13. Constituer le dataset
14. Fine-tuner la classification
15. Tester et deployer progressivement
16. Ameliorer periodiquement le systeme
```

## Conclusion

La cible finale est un systeme compose de :

```text
Contexte institutionnel versionne
    +
Regles metier controlees
    +
RAG synchronise et incrementiel
    +
Feedback humain
    +
Fine-tuning periodique
```

Le contexte de l'institution et les regles de base peuvent donc etre integres
des maintenant, meme sans plaintes reelles. Ils doivent d'abord etre stockes
comme connaissances versionnees et consultables par RAG. Le fine-tuning pourra
ensuite apprendre les comportements repetitifs a partir des exemples
synthetiques valides et des donnees reelles corrigees.
