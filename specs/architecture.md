# Space Fight — Architecture technique (§10)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

---

## 10. Architecture technique

### 10.1 Stack

- **Langage** : Python 3.11+
- **Affichage PC** : pyglet
- **Affichage web/iPhone** : HTML/CSS/JS + [Pyodide](https://pyodide.org/) (exécute `src/gameplay/`
  tel quel dans le navigateur, sans le modifier) — voir README.md. Les deux façons de jouer doivent
  rester fonctionnelles en permanence (voir CLAUDE.md)
- **Tests** : pytest
- **Dépendances / packaging** : `pyproject.toml`

### 10.2 Arborescence du dépôt

```
assets/
  cartes/      → images des cartes
  modules/     → images des modules
  ennemis/     → images des ennemis
config/        → fichiers de donnees JSON (modules, ennemis, cartes)
src/
  ui/          → tout ce qui concerne l'affichage avec pyglet (PC)
  gameplay/    → logique de jeu, partagee par les deux facons de jouer
index.html, web/ → affichage web/iPhone (Pyodide), voir README.md
saves/         → sauvegardes de partie (PC uniquement, §10.3), ignore par git
tests/
pyproject.toml
```

- `assets/` : uniquement des images pour le moment ; le son sera ajouté plus tard si besoin
- `config/` : contenu du jeu décrit en JSON (modules, ennemis, cartes), référençant les images d'`assets/` — détail du format dans la docstring de `src/gameplay/donnees.py`
- Séparation stricte entre `src/ui` (affichage PC) et `src/gameplay` (logique de jeu, partagée avec la version web)
- `src/gameplay` reste la seule source de vérité des règles de jeu : la version web ne fait que l'exécuter et l'afficher, elle ne réimplémente aucune règle

### 10.3 Persistance du parcours (profils et sauvegardes)

Nécessaire pour que les dégâts/niveau de mise à jour des modules (§2.2) et l'avancement dans le
parcours (§2.3) survivent d'un combat à l'autre. **Les sauvegardes sont rattachées à un joueur**
(décision utilisateur) : pas de compte/login, mais plusieurs **profils locaux nommés** peuvent
coexister sur un même appareil. **Un joueur ne peut avoir qu'une seule partie EN_COURS à la fois**
(décision utilisateur) — remplace la piste antérieure de plusieurs parties actives en parallèle par
profil ; ses anciennes parties `TERMINEE` restent sur disque (pour de futures statistiques, voir
plus bas) mais ne sont pas sélectionnables, il n'y a donc **pas besoin d'écran de sélection de
partie** (contrairement à ce qui avait été envisagé).

**Implémenté** — `main.py`/`index.html` sont désormais le **vrai point d'entrée du jeu** (décision
utilisateur), plus des écrans autonomes non reliés comme les précédents.

#### Profil joueur

- PC : `saves/<joueur_id>/profil.json` ; web : `localStorage` (une entrée par joueur, sous la clé
  `space_fight_joueurs`, contenant directement la liste des profils plutôt qu'un index séparé — plus
  simple tant que les profils restent de petits objets)
- **Contenu actuel** : `{"version": 1, "id": "joueur_20260823_140000", "nom": "Alice"}`
- **Statistiques et déblocages évoqués par l'utilisateur (parties jouées/victoires/défaites, niveau
  max atteint, module le plus choisi, déblocages en fin de partie) : sciemment laissés de côté pour
  l'instant** (décision utilisateur explicite, "pas de stat pour le moment") — pas de champ dans le
  JSON actuel, à ajouter dans une passe dédiée. Pistes envisagées à ce moment-là : compteurs mis à
  jour au fil du jeu plutôt que recalculés depuis l'historique (`parties_jouees`, `defaites`,
  `niveau_max`, `modules_choisis` par `module_id`) ; `victoires` reste bloqué tant qu'une condition
  de victoire de run n'est pas définie (voir §9.1) ; `deblocages` en liste vide, mécanique à
  imaginer

#### Partie (une sauvegarde, rattachée à un profil)

