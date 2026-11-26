"""
Carte (Carte) : modele de donnees issu de la refonte des cartes
(specs.md 12). Source de verite :
config/cartes.json (charger_cartes). Relue et validee par l'utilisateur le 2026-11-08.
Seul modele de carte du jeu depuis la suppression de l'ancien moteur (PR 4 du branchement,
specs/refonte-branchement.md).

Principes :
- une carte porte des VALEURS NOMMEES (ex. {"degats_cible": 15, "degats_autres": 6}) et une liste
  d'EFFETS qui y renvoient par leur nom : plusieurs valeurs par carte (Missiles : degats sur la
  cible et sur les autres ennemis), et une description qui les cite entre accolades ("Inflige
  {degats_cible} degats...") ;
- les natures d'effet qui posent un etat durable (bouclier, incendie, leurre) renvoient a un
  STATUT (statut.py, statut_pose), qui porte seul ses regles de cumul et d'extinction ;
- une carte peut etre lancee plusieurs fois (`lancements_base`) ; les cartes "les cartes X sont
  lancees N fois de plus" (Salve laser, Protocole d'urgence, Bouclier stabilise) sont un effet
  REPETITION dont le FiltreCartes designe les cartes visees : il augmente leur `lancements_actuels`
  jusqu'a la fin du combat (appliquer_repetition) ;
- mot-cle Persistante et rattachement a un exemplaire de module (exemplaire_module) : une carte dont
  le module est detruit part en pile Hors service, sauf si elle est Persistante
  (specs.md 3.4, 12.4) ;
- la cible reprend le vocabulaire du registre des cartes ("Ennemi Unique", "Module Tous"...) ;
- la carte dit a quel(s) type(s) de module elle appartient (`modules`, ex. ["MOD_2"]) :
  config/modules.json ne liste plus ses cartes, Module.cartes est calcule a partir des cartes
  (module.py:charger_modules) ;
- `jouabilite` a trois valeurs : oui, non, supprimee (carte retiree du jeu sans etre effacee du
  fichier, specs/outil-editeur-cartes.md).
"""

import dataclasses
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from string import Formatter

from src.gameplay.statut import Statut

FICHIER_CARTES = Path(__file__).resolve().parents[2] / "config" / "cartes.json"


class RareteCarte(Enum):
    """Palier de rarete d'une carte, cf. specs.md paragraphe 7.3 et 7.4."""

    BASE = auto()
    COMMUNE = auto()
    RARE = auto()
    LEGENDAIRE = auto()


class Jouabilite(Enum):
    """Champ "jouable" de config/cartes.json."""

    # Proposee en recompense et jouee normalement
    OUI = "oui"
    # Pas proposee (ex. carte en preparation)
    NON = "non"
    # Retiree du jeu mais gardee dans le fichier ; traitee comme NON par le jeu
    SUPPRIMEE = "supprimee"


class CategorieCarte(Enum):
    """Categorie d'une carte (specs.md 7.1)."""

    ATTAQUE = "Attaque"
    DEFENSE = "Defense"
    REPARATION = "Reparation"
    BUFF = "Buff"
    DEBUFF = "Debuff"
    OUTILS = "Outils"
    CONTROLE = "Controle"


class Camp(Enum):
    ENNEMI = auto()
    JOUEUR = auto()


class CibleCarte(Enum):
    """Cible d'une carte. Une cible "unique" ou "ligne" depend de la case cliquee ; les autres
    touchent un ensemble fixe, mais demandent quand meme un clic de confirmation sur une case du bon
    camp (specs.md 8.3, identique PC et web)."""

    ENNEMI_UNIQUE = "Ennemi Unique"
    ENNEMI_LIGNE = "Ennemi Ligne"
    ENNEMI_AVANT = "Ennemi Avant"
    ENNEMI_ARRIERE = "Ennemi Arriere"
    ENNEMI_TOUS = "Ennemi Tous"
    MODULE_UNIQUE = "Module Unique"
    MODULE_PRINCIPAL = "Module Principal"
    MODULE_AVANT = "Module Avant"
    MODULE_TOUS = "Module Tous"

    @property
    def camp(self) -> Camp:
        return Camp.ENNEMI if self.name.startswith("ENNEMI") else Camp.JOUEUR

    @property
    def depend_de_la_case_cliquee(self) -> bool:
        """True si la case cliquee determine ce qui est touche (sinon simple confirmation)."""
        return self in (CibleCarte.ENNEMI_UNIQUE, CibleCarte.ENNEMI_LIGNE, CibleCarte.MODULE_UNIQUE)


