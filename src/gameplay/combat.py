"""
Moteur du combat entre le vaisseau du joueur et une flotte d'ennemis (cf. specs.md paragraphe 8).
"""

import random
from enum import Enum, auto

from src.gameplay.carte import CIBLES_SANS_CLIC, ActionCarte, Carte, CibleCarte, TypeCarte
from src.gameplay.ciblage import module_cible_par_ennemi
from src.gameplay.ennemi import ActionEnnemi, CibleActionEnnemi, Ennemi, TypeActionEnnemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee


class EtatCombat(Enum):
    """Etat courant du combat."""

    EN_COURS = auto()
    VICTOIRE = auto()
    DEFAITE = auto()


def _degats_effectifs(cible: Module | Ennemi, degats: int) -> int:
    """Combien de PV+bouclier une cible va reellement perdre pour ces degats, sans
    depasser ce qu'il lui reste (specs.md paragraphe 3.5 : le bouclier absorbe en premier).
    Un leurre actif (specs.md 12.6) annule totalement l'attaque : 0 degats, quel que soit
    le montant."""
    if getattr(cible, "leurre_actif", False):
        return 0
    return min(degats, cible.pv + getattr(cible, "bouclier", 0))


# Seuil de dissipation naturelle du bouclier (specs.md 3.5) : en dessous ou egal a cette valeur
# apres division, le reste de bouclier disparait entierement plutot que de continuer a decliner
# indefiniment (ceil(1/2) = 1 ne convergerait jamais vers 0 sans ce seuil).
SEUIL_DISSIPATION_BOUCLIER = 5


def _dissiper_bouclier(entite: Module | Ennemi) -> None:
    """Dissipation naturelle du bouclier a chaque tour (specs.md 3.5, meme regle pour un module
    et un ennemi) : divise par deux (arrondi au-dessus), puis completement dissipe si le
    resultat ne depasse pas SEUIL_DISSIPATION_BOUCLIER. Appelee une fois par tour pour chaque
    camp (modules au debut de chaque tour joueur, ennemis au debut de chaque tour ennemi),
    avant que les buffs de ce tour ne reposent eventuellement du bouclier frais par-dessus."""
    moitie = (entite.bouclier + 1) // 2
    entite.bouclier = 0 if moitie <= SEUIL_DISSIPATION_BOUCLIER else moitie


