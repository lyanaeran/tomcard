"""
Tests unitaires pour src/gameplay/partie.py (persistance du parcours, specs.md 10.3), avec le
moteur de la refonte (refonte-branchement.md, PR 1).
"""

import json
import random

import pytest

from src.gameplay import partie as partie_module
from src.gameplay.carte_new import charger_cartes_new
from src.gameplay.combat_new import CombatNew, EtatCombatNew
from src.gameplay.deck_new import DECK_DE_DEPART
from src.gameplay.flotte_new import ID_BOSS, NOMBRE_ENNEMIS_ASTEROIDES
from src.gameplay.module_new import charger_modules_new
from src.gameplay.partie import (
    ARGENT_DEPART,
    ARGENT_PAR_ENNEMI_TUE,
    COUT_ACTION_STATION_SERVICE,
    COUT_METTRE_AUX_NORMES,
    DEGATS_ASTEROIDES,
    NIVEAU_MAJ_MAX,
    PV_AMELIORATION,
    PV_REPARATION,
    PV_REPARATION_VAISSEAU,
    STATUT_EN_COURS,
    CartePossedee,
    SauvegardeObsolete,
    abandonner_partie,
    ajouter_carte,
    ameliorer_module,
    ameliorer_module_aventure,
    avancer_niveau,
    combat_aventure_asteroides,
    combat_depuis_partie,
    creer_profil,
    deck_de_la_partie,
    demarrer_aventure_police,
    deplacer_module,
    detourner_aventure_police,
    equiper_module,
    gagner_argent_combat,
    lire_partie,
    lister_profils,
    mettre_a_jour_module,
    modules_de_la_partie,
    nouveau_profil,
    nouvelle_partie,
    partie_depuis_dict,
    partie_depuis_json,
    partie_en_cours,
    partie_vers_dict,
    partie_vers_json,
    payer_mise_aux_normes,
    profil_depuis_json,
    profil_vers_json,
    reparer_principal,
    reparer_vaisseau,
    reporter_combat,
    retirer_carte,
    sauvegarder_partie,
    second_choc_asteroides,
    subir_degats_principal,
    supprimer_profil,
)
from src.gameplay.position import Colonne, Position, Rangee

LANCEUR = charger_modules_new()["MOD_2"]


def _partie_avec_lanceur(graine: int = 1):
    """Nouvelle partie avec le Lanceur equipe (M2, avant gauche) et une carte du Lanceur."""
    partie = nouvelle_partie(random.Random(graine))
    lanceur = equiper_module(partie, LANCEUR)
    ajouter_carte(partie, "CRT_9", lanceur.exemplaire)
    return partie


# --- Serialisation ---


def test_partie_vers_json_puis_depuis_json_garde_tout():
    partie = _partie_avec_lanceur()
    partie.principal.pv = 37
    partie.principal.pv_max = 70
    partie.vaisseau["avant_gauche"].niveau_maj = 2

    relue = partie_depuis_json(partie_vers_json(partie))

    assert partie_vers_dict(relue) == partie_vers_dict(partie)
    assert relue.principal.pv == 37 and relue.principal.principal
    assert relue.vaisseau["avant_gauche"].emplacement == "avant_gauche"
    assert relue.deck[-1] == CartePossedee("CRT_9", "M2")


def test_le_deck_est_sauvegarde_avec_le_module_de_chaque_carte():
    donnees = partie_vers_dict(_partie_avec_lanceur())

    assert donnees["version"] == 2
    assert donnees["deck"][0] == {"id": "CRT_7", "module": "M1"}
    assert donnees["deck"][-1] == {"id": "CRT_9", "module": "M2"}
    assert donnees["vaisseau"]["avant_gauche"] == {
        "module_id": "MOD_2", "exemplaire": "M2", "pv": 20, "pv_max": 20, "niveau_maj": 1,
    }


def test_une_ancienne_sauvegarde_est_abandonnee():
    """Decision 1 (refonte-branchement.md 2) : pas de conversion, la partie est abandonnee."""
    ancienne = {
        "version": 1, "id": "p", "nom": "n", "statut": STATUT_EN_COURS, "graine": 1, "niveau": 3,
        "argent": 10, "deck": ["CRT_7"],
        "vaisseau": {"base": {"module_id": "MOD_1", "pv": 60, "pv_max": 60, "niveau_maj": 1}},
    }

    with pytest.raises(SauvegardeObsolete):
        partie_depuis_dict(ancienne)
    assert lire_partie(json.dumps(ancienne)) is None
    assert lire_partie(partie_vers_json(nouvelle_partie(random.Random(1)))) is not None


