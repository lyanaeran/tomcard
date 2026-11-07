"""
Tests du simulateur d'equilibrage (outils/simulation/, specs/simulation.md).
"""

import random

from outils.simulation.bot import BotRecherche, cible_depuis_reference, jouer_combat, reference_cible
from outils.simulation.partie_auto import choisir_etape
from src.gameplay import deroulement
from src.gameplay.combat import EtatCombat
from src.gameplay.donnees import charger_modules
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import combat_depuis_partie, nouvelle_partie


def _combat_niveau_2(graine: int):
    partie = nouvelle_partie(random.Random(graine))
    spec = next(spec for spec in charger_modules() if spec.id == "MOD_2")
    deroulement.choisir_module(partie, spec, random.Random(graine))
    deroulement.resoudre_carte_module(partie, None)
    return combat_depuis_partie(partie, random.Random(graine))


def test_reference_de_cible_retrouve_la_meme_cible_dans_le_combat():
    combat = _combat_niveau_2(1)
    for cible in [combat.joueur.vaisseau.base, *combat.flotte.ennemis_vivants(), None]:
        assert cible_depuis_reference(combat, reference_cible(combat, cible)) is cible


def test_le_bot_de_recherche_termine_un_combat_de_niveau_2_de_facon_deterministe():
    stats = [jouer_combat(_combat_niveau_2(3), BotRecherche(random.Random(3))) for _ in range(2)]

    assert stats[0] == stats[1]
    assert stats[0]["victoire"]
    assert sum(stats[0]["cartes_jouees"].values()) > 0


def test_le_bot_ne_modifie_pas_le_combat_reel_en_cherchant():
    combat = _combat_niveau_2(4)
    pv_avant = [ennemi.pv for ennemi in combat.flotte.ennemis_vivants()]
    main_avant = list(combat.joueur.deck.main)

    BotRecherche(random.Random(4)).choisir_sequence(combat)

    assert [ennemi.pv for ennemi in combat.flotte.ennemis_vivants()] == pv_avant
    assert combat.joueur.deck.main == main_avant
    assert combat.etat == EtatCombat.EN_COURS


def test_politique_par_defaut_va_en_station_si_le_principal_est_bas_et_l_argent_suffit():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = 50
    propositions = [TypeEtape.PRIME, TypeEtape.STATION_SERVICE]

    assert choisir_etape(partie, propositions) == TypeEtape.PRIME
    partie.vaisseau["base"].pv = 5
    assert choisir_etape(partie, propositions) == TypeEtape.STATION_SERVICE
