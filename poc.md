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
- **4 modules différents** sont tirés au sort parmi les 5 autres (Laser, Missiles, Mitrailleuse, Bouclier, Soin) et placés aléatoirement sur les 4 cases équipables — un des 5 modules ne sera donc **pas** du tout présent dans le combat
- PV et cartes jouables de chaque module : voir `config/modules.json`

- **Électricité** : 3 par tour (ressource pleine à chaque début de tour, ne se cumule pas d'un tour à l'autre)
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

Chaque attaque résolue affiche un popup `-N` (dégâts réellement infligés, voir §8) sur le module touché. Au survol de la souris sur un ennemi vivant, une infobulle affiche la cible qu'il vise et les dégâts qu'il infligerait ce tour, calculés avec la même règle (voir §8).

---

## 4. Cartes

6 cartes définies dans `config/cartes.json` (Attaquer, Mitrailler, Percer, Défendre, Protéger, Soigner), chacune avec un type, un coût et une cible parmi :

| Cible | Comportement au clic |
|---|---|
| **Ennemi unique** | Sélectionner la carte, puis cliquer un ennemi vivant |
| **Allié unique** | Sélectionner la carte, puis cliquer un module vivant |
| **Ligne ennemie** | Sélectionner la carte, puis cliquer un ennemi vivant — touche aussi l'autre case (Avant ↔ Arrière) de la **même rangée**, si elle est occupée |
| **Alliés multiples** | Se résout **dès la sélection** de la carte (pas de clic de ciblage) — touche tous les modules vivants du joueur |
| **Ennemis multiples** | Se résout **dès la sélection** de la carte (pas de clic de ciblage) — touche tous les ennemis vivants |

Une carte est associée à un ou plusieurs modules dans `config/modules.json` (qui peuvent la piocher dans leur deck, cf. §5), mais **son effet ne dépend jamais du module dont elle provient** : une fois dans le deck, elle est jouable sur n'importe quelle cible valide, comme les autres.

Le Bouclier absorbe les dégâts subis avant les PV. Exemple : un module protégé par 5 Bouclier subit une attaque de 7 dégâts → le Bouclier absorbe 5, les **2 dégâts restants** sont retirés des PV.

---

## 5. Composition du deck

**20 cartes tirées au sort à chaque combat**, à partir des jeux de cartes des modules retenus (§2) :
- **8 cartes** tirées au sort (avec remise) parmi les cartes jouables par le module **Principal**
- **3 cartes** tirées au sort (avec remise) parmi les cartes jouables par **chacun** des 4 modules équipés (4 x 3 = 12)

Une fois tirée, une carte perd tout lien avec le module qui l'a fournie (§4) : le deck n'est qu'une liste de 20 cartes, indifférenciées par leur origine.

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
```

Le rendu utilise les vraies images d'`assets/` (module/ennemi/carte affichés comme des sprites). Cartes, ennemis et le module de base sont mis à l'échelle **sans déformation** dans leur case (ratio préservé). Exception volontaire : les **modules équipés** sur le vaisseau sont **étirés** (largeur et hauteur mises à l'échelle indépendamment) pour que leur propre cadre décoratif recouvre exactement le cadre correspondant sur l'image du vaisseau, plutôt que de laisser un espace vide entre les deux cadres — une légère déformation de l'image est jugée préférable à ce défaut visuel. Un bandeau semi-transparent reste utilisé pour le nom/coût des cartes et pour la mention "Détruit" ; en revanche les PV et le Bouclier ne sont plus affichés dans un bandeau mais par des **pastilles** rondes (rouge pour les PV, bleue pour le Bouclier) flottant juste au-dessus de chaque case, jamais par-dessus l'image (pour ne pas la cacher).

Conventions : classes claires par responsabilité, commentaires en français sans accents ni cédilles (cf. specs.md §10.3).

### Vaisseau du joueur : emplacements mesurés sur l'image

Le module de base (`assets/modules/principal.png`) est affiché en grand ; les 4 modules équipés se positionnent dans les emplacements vides visibles sur cette image, mesurés directement dessus (coordonnées du cadre métallique complet de chaque emplacement, pas seulement du trou noir intérieur, pour que le cadre du module vienne bien recouvrir celui du vaisseau une fois étiré comme décrit ci-dessus). Les pastilles PV/Bouclier de la base sont positionnées au-dessus du pare-brise du vaisseau (repère mesuré sur l'image), plutôt qu'au hasard au-dessus de toute l'image.

### Retour visuel des effets (popups +/-N)

Chaque effet résolu — carte jouée par le joueur ou attaque ennemie — affiche un popup pendant 2 secondes sur la ou les cases touchées, puis disparaît :
- Dégâts (carte d'attaque ou attaque ennemie) : `-N` en rouge
- Bouclier posé (carte de défense) : `+N` en bleu
- Soin (carte de soin) : `+N` en vert

`N` est le montant **réellement appliqué**, pas la valeur nominale de la carte : les dégâts sont plafonnés par les PV + Bouclier restants de la cible, le soin par son PV max (le Bouclier, lui, n'est jamais plafonné, cf. §4). Une carte à cibles multiples (Alliés multiples, Ennemis multiples, Ligne ennemie) affiche un popup indépendant sur chacune de ses cibles.

Il n'y a pas d'animation de rayon entre l'attaquant et sa cible : ce retour par popup a été préféré, plus lisible quand plusieurs attaques se résolvent au même tour.

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
  - `TYPE` : `ATK` (attaque) ou `SOIN` (soin) — mêmes types que les cartes (§4), d'autres pourront s'ajouter
  - `valeur` : dégâts infligés ou PV réparés
  - `cible` : toujours `AUTO` pour l'instant — délègue au ciblage automatique déjà implémenté (§3 : propre rangée d'abord, repli sur la plus proche). Prévu pour accueillir d'autres modes plus tard si besoin (ex. cible aléatoire, PV le plus bas)

**`config/cartes.json`** — une carte par entrée :
- `id` : identifiant unique, format `CRT_N`
- `nom`, `image` (chemin vers `assets/cartes/`)
- `cout` (en électricité)
- `effet` : objet `{ type, cible, valeur }` où `type` et `cible` reprennent les valeurs de specs.md §7.1/§7.2 :
  - `type` : `ATTAQUE` / `DEFENSE` / `SOIN`
  - `cible` : `ALLIE_UNIQUE` / `ALLIES_MULTIPLES` / `ENNEMI_UNIQUE` / `ENNEMIS_MULTIPLES` / **`LIGNE_ENNEMIE`** (nouveau : touche l'avant et l'arrière de la rangée visée, soit 2 ennemis — pour les cartes perçantes de specs.md §3.1, ex. Percer)

Les 6 cartes actuelles couvrent les 6 images disponibles : Attaquer (cible unique), Mitrailler (dégâts répartis sur plusieurs ennemis), Percer (perçant, toute la rangée visée), Défendre (Bouclier sur un allié au choix), Protéger (Bouclier sur tous les alliés), Soigner (PV sur un allié au choix). Les modules leur sont associés par thème (ex. Bouclier → Défendre/Protéger, Soin → Protéger/Soigner) — répartition à ajuster librement, ce n'est qu'une première proposition.

**Toutes les valeurs (PV, dégâts, coûts) sont inventées**, comme le reste des données numériques de ce POC (§1).
