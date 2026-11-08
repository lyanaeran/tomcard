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
- Ça ouvre une mécanique de jeu liée à leur mort : un **effet déclenché à la destruction** (buff
  « Destruction » apporté par des cartes, §4, façon « Râle d'agonie » de Hearthstone) et/ou une
  **résurrection** en cours de combat.

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
- **Modules jouables** : champ `jouable` de `config/modules.json` ; pendant la refonte des cartes,
  seuls le module principal et le Lanceur de missiles le sont (modules-cartes.md §4).

---

## 3. Conséquences directes de la règle

### 3.1 Sur le parcours

- **Réparer** ne sert plus qu'au module principal. On peut la garder telle quelle (seule cible
  utile), ou la rendre plus chère/plus forte puisque le principal devient la seule ressource de
  PV de la run.
- **Améliorer** (+PV max) reste utile pour les secondaires : un module plus solide meurt moins vite,
  dans chaque combat. Elle prend même plus de valeur qu'aujourd'hui.
- **PV du principal** : devient la seule « jauge de vie » de la run, réévalué à la hausse
  (§9 : 60 provisoire, à affiner par simulation).
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

**Lien carte ↔ exemplaire de module (validé, 2026-11-08)** : aujourd'hui le deck sauvegardé
d'une partie est une simple liste d'ids de cartes, sans module : avec deux exemplaires du même
module (§5), impossible de savoir quelle carte appartient auquel. Conception retenue :

1. **Chaque exemplaire de module de la partie reçoit un identifiant d'exemplaire** stable
   (`EtatModule`, ex. `M1` pour le principal, `M2`, `M3`... ensuite), qui ne change jamais.
2. **Chaque carte du deck sauvegardé indique son exemplaire** : le deck passe d'une liste d'ids à
   une liste de couples, ex. `[{"id": "CRT_9", "module": "M2"}, {"id": "CRT_9", "module": "M3"}]`.
3. **En début de combat**, chaque carte est créée rattachée à son exemplaire (`CarteNew`) ; si cet
   exemplaire est détruit, ses cartes non persistantes partent en pile Hors service (§3.4).

Un identifiant d'exemplaire plutôt que l'emplacement (`avant_gauche`...) : la Station service
**déplace** des modules (échange possible entre deux emplacements) ; lié à l'emplacement, chaque
déplacement obligerait à mettre à jour les cartes, avec un risque d'erreur. Avec un identifiant,
les cartes suivent leur module sans rien faire (champ `exemplaire_module` de `CarteNew`). La carte
ne stocke pas le type de son module : il se lit sur l'exemplaire, et `config/modules.json` reste la
seule source de vérité des cartes de chaque type (une carte peut être commune à plusieurs modules).

Rattachement au moment où la carte entre dans le deck :

| Origine de la carte | Exemplaire de rattachement |
|---|---|
| Deck de départ | le principal |
| Carte choisie après le choix de module (Niveau 1) | le module qui vient d'être équipé |
| Récompense de combat | le module qui a proposé la carte (une candidate par module équipé, §6) |
| Aventure, Planète commerciale | **à trancher**, voir ci-dessous |

C'est le plus gros chantier moteur de cette refonte (format de sauvegarde dans
`src/gameplay/partie.py`, `web/bridge.py`, `web/app.js`), à faire au branchement de la refonte avec
la pile Hors service.

**Cartes obtenues hors module (Aventure, Planète commerciale) : à trancher.** Les rattacher toutes
au principal (proposition initiale) les rend insensibles à la mort des modules : si beaucoup de
cartes finissent rattachées au principal, perdre un module coûte de moins en moins, et le mot-clé
Persistante perd de son intérêt (remarque utilisateur). Pistes :
- **au module d'origine de la carte** (son type, ex. une carte du Lanceur de missiles va à un
  Lanceur équipé) ; à préciser si aucun exemplaire de ce type n'est équipé (carte refusée, ou
  repli sur le principal) et s'il y en a plusieurs (choix du joueur, ou le moins fourni) ;
