"""
Simulations de combats isoles avec le combat de la refonte (CombatNew, specs/refonte-combat.md).
Deux objectifs (demande utilisateur, 2026-11-11) :
1. robustesse : verifier a chaque action des invariants du combat (piles de cartes, PV, statuts,
   journal, intentions, fin de combat), avec le bot aleatoire (beaucoup de coups varies) et le
   bot de recherche ;
2. equilibre : reperer les problemes flagrants par ennemi, paire d'ennemis et Boss.

Pas de partie complete : le combat de la refonte n'est pas encore branche au parcours.

    caffeinate -i python -m outils.simulation.combats_new --graines 10
"""

import argparse
import itertools
import json
import os
import random
import statistics
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

from src.gameplay.carte_new import RareteCarte, charger_cartes_new
from src.gameplay.combat_new import CombatNew, EtatCombatNew, NatureEvenement
from src.gameplay.deck_new import TAILLE_MAIN_MAX, deck_de_depart
from src.gameplay.ennemi_new import NatureEffetEnnemi, PlacementEnnemi, charger_ennemis_new
from src.gameplay.flotte_new import FlotteNew
from src.gameplay.module_new import charger_modules_new
from src.gameplay.position import Colonne, Position, Rangee

from outils.simulation.bot_new import BotAleatoire, BotRecherche, jouer_combat

DOSSIER_RESULTATS = Path(__file__).parent / "resultats"

# Vaisseau teste : principal + Lanceur de missiles, seuls modules jouables (avant gauche : premier
# emplacement libre, comme au choix du module du Niveau 1)
EMPLACEMENT_LANCEUR = "avant_gauche"
ENNEMIS_STANDARD = ["ENM_PAT_LE_PIRATE", "ENM_LE_NETTOYEUR", "ENM_PETIT_JEAN", "ENM_LE_PUZZLE", "ENM_MIROIR"]
ID_BOSS = "ENM_BOSS_PIRATES"
# Cartes ajoutees au deck de depart pour le deck "etoffe" (milieu de partie)
CARTES_AJOUTEES_ETOFFE = 5
DEGATS = (NatureEvenement.ATTAQUE, NatureEvenement.RENVOI, NatureEvenement.INCENDIE)

POSITIONS_AVANT = [Position(Colonne.AVANT, rangee) for rangee in Rangee]
POSITIONS_ARRIERE = [Position(Colonne.ARRIERE, rangee) for rangee in Rangee]


# --- Mise en place d'un combat ---


def _module_de_chaque_carte() -> dict[str, str]:
    """id de carte -> exemplaire de module de rattachement (M1 principal, M2 Lanceur)."""
    exemplaires = {"MOD_1": "M1", "MOD_2": "M2"}
    return {id_carte: exemplaires[module.id] for module in charger_modules_new().values() for id_carte in module.cartes}


def construire_deck(variante: str, aleatoire: random.Random) -> list:
    """Deck de depart, plus une carte du Lanceur (choix du module, Niveau 1) ; le deck "etoffe"
    ajoute CARTES_AJOUTEES_ETOFFE cartes revues hors Base, tirees au hasard (jouables ou non
    par l'ancien moteur : CombatNew les gere toutes)."""
    modeles = charger_cartes_new()
    modules = _module_de_chaque_carte()
    deck = deck_de_depart(modeles, "M1")
    cartes_lanceur = sorted(id_carte for id_carte, exemplaire in modules.items() if exemplaire == "M2")
    ajouts = [aleatoire.choice(cartes_lanceur)]
    if variante == "etoffe":
        hors_base = sorted(id_carte for id_carte, carte in modeles.items() if carte.rarete != RareteCarte.BASE)
        ajouts += [aleatoire.choice(hors_base) for _ in range(CARTES_AJOUTEES_ETOFFE)]
    return deck + [modeles[id_carte].copie(exemplaire_module=modules[id_carte]) for id_carte in ajouts]


