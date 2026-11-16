# Space Fight

Deckbuilder roguelike (thème vaisseaux spatiaux) inspiré de Slay the Spire. Le combat est jouable
et le **parcours** (boucle de run) s'enchaîne écran par écran jusqu'au Boss du niveau 10
(specs.md §2.4), sur les deux versions : `main.py` côté PC, `src/web/app.js` côté web.

**Le jeu tourne sur le moteur issu de la refonte** (cartes, modules, ennemis, statuts, combat),
branché en 4 PR (`specs/refonte-branchement.md`). L'ancien moteur est supprimé et les fichiers de
la refonte ont perdu leur suffixe `_new` (2026-11-14) : `carte_new.py` → `carte.py`, `CarteNew` →
`Carte`, `config/carte_new.json` → `config/cartes.json`… Un nom en `_new` dans un vieux document
(`refonte-branchement.md`, synthèses de simulation) désigne le fichier actuel.
**Lire `specs/refonte.md` en premier** : état des lieux, où est quoi, ce qui reste à faire.

## Langue

Répondre à l'utilisateur en français, y compris pour les messages de statut/résumés. Le code
(identifiants, commentaires) est en français ; commentaires en **ASCII uniquement (sans accents ni
cédilles)**. `specs/` et les `CLAUDE.md` utilisent l'orthographe normale. Les **textes affichés
dans le jeu** (noms et descriptions des cartes dans `config/`) gardent leurs accents (consigne
utilisateur) ; tout le reste (identifiants, clés JSON, code, commentaires) reste sans accent.

## Travailler avec l'utilisateur

L'utilisateur conçoit le jeu ; l'agent propose, documente et code. Préférences constatées :

- **Spécifier avant de coder.** Une nouvelle mécanique se discute d'abord (propositions, questions
  numérotées), puis la décision est notée dans `specs/` (« décision utilisateur », avec la date),
  puis seulement codée quand l'utilisateur le demande. Quand il dit « ne code rien » ou pose une
  question, répondre et proposer, sans modifier le code.
- **Signaler ce qu'on invente** : une valeur ou une règle choisie faute de spec est marquée
  « proposition » ou « valeur inventée » dans `specs/` et dans la PR, et soumise à l'utilisateur.
- **Ne jamais lancer une campagne de simulation sans son accord** (c'est long) : proposer le volume
  et la durée, attendre le feu vert. Un essai qu'il a lui-même demandé et dimensionné est autorisé
  tel quel.
- **Réponses courtes et concrètes, en français**, avec des exemples chiffrés plutôt que du jargon ;
  dire clairement ce qui a été testé et ce qui ne l'a pas été.
- **Cartes modifiées dans l'outil d'administration** (éditeur de cartes web / iPhone,
  `specs/outil-editeur-cartes.md`) : l'utilisateur colle **seulement les cartes modifiées ou
  ajoutées**, copiées par l'outil (`{"cartes": [...]}`). Les **fusionner par id** dans
  `config/cartes.json` (une carte existante est remplacée, une nouvelle ajoutée à la fin, les
  autres cartes ne bougent pas), puis **écrire ou corriger les effets** des cartes nouvelles ou
  dont la description ou les valeurs ont changé (l'outil ne les saisit pas : ils se déduisent de
  la description ; un effet d'un genre nouveau demande du code : tant qu'il n'est pas codé, la
  carte reste `"jouable": "non"` et l'effet est décrit dans `specs/effets-a-coder.md`), régénérer `config/cartes.md`
  (`python -m outils.tableau_cartes`), lancer `pytest`, et résumer ce qui a changé carte par
  carte avant la PR.
- **Revues de PR** : un bot (Claude Code) commente les PR. À la demande de l'utilisateur, lire les
  commentaires (`~/.local/bin/gh api repos/{owner}/{repo}/pulls/<n>/comments`), corriger ce qui
  est juste (avec un test), et répondre sous chaque commentaire (corrigé dans tel commit, ou
  pourquoi on ne change pas).

## Documents de référence (à tenir à jour)

- `specs/` — document de conception, **seule source de vérité pour le design**, découpé par thème.
  **Lire d'abord `specs/specs.md`** (index court : quelle section dans quel fichier, quel fichier
  lire selon la tâche), puis seulement le fichier utile ; pour la refonte, `specs/refonte.md`. Les références « specs.md §X.Y » du code se
  résolvent avec cet index (numérotation commune à tous les fichiers).
- **Tous les documents de conception `.md` vont dans `specs/`** (consigne utilisateur), y compris
  les brouillons de refonte et la conception d'outils (ex. `specs/simulation.md` pour
  `outils/simulation/`), et sont listés dans l'index `specs/specs.md`. Seules exceptions : les
  `CLAUDE.md`, `README.md`, et les fichiers générés (ex. synthèses de simulation,
  `config/cartes.md`, `config/modules.md`, `config/ennemis.md`).
