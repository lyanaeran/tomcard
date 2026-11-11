# Refonte du combat (`combat_new`) — spécification

*Document de travail. Rien n'est implémenté. Spécifie `src/gameplay/combat_new.py`, le combat de la
refonte, qui fait jouer ensemble `CarteNew`, `ModuleNew`, `EnnemiNew` et les statuts. **Gameplay
seulement** : l'affichage (PC et web), la sauvegarde de la partie et l'enchaînement des écrans
viendront au branchement (§9). Une fois stabilisé, le contenu ira dans [combat.md](combat.md) et
ce fichier sera supprimé.*

Documents liés : [refonte-statuts.md](refonte-statuts.md), [refonte-ennemis.md](refonte-ennemis.md),
[refonte-modules.md](refonte-modules.md), [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md),
[simulation.md](simulation.md).

Les points marqués **(proposition)** ne sont pas encore validés par l'utilisateur.

---

## 1. Périmètre

### 1.1 Inclus

- Les **mécaniques des cartes jouables** de `config/carte_new.json` : dégâts (avec portées
  « autres ennemis », colonnes), bouclier, réparation, leurre.
- Les **mécaniques déjà modélisées**, même si aucune carte jouable ne les utilise encore :
  incendie, répétition (Salve laser…), munitions, lancements multiples, gain d'électricité,
  pioche.
- Les **6 ennemis** de `config/ennemi_new.json` : cycle d'actions, valeurs qui montent avec le
  tour, coefficient de difficulté, bouclier, renvoi.
- La **pile Hors service** et le mot-clé **Persistante** (refonte-modules.md §3.3 à §3.5).
- L'**API** de `combat_new` (§8) : jouer une carte, finir le tour, et les consultations qui
  répondent à une question de règle (cibles valides, intentions, journal).

### 1.2 Exclu, pour plus tard (décision utilisateur)

- Vulnérabilité, Réduction de dégâts, Tir allié (`REDIRECTION_CIBLE`) : aucune carte jouable ne
  les utilise ; une carte qui en porte ne peut pas être jouée dans `combat_new` (erreur explicite).
- Buff Destruction ([refonte-destruction.md](refonte-destruction.md)), résurrection, sacrifice
  volontaire.
- Composition des flottes par niveau, nouveaux ennemis ([refonte-ennemis.md](refonte-ennemis.md) §5).

---

## 2. Entrées et sorties

### 2.1 Création d'un combat

`combat_new` reçoit des objets **déjà prêts**, sans rien lire lui-même dans les JSON :

| Entrée | Contenu |
|---|---|
| **Modules** | Les copies de combat des modules équipés (`ModuleNew.copie_pour_combat`), chacune à son emplacement : la base (principal) et jusqu'à 4 emplacements |
| **Deck** | Les cartes de la partie, chacune rattachée à son exemplaire de module (`CarteNew.copie(exemplaire_module=...)`) |
| **Flotte** | Les ennemis en combat (`EnnemiNew.pour_combat(coefficient)`), chacun à sa ou ses cases |
| **Aléatoire** | Un `random.Random` injecté (mélange du deck, cible des effets au hasard), jamais le module `random` global (`src/gameplay/CLAUDE.md`) |

### 2.2 Grille

Même grille qu'aujourd'hui (combat.md §3.1) : 2 colonnes (avant, arrière) × 3 rangées (gauche,
milieu, droite), côté joueur comme côté ennemi.

- **Joueur** : la base (principal) occupe la rangée du milieu ; les emplacements `avant_gauche`,
  `arriere_gauche`, `avant_droite`, `arriere_droite` de `ModuleNew.emplacement` correspondent aux
  cases du même nom.
- **Ennemis** : un ennemi occupe `emplacements` cases (Boss : une case avant et une case arrière de
  la même rangée), c'est un **seul** ennemi. Placement préféré (`PROTECTEUR_AVANT`,
  `PROTEGE_ARRIERE`) respecté quand la flotte est composée, comme aujourd'hui.

### 2.3 Deck de départ (décision utilisateur)

Laser ×4, Bouclier ×4, Protéger le vaisseau ×1, Réparation ×1, **tous rattachés au principal**.
Les cartes obtenues hors module (Aventure, Planète commerciale) sont **rattachées au principal pour
l'instant** ; la question reste ouverte (refonte-modules.md §3.3).