- **au choix du joueur** parmi ses modules équipés, au moment de prendre la carte ;
- **au principal**, en limitant ces cartes (rares, ou réservées aux cartes du module principal) ;
- **au hasard** parmi les modules secondaires équipés.

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
   joueur (sacrifice volontaire §6, *Renvoi*, buffs Destruction en chaîne).
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
- **Données** : champ booléen `"persistante"` dans `config/carte_new.json` (`CarteNew.persistante`).
- **Candidates naturelles** : des cartes dont le thème survit au module, par exemple *Leurre*
  (un leurre déjà largué), ou des cartes de résurrection (§5), qui doivent pouvoir ressusciter leur
  propre module. Sans Persistante, une carte de résurrection d'un module mort serait elle-même hors
  service : à proscrire.
- **Vocabulaire (validé)** : « persistant » désignait déjà les **buffs sans durée**
  (`tours_restants = None`, modules-cartes.md §12.3, combat.md §13). Le mot-clé **Persistante est
  gardé pour les cartes**, et les buffs sans durée seront renommés **« permanents »** lors de la
  refonte des buffs (noté dans [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) §8).

---

## 4. Effet à la destruction : le buff « Destruction » (décision utilisateur, 2026-11-08)

### 4.1 Principe

Un module n'a **pas d'effet à la mort propre à son type**. Ce sont des **cartes** qui donnent à un
module le **buff « Destruction »**, qui porte un effet déclenché quand ce module est détruit
(façon « Râle d'agonie » conféré dans Hearthstone). Exemple de carte :

> « Applique à un module : **Destruction** — inflige 10 dégâts à tous les ennemis »

- La carte cible un **module allié** ; l'effet déclenché vise **autre chose** (ici tous les ennemis).
- Le buff reste sur le module jusqu'à sa destruction, puis se **déclenche et disparaît** (cumul
  « jusqu'à consommation », comme le Leurre).
- Plusieurs buffs Destruction sur un même module se déclenchent **tous**, dans l'ordre de pose.
- L'ancienne idée d'un effet à la mort par type de module (ex-§4.2) est **abandonnée** ; ses idées
  deviennent des idées de **cartes Destruction** (§4.3).

### 4.2 Format et points ouverts : voir [refonte-destruction.md](refonte-destruction.md)

Le format du buff dans `config/carte_new.json` et ses points à trancher (cible de l'effet
déclenché, moment du déclenchement, valeurs, modules concernés, effets autorisés, affichage) sont
dans un brouillon dédié, **en attente** : aucune carte ne pose encore ce buff (décision
utilisateur, 2026-11-08).

### 4.3 Idées de cartes Destruction (toutes valeurs inventées)

| Effet déclenché | Rôle tactique |
|---|---|
| 8 dégâts à tous les ennemis | Mourir au bon moment finit un combat |
| Bouclier de 10 sur le module principal | Protège le principal juste quand il devient exposé |
| +2 électricité au prochain tour | Accélère le tour suivant |
| Pioche 2 cartes | Compense la perte des cartes du module (§3.3) |
| Vulnérabilité sur l'ennemi qui a détruit le module | Punit l'attaquant |
| 15 dégâts à l'ennemi qui a détruit le module | Idem, version brute |
| L'ennemi qui a détruit le module perd sa prochaine action | Gagne un tour |
| Répare le module principal de 8 PV | Seule source de soin « gratuite » du principal : à doser |
| Tous les ennemis subissent +50 % de dégâts pendant 1 tour | Fenêtre d'attaque |

Ces cartes peuvent donner une identité aux modules sans cartes (Canon lourd, Contrôle, Atelier,
Radar). Autre idée, distincte du buff : une carte ou un module qui réagit à **n'importe quelle**
mort alliée (*Recyclage* : « gagne 1 électricité chaque fois qu'un module allié meurt ce
combat »).

---

## 5. Résurrection

### 5.1 Pistes

| Mécanique | Effet | Remarque |
|---|---|---|
| Carte *Reconstruction* (reprise de modules-cartes.md §4.2) | Ressuscite un module mort à X PV, munitions limitées | Avec l'option B (§3.3), lui rend aussi ses cartes : forte valeur |
| Module *Atelier* (passif) | Un module mort revient seul après 2 tours, à moitié de ses PV | Façon « Réincarnation » de Hearthstone ; une seule fois par module et par combat |
| Carte *Nanobots* | Pose un buff sur un module vivant : s'il meurt dans les 2 tours, il revient à 1 PV | Prépare la mort plutôt que la réparer ; s'inscrit dans le modèle de durée de la refonte des buffs |
| *Pièces détachées* | Chaque mort de module donne 1 « pièce » ; X pièces = un module ressuscité | Ressource de combat supplémentaire, plus lourd à afficher |

### 5.2 Combo mort + résurrection : garde-fou nécessaire

Le buff Destruction **disparaît quand il se déclenche** (§4.1) : un module ressuscité ne le
redéclenche pas à sa mort suivante, sauf si une nouvelle carte le lui rend. La boucle mort /
résurrection ne peut donc pas se répéter seule. Garde-fou restant à décider : limiter la
résurrection à **une fois par module et par combat**.

---

## 6. Sacrifice volontaire

Pour que la destruction d'un module soit un choix et pas seulement une conséquence subie :

- Carte *Éjection* (0 ou 1⚡) : détruit un de vos modules secondaires, ce qui déclenche ses buffs
  Destruction, et donne un bonus (ex. +1 électricité, ou pioche 1).
- Variante : *Surcharge critique* — double les effets Destruction du module sacrifié.

Rend la mort **active** (on choisit quand faire exploser un module chargé de Destruction) plutôt
que seulement subie.

---

## 7. Interactions avec l'existant

- **Fonds de tiroir** (+1 électricité par module actif) : pénalisée quand des modules meurent.
  Cohérent avec le thème, à garder en tête.
- **Récompense de combat** (§6 : une carte candidate par module équipé) : un module mort pendant le
  combat propose quand même sa candidate, puisqu'il revient au combat suivant.
- **Leurre**, **boucliers** : protéger un secondaire devient un choix (le garder en vie pour ses
  cartes) plutôt qu'une obligation (préserver des PV pour la suite de la run).
- **Montée des dégâts ennemis** (refonte buffs §7.2) : rend les morts certaines dans les combats
  longs, donc les cartes Destruction systématiquement utiles.
- **Ciblage** : si `PROXIMITE` protège trop bien le principal, prévoir plus d'ennemis à
  `TOUS_MODULES_JOUEUR` ou un ciblage qui vise le principal en priorité.

---

## 8. Modèle de données : `module_new.py` et `config/module_new.json` (décision utilisateur)

Même démarche que pour les cartes (`carte_new.py`, `config/carte_new.json`) :

- **`src/gameplay/module_new.py`** : classe `ModuleNew`, cible de la refonte, d'abord sans
  branchement au moteur.
- **`config/module_new.json`** : source de vérité des modules de la refonte, avec **les deux modules
  jouables** pour commencer (principal et Lanceur de missiles), champs `jouable` et `refonte`,
  et un tableau lisible `config/module_new.md` **généré** à côté, comme pour les cartes.

Un module mêle aujourd'hui **trois niveaux d'information**, répartis dans trois classes :

| Niveau | Aujourd'hui | Contenu | Durée de vie |
|---|---|---|---|
| **Modèle** (le type de module) | `SpecModule` | id (`MOD_2`), nom, image, description, PV max de base, cartes du module, `jouable`, `refonte` | lu dans le JSON, ne change jamais |
| **Exemplaire dans la partie** | `EtatModule` | identifiant d'exemplaire (`M3`, à ajouter), type, emplacement, PV max avec améliorations, niveau de mise à jour, PV (principal seulement) | sauvegardé d'une partie à l'autre |
| **État en combat** | `Module` | PV, bouclier, buffs (dont Destruction), leurre, mort, résurrections utilisées | remis à zéro à chaque combat |

**Découpage (décision utilisateur, 2026-11-08)** : **une seule classe `ModuleNew`** dans
`module_new.py`, qui réunit le modèle, l'exemplaire et les champs de combat (PV de combat,
bouclier, buffs dont Destruction, leurre, détruit) — même principe que `CarteNew`.