class NatureEffet(Enum):
    """Ce que fait un effet. `valeur` designe la valeur nommee de la carte que l'effet utilise. Le
    statut pose, s'il y en a un, est donne par statut_pose (STATUT_PAR_NATURE)."""

    # Retire `valeur` PV (apres le bouclier) a chaque ennemi touche (Laser, Missiles, Bombardement)
    DEGATS = auto()
    # Pose le statut BOUCLIER d'intensite `valeur` sur chaque module touche (Bouclier, Proteger le
    # vaisseau, Blindage cible)
    BOUCLIER = auto()
    # Rend `valeur` PV au module touche, sans depasser ses PV max (Reparation)
    REPARATION = auto()
    # Pose le statut INCENDIE d'intensite `valeur` sur l'ennemi (poison de Slay the Spire : Tir
    # incendiaire, Embrasement)
    INCENDIE = auto()
    # L'ennemi subit `valeur` % de degats en plus (Breche, Ligne avant)
    VULNERABILITE = auto()
    # L'ennemi inflige `valeur` degats de moins par attaque (Tordre le canon)
    REDUCTION_DEGATS = auto()
    # Pose le statut LEURRE sur le module touche : annule sa prochaine attaque recue, sans valeur
    # (Leurre)
    ANNULATION_PROCHAINE_ATTAQUE = auto()
    # Pose le statut RENVOI d'intensite `valeur` sur le module touche : il renvoie a l'ennemi qui
    # l'attaque les degats recus, jusqu'a son intensite (Bouclier reflechissant, decision
    # utilisateur du 2026-11-22 ; memes regles que le renvoi de Miroir, specs.md 3.5)
    RENVOI = auto()
    # Retire `valeur` de bouclier a l'ennemi touche, sans toucher a son renvoi ni a son leurre
    # (Laser disrupteur, decision utilisateur du 2026-11-22)
    RETRAIT_BOUCLIER = auto()
    # L'ennemi touche attaque un de ses allies au hasard au lieu du joueur, sans valeur (Tir allie)
    REDIRECTION_CIBLE = auto()
    # Donne `valeur` electricite en plus pour ce tour (aucune carte pour l'instant)
    GAIN_ELECTRICITE = auto()
    # Pioche `valeur` cartes en plus (Boost)
    PIOCHE = auto()
    # Les cartes designees par le filtre de l'effet sont lancees `valeur` fois de plus, jusqu'a la
    # fin du combat (appliquer_repetition : Salve laser, Protocole d'urgence, Bouclier stabilise)
    REPETITION = auto()
    # Pose le statut SURCHARGE d'intensite `valeur` sur le module principal : +intensite aux degats
    # de chaque coup des cartes du joueur, -1 par tour (Post-combustion, Ogive surchauffee)
    SURCHARGE = auto()
    # Multiplie la Surcharge du principal par `valeur` (Amplificateur)
    MULTIPLIER_SURCHARGE = auto()
    # La Surcharge du principal ne baisse plus jusqu'a la fin du combat, sans valeur (Lanceur
    # incandescent)
    FIGER_SURCHARGE = auto()
    # Pose le statut VERROUILLAGE d'intensite `valeur` sur l'ennemi touche : il subit +intensite
    # aux degats de chaque coup de carte, -1 par tour (Missile marqueur, Protocole de ciblage)
    VERROUILLAGE = auto()

    @property
    def statut_pose(self) -> Statut | None:
        """Statut pose sur l'entite touchee, None pour un effet sans etat durable."""
        return STATUT_PAR_NATURE.get(self)


# Natures sans valeur numerique : leur effet ne renvoie a aucune valeur nommee de la carte
NATURES_SANS_VALEUR = {
    NatureEffet.ANNULATION_PROCHAINE_ATTAQUE, NatureEffet.REDIRECTION_CIBLE, NatureEffet.FIGER_SURCHARGE,
}

# Statut pose sur l'entite touchee : ses regles de cumul et d'extinction sont celles de
# statut.py (une seule source, partagee avec les modules et les ennemis, specs.md 3.5)
STATUT_PAR_NATURE = {
    NatureEffet.BOUCLIER: Statut.BOUCLIER,
    NatureEffet.INCENDIE: Statut.INCENDIE,
    NatureEffet.ANNULATION_PROCHAINE_ATTAQUE: Statut.LEURRE,
    NatureEffet.RENVOI: Statut.RENVOI,
    NatureEffet.SURCHARGE: Statut.SURCHARGE,
    NatureEffet.VERROUILLAGE: Statut.VERROUILLAGE,
}

# Natures qui n'agissent que sur la Surcharge du module principal : la carte doit viser le
# principal (cible Module Principal, ou portee MODULE_PRINCIPAL)
NATURES_DU_PRINCIPAL = {NatureEffet.SURCHARGE, NatureEffet.MULTIPLIER_SURCHARGE, NatureEffet.FIGER_SURCHARGE}

