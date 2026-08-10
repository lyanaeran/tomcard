"""
Moteur du combat entre le vaisseau du joueur et une flotte d'ennemis (cf. poc.md).
"""

from enum import Enum, auto

from src.gameplay.carte import CIBLES_SANS_CLIC, Carte, CibleCarte, TypeCarte
from src.gameplay.ciblage import module_cible_par_ennemi
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position


class EtatCombat(Enum):
    """Etat courant du combat."""

    EN_COURS = auto()
    VICTOIRE = auto()
    DEFAITE = auto()


def _degats_effectifs(cible: Module | Ennemi, degats: int) -> int:
    """Combien de PV+bouclier une cible va reellement perdre pour ces degats, sans
    depasser ce qu'il lui reste (specs.md paragraphe 3.5 : le bouclier absorbe en premier)."""
    return min(degats, cible.pv + getattr(cible, "bouclier", 0))


class Combat:
    """Orchestre le deroulement du combat entre le joueur et la flotte ennemie."""

    def __init__(self, joueur: Joueur, flotte: Flotte):
        self.joueur = joueur
        self.flotte = flotte
        self.etat = EtatCombat.EN_COURS
        self.joueur.debut_de_tour()

    def jouer_carte(self, carte: Carte, cible: Module | Ennemi | None = None) -> list[tuple[Module | Ennemi, int]]:
        """Applique l'effet d'une carte jouee par le joueur.

        cible est ignoree pour les cartes de CIBLES_SANS_CLIC (elles touchent tout
        un camp) et obligatoire sinon. Renvoie, pour chaque cible effectivement
        touchee, le montant reellement applique (degats/bouclier/soin, qui peut etre
        inferieur a carte.valeur : cf. `_appliquer_effet_simple`) ; liste vide si la
        carte n'a pas ete jouee.
        """
        if self.etat != EtatCombat.EN_COURS:
            return []
        if not self.joueur.peut_jouer(carte):
            return []
        if not self._cible_valide(carte, cible):
            return []
        self.joueur.depenser_electricite(carte.cout)
        self.joueur.deck.jouer(carte)
        cibles_touchees = self._appliquer_effet(carte, cible)
        self._verifier_fin_de_combat()
        return cibles_touchees

    def finir_tour_joueur(self) -> list[tuple[Position, Ennemi, Module, int]]:
        """Termine le tour du joueur (defausse la main restante) et enchaine sur le tour ennemi.

        Renvoie la liste des attaques resolues (position et ennemi attaquant, module cible,
        degats reellement infliges), pour permettre a l'UI d'animer chaque attaque.
        """
        if self.etat != EtatCombat.EN_COURS:
            return []
        self.joueur.deck.defausser_main()
        attaques = self._tour_ennemi()
        if self.etat == EtatCombat.EN_COURS:
            self.joueur.debut_de_tour()
        return attaques

    def previsualiser_cible(self, ennemi: Ennemi) -> Module | None:
        """Renvoie le module que cet ennemi attaquerait s'il agissait maintenant (pour le survol UI)."""
        position = self._position_de_ennemi(ennemi)
        if position is None:
            return None
        return module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)

    def _modules_vivants(self) -> list[Module]:
        """Tous les modules du joueur encore en vie (base incluse)."""
        modules = [self.joueur.vaisseau.base, *self.joueur.vaisseau.modules_equipes().values()]
        return [m for m in modules if not m.est_detruit()]

    def _cible_valide(self, carte: Carte, cible: Module | Ennemi | None) -> bool:
        """Verifie que la cible correspond au type de carte et est bien vivante dans ce combat."""
        if carte.cible in CIBLES_SANS_CLIC:
            return cible is None
        if carte.cible == CibleCarte.ENNEMI_UNIQUE:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants()
        if carte.cible == CibleCarte.ALLIE_UNIQUE:
            return isinstance(cible, Module) and cible in self._modules_vivants()
        if carte.cible == CibleCarte.LIGNE_ENNEMIE:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants()
        return False

    def _appliquer_effet(self, carte: Carte, cible: Module | Ennemi | None) -> list[tuple[Module | Ennemi, int]]:
        """Applique l'effet d'une carte selon sa cible (specs.md 7.1/7.2).

        Renvoie, pour chaque cible effectivement touchee, le montant reellement applique.
        """
        if carte.cible == CibleCarte.ALLIES_MULTIPLES:
            cibles = self._modules_vivants()
        elif carte.cible == CibleCarte.ENNEMIS_MULTIPLES:
            cibles = self.flotte.ennemis_vivants()
        elif carte.cible == CibleCarte.LIGNE_ENNEMIE:
            position = self._position_de_ennemi(cible)
            occupants = (self.flotte.ennemi_en(colonne, position.rangee) for colonne in (Colonne.AVANT, Colonne.ARRIERE))
            cibles = [occupant for occupant in occupants if occupant is not None]
        else:
            cibles = [cible]
        return [(une_cible, self._appliquer_effet_simple(carte, une_cible)) for une_cible in cibles]

    def _appliquer_effet_simple(self, carte: Carte, cible: Module | Ennemi) -> int:
        """Applique l'effet d'une carte a une seule cible, selon son type (specs.md 7.1).

        Renvoie le montant reellement applique, qui peut etre inferieur a carte.valeur :
        les degats sont plafonnes par les PV+bouclier restants de la cible, le soin par
        son PV max (le bouclier, lui, n'est jamais plafonne).
        """
        if carte.type == TypeCarte.ATTAQUE:
            valeur_effective = _degats_effectifs(cible, carte.valeur)
            cible.subir_degats(carte.valeur)
        elif carte.type == TypeCarte.DEFENSE:
            valeur_effective = carte.valeur
            cible.ajouter_bouclier(carte.valeur)
        else:
            valeur_effective = min(carte.valeur, cible.pv_max - cible.pv)
            cible.soigner(carte.valeur)
        return valeur_effective

    def _tour_ennemi(self) -> list[tuple[Position, Ennemi, Module, int]]:
        """Chaque ennemi vivant attaque sa cible, dans l'ordre de la grille (poc.md paragraphe 3)."""
        attaques = []
        for position, ennemi in self.flotte.positions().items():
            if ennemi.est_detruit():
                continue
            cible = module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)
            if cible is not None:
                degats_effectifs = _degats_effectifs(cible, ennemi.degats_attaque)
                cible.subir_degats(ennemi.degats_attaque)
                attaques.append((position, ennemi, cible, degats_effectifs))
            self._verifier_fin_de_combat()
            if self.etat != EtatCombat.EN_COURS:
                break
        return attaques

    def _position_de_ennemi(self, ennemi: Ennemi) -> Position | None:
        """Retrouve la position d'un ennemi dans la flotte, ou None s'il n'y est pas."""
        for position, occupant in self.flotte.positions().items():
            if occupant is ennemi:
                return position
        return None

    def _verifier_fin_de_combat(self) -> None:
        """Met a jour l'etat du combat si la flotte ou le module de base est detruit."""
        if self.flotte.est_vide():
            self.etat = EtatCombat.VICTOIRE
        elif self.joueur.vaisseau.est_detruit():
            self.etat = EtatCombat.DEFAITE
