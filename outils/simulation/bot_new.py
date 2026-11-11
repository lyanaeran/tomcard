"""
Joueurs automatiques pour le combat de la refonte (CombatNew, specs/refonte-combat.md) : meme
principe que bot.py (bot "recherche" en faisceau et bot aleatoire de reference, specs/simulation.md
3), adapte a l'API de CombatNew. Ils ne font que choisir des cartes et des cases ; toutes les
regles sont appliquees par src/gameplay (CombatNew.jouer_carte, finir_tour).
"""

import copy
import random
from collections import Counter

from src.gameplay.carte_new import CarteNew, CibleCarteNew, NatureEffet, PorteeEffet
from src.gameplay.combat_new import CombatNew, EtatCombatNew
from src.gameplay.statut_new import Statut

# Memes garde-fous que bot.py
LARGEUR_FAISCEAU = 6
PROFONDEUR_MAX = 6
TOURS_MAX = 40

# Poids de l'evaluation (repris de bot.py, specs/simulation.md 3.2)
POIDS_PV_PRINCIPAL = 2.0
POIDS_PV_SECONDAIRE = 1.0
BONUS_SECONDAIRE_VIVANT = 12.0
POIDS_PV_ENNEMI = 2.5
MALUS_ENNEMI_VIVANT = 40.0
POIDS_BOUCLIER = 0.5
POIDS_LEURRE = 3.0
# Incendie restant : degats encore a venir (k + k-1 + ... + 1), comptes comme des PV ennemis
# en moins, la recherche ne voyant que le tour suivant
POIDS_INCENDIE = 1.0

# Valeur du deck (idee utilisateur, 2026-11-11) : une carte de repetition ne paie que sur les tours
# suivants, que la recherche ne voit pas. On estime donc ce que rapportent les lancements en plus
# des cartes du combat : valeur d'un lancement x nombre de fois ou la carte sera encore jouee. Plus
# le combat est jeune, plus il reste de tours, plus l'amelioration vaut. Les tours restants sont
# estimes d'apres le numero du tour, jamais d'apres les PV ennemis : sinon le bot gagnerait des
# points a ne pas frapper (combats enlises constates lors d'un premier essai).
VALEUR_DECK = True
DUREE_COMBAT_ESTIMEE = 10  # tours (combats a deux ennemis : 5 a 15 tours en simulation)
TAUX_DE_JEU_ESTIME = 0.7  # part des cartes piochees qui sont jouees
# Valeur d'un point d'effet, en unites de la note (PV ennemis : POIDS_PV_ENNEMI)
VALEUR_PAR_NATURE = {
    NatureEffet.DEGATS: POIDS_PV_ENNEMI,
    NatureEffet.INCENDIE: 2 * POIDS_PV_ENNEMI,  # l'incendie frappe plusieurs tours
    NatureEffet.BOUCLIER: 1.0,
    NatureEffet.REPARATION: 1.0,
    NatureEffet.GAIN_ELECTRICITE: 5.0,
    NatureEffet.PIOCHE: 5.0,
}
VALEUR_LEURRE = 8.0


def copie_sans_journal(combat: CombatNew) -> CombatNew:
    """Copie profonde du combat sans son journal (qui grossit a chaque tour et n'est pas utile a
    la recherche)."""
    journal, combat.journal = combat.journal, []
    try:
        return copy.deepcopy(combat)
    finally:
        combat.journal = journal


def actions_possibles(combat: CombatNew) -> list[tuple[int, object]]:
    """(index de carte en main, case) jouables. Une carte presente en plusieurs exemplaires
    identiques n'est essayee qu'une fois ; deux cases qui donnent le meme coup (deux cases du
    principal, ou n'importe quelle case pour une cible Tous) aussi."""
    actions, deja_vues = [], set()
    for index, carte in enumerate(combat.deck.main):
        cle_carte = (carte.id, carte.munitions_restantes, carte.lancements_actuels, carte.exemplaire_module)
        if cle_carte in deja_vues or not combat.peut_jouer(carte):
            continue
        deja_vues.add(cle_carte)
        coups = set()
        for case in combat.cibles_possibles(carte):
            if carte.cible in (CibleCarteNew.ENNEMI_UNIQUE, CibleCarteNew.MODULE_UNIQUE):
                entite = combat.flotte.ennemi_en(case) if carte.cible == CibleCarteNew.ENNEMI_UNIQUE else combat.vaisseau.module_en(case)
                coup = id(entite)
            elif carte.cible == CibleCarteNew.ENNEMI_COLONNE:
                coup = case.colonne
            else:
                coup = None
            if coup not in coups:
                coups.add(coup)
                actions.append((index, case))
    return actions


