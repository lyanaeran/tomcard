"""
Flotte de la refonte (FlotteNew) : les ennemis en combat (copies d'EnnemiNew) places sur la grille
ennemie (specs/refonte-combat.md 2.2, 5.1). Pas encore branchee au moteur : remplacera
flotte.py:Flotte. La composition des flottes (quels ennemis, preferences de placement) reste
faite a l'exterieur : la flotte recoit les ennemis deja places.

Un ennemi sur plusieurs cases (Boss des pirates) est le meme objet range a plusieurs cases : il
n'est compte, touche et joue qu'une fois.
"""

from src.gameplay.ennemi_new import EnnemiNew
from src.gameplay.position import Colonne, Position, Rangee

# Ordre de jeu des ennemis (decision utilisateur) : colonne avant puis arriere ; dans une colonne,
# rangee droite, milieu, gauche (la rangee gauche est en bas de l'ecran)
ORDRE_DE_JEU = tuple(
    Position(colonne, rangee)
    for colonne in (Colonne.AVANT, Colonne.ARRIERE)
    for rangee in (Rangee.DROITE, Rangee.MID, Rangee.GAUCHE)
)


class FlotteNew:
    """Les ennemis d'un combat, sur leurs cases."""

    def __init__(self, ennemis: dict[Position, EnnemiNew]):
        self._par_case = dict(ennemis)
        # Le placement ne change jamais pendant un combat : ennemis et cases calcules une fois
        self._ennemis: list[EnnemiNew] = []
        self._cases: list[list[Position]] = []
        for case in ORDRE_DE_JEU:
            ennemi = self._par_case.get(case)
            if ennemi is None:
                continue
            index = next((i for i, deja in enumerate(self._ennemis) if deja is ennemi), None)
            if index is None:
                self._ennemis.append(ennemi)
                self._cases.append([case])
            else:
                self._cases[index].append(case)
        for ennemi in self._ennemis:
            if ennemi.pv is None:
                raise ValueError(f"Ennemi {ennemi.id} : la flotte prend des ennemis en combat (pour_combat)")
            cases = self.cases_de(ennemi)
            if len(cases) != ennemi.emplacements:
                raise ValueError(f"Ennemi {ennemi.id} : {len(cases)} case(s) pour {ennemi.emplacements} emplacement(s)")
            if len({case.rangee for case in cases}) != 1:
                raise ValueError(f"Ennemi {ennemi.id} : ses cases doivent etre sur la meme rangee")
        if not self._par_case:
            raise ValueError("Une flotte a au moins un ennemi")

    @property
    def ennemis(self) -> list[EnnemiNew]:
        """Tous les ennemis, detruits compris, une fois chacun, dans l'ordre de jeu."""
        return list(self._ennemis)

    def ennemis_vivants(self) -> list[EnnemiNew]:
        """Ennemis vivants dans l'ordre de jeu (decision utilisateur, refonte-combat.md 5.1)."""
        return [ennemi for ennemi in self.ennemis if not ennemi.est_detruit()]

    def ennemis_vivants_de_colonne(self, colonne: Colonne) -> list[EnnemiNew]:
        return [ennemi for ennemi in self.ennemis_vivants() if any(
            case.colonne == colonne for case in self.cases_de(ennemi)
        )]

    def ennemi_en(self, case: Position) -> EnnemiNew | None:
        """Ennemi vivant sur cette case, None si elle est vide ou si son ennemi est detruit."""
        ennemi = self._par_case.get(case)
        return None if ennemi is None or ennemi.est_detruit() else ennemi

    def cases_de(self, ennemi: EnnemiNew) -> list[Position]:
        index = next((i for i, deja in enumerate(self._ennemis) if deja is ennemi), None)
        if index is None:
            raise ValueError(f"Ennemi {ennemi.id} : absent de cette flotte")
        return list(self._cases[index])

    def cases_vivantes(self) -> list[Position]:
        return [case for case in ORDRE_DE_JEU if self.ennemi_en(case) is not None]

    def rangee_de(self, ennemi: EnnemiNew) -> Rangee:
        return self.cases_de(ennemi)[0].rangee

    def est_vide(self) -> bool:
        """Tous les ennemis sont detruits : victoire."""
        return not self.ennemis_vivants()
