# Proposition : cartes du Lanceur de missiles

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **Rien n'est codé** : ce
fichier propose un jeu de cartes complet pour le module Lanceur de missiles (`MOD_2`) et
l'implémentation des mécanismes nouveaux qu'il demande. Les choix marqués « décision
utilisateur » sont validés (questions posées une par une le 2026-11-18) ; **toutes les valeurs
numériques (coûts, dégâts, munitions) sont des valeurs inventées**, à ajuster.*

---

## 1. Intention (décision utilisateur, 2026-11-18)

- Le Lanceur est le module **spécialisé en attaque**, sur cible unique comme en zone.
- Les ennemis deviennent de plus en plus forts : le joueur doit pouvoir **faire monter ses dégâts
  très haut** avec les bonnes cartes (« scaling »).
- **Toutes les cartes font des dégâts, en empêchent, ou agissent sur les dégâts**, et peuvent faire
  autre chose en plus (bouclier, pioche, électricité…).
- La puissance dépend de la rareté. Demande : au moins **3 légendaires, 8 rares, 15 communes**,
  de coûts variés. Après la revue du 2026-11-21 (§5) : **4 légendaires, 12 rares, 21 communes** (37 cartes).

### 1.1 Repère de puissance (proposition)

Électricité : 3 par tour, 5 cartes piochées. Laser (base) : 6 dégâts pour 1⚡.

