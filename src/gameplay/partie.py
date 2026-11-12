"""
Persistance du parcours (specs.md 10.3) : profils joueur locaux et parties sauvegardees. Pas de
compte/login, mais plusieurs profils peuvent coexister sur un meme appareil. Chaque joueur ne peut
avoir qu'une seule partie EN_COURS a la fois (decision utilisateur).

Les fonctions vers_dict/depuis_dict/vers_json/depuis_json sont pures (testables sans I/O). L'I/O
fichier (PC uniquement, cf. web/bridge.py + web/app.js pour localStorage cote web) est regroupee en
bas de ce fichier.
"""

import functools
import json
import random
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.gameplay.carte_new import CarteNew, charger_cartes_new
from src.gameplay.combat_new import CombatNew
from src.gameplay.deck_new import DECK_DE_DEPART
from src.gameplay.ennemi_new import charger_ennemis_new
from src.gameplay.flotte_new import FlotteNew, flotte_asteroides, flotte_boss, flotte_prime
from src.gameplay.module_new import ModuleNew, charger_modules_new
from src.gameplay.parcours import est_niveau_boss, pool_toutes_cartes, tirer_carte_deck, tirer_carte_recompense

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_SAVES = RACINE / "saves"

# Version du format de sauvegarde d'une partie. 2 : moteur de la refonte (modules ModuleNew,
# cartes rattachees a un exemplaire de module). Une partie d'une autre version est abandonnee a la
# lecture (refonte-branchement.md 2, decision 1) : aucune conversion.
VERSION_FORMAT = 2
# Version du format d'un profil, independante : les profils sont gardes tels quels
VERSION_PROFIL = 1

# Un exemplaire de module par emplacement du vaisseau (specs.md 3.1/5) : la base (module
# principal, toujours equipee) et les 4 emplacements equipables. None = emplacement vide.
POSITIONS_EQUIPABLES = ("avant_gauche", "avant_droite", "arriere_gauche", "arriere_droite")
POSITIONS_VAISSEAU = ("base",) + POSITIONS_EQUIPABLES

STATUT_EN_COURS = "EN_COURS"
STATUT_TERMINEE = "TERMINEE"


class SauvegardeObsolete(ValueError):
    """Partie sauvegardee par une ancienne version du jeu : elle est abandonnee (decision 1)."""


@dataclass(frozen=True)
class CartePossedee:
    """Une carte du deck possede : l'id de son modele (config/carte_new.json) et l'exemplaire de
    module auquel elle est rattachee ("M1"...), stable meme si la Station deplace le module
    (refonte-modules.md 3.3)."""

    id: str
    module: str


@dataclass
class Partie:
    """Une sauvegarde de partie, rattachee a un profil (specs.md 10.3). `vaisseau` : exemplaire de
    module (ModuleNew, partie "exemplaire" seulement) de chaque emplacement."""

    id: str
    nom: str
    statut: str
    graine: int
    niveau: int
    argent: int
    vaisseau: dict[str, ModuleNew | None]
    deck: list[CartePossedee]
    version: int = VERSION_FORMAT

    @property
    def principal(self) -> ModuleNew:
        return self.vaisseau["base"]


@dataclass
class Profil:
    """Un profil joueur local (specs.md 10.3), distinct de l'etat de combat."""

    id: str
    nom: str
    version: int = VERSION_PROFIL


