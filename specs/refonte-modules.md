# Refonte des modules secondaires — brouillon de conception

*Document de travail, pas encore une section numérotée du document de conception (cf.
[specs.md](specs.md)) : rien ci-dessous n'est décidé ni implémenté, sauf mention « décision
utilisateur ». Une fois le modèle tranché, le contenu stabilisé ira dans [combat.md](combat.md)
(§3.4), [parcours.md](parcours.md) (§2.2) et [modules-cartes.md](modules-cartes.md) (§4, §5), et ce
fichier sera supprimé. Pointeur depuis [a-trancher.md](a-trancher.md) §11.*

---

## 1. Objectif (décision utilisateur)

- **Seuls les PV du module principal persistent** d'un combat à l'autre.
- Les **modules secondaires repartent à leur PV max à chaque début de combat** — un PV max qu'il
  faudra baisser par rapport aux 30 actuels.
- Les modules secondaires deviennent donc **sacrifiables** : ils peuvent mourir en combat et revenir
  au combat suivant.
- Ça ouvre une mécanique de jeu liée à leur mort : un **effet déclenché à la mort** (façon « Râle
  d'agonie » de Hearthstone) et/ou une **résurrection** en cours de combat.

---

## 2. Existant (à ne pas perdre de vue)

- **PV persistants pour tous les modules** (parcours.md §2.2) : `EtatModule.pv` est reporté après
  chaque combat gagné (`synchroniser_vaisseau_depuis_combat`), principal et secondaires confondus.
- **Un module à 0 PV est détruit, perte permanente** (combat.md §3.4) ; seule la destruction du
  module principal termine la run.
- **Station service** (parcours.md §2.2), 20 € par action : *Réparer* (+20 PV), *Améliorer* (+10 PV
  max et +10 PV), *Mettre à jour* (palier de rareté des récompenses), *Déplacer*.
- **PV actuels** (valeurs inventées, combat.md §13.5) : 50 pour le principal, 30 pour chaque
  secondaire.
- **Les cartes ne sont pas liées à leur module en combat** : `Carte` n'a aucun champ de module, le
  deck est une simple liste d'ids. Aujourd'hui, **la mort d'un module ne change rien à ses cartes**
  : elles restent dans la pioche et restent jouables.
- **Ciblage ennemi** (combat.md §13.1) : la plupart des ennemis visent par `PROXIMITE` (le module
  vivant le plus proche) ; *Le puzzle* et le Boss frappent `TOUS_MODULES_JOUEUR`. Les modules avant
  servent donc déjà, de fait, de boucliers au principal.
- Idée déjà notée en modules-cartes.md §4.2 : *Reconstruction* (3⚡, une fois par run, ressuscite un
  module détruit à 1 PV).

---

## 3. Conséquences directes de la règle

### 3.1 Sur le parcours

- **Réparer** ne sert plus qu'au module principal. On peut la garder telle quelle (seule cible
  utile), ou la rendre plus chère/plus forte puisque le principal devient la seule ressource de
  PV de la run.
- **Améliorer** (+PV max) reste utile pour les secondaires : un module plus solide meurt moins vite,
  dans chaque combat. Elle prend même plus de valeur qu'aujourd'hui.
- **PV du principal** : devient la seule « jauge de vie » de la run. À réévaluer à la hausse
  (proposition à discuter : 60 à 70) si les secondaires l'exposent davantage en mourant.
- **Persistance** : `EtatModule.pv` devient inutile pour les secondaires (seul `pv_max` compte).
  Les sauvegardes existantes restent lisibles, le champ est simplement ignoré.

### 3.2 Sur le combat

- **Le module qui meurt protège encore** : tant qu'il est vivant, il absorbe les coups `PROXIMITE`.
  Sa mort expose les modules suivants, puis le principal. Le PV max des secondaires règle donc
  directement **combien de tours le principal est à l'abri**.
- Avec la montée des dégâts ennemis proposée dans
  [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) §7.2, **les morts deviennent quasi certaines
  dans les combats longs** : les deux refontes se renforcent (la course contre la montée des dégâts
  se joue en sacrifiant des modules).

