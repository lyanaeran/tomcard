"""
Pont entre le JS de la page web et le moteur de combat Python reel (src/gameplay/),
execute tel quel dans le navigateur via Pyodide. Aucune modification du gameplay :
ce fichier ne fait que traduire son etat en JSON et router les actions du joueur.

POC experimental (branche web-ui-poc) : layout simplifie, pas de survol tactile (une
infobulle s'affiche au tap a la place). Les popups +/-N et l'intention des ennemis
sont repris a partir de ce que combat.py calcule deja, sans dupliquer la logique de
ciblage/degats.
"""

import json
import random
import sys

sys.path.insert(0, "/repo")

from src.gameplay.carte import CIBLES_SANS_CLIC, ActionCarte, CibleCarte, regrouper_cartes
from src.gameplay import deroulement
from src.gameplay.config_poc import creer_combat_poc, creer_deck, creer_vaisseau
from src.gameplay.donnees import charger_cartes, charger_modules, image_case_module
from src.gameplay.ennemi import CibleActionEnnemi, TypeActionEnnemi
from src.gameplay.journal import EvenementCarteJouee, EvenementTour
from src.gameplay.module import Module
from src.gameplay.parcours import (
    TypeEtape,
    modules_equipables,
    tirer_candidats_module,
    tirer_candidats_recompense,
)
from src.gameplay.partie import (
    COUT_ACTION_STATION_SERVICE,
    COUT_METTRE_AUX_NORMES,
    DEGATS_ASTEROIDES,
    PV_AMELIORATION,
    PV_REPARATION_VAISSEAU,
    ajouter_carte,
    ameliorer_module,
    ameliorer_module_aventure,
    combat_aventure_asteroides,
    combat_depuis_partie,
    deck_de_la_partie,
    demarrer_aventure_police,
    deplacer_module,
    detourner_aventure_police,
    marquer_terminee,
    mettre_a_jour_module,
    nouveau_profil,
    nouvelle_partie,
    partie_depuis_json,
    partie_vers_json,
    payer_mise_aux_normes,
    profil_vers_json,
    reparer_module,
    reparer_vaisseau,
    retirer_carte,
    second_choc_asteroides,
    subir_degats_module,
)
from src.gameplay.position import Colonne, Position, Rangee

RACINE_FS = "/repo/"

IDS_MODULES = {
    "AV_G": Position(Colonne.AVANT, Rangee.GAUCHE),
    "AV_D": Position(Colonne.AVANT, Rangee.DROITE),
    "AR_G": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "AR_D": Position(Colonne.ARRIERE, Rangee.DROITE),
}
IDS_ENNEMIS = {
    "AV_G": Position(Colonne.AVANT, Rangee.GAUCHE),
    "AV_M": Position(Colonne.AVANT, Rangee.MID),
    "AV_D": Position(Colonne.AVANT, Rangee.DROITE),
    "AR_G": Position(Colonne.ARRIERE, Rangee.GAUCHE),
    "AR_M": Position(Colonne.ARRIERE, Rangee.MID),
    "AR_D": Position(Colonne.ARRIERE, Rangee.DROITE),
}

combat = None
# Etat de resolution de l'Aventure "Police" en cours (specs.md 2.5, src/gameplay/partie.py:
# EtatAventurePolice) - meme principe que `combat` ci-dessus : possede par le gameplay, pas
# reconstruit cote JS (cf. CLAUDE.md, gameplay commun aux deux interfaces).
etat_aventure_police = None


def _transition_json(partie, ecran) -> str:
    """Resultat d'une transition du parcours : partie mise a jour et ecran suivant, decide par
    src/gameplay/deroulement.py (web/app.js ne fait que l'afficher, cf. allerA)."""
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "ecran": ecran.name})


def _chemin_web(chemin_fs: str) -> str:
    """Convertit un chemin absolu de la FS Pyodide (/repo/...) en URL relative de la page."""
    return chemin_fs[len(RACINE_FS):] if chemin_fs and chemin_fs.startswith(RACINE_FS) else chemin_fs


def _buffs_json(module):
    """Buffs actifs de ce module (specs.md 12.3/12.5), chacun independant des autres
    (aucune fusion). tours_restants est None pour un buff persistant (dure tout le
    combat, cf. Module.declencher_buffs_tour)."""
    return [
        {"action": buff.action.name, "valeur": buff.valeur, "tours_restants": buff.tours_restants}
        for buff in module.buffs_actifs
    ]


def _module_json(module, id_case: str):
    if module is None:
        return None
    return {
        "id": id_case,
        "nom": module.nom,
        "pv": module.pv,
        "pv_max": module.pv_max,
        "bouclier": module.bouclier,
        "detruit": module.est_detruit(),
        "image": _chemin_web(module.image),
        "buffs": _buffs_json(module),
        "leurre_actif": module.leurre_actif,
    }


