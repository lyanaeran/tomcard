"""
Ennemi de la refonte (EnnemiNew, nom provisoire) : modele de donnees cible de la refonte des
ennemis (specs/refonte-ennemis.md). Source de verite : config/ennemi_new.json
(charger_ennemis_new). Pas encore branche au moteur : coexiste avec ennemi.py:Ennemi
(config/ennemis.json), qu'il remplacera au branchement de la refonte.

Differences avec Ennemi :
- un CYCLE D'ACTIONS remplace la frequence et le tour de depart : une etape par tour ennemi, dans
  l'ordre, puis retour a la premiere ; une etape est une liste d'effets joues le meme tour ;
  l'intention affichee est simplement l'etape courante ;
- les effets renvoient a des VALEURS NOMMEES de l'ennemi, comme les cartes ; chaque valeur a une
  augmentation (de combien, tous les combien de tours) et un COEFFICIENT de difficulte (>= 1,
  donne a la creation pour le combat) multiplie base, augmentations et PV, arrondi a l'inferieur ;
- le bouclier baisse de 1 a la fin du tour du joueur ; l'incendie frappe a la fin du tour du joueur,
  avant cette baisse ;
- Miroir pose un RENVOI (plus un bouclier) : non cumulable, il dure jusqu'a la fin du tour du
  joueur.

Comme ModuleNew, la meme classe sert de modele (lu dans le JSON) et d'ennemi en combat : le combat
travaille sur une copie (pour_combat), le modele n'est jamais modifie. Le numero de tour n'est pas
dans l'ennemi : c'est le combat qui le tient (il passe au tour suivant au debut du tour du joueur,
a partir du tour 2) et le donne pour lire une valeur (valeur, valeurs_au_tour).
"""

import dataclasses
import json
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from fractions import Fraction
from pathlib import Path

FICHIER_ENNEMIS_NEW = Path(__file__).resolve().parents[2] / "config" / "ennemi_new.json"

# Cles autorisees dans config/ennemi_new.json : une cle inconnue est refusee au chargement
CLES_ENNEMI = {"id", "nom", "image", "taille", "emplacements", "placement", "pv", "valeurs", "actions"}
CLES_VALEUR = {"base", "augmentation", "tous_les"}
CLES_EFFET = {"nature", "valeur", "cible", "repetitions"}


def _verifier_cles(entree: dict, autorisees: set[str], ou: str) -> None:
    inconnues = entree.keys() - autorisees
    if inconnues:
        raise ValueError(f"{ou} : cles inconnues {sorted(inconnues)}")


class PlacementEnnemi(Enum):
    """Colonne preferee de l'ennemi dans la flotte (specs.md 3.2) ; absent si indifferent."""

    # Se place devant un autre ennemi pour le proteger (Petit Jean)
    PROTECTEUR_AVANT = auto()
    # Se place derriere un autre ennemi, protege (Le nettoyeur)
    PROTEGE_ARRIERE = auto()


class NatureEffetEnnemi(Enum):
    """Ce que fait un effet d'ennemi ; `valeur` designe la valeur nommee de l'ennemi utilisee."""

    # Inflige `valeur` degats a chaque module touche (apres son bouclier)
    ATTAQUE = auto()
    # Ajoute `valeur` de bouclier ; il baisse de 1 a la fin du tour du joueur
    BOUCLIER = auto()
    # Pose un renvoi de `valeur` : les degats recus sont renvoyes a l'attaquant jusqu'a `valeur`,
    # l'ennemi encaisse le reste ; non cumulable (le reposer le remplace), jusqu'a la fin du tour
    # du joueur (Miroir)
    RENVOI = auto()


class CibleEffetEnnemi(Enum):
    """Ce que touche un effet d'ennemi."""

    # Le module vivant le plus proche (meme regle que ciblage.py:module_cible_par_ennemi)
    PROXIMITE = auto()
    # Tous les modules vivants du joueur
    TOUS_MODULES = auto()
    # L'ennemi qui joue l'effet
    SOI_MEME = auto()
    # Un ennemi de la colonne avant de la flotte (lui-meme compris), sinon de la colonne arriere
    # (Miroir : il se protege lui-meme s'il est seul)
    ALLIE_AVANT_SINON_ARRIERE = auto()

    @property
    def vise_le_joueur(self) -> bool:
        return self in (CibleEffetEnnemi.PROXIMITE, CibleEffetEnnemi.TOUS_MODULES)


