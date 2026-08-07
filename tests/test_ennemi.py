"""
Tests unitaires pour la classe Ennemi.
"""

from src.gameplay.ennemi import Ennemi


def test_ennemi_commence_a_pv_max():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    assert ennemi.pv == 15
    assert not ennemi.est_detruit()


def test_ennemi_subit_des_degats():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.subir_degats(9)

    assert ennemi.pv == 6


def test_ennemi_detruit_a_zero_pv():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.subir_degats(30)

    assert ennemi.pv == 0
    assert ennemi.est_detruit()