def _intention_action_json(ennemi, action):
    """Intention correspondant a une seule Action active de cet ennemi (cf. _intentions_json
    ci-dessous pour la liste complete), calculee avec les memes fonctions que fenetre.py
    (previsualiser_cible/degats_attaque_effectifs, aucune logique dupliquee) - None si son
    Attaque de proximite n'a plus de cible (combat deja termine sur ce point).

    type: "ATTAQUE" ou "POSE_BUFF" (cf. TypeActionEnnemi). Pour une ATTAQUE :
    cible_type "TOUS" (attaque de zone, Le puzzle), "REDIRECTION" (Tir allie actif, specs.md
    12.6 - la cible reelle, un autre ennemi, n'est tiree au hasard qu'a la resolution du
    tour, jamais ici, pour rester deterministe au tap/redessin) ou "MODULE" (cible normale,
    avec module_id/module_nom). Le "degats" est volontairement la valeur "brute" de
    l'ennemi, pas _degats_effectifs de combat.py (qui plafonne selon PV+bouclier de la
    cible et renvoie 0 si un leurre est actif, specs.md 12.6) : l'intention doit montrer la
    vraie attaque de chaque ennemi. Pour une POSE_BUFF, "action_buff" (cf. carte.py:ActionCarte,
    pour app.js:LIBELLES_ACTION_ACTIF) et "soi_meme" (True = SOI_MEME, False = un module tire
    au hasard a la resolution) decrivent l'effet et sa cible. "repetitions" (les deux types)
    indique que l'action se declenche plusieurs fois dans le meme tour (ex. Le nettoyeur,
    valeur/effet infliges/poses ce nombre de fois, pas une seule)."""
    if action.type != TypeActionEnnemi.ATTAQUE:
        return {
            "type": "POSE_BUFF",
            "valeur": action.valeur,
            "action_buff": action.action_buff.name if action.action_buff else None,
            "soi_meme": action.cible == CibleActionEnnemi.SOI_MEME,
            "repetitions": action.repetitions,
        }
    degats = ennemi.degats_attaque_effectifs(action.valeur)
    if action.cible == CibleActionEnnemi.TOUS_MODULES_JOUEUR:
        return {"type": "ATTAQUE", "cible_type": "TOUS", "degats": degats, "repetitions": action.repetitions}
    if any(buff.action == ActionCarte.REDIRECTION_CIBLE for buff in ennemi.buffs_actifs):
        return {"type": "ATTAQUE", "cible_type": "REDIRECTION", "repetitions": action.repetitions}
    cible = combat.previsualiser_cible(ennemi)
    if cible is None:
        return None
    return {
        "type": "ATTAQUE",
        "cible_type": "MODULE",
        "module_id": _id_module(cible),
        "module_nom": cible.nom,
        "degats": degats,
        "repetitions": action.repetitions,
    }


def _intentions_json(ennemi):
    """Intentions de cet ennemi a son prochain tour (specs.md 13, ActionEnnemi) : une entree
    par Action active ce tour-la (cf. Combat.prochaines_actions_actives - plusieurs peuvent
    l'etre le meme tour, ex. le Boss des pirates qui attaque ET pose un buff), liste vide si
    aucune (ex. Petit Jean, dont le bouclier n'est pose qu'un tour sur 3)."""
    if ennemi.est_detruit():
        return []
    actions = combat.prochaines_actions_actives(ennemi)
    return [intention for action in actions if (intention := _intention_action_json(ennemi, action)) is not None]


def _debuffs_json(ennemi):
    """Buffs/debuffs actifs de cet ennemi (specs.md 12.1/12.4/13), chacun independant des
    autres (aucune fusion : la magnitude affichee est celle de cette instance, pas la somme).
    "cible_reflet_nom" (uniquement pour BOUCLIER_MIROIR, ennemi Miroir) : nom du module du
    joueur qui recevra les degats renvoyes - le joueur doit pouvoir l'anticiper avant
    d'attaquer cet ennemi, cf. app.js:libelleEffetActif."""
    return [
        {
            "action": buff.action.name,
            "valeur": buff.valeur,
            "tours_restants": buff.tours_restants,
            "cible_reflet_nom": buff.cible_reflet.nom if buff.cible_reflet is not None else None,
        }
        for buff in ennemi.buffs_actifs
    ]


