"""
Persistance du parcours (specs.md 10.3) : profils joueur locaux et parties sauvegardees. Pas de
compte/login, mais plusieurs profils peuvent coexister sur un meme appareil. Chaque joueur ne peut
avoir qu'une seule partie EN_COURS a la fois (decision utilisateur).

Les fonctions vers_dict/depuis_dict/vers_json/depuis_json sont pures (testables sans I/O). L'I/O
fichier (PC uniquement, cf. web/bridge.py + web/app.js pour localStorage cote web) est regroupee en
bas de ce fichier.
"""

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from src.gameplay.carte import Carte
from src.gameplay.combat import Combat
from src.gameplay.config_poc import (
    ELECTRICITE_PAR_TOUR,
    ID_MODULE_PRINCIPAL,
    MODE_TEST,
    PV_MODULE_MODE_TEST,
    creer_flotte,
    ids_deck_module_principal,
)
from src.gameplay.deck import Deck
from src.gameplay.donnees import SpecModule, charger_cartes, charger_ennemis, charger_modules
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.vaisseau import Vaisseau

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_SAVES = RACINE / "saves"

VERSION_FORMAT = 1

# Un etat par emplacement du vaisseau (specs.md 3.1/5) : la base (module principal, toujours
# equipee) et les 4 emplacements equipables. None = emplacement vide.
POSITIONS_EQUIPABLES = ("avant_gauche", "avant_droite", "arriere_gauche", "arriere_droite")
POSITIONS_VAISSEAU = ("base",) + POSITIONS_EQUIPABLES

STATUT_EN_COURS = "EN_COURS"
STATUT_TERMINEE = "TERMINEE"


@dataclass
class EtatModule:
    """Etat persistant d'un module equipe (specs.md 2.2) : PV actuels/max et palier de mise a
    jour (1 a 3), independants du reste (Module, dans src/gameplay/module.py, est l'etat de
    combat ephemere - recree a chaque combat a partir de cet etat persistant)."""

    module_id: str
    pv: int
    pv_max: int
    niveau_maj: int = 1


@dataclass
class Partie:
    """Une sauvegarde de partie, rattachee a un profil (specs.md 10.3)."""

    id: str
    nom: str
    statut: str
    graine: int
    niveau: int
    argent: int
    vaisseau: dict[str, EtatModule | None]
    deck: list[str]
    version: int = VERSION_FORMAT


@dataclass
class Profil:
    """Un profil joueur local (specs.md 10.3). Distinct de la classe Joueur de
    src/gameplay/joueur.py, qui represente l'etat *de combat* (vaisseau + deck + electricite),
    ephemere et sans rapport avec la persistance entre parties."""

    id: str
    nom: str
    version: int = VERSION_FORMAT


