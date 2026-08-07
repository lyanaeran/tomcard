"""
Configuration du combat du POC (cf. poc.md).

Toutes les valeurs numeriques (PV, degats, cout des cartes) sont inventees faute
d'etre specifiees ailleurs - a ajuster apres test (poc.md paragraphe 1).
"""

from src.gameplay.carte import CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN, fabriquer_kit
from src.gameplay.combat import Combat
from src.gameplay.deck import Deck
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

ELECTRICITE_PAR_TOUR = 3

# Modules du joueur, cf. poc.md paragraphe 2
PV_BASE = 15
PV_AVANT_GAUCHE = 12
PV_AVANT_DROITE = 18
PV_ARRIERE_GAUCHE = 10
PV_ARRIERE_DROITE = 9

KIT_AVANT_GAUCHE = fabriquer_kit("Avant-Gauche", cout=1, degats=9, bouclier=4, soin=3)
KIT_AVANT_DROITE = fabriquer_kit("Avant-Droite", cout=1, degats=5, bouclier=7, soin=3)
KIT_ARRIERE_GAUCHE = fabriquer_kit("Arriere-Gauche", cout=1, degats=4, bouclier=3, soin=6)
KIT_ARRIERE_DROITE = fabriquer_kit("Arriere-Droite", cout=1, degats=10, bouclier=2, soin=2)

# Ennemis, cf. poc.md paragraphe 3 (mix S/M, 2 cases laissees vides)
# Stockes comme donnees brutes (pas des instances Ennemi partagees, qui sont mutables :
# chaque combat doit repartir avec des ennemis frais, pas ceux d'un combat precedent).
_CONFIG_ENNEMIS = [
    (Position(Colonne.AVANT, Rangee.GAUCHE), 8, 4, "Ennemi S"),
    (Position(Colonne.AVANT, Rangee.DROITE), 16, 8, "Ennemi M"),
    (Position(Colonne.ARRIERE, Rangee.GAUCHE), 8, 4, "Ennemi S"),
    (Position(Colonne.ARRIERE, Rangee.MID), 16, 8, "Ennemi M"),
]


def _nouvelle_flotte() -> Flotte:
    """Construit une flotte fraiche (nouvelles instances Ennemi) pour un nouveau combat."""
    ennemis = {
        position: Ennemi(pv_max=pv_max, degats_attaque=degats, nom=nom)
        for position, pv_max, degats, nom in _CONFIG_ENNEMIS
    }
    return Flotte(ennemis)


def _kit_de_base() -> tuple:
    return CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN


def _composition_deck() -> list:
    """5x Attaque + 3x Bouclier + 1x Soin pour chacun des 5 kits (poc.md paragraphe 5)."""
    cartes = []
    for attaque, bouclier, soin in (
        _kit_de_base(),
        KIT_AVANT_GAUCHE,
        KIT_AVANT_DROITE,
        KIT_ARRIERE_GAUCHE,
        KIT_ARRIERE_DROITE,
    ):
        cartes += [attaque] * 5 + [bouclier] * 3 + [soin] * 1
    return cartes


def creer_combat_poc() -> Combat:
    """Cree un combat pret a l'emploi avec les valeurs du POC (poc.md)."""
    vaisseau = Vaisseau(
        base=Module(pv_max=PV_BASE),
        avant_gauche=Module(pv_max=PV_AVANT_GAUCHE),
        avant_droite=Module(pv_max=PV_AVANT_DROITE),
        arriere_gauche=Module(pv_max=PV_ARRIERE_GAUCHE),
        arriere_droite=Module(pv_max=PV_ARRIERE_DROITE),
    )
    deck = Deck(cartes=_composition_deck())
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=ELECTRICITE_PAR_TOUR)
    return Combat(joueur=joueur, flotte=_nouvelle_flotte())
