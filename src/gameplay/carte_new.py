"""
Carte de la refonte (CarteNew, nom provisoire) : modele de donnees cible de la refonte des cartes
(specs/refonte-buffs-debuffs.md, specs/refonte-modules.md, colonne "Refonte" de
specs/cartes.xlsx). Pas encore branchee au moteur : coexiste avec carte.py:Carte, qu'elle
remplacera une fois relue et validee.

Differences avec Carte :
- une carte porte une liste d'EFFETS (et non une seule valeur) : cartes a deux valeurs (Missiles :
  X sur la cible et Y sur les autres ennemis ; Torpille : X sur la ligne avant, Y sur l'arriere) ;
- chaque nature d'effet declare comment elle se cumule (Cumul) : l'incendie (poison de Slay the
  Spire) additionne son intensite, qui decroit de 1 par tour ;
- une carte peut etre lancee plusieurs fois (`lancements`) ; les cartes "les cartes X sont lancees
  N fois de plus" (Salve laser, Protocole d'urgence, Bouclier stabilise) sont un effet REPETITION
  dont le FiltreCartes designe les cartes visees : il augmente leur `lancements` jusqu'a la fin du
  combat (appliquer_repetition) ;
- mot-cle Persistante et rattachement a un exemplaire de module (emplacement) : une carte dont le
  module est detruit part en pile Hors service, sauf si elle est Persistante
  (specs/refonte-modules.md 3.3 a 3.5) ;
- la cible reprend le vocabulaire du registre des cartes ("Ennemi Unique", "Module Tous"...).
"""

import dataclasses
import re
from dataclasses import dataclass
from enum import Enum, auto

from src.gameplay.carte import RareteCarte


class CategorieCarte(Enum):
    """Categorie d'une carte (colonne "Categorie" du registre, specs.md 7.1)."""

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


class CibleCarteNew(Enum):
    """Cible d'une carte (colonne "Cible" du registre). Une cible "unique" ou "colonne" depend de
    la case cliquee ; les autres touchent un ensemble fixe, mais demandent quand meme un clic de
    confirmation sur une case du bon camp (specs.md 8.3, identique PC et web)."""

    ENNEMI_UNIQUE = "Ennemi Unique"
    ENNEMI_COLONNE = "Ennemi Colonne"
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
        return self in (CibleCarteNew.ENNEMI_UNIQUE, CibleCarteNew.ENNEMI_COLONNE, CibleCarteNew.MODULE_UNIQUE)


class Cumul(Enum):
    """Comment un effet se combine avec le meme effet deja actif sur l'entite visee."""

    # Applique une fois, rien ne reste actif (degats, reparation, gain d'electricite...)
    INSTANTANE = auto()
    # L'intensite s'additionne et decroit de 1 a chaque tour (incendie, poison de Slay the Spire)
    INTENSITE_DECROISSANTE = auto()
    # L'intensite s'additionne et ne decroit jamais jusqu'a la fin du combat (Force de Slay the
    # Spire) : Salve laser et ses semblables
    INTENSITE_SANS_DECROISSANCE = auto()
    # La duree s'additionne, l'intensite reste celle de la carte (Vulnerable de Slay the Spire)
    DUREE = auto()
    # Etat consomme par un evenement, pas par le temps (Leurre, Bouclier miroir)
    JUSQU_A_CONSOMMATION = auto()
    # Bouclier brut : compteur avec sa propre regle de dissipation (specs.md 3.5, en refonte)
    BOUCLIER = auto()


class NatureEffet(Enum):
    """Ce que fait un effet. Le Cumul de chaque nature est donne par CUMUL_PAR_NATURE."""

    DEGATS = auto()
    BOUCLIER = auto()
    REPARATION = auto()
    INCENDIE = auto()
    VULNERABILITE = auto()
    REDUCTION_DEGATS = auto()
    BOUCLIER_MIROIR = auto()
    ANNULATION_PROCHAINE_ATTAQUE = auto()
    REDIRECTION_CIBLE = auto()
    GAIN_ELECTRICITE = auto()
    PIOCHE = auto()
    # Les cartes designees par le filtre de l'effet sont lancees `valeur` fois de plus, jusqu'a la
    # fin du combat (appliquer_repetition)
    REPETITION = auto()


