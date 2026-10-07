# Reporting IA - premiere tranche Text-to-SQL

## But

Faire fonctionner une premiere tranche utile sur les donnees deja disponibles,
sans attendre l'inventaire complet de la base source ni construire tous les
catalogues. Le comportement actuel de `POST /reporting/query` reste inchange
jusqu'a ce que la generation, la validation et l'execution SQL soient testees.

La cible interrogeable reste `gpr_ai_reporting`, jamais la base operationnelle
`gpr_sicma_online`.

## Perimetre initial

Utiliser uniquement la projection existante `reporting_claim`. Ne pas ajouter
de tables ou modifier la synchronisation tant qu'une question concrete ne
l'exige pas. Verifier les types effectivement presents parmi `CLAIM`,
`DENUNCIACION` et `SUGGESTION`; signaler toute absence, sans supposer que le
type manque ou lancer une migration preventivement.

Premieres capacites :

- mesure : nombre de dossiers ;
- dimensions : type de dossier, statut, agence, canal et categorie ;
- filtre de periode, uniquement si la question en contient une ; date de
  reception par defaut, fuseau `Africa/Porto-Novo`, bornes inclusives ;
- sans periode demandee, aucun filtre temporel ;
- clarification si la demande ne peut pas etre comprise sans une decision
  metier.

Les ratios, comparaisons, delais, SLA, scores, contenu textuel et autres
dimensions sont reportes jusqu'a une question qui les necessite.

Le LLM ne recoit que la description des champs utiles. Les identifiants,
donnees client, contenu et solution ne sont pas transmis au modele ni retournes
dans le resultat. Aucun filtre d'acces propre a un utilisateur n'est requis :
l'application est mono-institution.

## Contrats minimaux

Les schemas Pydantic sont dans
[`app/reporting/text_to_sql_contracts.py`](../gpr_ai_service/app/reporting/text_to_sql_contracts.py).
Ils servent a valider les sorties, mais ne sont pas encore connectes a la route
ou a un moteur d'execution.

### Intention

La sortie d'interpretation contient la version, un statut (`ready`,
`needs_clarification` ou `unsupported`), l'objet et son type, la mesure, les
dimensions, filtres simples, la periode eventuelle et les informations de
clarification/limite. Seul `ready` peut aller vers la generation SQL.

Les operations et filtres implementes pour cette tranche restent limites au
comptage et aux egalites/inclusions necessaires aux dimensions ci-dessus. Les
concepts doivent correspondre au catalogue autorise cote backend ; le LLM ne
choisit jamais de table ou colonne.

### SQL candidat

Le candidat contient le SQL, des parametres typés avec leurs sources
d'intention, les champs utilises et les colonnes resultat attendues. Les
valeurs restent separees du SQL et sont injectees par FastAPI comme parametres
lies. Le modele ne peut ni executer sa requete ni accorder ses propres droits.

Un candidat n'est pas execute avant mise en place du controle AST, de la liste
de tables/colonnes autorisees, d'un compte SQL en lecture seule et de limites
de ressources. La validation de forme Pydantic ne constitue pas un validateur
de securite SQL.

La reponse conserve `ReportingQueryResponse`, consomme par React. Les chiffres
et graphiques sont construits par le backend a partir des lignes SQL, jamais
inventes par le LLM.

## Ordre de travail

1. Verifier en base la presence des types de dossiers et dimensions existants
   utiles aux questions de depart.
2. Tester les contrats minimaux d'intention et de SQL candidat.
3. Implementer et tester le validateur SQL en lecture seule avant toute
   execution d'une requete generee.
4. Brancher une premiere question simple sur `POST /reporting/query` en
   conservant le contrat React.

On ne touche pas au dashboard fixe, a la synchronisation, ni aux autres
endpoints pour cette tranche. Les decisions metier sont demandees uniquement
quand elles bloquent une mesure ou peuvent changer son resultat.

## Reporte

Inventaire exhaustif des tables source, projection de nouvelles tables,
catalogue de requetes approuvees et interface de revue, conservation des
candidats, protection configurable des petits agregats, tool calling,
comparaisons, ratios, SLA, recherche dans le texte et refonte du dashboard.
Ces travaux seront reouverts lorsqu'un besoin concret les justifiera.
