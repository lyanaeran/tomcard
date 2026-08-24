"""
Ecran generique pour une etape du parcours dont le contenu n'est pas encore prepare (Aventure,
Planete commerciale - specs.md 2/9.1) : reutilise l'icone/description deja definie pour l'ecran
"Choix du prochain niveau" (LIBELLES_TYPE_ETAPE, src/ui/ecran_choix_niveau.py) avec un message
explicite, et un bouton "J'ai termine" qui avance simplement au niveau suivant (specs.md 2.4,
etapes 7 et 9) - remplace l'ancien comportement qui rouvrait silencieusement le choix du niveau
sans aucun ecran visible.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.parcours import TypeEtape
from src.ui.ecran_choix_niveau import LIBELLES_TYPE_ETAPE
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_ajuste, _sprite_etire

COULEUR_TEXTE = (255, 255, 255)
COULEUR_SOUS_TITRE = (200, 200, 205)
COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)

# Titre affiche par type d'etape (LIBELLES_TYPE_ETAPE ne fournit qu'une icone + une courte
# description, pas de nom a afficher en titre) - uniquement les deux types encore sans ecran
# dedie (specs.md 2.4, etapes 7 et 9) ; Prime/Station service/Boss ont chacun leur propre ecran.
TITRES_TYPE_ETAPE = {
    TypeEtape.AVENTURE: "Aventure",
    TypeEtape.PLANETE_COMMERCIALE: "Planete commerciale",
}

MESSAGE_CONTENU_A_VENIR = "Contenu pas encore defini pour cette etape."

IMAGE_TAILLE = 240
LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 46
Y_BOUTON = 100


def _rect_bouton() -> tuple[float, float, float, float]:
    x = (LARGEUR_FENETRE - LARGEUR_BOUTON) / 2
    return x, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranEtapePlaceholder(pyglet.window.Window):
    """Etape sans contenu prepare (Aventure, Planete commerciale) : icone + message + bouton
    "J'ai termine" qui signale a l'appelant d'avancer au niveau suivant, sans autre effet."""

    def __init__(self, type_etape: TypeEtape):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.type_etape = type_etape
        self.bouton_survole: bool = False
        self.termine: bool = False

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        image, _description = LIBELLES_TYPE_ETAPE[self.type_etape]
        elements = [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        elements.append(
            pyglet.text.Label(
                TITRES_TYPE_ETAPE[self.type_etape],
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 60,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        elements.append(
            _sprite_ajuste(
                image,
                LARGEUR_FENETRE / 2 - IMAGE_TAILLE / 2,
                HAUTEUR_FENETRE / 2 - IMAGE_TAILLE / 2 + 40,
                IMAGE_TAILLE,
                IMAGE_TAILLE,
                lot,
            )
        )
        elements.append(
            pyglet.text.Label(
                MESSAGE_CONTENU_A_VENIR,
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE / 2 - IMAGE_TAILLE / 2 + 10,
                anchor_x="center",
                anchor_y="center",
                font_size=16,
                color=(*COULEUR_SOUS_TITRE, 255),
                batch=lot,
            )
        )
        elements.extend(self._dessiner_bouton(lot))
        return elements

    def _dessiner_bouton(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "J'ai termine",
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
        self.bouton_survole = _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True
