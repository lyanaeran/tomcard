"""
Etudes d'equilibrage (specs/simulation.md 4 a 5) executees en parallele sur tous les coeurs, dans
la limite d'un budget de simulations (une simulation = un combat isole ou une partie complete).

- validation du bot : bot de recherche contre bot aleatoire sur les memes combats (3.4)
- combats isoles par module secondaire, a plusieurs niveaux (4)
- parties completes a module force, memes graines pour chaque module (5.3)
- choix clones : une partie de l'etude precedente est rejouee avec un autre choix du prochain
  niveau a un point de decision, toutes choses egales par ailleurs (5.2)
"""

import os
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict

from src.gameplay import deroulement
from src.gameplay.module_new import charger_modules_new
from src.gameplay.parcours import modules_equipables
from src.gameplay.partie import combat_depuis_partie, nouvelle_partie

from outils.simulation.bot_new import BotAleatoire, BotRecherche, jouer_combat
from outils.simulation.partie_auto import jouer_partie

# Modules secondaires testables : ceux que le jeu peut proposer (jouables et avec des cartes)
MODULES_TESTES = [module.id for module in modules_equipables(charger_modules_new().values())]
NIVEAUX_COMBATS_ISOLES = (3, 7, 10)


def _combat_isole(module_id: str, niveau: int, graine: int, bot: str, validation: bool) -> dict:
    """Combat au niveau donne, avec le deck de depart et le module equipe au Niveau 1."""
    partie = nouvelle_partie(random.Random(graine))
    cartes = deroulement.choisir_module(partie, charger_modules_new()[module_id], random.Random(graine))
    carte = max(cartes, key=lambda c: c.rarete.value) if cartes else None
    deroulement.resoudre_carte_module(partie, carte)
    partie.niveau = niveau
    classe_bot = BotRecherche if bot == "recherche" else BotAleatoire
    stats = jouer_combat(combat_depuis_partie(partie, random.Random(graine)), classe_bot(random.Random(graine)))
    stats.update({"module_id": module_id, "niveau": niveau, "graine": graine, "bot": bot, "validation": validation})
    return stats


def _partie(graine: int, module_force: str | None, choix_imposes: dict | None, etiquette: dict) -> dict:
    resultat = asdict(jouer_partie(graine, module_force, choix_imposes))
    resultat.update(etiquette)
    return resultat


def lancer(budget: int, parties_par_module: int, combats_validation: int, graine_depart: int = 1) -> dict:
    """Lance toutes les etudes dans la limite de `budget` simulations. Renvoie les resultats bruts."""
    taches_combats = []
    for i in range(combats_validation):
        module_id = MODULES_TESTES[i % len(MODULES_TESTES)]
        niveau = NIVEAUX_COMBATS_ISOLES[i % len(NIVEAUX_COMBATS_ISOLES)]
        for bot in ("recherche", "aleatoire"):
            taches_combats.append((module_id, niveau, graine_depart + i, bot, True))
    for module_id in MODULES_TESTES:
        for niveau in NIVEAUX_COMBATS_ISOLES:
            for k in range(6):
                taches_combats.append((module_id, niveau, graine_depart + 1000 + k, "recherche", False))
    graines_parties = [graine_depart + 2000 + k for k in range(parties_par_module)]
    taches_parties = [
        (graine, module_id, None, {"etude": "module_force"}) for module_id in MODULES_TESTES for graine in graines_parties
    ]
    restant = budget - len(taches_combats) - len(taches_parties)
    if restant < 0:
        raise ValueError(f"Budget insuffisant : {len(taches_combats) + len(taches_parties)} simulations prevues")

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executeur:
        combats = list(executeur.map(_combat_isole, *zip(*taches_combats)))
        parties = list(executeur.map(_partie, *zip(*taches_parties)))

        # Choix clones : un point de decision par partie de base, autres options rejouees
        taches_clones = []
        for base in parties:
            if not base["decisions"]:
                continue
            index, options, pris = random.Random(base["graine"]).choice(base["decisions"])
            for option in options:
                if option != pris and len(taches_clones) < restant:
                    etiquette = {"etude": "clone", "point": (base["graine"], base["module_id"], index), "option": option}
                    taches_clones.append((base["graine"], base["module_id"], {index: option}, etiquette))
        clones = list(executeur.map(_partie, *zip(*taches_clones))) if taches_clones else []

    return {
        "combats": combats,
        "parties": parties,
        "clones": clones,
        "simulations": len(combats) + len(parties) + len(clones),
    }
