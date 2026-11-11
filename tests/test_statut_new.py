"""
Tests unitaires pour src/gameplay/statut_new.py (statuts de la refonte : bouclier, incendie,
renvoi, leurre).
"""

from src.gameplay.statut_new import REGLES_STATUT, Statut, Statuts


def test_chaque_statut_a_une_regle():
    assert set(REGLES_STATUT) == set(Statut)


def test_un_statut_absent_vaut_zero():
    assert Statuts()[Statut.BOUCLIER] == 0


def test_bouclier_et_incendie_s_additionnent():
    statuts = Statuts()
    statuts.ajouter(Statut.BOUCLIER, 3)
    statuts.ajouter(Statut.BOUCLIER, 4)

    assert statuts[Statut.BOUCLIER] == 7


def test_les_renvois_s_additionnent():
    statuts = Statuts()
    statuts.ajouter(Statut.RENVOI, 5)
    statuts.ajouter(Statut.RENVOI, 3)

    assert statuts[Statut.RENVOI] == 8


def test_le_leurre_ne_se_cumule_pas():
    statuts = Statuts()
    statuts.ajouter(Statut.LEURRE, 1)
    statuts.ajouter(Statut.LEURRE, 1)

    assert statuts[Statut.LEURRE] == 1


def test_une_intensite_nulle_ne_pose_rien():
    statuts = Statuts()
    statuts.ajouter(Statut.INCENDIE, 0)

    assert statuts.intensites == {}


def test_le_bouclier_absorbe_puis_disparait_a_zero():
    statuts = Statuts({Statut.BOUCLIER: 5})

    encaissement = statuts.encaisser_attaque(7)

    assert (encaissement.degats_pv, encaissement.renvoyes, encaissement.absorbes_bouclier) == (2, 0, 5)
    assert Statut.BOUCLIER not in statuts.intensites


def test_le_leurre_annule_toute_l_attaque_avant_renvoi_et_bouclier():
    statuts = Statuts({Statut.LEURRE: 1, Statut.RENVOI: 5, Statut.BOUCLIER: 3})

    encaissement = statuts.encaisser_attaque(50)

    assert (encaissement.degats_pv, encaissement.renvoyes, encaissement.annules_leurre) == (0, 0, 50)
    assert statuts.intensites == {Statut.RENVOI: 5, Statut.BOUCLIER: 3}


def test_le_renvoi_passe_avant_le_bouclier_et_diminue():
    statuts = Statuts({Statut.RENVOI: 5, Statut.BOUCLIER: 2})

    premiere = statuts.encaisser_attaque(3)
    seconde = statuts.encaisser_attaque(6)

    assert (premiere.degats_pv, premiere.renvoyes) == (0, 3)
    assert (seconde.degats_pv, seconde.renvoyes, seconde.absorbes_bouclier) == (2, 2, 2)  # 4 non renvoyes, dont 2 absorbes
    assert statuts.intensites == {}


def test_fin_de_tour_l_incendie_frappe_a_travers_le_bouclier_puis_tout_baisse():
    statuts = Statuts({Statut.BOUCLIER: 3, Statut.INCENDIE: 4, Statut.RENVOI: 5, Statut.LEURRE: 1})

    encaissement = statuts.fin_de_tour()

    assert (encaissement.degats, encaissement.absorbes_bouclier, encaissement.degats_pv) == (4, 3, 1)
    # bouclier vide par l'incendie, incendie -1, renvoi termine, leurre intact
    assert statuts.intensites == {Statut.INCENDIE: 3, Statut.LEURRE: 1}


def test_fin_de_tour_sans_incendie_le_bouclier_baisse_de_un():
    statuts = Statuts({Statut.BOUCLIER: 3})

    assert statuts.fin_de_tour().degats_pv == 0
    assert statuts[Statut.BOUCLIER] == 2


def test_une_intensite_mise_a_zero_retire_le_statut():
    statuts = Statuts({Statut.BOUCLIER: 2})

    statuts[Statut.BOUCLIER] -= 2

    assert statuts.intensites == {}


def test_une_attaque_a_zero_degat_ne_consomme_ni_leurre_ni_renvoi():
    statuts = Statuts({Statut.LEURRE: 1, Statut.RENVOI: 5})

    encaissement = statuts.encaisser_attaque(0)

    assert (encaissement.degats_pv, encaissement.renvoyes) == (0, 0)
    assert statuts.intensites == {Statut.LEURRE: 1, Statut.RENVOI: 5}
