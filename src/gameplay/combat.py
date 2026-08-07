"""
Moteur du combat 1 contre 1 du POC (cf. poc.md).
"""

from enum import Enum, auto

from src.gameplay.carte import Carte, TypeCarte
from src.gameplay.ennemi import Ennemi
from src.gameplay.joueur import Joueur


class EtatCombat(Enum):
    """Etat courant du combat."""

    EN_COURS = auto()
    VICTOIRE = auto()
    DEFAITE = auto()


class Combat:
    """Orchestre le deroulement du combat entre le joueur et l'ennemi."""

    def __init__(self, joueur: Joueur, ennemi: Ennemi):
        self.joueur = joueur
        self.ennemi = ennemi
        self.etat = EtatCombat.EN_COURS
        self.joueur.debut_de_tour()

    def jouer_carte(self, carte: Carte) -> None:
        """Applique l'effet d'une carte jouee par le joueur, si le combat est en cours."""
        if self.etat != EtatCombat.EN_COURS:
            return
        if not self.joueur.peut_jouer(carte):
            return
        self.joueur.depenser_electricite(carte.cout)
        self.joueur.deck.jouer(carte)
        self._appliquer_effet(carte)
        self._verifier_fin_de_combat()

    def finir_tour_joueur(self) -> None:
        """Termine le tour du joueur (defausse la main restante) et enchaine sur le tour de l'ennemi."""
        if self.etat != EtatCombat.EN_COURS:
            return
        self.joueur.deck.defausser_main()
        self._tour_ennemi()
        if self.etat == EtatCombat.EN_COURS:
            self.joueur.debut_de_tour()

    def _appliquer_effet(self, carte: Carte) -> None:
        """Applique l'effet d'une carte selon son type (specs.md paragraphe 7.1)."""
        if carte.type == TypeCarte.ATTAQUE:
            self.ennemi.subir_degats(carte.valeur)
        elif carte.type == TypeCarte.DEFENSE:
            self.joueur.module.ajouter_bouclier(carte.valeur)
        elif carte.type == TypeCarte.SOIN:
            self.joueur.module.soigner(carte.valeur)

    def _tour_ennemi(self) -> None:
        """L'ennemi attaque automatiquement (poc.md paragraphe 3)."""
        self.joueur.module.subir_degats(self.ennemi.degats_attaque)
        self._verifier_fin_de_combat()

    def _verifier_fin_de_combat(self) -> None:
        """Met a jour l'etat du combat si l'ennemi ou le module de base est detruit."""
        if self.ennemi.est_detruit():
            self.etat = EtatCombat.VICTOIRE
        elif self.joueur.module.est_detruit():
            self.etat = EtatCombat.DEFAITE
