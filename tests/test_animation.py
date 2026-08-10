"""
Tests unitaires pour la minuterie d'animation des popups +/-.
"""

from src.ui.animation import AnimationPopup


def test_animation_inactive_au_depart():
    animation = AnimationPopup()

    assert not animation.est_active()


def test_demarrer_active_l_animation():
    animation = AnimationPopup()

    animation.demarrer()

    assert animation.est_active()


def test_mettre_a_jour_partiel_ne_termine_pas_l_animation():
    animation = AnimationPopup()
    animation.demarrer()

    animation.mettre_a_jour(AnimationPopup.DUREE / 2)

    assert animation.est_active()


def test_animation_se_termine_apres_sa_duree():
    animation = AnimationPopup()
    animation.demarrer()

    animation.mettre_a_jour(AnimationPopup.DUREE)

    assert not animation.est_active()


def test_temps_restant_ne_descend_jamais_sous_zero():
    animation = AnimationPopup()
    animation.demarrer()

    animation.mettre_a_jour(AnimationPopup.DUREE * 10)

    assert animation.temps_restant == 0.0