def test_profil_vers_json_puis_depuis_json_roundtrip():
    profil = nouveau_profil("Alice")

    assert profil_depuis_json(profil_vers_json(profil)) == profil


# --- Creation ---


def test_nouvelle_partie_commence_au_niveau_1_avec_seulement_le_principal():
    partie = nouvelle_partie(random.Random(1))

    assert partie.niveau == 1
    assert partie.argent == ARGENT_DEPART
    assert partie.statut == STATUT_EN_COURS
    assert partie.principal.id == "MOD_1" and partie.principal.exemplaire == "M1"
    assert partie.principal.pv == partie.principal.pv_max == charger_modules_new()["MOD_1"].pv_max_base
    assert all(partie.vaisseau[position] is None for position in partie.vaisseau if position != "base")


def test_nouvelle_partie_deck_de_depart_rattache_au_principal():
    partie = nouvelle_partie(random.Random(1))

    assert sorted(carte.id for carte in partie.deck) == sorted(
        id_carte for id_carte, nombre in DECK_DE_DEPART.items() for _ in range(nombre)
    )
    assert {carte.module for carte in partie.deck} == {"M1"}


def test_deck_de_la_partie_donne_des_exemplaires_rattaches():
    cartes = deck_de_la_partie(_partie_avec_lanceur())

    assert cartes[-1].id == "CRT_9" and cartes[-1].exemplaire_module == "M2"
    assert cartes[0].exemplaire_module == "M1"
    assert len({id(carte) for carte in cartes}) == len(cartes)


def test_deux_appels_a_nouvelle_partie_ont_des_graines_et_ids_differents():
    partie_1 = nouvelle_partie(random.Random(1))
    partie_2 = nouvelle_partie(random.Random(2))

    assert partie_1.id != partie_2.id
    assert partie_1.graine != partie_2.graine


def test_equiper_module_cree_un_exemplaire_sur_le_premier_emplacement_libre():
    partie = nouvelle_partie(random.Random(1))

    premier = equiper_module(partie, LANCEUR)
    second = equiper_module(partie, LANCEUR)

    assert (premier.exemplaire, premier.emplacement) == ("M2", "avant_gauche")
    assert (second.exemplaire, second.emplacement) == ("M3", "avant_droite")
    assert partie.vaisseau["avant_droite"] is second
    assert premier.pv == premier.pv_max == LANCEUR.pv_max_base
    assert LANCEUR.exemplaire is None  # le modele n'est pas modifie


def test_ajouter_carte_refuse_un_module_absent():
    partie = nouvelle_partie(random.Random(1))

    with pytest.raises(ValueError, match="M2"):
        ajouter_carte(partie, "CRT_9", "M2")


def test_avancer_niveau_incremente():
    partie = nouvelle_partie(random.Random(1))

    avancer_niveau(partie)

    assert partie.niveau == 2


def test_modules_de_la_partie_principal_en_premier():
    partie = nouvelle_partie(random.Random(1))
    partie.vaisseau["arriere_droite"] = LANCEUR.nouvel_exemplaire("M2", "arriere_droite")

    assert [module.exemplaire for module in modules_de_la_partie(partie)] == ["M1", "M2"]


# --- Combat ---


def test_combat_depuis_partie_reprend_le_vaisseau_et_le_deck_de_la_partie():
    partie = _partie_avec_lanceur()
    partie.principal.pv = 33
    partie.vaisseau["avant_gauche"].pv_max = 30
    partie.niveau = 3

    combat = combat_depuis_partie(partie, random.Random(1))

    assert isinstance(combat, CombatNew)
    assert combat.vaisseau.principal.pv_combat == 33
    # Un secondaire repart a ses PV max (ameliorations comprises)
    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    assert lanceur.pv_combat == 30 and lanceur.emplacement == "avant_gauche"
    assert len(combat.deck.toutes_les_cartes()) == len(partie.deck)
    # Copies : la partie n'est pas touchee par le combat
    assert combat.vaisseau.principal is not partie.principal


