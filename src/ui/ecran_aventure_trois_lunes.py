"""
Ecran Aventure "Trois lunes" (specs.md 2.5) : une des 3 premieres Aventures specifiees. Choix
unique parmi Reparer/Ameliorer/Bricoler, resolu immediatement des le clic - contrairement a
l'Aventure Asteroides (a venir), pas de sequence en plusieurs temps ici. Fenetre pyglet
independante comme les autres ecrans du parcours, mute directement `partie.vaisseau`/`partie.deck`
(src/gameplay/partie.py) - c'est a l'appelant de sauvegarder la partie une fois l'ecran ferme.
"""

from collections import Counter

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte
from src.gameplay.donnees import RACINE, charger_cartes, charger_modules, image_case_module
from src.gameplay.partie import (
    PV_AMELIORATION,
    PV_REPARATION_VAISSEAU,
    Partie,
    ameliorer_module_aventure,
    reparer_vaisseau,
    retirer_carte,
)
from src.ui.ecran_station_service import POSITIONS_AFFICHEES
from src.ui.fenetre import HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_ajuste, _sprite_etire

FOND_TROIS_LUNES = str(RACINE / "assets" / "aventure" / "trois_lunes.png")

DESCRIPTION = (
    "Un havre de paix au milieu de la galaxie. Aucune forme de vie intelligente, des animaux de "
    "taille raisonnable, de l'eau, des fruits et des legumes sauvages partout. Il est temps de "
    "faire une pause."
)

COULEUR_TEXTE = (255, 255, 255)
COULEUR_SOUS_TITRE = (200, 200, 205)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_SURVOLEE = (255, 255, 255)
COULEUR_FOND_VIDE = (15, 17, 24)
COULEUR_CONTOUR_VIDE = (60, 65, 80)
COULEUR_NOM = (255, 220, 120)
COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)
OPACITE_FOND = 190

# (identifiant, image, titre, description) des 3 choix (specs.md 2.5) - la description reprend
# les constantes reelles du moteur plutot que des valeurs dupliquees en dur. Image = None en
# attendant un visuel dedie (aucune icone existante pertinente pour "Bricoler").
# Reparer/Ameliorer recadrees depuis assets/station_service/ (bandeau de titre incruste retire,
# "REPARER"/"AMELIORER") - coherence avec le reste des choix d'Aventure (specs.md 2.5) : le titre
# est de toute facon toujours redessine a cote dans le rectangle de texte, un doublon du bandeau
# incruste original n'aurait plus d'interet. Sources originales inchangees (toujours utilisees
# telles quelles en Station service).
_ICONE_REPARER = str(RACINE / "assets" / "aventure" / "reparer.png")
_ICONE_AMELIORER = str(RACINE / "assets" / "aventure" / "ameliorer.png")

CHOIX = (
    ("reparer", _ICONE_REPARER, "Reparer le vaisseau", f"Chaque module regagne {PV_REPARATION_VAISSEAU} PV."),
    ("ameliorer", _ICONE_AMELIORER, "Ameliorer un module", f"+{PV_AMELIORATION} PV max sur le module de votre choix."),
    ("bricoler", None, "Bricoler", "Retirez une carte de votre deck."),
)

# Choix empiles verticalement : image carree a gauche, rectangle de texte (titre + description) a
# droite - meme convention pour toutes les Aventures (specs.md 2.5).
LARGEUR_LIGNE_CHOIX = 820
HAUTEUR_LIGNE_CHOIX = 110
TAILLE_IMAGE_CHOIX = 100
ESPACEMENT_IMAGE_TEXTE = 16
ESPACEMENT_LIGNES_CHOIX = 16
Y_HAUT_CHOIX = 560

LARGEUR_CARTE_MODULE = 200
HAUTEUR_CARTE_MODULE = 220
IMAGE_MODULE_TAILLE = 100
ESPACEMENT_MODULE = 24
Y_HAUT_MODULES = HAUTEUR_FENETRE - 200

LARGEUR_CARTE_DECK = 160
HAUTEUR_CARTE_DECK = 220
IMAGE_DECK_TAILLE = 90
ESPACEMENT_DECK = 24
Y_HAUT_DECK = HAUTEUR_FENETRE - 200

LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 46
Y_BOUTON = 100


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


