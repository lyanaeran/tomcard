"""
Ecran "voir le deck en entier" (specs.md 6/10.3), ouvert depuis l'ecran de partie (bouton "Voir le
deck"). Fenetre pyglet independante comme les autres ecrans du parcours ; l'ecran de partie ayant
deja ete ferme avant l'ouverture de celui-ci (main.py), le bouton "Retour" (self.termine) est le
seul moyen d'y revenir - pas de fermeture de fenetre native qui rouvrirait quoi que ce soit.

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
    _image,
    _sprite_etire,
)

COULEUR_TEXTE = (255, 255, 255)

COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)

# Cartes de 180 px, 6 par ligne (demande utilisateur, 2026-11-27 : 130 px etait trop petit) ; la
# grille defile a la molette quand elle depasse l'ecran.
LARGEUR_CARTE_DECK = 180
HAUTEUR_CARTE_DECK = carte_visuel.hauteur_carte(LARGEUR_CARTE_DECK)
ESPACEMENT_CARTE = 24
# Ecart vertical plus grand : le nombre d'exemplaires ("x4") s'ecrit au-dessus de la carte
ESPACEMENT_LIGNES = 34
COLONNES = 6
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 130
MARGE_BAS = 20
# Bandeau du haut (titre, Retour) : les cartes qui defilent passent dessous
Y_BANDEAU = HAUTEUR_FENETRE - 100
PAS_MOLETTE = 60
GROUPE_BANDEAU = pyglet.graphics.Group(order=5)
GROUPE_BANDEAU_DESSUS = pyglet.graphics.Group(order=6)
COULEUR_ASCENSEUR = (200, 210, 230)

# Bouton "Retour" en haut a droite (plutot qu'en bas, ou la place depend de la taille du deck) -
# seul moyen de fermer cet ecran et de revenir a l'ecran de partie (specs.md 10.3), qui a ete
# ferme avant l'ouverture de celui-ci (main.py).
LARGEUR_BOUTON = 140
HAUTEUR_BOUTON = 40
X_BOUTON = LARGEUR_FENETRE - LARGEUR_BOUTON - 20
Y_BOUTON = HAUTEUR_FENETRE - HAUTEUR_BOUTON - 20


def _rect_bouton() -> tuple[float, float, float, float]:
    return X_BOUTON, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _grille_depart_x() -> float:
    largeur_totale = COLONNES * LARGEUR_CARTE_DECK + (COLONNES - 1) * ESPACEMENT_CARTE
    return (LARGEUR_FENETRE - largeur_totale) / 2


def _rect_carte(index: int, defilement: float = 0) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) de la carte a cet index, grille de COLONNES
    colonnes remplie ligne par ligne, centree horizontalement dans la fenetre, remontee de
    `defilement` pixels."""
    colonne = index % COLONNES
    ligne = index // COLONNES
    x = _grille_depart_x() + colonne * (LARGEUR_CARTE_DECK + ESPACEMENT_CARTE)
    y = Y_HAUT_GRILLE - HAUTEUR_CARTE_DECK - ligne * (HAUTEUR_CARTE_DECK + ESPACEMENT_LIGNES) + defilement
    return x, y, LARGEUR_CARTE_DECK, HAUTEUR_CARTE_DECK