- **Une copie par combat** : au début de chaque combat, le combat travaille sur une **copie** du
  module, champs de combat remis à zéro (PV au maximum pour un secondaire, PV sauvegardés pour le
  principal). Le module de la partie n'est jamais modifié pendant le combat : un combat abandonné
  (« Quitter ») ou copié par le simulateur ne touche pas la partie, et un état de combat ne peut
  pas fuiter d'un combat à l'autre.
- **Fin de combat** : seuls les PV du principal sont reportés de la copie vers le module de la
  partie.
- **Sauvegarde** : seuls les champs du modèle et de l'exemplaire sont sauvegardés, jamais les
  champs de combat (liste explicite).
- **Deux sortes de PV** à nommer clairement : les PV sauvegardés (principal seulement) et les PV du
  combat en cours.
- Variante écartée : une classe à part pour le combat, liée à son `ModuleNew` (plus de classes et
  un lien à suivre, pour le même résultat).

**Implémenté (2026-11-08), pas encore branché au moteur** : `src/gameplay/module_new.py`
(`ModuleNew`, `charger_modules_new`), `config/module_new.json` (principal 60 PV, Lanceur de
missiles 20 PV, toutes leurs cartes de `config/carte_new.json`, un champ `principal`), tableau
généré `config/module_new.md`, tests `tests/test_module_new.py`. Méthodes : `nouvel_exemplaire`
(exemplaire neuf pour une partie), `copie_pour_combat`, `reporter_combat` (PV du principal
seulement), règles de combat de base (`subir_degats` avec bouclier puis leurre, `ajouter_bouclier`,
`reparer`, `debut_de_tour` : bouclier −1). Les buffs restent une simple liste, en attendant la
refonte des buffs. La sauvegarde de l'exemplaire (`EtatModule`) sera adaptée au branchement.

