"""
Enchainement des ecrans d'une partie (specs.md 2.4) : seule source de verite de "quel ecran
vient ensuite" et des regles appliquees a chaque transition (equipement du module, avancee de
niveau, Argent et PV apres un combat, fin de partie...).

Le PC (main.py), le web (src/web/bridge.py + src/web/app.js) et la simulation (outils/simulation/) ne font
qu'appeler ces fonctions et afficher l'Ecran renvoye. Aucune I/O ici : la sauvegarde de la partie
apres chaque transition reste a la charge de l'appelant (fichier cote PC, localStorage cote web).
Tout tirage passe par un random.Random injecte (CLAUDE.md).
"""

import random
from enum import Enum, auto

from src.gameplay.carte_new import CarteNew, charger_cartes_new
from src.gameplay.combat_new import CombatNew, EtatCombatNew
from src.gameplay.module_new import ModuleNew, charger_modules_new
from src.gameplay.parcours import (
    TypeAventure,
    TypeEtape,
    aleatoire_pour_niveau,
    est_niveau_boss,
    modules_equipables,
    tirer_candidats_carte_module,
    tirer_candidats_module,
    tirer_candidats_recompense,
    tirer_propositions_niveau,
    tirer_type_aventure,
)
from src.gameplay.partie import (
    CartePossedee,
    Partie,
    ajouter_carte,
    avancer_niveau,
    equiper_module,
    gagner_argent_combat,
    marquer_terminee,
    modules_de_la_partie,
    reporter_combat,
)


class Ecran(Enum):
    """Ecran a afficher ensuite (specs.md 2.4)."""

    ACCUEIL = auto()
    CHOIX_MODULE = auto()
    CHOIX_NIVEAU = auto()
    COMBAT = auto()
    STATION_SERVICE = auto()
    AVENTURE_TROIS_LUNES = auto()
    AVENTURE_ASTEROIDES = auto()
    AVENTURE_POLICE = auto()
    PLANETE_COMMERCIALE = auto()
    # Choix de la carte de recompense d'un combat gagne (reprise d'une partie quittee sur cet ecran)
    RECOMPENSE = auto()
    VICTOIRE_FINALE = auto()


ECRAN_PAR_AVENTURE = {
    TypeAventure.TROIS_LUNES: Ecran.AVENTURE_TROIS_LUNES,
    TypeAventure.ASTEROIDES: Ecran.AVENTURE_ASTEROIDES,
    TypeAventure.POLICE: Ecran.AVENTURE_POLICE,
}


def ecran_de_reprise(partie: Partie) -> Ecran:
    """Ecran ou reprendre une partie en cours ("Continuer") : le Niveau 1 sans 2e module equipe
    reprend au choix de module ; un combat gagne dont la recompense n'a pas ete choisie reprend a
    ce choix (jamais au niveau deja gagne) ; sinon au choix du niveau courant (propositions
    retirees de facon deterministe, cf. aleatoire_pour_niveau)."""
    if partie.recompense is not None:
        return Ecran.RECOMPENSE
    if partie.niveau == 1 and partie.vaisseau["avant_gauche"] is None:
        return Ecran.CHOIX_MODULE
    return Ecran.CHOIX_NIVEAU


def candidats_choix_module(partie: Partie) -> list[ModuleNew]:
    """Modeles de modules proposes au Niveau 1 (specs.md 2.3), tires a partir de la graine de la
    partie."""
    return tirer_candidats_module(modules_equipables(charger_modules_new().values()), random.Random(partie.graine))


def choisir_module(partie: Partie, modele: ModuleNew, aleatoire: random.Random) -> list[CarteNew]:
    """Equipe un exemplaire du module choisi et renvoie les cartes proposees pour lui (ecran de
    choix de carte, enchaine directement apres le choix du module), deja rattachees au nouvel
    exemplaire. Liste vide si son pool n'a rien a proposer : appeler alors directement
    resoudre_carte_module avec None, sans afficher l'ecran."""
    module = equiper_module(partie, modele)
    candidats = tirer_candidats_carte_module(module, charger_cartes_new(), aleatoire)
    return [carte.copie(exemplaire_module=module.exemplaire) for carte in candidats]


def _ajouter(partie: Partie, carte: CarteNew | None) -> None:
    """Ajoute au deck une carte proposee (deja rattachee a son module), rien pour None."""
    if carte is not None:
        ajouter_carte(partie, carte.id, carte.exemplaire_module)