- **Données de la refonte (décision utilisateur)** :
  - `config/cartes.json` est la **source de vérité des cartes** : format de la refonte
    (`src/gameplay/carte.py:Carte`), valeurs nommées, effets, `modules` (la carte dit à quels
    modules elle appartient), `jouable` (`"oui"`, `"non"`, `"supprimee"`) et `refonte`.
    C'est là qu'on modifie une carte, puis on régénère `config/cartes.md` (tableau lisible,
    **toujours généré**, jamais modifié à la main) avec `python -m outils.tableau_cartes` ;
    `tests/test_tableau_cartes.py` échoue tant que le tableau n'est pas à jour.
  - **Modules, même principe** : `config/modules.json` (`src/gameplay/module.py:Module`)
    est la source de vérité des modules de la refonte (pour l'instant les deux modules jouables),
    avec son tableau **généré** `config/modules.md` (`python -m outils.tableau_modules`,
    `tests/test_tableau_modules.py`).
  - **Ennemis, même principe** : `config/ennemis.json` (`src/gameplay/ennemi.py:Ennemi`)
    est la source de vérité des ennemis de la refonte, avec son tableau **généré**
    `config/ennemis.md` (`python -m outils.tableau_ennemis`, `tests/test_tableau_ennemis.py`).
  - `specs/archive-cartes-modules.md` : **toutes les cartes et tous les modules de l'ancien
    moteur** (dernière version des anciens JSON, en tableaux), gardés comme réserve d'idées
    (décision utilisateur, 2026-11-15) ; archive, ne décrit pas le jeu actuel.
  - `specs/cartes_legacy.xlsx` : ancien registre (onglets Cartes, Aventures, Ennemis, Modules),
    **archivé, plus maintenu**.

**`specs/` doit rester synchronisé avec le code.** Une décision de design prise ou clarifiée en
cours d'implémentation (règle de ciblage, format d'une carte, retour visuel, mécanique du parcours)
est reportée dans le fichier de spec concerné. Avant d'implémenter une fonctionnalité ambiguë,
relire la section concernée.

## CLAUDE.md par dossier

Les détails propres à chaque partie sont dans des `CLAUDE.md` chargés quand on travaille dans le
dossier : `src/gameplay/CLAUDE.md` (compatibilité web, déterminisme du tirage aléatoire),
`src/ui/CLAUDE.md` (pièges pyglet, méthode de test PC par capture), `src/web/CLAUDE.md` (Pyodide,
cache-busting, méthode de test web), `outils/simulation/CLAUDE.md` (lancer les simulations, les
deux simulateurs, les synthèses). **Les lire avant de toucher ces dossiers ou de tester.**

## Deux façons de jouer (PC et web/iOS) — les deux doivent rester fonctionnelles

Même logique (`src/gameplay/`), deux couches d'affichage (lancement : `README.md`). « PC » et
« web » désignent la **version**, pas la machine :

- **PC (pyglet)** : application de bureau, `python main.py`, affichage `src/ui/` — tourne sur
  Windows comme sur macOS. Version de référence, la plus fidèle à `specs/`.
- **Web (navigateur / iPhone)** : `index.html` + `src/web/`, exécute `src/gameplay/` via Pyodide.

Règles :

- `src/gameplay` est la seule source de vérité des règles : ne jamais dupliquer une règle en JS.
- **Le flux d'interaction (nombre de clics/taps pour jouer une carte) reste identique entre PC et
  web**, même pour les cartes « sans clic de ciblage » : sélectionner la carte puis confirmer par un
  clic/tap sur une case vivante du bon camp, jamais de résolution automatique (specs.md §8.3). Toute
  divergence entre `src/ui/fenetre.py` (`_essayer_de_cibler`) et `src/web/app.js` (`cliquerCase`) est
  un bug.
- **Tout changement est testé avant d'être considéré terminé**, pas seulement relu :
  - changement interne à `src/gameplay/` ou `config/*.json` sans impact visible → `pytest` suffit
    (même code pour les deux versions) ;
  - changement de `src/ui/`, `src/web/` ou du comportement visible d'une carte/mécanique → vérification
    sur **PC et web** avec les méthodes de `src/ui/CLAUDE.md` et `src/web/CLAUDE.md`.

