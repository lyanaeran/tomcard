"""
Tests unitaires pour la classe Ennemi et le modele ActionEnnemi (specs.md 13).
"""

from src.gameplay.carte import ActionCarte
from src.gameplay.ennemi import ActionEnnemi, CibleActionEnnemi, Ennemi, TypeActionEnnemi


def test_ennemi_commence_a_pv_max():
    ennemi = Ennemi(pv_max=15)

    assert ennemi.pv == 15
    assert ennemi.bouclier == 0
    assert not ennemi.est_detruit()


def test_ennemi_subit_des_degats():
    ennemi = Ennemi(pv_max=15)

    ennemi.subir_degats(9)

    assert ennemi.pv == 6


def test_ennemi_detruit_a_zero_pv():
    ennemi = Ennemi(pv_max=15)

    ennemi.subir_degats(30)

    assert ennemi.pv == 0
    assert ennemi.est_detruit()


def test_bouclier_absorbe_les_degats_avant_les_pv():
    ennemi = Ennemi(pv_max=15)
    ennemi.ajouter_bouclier(5)

    ennemi.subir_degats(7)

    assert ennemi.bouclier == 0
    assert ennemi.pv == 13  # 7 - 5 de bouclier absorbe = 2 degats restants


def test_reduction_degats_diminue_les_degats_infliges():
    ennemi = Ennemi(pv_max=15)

    ennemi.appliquer_buff(ActionCarte.REDUCTION_DEGATS, 5, tours=1)

    assert ennemi.degats_attaque_effectifs(7) == 2


def test_reduction_degats_ne_descend_jamais_sous_zero():
    ennemi = Ennemi(pv_max=15)

    ennemi.appliquer_buff(ActionCarte.REDUCTION_DEGATS, 100, tours=1)

    assert ennemi.degats_attaque_effectifs(7) == 0


def test_vulnerabilite_majore_les_degats_subis():
    ennemi = Ennemi(pv_max=15)

    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 100, tours=1)

    assert ennemi.degats_subis(6) == 12


def test_sans_vulnerabilite_les_degats_ne_changent_pas():
    ennemi = Ennemi(pv_max=15)

    assert ennemi.degats_subis(6) == 6


def test_bouclier_par_tour_ajoute_du_bouclier_immediatement():
    """Contrairement a Module.declencher_buffs_tour, ce buff ne se redeclenche jamais tout
    seul cote ennemi (specs.md 13) : seul l'ajout immediat a la pose est teste ici."""
    ennemi = Ennemi(pv_max=15)

    ennemi.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 3, tours=2)

    assert ennemi.bouclier == 3
    assert len(ennemi.buffs_actifs) == 1


def test_decrementer_buffs_fait_expirer_a_zero():
    ennemi = Ennemi(pv_max=15)
    ennemi.appliquer_buff(ActionCarte.REDUCTION_DEGATS, 5, tours=1)
    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 100, tours=1)

    ennemi.decrementer_buffs()

    assert ennemi.degats_attaque_effectifs(7) == 7
    assert ennemi.degats_subis(6) == 6
    assert ennemi.buffs_actifs == []


def test_decrementer_buffs_sur_plusieurs_tours():
    ennemi = Ennemi(pv_max=15)
    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 100, tours=2)

    ennemi.decrementer_buffs()
    assert ennemi.degats_subis(6) == 12  # encore actif apres 1 tour

    ennemi.decrementer_buffs()
    assert ennemi.degats_subis(6) == 6  # expire apres 2 tours


def test_buff_persistant_ne_decompte_jamais():
    ennemi = Ennemi(pv_max=15)
    ennemi.appliquer_buff(ActionCarte.BOUCLIER_PAR_TOUR, 3, tours=None)

    for _ in range(5):
        ennemi.decrementer_buffs()

    assert len(ennemi.buffs_actifs) == 1
    assert ennemi.buffs_actifs[0].tours_restants is None


def test_deux_buffs_du_meme_type_coexistent_et_s_additionnent():
    """Un ennemi peut porter plusieurs debuffs Vulnerabilite en meme temps : ils sont
    independants (aucune fusion ni remplacement) et leurs magnitudes s'additionnent."""
    ennemi = Ennemi(pv_max=15)

    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 20, tours=1)
    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 50, tours=3)

    assert len(ennemi.buffs_actifs) == 2
    assert ennemi.degats_subis(10) == 17  # +20% et +50% cumules : 10 * 1.70


def test_buffs_du_meme_type_expirent_independamment():
    """Exemple exact demande : (X% pour 1 tour) + (Y% pour 3 tours) -> apres un tour
    ennemi, seul le debuff Y% (2 tours restants) doit rester actif."""
    ennemi = Ennemi(pv_max=15)
    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 20, tours=1)
    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 50, tours=3)

    ennemi.decrementer_buffs()

    assert len(ennemi.buffs_actifs) == 1
    assert ennemi.buffs_actifs[0].valeur == 50
    assert ennemi.buffs_actifs[0].tours_restants == 2
    assert ennemi.degats_subis(10) == 15  # seul le +50% restant s'applique


def test_buffs_de_types_differents_restent_independants():
    ennemi = Ennemi(pv_max=15)

    ennemi.appliquer_buff(ActionCarte.REDUCTION_DEGATS, 3, tours=1)
    ennemi.appliquer_buff(ActionCarte.VULNERABILITE, 50, tours=1)

    assert ennemi.degats_attaque_effectifs(7) == 4
    assert ennemi.degats_subis(10) == 15


def test_active_au_tour_frequence_un_se_declenche_tous_les_tours():
    action = ActionEnnemi(type=TypeActionEnnemi.ATTAQUE, cible=CibleActionEnnemi.PROXIMITE, valeur=5)

    assert [action.active_au_tour(t) for t in range(1, 5)] == [True, True, True, True]


def test_active_au_tour_respecte_la_frequence_et_le_tour_de_depart():
    """tour_depart=1, frequence=3 -> actif aux tours 1, 4, 7..."""
    action = ActionEnnemi(
        type=TypeActionEnnemi.POSE_BUFF, cible=CibleActionEnnemi.SOI_MEME, valeur=3, frequence=3, tour_depart=1
    )

    resultats = [action.active_au_tour(t) for t in range(1, 8)]

    assert resultats == [True, False, False, True, False, False, True]


def test_active_au_tour_avec_tour_de_depart_different_de_un():
    """tour_depart=2 : rien au tour 1, puis actif tous les `frequence` tours a partir de 2."""
    action = ActionEnnemi(
        type=TypeActionEnnemi.ATTAQUE, cible=CibleActionEnnemi.PROXIMITE, valeur=5, frequence=2, tour_depart=2
    )

    resultats = [action.active_au_tour(t) for t in range(1, 6)]

    assert resultats == [False, True, False, True, False]
