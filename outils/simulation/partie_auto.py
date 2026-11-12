"""
Partie complete jouee automatiquement (specs/simulation.md 5) : suit l'enchainement decide par
src/gameplay/deroulement.py, le bot de recherche du combat de la refonte (bot_new.py) pour les
combats, et une politique par defaut simple pour les decisions hors combat (5.1).

Tout le hasard derive de la graine de la partie, du niveau et de l'usage (_aleatoire) : rejouer
une graine avec les memes choix imposes redonne exactement la meme partie. C'est ce qui permet de
"cloner" une partie a un point de decision (5.2) en la rejouant avec un autre choix.
"""

import random
from dataclasses import dataclass, field

from src.gameplay import deroulement
from src.gameplay.carte_new import charger_cartes_new
from src.gameplay.combat_new import EtatCombatNew
from src.gameplay.deroulement import Ecran
from src.gameplay.module_new import charger_modules_new
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import (
    COUT_ACTION_STATION_SERVICE,
    COUT_METTRE_AUX_NORMES,
    DEGATS_ASTEROIDES,
    Partie,
    ajouter_carte,
    ameliorer_module,
    ameliorer_module_aventure,
    combat_depuis_partie,
    demarrer_aventure_police,
    nouvelle_partie,
    payer_mise_aux_normes,
    reparer_principal,
    retirer_carte,
    second_choc_asteroides,
    subir_degats_principal,
)

from outils.simulation.bot_new import BotRecherche, jouer_combat

# Garde-fou : etapes au-dela desquelles une partie est arretee
ETAPES_MAX = 40
# Choix du prochain niveau : aller en Station service si le principal est sous cette part de ses PV
SEUIL_PV_STATION = 0.5
# Station service : reparer le principal s'il lui manque au moins ce nombre de PV
MANQUE_PV_REPARATION = 15


def _aleatoire(partie: Partie, usage: str) -> random.Random:
    """Generateur derive de la graine, du niveau et de l'usage (memes tirages pour deux clones)."""
    return random.Random(f"{partie.graine}:{partie.niveau}:{usage}")


def _la_plus_rare(cartes: list):
    """Politique par defaut des choix de carte : la plus rare, la premiere a egalite."""
    return max(cartes, key=lambda carte: carte.rarete.value) if cartes else None


@dataclass
class ResultatPartie:
    graine: int
    module_id: str
    victoire_finale: bool = False
    niveau_atteint: int = 1
    pv_principal_fin: int = 0
    pv_principal_max_fin: int = 0
    argent_fin: int = 0
    deck_fin: list[str] = field(default_factory=list)
    etapes: list[str] = field(default_factory=list)
    combats: list[dict] = field(default_factory=list)
    # Choix du prochain niveau : (index de decision, options distinctes proposees, option prise)
    decisions: list[tuple[int, list[str], str]] = field(default_factory=list)


def choisir_etape(partie: Partie, propositions: list[TypeEtape]) -> TypeEtape:
    """Politique par defaut du choix du prochain niveau (specs/simulation.md 5.1)."""
    base = partie.vaisseau["base"]
    if (
        TypeEtape.STATION_SERVICE in propositions
        and base.pv < SEUIL_PV_STATION * base.pv_max
        and partie.argent >= COUT_ACTION_STATION_SERVICE
    ):
        return TypeEtape.STATION_SERVICE
    for prefere in (TypeEtape.BOSS, TypeEtape.PRIME, TypeEtape.AVENTURE, TypeEtape.STATION_SERVICE):
        if prefere in propositions:
            return prefere
    return propositions[0]


def _station_service(partie: Partie) -> None:
    """Depense l'Argent : reparer le principal s'il est entame, sinon l'ameliorer."""
    while partie.argent >= COUT_ACTION_STATION_SERVICE:
        base = partie.vaisseau["base"]
        if base.pv_max - base.pv >= MANQUE_PV_REPARATION:
            reparer_principal(partie)
        else:
            ameliorer_module(partie, "base")


def _aventure_asteroides(partie: Partie) -> Ecran:
    """Traverse le champ d'asteroides (les chocs touchent le principal) et prend la carte offerte."""
    subir_degats_principal(partie, DEGATS_ASTEROIDES)
    carte = second_choc_asteroides(partie, charger_cartes_new(), _aleatoire(partie, "asteroides"))
    if carte is not None:
        ajouter_carte(partie, carte.id, carte.exemplaire_module)
    return deroulement.terminer_etape(partie)


