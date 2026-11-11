"""
Tests unitaires pour src/gameplay/deck_new.py (piles de cartes d'un combat de la refonte).
"""

import random

import pytest

from src.gameplay.carte_new import charger_cartes_new
from src.gameplay.deck_new import TAILLE_MAIN_MAX, DeckNew, deck_de_depart


def _cartes(id_carte, nombre, module="M1"):
    modele = charger_cartes_new()[id_carte]
    return [modele.copie(exemplaire_module=module) for _ in range(nombre)]


def test_deck_de_depart_dix_cartes_rattachees_au_principal():
    deck = deck_de_depart(charger_cartes_new(), "M1")

    assert sorted(carte.id for carte in deck) == sorted(["CRT_7"] * 4 + ["CRT_10"] * 4 + ["CRT_11", "CRT_12"])
    assert {carte.exemplaire_module for carte in deck} == {"M1"}


def test_la_defausse_est_remelangee_quand_la_pioche_est_vide_jamais_les_epuisees_ni_hors_service():
    deck = DeckNew(_cartes("CRT_7", 3), random.Random(0))
    deck.defausse, deck.pioche = deck.pioche[:2], []
    deck.epuisees = _cartes("CRT_12", 1)
    deck.hors_service = _cartes("CRT_9", 1, "M2")

    assert deck.piocher(5) == 2
    assert len(deck.epuisees) == len(deck.hors_service) == 1


def test_la_main_est_limitee():
    deck = DeckNew(_cartes("CRT_7", TAILLE_MAIN_MAX + 3), random.Random(0))

    assert deck.piocher(TAILLE_MAIN_MAX + 3) == TAILLE_MAIN_MAX


def test_module_detruit_ses_cartes_non_persistantes_passent_hors_service_partout():
    cartes_m2 = _cartes("CRT_9", 3, "M2")
    persistante = _cartes("CRT_18", 1, "M2")[0]
    persistante.persistante = True
    deck = DeckNew(_cartes("CRT_7", 2) + cartes_m2 + [persistante], random.Random(0))
    deck.main = [deck.pioche.pop()]
    deck.defausse = [deck.pioche.pop()]

    deplacees = deck.mettre_hors_service("M2")

    assert sorted(map(id, deplacees)) == sorted(map(id, cartes_m2))
    assert all(carte.exemplaire_module == "M1" or carte is persistante for carte in deck.pioche + deck.main + deck.defausse)


def test_ranger_une_carte_jouee():
    deck = DeckNew([], random.Random(0))
    epuisee, orpheline, normale = _cartes("CRT_7", 3)

    deck.ranger_carte_jouee(epuisee, epuisee=True, module_detruit=True)
    deck.ranger_carte_jouee(orpheline, epuisee=False, module_detruit=True)
    deck.ranger_carte_jouee(normale, epuisee=False, module_detruit=False)

    assert (deck.epuisees, deck.hors_service, deck.defausse) == ([epuisee], [orpheline], [normale])


def test_retirer_une_carte_absente_de_la_main_est_refuse():
    with pytest.raises(ValueError, match="pas en main"):
        DeckNew([], random.Random(0)).retirer_de_la_main(_cartes("CRT_7", 1)[0])