### 2.4 Sortie

À la fin : **victoire** ou **défaite** (§7), PV de combat des modules (le principal sera reporté
dans la partie par `ModuleNew.reporter_combat`), ennemis détruits (pour l'Argent gagné, inchangé).

---

## 3. Déroulement d'un tour

Le **numéro de tour** est tenu par le combat (décision utilisateur) : 1 au début, puis +1 au
début de chaque tour du joueur à partir du tour 2. Il sert à lire les valeurs des ennemis
(`EnnemiNew.valeur(nom, tour)`).

### 3.1 Début du combat

1. Le deck est mélangé pour former la pioche ; défausse, main, épuisées et Hors service vides.
2. Tour 1.

### 3.2 Tour du joueur

1. **Début** : à partir du tour 2, le numéro de tour augmente de 1 (les intentions consultées
   ensuite tiennent donc compte des nouvelles valeurs). Électricité remise à **3**, pioche de **5** cartes (main
   limitée à **10**), valeurs inchangées par rapport à aujourd'hui (décision utilisateur).
2. **Jeu** : le joueur joue les cartes qu'il veut, dans l'ordre qu'il veut (§4).
3. **Fin** :
   1. les cartes restant en main sont défaussées ;
   2. **fin du tour du joueur pour chaque ennemi vivant** (`EnnemiNew.fin_du_tour_du_joueur`) :
      l'incendie frappe (absorbé par le bouclier), puis bouclier et incendie −1, renvoi retiré ;
   3. si tous les ennemis sont détruits : **victoire**.

### 3.3 Tour ennemi

1. **Chaque ennemi vivant joue son étape courante**, l'un après l'autre (§5), avec les valeurs du
   tour en cours, puis avance dans son cycle (`avancer_cycle`).
2. Après chaque coup : un module à 0 PV est **détruit** (§6) ; si c'est le principal, **défaite**
   immédiate, le tour s'arrête.
3. **Fin du tour ennemi pour chaque module vivant** (`ModuleNew.fin_du_tour_ennemi`) : incendie,
   puis bouclier −1. Un module détruit par l'incendie l'est comme au point 2.
4. Retour au tour du joueur.

---

## 4. Jouer une carte

### 4.1 Conditions

Une carte peut être jouée si elle est **en main**, si l'électricité suffit (`cout`), et si elle a
une **cible valide** (§4.2). Une carte en pile Hors service ou épuisée n'est jamais en main.

`jouer_carte` refuse une carte qui ne remplit pas ces conditions, ou une cible invalide (erreur
explicite). La façon dont le joueur choisit sa carte et sa cible (clics, taps, specs.md §8.3)
relève de l'affichage et n'est pas spécifiée ici.

### 4.2 Cible de la carte (`CibleCarteNew`)

| Cible | Case cliquée | Ce qui est touché |
|---|---|---|
| Ennemi Unique | un ennemi vivant | cet ennemi |
| Ennemi Colonne | un ennemi vivant | les ennemis vivants de sa colonne |
| Ennemi Avant / Arrière | un ennemi vivant de cette colonne | les ennemis vivants de la colonne avant / arrière |
| Ennemi Tous | un ennemi vivant | tous les ennemis vivants |
| Module Unique | un module vivant | ce module |
| Module Principal | le principal | le principal |
| Module Avant | un module vivant de la colonne avant | les modules vivants de la colonne avant |
| Module Tous | un module vivant | tous les modules vivants |

Un ennemi sur 2 cases n'est touché **qu'une fois** par effet, même si les deux cases sont visées.

### 4.3 Résolution

1. L'électricité est payée **une fois**.
2. La carte est **lancée `lancements_actuels` fois** ; à chaque lancement, ses effets sont
   appliqués **dans l'ordre**, avec ses valeurs actuelles (`valeurs_actuelles`).
3. Chaque effet touche, selon sa **portée** (`PorteeEffet`) : la cible de la carte (`CIBLE`), les
   autres ennemis vivants (`AUTRES_ENNEMIS`), la colonne avant ou arrière ennemie.
4. **Munitions** : une munition est consommée **par carte jouée**, pas par lancement
   **(proposition)**. À 0, la carte part dans les **épuisées** (combat.md §3.6) ; sinon dans la
   défausse.
5. Après la carte : un module détruit (par un renvoi) l'est selon §6 ; ennemis tous détruits →
   **victoire** immédiate.

### 4.4 Effets

| Nature | Effet sur chaque entité touchée |
|---|---|
| Dégâts | Une attaque de la valeur (`subir_degats`) : leurre, puis renvoi, puis bouclier, puis PV (refonte-statuts.md §4.1) ; les dégâts renvoyés partent vers un module (§4.5) |
| Bouclier, Incendie, Leurre | Pose du statut (`NatureEffet.statut_pose`), selon sa règle de cumul |
| Réparation | Rend des PV de combat, sans dépasser le PV max (`reparer`) ; jamais sur un module détruit |
| Gain d'électricité | Électricité en plus pour ce tour |
| Pioche | Pioche de cartes en plus (main limitée à 10) |
| Répétition | `appliquer_repetition` sur **toutes** les cartes du combat (pioche, main, défausse, Hors service), jusqu'à la fin du combat |

Chaque lancement et chaque cible sont des **attaques distinctes** : un Laser lancé 2 fois sur un
ennemi protégé par un renvoi de 5 renvoie d'abord 5, puis plus rien.

### 4.5 Dégâts renvoyés (décision utilisateur)

Quand le joueur frappe un ennemi qui porte un **renvoi**, les dégâts renvoyés vont au **module
auquel la carte jouée est rattachée** (`exemplaire_module`). Le joueur sait donc d'avance quel
module il expose.

- Le renvoi diminue d'autant à chaque coup renvoyé (décision utilisateur) : avec un renvoi de 5, un
  coup de 5 est entièrement renvoyé et le renvoi tombe à 0.
- **(proposition)** Les dégâts renvoyés sont une **attaque** sur ce module : son leurre l'annule,
  son bouclier l'absorbe.
- **(proposition)** Si ce module est déjà détruit (carte Persistante), les dégâts renvoyés vont au
  **principal**.

---

## 5. Tour ennemi en détail

### 5.1 Ordre de jeu des ennemis (décision utilisateur)

Dans l'**ordre de la flotte, de l'avant vers l'arrière** : colonne avant d'abord, puis colonne
arrière ; dans une colonne, rangées gauche, milieu, droite **(proposition pour l'ordre des
rangées)**. Un ennemi sur 2 cases joue **une seule fois**, à sa case avant. Un ennemi **détruit ne
joue plus** et son cycle s'arrête.

### 5.2 Effets d'une étape

| Nature | Cible | Résolution |
|---|---|---|
| Attaque | `PROXIMITE` | Le module vivant le plus proche (règle actuelle, `ciblage.py:module_cible_par_ennemi` : rangée de l'ennemi d'abord, avant puis arrière, puis rangées voisines) |
| Attaque | `TOUS_MODULES` | Chaque module vivant, une attaque chacun |
| Bouclier, Renvoi | `SOI_MEME` | L'ennemi lui-même |
| Bouclier, Renvoi | `ALLIE_AVANT_SINON_ARRIERE` | Un ennemi vivant tiré au hasard dans la colonne avant (lui-même compris), sinon dans la colonne arrière ; tirage au moment de jouer, avec l'aléatoire injecté |

- **Répétitions** (Le nettoyeur ×2) : l'effet est joué autant de fois, **cible recalculée à chaque
  fois** **(proposition)** : si la première attaque détruit le module visé, la seconde frappe le
  module suivant le plus proche.
- Une attaque sur un module passe par ses statuts (`subir_degats` : leurre, bouclier, PV).

### 5.3 Intention

Pour chaque ennemi vivant, `combat_new` donne son **intention** : l'étape courante
(`etape_courante`) avec les valeurs du tour en cours (`valeurs_au_tour`), et, pour une attaque
`PROXIMITE`, le module qui serait visé si rien ne change. La cible d'un tirage au hasard
(`ALLIE_AVANT_SINON_ARRIERE`) n'est pas annoncée.

---

## 6. Destruction d'un module

Un module à 0 PV est **détruit** pour le reste du combat :

1. **Toutes ses cartes non Persistantes** partent immédiatement en **pile Hors service**, où
   qu'elles soient (pioche, main, défausse), avec leurs munitions (refonte-modules.md §3.4).
2. La pile Hors service n'est **jamais remélangée** dans la pioche.
3. Ses statuts sont perdus ; il n'est plus une cible, ni pour les ennemis, ni pour les cartes.
4. **Principal détruit** : **défaite** immédiate.
5. Un secondaire détruit **repart à ses PV max au combat suivant** (`ModuleNew.copie_pour_combat`) :
   ce n'est pas une perte permanente.

---

## 7. Fin du combat (décision utilisateur)

- **Victoire** : tous les ennemis sont détruits (par une carte, ou par l'incendie à la fin du tour
  du joueur).
- **Défaite** : le principal est détruit. La destruction d'un ou de tous les secondaires n'est
  **pas** une défaite.
- À la fin : la pile Hors service et les épuisées sont vidées, les PV du principal sont reportés
  dans la partie ; le deck de la partie n'est jamais modifié par le combat.
- **Pioche vide** : la défausse est remélangée pour reformer la pioche, comme aujourd'hui ; si les
  deux sont vides (cartes épuisées ou hors service), le joueur pioche moins de cartes, sans
  remélange de secours (combat.md §3.6 ; cas limite déjà noté dans a-trancher.md §9.1, plus
  probable avec la pile Hors service).

---

## 8. API de `combat_new`

`combat_new` ne contient **aucun affichage** : il expose une API, utilisée par le simulateur
aujourd'hui, par l'affichage PC et web au branchement.

### 8.1 Actions

- `jouer_carte(carte, cible)` : joue une carte de la main sur une cible (§4) ; refuse une action
  invalide.
- `finir_tour()` : termine le tour du joueur, joue le tour ennemi (§3.2, §3.3) et commence le tour
  suivant, sauf fin de combat.

### 8.2 Consultations

Lectures seules, qui ne modifient rien. Elles sont dans `combat_new` et non dans l'affichage parce
que **chacune répond à une question de règle** : `src/ui` et `web/` ne doivent jamais recalculer
une règle (CLAUDE.md), et le simulateur en a besoin aussi.

- **État** : tour, électricité, piles (pioche, main, défausse, épuisées, Hors service), PV et
  statuts des modules et des ennemis, combat en cours / gagné / perdu.
- `cibles_possibles(carte)` : les cibles valides d'une carte (règles du §4.2), pour ne proposer
  que des coups légaux.
- **Intentions** des ennemis (§5.3) : ce que chaque ennemi va jouer, d'après son cycle, la valeur
  du tour et le ciblage par proximité.
- **Journal** des événements (carte jouée, dégâts, renvoi, statut posé, incendie, destruction,
  carte hors service, victoire/défaite) : ce qui s'est passé, dans l'ordre, comme
  `Combat.journal` aujourd'hui. Seulement des faits, sans mise en forme ni texte affiché.

---

## 9. Plan de réalisation

1. **`src/gameplay/combat_new.py`** (et, si besoin, des petits fichiers pour la grille de modules
   et la flotte de la refonte), ajoutés à `FICHIERS_A_MONTER` de `web/app.js`.
2. **`tests/test_combat_new.py`** : tour complet, chaque nature d'effet, portées, lancements,
   munitions, renvoi vers le module de la carte, ordre des ennemis, répétitions, intentions,
   destruction et pile Hors service, Persistante, victoire, défaite.
3. **Simulateur** (`outils/simulation/`) : jouer `combat_new` avec le bot, puis simuler pour caler
   les valeurs provisoires (PV 60/20, boucliers de Petit Jean et du Boss, renvoi de Miroir,
   augmentations des ennemis).
4. **Branchement** (hors de ce document) : sauvegarde de la partie (deck avec exemplaires, modules),
   `deroulement.py`, affichage PC et web, suppression de l'ancien moteur (`combat.py`,
   `cartes.json`, `modules.json`, `ennemis.json`).

---

## 10. Points à trancher

1. **Munitions** : une munition par carte jouée, et non par lancement (§4.3) ?
2. **Dégâts renvoyés** : traités comme une attaque (leurre et bouclier du module), et redirigés vers
   le principal si le module de la carte est détruit (§4.5) ?
3. **Ordre des rangées** pour l'ordre de jeu des ennemis : gauche, milieu, droite (§5.1) ?
4. **Répétitions d'une attaque ennemie** : cible recalculée à chaque coup (§5.2) ?
5. **Rattachement des cartes hors module** : au principal pour l'instant, à trancher plus tard
   (refonte-modules.md §3.3).