def _horodatage() -> str:
    """Horodatage avec microsecondes (pas seulement secondes) pour eviter toute collision
    d'id entre deux profils/parties crees dans la meme seconde."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


# --- Serialisation (pure, testable sans I/O) ---


def _module_vers_dict(module: ModuleNew) -> dict:
    """Ce qui est sauvegarde d'un exemplaire de module ; l'emplacement est la cle du vaisseau."""
    return {
        "module_id": module.id,
        "exemplaire": module.exemplaire,
        "pv": module.pv,
        "pv_max": module.pv_max,
        "niveau_maj": module.niveau_maj,
    }


def _module_depuis_dict(donnees: dict, emplacement: str, modeles: dict[str, ModuleNew]) -> ModuleNew:
    module = modeles[donnees["module_id"]].nouvel_exemplaire(donnees["exemplaire"], emplacement)
    module.pv_max = donnees["pv_max"]
    module.pv = donnees["pv"]
    module.niveau_maj = donnees["niveau_maj"]
    return module


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
            position: (_module_vers_dict(module) if module is not None else None)
            for position, module in partie.vaisseau.items()
        },
        "deck": [{"id": carte.id, "module": carte.module} for carte in partie.deck],
    }


@functools.cache
def _modeles_modules() -> dict[str, ModuleNew]:
    """Modeles de modules lus une seule fois (config/module_new.json) : la partie est relue a
    chaque action cote web. Jamais modifies : un exemplaire est une copie (nouvel_exemplaire)."""
    return charger_modules_new()


def partie_depuis_dict(donnees: dict, modeles: dict[str, ModuleNew] | None = None) -> Partie:
    """Partie a partir de sa sauvegarde. Leve SauvegardeObsolete pour une autre version du format
    (ancienne sauvegarde, decision 1)."""
    version = donnees.get("version", 1)
    if version != VERSION_FORMAT:
        raise SauvegardeObsolete(f"Partie au format {version}, format attendu {VERSION_FORMAT}")
    modeles = modeles if modeles is not None else _modeles_modules()
    return Partie(
        id=donnees["id"],
        nom=donnees["nom"],
        statut=donnees["statut"],
        graine=donnees["graine"],
        niveau=donnees["niveau"],
        argent=donnees["argent"],
        vaisseau={
            position: (_module_depuis_dict(module, position, modeles) if module is not None else None)
            for position, module in donnees["vaisseau"].items()
        },
        deck=[CartePossedee(id=carte["id"], module=carte["module"]) for carte in donnees["deck"]],
        version=version,
    )


def partie_vers_json(partie: Partie) -> str:
    return json.dumps(partie_vers_dict(partie))


def partie_depuis_json(texte: str) -> Partie:
    return partie_depuis_dict(json.loads(texte))


def lire_partie(texte: str) -> Partie | None:
    """Partie sauvegardee, ou None si elle vient d'une ancienne version du jeu (abandonnee,
    decision 1) : a l'appelant de l'effacer (fichier cote PC, localStorage cote web)."""
    try:
        return partie_depuis_json(texte)
    except SauvegardeObsolete:
        return None


def profil_vers_dict(profil: Profil) -> dict:
    return {"version": profil.version, "id": profil.id, "nom": profil.nom}


def profil_depuis_dict(donnees: dict) -> Profil:
    return Profil(id=donnees["id"], nom=donnees["nom"], version=donnees.get("version", VERSION_PROFIL))


def profil_vers_json(profil: Profil) -> str:
    return json.dumps(profil_vers_dict(profil))


def profil_depuis_json(texte: str) -> Profil:
    return profil_depuis_dict(json.loads(texte))


# --- Creation ---


def nouveau_profil(nom: str) -> Profil:
    return Profil(id=f"joueur_{_horodatage()}", nom=nom)


ARGENT_DEPART = 7
# Identifiant d'exemplaire du principal, premier module de toute partie
EXEMPLAIRE_PRINCIPAL = "M1"


def nouvelle_partie(aleatoire: random.Random | None = None) -> Partie:
    """Nouvelle partie au Niveau 1 (specs.md 2.3) : seul le module principal est equipe (le 2e
    slot est pourvu par le choix de module du Niveau 1), avec le deck de depart
    (deck_new.DECK_DE_DEPART) rattache au principal. Argent a ARGENT_DEPART (specs.md 2.1/9.1)."""
    aleatoire = aleatoire or random.Random()
    modele_principal = next(module for module in charger_modules_new().values() if module.principal)
    vaisseau: dict[str, ModuleNew | None] = {position: None for position in POSITIONS_VAISSEAU}
    vaisseau["base"] = modele_principal.nouvel_exemplaire(EXEMPLAIRE_PRINCIPAL, "base")
    return Partie(
        id=f"partie_{_horodatage()}",
        nom=f"Partie du {datetime.now():%d/%m/%Y}",
        statut=STATUT_EN_COURS,
        graine=aleatoire.randrange(2**31),
        niveau=1,
        argent=ARGENT_DEPART,
        vaisseau=vaisseau,
        deck=[
            CartePossedee(id=id_carte, module=EXEMPLAIRE_PRINCIPAL)
            for id_carte, nombre in DECK_DE_DEPART.items()
            for _ in range(nombre)
        ],
    )


def modules_de_la_partie(partie: Partie) -> list[ModuleNew]:
    """Exemplaires de modules equipes, principal en premier (ordre de POSITIONS_VAISSEAU)."""
    return [partie.vaisseau[position] for position in POSITIONS_VAISSEAU if partie.vaisseau[position] is not None]


def deck_de_la_partie(partie: Partie, cartes: dict[str, CarteNew] | None = None) -> list[CarteNew]:
    """Exemplaires CarteNew independants du deck possede, rattaches a leur module - pour afficher
    le deck ou le donner a un combat."""
    cartes = cartes if cartes is not None else charger_cartes_new()
    return [cartes[carte.id].copie(exemplaire_module=carte.module) for carte in partie.deck]


def _combat(partie: Partie, flotte: FlotteNew, aleatoire: random.Random) -> CombatNew:
    """Combat avec le vaisseau et le deck de la partie : copies de combat des modules (PV
    sauvegardes pour le principal, PV max pour les secondaires), copies des cartes. La partie
    n'est pas modifiee (un combat abandonne ne la touche pas)."""
    if partie.principal.pv <= 0:
        # Garde-fou : CombatNew ne declare la defaite que sur un nouveau coup, un combat commence
        # avec un principal deja detruit ne se terminerait jamais
        raise ValueError("Le principal est detruit : aucun combat ne peut commencer")
    modules = [module.copie_pour_combat() for module in modules_de_la_partie(partie)]
    return CombatNew(modules, deck_de_la_partie(partie), flotte, aleatoire)


