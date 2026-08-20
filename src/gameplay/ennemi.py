"""
L'ennemi unique affronte dans le combat du POC.
"""

from dataclasses import dataclass

from src.gameplay.carte import ActionCarte


@dataclass
class DebuffActif:
    """Un debuff Sabotage applique sur un ennemi (specs.md 12.1/12.4). Chaque debuff joue est
    independant des autres : ils ne fusionnent jamais, meme du meme type sur le meme ennemi
    (decide avec l'utilisateur - un ennemi peut porter plusieurs debuffs du meme type a la fois,
    leurs effets s'additionnent tant qu'ils sont actifs)."""

    action: ActionCarte
    valeur: int
    tours_restants: int


class Ennemi:
    """Represente un ennemi affronte en combat."""

    def __init__(self, pv_max: int, degats_attaque: int, nom: str = "Ennemi", image: str | None = None):
        self.pv_max = pv_max
        self.pv = pv_max
        self.degats_attaque = degats_attaque
        self.nom = nom
        self.image = image
        self.debuffs_actifs: list[DebuffActif] = []

    def est_detruit(self) -> bool:
        """Renvoie True si l'ennemi n'a plus de points de vie."""
        return self.pv <= 0

    def subir_degats(self, degats: int) -> None:
        """Applique des degats directement sur les points de vie (pas de bouclier ennemi dans ce POC)."""
        self.pv = max(0, self.pv - degats)

    def appliquer_debuff(self, action: ActionCarte, valeur: int, tours: int) -> None:
        """Ajoute un nouveau debuff a la liste des debuffs actifs (specs.md 12.1/12.4).

        Independant des debuffs deja actifs : n'ecrase ni ne fusionne rien, meme un debuff du
        meme type deja present. Leurs effets s'additionnent tant qu'ils sont actifs (§12.1).
        """
        self.debuffs_actifs.append(DebuffActif(action=action, valeur=valeur, tours_restants=tours))

    def _somme_debuffs(self, action: ActionCarte) -> int:
        return sum(debuff.valeur for debuff in self.debuffs_actifs if debuff.action == action)

    def degats_attaque_effectifs(self) -> int:
        """Degats reellement infliges par cet ennemi, somme des reductions actives soustraite."""
        return max(0, self.degats_attaque - self._somme_debuffs(ActionCarte.REDUCTION_DEGATS))

    def degats_subis(self, degats: int) -> int:
        """Degats bruts d'une carte, majores par la somme des vulnerabilites actives de cet ennemi."""
        vulnerabilite = self._somme_debuffs(ActionCarte.VULNERABILITE)
        if vulnerabilite:
            return round(degats * (1 + vulnerabilite / 100))
        return degats

    def decrementer_debuffs(self) -> None:
        """A appeler une fois par tour ennemi ecoule : fait expirer les debuffs a duree
        (specs.md 12.1/12.4 - chaque debuff decompte independamment, meme si l'ennemi n'a pas agi)."""
        for debuff in self.debuffs_actifs:
            debuff.tours_restants -= 1
        self.debuffs_actifs = [debuff for debuff in self.debuffs_actifs if debuff.tours_restants > 0]
