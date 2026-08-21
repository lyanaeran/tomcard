"""
Generation aleatoire du combat du POC a partir des fichiers de config/ (cf. poc.md).

A chaque combat : le module principal est fixe (deck de base fige, cf. `_deck_module_principal`),
4 modules differents sont tires au sort parmi les autres et places sur les 4 emplacements, les 6
cases ennemies sont tirees au sort (avec remise), et 3 cartes de chaque module equipe sont tirees
au sort dans leur pool respectif. Une fois dans le deck, une carte n'est plus liee au module dont
elle provient.

Chaque tirage cree un exemplaire independant (Carte.copie()) : deux copies de la meme carte dans
le deck ont chacune leur propre compteur de munitions (specs.md paragraphe 3.6).
"""

import random

from src.gameplay.carte import Carte, RareteCarte
from src.gameplay.combat import Combat
from src.gameplay.deck import Deck
from src.gameplay.donnees import SpecEnnemi, SpecModule, charger_cartes, charger_ennemis, charger_modules
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

ELECTRICITE_PAR_TOUR = 5
ID_MODULE_PRINCIPAL = "MOD_1"
NOMBRE_MODULES_EQUIPES = 4
# Deck de base du module principal (12 cartes) : chaque carte de rarete Base une fois, sauf
# Laser et Bouclier, 4 exemplaires chacune (regle donnee explicitement par l'utilisateur).
NOMS_QUADRUPLES_MODULE_PRINCIPAL = ("Laser", "Bouclier")
# Nombre de cartes tirees au hasard par module equipe (regle interimaire : la regle cible
# "2 Communes + 1 Rare + 1 Legendaire" par module equipe necessite qu'aucun module n'ait de
# pool vide a un palier de rarete donne, ce qui n'est pas encore le cas pour tous les modules
# equipables - voir specs.md paragraphe 12. A remplacer une fois tous les modules pourvus.)
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
    """Tire `quantite` cartes au hasard, avec remise, parmi les ids de la pool donnee.

    Chaque tirage renvoie un exemplaire independant (copie()), meme si le meme id est tire
    plusieurs fois : les munitions (specs.md 3.6) se comptent par exemplaire physique.
    """
    return [cartes[aleatoire.choice(pool_ids)].copie() for _ in range(quantite)]


def _deck_module_principal(spec_principal: SpecModule, cartes: dict[str, Carte]) -> list[Carte]:
    """Deck de base fixe du module principal (12 cartes, pas de tirage aleatoire) : chaque
    carte de rarete Base de sa pool une fois, sauf Laser et Bouclier en 4 exemplaires."""
    deck_cartes = []
    for id_carte in spec_principal.cartes:
        carte = cartes[id_carte]
        if carte.rarete != RareteCarte.BASE:
            continue
        quantite = 4 if carte.nom in NOMS_QUADRUPLES_MODULE_PRINCIPAL else 1
        deck_cartes += [carte.copie() for _ in range(quantite)]
    return deck_cartes


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
    """Deck de base fixe du module principal (le premier de la liste, 12 cartes, cf.
    `_deck_module_principal`) + 3 cartes tirees au sort dans la pool de chaque autre module."""
    spec_principal, *specs_equipes = specs_utilisees
    deck_cartes = _deck_module_principal(spec_principal, cartes)
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

    return Combat(joueur=joueur, flotte=flotte, aleatoire=aleatoire)
