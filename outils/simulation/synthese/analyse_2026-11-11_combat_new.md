# Synthèse de simulation — combat de la refonte — 11 novembre 2026

*Campagne faite avec le **réglage actuel des boucliers** (décision utilisateur) : Bouclier 4,
Protéger le vaisseau 6, Blindage ciblé 8. Les réglages essayés avant (3 / 5 / 6, puis 5 / 7 / 8)
sont comparés au §6 ; leurs synthèses complètes restent dans l'historique git de ce fichier.*

## État du jeu testé

| | |
|---|---|
| **Date de la campagne** | 2026-11-11, 19 h 35 |
| **Code** | branche `devjeux` (PR #61) : `CombatNew`, simulateur `outils/simulation/bot_new.py` et `combats_new.py`, boucliers 4 / 6 / 8 dans `config/carte_new.json`. Aucune règle de jeu modifiée pour la simulation |
| **Règles** | **Règles de la refonte**, telles que codées dans `src/gameplay/combat_new.py` (`specs/refonte-combat.md`) : statuts partagés (bouclier et incendie −1 par tour, renvoi cumulable jusqu'au tour suivant, leurre), cycles d'actions des ennemis avec montée des valeurs, pile Hors service, défaite seulement si le principal est détruit |
| **Joueur** | Principal 60 PV, Lanceur de missiles 20 PV (avant gauche). 3 électricité, 5 cartes par tour. Deck **« départ »** : deck de départ (Laser ×4, Bouclier ×4, Protéger le vaisseau, Réparation) + 1 carte du Lanceur au hasard. Deck **« étoffé »** : le même + 5 cartes revues hors Base au hasard (milieu de partie) |
| **Cartes** | Les 19 cartes de `config/carte_new.json`, **y compris celles que l'ancien moteur ne sait pas jouer** (Missiles, Torpille, incendie, répétitions) : `CombatNew` les gère toutes. **Boucliers : Bouclier 4, Protéger le vaisseau 6, Blindage ciblé 8** |
| **Ennemis** | Les 6 ennemis de `config/ennemi_new.json` (dégâts +1 tous les 3 tours, Boss +2), coefficient 1. Placement comme le jeu actuel (protecteur devant, protégé derrière) |
| **Joueur automatique** | Bot « recherche » en faisceau (6 états par profondeur, noté après la réponse ennemie simulée), avec la **valeur des lancements en plus** pour les cartes de répétition (idée utilisateur, §7) |
| **Volume** | **5 811 combats** : 2 000 combats du bot aléatoire (robustesse), 42 combats de validation, 1 260 combats isolés du bot de recherche (21 flottes × 2 decks × 30), 300 enchaînements des niveaux 2 à 10 (2 509 combats) |
| **Durée** | 2 min 39 s sur 8 cœurs, lancé avec `caffeinate -i` |
| **Reproduire** | `caffeinate -i python -m outils.simulation.combats_new --graines 30 --robustesse 2000 --enchainements 300 --graine 1` ; résultats bruts dans `outils/simulation/resultats/2026-11-11_1935_combats_new.*` (non versionnés) |

**Pas de partie complète** : le combat de la refonte n'est pas encore branché au parcours (pas de
récompenses, de Station ni d'Aventures). L'« enchaînement » (§4) est une **approximation** : un
combat par niveau, PV du principal reportés, sans aucun soin hors combat.

---

## En bref

1. **Tout va bien côté moteur** : 5 811 combats, **aucune erreur, aucun invariant violé**.
2. **Miroir n'est plus un problème** : aucun combat enlisé, 5 à 29 dégâts renvoyés par combat
   selon la flotte.
3. **Le réglage 4 / 6 / 8 est un juste milieu** entre les deux réglages essayés (§6) : sur
   l'enchaînement, **45 % des parties battent le Boss** (32 % avec 3 / 5 / 6, 59 % avec 5 / 7 / 8).
4. **Les combats à un ennemi (niveaux 2 à 5) restent trop faciles** : 100 % de victoires, environ
   3 PV perdus.
5. **Les combats à deux ennemis restent le cœur de la difficulté**, surtout avec **Le nettoyeur** :
   14 à 19 PV perdus en moyenne par paire, jusqu'à 42 avec Le nettoyeur + Le puzzle.
6. **Le Boss reste exigeant avec le deck de départ** (63 % de victoires, 45 PV perdus avec le
   principal plein) mais facile avec un deck étoffé (100 %, 20 PV perdus) : il tue surtout les
   principaux déjà entamés.
7. **Le Bouclier est bien joué** : environ un tous les deux tours et 15 % de l'électricité dépensée,
   deuxième carte après le Laser. Son faible « taux de jeu » (25 %) vient du manque d'électricité,
   pas de sa faiblesse (§6.1).

---

## 1. Robustesse : le moteur tient

| Étude | Combats | Exceptions | Combats avec un invariant violé |
|---|---|---|---|
| Bot aléatoire (robustesse) | 2 000 | 0 | 0 |
| Validation (les deux bots) | 42 | 0 | 0 |
| Bot de recherche (équilibre) | 1 260 | 0 | 0 |
| Enchaînements (bot de recherche) | 2 509 | 0 | 0 |

Après **chaque carte jouée et chaque fin de tour**, le simulateur vérifie : une seule pile par
carte et aucune carte perdue, main limitée à 10, électricité jamais négative, tour qui ne recule
pas, PV entre 0 et le maximum, aucun statut à 0, module détruit sans statuts et avec toutes ses
cartes non Persistantes en Hors service, victoire et défaite au bon moment, détail des dégâts du
journal cohérent, **attaques ennemies conformes à leur intention**.

## 2. Le bot est-il fiable ?

| Bot | Combats | Victoires | PV principal perdus |
|---|---|---|---|
| Recherche | 42 | 95 % | 17,4 |
| Aléatoire | 42 | 55 % | 39,6 |

Sur les mêmes combats, le bot de recherche gagne nettement plus et perd plus de deux fois moins de
PV. Ses résultats servent à **comparer** ; un joueur humain attentif fera sans doute un peu mieux.

## 3. Combats isolés (principal à 60 PV)

### 3.1 Un ennemi (niveaux 2 à 5)

| Ennemi | Deck | Victoires | Tours | PV principal perdus (moy. / max) | Lanceur détruit |
|---|---|---|---|---|---|
| Pat le Pirate | départ | 100 % | 4,1 | 1,9 / 10 | 0 % |
| Le nettoyeur | départ | 100 % | 2,4 | 5,6 / 20 | 10 % |
| Petit Jean | départ | 100 % | 10,4 | 0,6 / 5 | 0 % |
| Le puzzle | départ | 100 % | 4,3 | 3,0 / 11 | 0 % |
| Miroir | départ | 100 % | 6,1 | 2,2 / 11 | 3 % |

**Aucun combat à un ennemi n'est une menace** (2,7 PV perdus en moyenne avec le deck de départ).

### 3.2 Deux ennemis (niveaux 6 à 9)

| Flotte | Deck | Victoires | Défaites | Tours | PV principal perdus (moy. / max) | Lanceur détruit |
|---|---|---|---|---|---|---|
| Le nettoyeur + Le puzzle | départ | **83 %** | 17 % | 5,5 | **42,3** / 60 | 53 % |
| Le nettoyeur + Le puzzle | étoffé | 100 % | 0 % | 4,4 | 26,7 / 57 | 33 % |
| Pat + Le nettoyeur | départ | 100 % | 0 % | 6,1 | **39,1** / 59 | 40 % |
| Pat + Le nettoyeur | étoffé | 100 % | 0 % | 4,4 | 23,4 / 58 | 47 % |
| Le nettoyeur + Le nettoyeur | départ | 97 % | 3 % | 4,6 | 29,1 / 60 | 70 % |
| Le nettoyeur + Le nettoyeur | étoffé | 97 % | 3 % | 3,4 | 23,6 / 60 | 67 % |
| Le puzzle + Le puzzle | départ | 100 % | 0 % | 8,1 | 22,9 / 32 | **100 %** |
| Petit Jean + Petit Jean | départ | 97 % | 3 % | **18,8** | 22,5 / 60 | 60 % |
| Pat + Le puzzle | départ | 100 % | 0 % | 7,8 | 20,0 / 35 | 73 % |
| Petit Jean + Le puzzle | départ | 100 % | 0 % | 14,4 | 18,5 / 41 | 63 % |
| Le nettoyeur + Petit Jean | départ | 100 % | 0 % | 12,9 | 15,2 / 49 | 40 % |

(Tableau complet en annexe.)

- **Le nettoyeur** (2 attaques de 7) reste l'ennemi le plus dangereux en paire : les 4 paires les
  plus coûteuses le contiennent. Un bouclier aide peu contre lui : les combats durent 4 à 6 tours,
  le meilleur moyen de se protéger est de le tuer vite.
- **Le puzzle** (frappe tous les modules) détruit presque toujours le Lanceur.
- **Petit Jean** allonge les combats (19 tours à deux) ; avec la montée des dégâts, un combat long
  finit par coûter cher.
- En moyenne par paire : 18,6 PV perdus avec le deck de départ, 13,7 avec le deck étoffé.

### 3.3 Le Boss

| Deck | Victoires | Tours | PV principal perdus (moy. / max) |
|---|---|---|---|
| départ | **63 %** | 14,7 | 44,6 / 60 |
| étoffé | **100 %** | 10,0 | 20,3 / 56 |

Le Boss frappe **tous les modules** (5, puis 7, 9, 11… tous les 3 tours) et se protège de 10 tous
les 3 tours. Avec un deck étoffé, il est battu à coup sûr mais coûte encore 20 PV : un principal
entamé (28 PV en moyenne à l'arrivée sur l'enchaînement, §4) peut y mourir.

## 4. Enchaînement des niveaux 2 à 10 (approximation d'une partie)

Un combat par niveau, flottes tirées comme aujourd'hui (1 ennemi jusqu'au niveau 5, 2 ensuite, Boss
au 10), PV du principal reportés, **aucun soin hors combat** (ni Station, ni Aventure). Deck départ
jusqu'au niveau 5, étoffé ensuite.

| Niveau | Parties encore en vie | PV du principal au début | PV perdus pendant le niveau (nets, Réparation comprise) |
|---|---|---|---|
| 2 | 100 % | 60,0 | 2,5 |
| 3 à 5 | 100 % | 57,5 → 56,3 | moins de 1 |
| 6 | 100 % | 55,7 | **13,7** |
| 7 | 98 % | 42,8 | 10,3 |
| 8 | 90 % | 35,2 | 8,3 |
| 9 | 80 % | 30,3 | 6,5 |
| 10 (Boss) | 68 % | 28,3 | 10,8 |

**45 % des parties battent le Boss.** Les défaites viennent du Boss (69 parties, avec un principal
déjà bas : 14 PV en moyenne à l'arrivée, contre 36 pour les parties gagnées) et des paires avec Le
nettoyeur (Le nettoyeur + Le puzzle 20, Pat + Le nettoyeur 17, Le nettoyeur + Petit Jean 14, Le
nettoyeur + Le nettoyeur 10).

- Le jeu complet aura des Stations (niveaux 5 et 9) : ces chiffres sont un plancher, à refaire après
  le branchement au parcours.
- **La difficulté reste mal répartie** : rien ne se passe aux niveaux 2 à 5, tout se joue de 6 à 10.

## 5. Mesures de la refonte

| Mesure | Valeur |
|---|---|
| Lanceur détruit | 42 % des combats isolés, au tour 4,4 en moyenne |
| Cartes en Hors service à la fin (si le Lanceur est détruit) | 2,4 en moyenne |
| Dégâts absorbés par le bouclier des modules | 18,2 par combat |
| Dégâts d'incendie infligés | 22,2 par combat en moyenne (sur tous les combats) |
| Combats enlisés (arrêtés à 40 tours) | **0** |

## 6. Bouclier : les trois réglages essayés

Trois réglages des cartes de bouclier ont été simulés le même jour, sur les mêmes combats et les
mêmes graines (essais détaillés et décision : `essai_bouclier_2026-11-11.md`) :

| | 3 / 5 / 6 (départ) | **4 / 6 / 8 (retenu)** | 5 / 7 / 8 (jugé trop haut) |
|---|---|---|---|
| Combats isolés : victoires | 97,1 % | **98,5 %** | 99,4 % |
| Combats isolés : PV principal perdus | 15,7 | **13,8** | 12,1 |
| Un ennemi, deck départ : PV perdus | 3,3 | 2,7 | 2,2 |
| Deux ennemis, deck départ : PV perdus | 22,3 | **18,6** | 15,4 |
| Deux ennemis, deck étoffé : PV perdus | 14,6 | 13,7 | 12,9 |
| Boss, deck départ : victoires / PV perdus | 37 % / 48,7 | **63 % / 44,6** | 97 % / 38,5 |
| Boss, deck étoffé : victoires / PV perdus | 97 % / 23,4 | **100 % / 20,3** | 100 % / 17,0 |
| Enchaînement : parties qui battent le Boss | 32 % | **45 %** | 59 % |
| Dégâts absorbés par les boucliers / combat | 14,9 | 18,2 | 21,3 |

(Valeurs : Bouclier / Protéger le vaisseau / Blindage ciblé.)

### 6.1 Combien de Bouclier on joue

Le **taux de jeu** (carte jouée / carte vue en main) est trompeur pour une carte en 4 exemplaires.
Par tour, avec le deck de départ :

| | 3 / 5 / 6 | 4 / 6 / 8 | 5 / 7 / 8 |
|---|---|---|---|
| Électricité dépensée par tour (sur 3) | 2,86 | 2,87 | 2,87 |
| Laser joués par tour | 1,57 | 1,55 | 1,55 |
| Bouclier : en main / joués par tour | 1,92 / 0,47 | 1,91 / 0,49 | 1,89 / 0,51 |

L'électricité est presque toujours dépensée en entier ; le Laser passe en premier et le Bouclier
prend ce qui reste, **environ un tous les deux tours, quelle que soit sa valeur**. Remonter le
Bouclier ne change pas combien on en joue, mais ce que chacun rapporte.

### 6.2 Les autres cartes de défense

| Carte | Taux de jeu (3 / 5 / 6) | Taux de jeu (4 / 6 / 8) | Taux de jeu (5 / 7 / 8) |
|---|---|---|---|
| Protéger le vaisseau | 53 % | 53 % | 53 % |
| Blindage ciblé | 19 % | 17 % | 11 % |
| Bouclier stabilisé (fait lancer Bouclier 2 fois) | 6 % | 9 % | 13 % |
| Réparation | 51 % | 48 % | 43 % |
| Leurre | 50 % | 45 % | 35 % |

Plus les boucliers montent, plus ils remplacent le Leurre et la Réparation. Blindage ciblé (8 pour
2) reste peu joué : la carte mérite d'être revue (coût 1 ? effet en plus ?) si elle doit rester un
choix.

### 6.3 Accumulation

La campagne ne mesure pas le bouclier maximal ; l'essai dédié l'a fait sur 32 combats : avec
Bouclier à 4, le bouclier d'un module monte jusqu'à 15 dans les combats difficiles et **jusqu'à 34
contre Petit Jean seul**, sans changer l'issue de ces combats. À surveiller, aucun frein ajouté.

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

Effet (boucliers 3 / 5 / 6, mêmes combats) : *Salve laser* 10 % → 74 % de jeu, *Protocole
d'urgence* 0 % → 63 %, parties de l'enchaînement qui battent le Boss 14 % → 32 %. Ces cartes
étaient **sous-estimées par le bot**, pas mauvaises. L'autre idée de l'utilisateur (jouer la carte
avant et après amélioration pour comparer) demande de simuler plusieurs tours à l'avance pour
chaque essai : gardée en réserve.

## 8. Cartes

« En main / tour » et « jouée / tour » sont comptés sur les tours des combats où la carte était
dans le deck : ils sont plus parlants que le taux de jeu pour une carte en plusieurs exemplaires.

| Carte | Coût | Taux de jeu | En main / tour | Jouée / tour | Part de l'électricité dépensée |
|---|---|---|---|---|---|
| Missiles | 2 | 75 % | 0,33 | 0,25 | 4 % |
| Ciel de missiles | 1 | 75 % | 0,32 | 0,24 | 2 % |
| Salve laser | 2 | 74 % | 0,37 | 0,27 | 2 % |
| Laser | 1 | 73 % | 1,71 | 1,24 | 44 % |
| Laser lourd | 1 | 71 % | 0,36 | 0,25 | 1 % |
| Bombardement | 1 | 67 % | 0,32 | 0,22 | 2 % |
| Embrasement | 2 | 66 % | 0,34 | 0,23 | 3 % |
| Protocole d'urgence | 3 | 63 % | 0,37 | 0,23 | 3 % |
| Torpille | 2 | 59 % | 0,32 | 0,19 | 3 % |
| Protéger le vaisseau | 1 | 53 % | 0,42 | 0,22 | 8 % |
| Guerre nucléaire | 3 | 52 % | 0,37 | 0,19 | 4 % |
| Réparation | 1 | 48 % | 0,33 | 0,16 | 5 % |
| Leurre | 1 | 45 % | 0,32 | 0,14 | 1 % |
| Laser perçant | 2 | 37 % | 0,38 | 0,14 | 1 % |
| Tir incendiaire | 2 | 34 % | 0,36 | 0,12 | 1 % |
| Bouclier | 1 | 25 % | 1,67 | 0,42 | 15 % |
| Blindage ciblé | 2 | 17 % | 0,39 | 0,07 | 1 % |
| Ligne arrière | 1 | 12 % | 0,32 | 0,04 | 0 % |
| Bouclier stabilisé | 3 | 9 % | 0,35 | 0,03 | 0 % |

- **Les cartes d'attaque dominent** : tuer vite reste la meilleure défense, d'autant que les
  dégâts ennemis montent avec le temps.
- **Bouclier est la deuxième carte en électricité dépensée** (15 %, après le Laser) : son faible
  taux de jeu vient du nombre d'exemplaires.
- **Ligne arrière** (12 %) n'a de cible que si un ennemi est à l'arrière, ce qui est rare avec 1 ou
  2 ennemis.

## 9. Pistes (à décider par l'utilisateur)

1. **Répartir la difficulté** : rendre les niveaux 2 à 5 plus menaçants (coefficient de difficulté
   par niveau, ou deux ennemis plus tôt). C'est le levier prioritaire (`specs/refonte-ennemis.md`
   §5, flottes laissées pour plus tard).
2. **Le nettoyeur** : ses 2 attaques de 7 restent les plus coûteuses (4 paires les plus mortelles).
   Baisser à 6 si c'est encore vrai après le travail sur les flottes.
3. **Le Boss** : exigeant avec le deck de départ, facile avec un deck étoffé ; à revoir avec la
   composition des flottes.
4. **Petit Jean** : seul, un combat long et sans risque (10 tours, moins de 1 PV perdu). Lui donner
   un peu de mordant, ou moins de PV.
5. **Blindage ciblé** (8 pour 2) : peu joué ; à revoir s'il doit rester un choix.
6. **Accumulation du bouclier** : à surveiller (jusqu'à 34 contre Petit Jean avec Bouclier à 4) ;
   freins possibles dans `essai_bouclier_2026-11-11.md`.
7. **Répétitions** : *Salve laser* et *Protocole d'urgence* sont parmi les cartes les plus fortes ;
   à surveiller en jeu réel.
8. **Après le branchement au parcours** : relancer des parties complètes (Stations, récompenses)
   pour caler les PV du principal (60) et du Lanceur (20).

---

## Annexe : toutes les flottes (boucliers 4 / 6 / 8)

| Flotte | Deck | Victoires | Défaites | Tours | PV principal perdus (moy. / max) | Lanceur détruit | Renvoi subi |
|---|---|---|---|---|---|---|---|
| Pat | départ | 100 % | 0 % | 4,1 | 1,9 / 10 | 0 % | 0,0 |
| Pat | étoffé | 100 % | 0 % | 3,8 | 3,3 / 15 | 0 % | 0,0 |
| Le nettoyeur | départ | 100 % | 0 % | 2,4 | 5,6 / 20 | 10 % | 0,0 |
| Le nettoyeur | étoffé | 100 % | 0 % | 2,2 | 4,4 / 17 | 7 % | 0,0 |
| Petit Jean | départ | 100 % | 0 % | 10,4 | 0,6 / 5 | 0 % | 0,0 |
| Petit Jean | étoffé | 100 % | 0 % | 7,7 | 1,7 / 12 | 0 % | 0,0 |
| Le puzzle | départ | 100 % | 0 % | 4,3 | 3,0 / 11 | 0 % | 0,0 |
| Le puzzle | étoffé | 100 % | 0 % | 3,7 | 5,9 / 15 | 0 % | 0,0 |
| Miroir | départ | 100 % | 0 % | 6,1 | 2,2 / 11 | 3 % | 16,7 |
| Miroir | étoffé | 100 % | 0 % | 4,4 | 2,4 / 8 | 3 % | 10,0 |
| Pat + Pat | départ | 100 % | 0 % | 8,4 | 7,0 / 24 | 60 % | 0,0 |
| Pat + Pat | étoffé | 100 % | 0 % | 5,4 | 8,5 / 22 | 37 % | 0,0 |
| Pat + Le nettoyeur | départ | 100 % | 0 % | 6,1 | 39,1 / 59 | 40 % | 0,0 |
| Pat + Le nettoyeur | étoffé | 100 % | 0 % | 4,4 | 23,4 / 58 | 47 % | 0,0 |
| Pat + Petit Jean | départ | 100 % | 0 % | 13,5 | 8,2 / 36 | 37 % | 0,0 |
| Pat + Petit Jean | étoffé | 100 % | 0 % | 9,1 | 4,2 / 25 | 30 % | 0,0 |
| Pat + Le puzzle | départ | 100 % | 0 % | 7,8 | 20,0 / 35 | 73 % | 0,0 |
| Pat + Le puzzle | étoffé | 100 % | 0 % | 5,9 | 17,3 / 36 | 67 % | 0,0 |
| Pat + Miroir | départ | 100 % | 0 % | 9,1 | 7,8 / 21 | 40 % | 10,0 |
| Pat + Miroir | étoffé | 100 % | 0 % | 6,0 | 6,6 / 27 | 23 % | 7,5 |
| Le nettoyeur + Le nettoyeur | départ | 97 % | 3 % | 4,6 | 29,1 / 60 | 70 % | 0,0 |
| Le nettoyeur + Le nettoyeur | étoffé | 97 % | 3 % | 3,4 | 23,6 / 60 | 67 % | 0,0 |
| Le nettoyeur + Petit Jean | départ | 100 % | 0 % | 12,9 | 15,2 / 49 | 40 % | 0,0 |
| Le nettoyeur + Petit Jean | étoffé | 100 % | 0 % | 8,9 | 14,0 / 48 | 20 % | 0,0 |
| Le nettoyeur + Le puzzle | départ | 83 % | 17 % | 5,5 | 42,3 / 60 | 53 % | 0,0 |
| Le nettoyeur + Le puzzle | étoffé | 100 % | 0 % | 4,4 | 26,7 / 57 | 33 % | 0,0 |
| Le nettoyeur + Miroir | départ | 100 % | 0 % | 8,1 | 13,4 / 42 | 53 % | 18,2 |
| Le nettoyeur + Miroir | étoffé | 100 % | 0 % | 5,5 | 17,1 / 56 | 37 % | 10,8 |
| Petit Jean + Petit Jean | départ | 97 % | 3 % | 18,8 | 22,5 / 60 | 60 % | 0,0 |
| Petit Jean + Petit Jean | étoffé | 100 % | 0 % | 10,3 | 4,6 / 24 | 23 % | 0,0 |
| Petit Jean + Le puzzle | départ | 100 % | 0 % | 14,4 | 18,5 / 41 | 63 % | 0,0 |
| Petit Jean + Le puzzle | étoffé | 100 % | 0 % | 9,3 | 13,0 / 37 | 67 % | 0,0 |
| Petit Jean + Miroir | départ | 100 % | 0 % | 14,7 | 6,7 / 40 | 27 % | 5,3 |
| Petit Jean + Miroir | étoffé | 100 % | 0 % | 9,8 | 3,6 / 43 | 33 % | 9,2 |
| Le puzzle + Le puzzle | départ | 100 % | 0 % | 8,1 | 22,9 / 32 | 100 % | 0,0 |
| Le puzzle + Le puzzle | étoffé | 100 % | 0 % | 5,8 | 20,8 / 42 | 100 % | 0,0 |
| Le puzzle + Miroir | départ | 100 % | 0 % | 8,6 | 17,6 / 34 | 83 % | 7,3 |
| Le puzzle + Miroir | étoffé | 100 % | 0 % | 6,1 | 16,7 / 35 | 93 % | 9,3 |
| Miroir + Miroir | départ | 100 % | 0 % | 10,3 | 8,4 / 25 | 43 % | 28,5 |
| Miroir + Miroir | étoffé | 100 % | 0 % | 7,1 | 5,3 / 26 | 33 % | 17,1 |
| Boss | départ | 63 % | 37 % | 14,7 | 44,6 / 60 | 100 % | 0,0 |
| Boss | étoffé | 100 % | 0 % | 10,0 | 20,3 / 56 | 100 % | 0,0 |

Aucun combat enlisé dans aucune flotte.
