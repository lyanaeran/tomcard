"""
Ciblage automatique des ennemis.

La rangee (ligne) est le critere principal, avant/arriere le critere secondaire :
un ennemi regarde d'abord sa propre rangee (avant puis arriere de cette rangee),
et ne passe a une rangee voisine que si sa propre rangee est entierement vide.
La base ne protege donc pas les modules arriere des autres rangees.
"""

from src.gameplay.module import Module
from src.gameplay.position import Colonne, Rangee, ordre_rangees_par_proximite
from src.gameplay.vaisseau import Vaisseau


def module_cible_par_ennemi(vaisseau: Vaisseau, rangee_ennemi: Rangee) -> Module | None:
    """Determine quel module du joueur un ennemi de cette rangee va attaquer."""
    for rangee in ordre_rangees_par_proximite(rangee_ennemi):
        for colonne in (Colonne.AVANT, Colonne.ARRIERE):
            module = vaisseau.module_en(colonne, rangee)
            if module is not None:
                return module
    return None
