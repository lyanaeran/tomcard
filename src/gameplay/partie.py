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
    appliquer_degats_mode_test,
    creer_flotte,
    creer_flotte_asteroides,
    ids_deck_module_principal,
)
from src.gameplay.deck import Deck
from src.gameplay.donnees import SpecModule, charger_cartes, charger_ennemis, charger_modules
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_SAVES = RACINE / "saves"

VERSION_FORMAT = 1

# Un etat par emplacement du vaisseau (specs.md 3.1/5) : la base (module principal, toujours
# equipee) et les 4 emplacements equipables. None = emplacement vide.
POSITIONS_EQUIPABLES = ("avant_gauche", "avant_droite", "arriere_gauche", "arriere_droite")
POSITIONS_VAISSEAU = ("base",) + POSITIONS_EQUIPABLES

# Correspondance entre les cles de partie.vaisseau (str) et les Position (Colonne/Rangee) du
# Vaisseau de combat (src/gameplay/vaisseau.py) - meme ordre que POSITIONS_EQUIPABLES, utilisee
# par synchroniser_vaisseau_depuis_combat pour reporter les PV de combat sur la partie.
_POSITIONS_GAMEPLAY_PAR_CLE = {
    "avant_gauche": Position(Colonne.AVANT, Rangee.GAUCHE),
    "avant_droite": Position(Colonne.AVANT, Rangee.DROITE),
    "arriere_gauche": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "arriere_droite": Position(Colonne.ARRIERE, Rangee.DROITE),
}

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


def _pv_module_initial(spec: SpecModule) -> int:
    """PV de depart d'un module tout juste equipe - PV_MODULE_MODE_TEST en mode test (cf.
    config_poc.py), sinon la valeur normale (config/modules.json). Sert de point de depart
    seulement : les PV persistent ensuite normalement d'un combat a l'autre (specs.md 2.2), y
    compris en mode test - cf. combat_depuis_partie."""
    return PV_MODULE_MODE_TEST if MODE_TEST else spec.points_de_vie


ARGENT_DEPART = 7


def nouvelle_partie(aleatoire: random.Random | None = None) -> Partie:
    """Nouvelle partie au Niveau 1 (specs.md 2.3) : seul le module principal est equipe (le 2e
    slot est pourvu par le choix de module du Niveau 1, qui n'a pas encore eu lieu a ce stade),
    avec son deck de depart fixe (config_poc.ids_deck_module_principal). Argent a ARGENT_DEPART
    (specs.md 2.1/9.1)."""
    aleatoire = aleatoire or random.Random()
    modules = charger_modules()
    cartes = charger_cartes()
    spec_principal = next(spec for spec in modules if spec.id == ID_MODULE_PRINCIPAL)
    vaisseau: dict[str, EtatModule | None] = {position: None for position in POSITIONS_VAISSEAU}
    pv_principal = _pv_module_initial(spec_principal)
    vaisseau["base"] = EtatModule(
        module_id=spec_principal.id,
        pv=pv_principal,
        pv_max=pv_principal,
        niveau_maj=1,
    )
    return Partie(
        id=f"partie_{_horodatage()}",
        nom=f"Partie du {datetime.now():%d/%m/%Y}",
        statut=STATUT_EN_COURS,
        graine=aleatoire.randrange(2**31),
        niveau=1,
        argent=ARGENT_DEPART,
        vaisseau=vaisseau,
        deck=ids_deck_module_principal(spec_principal, cartes),
    )


def deck_de_la_partie(partie: Partie, cartes: dict[str, Carte] | None = None) -> list[Carte]:
    """Resout les ids de `partie.deck` en exemplaires Carte independants (copie()) - pour
    afficher/jouer le deck reel d'une partie sauvegardee (ex. ecran deck en entier)."""
    cartes = cartes if cartes is not None else charger_cartes()
    return [cartes[id_carte].copie() for id_carte in partie.deck]


