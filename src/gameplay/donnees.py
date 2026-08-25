"""
Chargement des fichiers de configuration (config/*.json).

Format de chaque fichier (contenu declaratif du jeu, cf. specs.md paragraphe 10.2) :

- modules.json : un module par entree - id (MOD_N), nom, image (chemin sous assets/modules/),
  points_de_vie, description (type de carte debloque, sans reveler les cartes - utilisee par
  l'ecran de choix de module du parcours, specs.md 2.3), cartes (liste d'ids CRT_N jouables).
- ennemis.json : un ennemi par entree - id (ENM_N), nom, image (assets/ennemis/), points_de_vie,
  action : chaine "TYPE,valeur,cible" (ex. "ATK,8,AUTO") - seul TYPE=ATK (attaque) est interprete
  ici pour l'instant, les autres types ignores ; cible vaut toujours AUTO (ciblage automatique,
  cf. ciblage.py), prevu pour accueillir d'autres modes plus tard si besoin.
- cartes.json : une carte par entree - id (CRT_N), nom, image (assets/cartes/), cout (electricite),
  rarete (Base/Commune/Rare/Legendaire, cf. RareteCarte), munition (nombre de munitions, absent/
  null = illimitees, cf. carte.py), effet (absent = carte non jouable, ignoree par charger_cartes) :
  objet {type, cible, valeur, action?, duree?} - type/cible/action reprennent les valeurs de
  TypeCarte/CibleCarte/ActionCarte (cf. carte.py pour le detail de chaque valeur), duree est le
  nombre de tours d'un effet Debuff/Buff (absente/null pour un Buff persistant).
"""

import json
from dataclasses import dataclass
from pathlib import Path

from src.gameplay.carte import ActionCarte, Carte, CibleCarte, RareteCarte, TypeCarte

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_CONFIG = RACINE / "config"


@dataclass(frozen=True)
class SpecModule:
    """Description d'un module, telle que lue dans config/modules.json."""

    id: str
    nom: str
    image: str
    points_de_vie: int
    description: str
    cartes: tuple[str, ...]


@dataclass(frozen=True)
class SpecEnnemi:
    """Description d'un ennemi, telle que lue dans config/ennemis.json.

    Seule l'action ATK (attaque) est supportee pour l'instant (cf. module docstring ci-dessus).
    """

    id: str
    nom: str
    image: str
    points_de_vie: int
    degats_attaque: int


def _chemin_image(chemin_relatif: str) -> str:
    """Renvoie le chemin absolu d'une image reference dans un fichier de config."""
    return str(RACINE / chemin_relatif)


# Module principal (config/modules.json) : son image complete (spec.image) sert de fond au
# vaisseau entier en combat (src/ui/fenetre.py) et n'est donc pas adaptee a une case de la taille
# des autres modules (Station service, accueil joueur, specs.md 2.2/10.3) - decision utilisateur.
_ID_MODULE_PRINCIPAL = "MOD_1"
_IMAGE_CASE_MODULE_PRINCIPAL = "assets/modules/principal_avant.png"


def image_case_module(spec: SpecModule) -> str:
    """Chemin de l'image a utiliser pour ce module dans une case de la taille des autres modules
    (Station service, accueil joueur) : un recadrage dedie sur l'avant du vaisseau pour le module
    principal, l'image normale (spec.image) pour tous les autres."""
    if spec.id == _ID_MODULE_PRINCIPAL:
        return _chemin_image(_IMAGE_CASE_MODULE_PRINCIPAL)
    return spec.image


def charger_cartes() -> dict[str, Carte]:
    """Charge config/cartes.json. Renvoie un dict id de carte -> Carte.

    Les entrees sans bloc "effet" sont des cartes de design pas encore jouables
    (mecanique non supportee par le moteur actuel, ex : Debuff, Buff, Outils,
    cible figee, effet a duree/munitions limitees - voir specs.md 9.1) : elles
    restent presentes dans cartes.json pour reference mais sont ignorees ici.
    """
    donnees = json.loads((DOSSIER_CONFIG / "cartes.json").read_text())
    cartes = {}
    for entree in donnees["cartes"]:
        effet = entree.get("effet")
        if effet is None:
            continue
        rarete = RareteCarte[entree["rarete"].upper()] if "rarete" in entree else RareteCarte.BASE
        action = ActionCarte[effet["action"]] if "action" in effet else None
        cartes[entree["id"]] = Carte(
            nom=entree["nom"],
            image=_chemin_image(entree["image"]),
            type=TypeCarte[effet["type"]],
            cible=CibleCarte[effet["cible"]],
            cout=entree["cout"],
            valeur=effet["valeur"],
            rarete=rarete,
            duree=effet.get("duree"),
            munitions_max=entree.get("munition"),
            action=action,
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
            description=entree["description"],
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
