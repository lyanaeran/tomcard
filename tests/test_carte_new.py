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
    Effet,
    FiltreCartes,
    NatureEffet,
    PorteeEffet,
    FICHIER_CARTES_NEW,
    appliquer_repetition,
    charger_cartes_new,
)
from src.gameplay.statut_new import Statut


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


def test_les_19_cartes_revues_sont_jouables():
    # Decision 5 du branchement (refonte-branchement.md 2) : toutes proposables en recompense
    assert all(carte.jouable for carte in charger_cartes_new().values())


def test_description_affichee_remplace_les_valeurs_nommees():
    cartes = _cartes()

    assert cartes["Missiles"].description_affichee() == "Inflige 15 dégâts à un ennemi et 6 à tous les autres"
    assert cartes["Torpille"].description_affichee() == "Inflige 10 dégâts à la ligne avant et 8 à la ligne arrière"
    assert cartes["Laser"].description_affichee() == "Inflige 6 dégâts à un ennemi unique"
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


# --- Statuts poses (regles dans statut_new.py) ---


def test_bouclier_incendie_et_leurre_posent_le_statut_correspondant():
    """Une seule source pour les regles de cumul et d'extinction : statut_new.py."""
    cartes = _cartes()

    assert cartes["Embrasement"].effets[0].nature.statut_pose == Statut.INCENDIE
    assert cartes["Bouclier"].effets[0].nature.statut_pose == Statut.BOUCLIER
    assert NatureEffet.ANNULATION_PROCHAINE_ATTAQUE.statut_pose == Statut.LEURRE
    assert cartes["Laser"].effets[0].nature.statut_pose is None


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

    modifiees = appliquer_repetition(salve.effets[0], salve.valeur_de(salve.effets[0]), deck)

    assert modifiees == 4
    assert [carte.lancements_actuels for carte in deck] == [2, 2, 2, 2, 1, 1]
    assert [carte.lancements_base for carte in deck] == [1] * 6  # la valeur du modele ne change pas
    assert deck[0].copie().lancements_actuels == 1  # un nouvel exemplaire repart de la base


def test_les_repetitions_se_cumulent_pour_le_combat():
    cartes = _cartes()
    laser, reparation, laser_percant = cartes["Laser"], cartes["Réparation"], cartes["Laser perçant"]
    deck = [laser, reparation, laser_percant]

    for nom in ("Salve laser", "Protocole d'urgence"):
        effet = cartes[nom].effets[0]
        appliquer_repetition(effet, cartes[nom].valeur_de(effet), deck)

    assert (laser.lancements_actuels, reparation.lancements_actuels, laser_percant.lancements_actuels) == (3, 2, 1)


def test_bouclier_stabilise_double_le_bouclier_de_base():
    cartes = _cartes()
    stabilise = cartes["Bouclier stabilisé"]

    effet = stabilise.effets[0]
    appliquer_repetition(effet, stabilise.valeur_de(effet), [cartes["Bouclier"], cartes["Blindage ciblé"]])

    assert (cartes["Bouclier"].lancements_actuels, cartes["Blindage ciblé"].lancements_actuels) == (2, 1)


def test_seul_un_effet_repetition_modifie_les_lancements():
    laser = _cartes()["Laser"]
    with pytest.raises(ValueError):
        appliquer_repetition(laser.effets[0], 1, [laser])


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
    assert laser.description_affichee() == "Inflige 8 dégâts à un ennemi unique"
    assert laser.valeurs["degats"] == 6
    assert laser.copie().valeur_de(laser.effets[0]) == 6  # un nouvel exemplaire repart du modele


def test_la_copie_ne_partage_aucun_dictionnaire_de_valeurs():
    laser = _cartes()["Laser"]
    copie = laser.copie()

    copie.valeurs["degats"] = 9
    copie.valeurs_actuelles["degats"] = 11

    assert laser.valeurs["degats"] == 6 and laser.valeurs_actuelles["degats"] == 6
    assert copie.effets is laser.effets  # partage voulu : les Effet sont figes


def test_le_filtre_vise_une_carte_par_son_id_pas_par_son_nom():
    cartes = _cartes()
    filtre = cartes["Salve laser"].effets[0].filtre
    laser_renomme = CarteNew.depuis_dict(dict(_entree("CRT_7"), nom="Laser léger"))

    assert filtre.correspond(laser_renomme)
    assert not filtre.correspond(cartes["Laser lourd"])


@pytest.mark.parametrize(
    "modification",
    [
        lambda entree: entree.update(persistant=True),  # faute de frappe sur une cle de carte
        lambda entree: entree["effets"][0].update(portée="CIBLE"),  # cle d'effet inconnue
    ],
)
def test_une_cle_inconnue_dans_le_json_est_refusee(modification):
    entree = json.loads(json.dumps(_entree("CRT_7")))
    modification(entree)

    with pytest.raises(ValueError, match="cles inconnues"):
        CarteNew.depuis_dict(entree)


@pytest.mark.parametrize(
    "modification, message",
    [
        (lambda entree: entree.pop("cout"), "cle manquante ou texte inconnu 'cout'"),
        (lambda entree: entree["effets"][0].update(nature="DEGAT"), "cle manquante ou texte inconnu 'DEGAT'"),
        (lambda entree: entree.update(cible="Ennemi unique"), "is not a valid CibleCarteNew"),
        (lambda entree: entree["effets"][0].pop("valeur"), "valeur nommee manquante"),
    ],
)
def test_une_erreur_de_lecture_du_json_indique_la_carte(modification, message):
    entree = json.loads(json.dumps(_entree("CRT_13")))
    modification(entree)

    with pytest.raises(ValueError, match="^Carte CRT_13 : ") as erreur:
        CarteNew.depuis_dict(entree)
    assert message in str(erreur.value)


def test_une_cle_inconnue_dans_un_filtre_est_refusee():
    entree = json.loads(json.dumps(_entree("CRT_49")))
    entree["effets"][0]["filtre"]["nom"] = "Laser"  # ancien critere par nom

    with pytest.raises(ValueError, match="cles inconnues"):
        CarteNew.depuis_dict(entree)


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
        Effet(NatureEffet.DEGATS, "degats", filtre=FiltreCartes(id="CRT_7"))  # filtre interdit
    with pytest.raises(ValueError):
        FiltreCartes()  # aucun critere


def test_chaque_portee_declare_le_camp_qu_elle_touche():
    assert PorteeEffet.CIBLE.camp is None
    assert all(portee.camp == Camp.ENNEMI for portee in PorteeEffet if portee != PorteeEffet.CIBLE)
