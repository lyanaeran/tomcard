# Space Fight — Combat et ennemis (§3 et §13)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md). Décrit le moteur actuel (`src/gameplay/combat.py`, `statut.py`,
`ennemi.py`, `flotte.py`, `vaisseau.py`, `deck.py`), issu de la refonte de novembre 2026 : les
brouillons `refonte-combat.md`, `refonte-statuts.md` et `refonte-ennemis.md` ont été reportés ici
le 2026-11-14, puis supprimés.*

---

## 3. Système de combat

### 3.1 Placement / rangs

#### 3.1.1 Vocabulaire de la grille (décision utilisateur, 2026-11-21)

**On décrit toujours la grille du point de vue du camp concerné**, pas de l'écran. Chaque camp
(joueur, ennemi) a une grille de **2 lignes × 3 colonnes** :

- **2 lignes** : la **ligne avant** (tournée vers l'adversaire) et la **ligne arrière**. La ligne
  avant ennemie compte jusqu'à 3 ennemis, la ligne arrière aussi.
- **3 colonnes** : **gauche, milieu, droite**. Deux cases de la même colonne sont l'une
  **derrière** l'autre (une avant, une arrière).

Sur l'écran, le joueur est tourné vers la droite et les ennemis vers la gauche :

```
  écran :  [arrière joueur] [avant joueur]  →  ←  [avant ennemi] [arrière ennemi]
            tout à gauche                                         tout à droite
```

- La **ligne arrière du joueur** est **tout à gauche** de l'écran, la **ligne arrière ennemie**
  **tout à droite** ; les deux lignes avant sont au centre, face à face.
- Vues sur l'écran, les lignes sont donc des bandes **verticales** et les colonnes des bandes
  **horizontales**. Ne pas parler de « colonnes » pour l'avant et l'arrière, même si c'est ce
  qu'on voit à l'écran.

**Ancien vocabulaire encore présent** (à harmoniser) : le code (`position.py`, `combat.py`,
`flotte.py`, `vaisseau.py`, `src/ui/`, `src/web/`) et plusieurs passages de `specs/` utilisent
l'inverse, hérité de la vue écran. Correspondance :

| Vocabulaire retenu | Ancien vocabulaire (code, anciens textes) |
|---|---|
| ligne avant / ligne arrière | colonne avant / colonne arrière (`Colonne.AVANT`, `Colonne.ARRIERE`, portées `COLONNE_AVANT_ENNEMIE`…) |
| colonne gauche / milieu / droite | rangée gauche / mid / droite (`Rangee.GAUCHE`, `Rangee.MID`, `Rangee.DROITE`) |
| l'ennemi derrière la cible (même colonne) | l'ennemi de la même rangée |

Dans la suite de ce fichier et dans les autres specs, un texte qui parle de « colonne avant » ou
de « rangée du milieu » suit l'ancien vocabulaire : le lire avec ce tableau.

#### 3.1.2 Occupation de la grille

Grille de 2 lignes × 3 colonnes, côté joueur comme côté ennemi (`position.py`).

- **Joueur** (`vaisseau.py`) : le module principal occupe **toute la colonne du milieu** (ses
  deux cases, avant et arrière) ; les emplacements `avant_gauche`, `arriere_gauche`,
  `avant_droite`, `arriere_droite` (`Module.emplacement`) correspondent aux cases du même nom. Le
  principal compte donc dans les deux lignes : il est touché par une carte « Module Avant ».
- **Ennemis** (`flotte.py`) : un ennemi occupe `emplacements` cases (le Boss : une case avant et
  la case arrière juste derrière, dans la même colonne) ; c'est un **seul** ennemi.
- Le placement des modules fragiles à l'arrière est une décision tactique : une attaque ennemie
  « au plus proche » vise d'abord la ligne avant (§13.2.2).
- Idée non codée : un module dédié (Propulseur) pour repositionner en cours de combat.

### 3.2 Tailles de monstres

- Trois tailles : **S, M, L**, **purement informatives** pour l'instant (`Ennemi.taille`) : la
  composition des flottes n'en tient pas compte.
- **Nombre de cases occupées** (`Ennemi.emplacements`) : champ indépendant de la taille, 1 par
  défaut, 2 pour le Boss des pirates (taille M). C'est ce champ, jamais la taille, qui pilote
  l'occupation de la grille (décision utilisateur).
- Un ennemi sur plusieurs cases est réservé aux flottes fixes (`flotte.flotte_boss`), jamais tiré
  au hasard (`flotte.ennemis_standard` l'exclut).
- Idée d'origine, non codée : annoncer la composition avant le combat (« 2 S + 1 M ») sans le
  détail des ennemis.

### 3.3 Ressource et main de cartes

- **Électricité** : ressource commune à tout le vaisseau, remise à **3** au début de chaque tour
  du joueur (`ELECTRICITE_PAR_TOUR`).
- Le joueur joue ses cartes **librement, dans l'ordre de son choix**, puis le tour ennemi se
  déroule. Pas d'initiative par module.
- **Main** : pioche de **5** cartes par tour, main limitée à **10** (`deck.py`).
- **Cinq piles** (`Deck`) : pioche, main, défausse, **épuisées** (§3.6), **Hors service** (§3.4).
  Quand la pioche est vide, la défausse est remélangée pour la reformer ; épuisées et Hors
  service ne reviennent jamais. Si pioche et défausse sont vides, le joueur pioche moins de
  cartes (cas limite : a-trancher.md §9.1).
- **Fin de tour** : les cartes restant en main sont défaussées.
- **Deck de départ** (décision utilisateur) : Laser ×4, Bouclier ×4, Protéger le vaisseau ×1,
  Réparation ×1, tous rattachés au principal (`deck.DECK_DE_DEPART`).
- **Le deck de la partie n'est jamais modifié par un combat** : `Combat` travaille sur des copies
  des cartes, des modules et des ennemis.

### 3.4 Destruction de module

Un module à 0 PV est **détruit pour le reste du combat** (décisions utilisateur) :

1. **Toutes ses cartes non Persistantes** partent immédiatement en **pile Hors service**, où
   qu'elles soient (pioche, main, défausse), avec leurs munitions. Cette pile n'est jamais
   remélangée. Une carte **Persistante** reste jouable (modules-cartes.md §12.4).
2. Ses statuts sont perdus ; il n'est plus une cible, ni pour les ennemis, ni pour les cartes.
3. **Principal détruit** : **défaite** immédiate.
4. **Un secondaire détruit n'est pas une perte permanente** : il repart à ses PV max au combat
   suivant (`Module.copie_pour_combat`). Seuls les **PV du principal** persistent d'un combat à
   l'autre (`Module.reporter_combat`) ; ils se réparent à la Station service ou par une Aventure
   (parcours.md §2.2, aventures.md §2.5).
5. Une carte dont le module meurt pendant qu'elle est jouée (dégâts renvoyés) part en Hors service
   une fois jouée, sauf si elle est épuisée ou Persistante.

Pistes non codées (effet à la destruction, résurrection, sacrifice volontaire) :
[refonte-destruction.md](refonte-destruction.md).

### 3.5 Statuts (bouclier, incendie, renvoi, leurre)

Bouclier, incendie, renvoi et leurre sont gérés **ensemble**, de la même façon pour les
**modules** et les **ennemis** (décision utilisateur, 2026-11-11 ; `statut.py`, classe `Statuts`).

- Chaque entité en combat porte ses statuts : **statut → intensité** (`{BOUCLIER: 6,
  INCENDIE: 3}`) ; un statut absent vaut 0, une intensité tombée à 0 est retirée.
- Chaque statut **déclare sa règle** (cumul et extinction) ; le code applique la règle.

| Statut | Cumul (nouvelle pose) | Extinction | Effet |
|---|---|---|---|
| **Bouclier** | Addition | −1 par tour | Absorbe les dégâts avant les PV (5 de bouclier, attaque de 7 : 2 PV perdus) |
| **Incendie** | Addition | −1 par tour | Inflige son intensité en dégâts à la fin du tour, avant la baisse |
| **Renvoi** | Addition | Tour suivant (disparaît entièrement) | Renvoie à l'attaquant les dégâts reçus jusqu'à son intensité, qui diminue d'autant ; l'entité encaisse le reste |
| **Leurre** | Remplacement (non cumulable) | Consommation | Annule entièrement la prochaine attaque reçue, puis disparaît |

Le renvoi n'est posé que par l'ennemi Miroir pour l'instant (§13.3).

#### 3.5.1 Attaque reçue

1. **Leurre** : s'il est présent, l'attaque est entièrement annulée et le leurre disparaît.
2. **Renvoi** : il prend les dégâts jusqu'à son intensité restante ; ces dégâts sont renvoyés à
   l'attaquant (§3.8.5).
3. **Bouclier** : il absorbe ce qui reste.
4. Le reste est retiré des **PV**.

#### 3.5.2 Fin de tour

À la **fin du tour de l'adversaire** de l'entité (décision utilisateur) : fin du tour du joueur
pour un ennemi, fin du tour ennemi pour un module.

1. **L'incendie frappe** de son intensité, **absorbé par le bouclier** (jamais renvoyé ni annulé
   par le leurre).
2. Chaque statut **s'éteint selon sa règle** : bouclier et incendie −1, renvoi retiré, leurre
   inchangé.

#### 3.5.3 Lien avec les cartes

Une seule source pour les règles : chaque nature d'effet de carte qui pose un statut le désigne
(`NatureEffet.statut_pose`) : `BOUCLIER` → Bouclier, `INCENDIE` → Incendie,
`ANNULATION_PROCHAINE_ATTAQUE` → Leurre (modules-cartes.md §12.2).

**Décidé, pas encore codé** : le statut **Surcharge** (+intensité aux dégâts de chaque coup,
−1 par tour, porté par le principal pour toutes les cartes, et par les ennemis) :
[effets-a-coder.md](effets-a-coder.md) §1.

**Points ouverts** : les statuts à durée (Vulnérabilité, Réduction de dégâts : une intensité et un
nombre de tours) ne sont pas codés ; le buff Destruction portera des effets, pas un nombre, et
aura son propre champ ([refonte-destruction.md](refonte-destruction.md)).

### 3.6 Munitions (cartes à usage limité)

Certaines cartes ont un nombre de munitions limité en plus de leur coût (modules-cartes.md §7.4) :

- **Illimitées** (cas par défaut) : la carte se joue autant de fois que l'électricité le permet.
- **Limitées à N** : chaque carte jouée consomme **une munition, quel que soit le nombre de
  lancements** (décision utilisateur). Le compteur est **propre à chaque exemplaire** de la carte.
- À **0**, l'exemplaire part dans les **cartes épuisées** au lieu de la défausse et ne revient
  plus du combat, même si pioche et défausse sont vides.
- **Entre deux combats**, chaque carte repart avec ses munitions d'origine.

### 3.7 Déroulement d'un tour

Le **numéro de tour** est tenu par le combat : 1 au début, +1 au début de chaque tour du joueur à
partir du tour 2. Il sert à lire les valeurs des ennemis (§13.1.3).

1. **Début du combat** : le deck est mélangé pour former la pioche ; tour 1.
2. **Début du tour du joueur** : électricité à 3, pioche de 5 cartes.
3. **Jeu** : le joueur joue les cartes qu'il veut (§3.8).
4. **Fin du tour du joueur** (`finir_tour`) : la main est défaussée, puis **fin de tour de chaque
   ennemi vivant** (§3.5.2 : incendie, puis extinction des statuts). Si tous les ennemis sont
   détruits : victoire.
5. **Tour ennemi** (§13.2) : chaque ennemi vivant joue son étape. Après chaque coup, un module à
   0 PV est détruit (§3.4) ; si c'est le principal, défaite immédiate.
6. **Fin du tour ennemi** : fin de tour de chaque module vivant (§3.5.2). Un module détruit par
   l'incendie l'est comme au point 5.
7. Retour au point 2, tour suivant.

### 3.8 Jouer une carte

#### 3.8.1 Conditions

Une carte peut être jouée si elle est **en main**, si l'électricité suffit, si le moteur sait
exécuter tous ses effets et si elle a au moins une **case valide** (`Combat.peut_jouer`).
`jouer_carte` refuse toute autre action (erreur explicite). Le flux de clics est décrit dans
interface.md §8.3.

#### 3.8.2 Cible de la carte (`CibleCarte`)

La cible d'une carte est une **case** (`jouer_carte(carte, case)` ; `cibles_possibles` renvoie
des cases).

