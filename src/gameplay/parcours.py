"""
Logique du parcours (run), hors combat (specs.md paragraphe 2/2.3/2.1/2.4/6). Pour l'instant : le
tirage des candidats du Niveau 1 (choix de module), celui des recompenses de fin de combat, et
celui des propositions d'etape des autres niveaux (specs.md 2.4, ecran "Choix du prochain niveau").
"""

import random
from collections.abc import Iterable
from enum import Enum, auto
from typing import TypeVar

from src.gameplay.carte_new import CarteNew, RareteCarte
from src.gameplay.module_new import ModuleNew

NOMBRE_CANDIDATS_MODULE = 3

T = TypeVar("T")


def modules_equipables(modules: Iterable[ModuleNew]) -> list[ModuleNew]:
    """Modeles de modules pouvant etre proposes en choix : tous sauf le module principal, deja
    acquis d'office en debut de run (specs.md paragraphe 5), sauf ceux marques non jouables dans
    module_new.json (seul le Lanceur de missiles l'est pendant la refonte) et sauf ceux sans
    carte."""
    return [module for module in modules if not module.principal and module.jouable and module.cartes]


def tirer_candidats_module(
    pool: list[ModuleNew], aleatoire: random.Random, quantite: int = NOMBRE_CANDIDATS_MODULE
) -> list[ModuleNew]:
    """Tire `quantite` modules differents au hasard dans la pool (specs.md paragraphe 2.3,
    Niveau 1) : uniforme pour l'instant, puisqu'aucun module n'est encore possede a ce stade du
    run (donc pas de ponderation par doublons a appliquer - cf. specs.md 2.3 "points encore
    ouverts" pour les tirages ulterieurs, apres un Boss, une fois des modules deja possedes).
    Moins de `quantite` candidats si la pool est plus petite (modules non jouables exclus)."""
    return aleatoire.sample(pool, min(quantite, len(pool)))


# Recompenses de fin de combat (specs.md 2.1/6, decision utilisateur) : la rarete d'une carte
# candidate est tiree en premier, independamment du reste. Les cartes Base ne sont jamais
# proposees en recompense (deck de depart uniquement, cf. specs.md 7.3).
PROBABILITE_LEGENDAIRE = 0.05
PROBABILITE_RARE = 0.20
_ORDRE_RARETES_RECOMPENSE = (RareteCarte.LEGENDAIRE, RareteCarte.RARE, RareteCarte.COMMUNE)


def tirer_rarete_recompense(aleatoire: random.Random) -> RareteCarte:
    """5% Legendaire, 20% Rare, sinon (75%) Commune (specs.md 2.1/6)."""
    tirage = aleatoire.random()
    if tirage < PROBABILITE_LEGENDAIRE:
        return RareteCarte.LEGENDAIRE
    if tirage < PROBABILITE_LEGENDAIRE + PROBABILITE_RARE:
        return RareteCarte.RARE
    return RareteCarte.COMMUNE


def tirer_carte_recompense(pool: list[CarteNew], aleatoire: random.Random) -> CarteNew | None:
    """Tire une carte de recompense dans `pool` (deja jouable, Base exclue en amont par
    pool_module/pool_toutes_cartes) : la rarete est tiree en premier (tirer_rarete_recompense),
    puis une carte au hasard parmi celles de `pool` a cette rarete precise. Si `pool` n'a aucune
    carte a la rarete tiree, redescend au palier inferieur (Legendaire -> Rare -> Commune) pour
    ne jamais renvoyer aucune recompense a cause d'un pool encore peu fourni a ce palier (ex. un
    module avec une seule carte Commune pour l'instant). None uniquement si `pool` est vide."""
    if not pool:
        return None
    rarete_visee = tirer_rarete_recompense(aleatoire)
    index_depart = _ORDRE_RARETES_RECOMPENSE.index(rarete_visee)
    for rarete in _ORDRE_RARETES_RECOMPENSE[index_depart:]:
        candidates = [carte for carte in pool if carte.rarete == rarete]
        if candidates:
            return aleatoire.choice(candidates)
    return None


def _proposable(carte: CarteNew) -> bool:
    """Carte proposable en recompense : jouable (champ de carte_new.json) et hors Base."""
    return carte.jouable and carte.rarete != RareteCarte.BASE


