# Space Fight

*Deckbuilder roguelike (vaisseaux spatiaux) — Document de conception — v0.1*

---

## 1. Pitch

Un deckbuilder roguelike inspiré de Slay the Spire, où le joueur incarne un vaisseau spatial composé de **modules**. Chaque module possède son propre deck de compétences. Contrairement à Slay the Spire, il n'y a pas de héros unique ni de carte de monde classique : le joueur avance à travers une série de choix à chaque tour, en gérant la survie et la progression de son vaisseau.

---

## 2. Boucle de jeu (structure de run)

- Pas de carte de progression classique : à chaque étape, le joueur ne voit que **la prochaine étape** (aucune visibilité au-delà)
- Après chaque combat gagné, phase de récompenses (§2.1) puis le joueur choisit la prochaine étape parmi celles proposées
- Structure précise par niveau numéroté (1, 2, 3...) : voir §2.3 — logique d'apparition de la Station
  service, cadence des Boss et probabilités des étapes désormais tranchées
- Types d'étapes possibles :
  - **PRIME** — combat, contrat de chasseur de primes. Affiche un niveau de difficulté / la composition annoncée des ennemis (tailles S/M/L, cf. 3.2) sans révéler le détail exact
  - **STATION SERVICE** (le "garage") — entretien du vaisseau contre de l'Argent : réparer, améliorer ou déplacer un module (détail en §2.2)
  - **PLANÈTE COMMERCIALE** (le "marché") — achat de cartes contre de l'Argent ; la disponibilité des cartes Rares/Légendaires pour un module dépend de son niveau d'amélioration (voir §2.2 et §6)
  - **AVENTURE** — événement inconnu, façon "?" de Slay the Spire. Contenu entièrement à définir (§9.1)
  - **CHOIX DE MODULE** — niveau 1 uniquement (§2.3) : 3 modules différents tirés au sort, le joueur en choisit un
  - *(autres types d'étapes à imaginer)*
- **Boss** : niveau 10, puis tous les 10 niveaux (20, 30, 40...) — voir §2.3
  - Victoire sur un boss → le joueur choisit **1 nouveau module parmi 2 propositions**, avec ses cartes de base associées (deck de départ propre au module — détail à trancher une fois le système de cartes approfondi, voir §7)
  - **Le run s'arrête réellement au Niveau 10 dans l'état actuel** (décision utilisateur, provisoire,
    voir §2.4) : gagner le Boss du niveau 10 mène à un écran de victoire finale, le run ne continue
    pas au-delà pour l'instant — la récompense de Boss "1 module parmi 2" ci-dessus reste donc hors
    champ tant que cette limite n'est pas repoussée (niveaux 20, 30..., voir §9.1)

### 2.1 Argent et récompenses de combat

- Après chaque combat gagné, le joueur gagne de l'**Argent** — nouvelle ressource de run, distincte de l'Électricité (ressource de combat, voir §3). Montant exact à définir (§9.1)
- Il gagne aussi une carte : voir §6 pour le mécanisme de choix (candidate par module équipé). **Récompense garantie** à chaque victoire (pas probabiliste) — écran de fin de combat implémenté, voir §6
- En cas de défaite, écran dédié avec message de défaite (pas de choix de carte) — implémenté, voir §6
- Le joueur choisit ensuite l'étape suivante parmi celles qui apparaissent (Prime, Station service, Planète commerciale ou Aventure) — l'offre n'est pas forcément la même à chaque fois (voir §9.1)

### 2.2 Station service (garage)

Quatre actions indépendantes, appliquées à un module choisi par le joueur (voir écran ci-dessous) :

- **Réparer** : restaure 20 PV au module sélectionné (plafonné à son pv_max)
- **Améliorer** : augmente le pv_max du module sélectionné de 10, et ses PV actuels du même montant
  (pas seulement le plafond — un module endommagé regagne aussi 10 PV immédiats)
- **Mettre à jour** : fait progresser le palier de cartes proposées pour ce module, en récompense de
  combat (§6) et à la Planète commerciale (§2.2 ci-dessus) :
  **Niveau 1** (valeur de départ, Commune uniquement) → **Niveau 2** (+Rare) → **Niveau 3** (+Légendaire,
  niveau maximum, cohérent avec les 3 paliers de rareté de §7.3)
- **Déplacer** : change la position d'un module sur la grille d'équipement (§3.1/§5). Le joueur
  sélectionne le module à déplacer, clique "Déplacer", puis clique l'emplacement de destination :
  vide, le module y est simplement déplacé ; occupé, les deux modules échangent leur position

**Toutes les actions sont gratuites pour l'instant** (décision utilisateur, provisoire) : la ressource
Argent n'existe pas encore côté gameplay (§2.1/§9.1) — un coût en Argent sera réintroduit sur ces 4
actions une fois cette ressource implémentée.

- Réparer/Améliorer/Mettre à jour s'appliquent au **module principal** comme aux modules équipés.
  Déplacer ne s'applique pas au principal (toujours en position Mid, pas d'emplacement équivalent à
  échanger)
- Améliorer/Mettre à jour progressent **par exemplaire équipé**, pas par type de module : deux
  exemplaires du même module peuvent avoir des PV max et des paliers de mise à jour différents —
  cohérent avec les doublons de modules autorisés (§2.3/§5)
