"""
Tests unitaires pour src/gameplay/ennemi_new.py (EnnemiNew, ennemi de la refonte) et
config/ennemi_new.json.
"""

import json
from fractions import Fraction

import pytest

from src.gameplay.ennemi_new import (
    FICHIER_ENNEMIS_NEW, CibleEffetEnnemi, EffetEnnemi, EnnemiNew, NatureEffetEnnemi, ValeurEnnemi,
    charger_ennemis_new,
)


def _entree(id_ennemi: str) -> dict:
    """Entree brute d'un ennemi dans config/ennemi_new.json (pour fabriquer des variantes)."""
    entrees = json.loads(FICHIER_ENNEMIS_NEW.read_text(encoding="utf-8"))["ennemis"]
    return json.loads(json.dumps(next(entree for entree in entrees if entree["id"] == id_ennemi)))


def _en_combat(id_ennemi: str, coefficient=1) -> EnnemiNew:
    return charger_ennemis_new()[id_ennemi].pour_combat(coefficient)


# --- config/ennemi_new.json ---


def test_les_six_ennemis_actuels_sont_dans_le_json():
    ennemis = charger_ennemis_new()

    assert sorted(ennemis) == sorted([
        "ENM_PAT_LE_PIRATE", "ENM_LE_NETTOYEUR", "ENM_PETIT_JEAN", "ENM_LE_PUZZLE", "ENM_MIROIR", "ENM_BOSS_PIRATES",
    ])
    assert ennemis["ENM_BOSS_PIRATES"].emplacements == 2


def test_les_ids_et_images_sont_ceux_de_l_ancien_format():
    anciens = {entree["id"]: entree for entree in json.loads((FICHIER_ENNEMIS_NEW.parent / "ennemis.json").read_text(encoding="utf-8"))["ennemis"]}

    for ennemi in charger_ennemis_new().values():
        assert ennemi.image == anciens[ennemi.id]["image"]
        assert ennemi.pv_base == anciens[ennemi.id]["points_de_vie"]


# --- Valeurs : augmentation et coefficient (specs/refonte-ennemis.md 3.3, 3.4) ---


def test_exemple_de_la_spec_6_plus_1_tous_les_2_tours_coefficient_1_5():
    valeur = ValeurEnnemi(base=6, augmentation=1, tous_les=2)

    assert [valeur.au_tour(tour, Fraction("1.5")) for tour in range(1, 6)] == [9, 9, 10, 10, 12]


def test_une_augmentation_tous_les_tours_suit_la_formule_de_l_utilisateur():
    valeur = ValeurEnnemi(base=5, augmentation=2)

    assert [valeur.au_tour(tour) for tour in range(1, 5)] == [5, 7, 9, 11]


def test_le_coefficient_s_applique_aux_pv_et_aux_valeurs_arrondi_a_l_inferieur():
    boss = _en_combat("ENM_BOSS_PIRATES", 1.5)

    assert (boss.pv_max, boss.pv) == (225, 225)
    assert boss.valeurs_actuelles == {"degats": 7, "bouclier": 15}


def test_le_coefficient_ne_souffre_pas_des_erreurs_d_arrondi_des_flottants():
    # 1.15 x 20 vaut 22.999999999999996 en flottants
    assert ValeurEnnemi(base=20).au_tour(1, Fraction("1.15")) == 23


def test_un_coefficient_inferieur_a_1_est_refuse():
    with pytest.raises(ValueError, match="au moins 1"):
        _en_combat("ENM_PAT_LE_PIRATE", 0.9)


def test_les_valeurs_montent_au_fil_des_tours():
    pat = _en_combat("ENM_PAT_LE_PIRATE")
    degats = []
    for _ in range(6):
        degats.append(pat.valeur("degats"))
        pat.passer_au_tour_suivant()

    assert degats == [5, 5, 5, 6, 6, 6]


def test_le_modele_n_est_jamais_modifie_par_le_combat():
    modele = charger_ennemis_new()["ENM_PETIT_JEAN"]
    combat = modele.pour_combat(2)
    combat.subir_degats(30)
    combat.passer_au_tour_suivant()
    combat.avancer_cycle()

    assert (modele.pv, modele.tour, modele.etape, modele.coefficient) == (None, 1, 0, 1)


# --- Cycle d'actions ---


