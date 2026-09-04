"""
Tests unitaires pour la generation aleatoire du combat du POC (src/gameplay/config_poc.py).
"""

import random

from src.gameplay import config_poc as config_poc_module
from src.gameplay.carte import RareteCarte, TypeCarte
from src.gameplay.combat import EtatCombat
from src.gameplay.config_poc import (
    CARTES_PAR_MODULE_EQUIPE,
    ELECTRICITE_PAR_TOUR,
    ID_MODULE_PRINCIPAL,
    MODE_TEST,
    NIVEAU_PRIME_DEUX_ENNEMIS,
    NOMBRE_ENNEMIS_ASTEROIDES,
    NOMBRE_ENNEMIS_MODE_TEST,
    NOMBRE_ENNEMIS_PRIME_NIVEAU_ELEVE,
    NOMBRE_ENNEMIS_PRIME_NIVEAU_FAIBLE,
    NOMBRE_MODULES_EQUIPES,
    PV_ENNEMI_MODE_TEST,
    PV_MODULE_MODE_TEST,
    VALEUR_ATTAQUE_BASE_MODE_TEST,
    creer_combat_poc,
    creer_deck,
    creer_deck_mode_test,
    creer_flotte,
    creer_flotte_asteroides,
    creer_flotte_boss,
    creer_flotte_prime,
    creer_vaisseau,
    nombre_ennemis_prime,
    tirer_cartes,
)
from src.gameplay.donnees import charger_cartes, charger_ennemis, charger_modules
from src.gameplay.position import Colonne


def test_charger_modules_contient_le_module_principal():
    specs = charger_modules()

    principal = next(spec for spec in specs if spec.id == ID_MODULE_PRINCIPAL)

    assert principal.nom == "Principal"
    assert principal.points_de_vie == 50
    assert len(specs) >= NOMBRE_MODULES_EQUIPES + 1  # le principal + au moins 4 equipables


def test_charger_modules_secondaires_ont_30_pv():
    specs = charger_modules()

    secondaires = [spec for spec in specs if spec.id != ID_MODULE_PRINCIPAL]

    assert secondaires
    assert all(spec.points_de_vie == 30 for spec in secondaires)


def test_charger_ennemis_contient_les_5_ennemis():
    specs = charger_ennemis()

    noms = {spec.nom for spec in specs}

    assert noms == {"Pat le Pirate", "Le nettoyeur", "Petit Jean", "Le puzzle", "Miroir"}


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
    """Hors mode test (MODE_TEST est desormais False en production, cf. sa docstring)."""
    assert MODE_TEST is False
    specs = charger_ennemis()
    aleatoire = random.Random(1)

    flotte = creer_flotte(specs, aleatoire)

    assert len(flotte.positions()) == 6
    assert len(flotte.ennemis_vivants()) == 6
    noms_connus = {spec.nom for spec in specs}
    for ennemi in flotte.ennemis_vivants():
        assert ennemi.nom in noms_connus


def test_creer_flotte_en_mode_test_ne_remplit_que_2_cases(monkeypatch):
    """MODE_TEST reste utilisable pour accelerer les essais manuels (cf. sa docstring), meme
    si desactive par defaut en production."""
    monkeypatch.setattr(config_poc_module, "MODE_TEST", True)
    specs = charger_ennemis()
    aleatoire = random.Random(1)

    flotte = creer_flotte(specs, aleatoire)

    assert len(flotte.positions()) == NOMBRE_ENNEMIS_MODE_TEST
    assert len(flotte.ennemis_vivants()) == NOMBRE_ENNEMIS_MODE_TEST


def test_creer_flotte_asteroides_remplit_3_cases():
    """Aventure Asteroides (specs.md 2.5) : nombre fixe d'ennemis, independant de MODE_TEST
    (contrairement a creer_flotte) - seul leur PV depend de MODE_TEST via _ennemi_depuis_spec."""
    specs = charger_ennemis()
    aleatoire = random.Random(1)

    flotte = creer_flotte_asteroides(specs, aleatoire)

    assert len(flotte.positions()) == NOMBRE_ENNEMIS_ASTEROIDES == 3
    assert len(flotte.ennemis_vivants()) == NOMBRE_ENNEMIS_ASTEROIDES


