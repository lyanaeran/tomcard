"""
Tests unitaires pour les fonctions libres de src/gameplay/carte.py.
"""

from src.gameplay.carte import Carte, CibleCarte, TypeCarte, regrouper_cartes

CARTE_ATTAQUE = Carte(id="TEST_ATTAQUE", nom="Attaque", image="test.png", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=1, valeur=7)
CARTE_BOUCLIER = Carte(id="TEST_BOUCLIER", nom="Bouclier", image="test.png", type=TypeCarte.DEFENSE, cible=CibleCarte.ALLIE_UNIQUE, cout=1, valeur=5)


def test_regrouper_cartes_compte_les_doublons():
    cartes = [CARTE_ATTAQUE.copie(), CARTE_BOUCLIER.copie(), CARTE_ATTAQUE.copie()]

    groupes = regrouper_cartes(cartes)

    assert len(groupes) == 2
    carte_attaque, quantite_attaque = next(g for g in groupes if g[0].nom == "Attaque")
    assert quantite_attaque == 2
    carte_bouclier, quantite_bouclier = next(g for g in groupes if g[0].nom == "Bouclier")
    assert quantite_bouclier == 1


def test_regrouper_cartes_distingue_deux_modeles_de_meme_nom():
    """Regroupement par id, pas par nom : deux modeles homonymes restent deux entrees."""
    autre_attaque = Carte(id="TEST_ATTAQUE_2", nom="Attaque", image="test.png", type=TypeCarte.ATTAQUE, cible=CibleCarte.ENNEMI_UNIQUE, cout=2, valeur=12)
    cartes = [CARTE_ATTAQUE.copie(), autre_attaque.copie(), CARTE_ATTAQUE.copie()]

    groupes = regrouper_cartes(cartes)

    assert [(carte.id, quantite) for carte, quantite in groupes] == [("TEST_ATTAQUE", 2), ("TEST_ATTAQUE_2", 1)]


def test_regrouper_cartes_liste_vide():
    assert regrouper_cartes([]) == []


def test_regrouper_cartes_conserve_l_ordre_de_premiere_apparition():
    cartes = [CARTE_BOUCLIER.copie(), CARTE_ATTAQUE.copie(), CARTE_BOUCLIER.copie()]

    groupes = regrouper_cartes(cartes)

    assert [carte.nom for carte, _ in groupes] == ["Bouclier", "Attaque"]
