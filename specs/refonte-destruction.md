# Buff « Destruction » — brouillon de conception

*Document de travail, rien n'est implémenté. **En attente** (décision utilisateur, 2026-11-08) :
aucune carte ne pose encore ce buff ; à reprendre quand les premières cartes Destruction seront
conçues. Principe et idées de cartes : [refonte-modules.md](refonte-modules.md) §4. Une fois
tranché, le contenu ira dans [modules-cartes.md](modules-cartes.md) (§12) et ce fichier sera
supprimé.*

---

## 1. Rappel du principe (décidé)

Des **cartes** donnent à un module le **buff « Destruction »**, qui porte un effet déclenché quand
ce module est détruit. Exemple :

> « Applique à un module : **Destruction** — inflige 10 dégâts à tous les ennemis »

Le buff se déclenche à la destruction du module puis **disparaît** ; plusieurs buffs sur un même
module se déclenchent **tous**, dans l'ordre de pose. Un module ressuscité ne redéclenche donc pas
un buff déjà consommé.

---

## 2. Format envisagé dans `config/carte_new.json`

Une nouvelle nature d'effet `DESTRUCTION`, dont les effets déclenchés sont décrits avec le format
habituel (valeurs nommées de la carte), dans une liste imbriquée :

```json
"description": "Applique à un module : Destruction - inflige {degats} degats a tous les ennemis",
"cible": "Module Unique",
"valeurs": { "degats": 10 },
"effets": [
  { "nature": "DESTRUCTION", "declenche": [
      { "nature": "DEGATS", "valeur": "degats", "portee": "TOUS_ENNEMIS" }
  ] }
]
```

---

Destruction porte des effets, pas un nombre : ce n'est **pas un statut** du dictionnaire de
[refonte-statuts.md](refonte-statuts.md), il aura son propre champ sur le module.

## 3. Points à trancher (propositions par défaut)

1. **Ce que vise l'effet déclenché.** La carte vise un module allié, l'effet déclenché vise autre
   chose : nouvelles portées à définir — tous les ennemis, l'ennemi qui a détruit le module, un
   ennemi au hasard, le module principal, tous les modules alliés vivants. Cas limite :
   « l'ennemi qui a détruit le module » quand la destruction vient d'une attaque de zone, de
   l'incendie, d'un dégât renvoyé ou d'un sacrifice volontaire. *Proposition* : l'ennemi auteur du
   coup s'il y en a un, sinon l'effet ne fait rien.
2. **Moment du déclenchement.** *Proposition* : **immédiatement** à la destruction, avant l'action
   ennemie suivante ; une explosion peut tuer un ennemi avant qu'il n'attaque, et tuer le dernier
   ennemi gagne le combat.
3. **Valeurs utilisées.** Si une carte de bonus augmente les valeurs de la carte Destruction après
   sa pose : *proposition* : le buff **garde les valeurs du moment où la carte est jouée** (photo),
   il ne change plus ensuite.
4. **Modules concernés.** *Proposition* : **modules secondaires uniquement** (la destruction du
   principal termine la run) : une cible « module secondaire », ou une règle qui refuse le
   principal pour ce buff.
5. **Effets autorisés dans `declenche`.** *Proposition* : tous les effets ordinaires (dégâts,
   bouclier, réparation, incendie, vulnérabilité, pioche, électricité), mais **pas de Destruction
   imbriquée ni de répétition**, pour éviter les chaînes.
6. **Cumul** (décidé) : tous les buffs se déclenchent, dans l'ordre de pose. Conséquence : une
   carte lancée deux fois (`lancements`, ou sous un effet de répétition) pose **deux** buffs.
7. **Affichage.** Le module montre son buff (pastille, et une ligne dans l'infobulle, ex.
   « Destruction : 10 dégâts à tous les ennemis »). *Proposition* : un petit texte propre au buff,
   avec ses valeurs nommées, distinct de la description de la carte.
