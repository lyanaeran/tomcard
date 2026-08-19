# Space Fight

Deckbuilder roguelike (thème vaisseaux spatiaux) inspiré de Slay the Spire. Actuellement un
**POC de combat** jouable (pas de boucle de run complète).

## Langue

Répondre à l'utilisateur en français, y compris pour les messages de statut/résumés (les
commentaires de code restent en français ASCII comme précisé plus bas ; le code lui-même — noms de
variables, identifiants — reste en français, déjà la convention du projet).

## Documents de référence (à tenir à jour)

- `specs/specs.md` — vision de conception globale du jeu complet (boucle de run, modules, cartes, etc.)
- `specs/poc.md` — spec du POC de combat actuellement implémenté, dérivée de `specs/specs.md`
- `specs/cartes.xlsx` — registre éditable des cartes (une ligne par carte du tableau de conception,
  colonnes Rareté/Module/Catégorie/Cible/Coût/X/Y/Munition/Nom/Description/Jouable/Notes), miroir
  humainement modifiable de `config/cartes.json`. Pas rechargé par le code (`config/cartes.json`
  reste la seule source de vérité pour le moteur) : si l'un est modifié, reporter le changement dans
  l'autre à la main.

**Les deux fichiers `specs.md`/`poc.md` doivent rester synchronisés avec le code.** Quand une décision de design est
prise ou clarifiée en cours d'implémentation (ex. règle de ciblage, format d'une carte, retour
visuel d'un effet), reporte-la dans `specs/poc.md` (détail POC) et, si c'est une décision de design
réutilisable au-delà du POC, dans `specs/specs.md` aussi. Inversement, avant d'implémenter une
fonctionnalité un peu ambiguë, relis la section concernée de ces deux fichiers.

## Deux façons de jouer (PC et web/iOS) — les deux doivent rester fonctionnelles

Le jeu se lance de deux façons distinctes, qui partagent la même logique (`src/gameplay/`) mais ont
chacune leur propre couche d'affichage. Voir `README.md` pour les instructions de lancement
détaillées.

- **PC (pyglet)** : `python main.py`, affichage natif via `src/ui/fenetre.py`. Version de référence,
  la plus fidèle à `specs/poc.md`/`specs/specs.md`.
