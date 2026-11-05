# Space Fight — Interface de combat (§8)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

---

## 8. Interface / écran de combat

### 8.1 Disposition générale (wireframe)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SPACE FIGHT — ÉCRAN DE COMBAT                                                    │
│ [Niveau/Argent/Deck/Vaisseau]                                                     │
│ [⚡ 3][►►][X]  ← barre latérale + contrôles de combat, haut gauche (pas de bandeau)│
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
- **Les 3 rangées ennemies sont alignées verticalement sur celles du vaisseau du joueur** (décision
  utilisateur) : rangée du haut face aux modules du haut (FG/FD), rangée du bas face aux modules
  du bas (AG/AD), rangée du milieu face au vaisseau (module de base, au centre). PC
  (`src/ui/fenetre.py:RANGEE_Y`) : centres dérivés directement des mêmes emplacements que
  `_rect_module` (rangée du milieu = moyenne des centres haut/bas). Web (`web/style.css`) :
  `.grille.grille-ennemis` définit un `row-gap` dérivé du même ratio (`--taille-case`), et un
  padding haut/bas égal (contrairement à une version antérieure, plus généreuse en haut pour la
  pastille PV/Bouclier) pour que la rangée du milieu reste centrée sur le bloc vaisseau — les deux
  blocs étant déjà centrés l'un sur l'autre par `#grilles` (`align-items:center`)
- **Compteur d'électricité** restante affiché en haut à gauche, empilé sous la barre latérale
  (Niveau/Argent/Deck/Vaisseau, §10.3) plutôt que dans un bandeau dédié en haut d'écran (décision
  utilisateur, remplace l'ancien bandeau "Électricité : N" + bouton "Fin de tour" en toutes
  lettres) — voir §8.3 point 4 pour les boutons de contrôle placés juste en dessous
- **Main de cartes** : alignée en bas de l'écran (pas en éventail, pour la lisibilité)
- **Pioche, défausse et cartes épuisées** (§3.6) : regroupées ensemble dans un coin de l'écran (compteurs de nombre de cartes), séparées de la main

### 8.2 Formes visuelles