---

## 9. Valeurs et points à trancher

1. ~~**Cartes d'un module mort**~~ : **tranché et validé**, injouables tant que le module est
   mort, pile Hors service et ses 6 règles, lien carte ↔ exemplaire de module par identifiant
   d'exemplaire, mot-clé Persistante (0 ou 1 par module) — §3.3 à §3.5. **Rouvert** : le
   rattachement des cartes obtenues hors module (Aventure, Planète commerciale), §3.3.
2. ~~**PV max des secondaires**~~ : **20, provisoire** (validé, en attendant les simulations).
3. ~~**PV du principal**~~ : **60, provisoire** (validé, en attendant les simulations).
4. **Réparer** : inchangée (principal seul) ou revue.
5. ~~**Effet à la mort**~~ : **tranché**, buff « Destruction » apporté par des cartes (§4) ; format
   et détails en attente dans [refonte-destruction.md](refonte-destruction.md).
6. **Résurrection** : quelles pistes garder (§5.1) ; garde-fou contre les boucles en partie réglé
   par la consommation du buff Destruction (§5.2).
7. **Sacrifice volontaire** (§6) : oui ou non.
8. ~~**Découpage de `ModuleNew`**~~ : **tranché**, une seule classe `ModuleNew` (modèle,
   exemplaire et champs de combat), avec une copie par combat (§8).

---

## 10. Prochaines étapes

1. Créer `module_new.py` (`ModuleNew`, copie par combat, §8), `config/module_new.json`
   (principal 60 PV, Lanceur de missiles 20 PV) et son tableau généré.
2. Trancher le rattachement des cartes obtenues hors module (§3.3), puis implémenter le lien
   carte ↔ exemplaire de module (identifiant d'exemplaire, format du deck sauvegardé, `CarteNew`,
   `web/bridge.py`, `web/app.js`) et choisir les premières cartes Persistantes.
3. Concevoir les premières cartes Destruction (puis trancher
   [refonte-destruction.md](refonte-destruction.md)), de résurrection et de sacrifice.
4. Simuler pour caler les PV du principal et des secondaires.
5. Une fois stabilisé : migrer dans `combat.md` (§3.4), `parcours.md` (§2.2), `modules-cartes.md`
   (§4, §5), supprimer ce fichier.
