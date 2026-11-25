"""
Tests du simulateur de combats de la refonte (outils/simulation/bot.py, combats.py).
"""

from outils.simulation.combats import Controle, construire_combat, simuler


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


def test_valeur_d_un_lancement_d_une_carte_de_ligne_ne_compte_que_sa_ligne():
    from outils.simulation.bot import valeur_d_un_lancement
    from src.gameplay.carte import charger_cartes

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE", "ENM_LE_NETTOYEUR"), 1)  # un avant, un arriere
    cartes = charger_cartes()

    def degats(id_carte):
        return cartes[id_carte].valeurs["degats"]

    # Laser percant (une ligne) touche 1 ennemi, comme Laser lourd ; Ogive legere (tous) en touche 2
    assert valeur_d_un_lancement(cartes["CRT_8"], combat) == (
        valeur_d_un_lancement(cartes["CRT_47"], combat) * degats("CRT_8") / degats("CRT_47")
    )
    assert valeur_d_un_lancement(cartes["CRT_9"], combat) == (
        2 * valeur_d_un_lancement(cartes["CRT_7"], combat) * degats("CRT_9") / degats("CRT_7")
    )


def test_valeur_d_un_lancement_sur_tous_les_modules_compte_chaque_module_vivant():
    from outils.simulation.bot import valeur_d_un_lancement
    from src.gameplay.carte import Carte, CategorieCarte, CibleCarte, Effet, NatureEffet, RareteCarte

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    bouclier_de_zone = Carte(
        id="TEST", nom="Bouclier de zone", image="", rarete=RareteCarte.COMMUNE, categorie=CategorieCarte.DEFENSE,
        cible=CibleCarte.MODULE_TOUS, cout=1, valeurs={"bouclier": 4}, effets=(Effet(NatureEffet.BOUCLIER, "bouclier"),),
    )

    assert valeur_d_un_lancement(bouclier_de_zone, combat) == 2 * 4 * 1.0  # principal + Lanceur


def test_la_recherche_du_bot_ne_connait_pas_les_vrais_melanges():
    import random

    from outils.simulation.bot import BotRecherche

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    copie = BotRecherche(random.Random(7))._copie_reensemencee(combat)

    assert copie.deck.aleatoire is copie.aleatoire
    assert copie.deck.aleatoire.getstate() != combat.deck.aleatoire.getstate()


def test_valeur_du_retrait_de_bouclier_et_du_renvoi():
    from outils.simulation.bot import RENVOI_MODULES_ATTAQUES, valeur_d_un_lancement
    from src.gameplay.carte import charger_cartes
    from src.gameplay.statut import Statut

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    cartes = charger_cartes()
    laser_disrupteur, bouclier_miroir = cartes["CRT_100"], cartes["CRT_102"]

    # Sans bouclier ennemi, le retrait ne vaut rien ; avec, il vaut des degats
    sans_bouclier = valeur_d_un_lancement(laser_disrupteur, combat)
    combat.flotte.ennemis_vivants()[0].statuts.ajouter(Statut.BOUCLIER, 50)
    assert valeur_d_un_lancement(laser_disrupteur, combat) > sans_bouclier
    # Le renvoi sur tous les modules ne compte que les modules attaques en general
    renvoi = bouclier_miroir.valeurs["renvoi"]
    modules = min(RENVOI_MODULES_ATTAQUES, len(combat.vaisseau.modules_vivants()))
    assert valeur_d_un_lancement(bouclier_miroir, combat) == renvoi * modules



def test_valeur_de_la_surcharge_plafonnee_et_gain_a_partir_de_l_existant():
    from outils.simulation.bot import degats_a_venir_de_la_surcharge, valeur_d_un_lancement
    from src.gameplay.carte import charger_cartes
    from src.gameplay.statut import Statut

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    pv_ennemis = sum(ennemi.pv for ennemi in combat.flotte.ennemis_vivants())
    # Plafond : jamais plus que les PV des ennemis vivants, meme figee et tres haute
    assert degats_a_venir_de_la_surcharge(combat, 24, True) == pv_ennemis
    assert degats_a_venir_de_la_surcharge(combat, 2, False) < pv_ennemis

    # Amplificateur ne vaut rien sans Surcharge, et quelque chose avec
    amplificateur = charger_cartes()["CRT_68"]
    assert valeur_d_un_lancement(amplificateur, combat) == 0
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 2)
    assert valeur_d_un_lancement(amplificateur, combat) > 0


def test_valeur_du_verrouillage_plafonnee_et_bonus_lu_sur_les_ennemis():
    from outils.simulation.bot import degats_a_venir_du_verrouillage, evaluer, valeur_d_un_lancement
    from src.gameplay.carte import charger_cartes
    from src.gameplay.statut import Statut

    combat = construire_combat("depart", ("ENM_PAT_LE_PIRATE",), 1)
    (pat,) = combat.flotte.ennemis_vivants()
    # Plafond : jamais plus que les PV de l'ennemi
    assert degats_a_venir_du_verrouillage(pat, 50) == pat.pv
    assert 0 < degats_a_venir_du_verrouillage(pat, 2) < pat.pv

    cartes = charger_cartes()
    assert valeur_d_un_lancement(cartes["CRT_106"], combat) > 0
    sans = valeur_d_un_lancement(cartes["CRT_74"], combat)
    note = evaluer(combat)
    pat.statuts.ajouter(Statut.VERROUILLAGE, 3)
    # Un ennemi verrouille vaut mieux pour le joueur, et Missile de precision en profite
    assert evaluer(combat) > note
    assert valeur_d_un_lancement(cartes["CRT_74"], combat) > sans
