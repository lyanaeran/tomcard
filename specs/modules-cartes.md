# Space Fight — Modules et cartes (§4 à §7 et §12)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md). Décrit le moteur actuel (`src/gameplay/module.py`, `carte.py`,
`parcours.py`), issu de la refonte de novembre 2026 : la partie codée du brouillon
`refonte-modules.md` a été reportée ici le 2026-11-14.*

---

## 4. Modules

Le vaisseau démarre avec un **module principal** et en récupère d'autres au fil de l'avancée.
Chaque module a ses propres cartes (une carte peut être commune à plusieurs modules). **C'est la
carte qui dit à quels modules elle appartient** : champ `modules` de `config/cartes.json` (ex.
`"modules": ["MOD_2"]`) ; `config/modules.json` ne liste plus ses cartes (décision utilisateur,
2026-11-15, `specs/outil-editeur-cartes.md` §10).

**Données** : `config/modules.json` (source de vérité), tableau lisible **généré**
`config/modules.md` (`python -m outils.tableau_modules`). **Deux modules jouables** pour l'instant
(décision utilisateur, 2026-11-07) : le **Principal** (60 PV, 11 cartes) et le **Lanceur de
missiles** (20 PV, 8 cartes). Le choix de module du Niveau 1 ne propose donc que le Lanceur. Les
autres modules (Blindage, Générateur, Soute, Sabotage, Canon lourd, Contrôle, Atelier, Radar)
restent des idées, décrites en §4.1 à §4.3, à reprendre un par un ; leurs anciennes données
(PV, description, cartes) sont gardées dans [archive-cartes-modules.md](archive-cartes-modules.md).

**Une seule classe `Module`** (décision utilisateur, 2026-11-08) réunit trois niveaux
d'information :

| Niveau | Contenu | Durée de vie |
|---|---|---|
| **Modèle** (le type de module) | id (`MOD_2`), nom, image, description, PV max de base, `principal`, `jouable` ; ses cartes, calculées à partir du champ `modules` des cartes (`charger_modules`) | lu dans le JSON, ne change jamais |
| **Exemplaire dans la partie** | identifiant d'exemplaire (`M1` pour le principal, puis `M2`, `M3`…), emplacement, PV max (améliorations comprises), palier de mise à jour, PV (principal seulement) | sauvegardé |
| **État en combat** | PV de combat, statuts (combat.md §3.5) | une **copie par combat** (`copie_pour_combat`), jamais sauvegardée |

- **Seuls les PV du principal persistent** d'un combat à l'autre ; un secondaire repart à ses PV
  max à chaque combat et peut donc être **sacrifié** (décision utilisateur ; combat.md §3.4).
- Le module de la partie n'est jamais modifié par un combat : un combat abandonné ne touche pas la
  partie. À la fin, seuls les PV du principal sont reportés (`reporter_combat`).
