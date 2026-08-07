"""
L'ennemi unique affronte dans le combat du POC.
"""


class Ennemi:
    """Represente un ennemi affronte en combat."""

    def __init__(self, pv_max: int, degats_attaque: int, nom: str = "Ennemi"):
        self.pv_max = pv_max
        self.pv = pv_max
        self.degats_attaque = degats_attaque
        self.nom = nom

    def est_detruit(self) -> bool:
        """Renvoie True si l'ennemi n'a plus de points de vie."""
        return self.pv <= 0

    def subir_degats(self, degats: int) -> None:
        """Applique des degats directement sur les points de vie (pas de bouclier ennemi dans ce POC)."""
        self.pv = max(0, self.pv - degats)
