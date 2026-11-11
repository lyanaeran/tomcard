# Synthèse de simulation — combat de la refonte — 11 novembre 2026

## État du jeu testé

| | |
|---|---|
| **Date de la campagne** | 2026-11-11, 18 h 23 |
| **Code** | branche `devjeux` (PR #61) : `CombatNew` après les deux reviews (commit `a5e83ab`), plus le simulateur `outils/simulation/bot_new.py` et `combats_new.py` (même PR). Aucune règle de jeu modifiée pour la simulation |
| **Règles** | **Règles de la refonte**, telles que codées dans `src/gameplay/combat_new.py` (`specs/refonte-combat.md`) : statuts partagés (bouclier et incendie −1 par tour, renvoi cumulable jusqu'au tour suivant, leurre), cycles d'actions des ennemis avec montée des valeurs, pile Hors service, défaite seulement si le principal est détruit |
| **Joueur** | Principal 60 PV, Lanceur de missiles 20 PV (avant gauche). 3 électricité, 5 cartes par tour. Deck **« départ »** : deck de départ (10 cartes) + 1 carte du Lanceur au hasard. Deck **« étoffé »** : le même + 5 cartes revues hors Base au hasard (milieu de partie) |
| **Cartes** | Les 19 cartes de `config/carte_new.json`, **y compris celles que l'ancien moteur ne sait pas jouer** (Missiles, Torpille, incendie, répétitions) : `CombatNew` les gère toutes |
| **Ennemis** | Les 6 ennemis de `config/ennemi_new.json` (tableau validé le 2026-11-08 : dégâts +1 tous les 3 tours, Boss +2), coefficient 1. Placement comme le jeu actuel (protecteur devant, protégé derrière) |
| **Joueur automatique** | Bot « recherche » en faisceau, repris de la campagne du 7 novembre et adapté à `CombatNew` (6 états par profondeur, noté après la réponse ennemie simulée), **plus une valeur des lancements en plus** (idée utilisateur, §6) |
| **Volume** | **5 760 combats** : 2 000 combats du bot aléatoire (robustesse), 42 combats de validation, 1 260 combats isolés du bot de recherche (21 flottes × 2 decks × 30), 300 enchaînements des niveaux 2 à 10 (2 458 combats) |
| **Durée** | 2 min 38 s sur 8 cœurs, lancé avec `caffeinate -i` |
| **Reproduire** | `caffeinate -i python -m outils.simulation.combats_new --graines 30 --robustesse 2000 --enchainements 300 --graine 1` ; résultats bruts dans `outils/simulation/resultats/2026-11-11_1823_combats_new.*` (non versionnés) |

**Pas de partie complète** : le combat de la refonte n'est pas encore branché au parcours (pas de
récompenses, de Station ni d'Aventures). L'« enchaînement » (§4) est une **approximation** : un
combat par niveau, PV du principal reportés, sans aucun soin hors combat.

---

## En bref

1. **Tout va bien côté moteur** : 5 760 combats, **aucune erreur, aucun invariant violé** (piles de
   cartes, PV, statuts, Hors service, journal, intentions, fin de combat).
2. **Miroir n'est plus un problème** : aucun combat enlisé (47 % des combats contre Miroir
   s'enlisaient le 7 novembre). Il renvoie 6 à 28 dégâts par combat en moyenne selon la flotte, sans blocage.
3. **Les combats à un ennemi (niveaux 2 à 5) sont toujours trop faciles** : 100 % de victoires,
   environ 3 PV perdus.
4. **Les combats à deux ennemis (niveaux 6 à 9) font mal** : 15 à 22 PV perdus en moyenne, jusqu'à
   44 avec Le nettoyeur + Le puzzle. Sans soin entre les combats, le principal arrive au Boss avec
   **27 PV en moyenne**.
5. **Le Boss est devenu très dur** (il était battu 51 fois sur 51 le 7 novembre) : même avec 60 PV,
   il bat le deck de départ 63 fois sur 100 ; le deck étoffé le bat presque toujours, mais en y
   laissant 23 PV. Sur l'enchaînement, **32 % des parties battent le Boss**.
6. **Le Lanceur de missiles (20 PV) joue bien son rôle de module sacrifiable** : détruit dans 44 %
   des combats, au tour 4,4 en moyenne, il protège le principal.
7. **Les cartes de répétition sont fortes une fois que le bot sait les estimer** : *Salve laser*
   et *Protocole d'urgence* passent de 10 % et 0 % de jeu à 74 % et 63 %, et les parties gagnées de
   14 % à 32 % (§6). *Bouclier stabilisé* reste à 6 % : il ne fait que doubler le petit Bouclier.

---

## 1. Robustesse : le moteur tient

| Étude | Combats | Exceptions | Combats avec un invariant violé |
|---|---|---|---|
| Bot aléatoire (robustesse) | 2 000 | 0 | 0 |
| Validation (les deux bots) | 42 | 0 | 0 |
| Bot de recherche (équilibre) | 1 260 | 0 | 0 |
| Enchaînements (bot de recherche) | 2 458 | 0 | 0 |

Après **chaque carte jouée et chaque fin de tour**, le simulateur vérifie :

- chaque carte est dans une seule pile, et le nombre total de cartes ne change pas ;
- la main ne dépasse pas 10 cartes ; l'électricité n'est jamais négative ; le tour ne recule pas ;
- les PV restent entre 0 et le maximum ; aucun statut à 0 ne traîne ;
- un module détruit n'a plus de statuts, et ses cartes non Persistantes sont toutes en Hors service ;
- victoire si et seulement si tous les ennemis sont détruits, défaite si et seulement si le
  principal l'est ;
- dans le journal, le détail des dégâts (leurre, renvoi, bouclier, PV perdus) ne dépasse jamais
  les dégâts reçus ;
- **chaque attaque ennemie a bien la valeur annoncée par son intention**.

Le bot aléatoire joue des coups très variés (cartes au hasard, sur des cibles au hasard), ce qui
couvre des situations qu'un joueur raisonnable ne provoque pas.

## 2. Le bot est-il fiable ?

| Bot | Combats | Victoires | PV principal perdus |
|---|---|---|---|
| Recherche | 42 | 93 % | 20,7 |
| Aléatoire | 42 | 45 % | 43,8 |

Sur les mêmes combats (deck de départ, toutes les flottes), le bot de recherche gagne deux fois
plus et perd deux fois moins de PV. Comme le 7 novembre, ses résultats servent à **comparer**
(ennemis, decks, cartes) ; un joueur humain attentif fera sans doute un peu mieux.

## 3. Combats isolés (principal à 60 PV)

### 3.1 Un ennemi (niveaux 2 à 5)

| Ennemi | Deck | Victoires | Tours | PV principal perdus (moy. / max) | Lanceur détruit |
|---|---|---|---|---|---|
| Pat le Pirate | départ | 100 % | 4,1 | 2,6 / 10 | 0 % |
| Le nettoyeur | départ | 100 % | 2,4 | 6,1 / 22 | 13 % |
| Petit Jean | départ | 100 % | 10,4 | 1,1 / 7 | 0 % |
| Le puzzle | départ | 100 % | 4,3 | 3,2 / 11 | 3 % |
| Miroir | départ | 100 % | 6,1 | 3,5 / 14 | 3 % |

Avec le deck étoffé, mêmes résultats à quelques PV près. **Aucun combat à un ennemi n'est une
menace** : c'est le même constat que le 7 novembre.

### 3.2 Deux ennemis (niveaux 6 à 9) — les plus durs

| Flotte | Deck | Victoires | Défaites | Tours | PV principal perdus (moy. / max) | Lanceur détruit | Renvoi subi |
|---|---|---|---|---|---|---|---|
| Le nettoyeur + Le puzzle | départ | **73 %** | 27 % | 5,3 | **43,8** / 60 | 53 % | 0,0 |
| Le nettoyeur + Le puzzle | étoffé | 100 % | 0 % | 4,4 | 27,5 / 57 | 33 % | 0,0 |
| Pat + Le nettoyeur | départ | 93 % | 7 % | 6,0 | **41,1** / 60 | 40 % | 0,0 |
| Pat + Le nettoyeur | étoffé | 100 % | 0 % | 4,4 | 24,1 / 58 | 47 % | 0,0 |
| Le nettoyeur + Le nettoyeur | départ | 97 % | 3 % | 4,6 | 31,7 / 60 | 70 % | 0,0 |
| Le nettoyeur + Le nettoyeur | étoffé | 97 % | 3 % | 3,4 | 24,5 / 60 | 67 % | 0,0 |
| Petit Jean + Petit Jean | départ | **83 %** | 17 % | **18,3** | 29,1 / 60 | 67 % | 0,0 |
| Petit Jean + Petit Jean | étoffé | 100 % | 0 % | 10,2 | 6,2 / 26 | 30 % | 0,0 |
| Le puzzle + Le puzzle | départ | 100 % | 0 % | 8,1 | 26,5 / 36 | **100 %** | 0,0 |
| Petit Jean + Le puzzle | départ | 100 % | 0 % | 14,4 | 23,2 / 47 | 83 % | 0,0 |
| Pat + Le puzzle | départ | 100 % | 0 % | 7,7 | 23,0 / 43 | 73 % | 0,0 |
| Pat + Pat | départ | 100 % | 0 % | 8,3 | 11,1 / 35 | 63 % | 0,0 |
| Pat + Miroir | départ | 100 % | 0 % | 9,0 | 11,5 / 33 | 50 % | 10,2 |
| Miroir + Miroir | départ | 100 % | 0 % | 10,3 | 12,0 / 32 | 53 % | 28,0 |

(Tableau complet des 15 paires et des deux decks en annexe.)

- **Le nettoyeur** (2 attaques de 7) est le plus dangereux en paire : il détruit vite le
  Lanceur, puis frappe le principal.
- **Le puzzle** (frappe tous les modules) détruit le Lanceur dans presque tous les combats où il
  est en paire.
- **Petit Jean** est peu dangereux seul, mais **allonge** les combats (100 PV, bouclier) : à deux,
  18 tours en moyenne avec le deck de départ. Avec la montée des dégâts (+1 tous les 3 tours), un
  combat long devient mortel.
- Le deck étoffé réduit nettement les pertes : 14,6 PV en moyenne par paire, contre 22,3.

### 3.3 Le Boss

| Deck | Victoires | Tours | PV principal perdus (moy. / max) |
|---|---|---|---|
| départ | **37 %** | 13,9 | 48,7 / 60 |
| étoffé | 97 % | 9,9 | 23,4 / 60 |

Le Boss frappe **tous les modules** (5, puis 7, 9, 11… tous les 3 tours) et se protège de 10 tous
les 3 tours. Sur un combat de 10 à 14 tours, ses dégâts montent à 11 ou 13 par coup : **même avec
le principal plein, il coûte 23 PV au deck étoffé**, presque la moitié de ce qu'il reste en
moyenne au principal à ce stade (§4).

## 4. Enchaînement des niveaux 2 à 10 (approximation d'une partie)

Un combat par niveau, flottes tirées comme aujourd'hui (1 ennemi jusqu'au niveau 5, 2 ensuite, Boss
au 10), PV du principal reportés, **aucun soin hors combat** (ni Station, ni Aventure). Deck départ
jusqu'au niveau 5, étoffé ensuite.

| Niveau | Parties encore en vie | PV du principal au début | PV perdus pendant le niveau (nets, Réparation comprise) |
|---|---|---|---|
| 2 | 100 % | 60,0 | 3,3 |
| 3 à 5 | 100 % | 56,7 → 55,3 | moins de 1 |
| 6 | 100 % | 54,5 | **14,8** |
| 7 | 98 % | 40,7 | 10,8 |
| 8 | 87 % | 33,6 | 9,3 |
| 9 | 76 % | 27,9 | 6,8 |
| 10 (Boss) | 59 % | 27,0 | 13,4 |

**32 % des parties battent le Boss.** Les défaites viennent du Boss (80 parties) et des paires
avec Le nettoyeur (Le nettoyeur + Le puzzle 22, Pat + Le nettoyeur 21, Le nettoyeur + Petit Jean
18, Le nettoyeur + Le nettoyeur 12). Les parties qui battent le Boss y arrivent avec 35 PV en
moyenne, celles qui perdent avec 17.

- **Le principal ne remonte pas** : sans Station ni Aventure, seule la carte Réparation (8 PV, 2
  munitions) soigne. C'est voulu (seuls les PV du principal persistent), mais le jeu complet aura
  des Stations (niveaux 5 et 9) qui changeront ces chiffres : à refaire après le branchement.
- **La difficulté est mal répartie** : rien ne se passe pendant 4 niveaux, puis tout se joue aux
  niveaux 6 à 10.

## 5. Mesures de la refonte

| Mesure | Valeur |
|---|---|
| Lanceur détruit | 44 % des combats isolés, au tour 4,4 en moyenne |
| Cartes en Hors service à la fin (si le Lanceur est détruit) | 2,6 en moyenne |
| Dégâts absorbés par le bouclier des modules | 14,9 par combat |
| Dégâts d'incendie infligés | 22,2 par combat en moyenne (sur tous les combats, avec ou sans carte d'incendie dans le deck) |
| Combats enlisés (arrêtés à 40 tours) | **0** |

