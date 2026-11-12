# Space Fight — Aventures (§2.5)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

---

### 2.5 Aventures (contenu)

Contenu concret des 3 premières Aventures spécifiées à ce jour — brouillon détaillé dans
l'ancien registre `specs/cartes_legacy.xlsx`, onglet "Aventures" (archivé, plus maintenu ; cette
section fait foi). **Les trois Aventures (Trois lunes, Astéroïdes, Police) sont
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

> **Refonte branchée côté gameplay (PR 1, 2026-11-12, décision utilisateur du 2026-11-11 n° 3)** :
> les deux chocs de « Traverser » touchent **toujours le principal** (`subir_degats_principal`,
> `second_choc_asteroides(partie, cartes, aleatoire)`), le choix du module disparaît, et ils lui
> **laissent toujours au moins 1 PV** (`PV_MIN_APRES_ASTEROIDES`, décision utilisateur du
> 2026-11-12 : un combat ne commence jamais avec un principal détruit) ; la carte
> offerte est rattachée au principal. « Affronter les pirates » : 3 ennemis de la refonte placés
> selon leur préférence (`flotte_new.flotte_asteroides`). Écrans PC et web à adapter (PR 2 et 3).
- Choix 1, *Traverser le champ d'astéroïdes* (**ancienne règle, remplacée par la note ci-dessus**
  pour le module touché, la fonction et le plancher de PV ; la séquence d'écrans reste à adapter
  aux PR 2 et 3) : séquence en 3 temps sur le même écran, chaque étape validée par un bouton
  "Continuer" :
  1. Le joueur clique un module (`_dessiner_choix_module`/`choix_module`) : -`DEGATS_ASTEROIDES` (5)
     PV appliqués immédiatement (`subir_degats_module`, dégâts hors combat, plafonnés à 0,
     opération inverse de `reparer_module`/`reparer_vaisseau`), puis affichage d'un message de
     confirmation + bouton "Continuer" (étape `sequence_2`)
  2. Au clic sur "Continuer" : **`second_choc_asteroides`** (`src/gameplay/partie.py`) inflige
     -`DEGATS_ASTEROIDES` PV supplémentaires (même module) **et** tire, en un seul appel, une carte
     dans le pool complet (`pool_toutes_cartes`/`tirer_carte_recompense`, §6) proposée gratuitement
     — c'est cette fonction gameplay qui décide seule si une carte est offerte, ni PC ni web ne
     retirent cette décision eux-mêmes (cf. CLAUDE.md, gameplay commun aux deux interfaces ;
     décision initialement dupliquée indépendamment côté PC et web, corrigée après relecture)
  3. Si une carte a été offerte, elle est présentée (boutons "Prendre"/"Passer", étape
     `sequence_3`) — gratuite et hors du flux de récompense standard de fin de combat. Si le pool
     était vide (`second_choc_asteroides` renvoie `None`), l'étape `sequence_3` est sautée
     directement vers `resolu`