def test_le_cycle_revient_a_la_premiere_etape():
    boss = _en_combat("ENM_BOSS_PIRATES")
    natures = []
    for _ in range(4):
        natures.append([effet.nature for effet in boss.etape_courante])
        boss.avancer_cycle()

    attaque, bouclier = NatureEffetEnnemi.ATTAQUE, NatureEffetEnnemi.BOUCLIER
    assert natures == [[attaque], [attaque], [attaque, bouclier], [attaque]]


def test_le_nettoyeur_attaque_deux_fois():
    (effet,) = _en_combat("ENM_LE_NETTOYEUR").etape_courante

    assert (effet.nature, effet.repetitions) == (NatureEffetEnnemi.ATTAQUE, 2)


# --- Combat ---


def test_le_bouclier_absorbe_puis_baisse_de_un_a_la_fin_du_tour_du_joueur():
    jean = _en_combat("ENM_PETIT_JEAN")
    jean.ajouter_bouclier(6)

    jean.subir_degats(4)
    jean.fin_du_tour_du_joueur()

    assert (jean.pv, jean.bouclier) == (100, 1)


def test_l_incendie_frappe_avant_la_baisse_du_bouclier_et_baisse_de_un():
    pat = _en_combat("ENM_PAT_LE_PIRATE")
    pat.ajouter_bouclier(3)
    pat.ajouter_incendie(4)

    pat.fin_du_tour_du_joueur()
    assert (pat.pv, pat.bouclier, pat.incendie) == (49, 0, 3)

    pat.fin_du_tour_du_joueur()
    assert (pat.pv, pat.incendie) == (46, 2)


def test_le_renvoi_renvoie_jusqu_a_sa_valeur_et_le_protege_encaisse_le_reste():
    pat = _en_combat("ENM_PAT_LE_PIRATE")
    pat.poser_renvoi(5)

    assert pat.subir_degats(3) == 3 and pat.pv == 50
    assert pat.subir_degats(6) == 2 and pat.pv == 46
    assert pat.subir_degats(4) == 0 and pat.pv == 42


def test_le_renvoi_ne_se_cumule_pas_et_dure_jusqu_a_la_fin_du_tour_du_joueur():
    pat = _en_combat("ENM_PAT_LE_PIRATE")
    pat.poser_renvoi(5)
    pat.poser_renvoi(5)
    assert pat.renvoi == 5

    pat.fin_du_tour_du_joueur()
    assert pat.subir_degats(6) == 0 and pat.pv == 44


def test_l_ennemi_est_detruit_a_zero_pv():
    nettoyeur = _en_combat("ENM_LE_NETTOYEUR")

    nettoyeur.subir_degats(40)

    assert nettoyeur.pv == 0 and nettoyeur.est_detruit()


# --- Lecture du JSON ---


def test_une_cle_inconnue_est_refusee():
    entree = _entree("ENM_PAT_LE_PIRATE")
    entree["points_de_vie"] = 50

    with pytest.raises(ValueError, match="^Ennemi ENM_PAT_LE_PIRATE : cles inconnues"):
        EnnemiNew.depuis_dict(entree)


def test_une_valeur_citee_par_un_effet_doit_exister():
    entree = _entree("ENM_PAT_LE_PIRATE")
    entree["actions"][0][0]["valeur"] = "degat"

    with pytest.raises(ValueError, match="^Ennemi ENM_PAT_LE_PIRATE : valeur inconnue 'degat'"):
        EnnemiNew.depuis_dict(entree)


def test_une_erreur_dans_une_valeur_est_signalee_avec_l_id_de_l_ennemi():
    entree = _entree("ENM_PAT_LE_PIRATE")
    entree["valeurs"]["degats"]["tous_les"] = 0

    with pytest.raises(ValueError, match="^Ennemi ENM_PAT_LE_PIRATE : tous_les"):
        EnnemiNew.depuis_dict(entree)


def test_une_etape_vide_est_refusee():
    entree = _entree("ENM_PAT_LE_PIRATE")
    entree["actions"].append([])

    with pytest.raises(ValueError, match="au moins un effet"):
        EnnemiNew.depuis_dict(entree)


@pytest.mark.parametrize("nature, cible", [
    (NatureEffetEnnemi.ATTAQUE, CibleEffetEnnemi.SOI_MEME),
    (NatureEffetEnnemi.BOUCLIER, CibleEffetEnnemi.PROXIMITE),
])
def test_une_cible_du_mauvais_camp_est_refusee(nature, cible):
    with pytest.raises(ValueError, match="ne peut pas viser"):
        EffetEnnemi(nature, "degats", cible)