- **Les dégâts subis en combat persistent d'un combat à l'autre** (décision utilisateur — sinon
  Réparer n'aurait aucune utilité) : un module endommagé le reste au niveau suivant tant qu'il n'a
  pas été réparé. Format et couche de persistance hors-combat **implémentés** en §10.3 (`EtatModule`
  dans `src/gameplay/partie.py` : PV actuels, PV max, niveau de mise à jour, par module équipé),
  réutilisés directement par les 4 actions ci-dessus (`reparer_module`/`ameliorer_module`/
  `mettre_a_jour_module`/`deplacer_module`, fonctions pures partagées PC+web)

#### Écran Station service (interface) — **implémenté**, relié à l'orchestration du parcours (§2.4)

- Fond de combat réutilisé en placeholder (comme les autres écrans du parcours), à remplacer par un
  fond dédié
- Modules du vaisseau affichés en **ligne de 5 cartes** (principal + 4 équipables, une carte "Emplacement
  vide" pour un slot non équipé) plutôt que dans la grille 2×2 façon combat envisagée initialement —
  décision d'implémentation, reprend le layout déjà existant de l'écran d'accueil du joueur
  (`POSITIONS_AFFICHEES`, §10.3) : le joueur clique une carte de module équipé pour la sélectionner
  (contour en surbrillance), puis clique une des 4 actions pour l'appliquer au module sélectionné.
  **Déplacer** : cliquer "Déplacer" arme le mode (icône encadrée en orange) en attendant un clic sur
  l'emplacement de destination (vide ou occupé) parmi les 4 équipables ; recliquer le module source
  annule l'armement. Un bouton "J'ai terminé" ferme l'écran → Choix du prochain niveau (étape 3),
  avec avancement du niveau (comme une étape résolue, §2.4)
- Icônes des 4 actions dans `assets/station_service/` (`reparer.png`, `ameliorer.png`,
  `mettre_a_jour.png`, `deplacer.png`) : déjà pourvues de leur propre cadre/nom incrusté (fournies
  par l'utilisateur, même principe que `assets/prochain_niveau/`), affichées seules sans étiquette de
  texte supplémentaire à côté
- La carte du module principal utilise `assets/modules/principal_avant.png` (recadrage sur l'avant
  du vaisseau, décision utilisateur) plutôt que l'image complète du vaisseau (`config/modules.json`,
  utilisée telle quelle comme fond du vaisseau en combat) — sinon hors d'échelle par rapport aux
  cases des autres modules. `src/gameplay/donnees.py:image_case_module()`, réutilisée par l'écran
  d'accueil du joueur (§10.3) pour la même raison
- `src/gameplay/partie.py` (`reparer_module`, `ameliorer_module`, `mettre_a_jour_module`,
  `deplacer_module`, fonctions pures partagées PC+web) ; `src/ui/ecran_station_service.py` (PC) ;
  `main.py:_ouvrir_station_service` (PC) ; côté web `web/bridge.py` (`reparer_module_web`/
  `ameliorer_module_web`/`mettre_a_jour_module_web`/`deplacer_module_web`/
  `terminer_station_service_web`) + `web/app.js` (`ouvrirStationServicePartie` et les fonctions
  `cliquerModuleStation`/`cliquerActionStation`/`terminerStationServicePartie`)

### 2.3 Structure par niveaux

Le run est une suite de **niveaux numérotés** (1, 2, 3...), chacun une étape. Décision utilisateur,
remplace les pistes encore ouvertes en §2 pour la Station service et la cadence des Boss :

- **Niveau 1** — **Choix de module**, obligatoire, pas de tirage d'étape : 3 modules **différents**
  tirés au sort parmi le pool, le joueur en choisit un (2ᵉ slot équipé, en plus du module de base —
  voir §5). C'est ce choix qui pourvoit le 2ᵉ des "2 slots" de départ mentionnés en §5.
  **Implémenté** et relié à l'orchestration du parcours (§2.4) pour une vraie partie :
  `src/gameplay/parcours.py` (tirage), `src/ui/ecran_choix_module.py` (PC),
  `main.py:_ouvrir_choix_module` (equipe le module choisi, avance le niveau, sauvegarde) ;
  côté web `web/bridge.py:choisir_module_partie_web` + `web/app.js:ouvrirChoixModulePartie`/
  `choisirModule`. Reste aussi accessible en démonstration isolée (candidats tirés indépendamment
  d'une partie) via `web/app.js` (`nouveauChoixModule`, exposée sur `window`) + `web/bridge.py`
  (`nouveau_choix_module`), utilisée quand `partieActive` est `null`. Chaque module a désormais un champ
  `description` dans `config/modules.json` (type de carte débloqué, sans révéler les cartes) —
  fond de combat réutilisé en placeholder (décision utilisateur), à remplacer par un fond dédié
- **Niveaux 5 et 9** — 3 propositions dont une **Station service garantie** (les 2 autres tirées
  normalement, voir ci-dessous) — le joueur garde le choix, la Station service n'est pas forcée
- **Niveau 10** — **Boss**, obligatoire, pas de tirage d'étape. Se répète tous les 10 niveaux (20,
  30, 40...) — remplace la valeur indicative "8-10" précédemment envisagée en §2
- **Tous les autres niveaux** (2-4, 6-8, 11-14, 16-19...) — **3 propositions**, chaque slot tiré
  **indépendamment** des deux autres (donc parfois 2 ou 3 propositions identiques, ex. 3 Primes) :
  - 1/30 **Station service**
  - 1/30 **Planète commerciale**
  - 1/10 **Aventure**
  - Reste (5/6) **Prime** (combat)
- **Nombre d'ennemis en Prime** : 1 seul ennemi jusqu'au niveau 5, puis 2 à partir du niveau 6 —
  s'ajoute au système de tailles S/M/L existant (§3.2, deux axes de difficulté indépendants), ne le
  remplace pas. Progression au-delà de 2 (après le niveau 10 ?) pas encore définie
- **Doublons de modules autorisés** (remplace la piste "interdire les doublons" de §5) : posséder
  déjà des exemplaires d'un module **augmente son poids au tirage** lors d'un prochain choix de
  module (Niveau 1 ou récompense de Boss) — formule de pondération exacte à définir (§9.1)

**Points encore ouverts** (à confirmer avant implémentation, voir aussi §9.1) :
- Le motif niveaux 5/9 + Boss niveau 10 se répète-t-il identique à chaque décennie (15/19 + 20,
  25/29 + 30...), ou seule la première décennie a cette forme ?
- Le nombre d'ennemis en Prime continue-t-il à augmenter après le niveau 10 (Boss), ou reste-t-il
  bloqué à 2 ?
- La pondération par doublons déjà possédés s'applique-t-elle aussi au choix de module après un
  Boss (2 propositions, §2), ou seulement au Niveau 1 ?

### 2.4 Enchaînement des écrans (orchestration du parcours)

Vue d'ensemble de tous les écrans du jeu et de ce que chacun déclenche une fois son action
terminée — schéma fourni par l'utilisateur, normalisé ici en un seul endroit. Statut
d'implémentation entre parenthèses pour chaque écran ; le detail de chacun reste dans sa propre
section (référencée), cette liste ne fait que les enchaîner.

1. **Sélection du joueur** (implémenté, §10.3) — choisir un profil existant ou en créer un →
   Écran de partie (étape 2). Bouton "Quitter le jeu" (**PC uniquement** : ferme l'application ;
   pas d'équivalent fiable côté web, un onglet de navigateur ne peut pas se fermer par script dans
   le cas général — décision utilisateur, écart PC/web assumé comme les autres déjà documentés
   dans `CLAUDE.md`)
2. **Écran de partie** (implémenté, §10.3 — nommé `EcranAccueilJoueur`/`afficherAccueilJoueur` dans
   le code, "écran de partie" dans le vocabulaire de ce schéma) :
   - Une partie `EN_COURS` existe : Continuer / Abandonner / Voir le deck, vaisseau et ses modules
     affichés. **Continuer** → reprend l'étape exacte où le joueur s'était arrêté, déduite des
     seuls champs déjà présents dans la sauvegarde plutôt que d'une "étape courante" dédiée
     (décision utilisateur) : Niveau 1 sans 2ᵉ module équipé (`vaisseau.avant_gauche` vide) → Choix
     de module (étape 4) ; sinon → Choix du prochain niveau (étape 3) pour le niveau courant. La
     flotte ennemie d'un combat repris ainsi reste tirée au hasard (`combat_depuis_partie`, §10.3),
     cf. "Limites connues" en §10.3
   - Pas de partie en cours : bouton "Nouvelle partie" → Choix de module, Niveau 1 (étape 4)
   - Bouton "Quitter le jeu" (même remarque PC/web qu'à l'étape 1)
3. **Choix du prochain niveau** (**implémenté** et relié à l'enchaînement — tirage tranché en §2.3,
   `TypeEtape`/`tirer_propositions_niveau`/
   `est_niveau_boss`/`aleatoire_pour_niveau` dans `src/gameplay/parcours.py`) — à chaque niveau sauf
   le 1 (§2.3) : tire les propositions selon les probabilités et exceptions déjà définies en §2.3
   (1/30 Station service, 1/30 Planète commerciale, 1/10 Aventure, sinon Prime ; Station service
   garantie aux niveaux 5 et 9). **Aux niveaux Boss (10, puis multiples de 10), le même écran
   s'affiche mais avec une seule proposition forcée, `TypeEtape.BOSS`** (décision utilisateur : pas
   d'enchaînement automatique direct vers le combat, le joueur confirme explicitement via un unique
   bouton/carte "Combattre le Boss !") → l'écran correspondant à la proposition choisie (Prime →
   Combat, Station service → Station service, Planète commerciale → Planète commerciale, Aventure →
   Aventure, Boss → Combat de Boss, étape 10). Tirage déterministe via
   `aleatoire_pour_niveau(graine, niveau)` (seed textuelle `"{graine}:{niveau}"`, cohérent avec le
   principe déjà décrit en §10.3) — `est_niveau_boss` reste utile pour d'autres besoins (ex. décider
   quel ennemi affronter une fois au Combat), mais n'a plus besoin d'être vérifié par l'appelant
   avant d'afficher cet écran : `tirer_propositions_niveau` gère le cas Boss en interne.
   `src/ui/ecran_choix_niveau.py` (PC, jusqu'à 5 cartes possibles au total — layout généralisé pour
   accepter 1 ou 3 propositions — avec icône dédiée par type — `assets/prochain_niveau/`, images
   fournies par l'utilisateur, déjà leur propre cadre/nom incrusté — et description sous l'icône) ;
   `web/bridge.py` (`choix_niveau_web`), `web/app.js` (`choixNiveau`, exposée sur `window` pour test
   manuel)