# Camp que chaque nature d'effet peut toucher (portee de l'effet, sinon cible de la carte) : une
# carte qui l'applique a l'autre camp est refusee au chargement (Carte.__post_init__)
CAMP_PAR_NATURE = {
    NatureEffet.DEGATS: Camp.ENNEMI,
    NatureEffet.INCENDIE: Camp.ENNEMI,
    NatureEffet.RETRAIT_BOUCLIER: Camp.ENNEMI,
    NatureEffet.VERROUILLAGE: Camp.ENNEMI,
    NatureEffet.BOUCLIER: Camp.JOUEUR,
    NatureEffet.REPARATION: Camp.JOUEUR,
    NatureEffet.ANNULATION_PROCHAINE_ATTAQUE: Camp.JOUEUR,
    NatureEffet.RENVOI: Camp.JOUEUR,
    NatureEffet.SURCHARGE: Camp.JOUEUR,
    NatureEffet.MULTIPLIER_SURCHARGE: Camp.JOUEUR,
    NatureEffet.FIGER_SURCHARGE: Camp.JOUEUR,
}

# Natures dont l'effet peut avoir une duree en tours (statuts a duree, geres plus tard :
# specs.md 3.5.3)
NATURES_A_DUREE = {NatureEffet.VULNERABILITE, NatureEffet.REDUCTION_DEGATS, NatureEffet.REDIRECTION_CIBLE}


class PorteeEffet(Enum):
    """Ce que touche un effet, par rapport a la cible de la carte."""

    # La cible de la carte (ou tout l'ensemble vise pour une cible multiple)
    CIBLE = auto()
    # Tous les ennemis vivants sauf la cible (Missiles : degats sur la cible, puis sur les autres)
    AUTRES_ENNEMIS = auto()
    # Ligne avant / arriere de la flotte ennemie (Torpille : degats a l'avant, puis a l'arriere)
    LIGNE_AVANT_ENNEMIE = auto()
    LIGNE_ARRIERE_ENNEMIE = auto()
    # L'autre ennemi de la colonne de la case choisie, derriere ou devant elle (Torpille
    # traversante ; vocabulaire de specs.md 3.1.1)
    MEME_COLONNE = auto()
    # Le module principal, quelle que soit la cible de la carte (Missile de couverture : degats a
    # un ennemi et bouclier au principal)
    MODULE_PRINCIPAL = auto()
    # Le module auquel la carte est rattachee (exemplaire_module), le principal s'il est detruit,
    # comme le renvoi des degats (Torpille de barrage : bouclier au Lanceur)
    MODULE_DE_LA_CARTE = auto()

    @property
    def camp(self) -> "Camp | None":
        """Camp touche par cette portee ; None pour CIBLE, qui touche le camp de la cible de la
        carte. Une nouvelle portee doit etre ajoutee a _CAMP_PAR_PORTEE (KeyError sinon)."""
        return _CAMP_PAR_PORTEE[self]


_CAMP_PAR_PORTEE = {
    PorteeEffet.CIBLE: None,
    PorteeEffet.AUTRES_ENNEMIS: Camp.ENNEMI,
    PorteeEffet.LIGNE_AVANT_ENNEMIE: Camp.ENNEMI,
    PorteeEffet.LIGNE_ARRIERE_ENNEMIE: Camp.ENNEMI,
    PorteeEffet.MEME_COLONNE: Camp.ENNEMI,
    PorteeEffet.MODULE_PRINCIPAL: Camp.JOUEUR,
    PorteeEffet.MODULE_DE_LA_CARTE: Camp.JOUEUR,
}


# Cles autorisees dans config/cartes.json : une cle inconnue (ex. faute de frappe "persistant")
# est refusee au chargement plutot qu'ignoree
CLES_CARTE = {
    "id", "nom", "image", "rarete", "categorie", "cible", "modules", "famille", "cout", "munition", "lancements",
    "persistante", "jouable", "refonte", "description", "valeurs", "effets",
}
CLES_EFFET = {"nature", "valeur", "portee", "duree", "filtre", "bonus"}
CLES_BONUS = {"par", "facteur", "consomme"}
CLES_FILTRE = {"id", "rarete", "categorie", "famille", "module"}

# Familles de noms des cartes (proposition-module-principal.md 1.2, proposition-lanceur-missiles.md
# 5.1), sans accent. Le champ `famille` n'est rempli que sur les cartes qu'un buff doit pouvoir
# viser, aujourd'hui les seules cartes Laser (decision utilisateur, 2026-11-25) ; une famille hors de
# cette liste est refusee au chargement (coquille)
FAMILLES = ("Laser", "Bouclier", "Reparation", "Reacteur", "Protocole", "Missile", "Torpille", "Ogive", "Lanceur")


def _verifier_cles(entree: dict, autorisees: set[str], ou: str) -> None:
    inconnues = entree.keys() - autorisees
    if inconnues:
        raise ValueError(f"{ou} : cles inconnues {sorted(inconnues)}")


