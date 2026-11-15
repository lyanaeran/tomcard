# Space Fight — Parcours (boucle de run) (§2.1 à §2.4)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

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

- Après chaque combat gagné, le joueur gagne de l'**Argent**, ressource de run distincte de
  l'Électricité (combat.md §3.3) : **5 €** par ennemi détruit (`ARGENT_PAR_ENNEMI_TUE`,
  `partie.gagner_argent_combat`). Une partie démarre avec **7 €** (`ARGENT_DEPART`). Montants
  inventés, à ajuster.
- Il gagne aussi une **carte**, garantie : une candidate par module équipé, ou Passer
  (modules-cartes.md §6).
- **Défaite** : écran dédié, pas de carte ; la partie est terminée.
- Tout cela est appliqué **une seule fois, dès la fin du combat**, par
  `deroulement.conclure_combat` : PV du principal reportés (`partie.reporter_combat`), Argent,
  candidats de récompense notés dans la partie (`Partie.recompense`) et sauvegardés. Une partie
  quittée sur l'écran de récompense **reprend à cet écran**, jamais au combat déjà gagné
  (`Ecran.RECOMPENSE`, §2.4).
- Le joueur choisit ensuite l'étape suivante (§2.3).

### 2.2 Station service (garage)

Quatre actions, **20 € chacune** (`COUT_ACTION_STATION_SERVICE`, valeur inventée) :

- **Réparer** : rend **20 PV au module principal** (plafonné à son PV max). Toujours le
  principal, **sans sélection** : c'est le seul module dont les PV persistent d'un combat à
  l'autre, un secondaire repart à ses PV max (décision utilisateur, 2026-11-11 ; combat.md §3.4).
- **Améliorer** : +10 au PV max du module sélectionné (et +10 PV pour le principal). Sur tout
  module ; plafond éventuel à trancher (a-trancher.md §9.1).
- **Mettre à jour** : fait monter le **palier** du module sélectionné (1 → 2 → 3), qui ouvre les
  raretés qu'il propose en récompense : palier 1 Communes, palier 2 + Rares, palier 3 +
  Légendaires (modules-cartes.md §6 ; décision utilisateur, appliquée le 2026-11-13).
- **Déplacer** : change l'emplacement d'un module secondaire (jamais le principal). Vers un
  emplacement vide, il y est déplacé ; vers un emplacement occupé, les deux modules échangent
  leur place. Ses cartes le suivent (modules-cartes.md §12.4).

Règles communes (`src/gameplay/partie.py` : `reparer_principal`, `ameliorer_module`,
`mettre_a_jour_module`, `deplacer_module`) :

- Chaque action renvoie un **`ResultatStation`** : `OK`, `ARGENT_INSUFFISANT` ou `INUTILE`. Dans
  les deux derniers cas, rien n'est modifié ni payé.
- **Une action sans effet est refusée sans payer** (proposition, 2026-11-13) : Réparer quand le
  principal a tous ses PV, Mettre à jour au palier 3.
- L'écran affiche « Argent insuffisant ! » ou « Déjà au maximum ! » **d'après cette raison**, sans
  jamais revérifier la condition lui-même.
- Améliorer et Mettre à jour progressent **par exemplaire** de module : deux exemplaires du même
  type peuvent avoir des PV max et des paliers différents.

#### Écran Station service (PC et web)

- Les cinq emplacements en **ligne** (principal + 4, « Emplacement vide » pour un emplacement
  libre), les quatre actions en dessous avec leur prix, un bouton « J'ai terminé » qui passe au
  niveau suivant (§2.4).
- Le joueur clique un module pour le sélectionner, puis une action. **Réparer** s'applique
  directement au principal, sans sélection. **Déplacer** : cliquer l'action arme le déplacement,
  puis cliquer l'emplacement de destination ; recliquer le module source, ou choisir une autre
  action, l'annule.
- Chaque action réussie affiche un popup sur le module (« +20 PV », « +10 PV max », « Niveau 2 »),
  calculé d'après l'état avant et après ; le module est ensuite désélectionné.
- Les icônes des actions portent leur nom (`assets/station_service/avec_texte/`) ; une action
  trop chère est grisée (simple affichage : c'est le résultat de l'action qui décide).
- La carte du principal utilise `assets/modules/principal_avant.png` (recadrage sur l'avant du
  vaisseau), comme l'accueil du joueur et l'écran Vaisseau.
- Code : `src/ui/ecran_station_service.py` (PC) ; `src/web/bridge.py` (`reparer_principal_web`,
  `ameliorer_module_web`, `mettre_a_jour_module_web`, `deplacer_module_web`) et
  `src/web/app.js` (`cliquerModuleStation`, `cliquerActionStation`).

