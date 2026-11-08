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
2.1), `REDIRECTION_CIBLE`, `ANNULATION_PROCHAINE_ATTAQUE` (flags sans magnitude, cf. tableau §5).

### 2.3 Buffs récurrents (`BOUCLIER_PAR_TOUR`) — **retiré par décision utilisateur**

Un buff qui **repose du bouclier frais à chaque tour** tant qu'il reste actif
(`Module.declencher_buffs_tour`/`Ennemi` via la `frequence` de son Action), en plus de son premier
déclenchement à la pose. Peut être à durée limitée (*Blindage maximal*, *Blindage cible* : `duree`
finie) ou persistant (*Bouclier perpétuel* : `tours_restants=None`, ne décompte jamais).

**Décision (discussion utilisateur) : ce mécanisme et les 3 cartes qui l'utilisent sont retirés**,
plutôt que réconciliés avec le modèle de la §3 — la croissance sans limite qu'il produirait sous
une décroissance -1/tour fixe (cf. §5) n'est pas rattrapable proprement. Un simple bouclier posé
plusieurs fois (§2.1) couvre déjà le même besoin sous le nouveau modèle : poser deux fois une carte
Bouclier classique additionne sa valeur, exactement ce que *BOUCLIER_PAR_TOUR* cherchait à obtenir
automatiquement. `ActionCarte.BOUCLIER_PAR_TOUR` est donc à supprimer du moteur une fois la refonte
implémentée, et *Blindage maximal*, *Blindage cible*, *Bouclier perpétuel* à retirer ou redessiner
en cartes Bouclier classiques (§8, étape 7).

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
- ~~Les buffs récurrents (`BOUCLIER_PAR_TOUR`, §2.3) restent-ils un mécanisme à part, ou
  fusionnent-ils avec ce modèle ?~~ **Tranché : retirés** (§2.3) — un bouclier classique reposé
  plusieurs fois couvre déjà le même besoin sous le modèle unifié.
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

### 4.1 Oui, ça se ramène au cas général

**Seuil** : X qui **décroît** de 1/tour affaiblit naturellement l'effet (de moins en moins de
coups sont assez petits pour passer sous X) — cohérent avec le modèle unifié de la §3, aucun
problème, X **est** directement le compteur décroissant.

**Plafond** : Max n'a pas besoin d'être stocké directement, ni de croître. On garde **exactement**
le même compteur décroissant que le reste du modèle — ici, le compteur de durée `tours_restants`,
déjà utilisé par toute carte à durée aujourd'hui — et Max se **lit** à partir de lui par une
formule, au lieu d'être lu directement comme pour le bouclier ou la vulnérabilité :

```
Max_courant = Max_initial + pas × (duree_totale - tours_restants)
```

`tours_restants` décroît de 1/tour comme toujours, jusqu'à 0 (buff supprimé, plus de plafond du
tout). `duree_totale` et `pas` sont deux constantes de la carte (sa durée à la pose, et de combien
Max augmente par tour écoulé). `(duree_totale - tours_restants)` est simplement « le nombre de
tours déjà écoulés depuis la pose » : c'est **cette** quantité qui croît avec le temps, pas le
compteur stocké lui-même, qui continue de décroître vers 0 exactement comme toutes les autres
cartes à durée — rien de neuf dans le moteur, seule la formule de lecture de Max change.

### 4.2 Exemple chiffré (reprend l'exemple de la discussion)

Carte fictive « Bouclier capacitif » : `Max_initial = 10`, `pas = 5`, `duree_totale = 3` tours.
`Max_courant = 10 + 5 × (3 - tours_restants)`.

| Tour | `tours_restants` | Max_courant | Un coup de 30 dégâts... |
|---|---|---|---|
| 1 (pose) | 3 | 10 + 5×(3-3) = **10** | ...réduit à 10 (grosse protection) |
| 2 (décroissance -1) | 2 | 10 + 5×(3-2) = **15** | ...réduit à 15 |
| 3 (décroissance -1) | 1 | 10 + 5×(3-1) = **20** | ...réduit à 20 (protection faible) |
| 4 (décroissance -1) | 0 → buff **supprimé** | — | ...passe en entier (30), effet disparu |

