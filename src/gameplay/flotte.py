"""
La flotte ennemie : les ennemis positionnes sur la grille de combat.
"""

from src.gameplay.ennemi import Ennemi
from src.gameplay.position import Colonne, Position, Rangee


class Flotte:
    """Regroupe les ennemis affrontes en combat, positionnes sur la grille 2x3 (specs.md 8.1)."""

    def __init__(self, ennemis: dict[Position, Ennemi]):
        self._ennemis = dict(ennemis)

    def ennemi_en(self, colonne: Colonne, rangee: Rangee) -> Ennemi | None:
        """Renvoie l'ennemi vivant occupant cette case, ou None si vide/detruit."""
        ennemi = self._ennemis.get(Position(colonne, rangee))
        if ennemi is None or ennemi.est_detruit():
            return None
        return ennemi

    def positions(self) -> dict[Position, Ennemi]:
        """Renvoie les ennemis bruts (y compris detruits), pour l'affichage."""
        return dict(self._ennemis)

    def ennemis_vivants(self) -> list[Ennemi]:
        """Renvoie tous les ennemis encore en vie."""
        return [ennemi for ennemi in self._ennemis.values() if not ennemi.est_detruit()]

    def est_vide(self) -> bool:
        """Indique si tous les ennemis sont detruits (condition de victoire, specs.md 6)."""
        return len(self.ennemis_vivants()) == 0
