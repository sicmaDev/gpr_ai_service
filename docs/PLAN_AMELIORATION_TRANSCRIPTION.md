# Plan d'amélioration du service de transcription

## 1. Contexte et état actuel

Le service actuel est implémenté dans `gpr_ai_service/app/routers/transcribe.py`.

Son fonctionnement est actuellement le suivant :

```text
Fichier audio WebM
    ↓
API Cloud compatible Groq/OpenAI
    ↓
Modèle whisper-large-v3-turbo
    ↓
Nettoyage basique du texte
    ↓
Réponse JSON
```

Le service prend en charge :

- l'upload d'un fichier audio ;
- l'enregistrement audio ;
- la transcription en français ;
- l'utilisation du modèle `whisper-large-v3-turbo` ;
- le nettoyage des balises, caractères parasites et espaces ;
- le retour du texte dans les champs `texte_transcrit` et `transcription`.

Les fonctionnalités suivantes ne sont pas encore prises en charge :

- prétraitement audio ;
- transcription brute distincte de la transcription corrigée ;
- segments et timestamps ;
- vocabulaire métier ;
- correction IA post-transcription ;
- diarisation des locuteurs ;
- traitement asynchrone des fichiers longs ;
- stockage détaillé du résultat.

## 2. Objectifs

L'amélioration doit permettre de :

1. augmenter la qualité de reconnaissance du français ;
2. préserver fidèlement le résultat original du Speech-to-Text ;
3. améliorer la lisibilité du texte sans inventer de contenu ;
4. retrouver chaque passage dans l'audio grâce aux timestamps ;
5. prendre en compte le vocabulaire métier GPR/SICMA ;
6. préparer la prise en charge de plusieurs locuteurs ;
7. conserver la compatibilité avec le client existant ;
8. rendre le traitement observable, auditable et résistant aux erreurs.

## 3. Architecture cible

```text
Client
  ↓
API de transcription
  ↓
Validation du fichier
  ↓
Prétraitement audio
  ↓
Speech-to-Text
  ↓
Transcription brute + segments + timestamps
  ↓
Correction IA contrôlée
  ↓
Structuration du texte
  ↓
Stockage du résultat
  ↓
Client : texte, audio, timestamps et locuteurs
```

Le résultat brut doit toujours être conservé séparément du résultat corrigé.

## 4. Phase 1 — Fiabiliser le service actuel

**État : implémentée dans la première tranche du service.**

### Actions

- vérifier qu'au moins un fichier audio est fourni ;
- valider la taille maximale du fichier ;
- valider le type MIME et l'extension ;
- refuser les fichiers vides ou invalides ;
- configurer le délai d'attente par variable d'environnement ;
- améliorer la gestion des erreurs HTTP et réseau ;
- ne pas retourner une erreur technique comme si elle était une transcription ;
- ajouter des logs structurés ;
- journaliser la taille du fichier, le modèle, la durée de traitement et le statut ;
- conserver le nom et le format originaux lorsque cela est possible.

### Résultat attendu

Le service reste compatible avec son utilisation actuelle, mais les erreurs sont explicites et les traitements sont plus faciles à diagnostiquer.

## 5. Phase 2 — Séparer la transcription brute et corrigée

**État : implémentée.**

### Principe

La réponse du modèle ne doit jamais être écrasée par le nettoyage ou par une correction IA.

### Format cible

```json
{
  "success": true,
  "transcription_raw": "bonjour à tous [bruit]",
  "transcription_corrected": "Bonjour à tous.",
  "texte_transcrit": "Bonjour à tous.",
  "correction_appliquee": true
}
```

### Règles

- `transcription_raw` contient le résultat original du modèle ;
- `transcription_corrected` contient le texte nettoyé et éventuellement corrigé ;
- `texte_transcrit` conserve temporairement la compatibilité avec le client existant ;
- aucune correction ne doit modifier `transcription_raw` ;
- les erreurs doivent être retournées via un statut et un message dédiés.

## 6. Phase 3 — Ajouter les segments et les timestamps

**État : implémentée.**

### Actions

- demander un format de réponse détaillé à l'API Speech-to-Text ;
- récupérer les segments retournés par le modèle ;
- conserver les temps de début et de fin ;
- associer chaque segment à son texte ;
- exposer les segments dans la réponse JSON.

### Format cible

```json
{
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 4.2,
      "text": "Bonjour à tous."
    }
  ]
}
```

### Bénéfices

- navigation entre l'audio et le texte ;
- recherche précise dans un enregistrement ;
- préparation de la diarisation ;
- meilleure traçabilité des corrections ;
- possibilité d'afficher une transcription synchronisée.

## 7. Phase 4 — Améliorer le traitement audio

