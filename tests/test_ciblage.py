"""
Tests unitaires pour le ciblage automatique des ennemis (src/gameplay/ciblage.py).

La rangee (ligne) est le critere principal, avant/arriere le critere secondaire.
"""

from src.gameplay.ciblage import module_cible_par_ennemi
from src.gameplay.module import Module
from src.gameplay.position import Rangee
from src.gameplay.vaisseau import Vaisseau


def test_cible_l_avant_de_la_propre_rangee_en_priorite():
    avant = Module(pv_max=12)
    arriere = Module(pv_max=10)
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=avant, arriere_gauche=arriere)

    cible = module_cible_par_ennemi(vaisseau, Rangee.GAUCHE)

    assert cible is avant


def test_repli_sur_l_arriere_de_la_meme_rangee_si_l_avant_est_vide():
    # Cas corrige suite au retour utilisateur : la base (Mid) ne doit PAS etre
    # ciblee ici, meme si elle est vivante - l'arriere de la propre rangee prime.
    arriere = Module(pv_max=10)
    vaisseau = Vaisseau(base=Module(pv_max=15), arriere_gauche=arriere)

    cible = module_cible_par_ennemi(vaisseau, Rangee.GAUCHE)

    assert cible is arriere


def test_repli_sur_l_arriere_de_la_meme_rangee_si_l_avant_est_detruit():
    avant = Module(pv_max=12)
    arriere = Module(pv_max=10)
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=avant, arriere_gauche=arriere)
    avant.subir_degats(100)

    cible = module_cible_par_ennemi(vaisseau, Rangee.GAUCHE)

    assert cible is arriere


def test_rangee_mid_cible_toujours_la_base():
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=Module(pv_max=12))

    cible = module_cible_par_ennemi(vaisseau, Rangee.MID)

    assert cible is vaisseau.base


def test_repli_sur_la_rangee_la_plus_proche_si_la_propre_rangee_est_vide():
    # Rangee Gauche entierement vide -> repli sur Mid (la plus proche), donc la base.
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_droite=Module(pv_max=18))

    cible = module_cible_par_ennemi(vaisseau, Rangee.GAUCHE)

    assert cible is vaisseau.base


def test_repli_au_dela_de_mid_si_tout_est_detruit_jusque_la():
    droite = Module(pv_max=18)
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_droite=droite)
    vaisseau.base.subir_degats(100)

    cible = module_cible_par_ennemi(vaisseau, Rangee.GAUCHE)

    assert cible is droite


def test_aucune_cible_si_tout_est_detruit():
    avant_gauche = Module(pv_max=12)
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=avant_gauche)
    vaisseau.base.subir_degats(100)
    avant_gauche.subir_degats(100)

    cible = module_cible_par_ennemi(vaisseau, Rangee.GAUCHE)

    assert cible is None
