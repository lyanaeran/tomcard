"""
Tests unitaires pour le moteur de combat (src/gameplay/combat.py).
"""

import random

from src.gameplay.carte import ActionCarte, Carte, CibleCarte, TypeCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.deck import Deck
from src.gameplay.ennemi import ActionEnnemi, CibleActionEnnemi, Ennemi, TypeActionEnnemi
from src.gameplay.flotte import Flotte
from src.gameplay.joueur import Joueur
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.vaisseau import Vaisseau

IMG = "test.png"
CARTE_ATTAQUE = Carte(nom="Attaque", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=7)
CARTE_BOUCLIER = Carte(nom="Bouclier", image=IMG, type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE_UNIQUE, cout=1, valeur=5)
CARTE_REPARATION = Carte(nom="Soin", image=IMG, type=TypeCarte.REPARATION, cible=CibleCarte.ALLIE_UNIQUE, cout=1, valeur=4)
CARTE_PERCER = Carte(nom="Percer", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.LIGNE_ENNEMIE, cout=2, valeur=5)
CARTE_PROTEGER = Carte(nom="Proteger", image=IMG, type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIES_MULTIPLES, cout=2, valeur=4)
CARTE_MITRAILLER = Carte(nom="Mitrailler", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMIS_MULTIPLES, cout=2, valeur=3)
CARTE_REDUCTION_DEGATS = Carte(
    nom="Tordre le canon", image=IMG, type=TypeCarte.DEBUFF, cible=CibleCarte.ENNEMI_UNIQUE,
    cout=1, valeur=5, action=ActionCarte.REDUCTION_DEGATS, duree=1,
)
CARTE_VULNERABILITE = Carte(
    nom="Breche", image=IMG, type=TypeCarte.DEBUFF, cible=CibleCarte.ENNEMI_UNIQUE,
    cout=2, valeur=100, action=ActionCarte.VULNERABILITE, duree=1,
)
CARTE_COLONNE_AVANT = Carte(
    nom="Ligne avant", image=IMG, type=TypeCarte.DEBUFF, cible=CibleCarte.COLONNE_AVANT_ENNEMIE,
    cout=1, valeur=100, action=ActionCarte.VULNERABILITE, duree=1,
)
CARTE_BOUCLIER_PERPETUEL = Carte(
    nom="Bouclier perpetuel", image=IMG, type=TypeCarte.BUFF, cible=CibleCarte.MODULE_PRINCIPAL,
    cout=5, valeur=10, action=ActionCarte.BOUCLIER_PAR_TOUR, duree=None,
)
CARTE_TIR_ALLIE = Carte(
    nom="Tir allie", image=IMG, type=TypeCarte.DEBUFF, cible=CibleCarte.ENNEMI_UNIQUE,
    cout=3, valeur=0, action=ActionCarte.REDIRECTION_CIBLE, duree=1,
)
CARTE_COLONNE_AVANT_ALLIEE = Carte(
    nom="Proteger l'avant poste", image=IMG, type=TypeCarte.DEFENSE, cible=CibleCarte.COLONNE_AVANT_ALLIEE,
    cout=2, valeur=10,
)
CARTE_BLINDAGE_MAXIMAL = Carte(
    nom="Blindage maximal", image=IMG, type=TypeCarte.BUFF, cible=CibleCarte.MODULE_PRINCIPAL,
    cout=2, valeur=8, action=ActionCarte.BOUCLIER_PAR_TOUR, duree=3,
)
CARTE_BOUCLIER_ADAPTATIF = Carte(
    nom="Bouclier adaptatif", image=IMG, type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE_UNIQUE,
    cout=1, valeur=80, action=ActionCarte.BOUCLIER_POURCENTAGE_PV,
)
CARTE_FONDS_DE_TIROIR = Carte(
    nom="Fonds de tiroir", image=IMG, type=TypeCarte.OUTILS, cible=CibleCarte.ALLIES_MULTIPLES,
    cout=1, valeur=1, action=ActionCarte.GAIN_ELECTRICITE_PAR_MODULE,
)
CARTE_LEURRE = Carte(
    nom="Leurre", image=IMG, type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE_UNIQUE,
    cout=3, valeur=0, action=ActionCarte.ANNULATION_PROCHAINE_ATTAQUE,
)

POSITION_ENNEMI = Position(Colonne.AVANT, Rangee.GAUCHE)


def _ennemi_attaque(pv_max: int, degats: int, nom: str = "Ennemi") -> Ennemi:
    """Ennemi de test simple : une seule Action, ATTAQUE de proximite tous les tours (memes
    valeurs par defaut que l'ancienne API Ennemi(pv_max=, degats_attaque=))."""
    action = ActionEnnemi(type=TypeActionEnnemi.ATTAQUE, cible=CibleActionEnnemi.PROXIMITE, valeur=degats)
    return Ennemi(pv_max=pv_max, actions=[action], nom=nom)


def _nouveau_combat(
    pv_base: int = 15,
    pv_ennemi: int = 15,
    degats_ennemi: int = 7,
    ennemis: dict | None = None,
    vaisseau: Vaisseau | None = None,
    aleatoire: random.Random | None = None,
):
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_REPARATION]
    deck = Deck(cartes=cartes, generateur_aleatoire=random.Random(0))
    if vaisseau is None:
        vaisseau = Vaisseau(base=Module(pv_max=pv_base))
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=3)
    if ennemis is None:
        ennemis = {POSITION_ENNEMI: _ennemi_attaque(pv_ennemi, degats_ennemi)}
    flotte = Flotte(ennemis)
    combat = Combat(joueur=joueur, flotte=flotte, aleatoire=aleatoire)
    return combat, vaisseau, flotte