**État : implémentée avec FFmpeg optionnel.**

Le prétraitement conserve toujours le fichier original. Lorsque FFmpeg est disponible, une copie normalisée est utilisée pour la transcription ; sinon, le service journalise l'indisponibilité et utilise l'audio original.

### Pipeline

```text
Audio original
    ↓
Conversion vers un format normalisé
    ↓
Réduction du bruit
    ↓
Normalisation du volume
    ↓
Réduction des silences trop longs
    ↓
Speech-to-Text
```

### Actions

- convertir les fichiers vers un format stable, par exemple WAV ;
- normaliser le niveau sonore ;
- réduire les bruits constants et l'écho lorsque cela est possible ;
- détecter les fichiers silencieux ;
- supprimer uniquement les silences excessifs ;
- découper les fichiers très longs en morceaux ;
- conserver le fichier original sans le remplacer.

### Précaution

Le prétraitement doit être mesuré et réversible. Un filtrage trop agressif peut dégrader la voix et réduire la qualité de transcription.

## 8. Phase 5 — Ajouter le vocabulaire métier

**Périmètre défini avec le métier : réclamations et service client bancaire.**

La première version doit couvrir les produits et opérations bancaires courants, sans activer automatiquement les corrections avant validation.

### Vocabulaire initial proposé

#### Réclamations et relation client

```text
réclamation
plainte
demande
réclamation client
service client
conseiller
agence
guichet
centre d'appel
réclamation non traitée
réclamation en retard
réponse client
suivi de dossier
référence de dossier
médiateur
réclamation escaladée
insatisfaction
remboursement
geste commercial
indemnisation
```

#### Comptes et moyens de paiement

```text
compte courant
compte bancaire
compte épargne
livret
solde
relevé de compte
relevé bancaire
relevé d'identité bancaire
RIB
IBAN
carte bancaire
carte Visa
carte Mastercard
carte prépayée
carte bloquée
carte perdue
carte volée
opposition
code PIN
paiement
paiement sans contact
paiement en ligne
achat contesté
transaction
retrait
distributeur automatique
DAB
```

#### Opérations et frais

```text
virement
virement instantané
prélèvement
prélèvement contesté
transfert
dépôt
retrait
découvert
agios
frais bancaires
frais de tenue de compte
commission
commission d'intervention
date de valeur
crédit du compte
débit du compte
remise gracieuse
```

#### Crédits et incidents

```text
crédit
prêt
prêt immobilier
prêt automobile
crédit à la consommation
échéance
mensualité
tableau d'amortissement
renégociation
taux d'intérêt
retard de paiement
incident de paiement
découvert autorisé
```

#### Sécurité et fraude

```text
fraude
tentative de fraude
arnaque
piratage
vol
usurpation d'identité
transaction frauduleuse
transaction non autorisée
authentification
code de sécurité
mot de passe
accès bloqué
```

#### Canaux numériques

```text
application mobile
espace client
espace sécurisé
connexion
identifiant
mot de passe oublié
Face ID
Touch ID
SMS
notification
```

### Vocabulaire bancaire détaillé fourni pour la première version

#### Réclamations et service client

```text
réclamation, plainte, demande client, requête, doléance, incident,
insatisfaction, litige, contestation, réclamation bancaire, réclamation client,
traitement de réclamation, suivi de réclamation, clôture de réclamation,
numéro de réclamation, dossier client, service client, conseiller clientèle,
chargé de clientèle, agence, centre de relation client, centre d'appel,
satisfaction client, délai de traitement, accusé de réception, escalade,
réponse client, résolution, médiation
```

#### Comptes bancaires

```text
compte courant, compte d'épargne, compte bancaire, compte professionnel,
compte entreprise, compte joint, compte individuel, ouverture de compte,
clôture de compte, solde, relevé de compte, relevé bancaire, domiciliation,
titulaire, cotitulaire, bénéficiaire, RIB, IBAN, numéro de compte
```

#### Opérations courantes

```text
virement, transfert, dépôt, retrait, versement, prélèvement, encaissement,
décaissement, paiement, paiement en ligne, paiement marchand, transaction,
opération bancaire, solde disponible, historique des transactions,
frais bancaires, commission, agios, date de valeur
```

#### Cartes et moyens de paiement

```text
carte bancaire, carte de débit, carte de crédit, carte prépayée, carte Visa,
carte Mastercard, retrait DAB, retrait GAB, distributeur automatique, DAB,
GAB, TPE, terminal de paiement, paiement par carte, carte bloquée,
carte expirée, carte avalée, opposition, code PIN, plafond,
paiement sans contact
```

#### Crédits

