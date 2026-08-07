"""
Point d'entree du POC Space Fight : lance la fenetre de combat.
"""

import pyglet

from src.ui.fenetre import FenetreCombat


def main() -> None:
    """Ouvre la fenetre de combat et demarre la boucle pyglet."""
    FenetreCombat()
    pyglet.app.run()


if __name__ == "__main__":
    main()
