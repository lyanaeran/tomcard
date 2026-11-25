# Proposition : cartes du module principal

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **Rien n'est codé** : ce
fichier propose un jeu de cartes pour le module principal (`MOD_1`) et l'implémentation des
mécanismes nouveaux qu'il demande. Les choix marqués « décision utilisateur » sont validés
(questions posées une par une le 2026-11-22) ; **toutes les valeurs numériques sont des valeurs
inventées**, à ajuster. Il complète [proposition-lanceur-missiles.md](proposition-lanceur-missiles.md),
dont il réutilise plusieurs mécaniques (◆).*

---

## 1. Intention (décision utilisateur, 2026-11-21)

- À peu près **le même nombre de cartes que le Lanceur** : **20 communes, 12 rares, 4
  légendaires**, plus les 4 cartes de base, inchangées (Laser, Bouclier, Protéger le vaisseau,
  Réparation).
- Des **cartes basiques qui exploitent les mécanismes principaux** : le principal est le
  **socle** du vaisseau (attaque simple, défense, réparation, ressources, répétition). Peu de zone :
  c'est le rôle du Lanceur.

### 1.1 Repère de puissance (proposition, guide `designer-contenu`)

3⚡ par tour, pioche de 5. Laser (base) = 6 dégâts pour 1⚡.

| Rareté | Par ⚡ | Équivalences |
|---|---|---|
| Commune | ≈ 7 dégâts ou 7 de bouclier | 1 bouclier ≈ 1 dégât ; 1 pioche ≈ 3–4 ; +1⚡ ≈ 6 |
| Rare | ≈ 9–10 | |
| Légendaire | change la façon de jouer | |

### 1.2 Familles de noms (décision utilisateur, 2026-11-22)

| Famille | Ce que fait la carte |
|---|---|
| **Laser** | attaque, surtout sur un ennemi |
| **Bouclier** | défense : bouclier, renvoi |
| **Réparation** | rend des PV |
| **Réacteur** | électricité, pioche, Surcharge |
| **Protocole** | buffs, répétition, pioche, Verrouillage |

La famille devient un **champ des cartes** (§3.1), que les buffs peuvent viser.

### 1.3 Réponses de l'utilisateur (2026-11-22)

