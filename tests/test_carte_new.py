"""
Tests unitaires pour src/gameplay/carte_new.py (CarteNew, carte de la refonte) et
config/carte_new.json (source de verite des cartes revues).
"""

import json

import pytest

from src.gameplay.carte import RareteCarte
from src.gameplay.carte_new import (
    Camp,
    CarteNew,
    CategorieCarte,
    CibleCarteNew,
    Cumul,
    Effet,
    FiltreCartes,
    NatureEffet,
    PorteeEffet,
    FICHIER_CARTES_NEW,
    appliquer_repetition,
    charger_cartes_new,
)


def _cartes() -> dict[str, CarteNew]:
    """Cartes de config/carte_new.json, par nom (nouvelles instances a chaque appel)."""
    return {carte.nom: carte for carte in charger_cartes_new().values()}


def _entree(id_carte: str) -> dict:
    """Entree brute d'une carte dans config/carte_new.json (pour fabriquer des variantes)."""
    return next(entree for entree in json.loads(FICHIER_CARTES_NEW.read_text(encoding="utf-8"))["cartes"]
                if entree["id"] == id_carte)


def _carte_simple(**champs) -> CarteNew:
    valeurs = dict(
        id="TEST", nom="Test", image="test.png", rarete=RareteCarte.COMMUNE,
        categorie=CategorieCarte.ATTAQUE, cible=CibleCarteNew.ENNEMI_UNIQUE, cout=1,
        description="Inflige {degats} degats", valeurs={"degats": 5}, effets=(Effet(NatureEffet.DEGATS, "degats"),),
    )
    valeurs.update(champs)
    return CarteNew(**valeurs)


# --- config/carte_new.json ---


def test_carte_new_json_contient_les_19_cartes_revues():
    cartes = charger_cartes_new()

    assert len(cartes) == 19
    assert all(carte.refonte for carte in cartes.values())


def test_jouable_suit_le_moteur_actuel():
    cartes = _cartes()

    assert cartes["Laser"].jouable and cartes["Blindage cible"].jouable
    assert not cartes["Missiles"].jouable and not cartes["Embrasement"].jouable


def test_description_affichee_remplace_les_valeurs_nommees():
    cartes = _cartes()

    assert cartes["Missiles"].description_affichee() == "Inflige 15 degats a un ennemi et 6 a tous les autres"
    assert cartes["Torpille"].description_affichee() == "Inflige 10 degats a la ligne avant et 8 a la ligne arriere"
    assert cartes["Laser"].description_affichee() == "Inflige 6 degats a un ennemi unique"
    assert cartes["Tir incendiaire"].description_affichee() == "Ajoute 4 points d’incendie sur la cible"
    assert cartes["Leurre"].description_affichee() == "Annule la prochaine attaque ciblant le module"


def test_les_effets_lisent_leur_valeur_sur_la_carte():
    missiles = _cartes()["Missiles"]

    assert [missiles.valeur_de(effet) for effet in missiles.effets] == [15, 6]
    assert missiles.effets[1].portee == PorteeEffet.AUTRES_ENNEMIS


# --- Verification des valeurs nommees ---


def test_valeur_inconnue_dans_un_effet_refusee():
    with pytest.raises(ValueError, match="inconnues"):
        _carte_simple(effets=(Effet(NatureEffet.DEGATS, "degats_cible"),), description="")


def test_valeur_inconnue_dans_la_description_refusee():
    with pytest.raises(ValueError, match="inconnues"):
        _carte_simple(description="Inflige {degat} degats")  # coquille


def test_valeur_utilisee_par_aucun_effet_refusee():
    with pytest.raises(ValueError, match="aucun effet"):
        _carte_simple(valeurs={"degats": 5, "oubli": 3})


def test_effet_sans_valeur_seulement_pour_les_natures_sans_valeur():
    assert Effet(NatureEffet.ANNULATION_PROCHAINE_ATTAQUE).valeur is None
    with pytest.raises(ValueError):
        Effet(NatureEffet.DEGATS)
    with pytest.raises(ValueError):
        Effet(NatureEffet.ANNULATION_PROCHAINE_ATTAQUE, "x")