`tours_restants` est le seul état stocké, et il décroît de 1/tour comme n'importe quelle carte à
durée — exactement le cas général de la §3, avec une formule de lecture différente de celle du
bouclier/de la vulnérabilité (qui lisent leur compteur directement plutôt qu'au travers d'une
transformation).

### 4.3 Repose pendant que l'effet est actif

Sous cette formulation, reposer la carte **réinitialise `tours_restants` à `duree_totale`** (3)
plutôt que de l'additionner — contrairement à la magnitude des autres effets (§3), qui s'additionne
à la repose. Additionner les `tours_restants` ferait dépasser `duree_totale`, donc retomber Max
**en dessous** de `Max_initial` (sur-protection non prévue par la carte) : rafraîchir est donc la
seule option cohérente ici, pas un choix arbitraire parmi d'autres.

---

## 5. Tableau des cartes Bouclier / Buff / Debuff

Fonctionnement actuel → nouveau fonctionnement sous le modèle de la §3. **⚠️** = ne fonctionne pas
tel quel sous le nouveau modèle sans décision/ajustement supplémentaire.

| Carte (module) | Fonctionnement actuel | Nouveau fonctionnement | Avertissement |
|---|---|---|---|
| Bouclier, Protéger le vaisseau, Mode défensif, Protéger l'avant poste (Principal/Blindage) | Bouclier brut, dissipe par moitié/tour (seuil 5) | Bouclier brut, dissipe de -1/tour | Aucun — déjà additif, seule la dissipation change |
| Bouclier adaptatif (Blindage) | Bouclier = X% des PV **max**, calculé une fois à la pose puis bouclier brut classique | Identique : le % ne sert qu'au calcul initial, le résultat suit ensuite la règle bouclier brut (-1/tour) | Aucun |
| **Blindage maximal, Blindage cible, Bouclier perpétuel** (Principal/Blindage) — `BOUCLIER_PAR_TOUR` | Repose du bouclier chaque tour ; dissipation par moitié crée un point d'équilibre (ex. valeur 10 → stabilise à 20, specs.md §3.5) | **Retirées** (décision, cf. §2.3) | Carte à redessiner en Bouclier classique ou à retirer purement — sous une dissipation -1/tour fixe, reposer une valeur V chaque tour ferait croître le bouclier sans limite (+V-1 net par tour), non rattrapable proprement |
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

## 7. Analyse du modèle et contre-proposition (discussion du 2026-11-06)

### 7.1 Limite du « -1/tour pour tout » : le bouclier s'accumule

Le retrait de `BOUCLIER_PAR_TOUR` (§2.3) est motivé par une croissance sans limite sous une
décroissance -1/tour. Mais **le même problème touche les cartes Bouclier classiques** : dès que le
bouclier posé par tour dépasse (dégâts reçus + 1), il grossit à chaque tour. Avec le deck de
départ (3 électricité/tour, 5 cartes piochées, 4 *Bouclier* à 5 pour 1), deux cartes Bouclier par
tour donnent +10 - 1 = **+9 net/tour**, face à des ennemis qui frappent de 2 à 5 (Petit Jean, Pat
le Pirate, Le puzzle) : le module visé devient invulnérable en 2 ou 3 tours. C'est pour cette
raison que Slay the Spire remet le Block à zéro chaque tour ; la division par deux actuelle (§3.5)
jouait le même rôle de frein.

**Baisser la valeur des cartes ne suffit pas pour le bouclier** (proposition examinée : Bouclier 3
au lieu de 5) : un bouclier absorbe au plus sa valeur, une seule fois, la décroissance ne fait que
le grignoter — il ne « rapporte » pas 3+2+1 = 6. Baisser la valeur recule le seuil d'accumulation
sans le supprimer, et affaiblit le premier tour du combat.

À l'inverse, **pour les effets qui agissent à chaque tour** (réduction de dégâts, vulnérabilité,
dégâts répétés), ajuster la valeur de départ est bien le bon levier : une valeur V à -1/tour agit
V + (V-1) + ... + 1 = V(V+1)/2 au total (1, 3, 6, 10, 15... — granularité grossière). Conséquences
à intégrer au rééquilibrage :

