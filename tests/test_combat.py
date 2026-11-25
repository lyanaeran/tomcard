"""
Tests unitaires pour src/gameplay/combat.py (combat de la refonte, specs.md 3).

Vaisseau de test : principal M1 (60 PV, base) et Lanceur de missiles M2 (20 PV, avant gauche).
"""

import random

import pytest

from src.gameplay.carte import Carte, CategorieCarte, CibleCarte, Effet, NatureEffet, charger_cartes
from src.gameplay.carte import RareteCarte
from src.gameplay.combat import Combat, EtatCombat, NatureEvenement
from src.gameplay.deck import deck_de_depart
from src.gameplay.ennemi import charger_ennemis
from src.gameplay.flotte import Flotte
from src.gameplay.module import charger_modules
from src.gameplay.position import Ligne, Position, Colonne
from src.gameplay.statut import Statut

AVANT_GAUCHE = Position(Ligne.AVANT, Colonne.GAUCHE)
AVANT_MID = Position(Ligne.AVANT, Colonne.MID)
AVANT_DROITE = Position(Ligne.AVANT, Colonne.DROITE)
ARRIERE_MID = Position(Ligne.ARRIERE, Colonne.MID)
ARRIERE_DROITE = Position(Ligne.ARRIERE, Colonne.DROITE)
CARTES = charger_cartes()
# Valeur de la carte Bouclier (CRT_10), lue dans config/cartes.json pour suivre les reglages
BOUCLIER_CARTE = CARTES["CRT_10"].valeurs["bouclier"]


def _ennemi(id_ennemi="ENM_PAT_LE_PIRATE", coefficient=1):
    return charger_ennemis()[id_ennemi].pour_combat(coefficient)


def _ennemis_une_case():
    """Un exemplaire de combat de chaque ennemi sur une seule case."""
    return [modele.pour_combat() for modele in charger_ennemis().values() if modele.emplacements == 1]


def _carte(id_carte, module="M1"):
    return CARTES[id_carte].copie(exemplaire_module=module)


def _combat(ennemis=None, deck=None):
    """Combat de test ; `ennemis` : dict case -> ennemi (Pat le Pirate en avant milieu par defaut)."""
    modeles = charger_modules()
    modules = [
        modeles["MOD_1"].nouvel_exemplaire("M1", "base").copie_pour_combat(),
        modeles["MOD_2"].nouvel_exemplaire("M2", "avant_gauche").copie_pour_combat(),
    ]
    deck = deck if deck is not None else deck_de_depart(CARTES, "M1")
    return Combat(modules, deck, Flotte(ennemis or {AVANT_MID: _ennemi()}), random.Random(0))


def _en_main(combat, *cartes):
    """Met ces cartes seules en main, pioche et defausse vides."""
    combat.deck.main, combat.deck.pioche, combat.deck.defausse = list(cartes), [], []
    return cartes


def _evenements(combat, nature):
    return [evenement for evenement in combat.journal if evenement.nature == nature]


# --- Debut du combat et du tour (3.1, 3.2) ---