def _cible_valide_pour(combat: Combat, carte) -> Module | Ennemi | None:
    """Aide de test : cible valide pour cette carte, peu importe laquelle exactement."""
    if carte.cible in (CibleCarte.ALLIES_MULTIPLES, CibleCarte.ENNEMIS_MULTIPLES):
        return None
    if carte.cible in (CibleCarte.ENNEMI_UNIQUE, CibleCarte.LIGNE_ENNEMIE):
        return combat.flotte.ennemis_vivants()[0]
    return combat.joueur.vaisseau.base


def test_debut_de_combat_pioche_la_main_et_recharge_l_electricite():
    combat, _vaisseau, _flotte = _nouveau_combat()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == 3
    assert combat.etat == EtatCombat.EN_COURS


def test_jouer_une_carte_attaque_inflige_des_degats_a_l_ennemi():
    combat, _vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert ennemi.pv == 15 - CARTE_ATTAQUE.valeur
    assert combat.joueur.electricite == 3 - CARTE_ATTAQUE.cout


def test_jouer_une_carte_bouclier_protege_le_module_choisi():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BOUCLIER]

    combat.jouer_carte(CARTE_BOUCLIER, vaisseau.base)

    assert vaisseau.base.bouclier == CARTE_BOUCLIER.valeur


def test_jouer_une_carte_soin_repare_le_module_choisi():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_REPARATION]
    vaisseau.base.subir_degats(10)

    combat.jouer_carte(CARTE_REPARATION, vaisseau.base)

    assert vaisseau.base.pv == 15 - 10 + CARTE_REPARATION.valeur


def test_jouer_carte_renvoie_le_montant_effectif_applique():
    combat, vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE, CARTE_BOUCLIER]

    resultat_attaque = combat.jouer_carte(CARTE_ATTAQUE, ennemi)
    resultat_bouclier = combat.jouer_carte(CARTE_BOUCLIER, vaisseau.base)

    assert resultat_attaque == [(ennemi, CARTE_ATTAQUE.valeur)]
    assert resultat_bouclier == [(vaisseau.base, CARTE_BOUCLIER.valeur)]


def test_jouer_une_carte_soin_renvoie_le_montant_effectif_plafonne_au_pv_max():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_REPARATION]
    vaisseau.base.subir_degats(2)  # il ne manque que 2 PV, la carte en soigne 4

    resultat = combat.jouer_carte(CARTE_REPARATION, vaisseau.base)

    assert resultat == [(vaisseau.base, 2)]
    assert vaisseau.base.pv == vaisseau.base.pv_max


def test_jouer_une_carte_attaque_renvoie_le_montant_effectif_plafonne_aux_pv_restants():
    combat, _vaisseau, flotte = _nouveau_combat(pv_ennemi=3)  # l'ennemi n'a que 3 PV, la carte fait 7 degats
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    resultat = combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert resultat == [(ennemi, 3)]
    assert ennemi.pv == 0


def test_impossible_de_jouer_une_carte_sans_assez_d_electricite():
    combat, _vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]
    combat.joueur.electricite = 0

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert ennemi.pv == 15


def test_impossible_de_jouer_une_carte_avec_une_cible_du_mauvais_type():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, vaisseau.base)  # Attaque cible un ennemi, pas un module

    assert vaisseau.base.pv == 15  # rien ne s'est passe


def test_impossible_de_cibler_un_ennemi_deja_detruit():
    combat, _vaisseau, flotte = _nouveau_combat(pv_ennemi=1)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE, CARTE_ATTAQUE]
    combat.jouer_carte(CARTE_ATTAQUE, ennemi)  # detruit l'ennemi -> victoire, combat termine

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)  # no-op : combat deja termine

    assert combat.etat == EtatCombat.VICTOIRE


def test_finir_tour_joueur_declenche_l_attaque_ennemie():
    combat, vaisseau, _flotte = _nouveau_combat()

    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 7


def test_finir_tour_joueur_pioche_une_nouvelle_main():
    combat, _vaisseau, _flotte = _nouveau_combat()
    premiere_carte = combat.joueur.deck.main[0]
    combat.jouer_carte(premiere_carte, _cible_valide_pour(combat, premiere_carte))

    combat.finir_tour_joueur()

    assert len(combat.joueur.deck.main) == 5
    assert combat.joueur.electricite == 3


def test_victoire_quand_l_ennemi_est_detruit():
    combat, _vaisseau, flotte = _nouveau_combat(pv_ennemi=7)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert combat.etat == EtatCombat.VICTOIRE


def test_pas_de_victoire_tant_qu_un_ennemi_survit():
    e1 = _ennemi_attaque(7, 4)
    e2 = _ennemi_attaque(7, 4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e1,
        Position(Colonne.AVANT, Rangee.DROITE): e2,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, e1)

    assert combat.etat == EtatCombat.EN_COURS


def test_victoire_seulement_quand_tous_les_ennemis_sont_detruits():
    e1 = _ennemi_attaque(7, 4)
    e2 = _ennemi_attaque(7, 4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e1,
        Position(Colonne.AVANT, Rangee.DROITE): e2,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE, CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, e1)
    combat.jouer_carte(CARTE_ATTAQUE, e2)

    assert combat.etat == EtatCombat.VICTOIRE


def test_defaite_quand_le_module_de_base_est_detruit():
    combat, _vaisseau, _flotte = _nouveau_combat(pv_base=5)

    combat.finir_tour_joueur()

    assert combat.etat == EtatCombat.DEFAITE


def test_defaite_independante_de_la_destruction_d_un_module_non_base():
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_REPARATION]
    deck = Deck(cartes=cartes, generateur_aleatoire=random.Random(0))
    module_fragile = Module(pv_max=1)
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=module_fragile)
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=3)
    flotte = Flotte({POSITION_ENNEMI: _ennemi_attaque(15, 7)})
    combat = Combat(joueur=joueur, flotte=flotte)

    module_fragile.subir_degats(100)  # detruit un module non-base, hors du moteur de combat
    combat.finir_tour_joueur()  # declenche la verification de fin de combat

    assert module_fragile.est_detruit()
    assert combat.etat == EtatCombat.EN_COURS  # la base (15 - 7 = 8 PV) est toujours en vie


