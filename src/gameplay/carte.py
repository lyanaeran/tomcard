"""
Definition des cartes jouables pour le combat.
"""

from dataclasses import dataclass
from enum import Enum, auto


class TypeCarte(Enum):
    """Type d'une carte, tel que defini dans specs.md paragraphe 7.1."""

    ATTAQUE = auto()
    DEFENSE = auto()
    SOIN = auto()


class CibleCarte(Enum):
    """Cible visee par une carte, cf. specs.md paragraphe 7.2."""

    ENNEMI = auto()
    SOI = auto()


@dataclass(frozen=True)
class Carte:
    """Une carte jouable, avec son cout et son effet."""

    nom: str
    type: TypeCarte
    cible: CibleCarte
    cout: int
    valeur: int


# Les 3 cartes du POC, cf. poc.md paragraphe 4
CARTE_ATTAQUE = Carte(nom="Attaque", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI, cout=1, valeur=7)
CARTE_BOUCLIER = Carte(nom="Bouclier", type=TypeCarte.DEFENSE, cible=CibleCarte.SOI, cout=1, valeur=5)
CARTE_SOIN = Carte(nom="Soin", type=TypeCarte.SOIN, cible=CibleCarte.SOI, cout=1, valeur=4)
