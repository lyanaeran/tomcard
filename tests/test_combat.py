"""
Tests unitaires pour le moteur de combat (src/gameplay/combat.py).
"""

import random

from src.gameplay.carte import CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN, CibleCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.deck import Deck
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

POSITION_ENNEMI = Position(Colonne.AVANT, Rangee.GAUCHE)


def _nouveau_combat(pv_base: int = 15, pv_ennemi: int = 15, degats_ennemi: int = 7, ennemis: dict | None = None):
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_SOIN]
    deck = Deck(cartes=cartes, generateur_aleatoire=random.Random(0))
    vaisseau = Vaisseau(base=Module(pv_max=pv_base))
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=3)
    if ennemis is None:
        ennemis = {POSITION_ENNEMI: Ennemi(pv_max=pv_ennemi, degats_attaque=degats_ennemi)}
    flotte = Flotte(ennemis)
    combat = Combat(joueur=joueur, flotte=flotte)
    return combat, vaisseau, flotte


def _cible_valide_pour(combat: Combat, carte) -> Module | Ennemi:
    """Aide de test : cible valide pour cette carte, peu importe laquelle exactement."""
    if carte.cible == CibleCarte.ENNEMI:
        return combat.flotte.ennemis_vivants()[0]
    return combat.joueur.vaisseau.base


def test_debut_de_combat_pioche_la_main_et_recharge_l_electricite():
    combat, _vaisseau, _flotte = _nouveau_combat()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == 3
    assert combat.etat == EtatCombat.EN_COURS


def test_jouer_une_carte_attaque_inflige_des_degats_a_l_ennemi():
    combat, _vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert ennemi.pv == 15 - CARTE_ATTAQUE.valeur
    assert combat.joueur.electricite == 3 - CARTE_ATTAQUE.cout


def test_jouer_une_carte_bouclier_protege_le_module_choisi():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BOUCLIER]

    combat.jouer_carte(CARTE_BOUCLIER, vaisseau.base)

    assert vaisseau.base.bouclier == CARTE_BOUCLIER.valeur


def test_jouer_une_carte_soin_repare_le_module_choisi():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_SOIN]
    vaisseau.base.subir_degats(10)

    combat.jouer_carte(CARTE_SOIN, vaisseau.base)

    assert vaisseau.base.pv == 15 - 10 + CARTE_SOIN.valeur


def test_impossible_de_jouer_une_carte_sans_assez_d_electricite():
    combat, _vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]
    combat.joueur.electricite = 0

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert ennemi.pv == 15


def test_impossible_de_jouer_une_carte_avec_une_cible_du_mauvais_type():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, vaisseau.base)  # Attaque cible un ennemi, pas un module

    assert vaisseau.base.pv == 15  # rien ne s'est passe


def test_impossible_de_cibler_un_ennemi_deja_detruit():
    combat, _vaisseau, flotte = _nouveau_combat(pv_ennemi=1)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE, CARTE_ATTAQUE]
    combat.jouer_carte(CARTE_ATTAQUE, ennemi)  # detruit l'ennemi -> victoire, combat termine

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)  # no-op : combat deja termine

    assert combat.etat == EtatCombat.VICTOIRE


def test_finir_tour_joueur_declenche_l_attaque_ennemie():
    combat, vaisseau, _flotte = _nouveau_combat()

    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 7


def test_finir_tour_joueur_pioche_une_nouvelle_main():
    combat, _vaisseau, _flotte = _nouveau_combat()
    premiere_carte = combat.joueur.deck.main[0]
    combat.jouer_carte(premiere_carte, _cible_valide_pour(combat, premiere_carte))

    combat.finir_tour_joueur()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == 3


def test_victoire_quand_l_ennemi_est_detruit():
    combat, _vaisseau, flotte = _nouveau_combat(pv_ennemi=7)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert combat.etat == EtatCombat.VICTOIRE


def test_pas_de_victoire_tant_qu_un_ennemi_survit():
    e1 = Ennemi(pv_max=7, degats_attaque=4)
    e2 = Ennemi(pv_max=7, degats_attaque=4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e1,
        Position(Colonne.AVANT, Rangee.DROITE): e2,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, e1)

    assert combat.etat == EtatCombat.EN_COURS


def test_victoire_seulement_quand_tous_les_ennemis_sont_detruits():
    e1 = Ennemi(pv_max=7, degats_attaque=4)
    e2 = Ennemi(pv_max=7, degats_attaque=4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e1,
        Position(Colonne.AVANT, Rangee.DROITE): e2,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE, CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, e1)
    combat.jouer_carte(CARTE_ATTAQUE, e2)

    assert combat.etat == EtatCombat.VICTOIRE


def test_defaite_quand_le_module_de_base_est_detruit():
    combat, _vaisseau, _flotte = _nouveau_combat(pv_base=5)

    combat.finir_tour_joueur()

    assert combat.etat == EtatCombat.DEFAITE


def test_defaite_independante_de_la_destruction_d_un_module_non_base():
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_SOIN]
    deck = Deck(cartes=cartes, generateur_aleatoire=random.Random(0))
    module_fragile = Module(pv_max=1)
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=module_fragile)
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=3)
    flotte = Flotte({POSITION_ENNEMI: Ennemi(pv_max=15, degats_attaque=7)})
    combat = Combat(joueur=joueur, flotte=flotte)

    module_fragile.subir_degats(100)  # detruit un module non-base, hors du moteur de combat
    combat.finir_tour_joueur()  # declenche la verification de fin de combat

    assert module_fragile.est_detruit()
    assert combat.etat == EtatCombat.EN_COURS  # la base (15 - 7 = 8 PV) est toujours en vie


def test_finir_tour_joueur_renvoie_les_attaques_resolues():
    combat, vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]

    attaques = combat.finir_tour_joueur()

    assert attaques == [(POSITION_ENNEMI, ennemi, vaisseau.base)]


def test_plusieurs_ennemis_attaquent_dans_le_meme_tour():
    e1 = Ennemi(pv_max=15, degats_attaque=4)
    e2 = Ennemi(pv_max=15, degats_attaque=6)
    position_e1 = Position(Colonne.AVANT, Rangee.GAUCHE)
    position_e2 = Position(Colonne.AVANT, Rangee.DROITE)
    combat, vaisseau, _flotte = _nouveau_combat(ennemis={position_e1: e1, position_e2: e2})

    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 4 - 6


def test_arret_immediat_si_la_base_est_detruite_en_cours_de_tour():
    e1 = Ennemi(pv_max=15, degats_attaque=20)  # detruit la base d'un coup
    e2 = Ennemi(pv_max=15, degats_attaque=5)
    position_e1 = Position(Colonne.AVANT, Rangee.GAUCHE)
    position_e2 = Position(Colonne.AVANT, Rangee.DROITE)
    combat, vaisseau, _flotte = _nouveau_combat(pv_base=10, ennemis={position_e1: e1, position_e2: e2})

    attaques = combat.finir_tour_joueur()

    assert combat.etat == EtatCombat.DEFAITE
    assert attaques == [(position_e1, e1, vaisseau.base)]  # e2 n'a pas agi
