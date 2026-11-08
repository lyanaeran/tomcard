"""
Carte de la refonte (CarteNew, nom provisoire) : modele de donnees cible de la refonte des cartes
(specs/refonte-buffs-debuffs.md, specs/refonte-modules.md). Source de verite :
config/carte_new.json (charger_cartes_new). Relue et validee par l'utilisateur le 2026-11-08.
Pas encore branchee au moteur : coexiste avec carte.py:Carte (config/cartes.json), qu'elle
remplacera au branchement de la refonte.

Differences avec Carte :
- une carte porte des VALEURS NOMMEES (ex. {"degats_cible": 15, "degats_autres": 6}) et une liste
  d'EFFETS qui y renvoient par leur nom : plusieurs valeurs par carte (Missiles : degats sur la
  cible et sur les autres ennemis), et une description qui les cite entre accolades ("Inflige
  {degats_cible} degats...") ;
- chaque nature d'effet declare comment elle se cumule (Cumul) : l'incendie (poison de Slay the
  Spire) et le bouclier additionnent leur intensite, qui decroit de 1 par tour ;
- une carte peut etre lancee plusieurs fois (`lancements_base`) ; les cartes "les cartes X sont
  lancees N fois de plus" (Salve laser, Protocole d'urgence, Bouclier stabilise) sont un effet
  REPETITION dont le FiltreCartes designe les cartes visees : il augmente leur `lancements_actuels`
  jusqu'a la fin du combat (appliquer_repetition) ;
- mot-cle Persistante et rattachement a un exemplaire de module (exemplaire_module) : une carte dont
  le module est detruit part en pile Hors service, sauf si elle est Persistante
  (specs/refonte-modules.md 3.3 a 3.5) ;
- la cible reprend le vocabulaire du registre des cartes ("Ennemi Unique", "Module Tous"...).
"""

import dataclasses
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from string import Formatter

from src.gameplay.carte import RareteCarte

FICHIER_CARTES_NEW = Path(__file__).resolve().parents[2] / "config" / "carte_new.json"


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


class CibleCarteNew(Enum):
    """Cible d'une carte. Une cible "unique" ou "colonne" depend de la case cliquee ; les autres
    touchent un ensemble fixe, mais demandent quand meme un clic de confirmation sur une case du bon
    camp (specs.md 8.3, identique PC et web)."""

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
    # L'intensite s'additionne et decroit de 1 a chaque tour (incendie, poison de Slay the Spire ;
    # bouclier, decision utilisateur)
    INTENSITE_DECROISSANTE = auto()
    # L'intensite s'additionne et ne decroit jamais jusqu'a la fin du combat (Force de Slay the
    # Spire) : Salve laser et ses semblables
    INTENSITE_SANS_DECROISSANCE = auto()
    # La duree s'additionne, l'intensite reste celle de la carte (Vulnerable de Slay the Spire)
    DUREE = auto()
    # Etat consomme par un evenement, pas par le temps (Leurre, Bouclier miroir)
    JUSQU_A_CONSOMMATION = auto()


class NatureEffet(Enum):
    """Ce que fait un effet. `valeur` designe la valeur nommee de la carte que l'effet utilise. Le
    Cumul de chaque nature est donne par CUMUL_PAR_NATURE."""

    # Retire `valeur` PV (apres le bouclier) a chaque ennemi touche (Laser, Missiles, Bombardement)
    DEGATS = auto()
    # Ajoute `valeur` de bouclier a chaque module touche, absorbe avant les PV ; le bouclier baisse
    # de 1 a chaque tour, sans autre notion de duree (Bouclier, Proteger le vaisseau, Blindage cible)
    BOUCLIER = auto()
    # Rend `valeur` PV au module touche, sans depasser ses PV max (Reparation)
    REPARATION = auto()
    # Ajoute `valeur` points d'incendie a l'ennemi : il subit autant de degats a chaque tour, puis
    # l'incendie baisse de 1 (poison de Slay the Spire : Tir incendiaire, Embrasement)
    INCENDIE = auto()
    # L'ennemi subit `valeur` % de degats en plus (Breche, Ligne avant)
    VULNERABILITE = auto()
    # L'ennemi inflige `valeur` degats de moins par attaque (Tordre le canon)
    REDUCTION_DEGATS = auto()
    # Les degats recus par le module touche sont renvoyes a l'attaquant, jusqu'a `valeur` (Renvoi)
    BOUCLIER_MIROIR = auto()
    # Annule entierement la prochaine attaque recue par le module touche, sans valeur (Leurre)
    ANNULATION_PROCHAINE_ATTAQUE = auto()
    # L'ennemi touche attaque un de ses allies au hasard au lieu du joueur, sans valeur (Tir allie)
    REDIRECTION_CIBLE = auto()
    # Donne `valeur` electricite en plus pour ce tour (Surcharge temporaire)
    GAIN_ELECTRICITE = auto()
    # Pioche `valeur` cartes en plus (Boost)
    PIOCHE = auto()
    # Les cartes designees par le filtre de l'effet sont lancees `valeur` fois de plus, jusqu'a la
    # fin du combat (appliquer_repetition : Salve laser, Protocole d'urgence, Bouclier stabilise)
    REPETITION = auto()


