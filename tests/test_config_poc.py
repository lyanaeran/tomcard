"""
Tests unitaires pour la configuration du combat du POC (src/gameplay/config_poc.py).
"""

from collections import Counter

from src.gameplay.combat import EtatCombat
from src.gameplay.config_poc import (
    ELECTRICITE_PAR_TOUR,
    KIT_ARRIERE_DROITE,
    KIT_ARRIERE_GAUCHE,
    KIT_AVANT_DROITE,
    KIT_AVANT_GAUCHE,
    PV_ARRIERE_DROITE,
    PV_ARRIERE_GAUCHE,
    PV_AVANT_DROITE,
    PV_AVANT_GAUCHE,
    PV_BASE,
    creer_combat_poc,
)
from src.gameplay.carte import CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN


def test_creer_combat_poc_initialise_le_vaisseau():
    combat = creer_combat_poc()
    vaisseau = combat.joueur.vaisseau

    assert vaisseau.base.pv == PV_BASE
    assert vaisseau.base.pv_max == PV_BASE
    equipes = vaisseau.modules_equipes()
    assert len(equipes) == 4
    pv_equipes = sorted(module.pv_max for module in equipes.values())
    assert pv_equipes == sorted([PV_AVANT_GAUCHE, PV_AVANT_DROITE, PV_ARRIERE_GAUCHE, PV_ARRIERE_DROITE])


def test_creer_combat_poc_initialise_la_flotte():
    combat = creer_combat_poc()

    ennemis = combat.flotte.ennemis_vivants()

    assert len(ennemis) == 4
    assert combat.etat == EtatCombat.EN_COURS


def test_creer_combat_poc_pioche_la_main_de_depart():
    combat = creer_combat_poc()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == ELECTRICITE_PAR_TOUR


def test_le_deck_du_poc_contient_45_cartes_reparties_par_kit():
    combat = creer_combat_poc()

    toutes_les_cartes = combat.joueur.deck.pioche + combat.joueur.deck.main + combat.joueur.deck.defausse
    assert len(toutes_les_cartes) == 45

    compte = Counter(carte.nom for carte in toutes_les_cartes)
    for attaque, bouclier, soin in (
        (CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN),
        KIT_AVANT_GAUCHE,
        KIT_AVANT_DROITE,
        KIT_ARRIERE_GAUCHE,
        KIT_ARRIERE_DROITE,
    ):
        assert compte[attaque.nom] == 5
        assert compte[bouclier.nom] == 3
        assert compte[soin.nom] == 1


def test_deux_combats_successifs_ont_des_ennemis_independants():
    combat_1 = creer_combat_poc()
    combat_2 = creer_combat_poc()

    combat_1.flotte.ennemis_vivants()[0].subir_degats(1000)

    assert combat_2.flotte.ennemis_vivants()[0].pv > 0