def construire_flotte(ids_ennemis: tuple[str, ...], aleatoire: random.Random) -> FlotteNew:
    """Place les ennemis comme le jeu actuel (config_poc._placer_specs_avec_preference) :
    protecteurs a l'avant, proteges a l'arriere, les autres a l'avant puis a l'arriere ; le Boss
    sur la rangee du milieu, avant et arriere. Provisoire : la composition des flottes de la
    refonte n'est pas encore faite."""
    modeles = charger_ennemis_new()
    ennemis = [modeles[id_ennemi].pour_combat(1) for id_ennemi in ids_ennemis]
    if ids_ennemis == (ID_BOSS,):
        return FlotteNew({Position(Colonne.AVANT, Rangee.MID): ennemis[0], Position(Colonne.ARRIERE, Rangee.MID): ennemis[0]})
    avant, arriere = POSITIONS_AVANT[:], POSITIONS_ARRIERE[:]
    aleatoire.shuffle(avant)
    aleatoire.shuffle(arriere)
    places = {}
    ordre = sorted(ennemis, key=lambda e: {PlacementEnnemi.PROTECTEUR_AVANT: 0, PlacementEnnemi.PROTEGE_ARRIERE: 1}.get(e.placement, 2))
    for ennemi in ordre:
        if ennemi.placement == PlacementEnnemi.PROTEGE_ARRIERE and arriere:
            places[arriere.pop(0)] = ennemi
        else:
            places[(avant or arriere).pop(0)] = ennemi
    return FlotteNew(places)


def construire_combat(
    variante: str, ids_ennemis: tuple[str, ...], graine: int, pv_principal: int | None = None,
    valeurs_cartes: dict[str, dict[str, int]] | None = None,
) -> CombatNew:
    """Combat isole ; `pv_principal` : PV du principal au debut (pleins par defaut) ;
    `valeurs_cartes` : variante de valeurs de cartes pour un essai, ex. {"CRT_10": {"bouclier": 4}},
    sans toucher a config/carte_new.json."""
    aleatoire = random.Random(f"{graine}:{variante}:{ids_ennemis}")
    modeles = charger_modules_new()
    principal = modeles["MOD_1"].nouvel_exemplaire("M1", "base")
    if pv_principal is not None:
        principal.pv = pv_principal
    modules = [
        principal.copie_pour_combat(),
        modeles["MOD_2"].nouvel_exemplaire("M2", EMPLACEMENT_LANCEUR).copie_pour_combat(),
    ]
    deck = construire_deck(variante, aleatoire)
    for carte in deck:
        carte.valeurs.update((valeurs_cartes or {}).get(carte.id, {}))
    return CombatNew(modules, deck, construire_flotte(ids_ennemis, aleatoire), random.Random(aleatoire.random()))


# --- Invariants (robustesse) ---


