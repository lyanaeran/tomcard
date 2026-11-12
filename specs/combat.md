# Space Fight — Combat et ennemis (§3 et §13)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

---

## 3. Système de combat

### 3.1 Placement / rangs
- Formation en **2 rangs** : avant et arrière, pour le joueur et pour l'ennemi
- Corps à corps : ne peut frapper que le rang avant adverse
- Distance : peut frapper n'importe quel rang
- Certaines compétences perçantes touchent l'avant + l'arrière simultanément
- Le placement des modules fragiles/soigneurs à l'arrière devient une décision tactique
- Idée de module dédié (Propulseur) pour repositionner en cours de combat

### 3.2 Tailles de monstres
- Trois tailles : **S, M, L**
- Le joueur connaît la composition annoncée avant le combat (ex : "2 S + 1 M") mais pas le détail exact des ennemis
- **S** : 1 emplacement, PV faibles, souvent en groupe
- **M** : 1 emplacement, PV/dégâts intermédiaires
- **L** : gros PV, attaque de zone ou pattern en plusieurs temps
- **Nombre d'emplacements occupés** (`SpecEnnemi.emplacements`, `ennemi.py:Ennemi.emplacements`) :
  champ indépendant de la taille (contrairement à la version initiale de cette règle) — 1 par défaut
  pour tous les ennemis existants, sauf le Boss des pirates (§13.3, taille M mais 2 emplacements :
  une case Avant + une case Arrière de la même rangée). Une taille L ne prend donc pas forcément 2
  emplacements, ni une taille M forcément 1 seul — c'est ce champ, jamais la taille, qui pilote
  l'occupation réelle dans `Flotte`. Décision utilisateur, à confirmer côté design (le Boss des
  pirates a été donné comme taille M avec 2 emplacements, ce qui contredisait la règle précédente
  M=1/L=2 — plutôt que de le reclasser en L, la règle a été assouplie).