def _aventure_police(partie: Partie) -> Ecran:
    """Paie la mise aux normes si possible, sinon laisse confisquer la carte tiree."""
    etat = demarrer_aventure_police(partie, _aleatoire(partie, "police"))
    if partie.argent < COUT_METTRE_AUX_NORMES or not payer_mise_aux_normes(partie):
        retirer_carte(partie, etat.carte_actuelle)
    return deroulement.terminer_etape(partie)


def _combat(partie: Partie, resultat: ResultatPartie, combat, type_combat: str) -> Ecran:
    ennemis = [ennemi.nom for ennemi in combat.flotte.ennemis]
    stats = jouer_combat(combat, BotRecherche(_aleatoire(partie, "bot")))
    stats.update({"niveau": partie.niveau, "type": type_combat, "ennemis": ennemis})
    resultat.combats.append(stats)
    candidats = deroulement.conclure_combat(partie, combat, _aleatoire(partie, "recompense"))
    carte = _la_plus_rare([carte for _module, carte in candidats if carte is not None])
    victoire = combat.etat == EtatCombatNew.VICTOIRE
    return deroulement.resoudre_fin_combat(partie, victoire, carte)


def jouer_partie(
    graine: int, module_force: str | None = None, choix_imposes: dict[int, str] | None = None
) -> ResultatPartie:
    """Joue une partie complete. `module_force` : id du module du Niveau 1 (5.3) ;
    `choix_imposes` : {index de decision: TypeEtape.name} impose au choix du prochain niveau (5.2)."""
    choix_imposes = choix_imposes or {}
    modeles = charger_modules_new()
    partie = nouvelle_partie(random.Random(graine))

    # Niveau 1 : choix du module (force, sinon tire) puis de sa carte
    candidats = deroulement.candidats_choix_module(partie)
    modele = modeles[module_force] if module_force else _aleatoire(partie, "module").choice(candidats)
    cartes_module = deroulement.choisir_module(partie, modele, _aleatoire(partie, "carte_module"))
    ecran = deroulement.resoudre_carte_module(partie, _la_plus_rare(cartes_module))
    resultat = ResultatPartie(graine=graine, module_id=modele.id)

    index_decision = 0
    for _etape in range(ETAPES_MAX):
        if ecran in (Ecran.ACCUEIL, Ecran.VICTOIRE_FINALE):
            break
        if ecran != Ecran.CHOIX_NIVEAU:
            raise RuntimeError(f"Ecran inattendu hors etape : {ecran}")
        propositions = deroulement.propositions_niveau(partie)
        options = list(dict.fromkeys(type_etape.name for type_etape in propositions))
        choix = choisir_etape(partie, propositions).name
        if len(options) > 1:
            choix = choix_imposes.get(index_decision, choix)
            resultat.decisions.append((index_decision, options, choix))
            index_decision += 1
        ecran = deroulement.ecran_pour_etape(TypeEtape[choix], _aleatoire(partie, "aventure"))
        resultat.etapes.append(ecran.name)

        if ecran == Ecran.COMBAT:
            type_combat = "BOSS" if choix == "BOSS" else "PRIME"
            ecran = _combat(partie, resultat, combat_depuis_partie(partie, _aleatoire(partie, "combat")), type_combat)
        elif ecran == Ecran.STATION_SERVICE:
            _station_service(partie)
            ecran = deroulement.terminer_etape(partie)
        elif ecran == Ecran.AVENTURE_TROIS_LUNES:
            ameliorer_module_aventure(partie, "base")
            ecran = deroulement.terminer_etape(partie)
        elif ecran == Ecran.AVENTURE_ASTEROIDES:
            ecran = _aventure_asteroides(partie)
        elif ecran == Ecran.AVENTURE_POLICE:
            ecran = _aventure_police(partie)
        else:
            ecran = deroulement.terminer_etape(partie)

    if ecran == Ecran.VICTOIRE_FINALE:
        resultat.victoire_finale = True
        deroulement.terminer_victoire_finale(partie)
    base = partie.vaisseau["base"]
    resultat.niveau_atteint = partie.niveau
    resultat.pv_principal_fin = base.pv
    resultat.pv_principal_max_fin = base.pv_max
    resultat.argent_fin = partie.argent
    resultat.deck_fin = [carte.id for carte in partie.deck]
    return resultat
