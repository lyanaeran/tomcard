# Synthèse de simulation — combat de la refonte — 11 novembre 2026

> **Mise à jour** : après cette campagne, l'utilisateur a jugé le réglage 5 / 7 / 8 trop haut et
> retenu **Bouclier 4, Protéger le vaisseau 6, Blindage ciblé 8**, **non simulé** à ce jour. Les
> chiffres ci-dessous sont ceux du réglage 5 / 7 / 8.

*Campagne refaite le même jour avec les **nouvelles valeurs de bouclier** (décision utilisateur) :
Bouclier 5, Protéger le vaisseau 7, Blindage ciblé 8. Les campagnes précédentes (boucliers à 3, 5
et 6) restent dans l'historique git de ce fichier ; la comparaison est faite au §6.*

## État du jeu testé

| | |
|---|---|
| **Date de la campagne** | 2026-11-11, 19 h 07 |
| **Code** | branche `devjeux` (PR #61) : `CombatNew` après les deux reviews, simulateur `outils/simulation/bot_new.py` et `combats_new.py`, boucliers 5 / 7 / 8 dans `config/carte_new.json`. Aucune règle de jeu modifiée pour la simulation |
| **Règles** | **Règles de la refonte**, telles que codées dans `src/gameplay/combat_new.py` (`specs/refonte-combat.md`) : statuts partagés (bouclier et incendie −1 par tour, renvoi cumulable jusqu'au tour suivant, leurre), cycles d'actions des ennemis avec montée des valeurs, pile Hors service, défaite seulement si le principal est détruit |
| **Joueur** | Principal 60 PV, Lanceur de missiles 20 PV (avant gauche). 3 électricité, 5 cartes par tour. Deck **« départ »** : deck de départ (Laser ×4, Bouclier ×4, Protéger le vaisseau, Réparation) + 1 carte du Lanceur au hasard. Deck **« étoffé »** : le même + 5 cartes revues hors Base au hasard (milieu de partie) |
| **Cartes** | Les 19 cartes de `config/carte_new.json`, **y compris celles que l'ancien moteur ne sait pas jouer** (Missiles, Torpille, incendie, répétitions) : `CombatNew` les gère toutes. **Boucliers : Bouclier 5, Protéger le vaisseau 7, Blindage ciblé 8** |
| **Ennemis** | Les 6 ennemis de `config/ennemi_new.json` (dégâts +1 tous les 3 tours, Boss +2), coefficient 1. Placement comme le jeu actuel (protecteur devant, protégé derrière) |
| **Joueur automatique** | Bot « recherche » en faisceau (6 états par profondeur, noté après la réponse ennemie simulée), avec la **valeur des lancements en plus** pour les cartes de répétition (idée utilisateur, §7) |
| **Volume** | **5 872 combats** : 2 000 combats du bot aléatoire (robustesse), 42 combats de validation, 1 260 combats isolés du bot de recherche (21 flottes × 2 decks × 30), 300 enchaînements des niveaux 2 à 10 (2 570 combats) |
| **Durée** | 2 min 41 s sur 8 cœurs, lancé avec `caffeinate -i` |
| **Reproduire** | `caffeinate -i python -m outils.simulation.combats_new --graines 30 --robustesse 2000 --enchainements 300 --graine 1` ; résultats bruts dans `outils/simulation/resultats/2026-11-11_1907_combats_new.*` (non versionnés) |

**Pas de partie complète** : le combat de la refonte n'est pas encore branché au parcours (pas de
récompenses, de Station ni d'Aventures). L'« enchaînement » (§4) est une **approximation** : un
combat par niveau, PV du principal reportés, sans aucun soin hors combat.

---

## En bref

1. **Tout va bien côté moteur** : 5 872 combats, **aucune erreur, aucun invariant violé**.
2. **Miroir n'est plus un problème** : aucun combat enlisé, 5 à 28 dégâts renvoyés par combat
   selon la flotte.
3. **Les nouveaux boucliers rendent le jeu nettement plus facile** (§6) : sur l'enchaînement, les
   parties qui battent le Boss passent de **32 % à 59 %** ; le Boss avec le deck de départ passe de
   37 % à **97 %** de victoires.
4. **Les combats à un ennemi (niveaux 2 à 5) restent trop faciles** : 100 % de victoires, 2 à 3 PV
   perdus.
5. **Les combats à deux ennemis restent le cœur de la difficulté**, surtout avec **Le nettoyeur**
   : 13 à 15 PV perdus en moyenne par paire, jusqu'à 40 avec Le nettoyeur + Le puzzle.
6. **Le Boss redevient facile avec un deck étoffé** (100 %, 17 PV perdus) ; il ne tue plus que les
   principaux déjà très entamés.
7. **On ne joue pas plus de Bouclier, mais chacun rapporte plus** : environ un tous les deux tours,
   à 3 comme à 5, parce que l'électricité manque (§6.1) ; les cartes de bouclier remplacent en
   partie le Leurre et la Réparation.

---

## 1. Robustesse : le moteur tient

| Étude | Combats | Exceptions | Combats avec un invariant violé |
|---|---|---|---|
| Bot aléatoire (robustesse) | 2 000 | 0 | 0 |
| Validation (les deux bots) | 42 | 0 | 0 |
| Bot de recherche (équilibre) | 1 260 | 0 | 0 |
| Enchaînements (bot de recherche) | 2 570 | 0 | 0 |

Après **chaque carte jouée et chaque fin de tour**, le simulateur vérifie : une seule pile par
carte et aucune carte perdue, main limitée à 10, électricité jamais négative, tour qui ne recule
pas, PV entre 0 et le maximum, aucun statut à 0, module détruit sans statuts et avec toutes ses
cartes non Persistantes en Hors service, victoire et défaite au bon moment, détail des dégâts du
journal cohérent, **attaques ennemies conformes à leur intention**.

## 2. Le bot est-il fiable ?

| Bot | Combats | Victoires | PV principal perdus |
|---|---|---|---|
| Recherche | 42 | 98 % | 14,4 |
| Aléatoire | 42 | 57 % | 36,7 |

Sur les mêmes combats, le bot de recherche gagne nettement plus et perd 2,5 fois moins de PV. Ses
résultats servent à **comparer** ; un joueur humain attentif fera sans doute un peu mieux.

## 3. Combats isolés (principal à 60 PV)

### 3.1 Un ennemi (niveaux 2 à 5)

| Ennemi | Deck | Victoires | Tours | PV principal perdus (moy. / max) | Lanceur détruit |
|---|---|---|---|---|---|
| Pat le Pirate | départ | 100 % | 4,1 | 1,8 / 10 | 0 % |
| Le nettoyeur | départ | 100 % | 2,4 | 5,3 / 18 | 0 % |
| Petit Jean | départ | 100 % | 10,4 | 0,2 / 3 | 0 % |
| Le puzzle | départ | 100 % | 4,3 | 2,2 / 10 | 0 % |
| Miroir | départ | 100 % | 6,1 | 1,8 / 9 | 0 % |

**Aucun combat à un ennemi n'est une menace** (2,2 PV perdus en moyenne avec le deck de départ,
3,5 avec le deck étoffé).

### 3.2 Deux ennemis (niveaux 6 à 9)

| Flotte | Deck | Victoires | Défaites | Tours | PV principal perdus (moy. / max) | Lanceur détruit |
|---|---|---|---|---|---|---|
| Le nettoyeur + Le puzzle | départ | **80 %** | 20 % | 5,5 | **40,0** / 60 | 40 % |
| Le nettoyeur + Le puzzle | étoffé | 100 % | 0 % | 4,5 | 24,8 / 57 | 33 % |
| Pat + Le nettoyeur | départ | 100 % | 0 % | 6,1 | **35,9** / 57 | 40 % |
| Pat + Le nettoyeur | étoffé | 100 % | 0 % | 4,4 | 22,9 / 58 | 43 % |
| Le nettoyeur + Le nettoyeur | départ | 100 % | 0 % | 4,6 | 26,4 / 52 | 70 % |
| Le nettoyeur + Le nettoyeur | étoffé | 97 % | 3 % | 3,4 | 23,2 / 60 | 67 % |
| Le puzzle + Le puzzle | départ | 100 % | 0 % | 8,1 | 19,9 / 29 | **100 %** |
| Pat + Le puzzle | départ | 100 % | 0 % | 7,8 | 18,0 / 37 | 73 % |
| Petit Jean + Petit Jean | départ | 100 % | 0 % | **19,0** | 15,8 / 57 | 57 % |
| Petit Jean + Le puzzle | départ | 100 % | 0 % | 14,4 | 12,7 / 43 | 57 % |
| Le nettoyeur + Petit Jean | départ | 100 % | 0 % | 13,1 | 12,2 / 37 | 37 % |

(Tableau complet en annexe.)

- **Le nettoyeur** (2 attaques de 7) reste l'ennemi le plus dangereux en paire : les 4 paires les
  plus coûteuses le contiennent. Un bouclier aide peu contre lui : les combats durent 4 à 6 tours,
  le meilleur moyen de se protéger est de le tuer vite.
- **Le puzzle** (frappe tous les modules) détruit presque toujours le Lanceur.
- **Petit Jean** allonge les combats (19 tours à deux) sans être mortel.
- En moyenne par paire : 15,4 PV perdus avec le deck de départ, 12,9 avec le deck étoffé.

### 3.3 Le Boss

| Deck | Victoires | Tours | PV principal perdus (moy. / max) |
|---|---|---|---|
| départ | **97 %** | 14,7 | 38,5 / 60 |
| étoffé | **100 %** | 10,1 | 17,0 / 45 |

Avec le principal plein, le Boss ne fait plus peur. Il reste coûteux pour un deck de départ
(38 PV perdus) : un principal entamé peut encore y mourir.

## 4. Enchaînement des niveaux 2 à 10 (approximation d'une partie)

Un combat par niveau, flottes tirées comme aujourd'hui (1 ennemi jusqu'au niveau 5, 2 ensuite, Boss
au 10), PV du principal reportés, **aucun soin hors combat** (ni Station, ni Aventure). Deck départ
jusqu'au niveau 5, étoffé ensuite.

