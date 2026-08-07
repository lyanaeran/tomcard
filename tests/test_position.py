"""
Tests unitaires pour les primitives de position (src/gameplay/position.py).
"""

from src.gameplay.position import Colonne, Position, Rangee, ordre_rangees_par_proximite


def test_ordre_depuis_gauche():
    assert ordre_rangees_par_proximite(Rangee.GAUCHE) == [Rangee.GAUCHE, Rangee.MID, Rangee.DROITE]


def test_ordre_depuis_mid_privilegie_gauche_en_cas_d_egalite():
    assert ordre_rangees_par_proximite(Rangee.MID) == [Rangee.MID, Rangee.GAUCHE, Rangee.DROITE]


def test_ordre_depuis_droite():
    assert ordre_rangees_par_proximite(Rangee.DROITE) == [Rangee.DROITE, Rangee.MID, Rangee.GAUCHE]


def test_position_egalite_par_valeur():
    assert Position(Colonne.AVANT, Rangee.GAUCHE) == Position(Colonne.AVANT, Rangee.GAUCHE)
    assert Position(Colonne.AVANT, Rangee.GAUCHE) != Position(Colonne.ARRIERE, Rangee.GAUCHE)


def test_position_utilisable_comme_cle_de_dict():
    cles = {Position(Colonne.AVANT, Rangee.GAUCHE): "test"}
    assert cles[Position(Colonne.AVANT, Rangee.GAUCHE)] == "test"
