"""
Le tableau config/module_new.md doit toujours etre a jour avec config/module_new.json, dont il est
genere (outils/tableau_modules.py).
"""

import json

import pytest

from outils.tableau_modules import FICHIER_JSON, FICHIER_TABLEAU, tableau_markdown


def test_le_tableau_des_modules_est_a_jour_avec_le_json():
    assert FICHIER_TABLEAU.read_text(encoding="utf-8") == tableau_markdown(), (
        "config/module_new.md n'est plus a jour : lancer `python -m outils.tableau_modules`"
    )


def test_une_carte_absente_de_carte_new_json_est_une_erreur(tmp_path):
    donnees = json.loads(FICHIER_JSON.read_text(encoding="utf-8"))
    donnees["modules"][1]["cartes"].append("CRT_99")
    fichier = tmp_path / "module_new.json"
    fichier.write_text(json.dumps(donnees), encoding="utf-8")

    with pytest.raises(ValueError, match="CRT_99"):
        tableau_markdown(fichier)
