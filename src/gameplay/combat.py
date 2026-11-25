"""
Combat (Combat) : fait jouer ensemble Carte, Module, Ennemi et les
statuts (specs.md 3, seule reference de ce fichier). Gameplay seulement : aucune
dependance d'affichage, une API d'actions (jouer_carte, finir_tour) et de consultations (etat,
cibles_possibles, intentions, journal), utilisee par le parcours (partie.py), l'affichage PC et
web, le simulateur et les tests.
"""

import random
from dataclasses import dataclass
from enum import Enum, auto

from src.gameplay.carte import Camp, Carte, CibleCarte, Effet, NatureEffet, PorteeEffet, appliquer_repetition
from src.gameplay.deck import CARTES_PIOCHEES_PAR_TOUR, Deck
from src.gameplay.ennemi import CibleEffetEnnemi, EffetEnnemi, Ennemi, NatureEffetEnnemi
from src.gameplay.flotte import Flotte
from src.gameplay.module import Module
from src.gameplay.position import Ligne, Position
from src.gameplay.statut import Encaissement, Statut, Statuts
from src.gameplay.vaisseau import Vaisseau

# Electricite rendue au debut de chaque tour du joueur (combat.md 3.3)
ELECTRICITE_PAR_TOUR = 3

# Natures d'effet de carte laissees pour plus tard (specs.md 3.8.4) : une carte qui en porte
# est refusee
NATURES_NON_GEREES = {
    NatureEffet.VULNERABILITE, NatureEffet.REDUCTION_DEGATS, NatureEffet.REDIRECTION_CIBLE,
    # Decidee le 2026-11-16, pas encore codee (specs/effets-a-coder.md)
    NatureEffet.SURCHARGE,
}

# Natures qui agissent sur le joueur lui-meme (electricite, pioche, cartes), pas sur une entite
NATURES_GLOBALES = {NatureEffet.GAIN_ELECTRICITE, NatureEffet.PIOCHE, NatureEffet.REPETITION}

# Camp que chaque nature d'effet peut toucher : une carte qui l'applique a l'autre camp est
# injouable (verifie avant toute modification du combat)
CAMP_PAR_NATURE = {
    NatureEffet.DEGATS: Camp.ENNEMI,
    NatureEffet.INCENDIE: Camp.ENNEMI,
    NatureEffet.BOUCLIER: Camp.JOUEUR,
    NatureEffet.REPARATION: Camp.JOUEUR,
    NatureEffet.ANNULATION_PROCHAINE_ATTAQUE: Camp.JOUEUR,
    NatureEffet.RENVOI: Camp.JOUEUR,
    NatureEffet.RETRAIT_BOUCLIER: Camp.ENNEMI,
}

Entite = Module | Ennemi


class EtatCombat(Enum):
    EN_COURS = auto()
    VICTOIRE = auto()
    DEFAITE = auto()


class NatureEvenement(Enum):
    """Ce qu'enregistre une entree du journal (des faits, sans texte affiche)."""

    # Debut d'un tour du joueur (valeur : numero de tour)
    DEBUT_TOUR = auto()
    # Carte jouee (carte, cible : entite de la case choisie)
    CARTE_JOUEE = auto()
    # Attaque (source : carte ou ennemi, cible, valeur : degats, et le detail des degats)
    ATTAQUE = auto()
    # Attaque des degats renvoyes par un renvoi (source : entite protegee, cible : qui les recoit,
    # valeur : degats renvoyes, et le detail des degats)
    RENVOI = auto()
    # Statut pose (cible, statut, valeur : intensite posee)
    STATUT_POSE = auto()
    # Statut retire par une carte (cible, statut, valeur : intensite reellement retiree)
    STATUT_RETIRE = auto()
    # Reparation (cible, valeur : PV rendus, pv_restants)
    REPARATION = auto()
    # Incendie en fin de tour (cible, valeur : intensite, et le detail des degats)
    INCENDIE = auto()
    # Electricite gagnee, cartes piochees, cartes dont les lancements augmentent (valeur)
    ELECTRICITE = auto()
    PIOCHE = auto()
    REPETITION = auto()
    # Destruction (cible) ; CARTES_HORS_SERVICE : valeur = nombre de cartes deplacees
    MODULE_DETRUIT = auto()
    ENNEMI_DETRUIT = auto()
    CARTES_HORS_SERVICE = auto()
    VICTOIRE = auto()
    DEFAITE = auto()


