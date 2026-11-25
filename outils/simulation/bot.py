"""
Joueurs automatiques pour le combat de la refonte (Combat, specs.md 3) : meme
principe que bot.py (bot "recherche" en faisceau et bot aleatoire de reference, specs/simulation.md
3), adapte a l'API de Combat. Ils ne font que choisir des cartes et des cases ; toutes les
regles sont appliquees par src/gameplay (Combat.jouer_carte, finir_tour).
"""

import copy
import random
from collections import Counter

from src.gameplay.carte import Carte, CibleCarte, NatureEffet, PorteeEffet
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.deck import CARTES_PIOCHEES_PAR_TOUR
from src.gameplay.position import Ligne
from src.gameplay.statut import Statut

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
# Surcharge du principal : degats en plus a venir, comptes comme des PV ennemis en moins.
# Estimation : COUPS_PAR_TOUR_ESTIMES coups par tour, et une Surcharge S qui baisse de 1 par tour
# rapporte S + (S-1) + ... + 1 tours de bonus ; figee, S par tour jusqu'a la fin estimee du combat
COUPS_PAR_TOUR_ESTIMES = 2
# Verrouillage d'un ennemi : degats en plus a venir sur lui seul. Estimation : un coup de carte par
# tour sur cet ennemi, et un Verrouillage V qui baisse de 1 par tour rapporte V + (V-1) + ... + 1,
# plafonne par ses PV (comme l'incendie)
COUPS_PAR_TOUR_SUR_UN_ENNEMI = 1

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
    # Le renvoi protege comme un bouclier ; les degats rendus a l'attaquant ne sont pas comptes
    # (estimation prudente), et il ne sert que sur les modules attaques (RENVOI_MODULES_ATTAQUES)
    NatureEffet.RENVOI: 1.0,
    NatureEffet.REPARATION: 1.0,
    NatureEffet.GAIN_ELECTRICITE: 5.0,
    NatureEffet.PIOCHE: 5.0,
}
VALEUR_LEURRE = 8.0
# Modules attaques en general dans un tour ennemi : un renvoi pose sur plus de modules n'en protege
# pas davantage (Bouclier miroir)
RENVOI_MODULES_ATTAQUES = 2


def copie_sans_journal(combat: Combat) -> Combat:
    """Copie profonde du combat sans son journal (qui grossit a chaque tour et n'est pas utile a
    la recherche)."""
    journal, combat.journal = combat.journal, []
    try:
        return copy.deepcopy(combat)
    finally:
        combat.journal = journal


def actions_possibles(combat: Combat) -> list[tuple[int, object]]:
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
            if carte.cible in (CibleCarte.ENNEMI_UNIQUE, CibleCarte.MODULE_UNIQUE):
                entite = combat.flotte.ennemi_en(case) if carte.cible == CibleCarte.ENNEMI_UNIQUE else combat.vaisseau.module_en(case)
                coup = id(entite)
            elif carte.cible == CibleCarte.ENNEMI_LIGNE:
                coup = case.ligne
            else:
                coup = None
            if coup not in coups:
                coups.add(coup)
                actions.append((index, case))
    return actions


def jouer(combat: Combat, action: tuple[int, object]) -> str:
    """Joue une action ; renvoie l'id de la carte jouee."""
    index, case = action
    carte = combat.deck.main[index]
    combat.jouer_carte(carte, case)
    return carte.id


