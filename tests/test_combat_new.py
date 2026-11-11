"""
Tests unitaires pour src/gameplay/combat_new.py (combat de la refonte, specs/refonte-combat.md).

Vaisseau de test : principal M1 (60 PV, base) et Lanceur de missiles M2 (20 PV, avant gauche).
"""

import random

import pytest

from src.gameplay.carte_new import CarteNew, CategorieCarte, CibleCarteNew, Effet, NatureEffet, charger_cartes_new
from src.gameplay.carte import RareteCarte
from src.gameplay.combat_new import CombatNew, EtatCombatNew, NatureEvenement
from src.gameplay.deck_new import deck_de_depart
from src.gameplay.ennemi_new import charger_ennemis_new
from src.gameplay.flotte_new import FlotteNew
from src.gameplay.module_new import charger_modules_new
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.statut_new import Statut

AVANT_GAUCHE = Position(Colonne.AVANT, Rangee.GAUCHE)
AVANT_MID = Position(Colonne.AVANT, Rangee.MID)
AVANT_DROITE = Position(Colonne.AVANT, Rangee.DROITE)
ARRIERE_MID = Position(Colonne.ARRIERE, Rangee.MID)
ARRIERE_DROITE = Position(Colonne.ARRIERE, Rangee.DROITE)
CARTES = charger_cartes_new()


def _ennemi(id_ennemi="ENM_PAT_LE_PIRATE", coefficient=1):
    return charger_ennemis_new()[id_ennemi].pour_combat(coefficient)


def _carte(id_carte, module="M1"):
    return CARTES[id_carte].copie(exemplaire_module=module)


def _combat(ennemis=None, deck=None):
    """Combat de test ; `ennemis` : dict case -> ennemi (Pat le Pirate en avant milieu par defaut)."""
    modeles = charger_modules_new()
    modules = [
        modeles["MOD_1"].nouvel_exemplaire("M1", "base").copie_pour_combat(),
        modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche").copie_pour_combat(),
    ]
    deck = deck if deck is not None else deck_de_depart(CARTES, "M1")
    return CombatNew(modules, deck, FlotteNew(ennemis or {AVANT_MID: _ennemi()}), random.Random(0))


def _en_main(combat, *cartes):
    """Met ces cartes seules en main, pioche et defausse vides."""
    combat.deck.main, combat.deck.pioche, combat.deck.defausse = list(cartes), [], []
    return cartes


def _evenements(combat, nature):
    return [evenement for evenement in combat.journal if evenement.nature == nature]


# --- Debut du combat et du tour (3.1, 3.2) ---


def test_le_combat_commence_au_tour_1_avec_3_electricite_et_5_cartes():
    combat = _combat()

    assert (combat.tour, combat.electricite, combat.etat) == (1, 3, EtatCombatNew.EN_COURS)
    assert (len(combat.deck.main), len(combat.deck.pioche)) == (5, 5)


def test_une_carte_rattachee_a_un_module_absent_est_refusee():
    with pytest.raises(ValueError, match="module absent"):
        _combat(deck=[_carte("CRT_7", "M9")])


def test_fin_de_tour_main_defaussee_puis_nouveau_tour():
    combat = _combat()

    combat.finir_tour()

    assert (combat.tour, combat.electricite, len(combat.deck.main)) == (2, 3, 5)
    assert len(combat.deck.defausse) == 5


# --- Jouer une carte (4) ---


def test_laser_inflige_ses_degats_coute_son_electricite_et_part_en_defausse():
    combat = _combat()
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    pat = combat.flotte.ennemi_en(AVANT_MID)
    assert (pat.pv, combat.electricite, combat.deck.defausse) == (44, 2, [laser])
    (attaque,) = _evenements(combat, NatureEvenement.ATTAQUE)
    assert (attaque.source, attaque.cible, attaque.valeur, attaque.pv_perdus) == (laser, pat, 6, 6)


def test_cibles_possibles_selon_la_cible_de_la_carte():
    combat = _combat()

    assert combat.cibles_possibles(_carte("CRT_7")) == [AVANT_MID]
    assert set(combat.cibles_possibles(_carte("CRT_11"))) == {AVANT_MID, ARRIERE_MID}  # principal
    assert combat.cibles_possibles(_carte("CRT_16")) == []  # Ligne arriere : aucun ennemi a l'arriere