def test_le_combat_commence_au_tour_1_avec_3_electricite_et_5_cartes():
    combat = _combat()

    assert (combat.tour, combat.electricite, combat.etat) == (1, 3, EtatCombat.EN_COURS)
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
    assert (attaque.source, attaque.cible, attaque.valeur, attaque.pv_perdus, attaque.pv_restants) == (laser, pat, 6, 6, 44)


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
    breche = Carte(
        id="TEST", nom="Breche", image="", rarete=RareteCarte.COMMUNE, categorie=CategorieCarte.DEBUFF,
        cible=CibleCarte.ENNEMI_UNIQUE, cout=1, description="", valeurs={"vulnerabilite": 100},
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


def test_torpille_ligne_avant_puis_arriere():
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

    assert boss.pv == boss.pv_max - CARTES["CRT_9"].valeurs["degats"]


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
    assert lanceur.statuts.intensites == {Statut.BOUCLIER: BOUCLIER_CARTE, Statut.LEURRE: 1}
    assert pat.statuts[Statut.INCENDIE] == 4


def test_l_incendie_frappe_a_la_fin_du_tour_du_joueur_et_peut_gagner_le_combat():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    pat.statuts.ajouter(Statut.INCENDIE, 4)
    pat.pv = 4

    combat.finir_tour()

    assert combat.etat == EtatCombat.VICTOIRE
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

    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    assert lanceur.pv_combat == lanceur.pv_max - CARTES["CRT_47"].valeurs["degats"]
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


def test_miroir_pose_un_renvoi_sur_un_allie_de_la_ligne_avant():
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


def test_modules_vises_proximite_tous_et_aucun():
    pat = _ennemi()
    combat = _combat({AVANT_GAUCHE: pat})
    (intention,) = combat.intentions()
    assert combat.modules_vises(intention.effets[0]) == [combat.vaisseau.module_d_exemplaire("M2")]

    for ennemi in _ennemis_une_case():
        combat = _combat({AVANT_GAUCHE: ennemi})
        for effet in combat.intentions()[0].effets:
            vises = combat.modules_vises(effet)
            if effet.effet.cible.name == "TOUS_MODULES":
                assert vises == combat.vaisseau.modules_vivants()
            elif effet.effet.cible.name == "PROXIMITE":
                assert vises == [effet.cible_prevue]
            else:
                assert vises == []


# --- Destruction et fin du combat (6, 7) ---


def test_module_detruit_ses_cartes_passent_hors_service():
    pat = _ennemi()
    deck = deck_de_depart(CARTES, "M1") + [_carte("CRT_9", "M2"), _carte("CRT_15", "M2")]
    combat = _combat({AVANT_GAUCHE: pat}, deck=deck)
    combat.vaisseau.module_d_exemplaire("M2").pv_combat = 5

    combat.finir_tour()

    assert sorted(carte.id for carte in combat.deck.hors_service) == ["CRT_15", "CRT_9"]
    assert combat.etat == EtatCombat.EN_COURS  # un secondaire detruit n'est pas une defaite
    assert _evenements(combat, NatureEvenement.CARTES_HORS_SERVICE)[0].valeur == 2


def test_principal_detruit_defaite_immediate():
    combat = _combat()
    combat.vaisseau.principal.pv_combat = 5

    combat.finir_tour()

    assert combat.etat == EtatCombat.DEFAITE and combat.tour == 1
    with pytest.raises(ValueError, match="termine"):
        combat.finir_tour()


def test_dernier_ennemi_detruit_victoire():
    pat = _ennemi()
    pat.pv = 6
    combat = _combat({AVANT_MID: pat})
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    assert combat.etat == EtatCombat.VICTOIRE
    assert combat.ennemis_detruits() == [pat]
    assert [e.nature for e in combat.journal[-2:]] == [NatureEvenement.ENNEMI_DETRUIT, NatureEvenement.VICTOIRE]


# --- Journal detaille (degats absorbes, PV perdus et restants) ---


def test_journal_d_une_attaque_ennemie_bouclier_puis_pv():
    pat = _ennemi()
    combat = _combat({AVANT_GAUCHE: pat})
    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    lanceur.statuts.ajouter(Statut.BOUCLIER, 3)

    combat.finir_tour()

    (attaque,) = _evenements(combat, NatureEvenement.ATTAQUE)
    assert (attaque.source, attaque.cible) == (pat, lanceur)
    assert (attaque.valeur, attaque.absorbes_bouclier, attaque.annules_leurre, attaque.renvoyes) == (5, 3, 0, 0)
    assert (attaque.pv_perdus, attaque.pv_restants) == (2, 18)


def test_journal_d_une_attaque_annulee_par_le_leurre():
    combat = _combat({AVANT_GAUCHE: _ennemi()})
    combat.vaisseau.module_d_exemplaire("M2").statuts.ajouter(Statut.LEURRE, 1)

    combat.finir_tour()

    (attaque,) = _evenements(combat, NatureEvenement.ATTAQUE)
    assert (attaque.annules_leurre, attaque.pv_perdus, attaque.pv_restants) == (5, 0, 20)


def test_journal_du_renvoi_et_de_ses_degats():
    miroir = _ennemi("ENM_MIROIR")
    combat = _combat({AVANT_MID: miroir})
    miroir.statuts.ajouter(Statut.RENVOI, 5)
    miroir.statuts.ajouter(Statut.BOUCLIER, 2)
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    (attaque,) = _evenements(combat, NatureEvenement.ATTAQUE)
    assert (attaque.renvoyes, attaque.absorbes_bouclier, attaque.pv_perdus, attaque.pv_restants) == (5, 1, 0, 50)
    (renvoi,) = _evenements(combat, NatureEvenement.RENVOI)
    assert (renvoi.source, renvoi.cible, renvoi.valeur, renvoi.pv_perdus, renvoi.pv_restants) == (
        miroir, combat.vaisseau.principal, 5, 5, 55,
    )


def test_journal_de_l_incendie_absorbe_par_le_bouclier():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    pat.statuts.ajouter(Statut.INCENDIE, 4)
    pat.statuts.ajouter(Statut.BOUCLIER, 1)

    combat.finir_tour()

    (incendie,) = _evenements(combat, NatureEvenement.INCENDIE)
    assert (incendie.valeur, incendie.absorbes_bouclier, incendie.pv_perdus, incendie.pv_restants) == (4, 1, 3, 47)


def test_journal_pv_perdus_plafonnes_par_les_pv_restants():
    pat = _ennemi()
    pat.pv = 4
    pat2 = _ennemi()
    combat = _combat({AVANT_MID: pat, AVANT_DROITE: pat2})
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    (attaque,) = _evenements(combat, NatureEvenement.ATTAQUE)
    assert (attaque.valeur, attaque.pv_perdus, attaque.pv_restants) == (6, 4, 0)


# --- Lancements multiples : un seul cout, tous les effets a chaque lancement (4.3) ---


def test_carte_lancee_deux_fois_un_seul_cout_et_effets_a_chaque_lancement():
    combat = _combat()
    laser, bouclier = _en_main(combat, _carte("CRT_47"), _carte("CRT_10"))
    laser.lancements_actuels = bouclier.lancements_actuels = 2

    combat.jouer_carte(laser, AVANT_MID)
    combat.jouer_carte(bouclier, AVANT_MID)

    assert combat.electricite == 3 - laser.cout - bouclier.cout
    ennemi = combat.flotte.ennemi_en(AVANT_MID)
    assert ennemi.pv == ennemi.pv_max - 2 * laser.valeurs["degats"]
    assert combat.vaisseau.principal.statuts[Statut.BOUCLIER] == 2 * BOUCLIER_CARTE


def test_pioche_et_gain_d_electricite_a_chaque_lancement():
    boost = Carte(
        id="TEST", nom="Boost", image="", rarete=RareteCarte.COMMUNE, categorie=CategorieCarte.OUTILS,
        cible=CibleCarte.MODULE_PRINCIPAL, cout=1, description="", valeurs={"pioche": 1, "electricite": 1},
        effets=(Effet(NatureEffet.PIOCHE, "pioche"), Effet(NatureEffet.GAIN_ELECTRICITE, "electricite")),
        exemplaire_module="M1", lancements_actuels=2,
    )
    combat = _combat()
    _en_main(combat, boost)
    combat.deck.pioche = [_carte("CRT_7"), _carte("CRT_7"), _carte("CRT_7")]

    combat.jouer_carte(boost, AVANT_MID)

    assert (len(combat.deck.main), len(combat.deck.pioche)) == (2, 1)
    assert combat.electricite == 4  # 3 - 1 + 1 + 1


# --- Corrections de la review de la PR #61 ---


def test_le_combat_ne_modifie_pas_les_cartes_du_deck_de_la_partie():
    deck = deck_de_depart(CARTES, "M1")
    combat = _combat(deck=deck)
    reparation = next(carte for carte in combat.deck.toutes_les_cartes() if carte.id == "CRT_12")
    combat.deck.main = [reparation]

    combat.jouer_carte(reparation, AVANT_MID)

    assert not any(carte is originale for carte in combat.deck.toutes_les_cartes() for originale in deck)
    assert next(carte for carte in deck if carte.id == "CRT_12").munitions_restantes == 2
    assert reparation.munitions_restantes == 1


def test_un_module_detruit_perd_ses_statuts():
    combat = _combat({AVANT_GAUCHE: _ennemi()})
    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    lanceur.pv_combat = 1
    lanceur.statuts.ajouter(Statut.INCENDIE, 3)

    combat.finir_tour()

    assert lanceur.est_detruit() and lanceur.statuts.intensites == {}


def test_un_ennemi_detruit_pendant_son_etape_ne_joue_pas_la_suite():
    jean = _ennemi("ENM_PETIT_JEAN")
    jean.pv = 2
    combat = _combat({AVANT_GAUCHE: jean})
    combat.vaisseau.module_d_exemplaire("M2").statuts.ajouter(Statut.RENVOI, 10)

    combat.finir_tour()

    assert jean.est_detruit() and combat.etat == EtatCombat.VICTOIRE
    assert not _evenements(combat, NatureEvenement.STATUT_POSE)  # son bouclier n'est pas pose



def test_remplacer_aleatoire_change_aussi_les_melanges_du_deck():
    combat = _combat()
    nouveau = random.Random(42)

    combat.remplacer_aleatoire(nouveau)

    assert combat.aleatoire is nouveau and combat.deck.aleatoire is nouveau


# --- Lot 2 du plan des cartes : portees vers un module, meme colonne, renvoi, retrait de bouclier ---


def _valeur(id_carte, nom):
    return CARTES[id_carte].valeurs[nom]


def test_missile_de_couverture_degats_a_l_ennemi_et_bouclier_au_principal():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    (couverture,) = _en_main(combat, _carte("CRT_54", "M2"))

    combat.jouer_carte(couverture, AVANT_MID)

    assert pat.pv == pat.pv_max - _valeur("CRT_54", "degats")
    assert combat.vaisseau.principal.statuts[Statut.BOUCLIER] == _valeur("CRT_54", "bouclier")
    assert combat.vaisseau.module_d_exemplaire("M2").statuts[Statut.BOUCLIER] == 0


def test_torpille_de_barrage_bouclier_au_module_de_la_carte():
    pat, pat2 = _ennemi(), _ennemi()
    combat = _combat({AVANT_MID: pat, AVANT_GAUCHE: pat2})
    (barrage,) = _en_main(combat, _carte("CRT_62", "M2"))

    combat.jouer_carte(barrage, AVANT_MID)

    assert pat.pv == pat2.pv == pat.pv_max - _valeur("CRT_62", "degats")
    assert combat.vaisseau.module_d_exemplaire("M2").statuts[Statut.BOUCLIER] == _valeur("CRT_62", "bouclier")
    assert combat.vaisseau.principal.statuts[Statut.BOUCLIER] == 0


def test_portee_module_de_la_carte_va_au_principal_si_le_module_est_detruit():
    combat = _combat()
    barrage = _carte("CRT_62", "M2")
    barrage.persistante = True
    _en_main(combat, barrage)
    combat.vaisseau.module_d_exemplaire("M2").subir_degats(20)

    combat.jouer_carte(barrage, AVANT_MID)

    assert combat.vaisseau.principal.statuts[Statut.BOUCLIER] == _valeur("CRT_62", "bouclier")


def test_torpille_traversante_touche_aussi_l_ennemi_de_la_meme_colonne():
    devant, derriere, voisin = _ennemi(), _ennemi("ENM_LE_PUZZLE"), _ennemi()
    combat = _combat({AVANT_MID: devant, ARRIERE_MID: derriere, AVANT_DROITE: voisin})
    (traversante,) = _en_main(combat, _carte("CRT_61", "M2"))

    combat.jouer_carte(traversante, AVANT_MID)

    assert devant.pv == devant.pv_max - _valeur("CRT_61", "degats_cible")
    assert derriere.pv == derriere.pv_max - _valeur("CRT_61", "degats_colonne")
    assert voisin.pv == voisin.pv_max


def test_torpille_traversante_depuis_l_arriere_touche_l_ennemi_de_devant():
    devant, derriere = _ennemi(), _ennemi("ENM_LE_PUZZLE")
    combat = _combat({AVANT_MID: devant, ARRIERE_MID: derriere})
    (traversante,) = _en_main(combat, _carte("CRT_61", "M2"))

    combat.jouer_carte(traversante, ARRIERE_MID)

    assert derriere.pv == derriere.pv_max - _valeur("CRT_61", "degats_cible")
    assert devant.pv == devant.pv_max - _valeur("CRT_61", "degats_colonne")


def test_torpille_traversante_sans_personne_dans_la_colonne():
    seul = _ennemi()
    combat = _combat({AVANT_DROITE: seul})
    (traversante,) = _en_main(combat, _carte("CRT_61", "M2"))

    combat.jouer_carte(traversante, AVANT_DROITE)

    assert seul.pv == seul.pv_max - _valeur("CRT_61", "degats_cible")


def test_torpille_traversante_ne_touche_le_boss_qu_une_fois():
    # Le Boss occupe les deux cases de sa colonne
    boss = _ennemi("ENM_BOSS_PIRATES")
    combat = _combat({AVANT_MID: boss, ARRIERE_MID: boss})
    (traversante,) = _en_main(combat, _carte("CRT_61", "M2"))
    combat.jouer_carte(traversante, AVANT_MID)
    assert boss.pv == boss.pv_max - _valeur("CRT_61", "degats_cible")


def test_bouclier_reflechissant_renvoie_l_attaque_ennemie_a_l_attaquant():
    pat = _ennemi()
    combat = _combat({AVANT_GAUCHE: pat})  # Pat vise le Lanceur (avant gauche)
    (reflechissant,) = _en_main(combat, _carte("CRT_90"))
    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    attaque = combat.intentions()[0].effets[0].valeur
    renvoi = _valeur("CRT_90", "renvoi")

    combat.jouer_carte(reflechissant, AVANT_GAUCHE)
    assert lanceur.statuts[Statut.RENVOI] == renvoi
    combat.finir_tour()

    assert pat.pv == pat.pv_max - min(attaque, renvoi)
    assert lanceur.pv_combat == lanceur.pv_max - max(0, attaque - renvoi)
    assert _evenements(combat, NatureEvenement.RENVOI)[0].cible is pat


def test_le_renvoi_pose_par_une_carte_disparait_a_la_fin_du_tour_ennemi():
    combat = _combat({AVANT_GAUCHE: _ennemi()})  # Pat vise le Lanceur, pas le principal
    (riposte,) = _en_main(combat, _carte("CRT_107"))

    combat.jouer_carte(riposte, AVANT_MID)
    principal = combat.vaisseau.principal
    assert principal.statuts[Statut.RENVOI] == _valeur("CRT_107", "renvoi")
    combat.finir_tour()

    assert principal.statuts[Statut.RENVOI] == 0
    assert principal.statuts[Statut.BOUCLIER] == _valeur("CRT_107", "bouclier") - 1


def test_bouclier_miroir_pose_le_renvoi_sur_tous_les_modules():
    combat = _combat()
    (miroir,) = _en_main(combat, _carte("CRT_102"))

    combat.jouer_carte(miroir, AVANT_MID)

    assert all(module.statuts[Statut.RENVOI] == _valeur("CRT_102", "renvoi") for module in combat.vaisseau.modules)


def test_laser_disrupteur_retire_le_bouclier_puis_inflige_ses_degats():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.BOUCLIER, 12)
    combat = _combat({AVANT_MID: pat})
    (disrupteur,) = _en_main(combat, _carte("CRT_100"))
    retrait, degats = _valeur("CRT_100", "retrait"), _valeur("CRT_100", "degats")

    combat.jouer_carte(disrupteur, AVANT_MID)

    bouclier_restant = max(0, 12 - retrait)
    assert pat.pv == pat.pv_max - max(0, degats - bouclier_restant)
    assert pat.statuts[Statut.BOUCLIER] == max(0, bouclier_restant - degats)
    (retire,) = _evenements(combat, NatureEvenement.STATUT_RETIRE)
    assert (retire.cible, retire.statut, retire.valeur) == (pat, Statut.BOUCLIER, min(12, retrait))


