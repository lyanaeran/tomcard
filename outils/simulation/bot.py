"""
Joueurs automatiques de combat (specs/simulation.md 3) : bot "recherche" et bot aleatoire de
reference. Ils ne font que choisir des cartes et des cibles ; toutes les regles sont appliquees par
src/gameplay (Combat.jouer_carte, finir_tour_joueur).
"""

import copy
import random
from collections import Counter

from src.gameplay.carte import ActionCarte
from src.gameplay.combat import Combat, EtatCombat

# Nombre maximal d'etats gardes a chaque profondeur de la recherche (recherche en faisceau)
LARGEUR_FAISCEAU = 6
# Garde-fou : cartes jouees au maximum dans un meme tour par la recherche
PROFONDEUR_MAX = 6
# Garde-fou : tours au-dela desquels un combat est arrete, compte comme une defaite et signale
# comme "enlise" (ex. Miroir qui accumule du Bouclier miroir, cf. synthese)
TOURS_MAX = 40

# Poids de l'evaluation d'un etat apres la reponse ennemie (cf. specs/simulation.md 3.2), regles
# a la main sur 15 combats : (2, 1, 2.5, 40) gagne 12 combats sur 15, contre 8 pour un bot plus
# defensif (4, 1.5, 1, 15) qui s'enlisait (combats arretes par TOURS_MAX).
POIDS_PV_PRINCIPAL = 2.0
POIDS_PV_SECONDAIRE = 1.0
BONUS_SECONDAIRE_VIVANT = 12.0
POIDS_PV_ENNEMI = 2.5
MALUS_ENNEMI_VIVANT = 40.0
POIDS_BOUCLIER = 0.5
# Effets durables : la recherche ne voit que le tour suivant, ces termes estiment la valeur des
# tours d'apres (sinon les debuffs longs et buffs recurrents ne sont jamais joues)
POIDS_VULNERABILITE = 0.25  # par point de % et par tour restant
POIDS_BOUCLIER_RECURRENT = 1.0  # par point de bouclier et par tour restant
HORIZON_EFFET_PERMANENT = 4  # tours comptes pour un effet sans duree


def reference_cible(combat: Combat, cible) -> tuple | None:
    """Designation stable d'une cible, valable d'une copie du combat a l'autre."""
    if cible is None:
        return None
    if cible is combat.joueur.vaisseau.base:
        return ("base",)
    for position, module in combat.joueur.vaisseau.modules_equipes().items():
        if module is cible:
            return ("module", position)
    for position, ennemi in combat.flotte.positions().items():
        if ennemi is cible:
            return ("ennemi", position)
    raise ValueError("Cible introuvable dans ce combat")


def cible_depuis_reference(combat: Combat, reference: tuple | None):
    if reference is None:
        return None
    if reference[0] == "base":
        return combat.joueur.vaisseau.base
    if reference[0] == "module":
        return combat.joueur.vaisseau.modules_equipes()[reference[1]]
    return combat.flotte.positions()[reference[1]]


def _actions_possibles(combat: Combat) -> list[tuple[int, tuple | None]]:
    """(index de carte en main, reference de cible) jouables ; une seule fois par carte identique."""
    actions, deja_vues = [], set()
    for index, carte in enumerate(combat.joueur.deck.main):
        cle = (carte.id, carte.munitions_restantes)
        if cle in deja_vues or not combat.joueur.peut_jouer(carte):
            continue
        deja_vues.add(cle)
        for cible in combat.cibles_possibles(carte):
            actions.append((index, reference_cible(combat, cible)))
    return actions


def _jouer(combat: Combat, action: tuple[int, tuple | None]) -> bool:
    """Joue une action ; False si la carte n'a pas pu etre jouee."""
    index, reference = action
    carte = combat.joueur.deck.main[index]
    taille_main = len(combat.joueur.deck.main)
    combat.jouer_carte(carte, cible_depuis_reference(combat, reference))
    return len(combat.joueur.deck.main) < taille_main


def evaluer(combat: Combat) -> float:
    """Note d'un etat (plus haut = meilleur pour le joueur)."""
    if combat.etat == EtatCombat.VICTOIRE:
        return 1e6 + combat.joueur.vaisseau.base.pv
    if combat.etat == EtatCombat.DEFAITE:
        return -1e6
    vaisseau = combat.joueur.vaisseau
    score = POIDS_PV_PRINCIPAL * vaisseau.base.pv + POIDS_BOUCLIER * vaisseau.base.bouclier
    for module in vaisseau.modules_equipes().values():
        score += POIDS_PV_SECONDAIRE * module.pv + POIDS_BOUCLIER * module.bouclier
        score += BONUS_SECONDAIRE_VIVANT if not module.est_detruit() else 0.0
    for module in [vaisseau.base, *vaisseau.modules_equipes().values()]:
        if not module.est_detruit():
            score += POIDS_BOUCLIER_RECURRENT * _valeur_durable(module, ActionCarte.BOUCLIER_PAR_TOUR)
    for ennemi in combat.flotte.ennemis_vivants():
        score -= POIDS_PV_ENNEMI * (ennemi.pv + ennemi.bouclier) + MALUS_ENNEMI_VIVANT
        score += POIDS_VULNERABILITE * _valeur_durable(ennemi, ActionCarte.VULNERABILITE)
    return score


