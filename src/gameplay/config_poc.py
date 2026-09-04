"""
Generation aleatoire du combat du POC a partir des fichiers de config/.

A chaque combat : le module principal est fixe (deck de base fige, cf. `deck_module_principal`),
4 modules differents sont tires au sort parmi les autres et places sur les 4 emplacements, les 6
cases ennemies sont tirees au sort (avec remise), et 3 cartes de chaque module equipe sont tirees
au sort dans leur pool respectif. Une fois dans le deck, une carte n'est plus liee au module dont
elle provient.

Chaque tirage cree un exemplaire independant (Carte.copie()) : deux copies de la meme carte dans
le deck ont chacune leur propre compteur de munitions (specs.md paragraphe 3.6).

MODE_TEST (variable ci-dessous) remplace ce tirage aleatoire du deck et les PV normaux par une
configuration pensee pour les tests manuels - voir sa docstring.
"""

import random

from src.gameplay.carte import Carte, RareteCarte, TypeCarte
from src.gameplay.combat import Combat
from src.gameplay.deck import Deck
from src.gameplay.donnees import SpecEnnemi, SpecModule, charger_cartes, charger_ennemis, charger_modules
from src.gameplay.ennemi import Ennemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

# Mode test : bascule creer_combat_poc() ET combat_depuis_partie() (src/gameplay/partie.py, vrai
# combat du parcours) dans une configuration pensee pour les tests manuels plutot que pour le
# gameplay normal - PV du joueur enormement augmentes (survivre de nombreux tours sans mourir),
# PV et nombre d'ennemis abaisses, cartes de degats de base surpuissantes (tuer un ennemi en un
# coup, pour enchainer les tests sans y passer plusieurs tours), et (creer_combat_poc()
# uniquement) un exemplaire de chaque carte jouable existante dans le deck plutot que le tirage
# aleatoire habituel par module equipe, pour pouvoir essayer toutes les mecaniques en un seul
# combat. False = comportement normal (production, decision utilisateur) : PV reels de
# config/modules.json, flotte composee selon le niveau (creer_flotte_prime/creer_flotte_boss).
MODE_TEST = False
PV_MODULE_MODE_TEST = 200
PV_ENNEMI_MODE_TEST = 20
# Nombre de cases ennemies peuplees (sur les 6 de la grille, POSITIONS_ENNEMIES) en mode test -
# moins d'ennemis a vaincre par combat pour accelerer les essais manuels.
NOMBRE_ENNEMIS_MODE_TEST = 2
# Valeur (degats) appliquee aux cartes ATTAQUE de rarete Base (Laser, Laser percant,
# Bombardement) en mode test uniquement - superieure a PV_ENNEMI_MODE_TEST pour tuer un ennemi en
# un coup. Les autres cartes gardent leur valeur normale (config/cartes.json).
VALEUR_ATTAQUE_BASE_MODE_TEST = 20

ELECTRICITE_PAR_TOUR = 3
ID_MODULE_PRINCIPAL = "MOD_1"
NOMBRE_MODULES_EQUIPES = 4
# Deck de base du module principal (10 cartes) : chaque carte de rarete Base une fois, sauf
# Laser et Bouclier, 4 exemplaires chacune (regle donnee explicitement par l'utilisateur).
# Bombardement et Reparation retires de ce module (decision utilisateur) : Bombardement sera
# reintroduit sous une forme modifiee comme carte du Lanceur de missiles, Reparation comme carte
# de l'Atelier - aucun des deux n'est encore pret (cf. config/modules.json, cartes.json les garde
# telles quelles en attendant, juste detachees de la liste `cartes` du module principal).
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
    pv_max = PV_MODULE_MODE_TEST if MODE_TEST else spec.points_de_vie
    return Module(pv_max=pv_max, nom=spec.nom, image=spec.image)


def _ennemi_depuis_spec(spec: SpecEnnemi) -> Ennemi:
    pv_max = PV_ENNEMI_MODE_TEST if MODE_TEST else spec.points_de_vie
    return Ennemi(pv_max=pv_max, actions=list(spec.actions), nom=spec.nom, image=spec.image, taille=spec.taille)