# INCENDIE : decision utilisateur (registre des cartes, note de Tir incendiaire). REPETITION : dure
# tout le combat et se cumule (decision utilisateur). VULNERABILITE, REDUCTION_DEGATS,
# BOUCLIER_MIROIR : proposition du brouillon de refonte des buffs (refonte-buffs-debuffs.md
# 7.3/7.4), a valider. Seulement les effets des cartes du joueur : les mecaniques propres aux
# ennemis (ex. Augmentation de degats du Boss) sont gerees en dehors des cartes (decision
# utilisateur).
CUMUL_PAR_NATURE = {
    NatureEffet.DEGATS: Cumul.INSTANTANE,
    NatureEffet.BOUCLIER: Cumul.BOUCLIER,
    NatureEffet.REPARATION: Cumul.INSTANTANE,
    NatureEffet.INCENDIE: Cumul.INTENSITE_DECROISSANTE,
    NatureEffet.VULNERABILITE: Cumul.DUREE,
    NatureEffet.REDUCTION_DEGATS: Cumul.DUREE,
    NatureEffet.BOUCLIER_MIROIR: Cumul.JUSQU_A_CONSOMMATION,
    NatureEffet.ANNULATION_PROCHAINE_ATTAQUE: Cumul.JUSQU_A_CONSOMMATION,
    NatureEffet.REDIRECTION_CIBLE: Cumul.DUREE,
    NatureEffet.GAIN_ELECTRICITE: Cumul.INSTANTANE,
    NatureEffet.PIOCHE: Cumul.INSTANTANE,
    NatureEffet.REPETITION: Cumul.INTENSITE_SANS_DECROISSANCE,
}


class PorteeEffet(Enum):
    """Ce que touche un effet, par rapport a la cible de la carte."""

    # La cible de la carte (ou tout l'ensemble vise pour une cible multiple)
    CIBLE = auto()
    # Tous les ennemis vivants sauf la cible (Missiles : X sur la cible, Y sur les autres)
    AUTRES_ENNEMIS = auto()
    # Colonne avant / arriere de la flotte ennemie (Torpille : X a l'avant, Y a l'arriere)
    COLONNE_AVANT_ENNEMIE = auto()
    COLONNE_ARRIERE_ENNEMIE = auto()


@dataclass(frozen=True)
class FiltreCartes:
    """Designe des cartes par leurs caracteristiques (tous les criteres renseignes doivent
    correspondre) : cartes visees par un effet REPETITION ("les Laser de base", "les cartes de
    base"...)."""

    nom: str | None = None
    rarete: RareteCarte | None = None
    categorie: CategorieCarte | None = None

    def __post_init__(self):
        if self.nom is None and self.rarete is None and self.categorie is None:
            raise ValueError("Un filtre de cartes doit avoir au moins un critere")

    def correspond(self, carte: "CarteNew") -> bool:
        return (
            (self.nom is None or carte.nom == self.nom)
            and (self.rarete is None or carte.rarete == self.rarete)
            and (self.categorie is None or carte.categorie == self.categorie)
        )


@dataclass(frozen=True)
class Effet:
    """Un effet d'une carte. `duree` : nombre de tours pour un effet a duree (Cumul.DUREE ou un
    bouclier "pendant Y tours"), None sinon. `filtre` : obligatoire pour REPETITION, interdit
    sinon."""

    nature: NatureEffet
    valeur: int
    portee: PorteeEffet = PorteeEffet.CIBLE
    duree: int | None = None
    filtre: FiltreCartes | None = None

    def __post_init__(self):
        if self.valeur < 0:
            raise ValueError(f"Valeur d'effet negative : {self.valeur}")
        if self.duree is not None and self.duree < 1:
            raise ValueError(f"Duree d'effet invalide : {self.duree}")
        if (self.nature == NatureEffet.REPETITION) != (self.filtre is not None):
            raise ValueError("Un filtre de cartes est requis pour REPETITION, et seulement pour elle")

    @property
    def cumul(self) -> Cumul:
        return CUMUL_PAR_NATURE[self.nature]


