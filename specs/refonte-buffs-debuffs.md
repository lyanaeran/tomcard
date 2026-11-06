# Refonte des buffs/debuffs/bouclier — brouillon de conception

*Document de travail, pas encore une section numérotée du document de conception (cf.
[specs.md](specs.md)) : rien ci-dessous n'est décidé ni implémenté. Une fois le modèle tranché, le
contenu stabilisé ira dans [combat.md](combat.md) (§3.5, §13 point 2) et
[modules-cartes.md](modules-cartes.md) (§12.3/§12.4/§12.5), et ce fichier sera supprimé. Pointeur
depuis [a-trancher.md](a-trancher.md) §11 ("Stacks à intensité cumulative").*

---

## 1. Pourquoi cette refonte

Point de départ (discussion utilisateur) : deux buffs de dégâts de 3 tours posés l'un après l'autre
ne se combinent pas de façon satisfaisante avec le modèle actuel. Objectif : un modèle unique pour
bouclier, buffs et debuffs, où poser le même effet deux fois **additionne sa magnitude** plutôt que
de faire coexister deux instances à décompte indépendant.

## 2. Synthèse de l'existant

Trois mécanismes **distincts** aujourd'hui, à ne pas confondre en abordant la refonte :

### 2.1 Bouclier « brut » (`module.bouclier` / `ennemi.bouclier`)

Un simple entier sur l'entité, **pas** un `BuffActif`. Une carte Defense sans `action` (*Bouclier,
Protéger le vaisseau, Mode défensif, Protéger l'avant poste...*) appelle directement
`ajouter_bouclier(valeur)` : additif par construction, ça « stacke » déjà.

Ce qui s'use, c'est sa **dissipation naturelle** (`combat.py:_dissiper_bouclier`, specs.md §3.5) :
à chaque tour (tour joueur pour un module, tour ennemi pour un ennemi), si le bouclier actuel est
**≤ `SEUIL_DISSIPATION_BOUCLIER` (5)** il tombe à 0, sinon il est **divisé par deux** (arrondi
au-dessus). C'est cette règle que le point 1 de la demande veut remplacer par un **-1/tour** fixe.

### 2.2 Buffs/debuffs à %, via `BuffActif` (`carte.py`)

`BuffActif(action, valeur, tours_restants, cible_reflet)` — une liste par entité
(`Module.buffs_actifs` / `Ennemi.buffs_actifs`), **aucune fusion** : chaque pose ajoute une
nouvelle instance indépendante, avec sa propre durée. L'effet constaté est la **somme réactive**
de toutes les instances actives au moment du calcul (`Ennemi._somme_buffs`, appelée par
`degats_subis`/`degats_attaque_effectifs`) : *numériquement* additif dès aujourd'hui côté ennemi
(deux Brèche à 100% donnent bien +200% au moment présent). Ce qui gêne, c'est que chaque instance
**expire à son propre rythme** (escalier de décroissance) plutôt qu'un seul compteur lisible — et
que ce mécanisme n'existe **pas du tout côté module allié** : `Module._declencher_buff` ne réagit
qu'à `BOUCLIER_PAR_TOUR`, un buff de dégâts posé sur son propre module ne ferait rien.

`ActionCarte` concernés : `VULNERABILITE` (%, dégâts subis), `REDUCTION_DEGATS`/
`AUGMENTATION_DEGATS` (points, dégâts infligés par un ennemi), `BOUCLIER_POURCENTAGE_PV` (% des PV
max, converti en bouclier **une fois** à la pose, puis redevient un bouclier brut classique — cf.
2.1), `REDIRECTION_CIBLE`, `ANNULATION_PROCHAINE_ATTAQUE` (flags sans magnitude, cf. §5.3).

### 2.3 Buffs récurrents (`BOUCLIER_PAR_TOUR`)

Un buff qui **repose du bouclier frais à chaque tour** tant qu'il reste actif
(`Module.declencher_buffs_tour`/`Ennemi` via la `frequence` de son Action), en plus de son premier
déclenchement à la pose. Peut être à durée limitée (*Blindage maximal*, *Blindage cible* : `duree`
finie) ou persistant (*Bouclier perpétuel* : `tours_restants=None`, ne décompte jamais). C'est un
troisième mécanisme, orthogonal aux deux précédents — important pour la §4.1 ci-dessous.

---

## 3. Modèle proposé

