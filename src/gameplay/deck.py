"""
Gestion de la pioche, de la main et de la defausse d'un joueur.
"""

import random

from src.gameplay.carte import Carte


class Deck:
    """Gere la pioche, la main et la defausse d'un joueur (specs.md paragraphe 3.3)."""

    TAILLE_MAIN_MAX = 10
    CARTES_PIOCHEES_PAR_TOUR = 5

    def __init__(self, cartes: list[Carte], generateur_aleatoire: random.Random | None = None):
        self._aleatoire = generateur_aleatoire or random.Random()
        self.pioche: list[Carte] = list(cartes)
        self._aleatoire.shuffle(self.pioche)
        self.main: list[Carte] = []
        self.defausse: list[Carte] = []
        self.cartes_epuisees: list[Carte] = []

    def piocher_debut_de_tour(self) -> None:
        """Pioche le nombre de cartes prevu pour un tour."""
        self.piocher_cartes(self.CARTES_PIOCHEES_PAR_TOUR)

    def piocher_cartes(self, quantite: int) -> None:
        """Pioche `quantite` cartes (hors du tirage de debut de tour, ex : carte Outils)."""
        for _ in range(quantite):
            self._piocher_une_carte()

    def jouer(self, carte: Carte) -> None:
        """Retire une carte de la main. Part en defausse, sauf si ses munitions tombent a
        0 (paragraphe 3.6) : dans ce cas elle rejoint les cartes epuisees et ne revient
        jamais dans le combat en cours (pas de remelange avec la defausse)."""
        self.main.remove(carte)
        if carte.munitions_restantes is not None:
            carte.munitions_restantes -= 1
            if carte.munitions_restantes <= 0:
                self.cartes_epuisees.append(carte)
                return
        self.defausse.append(carte)

    def defausser_main(self) -> None:
        """Envoie toute la main restante en defausse (fin de tour, comme dans Slay the Spire)."""
        self.defausse.extend(self.main)
        self.main = []

    def _piocher_une_carte(self) -> None:
        """Pioche une carte, en remelangeant la defausse si la pioche est vide."""
        if len(self.main) >= self.TAILLE_MAIN_MAX:
            return
        if not self.pioche:
            self._remelanger_defausse()
        if not self.pioche:
            return
        self.main.append(self.pioche.pop())

    def _remelanger_defausse(self) -> None:
        """Remet la defausse dans la pioche et melange."""
        self.pioche = self.defausse
        self.defausse = []
        self._aleatoire.shuffle(self.pioche)
