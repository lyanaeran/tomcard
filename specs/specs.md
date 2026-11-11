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
| §3 | [combat.md](combat.md) | Règles de combat : placement/rangs, tailles, électricité/main, destruction, bouclier, munitions |
| §4 – §7 | [modules-cartes.md](modules-cartes.md) | Modules, slots, progression des modules/cartes (pool de récompense, `Carte.id`), types de cartes |
| §8 | [interface.md](interface.md) | Écran de combat : disposition, formes visuelles, interaction de jeu d'une carte (§8.3) |
| §9 | [a-trancher.md](a-trancher.md) | Points encore à trancher (design et technique) |
| §10 | [architecture.md](architecture.md) | Stack, arborescence, persistance (profils/sauvegardes, transitions de fenêtres PC), conventions |
| §11 | [a-trancher.md](a-trancher.md) | Idées à explorer plus tard |
| §12 | [modules-cartes.md](modules-cartes.md) | Mécaniques de carte : référence d'implémentation et manques restants |
| §13 | [combat.md](combat.md) | Comportement des ennemis (IA), ennemis de `config/ennemis.json`, flottes |

## Documents de travail (hors numérotation)

| Fichier | Contenu |
|---|---|
| [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) | Brouillon de refonte des buffs/debuffs/bouclier (non décidé, non implémenté) |
| [refonte-modules.md](refonte-modules.md) | Brouillon de refonte des modules secondaires sacrifiables (non implémenté) |
| [refonte-destruction.md](refonte-destruction.md) | Brouillon du buff « Destruction » (en attente, aucune carte ne le pose encore) |
| [refonte-statuts.md](refonte-statuts.md) | Statuts (bouclier, incendie, renvoi, leurre…) gérés ensemble pour modules et ennemis : règles de cumul et d'extinction, déroulement ; codé (`statut_new.py`), pas encore branché au combat |
| [refonte-ennemis.md](refonte-ennemis.md) | Brouillon de refonte des ennemis : cycle d'actions, valeurs nommées qui augmentent, coefficient de difficulté ; modèle codé (`EnnemiNew`, `config/ennemi_new.json`), pas encore branché au combat |
| [refonte-combat.md](refonte-combat.md) | Spécification du combat de la refonte (`combat_new`) : entrées, déroulement du tour, jeu d'une carte, tour ennemi, destruction, fin de combat (gameplay seulement) ; codé (`combat_new.py`), pas encore branché |
| [simulation.md](simulation.md) | Conception de l'outil de simulation d'équilibrage (`outils/simulation/`) |

## Quel fichier lire selon la tâche

- **Nouvel écran ou étape du parcours, récompenses, Argent, niveaux** → `parcours.md`
- **Aventure** → `aventures.md`
- **Règle de combat, ennemi, flotte** → `combat.md`
- **Nouvelle carte ou mécanique de carte, module** → `modules-cartes.md` (§12 d'abord pour savoir
  si la mécanique existe déjà dans le moteur)
- **Affichage ou flux de clics du combat** → `interface.md`
- **Sauvegarde, profils, structure du code, transitions de fenêtres** → `architecture.md`
- **Valeur non tranchée ou idée pour plus tard** → `a-trancher.md`

## Maintenance

- Le document reste la seule source de vérité pour le design, et doit rester synchronisé avec le
  code (cf. `CLAUDE.md`) : une décision prise en cours d'implémentation va dans le fichier qui
  contient la section concernée.
- Une nouvelle section garde la numérotation globale : elle va dans le fichier de sa section
  parente, et une nouvelle section de premier niveau s'ajoute à la table ci-dessus.
- Les références croisées s'écrivent par numéro (« §8.3 », « specs.md §8.3 »), jamais par numéro
  de ligne, pour survivre aux réorganisations.
