# src/ui — affichage PC (pyglet)

Chargé automatiquement quand on travaille dans `src/ui/`. Règles générales : `CLAUDE.md` racine.

## Rôle

Tout ce qui dépend de pyglet : un écran = une fenêtre (`fenetre.py` pour le combat, `ecran_*.py`
pour le parcours), enchaînés par `main.py`. `animation.py` contient les minuteries pures (testables
sans pyglet, `tests/test_animation.py`). Aucune règle de jeu ni état de session ici (cf. racine).

Le web (`web/app.js`) affiche les mêmes écrans : un changement de flux d'interaction ici doit être
reporté côté web (`_essayer_de_cibler` ↔ `cliquerCase`, cf. specs.md §8.3).

## Pièges pyglet connus

- `pyglet.text.Label(...)` **ne supporte pas `bold=True`** dans la version installée → `TypeError`.
  Ne pas l'utiliser.
- Dans un `Batch` partagé, l'ordre de dessin entre `Sprite` et formes/texte (`shapes.*`,
  `text.Label`) **n'est pas garanti** par l'ordre de création. Utiliser un
  `pyglet.graphics.Group` explicite (voir `GROUPE_SUPERPOSITION` dans `fenetre.py`) pour forcer ce
  qui doit rester au-dessus des sprites (pastilles, popups, infobulles, bandeaux...).
- **Écrans HiDPI (Retina)** : `main.py` règle `pyglet.options.dpi_scaling = "stretch"` avant toute
  fenêtre ; tout le dessin et les clics restent en coordonnées logiques 1280x800. Un script de test
  qui crée une fenêtre sans passer par `main.py` doit faire le même réglage, sinon le dessin
  n'occupe que le quart de la fenêtre.
- macOS : Python 3.14 fait planter pyglet (segfault) ; le `.venv` utilise Python 3.13.

## Tester un changement visible (obligatoire avant de le considérer terminé)

Pas de tests pytest pour le dessin. Vérifier par capture d'écran :

1. Écrire un petit script (dans le scratchpad, jamais dans le dépôt) qui construit l'écran voulu,
   avec un `random.Random(seed)` fixe passé à `creer_combat_poc()` pour un combat reproductible.
2. **macOS** : la fenêtre n'est dessinée qu'une fois la boucle lancée → programmer la capture avec
   `pyglet.clock.schedule_once(capture, 1.0)` puis `pyglet.app.run()`, et dans `capture` :
   `pyglet.image.get_buffer_manager().get_color_buffer().save("capture.png")` puis fermer la
   fenêtre. Avec `dpi_scaling = "stretch"` sur Retina, la capture fait 2560x1600.
   **Linux** : lancer `Xvfb :99 -screen 0 1280x800x24 &`, puis appeler
   `fenetre.switch_to(); fenetre.clear(); fenetre.on_draw(); fenetre.flip()` (**pas**
   `fenetre.dispatch_event("on_draw")`, écran noir) avant la sauvegarde, avec `DISPLAY=:99`.
3. Lancer avec `PYTHONPATH=.` et le Python du `.venv`.
4. Simuler clics/survols (`fenetre.on_mouse_press(...)`, `on_mouse_motion(...)`, ou les méthodes
   internes comme `_essayer_de_cibler`).
5. Inspecter la capture (Read) et, pour une couleur/position précise, échantillonner les pixels avec
   PIL (`Image.open(...).getpixel((x, y))`).
6. Supprimer scripts et captures une fois la vérification faite.
