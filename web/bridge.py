"""
Pont entre le JS de la page web et le moteur de jeu Python (src/gameplay/), execute tel quel
dans le navigateur via Pyodide. Aucune regle de jeu ici : ce fichier ne fait que traduire l'etat
du gameplay en JSON (presentation comprise : popups, phrases du journal mises en forme cote JS a
partir des memes champs) et router les actions du joueur.

Combat : moteur de la refonte (CombatNew, specs/refonte-combat.md), branche au parcours depuis la
PR 1 (specs/refonte-branchement.md). Le combat de demonstration n'existe plus : on ne joue que par
le parcours (decision utilisateur, 2026-11-12).
"""

import json
import random
import sys

sys.path.insert(0, "/repo")

from src.gameplay import deroulement
from src.gameplay.carte_new import Camp, CarteNew, charger_cartes_new
from src.gameplay.combat_new import ELECTRICITE_PAR_TOUR, NatureEvenement
from src.gameplay.ennemi_new import CibleEffetEnnemi, EnnemiNew
from src.gameplay.module_new import ModuleNew, charger_modules_new
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import (
    COUT_ACTION_STATION_SERVICE,
    COUT_METTRE_AUX_NORMES,
    DEGATS_ASTEROIDES,
    PV_AMELIORATION,
    PV_REPARATION,
    PV_REPARATION_VAISSEAU,
    CartePossedee,
    ancienne_partie_a_effacer,
    ajouter_carte,
    ameliorer_module,
    ameliorer_module_aventure,
    combat_aventure_asteroides,
    combat_depuis_partie,
    deck_de_la_partie,
    demarrer_aventure_police,
    deplacer_module,
    detourner_aventure_police,
    lire_partie,
    marquer_terminee,
    mettre_a_jour_module,
    modules_de_la_partie,
    nouveau_profil,
    nouvelle_partie,
    partie_depuis_json,
    partie_vers_json,
    payer_mise_aux_normes,
    profil_vers_json,
    reparer_principal,
    reparer_vaisseau,
    retirer_carte,
    second_choc_asteroides,
    subir_degats_principal,
)
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.statut_new import Statut

# Image du principal recadree pour une case de la taille des autres modules (Station service,
# accueil joueur) ; dans le combat, le principal garde son image entiere (le vaisseau)
IMAGE_CASE_PRINCIPAL = "assets/modules/principal_avant.png"

# Cases du joueur : le principal occupe les deux cases de la rangee du milieu
IDS_MODULES = {
    "AV_G": Position(Colonne.AVANT, Rangee.GAUCHE),
    "AV_D": Position(Colonne.AVANT, Rangee.DROITE),
    "AR_G": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "AR_D": Position(Colonne.ARRIERE, Rangee.DROITE),
}
CASE_PRINCIPAL = Position(Colonne.AVANT, Rangee.MID)
# Emplacement d'un module (ModuleNew.emplacement) -> id de case
IDS_PAR_EMPLACEMENT = {"base": "base", "avant_gauche": "AV_G", "avant_droite": "AV_D", "arriere_gauche": "AR_G", "arriere_droite": "AR_D"}
IDS_ENNEMIS = {
    "AV_G": Position(Colonne.AVANT, Rangee.GAUCHE),
    "AV_M": Position(Colonne.AVANT, Rangee.MID),
    "AV_D": Position(Colonne.AVANT, Rangee.DROITE),
    "AR_G": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "AR_M": Position(Colonne.ARRIERE, Rangee.MID),
    "AR_D": Position(Colonne.ARRIERE, Rangee.DROITE),
}
_PAIRES_CASES_ENNEMIES = (("AV_G", "AR_G"), ("AV_M", "AR_M"), ("AV_D", "AR_D"))

combat = None
# Taille du journal deja transmise : les popups d'une action sont calcules a partir des seules
# entrees ajoutees depuis (combat.journal[n:])
taille_journal_transmise = 0
# Etat de resolution de l'Aventure "Police" en cours (EtatAventurePolice), possede par le gameplay
etat_aventure_police = None


def _modeles_cartes() -> dict[str, CarteNew]:
    return charger_cartes_new()


def _noms_modules_partie(partie) -> dict[str, str]:
    """Exemplaire de module ("M2") -> nom affiche, pour dire a quel module une carte appartient."""
    return {module.exemplaire: module.nom for module in modules_de_la_partie(partie)}