def test_duree_nommee_seulement_pour_un_effet_a_duree():
    breche = _carte_simple(
        categorie=CategorieCarte.DEBUFF,
        description="+{vulnerabilite} % de degats subis pendant {vulnerabilite_duree} tours",
        valeurs={"vulnerabilite": 100, "vulnerabilite_duree": 2},
        effets=(Effet(NatureEffet.VULNERABILITE, "vulnerabilite", duree="vulnerabilite_duree"),),
    )

    assert breche.description_affichee() == "+100 % de degats subis pendant 2 tours"
    assert breche.duree_de(breche.effets[0]) == 2
    with pytest.raises(ValueError):
        Effet(NatureEffet.BOUCLIER, "bouclier", duree="bouclier_duree")


# --- Cumul des effets ---


def test_l_incendie_et_le_bouclier_baissent_de_un_par_tour():
    """Decisions utilisateur : incendie = poison de Slay the Spire ; bouclier -1 par tour, sans duree."""
    cartes = _cartes()

    assert cartes["Embrasement"].effets[0].cumul == Cumul.INTENSITE_DECROISSANTE
    assert cartes["Bouclier"].effets[0].cumul == Cumul.INTENSITE_DECROISSANTE
    assert cartes["Laser"].effets[0].cumul == Cumul.INSTANTANE


# --- Lancements et repetition ("lancee X fois de plus") ---


def test_une_carte_est_lancee_une_fois_par_defaut_ou_plus_si_precise():
    laser = _cartes()["Laser"]
    double_laser = CarteNew.depuis_dict(dict(_entree("CRT_7"), lancements=2))

    assert laser.lancements_base == laser.lancements_actuels == 1
    assert double_laser.lancements_base == double_laser.lancements_actuels == 2


def test_salve_laser_augmente_les_lancements_des_seuls_lasers_de_base_de_toutes_les_piles():
    cartes = _cartes()
    salve = cartes["Salve laser"]
    deck = [cartes["Laser"].copie() for _ in range(4)] + [cartes["Laser lourd"], cartes["Bouclier"]]

    modifiees = appliquer_repetition(salve, salve.effets[0], deck)

    assert modifiees == 4
    assert [carte.lancements_actuels for carte in deck] == [2, 2, 2, 2, 1, 1]
    assert [carte.lancements_base for carte in deck] == [1] * 6  # la valeur du modele ne change pas
    assert deck[0].copie().lancements_actuels == 1  # un nouvel exemplaire repart de la base


def test_les_repetitions_se_cumulent_pour_le_combat():
    cartes = _cartes()
    laser, reparation, laser_percant = cartes["Laser"], cartes["Réparation"], cartes["Laser percant"]
    deck = [laser, reparation, laser_percant]

    appliquer_repetition(cartes["Salve laser"], cartes["Salve laser"].effets[0], deck)
    appliquer_repetition(cartes["Protocole d'urgence"], cartes["Protocole d'urgence"].effets[0], deck)

    assert (laser.lancements_actuels, reparation.lancements_actuels, laser_percant.lancements_actuels) == (3, 2, 1)
    assert cartes["Salve laser"].effets[0].cumul == Cumul.INTENSITE_SANS_DECROISSANCE


def test_bouclier_stabilise_double_le_bouclier_de_base():
    cartes = _cartes()
    stabilise = cartes["Bouclier stabilise"]

    appliquer_repetition(stabilise, stabilise.effets[0], [cartes["Bouclier"], cartes["Blindage cible"]])

    assert (cartes["Bouclier"].lancements_actuels, cartes["Blindage cible"].lancements_actuels) == (2, 1)


def test_seul_un_effet_repetition_modifie_les_lancements():
    laser = _cartes()["Laser"]
    with pytest.raises(ValueError):
        appliquer_repetition(laser, laser.effets[0], [laser])