### 2.3 Structure par niveaux

Le run est une suite de **niveaux numérotés** (1, 2, 3...), chacun une étape. Décision utilisateur,
remplace les pistes encore ouvertes en §2 pour la Station service et la cadence des Boss :

- **Niveau 1** — **Choix de module**, obligatoire, pas de tirage d'étape : 3 modules **différents**
  tirés au sort parmi le pool (moins si le pool en compte moins : un seul, le Lanceur de missiles,
  tant que seuls deux modules sont jouables, cf. modules-cartes.md §4), le joueur en choisit un (2ᵉ slot équipé, en plus du module de base —
  voir §5). C'est ce choix qui pourvoit le 2ᵉ des "2 slots" de départ mentionnés en §5.
  **Implémenté** et relié à l'orchestration du parcours (§2.4) pour une vraie partie :
  `src/gameplay/parcours.py` (tirage), `src/ui/ecran_choix_module.py` (PC),
  `main.py:_ouvrir_choix_module` (equipe le module choisi, avance le niveau, sauvegarde) ;
  côté web `src/web/bridge.py:choisir_module_partie_web` + `src/web/app.js:ouvrirChoixModulePartie`/
  `choisirModule`. Écran présenté **empilé
  verticalement, image carrée à gauche et rectangle de texte (nom + `description`) à droite**, même
  convention que le choix du prochain niveau (§2.3 ci-dessus) et les choix d'Aventure/Station
  service — voir §4 pour le détail du champ `description` par module et l'exclusion des modules
  sans deck de cartes de ce tirage — fond de combat réutilisé en placeholder (décision
  utilisateur), à remplacer par un fond dédié
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
  remplace pas. **Implémenté** (`flotte.flotte_prime`/`nombre_ennemis_prime`, §13.4), de
  même que la composition fixe du Boss (§13.4). Progression au-delà de 2 (après le niveau 10 ?)
  pas encore définie
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

**Où vit l'enchaînement (décision utilisateur)** : dans `src/gameplay/deroulement.py`, **jamais**
dans `main.py`, `src/ui/` ou `src/web/`. Ce module décide de l'écran suivant (énumération `Ecran`) et
applique les règles de chaque transition :

| Fonction | Rôle |
|---|---|
| `ecran_de_reprise` | « Continuer » ou nouvelle partie : choix de module au Niveau 1 sans 2e module ; écran de récompense (`Ecran.RECOMPENSE`) si un combat gagné attend encore le choix de sa carte (2026-11-13) ; sinon choix du niveau |
| `candidats_choix_module` / `choisir_module` / `resoudre_carte_module` | Niveau 1 : modules proposés, équipement + cartes proposées, carte ajoutée (ou Passer) puis niveau suivant |
| `propositions_niveau` / `ecran_pour_etape` | Étapes proposées (déterministes par graine et niveau), écran ouvert par l'étape choisie (tirage de l'Aventure) |
| `terminer_etape` | Fin d'une étape hors combat (Station, Aventure, Planète commerciale) : niveau suivant |
| `conclure_combat` | Une seule fois à la fin d'un combat : PV reportés, Argent et candidats de récompense si victoire |
| `resoudre_fin_combat` | Défaite → partie terminée, accueil ; victoire → carte ajoutée, puis victoire finale (Boss) ou niveau suivant |
| `terminer_victoire_finale` | Partie terminée, accueil |

`main.py` (`_aller_a`) et `src/web/app.js` (`allerA`, via `src/web/bridge.py` qui renvoie
`{partie, ecran}`) ne font que sauvegarder la partie et afficher l'écran renvoyé ; la simulation
d'équilibrage (`outils/simulation/`, cf. [simulation.md](simulation.md)) appelle les mêmes
fonctions. Tout tirage est injecté (`random.Random`) : PC et web passent un générateur non seedé,
la simulation un générateur à graine.

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
  plus de `combat` ; la barre y
  occupe désormais la même position par défaut que sur les autres écrans (plus de bandeau du haut à
  éviter, cf. §8.1/§8.3) — `FenetreCombat` empile juste en dessous ses propres contrôles
  (`_dessiner_controles_combat` : Électricité, tour suivant, Quitter), via `barre_laterale.
  HAUTEUR_CONTENU` (hauteur exportée du contenu de la barre).