# --- Cartes (hors combat et en combat) ---


def _carte_json(carte: CarteNew, nom_module: str | None = None) -> dict:
    """Une carte, telle que l'affichent tous les ecrans : texte de carte_new.json avec les valeurs
    actuelles (description_affichee), cout, munitions, lancements, mot-cle Persistante."""
    return {
        "id_carte": carte.id,
        "module": carte.exemplaire_module,
        "module_nom": nom_module,
        "nom": carte.nom,
        "image": carte.image,
        "cout": carte.cout,
        "rarete": carte.rarete.name,
        "description": carte.description_affichee(),
        "munitions_base": carte.munitions_base,
        "munitions_restantes": carte.munitions_restantes,
        "lancements": carte.lancements_actuels,
        "persistante": carte.persistante,
    }


def _cartes_regroupees_json(cartes: list[CarteNew], noms_modules: dict[str, str]) -> list[dict]:
    """Regroupe les exemplaires identiques (meme carte, meme module) en une entree avec quantite."""
    groupes: dict[tuple[str, str | None], list[CarteNew]] = {}
    for carte in cartes:
        groupes.setdefault((carte.id, carte.exemplaire_module), []).append(carte)
    resultat = []
    for exemplaires in groupes.values():
        entree = _carte_json(exemplaires[0], noms_modules.get(exemplaires[0].exemplaire_module))
        entree["quantite"] = len(exemplaires)
        resultat.append(entree)
    return resultat


def _carte_proposee(id_carte: str, exemplaire_module: str) -> CarteNew:
    """Carte choisie par le joueur parmi celles proposees (JS renvoie son id et son module)."""
    return _modeles_cartes()[id_carte].copie(exemplaire_module=exemplaire_module)


# --- Combat : cases ---


def _id_case_module(module: ModuleNew) -> str | None:
    return IDS_PAR_EMPLACEMENT.get(module.emplacement)


def _id_case_ennemi(ennemi: EnnemiNew) -> str | None:
    """Case Avant de la rangee pour un ennemi sur deux cases (le Boss), sinon sa case."""
    cases = combat.flotte.cases_de(ennemi)
    case = next((c for c in cases if c.colonne == Colonne.AVANT), cases[0])
    return next(id_case for id_case, position in IDS_ENNEMIS.items() if position == case)


def _id_case_entite(entite) -> tuple[str | None, str]:
    if isinstance(entite, ModuleNew):
        return _id_case_module(entite), "allie"
    return _id_case_ennemi(entite), "ennemi"


def _position_case(id_case: str, camp: str) -> Position:
    if camp == "allie":
        return CASE_PRINCIPAL if id_case == "base" else IDS_MODULES[id_case]
    return IDS_ENNEMIS[id_case]


def _ids_cases(positions: list[Position], camp: Camp) -> list[str]:
    """Ids des cases valides d'une carte (cibles_possibles), sans doublon (principal, Boss)."""
    ids = []
    for position in positions:
        if camp == Camp.JOUEUR:
            module = combat.vaisseau.module_en(position)
            id_case = _id_case_module(module) if module else None
        else:
            ennemi = combat.flotte.ennemi_en(position)
            id_case = _id_case_ennemi(ennemi) if ennemi else None
        if id_case is not None and id_case not in ids:
            ids.append(id_case)
    return ids


# --- Combat : etat ---


def _statuts_json(entite) -> dict:
    statuts = entite.statuts
    return {
        "bouclier": statuts[Statut.BOUCLIER],
        "incendie": statuts[Statut.INCENDIE],
        "renvoi": statuts[Statut.RENVOI],
        "leurre": statuts[Statut.LEURRE] > 0,
    }


def _menaces(intentions) -> dict[int, list[dict]]:
    """Attaques prevues au prochain tour ennemi, par module vise (id de l'objet module) : le
    module le plus proche pour une attaque PROXIMITE (cible prevue par CombatNew.intentions), tous
    les modules vivants pour TOUS_MODULES. Sert a marquer les modules vises."""
    menaces: dict[int, list[dict]] = {}
    for intention in intentions:
        for effet in intention.effets:
            if effet.effet.cible == CibleEffetEnnemi.TOUS_MODULES:
                vises = combat.vaisseau.modules_vivants()
            elif effet.effet.cible == CibleEffetEnnemi.PROXIMITE and effet.cible_prevue is not None:
                vises = [effet.cible_prevue]
            else:
                continue
            for module in vises:
                menaces.setdefault(id(module), []).append(
                    {"ennemi": intention.ennemi.nom, "valeur": effet.valeur, "repetitions": effet.effet.repetitions}
                )
    return menaces


