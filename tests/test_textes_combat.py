"""Textes de l'ecran de combat PC (src/ui/textes_combat.py) : mise en mots des faits du gameplay,
sans pyglet."""

import random

from src.gameplay.carte import charger_cartes
from src.gameplay.combat import Combat, Evenement, NatureEvenement
from src.gameplay.ennemi import CibleEffetEnnemi, NatureEffetEnnemi
from src.gameplay.partie import combat_depuis_partie, nouvelle_partie
from src.gameplay.statut import Statut
from src.ui import textes_combat
from src.ui.commun import regrouper_cartes


def _combat(niveau: int = 2) -> Combat:
    partie = nouvelle_partie(random.Random(1))
    partie.niveau = niveau
    return combat_depuis_partie(partie, random.Random(2))


def test_intention_courte_et_detaillee_pour_chaque_effet():
    combat = _combat()
    for intention in combat.intentions():
        for effet in intention.effets:
            court = textes_combat.texte_intention_court(effet)
            detail = textes_combat.texte_intention(effet)
            assert str(effet.valeur) in court and str(effet.valeur) in detail
            if effet.effet.repetitions > 1:
                assert f"×{effet.effet.repetitions}" in court
            if effet.effet.cible == CibleEffetEnnemi.PROXIMITE:
                assert effet.cible_prevue.nom in detail
            if effet.effet.cible == CibleEffetEnnemi.TOUS_MODULES:
                assert court.endswith("tous") and "à chaque module" in detail
            if effet.effet.repetitions > 1:
                assert detail.endswith(f", {effet.effet.repetitions} fois")
            assert detail.startswith("- ")


def test_menaces_le_module_vise_par_une_attaque_de_proximite():
    combat = _combat()
    menaces = textes_combat.menaces_par_module(combat)
    attendus = {
        id(effet.cible_prevue)
        for intention in combat.intentions() for effet in intention.effets
        if effet.effet.nature == NatureEffetEnnemi.ATTAQUE and effet.effet.cible == CibleEffetEnnemi.PROXIMITE
    }
    assert attendus <= set(menaces)
    for lignes in menaces.values():
        assert all(" inflige " in ligne and "dégâts" in ligne for ligne in lignes)


def test_menaces_tous_les_modules_pour_le_boss():
    combat = _combat(niveau=10)
    boss = combat.flotte.ennemis[0]
    if any(e.cible == CibleEffetEnnemi.TOUS_MODULES and e.nature == NatureEffetEnnemi.ATTAQUE for e in boss.etape_courante):
        menaces = textes_combat.menaces_par_module(combat)
        assert {id(module) for module in combat.vaisseau.modules_vivants()} == set(menaces)


def test_lignes_statuts_seulement_les_actifs():
    combat = _combat()
    principal = combat.vaisseau.principal
    assert textes_combat.lignes_statuts(principal) == []
    principal.statuts.ajouter(Statut.BOUCLIER, 6)
    principal.statuts.ajouter(Statut.LEURRE, 1)
    assert textes_combat.lignes_statuts(principal) == ["Bouclier 6", "Leurre"]


def test_popups_des_degats():
    def attaque(**champs):
        base = dict(valeur=6, annules_leurre=0, renvoyes=0, absorbes_bouclier=0, pv_perdus=6, pv_restants=10)
        return Evenement(NatureEvenement.ATTAQUE, 1, cible=object(), **{**base, **champs})

    assert textes_combat.popup_evenement(attaque())[0] == "-6"
    assert textes_combat.popup_evenement(attaque(absorbes_bouclier=2, pv_perdus=4))[0] == "-4 (bouclier 2)"
    assert textes_combat.popup_evenement(attaque(absorbes_bouclier=6, pv_perdus=0))[0] == "bloqué (6)"
    assert textes_combat.popup_evenement(attaque(annules_leurre=6, pv_perdus=0))[0] == "annulé"
    assert textes_combat.popup_evenement(attaque(renvoyes=6, pv_perdus=0))[0] == "renvoi 6"
    # Renvoi et bouclier se partagent toute l'attaque : jamais "-0"
    assert textes_combat.popup_evenement(attaque(renvoyes=5, absorbes_bouclier=1, pv_perdus=0))[0] == "renvoi 5 · bloqué (1)"
    assert textes_combat.popup_evenement(attaque(annules_leurre=4, absorbes_bouclier=2, pv_perdus=0))[0] == "annulé · bloqué (2)"
    # Reparation d'un module deja plein : pas de popup
    assert textes_combat.popup_evenement(Evenement(NatureEvenement.REPARATION, 1, cible=object(), valeur=0, pv_restants=60)) is None
    assert textes_combat.popup_evenement(Evenement(NatureEvenement.REPARATION, 1, cible=object(), valeur=3, pv_restants=60))[0] == "+3"
    assert textes_combat.popup_evenement(Evenement(NatureEvenement.DEBUT_TOUR, 1, valeur=1)) is None
    leurre = Evenement(NatureEvenement.STATUT_POSE, 1, cible=object(), valeur=1, statut=Statut.LEURRE)
    assert textes_combat.popup_evenement(leurre)[0] == "Leurre"
    bouclier = Evenement(NatureEvenement.STATUT_POSE, 1, cible=object(), valeur=6, statut=Statut.BOUCLIER)
    assert textes_combat.popup_evenement(bouclier)[0] == "+6 bouclier"


