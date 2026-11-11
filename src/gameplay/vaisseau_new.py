"""
Vaisseau de la refonte (VaisseauNew) : les modules en combat (copies de ModuleNew) places sur la
grille du joueur (specs/refonte-combat.md 2.2). Pas encore branche au moteur : remplacera
vaisseau.py:Vaisseau.

Grille 2 colonnes (avant, arriere) x 3 rangees (gauche, milieu, droite). Le principal occupe toute
la rangee du milieu (les deux colonnes) ; les quatre autres emplacements correspondent chacun a une
case.
"""

from collections.abc import Iterable

from src.gameplay.module_new import ModuleNew
from src.gameplay.position import Colonne, Position, Rangee, ordre_rangees_par_proximite

# Cases occupees par chaque emplacement (ModuleNew.emplacement)
CASES_PAR_EMPLACEMENT = {
    "base": (Position(Colonne.AVANT, Rangee.MID), Position(Colonne.ARRIERE, Rangee.MID)),
    "avant_gauche": (Position(Colonne.AVANT, Rangee.GAUCHE),),
    "arriere_gauche": (Position(Colonne.ARRIERE, Rangee.GAUCHE),),
    "avant_droite": (Position(Colonne.AVANT, Rangee.DROITE),),
    "arriere_droite": (Position(Colonne.ARRIERE, Rangee.DROITE),),
}


class VaisseauNew:
    """Les modules du joueur pendant un combat, sur leurs cases."""

    def __init__(self, modules: Iterable[ModuleNew]):
        self.modules: list[ModuleNew] = list(modules)
        self._par_case: dict[Position, ModuleNew] = {}
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
        if Position(Colonne.AVANT, Rangee.MID) not in self._par_case:
            raise ValueError("Le vaisseau n'a pas de module principal")
        exemplaires = [module.exemplaire for module in self.modules]
        if None in exemplaires or len(set(exemplaires)) != len(exemplaires):
            raise ValueError("Chaque module doit avoir un identifiant d'exemplaire unique")

    @property
    def principal(self) -> ModuleNew:
        return self._par_case[Position(Colonne.AVANT, Rangee.MID)]

    def module_en(self, case: Position) -> ModuleNew | None:
        """Module vivant sur cette case, None si elle est vide ou si son module est detruit."""
        module = self._par_case.get(case)
        return None if module is None or module.est_detruit() else module

    def module_d_exemplaire(self, exemplaire: str) -> ModuleNew | None:
        """Module de cet identifiant d'exemplaire ("M3"), detruit ou non."""
        return next((module for module in self.modules if module.exemplaire == exemplaire), None)

    def modules_vivants(self) -> list[ModuleNew]:
        return [module for module in self.modules if not module.est_detruit()]

    def modules_vivants_de_colonne(self, colonne: Colonne) -> list[ModuleNew]:
        """Modules vivants de cette colonne ; le principal est dans les deux."""
        return [module for module in self.modules_vivants() if any(
            case.colonne == colonne for case in CASES_PAR_EMPLACEMENT[module.emplacement]
        )]

    def cases_vivantes(self) -> list[Position]:
        """Cases occupees par un module vivant."""
        return [case for case, module in self._par_case.items() if not module.est_detruit()]

    def module_le_plus_proche(self, rangee_ennemi: Rangee) -> ModuleNew | None:
        """Module vise par une attaque PROXIMITE d'un ennemi de cette rangee : sa rangee d'abord
        (avant puis arriere), puis les rangees voisines (meme regle que ciblage.py)."""
        for rangee in ordre_rangees_par_proximite(rangee_ennemi):
            for colonne in (Colonne.AVANT, Colonne.ARRIERE):
                module = self.module_en(Position(colonne, rangee))
                if module is not None:
                    return module
        return None