@dataclass(frozen=True)
class ValeurEnnemi:
    """Une valeur nommee d'un ennemi (degats, bouclier...) et son augmentation avec le temps."""

    # Valeur au tour 1, avant coefficient
    base: int
    # Ajout a chaque palier (0 : valeur fixe)
    augmentation: int = 0
    # Nombre de tours entre deux paliers (rythme, jamais multiplie par le coefficient)
    tous_les: int = 1

    def __post_init__(self):
        if self.base < 0 or self.augmentation < 0:
            raise ValueError("base et augmentation doivent etre positives ou nulles")
        if self.tous_les < 1:
            raise ValueError("tous_les doit valoir au moins 1")

    def au_tour(self, tour: int, coefficient: Fraction = Fraction(1)) -> int:
        """Valeur au tour donne (1 = premier tour du combat) : arrondi_inferieur((base +
        augmentation x paliers) x coefficient), paliers = (tour - 1) // tous_les
        (specs/refonte-ennemis.md 3.3)."""
        paliers = (tour - 1) // self.tous_les
        return math.floor((self.base + self.augmentation * paliers) * coefficient)


@dataclass(frozen=True)
class EffetEnnemi:
    """Un effet d'une etape du cycle. Ne contient aucun nombre a part les repetitions : `valeur`
    est le NOM d'une valeur de l'ennemi, lue au moment de jouer (EnnemiNew.valeur)."""

    nature: NatureEffetEnnemi
    # Nom de la valeur de l'ennemi utilisee par l'effet
    valeur: str
    cible: CibleEffetEnnemi
    # Nombre de fois que l'effet est joue dans l'etape, avec la meme valeur (Le nettoyeur : 2)
    repetitions: int = 1

    def __post_init__(self):
        if self.repetitions < 1:
            raise ValueError("repetitions doit valoir au moins 1")
        if (self.nature == NatureEffetEnnemi.ATTAQUE) != self.cible.vise_le_joueur:
            raise ValueError(f"{self.nature.name} ne peut pas viser {self.cible.name}")

    @classmethod
    def depuis_dict(cls, entree: dict) -> "EffetEnnemi":
        """Effet a partir d'une entree d'une etape de "actions" dans config/ennemi_new.json."""
        _verifier_cles(entree, CLES_EFFET, f"Effet {entree.get('nature')}")
        return cls(
            nature=NatureEffetEnnemi[entree["nature"]],
            valeur=entree["valeur"],
            cible=CibleEffetEnnemi[entree["cible"]],
            repetitions=entree.get("repetitions", 1),
        )


