"""
Tests unitaires pour la classe Deck.
"""

import random

from src.gameplay.carte import Carte, CibleCarte, TypeCarte
from src.gameplay.deck import Deck

CARTE_ATTAQUE = Carte(nom="Attaque", image="test.png", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=7)
CARTE_BOUCLIER = Carte(nom="Bouclier", image="test.png", type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE_UNIQUE, cout=1, valeur=5)
CARTE_REPARATION = Carte(nom="Soin", image="test.png", type=TypeCarte.REPARATION, cible=CibleCarte.ALLIE_UNIQUE, cout=1, valeur=4)


def _deck_poc() -> Deck:
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_REPARATION]
    return Deck(cartes=cartes, generateur_aleatoire=random.Random(0))


def test_deck_commence_avec_une_main_vide():
    deck = _deck_poc()

    assert deck.main == []
    assert len(deck.pioche) == 9
    assert deck.defausse == []


def test_piocher_debut_de_tour_pioche_cinq_cartes():
    deck = _deck_poc()

    deck.piocher_debut_de_tour()

    assert len(deck.main) == 5
    assert len(deck.pioche) == 4


def test_jouer_une_carte_l_envoie_en_defausse():
    deck = _deck_poc()
    deck.piocher_debut_de_tour()
    carte = deck.main[0]

    deck.jouer(carte)

    assert carte not in deck.main
    assert deck.defausse == [carte]


def test_la_defausse_est_remelangee_quand_la_pioche_est_vide():
    deck = _deck_poc()
    deck.piocher_debut_de_tour()  # 5 en main, 4 en pioche
    for carte in list(deck.main):
        deck.jouer(carte)  # 9 en defausse, pioche vide

    deck.piocher_debut_de_tour()  # doit remelanger la defausse pour pouvoir piocher

    assert len(deck.main) == 5
    assert len(deck.pioche) + len(deck.main) + len(deck.defausse) == 9


def test_defausser_main_vide_la_main():
    deck = _deck_poc()
    deck.piocher_debut_de_tour()

    deck.defausser_main()

    assert deck.main == []
    assert len(deck.defausse) == 5


def test_la_main_ne_depasse_jamais_la_capacite_maximale():
    deck = _deck_poc()
    deck.TAILLE_MAIN_MAX = 3  # capacite reduite pour rendre le test rapide

    deck.piocher_debut_de_tour()

    assert len(deck.main) == 3
