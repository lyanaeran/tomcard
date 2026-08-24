"""
Tests unitaires pour la logique du parcours (src/gameplay/parcours.py).
"""

import dataclasses
import random

from src.gameplay.carte import Carte, CibleCarte, RareteCarte, TypeCarte
from src.gameplay.config_poc import ID_MODULE_PRINCIPAL, creer_vaisseau
from src.gameplay.donnees import charger_cartes, charger_modules
from src.gameplay.parcours import (
    TypeEtape,
    aleatoire_pour_niveau,
    est_niveau_boss,
    modules_equipables,
    pool_module,
    pool_toutes_cartes,
    tirer_candidats_module,
    tirer_candidats_recompense,
    tirer_carte_recompense,
    tirer_propositions_niveau,
    tirer_rarete_recompense,
    tirer_type_etape,
)

IMG = "test.png"


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


def test_modules_equipables_exclut_le_module_principal():
    specs = charger_modules()

    equipables = modules_equipables(specs)

    assert all(spec.id != ID_MODULE_PRINCIPAL for spec in equipables)
    assert len(equipables) == len(specs) - 1


def test_tirer_candidats_module_renvoie_3_modules_differents():
    specs = charger_modules()
    pool = modules_equipables(specs)
    aleatoire = random.Random(1)

    candidats = tirer_candidats_module(pool, aleatoire)

    assert len(candidats) == 3
    assert len(set(candidat.id for candidat in candidats)) == 3
    assert all(candidat in pool for candidat in candidats)


def test_tirer_candidats_module_est_deterministe_pour_une_meme_graine():
    specs = charger_modules()
    pool = modules_equipables(specs)

    candidats_1 = tirer_candidats_module(pool, random.Random(7))
    candidats_2 = tirer_candidats_module(pool, random.Random(7))

    assert [c.id for c in candidats_1] == [c.id for c in candidats_2]


def test_tirer_candidats_module_respecte_la_quantite_demandee():
    specs = charger_modules()
    pool = modules_equipables(specs)
    aleatoire = random.Random(2)

    candidats = tirer_candidats_module(pool, aleatoire, quantite=2)

    assert len(candidats) == 2


# --- Recompenses de fin de combat (specs.md 2.1/6) ---


def test_tirer_rarete_recompense_respecte_les_bornes():
    assert tirer_rarete_recompense(_AleatoireFixe(0.0)) == RareteCarte.LEGENDAIRE
    assert tirer_rarete_recompense(_AleatoireFixe(0.049)) == RareteCarte.LEGENDAIRE
    assert tirer_rarete_recompense(_AleatoireFixe(0.05)) == RareteCarte.RARE
    assert tirer_rarete_recompense(_AleatoireFixe(0.249)) == RareteCarte.RARE
    assert tirer_rarete_recompense(_AleatoireFixe(0.25)) == RareteCarte.COMMUNE
    assert tirer_rarete_recompense(_AleatoireFixe(0.999)) == RareteCarte.COMMUNE


CARTE_COMMUNE = Carte(nom="C", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=1, rarete=RareteCarte.COMMUNE)
CARTE_RARE = Carte(nom="R", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=1, rarete=RareteCarte.RARE)
CARTE_BASE = Carte(nom="B", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=1, rarete=RareteCarte.BASE)


def test_tirer_carte_recompense_retombe_sur_le_palier_inferieur_si_vide():
    """Pool sans Legendaire : un tirage Legendaire doit retomber sur Rare (palier suivant)."""
    pool = [CARTE_COMMUNE, CARTE_RARE]

    resultat = tirer_carte_recompense(pool, _AleatoireFixe(0.0))  # vise Legendaire

    assert resultat is CARTE_RARE


def test_tirer_carte_recompense_renvoie_none_si_pool_vide():
    assert tirer_carte_recompense([], random.Random(1)) is None


def test_pool_module_exclut_les_cartes_base():
    cartes = {"CRT_B": CARTE_BASE, "CRT_C": CARTE_COMMUNE}
    spec = next(s for s in charger_modules() if s.id != ID_MODULE_PRINCIPAL)
    spec_test = dataclasses.replace(spec, cartes=("CRT_B", "CRT_C"))

    pool = pool_module(spec_test, cartes)

    assert pool == [CARTE_COMMUNE]


def test_pool_toutes_cartes_exclut_les_cartes_base():
    cartes = {"CRT_B": CARTE_BASE, "CRT_C": CARTE_COMMUNE, "CRT_R": CARTE_RARE}

    pool = pool_toutes_cartes(cartes)

    assert set(pool) == {CARTE_COMMUNE, CARTE_RARE}


def test_tirer_candidats_recompense_un_par_module_principal_pioche_dans_tout_le_pool():
    specs_modules = charger_modules()
    cartes = charger_cartes()
    _vaisseau, specs_utilisees = creer_vaisseau(specs_modules, random.Random(5))

    candidats = tirer_candidats_recompense(specs_utilisees, cartes, random.Random(5))

    assert len(candidats) == len(specs_utilisees) == 5
    assert candidats[0][0].id == ID_MODULE_PRINCIPAL
    for spec, carte in candidats:
        assert carte is not None
        assert carte.rarete != RareteCarte.BASE
        if spec.id != ID_MODULE_PRINCIPAL:
            assert carte in pool_module(spec, cartes)


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