def tirer_cartes(pool_ids: tuple, quantite: int, cartes: dict[str, Carte], aleatoire: random.Random) -> list[Carte]:
    """Tire `quantite` cartes au hasard, avec remise, parmi les ids de la pool donnee.

    Chaque tirage renvoie un exemplaire independant (copie()), meme si le meme id est tire
    plusieurs fois : les munitions (specs.md 3.6) se comptent par exemplaire physique.
    """
    return [cartes[aleatoire.choice(pool_ids)].copie() for _ in range(quantite)]


def ids_deck_module_principal(spec_principal: SpecModule, cartes: dict[str, Carte]) -> list[str]:
    """Ids des cartes du deck de base du module principal (meme regle que deck_module_principal,
    sous forme d'ids plutot que d'exemplaires Carte - utilise par la persistance du parcours,
    cf. src/gameplay/partie.py)."""
    ids = []
    for id_carte in spec_principal.cartes:
        carte = cartes[id_carte]
        if carte.rarete != RareteCarte.BASE:
            continue
        quantite = 4 if carte.nom in NOMS_QUADRUPLES_MODULE_PRINCIPAL else 1
        ids += [id_carte] * quantite
    return ids


def deck_module_principal(spec_principal: SpecModule, cartes: dict[str, Carte]) -> list[Carte]:
    """Deck de base fixe du module principal (10 cartes, pas de tirage aleatoire) : chaque
    carte de rarete Base de sa pool une fois, sauf Laser et Bouclier en 4 exemplaires."""
    return [cartes[id_carte].copie() for id_carte in ids_deck_module_principal(spec_principal, cartes)]


def creer_vaisseau(specs_modules: list[SpecModule], aleatoire: random.Random) -> tuple[Vaisseau, list[SpecModule]]:
    """Place le module principal et tire au sort 4 modules differents sur les 4 emplacements."""
    spec_principal = next(spec for spec in specs_modules if spec.id == ID_MODULE_PRINCIPAL)
    # Exclut les modules dont les cartes ne sont pas encore concues (cartes vide dans
    # modules.json) : les tirer planterait creer_deck (tirer_cartes sur une pool vide).
    specs_equipables = [spec for spec in specs_modules if spec.id != ID_MODULE_PRINCIPAL and spec.cartes]
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
    """Deck de base fixe du module principal (le premier de la liste, 10 cartes, cf.
    `deck_module_principal`) + 3 cartes tirees au sort dans la pool de chaque autre module."""
    spec_principal, *specs_equipes = specs_utilisees
    deck_cartes = deck_module_principal(spec_principal, cartes)
    for spec in specs_equipes:
        deck_cartes += tirer_cartes(spec.cartes, CARTES_PAR_MODULE_EQUIPE, cartes, aleatoire)
    return Deck(cartes=deck_cartes, generateur_aleatoire=aleatoire)


def appliquer_degats_mode_test(cartes: list[Carte]) -> None:
    """Mode test (cf. MODE_TEST) : les cartes ATTAQUE de rarete Base (Laser, Laser percant,
    Bombardement) infligent VALEUR_ATTAQUE_BASE_MODE_TEST degats (tuer un ennemi en un coup, cf.
    PV_ENNEMI_MODE_TEST) ; les autres cartes gardent leur valeur normale. Modifie `cartes` en
    place - reutilisee par creer_deck_mode_test() ci-dessous et par
    src/gameplay/partie.py:combat_depuis_partie() (vrai combat du parcours, deck reel de la
    partie plutot qu'un deck de demonstration)."""
    for carte in cartes:
        if carte.rarete == RareteCarte.BASE and carte.type == TypeCarte.ATTAQUE:
            carte.valeur = VALEUR_ATTAQUE_BASE_MODE_TEST


def creer_deck_mode_test(cartes: dict[str, Carte], aleatoire: random.Random) -> Deck:
    """Mode test (cf. MODE_TEST) : un exemplaire de chaque carte jouable existante, quels que
    soient les modules tires au sort - pour pouvoir essayer toutes les mecaniques en un seul
    combat plutot que de dependre du tirage aleatoire habituel."""
    deck_cartes = [carte.copie() for carte in cartes.values()]
    appliquer_degats_mode_test(deck_cartes)
    return Deck(cartes=deck_cartes, generateur_aleatoire=aleatoire)