def _ennemi_json(ennemi, id_case: str, fusionne: bool = False):
    if ennemi is None:
        return None
    return {
        "id": id_case,
        "nom": ennemi.nom,
        "pv": ennemi.pv,
        "pv_max": ennemi.pv_max,
        "bouclier": ennemi.bouclier,
        "detruit": ennemi.est_detruit(),
        "image": _chemin_web(ennemi.image),
        "intentions": _intentions_json(ennemi),
        "debuffs": _debuffs_json(ennemi),
        # Occupe aussi la case Arriere de cette rangee (specs.md 3.2, ex. le Boss des pirates) :
        # app.js n'affiche alors qu'une seule case, sur les 2 colonnes (cf. _ennemis_json).
        "fusionne": fusionne,
    }


_PAIRES_CASES_ENNEMIES = (("AV_G", "AR_G"), ("AV_M", "AR_M"), ("AV_D", "AR_D"))


def _ennemis_json(flotte) -> list:
    """Un objet JSON par case de la grille ennemie (ordre de IDS_ENNEMIS), None si vide. Un
    ennemi occupant 2 emplacements Avant+Arriere de la meme rangee (specs.md 3.2, ex. le Boss
    des pirates) n'est publie qu'une fois, sur sa case Avant (fusionne=True) : sa case Arriere
    reste a None, web/app.js n'affichant alors qu'une seule case fusionnee sur les 2 colonnes."""
    positions = flotte.positions()
    resultat = {}
    for id_avant, id_arriere in _PAIRES_CASES_ENNEMIES:
        ennemi_avant = positions.get(IDS_ENNEMIS[id_avant])
        ennemi_arriere = positions.get(IDS_ENNEMIS[id_arriere])
        fusionne = ennemi_avant is not None and ennemi_avant is ennemi_arriere
        resultat[id_avant] = _ennemi_json(ennemi_avant, id_avant, fusionne)
        resultat[id_arriere] = None if fusionne else _ennemi_json(ennemi_arriere, id_arriere)
    return [resultat[id_case] for id_case in IDS_ENNEMIS]


def _carte_json(carte, index: int):
    return {
        "index": index,
        "nom": carte.nom,
        "cout": carte.cout,
        "valeur": carte.valeur,
        "type": carte.type.name,
        "cible": carte.cible.name,
        "sans_clic": carte.cible in CIBLES_SANS_CLIC,
        "image": _chemin_web(carte.image),
        "rarete": carte.rarete.name,
        "munitions_restantes": carte.munitions_restantes,
        "action": carte.action.name if carte.action else None,
        "duree": carte.duree,
    }


def _etat_dict() -> dict:
    """Construit l'etat courant du combat (dict), pour le rendu JS."""
    vaisseau = combat.joueur.vaisseau
    flotte = combat.flotte
    modules_equipes = vaisseau.modules_equipes()

    vaisseau_json = {
        "base": _module_json(vaisseau.base, "base"),
        "modules": [_module_json(modules_equipes.get(pos), id_case) for id_case, pos in IDS_MODULES.items()],
    }
    ennemis_json = _ennemis_json(flotte)
    main_json = [_carte_json(carte, i) for i, carte in enumerate(combat.joueur.deck.main)]

    return {
        "etat": combat.etat.name,
        "electricite": combat.joueur.electricite,
        "electricite_max": combat.joueur.electricite_par_tour,
        "vaisseau": vaisseau_json,
        "ennemis": ennemis_json,
        "main": main_json,
        "pioche": len(combat.joueur.deck.pioche),
        "defausse": len(combat.joueur.deck.defausse),
        "journal": [_evenement_json(evenement) for evenement in combat.journal],
    }


def _evenement_json(evenement) -> dict:
    """Serialise un evenement de Combat.journal (specs.md 8.1) en JSON - simple traduction
    mecanique des champs deja decides par src/gameplay/journal.py/combat.py (quel evenement,
    quand l'enregistrer) : app.js n'a plus qu'a le mettre en forme (phrase/couleurs), jamais a
    decider quoi journaliser."""
    if isinstance(evenement, EvenementTour):
        return {"type": "tour", "numero": evenement.numero}
    if isinstance(evenement, EvenementCarteJouee):
        cible = evenement.cible
        if cible is None:
            return {
                "type": "carte",
                "carte_nom": evenement.carte.nom,
                "cible_camp": None,
                "cible_nom": None,
                "carte_cible": evenement.carte.cible.name,
            }
        camp = "allie" if isinstance(cible, Module) else "ennemi"
        return {"type": "carte", "carte_nom": evenement.carte.nom, "cible_camp": camp, "cible_nom": cible.nom, "carte_cible": None}
    camp = "allie" if isinstance(evenement.cible, Module) else "ennemi"
    return {
        "type": "action_ennemi",
        "ennemi_nom": evenement.ennemi.nom,
        "cible_camp": camp,
        "cible_nom": evenement.cible.nom,
        "cible_est_soi": evenement.cible is evenement.ennemi,
        "valeur": evenement.valeur,
        "type_evenement": evenement.type_evenement,
    }


