"""
L'ennemi unique affronte dans le combat du POC.
"""


class Ennemi:
    """Represente un ennemi affronte en combat."""

    def __init__(self, pv_max: int, degats_attaque: int, nom: str = "Ennemi", image: str | None = None):
        self.pv_max = pv_max
        self.pv = pv_max
        self.degats_attaque = degats_attaque
        self.nom = nom
        self.image = image
        # Debuffs temporaires (cartes Sabotage, specs.md 12.1/12.4) : appliquer un nouveau
        # debuff du meme type remplace l'ancien plutot que de cumuler (simplification, pas
        # de regle de cumul donnee dans le tableau de conception).
        self.reduction_degats = 0
        self.reduction_degats_tours = 0
        self.vulnerabilite_pourcent = 0
        self.vulnerabilite_tours = 0

    def est_detruit(self) -> bool:
        """Renvoie True si l'ennemi n'a plus de points de vie."""
        return self.pv <= 0

    def subir_degats(self, degats: int) -> None:
        """Applique des degats directement sur les points de vie (pas de bouclier ennemi dans ce POC)."""
        self.pv = max(0, self.pv - degats)

    def appliquer_reduction_degats(self, valeur: int, tours: int) -> None:
        """Debuff "Tordre le canon" : diminue les degats infliges par cet ennemi (specs.md 12.1)."""
        self.reduction_degats = valeur
        self.reduction_degats_tours = tours

    def appliquer_vulnerabilite(self, pourcent: int, tours: int) -> None:
        """Debuff "Breche"/"Ligne avant"/"Boucliers endommages"/"...hors service" : augmente
        les degats subis par cet ennemi en % (specs.md 12.4)."""
        self.vulnerabilite_pourcent = pourcent
        self.vulnerabilite_tours = tours

    def degats_attaque_effectifs(self) -> int:
        """Degats reellement infliges par cet ennemi, reduction de "Tordre le canon" appliquee."""
        return max(0, self.degats_attaque - self.reduction_degats)

    def degats_subis(self, degats: int) -> int:
        """Degats bruts d'une carte, majores par la vulnerabilite active de cet ennemi."""
        if self.vulnerabilite_pourcent:
            return round(degats * (1 + self.vulnerabilite_pourcent / 100))
        return degats

    def decrementer_debuffs(self) -> None:
        """A appeler une fois par tour ennemi ecoule : fait expirer les debuffs a duree
        (specs.md 12.1/12.4 - le compteur baisse a chaque tour, meme si l'ennemi n'a pas agi)."""
        if self.reduction_degats_tours > 0:
            self.reduction_degats_tours -= 1
            if self.reduction_degats_tours == 0:
                self.reduction_degats = 0
        if self.vulnerabilite_tours > 0:
            self.vulnerabilite_tours -= 1
            if self.vulnerabilite_tours == 0:
                self.vulnerabilite_pourcent = 0