| # | Question | Décision utilisateur |
|---|---|---|
| 1 | Cinq familles de noms | **Oui** |
| 2 | ✱ Champ « famille » et buffs qui visent une famille | **Oui**. *Salve laser* garde le **Laser de base** ; une **autre carte** booste **toute la famille Laser** → **Protocole laser**, légendaire, jusqu'à la fin du combat |
| 3 | Surcharge et Verrouillage (◆, du Lanceur) sur le principal | **Oui, les 3 cartes** (Laser de visée, Réacteur en surtension, Protocole de ciblage) |
| 4 | Laser de contre-charge (dégâts = bouclier du principal) : plafond ? | **Pas de plafond, mais il consomme le bouclier** |
| 5 | ✱ Renvoi pour le joueur | **Oui, les 2 cartes** (Bouclier réfléchissant, Bouclier miroir) |
| 6 | ✱ Électricité au tour suivant (Réacteur à condensateur) | **Oui**, +2⚡ au tour suivant |
| 7 | ✱ Retirer les protections (Laser disrupteur) | Retirer bouclier et renvoi : **trop fort**. **Retire 8 de bouclier (pas le renvoi), puis 6 dégâts** |
| 8 | ✱ Garder l'électricité non dépensée (Réacteur à batterie) | **Oui, sans maximum**, et la carte **coûte 2⚡** |
| 9 | Protocole de riposte (dégâts à l'attaquant) | **Non** (comme pour le Leurre explosif) : remplacé par **5 de bouclier + Renvoi 5 au principal** |
| 10 | ✱ Bouclier qui ne baisse plus (Bouclier éternel) | **Pour le futur module de défense**, pas pour le principal |
| 11 | ✱ Effet au début de chaque tour (Réacteur à fusion) | **Oui, à 3⚡** (combat long : rentabilisé au tour 4) |
| 12 | Cartes actuelles modifiées | **Acceptées** : Laser lourd (2⚡, 14), Laser incendiaire (ex-Tir incendiaire). **Refusées** : Blindage ciblé, Protocole d'urgence et Bouclier stabilisé restent **inchangés** |

---

## 2. Les cartes

### 2.1 Comment lire le tableau

Même notation que [proposition-lanceur-missiles.md](proposition-lanceur-missiles.md) §2.1 :
`NATURE(valeur)`, `@PORTEE`, `[clé=…]` ; noms en **gras** = nouveaux. Toutes les cartes ont
`"modules": ["MOD_1"]` ; **Mun.** vide = illimitées ; **Lanc.** vide = 1. **Id** : les cartes
existantes gardent le leur, les nouvelles ont un **id proposé** à partir de `CRT_82` (après les
ids proposés pour le Lanceur).

**Mécanique à coder** : « — » = jouable avec le moteur actuel ; **◆** = mécanique décidée pour le
Lanceur (voir sa §3) ; **✱** = mécanique nouvelle, décrite au §3 ci-dessous.

### 2.2 Communes (20)

| Id | Nom | Famille | État | Catégorie | Cible | Coût | Mun. | Lanc. | Description affichée | Valeurs | Effets | Mécanique à coder |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_8 | Laser perçant | Laser | existante | Attaque | Ennemi Ligne | 2 | | | Inflige {degats} dégâts à la ligne ciblée | `degats: 8` | `DEGATS(degats)` | — (cible et description corrigées au lot 0, 2026-11-25) |
| CRT_47 | Laser lourd | Laser | modifiée (1⚡ 12 → 2⚡ 14) | Attaque | Ennemi Unique | 2 | | | Inflige {degats} dégâts à un ennemi | `degats: 14` | `DEGATS(degats)` | — |
| CRT_45 | Laser incendiaire | Laser | modifiée (ex-Tir incendiaire : 2⚡, 3 mun., Incendie 4) | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts et {incendie} d'incendie à un ennemi | `degats: 2, incendie: 4` | `DEGATS(degats)` ; `INCENDIE(incendie)` | — |
| CRT_82 | Laser d'appoint | Laser | nouvelle | Attaque | Ennemi Unique | 0 | | | Inflige {degats} dégâts à un ennemi. Piochez {pioche} carte | `degats: 2, pioche: 1` | `DEGATS(degats)` ; `PIOCHE(pioche)` | — |
| CRT_83 | Laser défensif | Laser | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi et donne {bouclier} de bouclier au module principal | `degats: 4, bouclier: 3` | `DEGATS(degats)` ; `BOUCLIER(bouclier) @MODULE_PRINCIPAL` | ◆ portées vers un module |
| CRT_84 | Laser double | Laser | nouvelle | Attaque | Ennemi Unique | 1 | | 2 | Inflige {degats} dégâts à un ennemi, deux fois | `degats: 3` | `DEGATS(degats)` | — |
| CRT_85 | Laser de visée | Laser | nouvelle | Attaque | Ennemi Unique | 1 | | | Inflige {degats} dégâts à un ennemi et lui pose Verrouillage {verrouillage} | `degats: 4, verrouillage: 2` | `DEGATS(degats)` ; `VERROUILLAGE(verrouillage)` | ◆ Verrouillage |
| CRT_46 | Blindage ciblé | Bouclier | existante (inchangée, décision utilisateur) | Defense | Module Unique | 2 | 3 | | Bouclier de {bouclier} sur un module unique | `bouclier: 8` | `BOUCLIER(bouclier)` | — |
| CRT_86 | Bouclier d'escadre | Bouclier | nouvelle | Defense | Module Tous | 1 | | | Donne {bouclier} de bouclier à tous vos modules | `bouclier: 4` | `BOUCLIER(bouclier)` | — |
| CRT_87 | Bouclier avant | Bouclier | nouvelle | Defense | Module Avant | 1 | | | Donne {bouclier} de bouclier aux modules de la ligne avant | `bouclier: 6` | `BOUCLIER(bouclier)` | — |
| CRT_88 | Bouclier réactif | Bouclier | nouvelle | Defense | Module Unique | 1 | | | Donne {bouclier} de bouclier à un module. Piochez {pioche} carte | `bouclier: 4, pioche: 1` | `BOUCLIER(bouclier)` ; `PIOCHE(pioche)` | — |
| CRT_89 | Bouclier chargé | Bouclier | nouvelle | Defense | Module Principal | 2 | | | Donne {bouclier} de bouclier au module principal | `bouclier: 14` | `BOUCLIER(bouclier)` | — |
| CRT_90 | Bouclier réfléchissant | Bouclier | nouvelle | Defense | Module Unique | 1 | | | Renvoi {renvoi} sur un module : il renvoie à l'attaquant les dégâts reçus | `renvoi: 5` | **`RENVOI`**`(renvoi)` | ✱ Renvoi (§3.2) |
| CRT_91 | Réparation rapide | Réparation | nouvelle | Reparation | Module Principal | 0 | 2 | | Répare le module principal pour {reparation} | `reparation: 4` | `REPARATION(reparation)` | — |
| CRT_92 | Réparation de champ | Réparation | nouvelle | Reparation | Module Tous | 1 | 2 | | Répare tous vos modules pour {reparation} | `reparation: 4` | `REPARATION(reparation)` | — |
| CRT_93 | Réacteur d'appoint | Réacteur | nouvelle | Outils | Module Principal | 0 | 2 | | Donne {electricite} électricité en plus ce tour | `electricite: 1` | `GAIN_ELECTRICITE(electricite)` | — |
| CRT_94 | Réacteur à condensateur | Réacteur | nouvelle | Outils | Module Principal | 1 | | | Donne {electricite} électricité en plus au prochain tour | `electricite: 2` | **`GAIN_ELECTRICITE_DIFFERE`**`(electricite)` | ✱ électricité différée (§3.3) |
| CRT_95 | Réacteur en surtension | Réacteur | nouvelle | Buff | Module Principal | 1 | | | Surcharge {surcharge}. Piochez {pioche} carte | `surcharge: 2, pioche: 1` | `SURCHARGE(surcharge)` ; `PIOCHE(pioche)` | ◆ Surcharge |
| CRT_96 | Protocole d'analyse | Protocole | nouvelle | Outils | Module Principal | 1 | | | Piochez {pioche} cartes | `pioche: 2` | `PIOCHE(pioche)` | — |
| CRT_97 | Protocole de tir | Protocole | nouvelle | Buff | Module Principal | 1 | 2 | | Ce tour, vos cartes Laser sont lancées {repetition} fois de plus | `repetition: 1, tours: 1` | `REPETITION(repetition) [duree=tours, filtre={famille: Laser}]` | ◆ répétition au tour, ✱ filtre famille (§3.1) |

Coûts : 3 à 0⚡, 13 à 1⚡, 4 à 2⚡ (au moins 2 fois plus de cartes à 1⚡ qu'à 2⚡, critère de la
revue du Lanceur).

### 2.3 Rares (12)

| Id | Nom | Famille | État | Catégorie | Cible | Coût | Mun. | Lanc. | Description affichée | Valeurs | Effets | Mécanique à coder |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_49 | Salve laser | Protocole | existante (décision utilisateur : reste sur le Laser de base) | Buff | Module Tous | 2 | 2 | | Les Laser de base sont lancés {repetitions} fois de plus. | `repetitions: 1` | `REPETITION(repetitions) [filtre={id: CRT_7}]` | — |
| CRT_48 | Bouclier stabilisé | Protocole | existante (inchangée, décision utilisateur) | Buff | Module Principal | 3 | 1 | | Les Boucliers de base sont lancés {repetitions} fois de plus. | `repetitions: 1` | `REPETITION(repetitions) [filtre={id: CRT_10}]` | — |
| CRT_98 | Laser de siège | Laser | nouvelle | Attaque | Ennemi Unique | 2 | | | Inflige {degats} dégâts à un ennemi | `degats: 20` | `DEGATS(degats)` | — |
| CRT_99 | Laser de contre-charge | Laser | nouvelle | Attaque | Ennemi Unique | 1 | | | Consomme tout le bouclier du module principal et inflige autant de dégâts à un ennemi | `par_point: 1` | `DEGATS [bonus={par: BOUCLIER_PRINCIPAL, facteur: par_point, consomme: true}]` | ◆ bonus calculé, ✱ source « bouclier du principal » et consommation (§3.4) |
| CRT_100 | Laser disrupteur | Laser | nouvelle | Attaque | Ennemi Unique | 1 | | | Retire {retrait} de bouclier à un ennemi, puis lui inflige {degats} dégâts | `retrait: 8, degats: 6` | **`RETRAIT_BOUCLIER`**`(retrait)` ; `DEGATS(degats)` | ✱ retrait de bouclier (§3.5) |
| CRT_101 | Bouclier intégral | Bouclier | nouvelle | Defense | Module Tous | 2 | | | Donne {bouclier} de bouclier à tous vos modules | `bouclier: 9` | `BOUCLIER(bouclier)` | — |
| CRT_102 | Bouclier miroir | Bouclier | nouvelle | Defense | Module Tous | 1 | | | Renvoi {renvoi} sur tous vos modules | `renvoi: 4` | `RENVOI(renvoi)` | ✱ Renvoi (§3.2) |
| CRT_103 | Réparation complète | Réparation | nouvelle | Reparation | Module Principal | 2 | 1 | | Répare le module principal pour {reparation} | `reparation: 25` | `REPARATION(reparation)` | — |
| CRT_104 | Réacteur en surrégime | Réacteur | nouvelle | Outils | Module Principal | 0 | 1 | | Donne {electricite} électricité en plus ce tour | `electricite: 2` | `GAIN_ELECTRICITE(electricite)` | — |
| CRT_105 | Réacteur à batterie | Réacteur | nouvelle | Buff | Module Principal | 2 | 1 | | Jusqu'à la fin du combat, l'électricité non dépensée est gardée pour le tour suivant | `{}` | **`STOCKAGE_ELECTRICITE`** | ✱ report de l'électricité (§3.6) |
| CRT_106 | Protocole de ciblage | Protocole | nouvelle | Debuff | Ennemi Tous | 1 | | | Pose Verrouillage {verrouillage} à tous les ennemis | `verrouillage: 3` | `VERROUILLAGE(verrouillage)` | ◆ Verrouillage |
| CRT_107 | Protocole de riposte | Protocole | nouvelle | Defense | Module Principal | 1 | | | Donne {bouclier} de bouclier et Renvoi {renvoi} au module principal | `bouclier: 5, renvoi: 5` | `BOUCLIER(bouclier)` ; `RENVOI(renvoi)` | ✱ Renvoi (§3.2) |

### 2.4 Légendaires (4)

| Id | Nom | Famille | État | Catégorie | Cible | Coût | Mun. | Lanc. | Description affichée | Valeurs | Effets | Mécanique à coder |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_50 | Protocole d'urgence | Protocole | existante (inchangée, décision utilisateur) | Buff | Module Tous | 3 | 3 | | Les cartes de base sont lancées {repetitions} fois de plus. | `repetitions: 1` | `REPETITION(repetitions) [filtre={rarete: Base}]` | — |
| CRT_108 | Protocole laser | Protocole | nouvelle (décision utilisateur) | Buff | Module Principal | 2 | 1 | | Jusqu'à la fin du combat, vos cartes Laser sont lancées {repetitions} fois de plus | `repetitions: 1` | `REPETITION(repetitions) [filtre={famille: Laser}]` | ✱ filtre famille (§3.1) |
| CRT_109 | Réacteur à fusion | Réacteur | nouvelle | Buff | Module Principal | 3 | 1 | | Donne {electricite} électricité en plus à chaque tour, jusqu'à la fin du combat | `electricite: 1` | **`AU_DEBUT_DU_TOUR`**` [declenche=GAIN_ELECTRICITE(electricite)]` | ✱ effet au début de chaque tour (§3.7) |
| CRT_110 | Laser orbital | Laser | nouvelle | Attaque | Ennemi Unique | 3 | | | Inflige {degats_cible} dégâts à un ennemi et {degats_autres} à tous les autres | `degats_cible: 25, degats_autres: 10` | `DEGATS(degats_cible)` ; `DEGATS(degats_autres) @AUTRES_ENNEMIS` | — |

### 2.5 Écartées ou déplacées

- **Bouclier éternel** (bouclier du principal qui ne baisse plus) : **pour le futur module de
  défense** (décision utilisateur, 2026-11-22), avec le Leurre (CRT_18).
- **Bouclier renforcé** (Blindage ciblé à 1⚡, 7 de bouclier) : refusé, Blindage ciblé reste tel
  quel.
- **Protocole de riposte, version « dégâts à l'attaquant »** : refusée (§1.3, question 9).

### 2.6 Contrôle hors norme (écart de plus de 30 % au repère)

| Carte | Rendement | Remarque |
|---|---|---|
| Blindage ciblé (actuelle) | 8 de bouclier pour 2⚡, 3 munitions : 4/⚡ | **−40 %**, gardée telle quelle (décision utilisateur) |
| Protocole d'urgence (actuelle) | 3 munitions sur un buff jusqu'à la fin du combat | se **cumule** si on la rejoue (contrairement aux légendaires du Lanceur, à 1 munition) : gardée telle quelle (décision utilisateur), à surveiller |
| Laser d'appoint | 2 dégâts + 1 pioche pour 0⚡ | proche d'une carte à 1⚡, mais se remplace elle-même |
| Réacteur d'appoint, Réacteur en surrégime | +1⚡ et +2⚡ pour 0⚡ | limités par 2 et 1 munitions |
| Laser de contre-charge | = bouclier du principal | **pas de plafond** (décision utilisateur) : avec Bouclier chargé (14) au tour précédent, 14 pour 1⚡ ; le bouclier est perdu |
| Réacteur à batterie | report sans maximum | **non évalué** : dépend du deck ; à surveiller avec Réacteur à fusion (4⚡ par tour + report) |
| Bouclier réfléchissant, Bouclier miroir, Protocole de riposte, Protocole de ciblage | dépendent des attaques reçues ou des coups portés | **non évalué** |

Les autres cartes sont dans le repère (6 à 7 par ⚡ en commune, 9 à 10 en rare).

---

## 3. Implémentation proposée des mécanismes ✱

Les mécaniques ◆ (portées vers un module, Surcharge, Verrouillage, répétition au tour, bonus
calculé) sont décrites dans [proposition-lanceur-missiles.md](proposition-lanceur-missiles.md)
§3 et ne sont pas répétées ici.

### 3.1 Champ `famille` et filtre par famille

- **Règle** (décision utilisateur, 2026-11-25) : le champ `famille` n'est rempli **que sur les
  cartes qu'un buff doit pouvoir viser**. Aujourd'hui, seule la famille **Laser** est visée
  (Protocole de tir, Protocole laser) : seules les cartes Laser ont le champ. Ailleurs, les
  familles (Bouclier, Réparation, Réacteur, Protocole ; Missile, Torpille, Ogive, Lanceur) restent
  une **règle de nommage**, sans champ ; on ajoutera le champ à une famille le jour où un buff la
  visera.
- **Laser de base** (CRT_7) : famille Laser (proposition), donc boosté aussi par Protocole laser ;
  Salve laser continue de viser le seul Laser de base par son id.
- **Format** : champ de carte `"famille": "Laser"` (texte, sans accent : `Reparation`,
  `Reacteur`), optionnel. `FiltreCartes` gagne le critère `famille`.
- **Code** :
  - `Carte.famille: str | None` ;
  - famille ajoutée aux clés autorisées et lue au chargement ;
  - `FiltreCartes.correspond` compare la famille.
  - Proposition : refuser au chargement une famille hors d'une liste connue (coquilles).
- **Affichage** : rien d'obligatoire. Proposition : la famille en petit sous le nom, et une
  colonne dans `config/cartes.md` et dans l'éditeur de cartes.
- **Tests** : filtre par famille ; famille inconnue refusée.

### 3.2 Renvoi pour les cartes

- **Règle** (décision utilisateur) : une carte peut poser le statut **Renvoi** sur un module. Les
  règles sont celles du Renvoi de Miroir (combat.md §3.5 et §3.8.5) : cumul par addition, stock
  qui diminue à chaque coup renvoyé, retiré à la fin de tour du module (donc **actif pendant le
  tour ennemi qui suit**).
- **Déjà codé** : une attaque ennemie sur un module renvoie les dégâts à l'ennemi attaquant
  (`_jouer_effet_ennemi` appelle `_attaquer(..., renvoi_vers=ennemi)`).
- **À coder** : nature de carte `RENVOI` avec `statut_pose = Statut.RENVOI`, camp joueur
  (`CAMP_PAR_NATURE`).
- **Exemple** : un ennemi attaque pour 7 un module en Renvoi 5 → 5 renvoyés, 2 subis (bouclier
  compris ensuite).
- **Tests** : pose sur un module ; renvoi vers l'attaquant ; retrait après le tour ennemi.

### 3.3 Électricité au tour suivant (`GAIN_ELECTRICITE_DIFFERE`)

- **Règle** (décision utilisateur) : +N⚡ au début du prochain tour du joueur, en plus des 3.
- **Code** : `Combat.electricite_differee += N` ; `_debut_tour_joueur` l'ajoute puis la remet à 0.
  Deux Condensateurs le même tour → +4 (proposition).
- **Affichage** : une pastille ou une ligne « +2⚡ au prochain tour » près de l'électricité
  (proposition) ; journal.
- **Tests** : tour 2 à 5⚡ ; cumul ; remise à zéro.

### 3.4 Bonus calculé par le bouclier du principal, avec consommation

- Extension du bonus calculé du Lanceur (proposition-lanceur-missiles.md §3.11) : nouvelle source
  `BOUCLIER_PRINCIPAL` et clé `consomme` (booléen).
- **Règle** (décision utilisateur) : dégâts = bouclier du principal × facteur, **sans plafond** ;
  avec `consomme`, le bouclier du principal tombe à 0.
- **Ordre** (proposition) : bouclier lu et retiré au moment du coup, **avant** l'application des
  dégâts ; si la carte est lancée 2 fois, le deuxième lancement fait donc 0 (plus de bouclier).
  La Surcharge et le Verrouillage s'ajoutent normalement (calcul d'un coup,
  proposition-lanceur-missiles.md §3).