- Un ennemi à plusieurs emplacements est le même objet `Ennemi` rangé à plusieurs `Position` dans
  `Flotte` (§13.4) : réservé aux flottes scriptées (`creer_flotte_boss`), jamais tiré au hasard dans
  un combat Prime/démonstration/Astéroïdes (`config_poc._pool_ennemis_standard` l'exclut du pool)

### 3.3 Ressource et main de cartes
- **Électricité** = ressource commune à tout le vaisseau (pas un pool par module)
- Le joueur pioche une main et joue ses cartes **librement, dans l'ordre de son choix** (comme dans Slay the Spire)
- Force des choix de répartition : concentrer l'électricité sur un module ce tour, ou répartir
- **Ordre de jeu** : tour classique façon StS — le joueur joue librement toutes les cartes qu'il souhaite durant son tour, puis le tour ennemi se déroule. Pas de système d'initiative/vitesse par module
- **Main** : capacité maximale de 10 cartes ; le joueur pioche 5 cartes par tour. Cartes jouées partent en défausse ; quand la pioche est vide, la défausse est mélangée pour reformer la pioche. Exception : une carte à munitions limitées épuisée (0 munition restante) part dans la pile **cartes épuisées** au lieu de la défausse, cf. §3.6
- **Fin de tour** : les cartes non jouées restant en main sont défaussées à la fin du tour du joueur (comme dans Slay the Spire), avant la pioche de la main suivante

### 3.4 Destruction de module
- Un module à **0 PV est détruit**, même si le combat est gagné (perte permanente)
- Le **module de base** est la condition de game over : sa destruction termine la run
- **Récupération entre combats** : aucune régénération automatique des PV — seule la Réparation (module dédié, voir 4.2) permet d'en restaurer. Le vaisseau garde ses dégâts d'un combat à l'autre, sauf passage par une Station Service (voir §2)

### 3.5 Bouclier
- Le Bouclier absorbe les dégâts subis **avant** les PV. Exemple : un module protégé par 5 Bouclier subit une attaque de 7 dégâts → le Bouclier absorbe 5, les **2 dégâts restants** sont retirés des PV
- Un ennemi peut lui aussi avoir du Bouclier (specs.md §13), avec exactement la même règle
  d'absorption qu'un module
- **Dissipation naturelle** : à chaque tour (tour joueur pour un module, tour ennemi pour un
  ennemi), si le Bouclier actuel est ≤ 5 (`SEUIL_DISSIPATION_BOUCLIER`, `combat.py`) il disparaît
  complètement ; sinon il est divisé par deux (arrondi au-dessus) — la valeur est vérifiée
  **avant** la division, pas après. Garantit qu'un Bouclier finit toujours par disparaître
  entièrement plutôt que de décliner sans fin (`ceil(1/2)=1` ne convergerait jamais vers 0 sans ce
  seuil). La dissipation a lieu **avant** qu'un buff `BOUCLIER_PAR_TOUR` actif ce tour-là ne repose
  du Bouclier frais (§12.3) : un Bouclier persistant ou à durée n'est donc pas simplement remis à
  sa valeur de pose à chaque tour, il peut croître au-dessus si sa valeur reste supérieure au seuil
  après division (ex. buff de valeur 10 : 10 → 5+10=15 → 8+10=18 → ... → se stabilise à 20, point
  fixe où diviser par deux puis rajouter 10 redonne 20). Ne s'applique **pas** au Bouclier miroir
  (§13.2), qui est un mécanisme distinct (buff à part, consommé uniquement par le renvoi de
  dégâts, jamais par dissipation)
- Valeur du seuil (5) inventée faute de spec précise — à ajuster à l'équilibrage, comme les
  autres valeurs numériques du même type (§13)

### 3.6 Munitions (cartes à usage limité)

Certaines cartes ont un nombre de munitions limité en plus de leur coût en électricité (cf. §7.4) :

- **Munitions illimitées** (cas par défaut, toutes les cartes actuelles du POC) : aucun changement, la carte se joue normalement, autant de fois que voulu tant que l'électricité suit
- **Munitions limitées à N** : chaque utilisation de la carte décrémente son compteur de munitions restantes. Le compteur est **propre à chaque exemplaire physique de la carte dans le deck** (si le deck contient 2 exemplaires d'une carte à 1 munition, chacun peut être joué une fois, soit 2 utilisations au total sur le combat)
- Quand le compteur d'un exemplaire tombe à **0**, cet exemplaire quitte définitivement le combat : au lieu de partir en défausse, il rejoint une nouvelle pile, les **cartes épuisées**, distincte de la pioche et de la défausse
- Les cartes épuisées ne reviennent **jamais** dans la pioche pendant le combat en cours, même si la pioche et la défausse sont toutes les deux vides (pas de mélange de secours) — cf. §9.1 pour le cas limite où cela viderait totalement les cartes piochables
- **Entre deux combats**, chaque carte à munitions limitées repart avec son nombre de munitions d'origine (le compteur ne persiste pas d'un combat à l'autre) — cohérent avec le fait que le deck de combat est reconstitué à chaque combat à partir des pools de cartes des modules équipés (§6)

---

## 13. Comportement des ennemis (IA)

Remplace les 3 ennemis placeholder du POC (ENM_1/2/3, dégâts fixes tirés au hasard chaque tour) par
5 ennemis à comportement scripté (`config/ennemis.json`), et introduit le modèle qui les décrit.
Deux listes distinctes, indépendantes l'une de l'autre (décision utilisateur) :

1. **Les Actions** (`ennemi.py:ActionEnnemi`) — le *comportement* d'un ennemi : une liste ordonnée
   d'Actions, chacune caractérisée par :
   - `type` : `ATTAQUE` (inflige des dégâts) ou `POSE_BUFF` (pose un buff/debuff, cf. point 2)
   - `cible` : qui l'Action touche (`CibleActionEnnemi`, cf. plus bas)
   - `valeur` : montant de dégâts (ATTAQUE) ou valeur numérique du buff posé (POSE_BUFF)
   - `frequence` : l'Action se déclenche tous les *frequence* tours ennemi (1 = tous les tours)
   - `tour_depart` : à partir de quel tour ennemi elle peut se déclencher (1 = dès le premier tour
     ennemi du combat) — ensemble, ces deux champs déterminent l'activation d'un tour donné :
     `tour >= tour_depart et (tour - tour_depart) % frequence == 0` (`ActionEnnemi.active_au_tour`)
   - `repetitions` : nombre de fois que l'Action s'exécute **dans le même tour** quand elle se
     déclenche (axe indépendant de `frequence`/`tour_depart`, qui décide *quels* tours, pas combien
     de fois *dans* le tour) — ex. Le nettoyeur attaque 2 fois par tour (`repetitions=2`,
     `frequence=1`), quand Petit Jean ne pose son bouclier qu'un tour sur deux (`frequence=2`,
     `repetitions=1`)
   - `action_buff`/`duree_buff` (uniquement pour `type=POSE_BUFF`) : quel `ActionCarte` poser (les
     mêmes valeurs que sur une carte joueur, cf. §7.1/§12.5, ex. `BOUCLIER_PAR_TOUR`,
     `BOUCLIER_MIROIR`) et sa durée (`null` = persistant, comme un buff joueur §12.3)
   Un ennemi vivant exécute, à son tour, chacune de ses Actions actives ce tour-là, dans l'ordre de
   sa propre liste, chaque Action s'exécutant `repetitions` fois d'affilée avant de passer à la
   suivante (`Combat._tour_ennemi`).

2. **Les buffs/debuffs** (`carte.py:BuffActif`) — l'*état* passif d'un ennemi ou d'un module, une
   liste de buffs actifs indépendants (aucune fusion entre instances, même modèle des deux côtés
   des combattants, cf. §12.3) : `action` (un `ActionCarte`), `valeur`, `tours_restants` (`null` =
   persistant). "Buff" et "debuff" ne sont qu'un usage différent du même modèle (décision
   utilisateur) : un buff posé par le joueur sur un module se redéclenche à chaque tour joueur
   (`Module.declencher_buffs_tour`, §12.3), alors qu'un buff posé par une Action ennemie (sur
   l'ennemi lui-même ou sur un module joueur) ne se redéclenche **jamais** automatiquement — c'est
   la `frequence` de l'Action qui le pose qui décide quand il est reposé, pour ne pas cumuler les
   deux mécanismes de périodicité. Les ennemis peuvent désormais avoir du **Bouclier** comme les
   modules (même principe d'absorption avant les PV, §3.5).

### 13.1 Cibles d'une Action (`CibleActionEnnemi`)

- `PROXIMITE` : même règle que le ciblage historique du POC (`ciblage.py:module_cible_par_ennemi`,
  la rangée de l'ennemi d'abord, puis les rangées voisines si elle est vide) — sujette à Tir allié
  (§12.6) comme avant
- `TOUS_MODULES_JOUEUR` : tous les modules du joueur encore en vie (attaque de zone ennemie,
  symétrique des cartes joueur de type Alliés/Ennemis multiples) — jamais redirigée par Tir allié
  (pas de cible individuelle à rediriger)
- `COLONNE_AVANT_SINON_ARRIERE_JOUEUR` : un module du joueur tiré au hasard dans la colonne avant
  (base incluse, comme en §12.1) s'il y en a un de vivant, sinon dans la colonne arrière — le
  tirage n'a lieu qu'à la résolution réelle du tour, jamais au survol/tap (même principe que Tir
  allié, §12.6, pour rester déterministe). Plus utilisée par aucun ennemi actuel (Miroir, seul
  utilisateur, cible désormais un ennemi allié - cf. `COLONNE_AVANT_SINON_ARRIERE_ENNEMIE`
  ci-dessous et §13.2), conservée pour un futur ennemi qui ciblerait le joueur de cette façon
- `COLONNE_AVANT_SINON_ARRIERE_ENNEMIE` : un ennemi de la flotte tiré au hasard (l'ennemi qui
  exécute l'Action y compris — ex. Miroir peut se cibler lui-même) dans la colonne avant s'il y en
  a un de vivant, sinon dans la colonne arrière (ex. Miroir pose un Bouclier miroir sur un allié,
  §13.2)
- `SOI_MEME` : l'ennemi qui exécute l'Action (uniquement pertinent pour `POSE_BUFF`)

### 13.2 Bouclier miroir (`ActionCarte.BOUCLIER_MIROIR`)

**Changement de cible (décision utilisateur) :** posé désormais sur un **ennemi allié**
(`COLONNE_AVANT_SINON_ARRIERE_ENNEMIE`, §13.1 — colonne avant de la flotte si elle compte un
ennemi vivant, sinon arrière, Miroir peut se cibler lui-même) plutôt que sur un module du joueur
comme dans la version initiale de cette mécanique. Objectif inversé : protéger un allié ennemi
contre les attaques **du joueur**, plutôt qu'un module du joueur contre les attaques ennemies.

Tant qu'il est actif, une attaque reçue par l'ennemi protégé est en partie **renvoyée** : jusqu'à
la valeur du bouclier miroir, les dégâts sont retirés à l'attaquant plutôt qu'à la cible protégée ;
le reste (si les dégâts dépassent la valeur du bouclier miroir) s'applique normalement à la cible.
Se consomme comme un bouclier classique (sa valeur diminue à chaque dégât renvoyé, l'instance est
retirée à 0) ; plusieurs instances peuvent coexister sur une même cible, consommées dans l'ordre de
pose. Deux mécanismes distincts selon qui attaque, chacun avec sa propre méthode de consommation :

- **Une Action ennemie attaque l'ennemi protégé** (ex. Tir allié détourne un tir vers lui,
  §12.6) : l'« attaquant » est un `Ennemi` bien identifié — les dégâts lui sont renvoyés
  directement (`Combat._consommer_bouclier_miroir`/`_resoudre_attaque`), comme dans la version
  initiale de cette mécanique
- **Le joueur attaque l'ennemi protégé** (une carte) : il n'y a pas d'« attaquant » identifiable
  côté joueur (une carte n'est liée à aucun module, l'électricité est une ressource commune) — donc
  chaque instance de Bouclier miroir renvoie plutôt vers **son propre module du joueur**, tiré au
  hasard **une bonne fois pour toutes à la pose du buff** (`BuffActif.cible_reflet`,
  `Combat._executer_pose_buff`/`_consommer_bouclier_miroir_vers_joueur`), jamais à la résolution de
  l'attaque : contrairement à Tir allié (cible réelle découverte seulement à la résolution, pour
  rester déterministe au survol/tap), ce choix est **affiché dès la pose** dans l'infobulle de
  l'ennemi protégé (`Bouclier miroir 5 -> Principal`, PC `_libelle_buff`/web
  `libelleEffetActif`+`cible_reflet_nom`) : le joueur peut anticiper quel module de son vaisseau
  est en jeu avant de décider d'attaquer ou non la cible protégée

