"""
Tests unitaires pour le moteur de combat (src/gameplay/combat.py).
"""

import random

from src.gameplay.carte import CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.deck import Deck
from src.gameplay.ennemi import Ennemi
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module


def _nouveau_combat(pv_module: int = 15, pv_ennemi: int = 15, degats_ennemi: int = 7) -> Combat:
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_SOIN]
    deck = Deck(cartes=cartes, generateur_aleatoire=random.Random(0))
    joueur = Joueur(module=Module(pv_max=pv_module), deck=deck, electricite_par_tour=3)
    ennemi = Ennemi(pv_max=pv_ennemi, degats_attaque=degats_ennemi)
    return Combat(joueur=joueur, ennemi=ennemi)


def test_debut_de_combat_pioche_la_main_et_recharge_l_electricite():
    combat = _nouveau_combat()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == 3
    assert combat.etat == EtatCombat.EN_COURS


def test_jouer_une_carte_attaque_inflige_des_degats_a_l_ennemi():
    combat = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE)

    assert combat.ennemi.pv == 15 - CARTE_ATTAQUE.valeur
    assert combat.joueur.electricite == 3 - CARTE_ATTAQUE.cout


def test_jouer_une_carte_bouclier_protege_le_module():
    combat = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BOUCLIER]

    combat.jouer_carte(CARTE_BOUCLIER)

    assert combat.joueur.module.bouclier == CARTE_BOUCLIER.valeur


def test_jouer_une_carte_soin_repare_le_module():
    combat = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_SOIN]
    combat.joueur.module.subir_degats(10)

    combat.jouer_carte(CARTE_SOIN)

    assert combat.joueur.module.pv == 15 - 10 + CARTE_SOIN.valeur


def test_impossible_de_jouer_une_carte_sans_assez_d_electricite():
    combat = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_ATTAQUE]
    combat.joueur.electricite = 0

    combat.jouer_carte(CARTE_ATTAQUE)

    assert combat.ennemi.pv == 15


def test_impossible_de_jouer_une_carte_absente_de_la_main():
    combat = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BOUCLIER]

    combat.jouer_carte(CARTE_ATTAQUE)

    assert combat.ennemi.pv == 15


def test_finir_tour_joueur_declenche_l_attaque_ennemie():
    combat = _nouveau_combat()

    combat.finir_tour_joueur()

    assert combat.joueur.module.pv == 15 - 7


def test_finir_tour_joueur_pioche_une_nouvelle_main():
    combat = _nouveau_combat()
    combat.jouer_carte(combat.joueur.deck.main[0])

    combat.finir_tour_joueur()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == 3


def test_victoire_quand_l_ennemi_est_detruit():
    combat = _nouveau_combat(pv_ennemi=7)
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE)

    assert combat.etat == EtatCombat.VICTOIRE


def test_defaite_quand_le_module_de_base_est_detruit():
    combat = _nouveau_combat(pv_module=5)

    combat.finir_tour_joueur()

    assert combat.etat == EtatCombat.DEFAITE


def test_plus_aucune_action_possible_apres_la_fin_du_combat():
    combat = _nouveau_combat(pv_ennemi=7)
    combat.joueur.deck.main = [CARTE_ATTAQUE, CARTE_BOUCLIER]

    combat.jouer_carte(CARTE_ATTAQUE)  # met fin au combat (victoire)
    combat.jouer_carte(CARTE_BOUCLIER)
    combat.finir_tour_joueur()

    assert combat.joueur.module.bouclier == 0
    assert combat.etat == EtatCombat.VICTOIRE
