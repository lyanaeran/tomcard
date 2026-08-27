"""
Tests unitaires pour src/gameplay/partie.py (persistance du parcours, specs.md 10.3).
"""

import random

import pytest

from src.gameplay.position import Colonne, Rangee

from src.gameplay.donnees import charger_cartes, charger_modules
from src.gameplay import partie as partie_module
from src.gameplay.config_poc import NOMBRE_ENNEMIS_ASTEROIDES
from src.gameplay.partie import (
    ARGENT_DEPART,
    ARGENT_PAR_ENNEMI_TUE,
    COUT_ACTION_STATION_SERVICE,
    COUT_METTRE_AUX_NORMES,
    DEGATS_ASTEROIDES,
    NIVEAU_MAJ_MAX,
    PV_AMELIORATION,
    PV_REPARATION,
    PV_REPARATION_VAISSEAU,
    STATUT_EN_COURS,
    STATUT_TERMINEE,
    EtatModule,
    Partie,
    abandonner_partie,
    ajouter_carte,
    ameliorer_module,
    ameliorer_module_aventure,
    avancer_niveau,
    combat_aventure_asteroides,
    combat_depuis_partie,
    creer_profil,
    deck_de_la_partie,
    deplacer_module,
    equiper_module,
    gagner_argent_combat,
    id_de_carte,
    lister_profils,
    mettre_a_jour_module,
    nouvelle_partie,
    nouveau_profil,
    partie_depuis_dict,
    partie_depuis_json,
    partie_en_cours,
    partie_vers_dict,
    partie_vers_json,
    payer_mise_aux_normes,
    profil_depuis_json,
    profil_vers_json,
    reparer_module,
    reparer_vaisseau,
    retirer_carte,
    sauvegarder_partie,
    specs_utilisees_partie,
    subir_degats_module,
    synchroniser_vaisseau_depuis_combat,
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
    assert partie.argent == ARGENT_DEPART
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


def test_combat_depuis_partie_reflete_les_degats_meme_en_mode_test():
    """La persistance des PV entre combats (specs.md 2.2) doit rester testable en mode test
    (MODE_TEST, cf. config_poc.py) : seule la valeur de depart d'un module tout juste equipe est
    plus elevee (cf. test_equiper_module_utilise_pv_module_mode_test_par_defaut plus bas), pas la
    persistance elle-meme - sinon Reparer/Ameliorer n'auraient plus aucune utilite a tester."""
    assert partie_module.MODE_TEST is True
    partie = _partie_exemple()
    partie.vaisseau["base"].pv = 3  # simule des degats subis au combat precedent

    combat = combat_depuis_partie(partie, random.Random(1))

    assert combat.joueur.vaisseau.base.pv == 3
    assert combat.joueur.vaisseau.base.pv_max == 15


def test_combat_depuis_partie_en_mode_test_donne_20_degats_aux_cartes_attaque_de_base():
    """Meme comportement que creer_deck_mode_test (config_poc.py), applique cette fois au deck
    reel d'une partie (2 exemplaires de Laser dans _partie_exemple) plutot qu'a une demonstration."""
    from src.gameplay.config_poc import VALEUR_ATTAQUE_BASE_MODE_TEST

    assert partie_module.MODE_TEST is True
    partie = _partie_exemple()

    combat = combat_depuis_partie(partie, random.Random(1))

    toutes_les_cartes = combat.joueur.deck.pioche + combat.joueur.deck.main
    lasers = [carte for carte in toutes_les_cartes if carte.nom == "Laser"]
    assert len(lasers) == 2
    assert all(carte.valeur == VALEUR_ATTAQUE_BASE_MODE_TEST for carte in lasers)


def test_synchroniser_vaisseau_depuis_combat_reporte_les_pv_sur_la_partie():
    """Operation inverse de combat_depuis_partie : sans elle, les degats subis en combat ne
    persistaient jamais reellement (bug constate en jeu - rien dans l'orchestration reelle,
    main.py/web/bridge.py, ne reportait les PV de combat sur la partie sauvegardee)."""
    partie = _partie_exemple()
    combat = combat_depuis_partie(partie, random.Random(1))
    combat.joueur.vaisseau.base.pv = 4
    combat.joueur.vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).pv = 6

    synchroniser_vaisseau_depuis_combat(partie, combat.joueur.vaisseau)

    assert partie.vaisseau["base"].pv == 4
    assert partie.vaisseau["base"].pv_max == 15  # pv_max jamais touche
    assert partie.vaisseau["avant_gauche"].pv == 6