```text
crédit, prêt, crédit immobilier, crédit à la consommation,
crédit professionnel, crédit entreprise, crédit personnel, demande de crédit,
dossier de crédit, échéance, mensualité, taux d'intérêt, taux débiteur,
taux effectif global, TEG, durée du prêt, capital, principal, intérêts,
remboursement, remboursement anticipé, impayé, retard de paiement,
échéancier, garantie, caution, nantissement, hypothèque
```

#### Sécurité et fraude

```text
fraude, tentative de fraude, transaction frauduleuse, opération suspecte,
transaction suspecte, phishing, hameçonnage, usurpation d'identité, vol,
carte volée, carte perdue, compte compromis, authentification,
double authentification, code OTP, code de sécurité, opposition, blocage,
déblocage
```

#### Contexte UEMOA/BCEAO

```text
BCEAO, UEMOA, FCFA, XOF, établissement de crédit,
institution de microfinance, SFD, monnaie électronique, mobile money,
portefeuille électronique, transfert d'argent, paiement mobile, agent,
point de service, bénéficiaire, compte mobile
```

#### Acronymes et formes développées

| Acronyme | Forme développée |
|---|---|
| BCEAO | Banque Centrale des États de l'Afrique de l'Ouest |
| UEMOA | Union Économique et Monétaire Ouest-Africaine |
| DAB | Distributeur Automatique de Billets |
| GAB | Guichet Automatique Bancaire |
| TPE | Terminal de Paiement Électronique |
| RIB | Relevé d'Identité Bancaire |
| IBAN | International Bank Account Number |
| PIN | Personal Identification Number |
| OTP | One-Time Password |
| KYC | Know Your Customer |
| AML | Anti-Money Laundering |
| LCB-FT | Lutte contre le blanchiment de capitaux et le financement du terrorisme |
| TEG | Taux Effectif Global |
| KRI | Key Risk Indicator |

Cette liste est la base de cadrage de la phase 5. Elle doit être nettoyée, dédoublonnée et validée avant activation comme dictionnaire de correction automatique.

### Termes exclus du vocabulaire bancaire actif

Les termes suivants sont considérés comme invalides pour le vocabulaire métier bancaire de la transcription et ne doivent pas être transmis au modèle :

```text
SICMA
FinGovTool
KRI
DMR
risque opérationnel
risque de liquidité
contrôle interne
cartographie des risques
plan d'action
audit
```

### Règle d'activation

Cette liste constitue une proposition de travail. Chaque terme ou variante doit être validé avant son utilisation comme correction automatique. Les corrections proposées doivent rester séparées du vocabulaire validé.

### Implémentation de la phase 5

**État : implémentée avec un vocabulaire bancaire versionné.**

- vocabulaire centralisé dans `app/data/transcription_vocabulary.json` ;
- catégories bancaires et UEMOA/BCEAO structurées ;
- acronymes et formes développées conservés ;
- vocabulaire transmis au Speech-to-Text via le champ `prompt` ;
- termes exclus explicitement absents du vocabulaire actif ;
- tests de présence et d'exclusion ajoutés ;
- aucune correction automatique n'est appliquée sans validation ultérieure.

### Actions restantes

- centraliser le vocabulaire dans une configuration dédiée ;
- permettre sa mise à jour sans modifier le code principal ;
- transmettre le vocabulaire au service Speech-to-Text lorsque l'API le permet ;
- appliquer des corrections lexicales contrôlées après transcription ;
- gérer les acronymes, noms propres et variantes courantes ;
- journaliser les corrections automatiques appliquées.

### Règle de sécurité

Les remplacements doivent être suffisamment précis pour ne pas modifier le sens d'une phrase ou transformer un mot courant en terme métier à tort.

### Sélection dynamique et double transcription

Les informations de contexte utilisées pour sélectionner le vocabulaire proviennent des champs saisis dans l'interface front-end. Elles doivent être considérées comme des **indices non fiables** et jamais comme une vérité métier :

```text
Champs du front
    ↓
Contexte indicatif
    ↓
Sélection initiale du vocabulaire
```

Le service doit toujours effectuer deux transcriptions :

```text
Audio
  ↓
Première transcription
  ├── contexte front indicatif
  └── vocabulaire global + vocabulaire contextuel présélectionné
  ↓
Analyse de la transcription obtenue
  ├── détection du domaine réel
  ├── score de confiance
  └── détection des termes suspects
  ↓
Seconde transcription obligatoire
  └── vocabulaire sélectionné à partir de l'audio et de la première transcription
  ↓
Résultat final
```

La première transcription ne doit pas être considérée comme le résultat final. Elle sert à confronter les indications du front au contenu réellement détecté dans l'audio.

Le résultat doit conserver les deux sorties afin de garantir la traçabilité :

```text
transcription_pass1_raw
transcription_pass2_raw
transcription_raw
transcription_corrected
```