- PC : `saves/<joueur_id>/parties/<partie_id>.json` (un fichier par partie, y compris les
  `TERMINEE` conservées) ; web : `localStorage`, une entrée `space_fight_partie_<joueur_id>` — une
  seule a la fois (cf. "un joueur ne peut avoir qu'une seule partie EN_COURS" plus haut : les
  parties `TERMINEE` ne sont pour l'instant pas conservées côté web, contrairement à PC — écart
  volontaire tant qu'aucun écran n'affiche l'historique, voir §9.1)
- **Format 2 (refonte branchée, PR 1, 2026-11-12)** : `version` vaut 2 ; chaque module du
  `vaisseau` porte aussi son identifiant d'exemplaire (`{"module_id": "MOD_2", "exemplaire": "M2",
  "pv": 20, "pv_max": 20, "niveau_maj": 1}`, `pv` ne compte que pour le principal) ; le `deck` est
  une liste `{"id": "CRT_7", "module": "M1"}` (carte rattachée à un exemplaire de module,
  `partie.CartePossedee`). **Une partie d'une autre version est abandonnée à la lecture**
  (décision utilisateur du 2026-11-11 n° 1, aucune conversion) : `partie.lire_partie` renvoie
  `None`, `partie_en_cours` (PC) efface le fichier ; le profil est gardé (son format ne change
  pas, `VERSION_PROFIL` = 1). Le web devra faire de même avec `localStorage` (PR 2). Ancien
  format (version 1) :
- **Contenu** :
  ```json
  {
    "version": 1,
    "id": "partie_20260823_142301",
    "nom": "Partie du 23/08/2026",
    "statut": "EN_COURS",
    "graine": 918273645,
    "niveau": 1,
    "argent": 0,
    "vaisseau": {
      "base":           {"module_id": "MOD_1", "pv": 15, "pv_max": 15, "niveau_maj": 1},
      "avant_gauche":   null,
      "avant_droite":   null,
      "arriere_gauche": null,
      "arriere_droite": null
    },
    "deck": ["CRT_7", "CRT_7", "CRT_7", "CRT_7", "CRT_8", "CRT_9", "CRT_10", "CRT_10", "CRT_10", "CRT_10", "CRT_11", "CRT_12"]
  }
  ```
  - `version` : version du format, pour d'éventuelles migrations futures
  - `id` : identifiant unique (nom de fichier PC / suffixe de clé localStorage web)
  - `nom` : affiché dans les futurs écrans d'historique (généré automatiquement pour l'instant à
    partir de la date — pas de renommage par le joueur prévu dans un premier temps)
  - `statut` : `EN_COURS` ou `TERMINEE` (décision utilisateur : une défaite ou un abandon **ne
    supprime pas** le fichier PC, marqué `TERMINEE` pour un futur écran de récapitulatif de run —
    une nouvelle partie crée un nouvel `id`)
  - `graine` : graine maîtresse du run (décision utilisateur). Combinée au `niveau`
    (`aleatoire_pour_niveau(graine, niveau)`, §2.3), elle **retire à l'identique** les propositions
    d'étape d'un niveau sans les stocker littéralement — cohérent avec la convention `random.Random` déjà utilisée partout dans le moteur (voir
    "Déterminisme du tirage aléatoire" dans `CLAUDE.md`). Utilisée pour tirer les 3 candidats du
    choix de module de Niveau 1 d'une nouvelle partie, les propositions du choix du prochain niveau,
    et comme graine de repli pour le combat approximatif du bouton "Continuer" (voir plus bas)
  - `niveau` : niveau courant (1 pour une partie neuve, incrémenté par `avancer_niveau()` à chaque
    étape résolue — choix de module, combat gagné — cf. §2.4)
  - `vaisseau` : un état par emplacement (base + 4 équipables, §5) — `module_id` (référence
    `config/modules.json`), `pv`/`pv_max` (§2.2), `niveau_maj` (palier de mise à jour, 1 à 3, §2.2) ;
    `null` si l'emplacement est vide. Une partie neuve n'a que `base` d'équipé (deck/PV du module
    principal, `config_poc.ids_deck_module_principal`) — le 2ᵉ emplacement est rempli au choix du
    Niveau 1 (`equiper_module()`, §2.4)
  - `deck` : ids de cartes possédées (`config/cartes.json`), doublons répétés dans la liste — même
    principe que `regrouper_cartes()` (§6) pour l'affichage, mais stockage à plat ici

#### Écrans (implémentés, PC + web)

Fond de combat réutilisé en placeholder (comme les autres écrans du parcours), à remplacer par un
fond dédié.

- **Sélection/création/suppression de profil** — liste des profils existants (clic pour choisir) +
  création d'un profil par un nom (Entrée/bouton "Créer"). `src/ui/ecran_selection_joueur.py` (PC,
  saisie de texte gérée manuellement via `on_text`/`on_key_press`, pas de widget pyglet dédié) ;
  `web/app.js` (`afficherSelectionJoueur`/`creerNouveauJoueur`) + `web/bridge.py`
  (`creer_profil_web`)
  - **Suppression d'un profil** : bouton croix rouge sur chaque ligne (même icône que "Quitter" en
    combat, `assets/interface/quitter.png`, déjà associée dans le jeu à une action destructive) —
    action irréversible, jamais exécutée sans confirmation explicite ("Vous allez détruire le
    joueur *nom*, êtes-vous sûr ?"). PC : dialogue de confirmation dessiné par-dessus la liste
    (`EcranSelectionJoueur._dessiner_dialogue_confirmation`, `GROUPE_SUPERPOSITION` pour garantir
    l'ordre de dessin, cf. "Pièges pyglet connus" du `CLAUDE.md`), Oui appelle
    `src/gameplay/partie.py:supprimer_profil` (supprime le dossier du profil sous `saves/`, parties
    sauvegardées incluses). Web : `confirm()` natif du navigateur plutôt qu'une boîte de dialogue
    maison (aucune infrastructure de modale ailleurs dans le web du jeu) — `supprimerJoueurLocal`
    (`web/app.js`) retire le profil de l'index `localStorage` et sa partie sauvegardée éventuelle
- **Accueil du joueur** — si une partie `EN_COURS` existe : niveau, vaisseau (grille des modules
  équipés avec PV/PV max/niveau de mise à jour, ou "Emplacement vide"), boutons **Continuer** /
  **Abandonner la partie** / **Voir le deck**. Sinon : bouton **Nouvelle partie**.
  `src/ui/ecran_accueil_joueur.py` (PC) ; `web/app.js` (`afficherAccueilJoueur` et les handlers de
  chaque bouton) + `web/bridge.py` (`infos_vaisseau_web`, `deck_partie_web`, `abandonner_partie_web`,
  `nouvelle_partie_web`, `choix_module_partie_web`, `continuer_partie_web`)
- **Nouvelle partie** → écran de choix de module du Niveau 1 déjà existant (§2.3), candidats tirés à
  partir de la graine de la partie fraîchement créée
- **Voir le deck** → écran "deck en entier" déjà existant (§6), alimenté par le deck réel de la
  partie (pas une démonstration aléatoire). L'Écran de partie ayant déjà été fermé/masqué à
  l'ouverture, un bouton **Retour** (PC : `EcranDeck.termine` ; web : `#bouton-retour-deck`) est le
  seul moyen d'y revenir — bug réel corrigé après un premier passage sans lui (aucune fermeture de
  fenêtre native ne rouvrait quoi que ce soit sur PC, et aucune navigation possible sur web)
