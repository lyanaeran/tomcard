"""
Logique du parcours (run), hors combat (specs.md paragraphe 2/2.3/2.1/6). Pour l'instant : le
tirage des candidats du Niveau 1 (choix de module) et celui des recompenses de fin de combat.
"""

import random

from src.gameplay.carte import Carte, RareteCarte
from src.gameplay.config_poc import ID_MODULE_PRINCIPAL
from src.gameplay.donnees import SpecModule

NOMBRE_CANDIDATS_MODULE = 3


def modules_equipables(specs_modules: list[SpecModule]) -> list[SpecModule]:
    """Modules pouvant etre proposes en choix : tous sauf le module principal, deja acquis
    d'office en debut de run (specs.md paragraphe 5)."""
    return [spec for spec in specs_modules if spec.id != ID_MODULE_PRINCIPAL]


def tirer_candidats_module(
    pool: list[SpecModule], aleatoire: random.Random, quantite: int = NOMBRE_CANDIDATS_MODULE
) -> list[SpecModule]:
    """Tire `quantite` modules differents au hasard dans la pool (specs.md paragraphe 2.3,
    Niveau 1) : uniforme pour l'instant, puisqu'aucun module n'est encore possede a ce stade du
    run (donc pas de ponderation par doublons a appliquer - cf. specs.md 2.3 "points encore
    ouverts" pour les tirages ulterieurs, apres un Boss, une fois des modules deja possedes)."""
    return aleatoire.sample(pool, quantite)


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


def tirer_carte_recompense(pool: list[Carte], aleatoire: random.Random) -> Carte | None:
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


def pool_module(spec: SpecModule, cartes: dict[str, Carte]) -> list[Carte]:
    """Cartes jouables et non-Base de ce module (specs.md 2.1/6)."""
    return [cartes[id_carte] for id_carte in spec.cartes if id_carte in cartes and cartes[id_carte].rarete != RareteCarte.BASE]


def pool_toutes_cartes(cartes: dict[str, Carte]) -> list[Carte]:
    """Toutes les cartes jouables non-Base, tous modules confondus (module principal, specs.md 6)."""
    return [carte for carte in cartes.values() if carte.rarete != RareteCarte.BASE]


def tirer_candidats_recompense(
    specs_utilisees: list[SpecModule], cartes: dict[str, Carte], aleatoire: random.Random
) -> list[tuple[SpecModule, Carte | None]]:
    """Un candidat de recompense par module utilise dans ce combat (specs.md 2.1/6), au maximum
    5 (base + 4 equipes, cf. specs.md 5) : le module principal (le premier de la liste, meme
    ordre que creer_vaisseau) pioche dans le pool entier de cartes jouables non-Base, chaque
    module equipe pioche dans son propre pool. Candidat a None si le pool de ce module est vide
    (aucune carte jouable non-Base actuellement associee)."""
    spec_principal, *specs_equipes = specs_utilisees
    resultats = [(spec_principal, tirer_carte_recompense(pool_toutes_cartes(cartes), aleatoire))]
    for spec in specs_equipes:
        resultats.append((spec, tirer_carte_recompense(pool_module(spec, cartes), aleatoire)))
    return resultats