`transcription_raw` correspond à la seconde transcription, sauf si celle-ci échoue explicitement. Dans ce cas, le service doit retourner la première transcription avec un statut d'avertissement et l'erreur associée.

La seconde transcription est obligatoire par défaut, même lorsque le front fournit une catégorie, un produit ou un motif. Cette règle protège le service contre les valeurs saisies au hasard, incomplètes ou incorrectes.

### Activation configurable de la seconde transcription

Le service doit disposer d'une variable d'environnement permettant d'activer ou de désactiver la seconde passe :

```env
TRANSCRIPTION_SECOND_PASS=true
```

Valeurs acceptées :

```text
true, 1, yes, on  → seconde transcription activée
false, 0, no, off → seconde transcription désactivée
```

Le comportement recommandé est :

```text
Variable absente       → seconde transcription activée
Valeur invalide        → démarrage refusé avec une erreur de configuration
Seconde passe activée  → deux appels Speech-to-Text
Seconde passe désactivée → un seul appel Speech-to-Text
```

Lorsque la seconde passe est désactivée, le service doit utiliser la première transcription comme résultat brut et retourner explicitement le mode employé :

```json
{
  "transcription_passes": 1,
  "second_pass_enabled": false,
  "transcription_status": "COMPLETED_SINGLE_PASS"
}
```

Lorsque la seconde passe est activée :

```json
{
  "transcription_passes": 2,
  "second_pass_enabled": true,
  "transcription_status": "COMPLETED_TWO_PASS"
}
```

La valeur effective de cette variable doit être journalisée, afin de connaître le mode utilisé pour chaque transcription. La désactivation est destinée aux tests, au diagnostic, à la maîtrise des coûts ou aux environnements où une seule passe est souhaitée ; elle ne doit pas être le comportement par défaut en production.

### Implémentation appliquée

La sélection dynamique est implémentée dans `app/services/vocabulary_selector.py`.

Les champs facultatifs envoyés par le front sont :

```text
vocabulary_context
claim_category
product
reason
```

Ils sont traités comme des indices et combinés avec le texte disponible. Le sélecteur :

- conserve un vocabulaire global limité ;
- sélectionne jusqu'à trois catégories pertinentes ;
- pondère les catégories par score ;
- ajoute le produit fourni comme terme spécifique ;
- déduplique les termes ;
- applique les limites de nombre et de caractères.

Les limites sont configurables :

```env
TRANSCRIPTION_VOCABULARY_MAX_TERMS=50
TRANSCRIPTION_VOCABULARY_MAX_CHARS=1200
TRANSCRIPTION_VOCABULARY_GLOBAL_TERMS=15
TRANSCRIPTION_VOCABULARY_CONTEXT_TERMS=25
TRANSCRIPTION_VOCABULARY_PRODUCT_TERMS=10
```

La seconde passe utilise le même fichier audio prétraité que la première et reçoit une sélection recalculée à partir du résultat de la première passe. La réponse expose le nombre de passes, le mode actif, les deux transcriptions brutes et la sélection de vocabulaire utilisée.

## 9. Phase 6 — Ajouter une correction IA contrôlée

**État : implémentée avec fallback vers le texte brut.**

### Pipeline

```text
Speech-to-Text
    ↓
transcription_raw
    ↓
Correction IA
    ↓
transcription_corrected
```

### Corrections autorisées

- ponctuation ;
- majuscules ;
- fautes évidentes ;
- répétitions manifestement inutiles ;
- découpage en phrases et paragraphes ;
- termes du vocabulaire métier ;
- noms propres connus.

### Contraintes du prompt

Le système de correction doit impérativement :

- conserver le sens original ;
- ne pas ajouter d'informations ;
- ne pas résumer ;
- ne pas supprimer une information importante ;
- conserver les incertitudes ;
- signaler les passages incompréhensibles au lieu de les inventer ;
- ne jamais modifier la transcription brute.

### Gestion des erreurs

Si le service de correction est indisponible, la transcription brute nettoyée doit rester disponible et être explicitement identifiée comme telle.

La correction est configurable avec :

```env
TRANSCRIPTION_AI_CORRECTION=true
```

La réponse expose `correction_ai_status`, avec notamment les valeurs `APPLIED`, `DISABLED`, `EMPTY` et `FALLBACK_RAW`.

## 10. Phase 7 — Structurer le résultat

**État : implémentée.**

### Format cible

```json
{
  "language": "fr",
  "duration": 125.4,
  "transcription_raw": "...",
  "transcription_corrected": "...",
  "segments": [
    {
      "start": 0.0,
      "end": 12.5,
      "text": "..."
    }
  ],
  "speakers": null
}
```

