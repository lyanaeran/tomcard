"""
Vaisseau de combat (Vaisseau) : les modules en combat (copies de Module) places sur la
grille du joueur (specs.md 3.1).

Grille 2 lignes (avant, arriere) x 3 colonnes (gauche, milieu, droite). Le principal occupe toute
la colonne du milieu (les deux lignes) ; les quatre autres emplacements correspondent chacun a une
case.
"""

from collections.abc import Iterable

from src.gameplay.module import Module
from src.gameplay.position import Ligne, Position, Colonne, ordre_colonnes_par_proximite

# Cases occupees par chaque emplacement (Module.emplacement)
CASES_PAR_EMPLACEMENT = {
    "base": (Position(Ligne.AVANT, Colonne.MID), Position(Ligne.ARRIERE, Colonne.MID)),
    "avant_gauche": (Position(Ligne.AVANT, Colonne.GAUCHE),),
    "arriere_gauche": (Position(Ligne.ARRIERE, Colonne.GAUCHE),),
    "avant_droite": (Position(Ligne.AVANT, Colonne.DROITE),),
    "arriere_droite": (Position(Ligne.ARRIERE, Colonne.DROITE),),
}


class Vaisseau:
    """Les modules du joueur pendant un combat, sur leurs cases."""

    def __init__(self, modules: Iterable[Module]):
        self.modules: list[Module] = list(modules)
        self._par_case: dict[Position, Module] = {}
        for module in self.modules:
            if module.pv_combat is None:
                raise ValueError(f"Module {module.id} : le vaisseau de combat prend des copies de combat")
            if module.emplacement not in CASES_PAR_EMPLACEMENT:
                raise ValueError(f"Module {module.id} : emplacement inconnu {module.emplacement!r}")
            if module.principal != (module.emplacement == "base"):
                raise ValueError(f"Module {module.id} : le principal, et lui seul, occupe l'emplacement base")
            for case in CASES_PAR_EMPLACEMENT[module.emplacement]:
                if case in self._par_case:
                    raise ValueError(f"Emplacement {module.emplacement} occupe deux fois")
                self._par_case[case] = module
        if Position(Ligne.AVANT, Colonne.MID) not in self._par_case:
            raise ValueError("Le vaisseau n'a pas de module principal")
        exemplaires = [module.exemplaire for module in self.modules]
        if None in exemplaires or len(set(exemplaires)) != len(exemplaires):
            raise ValueError("Chaque module doit avoir un identifiant d'exemplaire unique")

    @property
    def principal(self) -> Module:
        return self._par_case[Position(Ligne.AVANT, Colonne.MID)]

    def module_en(self, case: Position) -> Module | None:
        """Module vivant sur cette case, None si elle est vide ou si son module est detruit."""
        module = self._par_case.get(case)
        return None if module is None or module.est_detruit() else module

    def module_d_exemplaire(self, exemplaire: str) -> Module | None:
        """Module de cet identifiant d'exemplaire ("M3"), detruit ou non."""
        return next((module for module in self.modules if module.exemplaire == exemplaire), None)

    def modules_vivants(self) -> list[Module]:
        return [module for module in self.modules if not module.est_detruit()]

    def modules_vivants_de_ligne(self, ligne: Ligne) -> list[Module]:
        """Modules vivants de cette ligne ; le principal est dans les deux."""
        return [module for module in self.modules_vivants() if any(
            case.ligne == ligne for case in CASES_PAR_EMPLACEMENT[module.emplacement]
        )]

    def cases_vivantes(self) -> list[Position]:
        """Cases occupees par un module vivant."""
        return [case for case, module in self._par_case.items() if not module.est_detruit()]

    def module_le_plus_proche(self, colonne_ennemi: Colonne) -> Module | None:
        """Module vise par une attaque PROXIMITE d'un ennemi de cette colonne : sa colonne d'abord
        (avant puis arriere), puis les colonnes voisines (meme regle que ciblage.py)."""
        for colonne in ordre_colonnes_par_proximite(colonne_ennemi):
            for ligne in (Ligne.AVANT, Ligne.ARRIERE):
                module = self.module_en(Position(ligne, colonne))
                if module is not None:
                    return module
        return None
