"""
Ecran de fin de combat (parcours, specs.md paragraphe 2.1/6), fenetre pyglet independante de
FenetreCombat pour l'instant : le parcours (enchainement des niveaux) n'est pas encore
implemente, cf. specs.md 2.3 - meme situation que src/ui/ecran_choix_module.py.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte, RareteCarte
from src.gameplay.donnees import SpecModule
from src.ui.fenetre import (
    COULEUR_ETOILE_RARETE,
    FOND_IMAGE,
    HAUTEUR_FENETRE,
    LARGEUR_FENETRE,
    _sprite_ajuste,
    _sprite_etire,
    texte_effet_carte,
)

COULEUR_DEFAITE = (190, 40, 40)
COULEUR_VICTOIRE = (70, 190, 90)
COULEUR_TEXTE = (255, 255, 255)
COULEUR_NOM_MODULE = (180, 200, 230)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_SURVOLEE = (255, 255, 255)
OPACITE_FOND_CARTE = 190

MESSAGE_DEFAITE = "Pas d'inquietude : vos restes seront recycles, rien ne se perd dans l'espace."
INSTRUCTION_VICTOIRE = "Choisissez une carte a ajouter a votre deck."

LARGEUR_CARTE_RECOMPENSE = 180
HAUTEUR_IMAGE_RECOMPENSE = 100
ESPACEMENT_RECOMPENSE = 30
Y_CARTE_RECOMPENSE = 240
HAUTEUR_CARTE_RECOMPENSE = 340


def _rect_candidat(index: int, total: int) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) de la case cliquable du candidat a cet index,
    `total` cases centrees horizontalement dans la fenetre (2 a 5, cf. specs.md 5)."""
    largeur_totale = total * LARGEUR_CARTE_RECOMPENSE + (total - 1) * ESPACEMENT_RECOMPENSE
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE_RECOMPENSE + ESPACEMENT_RECOMPENSE)
    return x, Y_CARTE_RECOMPENSE, LARGEUR_CARTE_RECOMPENSE, HAUTEUR_CARTE_RECOMPENSE


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranFinCombat(pyglet.window.Window):
    """Ecran de fin de combat : Defaite (message), ou Victoire (choix d'une carte de
    recompense parmi les candidats, un par module utilise - specs.md 2.1/6)."""

    def __init__(self, victoire: bool, candidats: list[tuple[SpecModule, Carte | None]] | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.victoire = victoire
        # Seuls les modules avec un candidat reel sont affiches/cliquables (specs.md 2.1/6 :
        # un pool vide - aucune carte jouable non-Base pour ce module - n'a rien a proposer).
        self.candidats = [(spec, carte) for spec, carte in (candidats or []) if carte is not None]
        self.index_survole: int | None = None
        self.carte_choisie: Carte | None = None
        # True une fois que l'ecran peut etre ferme : defaite (clic n'importe ou), ou victoire
        # avec une carte choisie (ou sans aucun candidat a choisir, cf. on_mouse_press) - un seul
        # signal a surveiller par l'appelant quelle que soit la branche (specs.md 2.4).
        self.termine: bool = False

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        elements = [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        if self.victoire:
            elements.extend(self._dessiner_victoire(lot))
        else:
            elements.extend(self._dessiner_defaite(lot))
        return elements

    def _dessiner_defaite(self, lot: pyglet.graphics.Batch) -> list:
        titre = pyglet.text.Label(
            "DEFAITE",
            x=LARGEUR_FENETRE / 2,
            y=HAUTEUR_FENETRE - 120,
            anchor_x="center",
            anchor_y="center",
            font_size=40,
            color=(*COULEUR_DEFAITE, 255),
            batch=lot,
        )
        message = pyglet.text.Label(
            MESSAGE_DEFAITE,
            x=LARGEUR_FENETRE / 2,
            y=HAUTEUR_FENETRE - 200,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        instruction = pyglet.text.Label(
            "Cliquez pour continuer.",
            x=LARGEUR_FENETRE / 2,
            y=100,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [titre, message, instruction]

    def _dessiner_victoire(self, lot: pyglet.graphics.Batch) -> list:
        elements = [
            pyglet.text.Label(
                "VICTOIRE",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 80,
                anchor_x="center",
                anchor_y="center",
                font_size=40,
                color=(*COULEUR_VICTOIRE, 255),
                batch=lot,
            )
        ]
        total = len(self.candidats)
        for index, (spec, carte) in enumerate(self.candidats):
            elements.extend(self._dessiner_candidat(index, total, spec, carte, lot))
        elements.append(
            pyglet.text.Label(
                INSTRUCTION_VICTOIRE,
                x=LARGEUR_FENETRE / 2,
                y=100,
                anchor_x="center",
                anchor_y="center",
                font_size=18,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        return elements

    def _dessiner_candidat(
        self, index: int, total: int, spec: SpecModule, carte: Carte, lot: pyglet.graphics.Batch
    ) -> list:
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

        nom_module = pyglet.text.Label(
            spec.nom,
            x=cx,
            y=y + hauteur - 18,
            anchor_x="center",
            anchor_y="center",
            font_size=11,
            color=(*COULEUR_NOM_MODULE, 255),
            batch=lot,
        )

        y_image = y + hauteur - 40 - HAUTEUR_IMAGE_RECOMPENSE
        sprite = _sprite_ajuste(carte.image, cx - HAUTEUR_IMAGE_RECOMPENSE / 2, y_image, HAUTEUR_IMAGE_RECOMPENSE, HAUTEUR_IMAGE_RECOMPENSE, lot)

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

        nom_carte = pyglet.text.Label(
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
        return [cadre, nom_module, sprite, etoile, nom_carte, cout, description]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if not self.victoire or not self.candidats:
            # Defaite, ou victoire sans aucun candidat (pool vide pour tous les modules utilises) :
            # un clic n'importe ou suffit a continuer, il n'y a rien a choisir.
            self.termine = True
            return
        index = self._index_a(x, y)
        if index is not None:
            self.carte_choisie = self.candidats[index][1]
            self.termine = True

    def _index_a(self, x: int, y: int) -> int | None:
        if not self.victoire:
            return None
        total = len(self.candidats)
        for index in range(total):
            if _point_dans_rectangle(x, y, *_rect_candidat(index, total)):
                return index
        return None
