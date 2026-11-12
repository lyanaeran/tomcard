"""
Flotte de la refonte (FlotteNew) : les ennemis en combat (copies d'EnnemiNew) places sur la grille
ennemie (specs/refonte-combat.md 2.2, 5.1). Remplace flotte.py:Flotte. La classe recoit les
ennemis deja places ; la composition des flottes du parcours (quels ennemis selon le niveau, et
leur placement) est faite par les fonctions en bas de ce fichier (refonte-branchement.md 2,
decision 4 : memes regles que l'ancien moteur, config_poc.py, avec les ennemis de la refonte).

Un ennemi sur plusieurs cases (Boss des pirates) est le meme objet range a plusieurs cases : il
n'est compte, touche et joue qu'une fois.
"""

import random

from src.gameplay.ennemi_new import EnnemiNew, PlacementEnnemi
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


# --- Composition des flottes du parcours (refonte-branchement.md 2, decision 4) ---

# Nombre d'ennemis d'un combat Prime : 1 jusqu'au niveau 5 inclus, 2 ensuite (specs.md 2.1/13)
NIVEAU_PRIME_DEUX_ENNEMIS = 6
# Combat "Affronter les pirates" de l'Aventure Asteroides (specs.md 2.5)
NOMBRE_ENNEMIS_ASTEROIDES = 3
# Boss des niveaux multiples de 10 (specs.md 2.3/13) : un seul pour l'instant
ID_BOSS = "ENM_BOSS_PIRATES"
# Coefficient de difficulte des ennemis du parcours : 1 pour l'instant (decision 4), a regler
# par niveau apres le branchement
COEFFICIENT_PARCOURS = 1

CASES_AVANT = tuple(Position(Colonne.AVANT, rangee) for rangee in Rangee)
CASES_ARRIERE = tuple(Position(Colonne.ARRIERE, rangee) for rangee in Rangee)


def nombre_ennemis_prime(niveau: int) -> int:
    return 1 if niveau < NIVEAU_PRIME_DEUX_ENNEMIS else 2


def ennemis_standard(modeles: dict[str, EnnemiNew]) -> list[EnnemiNew]:
    """Ennemis tirables au hasard : ceux d'une seule case (le Boss a sa flotte fixe)."""
    return [modele for modele in modeles.values() if modele.emplacements == 1]


def placer_ennemis(ennemis: list[EnnemiNew], aleatoire: random.Random) -> FlotteNew:
    """Place des ennemis d'une case selon leur preference (specs.md 13, comme
    config_poc._placer_specs_avec_preference) : les protecteurs d'abord a l'avant, puis les
    proteges a l'arriere, puis les autres a l'avant, sinon a l'arriere ; cases tirees au hasard
    dans chaque colonne. Au plus 6 ennemis."""
    avant, arriere = list(CASES_AVANT), list(CASES_ARRIERE)
    aleatoire.shuffle(avant)
    aleatoire.shuffle(arriere)
    places: dict[Position, EnnemiNew] = {}
    reste = list(ennemis)
    for preference, colonne in ((PlacementEnnemi.PROTECTEUR_AVANT, avant), (PlacementEnnemi.PROTEGE_ARRIERE, arriere)):
        for ennemi in [e for e in reste if e.placement == preference]:
            if colonne:
                places[colonne.pop(0)] = ennemi
                reste.remove(ennemi)
    for ennemi in reste:
        places[(avant or arriere).pop(0)] = ennemi
    return FlotteNew(places)


def _tirer_ennemis(modeles: dict[str, EnnemiNew], nombre: int, aleatoire: random.Random) -> list[EnnemiNew]:
    """`nombre` ennemis standard tires au hasard (avec remise), prets pour le combat."""
    pool = ennemis_standard(modeles)
    return [aleatoire.choice(pool).pour_combat(COEFFICIENT_PARCOURS) for _ in range(nombre)]


def flotte_prime(modeles: dict[str, EnnemiNew], niveau: int, aleatoire: random.Random) -> FlotteNew:
    """Flotte d'un combat Prime : nombre_ennemis_prime(niveau) ennemis tires et places."""
    return placer_ennemis(_tirer_ennemis(modeles, nombre_ennemis_prime(niveau), aleatoire), aleatoire)


def flotte_asteroides(modeles: dict[str, EnnemiNew], aleatoire: random.Random) -> FlotteNew:
    """Flotte du choix "Affronter les pirates" : NOMBRE_ENNEMIS_ASTEROIDES ennemis tires et places
    (placement prefere respecte, decision 4)."""
    return placer_ennemis(_tirer_ennemis(modeles, NOMBRE_ENNEMIS_ASTEROIDES, aleatoire), aleatoire)


def flotte_boss(modeles: dict[str, EnnemiNew]) -> FlotteNew:
    """Flotte du Boss : le Boss des pirates seul, sur les deux cases de la rangee du milieu."""
    boss = modeles[ID_BOSS].pour_combat(COEFFICIENT_PARCOURS)
    return FlotteNew({Position(Colonne.AVANT, Rangee.MID): boss, Position(Colonne.ARRIERE, Rangee.MID): boss})
