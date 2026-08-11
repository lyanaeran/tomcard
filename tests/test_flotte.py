"""
Tests unitaires pour la classe Flotte (grille d'ennemis).
"""

from src.gameplay.ennemi import Ennemi
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.flotte import Flotte


def _flotte_deux_ennemis() -> tuple[Flotte, Ennemi, Ennemi]:
    e1 = Ennemi(pv_max=8, degats_attaque=4)
    e2 = Ennemi(pv_max=16, degats_attaque=8)
    flotte = Flotte(
        {
            Position(Colonne.AVANT, Rangee.GAUCHE): e1,
            Position(Colonne.ARRIERE, Rangee.MID): e2,
        }
    )
    return flotte, e1, e2


def test_ennemi_en_renvoie_l_ennemi_de_la_case():
    flotte, e1, _e2 = _flotte_deux_ennemis()

    assert flotte.ennemi_en(Colonne.AVANT, Rangee.GAUCHE) is e1


def test_ennemi_en_renvoie_none_pour_une_case_non_declaree():
    flotte, _e1, _e2 = _flotte_deux_ennemis()

    assert flotte.ennemi_en(Colonne.AVANT, Rangee.MID) is None


def test_ennemi_en_renvoie_none_pour_un_ennemi_detruit():
    flotte, e1, _e2 = _flotte_deux_ennemis()
    e1.subir_degats(100)

    assert flotte.ennemi_en(Colonne.AVANT, Rangee.GAUCHE) is None


def test_ennemis_vivants_exclut_les_detruits():
    flotte, e1, e2 = _flotte_deux_ennemis()
    e1.subir_degats(100)

    vivants = flotte.ennemis_vivants()

    assert vivants == [e2]


def test_est_vide_quand_tous_les_ennemis_sont_detruits():
    flotte, e1, e2 = _flotte_deux_ennemis()
    assert not flotte.est_vide()

    e1.subir_degats(100)
    e2.subir_degats(100)

    assert flotte.est_vide()


def test_positions_inclut_les_detruits():
    flotte, e1, _e2 = _flotte_deux_ennemis()
    e1.subir_degats(100)

    positions = flotte.positions()

    assert len(positions) == 2
    assert e1 in positions.values()
