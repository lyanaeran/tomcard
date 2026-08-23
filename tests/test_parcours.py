"""
Tests unitaires pour la logique du parcours (src/gameplay/parcours.py).
"""

import dataclasses
import random

from src.gameplay.carte import Carte, CibleCarte, RareteCarte, TypeCarte
from src.gameplay.config_poc import ID_MODULE_PRINCIPAL, creer_vaisseau
from src.gameplay.donnees import charger_cartes, charger_modules
from src.gameplay.parcours import (
    modules_equipables,
    pool_module,
    pool_toutes_cartes,
    tirer_candidats_module,
    tirer_candidats_recompense,
    tirer_carte_recompense,
    tirer_rarete_recompense,
)

IMG = "test.png"


class _AleatoireFixe:
    """Stub deterministe : random() renvoie toujours la meme valeur, choice() prend toujours
    le premier element - pour tester precisement les bornes de tirer_rarete_recompense."""

    def __init__(self, valeur_random: float):
        self._valeur = valeur_random

    def random(self) -> float:
        return self._valeur

    def choice(self, sequence):
        return sequence[0]


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
