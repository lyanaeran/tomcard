"""
Module de la refonte (ModuleNew, nom provisoire) : modele de donnees cible de la refonte des
modules (specs/refonte-modules.md, 8). Source de verite : config/module_new.json
(charger_modules_new). Remplace donnees.py:SpecModule et module.py:Module (ancien moteur,
supprimes a la PR 4 du branchement) et l'ancien partie.py:EtatModule.

Une seule classe reunit les trois niveaux d'information d'un module :
- le MODELE (le type de module, lu dans le JSON : nom, PV de base, cartes...) ;
- l'EXEMPLAIRE dans la partie (identifiant "M3", emplacement, PV max ameliores...), sauvegarde ;
- l'ETAT EN COMBAT (PV de combat, statuts : bouclier, leurre...), jamais sauvegarde.

Le combat travaille sur une COPIE du module (copie_pour_combat), champs de combat remis a zero :
le module de la partie n'est jamais modifie pendant un combat (un combat abandonne ne touche pas
la partie), et seuls les PV du principal y sont reportes a la fin (reporter_combat).

Regles de la refonte : les modules secondaires repartent a leur PV max a chaque combat, seuls les
PV du principal persistent. Bouclier, leurre, incendie... sont des STATUTS (statut_new.py,
specs/refonte-statuts.md), partages avec EnnemiNew ; ils s'eteignent a la fin du tour ennemi.
"""

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path

from src.gameplay.statut_new import Encaissement, Statuts

FICHIER_MODULES_NEW = Path(__file__).resolve().parents[2] / "config" / "module_new.json"

# Cles autorisees dans config/module_new.json : une cle inconnue est refusee au chargement
CLES_MODULE = {"id", "nom", "image", "description", "principal", "pv_max", "cartes", "jouable", "refonte"}


