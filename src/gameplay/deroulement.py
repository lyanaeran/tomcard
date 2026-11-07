"""
Enchainement des ecrans d'une partie (specs.md 2.4) : seule source de verite de "quel ecran
vient ensuite" et des regles appliquees a chaque transition (equipement du module, avancee de
niveau, Argent et PV apres un combat, fin de partie...).

Le PC (main.py), le web (web/bridge.py + web/app.js) et la simulation (outils/simulation/) ne font
qu'appeler ces fonctions et afficher l'Ecran renvoye. Aucune I/O ici : la sauvegarde de la partie
apres chaque transition reste a la charge de l'appelant (fichier cote PC, localStorage cote web).
Tout tirage passe par un random.Random injecte (CLAUDE.md).
"""

import random
from enum import Enum, auto

from src.gameplay.carte import Carte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.donnees import SpecModule, charger_cartes, charger_modules
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
    Partie,
    ajouter_carte,
    avancer_niveau,
    equiper_module,
    gagner_argent_combat,
    marquer_terminee,
    specs_utilisees_partie,
    synchroniser_vaisseau_depuis_combat,
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
    VICTOIRE_FINALE = auto()


ECRAN_PAR_AVENTURE = {
    TypeAventure.TROIS_LUNES: Ecran.AVENTURE_TROIS_LUNES,
    TypeAventure.ASTEROIDES: Ecran.AVENTURE_ASTEROIDES,
    TypeAventure.POLICE: Ecran.AVENTURE_POLICE,
}


def ecran_de_reprise(partie: Partie) -> Ecran:
    """Ecran ou reprendre une partie en cours ("Continuer") : le Niveau 1 sans 2e module equipe
    reprend au choix de module, sinon au choix du niveau courant (propositions retirees de facon
    deterministe, cf. aleatoire_pour_niveau)."""
    if partie.niveau == 1 and partie.vaisseau["avant_gauche"] is None:
        return Ecran.CHOIX_MODULE
    return Ecran.CHOIX_NIVEAU


def candidats_choix_module(partie: Partie) -> list[SpecModule]:
    """Modules proposes au Niveau 1 (specs.md 2.3), tires a partir de la graine de la partie."""
    return tirer_candidats_module(modules_equipables(charger_modules()), random.Random(partie.graine))


def choisir_module(partie: Partie, spec: SpecModule, aleatoire: random.Random) -> list[Carte]:
    """Equipe le module choisi et renvoie les cartes proposees pour lui (ecran de choix de carte,
    enchaine directement apres le choix du module).
    Liste vide si son pool n'a rien a proposer : appeler alors directement resoudre_carte_module
    avec None, sans afficher l'ecran."""
    equiper_module(partie, spec)
    return tirer_candidats_carte_module(spec, charger_cartes(), aleatoire)


def resoudre_carte_module(partie: Partie, id_carte: str | None) -> Ecran:
    """Ajoute la carte choisie (None = Passer) et passe au niveau suivant."""
    if id_carte is not None:
        ajouter_carte(partie, id_carte)
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
    partie: Partie, combat: Combat, aleatoire: random.Random
) -> list[tuple[SpecModule, Carte | None]]:
    """A appeler une seule fois, des que le combat se termine : reporte les PV du combat sur la
    partie (specs.md 2.2/3.4), et en cas de victoire ajoute l'Argent gagne (specs.md 2.1) et
    renvoie les candidats de recompense (specs.md 6, vide en cas de defaite)."""
    synchroniser_vaisseau_depuis_combat(partie, combat.joueur.vaisseau)
    if combat.etat != EtatCombat.VICTOIRE:
        return []
    gagner_argent_combat(partie, combat)
    specs_par_id = {spec.id: spec for spec in charger_modules()}
    return tirer_candidats_recompense(specs_utilisees_partie(partie, specs_par_id), charger_cartes(), aleatoire)


def resoudre_fin_combat(partie: Partie, victoire: bool, id_carte: str | None) -> Ecran:
    """Ecran de fin de combat ferme : une defaite termine la partie ; une victoire ajoute la carte
    choisie (None = aucune ou Passer), puis mene a la victoire finale apres le Boss (le run
    s'arrete au Niveau 10, specs.md 2) ou au niveau suivant."""
    if not victoire:
        marquer_terminee(partie)
        return Ecran.ACCUEIL
    if id_carte is not None:
        ajouter_carte(partie, id_carte)
    if est_niveau_boss(partie.niveau):
        return Ecran.VICTOIRE_FINALE
    avancer_niveau(partie)
    return Ecran.CHOIX_NIVEAU


def terminer_victoire_finale(partie: Partie) -> Ecran:
    """Ecran de victoire finale ferme : la partie est terminee."""
    marquer_terminee(partie)
    return Ecran.ACCUEIL