def test_finir_tour_joueur_renvoie_les_attaques_resolues():
    combat, vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]

    attaques = combat.finir_tour_joueur()

    assert attaques == [(POSITION_ENNEMI, ennemi, vaisseau.base, 7, "degats")]


def test_plusieurs_ennemis_attaquent_dans_le_meme_tour():
    e1 = _ennemi_attaque(15, 4)
    e2 = _ennemi_attaque(15, 6)
    position_e1 = Position(Colonne.AVANT, Rangee.GAUCHE)
    position_e2 = Position(Colonne.AVANT, Rangee.DROITE)
    combat, vaisseau, _flotte = _nouveau_combat(ennemis={position_e1: e1, position_e2: e2})

    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 4 - 6


def test_ordre_de_resolution_avant_haut_bas_puis_arriere_haut_bas():
    """L'ordre de resolution des attaques (cf. Combat._tour_ennemi) determine notamment quelle
    attaque un Leurre annule quand plusieurs ennemis visent le meme module (specs.md 12.6)."""
    positions_ordonnees = [
        Position(Colonne.AVANT, Rangee.GAUCHE),
        Position(Colonne.AVANT, Rangee.MID),
        Position(Colonne.AVANT, Rangee.DROITE),
        Position(Colonne.ARRIERE, Rangee.GAUCHE),
        Position(Colonne.ARRIERE, Rangee.MID),
        Position(Colonne.ARRIERE, Rangee.DROITE),
    ]
    ennemis = {position: _ennemi_attaque(15, 1, nom=str(position)) for position in positions_ordonnees}
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=_vaisseau_complet(), ennemis=ennemis)

    attaques = combat.finir_tour_joueur()

    assert [position for position, _e, _c, _d, _t in attaques] == positions_ordonnees


def test_leurre_avec_deux_attaquants_n_annule_que_la_premiere_attaque_resolue():
    """Cf. test_ordre_de_resolution_avant_haut_bas_puis_arriere_haut_bas : le premier
    attaquant dans cet ordre est celui dont l'attaque est annulee par le leurre."""
    e_avant = _ennemi_attaque(15, 5, nom="avant")
    e_arriere = _ennemi_attaque(15, 3, nom="arriere")
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e_avant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): e_arriere,
    }
    vaisseau = _vaisseau_complet()
    vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).pv = 0  # AVANT-GAUCHE vide : les deux visent ARRIERE-GAUCHE
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau, ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_LEURRE]
    combat.joueur.electricite = 3
    arriere_gauche = vaisseau.module_en(Colonne.ARRIERE, Rangee.GAUCHE)
    combat.jouer_carte(CARTE_LEURRE, arriere_gauche)

    attaques = combat.finir_tour_joueur()

    assert [degats for _p, _e, _c, degats, _t in attaques] == [0, 3]  # avant (premier resolu) annule, arriere non
    assert arriere_gauche.pv == arriere_gauche.pv_max - 3


def test_arret_immediat_si_la_base_est_detruite_en_cours_de_tour():
    e1 = _ennemi_attaque(15, 20)  # detruit la base d'un coup
    e2 = _ennemi_attaque(15, 5)
    position_e1 = Position(Colonne.AVANT, Rangee.GAUCHE)
    position_e2 = Position(Colonne.AVANT, Rangee.DROITE)
    combat, vaisseau, _flotte = _nouveau_combat(pv_base=10, ennemis={position_e1: e1, position_e2: e2})

    attaques = combat.finir_tour_joueur()

    assert combat.etat == EtatCombat.DEFAITE
    assert attaques == [(position_e1, e1, vaisseau.base, 10, "degats")]  # e2 n'a pas agi, degats plafonnes aux 10 PV restants


# --- Cibles multiples (LIGNE_ENNEMIE, ALLIES_MULTIPLES, ENNEMIS_MULTIPLES) ---


def test_ligne_ennemie_touche_l_avant_et_l_arriere_de_la_rangee():
    avant = _ennemi_attaque(10, 4)
    arriere = _ennemi_attaque(10, 4)
    autre_rangee = _ennemi_attaque(10, 4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): avant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): arriere,
        Position(Colonne.AVANT, Rangee.DROITE): autre_rangee,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_PERCER]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_PERCER, avant)  # clic sur l'avant de la rangee gauche

    assert avant.pv == 10 - 5
    assert arriere.pv == 10 - 5  # touche aussi, meme rangee
    assert autre_rangee.pv == 10  # rangee differente, pas touchee


def test_ligne_ennemie_ne_plante_pas_si_l_arriere_est_absent():
    seul = _ennemi_attaque(10, 4)
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis={Position(Colonne.AVANT, Rangee.GAUCHE): seul})
    combat.joueur.deck.main = [CARTE_PERCER]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_PERCER, seul)

    assert seul.pv == 10 - 5


def test_proteger_donne_du_bouclier_a_tous_les_modules_vivants():
    module_equipe = Module(pv_max=10)
    module_detruit = Module(pv_max=5)
    module_detruit.subir_degats(100)  # detruit, ne doit pas etre affecte
    vaisseau = Vaisseau(base=Module(pv_max=15), avant_gauche=module_equipe, arriere_gauche=module_detruit)
    deck = Deck(cartes=[CARTE_PROTEGER], generateur_aleatoire=random.Random(0))
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=3)
    flotte = Flotte({POSITION_ENNEMI: _ennemi_attaque(15, 7)})
    combat = Combat(joueur=joueur, flotte=flotte)
    combat.joueur.deck.main = [CARTE_PROTEGER]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_PROTEGER)  # pas de cible a fournir

    assert vaisseau.base.bouclier == 4
    assert module_equipe.bouclier == 4
    assert module_detruit.bouclier == 0