- Web (`src/web/app.js` : `actualiserBarreLaterale`/`ouvrirSurvolDeck`/`ouvrirSurvolVaisseau`) :
  `#ecran-deck`/`#ecran-vaisseau` passent en `position: fixed` (classe `.ecran-survol`,
  `src/web/style.css`) pour se superposer à l'écran actuellement affiché sans passer par
  `masquerTousLesEcrans()` (qui le masquerait) — même principe que côté PC, sans fenêtre
  additionnelle puisque le web n'affiche qu'un seul écran DOM visible à la fois. En Combat, un
  élément séparé `#controles-combat` (Électricité/tour suivant/Quitter) s'empile sous
  `#barre-laterale` quand elle est visible, ou prend sa place par défaut sinon (portrait, écran trop étroit ou chevauchement, cf. juste en dessous) — élément
  distinct plutôt que nichée dans la barre elle-même, pour que mettre fin à son tour reste possible
  même quand la barre (Niveau/Argent/Deck/Vaisseau, moins essentielle) est masquée. **Simplification
  web** (écart documenté, cf. CLAUDE.md) : barre étroite (52px, choisie expressément pour inclure
  l'iPhone 12/13 mini — 812px de large en paysage, remonté par l'utilisateur comme resté sans barre
  avec une première largeur de 60px/seuil 820px) et **masquée sous 760px de large en paysage, et
  systématiquement en portrait** — mesuré empiriquement (Playwright) comme le seuil au delà duquel
  elle ne chevauche jamais la grille de 5 modules (Station service et l'étape "choix_module" des
  Aventures Trois lunes/Astéroïdes) ; seul l'iPhone SE et plus petit (667px) reste sous ce seuil, la
  barre y est simplement absente. En Combat spécifiquement, la largeur du bloc vaisseau dépend aussi de la
  hauteur d'écran (`--taille-case`) : un seuil de largeur fixe ne suffisant pas à garantir l'absence
  de chevauchement sur tous les formats (fenêtre large et haute, tablette en paysage...),
  `actualiserBarreLaterale`/`barreChevaucheVaisseau` vérifient le chevauchement réel après affichage
  (comparaison des rectangles DOM) et masquent la barre au lieu de deviner un second seuil.
- **`EcranVaisseau`** : cliquer/taper un module équipé (non vide) affiche son nom et sa
  `description` (§4) dans une infobulle temporaire (4 secondes), superposée au-dessus de la case
  cliquée. PC (`src/ui/ecran_vaisseau.py`) : affichée au-dessus du **point cliqué** (même
  infobulle que le survol en combat, `fenetre.py:_infobulle_au_curseur`, §8.2) ; réutilise le minuteur `AnimationPopup` existant
  (`src/ui/animation.py`), avec une durée dédiée `DUREE_INFOBULLE_MODULE` plus longue que celle
  des popups de combat (le temps de lire la phrase) ; nécessite une boucle
  `pyglet.clock.schedule_interval` que cet écran n'avait pas jusqu'ici. Web (`src/web/app.js`) : réutilise
  le panneau `position: fixed` centré déjà utilisé pour `#info-carte`/`#info-case`/`#info-carte-deck`
  (nouveau `#info-carte-vaisseau` dans `index.html`), rempli par `afficherDescriptionModuleVaisseau`
  et effacé après le même délai via `setTimeout` ; `src/web/bridge.py:infos_vaisseau_web` inclut
  désormais `description` par module équipé pour l'alimenter.

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
     de module (étape 4) ; sinon → Choix du prochain niveau (étape 3) pour le niveau courant. Un combat gagné dont la
     carte de récompense n'a pas encore été choisie reprend à l'écran de récompense
     (`Ecran.RECOMPENSE`). Un combat quitté en cours n'est pas sauvegardé : il recommence avec un
     nouveau tirage d'ennemis (a-trancher.md §9.1)
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
   page initiale, abandonnée une fois les icônes fournies sans texte) ; `src/web/bridge.py`
   (`choix_niveau_web`), `src/web/app.js` (`afficherChoixNiveau`/`choisirEtape`)
4. **Choix de module, Niveau 1** (implémenté en écran autonome, §2.3, **relié à la partie**) : une
   fois un module choisi, met à jour la partie (2ᵉ emplacement du vaisseau), puis → **Choix d'une
   carte du module** (décision utilisateur, **implémenté**) : jusqu'à 3 cartes candidates tirées
   dans le pool jouable non-Base de ce module tout juste équipé (`parcours.
   tirer_candidats_carte_module`, même tirage pondéré par rareté que la récompense de fin de combat,
   §6, sans doublon parmi les candidats), le joueur en choisit une à ajouter à son deck ou passe
   (bouton **Passer**, décision utilisateur — voir aussi §6) ; écran sauté directement (candidats vide, pool de ce module encore
   vide) sans action du joueur. Le niveau n'avance (1 → 2) qu'une fois ce choix résolu, puis →
   Choix du prochain niveau (étape 3). `src/ui/ecran_choix_carte_module.py` (PC),
   `main.py:_ouvrir_choix_carte_module` ; côté web `src/web/bridge.py`
   (`candidats_carte_module_web`/`resoudre_carte_module_web`) + `src/web/app.js`
   (`ouvrirChoixCarteModule`/`afficherChoixCarteModule`/`choisirCarteModule`/`passerCarteModule`)
