"""
Tests unitaires pour src/gameplay/flotte_new.py (ennemis de la refonte sur la grille ennemie).
"""

import random

import pytest

from src.gameplay.ennemi_new import charger_ennemis_new
from src.gameplay.flotte_new import (
    ID_BOSS,
    NOMBRE_ENNEMIS_ASTEROIDES,
    FlotteNew,
    flotte_asteroides,
    flotte_boss,
    flotte_prime,
    nombre_ennemis_prime,
    placer_ennemis,
)
from src.gameplay.position import Colonne, Position, Rangee


def _ennemi(id_ennemi):
    return charger_ennemis_new()[id_ennemi].pour_combat()


def test_ordre_de_jeu_avant_puis_arriere_de_droite_a_gauche():
    """Decision utilisateur : la rangee gauche est en bas de l'ecran."""
    arriere_droite, avant_gauche, avant_droite = (_ennemi("ENM_PAT_LE_PIRATE") for _ in range(3))
    flotte = FlotteNew({
        Position(Colonne.ARRIERE, Rangee.DROITE): arriere_droite,
        Position(Colonne.AVANT, Rangee.GAUCHE): avant_gauche,
        Position(Colonne.AVANT, Rangee.DROITE): avant_droite,
    })

    assert flotte.ennemis_vivants() == [avant_droite, avant_gauche, arriere_droite]


def test_un_ennemi_sur_deux_cases_compte_une_fois_et_est_dans_les_deux_colonnes():
    boss = _ennemi("ENM_BOSS_PIRATES")
    flotte = FlotteNew({Position(Colonne.AVANT, Rangee.MID): boss, Position(Colonne.ARRIERE, Rangee.MID): boss})

    assert flotte.ennemis_vivants() == [boss]
    assert flotte.ennemis_vivants_de_colonne(Colonne.ARRIERE) == [boss]
    assert flotte.rangee_de(boss) == Rangee.MID


def test_le_nombre_de_cases_doit_correspondre_aux_emplacements():
    with pytest.raises(ValueError, match="1 case"):
        FlotteNew({Position(Colonne.AVANT, Rangee.MID): _ennemi("ENM_BOSS_PIRATES")})


def test_la_flotte_est_vide_quand_tous_les_ennemis_sont_detruits():
    pat = _ennemi("ENM_PAT_LE_PIRATE")
    flotte = FlotteNew({Position(Colonne.AVANT, Rangee.MID): pat})

    pat.subir_degats(50)

    assert flotte.est_vide() and flotte.ennemi_en(Position(Colonne.AVANT, Rangee.MID)) is None


def test_les_cases_d_un_ennemi_absent_de_la_flotte_sont_refusees():
    flotte = FlotteNew({Position(Colonne.AVANT, Rangee.MID): _ennemi("ENM_PAT_LE_PIRATE")})

    with pytest.raises(ValueError, match="absent de cette flotte"):
        flotte.cases_de(_ennemi("ENM_PAT_LE_PIRATE"))


# --- Composition des flottes du parcours (refonte-branchement.md 2, decision 4) ---


def _colonnes(flotte: FlotteNew, id_ennemi: str) -> list[Colonne]:
    return [flotte.cases_de(e)[0].colonne for e in flotte.ennemis if e.id == id_ennemi]


def test_nombre_ennemis_prime_1_jusqu_au_niveau_5_puis_2():
    assert [nombre_ennemis_prime(niveau) for niveau in range(1, 10)] == [1, 1, 1, 1, 1, 2, 2, 2, 2]


def test_placer_ennemis_protecteurs_a_l_avant_proteges_a_l_arriere():
    for graine in range(10):
        flotte = placer_ennemis([_ennemi("ENM_LE_NETTOYEUR"), _ennemi("ENM_PETIT_JEAN"), _ennemi("ENM_PAT_LE_PIRATE")], random.Random(graine))

        assert _colonnes(flotte, "ENM_PETIT_JEAN") == [Colonne.AVANT]
        assert _colonnes(flotte, "ENM_LE_NETTOYEUR") == [Colonne.ARRIERE]
        # Les autres d'abord a l'avant
        assert _colonnes(flotte, "ENM_PAT_LE_PIRATE") == [Colonne.AVANT]


def test_placer_ennemis_un_4e_protecteur_passe_a_l_arriere():
    flotte = placer_ennemis([_ennemi("ENM_PETIT_JEAN") for _ in range(4)], random.Random(1))

    assert sorted(_colonnes(flotte, "ENM_PETIT_JEAN"), key=lambda c: c.value) == [Colonne.AVANT] * 3 + [Colonne.ARRIERE]


def test_placer_ennemis_un_4e_protege_passe_a_l_avant():
    flotte = placer_ennemis([_ennemi("ENM_LE_NETTOYEUR") for _ in range(4)], random.Random(1))

    assert sorted(_colonnes(flotte, "ENM_LE_NETTOYEUR"), key=lambda c: c.value) == [Colonne.AVANT] + [Colonne.ARRIERE] * 3


def test_placer_ennemis_refuse_plus_de_6_ennemis_ou_un_ennemi_de_deux_cases():
    with pytest.raises(ValueError, match="7 ennemis"):
        placer_ennemis([_ennemi("ENM_PAT_LE_PIRATE") for _ in range(7)], random.Random(1))
    with pytest.raises(ValueError, match="une case"):
        placer_ennemis([_ennemi(ID_BOSS)], random.Random(1))


def test_flotte_prime_selon_le_niveau_sans_le_boss():
    modeles = charger_ennemis_new()
    for graine in range(10):
        for niveau, nombre in ((3, 1), (7, 2)):
            flotte = flotte_prime(modeles, niveau, random.Random(graine))
            assert len(flotte.ennemis) == nombre
            assert all(ennemi.id != ID_BOSS and ennemi.coefficient == 1 for ennemi in flotte.ennemis)


def test_flotte_asteroides_a_3_ennemis():
    assert len(flotte_asteroides(charger_ennemis_new(), random.Random(1)).ennemis) == NOMBRE_ENNEMIS_ASTEROIDES == 3


def test_flotte_boss_sur_les_deux_cases_du_milieu():
    flotte = flotte_boss(charger_ennemis_new())

    (boss,) = flotte.ennemis
    assert boss.id == ID_BOSS
    assert flotte.cases_de(boss) == [Position(Colonne.AVANT, Rangee.MID), Position(Colonne.ARRIERE, Rangee.MID)]
