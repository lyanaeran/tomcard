# Doc de force — Jeu de deckbuilding roguelike (thème vaisseau spatial)

*Document de conception — v0.1*

---

## 1. Pitch

Un deckbuilder roguelike inspiré de Slay the Spire, où le joueur incarne un vaisseau spatial composé de **modules**. Chaque module possède son propre deck de compétences. Contrairement à Slay the Spire, il n'y a pas de héros unique ni de carte de monde classique : le joueur avance à travers une série de choix à chaque tour, en gérant la survie et la progression de son vaisseau.

---

## 2. Boucle de jeu (structure de run)

- Pas de carte de progression classique : **un choix à faire à chaque tour**
- Options possibles à chaque étape :
  - **Combat** — contrat de chasseur de primes, plusieurs types de rencontres possibles
  - **Auberge** — fonction à définir (repos, achat, amélioration ?)
  - **Camper** — fonction à définir
  - *(autres types d'étapes à imaginer)*

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

### 3.4 Destruction de module
- Un module à **0 PV est détruit**, même si le combat est gagné (perte permanente)
- Le **module de base** est la condition de game over : sa destruction termine la run

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

- **Proposition : 4 à 6 slots actifs**, plafond à 6
  - Début de run : module de base + 1 module (2 slots)
  - +1 slot débloqué tous les 2-3 combats/événements, jusqu'à 6
  - Le module de base occupe toujours un slot et reste équipé
- **Doublons de modules** : à trancher — proposition initiale : **interdire les doublons** (un archétype par run) pour forcer la diversité et simplifier l'équilibrage en v1

---

## 6. Progression des modules / cartes

- Après un combat gagné, le joueur reçoit une nouvelle carte
- Possibilité de choisir (ou non) **quel module** reçoit cette carte

---

## 7. Types de cartes

| Type | Portée | Persistance |
|---|---|---|
| **Attaque** | Cible ennemie | Le combat en cours |
| **Compétence** | Soi/allié/ennemi | Le combat en cours |
| **Pouvoir** | Le vaisseau entier | Le combat en cours (comme StS) |
| **Installation** *(à trancher)* | Un module spécifique | Toute la run |

**Installation vs Relique classique** — point encore ouvert :
- **Relique classique (façon StS)** : effet global sur le vaisseau/la run (ex : +1⚡/tour), indépendant des cartes
- **Installation** : effet passif attaché à **un module précis**, qui modifie ses cartes (ex : "les cartes de ce module coûtent 1⚡ de moins")
- Question non tranchée : garder les deux systèmes séparés (deux couches de personnalisation : run globale + spécialisation par module), ou fusionner en un seul concept de relique (globale ou ciblée) pour éviter la redondance

---

## 8. Points encore à trancher

- Thème définitif (vaisseau spatial est la piste actuelle, mais pas encore 100% figé)
- Contenu exact de l'Auberge et du Camp
- Mécanique précise du "choix à chaque tour" (aléatoire ? révélé à l'avance ? jauge ?)
- Ordre de jeu en combat : libre (comme StS) ou basé sur une initiative/vitesse par module ?
- Régénération des PV de module entre combats : automatique ou uniquement via Réparation ?
- Nombre de slots équipables (proposition : 4-6) et autorisation ou non des doublons de modules
- Installation vs Relique classique : systèmes séparés ou fusionnés ?