### 13.3 Les ennemis (`config/ennemis.json`)

Les 5 premiers remplacent entièrement les 3 ennemis placeholder du POC (ENM_1/2/3, retirés) ; le
Boss des pirates a été ajouté séparément comme boss unique du parcours (§13.4) :

| Ennemi | Taille | PV | Comportement |
| --- | --- | --- | --- |
| Pat le Pirate | S | 50 | Attaque 5 dégâts par tour, cible de proximité |
| Le nettoyeur | S | 25 | Attaque 7 dégâts, **2 fois** par tour (`repetitions=2`), cible de proximité |
| Petit Jean | S | 100 | Attaque 2 dégâts par tour (proximité) ; tous les 2 tours (à partir du tour 1), se pose 3 bouclier pendant 2 tours |
| Le puzzle | S | 50 | Attaque 5 dégâts **tous les modules du joueur** par tour (zone) |
| Miroir | S | 50 | Attaque 2 dégâts par tour (proximité) ; chaque tour, pose un Bouclier miroir de valeur 5 (persistant) sur un ennemi allié tiré au hasard (lui-même inclus, colonne avant sinon arrière) |
| Le Boss des pirates | M, 2 emplacements | 150 | Attaque 5 dégâts **tous les modules du joueur** par tour (zone) ; à partir du tour 2, tous les 3 tours, augmente ses dégâts d'attaque de 2 (persistant, cumulatif) ; à partir du tour 3, tous les 3 tours, se pose un bouclier de 5 |