# --- Cible ---


def test_cible_camp_et_case_cliquee():
    assert CibleCarteNew("Ennemi Tous").camp == Camp.ENNEMI
    assert CibleCarteNew("Module Principal").camp == Camp.JOUEUR
    assert CibleCarteNew.ENNEMI_UNIQUE.depend_de_la_case_cliquee
    assert CibleCarteNew.ENNEMI_COLONNE.depend_de_la_case_cliquee
    assert not CibleCarteNew.ENNEMI_TOUS.depend_de_la_case_cliquee
    assert not CibleCarteNew.MODULE_PRINCIPAL.depend_de_la_case_cliquee


# --- Munitions, valeurs et exemplaires ---


def test_munitions_consommees_jusqu_a_epuisement():
    reparation = _cartes()["Réparation"]

    assert reparation.munitions_restantes == 2
    assert not reparation.consommer_munition()
    assert reparation.consommer_munition()
    assert reparation.est_epuisee


def test_carte_sans_munition_jamais_epuisee():
    laser = _cartes()["Laser"]

    for _ in range(5):
        assert not laser.consommer_munition()


def test_valeurs_actuelles_modifiables_sans_toucher_au_modele():
    """Base d'un futur bonus ("+2 aux degats des cartes a cible unique") : propre a l'exemplaire."""
    laser = _cartes()["Laser"]

    laser.valeurs_actuelles["degats"] += 2

    assert laser.valeur_de(laser.effets[0]) == 8
    assert laser.description_affichee() == "Inflige 8 degats a un ennemi unique"
    assert laser.valeurs["degats"] == 6
    assert laser.copie().valeur_de(laser.effets[0]) == 6  # un nouvel exemplaire repart du modele


def test_copie_donne_un_exemplaire_independant_rattache_si_demande():
    reparation = _cartes()["Réparation"]
    reparation.consommer_munition()

    copie = reparation.copie()
    rattachee = reparation.copie("M3")

    assert copie is not reparation and copie.munitions_restantes == 2
    assert rattachee.exemplaire_module == "M3" and reparation.exemplaire_module is None
    assert rattachee.munitions_restantes == 2
    assert rattachee.copie().exemplaire_module == "M3"  # sans argument, garde son rattachement


# --- Module detruit (mot-cle Persistante) ---


def test_seule_une_carte_persistante_reste_jouable_si_son_module_est_detruit():
    assert not _carte_simple().jouable_si_module_detruit()
    assert _carte_simple(persistante=True).jouable_si_module_detruit()


def test_persistante_lue_depuis_le_json():
    laser = _cartes()["Laser"]

    assert CarteNew.depuis_dict(dict(_entree("CRT_7"), persistante=True)).persistante
    assert not laser.persistante


# --- Validations ---


@pytest.mark.parametrize(
    "champs",
    [
        {"cout": -1},
        {"effets": ()},
        {"munitions_base": 0},
        {"lancements_base": 0},
        {"valeurs": {"degats": -1}},
        {"cible": CibleCarteNew.MODULE_UNIQUE,
         "effets": (Effet(NatureEffet.DEGATS, "degats", PorteeEffet.AUTRES_ENNEMIS),)},
        {"cible": CibleCarteNew.ENNEMI_TOUS,
         "effets": (Effet(NatureEffet.DEGATS, "degats", PorteeEffet.AUTRES_ENNEMIS),)},
    ],
)
def test_carte_invalide_refusee(champs):
    with pytest.raises(ValueError):
        _carte_simple(**champs)


def test_effet_invalide_refuse():
    with pytest.raises(ValueError):
        Effet(NatureEffet.REPETITION, "repetitions")  # filtre manquant
    with pytest.raises(ValueError):
        Effet(NatureEffet.DEGATS, "degats", filtre=FiltreCartes(nom="Laser"))  # filtre interdit
    with pytest.raises(ValueError):
        FiltreCartes()  # aucun critere