def combat_depuis_partie(partie: Partie, aleatoire: random.Random | None = None) -> CombatNew:
    """Combat du niveau courant (specs.md 2.1/2.3/13) : flotte du Boss aux niveaux Boss, sinon
    flotte Prime (1 ennemi jusqu'au Niveau 5, 2 au-dela), flotte_new.py."""
    aleatoire = aleatoire or random.Random(partie.graine + partie.niveau)
    modeles = charger_ennemis_new()
    flotte = flotte_boss(modeles) if est_niveau_boss(partie.niveau) else flotte_prime(modeles, partie.niveau, aleatoire)
    return _combat(partie, flotte, aleatoire)


def combat_aventure_asteroides(partie: Partie, aleatoire: random.Random | None = None) -> CombatNew:
    """Combat du choix "Affronter les pirates" (Aventure Asteroides, specs.md 2.5) :
    NOMBRE_ENNEMIS_ASTEROIDES ennemis (flotte_asteroides)."""
    aleatoire = aleatoire or random.Random(partie.graine + partie.niveau)
    return _combat(partie, flotte_asteroides(charger_ennemis_new(), aleatoire), aleatoire)


def reporter_combat(partie: Partie, combat: CombatNew) -> Partie:
    """Fin de combat (victoire ou defaite) : reporte sur la partie ce qui persiste, c'est-a-dire
    les PV du principal seulement (ModuleNew.reporter_combat ; un secondaire repart plein au
    combat suivant). A appeler une fois, par deroulement.conclure_combat. Modifie et renvoie
    `partie`."""
    for module in modules_de_la_partie(partie):
        copie = combat.vaisseau.module_d_exemplaire(module.exemplaire)
        if copie is not None:
            module.reporter_combat(copie)
    return partie


ARGENT_PAR_ENNEMI_TUE = 5


def gagner_argent_combat(partie: Partie, combat: CombatNew) -> Partie:
    """Recompense en Argent d'une victoire (specs.md 2.1) : ARGENT_PAR_ENNEMI_TUE par ennemi
    detruit (le Boss, sur deux cases, compte pour un). Modifie et renvoie `partie`."""
    partie.argent += ARGENT_PAR_ENNEMI_TUE * len(combat.ennemis_detruits())
    return partie


