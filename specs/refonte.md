# Refonte du jeu — vue d'ensemble

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **À lire en premier** pour
comprendre l'état du projet : une refonte des cartes, des modules, des ennemis, des statuts et du
combat est en cours, avec un **nouveau moteur codé à côté de l'ancien**, pas encore branché au jeu.
Mis à jour le 2026-11-11.*

---

## 1. Deux moteurs coexistent

| | Ancien moteur (le jeu actuel) | Moteur de la refonte (`_new`) |
|---|---|---|
| **Utilisé par** | le jeu PC (`main.py`, `src/ui/`) et web (`web/`), le parcours (`deroulement.py`, `partie.py`), l'ancien simulateur (`outils/simulation/bot.py`, `etudes.py`) | les tests et le simulateur de la refonte (`outils/simulation/bot_new.py`, `combats_new.py`) seulement |
| **Code** | `carte.py`, `module.py`, `ennemi.py`, `combat.py`, `deck.py`, `flotte.py`, `vaisseau.py`, `joueur.py`, `ciblage.py`, `config_poc.py`, `donnees.py` | `carte_new.py`, `module_new.py`, `ennemi_new.py`, `statut_new.py`, `combat_new.py`, `deck_new.py`, `flotte_new.py`, `vaisseau_new.py` |
| **Données** | `config/cartes.json`, `config/modules.json`, `config/ennemis.json` | `config/carte_new.json`, `config/module_new.json`, `config/ennemi_new.json` (**sources de vérité**), avec leurs tableaux générés `.md` |
| **Spec** | `combat.md`, `modules-cartes.md`, `interface.md`… (§2 à §13) | les brouillons `refonte-*.md` (§3 ci-dessous) |

- **Le « branchement »** (§5) remplacera l'ancien moteur par le nouveau dans le parcours, la
  sauvegarde et l'affichage, puis supprimera l'ancien. D'ici là, **les deux doivent continuer à
  fonctionner**.
- **Une valeur de carte changée** dans `config/carte_new.json` pour une carte jouable doit être
  **reportée à la main dans `config/cartes.json`**, sinon le jeu actuel ne la voit pas (fait pour
  les boucliers le 2026-11-11).
- Les fichiers `_new` sont déjà montés côté web (`FICHIERS_A_MONTER` de `web/app.js`, exigé par
  `tests/test_architecture.py`) même s'ils ne sont pas utilisés.
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
| Cartes | `modules-cartes.md` §4 (valeurs revues), `refonte-modules.md` §3 | `carte_new.py` (`CarteNew`) | `config/carte_new.json` (19 cartes), tableau `config/carte_new.md` | `test_carte_new.py`, `test_tableau_cartes.py` |
| Modules | `refonte-modules.md` (§3 Hors service et Persistante, §8 modèle) | `module_new.py` (`ModuleNew`) | `config/module_new.json`, `config/module_new.md` | `test_module_new.py`, `test_tableau_modules.py` |
| Ennemis | `refonte-ennemis.md` | `ennemi_new.py` (`EnnemiNew`) | `config/ennemi_new.json`, `config/ennemi_new.md` | `test_ennemi_new.py`, `test_tableau_ennemis.py` |
| Statuts | `refonte-statuts.md` | `statut_new.py` | — | `test_statut_new.py` |
| Combat | `refonte-combat.md` (§11 : choix faits en codant) | `combat_new.py`, `vaisseau_new.py`, `flotte_new.py`, `deck_new.py` | — | `test_combat_new.py`, `test_vaisseau_new.py`, `test_flotte_new.py`, `test_deck_new.py` |
| Simulation | `simulation.md` §12 | `outils/simulation/bot_new.py`, `combats_new.py`, `essai_bouclier.py` | — | `test_simulation_combats_new.py` |
| Buff Destruction | `refonte-destruction.md` (**en attente**) | — | — | — |
| Réflexion d'origine sur les buffs | `refonte-buffs-debuffs.md` (en partie dépassé par `refonte-statuts.md`) | — | — | — |

Les tableaux `config/*_new.md` sont **générés** (`python -m outils.tableau_cartes`,
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

**Branchement** (le gros chantier suivant, pas encore commencé) :
1. Sauvegarde de la partie : deck avec exemplaire de module par carte, modules `ModuleNew`
   (`partie.py`, `web/bridge.py`).
2. Composition des flottes de la refonte (placement, coefficient par niveau) et appel de
   `CombatNew` depuis le parcours (`deroulement.py`).
3. Affichage PC (`src/ui/`) et web (`web/`) du nouveau combat : il lit tout dans l'API de
   `CombatNew` (`combat.deck`, `cibles_possibles`, `intentions`, `journal`), jamais dans le deck de
   la partie.
4. Suppression de l'ancien moteur et des anciens `config/*.json`.

**Design encore ouvert** :
- Flottes par niveau (les niveaux 2 à 5 sont trop faciles), éventuels nouveaux ennemis
  (`refonte-ennemis.md` §5).
- Rattachement des cartes obtenues hors module (`refonte-modules.md` §3.3).
- Buff Destruction, résurrection, sacrifice volontaire (`refonte-destruction.md`,
  `refonte-modules.md` §4 à §6).
- Vulnérabilité, Réduction de dégâts, Tir allié : refusés par `CombatNew` pour l'instant
  (`refonte-combat.md` §1.2).
- Revue des autres modules et de leurs cartes (seuls principal et Lanceur sont revus).
- Accumulation du bouclier à surveiller (`essai_bouclier_2026-11-11.md`).

Une fois la refonte stabilisée et branchée, son contenu ira dans les sections numérotées
(`combat.md`, `modules-cartes.md`…) et les fichiers `refonte-*.md` seront supprimés.
