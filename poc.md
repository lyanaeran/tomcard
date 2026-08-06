# Space Fight — POC (preuve de concept)

*Spécification minimale pour un premier combat jouable — dérivée de `specs.md`*

---

## 1. Objectif

Un seul combat 1 contre 1 (module de base du joueur contre un ennemi unique), avec 3 cartes, pour valider la boucle de combat de base : jouer des cartes, dépenser de l'électricité, infliger des dégâts, encaisser une attaque ennemie.

Simplifications par rapport à `specs.md` : pas de grille de rangs (2x3), pas d'autres modules équipables, pas de boucle de run (pas d'étapes, pas de boss, pas de récompense de cartes). Un seul combat, une seule fois.

---

## 2. Vaisseau du joueur

- **Module de base** : 15 PV
- Pas d'autre module équipé pour ce POC
- **Électricité** : 3 par tour (ressource pleine à chaque début de tour, ne se cumule pas d'un tour à l'autre)
- **Main** : 5 cartes piochées à chaque tour
- Cartes jouées partent en défausse ; quand la pioche est vide, la défausse est mélangée pour reformer la pioche (comme Slay the Spire, cf. specs.md §3.3)

---

## 3. Ennemi

- **Un seul ennemi**, 15 PV
- **Attaque à chaque tour ennemi** : inflige **7 dégâts** au module de base (attaque fixe, pas de pattern ni de variation pour ce POC)

---

## 4. Cartes

| Carte | Type | Cible | Coût | Effet |
|---|---|---|---|---|
| **Attaque** | Attaque | Ennemi (unique) | 1⚡ | Inflige **7 dégâts** |
| **Bouclier** | Défense | Soi (unique) | 1⚡ | Donne **5 Bouclier** au module de base |
| **Soin** | Soin | Soi (unique) | 1⚡ | Répare **4 PV** au module de base |

Le Bouclier absorbe les dégâts subis avant les PV (règle standard façon StS, à confirmer si un comportement différent est voulu).

---

## 5. Composition du deck

9 cartes au total :
- **5x Attaque**
- **3x Bouclier**
- **1x Soin**

---

## 6. Déroulé d'un tour

1. **Tour du joueur** : la main se remplit à 5 cartes, l'électricité est remise à 3. Le joueur joue librement les cartes de son choix, dans l'ordre qu'il veut, tant qu'il a assez d'électricité (voir specs.md §3.3)
2. **Tour de l'ennemi** : l'ennemi attaque automatiquement pour 7 dégâts

Ce cycle se répète jusqu'à la fin du combat.

---

## 7. Fin de combat

- **Victoire** : l'ennemi atteint 0 PV
- **Défaite** : le module de base atteint 0 PV (cf. specs.md §3.4 : la destruction du module de base termine la run)

---

## 8. Points laissés à l'appréciation de l'implémentation

- Taille de main (5 cartes) et non-cumul de l'électricité entre tours : valeurs choisies pour ce POC, à ajuster après tests
- Comportement du Bouclier (absorbe avant les PV, expire en fin de combat) : à confirmer si besoin d'un comportement différent
