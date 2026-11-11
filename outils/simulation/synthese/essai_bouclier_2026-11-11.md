# Essai — carte Bouclier à 3, 4, 5 ou 6 — 11 novembre 2026

## Ce qui a été testé

| | |
|---|---|
| **Question** | La carte *Bouclier* (CRT_10, coût 1, Module Unique) donne 3 de bouclier. Avec 4, 5 ou 6, devient-elle plus utile, ou trop forte ? Et le bouclier, qui ne perd que 1 par tour, s'accumule-t-il jusqu'à des montants très élevés ? |
| **Combats** | **20 combats difficiles** et **12 combats contre des ennemis faibles**, joués quatre fois avec les **mêmes graines** (même deck mélangé, mêmes ennemis, mêmes tirages) : avec Bouclier à 3, 4, 5 puis 6. Seule la valeur de la carte change |
| **Flottes** | Difficiles : les 5 plus dures de la campagne du jour (`analyse_2026-11-11_combat_new.md`), 4 combats chacune : Le nettoyeur + Le puzzle, Pat + Le nettoyeur, Le nettoyeur + Le nettoyeur, Petit Jean + Petit Jean, le Boss. Faibles : Petit Jean, Pat le Pirate, Miroir, seuls, 4 combats chacun |
| **Joueur** | Deck de départ (4 Bouclier sur 11 cartes), principal 60 PV, Lanceur de missiles 20 PV, bot de recherche avec la valeur du deck |
| **Code** | `config/carte_new.json` n'est **pas modifié** : la valeur est changée seulement sur les cartes du combat simulé (`construire_combat(..., valeurs_cartes=...)`) |
| **Reproduire** | `python -m outils.simulation.essai_bouclier` (31 secondes) |
| **Bouclier max atteint** | Plus gros bouclier porté par un module du joueur à un moment du combat, relevé après chaque carte jouée et chaque fin de tour |

**Attention, petit échantillon** : 4 combats par flotte. Un écart d'une victoire ou de quelques PV
peut venir du hasard. L'essai sert à voir un ordre de grandeur, pas à trancher au point près.

---

## Résultats

### Total des 20 combats

| Bouclier | Victoires | PV principal perdus (moy.) | Bouclier joué quand il est en main | Dégâts absorbés par les boucliers |
|---|---|---|---|---|
| 3 | 16/20 | 36,2 | 27 % | 28,1 |
| 4 | 17/20 | 34,0 | 28 % | 35,0 |
| 5 | 18/20 | 29,9 | **37 %** | 40,8 |
| 6 | 19/20 | 26,9 | **40 %** | 41,8 |

### Par flotte

| Flotte | Bouclier | Victoires | PV principal perdus (moy.) | Tours | Bouclier joué quand il est en main | Dégâts absorbés par les boucliers |
|---|---|---|---|---|---|---|
| Le nettoyeur + Le puzzle | 3 | 3/4 | 40,0 | 5,0 | 11 % | 9,2 |
| | 4 | 3/4 | 39,8 | 5,0 | 11 % | 10,2 |
| | 5 | 3/4 | 39,5 | 5,0 | 18 % | 11,2 |
| | 6 | 3/4 | 38,8 | 5,0 | 24 % | 14,5 |
| Pat + Le nettoyeur | 3 | 4/4 | 36,2 | 5,5 | 8 % | 12,2 |
| | 4 | 4/4 | 35,5 | 5,5 | 8 % | 13,0 |
| | 5 | 4/4 | 24,5 | 5,5 | 26 % | 13,8 |
| | 6 | 4/4 | 23,2 | 5,5 | 26 % | 16,0 |
| Le nettoyeur + Le nettoyeur | 3 | 4/4 | 29,5 | 5,0 | 15 % | 9,5 |
| | 4 | 4/4 | 28,0 | 5,0 | 15 % | 11,0 |
| | 5 | 4/4 | 26,5 | 5,0 | 21 % | 12,5 |
| | 6 | 4/4 | 24,0 | 5,0 | 28 % | 16,5 |
| Petit Jean + Petit Jean | 3 | 2/4 | 41,0 | 19,5 | 28 % | 54,0 |
| | 4 | 3/4 | 39,5 | 21,5 | 32 % | 76,5 |
| | 5 | 4/4 | 37,5 | 21,0 | 39 % | 78,0 |
| | 6 | 4/4 | 28,2 | 20,8 | 40 % | 83,5 |
| Boss | 3 | 3/4 | 34,2 | 13,5 | 42 % | 55,2 |
| | 4 | 3/4 | 27,0 | 13,5 | 41 % | 64,5 |
| | 5 | 3/4 | 21,8 | 14,5 | 50 % | 88,2 |
| | 6 | 4/4 | 20,5 | 13,5 | 54 % | 78,5 |