def test_nombre_ennemis_prime_un_ennemi_avant_le_niveau_6():
    assert nombre_ennemis_prime(1) == NOMBRE_ENNEMIS_PRIME_NIVEAU_FAIBLE == 1
    assert nombre_ennemis_prime(NIVEAU_PRIME_DEUX_ENNEMIS - 1) == 1


def test_nombre_ennemis_prime_deux_ennemis_a_partir_du_niveau_6():
    assert nombre_ennemis_prime(NIVEAU_PRIME_DEUX_ENNEMIS) == NOMBRE_ENNEMIS_PRIME_NIVEAU_ELEVE == 2
    assert nombre_ennemis_prime(NIVEAU_PRIME_DEUX_ENNEMIS + 4) == 2


def test_creer_flotte_prime_niveau_faible_a_un_seul_ennemi():
    specs = charger_ennemis()

    flotte = creer_flotte_prime(specs, niveau=1, aleatoire=random.Random(1))

    assert len(flotte.ennemis_vivants()) == 1


def test_creer_flotte_prime_niveau_eleve_a_deux_ennemis():
    specs = charger_ennemis()

    flotte = creer_flotte_prime(specs, niveau=NIVEAU_PRIME_DEUX_ENNEMIS, aleatoire=random.Random(1))

    assert len(flotte.ennemis_vivants()) == 2


def test_creer_flotte_prime_respecte_la_preference_de_placement():
    """Petit Jean (PROTECTEUR_AVANT) et Le nettoyeur (PROTEGE_ARRIERE) doivent se retrouver
    sur leurs colonnes preferees, meme si le tirage les place ensemble."""
    specs = charger_ennemis()
    specs_par_id = {spec.id: spec for spec in specs}
    petit_jean = specs_par_id["ENM_PETIT_JEAN"]
    nettoyeur = specs_par_id["ENM_LE_NETTOYEUR"]

    aleatoire = random.Random(0)
    positions = config_poc_module._placer_specs_avec_preference([petit_jean, nettoyeur], aleatoire)

    position_jean = next(pos for pos, spec in positions.items() if spec is petit_jean)
    position_nettoyeur = next(pos for pos, spec in positions.items() if spec is nettoyeur)
    assert position_jean.colonne == Colonne.AVANT
    assert position_nettoyeur.colonne == Colonne.ARRIERE


def test_creer_flotte_boss_composition_fixe():
    specs = charger_ennemis()

    flotte = creer_flotte_boss(specs)

    noms = sorted(ennemi.nom for ennemi in flotte.ennemis_vivants())
    assert noms == sorted(["Petit Jean", "Petit Jean", "Le nettoyeur", "Le puzzle"])
    for position, ennemi in flotte.positions().items():
        if ennemi.nom == "Petit Jean":
            assert position.colonne == Colonne.AVANT
        else:
            assert position.colonne == Colonne.ARRIERE


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


def test_creer_deck_contient_22_cartes():
    """10 cartes fixes du module principal (deck de base) + 3 par module equipe."""
    specs_modules = charger_modules()
    cartes = charger_cartes()
    aleatoire = random.Random(5)
    _vaisseau, specs_utilisees = creer_vaisseau(specs_modules, aleatoire)

    deck = creer_deck(specs_utilisees, cartes, aleatoire)

    total = len(deck.pioche) + len(deck.main) + len(deck.defausse)
    attendu = 10 + CARTES_PAR_MODULE_EQUIPE * NOMBRE_MODULES_EQUIPES
    assert total == attendu == 22


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
    assert len(combat.flotte.positions()) == 6  # MODE_TEST desactive : les 6 cases sont peuplees
    assert combat.joueur.electricite == ELECTRICITE_PAR_TOUR
    assert len(combat.joueur.deck.main) == 5


