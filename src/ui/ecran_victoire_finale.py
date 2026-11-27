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
COULEUR_VICTOIRE = (70, 190, 90)

COULEUR_BOUTON = (70, 190, 90)
COULEUR_BOUTON_SURVOLE = (100, 210, 115)

MESSAGE_FELICITATIONS = "Vous avez vaincu le Boss et terminé ce run !"

LARGEUR_CARTE_DECK = 130
HAUTEUR_CARTE_DECK = carte_visuel.hauteur_carte(LARGEUR_CARTE_DECK)
ESPACEMENT_CARTE = 18
COLONNES = 8
# Grille decalee vers le bas par rapport a EcranDeck (Y_HAUT_GRILLE = HAUTEUR_FENETRE - 110) pour
# laisser la place au sous-titre de felicitations sous le titre.
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 150

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
            elements.extend(self._dessiner_carte_agrandie(carte, lot))
        elements.extend(self._dessiner_bouton(lot))
        return elements

    def _dessiner_carte(self, index: int, carte: Carte, quantite: int, lot: pyglet.graphics.Batch) -> list:
        return carte_visuel.dessiner_carte_de_grille(
            carte, _rect_carte(index), quantite, index == self.index_survole, lot, ordre=1 + index
        )

    def _dessiner_carte_agrandie(self, carte: Carte, lot: pyglet.graphics.Batch) -> list:
        """Carte survolee en grand a cote d'elle."""
        lignes = []
        return carte_visuel.dessiner_carte_agrandie_a_cote(
            carte, _rect_carte(self.index_survole), lignes, lot, carte_visuel.GROUPE_CARTE_AGRANDIE, LARGEUR_FENETRE, HAUTEUR_FENETRE
        )

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
