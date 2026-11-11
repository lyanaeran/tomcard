"""
Statuts de la refonte (buffs, debuffs, bouclier) portes en combat par un module (ModuleNew) ou un
ennemi (EnnemiNew) : specs/refonte-statuts.md. Pas encore branche au moteur : remplacera
carte.py:BuffActif et les champs bouclier des entites actuelles.

Un statut est un nombre (son intensite) range dans un dictionnaire Statut -> intensite ; absent
signifie 0. Chaque Statut declare sa regle (RegleStatut) : comment une nouvelle pose se cumule
avec l'ancienne, et comment il s'eteint. Les deux camps partagent tout le code ; seul le moment de
la fin de tour differe (fin du tour du joueur pour un ennemi, fin du tour ennemi pour un module).
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class CumulStatut(Enum):
    """Ce que fait une nouvelle pose d'un statut deja present."""

    # Les intensites s'additionnent (bouclier, incendie)
    ADDITION = auto()
    # La nouvelle pose remplace l'ancienne, non cumulable (leurre)
    REMPLACEMENT = auto()


class ExtinctionStatut(Enum):
    """Comment un statut disparait."""

    # Baisse de 1 a chaque fin de tour (bouclier, incendie)
    MOINS_UN_PAR_TOUR = auto()
    # Valable de la pose jusqu'au debut du tour suivant du camp qui l'a pose, puis disparait
    # entierement (renvoi de Miroir) : c'est la fin de tour de l'entite qui le porte
    TOUR_SUIVANT = auto()
    # Ne baisse qu'en etant consomme par les attaques recues (leurre)
    CONSOMMATION = auto()


@dataclass(frozen=True)
class RegleStatut:
    cumul: CumulStatut
    extinction: ExtinctionStatut


class Statut(Enum):
    """Un statut porte par un module ou un ennemi ; sa regle est donnee par REGLES_STATUT."""

    # Absorbe les degats avant les PV, a hauteur de son intensite
    BOUCLIER = auto()
    # Inflige son intensite en degats a la fin du tour (absorbes par le bouclier, jamais renvoyes),
    # avant de baisser de 1 (poison de Slay the Spire)
    INCENDIE = auto()
    # Renvoie a l'attaquant les degats recus jusqu'a son intensite, qui diminue d'autant ;
    # l'entite encaisse le reste (Miroir)
    RENVOI = auto()
    # Annule entierement la prochaine attaque recue, puis disparait (carte Leurre) ; intensite 1
    LEURRE = auto()

    @property
    def regle(self) -> RegleStatut:
        return REGLES_STATUT[self]


# Decisions utilisateur : bouclier et incendie -1 par tour, cumulables ; renvoi cumulable, valable
# jusqu'au tour suivant (2026-11-11, pose seulement par l'ennemi Miroir pour l'instant) ; leurre
# consomme par la premiere attaque (specs/refonte-statuts.md 3).
REGLES_STATUT = {
    Statut.BOUCLIER: RegleStatut(CumulStatut.ADDITION, ExtinctionStatut.MOINS_UN_PAR_TOUR),
    Statut.INCENDIE: RegleStatut(CumulStatut.ADDITION, ExtinctionStatut.MOINS_UN_PAR_TOUR),
    Statut.RENVOI: RegleStatut(CumulStatut.ADDITION, ExtinctionStatut.TOUR_SUIVANT),
    Statut.LEURRE: RegleStatut(CumulStatut.REMPLACEMENT, ExtinctionStatut.CONSOMMATION),
}


@dataclass(frozen=True)
class Encaissement:
    """Resultat d'une attaque recue, une fois les statuts appliques."""

    # Degats a retirer des PV
    degats_pv: int
    # Degats a renvoyer a l'attaquant (statut RENVOI)
    renvoyes: int = 0


@dataclass
class Statuts:
    """Les statuts d'une entite en combat. Lecture et ecriture d'une intensite toujours par
    statuts[statut] (jamais directement dans `intensites`) : un statut absent se lit 0, une
    intensite mise a 0 retire le statut. Pour poser un statut selon sa regle de cumul : ajouter."""

    intensites: dict[Statut, int] = field(default_factory=dict)

    def __getitem__(self, statut: Statut) -> int:
        """Intensite du statut, 0 s'il est absent."""
        return self.intensites.get(statut, 0)

    def __setitem__(self, statut: Statut, intensite: int) -> None:
        """Fixe l'intensite brute (sans regle de cumul) ; 0 ou moins retire le statut."""
        if intensite > 0:
            self.intensites[statut] = intensite
        else:
            self.intensites.pop(statut, None)

    def ajouter(self, statut: Statut, intensite: int) -> None:
        """Pose un statut selon son cumul ; une intensite nulle ou negative ne pose rien."""
        if intensite <= 0:
            return
        if statut.regle.cumul == CumulStatut.ADDITION:
            intensite += self[statut]
        self[statut] = intensite

    def retirer(self, statut: Statut, quantite: int) -> int:
        """Baisse un statut d'au plus `quantite` ; renvoie ce qui a ete reellement retire."""
        retire = min(self[statut], max(0, quantite))
        self[statut] -= retire
        return retire

    def absorber_par_bouclier(self, degats: int) -> int:
        """Le bouclier absorbe ce qu'il peut ; renvoie les degats restants."""
        return degats - self.retirer(Statut.BOUCLIER, degats)

    def encaisser_attaque(self, degats: int) -> Encaissement:
        """Ordre d'une attaque recue : le leurre l'annule entierement (et se consomme) ; sinon le
        renvoi prend les degats jusqu'a son intensite, puis le bouclier absorbe le reste avant
        les PV."""
        if self.retirer(Statut.LEURRE, 1):
            return Encaissement(degats_pv=0)
        renvoyes = self.retirer(Statut.RENVOI, degats)
        return Encaissement(degats_pv=self.absorber_par_bouclier(degats - renvoyes), renvoyes=renvoyes)

    def fin_de_tour(self) -> int:
        """Fin de tour de l'entite (decision utilisateur) : l'incendie frappe d'abord, absorbe par
        le bouclier, puis chaque statut s'eteint selon sa regle (bouclier et incendie -1, renvoi
        retire). Renvoie les degats d'incendie a retirer des PV."""
        degats_pv = self.absorber_par_bouclier(self[Statut.INCENDIE])
        for statut in list(self.intensites):
            extinction = statut.regle.extinction
            if extinction == ExtinctionStatut.MOINS_UN_PAR_TOUR:
                self[statut] -= 1
            elif extinction == ExtinctionStatut.TOUR_SUIVANT:
                self[statut] = 0
        return degats_pv
