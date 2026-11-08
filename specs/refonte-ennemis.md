# Refonte des ennemis — brouillon de conception

*Document de travail, rien n'est implémenté. Les choix marqués « décision utilisateur » sont
validés ; le reste est une proposition. Une fois stabilisé, le contenu ira dans
[combat.md](combat.md) (§3.2, §13) et ce fichier sera supprimé. Voir aussi
[refonte-buffs-debuffs.md](refonte-buffs-debuffs.md), [refonte-modules.md](refonte-modules.md),
et la synthèse de simulation `outils/simulation/synthese/analyse_2026-11-07.md`.*

---

## 1. Existant

### 1.1 Les 6 ennemis (`config/ennemis.json`)

| Ennemi | PV | Taille | Placement préféré | Actions |
|---|---|---|---|---|
| Pat le Pirate | 50 | S | — | attaque 5, au plus proche |
| Le nettoyeur | 25 | S | protégé, à l'arrière | attaque 7, deux fois par tour, au plus proche |
| Petit Jean | 100 | S | protecteur, à l'avant | attaque 2 ; tous les 2 tours, se pose un « bouclier par tour » de 3 pendant 2 tours |
| Le puzzle | 50 | S | — | attaque 5 sur **tous** les modules |
| Miroir | 50 | S | — | attaque 2 ; chaque tour, pose un bouclier miroir de 5 (permanent, cumulable) sur l'ennemi de la colonne avant, lui-même s'il est seul |
| Boss des pirates | 150 | M, 2 cases | — | attaque 5 sur tous les modules ; à partir du tour 2, tous les 3 tours, +2 dégâts (cumulé) ; à partir du tour 3, tous les 3 tours, un « bouclier par tour » de 5 |

### 1.2 Modèle actuel

- **Actions** : attaquer (`ATTAQUE`) ou poser un buff (`POSE_BUFF`), chacune avec une cible, une
  **fréquence**, un **tour de départ** et un nombre de **répétitions** ; plusieurs actions peuvent
  se déclencher le même tour.
- **Cibles** : le module le plus proche, tous les modules, lui-même, l'ennemi de la colonne avant.
- **Intention** du prochain tour affichée au joueur.
- **Buffs** : même modèle que les buffs des cartes du moteur actuel.
- **Placement** : préférence de colonne pour certains ennemis ; le Boss occupe 2 cases.

### 1.3 Flottes

- **Prime** : 1 ennemi tiré au sort jusqu'au niveau 5, puis 2.
- **Boss** : le Boss des pirates seul, au niveau 10 (plusieurs boss tirés au sort prévus à terme,
  décision utilisateur antérieure).
- **Astéroïdes** : 3 ennemis.
- Les **tailles S/M/L** sont purement informatives : la composition ne tient pas encore compte de
  la difficulté prévue par niveau (combat.md §3.2).

### 1.4 Ce que la simulation a montré (règles actuelles)

- **Miroir rend le combat ingagnable** : bouclier miroir cumulable qui renvoie tous les dégâts ;
  127 des 149 fins de partie hors victoire.
- **Boss trop facile** : battu 51 fois sur 51, 5,7 PV perdus en moyenne.
- **Niveaux 2 à 5 trop faciles** (3 à 5 PV perdus par combat), pic aux niveaux 6 et 7 (2 ennemis).
- **Vraies défaites** surtout face au duo Le nettoyeur + Le puzzle (attaques multiples et zone).

---

## 2. Décisions déjà prises

- **Les ennemis sont gérés en dehors des cartes** : leurs mécaniques n'entrent pas dans
  `CarteNew` (décision utilisateur).
- **Le « bouclier par tour » est retiré** par la refonte des buffs : Petit Jean et le Boss sont à
  redessiner.
- **Le bouclier perd 1 par tour**, sans durée, **pour les ennemis comme pour les modules**
  (décision utilisateur) : celui d'un ennemi baisse de 1 **à la fin du tour du joueur**, une fois
  les dégâts du joueur encaissés ; celui d'un module, à la fin du tour ennemi. Les valeurs de
  bouclier des ennemis seront peut-être à réajuster en conséquence.
- **L'incendie inflige ses dégâts à la fin du tour de l'attaquant** (décision utilisateur) : sur un
  ennemi, à la fin du tour du joueur ; sur un module du joueur, à la fin du tour ennemi.
  *Proposition* pour l'ordre de fin de tour : l'incendie d'abord (absorbé par le bouclier comme des
  dégâts ordinaires, puis il baisse de 1), ensuite le bouclier perd 1.
- **La montée des dégâts propre à chaque ennemi** (refonte-buffs-debuffs.md §7.2) est désormais
  couverte par l'**augmentation des valeurs** (§3.3).

---

## 3. Nouveau modèle (décisions utilisateur, 2026-11-08)

### 3.1 Un cycle d'actions

Chaque ennemi a une **liste d'actions** jouée **dans l'ordre**, une étape par tour ; arrivé au bout,
il **repart à la première**, et ainsi de suite tout le combat. Remplace la fréquence et le tour de
départ actuels.

- L'**intention** devient simple à afficher : c'est la prochaine étape du cycle.
- **Une étape = une liste d'effets** joués le même tour (décision utilisateur), comme les effets
  d'une carte : ex. le Boss qui attaque et se protège dans la même étape.
- **Attaques multiples** : un **nombre de répétitions** sur l'effet (décision utilisateur) : Le
  nettoyeur attaque 2 fois avec la même valeur.