class Controle:
    """Verifie les invariants du combat apres chaque action et chaque fin de tour ; note les
    violations au lieu de s'arreter, pour toutes les voir dans le rapport."""

    def __init__(self, combat: CombatNew):
        self.nb_cartes = len(combat.deck.toutes_les_cartes())
        self.violations: list[str] = []
        self.tour = combat.tour
        self._intentions: dict[int, list[int]] = {}
        self._taille_journal = 0

    def _verifier(self, condition: bool, message: str) -> None:
        if not condition and message not in self.violations:
            self.violations.append(message)

    def avant_fin_de_tour(self, combat: CombatNew) -> None:
        """Retient les degats annonces par les intentions, compares ensuite aux attaques jouees."""
        self._intentions = {
            id(intention.ennemi): [e.valeur for e in intention.effets if e.effet.nature == NatureEffetEnnemi.ATTAQUE]
            for intention in combat.intentions()
        }
        self._taille_journal = len(combat.journal)

    def apres_action(self, combat: CombatNew) -> None:
        verifier = self._verifier
        deck = combat.deck
        cartes = deck.toutes_les_cartes()
        verifier(len(cartes) == self.nb_cartes, "nombre de cartes du combat change")
        verifier(len({id(carte) for carte in cartes}) == len(cartes), "carte presente dans deux piles")
        verifier(len(deck.main) <= TAILLE_MAIN_MAX, "main au-dela de 10 cartes")
        verifier(combat.electricite >= 0, "electricite negative")
        verifier(combat.tour >= self.tour, "numero de tour qui recule")
        self.tour = combat.tour
        for carte in deck.epuisees:
            verifier(carte.est_epuisee, "carte non epuisee dans les epuisees")
        for module in combat.vaisseau.modules:
            verifier(0 <= module.pv_combat <= module.pv_max, f"PV hors bornes ({module.nom})")
            verifier(all(v > 0 for v in module.statuts.intensites.values()), "statut a intensite nulle")
            if module.est_detruit():
                verifier(not module.statuts.intensites, "module detruit avec des statuts")
                actives = deck.pioche + deck.main + deck.defausse
                verifier(
                    not any(c.exemplaire_module == module.exemplaire and not c.persistante for c in actives),
                    "carte d'un module detruit hors de la pile Hors service",
                )
        for ennemi in combat.flotte.ennemis:
            verifier(0 <= ennemi.pv <= ennemi.pv_max, f"PV hors bornes ({ennemi.nom})")
            verifier(all(v > 0 for v in ennemi.statuts.intensites.values()), "statut a intensite nulle")
            if ennemi.est_detruit():
                verifier(not ennemi.statuts.intensites, "ennemi detruit avec des statuts")
        verifier((combat.etat == EtatCombatNew.VICTOIRE) == combat.flotte.est_vide(), "victoire incoherente")
        verifier(
            (combat.etat == EtatCombatNew.DEFAITE) == combat.vaisseau.principal.est_detruit(), "defaite incoherente",
        )
        for evenement in combat.journal:
            if evenement.nature in DEGATS:
                proteges = evenement.annules_leurre + evenement.renvoyes + evenement.absorbes_bouclier
                verifier(proteges + evenement.pv_perdus <= evenement.valeur, "journal : detail des degats > degats")
                verifier(evenement.pv_perdus >= 0 and evenement.pv_restants >= 0, "journal : PV negatifs")
        verifier(
            combat.journal[-1].nature not in (NatureEvenement.VICTOIRE, NatureEvenement.DEFAITE)
            or combat.etat != EtatCombatNew.EN_COURS,
            "fin de combat notee mais combat en cours",
        )
        # Attaques ennemies du tour qui vient de se jouer : valeur annoncee par l'intention
        if self._intentions:
            for evenement in combat.journal[self._taille_journal:]:
                if evenement.nature == NatureEvenement.ATTAQUE and id(evenement.source) in self._intentions:
                    verifier(
                        evenement.valeur in self._intentions[id(evenement.source)],
                        "attaque ennemie differente de son intention",
                    )
            self._intentions = {}


# --- Une simulation ---


def simuler(variante: str, ids_ennemis: tuple[str, ...], graine: int, bot: str, etude: str) -> dict:
    """Un combat isole ; renvoie ses statistiques, les violations d'invariants et l'eventuelle
    exception."""
    resultat = {"variante": variante, "ennemis": list(ids_ennemis), "graine": graine, "bot": bot, "etude": etude}
    try:
        combat = construire_combat(variante, ids_ennemis, graine)
        controle = Controle(combat)
        classe = BotRecherche if bot == "recherche" else BotAleatoire
        stats = jouer_combat(combat, classe(random.Random(graine)), controle)
        resultat.update(stats)
        resultat["violations"] = controle.violations
        resultat.update(_mesures_du_journal(combat))
    except Exception:  # noqa: BLE001 - toute erreur du moteur est un resultat a rapporter
        resultat["exception"] = traceback.format_exc(limit=6)
    return resultat


def _mesures_du_journal(combat: CombatNew) -> dict:
    journal = combat.journal
    lanceur = next(module for module in combat.vaisseau.modules if not module.principal)
    tour_destruction = next(
        (e.tour for e in journal if e.nature == NatureEvenement.MODULE_DETRUIT and e.cible is lanceur), None,
    )
    return {
        "renvoi_subi": sum(e.valeur for e in journal if e.nature == NatureEvenement.RENVOI),
        "absorbe_bouclier_modules": sum(
            e.absorbes_bouclier for e in journal if e.nature == NatureEvenement.ATTAQUE and e.cible in combat.vaisseau.modules
        ),
        "degats_incendie": sum(e.pv_perdus for e in journal if e.nature == NatureEvenement.INCENDIE),
        "cartes_hors_service": len(combat.deck.hors_service),
        "tour_destruction_lanceur": tour_destruction,
    }


