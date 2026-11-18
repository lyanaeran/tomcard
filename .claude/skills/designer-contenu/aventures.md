# Guide : Aventures

## Cadre (à relire dans les specs, il peut changer)

- Aventures existantes : `specs/aventures.md` §2.5 (Trois lunes, Astéroïdes, Police). Elles sont
  **scriptées en dur**, un écran par Aventure, pas de moteur narratif générique (décision
  utilisateur) ; un `config/aventures.json` est envisagé mais pas créé.
- Place dans le parcours : `specs/parcours.md` §2.3 (1 chance sur 10 par proposition de niveau).
- Ressources du joueur à mettre en jeu : **Argent** (départ 7 €, 5 € par ennemi tué, §2.1),
  **PV du principal** (seuls persistants), **cartes** du deck, **modules**, munitions.
- Présentation : texte d'ambiance, puis **2 ou 3 choix** empilés (image carrée + titre +
  description) ; une Aventure en plusieurs temps reste **un seul écran** dont le contenu change.
- Les règles (tirages, coûts, résultats) vivent dans `src/gameplay/` ; PC et web affichent.

## Budget (repère, proposition 2026-11-18)

- Un choix **sûr** : gain modeste ou rien. Un choix **risqué** : gain clairement meilleur, avec un
  risque chiffré (« 50 % : +1 carte rare, sinon −10 PV »).
- Comparer aux autres étapes : une Aventure doit valoir à peu près une Prime (≈ 5 à 10 € + une
  carte) en espérance, plus de variance.
- Contrôle hors norme : calculer l'espérance de chaque choix en € et PV ; signaler un choix
  dominé (toujours moins bon qu'un autre) ou dominant (toujours meilleur).

## Pièges

| Piège | Remède |
|---|---|
| Choix évident (un choix domine) | chaque choix doit perdre quelque chose |
| Hasard non annoncé | annoncer les chances ou au moins le risque |
| Punition qui tue la partie | plafonner les pertes de PV, jamais de défaite directe sans choix |
| Texte trop long | 2 à 4 phrases d'ambiance, une ligne par choix |
| Règle dans l'écran | résolution dans `src/gameplay/` (précédent : Astéroïdes, Police) |

## Format de proposition

Pour chaque Aventure : nom, texte d'ambiance (accentué), puis un tableau des choix : titre,
description affichée, condition (ex. « 10 € requis »), résultat (avec chances), étape suivante si
l'Aventure est en plusieurs temps, image à fournir.
