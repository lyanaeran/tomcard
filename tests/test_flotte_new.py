"""
Tests unitaires pour src/gameplay/flotte_new.py (ennemis de la refonte sur la grille ennemie).
"""

import pytest

from src.gameplay.ennemi_new import charger_ennemis_new
from src.gameplay.flotte_new import FlotteNew
from src.gameplay.position import Colonne, Position, Rangee


def _ennemi(id_ennemi):
    return charger_ennemis_new()[id_ennemi].pour_combat()


def test_ordre_de_jeu_avant_puis_arriere_de_droite_a_gauche():
    """Decision utilisateur : la rangee gauche est en bas de l'ecran."""
    arriere_droite, avant_gauche, avant_droite = (_ennemi("ENM_PAT_LE_PIRATE") for _ in range(3))
    flotte = FlotteNew({
        Position(Colonne.ARRIERE, Rangee.DROITE): arriere_droite,
        Position(Colonne.AVANT, Rangee.GAUCHE): avant_gauche,
        Position(Colonne.AVANT, Rangee.DROITE): avant_droite,
    })

    assert flotte.ennemis_vivants() == [avant_droite, avant_gauche, arriere_droite]


def test_un_ennemi_sur_deux_cases_compte_une_fois_et_est_dans_les_deux_colonnes():
    boss = _ennemi("ENM_BOSS_PIRATES")
    flotte = FlotteNew({Position(Colonne.AVANT, Rangee.MID): boss, Position(Colonne.ARRIERE, Rangee.MID): boss})

    assert flotte.ennemis_vivants() == [boss]
    assert flotte.ennemis_vivants_de_colonne(Colonne.ARRIERE) == [boss]
    assert flotte.rangee_de(boss) == Rangee.MID


def test_le_nombre_de_cases_doit_correspondre_aux_emplacements():
    with pytest.raises(ValueError, match="1 case"):
        FlotteNew({Position(Colonne.AVANT, Rangee.MID): _ennemi("ENM_BOSS_PIRATES")})


def test_la_flotte_est_vide_quand_tous_les_ennemis_sont_detruits():
    pat = _ennemi("ENM_PAT_LE_PIRATE")
    flotte = FlotteNew({Position(Colonne.AVANT, Rangee.MID): pat})

    pat.subir_degats(50)

    assert flotte.est_vide() and flotte.ennemi_en(Position(Colonne.AVANT, Rangee.MID)) is None
