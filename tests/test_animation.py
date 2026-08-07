"""
Tests unitaires pour la minuterie d'animation du rayon d'attaque.
"""

from src.ui.animation import AnimationRayon


def test_animation_inactive_au_depart():
    animation = AnimationRayon()

    assert not animation.est_active()
    assert animation.progression() == 0.0


def test_demarrer_active_l_animation():
    animation = AnimationRayon()

    animation.demarrer()

    assert animation.est_active()
    assert animation.progression() == 1.0


def test_mettre_a_jour_partiel_ne_termine_pas_l_animation():
    animation = AnimationRayon()
    animation.demarrer()

    animation.mettre_a_jour(AnimationRayon.DUREE / 2)

    assert animation.est_active()
    assert 0.0 < animation.progression() < 1.0


def test_animation_se_termine_apres_sa_duree():
    animation = AnimationRayon()
    animation.demarrer()

    animation.mettre_a_jour(AnimationRayon.DUREE)

    assert not animation.est_active()
    assert animation.progression() == 0.0


def test_temps_restant_ne_descend_jamais_sous_zero():
    animation = AnimationRayon()
    animation.demarrer()

    animation.mettre_a_jour(AnimationRayon.DUREE * 10)

    assert animation.temps_restant == 0.0
