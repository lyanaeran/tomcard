# Archive : cartes et modules de l'ancien moteur

*Document d'archive, hors numérotation (cf. [specs.md](specs.md)) : **ne décrit pas le jeu
actuel**. Contenu des anciens `config/cartes.json` et `config/modules.json` tels qu'ils étaient
juste avant la suppression de l'ancien moteur (PR 4 du branchement, 2026-11-14 ; décision
utilisateur : garder une trace de toutes les anciennes cartes). C'est la version la plus récente de
ces idées : elle inclut les ajustements faits après l'ancien registre `specs/cartes_legacy.xlsx`
(ex. *Renvoi* repensée en bouclier miroir, *Tir allié* qui vise n'importe quel allié). Fichiers
JSON d'origine : `git show 14dfde5:config/cartes.json` et `git show 14dfde5:config/modules.json`.*

À utiliser comme **réserve d'idées** pour revoir les autres modules : une carte reprise doit être
réécrite au format actuel dans `config/cartes.json` (modules-cartes.md §12), pas recopiée telle
quelle. Les mécaniques correspondantes, et celles que le moteur actuel ne sait pas encore faire,
sont résumées en modules-cartes.md §12.6.

**Lecture des colonnes** : textes recopiés tels quels (sans accents pour la plupart, comme dans
l'ancien JSON). *Description* : `X` et `Y` renvoient aux colonnes du même nom. *Ancien effet* :
ce que l'ancien moteur exécutait (`type`, `cible`, `valeur`, `action`, `durée` de l'ancienne
classe `Carte`), ou la raison pour laquelle la carte n'y était pas jouable. *Aujourd'hui* : la
carte existe-t-elle encore dans `config/cartes.json` (même id) ? Ses valeurs y ont souvent changé.

---

## 1. Modules (10)

| Id | Nom | PV | Jouable alors | Aujourd'hui | Description | Cartes | Image |
|---|---|---|---|---|---|---|---|
| MOD_1 | Principal | 50 | Oui | conservé (config/modules.json) | Votre vaisseau, plus cabosse que le Faucon Millenium, mais la prunelle de vos yeux. | CRT_7 Laser<br>CRT_8 Laser percant<br>CRT_10 Bouclier<br>CRT_11 Protéger le vaisseau<br>CRT_12 Réparation<br>CRT_46 Blindage cible<br>CRT_47 Laser lourd | `assets/modules/principal.png` |
| MOD_2 | Lanceur de missiles | 30 | Oui | conservé (config/modules.json) | Tout dans la finesse, des bons vieux missiles qui explosent partout (sauf la ou vous etes, on espere). | CRT_9 Bombardement<br>CRT_15 Ciel de missiles<br>CRT_16 Ligne arriere<br>CRT_18 Leurre | `assets/modules/missiles.png` |
| MOD_3 | Blindage | 30 | Non | **supprimé** | Quand la diplomatie a echoue et qu'on passe a la suite, mieux vaut pouvoir s'abriter. | CRT_20 Mode defensif<br>CRT_21 Bouclier adaptatif<br>CRT_23 Proteger l'avant poste<br>CRT_24 Blindage maximal<br>CRT_26 Bouclier perpetuel | `assets/modules/bouclier.png` |
| MOD_4 | Generateur | 30 | Non | **supprimé** | Une eolienne dans l'espace ? Vous etes sur ? | CRT_27 Surcharge temporaire<br>CRT_31 Fonds de tiroir | `assets/modules/generateur.png` |
| MOD_5 | Soute | 30 | Non | **supprimé** | Une soute bien remplie pour parer a toutes les (mauvaises) surprises... | CRT_39 Boost | `assets/modules/soute.png` |
| MOD_6 | Sabotage | 30 | Non | **supprimé** | Comment ca ton canon est tombe en panne ? C'est marrant parce que le mien non. Regarde... | CRT_33 Tordre le canon<br>CRT_34 Breche<br>CRT_35 Ligne avant<br>CRT_36 Tir allie<br>CRT_37 Boucliers endomages<br>CRT_38 Boucliers hors service | `assets/modules/sabotage.png` |
| MOD_7 | Canon lourd | 30 | Non | **supprimé** | Ce module envoie du lourd, mieux vaut ne pas se trouver en face. | *(aucune)* | `assets/modules/canon_lourd.png` |
| MOD_8 | Controle | 30 | Non | **supprimé** | La meilleure facon de se proteger des attaques de l'ennemi, c'est encore de l'empecher de les lancer. | *(aucune)* | `assets/modules/controle.png` |
| MOD_9 | Atelier | 30 | Non | **supprimé** | Bricoler le vaisseau alors que ca tire de tout cote ? Meme pas peur ! | *(aucune)* | `assets/modules/atelier.png` |
| MOD_10 | Radar | 30 | Non | **supprimé** | Quand on connait les points faibles, on peut faire beaucoup plus mal. | *(aucune)* | `assets/modules/radar.png` |

## 2. Cartes (44)

Dans l'ordre de l'ancien JSON, groupées par module d'origine.

### Module principal (11)

| Id | Nom | Rareté | Catégorie | Cible (conception) | Coût | X | Y | Munitions | Description | Ancien effet | Aujourd'hui |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_7 | Laser | Base | Attaque | Ennemi Unique | 1 | 6 | — | — | Inflige X degats a un ennemi unique | ATTAQUE, cible ENNEMI_UNIQUE, valeur 6 | conservée (« Laser ») |
| CRT_8 | Laser percant | Commune | Attaque | Ennemi Colonne | 2 | 8 | — | — | Inflige X degats a la colonne ciblee | ATTAQUE, cible LIGNE_ENNEMIE, valeur 8 | conservée (« Laser perçant ») |
| CRT_10 | Bouclier | Base | Defense | Module Unique | 1 | 4 | — | — | Bouclier de X sur un module unique | DEFENSE, cible ALLIE_UNIQUE, valeur 4 | conservée (« Bouclier ») |
| CRT_11 | Protéger le vaisseau | Base | Defense | Module Principal | 1 | 6 | — | — | Bouclier de X sur le module principal | DEFENSE, cible MODULE_PRINCIPAL, valeur 6 | conservée (« Protéger le vaisseau ») |
| CRT_12 | Réparation | Base | Reparation | Module Principal | 1 | 8 | — | 2 | Repare le module principal pour X | REPARATION, cible MODULE_PRINCIPAL, valeur 8 | conservée (« Réparation ») |
| CRT_45 | Tir incendiaire | Commune | Attaque | Ennemi Unique | 2 | 4 | — | 3 | Ajoute X points d’incendie sur la cible | *Non jouable :* incendie (equivalent du poison de Slay the Spire : intensite cumulative qui decroit de 1 par tour, cf. specs/refonte-buffs-debuffs.md) non supporte par le moteur actuel. Nom invente, a valider. | conservée (« Tir incendiaire ») |
| CRT_46 | Blindage cible | Commune | Defense | Module Unique | 2 | 8 | — | 3 | Bouclier de X sur un module unique | DEFENSE, cible ALLIE_UNIQUE, valeur 8 | conservée (« Blindage ciblé ») |
| CRT_47 | Laser lourd | Commune | Attaque | Ennemi Unique | 1 | 12 | — | — | Inflige X degats a un ennemi unique | ATTAQUE, cible ENNEMI_UNIQUE, valeur 12 | conservée (« Laser lourd ») |
| CRT_48 | Bouclier stabilise | Rare | Buff | Module Principal | 3 | 1 | — | 1 | Les Boucliers de base sont lancés X fois de plus. | *Non jouable :* duplication d'effet des cartes Bouclier de rarete Base non supportee par le moteur actuel, meme famille que Salve laser/Protocole d'urgence. Nom invente, a valider. | conservée (« Bouclier stabilisé ») |
| CRT_49 | Salve laser | Rare | Buff | Module Tous | 2 | 1 | — | 2 | Les Laser de base sont lances X fois de plus. | *Non jouable :* duplication d'effet des cartes Laser de rarete Base non supportee par le moteur actuel, meme famille que Double defense/Circuit parallele. Nom invente, a valider. | conservée (« Salve laser ») |
| CRT_50 | Protocole d'urgence | Legendaire | Buff | Module Tous | 3 | 1 | — | 3 | Les cartes de bases sont lancees X fois de plus. | *Non jouable :* duplication d'effet des cartes de rarete Base non supportee par le moteur actuel. Nom invente, a valider. | conservée (« Protocole d'urgence ») |

### Lanceur de missiles (8)

| Id | Nom | Rareté | Catégorie | Cible (conception) | Coût | X | Y | Munitions | Description | Ancien effet | Aujourd'hui |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_13 | Missiles | Commune | Attaque | Ennemi Unique | 2 | 15 | 6 | — | Inflige X degats a un ennemi et Y a tous les autres | *Non jouable :* effet a deux valeurs (cible unique + splash) non supporte par le moteur actuel | conservée (« Missiles ») |
| CRT_14 | Torpille | Commune | Attaque | Ennemi Tous | 2 | 10 | 8 | — | Inflige X degats a la ligne avant et Y a la ligne arriere | *Non jouable :* effet a deux valeurs (deux zones distinctes) non supporte par le moteur actuel | conservée (« Torpille ») |
| CRT_15 | Ciel de missiles | Rare | Attaque | Ennemi Tous | 1 | 8 | — | — | Inflige X degats a tous les ennemis | ATTAQUE, cible ENNEMIS_MULTIPLES, valeur 8 | conservée (« Ciel de missiles ») |
| CRT_16 | Ligne arriere | Commune | Attaque | Ennemi Arriere | 1 | 8 | — | — | Inflige X degats a tous les ennemis de la ligne arriere | ATTAQUE, cible COLONNE_ARRIERE_ENNEMIE, valeur 8 | conservée (« Ligne arrière ») |
| CRT_17 | Embrasement | Rare | Attaque | Ennemi Unique | 2 | 8 | — | — | Ajoute X points d’incendie à un ennemi | *Non jouable :* incendie (equivalent du poison de Slay the Spire : intensite cumulative qui decroit de 1 par tour, cf. specs/refonte-buffs-debuffs.md) non supporte par le moteur actuel | conservée (« Embrasement ») |
| CRT_18 | Leurre | Rare | Defense | Module Unique | 1 | 0 | — | — | Annule la prochaine attaque ciblant le module | DEFENSE, cible ALLIE_UNIQUE, valeur 0, action ANNULATION_PROCHAINE_ATTAQUE | conservée (« Leurre ») |
| CRT_19 | Guerre nucleaire | Legendaire | Attaque | Ennemi Tous | 3 | 8 | — | — | Ajoute X points d’incendie à tous les ennemis | *Non jouable :* incendie (equivalent du poison de Slay the Spire : intensite cumulative qui decroit de 1 par tour, cf. specs/refonte-buffs-debuffs.md) non supporte par le moteur actuel | conservée (« Guerre nucléaire ») |
| CRT_9 | Bombardement | Commune | Attaque | Ennemi Tous | 1 | 6 | — | — | Inflige X degats a tous les ennemis | ATTAQUE, cible ENNEMIS_MULTIPLES, valeur 6 | conservée (« Bombardement ») |

### Blindage (7)

| Id | Nom | Rareté | Catégorie | Cible (conception) | Coût | X | Y | Munitions | Description | Ancien effet | Aujourd'hui |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_20 | Mode defensif | Commune | Defense | Module Tous | 2 | 8 | — | — | Bouclier de X sur tous les modules | DEFENSE, cible ALLIES_MULTIPLES, valeur 8 | **supprimée** |
| CRT_21 | Bouclier adaptatif | Commune | Defense | Module Unique | 1 | 50 | — | — | Bouclier de X% des points de vie du module | DEFENSE, cible ALLIE_UNIQUE, valeur 50, action BOUCLIER_POURCENTAGE_PV | **supprimée** |
| CRT_22 | Transfert | Commune | Defense | Module Unique | 1 | 0 | — | — | Les degats du module cible sont transferes au module Blindage au prochain tour | *Non jouable :* mecanique de redirection de degats non supportee par le moteur actuel | **supprimée** |
| CRT_23 | Proteger l'avant poste | Commune | Defense | Module Avant | 2 | 13 | — | — | Bouclier de X sur tous les modules de la ligne avant | DEFENSE, cible COLONNE_AVANT_ALLIEE, valeur 13 | **supprimée** |
| CRT_24 | Blindage maximal | Rare | Defense | Module Principal | 1 | 8 | 3 | — | Bouclier de X sur le module principal pour les Y prochains tours | BUFF, cible MODULE_PRINCIPAL, valeur 8, action BOUCLIER_PAR_TOUR, durée 3 | **supprimée** |
| CRT_25 | Renvoi | Rare | Defense | Module Unique | 1 | 15 | — | — | Bouclier miroir de X | DEFENSE, cible ALLIE_UNIQUE, valeur 15, action BOUCLIER_MIROIR | **supprimée** |
| CRT_26 | Bouclier perpetuel | Legendaire | Buff | Module Unique | 3 | 10 | — | 2 | Le module recoit un bouclier de X chaque tour | BUFF, cible ALLIE_UNIQUE, valeur 10, action BOUCLIER_PAR_TOUR | **supprimée** |

### Generateur (6)

| Id | Nom | Rareté | Catégorie | Cible (conception) | Coût | X | Y | Munitions | Description | Ancien effet | Aujourd'hui |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_27 | Surcharge temporaire | Commune | Outils | Module Tous | 0 | 2 | — | — | Gagne X electricite | OUTILS, cible ALLIES_MULTIPLES, valeur 2, action GAIN_ELECTRICITE | **supprimée** |
| CRT_28 | Optimisation des boucliers | Commune | Buff | Module Tous | 3 | 1 | — | 1 | Le cout de toutes les cartes Defense passe a X | *Non jouable :* modification de cout des cartes non supportee par le moteur actuel | **supprimée** |
| CRT_29 | Attaques performantes | Commune | Buff | Module Tous | 3 | 1 | — | 1 | Le cout de toutes les cartes attaque passe a X | *Non jouable :* modification de cout des cartes non supportee par le moteur actuel | **supprimée** |
| CRT_30 | Double defense | Rare | Buff | Module Tous | 3 | 1 | — | — | Les cartes Defense sont jouees X fois de plus | *Non jouable :* duplication d'effet de carte non supportee par le moteur actuel | **supprimée** |
| CRT_31 | Fonds de tiroir | Rare | Outils | Module Tous | 1 | 1 | — | — | Gagne X electricite par module actif | OUTILS, cible ALLIES_MULTIPLES, valeur 1, action GAIN_ELECTRICITE_PAR_MODULE | **supprimée** |
| CRT_32 | Circuit parallele | Legendaire | Buff | Module Tous | 3 | 2 | — | — | Les cartes Attaque sont jouees X fois de plus | *Non jouable :* duplication d'effet de carte non supportee par le moteur actuel | **supprimée** |

### Sabotage (6)

| Id | Nom | Rareté | Catégorie | Cible (conception) | Coût | X | Y | Munitions | Description | Ancien effet | Aujourd'hui |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_33 | Tordre le canon | Commune | Debuff | Ennemi Unique | 1 | 5 | — | — | Diminue les degats de l'ennemi de X au prochain tour | DEBUFF, cible ENNEMI_UNIQUE, valeur 5, action REDUCTION_DEGATS, durée 1 | **supprimée** |
| CRT_34 | Breche | Commune | Debuff | Ennemi Unique | 1 | 100 | — | — | Augmente les degats subis par l'ennemi de X% pendant Y tours | DEBUFF, cible ENNEMI_UNIQUE, valeur 100, action VULNERABILITE, durée 2 | **supprimée** |
| CRT_35 | Ligne avant | Commune | Debuff | Ennemi Avant | 1 | 100 | — | — | Augmente les degats subis par la ligne avant ennemie de X% pendant Y tours | DEBUFF, cible COLONNE_AVANT_ENNEMIE, valeur 100, action VULNERABILITE, durée 2 | **supprimée** |
| CRT_36 | Tir allie | Rare | Debuff | Ennemi Unique | 2 | — | — | — | Change la cible de l'ennemi pour un de ses voisins au prochain tour | DEBUFF, cible ENNEMI_UNIQUE, valeur 0, action REDIRECTION_CIBLE, durée 1 | **supprimée** |
| CRT_37 | Boucliers endomages | Rare | Debuff | Ennemi Tous | 2 | 100 | — | — | Augmente les degats subis par tous les ennemis de X% pendant Y tours | DEBUFF, cible ENNEMIS_MULTIPLES, valeur 100, action VULNERABILITE, durée 2 | **supprimée** |
| CRT_38 | Boucliers hors service | Legendaire | Debuff | Ennemi Tous | 3 | 100 | 5 | — | Augmente les degats subis par tous les ennemis de X% pour les Y prochains tours | DEBUFF, cible ENNEMIS_MULTIPLES, valeur 100, action VULNERABILITE, durée 5 | **supprimée** |

### Soute (6)

| Id | Nom | Rareté | Catégorie | Cible (conception) | Coût | X | Y | Munitions | Description | Ancien effet | Aujourd'hui |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_39 | Boost | Commune | Outils | Module Unique (n'importe lequel, la cible n'affecte pas l'effet) | 1 | 2 | — | — | Pioche X cartes supplementaires | OUTILS, cible ALLIE_UNIQUE, valeur 2, action PIOCHE_SUPPLEMENTAIRE | **supprimée** |
| CRT_40 | Changement d'outil | Commune | Outils | Module Unique (n'importe lequel, la cible n'affecte pas l'effet) | 0 | 1 | 1 | — | Pioche X carte, defausse Y carte | *Non jouable :* manipulation de pioche/defausse non supportee par le moteur actuel | **supprimée** |
| CRT_41 | Manque de jus | Commune | Outils | Module Unique (n'importe lequel, la cible n'affecte pas l'effet) | 0 | 1 | — | — | Defausse X carte, gagne X electricite | *Non jouable :* manipulation de defausse/electricite non supportee par le moteur actuel | **supprimée** |
| CRT_42 | Canibalisme | Rare | Outils | Module Unique (n'importe lequel, la cible n'affecte pas l'effet) | 0 | 1 | 3 | — | Defausse de X a Y cartes, gagne 1 electricite par carte defaussee | *Non jouable :* manipulation de defausse/electricite non supportee par le moteur actuel ; quantite a defausser choisie par le joueur entre X et Y, mecanique de choix supplementaire non supportee | **supprimée** |
| CRT_43 | Grand remplacement | Rare | Outils | Module Unique (n'importe lequel, la cible n'affecte pas l'effet) | 1 | — | — | — | Defausse la main, pioche le meme nombre de cartes | *Non jouable :* manipulation de main/pioche non supportee par le moteur actuel | **supprimée** |
| CRT_44 | Multi fonction | Legendaire | Outils | Module Unique (n'importe lequel, la cible n'affecte pas l'effet) | 3 | 2 | 4 | — | Pioche X cartes en plus pour les Y prochains tours | *Non jouable :* manipulation de pioche + effet a duree non supportes par le moteur actuel | **supprimée** |

**Bilan** : 44 cartes, dont 19 conservées dans le jeu actuel et 25 supprimées ; 10 modules, dont 2 conservés.