@dataclass(eq=False)
class EnnemiNew:
    """Un ennemi de la refonte. eq=False : deux ennemis du meme type dans une flotte sont
    distincts."""

    # --- Modele : lu dans config/ennemi_new.json ---

    # Identifiant du type d'ennemi (ex. "ENM_PAT_LE_PIRATE")
    id: str
    # Nom affiche en jeu (texte affiche : accents autorises, cf. CLAUDE.md)
    nom: str
    # Chemin de l'image (assets/ennemis/)
    image: str
    # PV avant coefficient
    pv_base: int
    # Valeurs nommees (ex. {"degats": ValeurEnnemi(5, 1, 3)})
    valeurs: dict[str, ValeurEnnemi]
    # Cycle d'actions : une etape (tuple d'effets) par tour ennemi, puis retour a la premiere
    actions: tuple[tuple[EffetEnnemi, ...], ...]
    # Taille S/M/L, informative (combat.md 3.2)
    taille: str = "S"
    # Nombre de cases occupees dans la flotte (Boss des pirates : 2)
    emplacements: int = 1
    # Colonne preferee, None si indifferent
    placement: PlacementEnnemi | None = None

    # --- Etat en combat : sur la copie de combat seulement ---

    # Coefficient de difficulte (>= 1), fixe a la creation de la copie de combat
    coefficient: Fraction = Fraction(1)
    # PV max et PV du combat (pv_base x coefficient, arrondi a l'inferieur) ; None hors combat
    pv_max: int | None = None
    pv: int | None = None
    # Index de la prochaine etape du cycle
    etape: int = 0
    bouclier: int = 0
    # Degats encore renvoyables jusqu'a la fin du tour du joueur (0 : pas de renvoi)
    renvoi: int = 0
    # Points d'incendie : autant de degats a la fin du tour du joueur, puis -1
    incendie: int = 0

    def __post_init__(self):
        self.actions = tuple(tuple(etape) for etape in self.actions)
        if self.pv_base < 1:
            raise ValueError(f"Ennemi {self.id} : pv doit valoir au moins 1")
        if self.emplacements < 1:
            raise ValueError(f"Ennemi {self.id} : emplacements doit valoir au moins 1")
        if not self.actions or not all(self.actions):
            raise ValueError(f"Ennemi {self.id} : le cycle et chacune de ses etapes doivent avoir au moins un effet")
        for etape in self.actions:
            for effet in etape:
                if effet.valeur not in self.valeurs:
                    raise ValueError(f"Ennemi {self.id} : valeur inconnue '{effet.valeur}'")

    # --- Creation pour un combat ---

    def pour_combat(self, coefficient: float | Fraction = 1) -> "EnnemiNew":
        """Copie de cet ennemi pour un combat, avec son coefficient de difficulte (au moins 1,
        decision utilisateur) : PV pleins, debut du cycle, aucun etat de combat."""
        # Fraction(str(...)) : 1.15 x 20 vaut exactement 23, sans erreur d'arrondi des flottants
        coefficient = Fraction(str(coefficient))
        if coefficient < 1:
            raise ValueError(f"Ennemi {self.id} : le coefficient doit valoir au moins 1 ({coefficient})")
        pv_max = math.floor(self.pv_base * coefficient)
        return dataclasses.replace(
            self, coefficient=coefficient, pv_max=pv_max, pv=pv_max, etape=0, bouclier=0, renvoi=0, incendie=0,
        )

    # --- Valeurs et cycle ---

    def valeur(self, nom: str, tour: int) -> int:
        """Valeur nommee au tour donne du combat (tenu par le combat, pas par l'ennemi),
        augmentation et coefficient compris."""
        return self.valeurs[nom].au_tour(tour, self.coefficient)

    def valeurs_au_tour(self, tour: int) -> dict[str, int]:
        return {nom: self.valeur(nom, tour) for nom in self.valeurs}

    @property
    def etape_courante(self) -> tuple[EffetEnnemi, ...]:
        """Etape jouee au prochain tour ennemi : c'est l'intention affichee au joueur."""
        return self.actions[self.etape]

    def avancer_cycle(self) -> None:
        """Apres avoir joue l'etape courante : passe a la suivante, ou revient a la premiere."""
        self.etape = (self.etape + 1) % len(self.actions)

    # --- Combat ---

    def est_detruit(self) -> bool:
        return self.pv is not None and self.pv <= 0

    def subir_degats(self, degats: int) -> int:
        """Encaisse une attaque. Un renvoi actif prend les degats en premier, jusqu'a sa valeur
        restante ; le bouclier absorbe ensuite le reste avant les PV. Renvoie les degats a
        renvoyer a l'attaquant (0 sans renvoi)."""
        renvoyes = min(self.renvoi, degats)
        self.renvoi -= renvoyes
        self._encaisser(degats - renvoyes)
        return renvoyes

    def _encaisser(self, degats: int) -> None:
        """Bouclier d'abord, puis PV."""
        degats_restants = max(0, degats - self.bouclier)
        self.bouclier = max(0, self.bouclier - degats)
        self.pv = max(0, self.pv - degats_restants)

    def ajouter_bouclier(self, valeur: int) -> None:
        self.bouclier += valeur

    def poser_renvoi(self, valeur: int) -> None:
        """Non cumulable : un nouveau renvoi remplace l'ancien (decision utilisateur)."""
        self.renvoi = valeur

    def ajouter_incendie(self, valeur: int) -> None:
        self.incendie += valeur

    def fin_du_tour_du_joueur(self) -> None:
        """Ordre decide par l'utilisateur : l'incendie frappe (absorbe par le bouclier, jamais
        renvoye) puis baisse de 1 ; ensuite le bouclier baisse de 1 ; le renvoi prend fin."""
        if self.incendie:
            self._encaisser(self.incendie)
            self.incendie -= 1
        self.bouclier = max(0, self.bouclier - 1)
        self.renvoi = 0

    # --- Lecture JSON (format de config/ennemi_new.json) ---

    @classmethod
    def depuis_dict(cls, entree: dict) -> "EnnemiNew":
        """Modele d'ennemi a partir d'une entree de config/ennemi_new.json ; toute erreur de
        lecture est signalee avec l'id de l'ennemi."""
        ennemi = f"Ennemi {entree.get('id', '?')}"
        _verifier_cles(entree, CLES_ENNEMI, ennemi)
        try:
            valeurs = {}
            for nom, valeur in entree["valeurs"].items():
                _verifier_cles(valeur, CLES_VALEUR, f"{ennemi}, valeur '{nom}'")
                valeurs[nom] = ValeurEnnemi(**valeur)
            placement = entree.get("placement")
            return cls(
                id=entree["id"],
                nom=entree["nom"],
                image=entree["image"],
                pv_base=entree["pv"],
                valeurs=valeurs,
                actions=tuple(tuple(EffetEnnemi.depuis_dict(effet) for effet in etape) for etape in entree["actions"]),
                taille=entree.get("taille", "S"),
                emplacements=entree.get("emplacements", 1),
                placement=PlacementEnnemi[placement] if placement else None,
            )
        except KeyError as erreur:
            raise ValueError(f"{ennemi} : cle manquante ou inconnue {erreur}") from erreur
        except (TypeError, ValueError) as erreur:
            if str(erreur).startswith(ennemi):
                raise
            raise ValueError(f"{ennemi} : {erreur}") from erreur


def charger_ennemis_new(fichier: Path = FICHIER_ENNEMIS_NEW) -> dict[str, EnnemiNew]:
    """Charge config/ennemi_new.json. Renvoie un dict id d'ennemi -> modele d'ennemi."""
    donnees = json.loads(fichier.read_text(encoding="utf-8"))
    return {entree["id"]: EnnemiNew.depuis_dict(entree) for entree in donnees["ennemis"]}
