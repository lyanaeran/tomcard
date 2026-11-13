"""
Tests unitaires pour src/gameplay/deroulement.py (enchainement des ecrans, specs.md 2.4).
"""

import random

import pytest

from src.gameplay import deroulement
from src.gameplay.carte_new import charger_cartes_new
from src.gameplay.combat_new import EtatCombatNew
from src.gameplay.deroulement import Ecran
from src.gameplay.module_new import charger_modules_new
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import (
    ARGENT_DEPART,
    STATUT_EN_COURS,
    STATUT_TERMINEE,
    CartePossedee,
    combat_depuis_partie,
    nouvelle_partie,
)


def _carte(id_carte: str, exemplaire: str):
    return charger_cartes_new()[id_carte].copie(exemplaire_module=exemplaire)


def _partie_au_niveau_2() -> deroulement.Partie:
    partie = nouvelle_partie(random.Random(1))
    modele = deroulement.candidats_choix_module(partie)[0]
    deroulement.choisir_module(partie, modele, random.Random(2))
    deroulement.resoudre_carte_module(partie, None)
    return partie


def test_ecran_de_reprise_niveau_1_sans_module_reprend_au_choix_de_module():
    assert deroulement.ecran_de_reprise(nouvelle_partie(random.Random(1))) == Ecran.CHOIX_MODULE


def test_ecran_de_reprise_apres_choix_du_module_reprend_au_choix_de_niveau():
    assert deroulement.ecran_de_reprise(_partie_au_niveau_2()) == Ecran.CHOIX_NIVEAU


def test_choisir_module_equipe_le_module_et_propose_des_cartes_de_son_pool():
    partie = nouvelle_partie(random.Random(1))
    modele = deroulement.candidats_choix_module(partie)[0]

    candidats = deroulement.choisir_module(partie, modele, random.Random(2))

    module = partie.vaisseau["avant_gauche"]
    assert (module.id, module.exemplaire) == (modele.id, "M2")
    assert candidats
    assert all(carte.id in modele.cartes and carte.exemplaire_module == "M2" for carte in candidats)


def test_resoudre_carte_module_ajoute_la_carte_et_avance_au_niveau_2():
    partie = nouvelle_partie(random.Random(1))
    candidats = deroulement.choisir_module(partie, deroulement.candidats_choix_module(partie)[0], random.Random(2))
    taille_deck = len(partie.deck)

    ecran = deroulement.resoudre_carte_module(partie, candidats[0])

    assert ecran == Ecran.CHOIX_NIVEAU
    assert partie.niveau == 2
    assert partie.deck[-1] == CartePossedee(candidats[0].id, "M2")
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
    for ennemi in combat.flotte.ennemis:
        ennemi.pv = 0
    combat.etat = EtatCombatNew.VICTOIRE

    candidats = deroulement.conclure_combat(partie, combat, random.Random(5))

    assert partie.argent > ARGENT_DEPART
    # Principal + module du niveau 1, chaque carte rattachee a son module
    assert [module.exemplaire for module, _carte in candidats] == ["M1", "M2"]
    assert [carte.exemplaire_module for _module, carte in candidats] == ["M1", "M2"]


def test_conclure_combat_defaite_reporte_les_pv_sans_argent_ni_candidat():
    partie = _partie_au_niveau_2()
    combat = combat_depuis_partie(partie, random.Random(4))
    combat.vaisseau.principal.pv_combat = 7
    combat.etat = EtatCombatNew.DEFAITE

    assert deroulement.conclure_combat(partie, combat, random.Random(5)) == []
    assert partie.argent == ARGENT_DEPART
    assert partie.vaisseau["base"].pv == 7
    # La partie est terminee tout de suite : la quitter sur l'ecran de defaite ne la bloque pas
    assert partie.statut == STATUT_TERMINEE and partie.recompense is None


def test_un_combat_en_cours_ne_se_conclut_pas():
    partie = _partie_au_niveau_2()
    combat = combat_depuis_partie(partie, random.Random(4))

    with pytest.raises(ValueError, match="pas termine"):
        deroulement.conclure_combat(partie, combat, random.Random(5))


def test_une_partie_quittee_sur_la_recompense_reprend_a_la_recompense():
    """Sinon le niveau deja gagne se rejouait, et l'Argent etait gagne deux fois."""
    partie = _partie_au_niveau_2()
    combat = combat_depuis_partie(partie, random.Random(4))
    for ennemi in combat.flotte.ennemis:
        ennemi.pv = 0
    combat.etat = EtatCombatNew.VICTOIRE
    candidats = deroulement.conclure_combat(partie, combat, random.Random(5))

    assert deroulement.ecran_de_reprise(partie) == Ecran.RECOMPENSE
    en_attente = deroulement.recompense_en_attente(partie)
    assert [(m.exemplaire, c.id, c.exemplaire_module) for m, c in en_attente] == [
        (m.exemplaire, c.id, c.exemplaire_module) for m, c in candidats
    ]

    with pytest.raises(ValueError, match="pas parmi"):
        deroulement.resoudre_fin_combat(partie, True, _carte("CRT_7", "M1"))
    assert deroulement.resoudre_fin_combat(partie, True, en_attente[0][1]) == Ecran.CHOIX_NIVEAU
    assert partie.recompense is None and partie.niveau == 3
    assert deroulement.ecran_de_reprise(partie) == Ecran.CHOIX_NIVEAU


def test_resoudre_fin_combat_defaite_termine_la_partie():
    partie = _partie_au_niveau_2()

    assert deroulement.resoudre_fin_combat(partie, False, None) == Ecran.ACCUEIL
    assert partie.statut == STATUT_TERMINEE


def test_resoudre_fin_combat_victoire_ajoute_la_carte_et_avance():
    partie = _partie_au_niveau_2()

    ecran = deroulement.resoudre_fin_combat(partie, True, _carte("CRT_9", "M2"))

    assert ecran == Ecran.CHOIX_NIVEAU
    assert partie.niveau == 3
    assert partie.deck[-1] == CartePossedee("CRT_9", "M2")
    assert partie.statut == STATUT_EN_COURS


def test_resoudre_fin_combat_victoire_au_boss_mene_a_la_victoire_finale_sans_avancer():
    partie = _partie_au_niveau_2()
    partie.niveau = 10

    assert deroulement.resoudre_fin_combat(partie, True, None) == Ecran.VICTOIRE_FINALE
    assert partie.niveau == 10
    # Partie terminee des la victoire sur le Boss : on ne peut pas le rejouer
    assert partie.statut == STATUT_TERMINEE


def test_terminer_victoire_finale_termine_la_partie():
    partie = _partie_au_niveau_2()

    assert deroulement.terminer_victoire_finale(partie) == Ecran.ACCUEIL
    assert partie.statut == STATUT_TERMINEE


def test_candidats_choix_module_parmi_les_modules_equipables():
    ids_equipables = {module.id for module in charger_modules_new().values() if not module.principal and module.cartes}

    candidats = deroulement.candidats_choix_module(nouvelle_partie(random.Random(1)))

    assert candidats and {module.id for module in candidats} <= ids_equipables