# Raretes qu'un module propose selon son palier de mise a jour (Station service, specs.md 2.2/6,
# decision utilisateur du 2026-11-13 : regle de la spec appliquee) : palier 1 Commune seulement,
# palier 2 + Rare, palier 3 + Legendaire
RARETES_PAR_NIVEAU_MAJ = {
    1: (RareteCarte.COMMUNE,),
    2: (RareteCarte.COMMUNE, RareteCarte.RARE),
    3: (RareteCarte.COMMUNE, RareteCarte.RARE, RareteCarte.LEGENDAIRE),
}


def pool_module(module: ModuleNew, cartes: dict[str, CarteNew]) -> list[CarteNew]:
    """Modeles des cartes que ce module peut proposer (specs.md 2.1/6) : les siennes, jouables,
    non-Base, d'une rarete ouverte par son palier de mise a jour (RARETES_PAR_NIVEAU_MAJ ; un
    modele ou un exemplaire neuf est au palier 1)."""
    raretes = RARETES_PAR_NIVEAU_MAJ[module.niveau_maj]
    return [
        cartes[id_carte] for id_carte in module.cartes
        if id_carte in cartes and _proposable(cartes[id_carte]) and cartes[id_carte].rarete in raretes
    ]


def pool_toutes_cartes(cartes: dict[str, CarteNew]) -> list[CarteNew]:
    """Toutes les cartes jouables non-Base, tous modules et toutes raretes confondus (carte
    offerte par l'Aventure Asteroides, specs.md 2.5 : pas de palier de mise a jour)."""
    return [carte for carte in cartes.values() if _proposable(carte)]


def tirer_candidats_carte_module(
    module: ModuleNew, cartes: dict[str, CarteNew], aleatoire: random.Random, quantite: int = 3
) -> list[CarteNew]:
    """Tire jusqu'a `quantite` cartes candidates DISTINCTES dans le pool jouable non-Base de ce
    module (specs.md 2.3, apres le choix de module en debut de partie - le joueur en choisit une
    a ajouter a son deck, ou passe). Meme tirage pondere par rarete que tirer_carte_recompense a
    chaque tirage, sur un pool qui retrecit a mesure (jamais deux fois la meme carte parmi les
    candidats) - moins de `quantite` si le pool du module en compte moins."""
    pool_restant = list(pool_module(module, cartes))
    candidats: list[CarteNew] = []
    for _ in range(quantite):
        carte = tirer_carte_recompense(pool_restant, aleatoire)
        if carte is None:
            break
        candidats.append(carte)
        pool_restant.remove(carte)
    return candidats


def tirer_candidats_recompense(
    modules: list[ModuleNew], cartes: dict[str, CarteNew], aleatoire: random.Random
) -> list[tuple[ModuleNew, CarteNew | None]]:
    """Un candidat de recompense par module utilise dans ce combat (specs.md 2.1/6), au maximum
    5 (base + 4 equipes, cf. specs.md 5) : chaque module, module principal inclus, pioche dans
    son propre pool de cartes jouables non-Base (pool_module) - jamais dans le pool entier du
    jeu (bug corrige : le module principal piochait auparavant parmi toutes les cartes du jeu au
    lieu des siennes, cf. CLAUDE.md). Candidat a None si le pool de ce module est vide (aucune
    carte jouable non-Base actuellement associee). `modules` : les exemplaires de la partie ;
    chaque carte candidate est un nouvel exemplaire rattache a l'exemplaire de son module."""
    candidats = []
    for module in modules:
        carte = tirer_carte_recompense(pool_module(module, cartes), aleatoire)
        candidats.append((module, carte.copie(exemplaire_module=module.exemplaire) if carte else None))
    return candidats


# Choix du prochain niveau (specs.md 2.3/2.4), pour tous les niveaux sauf le 1 (choix de module,
# pas de tirage). Aux niveaux Boss (multiples de 10), une seule proposition forcee (TypeEtape.BOSS,
# decision utilisateur : ecran de choix avec un seul bouton "Combattre le Boss !", pas d'enchainement
# automatique direct vers le combat). Ne couvre pour l'instant que les niveaux 2 a 10 : le run
# s'arrete reellement au Niveau 10 dans l'etat actuel (decision utilisateur, specs.md 2), donc le
# motif 5/9/10 n'a pas encore besoin de se repeter par decennie (question encore ouverte, specs.md 9.1).


class TypeEtape(Enum):
    """Type d'etape propose au joueur a un niveau donne (specs.md 2/2.4)."""

    PRIME = auto()
    STATION_SERVICE = auto()
    PLANETE_COMMERCIALE = auto()
    AVENTURE = auto()
    BOSS = auto()


