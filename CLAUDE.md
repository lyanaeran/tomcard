# Space Fight

Deckbuilder roguelike (thème vaisseaux spatiaux) inspiré de Slay the Spire. Le combat est jouable
et le **parcours** (boucle de run) s'enchaîne écran par écran jusqu'au Boss du niveau 10
(specs.md §2.4), sur les deux versions : `main.py` côté PC, `web/app.js` côté web.

## Langue

Répondre à l'utilisateur en français, y compris pour les messages de statut/résumés. Le code
(identifiants, commentaires) est en français ; commentaires en **ASCII uniquement (sans accents ni
cédilles)**. `specs/` et les `CLAUDE.md` utilisent l'orthographe normale.

## Documents de référence (à tenir à jour)

- `specs/` — document de conception, **seule source de vérité pour le design**, découpé par thème.
  **Lire d'abord `specs/specs.md`** (index court : quelle section dans quel fichier, quel fichier
  lire selon la tâche), puis seulement le fichier utile. Les références « specs.md §X.Y » du code se
  résolvent avec cet index (numérotation commune à tous les fichiers).
- **Tous les documents de conception `.md` vont dans `specs/`** (consigne utilisateur), y compris
  les brouillons de refonte et la conception d'outils (ex. `specs/simulation.md` pour
  `outils/simulation/`), et sont listés dans l'index `specs/specs.md`. Seules exceptions : les
  `CLAUDE.md`, `README.md`, et les rapports générés (ex. synthèses de simulation).
- `specs/cartes.xlsx` — miroir éditable de `config/cartes.json` (une ligne par carte). Pas rechargé
  par le code (`config/cartes.json` reste la seule source de vérité du moteur) : si l'un est modifié,
  reporter le changement dans l'autre à la main.

**`specs/` doit rester synchronisé avec le code.** Une décision de design prise ou clarifiée en
cours d'implémentation (règle de ciblage, format d'une carte, retour visuel, mécanique du parcours)
est reportée dans le fichier de spec concerné. Avant d'implémenter une fonctionnalité ambiguë,
relire la section concernée.

## CLAUDE.md par dossier

Les détails propres à chaque partie sont dans des `CLAUDE.md` chargés quand on travaille dans le
dossier : `src/gameplay/CLAUDE.md` (compatibilité web, déterminisme du tirage aléatoire),
`src/ui/CLAUDE.md` (pièges pyglet, méthode de test PC par capture), `web/CLAUDE.md` (Pyodide,
cache-busting, méthode de test web). **Les lire avant de toucher ces dossiers ou de tester.**

## Deux façons de jouer (PC et web/iOS) — les deux doivent rester fonctionnelles

Même logique (`src/gameplay/`), deux couches d'affichage (lancement : `README.md`). « PC » et
« web » désignent la **version**, pas la machine :

- **PC (pyglet)** : application de bureau, `python main.py`, affichage `src/ui/` — tourne sur
  Windows comme sur macOS. Version de référence, la plus fidèle à `specs/`.
- **Web (navigateur / iPhone)** : `index.html` + `web/`, exécute `src/gameplay/` via Pyodide.

Règles :

- `src/gameplay` est la seule source de vérité des règles : ne jamais dupliquer une règle en JS.
- **Le flux d'interaction (nombre de clics/taps pour jouer une carte) reste identique entre PC et
  web**, même pour les cartes « sans clic de ciblage » : sélectionner la carte puis confirmer par un
  clic/tap sur une case vivante du bon camp, jamais de résolution automatique (specs.md §8.3). Toute
  divergence entre `src/ui/fenetre.py` (`_essayer_de_cibler`) et `web/app.js` (`cliquerCase`) est
  un bug.
- **Tout changement est testé avant d'être considéré terminé**, pas seulement relu :
  - changement interne à `src/gameplay/` ou `config/*.json` sans impact visible → `pytest` suffit
    (même code pour les deux versions) ;
  - changement de `src/ui/`, `web/` ou du comportement visible d'une carte/mécanique → vérification
    sur **PC et web** avec les méthodes de `src/ui/CLAUDE.md` et `web/CLAUDE.md`.

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
  vit dans `src/gameplay/deroulement.py`, jamais dans `main.py`, `src/ui/` ou `web/`** (consigne
  utilisateur) : PC (`main.py:_aller_a`), web (`web/app.js:allerA`) et simulation ne font
  qu'afficher ou suivre l'`Ecran` qu'il renvoie
- `outils/simulation/` — simulateur d'équilibrage (conception : `specs/simulation.md`), qui joue
  des combats et des parties sans affichage en appelant `src/gameplay`
- `index.html` + `web/` — version web ; `web/bridge.py` importe `src/gameplay/` sans le modifier
- `config/*.json` — contenu déclaratif (modules, ennemis, cartes), chargé par
  `src/gameplay/donnees.py` (PC) et fetché directement par `web/app.js` (web)
- `assets/` — images ; `tests/` — un fichier de test par module de `src/gameplay/`, plus
  `test_animation.py` et `test_architecture.py`

**`src/ui` et `web/` ne possèdent jamais de règle de jeu ni d'état de session** (uniquement la
présentation d'un état décidé par `src/gameplay`) — précédents : le journal de combat
(`Combat.journal`) et la résolution des Aventures Astéroïdes/Police vivent dans `src/gameplay`.
Avant de considérer terminée une tâche qui ajoute du code à `src/ui` ou `web/`, vérifier qu'il n'y
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
