"""
Chargement des fichiers de configuration (config/*.json).

Format de chaque fichier (contenu declaratif du jeu, cf. specs.md paragraphe 10.2) :

- modules.json : un module par entree - id (MOD_N), nom, image (chemin sous assets/modules/),
  points_de_vie, description (accroche narrative, une phrase - affichee a l'ecran de choix de
  module du parcours, specs.md 2.3), description_gameplay (indice sur le type de carte debloque,
  sans reveler les cartes - affiche en plus de description dans l'infobulle de l'ecran Vaisseau),
  cartes (liste d'ids CRT_N jouables - vide pour un module dont les cartes ne sont pas encore
  concues : cf. modules_equipables/specs_equipables qui l'excluent alors du tirage, specs.md 5).
- ennemis.json : un ennemi par entree - id (ENM_N), nom, image (assets/ennemis/), points_de_vie,
  taille (S/M/L, cf. specs.md 3.2 - purement informatif pour l'instant, seule S est utilisee),
  placement (absent/null, ou "PROTECTEUR_AVANT"/"PROTEGE_ARRIERE" - preference de position en
  flotte, specs.md 13), actions : liste d'objets {type, cible, valeur, frequence?, tour_depart?,
  repetitions?, action_buff?, duree_buff?} - type/cible reprennent TypeActionEnnemi/
  CibleActionEnnemi (cf. ennemi.py), action_buff un ActionCarte (cf. carte.py, uniquement pour
  type=POSE_BUFF). frequence/tour_depart/repetitions par defaut a 1, duree_buff a null
  (persistant) - cf. ennemi.py:ActionEnnemi pour le detail de chaque champ (specs.md 13).
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
from src.gameplay.ennemi import ActionEnnemi, CibleActionEnnemi, TypeActionEnnemi

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
    description_gameplay: str
    cartes: tuple[str, ...]


@dataclass(frozen=True)
class SpecEnnemi:
    """Description d'un ennemi, telle que lue dans config/ennemis.json (specs.md 13)."""

    id: str
    nom: str
    image: str
    points_de_vie: int
    taille: str
    actions: tuple[ActionEnnemi, ...]
    placement: str | None


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
            description_gameplay=entree["description_gameplay"],
            cartes=tuple(entree["cartes"]),
        )
        for entree in donnees["modules"]
    ]


def _action_ennemi_depuis_json(action: dict) -> ActionEnnemi:
    return ActionEnnemi(
        type=TypeActionEnnemi[action["type"]],
        cible=CibleActionEnnemi[action["cible"]],
        valeur=action["valeur"],
        frequence=action.get("frequence", 1),
        tour_depart=action.get("tour_depart", 1),
        repetitions=action.get("repetitions", 1),
        action_buff=ActionCarte[action["action_buff"]] if "action_buff" in action else None,
        duree_buff=action.get("duree_buff"),
    )


def charger_ennemis() -> list[SpecEnnemi]:
    """Charge config/ennemis.json (specs.md 13)."""
    donnees = json.loads((DOSSIER_CONFIG / "ennemis.json").read_text())
    specs = []
    for entree in donnees["ennemis"]:
        specs.append(
            SpecEnnemi(
                id=entree["id"],
                nom=entree["nom"],
                image=_chemin_image(entree["image"]),
                points_de_vie=entree["points_de_vie"],
                taille=entree.get("taille", "S"),
                placement=entree.get("placement"),
                actions=tuple(_action_ennemi_depuis_json(action) for action in entree["actions"]),
            )
        )
    return specs