| Niveau | Parties encore en vie | PV du principal au début | PV perdus pendant le niveau (nets, Réparation comprise) |
|---|---|---|---|
| 2 | 100 % | 60,0 | 2,1 |
| 3 à 5 | 100 % | 57,9 → 56,9 | moins de 1 |
| 6 | 100 % | 56,5 | **12,9** |
| 7 | 99 % | 44,0 | 9,0 |
| 8 | 95 % | 36,5 | 7,6 |
| 9 | 86 % | 31,9 | 6,2 |
| 10 (Boss) | 76 % | 28,9 | 9,3 |

**59 % des parties battent le Boss.** Les défaites viennent du Boss (51 parties, avec un principal
déjà bas : 16 PV en moyenne à l'arrivée, contre 33 pour les parties gagnées) et des paires avec Le
nettoyeur (Le nettoyeur + Le puzzle 16, Pat + Le nettoyeur 13, Le nettoyeur + Petit Jean 12, Le
nettoyeur + Le nettoyeur 10).

- Le jeu complet aura des Stations (niveaux 5 et 9) : ces chiffres sont un plancher, à refaire après
  le branchement au parcours.
- **La difficulté reste mal répartie** : rien ne se passe aux niveaux 2 à 5, tout se joue de 6 à 10.

## 5. Mesures de la refonte

| Mesure | Valeur |
|---|---|
| Lanceur détruit | 40 % des combats isolés, au tour 4,5 en moyenne |
| Cartes en Hors service à la fin (si le Lanceur est détruit) | 2,3 en moyenne |
| Dégâts absorbés par le bouclier des modules | 21,3 par combat |
| Dégâts d'incendie infligés | 22,3 par combat en moyenne (sur tous les combats) |
| Combats enlisés (arrêtés à 40 tours) | **0** |

## 6. Bouclier : effet des nouvelles valeurs

Les trois cartes de bouclier sont passées de 3 / 5 / 6 à **5 / 7 / 8** (décision utilisateur,
après l'essai `essai_bouclier_2026-11-11.md`, qui garde les essais à 3, 4, 5 et 6). Comparaison sur
les mêmes combats et les mêmes graines :

| | Boucliers 3 / 5 / 6 | **Boucliers 5 / 7 / 8** |
|---|---|---|
| Combats isolés : victoires | 97,1 % | **99,4 %** |
| Combats isolés : PV principal perdus | 15,7 | **12,1** |
| Un ennemi, deck départ : PV perdus | 3,3 | 2,2 |
| Deux ennemis, deck départ : PV perdus | 22,3 | **15,4** |
| Deux ennemis, deck étoffé : PV perdus | 14,6 | 12,9 |
| Boss, deck départ : victoires / PV perdus | 37 % / 48,7 | **97 % / 38,5** |
| Boss, deck étoffé : victoires / PV perdus | 97 % / 23,4 | **100 % / 17,0** |
| Enchaînement : parties qui battent le Boss | 32 % | **59 %** |
| Dégâts absorbés par les boucliers / combat | 14,9 | 21,3 |

### 6.1 Qui joue quoi

| Carte | Taux de jeu (3 / 5 / 6) | Taux de jeu (5 / 7 / 8) |
|---|---|---|
| Bouclier (5) | 24 % | 26 % |
| Protéger le vaisseau (7) | 53 % | 53 % |
| Blindage ciblé (8) | 19 % | **11 %** |
| Bouclier stabilisé (fait lancer Bouclier 2 fois) | 6 % | 13 % |
| Réparation | 51 % | **43 %** |
| Leurre | 50 % | **35 %** |

- **Le taux de jeu de Bouclier (24 % → 26 %) est trompeur** : il compte chaque exemplaire en main.
  Par tour, avec le deck de départ :

  | | Boucliers 3 / 5 / 6 | Boucliers 5 / 7 / 8 |
  |---|---|---|
  | Électricité dépensée par tour (sur 3) | 2,86 | 2,87 |
  | Laser : en main / joués par tour | 1,95 / 1,57 | 1,92 / 1,55 |
  | Bouclier : en main / joués par tour | 1,92 / 0,47 | 1,89 / 0,51 |
  | Part de l'électricité : Laser / Bouclier | 55 % / 17 % | 54 % / 18 % |

  L'électricité est presque toujours dépensée en entier ; le Laser passe en premier (80 % des
  Lasers en main sont joués) et le Bouclier prend ce qui reste, **environ un tous les deux tours, à
  3 comme à 5**. Ce n'est donc pas une carte faible mais une carte moins prioritaire quand
  l'électricité manque. Remonter sa valeur ne change pas combien on en joue, mais ce que chacun
  rapporte (dégâts absorbés 14,9 → 21,3 par combat).
- **Blindage ciblé recule** (19 % → 11 %) : à 8 pour un coût de 2, il fait à peine mieux que
  Bouclier à 5 pour 1.
- **Les boucliers remplacent en partie le Leurre et la Réparation** : mieux vaut éviter les dégâts
  que les réparer.

### 6.2 Accumulation

La campagne ne mesure pas le bouclier maximal ; l'essai dédié l'a fait sur 32 combats
(`essai_bouclier_2026-11-11.md`) : avec Bouclier à 5, le bouclier d'un module monte jusqu'à 21
dans les combats difficiles et **jusqu'à 44 contre Petit Jean seul**, sans changer l'issue de ces
combats (déjà gagnés sans perte). À surveiller, aucun frein ajouté pour l'instant.

### 6.3 À retenir

- Les nouveaux boucliers **règlent le problème du Boss trop dur** et rendent les paires moins
  coûteuses, mais **ne règlent pas** le déséquilibre entre les niveaux 2 à 5 (trop faciles) et 6 à
  9 (Le nettoyeur), ni la faible utilisation de la carte Bouclier.
- Le jeu devient **plutôt facile** pour le bot (99,4 % de combats gagnés) : le prochain levier est la
  composition des flottes (coefficient de difficulté par niveau), pas les cartes.
- **Blindage ciblé** mérite d'être revu (coût 1 ? effet en plus ?) s'il doit rester un choix.

## 7. Le bot et les cartes de répétition (idée utilisateur)

**Problème** : une première campagne ne jouait jamais *Protocole d'urgence* ni *Bouclier
stabilisé*, et *Salve laser* 10 % du temps. La recherche du bot ne voit que le tour suivant, alors
qu'une répétition ne paie que sur les tours d'après.

**Correction (idée utilisateur)** : le bot donne une valeur à l'**amélioration du deck**. Pour
chaque carte encore jouable (pioche, main, défausse) qui a des lancements en plus :

> lancements en plus × valeur d'un lancement × nombre de fois où la carte sera encore jouée

- **valeur d'un lancement** : somme de ses effets (dégâts comptés comme des PV ennemis en moins,
  multipliés par le nombre d'ennemis pour une carte de zone ; bouclier, réparation, incendie,
  leurre, pioche, électricité avec leur propre poids) ;