@dataclass(frozen=True)
class FiltreCartes:
    """Designe des cartes par leurs caracteristiques (tous les criteres renseignes doivent
    correspondre) : cartes visees par un effet REPETITION ("les Laser de base" : id CRT_7, "les
    cartes de base" : rarete Base...). Une carte precise est designee par son id, jamais par son nom
    affiche, qui peut changer."""

    # Id d'un modele de carte (ex. "CRT_7")
    id: str | None = None
    # Palier de rarete vise
    rarete: RareteCarte | None = None
    # Categorie visee
    categorie: CategorieCarte | None = None
    # Famille visee (champ `famille` des cartes, ex. "Laser" : Protocole laser)
    famille: str | None = None
    # Type de module vise (ex. "MOD_2" : Feu a volonte) : cartes rattachees a un exemplaire de ce
    # type de module, pas cartes dont la liste `modules` le cite (proposition-lanceur-missiles.md 3.9)
    module: str | None = None

    def __post_init__(self):
        if all(critere is None for critere in (self.id, self.rarete, self.categorie, self.famille, self.module)):
            raise ValueError("Un filtre de cartes doit avoir au moins un critere")
        if self.famille is not None and self.famille not in FAMILLES:
            raise ValueError(f"Filtre : famille inconnue {self.famille!r}")

    def correspond(self, carte: "Carte", types_de_module: dict[str, str] | None = None) -> bool:
        """`types_de_module` : type de module (ex. "MOD_2") de chaque exemplaire de la partie (ex.
        "M2"), necessaire au critere `module` ; sans lui, aucune carte ne correspond a ce critere."""
        type_du_module = (types_de_module or {}).get(carte.exemplaire_module)
        return (
            (self.id is None or carte.id == self.id)
            and (self.rarete is None or carte.rarete == self.rarete)
            and (self.categorie is None or carte.categorie == self.categorie)
            and (self.famille is None or carte.famille == self.famille)
            and (self.module is None or type_du_module == self.module)
        )


class SourceBonus(Enum):
    """Ce qui compte pour un bonus calcule (proposition-lanceur-missiles.md 3.11)."""

    # Surcharge du module principal (Missile surcharge : en plus de la Surcharge normale)
    SURCHARGE_JOUEUR = auto()
    # Bouclier du module principal (Laser de contre-charge)
    BOUCLIER_PRINCIPAL = auto()
    # Verrouillage de l'ennemi touche (Missile de precision : en plus du Verrouillage normal)
    VERROUILLAGE_CIBLE = auto()

    @property
    def statut(self) -> Statut:
        """Statut compte par ce bonus (seule correspondance, pour le combat et les simulateurs) :
        sur le module principal, ou sur la cible du coup si sur_la_cible."""
        return {
            SourceBonus.SURCHARGE_JOUEUR: Statut.SURCHARGE,
            SourceBonus.BOUCLIER_PRINCIPAL: Statut.BOUCLIER,
            SourceBonus.VERROUILLAGE_CIBLE: Statut.VERROUILLAGE,
        }[self]

    @property
    def sur_la_cible(self) -> bool:
        """True si le compteur est lu sur l'ennemi touche, False s'il est lu sur le principal."""
        return self == SourceBonus.VERROUILLAGE_CIBLE


@dataclass(frozen=True)
class BonusCalcule:
    """Degats en plus d'un effet DEGATS : facteur x compteur, lu au moment du coup. `facteur` est
    le NOM d'une valeur de la carte. Avec `consomme`, le compteur est remis a 0 au premier coup
    (Laser de contre-charge consomme le bouclier du principal, decision utilisateur 2026-11-22)."""

    par: SourceBonus
    facteur: str
    consomme: bool = False

    @classmethod
    def depuis_dict(cls, entree: dict) -> "BonusCalcule":
        _verifier_cles(entree, CLES_BONUS, "Bonus d'un effet")
        return cls(par=SourceBonus[entree["par"]], facteur=entree["facteur"], consomme=bool(entree.get("consomme", False)))


