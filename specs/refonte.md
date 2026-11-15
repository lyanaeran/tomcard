# Le moteur du jeu — vue d'ensemble (refonte de novembre 2026)

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **À lire en premier** pour
comprendre l'état du projet : une refonte des cartes, des modules, des ennemis, des statuts et du
combat a été faite avec un **nouveau moteur codé à côté de l'ancien**, puis branchée au jeu :
le gameplay du parcours (partie, sauvegarde, déroulement, Station, Aventures, simulateur de parties)
utilise le nouveau moteur depuis la PR 1 (2026-11-12), la version web depuis la PR 2, la version
PC depuis la PR 3 (2026-11-14) : **le jeu est jouable sur PC et sur le web**. **L'ancien moteur
est supprimé (PR 4, 2026-11-14).** Mis à jour le 2026-11-14.*

---

## 1. Un seul moteur

L'ancien moteur (code, données, tests) est **supprimé** depuis la PR 4 du branchement. Le moteur de
la refonte est le seul, et ses fichiers ont perdu leur suffixe `_new` (2026-11-14, décision
utilisateur) :

| | Aujourd'hui | Nom pendant la refonte |
|---|---|---|
| **Code** (`src/gameplay/`) | `carte.py`, `module.py`, `ennemi.py`, `statut.py`, `combat.py`, `deck.py`, `flotte.py`, `vaisseau.py` | `carte_new.py`, `module_new.py`… |
| **Classes** | `Carte`, `Module`, `Ennemi`, `Combat`, `Deck`, `Flotte`, `Vaisseau`, `CibleCarte`, `EtatCombat` | `CarteNew`, `ModuleNew`… |
| **Données** | `config/cartes.json`, `config/modules.json`, `config/ennemis.json` (**sources de vérité**), avec leurs tableaux générés `.md` | `config/carte_new.json`… |
| **Simulateur de combats** | `outils/simulation/bot.py`, `combats.py` | `bot_new.py`, `combats_new.py` |

- **Utilisé par** : le parcours (`deroulement.py`, `partie.py`, `parcours.py`), l'affichage PC
  (`main.py`, `src/ui/`) et web (`src/web/`), les deux simulateurs.
- Un nom en `_new` ou en `…New` dans un document plus ancien (`refonte-branchement.md`, synthèses
  de simulation) désigne le fichier ou la classe d'aujourd'hui.
- **Le « branchement »** a remplacé l'ancien moteur dans le parcours (PR 1), le web (PR 2), le PC
  (PR 3), puis l'a supprimé (PR 4) : historique dans
  [refonte-branchement.md](refonte-branchement.md).
- **Une valeur de carte se change dans `config/cartes.json`**, puis on régénère
  `config/cartes.md`.
- Seuls **deux modules sont jouables** dans les deux moteurs : le module **principal** (`MOD_1`)
  et le **Lanceur de missiles** (`MOD_2`). Les autres modules et leurs cartes ne sont pas encore
  revus.

## 2. Les grandes idées de la refonte (décisions utilisateur)

- **Modules secondaires sacrifiables** : seuls les PV du **principal** (60) persistent d'un combat
  à l'autre ; un secondaire (20 PV) repart plein à chaque combat. Sa destruction n'est pas une
  défaite, mais ses cartes partent dans une **pile Hors service** jusqu'à la fin du combat (sauf
  mot-clé **Persistante**). Défaite seulement si le principal est détruit.
- **Cartes rattachées à un exemplaire de module** (`"M1"`, `"M2"`…) ; deck de départ et cartes
  obtenues hors module rattachés au principal pour l'instant.
- **Cartes à valeurs nommées** (`{"degats": 6}`) et effets qui y renvoient ; **lancements
  multiples** (une carte peut s'appliquer plusieurs fois pour un seul coût) et cartes de
  **répétition** (Salve laser…) qui en ajoutent.
- **Statuts partagés** par modules et ennemis (bouclier, incendie, renvoi, leurre), chacun avec sa
  règle de cumul et d'extinction ; **bouclier et incendie perdent 1 par tour** (plus de division
  par deux, plus de « bouclier par tour »).
- **Ennemis à cycle d'actions** (une étape par tour, puis on recommence), valeurs nommées qui
  **augmentent avec le tour**, **coefficient de difficulté** ; Miroir pose un **renvoi** (plus un
  bouclier miroir permanent, qui bloquait le jeu).
- **Combat** : tour du joueur (3 électricité, 5 cartes), fin de tour (statuts des ennemis), tour
  ennemi (ordre avant → arrière, droite → gauche), fin du tour ennemi (statuts des modules) ; cible
  d'une carte = une **case** ; journal détaillé (dégâts absorbés par leurre, renvoi, bouclier, PV
  perdus et restants).

## 3. Où est quoi

