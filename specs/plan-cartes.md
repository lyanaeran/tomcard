# Plan : rendre jouables les cartes du principal et du Lanceur

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). Plan validé par l'utilisateur
le 2026-11-25 pour coder les cartes décidées dans
[proposition-lanceur-missiles.md](proposition-lanceur-missiles.md) (§2) et
[proposition-module-principal.md](proposition-module-principal.md) (§2 et §5). Les mécaniques
partagées par les deux propositions sont codées une seule fois. Rien n'est codé à la date du plan ;
**toutes les valeurs des cartes sont inventées**, à régler.*

---

## 1. Objectif et périmètre

- **Aujourd'hui** : 19 cartes jouables (11 du principal, 8 du Lanceur).
- **À la fin du plan** : **62 cartes jouables** sur les 77 décidées (4 de base, 36 du principal,
  37 du Lanceur).
- **15 cartes sont mises de côté** (décision utilisateur, 2026-11-25) : leurs mécaniques ne
  servent qu'à 1 à 4 cartes chacune (§4). Elles restent dans les propositions, **pas dans
  `config/cartes.json`** (pas de format inventé pour une mécanique non codée).
- Après les mises de côté : Lanceur **15 communes, 8 rares, 3 légendaires** (le minimum demandé
  au départ), principal **18 communes, 11 rares, 3 légendaires**.

## 2. Décisions prises pour le plan (décision utilisateur, 2026-11-25)

1. **Images** : l'agent ne sait pas générer d'illustrations. Les nouvelles cartes reprennent
   l'image existante la plus proche (`assets/cartes/`) ; **étape 6** : demander les vraies images
   à l'utilisateur.
2. **Baisse des statuts : une seule règle pour tous**, celle de combat.md §3.5.2 : tous les
   statuts d'une entité baissent ensemble, **à la fin du tour de son adversaire** (ennemi : fin du
   tour du joueur ; module : fin du tour ennemi).
   - **Verrouillage** (porté par un ennemi) : −1 à la fin du tour du joueur, avec l'incendie, le
     bouclier et le renvoi de l'ennemi.
   - **Surcharge** (portée par le principal) : −1 à la fin du tour ennemi, avec le bouclier du
     principal. Pour le joueur : Surcharge 4 posée au tour 1 → +4 pendant tout le tour 1, +3 au
     tour 2, +2 au tour 3… ; pour un boss qui se la poserait, elle baisserait à la fin du tour du
     joueur.
3. **Laser de base** (CRT_7) : **famille Laser**, donc boosté par Protocole laser ; Salve laser
   continue de ne viser que lui (par son id).
4. **Protocole d'urgence** : **garde 3 munitions** (le cumul reste possible, à surveiller en
   simulation).
5. **Le renommage ligne / colonne passe en premier** (lot 0), pour que tout le code nouveau soit
   écrit avec le bon vocabulaire.

## 3. Les étapes

Une PR `devjeux` → `main` par lot ; un lot commence quand le précédent est mergé (une seule
branche de travail).

| Étape | Contenu | Cartes rendues jouables | Jouables à la fin |
|---|---|---|---|
| **0** | **Renommage ligne / colonne** (combat.md §3.1.1) dans le code, les données, l'affichage, la simulation et les specs ; aucun changement de jeu ; texte et cible de Laser perçant corrigés au passage. **Fait le 2026-11-25** | — | 19 |
| **1** | **Données seulement** : cartes renommées ou revalorisées, nouvelles cartes sans mécanique, Leurre retiré du Lanceur (`"modules": []`). **Fait le 2026-11-25** : 40 cartes dans `config/cartes.json`, images provisoires reprises des existantes (étape 6) | Lanceur : Missile à fragmentation, Vague de torpilles, Ogive légère, Torpille arrière, Torpille avant, Mini-missile, Missile guidé, Missiles jumeaux, Missile thermique, Ogive lourde, Missile incendiaire, Ogive nucléaire. Principal : Laser perçant, Laser lourd, Laser incendiaire, Laser d'appoint, Laser double, Laser de siège, Laser orbital, Bouclier d'escadre, Bouclier avant, Bouclier réactif, Bouclier chargé, Bouclier intégral, Réparation rapide, Réparation de champ, Réparation complète, Réacteur d'appoint, Réacteur en surrégime, Protocole d'analyse | 38 |
| **2** | **Mécaniques simples** : portées `MODULE_PRINCIPAL`, `MODULE_DE_LA_CARTE`, `MEME_COLONNE` ; Renvoi posé par les cartes ; retrait de bouclier | Missile de couverture, Torpille de barrage, Torpille traversante, Laser défensif, Bouclier réfléchissant, Bouclier miroir, Protocole de riposte, Laser disrupteur | 46 |
| **3** | **Surcharge** (statut, doublement, Surcharge figée) et **bonus calculé** (dont le bouclier du principal consommé) | Ogive surchauffée, Post-combustion, Amplificateur, Armer le lanceur, Missile surchargé, Lanceur incandescent, Réacteur en surtension, Laser de contre-charge | 54 |
| ⏸ | **Point d'étape** : l'utilisateur règle les valeurs dans l'éditeur de cartes, puis simulation (volume et durée proposés, **accord de l'utilisateur** avant de la lancer) | | |
| **4** | **Verrouillage** | Missile marqueur, Ogive de marquage, Missile verrouilleur, Missile de précision, Laser de visée, Protocole de ciblage | 60 |
| **5** | **Champ `famille`** (seulement sur les cartes Laser) et **filtres** par module et par famille | Feu à volonté, Protocole laser | 62 |
| **6** | **Images** : demander à l'utilisateur les illustrations des nouvelles cartes et les remplacer | — | 62 |
| ⏸ | **Simulation finale**, avec l'accord de l'utilisateur | | |

## 4. Cartes mises de côté (15)

À reprendre plus tard, mécanique par mécanique, quand l'utilisateur le demandera :

| Mécanique | Cartes |
|---|---|
| Exécution | Coup de grâce, Chasseur de primes |
| Coups au hasard, rebonds | Ogive à dispersion, Missile rebondissant, Missile à ricochets |
| Calibrage | Calibrage |
| Rechargement | Rechargement rapide |
| Perforant | Torpille perforante |
| Destruction (règles à trancher, refonte-destruction.md §3) | Piéger le lanceur |
| Électricité différée, report, début de tour, réactions | Réacteur à condensateur, Réacteur à batterie, Réacteur à fusion, Cadence de tir |
| Répétition limitée au tour | Double frappe, Protocole de tir |

## 5. Ce que fait chaque lot

1. Le code dans `src/gameplay/` seulement, avec ses tests ; une carte qui attend sa mécanique
   reste hors de `config/cartes.json` (cartes mises de côté) ou `"jouable": "non"`.
2. `config/cartes.json` mis à jour, `config/cartes.md` régénéré (`python -m outils.tableau_cartes`),
   `pytest`.
3. Vérification **PC et web** (`src/ui/CLAUDE.md`, `src/web/CLAUDE.md`) dès que l'affichage
   change : pastilles Surcharge, Verrouillage, Renvoi sur les modules, journal (lots 0, 2, 3, 4).
4. Les règles codées passent dans combat.md (statuts, §3.5) ou modules-cartes.md (§12) et sont
   retirées des propositions et d'[effets-a-coder.md](effets-a-coder.md).
5. PR `devjeux` → `main`, plan de test, valeurs inventées signalées.