def _module_json(module: ModuleNew | None, id_case: str, menaces: dict | None = None) -> dict | None:
    if module is None:
        return None
    hors_service = sum(carte.exemplaire_module == module.exemplaire for carte in combat.deck.hors_service)
    return {
        "id": id_case,
        "nom": module.nom,
        "pv": module.pv_combat,
        "pv_max": module.pv_max,
        "detruit": module.est_detruit(),
        "image": module.image,
        "principal": module.principal,
        "hors_service": hors_service,
        # Attaques qui le visent au prochain tour ennemi (cf. _menaces)
        "menaces": (menaces or {}).get(id(module), []),
        **_statuts_json(module),
    }


def _effet_ennemi_json(effet, valeur: int, ennemi: EnnemiNew, cible_prevue=None) -> dict:
    """Un effet d'etape ennemie avec sa valeur au tour en cours. `cible` : "MODULE" (module prevu,
    nom et case), "TOUS" (tous les modules), "SOI" (l'ennemi lui-meme), "ALLIE" (un allie tire au
    moment de jouer) ; None pour un module qui n'est pas encore connu (cycle complet)."""
    if effet.cible == CibleEffetEnnemi.TOUS_MODULES:
        cible = "TOUS"
    elif effet.cible == CibleEffetEnnemi.SOI_MEME:
        cible = "SOI"
    elif effet.cible == CibleEffetEnnemi.ALLIE_AVANT_SINON_ARRIERE:
        cible = "ALLIE"
    else:
        cible = "MODULE"
    resultat = {
        "nature": effet.nature.name,
        "valeur": valeur,
        "repetitions": effet.repetitions,
        "cible": cible,
        "cible_nom": None,
        "cible_id": None,
    }
    if cible == "MODULE" and isinstance(cible_prevue, ModuleNew):
        resultat["cible_nom"] = cible_prevue.nom
        resultat["cible_id"] = _id_case_module(cible_prevue)
    return resultat


def _ennemi_json(ennemi: EnnemiNew | None, id_case: str, intentions: dict, fusionne: bool = False) -> dict | None:
    if ennemi is None:
        return None
    intention = intentions.get(id(ennemi))
    cycle = [
        [_effet_ennemi_json(effet, ennemi.valeur(effet.valeur, combat.tour), ennemi) for effet in etape]
        for etape in ennemi.actions
    ]
    return {
        "id": id_case,
        "nom": ennemi.nom,
        "pv": ennemi.pv,
        "pv_max": ennemi.pv_max,
        "detruit": ennemi.est_detruit(),
        "image": ennemi.image,
        "fusionne": fusionne,
        **_statuts_json(ennemi),
        # Prochaine etape (ce qu'il jouera a son tour), vide si detruit
        "intention": [
            _effet_ennemi_json(effet.effet, effet.valeur, ennemi, effet.cible_prevue) for effet in intention.effets
        ] if intention else [],
        # Cycle complet, valeurs au tour en cours, et etape courante
        "cycle": cycle,
        "etape": ennemi.etape,
    }


def _ennemis_json() -> list:
    """Un objet par case de la grille ennemie (ordre de IDS_ENNEMIS), None si vide. Un ennemi sur
    les deux cases d'une rangee (le Boss) n'est publie qu'une fois, sur sa case Avant
    (fusionne=True)."""
    flotte = combat.flotte
    intentions = {id(intention.ennemi): intention for intention in combat.intentions()}
    # Ennemi de chaque case, detruit compris (ennemi_en ne renvoie que les vivants)
    par_case = {case: ennemi for ennemi in flotte.ennemis for case in flotte.cases_de(ennemi)}
    resultat = {}
    for id_avant, id_arriere in _PAIRES_CASES_ENNEMIES:
        avant = par_case.get(IDS_ENNEMIS[id_avant])
        arriere = par_case.get(IDS_ENNEMIS[id_arriere])
        fusionne = avant is not None and avant is arriere
        resultat[id_avant] = _ennemi_json(avant, id_avant, intentions, fusionne)
        resultat[id_arriere] = None if fusionne else _ennemi_json(arriere, id_arriere, intentions)
    return [resultat[id_case] for id_case in IDS_ENNEMIS]