## 6. Le bot et les cartes de répétition (idée utilisateur)

**Problème** : la première campagne (même jour, 18 h 04) ne jouait jamais *Protocole d'urgence* ni
*Bouclier stabilisé*, et *Salve laser* 10 % du temps. La recherche du bot ne voit que le tour
suivant, alors qu'une répétition ne paie que sur les tours d'après.

**Correction (idée utilisateur)** : le bot donne une valeur à l'**amélioration du deck**. Pour
chaque carte encore jouable (pioche, main, défausse) qui a des lancements en plus :

> lancements en plus × valeur d'un lancement × nombre de fois où la carte sera encore jouée

- **valeur d'un lancement** : somme de ses effets (dégâts comptés comme des PV ennemis en moins,
  multipliés par le nombre d'ennemis pour une carte de zone ; bouclier, réparation, incendie,
  leurre, pioche, électricité avec leur propre poids) ;
- **nombre de fois où elle sera encore jouée** : tours restants estimés × chance de la piocher (5
  cartes sur le deck actif) × 70 % ;
- **tours restants** : 10 moins le numéro du tour. **Plus le combat est jeune, plus l'amélioration
  vaut**, comme le suggérait l'utilisateur.

Un premier essai estimait les tours restants d'après les PV des ennemis : le bot gagnait alors des
points à **ne pas frapper**, et 1 à 7 % des combats s'enlisaient. Le numéro du tour, sur lequel le
bot n'a pas de prise, règle le problème (0 enlisé).

