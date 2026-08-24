"""
Tests unitaires pour src/gameplay/partie.py (persistance du parcours, specs.md 10.3).
"""

import random

import pytest

from src.gameplay.position import Colonne, Rangee

from src.gameplay.donnees import charger_cartes, charger_modules
from src.gameplay import partie as partie_module
from src.gameplay.partie import (
    STATUT_EN_COURS,
    STATUT_TERMINEE,
    EtatModule,
    Partie,
    abandonner_partie,
    ajouter_carte,
    avancer_niveau,
    combat_depuis_partie,
    creer_profil,
    deck_de_la_partie,
    equiper_module,
    id_de_carte,
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
    specs_utilisees_partie,
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


# --- Progression (specs.md 2.4) ---


def test_equiper_module_remplit_le_premier_emplacement_libre():
    partie = nouvelle_partie(random.Random(1))
    spec = next(s for s in charger_modules() if s.id != "MOD_1")

    equiper_module(partie, spec)

    assert partie.vaisseau["avant_gauche"] is not None
    assert partie.vaisseau["avant_gauche"].module_id == spec.id
    assert partie.vaisseau["avant_gauche"].pv == spec.points_de_vie
    assert partie.vaisseau["avant_gauche"].pv_max == spec.points_de_vie
    assert partie.vaisseau["avant_gauche"].niveau_maj == 1
    assert partie.vaisseau["avant_droite"] is None


def test_equiper_module_remplit_le_deuxieme_emplacement_si_le_premier_est_pris():
    partie = nouvelle_partie(random.Random(1))
    specs = [s for s in charger_modules() if s.id != "MOD_1"]

    equiper_module(partie, specs[0])
    equiper_module(partie, specs[1])

    assert partie.vaisseau["avant_gauche"].module_id == specs[0].id
    assert partie.vaisseau["avant_droite"].module_id == specs[1].id


def test_avancer_niveau_incremente():
    partie = nouvelle_partie(random.Random(1))

    avancer_niveau(partie)

    assert partie.niveau == 2


def test_id_de_carte_retrouve_l_id_par_identite():
    cartes = charger_cartes()
    id_attendu, carte = next(iter(cartes.items()))

    assert id_de_carte(carte, cartes) == id_attendu


def test_ajouter_carte_etend_le_deck():
    partie = nouvelle_partie(random.Random(1))
    taille_avant = len(partie.deck)

    ajouter_carte(partie, "CRT_20")

    assert len(partie.deck) == taille_avant + 1
    assert partie.deck[-1] == "CRT_20"


def test_specs_utilisees_partie_module_principal_en_premier():
    partie = nouvelle_partie(random.Random(1))
    specs_par_id = {spec.id: spec for spec in charger_modules()}
    spec_secondaire = next(s for s in charger_modules() if s.id != "MOD_1")
    equiper_module(partie, spec_secondaire)

    specs = specs_utilisees_partie(partie, specs_par_id)

    assert specs[0].id == "MOD_1"
    assert specs[1].id == spec_secondaire.id
    assert len(specs) == 2


def test_specs_utilisees_partie_ignore_les_emplacements_vides():
    partie = nouvelle_partie(random.Random(1))
    specs_par_id = {spec.id: spec for spec in charger_modules()}

    specs = specs_utilisees_partie(partie, specs_par_id)

    assert len(specs) == 1
    assert specs[0].id == "MOD_1"


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