- **Tests** : bouclier 14 → 14 dégâts et bouclier 0 ; bouclier 0 → 0 dégât (+ Surcharge) ;
  deuxième lancement à 0.

### 3.5 Retrait de bouclier (`RETRAIT_BOUCLIER`)

- **Règle** (décision utilisateur) : retire N de bouclier à la cible (jamais en dessous de 0),
  **pas le renvoi ni le leurre** ; puis les dégâts de la carte, dans l'ordre des effets.
- **Code** : nature `RETRAIT_BOUCLIER`, camp ennemi ; `cible.statuts.retirer(Statut.BOUCLIER, N)`
  (méthode existante).
- **Exemple** : Petit Jean à 12 de bouclier → 4 de bouclier, puis 6 dégâts dont 4 absorbés : il
  perd 2 PV. Sans bouclier : 6 PV perdus.
- **Tests** : retrait partiel, total, sur un ennemi sans bouclier ; renvoi intact.

### 3.6 Report de l'électricité (`STOCKAGE_ELECTRICITE`)

- **Règle** (décision utilisateur) : jusqu'à la fin du combat, l'électricité non dépensée en fin
  de tour est gardée pour le tour suivant, **sans maximum**.
- **Code** : drapeau `Combat.stockage_electricite` ; au début du tour, `electricite = 3 +
  reste` au lieu de `3` quand il est levé.