def _joueur_depuis_partie(partie: Partie, cartes: dict[str, Carte], aleatoire: random.Random) -> Joueur:
    """Construit le Joueur (vaisseau + deck) d'un combat a partir d'une partie sauvegardee -
    partage entre combat_depuis_partie (flotte aleatoire standard) et combat_aventure_asteroides
    (flotte scriptee, specs.md 2.5). Les PV des modules sont repris tels quels depuis la partie
    (persistance entre combats, specs.md 2.2) - y compris en mode test (MODE_TEST, cf.
    config_poc.py), ou seule leur valeur de depart est plus elevee (PV_MODULE_MODE_TEST, cf.
    equiper_module/nouvelle_partie) : la persistance elle-meme reste testable (Reparer/Ameliorer
    en Station service, degats qui persistent d'un combat a l'autre).

    En mode test, les cartes ATTAQUE de rarete Base du deck reel infligent
    VALEUR_ATTAQUE_BASE_MODE_TEST degats plutot que leur valeur normale - meme principe que la
    flotte ennemie (creer_flotte), pour pouvoir enchainer les essais manuels sans y passer
    plusieurs tours. Rien n'est modifie dans la partie sauvegardee pour autant (aucune ecriture
    ici)."""
    specs_par_id = {spec.id: spec for spec in charger_modules()}

    def _module(etat: EtatModule | None) -> Module | None:
        if etat is None:
            return None
        spec = specs_par_id[etat.module_id]
        module = Module(pv_max=etat.pv_max, nom=spec.nom, image=spec.image)
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
    deck_cartes = deck_de_la_partie(partie, cartes)
    if MODE_TEST:
        appliquer_degats_mode_test(deck_cartes)
    deck = Deck(cartes=deck_cartes, generateur_aleatoire=aleatoire)
    return Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=ELECTRICITE_PAR_TOUR)


def combat_depuis_partie(partie: Partie, aleatoire: random.Random | None = None) -> Combat:
    """Construit un Combat a partir d'une partie sauvegardee : vaisseau et deck reels du joueur
    (_joueur_depuis_partie), mais flotte ennemie tiree au hasard - approximation temporaire
    (bouton "Continuer", decision utilisateur) en attendant que l'orchestration du parcours
    (specs.md 2.3/10.3) determine precisement quel combat affronter a ce niveau."""
    aleatoire = aleatoire or random.Random(partie.graine + partie.niveau)
    cartes = charger_cartes()
    joueur = _joueur_depuis_partie(partie, cartes, aleatoire)
    flotte = creer_flotte(charger_ennemis(), aleatoire)
    return Combat(joueur=joueur, flotte=flotte, aleatoire=aleatoire)


def combat_aventure_asteroides(partie: Partie, aleatoire: random.Random | None = None) -> Combat:
    """Combat scripte du choix "Affronter les pirates" (Aventure Asteroides, specs.md 2.5) :
    meme vaisseau/deck reels que combat_depuis_partie (_joueur_depuis_partie), mais flotte fixee a
    NOMBRE_ENNEMIS_ASTEROIDES ennemis (creer_flotte_asteroides) plutot que le tirage standard lie
    au niveau."""
    aleatoire = aleatoire or random.Random(partie.graine + partie.niveau)
    cartes = charger_cartes()
    joueur = _joueur_depuis_partie(partie, cartes, aleatoire)
    flotte = creer_flotte_asteroides(charger_ennemis(), aleatoire)
    return Combat(joueur=joueur, flotte=flotte, aleatoire=aleatoire)


def synchroniser_vaisseau_depuis_combat(partie: Partie, vaisseau: Vaisseau) -> Partie:
    """Reporte sur la partie sauvegardee les PV du vaisseau tel qu'il ressort d'un combat
    (degats subis, soins recus) - operation inverse de combat_depuis_partie, indispensable pour
    que les degats persistent reellement d'un combat a l'autre (specs.md 2.2/3.4). A appeler des
    qu'un combat se termine (victoire), avant de sauvegarder la partie - `main.py:_ouvrir_combat`
    (PC) et `web/bridge.py:resoudre_victoire_partie_web` (web).

    Ne touche qu'aux PV : ni pv_max (ne change que via Ameliorer, Station service), ni le
    bouclier (mecanique de combat ephemere, non persistee, absente d'EtatModule). Modifie et
    renvoie `partie`."""
    partie.vaisseau["base"].pv = vaisseau.base.pv
    modules_equipes = vaisseau.modules_equipes()
    for cle, position in _POSITIONS_GAMEPLAY_PAR_CLE.items():
        etat = partie.vaisseau[cle]
        module = modules_equipes.get(position)
        if etat is not None and module is not None:
            etat.pv = module.pv
    return partie