def test_synchroniser_vaisseau_depuis_combat_ignore_les_emplacements_vides():
    partie = _partie_exemple()
    combat = combat_depuis_partie(partie, random.Random(1))

    synchroniser_vaisseau_depuis_combat(partie, combat.joueur.vaisseau)

    assert partie.vaisseau["avant_droite"] is None
    assert partie.vaisseau["arriere_gauche"] is None
    assert partie.vaisseau["arriere_droite"] is None


def test_gagner_argent_combat_ajoute_argent_par_ennemi_de_la_flotte():
    """specs.md 2.1 : ARGENT_PAR_ENNEMI_TUE par ennemi de la flotte affrontee - une victoire
    suppose que tous ces ennemis sont detruits, la flotte n'existe qu'a raison d'un ennemi par
    case peuplee (pas de fusion d'un ennemi L sur plusieurs cases, cf. specs.md 3.2/9.1)."""
    partie = _partie_exemple()
    combat = combat_depuis_partie(partie, random.Random(1))
    nombre_ennemis = len(combat.flotte.positions())

    gagner_argent_combat(partie, combat)

    assert partie.argent == 50 + ARGENT_PAR_ENNEMI_TUE * nombre_ennemis


# --- Progression (specs.md 2.4) ---


def test_equiper_module_remplit_le_premier_emplacement_libre(monkeypatch):
    """Hors mode test (cf. test_equiper_module_utilise_pv_module_mode_test_par_defaut ci-dessous
    pour son comportement) : PV de depart = valeur normale du module (config/modules.json)."""
    monkeypatch.setattr(partie_module, "MODE_TEST", False)
    partie = nouvelle_partie(random.Random(1))
    spec = next(s for s in charger_modules() if s.id != "MOD_1")

    equiper_module(partie, spec)

    assert partie.vaisseau["avant_gauche"] is not None
    assert partie.vaisseau["avant_gauche"].module_id == spec.id
    assert partie.vaisseau["avant_gauche"].pv == spec.points_de_vie
    assert partie.vaisseau["avant_gauche"].pv_max == spec.points_de_vie
    assert partie.vaisseau["avant_gauche"].niveau_maj == 1
    assert partie.vaisseau["avant_droite"] is None


def test_equiper_module_utilise_pv_module_mode_test_par_defaut():
    """MODE_TEST (cf. src/gameplay/config_poc.py) donne une valeur de depart plus elevee aux
    modules tout juste equipes, mais uniquement au moment de l'equipement : les PV persistent
    ensuite normalement d'un combat a l'autre (cf.
    test_combat_depuis_partie_reflete_les_degats_meme_en_mode_test)."""
    from src.gameplay.config_poc import PV_MODULE_MODE_TEST

    assert partie_module.MODE_TEST is True
    partie = nouvelle_partie(random.Random(1))
    spec = next(s for s in charger_modules() if s.id != "MOD_1")

    equiper_module(partie, spec)

    assert partie.vaisseau["avant_gauche"].pv == PV_MODULE_MODE_TEST
    assert partie.vaisseau["avant_gauche"].pv_max == PV_MODULE_MODE_TEST


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


# --- Station service (specs.md 2.2) ---


def test_reparer_module_restaure_les_pv_plafonne_au_max():
    partie = _partie_exemple()

    succes = reparer_module(partie, "avant_gauche")

    assert succes is True
    assert partie.vaisseau["avant_gauche"].pv == min(10 + PV_REPARATION, 18)
    assert partie.argent == 50 - COUT_ACTION_STATION_SERVICE


def test_reparer_module_ne_depasse_jamais_le_pv_max():
    partie = _partie_exemple()
    partie.vaisseau["base"].pv = partie.vaisseau["base"].pv_max

    reparer_module(partie, "base")

    assert partie.vaisseau["base"].pv == partie.vaisseau["base"].pv_max


def test_action_station_service_refusee_si_argent_insuffisant():
    """specs.md 2.1/2.2 : aucune action n'est appliquee, l'Argent n'est pas non plus deduit."""
    partie = _partie_exemple()
    partie.argent = COUT_ACTION_STATION_SERVICE - 1

    succes = reparer_module(partie, "avant_gauche")

    assert succes is False
    assert partie.vaisseau["avant_gauche"].pv == 10
    assert partie.argent == COUT_ACTION_STATION_SERVICE - 1


def test_ameliorer_module_augmente_pv_max_et_pv_actuels():
    partie = _partie_exemple()

    succes = ameliorer_module(partie, "avant_gauche")

    assert succes is True
    assert partie.vaisseau["avant_gauche"].pv_max == 18 + PV_AMELIORATION
    assert partie.vaisseau["avant_gauche"].pv == 10 + PV_AMELIORATION
    assert partie.argent == 50 - COUT_ACTION_STATION_SERVICE


