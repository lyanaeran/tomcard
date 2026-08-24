"""
Ecran d'accueil d'un joueur (specs.md 10.3), affiche une fois le profil choisi sur
src/ui/ecran_selection_joueur.py. Si une partie est en cours (au plus une par joueur, decision
utilisateur) : niveau, vaisseau, et boutons Continuer/Abandonner/Voir le deck. Sinon : bouton
Nouvelle partie (vers le choix de module du Niveau 1, specs.md 2.3).

Fond de combat reutilise en placeholder (decision utilisateur, meme principe que les autres
ecrans du parcours), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.donnees import charger_modules
from src.gameplay.partie import EtatModule, Partie, Profil
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
COULEUR_BOUTON_DANGER = (150, 55, 55)
COULEUR_BOUTON_DANGER_SURVOLE = (190, 75, 75)
OPACITE_FOND = 190

# Ordre d'affichage des emplacements du vaisseau (specs.md 3.1/5), meme cles que
# src/gameplay/partie.py:POSITIONS_VAISSEAU.
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
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 180

LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 56
ESPACEMENT_BOUTON = 30
Y_BOUTONS = 140


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranAccueilJoueur(pyglet.window.Window):
    def __init__(self, profil: Profil, partie_active: Partie | None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.profil = profil
        self.partie_active = partie_active
        self.specs_modules = {spec.id: spec for spec in charger_modules()}
        self.index_bouton_survole: int | None = None
        self.action: str | None = None

    def _boutons(self) -> list[tuple[str, str]]:
        """Liste (identifiant_action, libelle) des boutons de cet ecran, dans l'ordre affiche."""
        if self.partie_active is not None:
            return [("continuer", "Continuer"), ("abandonner", "Abandonner la partie"), ("voir_deck", "Voir le deck")]
        return [("nouvelle_partie", "Nouvelle partie")]

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
                self.profil.nom,
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 50,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        if self.partie_active is not None:
            elements.append(
                pyglet.text.Label(
                    f"Niveau {self.partie_active.niveau}",
                    x=LARGEUR_FENETRE / 2,
                    y=HAUTEUR_FENETRE - 90,
                    anchor_x="center",
                    anchor_y="center",
                    font_size=16,
                    color=(*COULEUR_SOUS_TITRE, 255),
                    batch=lot,
                )
            )
            for index, (position, libelle) in enumerate(POSITIONS_AFFICHEES):
                elements.extend(self._dessiner_module(index, libelle, self.partie_active.vaisseau[position], lot))
        for index, (_action, libelle) in enumerate(self._boutons()):
            elements.extend(self._dessiner_bouton(index, libelle, lot))
        return elements

    def _rect_module(self, index: int) -> tuple[float, float, float, float]:
        total = len(POSITIONS_AFFICHEES)
        largeur_totale = total * LARGEUR_CARTE_MODULE + (total - 1) * ESPACEMENT_CARTE
        x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
        x = x_depart + index * (LARGEUR_CARTE_MODULE + ESPACEMENT_CARTE)
        return x, Y_HAUT_GRILLE - HAUTEUR_CARTE_MODULE, LARGEUR_CARTE_MODULE, HAUTEUR_CARTE_MODULE

    def _dessiner_module(
        self, index: int, libelle: str, etat: EtatModule | None, lot: pyglet.graphics.Batch
    ) -> list:
        x, y, largeur, hauteur = self._rect_module(index)
        cx = x + largeur / 2
        if etat is None:
            cadre = shapes.BorderedRectangle(
                x, y, largeur, hauteur, border=2, color=COULEUR_FOND_VIDE, border_color=COULEUR_CONTOUR_VIDE, batch=lot
            )
            cadre.opacity = OPACITE_FOND
            libelle_label = pyglet.text.Label(
                libelle,
                x=cx,
                y=y + hauteur - 20,
                anchor_x="center",
                anchor_y="center",
                font_size=13,
                color=(*COULEUR_SOUS_TITRE, 255),
                batch=lot,
            )
            vide = pyglet.text.Label(
                "Emplacement vide",
                x=cx,
                y=y + hauteur / 2,
                anchor_x="center",
                anchor_y="center",
                font_size=12,
                color=(120, 124, 135, 255),
                batch=lot,
            )
            return [cadre, libelle_label, vide]

        spec = self.specs_modules[etat.module_id]
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE, border_color=COULEUR_CONTOUR_CARTE, batch=lot
        )
        cadre.opacity = OPACITE_FOND
        libelle_label = pyglet.text.Label(
            libelle,
            x=cx,
            y=y + hauteur - 18,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
            color=(*COULEUR_SOUS_TITRE, 255),
            batch=lot,
        )
        sprite = _sprite_ajuste(spec.image, cx - IMAGE_TAILLE / 2, y + hauteur - 40 - IMAGE_TAILLE, IMAGE_TAILLE, IMAGE_TAILLE, lot)
        nom = pyglet.text.Label(
            spec.nom,
            x=cx,
            y=y + hauteur - 52 - IMAGE_TAILLE,
            anchor_x="center",
            anchor_y="center",
            font_size=13,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        pv = pyglet.text.Label(
            f"{etat.pv} / {etat.pv_max} PV",
            x=cx,
            y=y + 34,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        niveau_maj = pyglet.text.Label(
            f"Mise a jour : niveau {etat.niveau_maj}",
            x=cx,
            y=y + 14,
            anchor_x="center",
            anchor_y="center",
            font_size=11,
            color=(*COULEUR_NIVEAU_MAJ, 255),
            batch=lot,
        )
        return [cadre, libelle_label, sprite, nom, pv, niveau_maj]

    def _rect_bouton(self, index: int) -> tuple[float, float, float, float]:
        total = len(self._boutons())
        largeur_totale = total * LARGEUR_BOUTON + (total - 1) * ESPACEMENT_BOUTON
        x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
        x = x_depart + index * (LARGEUR_BOUTON + ESPACEMENT_BOUTON)
        return x, Y_BOUTONS, LARGEUR_BOUTON, HAUTEUR_BOUTON

    def _dessiner_bouton(self, index: int, libelle: str, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = self._rect_bouton(index)
        survole = index == self.index_bouton_survole
        est_danger = self._boutons()[index][0] == "abandonner"
        if est_danger:
            couleur = COULEUR_BOUTON_DANGER_SURVOLE if survole else COULEUR_BOUTON_DANGER
        else:
            couleur = COULEUR_BOUTON_SURVOLE if survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            libelle,
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=14,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [rectangle, texte]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_bouton_survole = self._index_bouton_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        index = self._index_bouton_a(x, y)
        if index is not None:
            self.action = self._boutons()[index][0]

    def _index_bouton_a(self, x: int, y: int) -> int | None:
        for index in range(len(self._boutons())):
            if _point_dans_rectangle(x, y, *self._rect_bouton(index)):
                return index
        return None
