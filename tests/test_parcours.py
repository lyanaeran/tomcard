"""
Tests unitaires pour la logique du parcours (src/gameplay/parcours.py).
"""

import dataclasses
import random

from src.gameplay.carte_new import RareteCarte, charger_cartes_new
from src.gameplay.module_new import charger_modules_new
from src.gameplay.parcours import (
    TypeAventure,
    TypeEtape,
    aleatoire_pour_niveau,
    est_niveau_boss,
    modules_equipables,
    pool_module,
    pool_toutes_cartes,
    tirer_candidats_carte_module,
    tirer_candidats_module,
    tirer_candidats_recompense,
    tirer_carte_deck,
    tirer_carte_recompense,
    tirer_propositions_niveau,
    tirer_rarete_recompense,
    tirer_type_aventure,
    tirer_type_etape,
)

class _AleatoireFixe:
    """Stub deterministe : random() renvoie toujours la meme valeur, choice() prend toujours
    le premier element, randrange() renvoie toujours le meme index - pour tester precisement les
    bornes de tirer_rarete_recompense/tirer_type_etape et le remplacement dans
    tirer_propositions_niveau."""

    def __init__(self, valeur_random: float, index_randrange: int = 0):
        self._valeur = valeur_random
        self._index = index_randrange

    def random(self) -> float:
        return self._valeur

    def choice(self, sequence):
        return sequence[0]

    def randrange(self, stop):
        return self._index


def _modules_fictifs(nombre: int = 4):
    """Modeles de modules : le principal, le Lanceur, et `nombre` copies jouables du Lanceur sous
    d'autres ids, pour tester le tirage parmi plusieurs modules (un seul secondaire jouable pour
    l'instant)."""
    modeles = charger_modules_new()
    lanceur = modeles["MOD_2"]
    fictifs = [dataclasses.replace(lanceur, id=f"MOD_TEST_{i}") for i in range(nombre)]
    sans_cartes = dataclasses.replace(lanceur, id="MOD_SANS_CARTE", cartes=())
    non_jouable = dataclasses.replace(lanceur, id="MOD_NON_JOUABLE", jouable=False)
    return [*modeles.values(), *fictifs, sans_cartes, non_jouable]


def test_modules_equipables_seul_le_lanceur_est_jouable_pendant_la_refonte():
    assert [module.id for module in modules_equipables(charger_modules_new().values())] == ["MOD_2"]


def test_modules_equipables_exclut_le_principal_les_non_jouables_et_les_modules_sans_cartes():
    equipables = modules_equipables(_modules_fictifs())

    assert [module.id for module in equipables] == ["MOD_2", "MOD_TEST_0", "MOD_TEST_1", "MOD_TEST_2", "MOD_TEST_3"]


def test_tirer_candidats_module_renvoie_3_modules_differents():
    pool = modules_equipables(_modules_fictifs())

    candidats = tirer_candidats_module(pool, random.Random(1))

    assert len(candidats) == 3
    assert len({candidat.id for candidat in candidats}) == 3
    assert all(candidat in pool for candidat in candidats)


def test_tirer_candidats_module_est_deterministe_pour_une_meme_graine():
    pool = modules_equipables(_modules_fictifs())

    assert [c.id for c in tirer_candidats_module(pool, random.Random(7))] == [
        c.id for c in tirer_candidats_module(pool, random.Random(7))
    ]


def test_tirer_candidats_module_moins_de_candidats_si_la_pool_est_petite():
    candidats = tirer_candidats_module(modules_equipables(charger_modules_new().values()), random.Random(1))

    assert [candidat.id for candidat in candidats] == ["MOD_2"]


def test_tirer_candidats_module_respecte_la_quantite_demandee():
    candidats = tirer_candidats_module(modules_equipables(_modules_fictifs()), random.Random(2), quantite=2)

    assert len(candidats) == 2


# --- Recompenses de fin de combat (specs.md 2.1/6) ---


def test_tirer_rarete_recompense_respecte_les_bornes():
    assert tirer_rarete_recompense(_AleatoireFixe(0.0)) == RareteCarte.LEGENDAIRE
    assert tirer_rarete_recompense(_AleatoireFixe(0.049)) == RareteCarte.LEGENDAIRE
    assert tirer_rarete_recompense(_AleatoireFixe(0.05)) == RareteCarte.RARE
    assert tirer_rarete_recompense(_AleatoireFixe(0.249)) == RareteCarte.RARE
    assert tirer_rarete_recompense(_AleatoireFixe(0.25)) == RareteCarte.COMMUNE
    assert tirer_rarete_recompense(_AleatoireFixe(0.999)) == RareteCarte.COMMUNE