La transcription, l'analyse et le résumé doivent rester des étapes distinctes :

- la transcription décrit ce qui a été dit ;
- la correction améliore la lisibilité ;
- la structuration organise le contenu ;
- le résumé et l'extraction d'actions interprètent le contenu.

Le service expose désormais `transcription_structuree`, avec les paragraphes,
les phrases, les identifiants de segments et les bornes temporelles lorsqu'elles
sont disponibles. Les métadonnées de structure (`word_count`,
`character_count`, `paragraph_count` et `sentence_count`) sont exposées dans
`metadata`. Cette étape est déterministe : elle ne modifie pas le contenu, ne
résume pas et n'ajoute aucune information.

## 11. Phase 8 — Ajouter la diarisation

**État : implémentée avec intégration des locuteurs fournis par le moteur STT.**

### Objectif

Identifier les différents locuteurs dans une réunion, une interview ou un appel.

### Format cible

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 4.2,
      "speaker": "SPEAKER_00",
      "text": "Bonjour à tous."
    },
    {
      "start": 4.2,
      "end": 8.7,
      "speaker": "SPEAKER_01",
      "text": "Bonjour."
    }
  ]
}
```

La réponse conserve les locuteurs présents dans les segments et expose
`speakers`, `diarization_status` et `diarization_enabled`. Le traitement est
contrôlé par :

```env
TRANSCRIPTION_DIARIZATION=false
```

Lorsque le moteur STT ne fournit aucun locuteur, le statut devient
`UNAVAILABLE` plutôt que d'inventer une attribution. Une intégration avec un
moteur de diarisation audio dédié pourra être ajoutée ultérieurement sans
modifier le contrat de réponse.

## 12. Phase 9 — Adapter le stockage côté backend

**État : implémentée côté service IA et backend Java.**

Le backend Java gère actuellement les audios et le statut `transcriptionAdded`, notamment dans :

- `gpr_server_sicma_new_version/src/main/java/com/sicmagroup/gpr/domain/model/ClaimAudio.java` ;
- `gpr_server_sicma_new_version/src/main/java/com/sicmagroup/gpr/api/claimAudio/ClaimAudioController.java`.

### Données à prévoir

```text
audio_original
transcription_raw
transcription_corrected
segments_json
speakers_json
language
duration
transcription_status
transcription_error
model_name
created_at
updated_at
```

### Statuts recommandés

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

Pour les fichiers longs, le traitement doit progressivement devenir asynchrone afin d'éviter les délais d'attente HTTP trop importants.

Le service expose désormais `storage_payload`, construit par
`transcription_storage.py`. Le backend Java persiste ce payload dans
`gps_claim_audio` et expose `PUT /api/v1/claimaudio/transcription/{id}`.
Les réponses audio incluent également les données de transcription disponibles.
Le schéma Hibernate `ddl-auto=update` ajoute les colonnes sur les
environnements existants ; une migration SQL dédiée pourra être ajoutée si la
gestion de schéma est ultérieurement généralisée à cette table.

## 13. Phase 10 — Adapter l'interface utilisateur

**État : première intégration implémentée.**

L'interface pourra proposer :

- l'affichage de la transcription corrigée par défaut ;
- l'affichage optionnel de la transcription brute ;
- des timestamps cliquables ;
- la lecture audio synchronisée avec le texte ;
- l'affichage des locuteurs lorsqu'ils sont disponibles ;
- un indicateur de progression ;
- un message explicite en cas d'échec ;
- la possibilité de signaler une correction incorrecte.

Le client existant sauvegarde désormais la transcription complète des audios
déjà persistés via `PUT /api/v1/claimaudio/transcription/{id}` après une
transcription réussie. Il affiche prioritairement `transcription_corrected`
et réutilise cette valeur depuis le backend lorsqu'elle existe.
`transcriptionAdded` reste réservé à l'action volontaire « Ajouter au
contenu » : la génération ou la sauvegarde d'une transcription ne coche pas
automatiquement cet indicateur.

## 14. Phase 10 bis — Mettre en place le plan de correction fiable

**État : première tranche implémentée.**

Le service sépare maintenant le texte nettoyé (`transcription_cleaned`) du
texte corrigé (`transcription_corrected`). La correction IA conserve le texte
original et retourne `REVIEW_REQUIRED` lorsqu'une information protégée risque
d'être supprimée. La détection générique de cohérence, la réécoute ciblée et
la validation dans l'interface restent à implémenter.

### Objectif

Corriger les erreurs de reconnaissance sans demander au LLM d'inventer le contenu
prononcé. Le cas de référence est :

```text
Audio réel : Cela fait deux mois que le client...
ASR        : Cela fait de nous que le client...
Correction : Cela fait que le client...
```

La correction doit préserver l'information même lorsqu'elle est ambiguë. Le
vocabulaire aide à reconnaître les termes métier, mais il ne doit pas être
utilisé comme solution principale aux erreurs générales de dates, durées ou
nombres.

### Architecture de correction

```text
Transcription ASR + segments + timestamps
                    ↓
          Analyse de cohérence
                    ↓
          ┌─────────┴─────────┐
          │                   │
       Cohérent            Suspect
          │                   │
          ↓                   ↓
         Fin          Extraction audio ciblée
                                  ↓
                         Retranscription ASR
                                  ↓
                            Hypothèses
                                  ↓
                     Validation audio et contexte
                         ┌────────┴────────┐
                         │                 │
                    suffisamment sûr   incertain
                         │                 │
                         ↓                 ↓
                    Remplacement     REVIEW_REQUIRED
