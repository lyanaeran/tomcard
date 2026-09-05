# Space Fight

Deckbuilder roguelike (thème vaisseaux spatiaux) inspiré de Slay the Spire. Le **POC de combat**
est jouable ; le développement porte maintenant sur le **parcours** (boucle de run), construit
écran par écran (voir specs.md §2.3 et suivants) - pas encore d'orchestration reliant ces écrans
entre eux ni au combat.

## Langue

Répondre à l'utilisateur en français, y compris pour les messages de statut/résumés (les
commentaires de code restent en français ASCII comme précisé plus bas ; le code lui-même — noms de
variables, identifiants — reste en français, déjà la convention du projet).

## Documents de référence (à tenir à jour)

- `specs/specs.md` — vision de conception globale du jeu complet (boucle de run, modules, cartes,
  etc.), document vivant et seule source de vérité pour le design (le POC de combat y est
  documenté au même titre que le reste, plus de spec séparée depuis que le développement a basculé
  sur le parcours)
- `specs/cartes.xlsx` — registre éditable des cartes (une ligne par carte du tableau de conception,
  colonnes Rareté/Module/Catégorie/Cible/Coût/X/Y/Munition/Nom/Description/Jouable/Notes), miroir
  humainement modifiable de `config/cartes.json`. Pas rechargé par le code (`config/cartes.json`
  reste la seule source de vérité pour le moteur) : si l'un est modifié, reporter le changement dans
  l'autre à la main.

**`specs.md` doit rester synchronisé avec le code.** Quand une décision de design est prise ou
clarifiée en cours d'implémentation (ex. règle de ciblage, format d'une carte, retour visuel d'un
effet, mécanique du parcours), reporte-la dans `specs/specs.md`. Inversement, avant d'implémenter une
fonctionnalité un peu ambiguë, relis la section concernée de ce fichier.

## Deux façons de jouer (PC et web/iOS) — les deux doivent rester fonctionnelles

Le jeu se lance de deux façons distinctes, qui partagent la même logique (`src/gameplay/`) mais ont
chacune leur propre couche d'affichage. Voir `README.md` pour les instructions de lancement
détaillées.

- **PC (pyglet)** : `python main.py`, affichage natif via `src/ui/fenetre.py`. Version de référence,
  la plus fidèle à `specs/specs.md`.
- **Web (navigateur / iPhone)** : `index.html` + `web/` (`app.js`, `style.css`, `bridge.py`).
  Exécute `src/gameplay/` tel quel dans le navigateur via [Pyodide](https://pyodide.org/) (Python
  compilé en WebAssembly) ; `web/bridge.py` sérialise l'état du combat en JSON pour l'affichage
  HTML/CSS/JS. UI volontairement simplifiée par rapport à pyglet (pas d'infobulle au survol, taille
  des cases pilotée par la hauteur d'écran...) — ces écarts sont documentés dans les commentaires de
  `web/app.js`/`web/style.css`, pas dans `specs/specs.md` qui décrit la version de référence.

**Ces deux façons de jouer doivent rester fonctionnelles en permanence.** En particulier :

- Une modification de `src/gameplay/` (nouvelle fonction, signature changée, nouveau champ sur une
  entité...) doit rester compatible avec ce que `web/bridge.py` attend de ce module ; vérifier
  `web/bridge.py` avant de renommer/déplacer quoi que ce soit dans `src/gameplay/`.
- Une modification de `config/*.json` (nouveau champ, format changé) doit rester chargeable par
  `src/gameplay/donnees.py` **et** rester interprétable par `web/bridge.py`/`web/app.js` (qui
  fetchent ces fichiers directement).
- `src/gameplay` reste la seule source de vérité pour les règles de jeu : ne jamais dupliquer une
  règle en JS dans `web/app.js`, qui ne doit que lire/afficher l'état renvoyé par `web/bridge.py`.
- **Le flux d'interaction (nombre de clics/taps pour jouer une carte) doit rester identique entre PC
  et web**, même pour les cartes "sans clic de ciblage" (Alliés/Ennemis multiples, Module principal) :
  sélectionner la carte puis confirmer par un clic/tap sur une case vivante du bon camp — jamais de
  résolution automatique au seul clic sur la carte, cf. specs.md §8.3. Toute divergence de
  ce flux entre `src/ui/fenetre.py` (`_essayer_de_cibler`) et `web/app.js` (`cliquerCase`) est un bug.
- **Tout changement doit être testé sur PC et sur web/iOS avant d'être considéré terminé** — pas
  seulement vérifié par lecture de code des deux côtés. Un changement qui touche `src/gameplay/` ou
  `config/*.json` sans impact visuel/interactif (règle de calcul interne, etc.) reste couvert par
  `pytest` seul, qui s'exécute contre le même code pour les deux versions ; tout changement qui
  touche `src/ui/fenetre.py`, `web/app.js`/`web/style.css`/`web/bridge.py`, ou le comportement visible
  d'une carte/mécanique, doit être vérifié sur les deux avec les méthodes de la section "Tester les
  deux versions" ci-dessous.

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
  minuterie de `src/ui/`, `test_architecture.py` pour les règles ci-dessous). Les fonctions de
  `src/ui/fenetre.py` autres que les minuteries, et tout `web/`, ne sont pas couverts par pytest
  (voir "Tester les deux versions" ci-dessous)