def _horodatage() -> str:
    """Horodatage avec microsecondes (pas seulement secondes) pour eviter toute collision
    d'id entre deux profils/parties crees dans la meme seconde."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


# --- Serialisation (pure, testable sans I/O) ---


def partie_vers_dict(partie: Partie) -> dict:
    return {
        "version": partie.version,
        "id": partie.id,
        "nom": partie.nom,
        "statut": partie.statut,
        "graine": partie.graine,
        "niveau": partie.niveau,
        "argent": partie.argent,
        "vaisseau": {
            position: (asdict(etat) if etat is not None else None) for position, etat in partie.vaisseau.items()
        },
        "deck": list(partie.deck),
    }


def partie_depuis_dict(donnees: dict) -> Partie:
    return Partie(
        id=donnees["id"],
        nom=donnees["nom"],
        statut=donnees["statut"],
        graine=donnees["graine"],
        niveau=donnees["niveau"],
        argent=donnees["argent"],
        vaisseau={
            position: (EtatModule(**etat) if etat is not None else None)
            for position, etat in donnees["vaisseau"].items()
        },
        deck=list(donnees["deck"]),
        version=donnees.get("version", VERSION_FORMAT),
    )


def partie_vers_json(partie: Partie) -> str:
    return json.dumps(partie_vers_dict(partie))


def partie_depuis_json(texte: str) -> Partie:
    return partie_depuis_dict(json.loads(texte))


def profil_vers_dict(profil: Profil) -> dict:
    return {"version": profil.version, "id": profil.id, "nom": profil.nom}


def profil_depuis_dict(donnees: dict) -> Profil:
    return Profil(id=donnees["id"], nom=donnees["nom"], version=donnees.get("version", VERSION_FORMAT))


def profil_vers_json(profil: Profil) -> str:
    return json.dumps(profil_vers_dict(profil))


def profil_depuis_json(texte: str) -> Profil:
    return profil_depuis_dict(json.loads(texte))


# --- Creation ---


def nouveau_profil(nom: str) -> Profil:
    return Profil(id=f"joueur_{_horodatage()}", nom=nom)


def nouvelle_partie(aleatoire: random.Random | None = None) -> Partie:
    """Nouvelle partie au Niveau 1 (specs.md 2.3) : seul le module principal est equipe (le 2e
    slot est pourvu par le choix de module du Niveau 1, qui n'a pas encore eu lieu a ce stade),
    avec son deck de depart fixe (config_poc.ids_deck_module_principal). Argent a 0 (montant de
    depart pas encore defini, specs.md 9.1)."""
    aleatoire = aleatoire or random.Random()
    modules = charger_modules()
    cartes = charger_cartes()
    spec_principal = next(spec for spec in modules if spec.id == ID_MODULE_PRINCIPAL)
    vaisseau: dict[str, EtatModule | None] = {position: None for position in POSITIONS_VAISSEAU}
    vaisseau["base"] = EtatModule(
        module_id=spec_principal.id,
        pv=spec_principal.points_de_vie,
        pv_max=spec_principal.points_de_vie,
        niveau_maj=1,
    )
    return Partie(
        id=f"partie_{_horodatage()}",
        nom=f"Partie du {datetime.now():%d/%m/%Y}",
        statut=STATUT_EN_COURS,
        graine=aleatoire.randrange(2**31),
        niveau=1,
        argent=0,
        vaisseau=vaisseau,
        deck=ids_deck_module_principal(spec_principal, cartes),
    )


def deck_de_la_partie(partie: Partie, cartes: dict[str, Carte] | None = None) -> list[Carte]:
    """Resout les ids de `partie.deck` en exemplaires Carte independants (copie()) - pour
    afficher/jouer le deck reel d'une partie sauvegardee (ex. ecran deck en entier)."""
    cartes = cartes if cartes is not None else charger_cartes()
    return [cartes[id_carte].copie() for id_carte in partie.deck]


def combat_depuis_partie(partie: Partie, aleatoire: random.Random | None = None) -> Combat:
    """Construit un Combat a partir d'une partie sauvegardee : vaisseau et deck reels du joueur,
    mais flotte ennemie tiree au hasard - approximation temporaire (bouton "Continuer", decision
    utilisateur) en attendant que l'orchestration du parcours (specs.md 2.3/10.3) determine
    precisement quel combat affronter a ce niveau.

    En mode test (MODE_TEST, cf. config_poc.py), les modules du joueur demarrent ce combat a
    PV_MODULE_MODE_TEST/PV_MODULE_MODE_TEST (pleine vie), sans tenir compte des PV persistes de
    la partie - meme principe que la flotte ennemie (creer_flotte), pour pouvoir enchainer les
    essais manuels du parcours sans jamais perdre. Les PV persistes ne sont pas modifies pour
    autant (aucune ecriture ici)."""
    aleatoire = aleatoire or random.Random(partie.graine + partie.niveau)
    specs_par_id = {spec.id: spec for spec in charger_modules()}
    cartes = charger_cartes()

    def _module(etat: EtatModule | None) -> Module | None:
        if etat is None:
            return None
        spec = specs_par_id[etat.module_id]
        pv_max = PV_MODULE_MODE_TEST if MODE_TEST else etat.pv_max
        module = Module(pv_max=pv_max, nom=spec.nom, image=spec.image)
        if not MODE_TEST:
            module.pv = etat.pv
        return module

    base = _module(partie.vaisseau["base"])
    if base is None:
        raise ValueError("Partie invalide : le module principal doit toujours etre equipe")

    vaisseau = Vaisseau(
        base=base,
        avant_gauche=_module(partie.vaisseau["avant_gauche"]),
        avant_droite=_module(partie.vaisseau["avant_droite"]),
        arriere_gauche=_module(partie.vaisseau["arriere_gauche"]),
        arriere_droite=_module(partie.vaisseau["arriere_droite"]),
    )
    deck = Deck(cartes=deck_de_la_partie(partie, cartes), generateur_aleatoire=aleatoire)
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=ELECTRICITE_PAR_TOUR)
    flotte = creer_flotte(charger_ennemis(), aleatoire)
    return Combat(joueur=joueur, flotte=flotte, aleatoire=aleatoire)