## Stack et commandes

- Python 3.11+ (3.13 sur macOS : 3.14 fait planter pyglet), pyglet pour le PC, pytest
- Lancer le jeu (PC) : `python main.py` — web : voir `README.md`
- Tests : `pytest` (config dans `pyproject.toml`)
- Dépendances : `pip install -e .` puis `pip install -e ".[dev]"`

## Architecture

Séparation stricte (specs.md §10) :

- `src/gameplay/` — logique de jeu pure, sans pyglet, entièrement testable
- `src/ui/` — tout ce qui dépend de pyglet ; `main.py` ouvre et ferme les fenêtres
- **L'enchaînement des écrans du parcours (quel écran vient ensuite, règles de chaque transition)
  vit dans `src/gameplay/deroulement.py`, jamais dans `main.py`, `src/ui/` ou `src/web/`** (consigne
  utilisateur) : PC (`main.py:_aller_a`), web (`src/web/app.js:allerA`) et simulation ne font
  qu'afficher ou suivre l'`Ecran` qu'il renvoie
- `outils/simulation/` — simulateurs d'équilibrage (conception : `specs/simulation.md`), qui jouent
  des combats et des parties sans affichage en appelant `src/gameplay` : un pour les parties
  complètes, un pour les combats isolés
- `outils/tableau_*.py` — génèrent les tableaux lisibles `config/*.md` à partir des JSON
- `outils/test_web/essais.js` — essais de la version web dans Chromium (cf. `src/web/CLAUDE.md`) ;
  `.github/workflows/tests.yml` lance `pytest` et la syntaxe du web à chaque PR
- `index.html` (à la racine : c'est l'adresse servie par GitHub Pages) + `src/web/` — version web
  (dossier déplacé de `web/` vers `src/web/` le 2026-11-14, décision utilisateur) ;
  `src/web/bridge.py` importe `src/gameplay/` sans le modifier
- `config/*.json` — contenu déclaratif (modules, ennemis, cartes), chargé par
  `charger_cartes`, `charger_modules`, `charger_ennemis` ; `src/web/app.js` les monte
  dans Pyodide pour que le même code les lise
- `assets/` — images ; `tests/` — un fichier de test par module de `src/gameplay/`,
  plus `test_animation.py`, `test_architecture.py`, les tests des tableaux générés et des
  simulateurs

**`src/ui` et `src/web/` ne possèdent jamais de règle de jeu ni d'état de session** (uniquement la
présentation d'un état décidé par `src/gameplay`) — précédents : le journal de combat
(`Combat.journal`) et la résolution des Aventures Astéroïdes/Police vivent dans `src/gameplay`.
Avant de considérer terminée une tâche qui ajoute du code à `src/ui` ou `src/web/`, vérifier qu'il n'y
a : aucun tirage aléatoire non injecté, aucune machine à états qui décide d'une branche métier (ex.
« une carte est-elle offerte ? »), aucune ressource à usage limité suivie localement, aucune
condition métier (ex. seuil d'Argent) re-vérifiée en plus de la valeur de retour d'une fonction
gameplay. `tests/test_architecture.py` en vérifie une partie ; le reste est une vérification
manuelle systématique.

## Conventions de code

- Une responsabilité claire par classe ; docstrings courtes, une ligne si possible
- Commentaires en français ASCII (cf. Langue)

## Git / PR

**Une seule branche de travail : `devjeux`**, avec une PR `devjeux` → `main` par changement
logique, plan de test dans la description. Ne pas créer de branche par tâche (ça a produit beaucoup
de branches mortes dans ce projet). Toute valeur numérique inventée faute de spec (PV, dégâts,
coûts...) est signalée comme telle dans la PR et dans `specs/`.

**Avant de pousser sur `devjeux`, vérifier l'état de sa PR.** Si elle est déjà mergée/fermée,
remettre `devjeux` à jour depuis `main` d'abord
(`git fetch origin main && git checkout -B devjeux origin/main && git push -f origin devjeux`),
sinon le commit reste orphelin.

**Ouvrir la PR `devjeux` → `main` systématiquement après chaque push**, sans attendre qu'on la
demande (préférence confirmée par l'utilisateur) : nouvelle PR si la précédente est mergée/fermée,
sinon mise à jour de la description de celle qui est ouverte. Sur le Mac de l'utilisateur, `gh` est
installé dans `~/.local/bin/gh` (pas dans le `PATH`) et authentifié.

Messages de commit en français sans accents (comme le code), titre court puis détail si besoin.
