"""
Petites fonctions partagees par les ecrans PC (aucun pyglet, aucune regle de jeu) : chemins
d'images, regroupement des cartes identiques pour l'affichage, textes d'une carte.
"""

from src.gameplay.carte_new import CarteNew
from src.gameplay.module_new import ModuleNew
from src.gameplay.partie import RACINE, Partie, modules_de_la_partie
from src.ui import textes_combat

# Image du principal recadree pour une case de la taille des autres modules (accueil, Station,
# Aventures, ecran Vaisseau) ; dans le combat, le principal garde son image entiere (le vaisseau).
# Meme choix que web/bridge.py:IMAGE_CASE_PRINCIPAL.
_IMAGE_CASE_PRINCIPAL = "assets/modules/principal_avant.png"


def chemin_image(relatif: str) -> str:
    """Chemin absolu d'une image citee par config/*_new.json ("assets/...")."""
    return str(RACINE / relatif)


def image_case_module(module: ModuleNew) -> str:
    """Image d'un module dans une case hors combat (chemin absolu)."""
    return chemin_image(_IMAGE_CASE_PRINCIPAL if module.principal else module.image)


def noms_modules(partie: Partie) -> dict[str, str]:
    """Exemplaire de module ("M2") -> nom affiche, pour dire a quel module une carte appartient."""
    return {module.exemplaire: module.nom for module in modules_de_la_partie(partie)}


def regrouper_cartes(cartes: list[CarteNew]) -> list[tuple[CarteNew, int]]:
    """Regroupe les exemplaires identiques (meme carte, meme module) : (carte, quantite), dans
    l'ordre de premiere apparition. Affichage seulement (meme regroupement que le web)."""
    groupes: dict[tuple[str, str | None], list[CarteNew]] = {}
    for carte in cartes:
        groupes.setdefault((carte.id, carte.exemplaire_module), []).append(carte)
    return [(exemplaires[0], len(exemplaires)) for exemplaires in groupes.values()]


def texte_carte(carte: CarteNew, noms: dict[str, str] | None = None) -> str:
    """Description d'une carte (valeurs actuelles, fournie par le gameplay) suivie de ses details
    sur une ligne : munitions, lancements, Persistante, module."""
    nom_module = (noms or {}).get(carte.exemplaire_module)
    details = textes_combat.lignes_details_carte(carte, nom_module)
    description = carte.description_affichee()
    return f"{description}\n{' · '.join(details)}" if details else description