@pytest.mark.parametrize("niveau, nombre", [(2, 1), (5, 1), (6, 2), (9, 2)])
def test_flotte_prime_selon_le_niveau(niveau, nombre):
    partie = _partie_avec_lanceur()
    partie.niveau = niveau

    for graine in range(5):
        combat = combat_depuis_partie(partie, random.Random(graine))
        assert len(combat.flotte.ennemis) == nombre
        assert all(ennemi.emplacements == 1 and ennemi.coefficient == 1 for ennemi in combat.flotte.ennemis)


def test_flotte_du_boss_au_niveau_10():
    partie = _partie_avec_lanceur()
    partie.niveau = 10

    combat = combat_depuis_partie(partie, random.Random(1))

    (boss,) = combat.flotte.ennemis
    assert boss.id == ID_BOSS
    assert combat.flotte.cases_de(boss) == [Position(Colonne.AVANT, Rangee.MID), Position(Colonne.ARRIERE, Rangee.MID)]


def test_combat_aventure_asteroides_a_trois_ennemis_places_selon_leur_preference():
    partie = _partie_avec_lanceur()

    for graine in range(30):
        combat = combat_aventure_asteroides(partie, random.Random(graine))
        assert len(combat.flotte.ennemis) == NOMBRE_ENNEMIS_ASTEROIDES
        for ennemi in combat.flotte.ennemis:
            colonne = combat.flotte.cases_de(ennemi)[0].colonne
            if ennemi.id == "ENM_PETIT_JEAN":
                assert colonne == Colonne.AVANT
            if ennemi.id == "ENM_LE_NETTOYEUR":
                assert colonne == Colonne.ARRIERE


def _gagner(combat: CombatNew) -> None:
    """Detruit tous les ennemis (fin de combat simulee, sans jouer de cartes)."""
    for ennemi in combat.flotte.ennemis:
        ennemi.pv = 0
    combat.etat = EtatCombatNew.VICTOIRE


def test_reporter_combat_reporte_seulement_les_pv_du_principal():
    partie = _partie_avec_lanceur()
    combat = combat_depuis_partie(partie, random.Random(1))
    combat.vaisseau.principal.pv_combat = 41
    combat.vaisseau.module_d_exemplaire("M2").pv_combat = 3

    reporter_combat(partie, combat)

    assert partie.principal.pv == 41
    assert partie.vaisseau["avant_gauche"].pv == partie.vaisseau["avant_gauche"].pv_max


def test_gagner_argent_combat_par_ennemi_detruit():
    partie = _partie_avec_lanceur()
    partie.niveau = 7
    combat = combat_depuis_partie(partie, random.Random(1))
    _gagner(combat)

    gagner_argent_combat(partie, combat)

    assert partie.argent == ARGENT_DEPART + 2 * ARGENT_PAR_ENNEMI_TUE


def test_le_boss_rapporte_l_argent_d_un_seul_ennemi():
    partie = _partie_avec_lanceur()
    partie.niveau = 10
    combat = combat_depuis_partie(partie, random.Random(1))
    _gagner(combat)

    gagner_argent_combat(partie, combat)

    assert partie.argent == ARGENT_DEPART + ARGENT_PAR_ENNEMI_TUE


# --- Station service (decision 2 : Reparer ne vise que le principal) ---


def test_reparer_principal_restaure_les_pv_plafonne_au_max():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = 100
    partie.principal.pv = 10

    assert reparer_principal(partie) is True
    assert partie.principal.pv == 10 + PV_REPARATION
    assert partie.argent == 100 - COUT_ACTION_STATION_SERVICE

    partie.principal.pv = partie.principal.pv_max - 1
    reparer_principal(partie)
    assert partie.principal.pv == partie.principal.pv_max


def test_action_station_service_refusee_si_argent_insuffisant():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = COUT_ACTION_STATION_SERVICE - 1
    partie.principal.pv = 10

    assert reparer_principal(partie) is False
    assert ameliorer_module(partie, "base") is False
    assert partie.principal.pv == 10
    assert partie.argent == COUT_ACTION_STATION_SERVICE - 1