| Cible | Case à choisir | Ce qui est touché |
|---|---|---|
| Ennemi Unique | un ennemi vivant | cet ennemi |
| Ennemi Colonne | un ennemi vivant | les ennemis vivants de la colonne de la case |
| Ennemi Avant / Arrière | un ennemi vivant de cette colonne | les ennemis vivants de la colonne avant / arrière |
| Ennemi Tous | un ennemi vivant | tous les ennemis vivants |
| Module Unique | un module vivant | ce module |
| Module Principal | le principal | le principal |
| Module Avant | un module vivant de la colonne avant | les modules vivants de la colonne avant |
| Module Tous | un module vivant | tous les modules vivants |

Un ennemi sur 2 cases n'est touché **qu'une fois par effet** ; une carte à deux effets (Torpille :
colonne avant puis colonne arrière) le touche une fois par effet.

#### 3.8.3 Résolution

1. L'électricité est payée **une fois**.
2. La carte est **lancée `lancements_actuels` fois** ; à chaque lancement, **tous** ses effets
   s'appliquent dans l'ordre (y compris gain d'électricité, pioche, répétition). Les cibles sont
   choisies une fois pour tous les lancements ; une cible détruite ne reçoit pas les suivants.
3. Chaque effet touche, selon sa **portée** (`PorteeEffet`) : la cible de la carte, les autres
   ennemis vivants, la colonne avant ou arrière ennemie.
4. **Munitions** : §3.6. La carte part ensuite en défausse, en épuisées ou en Hors service (§3.4).
5. **Victoire ou défaite au milieu d'une carte** : les effets et lancements restants ne sont pas
   joués.

#### 3.8.4 Effets

| Nature | Effet sur chaque entité touchée |
|---|---|
| Dégâts | Une attaque de la valeur (§3.5.1) ; les dégâts renvoyés partent vers un module (§3.8.5) |
| Bouclier, Incendie, Leurre | Pose du statut, selon sa règle de cumul (§3.5) |
| Réparation | Rend des PV de combat, sans dépasser le PV max ; jamais sur un module détruit |
| Gain d'électricité | Électricité en plus pour ce tour |
| Pioche | Pioche de cartes en plus (main limitée à 10) |
| Répétition | Augmente les lancements des cartes visées, dans **toutes** les piles, jusqu'à la fin du combat |

Chaque lancement et chaque cible sont des **attaques distinctes** : un Laser lancé 2 fois sur un
ennemi protégé par un renvoi de 5 renvoie d'abord 5, puis plus rien.

**Natures laissées pour plus tard** (décision utilisateur) : Vulnérabilité, Réduction de dégâts,
Tir allié (`REDIRECTION_CIBLE`). Une carte qui en porte n'est pas jouable.

#### 3.8.5 Dégâts renvoyés (décision utilisateur)

Quand le joueur frappe un ennemi qui porte un **renvoi**, les dégâts renvoyés vont au **module
auquel la carte jouée est rattachée** : le joueur sait d'avance quel module il expose.

- Le renvoi diminue d'autant à chaque coup renvoyé : avec un renvoi de 5, un coup de 5 est
  entièrement renvoyé et le renvoi tombe à 0.
- Les dégâts renvoyés sont une **attaque** sur ce module : son leurre l'annule, son bouclier
  l'absorbe. Ils ne sont jamais renvoyés à leur tour.
- Si ce module est déjà détruit (carte Persistante), ils vont au **principal**.
- Un renvoi porté par un module (aucune carte ne le pose) renverrait les dégâts à l'ennemi
  attaquant.

### 3.9 Fin du combat (décision utilisateur)

- **Victoire** : tous les ennemis sont détruits (par une carte, ou par l'incendie à la fin du tour
  du joueur).
- **Défaite** : le principal est détruit. La destruction des secondaires n'est **pas** une défaite.
- Ensuite (`deroulement.conclure_combat`, parcours.md §2.4) : les PV du principal sont reportés
  dans la partie, l'Argent est gagné pour les ennemis détruits, les récompenses sont tirées.

### 3.10 API de `combat.py`

`Combat` ne contient **aucun affichage**. Il reçoit des objets déjà prêts : copies de combat des
modules, cartes rattachées à leur module, flotte, et un `random.Random` injecté.

- **Actions** : `jouer_carte(carte, case)`, `finir_tour()`.
- **Consultations** (lectures seules, chacune répond à une question de règle, pour que `src/ui` et
  `src/web/` n'en recalculent aucune) :
  - état : tour, électricité, piles, PV et statuts, combat en cours / gagné / perdu ;
  - `peut_jouer(carte)`, `cibles_possibles(carte)` ;
  - `intentions()` (§13.2.3) et `modules_vises(effet)` ;
  - `journal` : des événements typés (`NatureEvenement`), sans texte : début de tour, carte jouée,
    attaque, renvoi, statut posé, réparation, incendie, électricité, pioche, répétition,
    destruction, cartes hors service, victoire, défaite. Pour des dégâts : qui attaque qui, les
    dégâts reçus, la part **annulée par le leurre**, **renvoyée**, **absorbée par le bouclier**,
    les **PV perdus** et les **PV restants**. L'affichage le met en phrases (interface.md §8.1).

---

## 13. Ennemis

Les ennemis sont gérés **en dehors des cartes** (décision utilisateur) : `ennemi.py:Ennemi`,
données dans `config/ennemis.json` (source de vérité), tableau lisible **généré**
`config/ennemis.md` (`python -m outils.tableau_ennemis`).

### 13.1 Modèle (décisions utilisateur, 2026-11-08)

#### 13.1.1 Un cycle d'actions

Chaque ennemi a une **liste d'étapes** jouée dans l'ordre, une par tour ennemi ; arrivé au bout,
il repart à la première. **Une étape = une liste d'effets** joués le même tour (le Boss attaque et
se protège dans la même étape). Un effet peut avoir un **nombre de répétitions** (Le nettoyeur
attaque 2 fois).

#### 13.1.2 Des valeurs nommées

Les effets renvoient à des **valeurs nommées** de l'ennemi, comme les effets des cartes :
`{"degats": 6, "bouclier": 5}`.

#### 13.1.3 Chaque valeur peut augmenter avec le temps

Chaque valeur a une **augmentation** et un **rythme** (« +1 tous les 3 tours »). L'augmentation
s'applique au début du tour du joueur, à partir du tour 2 : l'intention affichée en tient compte.

```
valeur(tour) = arrondi_inferieur( (base + augmentation × paliers) × coefficient )
paliers      = (tour - 1) // tous_les
```

Exemple : dégâts 6, +1 tous les 2 tours, coefficient 1,5 → 9, 9, 10, 10, 12 aux tours 1 à 5.

#### 13.1.4 Un coefficient de difficulté

À la création d'un ennemi de combat (`Ennemi.pour_combat(coefficient)`), un **coefficient ≥ 1**
multiplie toutes ses valeurs, leurs augmentations et ses **PV**, arrondis à l'inférieur. Les
rythmes ne sont jamais multipliés. Le parcours utilise pour l'instant le coefficient 1
(`flotte.COEFFICIENT_PARCOURS`).

#### 13.1.5 Format (`config/ennemis.json`)

```json
{
  "id": "ENM_PAT_LE_PIRATE",
  "nom": "Pat le Pirate",
  "pv": 50,
  "valeurs": { "degats": { "base": 5, "augmentation": 1, "tous_les": 3 } },
  "actions": [
    [ { "nature": "ATTAQUE", "valeur": "degats", "cible": "PROXIMITE" } ]
  ]
}
```

- **Natures d'effet** : `ATTAQUE`, `BOUCLIER`, `RENVOI` (les deux dernières posent le statut du
  même nom, §3.5).