```

### Étape 1 — Protéger la transcription

- conserver `transcription_raw` sans aucune modification ;
- séparer le nettoyage technique de la correction sémantique ;
- conserver `transcription_cleaned` et `transcription_corrected` séparément ;
- interdire au LLM de supprimer silencieusement un nombre, une date, une durée,
  un montant, une négation, un nom propre, une référence ou un produit ;
- conserver le texte original si aucune validation suffisante n'est disponible.

### Étape 2 — Détecter les anomalies

Créer un détecteur combinant règles déterministes, informations ASR et analyse
linguistique. Il doit rechercher notamment :

- une expression incohérente dans son contexte ;
- un mot ou segment à faible confiance ;
- une durée, date, quantité ou montant mal formé ;
- une négation possiblement perdue ;
- un mot manquant ou une répétition anormale ;
- une information incompatible avec la phrase environnante.

Exemple de résultat :

```json
{
  "type": "TEMPORAL_EXPRESSION",
  "text": "de nous",
  "start": 0.61,
  "end": 1.24,
  "severity": "HIGH",
  "action": "TARGETED_RETRANSCRIPTION"
}
```

Le LLM peut signaler une incohérence, mais ne peut pas valider seul le texte
qui doit remplacer le passage suspect.

### Étape 3 — Réécouter le passage suspect

- utiliser les timestamps mot à mot lorsqu'ils sont disponibles ;
- ajouter une marge avant et après le passage ;
- extraire un fichier audio temporaire sans modifier l'original ;
- conserver les bornes utilisées dans le résultat et dans l'audit ;
- ne pas lancer une réécoute si le texte est déjà cohérent et suffisamment
  fiable.

```text
passage suspect : 0.61 - 1.24
marge avant     : 0.20
marge après     : 0.20
extrait analysé : 0.41 - 1.44
```

### Étape 4 — Retranscrire et comparer

La retranscription ciblée doit recevoir :

- l'extrait audio ;
- le contexte de la phrase ;
- la catégorie détectée ;
- le vocabulaire métier pertinent uniquement ;
- les paramètres ASR utilisés.

Le service doit conserver toutes les hypothèses obtenues :

```json
{
  "original": "de nous",
  "hypotheses": [
    {"text": "de nous", "source": "initial_asr"},
    {"text": "deux mois", "source": "targeted_asr"}
  ],
  "selected": "deux mois",
  "confidence": 0.76
}
```

Les hypothèses ne doivent pas être transformées artificiellement en scores si
le fournisseur ne retourne pas de probabilités exploitables.

### Étape 5 — Valider avant remplacement

Un remplacement automatique est autorisé uniquement si :

- le candidat provient d'une retranscription de l'audio ciblé ;
- les timestamps correspondent au passage remplacé ;
- le candidat est cohérent avec le contexte ;
- aucune information protégée n'est supprimée sans preuve ;
- le niveau de confiance minimal configuré est atteint.

Sinon, le texte original est conservé et le statut devient :

```text
REVIEW_REQUIRED
```

Le LLM peut reformuler la ponctuation et la présentation, mais il ne peut pas
inventer une durée, un montant, une date ou un nom absent des résultats ASR.

### Étape 6 — Produire un audit complet

Chaque correction doit conserver :

```json
{
  "original_text": "Cela fait de nous que...",
  "corrected_text": "Cela fait deux mois que...",
  "correction_source": "TARGETED_ASR",
  "confidence": 0.76,
  "validated_by_audio": true,
  "validated_by_user": false,
  "model": "whisper-large-v3-turbo",
  "created_at": "..."
}
```

Les statuts recommandés sont :

- `NOT_REQUIRED` ;
- `PROPOSED` ;
- `APPLIED` ;
- `REVIEW_REQUIRED` ;
- `REJECTED` ;
- `FALLBACK_RAW`.

### Étape 7 — Préparer la validation dans l'interface

L'interface doit pouvoir :

- rendre le timestamp suspect cliquable ;
- lire uniquement l'extrait concerné ;
- afficher le texte original et la proposition ;
- afficher la source et la confiance ;
- accepter ou refuser la correction ;
- conserver la décision de l'agent dans l'audit.

La validation d'une correction ne doit jamais modifier automatiquement
`transcriptionAdded`, qui reste réservé à l'ajout manuel du contenu par
l'agent.

### Catégories d'informations protégées

Les catégories suivantes doivent être traitées avec le niveau de prudence le
plus élevé :

- montants et devises ;
- dates et heures ;
- durées et délais ;
- nombres et références ;
- numéros de compte ou de dossier ;
- noms de personnes, agences et produits ;
- négations ;
- obligations, refus et engagements.

### Critères d'acceptation du plan de correction

- une correction grammaticale ne peut plus supprimer une information
  potentiellement métier ;
- les erreurs de cohérence, dont les expressions temporelles mal reconnues,
  sont traitées par le détecteur générique et peuvent déclencher une réécoute
  ciblée lorsque les timestamps sont disponibles ;
- une correction non validée conserve le texte brut et retourne
  `REVIEW_REQUIRED` ;
- chaque remplacement est explicable par une source audio, un timestamp et un
  modèle ;
- les hypothèses sont conservées sans inventer de scores ;
- une correction rejetée n'est pas réappliquée automatiquement ;
- l'audio original reste inchangé ;
- le vocabulaire reste ciblé sur les termes métier rares et spécialisés.

## 15. Phase 11 — Mettre en place l'apprentissage continu contrôlé

### Objectif

Permettre au service de s'améliorer progressivement à partir des corrections humaines validées, sans réentraîner automatiquement le modèle Speech-to-Text à chaque utilisation.

### Principe

```text
Audio
  ↓
