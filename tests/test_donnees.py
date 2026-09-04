"""
Tests unitaires pour le chargement des fichiers de configuration (src/gameplay/donnees.py).
"""

from pathlib import Path

from src.gameplay.carte import CibleCarte, TypeCarte
from src.gameplay.donnees import charger_cartes, charger_ennemis, charger_modules, image_case_module


def test_charger_cartes_renvoie_les_cartes_jouables_avec_images_existantes():
    cartes = charger_cartes()

    assert len(cartes) == 23
    for carte in cartes.values():
        assert isinstance(carte.type, TypeCarte)
        assert isinstance(carte.cible, CibleCarte)
        assert Path(carte.image).is_file()


def test_charger_cartes_ignore_les_cartes_sans_bloc_effet():
    """Cartes de design pas encore jouables (mecanique non supportee, cf. specs.md 9.1)."""
    cartes = charger_cartes()

    assert "CRT_15" in cartes  # jouable (Ciel de missiles)
    assert "CRT_13" not in cartes  # non jouable (Missiles, effet a deux valeurs)


def test_charger_modules_renvoie_10_modules_avec_images_existantes_et_cartes_connues():
    """4 des 10 modules (Canon lourd/Controle/Atelier/Radar) ont volontairement une liste de
    cartes vide : leurs cartes ne sont pas encore concues (cf. modules_equipables qui les exclut
    du tirage pour cette raison, src/gameplay/parcours.py)."""
    modules = charger_modules()
    ids_cartes_connus = set(charger_cartes())

    assert len(modules) == 10
    for module in modules:
        assert Path(module.image).is_file()
        assert set(module.cartes).issubset(ids_cartes_connus)
        assert module.description


def test_charger_ennemis_renvoie_6_ennemis_avec_images_existantes():
    ennemis = charger_ennemis()

    assert len(ennemis) == 6
    for ennemi in ennemis:
        assert Path(ennemi.image).is_file()
        assert len(ennemi.actions) > 0
        assert ennemi.points_de_vie > 0


def test_charger_ennemis_le_boss_des_pirates_occupe_2_emplacements():
    """specs.md 3.2 : le Boss des pirates est le seul ennemi a occuper 2 emplacements pour
    l'instant (une case Avant + une Arriere de la meme rangee, cf. config_poc.creer_flotte_boss).
    Les autres ennemis restent a 1 emplacement (valeur par defaut, absente de leur config)."""
    ennemis = charger_ennemis()
    par_id = {spec.id: spec for spec in ennemis}

    assert par_id["ENM_BOSS_PIRATES"].emplacements == 2
    assert par_id["ENM_PAT_LE_PIRATE"].emplacements == 1


def test_image_case_module_recadre_le_module_principal():
    modules = charger_modules()
    principal = next(spec for spec in modules if spec.id == "MOD_1")

    image = image_case_module(principal)

    assert image != principal.image
    assert Path(image).is_file()


def test_image_case_module_inchangee_pour_un_module_equipable():
    modules = charger_modules()
    equipable = next(spec for spec in modules if spec.id != "MOD_1")

    assert image_case_module(equipable) == equipable.image
