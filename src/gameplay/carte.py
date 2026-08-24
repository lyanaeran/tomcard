"""
Definition des cartes jouables pour le combat.
"""

import dataclasses
from dataclasses import dataclass
from enum import Enum, auto


class TypeCarte(Enum):
    """Type d'une carte, tel que defini dans specs.md paragraphe 7.1.

    REPARATION remplace l'ancien type SOIN (meme role : repare des PV).
    """

    ATTAQUE = auto()
    DEFENSE = auto()
    REPARATION = auto()
    OUTILS = auto()
    DEBUFF = auto()
    BUFF = auto()


class CibleCarte(Enum):
    """Cible visee par une carte, cf. specs.md paragraphe 7.2 et config/cartes.json.

    ALLIE_UNIQUE / ENNEMI_UNIQUE : un module/ennemi vivant, au choix du joueur.
    ALLIES_MULTIPLES / ENNEMIS_MULTIPLES : tous les modules/ennemis vivants, pas de
    choix a faire (la carte se resout des sa selection).
    LIGNE_ENNEMIE : l'avant et l'arriere de la rangee de l'ennemi clique (2 ennemis
    au plus), pour les cartes percantes (specs.md paragraphe 3.1).
    MODULE_PRINCIPAL : cible toujours le module de base, pas de clic necessaire
    (specs.md paragraphe 9.1).
    COLONNE_AVANT_ENNEMIE / COLONNE_ARRIERE_ENNEMIE : toute la colonne avant (ou
    arriere) ennemie, jusqu'a 3 ennemis. Le joueur doit cliquer un ennemi de cette
    colonne precise pour confirmer (specs.md paragraphe 12.1) - contrairement a
    LIGNE_ENNEMIE, la colonne visee est fixe par la carte, pas deduite du clic.
    COLONNE_AVANT_ALLIEE : les modules avant-gauche et avant-droite du joueur, plus le
    module principal (qui occupe la rangee mid et compte donc a la fois comme avant et
    comme arriere). Meme principe que les colonnes ennemies : le joueur doit cliquer un
    module de cette colonne (ou le module principal) pour confirmer.
    """

    ENNEMI_UNIQUE = auto()
    ALLIE_UNIQUE = auto()
    ALLIES_MULTIPLES = auto()
    ENNEMIS_MULTIPLES = auto()
    LIGNE_ENNEMIE = auto()
    MODULE_PRINCIPAL = auto()
    COLONNE_AVANT_ENNEMIE = auto()
    COLONNE_ARRIERE_ENNEMIE = auto()
    COLONNE_AVANT_ALLIEE = auto()


# Cibles qui se resolvent sans clic de ciblage (pas de choix individuel possible)
CIBLES_SANS_CLIC = (CibleCarte.ALLIES_MULTIPLES, CibleCarte.ENNEMIS_MULTIPLES, CibleCarte.MODULE_PRINCIPAL)


class RareteCarte(Enum):
    """Palier de rarete d'une carte, cf. specs.md paragraphe 7.3 et 7.4."""

    BASE = auto()
    COMMUNE = auto()
    RARE = auto()
    LEGENDAIRE = auto()


class ActionCarte(Enum):
    """Effet precis d'une carte DEFENSE, OUTILS, DEBUFF ou BUFF (chaque carte est un
    mecanisme different, cf. specs.md paragraphe 12.4/12.8/12.9/12.1/12.5) : la valeur de
    la carte s'interprete differemment selon cette action."""

    GAIN_ELECTRICITE = auto()
    GAIN_ELECTRICITE_PAR_MODULE = auto()
    PIOCHE_SUPPLEMENTAIRE = auto()
    REDUCTION_DEGATS = auto()
    VULNERABILITE = auto()
    BOUCLIER_PAR_TOUR = auto()
    BOUCLIER_POURCENTAGE_PV = auto()
    REDIRECTION_CIBLE = auto()
    ANNULATION_PROCHAINE_ATTAQUE = auto()


@dataclass(eq=False)
class Carte:
    """Une carte jouable, avec son cout, son effet et son image.

    eq=False : deux cartes ne sont egales que si c'est le meme objet Python. Necessaire
    depuis l'ajout des munitions (paragraphe 3.6) : deux exemplaires du meme modele de
    carte dans un deck peuvent avoir un compte de munitions_restantes different, donc ne
    doivent jamais etre confondus par Deck.jouer()/main.remove() malgre des champs egaux.
    """

    nom: str
    image: str
    type: TypeCarte
    cible: CibleCarte
    cout: int
    valeur: int
    rarete: RareteCarte = RareteCarte.BASE
    munitions_max: int | None = None
    munitions_restantes: int | None = None
    action: ActionCarte | None = None
    duree: int | None = None

    def __post_init__(self):
        if self.munitions_restantes is None and self.munitions_max is not None:
            self.munitions_restantes = self.munitions_max

    def copie(self) -> "Carte":
        """Nouvel exemplaire independant de cette carte (munitions_restantes reinitialise
        a munitions_max) : chaque copie physique tiree dans un deck doit avoir son propre
        compteur de munitions, cf. specs.md paragraphe 3.6."""
        return dataclasses.replace(self, munitions_restantes=self.munitions_max)


def regrouper_cartes(cartes: list[Carte]) -> list[tuple[Carte, int]]:
    """Regroupe une liste de cartes par modele (meme nom = meme modele) en (carte, quantite),
    premiere occurrence conservee comme representant - pour les ecrans affichant "le deck en
    entier" sans repeter chaque exemplaire individuel (ex. 5 Attaque de base -> une entree x5)."""
    groupes: dict[str, list[Carte]] = {}
    for carte in cartes:
        groupes.setdefault(carte.nom, []).append(carte)
    return [(exemplaires[0], len(exemplaires)) for exemplaires in groupes.values()]