- **Cibles** : `PROXIMITE`, `TOUS_MODULES` (attaques) ; `SOI_MEME`, `ALLIE_AVANT_SINON_ARRIERE`
  (bouclier, renvoi). Vérifié au chargement.
- Autres champs : `image`, `taille`, `emplacements`, `placement` (§13.4), `repetitions` sur un
  effet. Une valeur sans `augmentation` est fixe.

### 13.2 Tour ennemi

#### 13.2.1 Ordre de jeu (décision utilisateur)

Colonne avant d'abord, puis colonne arrière ; dans une colonne, rangées **droite, milieu, gauche**
(la rangée gauche est en bas de l'écran : on joue de haut en bas). Un ennemi sur 2 cases joue une
seule fois, à sa case avant. Un ennemi détruit ne joue plus.

#### 13.2.2 Effets d'une étape

| Nature | Cible | Résolution |
|---|---|---|
| Attaque | `PROXIMITE` | Le module vivant le plus proche : rangée de l'ennemi d'abord (avant puis arrière), puis les rangées voisines (`Vaisseau.module_le_plus_proche`) |
| Attaque | `TOUS_MODULES` | Chaque module vivant, une attaque chacun |
| Bouclier, Renvoi | `SOI_MEME` | L'ennemi lui-même |
| Bouclier, Renvoi | `ALLIE_AVANT_SINON_ARRIERE` | Un ennemi vivant tiré au hasard dans la colonne avant (lui-même compris), sinon dans la colonne arrière, au moment de jouer |

- **Répétitions** : la cible est choisie **une seule fois**, puis l'effet est répété sur elle. Si
  elle est détruite, les répétitions suivantes sont perdues.
- Une attaque sur un module passe par ses statuts (§3.5.1) ; ce qu'un module renverrait irait à
  l'ennemi attaquant.

#### 13.2.3 Intention

Pour chaque ennemi vivant, `Combat.intentions()` donne son **étape courante** avec les valeurs du
tour, et, pour une attaque `PROXIMITE`, le module qui serait visé si rien ne change. La cible d'un
tirage au hasard n'est pas annoncée. Affichage : interface.md §8.1.

### 13.3 Les ennemis (`config/ennemis.json`)

Valeurs à jour et détail tour par tour : `config/ennemis.md` (généré). Résumé :

| Ennemi | PV | Valeurs | Cycle |
|---|---|---|---|
| Pat le Pirate | 50 | dégâts 5 (+1 / 3 tours) | ① attaque le plus proche |
| Le nettoyeur | 25 | dégâts 7 (+1 / 3 tours) | ① attaque le plus proche ×2 |
| Petit Jean | 100 | dégâts 2 (+1 / 3 tours), bouclier 6 | ① attaque + bouclier sur soi ② attaque |
| Le puzzle | 50 | dégâts 5 (+1 / 3 tours) | ① attaque tous les modules |
| Miroir | 50 | dégâts 2 (+1 / 3 tours), renvoi 5 | ① attaque + renvoi sur un allié avant (lui-même s'il est seul) |
| Le Boss des pirates (M, 2 cases) | 150 | dégâts 5 (+2 / 3 tours), bouclier 10 | ① attaque tous ② attaque tous ③ attaque tous + bouclier sur soi |

- **Miroir** (décision utilisateur) : il pose un **renvoi**, valable de la pose jusqu'à la fin du
  tour du joueur suivant ; plusieurs renvois s'additionnent. Le renvoi est un **stock pour le
  tour** qui diminue à chaque coup renvoyé (interprétation à valider) ; l'incendie n'est jamais
  renvoyé.
- **Valeurs inventées, à régler par simulation** : bouclier 6 de Petit Jean, bouclier 10 du Boss,
  renvoi 5 de Miroir, augmentations de +1 tous les 3 tours. PV et dégâts de base repris des
  premiers ennemis du jeu (eux-mêmes inventés, sauf le Boss : 150 PV, 5 dégâts, +2, donnés par
  l'utilisateur).

### 13.4 Composition des flottes (`flotte.py`)

- **Prime** (`flotte_prime`) : 1 ennemi tiré au sort jusqu'au niveau 5, puis 2 à partir du
  niveau 6, parmi les ennemis à 1 case.
- **Boss** (`flotte_boss`) : le Boss des pirates seul, sur les deux cases de la rangée du milieu,
  au niveau 10. Plusieurs boss tirés au sort sont prévus à terme, pas codés.
- **Astéroïdes** (`flotte_asteroides`, aventures.md §2.5) : 3 ennemis.
- **Placement préféré** (`Ennemi.placement`, `placer_ennemis`) : Petit Jean (`PROTECTEUR_AVANT`) de
  préférence à l'avant, Le nettoyeur (`PROTEGE_ARRIERE`) à l'arrière ; les autres remplissent les
  cases restantes, avant d'abord.
- **À reprendre** : la difficulté par niveau (coefficient, tailles, nombre d'ennemis). Les
  simulations montrent des niveaux 2 à 5 trop faciles (a-trancher.md §11).

### 13.5 Points de vie des modules

Les PV se lisent dans `config/modules.json` : **60 PV** pour le principal, **20 PV** pour le
Lanceur de missiles (valeurs provisoires, à régler par simulation). Un secondaire repart à ses PV
max à chaque combat (§3.4) ; « Améliorer » à la Station augmente les PV max (parcours.md §2.2).