class Combat:
    """Orchestre le deroulement du combat entre le joueur et la flotte ennemie."""

    def __init__(self, joueur: Joueur, flotte: Flotte, aleatoire: random.Random | None = None):
        self.joueur = joueur
        self.flotte = flotte
        self.etat = EtatCombat.EN_COURS
        # Utilise pour le tirage au sort de Tir allie et de la cible du Bouclier miroir
        # (specs.md 12.6/13) - jamais le module random global directement, cf. CLAUDE.md
        # "Determinisme du tirage aleatoire".
        self.aleatoire = aleatoire or random.Random()
        # Numero du tour ennemi ecoule (0 = aucun tour ennemi encore joue), incremente au debut
        # de chaque _tour_ennemi() - determine quelles Actions ennemies se declenchent ce tour
        # (specs.md 13, ActionEnnemi.active_au_tour).
        self.tour_ennemi_actuel = 0
        self.joueur.debut_de_tour()
        self._declencher_buffs_debut_de_tour()

    def jouer_carte(self, carte: Carte, cible: Module | Ennemi | None = None) -> list[tuple[Module | Ennemi, int]]:
        """Applique l'effet d'une carte jouee par le joueur.

        cible est ignoree pour les cartes de CIBLES_SANS_CLIC (elles touchent tout
        un camp) et obligatoire sinon. Renvoie, pour chaque cible effectivement
        touchee, le montant reellement applique (degats/bouclier/soin, qui peut etre
        inferieur a carte.valeur : cf. `_appliquer_effet_simple`) ; liste vide si la
        carte n'a pas ete jouee.
        """
        if self.etat != EtatCombat.EN_COURS:
            return []
        if not self.joueur.peut_jouer(carte):
            return []
        if not self._cible_valide(carte, cible):
            return []
        self.joueur.depenser_electricite(carte.cout)
        self.joueur.deck.jouer(carte)
        cibles_touchees = self._appliquer_effet(carte, cible)
        self._verifier_fin_de_combat()
        return cibles_touchees

    def finir_tour_joueur(self) -> list[tuple[Position, Ennemi, Module | Ennemi, int, str]]:
        """Termine le tour du joueur (defausse la main restante) et enchaine sur le tour ennemi.

        Renvoie la liste des evenements resolus - (position et ennemi a l'origine de l'action,
        cible touchee - un module, un autre ennemi si Tir allie est actif (specs.md 12.6), ou
        l'ennemi lui-meme en cas de renvoi par un Bouclier miroir (specs.md 13) -, montant
        reellement applique, et son type : "degats" ou "bouclier") - pour permettre a l'UI
        d'animer chaque action."""
        if self.etat != EtatCombat.EN_COURS:
            return []
        self.joueur.deck.defausser_main()
        evenements = self._tour_ennemi()
        if self.etat == EtatCombat.EN_COURS:
            self.joueur.debut_de_tour()
            self._declencher_buffs_debut_de_tour()
        return evenements

    def _declencher_buffs_debut_de_tour(self) -> None:
        """Dissipe le bouclier restant de chaque module vivant (specs.md 3.5) puis redeclenche
        l'effet de chaque buff actif et decompte sa duree (specs.md 12.3/12.5) - meme principe
        que decrementer_buffs()/_dissiper_bouclier() cote ennemi, mais au debut de chaque tour
        joueur plutot qu'a chaque tour ennemi. Dissipation avant redeclenchement : un buff
        Bouclier qui se repose ce tour n'est jamais rogne par la dissipation du reste de
        l'ancien bouclier."""
        for module in self._modules_vivants():
            _dissiper_bouclier(module)
            module.declencher_buffs_tour()

    def prochaine_action_active(self, ennemi: Ennemi) -> ActionEnnemi | None:
        """Premiere Action de cet ennemi qui se declenchera a son prochain tour (specs.md 13),
        pour l'affichage de son intention (survol/tap) - None si aucune de ses actions n'est
        active a ce tour-la."""
        prochain_tour = self.tour_ennemi_actuel + 1
        for action in ennemi.actions:
            if action.active_au_tour(prochain_tour):
                return action
        return None

    def previsualiser_cible(self, ennemi: Ennemi) -> Module | None:
        """Renvoie le module que cet ennemi attaquerait a son prochain tour si sa prochaine
        action est une Attaque a cible PROXIMITE (pour le survol UI) - None si sa prochaine
        action n'est pas de ce type, si aucun module n'est a portee, OU si un debuff Tir allie
        est actif (specs.md 12.6) : dans ce cas la cible reelle (un autre ennemi tire au hasard)
        n'est determinee qu'a la resolution du tour (_tour_ennemi/_cible_redirection), jamais
        ici, pour ne pas consommer l'alea a chaque survol/redessin (appele en boucle par l'UI,
        cf. CLAUDE.md determinisme du tirage aleatoire)."""
        action = self.prochaine_action_active(ennemi)
        if action is None or action.type != TypeActionEnnemi.ATTAQUE or action.cible != CibleActionEnnemi.PROXIMITE:
            return None
        position = self._position_de_ennemi(ennemi)
        if position is None or self._redirection_active(ennemi):
            return None
        return module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)

    def _modules_vivants(self) -> list[Module]:
        """Tous les modules du joueur encore en vie (base incluse)."""
        modules = [self.joueur.vaisseau.base, *self.joueur.vaisseau.modules_equipes().values()]
        return [m for m in modules if not m.est_detruit()]

    def _position_de_module(self, module: Module) -> Position | None:
        """Retrouve la position d'un module equipe dans le vaisseau, ou None (base incluse,
        car la base n'a pas de position de colonne/rangee equipee - cf. Vaisseau.module_en)."""
        for position, occupant in self.joueur.vaisseau.modules_equipes().items():
            if occupant is module:
                return position
        return None

    def _cible_valide(self, carte: Carte, cible: Module | Ennemi | None) -> bool:
        """Verifie que la cible correspond au type de carte et est bien vivante dans ce combat."""
        if carte.cible in CIBLES_SANS_CLIC:
            return cible is None
        if carte.cible == CibleCarte.ENNEMI_UNIQUE:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants()
        if carte.cible == CibleCarte.ALLIE_UNIQUE:
            return isinstance(cible, Module) and cible in self._modules_vivants()
        if carte.cible == CibleCarte.LIGNE_ENNEMIE:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants()
        if carte.cible == CibleCarte.COLONNE_AVANT_ENNEMIE:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants() and self._position_de_ennemi(cible).colonne == Colonne.AVANT
        if carte.cible == CibleCarte.COLONNE_ARRIERE_ENNEMIE:
            return isinstance(cible, Ennemi) and cible in self.flotte.ennemis_vivants() and self._position_de_ennemi(cible).colonne == Colonne.ARRIERE
        if carte.cible == CibleCarte.COLONNE_AVANT_ALLIEE:
            if not (isinstance(cible, Module) and cible in self._modules_vivants()):
                return False
            if cible is self.joueur.vaisseau.base:
                return True  # la base occupe la rangee mid, a la fois avant et arriere
            position = self._position_de_module(cible)
            return position is not None and position.colonne == Colonne.AVANT
        return False

    def _appliquer_effet(self, carte: Carte, cible: Module | Ennemi | None) -> list[tuple[Module | Ennemi, int]]:
        """Applique l'effet d'une carte selon sa cible (specs.md 7.1/7.2).

        Renvoie, pour chaque cible effectivement touchee, le montant reellement applique.
        """
        if carte.type == TypeCarte.OUTILS:
            # Une carte Outils ne touche jamais de module/ennemi : sa cible ne sert qu'a
            # valider un clic eventuel (specs.md 12.11), l'effet s'applique une seule fois
            # quel que soit le nombre de modules/ennemis vivants.
            return [(None, self._appliquer_outils(carte))]
        if carte.cible == CibleCarte.ALLIES_MULTIPLES:
            cibles = self._modules_vivants()
        elif carte.cible == CibleCarte.ENNEMIS_MULTIPLES:
            cibles = self.flotte.ennemis_vivants()
        elif carte.cible == CibleCarte.MODULE_PRINCIPAL:
            cibles = [self.joueur.vaisseau.base]
        elif carte.cible == CibleCarte.LIGNE_ENNEMIE:
            position = self._position_de_ennemi(cible)
            occupants = (self.flotte.ennemi_en(colonne, position.rangee) for colonne in (Colonne.AVANT, Colonne.ARRIERE))
            cibles = [occupant for occupant in occupants if occupant is not None]
        elif carte.cible in (CibleCarte.COLONNE_AVANT_ENNEMIE, CibleCarte.COLONNE_ARRIERE_ENNEMIE):
            colonne = Colonne.AVANT if carte.cible == CibleCarte.COLONNE_AVANT_ENNEMIE else Colonne.ARRIERE
            occupants = (self.flotte.ennemi_en(colonne, rangee) for rangee in (Rangee.GAUCHE, Rangee.MID, Rangee.DROITE))
            cibles = [occupant for occupant in occupants if occupant is not None]
        elif carte.cible == CibleCarte.COLONNE_AVANT_ALLIEE:
            # Rangee.MID (la base) est incluse : elle occupe la rangee mid, a la fois avant
            # et arriere (specs.md 12.1), contrairement aux colonnes ennemies ou la base n'a
            # pas d'equivalent.
            occupants = (
                self.joueur.vaisseau.module_en(Colonne.AVANT, rangee) for rangee in (Rangee.GAUCHE, Rangee.MID, Rangee.DROITE)
            )
            cibles = [occupant for occupant in occupants if occupant is not None]
        else:
            cibles = [cible]
        return [(une_cible, self._appliquer_effet_simple(carte, une_cible)) for une_cible in cibles]

    def _appliquer_effet_simple(self, carte: Carte, cible: Module | Ennemi) -> int:
        """Applique l'effet d'une carte a une seule cible, selon son type (specs.md 7.1).

        Renvoie le montant reellement applique, qui peut etre inferieur a carte.valeur :
        les degats sont plafonnes par les PV+bouclier restants de la cible, le soin par
        son PV max (le bouclier, lui, n'est jamais plafonne).
        """
        if carte.type == TypeCarte.ATTAQUE:
            degats_bruts = cible.degats_subis(carte.valeur) if isinstance(cible, Ennemi) else carte.valeur
            valeur_effective = _degats_effectifs(cible, degats_bruts)
            cible.subir_degats(degats_bruts)
        elif carte.type == TypeCarte.DEFENSE:
            if carte.action == ActionCarte.BOUCLIER_POURCENTAGE_PV:
                valeur_effective = round(cible.pv_max * carte.valeur / 100)
                cible.ajouter_bouclier(valeur_effective)
            elif carte.action == ActionCarte.ANNULATION_PROCHAINE_ATTAQUE:
                cible.leurre_actif = True
                valeur_effective = 0
            else:
                valeur_effective = carte.valeur
                cible.ajouter_bouclier(valeur_effective)
        elif carte.type == TypeCarte.DEBUFF:
            valeur_effective = self._appliquer_buff_ou_debuff(carte, cible)
        elif carte.type == TypeCarte.BUFF:
            valeur_effective = self._appliquer_buff_ou_debuff(carte, cible)
        else:
            valeur_effective = min(carte.valeur, cible.pv_max - cible.pv)
            cible.soigner(carte.valeur)
        return valeur_effective

    def _appliquer_buff_ou_debuff(self, carte: Carte, cible: Module | Ennemi) -> int:
        """Applique un buff/debuff d'une carte a une cible (specs.md 12.1/12.3/12.4/12.5/13) :
        meme liste sur Module et Ennemi (BuffActif), la distinction n'est que semantique.
        Independant des buffs deja actifs sur cette cible : s'ajoute a la liste plutot que de
        les remplacer."""
        cible.appliquer_buff(carte.action, carte.valeur, carte.duree)
        return carte.valeur

    def _appliquer_outils(self, carte: Carte) -> int:
        """Applique l'effet d'une carte Outils (specs.md 12.9) : n'affecte pas la cible
        cliquee (celle-ci n'a qu'un role de clic obligatoire, cf. specs.md 12.11), mais
        une ressource commune au joueur (electricite ou pioche)."""
        if carte.action == ActionCarte.GAIN_ELECTRICITE:
            self.joueur.electricite += carte.valeur
            return carte.valeur
        if carte.action == ActionCarte.GAIN_ELECTRICITE_PAR_MODULE:
            gain = carte.valeur * len(self._modules_vivants())
            self.joueur.electricite += gain
            return gain
        if carte.action == ActionCarte.PIOCHE_SUPPLEMENTAIRE:
            self.joueur.deck.piocher_cartes(carte.valeur)
        return carte.valeur

    def _tour_ennemi(self) -> list[tuple[Position, Ennemi, Module | Ennemi, int, str]]:
        """Chaque ennemi vivant execute ses Actions eligibles ce tour (specs.md 13 : frequence/
        tour_depart/repetitions, cf. ActionEnnemi.active_au_tour), dans l'ordre de la grille -
        la colonne Avant de haut en bas (Gauche, Mid, Droite), puis la colonne Arriere de haut
        en bas, ordre garanti par Flotte.positions() (dict construit dans cet ordre par
        creer_flotte(), cf. config_poc.POSITIONS_ENNEMIES) - puis dans l'ordre de sa propre
        liste d'actions. Cet ordre determine notamment quelle attaque est annulee quand un
        Leurre (specs.md 12.6) protege une cible visee par plusieurs actions dans le meme
        tour : seule la premiere resolue sur cette cible est annulee."""
        self.tour_ennemi_actuel += 1
        for ennemi in self.flotte.ennemis_vivants():
            _dissiper_bouclier(ennemi)
        evenements = []
        for position, ennemi in self.flotte.positions().items():
            if ennemi.est_detruit():
                continue
            for action in ennemi.actions:
                if not action.active_au_tour(self.tour_ennemi_actuel):
                    continue
                for _ in range(action.repetitions):
                    evenements.extend(self._executer_action_ennemi(ennemi, position, action))
                    self._verifier_fin_de_combat()
                    if self.etat != EtatCombat.EN_COURS:
                        return evenements
        for ennemi in self.flotte.ennemis_vivants():
            ennemi.decrementer_buffs()
        return evenements

    def _executer_action_ennemi(
        self, ennemi: Ennemi, position: Position, action: ActionEnnemi
    ) -> list[tuple[Position, Ennemi, Module | Ennemi, int, str]]:
        """Execute une occurrence d'une Action ennemie (specs.md 13), selon son type."""
        if action.type == TypeActionEnnemi.ATTAQUE:
            return self._executer_attaque(ennemi, position, action)
        if action.type == TypeActionEnnemi.POSE_BUFF:
            return self._executer_pose_buff(ennemi, position, action)
        return []

    def _executer_attaque(
        self, ennemi: Ennemi, position: Position, action: ActionEnnemi
    ) -> list[tuple[Position, Ennemi, Module | Ennemi, int, str]]:
        """Determine la ou les cibles d'une Action ATTAQUE (specs.md 13) et resout les degats
        sur chacune. PROXIMITE reutilise le ciblage historique (module_cible_par_ennemi), sujet
        a Tir allie (specs.md 12.6) ; TOUS_MODULES_JOUEUR touche tous les modules vivants du
        joueur (attaque de zone, ennemi Le puzzle) - jamais redirigee par Tir allie (l'attaque
        de zone n'a pas de cible individuelle a rediriger)."""
        if action.cible == CibleActionEnnemi.PROXIMITE:
            cible_redirigee = self._cible_redirection(ennemi)
            cible = cible_redirigee or module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)
            cibles = [cible] if cible is not None else []
        elif action.cible == CibleActionEnnemi.TOUS_MODULES_JOUEUR:
            cibles = self._modules_vivants()
        else:
            cibles = []
        degats = ennemi.degats_attaque_effectifs(action.valeur)
        evenements = []
        for cible in cibles:
            evenements.extend(self._resoudre_attaque(ennemi, position, cible, degats))
        return evenements

    def _resoudre_attaque(
        self, attaquant: Ennemi, position: Position, cible: Module | Ennemi, degats: int
    ) -> list[tuple[Position, Ennemi, Module | Ennemi, int, str]]:
        """Applique `degats` a `cible`, en tenant compte d'un Bouclier miroir actif dessus
        (specs.md 13, ennemi Miroir) : jusqu'a sa valeur est renvoyee a `attaquant` (qui subit
        ces degats a la place, la cible ne subit rien pour cette part), le reste s'applique
        normalement a `cible`."""
        reflete = self._consommer_bouclier_miroir(cible, degats)
        evenements = []
        if reflete > 0:
            degats_attaquant = _degats_effectifs(attaquant, reflete)
            attaquant.subir_degats(reflete)
            evenements.append((position, attaquant, attaquant, degats_attaquant, "degats"))
        restant = degats - reflete
        if reflete == 0 or restant > 0:
            degats_cible = _degats_effectifs(cible, restant)
            cible.subir_degats(restant)
            evenements.append((position, attaquant, cible, degats_cible, "degats"))
        return evenements

    def _consommer_bouclier_miroir(self, cible: Module | Ennemi, degats: int) -> int:
        """Combien des `degats` sont renvoyes a l'attaquant a cause d'un Bouclier miroir actif
        sur `cible` (specs.md 13) - consomme les buffs BOUCLIER_MIROIR actifs dans l'ordre de
        pose jusqu'a epuiser les degats ou les buffs disponibles (chaque instance depuis sa
        propre valeur, comme un bouclier classique)."""
        restant = degats
        total_reflete = 0
        for buff in cible.buffs_actifs:
            if buff.action != ActionCarte.BOUCLIER_MIROIR or restant <= 0:
                continue
            consomme = min(buff.valeur, restant)
            buff.valeur -= consomme
            total_reflete += consomme
            restant -= consomme
        cible.buffs_actifs = [
            buff for buff in cible.buffs_actifs if not (buff.action == ActionCarte.BOUCLIER_MIROIR and buff.valeur <= 0)
        ]
        return total_reflete

    def _executer_pose_buff(
        self, ennemi: Ennemi, position: Position, action: ActionEnnemi
    ) -> list[tuple[Position, Ennemi, Module | Ennemi, int, str]]:
        """Pose le buff d'une Action POSE_BUFF (specs.md 13) sur sa cible - SOI_MEME (l'ennemi
        lui-meme, ex. Petit Jean se met du bouclier) ou COLONNE_AVANT_SINON_ARRIERE_JOUEUR (un
        module du joueur tire au hasard, ex. Miroir pose un Bouclier miroir)."""
        if action.cible == CibleActionEnnemi.SOI_MEME:
            cible = ennemi
        elif action.cible == CibleActionEnnemi.COLONNE_AVANT_SINON_ARRIERE_JOUEUR:
            cible = self._cible_ligne_avant_ou_arriere_joueur()
        else:
            cible = None
        if cible is None:
            return []
        cible.appliquer_buff(action.action_buff, action.valeur, action.duree_buff)
        return [(position, ennemi, cible, action.valeur, "bouclier")]

    def _cible_ligne_avant_ou_arriere_joueur(self) -> Module | None:
        """Tire au hasard un module du joueur dans la colonne avant (base incluse, specs.md
        12.1) si elle compte au moins un module vivant, sinon dans la colonne arriere (specs.md
        13, ennemi Miroir) - None si le joueur n'a plus aucun module vivant (combat deja
        termine dans ce cas)."""
        avant = [
            module
            for module in (self.joueur.vaisseau.module_en(Colonne.AVANT, rangee) for rangee in (Rangee.GAUCHE, Rangee.MID, Rangee.DROITE))
            if module is not None
        ]
        candidats = avant or [
            module
            for module in (self.joueur.vaisseau.module_en(Colonne.ARRIERE, rangee) for rangee in (Rangee.GAUCHE, Rangee.MID, Rangee.DROITE))
            if module is not None
        ]
        if not candidats:
            return None
        return self.aleatoire.choice(candidats)

    def _redirection_active(self, ennemi: Ennemi) -> bool:
        """Indique si Tir allie (specs.md 12.6) est actif sur cet ennemi ET qu'un autre
        ennemi est vivant pour en recevoir l'effet - sans tirer au sort lequel (cf.
        previsualiser_cible/_cible_redirection)."""
        a_le_debuff = any(buff.action == ActionCarte.REDIRECTION_CIBLE for buff in ennemi.buffs_actifs)
        if not a_le_debuff:
            return False
        return any(autre is not ennemi for autre in self.flotte.ennemis_vivants())

    def _cible_redirection(self, ennemi: Ennemi) -> Ennemi | None:
        """Si Tir allie est actif sur cet ennemi (specs.md 12.6), tire au hasard un autre
        ennemi vivant pour cibler a sa place ; None sinon. Seule methode qui consomme l'alea
        pour cette mecanique - previsualiser_cible ne fait que verifier l'eligibilite via
        _redirection_active, sans tirage, pour rester deterministe au survol/redessin."""
        if not self._redirection_active(ennemi):
            return None
        autres = [autre for autre in self.flotte.ennemis_vivants() if autre is not ennemi]
        return self.aleatoire.choice(autres)

    def _position_de_ennemi(self, ennemi: Ennemi) -> Position | None:
        """Retrouve la position d'un ennemi dans la flotte, ou None s'il n'y est pas."""
        for position, occupant in self.flotte.positions().items():
            if occupant is ennemi:
                return position
        return None

    def _verifier_fin_de_combat(self) -> None:
        """Met a jour l'etat du combat si la flotte ou le module de base est detruit."""
        if self.flotte.est_vide():
            self.etat = EtatCombat.VICTOIRE
        elif self.joueur.vaisseau.est_detruit():
            self.etat = EtatCombat.DEFAITE
