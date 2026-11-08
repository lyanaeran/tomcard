"""
Le tableau config/ennemi_new.md doit toujours etre a jour avec config/ennemi_new.json, dont il est
genere (outils/tableau_ennemis.py).
"""

from outils.tableau_ennemis import FICHIER_TABLEAU, tableau_markdown


def test_le_tableau_des_ennemis_est_a_jour_avec_le_json():
    assert FICHIER_TABLEAU.read_text(encoding="utf-8") == tableau_markdown(), (
        "config/ennemi_new.md n'est plus a jour : lancer `python -m outils.tableau_ennemis`"
    )
