"""
Tests unitaires pour la configuration du combat du POC (src/gameplay/config_poc.py).
"""

from src.gameplay.combat import EtatCombat
from src.gameplay.config_poc import (
    DEGATS_ENNEMI,
    ELECTRICITE_PAR_TOUR,
    PV_ENNEMI,
    PV_MODULE_BASE,
    creer_combat_poc,
)


def test_creer_combat_poc_initialise_les_valeurs_du_poc():
    combat = creer_combat_poc()

    assert combat.joueur.module.pv == PV_MODULE_BASE
    assert combat.ennemi.pv == PV_ENNEMI
    assert combat.ennemi.degats_attaque == DEGATS_ENNEMI
    assert combat.etat == EtatCombat.EN_COURS


def test_creer_combat_poc_pioche_la_main_de_depart():
    combat = creer_combat_poc()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == ELECTRICITE_PAR_TOUR


def test_le_deck_du_poc_contient_les_bonnes_cartes():
    combat = creer_combat_poc()

    toutes_les_cartes = combat.joueur.deck.pioche + combat.joueur.deck.main + combat.joueur.deck.defausse
    noms = sorted(carte.nom for carte in toutes_les_cartes)

    assert noms == sorted(["Attaque"] * 5 + ["Bouclier"] * 3 + ["Soin"])