NOMBRE_PROPOSITIONS_NIVEAU = 3
PROBABILITE_STATION_SERVICE = 1 / 30
PROBABILITE_PLANETE_COMMERCIALE = 1 / 30
PROBABILITE_AVENTURE = 1 / 10
NIVEAUX_STATION_GARANTIE = (5, 9)


def est_niveau_boss(niveau: int) -> bool:
    """Niveau 10, puis tous les 10 niveaux (specs.md 2.3) - une seule proposition forcee
    (TypeEtape.BOSS) plutot qu'un tirage, cf. tirer_propositions_niveau ci-dessous."""
    return niveau % 10 == 0


def aleatoire_pour_niveau(graine: int, niveau: int) -> random.Random:
    """Generateur aleatoire deterministe pour un niveau donne d'une partie (specs.md 10.3) :
    memes graine+niveau -> memes propositions tirees, sans avoir a les stocker litteralement dans
    la sauvegarde. Graine textuelle (random.Random n'accepte pas un tuple en seed) plutot qu'une
    combinaison arithmetique, pour eviter tout risque de collision entre graine/niveau."""
    return random.Random(f"{graine}:{niveau}")


def tirer_type_etape(aleatoire: random.Random) -> TypeEtape:
    """1/30 Station service, 1/30 Planete commerciale, 1/10 Aventure, sinon (5/6) Prime
    (specs.md 2.3)."""
    tirage = aleatoire.random()
    if tirage < PROBABILITE_STATION_SERVICE:
        return TypeEtape.STATION_SERVICE
    if tirage < PROBABILITE_STATION_SERVICE + PROBABILITE_PLANETE_COMMERCIALE:
        return TypeEtape.PLANETE_COMMERCIALE
    if tirage < PROBABILITE_STATION_SERVICE + PROBABILITE_PLANETE_COMMERCIALE + PROBABILITE_AVENTURE:
        return TypeEtape.AVENTURE
    return TypeEtape.PRIME


def tirer_propositions_niveau(
    niveau: int, aleatoire: random.Random, quantite: int = NOMBRE_PROPOSITIONS_NIVEAU
) -> list[TypeEtape]:
    """Propositions d'etape pour ce niveau (specs.md 2.3/2.4). Niveau Boss (cf. est_niveau_boss) :
    une seule proposition forcee, TypeEtape.BOSS (decision utilisateur). Sinon, `quantite`
    propositions tirees independamment (donc parfois identiques) parmi Prime/Station service/
    Planete commerciale/Aventure. Aux niveaux 5 et 9, la Station service est garantie parmi les 3 :
    si le tirage independant n'en a pas produit, un emplacement tire au hasard est remplace par
    Station service plutot que d'en ajouter un 4e. Ne pas appeler pour le Niveau 1 (choix de
    module, pas de tirage)."""
    if est_niveau_boss(niveau):
        return [TypeEtape.BOSS]
    propositions = [tirer_type_etape(aleatoire) for _ in range(quantite)]
    if niveau in NIVEAUX_STATION_GARANTIE and TypeEtape.STATION_SERVICE not in propositions:
        propositions[aleatoire.randrange(quantite)] = TypeEtape.STATION_SERVICE
    return propositions


# Quelle Aventure ouvrir quand TypeEtape.AVENTURE est choisi (specs.md 2.5) : les trois specifiees
# sont maintenant implementees.


class TypeAventure(Enum):
    """Aventure concrete ouverte pour une etape TypeEtape.AVENTURE (specs.md 2.5)."""

    TROIS_LUNES = auto()
    ASTEROIDES = auto()
    POLICE = auto()


def tirer_type_aventure(aleatoire: random.Random) -> TypeAventure:
    """Tirage uniforme entre les Aventures implementees (specs.md 2.5) - non deterministe (comme
    les recompenses de fin de combat), pas encore lie a graine/niveau."""
    return aleatoire.choice((TypeAventure.TROIS_LUNES, TypeAventure.ASTEROIDES, TypeAventure.POLICE))


def tirer_carte_deck(deck: list[T], aleatoire: random.Random) -> T:
    """Tire au hasard une carte du deck reel du joueur (Aventure "Police", specs.md 2.5) -
    contrairement a tirer_carte_recompense, qui tire dans un pool de recompense plutot que dans
    le deck possede."""
    return aleatoire.choice(deck)