def test_mettre_a_jour_module_incremente_le_palier():
    partie = _partie_exemple()

    succes = mettre_a_jour_module(partie, "avant_gauche")

    assert succes is True
    assert partie.vaisseau["avant_gauche"].niveau_maj == 3
    assert partie.argent == 50 - COUT_ACTION_STATION_SERVICE


def test_mettre_a_jour_module_plafonne_a_niveau_maj_max():
    partie = _partie_exemple()
    partie.vaisseau["avant_gauche"].niveau_maj = NIVEAU_MAJ_MAX

    mettre_a_jour_module(partie, "avant_gauche")

    assert partie.vaisseau["avant_gauche"].niveau_maj == NIVEAU_MAJ_MAX


def test_deplacer_module_echange_deux_emplacements_occupes():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = 50
    specs = [s for s in charger_modules() if s.id != "MOD_1"]
    equiper_module(partie, specs[0])
    equiper_module(partie, specs[1])

    succes = deplacer_module(partie, "avant_gauche", "avant_droite")

    assert succes is True
    assert partie.vaisseau["avant_gauche"].module_id == specs[1].id
    assert partie.vaisseau["avant_droite"].module_id == specs[0].id
    assert partie.argent == 50 - COUT_ACTION_STATION_SERVICE


def test_deplacer_module_vers_un_emplacement_vide():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = 50
    spec = next(s for s in charger_modules() if s.id != "MOD_1")
    equiper_module(partie, spec)

    deplacer_module(partie, "avant_gauche", "arriere_gauche")

    assert partie.vaisseau["avant_gauche"] is None
    assert partie.vaisseau["arriere_gauche"].module_id == spec.id


# --- Aventures (specs.md 2.5) ---


def test_reparer_vaisseau_soigne_chaque_module_equipe_plafonne_au_max():
    partie = _partie_exemple()  # base pv=15/15 (deja au max), avant_gauche pv=10/18

    reparer_vaisseau(partie)

    assert partie.vaisseau["base"].pv == 15
    assert partie.vaisseau["avant_gauche"].pv == min(10 + PV_REPARATION_VAISSEAU, 18)


def test_reparer_vaisseau_ignore_les_emplacements_vides():
    partie = _partie_exemple()

    reparer_vaisseau(partie)  # ne doit pas lever d'exception sur avant_droite/arriere_* (None)

    assert partie.vaisseau["avant_droite"] is None


def test_retirer_carte_retire_un_seul_exemplaire():
    partie = _partie_exemple()  # deck=["CRT_7", "CRT_7", "CRT_10"]

    retirer_carte(partie, "CRT_7")

    assert partie.deck == ["CRT_7", "CRT_10"]


def test_ameliorer_module_aventure_meme_effet_que_ameliorer_module_mais_gratuit():
    partie = _partie_exemple()  # argent=50
    argent_avant = partie.argent

    ameliorer_module_aventure(partie, "avant_gauche")

    assert partie.vaisseau["avant_gauche"].pv_max == 18 + PV_AMELIORATION
    assert partie.vaisseau["avant_gauche"].pv == 10 + PV_AMELIORATION
    assert partie.argent == argent_avant  # contrairement a ameliorer_module (Station service)


def test_subir_degats_module_reduit_les_pv():
    partie = _partie_exemple()  # avant_gauche pv=10

    subir_degats_module(partie, "avant_gauche", DEGATS_ASTEROIDES)

    assert partie.vaisseau["avant_gauche"].pv == 10 - DEGATS_ASTEROIDES


def test_subir_degats_module_plafonne_a_0():
    partie = _partie_exemple()  # avant_gauche pv=10

    subir_degats_module(partie, "avant_gauche", 999)

    assert partie.vaisseau["avant_gauche"].pv == 0


def test_combat_aventure_asteroides_a_une_flotte_scriptee():
    partie = _partie_exemple()

    combat = combat_aventure_asteroides(partie, random.Random(1))

    assert len(combat.flotte.positions()) == NOMBRE_ENNEMIS_ASTEROIDES
    assert combat.joueur.vaisseau.base.pv == 15  # meme vaisseau reel que combat_depuis_partie


def test_payer_mise_aux_normes_deduit_le_cout_si_assez_d_argent():
    partie = _partie_exemple()  # argent=50

    succes = payer_mise_aux_normes(partie)

    assert succes is True
    assert partie.argent == 50 - COUT_METTRE_AUX_NORMES


def test_payer_mise_aux_normes_refuse_si_argent_insuffisant():
    partie = _partie_exemple()
    partie.argent = COUT_METTRE_AUX_NORMES - 1

    succes = payer_mise_aux_normes(partie)

    assert succes is False
    assert partie.argent == COUT_METTRE_AUX_NORMES - 1


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
