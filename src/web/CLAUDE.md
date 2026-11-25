# web — version navigateur / iPhone (Pyodide)

Chargé automatiquement quand on travaille dans `src/web/`. Règles générales : `CLAUDE.md` racine.

## Rôle

`index.html` + `src/web/` exécutent `src/gameplay/` tel quel dans le navigateur via Pyodide.
`bridge.py` sérialise l'état en JSON ; `app.js`/`style.css` ne font que l'afficher — **aucune
règle de jeu en JS**, aucun tirage `random` global (vérifié par `tests/test_architecture.py`).

UI volontairement simplifiée par rapport à pyglet (pas d'infobulle au survol, taille des cases
pilotée par la hauteur d'écran...) : ces écarts sont documentés dans les commentaires de
`app.js`/`style.css`, pas dans `specs/`, qui décrit la version de référence (PC).

Le flux d'interaction doit rester identique au PC (`cliquerCase` ↔ `_essayer_de_cibler` de
`src/ui/fenetre.py`, cf. specs.md §8.3) : toute divergence est un bug.

## À chaque modification

- **Incrémenter `VERSION_CACHE`** dans `app.js`, **`VERSION_WEB`** dans `bridge.py` (même valeur)
  et les paramètres `?v=` dans `index.html` à chaque changement de `app.js`/`bridge.py`/`style.css`
  (cache-busting manuel, cf. commentaire en tête de `app.js`). Au démarrage, `app.js` recharge la
  page si `bridge.py` n'a pas la même version (fichiers de deux mises en ligne mélangés par le
  cache du téléphone) ; `tests/test_architecture.py` vérifie que les trois valeurs sont égales.
- `src/web/editeur.js` (outil d'administration, éditeur de cartes, TEMPORAIRE,
  `specs/outil-editeur-cartes.md`) est chargé après `app.js` : son `?v=` dans `index.html` suit la
  même version. Essai navigateur dédié : `node outils/test_web/essais_editeur.js`.
- Un nouveau fichier dans `src/gameplay/` doit être ajouté à `FICHIERS_A_MONTER` dans `app.js`,
  sinon l'import échoue dans Pyodide et le web ne charge plus (déjà arrivé avec `journal.py`).
- `app.js` fetche aussi `config/*.json` directement : un changement de format doit y rester lisible.

## Tester (obligatoire avant de considérer un changement terminé)

Un vrai test Pyodide n'est pas toujours possible (CDN `cdn.jsdelivr.net` parfois bloqué, Node
absent de la machine Mac) — le **signaler explicitement dans la PR** plutôt que prétendre avoir
testé en navigateur. Méthodes à combiner :

1. **Appeler `bridge.py` directement en Python**, sans navigateur : créer une partie
   (`bridge.nouvelle_partie_web()`, puis `continuer_partie_web(...)` pour un combat), ou construire
   un `Combat` à la main et le passer à `bridge._demarrer_combat`, puis appeler les fonctions
   exposées (`bridge.jouer_carte(index, id_case)`, `bridge.finir_tour()`...) et vérifier le JSON
   produit — c'est le même code que celui exécuté par Pyodide.
2. **Valider la syntaxe** avec `node --check src/web/app.js` (si Node est disponible).
3. **Essais dans un vrai navigateur** : `python -m http.server 8765` à la racine, puis
   `node outils/test_web/essais.js [dossier des captures]` (Chromium + Pyodide, iPhone 13 paysage :
   une partie réelle, des combats préparés, les écrans hors combat, la reprise d'une partie, le
   rechargement sur versions différentes ; sort en erreur au premier contrôle faux). À compléter
   quand on ajoute un écran ou un élément d'affichage. Demande Node et Playwright.
4. Si un navigateur est accessible : DevTools (menu réactif au pouce, paysage, tailles iPhone).
   En session cloud, Chromium + Playwright sont installés : servir le dépôt (`python -m
   http.server`), ouvrir `index.html` au format `devices['iPhone 13 landscape']`, et préparer un
   combat précis depuis la page avec `pyodide.runPython(...)` (les fonctions de `bridge.py` sont
   dans les globales de Pyodide).

### Recette en session cloud (version iPhone, éprouvée le 2026-11-25 sur la PR 79)

1. **Accès au CDN de Pyodide.** Vérifier `curl -s -o /dev/null -w "%{http_code}"
   https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js` (200 attendu). S'il est refusé (403
   du proxy), utiliser l'**environnement cloud « tomcard »** (personnel, créé le 2026-11-25), qui
   autorise `cdn.jsdelivr.net` ; l'environnement « Default » ne l'autorise pas. **Ne pas
   contourner** le blocage (par exemple en servant Pyodide depuis un paquet npm local) : c'est
   refusé ; passer par l'environnement, avec l'accord de l'utilisateur.
2. **Essais de non-régression** : `python -m http.server 8765` en arrière-plan à la racine, puis
   `NODE_PATH=$(npm root -g) node outils/test_web/essais.js <dossier des captures>` (Playwright
   est installé globalement : sans `NODE_PATH`, `require("playwright")` échoue). Environ 3 à 5 min,
   « N controles passes » à la fin. Regarder quelques captures.
3. **Essai ciblé de la nouveauté** quand `essais.js` ne la couvre pas (ex. nouvelles cartes) :
   petit script Playwright qui ouvre la page, attend `#ecran-selection-joueur`, prépare un combat
   avec le même code Python que `PREPARATION_PYTHON` d'`essais.js` (main imposée, électricité
   augmentée si besoin), puis **joue par de vrais clics** (`.carte[data-index=…]` puis
   `.case.<camp>[data-id=…]`) et lit `etatCourant` : valeurs attendues, pastilles
   (`.pastille-…`), popups, journal (`#bouton-journal-combat`), aucune erreur de page. Si l'essai
   a de la valeur durable, l'ajouter à `essais.js`.
4. **Sans Pyodide** (CDN injoignable et pas d'environnement adapté) : on peut encore vérifier le
   **rendu** d'`app.js`/`style.css`. Produire l'état en Python avec `bridge.py` (méthode 1), servir
   la page, puis dans Playwright appeler `masquerTousLesEcrans()`, afficher `#app` et
   `appliquerResultat(<json>)`, et tester les fonctions d'affichage (ex.
   `afficherInfobulle(idCase, "allie" | "ennemi")`, puis lire `#info-case`). Le message
   « Erreur de chargement : loadPyodide is not defined » est alors normal. Cela ne remplace pas
   l'essai complet : le dire dans la PR.
5. **Compte rendu** : dire ce qui a tourné (essais.js, essai ciblé, bridge en Python, rendu sans
   Pyodide) et ce qui n'a pas pu tourner ; arrêter le serveur (`pkill -f "http.server 8765"`).