**Résultat** (mêmes combats, mêmes graines ; le deck de départ, sans répétition, ne change pas) :

| | Bot sans valeur du deck | Bot avec valeur du deck |
|---|---|---|
| *Salve laser* jouée | 10 % | **74 %** |
| *Protocole d'urgence* jouée | 0 % | **63 %** |
| *Bouclier stabilisé* jouée | 0 % | 6 % |
| Boss, deck étoffé : victoires / PV perdus | 87 % / 33,5 | 97 % / 23,4 |
| Enchaînement : parties qui battent le Boss | 14 % | **32 %** |

- Ces cartes étaient donc **sous-estimées par le bot**, pas mauvaises : bien jouées, elles
  comptent parmi les plus fortes du jeu.
- **Bouclier stabilisé** reste presque ignoré : il fait lancer deux fois le Bouclier (3), la carte
  la plus faible du deck (§7). Son sort dépend de celui du Bouclier.
- L'autre idée de l'utilisateur (jouer la carte avant et après amélioration pour comparer) demande
  de simuler plusieurs tours à l'avance pour chaque essai : beaucoup plus lent. Gardée en réserve.

## 7. Cartes

| Carte | Vue en main | Taux de jeu |
|---|---|---|
| Missiles | 663 | 74 % |
| Ciel de missiles | 627 | 74 % |
| Salve laser | 400 | 74 % |
| Laser | 16 636 | 73 % |
| Laser lourd | 378 | 71 % |
| Embrasement | 699 | 67 % |
| Bombardement | 727 | 67 % |
| Protocole d'urgence | 394 | 63 % |
| Torpille | 656 | 59 % |
| Protéger le vaisseau | 4 090 | 53 % |
| Guerre nucléaire | 713 | 52 % |
| Réparation | 3 069 | 51 % |
| Leurre | 822 | 50 % |
| Laser perçant | 411 | 36 % |
| Tir incendiaire | 426 | 34 % |
| Bouclier | 16 320 | 24 % |
| Blindage ciblé | 469 | 19 % |
| Ligne arrière | 672 | 12 % |
| Bouclier stabilisé | 418 | 6 % |

