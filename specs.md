# Space Fight

*Deckbuilder roguelike (vaisseaux spatiaux) — Document de conception — v0.1*

---

## 1. Pitch

Un deckbuilder roguelike inspiré de Slay the Spire, où le joueur incarne un vaisseau spatial composé de **modules**. Chaque module possède son propre deck de compétences. Contrairement à Slay the Spire, il n'y a pas de héros unique ni de carte de monde classique : le joueur avance à travers une série de choix à chaque tour, en gérant la survie et la progression de son vaisseau.

---

## 2. Boucle de jeu (structure de run)

- Pas de carte de progression classique : à chaque étape, le joueur ne voit que **la prochaine étape** (aucune visibilité au-delà)
- Types d'étapes possibles :
  - **PRIME** — combat, contrat de chasseur de primes. Affiche un niveau de difficulté / la composition annoncée des ennemis (tailles S/M/L, cf. 3.2) sans révéler le détail exact
  - **STATION SERVICE** — réparation du vaisseau (remonte les PV des modules). Logique d'apparition encore ouverte (voir §8), pistes à l'étude :
    - toujours disponible en alternative à chaque étape, ou
    - probabilité liée aux PV du vaisseau (voire garantie sous un seuil de dégâts), ou
    - garantie après un combat difficile (Prime dure ou Boss)
  - **PLANÈTE COMMERCIALE** — achat de cartes ou d'autres bonus
  - **AVENTURE** — événement inconnu, façon "?" de Slay the Spire
  - *(autres types d'étapes à imaginer)*
- **Boss** : revient toutes les *n* étapes (n à ajuster en playtest, indicatif 8-10)
  - Victoire sur un boss → le joueur choisit **1 nouveau module parmi 2 propositions**, avec ses cartes de base associées (deck de départ propre au module — détail à trancher une fois le système de cartes approfondi, voir §7)

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
- **Main** : capacité maximale de 10 cartes ; le joueur pioche 5 cartes par tour. Cartes jouées partent en défausse ; quand la pioche est vide, la défausse est mélangée pour reformer la pioche

### 3.4 Destruction de module
- Un module à **0 PV est détruit**, même si le combat est gagné (perte permanente)
- Le **module de base** est la condition de game over : sa destruction termine la run
- **Récupération entre combats** : aucune régénération automatique des PV — seule la Réparation (module dédié, voir 4.2) permet d'en restaurer. Le vaisseau garde ses dégâts d'un combat à l'autre, sauf passage par une Station Service (voir §2)

### 3.5 Bouclier
- Le Bouclier absorbe les dégâts subis **avant** les PV. Exemple : un module protégé par 5 Bouclier subit une attaque de 7 dégâts → le Bouclier absorbe 5, les **2 dégâts restants** sont retirés des PV

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

- Après un combat gagné, le joueur choisit **1 carte parmi 3 propositions**, pondérées par rareté (voir 7.3)
- Possibilité de choisir (ou non) **quel module** reçoit cette carte

---

## 7. Types de cartes

### 7.1 Types (par effet)

Classification par nature de l'effet — remplace l'ancien découpage par portée/persistance.

| Type | Description | Sous-catégories |
|---|---|---|
| **Attaque** | Inflige des dégâts | Direct / décalé (dégâts différés) / poison (dégâts sur la durée) |
| **Défense** | Protège un ou plusieurs modules | Bouclier absolu (x tours), réduction de dégâts en %, régénération de Bouclier sur la durée |
| **Contrôle** | Neutralise ou limite un ennemi | Stun, restriction d'action (ex : pas d'attaque ce tour) |
| **Debuff** | Affaiblit une cible ennemie | Plafond de dégâts infligés, réduction en %, réduction de Bouclier |
| **Buff** | Renforce le vaisseau ou un module | Augmentation de dégâts, augmentation de Bouclier |
| **Soin** | Répare les PV d'un module | (voir aussi module Réparation, §4.2) |
| **Outils** | Manipule la pioche/défausse ou l'électricité | Piocher, défausser, recycler... ; gagner/convertir de l'électricité |

### 7.2 Cible

Troisième axe, indépendant du type — n'importe quel type (pas seulement Attaque) peut cibler différents camps/motifs : une Défense peut protéger un allié unique ou tout le vaisseau, un Debuff peut viser un ennemi unique ou tout un rang, etc.

