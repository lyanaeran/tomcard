"""
Les ennemis affrontes en combat : points de vie, bouclier, buffs/debuffs actifs, et la liste
d'Actions qui determine leur comportement au tour ennemi (specs.md paragraphe 13).
"""

from dataclasses import dataclass
from enum import Enum, auto

from src.gameplay.carte import ActionCarte, BuffActif


class TypeActionEnnemi(Enum):
    """Nature de l'effet d'une Action ennemie (specs.md 13)."""

    ATTAQUE = auto()
    POSE_BUFF = auto()


class CibleActionEnnemi(Enum):
    """Qui une Action ennemie touche (specs.md 13).

    PROXIMITE : meme regle que le ciblage historique (ciblage.py:module_cible_par_ennemi) - la
    rangee de l'ennemi d'abord, puis les rangees voisines si elle est vide.
    TOUS_MODULES_JOUEUR : tous les modules du joueur encore en vie (attaque de zone).
    COLONNE_AVANT_SINON_ARRIERE_JOUEUR : un module du joueur tire au hasard dans la colonne
    avant (base incluse) si elle compte au moins un module vivant, sinon dans la colonne
    arriere.
    COLONNE_AVANT_SINON_ARRIERE_ENNEMIE : un ennemi de la flotte tire au hasard (l'ennemi qui
    execute l'action y compris, specs.md 13 - ex. Miroir peut se cibler lui-meme) dans la
    colonne avant si elle compte au moins un ennemi vivant, sinon dans la colonne arriere.
    SOI_MEME : l'ennemi qui execute l'action.
    """

    PROXIMITE = auto()
    TOUS_MODULES_JOUEUR = auto()
    COLONNE_AVANT_SINON_ARRIERE_JOUEUR = auto()
    COLONNE_AVANT_SINON_ARRIERE_ENNEMIE = auto()
    SOI_MEME = auto()


@dataclass(frozen=True)
class ActionEnnemi:
    """Une action du comportement d'un ennemi (specs.md 13) : declenchee tous les `frequence`
    tours ennemi a partir de `tour_depart` (tour 1 = premier tour ennemi du combat, cf.
    active_au_tour), repetee `repetitions` fois a chaque declenchement (dans le meme tour).
    `action_buff`/`duree_buff` ne s'appliquent qu'a type=POSE_BUFF : quel ActionCarte poser
    (cf. carte.py, ex. BOUCLIER_PAR_TOUR/BOUCLIER_MIROIR), et sa duree (None = persistant)."""

    type: TypeActionEnnemi
    cible: CibleActionEnnemi
    valeur: int
    frequence: int = 1
    tour_depart: int = 1
    repetitions: int = 1
    action_buff: ActionCarte | None = None
    duree_buff: int | None = None

    def active_au_tour(self, tour: int) -> bool:
        """Indique si cette action se declenche a ce tour ennemi (1 = premier tour ennemi du
        combat) : a partir de tour_depart, puis tous les `frequence` tours."""
        return tour >= self.tour_depart and (tour - self.tour_depart) % self.frequence == 0


class Ennemi:
    """Represente un ennemi affronte en combat."""

    def __init__(
        self,
        pv_max: int,
        actions: list[ActionEnnemi] | None = None,
        nom: str = "Ennemi",
        image: str | None = None,
        taille: str = "S",
        emplacements: int = 1,
    ):
        self.pv_max = pv_max
        self.pv = pv_max
        self.bouclier = 0
        self.nom = nom
        self.image = image
        self.taille = taille
        # Nombre de cases de la grille ennemie occupees par cet ennemi (specs.md 3.2) : 1 dans
        # tous les cas actuels sauf le Boss des pirates (2, une case Avant + une Arriere de la
        # meme rangee) - independant de `taille`, purement informatif (cf. donnees.py). C'est
        # Flotte qui materialise cette occupation (le meme objet Ennemi range a 2 Positions).
        self.emplacements = emplacements
        self.actions = actions or []
        self.buffs_actifs: list[BuffActif] = []

    def est_detruit(self) -> bool:
        """Renvoie True si l'ennemi n'a plus de points de vie."""
        return self.pv <= 0

    def subir_degats(self, degats: int) -> None:
        """Applique des degats, en absorbant d'abord avec le bouclier (specs.md 3.5, meme
        principe que Module.subir_degats - les ennemis peuvent desormais en avoir, specs.md 13)."""
        degats_restants = max(0, degats - self.bouclier)
        self.bouclier = max(0, self.bouclier - degats)
        self.pv = max(0, self.pv - degats_restants)

    def ajouter_bouclier(self, valeur: int) -> None:
        """Ajoute du bouclier a l'ennemi."""
        self.bouclier += valeur

    def appliquer_buff(
        self, action: ActionCarte, valeur: int, tours: int | None, cible_reflet=None
    ) -> None:
        """Ajoute un nouveau buff/debuff actif (specs.md 13 - meme liste pour les deux, la
        distinction n'est que semantique) et declenche son effet immediat si BOUCLIER_PAR_TOUR
        (ajoute du bouclier). Contrairement a Module, aucun redeclenchement automatique a
        chaque tour ennemi : c'est la frequence de l'Action qui pose ce buff qui decide quand
        il est repose (cf. ActionEnnemi.active_au_tour). Independant des buffs deja actifs :
        n'ecrase ni ne fusionne rien, meme un buff du meme type deja present. cible_reflet
        (uniquement pour BOUCLIER_MIROIR, cf. carte.py:BuffActif) : module du joueur qui
        recevra les degats renvoyes quand le joueur attaquera cet ennemi."""
        buff = BuffActif(action=action, valeur=valeur, tours_restants=tours, cible_reflet=cible_reflet)
        self.buffs_actifs.append(buff)
        if action == ActionCarte.BOUCLIER_PAR_TOUR:
            self.ajouter_bouclier(valeur)

    def _somme_buffs(self, action: ActionCarte) -> int:
        return sum(buff.valeur for buff in self.buffs_actifs if buff.action == action)

    def degats_attaque_effectifs(self, valeur_brute: int) -> int:
        """Degats reellement infliges par une Action ATTAQUE de cet ennemi (valeur_brute =
        ActionEnnemi.valeur) : la somme des augmentations actives (specs.md 13, Boss des
        pirates) est ajoutee, celle des reductions actives est soustraite."""
        augmentation = self._somme_buffs(ActionCarte.AUGMENTATION_DEGATS)
        reduction = self._somme_buffs(ActionCarte.REDUCTION_DEGATS)
        return max(0, valeur_brute + augmentation - reduction)

    def degats_subis(self, degats: int) -> int:
        """Degats bruts d'une carte, majores par la somme des vulnerabilites actives de cet ennemi."""
        vulnerabilite = self._somme_buffs(ActionCarte.VULNERABILITE)
        if vulnerabilite:
            return round(degats * (1 + vulnerabilite / 100))
        return degats

    def decrementer_buffs(self) -> None:
        """A appeler une fois par tour ennemi ecoule : fait expirer les buffs/debuffs a duree
        (specs.md 12.1/12.4/13 - chaque instance decompte independamment, meme si l'ennemi n'a
        pas agi). Les buffs persistants (tours_restants=None) ne decomptent jamais."""
        for buff in self.buffs_actifs:
            if buff.tours_restants is not None:
                buff.tours_restants -= 1
        self.buffs_actifs = [buff for buff in self.buffs_actifs if buff.tours_restants is None or buff.tours_restants > 0]
