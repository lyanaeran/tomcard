# Space Fight — POC (preuve de concept)

*Spécification minimale pour un premier combat jouable — dérivée de `specs.md`*

---

## 1. Objectif

Un combat sur la grille complète, avec un vaisseau et une flotte ennemie **tirés au sort à chaque lancement** à partir des fichiers de `config/` (modules, ennemis, cartes), pour valider le placement 2x3, le ciblage à cible multiple, le ciblage automatique des ennemis et l'affichage avec les vraies images — en plus de la boucle de combat déjà validée dans les versions précédentes du POC (jouer des cartes, dépenser de l'électricité, infliger des dégâts, encaisser une attaque).

Simplifications restantes par rapport à `specs.md` : pas de boucle de run (pas d'étapes, pas de boss, pas de récompense de cartes), pas d'ennemis de taille L (point encore ouvert en specs.md §9.1, volontairement évité ici). Un seul combat, une seule fois — mais différent (et rejouable) à chaque lancement grâce au tirage aléatoire.

**⚠️ Toutes les valeurs numériques de ce document (PV, dégâts, coûts) sont inventées faute d'être spécifiées ailleurs — à ajuster après test.**

---

## 2. Vaisseau du joueur

Grille **2 colonnes (Avant / Arrière) x 3 rangées (Gauche / Mid / Droite)**, comme décrit en specs.md §3.1/§5. La colonne Avant fait face à l'ennemi. Le module de base occupe la rangée Mid en entier (les deux colonnes) ; les 4 autres modules équipés occupent chacun une case.

**Composition tirée au sort à chaque combat**, à partir de `config/modules.json` (6 modules définis : Principal + 5 autres) :
- Le module **Principal** (`MOD_1`) est toujours la base
- **4 modules différents** sont tirés au sort parmi les 5 autres (Lanceur de missiles, Blindage, Générateur, Soute, Sabotage) et placés aléatoirement sur les 4 cases équipables — un des 5 modules ne sera donc pas présent dans le combat
- PV et cartes jouables de chaque module : voir `config/modules.json`

- **Électricité** : 5 par tour (ressource pleine à chaque début de tour, ne se cumule pas d'un tour à l'autre)
- **Main** : capacité maximale de **10 cartes** ; le joueur pioche **5 cartes par tour**
- Cartes jouées partent en défausse ; quand la pioche est vide, la défausse est mélangée pour reformer la pioche (comme Slay the Spire, cf. specs.md §3.3)
- Un module (autre que la base) à 0 PV est détruit mais **ne met pas fin au combat** ; seule la destruction de la base termine la run (specs.md §3.4)

---

## 3. Ennemis

Grille miroir **2 colonnes (Avant / Arrière) x 3 rangées (Gauche / Mid / Droite)**, la colonne Avant faisant face au joueur. Pas de base côté ennemi : les 6 cases sont indépendantes.

**Composition tirée au sort à chaque combat**, à partir de `config/ennemis.json` (3 ennemis définis) : un ennemi est tiré au sort **avec remise** pour chacune des 6 cases — les 6 cases sont donc toujours remplies, avec des doublons possibles (voire un ennemi absent du tirage). PV et dégâts de chaque ennemi : voir `config/ennemis.json`.

**Ciblage automatique** : chaque ennemi attaque un seul module du joueur par tour, choisi ainsi :
1. Regarder sa **propre rangée** (celle où il se trouve) : d'abord la case Avant de cette rangée, puis la case Arrière de cette même rangée si l'Avant est vide/détruite
2. Si sa rangée entière est vide, passer à la **rangée la plus proche** (même règle avant-puis-arrière), et ainsi de suite
3. La rangée Mid contient toujours la base (tant qu'elle est vivante)

**Important** : la base ne protège pas les modules Arrière des autres rangées — un ennemi peut attaquer directement le module Arrière de sa propre rangée si l'Avant de cette rangée est vide, même si la base (Mid) est toujours en vie.

**Ordre de résolution des attaques** (`Combat._tour_ennemi`) : la colonne Avant de haut en bas (Gauche, Mid, Droite), puis la colonne Arrière de haut en bas. Cet ordre est surtout significatif quand un Leurre (§12.6) protège un module visé par plusieurs ennemis dans le même tour : seule la **première** attaque résolue sur ce module (au sens de cet ordre) est annulée, les suivantes s'appliquent normalement.

Chaque attaque résolue affiche un popup `-N` (dégâts réellement infligés, voir §8) sur le module touché. Au survol de la souris sur un ennemi vivant, une infobulle affiche la cible qu'il vise et les dégâts qu'il **infligerait** ce tour (la vraie attaque de cet ennemi, jamais affectée par un Leurre potentiellement actif sur sa cible — seule la résolution réelle du tour applique l'annulation), calculés avec la même règle (voir §8).

---

## 4. Cartes

23 cartes jouables définies dans `config/cartes.json` (issues du tableau de conception complet de
l'utilisateur, dont 15 autres cartes sont stockées mais pas encore jouables faute de mécanique
correspondante dans le moteur — voir specs.md §12 pour l'inventaire de ce qui manque). Chaque carte
a un type, un coût, une cible et une rareté :

**Types** (`TypeCarte`, specs.md §7.1) : `ATTAQUE`, `DEFENSE`, `REPARATION` (remplace l'ancien
`SOIN`), `OUTILS` (manipule une ressource commune au joueur — électricité ou pioche — pas un
module/ennemi précis, cf. plus bas), `DEBUFF` (affaiblit un ennemi, temporairement), `BUFF`
(renforce un module allié, temporairement ou de façon persistante).

**Cibles**, avec leur comportement au clic :

| Cible | Comportement au clic |
|---|---|
| **Ennemi unique** | Sélectionner la carte, puis cliquer un ennemi vivant |
| **Allié unique** | Sélectionner la carte, puis cliquer un module vivant (pour une carte Outils, le module cliqué n'a pas d'influence sur l'effet, cf. specs.md §12.11) |
| **Ligne ennemie** | Sélectionner la carte, puis cliquer un ennemi vivant — touche aussi l'autre case (Avant ↔ Arrière) de la **même rangée**, si elle est occupée |
| **Alliés multiples** | Sélectionner la carte, puis cliquer **n'importe quel** module allié vivant pour confirmer (la case cliquée n'a pas d'influence, l'effet touche tous les modules vivants du joueur) |
| **Ennemis multiples** | Sélectionner la carte, puis cliquer **n'importe quel** ennemi vivant pour confirmer (la case cliquée n'a pas d'influence, l'effet touche tous les ennemis vivants) |
| **Module principal** | Sélectionner la carte, puis cliquer **n'importe quel** module allié vivant pour confirmer (la case cliquée n'a pas d'influence, l'effet touche toujours le module de base) |
| **Colonne avant/arrière ennemie** | Sélectionner la carte, puis cliquer un ennemi de la colonne visée par la carte (avant ou arrière, fixé par la carte — un clic sur l'autre colonne est refusé) — touche les 3 ennemis de cette colonne |
| **Colonne avant alliée** | Sélectionner la carte, puis cliquer un module de la colonne avant (avant-gauche ou avant-droite, jamais le module principal — un clic sur l'arrière ou le module principal est refusé) — touche les 2 modules de cette colonne |

Pour Alliés multiples/Ennemis multiples/Module principal (les 3 cibles "sans clic de ciblage précis"
de specs.md §7.2), la cible cliquée ne détermine pas l'effet, mais **un clic de confirmation reste
obligatoire** sur une case vivante du bon camp — la carte ne se joue jamais au seul clic de
sélection, pour éviter qu'un clic accidentel sur une carte en main ne la joue immédiatement. **Ce
flux (sélection puis confirmation) est identique sur PC et sur web/iOS**, cf. CLAUDE.md.

**Cartes Outils** : leur effet ne porte jamais sur un module/ennemi mais sur une ressource commune
(gagner de l'électricité, piocher des cartes supplémentaires) — un champ `action` (`GAIN_ELECTRICITE`
/ `PIOCHE_SUPPLEMENTAIRE`) précise laquelle, cf. §8.

**Cartes Debuff** : affaiblissent temporairement un ennemi, pour un nombre de tours donné (`duree`,
décrémenté à la fin de chaque tour ennemi, que l'ennemi concerné ait agi ou non) :
- `REDUCTION_DEGATS` : diminue les dégâts infligés par l'ennemi lors de ses prochaines attaques
- `VULNERABILITE` : augmente en % les dégâts qu'il subit des attaques du joueur
- `REDIRECTION_CIBLE` : au prochain tour ennemi, l'ennemi debuffé attaque un **autre ennemi vivant
  tiré au hasard** plutôt qu'un module du joueur (*Tir allié*, specs.md §12.6) ; sans autre ennemi
  vivant, il attaque normalement (rien à rediriger vers). Le tirage au hasard n'a lieu qu'à la
  résolution réelle du tour (`Combat._cible_redirection`), jamais lors d'un survol/tap de
  prévisualisation (`Combat.previsualiser_cible`), pour ne pas consommer l'aléa à chaque redessin
  (cf. CLAUDE.md "Déterminisme du tirage aléatoire") : tant que le debuff est actif, l'infobulle affiche "Vise
  un allié au hasard" plutôt qu'une cible précise, et l'intention réelle n'est connue qu'après
  "Fin de tour"

Chaque debuff appliqué est **indépendant** des autres : un ennemi porte une liste de 0 à N debuffs
actifs, sans fusion ni remplacement, même entre deux debuffs du même type. Tant qu'ils sont actifs,
leurs magnitudes s'additionnent (ex : un ennemi avec Vulnérabilité +20% pendant 1 tour puis
Vulnérabilité +50% pendant 3 tours subit +70% de dégâts tant que les deux sont actifs). Chaque
debuff décompte sa propre durée indépendamment des autres et disparaît de la liste dès qu'elle
atteint 0 (dans l'exemple, après le premier tour ennemi il ne reste que le +50% pour 2 tours).

Affichage (UI) : les debuffs actifs d'un ennemi apparaissent dans son infobulle (un par ligne, avec
sa magnitude et ses tours restants), et une pastille orange au-dessus de sa case affiche le nombre
de debuffs actifs — absente si aucun debuff n'est actif.

**Cartes Buff** : renforcent un module allié, sur le même modèle que les cartes Debuff (liste de
buffs actifs indépendants sur `Module.buffs_actifs`, magnitudes cumulées tant qu'ils sont actifs) :
- `BOUCLIER_PAR_TOUR` : donne du Bouclier au module, une première fois immédiatement à la pose de la
  carte (comme les autres types de carte), puis à nouveau à chaque début de tour joueur tant que le
  buff reste actif

Un buff peut avoir une durée limitée (`duree`, décomptée à chaque début de tour joueur suivant la
pose) ou être **persistant** (`duree` absente/nulle) : il ne décompte alors jamais et dure tout le
combat. Un buff persistant cible toujours le **module principal** (`CibleCarte.MODULE_PRINCIPAL`,
pas de clic requis) plutôt qu'un module au choix du joueur : c'est le seul module dont la survie
est garantie tout le combat (§3.4), donc le seul endroit où un effet censé durer jusqu'à la fin a du
sens — décision explicite qui déroge à la cible "Module Unique" du tableau de conception d'origine,
cf. `cible_design` dans `config/cartes.json` (même principe que la correction des cartes Soute,
§12.11 de specs.md). *Bouclier perpétuel* (Blindage, Légendaire) est persistant : `+10` Bouclier au
module principal, immédiatement puis à chaque tour joueur, jusqu'à la fin du combat.

Affichage (UI) : les buffs actifs d'un module apparaissent dans son infobulle, groupés en deux
sections **séparées** (jamais mélangées) — d'abord ceux à durée limitée, puis ceux persistants (avec
un séparateur "Persistants :" si les deux groupes sont non vides) — et **deux pastilles distinctes**
au-dessus de sa case affichent chacune leur propre compte (dorée pour les buffs à durée limitée,
violette pour les persistants), jamais additionnées dans une seule pastille ; chacune absente si son
compte est à 0 (même principe que la pastille des debuffs ennemis, couleurs différentes pour
distinguer les trois d'un coup d'œil).

**Munitions** (specs.md §3.6/§7.4) : une carte peut avoir un nombre de munitions limité en plus de
son coût. Chaque utilisation le décrémente ; à 0, l'exemplaire rejoint la pile **cartes épuisées**
(distincte de la pioche/défausse, jamais remélangée pendant le combat) au lieu de la défausse. Le
compteur est propre à chaque exemplaire physique dans le deck, et se réinitialise à chaque nouveau
combat (le deck est reconstitué à zéro, cf. §5). Une carte à munitions illimitées (la majorité) n'est
pas concernée.

Une carte est associée à un ou plusieurs modules dans `config/modules.json` (qui peuvent la piocher
dans leur deck, cf. §5), mais **son effet ne dépend jamais du module dont elle provient** : une fois
dans le deck, elle est jouable sur n'importe quelle cible valide, comme les autres.

Le Bouclier absorbe les dégâts subis avant les PV. Exemple : un module protégé par 5 Bouclier subit une attaque de 7 dégâts → le Bouclier absorbe 5, les **2 dégâts restants** sont retirés des PV.

---

## 5. Composition du deck

**24 cartes à chaque combat** :
- **Deck de base du module Principal (12 cartes, fixe, pas de tirage aléatoire)** : chacune de ses
  cartes de rareté Base une fois, sauf Laser et Bouclier qui en comptent 4 exemplaires chacune
  (règle donnée explicitement par l'utilisateur, pas un choix du moteur)
- **3 cartes tirées au sort** (avec remise) parmi les cartes jouables par **chacun** des 4 modules
  équipés (4 x 3 = 12) — règle intérimaire : la règle cible de specs.md §2.1/§6 (2 Communes + 1 Rare
  + 1 Légendaire par module équipé) demande qu'aucun module équipable n'ait de pool vide à un palier
  de rareté donné, ce qui n'est pas encore le cas pour tous les modules (voir specs.md §12) ; en
  attendant, un tirage uniforme dans les cartes jouables du module (aujourd'hui une seule carte
  Commune par module) en tient lieu

Une fois tirée, une carte perd tout lien avec le module qui l'a fournie (§4) : le deck n'est qu'une liste de 24 cartes, indifférenciées par leur origine. Chaque tirage crée un **exemplaire indépendant** (pas une référence partagée) : deux copies de la même carte ont chacune leur propre compteur de munitions.

---

## 6. Déroulé d'un tour

1. **Tour du joueur** : le joueur pioche 5 cartes, l'électricité est remise à 3. Le joueur joue librement les cartes de son choix (en choisissant la cible parmi les modules/ennemis vivants — ou sans cible à choisir pour les cartes "Alliés multiples"/"Ennemis multiples", cf. §4), dans l'ordre qu'il veut, tant qu'il a assez d'électricité (voir specs.md §3.3), puis clique sur le bouton **"Fin de tour"** pour passer la main. Chaque carte jouée affiche un popup `+N`/`-N` sur sa ou ses cibles (voir §8)
2. **Fin du tour joueur** : les cartes non jouées restant en main sont défaussées (voir specs.md §3.3)
3. **Tour de l'ennemi** : chaque ennemi vivant attaque automatiquement le module qu'il vise (règle de ciblage en §3), dans l'ordre de la grille. Un popup `-N` apparaît sur chaque module touché (voir §8). Si la base est détruite en cours de tour, les ennemis suivants n'agissent plus (la run est terminée)

Ce cycle se répète jusqu'à la fin du combat. Le jeu se joue entièrement à la souris (voir specs.md §8.3) : clic sur une carte pour la sélectionner, clic sur la cible (module ou ennemi) pour la jouer, survol d'un ennemi pour voir son intention, clic sur "Fin de tour" pour passer la main.

---

## 7. Fin de combat

- **Victoire** : tous les ennemis sont détruits
- **Défaite** : le module de base atteint 0 PV (cf. specs.md §3.4 : la destruction du module de base termine la run — la destruction d'un autre module n'y met pas fin)
- À la fin du combat, un message fixe ("Victoire" ou "Défaite") s'affiche à l'écran et le combat se fige (plus aucune interaction possible)
- Un module ou un ennemi détruit reste affiché en grisé avec la mention "Détruit" (la grille garde sa forme), plutôt que de disparaître

---

## 8. Implémentation

Stack et arborescence définies en specs.md §10. Pour ce POC :

```
assets/
  cartes/      → images des cartes
  modules/     → images des modules
  ennemis/     → images des ennemis
config/        → fichiers de donnees JSON (modules, ennemis, cartes) - voir ci-dessous
src/
  ui/          → affichage pyglet de l'écran de combat (§8 de specs.md)
  gameplay/    → logique du combat (grille, cartes, PV, Bouclier, ciblage, tour de jeu)
tests/         → tests unitaires pytest
index.html, web/ → version web/iPhone du meme POC (voir README.md/CLAUDE.md)
```

Ce même POC est aussi jouable dans un navigateur (voir `README.md`) : `web/bridge.py` exécute
`src/gameplay/` tel quel via Pyodide, avec un affichage HTML/CSS/JS volontairement simplifié par
rapport à ce qui suit (pas d'infobulle au survol, pas de pastilles PV/Bouclier positionnées à
l'identique...). Les règles ci-dessous décrivent la version de référence (pyglet) ; les écarts de la
version web sont documentés dans les commentaires de `web/app.js`/`web/style.css`, pas ici.

Le rendu utilise les vraies images d'`assets/` (module/ennemi/carte affichés comme des sprites). Cartes, ennemis et le module de base sont mis à l'échelle **sans déformation** dans leur case (ratio préservé). Exception volontaire : les **modules équipés** sur le vaisseau sont **étirés** (largeur et hauteur mises à l'échelle indépendamment) pour que leur propre cadre décoratif recouvre exactement le cadre correspondant sur l'image du vaisseau, plutôt que de laisser un espace vide entre les deux cadres — une légère déformation de l'image est jugée préférable à ce défaut visuel. Un bandeau semi-transparent reste utilisé pour le nom/coût des cartes et pour la mention "Détruit" ; en revanche les PV et le Bouclier ne sont plus affichés dans un bandeau mais par des **pastilles** rondes (rouge pour les PV, bleue pour le Bouclier) flottant juste au-dessus de chaque case, jamais par-dessus l'image (pour ne pas la cacher).

**Disposition générale** (rapprochée de la version web, cf. `web/style.css`) : une image de fond
(`assets/fond.PNG`) remplit toute la fenêtre, étirée pour s'adapter à sa taille (une légère
déformation est acceptée plutôt que de laisser des bandes vides). Un bandeau en haut de l'écran
regroupe l'électricité disponible (à gauche) et le bouton "Fin de tour" (à droite), comme l'en-tête
de la version web. Le bloc vaisseau + flotte ennemie est centré horizontalement dans la fenêtre
(marges égales des deux côtés), et la main de cartes est centrée en bas de l'écran plutôt qu'alignée
à une position fixe.

Chaque carte de la main affiche aussi (specs.md §8.2) :
- Une **étoile de rareté** en haut à gauche, colorée par palier : blanche (Base), verte (Commune),
  bleue (Rare), orange (Légendaire)
- Une **pastille verte** avec le nombre de munitions restantes, en haut à droite de la carte
  (uniquement pour les cartes à munitions limitées ; rien pour les munitions illimitées)

Conventions : classes claires par responsabilité, commentaires en français sans accents ni cédilles (cf. specs.md §10.3).

### Mode test

`MODE_TEST` (`src/gameplay/config_poc.py`) est une variable booléenne, **actuellement `True`**, qui
remplace la génération aléatoire normale du combat par une configuration pensée pour les tests
manuels des mécaniques de cartes plutôt que pour le gameplay réel :
- Tous les modules du joueur et tous les ennemis ont **200 PV** (`PV_MODULE_MODE_TEST`/
  `PV_ENNEMI_MODE_TEST`), pour survivre de nombreux tours sans mourir. Les modules équipés restent
  tirés au sort normalement (seuls leurs PV changent).
- Le deck contient **un exemplaire de chaque carte jouable existante** (`creer_deck_mode_test()`),
  quels que soient les modules tirés au sort, plutôt que le tirage aléatoire habituel par module
  équipé — pour pouvoir essayer toutes les mécaniques en un seul combat.

`creer_combat_poc()` lit cette variable directement : aucun changement nécessaire côté PC
(`FenetreCombat()`) ni web (`web/bridge.py`), les deux appellent cette fonction sans paramètre
dédié. Remettre `MODE_TEST` à `False` restaure le comportement normal (production) décrit dans le
reste de cette section et dans specs.md §2/§6.

### Vaisseau du joueur : emplacements mesurés sur l'image

Le module de base (`assets/modules/principal.png`) est affiché en grand ; les 4 modules équipés se positionnent dans les emplacements vides visibles sur cette image, mesurés directement dessus (coordonnées du cadre métallique complet de chaque emplacement, pas seulement du trou noir intérieur, pour que le cadre du module vienne bien recouvrir celui du vaisseau une fois étiré comme décrit ci-dessus). Les pastilles PV/Bouclier de la base sont positionnées au-dessus du pare-brise du vaisseau (repère mesuré sur l'image), plutôt qu'au hasard au-dessus de toute l'image.

### Retour visuel des effets (popups +/-N)

Chaque effet résolu — carte jouée par le joueur ou attaque ennemie — affiche un popup pendant 2 secondes sur la ou les cases touchées, puis disparaît :
- Dégâts (carte d'attaque ou attaque ennemie) : `-N` en rouge
- Bouclier posé (carte de défense) : `+N` en bleu
- Réparation (carte de réparation) : `+N` en vert
- Debuff (carte Debuff) : `-N` (réduction de dégâts) ou `+N%` (vulnérabilité), en orange
- Buff (carte Buff) : `+N`, en doré

`N` est le montant **réellement appliqué**, pas la valeur nominale de la carte : les dégâts sont plafonnés par les PV + Bouclier restants de la cible, la réparation par son PV max (le Bouclier, lui, n'est jamais plafonné, cf. §4). Une carte à cibles multiples (Alliés multiples, Ennemis multiples, Ligne ennemie, Colonne avant/arrière ennemie) affiche un popup indépendant sur chacune de ses cibles. Une carte Outils ne touche aucun module/ennemi : elle n'affiche pas de popup.

Il n'y a pas d'animation de rayon entre l'attaquant et sa cible : ce retour par popup a été préféré, plus lisible quand plusieurs attaques se résolvent au même tour.

Ce popup +/-N reste ancré sur la case touchée, comme sur la version web — contrairement à
l'infobulle de survol/tap (module, ennemi, ou carte sélectionnée) qui, elle, est centrée à l'écran
sur la version web (`#info-carte`/`#info-case`) mais reste ancrée au-dessus de sa case sur pc :
différence assumée entre les deux versions, pas à unifier.

### Survol de la souris (infobulle)

Survoler un module (du joueur) ou un ennemi vivant avec la souris affiche une infobulle au-dessus de sa case :
- **Module** : nom, PV/PV max, Bouclier
- **Ennemi** : nom, PV/PV max, et son intention — quel module il vise et les dégâts qu'il infligerait s'il attaquait maintenant, calculés avec la même fonction de ciblage que celle utilisée pour la résolution réelle de l'attaque (pas de logique dupliquée), donc toujours cohérent avec ce qui va effectivement se passer.

### Fichiers de configuration (`config/`)

Trois fichiers JSON décrivent le contenu du jeu (modules, ennemis, cartes) de façon déclarative, référençant les images de `assets/`. **Chargés par le moteur** (`src/gameplay/donnees.py`) à chaque combat : `config_poc.py` s'en sert pour tirer au sort le vaisseau, la flotte et le deck (§2-3-5).

**`config/modules.json`** — un module par entrée :
- `id` : identifiant unique, format `MOD_N`
- `nom`, `image` (chemin vers `assets/modules/`)
- `points_de_vie`
- `cartes` : liste d'identifiants de cartes (`CRT_N`) que ce module peut jouer

**`config/ennemis.json`** — un ennemi par entrée :
- `id` : identifiant unique, format `ENM_N`
- `nom`, `image` (chemin vers `assets/ennemis/`)
- `points_de_vie`
- `action` : une chaîne `TYPE,valeur,cible` décrivant ce que l'ennemi fait à son tour
  - `TYPE` : `ATK` (attaque) ou `REPARATION` (soin) — mêmes types que les cartes (§4), d'autres pourront s'ajouter ; seul `ATK` est interprété par `donnees.charger_ennemis()` pour l'instant, les autres sont ignorés
  - `valeur` : dégâts infligés ou PV réparés
  - `cible` : toujours `AUTO` pour l'instant — délègue au ciblage automatique déjà implémenté (§3 : propre rangée d'abord, repli sur la plus proche). Prévu pour accueillir d'autres modes plus tard si besoin (ex. cible aléatoire, PV le plus bas)

**`config/cartes.json`** — une carte par entrée. Le fichier contient en réalité 38 cartes (tout le
tableau de conception fourni par l'utilisateur), mais seules celles avec un bloc `effet` sont
jouables (`donnees.charger_cartes()` ignore silencieusement les autres, cf. specs.md §12) :
- `id` : identifiant unique, format `CRT_N`
- `nom`, `image` (chemin vers `assets/cartes/`)
- `cout` (en électricité)
- `rarete` : `Base` / `Commune` / `Rare` / `Legendaire` (specs.md §7.3)
- `munition` : nombre de munitions (absent/`null` = illimitées, cf. §4)
- `effet` (absent = carte non jouable) : objet `{ type, cible, valeur, action?, duree? }` où `type`
  et `cible` reprennent les valeurs de specs.md §7.1/§7.2 :
  - `type` : `ATTAQUE` / `DEFENSE` / `REPARATION` / `OUTILS` / `DEBUFF` / `BUFF`
  - `cible` : `ALLIE_UNIQUE` / `ALLIES_MULTIPLES` / `ENNEMI_UNIQUE` / `ENNEMIS_MULTIPLES` /
    `LIGNE_ENNEMIE` (touche l'avant et l'arrière de la rangée visée, soit 2 ennemis) /
    `MODULE_PRINCIPAL` (toujours le module de base, pas de clic) / `COLONNE_AVANT_ENNEMIE` /
    `COLONNE_ARRIERE_ENNEMIE` (toute la colonne visée par la carte, fixe — 3 ennemis au plus ;
    contrairement à `LIGNE_ENNEMIE`, le clic doit tomber dans cette colonne precise) /
    `COLONNE_AVANT_ALLIEE` (les 2 modules avant-gauche/avant-droite, jamais le module principal ;
    même principe que les colonnes ennemies)
  - `action` (pour `type: DEFENSE`, `OUTILS`, `DEBUFF` ou `BUFF`) : `BOUCLIER_POURCENTAGE_PV`
    (Defense — bouclier = X% des PV max de la cible plutôt qu'un montant fixe, cf. §12.4),
    `ANNULATION_PROCHAINE_ATTAQUE` (Defense — annule totalement la toute prochaine attaque reçue
    par la cible puis se consomme, cf. §12.6), `GAIN_ELECTRICITE` / `GAIN_ELECTRICITE_PAR_MODULE`
    (gain fixe, ou X par module allié encore en vie, base incluse) / `PIOCHE_SUPPLEMENTAIRE`
    (Outils), `REDUCTION_DEGATS` / `VULNERABILITE` / `REDIRECTION_CIBLE` (Debuff), ou
    `BOUCLIER_PAR_TOUR` (Buff) — précise l'effet exact, chaque carte étant un mécanisme différent
    (specs.md §12.4/§12.6/§12.8/§12.9/§12.1/§12.5)
  - `duree` (pour `type: DEBUFF` ou `BUFF`) : nombre de tours pendant lesquels l'effet reste actif,
    décrémenté à chaque tour ennemi écoulé (Debuff) ou chaque tour joueur écoulé (Buff), même si
    l'ennemi/le module concerné n'a pas agi ; absente/`null` pour un Buff **persistant** (ne
    décompte jamais, dure tout le combat — cf. *Bouclier perpétuel*)

Les 23 cartes actuellement jouables : les 6 du module Principal (Laser, Laser perçant,
Bombardement, Bouclier, Protéger le vaisseau, Réparation), Ciel de missiles, Ligne arrière et
Leurre (Lanceur de missiles), Mode défensif, Bouclier perpétuel, Protéger l'avant poste, Bouclier
adaptatif et Blindage maximal (Blindage), Surcharge temporaire et Fonds de tiroir (Générateur),
Boost (Soute), et les 6 cartes de Sabotage (Tordre le canon, Brèche, Ligne avant, Boucliers
endommagés, Boucliers hors service, Tir allié) — le module Sabotage est entièrement jouable, le
module Blindage l'est presque (5 cartes sur 7, restent Transfert et Renvoie, specs.md §12.6). Les 15
autres cartes du tableau restent stockées pour référence, non jouables faute de mécanique (specs.md
§12).

**Toutes les valeurs (PV, dégâts, coûts, munitions) viennent du tableau de conception fourni par
l'utilisateur**, sauf les PV des modules Générateur et Soute (10 chacun) qui restent **inventés**
faute de valeur donnée, comme le reste des données numériques de ce POC (§1).
