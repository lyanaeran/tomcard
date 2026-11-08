"""
Le tableau config/module_new.md doit toujours etre a jour avec config/module_new.json, dont il est
genere (outils/tableau_modules.py).
"""

from outils.tableau_modules import FICHIER_TABLEAU, tableau_markdown


def test_le_tableau_des_modules_est_a_jour_avec_le_json():
    assert FICHIER_TABLEAU.read_text(encoding="utf-8") == tableau_markdown(), (
        "config/module_new.md n'est plus a jour : lancer `python -m outils.tableau_modules`"
    )
