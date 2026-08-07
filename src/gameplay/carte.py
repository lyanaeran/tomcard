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
    """Cible visee par une carte, cf. specs.md paragraphe 7.2.

    ALLIE : n'importe quel module allie vivant, au choix du joueur (pas seulement
    le module dont la carte provient).
    """

    ENNEMI = auto()
    ALLIE = auto()


@dataclass(frozen=True)
class Carte:
    """Une carte jouable, avec son cout et son effet."""

    nom: str
    type: TypeCarte
    cible: CibleCarte
    cout: int
    valeur: int


def fabriquer_kit(suffixe: str, cout: int, degats: int, bouclier: int, soin: int) -> tuple[Carte, Carte, Carte]:
    """Fabrique le trio Attaque/Bouclier/Soin d'un module (poc.md paragraphe 2)."""
    attaque = Carte(nom=f"Attaque {suffixe}", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI, cout=cout, valeur=degats)
    bouclier_carte = Carte(nom=f"Bouclier {suffixe}", type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE, cout=cout, valeur=bouclier)
    soin_carte = Carte(nom=f"Soin {suffixe}", type=TypeCarte.SOIN, cible=CibleCarte.ALLIE, cout=cout, valeur=soin)
    return attaque, bouclier_carte, soin_carte


# Le kit de la base, cf. poc.md paragraphe 2 (inchange depuis la premiere version du POC)
CARTE_ATTAQUE = Carte(nom="Attaque", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI, cout=1, valeur=7)
CARTE_BOUCLIER = Carte(nom="Bouclier", type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE, cout=1, valeur=5)
CARTE_SOIN = Carte(nom="Soin", type=TypeCarte.SOIN, cible=CibleCarte.ALLIE, cout=1, valeur=4)