ARGENT_PAR_ENNEMI_TUE = 5


def gagner_argent_combat(partie: Partie, combat: Combat) -> Partie:
    """Recompense en Argent d'une victoire (specs.md 2.1) : ARGENT_PAR_ENNEMI_TUE par ennemi de la
    flotte affrontee (combat.flotte.positions(), qui compte aussi les ennemis detruits - une
    victoire suppose que toute la flotte l'est). A appeler uniquement apres une victoire
    (combat.etat == EtatCombat.VICTOIRE), au meme moment que synchroniser_vaisseau_depuis_combat.
    Modifie et renvoie `partie`."""
    partie.argent += ARGENT_PAR_ENNEMI_TUE * len(combat.flotte.positions())
    return partie


# --- Progression (specs.md 2.4) : fonctions pures utilisees par l'enchainement des ecrans, cote
# PC (main.py) comme cote web (web/bridge.py) ---


def equiper_module(partie: Partie, spec: SpecModule) -> Partie:
    """Equipe ce module sur le premier emplacement libre du vaisseau (specs.md 2.3/5) - utilise
    par le choix de module du Niveau 1 (un seul emplacement libre a ce stade). Modifie et renvoie
    `partie`."""
    position = next(p for p in POSITIONS_EQUIPABLES if partie.vaisseau[p] is None)
    pv = _pv_module_initial(spec)
    partie.vaisseau[position] = EtatModule(module_id=spec.id, pv=pv, pv_max=pv, niveau_maj=1)
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


# --- Station service (garage), specs.md 2.2 : 4 actions couttant chacune COUT_ACTION_STATION_
# SERVICE en Argent, appliquees a un module equipe de la partie, partagees PC/web ---

PV_REPARATION = 20
PV_AMELIORATION = 10
NIVEAU_MAJ_MAX = 3
COUT_ACTION_STATION_SERVICE = 20


def _payer_action_station_service(partie: Partie) -> bool:
    """Deduit COUT_ACTION_STATION_SERVICE de l'Argent de la partie si elle en a assez (specs.md
    2.1/2.2). Ne modifie rien et renvoie False si l'Argent est insuffisant - a l'appelant de ne
    pas appliquer l'effet de l'action dans ce cas."""
    if partie.argent < COUT_ACTION_STATION_SERVICE:
        return False
    partie.argent -= COUT_ACTION_STATION_SERVICE
    return True


def reparer_module(partie: Partie, position: str) -> bool:
    """Restaure PV_REPARATION PV au module de cet emplacement, plafonne a son pv_max (specs.md
    2.2), contre COUT_ACTION_STATION_SERVICE d'Argent (specs.md 2.1). S'applique au module
    principal comme aux modules equipes. Modifie `partie` et renvoie True si l'Argent etait
    suffisant, sinon ne fait rien et renvoie False."""
    if not _payer_action_station_service(partie):
        return False
    etat = partie.vaisseau[position]
    etat.pv = min(etat.pv + PV_REPARATION, etat.pv_max)
    return True


def _effet_ameliorer_module(partie: Partie, position: str) -> None:
    """Coeur de l'effet Ameliorer (specs.md 2.2) : augmente le pv_max du module de cet
    emplacement de PV_AMELIORATION, et ses PV actuels du meme montant (pas seulement le plafond).
    Partage entre ameliorer_module (Station service, payant) et ameliorer_module_aventure
    (specs.md 2.5, gratuit) - pas de cout applique ici, a la charge de l'appelant."""
    etat = partie.vaisseau[position]
    etat.pv_max += PV_AMELIORATION
    etat.pv += PV_AMELIORATION


