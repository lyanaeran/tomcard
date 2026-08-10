"""
Chargement des fichiers de configuration (config/*.json, cf. poc.md).
"""

import json
from dataclasses import dataclass
from pathlib import Path

from src.gameplay.carte import Carte, CibleCarte, TypeCarte

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_CONFIG = RACINE / "config"


@dataclass(frozen=True)
class SpecModule:
    """Description d'un module, telle que lue dans config/modules.json."""

    id: str
    nom: str
    image: str
    points_de_vie: int
    cartes: tuple[str, ...]


@dataclass(frozen=True)
class SpecEnnemi:
    """Description d'un ennemi, telle que lue dans config/ennemis.json.

    Seule l'action ATK (attaque) est supportee pour l'instant, cf. poc.md.
    """

    id: str
    nom: str
    image: str
    points_de_vie: int
    degats_attaque: int


def _chemin_image(chemin_relatif: str) -> str:
    """Renvoie le chemin absolu d'une image reference dans un fichier de config."""
    return str(RACINE / chemin_relatif)


def charger_cartes() -> dict[str, Carte]:
    """Charge config/cartes.json. Renvoie un dict id de carte -> Carte."""
    donnees = json.loads((DOSSIER_CONFIG / "cartes.json").read_text())
    cartes = {}
    for entree in donnees["cartes"]:
        effet = entree["effet"]
        cartes[entree["id"]] = Carte(
            nom=entree["nom"],
            image=_chemin_image(entree["image"]),
            type=TypeCarte[effet["type"]],
            cible=CibleCarte[effet["cible"]],
            cout=entree["cout"],
            valeur=effet["valeur"],
        )
    return cartes


def charger_modules() -> list[SpecModule]:
    """Charge config/modules.json."""
    donnees = json.loads((DOSSIER_CONFIG / "modules.json").read_text())
    return [
        SpecModule(
            id=entree["id"],
            nom=entree["nom"],
            image=_chemin_image(entree["image"]),
            points_de_vie=entree["points_de_vie"],
            cartes=tuple(entree["cartes"]),
        )
        for entree in donnees["modules"]
    ]


def charger_ennemis() -> list[SpecEnnemi]:
    """Charge config/ennemis.json. Ignore les actions autres que ATK pour l'instant."""
    donnees = json.loads((DOSSIER_CONFIG / "ennemis.json").read_text())
    specs = []
    for entree in donnees["ennemis"]:
        type_action, valeur, _cible = entree["action"].split(",")
        if type_action != "ATK":
            continue
        specs.append(
            SpecEnnemi(
                id=entree["id"],
                nom=entree["nom"],
                image=_chemin_image(entree["image"]),
                points_de_vie=entree["points_de_vie"],
                degats_attaque=int(valeur),
            )
        )
    return specs