def test_mitrailler_touche_tous_les_ennemis_vivants():
    e1 = _ennemi_attaque(15, 4)
    e2 = _ennemi_attaque(15, 4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e1,
        Position(Colonne.AVANT, Rangee.DROITE): e2,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_MITRAILLER]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_MITRAILLER)  # pas de cible a fournir

    assert e1.pv == 15 - 3
    assert e2.pv == 15 - 3


def test_cible_sans_clic_refusee_si_une_cible_est_quand_meme_fournie():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_PROTEGER]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_PROTEGER, vaisseau.base)  # cible superflue -> refuse

    assert vaisseau.base.bouclier == 0


# --- Debuff (Sabotage, specs.md 12.1/12.4) ---


def test_reduction_degats_diminue_les_degats_de_la_prochaine_attaque():
    combat, vaisseau, flotte = _nouveau_combat(degats_ennemi=7)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_REDUCTION_DEGATS]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_REDUCTION_DEGATS, ennemi)
    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - (7 - 5)


def test_reduction_degats_expire_apres_un_tour():
    combat, vaisseau, flotte = _nouveau_combat(degats_ennemi=7, pv_base=100)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_REDUCTION_DEGATS]
    combat.joueur.electricite = 2
    combat.jouer_carte(CARTE_REDUCTION_DEGATS, ennemi)
    combat.finir_tour_joueur()  # 1er tour ennemi : reduction active (-5)
    pv_apres_premier_tour = vaisseau.base.pv

    combat.finir_tour_joueur()  # 2e tour ennemi : reduction expiree, degats pleins

    assert vaisseau.base.pv == pv_apres_premier_tour - 7


def test_vulnerabilite_majore_les_degats_d_une_attaque_du_joueur():
    combat, _vaisseau, flotte = _nouveau_combat(pv_ennemi=30)
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_VULNERABILITE, CARTE_ATTAQUE]
    combat.joueur.electricite = 5

    combat.jouer_carte(CARTE_VULNERABILITE, ennemi)
    resultat = combat.jouer_carte(CARTE_ATTAQUE, ennemi)

    assert resultat == [(ennemi, 14)]  # 7 degats * (1 + 100%)
    assert ennemi.pv == 30 - 14


def test_colonne_avant_ennemie_touche_toute_la_colonne_avant_uniquement():
    avant_g = _ennemi_attaque(15, 1)
    avant_d = _ennemi_attaque(15, 1)
    arriere_g = _ennemi_attaque(15, 1)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): avant_g,
        Position(Colonne.AVANT, Rangee.DROITE): avant_d,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): arriere_g,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_COLONNE_AVANT, avant_g)  # clic sur un ennemi de la colonne avant

    assert avant_g.buffs_actifs[0].valeur == 100
    assert avant_d.buffs_actifs[0].valeur == 100
    assert arriere_g.buffs_actifs == []  # colonne arriere non touchee


def test_colonne_avant_ennemie_refuse_un_clic_sur_l_arriere():
    avant = _ennemi_attaque(15, 1)
    arriere = _ennemi_attaque(15, 1)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): avant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): arriere,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_COLONNE_AVANT, arriere)  # clic sur l'arriere -> refuse

    assert arriere.buffs_actifs == []
    assert avant.buffs_actifs == []


# --- Buff (Blindage, specs.md 12.3/12.5) ---


def test_buff_bouclier_perpetuel_donne_du_bouclier_immediatement():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BOUCLIER_PERPETUEL]
    combat.joueur.electricite = 5

    resultat = combat.jouer_carte(CARTE_BOUCLIER_PERPETUEL, None)  # Module Principal, sans clic

    assert resultat == [(vaisseau.base, 10)]
    assert vaisseau.base.bouclier == 10


def test_buff_bouclier_perpetuel_se_redeclenche_a_chaque_tour_joueur_sans_expirer():
    """Le buff (persistant) ne s'arrete jamais. La dissipation naturelle du bouclier (specs.md
    3.5) verifie d'abord si la valeur ACTUELLE est <= SEUIL_DISSIPATION_BOUCLIER (10 > 5 : elle
    ne disparait pas completement, elle est divisee par deux), puis le buff repose sa valeur
    par-dessus : le bouclier ne se stabilise donc pas a la valeur du buff, il croit tant qu'il
    reste au-dessus du seuil apres division (10 -> 5+10=15 -> 8+10=18 -> ...)."""
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    combat.joueur.deck.main = [CARTE_BOUCLIER_PERPETUEL]
    combat.joueur.electricite = 5
    combat.jouer_carte(CARTE_BOUCLIER_PERPETUEL, None)

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 15  # dissipe 10 -> 5 (10 > seuil), puis repose a +10

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 18  # dissipe 15 -> 8 (ceil(15/2)), puis repose a +10
    assert len(vaisseau.base.buffs_actifs) == 1


# --- Tir allie (Sabotage, specs.md 12.6) ---


def test_tir_allie_redirige_l_attaque_vers_un_autre_ennemi_vivant():
    attaquant = _ennemi_attaque(15, 7)
    # degats_attaque=0 : isole l'assertion sur le joueur (sinon cible_potentielle
    # attaquerait aussi normalement le joueur de son cote, ce qui est correct mais
    # brouillerait l'assertion "attaquant n'a pas touche le joueur").
    cible_potentielle = _ennemi_attaque(15, 0)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): attaquant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): cible_potentielle,
    }
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_TIR_ALLIE]
    combat.joueur.electricite = 3

    combat.jouer_carte(CARTE_TIR_ALLIE, attaquant)
    combat.finir_tour_joueur()

    assert cible_potentielle.pv == 15 - 7  # a subi l'attaque a la place du joueur
    assert vaisseau.base.pv == 15  # le joueur n'a pas ete touche