def _carte_en_main_json(carte: CarteNew, index: int) -> dict:
    module = combat.vaisseau.module_d_exemplaire(carte.exemplaire_module)
    entree = _carte_json(carte, module.nom if module else None)
    entree["index"] = index
    entree["camp"] = "allie" if carte.cible.camp == Camp.JOUEUR else "ennemi"
    entree["jouable"] = combat.peut_jouer(carte)
    # Cases ou confirmer la carte (refonte-combat.md 4.2) : decidees par le gameplay, jamais en JS
    entree["cases"] = _ids_cases(combat.cibles_possibles(carte), carte.cible.camp) if entree["jouable"] else []
    return entree


def _nom_source(source) -> tuple[str | None, str | None]:
    """(nom, genre) d'une source d'evenement : carte, ennemi, module, ou None (incendie)."""
    if isinstance(source, CarteNew):
        return source.nom, "carte"
    if isinstance(source, EnnemiNew):
        return source.nom, "ennemi"
    if isinstance(source, ModuleNew):
        return source.nom, "module"
    return None, None


def _evenement_json(evenement) -> dict:
    """Une entree du journal (des faits, combat_new.Evenement), mise en phrase par app.js."""
    source_nom, source_genre = _nom_source(evenement.source)
    cible_nom, cible_genre = _nom_source(evenement.cible)
    return {
        "nature": evenement.nature.name,
        "tour": evenement.tour,
        "source_nom": source_nom,
        "source_genre": source_genre,
        "cible_nom": cible_nom,
        "cible_genre": cible_genre,
        "valeur": evenement.valeur,
        "statut": evenement.statut.name if evenement.statut else None,
        "annules_leurre": evenement.annules_leurre,
        "renvoyes": evenement.renvoyes,
        "absorbes_bouclier": evenement.absorbes_bouclier,
        "pv_perdus": evenement.pv_perdus,
        "pv_restants": evenement.pv_restants,
    }


def _etat_dict() -> dict:
    """Etat courant du combat, pour le rendu JS."""
    vaisseau = combat.vaisseau
    deck = combat.deck
    par_id = {_id_case_module(module): module for module in vaisseau.modules}
    menaces = _menaces(combat.intentions()) if combat.en_cours else {}
    return {
        "etat": combat.etat.name,
        "tour": combat.tour,
        "electricite": combat.electricite,
        "electricite_max": ELECTRICITE_PAR_TOUR,
        "vaisseau": {
            "base": _module_json(vaisseau.principal, "base", menaces),
            "modules": [_module_json(par_id.get(id_case), id_case, menaces) for id_case in IDS_MODULES],
        },
        "ennemis": _ennemis_json(),
        "main": [_carte_en_main_json(carte, index) for index, carte in enumerate(deck.main)],
        "pioche": len(deck.pioche),
        "defausse": len(deck.defausse),
        "epuisees": len(deck.epuisees),
        "hors_service": len(deck.hors_service),
        "journal": [_evenement_json(evenement) for evenement in combat.journal],
    }


# --- Combat : popups (presentation des entrees du journal ajoutees par la derniere action) ---

_SYMBOLES_STATUT = {"BOUCLIER": "🛡", "INCENDIE": "🔥", "RENVOI": "↩"}


def _popup_evenement(evenement) -> dict | None:
    nature = evenement.nature
    if nature not in (
        NatureEvenement.ATTAQUE, NatureEvenement.RENVOI, NatureEvenement.INCENDIE,
        NatureEvenement.STATUT_POSE, NatureEvenement.REPARATION,
    ) or evenement.cible is None:
        return None
    id_case, camp = _id_case_entite(evenement.cible)
    if id_case is None:
        return None
    if nature == NatureEvenement.STATUT_POSE:
        if evenement.statut == Statut.LEURRE:
            texte = "Leurre"
        else:
            texte = f"+{evenement.valeur} {_SYMBOLES_STATUT[evenement.statut.name]}"
        couleur = {"BOUCLIER": "bouclier", "INCENDIE": "degats", "RENVOI": "debuff"}.get(evenement.statut.name, "buff")
    elif nature == NatureEvenement.REPARATION:
        texte, couleur = f"+{evenement.valeur}", "soin"
    elif evenement.annules_leurre and not evenement.pv_perdus and not evenement.absorbes_bouclier:
        texte, couleur = "annulé", "bouclier"
    elif evenement.renvoyes and not evenement.pv_perdus and not evenement.absorbes_bouclier:
        texte, couleur = f"↩ {evenement.renvoyes}", "debuff"
    else:
        texte = f"-{evenement.pv_perdus}"
        if evenement.absorbes_bouclier:
            texte += f" (🛡{evenement.absorbes_bouclier})"
        couleur = "degats"
    return {"id": id_case, "camp": camp, "texte": texte, "couleur": couleur}


