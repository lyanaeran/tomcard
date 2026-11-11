# Essai — carte Bouclier à 3 ou à 4 — 11 novembre 2026

## Ce qui a été testé

| | |
|---|---|
| **Question** | La carte *Bouclier* (CRT_10, coût 1, Module Unique) donne 3 de bouclier. Passer à 4 la rend-elle plus utile, ou trop forte ? |
| **Combats** | **20 combats difficiles**, joués deux fois avec les **mêmes graines** (même deck mélangé, mêmes ennemis, mêmes tirages) : une fois avec Bouclier à 3, une fois à 4. Seule la valeur de la carte change |
| **Flottes** | Les 5 plus dures de la campagne du jour (`analyse_2026-11-11_combat_new.md`), 4 combats chacune : Le nettoyeur + Le puzzle, Pat + Le nettoyeur, Le nettoyeur + Le nettoyeur, Petit Jean + Petit Jean, le Boss |
| **Joueur** | Deck de départ (4 Bouclier sur 11 cartes), principal 60 PV, Lanceur de missiles 20 PV, bot de recherche avec la valeur du deck |
| **Code** | `config/carte_new.json` n'est **pas modifié** : la valeur est changée seulement sur les cartes du combat simulé (`construire_combat(..., valeurs_cartes=...)`) |
| **Reproduire** | `python -m outils.simulation.essai_bouclier` (11 secondes) |

**Attention, petit échantillon** : 4 combats par flotte. Un écart d'une victoire ou de quelques PV
peut venir du hasard. L'essai sert à voir un ordre de grandeur, pas à trancher au point près.

---

## Résultats

| Flotte | Bouclier | Victoires | PV principal perdus (moy.) | Tours | Bouclier joué quand il est en main | Dégâts absorbés par les boucliers |
|---|---|---|---|---|---|---|
| Le nettoyeur + Le puzzle | 3 | 3/4 | 40,0 | 5,0 | 11 % | 9,2 |
| | 4 | 3/4 | 39,8 | 5,0 | 11 % | 10,2 |
| Pat + Le nettoyeur | 3 | 4/4 | 36,2 | 5,5 | 8 % | 12,2 |
| | 4 | 4/4 | 35,5 | 5,5 | 8 % | 13,0 |
| Le nettoyeur + Le nettoyeur | 3 | 4/4 | 29,5 | 5,0 | 15 % | 9,5 |
| | 4 | 4/4 | 28,0 | 5,0 | 15 % | 11,0 |
| Petit Jean + Petit Jean | 3 | 2/4 | 41,0 | 19,5 | 28 % | 54,0 |
| | 4 | 3/4 | 39,5 | 21,5 | 32 % | 76,5 |
| Boss | 3 | 3/4 | 34,2 | 13,5 | 42 % | 55,2 |
| | 4 | 3/4 | **27,0** | 13,5 | 41 % | 64,5 |
| **Total** | **3** | **16/20** | **36,2** | 9,7 | **27 %** | 28,1 |
| **Total** | **4** | **17/20** | **34,0** | 10,1 | **28 %** | 35,0 |

## Ce qu'on en retient

1. **Bouclier à 4 n'est pas trop fort** : sur ces combats difficiles, il fait gagner **2 PV par
   combat** en moyenne (36,2 → 34,0) et une victoire de plus sur 20. C'est un petit gain.
2. **Le gain se concentre sur les combats longs** : contre le Boss, 7 PV de moins perdus
   (34,2 → 27,0) ; contre les deux Petit Jean, une victoire de plus. Dans les combats courts et
   violents (Le nettoyeur), presque rien ne change (1 à 1,5 PV).
3. **Le bot ne le joue pas plus souvent** : 27 % → 28 % quand il l'a en main. À 4, la carte reste
   jugée moins utile qu'une attaque dans la plupart des situations. Le passage à 4 ne règle donc
   pas le constat de la campagne (« Bouclier, la carte la moins jouée du deck de départ ») : elle
   protège un peu mieux quand elle est jouée, sans devenir un meilleur choix.
4. **Pourquoi** : contre Le nettoyeur, les combats durent 5 tours et le meilleur moyen de se
   protéger est de tuer vite ; un bouclier qui perd 1 par tour sert surtout dans les combats longs.

## Conclusion

Passer Bouclier à 4 est **sans risque** (pas de déséquilibre visible) mais **peu efficace** pour
rendre la carte intéressante : elle reste peu jouée. Si le but est qu'elle soit plus souvent un bon
choix, d'autres pistes sont possibles (non testées, à décider) : l'associer à un petit effet en
plus (piocher une carte, par exemple), ou réduire son coût. Rester à 3 ne pose pas de problème
non plus : la carte garde son rôle dans les combats longs (Boss, Petit Jean).
