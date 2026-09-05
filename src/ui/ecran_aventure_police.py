"""
Ecran Aventure "Police" (specs.md 2.5) : une carte est tiree au hasard du deck reel du joueur et
affichee avant les choix - Confiscation / Mettre aux normes / Detourner l'attention (une seule
fois par Aventure, pas par run - etat purement local a cet ecran). Fenetre pyglet independante
comme les autres ecrans du parcours, mute directement `partie.vaisseau`/`partie.deck`/`partie.argent`
(src/gameplay/partie.py) - c'est a l'appelant de sauvegarder la partie une fois l'ecran ferme.
"""

import random

import pyglet
from pyglet import shapes

from src.gameplay.carte import Carte
from src.gameplay.donnees import RACINE, charger_cartes
from src.gameplay.partie import (
    COUT_METTRE_AUX_NORMES,
    Partie,
    deck_de_la_partie,
    demarrer_aventure_police,
    detourner_aventure_police,
    payer_mise_aux_normes,
    retirer_carte,
)
from src.ui import barre_laterale
from src.ui.ecran_deck import EcranDeck
from src.ui.ecran_vaisseau import EcranVaisseau
from src.ui.fenetre import COULEUR_ETOILE_RARETE, HAUTEUR_FENETRE, LARGEUR_FENETRE, _sprite_ajuste, _sprite_etire, texte_effet_carte

FOND_POLICE = str(RACINE / "assets" / "aventure" / "police.png")

# Reutilise l'icone de assets/station_service/mettre_a_jour.png, desormais sans texte incruste
# (fournie par l'utilisateur) - le titre est de toute facon toujours redessine a cote dans le
# rectangle de texte, cf. commentaire de CHOIX plus bas.
_ICONE_METTRE_AUX_NORMES = str(RACINE / "assets" / "station_service" / "mettre_a_jour.png")
_ICONE_CONFISCATION = str(RACINE / "assets" / "aventure" / "confiscation.png")
_ICONE_DETOURNER = str(RACINE / "assets" / "aventure" / "detourner.png")

DESCRIPTION = "Pas de bol, votre dernier achat n'est pas aux normes. Et la police de l'espace ne plaisante pas trop dans le coin..."

COULEUR_TEXTE = (255, 255, 255)
COULEUR_SOUS_TITRE = (200, 200, 205)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_CARTE_ACTUELLE = (235, 150, 30)
COULEUR_CONTOUR_SURVOLEE = (255, 255, 255)
COULEUR_FOND_VIDE = (15, 17, 24)
COULEUR_NOM = (255, 220, 120)
COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)
OPACITE_FOND = 190

# (identifiant, image, titre, description). "detourner" retire de la liste affichee une fois
# utilise (specs.md 2.5 : une seule fois par Aventure, pas par run).
CHOIX = (
    ("confiscation", _ICONE_CONFISCATION, "Confiscation", "Supprime cette carte de votre deck."),
    ("mettre_aux_normes", _ICONE_METTRE_AUX_NORMES, "Mettre aux normes", f"Payez {COUT_METTRE_AUX_NORMES} € et gardez la carte."),
    ("detourner", _ICONE_DETOURNER, "Detourner l'attention", "Tire une autre carte (une seule fois)."),
)

# Carte tiree affichee seule au-dessus des choix, comme une carte en combat (image en haut, texte
# en dessous) plutot que la ligne image+texte des choix en dessous - pour ne pas donner
# l'impression que c'est elle-meme une option cliquable (specs.md 2.5). Meme composition que
# _dessiner_carte_offerte de l'Aventure Astéroïdes (etoile + image + nom + description empiles).
LARGEUR_CARTE_ACTUELLE = 240
HAUTEUR_CARTE_ACTUELLE = 250
IMAGE_CARTE_ACTUELLE_TAILLE = 130
X_CARTE_ACTUELLE = (LARGEUR_FENETRE - LARGEUR_CARTE_ACTUELLE) / 2
Y_HAUT_CARTE_ACTUELLE = 675

# Lignes de choix empilees en dessous - meme convention que les autres Aventures (specs.md 2.5).
LARGEUR_LIGNE = 820
HAUTEUR_LIGNE_CHOIX = 110
TAILLE_IMAGE = 100
ESPACEMENT_IMAGE_TEXTE = 16
ESPACEMENT_LIGNES_CHOIX = 16
ESPACEMENT_CARTE_CHOIX = 30
Y_HAUT_CHOIX = Y_HAUT_CARTE_ACTUELLE - HAUTEUR_CARTE_ACTUELLE - ESPACEMENT_CARTE_CHOIX

LARGEUR_BOUTON = 220
HAUTEUR_BOUTON = 46
Y_BOUTON = 100


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