@dataclass(frozen=True)
class Evenement:
    """Une entree du journal de combat. Pour des degats (ATTAQUE, RENVOI, INCENDIE) : valeur =
    annules_leurre + renvoyes + absorbes_bouclier + degats sur les PV ; pv_perdus est plafonne par
    les PV qui restaient ; pv_restants : PV de la cible apres l'evenement."""

    nature: NatureEvenement
    tour: int
    source: object = None
    cible: object = None
    valeur: int | None = None
    statut: Statut | None = None
    # Detail des degats recus
    annules_leurre: int | None = None
    renvoyes: int | None = None
    absorbes_bouclier: int | None = None
    pv_perdus: int | None = None
    pv_restants: int | None = None


@dataclass(frozen=True)
class IntentionEffet:
    """Un effet de la prochaine etape d'un ennemi, avec sa valeur au tour en cours. `cible_prevue` :
    module vise par une attaque PROXIMITE si rien ne change, l'ennemi lui-meme pour SOI_MEME, None
    sinon (tous les modules, ou allie tire au hasard au moment de jouer)."""

    effet: EffetEnnemi
    valeur: int
    cible_prevue: Entite | None


@dataclass(frozen=True)
class Intention:
    ennemi: Ennemi
    effets: tuple[IntentionEffet, ...]


