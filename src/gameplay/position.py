"""
Position sur la grille de combat : ligne (avant/arriere) x colonne (gauche/mid/droite).
"""

from dataclasses import dataclass
from enum import Enum, auto


class Ligne(Enum):
    """Ligne d'une case : avant (face a l'adversaire) ou arriere."""

    AVANT = auto()
    ARRIERE = auto()


class Colonne(Enum):
    """Colonne d'une case (gauche, milieu, droite), cf. specs.md paragraphe 3.1.1."""

    GAUCHE = auto()
    MID = auto()
    DROITE = auto()


@dataclass(frozen=True)
class Position:
    """Une case de la grille de combat."""

    ligne: Ligne
    colonne: Colonne


_ORDRE_COLONNES = [Colonne.GAUCHE, Colonne.MID, Colonne.DROITE]


def ordre_colonnes_par_proximite(colonne_reference: Colonne) -> list[Colonne]:
    """Renvoie les 3 colonnes triees par proximite croissante depuis colonne_reference.

    En cas d'egalite de distance (colonne_reference = MID), GAUCHE est prioritaire
    sur DROITE (ordre stable de la liste de reference).
    """
    index_reference = _ORDRE_COLONNES.index(colonne_reference)
    return sorted(_ORDRE_COLONNES, key=lambda colonne: abs(_ORDRE_COLONNES.index(colonne) - index_reference))
