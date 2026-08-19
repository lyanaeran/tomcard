# Space Fight

Deckbuilder roguelike (thème vaisseaux spatiaux) inspiré de Slay the Spire. Actuellement un
**POC de combat** jouable (pas de boucle de run complète) — voir `specs/poc.md` pour le détail du POC et
`specs/specs.md` pour la vision de conception globale du jeu complet.

Le jeu se lance de **deux façons**, qui partagent exactement la même logique de jeu
(`src/gameplay/`) et doivent toutes les deux rester fonctionnelles :

## 1. Version PC (pyglet)

```
pip install -e .
python main.py
```

Fenêtre native, affichage géré par [pyglet](https://pyglet.readthedocs.io/) (`src/ui/fenetre.py`).
C'est la version de référence : la plus fidèle à `specs/poc.md`/`specs/specs.md`.

## 2. Version web (navigateur / iPhone)

Aucune installation : `index.html` charge [Pyodide](https://pyodide.org/) (Python compilé en
WebAssembly) et exécute `src/gameplay/` **tel quel**, sans aucune modification, directement dans le
navigateur. `web/bridge.py` fait le lien entre ce moteur Python et l'affichage HTML/CSS/JS
(`web/app.js`, `web/style.css`).

- **En local** : servir le dossier à la racine du dépôt avec un serveur HTTP quelconque (ex.
  `python -m http.server`) et ouvrir `index.html`. Un simple `file://` ne fonctionne pas (les
  `fetch()` de `web/app.js` vers `src/gameplay/*.py` et `config/*.json` ont besoin d'un serveur).
- **En ligne** : publié via GitHub Pages (Settings → Pages → Deploy from a branch → `main` →
  `/ (root)` — nécessite un dépôt public sur un compte gratuit). Le fichier `.nojekyll` à la racine
  est indispensable : sans lui, GitHub Pages traite le site avec Jekyll, qui ignore silencieusement
  tout fichier/dossier commençant par `_` (`src/__init__.py`, `src/gameplay/__init__.py`), causant
  des 404.

Cette version a quelques simplifications visuelles assumées par rapport à `specs/poc.md` (détaillées dans
les commentaires de `web/app.js`/`web/style.css`) : pas d'infobulle au survol (remplacée par un tap
sur une case sans carte sélectionnée), taille des cases pilotée par la hauteur d'écran plutôt que
mesurée pixel près, etc.

## Tests

```
pip install -e ".[dev]"
pytest
```

Les tests couvrent `src/gameplay/` (pur Python, sans dépendance à pyglet ni à la version web) et
`src/ui/animation.py`. Voir `CLAUDE.md` pour les conventions de code et la stack complète.
