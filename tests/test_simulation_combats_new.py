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


def test_valeur_d_un_lancement_d_une_carte_de_colonne_ne_compte_que_sa_colonne():
    from outils.simulation.bot_new import valeur_d_un_lancement
    from src.gameplay.carte_new import charger_cartes_new

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE", "ENM_LE_NETTOYEUR"), 1)  # un avant, un arriere
    cartes = charger_cartes_new()

    assert valeur_d_un_lancement(cartes["CRT_8"], combat) == valeur_d_un_lancement(cartes["CRT_47"], combat) * 8 / 12
    assert valeur_d_un_lancement(cartes["CRT_9"], combat) == 2 * valeur_d_un_lancement(cartes["CRT_7"], combat)


def test_valeur_d_un_lancement_sur_tous_les_modules_compte_chaque_module_vivant():
    from outils.simulation.bot_new import valeur_d_un_lancement
    from src.gameplay.carte_new import CarteNew, CategorieCarte, CibleCarteNew, Effet, NatureEffet, RareteCarte

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    bouclier_de_zone = CarteNew(
        id="TEST", nom="Bouclier de zone", image="", rarete=RareteCarte.COMMUNE, categorie=CategorieCarte.DEFENSE,
        cible=CibleCarteNew.MODULE_TOUS, cout=1, valeurs={"bouclier": 4}, effets=(Effet(NatureEffet.BOUCLIER, "bouclier"),),
    )

    assert valeur_d_un_lancement(bouclier_de_zone, combat) == 2 * 4 * 1.0  # principal + Lanceur


def test_la_recherche_du_bot_ne_connait_pas_les_vrais_melanges():
    import random

    from outils.simulation.bot_new import BotRecherche

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    copie = BotRecherche(random.Random(7))._copie_reensemencee(combat)

    assert copie.deck.aleatoire is copie.aleatoire
    assert copie.deck.aleatoire.getstate() != combat.deck.aleatoire.getstate()