def _valeur_durable(entite, action: ActionCarte) -> float:
    """Somme valeur x tours restants des buffs `action` actifs sur l'entite."""
    return sum(
        buff.valeur * (buff.tours_restants if buff.tours_restants is not None else HORIZON_EFFET_PERMANENT)
        for buff in entite.buffs_actifs
        if buff.action == action
    )


class BotRecherche:
    """Essaie les sequences de cartes du tour sur des copies du combat, laisse les ennemis repondre
    et garde la meilleure (recherche en faisceau, specs/simulation.md 3.1)."""

    def __init__(self, aleatoire: random.Random):
        # Sert uniquement a donner un nouveau generateur a chaque copie evaluee (3.3) : le bot ne
        # doit pas connaitre a l'avance le resultat des tirages du vrai combat.
        self.aleatoire = aleatoire

    def _note_apres_reponse_ennemie(self, etat: Combat) -> float:
        if etat.etat != EtatCombat.EN_COURS:
            return evaluer(etat)
        copie = copy.deepcopy(etat)
        copie.aleatoire = random.Random(self.aleatoire.random())
        copie.finir_tour_joueur()
        return evaluer(copie)

    def choisir_sequence(self, combat: Combat) -> list[tuple[int, tuple | None]]:
        racine = copy.deepcopy(combat)
        meilleure = ([], self._note_apres_reponse_ennemie(racine))
        faisceau = [(racine, [])]
        for _profondeur in range(PROFONDEUR_MAX):
            suivants = []
            for etat, sequence in faisceau:
                for action in _actions_possibles(etat):
                    copie = copy.deepcopy(etat)
                    if not _jouer(copie, action):
                        continue
                    note = self._note_apres_reponse_ennemie(copie)
                    suivants.append((note, copie, sequence + [action]))
            if not suivants:
                break
            suivants.sort(key=lambda element: element[0], reverse=True)
            if suivants[0][0] > meilleure[1]:
                meilleure = (suivants[0][2], suivants[0][0])
            faisceau = [(copie, sequence) for _note, copie, sequence in suivants[:LARGEUR_FAISCEAU]]
        return meilleure[0]

    def jouer_tour(self, combat: Combat, cartes_jouees: Counter) -> None:
        for action in self.choisir_sequence(combat):
            carte = combat.joueur.deck.main[action[0]]
            if _jouer(combat, action):
                cartes_jouees[carte.id] += 1


class BotAleatoire:
    """Joue des cartes jouables au hasard sur des cibles valides au hasard (plancher, 3.4)."""

    def __init__(self, aleatoire: random.Random):
        self.aleatoire = aleatoire

    def jouer_tour(self, combat: Combat, cartes_jouees: Counter) -> None:
        while combat.etat == EtatCombat.EN_COURS:
            actions = _actions_possibles(combat)
            if not actions:
                return
            action = self.aleatoire.choice(actions)
            carte = combat.joueur.deck.main[action[0]]
            if _jouer(combat, action):
                cartes_jouees[carte.id] += 1


def jouer_combat(combat: Combat, bot) -> dict:
    """Joue un combat jusqu'au bout. Renvoie ses statistiques."""
    cartes_jouees, cartes_vues = Counter(), Counter()
    base = combat.joueur.vaisseau.base
    pv_base_depart = base.pv
    noms_ennemis = [ennemi.nom for ennemi in combat.flotte.ennemis_vivants()]
    tours = 0
    while combat.etat == EtatCombat.EN_COURS and tours < TOURS_MAX:
        tours += 1
        cartes_vues.update(carte.id for carte in combat.joueur.deck.main)
        bot.jouer_tour(combat, cartes_jouees)
        if combat.etat == EtatCombat.EN_COURS:
            combat.finir_tour_joueur()
    secondaires = list(combat.joueur.vaisseau.modules_equipes().values())
    return {
        "victoire": combat.etat == EtatCombat.VICTOIRE,
        "enlise": combat.etat == EtatCombat.EN_COURS,
        "tours": tours,
        "pv_principal_perdus": pv_base_depart - base.pv,
        "secondaires_detruits": sum(module.est_detruit() for module in secondaires),
        "ennemis": noms_ennemis,
        "cartes_jouees": dict(cartes_jouees),
        "cartes_vues": dict(cartes_vues),
    }
