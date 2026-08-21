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

POSITION_ENNEMI = Position(Colonne.AVANT, Rangee.GAUCHE)


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
        ennemis = {POSITION_ENNEMI: Ennemi(pv_max=pv_ennemi, degats_attaque=degats_ennemi)}
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


# --- Tir allie (Sabotage, specs.md 12.6) ---


def test_tir_allie_redirige_l_attaque_vers_un_autre_ennemi_vivant():
    attaquant = Ennemi(pv_max=15, degats_attaque=7)
    # degats_attaque=0 : isole l'assertion sur le joueur (sinon cible_potentielle
    # attaquerait aussi normalement le joueur de son cote, ce qui est correct mais
    # brouillerait l'assertion "attaquant n'a pas touche le joueur").
    cible_potentielle = Ennemi(pv_max=15, degats_attaque=0)
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
    seul = Ennemi(pv_max=15, degats_attaque=7)
    ennemis = {POSITION_ENNEMI: seul}
    combat, vaisseau, _flotte = _nouveau_combat(ennemis=ennemis)
    combat.joueur.deck.main = [CARTE_TIR_ALLIE]
    combat.joueur.electricite = 3

    combat.jouer_carte(CARTE_TIR_ALLIE, seul)
    combat.finir_tour_joueur()

    assert vaisseau.base.pv == 15 - 7  # aucun autre ennemi disponible : attaque normale


def test_tir_allie_expire_apres_un_tour():
    attaquant = Ennemi(pv_max=15, degats_attaque=7)
    autre = Ennemi(pv_max=15, degats_attaque=0)
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
    attaquant = Ennemi(pv_max=15, degats_attaque=7)
    autre = Ennemi(pv_max=15, degats_attaque=1)
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


# --- Colonne avant alliee (Blindage, specs.md 12.1) ---


def _vaisseau_complet(pv: int = 15) -> Vaisseau:
    return Vaisseau(
        base=Module(pv_max=pv, nom="Base"),
        avant_gauche=Module(pv_max=pv, nom="AvantGauche"),
        avant_droite=Module(pv_max=pv, nom="AvantDroite"),
        arriere_gauche=Module(pv_max=pv, nom="ArriereGauche"),
        arriere_droite=Module(pv_max=pv, nom="ArriereDroite"),
    )


def test_colonne_avant_alliee_protege_seulement_les_deux_modules_avant():
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
    assert vaisseau.base.bouclier == 0


def test_colonne_avant_alliee_refuse_un_clic_sur_l_arriere_ou_la_base():
    vaisseau = _vaisseau_complet()
    combat, _vaisseau, _flotte = _nouveau_combat(vaisseau=vaisseau)
    combat.joueur.deck.main = [CARTE_COLONNE_AVANT_ALLIEE]
    combat.joueur.electricite = 2
    arriere_gauche = vaisseau.module_en(Colonne.ARRIERE, Rangee.GAUCHE)

    resultat_arriere = combat.jouer_carte(CARTE_COLONNE_AVANT_ALLIEE, arriere_gauche)
    resultat_base = combat.jouer_carte(CARTE_COLONNE_AVANT_ALLIEE, vaisseau.base)

    assert resultat_arriere == []
    assert resultat_base == []
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
    combat, vaisseau, _flotte = _nouveau_combat(degats_ennemi=0)
    combat.joueur.deck.main = [CARTE_BLINDAGE_MAXIMAL]
    combat.joueur.electricite = 2
    combat.jouer_carte(CARTE_BLINDAGE_MAXIMAL, None)

    combat.finir_tour_joueur()
    combat.finir_tour_joueur()
    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 32  # 8 a la pose + 8 x 3 tours
    assert vaisseau.base.buffs_actifs == []

    combat.finir_tour_joueur()
    assert vaisseau.base.bouclier == 32  # expire : plus de redeclenchement


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