def test_creer_combat_poc_utilise_le_deck_reel_quand_mode_test_desactive():
    combat = creer_combat_poc(random.Random(4))

    total = len(combat.joueur.deck.pioche) + len(combat.joueur.deck.main) + len(combat.joueur.deck.defausse)
    attendu = 10 + CARTES_PAR_MODULE_EQUIPE * NOMBRE_MODULES_EQUIPES
    assert total == attendu == 22


def test_deux_combats_successifs_ont_des_ennemis_independants():
    combat_1 = creer_combat_poc(random.Random(1))
    combat_2 = creer_combat_poc(random.Random(1))

    combat_1.flotte.ennemis_vivants()[0].subir_degats(1000)

    assert combat_2.flotte.ennemis_vivants()[0].pv > 0


# --- Mode test (bascule manuelle, desactivee par defaut - cf. MODE_TEST) ---


def test_creer_deck_mode_test_contient_un_exemplaire_de_chaque_carte_jouable():
    cartes = charger_cartes()
    aleatoire = random.Random(3)

    deck = creer_deck_mode_test(cartes, aleatoire)

    toutes = deck.pioche + deck.main + deck.defausse
    assert len(toutes) == len(cartes)
    assert sorted(carte.nom for carte in toutes) == sorted(carte.nom for carte in cartes.values())


def test_mode_test_actif_donne_200_pv_aux_modules_et_aux_ennemis(monkeypatch):
    """MODE_TEST est la variable de bascule pour les tests manuels (cf. sa docstring),
    desactivee par defaut en production (MODE_TEST is False) - ce test verifie son effet
    quand elle est reactivee explicitement."""
    monkeypatch.setattr(config_poc_module, "MODE_TEST", True)
    specs_modules = charger_modules()
    specs_ennemis = charger_ennemis()

    vaisseau, _specs = creer_vaisseau(specs_modules, random.Random(3))
    flotte = creer_flotte(specs_ennemis, random.Random(3))

    assert vaisseau.base.pv_max == PV_MODULE_MODE_TEST
    assert all(module.pv_max == PV_MODULE_MODE_TEST for module in vaisseau.modules_equipes().values())
    assert all(ennemi.pv_max == PV_ENNEMI_MODE_TEST for ennemi in flotte.ennemis_vivants())


def test_creer_deck_mode_test_donne_20_degats_aux_cartes_attaque_de_base():
    """Les cartes ATTAQUE de rarete Base (Laser, Laser percant, Bombardement) tuent un ennemi en
    un coup en mode test (PV_ENNEMI_MODE_TEST), les autres cartes gardent leur valeur normale."""
    cartes = charger_cartes()
    aleatoire = random.Random(3)

    deck = creer_deck_mode_test(cartes, aleatoire)

    toutes = deck.pioche + deck.main + deck.defausse
    attaques_base = [c for c in toutes if c.rarete == RareteCarte.BASE and c.type == TypeCarte.ATTAQUE]
    autres = [c for c in toutes if c.rarete != RareteCarte.BASE or c.type != TypeCarte.ATTAQUE]

    assert attaques_base  # au moins Laser/Laser percant/Bombardement
    assert all(carte.valeur == VALEUR_ATTAQUE_BASE_MODE_TEST for carte in attaques_base)
    assert VALEUR_ATTAQUE_BASE_MODE_TEST >= PV_ENNEMI_MODE_TEST
    for carte in autres:
        carte_originale = cartes[next(id_carte for id_carte, c in cartes.items() if c.nom == carte.nom)]
        assert carte.valeur == carte_originale.valeur


def test_creer_combat_poc_utilise_le_deck_mode_test_quand_actif(monkeypatch):
    monkeypatch.setattr(config_poc_module, "MODE_TEST", True)
    combat = creer_combat_poc(random.Random(4))

    total = len(combat.joueur.deck.pioche) + len(combat.joueur.deck.main) + len(combat.joueur.deck.defausse)
    assert total == len(charger_cartes())