# --- Enchainement de combats (approximation d'une partie) ---

# Approximation d'une partie, en attendant le branchement au parcours : un combat par niveau, du
# niveau 2 au niveau 10, flottes tirees comme aujourd'hui (1 ennemi jusqu'au niveau 5, 2 ensuite,
# Boss au niveau 10), PV du principal reportes d'un combat a l'autre, sans Station ni Aventure.
# Deck "depart" jusqu'au niveau 5, "etoffe" ensuite (le deck grossit avec les recompenses).
NIVEAUX = range(2, 11)


def simuler_enchainement(graine: int) -> dict:
    aleatoire = random.Random(f"enchainement:{graine}")
    pv = charger_modules_new()["MOD_1"].pv_max_base
    pv_par_niveau = {}
    resultat = {"etude": "enchainement", "graine": graine}
    try:
        for niveau in NIVEAUX:
            if niveau == 10:
                flotte = (ID_BOSS,)
            else:
                flotte = tuple(aleatoire.choice(ENNEMIS_STANDARD) for _ in range(1 if niveau <= 5 else 2))
            combat = construire_combat("depart" if niveau <= 5 else "etoffe", flotte, graine * 100 + niveau, pv)
            controle = Controle(combat)
            stats = jouer_combat(combat, BotRecherche(random.Random(graine * 100 + niveau)), controle)
            if controle.violations:
                resultat["violations"] = controle.violations
            pv = combat.vaisseau.principal.pv_combat
            pv_par_niveau[niveau] = pv
            if not stats["victoire"]:
                resultat.update(niveau_atteint=niveau, victoire_finale=False, pv_par_niveau=pv_par_niveau, flotte_fatale=flotte)
                return resultat
        resultat.update(niveau_atteint=10, victoire_finale=True, pv_par_niveau=pv_par_niveau)
    except Exception:  # noqa: BLE001
        resultat["exception"] = traceback.format_exc(limit=6)
    return resultat


def tableau_enchainement(enchainements: list[dict]) -> str:
    valides = [r for r in enchainements if "exception" not in r]
    n = len(valides)
    lignes = ["| Niveau | Parties encore en vie au début | PV du principal au début (moyenne) |", "|---|---|---|"]
    for niveau in NIVEAUX:
        vivantes = [r for r in valides if r["niveau_atteint"] >= niveau]
        pv_debut = [60 if niveau == 2 else r["pv_par_niveau"].get(niveau - 1) for r in vivantes]
        lignes.append(f"| {niveau}{' (Boss)' if niveau == 10 else ''} | {_pct(len(vivantes), n)} | {_moy(pv_debut)} |")
    gagnees = sum(r["victoire_finale"] for r in valides)
    texte = "\n".join(lignes) + f"\n\n**Parties gagnées (Boss battu) : {_pct(gagnees, n)}** sur {n}.\n"
    fatales = Counter(
        " + ".join(sorted(NOMS[e] for e in r["flotte_fatale"])) for r in valides if not r["victoire_finale"]
    )
    texte += "\nFlottes fatales : " + ", ".join(f"{nom} ({nombre})" for nom, nombre in fatales.most_common()) + "\n"
    return texte


# --- Campagne ---


def flottes_testees() -> list[tuple[str, ...]]:
    seuls = [(id_ennemi,) for id_ennemi in ENNEMIS_STANDARD]
    paires = list(itertools.combinations_with_replacement(ENNEMIS_STANDARD, 2))
    return seuls + paires + [(ID_BOSS,)]


def taches(graines: int, robustesse: int, graine_depart: int) -> list[tuple]:
    resultat = []
    flottes = flottes_testees()
    for flotte in flottes:
        for variante in ("depart", "etoffe"):
            for k in range(graines):
                resultat.append((variante, flotte, graine_depart + k, "recherche", "equilibre"))
    # Validation du bot : memes combats joues par le bot aleatoire (plancher)
    for flotte in flottes:
        for k in range(min(2, graines)):
            resultat.append(("depart", flotte, graine_depart + k, "aleatoire", "validation"))
    # Robustesse : bot aleatoire, beaucoup de combats varies
    for k in range(robustesse):
        flotte = flottes[k % len(flottes)]
        variante = ("depart", "etoffe")[k % 2]
        resultat.append((variante, flotte, graine_depart + 10_000 + k, "aleatoire", "robustesse"))
    return resultat