- **Point ouvert** (proposition) : le gain d'électricité différé (§3.3) et Réacteur à fusion
  (§3.7) s'ajoutent au report.
- **Tests** : fin de tour à 2⚡ → 5⚡ ; deux tours sans rien jouer → 3 + 3 + 3 = 9⚡ ; sans le
  drapeau, retour à 3.

### 3.7 Effet au début de chaque tour (`AU_DEBUT_DU_TOUR`)

- **Règle** (décision utilisateur) : Réacteur à fusion donne +1⚡ au début de chaque tour du
  joueur jusqu'à la fin du combat, à partir du tour suivant sa pose.
- **Format** : nature `AU_DEBUT_DU_TOUR` sans valeur, avec `declenche` (liste d'effets, même format
  que la Destruction et `SUR_CARTE_JOUEE` du Lanceur §3.12–§3.13).
- **Code** : `Combat.reactions_debut_tour` ; `_debut_tour_joueur` applique leurs effets après la
  remise de l'électricité. Même mécanisme que `SUR_CARTE_JOUEE` (réactions) : à coder ensemble.
- **Tests** : 4⚡ dès le tour suivant ; deux poses → 5⚡ (si la carte revient par Rechargement,
  proposition : cumul).

### 3.8 Ordre de réalisation proposé (une PR par lot)

