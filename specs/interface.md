# Space Fight — Interface de combat (§8)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md). Décrit l'écran de combat actuel des deux versions (PC :
`src/ui/fenetre.py`, `textes_combat.py` ; web : `src/web/app.js`, `bridge.py`) ; les choix
d'affichage faits au branchement de la refonte (refonte-branchement.md §4, §5.2, §5.4) ont été
reportés ici le 2026-11-14.*

---

## 8. Interface / écran de combat

**Règle générale** : l'affichage ne décide de rien. Cases valides d'une carte, carte jouable,
intentions des ennemis, modules visés, journal : tout vient de `Combat` (combat.md §3.10). PC et
web montrent le **même contenu** ; les écarts sont listés en §8.4.

### 8.1 Disposition générale (wireframe)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SPACE FIGHT — ÉCRAN DE COMBAT                                                    │
│ [Niveau/Argent/Deck/Vaisseau]                                                     │
│ [⚡ 3/3][►►][X][journal][Tour, piles]  ← barre latérale + contrôles, à gauche     │
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

- **Vaisseau du joueur** (haut gauche) : grille de **2 lignes (arrière/avant) x 3 colonnes (gauche/mid/droite)** (combat.md §3.1.1). La ligne **avant est tournée vers l'ennemi** (la plus proche du centre de l'écran), la ligne arrière est la plus éloignée. Le tout repose sur un **fond commun** qui regroupe visuellement les 5 emplacements. Le **module de base** occupe la colonne du milieu en entier (arrière-mid + avant-mid fusionnés) ; les 4 autres modules équipés prennent FG/FD/AG/AD
- **Flotte ennemie** (haut droite) : grille symétrique 2x3, 6 emplacements libres (pas de base adverse). La ligne **avant est tournée vers le joueur** (la plus proche du centre de l'écran) et c'est elle qui est visée en premier par les attaques « au plus proche » (combat.md §13.2.2) ; la ligne arrière est la plus éloignée
- **Les 3 colonnes ennemies sont alignées verticalement sur celles du vaisseau du joueur** (décision
  utilisateur ; vues sur l'écran, ce sont des bandes horizontales) : colonne du haut face aux modules du haut (FG/FD), colonne du bas face aux modules
  du bas (AG/AD), colonne du milieu face au vaisseau (module de base, au centre). PC
  (`src/ui/fenetre.py:COLONNE_Y`) : centres dérivés directement des mêmes emplacements que
  `_rect_module` (colonne du milieu = moyenne des centres haut/bas). Web (`src/web/style.css`) :
  `.grille.grille-ennemis` définit un `row-gap` dérivé du même ratio (`--taille-case`), et un
  padding haut/bas égal (contrairement à une version antérieure, plus généreuse en haut pour la
  pastille PV/Bouclier) pour que la colonne du milieu reste centrée sur le bloc vaisseau — les deux
  blocs étant déjà centrés l'un sur l'autre par `#grilles` (`align-items:center`)
- **Contrôles** (à gauche, sous la barre latérale Niveau/Argent/Deck/Vaisseau, architecture.md
  §10.3) : électricité « ⚡ 3/3 », boutons icônes Tour suivant, Quitter, Journal (§8.3), puis le
  numéro de tour et les **compteurs des piles** : Pioche, Défausse, Épuisées, et Hors service
  seulement si elle n'est pas vide.
- **Main de cartes** : alignée en bas de l'écran, centrée. PC : cartes de **150 px** de large
  (décision utilisateur, 2026-11-27), qui **se chevauchent** quand la main ne tient plus en largeur
  (chacune passe au-dessus de sa voisine de gauche) ; la carte sélectionnée est soulevée et
  entourée. Le vaisseau et la flotte sont remontés d'autant (`VAISSEAU_Y`) : la main ne cache
  pas la ligne du bas ni ses intentions. Web : cartes plus petites, côte à côte (le texte se lit
  sur la carte agrandie).
- **Bouton Deck pendant un combat** : toutes les cartes du combat, toutes piles confondues.

### 8.2 Formes visuelles

- **Modules et ennemis** : images carrées ; le **principal** est le grand vaisseau qui porte les
  quatre emplacements. Un ennemi sur 2 cases (le Boss) est **un seul rectangle fusionné**.
- **Carte** (décisions utilisateur du 2026-11-27, gabarit et icônes :
  `specs/generation-images/prompt-modele-carte.md`) : partout la même (main, récompenses, deck,
  Aventures, victoire finale), dessinée sur un **gabarit** dont la **couleur dit la rareté**
  (argent Base, vert Commune, bleu Rare, or Légendaire ; plus d'étoile). De haut en bas :
  - **barre du haut** : à gauche le **coût** (icône éclair et chiffre), les **munitions**
    « restantes/de départ » si elles sont limitées, les **lancements** « ×2 » si la carte est
    lancée plus d'une fois (pas sur une carte qui en fait lancer d'autres, comme Feu à volonté) ;
    à droite l'**icône du type** (Attaque : missile, Défense : bouclier plein, Réparation : clé,
    Buff : flèche vers le haut, Debuff : flèche cassée, Outils : engrenage, Contrôle : main) ;
  - l'**illustration** ; bandeau **PERSISTANTE** en bas de l'illustration si la carte l'est ;
  - le **texte** : sa description avec ses valeurs actuelles (`description_affichee`), qui finit
    par un point ;
  - le **nom**, dans le bandeau du bas.

  Le texte prend au plus la taille du nom, et rétrécit seulement s'il ne tient pas dans sa zone.
  Une carte **injouable maintenant** (électricité, aucune cible) est assombrie.
- **Carte agrandie** (décision utilisateur, 2026-11-27) : la carte en grand (300 px sur PC),
  avec ce qu'elle ne montre pas : son **module**, « **Pas jouable maintenant** ». PC : au survol
  d'une carte de la main, **collée au bas de l'écran** par-dessus la main (détails au-dessus
  d'elle), ou d'une grille de deck (à côté d'elle, détails dessous) ;
  web : quand la carte est armée, ou touchée dans un deck, au centre de l'écran. Les récompenses
  et les cartes des Aventures sont déjà assez grandes, avec le nom de leur module au-dessus.
- **Pastilles** au-dessus de chaque case, jamais sur l'image : **PV** (rouge) et **Bouclier**
  (bleu) toujours ; **Incendie** (orange), **Renvoi** (violet), **Leurre** (cyan) seulement s'ils
  sont actifs.
- **Module visé** par une attaque au prochain tour ennemi : un marqueur (anneau rouge sur PC,
  « 🎯 » sur le web).
- **Intention d'un ennemi** : version courte dans sa case (web « ⚔7×2 », PC « Att. 7×2 » ;
  « tous » pour une attaque de tous les modules).
- **Module détruit** : case assombrie, « Détruit », et le nombre de ses cartes hors service.
- **Infobulle** d'une case (survol sur PC, tap sans carte armée sur le web) : nom, PV / PV max,
  statuts actifs en clair. Module : « Visé au prochain tour par : … », cartes hors service s'il
  est détruit. Ennemi : **seulement les actions de son prochain tour, une par ligne, sans titre
  ni cycle complet** (décisions utilisateur, 2026-11-13). PC : au-dessus du curseur, police 13,
  300 px de large.
- **Carte armée** : cadre jaune autour de la carte ; les **cases où elle peut être confirmée**
  sont mises en évidence (contour vert sur PC).

### 8.3 Interaction de jeu d'une carte

**Le jeu se joue entièrement à la souris (PC) ou au doigt (web).**

1. Clic sur une carte de la main → elle est **armée** (un second clic la désarme).
2. Clic sur une **case valide** → la carte est jouée. Les cases valides sont celles de
   `Combat.cibles_possibles(carte)` : une case du bon camp, vivante, de la bonne ligne pour
   Avant / Arrière, celle du principal pour Module Principal.
3. **Toujours un clic de confirmation**, même quand la case ne change rien à l'effet (Ennemi
   Tous, Module Tous, Module Principal) : jamais de résolution automatique. Un clic ailleurs, ou
   avec une carte injouable, est ignoré et la carte reste armée. **Ce flux doit rester identique
   entre PC (`fenetre.py:_essayer_de_cibler`) et web (`app.js:cliquerCase`)** : toute divergence
   est un bug.
4. Une entité sur deux cases (principal, Boss) n'a qu'une case à l'écran : l'affichage transmet
   celle de ses cases que le gameplay accepte (Ligne arrière sur le Boss : sa case arrière).
5. **Tour suivant** (chevrons verts) : termine le tour à tout moment (`Combat.finir_tour`).
6. **Quitter** (croix rouge) : ferme le combat et ramène à la sélection du joueur, **sans le
   sauvegarder** (décision utilisateur) : la partie reste telle qu'avant ce combat, qui
   recommencera avec un nouveau tirage au prochain « Continuer » (a-trancher.md §9.1).
7. **Popups** : chaque entrée du journal ajoutée par la dernière action donne un popup sur la
   case touchée, avec ce qui s'est **réellement** passé : PV perdus, part absorbée par le
   bouclier, réparation, statut posé. Une attaque qui ne fait perdre aucun PV dit ce qui l'a
   arrêtée (annulée par le leurre, renvoyée, bloquée), même à plusieurs ; une réparation de 0 PV
   ne donne pas de popup.
8. **Journal de combat** (bouton parchemin) : une ligne par événement de `Combat.journal`
   (combat.md §3.10), mise en phrase par l'affichage (PC : `textes_combat.ligne_journal` ; web :
   `construireLigneJournal`). Exemples :
   - « --- Tour 3 --- »
   - « Laser → Pat le Pirate : 6 dégâts, 2 absorbés par le bouclier, 4 PV perdus (46 restants) »
   - « Pat le Pirate → Lanceur de missiles : 5 dégâts, annulés par le leurre »
   - « Renvoi → Principal : 5 dégâts, 5 PV perdus (55 restants) »
   - « Incendie sur Petit Jean : 4 dégâts, 4 PV perdus (96 restants) »
   - « Protéger le vaisseau → Principal : bouclier 6 »
   - « Lanceur de missiles détruit », « Lanceur de missiles : 3 carte(s) hors service »
   - « Victoire » / « Défaite »

   Une carte jouée ne donne pas de ligne à elle seule : chacun de ses effets en donne une. Le
   journal n'est jamais sauvegardé.

### 8.4 Écarts entre PC et web (propositions à valider)

1. **Ni emoji ni symbole rare sur PC** : leur affichage dépend de la police de la machine. Le PC
   écrit des mots (« Att. 7×2 », « Bouclier 10 », « Renvoi 5 », popups « +6 bouclier »,
   « bloqué (6) », « renvoi 5 », pastille « L » pour le Leurre) là où le web utilise « ⚔ », « 🛡 »,
   « ↩ », « 🎭 ». Restent sur PC « × », « → », « ⚡ », « ★ ».
2. **Plusieurs popups sur la même case** : empilés vers le haut sur PC, décalés dans le temps sur
   le web.
3. **Fin de combat** : sur PC, la fenêtre se ferme dès la victoire ou la défaite pour ouvrir
   l'écran de fin ; le web affiche une bannière « Continuer ».
4. **Intention courte et pastille de cible** (web, validé le 2026-11-13 « pour le moment ») : le
   détail de l'intention est dans l'infobulle plutôt que dans la case.
5. Le web est volontairement simplifié (pas de survol, tailles pilotées par la hauteur de
   l'écran) : ces écarts-là sont commentés dans `app.js` et `style.css`.