def _id_module(module) -> str | None:
    """Retrouve l'id de case ('base' ou une des 4 cases equipees) occupe par ce module."""
    vaisseau = combat.joueur.vaisseau
    if module is vaisseau.base:
        return "base"
    modules_equipes = vaisseau.modules_equipes()
    for id_case, position in IDS_MODULES.items():
        if modules_equipes.get(position) is module:
            return id_case
    return None


def _id_ennemi(ennemi) -> str | None:
    """Retrouve l'id de case occupe par cet ennemi dans la flotte."""
    positions = combat.flotte.positions()
    for id_case, position in IDS_ENNEMIS.items():
        if positions.get(position) is ennemi:
            return id_case
    return None


def _popup(cible, type_carte: str, valeur: int, action: str | None) -> dict | None:
    """Construit le popup +/-N pour une cible touchee."""
    if isinstance(cible, Module):
        id_case, camp = _id_module(cible), "allie"
    else:
        id_case, camp = _id_ennemi(cible), "ennemi"
    if id_case is None:
        return None
    if type_carte == "ATTAQUE":
        texte, couleur = f"-{valeur}", "degats"
    elif type_carte == "DEFENSE":
        if action == "ANNULATION_PROCHAINE_ATTAQUE":
            texte, couleur = "Leurre actif !", "bouclier"
        else:
            texte, couleur = f"+{valeur}", "bouclier"
    elif type_carte == "DEBUFF":
        if action == "VULNERABILITE":
            texte, couleur = f"+{valeur}%", "debuff"
        elif action == "REDIRECTION_CIBLE":
            texte, couleur = "Detourne !", "debuff"
        else:
            texte, couleur = f"-{valeur}", "debuff"
    elif type_carte == "BUFF":
        texte, couleur = f"+{valeur}", "buff"
    else:
        texte, couleur = f"+{valeur}", "soin"
    return {"id": id_case, "camp": camp, "texte": texte, "couleur": couleur}


def nouveau_combat(graine) -> str:
    """Demarre un nouveau combat aleatoire (graine optionnelle pour reproduire un combat)."""
    global combat
    aleatoire = random.Random(int(graine)) if graine is not None else random.Random()
    combat = creer_combat_poc(generateur_aleatoire=aleatoire)
    return json.dumps({"etat": _etat_dict(), "popups": []})


def nouveau_choix_module(graine) -> str:
    """Tire 3 modules candidats differents (specs.md 2.3, Niveau 1), graine optionnelle."""
    aleatoire = random.Random(int(graine)) if graine is not None else random.Random()
    pool = modules_equipables(charger_modules())
    candidats = tirer_candidats_module(pool, aleatoire)
    return json.dumps(
        [
            {"id": candidat.id, "nom": candidat.nom, "image": _chemin_web(candidat.image), "description": candidat.description}
            for candidat in candidats
        ]
    )


def _candidat_recompense_json(spec, carte) -> dict:
    return {
        "module_nom": spec.nom,
        "carte_nom": carte.nom,
        "carte_id": carte.id,
        "image": _chemin_web(carte.image),
        "cout": carte.cout,
        "rarete": carte.rarete.name,
        "valeur": carte.valeur,
        "type": carte.type.name,
        "cible": carte.cible.name,
        "action": carte.action.name if carte.action else None,
        "duree": carte.duree,
    }


def fin_combat_victoire(graine) -> str:
    """Ecran de victoire (specs.md 2.1/6) : un candidat de recompense par module d'un vaisseau
    tire au sort - demo, pas encore reliee a un vrai combat termine (cf. specs.md 2.3), meme
    situation que nouveau_choix_module."""
    aleatoire = random.Random(int(graine)) if graine is not None else random.Random()
    _vaisseau, specs_utilisees = creer_vaisseau(charger_modules(), aleatoire)
    cartes = charger_cartes()
    candidats = tirer_candidats_recompense(specs_utilisees, cartes, aleatoire)
    return json.dumps(
        [_candidat_recompense_json(spec, carte) for spec, carte in candidats if carte is not None]
    )


def _carte_regroupee_json(carte, quantite: int) -> dict:
    return {
        "id_carte": carte.id,
        "nom": carte.nom,
        "image": _chemin_web(carte.image),
        "cout": carte.cout,
        "rarete": carte.rarete.name,
        "valeur": carte.valeur,
        "type": carte.type.name,
        "cible": carte.cible.name,
        "action": carte.action.name if carte.action else None,
        "duree": carte.duree,
        "quantite": quantite,
    }