@dataclass(frozen=True)
class Effet:
    """Un effet d'une carte. Ne contient aucun nombre : `valeur` et `duree` sont des NOMS de
    valeurs de la carte (Carte.valeurs), lues au moment de jouer (Carte.valeur_de)."""

    # Ce que fait l'effet
    nature: NatureEffet
    # Nom de la valeur de la carte utilisee par l'effet ; None pour une nature sans valeur
    valeur: str | None = None
    # Ce que touche l'effet, par rapport a la cible de la carte
    portee: PorteeEffet = PorteeEffet.CIBLE
    # Nom de la valeur donnant la duree en tours, seulement pour une nature de NATURES_A_DUREE
    duree: str | None = None
    # Cartes visees, obligatoire pour REPETITION et interdit sinon
    filtre: FiltreCartes | None = None
    # Degats en plus calcules au moment du coup (Missile surcharge), seulement pour DEGATS
    bonus: "BonusCalcule | None" = None

    def __post_init__(self):
        if (self.valeur is None) != (self.nature in NATURES_SANS_VALEUR):
            raise ValueError(f"{self.nature.name} : valeur nommee manquante ou en trop")
        if self.duree is not None and self.nature not in NATURES_A_DUREE:
            raise ValueError(f"{self.nature.name} n'a pas de duree")
        if (self.nature == NatureEffet.REPETITION) != (self.filtre is not None):
            raise ValueError("Un filtre de cartes est requis pour REPETITION, et seulement pour elle")
        if self.bonus is not None and self.nature != NatureEffet.DEGATS:
            raise ValueError(f"{self.nature.name} : un bonus calcule ne va que sur des DEGATS")

    @property
    def noms_de_valeurs(self) -> list[str]:
        """Noms des valeurs de la carte utilisees par cet effet."""
        facteur = self.bonus.facteur if self.bonus is not None else None
        return [nom for nom in (self.valeur, self.duree, facteur) if nom is not None]

    @classmethod
    def depuis_dict(cls, entree: dict) -> "Effet":
        """Effet a partir d'une entree du tableau "effets" de config/cartes.json."""
        _verifier_cles(entree, CLES_EFFET, f"Effet {entree.get('nature')}")
        filtre = entree.get("filtre")
        if filtre:
            _verifier_cles(filtre, CLES_FILTRE, f"Filtre de l'effet {entree.get('nature')}")
        return cls(
            nature=NatureEffet[entree["nature"]],
            valeur=entree.get("valeur"),
            portee=PorteeEffet[entree.get("portee", "CIBLE")],
            duree=entree.get("duree"),
            filtre=FiltreCartes(
                id=filtre.get("id"),
                rarete=RareteCarte[filtre["rarete"].upper()] if "rarete" in filtre else None,
                categorie=CategorieCarte(filtre["categorie"]) if "categorie" in filtre else None,
                famille=filtre.get("famille"),
                module=filtre.get("module"),
            ) if filtre else None,
            bonus=BonusCalcule.depuis_dict(entree["bonus"]) if "bonus" in entree else None,
        )


_PORTEES_ENNEMIES = tuple(portee for portee in PorteeEffet if portee.camp == Camp.ENNEMI)


def _noms_cites(description: str) -> set[str]:
    """Noms cites entre accolades dans une description ("Inflige {degats} degats" -> {"degats"})."""
    return {nom for _texte, nom, _format, _conversion in Formatter().parse(description) if nom}