Les lots du Lanceur (proposition-lanceur-missiles.md §3.14) et ceux-ci peuvent être fusionnés :
une mécanique ◆ est codée une seule fois.

| Lot | Contenu | Cartes du principal rendues jouables |
|---|---|---|
| P1 | Aucune mécanique : nouvelles cartes et valeurs modifiées | Laser lourd, Laser incendiaire, Laser d'appoint, Laser double, Bouclier d'escadre, Bouclier avant, Bouclier réactif, Bouclier chargé, Réparation rapide, Réparation de champ, Réacteur d'appoint, Protocole d'analyse, Laser de siège, Bouclier intégral, Réparation complète, Réacteur en surrégime, Laser orbital |
| P2 | Champ famille (§3.1) | (prépare Protocole de tir, Protocole laser) |
| P3 | Renvoi des cartes (§3.2), retrait de bouclier (§3.5) | Bouclier réfléchissant, Bouclier miroir, Protocole de riposte, Laser disrupteur |
| P4 | Électricité différée, report, début de tour (§3.3, §3.6, §3.7) | Réacteur à condensateur, Réacteur à batterie, Réacteur à fusion |
| avec le Lanceur | ◆ portées, Surcharge, Verrouillage, répétition au tour, bonus calculé (+ §3.4) | Laser défensif, Laser de visée, Réacteur en surtension, Protocole de ciblage, Protocole de tir, Laser de contre-charge, Protocole laser |