def creer_flotte(specs_ennemis: list[SpecEnnemi], aleatoire: random.Random) -> Flotte:
    """Tire au sort un ennemi (avec remise) pour chacune des 6 cases de la grille ennemie - en
    mode test, seules les NOMBRE_ENNEMIS_MODE_TEST premieres (POSITIONS_ENNEMIES) sont peuplees,
    pour accelerer les essais manuels. Utilisee par creer_combat_poc() (demonstration, sans
    notion de niveau) - le vrai parcours utilise creer_flotte_prime/creer_flotte_boss ci-dessous
    (specs.md 2.1/13)."""
    positions = POSITIONS_ENNEMIES[:NOMBRE_ENNEMIS_MODE_TEST] if MODE_TEST else POSITIONS_ENNEMIES
    ennemis = {position: _ennemi_depuis_spec(aleatoire.choice(specs_ennemis)) for position in positions}
    return Flotte(ennemis)


# Preference de position en flotte d'un ennemi (SpecEnnemi.placement, specs.md 13) : un
# protecteur (Petit Jean) prend une case avant en priorite, un protege (Le nettoyeur) une case
# arriere - pour se retrouver effectivement protege par un protecteur avant quand les deux sont
# tires ensemble.
PLACEMENT_PROTECTEUR_AVANT = "PROTECTEUR_AVANT"
PLACEMENT_PROTEGE_ARRIERE = "PROTEGE_ARRIERE"


def _placer_specs_avec_preference(specs: list[SpecEnnemi], aleatoire: random.Random) -> dict[Position, SpecEnnemi]:
    """Place des ennemis tires au sort sur la grille en respectant leur preference de position
    (specs.md 13, PLACEMENT_PROTECTEUR_AVANT/PLACEMENT_PROTEGE_ARRIERE ci-dessus) : les
    protecteurs d'abord (case avant), puis les proteges (case arriere), puis le reste (premiere
    case avant restante, sinon arriere) - cases tirees au hasard au sein de chaque colonne pour
    ne pas toujours occuper les memes."""
    positions_avant = [position for position in POSITIONS_ENNEMIES if position.colonne == Colonne.AVANT]
    positions_arriere = [position for position in POSITIONS_ENNEMIES if position.colonne == Colonne.ARRIERE]
    aleatoire.shuffle(positions_avant)
    aleatoire.shuffle(positions_arriere)

    resultat: dict[Position, SpecEnnemi] = {}
    reste = list(specs)
    for spec in [s for s in reste if s.placement == PLACEMENT_PROTECTEUR_AVANT]:
        if positions_avant:
            resultat[positions_avant.pop(0)] = spec
            reste.remove(spec)
    for spec in [s for s in reste if s.placement == PLACEMENT_PROTEGE_ARRIERE]:
        if positions_arriere:
            resultat[positions_arriere.pop(0)] = spec
            reste.remove(spec)
    for spec in reste:
        if positions_avant:
            resultat[positions_avant.pop(0)] = spec
        elif positions_arriere:
            resultat[positions_arriere.pop(0)] = spec
    return resultat


# Nombre d'ennemis d'un combat Prime standard (specs.md 2.1/13, decision utilisateur) : un seul
# jusqu'au Niveau 5 inclus, deux a partir du Niveau 6 - remplace le tirage systematique des 6
# cases de creer_flotte pour le vrai parcours (combat_depuis_partie).
NOMBRE_ENNEMIS_PRIME_NIVEAU_FAIBLE = 1
NOMBRE_ENNEMIS_PRIME_NIVEAU_ELEVE = 2
NIVEAU_PRIME_DEUX_ENNEMIS = 6


def nombre_ennemis_prime(niveau: int) -> int:
    """1 ennemi jusqu'au Niveau 5 inclus, 2 a partir du Niveau 6 (specs.md 2.1/13)."""
    if niveau < NIVEAU_PRIME_DEUX_ENNEMIS:
        return NOMBRE_ENNEMIS_PRIME_NIVEAU_FAIBLE
    return NOMBRE_ENNEMIS_PRIME_NIVEAU_ELEVE