**Règle commune** : un seul compteur cumulatif par (entité, effet) plutôt qu'une liste
d'instances. Poser une carte **ajoute** sa valeur au compteur existant. Au début du tour concerné
(même cadence qu'aujourd'hui : tour joueur pour un module, tour ennemi pour un ennemi), le
compteur **décroît** d'un montant fixe ; à 0 (ou à l'équivalent neutre), l'effet disparaît.

Le montant de décroissance dépend de l'**unité** de la valeur — c'est le point qui doit rester
différent selon l'effet, le reste du mécanisme est unique :

| Nature de la valeur | Décroissance proposée | Cartes concernées |
|---|---|---|
| Points (bouclier brut, réduction/augmentation de dégâts) | **-1 / tour** | Bouclier, Tordre le canon... |
| Pourcentage (vulnérabilité) | **-10 %/tour** (ou -5 %, à trancher) | Brèche, Ligne avant, Boucliers endommagés, Boucliers hors service |
| Multiplicateur (x2/x3 en dégâts) | **à voir** (cf. §3.3) | Aucune carte actuelle — piste future |

### 3.1 Exemple chiffré — Bouclier (reprend l'exemple utilisateur)

| Moment | Bouclier |
|---|---|
| Ennemi attaque de 3 (bouclier à 7) | 4 |
| Début tour joueur (décroissance -1) | 3 |
| Joueur pose Bouclier (+7) | 10 |

### 3.2 Exemple chiffré — Vulnérabilité à -10 %/tour

| Moment | Compteur |
|---|---|
| Tour 1, joueur joue Brèche (+100%) | 100% |
| Début tour ennemi 1 (décroissance -10%) | 90% |
| Tour 2, joueur rejoue Brèche (+100%) | 190% |
| Début tour ennemi 2 | 180% |
| ... | décroît de 10 points par tour jusqu'à 0 |

### 3.3 Points non tranchés

- **x2/x3 en dégâts** : proposition — décroît par **cran entier** (-1 par tour : x3 → x2 → x1 →
  disparu), symétrique du modèle « points ». Aucune carte actuelle n'en a besoin, piste pour une
  future carte Légendaire.
- **Un seul taux de décroissance global pour tous les % (-10 %/tour), ou un taux par carte ?**
  Un taux global est plus simple et plus lisible pour le joueur (« tout % perd 10 points par
  tour », point commun à toutes les cartes de ce type) mais fait perdre la différenciation
  actuelle par **durée** : aujourd'hui *Brèche*/*Ligne avant* durent 2 tours et *Boucliers hors
  service* 5 tours, pour la même magnitude (100%) — à rebalancer sur la **magnitude** posée plutôt
  que sur la durée si le taux devient global (cf. tableau §5, avertissements).
- **Les buffs récurrents (`BOUCLIER_PAR_TOUR`, §2.3) restent-ils un mécanisme à part, ou
  fusionnent-ils avec ce modèle ?** Voir §4.1 : les fusionner naïvement casse l'équilibrage
  (croissance sans limite).
- **Bouclier miroir** (*Renvoi*) : aujourd'hui ne dissipe jamais, seulement consommé par un
  dégât renvoyé (specs.md §13.2). Doit-il désormais décroître de -1/tour comme un bouclier
  classique, en plus d'être consommé par les dégâts ?

---

## 4. Boucliers à seuil et à plafond (nouvelle idée)

Deux nouveaux archétypes de bouclier évoqués, tous deux caractérisés par une valeur **X/Y** qui
module l'effet plutôt que d'absorber des points comme le bouclier classique :

- **Bouclier à seuil** : annule **entièrement** tout dégât strictement inférieur à X (laisse
  passer tel quel tout dégât ≥ X). Protège contre le harcèlement de petits coups répétés, inutile
  contre un gros coup.
- **Bouclier à plafond** : plafonne chaque dégât reçu à **Y au maximum** (`dégâts_subis =
  min(dégâts, Y)`). Protège contre les gros coups ponctuels, inutile contre du grignotage sous Y.

### 4.1 Pourquoi le seuil (X) fonctionne nativement, et pas le plafond (Y)

**Seuil** : X qui **décroît** de 1/tour affaiblit naturellement l'effet (de moins en moins de
coups sont assez petits pour passer sous X) — cohérent avec le modèle unifié de la §3, aucun
problème.

**Plafond** : plus Y est **grand**, moins le plafond protège (plus de dégâts passent). Pour que
l'effet s'affaiblisse avec le temps, c'est donc Y qui doit **augmenter** — sens inverse de tout le
reste du modèle (qui décroît toujours vers 0/neutre). Trois façons de résoudre ça :

