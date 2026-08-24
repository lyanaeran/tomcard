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


def test_charger_modules_renvoie_6_modules_avec_images_existantes_et_cartes_connues():
    modules = charger_modules()
    ids_cartes_connus = set(charger_cartes())

    assert len(modules) == 6
    for module in modules:
        assert Path(module.image).is_file()
        assert set(module.cartes).issubset(ids_cartes_connus)
        assert len(module.cartes) > 0


def test_charger_ennemis_renvoie_3_ennemis_avec_images_existantes():
    ennemis = charger_ennemis()

    assert len(ennemis) == 3
    for ennemi in ennemis:
        assert Path(ennemi.image).is_file()
        assert ennemi.degats_attaque > 0
        assert ennemi.points_de_vie > 0


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