@dataclass(eq=False)
class Carte:
    """Une carte de la refonte. eq=False : deux exemplaires du meme modele sont distincts
    (chacun a ses propres munitions, lancements, valeurs et module de rattachement).

    Le modele dit a quels types de module la carte appartient (`modules`, une carte pouvant etre
    commune a plusieurs modules) ; chaque exemplaire est en plus rattache a un exemplaire de module
    de la partie (`exemplaire_module`)."""

    # --- Modele : lu dans config/cartes.json, identique pour tous les exemplaires sauf `valeurs`
    # (propre a chaque exemplaire, pour pouvoir modifier les valeurs d'une seule carte) ---

    # Identifiant du modele (ex. "CRT_7"), commun a tous ses exemplaires
    id: str
    # Nom affiche en jeu (texte affiche : accents autorises, cf. CLAUDE.md)
    nom: str
    # Chemin de l'image de la carte (assets/cartes/)
    image: str
    # Palier de rarete : Base (deck de depart), Commune, Rare, Legendaire
    rarete: RareteCarte
    # Categorie (Attaque, Defense, Buff...), sert aussi aux filtres de REPETITION
    categorie: CategorieCarte
    # Ce que le joueur cible au clic ("Ennemi Unique"...)
    cible: CibleCarte
    # Cout en electricite pour jouer la carte
    cout: int
    # Effets appliques quand la carte est jouee, dans l'ordre (au moins un)
    effets: tuple[Effet, ...]
    # Description affichee, qui cite les valeurs par leur nom entre accolades ("{degats_cible}")
    description: str = ""
    # Valeurs nommees de la carte (ex. {"degats_cible": 15}), utilisees par les effets ; propres a
    # chaque exemplaire (copie), pour pouvoir un jour modifier les valeurs d'une seule carte
    valeurs: dict[str, int] = field(default_factory=dict)
    # Mot-cle Persistante : reste jouable si son module est detruit (specs.md 12.4)
    persistante: bool = False
    # Oui : proposee et jouee ; Non ou Supprimee : jamais proposee (cf. propriete `jouable`)
    jouabilite: Jouabilite = Jouabilite.OUI
    # Ids des types de module qui proposent cette carte (config/modules.json), ex. ("MOD_2",) ;
    # vide : proposee nulle part. Verifies par module.py:charger_modules
    modules: tuple[str, ...] = ()
    # Famille de noms (FAMILLES, ex. "Laser"), seulement sur les cartes qu'un buff peut viser par
    # famille (Protocole laser) ; None ailleurs
    famille: str | None = None
    # True si la carte a ete revue dans la refonte des cartes
    refonte: bool = False
    # Nombre de fois que les effets s'appliquent quand la carte est jouee, au depart de chaque combat
    # (1 d'ordinaire, 2 pour une carte "lancee deux fois")
    lancements_base: int = 1
    # Munitions au depart de chaque combat ; None = illimitee (specs.md 3.6)
    munitions_base: int | None = None

    # --- Etat de cet exemplaire (propre a chaque copie de la carte) ---

    # Munitions restantes pendant le combat ; a 0 la carte est epuisee ; None = illimitee
    munitions_restantes: int | None = None
    # Nombre de lancements en combat : lancements_base, augmente par les effets REPETITION
    # (appliquer_repetition) jusqu'a la fin du combat
    lancements_actuels: int | None = None
    # Valeurs en combat : copie de `valeurs`, modifiable par de futurs effets de bonus (ex. "+2 aux
    # degats des cartes a cible unique") sans toucher au modele
    valeurs_actuelles: dict[str, int] | None = None
    # Exemplaire de module de la partie auquel cette carte est rattachee (ex. "M3"), None tant
    # qu'elle ne l'est pas ; stable meme si la Station deplace le module (specs.md 12.4)
    exemplaire_module: str | None = None

    def __post_init__(self):
        self.effets = tuple(self.effets)
        self.modules = tuple(self.modules)
        if not all(isinstance(module, str) for module in self.modules):
            raise ValueError(f"{self.id} : modules doit etre une liste d'ids de module")
        if self.famille is not None and self.famille not in FAMILLES:
            raise ValueError(f"{self.id} : famille inconnue {self.famille!r} (familles : {', '.join(FAMILLES)})")
        if self.cout < 0:
            raise ValueError(f"{self.id} : cout negatif")
        if not self.effets:
            raise ValueError(f"{self.id} : une carte a au moins un effet")
        if self.lancements_base < 1:
            raise ValueError(f"{self.id} : une carte est lancee au moins une fois")
        if self.munitions_base is not None and self.munitions_base < 1:
            raise ValueError(f"{self.id} : munitions_base doit etre None (illimite) ou >= 1")
        if self.cible.camp == Camp.JOUEUR and any(effet.portee in _PORTEES_ENNEMIES for effet in self.effets):
            raise ValueError(f"{self.id} : portee ennemie sur une carte qui cible le joueur")
        if any(effet.portee == PorteeEffet.AUTRES_ENNEMIS for effet in self.effets) and (
            self.cible != CibleCarte.ENNEMI_UNIQUE
        ):
            raise ValueError(f"{self.id} : 'autres ennemis' suppose une cible Ennemi Unique")
        if any(effet.portee == PorteeEffet.MEME_COLONNE for effet in self.effets) and (
            self.cible != CibleCarte.ENNEMI_UNIQUE
        ):
            raise ValueError(f"{self.id} : 'meme colonne' suppose une cible Ennemi Unique")
        for effet in self.effets:
            if effet.nature in NATURES_DU_PRINCIPAL and not (
                effet.portee == PorteeEffet.MODULE_PRINCIPAL
                or (effet.portee == PorteeEffet.CIBLE and self.cible == CibleCarte.MODULE_PRINCIPAL)
            ):
                raise ValueError(f"{self.id} : {effet.nature.name} ne vise que le module principal")
            camp_touche = effet.portee.camp or self.cible.camp
            camp_nature = CAMP_PAR_NATURE.get(effet.nature)
            if camp_nature is not None and camp_nature != camp_touche:
                raise ValueError(
                    f"{self.id} : {effet.nature.name} ne peut pas toucher le camp {camp_touche.name.lower()}"
                )
        self._verifier_valeurs()
        if self.munitions_restantes is None:
            self.munitions_restantes = self.munitions_base
        if self.lancements_actuels is None:
            self.lancements_actuels = self.lancements_base
        if self.valeurs_actuelles is None:
            self.valeurs_actuelles = dict(self.valeurs)

    def _verifier_valeurs(self) -> None:
        """Chaque nom utilise (effets, description) existe, et chaque valeur sert a un effet."""
        if any(valeur < 0 for valeur in self.valeurs.values()):
            raise ValueError(f"{self.id} : valeur negative")
        utilisees = {nom for effet in self.effets for nom in effet.noms_de_valeurs}
        inconnues = (utilisees | _noms_cites(self.description)) - self.valeurs.keys()
        if inconnues:
            raise ValueError(f"{self.id} : valeurs inconnues {sorted(inconnues)}")
        inutilisees = self.valeurs.keys() - utilisees
        if inutilisees:
            raise ValueError(f"{self.id} : valeurs utilisees par aucun effet {sorted(inutilisees)}")
        if any(self.valeurs[effet.duree] < 1 for effet in self.effets if effet.duree is not None):
            raise ValueError(f"{self.id} : une duree vaut au moins 1 tour")

    # --- Exemplaires ---

    def copie(self, exemplaire_module: str | None = None) -> "Carte":
        """Nouvel exemplaire independant, munitions, lancements et valeurs de depart. Rattache a
        `exemplaire_module` s'il est donne, sinon au meme exemplaire de module que cette carte.
        Rien de modifiable n'est partage avec la carte copiee : `valeurs` et `valeurs_actuelles`
        sont des dictionnaires propres a chaque exemplaire ; `effets` est partage, mais ses Effet
        sont figes (frozen)."""
        return dataclasses.replace(
            self,
            exemplaire_module=exemplaire_module if exemplaire_module is not None else self.exemplaire_module,
            munitions_restantes=self.munitions_base,
            lancements_actuels=self.lancements_base,
            valeurs=dict(self.valeurs),
            valeurs_actuelles=dict(self.valeurs),
        )

    # --- Valeurs ---

    def valeur_de(self, effet: Effet) -> int | None:
        """Valeur actuelle utilisee par cet effet de la carte (None pour une nature sans valeur)."""
        return self.valeurs_actuelles[effet.valeur] if effet.valeur is not None else None

    def duree_de(self, effet: Effet) -> int | None:
        """Duree actuelle, en tours, de cet effet de la carte (None s'il n'en a pas)."""
        return self.valeurs_actuelles[effet.duree] if effet.duree is not None else None

    def description_affichee(self) -> str:
        """Description, chaque {nom} remplace par la valeur actuelle correspondante."""
        return self.description.format_map(self.valeurs_actuelles)

    # --- Munitions (specs.md 3.6) ---

    @property
    def est_epuisee(self) -> bool:
        return self.munitions_restantes is not None and self.munitions_restantes <= 0

    def consommer_munition(self) -> bool:
        """A appeler quand la carte est jouee. Renvoie True si elle est desormais epuisee."""
        if self.munitions_restantes is not None:
            self.munitions_restantes -= 1
        return self.est_epuisee

    # --- Module detruit (specs.md 3.4, 12.4) ---

    def jouable_si_module_detruit(self) -> bool:
        """False : la carte part en pile Hors service tant que son module est detruit."""
        return self.persistante

    @property
    def jouable(self) -> bool:
        """True si la carte peut etre proposee et jouee (jouabilite Oui)."""
        return self.jouabilite == Jouabilite.OUI

    # --- Lecture JSON (format de config/cartes.json) ---

    @classmethod
    def depuis_dict(cls, entree: dict) -> "Carte":
        """Carte a partir d'une entree de config/cartes.json. Toute erreur de lecture (cle
        manquante ou inconnue, texte inconnu dans une enumeration, effet invalide) est signalee avec
        l'id de la carte, pour retrouver facilement la faute dans le JSON ecrit a la main."""
        carte = f"Carte {entree.get('id', '?')}"
        try:
            _verifier_cles(entree, CLES_CARTE, carte)
            champs = dict(
                id=entree["id"],
                nom=entree["nom"],
                image=entree["image"],
                rarete=RareteCarte[entree["rarete"].upper()],
                categorie=CategorieCarte(entree["categorie"]),
                cible=CibleCarte(entree["cible"]),
                cout=entree["cout"],
                effets=tuple(Effet.depuis_dict(effet) for effet in entree["effets"]),
                description=entree.get("description", ""),
                valeurs=dict(entree.get("valeurs", {})),
                persistante=entree.get("persistante", False),
                jouabilite=_jouabilite(entree.get("jouable", "oui")),
                modules=tuple(entree.get("modules", [])),
                famille=entree.get("famille"),
                refonte=entree.get("refonte", False),
                lancements_base=entree.get("lancements", 1),
                munitions_base=entree.get("munition"),
            )
        except KeyError as erreur:
            raise ValueError(f"{carte} : cle manquante ou texte inconnu {erreur}") from erreur
        except ValueError as erreur:
            raise ValueError(erreur if str(erreur).startswith(carte) else f"{carte} : {erreur}") from erreur
        return cls(**champs)