def _rect_bouton() -> tuple[float, float, float, float]:
    x = (LARGEUR_FENETRE - LARGEUR_BOUTON) / 2
    return x, Y_BOUTON, LARGEUR_BOUTON, HAUTEUR_BOUTON


def _rect_choix(index: int) -> tuple[float, float, float, float]:
    """Ligne complete (image + rectangle de texte) du choix visible a cet index - empilees du
    haut vers le bas, index 0 en premier."""
    x = (LARGEUR_FENETRE - LARGEUR_LIGNE) / 2
    y = Y_HAUT_CHOIX - HAUTEUR_LIGNE_CHOIX - index * (HAUTEUR_LIGNE_CHOIX + ESPACEMENT_LIGNES_CHOIX)
    return x, y, LARGEUR_LIGNE, HAUTEUR_LIGNE_CHOIX


class EcranAventurePolice(pyglet.window.Window):
    """Aventure "Police" (specs.md 2.5). `self.termine` signale a l'appelant qu'il peut
    sauvegarder la partie et enchainer sur le choix du prochain niveau."""

    def __init__(self, partie: Partie, aleatoire: random.Random | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.partie = partie
        # Un seul chargement, reutilise pour chaque tirage (charger_cartes() reconstruit de
        # nouvelles instances a chaque appel, ce qui casserait toute comparaison par identite).
        self.cartes = charger_cartes()
        # Instance explicite (jamais le module random global directement, cf. CLAUDE.md
        # "Determinisme du tirage aleatoire"), injectable pour un test reproductible.
        self.aleatoire = aleatoire or random.Random()
        # Etat de resolution de l'Aventure (carte tiree, disponibilite de "Detourner l'attention")
        # possede par le gameplay (src/gameplay/partie.py:EtatAventurePolice), pas par cet ecran -
        # gameplay commun aux deux interfaces (CLAUDE.md), web garde la meme donnee cote bridge.py.
        self.etat_police = demarrer_aventure_police(partie, self.aleatoire)
        self.etape: str = "choix"
        self.message_resolu: str = ""
        # Message d'echec affiche sous les choix (etape "choix" uniquement, ex. Argent
        # insuffisant) - distinct de message_resolu, qui n'est dessine qu'a l'etape "resolu".
        self.message_erreur: str = ""
        self.index_survole: int | None = None
        self.bouton_survole: bool = False
        self.survole_barre: str | None = None
        self.termine: bool = False

    def _carte_actuelle(self) -> Carte:
        return self.cartes[self.etat_police.id_carte_actuelle]

    def _choix_visibles(self) -> tuple:
        if self.etat_police.detourner_disponible:
            return CHOIX
        return tuple(choix for choix in CHOIX if choix[0] != "detourner")

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        elements = [_sprite_etire(FOND_POLICE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        elements.append(
            pyglet.text.Label(
                "Police",
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
            elements.append(
                pyglet.text.Label(
                    DESCRIPTION,
                    x=LARGEUR_FENETRE / 2,
                    y=HAUTEUR_FENETRE - 95,
                    anchor_x="center",
                    anchor_y="center",
                    font_size=14,
                    color=(*COULEUR_SOUS_TITRE, 255),
                    batch=lot,
                )
            )
            elements.extend(self._dessiner_carte_actuelle(lot))
            for index, (_identifiant, image, titre, description) in enumerate(self._choix_visibles()):
                elements.extend(self._dessiner_ligne_choix(index, image, titre, description, lot))
            if self.message_erreur:
                elements.append(
                    pyglet.text.Label(
                        self.message_erreur,
                        x=LARGEUR_FENETRE / 2,
                        y=15,
                        anchor_x="center",
                        anchor_y="center",
                        font_size=15,
                        color=(220, 90, 90, 255),
                        batch=lot,
                    )
                )
        else:
            elements.extend(self._dessiner_resolu(lot))
        elements.extend(barre_laterale.dessiner(self.partie, self.survole_barre, lot))
        return elements

    def _dessiner_carte_actuelle(self, lot: pyglet.graphics.Batch) -> list:
        """Carte tiree, seule et non cliquable, dans le meme format qu'une carte en combat (image
        en haut, texte en dessous) - pour ne pas la confondre avec les choix en dessous."""
        carte = self._carte_actuelle()
        x, y = X_CARTE_ACTUELLE, Y_HAUT_CARTE_ACTUELLE - HAUTEUR_CARTE_ACTUELLE
        largeur, hauteur = LARGEUR_CARTE_ACTUELLE, HAUTEUR_CARTE_ACTUELLE
        cx = x + largeur / 2
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=2, color=COULEUR_FOND_CARTE,
            border_color=COULEUR_CONTOUR_CARTE_ACTUELLE, batch=lot,
        )
        cadre.opacity = OPACITE_FOND
        etoile = pyglet.text.Label(
            "★", x=x + 16, y=y + hauteur - 16, anchor_x="center", anchor_y="center",
            font_size=18, color=(*COULEUR_ETOILE_RARETE[carte.rarete], 255), batch=lot,
        )
        taille_image = IMAGE_CARTE_ACTUELLE_TAILLE
        sprite = _sprite_ajuste(
            carte.image, cx - taille_image / 2, y + hauteur - 30 - taille_image, taille_image, taille_image, lot
        )
        nom = pyglet.text.Label(
            f"{carte.nom}  (⚡{carte.cout})", x=cx, y=y + hauteur - 48 - taille_image,
            anchor_x="center", anchor_y="center", font_size=15, color=(*COULEUR_NOM, 255), batch=lot,
        )
        description = pyglet.text.Label(
            texte_effet_carte(carte), x=cx, y=y + hauteur - 70 - taille_image,
            anchor_x="center", anchor_y="top", font_size=12, color=(*COULEUR_TEXTE, 255),
            multiline=True, width=largeur - 24, align="center", batch=lot,
        )
        return [cadre, etoile, sprite, nom, description]

    def _dessiner_ligne_choix(
        self, index: int, image: str | None, titre: str, description: str, lot: pyglet.graphics.Batch
    ) -> list:
        """Une ligne de choix : image carree a gauche (None -> case vide en attendant un visuel
        dedie), rectangle de texte (titre + description) a droite (specs.md 2.5)."""
        x, y, largeur, hauteur = _rect_choix(index)
        survole = index == self.index_survole
        couleur_contour = COULEUR_CONTOUR_SURVOLEE if survole else COULEUR_CONTOUR_CARTE
        y_image = y + (hauteur - TAILLE_IMAGE) / 2

        cadre_image = shapes.BorderedRectangle(
            x, y_image, TAILLE_IMAGE, TAILLE_IMAGE, border=2,
            color=COULEUR_FOND_VIDE if image is None else COULEUR_FOND_CARTE,
            border_color=couleur_contour, batch=lot,
        )
        cadre_image.opacity = OPACITE_FOND
        elements = [cadre_image]
        if image is not None:
            elements.append(_sprite_ajuste(image, x, y_image, TAILLE_IMAGE, TAILLE_IMAGE, lot))

        x_texte = x + TAILLE_IMAGE + ESPACEMENT_IMAGE_TEXTE
        largeur_texte = largeur - TAILLE_IMAGE - ESPACEMENT_IMAGE_TEXTE
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

    def _dessiner_resolu(self, lot: pyglet.graphics.Batch) -> list:
        message = pyglet.text.Label(
            self.message_resolu, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE / 2 + 40,
            anchor_x="center", anchor_y="center", font_size=20, color=(*COULEUR_NOM, 255),
            multiline=True, width=900, align="center", batch=lot,
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
            self.index_survole = self._index_a(x, y, len(self._choix_visibles()), _rect_choix)
        else:
            self.index_survole = None
        self.bouton_survole = self.etape == "resolu" and _point_dans_rectangle(x, y, *_rect_bouton())
        self.survole_barre = barre_laterale.bouton_survole(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        bouton_barre = barre_laterale.bouton_survole(x, y)
        if bouton_barre == "deck":
            barre_laterale.ouvrir_survol(EcranDeck(deck_de_la_partie(self.partie)))
            return
        if bouton_barre == "vaisseau":
            barre_laterale.ouvrir_survol(EcranVaisseau(self.partie))
            return
        if self.etape == "choix":
            self._cliquer_choix(x, y)
        elif _point_dans_rectangle(x, y, *_rect_bouton()):
            self.termine = True

    def _cliquer_choix(self, x: int, y: int) -> None:
        choix_visibles = self._choix_visibles()
        index = self._index_a(x, y, len(choix_visibles), _rect_choix)
        if index is None:
            return
        identifiant = choix_visibles[index][0]
        if identifiant == "confiscation":
            carte = self._carte_actuelle()
            retirer_carte(self.partie, self.etat_police.id_carte_actuelle)
            self.message_resolu = f"Carte confisquee : {carte.nom}."
            self.etape = "resolu"
        elif identifiant == "mettre_aux_normes":
            if payer_mise_aux_normes(self.partie):
                self.message_resolu = f"Vous mettez {self._carte_actuelle().nom} aux normes."
                self.etape = "resolu"
            else:
                self.message_erreur = "Argent insuffisant pour mettre cette carte aux normes."
        elif identifiant == "detourner":
            detourner_aventure_police(self.etat_police, self.partie, self.aleatoire)
            self.message_erreur = ""
            self.index_survole = None

    def _index_a(self, x: int, y: int, total: int, rect_de) -> int | None:
        for index in range(total):
            if _point_dans_rectangle(x, y, *rect_de(index)):
                return index
        return None
