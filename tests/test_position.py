"""
Tests unitaires pour les primitives de position (src/gameplay/position.py).
"""

from src.gameplay.position import Ligne, Position, Colonne, ordre_colonnes_par_proximite


def test_ordre_depuis_gauche():
    assert ordre_colonnes_par_proximite(Colonne.GAUCHE) == [Colonne.GAUCHE, Colonne.MID, Colonne.DROITE]


def test_ordre_depuis_mid_privilegie_gauche_en_cas_d_egalite():
    assert ordre_colonnes_par_proximite(Colonne.MID) == [Colonne.MID, Colonne.GAUCHE, Colonne.DROITE]


def test_ordre_depuis_droite():
    assert ordre_colonnes_par_proximite(Colonne.DROITE) == [Colonne.DROITE, Colonne.MID, Colonne.GAUCHE]


def test_position_egalite_par_valeur():
    assert Position(Ligne.AVANT, Colonne.GAUCHE) == Position(Ligne.AVANT, Colonne.GAUCHE)
    assert Position(Ligne.AVANT, Colonne.GAUCHE) != Position(Ligne.ARRIERE, Colonne.GAUCHE)


def test_position_utilisable_comme_cle_de_dict():
    cles = {Position(Ligne.AVANT, Colonne.GAUCHE): "test"}
    assert cles[Position(Ligne.AVANT, Colonne.GAUCHE)] == "test"
