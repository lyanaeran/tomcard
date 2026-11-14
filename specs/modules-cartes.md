# Space Fight — Modules et cartes (§4 à §7 et §12)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

---

## 4. Modules

Le vaisseau démarre avec un **module de base**, et en récupère d'autres au fil de l'avancée. Chaque module a son propre deck de cartes (certaines cartes communes entre modules).

**10 modules dans `config/modules.json`** (nom, image, PV, description) : les 6 déjà dotés d'un
deck de cartes jouable (Principal, Lanceur de missiles, Blindage, Générateur, Soute, Sabotage) et
4 nouveaux ajoutés avec leur nom/image/description mais **sans deck de cartes pour l'instant**
(Canon lourd, Contrôle, Atelier — proche de l'archétype "Réparation" ci-dessous, Radar — proche de
l'archétype "Radar / Ciblage" en §4.3) : exclus du tirage de choix de module tant qu'ils n'ont pas
de cartes (`modules_equipables`/`specs_equipables`, §5), pour ne jamais planter le tirage du deck.

**Refonte des cartes en cours (décision utilisateur, 2026-11-07)** : les cartes du module
principal et du Lanceur de missiles ont été revues (19 cartes, `config/carte_new.json`, nouvelle
source de vérité des cartes ; valeurs reportées dans `config/cartes.json`, encore lu par le moteur
actuel ; l'ancien registre `specs/cartes.xlsx` est archivé en `specs/cartes_legacy.xlsx`). Pendant la refonte, **seuls ces deux modules sont jouables** :
champ `jouable` de `config/modules.json` (`SpecModule.jouable`), les autres ne sont jamais
proposés ni équipés (`parcours.modules_equipables` ; depuis la PR 1 du branchement, le champ lu
est celui de `config/module_new.json`). Le choix de module du Niveau 1 ne
propose donc que le Lanceur de missiles. Changements principaux :
- **Deck de départ** (10 cartes) : Laser x4, Bouclier x4, Protéger le vaisseau x1, Réparation x1.
  *Réparation* revient dans le pool du module principal ; *Laser perçant* devient Commune (plus dans
  le deck de départ, proposée en récompense).
- Valeurs : *Bouclier* 5 → 3, *Protéger le vaisseau* 8 → 5, *Blindage ciblé* bouclier de 7 pendant 4 tours → **bouclier simple de 6** (sans durée),
  *Protocole d'urgence* X 2 → 1, *Bombardement* 4 → 6, *Torpille* Y 6 → 8.
- **Boucliers remontés (décision utilisateur, 2026-11-11, après simulation)** : *Bouclier* 3 → **4**,
  *Protéger le vaisseau* 5 → **6**, *Blindage ciblé* 6 → **8**. Les trois montent ensemble pour
  garder leur hiérarchie. Un premier réglage à 5 / 7 / 8 a été simulé puis jugé trop haut
  (`outils/simulation/synthese/essai_bouclier_2026-11-11.md`). Le faible taux de jeu de Bouclier
  vient surtout du manque d'électricité (4 exemplaires, 3 électricité, le Laser passe en premier),
  pas de sa faiblesse.
- **Incendie** (nouvelle mécanique, non jouable pour l'instant) : *Tir incendiaire* (4),
  *Embrasement* (8, un ennemi) et *Guerre nucléaire* (8, tous les ennemis) ajoutent des points
  d'incendie, équivalent du poison de Slay the Spire (décroissance de 1 par tour).
- *Bouclier stabilisé* change d'effet : « les Boucliers de base sont lancés X fois de plus »
  (même famille que *Salve laser* et *Protocole d'urgence*).
- **Format de `config/carte_new.json`** (validé) : chaque carte a des **valeurs nommées**
  (`"valeurs": {"degats_cible": 15, "degats_autres": 6}`), une liste d'**effets** qui y renvoient par
  leur nom (`{"nature": "DEGATS", "valeur": "degats_cible"}`, avec une portée, une durée nommée ou
  un filtre si besoin), une **description** qui cite les valeurs entre accolades (« Inflige
  {degats_cible} degats… », remplie par `CarteNew.description_affichee`), et deux booléens
  `jouable` (le moteur sait l'exécuter) et `refonte` (carte revue). Au chargement, tout nom cité
  doit exister et toute valeur doit servir à un effet, et **toute clé inconnue du JSON est
  refusée** (coquilles détectées). Un **filtre de cartes** (Salve laser…) désigne une carte précise
  par son **id** (`{"id": "CRT_7"}`), jamais par son nom affiché, ou un ensemble par rareté ou
  catégorie. Chaque exemplaire a ses propres dictionnaires `valeurs` et `valeurs_actuelles`
  (copie), pour pouvoir un jour modifier les valeurs d'une seule carte. En combat, chaque
  exemplaire a ses `valeurs_actuelles` (copie des valeurs), base de futurs bonus du type « +2 aux
  dégâts des cartes à cible unique ».
- Classe de carte cible de la refonte : `src/gameplay/carte_new.py` (`CarteNew`), **relue et
  validée par l'utilisateur le 2026-11-08**, pas encore branchée au moteur. Une carte y porte une liste d'effets, un nombre de **lancements** de départ (`lancements_base`, 1 par
  défaut, 2 pour une carte lancée deux fois ; décision utilisateur), et les effets « les cartes X
  sont lancées N fois de plus » (*Salve laser*, *Protocole d'urgence*, *Bouclier stabilisé*, X = 1
  pour ce dernier) **augmentent directement les lancements** des cartes qu'ils désignent, dans
  toutes les piles, **jusqu'à la fin du combat**, et se cumulent (décision utilisateur ; chaque
  combat recrée ses cartes, l'augmentation disparaît donc d'elle-même).
- `CarteNew` ne décrit que les **effets des cartes du joueur** : les mécaniques propres aux ennemis
  (ex. Augmentation de dégâts du Boss) sont gérées **en dehors des cartes** (décision utilisateur).
- Textes affichés accentués : *Protéger le vaisseau*, *Réparation* (consigne utilisateur).
Chaque module a une seule `description` (une phrase, accroche narrative spécifiée par
l'utilisateur), affichée à l'écran de choix de module et reprise telle quelle dans l'infobulle de
l'écran Vaisseau au clic/tap sur un module (§2.4) — les decks de cartes détaillés ci-dessous
restent le plan cible pour les 4 nouveaux modules, à concevoir dans une passe dédiée.

### 4.1 Modules d'attaque (spécialisés, pas un seul module générique)

**Canon lourd** — mono-cible, gros dégâts. Fort contre les L, faible contre les essaims de S.
- Tir de précision (1⚡, 8 dégâts)
- Charge concentrée (2⚡, 14 dégâts)
- Tir perforant (2⚡, 10 dégâts, avant + arrière de la colonne)
- Surcharge (3⚡, 20 dégâts, ne peut pas retirer au tour suivant)

**Batterie Gatling** — multi-cible / dégâts répartis. Fort contre les groupes de S, faible contre un seul L.
- Rafale (1⚡, 3 dégâts à 2 cibles aléatoires)
- Tir de suppression (2⚡, 4 dégâts à tout le rang avant)
- Barrage (2⚡, 3 dégâts à toutes les cibles)
- Surchauffe (0⚡, 5 dégâts, génère de la Chaleur/malus cumulatif)

**Missiles** — ciblage à distance, ignore le placement. Très fort contre les soigneurs/supports planqués à l'arrière ; disruptif pour le système de rangs, à réserver en rare/tardif.
- Verrouillage (1⚡, 6 dégâts, cible n'importe quel rang)
- Salve guidée (2⚡, 4 dégâts x2, cibles différentes, ignore le rang)
- Frappe orbitale (3⚡, 12 dégâts sur tout le rang arrière ennemi)

**Laser** — dégâts constants / perçants en ligne. Bon contre les ennemis à haut PV qui durent.
- Faisceau (1⚡, 4 dégâts, traverse toute la colonne)
- Incision (1⚡, applique Brûlure 3 dégâts/tour x3)
- Rayon continu (2⚡, 6 dégâts + Brûlure 2 dégâts/tour x2)

### 4.2 Modules de soutien / défense

**Blindage** — absorbe les dégâts, protège les autres modules.
- Plaque renforcée (1⚡, 6 Bouclier sur ce module)
- Mur défensif (1⚡, 4 Bouclier sur ce module + 4 sur un allié adjacent)
- Protection croisée (2⚡, 8 Bouclier réparti sur jusqu'à 2 modules)
- Position de tank (1⚡, ce module devient la seule cible possible ce tour) — *carte signature*
- Renfort d'urgence (2⚡, Bouclier = PV manquants d'un allié, plafonné)
- Bouclier réactif (2⚡, 6 Bouclier + renvoie des dégâts si attaqué)
- Fortification totale (3⚡, Bouclier à tout le vaisseau, ce module ne peut ni attaquer ni bouger)
- Bastion (2⚡, carte power : génère 3 Bouclier auto chaque tour)
- *Malus optionnel* : Blindage lourd (0⚡, 5 Bouclier, -1 PV max permanent)

**Contrôle** — désactive/stun temporairement les ennemis. Aucun dégât, mais désamorce les menaces prioritaires (essentiel contre les L).
- Impulsion électromagnétique (1⚡, stun 1 tour)
- Brouillage (1⚡, -50% dégâts d'une cible pendant 2 tours)
- Champ de gel (2⚡, stun tout le rang arrière ennemi)
- Piratage (2⚡, force une cible à attaquer un allié à elle)
- Verrou total (3⚡, stun un L pendant 2 tours)

**Réparation** — répare les modules abîmés. Seul contre-poids à la destruction permanente.
- Soudure rapide (1⚡, répare 6 PV)
- Nanites réparatrices (1⚡, répare 3 PV/tour x3, persiste)
- Atelier d'urgence (2⚡, répare 10 PV réparti sur 2 modules)
- Restauration critique (2⚡, répare un module à 1 PV jusqu'à 15 PV)
- Reconstruction (3⚡, une fois par run, ressuscite un module détruit à 1 PV) — *rare*

### 4.3 Autres archétypes proposés

- **Bouclier énergétique** : convertit l'électricité non dépensée en Bouclier
- **Radar / Ciblage** : marque une cible (+dégâts subis), révèle les intentions ennemies
- **Propulseur** : esquive, échange de position entre modules en cours de combat
- **IA de combat / Drone** : invoque une unité automatique, rend une carte gratuite
- **Générateur** : produit de l'électricité bonus (module "économique" pur)
- **Sabotage** : dégâts dans le temps (Brûlure), réduction d'armure ennemie
- **Soute / Fret** : non-combattant, bonus passif (pioche, or) en échange d'un slot de combat

---

## 5. Slots de modules équipables

- Début de run : module de base + 1 module (2 slots) — le 2ᵉ module est choisi au Niveau 1 (§2.3)
- +1 slot débloqué à chaque victoire de boss (rythme lié à la fréquence des boss, voir §2/§2.3)
- **Plafond proposé : 5 slots** (module de base inclus) — valeur provisoire, encore susceptible de changer
- Le module de base occupe toujours un slot et reste équipé
- **Doublons de modules autorisés** (décision utilisateur, remplace l'ancienne proposition
  "interdire les doublons") : posséder déjà des exemplaires d'un module augmente son poids au
  tirage lors d'un prochain choix de module — détail en §2.3
- Un module dont le deck de cartes n'est pas encore conçu (`cartes` vide dans `config/modules.json`,
  §4) ou marqué `"jouable": false` (refonte des cartes en cours, §4) n'est **jamais proposé** au
  tirage (`parcours.modules_equipables` l'exclut) : le proposer planterait le
  tirage du deck (`Deck`/`tirer_cartes` sur une pool vide)

---

## 6. Progression des modules / cartes

- Après un combat gagné, le joueur gagne une carte, garantie (voir §2.1). Mécanisme : **1 carte
  candidate par module équipé** (base incluse, au maximum 5 — §5), tirée dans le pool de cartes
  propre à ce module — le joueur choisit parmi ces N candidates, ce qui attribue implicitement la
  carte au module correspondant
  - Le **module principal** pioche sa candidate dans son **propre pool** de cartes jouables non-Base
    (`config/modules.json:MOD_1.cartes`), exactement comme un module secondaire — **jamais** dans le
    pool entier du jeu. Corrige un bug (décision utilisateur) où le module principal piochait
    auparavant dans `pool_toutes_cartes` (toutes les cartes du jeu, tous modules confondus), ce qui
    pouvait lui proposer en récompense une carte d'un autre module (`parcours.
    tirer_candidats_recompense`, régression couverte par un test dédié)
  - Pour un **module secondaire**, sa candidate est tirée dans la **liste de cartes propre à ce module**
  - La rareté (voir 7.3) pondère chaque tirage individuel : **5% Légendaire, 20% Rare, sinon (75%)
    Commune** — décision utilisateur. **Les cartes Base ne sont jamais proposées en récompense**
    (deck de départ uniquement). Si le pool d'un module n'a aucune carte au palier tiré, on
    redescend au palier inférieur (Légendaire → Rare → Commune) plutôt que de ne rien proposer
  - Remplace l'ancien mécanisme "1 carte parmi 3 propositions pondérées par rareté, avec choix du module destinataire" : le choix du module destinataire se fait maintenant implicitement en choisissant la candidate
  - **Bouton Passer** (décision utilisateur) : le joueur n'est jamais obligé de choisir une
    carte, y compris ici — visible dès qu'il y a au moins un candidat (rien à passer sinon, un clic
    suffit déjà à continuer). Convention étendue à tous les écrans de choix de carte tranchés à ce
    jour : ce même écran de fin de combat et le Choix d'une carte de module (§2.4 étape 4) l'ont
    tous les deux ; la carte offerte d'Astéroïdes (§2.5) avait déjà "Prendre"/"Passer" avant cette
    décision. **Hors périmètre pour l'instant** (décision utilisateur, faute de temps) : "Bricoler"
    de l'Aventure Trois lunes et les choix Confiscation/Mettre aux normes de l'Aventure Police
    (§2.5), qui ne sont pas des écrans de choix de carte à proprement parler (un choix parmi
    plusieurs actions, pas une carte candidate à accepter ou refuser)
  - **Implémenté** en écran de fin de combat autonome (Victoire/Défaite), **relié à l'orchestration
    du parcours** (§2.4) pour une vraie partie : `src/gameplay/parcours.py`
    (`tirer_candidats_recompense` et les fonctions de tirage par palier), `src/ui/ecran_fin_combat.py`
    (PC), `main.py:_ouvrir_fin_combat` ; côté web `src/web/bridge.py:conclure_combat_partie_web`/
    `resoudre_victoire_partie_web` + `src/web/app.js:terminerCombatPartie`/`choisirRecompense`. Reste
    aussi accessible en démonstration isolée (candidats tirés depuis un vaisseau tiré au sort plutôt
    qu'une vraie partie) via `src/web/app.js` (`nouvelleVictoire`/`nouvelleDefaite`, exposées sur
    `window`) + `src/web/bridge.py` (`fin_combat_victoire`), utilisée quand `partieActive` est `null`.
    Défaite : titre rouge "DEFAITE" + message
    "Pas d'inquietude : vos restes seront recycles, rien ne se perd dans l'espace." (fond de
    combat réutilisé en placeholder, décision utilisateur, à remplacer par un fond dédié)
  - Chaque carte candidate affiche son coût en électricité sous forme d'emoji (⚡N, plutôt qu'un
    texte "Coût N") et sa description d'effet en toutes lettres, générée depuis ses données
    (type/cible/action/valeur/durée) : `texte_effet_carte()` dans `src/ui/fenetre.py` côté PC
    (réutilisable par d'autres écrans, notamment le futur écran de deck complet, §6 plus bas),
    `texteEffetCarte()` déjà existant dans `src/web/app.js` côté web (réutilisé tel quel, `bridge.py`
    enrichi des champs `type`/`cible`/`action`/`duree`/`valeur` par candidate)
- **Écran "deck en entier"** : consultable depuis plusieurs endroits du parcours (pour l'instant
  uniquement depuis l'Écran de partie via "Voir le deck", §10.3 — pas encore depuis les autres
  écrans du parcours) — grille de toutes les cartes actuellement possédées par le joueur, regroupées par modèle (une
  entrée par carte différente, avec un badge ×N si plusieurs exemplaires) plutôt qu'une case par
  exemplaire individuel
  - `Deck.toutes_cartes()` (`src/gameplay/deck.py`) réunit pioche + main + défausse + cartes
    épuisées ; `regrouper_cartes()` (`src/gameplay/carte.py`) transforme une liste de cartes en
    `(carte, quantité)` par modèle — fonctions gameplay partagées par les deux plateformes. Le
    modèle est identifié par **l'id de la carte** (`Carte.id`, son id dans `config/cartes.json`,
    renseigné par `charger_cartes` et conservé par `copie()`), pas par son nom : deux cartes
    différentes qui porteraient le même nom restent deux entrées distinctes. `Carte.id` sert aussi
    partout où une carte doit être rattachée au deck d'une partie (`ajouter_carte`/`retirer_carte`),
    en remplacement de l'ancienne recherche par identité d'objet (`id_de_carte`, supprimée)
  - **Implémenté** en écran autonome (même situation que les deux écrans précédents, pas encore
    relié à un vrai bouton dans l'UI) : `src/ui/ecran_deck.py` (PC, grille figée de 8 colonnes,
    survol d'une carte → panneau de description fixe en bas d'écran plutôt qu'une infobulle
    ancrée sur la carte, pour éviter tout chevauchement avec la ligne voisine dans une grille
    dense) ; `src/web/bridge.py` (`etat_deck`, cartes du combat en cours si actif sinon un deck de
    démonstration tiré au sort) + `src/web/app.js` (`voirDeck`, exposée sur `window` — pas
    d'infobulle au survol comme le reste de l'UI web, taper une carte affiche sa description
    dans un popup, même principe que `#info-carte` pour la main en combat)
- À la Planète commerciale (§2.2), achat direct de cartes contre de l'Argent ; la disponibilité de cartes Rares/Légendaires pour un module dépend de son niveau de mise à jour (Station service, §2.2)
- **Mettre à jour un module (Station service, §2.2) débloque directement les paliers de rareté
  disponibles pour ses candidates après combat** (et pour ses cartes à la Planète commerciale) :
  Niveau 1 = Commune uniquement, Niveau 2 = +Rare, Niveau 3 = +Légendaire (palier maximum) —
  décision utilisateur, remplace l'ancienne piste encore ouverte de probabilités graduelles.
  Implique qu'à terme, le tirage de récompense (`tirer_carte_recompense`) devra filtrer le pool par
  palier débloqué du module concerné plutôt que retomber automatiquement au palier inférieur en cas
  de pool vide comme aujourd'hui (pas encore implémenté, cf. §2.2 pour l'état d'avancement)

---

## 7. Types de cartes

### 7.1 Types (par effet)

Classification par nature de l'effet — remplace l'ancien découpage par portée/persistance.

| Type | Description | Sous-catégories |
|---|---|---|
| **Attaque** | Inflige des dégâts | Direct / décalé (dégâts différés) / poison (dégâts sur la durée) |
| **Defense** | Protège un ou plusieurs modules | Bouclier absolu (x tours), réduction de dégâts en %, régénération de Bouclier sur la durée |
| **Controle** | Neutralise ou limite un ennemi | Stun, restriction d'action (ex : pas d'attaque ce tour) |
| **Debuff** | Affaiblit une cible ennemie | Plafond de dégâts infligés, réduction en %, réduction de Bouclier |
| **Buff** | Renforce le vaisseau ou un module | Augmentation de dégâts, augmentation de Bouclier |
| **Reparation** | Répare les PV d'un module | (voir aussi module Réparation, §4.2) — remplace l'ancien type "Soin" |
| **Outils** | Manipule la pioche/défausse ou l'électricité | Piocher, défausser, recycler... ; gagner/convertir de l'électricité |

Noms de type volontairement **sans accent** (Defense, Controle, Reparation), pour correspondre
directement aux futures valeurs de l'enum `TypeCarte` côté code (§10). Le moteur actuel n'implémente
encore qu'un sous-ensemble : voir §12.5 pour l'état d'implémentation par type.

### 7.2 Cible

Troisième axe, indépendant du type — n'importe quel type (pas seulement Attaque) peut cibler différents camps/motifs : une Défense peut protéger un allié unique ou tout le vaisseau, un Debuff peut viser un ennemi unique ou tout un rang, etc.

| Cible | Description |
|---|---|
| **Soi** | Le module qui joue la carte |
| **Allié unique** | Un module ami au choix (parfois avec contrainte : adjacent, à portée...) |
| **Alliés multiples / vaisseau entier** | Plusieurs modules ciblés, ou tout le vaisseau |
| **Ennemi unique** | Une cible ennemie, avec contraintes de rang possibles (rang avant uniquement, n'importe quel rang...) |
| **Ennemis multiples** | Motif fixe (ligne, colonne, rang entier) ou aléatoire, jusqu'à tous les ennemis |
| **Ligne ennemie** | Cas particulier d'"ennemis multiples" pour les cartes perçantes (§3.1) : touche l'avant et l'arrière de la rangée de la cible cliquée (2 ennemis au plus) |

### 7.3 Rareté

Axe indépendant du type et de la cible — une carte a un type, une cible **et** une rareté.

| Palier | Fréquence | Puissance |
|---|---|---|
| **Commune** | Fréquente | Effets simples et fiables, cœur du deck |
| **Rare** | Peu fréquente | Meilleur ratio effet/électricité, ou mécanique inédite |
| **Légendaire** | Très peu de cartes | Effets exceptionnels, peuvent changer la façon de jouer un module (ex : Reconstruction, §4.2) |

- La rareté pondère le tirage des **candidates de carte** offertes après un combat gagné (§6, une candidate par module équipé) ainsi que la disponibilité des cartes à la Planète commerciale (§2.2) : plus une carte est rare, moins elle a de chances d'apparaître, sauf module suffisamment amélioré (Station service, §2.2)
- Le tag "rare" déjà présent sur *Reconstruction* (§4.2) sera à réévaluer : son effet (résurrection d'un module) correspond plutôt au palier **Légendaire**
- Rareté et attribution précise par carte (§4.1-4.3) : à faire dans une passe dédiée (voir §9.1 "compléter le jeu de cartes")

### 7.4 Munitions

Axe indépendant du type, de la cible et de la rareté — une carte a, en plus de son coût en
électricité, un nombre de munitions : soit **illimité** (comportement par défaut, cf. §3.6), soit un
nombre fixe qui se consomme au fil du combat et se réinitialise au combat suivant. Voir §3.6 pour le
détail du fonctionnement (pile "cartes épuisées", compteur par exemplaire).

- Sert à limiter des effets ponctuellement très forts (ex : Bouclier perpétuel, §4.2) sans les
  rendre indéfiniment répétables dans un même combat
- Rôle par rapport à la rareté : deux axes différents, une carte Commune peut avoir des munitions
  limitées et une carte Légendaire des munitions illimitées, ou l'inverse — pas de règle systématique
  pour l'instant (voir §9.1)

---

## 12. Mécaniques de carte : référence d'implémentation et manques restants

En important le tableau de conception de cartes de l'utilisateur dans `config/cartes.json` (voir la
PR "config : import des cartes Module principal, Lanceur de missiles, Blindage"), seules 6 des 38
cartes du tableau correspondaient à ce que le moteur (`src/gameplay/carte.py`, `combat.py`) savait
exécuter à l'époque. Ce nombre a augmenté au fil des mécaniques ajoutées, groupées ci-dessous par
nature plutôt que par carte : la plupart sont désormais **implémentées** (détail par mécanique dans
chaque sous-section) ; les cartes dont la mécanique ne l'est pas encore restent stockées pour
référence (champ `_non_jouable`) mais inertes en jeu.

**Reste à implémenter** (résumé — le détail de chaque mécanique déjà en place est dans les
sous-sections ci-dessous, ce résumé ne liste que ce qui manque encore) :

- Effets à deux valeurs X/Y sur une même carte : cible cliquée + splash différencié (*Missiles*),
  deux zones différentes en une carte (*Torpille*) — §12.2
- Effets à durée : dégâts répétés pendant Y tours (*Embrasement, Guerre nucléaire, Tir
  incendiaire* — Module principal, carte ajoutée depuis, nom inventé), pioche bonus pendant Y tours
  (*Multi fonction*) — §12.3
- Transfert des dégâts subis vers un autre module désigné (*Transfert*) — §12.6. Le renvoi des
  dégâts subis à l'attaquant (*Renvoie*) est désormais **implémenté**, la carte a été repensée
  (décision utilisateur) pour utiliser directement le Bouclier miroir déjà existant côté ennemi
  (§13.2) plutôt qu'un renvoi de dégâts brut inédit — renommée *Renvoi*, jouable, cf. §12.6
- Méta-effets : changer le coût en électricité de toutes les cartes d'une catégorie (*Optimisation
  des boucliers, Attaques performantes*), dupliquer l'effet de toutes les cartes d'une catégorie ou
  d'une carte précise (*Double défense, Circuit parallèle, Salve laser, Protocole d'urgence* — ces
  deux dernières ajoutées depuis pour le Module principal, noms inventés) — bloque aussi certaines
  cartes à munitions limitées (§12.10) qui en dépendent — §12.7
- Bloquer la dissipation naturelle du Bouclier en début de tour (§3.5) : *Bouclier stabilisé*
  (Module principal, carte ajoutée depuis, nom inventé) — mécanique inédite, aucune carte existante
  n'en avait besoin jusqu'ici — §12.5
- Gain d'électricité en échange d'une défausse (*Manque de jus, Cannibalisme*) — §12.8
- Manipulation de pioche/main/défausse : piocher puis défausser (*Changement d'outil*), tout
  défausser puis repiocher (*Grand remplacement*), défausser une quantité choisie entre X et Y
  (*Cannibalisme*, nécessite un sous-choix de quantité au moment de jouer la carte) — §12.9
- Type Controle (stun, restriction d'action) : aucune carte taguée Controle dans le tableau pour
  l'instant, rien à implémenter tant qu'aucune n'existe — §12.5

### 12.1 Cibles fixes ou par rang — entièrement implémenté

- **Module Principal** — cible toujours le module de base, sans choix du joueur — **implémenté**
  (`CibleCarte.MODULE_PRINCIPAL`, sans clic) : *Protéger le vaisseau, Réparation, Blindage maximal*
  jouables
- **Ennemi Avant** / **Ligne avant** ennemie, **Ennemi Arrière** / **Ligne arrière** — **implémenté**
  (`CibleCarte.COLONNE_AVANT_ENNEMIE` / `COLONNE_ARRIERE_ENNEMIE`, colonne fixée par la carte, un
  clic sur l'autre colonne est refusé) : *Ligne avant, Ligne arrière* jouables
- **Module Avant** — colonne avant alliée : avant-gauche + avant-droite, **et le module
  principal** (qui occupe la rangée mid et compte donc à la fois comme avant et comme arrière,
  décision utilisateur — contrairement à une première version qui l'excluait) — **implémenté**
  (`CibleCarte.COLONNE_AVANT_ALLIEE`, même principe que les colonnes ennemies : un clic sur un
  module de cette colonne précise, ou sur le module principal, confirme) : *Protéger l'avant
  poste* jouable

Ces cibles par rang se résolvent par un **clic sur une case du rang visé**, comme la Ligne ennemie
perçante (§3.1, §7.2), et non automatiquement comme Alliés/Ennemis multiples.

### 12.2 Effets à deux valeurs (X et Y) sur une même carte

- Cible unique + splash différencié : X à la cible cliquée, Y à toutes les autres (*Missiles*)
- Deux zones différentes en une carte : X sur la ligne avant ennemie, Y sur la ligne arrière
  (*Torpille*)

### 12.3 Effets à durée (plusieurs tours)

Debuff actif pendant Y tours (chaque application ajoutée à la liste `Ennemi.buffs_actifs`, comme
une instance indépendante avec sa propre durée ; décrémentée à chaque tour ennemi écoulé même si
l'ennemi concerné n'a pas agi, et retirée de la liste à 0) — **implémenté** pour les debuffs
(§12.4/§12.5) : *Boucliers hors service* jouable. Depuis §13, cette liste est **partagée avec les
buffs** posés par les Actions des ennemis eux-mêmes (ex. Petit Jean se pose du bouclier) : buffs et
debuffs ne sont plus que des cas d'usage du même modèle `BuffActif` (`carte.py`), qu'ils s'appliquent
à un `Module` ou à un `Ennemi`.

Même mécanique côté allié (`Module.buffs_actifs`), avec en plus la possibilité d'une durée **nulle**
(`tours_restants=None`) pour un buff **persistant** qui ne décompte jamais et dure tout le combat —
**implémenté** (§12.5) : *Bouclier perpétuel* (persistant) et *Blindage maximal* (durée limitée,
même mécanisme `BOUCLIER_PAR_TOUR` avec `duree` finie plutôt que nulle) jouables — les deux seules
cartes Buff à effet périodique simple (les 3 autres cartes Buff restantes sont des méta-effets, cf.
§12.5/§12.7). L'effet d'un buff se déclenche une première fois immédiatement à la pose de la carte
(comme les autres types de carte), puis se redéclenche à chaque début de tour joueur tant qu'il
reste actif. Pour un buff `BOUCLIER_PAR_TOUR`, ce redéclenchement pose du Bouclier frais
**après** la dissipation naturelle du tour (§3.5), qui ne fait que diviser par deux la valeur
existante tant qu'elle dépasse le seuil : le Bouclier peut donc croître au-dessus de la valeur du
buff avant de se stabiliser à un palier plus élevé (cf. §3.5 pour l'exemple chiffré).

Un buff persistant cible toujours le **module principal** plutôt qu'un module au choix du joueur
(déviation assumée de la cible "Module Unique" du tableau de conception, décision utilisateur) : lui
seul est garanti de survivre tout le combat (§3.4), donc le seul module où un effet censé durer
jusqu'à la fin a du sens. Sur un module, les buffs à durée limitée et les buffs persistants sont
affichés **séparément** (deux pastilles distinctes avec un compte chacune, jamais additionnées ; deux
groupes distincts dans l'infobulle), pour que le joueur distingue d'un coup d'œil ce qui va expirer
de ce qui ne bougera plus jusqu'à la fin du combat.

Reste manquant pour les autres effets à durée :

- Dégâts répétés pendant Y tours (*Embrasement, Guerre nucléaire*)
- Pioche bonus pendant Y tours (*Multi fonction*)

### 12.4 Effets en pourcentage — entièrement implémenté

**Implémenté pour les debuffs** (somme des `valeur` des debuffs `VULNERABILITE` actifs dans
`Ennemi.buffs_actifs`, majore les dégâts subis d'une attaque du joueur) : *Brèche, Ligne avant,
Boucliers endommagés, Boucliers hors service* jouables. **Implémenté aussi côté allié**
(`ActionCarte.BOUCLIER_POURCENTAGE_PV` sur une carte Defense : bouclier = `valeur`% des PV **max**
de la cible cliquée — les PV actuels varieraient trop selon les dégâts déjà subis, l'effet doit
rester prévisible — arrondi à l'entier le plus proche) : *Bouclier adaptatif* jouable.

### 12.5 Types de carte absents du moteur

Déjà nommés en §7.1. État d'implémentation dans `combat.py` :

- **Reparation** — **implémenté** (renommage de l'ancien type `SOIN`, même logique)
- **Debuff** — **implémenté** (`TypeCarte.DEBUFF`, trois actions : `REDUCTION_DEGATS`,
  `VULNERABILITE` et `REDIRECTION_CIBLE`, cf. §12.1/§12.3/§12.4/§12.6) : *Tordre le canon, Brèche,
  Ligne avant, Boucliers endommagés, Boucliers hors service, Tir allié* jouables — les 6 cartes du
  module Sabotage sont maintenant toutes jouables
- **Buff** — **implémenté** (`TypeCarte.BUFF`, une action : `BOUCLIER_PAR_TOUR`, cf. §12.3) :
  *Bouclier perpétuel, Blindage maximal, Blindage cible* (Module principal, carte ajoutée depuis,
  nom inventé — même mécanique que *Blindage maximal*, cible Module Unique au lieu de Module
  Principal) jouables. *Optimisation des boucliers, Attaques performantes* (modification du coût
  d'une catégorie de cartes), *Double défense, Circuit parallèle, Salve laser, Protocole d'urgence*
  (duplication d'effet, cf. §12.7) et *Bouclier stabilisé* (blocage de la dissipation naturelle du
  Bouclier, Module principal, carte ajoutée depuis, nom inventé — aucune mécanique existante à
  réutiliser, `combat._dissiper_bouclier`/§3.5 s'applique inconditionnellement pour l'instant)
  restent non jouables, ce sont des méta-effets ou des mécaniques inédites, pas de simples buffs sur
  un module
- **Outils** — **implémenté** (`TypeCarte.OUTILS`, cf. §12.9) pour trois actions (`GAIN_ELECTRICITE`,
  `GAIN_ELECTRICITE_PAR_MODULE`, `PIOCHE_SUPPLEMENTAIRE`) : *Surcharge temporaire, Fonds de tiroir,
  Boost* jouables. Le reste demande encore une logique dédiée (*Changement d'outil, Manque de jus,
  Cannibalisme, Grand remplacement, Multi fonction*)
- **Controle** : toujours aucune carte taguée Controle dans le tableau ; type prévu en §7.1 (stun,
  restriction d'action) mais rien à implémenter pour l'instant

### 12.6 Altération / redirection des dégâts

- Transfert des dégâts subis vers un autre module désigné (*Transfert*)
- Renvoi des dégâts subis à l'attaquant — **implémenté** (décision utilisateur : la carte, renommée
  *Renvoi* (ex-*Renvoie*), pose un Bouclier miroir sur le module cible plutôt qu'un renvoi de
  dégâts brut inédit, en réutilisant directement `ActionCarte.BOUCLIER_MIROIR`/
  `Combat._consommer_bouclier_miroir` déjà écrits pour l'ennemi Miroir (§13.2) — ces fonctions
  étaient déjà génériques `Module | Ennemi`, aucun changement moteur nécessaire) : *Renvoi* jouable
- Annulation totale de la prochaine attaque sur une cible, différent d'un bouclier classique
  (*Leurre*) — **implémenté** (`ActionCarte.ANNULATION_PROCHAINE_ATTAQUE`, sur une carte Defense) :
  *Leurre* jouable. Un flag `Module.leurre_actif` (pas un buff : pas de redéclenchement
  périodique, pas de durée en tours) rend la **toute prochaine** attaque reçue totalement nulle
  (0 dégât, y compris si elle dépasserait PV+bouclier cumulés), puis se consomme — dès la première
  attaque reçue après la pose, même si plusieurs ennemis attaquent ce module dans le même tour —
  seule la **première** attaque résolue sur ce module est annulée, dans l'ordre de résolution du
  tour ennemi (`Combat._tour_ennemi` : colonne Avant de haut en bas puis colonne
  Arrière de haut en bas), les suivantes s'appliquent normalement. L'intention affichée au
  survol/tap d'un ennemi montre toujours sa **vraie** attaque, jamais 0 à cause d'un
  leurre potentiellement actif sur sa cible : elle reflète ce que cet ennemi ferait pris
  isolément, pas le résultat final après résolution de tout le tour (qui dépend de l'ordre).
  Pastille dédiée (cyan) distincte des pastilles de buff, affichée tant que le leurre n'a pas
  encore été consommé
- Détournement de la cible d'un ennemi vers un de ses voisins — mécanique déjà anticipée comme
  *Piratage* en §4.2 — **implémenté** (`ActionCarte.REDIRECTION_CIBLE`) : *Tir allié* jouable. Le
  "voisin" est **n'importe quel autre ennemi vivant** (pas de restriction géométrique d'adjacence,
  décision prise avec l'utilisateur) — l'ennemi debuffé attaque un allié à lui tiré au hasard parmi
  les ennemis vivants restants, plutôt qu'un module du joueur, à son prochain tour ; sans autre
  ennemi vivant, il attaque normalement (rien à rediriger vers). Le tirage au hasard n'a lieu qu'à
  la résolution réelle du tour (`Combat._cible_redirection`), jamais lors d'un simple survol/tap de
  prévisualisation (`Combat.previsualiser_cible`), pour ne pas consommer l'aléa à chaque redessin —
  l'UI affiche alors "Vise un allié au hasard" plutôt qu'une cible précise, tant que le tour n'est
  pas résolu

### 12.7 Modification des règles d'autres cartes (méta-effets)

- Changer le coût en électricité de toutes les cartes d'une catégorie pour le reste du combat
  (*Optimisation des boucliers, Attaques performantes*)
- Dupliquer l'effet de toutes les cartes d'une catégorie X fois (*Double défense, Circuit
  parallèle*), d'une carte précise nommément (*Salve laser* — Module principal, carte ajoutée
  depuis, nom inventé, cible *Laser*) ou de toute une rareté (*Protocole d'urgence* — Module
  principal, carte ajoutée depuis, nom inventé, cible les cartes Base) — même famille de mécanique
  non implémentée, sous des granularités différentes (une catégorie entière, une carte nommée, une
  rareté entière)

### 12.8 Gain d'électricité via une carte

- Gain fixe (*Surcharge temporaire*) — **implémenté** (`ActionCarte.GAIN_ELECTRICITE`)
- Gain proportionnel au nombre de modules actifs (*Fonds de tiroir*) — **implémenté**
  (`ActionCarte.GAIN_ELECTRICITE_PAR_MODULE`, `valeur` x nombre de modules alliés vivants, base
  incluse - mêmes modules que `Combat._modules_vivants()`, déjà utilisé pour Alliés multiples §7.2)
- Gain en échange d'une défausse (*Manque de jus, Cannibalisme*)

### 12.9 Manipulation de pioche / main / défausse via une carte

- Piocher des cartes supplémentaires — **implémenté** (`ActionCarte.PIOCHE_SUPPLEMENTAIRE`,
  `Deck.piocher_cartes()`) : *Boost* jouable. Manque encore la durée pour *Multi fonction*
- Piocher puis défausser en une carte (*Changement d'outil*)
- Défausser toute la main puis repiocher autant (*Grand remplacement*)
- Défausser une **quantité choisie par le joueur** entre X et Y (*Cannibalisme*) — nécessite un
  sous-choix de quantité au moment de jouer la carte, en plus du ciblage habituel

### 12.10 Munitions limitées

Déjà spécifiées en §3.6/§7.4 (mécanique de jeu tranchée) — **implémenté** (`Carte.munitions_max`/
`munitions_restantes`, pile `Deck.cartes_epuisees`) : *Réparation* jouable. Reste bloqué par
d'autres mécaniques manquantes pour les autres cartes à munitions (*Bouclier perpétuel,
Optimisation des boucliers, Attaques performantes*, qui ont toutes en plus besoin du type Buff).

### 12.11 Note annexe : cible des cartes Soute

Les 6 cartes du module Soute (pioche/défausse/électricité) portaient une cible "Ennemi Tous" dans le
tableau source, incohérente pour des cartes qui ne visent aucun ennemi. Corrigé dans
`config/cartes.json` : elles se jouent en cliquant **n'importe quel module allié**, dont l'identité
n'a aucune influence sur l'effet (celui-ci porte sur le deck ou l'électricité, ressources communes
au vaisseau, pas sur le module cliqué).