- **nombre de fois où elle sera encore jouée** : tours restants estimés × chance de la piocher (5
  cartes sur le deck actif) × 70 % ;
- **tours restants** : 10 moins le numéro du tour : **plus le combat est jeune, plus l'amélioration
  vaut**.

Un premier essai estimait les tours restants d'après les PV des ennemis : le bot gagnait alors des
points à **ne pas frapper**, et des combats s'enlisaient. Le numéro du tour, sur lequel le bot n'a
pas de prise, règle le problème.

Effet (boucliers à 3 / 5 / 6, mêmes combats) : *Salve laser* 10 % → 74 % de jeu, *Protocole
d'urgence* 0 % → 63 %, parties de l'enchaînement qui battent le Boss 14 % → 32 %. Ces cartes
étaient **sous-estimées par le bot**, pas mauvaises. L'autre idée de l'utilisateur (jouer la carte
avant et après amélioration pour comparer) demande de simuler plusieurs tours à l'avance pour
chaque essai : gardée en réserve.

## 8. Cartes

« En main / tour » et « jouée / tour » sont comptés sur les tours des combats où la carte était
dans le deck : ils sont plus parlants que le taux de jeu pour une carte en plusieurs exemplaires.

| Carte | Coût | Taux de jeu | En main / tour | Jouée / tour | Part de l'électricité dépensée |
|---|---|---|---|---|---|
| Missiles | 2 | 76 % | 0,34 | 0,25 | 4 % |
| Ciel de missiles | 1 | 76 % | 0,32 | 0,25 | 2 % |
| Salve laser | 2 | 74 % | 0,37 | 0,27 | 2 % |
| Laser | 1 | 73 % | 1,70 | **1,23** | **44 %** |
| Laser lourd | 1 | 72 % | 0,36 | 0,25 | 1 % |
| Bombardement | 1 | 68 % | 0,33 | 0,22 | 2 % |
| Embrasement | 2 | 65 % | 0,35 | 0,23 | 3 % |
| Protocole d'urgence | 3 | 64 % | 0,37 | 0,24 | 3 % |
| Torpille | 2 | 59 % | 0,32 | 0,19 | 3 % |
| Protéger le vaisseau | 1 | 53 % | 0,42 | 0,22 | 8 % |
| Guerre nucléaire | 3 | 52 % | 0,37 | 0,19 | 4 % |
| Réparation | 1 | 43 % | 0,34 | 0,15 | 5 % |
| Laser perçant | 2 | 38 % | 0,37 | 0,14 | 1 % |
| Leurre | 1 | 35 % | 0,33 | 0,12 | 1 % |
| Tir incendiaire | 2 | 33 % | 0,36 | 0,12 | 1 % |
| Bouclier | 1 | 26 % | 1,66 | **0,44** | **16 %** |
| Bouclier stabilisé | 3 | 13 % | 0,32 | 0,04 | 1 % |
| Ligne arrière | 1 | 12 % | 0,33 | 0,04 | 0 % |
| Blindage ciblé | 2 | 11 % | 0,39 | 0,04 | 0 % |

