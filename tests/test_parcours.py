"""
Tests unitaires pour la logique du parcours (src/gameplay/parcours.py).
"""

import random

from src.gameplay.config_poc import ID_MODULE_PRINCIPAL
from src.gameplay.donnees import charger_modules
from src.gameplay.parcours import modules_equipables, tirer_candidats_module


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