def test_le_retrait_de_bouclier_ne_touche_ni_au_renvoi_ni_au_leurre():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.RENVOI, 4)
    pat.statuts.ajouter(Statut.LEURRE, 1)
    combat = _combat({AVANT_MID: pat})
    retrait = Carte(
        id="TEST", nom="Retrait", image="test.png", rarete=RareteCarte.COMMUNE, categorie=CategorieCarte.ATTAQUE,
        cible=CibleCarte.ENNEMI_UNIQUE, cout=1, description="Retire {retrait}", valeurs={"retrait": 8},
        effets=(Effet(NatureEffet.RETRAIT_BOUCLIER, "retrait"),), exemplaire_module="M1",
    )
    _en_main(combat, retrait)

    combat.jouer_carte(retrait, AVANT_MID)

    assert pat.statuts[Statut.RENVOI] == 4 and pat.statuts[Statut.LEURRE] == 1
    assert _evenements(combat, NatureEvenement.STATUT_RETIRE)[0].valeur == 0


# --- Lot 3 du plan des cartes : Surcharge et bonus calcule ---


def _surcharge(combat):
    return combat.vaisseau.principal.statuts[Statut.SURCHARGE]


def test_post_combustion_pose_la_surcharge_qui_s_ajoute_a_chaque_coup():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    post_combustion, laser = _en_main(combat, _carte("CRT_51", "M2"), _carte("CRT_7"))

    combat.jouer_carte(post_combustion, AVANT_MID)
    combat.jouer_carte(laser, AVANT_MID)

    surcharge = _valeur("CRT_51", "surcharge")
    assert _surcharge(combat) == surcharge
    assert pat.pv == pat.pv_max - (_valeur("CRT_7", "degats") + surcharge)
    attaque = _evenements(combat, NatureEvenement.ATTAQUE)[-1]
    assert attaque.dont_surcharge == surcharge