| Cible | Description |
|---|---|
| **Soi** | Le module qui joue la carte |
| **Allié unique** | Un module ami au choix (parfois avec contrainte : adjacent, à portée...) |
| **Alliés multiples / vaisseau entier** | Plusieurs modules ciblés, ou tout le vaisseau |
| **Ennemi unique** | Une cible ennemie, avec contraintes de rang possibles (rang avant uniquement, n'importe quel rang...) |
| **Ennemis multiples** | Motif fixe (ligne, colonne, rang entier) ou aléatoire, jusqu'à tous les ennemis |

### 7.3 Rareté

Axe indépendant du type et de la cible — une carte a un type, une cible **et** une rareté.

| Palier | Fréquence | Puissance |
|---|---|---|
| **Commune** | Fréquente | Effets simples et fiables, cœur du deck |
| **Rare** | Peu fréquente | Meilleur ratio effet/électricité, ou mécanique inédite |
| **Légendaire** | Très peu de cartes | Effets exceptionnels, peuvent changer la façon de jouer un module (ex : Reconstruction, §4.2) |

- La rareté pondère le tirage des **3 propositions** offertes après un combat gagné (§6) : plus une carte est rare, moins elle a de chances d'apparaître dans les propositions
- Le tag "rare" déjà présent sur *Reconstruction* (§4.2) sera à réévaluer : son effet (résurrection d'un module) correspond plutôt au palier **Légendaire**
- Rareté et attribution précise par carte (§4.1-4.3) : à faire dans une passe dédiée (voir §9.1 "compléter le jeu de cartes")

---

## 8. Interface / écran de combat

### 8.1 Disposition générale (wireframe)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SPACE FIGHT — ÉCRAN DE COMBAT                                  ⚡ Électricité: 3 │
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
- **Pioche et défausse** : regroupées ensemble dans un coin de l'écran (compteurs de nombre de cartes), séparées de la main

### 8.2 Formes visuelles

- **Modules du joueur et ennemis** : images **carrées**
- **Module de base** : exception, forme différente (plus grande, fond dédié qui englobe les 5 emplacements)
- **Cartes** : format **rectangulaire**

### 8.3 Interaction de jeu d'une carte

1. Clic sur une carte de la main → la carte se **surligne** (état "armée")
2. Clic sur une **cible valide** → la carte se résout, part en défausse, la surbrillance disparaît
3. Pour les cartes sans cible unique (Pouvoir, effet sur tout le vaisseau...) : le comportement exact (résolution automatique dès le clic vs. confirmation par un clic supplémentaire) **dépend du type de carte** — à détailler carte par carte lors de l'approfondissement du système de cartes (§7)

---

## 9. Points encore à trancher

### 9.1 Design / gameplay

- Contenu exact de la Planète commerciale et de l'Aventure
- Logique d'apparition de la Station Service : toujours disponible, liée aux PV du vaisseau, ou garantie après un combat difficile (voir §2)
- Fréquence exacte des Boss (valeur de *n* étapes)
- Cartes de base fournies avec un nouveau module choisi après un Boss : deck de départ fixe par module, à définir une fois le système de cartes approfondi (voir §7)
- Plafond exact de slots équipables (proposition actuelle : 5, base incluse) et autorisation ou non des doublons de modules
- Représentation visuelle d'un ennemi L occupant 2 emplacements (§3.2, §8.1) : rectangle fusionné sur les 2 cases, ou deux images liées logiquement ?
- Comportement exact des cartes sans cible unique lors du clic (§8.3) : à détailler carte par carte
- Compléter le jeu de cartes de chaque module : les archétypes de §4.3 (Bouclier énergétique, Radar, Propulseur, IA de combat, Générateur, Sabotage, Soute/Fret) n'ont pas encore de decks détaillés comme ceux de §4.1-4.2 ; les cartes déjà écrites en §4.1-4.2 n'ont pas encore de type/cible/rareté assignés (§7)

### 9.2 Technique / développement

- Organisation du code dans le dépôt (arborescence, séparation moteur de jeu / affichage / contenu des cartes...)
- Choix techniques : langage, framework et librairies à utiliser
