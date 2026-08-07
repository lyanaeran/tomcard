"""
Position sur la grille de combat : colonne (avant/arriere) x rangee (gauche/mid/droite).
"""

from dataclasses import dataclass
from enum import Enum, auto


class Colonne(Enum):
    """Colonne d'une case : avant (face a l'adversaire) ou arriere."""

    AVANT = auto()
    ARRIERE = auto()


class Rangee(Enum):
    """Rangee d'une case, cf. specs.md paragraphe 3.1."""

    GAUCHE = auto()
    MID = auto()
    DROITE = auto()


@dataclass(frozen=True)
class Position:
    """Une case de la grille de combat."""

    colonne: Colonne
    rangee: Rangee


_ORDRE_RANGEES = [Rangee.GAUCHE, Rangee.MID, Rangee.DROITE]


def ordre_rangees_par_proximite(rangee_reference: Rangee) -> list[Rangee]:
    """Renvoie les 3 rangees triees par proximite croissante depuis rangee_reference.

    En cas d'egalite de distance (rangee_reference = MID), GAUCHE est prioritaire
    sur DROITE (ordre stable de la liste de reference).
    """
    index_reference = _ORDRE_RANGEES.index(rangee_reference)
    return sorted(_ORDRE_RANGEES, key=lambda rangee: abs(_ORDRE_RANGEES.index(rangee) - index_reference))