- Choix 2, *Affronter les pirates* : lance un combat scripté contre `NOMBRE_ENNEMIS_ASTEROIDES` (3)
  ennemis (`combat_aventure_asteroides`/`flotte_new.flotte_asteroides`) — approximation décidée en
  attendant la taille S/M/L par ennemi (absente de `config/ennemis.json`, cf. §3.2/§9.1/§10.3) :
  ennemis tirés du pool existant sur les 3 premières cases de la grille (colonne Avant), plutôt que
  le tirage standard d'un combat Prime (grille complète, `combat_depuis_partie`). Délègue
  entièrement au pipeline Combat existant (étape 5/6 : victoire → Argent + carte, comme un Prime
  normal ; défaite → même traitement qu'un combat normal) via `main.py:_ouvrir_combat`
  (paramètre `combat` optionnel, déjà construit par l'appelant) / `web/bridge.py:combat_aventure_asteroides_web`
  (même variable globale `combat` que `continuer_partie_web`, reste du pipeline de fin de combat
  inchangé)
- Pas de 3ᵉ choix (binaire assumé)

`src/gameplay/flotte_new.py` (`NOMBRE_ENNEMIS_ASTEROIDES`, `flotte_asteroides`) ;
`src/gameplay/partie.py` (`DEGATS_ASTEROIDES`, `subir_degats_module`, **`second_choc_asteroides`**
— 2e choc + tirage de la carte offerte en un seul appel, `cartes` reçu en paramètre plutôt que
rechargé en interne ; l'id de la carte offerte est lu directement sur `Carte.id` (§6) —,
`combat_aventure_asteroides`, `_joueur_depuis_partie`
factorisée avec `combat_depuis_partie`) ; `src/ui/ecran_aventure_asteroides.py` (PC, garde une
instance `random.Random` explicite en attribut — jamais recréée à chaque appel, cf. CLAUDE.md
"Déterminisme du tirage aléatoire") + `main.py:_ouvrir_aventure_asteroides` ; côté web
`web/bridge.py` (`constantes_aventure_asteroides_web` expose `DEGATS_ASTEROIDES` pour le texte des
choix avant de les jouer, plutôt que dupliqué en dur dans `web/app.js`, cf. CLAUDE.md ;
`subir_degats_module_asteroides_web` pour le 1er choc ; **`second_choc_asteroides_web`** pour le
2e — sérialise le résultat de `second_choc_asteroides`, ne recalcule jamais si une carte est
offerte ; `prendre_carte_offerte_asteroides_web` ; `combat_aventure_asteroides_web` ;
`terminer_aventure_asteroides_web`) + `web/app.js` (`ouvrirAventureAsteroidesPartie` et fonctions
associées)

**Trois lunes** — **implémentée** (fond `assets/aventure/trois_lunes.png`) — "Un havre de paix au
milieu de la galaxie [...]. Il est temps de faire une pause." Trois choix, chacun résolu
immédiatement (pas de séquence), retour direct au Choix du prochain niveau (bouton "Continuer") :
- *Réparer le vaisseau* (**refonte branchée, PR 1** : soigne **le principal seul**, seul module dont
  les PV persistent, décision n° 3 du 2026-11-11 ; ancienne règle ci-après) :
  +`PV_REPARATION_VAISSEAU` (5) PV à **chaque** module équipé, plafonné à
  son pv_max chacun (`reparer_vaisseau`, nouveau côté moteur : soin groupé, distinct de
  `reparer_module`, §2.2, qui ne cible qu'un seul module choisi)
- *Améliorer* : même effet que `ameliorer_module` (+`PV_AMELIORATION`, §2.2) mais **gratuit**
  (`ameliorer_module_aventure`, aucun coût en Argent contrairement à la Station service — l'effet
  commun aux deux est factorisé dans `_effet_ameliorer_module`), sur le module cliqué par le joueur
- *Bricoler* : retire une carte choisie par le joueur de son deck réel (`retirer_carte`, nouveau
  côté moteur : opération inverse de `ajouter_carte`, §2.4 étape 6). Cartes regroupées par id via
  `regrouper_cartes` (même regroupement que l'écran "deck en entier", §6), l'id de la carte cliquée
  (`Carte.id`) étant passé à `retirer_carte`

`src/gameplay/partie.py` (`PV_REPARATION_VAISSEAU`, `reparer_vaisseau`, `ameliorer_module_aventure`,
`retirer_carte`) ; `src/ui/ecran_aventure_trois_lunes.py` (PC, écran à état interne `etape` : "choix"
-> "choix_module"/"choix_carte" -> "resolu") + `main.py:_ouvrir_etape` ; côté web
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
- *Mettre aux normes* : coûte un montant fixe en Argent (`COUT_METTRE_AUX_NORMES`, 10 € inventés
  par symétrie avec les autres montants du jeu, à ajuster en playtest si besoin) plutôt qu'un
  pourcentage du prix de vente en magasin comme envisagé initialement — abandonné, la
  Planète commerciale n'ayant pas de prix par carte (§9.1) ; garde la carte si l'Argent est
  suffisant (`payer_mise_aux_normes`), sinon reste sur l'écran avec un message d'erreur
- *Détourner l'attention* : tire une **seconde** carte au hasard qui remplace la première affichée,
  puis revient au même écran avec seulement les 2 choix restants (Confiscation/Mettre aux normes —
  "Détourner" ne peut être choisi qu'une fois **par Aventure**, pas par run)

L'état de résolution (carte actuellement affichée, disponibilité de "Détourner") est possédé par
le gameplay — **`EtatAventurePolice`** (`src/gameplay/partie.py`, dataclass
`id_carte_actuelle`/`detourner_disponible`), jamais par l'écran PC ni par des variables JS
indépendantes : `demarrer_aventure_police` l'initialise (1er tirage), `detourner_aventure_police`
le fait évoluer (renvoie `False` sans rien faire si "Détourner" a déjà été utilisé). PC
(`EcranAventurePolice.etat_police`) et web (`web/bridge.py:etat_aventure_police`, variable globale
— même principe que `combat`) gardent chacun une référence à cet état plutôt que de suivre
`detourner_disponible` séparément (cf. CLAUDE.md, gameplay commun aux deux interfaces — décision
initialement dupliquée indépendamment côté PC et web, corrigée après relecture).

`src/gameplay/parcours.py` (`tirer_carte_deck`) ; `src/gameplay/partie.py`
(`COUT_METTRE_AUX_NORMES`, `payer_mise_aux_normes`, `EtatAventurePolice`,
`demarrer_aventure_police`, `detourner_aventure_police`) ; `src/ui/ecran_aventure_police.py` (PC,
écran à état interne `etape` : "choix" -> "resolu", garde une instance `random.Random` explicite en
attribut) + `main.py:_ouvrir_etape` ; côté web `web/bridge.py`
(`constantes_aventure_police_web` expose `COUT_METTRE_AUX_NORMES` pour le texte du choix avant de
le jouer, plutôt que dupliqué en dur dans `web/app.js`, cf. CLAUDE.md ;
`demarrer_aventure_police_web` — appelée à l'ouverture de l'écran ; `detourner_police_web` — renvoie
aussi `succes`/`detourner_disponible`, JS ne décide jamais lui-même si "Détourner" reste possible ;
`confiscation_police_web` — retire `etat_aventure_police.id_carte_actuelle`, plus besoin de le
transmettre depuis JS ; `mettre_aux_normes_police_web` renvoie `{"partie": ..., "succes": bool}`,
même convention que les actions payantes qui peuvent échouer ; `terminer_aventure_police_web`) +
`web/app.js` (`ouvrirAventurePolicePartie`/`rendreAventurePolice` et les fonctions de clic
associées, qui ne font plus que refléter la dernière réponse du gameplay)