class Combat:
    """Un combat de la refonte. Le combat commence au debut du tour 1 du joueur."""

    def __init__(self, modules: list[Module], deck: list[Carte], flotte: Flotte, aleatoire: random.Random):
        self.vaisseau = Vaisseau(modules)
        self.flotte = flotte
        self.aleatoire = aleatoire
        for carte in deck:
            if carte.exemplaire_module is None or self.vaisseau.module_d_exemplaire(carte.exemplaire_module) is None:
                raise ValueError(f"Carte {carte.id} : rattachee a un module absent ({carte.exemplaire_module})")
        # Copie de chaque carte, comme les modules et les ennemis : munitions et lancements
        # repartent de leur base, et le deck de la partie n'est jamais modifie (7)
        self.deck = Deck([carte.copie() for carte in deck], aleatoire)
        self.etat = EtatCombat.EN_COURS
        self.tour = 1
        self.electricite = 0
        self.journal: list[Evenement] = []
        # Entites deja traitees comme detruites (pile Hors service faite, journal note)
        self._detruits: list[Entite] = []
        self._debut_tour_joueur()

    def remplacer_aleatoire(self, aleatoire: random.Random) -> None:
        """Remplace le generateur de tout le combat (melanges du deck compris) : un bot qui essaie
        des coups sur une copie ne doit pas connaitre a l'avance les vrais tirages."""
        self.aleatoire = aleatoire
        self.deck.aleatoire = aleatoire

    # --- Consultations ---

    @property
    def en_cours(self) -> bool:
        return self.etat == EtatCombat.EN_COURS

    def ennemis_detruits(self) -> list[Ennemi]:
        return [ennemi for ennemi in self.flotte.ennemis if ennemi.est_detruit()]

    def cibles_possibles(self, carte: Carte) -> list[Position]:
        """Cases valides pour jouer cette carte (specs.md 3.8.2) : une case vivante du bon
        camp, de la bonne ligne pour Avant/Arriere, celle du principal pour Module Principal."""
        cible = carte.cible
        if cible.camp == Camp.ENNEMI:
            cases = self.flotte.cases_vivantes()
            if cible == CibleCarte.ENNEMI_AVANT:
                return [case for case in cases if case.ligne == Ligne.AVANT]
            if cible == CibleCarte.ENNEMI_ARRIERE:
                return [case for case in cases if case.ligne == Ligne.ARRIERE]
            return cases
        cases = self.vaisseau.cases_vivantes()
        if cible == CibleCarte.MODULE_PRINCIPAL:
            return [case for case in cases if self.vaisseau.module_en(case) is self.vaisseau.principal]
        if cible == CibleCarte.MODULE_AVANT:
            return [case for case in cases if case.ligne == Ligne.AVANT]
        return cases

    def peut_jouer(self, carte: Carte) -> bool:
        """En main, electricite suffisante, effets geres, au moins une cible."""
        return bool(self._cases_jouables(carte))

    def _cases_jouables(self, carte: Carte) -> list[Position]:
        """Cases ou la carte peut etre jouee maintenant ; vide si elle est injouable (hors main,
        electricite, nature laissee pour plus tard ou appliquee au mauvais camp, aucune cible)."""
        if not (
            self.en_cours
            and any(carte is en_main for en_main in self.deck.main)
            and carte.cout <= self.electricite
            and all(self._effet_gere(carte, effet) for effet in carte.effets)
        ):
            return []
        return self.cibles_possibles(carte)

    @staticmethod
    def _effet_gere(carte: Carte, effet: Effet) -> bool:
        if effet.nature in NATURES_NON_GEREES:
            return False
        camp = CAMP_PAR_NATURE.get(effet.nature)
        if camp is None:
            return True
        camp_touche = effet.portee.camp or carte.cible.camp
        return camp == camp_touche

    def intentions(self) -> list[Intention]:
        """Ce que chaque ennemi vivant jouera a son prochain tour (specs.md 13.2.3)."""
        resultat = []
        for ennemi in self.flotte.ennemis_vivants():
            effets = []
            for effet in ennemi.etape_courante:
                if effet.cible == CibleEffetEnnemi.PROXIMITE:
                    prevue = self.vaisseau.module_le_plus_proche(self.flotte.colonne_de(ennemi))
                elif effet.cible == CibleEffetEnnemi.SOI_MEME:
                    prevue = ennemi
                else:
                    prevue = None
                effets.append(IntentionEffet(effet, ennemi.valeur(effet.valeur, self.tour), prevue))
            resultat.append(Intention(ennemi, tuple(effets)))
        return resultat

    def modules_vises(self, effet: IntentionEffet) -> list[Module]:
        """Modules que toucherait cet effet d'intention si rien ne change : le module prevu d'une
        attaque PROXIMITE, tous les modules vivants pour TOUS_MODULES, aucun pour un effet qui ne
        vise pas le joueur. Sert a l'affichage a marquer les modules vises (PC et web)."""
        if effet.effet.cible == CibleEffetEnnemi.TOUS_MODULES:
            return self.vaisseau.modules_vivants()
        if effet.effet.cible == CibleEffetEnnemi.PROXIMITE and effet.cible_prevue is not None:
            return [effet.cible_prevue]
        return []

    # --- Actions ---

    def jouer_carte(self, carte: Carte, case: Position) -> None:
        """Joue une carte de la main sur la case choisie (specs.md 3.8). Refuse une action
        invalide (ValueError)."""
        cases = self._cases_jouables(carte)
        if not cases:
            raise ValueError(f"Carte {carte.id} : injouable maintenant")
        if case not in cases:
            raise ValueError(f"Carte {carte.id} : cible invalide {case}")
        cible_choisie = self._entite_en(carte, case)
        self.deck.retirer_de_la_main(carte)
        self.electricite -= carte.cout
        epuisee = carte.consommer_munition()
        self._noter(NatureEvenement.CARTE_JOUEE, source=carte, cible=cible_choisie)
        # Cibles choisies une fois pour tous les lancements (decision utilisateur, 4.3) : une
        # cible detruite par un lancement ne recoit plus les suivants
        cibles_par_effet = [self._cibles_de_l_effet(carte, effet, case) for effet in carte.effets]
        for _ in range(carte.lancements_actuels):
            for effet, cibles in zip(carte.effets, cibles_par_effet):
                if not self.en_cours:
                    break
                self._appliquer_effet_de_carte(carte, effet, cibles)
        module_de_la_carte = self.vaisseau.module_d_exemplaire(carte.exemplaire_module)
        self.deck.ranger_carte_jouee(carte, epuisee, module_de_la_carte.est_detruit())

    def finir_tour(self) -> None:
        """Termine le tour du joueur, joue le tour ennemi et commence le tour suivant (3.2, 3.3)."""
        if not self.en_cours:
            raise ValueError("Le combat est termine")
        self.deck.defausser_main()
        for ennemi in self.flotte.ennemis_vivants():
            self._fin_de_tour_d_entite(ennemi, ennemi.fin_du_tour_du_joueur)
            if not self.en_cours:
                return
        self._tour_ennemi()
        if not self.en_cours:
            return
        for module in self.vaisseau.modules_vivants():
            self._fin_de_tour_d_entite(module, module.fin_du_tour_ennemi)
            if not self.en_cours:
                return
        self.tour += 1
        self._debut_tour_joueur()

    # --- Deroulement ---

    def _debut_tour_joueur(self) -> None:
        self.electricite = ELECTRICITE_PAR_TOUR
        self.deck.piocher(CARTES_PIOCHEES_PAR_TOUR)
        self._noter(NatureEvenement.DEBUT_TOUR, valeur=self.tour)

    def _fin_de_tour_d_entite(self, entite: Entite, fin_de_tour) -> None:
        """Fin de tour d'un module ou d'un ennemi : incendie (note au journal) puis extinction des
        statuts, puis destruction eventuelle."""
        pv_avant = self._pv(entite)
        encaissement = fin_de_tour()
        if encaissement.degats:
            self._noter_degats(NatureEvenement.INCENDIE, None, entite, encaissement, pv_avant)
        self._traiter_destruction(entite)

    def _tour_ennemi(self) -> None:
        """Chaque ennemi vivant joue son etape courante, dans l'ordre de jeu (5.1), puis avance."""
        for ennemi in self.flotte.ennemis_vivants():
            if ennemi.est_detruit():
                continue
            for effet in ennemi.etape_courante:
                self._jouer_effet_ennemi(ennemi, effet)
                if not self.en_cours:
                    return
                if ennemi.est_detruit():
                    # Detruit pendant son etape (renvoi d'un module) : il ne joue plus
                    break
            else:
                ennemi.avancer_cycle()

    def _jouer_effet_ennemi(self, ennemi: Ennemi, effet: EffetEnnemi) -> None:
        """Un effet d'etape ennemie. Cible choisie une seule fois, puis l'effet est repete sur elle
        (decision utilisateur, 5.2) : une cible detruite ne recoit plus les repetitions."""
        valeur = ennemi.valeur(effet.valeur, self.tour)
        if effet.nature == NatureEffetEnnemi.ATTAQUE:
            if effet.cible == CibleEffetEnnemi.PROXIMITE:
                proche = self.vaisseau.module_le_plus_proche(self.flotte.colonne_de(ennemi))
                cibles = [proche] if proche is not None else []
            else:
                cibles = self.vaisseau.modules_vivants()
            for _ in range(effet.repetitions):
                for module in cibles:
                    if module.est_detruit():
                        continue
                    self._attaquer(ennemi, module, valeur, renvoi_vers=ennemi)
                    if not self.en_cours:
                        return
            return
        if effet.cible == CibleEffetEnnemi.SOI_MEME:
            allie = ennemi
        else:
            candidats = (
                self.flotte.ennemis_vivants_de_ligne(Ligne.AVANT)
                or self.flotte.ennemis_vivants_de_ligne(Ligne.ARRIERE)
            )
            allie = self.aleatoire.choice(candidats)
        for _ in range(effet.repetitions):
            self._poser_statut(allie, effet.nature.statut_pose, valeur)

    # --- Cartes ---

    def _entite_en(self, carte: Carte, case: Position) -> Entite | None:
        if carte.cible.camp == Camp.ENNEMI:
            return self.flotte.ennemi_en(case)
        return self.vaisseau.module_en(case)

    def _cibles_de_la_carte(self, carte: Carte, case: Position) -> list[Entite]:
        """Ce que touche la cible de la carte pour la case choisie (tableau du 4.2)."""
        cible = carte.cible
        if cible in (CibleCarte.ENNEMI_UNIQUE, CibleCarte.MODULE_UNIQUE):
            return [self._entite_en(carte, case)]
        if cible == CibleCarte.ENNEMI_LIGNE:
            return self.flotte.ennemis_vivants_de_ligne(case.ligne)
        if cible == CibleCarte.ENNEMI_AVANT:
            return self.flotte.ennemis_vivants_de_ligne(Ligne.AVANT)
        if cible == CibleCarte.ENNEMI_ARRIERE:
            return self.flotte.ennemis_vivants_de_ligne(Ligne.ARRIERE)
        if cible == CibleCarte.ENNEMI_TOUS:
            return self.flotte.ennemis_vivants()
        if cible == CibleCarte.MODULE_PRINCIPAL:
            return [self.vaisseau.principal]
        if cible == CibleCarte.MODULE_AVANT:
            return self.vaisseau.modules_vivants_de_ligne(Ligne.AVANT)
        return self.vaisseau.modules_vivants()

    def _cibles_de_l_effet(self, carte: Carte, effet: Effet, case: Position) -> list[Entite]:
        """Entites touchees par un effet selon sa portee (4.3) ; vide pour une nature globale."""
        if effet.nature in NATURES_GLOBALES:
            return []
        if effet.portee == PorteeEffet.CIBLE:
            return self._cibles_de_la_carte(carte, case)
        if effet.portee == PorteeEffet.AUTRES_ENNEMIS:
            choisi = self.flotte.ennemi_en(case)
            return [ennemi for ennemi in self.flotte.ennemis_vivants() if ennemi is not choisi]
        if effet.portee == PorteeEffet.MEME_COLONNE:
            # L'ennemi de l'autre case de la colonne ; un ennemi sur les deux cases (le Boss) est la
            # cible elle-meme, il n'est pas touche une seconde fois
            choisi = self.flotte.ennemi_en(case)
            autre_ligne = Ligne.ARRIERE if case.ligne == Ligne.AVANT else Ligne.AVANT
            autre = self.flotte.ennemi_en(Position(autre_ligne, case.colonne))
            return [autre] if autre is not None and autre is not choisi and not autre.est_detruit() else []
        if effet.portee == PorteeEffet.MODULE_PRINCIPAL:
            return [self.vaisseau.principal]
        if effet.portee == PorteeEffet.MODULE_DE_LA_CARTE:
            module = self.vaisseau.module_d_exemplaire(carte.exemplaire_module)
            return [module] if module is not None and not module.est_detruit() else []
        ligne = Ligne.AVANT if effet.portee == PorteeEffet.LIGNE_AVANT_ENNEMIE else Ligne.ARRIERE
        return self.flotte.ennemis_vivants_de_ligne(ligne)

    def _appliquer_effet_de_carte(self, carte: Carte, effet: Effet, cibles: list[Entite]) -> None:
        """Un lancement d'un effet de carte (tableau du 4.4)."""
        valeur = carte.valeur_de(effet)
        nature = effet.nature
        if nature == NatureEffet.GAIN_ELECTRICITE:
            self.electricite += valeur
            self._noter(NatureEvenement.ELECTRICITE, source=carte, valeur=valeur)
        elif nature == NatureEffet.PIOCHE:
            piochees = self.deck.piocher(valeur)
            self._noter(NatureEvenement.PIOCHE, source=carte, valeur=piochees)
        elif nature == NatureEffet.REPETITION:
            modifiees = appliquer_repetition(effet, valeur, self.deck.toutes_les_cartes() + [carte])
            self._noter(NatureEvenement.REPETITION, source=carte, valeur=modifiees)
        for cible in cibles:
            if cible.est_detruit() or not self.en_cours:
                continue
            if nature == NatureEffet.DEGATS:
                if not isinstance(cible, Ennemi):
                    raise ValueError(f"Carte {carte.id} : degats sur un module non geres")
                self._attaquer(carte, cible, valeur, renvoi_vers=self._module_qui_recoit_le_renvoi(carte))
            elif nature == NatureEffet.RETRAIT_BOUCLIER:
                retire = cible.statuts.retirer(Statut.BOUCLIER, valeur)
                self._noter(
                    NatureEvenement.STATUT_RETIRE, source=carte, cible=cible, valeur=retire, statut=Statut.BOUCLIER,
                )
            elif nature == NatureEffet.REPARATION:
                pv_avant = cible.pv_combat
                cible.reparer(valeur)
                self._noter(
                    NatureEvenement.REPARATION, source=carte, cible=cible, valeur=cible.pv_combat - pv_avant,
                    pv_restants=cible.pv_combat,
                )
            elif nature.statut_pose is not None:
                # Le leurre n'a pas de valeur : intensite 1
                self._poser_statut(cible, nature.statut_pose, valeur if valeur is not None else 1, source=carte)

    def _module_qui_recoit_le_renvoi(self, carte: Carte) -> Module:
        """Module de la carte jouee, ou le principal s'il est detruit (decision utilisateur, 4.5)."""
        module = self.vaisseau.module_d_exemplaire(carte.exemplaire_module)
        return self.vaisseau.principal if module.est_detruit() else module

    # --- Resolution commune ---

    def _attaquer(self, source: object, cible: Entite, degats: int, renvoi_vers: Entite) -> None:
        """Une attaque de `degats` sur `cible` ; les degats renvoyes sont une nouvelle attaque sur
        `renvoi_vers` (decision utilisateur, 4.5), qui ne renvoie rien a son tour."""
        pv_avant = self._pv(cible)
        encaissement = cible.subir_degats(degats)
        self._noter_degats(NatureEvenement.ATTAQUE, source, cible, encaissement, pv_avant)
        self._traiter_destruction(cible)
        if encaissement.renvoyes and not renvoi_vers.est_detruit() and self.en_cours:
            pv_avant = self._pv(renvoi_vers)
            # Les degats renvoyes ne sont jamais renvoyes a leur tour : leur propre renvoi est ignore
            renvoi = renvoi_vers.subir_degats(encaissement.renvoyes)
            self._noter_degats(NatureEvenement.RENVOI, cible, renvoi_vers, renvoi, pv_avant)
            self._traiter_destruction(renvoi_vers)

    def _noter_degats(self, nature: NatureEvenement, source: object, cible: Entite, encaissement: Encaissement, pv_avant: int) -> None:
        """Note des degats recus avec leur detail : leurre, renvoi, bouclier, PV perdus et restants."""
        self._noter(
            nature, source=source, cible=cible, valeur=encaissement.degats,
            annules_leurre=encaissement.annules_leurre, renvoyes=encaissement.renvoyes,
            absorbes_bouclier=encaissement.absorbes_bouclier, pv_perdus=pv_avant - self._pv(cible),
            pv_restants=self._pv(cible),
        )

    def _poser_statut(self, cible: Entite, statut: Statut, valeur: int, source: object = None) -> None:
        cible.statuts.ajouter(statut, valeur)
        self._noter(NatureEvenement.STATUT_POSE, source=source, cible=cible, valeur=valeur, statut=statut)

    def _traiter_destruction(self, entite: Entite) -> None:
        """Destruction d'un module (6) ou d'un ennemi, et fin de combat eventuelle (7)."""
        if not entite.est_detruit() or any(entite is deja for deja in self._detruits):
            return
        self._detruits.append(entite)
        # Ses statuts sont perdus (6)
        entite.statuts = Statuts()
        if isinstance(entite, Module):
            self._noter(NatureEvenement.MODULE_DETRUIT, cible=entite)
            deplacees = self.deck.mettre_hors_service(entite.exemplaire)
            if deplacees:
                self._noter(NatureEvenement.CARTES_HORS_SERVICE, cible=entite, valeur=len(deplacees))
            if entite.principal:
                self.etat = EtatCombat.DEFAITE
                self._noter(NatureEvenement.DEFAITE)
            return
        self._noter(NatureEvenement.ENNEMI_DETRUIT, cible=entite)
        self._verifier_victoire()

    def _verifier_victoire(self) -> bool:
        if self.en_cours and self.flotte.est_vide():
            self.etat = EtatCombat.VICTOIRE
            self._noter(NatureEvenement.VICTOIRE)
        return self.etat == EtatCombat.VICTOIRE

    @staticmethod
    def _pv(entite: Entite) -> int:
        return entite.pv_combat if isinstance(entite, Module) else entite.pv

    def _noter(self, nature: NatureEvenement, **champs) -> None:
        self.journal.append(Evenement(nature, self.tour, **champs))