### Accumulation : bouclier maximal atteint

| Flottes | Bouclier | Victoires | PV principal perdus (moy.) | Tours | Bouclier joué quand il est en main | Bouclier max atteint (moy. / max) |
|---|---|---|---|---|---|---|
| Difficiles (20) | 3 | 16/20 | 36,2 | 9,7 | 27 % | 6,9 / 11 |
| | 4 | 17/20 | 34,0 | 10,1 | 28 % | 8,6 / 15 |
| | 5 | 18/20 | 29,9 | 10,2 | 37 % | 10,2 / 21 |
| | 6 | 19/20 | 26,9 | 9,9 | 40 % | 12,1 / 28 |
| Faibles (12) | 3 | 12/12 | 1,7 | 7,2 | 26 % | 9,0 / 24 |
| | 4 | 12/12 | 1,1 | 7,2 | 28 % | 11,4 / 34 |
| | 5 | 12/12 | 0,8 | 7,2 | 39 % | 15,2 / 44 |
| | 6 | 12/12 | 0,8 | 7,2 | 46 % | 19,2 / 63 |

| Ennemi faible | Bouclier | PV principal perdus (moy.) | Tours | Bouclier max atteint (moy. / max) |
|---|---|---|---|---|
| Petit Jean | 3 | 0,2 | 10,5 | 12,8 / 24 |
| | 4 | 0,0 | 10,5 | 16,5 / 34 |
| | 5 | 0,0 | 10,5 | 23,5 / 44 |
| | 6 | 0,0 | 10,5 | **32,5 / 63** |
| Pat le Pirate | 3 | 0,0 | 5,0 | 6,5 / 9 |
| | 6 | 0,0 | 5,0 | 9,0 / 12 |
| Miroir | 3 | 4,8 | 6,0 | 7,8 / 12 |
| | 6 | 2,2 | 6,2 | 16,0 / 24 |

Bouclier max atteint des combats difficiles, par flotte (moyenne / max) : Le nettoyeur + Le puzzle
5 → 7,5 / 12 ; Pat + Le nettoyeur 5,2 → 6,0 / 12 ; Le nettoyeur + Le nettoyeur 6,0 → 10,5 / 12 ;
Petit Jean + Petit Jean 8,0 → 17,0 / 20 ; Boss 10,2 → 19,5 / 28 (de Bouclier 3 à Bouclier 6).

## Ce qu'on en retient


1. **Chaque point de bouclier rapporte, de façon régulière** : de 3 à 6, les PV perdus baissent de
   36,2 à 26,9 (environ 3 PV par point), et les victoires montent de 16 à 19 sur 20.
2. **Le vrai seuil est entre 4 et 5** : à 4, le bot ne joue pas la carte plus souvent (28 %) ; **à
   5, elle devient un choix intéressant** (37 %), y compris dans les combats courts contre Le
   nettoyeur (8 % → 26 % contre Pat + Le nettoyeur, avec 11 PV de moins perdus).
3. **Les combats longs en profitent le plus** : contre le Boss, 34 → 20 PV perdus de 3 à 6 ; contre
   les deux Petit Jean, 2 victoires sur 4 à 3, 4 sur 4 dès 5.
4. **À 6, aucun déséquilibre visible dans ces combats**, mais le gain sur 5 est modeste (3 PV par
   combat), et ce sont les combats les plus durs : dans les combats faciles, un bouclier plus fort
   ne fait que rendre le jeu plus facile.