1. **Stocker l'inverse de Y, pas Y lui-même (recommandé)** — ne pas stocker le plafond directement :
   stocker une « protection » `P` qui décroît de 1/tour **exactement comme tout le reste du
   modèle**, et calculer le plafond effectif à l'usage : `Y_effectif = Y_PLANCHER + P` (`Y_PLANCHER`
   = plafond le plus bas/protecteur possible, une constante de la carte). `P` à 0 → `Y_effectif =
   Y_PLANCHER`, le plafond le plus fort n'a alors plus de marge au-delà. Aucune exception dans le
   moteur : tout le code de décroissance reste « une valeur qui tend vers 0 », seule la **formule
   d'application** du plafond change (elle lit `Y_PLANCHER + P` au lieu de `P` directement).
2. **Stocker Y directement et le faire croître** — ajoute une direction de décroissance différente
   selon l'effet (un `sens: +1 | -1` sur chaque `ActionCarte`) : fonctionne, mais introduit une
   vraie asymétrie dans le moteur que l'option 1 évite complètement pour un coût de formule
   négligeable à l'usage (une addition au lieu d'une lecture directe).
3. **Changer la sémantique de la carte** — remplacer « plafonne à Y » par « réduit chaque coup de
   Z points » (`dégâts_subis = max(0, dégâts - Z)`) : mathématiquement différent (un plafond laisse
   passer le dégât en dessous de Y inchangé ; une réduction retranche Z même aux petits dégâts),
   mais Z décroît nativement comme tout le reste (c'est la même mécanique que `REDUCTION_DEGATS`,
   déjà implémentée côté ennemi, §2.2). À envisager si la nuance plafond/réduction n'est pas
   essentielle au ressenti recherché.

**Recommandation** : option 1 — elle garde le moteur à une seule règle de décroissance (toujours
vers 0), au prix d'une formule légèrement indirecte pour ce seul effet.

---

## 5. Tableau des cartes Bouclier / Buff / Debuff

Fonctionnement actuel → nouveau fonctionnement sous le modèle de la §3. **⚠️** = ne fonctionne pas
tel quel sous le nouveau modèle sans décision/ajustement supplémentaire.

