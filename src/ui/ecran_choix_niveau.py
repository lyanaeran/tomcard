"""
Ecran "Choix du prochain niveau" (specs.md 2.3/2.4), affiche a chaque niveau sauf le 1 (choix de
module, pas de tirage). 3 propositions d'ordinaire, ou une seule (TypeEtape.BOSS) aux niveaux Boss
(multiples de 10, cf. src/gameplay/parcours.py:est_niveau_boss/tirer_propositions_niveau) -
decision utilisateur : meme ecran de choix, juste une seule carte "Combattre le Boss !" au lieu de
3, pas d'enchainement automatique direct vers le combat. Fenetre pyglet independante pour
l'instant, meme situation que les autres ecrans du parcours deja implementes.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.donnees import RACINE
from src.gameplay.parcours import TypeEtape
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_ajuste, _sprite_etire

COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_SURVOLEE = (255, 255, 255)
COULEUR_DESCRIPTION = (220, 220, 225)
COULEUR_TEXTE = (255, 255, 255)
COULEUR_TITRE = (255, 220, 120)
OPACITE_FOND_CARTE = 190

_DOSSIER_ICONES = RACINE / "assets" / "prochain_niveau"

# Icone (desormais sans texte incruste, fournie par l'utilisateur), titre et description par type
# d'etape (specs.md 2), memes textes que le web (web/app.js).
LIBELLES_TYPE_ETAPE = {
    TypeEtape.PRIME: (str(_DOSSIER_ICONES / "prime.png"), "Prime", "Combat, contrat de chasseur de primes."),
    TypeEtape.STATION_SERVICE: (
        str(_DOSSIER_ICONES / "station_service.png"), "Station service", "Entretien du vaisseau contre de l'Argent.",
    ),
    TypeEtape.PLANETE_COMMERCIALE: (
        str(_DOSSIER_ICONES / "planete_commerciale.png"), "Planete commerciale", "Achat de cartes contre de l'Argent.",
    ),
    TypeEtape.AVENTURE: (str(_DOSSIER_ICONES / "aventure.png"), "Aventure", "Evenement inconnu."),
    TypeEtape.BOSS: (str(_DOSSIER_ICONES / "boss.png"), "Boss", "Combattre le Boss !"),
}

# Choix empiles verticalement : image carree a gauche, rectangle de texte (titre + description) a
# droite - meme convention que les choix d'Aventure (specs.md 2.5).
LARGEUR_LIGNE = 820
HAUTEUR_LIGNE = 110
TAILLE_IMAGE = 100
ESPACEMENT_IMAGE_TEXTE = 16
ESPACEMENT_LIGNES = 16
Y_HAUT = HAUTEUR_FENETRE - 140


def _rect_candidat(index: int, _total: int) -> tuple[float, float, float, float]:
    """Ligne complete (image + rectangle de texte) du candidat a cet index, empilees du haut vers
    le bas (3 d'ordinaire, 1 seule a un niveau Boss)."""
    x = (LARGEUR_FENETRE - LARGEUR_LIGNE) / 2
    y = Y_HAUT - HAUTEUR_LIGNE - index * (HAUTEUR_LIGNE + ESPACEMENT_LIGNES)
    return x, y, LARGEUR_LIGNE, HAUTEUR_LIGNE


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranChoixNiveau(pyglet.window.Window):
    """Ecran de choix d'une etape parmi les propositions tirees pour ce niveau (specs.md 2.3/2.4) -
    3 d'ordinaire, une seule (TypeEtape.BOSS) a un niveau Boss."""

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
        total = len(self.propositions)
        for index, type_etape in enumerate(self.propositions):
            elements.extend(self._dessiner_candidat(index, total, type_etape, lot))
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

    def _dessiner_candidat(self, index: int, total: int, type_etape: TypeEtape, lot: pyglet.graphics.Batch) -> list:
        """Une ligne de candidat : image carree a gauche, rectangle de texte (titre + description)
        a droite - meme convention que les choix d'Aventure (specs.md 2.5)."""
        x, y, largeur, hauteur = _rect_candidat(index, total)
        survole = index == self.index_survole
        couleur_contour = COULEUR_CONTOUR_CARTE_SURVOLEE if survole else COULEUR_CONTOUR_CARTE
        image, titre, description = LIBELLES_TYPE_ETAPE[type_etape]

        y_image = y + (hauteur - TAILLE_IMAGE) / 2
        cadre_image = shapes.BorderedRectangle(
            x, y_image, TAILLE_IMAGE, TAILLE_IMAGE, border=2,
            color=COULEUR_FOND_CARTE, border_color=couleur_contour, batch=lot,
        )
        cadre_image.opacity = OPACITE_FOND_CARTE
        sprite = _sprite_ajuste(image, x, y_image, TAILLE_IMAGE, TAILLE_IMAGE, lot)

        x_texte = x + TAILLE_IMAGE + ESPACEMENT_IMAGE_TEXTE
        largeur_texte = largeur - TAILLE_IMAGE - ESPACEMENT_IMAGE_TEXTE
        cadre_texte = shapes.BorderedRectangle(
            x_texte, y, largeur_texte, hauteur, border=2,
            color=COULEUR_FOND_CARTE, border_color=couleur_contour, batch=lot,
        )
        cadre_texte.opacity = OPACITE_FOND_CARTE
        titre_label = pyglet.text.Label(
            titre, x=x_texte + 20, y=y + hauteur - 30, anchor_x="left", anchor_y="center",
            font_size=16, color=(*COULEUR_TITRE, 255), batch=lot,
        )
        description_label = pyglet.text.Label(
            description, x=x_texte + 20, y=y + hauteur - 52, anchor_x="left", anchor_y="top",
            font_size=13, color=(*COULEUR_DESCRIPTION, 255), multiline=True, width=largeur_texte - 40,
            align="left", batch=lot,
        )
        return [cadre_image, sprite, cadre_texte, titre_label, description_label]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        index = self._index_a(x, y)
        if index is not None:
            self.type_choisi = self.propositions[index]

    def _index_a(self, x: int, y: int) -> int | None:
        total = len(self.propositions)
        for index in range(total):
            if _point_dans_rectangle(x, y, *_rect_candidat(index, total)):
                return index
        return None