_MODELES = charger_cartes_new()
CARTE_COMMUNE = dataclasses.replace(_MODELES["CRT_8"], id="TEST_C")
CARTE_RARE = dataclasses.replace(_MODELES["CRT_15"], id="TEST_R")
CARTE_BASE = dataclasses.replace(_MODELES["CRT_7"], id="TEST_B")
CARTE_NON_JOUABLE = dataclasses.replace(_MODELES["CRT_8"], id="TEST_NJ", jouable=False)


def test_tirer_carte_recompense_retombe_sur_le_palier_inferieur_si_vide():
    """Pool sans Legendaire : un tirage Legendaire doit retomber sur Rare (palier suivant)."""
    resultat = tirer_carte_recompense([CARTE_COMMUNE, CARTE_RARE], _AleatoireFixe(0.0))  # vise Legendaire

    assert resultat is CARTE_RARE


def test_tirer_carte_recompense_renvoie_none_si_pool_vide():
    assert tirer_carte_recompense([], random.Random(1)) is None


def _lanceur_avec_cartes(*ids: str):
    return dataclasses.replace(charger_modules_new()["MOD_2"], cartes=ids)


def test_pool_module_exclut_les_cartes_base_et_non_jouables():
    cartes = {"B": CARTE_BASE, "C": CARTE_COMMUNE, "NJ": CARTE_NON_JOUABLE}

    assert pool_module(_lanceur_avec_cartes("B", "C", "NJ"), cartes) == [CARTE_COMMUNE]


def test_pool_toutes_cartes_exclut_les_cartes_base_et_non_jouables():
    cartes = {"B": CARTE_BASE, "C": CARTE_COMMUNE, "R": CARTE_RARE, "NJ": CARTE_NON_JOUABLE}

    assert pool_toutes_cartes(cartes) == [CARTE_COMMUNE, CARTE_RARE]


