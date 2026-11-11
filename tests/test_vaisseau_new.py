"""
Tests unitaires pour src/gameplay/vaisseau_new.py (modules de la refonte sur la grille du joueur).
"""

import pytest

from src.gameplay.module_new import charger_modules_new
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau_new import VaisseauNew


def _modules():
    modeles = charger_modules_new()
    principal = modeles["MOD_1"].nouvel_exemplaire("M1", "base").copie_pour_combat()
    lanceur = modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche").copie_pour_combat()
    return principal, lanceur


def test_le_principal_occupe_toute_la_rangee_du_milieu():
    principal, lanceur = _modules()
    vaisseau = VaisseauNew([principal, lanceur])

    assert vaisseau.principal is principal
    assert vaisseau.module_en(Position(Colonne.AVANT, Rangee.MID)) is principal
    assert vaisseau.module_en(Position(Colonne.ARRIERE, Rangee.MID)) is principal
    assert vaisseau.modules_vivants_de_colonne(Colonne.AVANT) == [principal, lanceur]
    assert vaisseau.modules_vivants_de_colonne(Colonne.ARRIERE) == [principal]


def test_proximite_rangee_de_l_ennemi_puis_voisines():
    principal, lanceur = _modules()
    vaisseau = VaisseauNew([principal, lanceur])

    assert vaisseau.module_le_plus_proche(Rangee.GAUCHE) is lanceur
    assert vaisseau.module_le_plus_proche(Rangee.DROITE) is principal
    lanceur.subir_degats(20)
    assert vaisseau.module_le_plus_proche(Rangee.GAUCHE) is principal
    assert vaisseau.module_en(Position(Colonne.AVANT, Rangee.GAUCHE)) is None


def test_un_module_hors_combat_est_refuse():
    modeles = charger_modules_new()

    with pytest.raises(ValueError, match="copies de combat"):
        VaisseauNew([modeles["MOD_1"].nouvel_exemplaire("M1", "base")])


def test_un_vaisseau_sans_principal_ou_avec_deux_modules_au_meme_endroit_est_refuse():
    principal, lanceur = _modules()
    second = charger_modules_new()["MOD_2"].nouvel_exemplaire("M3", "avant_gauche").copie_pour_combat()

    with pytest.raises(ValueError, match="pas de module principal"):
        VaisseauNew([lanceur])
    with pytest.raises(ValueError, match="occupe deux fois"):
        VaisseauNew([principal, lanceur, second])