- *Tordre le canon* (5 points) : 5+4+3+2+1 = **-15 dégâts au total, contre -5 aujourd'hui (x3)** —
  pas un écart « mineur » comme indiqué en §5.
- *Brèche* à -10 %/tour : 100+90+...+10 = **550 % cumulés, contre 200 % aujourd'hui (x2,75)**.
- Poser deux fois le même effet rapporte plus que le double (2 x 3 → 4+3+2+1 = 10) : bonus au
  cumul, peut-être voulu.

### 7.2 Montée des dégâts ennemis : caractéristique propre à chaque ennemi

Proposition utilisateur : les ennemis démarrent avec des dégâts faibles (ex. 3), qui **montent de
+1 ou +2 par tour**, la valeur de montée étant **une caractéristique de chaque ennemi** (un
ennemi agressif à +2, un ennemi costaud à +1, 0 pour un ennemi déjà dangereux). Règle les deux
problèmes à la fois : un premier tour jouable avec peu de bouclier, et une accumulation de
bouclier bornée dans le temps — le bouclier sert à **gagner des tours**, le combat devient une
course qui pousse à attaquer.

Simulation (un module attaqué, dégâts de départ 3, bouclier -1/tour ; chaque case = dégâts reçus →
bouclier restant / PV perdus cumulés, sur 8 tours) :

| Bouclier posé/tour | Montée | Résultat |
|---|---|---|
| 8 (2 cartes) | +0 | 3→5 · 3→9 · 3→13 · ... · 3→33 : **bouclier infini** |
| 8 | **+1** | 3→5 · 4→8 · 5→10 · 6→11 · 7→11 · 8→10 · 9→8 · 10→5 : plafonne puis cède vers le tour 9 |
| 8 | **+2** | 3→5 · 5→7 · 7→7 · 9→5 · 11→1 · 13→0/5 · 15→0/12 · 17→0/21 : tient 5 tours |
| 4 (1 carte) | +1 | 3→1 · 4→0 · 5→0/1 · 6→0/3 · ... · 10→0/21 : insuffisant dès le tour 3 |