# --- Progression (specs.md 2.4) : fonctions pures utilisees par l'enchainement des ecrans
# (deroulement.py) ---


def _nouvel_exemplaire(partie: Partie) -> str:
    """Identifiant d'exemplaire jamais utilise dans la partie : "M" suivi du plus grand numero vu
    (modules equipes et cartes du deck, pour ne jamais rattacher d'anciennes cartes a un nouveau
    module si un module quitte un jour le vaisseau) plus un."""
    exemplaires = [module.exemplaire for module in modules_de_la_partie(partie)] + [carte.module for carte in partie.deck]
    numeros = [int(exemplaire[1:]) for exemplaire in exemplaires]
    return f"M{max(numeros, default=0) + 1}"


def equiper_module(partie: Partie, modele: ModuleNew) -> ModuleNew:
    """Equipe un nouvel exemplaire de ce module sur le premier emplacement libre du vaisseau
    (specs.md 2.3/5), PV pleins. Modifie `partie` et renvoie l'exemplaire equipe."""
    position = next(p for p in POSITIONS_EQUIPABLES if partie.vaisseau[p] is None)
    module = modele.nouvel_exemplaire(_nouvel_exemplaire(partie), position)
    partie.vaisseau[position] = module
    return module


def avancer_niveau(partie: Partie) -> Partie:
    """Fait passer la partie au niveau suivant (specs.md 2.4). Modifie et renvoie `partie`."""
    partie.niveau += 1
    return partie


def ajouter_carte(partie: Partie, id_carte: str, exemplaire_module: str) -> Partie:
    """Ajoute une carte au deck possede, rattachee a cet exemplaire de module (recompense de fin
    de combat, specs.md 6). Modifie et renvoie `partie`."""
    if exemplaire_module not in {module.exemplaire for module in modules_de_la_partie(partie)}:
        raise ValueError(f"Carte {id_carte} : module {exemplaire_module} absent du vaisseau")
    partie.deck.append(CartePossedee(id=id_carte, module=exemplaire_module))
    return partie


# --- Station service (garage), specs.md 2.2 : 4 actions coutant chacune COUT_ACTION_STATION_
# SERVICE en Argent, partagees PC/web ---

PV_REPARATION = 20
PV_AMELIORATION = 10
NIVEAU_MAJ_MAX = 3
COUT_ACTION_STATION_SERVICE = 20


def _payer_action_station_service(partie: Partie) -> bool:
    """Deduit COUT_ACTION_STATION_SERVICE de l'Argent de la partie si elle en a assez (specs.md
    2.1/2.2). Ne modifie rien et renvoie False si l'Argent est insuffisant."""
    if partie.argent < COUT_ACTION_STATION_SERVICE:
        return False
    partie.argent -= COUT_ACTION_STATION_SERVICE
    return True


def reparer_principal(partie: Partie) -> bool:
    """Restaure PV_REPARATION PV au module principal, plafonne a son pv_max (specs.md 2.2), contre
    COUT_ACTION_STATION_SERVICE d'Argent. Seul le principal se repare : un secondaire repart plein
    a chaque combat (refonte-branchement.md 2, decision 2). Renvoie False, sans rien modifier, si
    l'Argent est insuffisant."""
    if not _payer_action_station_service(partie):
        return False
    principal = partie.principal
    principal.pv = min(principal.pv + PV_REPARATION, principal.pv_max)
    return True


def _effet_ameliorer_module(partie: Partie, position: str) -> None:
    """Coeur de l'effet Ameliorer (specs.md 2.2) : +PV_AMELIORATION au pv_max du module de cet
    emplacement, et a ses PV du meme montant. Partage entre ameliorer_module (Station service,
    payant) et ameliorer_module_aventure (specs.md 2.5, gratuit)."""
    module = partie.vaisseau[position]
    module.pv_max += PV_AMELIORATION
    module.pv += PV_AMELIORATION