_PORTEES_ENNEMIES = (PorteeEffet.AUTRES_ENNEMIS, PorteeEffet.COLONNE_AVANT_ENNEMIE, PorteeEffet.COLONNE_ARRIERE_ENNEMIE)
_MOT_X = re.compile(r"\bX\b")
_MOT_Y = re.compile(r"\bY\b")


@dataclass(eq=False)
class CarteNew:
    """Une carte de la refonte. eq=False : deux exemplaires du meme modele sont distincts (comme
    Carte, chacun a ses propres munitions et son propre module de rattachement).

    `module_origine` : module dont la carte fait partie (colonne "Module" du registre).
    `emplacement` : exemplaire de module auquel cet exemplaire de carte est rattache dans une
    partie ("base", "avant_gauche"...), None tant qu'il ne l'est pas (specs/refonte-modules.md
    3.3 : deux exemplaires du meme module ont chacun leurs cartes).
    `persistante` : reste jouable si son module est detruit (mot-cle, refonte-modules.md 3.5).
    `lancements` : nombre de fois que les effets de la carte s'appliquent quand elle est jouee (1
    d'ordinaire, 2 pour une carte "lancee deux fois"). Augmente en combat par les effets
    REPETITION (appliquer_repetition) ; chaque combat recree ses cartes a partir du deck de la
    partie, donc l'augmentation disparait d'elle-meme a la fin du combat."""

    id: str
    nom: str
    image: str
    module_origine: str
    rarete: RareteCarte
    categorie: CategorieCarte
    cible: CibleCarteNew
    cout: int
    effets: tuple[Effet, ...]
    description: str = ""
    munitions_max: int | None = None
    persistante: bool = False
    lancements: int = 1
    emplacement: str | None = None
    munitions_restantes: int | None = None

    def __post_init__(self):
        self.effets = tuple(self.effets)
        if self.cout < 0:
            raise ValueError(f"{self.id} : cout negatif")
        if not self.effets:
            raise ValueError(f"{self.id} : une carte a au moins un effet")
        if self.lancements < 1:
            raise ValueError(f"{self.id} : une carte est lancee au moins une fois")
        if self.munitions_max is not None and self.munitions_max < 1:
            raise ValueError(f"{self.id} : munitions_max doit etre None (illimite) ou >= 1")
        if self.cible.camp == Camp.JOUEUR and any(effet.portee in _PORTEES_ENNEMIES for effet in self.effets):
            raise ValueError(f"{self.id} : portee ennemie sur une carte qui cible le joueur")
        if any(effet.portee == PorteeEffet.AUTRES_ENNEMIS for effet in self.effets) and (
            self.cible != CibleCarteNew.ENNEMI_UNIQUE
        ):
            raise ValueError(f"{self.id} : 'autres ennemis' suppose une cible Ennemi Unique")
        if self.munitions_restantes is None:
            self.munitions_restantes = self.munitions_max

    # --- Exemplaires ---

    def copie(self) -> "CarteNew":
        """Nouvel exemplaire independant : munitions pleines, meme rattachement."""
        return dataclasses.replace(self, munitions_restantes=self.munitions_max)

    def rattachee_a(self, emplacement: str) -> "CarteNew":
        """Nouvel exemplaire rattache a l'exemplaire de module de cet emplacement."""
        return dataclasses.replace(self, emplacement=emplacement, munitions_restantes=self.munitions_max)

    # --- Munitions (specs.md 3.6) ---

    @property
    def est_epuisee(self) -> bool:
        return self.munitions_restantes is not None and self.munitions_restantes <= 0

    def consommer_munition(self) -> bool:
        """A appeler quand la carte est jouee. Renvoie True si elle est desormais epuisee."""
        if self.munitions_restantes is not None:
            self.munitions_restantes -= 1
        return self.est_epuisee

    # --- Module detruit (specs/refonte-modules.md 3.3 a 3.5) ---

    def jouable_si_module_detruit(self) -> bool:
        """False : la carte part en pile Hors service tant que son module est detruit."""
        return self.persistante

    # --- Texte ---

    @property
    def x(self) -> int:
        """Valeur X du registre : celle du premier effet."""
        return self.effets[0].valeur

    @property
    def y(self) -> int | None:
        """Valeur Y du registre : celle du second effet, sinon la duree du premier."""
        return self.effets[1].valeur if len(self.effets) > 1 else self.effets[0].duree

    def description_affichee(self) -> str:
        """Description du registre, X et Y remplaces par leurs valeurs."""
        texte = _MOT_X.sub(str(self.x), self.description)
        return _MOT_Y.sub(str(self.y), texte) if self.y is not None else texte

    # --- Lecture / ecriture JSON (format propose pour config/cartes.json) ---

    @classmethod
    def depuis_dict(cls, entree: dict) -> "CarteNew":
        return cls(
            id=entree["id"],
            nom=entree["nom"],
            image=entree["image"],
            module_origine=entree["module_origine"],
            rarete=RareteCarte[entree["rarete"].upper()],
            categorie=CategorieCarte(entree["categorie"]),
            cible=CibleCarteNew(entree["cible"]),
            cout=entree["cout"],
            effets=tuple(_effet_depuis_dict(effet) for effet in entree["effets"]),
            description=entree.get("description", ""),
            munitions_max=entree.get("munition"),
            persistante=entree.get("persistante", False),
            lancements=entree.get("lancements", 1),
        )

    def vers_dict(self) -> dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "image": self.image,
            "module_origine": self.module_origine,
            "rarete": self.rarete.name.capitalize(),
            "categorie": self.categorie.value,
            "cible": self.cible.value,
            "cout": self.cout,
            "munition": self.munitions_max,
            "persistante": self.persistante,
            "lancements": self.lancements,
            "description": self.description,
            "effets": [_effet_vers_dict(effet) for effet in self.effets],
        }