def test_journal_une_ligne_par_evenement_sauf_carte_jouee():
    combat = _combat()
    carte = next(c for c in combat.deck.main if combat.peut_jouer(c))
    combat.jouer_carte(carte, combat.cibles_possibles(carte)[0])
    combat.finir_tour()
    for evenement in combat.journal:
        ligne = textes_combat.ligne_journal(evenement)
        assert bool(ligne) == (evenement.nature != NatureEvenement.CARTE_JOUEE)
    texte = "".join(morceau for morceau, _couleur in textes_combat.ligne_journal(combat.journal[0]))
    assert texte == "--- Tour 1 ---"


def test_compteurs_hors_service_seulement_si_non_vide():
    combat = _combat()
    assert "Hors service" not in textes_combat.texte_compteurs(combat)
    combat.deck.hors_service.append(combat.deck.pioche.pop())
    assert "Hors service 1" in textes_combat.texte_compteurs(combat)


def test_regrouper_cartes_par_carte_et_module():
    modeles = charger_cartes()
    laser = next(iter(modeles.values()))
    cartes = [laser.copie(exemplaire_module="M1"), laser.copie(exemplaire_module="M1"), laser.copie(exemplaire_module="M2")]
    groupes = regrouper_cartes(cartes)
    assert [(carte.exemplaire_module, quantite) for carte, quantite in groupes] == [("M1", 2), ("M2", 1)]


def test_popup_et_journal_du_retrait_de_bouclier():
    combat = _combat()
    carte = charger_cartes()["CRT_100"]
    ennemi = combat.flotte.ennemis_vivants()[0]
    retire = Evenement(NatureEvenement.STATUT_RETIRE, 1, source=carte, cible=ennemi, valeur=8, statut=Statut.BOUCLIER)
    rien = Evenement(NatureEvenement.STATUT_RETIRE, 1, source=carte, cible=ennemi, valeur=0, statut=Statut.BOUCLIER)

    assert textes_combat.popup_evenement(retire)[0] == "-8 bouclier"
    assert textes_combat.popup_evenement(rien) is None
    texte = "".join(morceau for morceau, _couleur in textes_combat.ligne_journal(retire))
    assert texte == f"{carte.nom} → {ennemi.nom} : bouclier -8"
    texte = "".join(morceau for morceau, _couleur in textes_combat.ligne_journal(rien))
    assert texte == f"{carte.nom} → {ennemi.nom} : aucun bouclier à retirer"



def test_textes_de_la_surcharge():
    combat = _combat()
    principal = combat.vaisseau.principal
    principal.statuts.ajouter(Statut.SURCHARGE, 4)
    assert "Surcharge 4" in textes_combat.lignes_statuts(principal)
    principal.statuts.figes.add(Statut.SURCHARGE)
    assert "Surcharge 4 (figée)" in textes_combat.lignes_statuts(principal)

    ennemi = combat.flotte.ennemis_vivants()[0]
    attaque = Evenement(
        NatureEvenement.ATTAQUE, 1, source=principal, cible=ennemi, valeur=10, annules_leurre=0, renvoyes=0,
        absorbes_bouclier=0, pv_perdus=10, pv_restants=40, dont_surcharge=4,
    )
    assert "10 dégâts (dont 4 de surcharge)" in "".join(m for m, _c in textes_combat.ligne_journal(attaque))
    fige = Evenement(NatureEvenement.STATUT_FIGE, 1, cible=principal, valeur=8, statut=Statut.SURCHARGE)
    assert textes_combat.popup_evenement(fige)[0] == "Surcharge figée"



def test_textes_du_verrouillage():
    combat = _combat()
    ennemi = combat.flotte.ennemis_vivants()[0]
    ennemi.statuts.ajouter(Statut.VERROUILLAGE, 3)
    assert "Verrouillage 3" in textes_combat.lignes_statuts(ennemi)
    assert Statut.VERROUILLAGE in textes_combat.STATUTS_EN_PASTILLE

    attaque = Evenement(
        NatureEvenement.ATTAQUE, 1, source=combat.vaisseau.principal, cible=ennemi, valeur=12, annules_leurre=0,
        renvoyes=0, absorbes_bouclier=0, pv_perdus=12, pv_restants=38, dont_surcharge=4, dont_verrouillage=3,
    )
    texte = "".join(m for m, _c in textes_combat.ligne_journal(attaque))
    assert "12 dégâts (dont 4 de surcharge, 3 de verrouillage)" in texte
    pose = Evenement(NatureEvenement.STATUT_POSE, 1, cible=ennemi, valeur=2, statut=Statut.VERROUILLAGE)
    assert textes_combat.popup_evenement(pose) == ("+2 verrouillage", textes_combat.COULEUR_VERROUILLAGE)


def test_fige_s_accorde_au_genre_du_statut():
    combat = _combat()
    principal = combat.vaisseau.principal
    principal.statuts.ajouter(Statut.BOUCLIER, 5)
    principal.statuts.figes.add(Statut.BOUCLIER)
    assert "Bouclier 5 (figé)" in textes_combat.lignes_statuts(principal)