| Carte (module) | Fonctionnement actuel | Nouveau fonctionnement | Avertissement |
|---|---|---|---|
| Bouclier, Protéger le vaisseau, Mode défensif, Protéger l'avant poste (Principal/Blindage) | Bouclier brut, dissipe par moitié/tour (seuil 5) | Bouclier brut, dissipe de -1/tour | Aucun — déjà additif, seule la dissipation change |
| Bouclier adaptatif (Blindage) | Bouclier = X% des PV **max**, calculé une fois à la pose puis bouclier brut classique | Identique : le % ne sert qu'au calcul initial, le résultat suit ensuite la règle bouclier brut (-1/tour) | Aucun |
| **Blindage maximal, Blindage cible, Bouclier perpétuel** (Principal/Blindage) — `BOUCLIER_PAR_TOUR` | Repose du bouclier chaque tour ; dissipation par moitié crée un point d'équilibre (ex. valeur 10 → stabilise à 20, specs.md §3.5) | — | **⚠️ Casse l'équilibrage tel quel** : avec une dissipation à -1/tour fixe, reposer une valeur V > 1 chaque tour fait **croître le bouclier sans limite** (+V-1 net par tour, jamais de point d'équilibre). Décision à prendre en §3.3 avant d'y toucher — ces 3 cartes doivent peut-être garder l'ancienne dissipation par moitié, ou plafonner le bouclier brut, ou autre chose |
| Tordre le canon (Sabotage) | `REDUCTION_DEGATS` 5 points, 1 tour, instance indépendante | Compteur cumulatif, -1 point/tour | Mineur : 5 points à -1/tour prennent 5 tours à s'éteindre au lieu de 1 — magnitude à revoir si on veut garder le même ressenti (carte courte et forte) |
| **Brèche, Ligne avant, Boucliers endommagés, Boucliers hors service** (Sabotage) | `VULNERABILITE` 100%, instances indépendantes à 2/2/2/5 tours | Compteur cumulatif, -10%/tour (ou le taux choisi) | **⚠️ Perd la différenciation par durée** : les 4 cartes partagent aujourd'hui la même magnitude (100%) et ne se distinguent que par leur durée (2 ou 5 tours) — avec un taux de décroissance global, elles deviennent identiques. Il faudra les différencier par **magnitude** (ex. Boucliers hors service à 150% plutôt que 100%) plutôt que par durée |
| Renvoi (Blindage) — `BOUCLIER_MIROIR` | Ne dissipe jamais, consommé uniquement par un dégât renvoyé | — | Point ouvert (§3.3) : doit-il décroître de -1/tour en plus, ou rester une exception comme aujourd'hui ? À trancher, pas de proposition par défaut |
| Leurre (Lanceur de missiles) — `ANNULATION_PROCHAINE_ATTAQUE` | Flag booléen, pas de magnitude, consommé au 1er coup reçu | Inchangé | **⚠️ Hors périmètre** : aucune valeur à faire décroître, ne rentre pas dans le modèle de la §3 |
| Tir allié (Sabotage) — `REDIRECTION_CIBLE` | Valeur 0, 1 tour, flag sans magnitude | Inchangé (durée fixe classique) | **⚠️ Hors périmètre**, même raison que Leurre |
| Bouclier stabilisé (Principal, *non jouable*) | — | Bloque la décroissance (-1/tour ou -10%/tour) de tout effet sur ce module pendant sa durée | Mécanique encore à construire, mais désormais plus simple à exprimer : « ignorer la décroissance de ce tour » plutôt que « ignorer la division par deux » — directement compatible avec le modèle unifié |
| Optimisation des boucliers, Attaques performantes, Double défense, Circuit parallèle, Salve laser, Protocole d'urgence (*non jouables*) | — | Sans rapport avec la refonte (méta-effets : coût/duplication de cartes) | Hors périmètre de ce document |

*Cartes connexes non listées ci-dessus* : *Embrasement, Guerre nucléaire, Tir incendiaire* (dégâts
répétés sur Y tours, `TypeCarte.ATTAQUE`, non jouables) partagent la même famille de problème
(« une valeur qui doit décroître dans le temps ») — le modèle de la §3 (et l'idée « Stacks à
intensité façon Poison », déjà notée en [a-trancher.md](a-trancher.md) §11) les débloquerait
probablement du même coup : un stack de dégâts qui s'inflige chaque tour puis décroît de -1, au
lieu d'un `duree` fixe à suivre séparément.

---

## 6. Autres mécaniques du même genre (pistes)

| Idée | Effet | Décroissance proposée | Remarque |
|---|---|---|---|
| **Armure** (généraliser `REDUCTION_DEGATS` aux dégâts subis par un module) | Réduit de Z points chaque coup reçu par ce module (pas seulement les dégâts infligés par un ennemi, cf. §2.2) | -1 point/tour | Réutilise un `ActionCarte` déjà implémenté, juste appliqué côté module plutôt que côté ennemi |
| **Régénération** | Répare X PV à chaque tour, tant que le buff est actif (symétrique de `BOUCLIER_PAR_TOUR` mais pour les PV) | -1 point/tour sur X (le montant réparé par tour diminue) | Nouveau `ActionCarte`, logique proche de `BOUCLIER_PAR_TOUR` existant |
| **Esquive à charges** | X% de chance d'éviter *totalement* la prochaine attaque (pile ou face, pas une réduction) | -10%/tour (même famille que Vulnérabilité) | Nécessite un tirage aléatoire à la résolution (cf. `Combat.aleatoire`, déterminisme injecté) |
| **Contre-attaque** | Le module subit le coup normalement, **et** inflige X dégâts en retour à l'attaquant | -1 point/tour | Différent du Bouclier miroir existant (qui absorbe au lieu de subir) — un vrai nouveau mécanisme |
| **Bouclier absorbant qui soigne l'excédent** | Si le bouclier n'est pas entamé à la fin de son tour, l'excédent se convertit en PV soignés (façon « absorb shield » de certains MMO) | Suit la dissipation classique du bouclier (§3.1) | Plus complexe (lecture de l'état en fin de tour), piste pour plus tard plutôt que prioritaire |

---

## 7. Prochaines étapes

1. Trancher les points ouverts de la §3.3 (taux de décroissance %, sort des buffs récurrents,
   bouclier miroir).
2. Choisir une résolution pour le bouclier à plafond (§4.1 — recommandation : option 1).
3. Rebalancer la magnitude des 4 cartes Vulnérabilité (§5) si le taux de décroissance devient
   global.
4. Une fois stabilisé : migrer ce contenu dans `combat.md` (§3.5, §13) et `modules-cartes.md`
   (§12.3-§12.5), supprimer ce fichier, mettre à jour la table d'index de `specs.md` si une
   nouvelle section est nécessaire.
