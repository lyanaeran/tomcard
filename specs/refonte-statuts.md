# Statuts (buffs, debuffs, bouclier) — conception

*Document de travail. Modèle codé (`src/gameplay/statut_new.py`), utilisé par `ModuleNew` et
`EnnemiNew`, pas encore branché au combat. Une fois stabilisé, le contenu ira dans
[combat.md](combat.md) et ce fichier sera supprimé. Voir aussi
[refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) (réflexion d'origine),
[refonte-ennemis.md](refonte-ennemis.md), [refonte-modules.md](refonte-modules.md).*

---

## 1. Principe (décision utilisateur, 2026-11-11)

Bouclier, incendie, renvoi, leurre… et les buffs/debuffs à venir sont gérés **ensemble**, de la
même façon pour les **modules** et les **ennemis**, au lieu d'un champ par effet dans chaque
classe.

- Chaque entité en combat porte ses **statuts** : un dictionnaire **statut → intensité**
  (`{BOUCLIER: 6, INCENDIE: 3}`) ; un statut absent vaut 0, une intensité tombée à 0 est retirée.
- La clé est une **énumération** (`Statut`), pas un texte : une faute de frappe est une erreur
  immédiate.
- Chaque statut **déclare sa règle** ; le code applique la règle, sans cas particulier par statut
  sauf ce qui lui est vraiment propre (dégâts de l'incendie, renvoi des dégâts).
- Le code est **partagé** : `Statuts` (`statut_new.py`) sert à `ModuleNew` comme à `EnnemiNew`.

---

## 2. Règle d'un statut

Deux caractéristiques :

| Caractéristique | Valeurs |
|---|---|
| **Cumul** : ce que fait une nouvelle pose d'un statut déjà présent | **Addition** des intensités, ou **Remplacement** (non cumulable) |
| **Extinction** : comment il disparaît | **−1 par tour** (à chaque fin de tour), **fin du tour** (disparaît entièrement), ou **consommation** (seulement en servant) |

## 3. Statuts actuels

| Statut | Cumul | Extinction | Effet |
|---|---|---|---|
| **Bouclier** | Addition | −1 par tour | Absorbe les dégâts avant les PV |
| **Incendie** | Addition | −1 par tour | Inflige son intensité en dégâts à la fin du tour, avant la baisse |
| **Renvoi** | Remplacement | Fin du tour | Renvoie à l'attaquant les dégâts reçus jusqu'à son intensité, qui diminue d'autant ; l'entité encaisse le reste (Miroir) |
| **Leurre** | Remplacement | Consommation | Annule entièrement la prochaine attaque reçue, puis disparaît (intensité 1) |

Décisions utilisateur : bouclier et incendie (−1 par tour, cumulables), renvoi de Miroir (non
cumulable, un tour). Le **renvoi comme stock qui diminue** à chaque coup est une interprétation à
valider ([refonte-ennemis.md](refonte-ennemis.md) §4.1).

---

## 4. Déroulement

### 4.1 Attaque reçue

1. **Leurre** : s'il est présent, l'attaque est entièrement annulée et le leurre disparaît.
2. **Renvoi** : il prend les dégâts jusqu'à son intensité restante ; ces dégâts sont renvoyés à
   l'attaquant.
3. **Bouclier** : il absorbe ce qui reste.
4. Le reste est retiré des **PV**.

### 4.2 Fin de tour

À la **fin du tour de l'adversaire** de l'entité (décision utilisateur) : fin du tour du joueur
pour un ennemi, fin du tour ennemi pour un module.

1. **L'incendie frappe** de son intensité, **absorbé par le bouclier** (jamais renvoyé ni annulé
   par le leurre).
2. Chaque statut **s'éteint selon sa règle** : bouclier et incendie −1, renvoi retiré, leurre
   inchangé.

---

## 5. Points ouverts

1. **Carte *Renvoi* du joueur** (`BOUCLIER_MIROIR` dans `config/carte_new.json`) : la carte la
   décrit comme durant **jusqu'à consommation**, alors que le renvoi de Miroir dure **un tour**.
   Même statut avec une règle commune, ou deux statuts distincts ?
2. **Statuts à durée** (Vulnérabilité, Réduction de dégâts : une intensité **et** une durée en
   tours, cumul « Durée » de `CarteNew`) : une intensité seule ne suffit plus ; il faudra une
   petite valeur (intensité, tours restants) pour ces statuts.
3. **Destruction** ([refonte-destruction.md](refonte-destruction.md)) porte des **effets**, pas un
   nombre : ce n'est pas un statut de ce dictionnaire, il aura son propre champ.
4. **Lien avec les cartes** : `CarteNew` décrit le cumul de ses effets avec sa propre énumération
   (`Cumul`) ; au branchement, chaque nature d'effet qui pose un statut renverra au `Statut`
   correspondant, et les deux descriptions devront être alignées.
