# Guide : ennemis, boss et flottes

## Cadre chiffré (à relire dans les specs, il peut changer)

- Modèle : combat.md §13.1. Un ennemi a des **PV**, des **valeurs nommées** qui peuvent
  augmenter avec les tours (`base`, `augmentation`, `tous_les`), et un **cycle d'étapes** (une par
  tour ennemi, chaque étape = une liste d'effets, avec `repetitions` possibles).
- Natures et cibles existantes : combat.md §13.2.2 (Attaque `PROXIMITE` / `TOUS_MODULES`,
  Bouclier et Renvoi sur `SOI_MEME` / `ALLIE_AVANT_SINON_ARRIERE`). Tout le reste est ✱ (ex.
  Surcharge ennemie : effets-a-coder.md §1.4).
- Coefficient de difficulté (§13.1.4) : multiplie valeurs, augmentations et PV.
- Flottes (§13.4) : 1 ennemi en Prime jusqu'au niveau 5, 2 ensuite ; Boss au niveau 10.
  Placement : `PROTECTEUR_AVANT`, `PROTEGE_ARRIERE`, tailles S / M (2 cases).
- Vaisseau du joueur : PV dans `config/modules.md` (principal 60, secondaires repartent pleins à
  chaque combat). Intentions visibles (§13.2.3) : le joueur voit le coup suivant.
- Valeurs à jour : `config/ennemis.md` (tableau généré, avec les valeurs des tours 1 à 6).

## Budget (repère, proposition 2026-11-18)

- **Durée visée d'un combat** : 3 à 4 tours pour un ennemi normal du niveau, 6 à 8 pour un boss.
- **PV ≈ dégâts par tour du deck attendu à ce niveau × durée visée.** Deck de départ : environ
  12 à 18 dégâts par tour (3⚡ de Laser, moins les tours de défense) ; à mesurer par simulation
  plutôt qu'à estimer.
- **Dégâts par tour de l'ennemi** : ce que les cartes de défense d'un tour (≈ 5 à 10 de bouclier)
  absorbent à peu près, pour qu'un tour de défense soit un vrai choix. Une attaque `TOUS_MODULES`
  compte pour une attaque **par module**.
- **Montée en puissance** : l'augmentation (+1 tous les 3 tours) punit les combats longs ; un
  ennemi « horloge » (grosse augmentation) oblige le joueur à scaler vite.
- Contrôle hors norme : PV ÷ (dégâts du deck par tour) et dégâts par tour ÷ PV du principal,
  comparés aux ennemis existants ; « non évalué » si les dégâts du deck ne sont pas connus.

## Rôles (pour varier une flotte)

| Rôle | Exemple existant | Ce qu'il demande au joueur |
|---|---|---|
| Frappeur | Pat le Pirate, Le nettoyeur | défense ou tuer vite |
| Tank / protecteur | Petit Jean | zone, ou ignorer le bouclier |
| Zone | Le puzzle | boucliers sur tous les modules |
| Punition | Miroir (renvoi) | choisir quand attaquer |
| Boss | Le Boss des pirates | combat long, scaling |

Un nouvel ennemi doit **demander une réponse différente** au joueur (lire les intentions,
changer de cible, garder du bouclier) : sinon c'est un sac de PV de plus.

## Pièges

| Piège | Remède |
|---|---|
| Sac de PV sans décision | une étape qui change la priorité (bouclier, renvoi, buff) |
| Dégâts imparables au tour 1 | première étape faible, ou intention claire |
| Ennemi qui annule un module entier (ex. immunité aux zones) | contre partiel, pas total |
| Cycle trop long pour être lisible | 1 à 3 étapes |
| Hasard caché | une cible tirée au hasard n'est pas annoncée : l'éviter sur les gros coups |
| Bouclier ennemi + renvoi cumulés sans limite | plafond ou extinction claire |

## Format de proposition

Colonnes du tableau (comme `config/ennemis.json`) : `id` (`ENM_...`), `nom`, `taille`,
`emplacements`, `placement`, `pv`, `valeurs` (base, augmentation, tous_les), `actions` (cycle,
étape par étape), rôle, niveau visé, mécaniques ✱.
