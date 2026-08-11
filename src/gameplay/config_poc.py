"""
Generation aleatoire du combat du POC a partir des fichiers de config/ (cf. poc.md).

A chaque combat : le module principal est fixe, 4 modules differents sont tires au
sort parmi les autres et places sur les 4 emplacements, les 6 cases ennemies sont
tirees au sort (avec remise), et le deck (20 cartes) est tire au sort a partir des
jeux de cartes des modules retenus. Une fois dans le deck, une carte n'est plus
liee au module dont elle provient.
"""

import random

from src.gameplay.carte import Carte
from src.gameplay.combat import Combat
from src.gameplay.deck import Deck
from src.gameplay.donnees import SpecEnnemi, SpecModule, charger_cartes, charger_ennemis, charger_modules
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

ELECTRICITE_PAR_TOUR = 3
ID_MODULE_PRINCIPAL = "MOD_1"
NOMBRE_MODULES_EQUIPES = 4
CARTES_PAR_MODULE_PRINCIPAL = 8
CARTES_PAR_MODULE_EQUIPE = 3

POSITIONS_MODULES_EQUIPES = (
    Position(Colonne.AVANT, Rangee.GAUCHE),
    Position(Colonne.AVANT, Rangee.DROITE),
    Position(Colonne.ARRIERE, Rangee.GAUCHE),
    Position(Colonne.ARRIERE, Rangee.DROITE),
)

POSITIONS_ENNEMIES = (
    Position(Colonne.AVANT, Rangee.GAUCHE),
    Position(Colonne.AVANT, Rangee.MID),
    Position(Colonne.AVANT, Rangee.DROITE),
    Position(Colonne.ARRIERE, Rangee.GAUCHE),
    Position(Colonne.ARRIERE, Rangee.MID),
    Position(Colonne.ARRIERE, Rangee.DROITE),
)


def _module_depuis_spec(spec: SpecModule) -> Module:
    return Module(pv_max=spec.points_de_vie, nom=spec.nom, image=spec.image)


def _ennemi_depuis_spec(spec: SpecEnnemi) -> Ennemi:
    return Ennemi(pv_max=spec.points_de_vie, degats_attaque=spec.degats_attaque, nom=spec.nom, image=spec.image)


def tirer_cartes(pool_ids: tuple, quantite: int, cartes: dict[str, Carte], aleatoire: random.Random) -> list[Carte]:
    """Tire `quantite` cartes au hasard, avec remise, parmi les ids de la pool donnee."""
    return [cartes[aleatoire.choice(pool_ids)] for _ in range(quantite)]


def creer_vaisseau(specs_modules: list[SpecModule], aleatoire: random.Random) -> tuple[Vaisseau, list[SpecModule]]:
    """Place le module principal et tire au sort 4 modules differents sur les 4 emplacements."""
    spec_principal = next(spec for spec in specs_modules if spec.id == ID_MODULE_PRINCIPAL)
    specs_equipables = [spec for spec in specs_modules if spec.id != ID_MODULE_PRINCIPAL]
    specs_choisies = aleatoire.sample(specs_equipables, NOMBRE_MODULES_EQUIPES)

    modules_par_position = dict(zip(POSITIONS_MODULES_EQUIPES, (_module_depuis_spec(spec) for spec in specs_choisies)))
    vaisseau = Vaisseau(
        base=_module_depuis_spec(spec_principal),
        avant_gauche=modules_par_position[Position(Colonne.AVANT, Rangee.GAUCHE)],
        avant_droite=modules_par_position[Position(Colonne.AVANT, Rangee.DROITE)],
        arriere_gauche=modules_par_position[Position(Colonne.ARRIERE, Rangee.GAUCHE)],
        arriere_droite=modules_par_position[Position(Colonne.ARRIERE, Rangee.DROITE)],
    )
    return vaisseau, [spec_principal, *specs_choisies]


def creer_deck(specs_utilisees: list[SpecModule], cartes: dict[str, Carte], aleatoire: random.Random) -> Deck:
    """Tire au sort 8 cartes du module principal (le premier de la liste) et 3 de chaque autre."""
    spec_principal, *specs_equipes = specs_utilisees
    deck_cartes = tirer_cartes(spec_principal.cartes, CARTES_PAR_MODULE_PRINCIPAL, cartes, aleatoire)
    for spec in specs_equipes:
        deck_cartes += tirer_cartes(spec.cartes, CARTES_PAR_MODULE_EQUIPE, cartes, aleatoire)
    return Deck(cartes=deck_cartes, generateur_aleatoire=aleatoire)


def creer_flotte(specs_ennemis: list[SpecEnnemi], aleatoire: random.Random) -> Flotte:
    """Tire au sort un ennemi (avec remise) pour chacune des 6 cases de la grille ennemie."""
    ennemis = {
        position: _ennemi_depuis_spec(aleatoire.choice(specs_ennemis)) for position in POSITIONS_ENNEMIES
    }
    return Flotte(ennemis)


def creer_combat_poc(generateur_aleatoire: random.Random | None = None) -> Combat:
    """Genere un combat aleatoire (modules, ennemis, deck) a partir de config/ (poc.md)."""
    aleatoire = generateur_aleatoire or random.Random()
    cartes = charger_cartes()
    specs_modules = charger_modules()
    specs_ennemis = charger_ennemis()

    vaisseau, specs_utilisees = creer_vaisseau(specs_modules, aleatoire)
    deck = creer_deck(specs_utilisees, cartes, aleatoire)
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=ELECTRICITE_PAR_TOUR)
    flotte = creer_flotte(specs_ennemis, aleatoire)

    return Combat(joueur=joueur, flotte=flotte)
