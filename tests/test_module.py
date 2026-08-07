"""
Tests unitaires pour la classe Module.
"""

from src.gameplay.module import Module


def test_module_commence_a_pv_max():
    module = Module(pv_max=15)

    assert module.pv == 15
    assert module.bouclier == 0
    assert not module.est_detruit()


def test_bouclier_absorbe_les_degats_avant_les_pv():
    # Exemple de specs.md paragraphe 3.5 : 7 degats vs 5 bouclier -> 2 degats aux PV
    module = Module(pv_max=15)
    module.ajouter_bouclier(5)

    module.subir_degats(7)

    assert module.bouclier == 0
    assert module.pv == 13


def test_bouclier_absorbe_totalement_si_superieur_aux_degats():
    module = Module(pv_max=15)
    module.ajouter_bouclier(10)

    module.subir_degats(4)

    assert module.bouclier == 6
    assert module.pv == 15


def test_soigner_ne_depasse_pas_le_pv_max():
    module = Module(pv_max=15)
    module.subir_degats(3)  # pv = 12, il manque 3 PV

    module.soigner(8)  # un soin de 8 ne doit pas depasser le maximum

    assert module.pv == 15


def test_module_detruit_a_zero_pv():
    module = Module(pv_max=15)

    module.subir_degats(20)

    assert module.pv == 0
    assert module.est_detruit()