# Natures sans valeur numerique : leur effet ne renvoie a aucune valeur nommee de la carte
NATURES_SANS_VALEUR = {NatureEffet.ANNULATION_PROCHAINE_ATTAQUE, NatureEffet.REDIRECTION_CIBLE}

# INCENDIE : decision utilisateur (registre des cartes, note de Tir incendiaire). BOUCLIER : baisse
# de 1 par tour et c'est tout, sans duree (decision utilisateur). REPETITION : dure
# tout le combat et se cumule (decision utilisateur). VULNERABILITE, REDUCTION_DEGATS,
# BOUCLIER_MIROIR : proposition du brouillon de refonte des buffs (refonte-buffs-debuffs.md
# 7.3/7.4), a valider. Seulement les effets des cartes du joueur : les mecaniques propres aux
# ennemis (ex. Augmentation de degats du Boss) sont gerees en dehors des cartes (decision
# utilisateur).
CUMUL_PAR_NATURE = {
    NatureEffet.DEGATS: Cumul.INSTANTANE,
    NatureEffet.BOUCLIER: Cumul.INTENSITE_DECROISSANTE,
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
    # Tous les ennemis vivants sauf la cible (Missiles : degats sur la cible, puis sur les autres)
    AUTRES_ENNEMIS = auto()
    # Colonne avant / arriere de la flotte ennemie (Torpille : degats a l'avant, puis a l'arriere)
    COLONNE_AVANT_ENNEMIE = auto()
    COLONNE_ARRIERE_ENNEMIE = auto()


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

    def __post_init__(self):
        if self.id is None and self.rarete is None and self.categorie is None:
            raise ValueError("Un filtre de cartes doit avoir au moins un critere")

    def correspond(self, carte: "CarteNew") -> bool:
        return (
            (self.id is None or carte.id == self.id)
            and (self.rarete is None or carte.rarete == self.rarete)
            and (self.categorie is None or carte.categorie == self.categorie)
        )


@dataclass(frozen=True)
class Effet:
    """Un effet d'une carte. Ne contient aucun nombre : `valeur` et `duree` sont des NOMS de
    valeurs de la carte (CarteNew.valeurs), lues au moment de jouer (CarteNew.valeur_de)."""

    # Ce que fait l'effet
    nature: NatureEffet
    # Nom de la valeur de la carte utilisee par l'effet ; None pour une nature sans valeur
    valeur: str | None = None
    # Ce que touche l'effet, par rapport a la cible de la carte
    portee: PorteeEffet = PorteeEffet.CIBLE
    # Nom de la valeur donnant la duree en tours, seulement pour un effet a duree (Cumul.DUREE)
    duree: str | None = None
    # Cartes visees, obligatoire pour REPETITION et interdit sinon
    filtre: FiltreCartes | None = None

    def __post_init__(self):
        if (self.valeur is None) != (self.nature in NATURES_SANS_VALEUR):
            raise ValueError(f"{self.nature.name} : valeur nommee manquante ou en trop")
        if self.duree is not None and self.cumul != Cumul.DUREE:
            raise ValueError(f"{self.nature.name} n'a pas de duree")
        if (self.nature == NatureEffet.REPETITION) != (self.filtre is not None):
            raise ValueError("Un filtre de cartes est requis pour REPETITION, et seulement pour elle")

    @property
    def cumul(self) -> Cumul:
        return CUMUL_PAR_NATURE[self.nature]

    @property
    def noms_de_valeurs(self) -> list[str]:
        """Noms des valeurs de la carte utilisees par cet effet."""
        return [nom for nom in (self.valeur, self.duree) if nom is not None]

    @classmethod
    def depuis_dict(cls, entree: dict) -> "Effet":
        """Effet a partir d'une entree du tableau "effets" de config/carte_new.json."""
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
            ) if filtre else None,
        )


# Cles autorisees dans config/carte_new.json : une cle inconnue (ex. faute de frappe "persistant")
# est refusee au chargement plutot qu'ignoree
CLES_CARTE = {
    "id", "nom", "image", "rarete", "categorie", "cible", "cout", "munition", "lancements",
    "persistante", "jouable", "refonte", "description", "valeurs", "effets",
}
CLES_EFFET = {"nature", "valeur", "portee", "duree", "filtre"}
CLES_FILTRE = {"id", "rarete", "categorie"}


def _verifier_cles(entree: dict, autorisees: set[str], ou: str) -> None:
    inconnues = entree.keys() - autorisees
    if inconnues:
        raise ValueError(f"{ou} : cles inconnues {sorted(inconnues)}")