def etat_deck(graine) -> str:
    """Ecran "deck en entier" (appelable depuis plusieurs endroits, cf. specs.md 6) : cartes du
    combat en cours si un combat est actif (combat.joueur.deck), sinon un deck de demonstration
    tire au sort (graine optionnelle) - meme situation que nouveau_choix_module/
    fin_combat_victoire pour l'instant : pas encore reliee a un vrai bouton dans l'UI."""
    if combat is not None:
        cartes = combat.joueur.deck.toutes_cartes()
    else:
        aleatoire = random.Random(int(graine)) if graine is not None else random.Random()
        _vaisseau, specs_utilisees = creer_vaisseau(charger_modules(), aleatoire)
        cartes = creer_deck(specs_utilisees, charger_cartes(), aleatoire).toutes_cartes()
    return json.dumps([_carte_regroupee_json(carte, quantite) for carte, quantite in regrouper_cartes(cartes)])


# --- Profils et parties (specs.md 10.3) : la persistance elle-meme (lister/lire/ecrire) est geree
# cote JS via localStorage (web/app.js), Pyodide n'ayant pas acces a une FS persistante entre
# recharges de page. Ces fonctions ne font que (de)serialiser et appliquer la logique de jeu pure
# de src/gameplay/partie.py - jamais de lecture/ecriture disque ici.


def creer_profil_web(nom) -> str:
    return profil_vers_json(nouveau_profil(nom))


def nouvelle_partie_web() -> str:
    """Cree une partie et renvoie {"partie", "ecran"} : ecran de depart decide par
    src/gameplay/deroulement.py (choix de module du Niveau 1)."""
    partie = nouvelle_partie()
    return _transition_json(partie, deroulement.ecran_de_reprise(partie))


def infos_vaisseau_web(partie_json) -> str:
    """Vaisseau d'une partie (JSON), enrichi de l'image/nom de chaque module - pour l'ecran
    d'accueil joueur (src/ui/ecran_accueil_joueur.py cote PC, meme donnees ici pour le web)."""
    partie = partie_depuis_json(partie_json)
    specs_par_id = {spec.id: spec for spec in charger_modules()}
    resultat = {}
    for position, etat in partie.vaisseau.items():
        if etat is None:
            resultat[position] = None
        else:
            spec = specs_par_id[etat.module_id]
            resultat[position] = {
                "module_id": etat.module_id,
                "pv": etat.pv,
                "pv_max": etat.pv_max,
                "niveau_maj": etat.niveau_maj,
                "nom": spec.nom,
                "image": _chemin_web(image_case_module(spec)),
                "description": spec.description,
            }
    return json.dumps(resultat)


def deck_partie_web(partie_json) -> str:
    """Deck reel d'une partie sauvegardee (par opposition a etat_deck, qui affiche le combat en
    cours ou une demonstration) - pour le bouton "Voir le deck" de l'ecran d'accueil joueur."""
    partie = partie_depuis_json(partie_json)
    cartes = deck_de_la_partie(partie, charger_cartes())
    return json.dumps([_carte_regroupee_json(carte, quantite) for carte, quantite in regrouper_cartes(cartes)])


def abandonner_partie_web(partie_json) -> str:
    """Marque une partie TERMINEE (decision utilisateur : comme une defaite, cf.
    src/gameplay/partie.py:marquer_terminee) - web/app.js re-sauvegarde le resultat dans
    localStorage."""
    return partie_vers_json(marquer_terminee(partie_depuis_json(partie_json)))


def choix_module_partie_web(partie_json) -> str:
    """Candidats de choix de module (Niveau 1, specs.md 2.3), tires a partir de la graine de la
    partie (deroulement.candidats_choix_module)."""
    candidats = deroulement.candidats_choix_module(partie_depuis_json(partie_json))
    return json.dumps(
        [
            {"id": candidat.id, "nom": candidat.nom, "image": _chemin_web(candidat.image), "description": candidat.description}
            for candidat in candidats
        ]
    )


def choisir_module_partie_web(partie_json, module_id) -> str:
    """Equipe le module choisi et tire les cartes proposees pour lui (deroulement.choisir_module).
    Renvoie {"partie", "module_nom", "candidats"} ; `candidats` vide : web/app.js appelle
    directement resoudre_carte_module_web(None), sans afficher l'ecran (comme le PC)."""
    partie = partie_depuis_json(partie_json)
    spec = {spec.id: spec for spec in charger_modules()}[module_id]
    candidats = deroulement.choisir_module(partie, spec, random.Random())
    return json.dumps({
        "partie": json.loads(partie_vers_json(partie)),
        "module_nom": spec.nom,
        "candidats": [_carte_avec_id_json(carte) for carte in candidats],
    })


def resoudre_carte_module_web(partie_json, id_carte) -> str:
    """Ajoute la carte choisie (None = Passer) et avance de niveau. Renvoie {"partie", "ecran"}."""
    partie = partie_depuis_json(partie_json)
    return _transition_json(partie, deroulement.resoudre_carte_module(partie, id_carte))