def test_carte_injouable_ou_cible_invalide_refusee():
    combat = _combat()
    laser, laser_lourd = _en_main(combat, _carte("CRT_7"), _carte("CRT_47"))
    combat.electricite = 0

    with pytest.raises(ValueError, match="injouable"):
        combat.jouer_carte(laser, AVANT_MID)
    combat.electricite = 3
    with pytest.raises(ValueError, match="cible invalide"):
        combat.jouer_carte(laser_lourd, AVANT_GAUCHE)
    with pytest.raises(ValueError, match="injouable"):
        combat.jouer_carte(_carte("CRT_7"), AVANT_MID)  # pas en main


def test_une_nature_laissee_pour_plus_tard_rend_la_carte_injouable():
    breche = CarteNew(
        id="TEST", nom="Breche", image="", rarete=RareteCarte.COMMUNE, categorie=CategorieCarte.DEBUFF,
        cible=CibleCarteNew.ENNEMI_UNIQUE, cout=1, description="", valeurs={"vulnerabilite": 100},
        effets=(Effet(NatureEffet.VULNERABILITE, "vulnerabilite"),), exemplaire_module="M1",
    )
    combat = _combat()
    _en_main(combat, breche)

    assert not combat.peut_jouer(breche)


def test_missiles_degats_sur_la_cible_puis_sur_les_autres():
    cible, autre = _ennemi(), _ennemi()
    combat = _combat({AVANT_MID: cible, AVANT_DROITE: autre})
    (missiles,) = _en_main(combat, _carte("CRT_13", "M2"))

    combat.jouer_carte(missiles, AVANT_MID)

    assert (cible.pv, autre.pv) == (35, 44)


def test_torpille_colonne_avant_puis_arriere():
    avant, arriere = _ennemi(), _ennemi()
    combat = _combat({AVANT_MID: avant, ARRIERE_DROITE: arriere})
    (torpille,) = _en_main(combat, _carte("CRT_14", "M2"))

    combat.jouer_carte(torpille, AVANT_MID)

    assert (avant.pv, arriere.pv) == (40, 42)


def test_un_ennemi_sur_deux_cases_n_est_touche_qu_une_fois_par_effet():
    boss = _ennemi("ENM_BOSS_PIRATES")
    combat = _combat({AVANT_MID: boss, ARRIERE_MID: boss})
    (bombardement,) = _en_main(combat, _carte("CRT_9", "M2"))

    combat.jouer_carte(bombardement, ARRIERE_MID)

    assert boss.pv == 144


# --- Lancements, munitions, repetition (4.3) ---


def test_salve_laser_puis_laser_lance_deux_fois():
    combat = _combat()
    salve, laser = _en_main(combat, _carte("CRT_49"), _carte("CRT_7"))

    combat.jouer_carte(salve, AVANT_MID)
    combat.electricite = 3
    combat.jouer_carte(laser, AVANT_MID)

    assert combat.flotte.ennemi_en(AVANT_MID).pv == 38
    assert _evenements(combat, NatureEvenement.REPETITION)[0].valeur == 1


def test_cible_detruite_au_premier_lancement_les_suivants_sont_perdus():
    """Decision utilisateur : la cible est choisie une fois, pas de report sur un autre ennemi."""
    cible, autre = _ennemi(), _ennemi()
    cible.pv = 6
    combat = _combat({AVANT_MID: cible, AVANT_DROITE: autre})
    (laser,) = _en_main(combat, _carte("CRT_7"))
    laser.lancements_actuels = 2

    combat.jouer_carte(laser, AVANT_MID)

    assert cible.est_detruit() and autre.pv == 50


def test_une_munition_par_carte_jouee_meme_lancee_plusieurs_fois():
    combat = _combat()
    combat.vaisseau.principal.subir_degats(30)
    (reparation,) = _en_main(combat, _carte("CRT_12"))
    reparation.lancements_actuels = 2

    combat.jouer_carte(reparation, AVANT_MID)
    assert (combat.vaisseau.principal.pv_combat, reparation.munitions_restantes) == (46, 1)

    combat.deck.main = [combat.deck.defausse.pop()]
    combat.jouer_carte(reparation, AVANT_MID)
    assert combat.deck.epuisees == [reparation]


