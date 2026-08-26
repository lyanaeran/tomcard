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
from src.gameplay.config_poc import creer_combat_poc, creer_deck, creer_vaisseau
from src.gameplay.donnees import charger_cartes, charger_modules, image_case_module
from src.gameplay.module import Module
from src.gameplay.parcours import (
    aleatoire_pour_niveau,
    est_niveau_boss,
    modules_equipables,
    tirer_candidats_module,
    tirer_candidats_recompense,
    tirer_propositions_niveau,
)
from src.gameplay.partie import (
    COUT_ACTION_STATION_SERVICE,
    ajouter_carte,
    ameliorer_module,
    avancer_niveau,
    combat_depuis_partie,
    deck_de_la_partie,
    deplacer_module,
    equiper_module,
    gagner_argent_combat,
    id_de_carte,
    marquer_terminee,
    mettre_a_jour_module,
    nouveau_profil,
    nouvelle_partie,
    partie_depuis_json,
    partie_vers_json,
    profil_vers_json,
    reparer_module,
    specs_utilisees_partie,
    synchroniser_vaisseau_depuis_combat,
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


def _intention_json(ennemi):
    """Intention de cet ennemi : module vise et degats que cet
    ennemi infligerait, calcules avec la meme fonction que fenetre.py (previsualiser_cible
    + degats_attaque_effectifs, aucune logique dupliquee).

    Volontairement la valeur "brute" de l'ennemi, pas _degats_effectifs de combat.py (qui
    plafonne selon PV+bouclier de la cible et renvoie 0 si un leurre est actif, specs.md
    12.6) : l'intention doit montrer la vraie attaque de chaque ennemi, meme si plusieurs
    ennemis visent un module leurre - un seul des deux sera reellement annule a la
    resolution, mais lequel n'est determine qu'a ce moment-la (ordre de resolution).

    Si Tir allie est actif (specs.md 12.6), previsualiser_cible renvoie None expres (la
    cible reelle - un autre ennemi - n'est tiree au hasard qu'a la resolution du tour,
    jamais au survol/tap, pour rester deterministe) : on le signale explicitement plutot
    que de renvoyer None comme pour "aucune cible a portee", pour que l'UI l'affiche."""
    if ennemi.est_detruit():
        return None
    if any(debuff.action == ActionCarte.REDIRECTION_CIBLE for debuff in ennemi.debuffs_actifs):
        return {"redirection": True}
    cible = combat.previsualiser_cible(ennemi)
    if cible is None:
        return None
    return {
        "redirection": False,
        "module_id": _id_module(cible),
        "module_nom": cible.nom,
        "degats": ennemi.degats_attaque_effectifs(),
    }


def _debuffs_json(ennemi):
    """Debuffs actifs de cet ennemi (specs.md 12.1/12.4), chacun independant des autres
    (aucune fusion : la magnitude affichee est celle de cette instance, pas la somme)."""
    return [
        {"action": debuff.action.name, "valeur": debuff.valeur, "tours_restants": debuff.tours_restants}
        for debuff in ennemi.debuffs_actifs
    ]


def _ennemi_json(ennemi, id_case: str):
    if ennemi is None:
        return None
    return {
        "id": id_case,
        "nom": ennemi.nom,
        "pv": ennemi.pv,
        "pv_max": ennemi.pv_max,
        "detruit": ennemi.est_detruit(),
        "image": _chemin_web(ennemi.image),
        "degats_attaque": ennemi.degats_attaque_effectifs(),
        "intention": _intention_json(ennemi),
        "debuffs": _debuffs_json(ennemi),
    }


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
    ennemis_json = [_ennemi_json(flotte.positions().get(pos), id_case) for id_case, pos in IDS_ENNEMIS.items()]
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


def _candidat_recompense_json(spec, carte, cartes: dict) -> dict:
    return {
        "module_nom": spec.nom,
        "carte_nom": carte.nom,
        "carte_id": id_de_carte(carte, cartes),
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
        [_candidat_recompense_json(spec, carte, cartes) for spec, carte in candidats if carte is not None]
    )


def _carte_regroupee_json(carte, quantite: int) -> dict:
    return {
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
    return partie_vers_json(nouvelle_partie())


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
    """Candidats de choix de module (Niveau 1, specs.md 2.3) pour une partie qui vient d'etre
    creee, tires a partir de sa graine (coherence avec specs.md 10.3 - meme logique que
    nouveau_choix_module, mais deterministe par rapport a la graine de la partie plutot que
    tire independamment)."""
    partie = partie_depuis_json(partie_json)
    pool = modules_equipables(charger_modules())
    candidats = tirer_candidats_module(pool, random.Random(partie.graine))
    return json.dumps(
        [
            {"id": candidat.id, "nom": candidat.nom, "image": _chemin_web(candidat.image), "description": candidat.description}
            for candidat in candidats
        ]
    )


def choisir_module_partie_web(partie_json, module_id) -> str:
    """Equipe le module choisi (Niveau 1, specs.md 2.3/2.4) et avance au niveau suivant ; renvoie
    la partie mise a jour (web/app.js la re-sauvegarde dans localStorage puis enchaine sur le
    choix du niveau) - meme logique que main.py:_ouvrir_choix_module cote PC."""
    partie = partie_depuis_json(partie_json)
    specs_par_id = {spec.id: spec for spec in charger_modules()}
    equiper_module(partie, specs_par_id[module_id])
    avancer_niveau(partie)
    return partie_vers_json(partie)


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
    """Ecran "Choix du prochain niveau" (specs.md 2.3/2.4) : 3 propositions d'etape tirees de
    facon deterministe a partir de la graine et du niveau de la partie (ou une seule, BOSS, a un
    niveau Boss - cf. src/gameplay/parcours.py:tirer_propositions_niveau)."""
    partie = partie_depuis_json(partie_json)
    aleatoire = aleatoire_pour_niveau(partie.graine, partie.niveau)
    propositions = tirer_propositions_niveau(partie.niveau, aleatoire)
    return json.dumps({"niveau": partie.niveau, "propositions": [type_etape.name for type_etape in propositions]})


def candidats_recompense_partie_web(partie_json) -> str:
    """Candidats de recompense de fin de combat (victoire) pour une partie reelle (specs.md 2.1/6),
    un par module effectivement equipe sur cette partie (specs_utilisees_partie) plutot qu'un
    vaisseau tire au sort comme fin_combat_victoire (demo) - meme logique que
    main.py:_ouvrir_fin_combat cote PC."""
    partie = partie_depuis_json(partie_json)
    specs_par_id = {spec.id: spec for spec in charger_modules()}
    cartes = charger_cartes()
    candidats = tirer_candidats_recompense(specs_utilisees_partie(partie, specs_par_id), cartes, random.Random())
    return json.dumps(
        [_candidat_recompense_json(spec, carte, cartes) for spec, carte in candidats if carte is not None]
    )


def resoudre_victoire_partie_web(partie_json, id_carte) -> str:
    """Resout la victoire d'un combat pour une partie reelle : reporte d'abord les PV du combat
    qui vient de se terminer (`combat`, variable globale toujours celle de ce combat a ce stade -
    cf. continuer_partie_web) sur la partie (specs.md 2.2/3.4 : persistance des PV entre combats,
    meme logique que main.py:_ouvrir_combat cote PC), puis ajoute la carte choisie (id_carte, ou
    None si aucun candidat n'etait propose), puis avance au niveau suivant - sauf si c'etait un
    Boss, auquel cas le niveau n'avance pas encore et la partie reste EN_COURS : web/app.js doit
    d'abord ouvrir l'ecran de victoire finale (cle "niveau_boss") avant de marquer la partie
    TERMINEE (terminer_victoire_finale_web, une fois l'ecran ferme) - meme logique que
    main.py:_ouvrir_fin_combat/_ouvrir_victoire_finale cote PC. Renvoie
    {"partie": ..., "niveau_boss": bool}."""
    partie = partie_depuis_json(partie_json)
    synchroniser_vaisseau_depuis_combat(partie, combat.joueur.vaisseau)
    gagner_argent_combat(partie, combat)  # specs.md 2.1 : Argent par ennemi tue
    if id_carte is not None:
        ajouter_carte(partie, id_carte)
    boss = est_niveau_boss(partie.niveau)
    if not boss:
        avancer_niveau(partie)
    return json.dumps({"partie": json.loads(partie_vers_json(partie)), "niveau_boss": boss})


def terminer_victoire_finale_web(partie_json) -> str:
    """Bouton "Continuer" de l'ecran de victoire finale (specs.md 2.4, etape 11) : marque la partie
    TERMINEE, meme logique que main.py:_ouvrir_victoire_finale cote PC. Renvoie la partie mise a
    jour (web/app.js la re-sauvegarde dans localStorage)."""
    partie = partie_depuis_json(partie_json)
    marquer_terminee(partie)
    return partie_vers_json(partie)


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


def terminer_station_service_web(partie_json) -> str:
    """Bouton "J'ai termine" de l'ecran Station service : avance au niveau suivant (specs.md 2.4,
    etape 8), meme logique que main.py:_ouvrir_station_service cote PC. Renvoie la partie mise a
    jour (web/app.js la re-sauvegarde dans localStorage puis enchaine sur le choix du niveau)."""
    partie = partie_depuis_json(partie_json)
    avancer_niveau(partie)
    return partie_vers_json(partie)


def terminer_etape_placeholder_web(partie_json) -> str:
    """Bouton "J'ai termine" de l'ecran generique Aventure/Planete commerciale (contenu pas encore
    prepare, specs.md 2.4 etapes 7/9, 9.1) : avance au niveau suivant, meme logique que
    main.py:_ouvrir_etape_placeholder cote PC. Renvoie la partie mise a jour (web/app.js la
    re-sauvegarde dans localStorage puis enchaine sur le choix du niveau)."""
    partie = partie_depuis_json(partie_json)
    avancer_niveau(partie)
    return partie_vers_json(partie)


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
    """Termine le tour du joueur ; renvoie aussi un popup -N par attaque ennemie resolue.

    La cible peut etre un module (cas normal) ou un autre ennemi si Tir allie est actif sur
    l'attaquant (specs.md 12.6, resolu dans Combat._tour_ennemi)."""
    attaques = combat.finir_tour_joueur()
    popups = []
    for _position, _ennemi, cible, degats_effectifs in attaques:
        if isinstance(cible, Module):
            id_case, camp = _id_module(cible), "allie"
        else:
            id_case, camp = _id_ennemi(cible), "ennemi"
        if id_case is not None:
            popups.append({"id": id_case, "camp": camp, "texte": f"-{degats_effectifs}", "couleur": "degats"})
    return json.dumps({"etat": _etat_dict(), "popups": popups})
