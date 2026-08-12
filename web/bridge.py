"""
Pont entre le JS de la page web et le moteur de combat Python reel (src/gameplay/),
execute tel quel dans le navigateur via Pyodide. Aucune modification du gameplay :
ce fichier ne fait que traduire son etat en JSON et router les actions du joueur.

POC experimental (branche web-ui-poc) : layout simplifie, pas de popups/infobulles,
juste de quoi valider que le vrai moteur de combat est jouable au doigt sur iPhone.
"""

import json
import random
import sys

sys.path.insert(0, "/repo")

from src.gameplay.carte import CIBLES_SANS_CLIC, CibleCarte
from src.gameplay.config_poc import creer_combat_poc
from src.gameplay.position import Colonne, Position, Rangee

RACINE_FS = "/repo/"

IDS_MODULES = {
    "AV_G": Position(Colonne.AVANT, Rangee.GAUCHE),
    "AV_D": Position(Colonne.AVANT, Rangee.DROITE),
    "AR_G": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "AR_D": Position(Colonne.ARRIERE, Rangee.DROITE),
}
IDS_ENNEMIS = {
    "AV_G": Position(Colonne.AVANT, Rangee.GAUCHE),
    "AV_M": Position(Colonne.AVANT, Rangee.MID),
    "AV_D": Position(Colonne.AVANT, Rangee.DROITE),
    "AR_G": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "AR_M": Position(Colonne.ARRIERE, Rangee.MID),
    "AR_D": Position(Colonne.ARRIERE, Rangee.DROITE),
}

combat = None


def _chemin_web(chemin_fs: str) -> str:
    """Convertit un chemin absolu de la FS Pyodide (/repo/...) en URL relative de la page."""
    return chemin_fs[len(RACINE_FS):] if chemin_fs and chemin_fs.startswith(RACINE_FS) else chemin_fs


def _module_json(module, id_case: str):
    if module is None:
        return None
    return {
        "id": id_case,
        "nom": module.nom,
        "pv": module.pv,
        "pv_max": module.pv_max,
        "bouclier": module.bouclier,
        "detruit": module.est_detruit(),
        "image": _chemin_web(module.image),
    }


def _ennemi_json(ennemi, id_case: str):
    if ennemi is None:
        return None
    return {
        "id": id_case,
        "nom": ennemi.nom,
        "pv": ennemi.pv,
        "pv_max": ennemi.pv_max,
        "detruit": ennemi.est_detruit(),
        "image": _chemin_web(ennemi.image),
        "degats_attaque": ennemi.degats_attaque,
    }


def _carte_json(carte, index: int):
    return {
        "index": index,
        "nom": carte.nom,
        "cout": carte.cout,
        "valeur": carte.valeur,
        "type": carte.type.name,
        "cible": carte.cible.name,
        "sans_clic": carte.cible in CIBLES_SANS_CLIC,
        "image": _chemin_web(carte.image),
    }


def etat() -> str:
    """Serialise l'etat courant du combat en JSON pour le rendu JS."""
    vaisseau = combat.joueur.vaisseau
    flotte = combat.flotte
    modules_equipes = vaisseau.modules_equipes()

    vaisseau_json = {
        "base": _module_json(vaisseau.base, "base"),
        "modules": [_module_json(modules_equipes.get(pos), id_case) for id_case, pos in IDS_MODULES.items()],
    }
    ennemis_json = [_ennemi_json(flotte.positions().get(pos), id_case) for id_case, pos in IDS_ENNEMIS.items()]
    main_json = [_carte_json(carte, i) for i, carte in enumerate(combat.joueur.deck.main)]

    return json.dumps(
        {
            "etat": combat.etat.name,
            "electricite": combat.joueur.electricite,
            "electricite_max": combat.joueur.electricite_par_tour,
            "vaisseau": vaisseau_json,
            "ennemis": ennemis_json,
            "main": main_json,
            "pioche": len(combat.joueur.deck.pioche),
            "defausse": len(combat.joueur.deck.defausse),
        }
    )


def nouveau_combat(graine) -> str:
    """Demarre un nouveau combat aleatoire (graine optionnelle pour reproduire un combat)."""
    global combat
    aleatoire = random.Random(int(graine)) if graine is not None else random.Random()
    combat = creer_combat_poc(generateur_aleatoire=aleatoire)
    return etat()


def _resoudre_cible(carte, id_cible):
    if carte.cible in CIBLES_SANS_CLIC:
        return None
    if carte.cible == CibleCarte.ALLIE_UNIQUE:
        if id_cible == "base":
            return combat.joueur.vaisseau.base
        position = IDS_MODULES.get(id_cible)
        return combat.joueur.vaisseau.modules_equipes().get(position) if position else None
    position = IDS_ENNEMIS.get(id_cible)
    return combat.flotte.positions().get(position) if position else None


def jouer_carte(index_carte: int, id_cible) -> str:
    """Joue la carte en main a cet index sur la cible designee par son id (ou None)."""
    carte = combat.joueur.deck.main[index_carte]
    cible = _resoudre_cible(carte, id_cible)
    combat.jouer_carte(carte, cible)
    return etat()


def finir_tour() -> str:
    combat.finir_tour_joueur()
    return etat()
