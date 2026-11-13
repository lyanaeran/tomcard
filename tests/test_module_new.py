"""
Tests unitaires pour src/gameplay/module_new.py (ModuleNew, module de la refonte) et
config/module_new.json.
"""

import json

import pytest

from src.gameplay.carte_new import charger_cartes_new
from src.gameplay.module_new import FICHIER_MODULES_NEW, ModuleNew, charger_modules_new
from src.gameplay.statut_new import Statut


def _entree(id_module: str) -> dict:
    """Entree brute d'un module dans config/module_new.json (pour fabriquer des variantes)."""
    entrees = json.loads(FICHIER_MODULES_NEW.read_text(encoding="utf-8"))["modules"]
    return json.loads(json.dumps(next(entree for entree in entrees if entree["id"] == id_module)))


def _exemplaires():
    """Principal (M1, base) et Lanceur de missiles (M2, avant gauche), exemplaires neufs."""
    modules = charger_modules_new()
    return modules["MOD_1"].nouvel_exemplaire("M1", "base"), modules["MOD_2"].nouvel_exemplaire("M2", "avant_gauche")


# --- config/module_new.json ---


def test_module_new_json_contient_les_deux_modules_jouables_avec_les_pv_provisoires():
    modules = charger_modules_new()

    assert sorted(modules) == ["MOD_1", "MOD_2"]
    assert all(module.jouable and module.refonte for module in modules.values())
    assert (modules["MOD_1"].pv_max_base, modules["MOD_2"].pv_max_base) == (60, 20)
    assert modules["MOD_1"].principal and not modules["MOD_2"].principal


def test_les_cartes_des_modules_existent_dans_carte_new_json():
    cartes = charger_cartes_new()

    for module in charger_modules_new().values():
        assert set(module.cartes) <= cartes.keys(), module.id


def test_chaque_carte_revue_appartient_a_un_module():
    ids_modules = {id_carte for module in charger_modules_new().values() for id_carte in module.cartes}

    assert ids_modules == charger_cartes_new().keys()


# --- Exemplaires ---


def test_pv_au_prochain_combat_principal_sauvegardes_secondaire_plein():
    principal, lanceur = _exemplaires()
    principal.pv, lanceur.pv = 35, 3

    assert principal.pv_au_prochain_combat == principal.copie_pour_combat().pv_combat == 35
    assert lanceur.pv_au_prochain_combat == lanceur.copie_pour_combat().pv_combat == lanceur.pv_max


def test_nouvel_exemplaire_part_des_pv_de_base_et_du_palier_1():
    principal, lanceur = _exemplaires()

    assert (principal.exemplaire, principal.emplacement, principal.pv_max, principal.pv) == ("M1", "base", 60, 60)
    assert (lanceur.exemplaire, lanceur.pv_max, lanceur.niveau_maj) == ("M2", 20, 1)
    assert principal.pv_combat is None  # hors combat


def test_deux_exemplaires_du_meme_module_sont_distincts():
    lanceur = charger_modules_new()["MOD_2"]

    assert lanceur.nouvel_exemplaire("M2", "avant_gauche") != lanceur.nouvel_exemplaire("M3", "avant_droite")


# --- Copie de combat ---


def test_copie_de_combat_principal_garde_ses_pv_secondaire_repart_au_maximum():
    principal, lanceur = _exemplaires()
    principal.pv, lanceur.pv = 35, 3  # les PV d'un secondaire ne comptent pas

    assert principal.copie_pour_combat().pv_combat == 35
    assert lanceur.copie_pour_combat().pv_combat == 20


def test_le_combat_ne_modifie_jamais_le_module_de_la_partie():
    principal, _ = _exemplaires()
    combat = principal.copie_pour_combat()

    combat.subir_degats(15)
    combat.statuts.ajouter(Statut.BOUCLIER, 4)
    combat.statuts.ajouter(Statut.INCENDIE, 2)

    assert principal.pv == 60 and principal.statuts.intensites == {}
    assert principal.pv_combat is None


def test_fin_de_combat_seuls_les_pv_du_principal_sont_reportes():
    principal, lanceur = _exemplaires()
    combat_principal, combat_lanceur = principal.copie_pour_combat(), lanceur.copie_pour_combat()
    combat_principal.subir_degats(12)
    combat_lanceur.subir_degats(15)

    principal.reporter_combat(combat_principal)
    lanceur.reporter_combat(combat_lanceur)

    assert principal.pv == 48
    assert lanceur.pv == 20 and lanceur.copie_pour_combat().pv_combat == 20


