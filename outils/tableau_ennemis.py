"""
Genere config/ennemi_new.md, tableau lisible des ennemis, a partir de config/ennemi_new.json
(seule source de verite). Ne jamais modifier le tableau a la main : relancer ce script apres
chaque modification du JSON (tests/test_tableau_ennemis.py echoue sinon).

    python -m outils.tableau_ennemis
"""

from pathlib import Path

from src.gameplay.ennemi_new import EffetEnnemi, EnnemiNew, ValeurEnnemi, charger_ennemis_new

RACINE = Path(__file__).resolve().parents[1]
FICHIER_JSON = RACINE / "config" / "ennemi_new.json"
FICHIER_TABLEAU = RACINE / "config" / "ennemi_new.md"

ENTETE = """# Ennemis (refonte) — tableau généré

> **Fichier généré automatiquement à partir de `config/ennemi_new.json`, ne pas le modifier à la
> main** : toute modification se fait dans le JSON, puis `python -m outils.tableau_ennemis`
> régénère ce tableau (un test échoue tant qu'il n'est pas à jour).
>
> Valeurs : base, puis augmentation et rythme (« +1 / 3 tours » : +1 aux tours 4, 7, 10…), avant
> coefficient de difficulté. Cycle : une étape par tour ennemi, retour à la première après la
> dernière.

"""

COLONNES = ["Id", "Nom", "Taille", "Cases", "Placement", "PV", "Valeurs", "Cycle d'actions", "Tours 1 à 6"]

NATURES = {"ATTAQUE": "Attaque", "BOUCLIER": "Bouclier", "RENVOI": "Renvoi"}
CIBLES = {
    "PROXIMITE": "le plus proche",
    "TOUS_MODULES": "tous les modules",
    "SOI_MEME": "soi-même",
    "ALLIE_AVANT_SINON_ARRIERE": "un allié avant, sinon arrière",
}


def _cellule(texte: str) -> str:
    """Texte sur une ligne, sans casser le tableau Markdown."""
    return str(texte).replace("|", "\\|").replace("\n", " ")


def _valeur(nom: str, valeur: ValeurEnnemi) -> str:
    if not valeur.augmentation:
        return f"{nom} {valeur.base}"
    rythme = "tour" if valeur.tous_les == 1 else f"{valeur.tous_les} tours"
    return f"{nom} {valeur.base} (+{valeur.augmentation} / {rythme})"


def _effet(effet: EffetEnnemi) -> str:
    fois = f" ×{effet.repetitions}" if effet.repetitions > 1 else ""
    return f"{NATURES[effet.nature.name]} {{{effet.valeur}}}{fois}, {CIBLES[effet.cible.name]}"


def _evolution(ennemi: EnnemiNew) -> str:
    """Valeurs aux tours 1 a 6, coefficient 1."""
    return "<br>".join(
        f"{nom} : " + ", ".join(str(valeur.au_tour(tour)) for tour in range(1, 7))
        for nom, valeur in ennemi.valeurs.items()
    )


def tableau_markdown(fichier_json: Path = FICHIER_JSON) -> str:
    """Contenu complet de config/ennemi_new.md pour ce fichier JSON."""
    ennemis = charger_ennemis_new(fichier_json).values()
    lignes = ["| " + " | ".join(COLONNES) + " |", "|" + "|".join("---" for _ in COLONNES) + "|"]
    for ennemi in ennemis:
        cycle = "<br>".join(
            f"{numero}. " + " + ".join(_effet(effet) for effet in etape)
            for numero, etape in enumerate(ennemi.actions, start=1)
        )
        valeurs = [
            ennemi.id, ennemi.nom, ennemi.taille, str(ennemi.emplacements),
            ennemi.placement.name if ennemi.placement else "—", str(ennemi.pv_base),
            "<br>".join(_valeur(nom, valeur) for nom, valeur in ennemi.valeurs.items()), cycle, _evolution(ennemi),
        ]
        lignes.append("| " + " | ".join(_cellule(valeur) for valeur in valeurs) + " |")
    return ENTETE + f"{len(ennemis)} ennemis.\n\n" + "\n".join(lignes) + "\n"


def main() -> None:
    FICHIER_TABLEAU.write_text(tableau_markdown(), encoding="utf-8")
    print(f"{FICHIER_TABLEAU} regenere")


if __name__ == "__main__":
    main()
