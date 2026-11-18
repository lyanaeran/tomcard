# Guide : cartes et modules

## Cadre chiffré (à relire dans les specs, il peut changer)

- **3 électricité (⚡) par tour, pioche de 5 cartes**, main défaussée en fin de tour
  (combat.md §3.7).
- Deck de départ : les cartes du module principal (`config/modules.md`) ; une carte gagnée par
  combat (une candidate par module équipé, ou Passer).
- **Dilution** : une carte précise a environ **5 / taille du deck** chances d'être en main à un
  tour donné (50 % avec 10 cartes, 25 % avec 20). Une carte n'est forte que si on la pioche :
  les cartes de pioche et les effets « jusqu'à la fin du combat » valent plus dans un gros deck.
- **Cycle** : taille du deck ÷ 5 = nombre de tours pour revoir une carte.
- Munitions (combat.md §3.6) : limitent une carte forte sans changer son coût ; reviennent au
  combat suivant.

## Budget de puissance (repère, proposition 2026-11-18)

Référence : *Laser* (base) = **6 dégâts pour 1⚡**.

| Rareté | Cible unique | Zone (par ennemi) | Remarque |
|---|---|---|---|
| Base | 6 / ⚡ | — | cartes de départ |
| Commune | ≈ 7 / ⚡ | ≈ 4–5 / ⚡ | |
| Rare | ≈ 9–10 / ⚡ | ≈ 6–8 / ⚡ | +30 à 40 % |
| Légendaire | hors budget | | change la façon de jouer : moteur, effet jusqu'à la fin du combat |

Équivalences pour chiffrer un effet secondaire (propositions, à ajuster par simulation) :

| Effet | Vaut environ |
|---|---|
| 1 bouclier | 1 dégât |
| Piocher 1 carte | 3 à 4 dégâts |
| +1⚡ | 6 dégâts |
| 1 incendie | 1 à 1,5 dégât (il dure, mais baisse) |
| Surcharge X | X × nombre de coups attendus sur sa durée |
| 1 munition en moins sur 3 | +20 à 30 % de budget |
| Coût 0 | effet petit (≤ 4 dégâts) ou contrepartie |

Le **contrôle hors norme** (SKILL.md, étape 2 bis) compare chaque carte à ces repères.

## Format d'une carte (`config/cartes.json`)

Lire modules-cartes.md §12.1 à §12.5. Les colonnes du tableau de proposition suivent ces champs :
`id`, `nom`, `rarete`, `categorie`, `cible`, `modules`, `cout`, `munitions`, `lancements`,
`persistante`, `description` (avec `{valeurs}`), `valeurs`, `effets` (nature, valeur, portée,
durée, filtre), `jouable`.

- **Ce qui existe** : natures d'effet (modules-cartes.md §12.2, colonne « État »), portées (§12.3),
  cibles (§7.2, combat.md §3.8.2), statuts (combat.md §3.5). Tout le reste est ✱.
- **Interaction** : toute carte se joue par sélection puis clic sur une case valide, même sans
  choix réel (interface.md §8.3). Une carte « sans cible » choisit quand même une cible de clic
  (souvent « Module Principal » ou « Ennemi Tous »).
- Une carte qui demande du code reste `"jouable": "non"` tant qu'il n'est pas fait.

## Identité d'un module

Avant les cartes, écrire en une phrase **le rôle du module** (« spécialisé attaque, monte en
dégâts ») et **sa façon de monter en puissance** : chaque module doit offrir au moins une manière
de « scaler » contre des ennemis de plus en plus forts. Idées de modules : modules-cartes.md
§4.1 à §4.3 ; anciennes cartes : `specs/archive-cartes-modules.md`.

Répartition demandée la dernière fois (Lanceur) : 15 communes, 8 rares, 3 légendaires minimum,
coûts variés (0 à 3⚡). Proposer plus, l'utilisateur choisit.

## Pièges (vérifier chaque proposition)

| Piège | Signe | Remède |
|---|---|---|
| **« Pour chaque X » sans plafond** | dégâts × cartes jouées, + par point de statut | plafond, diviseur, ou compter une chose bornée (ennemis vivants, modules) |
| **Doublement** | « double votre Surcharge / électricité » | munitions 1–2, coût élevé, ou effet figé une seule fois |
| **Boucle de ressources** | une carte rend plus d'⚡ ou de pioche qu'elle ne coûte | condition (ennemi tué), munitions, plafond par tour |
| **Coût 0 sans contrepartie** | 0⚡ et effet de carte à 1⚡ | effet ≤ 4 dégâts, ou munitions |
| **Carte morte** | dépend d'une condition rare (statut absent, une seule carte qui le pose) | au moins 3–4 cartes qui posent / utilisent la mécanique |
| **Mécanique orpheline** | ✱ utilisée par une seule carte | l'assumer explicitement (« une seule carte, exprès ») ou ajouter des cartes |
| **Règle cachée dans l'ordre des effets** | « puis Surcharge » : profite-t-elle à ses propres dégâts ? | trancher et l'écrire dans la description |
| **Descriptions incohérentes** | mêmes effets formulés différemment | reprendre les tournures des cartes existantes (« Inflige {degats} dégâts à un ennemi ») |
| **Hasard non injecté** | rebond, cible au hasard | tirage par `Combat.aleatoire` (src/gameplay/CLAUDE.md) |
| **Règle dans l'affichage** | effet qui dépendrait de l'UI | toute règle dans `src/gameplay/` |

## Exemple complet

`specs/proposition-lanceur-missiles.md` (2026-11-18) : proposition, réponses de l'utilisateur,
tableau et implémentation. S'en servir comme modèle de niveau de détail.
