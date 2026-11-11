# outils/simulation — simulateurs d'équilibrage

Chargé automatiquement quand on travaille dans `outils/simulation/`. Règles générales : `CLAUDE.md`
racine. Conception : `specs/simulation.md` (§11 ancien moteur, §12 refonte).

## Accord préalable obligatoire

**Ne jamais lancer une campagne sans l'accord de l'utilisateur** (consigne du 2026-11-11 : c'est
long). Proposer le volume et la durée estimée, attendre son feu vert. Un essai qu'il a demandé et
dimensionné lui-même (ex. « 20 combats ») est autorisé tel quel, sans l'élargir. Sur Mac, toujours
lancer avec `caffeinate -i` (sinon la mise en veille interrompt le calcul), de préférence en
arrière-plan.

## Deux simulateurs

| | Ancien moteur (jeu actuel) | Combat de la refonte (`CombatNew`) |
|---|---|---|
| Fichiers | `bot.py`, `partie_auto.py`, `etudes.py`, `rapport.py`, `__main__.py` | `bot_new.py`, `combats_new.py`, `essai_bouclier.py` |
| Lancement | `caffeinate -i python -m outils.simulation --budget 500 --parties-par-module 40 --validation 30` | `caffeinate -i python -m outils.simulation.combats_new --graines 30 --robustesse 2000 --enchainements 300 --graine 1` (environ 3 min sur 8 cœurs) |
| Ce qu'il joue | combats et parties complètes (parcours, Stations, Aventures) | combats isolés seulement (le nouveau combat n'est pas branché au parcours) : robustesse avec contrôle d'invariants, équilibre par ennemi / paire / Boss, enchaînement approché des niveaux 2 à 10 |
| Tests | `tests/test_simulation.py` | `tests/test_simulation_combats_new.py` |

- **Bot « recherche »** : recherche en faisceau sur des copies du combat, chaque séquence notée
  après la réponse ennemie simulée. Côté refonte, l'évaluation ajoute la **valeur des lancements en
  plus** (cartes de répétition), estimée d'après le numéro du tour (jamais d'après les PV ennemis :
  le bot gagnait alors des points à ne pas frapper).
- **Essai sur une valeur de carte** sans toucher aux JSON : `construire_combat(...,
  valeurs_cartes={"CRT_10": {"bouclier": 4}})` (exemple : `essai_bouclier.py`).
- Aucune règle de jeu dans les simulateurs : ils ne font que choisir des cartes et des cibles.
  Exception provisoire : la composition des flottes de la refonte (`construire_flotte`), reprise de
  `config_poc`, en attendant celle du jeu.

## Résultats et synthèses

- Résultats bruts (JSON) et tableaux (Markdown) : `outils/simulation/resultats/`, **ignoré par
  git**, horodaté.
- Synthèses rédigées pour l'utilisateur : `outils/simulation/synthese/` (fichiers générés, hors
  `specs/`), une par campagne ou essai, datée. Structure habituelle : état du jeu testé (code,
  règles, valeurs, volume, durée, commande pour reproduire), « En bref », sections chiffrées,
  pistes **à décider par l'utilisateur**. Signaler les limites (bot qui ne voit que le tour
  suivant, petit échantillon, enchaînement approché sans Station).
- Taux de jeu d'une carte : trompeur pour une carte en plusieurs exemplaires quand l'électricité
  manque ; regarder aussi « jouée / tour » et la part de l'électricité dépensée.
