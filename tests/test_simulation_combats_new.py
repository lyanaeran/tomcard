"""
Tests du simulateur de combats de la refonte (outils/simulation/bot_new.py, combats_new.py).
"""

from outils.simulation.combats_new import Controle, construire_combat, simuler


def test_un_combat_simule_se_termine_sans_violation_et_de_facon_deterministe():
    premier = simuler("depart", ("ENM_PAT_LE_PIRATE",), 1, "recherche", "test")
    second = simuler("depart", ("ENM_PAT_LE_PIRATE",), 1, "recherche", "test")

    assert "exception" not in premier and premier["violations"] == []
    assert premier["victoire"] and premier == second


def test_le_bot_aleatoire_joue_aussi_un_combat_a_deux_ennemis():
    resultat = simuler("etoffe", ("ENM_MIROIR", "ENM_LE_PUZZLE"), 3, "aleatoire", "test")

    assert "exception" not in resultat and resultat["violations"] == []
    assert resultat["victoire"] or resultat["defaite"] or resultat["enlise"]


def test_le_controle_detecte_un_invariant_casse():
    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    controle = Controle(combat)
    combat.deck.main.append(combat.deck.pioche[0])  # carte dans deux piles

    controle.apres_action(combat)

    assert "carte presente dans deux piles" in controle.violations
