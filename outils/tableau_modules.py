"""
Genere config/module_new.md, tableau lisible des modules, a partir de config/module_new.json
(seule source de verite). Ne jamais modifier le tableau a la main : relancer ce script apres
chaque modification du JSON (tests/test_tableau_modules.py echoue sinon).

    python -m outils.tableau_modules
"""

import json
from pathlib import Path

from src.gameplay.carte_new import charger_cartes_new

RACINE = Path(__file__).resolve().parents[1]
FICHIER_JSON = RACINE / "config" / "module_new.json"
FICHIER_TABLEAU = RACINE / "config" / "module_new.md"

ENTETE = """# Modules (refonte) — tableau généré

> **Fichier généré automatiquement à partir de `config/module_new.json`, ne pas le modifier à la
> main** : toute modification se fait dans le JSON, puis `python -m outils.tableau_modules`
> régénère ce tableau (un test échoue tant qu'il n'est pas à jour).

"""

COLONNES = ["Id", "Nom", "Principal", "PV max", "Jouable", "Refonte", "Description", "Cartes"]


def _cellule(texte: str) -> str:
    """Texte sur une ligne, sans casser le tableau Markdown."""
    return str(texte).replace("|", "\\|").replace("\n", " ")


def _oui_non(valeur: bool) -> str:
    return "Oui" if valeur else "Non"


def tableau_markdown(fichier_json: Path = FICHIER_JSON) -> str:
    """Contenu complet de config/module_new.md pour ce fichier JSON."""
    entrees = json.loads(fichier_json.read_text(encoding="utf-8"))["modules"]
    noms_cartes = {id_carte: carte.nom for id_carte, carte in charger_cartes_new().items()}
    lignes = ["| " + " | ".join(COLONNES) + " |", "|" + "|".join("---" for _ in COLONNES) + "|"]
    for entree in entrees:
        cartes = "<br>".join(f"{id_carte} {noms_cartes.get(id_carte, '(inconnue)')}" for id_carte in entree["cartes"])
        valeurs = [
            entree["id"], entree["nom"], _oui_non(entree.get("principal", False)), str(entree["pv_max"]),
            _oui_non(entree.get("jouable", True)), _oui_non(entree.get("refonte", False)), entree["description"], cartes,
        ]
        lignes.append("| " + " | ".join(_cellule(valeur) for valeur in valeurs) + " |")
    return ENTETE + f"{len(entrees)} modules.\n\n" + "\n".join(lignes) + "\n"


def main() -> None:
    FICHIER_TABLEAU.write_text(tableau_markdown(), encoding="utf-8")
    print(f"{FICHIER_TABLEAU} regenere")


if __name__ == "__main__":
    main()
