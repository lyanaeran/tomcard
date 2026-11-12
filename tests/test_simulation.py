"""
Tests du simulateur de parties completes (outils/simulation/partie_auto.py, etudes.py,
specs/simulation.md), branche sur le combat de la refonte (bot_new.py).
"""

import random

from outils.simulation.bot_new import BotRecherche, jouer_combat
from outils.simulation.partie_auto import _aventure_asteroides, _aventure_police, choisir_etape, jouer_partie
from src.gameplay import deroulement
from src.gameplay.combat_new import EtatCombatNew
from src.gameplay.module_new import charger_modules_new
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import DEGATS_ASTEROIDES, combat_depuis_partie, nouvelle_partie


def _combat_niveau_2(graine: int):
    partie = nouvelle_partie(random.Random(graine))
    deroulement.choisir_module(partie, charger_modules_new()["MOD_2"], random.Random(graine))
    deroulement.resoudre_carte_module(partie, None)
    return combat_depuis_partie(partie, random.Random(graine))


def test_le_bot_de_recherche_termine_un_combat_de_niveau_2_de_facon_deterministe():
    stats = [jouer_combat(_combat_niveau_2(3), BotRecherche(random.Random(3))) for _ in range(2)]

    assert stats[0] == stats[1]
    assert stats[0]["victoire"]
    assert sum(stats[0]["cartes_jouees"].values()) > 0


def test_le_bot_ne_modifie_pas_le_combat_reel_en_cherchant():
    combat = _combat_niveau_2(4)
    pv_avant = [ennemi.pv for ennemi in combat.flotte.ennemis_vivants()]
    main_avant = list(combat.deck.main)

    BotRecherche(random.Random(4)).choisir_sequence(combat)

    assert [ennemi.pv for ennemi in combat.flotte.ennemis_vivants()] == pv_avant
    assert combat.deck.main == main_avant
    assert combat.etat == EtatCombatNew.EN_COURS


def test_politique_par_defaut_va_en_station_si_le_principal_est_bas_et_l_argent_suffit():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = 50
    propositions = [TypeEtape.PRIME, TypeEtape.STATION_SERVICE]

    assert choisir_etape(partie, propositions) == TypeEtape.PRIME
    partie.vaisseau["base"].pv = 5
    assert choisir_etape(partie, propositions) == TypeEtape.STATION_SERVICE


def test_une_partie_complete_se_joue_jusqu_au_bout():
    resultat = jouer_partie(2, module_force="MOD_2")

    assert resultat.niveau_atteint == 10
    assert resultat.combats and all("ennemis" in combat for combat in resultat.combats)
    assert len(resultat.deck_fin) > 10


def test_politique_des_aventures_asteroides_et_police():
    partie = nouvelle_partie(random.Random(1))
    deroulement.choisir_module(partie, charger_modules_new()["MOD_2"], random.Random(1))
    taille_deck, pv = len(partie.deck), partie.principal.pv

    _aventure_asteroides(partie)
    assert partie.principal.pv == pv - 2 * DEGATS_ASTEROIDES
    assert len(partie.deck) == taille_deck + 1

    partie.argent = 0
    _aventure_police(partie)
    assert len(partie.deck) == taille_deck