def _resultat_combat() -> str:
    """Etat du combat et popups des entrees du journal ajoutees depuis le dernier envoi."""
    global taille_journal_transmise
    nouvelles = combat.journal[taille_journal_transmise:]
    taille_journal_transmise = len(combat.journal)
    popups = [popup for evenement in nouvelles if (popup := _popup_evenement(evenement))]
    return json.dumps({"etat": _etat_dict(), "popups": popups})


def _demarrer_combat(nouveau) -> str:
    global combat, taille_journal_transmise
    combat = nouveau
    taille_journal_transmise = len(combat.journal)
    return json.dumps({"etat": _etat_dict(), "popups": []})


def jouer_carte(index_carte: int, id_case: str) -> str:
    """Joue la carte en main a cet index sur la case touchee (refonte-combat.md 4)."""
    carte = combat.deck.main[index_carte]
    camp = "allie" if carte.cible.camp == Camp.JOUEUR else "ennemi"
    combat.jouer_carte(carte, _position_case(id_case, camp))
    return _resultat_combat()


def finir_tour() -> str:
    """Termine le tour du joueur : fin de tour, tour ennemi, debut du tour suivant."""
    combat.finir_tour()
    return _resultat_combat()


def etat_deck_combat() -> str:
    """Toutes les cartes du combat en cours, toutes piles confondues (ecran "deck en entier")."""
    noms = {module.exemplaire: module.nom for module in combat.vaisseau.modules}
    return json.dumps(_cartes_regroupees_json(combat.deck.toutes_les_cartes(), noms))


# --- Profils et parties (specs.md 10.3) : la persistance (localStorage) est geree cote JS ;
# ces fonctions ne font que (de)serialiser et appliquer les fonctions de src/gameplay ---


def _transition_json(partie, ecran) -> str:
    """Partie mise a jour et ecran suivant, decide par src/gameplay/deroulement.py."""
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "ecran": ecran.name})


def _partie_json(partie) -> dict:
    return json.loads(partie_vers_json(partie))


def creer_profil_web(nom) -> str:
    return profil_vers_json(nouveau_profil(nom))


def lire_partie_web(partie_json) -> str:
    """Partie sauvegardee relue : {"partie": ..., "effacer": bool}. partie vaut None pour une
    ancienne version du jeu, effacer dit si web/app.js doit la retirer de localStorage (EN_COURS,
    decision 1, meme regle que partie_en_cours cote PC) ; le profil est garde."""
    partie = lire_partie(partie_json)
    return json.dumps({
        "partie": None if partie is None else _partie_json(partie),
        "effacer": ancienne_partie_a_effacer(partie_json),
    })


def nouvelle_partie_web() -> str:
    partie = nouvelle_partie()
    return _transition_json(partie, deroulement.ecran_de_reprise(partie))


def infos_vaisseau_web(partie_json) -> str:
    """Modules de la partie par emplacement (accueil, Station, Aventures, survol Vaisseau)."""
    partie = partie_depuis_json(partie_json)
    resultat = {}
    for position, module in partie.vaisseau.items():
        if module is None:
            resultat[position] = None
            continue
        resultat[position] = {
            "module_id": module.id,
            "exemplaire": module.exemplaire,
            "principal": module.principal,
            "pv": module.pv if module.principal else module.pv_max,
            "pv_max": module.pv_max,
            "niveau_maj": module.niveau_maj,
            "nom": module.nom,
            "image": IMAGE_CASE_PRINCIPAL if module.principal else module.image,
            "description": module.description,
        }
    return json.dumps(resultat)


