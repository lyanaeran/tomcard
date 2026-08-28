"""
Ecran "voir le vaisseau" (specs.md 10.3), ouvert depuis la barre laterale (src/ui/barre_laterale.py)
par-dessus l'ecran appelant, qui reste ouvert et inchange derriere - le bouton "Retour" (self.termine)
ferme uniquement cet ecran de consultation. Lecture seule (aucune action, contrairement a la
Station service) : modules equipes, PV et niveau de mise a jour, meme presentation que
src/ui/ecran_accueil_joueur.py.

Fond de combat reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.donnees import charger_modules, image_case_module
from src.gameplay.partie import EtatModule, Partie
from src.ui.fenetre import FOND_IMAGE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_ajuste, _sprite_etire

COULEUR_TEXTE = (255, 255, 255)
COULEUR_SOUS_TITRE = (200, 200, 205)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_FOND_VIDE = (15, 17, 24)
COULEUR_CONTOUR_VIDE = (60, 65, 80)
COULEUR_NIVEAU_MAJ = (255, 220, 120)
COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)
OPACITE_FOND = 190

# Meme ordre d'affichage que src/ui/ecran_accueil_joueur.py/ecran_station_service.py (specs.md 3.1/5).
POSITIONS_AFFICHEES = (
    ("base", "Principal"),
    ("avant_gauche", "Avant gauche"),
    ("avant_droite", "Avant droite"),
    ("arriere_gauche", "Arriere gauche"),
    ("arriere_droite", "Arriere droite"),
)

LARGEUR_CARTE_MODULE = 200
HAUTEUR_CARTE_MODULE = 240
IMAGE_TAILLE = 110
ESPACEMENT_CARTE = 24
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 140

LARGEUR_BOUTON = 140
HAUTEUR_BOUTON = 40
X_BOUTON = LARGEUR_FENETRE - LARGEUR_BOUTON - 20
Y_BOUTON = HAUTEUR_FENETRE - HAUTEUR_BOUTON - 20


def _rect_bouton() -> tuple[float, float, float, float]:
    return X_BOUTON, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _rect_module(index: int) -> tuple[float, float, float, float]:
    total = len(POSITIONS_AFFICHEES)
    largeur_totale = total * LARGEUR_CARTE_MODULE + (total - 1) * ESPACEMENT_CARTE
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE_MODULE + ESPACEMENT_CARTE)
    return x, Y_HAUT_GRILLE - HAUTEUR_CARTE_MODULE, LARGEUR_CARTE_MODULE, HAUTEUR_CARTE_MODULE


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranVaisseau(pyglet.window.Window):
    """Vue lecture seule du vaisseau (modules equipes, PV, niveau de mise a jour). `self.termine`
    signale que le bouton "Retour" a ete clique - a l'appelant de fermer cette fenetre."""

    def __init__(self, partie: Partie):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.partie = partie
        self.specs_par_id = {spec.id: spec for spec in charger_modules()}
        self.bouton_retour_survole: bool = False
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
                "Vaisseau",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 50,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, (position, libelle) in enumerate(POSITIONS_AFFICHEES):
            elements.extend(self._dessiner_module(index, libelle, self.partie.vaisseau[position], lot))
        elements.extend(self._dessiner_bouton_retour(lot))
        return elements

    def _dessiner_module(
        self, index: int, libelle: str, etat: EtatModule | None, lot: pyglet.graphics.Batch
    ) -> list:
        x, y, largeur, hauteur = _rect_module(index)
        cx = x + largeur / 2
        if etat is None:
            cadre = shapes.BorderedRectangle(
                x, y, largeur, hauteur, border=2, color=COULEUR_FOND_VIDE, border_color=COULEUR_CONTOUR_VIDE, batch=lot
            )
            cadre.opacity = OPACITE_FOND
            libelle_label = pyglet.text.Label(
                libelle, x=cx, y=y + hauteur - 20, anchor_x="center", anchor_y="center",
                font_size=13, color=(*COULEUR_SOUS_TITRE, 255), batch=lot,
            )
            vide = pyglet.text.Label(
                "Emplacement vide", x=cx, y=y + hauteur / 2, anchor_x="center", anchor_y="center",
                font_size=12, color=(120, 124, 135, 255), batch=lot,
            )
            return [cadre, libelle_label, vide]

        spec = self.specs_par_id[etat.module_id]
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE, border_color=COULEUR_CONTOUR_CARTE, batch=lot
        )
        cadre.opacity = OPACITE_FOND
        libelle_label = pyglet.text.Label(
            libelle, x=cx, y=y + hauteur - 18, anchor_x="center", anchor_y="center",
            font_size=12, color=(*COULEUR_SOUS_TITRE, 255), batch=lot,
        )
        sprite = _sprite_ajuste(
            image_case_module(spec), cx - IMAGE_TAILLE / 2, y + hauteur - 40 - IMAGE_TAILLE, IMAGE_TAILLE, IMAGE_TAILLE, lot
        )
        nom = pyglet.text.Label(
            spec.nom, x=cx, y=y + hauteur - 52 - IMAGE_TAILLE, anchor_x="center", anchor_y="center",
            font_size=13, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        pv = pyglet.text.Label(
            f"{etat.pv} / {etat.pv_max} PV", x=cx, y=y + 34, anchor_x="center", anchor_y="center",
            font_size=12, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        niveau_maj = pyglet.text.Label(
            f"Mise a jour : niveau {etat.niveau_maj}", x=cx, y=y + 14, anchor_x="center", anchor_y="center",
            font_size=11, color=(*COULEUR_NIVEAU_MAJ, 255), batch=lot,
        )
        return [cadre, libelle_label, sprite, nom, pv, niveau_maj]

    def _dessiner_bouton_retour(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_retour_survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "Retour", x=x + largeur / 2, y=y + hauteur / 2, anchor_x="center", anchor_y="center",
            font_size=14, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        return [rectangle, texte]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.bouton_retour_survole = _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True