def test_tir_allie_sans_autre_ennemi_attaque_normalement():
    seul = _ennemi_attaque(15, 7)
    ennemis = {POSITION_ENNEMI: seul}
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_TIR_ALLIE]
    combat.joueur.electricite = 3

    combat.jouer_carte(CARTE_TIR_ALLIE, seul)
    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 7  # aucun autre ennemi disponible : attaque normale


def test_tir_allie_expire_apres_un_tour():
    attaquant = _ennemi_attaque(15, 7)
    autre = _ennemi_attaque(15, 0)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): attaquant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): autre,
    }
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_TIR_ALLIE]
    combat.joueur.electricite = 3
    combat.jouer_carte(CARTE_TIR_ALLIE, attaquant)
    combat.finir_tour_joueur()  # 1er tour ennemi : redirection active
    pv_base_apres_premier_tour = vaisseau.base.pv

    combat.finir_tour_joueur()  # 2e tour ennemi : debuff expire, attaque normale

    assert vaisseau.base.pv == pv_base_apres_premier_tour - 7


def test_previsualiser_cible_masque_le_module_si_redirection_active():
    attaquant = _ennemi_attaque(15, 7)
    autre = _ennemi_attaque(15, 1)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): attaquant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): autre,
    }
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_TIR_ALLIE]
    combat.joueur.electricite = 3
    assert combat.previsualiser_cible(attaquant) is vaisseau.base

    combat.jouer_carte(CARTE_TIR_ALLIE, attaquant)

    # Appele plusieurs fois (comme au survol/redessin repete de l'UI) : ne doit jamais
    # consommer l'alea ni faire planter, contrairement a la resolution reelle du tour.
    assert combat.previsualiser_cible(attaquant) is None
    assert combat.previsualiser_cible(attaquant) is None


def test_prochaines_actions_actives_renvoie_toutes_les_actions_du_meme_tour():
    """Un ennemi comme le Boss des pirates (specs.md 13) attaque a chaque tour ET pose un buff
    a partir d'un certain tour : les deux doivent apparaitre au meme tour, pas seulement la
    premiere de la liste (ce que prochaine_action_active, utilisee par previsualiser_cible,
    renvoie seule - cf. test suivant)."""
    attaque = ActionEnnemi(type=TypeActionEnnemi.ATTAQUE, cible=CibleActionEnnemi.TOUS_MODULES_JOUEUR, valeur=5)
    buff = ActionEnnemi(
        type=TypeActionEnnemi.POSE_BUFF, cible=CibleActionEnnemi.SOI_MEME, valeur=2, frequence=3, tour_depart=2,
        action_buff=ActionCarte.AUGMENTATION_DEGATS,
    )
    boss = Ennemi(pv_max=150, actions=[attaque, buff], nom="Boss")
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): boss}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)

    assert combat.prochaines_actions_actives(boss) == [attaque]  # tour 1 : le buff n'est pas encore actif

    combat.finir_tour_joueur()  # ecoule le tour ennemi 1

    assert combat.prochaines_actions_actives(boss) == [attaque, buff]  # tour 2 : les deux


def test_prochaine_action_active_renvoie_la_premiere_des_actions_actives():
    attaque = ActionEnnemi(type=TypeActionEnnemi.ATTAQUE, cible=CibleActionEnnemi.TOUS_MODULES_JOUEUR, valeur=5)
    buff = ActionEnnemi(
        type=TypeActionEnnemi.POSE_BUFF, cible=CibleActionEnnemi.SOI_MEME, valeur=2, frequence=3, tour_depart=2,
        action_buff=ActionCarte.AUGMENTATION_DEGATS,
    )
    boss = Ennemi(pv_max=150, actions=[attaque, buff], nom="Boss")
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): boss}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.finir_tour_joueur()

    assert combat.prochaine_action_active(boss) is attaque


def test_prochaine_action_active_renvoie_none_sans_action_active():
    buff = ActionEnnemi(
        type=TypeActionEnnemi.POSE_BUFF, cible=CibleActionEnnemi.SOI_MEME, valeur=3, frequence=2, tour_depart=1,
        action_buff=ActionCarte.BOUCLIER_PAR_TOUR,
    )
    petit_jean = Ennemi(pv_max=100, actions=[buff], nom="Petit Jean")
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): petit_jean}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.finir_tour_joueur()  # tour 1 ecoule : buff pose (tour_depart=1)

    assert combat.prochaines_actions_actives(petit_jean) == []  # tour 2 : frequence=2, pas actif
    assert combat.prochaine_action_active(petit_jean) is None


# --- Colonne avant alliee (Blindage, specs.md 12.1) ---


def _vaisseau_complet(pv: int = 15) -> Vaisseau:
    return Vaisseau(
        base=Module(pv_max=pv, nom="Base"),
        avant_gauche=Module(pv_max=pv, nom="AvantGauche"),
        avant_droite=Module(pv_max=pv, nom="AvantDroite"),
        arriere_gauche=Module(pv_max=pv, nom="ArriereGauche"),
        arriere_droite=Module(pv_max=pv, nom="ArriereDroite"),
    )


def test_colonne_avant_alliee_protege_les_deux_modules_avant_et_le_principal():
    vaisseau = _vaisseau_complet()
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT_ALLIEE]
    combat.joueur.electricite = 2
    avant_gauche = vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE)

    combat.jouer_carte(CARTE_COLONNE_AVANT_ALLIEE, avant_gauche)  # clic sur un module avant

    assert vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).bouclier == 10
    assert vaisseau.module_en(Colonne.AVANT, Rangee.DROITE).bouclier == 10
    assert vaisseau.module_en(Colonne.ARRIERE, Rangee.GAUCHE).bouclier == 0
    assert vaisseau.module_en(Colonne.ARRIERE, Rangee.DROITE).bouclier == 0
    # Le module principal occupe la rangee mid, a la fois avant et arriere (specs.md 12.1).
    assert vaisseau.base.bouclier == 10