def appliquer_repetition(effet: Effet, cartes) -> int:
    """Effet REPETITION joue : chaque carte visee par son filtre est lancee `effet.valeur` fois de
    plus pour le reste du combat. `cartes` : toutes les cartes du combat, toutes piles confondues
    (main, pioche, defausse, epuisees, Hors service), pour qu'une carte piochee plus tard soit
    concernee elle aussi. Renvoie le nombre de cartes modifiees."""
    if effet.nature != NatureEffet.REPETITION:
        raise ValueError(f"Effet {effet.nature.name} : seul un effet REPETITION modifie les lancements")
    visees = [carte for carte in cartes if effet.filtre.correspond(carte)]
    for carte in visees:
        carte.lancements += effet.valeur
    return len(visees)


def _effet_depuis_dict(entree: dict) -> Effet:
    filtre = entree.get("filtre")
    return Effet(
        nature=NatureEffet[entree["nature"]],
        valeur=entree["valeur"],
        portee=PorteeEffet[entree.get("portee", "CIBLE")],
        duree=entree.get("duree"),
        filtre=FiltreCartes(
            nom=filtre.get("nom"),
            rarete=RareteCarte[filtre["rarete"].upper()] if "rarete" in filtre else None,
            categorie=CategorieCarte(filtre["categorie"]) if "categorie" in filtre else None,
        ) if filtre else None,
    )


def _effet_vers_dict(effet: Effet) -> dict:
    resultat = {"nature": effet.nature.name, "valeur": effet.valeur}
    if effet.portee != PorteeEffet.CIBLE:
        resultat["portee"] = effet.portee.name
    if effet.duree is not None:
        resultat["duree"] = effet.duree
    if effet.filtre is not None:
        filtre = {}
        if effet.filtre.nom is not None:
            filtre["nom"] = effet.filtre.nom
        if effet.filtre.rarete is not None:
            filtre["rarete"] = effet.filtre.rarete.name.capitalize()
        if effet.filtre.categorie is not None:
            filtre["categorie"] = effet.filtre.categorie.value
        resultat["filtre"] = filtre
    return resultat
