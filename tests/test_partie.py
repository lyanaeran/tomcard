"""
Tests unitaires pour src/gameplay/partie.py (persistance du parcours, specs.md 10.3).
"""

import random

import pytest

from src.gameplay.position import Colonne, Rangee

from src.gameplay import partie as partie_module
from src.gameplay.partie import (
    STATUT_EN_COURS,
    STATUT_TERMINEE,
    EtatModule,
    Partie,
    abandonner_partie,
    combat_depuis_partie,
    creer_profil,
    deck_de_la_partie,
    lister_profils,
    nouvelle_partie,
    nouveau_profil,
    partie_depuis_dict,
    partie_depuis_json,
    partie_en_cours,
    partie_vers_dict,
    partie_vers_json,
    profil_depuis_json,
    profil_vers_json,
    sauvegarder_partie,
)


def _partie_exemple() -> Partie:
    return Partie(
        id="partie_test",
        nom="Partie de test",
        statut=STATUT_EN_COURS,
        graine=42,
        niveau=3,
        argent=50,
        vaisseau={
            "base": EtatModule(module_id="MOD_1", pv=15, pv_max=15, niveau_maj=1),
            "avant_gauche": EtatModule(module_id="MOD_3", pv=10, pv_max=18, niveau_maj=2),
            "avant_droite": None,
            "arriere_gauche": None,
            "arriere_droite": None,
        },
        deck=["CRT_7", "CRT_7", "CRT_10"],
    )


def test_partie_vers_dict_puis_depuis_dict_roundtrip():
    partie = _partie_exemple()

    reconstruite = partie_depuis_dict(partie_vers_dict(partie))

    assert reconstruite == partie


def test_partie_vers_json_puis_depuis_json_roundtrip():
    partie = _partie_exemple()

    reconstruite = partie_depuis_json(partie_vers_json(partie))

    assert reconstruite == partie


def test_profil_vers_json_puis_depuis_json_roundtrip():
    profil = nouveau_profil("Alice")

    reconstruit = profil_depuis_json(profil_vers_json(profil))

    assert reconstruit == profil


def test_nouvelle_partie_commence_au_niveau_1_avec_seulement_le_module_principal():
    partie = nouvelle_partie(random.Random(1))

    assert partie.niveau == 1
    assert partie.statut == STATUT_EN_COURS
    assert partie.argent == 0
    assert partie.vaisseau["base"] is not None
    assert partie.vaisseau["base"].module_id == "MOD_1"
    assert partie.vaisseau["avant_gauche"] is None
    assert partie.vaisseau["avant_droite"] is None
    assert partie.vaisseau["arriere_gauche"] is None
    assert partie.vaisseau["arriere_droite"] is None


def test_nouvelle_partie_deck_de_depart_du_module_principal():
    partie = nouvelle_partie(random.Random(1))

    assert len(partie.deck) == 12
    assert partie.deck.count("CRT_7") == 4  # Laser
    assert partie.deck.count("CRT_10") == 4  # Bouclier


def test_deck_de_la_partie_resout_les_ids_en_cartes():
    partie = _partie_exemple()

    cartes = deck_de_la_partie(partie)

    assert len(cartes) == 3
    assert [carte.nom for carte in cartes] == ["Laser", "Laser", "Bouclier"]


def test_deux_appels_a_nouvelle_partie_ont_des_graines_et_ids_differents():
    partie1 = nouvelle_partie(random.Random(1))
    partie2 = nouvelle_partie(random.Random(2))

    assert partie1.graine != partie2.graine


def test_combat_depuis_partie_reprend_le_vaisseau_et_le_deck_persistants():
    partie = _partie_exemple()

    combat = combat_depuis_partie(partie, random.Random(1))

    assert combat.joueur.vaisseau.base.pv == 15
    assert combat.joueur.vaisseau.base.pv_max == 15
    assert combat.joueur.vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).pv == 10
    assert len(combat.joueur.deck.pioche) + len(combat.joueur.deck.main) == 3


@pytest.fixture
def dossier_saves_isole(tmp_path, monkeypatch):
    monkeypatch.setattr(partie_module, "DOSSIER_SAVES", tmp_path / "saves")
    return tmp_path / "saves"


def test_lister_profils_vide_si_aucun_dossier(dossier_saves_isole):
    assert lister_profils() == []


def test_creer_profil_puis_le_retrouver_dans_lister_profils(dossier_saves_isole):
    creer_profil("Bob")
    creer_profil("Alice")

    noms = [profil.nom for profil in lister_profils()]

    assert noms == ["Alice", "Bob"]  # trie par nom


def test_partie_en_cours_renvoie_none_si_aucune_partie(dossier_saves_isole):
    profil = creer_profil("Alice")

    assert partie_en_cours(profil.id) is None


def test_sauvegarder_partie_puis_la_retrouver_en_cours(dossier_saves_isole):
    profil = creer_profil("Alice")
    partie = nouvelle_partie(random.Random(1))

    sauvegarder_partie(profil.id, partie)

    retrouvee = partie_en_cours(profil.id)
    assert retrouvee is not None
    assert retrouvee.id == partie.id
    assert retrouvee.statut == STATUT_EN_COURS


def test_abandonner_partie_la_marque_terminee(dossier_saves_isole):
    profil = creer_profil("Alice")
    partie = nouvelle_partie(random.Random(1))
    sauvegarder_partie(profil.id, partie)

    abandonner_partie(profil.id, partie)

    assert partie_en_cours(profil.id) is None
