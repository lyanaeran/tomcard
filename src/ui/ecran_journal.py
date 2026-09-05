"""
Ecran "Journal de combat" (specs.md 8.1), ouvert depuis les controles de FenetreCombat (bouton
journal). Affiche l'historique accumule pendant le combat (cartes jouees, actions ennemies
resolues, marqueurs de tour) - simple liste de lignes multicolores, defilable a la molette.

Fond de combat reutilise en placeholder (meme principe que les autres ecrans de survol du
parcours, cf. ecran_deck.py/ecran_vaisseau.py).
"""

import pyglet
from pyglet import shapes

from src.gameplay.journal import Evenement
from src.ui import journal_combat
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_etire

COULEUR_TEXTE = (255, 255, 255)
COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)

HAUTEUR_LIGNE = 24
MARGE_HAUT = 100
MARGE_BAS = 40
X_TEXTE = 60
TAILLE_POLICE = 13

LARGEUR_BOUTON = 140
HAUTEUR_BOUTON = 40
X_BOUTON = LARGEUR_FENETRE - LARGEUR_BOUTON - 20
Y_BOUTON = HAUTEUR_FENETRE - HAUTEUR_BOUTON - 20


def _rect_bouton() -> tuple[float, float, float, float]:
    return X_BOUTON, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _point_dans_rectangle(px, py, x, y, largeur, hauteur) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranJournal(pyglet.window.Window):
    """Historique du combat en cours (specs.md 8.1) : instantane du journal au moment de
    l'ouverture (comme EcranDeck/EcranVaisseau, l'ecran appelant reste inchange derriere)."""

    def __init__(self, journal: list[Evenement]):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Journal de combat")
        self.journal = journal
        self.termine = False
        self.bouton_survole = False
        self.defilement = 0

    def _lignes_visibles(self) -> int:
        return max(1, int((HAUTEUR_FENETRE - MARGE_HAUT - MARGE_BAS) / HAUTEUR_LIGNE))

    def _defilement_max(self) -> int:
        return max(0, len(self.journal) - self._lignes_visibles())

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
                "Journal de combat",
                x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE - 50, anchor_x="center", anchor_y="center",
                font_size=22, color=(*COULEUR_TEXTE, 255), batch=lot,
            )
        )
        elements.extend(self._dessiner_lignes(lot))
        elements.extend(self._dessiner_bouton_retour(lot))
        return elements

    def _dessiner_lignes(self, lot: pyglet.graphics.Batch) -> list:
        elements = []
        lignes_visibles = self._lignes_visibles()
        fin = len(self.journal) - self.defilement
        debut = max(0, fin - lignes_visibles)
        y = MARGE_BAS + (fin - debut - 1) * HAUTEUR_LIGNE + HAUTEUR_LIGNE / 2
        for evenement in self.journal[debut:fin]:
            cx = X_TEXTE
            for texte, couleur in journal_combat.ligne_evenement(evenement):
                label = pyglet.text.Label(
                    texte, x=cx, y=y, anchor_x="left", anchor_y="center",
                    font_size=TAILLE_POLICE, color=(*couleur, 255), batch=lot,
                )
                elements.append(label)
                cx += label.content_width
            y -= HAUTEUR_LIGNE
        return elements

    def _dessiner_bouton_retour(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_survole else COULEUR_BOUTON
        fond = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "Retour", x=x + largeur / 2, y=y + hauteur / 2, anchor_x="center", anchor_y="center",
            font_size=14, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        return [fond, texte]

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        self.bouton_survole = _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y) -> None:
        self.defilement = max(0, min(self._defilement_max(), self.defilement + int(scroll_y)))
