"""
Le joueur : son module de base, son deck de cartes et son electricite.
"""

from src.gameplay.carte import Carte
from src.gameplay.deck import Deck
from src.gameplay.module import Module


class Joueur:
    """Regroupe le module de base, le deck de cartes et l'electricite du joueur."""

    def __init__(self, module: Module, deck: Deck, electricite_par_tour: int):
        self.module = module
        self.deck = deck
        self.electricite_par_tour = electricite_par_tour
        self.electricite = 0

    def debut_de_tour(self) -> None:
        """Recharge l'electricite et pioche les cartes du tour (specs.md paragraphe 3.3)."""
        self.electricite = self.electricite_par_tour
        self.deck.piocher_debut_de_tour()

    def peut_jouer(self, carte: Carte) -> bool:
        """Indique si le joueur a assez d'electricite et si la carte est bien en main."""
        return self.electricite >= carte.cout and carte in self.deck.main

    def depenser_electricite(self, cout: int) -> None:
        """Deduit le cout d'une carte de l'electricite disponible."""
        self.electricite -= cout