**Forme proposée : un champ dédié dans `config/ennemis.json`** (ex. `"montee_degats": 1`), ajouté
par le moteur aux dégâts de l'ennemi à chaque tour ennemi, plutôt qu'une Action `POSE_BUFF`
`AUGMENTATION_DEGATS` répétée chaque tour (possible sans code moteur, mais encombre l'intention
affichée d'une ligne « Va poser +1 dégâts » à chaque tour et empile une instance par tour).
Affichage dans l'infobulle comme une caractéristique (ex. « Rage +3 »). `AUGMENTATION_DEGATS` reste
disponible pour des effets ponctuels (Boss des pirates).

Points d'équilibrage à surveiller :

- **Plusieurs ennemis** : 3 ennemis à +2 = +6 dégâts/tour au total — d'où une valeur par ennemi
  plutôt qu'une règle globale.
- **Attaques multiples** (*Le nettoyeur*, 7 x 2) : décider si la montée s'applique à chaque coup.
- **Ennemis à beaucoup de PV** (Boss 150, Petit Jean 100) : les combats durent 10 tours ou plus
  avec les dégâts actuels du joueur ; +2/tour les rendrait impossibles → +1, ou un plafond.
- **Bouclier des ennemis** : soumis à la même décroissance -1/tour, à équilibrer en même temps.

### 7.3 Contre-proposition : deux familles d'effets plutôt qu'une

Un seul mécanisme de compteur dans le moteur, mais chaque effet déclare ce que son compteur
représente :

1. **Cumul en durée, intensité fixe** (le Vulnérable de Slay the Spire) : « Vulnérabilité 3 » =
   +X % pendant 3 tours ; reposer l'effet **ajoute des tours**, le compteur perd 1 par tour. Règle
   le cas de départ (deux buffs de 3 tours = 6 tours lisibles) et **conserve la différenciation
   par durée** (*Brèche* 2 tours vs *Boucliers hors service* 5 tours) — l'avertissement ⚠️ de la §5
   disparaît. *Tordre le canon*, *Tir allié* y entrent naturellement.
2. **Cumul en intensité** : qui décroît (Poison : *Embrasement*, *Guerre nucléaire*, *Tir
   incendiaire*), ou **sans décroissance** (Force : `AUGMENTATION_DEGATS` du Boss, montée de dégâts
   §7.2). Décision utilisateur : les mécaniques des ennemis seront gérées **en dehors des cartes**
   (pas dans `CarteNew`) ; côté cartes, le cumul sans décroissance sert aux effets « lancées N fois
   de plus » (*Salve laser*…, modules-cartes.md §4).

Le **bouclier** garde une décroissance **proportionnelle** (moitié comme aujourd'hui, ou un quart
avec un minimum de 1) ou un plafond, si la montée des dégâts ennemis (§7.2) ne suffit pas à
contenir l'accumulation — à vérifier une fois la montée implémentée.

### 7.4 Oublis du brouillon

- **Les ennemis utilisent `BOUCLIER_PAR_TOUR`** : Petit Jean (3 tous les 2 tours, durée 2) et le
  Boss des pirates (5 tous les 3 tours). Le §2.3 ne retire que les 3 cartes joueur : supprimer
  l'action du moteur casserait ces deux ennemis, à redessiner aussi.
- **`AUGMENTATION_DEGATS` du Boss** (persistante, cumulative : +2, +4, +6...) est absente du tableau
  §5 : sous -1/tour, elle s'effacerait d'elle-même et changerait le Boss. Relève de la famille
  « intensité permanente » (§7.3).
- **Bouclier miroir** (§3.3, point ouvert) : proposition de le faire décroître comme un bouclier,
  par cohérence, plutôt qu'une réserve de renvoi éternelle.
- **Régénération** (§6) : même risque de croissance sans limite que `BOUCLIER_PAR_TOUR` si elle se
  cumule en intensité → famille « durée ».
- **Bouclier à plafond** (§4) : trois champs (`Max_initial`, `pas`, `duree_totale`) pour des cartes
  qui n'ont aujourd'hui que X et Y ; proposition : X = plafond initial, Y = durée, pas global ou
  dérivé de X.

---

## 8. Prochaines étapes

1. Trancher le modèle : « -1/tour pour tout » (§3) ou deux familles (§7.3). **Bouclier tranché
   (décision utilisateur, 2026-11-07)** : il baisse de 1 par tour et c'est tout, sans notion de
   durée ; l'accumulation (§7.1) est contenue par la montée des dégâts propre à chaque ennemi
   (§7.2). Conséquence : *Blindage ciblé* devient un bouclier simple de 6 (plus de « pendant Y
   tours »), et `CarteNew` refuse une durée sur un bouclier.
2. Fixer la montée de dégâts de chaque ennemi (§7.2) et ajouter le champ à `config/ennemis.json`.
3. Redessiner Petit Jean et le Boss des pirates (§7.4) si `BOUCLIER_PAR_TOUR` est retiré.
4. Trancher les points ouverts restants de la §3.3 (taux de décroissance %, bouclier miroir).
5. Confirmer `Max_initial`/`pas`/`duree_totale` comme champs de carte pour le bouclier à plafond
   (§4, cf. §7.4) — mécanique prête à spécifier une fois une première carte de ce type conçue.
6. Rebalancer la magnitude des 4 cartes Vulnérabilité (§5) si le taux de décroissance devient
   global (inutile avec le modèle à deux familles, §7.3).
7. Redessiner ou retirer *Blindage maximal*, *Blindage cible*, *Bouclier perpétuel* (§2.3, §5) —
   `BOUCLIER_PAR_TOUR` est abandonné.
8. Renommer les buffs « persistants » (sans durée, `tours_restants = None`) en **« permanents »**
   dans le code et les specs : « Persistante » devient un mot-clé de carte (décision prise dans
   [refonte-modules.md](refonte-modules.md) §3.5).
9. Une fois stabilisé : migrer ce contenu dans `combat.md` (§3.5, §13) et `modules-cartes.md`
   (§12.3-§12.5), supprimer ce fichier, mettre à jour la table d'index de `specs.md` si une
   nouvelle section est nécessaire.