# --- Statuts poses par les cartes (4.4) ---


def test_bouclier_et_leurre_sur_un_module_incendie_sur_un_ennemi():
    combat = _combat()
    bouclier, leurre, incendiaire = _en_main(combat, _carte("CRT_10"), _carte("CRT_18", "M2"), _carte("CRT_45"))
    combat.electricite = 10

    combat.jouer_carte(bouclier, AVANT_GAUCHE)
    combat.jouer_carte(leurre, AVANT_GAUCHE)
    combat.jouer_carte(incendiaire, AVANT_MID)

    lanceur, pat = combat.vaisseau.module_d_exemplaire("M2"), combat.flotte.ennemi_en(AVANT_MID)
    assert lanceur.statuts.intensites == {Statut.BOUCLIER: 3, Statut.LEURRE: 1}
    assert pat.statuts[Statut.INCENDIE] == 4


def test_l_incendie_frappe_a_la_fin_du_tour_du_joueur_et_peut_gagner_le_combat():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    pat.statuts.ajouter(Statut.INCENDIE, 4)
    pat.pv = 4

    combat.finir_tour()

    assert combat.etat == EtatCombatNew.VICTOIRE
    assert _evenements(combat, NatureEvenement.INCENDIE)[0].pv_perdus == 4


# --- Renvoi (4.5) ---


def test_les_degats_renvoyes_vont_au_module_de_la_carte():
    miroir = _ennemi("ENM_MIROIR")
    combat = _combat({AVANT_MID: miroir})
    miroir.statuts.ajouter(Statut.RENVOI, 5)
    (laser,) = _en_main(combat, _carte("CRT_7", "M2"))

    combat.jouer_carte(laser, AVANT_MID)

    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    assert (miroir.pv, miroir.statuts[Statut.RENVOI], lanceur.pv_combat) == (49, 0, 15)
    assert _evenements(combat, NatureEvenement.RENVOI)[0].cible is lanceur


def test_les_degats_renvoyes_sont_une_attaque_que_le_leurre_annule():
    miroir = _ennemi("ENM_MIROIR")
    combat = _combat({AVANT_MID: miroir})
    miroir.statuts.ajouter(Statut.RENVOI, 5)
    combat.vaisseau.principal.statuts.ajouter(Statut.LEURRE, 1)
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    assert combat.vaisseau.principal.pv_combat == 60


def test_module_de_la_carte_detruit_le_renvoi_va_au_principal():
    miroir = _ennemi("ENM_MIROIR")
    combat = _combat({AVANT_MID: miroir})
    miroir.statuts.ajouter(Statut.RENVOI, 5)
    persistante = _carte("CRT_7", "M2")
    persistante.persistante = True
    _en_main(combat, persistante)
    combat.vaisseau.module_d_exemplaire("M2").subir_degats(20)

    combat.jouer_carte(persistante, AVANT_MID)

    assert combat.vaisseau.principal.pv_combat == 55


def test_carte_dont_le_module_meurt_pendant_qu_elle_est_jouee_part_hors_service():
    miroir = _ennemi("ENM_MIROIR")
    combat = _combat({AVANT_MID: miroir})
    miroir.statuts.ajouter(Statut.RENVOI, 20)
    (laser_lourd,) = _en_main(combat, _carte("CRT_47", "M2"))

    combat.jouer_carte(laser_lourd, AVANT_MID)

    assert combat.vaisseau.module_d_exemplaire("M2").pv_combat == 8
    combat.electricite = 3
    combat.deck.main = [laser_lourd2 := _carte("CRT_47", "M2")]
    combat.jouer_carte(laser_lourd2, AVANT_MID)
    assert combat.vaisseau.module_d_exemplaire("M2").est_detruit()
    assert laser_lourd2 in combat.deck.hors_service and laser_lourd in combat.deck.hors_service


# --- Tour ennemi (5) ---


def test_attaque_au_plus_proche_puis_cycle():
    pat = _ennemi()
    combat = _combat({AVANT_GAUCHE: pat})

    combat.finir_tour()

    assert combat.vaisseau.module_d_exemplaire("M2").pv_combat == 15
    assert combat.vaisseau.principal.pv_combat == 60