**`src/ui` et `web/` ne doivent jamais posséder de règle de jeu ni d'état de session** (uniquement
la présentation d'un état déjà décidé par `src/gameplay`) — précédent concret : le journal de
combat (`Combat.journal`) et la résolution des Aventures Astéroïdes/Police
(`src/gameplay/partie.py:second_choc_asteroides`/`EtatAventurePolice`) vivent entièrement dans
`src/gameplay`, PC et web ne font que lire/afficher ce qu'ils renvoient. Avant de considérer
terminée une tâche qui ajoute du code à `src/ui` ou `web/`, vérifier qu'aucun nouveau fichier/état
touché n'y contient : un tirage aléatoire non injecté (cf. "Déterminisme du tirage aléatoire"
ci-dessous, vérifié par `tests/test_architecture.py`), une machine à états qui décide d'une
branche métier (ex. "une carte est-elle offerte ?") plutôt que de l'afficher, une ressource à usage
limité (ex. "disponible une seule fois") suivie localement sans exister côté `src/gameplay`, ou une
condition métier (ex. un seuil d'Argent) re-vérifiée en plus de la valeur de retour déjà fiable
d'une fonction gameplay. `tests/test_architecture.py` vérifie mécaniquement une partie de ces
points ; le reste reste une vérification manuelle à faire systématiquement, pas seulement quand
elle est demandée.

## Conventions de code

- Une responsabilité claire par classe
- Commentaires en français, **ASCII uniquement (sans accents ni cédilles)** — cette règle ne
  s'applique qu'au code, pas à `specs/specs.md`/`CLAUDE.md` qui utilisent l'orthographe normale
- Docstrings courtes, une ligne si possible
- `src/gameplay` ne doit jamais importer `pyglet` ; si une fonction a besoin d'affichage, elle
  appartient à `src/ui`

## Tester les deux versions

Aucune des deux UI n'a de tests pytest classiques (`fenetre.py` : dessiner avec pyglet n'est pas
unitaire ; `web/` : n'est pas exécuté par pytest du tout, cf. Architecture). Un changement visible
sur l'une ou l'autre doit donc être vérifié manuellement avec les méthodes ci-dessous **avant d'être
considéré terminé** (cf. "Deux façons de jouer").

### PC (pyglet)

1. Lancer un serveur X virtuel : `Xvfb :99 -screen 0 1280x800x24 &`
2. Écrire un petit script Python qui construit une `FenetreCombat`, appelle
   `fenetre.switch_to(); fenetre.clear(); fenetre.on_draw(); fenetre.flip()` (**pas**
   `fenetre.dispatch_event("on_draw")`, qui produit un ecran noir dans cet environnement), puis
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

### Web (iOS/navigateur)

Un vrai test en navigateur avec Pyodide n'est pas toujours possible (le CDN `cdn.jsdelivr.net` peut
être bloqué par le sandbox réseau de l'environnement d'exécution) — dans ce cas, le signaler
explicitement dans la PR plutôt que prétendre avoir testé en navigateur. Méthodes de repli, à
combiner :

