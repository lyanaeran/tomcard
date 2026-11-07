"""
Tests unitaires pour src/gameplay/carte_new.py (CarteNew, carte de la refonte).
"""

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
)

MP, LDM = "Module principal", "Lanceur de missiles"


def _carte(id_carte, nom, rarete, categorie, cible, cout, effets, description, munition=None, module=MP):
    return {
        "id": id_carte, "nom": nom, "image": "test.png", "module_origine": module, "rarete": rarete,
        "categorie": categorie, "cible": cible, "cout": cout, "munition": munition,
        "description": description, "effets": effets,
    }


# Les 19 cartes revues (colonne "Refonte" de specs/cartes.xlsx), dans le format JSON propose
REGISTRE_REFONTE = [
    _carte("CRT_7", "Laser", "Base", "Attaque", "Ennemi Unique", 1, [{"nature": "DEGATS", "valeur": 6}],
           "Inflige X degats a un ennemi unique"),
    _carte("CRT_10", "Bouclier", "Base", "Defense", "Module Unique", 1, [{"nature": "BOUCLIER", "valeur": 3}],
           "Bouclier de X sur un module unique"),
    _carte("CRT_11", "Proteger le vaisseau", "Base", "Defense", "Module Principal", 1,
           [{"nature": "BOUCLIER", "valeur": 5}], "Bouclier de X sur le module principal"),
    _carte("CRT_12", "Reparation", "Base", "Reparation", "Module Principal", 1,
           [{"nature": "REPARATION", "valeur": 8}], "Repare le module principal pour X", munition=2),
    _carte("CRT_8", "Laser percant", "Commune", "Attaque", "Ennemi Colonne", 2, [{"nature": "DEGATS", "valeur": 8}],
           "Inflige X degats a la colonne ciblee"),
    _carte("CRT_45", "Tir incendiaire", "Commune", "Attaque", "Ennemi Unique", 2, [{"nature": "INCENDIE", "valeur": 4}],
           "Ajoute X points d’incendie sur la cible", munition=3),
    _carte("CRT_46", "Blindage cible", "Commune", "Defense", "Module Unique", 2,
           [{"nature": "BOUCLIER", "valeur": 6, "duree": 3}], "Bouclier de X sur un module unique pendant Y tours.",
           munition=3),
    _carte("CRT_47", "Laser lourd", "Commune", "Attaque", "Ennemi Unique", 1, [{"nature": "DEGATS", "valeur": 12}],
           "Inflige X degats a un ennemi unique"),
    _carte("CRT_48", "Bouclier stabilise", "Rare", "Buff", "Module Principal", 3,
           [{"nature": "REPETITION", "valeur": 0, "filtre": {"nom": "Bouclier", "rarete": "Base"}}],
           "Les Boucliers de base sont lancés X fois de plus.", munition=1),
    _carte("CRT_49", "Salve laser", "Rare", "Buff", "Module Tous", 2,
           [{"nature": "REPETITION", "valeur": 1, "filtre": {"nom": "Laser", "rarete": "Base"}}],
           "Les Laser de base sont lances X fois de plus.", munition=2),
    _carte("CRT_50", "Protocole d'urgence", "Legendaire", "Buff", "Module Tous", 3,
           [{"nature": "REPETITION", "valeur": 1, "filtre": {"rarete": "Base"}}],
           "Les cartes de bases sont lancees X fois de plus.", munition=3),
    _carte("CRT_13", "Missiles", "Commune", "Attaque", "Ennemi Unique", 2,
           [{"nature": "DEGATS", "valeur": 15}, {"nature": "DEGATS", "valeur": 6, "portee": "AUTRES_ENNEMIS"}],
           "Inflige X degats a un ennemi et Y a tous les autres", module=LDM),
    _carte("CRT_14", "Torpille", "Commune", "Attaque", "Ennemi Tous", 2,
           [{"nature": "DEGATS", "valeur": 10, "portee": "COLONNE_AVANT_ENNEMIE"},
            {"nature": "DEGATS", "valeur": 8, "portee": "COLONNE_ARRIERE_ENNEMIE"}],
           "Inflige X degats a la ligne avant et Y a la ligne arriere", module=LDM),
    _carte("CRT_9", "Bombardement", "Commune", "Attaque", "Ennemi Tous", 1, [{"nature": "DEGATS", "valeur": 6}],
           "Inflige X degats a tous les ennemis", module=LDM),
    _carte("CRT_16", "Ligne arriere", "Commune", "Attaque", "Ennemi Arriere", 1, [{"nature": "DEGATS", "valeur": 8}],
           "Inflige X degats a tous les ennemis de la ligne arriere", module=LDM),
    _carte("CRT_15", "Ciel de missiles", "Rare", "Attaque", "Ennemi Tous", 1, [{"nature": "DEGATS", "valeur": 8}],
           "Inflige X degats a tous les ennemis", module=LDM),
    _carte("CRT_17", "Embrasement", "Rare", "Attaque", "Ennemi Unique", 2, [{"nature": "INCENDIE", "valeur": 8}],
           "Ajoute X points d’incendie à un ennemi", module=LDM),
    _carte("CRT_18", "Leurre", "Rare", "Defense", "Module Unique", 1,
           [{"nature": "ANNULATION_PROCHAINE_ATTAQUE", "valeur": 0}],
           "Annule la prochaine attaque ciblant le module", module=LDM),
    _carte("CRT_19", "Guerre nucleaire", "Legendaire", "Attaque", "Ennemi Tous", 3, [{"nature": "INCENDIE", "valeur": 8}],
           "Ajoute X points d’incendie à tous les ennemis", module=LDM),
]


