"""
Essai limite (demande utilisateur, 2026-11-11) : la carte Bouclier (CRT_10) a 3, 4, 5 ou 6, sur les
memes combats (memes graines, deck de depart, bot de recherche) : 20 combats difficiles et 12
combats contre des ennemis faibles. Mesure aussi le bouclier maximal atteint (accumulation). Ne
modifie pas config/carte_new.json : la valeur est changee sur les cartes du combat simule.

    python -m outils.simulation.essai_bouclier
"""

import random
import statistics
from collections import Counter

from outils.simulation.bot_new import BotRecherche, jouer_combat
from outils.simulation.combats_new import NOMS, construire_combat
from src.gameplay.combat_new import NatureEvenement
from src.gameplay.statut_new import Statut

# Les flottes les plus dures de la campagne du 2026-11-11 (deck de depart), 4 combats chacune
FLOTTES_DIFFICILES = [
    ("ENM_LE_NETTOYEUR", "ENM_LE_PUZZLE"),
    ("ENM_PAT_LE_PIRATE", "ENM_LE_NETTOYEUR"),
    ("ENM_LE_NETTOYEUR", "ENM_LE_NETTOYEUR"),
    ("ENM_PETIT_JEAN", "ENM_PETIT_JEAN"),
    ("ENM_BOSS_PIRATES",),
]
# Ennemis faibles, ou le joueur a le temps d'empiler du bouclier
FLOTTES_FAIBLES = [("ENM_PETIT_JEAN",), ("ENM_PAT_LE_PIRATE",), ("ENM_MIROIR",)]
FLOTTES = FLOTTES_DIFFICILES + FLOTTES_FAIBLES
GRAINES = range(1, 5)
VALEURS = (3, 4, 5, 6)


class MesureBouclier:
    """Releve le plus gros bouclier porte par un module, apres chaque action et fin de tour."""

    def __init__(self):
        self.maximum = 0

    def apres_action(self, combat) -> None:
        for module in combat.vaisseau.modules:
            self.maximum = max(self.maximum, module.statuts[Statut.BOUCLIER])

    def avant_fin_de_tour(self, combat) -> None:
        self.apres_action(combat)


def jouer(flotte: tuple[str, ...], graine: int, bouclier: int) -> dict:
    combat = construire_combat("depart", flotte, graine, valeurs_cartes={"CRT_10": {"bouclier": bouclier}})
    mesure = MesureBouclier()
    stats = jouer_combat(combat, BotRecherche(random.Random(graine)), mesure)
    stats["absorbe"] = sum(
        e.absorbes_bouclier for e in combat.journal
        if e.nature == NatureEvenement.ATTAQUE and e.cible in combat.vaisseau.modules
    )
    stats["bouclier_max"] = mesure.maximum
    return stats


def _ligne(nom: str, bouclier: int, groupe: list[dict]) -> str:
    jouees, vues = Counter(), Counter()
    for r in groupe:
        jouees.update(r["cartes_jouees"])
        vues.update(r["cartes_vues"])
    maxima = [r["bouclier_max"] for r in groupe]
    return (
        f"| {nom} | {bouclier} | {sum(r['victoire'] for r in groupe)}/{len(groupe)} | "
        f"{statistics.mean(r['pv_principal_perdus'] for r in groupe):.1f} | "
        f"{statistics.mean(r['tours'] for r in groupe):.1f} | "
        f"{100 * jouees['CRT_10'] / max(1, vues['CRT_10']):.0f} % | {statistics.mean(r['absorbe'] for r in groupe):.1f} | "
        f"{statistics.mean(maxima):.1f} / {max(maxima)} |"
    )


def main() -> None:
    resultats = {b: {(f, g): jouer(f, g, b) for f in FLOTTES for g in GRAINES} for b in VALEURS}
    print("| Flotte | Bouclier | Victoires | PV principal perdus (moy.) | Tours | Bouclier joué / vu | "
          "Dégâts absorbés par les boucliers | Bouclier max atteint (moy. / max) |")
    print("|---|---|---|---|---|---|---|---|")
    groupes = [(" + ".join(NOMS[e] for e in f), [f]) for f in FLOTTES]
    groupes += [("**Total difficiles**", FLOTTES_DIFFICILES), ("**Total faibles**", FLOTTES_FAIBLES)]
    for nom, flottes in groupes:
        for bouclier in VALEURS:
            groupe = [r for (f, _g), r in resultats[bouclier].items() if f in flottes]
            print(_ligne(nom, bouclier, groupe))


if __name__ == "__main__":
    main()
