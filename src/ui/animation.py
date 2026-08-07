"""
Minuterie d'animation pour le rayon d'attaque de l'ennemi.

Logique pure, independante de pyglet, pour rester testable sans affichage.
"""


class AnimationRayon:
    """Gere la duree d'affichage du rayon d'attaque entre l'ennemi et le module."""

    DUREE = 0.4  # secondes

    def __init__(self):
        self.temps_restant = 0.0

    def demarrer(self) -> None:
        """Declenche l'animation pour sa duree totale."""
        self.temps_restant = self.DUREE

    def est_active(self) -> bool:
        """Indique si le rayon doit etre affiche."""
        return self.temps_restant > 0

    def progression(self) -> float:
        """Renvoie la part de temps restante, entre 0 (fini) et 1 (vient de demarrer)."""
        if self.DUREE <= 0:
            return 0.0
        return max(0.0, min(1.0, self.temps_restant / self.DUREE))

    def mettre_a_jour(self, dt: float) -> None:
        """Fait avancer le temps ecoule (dt en secondes) sans jamais descendre sous zero."""
        self.temps_restant = max(0.0, self.temps_restant - dt)