- **Web (navigateur / iPhone)** : `index.html` + `web/` (`app.js`, `style.css`, `bridge.py`).
  Exécute `src/gameplay/` tel quel dans le navigateur via [Pyodide](https://pyodide.org/) (Python
  compilé en WebAssembly) ; `web/bridge.py` sérialise l'état du combat en JSON pour l'affichage
  HTML/CSS/JS. UI volontairement simplifiée par rapport à pyglet (pas d'infobulle au survol, taille
  des cases pilotée par la hauteur d'écran...) — ces écarts sont documentés dans les commentaires de
  `web/app.js`/`web/style.css`, pas dans `specs/poc.md`/`specs/specs.md` qui décrivent la version de référence.

**Ces deux façons de jouer doivent rester fonctionnelles en permanence.** En particulier :

- Une modification de `src/gameplay/` (nouvelle fonction, signature changée, nouveau champ sur une
  entité...) doit rester compatible avec ce que `web/bridge.py` attend de ce module ; vérifier
  `web/bridge.py` avant de renommer/déplacer quoi que ce soit dans `src/gameplay/`.
- Une modification de `config/*.json` (nouveau champ, format changé) doit rester chargeable par
  `src/gameplay/donnees.py` **et** rester interprétable par `web/bridge.py`/`web/app.js` (qui
  fetchent ces fichiers directement).
- `src/gameplay` reste la seule source de vérité pour les règles de jeu : ne jamais dupliquer une
  règle en JS dans `web/app.js`, qui ne doit que lire/afficher l'état renvoyé par `web/bridge.py`.

## Stack et commandes

- Python 3.11+, [pyglet](https://pyglet.readthedocs.io/) pour l'affichage PC, pytest pour les tests
- Lancer le jeu (PC) : `python main.py` — voir `README.md` pour la version web
- Lancer les tests : `pytest` (config dans `pyproject.toml`, `testpaths = ["tests"]`)
- Dépendances : `pip install -e .` puis `pip install -e ".[dev]"` pour pytest

## Architecture

Séparation stricte, cf. `specs/specs.md` §10 :

- `src/gameplay/` — logique de jeu pure, **zéro dépendance pyglet**, entièrement testable sans
  affichage. Contient le moteur de combat (`combat.py`), le ciblage ennemi (`ciblage.py`), les
  entités (`module.py`, `ennemi.py`, `vaisseau.py`, `flotte.py`, `carte.py`, `joueur.py`,
  `deck.py`), le chargement de `config/` (`donnees.py`) et l'orchestration du tirage aléatoire du
  POC (`config_poc.py`)
- `src/ui/` — tout ce qui dépend de pyglet (fenêtre, dessin, animations). `fenetre.py` est le seul
  gros fichier ; `animation.py` contient les minuteries pures (testables sans pyglet)
- `index.html` + `web/` — version web/iPhone (voir "Deux façons de jouer" ci-dessus). `web/bridge.py`
  importe `src/gameplay/` sans le modifier ; `web/app.js`/`web/style.css` gèrent l'affichage
- `config/*.json` — contenu du jeu déclaratif (modules, ennemis, cartes), référence les images
  d'`assets/`. Chargé par `src/gameplay/donnees.py` (PC) et fetché directement par `web/app.js` (web)
- `assets/{cartes,modules,ennemis}/` — images uniquement pour l'instant
- `tests/` — un fichier de test par module de `src/gameplay/` (et `test_animation.py` pour la
  minuterie de `src/ui/`). Les fonctions de `src/ui/fenetre.py` autres que les minuteries, et tout
  `web/`, ne sont pas couverts par pytest (voir "Tester l'UI" ci-dessous)

## Conventions de code

- Une responsabilité claire par classe
- Commentaires en français, **ASCII uniquement (sans accents ni cédilles)** — cette règle ne
  s'applique qu'au code, pas à `specs/specs.md`/`specs/poc.md`/`CLAUDE.md` qui utilisent l'orthographe normale
- Docstrings courtes, une ligne si possible
- `src/gameplay` ne doit jamais importer `pyglet` ; si une fonction a besoin d'affichage, elle
  appartient à `src/ui`

## Tester l'UI (pyglet)

`src/ui/fenetre.py` n'a pas de tests pytest classiques (dessiner avec pyglet n'est pas unitaire).
Pattern utilisé jusqu'ici pour valider visuellement un changement :

1. Lancer un serveur X virtuel : `Xvfb :99 -screen 0 1280x800x24 &`
2. Écrire un petit script Python qui construit une `FenetreCombat`, appelle
   `fenetre.dispatch_event("on_draw")` puis
   `pyglet.image.get_buffer_manager().get_color_buffer().save("capture.png")`, en simulant les
   clics/survols voulus (`fenetre.on_mouse_press(...)`, `fenetre.on_mouse_motion(...)`, ou en
   appelant directement les méthodes internes comme `_essayer_de_cibler`)
3. Lancer ce script avec `DISPLAY=:99` et le bon `PYTHONPATH`
4. Inspecter le screenshot (Read tool) et, pour vérifier une couleur/position précise,
   échantillonner les pixels avec PIL (`Image.open(...).getpixel((x, y))`) plutôt que de se fier
   seulement à l'œil
5. Utiliser un `random.Random(seed)` fixe passé à `creer_combat_poc()` pour un combat reproductible
6. Nettoyer les scripts/captures temporaires du scratchpad une fois la vérification faite (ne rien
   laisser dans le dépôt)

## Déterminisme du tirage aléatoire

Tout ce qui est tiré au sort (vaisseau, flotte, deck) passe par un `random.Random` explicite
injecté dans `creer_combat_poc(generateur_aleatoire=...)` — jamais le module `random` global
directement — pour que les tests et les captures d'écran restent reproductibles.

## Pièges pyglet connus

- `pyglet.text.Label(...)` **ne supporte pas `bold=True`** dans la version installée (2.1.16) →
  `TypeError`. Ne pas l'utiliser.
- Dans un `Batch` partagé, l'ordre de dessin entre `Sprite` et formes/texte (`shapes.*`,
  `text.Label`) **n'est pas garanti** par l'ordre de création. Utiliser un `pyglet.graphics.Group`
  explicite (voir `GROUPE_SUPERPOSITION` dans `fenetre.py`) pour forcer ce qui doit rester
  au-dessus des sprites (pastilles, popups, infobulles, bandeaux...).

## Git / PR

Créer une PR par changement logique, avec plan de test dans la description. Toute valeur numérique
inventée faute de spec précise (PV, dégâts, coûts...) doit être signalée comme telle dans la PR et
dans `specs/poc.md` (voir l'avertissement en tête de `specs/poc.md`).

**Avant de pousser un commit supplémentaire sur une branche existante, vérifier l'état de sa PR**
(mergée/fermée ou encore ouverte). Pousser sur une branche dont la PR est déjà mergée ou fermée
laisse le commit orphelin, jamais intégré à `main` sans action manuelle supplémentaire — c'est
arrivé plusieurs fois dans ce projet. Si la PR est déjà mergée/fermée, repartir d'une nouvelle
branche depuis `main` (ou rouvrir une PR dédiée) plutôt que de pousser sur l'ancienne branche.
