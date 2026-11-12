# Cartes (refonte) — tableau généré

> **Fichier généré automatiquement à partir de `config/carte_new.json`, ne pas le modifier à la
> main** : toute modification se fait dans le JSON, puis `python -m outils.tableau_cartes`
> régénère ce tableau (un test échoue tant qu'il n'est pas à jour).

19 cartes.

| Id | Nom | Rareté | Catégorie | Cible | Coût | Munitions | Lancements | Persistante | Jouable | Refonte | Description affichée | Valeurs | Effets |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT_7 | Laser | Base | Attaque | Ennemi Unique | 1 | Illimitées | 1 | Non | Oui | Oui | Inflige 6 degats a un ennemi unique | `{"degats": 6}` | `{"nature": "DEGATS", "valeur": "degats"}` |
| CRT_10 | Bouclier | Base | Defense | Module Unique | 1 | Illimitées | 1 | Non | Oui | Oui | Bouclier de 4 sur un module unique | `{"bouclier": 4}` | `{"nature": "BOUCLIER", "valeur": "bouclier"}` |
| CRT_11 | Protéger le vaisseau | Base | Defense | Module Principal | 1 | Illimitées | 1 | Non | Oui | Oui | Bouclier de 6 sur le module principal | `{"bouclier": 6}` | `{"nature": "BOUCLIER", "valeur": "bouclier"}` |
| CRT_12 | Réparation | Base | Reparation | Module Principal | 1 | 2 | 1 | Non | Oui | Oui | Repare le module principal pour 8 | `{"reparation": 8}` | `{"nature": "REPARATION", "valeur": "reparation"}` |
| CRT_8 | Laser percant | Commune | Attaque | Ennemi Colonne | 2 | Illimitées | 1 | Non | Oui | Oui | Inflige 8 degats a la colonne ciblee | `{"degats": 8}` | `{"nature": "DEGATS", "valeur": "degats"}` |
| CRT_45 | Tir incendiaire | Commune | Attaque | Ennemi Unique | 2 | 3 | 1 | Non | Oui | Oui | Ajoute 4 points d’incendie sur la cible | `{"incendie": 4}` | `{"nature": "INCENDIE", "valeur": "incendie"}` |
| CRT_46 | Blindage cible | Commune | Defense | Module Unique | 2 | 3 | 1 | Non | Oui | Oui | Bouclier de 8 sur un module unique | `{"bouclier": 8}` | `{"nature": "BOUCLIER", "valeur": "bouclier"}` |
| CRT_47 | Laser lourd | Commune | Attaque | Ennemi Unique | 1 | Illimitées | 1 | Non | Oui | Oui | Inflige 12 degats a un ennemi unique | `{"degats": 12}` | `{"nature": "DEGATS", "valeur": "degats"}` |
| CRT_48 | Bouclier stabilise | Rare | Buff | Module Principal | 3 | 1 | 1 | Non | Oui | Oui | Les Boucliers de base sont lancés 1 fois de plus. | `{"repetitions": 1}` | `{"nature": "REPETITION", "valeur": "repetitions", "filtre": {"id": "CRT_10"}}` |
| CRT_49 | Salve laser | Rare | Buff | Module Tous | 2 | 2 | 1 | Non | Oui | Oui | Les Laser de base sont lances 1 fois de plus. | `{"repetitions": 1}` | `{"nature": "REPETITION", "valeur": "repetitions", "filtre": {"id": "CRT_7"}}` |
| CRT_50 | Protocole d'urgence | Legendaire | Buff | Module Tous | 3 | 3 | 1 | Non | Oui | Oui | Les cartes de bases sont lancees 1 fois de plus. | `{"repetitions": 1}` | `{"nature": "REPETITION", "valeur": "repetitions", "filtre": {"rarete": "Base"}}` |
| CRT_13 | Missiles | Commune | Attaque | Ennemi Unique | 2 | Illimitées | 1 | Non | Oui | Oui | Inflige 15 degats a un ennemi et 6 a tous les autres | `{"degats_cible": 15, "degats_autres": 6}` | `{"nature": "DEGATS", "valeur": "degats_cible"}`<br>`{"nature": "DEGATS", "valeur": "degats_autres", "portee": "AUTRES_ENNEMIS"}` |
| CRT_14 | Torpille | Commune | Attaque | Ennemi Tous | 2 | Illimitées | 1 | Non | Oui | Oui | Inflige 10 degats a la ligne avant et 8 a la ligne arriere | `{"degats_avant": 10, "degats_arriere": 8}` | `{"nature": "DEGATS", "valeur": "degats_avant", "portee": "COLONNE_AVANT_ENNEMIE"}`<br>`{"nature": "DEGATS", "valeur": "degats_arriere", "portee": "COLONNE_ARRIERE_ENNEMIE"}` |
| CRT_9 | Bombardement | Commune | Attaque | Ennemi Tous | 1 | Illimitées | 1 | Non | Oui | Oui | Inflige 6 degats a tous les ennemis | `{"degats": 6}` | `{"nature": "DEGATS", "valeur": "degats"}` |
| CRT_16 | Ligne arriere | Commune | Attaque | Ennemi Arriere | 1 | Illimitées | 1 | Non | Oui | Oui | Inflige 8 degats a tous les ennemis de la ligne arriere | `{"degats": 8}` | `{"nature": "DEGATS", "valeur": "degats"}` |
| CRT_15 | Ciel de missiles | Rare | Attaque | Ennemi Tous | 1 | Illimitées | 1 | Non | Oui | Oui | Inflige 8 degats a tous les ennemis | `{"degats": 8}` | `{"nature": "DEGATS", "valeur": "degats"}` |
| CRT_17 | Embrasement | Rare | Attaque | Ennemi Unique | 2 | Illimitées | 1 | Non | Oui | Oui | Ajoute 8 points d’incendie à un ennemi | `{"incendie": 8}` | `{"nature": "INCENDIE", "valeur": "incendie"}` |
| CRT_18 | Leurre | Rare | Defense | Module Unique | 1 | Illimitées | 1 | Non | Oui | Oui | Annule la prochaine attaque ciblant le module | `{}` | `{"nature": "ANNULATION_PROCHAINE_ATTAQUE"}` |
| CRT_19 | Guerre nucleaire | Legendaire | Attaque | Ennemi Tous | 3 | Illimitées | 1 | Non | Oui | Oui | Ajoute 8 points d’incendie à tous les ennemis | `{"incendie": 8}` | `{"nature": "INCENDIE", "valeur": "incendie"}` |
