"""
Ecran "voir le deck en entier" (specs.md 6/10.3), ouvert depuis l'ecran de partie (bouton "Voir le
deck"). Fenetre pyglet independante comme les autres ecrans du parcours ; l'ecran de partie ayant
deja ete ferme avant l'ouverture de celui-ci (main.py), le bouton "Retour" (self.termine) est le
seul moyen d'y revenir - pas de fermeture de fenetre native qui rouvrirait quoi que ce soit.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte
from src.ui import carte_visuel
from src.ui.commun import regrouper_cartes
from src.ui.fenetre import (
    FOND_IMAGE,
    HAUTEUR_FENETRE,
    LARGEUR_FENETRE,
    _sprite_etire,
)

COULEUR_TEXTE = (255, 255, 255)

COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)

LARGEUR_CARTE_DECK = 130
HAUTEUR_CARTE_DECK = carte_visuel.hauteur_carte(LARGEUR_CARTE_DECK)
ESPACEMENT_CARTE = 18
COLONNES = 8
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 110

# Bouton "Retour" en haut a droite (plutot qu'en bas, ou la place depend de la taille du deck) -
# seul moyen de fermer cet ecran et de revenir a l'ecran de partie (specs.md 10.3), qui a ete
# ferme avant l'ouverture de celui-ci (main.py).
LARGEUR_BOUTON = 140
HAUTEUR_BOUTON = 40
X_BOUTON = LARGEUR_FENETRE - LARGEUR_BOUTON - 20
Y_BOUTON = HAUTEUR_FENETRE - HAUTEUR_BOUTON - 20


def _rect_bouton() -> tuple[float, float, float, float]:
    return X_BOUTON, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _grille_depart_x() -> float:
    largeur_totale = COLONNES * LARGEUR_CARTE_DECK + (COLONNES - 1) * ESPACEMENT_CARTE
    return (LARGEUR_FENETRE - largeur_totale) / 2


def _rect_carte(index: int) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) de la carte a cet index, grille de COLONNES
    colonnes remplie ligne par ligne, centree horizontalement dans la fenetre."""
    colonne = index % COLONNES
    ligne = index // COLONNES
    x = _grille_depart_x() + colonne * (LARGEUR_CARTE_DECK + ESPACEMENT_CARTE)
    y = Y_HAUT_GRILLE - HAUTEUR_CARTE_DECK - ligne * (HAUTEUR_CARTE_DECK + ESPACEMENT_CARTE)
    return x, y, LARGEUR_CARTE_DECK, HAUTEUR_CARTE_DECK


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranDeck(pyglet.window.Window):
    """Grille de cartes (deck possede, ou toutes les cartes d'un combat en cours), regroupees par
    carte et module (carte, quantite). Survol d'une carte : sa description complete et le module
    auquel elle est rattachee (`noms_modules` : exemplaire -> nom)."""

    def __init__(self, cartes: list[Carte], noms_modules: dict[str, str] | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.groupes = regrouper_cartes(cartes)
        self.noms_modules = noms_modules or {}
        self.index_survole: int | None = None
        self.bouton_retour_survole: bool = False
        self.termine: bool = False

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        elements = [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        elements.append(
            pyglet.text.Label(
                "Deck",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 50,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, (carte, quantite) in enumerate(self.groupes):
            elements.extend(self._dessiner_carte(index, carte, quantite, lot))
        if self.index_survole is not None:
            carte, _quantite = self.groupes[self.index_survole]
            elements.extend(self._dessiner_carte_agrandie(carte, lot))
        elements.extend(self._dessiner_bouton_retour(lot))
        return elements

    def _dessiner_bouton_retour(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_retour_survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "Retour",
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=14,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [rectangle, texte]

    def _dessiner_carte(self, index: int, carte: Carte, quantite: int, lot: pyglet.graphics.Batch) -> list:
        return carte_visuel.dessiner_carte_de_grille(
            carte, _rect_carte(index), quantite, index == self.index_survole, lot, ordre=1 + index
        )

    def _dessiner_carte_agrandie(self, carte: Carte, lot: pyglet.graphics.Batch) -> list:
        """Carte survolee en grand a cote d'elle, avec le module auquel elle est rattachee."""
        nom_module = self.noms_modules.get(carte.exemplaire_module)
        lignes = [f"Module : {nom_module}"] if nom_module else []
        return carte_visuel.dessiner_carte_agrandie_a_cote(
            carte, _rect_carte(self.index_survole), lignes, lot, carte_visuel.GROUPE_CARTE_AGRANDIE, LARGEUR_FENETRE, HAUTEUR_FENETRE
        )

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)
        self.bouton_retour_survole = _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True

    def _index_a(self, x: int, y: int) -> int | None:
        for index in range(len(self.groupes)):
            if _point_dans_rectangle(x, y, *_rect_carte(index)):
                return index
        return None