def test_colonne_avant_alliee_accepte_un_clic_sur_le_module_principal():
    vaisseau = _vaisseau_complet()
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT_ALLIEE]
    combat.joueur.electricite = 2

    resultat = combat.jouer_carte(CARTE_COLONNE_AVANT_ALLIEE, vaisseau.base)  # clic sur le principal

    assert vaisseau.base.bouclier == 10
    assert vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).bouclier == 10
    assert len(resultat) == 3  # avant-gauche, avant-droite, principal


def test_colonne_avant_alliee_refuse_un_clic_sur_l_arriere():
    vaisseau = _vaisseau_complet()
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT_ALLIEE]
    combat.joueur.electricite = 2
    arriere_gauche = vaisseau.module_en(Colonne.ARRIERE, Rangee.GAUCHE)

    resultat_arriere = combat.jouer_carte(CARTE_COLONNE_AVANT_ALLIEE, arriere_gauche)

    assert resultat_arriere == []
    assert vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).bouclier == 0


# --- Blindage maximal (Blindage, specs.md 12.1/12.3) ---


def test_blindage_maximal_donne_du_bouclier_immediatement():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BLINDAGE_MAXIMAL]
    combat.joueur.electricite = 2

    resultat = combat.jouer_carte(CARTE_BLINDAGE_MAXIMAL, None)  # Module Principal, sans clic

    assert resultat == [(vaisseau.base, 8)]
    assert vaisseau.base.bouclier == 8


def test_blindage_maximal_expire_apres_3_tours():
    """La dissipation naturelle du bouclier (specs.md 3.5) verifie d'abord la valeur ACTUELLE
    contre SEUIL_DISSIPATION_BOUCLIER (8 > 5 : divisee par deux, pas annulee) avant que le buff
    ne repose sa valeur par-dessus : le bouclier croit tant que le buff est actif
    (8 -> 4+8=12 -> 6+8=14 -> 7+8=15), puis, une fois le buff expire (3 tours), plus rien ne le
    repose : seule la dissipation continue de s'appliquer, jusqu'a tomber sous le seuil."""
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    combat.joueur.deck.main = [CARTE_BLINDAGE_MAXIMAL]
    combat.joueur.electricite = 2
    combat.jouer_carte(CARTE_BLINDAGE_MAXIMAL, None)

    combat.finir_tour_joueur()
    combat.finir_tour_joueur()
    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 15  # 8 -> 12 -> 14 -> 15 (dissipation puis +8 a chaque tour)
    assert vaisseau.base.buffs_actifs == []  # buff expire apres ce 3e redeclenchement

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 8  # plus de buff pour le reposer : ceil(15/2)=8

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 4  # ceil(8/2)=4

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 0  # 4 <= SEUIL_DISSIPATION_BOUCLIER


# --- Dissipation naturelle du bouclier (specs.md 3.5) ---


def test_bouclier_module_se_dissipe_de_moitie_a_chaque_tour_joueur():
    """La valeur ACTUELLE est comparee au seuil avant division (specs.md 3.5) : 20 et 10 sont
    tous deux > SEUIL_DISSIPATION_BOUCLIER, ils sont donc divises par deux ; seul 5 (<= seuil)
    disparait completement plutot que d'etre divise."""
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    vaisseau.base.ajouter_bouclier(20)

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 10  # 20 > seuil : ceil(20/2)

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 5  # 10 > seuil : ceil(10/2)

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 0  # 5 <= SEUIL_DISSIPATION_BOUCLIER : dissipe completement


def test_bouclier_module_au_ou_sous_le_seuil_dissipe_completement_en_un_tour():
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    vaisseau.base.ajouter_bouclier(5)

    combat.finir_tour_joueur()

    assert vaisseau.base.bouclier == 0  # 5 <= SEUIL_DISSIPATION_BOUCLIER : pas de division


def test_bouclier_module_au_dessus_du_seuil_diminue_sans_disparaitre():
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    vaisseau.base.ajouter_bouclier(12)

    combat.finir_tour_joueur()

    assert vaisseau.base.bouclier == 6  # 12 > SEUIL_DISSIPATION_BOUCLIER : ceil(12/2)=6


def test_bouclier_ennemi_se_dissipe_a_chaque_tour_ennemi():
    combat, _vaisseau, flotte = _nouveau_combat(degats_ennemi=0)
    ennemi = flotte.ennemis_vivants()[0]
    ennemi.ajouter_bouclier(20)

    combat.finir_tour_joueur()
    assert ennemi.bouclier == 10  # 20 > seuil : ceil(20/2)

    combat.finir_tour_joueur()
    assert ennemi.bouclier == 5  # 10 > seuil : ceil(10/2)

    combat.finir_tour_joueur()
    assert ennemi.bouclier == 0  # 5 <= SEUIL_DISSIPATION_BOUCLIER


# --- Bouclier adaptatif (Blindage, specs.md 12.4) ---


def test_bouclier_adaptatif_donne_un_bouclier_proportionnel_aux_pv_max():
    combat, vaisseau, _flotte = _nouveau_combat(pv_base=15)
    combat.joueur.deck.main = [CARTE_BOUCLIER_ADAPTATIF]
    combat.joueur.electricite = 2

    resultat = combat.jouer_carte(CARTE_BOUCLIER_ADAPTATIF, vaisseau.base)

    assert resultat == [(vaisseau.base, 12)]  # round(15 * 80 / 100)
    assert vaisseau.base.bouclier == 12


# --- Fonds de tiroir (Generateur, specs.md 12.8) ---


