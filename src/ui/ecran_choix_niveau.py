"""
Ecran "Choix du prochain niveau" (specs.md 2.3/2.4), affiche a chaque niveau sauf le 1 (choix de
module, pas de tirage) et les niveaux Boss (multiples de 10, tirage inexistant - directement vers
le combat de Boss, cf. src/gameplay/parcours.py:est_niveau_boss). Fenetre pyglet independante pour
l'instant, meme situation que les autres ecrans du parcours deja implementes.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.parcours import TypeEtape
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_etire

COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_SURVOLEE = (255, 255, 255)
COULEUR_NOM_ETAPE = (255, 220, 120)
COULEUR_DESCRIPTION = (220, 220, 225)
COULEUR_TEXTE = (255, 255, 255)
OPACITE_FOND_CARTE = 190

# Libelles/descriptions par type d'etape (specs.md 2), memes textes que le web (web/app.js).
LIBELLES_TYPE_ETAPE = {
    TypeEtape.PRIME: ("Prime", "Combat, contrat de chasseur de primes."),
    TypeEtape.STATION_SERVICE: ("Station service", "Entretien du vaisseau contre de l'Argent."),
    TypeEtape.PLANETE_COMMERCIALE: ("Planete commerciale", "Achat de cartes contre de l'Argent."),
    TypeEtape.AVENTURE: ("Aventure", "Evenement inconnu."),
}

LARGEUR_CARTE = 320
HAUTEUR_CARTE = 220
ESPACEMENT_CARTES = 60
Y_HAUT = HAUTEUR_FENETRE - 160


def _rect_candidat(index: int) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) de la case cliquable du candidat a cet index (0-2),
    3 cases centrees horizontalement dans la fenetre."""
    largeur_totale = 3 * LARGEUR_CARTE + 2 * ESPACEMENT_CARTES
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE + ESPACEMENT_CARTES)
    return x, Y_HAUT - HAUTEUR_CARTE, LARGEUR_CARTE, HAUTEUR_CARTE


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranChoixNiveau(pyglet.window.Window):
    """Ecran de choix d'une etape parmi 3 propositions tirees pour ce niveau (specs.md 2.3/2.4)."""

    def __init__(self, niveau: int, propositions: list[TypeEtape]):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.niveau = niveau
        self.propositions = propositions
        self.index_survole: int | None = None
        self.type_choisi: TypeEtape | None = None

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
                f"Niveau {self.niveau}",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 60,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, type_etape in enumerate(self.propositions):
            elements.extend(self._dessiner_candidat(index, type_etape, lot))
        elements.append(
            pyglet.text.Label(
                "Choisissez la prochaine etape.",
                x=LARGEUR_FENETRE / 2,
                y=150,
                anchor_x="center",
                anchor_y="center",
                font_size=18,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        return elements

    def _dessiner_candidat(self, index: int, type_etape: TypeEtape, lot: pyglet.graphics.Batch) -> list:
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
        nom, description = LIBELLES_TYPE_ETAPE[type_etape]

        nom_label = pyglet.text.Label(
            nom,
            x=cx,
            y=y + hauteur - 40,
            anchor_x="center",
            anchor_y="center",
            font_size=18,
            color=(*COULEUR_NOM_ETAPE, 255),
            batch=lot,
        )
        description_label = pyglet.text.Label(
            description,
            x=cx,
            y=y + hauteur - 80,
            anchor_x="center",
            anchor_y="top",
            font_size=13,
            color=(*COULEUR_DESCRIPTION, 255),
            multiline=True,
            width=largeur - 40,
            align="center",
            batch=lot,
        )
        return [cadre, nom_label, description_label]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        index = self._index_a(x, y)
        if index is not None:
            self.type_choisi = self.propositions[index]

    def _index_a(self, x: int, y: int) -> int | None:
        for index in range(len(self.propositions)):
            if _point_dans_rectangle(x, y, *_rect_candidat(index)):
                return index
        return None