def creer_flotte_prime(specs_ennemis: list[SpecEnnemi], niveau: int, aleatoire: random.Random) -> Flotte:
    """Flotte d'un combat Prime standard (specs.md 2.1/2.3/13) : nombre_ennemis_prime(niveau)
    ennemis tires au hasard (avec remise) dans le pool actuel, places selon leur preference de
    position (_placer_specs_avec_preference)."""
    specs_tirees = [aleatoire.choice(specs_ennemis) for _ in range(nombre_ennemis_prime(niveau))]
    positions = _placer_specs_avec_preference(specs_tirees, aleatoire)
    return Flotte({position: _ennemi_depuis_spec(spec) for position, spec in positions.items()})


# Composition fixe du Boss (specs.md 2.3/13, niveaux multiples de 10, decision utilisateur) :
# aucun tirage aleatoire, contrairement a un combat Prime standard.
ID_ENNEMI_PETIT_JEAN = "ENM_PETIT_JEAN"
ID_ENNEMI_LE_NETTOYEUR = "ENM_LE_NETTOYEUR"
ID_ENNEMI_LE_PUZZLE = "ENM_LE_PUZZLE"


def creer_flotte_boss(specs_ennemis: list[SpecEnnemi]) -> Flotte:
    """Flotte du Boss (specs.md 2.3/13) : 2 Petit Jean en avant (protecteurs), Le nettoyeur et
    Le puzzle en arriere - composition fixe donnee par l'utilisateur, pas de tirage au sort."""
    specs_par_id = {spec.id: spec for spec in specs_ennemis}
    petit_jean = specs_par_id[ID_ENNEMI_PETIT_JEAN]
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): _ennemi_depuis_spec(petit_jean),
        Position(Colonne.AVANT, Rangee.DROITE): _ennemi_depuis_spec(petit_jean),
        Position(Colonne.ARRIERE, Rangee.GAUCHE): _ennemi_depuis_spec(specs_par_id[ID_ENNEMI_LE_NETTOYEUR]),
        Position(Colonne.ARRIERE, Rangee.DROITE): _ennemi_depuis_spec(specs_par_id[ID_ENNEMI_LE_PUZZLE]),
    }
    return Flotte(ennemis)


# Combat scripte du choix "Affronter les pirates" (Aventure Asteroides, specs.md 2.5) :
# approximation decidee - un nombre fixe d'ennemis tires du pool actuel, distincte du tirage
# standard d'un combat Prime (creer_flotte_prime, qui varie avec le niveau).
NOMBRE_ENNEMIS_ASTEROIDES = 3


def creer_flotte_asteroides(specs_ennemis: list[SpecEnnemi], aleatoire: random.Random) -> Flotte:
    """Flotte scriptee a NOMBRE_ENNEMIS_ASTEROIDES ennemis tires au hasard (avec remise) dans le
    pool actuel, sur les premieres cases de POSITIONS_ENNEMIES."""
    positions = POSITIONS_ENNEMIES[:NOMBRE_ENNEMIS_ASTEROIDES]
    ennemis = {position: _ennemi_depuis_spec(aleatoire.choice(specs_ennemis)) for position in positions}
    return Flotte(ennemis)


def creer_combat_poc(generateur_aleatoire: random.Random | None = None) -> Combat:
    """Genere un combat aleatoire (modules, ennemis, deck) a partir de config/."""
    aleatoire = generateur_aleatoire or random.Random()
    cartes = charger_cartes()
    specs_modules = charger_modules()
    specs_ennemis = charger_ennemis()

    vaisseau, specs_utilisees = creer_vaisseau(specs_modules, aleatoire)
    deck = creer_deck_mode_test(cartes, aleatoire) if MODE_TEST else creer_deck(specs_utilisees, cartes, aleatoire)
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=ELECTRICITE_PAR_TOUR)
    flotte = creer_flotte(specs_ennemis, aleatoire)

    return Combat(joueur=joueur, flotte=flotte, aleatoire=aleatoire)