5. **Combat** (implémenté en écran indépendant, `FenetreCombat`/`#app`, **relié à l'enchaînement**) :
   une fois le combat terminé (victoire ou défaite) → Fin de combat (étape 6)
6. **Fin de combat** (implémenté en écran autonome, §6, **relié à l'enchaînement**) :
   - Victoire : choix d'une carte candidate (une par module équipé, déjà rattachée à ce module,
     §6), ajoutée au deck, puis → Choix du prochain niveau (étape 3), sauf si le combat était un
     Boss → Victoire finale (étape 11), la partie étant alors **terminée tout de suite** (on ne
     peut pas rejouer le Boss ; proposition, 2026-11-13). Sans candidat, un bouton « Continuer »
     passe l'écran
   - Défaite : la partie est marquée `TERMINEE` **dès la fin du combat** (même statut qu'un abandon, décision utilisateur —
     pas de distinction victoire/défaite/abandon pour l'instant, cf. §10.3) → Écran de partie
     (étape 2), via un bouton "Continuer" (PC : clic n'importe où sur l'écran, cf.
     `src/ui/ecran_fin_combat.py`)
7. **Aventure** (détaillé en §2.5, **trois Aventures implémentées et reliées à l'enchaînement :
   "Trois lunes", "Astéroïdes" et "Police"** ; tirage uniforme non déterministe entre les trois via
   `tirer_type_aventure`, PC (`main.py`) et web (`ecran_pour_etape_web`)) : un choix résolu puis un
   bouton "Continuer" avance le niveau et revient au Choix du prochain niveau (étape 3), même
   principe que Station service — sauf le choix "Affronter les pirates" de l'Astéroïdes, qui délègue
   au pipeline Combat (étape 5) via un combat scripté plutôt que d'avancer directement.
   `src/ui/ecran_aventure_trois_lunes.py`/`src/ui/ecran_aventure_asteroides.py`/
   `src/ui/ecran_aventure_police.py` (PC) + `main.py:_ouvrir_etape`/
   `_ouvrir_aventure_asteroides`/`_ouvrir_aventure_police` ; côté web, les fonctions `*_web` de
   `src/web/bridge.py` et les fonctions `ouvrirAventure…Partie` de `src/web/app.js`
8. **Station service** (détaillé en §2.2, **implémenté et relié à l'enchaînement**) : Réparer /
   Améliorer / Mettre à jour / Déplacer un module, un bouton "j'ai terminé" avance le niveau et
   revient au Choix du prochain niveau (étape 3), même principe que la fin d'un combat gagné
9. **Planète commerciale** (contenu non préparé, §2/§9.1, **relié à l'enchaînement via un écran
   générique**) : un bouton "j'ai terminé" avance le niveau et revient au Choix du prochain niveau
   (étape 3) — en attendant un vrai contenu, l'écran se limite à afficher l'icône/description déjà
   utilisées au Choix du prochain niveau avec un message "Contenu pas encore défini pour cette
   étape." `src/ui/ecran_etape_placeholder.py` (PC) + `main.py:_ouvrir_etape` ; côté web
   `src/web/bridge.py` (`terminer_etape_placeholder_web`) + `src/web/app.js`
   (`ouvrirEtapePlaceholderPartie`/`terminerEtapePlaceholder`)
10. **Boss** (niveau 10, puis tous les 10 niveaux à terme — §2.3), atteint via la proposition
    unique "Combattre le Boss !" de l'étape 3 : réutilise l'écran Combat, contre le Boss des
    pirates (combat.md §13.4) → Victoire : Victoire finale (étape 11) ; Défaite : même
    traitement qu'un combat normal (étape 6, branche Défaite)
11. **Victoire finale** (**implémenté et relié à l'enchaînement**) : félicite le joueur, affiche son
    deck complet (même rendu que l'écran "deck en entier", §6, dupliqué plutôt que réutilisé
    littéralement — même convention que les autres écrans du parcours, chacun avec ses propres
    petits helpers de disposition) → bouton "Continuer" → Écran de partie (étape 2) ; la partie est déjà `TERMINEE`
    depuis l'étape 6. `src/ui/ecran_victoire_finale.py` (PC) + `main.py:_ouvrir_victoire_finale` ;
    côté web `src/web/bridge.py` (`terminer_victoire_finale_web`) + `src/web/app.js`
    (`ouvrirVictoireFinalePartie`, `terminerVictoireFinale`)