### 3.2 Des valeurs nommées, comme les cartes

Les actions renvoient à des **valeurs nommées** de l'ennemi (dictionnaire), comme les effets des
cartes : `{"degats": 6, "bouclier": 5}`, et une action « attaque » utilise `"degats"`.

### 3.3 Chaque valeur augmente avec le temps

Chaque valeur a une **augmentation** : de combien elle augmente, et tous les combien de tours.
Exemple : dégâts 6, +1 tous les 2 tours → 6, 6, 7, 7, 8… Remplace la montée des dégâts par ennemi
et l'Augmentation de dégâts du Boss (qui n'est plus un buff).

**Calcul (décision utilisateur)** : au tour 1 de l'ennemi, les valeurs valent leur base
(coefficient de difficulté compris, §3.4) ; l'augmentation s'applique **au début du tour du
joueur, à partir du tour 2** (l'intention affichée tient donc déjà compte de la nouvelle valeur).

```
valeur(tour) = arrondi_inferieur( (base + augmentation × paliers) × coefficient )
paliers      = (tour - 1) // tous_les
```

Avec une augmentation tous les tours (`tous_les` = 1), `paliers` = `tour - 1` : c'est la formule
donnée par l'utilisateur, `(valeur_base + augmentation × (nb_tour - 1)) × coeff_difficulte`. Prise
en compte du rythme « tous les N tours » par `paliers` **validée** (décision utilisateur).
Exemple : dégâts 6, +1 tous les 2 tours, coefficient 1,5 → 9, 9, 10, 10, 12 aux tours 1 à 5.

### 3.4 Un coefficient de difficulté

À la **création** d'un ennemi, on peut donner un **coefficient multiplicateur**, appliqué à **toutes
ses valeurs**, **arrondi à l'inférieur**. Exemple : coefficient 1,5 → dégâts 6 → 9, bouclier
5 → 7. Sert à moduler la difficulté (selon le niveau, versions « élite »…).

- **Le coefficient s'applique aussi aux PV et aux augmentations** (décision utilisateur) : la
  formule du §3.3 multiplie la somme base + augmentations ; PV = arrondi_inferieur(PV × coefficient).
- **Le coefficient vaut au moins 1** (décision utilisateur, **vérifié à la création** de
  l'ennemi) : il ne sert qu'à durcir un ennemi, et une valeur ne peut jamais tomber sous sa base.
- Les **rythmes** (« tous les 2 tours ») et les **durées** ne sont pas des valeurs et ne sont
  jamais multipliés.

### 3.5 Format envisagé (`config/ennemi_new.json`)

```json
{
  "id": "ENM_PAT_LE_PIRATE",
  "nom": "Pat le Pirate",
  "pv": 50,
  "valeurs": {
    "degats": { "base": 5, "augmentation": 1, "tous_les": 2 }
  },
  "actions": [
    [ { "nature": "ATTAQUE", "valeur": "degats", "cible": "PROXIMITE" } ]
  ]
}
```

Le nettoyeur, avec ses attaques multiples : `{ "nature": "ATTAQUE", "valeur": "degats", "cible":
"PROXIMITE", "repetitions": 2 }`.

`actions` est le cycle : chaque élément est une étape (une liste d'effets). Même démarche que les
cartes et les modules : `config/ennemi_new.json` source de vérité, une classe dédiée (ex.
`EnnemiNew`, avec une copie par combat), un tableau `.md` généré.

---

## 4. Ennemis à redessiner

### 4.1 Miroir (décision utilisateur)

Ce n'est **plus un bouclier** : Miroir pose un **effet de renvoi** qui **ne se cumule plus** (le
reposer le rafraîchit) et **dure un tour**. Corrige le blocage constaté en simulation.

- **Ce qui est renvoyé (décision utilisateur)** : les dégâts reçus par l'ennemi protégé sont
  renvoyés **jusqu'à une valeur** (valeur nommée de Miroir, avec augmentation et coefficient) ;
  **l'ennemi protégé encaisse le reste**.

### 4.2 Petit Jean et le Boss (sans « bouclier par tour »)

Avec le cycle d'actions, un **bouclier simple** devient une étape du cycle (ex. Petit Jean :
attaque, attaque, bouclier). Le +2 dégâts du Boss devient une augmentation de sa valeur de dégâts
(§3.3). Reste à fixer les cycles et les valeurs.

---

## 5. Questions ouvertes

1. **Ordre de fin de tour** : confirmer la proposition du §2 (incendie absorbé par le bouclier,
   puis bouclier −1).
2. **Ciblage** : avec des secondaires à 20 PV et la pile Hors service, les attaques « au plus
   proche » détruisent vite les modules avant et protègent le principal ; plus d'attaques de zone,
   ou un ciblage du principal (refonte-modules.md §7) ?
3. **Flottes** : utiliser le coefficient (§3.4) et les tailles S/M/L pour une difficulté par niveau ;
   plusieurs boss.
4. **Nouveaux ennemis** : plus tard (décision utilisateur, 2026-11-08) ; par exemple un ennemi qui
   pose de l'incendie ou un debuff sur le joueur.

---

## 6. Prochaines étapes

1. Trancher les questions du §5.
2. Redessiner les 6 ennemis dans ce format (cycles, valeurs, augmentations).
3. Créer `config/ennemi_new.json`, la classe dédiée et son tableau généré.
4. Puis le combat de la refonte (`combat_new`), validé par le simulateur.