def continuer_partie_web(partie_json) -> str:
    """Demarre un combat a partir du vaisseau/deck reels de la partie (bouton "Continuer" de
    l'ecran d'accueil joueur, ou choix d'une etape Prime/Boss depuis le choix du prochain niveau) :
    la flotte ennemie reste tiree au hasard - approximation temporaire (decision utilisateur) en
    attendant que le parcours applique les regles de difficulte par niveau (specs.md 2.3/3.2),
    meme situation que main.py:_ouvrir_combat cote PC."""
    global combat
    partie = partie_depuis_json(partie_json)
    combat = combat_depuis_partie(partie)
    return json.dumps({"etat": _etat_dict(), "popups": []})


def choix_niveau_web(partie_json) -> str:
    """Ecran "Choix du prochain niveau" (specs.md 2.3/2.4) : propositions deterministes pour la
    graine et le niveau de la partie (deroulement.propositions_niveau)."""
    partie = partie_depuis_json(partie_json)
    return json.dumps({"niveau": partie.niveau, "propositions": [t.name for t in deroulement.propositions_niveau(partie)]})


def ecran_pour_etape_web(type_etape) -> str:
    """Ecran ouvert par l'etape choisie (deroulement.ecran_pour_etape, qui tire l'Aventure)."""
    return json.dumps(deroulement.ecran_pour_etape(TypeEtape[type_etape], random.Random()).name)


def ecran_reprise_web(partie_json) -> str:
    """Ecran ou reprendre une partie en cours, bouton "Continuer" (deroulement.ecran_de_reprise)."""
    return json.dumps(deroulement.ecran_de_reprise(partie_depuis_json(partie_json)).name)


def conclure_combat_partie_web(partie_json) -> str:
    """A appeler une seule fois, a la fin du combat `combat` (variable globale, celui qui vient de
    se terminer) : PV reportes sur la partie, Argent et candidats de recompense en cas de victoire
    (deroulement.conclure_combat). Renvoie {"partie", "candidats"}."""
    partie = partie_depuis_json(partie_json)
    candidats = deroulement.conclure_combat(partie, combat, random.Random())
    return json.dumps({
        "partie": json.loads(partie_vers_json(partie)),
        "candidats": [_candidat_recompense_json(spec, carte) for spec, carte in candidats if carte is not None],
    })


def resoudre_fin_combat_web(partie_json, victoire, id_carte) -> str:
    """Ecran de fin de combat ferme (deroulement.resoudre_fin_combat). Renvoie {"partie", "ecran"}."""
    partie = partie_depuis_json(partie_json)
    return _transition_json(partie, deroulement.resoudre_fin_combat(partie, bool(victoire), id_carte))


def terminer_victoire_finale_web(partie_json) -> str:
    """Bouton "Continuer" de l'ecran de victoire finale. Renvoie {"partie", "ecran"}."""
    partie = partie_depuis_json(partie_json)
    return _transition_json(partie, deroulement.terminer_victoire_finale(partie))


# --- Station service (specs.md 2.2) : 4 actions couttant chacune COUT_ACTION_STATION_SERVICE
# d'Argent, appliquees a un module equipe, memes fonctions pures que main.py:EcranStationService
# cote PC (src/gameplay/partie.py). Chaque fonction renvoie {"partie": ..., "succes": bool} :
# succes=False (Argent insuffisant, cf. src/gameplay/partie.py) laisse la partie inchangee,
# web/app.js doit alors afficher un retour "Argent insuffisant" plutot que l'effet normal. ---


def cout_action_station_service_web() -> str:
    """Expose COUT_ACTION_STATION_SERVICE (src/gameplay/partie.py) pour l'affichage du prix par
    action avant meme de la jouer - seule source de verite (CLAUDE.md), web/app.js ne duplique
    jamais cette valeur."""
    return json.dumps(COUT_ACTION_STATION_SERVICE)


def reparer_module_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    succes = reparer_module(partie, position)
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "succes": succes})


def ameliorer_module_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    succes = ameliorer_module(partie, position)
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "succes": succes})


def mettre_a_jour_module_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    succes = mettre_a_jour_module(partie, position)
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "succes": succes})


def deplacer_module_web(partie_json, position_source, position_destination) -> str:
    partie = partie_depuis_json(partie_json)
    succes = deplacer_module(partie, position_source, position_destination)
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "succes": succes})


def terminer_etape_web(partie_json) -> str:
    """Fin d'une etape hors combat (Station service, Aventures, Planete commerciale) :
    deroulement.terminer_etape. Renvoie {"partie", "ecran"}."""
    partie = partie_depuis_json(partie_json)
    return _transition_json(partie, deroulement.terminer_etape(partie))


