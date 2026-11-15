"""
Le tableau config/cartes.md doit toujours etre a jour avec config/cartes.json, dont il est
genere (outils/tableau_cartes.py).
"""

from outils.tableau_cartes import FICHIER_TABLEAU, tableau_markdown


def test_le_tableau_des_cartes_est_a_jour_avec_le_json():
    assert FICHIER_TABLEAU.read_text(encoding="utf-8") == tableau_markdown(), (
        "config/cartes.md n'est plus a jour : lancer `python -m outils.tableau_cartes`"
    )
