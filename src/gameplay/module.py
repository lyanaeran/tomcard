"""
Le module de base du vaisseau du joueur : points de vie et bouclier.
"""


class Module:
    """Represente le module de base du vaisseau du joueur."""

    def __init__(self, pv_max: int):
        self.pv_max = pv_max
        self.pv = pv_max
        self.bouclier = 0

    def est_detruit(self) -> bool:
        """Renvoie True si le module n'a plus de points de vie."""
        return self.pv <= 0

    def subir_degats(self, degats: int) -> None:
        """Applique des degats, en absorbant d'abord avec le bouclier (specs.md paragraphe 3.5)."""
        degats_restants = max(0, degats - self.bouclier)
        self.bouclier = max(0, self.bouclier - degats)
        self.pv = max(0, self.pv - degats_restants)

    def ajouter_bouclier(self, valeur: int) -> None:
        """Ajoute du bouclier au module."""
        self.bouclier += valeur

    def soigner(self, valeur: int) -> None:
        """Repare des points de vie, sans depasser le maximum."""
        self.pv = min(self.pv_max, self.pv + valeur)
