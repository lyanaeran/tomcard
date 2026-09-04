"""
La flotte ennemie : les ennemis positionnes sur la grille de combat.
"""

from src.gameplay.ennemi import Ennemi
from src.gameplay.position import Colonne, Position, Rangee


class Flotte:
    """Regroupe les ennemis affrontes en combat, positionnes sur la grille 2x3 (specs.md 8.1).

    Un ennemi a plusieurs emplacements (specs.md 3.2, ex. le Boss des pirates) est le meme
    objet Ennemi range a plusieurs Positions du dict `_ennemis` - ennemis_vivants()/positions_de()
    le deduplique/regroupe en consequence, pour qu'il ne joue son tour ou ne soit touche par une
    attaque de zone qu'une seule fois."""

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

    def positions_de(self, ennemi: Ennemi) -> list[Position]:
        """Toutes les cases occupees par cet ennemi (specs.md 3.2 : plusieurs pour un ennemi a
        plusieurs emplacements comme le Boss des pirates), vide s'il n'est pas dans la flotte."""
        return [position for position, occupant in self._ennemis.items() if occupant is ennemi]

    def ennemis_vivants(self) -> list[Ennemi]:
        """Renvoie tous les ennemis encore en vie, une seule fois chacun meme s'ils occupent
        plusieurs cases (specs.md 3.2)."""
        vivants: list[Ennemi] = []
        for ennemi in self._ennemis.values():
            if not ennemi.est_detruit() and not any(existant is ennemi for existant in vivants):
                vivants.append(ennemi)
        return vivants

    def est_vide(self) -> bool:
        """Indique si tous les ennemis sont detruits (condition de victoire, specs.md 6)."""
        return len(self.ennemis_vivants()) == 0