Speech-to-Text
  ↓
Transcription brute
  ↓
Correction IA + vocabulaire
  ↓
Transcription corrigée
  ↓
Validation humaine
  ↓
Base d'apprentissage
  ↓
Amélioration des prochaines transcriptions
```

### Niveaux d'apprentissage

#### Niveau 1 — Apprentissage du vocabulaire

Le système doit pouvoir mémoriser les termes métier validés, les acronymes, les noms propres, les erreurs fréquentes et leurs corrections.

Exemples :

```text
"cri de liquidité" → "KRI de liquidité"
"fin gov tool" → "FinGovTool"
"DME" → "DMR"
```

#### Niveau 2 — Apprentissage du contexte

Le système peut conserver les associations fréquentes entre termes afin d'améliorer la correction dans son contexte métier.

Exemple :

```text
risque + KRI + seuil + fréquence
```

Ces associations servent uniquement de signaux de correction et ne doivent jamais être utilisées pour inventer du contenu absent de l'audio.

#### Niveau 3 — Préparation d'une adaptation du modèle

Les couples suivants peuvent être conservés afin de constituer un jeu de données de qualité :

```text
Audio original
    +
Transcription brute
    +
Transcription corrigée et validée
```

Lorsque le volume et la qualité des données sont suffisants, ce jeu de données pourra servir à évaluer ou fine-tuner un modèle spécialisé. Cette étape reste séparée de l'apprentissage automatique quotidien.

### Données à enregistrer

```text
audio_id
segment_id
transcription_raw
transcription_corrected
term_source
term_target
context
status
confidence
validated_by
validated_at
created_at
```

### Statuts recommandés

```text
PROPOSED
VALIDATED
REJECTED
DISABLED
```

### Règles de validation

- une correction ne devient pas automatiquement une connaissance ;
- une validation humaine est nécessaire avant son application globale ;
- les corrections rejetées ne doivent pas être reproposées indéfiniment ;
- chaque correction doit être désactivable et réversible ;
- les corrections doivent rester liées à leur source et à leur contexte ;
- les variantes concurrentes doivent être conservées plutôt qu'écrasées ;
- les données sensibles doivent respecter les règles de confidentialité du projet.

### Seuils d'automatisation

Une correction peut être proposée automatiquement lorsqu'elle est fréquente, mais son activation globale doit dépendre de critères explicites :

- nombre minimal d'occurrences ;
- nombre minimal de validations distinctes ;
- taux de validation minimal ;
- absence de rejet récent ;
- cohérence avec le vocabulaire métier actif.

Le seuil doit être configurable et son activation doit rester auditable.

### Résultat attendu

Le service dispose de trois espaces distincts :

```text
Vocabulaire validé
Corrections proposées
Données validées pour une future adaptation du modèle
```

Cette séparation empêche une correction incertaine de dégrader le vocabulaire ou le modèle.

## 16. Phase 12 — Superviser et mesurer l'apprentissage

### Indicateurs à suivre

- nombre de corrections proposées, validées, rejetées et désactivées ;
- fréquence de chaque correction ;
- taux de validation ;
- taux d'annulation après activation ;
- qualité par modèle et par version du vocabulaire ;
- amélioration observée sur un jeu de test de référence ;
- nombre de corrections par type d'audio et contexte métier.

### Actions

- créer une interface de validation ;
- permettre la recherche et le filtrage des corrections ;
- afficher l'historique des changements ;
- versionner le vocabulaire actif ;
- permettre un retour arrière vers une version précédente ;
- tester chaque nouvelle version sur un jeu de données stable avant activation.

## 17. Ordre de mise en œuvre recommandé

### Version 1 — Fiabilisation

1. validation des fichiers ;
2. gestion robuste des erreurs ;
3. logs et configuration des délais ;
4. conservation de `transcription_raw` ;
5. réponse structurée compatible avec les champs actuels.

### Version 2 — Qualité et traçabilité

1. format détaillé Speech-to-Text ;
2. segments et timestamps ;
3. vocabulaire métier ;
4. détection de cohérence ;
5. réécoute et retranscription ciblée ;
6. correction IA contrôlée et sécurisée ;
7. audit des corrections ;
8. tests de non-invention et de conservation du sens.

### Version 3 — Apprentissage continu contrôlé

1. validation humaine des corrections ;
2. enregistrement des corrections validées ;
3. apprentissage du vocabulaire ;
4. comptage des occurrences et calcul de confiance ;
5. activation réversible des corrections fiables ;
6. stockage des exemples audio et texte pour une adaptation future ;
7. versionnement et supervision du vocabulaire.

### Version 4 — Traitement avancé

1. prétraitement audio ;
2. découpage des fichiers longs ;
3. traitement asynchrone ;
4. diarisation ;
5. stockage des segments ;
6. synchronisation audio-texte dans l'interface.

## 18. Tests et critères d'acceptation

### Tests fonctionnels

- transcription d'un fichier WebM valide ;
- transcription d'un enregistrement audio ;
- rejet d'un fichier vide ;
- rejet d'un type non supporté ;
- gestion d'une clé API absente ;
- gestion d'une erreur de l'API Cloud ;
- prise en charge du texte saisi en complément de l'audio ;
- conservation de la transcription brute ;
- présence des timestamps lorsque le format détaillé est activé.

### Tests de qualité

- audio français propre ;
- audio avec bruit de fond ;
- audio avec accent ;
- termes métier et acronymes ;
- phrases répétées ;
- fichier long ;
- plusieurs locuteurs ;
- passage inaudible ou ambigu.
- correction utilisateur validée puis réutilisée sur une transcription similaire ;
- correction utilisateur rejetée et vérification qu'elle n'est pas appliquée ;
- désactivation d'une correction précédemment activée ;
- conflit entre deux corrections pour un même terme ;
- retour arrière d'une version du vocabulaire ;
- absence de fuite de données sensibles dans la base d'apprentissage.

### Critères d'acceptation

- aucune correction ne modifie `transcription_raw` ;
- aucune erreur technique n'est présentée comme une transcription réussie ;
- les erreurs sont visibles et exploitables ;
- les anciens champs `texte_transcrit` et `transcription` restent disponibles pendant la transition ;
- les corrections IA n'ajoutent pas de faits absents de l'audio ;
- les segments restent alignés avec l'audio ;
- le fichier original reste conservé.
- aucune correction non validée n'est appliquée globalement ;
- chaque connaissance apprise est traçable, réversible et associée à une validation ;
- une correction rejetée n'est pas réintroduite automatiquement ;
- le vocabulaire peut être versionné et restauré ;
- le réentraînement du modèle ne se déclenche jamais automatiquement sans validation du jeu de données.

## 19. Priorités finales

L'ordre de priorité recommandé est :

1. conserver la transcription brute ;
2. fiabiliser la gestion des fichiers et des erreurs ;
3. ajouter les timestamps ;
4. ajouter le vocabulaire métier ;
5. séparer le nettoyage et la correction sémantique ;
6. détecter les anomalies de cohérence ;
7. ajouter la réécoute et la retranscription ciblée ;
8. valider toute correction avant remplacement ;
9. journaliser les hypothèses et les décisions ;
10. ajouter la validation humaine dans l'interface ;
11. mettre en place l'apprentissage continu du vocabulaire ;
12. améliorer le prétraitement audio ;
13. mettre en place le traitement asynchrone ;
14. ajouter la diarisation ;
15. préparer une éventuelle adaptation du modèle ;
16. synchroniser l'audio et le texte dans l'interface.