- **Modules du joueur et ennemis** : images **carrées**
- **Module de base** : exception, forme différente (plus grande, fond dédié qui englobe les 5 emplacements)
- **Cartes** : format **rectangulaire**
- **PV / Bouclier** : affichés par de petites pastilles rondes (rouge pour les PV, bleue pour le Bouclier) flottant juste au-dessus de chaque case, jamais superposées à l'image (validé en POC)
- **Infobulle au survol** d'un module ou d'un ennemi (PV, Bouclier, buffs, intention §13) : PC,
  affichée **au-dessus du curseur** (ou dessous s'il n'y a pas la place en haut de l'écran), en
  police 13 sur 300 px de large, maintenue dans la fenêtre (décision utilisateur, l'ancienne
  version en police 9 au-dessus de la case était illisible). Web : infobulle au tap, inchangée
- **Carte armée** (§8.3) : PC, cadre jaune de 4 px *autour* de la carte, jamais un rectangle plein
  dessous (pouvait masquer l'image, l'ordre forme/sprite n'étant pas garanti par pyglet)
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
4. **Tour suivant** : un bouton icône (chevrons verts, sans texte — décision utilisateur, remplace
   l'ancien bouton texte "Fin de tour") permet au joueur de terminer son tour à tout moment, même
   s'il lui reste de l'électricité ou des cartes jouables. Placé en haut à gauche, empilé sous la
   barre latérale (Niveau/Argent/Deck/Vaisseau) plutôt que dans un bandeau du haut (retiré) — PC
   (`src/ui/fenetre.py:FenetreCombat._dessiner_controles_combat`) et web (`#controles-combat`,
   `#tour-suivant`) partagent la même logique de fin de tour (`Combat.finir_tour_joueur`),
   seul l'affichage change
5. **Quitter la partie** : un second bouton icône (croix rouge), juste sous "Tour suivant", ferme
   le combat en cours et ramène à l'écran de sélection du joueur — **sans synchroniser ni
   sauvegarder** ce combat (décision utilisateur) : la partie sauvegardée reste `EN_COURS` telle
   qu'elle était avant ce combat (PV du vaisseau, deck), qui repartira intégralement de zéro
   (nouveau tirage de flotte) au prochain "Continuer" depuis l'accueil du joueur. PC
   (`main.py:_ouvrir_combat`, `FenetreCombat.quitte_demandee`) rouvre `EcranSelectionJoueur` ; web
   (`quitterCombat()`) réinitialise `partieActive`/`joueurCourant` et rappelle
   `afficherSelectionJoueur()`. En mode démonstration (POC sans vraie partie, `partie=None` côté
   PC / `partieActive` nul côté web), le bouton reste actif : PC ferme simplement la fenêtre
   (aucun écran de sélection à rouvrir depuis un script autonome), web revient quand même à
   l'écran de sélection du joueur (ne dépend d'aucun état de partie)
6. **Retour visuel des effets** : chaque effet résolu (carte jouée ou attaque ennemie) affiche un popup `+N`/`-N` pendant quelques secondes sur la ou les cases touchées, avec le montant **réellement appliqué** (plafonné par les PV+Bouclier restants pour les dégâts, par le PV max pour le soin) plutôt que la valeur nominale de la carte — validé en POC
7. **Journal de combat** : un troisième bouton icône (rouleau/parchemin), juste sous "Quitter la
   partie", ouvre un écran de consultation listant l'historique complet du combat en cours — une
   ligne par carte jouée, par action ennemie résolue (attaque ou pose de buff/bouclier), et un
   marqueur `--- Tour N ---` à chaque début de tour (y compris le tour 1). Chaque ligne colore ses
   éléments : nom de la carte en **jaune**, nom d'un module allié touché en **vert**, nom d'un
   ennemi (acteur ou cible) en **rouge**, reste du texte en **bleu**, marqueur de tour en blanc —
   décision utilisateur. Une carte jouée est journalisée sous la forme invariante
   `"Carte {nom} jouée sur {cible}."` plutôt qu'un accord de genre sur le nom de la carte
   (`"Bouclier joué"` vs `"Attaque perçante jouée"`) : simplification pour éviter toute erreur
   d'accord, `config/cartes.json` ne portant aucune métadonnée de genre.
   **L'historique lui-même est une donnée de `Combat`, pas un artefact d'affichage** (cf. CLAUDE.md,
   gameplay commun aux deux interfaces) : `Combat.journal` (`src/gameplay/journal.py` —
   `EvenementCarteJouee`/`EvenementActionEnnemi`/`EvenementTour`) est alimenté uniquement par
   `Combat.jouer_carte`/`finir_tour_joueur`, qui décident seuls quoi enregistrer et quand (une
   carte n'est journalisée que si elle a eu un effet ; le marqueur de tour suivant n'est ajouté que
   si le combat continue). PC (`src/ui/journal_combat.py:ligne_evenement`,
   `src/ui/ecran_journal.py:EcranJournal`, ouvert en survol comme Deck/Vaisseau, lit directement
   `combat.journal`) et web (`#ecran-journal-combat`, `#bouton-journal-combat`,
   `construireLigneJournal`/`construireLigne*` dans `app.js`, qui lisent `etatCourant.journal` —
   `web/bridge.py:_evenement_json` ne fait que sérialiser `Combat.journal` en JSON dans
   `_etat_dict()`) ne dupliquent que la mise en forme (phrases/couleurs), jamais le calcul de ce
   qui s'est produit — même précédent que `texte_effet_carte`/`texteEffetCarte`. Journal
   réinitialisé (avec le marqueur du tour 1) à chaque nouveau combat via `Combat.__init__`, jamais
   persisté au-delà (comme le combat lui-même, cf. point 5 ci-dessus)