### 3.3 Question centrale : que deviennent les cartes d'un module mort ?

C'est ce qui décide si la mort a un **coût**. Trois options :

| Option | Effet | Avis |
|---|---|---|
| **A. Rien (comme aujourd'hui)** | Les cartes restent jouables | La mort ne coûte presque rien (juste un absorbeur de coups en moins) : « sacrifiable » devient « gratuit », et protéger un module n'a plus d'intérêt |
| **B. Cartes inutilisables jusqu'à la fin du combat** | Les cartes du module mort en main sont grisées ou défaussées ; celles piochées ensuite aussi | **Recommandé** : la mort a un vrai coût, le joueur arbitre entre protéger et sacrifier. Une résurrection rend les cartes à nouveau jouables, ce qui lui donne de la valeur |
| **C. Cartes transformées** | Les cartes du module mort deviennent une carte « Épave » (ex. 0⚡, +1 électricité ou pioche 1) | Intéressant mais plus lourd ; peut venir plus tard en variante de B |

**Implication technique de B et C** : il faut lier chaque carte du deck à **l'exemplaire de module**
qui l'a apportée (et pas seulement au type : deux exemplaires du même module sont possibles, §5).
Concrètement, le deck de la partie passerait d'une liste d'ids à une liste de couples (id de
carte, emplacement du module), ou chaque `Carte` de combat porterait une référence à son `Module`.
C'est le plus gros chantier moteur de cette refonte.

Cas particuliers à trancher avec B :
- Les cartes du **module principal** ne sont jamais concernées (sa mort termine la run).
- Une carte qui **cible** un module allié (ex. *Bouclier* sur module unique) peut-elle viser un
  module mort ? Non (comme aujourd'hui).

---

## 4. Effet à la mort (« Râle d'agonie »)

### 4.1 Forme

Un effet défini **par module** dans `config/modules.json` (ex. bloc `a_la_mort`, même format qu'un
`effet` de carte : type, cible, valeur), déclenché **une fois** quand le module tombe à 0 PV, avant
la suite de la résolution du tour ennemi. Réutilise le moteur d'effets des cartes : pas de nouveau
type d'effet nécessaire pour la plupart des idées ci-dessous.

### 4.2 Idées par module (toutes valeurs inventées)

| Module | Effet à la mort | Rôle tactique |
|---|---|---|
| Lanceur de missiles | Explose : 8 dégâts à tous les ennemis | Mourir au bon moment finit un combat |
| Blindage | Transfère un bouclier de 10 au module principal | Protège le principal juste quand il devient exposé |
| Générateur | +2 électricité immédiatement (ou au prochain tour joueur) | Accélère le tour suivant |
| Soute | Pioche 2 cartes | Compense la perte des cartes du module (option B) |
| Sabotage | Vulnérabilité sur l'ennemi qui l'a tué | Punit l'attaquant |
| Canon lourd *(cartes non conçues)* | Dernier tir : 15 dégâts à l'ennemi qui l'a tué | Idem, version brute |
| Contrôle *(cartes non conçues)* | L'ennemi qui l'a tué perd sa prochaine action | Gagne un tour |
| Atelier *(cartes non conçues)* | Répare le module principal de 8 PV | Seule source de soin « gratuite » du principal : à doser |
| Radar *(cartes non conçues)* | Tous les ennemis subissent +50 % de dégâts pendant 1 tour | Fenêtre d'attaque |

Ça donne une **identité** aux 4 modules sans cartes (Canon lourd, Contrôle, Atelier, Radar) avant
même que leurs cartes soient conçues.

### 4.3 Effets apportés par des cartes

En plus de l'effet propre au module, des cartes peuvent **ajouter** un effet à la mort à un module
(comme les « Râle d'agonie » conférés dans Hearthstone) :

- *Charge explosive* : « quand ce module meurt, inflige X dégâts à la colonne ennemie en face »
- *Capsule de sauvetage* : « quand ce module meurt, ajoute une carte X à votre main »

Et des cartes ou modules qui réagissent à **n'importe quelle** mort alliée :
- *Recyclage* : « gagne 1 électricité chaque fois qu'un module allié meurt ce combat »

---

## 5. Résurrection

### 5.1 Pistes

| Mécanique | Effet | Remarque |
|---|---|---|
| Carte *Reconstruction* (reprise de §4.2) | Ressuscite un module mort à X PV, munitions limitées | Avec l'option B (§3.3), lui rend aussi ses cartes : forte valeur |
| Module *Atelier* (passif) | Un module mort revient seul après 2 tours, à moitié de ses PV | Façon « Réincarnation » de Hearthstone ; une seule fois par module et par combat |
| Carte *Nanobots* | Pose un buff sur un module vivant : s'il meurt dans les 2 tours, il revient à 1 PV | Prépare la mort plutôt que la réparer ; s'inscrit dans le modèle de durée de la refonte des buffs |
| *Pièces détachées* | Chaque mort de module donne 1 « pièce » ; X pièces = un module ressuscité | Ressource de combat supplémentaire, plus lourd à afficher |

### 5.2 Combo mort + résurrection : garde-fou nécessaire

Un module qui meurt, ressuscite et remeurt **redéclenche son effet à la mort**. C'est une belle
synergie (Hearthstone la joue volontairement), mais elle peut boucler. Garde-fous possibles :

- un module ne ressuscite **qu'une fois par combat** ;
- ou l'effet à la mort ne se déclenche **qu'à la première mort** du combat.

---

## 6. Sacrifice volontaire

Pour que l'effet à la mort soit un choix et pas seulement une conséquence subie :

- Carte *Éjection* (0 ou 1⚡) : détruit un de vos modules secondaires, déclenche son effet à la
  mort, et donne un bonus (ex. +1 électricité, ou pioche 1).
- Variante : *Surcharge critique* — double l'effet à la mort du module sacrifié.

Rend la mort **active** (on choisit quand faire exploser le Lanceur de missiles) plutôt que
seulement subie.

---

## 7. Interactions avec l'existant

- **Fonds de tiroir** (+1 électricité par module actif) : pénalisée quand des modules meurent.
  Cohérent avec le thème, à garder en tête.
- **Récompense de combat** (§6 : une carte candidate par module équipé) : un module mort pendant le
  combat propose quand même sa candidate, puisqu'il revient au combat suivant.
- **Leurre**, **boucliers** : protéger un secondaire devient un choix (le garder en vie pour ses
  cartes) plutôt qu'une obligation (préserver des PV pour la suite de la run).
- **Montée des dégâts ennemis** (refonte buffs §7.2) : rend les morts certaines dans les combats
  longs, donc les effets à la mort systématiquement utiles.
- **Ciblage** : si `PROXIMITE` protège trop bien le principal, prévoir plus d'ennemis à
  `TOUS_MODULES_JOUEUR` ou un ciblage qui vise le principal en priorité.

---

## 8. Valeurs et points à trancher

1. **Cartes d'un module mort** : option A, B ou C (§3.3) — décision structurante, à prendre en
   premier (B recommandé).
2. **PV max des secondaires** : proposition 15 à 20 (inventé), à caler sur les dégâts ennemis et la
   durée moyenne d'un combat.
3. **PV du principal** : 50 actuels, peut-être 60 à 70 (inventé).
4. **Réparer** : inchangée (principal seul) ou revue.
5. **Effet à la mort** : un par module (§4.2) seulement, ou aussi apporté par des cartes (§4.3).
6. **Résurrection** : quelles pistes garder (§5.1) et quel garde-fou (§5.2).
7. **Sacrifice volontaire** (§6) : oui ou non.

---

## 9. Prochaines étapes

1. Trancher les points 1 à 3 de la §8 (règle de base).
2. Si option B : spécifier le lien carte ↔ exemplaire de module (deck de la partie, `Carte` de
   combat, sauvegarde, `web/bridge.py`).
3. Choisir les effets à la mort par module et leur format dans `config/modules.json`.
4. Concevoir les premières cartes de résurrection et de sacrifice.
5. Une fois stabilisé : migrer dans `combat.md` (§3.4), `parcours.md` (§2.2), `modules-cartes.md`
   (§4, §5), supprimer ce fichier.