def test_fonds_de_tiroir_donne_de_l_electricite_par_module_actif():
    vaisseau = _vaisseau_complet()
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau)
    combat.joueur.deck.main = [CARTE_FONDS_DE_TIROIR]
    combat.joueur.electricite = 10

    resultat = combat.jouer_carte(CARTE_FONDS_DE_TIROIR, None)  # ALLIES_MULTIPLES, sans clic

    assert resultat == [(None, 5)]  # 1 x (base + 4 modules equipes)
    assert combat.joueur.electricite == 14  # 10 - 1 (cout) + 5 (gain)


def test_fonds_de_tiroir_ignore_les_modules_detruits():
    vaisseau = _vaisseau_complet()
    vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).pv = 0
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau)
    combat.joueur.deck.main = [CARTE_FONDS_DE_TIROIR]
    combat.joueur.electricite = 10

    resultat = combat.jouer_carte(CARTE_FONDS_DE_TIROIR, None)

    assert resultat == [(None, 4)]  # 4 modules vivants sur 5


# --- Leurre (Lanceur de missiles, specs.md 12.6) ---


def test_leurre_pose_le_flag_sans_toucher_au_bouclier():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_LEURRE]
    combat.joueur.electricite = 3

    resultat = combat.jouer_carte(CARTE_LEURRE, vaisseau.base)

    assert resultat == [(vaisseau.base, 0)]
    assert vaisseau.base.leurre_actif is True
    assert vaisseau.base.bouclier == 0


def test_leurre_annule_totalement_la_prochaine_attaque_puis_se_consomme():
    combat, vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]
    combat.joueur.deck.main = [CARTE_LEURRE]
    combat.joueur.electricite = 3
    combat.jouer_carte(CARTE_LEURRE, vaisseau.base)

    attaques = combat.finir_tour_joueur()

    assert attaques == [(POSITION_ENNEMI, ennemi, vaisseau.base, 0, "degats")]
    assert vaisseau.base.pv == 15  # aucun degat, meme sans bouclier
    assert vaisseau.base.leurre_actif is False  # consomme par cette attaque

    attaques_suivantes = combat.finir_tour_joueur()

    assert attaques_suivantes == [(POSITION_ENNEMI, ennemi, vaisseau.base, 7, "degats")]  # plus de leurre : degats normaux
    assert vaisseau.base.pv == 15 - 7


# --- Ennemi a plusieurs emplacements (specs.md 3.2, ex. Boss des pirates) ---

CARTE_COLONNE_ARRIERE = Carte(
    nom="Ligne arriere", image=IMG, type=TypeCarte.DEBUFF, cible=CibleCarte.COLONNE_ARRIERE_ENNEMIE,
    cout=1, valeur=100, action=ActionCarte.VULNERABILITE, duree=1,
)


def _boss_deux_emplacements(pv_max: int = 150, actions: list | None = None) -> dict[Position, Ennemi]:
    """Un ennemi range aux 2 Positions Avant/Arriere de la rangee du milieu (specs.md 3.2)."""
    boss = Ennemi(pv_max=pv_max, actions=actions or [], nom="Boss", emplacements=2)
    return {
        Position(Colonne.AVANT, Rangee.MID): boss,
        Position(Colonne.ARRIERE, Rangee.MID): boss,
    }


def test_ennemis_multiples_ne_touche_qu_une_fois_un_ennemi_a_2_emplacements():
    ennemis = _boss_deux_emplacements()
    combat, _vaisseau, flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_MITRAILLER]
    combat.joueur.electricite = 2
    boss = flotte.ennemis_vivants()[0]

    resultat = combat.jouer_carte(CARTE_MITRAILLER)  # CIBLES_SANS_CLIC, pas de cible cliquee

    assert len(resultat) == 1
    assert boss.pv == boss.pv_max - CARTE_MITRAILLER.valeur


def test_ligne_ennemie_ne_touche_qu_une_fois_un_ennemi_a_2_emplacements():
    ennemis = _boss_deux_emplacements()
    combat, _vaisseau, flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_PERCER]
    combat.joueur.electricite = 2
    boss = flotte.ennemis_vivants()[0]

    resultat = combat.jouer_carte(CARTE_PERCER, boss)

    assert len(resultat) == 1
    assert boss.pv == boss.pv_max - CARTE_PERCER.valeur


def test_colonne_avant_ennemie_accepte_un_clic_sur_un_ennemi_a_2_emplacements():
    ennemis = _boss_deux_emplacements()
    combat, _vaisseau, flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT]
    combat.joueur.electricite = 2
    boss = flotte.ennemis_vivants()[0]

    resultat = combat.jouer_carte(CARTE_COLONNE_AVANT, boss)

    assert len(resultat) == 1
    assert any(buff.action == ActionCarte.VULNERABILITE for buff in boss.buffs_actifs)


def test_colonne_arriere_ennemie_accepte_aussi_un_clic_sur_le_meme_ennemi():
    """Un ennemi a 2 emplacements occupe l'Avant ET l'Arriere de sa rangee (specs.md 3.2) : un
    clic dessus doit etre une cible valide pour les deux cartes de colonne, pas seulement une."""
    ennemis = _boss_deux_emplacements()
    combat, _vaisseau, flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_COLONNE_ARRIERE]
    combat.joueur.electricite = 2
    boss = flotte.ennemis_vivants()[0]

    resultat = combat.jouer_carte(CARTE_COLONNE_ARRIERE, boss)

    assert len(resultat) == 1


def test_tour_ennemi_n_execute_qu_une_fois_les_actions_d_un_ennemi_a_2_emplacements():
    action = ActionEnnemi(type=TypeActionEnnemi.ATTAQUE, cible=CibleActionEnnemi.TOUS_MODULES_JOUEUR, valeur=5)
    ennemis = _boss_deux_emplacements(actions=[action])
    vaisseau = _vaisseau_complet(pv=50)
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis, vaisseau=vaisseau)

    combat.finir_tour_joueur()

    # 5 modules (base + 4 equipes) x 5 degats chacun - le double si l'action se declenchait
    # deux fois (une par emplacement occupe) au lieu d'une seule.
    assert vaisseau.base.pv == 45
    assert vaisseau.module_en(Colonne.AVANT, Rangee.GAUCHE).pv == 45