# --- Progression (specs.md 2.4) : fonctions pures utilisees par l'enchainement des ecrans, cote
# PC (main.py) comme cote web (web/bridge.py) ---


def equiper_module(partie: Partie, spec: SpecModule) -> Partie:
    """Equipe ce module sur le premier emplacement libre du vaisseau (specs.md 2.3/5) - utilise
    par le choix de module du Niveau 1 (un seul emplacement libre a ce stade). Modifie et renvoie
    `partie`."""
    position = next(p for p in POSITIONS_EQUIPABLES if partie.vaisseau[p] is None)
    partie.vaisseau[position] = EtatModule(
        module_id=spec.id, pv=spec.points_de_vie, pv_max=spec.points_de_vie, niveau_maj=1
    )
    return partie


def avancer_niveau(partie: Partie) -> Partie:
    """Fait passer la partie au niveau suivant (specs.md 2.4), une fois l'etape du niveau courant
    resolue (module choisi, combat gagne, etape de service terminee...). Modifie et renvoie
    `partie`."""
    partie.niveau += 1
    return partie


def id_de_carte(carte: Carte, cartes: dict[str, Carte]) -> str:
    """Retrouve l'id d'une Carte dans le dict cartes.json, par identite d'objet : pool_module/
    pool_toutes_cartes (src/gameplay/parcours.py) renvoient des references directes vers ce dict,
    jamais des copies, donc `is` est fiable ici."""
    return next(id_carte for id_carte, c in cartes.items() if c is carte)


def ajouter_carte(partie: Partie, id_carte: str) -> Partie:
    """Ajoute une carte au deck possede de la partie (recompense de fin de combat, specs.md 6).
    Modifie et renvoie `partie`."""
    partie.deck.append(id_carte)
    return partie


def specs_utilisees_partie(partie: Partie, specs_par_id: dict[str, SpecModule]) -> list[SpecModule]:
    """Specs des modules actuellement equipes sur cette partie, module principal en premier
    (meme ordre que creer_vaisseau/tirer_candidats_recompense, specs.md 6) - pour tirer une
    recompense de fin de combat a partir d'une partie sauvegardee plutot que d'un vaisseau tire au
    hasard."""
    return [
        specs_par_id[partie.vaisseau[position].module_id]
        for position in POSITIONS_VAISSEAU
        if partie.vaisseau[position] is not None
    ]


# --- Station service (garage), specs.md 2.2 : 4 actions gratuites pour l'instant (pas de
# ressource Argent implementee) appliquees a un module equipe de la partie, partagees PC/web ---

PV_REPARATION = 20
PV_AMELIORATION = 10
NIVEAU_MAJ_MAX = 3


def reparer_module(partie: Partie, position: str) -> Partie:
    """Restaure PV_REPARATION PV au module de cet emplacement, plafonne a son pv_max (specs.md
    2.2). S'applique au module principal comme aux modules equipes. Modifie et renvoie `partie`."""
    etat = partie.vaisseau[position]
    etat.pv = min(etat.pv + PV_REPARATION, etat.pv_max)
    return partie


