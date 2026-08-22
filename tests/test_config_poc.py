"""
Tests unitaires pour la generation aleatoire du combat du POC (src/gameplay/config_poc.py).
"""

import random

from src.gameplay.combat import EtatCombat
from src.gameplay.config_poc import (
    CARTES_PAR_MODULE_EQUIPE,
    ELECTRICITE_PAR_TOUR,
    ID_MODULE_PRINCIPAL,
    MODE_TEST,
    NOMBRE_MODULES_EQUIPES,
    PV_ENNEMI_MODE_TEST,
    PV_MODULE_MODE_TEST,
    creer_combat_poc,
    creer_deck,
    creer_deck_mode_test,
    creer_flotte,
    creer_vaisseau,
    tirer_cartes,
)
from src.gameplay.donnees import charger_cartes, charger_ennemis, charger_modules


def test_charger_modules_contient_le_module_principal():
    specs = charger_modules()

    principal = next(spec for spec in specs if spec.id == ID_MODULE_PRINCIPAL)

    assert principal.nom == "Principal"
    assert len(specs) >= NOMBRE_MODULES_EQUIPES + 1  # le principal + au moins 4 equipables


def test_creer_vaisseau_place_le_principal_et_4_modules_differents():
    specs = charger_modules()
    aleatoire = random.Random(42)

    vaisseau, specs_utilisees = creer_vaisseau(specs, aleatoire)

    assert vaisseau.base.nom == "Principal"
    equipes = vaisseau.modules_equipes()
    assert len(equipes) == NOMBRE_MODULES_EQUIPES
    noms = [module.nom for module in equipes.values()]
    assert len(set(noms)) == NOMBRE_MODULES_EQUIPES  # tous differents
    assert len(specs_utilisees) == NOMBRE_MODULES_EQUIPES + 1
    assert specs_utilisees[0].id == ID_MODULE_PRINCIPAL


def test_creer_vaisseau_est_deterministe_pour_une_meme_graine():
    specs = charger_modules()

    vaisseau_1, _ = creer_vaisseau(specs, random.Random(7))
    vaisseau_2, _ = creer_vaisseau(specs, random.Random(7))

    noms_1 = sorted(m.nom for m in vaisseau_1.modules_equipes().values())
    noms_2 = sorted(m.nom for m in vaisseau_2.modules_equipes().values())
    assert noms_1 == noms_2


def test_creer_flotte_remplit_les_6_cases():
    specs = charger_ennemis()
    aleatoire = random.Random(1)

    flotte = creer_flotte(specs, aleatoire)

    assert len(flotte.positions()) == 6
    assert len(flotte.ennemis_vivants()) == 6
    ids_connus = {spec.nom for spec in specs}
    for ennemi in flotte.ennemis_vivants():
        assert ennemi.nom in ids_connus


def test_tirer_cartes_pioche_la_bonne_quantite_dans_la_pool():
    cartes = charger_cartes()
    pool = ("CRT_7", "CRT_10", "CRT_12")
    aleatoire = random.Random(3)

    tirees = tirer_cartes(pool, 8, cartes, aleatoire)

    assert len(tirees) == 8
    noms_pool = {cartes[cid].nom for cid in pool}
    assert all(carte.nom in noms_pool for carte in tirees)


def test_tirer_cartes_renvoie_des_exemplaires_independants():
    """Deux tirages du meme id ne doivent pas partager d'objet (munitions par exemplaire)."""
    cartes = charger_cartes()
    tirees = tirer_cartes(("CRT_12",), 2, cartes, random.Random(1))

    assert tirees[0] is not tirees[1]
    assert tirees[0] is not cartes["CRT_12"]


def test_creer_deck_contient_24_cartes():
    """12 cartes fixes du module principal (deck de base) + 3 par module equipe."""
    specs_modules = charger_modules()
    cartes = charger_cartes()
    aleatoire = random.Random(5)
    _vaisseau, specs_utilisees = creer_vaisseau(specs_modules, aleatoire)

    deck = creer_deck(specs_utilisees, cartes, aleatoire)

    total = len(deck.pioche) + len(deck.main) + len(deck.defausse)
    attendu = 12 + CARTES_PAR_MODULE_EQUIPE * NOMBRE_MODULES_EQUIPES
    assert total == attendu == 24


def test_creer_deck_module_principal_a_4_laser_et_4_bouclier():
    specs_modules = charger_modules()
    cartes = charger_cartes()
    aleatoire = random.Random(5)
    _vaisseau, specs_utilisees = creer_vaisseau(specs_modules, aleatoire)

    deck = creer_deck(specs_utilisees, cartes, aleatoire)

    toutes = deck.pioche + deck.main + deck.defausse
    noms = [carte.nom for carte in toutes]
    assert noms.count("Laser") == 4
    assert noms.count("Bouclier") == 4


def test_creer_combat_poc_initialise_un_combat_complet():
    combat = creer_combat_poc(random.Random(99))

    assert combat.etat == EtatCombat.EN_COURS
    assert combat.joueur.vaisseau.base.nom == "Principal"
    assert len(combat.joueur.vaisseau.modules_equipes()) == NOMBRE_MODULES_EQUIPES
    assert len(combat.flotte.positions()) == 6
    assert combat.joueur.electricite == ELECTRICITE_PAR_TOUR
    assert len(combat.joueur.deck.main) == 5


def test_deux_combats_successifs_ont_des_ennemis_independants():
    combat_1 = creer_combat_poc(random.Random(1))
    combat_2 = creer_combat_poc(random.Random(1))

    combat_1.flotte.ennemis_vivants()[0].subir_degats(1000)

    assert combat_2.flotte.ennemis_vivants()[0].pv > 0


# --- Mode test (poc.md "Mode test") ---


def test_creer_deck_mode_test_contient_un_exemplaire_de_chaque_carte_jouable():
    cartes = charger_cartes()
    aleatoire = random.Random(3)

    deck = creer_deck_mode_test(cartes, aleatoire)

    toutes = deck.pioche + deck.main + deck.defausse
    assert len(toutes) == len(cartes)
    assert sorted(carte.nom for carte in toutes) == sorted(carte.nom for carte in cartes.values())


def test_mode_test_actif_donne_200_pv_aux_modules_et_aux_ennemis():
    """MODE_TEST est la variable de bascule pour les tests manuels (cf. poc.md "Mode test") :
    ce test verifie son effet quand elle est active, comme actuellement configure."""
    assert MODE_TEST is True
    specs_modules = charger_modules()
    specs_ennemis = charger_ennemis()

    vaisseau, _specs = creer_vaisseau(specs_modules, random.Random(3))
    flotte = creer_flotte(specs_ennemis, random.Random(3))

    assert vaisseau.base.pv_max == PV_MODULE_MODE_TEST
    assert all(module.pv_max == PV_MODULE_MODE_TEST for module in vaisseau.modules_equipes().values())
    assert all(ennemi.pv_max == PV_ENNEMI_MODE_TEST for ennemi in flotte.ennemis_vivants())


def test_creer_combat_poc_utilise_le_deck_mode_test_quand_actif():
    combat = creer_combat_poc(random.Random(4))

    total = len(combat.joueur.deck.pioche) + len(combat.joueur.deck.main) + len(combat.joueur.deck.defausse)
    assert total == len(charger_cartes())
