# Space Fight

Deckbuilder roguelike (thème vaisseaux spatiaux) inspiré de Slay the Spire. Actuellement un
**POC de combat** jouable (pas de boucle de run complète).

## Documents de référence (à tenir à jour)

- `specs.md` — vision de conception globale du jeu complet (boucle de run, modules, cartes, etc.)
- `poc.md` — spec du POC de combat actuellement implémenté, dérivée de `specs.md`

**Ces deux fichiers doivent rester synchronisés avec le code.** Quand une décision de design est
prise ou clarifiée en cours d'implémentation (ex. règle de ciblage, format d'une carte, retour
visuel d'un effet), reporte-la dans `poc.md` (détail POC) et, si c'est une décision de design
réutilisable au-delà du POC, dans `specs.md` aussi. Inversement, avant d'implémenter une
fonctionnalité un peu ambiguë, relis la section concernée de ces deux fichiers.

## Stack et commandes

- Python 3.11+, [pyglet](https://pyglet.readthedocs.io/) pour l'affichage, pytest pour les tests
- Lancer le jeu : `python main.py`
- Lancer les tests : `pytest` (config dans `pyproject.toml`, `testpaths = ["tests"]`)
- Dépendances : `pip install -e .` puis `pip install -e ".[dev]"` pour pytest

## Architecture

Séparation stricte, cf. `specs.md` §10 :

- `src/gameplay/` — logique de jeu pure, **zéro dépendance pyglet**, entièrement testable sans
  affichage. Contient le moteur de combat (`combat.py`), le ciblage ennemi (`ciblage.py`), les
  entités (`module.py`, `ennemi.py`, `vaisseau.py`, `flotte.py`, `carte.py`, `joueur.py`,
  `deck.py`), le chargement de `config/` (`donnees.py`) et l'orchestration du tirage aléatoire du
  POC (`config_poc.py`)
- `src/ui/` — tout ce qui dépend de pyglet (fenêtre, dessin, animations). `fenetre.py` est le seul
  gros fichier ; `animation.py` contient les minuteries pures (testables sans pyglet)
- `config/*.json` — contenu du jeu déclaratif (modules, ennemis, cartes), référence les images
  d'`assets/`. Chargé par `src/gameplay/donnees.py`
- `assets/{cartes,modules,ennemis}/` — images uniquement pour l'instant
- `tests/` — un fichier de test par module de `src/gameplay/` (et `test_animation.py` pour la
  minuterie de `src/ui/`). Les fonctions de `src/ui/fenetre.py` autres que les minuteries ne sont
  pas couvertes par pytest (voir "Tester l'UI" ci-dessous)

## Conventions de code

- Une responsabilité claire par classe
- Commentaires en français, **ASCII uniquement (sans accents ni cédilles)** — cette règle ne
  s'applique qu'au code, pas à `specs.md`/`poc.md`/`CLAUDE.md` qui utilisent l'orthographe normale
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

Historique de travail sur deux branches : `spec-jeu` (évolutions de `specs.md`/`poc.md` seules) et
`poc` (code du POC). Créer une PR par changement logique, avec plan de test dans la description.
Toute valeur numérique inventée faute de spec précise (PV, dégâts, coûts...) doit être signalée
comme telle dans la PR et dans `poc.md` (voir l'avertissement en tête de `poc.md`).