def test_la_surcharge_compte_pour_chaque_cible_et_chaque_lancement():
    pat, pat2 = _ennemi(), _ennemi()
    combat = _combat({AVANT_MID: pat, AVANT_DROITE: pat2})
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 3)
    ogive, jumeaux = _en_main(combat, _carte("CRT_9", "M2"), _carte("CRT_58", "M2"))

    combat.jouer_carte(ogive, AVANT_MID)
    combat.jouer_carte(jumeaux, AVANT_DROITE)

    assert pat.pv == pat.pv_max - (_valeur("CRT_9", "degats") + 3)
    assert pat2.pv == pat2.pv_max - (_valeur("CRT_9", "degats") + 3) - 2 * (_valeur("CRT_58", "degats") + 3)


def test_la_surcharge_ne_compte_ni_pour_l_incendie_ni_pour_les_degats_renvoyes():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.RENVOI, 50)
    combat = _combat({AVANT_MID: pat})
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 3)
    (thermique,) = _en_main(combat, _carte("CRT_65", "M2"))

    combat.jouer_carte(thermique, AVANT_MID)

    # Coup de la carte : degats + Surcharge, tout renvoye au Lanceur sans nouveau bonus
    coup = _valeur("CRT_65", "degats") + 3
    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    assert lanceur.pv_combat == lanceur.pv_max - coup
    assert pat.statuts[Statut.INCENDIE] == _valeur("CRT_65", "incendie")