_PORTEES_ENNEMIES = (PorteeEffet.AUTRES_ENNEMIS, PorteeEffet.COLONNE_AVANT_ENNEMIE, PorteeEffet.COLONNE_ARRIERE_ENNEMIE)


def _noms_cites(description: str) -> set[str]:
    """Noms cites entre accolades dans une description ("Inflige {degats} degats" -> {"degats"})."""
    return {nom for _texte, nom, _format, _conversion in Formatter().parse(description) if nom}


@dataclass(eq=False)
class CarteNew:
    """Une carte de la refonte. eq=False : deux exemplaires du meme modele sont distincts (comme
    Carte, chacun a ses propres munitions, lancements, valeurs et module de rattachement).

    Le type du module n'est pas stocke sur la carte : il se lit sur l'exemplaire de module dans la
    partie, et les cartes de chaque type de module sont listees dans config/modules.json (une carte
    peut etre commune a plusieurs modules)."""

    # --- Modele : identique pour tous les exemplaires, lu dans config/carte_new.json ---

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
    cible: CibleCarteNew
    # Cout en electricite pour jouer la carte
    cout: int
    # Effets appliques quand la carte est jouee, dans l'ordre (au moins un)
    effets: tuple[Effet, ...]
    # Description affichee, qui cite les valeurs par leur nom entre accolades ("{degats_cible}")
    description: str = ""
    # Valeurs nommees de la carte (ex. {"degats_cible": 15}), utilisees par les effets ; propres a
    # chaque exemplaire (copie), pour pouvoir un jour modifier les valeurs d'une seule carte
    valeurs: dict[str, int] = field(default_factory=dict)
    # Mot-cle Persistante : reste jouable si son module est detruit (refonte-modules.md 3.5)
    persistante: bool = False
    # True si le moteur sait executer tous les effets de la carte
    jouable: bool = True
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
    # qu'elle ne l'est pas ; stable meme si la Station deplace le module (refonte-modules.md 3.3)
    exemplaire_module: str | None = None

    def __post_init__(self):
        self.effets = tuple(self.effets)
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
            self.cible != CibleCarteNew.ENNEMI_UNIQUE
        ):
            raise ValueError(f"{self.id} : 'autres ennemis' suppose une cible Ennemi Unique")
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

    def copie(self, exemplaire_module: str | None = None) -> "CarteNew":
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

    # --- Module detruit (specs/refonte-modules.md 3.3 a 3.5) ---

    def jouable_si_module_detruit(self) -> bool:
        """False : la carte part en pile Hors service tant que son module est detruit."""
        return self.persistante

    # --- Lecture JSON (format de config/carte_new.json) ---

    @classmethod
    def depuis_dict(cls, entree: dict) -> "CarteNew":
        _verifier_cles(entree, CLES_CARTE, f"Carte {entree.get('id')}")
        return cls(
            id=entree["id"],
            nom=entree["nom"],
            image=entree["image"],
            rarete=RareteCarte[entree["rarete"].upper()],
            categorie=CategorieCarte(entree["categorie"]),
            cible=CibleCarteNew(entree["cible"]),
            cout=entree["cout"],
            effets=tuple(Effet.depuis_dict(effet) for effet in entree["effets"]),
            description=entree.get("description", ""),
            valeurs=dict(entree.get("valeurs", {})),
            persistante=entree.get("persistante", False),
            jouable=entree.get("jouable", True),
            refonte=entree.get("refonte", False),
            lancements_base=entree.get("lancements", 1),
            munitions_base=entree.get("munition"),
        )


def charger_cartes_new(fichier: Path = FICHIER_CARTES_NEW) -> dict[str, CarteNew]:
    """Charge config/carte_new.json. Renvoie un dict id de carte -> modele de carte."""
    donnees = json.loads(fichier.read_text(encoding="utf-8"))
    return {entree["id"]: CarteNew.depuis_dict(entree) for entree in donnees["cartes"]}


def appliquer_repetition(effet: Effet, supplement: int, cartes: Iterable[CarteNew]) -> int:
    """Effet REPETITION joue : chaque carte visee par son filtre est lancee `supplement` fois de plus
    (valeur de l'effet sur la carte jouee : carte.valeur_de(effet)), pour le reste du combat.
    `cartes` : toutes les cartes du combat, toutes piles confondues (main, pioche, defausse,
    epuisees, Hors service), pour qu'une carte piochee plus tard soit concernee elle aussi. Renvoie
    le nombre de cartes modifiees."""
    if effet.nature != NatureEffet.REPETITION:
        raise ValueError(f"Effet {effet.nature.name} : seul un effet REPETITION modifie les lancements")
    visees = [carte for carte in cartes if effet.filtre.correspond(carte)]
    for carte in visees:
        carte.lancements_actuels += supplement
    return len(visees)