Chaque lot :

- régénère `config/cartes.md` et passe `pytest` ;
- est vérifié sur PC et web dès qu'il change l'affichage ;
- reporte les règles dans combat.md / modules-cartes.md.

---

## 4. Questions restantes

1. **Valeurs** : toutes inventées ; réglage à la main dans l'éditeur, puis simulation après les
   premiers lots (comme décidé pour le Lanceur).
2. **Protocole d'urgence** garde 3 munitions et se cumule : on le laisse ainsi (décision de ce
   jour), ou on s'aligne plus tard sur les légendaires du Lanceur (1 munition) ?
3. **Laser perçant** : description et cible corrigées (« la ligne ciblée », cible « Ennemi
   Ligne ») au lot 0 du plan, 2026-11-25.

---

## 5. Revue avec l'utilisateur (2026-11-25)

Discussion seulement : rien n'est codé.

- **Blindage ciblé** : gardée telle quelle (décision utilisateur). Le bouclier qui ne perd que 1
  par tour rend tous les boucliers plus durables que dans Slay the Spire, mais Blindage ciblé est
  le moins rentable par ⚡ (4/⚡) ; c'est plutôt **Bouclier chargé** (14 pour 2⚡, et avec Laser de
  contre-charge) qu'il faudra surveiller en simulation.
