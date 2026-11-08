"""
Genere config/carte_new.md, tableau lisible des cartes, a partir de config/carte_new.json (seule
source de verite). Ne jamais modifier le tableau a la main : relancer ce script apres chaque
modification du JSON (tests/test_tableau_cartes.py echoue sinon).

    python -m outils.tableau_cartes
"""

import json
from pathlib import Path

from src.gameplay.carte_new import CarteNew, charger_cartes_new

RACINE = Path(__file__).resolve().parents[1]
FICHIER_JSON = RACINE / "config" / "carte_new.json"
FICHIER_TABLEAU = RACINE / "config" / "carte_new.md"

ENTETE = """# Cartes (refonte) — tableau généré

> **Fichier généré automatiquement à partir de `config/carte_new.json`, ne pas le modifier à la
> main** : toute modification se fait dans le JSON, puis `python -m outils.tableau_cartes`
> régénère ce tableau (un test échoue tant qu'il n'est pas à jour).

"""

COLONNES = [
    "Id", "Nom", "Rareté", "Catégorie", "Cible", "Coût", "Munitions", "Lancements", "Persistante",
    "Jouable", "Refonte", "Description affichée", "Valeurs", "Effets",
]


def _cellule(texte: str) -> str:
    """Texte sur une ligne, sans casser le tableau Markdown."""
    return str(texte).replace("|", "\\|").replace("\n", " ")


def _compact(valeur) -> str:
    return json.dumps(valeur, ensure_ascii=False, separators=(", ", ": "))


def _oui_non(valeur: bool) -> str:
    return "Oui" if valeur else "Non"


def _ligne(entree: dict, carte: CarteNew) -> list[str]:
    return [
        entree["id"],
        entree["nom"],
        entree["rarete"],
        entree["categorie"],
        entree["cible"],
        str(entree["cout"]),
        "Illimitées" if entree.get("munition") is None else str(entree["munition"]),
        str(entree.get("lancements", 1)),
        _oui_non(entree.get("persistante", False)),
        _oui_non(entree.get("jouable", True)),
        _oui_non(entree.get("refonte", False)),
        carte.description_affichee(),
        f"`{_compact(entree.get('valeurs', {}))}`",
        "<br>".join(f"`{_compact(effet)}`" for effet in entree["effets"]),
    ]


def tableau_markdown(fichier_json: Path = FICHIER_JSON) -> str:
    """Contenu complet de config/carte_new.md pour ce fichier JSON."""
    entrees = json.loads(fichier_json.read_text(encoding="utf-8"))["cartes"]
    cartes = charger_cartes_new(fichier_json)
    lignes = ["| " + " | ".join(COLONNES) + " |", "|" + "|".join("---" for _ in COLONNES) + "|"]
    for entree in entrees:
        lignes.append("| " + " | ".join(_cellule(c) for c in _ligne(entree, cartes[entree["id"]])) + " |")
    return ENTETE + f"{len(entrees)} cartes.\n\n" + "\n".join(lignes) + "\n"


def main() -> None:
    FICHIER_TABLEAU.write_text(tableau_markdown(), encoding="utf-8")
    print(f"{FICHIER_TABLEAU} regenere")


if __name__ == "__main__":
    main()
