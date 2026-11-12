# src/gameplay — logique de jeu (partagée PC et web)

Chargé automatiquement quand on travaille dans `src/gameplay/`. Règles générales : `CLAUDE.md`
racine.

## Rôle

Seule source de vérité des règles de jeu, exécutée telle quelle par le PC (`src/ui/`) et par le web
(Pyodide, via `web/bridge.py`). **Zéro dépendance pyglet** : si une fonction a besoin d'affichage,
elle appartient à `src/ui`. Couvert par pytest (`tests/`, un fichier de test par module).

## Deux moteurs (refonte en cours)

Les fichiers `*_new.py` (`carte_new`, `module_new`, `ennemi_new`, `statut_new`, `combat_new`,
`deck_new`, `flotte_new`, `vaisseau_new`) sont le **moteur de la refonte**. Depuis la PR 1 du
branchement, le parcours (`partie.py`, `parcours.py`, `deroulement.py`) l'utilise ; l'ancien moteur
(`carte.py`, `module.py`, `ennemi.py`, `combat.py`...) n'est plus lu que par l'affichage PC et web
(en attente des PR 2 et 3) et le combat de démonstration (`config_poc.py`), puis sera supprimé
(PR 4). Vue d'ensemble : `specs/refonte.md`, plan : `specs/refonte-branchement.md`.

- Ne pas mélanger les deux : un fichier `_new` n'importe pas l'ancien moteur, sauf réutilisation
  explicite d'un élément neutre (`position.py`, `RareteCarte`).
- Dans le moteur de la refonte, les objets de la partie (cartes, modules) ne sont **jamais modifiés
  par un combat** : `CombatNew` travaille sur des copies (`CarteNew.copie`,
  `ModuleNew.copie_pour_combat`, `EnnemiNew.pour_combat`).
- Les tests ne doivent pas coder en dur une valeur de carte réglable (ex. Bouclier) : la lire dans
  `config/carte_new.json`, l'utilisateur ajuste souvent les valeurs.

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