def test_un_etat_de_combat_ne_passe_pas_d_un_combat_a_l_autre():
    principal, _ = _exemplaires()
    premier = principal.copie_pour_combat()
    premier.statuts.ajouter(Statut.BOUCLIER, 10)
    premier.statuts.ajouter(Statut.LEURRE, 1)

    second = principal.copie_pour_combat()

    assert second.statuts.intensites == {}


# --- Regles de combat ---


def test_le_bouclier_absorbe_avant_les_pv_et_baisse_de_un_a_la_fin_du_tour_ennemi():
    _, lanceur = _exemplaires()
    combat = lanceur.copie_pour_combat()
    combat.statuts.ajouter(Statut.BOUCLIER, 5)

    combat.subir_degats(7)
    assert (combat.statuts[Statut.BOUCLIER], combat.pv_combat) == (0, 18)

    combat.statuts.ajouter(Statut.BOUCLIER, 3)
    combat.fin_du_tour_ennemi()
    assert combat.statuts[Statut.BOUCLIER] == 2


def test_l_incendie_frappe_le_module_a_la_fin_du_tour_ennemi():
    _, lanceur = _exemplaires()
    combat = lanceur.copie_pour_combat()
    combat.statuts.ajouter(Statut.INCENDIE, 3)

    combat.fin_du_tour_ennemi()

    assert (combat.pv_combat, combat.statuts[Statut.INCENDIE]) == (17, 2)


def test_le_leurre_annule_une_seule_attaque():
    _, lanceur = _exemplaires()
    combat = lanceur.copie_pour_combat()
    combat.statuts.ajouter(Statut.LEURRE, 1)

    combat.subir_degats(50)
    assert combat.pv_combat == 20 and combat.statuts[Statut.LEURRE] == 0
    combat.subir_degats(25)
    assert combat.est_detruit()


def test_la_reparation_ne_depasse_pas_le_pv_max():
    principal, _ = _exemplaires()
    combat = principal.copie_pour_combat()
    combat.subir_degats(10)

    combat.reparer(25)

    assert combat.pv_combat == 60


# --- Lecture du JSON ---


def test_une_cle_inconnue_est_refusee():
    entree = _entree("MOD_2")
    entree["pv_maxi"] = 20

    with pytest.raises(ValueError, match="^Module MOD_2 : cles inconnues"):
        ModuleNew.depuis_dict(entree)


def test_une_cle_manquante_est_signalee_avec_l_id_du_module():
    entree = _entree("MOD_2")
    del entree["pv_max"]

    with pytest.raises(ValueError, match="^Module MOD_2 : cle manquante 'pv_max'"):
        ModuleNew.depuis_dict(entree)


def test_il_faut_exactement_un_module_principal(tmp_path):
    entrees = [_entree("MOD_1"), _entree("MOD_2")]
    entrees[1]["principal"] = True
    fichier = tmp_path / "module_new.json"
    fichier.write_text(json.dumps({"modules": entrees}), encoding="utf-8")

    with pytest.raises(ValueError, match="exactement un module principal"):
        charger_modules_new(fichier)


@pytest.mark.parametrize("champs", [{"pv_max_base": 0}, {"niveau_maj": 4}])
def test_module_invalide_refuse(champs):
    valeurs = dict(id="TEST", nom="Test", image="test.png", description="", pv_max_base=10)
    valeurs.update(champs)

    with pytest.raises(ValueError):
        ModuleNew(**valeurs)


# --- Corrections de la review de la PR #60 ---


def test_la_reparation_ne_ressuscite_pas_un_module_detruit():
    _, lanceur = _exemplaires()
    combat = lanceur.copie_pour_combat()
    combat.subir_degats(20)

    combat.reparer(5)

    assert combat.est_detruit() and combat.pv_combat == 0


def test_une_valeur_de_mauvais_type_est_signalee_avec_l_id_du_module():
    entree = _entree("MOD_2")
    entree["pv_max"] = "20"

    with pytest.raises(ValueError, match="^Module MOD_2 : "):
        ModuleNew.depuis_dict(entree)


def test_un_id_de_module_en_double_est_refuse(tmp_path):
    fichier = tmp_path / "module_new.json"
    fichier.write_text(json.dumps({"modules": [_entree("MOD_1"), _entree("MOD_2"), _entree("MOD_2")]}), encoding="utf-8")

    with pytest.raises(ValueError, match="MOD_2 en double"):
        charger_modules_new(fichier)


def test_les_methodes_de_combat_refusent_un_module_hors_combat():
    principal, _ = _exemplaires()

    with pytest.raises(ValueError, match="hors combat"):
        principal.subir_degats(5)
