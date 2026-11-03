"""
Ecran de choix d'une carte du module fraichement equipe (parcours, specs.md paragraphe 2.3) :
apres le choix de module en debut de partie, 3 candidats sont tires dans le pool jouable non-Base
de ce module (parcours.tirer_candidats_carte_module) et le joueur en choisit une a ajouter a son
deck, ou passe (bouton Passer, specs.md 8.3).

Fond de combat reutilise en placeholder (decision utilisateur), meme convention que
ecran_choix_module.py/ecran_fin_combat.py.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte
from src.gameplay.partie import Partie, deck_de_la_partie
from src.ui import barre_laterale
from src.ui.ecran_deck import EcranDeck
from src.ui.ecran_vaisseau import EcranVaisseau
from src.ui.fenetre import (
    COULEUR_ETOILE_RARETE,
    FOND_IMAGE,
    HAUTEUR_FENETRE,
    LARGEUR_FENETRE,
    _sprite_ajuste,
    _sprite_etire,
    texte_effet_carte,
)

COULEUR_TEXTE = (255, 255, 255)
COULEUR_TITRE = (255, 220, 120)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_SURVOLEE = (255, 255, 255)
COULEUR_BOUTON_PASSER = (60, 66, 82)
COULEUR_CONTOUR_BOUTON_PASSER = (140, 150, 170)
OPACITE_FOND_CARTE = 190

LARGEUR_CARTE = 180
HAUTEUR_CARTE = 340
HAUTEUR_IMAGE = 100
ESPACEMENT_CARTES = 30
Y_CARTE = 220

LARGEUR_BOUTON_PASSER = 140
HAUTEUR_BOUTON_PASSER = 44
X_BOUTON_PASSER = LARGEUR_FENETRE - LARGEUR_BOUTON_PASSER - 40
Y_BOUTON_PASSER = 40


def _rect_candidat(index: int, total: int) -> tuple[float, float, float, float]:
    largeur_totale = total * LARGEUR_CARTE + (total - 1) * ESPACEMENT_CARTES
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE + ESPACEMENT_CARTES)
    return x, Y_CARTE, LARGEUR_CARTE, HAUTEUR_CARTE


def _rect_bouton_passer() -> tuple[float, float, float, float]:
    return X_BOUTON_PASSER, Y_BOUTON_PASSER, LARGEUR_BOUTON_PASSER, HAUTEUR_BOUTON_PASSER


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranChoixCarteModule(pyglet.window.Window):
    """Choix d'une carte candidate du module fraichement equipe (specs.md 2.3), ou Passer."""

    def __init__(self, nom_module: str, candidats: list[Carte], partie: Partie):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.nom_module = nom_module
        self.candidats = candidats
        self.partie = partie
        self.index_survole: int | None = None
        self.survole_passer = False
        self.survole_barre: str | None = None
        self.carte_choisie: Carte | None = None
        # True une fois qu'un choix (carte ou Passer) a ete fait - seul signal a surveiller par
        # l'appelant, meme convention que EcranFinCombat.termine.
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
                f"Nouvelle carte pour {self.nom_module}",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 80,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TITRE, 255),
                batch=lot,
            )
        )
        total = len(self.candidats)
        for index, carte in enumerate(self.candidats):
            elements.extend(self._dessiner_candidat(index, total, carte, lot))
        elements.append(
            pyglet.text.Label(
                "Choisissez une carte a ajouter a votre deck, ou passez.",
                x=LARGEUR_FENETRE / 2,
                y=150,
                anchor_x="center",
                anchor_y="center",
                font_size=18,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        elements.extend(self._dessiner_bouton_passer(lot))
        elements.extend(barre_laterale.dessiner(self.partie, self.survole_barre, lot))
        return elements

    def _dessiner_candidat(self, index: int, total: int, carte: Carte, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_candidat(index, total)
        survole = index == self.index_survole
        cadre = shapes.BorderedRectangle(
            x,
            y,
            largeur,
            hauteur,
            border=2,
            color=COULEUR_FOND_CARTE,
            border_color=COULEUR_CONTOUR_CARTE_SURVOLEE if survole else COULEUR_CONTOUR_CARTE,
            batch=lot,
        )
        cadre.opacity = OPACITE_FOND_CARTE
        cx = x + largeur / 2

        y_image = y + hauteur - 40 - HAUTEUR_IMAGE
        sprite = _sprite_ajuste(carte.image, cx - HAUTEUR_IMAGE / 2, y_image, HAUTEUR_IMAGE, HAUTEUR_IMAGE, lot)

        etoile = pyglet.text.Label(
            "★",
            x=x + 14,
            y=y + hauteur - 14,
            anchor_x="center",
            anchor_y="center",
            font_size=20,
            color=(*COULEUR_ETOILE_RARETE[carte.rarete], 255),
            batch=lot,
        )
        nom = pyglet.text.Label(
            carte.nom,
            x=cx,
            y=y_image - 18,
            anchor_x="center",
            anchor_y="center",
            font_size=14,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        cout = pyglet.text.Label(
            f"⚡{carte.cout}",
            x=cx,
            y=y_image - 40,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
            color=(200, 200, 205, 255),
            batch=lot,
        )
        description = pyglet.text.Label(
            texte_effet_carte(carte),
            x=cx,
            y=y_image - 62,
            anchor_x="center",
            anchor_y="top",
            font_size=10,
            color=(200, 200, 205, 255),
            multiline=True,
            width=largeur - 24,
            align="center",
            batch=lot,
        )
        return [cadre, sprite, etoile, nom, cout, description]

    def _dessiner_bouton_passer(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton_passer()
        cadre = shapes.BorderedRectangle(
            x,
            y,
            largeur,
            hauteur,
            border=2,
            color=COULEUR_BOUTON_PASSER,
            border_color=COULEUR_CONTOUR_CARTE_SURVOLEE if self.survole_passer else COULEUR_CONTOUR_BOUTON_PASSER,
            batch=lot,
        )
        texte = pyglet.text.Label(
            "Passer",
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=15,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [cadre, texte]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)
        self.survole_passer = _point_dans_rectangle(x, y, *_rect_bouton_passer())
        self.survole_barre = barre_laterale.bouton_survole(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        bouton_barre = barre_laterale.bouton_survole(x, y)
        if bouton_barre == "deck":
            barre_laterale.ouvrir_survol(EcranDeck(deck_de_la_partie(self.partie)))
            return
        if bouton_barre == "vaisseau":
            barre_laterale.ouvrir_survol(EcranVaisseau(self.partie))
            return
        if _point_dans_rectangle(x, y, *_rect_bouton_passer()):
            self.termine = True
            return
        index = self._index_a(x, y)
        if index is not None:
            self.carte_choisie = self.candidats[index]
            self.termine = True

    def _index_a(self, x: int, y: int) -> int | None:
        total = len(self.candidats)
        for index in range(total):
            if _point_dans_rectangle(x, y, *_rect_candidat(index, total)):
                return index
        return None
