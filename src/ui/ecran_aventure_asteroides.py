"""
Ecran Aventure "Asteroides" (specs.md 2.5) : deux choix - Traverser (sequence en 3 temps sur ce
meme ecran, chaque etape validee par un bouton "Continuer") ou Affronter les pirates (combat
scripte, delegue a l'appelant via `self.combat_demande`). Fenetre pyglet independante comme les
autres ecrans du parcours, mute directement `partie.vaisseau`/`partie.deck`
(src/gameplay/partie.py) - c'est a l'appelant de sauvegarder la partie une fois l'ecran ferme.
"""

import random

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte
from src.gameplay.donnees import RACINE, charger_cartes, charger_modules, image_case_module
from src.gameplay.parcours import pool_toutes_cartes, tirer_carte_recompense
from src.gameplay.partie import DEGATS_ASTEROIDES, Partie, ajouter_carte, id_de_carte, subir_degats_module
from src.ui.ecran_station_service import POSITIONS_AFFICHEES
from src.ui.fenetre import (
    COULEUR_ETOILE_RARETE,
    HAUTEUR_FENETRE,
    LARGEUR_FENETRE,
    _sprite_ajuste,
    _sprite_etire,
    texte_effet_carte,
)

FOND_ASTEROIDES = str(RACINE / "assets" / "aventure" / "champ_asteroides.png")

# Recadree depuis assets/prochain_niveau/prime.png (bandeau "PRIME" retire) : affiche de toute facon
# de nouveau son propre titre a cote dans le rectangle de texte, cf. commentaire de CHOIX plus bas.
_ICONE_AFFRONTER = str(RACINE / "assets" / "aventure" / "pirates.png")

# Extrait du fond d'ecran de cette Aventure (FOND_ASTEROIDES ci-dessus) plutot qu'une icone
# distincte : aucune icone existante n'etait pertinente pour ce choix.
_ICONE_TRAVERSER = str(RACINE / "assets" / "aventure" / "traverser.png")

DESCRIPTION = "Poursuivi par des pirates de l'espace, vous n'avez plus le choix : vaincre ou perir ! A moins que..."

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

