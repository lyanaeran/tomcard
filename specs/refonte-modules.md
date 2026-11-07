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

### 3.3 Les cartes d'un module mort deviennent injouables (décision utilisateur)

C'est ce qui donne un **coût** à la mort. Options examinées :

| Option | Effet | Statut |
|---|---|---|
| A. Rien (comme aujourd'hui) | Les cartes restent jouables | Écartée : la mort ne coûte presque rien, « sacrifiable » deviendrait « gratuit » et protéger un module n'aurait plus d'intérêt |
| **B. Cartes injouables tant que le module est mort** | Les cartes partent dans une pile dédiée (§3.4) | **Retenue (décision utilisateur)** : le joueur arbitre entre protéger et sacrifier ; une résurrection rend les cartes, ce qui lui donne de la valeur |
| C. Cartes transformées en « Épave » | Ex. 0⚡, +1 électricité ou pioche 1 | Écartée pour l'instant, variante possible plus tard |

Exception : les cartes portant le mot-clé **Persistante** restent jouables (§3.5). Les cartes du
**module principal** ne sont jamais concernées, puisque sa mort termine la run.

**Implication technique** : il faut lier chaque carte du deck à **l'exemplaire de module** qui l'a
apportée, et pas seulement au type : deux exemplaires du même module sont possibles (§5). Le deck de
la partie passerait d'une liste d'ids à une liste de couples (id de carte, emplacement du module),
ou chaque `Carte` de combat porterait une référence à son `Module`. C'est le plus gros chantier
moteur de cette refonte (deck, sauvegarde, `web/bridge.py`). Une carte obtenue autrement que par un
module (Aventure, Planète commerciale) est **rattachée au module principal** (validé), donc jamais
concernée.

### 3.4 Pile « Hors service » (décision utilisateur : une défausse particulière)

Une **quatrième pile** de combat, à côté de la pioche, de la défausse et des cartes épuisées
(§3.6), nommée **Hors service** (validé ; *Casse* et *Épave* écartées).

**Différence avec les cartes épuisées** : une carte épuisée (munitions à 0) est sortie du combat
**définitivement** ; une carte hors service n'est sortie **que tant que son module est mort**, et
revient s'il ressuscite.

Règles (validées) :

1. **À la mort du module**, **toutes** ses cartes non persistantes partent immédiatement en pile
   Hors service, **où qu'elles soient** : pioche, défausse et main. La main est défaussée à chaque
   fin de tour (comme dans Slay the Spire), donc un module qui meurt pendant le tour ennemi trouve
   une main vide ; le cas « en main » ne se présente que si le module meurt pendant le tour du
   joueur (sacrifice volontaire §6, *Renvoi*, effets à la mort en chaîne).
   - *Alternative écartée* : laisser les cartes dans la pioche et ne les envoyer en pile Hors
     service qu'au moment où elles sont piochées. Plus punitif (pioches perdues), mais crée des
     tours creux frustrants et une règle moins lisible.
   - *Conséquence assumée* : la pioche s'amincit, le joueur tourne plus vite sur les cartes des
     modules survivants. C'est un léger avantage qui atténue la perte.
2. **Pas de remélange** : la pile Hors service n'est jamais remélangée dans la pioche quand
   celle-ci est vide (comme les cartes épuisées).
3. **À la résurrection du module**, ses cartes reviennent **dans la défausse** : elles réapparaissent
   au prochain remélange, sans arriver d'un coup en main. Une carte de résurrection plus rare
   pourrait les renvoyer directement dans la pioche (mélangées), voire en main.
4. **Munitions** : une carte hors service garde son compteur de munitions ; elle le retrouve tel
   quel si elle revient.
5. **Fin du combat** : la pile est vidée, toutes les cartes reviennent au deck de la partie (le
   deck sauvegardé n'est jamais modifié par une mort de module, qui ne dure qu'un combat).
6. **Affichage** : un compteur à côté de la pioche, de la défausse et des épuisées (interface.md
   §8.1), consultable comme elles. Sur PC et web.

### 3.5 Mot-clé « Persistante » (proposition utilisateur)

Une carte **Persistante** reste jouable même si son module est mort : elle ne part pas en pile Hors
service et continue son cycle normal (pioche, main, défausse).

- **Rare par construction** : réservée à quelques cartes Rares ou Légendaires, sinon le coût de la
  mort (§3.3) disparaît : **0 ou 1 carte Persistante par module** (validé).
- **Affichage** : le mot-clé apparaît sur la carte (bandeau ou icône), comme les munitions.
- **Données** : un champ booléen dans `config/cartes.json` (ex. `"persistante": true`), et la
  colonne correspondante dans `specs/cartes.xlsx`.
- **Candidates naturelles** : des cartes dont le thème survit au module, par exemple *Leurre*
  (un leurre déjà largué), ou des cartes de résurrection (§5), qui doivent pouvoir ressusciter leur
  propre module. Sans Persistante, une carte de résurrection d'un module mort serait elle-même hors
  service : à proscrire.
- **Vocabulaire (validé)** : « persistant » désignait déjà les **buffs sans durée**
  (`tours_restants = None`, modules-cartes.md §12.3, combat.md §13). Le mot-clé **Persistante est
  gardé pour les cartes**, et les buffs sans durée seront renommés **« permanents »** lors de la
  refonte des buffs (noté dans [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) §8).

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

1. ~~**Cartes d'un module mort**~~ : **tranché et validé**, injouables tant que le module est
   mort, pile Hors service et ses 6 règles, cartes hors module rattachées au principal, mot-clé
   Persistante (0 ou 1 par module) — §3.3 à §3.5.
2. **PV max des secondaires** : proposition 15 à 20 (inventé), à caler sur les dégâts ennemis et la
   durée moyenne d'un combat.
3. **PV du principal** : 50 actuels, peut-être 60 à 70 (inventé).
4. **Réparer** : inchangée (principal seul) ou revue.
5. **Effet à la mort** : un par module (§4.2) seulement, ou aussi apporté par des cartes (§4.3).
6. **Résurrection** : quelles pistes garder (§5.1) et quel garde-fou (§5.2).
7. **Sacrifice volontaire** (§6) : oui ou non.

---

## 9. Prochaines étapes

1. Trancher les points 2 et 3 de la §8 (PV des secondaires et du principal).
2. Spécifier le lien carte ↔ exemplaire de module (deck de la partie, `Carte` de combat,
   sauvegarde, `web/bridge.py`) et choisir les premières cartes Persistantes.
3. Choisir les effets à la mort par module et leur format dans `config/modules.json`.
4. Concevoir les premières cartes de résurrection et de sacrifice.
5. Une fois stabilisé : migrer dans `combat.md` (§3.4), `parcours.md` (§2.2), `modules-cartes.md`
   (§4, §5), supprimer ce fichier.
