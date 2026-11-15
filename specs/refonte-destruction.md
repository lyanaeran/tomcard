# Modules sacrifiables : destruction, résurrection, sacrifice — pistes non codées

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **Rien de ce document n'est
codé.** Il regroupe (2026-11-14) le brouillon du buff « Destruction » et les pistes de l'ancien
brouillon `refonte-modules.md`, dont la partie codée (PV du principal seuls persistants, pile Hors
service, mot-clé Persistante, rattachement des cartes, modèle `Module`) est maintenant dans
[combat.md](combat.md) §3.4 et [modules-cartes.md](modules-cartes.md) §4 et §12.4. Les choix
marqués « décision utilisateur » sont validés ; le reste est une proposition.*

---

## 1. Principe du buff « Destruction » (décision utilisateur, 2026-11-08)

Un module n'a **pas d'effet à la destruction propre à son type**. Ce sont des **cartes** qui
donnent à un module le **buff « Destruction »**, qui porte un effet déclenché quand ce module est
détruit (façon « Râle d'agonie » de Hearthstone). Exemple :

> « Applique à un module : **Destruction** — inflige 10 dégâts à tous les ennemis »

- La carte cible un **module allié** ; l'effet déclenché vise **autre chose**.
- Le buff se déclenche à la destruction du module puis **disparaît** ; plusieurs buffs sur un même
  module se déclenchent **tous**, dans l'ordre de pose. Un module ressuscité ne redéclenche donc
  pas un buff déjà consommé.
- **En attente** : aucune carte ne pose encore ce buff.

---

## 2. Format envisagé dans `config/cartes.json`

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
combat.md §3.5, il aura son propre champ sur le module.

## 3. Points à trancher sur le buff (propositions par défaut)

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

---

## 4. Idées de cartes Destruction (toutes valeurs inventées)

| Effet déclenché | Rôle tactique |
|---|---|
| 8 dégâts à tous les ennemis | Mourir au bon moment finit un combat |
| Bouclier de 10 sur le module principal | Protège le principal juste quand il devient exposé |
| +2 électricité au prochain tour | Accélère le tour suivant |
| Pioche 2 cartes | Compense la perte des cartes du module (pile Hors service) |
| Vulnérabilité sur l'ennemi qui a détruit le module | Punit l'attaquant |
| 15 dégâts à l'ennemi qui a détruit le module | Idem, version brute |
| L'ennemi qui a détruit le module perd sa prochaine action | Gagne un tour |
| Répare le module principal de 8 PV | Seule source de soin « gratuite » du principal : à doser |
| Tous les ennemis subissent +50 % de dégâts pendant 1 tour | Fenêtre d'attaque |

Ces cartes peuvent donner une identité aux modules sans cartes (Canon lourd, Contrôle, Atelier,
Radar). Autre idée, distincte du buff : une carte ou un module qui réagit à **n'importe quelle**
mort alliée (*Recyclage* : « gagne 1 électricité chaque fois qu'un module allié meurt ce
combat »).

---

## 5. Résurrection

### 5.1 Pistes

| Mécanique | Effet | Remarque |
|---|---|---|
| Carte *Reconstruction* (reprise de modules-cartes.md §4.2) | Ressuscite un module mort à X PV, munitions limitées | Lui rend aussi ses cartes (elles reviennent de la pile Hors service dans la défausse) : forte valeur |
| Module *Atelier* (passif) | Un module mort revient seul après 2 tours, à moitié de ses PV | Façon « Réincarnation » de Hearthstone ; une seule fois par module et par combat |
| Carte *Nanobots* | Pose un buff sur un module vivant : s'il meurt dans les 2 tours, il revient à 1 PV | Prépare la mort plutôt que la réparer ; s'inscrit dans le modèle de durée de la refonte des buffs |
| *Pièces détachées* | Chaque mort de module donne 1 « pièce » ; X pièces = un module ressuscité | Ressource de combat supplémentaire, plus lourd à afficher |

- **Les cartes d'un module ressuscité** reviennent de la pile Hors service **dans la défausse** :
  elles réapparaissent au prochain remélange, sans arriver d'un coup en main. Une carte de
  résurrection plus rare pourrait les renvoyer directement dans la pioche (mélangées), voire en
  main.
- **Une carte de résurrection doit être Persistante** (contrainte de conception) : sinon, rattachée
  au module mort, elle serait elle-même hors service et ne pourrait pas le ressusciter
  (modules-cartes.md §12.4).

### 5.2 Combo mort + résurrection : garde-fou nécessaire

Le buff Destruction **disparaît quand il se déclenche** (§1) : un module ressuscité ne le
redéclenche pas à sa mort suivante, sauf si une nouvelle carte le lui rend. La boucle mort /
résurrection ne peut donc pas se répéter seule. Garde-fou restant à décider : limiter la
résurrection à **une fois par module et par combat**.

---

## 6. Sacrifice volontaire

Pour que la destruction d'un module soit un choix et pas seulement une conséquence subie :

- Carte *Éjection* (0 ou 1⚡) : détruit un de vos modules secondaires, ce qui déclenche ses buffs
  Destruction, et donne un bonus (ex. +1 électricité, ou pioche 1).
- Variante : *Surcharge critique* — double les effets Destruction du module sacrifié.

Rend la mort **active** (on choisit quand faire exploser un module chargé de Destruction) plutôt
que seulement subie.

---

## 7. Interactions avec l'existant

- **Un module qui meurt protège encore** : tant qu'il est vivant, il absorbe les coups
  `PROXIMITE` ; sa mort expose les modules suivants, puis le principal. Le PV max des secondaires
  règle donc directement **combien de tours le principal est à l'abri** : à mesurer par
  simulation pour régler ces PV (combat.md §13.5).
- **Fonds de tiroir** (+1 électricité par module actif) : pénalisée quand des modules meurent.
  Cohérent avec le thème, à garder en tête.
- **Récompense de combat** (modules-cartes.md §6 : une carte candidate par module équipé) : un module mort pendant le
  combat propose quand même sa candidate, puisqu'il revient au combat suivant.
- **Leurre**, **boucliers** : protéger un secondaire devient un choix (le garder en vie pour ses
  cartes) plutôt qu'une obligation (préserver des PV pour la suite de la run).
- **Montée des dégâts ennemis** (aujourd'hui : l'augmentation des valeurs des ennemis, combat.md §13.1.3) : rend les morts certaines dans les combats
  longs, donc les cartes Destruction systématiquement utiles.
- **Ciblage** : si `PROXIMITE` protège trop bien le principal, prévoir plus d'ennemis à
  `TOUS_MODULES` ou un ciblage qui vise le principal en priorité.

---

## 8. Autres points à trancher

1. **Résurrection** : quelles pistes garder (§5.1) ; la limiter à une fois par module et par
   combat (§5.2).
2. **Sacrifice volontaire** (§6) : oui ou non.
3. **Réparer** à la Station : ne sert plus qu'au principal ; la garder telle quelle, ou la rendre
   plus chère ou plus forte.
4. **Cartes obtenues hors module** (Aventure, Planète commerciale) : rattachées au principal pour
   l'instant, ce qui les rend insensibles à la perte des modules (a-trancher.md §9.1).