def resoudre_carte_module(partie: Partie, carte: CarteNew | None) -> Ecran:
    """Ajoute la carte choisie parmi celles de choisir_module (None = Passer) et passe au niveau
    suivant."""
    _ajouter(partie, carte)
    avancer_niveau(partie)
    return Ecran.CHOIX_NIVEAU


def propositions_niveau(partie: Partie) -> list[TypeEtape]:
    """Etapes proposees au niveau courant, deterministes pour une graine et un niveau donnes."""
    return tirer_propositions_niveau(partie.niveau, aleatoire_pour_niveau(partie.graine, partie.niveau))


def ecran_pour_etape(type_etape: TypeEtape, aleatoire: random.Random) -> Ecran:
    """Ecran ouvert par l'etape choisie ; pour une Aventure, tire laquelle (specs.md 2.5)."""
    if type_etape in (TypeEtape.PRIME, TypeEtape.BOSS):
        return Ecran.COMBAT
    if type_etape == TypeEtape.STATION_SERVICE:
        return Ecran.STATION_SERVICE
    if type_etape == TypeEtape.AVENTURE:
        return ECRAN_PAR_AVENTURE[tirer_type_aventure(aleatoire)]
    return Ecran.PLANETE_COMMERCIALE


def terminer_etape(partie: Partie) -> Ecran:
    """Fin d'une etape hors combat (Station service, Aventure sans combat, Planete commerciale) :
    passe au niveau suivant."""
    avancer_niveau(partie)
    return Ecran.CHOIX_NIVEAU


def conclure_combat(
    partie: Partie, combat: CombatNew, aleatoire: random.Random
) -> list[tuple[ModuleNew, CarteNew | None]]:
    """A appeler une seule fois, des que le combat se termine : reporte les PV du principal sur la
    partie (reporter_combat). Defaite : la partie est terminee tout de suite. Victoire : ajoute
    l'Argent gagne (specs.md 2.1), renvoie les candidats de recompense (specs.md 6) : un par module
    equipe, la carte deja rattachee a ce module, et les note dans partie.recompense. La partie
    peut etre sauvegardee telle quelle : la reprendre ne rejoue pas le combat (ecran_de_reprise)."""
    if combat.en_cours:
        raise ValueError("Le combat n'est pas termine")
    reporter_combat(partie, combat)
    if combat.etat != EtatCombatNew.VICTOIRE:
        marquer_terminee(partie)
        return []
    gagner_argent_combat(partie, combat)
    candidats = tirer_candidats_recompense(modules_de_la_partie(partie), charger_cartes_new(), aleatoire)
    partie.recompense = [
        CartePossedee(id=carte.id, module=carte.exemplaire_module) for _module, carte in candidats if carte is not None
    ]
    return candidats


def recompense_en_attente(partie: Partie) -> list[tuple[ModuleNew, CarteNew]]:
    """Candidats de recompense notes par conclure_combat et pas encore resolus (reprise sur
    l'ecran de recompense), sous la meme forme que conclure_combat."""
    cartes = charger_cartes_new()
    modules = {module.exemplaire: module for module in modules_de_la_partie(partie)}
    return [
        (modules[possedee.module], cartes[possedee.id].copie(exemplaire_module=possedee.module))
        for possedee in partie.recompense or []
    ]


def resoudre_fin_combat(partie: Partie, victoire: bool, carte: CarteNew | None) -> Ecran:
    """Ecran de fin de combat ferme : une defaite termine la partie ; une victoire ajoute la carte
    choisie parmi les candidats de conclure_combat (None = aucune ou Passer), puis mene a la
    victoire finale apres le Boss (le run s'arrete au Niveau 10, specs.md 2 : la partie est
    terminee des maintenant, pour ne pas pouvoir rejouer le Boss) ou au niveau suivant."""
    if not victoire:
        marquer_terminee(partie)
        return Ecran.ACCUEIL
    if carte is not None and partie.recompense is not None and (
        CartePossedee(id=carte.id, module=carte.exemplaire_module) not in partie.recompense
    ):
        raise ValueError(f"Carte {carte.id} : pas parmi les recompenses proposees")
    _ajouter(partie, carte)
    partie.recompense = None
    if est_niveau_boss(partie.niveau):
        marquer_terminee(partie)
        return Ecran.VICTOIRE_FINALE
    avancer_niveau(partie)
    return Ecran.CHOIX_NIVEAU


def terminer_victoire_finale(partie: Partie) -> Ecran:
    """Ecran de victoire finale ferme : la partie est terminee."""
    marquer_terminee(partie)
    return Ecran.ACCUEIL
