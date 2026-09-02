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
  - **AVENTURE** — événement inconnu, façon "?" de Slay the Spire. 3 premières aventures spécifiées
    (voir §2.5), reste à en écrire d'autres pour varier le pool (§9.1)
  - **CHOIX DE MODULE** — niveau 1 uniquement (§2.3) : 3 modules différents tirés au sort, le joueur en choisit un
  - *(autres types d'étapes à imaginer)*
- **Boss** : niveau 10, puis tous les 10 niveaux (20, 30, 40...) — voir §2.3
  - Victoire sur un boss → le joueur choisit **1 nouveau module parmi 2 propositions**, avec ses cartes de base associées (deck de départ propre au module — détail à trancher une fois le système de cartes approfondi, voir §7)
  - **Le run s'arrête réellement au Niveau 10 dans l'état actuel** (décision utilisateur, provisoire,
    voir §2.4) : gagner le Boss du niveau 10 mène à un écran de victoire finale, le run ne continue
    pas au-delà pour l'instant — la récompense de Boss "1 module parmi 2" ci-dessus reste donc hors
    champ tant que cette limite n'est pas repoussée (niveaux 20, 30..., voir §9.1)

### 2.1 Argent et récompenses de combat

- Après chaque combat gagné, le joueur gagne de l'**Argent** — nouvelle ressource de run, distincte
  de l'Électricité (ressource de combat, voir §3). **Implémenté** : 5 € galactiques par ennemi de la
  flotte affrontée (`ARGENT_PAR_ENNEMI_TUE`, `src/gameplay/partie.py:gagner_argent_combat`), appelée
  juste après `synchroniser_vaisseau_depuis_combat` (§2.2) — `main.py:_ouvrir_combat` (PC),
  `web/bridge.py:resoudre_victoire_partie_web` (web). Compte un ennemi par case de la flotte
  (`Flotte.positions()`), pas de fusion des ennemis L sur 2 cases pour l'instant (§3.2/§9.1). Une
  partie démarre avec `ARGENT_DEPART` = 7 € (`nouvelle_partie`)
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

**Chaque action coûte `COUT_ACTION_STATION_SERVICE` = 20 €** (`src/gameplay/partie.py`), déduits de
`partie.argent` au moment où l'action s'applique (Déplacer : au clic de destination, pas à
l'armement). Si l'Argent est insuffisant, l'action est refusée sans rien modifier — les 4 fonctions
(`reparer_module`/`ameliorer_module`/`mettre_a_jour_module`/`deplacer_module`) renvoient un booléen
de succès plutôt que la `Partie` (rétro-incompatibilité assumée, aucun appelant n'utilisait la valeur
de retour). Écran Station service (PC et web) : prix affiché sous chaque action, icône grisée et
popup rouge "Argent insuffisant !" au clic si `partie.argent < COUT_ACTION_STATION_SERVICE` (armement
de Déplacer bloqué dans ce cas, pas seulement son exécution) ; Argent total affiché dans le titre de
l'écran ("... - Niveau N - X €"). Côté web, `COUT_ACTION_STATION_SERVICE` est exposé par
`web/bridge.py:cout_action_station_service_web()` plutôt que dupliqué en dur dans `web/app.js`
(CLAUDE.md).

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
- **Report des PV de combat sur la partie sauvegardée** : `combat_depuis_partie()` construit le
  `Combat` à partir des PV persistés, mais l'opération inverse est nécessaire pour que les dégâts
  subis *pendant* ce combat soient effectivement conservés — sans elle, la persistance ci-dessus
  restait inerte en jeu réel (bug constaté par l'utilisateur, corrigé). `synchroniser_vaisseau_depuis_combat(partie, vaisseau)`
  (`src/gameplay/partie.py`) reporte les PV du `Vaisseau` de combat sur `partie.vaisseau[...]` (pas
  `pv_max`, ni le bouclier, mécanique de combat éphémère absente d'`EtatModule`) — appelée dès la fin
  d'un combat gagné, avant tout enchaînement/sauvegarde ultérieur : `main.py:_ouvrir_combat` (PC),
  `web/bridge.py:resoudre_victoire_partie_web` (web, à partir de la variable globale `combat` encore
  celle du combat qui vient de se terminer à ce stade)

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
- **Réparer/Améliorer/Mettre à jour** affichent un popup de confirmation sur la carte du module
  concerné (2 secondes, même mécanisme que les popups +/-N du combat) — `+N PV`/`+N PV max`/
  `Niveau N`, calculé à partir de l'état avant/après l'action plutôt qu'une valeur de réglage
  dupliquée côté web (décision utilisateur, feedback demandé pendant les essais manuels). Le module
  sélectionné est ensuite **désélectionné automatiquement** (le popup suffit à confirmer l'effet) ;
  **Déplacer** garde son comportement propre (armement/clic de destination, cf. ci-dessus)
- **Icônes des 4 actions : rangée d'icônes déjà pourvues de leur propre cadre/nom incrusté**
  (`assets/station_service/avec_texte/reparer.png`/`ameliorer.png`/`mettre_a_jour.png`/
  `deplacer.png`), affichées seules avec juste le prix en dessous — décision utilisateur : un
  essai de mise en page "empilée verticalement, image sans texte à gauche + titre/description à
  droite" (même convention que les choix d'Aventure, §2.5) a été tenté avec les versions sans texte
  de `assets/station_service/` (celles réutilisées telles quelles par les Aventures Trois
  lunes/Police), puis abandonné pour cet écran uniquement, jugé moins lisible ; anciennes icônes
  avec texte restaurées depuis l'historique git dans un sous-dossier dédié (`avec_texte/`) plutôt
  que redemandées à l'utilisateur — Choix du prochain niveau et Station service ne partagent donc
  plus la même présentation, contrairement à ce qu'un essai précédent visait
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

**Barre latérale persistante** (décision utilisateur) affichée à gauche de **tous** les écrans du
parcours, Combat compris — Choix de module, Choix du prochain niveau, Station service, les trois
Aventures, Planète commerciale (écran placeholder), Fin de combat et Combat — mais pas sur l'Écran
de partie/Deck/Victoire finale (qui affichent déjà Argent/deck/vaisseau autrement). Contenu, du
haut vers le bas : **Niveau**, **Argent**, un bouton **Deck** (icône `assets/interface/deck.png`,
avec le nombre de cartes du deck en dessous) et un bouton **Vaisseau** (icône
`assets/interface/vaisseau.png`) qui ouvrent chacun un écran de consultation en lecture seule
**par-dessus l'écran appelant, qui reste ouvert et inchangé derrière** (aucun état interne à cet
écran perdu/réinitialisé — important pour les écrans à état multi-étapes comme les Aventures
Astéroïdes/Police). C'est désormais la **seule** source de Niveau/Argent visible sur ces écrans :
plus aucun titre ne répète "- Niveau N" ni l'Argent (retiré de Station service/Choix de
module/Choix du prochain niveau/Aventures/Planète commerciale/Fin de combat une fois la barre en
place, pour éviter la redondance) — le titre de l'écran garde uniquement son sujet propre (ex.
"Station service", "Choix du prochain niveau"). Non affichée à l'écran Victoire finale (le run est
terminé à ce stade).
- PC (`src/ui/barre_laterale.py`) : exploite le support natif de pyglet pour plusieurs fenêtres
  simultanément — l'écran de consultation (`EcranDeck`/`EcranVaisseau`, nouveau) s'ouvre dans une
  **fenêtre pyglet additionnelle**, sans fermer la fenêtre appelante ; se referme tout seul via un
  petit minuteur dédié (`barre_laterale.ouvrir_survol`) qui surveille son `self.termine` et appelle
  `.close()` — aucune modification nécessaire à l'orchestration existante de `main.py`. Largeur de
  90px, choisie pour tenir sous la marge la plus étroite des écrans concernés (grille de modules de
  Station service) sans retoucher leur mise en page. En Combat, `FenetreCombat` reçoit `partie` en
  plus de `combat` (`None` en mode démo POC, où la barre n'a alors rien à afficher) ; la barre y est
  décalée sous le bandeau Électricité/Fin de tour existant (`Y_HAUT_BARRE_COMBAT`, sous ce bandeau
  plutôt que par-dessus) via un paramètre `y_haut` optionnel de `barre_laterale.dessiner()`/
  `bouton_survole()`, sinon égale au haut de la fenêtre par défaut sur les écrans sans en-tête
  propre.
- Web (`web/app.js` : `actualiserBarreLaterale`/`ouvrirSurvolDeck`/`ouvrirSurvolVaisseau`) :
  `#ecran-deck`/`#ecran-vaisseau` passent en `position: fixed` (classe `.ecran-survol`,
  `web/style.css`) pour se superposer à l'écran actuellement affiché sans passer par
  `masquerTousLesEcrans()` (qui le masquerait) — même principe que côté PC, sans fenêtre
  additionnelle puisque le web n'affiche qu'un seul écran DOM visible à la fois. En Combat, la barre
  est décalée sous `#entete` (classe `.barre-laterale-combat`). **Simplification web** (écart
  documenté, cf. CLAUDE.md) : barre étroite (52px, choisie expressément pour inclure l'iPhone
  12/13 mini — 812px de large en paysage, remonté par l'utilisateur comme resté sans barre avec une
  première largeur de 60px/seuil 820px) et **masquée sous 760px de large en paysage, et
  systématiquement en portrait** — mesuré empiriquement (Playwright) comme le seuil au delà duquel
  elle ne chevauche jamais la grille de 5 modules (Station service et l'étape "choix_module" des
  Aventures Trois lunes/Astéroïdes) ; seul l'iPhone SE et plus petit (667px) reste sous ce seuil, la
  barre y est simplement absente. En Combat spécifiquement, la largeur du bloc vaisseau dépend aussi de la
  hauteur d'écran (`--taille-case`) : un seuil de largeur fixe ne suffisant pas à garantir l'absence
  de chevauchement sur tous les formats (fenêtre large et haute, tablette en paysage...),
  `actualiserBarreLaterale`/`barreChevaucheVaisseau` vérifient le chevauchement réel après affichage
  (comparaison des rectangles DOM) et masquent la barre au lieu de deviner un second seuil.

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
   `src/ui/ecran_choix_niveau.py` (PC, jusqu'à 3 propositions, 1 seule à un niveau Boss — icône
   dédiée par type, `assets/prochain_niveau/`, images fournies par l'utilisateur **sans texte
   incrusté** — présentées **empilées verticalement, image à gauche et rectangle de texte (titre +
   description) à droite**, même convention que les choix d'Aventure (§2.5) et de Station service
   (§2.2), plutôt que des cartes côte à côte avec image+description empilées à l'intérieur — mise en
   page initiale, abandonnée une fois les icônes fournies sans texte) ; `web/bridge.py`
   (`choix_niveau_web`), `web/app.js` (`afficherChoixNiveau`/`choisirEtape`)
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
7. **Aventure** (détaillé en §2.5, **trois Aventures implémentées et reliées à l'enchaînement :
   "Trois lunes", "Astéroïdes" et "Police"** ; tirage uniforme non déterministe entre les trois via
   `tirer_type_aventure`, PC (`main.py`) et web (`type_aventure_web`)) : un choix résolu puis un
   bouton "Continuer" avance le niveau et revient au Choix du prochain niveau (étape 3), même
   principe que Station service — sauf le choix "Affronter les pirates" de l'Astéroïdes, qui délègue
   au pipeline Combat (étape 5) via un combat scripté plutôt que d'avancer directement.
   `src/ui/ecran_aventure_trois_lunes.py`/`src/ui/ecran_aventure_asteroides.py`/
   `src/ui/ecran_aventure_police.py` (PC) + `main.py:_ouvrir_aventure_trois_lunes`/
   `_ouvrir_aventure_asteroides`/`_ouvrir_aventure_police` ; côté web `web/bridge.py`
   (`constantes_aventure_trois_lunes_web`/`deck_groupe_par_id_partie_web`/
   `reparer_vaisseau_aventure_web`/`ameliorer_module_aventure_web`/`retirer_carte_aventure_web`/
   `terminer_aventure_trois_lunes_web` ; `constantes_aventure_asteroides_web`/
   `subir_degats_module_asteroides_web`/`carte_offerte_asteroides_web`/
   `prendre_carte_offerte_asteroides_web`/`combat_aventure_asteroides_web`/
   `terminer_aventure_asteroides_web` ; `constantes_aventure_police_web`/`tirer_carte_police_web`/
   `confiscation_police_web`/`mettre_aux_normes_police_web`/`terminer_aventure_police_web`) + `web/app.js`
   (`ouvrirAventureTroisLunesPartie`/`ouvrirAventureAsteroidesPartie`/`ouvrirAventurePolicePartie` et
   fonctions associées)
8. **Station service** (détaillé en §2.2, **implémenté et relié à l'enchaînement**) : Réparer /
   Améliorer / Mettre à jour / Déplacer un module, un bouton "j'ai terminé" avance le niveau et
   revient au Choix du prochain niveau (étape 3), même principe que la fin d'un combat gagné
9. **Planète commerciale** (contenu non préparé, §2/§9.1, **relié à l'enchaînement via un écran
   générique**) : un bouton "j'ai terminé" avance le niveau et revient au Choix du prochain niveau
   (étape 3) — en attendant un vrai contenu, l'écran se limite à afficher l'icône/description déjà
   utilisées au Choix du prochain niveau avec un message "Contenu pas encore défini pour cette
   étape." `src/ui/ecran_etape_placeholder.py` (PC) + `main.py:_ouvrir_etape_placeholder` ; côté web
   `web/bridge.py` (`terminer_etape_placeholder_web`) + `web/app.js`
   (`ouvrirEtapePlaceholderPartie`/`terminerEtapePlaceholder`)
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

### 2.5 Aventures (contenu)

Contenu concret des 3 premières Aventures spécifiées à ce jour — brouillon détaillé dans
`specs/cartes.xlsx`, onglet "Aventures" (miroir humainement modifiable, même principe que l'onglet
Cartes, cf. CLAUDE.md/§10.3). **Les trois Aventures (Trois lunes, Astéroïdes, Police) sont
implémentées** (voir ci-dessous). `TypeEtape.AVENTURE` tire au hasard laquelle des trois ouvrir
(`tirer_type_aventure`, `TypeAventure`, `src/gameplay/parcours.py` — tirage uniforme non
déterministe, comme les récompenses de fin de combat).

Forme retenue pour l'écran Aventure : un écran dédié par Aventure (pas l'écran générique),
affichant description + 2-3 choix cliquables — même présentation que l'écran Choix du prochain
niveau (§2.4 étape 3, choix empilés verticalement, image sans texte incrusté à gauche, titre +
description à droite) plutôt qu'une mise en page différente par écran. Exception : la Station
service (§2.2) est revenue à sa rangée d'icônes avec texte incrusté (décision utilisateur, cf.
§2.2), les 2 écrans n'ont donc plus tout à fait la même présentation. Une Aventure scénarisée
en plusieurs temps (Astéroïdes ci-dessous) reste un **seul écran** dont le contenu affiché change à
mesure que le joueur avance (état interne à l'écran, comme `EcranStationService` se redessine après
chaque action) plutôt que plusieurs écrans/fenêtres séparés — décision utilisateur : pas de moteur
de séquence narrative générique, chaque Aventure scripte ses propres étapes en dur (Trois lunes :
"choix" -> "choix_module"/"choix_carte" -> "resolu" ; Astéroïdes : "choix" -> "choix_module" ->
"sequence_2" -> "sequence_3"/"resolu" -> "resolu" ; Police : "choix" -> "resolu", un attribut `etape`
interne à l'écran dans les trois cas). Contenu prévu à terme dans un `config/aventures.json` (miroir
de l'onglet xlsx, même relation que `config/cartes.json`/onglet Cartes) — pas encore créé, les trois
Aventures actuelles restant scriptées en dur ; structure à définir si/quand d'autres Aventures
s'ajoutent au pool (§9.1).

**Présentation des choix** (les trois écrans) : chaque choix est une ligne empilée verticalement
(pas de disposition en grille), avec une image carrée à gauche et, à droite, un long rectangle
contenant le titre puis la description — décision utilisateur, pour préparer une illustration par
choix. `_dessiner_carte_choix`/`construireLigneChoixHtml` (respectivement PC et web) partagent cette
mise en page entre les trois écrans (dupliquée par fichier côté PC, factorisée en une fonction
commune côté web). **Les 8 choix des 3 Aventures sont désormais tous illustrés** — une ligne sans
image dédiée afficherait un placeholder vide (même convention que les autres emplacements vides du
jeu), mais ce cas ne se présente plus à ce jour :
- Réparer/Améliorer (Trois lunes) depuis `assets/station_service/reparer.png`/`ameliorer.png`,
  Affronter les pirates (Astéroïdes) depuis `assets/prochain_niveau/prime.png`, Mettre aux normes
  (Police) depuis `assets/station_service/mettre_a_jour.png` — **recadrées pour retirer leur bandeau
  de titre incrusté** (respectivement "RÉPARER"/"AMÉLIORER" — déjà le bon titre, recadré tout de
  même par cohérence visuelle avec les autres —, "PRIME" et "METTRE À JOUR" — non pertinents pour
  ces choix). Le titre étant de toute façon systématiquement redessiné à côté dans le rectangle de
  texte, un bandeau incrusté n'a plus d'intérêt à être conservé, qu'il corresponde ou non au choix.
- Traverser le champ d'astéroïdes (Astéroïdes) depuis le fond d'écran de sa propre Aventure
  (`assets/aventure/champ_asteroides.png`, extrait carré plutôt qu'une icône dédiée)
- Bricoler (Trois lunes), Confiscation et Détourner l'attention (Police) : illustrations dédiées
  fournies par l'utilisateur (`assets/aventure/bricoler.png`/`confiscation.png`/`detourner.png`)

Recadrages/extraits/illustrations dédiées, toutes conservées dans `assets/aventure/`
(`reparer.png`/`ameliorer.png`/`pirates.png`/`mettre_aux_normes.png`/`traverser.png`/`bricoler.png`/
`confiscation.png`/`detourner.png`) ; sources originales des icônes recadrées inchangées pour leur
usage propre (Station service, Choix du prochain niveau).

**Astéroïdes** — **implémentée** (fond `assets/aventure/champ_asteroides.png`) — "Poursuivi par des
pirates de l'espace, vous n'avez plus le choix : vaincre ou périr ! À moins que..."
- Choix 1, *Traverser le champ d'astéroïdes* : séquence en 3 temps sur le même écran, chaque étape
  validée par un bouton "Continuer" :
  1. Le joueur clique un module (`_dessiner_choix_module`/`choix_module`) : -`DEGATS_ASTEROIDES` (5)
     PV appliqués immédiatement (`subir_degats_module`, nouveau côté moteur : dégâts hors combat,
     plafonnés à 0, opération inverse de `reparer_module`/`reparer_vaisseau`), puis affichage d'un
     message de confirmation + bouton "Continuer" (étape `sequence_2`)
  2. Au clic sur "Continuer" : -`DEGATS_ASTEROIDES` PV supplémentaires (même module)
  3. Une carte est tirée au hasard dans le pool complet (`pool_toutes_cartes`/`tirer_carte_recompense`,
     §6) et proposée gratuitement (boutons "Prendre"/"Passer", étape `sequence_3`) — gratuite et
     hors du flux de récompense standard de fin de combat. Si le pool est vide (`carte` = `None`),
     l'étape `sequence_3` est sautée directement vers `resolu`
- Choix 2, *Affronter les pirates* : lance un combat scripté contre `NOMBRE_ENNEMIS_ASTEROIDES` (3)
  ennemis (`combat_aventure_asteroides`/`creer_flotte_asteroides`) — approximation décidée en
  attendant la taille S/M/L par ennemi (absente de `config/ennemis.json`, cf. §3.2/§9.1/§10.3) :
  ennemis tirés du pool existant sur les 3 premières cases de la grille (colonne Avant), plutôt que
  le tirage standard d'un combat Prime (grille complète, `combat_depuis_partie`). Délègue
  entièrement au pipeline Combat existant (étape 5/6 : victoire → Argent + carte, comme un Prime
  normal ; défaite → même traitement qu'un combat normal) via `main.py:_ouvrir_combat`
  (paramètre `combat` optionnel, déjà construit par l'appelant) / `web/bridge.py:combat_aventure_asteroides_web`
  (même variable globale `combat` que `continuer_partie_web`, reste du pipeline de fin de combat
  inchangé)
- Pas de 3ᵉ choix (binaire assumé)

`src/gameplay/config_poc.py` (`NOMBRE_ENNEMIS_ASTEROIDES`, `creer_flotte_asteroides`) ;
`src/gameplay/partie.py` (`DEGATS_ASTEROIDES`, `subir_degats_module`, `combat_aventure_asteroides`,
`_joueur_depuis_partie` factorisée avec `combat_depuis_partie`) ; `src/ui/ecran_aventure_asteroides.py`
(PC) + `main.py:_ouvrir_aventure_asteroides` ; côté web `web/bridge.py`
(`constantes_aventure_asteroides_web` expose `DEGATS_ASTEROIDES` pour le texte des choix avant de
les jouer, plutôt que dupliqué en dur dans `web/app.js`, cf. CLAUDE.md ;
`subir_degats_module_asteroides_web` ; `carte_offerte_asteroides_web` — tirage et résolution de
l'id de la carte dans le même appel, sur le même `charger_cartes()`, pour éviter tout problème
d'identité entre deux chargements distincts, cf. `id_de_carte` — piège réel rencontré côté PC en
construisant cet écran ; `prendre_carte_offerte_asteroides_web` ; `combat_aventure_asteroides_web` ;
`terminer_aventure_asteroides_web`) + `web/app.js` (`ouvrirAventureAsteroidesPartie` et fonctions
associées)

**Trois lunes** — **implémentée** (fond `assets/aventure/trois_lunes.png`) — "Un havre de paix au
milieu de la galaxie [...]. Il est temps de faire une pause." Trois choix, chacun résolu
immédiatement (pas de séquence), retour direct au Choix du prochain niveau (bouton "Continuer") :
- *Réparer le vaisseau* : +`PV_REPARATION_VAISSEAU` (5) PV à **chaque** module équipé, plafonné à
  son pv_max chacun (`reparer_vaisseau`, nouveau côté moteur : soin groupé, distinct de
  `reparer_module`, §2.2, qui ne cible qu'un seul module choisi)
- *Améliorer* : même effet que `ameliorer_module` (+`PV_AMELIORATION`, §2.2) mais **gratuit**
  (`ameliorer_module_aventure`, aucun coût en Argent contrairement à la Station service — l'effet
  commun aux deux est factorisé dans `_effet_ameliorer_module`), sur le module cliqué par le joueur
- *Bricoler* : retire une carte choisie par le joueur de son deck réel (`retirer_carte`, nouveau
  côté moteur : opération inverse de `ajouter_carte`, §2.4 étape 6). Cartes regroupées par id (pas
  par nom comme `regrouper_cartes`/l'écran "deck en entier", §6) pour retirer un exemplaire précis

`src/gameplay/partie.py` (`PV_REPARATION_VAISSEAU`, `reparer_vaisseau`, `ameliorer_module_aventure`,
`retirer_carte`) ; `src/ui/ecran_aventure_trois_lunes.py` (PC, écran à état interne `etape` : "choix"
-> "choix_module"/"choix_carte" -> "resolu") + `main.py:_ouvrir_aventure_trois_lunes` ; côté web
`web/bridge.py` (`constantes_aventure_trois_lunes_web` expose PV_REPARATION_VAISSEAU/PV_AMELIORATION
pour le texte des choix avant de les jouer, plutôt que dupliqués en dur dans `web/app.js`, cf.
CLAUDE.md ; `deck_groupe_par_id_partie_web` ; `reparer_vaisseau_aventure_web` ;
`ameliorer_module_aventure_web` ; `retirer_carte_aventure_web` ; `terminer_aventure_trois_lunes_web`)
+ `web/app.js` (`ouvrirAventureTroisLunesPartie`/`rendreAventureTroisLunes` et les fonctions de clic
associées)

**Police** — **implémentée** (fond `assets/aventure/police.png`) — "Pas de bol, votre dernier achat
n'est pas aux normes [...]." Une carte est tirée au hasard du deck réel du joueur
(`tirer_carte_deck`, nouveau côté moteur : tirage dans le deck possédé, contrairement à
`tirer_carte_recompense` qui tire dans un pool de récompense) et affichée **avant** les choix
(contrairement aux deux autres Aventures) — dans le même format qu'une carte en combat (image en
haut, texte en dessous, non cliquable), pas dans le format ligne image+texte des choix en dessous,
pour ne pas donner l'impression que c'est elle-même une option :
- *Confiscation* : retire cette carte du deck (`retirer_carte`, réutilisée de Trois lunes/Bricoler)
- *Mettre aux normes* : coûte un montant fixe en Argent (`COUT_METTRE_AUX_NORMES`, 10 €, cf. §9.1)
  plutôt qu'un pourcentage du prix de vente en magasin comme envisagé initialement — abandonné, la
  Planète commerciale n'ayant pas de prix par carte (§9.1) ; garde la carte si l'Argent est
  suffisant (`payer_mise_aux_normes`), sinon reste sur l'écran avec un message d'erreur
- *Détourner l'attention* : tire une **seconde** carte au hasard qui remplace la première affichée,
  puis revient au même écran avec seulement les 2 choix restants (Confiscation/Mettre aux normes —
  "Détourner" ne peut être choisi qu'une fois **par Aventure**, pas par run : état purement local à
  l'écran, rien de persisté sur `Partie`)

`src/gameplay/parcours.py` (`tirer_carte_deck`) ; `src/gameplay/partie.py`
(`COUT_METTRE_AUX_NORMES`, `payer_mise_aux_normes`) ; `src/ui/ecran_aventure_police.py` (PC, écran à
état interne `etape` : "choix" -> "resolu") + `main.py:_ouvrir_aventure_police` ; côté web
`web/bridge.py` (`constantes_aventure_police_web` expose `COUT_METTRE_AUX_NORMES` pour le texte du
choix avant de le jouer, plutôt que dupliqué en dur dans `web/app.js`, cf. CLAUDE.md ;
`tirer_carte_police_web` — appelée à l'ouverture de l'écran et de nouveau au choix "Détourner
l'attention" ; `confiscation_police_web` ; `mettre_aux_normes_police_web` renvoie
`{"partie": ..., "succes": bool}`, même convention que les actions payantes qui peuvent échouer ;
`terminer_aventure_police_web`) + `web/app.js` (`ouvrirAventurePolicePartie`/`rendreAventurePolice`
et les fonctions de clic associées)

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
- **PV / Bouclier** : affichés par de petites pastilles rondes (rouge pour les PV, bleue pour le Bouclier) flottant juste au-dessus de chaque case, jamais superposées à l'image (validé en POC)
- **Munitions restantes** (§3.6) : affichées sur la carte comme le coût en électricité, dans une pastille ronde **verte** — uniquement pour les cartes à munitions limitées (rien affiché pour les munitions illimitées, comportement par défaut)

### 8.3 Interaction de jeu d'une carte

**Le jeu se joue entièrement à la souris.**

1. Clic sur une carte de la main → la carte se **surligne** (état "armée")
2. Clic sur une **cible valide** → la carte se résout, part en défausse, la surbrillance disparaît
3. Pour les cartes sans cible unique (Alliés multiples, Ennemis multiples, Module principal, effet
   sur tout un camp) : la cible précise du clic ne compte pas pour l'effet, mais **un clic de
   confirmation reste nécessaire** sur n'importe quelle case vivante du bon camp (allié ou ennemi) —
   pas de résolution automatique au seul clic sur la carte, pour éviter qu'un clic accidentel ne la
   joue (validé dans le POC). **Ce flux de clic/tap doit rester identique entre la
   version PC et la version web/iOS** (cf. CLAUDE.md, "Deux façons de jouer")
4. **Fin de tour** : un bouton cliquable "Fin de tour" permet au joueur de terminer son tour à tout moment, même s'il lui reste de l'électricité ou des cartes jouables
5. **Retour visuel des effets** : chaque effet résolu (carte jouée ou attaque ennemie) affiche un popup `+N`/`-N` pendant quelques secondes sur la ou les cases touchées, avec le montant **réellement appliqué** (plafonné par les PV+Bouclier restants pour les dégâts, par le PV max pour le soin) plutôt que la valeur nominale de la carte — validé en POC

---

## 9. Points encore à trancher

### 9.1 Design / gameplay

- Contenu exact de la Planète commerciale (uniquement des cartes, ou aussi d'autres bonus ?) reste
  à définir (§2). Contenu de l'Aventure : 3 premières aventures spécifiées (Astéroïdes/Trois
  lunes/Police), voir §2.5 — **les trois implémentées** (à en écrire d'autres pour varier le pool)
- Montants d'Argent (récompense de combat, coût des actions de Station service, Argent de départ) :
  **tranchés et implémentés**, voir §2.1/§2.2 — valeurs inventées faute de spec précise à l'origine
  de cette décision, à ajuster en playtest si besoin. Même situation pour le coût de "Mettre aux
  normes" (Aventure Police, §2.5) : **10 € inventés par symétrie avec les autres montants,
  implémenté**
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
- `config/` : contenu du jeu décrit en JSON (modules, ennemis, cartes), référençant les images d'`assets/` — détail du format dans la docstring de `src/gameplay/donnees.py`
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
- Planète commerciale n'a pas encore de contenu propre (§2.4, étape 9, §9.1) : l'écran générique
  (`EcranEtapePlaceholder`) la représente, sans autre effet que d'avancer au niveau suivant.
  L'Aventure a désormais sa propre implémentation pour ses trois variantes (Trois lunes, Astéroïdes,
  Police, §2.5)
- Le run s'arrête réellement au Niveau 10 dans l'état actuel (décision utilisateur, provisoire,
  voir §2) : la Victoire finale (§2.4, étape 11) marque la partie `TERMINEE` sans proposer de
  continuation au-delà de ce niveau
- La flotte ennemie d'un combat (Prime ou Boss) reste toujours tirée entièrement au hasard
  (`combat_depuis_partie`/`creer_flotte`), sans appliquer les règles de difficulté par niveau du
  §2.3/§3.2 (nombre d'ennemis, tailles S/M/L) — reste un tirage de démonstration
- Écart PC/web sur la conservation des parties `TERMINEE` (voir "Partie" plus haut) : à corriger si
  un écran d'historique est construit côté web
- `argent` progresse désormais via les combats gagnés et la Station service (§2.1/§2.2) ; la Planète
  commerciale n'a toujours aucun effet dessus, son contenu n'étant pas construit (§9.1)

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
au moment de la rédaction la plus récente de cette section) ; les cartes restantes
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
  allié, §12.6, pour rester déterministe)
- `SOI_MEME` : l'ennemi qui exécute l'Action (uniquement pertinent pour `POSE_BUFF`)

### 13.2 Bouclier miroir (`ActionCarte.BOUCLIER_MIROIR`)

Buff posé sur un module du joueur (ennemi Miroir). Tant qu'il est actif, une attaque reçue par ce
module est en partie **renvoyée à l'attaquant** : jusqu'à la valeur du bouclier miroir, les dégâts
sont retirés à l'ennemi attaquant plutôt qu'au module protégé ; le reste (si les dégâts dépassent la
valeur du bouclier miroir) s'applique normalement au module. Se consomme comme un bouclier classique
(sa valeur diminue à chaque dégât renvoyé, l'instance est retirée à 0) ; plusieurs instances peuvent
coexister sur un même module, consommées dans l'ordre de pose (`Combat._consommer_bouclier_miroir`).
Uniquement pris en compte côté résolution du tour ennemi (`Combat._resoudre_attaque`) : le joueur ne
s'attaque jamais lui-même, cette mécanique n'a de sens que pour une attaque ennemie.

### 13.3 Les 5 ennemis (`config/ennemis.json`)

Remplacent entièrement les 3 ennemis placeholder du POC (ENM_1/2/3, retirés) :

| Ennemi | PV | Comportement |
| --- | --- | --- |
| Pat le Pirate | 50 | Attaque 5 dégâts par tour, cible de proximité |
| Le nettoyeur | 25 | Attaque 7 dégâts, **2 fois** par tour (`repetitions=2`), cible de proximité |
| Petit Jean | 100 | Attaque 2 dégâts par tour (proximité) ; tous les 2 tours (à partir du tour 1), se pose 3 bouclier pendant 2 tours |
| Le puzzle | 50 | Attaque 5 dégâts **tous les modules du joueur** par tour (zone) |
| Miroir | 50 | Chaque tour, pose un Bouclier miroir de valeur 5 (persistant) sur un module allié tiré au hasard (colonne avant sinon arrière) |

Valeurs de PV/dégâts inventées faute de spec numérique précise (à ajuster à l'équilibrage) — à
signaler comme telles, cf. règle du fichier `CLAUDE.md`.

**Préférence de placement en flotte** (`SpecEnnemi.placement`, purement une préférence de
composition, pas un attribut de l'`Ennemi` en combat) :

- Le nettoyeur (`PROTEGE_ARRIERE`) : placé de préférence en colonne arrière
- Petit Jean (`PROTECTEUR_AVANT`) : placé de préférence en colonne avant, pour protéger les autres
- Les 3 autres (Pat le Pirate, Le puzzle, Miroir) : aucune préférence — placés dans les emplacements
  restants, colonne avant en priorité puis arrière (choix par défaut, pas de spec précise)

### 13.4 Composition des flottes de combat

- **Combat Intermédiaire** (Prime) : 1 ennemi tiré au sort (parmi les 5) jusqu'au niveau 5 inclus,
  puis 2 ennemis tirés au sort à partir du niveau 6 (`config_poc.creer_flotte_prime`)
- **Combat de Boss** : composition fixe (pas de tirage) — 2x Petit Jean en colonne avant (gauche et
  droite), Le nettoyeur et Le puzzle en colonne arrière (gauche et droite) ; les deux emplacements
  du milieu restent vides (`config_poc.creer_flotte_boss`)

### 13.5 Points de vie des modules (fin du mode test)

Le combat ne tourne plus en "mode test" (PV artificiellement gonflés) : les PV définis dans
`config/modules.json` s'appliquent réellement. Valeurs actuelles (inventées faute de spec précise,
à ajuster) : **50 PV** pour le module principal, **30 PV** pour chaque module secondaire.