def test_la_surcharge_baisse_de_1_a_la_fin_du_tour_ennemi():
    combat = _combat({AVANT_GAUCHE: _ennemi()})
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 4)
    _en_main(combat)

    combat.finir_tour()

    assert _surcharge(combat) == 3


def test_ogive_surchauffee_pose_la_surcharge_avant_ses_degats():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    (ogive,) = _en_main(combat, _carte("CRT_55", "M2"))

    combat.jouer_carte(ogive, AVANT_MID)

    surcharge = _valeur("CRT_55", "surcharge")
    assert _surcharge(combat) == surcharge
    assert pat.pv == pat.pv_max - (_valeur("CRT_55", "degats") + surcharge)


def test_amplificateur_multiplie_la_surcharge_et_rien_a_zero():
    combat = _combat()
    premier, second = _en_main(combat, _carte("CRT_68", "M2"), _carte("CRT_68", "M2"))

    combat.jouer_carte(premier, AVANT_MID)
    assert _surcharge(combat) == 0 and not _evenements(combat, NatureEvenement.STATUT_POSE)

    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 4)
    combat.jouer_carte(second, AVANT_MID)
    assert _surcharge(combat) == 4 * _valeur("CRT_68", "facteur")


def test_lanceur_incandescent_double_et_fige_la_surcharge():
    combat = _combat({AVANT_GAUCHE: _ennemi()})
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 3)
    incandescent, post_combustion = _en_main(combat, _carte("CRT_77", "M2"), _carte("CRT_51", "M2"))

    combat.jouer_carte(incandescent, AVANT_MID)
    figee = 3 * _valeur("CRT_77", "facteur")
    assert _surcharge(combat) == figee
    assert _evenements(combat, NatureEvenement.STATUT_FIGE)[0].valeur == figee
    combat.finir_tour()
    assert _surcharge(combat) == figee  # ne baisse plus

    # Les nouvelles poses s'ajoutent toujours
    combat.electricite = 3
    combat.deck.main = [post_combustion]
    combat.jouer_carte(post_combustion, AVANT_MID)
    assert _surcharge(combat) == figee + _valeur("CRT_51", "surcharge")