- **Bouclier est la deuxième carte du jeu en électricité dépensée** (16 %, après le Laser) : son
  faible taux de jeu vient du nombre d'exemplaires, pas d'un manque d'intérêt.

- **Les cartes d'attaque dominent** : tuer vite reste la meilleure défense, d'autant que les
  dégâts ennemis montent avec le temps.
- **Ligne arrière** (12 %) n'a de cible que si un ennemi est à l'arrière, ce qui est rare avec 1 ou
  2 ennemis.

## 9. Pistes (à décider par l'utilisateur)

1. **Répartir la difficulté** : rendre les niveaux 2 à 5 plus menaçants (coefficient de difficulté
   par niveau, ou deux ennemis plus tôt). Avec les nouveaux boucliers, le jeu est devenu plutôt
   facile : c'est le levier prioritaire (`specs/refonte-ennemis.md` §5, flottes laissées pour plus
   tard).
2. **Le nettoyeur** : ses 2 attaques de 7 restent les plus coûteuses (4 paires les plus mortelles).
   Baisser à 6 si c'est encore vrai après le travail sur les flottes.
3. **Le Boss** : n'est plus trop dur ; à revoir seulement avec la composition des flottes.
4. **Petit Jean** : seul, un combat long et sans risque (10 tours, 0,2 PV perdu). Lui donner un peu
   de mordant, ou moins de PV.
