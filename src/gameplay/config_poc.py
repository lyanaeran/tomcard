"""
Configuration du combat du POC (cf. poc.md).
"""

from src.gameplay.carte import CARTE_ATTAQUE, CARTE_BOUCLIER, CARTE_SOIN
from src.gameplay.combat import Combat
from src.gameplay.deck import Deck
from src.gameplay.ennemi import Ennemi
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module

# Valeurs du POC, cf. poc.md paragraphe 2 et 3
PV_MODULE_BASE = 15
PV_ENNEMI = 15
DEGATS_ENNEMI = 7
ELECTRICITE_PAR_TOUR = 3

# Composition du deck, cf. poc.md paragraphe 5
COMPOSITION_DECK = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_SOIN] * 1


def creer_combat_poc() -> Combat:
    """Cree un combat pret a l'emploi avec les valeurs du POC (poc.md)."""
    module = Module(pv_max=PV_MODULE_BASE)
    deck = Deck(cartes=list(COMPOSITION_DECK))
    joueur = Joueur(module=module, deck=deck, electricite_par_tour=ELECTRICITE_PAR_TOUR)
    ennemi = Ennemi(pv_max=PV_ENNEMI, degats_attaque=DEGATS_ENNEMI)
    return Combat(joueur=joueur, ennemi=ennemi)
