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
    """Cible visee par une carte, cf. specs.md paragraphe 7.2 et config/cartes.json.

    ALLIE_UNIQUE / ENNEMI_UNIQUE : un module/ennemi vivant, au choix du joueur.
    ALLIES_MULTIPLES / ENNEMIS_MULTIPLES : tous les modules/ennemis vivants, pas de
    choix a faire (la carte se resout des sa selection).
    LIGNE_ENNEMIE : l'avant et l'arriere de la rangee de l'ennemi clique (2 ennemis
    au plus), pour les cartes percantes (specs.md paragraphe 3.1).
    """

    ENNEMI_UNIQUE = auto()
    ALLIE_UNIQUE = auto()
    ALLIES_MULTIPLES = auto()
    ENNEMIS_MULTIPLES = auto()
    LIGNE_ENNEMIE = auto()


# Cibles qui se resolvent sans clic de ciblage (pas de choix individuel possible)
CIBLES_SANS_CLIC = (CibleCarte.ALLIES_MULTIPLES, CibleCarte.ENNEMIS_MULTIPLES)


@dataclass(frozen=True)
class Carte:
    """Une carte jouable, avec son cout, son effet et son image."""

    nom: str
    image: str
    type: TypeCarte
    cible: CibleCarte
    cout: int
    valeur: int