# --- Bouclier miroir sur un ennemi allie (specs.md 13, ennemi Miroir - pose desormais sur un
# allie ennemi plutot que sur un module du joueur) ---


def _pose_bouclier_miroir_ennemie() -> ActionEnnemi:
    return ActionEnnemi(
        type=TypeActionEnnemi.POSE_BUFF,
        cible=CibleActionEnnemi.COLONNE_AVANT_SINON_ARRIERE_ENNEMIE,
        valeur=5,
        action_buff=ActionCarte.BOUCLIER_MIROIR,
    )


def test_pose_bouclier_miroir_cible_un_ennemi_en_priorite_avant():
    miroir = Ennemi(pv_max=50, actions=[_pose_bouclier_miroir_ennemie()], nom="Miroir")
    protege_avant = Ennemi(pv_max=20, nom="Protege avant")
    ennemis = {
        Position(Colonne.ARRIERE, Rangee.GAUCHE): miroir,
        Position(Colonne.AVANT, Rangee.DROITE): protege_avant,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis, aleatoire=random.Random(1))

    combat.finir_tour_joueur()

    assert any(buff.action == ActionCarte.BOUCLIER_MIROIR for buff in protege_avant.buffs_actifs)
    assert not any(buff.action == ActionCarte.BOUCLIER_MIROIR for buff in miroir.buffs_actifs)


def test_pose_bouclier_miroir_se_cible_lui_meme_si_seul_ennemi_vivant():
    miroir = Ennemi(pv_max=50, actions=[_pose_bouclier_miroir_ennemie()], nom="Miroir")
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): miroir}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis, aleatoire=random.Random(1))

    combat.finir_tour_joueur()

    assert any(buff.action == ActionCarte.BOUCLIER_MIROIR for buff in miroir.buffs_actifs)


def test_bouclier_miroir_choisit_le_module_de_reflet_des_la_pose():
    """Le module qui recevra les degats renvoyes est tire au moment de la pose (tour ennemi),
    pas a la resolution de l'attaque joueur - il doit etre visible dans l'infobulle avant meme
    que le joueur n'attaque (decision utilisateur)."""
    miroir = Ennemi(pv_max=50, actions=[_pose_bouclier_miroir_ennemie()], nom="Miroir")
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): miroir}
    vaisseau = _vaisseau_complet(pv=20)
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis, vaisseau=vaisseau, aleatoire=random.Random(1))

    combat.finir_tour_joueur()

    buff = next(b for b in miroir.buffs_actifs if b.action == ActionCarte.BOUCLIER_MIROIR)
    modules_possibles = [vaisseau.base, *vaisseau.modules_equipes().values()]
    assert buff.cible_reflet in modules_possibles


def test_bouclier_miroir_renvoie_les_degats_de_l_attaque_joueur_vers_le_module_tire():
    miroir = Ennemi(pv_max=50, nom="Miroir")
    cible_reflet = Module(pv_max=20, nom="Cible")
    miroir.appliquer_buff(ActionCarte.BOUCLIER_MIROIR, 5, tours=None, cible_reflet=cible_reflet)
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): miroir}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE]  # ENNEMI_UNIQUE, valeur 7
    combat.joueur.electricite = 3

    resultat = combat.jouer_carte(CARTE_ATTAQUE, miroir)

    # 5 renvoyes vers cible_reflet (bouclier entierement consomme), 2 restants a Miroir.
    assert cible_reflet.pv == 20 - 5
    assert miroir.pv == 50 - 2
    assert (cible_reflet, 5) in resultat
    assert (miroir, 2) in resultat
    assert not any(buff.action == ActionCarte.BOUCLIER_MIROIR for buff in miroir.buffs_actifs)


def test_bouclier_miroir_absorbe_totalement_si_inferieur_a_sa_valeur():
    miroir = Ennemi(pv_max=50, nom="Miroir")
    cible_reflet = Module(pv_max=20, nom="Cible")
    miroir.appliquer_buff(ActionCarte.BOUCLIER_MIROIR, 10, tours=None, cible_reflet=cible_reflet)
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): miroir}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE]  # valeur 7
    combat.joueur.electricite = 3

    combat.jouer_carte(CARTE_ATTAQUE, miroir)

    assert cible_reflet.pv == 20 - 7
    assert miroir.pv == 50  # rien subi, tout absorbe
    buff = next(b for b in miroir.buffs_actifs if b.action == ActionCarte.BOUCLIER_MIROIR)
    assert buff.valeur == 3  # 10 - 7 restant, buff toujours actif


def test_bouclier_miroir_plusieurs_instances_renvoient_chacune_vers_son_propre_module():
    miroir = Ennemi(pv_max=50, nom="Miroir")
    module_a = Module(pv_max=20, nom="A")
    module_b = Module(pv_max=20, nom="B")
    miroir.appliquer_buff(ActionCarte.BOUCLIER_MIROIR, 3, tours=None, cible_reflet=module_a)
    miroir.appliquer_buff(ActionCarte.BOUCLIER_MIROIR, 3, tours=None, cible_reflet=module_b)
    ennemis = {Position(Colonne.AVANT, Rangee.GAUCHE): miroir}
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    carte = Carte(nom="Gros coup", image=IMG, type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=8)
    combat.joueur.deck.main = [carte]
    combat.joueur.electricite = 3

    combat.jouer_carte(carte, miroir)

    assert module_a.pv == 20 - 3
    assert module_b.pv == 20 - 3
    assert miroir.pv == 50 - 2  # 8 - 3 - 3 = 2 restant