def _exemplaires_principal_et_lanceur():
    modeles = charger_modules_new()
    return [modeles["MOD_1"].nouvel_exemplaire("M1", "base"), modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche")]


def test_tirer_candidats_recompense_un_par_module_rattache_a_son_exemplaire():
    cartes = charger_cartes_new()
    modules = _exemplaires_principal_et_lanceur()

    for graine in range(20):
        candidats = tirer_candidats_recompense(modules, cartes, random.Random(graine))

        assert [module for module, _carte in candidats] == modules
        for module, carte in candidats:
            assert carte.rarete != RareteCarte.BASE
            # Chaque module pioche dans son propre pool, jamais dans celui d'un autre module
            assert carte.id in module.cartes
            assert carte.exemplaire_module == module.exemplaire
            # Un nouvel exemplaire, pas le modele partage
            assert carte is not cartes[carte.id]


# --- Choix de carte du module fraichement equipe (specs.md 2.3, point 6) ---


def test_tirer_candidats_carte_module_renvoie_3_cartes_distinctes_du_pool_module():
    cartes = charger_cartes_new()
    lanceur = charger_modules_new()["MOD_2"]

    candidats = tirer_candidats_carte_module(lanceur, cartes, random.Random(1))

    assert len(candidats) == 3
    assert len({carte.id for carte in candidats}) == 3
    assert all(carte in pool_module(lanceur, cartes) for carte in candidats)


def test_tirer_candidats_carte_module_respecte_la_quantite_demandee():
    candidats = tirer_candidats_carte_module(charger_modules_new()["MOD_2"], charger_cartes_new(), random.Random(1), quantite=2)

    assert len(candidats) == 2


def test_tirer_candidats_carte_module_moins_de_candidats_si_pool_plus_petit():
    """Un module au pool plus restreint que `quantite` ne renvoie que ce qu'il a (jamais de
    doublon pour completer)."""
    cartes = {"C": CARTE_COMMUNE, "R": CARTE_RARE}
    module = dataclasses.replace(_lanceur_avec_cartes("C", "R"), niveau_maj=2)

    candidats = tirer_candidats_carte_module(module, cartes, random.Random(1), quantite=5)

    assert sorted(carte.id for carte in candidats) == ["TEST_C", "TEST_R"]


def test_le_palier_de_mise_a_jour_ouvre_les_raretes_proposees():
    """Decision utilisateur (2026-11-13) : palier 1 Commune, palier 2 + Rare, palier 3 +
    Legendaire (Station service, specs.md 2.2/6)."""
    cartes = charger_cartes_new()
    lanceur = charger_modules_new()["MOD_2"]
    attendu = {
        1: {RareteCarte.COMMUNE},
        2: {RareteCarte.COMMUNE, RareteCarte.RARE},
        3: {RareteCarte.COMMUNE, RareteCarte.RARE, RareteCarte.LEGENDAIRE},
    }

    for niveau, raretes in attendu.items():
        module = dataclasses.replace(lanceur, niveau_maj=niveau)
        assert {carte.rarete for carte in pool_module(module, cartes)} == raretes
        # Le tirage ne sort jamais du pool, quelle que soit la rarete tiree au sort
        for graine in range(40):
            assert tirer_carte_recompense(pool_module(module, cartes), random.Random(graine)).rarete in raretes


def test_tirer_candidats_carte_module_pool_vide_renvoie_liste_vide():
    assert tirer_candidats_carte_module(_lanceur_avec_cartes(), {"C": CARTE_COMMUNE}, random.Random(1)) == []


# --- Choix du prochain niveau (specs.md 2.3/2.4) ---


def test_est_niveau_boss():
    assert est_niveau_boss(10) is True
    assert est_niveau_boss(20) is True
    assert est_niveau_boss(1) is False
    assert est_niveau_boss(9) is False
    assert est_niveau_boss(11) is False


def test_aleatoire_pour_niveau_est_deterministe_pour_meme_graine_et_niveau():
    a1 = aleatoire_pour_niveau(42, 3)
    a2 = aleatoire_pour_niveau(42, 3)

    assert [a1.random() for _ in range(5)] == [a2.random() for _ in range(5)]


def test_aleatoire_pour_niveau_differe_selon_le_niveau():
    a1 = aleatoire_pour_niveau(42, 3)
    a2 = aleatoire_pour_niveau(42, 4)

    assert a1.random() != a2.random()


def test_tirer_type_etape_respecte_les_bornes():
    assert tirer_type_etape(_AleatoireFixe(0.0)) == TypeEtape.STATION_SERVICE
    assert tirer_type_etape(_AleatoireFixe(1 / 30 - 0.001)) == TypeEtape.STATION_SERVICE
    assert tirer_type_etape(_AleatoireFixe(1 / 30)) == TypeEtape.PLANETE_COMMERCIALE
    assert tirer_type_etape(_AleatoireFixe(0.05)) == TypeEtape.PLANETE_COMMERCIALE
    assert tirer_type_etape(_AleatoireFixe(2 / 30)) == TypeEtape.AVENTURE
    assert tirer_type_etape(_AleatoireFixe(0.1)) == TypeEtape.AVENTURE
    assert tirer_type_etape(_AleatoireFixe(2 / 30 + 1 / 10)) == TypeEtape.PRIME
    assert tirer_type_etape(_AleatoireFixe(0.99)) == TypeEtape.PRIME


def test_tirer_propositions_niveau_renvoie_la_quantite_demandee():
    propositions = tirer_propositions_niveau(3, random.Random(1))

    assert len(propositions) == 3
    assert all(isinstance(p, TypeEtape) for p in propositions)


def test_tirer_propositions_niveau_garantit_station_service_a_5_et_9():
    aleatoire = _AleatoireFixe(0.99)  # toujours Prime sans la garantie

    assert TypeEtape.STATION_SERVICE in tirer_propositions_niveau(5, aleatoire)
    assert TypeEtape.STATION_SERVICE in tirer_propositions_niveau(9, aleatoire)


def test_tirer_propositions_niveau_pas_de_garantie_hors_5_et_9():
    aleatoire = _AleatoireFixe(0.99)

    propositions = tirer_propositions_niveau(3, aleatoire)

    assert propositions == [TypeEtape.PRIME, TypeEtape.PRIME, TypeEtape.PRIME]


def test_tirer_propositions_niveau_ne_remplace_rien_si_deja_present():
    aleatoire = _AleatoireFixe(0.0)  # toujours Station service

    propositions = tirer_propositions_niveau(5, aleatoire)

    assert propositions.count(TypeEtape.STATION_SERVICE) == 3


def test_tirer_propositions_niveau_boss_renvoie_une_seule_proposition_boss():
    assert tirer_propositions_niveau(10, random.Random(1)) == [TypeEtape.BOSS]
    assert tirer_propositions_niveau(20, random.Random(1)) == [TypeEtape.BOSS]


# --- Aventures (specs.md 2.5) ---


def test_tirer_type_aventure_renvoie_une_des_aventures_implementees():
    aleatoire = random.Random(1)

    for _ in range(20):
        assert tirer_type_aventure(aleatoire) in (
            TypeAventure.TROIS_LUNES,
            TypeAventure.ASTEROIDES,
            TypeAventure.POLICE,
        )


def test_tirer_type_aventure_tire_les_trois_sur_un_grand_nombre_d_essais():
    aleatoire = random.Random(1)

    resultats = {tirer_type_aventure(aleatoire) for _ in range(100)}

    assert resultats == {TypeAventure.TROIS_LUNES, TypeAventure.ASTEROIDES, TypeAventure.POLICE}


def test_tirer_carte_deck_renvoie_un_id_du_deck():
    deck = ["CRT_7", "CRT_10", "CRT_12"]
    aleatoire = random.Random(1)

    for _ in range(20):
        assert tirer_carte_deck(deck, aleatoire) in deck
