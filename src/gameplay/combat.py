"""
Moteur du combat entre le vaisseau du joueur et une flotte d'ennemis (cf. poc.md).
"""

from enum import Enum, auto

from src.gameplay.carte import Carte, CibleCarte, TypeCarte
from src.gameplay.ciblage import module_cible_par_ennemi
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Position


class EtatCombat(Enum):
    """Etat courant du combat."""

    EN_COURS = auto()
    VICTOIRE = auto()
    DEFAITE = auto()


class Combat:
    """Orchestre le deroulement du combat entre le joueur et la flotte ennemie."""

    def __init__(self, joueur: Joueur, flotte: Flotte):
        self.joueur = joueur
        self.flotte = flotte
        self.etat = EtatCombat.EN_COURS
        self.joueur.debut_de_tour()

    def jouer_carte(self, carte: Carte, cible: Module | Ennemi) -> None:
        """Applique l'effet d'une carte jouee par le joueur sur la cible choisie."""
        if self.etat != EtatCombat.EN_COURS:
            return
        if not self.joueur.peut_jouer(carte):
            return
        if not self._cible_valide(carte, cible):
            return
        self.joueur.depenser_electricite(carte.cout)
        self.joueur.deck.jouer(carte)
        self._appliquer_effet(carte, cible)
        self._verifier_fin_de_combat()

    def finir_tour_joueur(self) -> list[tuple[Position, Ennemi, Module]]:
        """Termine le tour du joueur (defausse la main restante) et enchaine sur le tour ennemi.

        Renvoie la liste des attaques resolues (position et ennemi attaquant, module cible),
        pour permettre a l'UI d'animer chaque attaque.
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
        position = self._position_de(ennemi)
        if position is None:
            return None
        return module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)

    def _cible_valide(self, carte: Carte, cible: Module | Ennemi) -> bool:
        """Verifie que la cible correspond au type de carte et est bien vivante dans ce combat."""
        if carte.cible == CibleCarte.ENNEMI:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants()
        if carte.cible == CibleCarte.ALLIE:
            modules_vivants = [self.joueur.vaisseau.base, *self.joueur.vaisseau.modules_equipes().values()]
            return isinstance(cible, Module) and cible in modules_vivants and not cible.est_detruit()
        return False

    def _appliquer_effet(self, carte: Carte, cible: Module | Ennemi) -> None:
        """Applique l'effet d'une carte sur la cible choisie, selon son type (specs.md 7.1)."""
        if carte.type == TypeCarte.ATTAQUE:
            cible.subir_degats(carte.valeur)
        elif carte.type == TypeCarte.DEFENSE:
            cible.ajouter_bouclier(carte.valeur)
        elif carte.type == TypeCarte.SOIN:
            cible.soigner(carte.valeur)

    def _tour_ennemi(self) -> list[tuple[Position, Ennemi, Module]]:
        """Chaque ennemi vivant attaque sa cible, dans l'ordre de la grille (poc.md paragraphe 3)."""
        attaques = []
        for position, ennemi in self.flotte.positions().items():
            if ennemi.est_detruit():
                continue
            cible = module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)
            if cible is not None:
                cible.subir_degats(ennemi.degats_attaque)
                attaques.append((position, ennemi, cible))
            self._verifier_fin_de_combat()
            if self.etat != EtatCombat.EN_COURS:
                break
        return attaques

    def _position_de(self, ennemi: Ennemi) -> Position | None:
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