def jouer(combat: CombatNew, action: tuple[int, object]) -> str:
    """Joue une action ; renvoie l'id de la carte jouee."""
    index, case = action
    carte = combat.deck.main[index]
    combat.jouer_carte(carte, case)
    return carte.id


def evaluer(combat: CombatNew) -> float:
    """Note d'un etat (plus haut = meilleur pour le joueur)."""
    principal = combat.vaisseau.principal
    if combat.etat == EtatCombatNew.VICTOIRE:
        return 1e6 + principal.pv_combat
    if combat.etat == EtatCombatNew.DEFAITE:
        return -1e6
    score = 0.0
    for module in combat.vaisseau.modules:
        poids = POIDS_PV_PRINCIPAL if module.principal else POIDS_PV_SECONDAIRE
        score += poids * module.pv_combat
        if not module.est_detruit():
            score += POIDS_BOUCLIER * module.statuts[Statut.BOUCLIER] + POIDS_LEURRE * module.statuts[Statut.LEURRE]
            if not module.principal:
                score += BONUS_SECONDAIRE_VIVANT
    for ennemi in combat.flotte.ennemis_vivants():
        incendie = ennemi.statuts[Statut.INCENDIE]
        degats_a_venir = min(ennemi.pv, incendie * (incendie + 1) // 2)
        score -= POIDS_PV_ENNEMI * (ennemi.pv + ennemi.statuts[Statut.BOUCLIER] - POIDS_INCENDIE * degats_a_venir)
        score -= MALUS_ENNEMI_VIVANT
    if VALEUR_DECK:
        score += valeur_des_lancements_en_plus(combat)
    return score


def valeur_d_un_lancement(carte: CarteNew, ennemis_vivants: int) -> float:
    """Valeur estimee d'un lancement de la carte : somme de ses effets ; un effet sur tous les
    ennemis (ou les autres) compte pour chaque ennemi vivant."""
    valeur = 0.0
    for effet in carte.effets:
        if effet.nature == NatureEffet.ANNULATION_PROCHAINE_ATTAQUE:
            valeur += VALEUR_LEURRE
            continue
        par_point = VALEUR_PAR_NATURE.get(effet.nature, 0.0)
        cibles = 1
        if carte.cible in (CibleCarteNew.ENNEMI_TOUS, CibleCarteNew.ENNEMI_COLONNE) or effet.portee != PorteeEffet.CIBLE:
            cibles = max(1, ennemis_vivants - (effet.portee == PorteeEffet.AUTRES_ENNEMIS))
        valeur += par_point * (carte.valeur_de(effet) or 0) * cibles
    return valeur


def valeur_des_lancements_en_plus(combat: CombatNew) -> float:
    """Ce que rapporteront, d'ici la fin du combat, les lancements en plus des cartes encore
    jouables (pioche, main, defausse) : lancements en plus x valeur d'un lancement x nombre de
    fois ou la carte sera encore jouee (tours restants estimes x chance de la piocher)."""
    deck = combat.deck
    actives = deck.pioche + deck.main + deck.defausse
    if not actives:
        return 0.0
    ennemis = combat.flotte.ennemis_vivants()
    tours_restants = max(1, DUREE_COMBAT_ESTIMEE - combat.tour)
    jeux_par_carte = tours_restants * min(1.0, 5 / len(actives)) * TAUX_DE_JEU_ESTIME
    return sum(
        (carte.lancements_actuels - carte.lancements_base) * valeur_d_un_lancement(carte, len(ennemis)) * jeux_par_carte
        for carte in actives
        if carte.lancements_actuels > carte.lancements_base
    )


class BotRecherche:
    """Essaie les sequences de cartes du tour sur des copies du combat, laisse les ennemis repondre
    et garde la meilleure (recherche en faisceau, specs/simulation.md 3.1)."""

    def __init__(self, aleatoire: random.Random):
        # Donne un nouveau generateur a chaque copie evaluee (3.3) : le bot ne doit pas connaitre a
        # l'avance le resultat des tirages du vrai combat
        self.aleatoire = aleatoire

    def _note_apres_reponse_ennemie(self, etat: CombatNew) -> float:
        if etat.etat != EtatCombatNew.EN_COURS:
            return evaluer(etat)
        copie = copie_sans_journal(etat)
        copie.aleatoire = random.Random(self.aleatoire.random())
        copie.finir_tour()
        return evaluer(copie)

    def choisir_sequence(self, combat: CombatNew) -> list[tuple[int, object]]:
        racine = copie_sans_journal(combat)
        meilleure = ([], self._note_apres_reponse_ennemie(racine))
        faisceau = [(racine, [])]
        for _profondeur in range(PROFONDEUR_MAX):
            suivants = []
            for etat, sequence in faisceau:
                for action in actions_possibles(etat):
                    copie = copie_sans_journal(etat)
                    jouer(copie, action)
                    note = self._note_apres_reponse_ennemie(copie)
                    suivants.append((note, copie, sequence + [action]))
            if not suivants:
                break
            suivants.sort(key=lambda element: element[0], reverse=True)
            if suivants[0][0] > meilleure[1]:
                meilleure = (suivants[0][2], suivants[0][0])
            faisceau = [(copie, sequence) for _note, copie, sequence in suivants[:LARGEUR_FAISCEAU]]
        return meilleure[0]

    def jouer_tour(self, combat: CombatNew, cartes_jouees: Counter, controle=None) -> None:
        for action in self.choisir_sequence(combat):
            cartes_jouees[jouer(combat, action)] += 1
            if controle:
                controle.apres_action(combat)


class BotAleatoire:
    """Joue des cartes jouables au hasard sur des cases valides au hasard (plancher, 3.4)."""

    def __init__(self, aleatoire: random.Random):
        self.aleatoire = aleatoire

    def jouer_tour(self, combat: CombatNew, cartes_jouees: Counter, controle=None) -> None:
        while combat.etat == EtatCombatNew.EN_COURS:
            actions = actions_possibles(combat)
            if not actions:
                return
            cartes_jouees[jouer(combat, self.aleatoire.choice(actions))] += 1
            if controle:
                controle.apres_action(combat)


def jouer_combat(combat: CombatNew, bot, controle=None) -> dict:
    """Joue un combat jusqu'au bout (ou TOURS_MAX tours). `controle` (optionnel) est appele
    apres chaque carte jouee (apres_action), avant et apres chaque fin de tour (avant_fin_de_tour,
    apres_action) : verification des invariants. Renvoie ses statistiques."""
    cartes_jouees, cartes_vues = Counter(), Counter()
    principal = combat.vaisseau.principal
    pv_depart = principal.pv_combat
    tours = 0
    while combat.etat == EtatCombatNew.EN_COURS and tours < TOURS_MAX:
        tours += 1
        cartes_vues.update(carte.id for carte in combat.deck.main)
        bot.jouer_tour(combat, cartes_jouees, controle)
        if combat.etat == EtatCombatNew.EN_COURS:
            if controle:
                controle.avant_fin_de_tour(combat)
            combat.finir_tour()
            if controle:
                controle.apres_action(combat)
    secondaires = [module for module in combat.vaisseau.modules if not module.principal]
    return {
        "victoire": combat.etat == EtatCombatNew.VICTOIRE,
        "defaite": combat.etat == EtatCombatNew.DEFAITE,
        "enlise": combat.etat == EtatCombatNew.EN_COURS,
        "tours": tours,
        "pv_principal_perdus": pv_depart - principal.pv_combat,
        "secondaires_detruits": sum(module.est_detruit() for module in secondaires),
        "cartes_jouees": dict(cartes_jouees),
        "cartes_vues": dict(cartes_vues),
    }
