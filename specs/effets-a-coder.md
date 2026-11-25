# Effets à coder — conception en cours

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). Liste les **nouveaux effets
décidés ou en réflexion, pas encore codés**. **On ne les code pas** tant que l'utilisateur n'a pas
avancé dans sa réflexion et ne l'a pas demandé (décision utilisateur, 2026-11-16). Les choix
marqués « décision utilisateur » sont validés ; ceux marqués « proposition » sont à confirmer.
Une fois un effet codé, sa règle part dans [combat.md](combat.md) §3.5 (statuts) ou
[modules-cartes.md](modules-cartes.md) §12, et il est retiré d'ici.*

---

## 1. Surcharge des ennemis

La **Surcharge du joueur est codée** depuis le 2026-11-25 (lot 3 de [plan-cartes.md](plan-cartes.md)) :
règles dans [combat.md](combat.md) §3.5 et §3.8.4, natures dans [modules-cartes.md](modules-cartes.md)
§12.2. Les décisions d'origine (2026-11-16) et le renommage des autres usages du mot « surcharge »
sont dans l'historique git de ce fichier. Reste à décider la Surcharge **des ennemis** :

### 1.1 Surcharge des ennemis (à préciser)

- Nouvelle nature d'effet ennemi `SURCHARGE`, cible `SOI_MEME` (proposition) : par exemple un boss
  qui se pose Surcharge 3 tous les trois tours.
- Elle s'ajoute à **chaque coup** de ses attaques : chaque module pour une attaque sur tous les
  modules, chaque répétition (proposition).
- Question : garder aussi l'**augmentation des valeurs** des ennemis avec les tours (combat.md
  §13.1.3), ou la remplacer par la Surcharge pour les boss ?

---

## 2. Autres effets en attente

Rappel, détail ailleurs :

- **Vulnérabilité, Réduction de dégâts, Tir allié** : statuts à durée, non codés
  (combat.md §3.8.4 ; réflexion d'origine dans [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md)).
- **Buff Destruction, résurrection, sacrifice** : [refonte-destruction.md](refonte-destruction.md).
- **Mécaniques des anciennes cartes** (méta-effets, pioche, électricité…) :
  modules-cartes.md §12.6 et [archive-cartes-modules.md](archive-cartes-modules.md).