def lancer(graines: int, robustesse: int, enchainements: int, graine_depart: int) -> tuple[list[dict], list[dict]]:
    liste = taches(graines, robustesse, graine_depart)
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executeur:
        combats = list(executeur.map(simuler, *zip(*liste), chunksize=4))
        graines_enchainement = [graine_depart + 20_000 + k for k in range(enchainements)]
        parties = list(executeur.map(simuler_enchainement, graines_enchainement))
    return combats, parties


# --- Rapport (tableaux Markdown) ---


NOMS = {
    "ENM_PAT_LE_PIRATE": "Pat", "ENM_LE_NETTOYEUR": "Nettoyeur", "ENM_PETIT_JEAN": "Petit Jean",
    "ENM_LE_PUZZLE": "Puzzle", "ENM_MIROIR": "Miroir", "ENM_BOSS_PIRATES": "Boss",
}


def _pct(n: int, total: int) -> str:
    return f"{100 * n / total:.0f} %" if total else "-"


def _moy(valeurs) -> str:
    valeurs = [v for v in valeurs if v is not None]
    return f"{statistics.mean(valeurs):.1f}" if valeurs else "-"


def tableau_robustesse(resultats: list[dict]) -> str:
    lignes = ["| Étude | Combats | Exceptions | Combats avec violation | Violations distinctes |", "|---|---|---|---|---|"]
    for etude in ("robustesse", "validation", "equilibre", "enchainement"):
        groupe = [r for r in resultats if r["etude"] == etude]
        exceptions = sum("exception" in r for r in groupe)
        avec = sum(bool(r.get("violations")) for r in groupe)
        distinctes = sorted({v for r in groupe for v in r.get("violations", [])})
        lignes.append(f"| {etude} | {len(groupe)} | {exceptions} | {avec} | {'; '.join(distinctes) or '-'} |")
    texte = "\n".join(lignes) + "\n"
    exemples = [r["exception"] for r in resultats if "exception" in r][:3]
    if exemples:
        texte += "\nExemples d'exceptions :\n\n" + "\n".join(f"```\n{e}```" for e in exemples) + "\n"
    return texte


def tableau_validation(resultats: list[dict]) -> str:
    paires = defaultdict(dict)
    for r in resultats:
        if r["variante"] == "depart" and r["graine"] < resultats[0]["graine"] + 2 and "exception" not in r:
            if r["etude"] in ("validation", "equilibre"):
                paires[(tuple(r["ennemis"]), r["graine"])][r["bot"]] = r
    communs = [p for p in paires.values() if len(p) == 2]
    lignes = ["| Bot | Combats | Victoires | Enlisés | Tours | PV principal perdus |", "|---|---|---|---|---|---|"]
    for bot in ("recherche", "aleatoire"):
        groupe = [p[bot] for p in communs]
        lignes.append(
            f"| {bot} | {len(groupe)} | {_pct(sum(r['victoire'] for r in groupe), len(groupe))} | "
            f"{_pct(sum(r['enlise'] for r in groupe), len(groupe))} | {_moy(r['tours'] for r in groupe)} | "
            f"{_moy(r['pv_principal_perdus'] for r in groupe)} |"
        )
    return "\n".join(lignes) + "\n"