@dataclass(eq=False)
class ModuleNew:
    """Un module de la refonte. eq=False : deux exemplaires du meme type de module sont distincts."""

    # --- Modele : lu dans config/module_new.json, identique pour tous les exemplaires ---

    # Identifiant du type de module (ex. "MOD_2")
    id: str
    # Nom affiche en jeu (texte affiche : accents autorises, cf. CLAUDE.md)
    nom: str
    # Chemin de l'image du module (assets/modules/)
    image: str
    # Accroche narrative affichee au choix du module et dans l'ecran Vaisseau
    description: str
    # PV max d'un exemplaire neuf, avant toute amelioration
    pv_max_base: int
    # Ids des cartes du module (config/carte_new.json), jouables ou non
    cartes: tuple[str, ...] = ()
    # True pour le module principal : toujours equipe, seul a garder ses PV entre deux combats
    principal: bool = False
    # True si le module peut etre propose et equipe
    jouable: bool = True
    # True si le module a ete revu dans la refonte
    refonte: bool = False

    # --- Exemplaire dans la partie : sauvegarde ---

    # Identifiant de l'exemplaire dans la partie (ex. "M3"), None pour un simple modele ; stable
    # meme si la Station deplace le module, les cartes y sont rattachees (refonte-modules.md 3.3)
    exemplaire: str | None = None
    # Emplacement sur le vaisseau ("base", "avant_gauche"...), None tant qu'il n'est pas equipe
    emplacement: str | None = None
    # PV max de cet exemplaire, ameliorations de la Station comprises (pv_max_base au depart)
    pv_max: int | None = None
    # PV sauvegardes entre deux combats : utilises pour le principal seulement, un secondaire
    # repartant toujours a pv_max
    pv: int | None = None
    # Palier de mise a jour (1 a 3), qui ouvre les raretes proposees en recompense (specs.md 6)
    niveau_maj: int = 1

    # --- Etat en combat : sur la copie de combat seulement, jamais sauvegarde ---

    # PV pendant le combat ; None hors combat
    pv_combat: int | None = None
    # Statuts en cours (bouclier, leurre, incendie...), partages avec les ennemis (statut_new.py)
    statuts: Statuts = field(default_factory=Statuts)

    def __post_init__(self):
        self.cartes = tuple(self.cartes)
        if self.pv_max_base < 1:
            raise ValueError("pv_max_base doit valoir au moins 1")
        if not 1 <= self.niveau_maj <= 3:
            raise ValueError("niveau_maj doit etre entre 1 et 3")
        if self.pv_max is None:
            self.pv_max = self.pv_max_base
        if self.pv is None:
            self.pv = self.pv_max

    # --- Exemplaires ---

    def nouvel_exemplaire(self, exemplaire: str, emplacement: str) -> "ModuleNew":
        """Nouvel exemplaire de ce type de module pour une partie : PV max de base, PV pleins,
        palier 1, aucun etat de combat."""
        return dataclasses.replace(
            self, exemplaire=exemplaire, emplacement=emplacement, pv_max=self.pv_max_base,
            pv=self.pv_max_base, niveau_maj=1, pv_combat=None, statuts=Statuts(),
        )

    @property
    def pv_au_prochain_combat(self) -> int:
        """PV avec lesquels cet exemplaire commencera son prochain combat : PV sauvegardes pour le
        principal, PV max pour un secondaire (il repart plein). A afficher hors combat."""
        return self.pv if self.principal else self.pv_max

    def copie_pour_combat(self) -> "ModuleNew":
        """Copie de ce module pour un combat, champs de combat remis a zero, PV de depart
        pv_au_prochain_combat. Le module d'origine n'est pas modifie."""
        return dataclasses.replace(self, pv_combat=self.pv_au_prochain_combat, statuts=Statuts())

    def reporter_combat(self, copie_de_combat: "ModuleNew") -> None:
        """Fin de combat : reporte sur ce module de la partie ce qui doit persister, c'est-a-dire
        les PV du principal seulement."""
        if self.principal:
            self.pv = copie_de_combat.pv_combat

    # --- Combat (sur la copie de combat) ---

    def est_detruit(self) -> bool:
        return self.pv_combat is not None and self.pv_combat <= 0

    def _verifier_en_combat(self) -> None:
        """Les methodes de combat ne s'appellent que sur une copie de combat (copie_pour_combat)."""
        if self.pv_combat is None:
            raise ValueError(f"Module {self.id} : hors combat, utiliser sa copie de combat (copie_pour_combat)")

    def subir_degats(self, degats: int) -> Encaissement:
        """Encaisse une attaque a travers les statuts (leurre, renvoi, bouclier : Statuts.
        encaisser_attaque). Renvoie le detail, dont les degats a renvoyer a l'attaquant."""
        self._verifier_en_combat()
        encaissement = self.statuts.encaisser_attaque(degats)
        self._perdre_pv(encaissement.degats_pv)
        return encaissement

    def _perdre_pv(self, degats: int) -> None:
        self.pv_combat = max(0, self.pv_combat - degats)

    def reparer(self, valeur: int) -> None:
        """Rend des PV de combat, sans depasser le PV max. Sans effet sur un module detruit : la
        resurrection est une mecanique a part (refonte-modules.md 5, refonte-combat.md 4.4)."""
        self._verifier_en_combat()
        if self.est_detruit():
            return
        self.pv_combat = min(self.pv_max, self.pv_combat + valeur)

    def fin_du_tour_ennemi(self) -> Encaissement:
        """L'incendie frappe puis les statuts s'eteignent (Statuts.fin_de_tour). Renvoie le detail
        des degats d'incendie."""
        self._verifier_en_combat()
        encaissement = self.statuts.fin_de_tour()
        self._perdre_pv(encaissement.degats_pv)
        return encaissement

    # --- Lecture JSON (format de config/module_new.json) ---

    @classmethod
    def depuis_dict(cls, entree: dict) -> "ModuleNew":
        """Modele de module a partir d'une entree de config/module_new.json ; toute erreur de
        lecture est signalee avec l'id du module."""
        module = f"Module {entree.get('id', '?')}"
        inconnues = entree.keys() - CLES_MODULE
        if inconnues:
            raise ValueError(f"{module} : cles inconnues {sorted(inconnues)}")
        try:
            champs = dict(
                id=entree["id"],
                nom=entree["nom"],
                image=entree["image"],
                description=entree["description"],
                pv_max_base=entree["pv_max"],
                cartes=tuple(entree.get("cartes", [])),
                principal=entree.get("principal", False),
                jouable=entree.get("jouable", True),
                refonte=entree.get("refonte", False),
            )
        except KeyError as erreur:
            raise ValueError(f"{module} : cle manquante {erreur}") from erreur
        try:
            return cls(**champs)
        except (TypeError, ValueError) as erreur:
            # Mauvais type (ex. "pv_max": "60") ou valeur refusee par __post_init__
            raise ValueError(f"{module} : {erreur}") from erreur


def charger_modules_new(fichier: Path = FICHIER_MODULES_NEW) -> dict[str, ModuleNew]:
    """Charge config/module_new.json. Renvoie un dict id de module -> modele de module ; un id
    en double est refuse."""
    donnees = json.loads(fichier.read_text(encoding="utf-8"))
    modules = {}
    for entree in donnees["modules"]:
        module = ModuleNew.depuis_dict(entree)
        if module.id in modules:
            raise ValueError(f"config/module_new.json : module {module.id} en double")
        modules[module.id] = module
    if sum(module.principal for module in modules.values()) != 1:
        raise ValueError("config/module_new.json : il faut exactement un module principal")
    return modules