def test_missile_surcharge_compte_la_surcharge_deux_fois():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 4)
    (missile,) = _en_main(combat, _carte("CRT_75", "M2"))

    combat.jouer_carte(missile, AVANT_MID)

    # Base + bonus (par point de Surcharge) + la Surcharge normale
    attendu = _valeur("CRT_75", "degats") + _valeur("CRT_75", "par_point") * 4 + 4
    assert pat.pv == pat.pv_max - attendu


def test_laser_de_contre_charge_consomme_le_bouclier_du_principal():
    boss = _ennemi("ENM_BOSS_PIRATES")
    combat = _combat({AVANT_MID: boss, ARRIERE_MID: boss})
    principal = combat.vaisseau.principal
    principal.statuts.ajouter(Statut.BOUCLIER, 14)
    contre_charge, second = _en_main(combat, _carte("CRT_99"), _carte("CRT_99"))

    combat.jouer_carte(contre_charge, AVANT_MID)
    assert boss.pv == boss.pv_max - 14 * _valeur("CRT_99", "par_point")
    assert principal.statuts[Statut.BOUCLIER] == 0
    (retrait,) = _evenements(combat, NatureEvenement.STATUT_RETIRE)
    assert (retrait.cible, retrait.valeur) == (principal, 14)

    # Sans bouclier : plus de degats en plus
    pv = boss.pv
    combat.jouer_carte(second, AVANT_MID)
    assert boss.pv == pv - _valeur("CRT_99", "degats")