def deck_partie_web(partie_json) -> str:
    """Deck possede d'une partie, regroupe (carte, module) avec quantite."""
    partie = partie_depuis_json(partie_json)
    return json.dumps(_cartes_regroupees_json(deck_de_la_partie(partie), _noms_modules_partie(partie)))


def abandonner_partie_web(partie_json) -> str:
    return partie_vers_json(marquer_terminee(partie_depuis_json(partie_json)))


def choix_module_partie_web(partie_json) -> str:
    """Modules proposes au Niveau 1 (deroulement.candidats_choix_module)."""
    candidats = deroulement.candidats_choix_module(partie_depuis_json(partie_json))
    return json.dumps([
        {"id": candidat.id, "nom": candidat.nom, "image": candidat.image, "description": candidat.description}
        for candidat in candidats
    ])


def choisir_module_partie_web(partie_json, module_id) -> str:
    """Equipe le module choisi et tire les cartes proposees pour lui, deja rattachees au nouvel
    exemplaire. `candidats` vide : web/app.js appelle directement resoudre_carte_module_web avec
    None, sans afficher l'ecran (comme le PC)."""
    partie = partie_depuis_json(partie_json)
    modele = charger_modules_new()[module_id]
    candidats = deroulement.choisir_module(partie, modele, random.Random())
    return json.dumps({
        "partie": _partie_json(partie),
        "module_nom": modele.nom,
        "candidats": [_carte_json(carte, modele.nom) for carte in candidats],
    })


def resoudre_carte_module_web(partie_json, id_carte, exemplaire_module) -> str:
    """Ajoute la carte choisie (id_carte None = Passer) et avance de niveau."""
    partie = partie_depuis_json(partie_json)
    carte = _carte_proposee(id_carte, exemplaire_module) if id_carte is not None else None
    return _transition_json(partie, deroulement.resoudre_carte_module(partie, carte))


def continuer_partie_web(partie_json) -> str:
    """Demarre le combat du niveau courant (deroulement : etape Prime ou Boss)."""
    return _demarrer_combat(combat_depuis_partie(partie_depuis_json(partie_json)))


def choix_niveau_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    return json.dumps({"niveau": partie.niveau, "propositions": [t.name for t in deroulement.propositions_niveau(partie)]})


def ecran_pour_etape_web(type_etape) -> str:
    return json.dumps(deroulement.ecran_pour_etape(TypeEtape[type_etape], random.Random()).name)


def ecran_reprise_web(partie_json) -> str:
    return json.dumps(deroulement.ecran_de_reprise(partie_depuis_json(partie_json)).name)


def conclure_combat_partie_web(partie_json) -> str:
    """A appeler une seule fois a la fin du combat en cours : PV du principal reportes, Argent et
    candidats de recompense en cas de victoire (deroulement.conclure_combat)."""
    partie = partie_depuis_json(partie_json)
    candidats = deroulement.conclure_combat(partie, combat, random.Random())
    return json.dumps({
        "partie": _partie_json(partie),
        "candidats": [_carte_json(carte, module.nom) for module, carte in candidats if carte is not None],
    })


def resoudre_fin_combat_web(partie_json, victoire, id_carte, exemplaire_module) -> str:
    partie = partie_depuis_json(partie_json)
    carte = _carte_proposee(id_carte, exemplaire_module) if id_carte is not None else None
    return _transition_json(partie, deroulement.resoudre_fin_combat(partie, bool(victoire), carte))


def terminer_victoire_finale_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    return _transition_json(partie, deroulement.terminer_victoire_finale(partie))


def terminer_etape_web(partie_json) -> str:
    """Fin d'une etape hors combat (Station service, Aventures, Planete commerciale)."""
    partie = partie_depuis_json(partie_json)
    return _transition_json(partie, deroulement.terminer_etape(partie))


# --- Station service (specs.md 2.2) : chaque action renvoie {"partie", "succes"} ; succes=False
# (Argent insuffisant) laisse la partie inchangee ---


def constantes_station_service_web() -> str:
    """Valeurs affichees par l'ecran avant toute action (seule source : partie.py)."""
    return json.dumps({"cout": COUT_ACTION_STATION_SERVICE, "pv_reparation": PV_REPARATION, "pv_amelioration": PV_AMELIORATION})


def _resultat_station(partie, succes: bool) -> str:
    return json.dumps({"partie": _partie_json(partie), "succes": succes})