def _jouabilite(valeur) -> Jouabilite:
    """Champ "jouable" du JSON : "oui", "non" ou "supprimee" (un booleen est refuse, ancien
    format)."""
    try:
        return Jouabilite(valeur)
    except ValueError:
        raise ValueError(f"jouable doit valoir \"oui\", \"non\" ou \"supprimee\" ({valeur!r})") from None


def charger_cartes(fichier: Path = FICHIER_CARTES) -> dict[str, Carte]:
    """Charge config/cartes.json. Renvoie un dict id de carte -> modele de carte ; un id en
    double est refuse."""
    donnees = json.loads(fichier.read_text(encoding="utf-8"))
    cartes = {}
    for entree in donnees["cartes"]:
        carte = Carte.depuis_dict(entree)
        if carte.id in cartes:
            raise ValueError(f"config/cartes.json : carte {carte.id} en double")
        cartes[carte.id] = carte
    return cartes


def appliquer_repetition(
    effet: Effet, supplement: int, cartes: Iterable[Carte], types_de_module: dict[str, str] | None = None,
) -> int:
    """Effet REPETITION joue : chaque carte visee par son filtre est lancee `supplement` fois de plus
    (valeur de l'effet sur la carte jouee : carte.valeur_de(effet)), pour le reste du combat.
    `cartes` : toutes les cartes du combat, toutes piles confondues (main, pioche, defausse,
    epuisees, Hors service), pour qu'une carte piochee plus tard soit concernee elle aussi.
    `types_de_module` : type de module de chaque exemplaire, pour un filtre par module
    (FiltreCartes.correspond). Renvoie le nombre de cartes modifiees."""
    if effet.nature != NatureEffet.REPETITION:
        raise ValueError(f"Effet {effet.nature.name} : seul un effet REPETITION modifie les lancements")
    visees = [carte for carte in cartes if effet.filtre.correspond(carte, types_de_module)]
    for carte in visees:
        carte.lancements_actuels += supplement
    return len(visees)


