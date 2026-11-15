# src/gameplay — logique de jeu (partagée PC et web)

Chargé automatiquement quand on travaille dans `src/gameplay/`. Règles générales : `CLAUDE.md`
racine.

## Rôle

Seule source de vérité des règles de jeu, exécutée telle quelle par le PC (`src/ui/`) et par le web
(Pyodide, via `src/web/bridge.py`). **Zéro dépendance pyglet** : si une fonction a besoin d'affichage,
elle appartient à `src/ui`. Couvert par pytest (`tests/`, un fichier de test par module).

## Moteur de la refonte

`carte.py`, `module.py`, `ennemi.py`, `statut.py`, `combat.py`, `deck.py`, `flotte.py` et
`vaisseau.py` sont **le moteur du jeu** (issu de la refonte), utilisé par le parcours (`partie.py`,
`parcours.py`, `deroulement.py`), le PC, le web et les simulateurs. L'ancien moteur est supprimé
(PR 4 du branchement, 2026-11-14) et les fichiers de la refonte ont perdu leur suffixe `_new` le
même jour (`CarteNew` → `Carte`, `carte_new.py` → `carte.py`, `config/carte_new.json` →
`config/cartes.json`…) : un nom en `_new` dans un vieux document désigne le fichier actuel. Le jeu
ne se joue que par le parcours (pas de combat de démonstration). Vue d'ensemble :
`specs/refonte.md`, historique du branchement : `specs/refonte-branchement.md`.

- Les objets de la partie (cartes, modules) ne sont **jamais modifiés
  par un combat** : `Combat` travaille sur des copies (`Carte.copie`,
  `Module.copie_pour_combat`, `Ennemi.pour_combat`).
- Les tests ne doivent pas coder en dur une valeur de carte réglable (ex. Bouclier) : la lire dans
  `config/cartes.json`, l'utilisateur ajuste souvent les valeurs.

## Compatibilité avec le web

- Avant de renommer/déplacer une fonction, une signature ou un champ d'entité, vérifier ce que
  `src/web/bridge.py` utilise.
- Un **nouveau fichier** ici doit être ajouté à `FICHIERS_A_MONTER` dans `src/web/app.js` (sinon le web
  ne charge plus, cf. `src/web/CLAUDE.md`).
- Un changement de format de `config/*.json` doit rester chargeable par les fonctions
  `charger_cartes`, `charger_modules`, `charger_ennemis` ; `src/web/app.js` monte ces fichiers tels quels dans Pyodide.

## Déterminisme du tirage aléatoire

Tout tirage (vaisseau, flotte, deck, parcours, Aventures...) passe par un `random.Random` explicite
injecté (ex. `combat_depuis_partie(partie, aleatoire)`, `Combat.aleatoire`) — **jamais le module
`random` global** (`random.choice(...)`, `random.random()`...), et jamais une instance jetable
recréée à chaque appel là où une instance unique doit être conservée d'un bout à l'autre d'un
écran/d'une session. Un écran PC ou `src/web/bridge.py` peut construire son propre `random.Random()`
(non seedé si la reproductibilité n'est pas exigée). Vérifié par `tests/test_architecture.py` sur
tout `src/` et `src/web/`.

## Tests

Un changement ici sans impact visuel/interactif est couvert par `pytest` seul (même code pour les
deux versions). Un changement du comportement visible d'une carte/mécanique doit en plus être
vérifié sur PC et web (cf. `src/ui/CLAUDE.md` et `src/web/CLAUDE.md`).