| Sujet | Spec (décisions) | Code | Données | Tests |
|---|---|---|---|---|
| Cartes | `modules-cartes.md` §6, §7, §12 | `carte.py` (`Carte`) | `config/cartes.json` (19 cartes), tableau `config/cartes.md` | `test_carte.py`, `test_tableau_cartes.py` |
| Modules | `modules-cartes.md` §4, §5 ; destruction : `combat.md` §3.4 | `module.py` (`Module`) | `config/modules.json`, `config/modules.md` | `test_module.py`, `test_tableau_modules.py` |
| Ennemis, flottes | `combat.md` §13 | `ennemi.py` (`Ennemi`), `flotte.py` | `config/ennemis.json`, `config/ennemis.md` | `test_ennemi.py`, `test_flotte.py`, `test_tableau_ennemis.py` |
| Statuts | `combat.md` §3.5 | `statut.py` | — | `test_statut.py` |
| Combat | `combat.md` §3 | `combat.py`, `vaisseau.py`, `deck.py` | — | `test_combat.py`, `test_vaisseau.py`, `test_deck.py` |
| Parcours, Station, Aventures, sauvegarde | `parcours.md`, `aventures.md`, `architecture.md` §10.3 | `partie.py`, `parcours.py`, `deroulement.py` | — | `test_partie.py`, `test_parcours.py`, `test_deroulement.py` |
| Écran de combat | `interface.md` §8 | `src/ui/fenetre.py`, `textes_combat.py` ; `src/web/app.js`, `bridge.py` | — | `test_textes_combat.py`, `test_bridge.py`, `outils/test_web/essais.js` |
| Simulation | `simulation.md` | `outils/simulation/` | — | `test_simulation.py`, `test_simulation_combats.py` |
| Destruction, résurrection, sacrifice | `refonte-destruction.md` (**pistes non codées**) | — | — | — |
| Réflexion d'origine sur les buffs | `refonte-buffs-debuffs.md` (historique, pistes non codées) | — | — | — |
| Historique du branchement | `refonte-branchement.md` | — | — | — |
| Anciennes cartes et anciens modules | `archive-cartes-modules.md` (**archive**) | — | — | — |

Les tableaux `config/*.md` sont **générés** (`python -m outils.tableau_cartes`,
`tableau_modules`, `tableau_ennemis`), jamais modifiés à la main ; un test échoue s'ils ne sont pas
à jour.

## 4. Résultats de simulation

- `outils/simulation/synthese/analyse_2026-11-11_combat_new.md` : 5 800 combats sans aucune erreur
  moteur ; Miroir ne bloque plus ; combats à un ennemi trop faciles, Le nettoyeur le plus dangereux
  en paire ; réglage actuel des boucliers 4 / 6 / 8 (45 % des parties approchées battent le Boss),
  comparé aux réglages 3 / 5 / 6 et 5 / 7 / 8.
- `outils/simulation/synthese/essai_bouclier_2026-11-11.md` : Bouclier à 3, 4, 5, 6, accumulation
  du bouclier, décision 4 / 6 / 8.
- `outils/simulation/synthese/analyse_2026-11-07.md` : ancien moteur (avant refonte).

## 5. Ce qui reste à faire

**Branchement** (plan validé le 2026-11-11 : [refonte-branchement.md](refonte-branchement.md),
quatre PR, web avant PC) :
1. ~~Gameplay : sauvegarde (`Module`, cartes rattachées), flottes, `Combat` dans le parcours,
   Station et Aventures, simulateur de parties~~ : **fait (PR 1, 2026-11-12)**, refonte-branchement.md §5.1.
2. ~~Affichage web (`src/web/bridge.py`, `src/web/app.js`)~~ : **fait (PR 2, 2026-11-12)**, refonte-branchement.md §5.2.
3. ~~Affichage PC (`src/ui/`, `main.py`) : il lit tout dans l'API de `Combat` (`combat.deck`,
   `cibles_possibles`, `intentions`, `journal`), jamais dans le deck de la partie~~ : **fait (PR 3,
   2026-11-14)**, écarts avec le web à valider (interface.md §8.4).
4. ~~Suppression de l'ancien moteur et des anciens `config/*.json`~~ : **fait (PR 4, 2026-11-14)**.
   Suffixe `_new` retiré le même jour (refonte-branchement.md §5.5).

**Brouillons reportés (2026-11-14)** : `refonte-combat.md`, `refonte-statuts.md`,
`refonte-ennemis.md` et la partie codée de `refonte-modules.md` sont maintenant dans les sections
numérotées (`combat.md` §3 et §13, `modules-cartes.md` §4 et §12, `interface.md` §8) et ont été
supprimés. Restent hors numérotation : ce fichier, l'historique du branchement, et deux documents
de pistes non codées.

**Design encore ouvert** (liste complète : [a-trancher.md](a-trancher.md)) :
- Flottes par niveau (les niveaux 2 à 5 sont trop faciles), nouveaux ennemis.
- Rattachement des cartes obtenues hors module.
- Buff Destruction, résurrection, sacrifice volontaire
  ([refonte-destruction.md](refonte-destruction.md)).
- Vulnérabilité, Réduction de dégâts, Tir allié : non codés (`combat.md` §3.8.4).
- Revue des autres modules et de leurs cartes (seuls le principal et le Lanceur sont revus).
- Accumulation du bouclier à surveiller (`essai_bouclier_2026-11-11.md`).
- Écarts d'affichage entre PC et web à valider (`interface.md` §8.4).