def ameliorer_module(partie: Partie, position: str) -> bool:
    """Effet Ameliorer contre COUT_ACTION_STATION_SERVICE d'Argent (specs.md 2.1/2.2), sur tout
    module equipe. Renvoie False, sans rien modifier, si l'Argent est insuffisant."""
    if not _payer_action_station_service(partie):
        return False
    _effet_ameliorer_module(partie, position)
    return True


def mettre_a_jour_module(partie: Partie, position: str) -> bool:
    """Fait progresser d'un palier le niveau de mise a jour du module de cet emplacement (1 a
    NIVEAU_MAJ_MAX, specs.md 2.2/6), contre COUT_ACTION_STATION_SERVICE d'Argent. Renvoie False,
    sans rien modifier, si l'Argent est insuffisant."""
    if not _payer_action_station_service(partie):
        return False
    module = partie.vaisseau[position]
    module.niveau_maj = min(module.niveau_maj + 1, NIVEAU_MAJ_MAX)
    return True


def deplacer_module(partie: Partie, position_source: str, position_destination: str) -> bool:
    """Echange les modules de deux emplacements equipables (specs.md 2.2 : vide, le module y est
    simplement deplace ; occupe, les deux modules echangent leur position), contre
    COUT_ACTION_STATION_SERVICE d'Argent. Jamais le principal ('base'). Les cartes restent
    rattachees a leur exemplaire. Renvoie False, sans rien modifier, si l'Argent est insuffisant."""
    if "base" in (position_source, position_destination):
        raise ValueError("Le module principal ne se deplace pas")
    if not _payer_action_station_service(partie):
        return False
    source, destination = partie.vaisseau[position_source], partie.vaisseau[position_destination]
    partie.vaisseau[position_source], partie.vaisseau[position_destination] = destination, source
    for position in (position_source, position_destination):
        if partie.vaisseau[position] is not None:
            partie.vaisseau[position].emplacement = position
    return True


# --- Aventures (specs.md 2.5) : effets appliques a une partie sauvegardee, partages PC/web ---

PV_REPARATION_VAISSEAU = 5


def reparer_vaisseau(partie: Partie) -> Partie:
    """Aventure "Trois lunes", Reparer le vaisseau (specs.md 2.5) : +PV_REPARATION_VAISSEAU PV au
    principal, plafonne a son pv_max - seul module dont les PV persistent (decision 3). Modifie et
    renvoie `partie`."""
    principal = partie.principal
    principal.pv = min(principal.pv + PV_REPARATION_VAISSEAU, principal.pv_max)
    return partie


def retirer_carte(partie: Partie, carte: CartePossedee) -> Partie:
    """Retire un exemplaire de cette carte (meme id, meme module) du deck possede (specs.md 2.5,
    Aventures "Trois lunes" et "Police"). Modifie et renvoie `partie`."""
    partie.deck.remove(carte)
    return partie


def ameliorer_module_aventure(partie: Partie, position: str) -> Partie:
    """Meme effet que ameliorer_module (_effet_ameliorer_module, §2.2), mais gratuit (specs.md
    2.5, Aventure "Trois lunes"). Modifie et renvoie `partie`."""
    _effet_ameliorer_module(partie, position)
    return partie


DEGATS_ASTEROIDES = 5
# Les chocs d'Asteroides laissent toujours au moins ce nombre de PV au principal (decision
# utilisateur, 2026-11-12) : un combat ne commence jamais avec un principal detruit
PV_MIN_APRES_ASTEROIDES = 1


def subir_degats_principal(partie: Partie, degats: int) -> Partie:
    """Inflige `degats` PV au principal sans descendre sous PV_MIN_APRES_ASTEROIDES (specs.md 2.5,
    Aventure "Asteroides") : les chocs touchent toujours le principal (decision 3). Hors combat,
    pas de bouclier. Modifie et renvoie `partie`."""
    principal = partie.principal
    principal.pv = max(principal.pv - degats, min(principal.pv, PV_MIN_APRES_ASTEROIDES))
    return partie


