"""
Tests de src/web/bridge.py (pont entre l'affichage web et src/gameplay), appele directement en Python :
c'est le meme code que celui execute par Pyodide (src/web/CLAUDE.md).
"""

import importlib.util
import json
import random
from pathlib import Path

import pytest

from src.gameplay.carte import charger_cartes
from src.gameplay.combat import Combat
from src.gameplay.ennemi import charger_ennemis
from src.gameplay.flotte import flotte_boss
from src.gameplay.module import charger_modules

FICHIER_BRIDGE = Path(__file__).resolve().parents[1] / "src" / "web" / "bridge.py"


@pytest.fixture
def bridge():
    """Module bridge.py charge a neuf (son etat de combat est global)."""
    spec = importlib.util.spec_from_file_location("bridge_web", FICHIER_BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _combat_contre_le_boss(ids_main: list[str]) -> Combat:
    """Principal (M1) et Lanceur (M2) contre le Boss, avec ces cartes en main."""
    modeles = charger_modules()
    modules = [
        modeles["MOD_1"].nouvel_exemplaire("M1", "base").copie_pour_combat(),
        modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche").copie_pour_combat(),
    ]
    cartes = charger_cartes()
    deck = [cartes[id_carte].copie(exemplaire_module="M1") for id_carte in ids_main]
    combat = Combat(modules, deck, flotte_boss(charger_ennemis()), random.Random(1))
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


def test_une_attaque_arretee_par_le_renvoi_et_le_bouclier_n_affiche_pas_moins_zero(bridge):
    bridge._demarrer_combat(_combat_contre_le_boss(["CRT_7", "CRT_7"]))
    boss = bridge.combat.flotte.ennemis[0]
    boss.statuts.ajouter(bridge.Statut.RENVOI, 1)
    boss.statuts.ajouter(bridge.Statut.BOUCLIER, 50)

    resultat = json.loads(bridge.jouer_carte(0, "AV_M"))

    popup = next(p for p in resultat["popups"] if p["camp"] == "ennemi")
    assert "-0" not in popup["texte"]
    assert "↩ 1" in popup["texte"] and "bloqué" in popup["texte"]


def test_une_reparation_sans_effet_ne_donne_pas_de_popup(bridge):
    bridge._demarrer_combat(_combat_contre_le_boss(["CRT_12", "CRT_12"]))
    assert bridge.combat.vaisseau.principal.pv_combat == bridge.combat.vaisseau.principal.pv_max

    resultat = json.loads(bridge.jouer_carte(0, "base"))

    assert resultat["popups"] == []


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


# --- Outil d'administration : editeur de cartes (specs/outil-editeur-cartes.md) ---


def test_editeur_reference_cartes_du_fichier_et_listes_du_jeu(bridge):
    reference = json.loads(bridge.editeur_reference_web())
    cartes_fichier = json.loads((FICHIER_BRIDGE.parents[2] / "config" / "cartes.json").read_text(encoding="utf-8"))["cartes"]

    assert reference["cartes"] == cartes_fichier
    listes = reference["listes"]
    assert [choix["valeur"] for choix in listes["jouable"]] == ["oui", "non", "supprimee"]
    assert [choix["valeur"] for choix in listes["modules"]] == ["MOD_1", "MOD_2"]
    assert "Ennemi Unique" in [choix["valeur"] for choix in listes["cible"]]
    assert "nature" not in listes  # effets non saisis dans l'outil


def test_editeur_valide_comme_le_jeu_et_donne_l_apercu(bridge):
    cartes = json.loads(bridge.editeur_reference_web())["cartes"]
    cartes[0]["modules"] = ["MOD_9"]
    cartes[1]["jouable"] = True
    cartes[3]["id"] = cartes[2]["id"]

    resultats = json.loads(bridge.editeur_valider_web(json.dumps(cartes)))

    assert resultats[0]["erreurs"] == ["Carte CRT_7 : module inconnu 'MOD_9' (absent de config/modules.json)"]
    assert "jouable doit valoir" in resultats[1]["erreurs"][0]
    assert "utilisé par plusieurs cartes" in resultats[2]["erreurs"][0] and resultats[3]["erreurs"]
    attendu = {"erreurs": [], "apercu": cartes[4]["description"].format(**cartes[4]["valeurs"]), "effets_a_revoir": False}
    assert resultats[4] == attendu


def test_editeur_des_effets_qui_ne_correspondent_plus_ne_bloquent_pas(bridge):
    """Les effets ne se saisissent pas dans l'outil : ils sont ecrits par l'agent d'apres la
    description (decision utilisateur) ; seule la description doit citer des valeurs existantes."""
    cartes = json.loads(bridge.editeur_reference_web())["cartes"]
    laser = cartes[0]
    laser["valeurs"] = {"degats": 6, "brulure": 2}  # nouvelle valeur, citee par aucun effet
    laser["description"] = "Inflige {degats} dégâts et {brulure} d'incendie"
    nouvelle = dict(laser, id="CRT_900", effets=[])
    cartes.append(nouvelle)
    citation_inconnue = dict(laser, id="CRT_901", description="Inflige {inconnu} dégâts")
    cartes.append(citation_inconnue)

    resultats = json.loads(bridge.editeur_valider_web(json.dumps(cartes)))

    assert resultats[0] == {"erreurs": [], "apercu": "Inflige 6 dégâts et 2 d'incendie", "effets_a_revoir": True}
    assert resultats[-2]["erreurs"] == [] and resultats[-2]["effets_a_revoir"]
    assert resultats[-1]["erreurs"] and "inconnu" in resultats[-1]["erreurs"][0]


def test_editeur_exporte_le_fichier_dans_sa_mise_en_forme(bridge):
    cartes = json.loads(bridge.editeur_reference_web())["cartes"]
    cartes[0]["valeurs"]["degats"] = 7

    texte = json.loads(bridge.editeur_exporter_web(json.dumps(cartes)))

    original = (FICHIER_BRIDGE.parents[2] / "config" / "cartes.json").read_text(encoding="utf-8")
    assert texte == original.replace('"valeurs": { "degats": 6 }', '"valeurs": { "degats": 7 }', 1)


def test_est_admin_web(bridge):
    assert json.loads(bridge.est_admin_web("Thomas")) is True
    assert json.loads(bridge.est_admin_web("Paul")) is False
