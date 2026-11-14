# Refonte du jeu — vue d'ensemble

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
| Cartes | `modules-cartes.md` §4 (valeurs revues), `refonte-modules.md` §3 | `carte.py` (`Carte`) | `config/cartes.json` (19 cartes), tableau `config/cartes.md` | `test_carte.py`, `test_tableau_cartes.py` |
| Modules | `refonte-modules.md` (§3 Hors service et Persistante, §8 modèle) | `module.py` (`Module`) | `config/modules.json`, `config/modules.md` | `test_module.py`, `test_tableau_modules.py` |
| Ennemis | `refonte-ennemis.md` | `ennemi.py` (`Ennemi`) | `config/ennemis.json`, `config/ennemis.md` | `test_ennemi.py`, `test_tableau_ennemis.py` |
| Statuts | `refonte-statuts.md` | `statut.py` | — | `test_statut.py` |
| Combat | `refonte-combat.md` (§11 : choix faits en codant) | `combat.py`, `vaisseau.py`, `flotte.py`, `deck.py` | — | `test_combat.py`, `test_vaisseau.py`, `test_flotte.py`, `test_deck.py` |
| Simulation | `simulation.md` §12 | `outils/simulation/bot.py`, `combats.py`, `essai_bouclier.py` | — | `test_simulation_combats.py` |
| Buff Destruction | `refonte-destruction.md` (**en attente**) | — | — | — |
| Réflexion d'origine sur les buffs | `refonte-buffs-debuffs.md` (en partie dépassé par `refonte-statuts.md`) | — | — | — |

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
   Station et Aventures, simulateur de parties~~ : **fait (PR 1, 2026-11-12)**, choix à valider dans
   refonte-branchement.md §5.1.
2. ~~Affichage web (`src/web/bridge.py`, `src/web/app.js`)~~ : **fait (PR 2, 2026-11-12)**, maquette à
   valider (refonte-branchement.md §5.2).
3. ~~Affichage PC (`src/ui/`, `main.py`) : il lit tout dans l'API de `Combat` (`combat.deck`,
   `cibles_possibles`, `intentions`, `journal`), jamais dans le deck de la partie~~ : **fait (PR 3,
   2026-11-14)**, écarts avec le web à valider (refonte-branchement.md §5.4).
4. ~~Suppression de l'ancien moteur et des anciens `config/*.json`~~ : **fait (PR 4, 2026-11-14)**.
   Suffixe `_new` retiré le même jour (refonte-branchement.md §5.5).

**Design encore ouvert** :
- Flottes par niveau (les niveaux 2 à 5 sont trop faciles), éventuels nouveaux ennemis
  (`refonte-ennemis.md` §5).
- Rattachement des cartes obtenues hors module (`refonte-modules.md` §3.3).
- Buff Destruction, résurrection, sacrifice volontaire (`refonte-destruction.md`,
  `refonte-modules.md` §4 à §6).
- Vulnérabilité, Réduction de dégâts, Tir allié : refusés par `Combat` pour l'instant
  (`refonte-combat.md` §1.2).
- Revue des autres modules et de leurs cartes (seuls principal et Lanceur sont revus).
- Accumulation du bouclier à surveiller (`essai_bouclier_2026-11-11.md`).

Une fois la refonte stabilisée et branchée, son contenu ira dans les sections numérotées
(`combat.md`, `modules-cartes.md`…) et les fichiers `refonte-*.md` seront supprimés.