- **Les cartes d'attaque dominent** : le bot préfère tuer vite plutôt que se protéger, ce qui
  rejoint le constat sur la montée des dégâts (un combat long coûte cher).
- **Bouclier (3) est la carte la moins utile du deck de départ** : 24 %, contre 53 % pour Protéger
  le vaisseau (5). Avec −1 par tour, 3 de bouclier protègent peu. *Blindage ciblé* (6, coût 2) ne
  fait guère mieux (19 %).
- **Ligne arrière** (12 %) n'a de cible que si un ennemi est à l'arrière, ce qui est rare avec 1 ou
  2 ennemis.

## 8. Pistes (à décider par l'utilisateur)

1. **Répartir la difficulté** : rendre les niveaux 2 à 5 plus menaçants (coefficient de difficulté
   par niveau, ou deux ennemis plus tôt) et/ou les niveaux 6 à 9 moins brutaux. C'est la question
   des flottes, laissée pour plus tard (`specs/refonte-ennemis.md` §5).
2. **Le Boss** : sa montée (+2 tous les 3 tours) sur des combats de 10 à 14 tours le rend très dur
   pour un principal entamé. Pistes : montée plus lente (+1), ou moins de PV pour raccourcir le
   combat.
3. **Le nettoyeur** : ses 2 attaques de 7 sont les plus coûteuses, il est dans les 4 paires les
   plus mortelles. Si c'est encore vrai après le travail sur les flottes, baisser ses dégâts à 6.
