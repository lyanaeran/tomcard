"""
Moteur du combat entre le vaisseau du joueur et une flotte d'ennemis (cf. poc.md).
"""

import random
from enum import Enum, auto

from src.gameplay.carte import CIBLES_SANS_CLIC, ActionCarte, Carte, CibleCarte, TypeCarte
from src.gameplay.ciblage import module_cible_par_ennemi
from src.gameplay.ennemi import Ennemi
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


class Combat:
    """Orchestre le deroulement du combat entre le joueur et la flotte ennemie."""

    def __init__(self, joueur: Joueur, flotte: Flotte, aleatoire: random.Random | None = None):
        self.joueur = joueur
        self.flotte = flotte
        self.etat = EtatCombat.EN_COURS
        # Utilise pour le tirage au sort de Tir allie (specs.md 12.6) - jamais le module
        # random global directement, cf. CLAUDE.md "Determinisme du tirage aleatoire".
        self.aleatoire = aleatoire or random.Random()
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

    def finir_tour_joueur(self) -> list[tuple[Position, Ennemi, Module | Ennemi, int]]:
        """Termine le tour du joueur (defausse la main restante) et enchaine sur le tour ennemi.

        Renvoie la liste des attaques resolues (position et ennemi attaquant, cible - un
        module, ou un autre ennemi si Tir allie est actif, specs.md 12.6 -, degats reellement
        infliges), pour permettre a l'UI d'animer chaque attaque.
        """
        if self.etat != EtatCombat.EN_COURS:
            return []
        self.joueur.deck.defausser_main()
        attaques = self._tour_ennemi()
        if self.etat == EtatCombat.EN_COURS:
            self.joueur.debut_de_tour()
            self._declencher_buffs_debut_de_tour()
        return attaques

    def _declencher_buffs_debut_de_tour(self) -> None:
        """Redeclenche l'effet de chaque buff actif sur les modules vivants et decompte
        sa duree (specs.md 12.3/12.5) - meme principe que decrementer_debuffs() cote
        ennemi, mais au debut de chaque tour joueur plutot qu'a chaque tour ennemi."""
        for module in self._modules_vivants():
            module.declencher_buffs_tour()

    def previsualiser_cible(self, ennemi: Ennemi) -> Module | None:
        """Renvoie le module que cet ennemi attaquerait s'il agissait maintenant (pour le
        survol UI), ou None s'il n'y a pas de module a portee OU si un debuff Tir allie est
        actif (specs.md 12.6) : dans ce cas la cible reelle (un autre ennemi tire au hasard)
        n'est determinee qu'a la resolution du tour (_tour_ennemi/_cible_redirection),
        jamais ici, pour ne pas consommer l'alea a chaque survol/redessin (appele en boucle
        par l'UI, cf. CLAUDE.md determinisme du tirage aleatoire)."""
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
            occupants = (self.joueur.vaisseau.module_en(Colonne.AVANT, rangee) for rangee in (Rangee.GAUCHE, Rangee.DROITE))
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
            valeur_effective = self._appliquer_debuff(carte, cible)
        elif carte.type == TypeCarte.BUFF:
            valeur_effective = self._appliquer_buff(carte, cible)
        else:
            valeur_effective = min(carte.valeur, cible.pv_max - cible.pv)
            cible.soigner(carte.valeur)
        return valeur_effective

    def _appliquer_debuff(self, carte: Carte, cible: Ennemi) -> int:
        """Applique un debuff temporaire a un ennemi (specs.md 12.1/12.4). Independant des
        debuffs deja actifs sur cet ennemi : s'ajoute a la liste plutot que de les remplacer."""
        cible.appliquer_debuff(carte.action, carte.valeur, carte.duree)
        return carte.valeur

    def _appliquer_buff(self, carte: Carte, cible: Module) -> int:
        """Applique un buff a un module (specs.md 12.3/12.5). Comme les debuffs, s'ajoute
        a la liste des buffs actifs plutot que de remplacer un buff existant."""
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

    def _tour_ennemi(self) -> list[tuple[Position, Ennemi, Module | Ennemi, int]]:
        """Chaque ennemi vivant attaque sa cible, dans l'ordre de la grille (poc.md paragraphe
        3). Un ennemi sous Tir allie (specs.md 12.6) attaque un autre ennemi vivant tire au
        hasard a la place, si au moins un autre ennemi est encore en vie."""
        attaques = []
        for position, ennemi in self.flotte.positions().items():
            if ennemi.est_detruit():
                continue
            cible = self._cible_redirection(ennemi) or module_cible_par_ennemi(self.joueur.vaisseau, position.rangee)
            if cible is not None:
                degats = ennemi.degats_attaque_effectifs()
                degats_effectifs = _degats_effectifs(cible, degats)
                cible.subir_degats(degats)
                attaques.append((position, ennemi, cible, degats_effectifs))
            self._verifier_fin_de_combat()
            if self.etat != EtatCombat.EN_COURS:
                break
        for ennemi in self.flotte.ennemis_vivants():
            ennemi.decrementer_debuffs()
        return attaques

    def _redirection_active(self, ennemi: Ennemi) -> bool:
        """Indique si Tir allie (specs.md 12.6) est actif sur cet ennemi ET qu'un autre
        ennemi est vivant pour en recevoir l'effet - sans tirer au sort lequel (cf.
        previsualiser_cible/_cible_redirection)."""
        a_le_debuff = any(debuff.action == ActionCarte.REDIRECTION_CIBLE for debuff in ennemi.debuffs_actifs)
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