def second_choc_asteroides(partie: Partie, cartes: dict[str, CarteNew], aleatoire: random.Random) -> CarteNew | None:
    """2e choc du choix "Traverser" de l'Aventure "Asteroides" (specs.md 2.5) : inflige un second
    DEGATS_ASTEROIDES au principal puis tire une carte gratuite du pool complet de cartes
    jouables (tirer_carte_recompense), rattachee au principal (carte obtenue hors module,
    refonte-modules.md 3.3) - None si le pool est vide. Decide seule si une carte est offerte :
    PC et web ne font qu'afficher le resultat. Modifie `partie`."""
    subir_degats_principal(partie, DEGATS_ASTEROIDES)
    carte = tirer_carte_recompense(pool_toutes_cartes(cartes), aleatoire)
    return carte.copie(exemplaire_module=partie.principal.exemplaire) if carte else None


COUT_METTRE_AUX_NORMES = 10


def payer_mise_aux_normes(partie: Partie) -> bool:
    """Deduit COUT_METTRE_AUX_NORMES d'Argent si la partie en a assez (Aventure "Police", specs.md
    2.5, choix "Mettre aux normes" - garde la carte tiree). Renvoie True si l'Argent etait
    suffisant (et deduit), sinon ne modifie rien et renvoie False."""
    if partie.argent < COUT_METTRE_AUX_NORMES:
        return False
    partie.argent -= COUT_METTRE_AUX_NORMES
    return True


@dataclass
class EtatAventurePolice:
    """Etat de resolution en cours de l'Aventure "Police" (specs.md 2.5) - local a une Aventure,
    jamais persiste sur Partie. PC et web gardent une reference a cet objet plutot que de suivre
    `detourner_disponible` eux-memes."""

    carte_actuelle: CartePossedee
    detourner_disponible: bool = True


def demarrer_aventure_police(partie: Partie, aleatoire: random.Random) -> EtatAventurePolice:
    """Tire la premiere carte du deck reel de la partie (specs.md 2.5) et initialise l'etat de
    resolution de l'Aventure "Police"."""
    return EtatAventurePolice(carte_actuelle=tirer_carte_deck(partie.deck, aleatoire))


def detourner_aventure_police(etat: EtatAventurePolice, partie: Partie, aleatoire: random.Random) -> bool:
    """Choix "Detourner l'attention" (specs.md 2.5) : tire une nouvelle carte du deck reel de la
    partie. Disponible une seule fois par Aventure - ne fait rien et renvoie False si deja
    utilise, sinon modifie `etat` et renvoie True."""
    if not etat.detourner_disponible:
        return False
    etat.carte_actuelle = tirer_carte_deck(partie.deck, aleatoire)
    etat.detourner_disponible = False
    return True


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


def supprimer_profil(joueur_id: str) -> None:
    """Supprime definitivement un profil (PC) et toutes ses parties sauvegardees - action
    destructive, l'UI (ecran_selection_joueur.py) doit demander confirmation avant d'appeler
    cette fonction. Ne fait rien si le dossier n'existe pas (deja supprime)."""
    shutil.rmtree(_dossier_profil(joueur_id), ignore_errors=True)


def partie_en_cours(joueur_id: str) -> Partie | None:
    """La partie EN_COURS de ce joueur, s'il en a une (il ne peut y en avoir qu'une a la fois,
    garanti par sauvegarder_partie/abandonner_partie ci-dessous). Une partie EN_COURS d'une
    ancienne version du jeu est effacee au passage (decision 1) ; les parties TERMINEE et le
    profil sont gardes."""
    dossier = _dossier_parties(joueur_id)
    if not dossier.exists():
        return None
    for fichier in dossier.iterdir():
        texte = fichier.read_text()
        partie = lire_partie(texte)
        if partie is None:
            # Ancienne version du jeu : une partie EN_COURS est abandonnee et effacee (decision 1) ;
            # une partie TERMINEE est gardee telle quelle (futures statistiques), sans etre relue
            if json.loads(texte).get("statut") == STATUT_EN_COURS:
                fichier.unlink()
        elif partie.statut == STATUT_EN_COURS:
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
