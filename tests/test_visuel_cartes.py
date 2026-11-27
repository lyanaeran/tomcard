"""Images du nouvel affichage des cartes (src/ui/carte_visuel.py, htmlCarteVisuel de src/web/app.js) :
un gabarit par rarete, une icone par type, et le meme mapping des types sur PC et sur le web."""

import re

from src.gameplay.carte import CategorieCarte, RareteCarte
from src.gameplay.partie import RACINE

ICONES_BARRE = ("cout", "munitions", "lancements")


def test_un_gabarit_par_rarete():
    for rarete in RareteCarte:
        assert (RACINE / f"assets/interface/cartes/modele_{rarete.name.lower()}.png").exists(), rarete


def test_une_icone_par_type_et_pour_la_barre_du_haut():
    for categorie in CategorieCarte:
        assert (RACINE / f"assets/interface/icones/type_{categorie.name.lower()}.png").exists(), categorie
    for nom in ICONES_BARRE:
        assert (RACINE / f"assets/interface/icones/{nom}.png").exists(), nom


def test_meme_icone_de_type_sur_pc_et_sur_le_web():
    texte_pc = (RACINE / "src/ui/carte_visuel.py").read_text(encoding="utf-8")
    texte_web = (RACINE / "src/web/app.js").read_text(encoding="utf-8")
    bloc_pc = texte_pc[texte_pc.index("ICONE_TYPE = {") :]
    bloc_web = texte_web[texte_web.index("const ICONE_TYPE = {") :]
    pc = dict(re.findall(r'"([A-Z]+)": "(type_[a-z]+)"', bloc_pc[: bloc_pc.index("}")]))
    web = dict(re.findall(r'([A-Z]+): "(type_[a-z]+)"', bloc_web[: bloc_web.index("}")]))
    assert pc == web == {c.name: f"type_{c.name.lower()}" for c in CategorieCarte}


def test_memes_zones_du_gabarit_sur_pc_et_sur_le_web():
    """Les zones de ZONE_* (fractions) se retrouvent en % dans style.css (.cv-*)."""
    texte_pc = (RACINE / "src/ui/carte_visuel.py").read_text(encoding="utf-8")
    css = (RACINE / "src/web/style.css").read_text(encoding="utf-8")
    for zone, classe in (("BARRE", "cv-barre"), ("FENETRE", "cv-illustration"), ("TEXTE", "cv-texte"), ("NOM", "cv-nom")):
        gauche, haut, droite, bas = (float(v) for v in re.search(rf"ZONE_{zone} = \(([^)]*)\)", texte_pc).group(1).split(","))
        regles = "".join(re.findall(rf"\.{classe} \{{([^}}]*)\}}", css))
        valeurs = dict(re.findall(r"(left|top|width|height): ([\d.]+)%", regles))
        assert abs(float(valeurs["left"]) - gauche * 100) < 0.06, zone
        assert abs(float(valeurs["top"]) - haut * 100) < 0.06, zone
        assert abs(float(valeurs["width"]) - (droite - gauche) * 100) < 0.06, zone
        assert abs(float(valeurs["height"]) - (bas - haut) * 100) < 0.06, zone


def test_chaque_description_finit_par_un_point():
    """Decision utilisateur (2026-11-27) : la phrase ecrite sur la carte finit par un point."""
    import json

    cartes = json.loads((RACINE / "config/cartes.json").read_text(encoding="utf-8"))["cartes"]
    sans_point = [c["nom"] for c in cartes if not c["description"].rstrip().endswith(".")]
    assert sans_point == []