4. **Choix de module, Niveau 1** (implémenté en écran autonome, §2.3, **relié à la partie**) : une
   fois un module choisi, met à jour la partie (2ᵉ emplacement du vaisseau) et son niveau (1 → 2),
   puis → Choix du prochain niveau (étape 3)
5. **Combat** (implémenté en écran indépendant, `FenetreCombat`/`#app`, **relié à l'enchaînement**) :
   une fois le combat terminé (victoire ou défaite) → Fin de combat (étape 6)
6. **Fin de combat** (implémenté en écran autonome, §6, **relié à l'enchaînement**) :
   - Victoire : choix d'une carte candidate (candidats tirés à partir des modules réellement
     équipés sur la partie, `specs_utilisees_partie`) met à jour le deck de la partie, puis → Choix
     du prochain niveau (étape 3), sauf si le combat était un Boss → Victoire finale (étape 11 ; le
     niveau n'avance pas encore et la partie reste `EN_COURS` à ce stade, cf. étape 11). S'il n'y a
     aucun candidat (pool vide pour tous les modules équipés), un bouton "Continuer" permet de
     passer l'écran sans choisir de carte
   - Défaite : la partie est marquée `TERMINEE` (même statut qu'un abandon, décision utilisateur —
     pas de distinction victoire/défaite/abandon pour l'instant, cf. §10.3) → Écran de partie
     (étape 2), via un bouton "Continuer" (PC : clic n'importe où sur l'écran, cf.
     `src/ui/ecran_fin_combat.py`)
7. **Aventure** (contenu non préparé, §2/§9.1, **relié à l'enchaînement via un écran générique**) :
   un bouton "j'ai terminé" avance le niveau et revient au Choix du prochain niveau (étape 3), même
   principe que Station service — en attendant un vrai contenu, l'écran se limite à afficher
   l'icône/description déjà utilisées au Choix du prochain niveau avec un message "Contenu pas
   encore défini pour cette étape." `src/ui/ecran_etape_placeholder.py` (PC, un seul écran
   générique pour cette étape et l'étape 9) + `main.py:_ouvrir_etape_placeholder` ; côté web
   `web/bridge.py` (`terminer_etape_placeholder_web`) + `web/app.js`
   (`ouvrirEtapePlaceholderPartie`/`terminerEtapePlaceholder`)
8. **Station service** (détaillé en §2.2, **implémenté et relié à l'enchaînement**) : Réparer /
   Améliorer / Mettre à jour / Déplacer un module, un bouton "j'ai terminé" avance le niveau et
   revient au Choix du prochain niveau (étape 3), même principe que la fin d'un combat gagné
9. **Planète commerciale** (contenu non préparé, §2/§9.1) : même principe qu'Aventure — même écran
   générique, même comportement (étape 7)
10. **Boss** (niveau 10, puis tous les 10 niveaux à terme — §2.3), atteint via la proposition
    unique "Combattre le Boss !" de l'étape 3 : réutilise l'écran Combat pour l'instant, pas encore
    d'ennemi de Boss dédié (§9.1) → Victoire : Victoire finale (étape 11) ; Défaite : même
    traitement qu'un combat normal (étape 6, branche Défaite)
11. **Victoire finale** (**implémenté et relié à l'enchaînement**) : félicite le joueur, affiche son
    deck complet (même rendu que l'écran "deck en entier", §6, dupliqué plutôt que réutilisé
    littéralement — même convention que les autres écrans du parcours, chacun avec ses propres
    petits helpers de disposition) → bouton "Continuer" marque la partie `TERMINEE` (elle était
    restée `EN_COURS` depuis la résolution de l'étape 6) → Écran de partie (étape 2).
    `src/ui/ecran_victoire_finale.py` (PC) + `main.py:_ouvrir_victoire_finale` ; côté web
    `web/bridge.py` (`terminer_victoire_finale_web`, `resoudre_victoire_partie_web` renvoie
    désormais `{"partie": ..., "niveau_boss": bool}` pour signaler à `web/app.js` quand ouvrir cet
    écran plutôt que d'avancer directement) + `web/app.js` (`ouvrirVictoireFinalePartie`,
    `terminerVictoireFinale`)

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
- **L** : prend 2 emplacements, gros PV, attaque de zone ou pattern en plusieurs temps

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

### 3.6 Munitions (cartes à usage limité)

Certaines cartes ont un nombre de munitions limité en plus de leur coût en électricité (cf. §7.4) :

- **Munitions illimitées** (cas par défaut, toutes les cartes actuelles du POC) : aucun changement, la carte se joue normalement, autant de fois que voulu tant que l'électricité suit
- **Munitions limitées à N** : chaque utilisation de la carte décrémente son compteur de munitions restantes. Le compteur est **propre à chaque exemplaire physique de la carte dans le deck** (si le deck contient 2 exemplaires d'une carte à 1 munition, chacun peut être joué une fois, soit 2 utilisations au total sur le combat)
- Quand le compteur d'un exemplaire tombe à **0**, cet exemplaire quitte définitivement le combat : au lieu de partir en défausse, il rejoint une nouvelle pile, les **cartes épuisées**, distincte de la pioche et de la défausse
- Les cartes épuisées ne reviennent **jamais** dans la pioche pendant le combat en cours, même si la pioche et la défausse sont toutes les deux vides (pas de mélange de secours) — cf. §9.1 pour le cas limite où cela viderait totalement les cartes piochables
- **Entre deux combats**, chaque carte à munitions limitées repart avec son nombre de munitions d'origine (le compteur ne persiste pas d'un combat à l'autre) — cohérent avec le fait que le deck de combat est reconstitué à chaque combat à partir des pools de cartes des modules équipés (§6)

---

## 4. Modules

Le vaisseau démarre avec un **module de base**, et en récupère d'autres au fil de l'avancée. Chaque module a son propre deck de cartes (certaines cartes communes entre modules).

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

---

## 6. Progression des modules / cartes

- Après un combat gagné, le joueur gagne une carte, garantie (voir §2.1). Mécanisme : **1 carte
  candidate par module équipé** (base incluse, au maximum 5 — §5), tirée dans le pool de cartes
  propre à ce module — le joueur choisit parmi ces N candidates, ce qui attribue implicitement la
  carte au module correspondant
  - Pour le **module principal** (module de base), sa candidate est tirée dans le **pool entier** de cartes (tous modules confondus)
  - Pour un **module secondaire**, sa candidate est tirée dans la **liste de cartes propre à ce module**
  - La rareté (voir 7.3) pondère chaque tirage individuel : **5% Légendaire, 20% Rare, sinon (75%)
    Commune** — décision utilisateur. **Les cartes Base ne sont jamais proposées en récompense**
    (deck de départ uniquement). Si le pool d'un module n'a aucune carte au palier tiré, on
    redescend au palier inférieur (Légendaire → Rare → Commune) plutôt que de ne rien proposer
  - Remplace l'ancien mécanisme "1 carte parmi 3 propositions pondérées par rareté, avec choix du module destinataire" : le choix du module destinataire se fait maintenant implicitement en choisissant la candidate
  - **Implémenté** en écran de fin de combat autonome (Victoire/Défaite), **relié à l'orchestration
    du parcours** (§2.4) pour une vraie partie : `src/gameplay/parcours.py`
    (`tirer_candidats_recompense` et les fonctions de tirage par palier), `src/ui/ecran_fin_combat.py`
    (PC), `main.py:_ouvrir_fin_combat` ; côté web `web/bridge.py:candidats_recompense_partie_web`/
    `resoudre_victoire_partie_web` + `web/app.js:terminerCombatPartie`/`choisirRecompense`. Reste
    aussi accessible en démonstration isolée (candidats tirés depuis un vaisseau tiré au sort plutôt
    qu'une vraie partie) via `web/app.js` (`nouvelleVictoire`/`nouvelleDefaite`, exposées sur
    `window`) + `web/bridge.py` (`fin_combat_victoire`), utilisée quand `partieActive` est `null`.
    Défaite : titre rouge "DEFAITE" + message
    "Pas d'inquietude : vos restes seront recycles, rien ne se perd dans l'espace." (fond de
    combat réutilisé en placeholder, décision utilisateur, à remplacer par un fond dédié)
  - Chaque carte candidate affiche son coût en électricité sous forme d'emoji (⚡N, plutôt qu'un
    texte "Coût N") et sa description d'effet en toutes lettres, générée depuis ses données
    (type/cible/action/valeur/durée) : `texte_effet_carte()` dans `src/ui/fenetre.py` côté PC
    (réutilisable par d'autres écrans, notamment le futur écran de deck complet, §6 plus bas),
    `texteEffetCarte()` déjà existant dans `web/app.js` côté web (réutilisé tel quel, `bridge.py`
    enrichi des champs `type`/`cible`/`action`/`duree`/`valeur` par candidate)
- **Écran "deck en entier"** : consultable depuis plusieurs endroits du parcours (pour l'instant
  uniquement depuis l'Écran de partie via "Voir le deck", §10.3 — pas encore depuis les autres
  écrans du parcours) — grille de toutes les cartes actuellement possédées par le joueur, regroupées par modèle (une
  entrée par carte différente, avec un badge ×N si plusieurs exemplaires) plutôt qu'une case par
  exemplaire individuel
  - `Deck.toutes_cartes()` (`src/gameplay/deck.py`) réunit pioche + main + défausse + cartes
    épuisées ; `regrouper_cartes()` (`src/gameplay/carte.py`) transforme une liste de cartes en
    `(carte, quantité)` par modèle — fonctions gameplay partagées par les deux plateformes
  - **Implémenté** en écran autonome (même situation que les deux écrans précédents, pas encore
    relié à un vrai bouton dans l'UI) : `src/ui/ecran_deck.py` (PC, grille figée de 8 colonnes,
    survol d'une carte → panneau de description fixe en bas d'écran plutôt qu'une infobulle
    ancrée sur la carte, pour éviter tout chevauchement avec la ligne voisine dans une grille
    dense) ; `web/bridge.py` (`etat_deck`, cartes du combat en cours si actif sinon un deck de
    démonstration tiré au sort) + `web/app.js` (`voirDeck`, exposée sur `window` — pas
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
| **Ligne ennemie** | Cas particulier d'"ennemis multiples" pour les cartes perçantes (§3.1) : touche l'avant et l'arrière de la rangée de la cible cliquée (2 ennemis au plus), cf. poc.md §4 |

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

## 8. Interface / écran de combat

### 8.1 Disposition générale (wireframe)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SPACE FIGHT — ÉCRAN DE COMBAT                                  ⚡ Électricité: 5 │
│                                                                                    │
│  VAISSEAU DU JOUEUR                                FLOTTE ENNEMIE (6 emplacements)│
│  (fond commun aux 5 emplacements)                                                 │
│                                                                                    │
│   Arrière          Avant                            Avant           Arrière      │
│  (loin ennemi)   (face ennemi) →→              ←← (face joueur)   (loin joueur)   │
│  ┌──────┐        ┌──────┐                       ┌──────┐          ┌──────┐        │
│  │  AG  │        │  FG  │                       │  E   │          │  E   │        │
│  └──────┘        └──────┘                       └──────┘          └──────┘        │
│  ┌────────────────────┐                         ┌──────┐          ┌──────┐        │
│  │        BASE         │                         │  E   │          │  E   │        │
│  └────────────────────┘                         └──────┘          └──────┘        │
│  ┌──────┐        ┌──────┐                       ┌──────┐          ┌──────┐        │
│  │  AD  │        │  FD  │                       │  E   │          │  E   │        │
│  └──────┘        └──────┘                       └──────┘          └──────┘        │
│                                                                                    │
│                                                     ┌─────────┐ ┌─────────┐        │
│                                                     │ Pioche  │ │Défausse │        │
│                                                     │  (24)   │ │  (5)    │        │
│                                                     └─────────┘ └─────────┘        │
│         ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                        │
│         │ Carte │ │ Carte │ │ Carte │ │ Carte │ │ Carte │  ← main, alignée        │
│         │  1⚡   │ │  2⚡   │ │  1⚡   │ │  0⚡   │ │  3⚡   │   (pas en éventail)     │
│         └───────┘ └───────┘ └───────┘ └───────┘ └───────┘                        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

- **Vaisseau du joueur** (haut gauche) : grille de **2 colonnes (arrière/avant) x 3 rangées (gauche/mid/droite)**. La colonne **avant est tournée vers l'ennemi** (la plus proche du centre de l'écran), la colonne arrière est la plus éloignée. Le tout repose sur un **fond commun** qui regroupe visuellement les 5 emplacements. Le **module de base** occupe la rangée mid en entier (arrière-mid + avant-mid fusionnés) ; les 4 autres modules équipés prennent FG/FD/AG/AD
- **Flotte ennemie** (haut droite) : grille symétrique 2x3, 6 emplacements libres (pas de base adverse). La colonne **avant est tournée vers le joueur** (la plus proche du centre de l'écran) et c'est elle qui est exposée au corps à corps (voir 3.1) ; la colonne arrière est la plus éloignée
- **Compteur d'électricité** restante affiché en haut de l'écran
- **Main de cartes** : alignée en bas de l'écran (pas en éventail, pour la lisibilité)
- **Pioche, défausse et cartes épuisées** (§3.6) : regroupées ensemble dans un coin de l'écran (compteurs de nombre de cartes), séparées de la main

### 8.2 Formes visuelles

- **Modules du joueur et ennemis** : images **carrées**
- **Module de base** : exception, forme différente (plus grande, fond dédié qui englobe les 5 emplacements)
- **Cartes** : format **rectangulaire**
- **PV / Bouclier** : affichés par de petites pastilles rondes (rouge pour les PV, bleue pour le Bouclier) flottant juste au-dessus de chaque case, jamais superposées à l'image (validé en POC, voir poc.md §8)
- **Munitions restantes** (§3.6) : affichées sur la carte comme le coût en électricité, dans une pastille ronde **verte** — uniquement pour les cartes à munitions limitées (rien affiché pour les munitions illimitées, comportement par défaut)

### 8.3 Interaction de jeu d'une carte

**Le jeu se joue entièrement à la souris.**

1. Clic sur une carte de la main → la carte se **surligne** (état "armée")
2. Clic sur une **cible valide** → la carte se résout, part en défausse, la surbrillance disparaît
3. Pour les cartes sans cible unique (Alliés multiples, Ennemis multiples, Module principal, effet
   sur tout un camp) : la cible précise du clic ne compte pas pour l'effet, mais **un clic de
   confirmation reste nécessaire** sur n'importe quelle case vivante du bon camp (allié ou ennemi) —
   pas de résolution automatique au seul clic sur la carte, pour éviter qu'un clic accidentel ne la
   joue (validé dans le POC, voir poc.md §4). **Ce flux de clic/tap doit rester identique entre la
   version PC et la version web/iOS** (cf. CLAUDE.md, "Deux façons de jouer")
4. **Fin de tour** : un bouton cliquable "Fin de tour" permet au joueur de terminer son tour à tout moment, même s'il lui reste de l'électricité ou des cartes jouables
5. **Retour visuel des effets** : chaque effet résolu (carte jouée ou attaque ennemie) affiche un popup `+N`/`-N` pendant quelques secondes sur la ou les cases touchées, avec le montant **réellement appliqué** (plafonné par les PV+Bouclier restants pour les dégâts, par le PV max pour le soin) plutôt que la valeur nominale de la carte — validé en POC, voir poc.md §8

---

## 9. Points encore à trancher

### 9.1 Design / gameplay

- Contenu exact de la Planète commerciale (uniquement des cartes, ou aussi d'autres bonus ?) et de l'Aventure (entièrement à définir, voir §2)
- Montants exacts d'Argent : récompense de combat (§2.1) ; coût des 4 actions de Station service —
  **temporairement gratuites** le temps que la ressource Argent soit implémentée (§2.2)
- La Planète commerciale propose-t-elle des cartes pour tous les modules du pool, ou seulement pour les modules actuellement équipés ? (§2, §6)
- **Persistance des modules hors combat/profils joueur** (§2.2/§10.3) : **implémentée** (profil +
  partie, un seul joueur à la fois, écrans de sélection de profil/accueil du joueur, `main.py` en
  vrai point d'entrée), et l'orchestration du parcours (§2.4) relie désormais Choix de module, Choix
  du prochain niveau, Combat, Fin de combat et Station service à cette sauvegarde. Reste bloquant
  pour relier Planète commerciale/Aventure (contenu non préparé) à un vrai parcours — voir §10.3
  "Limites connues" pour le détail restant (portée limitée aux points de passage entre étapes,
  flotte ennemie toujours tirée au hasard sans tenir compte du niveau)
- Statistiques et déblocages par profil (parties jouées/victoires/défaites, niveau max, module le
  plus choisi, déblocages en fin de partie) : sciemment pas encore implémentés (§10.3, décision
  utilisateur "pas de stat pour le moment") — à faire dans une passe dédiée
- **Condition de victoire d'une partie** (§10.3) : la structure par niveaux actuelle (§2.3) enchaîne
  les Boss indéfiniment tous les 10 niveaux, sans fin de run définie — bloquant pour une future
  statistique `victoires` (dernier Boss d'une liste finie ? Palier de niveau à atteindre ? Le run
  est-il pensé comme sans fin, façon high-score, auquel cas `victoires` n'aurait peut-être pas de
  sens ?)
- Améliorer (Station service, §2.2) : y a-t-il un plafond de PV max, ou est-ce répétable indéfiniment ?
- Filtrage du pool de récompense par palier de mise à jour débloqué (§2.2/§6) : à réconcilier avec le
  mécanisme de repli au palier inférieur déjà implémenté dans `tirer_carte_recompense`, qui suppose
  aujourd'hui que tout le pool d'un module est accessible
- Cartes de base fournies avec un nouveau module choisi après un Boss : deck de départ fixe par module, à définir une fois le système de cartes approfondi (voir §7)
- Plafond exact de slots équipables (proposition actuelle : 5, base incluse) — voir aussi §2.3 pour les points encore ouverts sur la structure par niveaux (répétition du motif 5/9/10 par décennie, progression du nombre d'ennemis, pondération des doublons hors Niveau 1)
- Formule exacte de pondération des doublons de modules au tirage (§2.3, §5) : plus un exemplaire supplémentaire compte-t-il, linéaire ou autre ?
- Représentation visuelle d'un ennemi L occupant 2 emplacements (§3.2, §8.1) : rectangle fusionné sur les 2 cases, ou deux images liées logiquement ?
- Compléter le jeu de cartes de chaque module : les archétypes de §4.3 (Bouclier énergétique, Radar, Propulseur, IA de combat, Générateur, Sabotage, Soute/Fret) n'ont pas encore de decks détaillés comme ceux de §4.1-4.2 ; les cartes déjà écrites en §4.1-4.2 n'ont pas encore de type/cible/rareté assignés (§7)
- Munitions (§3.6/§7.4) : cas limite si la pioche et la défausse sont toutes les deux vides en cours de combat alors qu'il reste des cartes épuisées (qui ne sont jamais remélangées) — le joueur peut alors se retrouver sans carte à piocher ; à surveiller en playtest une fois des cartes à munitions limitées réellement jouables (voir §9.2 pour l'état d'implémentation actuel)
- Munitions (§7.4) : pas de règle systématique reliant rareté et munitions pour l'instant (une carte de n'importe quel palier peut avoir des munitions limitées ou non) — à revisiter si un pattern se dégage en concevant plus de cartes

### 9.2 Technique / développement

*(voir §10 pour les choix techniques déjà tranchés)*

- Munitions (§3.6/§7.4) : mécanique pas encore implémentée dans `src/gameplay/` — les cartes du
  tableau de conception qui en ont une (ex : Réparation, Bouclier perpétuel) sont pour l'instant
  stockées dans `config/cartes.json` sans bloc "effet" (non jouables), voir la PR "config : import
  des cartes Module principal, Lanceur de missiles, Blindage"

---

## 10. Architecture technique

### 10.1 Stack

- **Langage** : Python 3.11+
- **Affichage PC** : pyglet
- **Affichage web/iPhone** : HTML/CSS/JS + [Pyodide](https://pyodide.org/) (exécute `src/gameplay/`
  tel quel dans le navigateur, sans le modifier) — voir README.md. Les deux façons de jouer doivent
  rester fonctionnelles en permanence (voir CLAUDE.md)
- **Tests** : pytest
- **Dépendances / packaging** : `pyproject.toml`

### 10.2 Arborescence du dépôt

```
assets/
  cartes/      → images des cartes
  modules/     → images des modules
  ennemis/     → images des ennemis
config/        → fichiers de donnees JSON (modules, ennemis, cartes)
src/
  ui/          → tout ce qui concerne l'affichage avec pyglet (PC)
  gameplay/    → logique de jeu, partagee par les deux facons de jouer
index.html, web/ → affichage web/iPhone (Pyodide), voir README.md
saves/         → sauvegardes de partie (PC uniquement, §10.3), ignore par git
tests/
pyproject.toml
```

- `assets/` : uniquement des images pour le moment ; le son sera ajouté plus tard si besoin
- `config/` : contenu du jeu décrit en JSON (modules, ennemis, cartes), référençant les images d'`assets/` — détail du format en poc.md
- Séparation stricte entre `src/ui` (affichage PC) et `src/gameplay` (logique de jeu, partagée avec la version web)
- `src/gameplay` reste la seule source de vérité des règles de jeu : la version web ne fait que l'exécuter et l'afficher, elle ne réimplémente aucune règle

### 10.3 Persistance du parcours (profils et sauvegardes)

Nécessaire pour que les dégâts/niveau de mise à jour des modules (§2.2) et l'avancement dans le
parcours (§2.3) survivent d'un combat à l'autre. **Les sauvegardes sont rattachées à un joueur**
(décision utilisateur) : pas de compte/login, mais plusieurs **profils locaux nommés** peuvent
coexister sur un même appareil. **Un joueur ne peut avoir qu'une seule partie EN_COURS à la fois**
(décision utilisateur) — remplace la piste antérieure de plusieurs parties actives en parallèle par
profil ; ses anciennes parties `TERMINEE` restent sur disque (pour de futures statistiques, voir
plus bas) mais ne sont pas sélectionnables, il n'y a donc **pas besoin d'écran de sélection de
partie** (contrairement à ce qui avait été envisagé).

**Implémenté** — `main.py`/`index.html` sont désormais le **vrai point d'entrée du jeu** (décision
utilisateur), plus des écrans autonomes non reliés comme les précédents.

#### Profil joueur

- PC : `saves/<joueur_id>/profil.json` ; web : `localStorage` (une entrée par joueur, sous la clé
  `space_fight_joueurs`, contenant directement la liste des profils plutôt qu'un index séparé — plus
  simple tant que les profils restent de petits objets)
- **Contenu actuel** : `{"version": 1, "id": "joueur_20260823_140000", "nom": "Alice"}`
- **Statistiques et déblocages évoqués par l'utilisateur (parties jouées/victoires/défaites, niveau
  max atteint, module le plus choisi, déblocages en fin de partie) : sciemment laissés de côté pour
  l'instant** (décision utilisateur explicite, "pas de stat pour le moment") — pas de champ dans le
  JSON actuel, à ajouter dans une passe dédiée. Pistes envisagées à ce moment-là : compteurs mis à
  jour au fil du jeu plutôt que recalculés depuis l'historique (`parties_jouees`, `defaites`,
  `niveau_max`, `modules_choisis` par `module_id`) ; `victoires` reste bloqué tant qu'une condition
  de victoire de run n'est pas définie (voir §9.1) ; `deblocages` en liste vide, mécanique à
  imaginer

#### Partie (une sauvegarde, rattachée à un profil)

- PC : `saves/<joueur_id>/parties/<partie_id>.json` (un fichier par partie, y compris les
  `TERMINEE` conservées) ; web : `localStorage`, une entrée `space_fight_partie_<joueur_id>` — une
  seule a la fois (cf. "un joueur ne peut avoir qu'une seule partie EN_COURS" plus haut : les
  parties `TERMINEE` ne sont pour l'instant pas conservées côté web, contrairement à PC — écart
  volontaire tant qu'aucun écran n'affiche l'historique, voir §9.1)
- **Contenu** :
  ```json
  {
    "version": 1,
    "id": "partie_20260823_142301",
    "nom": "Partie du 23/08/2026",
    "statut": "EN_COURS",
    "graine": 918273645,
    "niveau": 1,
    "argent": 0,
    "vaisseau": {
      "base":           {"module_id": "MOD_1", "pv": 15, "pv_max": 15, "niveau_maj": 1},
      "avant_gauche":   null,
      "avant_droite":   null,
      "arriere_gauche": null,
      "arriere_droite": null
    },
    "deck": ["CRT_7", "CRT_7", "CRT_7", "CRT_7", "CRT_8", "CRT_9", "CRT_10", "CRT_10", "CRT_10", "CRT_10", "CRT_11", "CRT_12"]
  }
  ```
  - `version` : version du format, pour d'éventuelles migrations futures
  - `id` : identifiant unique (nom de fichier PC / suffixe de clé localStorage web)
  - `nom` : affiché dans les futurs écrans d'historique (généré automatiquement pour l'instant à
    partir de la date — pas de renommage par le joueur prévu dans un premier temps)
  - `statut` : `EN_COURS` ou `TERMINEE` (décision utilisateur : une défaite ou un abandon **ne
    supprime pas** le fichier PC, marqué `TERMINEE` pour un futur écran de récapitulatif de run —
    une nouvelle partie crée un nouvel `id`)
  - `graine` : graine maîtresse du run (décision utilisateur). Combinée au `niveau`
    (`aleatoire_pour_niveau(graine, niveau)`, §2.3), elle **retire à l'identique** les propositions
    d'étape d'un niveau sans les stocker littéralement — cohérent avec la convention `random.Random` déjà utilisée partout dans le moteur (voir
    "Déterminisme du tirage aléatoire" dans `CLAUDE.md`). Utilisée pour tirer les 3 candidats du
    choix de module de Niveau 1 d'une nouvelle partie, les propositions du choix du prochain niveau,
    et comme graine de repli pour le combat approximatif du bouton "Continuer" (voir plus bas)
  - `niveau` : niveau courant (1 pour une partie neuve, incrémenté par `avancer_niveau()` à chaque
    étape résolue — choix de module, combat gagné — cf. §2.4)
  - `vaisseau` : un état par emplacement (base + 4 équipables, §5) — `module_id` (référence
    `config/modules.json`), `pv`/`pv_max` (§2.2), `niveau_maj` (palier de mise à jour, 1 à 3, §2.2) ;
    `null` si l'emplacement est vide. Une partie neuve n'a que `base` d'équipé (deck/PV du module
    principal, `config_poc.ids_deck_module_principal`) — le 2ᵉ emplacement est rempli au choix du
    Niveau 1 (`equiper_module()`, §2.4)
  - `deck` : ids de cartes possédées (`config/cartes.json`), doublons répétés dans la liste — même
    principe que `regrouper_cartes()` (§6) pour l'affichage, mais stockage à plat ici

#### Écrans (implémentés, PC + web)

Fond de combat réutilisé en placeholder (comme les autres écrans du parcours), à remplacer par un
fond dédié.

- **Sélection/création de profil** — liste des profils existants (clic pour choisir) + création
  d'un profil par un nom (Entrée/bouton "Créer"). `src/ui/ecran_selection_joueur.py` (PC, saisie de
  texte gérée manuellement via `on_text`/`on_key_press`, pas de widget pyglet dédié) ; `web/app.js`
  (`afficherSelectionJoueur`/`creerNouveauJoueur`) + `web/bridge.py` (`creer_profil_web`)
- **Accueil du joueur** — si une partie `EN_COURS` existe : niveau, vaisseau (grille des modules
  équipés avec PV/PV max/niveau de mise à jour, ou "Emplacement vide"), boutons **Continuer** /
  **Abandonner la partie** / **Voir le deck**. Sinon : bouton **Nouvelle partie**.
  `src/ui/ecran_accueil_joueur.py` (PC) ; `web/app.js` (`afficherAccueilJoueur` et les handlers de
  chaque bouton) + `web/bridge.py` (`infos_vaisseau_web`, `deck_partie_web`, `abandonner_partie_web`,
  `nouvelle_partie_web`, `choix_module_partie_web`, `continuer_partie_web`)
- **Nouvelle partie** → écran de choix de module du Niveau 1 déjà existant (§2.3), candidats tirés à
  partir de la graine de la partie fraîchement créée
- **Voir le deck** → écran "deck en entier" déjà existant (§6), alimenté par le deck réel de la
  partie (pas une démonstration aléatoire). L'Écran de partie ayant déjà été fermé/masqué à
  l'ouverture, un bouton **Retour** (PC : `EcranDeck.termine` ; web : `#bouton-retour-deck`) est le
  seul moyen d'y revenir — bug réel corrigé après un premier passage sans lui (aucune fermeture de
  fenêtre native ne rouvrait quoi que ce soit sur PC, et aucune navigation possible sur web)
- **Continuer** → reprend l'étape exacte où le joueur s'était arrêté (§2.4, étape 2) : Choix de
  module si Niveau 1 sans 2ᵉ module équipé, sinon Choix du prochain niveau pour le niveau courant.
  Un combat lancé depuis là (Prime ou Boss) reprend le vaisseau/deck réels de la partie, mais tire
  toujours une **flotte ennemie au hasard** — l'orchestration ne détermine pas encore précisément
  quel combat affronter à ce niveau (nombre/taille d'ennemis selon §3.2, voir §10.3 "Limites
  connues"). `combat_depuis_partie()` dans `src/gameplay/partie.py`
- **Abandonner la partie** : marque la partie `TERMINEE` (`marquer_terminee()`) et revient à
  l'écran d'accueil, qui affiche alors le bouton "Nouvelle partie"
- **Enchaînement complet d'une vraie partie** (§2.4, étapes 2 à 6) : `main.py` (PC, une fonction
  `_ouvrir_xxx` par écran, transitions détectées via `pyglet.clock.schedule_interval`) ; côté web,
  `web/app.js` garde une variable `partieActive` (la `Partie` en cours d'orchestration, ou `null`
  en mode démonstration) que `choisirModule`/`choisirEtape`/`choisirRecompense` consultent pour
  choisir entre persistance réelle et comportement de démonstration (`console.log`) inchangé

#### Implémentation

- `src/gameplay/partie.py` (nouveau) : dataclasses `Profil`/`Partie`/`EtatModule`, sérialisation
  JSON pure (`profil_vers_json`/`profil_depuis_json`, `partie_vers_json`/`partie_depuis_json`,
  testables sans I/O), `nouveau_profil`/`nouvelle_partie`/`combat_depuis_partie`/`marquer_terminee`,
  et l'I/O fichier PC (`lister_profils`, `creer_profil`, `sauvegarder_partie`, `partie_en_cours`,
  `abandonner_partie`, sous `saves/`, nouveau dossier ajouté au `.gitignore`)
  - Nom `Profil` retenu plutôt que `Joueur` (déjà pris par `src/gameplay/joueur.py`, l'état de
    combat éphémère vaisseau + deck + électricité, §3.3) — pas de collision
  - `config_poc.deck_module_principal` factorisé en `ids_deck_module_principal` (renvoie des ids
    plutôt que des `Carte`) pour être réutilisable par `nouvelle_partie` sans dupliquer la règle
- `web/bridge.py` : les fonctions ci-dessus n'effectuent **aucune I/O** (Pyodide n'a pas de FS
  persistante entre rechargements de page) — elles ne font que (dé)sérialiser et appliquer la
  logique pure de `partie.py` ; la lecture/écriture `localStorage` est entièrement gérée côté
  `web/app.js`
- `main.py` : ouvre `EcranSelectionJoueur`, puis `EcranAccueilJoueur`, puis l'écran suivant selon
  l'action choisie — chaque écran étant une fenêtre pyglet indépendante, les transitions ferment la
  fenêtre courante et ouvrent la suivante, détectées via `pyglet.clock.schedule_interval` (pas
  d'événement dédié "l'utilisateur a fait un choix" sur ces fenêtres)

#### Limites connues (à lever plus tard)

- **Portée volontairement limitée** : seuls les points de passage entre étapes sont sauvegardés
  (juste après choix de module, juste après résolution d'une fin de combat, d'une Station service
  ou d'une étape Aventure/Planète commerciale) — un combat en cours n'est pas sauvegardable ; le
  quitter en cours de route (fermer l'onglet/l'appli) le fait recommencer entièrement à la reprise,
  au même niveau
- Planète commerciale et Aventure n'ont pas encore de contenu propre (§2.4, étapes 7 et 9, §9.1) :
  un seul écran générique (`EcranEtapePlaceholder`) les représente toutes les deux, sans autre
  effet que d'avancer au niveau suivant
- Le run s'arrête réellement au Niveau 10 dans l'état actuel (décision utilisateur, provisoire,
  voir §2) : la Victoire finale (§2.4, étape 11) marque la partie `TERMINEE` sans proposer de
  continuation au-delà de ce niveau
- La flotte ennemie d'un combat (Prime ou Boss) reste toujours tirée entièrement au hasard
  (`combat_depuis_partie`/`creer_flotte`), sans appliquer les règles de difficulté par niveau du
  §2.3/§3.2 (nombre d'ennemis, tailles S/M/L) — reste un tirage de démonstration
- Écart PC/web sur la conservation des parties `TERMINEE` (voir "Partie" plus haut) : à corriger si
  un écran d'historique est construit côté web
- `argent` ne progresse jamais dans le flux actuel (aucune étape ne le fait varier : la Station
  service est reliée mais ses 4 actions restent gratuites tant que la ressource Argent n'existe pas
  côté gameplay, §2.2/§9.1 ; Planète commerciale n'est pas construite)

### 10.4 Conventions de code

- Classes claires et bien définies, une responsabilité par classe
- Commentaires en français, **sans accents ni cédilles** (ASCII uniquement)
- Tests unitaires (pytest) dans `tests/`

---

## 11. Idées à explorer plus tard

Pistes évoquées mais pas encore approfondies ni décidées — à revisiter une fois le système de
cartes (§7) et la boucle de récompenses (§2.1, §6) stabilisés.

- **Cartes auto-jouées** : des cartes qui se déclenchent seules, sans action du joueur, en début ou
  en fin de combat (ex : buff automatique pour toute la durée du combat au démarrage, soin ou gain
  d'Argent à la fin) — distinct des cartes jouées normalement pendant le tour du joueur (§3, §7)
- Une carte auto-jouée en fin de combat pourrait aussi offrir une carte candidate supplémentaire, en
  plus de la récompense normale de combat (§2.1, §6)
- À trancher plus tard : comment ces cartes s'intègrent au deck existant (pioche normale, zone à
  part, slot dédié au module...), leur coût (électricité ou gratuites, puisqu'elles ne sont pas
  jouées manuellement), et si elles ont une rareté (§7.3) comme les autres cartes
- **Type de carte "Effet"** (nouveau, distinct des types de §7.1) : une carte qui produit son effet
  dès qu'elle est **piochée**, plutôt que jouée par le joueur. Probablement ajoutée au deck par les
  ennemis (dans l'esprit des cartes Statut/Malédiction de Slay the Spire) plutôt que choisie par le
  joueur
- **Stacks à intensité cumulative** (façon Poison/Force de Slay the Spire) : un unique compteur par
  ennemi qui s'additionne à chaque application (contrairement aux debuffs Vulnérabilité/Réduction de
  dégâts actuels, §7.1/§12.1, où chaque application reste une instance indépendante avec sa propre
  durée — plusieurs instances coexistent et leurs magnitudes s'additionnent tant qu'elles sont
  actives, mais rien ne fusionne en un seul compteur) et qui inflige un effet croissant avec le
  nombre de stacks (ex : dégâts égaux au compteur, qui décroît de 1 chaque tour). Mécanique distincte
  à concevoir pour de futures cartes, pas une règle à appliquer aux cartes de vulnérabilité
  existantes

---

## 12. Mécaniques de combat manquantes (constat issu du tableau de cartes)

En important le tableau de conception de cartes de l'utilisateur dans `config/cartes.json` (voir la
PR "config : import des cartes Module principal, Lanceur de missiles, Blindage"), seules 6 des 38
cartes du tableau correspondaient à ce que le moteur (`src/gameplay/carte.py`, `combat.py`) savait
exécuter à l'époque. Ce nombre a augmenté au fil des mécaniques ajoutées ci-dessous (22/38 jouables
au moment de la rédaction la plus récente de cette section, cf. poc.md §4) ; les cartes restantes
sont stockées pour référence (champ `_non_jouable`) mais inertes en jeu tant que leur mécanique
n'est pas implémentée. Cette section recense les mécaniques qui leur manquent, groupées par nature
plutôt que par carte, pour servir de feuille de route à une future extension du moteur.

### 12.1 Cibles fixes ou par rang

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

Debuff actif pendant Y tours (chaque application ajoutée à la liste `Ennemi.debuffs_actifs`, comme
une instance indépendante avec sa propre durée ; décrémentée à chaque tour ennemi écoulé même si
l'ennemi concerné n'a pas agi, et retirée de la liste à 0) — **implémenté** pour les debuffs
(§12.4/§12.5) : *Boucliers hors service* jouable.

Même mécanique côté allié (`Module.buffs_actifs`), avec en plus la possibilité d'une durée **nulle**
(`tours_restants=None`) pour un buff **persistant** qui ne décompte jamais et dure tout le combat —
**implémenté** (§12.5) : *Bouclier perpétuel* (persistant) et *Blindage maximal* (durée limitée,
même mécanisme `BOUCLIER_PAR_TOUR` avec `duree` finie plutôt que nulle) jouables — les deux seules
cartes Buff à effet périodique simple (les 3 autres cartes Buff restantes sont des méta-effets, cf.
§12.5/§12.7). L'effet d'un buff se déclenche une première fois immédiatement à la pose de la carte
(comme les autres types de carte), puis se redéclenche à chaque début de tour joueur tant qu'il
reste actif.

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

### 12.4 Effets en pourcentage

**Implémenté pour les debuffs** (somme des `valeur` des debuffs `VULNERABILITE` actifs dans
`Ennemi.debuffs_actifs`, majore les dégâts subis d'une attaque du joueur) : *Brèche, Ligne avant,
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
  *Bouclier perpétuel, Blindage maximal* jouables. *Optimisation des boucliers, Attaques
  performantes* (modification du coût d'une catégorie de cartes) et *Double défense, Circuit
  parallèle* (duplication d'effet) restent non jouables, ce sont des méta-effets distincts (§12.7),
  pas de simples buffs sur un module
- **Outils** — **implémenté** (`TypeCarte.OUTILS`, cf. §12.9) pour trois actions (`GAIN_ELECTRICITE`,
  `GAIN_ELECTRICITE_PAR_MODULE`, `PIOCHE_SUPPLEMENTAIRE`) : *Surcharge temporaire, Fonds de tiroir,
  Boost* jouables. Le reste demande encore une logique dédiée (*Changement d'outil, Manque de jus,
  Cannibalisme, Grand remplacement, Multi fonction*)
- **Controle** : toujours aucune carte taguée Controle dans le tableau ; type prévu en §7.1 (stun,
  restriction d'action) mais rien à implémenter pour l'instant

### 12.6 Altération / redirection des dégâts

- Transfert des dégâts subis vers un autre module désigné (*Transfert*)
- Renvoi des dégâts subis à l'attaquant (*Renvoie*)
- Annulation totale de la prochaine attaque sur une cible, différent d'un bouclier classique
  (*Leurre*) — **implémenté** (`ActionCarte.ANNULATION_PROCHAINE_ATTAQUE`, sur une carte Defense) :
  *Leurre* jouable. Un flag `Module.leurre_actif` (pas un buff : pas de redéclenchement
  périodique, pas de durée en tours) rend la **toute prochaine** attaque reçue totalement nulle
  (0 dégât, y compris si elle dépasserait PV+bouclier cumulés), puis se consomme — dès la première
  attaque reçue après la pose, même si plusieurs ennemis attaquent ce module dans le même tour —
  seule la **première** attaque résolue sur ce module est annulée, dans l'ordre de résolution du
  tour ennemi (`Combat._tour_ennemi`, poc.md §3 : colonne Avant de haut en bas puis colonne
  Arrière de haut en bas), les suivantes s'appliquent normalement. L'intention affichée au
  survol/tap d'un ennemi (poc.md §8) montre toujours sa **vraie** attaque, jamais 0 à cause d'un
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
  parallèle*)

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
