"""
Tests unitaires pour la classe Ennemi.
"""

from src.gameplay.carte import ActionCarte
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


def test_reduction_degats_diminue_les_degats_infliges():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.appliquer_debuff(ActionCarte.REDUCTION_DEGATS, 5, tours=1)

    assert ennemi.degats_attaque_effectifs() == 2


def test_reduction_degats_ne_descend_jamais_sous_zero():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.appliquer_debuff(ActionCarte.REDUCTION_DEGATS, 100, tours=1)

    assert ennemi.degats_attaque_effectifs() == 0


def test_vulnerabilite_majore_les_degats_subis():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 100, tours=1)

    assert ennemi.degats_subis(6) == 12


def test_sans_vulnerabilite_les_degats_ne_changent_pas():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    assert ennemi.degats_subis(6) == 6


def test_decrementer_debuffs_fait_expirer_a_zero():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)
    ennemi.appliquer_debuff(ActionCarte.REDUCTION_DEGATS, 5, tours=1)
    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 100, tours=1)

    ennemi.decrementer_debuffs()

    assert ennemi.degats_attaque_effectifs() == 7
    assert ennemi.degats_subis(6) == 6
    assert ennemi.debuffs_actifs == []


def test_decrementer_debuffs_sur_plusieurs_tours():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)
    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 100, tours=2)

    ennemi.decrementer_debuffs()
    assert ennemi.degats_subis(6) == 12  # encore actif apres 1 tour

    ennemi.decrementer_debuffs()
    assert ennemi.degats_subis(6) == 6  # expire apres 2 tours


def test_deux_debuffs_du_meme_type_coexistent_et_s_additionnent():
    """Un ennemi peut porter plusieurs debuffs Vulnerabilite en meme temps : ils sont
    independants (aucune fusion ni remplacement) et leurs magnitudes s'additionnent."""
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 20, tours=1)
    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 50, tours=3)

    assert len(ennemi.debuffs_actifs) == 2
    assert ennemi.degats_subis(10) == 17  # +20% et +50% cumules : 10 * 1.70


def test_debuffs_du_meme_type_expirent_independamment():
    """Exemple exact demande : (X% pour 1 tour) + (Y% pour 3 tours) -> apres un tour
    ennemi, seul le debuff Y% (2 tours restants) doit rester actif."""
    ennemi = Ennemi(pv_max=15, degats_attaque=7)
    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 20, tours=1)
    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 50, tours=3)

    ennemi.decrementer_debuffs()

    assert len(ennemi.debuffs_actifs) == 1
    assert ennemi.debuffs_actifs[0].valeur == 50
    assert ennemi.debuffs_actifs[0].tours_restants == 2
    assert ennemi.degats_subis(10) == 15  # seul le +50% restant s'applique


def test_debuffs_de_types_differents_restent_independants():
    ennemi = Ennemi(pv_max=15, degats_attaque=7)

    ennemi.appliquer_debuff(ActionCarte.REDUCTION_DEGATS, 3, tours=1)
    ennemi.appliquer_debuff(ActionCarte.VULNERABILITE, 50, tours=1)

    assert ennemi.degats_attaque_effectifs() == 4
    assert ennemi.degats_subis(10) == 15