# --- Ecriture de config/cartes.json (outil d'edition des cartes, specs/outil-editeur-cartes.md) ---

# Ordre des cles dans le fichier, comme ecrit a la main ; une cle absente de ces listes est ecrite
# apres les autres
ORDRE_CLES_CARTE = (
    "id", "nom", "image", "rarete", "categorie", "cible", "modules", "famille", "cout", "munition", "lancements",
    "persistante", "jouable", "refonte", "description", "valeurs", "effets",
)
ORDRE_CLES_EFFET = ("nature", "valeur", "portee", "duree", "filtre")
ORDRE_CLES_FILTRE = ("id", "rarete", "categorie", "famille", "module")


def _trier_cles(entree: dict, ordre: tuple[str, ...]) -> dict:
    connues = [cle for cle in ordre if cle in entree]
    return {cle: entree[cle] for cle in connues + [cle for cle in entree if cle not in ordre]}


def _sur_une_ligne(valeur) -> str:
    """Objet ou liste sur une ligne, au style de cartes.json : { "a": 1, "b": 2 }, ["MOD_1"]."""
    if isinstance(valeur, dict):
        if not valeur:
            return "{}"
        return "{ " + ", ".join(f"{json.dumps(cle, ensure_ascii=False)}: {_sur_une_ligne(v)}" for cle, v in valeur.items()) + " }"
    if isinstance(valeur, list):
        return "[" + ", ".join(_sur_une_ligne(v) for v in valeur) + "]"
    return json.dumps(valeur, ensure_ascii=False)


def _effet_trie(effet) -> dict:
    if not isinstance(effet, dict):
        return effet
    effet = _trier_cles(effet, ORDRE_CLES_EFFET)
    if isinstance(effet.get("filtre"), dict):
        effet["filtre"] = _trier_cles(effet["filtre"], ORDRE_CLES_FILTRE)
    return effet


def cartes_vers_texte_json(entrees: list[dict]) -> str:
    """Texte complet de config/cartes.json pour ces entrees, dans la mise en forme du fichier ecrit
    a la main (une cle par ligne, valeurs et effets sur une ligne) : un fichier exporte par l'outil
    d'edition remplace l'original avec un diff limite aux vrais changements."""
    blocs = []
    for entree in entrees:
        entree = _trier_cles(entree, ORDRE_CLES_CARTE)
        lignes = []
        for cle, valeur in entree.items():
            if cle == "effets" and isinstance(valeur, list) and valeur:
                effets = ",\n".join("        " + _sur_une_ligne(_effet_trie(effet)) for effet in valeur)
                texte = "[\n" + effets + "\n      ]"
            else:
                texte = _sur_une_ligne(valeur)
            lignes.append(f'      {json.dumps(cle)}: {texte}')
        blocs.append("    {\n" + ",\n".join(lignes) + "\n    }")
    return '{\n  "cartes": [\n' + ",\n".join(blocs) + "\n  ]\n}\n"
