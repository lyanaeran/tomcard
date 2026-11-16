# Space Fight

*Deckbuilder roguelike (vaisseaux spatiaux) — Document de conception — v0.1*

Ce fichier est l'**index** du document de conception, découpé par thème en plusieurs fichiers du
dossier `specs/` pour qu'on puisse lire seulement la partie utile. La **numérotation des sections
est commune** à tous les fichiers : une référence « specs.md §8.3 » (dans le code, les tests ou un
autre fichier de spec) se résout avec la table ci-dessous.

---

## 1. Pitch

Un deckbuilder roguelike inspiré de Slay the Spire, où le joueur incarne un vaisseau spatial composé de **modules**. Chaque module possède son propre deck de compétences. Contrairement à Slay the Spire, il n'y a pas de héros unique ni de carte de monde classique : le joueur avance à travers une série de choix à chaque tour, en gérant la survie et la progression de son vaisseau.

---

## Où trouver chaque section

| Sections | Fichier | Contenu |
|---|---|---|
| §2 – §2.4 | [parcours.md](parcours.md) | Boucle de run, Argent/récompenses, Station service, structure par niveaux, enchaînement des écrans |
| §2.5 | [aventures.md](aventures.md) | Aventures (Trois lunes, Astéroïdes, Police) |
| §3 | [combat.md](combat.md) | Règles de combat : grille, électricité et piles, destruction de module, statuts (bouclier, incendie, renvoi, leurre), munitions, déroulement d'un tour, jeu d'une carte, fin du combat, API de `combat.py` |
| §4 – §7 | [modules-cartes.md](modules-cartes.md) | Modules (modèle, idées de modules), emplacements, récompenses de cartes, catégories / cibles / rareté / munitions |
| §8 | [interface.md](interface.md) | Écran de combat : disposition, formes visuelles, interaction de jeu d'une carte (§8.3), écarts PC / web (§8.4) |
| §9 | [a-trancher.md](a-trancher.md) | Points encore à trancher (design et technique) |
| §10 | [architecture.md](architecture.md) | Stack, arborescence, persistance (profils/sauvegardes, transitions de fenêtres PC), conventions |
| §11 | [a-trancher.md](a-trancher.md) | Idées à explorer plus tard |
| §12 | [modules-cartes.md](modules-cartes.md) | Modèle de carte : format, natures d'effet, portées, rattachement à un module et Persistante, répétition, mécaniques non codées |
| §13 | [combat.md](combat.md) | Ennemis : modèle (cycle, valeurs, coefficient), tour ennemi et intentions, les ennemis de `config/ennemis.json`, flottes, PV des modules |

## Documents de travail (hors numérotation)

Le jeu tourne sur le moteur issu de la **refonte de novembre 2026** ; l'ancien moteur est supprimé
et les brouillons de la refonte ont été reportés dans les sections numérotées ci-dessus
(2026-11-14). **Pour une vue d'ensemble, commencer par [refonte.md](refonte.md).**

| Fichier | Contenu |
|---|---|
| [refonte.md](refonte.md) | **Vue d'ensemble** : les grandes décisions de la refonte, où est quoi (spec, code, données, tests), résultats de simulation, ce qui reste ouvert |
| [refonte-branchement.md](refonte-branchement.md) | **Historique** du branchement de la refonte en 4 PR : décisions, choix faits en codant, ce qui a été vérifié. Garde les noms `_new` de l'époque |
| [refonte-destruction.md](refonte-destruction.md) | **Pistes non codées** : buff « Destruction », résurrection, sacrifice volontaire d'un module |
| [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) | Réflexion d'origine sur les buffs, debuffs et bouclier : historique, avec des **pistes non codées** (statuts à durée, boucliers à seuil) |
| [effets-a-coder.md](effets-a-coder.md) | **Nouveaux effets décidés ou en réflexion, pas encore codés** (Surcharge…) ; on ne code pas avant l'accord de l'utilisateur |
| [archive-cartes-modules.md](archive-cartes-modules.md) | **Archive** : les 44 cartes et 10 modules de l'ancien moteur (anciens `config/cartes.json` et `modules.json`), en tableaux ; réserve d'idées pour revoir les autres modules, ne décrit pas le jeu actuel |
| [simulation.md](simulation.md) | Conception des simulateurs d'équilibrage (`outils/simulation/`) : parties complètes (§11) et combats isolés (§12) |
| [outil-editeur-cartes.md](outil-editeur-cartes.md) | **Spécification codée** (2026-11-15) de l'outil d'administration web / iPhone : liste des cartes, détail modifiable, sauvegarde locale, repérage des cartes modifiées, copie du fichier ; deux changements de format des cartes à faire avant (§10) |

## Quel fichier lire selon la tâche

- **Nouvel écran ou étape du parcours, récompenses, Argent, niveaux** → `parcours.md`
- **Aventure** → `aventures.md`
- **Règle de combat, ennemi, flotte** → `combat.md`
- **Nouvelle carte ou mécanique de carte, module** → `modules-cartes.md` (§12 d'abord pour savoir
  si la mécanique existe déjà dans le moteur) ; valeurs à jour : `config/*.md` (générés)
- **Affichage ou flux de clics du combat** → `interface.md`
- **Sauvegarde, profils, structure du code, transitions de fenêtres** → `architecture.md`
- **Valeur non tranchée ou idée pour plus tard** → `a-trancher.md`
- **Vue d'ensemble, où est le code de quoi** → `refonte.md`
- **Idée de mécanique pas encore codée** → `effets-a-coder.md`, `a-trancher.md` §11, `refonte-destruction.md`,
  `refonte-buffs-debuffs.md`
- **Équilibrage, simulation** → `simulation.md` et les synthèses `outils/simulation/synthese/`

## Maintenance

- Le document reste la seule source de vérité pour le design, et doit rester synchronisé avec le
  code (cf. `CLAUDE.md`) : une décision prise en cours d'implémentation va dans le fichier qui
  contient la section concernée.
- Une nouvelle section garde la numérotation globale : elle va dans le fichier de sa section
  parente, et une nouvelle section de premier niveau s'ajoute à la table ci-dessus.
- Les références croisées s'écrivent par numéro (« §8.3 », « specs.md §8.3 »), jamais par numéro
  de ligne, pour survivre aux réorganisations.