def _cartes() -> dict[str, CarteNew]:
    return {entree["nom"]: CarteNew.depuis_dict(entree) for entree in REGISTRE_REFONTE}


def _carte_simple(**champs) -> CarteNew:
    valeurs = dict(
        id="TEST", nom="Test", image="test.png", module_origine=MP, rarete=RareteCarte.COMMUNE,
        categorie=CategorieCarte.ATTAQUE, cible=CibleCarteNew.ENNEMI_UNIQUE, cout=1,
        effets=(Effet(NatureEffet.DEGATS, 5),),
    )
    valeurs.update(champs)
    return CarteNew(**valeurs)


# --- Couverture du registre de la refonte ---


def test_les_19_cartes_revues_s_expriment_avec_carte_new():
    cartes = _cartes()

    assert len(cartes) == 19


def test_description_affichee_remplace_x_et_y():
    cartes = _cartes()

    assert cartes["Missiles"].description_affichee() == "Inflige 15 degats a un ennemi et 6 a tous les autres"
    assert cartes["Torpille"].description_affichee() == "Inflige 10 degats a la ligne avant et 8 a la ligne arriere"
    assert cartes["Blindage cible"].description_affichee() == "Bouclier de 6 sur un module unique pendant 3 tours."
    assert cartes["Laser"].description_affichee() == "Inflige 6 degats a un ennemi unique"
    assert cartes["Tir incendiaire"].description_affichee() == "Ajoute 4 points d’incendie sur la cible"


def test_x_et_y_suivent_les_colonnes_du_registre():
    cartes = _cartes()

    assert (cartes["Missiles"].x, cartes["Missiles"].y) == (15, 6)
    assert (cartes["Blindage cible"].x, cartes["Blindage cible"].y) == (6, 3)
    assert (cartes["Laser lourd"].x, cartes["Laser lourd"].y) == (12, None)


def test_vers_dict_puis_depuis_dict_redonne_la_meme_carte():
    for carte in _cartes().values():
        relue = CarteNew.depuis_dict(carte.vers_dict())
        assert relue.vers_dict() == carte.vers_dict()


# --- Cumul des effets ---


def test_l_incendie_s_additionne_et_decroit_de_un_par_tour():
    """Decision utilisateur : incendie = poison de Slay the Spire, decroissance -1 par tour."""
    assert _cartes()["Embrasement"].effets[0].cumul == Cumul.INTENSITE_DECROISSANTE


def test_les_degats_sont_instantanes_et_le_bouclier_suit_sa_propre_regle():
    cartes = _cartes()

    assert cartes["Laser"].effets[0].cumul == Cumul.INSTANTANE
    assert cartes["Bouclier"].effets[0].cumul == Cumul.BOUCLIER


# --- Repetition ("lancee X fois de plus") ---


def test_salve_laser_ne_vise_que_le_laser_de_base():
    cartes = _cartes()
    salve = cartes["Salve laser"].effets

    assert cartes["Laser"].lancements_supplementaires(salve) == 1
    assert cartes["Laser lourd"].lancements_supplementaires(salve) == 0
    assert cartes["Bouclier"].lancements_supplementaires(salve) == 0