def tableau_flottes(resultats: list[dict]) -> str:
    lignes = [
        "| Flotte | Deck | Combats | Victoires | Défaites | Enlisés | Tours | PV principal perdus (moy / max) | Lanceur détruit | Renvoi subi |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    groupes = defaultdict(list)
    for r in resultats:
        if r["etude"] == "equilibre" and "exception" not in r:
            groupes[(tuple(r["ennemis"]), r["variante"])].append(r)
    for flotte in flottes_testees():
        for variante in ("depart", "etoffe"):
            groupe = groupes.get((flotte, variante), [])
            if not groupe:
                continue
            n = len(groupe)
            pertes = [r["pv_principal_perdus"] for r in groupe]
            lignes.append(
                f"| {' + '.join(NOMS[e] for e in flotte)} | {variante} | {n} | {_pct(sum(r['victoire'] for r in groupe), n)} | "
                f"{_pct(sum(r['defaite'] for r in groupe), n)} | {_pct(sum(r['enlise'] for r in groupe), n)} | "
                f"{_moy(r['tours'] for r in groupe)} | {_moy(pertes)} / {max(pertes)} | "
                f"{_pct(sum(r['secondaires_detruits'] > 0 for r in groupe), n)} | {_moy(r['renvoi_subi'] for r in groupe)} |"
            )
    return "\n".join(lignes) + "\n"


def tableau_cartes(resultats: list[dict]) -> str:
    jouees, vues = Counter(), Counter()
    for r in resultats:
        if r["etude"] == "equilibre" and "exception" not in r:
            jouees.update(r["cartes_jouees"])
            vues.update(r["cartes_vues"])
    noms = {id_carte: carte.nom for id_carte, carte in charger_cartes_new().items()}
    lignes = ["| Carte | Vue en main | Jouée | Taux de jeu |", "|---|---|---|---|"]
    for id_carte in sorted(vues, key=lambda i: jouees[i] / vues[i], reverse=True):
        lignes.append(f"| {noms[id_carte]} ({id_carte}) | {vues[id_carte]} | {jouees[id_carte]} | {_pct(jouees[id_carte], vues[id_carte])} |")
    return "\n".join(lignes) + "\n"


def tableau_mesures(resultats: list[dict]) -> str:
    groupe = [r for r in resultats if r["etude"] == "equilibre" and "exception" not in r]
    detruit = [r["tour_destruction_lanceur"] for r in groupe if r["tour_destruction_lanceur"]]
    lignes = ["| Mesure | Valeur |", "|---|---|"]
    lignes.append(f"| Combats (bot de recherche) | {len(groupe)} |")
    lignes.append(f"| Lanceur détruit | {_pct(len(detruit), len(groupe))} des combats, au tour {_moy(detruit)} en moyenne |")
    lignes.append(f"| Cartes en Hors service à la fin (si lanceur détruit) | {_moy(r['cartes_hors_service'] for r in groupe if r['tour_destruction_lanceur'])} |")
    lignes.append(f"| Dégâts absorbés par le bouclier des modules / combat | {_moy(r['absorbe_bouclier_modules'] for r in groupe)} |")
    lignes.append(f"| Dégâts d'incendie infligés / combat | {_moy(r['degats_incendie'] for r in groupe)} |")
    return "\n".join(lignes) + "\n"


def main() -> None:
    arguments = argparse.ArgumentParser(description="Simulations de combats isoles (CombatNew)")
    arguments.add_argument("--graines", type=int, default=10, help="combats par flotte et par deck (bot de recherche)")
    arguments.add_argument("--robustesse", type=int, default=600, help="combats du bot aleatoire pour la robustesse")
    arguments.add_argument("--enchainements", type=int, default=200, help="parties approximees (niveaux 2 a 10)")
    arguments.add_argument("--graine", type=int, default=1)
    options = arguments.parse_args()

    debut = time.time()
    resultats, enchainements = lancer(options.graines, options.robustesse, options.enchainements, options.graine)
    duree = round(time.time() - debut, 1)
    DOSSIER_RESULTATS.mkdir(exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H%M")
    (DOSSIER_RESULTATS / f"{horodatage}_combats_new.json").write_text(
        json.dumps({"combats": resultats, "enchainements": enchainements, "parametres": vars(options)}, default=str)
    )
    sections = [
        ("Robustesse", tableau_robustesse(resultats + enchainements)),
        ("Validation du bot", tableau_validation(resultats)),
        ("Flottes", tableau_flottes(resultats)),
        ("Mesures", tableau_mesures(resultats)),
        ("Cartes", tableau_cartes(resultats)),
        ("Enchaînement des niveaux 2 à 10", tableau_enchainement(enchainements)),
    ]
    texte = "".join(f"## {titre}\n\n{tableau}\n" for titre, tableau in sections)
    texte += f"{len(resultats)} combats isolés et {len(enchainements)} enchaînements en {duree} s.\n"
    (DOSSIER_RESULTATS / f"{horodatage}_combats_new.md").write_text(texte)
    print(texte)


if __name__ == "__main__":
    main()
