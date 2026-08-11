"""
Minuterie d'animation pour les popups +/- affiches sur une cible touchee.

Logique pure, independante de pyglet, pour rester testable sans affichage.
"""


class AnimationPopup:
    """Gere la duree d'affichage d'un popup +/-N sur une cible."""

    DUREE = 2.0  # secondes

    def __init__(self):
        self.temps_restant = 0.0

    def demarrer(self) -> None:
        """Declenche l'animation pour sa duree totale."""
        self.temps_restant = self.DUREE

    def est_active(self) -> bool:
        """Indique si le popup doit encore etre affiche."""
        return self.temps_restant > 0

    def mettre_a_jour(self, dt: float) -> None:
        """Fait avancer le temps ecoule (dt en secondes) sans jamais descendre sous zero."""
        self.temps_restant = max(0.0, self.temps_restant - dt)
