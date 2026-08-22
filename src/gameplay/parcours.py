"""
Logique du parcours (run), hors combat (specs.md paragraphe 2/2.3). Pour l'instant : uniquement
le tirage des candidats du Niveau 1 (choix de module).
"""

import random

from src.gameplay.config_poc import ID_MODULE_PRINCIPAL
from src.gameplay.donnees import SpecModule

NOMBRE_CANDIDATS_MODULE = 3


def modules_equipables(specs_modules: list[SpecModule]) -> list[SpecModule]:
    """Modules pouvant etre proposes en choix : tous sauf le module principal, deja acquis
    d'office en debut de run (specs.md paragraphe 5)."""
    return [spec for spec in specs_modules if spec.id != ID_MODULE_PRINCIPAL]


def tirer_candidats_module(
    pool: list[SpecModule], aleatoire: random.Random, quantite: int = NOMBRE_CANDIDATS_MODULE
) -> list[SpecModule]:
    """Tire `quantite` modules differents au hasard dans la pool (specs.md paragraphe 2.3,
    Niveau 1) : uniforme pour l'instant, puisqu'aucun module n'est encore possede a ce stade du
    run (donc pas de ponderation par doublons a appliquer - cf. specs.md 2.3 "points encore
    ouverts" pour les tirages ulterieurs, apres un Boss, une fois des modules deja possedes)."""
    return aleatoire.sample(pool, quantite)
