# web — version navigateur / iPhone (Pyodide)

Chargé automatiquement quand on travaille dans `web/`. Règles générales : `CLAUDE.md` racine.

## Rôle

`index.html` + `web/` exécutent `src/gameplay/` tel quel dans le navigateur via Pyodide.
`bridge.py` sérialise l'état en JSON ; `app.js`/`style.css` ne font que l'afficher — **aucune
règle de jeu en JS**, aucun tirage `random` global (vérifié par `tests/test_architecture.py`).

UI volontairement simplifiée par rapport à pyglet (pas d'infobulle au survol, taille des cases
pilotée par la hauteur d'écran...) : ces écarts sont documentés dans les commentaires de
`app.js`/`style.css`, pas dans `specs/`, qui décrit la version de référence (PC).

Le flux d'interaction doit rester identique au PC (`cliquerCase` ↔ `_essayer_de_cibler` de
`src/ui/fenetre.py`, cf. specs.md §8.3) : toute divergence est un bug.

## À chaque modification

- **Incrémenter `VERSION_CACHE`** dans `app.js` et les paramètres `?v=` dans `index.html` à chaque
  changement de `app.js`/`bridge.py`/`style.css` (cache-busting manuel, cf. commentaire en tête de
  `app.js`).
- Un nouveau fichier dans `src/gameplay/` doit être ajouté à `FICHIERS_A_MONTER` dans `app.js`,
  sinon l'import échoue dans Pyodide et le web ne charge plus (déjà arrivé avec `journal.py`).
- `app.js` fetche aussi `config/*.json` directement : un changement de format doit y rester lisible.

## Tester (obligatoire avant de considérer un changement terminé)

Un vrai test Pyodide n'est pas toujours possible (CDN `cdn.jsdelivr.net` parfois bloqué, Node
absent de la machine Mac) — le **signaler explicitement dans la PR** plutôt que prétendre avoir
testé en navigateur. Méthodes à combiner :

1. **Appeler `bridge.py` directement en Python**, sans navigateur : construire un `Combat` (via
   `creer_combat_poc` ou à la main), assigner `bridge.combat`, puis appeler les fonctions exposées
   (`bridge._etat_dict()`, `bridge.jouer_carte(...)`, etc.) et vérifier le JSON produit — c'est le
   même code que celui exécuté par Pyodide.
2. **Valider la syntaxe** avec `node --check web/app.js` (si Node est disponible).
3. Si un navigateur est accessible : DevTools (menu réactif au pouce, paysage, tailles iPhone).