def test_reacteur_en_surtension_et_armer_le_lanceur_piochent_et_surchargent():
    combat = _combat()
    reacteur, armer = _en_main(combat, _carte("CRT_95"), _carte("CRT_72", "M2"))
    combat.deck.pioche = [_carte("CRT_7") for _ in range(5)]

    combat.jouer_carte(reacteur, AVANT_MID)
    combat.jouer_carte(armer, AVANT_MID)

    assert _surcharge(combat) == _valeur("CRT_95", "surcharge") + _valeur("CRT_72", "surcharge")
    assert len(combat.deck.main) == _valeur("CRT_95", "pioche") + _valeur("CRT_72", "pioche")


# --- Verrouillage (lot 4) ---


def test_missile_marqueur_pose_le_verrouillage_apres_ses_degats():
    pat = _ennemi()
    combat = _combat({AVANT_MID: pat})
    (marqueur,) = _en_main(combat, _carte("CRT_56", "M2"))

    combat.jouer_carte(marqueur, AVANT_MID)

    # Effets dans l'ordre : ses propres degats ne profitent pas du Verrouillage qu'il pose
    assert pat.pv == pat.pv_max - _valeur("CRT_56", "degats")
    assert pat.statuts[Statut.VERROUILLAGE] == _valeur("CRT_56", "verrouillage")


def test_le_verrouillage_s_ajoute_a_chaque_coup_de_carte_et_au_journal():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.VERROUILLAGE, 3)
    combat = _combat({AVANT_MID: pat})
    (jumeaux,) = _en_main(combat, _carte("CRT_58", "M2"))

    combat.jouer_carte(jumeaux, AVANT_MID)

    # Deux lancements, +3 a chacun ; le Verrouillage n'est pas consomme
    assert pat.pv == pat.pv_max - 2 * (_valeur("CRT_58", "degats") + 3)
    assert pat.statuts[Statut.VERROUILLAGE] == 3
    attaque = _evenements(combat, NatureEvenement.ATTAQUE)[-1]
    assert attaque.dont_verrouillage == 3 and attaque.dont_surcharge is None


def test_verrouillage_et_surcharge_s_additionnent_avant_le_bouclier():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.VERROUILLAGE, 2)
    pat.statuts.ajouter(Statut.BOUCLIER, 5)
    combat = _combat({AVANT_MID: pat})
    combat.vaisseau.principal.statuts.ajouter(Statut.SURCHARGE, 3)
    (laser,) = _en_main(combat, _carte("CRT_7"))

    combat.jouer_carte(laser, AVANT_MID)

    # Exemple de la decision du 2026-11-22 : base + Surcharge + Verrouillage, puis le bouclier
    coup = _valeur("CRT_7", "degats") + 3 + 2
    assert pat.pv == pat.pv_max - (coup - 5)
    attaque = _evenements(combat, NatureEvenement.ATTAQUE)[-1]
    assert (attaque.valeur, attaque.dont_surcharge, attaque.dont_verrouillage) == (coup, 3, 2)