def ameliorer_module(partie: Partie, position: str) -> Partie:
    """Augmente le pv_max du module de cet emplacement de PV_AMELIORATION, et ses PV actuels du
    meme montant (specs.md 2.2 : pas seulement le plafond). S'applique au module principal comme
    aux modules equipes. Modifie et renvoie `partie`."""
    etat = partie.vaisseau[position]
    etat.pv_max += PV_AMELIORATION
    etat.pv += PV_AMELIORATION
    return partie


def mettre_a_jour_module(partie: Partie, position: str) -> Partie:
    """Fait progresser d'un palier le niveau de mise a jour du module de cet emplacement (1 a
    NIVEAU_MAJ_MAX, specs.md 2.2/6) - determine le palier de rarete propose en recompense/a la
    Planete commerciale. S'applique au module principal comme aux modules equipes. Modifie et
    renvoie `partie`."""
    etat = partie.vaisseau[position]
    etat.niveau_maj = min(etat.niveau_maj + 1, NIVEAU_MAJ_MAX)
    return partie


def deplacer_module(partie: Partie, position_source: str, position_destination: str) -> Partie:
    """Echange les modules de deux emplacements equipables (specs.md 2.2 : vide, le module y est
    simplement deplace ; occupe, les deux modules echangent leur position). Ne s'applique jamais
    au module principal ('base') - a l'appelant (ecran Station service) de ne jamais transmettre
    cette position. Modifie et renvoie `partie`."""
    partie.vaisseau[position_source], partie.vaisseau[position_destination] = (
        partie.vaisseau[position_destination],
        partie.vaisseau[position_source],
    )
    return partie


# --- I/O fichier (PC uniquement) ---


def _dossier_profil(joueur_id: str) -> Path:
    return DOSSIER_SAVES / joueur_id


def _dossier_parties(joueur_id: str) -> Path:
    return _dossier_profil(joueur_id) / "parties"


def lister_profils() -> list[Profil]:
    """Tous les profils existants (PC), tries par nom."""
    if not DOSSIER_SAVES.exists():
        return []
    profils = []
    for dossier in DOSSIER_SAVES.iterdir():
        fichier = dossier / "profil.json"
        if fichier.is_file():
            profils.append(profil_depuis_json(fichier.read_text()))
    return sorted(profils, key=lambda profil: profil.nom.lower())


def creer_profil(nom: str) -> Profil:
    """Cree un nouveau profil (PC) et l'ecrit sur disque."""
    profil = nouveau_profil(nom)
    sauvegarder_profil(profil)
    return profil


def sauvegarder_profil(profil: Profil) -> None:
    dossier = _dossier_profil(profil.id)
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "profil.json").write_text(profil_vers_json(profil))


def partie_en_cours(joueur_id: str) -> Partie | None:
    """La partie EN_COURS de ce joueur, s'il en a une (il ne peut y en avoir qu'une a la fois,
    garanti par sauvegarder_partie/abandonner_partie ci-dessous)."""
    dossier = _dossier_parties(joueur_id)
    if not dossier.exists():
        return None
    for fichier in dossier.iterdir():
        partie = partie_depuis_json(fichier.read_text())
        if partie.statut == STATUT_EN_COURS:
            return partie
    return None


def sauvegarder_partie(joueur_id: str, partie: Partie) -> None:
    dossier = _dossier_parties(joueur_id)
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{partie.id}.json").write_text(partie_vers_json(partie))


def marquer_terminee(partie: Partie) -> Partie:
    """Marque la partie TERMINEE (decision utilisateur : comme une defaite, gardee pour de
    futures statistiques) - fonction pure, reutilisee par abandonner_partie (I/O PC, ci-dessous)
    et par web/bridge.py:abandonner_partie_web (I/O localStorage cote JS)."""
    partie.statut = STATUT_TERMINEE
    return partie


def abandonner_partie(joueur_id: str, partie: Partie) -> Partie:
    """Marque la partie TERMINEE et la sauvegarde (PC). Renvoie la partie mise a jour."""
    marquer_terminee(partie)
    sauvegarder_partie(joueur_id, partie)
    return partie