- **Continuer** → reprend l'étape exacte où le joueur s'était arrêté (§2.4, étape 2) : Choix de
  module si Niveau 1 sans 2ᵉ module équipé, sinon Choix du prochain niveau pour le niveau courant.
  Un combat lancé depuis là (Prime ou Boss) reprend le vaisseau/deck réels de la partie, mais tire
  toujours une **flotte ennemie au hasard** — l'orchestration ne détermine pas encore précisément
  quel combat affronter à ce niveau (nombre/taille d'ennemis selon §3.2, voir §10.3 "Limites
  connues"). `combat_depuis_partie()` dans `src/gameplay/partie.py`
- **Abandonner la partie** : marque la partie `TERMINEE` (`marquer_terminee()`) et revient à
  l'écran d'accueil, qui affiche alors le bouton "Nouvelle partie"
- **Enchaînement complet d'une vraie partie** (§2.4, étapes 2 à 6) : décidé par
  `src/gameplay/deroulement.py` (cf. §2.4), affiché par `main.py` (PC, une fonction `_ouvrir_xxx`
  par écran, transitions détectées via `pyglet.clock.schedule_interval`) ; côté web,
  `web/app.js` garde une variable `partieActive` (la `Partie` en cours d'orchestration, ou `null`
  en mode démonstration) que `choisirModule`/`choisirEtape`/`choisirRecompense` consultent pour
  choisir entre persistance réelle et comportement de démonstration (`console.log`) inchangé

#### Implémentation

- `src/gameplay/partie.py` (nouveau) : dataclasses `Profil`/`Partie`/`EtatModule`, sérialisation
  JSON pure (`profil_vers_json`/`profil_depuis_json`, `partie_vers_json`/`partie_depuis_json`,
  testables sans I/O), `nouveau_profil`/`nouvelle_partie`/`combat_depuis_partie`/`marquer_terminee`,
  et l'I/O fichier PC (`lister_profils`, `creer_profil`, `supprimer_profil`, `sauvegarder_partie`,
  `partie_en_cours`, `abandonner_partie`, sous `saves/`, nouveau dossier ajouté au `.gitignore`)
  - Nom `Profil` retenu plutôt que `Joueur` (déjà pris par `src/gameplay/joueur.py`, l'état de
    combat éphémère vaisseau + deck + électricité, §3.3) — pas de collision
  - `config_poc.deck_module_principal` factorisé en `ids_deck_module_principal` (renvoie des ids
    plutôt que des `Carte`) pour être réutilisable par `nouvelle_partie` sans dupliquer la règle
