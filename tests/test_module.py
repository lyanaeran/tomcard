"""
Tests unitaires pour la classe Module.
"""

from src.gameplay.carte import ActionCarte
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


def test_appliquer_buff_declenche_l_effet_immediatement():
    """Bouclier perpetuel (specs.md 12.3/12.5) : la pose du buff donne du bouclier tout
    de suite, comme les autres types de carte (pas seulement a partir du tour suivant)."""
    module = Module(pv_max=15)

    module.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 10, tours=None)

    assert module.bouclier == 10
    assert len(module.buffs_actifs) == 1


def test_declencher_buffs_tour_redeclenche_l_effet():
    module = Module(pv_max=15)
    module.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 10, tours=None)

    module.declencher_buffs_tour()
    module.declencher_buffs_tour()

    assert module.bouclier == 30  # 10 a la pose + 10 par declenchement


def test_buff_persistant_ne_decompte_jamais():
    """tours_restants=None (Bouclier perpetuel) : dure tout le combat, jamais retire."""
    module = Module(pv_max=15)
    module.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 10, tours=None)

    for _ in range(10):
        module.declencher_buffs_tour()

    assert len(module.buffs_actifs) == 1
    assert module.buffs_actifs[0].tours_restants is None


def test_buff_a_duree_expire_apres_n_tours():
    module = Module(pv_max=15)
    module.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 10, tours=2)

    module.declencher_buffs_tour()
    assert len(module.buffs_actifs) == 1  # encore actif apres 1 declenchement

    module.declencher_buffs_tour()
    assert module.buffs_actifs == []  # expire apres 2 declenchements


def test_deux_buffs_du_meme_type_coexistent_et_s_additionnent():
    module = Module(pv_max=15)

    module.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 10, tours=None)
    module.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 5, tours=1)

    assert module.bouclier == 15  # 10 + 5 a la pose
    assert len(module.buffs_actifs) == 2

    module.declencher_buffs_tour()

    assert module.bouclier == 30  # +10 (persistant) +5 (dernier declenchement avant expiration)
    assert len(module.buffs_actifs) == 1
    assert module.buffs_actifs[0].tours_restants is None