def defilement_max(nombre: int) -> float:
    """Defilement maximal pour voir la derniere ligne au-dessus de MARGE_BAS (0 si tout tient)."""
    lignes = (nombre + COLONNES - 1) // COLONNES
    hauteur_grille = lignes * HAUTEUR_CARTE_DECK + max(0, lignes - 1) * ESPACEMENT_LIGNES
    return max(0.0, hauteur_grille - (Y_HAUT_GRILLE - MARGE_BAS))


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranDeck(pyglet.window.Window):
    """Grille de cartes (deck possede, ou toutes les cartes d'un combat en cours), regroupees par
    carte et module (carte, quantite). Survol d'une carte : sa description complete et le module
    auquel elle est rattachee (`noms_modules` : exemplaire -> nom)."""

    def __init__(self, cartes: list[Carte], noms_modules: dict[str, str] | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.groupes = regrouper_cartes(cartes)
        self.noms_modules = noms_modules or {}
        self.index_survole: int | None = None
        self.bouton_retour_survole: bool = False
        self.termine: bool = False
        # Pixels dont la grille est remontee (molette), entre 0 et defilement_max
        self.defilement: float = 0.0

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        elements = [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        for index, (carte, quantite) in enumerate(self.groupes):
            _x, y, _l, hauteur = self._rect(index)
            if y > HAUTEUR_FENETRE or y + hauteur < 0:
                continue  # hors de l'ecran
            elements.extend(self._dessiner_carte(index, carte, quantite, lot))
        elements.extend(self._dessiner_bandeau(lot))
        if self.index_survole is not None:
            carte, _quantite = self.groupes[self.index_survole]
            elements.extend(self._dessiner_carte_agrandie(carte, lot))
        return elements

    def _dessiner_bandeau(self, lot: pyglet.graphics.Batch) -> list:
        """Haut de l'ecran (fond, titre, Retour, ascenseur) par-dessus les cartes qui defilent."""
        fond = _image(FOND_IMAGE)
        echelle_x, echelle_y = LARGEUR_FENETRE / fond.width, HAUTEUR_FENETRE / fond.height
        y_image = int(Y_BANDEAU / echelle_y)
        region = fond.get_region(0, y_image, fond.width, fond.height - y_image)
        bandeau = pyglet.sprite.Sprite(region, x=0, y=Y_BANDEAU, batch=lot, group=GROUPE_BANDEAU)
        bandeau.scale_x, bandeau.scale_y = echelle_x, echelle_y
        titre = pyglet.text.Label(
            "Deck", x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE - 50, anchor_x="center", anchor_y="center",
            font_size=26, color=(*COULEUR_TEXTE, 255), batch=lot, group=GROUPE_BANDEAU_DESSUS,
        )
        elements = [bandeau, titre, *self._dessiner_bouton_retour(lot)]
        maximum = defilement_max(len(self.groupes))
        if maximum > 0:
            # Ascenseur a droite : sa barre montre la part visible de la grille et sa position
            haut, bas = Y_BANDEAU - 10, MARGE_BAS
            course = haut - bas
            visible = course * (Y_HAUT_GRILLE - MARGE_BAS) / (Y_HAUT_GRILLE - MARGE_BAS + maximum)
            y_barre = haut - visible - (course - visible) * self.defilement / maximum
            rail = shapes.Rectangle(
                LARGEUR_FENETRE - 14, bas, 6, course, color=COULEUR_ASCENSEUR, batch=lot, group=GROUPE_BANDEAU
            )
            rail.opacity = 60
            barre = shapes.Rectangle(
                LARGEUR_FENETRE - 14, y_barre, 6, visible, color=COULEUR_ASCENSEUR, batch=lot, group=GROUPE_BANDEAU_DESSUS
            )
            elements += [rail, barre]
        return elements

    def _dessiner_bouton_retour(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_retour_survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot, group=GROUPE_BANDEAU)
        texte = pyglet.text.Label(
            "Retour",
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=14,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
            group=GROUPE_BANDEAU_DESSUS,
        )
        return [rectangle, texte]

    def _dessiner_carte(self, index: int, carte: Carte, quantite: int, lot: pyglet.graphics.Batch) -> list:
        return carte_visuel.dessiner_carte_de_grille(
            carte, self._rect(index), quantite, index == self.index_survole, lot, ordre=1 + index
        )

    def _dessiner_carte_agrandie(self, carte: Carte, lot: pyglet.graphics.Batch) -> list:
        """Carte survolee en grand a cote d'elle, avec le module auquel elle est rattachee."""
        nom_module = self.noms_modules.get(carte.exemplaire_module)
        lignes = [f"Module : {nom_module}"] if nom_module else []
        return carte_visuel.dessiner_carte_agrandie_a_cote(
            carte, self._rect(self.index_survole), lignes, lot, carte_visuel.GROUPE_CARTE_AGRANDIE, LARGEUR_FENETRE, HAUTEUR_FENETRE
        )

    def _rect(self, index: int) -> tuple[float, float, float, float]:
        return _rect_carte(index, self.defilement)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_survole = self._index_a(x, y)
        self.bouton_retour_survole = _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        """Molette : la grille defile (vers le bas quand on tourne vers soi)."""
        self.defilement = min(max(self.defilement - scroll_y * PAS_MOLETTE, 0.0), defilement_max(len(self.groupes)))
        self.index_survole = self._index_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True

    def _index_a(self, x: int, y: int) -> int | None:
        if y >= Y_BANDEAU:
            return None  # cartes cachees sous le bandeau du haut
        for index in range(len(self.groupes)):
            if _point_dans_rectangle(x, y, *self._rect(index)):
                return index
        return None
