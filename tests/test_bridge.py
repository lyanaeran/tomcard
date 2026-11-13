"""
Tests de web/bridge.py (pont entre l'affichage web et src/gameplay), appele directement en Python :
c'est le meme code que celui execute par Pyodide (web/CLAUDE.md).
"""

import importlib.util
import json
import random
from pathlib import Path

import pytest

from src.gameplay.carte_new import charger_cartes_new
from src.gameplay.combat_new import CombatNew
from src.gameplay.ennemi_new import charger_ennemis_new
from src.gameplay.flotte_new import flotte_boss
from src.gameplay.module_new import charger_modules_new

FICHIER_BRIDGE = Path(__file__).resolve().parents[1] / "web" / "bridge.py"


@pytest.fixture
def bridge():
    """Module bridge.py charge a neuf (son etat de combat est global)."""
    spec = importlib.util.spec_from_file_location("bridge_web", FICHIER_BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _combat_contre_le_boss(ids_main: list[str]) -> CombatNew:
    """Principal (M1) et Lanceur (M2) contre le Boss, avec ces cartes en main."""
    modeles = charger_modules_new()
    modules = [
        modeles["MOD_1"].nouvel_exemplaire("M1", "base").copie_pour_combat(),
        modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche").copie_pour_combat(),
    ]
    cartes = charger_cartes_new()
    deck = [cartes[id_carte].copie(exemplaire_module="M1") for id_carte in ids_main]
    combat = CombatNew(modules, deck, flotte_boss(charger_ennemis_new()), random.Random(1))
    assert sorted(carte.id for carte in combat.deck.main) == sorted(ids_main)
    return combat


def test_ligne_arriere_se_joue_sur_la_case_arriere_du_boss(bridge):
    """Le Boss n'a qu'un id de case cote affichage (AV_M) mais occupe aussi la case Arriere :
    une carte Ennemi Arriere (Ligne arriere) doit pouvoir le viser."""
    etat = json.loads(bridge._demarrer_combat(_combat_contre_le_boss(["CRT_16"] * 3)))["etat"]
    carte = etat["main"][0]
    assert carte["jouable"] and carte["cases"] == ["AV_M"]

    resultat = json.loads(bridge.jouer_carte(carte["index"], "AV_M"))

    boss = next(ennemi for ennemi in resultat["etat"]["ennemis"] if ennemi)
    assert boss["pv"] < boss["pv_max"]
    assert resultat["popups"][0]["id"] == "AV_M"


def test_une_attaque_entierement_bloquee_par_le_bouclier_affiche_bloque(bridge):
    bridge._demarrer_combat(_combat_contre_le_boss(["CRT_7", "CRT_7"]))
    boss = bridge.combat.flotte.ennemis[0]
    boss.statuts.ajouter(bridge.Statut.BOUCLIER, 50)

    resultat = json.loads(bridge.jouer_carte(0, "AV_M"))

    assert resultat["popups"][0]["texte"].startswith("bloqué")
    assert "-0" not in resultat["popups"][0]["texte"]


def test_un_secondaire_s_affiche_avec_ses_pv_du_prochain_combat(bridge):
    partie = json.loads(bridge.nouvelle_partie_web())["partie"]
    partie = json.loads(bridge.choisir_module_partie_web(json.dumps(partie), "MOD_2"))["partie"]
    partie["vaisseau"]["avant_gauche"]["pv"] = 3

    vaisseau = json.loads(bridge.infos_vaisseau_web(json.dumps(partie)))

    assert vaisseau["avant_gauche"]["pv"] == vaisseau["avant_gauche"]["pv_max"]


def _partie_au_niveau_2(bridge) -> dict:
    partie = json.loads(bridge.nouvelle_partie_web())["partie"]
    partie = json.loads(bridge.choisir_module_partie_web(json.dumps(partie), "MOD_2"))["partie"]
    return json.loads(bridge.resoudre_carte_module_web(json.dumps(partie), None, None))["partie"]


def _terminer_le_combat(bridge, victoire: bool) -> None:
    """Fin de combat simulee, sans jouer de cartes."""
    etats = type(bridge.combat.etat)
    if victoire:
        for ennemi in bridge.combat.flotte.ennemis:
            ennemi.pv = 0
    else:
        bridge.combat.vaisseau.principal.pv_combat = 0
    bridge.combat.etat = etats.VICTOIRE if victoire else etats.DEFAITE


def test_une_partie_rechargee_sur_la_recompense_ne_rejoue_pas_le_niveau(bridge):
    """Rechargement de la page sur l'ecran de recompense : l'Argent n'est gagne qu'une fois."""
    partie = _partie_au_niveau_2(bridge)
    bridge.continuer_partie_web(json.dumps(partie))
    _terminer_le_combat(bridge, victoire=True)
    conclusion = json.loads(bridge.conclure_combat_partie_web(json.dumps(partie)))
    sauvegardee = json.dumps(conclusion["partie"])

    assert json.loads(bridge.ecran_reprise_web(sauvegardee)) == "RECOMPENSE"
    en_attente = json.loads(bridge.recompense_en_attente_web(sauvegardee))
    assert [(c["id_carte"], c["module"]) for c in en_attente] == [
        (c["id_carte"], c["module"]) for c in conclusion["candidats"]
    ]
    carte = en_attente[0]
    suite = json.loads(bridge.resoudre_fin_combat_web(sauvegardee, True, carte["id_carte"], carte["module"]))
    assert suite["ecran"] == "CHOIX_NIVEAU"
    assert suite["partie"]["niveau"] == 3 and suite["partie"]["recompense"] is None
    assert suite["partie"]["argent"] == conclusion["partie"]["argent"]


def test_une_defaite_termine_la_partie_des_la_fin_du_combat(bridge):
    """Sinon une partie quittee sur l'ecran de defaite restait en cours avec un principal detruit."""
    partie = _partie_au_niveau_2(bridge)
    bridge.continuer_partie_web(json.dumps(partie))
    _terminer_le_combat(bridge, victoire=False)

    conclusion = json.loads(bridge.conclure_combat_partie_web(json.dumps(partie)))

    assert conclusion["partie"]["statut"] == "TERMINEE" and conclusion["candidats"] == []


def test_la_station_dit_pourquoi_une_action_est_refusee(bridge):
    partie = _partie_au_niveau_2(bridge)
    partie["argent"] = 100

    plein = json.loads(bridge.reparer_principal_web(json.dumps(partie)))
    assert (plein["succes"], plein["raison"], plein["partie"]["argent"]) == (False, "INUTILE", 100)

    partie["argent"] = 0
    pauvre = json.loads(bridge.ameliorer_module_web(json.dumps(partie), "base"))
    assert (pauvre["succes"], pauvre["raison"]) == (False, "ARGENT_INSUFFISANT")

    partie["argent"] = 100
    reussi = json.loads(bridge.ameliorer_module_web(json.dumps(partie), "base"))
    assert (reussi["succes"], reussi["raison"]) == (True, "OK")