def test_les_valeurs_des_ennemis_montent_avec_le_tour():
    combat = _combat()
    for _ in range(3):
        combat.finir_tour()

    assert combat.tour == 4
    assert combat.intentions()[0].effets[0].valeur == 6  # 5, +1 tous les 3 tours


def test_attaque_repetee_cible_choisie_une_fois():
    """Decision utilisateur : si la cible meurt a la premiere attaque, la seconde est perdue."""
    nettoyeur = _ennemi("ENM_LE_NETTOYEUR")
    combat = _combat({AVANT_GAUCHE: nettoyeur})
    combat.vaisseau.module_d_exemplaire("M2").pv_combat = 7

    combat.finir_tour()

    assert combat.vaisseau.module_d_exemplaire("M2").est_detruit()
    assert combat.vaisseau.principal.pv_combat == 60


def test_le_boss_frappe_tous_les_modules_et_se_protege_a_la_troisieme_etape():
    boss = _ennemi("ENM_BOSS_PIRATES")
    combat = _combat({AVANT_MID: boss, ARRIERE_MID: boss})
    for _ in range(3):
        combat.finir_tour()

    assert combat.vaisseau.principal.pv_combat == 45
    assert combat.vaisseau.module_d_exemplaire("M2").pv_combat == 5
    assert boss.statuts[Statut.BOUCLIER] == 10


def test_miroir_pose_un_renvoi_sur_un_allie_de_la_colonne_avant():
    miroir, pat = _ennemi("ENM_MIROIR"), _ennemi()
    combat = _combat({AVANT_MID: pat, ARRIERE_DROITE: miroir})

    combat.finir_tour()

    assert pat.statuts[Statut.RENVOI] == 5 and miroir.statuts[Statut.RENVOI] == 0


def test_le_renvoi_dure_jusqu_au_tour_ennemi_suivant():
    miroir = _ennemi("ENM_MIROIR")
    combat = _combat({AVANT_MID: miroir})
    combat.finir_tour()
    assert miroir.statuts[Statut.RENVOI] == 5  # pose pendant le tour ennemi, protege ce tour-ci

    _en_main(combat)
    combat.finir_tour()
    assert miroir.statuts[Statut.RENVOI] == 5  # retire a la fin du tour du joueur, puis repose


def test_intentions_etape_courante_valeur_du_tour_et_cible_prevue():
    pat = _ennemi()
    combat = _combat({AVANT_GAUCHE: pat})

    (intention,) = combat.intentions()

    assert intention.ennemi is pat
    assert (intention.effets[0].valeur, intention.effets[0].cible_prevue) == (5, combat.vaisseau.module_d_exemplaire("M2"))


# --- Destruction et fin du combat (6, 7) ---


def test_module_detruit_ses_cartes_passent_hors_service():
    pat = _ennemi()
    deck = deck_de_depart(CARTES, "M1") + [_carte("CRT_9", "M2"), _carte("CRT_15", "M2")]
    combat = _combat({AVANT_GAUCHE: pat}, deck=deck)
    combat.vaisseau.module_d_exemplaire("M2").pv_combat = 5

    combat.finir_tour()

    assert sorted(carte.id for carte in combat.deck.hors_service) == ["CRT_15", "CRT_9"]
    assert combat.etat == EtatCombatNew.EN_COURS  # un secondaire detruit n'est pas une defaite
    assert _evenements(combat, NatureEvenement.CARTES_HORS_SERVICE)[0].valeur == 2


def test_principal_detruit_defaite_immediate():
    combat = _combat()
    combat.vaisseau.principal.pv_combat = 5

    combat.finir_tour()

    assert combat.etat == EtatCombatNew.DEFAITE and combat.tour == 1
    with pytest.raises(ValueError, match="termine"):
        combat.finir_tour()


def test_dernier_ennemi_detruit_victoire():
    pat = _ennemi()
    pat.pv = 6
    combat = _combat({AVANT_MID: pat})
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    assert combat.etat == EtatCombatNew.VICTOIRE
    assert combat.ennemis_detruits() == [pat]
    assert [e.nature for e in combat.journal[-2:]] == [NatureEvenement.ENNEMI_DETRUIT, NatureEvenement.VICTOIRE]