# --- Aventure "Trois lunes" (specs.md 2.5) : choix unique parmi Reparer/Ameliorer/Bricoler,
# resolu immediatement, memes fonctions pures que src/ui/ecran_aventure_trois_lunes.py cote PC
# (src/gameplay/partie.py). Une seule Aventure implementee pour l'instant. ---


def constantes_aventure_trois_lunes_web() -> str:
    """Expose PV_REPARATION_VAISSEAU/PV_AMELIORATION (src/gameplay/partie.py) pour le texte des
    choix avant meme de les jouer - seule source de verite (CLAUDE.md), web/app.js ne duplique
    jamais ces valeurs."""
    return json.dumps({"pv_reparation_vaisseau": PV_REPARATION_VAISSEAU, "pv_amelioration": PV_AMELIORATION})


def deck_groupe_par_id_partie_web(partie_json) -> str:
    """Deck reel d'une partie pour le choix "Bricoler" (retirer_carte prend un id) : meme
    regroupement par id que deck_partie_web, conserve sous ce nom pour web/app.js."""
    return deck_partie_web(partie_json)


def reparer_vaisseau_aventure_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    reparer_vaisseau(partie)
    return partie_vers_json(partie)


def ameliorer_module_aventure_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    ameliorer_module_aventure(partie, position)
    return partie_vers_json(partie)


def retirer_carte_aventure_web(partie_json, id_carte) -> str:
    partie = partie_depuis_json(partie_json)
    retirer_carte(partie, id_carte)
    return partie_vers_json(partie)


# --- Aventure "Asteroides" (specs.md 2.5) : choix "Traverser" en 3 temps (module cible des
# degats, puis carte offerte) ou "Affronter les pirates" (combat scripte), memes fonctions pures
# que src/ui/ecran_aventure_asteroides.py cote PC (src/gameplay/partie.py). ---


def constantes_aventure_asteroides_web() -> str:
    """Expose DEGATS_ASTEROIDES (src/gameplay/partie.py) pour le texte des choix avant de les
    jouer - seule source de verite (CLAUDE.md), web/app.js ne duplique jamais cette valeur."""
    return json.dumps({"degats_asteroides": DEGATS_ASTEROIDES})


def subir_degats_module_asteroides_web(partie_json, position) -> str:
    partie = partie_depuis_json(partie_json)
    subir_degats_module(partie, position, DEGATS_ASTEROIDES)
    return partie_vers_json(partie)


def _carte_avec_id_json(carte) -> dict:
    """Meme forme que _candidat_recompense_json, sans le module associe (non pertinent pour une
    carte offerte/tiree hors combat, specs.md 2.5)."""
    return {
        "id_carte": carte.id,
        "nom": carte.nom,
        "image": _chemin_web(carte.image),
        "cout": carte.cout,
        "rarete": carte.rarete.name,
        "valeur": carte.valeur,
        "type": carte.type.name,
        "cible": carte.cible.name,
        "action": carte.action.name if carte.action else None,
        "duree": carte.duree,
    }


def second_choc_asteroides_web(partie_json, position) -> str:
    """2e choc du choix "Traverser" (specs.md 2.5) : degats et tirage de la carte offerte (ou
    non) decides en une seule fois par second_choc_asteroides (src/gameplay/partie.py) - jamais
    recalcule ici, seulement serialise (cf. CLAUDE.md, gameplay commun aux deux interfaces)."""
    partie = partie_depuis_json(partie_json)
    cartes = charger_cartes()
    carte = second_choc_asteroides(partie, position, cartes, random.Random())
    return json.dumps({
        "partie": json.loads(partie_vers_json(partie)),
        "carte": _carte_avec_id_json(carte) if carte is not None else None,
    })


def prendre_carte_offerte_asteroides_web(partie_json, id_carte) -> str:
    partie = partie_depuis_json(partie_json)
    ajouter_carte(partie, id_carte)
    return partie_vers_json(partie)


def combat_aventure_asteroides_web(partie_json) -> str:
    """Choix "Affronter les pirates" (specs.md 2.5) : demarre le combat scripte a partir du
    vaisseau/deck reels de la partie, meme logique que continuer_partie_web mais avec une flotte
    fixee (combat_aventure_asteroides) plutot que le tirage standard lie au niveau."""
    global combat
    partie = partie_depuis_json(partie_json)
    combat = combat_aventure_asteroides(partie)
    return json.dumps({"etat": _etat_dict(), "popups": []})


# --- Aventure "Police" (specs.md 2.5) : une carte est tiree au hasard du deck reel du joueur et
# affichee avant les choix - Confiscation / Mettre aux normes / Detourner l'attention. L'etat de
# resolution (carte actuelle, disponibilite de "Detourner", specs.md 2.5 : une seule fois par
# Aventure) est possede par le gameplay (src/gameplay/partie.py:EtatAventurePolice, variable
# globale etat_aventure_police ci-dessus - meme principe que `combat`), jamais recalcule ou
# retrouve cote JS (cf. CLAUDE.md, gameplay commun aux deux interfaces). ---