- `web/bridge.py` : les fonctions ci-dessus n'effectuent **aucune I/O** (Pyodide n'a pas de FS
  persistante entre rechargements de page) — elles ne font que (dé)sérialiser et appliquer la
  logique pure de `partie.py` ; la lecture/écriture `localStorage` est entièrement gérée côté
  `web/app.js`
- `main.py` : ouvre `EcranSelectionJoueur`, puis `EcranAccueilJoueur`, puis l'écran suivant
  décidé par `src/gameplay/deroulement.py` (§2.4) — chaque écran étant une fenêtre pyglet indépendante, les transitions ferment la
  fenêtre courante et ouvrent la suivante, détectées via `pyglet.clock.schedule_interval` (pas
  d'événement dédié "l'utilisateur a fait un choix" sur ces fenêtres). Le comportement par défaut
  de pyglet (quitter l'application dès que la dernière fenêtre se ferme) est remplacé
  (`main.py:_on_window_close`) : la vérification "plus aucune fenêtre ouverte" est reportée au tick
  suivant, une fois l'écran suivant ouvert — sans quoi le jeu s'arrêtait juste après la sélection
  du joueur (bug constaté sur macOS). Fermer la dernière fenêtre (bouton de fermeture natif) quitte
  toujours le jeu. Sur écran HiDPI (Retina), `main.py` règle `pyglet.options.dpi_scaling = "stretch"` :
  toutes les fenêtres restent en coordonnées logiques 1280x800, étirées sur tout le framebuffer
  (avec le mode par défaut, le jeu n'occupait que le quart en bas à gauche de la fenêtre sur Mac)

#### Limites connues (à lever plus tard)

- **Portée volontairement limitée** : seuls les points de passage entre étapes sont sauvegardés
  (juste après choix de module, juste après résolution d'une fin de combat, d'une Station service
  ou d'une étape Aventure/Planète commerciale) — un combat en cours n'est pas sauvegardable ; le
  quitter en cours de route (fermer l'onglet/l'appli) le fait recommencer entièrement à la reprise,
  au même niveau
- Planète commerciale n'a pas encore de contenu propre (§2.4, étape 9, §9.1) : l'écran générique
  (`EcranEtapePlaceholder`) la représente, sans autre effet que d'avancer au niveau suivant.
  L'Aventure a désormais sa propre implémentation pour ses trois variantes (Trois lunes, Astéroïdes,
  Police, §2.5)
- Le run s'arrête réellement au Niveau 10 dans l'état actuel (décision utilisateur, provisoire,
  voir §2) : la Victoire finale (§2.4, étape 11) marque la partie `TERMINEE` sans proposer de
  continuation au-delà de ce niveau
- La flotte ennemie d'un combat (Prime ou Boss) applique désormais les règles de difficulté par
  niveau (§13.4, `creer_flotte_prime`/`creer_flotte_boss`) : **résolu**, n'est plus un tirage de
  démonstration
- Écart PC/web sur la conservation des parties `TERMINEE` (voir "Partie" plus haut) : à corriger si
  un écran d'historique est construit côté web
- `argent` progresse désormais via les combats gagnés et la Station service (§2.1/§2.2) ; la Planète
  commerciale n'a toujours aucun effet dessus, son contenu n'étant pas construit (§9.1)

### 10.4 Conventions de code

- Classes claires et bien définies, une responsabilité par classe
- Commentaires en français, **sans accents ni cédilles** (ASCII uniquement)
- Tests unitaires (pytest) dans `tests/`
