"""
Tests unitaires pour src/gameplay/vaisseau.py (modules de la refonte sur la grille du joueur).
"""

import pytest

from src.gameplay.module import charger_modules
from src.gameplay.position import Ligne, Position, Colonne
from src.gameplay.vaisseau import Vaisseau


def _modules():
    modeles = charger_modules()
    principal = modeles["MOD_1"].nouvel_exemplaire("M1", "base").copie_pour_combat()
    lanceur = modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche").copie_pour_combat()
    return principal, lanceur


def test_le_principal_occupe_toute_la_colonne_du_milieu():
    principal, lanceur = _modules()
    vaisseau = Vaisseau([principal, lanceur])

    assert vaisseau.principal is principal
    assert vaisseau.module_en(Position(Ligne.AVANT, Colonne.MID)) is principal
    assert vaisseau.module_en(Position(Ligne.ARRIERE, Colonne.MID)) is principal
    assert vaisseau.modules_vivants_de_ligne(Ligne.AVANT) == [principal, lanceur]
    assert vaisseau.modules_vivants_de_ligne(Ligne.ARRIERE) == [principal]


def test_proximite_colonne_de_l_ennemi_puis_voisines():
    principal, lanceur = _modules()
    vaisseau = Vaisseau([principal, lanceur])

    assert vaisseau.module_le_plus_proche(Colonne.GAUCHE) is lanceur
    assert vaisseau.module_le_plus_proche(Colonne.DROITE) is principal
    lanceur.subir_degats(20)
    assert vaisseau.module_le_plus_proche(Colonne.GAUCHE) is principal
    assert vaisseau.module_en(Position(Ligne.AVANT, Colonne.GAUCHE)) is None


def test_un_module_hors_combat_est_refuse():
    modeles = charger_modules()

    with pytest.raises(ValueError, match="copies de combat"):
        Vaisseau([modeles["MOD_1"].nouvel_exemplaire("M1", "base")])


def test_un_vaisseau_sans_principal_ou_avec_deux_modules_au_meme_endroit_est_refuse():
    principal, lanceur = _modules()
    second = charger_modules()["MOD_2"].nouvel_exemplaire("M3", "avant_gauche").copie_pour_combat()

    with pytest.raises(ValueError, match="pas de module principal"):
        Vaisseau([lanceur])
    with pytest.raises(ValueError, match="occupe deux fois"):
        Vaisseau([principal, lanceur, second])
