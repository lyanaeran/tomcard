"""
Ecran de selection/creation de profil joueur (specs.md 10.3), premier ecran du jeu (PC). Chaque
joueur ne peut avoir qu'une seule partie EN_COURS a la fois - voir src/ui/ecran_accueil_joueur.py
pour l'ecran suivant, une fois le joueur choisi.

Fond de combat reutilise en placeholder (decision utilisateur, meme principe que les autres
ecrans du parcours), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes
from pyglet.window import key

from src.gameplay.partie import Profil, creer_profil, lister_profils
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_etire

COULEUR_TEXTE = (255, 255, 255)
COULEUR_FOND_LIGNE = (20, 24, 34)
COULEUR_CONTOUR_LIGNE = (90, 110, 150)
COULEUR_CONTOUR_LIGNE_SURVOLEE = (255, 255, 255)
COULEUR_FOND_SAISIE = (20, 24, 34)
COULEUR_CONTOUR_SAISIE = (255, 220, 120)
OPACITE_FOND = 190

LARGEUR_LIGNE = 400
HAUTEUR_LIGNE = 50
ESPACEMENT_LIGNE = 14
Y_HAUT_LISTE = HAUTEUR_FENETRE - 140

LARGEUR_SAISIE = 400
HAUTEUR_SAISIE = 50


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranSelectionJoueur(pyglet.window.Window):
    """Liste des profils existants (clic pour choisir) + zone de saisie pour en creer un
    nouveau (Entree pour valider)."""

    def __init__(self):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.profils = lister_profils()
        self.nom_saisi = ""
        self.index_survole: int | None = None
        self.saisie_survolee = False
        self.profil_choisi: Profil | None = None

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
                "Choisir un joueur",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 60,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, profil in enumerate(self.profils):
            elements.extend(self._dessiner_ligne_profil(index, profil, lot))
        elements.extend(self._dessiner_saisie(lot))
        return elements

    def _rect_ligne(self, index: int) -> tuple[float, float, float, float]:
        x = (LARGEUR_FENETRE - LARGEUR_LIGNE) / 2
        y = Y_HAUT_LISTE - HAUTEUR_LIGNE - index * (HAUTEUR_LIGNE + ESPACEMENT_LIGNE)
        return x, y, LARGEUR_LIGNE, HAUTEUR_LIGNE

    def _rect_saisie(self) -> tuple[float, float, float, float]:
        x = (LARGEUR_FENETRE - LARGEUR_SAISIE) / 2
        y = Y_HAUT_LISTE - HAUTEUR_LIGNE - len(self.profils) * (HAUTEUR_LIGNE + ESPACEMENT_LIGNE) - 40
        return x, y, LARGEUR_SAISIE, HAUTEUR_SAISIE

    def _dessiner_ligne_profil(self, index: int, profil: Profil, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = self._rect_ligne(index)
        survole = index == self.index_survole
        cadre = shapes.BorderedRectangle(
            x,
            y,
            largeur,
            hauteur,
            border=2,
            color=COULEUR_FOND_LIGNE,
            border_color=COULEUR_CONTOUR_LIGNE_SURVOLEE if survole else COULEUR_CONTOUR_LIGNE,
            batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        nom = pyglet.text.Label(
            profil.nom,
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [cadre, nom]

    def _dessiner_saisie(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = self._rect_saisie()
        cadre = shapes.BorderedRectangle(
            x,
            y,
            largeur,
            hauteur,
            border=2,
            color=COULEUR_FOND_SAISIE,
            border_color=COULEUR_CONTOUR_SAISIE,
            batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        texte = self.nom_saisi + "_"
        contenu = pyglet.text.Label(
            texte,
            x=x + 14,
            y=y + hauteur / 2,
            anchor_x="left",
            anchor_y="center",
            font_size=16,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        instruction = pyglet.text.Label(
            "Nouveau joueur : tapez un nom puis appuyez sur Entree",
            x=LARGEUR_FENETRE / 2,
            y=y - 26,
            anchor_x="center",
            anchor_y="center",
            font_size=13,
            color=(200, 200, 205, 255),
            batch=lot,
        )
        return [cadre, contenu, instruction]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_ligne_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        index = self._index_ligne_a(x, y)
        if index is not None:
            self.profil_choisi = self.profils[index]

    def on_text(self, text: str) -> None:
        if text.isprintable():
            self.nom_saisi += text

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == key.BACKSPACE:
            self.nom_saisi = self.nom_saisi[:-1]
        elif symbol in (key.ENTER, key.RETURN):
            nom = self.nom_saisi.strip()
            if nom:
                self.profil_choisi = creer_profil(nom)

    def _index_ligne_a(self, x: int, y: int) -> int | None:
        for index in range(len(self.profils)):
            if _point_dans_rectangle(x, y, *self._rect_ligne(index)):
                return index
        return None
