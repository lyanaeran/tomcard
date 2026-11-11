"""
Mise en forme des nombres des rapports de simulation, partagee par rapport.py (ancien moteur) et
combats_new.py (refonte) pour que les deux rapports restent identiques.
"""

from collections.abc import Iterable
from statistics import mean


def pourcentage(n: int, total: int) -> str:
    """Ex. "42 %" ; "-" si le total est nul."""
    return f"{100 * n / total:.0f} %" if total else "-"


def moyenne(valeurs: Iterable) -> str:
    """Moyenne a une decimale, valeurs absentes (None) ignorees ; "-" s'il n'y en a aucune."""
    valeurs = [valeur for valeur in valeurs if valeur is not None]
    return f"{mean(valeurs):.1f}" if valeurs else "-"