5. **Blindage ciblé** (8 pour 2) : peu joué face à Bouclier (5 pour 1) ; à revoir s'il doit rester
   un choix.
6. **Accumulation du bouclier** : à surveiller (jusqu'à 44 contre Petit Jean) ; freins possibles
   dans `essai_bouclier_2026-11-11.md`.
7. **Répétitions** : *Salve laser* et *Protocole d'urgence* sont parmi les cartes les plus fortes ;
   à surveiller en jeu réel.
8. **Après le branchement au parcours** : relancer des parties complètes (Stations, récompenses)
   pour caler les PV du principal (60) et du Lanceur (20).

---

## Annexe : toutes les flottes (boucliers 5 / 7 / 8)

| Flotte | Deck | Victoires | Défaites | Tours | PV principal perdus (moy. / max) | Lanceur détruit | Renvoi subi |
|---|---|---|---|---|---|---|---|
| Pat | départ | 100 % | 0 % | 4,1 | 1,8 / 10 | 0 % | 0,0 |
| Pat | étoffé | 100 % | 0 % | 3,9 | 3,5 / 15 | 0 % | 0,0 |
| Le nettoyeur | départ | 100 % | 0 % | 2,4 | 5,3 / 18 | 0 % | 0,0 |
| Le nettoyeur | étoffé | 100 % | 0 % | 2,2 | 4,2 / 16 | 7 % | 0,0 |
| Petit Jean | départ | 100 % | 0 % | 10,4 | 0,2 / 3 | 0 % | 0,0 |
| Petit Jean | étoffé | 100 % | 0 % | 7,8 | 1,5 / 12 | 0 % | 0,0 |
| Le puzzle | départ | 100 % | 0 % | 4,3 | 2,2 / 10 | 0 % | 0,0 |
| Le puzzle | étoffé | 100 % | 0 % | 3,8 | 6,0 / 16 | 7 % | 0,0 |
| Miroir | départ | 100 % | 0 % | 6,1 | 1,8 / 9 | 0 % | 16,8 |
| Miroir | étoffé | 100 % | 0 % | 4,4 | 2,2 / 8 | 3 % | 9,7 |
| Pat + Pat | départ | 100 % | 0 % | 8,5 | 4,9 / 20 | 53 % | 0,0 |
| Pat + Pat | étoffé | 100 % | 0 % | 5,4 | 8,5 / 22 | 37 % | 0,0 |
| Pat + Le nettoyeur | départ | 100 % | 0 % | 6,1 | 35,9 / 57 | 40 % | 0,0 |
| Pat + Le nettoyeur | étoffé | 100 % | 0 % | 4,4 | 22,9 / 58 | 43 % | 0,0 |
| Pat + Petit Jean | départ | 100 % | 0 % | 13,9 | 5,9 / 33 | 13 % | 0,0 |
| Pat + Petit Jean | étoffé | 100 % | 0 % | 9,1 | 3,8 / 25 | 20 % | 0,0 |
| Pat + Le puzzle | départ | 100 % | 0 % | 7,8 | 18,0 / 37 | 73 % | 0,0 |
| Pat + Le puzzle | étoffé | 100 % | 0 % | 5,9 | 15,9 / 36 | 63 % | 0,0 |
| Pat + Miroir | départ | 100 % | 0 % | 8,9 | 5,1 / 19 | 37 % | 9,3 |
| Pat + Miroir | étoffé | 100 % | 0 % | 6,0 | 6,0 / 27 | 23 % | 7,2 |
| Le nettoyeur + Le nettoyeur | départ | 100 % | 0 % | 4,6 | 26,4 / 52 | 70 % | 0,0 |
| Le nettoyeur + Le nettoyeur | étoffé | 97 % | 3 % | 3,4 | 23,2 / 60 | 67 % | 0,0 |
| Le nettoyeur + Petit Jean | départ | 100 % | 0 % | 13,1 | 12,2 / 37 | 37 % | 0,0 |
| Le nettoyeur + Petit Jean | étoffé | 100 % | 0 % | 8,9 | 13,1 / 46 | 20 % | 0,0 |
| Le nettoyeur + Le puzzle | départ | 80 % | 20 % | 5,5 | 40,0 / 60 | 40 % | 0,0 |
| Le nettoyeur + Le puzzle | étoffé | 100 % | 0 % | 4,5 | 24,8 / 57 | 33 % | 0,0 |
| Le nettoyeur + Miroir | départ | 100 % | 0 % | 8,1 | 10,1 / 40 | 50 % | 17,7 |
| Le nettoyeur + Miroir | étoffé | 100 % | 0 % | 5,4 | 16,2 / 56 | 37 % | 11,0 |
| Petit Jean + Petit Jean | départ | 100 % | 0 % | 19,0 | 15,8 / 57 | 57 % | 0,0 |
| Petit Jean + Petit Jean | étoffé | 100 % | 0 % | 10,3 | 4,0 / 24 | 23 % | 0,0 |
| Petit Jean + Le puzzle | départ | 100 % | 0 % | 14,4 | 12,7 / 43 | 57 % | 0,0 |
| Petit Jean + Le puzzle | étoffé | 100 % | 0 % | 9,3 | 12,4 / 58 | 67 % | 0,0 |
| Petit Jean + Miroir | départ | 100 % | 0 % | 14,7 | 3,8 / 27 | 20 % | 5,5 |
| Petit Jean + Miroir | étoffé | 100 % | 0 % | 9,6 | 3,3 / 38 | 33 % | 9,2 |
| Le puzzle + Le puzzle | départ | 100 % | 0 % | 8,1 | 19,9 / 29 | 100 % | 0,0 |
| Le puzzle + Le puzzle | étoffé | 100 % | 0 % | 5,7 | 20,6 / 42 | 97 % | 0,0 |
| Le puzzle + Miroir | départ | 100 % | 0 % | 9,1 | 15,1 / 36 | 73 % | 8,7 |
| Le puzzle + Miroir | étoffé | 100 % | 0 % | 6,2 | 14,5 / 35 | 93 % | 9,3 |
| Miroir + Miroir | départ | 100 % | 0 % | 10,4 | 4,5 / 17 | 37 % | 27,8 |
| Miroir + Miroir | étoffé | 100 % | 0 % | 7,0 | 4,5 / 26 | 33 % | 17,9 |
| Boss | départ | 97 % | 3 % | 14,7 | 38,5 / 60 | 100 % | 0,0 |
| Boss | étoffé | 100 % | 0 % | 10,1 | 17,0 / 45 | 100 % | 0,0 |

Aucun combat enlisé dans aucune flotte.