# (identifiant, image, titre, description).
CHOIX = (
    ("traverser", _ICONE_TRAVERSER, "Traverser le champ d'asteroides", "Un module au choix va en subir les consequences..."),
    ("affronter", _ICONE_AFFRONTER, "Affronter les pirates", "Lance un combat contre 3 ennemis."),
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

LARGEUR_CARTE_OFFERTE = 220
HAUTEUR_CARTE_OFFERTE = 320
IMAGE_CARTE_TAILLE = 120
X_CARTE_OFFERTE = (LARGEUR_FENETRE - LARGEUR_CARTE_OFFERTE) / 2
Y_CARTE_OFFERTE = 240

LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 46
Y_BOUTON = 100

LARGEUR_BOUTON_DOUBLE = 180
ESPACEMENT_BOUTON_DOUBLE = 30


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


def _rect_bouton() -> tuple[float, float, float, float]:
    x = (LARGEUR_FENETRE - LARGEUR_BOUTON) / 2
    return x, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _rect_bouton_prendre() -> tuple[float, float, float, float]:
    largeur_totale = 2 * LARGEUR_BOUTON_DOUBLE + ESPACEMENT_BOUTON_DOUBLE
    x = (LARGEUR_FENETRE - largeur_totale) / 2
    return x, Y_BOUTON, LARGEUR_BOUTON_DOUBLE, HAUTEUR_BOUTON


def _rect_bouton_passer() -> tuple[float, float, float, float]:
    x_prendre, y, largeur, hauteur = _rect_bouton_prendre()
    return x_prendre + largeur + ESPACEMENT_BOUTON_DOUBLE, y, largeur, hauteur


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


class EcranAventureAsteroides(pyglet.window.Window):
    """Aventure "Asteroides" (specs.md 2.5). `self.combat_demande` signale a l'appelant d'ouvrir
    le combat scripte (choix "Affronter") ; `self.termine` signale qu'il peut sauvegarder la
    partie et enchainer sur le choix du prochain niveau (choix "Traverser" resolu)."""

    def __init__(self, partie: Partie, niveau: int):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.partie = partie
        self.niveau = niveau
        self.specs_par_id = {spec.id: spec for spec in charger_modules()}
        # Un seul chargement, reutilise pour le tirage (_resoudre_sequence_2) et pour retrouver
        # l'id de la carte offerte (_prendre_carte_offerte) : charger_cartes() reconstruit de
        # nouvelles instances a chaque appel, id_de_carte compare par identite (cf. sa docstring).
        self.cartes = charger_cartes()
        # "choix" (2 choix) -> "choix_module" (module cible des degats) -> "sequence_2" (2e coup,
        # apres le 1er deja applique au clic du module) -> "sequence_3" (carte offerte, si trouvee)
        # -> "resolu".
        self.etape: str = "choix"
        self.position_ciblee: str | None = None
        self.carte_offerte: Carte | None = None
        self.message_resolu: str = ""
        self.index_survole: int | None = None
        # Rectangle du bouton actuellement survole ("sequence_2"/"resolu"/"sequence_3" n'ont
        # qu'1 ou 2 boutons, jamais de grille) - None si la souris n'est sur aucun bouton.
        self._dernier_survol: tuple[float, float, float, float] | None = None
        self.combat_demande: bool = False
        self.termine: bool = False

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        elements = [_sprite_etire(FOND_ASTEROIDES, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        elements.append(
            pyglet.text.Label(
                f"Asteroides - Niveau {self.niveau}",
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
        elif self.etape in ("sequence_2", "resolu"):
            elements.extend(self._dessiner_message_simple(lot))
        else:
            elements.extend(self._dessiner_carte_offerte(lot))
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
        elements = [self._dessiner_instruction("Choisissez le module qui essuiera les degats.", lot)]
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

        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE,
            border_color=COULEUR_CONTOUR_SURVOLEE if survole else COULEUR_CONTOUR_CARTE, batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        libelle_label = pyglet.text.Label(
            libelle, x=cx, y=y + hauteur - 18, anchor_x="center", anchor_y="center",
            font_size=12, color=(*COULEUR_SOUS_TITRE, 255), batch=lot,
        )
        spec = self.specs_par_id[etat.module_id]
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

    def _dessiner_instruction(self, texte: str, lot: pyglet.graphics.Batch) -> pyglet.text.Label:
        return pyglet.text.Label(
            texte, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE - 100, anchor_x="center", anchor_y="center",
            font_size=16, color=(*COULEUR_TEXTE, 255), batch=lot,
        )

    def _dessiner_message_simple(self, lot: pyglet.graphics.Batch) -> list:
        message = pyglet.text.Label(
            self.message_resolu, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE / 2 + 40,
            anchor_x="center", anchor_y="center", font_size=18, color=(*COULEUR_NOM, 255),
            multiline=True, width=900, align="center", batch=lot,
        )
        return [message, *self._dessiner_bouton(_rect_bouton(), "Continuer", lot)]

    def _dessiner_carte_offerte(self, lot: pyglet.graphics.Batch) -> list:
        elements = [
            pyglet.text.Label(
                self.message_resolu, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE - 110,
                anchor_x="center", anchor_y="top", font_size=16, color=(*COULEUR_TEXTE, 255),
                multiline=True, width=900, align="center", batch=lot,
            )
        ]
        carte = self.carte_offerte
        x, y, largeur, hauteur = X_CARTE_OFFERTE, Y_CARTE_OFFERTE, LARGEUR_CARTE_OFFERTE, HAUTEUR_CARTE_OFFERTE
        cx = x + largeur / 2
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE,
            border_color=COULEUR_CONTOUR_CARTE, batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        etoile = pyglet.text.Label(
            "★", x=x + 16, y=y + hauteur - 16, anchor_x="center", anchor_y="center",
            font_size=18, color=(*COULEUR_ETOILE_RARETE[carte.rarete], 255), batch=lot,
        )
        sprite = _sprite_ajuste(carte.image, cx - IMAGE_CARTE_TAILLE / 2, y + hauteur - 30 - IMAGE_CARTE_TAILLE, IMAGE_CARTE_TAILLE, IMAGE_CARTE_TAILLE, lot)
        nom = pyglet.text.Label(
            carte.nom, x=cx, y=y + hauteur - 48 - IMAGE_CARTE_TAILLE, anchor_x="center", anchor_y="center",
            font_size=15, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        description = pyglet.text.Label(
            texte_effet_carte(carte), x=cx, y=y + hauteur - 74 - IMAGE_CARTE_TAILLE, anchor_x="center", anchor_y="top",
            font_size=11, color=(200, 200, 205, 255), multiline=True, width=largeur - 24, align="center", batch=lot,
        )
        elements.extend([cadre, etoile, sprite, nom, description])
        elements.extend(self._dessiner_bouton(_rect_bouton_prendre(), "Prendre", lot))
        elements.extend(self._dessiner_bouton(_rect_bouton_passer(), "Passer", lot))
        return elements

    def _dessiner_bouton(self, rect: tuple[float, float, float, float], texte: str, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = rect
        couleur = COULEUR_BOUTON_SURVOLE if self._rect_survolee(rect) else COULEUR_BOUTON
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        label = pyglet.text.Label(
            texte, x=x + largeur / 2, y=y + hauteur / 2, anchor_x="center", anchor_y="center",
            font_size=15, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
        return [rectangle, label]

    def _rect_survolee(self, rect: tuple[float, float, float, float]) -> bool:
        return self._dernier_survol == rect

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self._dernier_survol = None
        if self.etape == "choix":
            self.index_survole = self._index_a(x, y, len(CHOIX), _rect_choix)
        elif self.etape == "choix_module":
            self.index_survole = self._index_a(x, y, len(POSITIONS_AFFICHEES), _rect_module)
        elif self.etape in ("sequence_2", "resolu"):
            if _point_dans_rectangle(x, y, *_rect_bouton()):
                self._dernier_survol = _rect_bouton()
        else:
            if _point_dans_rectangle(x, y, *_rect_bouton_prendre()):
                self._dernier_survol = _rect_bouton_prendre()
            elif _point_dans_rectangle(x, y, *_rect_bouton_passer()):
                self._dernier_survol = _rect_bouton_passer()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.etape == "choix":
            self._cliquer_choix(x, y)
        elif self.etape == "choix_module":
            self._cliquer_module(x, y)
        elif self.etape == "sequence_2":
            if _point_dans_rectangle(x, y, *_rect_bouton()):
                self._resoudre_sequence_2()
        elif self.etape == "sequence_3":
            if _point_dans_rectangle(x, y, *_rect_bouton_prendre()):
                self._prendre_carte_offerte()
            elif _point_dans_rectangle(x, y, *_rect_bouton_passer()):
                self._passer_carte_offerte()
        elif self.etape == "resolu":
            if _point_dans_rectangle(x, y, *_rect_bouton()):
                self.termine = True

    def _cliquer_choix(self, x: int, y: int) -> None:
        index = self._index_a(x, y, len(CHOIX), _rect_choix)
        if index is None:
            return
        identifiant = CHOIX[index][0]
        if identifiant == "traverser":
            self.etape = "choix_module"
        elif identifiant == "affronter":
            self.combat_demande = True
        self.index_survole = None

    def _cliquer_module(self, x: int, y: int) -> None:
        index = self._index_a(x, y, len(POSITIONS_AFFICHEES), _rect_module)
        if index is None:
            return
        position, _libelle = POSITIONS_AFFICHEES[index]
        if self.partie.vaisseau[position] is None:
            return
        self.position_ciblee = position
        subir_degats_module(self.partie, position, DEGATS_ASTEROIDES)
        nom = self._nom_module_cible()
        self.etape = "sequence_2"
        self.message_resolu = f"Vous traversez le champ d'asteroides : {nom} perd {DEGATS_ASTEROIDES} PV."

    def _nom_module_cible(self) -> str:
        return self.specs_par_id[self.partie.vaisseau[self.position_ciblee].module_id].nom

    def _resoudre_sequence_2(self) -> None:
        subir_degats_module(self.partie, self.position_ciblee, DEGATS_ASTEROIDES)
        nom = self._nom_module_cible()
        self.carte_offerte = tirer_carte_recompense(pool_toutes_cartes(self.cartes), random.Random())
        if self.carte_offerte is None:
            self.etape = "resolu"
            self.message_resolu = (
                f"Ces asteroides n'en finissent plus : {nom} perd encore {DEGATS_ASTEROIDES} PV. "
                "Vous parvenez finalement a vous degager."
            )
        else:
            self.etape = "sequence_3"
            self.message_resolu = (
                f"Ces asteroides n'en finissent plus : {nom} perd encore {DEGATS_ASTEROIDES} PV. "
                "Pres de la sortie, vous reperez des debris..."
            )

    def _prendre_carte_offerte(self) -> None:
        ajouter_carte(self.partie, id_de_carte(self.carte_offerte, self.cartes))
        self.message_resolu = f"Vous recuperez : {self.carte_offerte.nom}."
        self.etape = "resolu"

    def _passer_carte_offerte(self) -> None:
        self.message_resolu = "Vous laissez les debris derriere vous."
        self.etape = "resolu"

    def _index_a(self, x: int, y: int, total: int, rect_de) -> int | None:
        for index in range(total):
            if _point_dans_rectangle(x, y, *rect_de(index)):
                return index
        return None