Valeurs de PV/dégâts inventées faute de spec numérique précise (à ajuster à l'équilibrage) — à
signaler comme telles, cf. règle du fichier `CLAUDE.md`. Pour le Boss des pirates, seules ces
valeurs sont inventées : le reste (PV 150, dégâts 5, +2 dégâts et bouclier 5 tous les 3 tours à
partir du tour 2/3 respectivement) a été donné explicitement par l'utilisateur.

**Augmentation de dégâts** (`ActionCarte.AUGMENTATION_DEGATS`, Boss des pirates) : buff posé sur
l'ennemi lui-même (`SOI_MEME`), symétrique de `REDUCTION_DEGATS` — augmente au lieu de diminuer les
dégâts de ses futures Actions ATTAQUE (`Ennemi.degats_attaque_effectifs`). Comme tout buff posé par
une Action ennemie (point 2 ci-dessus), ne se redéclenche jamais automatiquement : c'est la
`frequence`/`tour_depart` de l'Action qui le pose (persistante, `duree_buff=null`) qui décide de son
rythme — chaque déclenchement ajoute une nouvelle instance indépendante, l'effet est donc cumulatif
et permanent (+2 au tour 2, +4 au tour 5, +6 au tour 8...). Pas encore utilisée par une carte joueur.

**Préférence de placement en flotte** (`SpecEnnemi.placement`, purement une préférence de
composition, pas un attribut de l'`Ennemi` en combat) :

- Le nettoyeur (`PROTEGE_ARRIERE`) : placé de préférence en colonne arrière
- Petit Jean (`PROTECTEUR_AVANT`) : placé de préférence en colonne avant, pour protéger les autres
- Les 3 autres (Pat le Pirate, Le puzzle, Miroir) : aucune préférence — placés dans les emplacements
  restants, colonne avant en priorité puis arrière (choix par défaut, pas de spec précise)
- Le Boss des pirates n'a pas de préférence de placement au sens de `SpecEnnemi.placement` : sa
  position (Avant + Arrière de la rangée du milieu) est câblée en dur dans `creer_flotte_boss`
  (§13.4), puisqu'il n'est jamais mélangé avec d'autres ennemis dans une même flotte

**Intention affichée au survol/tap** (décision utilisateur, suite au Boss des pirates qui a révélé
deux lacunes) — une ligne par Action active au prochain tour, pas seulement la première :

- `Combat.prochaines_actions_actives(ennemi)` renvoie **toutes** les Actions actives au prochain
  tour (`prochaine_action_active` n'en renvoyait qu'une seule — toujours la première de la liste,
  ce qui masquait silencieusement toute Action suivante comme un `POSE_BUFF` déclenché le même tour
  qu'une `ATTAQUE`, ex. le Boss des pirates ; conservée telle quelle, utilisée par
  `previsualiser_cible` qui ne s'intéresse qu'à une éventuelle Attaque de proximité). PC
  (`fenetre.py:_dessiner_survol`) et web (`bridge.py:_intentions_json`, une liste — remplace
  l'ancien champ singulier `intention`) itèrent désormais sur cette liste complète
- **Répétitions** (`ActionEnnemi.repetitions > 1`, ex. Le nettoyeur) : la ligne d'intention
  précise "x{repetitions}" (`Vise : Module (7 dégâts x2)`) — auparavant la valeur affichée
  correspondait à un seul coup sans l'indiquer, laissant croire que l'ennemi n'inflige que cette
  valeur alors que l'Action se répète plusieurs fois dans le même tour
- **Type de buff/debuff posé** (`POSE_BUFF`) : la ligne d'intention décrit désormais l'effet par
  son type (`_texte_type_buff`/`texteTypeBuff`, même mapping que les buffs déjà actifs, §13 point 2
  ci-dessus — ex. "Va poser Dégâts augmentés +2 (sur lui-même)") plutôt que le générique "Pose un
  effet (X)" d'origine, qui ne précisait ni le type d'effet ni sa cible (soi-même ou un module tiré
  au hasard)
- Corrigé au passage un bug latent côté web : `app.js:LIBELLES_ACTION_ACTIF` n'avait pas d'entrée
  pour `AUGMENTATION_DEGATS`, ce qui aurait fait planter l'infobulle web au survol/tap d'un ennemi
  portant ce buff déjà actif (jamais déclenché avant le Boss des pirates, premier à l'utiliser)

### 13.4 Composition des flottes de combat

> **Refonte branchée côté gameplay (PR 1, 2026-11-12, décision utilisateur du 2026-11-11 n° 4)** :
> mêmes règles, avec les ennemis de la refonte (`config/ennemi_new.json`), coefficient de
> difficulté 1, dans `src/gameplay/flotte_new.py` (`flotte_prime`, `flotte_boss`,
> `flotte_asteroides`, `placer_ennemis`) ; le placement préféré (protecteur à l'avant, protégé à
> l'arrière) vaut aussi pour les Astéroïdes. Le simulateur du combat de la refonte utilise le même
> placement. La difficulté par niveau sera réglée après le branchement, par simulation.

- **Combat Intermédiaire** (Prime) : 1 ennemi tiré au sort (parmi les ennemis à 1 emplacement)
  jusqu'au niveau 5 inclus, puis 2 ennemis tirés au sort à partir du niveau 6
  (`config_poc.creer_flotte_prime`) — le Boss des pirates (2 emplacements) est exclu de ce tirage
  (`_pool_ennemis_standard`, §3.2)
- **Combat de Boss** : composition fixe (pas de tirage) — le Boss des pirates seul, occupant à la
  fois la case Avant et la case Arrière de la rangée du milieu (`config_poc.creer_flotte_boss`).
  Remplace l'ancienne composition (2x Petit Jean en colonne avant, Le nettoyeur et Le puzzle en
  colonne arrière) — un seul boss pour l'instant, utilisé à tous les niveaux Boss (multiples de 10) ;
  l'utilisateur prévoit plusieurs boss avec un tirage au sort entre eux à terme, pas encore implémenté

### 13.5 Points de vie des modules (fin du mode test)

Le combat ne tourne plus en "mode test" (PV artificiellement gonflés) : les PV définis dans
`config/modules.json` s'appliquent réellement. Valeurs actuelles (inventées faute de spec précise,
à ajuster) : **50 PV** pour le module principal, **30 PV** pour chaque module secondaire.
