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
"choix" -> "choix_module"/"choix_carte" -> "resolu" ; Astéroïdes : "choix" ->
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

**Astéroïdes** — **implémentée** (fond `assets/aventure/champ_asteroides.png`) — « Poursuivi par
des pirates de l'espace, vous n'avez plus le choix : vaincre ou périr ! À moins que... »

- Choix 1, *Traverser le champ d'astéroïdes* : séquence sur le même écran, chaque étape validée
  par « Continuer ».
  1. **Premier choc** : −`DEGATS_ASTEROIDES` (5) PV au **module principal** (`subir_degats_principal`),
     sans choix de module (décision utilisateur, 2026-11-11 : seul le principal garde ses PV).
  2. **Second choc** (`second_choc_asteroides`) : −5 PV au principal **et** tirage, dans le même
     appel, d'une carte offerte dans toutes les cartes jouables non Base, toutes raretés, sans
     palier de mise à jour. C'est cette fonction qui décide seule si une carte est offerte ; ni PC
     ni web ne refont le tirage.
  3. Si une carte est offerte : « Prendre » ou « Passer ». Elle est **rattachée au principal**
     (modules-cartes.md §12.4).
  - Les chocs **laissent toujours au moins 1 PV** au principal (`PV_MIN_APRES_ASTEROIDES`,
    décision utilisateur, 2026-11-12 : un combat ne commence jamais avec un principal détruit).
    Le message affiché donne les PV **réellement** perdus (différence avant / après).
- Choix 2, *Affronter les pirates* : combat contre `NOMBRE_ENNEMIS_ASTEROIDES` (3) ennemis, placés
  selon leur préférence (`combat_aventure_asteroides`, `flotte.flotte_asteroides`, combat.md
  §13.4), puis la même fin de combat qu'un Prime (Argent, carte, ou défaite).
- Pas de 3ᵉ choix.

Code : `src/gameplay/partie.py`, `src/gameplay/flotte.py` ; `src/ui/ecran_aventure_asteroides.py`
(PC, garde une instance `random.Random` en attribut) + `main.py:_ouvrir_aventure_asteroides` ;
côté web `src/web/bridge.py` (`premier_choc_asteroides_web`, `second_choc_asteroides_web`,
`prendre_carte_offerte_asteroides_web`, `combat_aventure_asteroides_web`) + `src/web/app.js`.

**Trois lunes** — **implémentée** (fond `assets/aventure/trois_lunes.png`) — « Un havre de paix au
milieu de la galaxie [...]. Il est temps de faire une pause. » Trois choix, chacun résolu
immédiatement, puis « Continuer » :

- *Réparer le vaisseau* : +`PV_REPARATION_VAISSEAU` (5) PV au **module principal**, plafonné à
  son PV max (`reparer_vaisseau` ; décision utilisateur, 2026-11-11 : seul le principal garde ses
  PV).
- *Améliorer un module* : même effet qu'Améliorer à la Station (+`PV_AMELIORATION`, parcours.md
  §2.2) mais **gratuit**, sur le module cliqué (`ameliorer_module_aventure`).
- *Bricoler* : retire du deck une carte choisie par le joueur (`retirer_carte`). Les cartes sont
  regroupées **par carte et par module** (une entrée par couple, avec le nom du module), et c'est
  ce couple (`CartePossedee`) qui est retiré.

Code : `src/gameplay/partie.py` ; `src/ui/ecran_aventure_trois_lunes.py` (PC) + `main.py:_ouvrir_etape` ;
côté web `src/web/bridge.py` (`reparer_vaisseau_aventure_web`, `ameliorer_module_aventure_web`,
`retirer_carte_aventure_web`, `constantes_aventure_trois_lunes_web`) + `src/web/app.js`.

**Police** — **implémentée** (fond `assets/aventure/police.png`) — « Pas de bol, votre dernier
achat n'est pas aux normes [...]. » Une carte est tirée au hasard dans le deck du joueur
(`tirer_carte_deck`) et affichée **avant** les choix, comme une carte en combat (non cliquable) :

- *Confiscation* : retire cette carte du deck (`retirer_carte`).
- *Mettre aux normes* : coûte `COUT_METTRE_AUX_NORMES` (10 €, valeur inventée) et garde la carte
  (`payer_mise_aux_normes`) ; sans assez d'Argent, l'écran reste ouvert avec un message.
- *Détourner l'attention* : tire une autre carte qui remplace la première, puis il ne reste que
  les deux autres choix (une seule fois **par Aventure**).

L'état de résolution (carte affichée, disponibilité de « Détourner ») est possédé par le gameplay :
**`EtatAventurePolice`** (`src/gameplay/partie.py` : `carte_actuelle`, un couple carte + module,
et `detourner_disponible`), initialisé par `demarrer_aventure_police` et modifié par
`detourner_aventure_police`. PC et web gardent une référence à cet état, jamais leurs propres
variables.

**Cas non géré** : avec un deck vide (après plusieurs « Bricoler » ou confiscations), le tirage
plante (a-trancher.md §9.1).

Code : `src/gameplay/parcours.py` (`tirer_carte_deck`), `src/gameplay/partie.py` ;
`src/ui/ecran_aventure_police.py` (PC) + `main.py:_ouvrir_etape` ; côté web `src/web/bridge.py`
(`demarrer_aventure_police_web`, `detourner_police_web`, `confiscation_police_web`,
`mettre_aux_normes_police_web`, `constantes_aventure_police_web`) + `src/web/app.js`.
