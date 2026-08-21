"""
Tests unitaires pour le moteur de combat (src/gameplay/combat.py).
"""

import random

from src.gameplay.carte import ActionCarte, Carte, CibleCarte, TypeCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.deck import Deck
from src.gameplay.ennemi import Ennemi
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

POSITION_ENNEMI = Position(Colonne.AVANT, Rangee.GAUCHE)


def _nouveau_combat(pv_base: int = 15, pv_ennemi: int = 15, degats_ennemi: int = 7, ennemis: dict | None = None):
    cartes = [CARTE_ATTAQUE] * 5 + [CARTE_BOUCLIER] * 3 + [CARTE_REPARATION]
    deck = Deck(cartes=cartes, generateur_aleatoire=random.Random(0))
    vaisseau = Vaisseau(base=Module(pv_max=pv_base))
    joueur = Joueur(vaisseau=vaisseau, deck=deck, electricite_par_tour=3)
    if ennemis is None:
        ennemis = {POSITION_ENNEMI: Ennemi(pv_max=pv_ennemi, degats_attaque=degats_ennemi)}
    flotte = Flotte(ennemis)
    combat = Combat(joueur=joueur, flotte=flotte)
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
    e1 = Ennemi(pv_max=7, degats_attaque=4)
    e2 = Ennemi(pv_max=7, degats_attaque=4)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): e1,
        Position(Colonne.AVANT, Rangee.DROITE): e2,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_ATTAQUE]

    combat.jouer_carte(CARTE_ATTAQUE, e1)

    assert combat.etat == EtatCombat.EN_COURS


def test_victoire_seulement_quand_tous_les_ennemis_sont_detruits():
    e1 = Ennemi(pv_max=7, degats_attaque=4)
    e2 = Ennemi(pv_max=7, degats_attaque=4)
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
    flotte = Flotte({POSITION_ENNEMI: Ennemi(pv_max=15, degats_attaque=7)})
    combat = Combat(joueur=joueur, flotte=flotte)

    module_fragile.subir_degats(100)  # detruit un module non-base, hors du moteur de combat
    combat.finir_tour_joueur()  # declenche la verification de fin de combat

    assert module_fragile.est_detruit()
    assert combat.etat == EtatCombat.EN_COURS  # la base (15 - 7 = 8 PV) est toujours en vie


def test_finir_tour_joueur_renvoie_les_attaques_resolues():
    combat, vaisseau, flotte = _nouveau_combat()
    ennemi = flotte.ennemis_vivants()[0]

    attaques = combat.finir_tour_joueur()

    assert attaques == [(POSITION_ENNEMI, ennemi, vaisseau.base, 7)]


def test_plusieurs_ennemis_attaquent_dans_le_meme_tour():
    e1 = Ennemi(pv_max=15, degats_attaque=4)
    e2 = Ennemi(pv_max=15, degats_attaque=6)
    position_e1 = Position(Colonne.AVANT, Rangee.GAUCHE)
    position_e2 = Position(Colonne.AVANT, Rangee.DROITE)
    combat, vaisseau, _flotte = _nouveau_combat(ennemis={position_e1: e1, position_e2: e2})

    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 4 - 6


def test_arret_immediat_si_la_base_est_detruite_en_cours_de_tour():
    e1 = Ennemi(pv_max=15, degats_attaque=20)  # detruit la base d'un coup
    e2 = Ennemi(pv_max=15, degats_attaque=5)
    position_e1 = Position(Colonne.AVANT, Rangee.GAUCHE)
    position_e2 = Position(Colonne.AVANT, Rangee.DROITE)
    combat, vaisseau, _flotte = _nouveau_combat(pv_base=10, ennemis={position_e1: e1, position_e2: e2})

    attaques = combat.finir_tour_joueur()

    assert combat.etat == EtatCombat.DEFAITE
    assert attaques == [(position_e1, e1, vaisseau.base, 10)]  # e2 n'a pas agi, degats plafonnes aux 10 PV restants


# --- Cibles multiples (LIGNE_ENNEMIE, ALLIES_MULTIPLES, ENNEMIS_MULTIPLES) ---


def test_ligne_ennemie_touche_l_avant_et_l_arriere_de_la_rangee():
    avant = Ennemi(pv_max=10, degats_attaque=4)
    arriere = Ennemi(pv_max=10, degats_attaque=4)
    autre_rangee = Ennemi(pv_max=10, degats_attaque=4)
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
    seul = Ennemi(pv_max=10, degats_attaque=4)
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
    flotte = Flotte({POSITION_ENNEMI: Ennemi(pv_max=15, degats_attaque=7)})
    combat = Combat(joueur=joueur, flotte=flotte)
    combat.joueur.deck.main = [CARTE_PROTEGER]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_PROTEGER)  # pas de cible a fournir

    assert vaisseau.base.bouclier == 4
    assert module_equipe.bouclier == 4
    assert module_detruit.bouclier == 0


def test_mitrailler_touche_tous_les_ennemis_vivants():
    e1 = Ennemi(pv_max=15, degats_attaque=4)
    e2 = Ennemi(pv_max=15, degats_attaque=4)
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
    avant_g = Ennemi(pv_max=15, degats_attaque=1)
    avant_d = Ennemi(pv_max=15, degats_attaque=1)
    arriere_g = Ennemi(pv_max=15, degats_attaque=1)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): avant_g,
        Position(Colonne.AVANT, Rangee.DROITE): avant_d,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): arriere_g,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_COLONNE_AVANT, avant_g)  # clic sur un ennemi de la colonne avant

    assert avant_g.debuffs_actifs[0].valeur == 100
    assert avant_d.debuffs_actifs[0].valeur == 100
    assert arriere_g.debuffs_actifs == []  # colonne arriere non touchee


def test_colonne_avant_ennemie_refuse_un_clic_sur_l_arriere():
    avant = Ennemi(pv_max=15, degats_attaque=1)
    arriere = Ennemi(pv_max=15, degats_attaque=1)
    ennemis = {
        Position(Colonne.AVANT, Rangee.GAUCHE): avant,
        Position(Colonne.ARRIERE, Rangee.GAUCHE): arriere,
    }
    combat, _vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT]
    combat.joueur.electricite = 2

    combat.jouer_carte(CARTE_COLONNE_AVANT, arriere)  # clic sur l'arriere -> refuse

    assert arriere.debuffs_actifs == []
    assert avant.debuffs_actifs == []


# --- Buff (Blindage, specs.md 12.3/12.5) ---


def test_buff_bouclier_perpetuel_donne_du_bouclier_immediatement():
    combat, vaisseau, _flotte = _nouveau_combat()
    combat.joueur.deck.main = [CARTE_BOUCLIER_PERPETUEL]
    combat.joueur.electricite = 5

    resultat = combat.jouer_carte(CARTE_BOUCLIER_PERPETUEL, None)  # Module Principal, sans clic

    assert resultat == [(vaisseau.base, 10)]
    assert vaisseau.base.bouclier == 10


def test_buff_bouclier_perpetuel_se_redeclenche_a_chaque_tour_joueur_sans_expirer():
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    combat.joueur.deck.main = [CARTE_BOUCLIER_PERPETUEL]
    combat.joueur.electricite = 5
    combat.jouer_carte(CARTE_BOUCLIER_PERPETUEL, None)

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 20  # 10 a la pose + 10 au debut du tour suivant

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 30  # persistant : ne s'arrete jamais
    assert len(vaisseau.base.buffs_actifs) == 1