1. **Appeler `web/bridge.py` directement en Python**, sans navigateur : construire un `Combat` (via
   `creer_combat_poc` ou à la main), assigner `bridge.combat`, puis appeler les fonctions exposées
   (`bridge._etat_dict()`, `bridge.jouer_carte(...)`, etc.) et vérifier le JSON produit — c'est le
   même code que celui exécuté par Pyodide dans le navigateur, aucune logique n'est dupliquée
2. **Valider la syntaxe de `web/app.js`** avec `node --check web/app.js` (n'exécute pas le code,
   détecte seulement les erreurs de syntaxe)
3. Si un navigateur réel est accessible, tester manuellement dans les DevTools (menu réactif au
   pouce, orientation paysage, tailles d'écran iPhone)
4. **Incrémenter `VERSION_CACHE`** dans `web/app.js` et les paramètres `?v=` dans `index.html` à
   chaque changement de `app.js`/`bridge.py`/`style.css` (cache-busting manuel, cf. commentaire en
   tête de `app.js`)

## Déterminisme du tirage aléatoire

Tout ce qui est tiré au sort (vaisseau, flotte, deck) passe par un `random.Random` explicite
injecté dans `creer_combat_poc(generateur_aleatoire=...)` — jamais le module `random` global
directement — pour que les tests et les captures d'écran restent reproductibles. Cette règle
**s'étend à tout tirage du parcours**, pas seulement au combat (Aventures comprises : carte offerte
d'Astéroïdes, tirage de carte de Police...) — un écran PC (`src/ui/ecran_aventure_*.py`) ou
`web/bridge.py` peut construire son propre `random.Random()` (non seedé si la reproductibilité
n'est pas exigée pour cet écran), mais **jamais un tirage direct sur le module `random`**
(`random.choice(...)`, `random.random()`...) et jamais une instance jetable recréée à chaque appel
là où une instance unique, injectable, devrait être conservée d'un bout à l'autre d'un écran/d'une
session (cf. `Combat.aleatoire`, `EcranAventureAsteroides.aleatoire`) — voir
`tests/test_architecture.py`, qui vérifie mécaniquement l'absence d'appel direct au module
`random` global dans tout `src/` et `web/`.

## Pièges pyglet connus

- `pyglet.text.Label(...)` **ne supporte pas `bold=True`** dans la version installée (2.1.16) →
  `TypeError`. Ne pas l'utiliser.
- Dans un `Batch` partagé, l'ordre de dessin entre `Sprite` et formes/texte (`shapes.*`,
  `text.Label`) **n'est pas garanti** par l'ordre de création. Utiliser un `pyglet.graphics.Group`
  explicite (voir `GROUPE_SUPERPOSITION` dans `fenetre.py`) pour forcer ce qui doit rester
  au-dessus des sprites (pastilles, popups, infobulles, bandeaux...).

## Git / PR

**Une seule branche de travail : `devjeux`.** Ne pas créer de nouvelle branche à chaque tâche (ça a
produit un grand nombre de branches mortes/orphelines dans ce projet, cf. plus bas) : tout le
développement se fait sur `devjeux`, avec une PR `devjeux` → `main` par changement logique, plan de
test dans la description. Toute valeur numérique inventée faute de spec précise (PV, dégâts,
coûts...) doit être signalée comme telle dans la PR et dans `specs/specs.md`.

**Avant de pousser un commit supplémentaire sur `devjeux`, vérifier l'état de sa PR** (mergée/fermée
ou encore ouverte). Pousser sur une branche dont la PR est déjà mergée ou fermée laisse le commit
orphelin, jamais intégré à `main` sans action manuelle supplémentaire — c'est arrivé plusieurs fois
dans ce projet quand chaque tâche avait sa propre branche. Si la PR `devjeux` → `main` est déjà
mergée/fermée, remettre `devjeux` à jour depuis `main` avant de continuer
(`git fetch origin main && git checkout -B devjeux origin/main && git push -f origin devjeux`)
plutôt que de pousser sur l'état obsolète de la branche, et plutôt que de créer une branche
supplémentaire.

**Ouvrir la PR `devjeux` → `main` systématiquement après chaque push**, sans attendre que
l'utilisateur la demande explicitement (préférence confirmée par l'utilisateur) — que ce soit une
nouvelle PR (si la précédente est mergée/fermée) ou une mise à jour de la description d'une PR déjà
ouverte sur le même commit.
