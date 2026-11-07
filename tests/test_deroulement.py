"""
Tests unitaires pour src/gameplay/deroulement.py (enchainement des ecrans, specs.md 2.4).
"""

import random

from src.gameplay import deroulement
from src.gameplay.combat import EtatCombat
from src.gameplay.deroulement import Ecran
from src.gameplay.donnees import charger_modules
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import (
    ARGENT_DEPART,
    STATUT_EN_COURS,
    STATUT_TERMINEE,
    combat_depuis_partie,
    nouvelle_partie,
)


def _partie_au_niveau_2() -> deroulement.Partie:
    partie = nouvelle_partie(random.Random(1))
    spec = deroulement.candidats_choix_module(partie)[0]
    deroulement.choisir_module(partie, spec, random.Random(2))
    deroulement.resoudre_carte_module(partie, None)
    return partie


def test_ecran_de_reprise_niveau_1_sans_module_reprend_au_choix_de_module():
    assert deroulement.ecran_de_reprise(nouvelle_partie(random.Random(1))) == Ecran.CHOIX_MODULE


def test_ecran_de_reprise_apres_choix_du_module_reprend_au_choix_de_niveau():
    assert deroulement.ecran_de_reprise(_partie_au_niveau_2()) == Ecran.CHOIX_NIVEAU


def test_choisir_module_equipe_le_module_et_propose_des_cartes_de_son_pool():
    partie = nouvelle_partie(random.Random(1))
    spec = deroulement.candidats_choix_module(partie)[0]

    candidats = deroulement.choisir_module(partie, spec, random.Random(2))

    assert partie.vaisseau["avant_gauche"].module_id == spec.id
    assert all(carte.id in spec.cartes for carte in candidats)


def test_resoudre_carte_module_ajoute_la_carte_et_avance_au_niveau_2():
    partie = nouvelle_partie(random.Random(1))
    taille_deck = len(partie.deck)

    ecran = deroulement.resoudre_carte_module(partie, "CRT_47")

    assert ecran == Ecran.CHOIX_NIVEAU
    assert partie.niveau == 2
    assert partie.deck[-1] == "CRT_47"
    assert len(partie.deck) == taille_deck + 1


def test_propositions_niveau_deterministes_pour_une_meme_partie():
    partie = _partie_au_niveau_2()

    assert deroulement.propositions_niveau(partie) == deroulement.propositions_niveau(partie)


def test_ecran_pour_etape():
    aleatoire = random.Random(3)
    assert deroulement.ecran_pour_etape(TypeEtape.PRIME, aleatoire) == Ecran.COMBAT
    assert deroulement.ecran_pour_etape(TypeEtape.BOSS, aleatoire) == Ecran.COMBAT
    assert deroulement.ecran_pour_etape(TypeEtape.STATION_SERVICE, aleatoire) == Ecran.STATION_SERVICE
    assert deroulement.ecran_pour_etape(TypeEtape.PLANETE_COMMERCIALE, aleatoire) == Ecran.PLANETE_COMMERCIALE
    assert deroulement.ecran_pour_etape(TypeEtape.AVENTURE, aleatoire) in deroulement.ECRAN_PAR_AVENTURE.values()


def test_terminer_etape_avance_d_un_niveau():
    partie = _partie_au_niveau_2()

    assert deroulement.terminer_etape(partie) == Ecran.CHOIX_NIVEAU
    assert partie.niveau == 3


def test_conclure_combat_victoire_donne_argent_et_candidats():
    partie = _partie_au_niveau_2()
    combat = combat_depuis_partie(partie, random.Random(4))
    for ennemi in combat.flotte.positions().values():
        ennemi.pv = 0
    combat.etat = EtatCombat.VICTOIRE

    candidats = deroulement.conclure_combat(partie, combat, random.Random(5))

    assert partie.argent > ARGENT_DEPART
    assert len(candidats) == 2  # principal + module du niveau 1


def test_conclure_combat_defaite_reporte_les_pv_sans_argent_ni_candidat():
    partie = _partie_au_niveau_2()
    combat = combat_depuis_partie(partie, random.Random(4))
    combat.joueur.vaisseau.base.pv = 7
    combat.etat = EtatCombat.DEFAITE

    assert deroulement.conclure_combat(partie, combat, random.Random(5)) == []
    assert partie.argent == ARGENT_DEPART
    assert partie.vaisseau["base"].pv == 7


def test_resoudre_fin_combat_defaite_termine_la_partie():
    partie = _partie_au_niveau_2()

    assert deroulement.resoudre_fin_combat(partie, False, None) == Ecran.ACCUEIL
    assert partie.statut == STATUT_TERMINEE


def test_resoudre_fin_combat_victoire_ajoute_la_carte_et_avance():
    partie = _partie_au_niveau_2()

    ecran = deroulement.resoudre_fin_combat(partie, True, "CRT_47")

    assert ecran == Ecran.CHOIX_NIVEAU
    assert partie.niveau == 3
    assert partie.deck[-1] == "CRT_47"
    assert partie.statut == STATUT_EN_COURS


def test_resoudre_fin_combat_victoire_au_boss_mene_a_la_victoire_finale_sans_avancer():
    partie = _partie_au_niveau_2()
    partie.niveau = 10

    assert deroulement.resoudre_fin_combat(partie, True, None) == Ecran.VICTOIRE_FINALE
    assert partie.niveau == 10


def test_terminer_victoire_finale_termine_la_partie():
    partie = _partie_au_niveau_2()

    assert deroulement.terminer_victoire_finale(partie) == Ecran.ACCUEIL
    assert partie.statut == STATUT_TERMINEE


def test_candidats_choix_module_parmi_les_modules_equipables():
    ids_equipables = {spec.id for spec in charger_modules() if spec.id != "MOD_1" and spec.cartes}

    candidats = deroulement.candidats_choix_module(nouvelle_partie(random.Random(1)))

    assert candidats and {spec.id for spec in candidats} <= ids_equipables