def _rect_bouton() -> tuple[float, float, float, float]:
    x = (LARGEUR_FENETRE - LARGEUR_BOUTON) / 2
    return x, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _rect_choix(index: int) -> tuple[float, float, float, float]:
    """Ligne complete (image + rectangle de texte) du choix a cet index - empilees du haut vers
    le bas, index 0 en premier."""
    x = (LARGEUR_FENETRE - LARGEUR_LIGNE_CHOIX) / 2
    y = Y_HAUT_CHOIX - HAUTEUR_LIGNE_CHOIX - index * (HAUTEUR_LIGNE_CHOIX + ESPACEMENT_LIGNES_CHOIX)
    return x, y, LARGEUR_LIGNE_CHOIX, HAUTEUR_LIGNE_CHOIX


def _rect_module(index: int) -> tuple[float, float, float, float]:
    total = len(POSITIONS_AFFICHEES)
    largeur_totale = total * LARGEUR_CARTE_MODULE + (total - 1) * ESPACEMENT_MODULE
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE_MODULE + ESPACEMENT_MODULE)
    return x, Y_HAUT_MODULES - HAUTEUR_CARTE_MODULE, LARGEUR_CARTE_MODULE, HAUTEUR_CARTE_MODULE


def _rect_carte_deck(index: int, total: int) -> tuple[float, float, float, float]:
    largeur_totale = total * LARGEUR_CARTE_DECK + (total - 1) * ESPACEMENT_DECK
    x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
    x = x_depart + index * (LARGEUR_CARTE_DECK + ESPACEMENT_DECK)
    return x, Y_HAUT_DECK - HAUTEUR_CARTE_DECK, LARGEUR_CARTE_DECK, HAUTEUR_CARTE_DECK


def _grouper_deck_par_id(deck: list[str], cartes: dict[str, Carte]) -> list[tuple[str, Carte, int]]:
    """Regroupe le deck (liste d'ids, doublons possibles) par id de carte - contrairement a
    regrouper_cartes (src/gameplay/carte.py) qui regroupe des objets Carte par nom, ici on garde
    l'id pour pouvoir le passer a retirer_carte."""
    compteur = Counter(deck)
    return [(id_carte, cartes[id_carte], quantite) for id_carte, quantite in compteur.items()]