- Chaque module a une `description` (une phrase d'accroche), affichée au choix de module et dans
  l'écran Vaisseau (parcours.md §2.4).
- **Doublons autorisés** : deux exemplaires du même type sont deux modules distincts, chacun avec
  son identifiant et ses cartes.

### 4.1 Modules d'attaque (spécialisés, pas un seul module générique)

**Canon lourd** — mono-cible, gros dégâts. Fort contre les L, faible contre les essaims de S.
- Tir de précision (1⚡, 8 dégâts)
- Charge concentrée (2⚡, 14 dégâts)
- Tir perforant (2⚡, 10 dégâts, avant + arrière de la colonne)
- Tir de rupture (3⚡, 20 dégâts, ne peut pas retirer au tour suivant) — ex-« Surcharge », renommée : le mot désigne désormais un statut (effets-a-coder.md §1)

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

- Début de run : module principal + 1 module, choisi au Niveau 1 (parcours.md §2.3).
- Quatre emplacements autour du principal : avant gauche, avant droite, arrière gauche, arrière
  droite (combat.md §3.1). La Station service peut **déplacer** un module (parcours.md §2.2) ; ses
  cartes le suivent (§12.4).
- **Plafond proposé : 5 modules** (principal inclus), valeur provisoire. Le rythme de déblocage
  des emplacements (idée d'origine : +1 à chaque victoire de boss) n'est pas codé : le run
  s'arrête au niveau 10.
- **Doublons autorisés** (décision utilisateur) : détail du tirage en parcours.md §2.3.
- Un module marqué `"jouable": false` ou sans carte n'est **jamais proposé**
  (`parcours.modules_equipables`).

---

## 6. Progression des modules / cartes

- **Après un combat gagné**, le joueur gagne une carte (parcours.md §2.1) : **une candidate par
  module équipé** (principal compris), tirée dans les cartes de ce module ; le joueur en choisit
  une, ou **passe**. La carte choisie est **rattachée au module qui l'a proposée** (§12.4)
  (`parcours.tirer_candidats_recompense`).
  - Rareté de chaque tirage (§7.3) : **5 % Légendaire, 20 % Rare, sinon Commune** (décision
    utilisateur). Les cartes **Base** ne sont jamais proposées. Si le module n'a aucune carte au
    palier tiré, on redescend au palier inférieur.
  - **Palier de mise à jour** du module (Station service, parcours.md §2.2 ; décision utilisateur,
    appliquée le 2026-11-13) : palier 1 = Communes seulement, palier 2 = + Rares, palier 3 = +
    Légendaires (`parcours.RARETES_PAR_NIVEAU_MAJ`).
  - Un module détruit pendant le combat propose quand même sa candidate.
- **Après le choix de module** (Niveau 1) : jusqu'à 3 cartes distinctes du nouveau module sont
  proposées, le joueur en prend une ou passe.
- **Bouton Passer** (décision utilisateur) : le joueur n'est jamais obligé de prendre une carte.
- **Écran « deck en entier »** : toutes les cartes possédées, regroupées par carte **et par
  module** (badge ×N), avec le module de chaque carte ; pendant un combat, toutes les cartes du
  combat, toutes piles confondues. PC : `src/ui/ecran_deck.py` ; web : `afficherDeck`.
- **Texte d'une carte** : partout (main, récompenses, deck, Aventures), c'est la `description` de
  `config/cartes.json` avec ses valeurs actuelles (`Carte.description_affichee`), jamais un texte
  recomposé par l'affichage.
- **Planète commerciale** (parcours.md §2.2) : achat de cartes, pas encore codé.

---

## 7. Types de cartes

### 7.1 Catégories (par effet)

`CategorieCarte` (noms sans accent dans le code et le JSON) :

| Catégorie | Description | Cartes actuelles |
|---|---|---|
| **Attaque** | Inflige des dégâts, directs ou dans la durée (incendie) | Laser, Missiles, Tir incendiaire… |
| **Defense** | Protège un ou plusieurs modules | Bouclier, Protéger le vaisseau, Blindage ciblé, Leurre |
| **Reparation** | Rend des PV à un module | Réparation |
| **Buff** | Renforce le vaisseau ou ses cartes | Salve laser, Protocole d'urgence, Bouclier stabilisé |
| **Debuff** | Affaiblit un ennemi | aucune (Vulnérabilité, Réduction de dégâts : non codées) |
| **Outils** | Pioche, électricité | aucune pour l'instant |
| **Controle** | Neutralise un ennemi (stun…) | aucune, rien de codé |

La catégorie sert aussi de filtre aux effets de répétition (§12.5).

### 7.2 Cible

Axe indépendant de la catégorie. Les neuf cibles (`CibleCarte`) et ce que chacune touche sont
décrits en combat.md §3.8.2 : Ennemi Unique, Colonne, Avant, Arrière, Tous ; Module Unique,
Principal, Avant, Tous. **Toutes** demandent un clic de confirmation sur une case valide, même
quand la case ne change rien à l'effet (interface.md §8.3).

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

Axe indépendant de la catégorie, de la cible et de la rareté : une carte a, en plus de son coût,
des munitions **illimitées** (par défaut) ou un nombre fixe qui se consomme pendant le combat et
revient au combat suivant. Fonctionnement : combat.md §3.6. Exemples : Réparation (2), Tir
incendiaire (3), Salve laser (2).

Sert à limiter des effets ponctuellement très forts sans les rendre répétables à volonté. Pas de
règle systématique entre rareté et munitions (a-trancher.md §9.1).

---

## 12. Modèle de carte et mécaniques

`src/gameplay/carte.py` (`Carte`), relu et validé par l'utilisateur le 2026-11-08. Données :
`config/cartes.json` (**source de vérité** : c'est là qu'on change une carte), tableau lisible
**généré** `config/cartes.md` (`python -m outils.tableau_cartes`). **19 cartes**, toutes jouables.
`Carte` ne décrit que les cartes du joueur : les ennemis ont leur propre modèle (combat.md §13).

### 12.1 Format d'une carte

- Des **valeurs nommées** : `"valeurs": {"degats_cible": 15, "degats_autres": 6}`.
- Une liste d'**effets** qui y renvoient par leur nom : `{"nature": "DEGATS", "valeur":
  "degats_cible"}`, avec une portée (§12.3), une durée nommée ou un filtre (§12.5) si besoin.
- Une **description** qui cite les valeurs entre accolades (« Inflige {degats_cible} dégâts… »),
  remplie par `Carte.description_affichee`.
- `cout`, `rarete`, `categorie`, `cible`, `munitions`, `lancements`, `persistante`, `refonte`
  (booléen : carte revue).
- `modules` : liste des types de module qui proposent la carte (ex. `["MOD_1"]`) ; une carte sans
  module n'est proposée nulle part, un module inconnu est refusé au chargement.
- `jouable` : **trois valeurs** (décision utilisateur, 2026-11-15) : `"oui"` (proposée et jouée),
  `"non"` (pas proposée), `"supprimee"` (retirée du jeu sans être effacée du fichier, traitée
  comme `"non"`). L'ancien format booléen est refusé.
- **Au chargement** : tout nom cité doit exister, toute valeur doit servir, et **toute clé
  inconnue est refusée** (coquilles détectées).
- Chaque **exemplaire** a ses propres valeurs (`valeurs`, et `valeurs_actuelles` en combat), base
  de futurs bonus du type « +2 aux dégâts des cartes à cible unique ».
- Textes affichés accentués (consigne utilisateur) ; identifiants et clés sans accent.

### 12.2 Natures d'effet (`NatureEffet`)

| Nature | Effet | État |
|---|---|---|
| `DEGATS` | Attaque de la valeur sur chaque ennemi touché | codé |
| `BOUCLIER` | Pose le statut Bouclier | codé |
| `REPARATION` | Rend des PV, sans dépasser le PV max | codé |
| `INCENDIE` | Pose le statut Incendie (le « poison » du jeu) | codé |
| `ANNULATION_PROCHAINE_ATTAQUE` | Pose le statut Leurre | codé |
| `GAIN_ELECTRICITE` | Électricité en plus pour ce tour | codé, aucune carte |
| `PIOCHE` | Pioche en plus | codé, aucune carte |
| `REPETITION` | Les cartes désignées sont lancées N fois de plus (§12.5) | codé |
| `SURCHARGE` | Pose le statut Surcharge sur le principal : +intensité aux dégâts de chaque coup des cartes, −1 par tour | **décidé le 2026-11-16, non codé** (effets-a-coder.md §1) ; *Lasers en surchauffe* non jouable en attendant |
| `VULNERABILITE`, `REDUCTION_DEGATS`, `REDIRECTION_CIBLE` | Statuts à durée, Tir allié | **non codé** : une carte qui en porte n'est pas jouable |

Règles des statuts : combat.md §3.5. Résolution d'une carte : combat.md §3.8. Le **renvoi** n'est
pas une nature de carte : seul l'ennemi Miroir le pose (la carte *Renvoi* du Blindage sera revue
avec son module).

### 12.3 Portée d'un effet (`PorteeEffet`)

Par rapport à la cible de la carte : `CIBLE` (la cible, ou tout l'ensemble visé),
`AUTRES_ENNEMIS` (Missiles : X sur la cible, Y sur les autres), `COLONNE_AVANT_ENNEMIE` et
`COLONNE_ARRIERE_ENNEMIE` (Torpille : X à l'avant, Y à l'arrière). C'est ce qui permet deux
valeurs sur une même carte.

### 12.4 Rattachement à un module et mot-clé Persistante

**Chaque carte du deck est rattachée à un exemplaire de module** (décision utilisateur,
2026-11-08) : le deck sauvegardé est une liste de couples `{"id": "CRT_9", "module": "M2"}`
(`partie.CartePossedee`, `Carte.exemplaire_module`).

- Un **identifiant d'exemplaire** plutôt que l'emplacement : la Station service déplace les
  modules, les cartes suivent sans rien faire.
- **Si le module est détruit en combat, ses cartes partent en pile Hors service** (combat.md
  §3.4) : c'est ce qui donne un coût à la perte d'un module. Les dégâts renvoyés par un ennemi
  vont au module de la carte jouée (combat.md §3.8.5).

| Origine de la carte | Module de rattachement |
|---|---|
| Deck de départ | le principal |
| Carte choisie après le choix de module | le module qui vient d'être équipé |
| Récompense de combat | le module qui a proposé la carte |
| Aventure, Planète commerciale | **le principal pour l'instant** (décision utilisateur, 2026-11-11) ; question ouverte, a-trancher.md §9.1 |

**Persistante** (`"persistante": true`) : la carte reste jouable même si son module est détruit.
Réservée à quelques cartes Rares ou Légendaires, **0 ou 1 par module** (validé), sinon la perte
d'un module ne coûte plus rien. Aucune carte ne le porte encore. Affichée par un bandeau sur la
carte.

- **Candidates naturelles** : des cartes dont le thème survit au module, par exemple *Leurre* (un
  leurre déjà largué), et les **cartes de résurrection**, qui doivent pouvoir ressusciter leur
  propre module. **Sans Persistante, une carte de résurrection d'un module mort serait elle-même
  hors service : à proscrire** (contrainte de conception, refonte-destruction.md §5).

### 12.5 Lancements et répétition

- Une carte est lancée `lancements_base` fois (1 par défaut) : coût payé une fois, tous les effets
  appliqués à chaque lancement (combat.md §3.8.3).
- Un effet `REPETITION` **augmente les lancements** des cartes que désigne son **filtre**, dans
  toutes les piles, **jusqu'à la fin du combat**, et se cumule (décision utilisateur). Le filtre
  désigne une carte par son **id** (`{"id": "CRT_7"}`, jamais par son nom), ou un ensemble par
  rareté ou catégorie.
- Cartes : *Salve laser* (les Laser), *Protocole d'urgence* (les cartes Base), *Bouclier
  stabilisé* (les Bouclier de base).

### 12.6 Mécaniques envisagées, non codées

Idées des anciennes cartes, à reprendre avec les modules concernés. **Les 44 cartes de l'ancien
moteur** (dont 25 qui n'existent plus dans le jeu : Mode défensif, Transfert, Renvoi, Tir allié,
Boost, Cannibalisme…), avec leurs dernières valeurs, sont dans
[archive-cartes-modules.md](archive-cartes-modules.md) ; leur première version, dans
`specs/cartes_legacy.xlsx` (archivé). Mécaniques correspondantes :

- **Statuts à durée** : Vulnérabilité (% de dégâts subis en plus), Réduction de dégâts, Tir allié
  (un ennemi attaque un de ses alliés) ; réflexion dans
  [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md).
- **Effet à la destruction, résurrection, sacrifice** :
  [refonte-destruction.md](refonte-destruction.md).
- **Bouclier en % des PV max**, transfert des dégâts vers un autre module, renvoi posé par une
  carte.
- **Méta-effets** : changer le coût de toutes les cartes d'une catégorie.
- **Électricité** : gain par module vivant, gain en échange d'une défausse.
- **Pioche / défausse** : piocher puis défausser, tout défausser puis repiocher, défausser une
  quantité choisie (demande un sous-choix au moment de jouer), pioche bonus pendant plusieurs
  tours.
- **Contrôle** : stun, restriction d'action.
