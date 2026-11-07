"""
Lance les etudes d'equilibrage et ecrit les resultats bruts (JSON) et leurs tableaux (Markdown)
dans outils/simulation/resultats/ (ignore par git).

    python -m outils.simulation --budget 500 --parties-par-module 40 --validation 30
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from outils.simulation import rapport
from outils.simulation.etudes import lancer

DOSSIER_RESULTATS = Path(__file__).parent / "resultats"


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    arguments.add_argument("--budget", type=int, default=500, help="nombre maximal de simulations")
    arguments.add_argument("--parties-par-module", type=int, default=40)
    arguments.add_argument("--validation", type=int, default=30, help="combats de validation du bot")
    arguments.add_argument("--graine", type=int, default=1)
    options = arguments.parse_args()

    debut = time.time()
    resultats = lancer(options.budget, options.parties_par_module, options.validation, options.graine)
    resultats["duree_s"] = round(time.time() - debut, 1)
    resultats["parametres"] = vars(options)

    DOSSIER_RESULTATS.mkdir(exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H%M")
    (DOSSIER_RESULTATS / f"{horodatage}_resultats.json").write_text(json.dumps(resultats, default=str))
    parties = resultats["parties"]
    sections = [
        ("Validation du bot", rapport.validation_bot(resultats["combats"])),
        ("Combats isolés par module", rapport.combats_isoles(resultats["combats"])),
        ("Parties complètes par module", rapport.parties_par_module(parties)),
        ("Fin de partie par niveau", rapport.fin_de_partie_par_niveau(parties)),
        ("Ennemis", rapport.ennemis(parties)),
        ("Cartes (taux de jeu)", rapport.cartes(parties)),
        ("Choix clonés", rapport.choix_clones(parties, resultats["clones"])),
    ]
    texte = "".join(f"## {titre}\n\n{tableau}\n" for titre, tableau in sections)
    (DOSSIER_RESULTATS / f"{horodatage}_tableaux.md").write_text(texte)
    print(texte)
    print(f"{resultats['simulations']} simulations en {resultats['duree_s']} s -> {DOSSIER_RESULTATS}")


if __name__ == "__main__":
    main()