def reparer_principal_web(partie_json) -> str:
    """Reparer : toujours le principal (decision 2, refonte-branchement.md)."""
    partie = partie_depuis_json(partie_json)
    return _resultat_station(partie, reparer_principal(partie))


def ameliorer_module_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    return _resultat_station(partie, ameliorer_module(partie, position))


def mettre_a_jour_module_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    return _resultat_station(partie, mettre_a_jour_module(partie, position))


def deplacer_module_web(partie_json, position_source, position_destination) -> str:
    partie = partie_depuis_json(partie_json)
    return _resultat_station(partie, deplacer_module(partie, position_source, position_destination))


# --- Aventure "Trois lunes" (specs.md 2.5) ---


def constantes_aventure_trois_lunes_web() -> str:
    return json.dumps({"pv_reparation_vaisseau": PV_REPARATION_VAISSEAU, "pv_amelioration": PV_AMELIORATION})


def reparer_vaisseau_aventure_web(partie_json) -> str:
    """Reparer le vaisseau : soigne le principal (decision 3)."""
    partie = partie_depuis_json(partie_json)
    reparer_vaisseau(partie)
    return partie_vers_json(partie)


def ameliorer_module_aventure_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    ameliorer_module_aventure(partie, position)
    return partie_vers_json(partie)


def retirer_carte_aventure_web(partie_json, id_carte, exemplaire_module) -> str:
    """Bricoler : retire un exemplaire de cette carte de ce module."""
    partie = partie_depuis_json(partie_json)
    retirer_carte(partie, CartePossedee(id_carte, exemplaire_module))
    return partie_vers_json(partie)


# --- Aventure "Asteroides" (specs.md 2.5) : "Traverser" (deux chocs sur le principal, puis une
# carte offerte ou non) ou "Affronter les pirates" (combat a 3 ennemis) ---


def constantes_aventure_asteroides_web() -> str:
    return json.dumps({"degats_asteroides": DEGATS_ASTEROIDES})


def premier_choc_asteroides_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    subir_degats_principal(partie, DEGATS_ASTEROIDES)
    return partie_vers_json(partie)


def second_choc_asteroides_web(partie_json) -> str:
    """2e choc et carte offerte (ou non), decides en une fois par second_choc_asteroides."""
    partie = partie_depuis_json(partie_json)
    carte = second_choc_asteroides(partie, _modeles_cartes(), random.Random())
    return json.dumps({
        "partie": _partie_json(partie),
        "carte": _carte_json(carte, partie.principal.nom) if carte is not None else None,
    })


def prendre_carte_offerte_asteroides_web(partie_json, id_carte, exemplaire_module) -> str:
    partie = partie_depuis_json(partie_json)
    ajouter_carte(partie, id_carte, exemplaire_module)
    return partie_vers_json(partie)


def combat_aventure_asteroides_web(partie_json) -> str:
    return _demarrer_combat(combat_aventure_asteroides(partie_depuis_json(partie_json)))


# --- Aventure "Police" (specs.md 2.5) : l'etat de resolution est possede par le gameplay
# (EtatAventurePolice), jamais reconstruit cote JS ---


def constantes_aventure_police_web() -> str:
    return json.dumps({"cout_mettre_aux_normes": COUT_METTRE_AUX_NORMES})


def _etat_aventure_police_json(partie) -> dict:
    possedee = etat_aventure_police.carte_actuelle
    carte = _modeles_cartes()[possedee.id].copie(exemplaire_module=possedee.module)
    return {
        "carte": _carte_json(carte, _noms_modules_partie(partie).get(possedee.module)),
        "detourner_disponible": etat_aventure_police.detourner_disponible,
    }


def demarrer_aventure_police_web(partie_json) -> str:
    global etat_aventure_police
    partie = partie_depuis_json(partie_json)
    etat_aventure_police = demarrer_aventure_police(partie, random.Random())
    return json.dumps(_etat_aventure_police_json(partie))


def detourner_police_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    succes = detourner_aventure_police(etat_aventure_police, partie, random.Random())
    resultat = _etat_aventure_police_json(partie)
    resultat["succes"] = succes
    return json.dumps(resultat)


def confiscation_police_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    retirer_carte(partie, etat_aventure_police.carte_actuelle)
    return partie_vers_json(partie)


def mettre_aux_normes_police_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    succes = payer_mise_aux_normes(partie)
    return json.dumps({"partie": _partie_json(partie), "succes": succes})
