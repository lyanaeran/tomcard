# Effets à coder — conception en cours

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). Liste les **nouveaux effets
décidés ou en réflexion, pas encore codés**. **On ne les code pas** tant que l'utilisateur n'a pas
avancé dans sa réflexion et ne l'a pas demandé (décision utilisateur, 2026-11-16). Les choix
marqués « décision utilisateur » sont validés ; ceux marqués « proposition » sont à confirmer.
Une fois un effet codé, sa règle part dans [combat.md](combat.md) §3.5 (statuts) ou
[modules-cartes.md](modules-cartes.md) §12, et il est retiré d'ici.*

---

## 1. Surcharge (statut)

### 1.1 Décisions utilisateur (2026-11-16)

- **Un seul statut**, nommé **Surcharge**, comme l'Incendie ou le Bouclier. Les autres usages du
  mot « surcharge » sont renommés (§1.6).
- **Effet** : augmente les dégâts. Il est **porté par le module principal**, mais s'applique à
  **toutes les cartes** du joueur, quel que soit leur module.
- **Baisse de 1 à chaque tour.**
- **Il servira aussi aux ennemis**, en particulier pour augmenter les dégâts des boss : comme les
  autres statuts, il sera partagé par les modules et les ennemis (combat.md §3.5).

### 1.2 Règle proposée

- **Cumul** : addition (deux poses de 2 donnent 4), comme le bouclier et l'incendie
  (proposition).
- **Chaque coup** porté par une carte reçoit **+intensité** dégâts : chaque cible d'une carte de
  zone et chaque lancement d'une carte lancée plusieurs fois (proposition, discutée le 2026-11-16 :
  un seul statut plutôt qu'un pour les cibles uniques et un pour la zone).
- **Ce qui n'est pas concerné** (proposition) : l'incendie (statut posé, pas un coup) et les
  dégâts renvoyés.
- Le bonus s'ajoute **avant** les protections de la cible : le leurre annule tout le coup, le
  renvoi puis le bouclier prennent leur part du total.

Exemples avec Surcharge 2 :

| Carte | Sans | Avec Surcharge 2 | Gain |
|---|---|---|---|
| Laser (6, un ennemi) | 6 | 8 | +2 |
| Laser perçant (8, ligne de 2 ennemis) | 16 | 20 | +4 |
| Missiles (15, puis 6 sur 2 autres) | 27 | 33 | +6 |
| Bombardement (6 sur 3 ennemis) | 18 | 24 | +6 |
| Laser lancé 2 fois (Salve laser) | 12 | 16 | +4 |

### 1.3 Baisse : à quel moment ?

**Décision utilisateur (2026-11-25)** : la règle commune de combat.md §3.5.2 s'applique, tous les
statuts d'une entité baissent ensemble à la fin du tour de son adversaire. La Surcharge du
principal baisse donc **à la fin du tour ennemi** (option A ci-dessous) ; celle d'un ennemi, à la
fin du tour du joueur. Historique de la question :


« Baisse de 1 à chaque tour » laisse un choix :

- **A. À la fin du tour ennemi** (proposition), comme le bouclier d'un module : posée à 2 pendant
  le tour 1, elle donne +2 au tour 1, +1 au tour 2, puis disparaît.
- **B. À la fin du tour du joueur** : posée à 2, elle donne +2 au tour 1 seulement… puis +1 au
  tour 2. Même résultat ici, mais une Surcharge de 1 ne servirait que le tour de sa pose.

Différence réelle seulement pour les ennemis : leur Surcharge baisserait à la fin de **leur**
tour (proposition), pour qu'un boss qui se la pose en profite au tour suivant.

### 1.4 Ennemis (à préciser)

- Nouvelle nature d'effet ennemi `SURCHARGE`, cible `SOI_MEME` (proposition) : par exemple un boss
  qui se pose Surcharge 3 tous les trois tours.
- Elle s'ajoute à **chaque coup** de ses attaques : chaque module pour une attaque sur tous les
  modules, chaque répétition (proposition).
- Question : garder aussi l'**augmentation des valeurs** des ennemis avec les tours (combat.md
  §13.1.3), ou la remplacer par la Surcharge pour les boss ?

### 1.5 Carte et affichage

- **Carte** : `CRT_51` *Lasers en surchauffe* (Rare, Buff, 1 électricité, 3 munitions, module
  Lanceur de missiles, cible Module Principal, valeur 2), ajoutée dans `config/cartes.json`
  le 2026-11-16 avec **`"jouable": "non"`** : elle n'est jamais proposée tant que l'effet n'est
  pas codé.
- **Code déjà en place, sans effet** : la nature `SURCHARGE` est déclarée dans
  `src/gameplay/carte.py` pour que le fichier se charge, et le combat la **refuse**
  (`combat.NATURES_NON_GEREES`) ; un test vérifie qu'aucune carte jouable n'utilise un effet non
  codé.
- **Description** à revoir avec l'utilisateur : « attaques directes » → par exemple « chaque coup
  de vos cartes inflige {surcharge} dégâts de plus » ; la valeur nommée `buff` pourrait devenir
  `surcharge`.
- **Affichage** (proposition) : pastille sur le module principal (comme Incendie, Renvoi,
  Leurre), dans une couleur à choisir ; infobulle « Surcharge 2 : +2 dégâts à chaque coup, −1 par
  tour » ; journal : « Laser → Pat le Pirate : 8 dégâts (dont 2 de surcharge)… ».

### 1.6 Autres usages du mot « surcharge » (décision utilisateur : on les change)

- Idée de carte du **Canon lourd** « Surcharge » (modules-cartes.md §4.1) → **Tir de rupture**
  (proposition de nom).
- Idée de carte « *Surcharge critique* » (refonte-destruction.md §6) → **Réaction en chaîne**
  (proposition de nom).
- Commentaire du code sur le gain d'électricité, qui citait l'ancienne carte *Surcharge
  temporaire* : retiré.
- **Gardés** : l'image `assets/cartes/surcharge.png` (un éclair, qui illustre bien la Surcharge ;
  elle sert aujourd'hui à *Embrasement*, qui pourrait recevoir une image de feu) et l'ancienne
  carte *Surcharge temporaire* dans [archive-cartes-modules.md](archive-cartes-modules.md)
  (archive, recopiée telle quelle).

---

## 2. Autres effets en attente

Rappel, détail ailleurs :

- **Vulnérabilité, Réduction de dégâts, Tir allié** : statuts à durée, non codés
  (combat.md §3.8.4 ; réflexion d'origine dans [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md)).
- **Buff Destruction, résurrection, sacrifice** : [refonte-destruction.md](refonte-destruction.md).
- **Mécaniques des anciennes cartes** (méta-effets, pioche, électricité…) :
  modules-cartes.md §12.6 et [archive-cartes-modules.md](archive-cartes-modules.md).
