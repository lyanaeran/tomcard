# Space Fight

*Deckbuilder roguelike (vaisseaux spatiaux) — Document de conception — v0.1*

---

## 1. Pitch

Un deckbuilder roguelike inspiré de Slay the Spire, où le joueur incarne un vaisseau spatial composé de **modules**. Chaque module possède son propre deck de compétences. Contrairement à Slay the Spire, il n'y a pas de héros unique ni de carte de monde classique : le joueur avance à travers une série de choix à chaque tour, en gérant la survie et la progression de son vaisseau.

---

## 2. Boucle de jeu (structure de run)

- Pas de carte de progression classique : à chaque étape, le joueur ne voit que **la prochaine étape** (aucune visibilité au-delà)
- Après chaque combat gagné, phase de récompenses (§2.1) puis le joueur choisit la prochaine étape parmi celles proposées
- Types d'étapes possibles :
  - **PRIME** — combat, contrat de chasseur de primes. Affiche un niveau de difficulté / la composition annoncée des ennemis (tailles S/M/L, cf. 3.2) sans révéler le détail exact
  - **STATION SERVICE** (le "garage") — entretien du vaisseau contre de l'Argent : réparer, améliorer ou déplacer un module (détail en §2.2). Logique d'apparition encore ouverte (voir §8), pistes à l'étude :
    - toujours disponible en alternative à chaque étape, ou
    - probabilité liée aux PV du vaisseau (voire garantie sous un seuil de dégâts), ou
    - garantie après un combat difficile (Prime dure ou Boss)
  - **PLANÈTE COMMERCIALE** (le "marché") — achat de cartes contre de l'Argent ; la disponibilité des cartes Rares/Légendaires pour un module dépend de son niveau d'amélioration (voir §2.2 et §6)
  - **AVENTURE** — événement inconnu, façon "?" de Slay the Spire. Contenu entièrement à définir (§9.1)
  - *(autres types d'étapes à imaginer)*
- **Boss** : revient toutes les *n* étapes (n à ajuster en playtest, indicatif 8-10)
  - Victoire sur un boss → le joueur choisit **1 nouveau module parmi 2 propositions**, avec ses cartes de base associées (deck de départ propre au module — détail à trancher une fois le système de cartes approfondi, voir §7)

### 2.1 Argent et récompenses de combat

- Après chaque combat gagné, le joueur gagne de l'**Argent** — nouvelle ressource de run, distincte de l'Électricité (ressource de combat, voir §3). Montant exact à définir (§9.1)
- Il gagne aussi peut-être une carte : voir §6 pour le mécanisme de choix (candidate par module équipé). Récompense garantie ou probabiliste à trancher (§9.1)
- Le joueur choisit ensuite l'étape suivante parmi celles qui apparaissent (Prime, Station service, Planète commerciale ou Aventure) — l'offre n'est pas forcément la même à chaque fois (voir §9.1)

### 2.2 Station service (garage)

Trois options indépendantes, chacune payante en Argent (montants à définir, §9.1) :

- **Réparer un module** : restaure ses PV jusqu'à son maximum actuel
- **Améliorer un module** : augmente ses PV max. Pistes envisagées (non exclusives, à trancher en §9.1) :
  - le module ne propose au départ que des cartes Communes (en récompense de combat comme à la Planète commerciale), et débloque le palier Rare puis Légendaire au fil de ses améliorations
  - un module amélioré propose plusieurs cartes au choix après combat plutôt qu'une seule
- **Déplacer un module** : change sa position sur le vaisseau, contre paiement

---

## 3. Système de combat

### 3.1 Placement / rangs
- Formation en **2 rangs** : avant et arrière, pour le joueur et pour l'ennemi
- Corps à corps : ne peut frapper que le rang avant adverse
- Distance : peut frapper n'importe quel rang
- Certaines compétences perçantes touchent l'avant + l'arrière simultanément
- Le placement des modules fragiles/soigneurs à l'arrière devient une décision tactique
- Idée de module dédié (Propulseur) pour repositionner en cours de combat

### 3.2 Tailles de monstres
- Trois tailles : **S, M, L**
- Le joueur connaît la composition annoncée avant le combat (ex : "2 S + 1 M") mais pas le détail exact des ennemis
- **S** : 1 emplacement, PV faibles, souvent en groupe
- **M** : 1 emplacement, PV/dégâts intermédiaires
- **L** : prend 2 emplacements, gros PV, attaque de zone ou pattern en plusieurs temps

### 3.3 Ressource et main de cartes
- **Électricité** = ressource commune à tout le vaisseau (pas un pool par module)
- Le joueur pioche une main et joue ses cartes **librement, dans l'ordre de son choix** (comme dans Slay the Spire)
- Force des choix de répartition : concentrer l'électricité sur un module ce tour, ou répartir
- **Ordre de jeu** : tour classique façon StS — le joueur joue librement toutes les cartes qu'il souhaite durant son tour, puis le tour ennemi se déroule. Pas de système d'initiative/vitesse par module
- **Main** : capacité maximale de 10 cartes ; le joueur pioche 5 cartes par tour. Cartes jouées partent en défausse ; quand la pioche est vide, la défausse est mélangée pour reformer la pioche. Exception : une carte à munitions limitées épuisée (0 munition restante) part dans la pile **cartes épuisées** au lieu de la défausse, cf. §3.6
- **Fin de tour** : les cartes non jouées restant en main sont défaussées à la fin du tour du joueur (comme dans Slay the Spire), avant la pioche de la main suivante

### 3.4 Destruction de module
- Un module à **0 PV est détruit**, même si le combat est gagné (perte permanente)
- Le **module de base** est la condition de game over : sa destruction termine la run
- **Récupération entre combats** : aucune régénération automatique des PV — seule la Réparation (module dédié, voir 4.2) permet d'en restaurer. Le vaisseau garde ses dégâts d'un combat à l'autre, sauf passage par une Station Service (voir §2)

### 3.5 Bouclier
- Le Bouclier absorbe les dégâts subis **avant** les PV. Exemple : un module protégé par 5 Bouclier subit une attaque de 7 dégâts → le Bouclier absorbe 5, les **2 dégâts restants** sont retirés des PV

### 3.6 Munitions (cartes à usage limité)

Certaines cartes ont un nombre de munitions limité en plus de leur coût en électricité (cf. §7.4) :

- **Munitions illimitées** (cas par défaut, toutes les cartes actuelles du POC) : aucun changement, la carte se joue normalement, autant de fois que voulu tant que l'électricité suit
- **Munitions limitées à N** : chaque utilisation de la carte décrémente son compteur de munitions restantes. Le compteur est **propre à chaque exemplaire physique de la carte dans le deck** (si le deck contient 2 exemplaires d'une carte à 1 munition, chacun peut être joué une fois, soit 2 utilisations au total sur le combat)
- Quand le compteur d'un exemplaire tombe à **0**, cet exemplaire quitte définitivement le combat : au lieu de partir en défausse, il rejoint une nouvelle pile, les **cartes épuisées**, distincte de la pioche et de la défausse
- Les cartes épuisées ne reviennent **jamais** dans la pioche pendant le combat en cours, même si la pioche et la défausse sont toutes les deux vides (pas de mélange de secours) — cf. §9.1 pour le cas limite où cela viderait totalement les cartes piochables
- **Entre deux combats**, chaque carte à munitions limitées repart avec son nombre de munitions d'origine (le compteur ne persiste pas d'un combat à l'autre) — cohérent avec le fait que le deck de combat est reconstitué à chaque combat à partir des pools de cartes des modules équipés (§6)

---

## 4. Modules

Le vaisseau démarre avec un **module de base**, et en récupère d'autres au fil de l'avancée. Chaque module a son propre deck de cartes (certaines cartes communes entre modules).

### 4.1 Modules d'attaque (spécialisés, pas un seul module générique)

**Canon lourd** — mono-cible, gros dégâts. Fort contre les L, faible contre les essaims de S.
- Tir de précision (1⚡, 8 dégâts)
- Charge concentrée (2⚡, 14 dégâts)
- Tir perforant (2⚡, 10 dégâts, avant + arrière de la colonne)
- Surcharge (3⚡, 20 dégâts, ne peut pas retirer au tour suivant)

**Batterie Gatling** — multi-cible / dégâts répartis. Fort contre les groupes de S, faible contre un seul L.
- Rafale (1⚡, 3 dégâts à 2 cibles aléatoires)
- Tir de suppression (2⚡, 4 dégâts à tout le rang avant)
- Barrage (2⚡, 3 dégâts à toutes les cibles)
- Surchauffe (0⚡, 5 dégâts, génère de la Chaleur/malus cumulatif)

**Missiles** — ciblage à distance, ignore le placement. Très fort contre les soigneurs/supports planqués à l'arrière ; disruptif pour le système de rangs, à réserver en rare/tardif.
- Verrouillage (1⚡, 6 dégâts, cible n'importe quel rang)
- Salve guidée (2⚡, 4 dégâts x2, cibles différentes, ignore le rang)
- Frappe orbitale (3⚡, 12 dégâts sur tout le rang arrière ennemi)

**Laser** — dégâts constants / perçants en ligne. Bon contre les ennemis à haut PV qui durent.
- Faisceau (1⚡, 4 dégâts, traverse toute la colonne)
- Incision (1⚡, applique Brûlure 3 dégâts/tour x3)
- Rayon continu (2⚡, 6 dégâts + Brûlure 2 dégâts/tour x2)

### 4.2 Modules de soutien / défense

**Blindage** — absorbe les dégâts, protège les autres modules.
- Plaque renforcée (1⚡, 6 Bouclier sur ce module)
- Mur défensif (1⚡, 4 Bouclier sur ce module + 4 sur un allié adjacent)
- Protection croisée (2⚡, 8 Bouclier réparti sur jusqu'à 2 modules)
- Position de tank (1⚡, ce module devient la seule cible possible ce tour) — *carte signature*
- Renfort d'urgence (2⚡, Bouclier = PV manquants d'un allié, plafonné)
- Bouclier réactif (2⚡, 6 Bouclier + renvoie des dégâts si attaqué)
- Fortification totale (3⚡, Bouclier à tout le vaisseau, ce module ne peut ni attaquer ni bouger)
- Bastion (2⚡, carte power : génère 3 Bouclier auto chaque tour)
- *Malus optionnel* : Blindage lourd (0⚡, 5 Bouclier, -1 PV max permanent)

**Contrôle** — désactive/stun temporairement les ennemis. Aucun dégât, mais désamorce les menaces prioritaires (essentiel contre les L).
- Impulsion électromagnétique (1⚡, stun 1 tour)
- Brouillage (1⚡, -50% dégâts d'une cible pendant 2 tours)
- Champ de gel (2⚡, stun tout le rang arrière ennemi)
- Piratage (2⚡, force une cible à attaquer un allié à elle)
- Verrou total (3⚡, stun un L pendant 2 tours)

**Réparation** — répare les modules abîmés. Seul contre-poids à la destruction permanente.
- Soudure rapide (1⚡, répare 6 PV)
- Nanites réparatrices (1⚡, répare 3 PV/tour x3, persiste)
- Atelier d'urgence (2⚡, répare 10 PV réparti sur 2 modules)
- Restauration critique (2⚡, répare un module à 1 PV jusqu'à 15 PV)
- Reconstruction (3⚡, une fois par run, ressuscite un module détruit à 1 PV) — *rare*

### 4.3 Autres archétypes proposés

- **Bouclier énergétique** : convertit l'électricité non dépensée en Bouclier
- **Radar / Ciblage** : marque une cible (+dégâts subis), révèle les intentions ennemies
- **Propulseur** : esquive, échange de position entre modules en cours de combat
- **IA de combat / Drone** : invoque une unité automatique, rend une carte gratuite
- **Générateur** : produit de l'électricité bonus (module "économique" pur)
- **Sabotage** : dégâts dans le temps (Brûlure), réduction d'armure ennemie
- **Soute / Fret** : non-combattant, bonus passif (pioche, or) en échange d'un slot de combat

---

## 5. Slots de modules équipables

- Début de run : module de base + 1 module (2 slots)
- +1 slot débloqué à chaque victoire de boss (rythme lié à la fréquence des boss, voir §2)
- **Plafond proposé : 5 slots** (module de base inclus) — valeur provisoire, encore susceptible de changer
- Le module de base occupe toujours un slot et reste équipé
- **Doublons de modules** : à trancher — proposition initiale : **interdire les doublons** (un archétype par run) pour forcer la diversité et simplifier l'équilibrage en v1

---

## 6. Progression des modules / cartes

- Après un combat gagné, le joueur gagne peut-être une carte (voir §2.1). Mécanisme : **1 carte candidate par module équipé**, tirée dans le pool de cartes propre à ce module — le joueur choisit parmi ces N candidates, ce qui attribue implicitement la carte au module correspondant
  - Pour le **module principal** (module de base), sa candidate est tirée dans le **pool entier** de cartes (tous modules confondus)
  - Pour un **module secondaire**, sa candidate est tirée dans la **liste de cartes propre à ce module**
  - La rareté (voir 7.3) pondère chaque tirage individuel
  - Remplace l'ancien mécanisme "1 carte parmi 3 propositions pondérées par rareté, avec choix du module destinataire" : le choix du module destinataire se fait maintenant implicitement en choisissant la candidate
- À la Planète commerciale (§2.2), achat direct de cartes contre de l'Argent ; la disponibilité de cartes Rares/Légendaires pour un module dépend de son niveau d'amélioration (Station service, §2.2)
- Amélioration d'un module (Station service, §2.2) : piste envisagée pour débloquer des paliers de rareté supérieurs pour ses candidates après combat et/ou pour ses cartes disponibles à la Planète commerciale — probabilités et seuils exacts à trancher (§9.1)

---

## 7. Types de cartes

### 7.1 Types (par effet)

Classification par nature de l'effet — remplace l'ancien découpage par portée/persistance.

| Type | Description | Sous-catégories |
|---|---|---|
| **Attaque** | Inflige des dégâts | Direct / décalé (dégâts différés) / poison (dégâts sur la durée) |
| **Defense** | Protège un ou plusieurs modules | Bouclier absolu (x tours), réduction de dégâts en %, régénération de Bouclier sur la durée |
| **Controle** | Neutralise ou limite un ennemi | Stun, restriction d'action (ex : pas d'attaque ce tour) |
| **Debuff** | Affaiblit une cible ennemie | Plafond de dégâts infligés, réduction en %, réduction de Bouclier |
| **Buff** | Renforce le vaisseau ou un module | Augmentation de dégâts, augmentation de Bouclier |
| **Reparation** | Répare les PV d'un module | (voir aussi module Réparation, §4.2) — remplace l'ancien type "Soin" |
| **Outils** | Manipule la pioche/défausse ou l'électricité | Piocher, défausser, recycler... ; gagner/convertir de l'électricité |

Noms de type volontairement **sans accent** (Defense, Controle, Reparation), pour correspondre
directement aux futures valeurs de l'enum `TypeCarte` côté code (§10). Le moteur actuel n'implémente
encore qu'un sous-ensemble : voir §12.5 pour l'état d'implémentation par type.

### 7.2 Cible

Troisième axe, indépendant du type — n'importe quel type (pas seulement Attaque) peut cibler différents camps/motifs : une Défense peut protéger un allié unique ou tout le vaisseau, un Debuff peut viser un ennemi unique ou tout un rang, etc.

| Cible | Description |
|---|---|
| **Soi** | Le module qui joue la carte |
| **Allié unique** | Un module ami au choix (parfois avec contrainte : adjacent, à portée...) |
| **Alliés multiples / vaisseau entier** | Plusieurs modules ciblés, ou tout le vaisseau |
| **Ennemi unique** | Une cible ennemie, avec contraintes de rang possibles (rang avant uniquement, n'importe quel rang...) |
| **Ennemis multiples** | Motif fixe (ligne, colonne, rang entier) ou aléatoire, jusqu'à tous les ennemis |
| **Ligne ennemie** | Cas particulier d'"ennemis multiples" pour les cartes perçantes (§3.1) : touche l'avant et l'arrière de la rangée de la cible cliquée (2 ennemis au plus), cf. poc.md §4 |

### 7.3 Rareté

Axe indépendant du type et de la cible — une carte a un type, une cible **et** une rareté.

| Palier | Fréquence | Puissance |
|---|---|---|
| **Commune** | Fréquente | Effets simples et fiables, cœur du deck |
| **Rare** | Peu fréquente | Meilleur ratio effet/électricité, ou mécanique inédite |
| **Légendaire** | Très peu de cartes | Effets exceptionnels, peuvent changer la façon de jouer un module (ex : Reconstruction, §4.2) |

- La rareté pondère le tirage des **candidates de carte** offertes après un combat gagné (§6, une candidate par module équipé) ainsi que la disponibilité des cartes à la Planète commerciale (§2.2) : plus une carte est rare, moins elle a de chances d'apparaître, sauf module suffisamment amélioré (Station service, §2.2)
- Le tag "rare" déjà présent sur *Reconstruction* (§4.2) sera à réévaluer : son effet (résurrection d'un module) correspond plutôt au palier **Légendaire**
- Rareté et attribution précise par carte (§4.1-4.3) : à faire dans une passe dédiée (voir §9.1 "compléter le jeu de cartes")

### 7.4 Munitions

Axe indépendant du type, de la cible et de la rareté — une carte a, en plus de son coût en
électricité, un nombre de munitions : soit **illimité** (comportement par défaut, cf. §3.6), soit un
nombre fixe qui se consomme au fil du combat et se réinitialise au combat suivant. Voir §3.6 pour le
détail du fonctionnement (pile "cartes épuisées", compteur par exemplaire).

- Sert à limiter des effets ponctuellement très forts (ex : Bouclier perpétuel, §4.2) sans les
  rendre indéfiniment répétables dans un même combat
- Rôle par rapport à la rareté : deux axes différents, une carte Commune peut avoir des munitions
  limitées et une carte Légendaire des munitions illimitées, ou l'inverse — pas de règle systématique
  pour l'instant (voir §9.1)

---

## 8. Interface / écran de combat

### 8.1 Disposition générale (wireframe)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SPACE FIGHT — ÉCRAN DE COMBAT                                  ⚡ Électricité: 5 │
│                                                                                    │
│  VAISSEAU DU JOUEUR                                FLOTTE ENNEMIE (6 emplacements)│
│  (fond commun aux 5 emplacements)                                                 │
│                                                                                    │
│   Arrière          Avant                            Avant           Arrière      │
│  (loin ennemi)   (face ennemi) →→              ←← (face joueur)   (loin joueur)   │
│  ┌──────┐        ┌──────┐                       ┌──────┐          ┌──────┐        │
│  │  AG  │        │  FG  │                       │  E   │          │  E   │        │
│  └──────┘        └──────┘                       └──────┘          └──────┘        │
│  ┌────────────────────┐                         ┌──────┐          ┌──────┐        │
│  │        BASE         │                         │  E   │          │  E   │        │
│  └────────────────────┘                         └──────┘          └──────┘        │
│  ┌──────┐        ┌──────┐                       ┌──────┐          ┌──────┐        │
│  │  AD  │        │  FD  │                       │  E   │          │  E   │        │
│  └──────┘        └──────┘                       └──────┘          └──────┘        │
│                                                                                    │
│                                                     ┌─────────┐ ┌─────────┐        │
│                                                     │ Pioche  │ │Défausse │        │
│                                                     │  (24)   │ │  (5)    │        │
│                                                     └─────────┘ └─────────┘        │
│         ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                        │
│         │ Carte │ │ Carte │ │ Carte │ │ Carte │ │ Carte │  ← main, alignée        │
│         │  1⚡   │ │  2⚡   │ │  1⚡   │ │  0⚡   │ │  3⚡   │   (pas en éventail)     │
│         └───────┘ └───────┘ └───────┘ └───────┘ └───────┘                        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

- **Vaisseau du joueur** (haut gauche) : grille de **2 colonnes (arrière/avant) x 3 rangées (gauche/mid/droite)**. La colonne **avant est tournée vers l'ennemi** (la plus proche du centre de l'écran), la colonne arrière est la plus éloignée. Le tout repose sur un **fond commun** qui regroupe visuellement les 5 emplacements. Le **module de base** occupe la rangée mid en entier (arrière-mid + avant-mid fusionnés) ; les 4 autres modules équipés prennent FG/FD/AG/AD
- **Flotte ennemie** (haut droite) : grille symétrique 2x3, 6 emplacements libres (pas de base adverse). La colonne **avant est tournée vers le joueur** (la plus proche du centre de l'écran) et c'est elle qui est exposée au corps à corps (voir 3.1) ; la colonne arrière est la plus éloignée
- **Compteur d'électricité** restante affiché en haut de l'écran
- **Main de cartes** : alignée en bas de l'écran (pas en éventail, pour la lisibilité)
- **Pioche, défausse et cartes épuisées** (§3.6) : regroupées ensemble dans un coin de l'écran (compteurs de nombre de cartes), séparées de la main

### 8.2 Formes visuelles

- **Modules du joueur et ennemis** : images **carrées**
- **Module de base** : exception, forme différente (plus grande, fond dédié qui englobe les 5 emplacements)
- **Cartes** : format **rectangulaire**
- **PV / Bouclier** : affichés par de petites pastilles rondes (rouge pour les PV, bleue pour le Bouclier) flottant juste au-dessus de chaque case, jamais superposées à l'image (validé en POC, voir poc.md §8)
- **Munitions restantes** (§3.6) : affichées sur la carte comme le coût en électricité, dans une pastille ronde **verte** — uniquement pour les cartes à munitions limitées (rien affiché pour les munitions illimitées, comportement par défaut)

### 8.3 Interaction de jeu d'une carte

**Le jeu se joue entièrement à la souris.**

1. Clic sur une carte de la main → la carte se **surligne** (état "armée")
2. Clic sur une **cible valide** → la carte se résout, part en défausse, la surbrillance disparaît
3. Pour les cartes sans cible unique (Alliés multiples, Ennemis multiples, Module principal, effet
   sur tout un camp) : la cible précise du clic ne compte pas pour l'effet, mais **un clic de
   confirmation reste nécessaire** sur n'importe quelle case vivante du bon camp (allié ou ennemi) —
   pas de résolution automatique au seul clic sur la carte, pour éviter qu'un clic accidentel ne la
   joue (validé dans le POC, voir poc.md §4). **Ce flux de clic/tap doit rester identique entre la
   version PC et la version web/iOS** (cf. CLAUDE.md, "Deux façons de jouer")
4. **Fin de tour** : un bouton cliquable "Fin de tour" permet au joueur de terminer son tour à tout moment, même s'il lui reste de l'électricité ou des cartes jouables
5. **Retour visuel des effets** : chaque effet résolu (carte jouée ou attaque ennemie) affiche un popup `+N`/`-N` pendant quelques secondes sur la ou les cases touchées, avec le montant **réellement appliqué** (plafonné par les PV+Bouclier restants pour les dégâts, par le PV max pour le soin) plutôt que la valeur nominale de la carte — validé en POC, voir poc.md §8

---

## 9. Points encore à trancher

### 9.1 Design / gameplay

- Contenu exact de la Planète commerciale (uniquement des cartes, ou aussi d'autres bonus ?) et de l'Aventure (entièrement à définir, voir §2)
- Logique d'apparition de la Station service : toujours disponible, liée aux PV du vaisseau, ou garantie après un combat difficile (voir §2)
- Montants exacts d'Argent : récompense de combat, coût de réparation, coût d'amélioration, coût de déplacement d'un module (§2.1, §2.2)
- Probabilités de déblocage des paliers de rareté (Commune → Rare → Légendaire) selon le niveau d'amélioration d'un module, et si l'amélioration ajoute plutôt/en plus des candidates multiples après combat (§2.2, §6)
- La Planète commerciale propose-t-elle des cartes pour tous les modules du pool, ou seulement pour les modules actuellement équipés ? (§2, §6)
- La carte gagnée après un combat est-elle garantie à chaque victoire, ou seulement probable ? (§2.1, §6)
- Fréquence exacte des Boss (valeur de *n* étapes)
- Cartes de base fournies avec un nouveau module choisi après un Boss : deck de départ fixe par module, à définir une fois le système de cartes approfondi (voir §7)
- Plafond exact de slots équipables (proposition actuelle : 5, base incluse) et autorisation ou non des doublons de modules
- Représentation visuelle d'un ennemi L occupant 2 emplacements (§3.2, §8.1) : rectangle fusionné sur les 2 cases, ou deux images liées logiquement ?
- Compléter le jeu de cartes de chaque module : les archétypes de §4.3 (Bouclier énergétique, Radar, Propulseur, IA de combat, Générateur, Sabotage, Soute/Fret) n'ont pas encore de decks détaillés comme ceux de §4.1-4.2 ; les cartes déjà écrites en §4.1-4.2 n'ont pas encore de type/cible/rareté assignés (§7)
- Munitions (§3.6/§7.4) : cas limite si la pioche et la défausse sont toutes les deux vides en cours de combat alors qu'il reste des cartes épuisées (qui ne sont jamais remélangées) — le joueur peut alors se retrouver sans carte à piocher ; à surveiller en playtest une fois des cartes à munitions limitées réellement jouables (voir §9.2 pour l'état d'implémentation actuel)
- Munitions (§7.4) : pas de règle systématique reliant rareté et munitions pour l'instant (une carte de n'importe quel palier peut avoir des munitions limitées ou non) — à revisiter si un pattern se dégage en concevant plus de cartes

### 9.2 Technique / développement

*(voir §10 pour les choix techniques déjà tranchés)*

- Munitions (§3.6/§7.4) : mécanique pas encore implémentée dans `src/gameplay/` — les cartes du
  tableau de conception qui en ont une (ex : Réparation, Bouclier perpétuel) sont pour l'instant
  stockées dans `config/cartes.json` sans bloc "effet" (non jouables), voir la PR "config : import
  des cartes Module principal, Lanceur de missiles, Blindage"

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
tests/
pyproject.toml
```

- `assets/` : uniquement des images pour le moment ; le son sera ajouté plus tard si besoin
- `config/` : contenu du jeu décrit en JSON (modules, ennemis, cartes), référençant les images d'`assets/` — détail du format en poc.md
- Séparation stricte entre `src/ui` (affichage PC) et `src/gameplay` (logique de jeu, partagée avec la version web)
- `src/gameplay` reste la seule source de vérité des règles de jeu : la version web ne fait que l'exécuter et l'afficher, elle ne réimplémente aucune règle

### 10.3 Conventions de code

- Classes claires et bien définies, une responsabilité par classe
- Commentaires en français, **sans accents ni cédilles** (ASCII uniquement)
- Tests unitaires (pytest) dans `tests/`

---

## 11. Idées à explorer plus tard

Pistes évoquées mais pas encore approfondies ni décidées — à revisiter une fois le système de
cartes (§7) et la boucle de récompenses (§2.1, §6) stabilisés.

- **Cartes auto-jouées** : des cartes qui se déclenchent seules, sans action du joueur, en début ou
  en fin de combat (ex : buff automatique pour toute la durée du combat au démarrage, soin ou gain
  d'Argent à la fin) — distinct des cartes jouées normalement pendant le tour du joueur (§3, §7)
- Une carte auto-jouée en fin de combat pourrait aussi offrir une carte candidate supplémentaire, en
  plus de la récompense normale de combat (§2.1, §6)
- À trancher plus tard : comment ces cartes s'intègrent au deck existant (pioche normale, zone à
  part, slot dédié au module...), leur coût (électricité ou gratuites, puisqu'elles ne sont pas
  jouées manuellement), et si elles ont une rareté (§7.3) comme les autres cartes
- **Type de carte "Effet"** (nouveau, distinct des types de §7.1) : une carte qui produit son effet
  dès qu'elle est **piochée**, plutôt que jouée par le joueur. Probablement ajoutée au deck par les
  ennemis (dans l'esprit des cartes Statut/Malédiction de Slay the Spire) plutôt que choisie par le
  joueur
- **Stacks à intensité cumulative** (façon Poison/Force de Slay the Spire) : un unique compteur par
  ennemi qui s'additionne à chaque application (contrairement aux debuffs Vulnérabilité/Réduction de
  dégâts actuels, §7.1/§12.1, où chaque application reste une instance indépendante avec sa propre
  durée — plusieurs instances coexistent et leurs magnitudes s'additionnent tant qu'elles sont
  actives, mais rien ne fusionne en un seul compteur) et qui inflige un effet croissant avec le
  nombre de stacks (ex : dégâts égaux au compteur, qui décroît de 1 chaque tour). Mécanique distincte
  à concevoir pour de futures cartes, pas une règle à appliquer aux cartes de vulnérabilité
  existantes

---

## 12. Mécaniques de combat manquantes (constat issu du tableau de cartes)

En important le tableau de conception de cartes de l'utilisateur dans `config/cartes.json` (voir la
PR "config : import des cartes Module principal, Lanceur de missiles, Blindage"), seules 6 des 38
cartes du tableau correspondaient à ce que le moteur (`src/gameplay/carte.py`, `combat.py`) savait
exécuter à l'époque. Ce nombre a augmenté au fil des mécaniques ajoutées ci-dessous (22/38 jouables
au moment de la rédaction la plus récente de cette section, cf. poc.md §4) ; les cartes restantes
sont stockées pour référence (champ `_non_jouable`) mais inertes en jeu tant que leur mécanique
n'est pas implémentée. Cette section recense les mécaniques qui leur manquent, groupées par nature
plutôt que par carte, pour servir de feuille de route à une future extension du moteur.

### 12.1 Cibles fixes ou par rang

- **Module Principal** — cible toujours le module de base, sans choix du joueur — **implémenté**
  (`CibleCarte.MODULE_PRINCIPAL`, sans clic) : *Protéger le vaisseau, Réparation, Blindage maximal*
  jouables
- **Ennemi Avant** / **Ligne avant** ennemie, **Ennemi Arrière** / **Ligne arrière** — **implémenté**
  (`CibleCarte.COLONNE_AVANT_ENNEMIE` / `COLONNE_ARRIERE_ENNEMIE`, colonne fixée par la carte, un
  clic sur l'autre colonne est refusé) : *Ligne avant, Ligne arrière* jouables
- **Module Avant** — colonne avant alliée uniquement (avant-gauche + avant-droite, jamais le
  module principal qui occupe la rangée mid) — **implémenté** (`CibleCarte.COLONNE_AVANT_ALLIEE`,
  même principe que les colonnes ennemies : un clic sur un module de cette colonne précise
  confirme) : *Protéger l'avant poste* jouable

Ces cibles par rang se résolvent par un **clic sur une case du rang visé**, comme la Ligne ennemie
perçante (§3.1, §7.2), et non automatiquement comme Alliés/Ennemis multiples.

### 12.2 Effets à deux valeurs (X et Y) sur une même carte

- Cible unique + splash différencié : X à la cible cliquée, Y à toutes les autres (*Missiles*)
- Deux zones différentes en une carte : X sur la ligne avant ennemie, Y sur la ligne arrière
  (*Torpille*)

### 12.3 Effets à durée (plusieurs tours)

Debuff actif pendant Y tours (chaque application ajoutée à la liste `Ennemi.debuffs_actifs`, comme
une instance indépendante avec sa propre durée ; décrémentée à chaque tour ennemi écoulé même si
l'ennemi concerné n'a pas agi, et retirée de la liste à 0) — **implémenté** pour les debuffs
(§12.4/§12.5) : *Boucliers hors service* jouable.

Même mécanique côté allié (`Module.buffs_actifs`), avec en plus la possibilité d'une durée **nulle**
(`tours_restants=None`) pour un buff **persistant** qui ne décompte jamais et dure tout le combat —
**implémenté** (§12.5) : *Bouclier perpétuel* (persistant) et *Blindage maximal* (durée limitée,
même mécanisme `BOUCLIER_PAR_TOUR` avec `duree` finie plutôt que nulle) jouables — les deux seules
cartes Buff à effet périodique simple (les 3 autres cartes Buff restantes sont des méta-effets, cf.
§12.5/§12.7). L'effet d'un buff se déclenche une première fois immédiatement à la pose de la carte
(comme les autres types de carte), puis se redéclenche à chaque début de tour joueur tant qu'il
reste actif.

Un buff persistant cible toujours le **module principal** plutôt qu'un module au choix du joueur
(déviation assumée de la cible "Module Unique" du tableau de conception, décision utilisateur) : lui
seul est garanti de survivre tout le combat (§3.4), donc le seul module où un effet censé durer
jusqu'à la fin a du sens. Sur un module, les buffs à durée limitée et les buffs persistants sont
affichés **séparément** (deux pastilles distinctes avec un compte chacune, jamais additionnées ; deux
groupes distincts dans l'infobulle), pour que le joueur distingue d'un coup d'œil ce qui va expirer
de ce qui ne bougera plus jusqu'à la fin du combat.

Reste manquant pour les autres effets à durée :

- Dégâts répétés pendant Y tours (*Embrasement, Guerre nucléaire*)
- Pioche bonus pendant Y tours (*Multi fonction*)

### 12.4 Effets en pourcentage

**Implémenté pour les debuffs** (somme des `valeur` des debuffs `VULNERABILITE` actifs dans
`Ennemi.debuffs_actifs`, majore les dégâts subis d'une attaque du joueur) : *Brèche, Ligne avant,
Boucliers endommagés, Boucliers hors service* jouables. **Implémenté aussi côté allié**
(`ActionCarte.BOUCLIER_POURCENTAGE_PV` sur une carte Defense : bouclier = `valeur`% des PV **max**
de la cible cliquée — les PV actuels varieraient trop selon les dégâts déjà subis, l'effet doit
rester prévisible — arrondi à l'entier le plus proche) : *Bouclier adaptatif* jouable.

### 12.5 Types de carte absents du moteur

Déjà nommés en §7.1. État d'implémentation dans `combat.py` :

- **Reparation** — **implémenté** (renommage de l'ancien type `SOIN`, même logique)
- **Debuff** — **implémenté** (`TypeCarte.DEBUFF`, trois actions : `REDUCTION_DEGATS`,
  `VULNERABILITE` et `REDIRECTION_CIBLE`, cf. §12.1/§12.3/§12.4/§12.6) : *Tordre le canon, Brèche,
  Ligne avant, Boucliers endommagés, Boucliers hors service, Tir allié* jouables — les 6 cartes du
  module Sabotage sont maintenant toutes jouables
- **Buff** — **implémenté** (`TypeCarte.BUFF`, une action : `BOUCLIER_PAR_TOUR`, cf. §12.3) :
  *Bouclier perpétuel, Blindage maximal* jouables. *Optimisation des boucliers, Attaques
  performantes* (modification du coût d'une catégorie de cartes) et *Double défense, Circuit
  parallèle* (duplication d'effet) restent non jouables, ce sont des méta-effets distincts (§12.7),
  pas de simples buffs sur un module
- **Outils** — **implémenté** (`TypeCarte.OUTILS`, cf. §12.9) pour trois actions (`GAIN_ELECTRICITE`,
  `GAIN_ELECTRICITE_PAR_MODULE`, `PIOCHE_SUPPLEMENTAIRE`) : *Surcharge temporaire, Fonds de tiroir,
  Boost* jouables. Le reste demande encore une logique dédiée (*Changement d'outil, Manque de jus,
  Cannibalisme, Grand remplacement, Multi fonction*)
- **Controle** : toujours aucune carte taguée Controle dans le tableau ; type prévu en §7.1 (stun,
  restriction d'action) mais rien à implémenter pour l'instant

### 12.6 Altération / redirection des dégâts

- Transfert des dégâts subis vers un autre module désigné (*Transfert*)
- Renvoi des dégâts subis à l'attaquant (*Renvoie*)
- Annulation totale de la prochaine attaque sur une cible, différent d'un bouclier classique
  (*Leurre*)
- Détournement de la cible d'un ennemi vers un de ses voisins — mécanique déjà anticipée comme
  *Piratage* en §4.2 — **implémenté** (`ActionCarte.REDIRECTION_CIBLE`) : *Tir allié* jouable. Le
  "voisin" est **n'importe quel autre ennemi vivant** (pas de restriction géométrique d'adjacence,
  décision prise avec l'utilisateur) — l'ennemi debuffé attaque un allié à lui tiré au hasard parmi
  les ennemis vivants restants, plutôt qu'un module du joueur, à son prochain tour ; sans autre
  ennemi vivant, il attaque normalement (rien à rediriger vers). Le tirage au hasard n'a lieu qu'à
  la résolution réelle du tour (`Combat._cible_redirection`), jamais lors d'un simple survol/tap de
  prévisualisation (`Combat.previsualiser_cible`), pour ne pas consommer l'aléa à chaque redessin —
  l'UI affiche alors "Vise un allié au hasard" plutôt qu'une cible précise, tant que le tour n'est
  pas résolu

### 12.7 Modification des règles d'autres cartes (méta-effets)

- Changer le coût en électricité de toutes les cartes d'une catégorie pour le reste du combat
  (*Optimisation des boucliers, Attaques performantes*)
- Dupliquer l'effet de toutes les cartes d'une catégorie X fois (*Double défense, Circuit
  parallèle*)

### 12.8 Gain d'électricité via une carte

- Gain fixe (*Surcharge temporaire*) — **implémenté** (`ActionCarte.GAIN_ELECTRICITE`)
- Gain proportionnel au nombre de modules actifs (*Fonds de tiroir*) — **implémenté**
  (`ActionCarte.GAIN_ELECTRICITE_PAR_MODULE`, `valeur` x nombre de modules alliés vivants, base
  incluse - mêmes modules que `Combat._modules_vivants()`, déjà utilisé pour Alliés multiples §7.2)
- Gain en échange d'une défausse (*Manque de jus, Cannibalisme*)

### 12.9 Manipulation de pioche / main / défausse via une carte

- Piocher des cartes supplémentaires — **implémenté** (`ActionCarte.PIOCHE_SUPPLEMENTAIRE`,
  `Deck.piocher_cartes()`) : *Boost* jouable. Manque encore la durée pour *Multi fonction*
- Piocher puis défausser en une carte (*Changement d'outil*)
- Défausser toute la main puis repiocher autant (*Grand remplacement*)
- Défausser une **quantité choisie par le joueur** entre X et Y (*Cannibalisme*) — nécessite un
  sous-choix de quantité au moment de jouer la carte, en plus du ciblage habituel

### 12.10 Munitions limitées

Déjà spécifiées en §3.6/§7.4 (mécanique de jeu tranchée) — **implémenté** (`Carte.munitions_max`/
`munitions_restantes`, pile `Deck.cartes_epuisees`) : *Réparation* jouable. Reste bloqué par
d'autres mécaniques manquantes pour les autres cartes à munitions (*Bouclier perpétuel,
Optimisation des boucliers, Attaques performantes*, qui ont toutes en plus besoin du type Buff).

### 12.11 Note annexe : cible des cartes Soute

Les 6 cartes du module Soute (pioche/défausse/électricité) portaient une cible "Ennemi Tous" dans le
tableau source, incohérente pour des cartes qui ne visent aucun ennemi. Corrigé dans
`config/cartes.json` : elles se jouent en cliquant **n'importe quel module allié**, dont l'identité
n'a aucune influence sur l'effet (celui-ci porte sur le deck ou l'électricité, ressources communes
au vaisseau, pas sur le module cliqué).