- **Réparations**, comparées à la carte de base *Réparation* (1⚡, 2 munitions, 8 au principal,
  soit 16 PV par combat) :

| Carte | Décision utilisateur | PV au principal par combat |
|---|---|---|
| Réparation rapide | 0⚡, 4 au principal, **2 munitions** (était 1) | 8, gratuits |
| Réparation de champ | **inchangée** : 1⚡, 2 munitions, 4 à tous les modules. Avec un secondaire, elle rend autant de PV que la base (4 + 4) ; plus avec 2 secondaires ou davantage | 8 (plus 4 par secondaire, pour le combat) |
| Réparation complète | 2⚡, **25** au principal (était 15), 1 munition | 25 |

  Rappel : seuls les PV du principal sont gardés d'un combat à l'autre, et la Station service
  vend aussi de la réparation ; trop de réparation dans les cartes lui ôterait son intérêt.
- **Textes des cartes qui donnent de l'électricité** (décision utilisateur) : verbe « Donne » et
  moment précisé : « Donne {electricite} électricité en plus **ce tour** » (Réacteur d'appoint,
  Réacteur en surrégime : effet immédiat confirmé), « … **au prochain tour** » (Réacteur à
  condensateur), « … **à chaque tour, jusqu'à la fin du combat** » (Réacteur à fusion). Même
  règle pour les cartes du Lanceur (Coup de grâce, Chasseur de primes).
- **Champ famille** (décision utilisateur) : seulement sur les cartes qu'un buff vise, donc pour
  l'instant les cartes Laser ; les autres familles ne sont qu'une règle de nommage (§3.1).
- **Laser de base** (CRT_7) : famille Laser, boosté par Protocole laser (décision utilisateur,
  2026-11-25). **Protocole d'urgence** garde 3 munitions (décision utilisateur, 2026-11-25 ;
  question 2 du §4 tranchée).