def test_le_verrouillage_ne_compte_ni_pour_l_incendie_ni_pour_les_degats_renvoyes():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.VERROUILLAGE, 4)
    pat.statuts.ajouter(Statut.RENVOI, 50)
    combat = _combat({AVANT_MID: pat})
    (thermique,) = _en_main(combat, _carte("CRT_65", "M2"))

    combat.jouer_carte(thermique, AVANT_MID)

    # Le coup de la carte compte le Verrouillage, tout est renvoye au Lanceur sans nouveau bonus
    lanceur = combat.vaisseau.module_d_exemplaire("M2")
    assert lanceur.pv_combat == lanceur.pv_max - (_valeur("CRT_65", "degats") + 4)
    pv = pat.pv
    combat.finir_tour()
    # Incendie en fin de tour du joueur : sa seule intensite, sans le Verrouillage
    incendie = [e for e in _evenements(combat, NatureEvenement.INCENDIE) if e.cible is pat]
    assert incendie[0].valeur == _valeur("CRT_65", "incendie")
    assert pat.pv == pv - _valeur("CRT_65", "incendie")


def test_le_verrouillage_baisse_de_1_a_la_fin_du_tour_du_joueur():
    pat = _ennemi()
    pat.statuts.ajouter(Statut.VERROUILLAGE, 2)
    combat = _combat({AVANT_MID: pat})
    _en_main(combat)

    combat.finir_tour()
    assert pat.statuts[Statut.VERROUILLAGE] == 1
    combat.finir_tour()
    assert pat.statuts[Statut.VERROUILLAGE] == 0


def test_ogive_de_marquage_et_protocole_de_ciblage_verrouillent_tous_les_ennemis():
    pat, pat2 = _ennemi(), _ennemi()
    combat = _combat({AVANT_MID: pat, ARRIERE_DROITE: pat2})
    ogive, protocole = _en_main(combat, _carte("CRT_57", "M2"), _carte("CRT_106"))

    combat.jouer_carte(ogive, AVANT_MID)
    combat.jouer_carte(protocole, AVANT_MID)

    attendu = _valeur("CRT_57", "verrouillage") + _valeur("CRT_106", "verrouillage")
    for ennemi in (pat, pat2):
        assert ennemi.pv == ennemi.pv_max - _valeur("CRT_57", "degats")
        assert ennemi.statuts[Statut.VERROUILLAGE] == attendu


def test_missile_de_precision_compte_le_verrouillage_de_sa_cible_deux_fois():
    pat, pat2 = _ennemi(), _ennemi()
    pat.statuts.ajouter(Statut.VERROUILLAGE, 5)
    combat = _combat({AVANT_MID: pat, AVANT_DROITE: pat2})
    precision, second = _en_main(combat, _carte("CRT_74", "M2"), _carte("CRT_74", "M2"))
    combat.electricite = 4

    combat.jouer_carte(precision, AVANT_MID)
    # Exemple de la proposition : 8 + 3 x 5 + 5 (Verrouillage normal) = 28
    attendu = _valeur("CRT_74", "degats") + _valeur("CRT_74", "par_point") * 5 + 5
    assert pat.pv == pat.pv_max - attendu
    assert pat.statuts[Statut.VERROUILLAGE] == 5

    # Un ennemi sans Verrouillage : la base seule (le Verrouillage de l'autre ne compte pas)
    combat.jouer_carte(second, AVANT_DROITE)
    assert pat2.pv == pat2.pv_max - _valeur("CRT_74", "degats")


def test_missile_verrouilleur_et_laser_de_visee_posent_leur_verrouillage():
    pat = _ennemi("ENM_PETIT_JEAN")
    combat = _combat({AVANT_MID: pat})
    verrouilleur, visee = _en_main(combat, _carte("CRT_73", "M2"), _carte("CRT_85"))

    combat.jouer_carte(verrouilleur, AVANT_MID)
    combat.jouer_carte(visee, AVANT_MID)

    v1 = _valeur("CRT_73", "verrouillage")
    assert pat.statuts[Statut.VERROUILLAGE] == v1 + _valeur("CRT_85", "verrouillage")
    # Le Laser de visee profite du Verrouillage pose par le Missile verrouilleur
    assert pat.pv == pat.pv_max - _valeur("CRT_73", "degats") - (_valeur("CRT_85", "degats") + v1)
