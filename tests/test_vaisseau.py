"""
Tests unitaires pour la classe Vaisseau (grille de modules du joueur).
"""

from src.gameplay.module import Module
from src.gameplay.position import Colonne, Rangee
from src.gameplay.vaisseau import Vaisseau


def _vaisseau_complet() -> Vaisseau:
    return Vaisseau(
        base=Module(pv_max=15),
        avant_gauche=Module(pv_max=12),
        avant_droite=Module(pv_max=18),
        arriere_gauche=Module(pv_max=10),
        arriere_droite=Module(pv_max=9),
    )


def test_mid_renvoie_toujours_la_base_quelle_que_soit_la_colonne():
    vaisseau = _vaisseau_complet()

    assert vaisseau.module_en(Colonne.AVANT, Rangee.MID) is vaisseau.base
    assert vaisseau.module_en(Colonne.ARRIERE, Rangee.MID) is vaisseau.base


def test_module_en_renvoie_le_module_equipe_correspondant():
    vaisseau = _vaisseau_complet()

    module = vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE)

    assert module is not None
    assert module.pv_max == 12


def test_module_en_renvoie_none_pour_un_emplacement_vide():
    vaisseau = Vaisseau(base=Module(pv_max=15))

    assert vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE) is None


def test_module_en_renvoie_none_pour_un_module_detruit():
    vaisseau = _vaisseau_complet()
    module = vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE)
    module.subir_degats(100)

    assert vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE) is None


def test_mid_renvoie_none_si_la_base_est_detruite():
    vaisseau = _vaisseau_complet()
    vaisseau.base.subir_degats(100)

    assert vaisseau.module_en(Colonne.AVANT, Rangee.MID) is None
    assert vaisseau.est_detruit()


def test_modules_equipes_inclut_les_detruits():
    vaisseau = _vaisseau_complet()
    module = vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE)
    module.subir_degats(100)

    equipes = vaisseau.modules_equipes()

    assert len(equipes) == 4
    assert module in equipes.values()