5. **L'accumulation existe, surtout contre les ennemis faibles et dans les combats longs** :
   contre Petit Jean seul (2 à 3 dégâts par tour, 10 tours), le bouclier monte jusqu'à 24 avec
   Bouclier à 3 et jusqu'à **63** avec Bouclier à 6. Contre le Boss, jusqu'à 28 à 6. Dans les
   combats courts et violents (Le nettoyeur), il ne dépasse pas 12 : les dégâts le consomment.
6. **Mais elle ne change pas le résultat de ces combats** : contre Petit Jean, le principal ne
   perd déjà presque rien avec Bouclier à 3, et le combat dure autant (10,5 tours) quelle que soit
   la valeur : c'est le temps de tuer Petit Jean, pas un blocage. L'excès de bouclier est perdu.
   Le risque n'est pas « trop facile » mais **un jeu où l'on empile sans enjeu** dans les combats
   faibles ; il le deviendrait si un combat récompensait le fait de durer (ennemis qui ne meurent
   pas, objectif de survie), ou avec *Bouclier stabilisé* (Bouclier lancé deux fois : 10 par carte
   à 5).
7. **Freins possibles, si besoin** (non testés) : plafond de bouclier par module (ex. ses PV max),
   perte plus forte au-delà d'un seuil (ex. −1 par tour plus la moitié de l'excédent au-delà de
   10), ou bouclier remis à zéro chaque tour comme dans Slay the Spire (annulerait la décision
   « −1 par tour »).

## Attention aux autres cartes de bouclier

La valeur du Bouclier se compare aux deux autres cartes de bouclier du principal :

| Carte | Coût | Cible | Bouclier |
|---|---|---|---|
| Bouclier | 1 | un module au choix | 3 (essai : 4 à 6) |
| Protéger le vaisseau | 1 | le principal seulement | 5 |
| Blindage ciblé | 2 | un module au choix, 3 munitions | 6 |

- **À 5, Bouclier ferait mieux que Protéger le vaisseau** : même coût, même valeur, mais sur
  n'importe quel module au lieu du seul principal. Protéger le vaisseau n'aurait plus de raison
  d'être, sauf à le remonter aussi.
- **À 6, Bouclier rendrait Blindage ciblé inutile** : même valeur pour un coût de 1 au lieu de 2, et
  sans limite de munitions.

## Conclusion

- **4** : sans risque, mais ne change presque rien à l'intérêt de la carte.
- **5** : le premier palier où la carte devient un vrai choix, mais elle dépasse alors *Protéger le
  vaisseau* : à n'envisager qu'en revoyant aussi cette carte (par exemple 6 ou 7 sur le principal).
- **6** : le plus efficace, mais *Blindage ciblé* et *Protéger le vaisseau* perdent tout intérêt.
- Si l'équilibre entre les trois cartes compte plus que la force du Bouclier, **rester à 3 ou passer
  à 4** garde la hiérarchie actuelle (Bouclier < Protéger le vaisseau < Blindage ciblé).

## Solution choisie (décision utilisateur, 2026-11-11)

Les trois cartes de bouclier montent ensemble, pour que Bouclier devienne un vrai choix sans
écraser les deux autres :

| Carte | Coût | Cible | Avant | **Après** |
|---|---|---|---|---|
| Bouclier | 1 | un module au choix | 3 | **5** |
| Protéger le vaisseau | 1 | le principal seulement | 5 | **7** |
| Blindage ciblé | 2 | un module au choix, 3 munitions | 6 | **8** |

- La hiérarchie est gardée : Bouclier (5, souple) < Protéger le vaisseau (7, principal seulement)
  < Blindage ciblé (8, mais coût 2 et 3 munitions).
- Appliqué dans `config/carte_new.json` (et reporté dans `config/cartes.json`, encore lu par le jeu
  actuel). L'accumulation (§ « Accumulation ») reste à surveiller ; aucun frein n'est ajouté pour
  l'instant.
- Effet sur l'ensemble des combats : voir la campagne refaite avec ces valeurs,
  `analyse_2026-11-11_combat_new.md` (partie « Bouclier »).
