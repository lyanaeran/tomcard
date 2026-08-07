"""
Le vaisseau du joueur : le module de base et les modules equipes sur la grille.
"""

from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee


class Vaisseau:
    """Regroupe le module de base et les modules equipes sur la grille 2x3 (specs.md 3.1/5)."""

    def __init__(
        self,
        base: Module,
        avant_gauche: Module | None = None,
        avant_droite: Module | None = None,
        arriere_gauche: Module | None = None,
        arriere_droite: Module | None = None,
    ):
        self.base = base
        self._modules_equipes: dict[Position, Module] = {}
        if avant_gauche is not None:
            self._modules_equipes[Position(Colonne.AVANT, Rangee.GAUCHE)] = avant_gauche
        if avant_droite is not None:
            self._modules_equipes[Position(Colonne.AVANT, Rangee.DROITE)] = avant_droite
        if arriere_gauche is not None:
            self._modules_equipes[Position(Colonne.ARRIERE, Rangee.GAUCHE)] = arriere_gauche
        if arriere_droite is not None:
            self._modules_equipes[Position(Colonne.ARRIERE, Rangee.DROITE)] = arriere_droite

    def module_en(self, colonne: Colonne, rangee: Rangee) -> Module | None:
        """Renvoie le module vivant occupant cette case, ou None si vide/detruit.

        La rangee MID est toujours occupee par la base (quelle que soit la colonne
        demandee), tant qu'elle est en vie : elle occupe la rangee Mid en entier.
        """
        if rangee == Rangee.MID:
            return None if self.base.est_detruit() else self.base
        module = self._modules_equipes.get(Position(colonne, rangee))
        if module is None or module.est_detruit():
            return None
        return module

    def modules_equipes(self) -> dict[Position, Module]:
        """Renvoie les modules equipes bruts (y compris detruits), pour l'affichage."""
        return dict(self._modules_equipes)

    def est_detruit(self) -> bool:
        """Le vaisseau est detruit si le module de base est detruit (specs.md 3.4)."""
        return self.base.est_detruit()