def test_ameliorer_module_augmente_pv_max_et_pv_du_principal_comme_d_un_secondaire():
    partie = _partie_avec_lanceur()
    partie.argent = 100
    partie.principal.pv = 30
    pv_max_principal = partie.principal.pv_max

    assert ameliorer_module(partie, "base") and ameliorer_module(partie, "avant_gauche")

    assert (partie.principal.pv, partie.principal.pv_max) == (30 + PV_AMELIORATION, pv_max_principal + PV_AMELIORATION)
    lanceur = partie.vaisseau["avant_gauche"]
    assert lanceur.pv == lanceur.pv_max == LANCEUR.pv_max_base + PV_AMELIORATION


def test_mettre_a_jour_module_incremente_puis_plafonne():
    partie = _partie_avec_lanceur()
    partie.argent = 1000

    for _ in range(NIVEAU_MAJ_MAX + 1):
        mettre_a_jour_module(partie, "avant_gauche")

    assert partie.vaisseau["avant_gauche"].niveau_maj == NIVEAU_MAJ_MAX


def test_deplacer_module_met_a_jour_l_emplacement_et_garde_les_cartes_rattachees():
    partie = _partie_avec_lanceur()
    partie.argent = 100
    second = equiper_module(partie, LANCEUR)  # M3, avant droite

    assert deplacer_module(partie, "avant_gauche", "arriere_droite")
    assert deplacer_module(partie, "arriere_droite", "avant_droite")

    assert partie.vaisseau["avant_gauche"] is None
    assert partie.vaisseau["avant_droite"].exemplaire == "M2"
    assert partie.vaisseau["avant_droite"].emplacement == "avant_droite"
    assert partie.vaisseau["arriere_droite"] is second and second.emplacement == "arriere_droite"
    assert partie.deck[-1] == CartePossedee("CRT_9", "M2")
    # Le combat suivant place bien chaque module a son nouvel emplacement
    combat = combat_depuis_partie(partie, random.Random(1))
    assert combat.vaisseau.module_en(Position(Colonne.AVANT, Rangee.DROITE)).exemplaire == "M2"


def test_deplacer_le_principal_est_refuse():
    partie = _partie_avec_lanceur()
    partie.argent = 100

    with pytest.raises(ValueError):
        deplacer_module(partie, "base", "avant_droite")
    assert partie.argent == 100


# --- Aventures (decision 3 : les PV hors combat ne concernent que le principal) ---


def test_reparer_vaisseau_soigne_le_principal_plafonne_au_max():
    partie = _partie_avec_lanceur()
    partie.principal.pv = 10

    reparer_vaisseau(partie)
    assert partie.principal.pv == 10 + PV_REPARATION_VAISSEAU

    partie.principal.pv = partie.principal.pv_max - 1
    reparer_vaisseau(partie)
    assert partie.principal.pv == partie.principal.pv_max


def test_ameliorer_module_aventure_est_gratuit():
    partie = _partie_avec_lanceur()
    argent = partie.argent

    ameliorer_module_aventure(partie, "avant_gauche")

    assert partie.vaisseau["avant_gauche"].pv_max == LANCEUR.pv_max_base + PV_AMELIORATION
    assert partie.argent == argent


def test_retirer_carte_retire_un_seul_exemplaire_de_ce_module():
    partie = _partie_avec_lanceur()
    nombre_lasers = sum(carte.id == "CRT_7" for carte in partie.deck)

    retirer_carte(partie, CartePossedee("CRT_7", "M1"))

    assert sum(carte.id == "CRT_7" for carte in partie.deck) == nombre_lasers - 1


def test_subir_degats_principal_plafonne_a_0():
    partie = _partie_avec_lanceur()
    partie.principal.pv = 3

    subir_degats_principal(partie, DEGATS_ASTEROIDES)

    assert partie.principal.pv == 0
    assert partie.vaisseau["avant_gauche"].pv == partie.vaisseau["avant_gauche"].pv_max


def test_second_choc_asteroides_touche_le_principal_et_offre_une_carte_rattachee_au_principal():
    partie = _partie_avec_lanceur()
    pv = partie.principal.pv

    carte = second_choc_asteroides(partie, charger_cartes_new(), random.Random(1))

    assert partie.principal.pv == pv - DEGATS_ASTEROIDES
    assert carte is not None and carte.exemplaire_module == "M1"