class EcranAventureTroisLunes(pyglet.window.Window):
    """Aventure "Trois lunes" (specs.md 2.5) : choix unique parmi Reparer/Ameliorer/Bricoler,
    resolu immediatement. `self.termine` signale a l'appelant qu'il peut sauvegarder la partie et
    enchainer sur le choix du prochain niveau."""

    def __init__(self, partie: Partie, niveau: int):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.partie = partie
        self.niveau = niveau
        self.specs_par_id = {spec.id: spec for spec in charger_modules()}
        self.groupes_deck = _grouper_deck_par_id(partie.deck, charger_cartes())
        # "choix" (3 choix initiaux) -> "choix_module" (Ameliorer) ou "choix_carte" (Bricoler),
        # ou directement "resolu" (Reparer, effet immediat sans cible a choisir) -> "resolu".
        self.etape: str = "choix"
        self.message_resolu: str = ""
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
        elements = [_sprite_etire(FOND_TROIS_LUNES, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        elements.append(
            pyglet.text.Label(
                f"Trois lunes - Niveau {self.niveau}",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 50,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        if self.etape == "choix":
            elements.extend(self._dessiner_choix(lot))
        elif self.etape == "choix_module":
            elements.extend(self._dessiner_choix_module(lot))
        elif self.etape == "choix_carte":
            elements.extend(self._dessiner_choix_carte(lot))
        else:
            elements.extend(self._dessiner_resolu(lot))
        return elements

    def _dessiner_choix(self, lot: pyglet.graphics.Batch) -> list:
        elements = [
            pyglet.text.Label(
                DESCRIPTION,
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 110,
                anchor_x="center",
                anchor_y="top",
                font_size=15,
                color=(*COULEUR_SOUS_TITRE, 255),
                multiline=True,
                width=900,
                align="center",
                batch=lot,
            )
        ]
        for index, (_identifiant, image, titre, description) in enumerate(CHOIX):
            elements.extend(self._dessiner_carte_choix(index, image, titre, description, lot))
        return elements

    def _dessiner_carte_choix(
        self, index: int, image: str | None, titre: str, description: str, lot: pyglet.graphics.Batch
    ) -> list:
        """Une ligne de choix : image carree a gauche (None -> case vide en attendant un visuel
        dedie), rectangle de texte (titre + description) a droite (specs.md 2.5)."""
        x, y, largeur, hauteur = _rect_choix(index)
        survole = index == self.index_survole
        couleur_contour = COULEUR_CONTOUR_SURVOLEE if survole else COULEUR_CONTOUR_CARTE
        y_image = y + (hauteur - TAILLE_IMAGE_CHOIX) / 2

        cadre_image = shapes.BorderedRectangle(
            x, y_image, TAILLE_IMAGE_CHOIX, TAILLE_IMAGE_CHOIX, border=2,
            color=COULEUR_FOND_VIDE if image is None else COULEUR_FOND_CARTE,
            border_color=couleur_contour, batch=lot,
        )
        cadre_image.opacity = OPACITE_FOND
        elements = [cadre_image]
        if image is not None:
            elements.append(_sprite_ajuste(image, x, y_image, TAILLE_IMAGE_CHOIX, TAILLE_IMAGE_CHOIX, lot))

        x_texte = x + TAILLE_IMAGE_CHOIX + ESPACEMENT_IMAGE_TEXTE
        largeur_texte = largeur - TAILLE_IMAGE_CHOIX - ESPACEMENT_IMAGE_TEXTE
        cadre_texte = shapes.BorderedRectangle(
            x_texte, y, largeur_texte, hauteur, border=2, color=COULEUR_FOND_CARTE,
            border_color=couleur_contour, batch=lot,
        )
        cadre_texte.opacity = OPACITE_FOND
        titre_label = pyglet.text.Label(
            titre, x=x_texte + 20, y=y + hauteur - 30, anchor_x="left", anchor_y="center",
            font_size=16, color=(*COULEUR_NOM, 255), batch=lot,
        )
        description_label = pyglet.text.Label(
            description, x=x_texte + 20, y=y + hauteur - 52, anchor_x="left", anchor_y="top",
            font_size=13, color=(*COULEUR_TEXTE, 255), multiline=True, width=largeur_texte - 40,
            align="left", batch=lot,
        )
        elements.extend([cadre_texte, titre_label, description_label])
        return elements

    def _dessiner_choix_module(self, lot: pyglet.graphics.Batch) -> list:
        elements = [self._dessiner_instruction("Choisissez le module a ameliorer.", lot)]
        for index, (position, libelle) in enumerate(POSITIONS_AFFICHEES):
            elements.extend(self._dessiner_carte_module(index, position, libelle, lot))
        return elements

    def _dessiner_carte_module(self, index: int, position: str, libelle: str, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_module(index)
        cx = x + largeur / 2
        survole = index == self.index_survole
        etat = self.partie.vaisseau[position]

        if etat is None:
            couleur_contour = COULEUR_CONTOUR_SURVOLEE if survole else COULEUR_CONTOUR_VIDE
            cadre = shapes.BorderedRectangle(
                x, y, largeur, hauteur, border=2, color=COULEUR_FOND_VIDE,
                border_color=couleur_contour, batch=lot,
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
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE,
            border_color=COULEUR_CONTOUR_SURVOLEE if survole else COULEUR_CONTOUR_CARTE, batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        libelle_label = pyglet.text.Label(
            libelle, x=cx, y=y + hauteur - 18, anchor_x="center", anchor_y="center",
            font_size=12, color=(*COULEUR_SOUS_TITRE, 255), batch=lot,
        )
        sprite = _sprite_ajuste(
            image_case_module(spec), cx - IMAGE_MODULE_TAILLE / 2, y + hauteur - 36 - IMAGE_MODULE_TAILLE,
            IMAGE_MODULE_TAILLE, IMAGE_MODULE_TAILLE, lot,
        )
        nom = pyglet.text.Label(
            spec.nom, x=cx, y=y + hauteur - 48 - IMAGE_MODULE_TAILLE, anchor_x="center", anchor_y="center",
            font_size=13, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        pv = pyglet.text.Label(
            f"{etat.pv} / {etat.pv_max} PV", x=cx, y=y + 16, anchor_x="center", anchor_y="center",
            font_size=12, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        return [cadre, libelle_label, sprite, nom, pv]

    def _dessiner_choix_carte(self, lot: pyglet.graphics.Batch) -> list:
        elements = [self._dessiner_instruction("Choisissez une carte a retirer de votre deck.", lot)]
        total = len(self.groupes_deck)
        for index, (_id_carte, carte, quantite) in enumerate(self.groupes_deck):
            elements.extend(self._dessiner_carte_deck(index, total, carte, quantite, lot))
        return elements

    def _dessiner_carte_deck(self, index: int, total: int, carte: Carte, quantite: int, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_carte_deck(index, total)
        survole = index == self.index_survole
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE,
            border_color=COULEUR_CONTOUR_SURVOLEE if survole else COULEUR_CONTOUR_CARTE, batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        cx = x + largeur / 2
        sprite = _sprite_ajuste(
            carte.image, cx - IMAGE_DECK_TAILLE / 2, y + hauteur - 16 - IMAGE_DECK_TAILLE,
            IMAGE_DECK_TAILLE, IMAGE_DECK_TAILLE, lot,
        )
        nom = pyglet.text.Label(
            carte.nom, x=cx, y=y + hauteur - 26 - IMAGE_DECK_TAILLE, anchor_x="center", anchor_y="top",
            font_size=13, color=(*COULEUR_TEXTE, 255), multiline=True, width=largeur - 16, align="center", batch=lot,
        )
        elements = [cadre, sprite, nom]
        if quantite > 1:
            elements.append(
                pyglet.text.Label(
                    f"×{quantite}", x=x + largeur - 20, y=y + hauteur - 16, anchor_x="center", anchor_y="center",
                    font_size=14, color=(*COULEUR_NOM, 255), batch=lot,
                )
            )
        return elements

    def _dessiner_instruction(self, texte: str, lot: pyglet.graphics.Batch) -> pyglet.text.Label:
        return pyglet.text.Label(
            texte, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE - 100, anchor_x="center", anchor_y="center",
            font_size=16, color=(*COULEUR_TEXTE, 255), batch=lot,
        )

    def _dessiner_resolu(self, lot: pyglet.graphics.Batch) -> list:
        message = pyglet.text.Label(
            self.message_resolu, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE / 2 + 40,
            anchor_x="center", anchor_y="center", font_size=20, color=(*COULEUR_NOM, 255), batch=lot,
        )
        return [message, *self._dessiner_bouton(lot)]

    def _dessiner_bouton(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = _rect_bouton()
        couleur = COULEUR_BOUTON_SURVOLE if self.bouton_survole else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "Continuer", x=x + largeur / 2, y=y + hauteur / 2, anchor_x="center", anchor_y="center",
            font_size=15, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        return [rectangle, texte]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        if self.etape == "choix":
            self.index_survole = self._index_a(x, y, len(CHOIX), _rect_choix)
        elif self.etape == "choix_module":
            self.index_survole = self._index_a(x, y, len(POSITIONS_AFFICHEES), _rect_module)
        elif self.etape == "choix_carte":
            total = len(self.groupes_deck)
            self.index_survole = self._index_a(x, y, total, lambda i: _rect_carte_deck(i, total))
        else:
            self.index_survole = None
        self.bouton_survole = self.etape == "resolu" and _point_dans_rectangle(x, y, *_rect_bouton())

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.etape == "choix":
            self._cliquer_choix(x, y)
        elif self.etape == "choix_module":
            self._cliquer_module(x, y)
        elif self.etape == "choix_carte":
            self._cliquer_carte(x, y)
        elif _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True

    def _cliquer_choix(self, x: int, y: int) -> None:
        index = self._index_a(x, y, len(CHOIX), _rect_choix)
        if index is None:
            return
        identifiant = CHOIX[index][0]
        if identifiant == "reparer":
            reparer_vaisseau(self.partie)
            self.etape = "resolu"
            self.message_resolu = f"Chaque module regagne {PV_REPARATION_VAISSEAU} PV !"
        elif identifiant == "ameliorer":
            self.etape = "choix_module"
        elif identifiant == "bricoler":
            self.etape = "choix_carte"
        self.index_survole = None

    def _cliquer_module(self, x: int, y: int) -> None:
        index = self._index_a(x, y, len(POSITIONS_AFFICHEES), _rect_module)
        if index is None:
            return
        position, _libelle = POSITIONS_AFFICHEES[index]
        if self.partie.vaisseau[position] is None:
            return
        ameliorer_module_aventure(self.partie, position)
        nom = self.specs_par_id[self.partie.vaisseau[position].module_id].nom
        self.etape = "resolu"
        self.message_resolu = f"{nom} ameliore : +{PV_AMELIORATION} PV max !"

    def _cliquer_carte(self, x: int, y: int) -> None:
        total = len(self.groupes_deck)
        index = self._index_a(x, y, total, lambda i: _rect_carte_deck(i, total))
        if index is None:
            return
        id_carte, carte, _quantite = self.groupes_deck[index]
        retirer_carte(self.partie, id_carte)
        self.etape = "resolu"
        self.message_resolu = f"Carte retiree : {carte.nom}."

    def _index_a(self, x: int, y: int, total: int, rect_de) -> int | None:
        for index in range(total):
            if _point_dans_rectangle(x, y, *rect_de(index)):
                return index
        return None
