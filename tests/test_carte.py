"""
Tests unitaires pour les fonctions libres de src/gameplay/carte.py.
"""

from src.gameplay.carte import Carte, CibleCarte, TypeCarte, regrouper_cartes

CARTE_ATTAQUE = Carte(nom="Attaque", image="test.png", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=7)
CARTE_BOUCLIER = Carte(nom="Bouclier", image="test.png", type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE_UNIQUE, cout=1, valeur=5)


def test_regrouper_cartes_compte_les_doublons():
    cartes = [CARTE_ATTAQUE.copie(), CARTE_BOUCLIER.copie(), CARTE_ATTAQUE.copie()]

    groupes = regrouper_cartes(cartes)

    assert len(groupes) == 2
    carte_attaque, quantite_attaque = next(g for g in groupes if g[0].nom == "Attaque")
    assert quantite_attaque == 2
    carte_bouclier, quantite_bouclier = next(g for g in groupes if g[0].nom == "Bouclier")
    assert quantite_bouclier == 1


def test_regrouper_cartes_liste_vide():
    assert regrouper_cartes([]) == []


def test_regrouper_cartes_conserve_l_ordre_de_premiere_apparition():
    cartes = [CARTE_BOUCLIER.copie(), CARTE_ATTAQUE.copie(), CARTE_BOUCLIER.copie()]

    groupes = regrouper_cartes(cartes)

    assert [carte.nom for carte, _ in groupes] == ["Bouclier", "Attaque"]
