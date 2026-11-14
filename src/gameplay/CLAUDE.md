# src/gameplay — logique de jeu (partagée PC et web)

Chargé automatiquement quand on travaille dans `src/gameplay/`. Règles générales : `CLAUDE.md`
racine.

## Rôle

Seule source de vérité des règles de jeu, exécutée telle quelle par le PC (`src/ui/`) et par le web
(Pyodide, via `src/web/bridge.py`). **Zéro dépendance pyglet** : si une fonction a besoin d'affichage,
elle appartient à `src/ui`. Couvert par pytest (`tests/`, un fichier de test par module).

## Moteur de la refonte

Les fichiers `*_new.py` (`carte_new`, `module_new`, `ennemi_new`, `statut_new`, `combat_new`,
`deck_new`, `flotte_new`, `vaisseau_new`) sont **le moteur du jeu**, utilisé par le parcours
(`partie.py`, `parcours.py`, `deroulement.py`), le PC, le web et les simulateurs. L'ancien moteur
(`carte.py`, `module.py`, `combat.py`, `donnees.py`...) et ses `config/*.json` sont supprimés
depuis la PR 4 du branchement (2026-11-14) ; le suffixe `_new` reste pour l'instant (renommage à
décider). Le jeu ne se joue que par le parcours (pas de combat de démonstration). Vue d'ensemble :
`specs/refonte.md`, plan : `specs/refonte-branchement.md`.

- Les objets de la partie (cartes, modules) ne sont **jamais modifiés
  par un combat** : `CombatNew` travaille sur des copies (`CarteNew.copie`,
  `ModuleNew.copie_pour_combat`, `EnnemiNew.pour_combat`).
- Les tests ne doivent pas coder en dur une valeur de carte réglable (ex. Bouclier) : la lire dans
  `config/carte_new.json`, l'utilisateur ajuste souvent les valeurs.

## Compatibilité avec le web

- Avant de renommer/déplacer une fonction, une signature ou un champ d'entité, vérifier ce que
  `src/web/bridge.py` utilise.
- Un **nouveau fichier** ici doit être ajouté à `FICHIERS_A_MONTER` dans `src/web/app.js` (sinon le web
  ne charge plus, cf. `src/web/CLAUDE.md`).
- Un changement de format de `config/*.json` doit rester chargeable par les fonctions
  `charger_*_new` ; `src/web/app.js` monte ces fichiers tels quels dans Pyodide.

## Déterminisme du tirage aléatoire

Tout tirage (vaisseau, flotte, deck, parcours, Aventures...) passe par un `random.Random` explicite
injecté (ex. `combat_depuis_partie(partie, aleatoire)`, `CombatNew.aleatoire`) — **jamais le module
`random` global** (`random.choice(...)`, `random.random()`...), et jamais une instance jetable
recréée à chaque appel là où une instance unique doit être conservée d'un bout à l'autre d'un
écran/d'une session. Un écran PC ou `src/web/bridge.py` peut construire son propre `random.Random()`
(non seedé si la reproductibilité n'est pas exigée). Vérifié par `tests/test_architecture.py` sur
tout `src/` et `src/web/`.

## Tests

Un changement ici sans impact visuel/interactif est couvert par `pytest` seul (même code pour les
deux versions). Un changement du comportement visible d'une carte/mécanique doit en plus être
vérifié sur PC et web (cf. `src/ui/CLAUDE.md` et `src/web/CLAUDE.md`).