def test_second_choc_asteroides_n_offre_aucune_carte_si_le_pool_est_vide():
    partie = _partie_avec_lanceur()

    assert second_choc_asteroides(partie, {}, random.Random(1)) is None


def test_payer_mise_aux_normes():
    partie = nouvelle_partie(random.Random(1))
    partie.argent = COUT_METTRE_AUX_NORMES

    assert payer_mise_aux_normes(partie) is True
    assert partie.argent == 0
    assert payer_mise_aux_normes(partie) is False
    assert partie.argent == 0


def test_aventure_police_tire_une_carte_du_deck_puis_detourner_une_seule_fois():
    partie = _partie_avec_lanceur()

    etat = demarrer_aventure_police(partie, random.Random(1))
    assert etat.carte_actuelle in partie.deck and etat.detourner_disponible

    assert detourner_aventure_police(etat, partie, random.Random(2)) is True
    carte = etat.carte_actuelle
    assert carte in partie.deck and not etat.detourner_disponible

    assert detourner_aventure_police(etat, partie, random.Random(3)) is False
    assert etat.carte_actuelle == carte


# --- I/O fichier (PC) ---


@pytest.fixture
def dossier_saves_isole(tmp_path, monkeypatch):
    monkeypatch.setattr(partie_module, "DOSSIER_SAVES", tmp_path / "saves")
    return tmp_path / "saves"


def test_lister_profils_vide_si_aucun_dossier(dossier_saves_isole):
    assert lister_profils() == []


def test_creer_profil_puis_le_retrouver_dans_lister_profils(dossier_saves_isole):
    creer_profil("Bob")
    creer_profil("Alice")

    noms = [profil.nom for profil in lister_profils()]

    assert noms == ["Alice", "Bob"]  # trie par nom


def test_supprimer_profil_le_retire_de_lister_profils(dossier_saves_isole):
    bob = creer_profil("Bob")
    creer_profil("Alice")

    supprimer_profil(bob.id)

    noms = [profil.nom for profil in lister_profils()]
    assert noms == ["Alice"]


def test_supprimer_profil_efface_aussi_ses_parties_sauvegardees(dossier_saves_isole):
    profil = creer_profil("Alice")
    sauvegarder_partie(profil.id, nouvelle_partie(random.Random(1)))
    assert partie_en_cours(profil.id) is not None

    supprimer_profil(profil.id)

    assert not (dossier_saves_isole / profil.id).exists()


def test_supprimer_profil_inexistant_ne_leve_pas(dossier_saves_isole):
    supprimer_profil("joueur_inexistant")  # ne doit pas lever, cf. docstring


def test_partie_en_cours_renvoie_none_si_aucune_partie(dossier_saves_isole):
    profil = creer_profil("Alice")

    assert partie_en_cours(profil.id) is None


def test_sauvegarder_partie_puis_la_retrouver_en_cours(dossier_saves_isole):
    profil = creer_profil("Alice")
    partie = nouvelle_partie(random.Random(1))

    sauvegarder_partie(profil.id, partie)

    retrouvee = partie_en_cours(profil.id)
    assert retrouvee is not None
    assert retrouvee.id == partie.id
    assert retrouvee.statut == STATUT_EN_COURS


def test_partie_en_cours_efface_une_ancienne_sauvegarde_et_garde_le_profil(dossier_saves_isole):
    profil = creer_profil("Alice")
    dossier = dossier_saves_isole / profil.id / "parties"
    dossier.mkdir(parents=True)
    ancienne = dossier / "partie_ancienne.json"
    ancienne.write_text(json.dumps({"version": 1, "id": "partie_ancienne", "statut": STATUT_EN_COURS}))

    assert partie_en_cours(profil.id) is None
    assert not ancienne.exists()
    assert [p.nom for p in lister_profils()] == ["Alice"]


def test_abandonner_partie_la_marque_terminee(dossier_saves_isole):
    profil = creer_profil("Alice")
    partie = nouvelle_partie(random.Random(1))
    sauvegarder_partie(profil.id, partie)

    abandonner_partie(profil.id, partie)

    assert partie_en_cours(profil.id) is None