4. **Petit Jean** : seul, il n'est qu'un combat long et sans risque (10 tours, 1 PV perdu). Lui
   donner un peu plus de mordant, ou moins de PV.
5. **Bouclier (3)** : à revaloriser (4 ?) si on veut qu'il reste une carte de base utile avec la
   perte de 1 par tour ; *Bouclier stabilisé* en profiterait.
6. **Répétitions** : *Salve laser* et *Protocole d'urgence* sont parmi les cartes les plus fortes ;
   à surveiller en jeu réel avant d'y toucher.
7. **Après le branchement au parcours** : relancer des parties complètes (Stations, récompenses)
   pour caler les PV du principal (60) et du Lanceur (20).

---

## Annexe : toutes les flottes

| Flotte | Deck | Victoires | Défaites | Tours | PV principal perdus (moy. / max) | Lanceur détruit | Renvoi subi |
|---|---|---|---|---|---|---|---|
| Pat | départ | 100 % | 0 % | 4,1 | 2,6 / 10 | 0 % | 0,0 |
| Pat | étoffé | 100 % | 0 % | 3,8 | 3,8 / 16 | 0 % | 0,0 |
| Le nettoyeur | départ | 100 % | 0 % | 2,4 | 6,1 / 22 | 13 % | 0,0 |
| Le nettoyeur | étoffé | 100 % | 0 % | 2,2 | 4,7 / 18 | 7 % | 0,0 |
| Petit Jean | départ | 100 % | 0 % | 10,4 | 1,1 / 7 | 0 % | 0,0 |
| Petit Jean | étoffé | 100 % | 0 % | 7,7 | 1,5 / 12 | 0 % | 0,0 |
| Le puzzle | départ | 100 % | 0 % | 4,3 | 3,2 / 11 | 3 % | 0,0 |
| Le puzzle | étoffé | 100 % | 0 % | 3,7 | 6,2 / 15 | 0 % | 0,0 |
| Miroir | départ | 100 % | 0 % | 6,1 | 3,5 / 14 | 3 % | 17,3 |
| Miroir | étoffé | 100 % | 0 % | 4,4 | 2,6 / 8 | 3 % | 10,0 |
| Pat + Pat | départ | 100 % | 0 % | 8,3 | 11,1 / 35 | 63 % | 0,0 |
| Pat + Pat | étoffé | 100 % | 0 % | 5,3 | 9,0 / 22 | 40 % | 0,0 |
| Pat + Le nettoyeur | départ | 93 % | 7 % | 6,0 | 41,1 / 60 | 40 % | 0,0 |
| Pat + Le nettoyeur | étoffé | 100 % | 0 % | 4,4 | 24,1 / 58 | 47 % | 0,0 |
| Pat + Petit Jean | départ | 100 % | 0 % | 13,6 | 11,1 / 39 | 40 % | 0,0 |
| Pat + Petit Jean | étoffé | 100 % | 0 % | 9,1 | 5,3 / 26 | 30 % | 0,0 |
| Pat + Le puzzle | départ | 100 % | 0 % | 7,7 | 23,0 / 43 | 73 % | 0,0 |
| Pat + Le puzzle | étoffé | 100 % | 0 % | 5,9 | 18,2 / 36 | 67 % | 0,0 |
| Pat + Miroir | départ | 100 % | 0 % | 9,0 | 11,5 / 33 | 50 % | 10,2 |
| Pat + Miroir | étoffé | 100 % | 0 % | 5,9 | 7,4 / 27 | 23 % | 7,0 |
| Le nettoyeur + Le nettoyeur | départ | 97 % | 3 % | 4,6 | 31,7 / 60 | 70 % | 0,0 |
| Le nettoyeur + Le nettoyeur | étoffé | 97 % | 3 % | 3,4 | 24,5 / 60 | 67 % | 0,0 |
| Le nettoyeur + Petit Jean | départ | 100 % | 0 % | 12,9 | 18,4 / 54 | 60 % | 0,0 |
| Le nettoyeur + Petit Jean | étoffé | 100 % | 0 % | 8,9 | 14,7 / 51 | 20 % | 0,0 |
| Le nettoyeur + Le puzzle | départ | 73 % | 27 % | 5,3 | 43,8 / 60 | 53 % | 0,0 |
| Le nettoyeur + Le puzzle | étoffé | 100 % | 0 % | 4,4 | 27,5 / 57 | 33 % | 0,0 |
| Le nettoyeur + Miroir | départ | 100 % | 0 % | 8,1 | 18,3 / 44 | 53 % | 18,8 |
| Le nettoyeur + Miroir | étoffé | 100 % | 0 % | 5,5 | 18,5 / 56 | 37 % | 11,0 |
| Petit Jean + Petit Jean | départ | 83 % | 17 % | 18,3 | 29,1 / 60 | 67 % | 0,0 |
| Petit Jean + Petit Jean | étoffé | 100 % | 0 % | 10,2 | 6,2 / 26 | 30 % | 0,0 |
| Petit Jean + Le puzzle | départ | 100 % | 0 % | 14,4 | 23,2 / 47 | 83 % | 0,0 |
| Petit Jean + Le puzzle | étoffé | 100 % | 0 % | 9,3 | 14,2 / 39 | 70 % | 0,0 |
| Petit Jean + Miroir | départ | 100 % | 0 % | 14,6 | 12,7 / 51 | 30 % | 5,7 |
| Petit Jean + Miroir | étoffé | 100 % | 0 % | 9,7 | 3,8 / 45 | 30 % | 9,2 |
| Le puzzle + Le puzzle | départ | 100 % | 0 % | 8,1 | 26,5 / 36 | 100 % | 0,0 |
| Le puzzle + Le puzzle | étoffé | 100 % | 0 % | 5,8 | 22,2 / 45 | 100 % | 0,0 |
| Le puzzle + Miroir | départ | 100 % | 0 % | 8,6 | 20,9 / 38 | 83 % | 7,5 |
| Le puzzle + Miroir | étoffé | 100 % | 0 % | 6,2 | 17,5 / 35 | 90 % | 9,2 |
| Miroir + Miroir | départ | 100 % | 0 % | 10,3 | 12,0 / 32 | 53 % | 28,0 |
| Miroir + Miroir | étoffé | 100 % | 0 % | 7,0 | 6,0 / 24 | 33 % | 16,7 |
| Boss | départ | 37 % | 63 % | 13,9 | 48,7 / 60 | 100 % | 0,0 |
| Boss | étoffé | 97 % | 3 % | 9,9 | 23,4 / 60 | 100 % | 0,0 |

Aucun combat enlisé dans aucune flotte.
