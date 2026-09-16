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

### Vocabulaire initial

```text
KRI
DMR
SICMA
FinGovTool
risque opérationnel
risque de liquidité
contrôle interne
cartographie des risques
plan d'action
audit
réclamation
dénonciation
```

### Actions

- centraliser le vocabulaire dans une configuration dédiée ;
- permettre sa mise à jour sans modifier le code principal ;
- transmettre le vocabulaire au service Speech-to-Text lorsque l'API le permet ;
- appliquer des corrections lexicales contrôlées après transcription ;
- gérer les acronymes, noms propres et variantes courantes ;
- journaliser les corrections automatiques appliquées.

### Règle de sécurité

Les remplacements doivent être suffisamment précis pour ne pas modifier le sens d'une phrase ou transformer un mot courant en terme métier à tort.

## 9. Phase 6 — Ajouter une correction IA contrôlée

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

## 10. Phase 7 — Structurer le résultat

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

## 11. Phase 8 — Ajouter la diarisation

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

La diarisation doit être implémentée après les segments et les timestamps, car elle dépend de la timeline audio.

## 12. Phase 9 — Adapter le stockage côté backend

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

## 13. Phase 10 — Adapter l'interface utilisateur

L'interface pourra proposer :

- l'affichage de la transcription corrigée par défaut ;
- l'affichage optionnel de la transcription brute ;
- des timestamps cliquables ;
- la lecture audio synchronisée avec le texte ;
- l'affichage des locuteurs lorsqu'ils sont disponibles ;
- un indicateur de progression ;
- un message explicite en cas d'échec ;
- la possibilité de signaler une correction incorrecte.

## 14. Phase 11 — Mettre en place l'apprentissage continu contrôlé

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

## 15. Phase 12 — Superviser et mesurer l'apprentissage

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

## 16. Ordre de mise en œuvre recommandé

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
4. correction IA contrôlée ;
5. tests de non-invention et de conservation du sens.

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

## 17. Tests et critères d'acceptation

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

## 18. Priorités finales

L'ordre de priorité recommandé est :

1. conserver la transcription brute ;
2. fiabiliser la gestion des fichiers et des erreurs ;
3. ajouter les timestamps ;
4. ajouter le vocabulaire métier ;
5. ajouter la correction IA contrôlée ;
6. ajouter la validation humaine ;
7. mettre en place l'apprentissage continu du vocabulaire ;
8. améliorer le prétraitement audio ;
9. mettre en place le traitement asynchrone ;
10. ajouter la diarisation ;
11. préparer une éventuelle adaptation du modèle ;
12. synchroniser l'audio et le texte dans l'interface.
