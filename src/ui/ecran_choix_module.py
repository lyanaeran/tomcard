"""
Ecran de choix de module (parcours, Niveau 1 - specs.md paragraphe 2.3). Fenetre pyglet
independante de FenetreCombat pour l'instant : le parcours (enchainement des niveaux) n'est pas
encore implemente, cf. specs.md 2.3 - cet ecran sera reliee a l'orchestration du parcours une
fois celle-ci ecrite.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.donnees import SpecModule
from src.gameplay.partie import Partie, deck_de_la_partie
from src.ui import barre_laterale
from src.ui.ecran_deck import EcranDeck
from src.ui.ecran_vaisseau import EcranVaisseau
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_ajuste, _sprite_etire

COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_SURVOLEE = (255, 255, 255)
COULEUR_NOM_MODULE = (255, 220, 120)
COULEUR_DESCRIPTION = (220, 220, 225)
COULEUR_TEXTE = (255, 255, 255)
OPACITE_FOND_CARTE = 190

LARGEUR_CARTE_MODULE = 320
IMAGE_TAILLE = 220
ESPACEMENT_CARTES = 60
Y_IMAGE = 400
HAUTEUR_CARTE = IMAGE_TAILLE + 120


def _rect_candidat(index: int) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) de la case cliquable du candidat a cet index (0-2),
    3 cases centrees horizontalement dans la fenetre."""
    largeur_totale = 3 * LARGEUR_CARTE_MODULE + 2 * ESPACEMENT_CARTES
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE_MODULE + ESPACEMENT_CARTES)
    return x, Y_IMAGE - 20, LARGEUR_CARTE_MODULE, HAUTEUR_CARTE


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranChoixModule(pyglet.window.Window):
    """Ecran de choix d'un nouveau module parmi 3 candidats (specs.md 2.3, Niveau 1)."""

    def __init__(self, candidats: list[SpecModule], partie: Partie):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.candidats = candidats
        self.partie = partie
        self.index_survole: int | None = None
        self.survole_barre: str | None = None
        self.module_choisi: SpecModule | None = None

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
                f"Nouveau module - Niveau {self.partie.niveau}",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 60,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, candidat in enumerate(self.candidats):
            elements.extend(self._dessiner_candidat(index, candidat, lot))
        elements.append(
            pyglet.text.Label(
                "Choisissez un nouveau module pour votre vaisseau.",
                x=LARGEUR_FENETRE / 2,
                y=150,
                anchor_x="center",
                anchor_y="center",
                font_size=18,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        elements.extend(barre_laterale.dessiner(self.partie, self.survole_barre, lot))
        return elements

    def _dessiner_candidat(self, index: int, candidat: SpecModule, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_candidat(index)
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

        sprite = _sprite_ajuste(candidat.image, cx - IMAGE_TAILLE / 2, Y_IMAGE + 20, IMAGE_TAILLE, IMAGE_TAILLE, lot)

        nom = pyglet.text.Label(
            candidat.nom,
            x=cx,
            y=Y_IMAGE + 5,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(*COULEUR_NOM_MODULE, 255),
            batch=lot,
        )
        description = pyglet.text.Label(
            candidat.description,
            x=cx,
            y=Y_IMAGE - 30,
            anchor_x="center",
            anchor_y="top",
            font_size=12,
            color=(*COULEUR_DESCRIPTION, 255),
            multiline=True,
            width=LARGEUR_CARTE_MODULE - 30,
            align="center",
            batch=lot,
        )
        return [cadre, sprite, nom, description]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)
        self.survole_barre = barre_laterale.bouton_survole(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        bouton_barre = barre_laterale.bouton_survole(x, y)
        if bouton_barre == "deck":
            barre_laterale.ouvrir_survol(EcranDeck(deck_de_la_partie(self.partie)))
            return
        if bouton_barre == "vaisseau":
            barre_laterale.ouvrir_survol(EcranVaisseau(self.partie))
            return
        index = self._index_a(x, y)
        if index is not None:
            self.module_choisi = self.candidats[index]

    def _index_a(self, x: int, y: int) -> int | None:
        for index in range(len(self.candidats)):
            if _point_dans_rectangle(x, y, *_rect_candidat(index)):
                return index
        return None