| Rareté | Cible unique | Zone (par ennemi) |
|---|---|---|
| Commune | ≈ 7 dégâts par ⚡ | ≈ 4–5 par ⚡ |
| Rare | ≈ 9–10 dégâts par ⚡ (+30 à 40 %) | ≈ 6–8 par ⚡ |
| Légendaire | change la façon de jouer (moteur de dégâts, effet jusqu'à la fin du combat) | |

### 1.2 Réponses de l'utilisateur sur les nouveautés (2026-11-18)

| # | Nouveauté | Décision utilisateur |
|---|---|---|
| 1 | **Verrouillage** (statut ennemi : +X dégâts par coup reçu, −1 par tour) | **Oui, tel que proposé**, nom validé. *Une seule carte, c'est peu* → 4 cartes ici |
| 2 | **Rebond** (coups sur des ennemis tirés au hasard) | **Oui, hasard total** : un rebond peut retoucher le même ennemi |
| 3 | **Exécution** (bonus si la carte tue) | **Oui, une fois par ennemi tué** par la carte, pas seulement la cible |
| 4 | **Calibrage** (la carte gagne des dégâts à chaque fois qu'on la joue) | **Oui, pour toutes les copies de la carte**, mais **pour le combat seulement, jamais pour la partie** |
| 5 | Trophée (gain de dégâts pour toute la partie) | **Non** |
| 6 | Coût X | **Non** |
| 7 | **Rechargement** (rend des munitions) | **Oui, y compris aux cartes épuisées** |
| 8 | **Perforant** (ignore les protections) | **Oui, ignore tout** (bouclier, leurre, renvoi), **sur une seule carte, exprès** |
| 9 | **Portée « même colonne que la cible »** | **Oui** |
| 10 | **Répétition limitée au tour** | **Oui** |
| 11 | Bonus de dégâts « ce tour » propre au Lanceur | **Non : utiliser la Surcharge** à la place |
| 12 | Dégâts à l'attaquant (Leurre explosif) | **Non. Le Leurre quitte le Lanceur** pour un futur module défensif |
| 13 | **Surcharge figée** (ne baisse plus jusqu'à la fin du combat) | **Oui** |
| 14 | **Cadence de tir** (+1 Surcharge à chaque carte du Lanceur jouée) | **Oui** |
| 15 | **Essaim** (coups au hasard, autant que de cartes jouées dans le combat) | **Oui** |
| 16 | **Destruction** (« carte destruction » = buff qui se déclenche à la mort du module, [refonte-destruction.md](refonte-destruction.md)) | **Oui** ; rareté et sort de Guerre nucléaire laissés à l'agent → proposition : *Soute piégée* en rare, *Guerre nucléaire* reste légendaire et est renforcée |
| 17 | Lasers en surchauffe (CRT_51) | **Remplacée** par *Post-combustion* (même id, Surcharge 4) |

---

## 2. Les cartes

### 2.1 Comment lire le tableau

- **Id** : les cartes existantes gardent leur id ; les nouvelles ont un **id proposé** (`CRT_52`
  et suivants, à la suite du dernier id de `config/cartes.json`).
- **État** : *existante* (inchangée), *modifiée* (valeurs ou effets changés), *nouvelle*.
- **Effets** : notation courte du format de `config/cartes.json` (modules-cartes.md §12.1) :
  `NATURE(valeur)` = `{"nature": "NATURE", "valeur": "valeur"}`, `@PORTEE` = `"portee"`,
  `[clé=…]` = une autre clé de l'effet. Les noms en **gras** sont nouveaux (§3).
- **Mécanique à coder** : la ou les mécaniques de §3 nécessaires ; « — » = jouable avec le moteur
  actuel. Une carte qui demande du code reste `"jouable": "non"` jusqu'à ce qu'il soit fait
  (CLAUDE.md racine).
- **Module** : toutes les cartes ont `"modules": ["MOD_2"]`, **Munitions** vide = illimitées,
  **Lancements** vide = 1, **Persistante** : aucune.

### 2.2 Communes (21)

| Id | Nom | État | Catégorie | Cible | Coût | Mun. | Lanc. | Description affichée | Valeurs | Effets | Mécanique à coder |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_13 | Missile à fragmentation | modifiée (nom, ex-Missiles) | Attaque | Ennemi Unique | 2 | | | Inflige {degats_cible} dégâts à un ennemi et {degats_autres} à tous les autres | `degats_cible: 15, degats_autres: 6` | `DEGATS(degats_cible)` ; `DEGATS(degats_autres) @AUTRES_ENNEMIS` | — |
| CRT_14 | Vague de torpilles | modifiée (nom, ex-Torpille) | Attaque | Ennemi Tous | 2 | | | Inflige {degats_avant} dégâts à la ligne avant et {degats_arriere} à la ligne arrière | `degats_avant: 10, degats_arriere: 8` | `DEGATS(degats_avant) @LIGNE_AVANT_ENNEMIE` ; `DEGATS(degats_arriere) @LIGNE_ARRIERE_ENNEMIE` | — |
| CRT_9 | Ogive légère | modifiée (nom, ex-Bombardement ; 6 → 5) | Attaque | Ennemi Tous | 1 | | | Inflige {degats} dégâts à tous les ennemis | `degats: 5` | `DEGATS(degats)` | — |
| CRT_16 | Torpille arrière | modifiée (nom, ex-Ligne arrière ; 8 → 9) | Attaque | Ennemi Arriere | 1 | | | Inflige {degats} dégâts à tous les ennemis de la ligne arrière | `degats: 9` | `DEGATS(degats)` | — |
| CRT_81 | Torpille avant | nouvelle (demandée par l'utilisateur) | Attaque | Ennemi Avant | 1 | | | Inflige {degats} dégâts à tous les ennemis de la ligne avant | `degats: 9` | `DEGATS(degats)` | — |
| CRT_52 | Mini-missile | nouvelle | Attaque | Ennemi Unique | 0 | | | Inflige {degats} dégâts à un ennemi | `degats: 4` | `DEGATS(degats)` | — |
| CRT_53 | Missile guidé | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi. Piochez {pioche} carte | `degats: 7, pioche: 1` | `DEGATS(degats)` ; `PIOCHE(pioche)` | — |
| CRT_54 | Missile de couverture | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi et donne {bouclier} de bouclier au module principal | `degats: 6, bouclier: 5` | `DEGATS(degats)` ; `BOUCLIER(bouclier) @`**`MODULE_PRINCIPAL`** | portées vers un module (§3.1) |
| CRT_55 | Ogive surchauffée | nouvelle | Attaque | Ennemi Tous | 1 | | | Surcharge {surcharge}, puis inflige {degats} dégâts (+ Surcharge) à tous les ennemis | `degats: 3, surcharge: 2` | `SURCHARGE(surcharge) @MODULE_PRINCIPAL` ; `DEGATS(degats)` | Surcharge (§3.2), portées (§3.1) |
| CRT_56 | Missile marqueur | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi et lui pose Verrouillage {verrouillage} | `degats: 5, verrouillage: 2` | `DEGATS(degats)` ; **`VERROUILLAGE`**`(verrouillage)` | Verrouillage (§3.3) |
| CRT_57 | Ogive de marquage | nouvelle | Attaque | Ennemi Tous | 1 | | | Inflige {degats} dégâts à tous les ennemis et leur pose Verrouillage {verrouillage} | `degats: 3, verrouillage: 2` | `DEGATS(degats)` ; `VERROUILLAGE(verrouillage)` | Verrouillage (§3.3) |
| CRT_58 | Missiles jumeaux | nouvelle | Attaque | Ennemi Unique | 1 | | 2 | Inflige {degats} dégâts à un ennemi, deux fois | `degats: 4` | `DEGATS(degats)` | — (premier usage de `lancements: 2` sur une carte) |
| CRT_59 | Ogive à dispersion | nouvelle | Attaque | Ennemi Tous | 2 | | | {coups} fois : inflige {degats} dégâts à un ennemi au hasard | `degats: 4, coups: 5` | `DEGATS(degats) @`**`ENNEMI_AU_HASARD`**` [`**`coups`**`=coups]` | Hasard et coups (§3.4) |
| CRT_60 | Coup de grâce | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi. Pour chaque ennemi tué : donne {electricite} électricité en plus ce tour | `degats: 7, electricite: 2` | `DEGATS(degats)` ; **`si_ennemi_tue`**` : GAIN_ELECTRICITE(electricite)` | Exécution (§3.5) |
| CRT_61 | Torpille traversante | nouvelle | Attaque | Ennemi Unique | 2 | | | Inflige {degats_cible} dégâts à un ennemi et {degats_colonne} à l'ennemi de sa colonne (derrière ou devant) | `degats_cible: 12, degats_colonne: 8` | `DEGATS(degats_cible)` ; `DEGATS(degats_colonne) @`**`MEME_COLONNE`** | portée même colonne (§3.1) |
| CRT_62 | Torpille de barrage | nouvelle | Attaque | Ennemi Avant | 2 | | | Inflige {degats} dégâts à la ligne avant et donne {bouclier} de bouclier au Lanceur | `degats: 12, bouclier: 8` | `DEGATS(degats)` ; `BOUCLIER(bouclier) @`**`MODULE_DE_LA_CARTE`** | portées vers un module (§3.1) |
| CRT_63 | Missile rebondissant | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi, puis rebondit {rebonds} fois au hasard | `degats: 5, rebonds: 1` | `DEGATS(degats)` ; `DEGATS(degats) @ENNEMI_AU_HASARD [coups=rebonds]` | Hasard et coups (§3.4) |
| CRT_64 | Rechargement rapide | nouvelle | Attaque | Ennemi Unique | 0 | | | Inflige {degats} dégâts à un ennemi. Rend {munitions} munition à toutes vos cartes du Lanceur, même épuisées | `degats: 3, munitions: 1` | `DEGATS(degats)` ; **`RECHARGEMENT`**`(munitions) [filtre={module: MOD_2}]` | Rechargement (§3.7), filtre module (§3.9) |
| CRT_65 | Missile thermique | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts et {incendie} d'incendie à un ennemi | `degats: 4, incendie: 3` | `DEGATS(degats)` ; `INCENDIE(incendie)` | — |
| CRT_66 | Calibrage | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi. Toutes vos cartes Calibrage gagnent +{gain} dégâts jusqu'à la fin du combat | `degats: 4, gain: 3` | `DEGATS(degats)` ; **`CALIBRAGE`**`(gain) [`**`augmente`**`=degats]` | Calibrage (§3.6) |
| CRT_67 | Torpille perforante | nouvelle | Attaque | Ennemi Unique | 1 | 3 | | Inflige {degats} dégâts à un ennemi, en ignorant bouclier, leurre et renvoi | `degats: 9` | `DEGATS(degats) [`**`perforant`**`=true]` | Perforant (§3.8) |

### 2.3 Rares (12)

| Id | Nom | État | Catégorie | Cible | Coût | Mun. | Lanc. | Description affichée | Valeurs | Effets | Mécanique à coder |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_15 | Ogive lourde | modifiée (nom, ex-Ciel de missiles ; 8 → 7) | Attaque | Ennemi Tous | 1 | | | Inflige {degats} dégâts à tous les ennemis | `degats: 7` | `DEGATS(degats)` | — |
| CRT_17 | Missile incendiaire | modifiée (nom, ex-Embrasement ; + dégâts) | Attaque | Ennemi Unique | 2 | | | Inflige {degats} dégâts et {incendie} d'incendie à un ennemi | `degats: 6, incendie: 8` | `DEGATS(degats)` ; `INCENDIE(incendie)` | — |
| CRT_51 | Post-combustion | modifiée (ex-Lasers en surchauffe ; 2 → 4) | Buff | Module Principal | 1 | 3 | | Surcharge {surcharge} | `surcharge: 4` | `SURCHARGE(surcharge)` | Surcharge (§3.2) |
| CRT_68 | Amplificateur | nouvelle | Buff | Module Principal | 1 | 2 | | Double votre Surcharge | `facteur: 2` | **`MULTIPLIER_SURCHARGE`**`(facteur)` | Surcharge (§3.2) |
| CRT_69 | Missile à ricochets | nouvelle | Attaque | Ennemi Unique | 2 | | | Inflige {degats} dégâts à un ennemi, puis rebondit {rebonds} fois au hasard | `degats: 6, rebonds: 3` | `DEGATS(degats)` ; `DEGATS(degats) @ENNEMI_AU_HASARD [coups=rebonds]` | Hasard et coups (§3.4) |
| CRT_70 | Chasseur de primes | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi. Pour chaque ennemi tué : donne {electricite} électricité en plus ce tour et piochez {pioche} cartes | `degats: 10, electricite: 2, pioche: 2` | `DEGATS(degats)` ; `si_ennemi_tue : GAIN_ELECTRICITE(electricite), PIOCHE(pioche)` | Exécution (§3.5) |
| CRT_71 | Double frappe | nouvelle | Buff | Module Principal | 1 | 2 | | Ce tour, vos attaques à cible unique sont lancées {repetition} fois de plus | `repetition: 1, tours: 1` | `REPETITION(repetition) [duree=tours, filtre={categorie: Attaque, cible: Ennemi Unique}]` | Répétition au tour (§3.10), filtre cible (§3.9) |
| CRT_72 | Armer le lanceur | nouvelle | Buff | Module Principal | 1 | | | Piochez {pioche} cartes. Surcharge {surcharge} | `pioche: 2, surcharge: 2` | `PIOCHE(pioche)` ; `SURCHARGE(surcharge)` | Surcharge (§3.2) |
| CRT_73 | Missile verrouilleur | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi et lui pose Verrouillage {verrouillage} | `degats: 4, verrouillage: 5` | `DEGATS(degats)` ; `VERROUILLAGE(verrouillage)` | Verrouillage (§3.3) |
| CRT_74 | Missile de précision | nouvelle | Attaque | Ennemi Unique | 2 | | | Inflige {degats} dégâts à un ennemi, plus {par_point} par point de Verrouillage de la cible | `degats: 8, par_point: 3` | `DEGATS(degats) [`**`bonus`**`={par: VERROUILLAGE_CIBLE, facteur: par_point}]` | Verrouillage (§3.3), bonus calculé (§3.11) |
| CRT_75 | Missile surchargé | nouvelle | Attaque | Ennemi Unique | 2 | | | Inflige {degats} dégâts à un ennemi, plus {par_point} par point de Surcharge | `degats: 6, par_point: 2` | `DEGATS(degats) [bonus={par: SURCHARGE_JOUEUR, facteur: par_point}]` | Surcharge (§3.2), bonus calculé (§3.11) |
| CRT_76 | Piéger le lanceur | nouvelle | Buff | Module Principal | 1 | 1 | | Destruction (Lanceur) : {degats_explosion} dégâts à tous les ennemis | `degats_explosion: 30` | **`DESTRUCTION`**` @MODULE_DE_LA_CARTE [declenche=DEGATS(degats_explosion) @TOUS_ENNEMIS]` | Destruction (§3.12), portées (§3.1) |

### 2.4 Légendaires (4)

| Id | Nom | État | Catégorie | Cible | Coût | Mun. | Lanc. | Description affichée | Valeurs | Effets | Mécanique à coder |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_19 | Ogive nucléaire | modifiée (nom, ex-Guerre nucléaire ; + dégâts, incendie 8 → 4) | Attaque | Ennemi Tous | 3 | | | Inflige {degats} dégâts et {incendie} d'incendie à tous les ennemis | `degats: 15, incendie: 4` | `DEGATS(degats)` ; `INCENDIE(incendie)` | — |
| CRT_77 | Lanceur incandescent | nouvelle | Buff | Module Principal | 2 | 1 | | Double votre Surcharge. Elle ne baisse plus jusqu'à la fin du combat | `facteur: 2` | `MULTIPLIER_SURCHARGE(facteur)` ; **`FIGER_SURCHARGE`** | Surcharge (§3.2) |
| CRT_78 | Feu à volonté | nouvelle | Buff | Module Principal | 2 | 1 | | Jusqu'à la fin du combat, vos cartes du Lanceur sont lancées {repetition} fois de plus | `repetition: 1` | `REPETITION(repetition) [filtre={module: MOD_2}]` | filtre module (§3.9) |
| CRT_79 | Cadence de tir | nouvelle | Buff | Module Principal | 1 | 1 | | Jusqu'à la fin du combat, chaque carte du Lanceur jouée vous donne Surcharge {surcharge} | `surcharge: 1` | **`SUR_CARTE_JOUEE`**` [filtre={module: MOD_2}, declenche=SURCHARGE(surcharge) @MODULE_PRINCIPAL]` | Réactions (§3.13), Surcharge (§3.2) |

### 2.5 Cartes retirées ou écartées

- **CRT_18 Leurre** : quitte le Lanceur (décision utilisateur), pour un futur module défensif
  (Blindage, modules-cartes.md §4.2). En attendant : `"modules": []`, elle n'est plus proposée
  nulle part (décision utilisateur, 2026-11-18). Elle reste `"jouable": "oui"`, puisque son effet
  est codé.
- **CRT_80 Essaim** : supprimée à la revue (décision utilisateur, 2026-11-21) ; le compteur
  `@CARTES_JOUEES_COMBAT` (§3.4) n'a plus d'utilisateur et n'est pas à coder.
- **Écartées** (décision utilisateur) : *Ogive à trophée* (Trophée), *Frappe de saturation* (coût
  X), *Leurre explosif* (dégâts à l'attaquant).

### 2.6 Exemples de montée en puissance (valeurs inventées)

| Combinaison | Dégâts |
|---|---|
| Missile à ricochets seul : 4 coups de 6 | 24 |
| Tour 1 : Post-combustion (S4) + Amplificateur (S8). Tour 2 (S7) : Missile à ricochets, 4 coups de 6 + 7 | 52 |
| Même chose avec Feu à volonté joué avant : Missile à ricochets frappe 8 fois | 104 |
| Missile verrouilleur (V5) puis Missile de précision : 8 + 3×5 + 5 (Verrouillage) | 28 sur un ennemi |
| Lanceur incandescent à S6 → S12 figée ; chaque Mini-missile (0⚡) fait 4 + 12 | 16 par Mini-missile, tout le combat |
| Ogive nucléaire avec Feu à volonté : lancée 2 fois | 30 + Incendie 8 à tous |

Ces chiffres sont des ordres de grandeur, à vérifier par simulation (`outils/simulation/`), avec
l'accord de l'utilisateur.

---

## 3. Implémentation proposée des mécanismes

Principes communs, repris de l'existant :

- Toute règle va dans `src/gameplay/` (`carte.py` pour le format, `statut.py` pour les statuts,
  `combat.py` pour la résolution) ; PC (`src/ui/`) et web (`src/web/`) **affichent seulement**
  (CLAUDE.md racine).
- Le format reste celui de `config/cartes.json` : valeurs nommées, `effets` qui y renvoient. Toute
  nouvelle clé est ajoutée à `CLES_EFFET` / `CLES_FILTRE` / aux clés de la carte, sinon le
  chargement la refuse.
- Une nature non codée est déclarée puis refusée par `combat.NATURES_NON_GEREES`, comme
  `SURCHARGE` aujourd'hui : la carte reste `"jouable": "non"`.
- Tout tirage passe par `Combat.aleatoire` (déterminisme, `src/gameplay/CLAUDE.md`).
- Le flux de clics ne change pas : toutes ces cartes se jouent en sélectionnant la carte, puis en
  cliquant sur une case valide (interface.md §8.3).
- **Ordre de calcul d'un coup de carte** (décision utilisateur, 2026-11-18) : valeur de base
  (avec Calibrage) + bonus calculé (§3.11) + Surcharge du joueur + Verrouillage de la cible,
  **puis** les protections (leurre, renvoi, bouclier) sauf si le coup est perforant. Exemple :
  Mini-missile (4) avec Surcharge 3 sur un ennemi Verrouillage 2 avec 5 de bouclier → 9, le bouclier
  en absorbe 5, l'ennemi perd 4 PV.

### 3.1 Nouvelles portées : `MODULE_PRINCIPAL`, `MODULE_DE_LA_CARTE`, `MEME_COLONNE`

- **Pourquoi** : une carte qui vise un ennemi doit pouvoir donner un bouclier ou une Surcharge à un
  module (Missile de couverture, Torpille de barrage, Ogive surchauffée), et la Torpille traversante touche l'autre
  ennemi de la colonne de sa cible.
- **Code** : `PorteeEffet` (dans `carte.py`) gagne trois membres, qui précisent leur camp ; ensuite
  `Combat._cibles_de_l_effet` les résout :
  - `MODULE_PRINCIPAL` → `[self.vaisseau.principal]` ;
  - `MODULE_DE_LA_CARTE` → le module de `carte.exemplaire_module`, ou rien s'il est détruit ;
  - `MEME_COLONNE` → l'autre ennemi vivant de la colonne de la case choisie, ou rien.
- **Point ouvert** : un bouclier sur le module de la carte quand ce module est détruit est perdu
  (proposition), il ne revient pas au principal.
- **Tests** : une case par portée, avec le cas « pas d'ennemi derrière ».

### 3.2 Surcharge, doublement et Surcharge figée (**codés le 2026-11-25**, lot 3 : règles dans combat.md §3.5)

- **Statut** `Statut.SURCHARGE` : cumul `ADDITION`, extinction `MOINS_UN_PAR_TOUR`, porté par le
  module principal (règles dans combat.md §3.5).
- **Application** : dans `Combat._attaquer`, quand la source est une `Carte`, ajouter
  `principal.statuts[SURCHARGE]` aux dégâts **de chaque coup**. L'incendie et le renvoi ne sont pas
  concernés.
- **Ordre dans une carte** : les effets s'appliquent dans l'ordre de la liste. Ogive surchauffée pose
  **d'abord** sa Surcharge, qui profite donc à ses propres dégâts : sur 3 ennemis, (3 + 2) × 3 = 15
  (décision utilisateur, 2026-11-18 ; la description le dit : « Surcharge 2, puis inflige 3 dégâts
  (+ Surcharge) à tous les ennemis »).
- **`MULTIPLIER_SURCHARGE(facteur)`** (Amplificateur, Lanceur incandescent) : nouvelle nature, cible
  le principal ; `intensité ← intensité × facteur`. Elle est sans effet à Surcharge 0.
- **`FIGER_SURCHARGE`** (sans valeur, Lanceur incandescent) : drapeau `Combat.surcharge_figee =
  True` ; `_fin_de_tour_d_entite` saute l'extinction de la Surcharge du principal tant qu'il est
  levé. Il disparaît à la fin du combat, puisque le combat est recréé à chaque fois. Les poses
  suivantes continuent de s'ajouter (proposition).
- **Affichage** : pastille Surcharge sur le principal, infobulle « Surcharge 4 », comme les
  autres statuts (« Surcharge 4 (figée) » une fois figée ; décision utilisateur du 2026-11-25), journal
  « Mini-missile → X : 16 dégâts (dont 12 de surcharge) ».
- **Tests** : Surcharge sur chaque coup d'une zone et de chaque lancement ; baisse de 1 ;
  doublement ; Surcharge figée qui ne baisse plus ; incendie non concerné.

### 3.3 Verrouillage (statut ennemi)

- **Règle** (décision utilisateur) : un ennemi verrouillé X subit **+X dégâts à chaque coup** de
  carte ; cumul `ADDITION` ; **−1 par tour**.
- **Baisse** (proposition) : à la fin du tour du joueur, dans la fin de tour de chaque ennemi
  (combat.md §3.7, point 4). Posé à 2 au tour 1 : +2 pendant le tour 1, +1 pendant le tour 2,
  puis il disparaît. C'est le même rythme que la Surcharge.
- **Code** : `Statut.VERROUILLAGE` dans `statut.py` (`REGLES_STATUT`) ; nature `VERROUILLAGE` dans
  `NatureEffet`, avec `statut_pose = Statut.VERROUILLAGE` (même chemin que `INCENDIE`) ; dans
  `_attaquer`, ajouter `cible.statuts[VERROUILLAGE]` quand la source est une carte.
- **Plus tard** : le même statut pourra servir aux ennemis contre les modules (« marquage »),
  sans rien changer à la règle.
- **Affichage** : pastille sur l'ennemi (une cible, par exemple), infobulle « Verrouillage 3 :
  +3 dégâts à chaque coup reçu, −1 par tour ».
- **Tests** : bonus sur chaque coup, cumul, baisse, disparition à 0, pas de bonus sur l'incendie.

### 3.4 Coups au hasard : portée `ENNEMI_AU_HASARD` et clé `coups` (rebonds, Ogive à dispersion)

- **Règle** (décision utilisateur) : chaque coup tire **un ennemi vivant au hasard, sans
  restriction** ; il peut retoucher le même ennemi.
- **Format** :
  - portée `ENNEMI_AU_HASARD` ;
  - clé d'effet `coups` : le **nom d'une valeur** de la carte (`"coups": "rebonds"`) ;
  - sans `coups`, l'effet fait un seul coup.
- **Code** :
  - dans `jouer_carte`, les cibles sont aujourd'hui choisies une fois pour tous les lancements ;
    **exception** pour cette portée : l'ennemi est **tiré au moment de chaque coup**
    (`self.aleatoire.choice(self.flotte.ennemis_vivants())`) ;
  - s'il ne reste aucun ennemi vivant, les coups restants sont perdus (et le combat est gagné).
- **Compteur de cartes jouées** (`@CARTES_JOUEES_COMBAT`) : **abandonné**, Essaim étant supprimée
  (2026-11-21).
- **Lancements** : un Missile à ricochets lancé 2 fois refait toute la séquence (1 coup ciblé + 3 rebonds).
- **Journal** : un événement par coup, comme une attaque normale.
- **Tests** : seed fixée → cibles attendues ; retouche possible du même ennemi ; arrêt quand la
  flotte est vide.

### 3.5 Exécution : clé de carte `si_ennemi_tue`

- **Règle** (décision utilisateur) : les effets se déclenchent **une fois par ennemi tué par la
  carte**, cible principale ou non (zone, rebonds, lancements).
- **Format** : clé de carte `"si_ennemi_tue": [ {effet}, … ]`, même format que `effets`, sans
  cible : seulement les natures sans cible (électricité, pioche, Surcharge sur le principal).
  Exemple :

  ```json
  "si_ennemi_tue": [ {"nature": "GAIN_ELECTRICITE", "valeur": "electricite"},
                     {"nature": "PIOCHE", "valeur": "pioche"} ]
  ```

- **Code** : `Combat` compte les ennemis détruits pendant la carte (`len(self._detruits)` avant
  et après les lancements, ennemis seulement), puis applique `si_ennemi_tue` autant de fois.
- **Dernier ennemi tué** : le combat est gagné, rien n'est appliqué (règle actuelle, combat.md
  §3.8.3).
- **Incendie** : un ennemi tué plus tard par l'incendie posé par la carte ne compte pas
  (proposition).
- **Tests** : 0, 1 et 2 ennemis tués ; ennemi tué par un rebond.

### 3.6 Calibrage

- **Règle** (décision utilisateur) : après la carte, **toutes les copies** de la carte (même id),
  dans toutes les piles, gagnent +gain à la valeur nommée, **jusqu'à la fin du combat
  seulement**.
- **Format** : nature `CALIBRAGE`, `valeur` = gain, nouvelle clé `augmente` = nom de la valeur
  augmentée (`"augmente": "degats"`).
- **Code** : comme `appliquer_repetition`, parcourir `self.deck.toutes_les_cartes() + [carte]` et
  augmenter `valeurs_actuelles[augmente]` des cartes de même id. Les cartes du combat sont des
  copies (`Carte.copie`) : la partie n'est jamais modifiée.
- **Affichage** : la description affichée lit déjà `valeurs_actuelles`, elle montre donc
  « Inflige 9 dégâts » après deux Calibrages.
- **Tests** : deux copies, la seconde gagne aussi ; rien ne reste au combat suivant.

### 3.7 Rechargement

- **Règle** (décision utilisateur) : rend N munitions aux cartes visées, **y compris épuisées**,
  sans dépasser leurs munitions d'origine. Une carte épuisée qui récupère au moins une munition
  **revient dans la défausse**.
- **Format** : nature `RECHARGEMENT`, `valeur` = munitions rendues, `filtre` obligatoire (ici
  `{"module": "MOD_2"}`, §3.9).
- **Code** :
  - `Carte.recharger(n)` ;
  - `Deck` sort de `epuisees` les cartes rechargées et les met dans `defausse` ;
  - les cartes **Hors service** (module détruit) ne sont pas rechargées (proposition) ;
  - les cartes aux munitions illimitées ne sont pas concernées.
- **Tests** : carte à 1/3 → 2/3 ; carte épuisée → défausse avec 1 munition ; plafond ; Hors
  service ignorée.

### 3.8 Perforant (une seule carte, exprès)

- **Règle** (décision utilisateur) : le coup **ignore leurre, renvoi et bouclier** et va
  directement aux PV. Réservé à la Torpille perforante.
- **Format** : clé d'effet booléenne `"perforant": true`, autorisée seulement avec `DEGATS`.
- **Code** : `Statuts.encaisser_attaque(degats, perforant=False)` ; si `perforant`, renvoie
  directement `Encaissement(degats=degats, degats_pv=degats)` ; le leurre **reste en place** et
  annulera le coup suivant (décision utilisateur, 2026-11-18).
- **Tests** : ennemi avec bouclier, leurre et renvoi → tout passe en PV, statuts inchangés.

### 3.9 Filtre de cartes : critères `module` et `cible`

- **Pourquoi** : Feu à volonté, Rechargement rapide et Cadence de tir visent « les cartes du
  Lanceur » ; Double frappe vise « les attaques à cible unique ».
- **Code** : `FiltreCartes` gagne `module: str | None` (type de module, ex. `"MOD_2"`) et
  `cible: CibleCarte | None`, ajoutés à `CLES_FILTRE` et à `correspond`.
- **« Carte du Lanceur »** (proposition) : carte rattachée à un **exemplaire** de module de type
  `MOD_2` (`exemplaire_module` → type), pas « carte dont la liste `modules` contient `MOD_2` ».
  Avec deux Lanceurs, les cartes des deux sont visées.
- **Tests** : correspondance par module et par cible ; refus d'un module inconnu au chargement.

### 3.10 Répétition limitée au tour

- **Règle** (décision utilisateur) : une répétition peut durer **jusqu'à la fin du tour** au lieu
  de jusqu'à la fin du combat.
- **Format** : `REPETITION` accepte la clé `duree` (valeur nommée en tours, `tours: 1` = ce tour) ;
  ajouter `REPETITION` à `NATURES_A_DUREE`. Sans `duree`, le comportement actuel (fin du combat)
  ne change pas.
- **Code** : `Combat` garde la liste des répétitions temporaires (filtre, valeur, tours restants)
  ; à la fin du tour du joueur, il retire les lancements ajoutés aux cartes qui correspondent,
  dans toutes les piles.
- **Tests** : Laser lancé 2 fois ce tour, 1 fois au tour suivant ; carte piochée après la pose
  aussi concernée.

### 3.11 Bonus calculé : clé d'effet `bonus`

- **Pourquoi** : Missile de précision (+3 par point de Verrouillage de la cible) et Missile
  surchargé (+2 par point de Surcharge, **en plus** de la Surcharge normale : l'idée « dégât qui
  utilise le double de la surcharge »).
- **Format** : `"bonus": {"par": "VERROUILLAGE_CIBLE" | "SURCHARGE_JOUEUR", "facteur":
  "<valeur nommée>"}` sur un effet `DEGATS`.
- **Code** : dans `_appliquer_effet_de_carte`, `valeur += facteur × compteur`, lu au moment du
  coup. Le statut n'est pas consommé (proposition).
- **Tests** : Missile de précision sur V0 et V5 ; Missile surchargé à S0 et S8.

### 3.12 Destruction (Piéger le lanceur)

- Reprend le buff Destruction de [refonte-destruction.md](refonte-destruction.md) §1–§3 (nature
  `DESTRUCTION`, liste `declenche`), avec la portée `MODULE_DE_LA_CARTE` (§3.1) pour le poser sur
  le Lanceur.
- **Il faut d'abord trancher** les points de refonte-destruction.md §3 ; propositions par défaut
  retenues ici :
  - déclenchement **immédiat** à la mort du module ;
  - **valeurs figées** au moment où la carte est jouée ;
  - **pas sur le principal**.
- **Code** :
  - champ `Module.destructions` (liste d'effets déclenchés) ;
  - `Combat._traiter_destruction` les applique à la mort d'un module ;
  - nouvelle portée d'effet déclenché `TOUS_ENNEMIS`.
- **Cumul** : Piéger le lanceur jouée deux fois (deux copies, ou une copie rechargée) → deux explosions (décision de refonte-destruction.md
  §3.6).
- **Affichage** : pastille « Destruction » sur le Lanceur, infobulle « À sa destruction : 20
  dégâts à tous les ennemis ».
- **Tests** : explosion à la mort du Lanceur ; victoire si elle tue le dernier ennemi ; deux poses
  → deux explosions.

### 3.13 Réactions jusqu'à la fin du combat : `SUR_CARTE_JOUEE` (Cadence de tir)

- **Règle** (décision utilisateur) : une fois Cadence de tir jouée, **chaque carte du Lanceur
  jouée** jusqu'à la fin du combat donne Surcharge 1.
- **Format** : nature `SUR_CARTE_JOUEE`, sans valeur, avec `filtre` (cartes qui déclenchent) et
  `declenche` (effets appliqués, même format que §3.12).
- **Code** :
  - `Combat.reactions` : liste de (filtre, effets) ;
  - à chaque `jouer_carte`, **après** la résolution de la carte (proposition : la Surcharge gagnée
    profite donc à la carte suivante), appliquer les réactions dont le filtre correspond ;
  - la carte qui pose la réaction ne la déclenche pas elle-même ;
  - deux Cadences de tir → +2 par carte.
- **Affichage** : une ligne de journal « Cadence de tir : Surcharge +1 » ; une icône sur le
  principal (proposition), avec la liste des réactions actives dans l'infobulle.
- **Tests** : 3 cartes du Lanceur jouées → Surcharge 3 ; carte du principal → rien ; cumul de
  deux Cadences.

### 3.14 Ordre de réalisation proposé (une PR par lot)

**Rien n'est codé avant la revue du module principal** (décision utilisateur, 2026-11-21) : le
lot 1 attend que les cartes du principal aient été revues de la même façon (noms, valeurs).

| Lot | Contenu | Cartes rendues jouables |
|---|---|---|
| 1 | Aucune mécanique : nouvelles cartes et valeurs modifiées ; Leurre retiré du Lanceur | Mini-missile, Missile guidé, Missiles jumeaux, Missile thermique, Torpille avant ; valeurs ou noms modifiés : Missile à fragmentation, Vague de torpilles, Ogive légère, Torpille arrière, Ogive lourde, Missile incendiaire, Ogive nucléaire |
| 2 | Portées vers un module et même colonne (§3.1) | Missile de couverture, Torpille de barrage, Torpille traversante |
| 3 | Surcharge, doublement, Surcharge figée, bonus calculé (§3.2, §3.11) | Ogive surchauffée, Post-combustion, Amplificateur, Armer le lanceur, Missile surchargé, Lanceur incandescent |
| 4 | Verrouillage (§3.3) | Missile marqueur, Ogive de marquage, Missile verrouilleur, Missile de précision |
| 5 | Coups au hasard (§3.4) | Ogive à dispersion, Missile rebondissant, Missile à ricochets |
| 6 | Exécution (§3.5) | Coup de grâce, Chasseur de primes |
| 7 | Calibrage, Rechargement, Perforant, filtre module/cible (§3.6–§3.9) | Calibrage, Rechargement rapide, Torpille perforante |
| 8 | Répétition au tour, réactions (§3.10, §3.13) | Double frappe, Feu à volonté, Cadence de tir |
| 9 | Destruction (§3.12), après décision sur refonte-destruction.md §3 | Piéger le lanceur |

Chaque lot :

- regénère `config/cartes.md` et passe `pytest` ;
- est vérifié sur PC et web dès qu'il change l'affichage (pastilles, journal) ;
- met à jour combat.md §3.5 / modules-cartes.md §12 et retire la mécanique de ce fichier et de
  effets-a-coder.md.

---

## 4. Décisions sur les questions ouvertes (décision utilisateur, 2026-11-18)

1. **Ordre de calcul d'un coup** : base + bonus + Surcharge + Verrouillage, puis protections (§3).
2. **Ogive surchauffée** (ex-Mise à feu) : Surcharge d'abord, elle profite à ses propres dégâts ; description changée (§2.2, §3.2).
3. **Essaim** ne se compte pas lui-même (sans objet : Essaim supprimée le 2026-11-21).
4. **Torpille perforante** (ex-Obus perforant) : le leurre de la cible reste en place (§3.8).
5. **Leurre** : `"modules": []` en attendant un module défensif (§2.5).
6. **Légendaires** : 4 gardées sur 5 à la revue du 2026-11-21 (Essaim supprimée).
7. **Valeurs** : réglage à la main par l'utilisateur dans l'éditeur de cartes d'abord, **puis**
   simulation (volume et durée proposés à l'utilisateur avant de la lancer). Prévue d'abord après
   les lots 1 à 3, **repoussée après le lot 5** (décision utilisateur, 2026-11-25 :
   plan-cartes.md §3).

---

## 5. Revue carte par carte (décision utilisateur, 2026-11-21)

Revue des cartes une par une : nom, valeurs, suppression. **Les choix sont reportés au §2**, qui
fait foi ; cette section garde l'historique et les raisons.

### 5.1 Noms : quatre familles

Les noms des cartes du Lanceur reprennent **quatre noms de base**, rendus uniques par un adjectif
ou un complément (décision utilisateur) ; quelques cartes gardent un nom hors famille quand il
est plus clair (Coup de grâce, Rechargement rapide, Calibrage) :

| Famille | Ce que fait la carte |
|---|---|
| **Missile** | frappe un ennemi (avec éventuellement un bonus : pioche, électricité, incendie, rebond) |
| **Torpille** | suit une ligne : ligne avant ou arrière, ennemi derrière la cible, perforation |
| **Ogive** | explose sur tous les ennemis |
| **Lanceur** | buffs (Surcharge, répétition), qui agissent sur le module |

Disparaissent : Bombardement, Roquette, Ciel de missiles, Frappe, Tir, Obus.

### 5.2 Ratio dégâts par électricité

Calculé dans deux cas (convention de grille : combat.md §3.1.1) : **6 ennemis** (3 en ligne
avant, 3 en ligne arrière) et **2 ennemis** (l'un derrière l'autre, même colonne), puis leur
**moyenne**. Dégâts immédiats seulement, sans Surcharge, Verrouillage ni protections ; l'incendie
est compté à part (incendie N = N + (N−1) + … + 1 si l'ennemi survit).

### 5.3 Communes (21) : revue terminée

| Id | Ancien nom | Nouveau nom | Coût | Valeurs décidées | 6 ennemis | 2 ennemis | Moyenne |
|---|---|---|---|---|---|---|---|
| CRT_13 | Missiles | **Missile à fragmentation** | 2 | 15 sur la cible, 6 aux autres (inchangé) | 22,5 | 10,5 | 16,5 |
| CRT_14 | Torpille | **Vague de torpilles** | 2 | 10 ligne avant, 8 ligne arrière (inchangé) | 27 | 9 | 18 |
| CRT_9 | Bombardement | **Ogive légère** | 1 | 5 à tous | 30 | 10 | 20 |
| CRT_16 | Ligne arrière | **Torpille arrière** | 1 | **9** à la ligne arrière (était 8) | 27 | 9 | 18 |
| CRT_81 | *(nouvelle)* | **Torpille avant** | 1 | 9 à la ligne avant (carte demandée par l'utilisateur, symétrique de Torpille arrière) | 27 | 9 | 18 |
| CRT_52 | Roquette | **Mini-missile** | 0 | 4 | 4 gratuits | 4 gratuits | — |
| CRT_53 | Missile guidé | **Missile guidé** | 1 | 7 + pioche 1 | 7 | 7 | 7 |
| CRT_54 | Contre-mesures | **Missile de couverture** | 1 | 6 + 5 bouclier au principal | 6 | 6 | 6 |
| CRT_55 | Mise à feu | **Ogive surchauffée** | 1 | Surcharge 2, puis 3 (+ Surcharge) à tous, soit 5 chacun | 30 | 10 | 20 |
| CRT_56 | Désignation de cible | **Missile marqueur** | 1 | 5 + Verrouillage 2 | 5 | 5 | 5 |
| CRT_57 | Marquage de zone | **Ogive de marquage** | 1 | 3 à tous + **Verrouillage 2** à tous (était 1) | 18 | 6 | 12 |
| CRT_58 | Tir double | **Missiles jumeaux** | 1 | 2 lancements de 4 (champ `lancements`, jouable au lot 1) | 8 | 8 | 8 |
| CRT_59 | Bombes à sous-munitions | **Ogive à dispersion** | 2 | **5 coups** de 4 au hasard (était 4 coups) | 10 | 10 | 10 |
| CRT_60 | Coup de grâce | **Coup de grâce** | 1 | 7 ; **+2 électricité** par ennemi tué (était +1) | 7 | 7 | 7 |
| CRT_61 | Ogive à fragmentation | **Torpille traversante** | 2 | 12 sur la cible + **8** à l'autre ennemi de sa colonne (était 5) | 10 | 10 | 10 |
| CRT_62 | Tir de barrage | **Torpille de barrage** | 2 | **12** à la ligne avant + **8** bouclier au Lanceur (était 8 + 6) | 18 | 6 | 12 |
| CRT_63 | Missile chercheur | **Missile rebondissant** | 1 | **5** + 1 rebond de **5** (était 6 + 6) | 10 | 10 | 10 |
| CRT_64 | Rechargement rapide | **Rechargement rapide** | 0 | 3 + 1 munition à toutes les cartes du Lanceur, **légendaires comprises** (inchangé) | 3 gratuits | 3 gratuits | — |
| CRT_65 | Missile thermique | **Missile thermique** | 1 | 4 + Incendie 3 (inchangé) | 4 (10 avec l'incendie) | 4 (10) | 4 (10) |
| CRT_66 | Calibrage | **Calibrage** | 1 | **4**, puis **+3** à chaque usage (était 5 + 2) | 4, 7, 10… | 4, 7, 10… | — |
| CRT_67 | Obus perforant | **Torpille perforante** | 1 | 9 perforant, 3 munitions (inchangé) | 9 | 9 | 9 |

Remarques de la revue :

- **Ogive surchauffée** fait autant qu'Ogive légère sur la zone et laisse en plus Surcharge 2 :
  elle la domine (choix assumé par l'utilisateur, à revoir éventuellement en fin de revue).
- **Torpille de barrage** reste à 2⚡ parce que les communes ont près de 3 fois plus de cartes
  à 1⚡ qu'à 2⚡ (14 contre 5) ; critère de l'utilisateur : au moins 2 fois plus de cartes à 1⚡.
- **Coup de grâce** à +2⚡ se rapproche de Chasseur de primes (rare) : à revoir avec elle.
- **Vocabulaire** : la portée `MEME_COLONNE` (Torpille traversante) est correcte avec la
  convention de combat.md §3.1.1 (l'ennemi derrière ou devant la cible).

### 5.4 Rares : revue (décision utilisateur, 2026-11-21)

La revue une par une s'arrête aux communes (décision utilisateur : trop long) : les rares sont
revues d'après un tableau de recommandations, ligne par ligne ; les légendaires, plus tard.

| Id | Ancien nom | Nouveau nom | Valeurs décidées | Statut |
|---|---|---|---|---|
| CRT_15 | Ciel de missiles | **Ogive lourde** | 1⚡, **7** à tous (était 8) : moyenne 28 | décidé |
| CRT_17 | Embrasement | **Missile incendiaire** | 2⚡, 6 + Incendie 8 (inchangé : seule valeur nettement au-dessus de 2 Missiles thermiques, 27 contre 23 sur 3 tours, 42 contre 29 au maximum) | décidé |
| CRT_51 | Lasers en surchauffe | **Post-combustion** | 1⚡, Surcharge 4, 3 munitions | décidé |
| CRT_68 | Amplificateur | **Amplificateur** | 1⚡, double la Surcharge, 2 munitions | décidé |
| CRT_69 | Ricochet | **Missile à ricochets** | 2⚡, **6 + 3 rebonds de 6** (était 8 + 4) : 12/⚡ | décidé |
| CRT_70 | Chasseur de primes | **Chasseur de primes** | 1⚡, 10 ; par ennemi tué : +2⚡ et **pioche 2** (était 1) | décidé |
| CRT_71 | Double frappe | **Double frappe** | 1⚡, ce tour : attaques à cible unique lancées 1 fois de plus ; **2 munitions** (était 1) | décidé |
| CRT_72 | Chargeur automatique | **Armer le lanceur** | 1⚡, pioche 2 + Surcharge 2 | décidé |
| CRT_73 | Verrouillage total | **Missile verrouilleur** | 1⚡, 4 + Verrouillage 5 | décidé |
| CRT_74 | Frappe de précision | **Missile de précision** | 2⚡, 8 + 3 par point de Verrouillage de la cible | décidé |
| CRT_75 | Frappe surchargée | **Missile surchargé** | 2⚡, 6 + 2 par point de Surcharge | décidé |
| CRT_76 | Soute piégée | **Piéger le lanceur** | **1⚡** (était 2), catégorie **Buff** ; **plus de dégâts immédiats** : à la destruction du Lanceur, **30 à tous les ennemis** (était 6 immédiat + 20) ; **1 munition** (pour limiter le cumul ; la rejouer après un Rechargement est voulu) | décidé |

Remarques :

- **Piéger le lanceur** : le joueur ne contrôle pas la destruction (sacrifice volontaire non codé,
  refonte-destruction.md), qui lui coûte déjà les cartes du Lanceur : d'où un coût bas et une
  explosion forte. **1 munition** pour limiter le cumul (décision utilisateur) ; une copie
  rejouée après Rechargement rapide est voulue. Les munitions comptent par copie : deux copies
  dans le deck peuvent donner 60 à tous : **accepté** (décision utilisateur, 2026-11-21).
- **Coûts des rares** après la revue : 8 à 1⚡, 4 à 2⚡ (Missile incendiaire, Missile à ricochets,
  Missile de précision, Missile surchargé).

### 5.5 Légendaires : revue (décision utilisateur, 2026-11-21)

| Id | Ancien nom | Nouveau nom | Valeurs décidées | Statut |
|---|---|---|---|---|
| CRT_19 | Guerre nucléaire | **Ogive nucléaire** | 3⚡, **15 à tous + Incendie 4**, **munitions illimitées** (était 20 + Incendie 10, 1 munition) : 24 par ennemi sur 3 tours, un peu plus que 3 Ogives lourdes (21) en une seule carte | décidé |
| CRT_77 | Surcharge critique | **Lanceur incandescent** | 2⚡, 1 munition, double la Surcharge et la fige (inchangé) | décidé |
| CRT_78 | Feu à volonté | **Feu à volonté** | 2⚡, 1 munition, cartes du Lanceur lancées 1 fois de plus jusqu'à la fin du combat (inchangé) | décidé |
| CRT_79 | Cadence de tir | **Cadence de tir** | 1⚡, 1 munition, Surcharge +1 par carte du Lanceur jouée jusqu'à la fin du combat (inchangé) | décidé |
| CRT_80 | Essaim | — | **supprimée** (décision utilisateur) | supprimée |

Remarques :

- **Une munition** pour les trois buffs « jusqu'à la fin du combat » : les rejouer reviendrait à
  les cumuler (comme les cartes Pouvoir de Slay the Spire). **Ogive nucléaire**, attaque
  ponctuelle, n'a plus de munitions, ce qui varie les légendaires.
- Avec Feu à volonté, Ogive nucléaire est lancée 2 fois : 30 + Incendie 8 à tous (combo voulu).
- **Revue terminée** : 21 communes, 12 rares, 4 légendaires (37 cartes), reportées au §2.