def test_protocole_d_urgence_vise_toutes_les_cartes_de_base_et_se_cumule_avec_salve_laser():
    cartes = _cartes()
    actifs = cartes["Protocole d'urgence"].effets + cartes["Salve laser"].effets

    assert cartes["Laser"].lancements_supplementaires(actifs) == 2
    assert cartes["Reparation"].lancements_supplementaires(actifs) == 1
    assert cartes["Laser percant"].lancements_supplementaires(actifs) == 0  # Commune


def test_bouclier_stabilise_vise_le_bouclier_de_base():
    cartes = _cartes()
    filtre = cartes["Bouclier stabilise"].effets[0].filtre

    assert filtre.correspond(cartes["Bouclier"])
    assert not filtre.correspond(cartes["Blindage cible"])


# --- Cible ---


def test_cible_camp_et_case_cliquee():
    assert CibleCarteNew("Ennemi Tous").camp == Camp.ENNEMI
    assert CibleCarteNew("Module Principal").camp == Camp.JOUEUR
    assert CibleCarteNew.ENNEMI_UNIQUE.depend_de_la_case_cliquee
    assert CibleCarteNew.ENNEMI_COLONNE.depend_de_la_case_cliquee
    assert not CibleCarteNew.ENNEMI_TOUS.depend_de_la_case_cliquee
    assert not CibleCarteNew.MODULE_PRINCIPAL.depend_de_la_case_cliquee


# --- Munitions et exemplaires ---


def test_munitions_consommees_jusqu_a_epuisement():
    reparation = _cartes()["Reparation"]

    assert reparation.munitions_restantes == 2
    assert not reparation.consommer_munition()
    assert reparation.consommer_munition()
    assert reparation.est_epuisee


def test_carte_sans_munition_jamais_epuisee():
    laser = _cartes()["Laser"]

    for _ in range(5):
        assert not laser.consommer_munition()


def test_copie_et_rattachement_donnent_des_exemplaires_independants():
    reparation = _cartes()["Reparation"]
    reparation.consommer_munition()

    copie = reparation.copie()
    rattachee = reparation.rattachee_a("avant_gauche")

    assert copie is not reparation and copie.munitions_restantes == 2
    assert rattachee.emplacement == "avant_gauche" and reparation.emplacement is None
    assert rattachee.munitions_restantes == 2


# --- Module detruit (mot-cle Persistante) ---


def test_seule_une_carte_persistante_reste_jouable_si_son_module_est_detruit():
    assert not _carte_simple().jouable_si_module_detruit()
    assert _carte_simple(persistante=True).jouable_si_module_detruit()


def test_persistante_lue_depuis_le_json():
    entree = dict(REGISTRE_REFONTE[0], persistante=True)

    assert CarteNew.depuis_dict(entree).persistante
    assert not CarteNew.depuis_dict(REGISTRE_REFONTE[0]).persistante


# --- Validations ---


@pytest.mark.parametrize(
    "champs",
    [
        {"cout": -1},
        {"effets": ()},
        {"munitions_max": 0},
        {"cible": CibleCarteNew.MODULE_UNIQUE, "effets": (Effet(NatureEffet.DEGATS, 3, PorteeEffet.AUTRES_ENNEMIS),)},
        {"cible": CibleCarteNew.ENNEMI_TOUS, "effets": (Effet(NatureEffet.DEGATS, 3, PorteeEffet.AUTRES_ENNEMIS),)},
    ],
)
def test_carte_invalide_refusee(champs):
    with pytest.raises(ValueError):
        _carte_simple(**champs)


def test_effet_invalide_refuse():
    with pytest.raises(ValueError):
        Effet(NatureEffet.DEGATS, -1)
    with pytest.raises(ValueError):
        Effet(NatureEffet.BOUCLIER, 5, duree=0)
    with pytest.raises(ValueError):
        Effet(NatureEffet.REPETITION, 1)  # filtre manquant
    with pytest.raises(ValueError):
        Effet(NatureEffet.DEGATS, 1, filtre=FiltreCartes(nom="Laser"))  # filtre interdit
    with pytest.raises(ValueError):
        FiltreCartes()  # aucun critere