def ameliorer_module(partie: Partie, position: str) -> bool:
    """Effet Ameliorer (_effet_ameliorer_module) contre COUT_ACTION_STATION_SERVICE d'Argent
    (specs.md 2.1/2.2). S'applique au module principal comme aux modules equipes. Modifie
    `partie` et renvoie True si l'Argent etait suffisant, sinon ne fait rien et renvoie False."""
    if not _payer_action_station_service(partie):
        return False
    _effet_ameliorer_module(partie, position)
    return True


def mettre_a_jour_module(partie: Partie, position: str) -> bool:
    """Fait progresser d'un palier le niveau de mise a jour du module de cet emplacement (1 a
    NIVEAU_MAJ_MAX, specs.md 2.2/6) - determine le palier de rarete propose en recompense/a la
    Planete commerciale - contre COUT_ACTION_STATION_SERVICE d'Argent (specs.md 2.1). S'applique
    au module principal comme aux modules equipes. Modifie `partie` et renvoie True si l'Argent
    etait suffisant, sinon ne fait rien et renvoie False."""
    if not _payer_action_station_service(partie):
        return False
    etat = partie.vaisseau[position]
    etat.niveau_maj = min(etat.niveau_maj + 1, NIVEAU_MAJ_MAX)
    return True


def deplacer_module(partie: Partie, position_source: str, position_destination: str) -> bool:
    """Echange les modules de deux emplacements equipables (specs.md 2.2 : vide, le module y est
    simplement deplace ; occupe, les deux modules echangent leur position), contre
    COUT_ACTION_STATION_SERVICE d'Argent (specs.md 2.1). Ne s'applique jamais au module principal
    ('base') - a l'appelant (ecran Station service) de ne jamais transmettre cette position.
    Modifie `partie` et renvoie True si l'Argent etait suffisant, sinon ne fait rien et renvoie
    False."""
    if not _payer_action_station_service(partie):
        return False
    partie.vaisseau[position_source], partie.vaisseau[position_destination] = (
        partie.vaisseau[position_destination],
        partie.vaisseau[position_source],
    )
    return True


# --- Aventures (specs.md 2.5) : effets appliques a une partie sauvegardee, partages PC/web ---

PV_REPARATION_VAISSEAU = 5


def reparer_vaisseau(partie: Partie) -> Partie:
    """Restaure PV_REPARATION_VAISSEAU PV a CHAQUE module equipe (base + equipables), plafonne a
    son pv_max chacun (specs.md 2.5, Aventure "Trois lunes") - contrairement a reparer_module
    (§2.2) qui ne cible qu'un seul module choisi. Modifie et renvoie `partie`."""
    for position in POSITIONS_VAISSEAU:
        etat = partie.vaisseau[position]
        if etat is not None:
            etat.pv = min(etat.pv + PV_REPARATION_VAISSEAU, etat.pv_max)
    return partie


def retirer_carte(partie: Partie, id_carte: str) -> Partie:
    """Retire un exemplaire de cette carte du deck possede de la partie (specs.md 2.5, Aventure
    "Trois lunes") - operation inverse de ajouter_carte. Modifie et renvoie `partie`."""
    partie.deck.remove(id_carte)
    return partie


def ameliorer_module_aventure(partie: Partie, position: str) -> Partie:
    """Meme effet que ameliorer_module (_effet_ameliorer_module, §2.2), mais gratuit (specs.md
    2.5, Aventure "Trois lunes") : contrairement a la Station service, aucun cout en Argent.
    Modifie et renvoie `partie`."""
    _effet_ameliorer_module(partie, position)
    return partie


DEGATS_ASTEROIDES = 5


def subir_degats_module(partie: Partie, position: str, degats: int) -> Partie:
    """Inflige `degats` PV au module de cet emplacement, plafonne a 0 (specs.md 2.5, Aventure
    "Asteroides") - operation inverse de reparer_module/reparer_vaisseau, mais hors combat (pas de
    bouclier ici, EtatModule n'en persiste pas). Modifie et renvoie `partie`."""
    etat = partie.vaisseau[position]
    etat.pv = max(etat.pv - degats, 0)
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