def constantes_aventure_police_web() -> str:
    """Expose COUT_METTRE_AUX_NORMES (src/gameplay/partie.py) pour le texte du choix avant de le
    jouer - seule source de verite (CLAUDE.md), web/app.js ne duplique jamais cette valeur."""
    return json.dumps({"cout_mettre_aux_normes": COUT_METTRE_AUX_NORMES})


def _etat_aventure_police_json() -> dict:
    cartes = charger_cartes()
    return {
        "carte": _carte_avec_id_json(cartes[etat_aventure_police.id_carte_actuelle]),
        "detourner_disponible": etat_aventure_police.detourner_disponible,
    }


def demarrer_aventure_police_web(partie_json) -> str:
    """Tire la premiere carte et initialise l'etat de resolution de l'Aventure "Police" (specs.md
    2.5, demarrer_aventure_police) - appelee a l'ouverture de l'ecran."""
    global etat_aventure_police
    partie = partie_depuis_json(partie_json)
    etat_aventure_police = demarrer_aventure_police(partie, random.Random())
    return json.dumps(_etat_aventure_police_json())


def detourner_police_web(partie_json) -> str:
    """Choix "Detourner l'attention" (specs.md 2.5, detourner_aventure_police) : `succes` est
    False si deja utilise pour cette Aventure - le bouton correspondant est deja masque cote JS
    dans ce cas (`detourner_disponible`), ce champ n'est qu'une securite supplementaire."""
    partie = partie_depuis_json(partie_json)
    succes = detourner_aventure_police(etat_aventure_police, partie, random.Random())
    resultat = _etat_aventure_police_json()
    resultat["succes"] = succes
    return json.dumps(resultat)


def confiscation_police_web(partie_json) -> str:
    """Retire la carte actuellement tiree (etat_aventure_police.id_carte_actuelle) - plus besoin
    de la transmettre depuis JS, le gameplay la connait deja."""
    partie = partie_depuis_json(partie_json)
    retirer_carte(partie, etat_aventure_police.id_carte_actuelle)
    return partie_vers_json(partie)


def mettre_aux_normes_police_web(partie_json) -> str:
    partie = partie_depuis_json(partie_json)
    succes = payer_mise_aux_normes(partie)
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "succes": succes})


def _resoudre_cible(carte, id_cible):
    if carte.cible in CIBLES_SANS_CLIC:
        return None
    if carte.cible in (CibleCarte.ALLIE_UNIQUE, CibleCarte.COLONNE_AVANT_ALLIEE):
        if id_cible == "base":
            return combat.joueur.vaisseau.base
        position = IDS_MODULES.get(id_cible)
        return combat.joueur.vaisseau.modules_equipes().get(position) if position else None
    position = IDS_ENNEMIS.get(id_cible)
    return combat.flotte.positions().get(position) if position else None


def jouer_carte(index_carte: int, id_cible) -> str:
    """Joue la carte en main a cet index sur la cible designee par son id (ou None)."""
    carte = combat.joueur.deck.main[index_carte]
    cible = _resoudre_cible(carte, id_cible)
    resultats = combat.jouer_carte(carte, cible)
    action = carte.action.name if carte.action else None
    popups = [popup for cible_touchee, valeur in resultats if (popup := _popup(cible_touchee, carte.type.name, valeur, action))]
    return json.dumps({"etat": _etat_dict(), "popups": popups})


def finir_tour() -> str:
    """Termine le tour du joueur ; renvoie aussi un popup par evenement ennemi resolu
    (specs.md 13) : -N (degats) sur un module, sur un autre ennemi si Tir allie est actif
    sur l'attaquant (specs.md 12.6), ou sur l'attaquant lui-meme en cas de renvoi par un
    Bouclier miroir ; +N (bouclier) sur la cible d'une Action POSE_BUFF."""
    evenements = combat.finir_tour_joueur()
    popups = []
    for _position, _ennemi, cible, valeur, type_evenement in evenements:
        if isinstance(cible, Module):
            id_case, camp = _id_module(cible), "allie"
        else:
            id_case, camp = _id_ennemi(cible), "ennemi"
        if id_case is None:
            continue
        if type_evenement == "bouclier":
            popups.append({"id": id_case, "camp": camp, "texte": f"+{valeur}", "couleur": "bouclier"})
        else:
            popups.append({"id": id_case, "camp": camp, "texte": f"-{valeur}", "couleur": "degats"})
    return json.dumps({"etat": _etat_dict(), "popups": popups})
