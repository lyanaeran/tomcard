"""
Ecran de victoire finale (specs.md 2.4, etape 11) : felicite le joueur a la victoire du Boss du
Niveau 10 (le run s'arrete reellement a ce niveau dans l'etat actuel, specs.md 2), affiche son
deck complet (meme grille que src/ui/ecran_deck.py, specs.md 6 - dupliquee plutot qu'importee,
meme convention que les autres ecrans du parcours qui ont chacun leurs propres petits helpers de
disposition), et propose un bouton "Continuer" qui signale a l'appelant de marquer la partie
TERMINEE et de revenir a l'ecran de partie.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte, regrouper_cartes
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
COULEUR_VICTOIRE = (70, 190, 90)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_SURVOLEE = (255, 255, 255)
COULEUR_QUANTITE = (255, 220, 120)
OPACITE_FOND_CARTE = 190

COULEUR_FOND_PANNEAU = (10, 14, 30)
COULEUR_CONTOUR_PANNEAU = (76, 110, 245)
OPACITE_FOND_PANNEAU = 235

COULEUR_BOUTON = (70, 190, 90)
COULEUR_BOUTON_SURVOLE = (100, 210, 115)

MESSAGE_FELICITATIONS = "Vous avez vaincu le Boss et termine ce run !"

LARGEUR_CARTE_DECK = 130
HAUTEUR_CARTE_DECK = 170
IMAGE_TAILLE = 90
ESPACEMENT_CARTE = 18
COLONNES = 8
# Grille decalee vers le bas par rapport a EcranDeck (Y_HAUT_GRILLE = HAUTEUR_FENETRE - 110) pour
# laisser la place au sous-titre de felicitations sous le titre.
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 150

HAUTEUR_PANNEAU = 70
LARGEUR_PANNEAU = 500

LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 46
Y_BOUTON = 100


def _grille_depart_x() -> float:
    largeur_totale = COLONNES * LARGEUR_CARTE_DECK + (COLONNES - 1) * ESPACEMENT_CARTE
    return (LARGEUR_FENETRE - largeur_totale) / 2


def _rect_carte(index: int) -> tuple[float, float, float, float]:
    colonne = index % COLONNES
    ligne = index // COLONNES
    x = _grille_depart_x() + colonne * (LARGEUR_CARTE_DECK + ESPACEMENT_CARTE)
    y = Y_HAUT_GRILLE - HAUTEUR_CARTE_DECK - ligne * (HAUTEUR_CARTE_DECK + ESPACEMENT_CARTE)
    return x, y, LARGEUR_CARTE_DECK, HAUTEUR_CARTE_DECK


def _rect_bouton() -> tuple[float, float, float, float]:
    x = (LARGEUR_FENETRE - LARGEUR_BOUTON) / 2
    return x, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranVictoireFinale(pyglet.window.Window):
    """Felicitations + deck complet du joueur (meme rendu que EcranDeck) + bouton "Continuer"
    (specs.md 2.4, etape 11)."""

    def __init__(self, cartes: list[Carte]):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.groupes = regrouper_cartes(cartes)
        self.index_survole: int | None = None
        self.bouton_survole: bool = False
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
                "VICTOIRE FINALE",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 40,
                anchor_x="center",
                anchor_y="center",
                font_size=30,
                color=(*COULEUR_VICTOIRE, 255),
                batch=lot,
            )
        )
        elements.append(
            pyglet.text.Label(
                MESSAGE_FELICITATIONS,
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 78,
                anchor_x="center",
                anchor_y="center",
                font_size=15,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, (carte, quantite) in enumerate(self.groupes):
            elements.extend(self._dessiner_carte(index, carte, quantite, lot))
        if self.index_survole is not None:
            carte, _quantite = self.groupes[self.index_survole]
            elements.extend(self._dessiner_panneau_description(carte, lot))
        elements.extend(self._dessiner_bouton(lot))
        return elements

    def _dessiner_carte(self, index: int, carte: Carte, quantite: int, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_carte(index)
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

        sprite = _sprite_ajuste(carte.image, cx - IMAGE_TAILLE / 2, y + hauteur - 12 - IMAGE_TAILLE, IMAGE_TAILLE, IMAGE_TAILLE, lot)

        etoile = pyglet.text.Label(
            "★",
            x=x + 14,
            y=y + hauteur - 14,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(*COULEUR_ETOILE_RARETE[carte.rarete], 255),
            batch=lot,
        )

        nom = pyglet.text.Label(
            carte.nom,
            x=cx,
            y=y + hauteur - 20 - IMAGE_TAILLE,
            anchor_x="center",
            anchor_y="top",
            font_size=11,
            color=(*COULEUR_TEXTE, 255),
            multiline=True,
            width=largeur - 12,
            align="center",
            batch=lot,
        )
        cout = pyglet.text.Label(
            f"⚡{carte.cout}",
            x=cx,
            y=y + 12,
            anchor_x="center",
            anchor_y="center",
            font_size=11,
            color=(200, 200, 205, 255),
            batch=lot,
        )
        elements = [cadre, sprite, etoile, nom, cout]
        if quantite > 1:
            elements.append(
                pyglet.text.Label(
                    f"×{quantite}",
                    x=x + largeur - 16,
                    y=y + hauteur - 14,
                    anchor_x="center",
                    anchor_y="center",
                    font_size=13,
                    color=(*COULEUR_QUANTITE, 255),
                    batch=lot,
                )
            )
        return elements

    def _dessiner_panneau_description(self, carte: Carte, lot: pyglet.graphics.Batch) -> list:
        cx = LARGEUR_FENETRE / 2
        y_bas = 20
        fond = shapes.BorderedRectangle(
            cx - LARGEUR_PANNEAU / 2,
            y_bas,
            LARGEUR_PANNEAU,
            HAUTEUR_PANNEAU,
            border=2,
            color=COULEUR_FOND_PANNEAU,
            border_color=COULEUR_CONTOUR_PANNEAU,
            batch=lot,
        )
        fond.opacity = OPACITE_FOND_PANNEAU
        nom = pyglet.text.Label(
            carte.nom,
            x=cx,
            y=y_bas + HAUTEUR_PANNEAU - 16,
            anchor_x="center",
            anchor_y="center",
            font_size=13,
            color=(*COULEUR_QUANTITE, 255),
            batch=lot,
        )
        description = pyglet.text.Label(
            texte_effet_carte(carte),
            x=cx,
            y=y_bas + HAUTEUR_PANNEAU - 34,
            anchor_x="center",
            anchor_y="top",
            font_size=12,
            color=(*COULEUR_TEXTE, 255),
            multiline=True,
            width=LARGEUR_PANNEAU - 30,
            align="center",
            batch=lot,
        )
        return [fond, nom, description]

    def _dessiner_bouton(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "Continuer",
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=15,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [rectangle, texte]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)
        self.bouton_survole = _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True

    def _index_a(self, x: int, y: int) -> int | None:
        for index in range(len(self.groupes)):
            if _point_dans_rectangle(x, y, *_rect_carte(index)):
                return index
        return None
