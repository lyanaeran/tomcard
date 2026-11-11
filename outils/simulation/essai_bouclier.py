"""
Essai limite (demande utilisateur, 2026-11-11) : la carte Bouclier (CRT_10) a 3, 4, 5 ou 6, sur les
memes 20 combats difficiles (memes graines, deck de depart, bot de recherche). Ne modifie pas
config/carte_new.json : la valeur est changee sur les cartes du combat simule.

    python -m outils.simulation.essai_bouclier
"""

import random
import statistics
from collections import Counter

from outils.simulation.bot_new import BotRecherche, jouer_combat
from outils.simulation.combats_new import NOMS, construire_combat
from src.gameplay.combat_new import NatureEvenement

# Les flottes les plus dures de la campagne du 2026-11-11 (deck de depart), 4 combats chacune
FLOTTES = [
    ("ENM_LE_NETTOYEUR", "ENM_LE_PUZZLE"),
    ("ENM_PAT_LE_PIRATE", "ENM_LE_NETTOYEUR"),
    ("ENM_LE_NETTOYEUR", "ENM_LE_NETTOYEUR"),
    ("ENM_PETIT_JEAN", "ENM_PETIT_JEAN"),
    ("ENM_BOSS_PIRATES",),
]
GRAINES = range(1, 5)
VALEURS = (3, 4, 5, 6)


def jouer(flotte: tuple[str, ...], graine: int, bouclier: int) -> dict:
    combat = construire_combat("depart", flotte, graine, valeurs_cartes={"CRT_10": {"bouclier": bouclier}})
    stats = jouer_combat(combat, BotRecherche(random.Random(graine)))
    stats["absorbe"] = sum(
        e.absorbes_bouclier for e in combat.journal
        if e.nature == NatureEvenement.ATTAQUE and e.cible in combat.vaisseau.modules
    )
    return stats


def main() -> None:
    resultats = {b: {(f, g): jouer(f, g, b) for f in FLOTTES for g in GRAINES} for b in VALEURS}
    print("| Flotte | Bouclier | Victoires | PV principal perdus (moy.) | Tours | Bouclier joué / vu | Dégâts absorbés par les boucliers |")
    print("|---|---|---|---|---|---|---|")
    for flotte in FLOTTES + [None]:
        for bouclier in VALEURS:
            groupe = [r for (f, _g), r in resultats[bouclier].items() if flotte is None or f == flotte]
            jouees, vues = Counter(), Counter()
            for r in groupe:
                jouees.update(r["cartes_jouees"])
                vues.update(r["cartes_vues"])
            nom = "**Total**" if flotte is None else " + ".join(NOMS[e] for e in flotte)
            print(
                f"| {nom} | {bouclier} | {sum(r['victoire'] for r in groupe)}/{len(groupe)} | "
                f"{statistics.mean(r['pv_principal_perdus'] for r in groupe):.1f} | "
                f"{statistics.mean(r['tours'] for r in groupe):.1f} | "
                f"{100 * jouees['CRT_10'] / vues['CRT_10']:.0f} % | {statistics.mean(r['absorbe'] for r in groupe):.1f} |"
            )


if __name__ == "__main__":
    main()