def evaluer(combat: Combat) -> float:
    """Note d'un etat (plus haut = meilleur pour le joueur)."""
    principal = combat.vaisseau.principal
    if combat.etat == EtatCombat.VICTOIRE:
        return 1e6 + principal.pv_combat
    if combat.etat == EtatCombat.DEFAITE:
        return -1e6
    score = 0.0
    for module in combat.vaisseau.modules:
        poids = POIDS_PV_PRINCIPAL if module.principal else POIDS_PV_SECONDAIRE
        score += poids * module.pv_combat
        if not module.est_detruit():
            score += POIDS_BOUCLIER * module.statuts[Statut.BOUCLIER] + POIDS_LEURRE * module.statuts[Statut.LEURRE]
            if not module.principal:
                score += BONUS_SECONDAIRE_VIVANT
    statuts = combat.vaisseau.principal.statuts
    score += POIDS_PV_ENNEMI * degats_a_venir_de_la_surcharge(
        combat, statuts[Statut.SURCHARGE], Statut.SURCHARGE in statuts.figes,
    )
    for ennemi in combat.flotte.ennemis_vivants():
        incendie = ennemi.statuts[Statut.INCENDIE]
        degats_a_venir = min(ennemi.pv, incendie * (incendie + 1) // 2)
        score -= POIDS_PV_ENNEMI * (ennemi.pv + ennemi.statuts[Statut.BOUCLIER] - POIDS_INCENDIE * degats_a_venir)
        score += POIDS_PV_ENNEMI * degats_a_venir_du_verrouillage(ennemi, ennemi.statuts[Statut.VERROUILLAGE])
        score -= MALUS_ENNEMI_VIVANT
    if VALEUR_DECK:
        score += valeur_des_lancements_en_plus(combat)
    return score


def degats_a_venir_de_la_surcharge(combat: Combat, surcharge: int, figee: bool) -> float:
    """Degats en plus qu'apporterait une Surcharge du principal (estimation), plafonnes par les PV
    des ennemis vivants, comme l'incendie : sinon le bot empilerait la Surcharge au lieu de finir
    les ennemis."""
    if figee:
        tours = max(1, DUREE_COMBAT_ESTIMEE - combat.tour)
        degats = COUPS_PAR_TOUR_ESTIMES * surcharge * tours
    else:
        degats = COUPS_PAR_TOUR_ESTIMES * surcharge * (surcharge + 1) / 2
    return min(degats, sum(ennemi.pv for ennemi in combat.flotte.ennemis_vivants()))


def degats_a_venir_du_verrouillage(ennemi, verrouillage: int) -> float:
    """Degats en plus qu'apporterait un Verrouillage sur cet ennemi (estimation), plafonnes par
    ses PV."""
    return min(ennemi.pv, COUPS_PAR_TOUR_SUR_UN_ENNEMI * verrouillage * (verrouillage + 1) / 2)


def _gain_de_verrouillage(combat: Combat, valeur: int) -> float:
    """Degats a venir en plus apres la pose d'un Verrouillage `valeur` sur un ennemi, a partir de
    son Verrouillage deja en place ; l'ennemi le plus interessant (le meilleur gain) est retenu."""
    gains = [
        degats_a_venir_du_verrouillage(ennemi, ennemi.statuts[Statut.VERROUILLAGE] + valeur)
        - degats_a_venir_du_verrouillage(ennemi, ennemi.statuts[Statut.VERROUILLAGE])
        for ennemi in combat.flotte.ennemis_vivants()
    ]
    return max(gains, default=0.0)


def _gain_de_surcharge(combat: Combat, effet, valeur: int | None) -> float:
    """Degats a venir en plus apres un effet de Surcharge (pose, multiplication, gel), a partir de
    la Surcharge deja en place."""
    statuts = combat.vaisseau.principal.statuts
    avant, figee = statuts[Statut.SURCHARGE], Statut.SURCHARGE in statuts.figes
    apres, figee_apres = avant, figee
    if effet.nature == NatureEffet.SURCHARGE:
        apres = avant + valeur
    elif effet.nature == NatureEffet.MULTIPLIER_SURCHARGE:
        apres = avant * valeur
    elif effet.nature == NatureEffet.FIGER_SURCHARGE:
        figee_apres = True
    return (
        degats_a_venir_de_la_surcharge(combat, apres, figee_apres)
        - degats_a_venir_de_la_surcharge(combat, avant, figee)
    )


def _nombre_de_cibles(carte: Carte, effet, combat: Combat) -> int:
    """Entites touchees par un effet : tous les ennemis, les autres, ceux d'une ligne (la plus
    peuplee pour une carte Ennemi Ligne, le joueur choisissant la meilleure), tous les modules
    vivants ou ceux de la ligne avant, sinon une seule."""
    flotte = combat.flotte
    vivants = len(flotte.ennemis_vivants())
    par_ligne = {ligne: len(flotte.ennemis_vivants_de_ligne(ligne)) for ligne in Ligne}
    if effet.portee == PorteeEffet.AUTRES_ENNEMIS:
        return vivants - 1
    # Un seul module ou un seul ennemi (l'autre de la colonne, s'il y en a un : estime a 1)
    if effet.portee in (PorteeEffet.MODULE_PRINCIPAL, PorteeEffet.MODULE_DE_LA_CARTE, PorteeEffet.MEME_COLONNE):
        return 1
    if effet.portee == PorteeEffet.LIGNE_AVANT_ENNEMIE:
        return par_ligne[Ligne.AVANT]
    if effet.portee == PorteeEffet.LIGNE_ARRIERE_ENNEMIE:
        return par_ligne[Ligne.ARRIERE]
    if carte.cible == CibleCarte.ENNEMI_TOUS:
        return vivants
    if carte.cible == CibleCarte.MODULE_TOUS:
        return len(combat.vaisseau.modules_vivants())
    if carte.cible == CibleCarte.MODULE_AVANT:
        return len(combat.vaisseau.modules_vivants_de_ligne(Ligne.AVANT))
    if carte.cible == CibleCarte.ENNEMI_LIGNE:
        return max(par_ligne.values())
    if carte.cible in (CibleCarte.ENNEMI_AVANT, CibleCarte.ENNEMI_ARRIERE):
        return par_ligne[Ligne.AVANT if carte.cible == CibleCarte.ENNEMI_AVANT else Ligne.ARRIERE]
    return 1


def valeur_d_un_lancement(carte: Carte, combat: Combat) -> float:
    """Valeur estimee d'un lancement de la carte : somme de ses effets, chacun multiplie par le
    nombre d'ennemis qu'il touche (_nombre_de_cibles)."""
    valeur = 0.0
    for effet in carte.effets:
        if effet.nature == NatureEffet.ANNULATION_PROCHAINE_ATTAQUE:
            valeur += VALEUR_LEURRE
            continue
        if effet.nature == NatureEffet.RETRAIT_BOUCLIER:
            # Vaut des degats, mais seulement a hauteur du bouclier que porte un ennemi
            boucliers = [ennemi.statuts[Statut.BOUCLIER] for ennemi in combat.flotte.ennemis_vivants()]
            valeur += POIDS_PV_ENNEMI * min(carte.valeur_de(effet), max(boucliers, default=0))
            continue
        if effet.nature in (NatureEffet.SURCHARGE, NatureEffet.MULTIPLIER_SURCHARGE, NatureEffet.FIGER_SURCHARGE):
            # Meme estimation que l'evaluation, a partir de la Surcharge deja en place
            valeur += POIDS_PV_ENNEMI * _gain_de_surcharge(combat, effet, carte.valeur_de(effet))
            continue
        if effet.nature == NatureEffet.VERROUILLAGE:
            # Meme estimation que l'evaluation, sur chaque ennemi touche
            gain = _gain_de_verrouillage(combat, carte.valeur_de(effet))
            valeur += POIDS_PV_ENNEMI * gain * max(0, _nombre_de_cibles(carte, effet, combat))
            continue
        if effet.nature == NatureEffet.DEGATS and effet.bonus is not None:
            # Bonus calcule : lu sur l'etat actuel (Surcharge ou bouclier du principal, ou le plus
            # fort Verrouillage d'un ennemi vivant pour un bonus lu sur la cible)
            statut = effet.bonus.par.statut
            if effet.bonus.par.sur_la_cible:
                compteur = max((e.statuts[statut] for e in combat.flotte.ennemis_vivants()), default=0)
            else:
                compteur = combat.vaisseau.principal.statuts[statut]
            bonus = carte.valeurs_actuelles[effet.bonus.facteur] * compteur
            valeur += POIDS_PV_ENNEMI * (carte.valeur_de(effet) + bonus) * max(0, _nombre_de_cibles(carte, effet, combat))
            continue
        if effet.nature == NatureEffet.RENVOI:
            cibles = min(RENVOI_MODULES_ATTAQUES, _nombre_de_cibles(carte, effet, combat))
            valeur += VALEUR_PAR_NATURE[NatureEffet.RENVOI] * carte.valeur_de(effet) * cibles
            continue
        par_point = VALEUR_PAR_NATURE.get(effet.nature, 0.0)
        valeur += par_point * (carte.valeur_de(effet) or 0) * max(0, _nombre_de_cibles(carte, effet, combat))
    return valeur


def valeur_des_lancements_en_plus(combat: Combat) -> float:
    """Ce que rapporteront, d'ici la fin du combat, les lancements en plus des cartes encore
    jouables (pioche, main, defausse) : lancements en plus x valeur d'un lancement x nombre de
    fois ou la carte sera encore jouee (tours restants estimes x chance de la piocher)."""
    deck = combat.deck
    actives = deck.pioche + deck.main + deck.defausse
    if not actives:
        return 0.0
    tours_restants = max(1, DUREE_COMBAT_ESTIMEE - combat.tour)
    jeux_par_carte = tours_restants * min(1.0, CARTES_PIOCHEES_PAR_TOUR / len(actives)) * TAUX_DE_JEU_ESTIME
    return sum(
        (carte.lancements_actuels - carte.lancements_base) * valeur_d_un_lancement(carte, combat) * jeux_par_carte
        for carte in actives
        if carte.lancements_actuels > carte.lancements_base
    )


class BotRecherche:
    """Essaie les sequences de cartes du tour sur des copies du combat, laisse les ennemis repondre
    et garde la meilleure (recherche en faisceau, specs/simulation.md 3.1)."""

    def __init__(self, aleatoire: random.Random):
        # Donne un nouveau generateur a chaque copie evaluee (3.3) : le bot ne doit pas connaitre a
        # l'avance le resultat des tirages du vrai combat (cibles au hasard, melanges du deck)
        self.aleatoire = aleatoire

    def _copie_reensemencee(self, etat: Combat) -> Combat:
        copie = copie_sans_journal(etat)
        copie.remplacer_aleatoire(random.Random(self.aleatoire.random()))
        return copie

    def _note_apres_reponse_ennemie(self, etat: Combat) -> float:
        if etat.etat != EtatCombat.EN_COURS:
            return evaluer(etat)
        copie = self._copie_reensemencee(etat)
        copie.finir_tour()
        return evaluer(copie)

    def choisir_sequence(self, combat: Combat) -> list[tuple[int, object]]:
        # Racine reensemencee : les copies de la recherche en heritent (une carte de pioche jouee
        # pendant la recherche ne remelange pas comme dans le vrai combat)
        racine = self._copie_reensemencee(combat)
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

    def jouer_tour(self, combat: Combat, cartes_jouees: Counter, controle=None) -> None:
        """Joue la meilleure sequence. Apres une carte qui pioche, la main reelle differe de celle
        de la recherche (tirages reensemences) : on recalcule la suite depuis l'etat reel."""
        while combat.etat == EtatCombat.EN_COURS:
            sequence = self.choisir_sequence(combat)
            if not sequence:
                return
            for action in sequence:
                carte = combat.deck.main[action[0]]
                cartes_jouees[jouer(combat, action)] += 1
                if controle:
                    controle.apres_action(combat)
                if any(effet.nature == NatureEffet.PIOCHE for effet in carte.effets):
                    break
            else:
                return


class BotAleatoire:
    """Joue des cartes jouables au hasard sur des cases valides au hasard (plancher, 3.4)."""

    def __init__(self, aleatoire: random.Random):
        self.aleatoire = aleatoire

    def jouer_tour(self, combat: Combat, cartes_jouees: Counter, controle=None) -> None:
        while combat.etat == EtatCombat.EN_COURS:
            actions = actions_possibles(combat)
            if not actions:
                return
            cartes_jouees[jouer(combat, self.aleatoire.choice(actions))] += 1
            if controle:
                controle.apres_action(combat)


def jouer_combat(combat: Combat, bot, controle=None) -> dict:
    """Joue un combat jusqu'au bout (ou TOURS_MAX tours). `controle` (optionnel) est appele
    apres chaque carte jouee (apres_action), avant et apres chaque fin de tour (avant_fin_de_tour,
    apres_action) : verification des invariants. Renvoie ses statistiques."""
    cartes_jouees, cartes_vues = Counter(), Counter()
    principal = combat.vaisseau.principal
    pv_depart = principal.pv_combat
    tours = 0
    while combat.etat == EtatCombat.EN_COURS and tours < TOURS_MAX:
        tours += 1
        cartes_vues.update(carte.id for carte in combat.deck.main)
        bot.jouer_tour(combat, cartes_jouees, controle)
        if combat.etat == EtatCombat.EN_COURS:
            if controle:
                controle.avant_fin_de_tour(combat)
            combat.finir_tour()
            if controle:
                controle.apres_action(combat)
    secondaires = [module for module in combat.vaisseau.modules if not module.principal]
    return {
        "victoire": combat.etat == EtatCombat.VICTOIRE,
        "defaite": combat.etat == EtatCombat.DEFAITE,
        "enlise": combat.etat == EtatCombat.EN_COURS,
        "tours": tours,
        "pv_principal_perdus": pv_depart - principal.pv_combat,
        "secondaires_detruits": sum(module.est_detruit() for module in secondaires),
        "cartes_jouees": dict(cartes_jouees),
        "cartes_vues": dict(cartes_vues),
    }
