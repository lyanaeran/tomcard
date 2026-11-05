# src/gameplay — logique de jeu (partagée PC et web)

Chargé automatiquement quand on travaille dans `src/gameplay/`. Règles générales : `CLAUDE.md`
racine.

## Rôle

Seule source de vérité des règles de jeu, exécutée telle quelle par le PC (`src/ui/`) et par le web
(Pyodide, via `web/bridge.py`). **Zéro dépendance pyglet** : si une fonction a besoin d'affichage,
elle appartient à `src/ui`. Couvert par pytest (`tests/`, un fichier de test par module).

## Compatibilité avec le web

- Avant de renommer/déplacer une fonction, une signature ou un champ d'entité, vérifier ce que
  `web/bridge.py` utilise.
- Un **nouveau fichier** ici doit être ajouté à `FICHIERS_A_MONTER` dans `web/app.js` (sinon le web
  ne charge plus, cf. `web/CLAUDE.md`).
- Un changement de format de `config/*.json` doit rester chargeable par `donnees.py` **et**
  interprétable par `web/bridge.py`/`web/app.js`, qui fetchent ces fichiers directement.

## Déterminisme du tirage aléatoire

Tout tirage (vaisseau, flotte, deck, parcours, Aventures...) passe par un `random.Random` explicite
injecté (ex. `creer_combat_poc(generateur_aleatoire=...)`, `Combat.aleatoire`) — **jamais le module
`random` global** (`random.choice(...)`, `random.random()`...), et jamais une instance jetable
recréée à chaque appel là où une instance unique doit être conservée d'un bout à l'autre d'un
écran/d'une session. Un écran PC ou `web/bridge.py` peut construire son propre `random.Random()`
(non seedé si la reproductibilité n'est pas exigée). Vérifié par `tests/test_architecture.py` sur
tout `src/` et `web/`.

## Tests

Un changement ici sans impact visuel/interactif est couvert par `pytest` seul (même code pour les
deux versions). Un changement du comportement visible d'une carte/mécanique doit en plus être
vérifié sur PC et web (cf. `src/ui/CLAUDE.md` et `web/CLAUDE.md`).
