# Space Fight — POC (preuve de concept)

*Spécification minimale pour un premier combat jouable — dérivée de `specs.md`*

---

## 1. Objectif

Un combat sur la grille complète (module de base + 4 modules équipés du joueur, contre plusieurs ennemis), pour valider le placement 2x3, le ciblage à cible multiple et le ciblage automatique des ennemis — en plus de la boucle de combat déjà validée dans la version précédente du POC (jouer des cartes, dépenser de l'électricité, infliger des dégâts, encaisser une attaque).

Simplifications restantes par rapport à `specs.md` : pas de boucle de run (pas d'étapes, pas de boss, pas de récompense de cartes), pas d'ennemis de taille L (point encore ouvert en specs.md §9.1, volontairement évité ici). Un seul combat, une seule fois.

**⚠️ Toutes les valeurs numériques de ce document (PV, dégâts, coûts) sont inventées faute d'être spécifiées ailleurs — à ajuster après test.**

---

## 2. Vaisseau du joueur

Grille **2 colonnes (Avant / Arrière) x 3 rangées (Gauche / Mid / Droite)**, comme décrit en specs.md §3.1/§5. La colonne Avant fait face à l'ennemi. Le module de base occupe la rangée Mid en entier (les deux colonnes) ; les 4 autres modules équipés occupent chacun une case.

| Module | Position | PV | Attaque | Bouclier | Soin |
|---|---|---|---|---|---|
| Base | Mid | 15 | 7 | 5 | 4 |
| Avant-Gauche | avant / gauche | 12 | 9 | 4 | 3 |
| Avant-Droite | avant / droite | 18 | 5 | 7 | 3 |
| Arrière-Gauche | arrière / gauche | 10 | 4 | 3 | 6 |
| Arrière-Droite | arrière / droite | 9 | 10 | 2 | 2 |

Chaque module a son propre jeu des 3 cartes déjà utilisées (Attaque/Bouclier/Soin, cf. §4), avec ses propres valeurs — toutes les cartes coûtent 1⚡.

- **Électricité** : 3 par tour (ressource pleine à chaque début de tour, ne se cumule pas d'un tour à l'autre)
- **Main** : capacité maximale de **10 cartes** ; le joueur pioche **5 cartes par tour**
- Cartes jouées partent en défausse ; quand la pioche est vide, la défausse est mélangée pour reformer la pioche (comme Slay the Spire, cf. specs.md §3.3)
- Un module (autre que la base) à 0 PV est détruit mais **ne met pas fin au combat** ; seule la destruction de la base termine la run (specs.md §3.4)

---

## 3. Ennemis

Grille miroir **2 colonnes (Avant / Arrière) x 3 rangées (Gauche / Mid / Droite)**, la colonne Avant faisant face au joueur. Pas de base côté ennemi : les 6 cases sont indépendantes, certaines peuvent rester vides.

| Ennemi | Taille | Position | PV | Dégâts |
|---|---|---|---|---|
| S1 | S | avant / gauche | 8 | 4 |
| M1 | M | avant / droite | 16 | 8 |
| S2 | S | arrière / gauche | 8 | 4 |
| M2 | M | arrière / mid | 16 | 8 |

(avant/mid et arrière/droite restent vides dans ce POC)

**Ciblage automatique** : chaque ennemi attaque un seul module du joueur par tour, choisi ainsi :
1. Regarder sa **propre rangée** (celle où il se trouve) : d'abord la case Avant de cette rangée, puis la case Arrière de cette même rangée si l'Avant est vide/détruite
2. Si sa rangée entière est vide, passer à la **rangée la plus proche** (même règle avant-puis-arrière), et ainsi de suite
3. La rangée Mid contient toujours la base (tant qu'elle est vivante)

**Important** : la base ne protège pas les modules Arrière des autres rangées — un ennemi peut attaquer directement le module Arrière de sa propre rangée si l'Avant de cette rangée est vide, même si la base (Mid) est toujours en vie.

Un rayon (voir §6) matérialise chaque attaque. Au survol de la souris sur un ennemi vivant, une étiquette affiche la cible qu'il vise et les dégâts qu'il infligera ce tour, calculés avec la même règle.

---

## 4. Cartes

Chaque module a 3 cartes (Attaque/Défense/Soin), avec ses propres valeurs (tableau en §2) :

| Type | Cible | Effet |
|---|---|---|
| **Attaque** | Ennemi (au choix parmi les ennemis vivants) | Inflige des dégâts |
| **Bouclier** (Défense) | Allié (au choix parmi les modules vivants) | Donne du Bouclier |
| **Soin** | Allié (au choix parmi les modules vivants) | Répare des PV |

Contrairement à la version précédente du POC, une carte Bouclier/Soin peut désormais cibler **n'importe quel module allié vivant**, pas seulement celui dont elle provient.

Le Bouclier absorbe les dégâts subis avant les PV. Exemple : un module protégé par 5 Bouclier subit une attaque de 7 dégâts → le Bouclier absorbe 5, les **2 dégâts restants** sont retirés des PV.

---

## 5. Composition du deck

Un seul deck partagé pour tout le vaisseau, assemblé à partir des 5 kits de modules (même ratio que la version précédente, dupliqué x5) :

**45 cartes au total** : pour chacun des 5 modules, 5x Attaque + 3x Bouclier + 1x Soin (= 9 cartes/module)

---

## 6. Déroulé d'un tour

1. **Tour du joueur** : le joueur pioche 5 cartes, l'électricité est remise à 3. Le joueur joue librement les cartes de son choix (en choisissant la cible parmi les modules/ennemis vivants), dans l'ordre qu'il veut, tant qu'il a assez d'électricité (voir specs.md §3.3), puis clique sur le bouton **"Fin de tour"** pour passer la main
2. **Fin du tour joueur** : les cartes non jouées restant en main sont défaussées (voir specs.md §3.3)
3. **Tour de l'ennemi** : chaque ennemi vivant attaque automatiquement le module qu'il vise (règle de ciblage en §3), dans l'ordre de la grille. Un **rayon** apparaît brièvement entre chaque ennemi attaquant et sa cible pour visualiser l'attaque, puis disparaît. Si la base est détruite en cours de tour, les ennemis suivants n'agissent plus (la run est terminée)

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

Le rendu actuel (formes simples/rectangles, cf. §6-7) n'utilise pas encore les images disponibles dans `assets/` ni les fichiers de `config/` (voir ci-dessous) : c'est la prochaine étape d'intégration.

Conventions : classes claires par responsabilité, commentaires en français sans accents ni cédilles (cf. specs.md §10.3).

### Animation d'attaque

Quand un ennemi attaque, un rayon (ligne colorée) relie brièvement cet ennemi et le module qu'il vise, pour donner un retour visuel sur l'attaque. Le rayon s'estompe puis disparaît après une courte durée (~0.4 seconde). Plusieurs ennemis pouvant attaquer au même tour, plusieurs rayons peuvent apparaître simultanément (un par attaque résolue).

Cette animation est gérée entièrement côté `src/ui` (minuterie + dessin) : elle n'a aucun impact sur le moteur de jeu (`src/gameplay`), qui reste inchangé.

### Survol de la souris (intention ennemie)

Survoler un ennemi vivant avec la souris affiche une étiquette indiquant quel module il vise et les dégâts qu'il infligerait s'il attaquait maintenant. Calculé avec la même fonction de ciblage que celle utilisée pour la résolution réelle de l'attaque (pas de logique dupliquée), donc toujours cohérent avec ce qui va effectivement se passer.

### Fichiers de configuration (`config/`)

Trois fichiers JSON décrivent le contenu du jeu (modules, ennemis, cartes) de façon déclarative, référençant les images de `assets/`. **Préparation seulement pour l'instant : ces fichiers ne sont pas encore chargés par le moteur** (`src/gameplay/config_poc.py` continue d'utiliser des valeurs codées en dur). Ce sera une étape d'intégration ultérieure.

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
