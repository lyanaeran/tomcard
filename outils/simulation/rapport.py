"""
Tableaux de synthese (Markdown) a partir des resultats bruts d'outils/simulation/etudes.py.
"""

from collections import Counter, defaultdict
from statistics import mean

from src.gameplay.donnees import charger_cartes, charger_modules

from outils.simulation.format import moyenne as _moy
from outils.simulation.format import pourcentage as _pct


def _tableau(entetes: list[str], lignes: list[list]) -> str:
    texte = "| " + " | ".join(entetes) + " |\n|" + "|".join("---" for _ in entetes) + "|\n"
    return texte + "".join("| " + " | ".join(str(c) for c in ligne) + " |\n" for ligne in lignes)


def _noms_modules() -> dict[str, str]:
    return {spec.id: spec.nom for spec in charger_modules()}


def validation_bot(combats: list[dict]) -> str:
    lignes = []
    for bot in ("recherche", "aleatoire"):
        liste = [c for c in combats if c["bot"] == bot and c.get("validation")]
        lignes.append([
            bot, len(liste), _pct(sum(c["victoire"] for c in liste), len(liste)),
            _pct(sum(c["enlise"] for c in liste), len(liste)), _moy([c["tours"] for c in liste]),
            _moy([c["pv_principal_perdus"] for c in liste]),
        ])
    return _tableau(["Bot", "Combats", "Victoires", "Enlisés", "Tours moyens", "PV principal perdus"], lignes)


def combats_isoles(combats: list[dict]) -> str:
    noms = _noms_modules()
    lignes = []
    for module_id in sorted({c["module_id"] for c in combats}):
        for niveau in sorted({c["niveau"] for c in combats}):
            liste = [c for c in combats if c["module_id"] == module_id and c["niveau"] == niveau
                     and c["bot"] == "recherche" and not c.get("validation")]
            if liste:
                lignes.append([
                    noms[module_id], niveau, len(liste), _pct(sum(c["victoire"] for c in liste), len(liste)),
                    _pct(sum(c["enlise"] for c in liste), len(liste)), _moy([c["tours"] for c in liste]),
                    _moy([c["pv_principal_perdus"] for c in liste]),
                ])
    return _tableau(["Module", "Niveau", "Combats", "Victoires", "Enlisés", "Tours moyens", "PV principal perdus"], lignes)


def parties_par_module(parties: list[dict]) -> str:
    noms = _noms_modules()
    lignes = []
    for module_id in sorted({p["module_id"] for p in parties}):
        liste = [p for p in parties if p["module_id"] == module_id]
        combats = [c for p in liste for c in p["combats"]]
        lignes.append([
            noms[module_id], len(liste), _pct(sum(p["victoire_finale"] for p in liste), len(liste)),
            _moy([p["niveau_atteint"] for p in liste]),
            _moy([p["pv_principal_fin"] for p in liste if p["victoire_finale"]]),
            _pct(sum(c["victoire"] for c in combats), len(combats)),
            _pct(sum(c["enlise"] for c in combats), len(combats)),
        ])
    return _tableau(
        ["Module", "Parties", "Victoires finales", "Niveau moyen atteint", "PV principal en fin (victoires)",
         "Combats gagnés", "Combats enlisés"], lignes)


def fin_de_partie_par_niveau(parties: list[dict]) -> str:
    fins = Counter(p["niveau_atteint"] for p in parties if not p["victoire_finale"])
    total = len(parties)
    lignes = [[niveau, fins[niveau], _pct(fins[niveau], total)] for niveau in sorted(fins)]
    lignes.append(["Victoire finale", sum(p["victoire_finale"] for p in parties),
                   _pct(sum(p["victoire_finale"] for p in parties), total)])
    return _tableau(["Niveau de la défaite", "Parties", "Part"], lignes)


def ennemis(parties: list[dict]) -> str:
    par_ennemi = defaultdict(list)
    for p in parties:
        for c in p["combats"]:
            for nom in set(c["ennemis"]):
                par_ennemi[nom].append(c)
    lignes = []
    for nom, liste in sorted(par_ennemi.items(), key=lambda e: -len(e[1])):
        lignes.append([
            nom, len(liste), _pct(sum(c["victoire"] for c in liste), len(liste)),
            _pct(sum(c["enlise"] for c in liste), len(liste)), _moy([c["tours"] for c in liste]),
            _moy([c["pv_principal_perdus"] for c in liste]),
        ])
    return _tableau(["Ennemi présent", "Combats", "Victoires", "Enlisés", "Tours moyens", "PV principal perdus"], lignes)


def cartes(parties: list[dict]) -> str:
    """Taux de jeu : exemplaires joues / exemplaires presents en main en debut de tour."""
    jouees, vues = Counter(), Counter()
    for p in parties:
        for c in p["combats"]:
            jouees.update(c["cartes_jouees"])
            vues.update(c["cartes_vues"])
    toutes = charger_cartes()
    lignes = []
    for id_carte in sorted(vues, key=lambda i: -(jouees[i] / vues[i])):
        carte = toutes[id_carte]
        lignes.append([carte.nom, carte.rarete.name.capitalize(), carte.cout, vues[id_carte], jouees[id_carte],
                       _pct(jouees[id_carte], vues[id_carte])])
    jamais_vues = sorted(carte.nom for id_carte, carte in toutes.items() if id_carte not in vues)
    texte = _tableau(["Carte", "Rareté", "Coût", "En main", "Jouée", "Taux de jeu"], lignes)
    return texte + f"\nCartes jouables jamais apparues en main : {', '.join(jamais_vues) or 'aucune'}.\n"


def choix_clones(parties: list[dict], clones: list[dict]) -> str:
    """Compare, pour un meme point de decision, l'option prise par la politique et une autre."""
    bases = {(p["graine"], p["module_id"]): p for p in parties}
    paires = defaultdict(list)
    for clone in clones:
        graine, module_id, index = clone["point"]
        base = bases[(graine, module_id)]
        pris = next(d[2] for d in base["decisions"] if d[0] == index)
        paires[(pris, clone["option"])].append((base, clone))
    lignes = []
    for (pris, autre), liste in sorted(paires.items(), key=lambda e: -len(e[1])):
        meilleur = sum(c["niveau_atteint"] > b["niveau_atteint"] or (c["victoire_finale"] and not b["victoire_finale"])
                       for b, c in liste)
        pire = sum(c["niveau_atteint"] < b["niveau_atteint"] or (b["victoire_finale"] and not c["victoire_finale"])
                   for b, c in liste)
        lignes.append([
            f"{pris} → {autre}", len(liste),
            _pct(sum(b["victoire_finale"] for b, _ in liste), len(liste)),
            _pct(sum(c["victoire_finale"] for _, c in liste), len(liste)),
            f"{mean(c['niveau_atteint'] - b['niveau_atteint'] for b, c in liste):+.1f}",
            _pct(meilleur, len(liste)), _pct(pire, len(liste)),
        ])
    return _tableau(
        ["Choix de la politique → autre choix", "Points", "Victoires (politique)", "Victoires (autre choix)",
         "Écart de niveau atteint", "Autre choix meilleur", "Autre choix pire"], lignes)
