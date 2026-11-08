# Ennemis (refonte) — tableau généré

> **Fichier généré automatiquement à partir de `config/ennemi_new.json`, ne pas le modifier à la
> main** : toute modification se fait dans le JSON, puis `python -m outils.tableau_ennemis`
> régénère ce tableau (un test échoue tant qu'il n'est pas à jour).
>
> Valeurs : base, puis augmentation et rythme (« +1 / 3 tours » : +1 aux tours 4, 7, 10…), avant
> coefficient de difficulté. Cycle : une étape par tour ennemi, retour à la première après la
> dernière.

6 ennemis.

| Id | Nom | Taille | Cases | Placement | PV | Valeurs | Cycle d'actions | Tours 1 à 6 |
|---|---|---|---|---|---|---|---|---|
| ENM_PAT_LE_PIRATE | Pat le Pirate | S | 1 | — | 50 | degats 5 (+1 / 3 tours) | 1. Attaque {degats}, le plus proche | degats : 5, 5, 5, 6, 6, 6 |
| ENM_LE_NETTOYEUR | Le nettoyeur | S | 1 | PROTEGE_ARRIERE | 25 | degats 7 (+1 / 3 tours) | 1. Attaque {degats} ×2, le plus proche | degats : 7, 7, 7, 8, 8, 8 |
| ENM_PETIT_JEAN | Petit Jean | S | 1 | PROTECTEUR_AVANT | 100 | degats 2 (+1 / 3 tours)<br>bouclier 6 | 1. Attaque {degats}, le plus proche + Bouclier {bouclier}, soi-même<br>2. Attaque {degats}, le plus proche | degats : 2, 2, 2, 3, 3, 3<br>bouclier : 6, 6, 6, 6, 6, 6 |
| ENM_LE_PUZZLE | Le puzzle | S | 1 | — | 50 | degats 5 (+1 / 3 tours) | 1. Attaque {degats}, tous les modules | degats : 5, 5, 5, 6, 6, 6 |
| ENM_MIROIR | Miroir | S | 1 | — | 50 | degats 2 (+1 / 3 tours)<br>renvoi 5 | 1. Attaque {degats}, le plus proche + Renvoi {renvoi}, un allié avant, sinon arrière | degats : 2, 2, 2, 3, 3, 3<br>renvoi : 5, 5, 5, 5, 5, 5 |
| ENM_BOSS_PIRATES | Le Boss des pirates | M | 2 | — | 150 | degats 5 (+2 / 3 tours)<br>bouclier 10 | 1. Attaque {degats}, tous les modules<br>2. Attaque {degats}, tous les modules<br>3. Attaque {degats}, tous les modules + Bouclier {bouclier}, soi-même | degats : 5, 5, 5, 7, 7, 7<br>bouclier : 10, 10, 10, 10, 10, 10 |
