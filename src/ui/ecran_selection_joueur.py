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

from src.gameplay.donnees import RACINE
from src.gameplay.partie import Profil, creer_profil, lister_profils, supprimer_profil
from src.ui.fenetre import (
    FOND_IMAGE,
    GROUPE_SUPERPOSITION,
    HAUTEUR_FENETRE,
    LARGEUR_FENETRE,
    _sprite_ajuste,
    _sprite_etire,
)

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

# Bouton de suppression (croix rouge, meme icone que "Quitter" en combat - specs.md 8.1) a
# droite de chaque ligne de profil : detruit definitivement le profil et ses parties
# sauvegardees (src/gameplay/partie.py:supprimer_profil), apres confirmation (cf. dialogue
# ci-dessous - action destructive irreversible, jamais executee sans confirmation explicite).
ICONE_SUPPRIMER = str(RACINE / "assets" / "interface" / "quitter.png")
TAILLE_BOUTON_SUPPRIMER = 32
MARGE_BOUTON_SUPPRIMER = 10

# Dialogue de confirmation (specs.md 10.3) : boite centree par-dessus un voile sombre.
LARGEUR_DIALOGUE = 480
HAUTEUR_DIALOGUE = 180
COULEUR_VOILE = (0, 0, 0)
OPACITE_VOILE = 170
COULEUR_FOND_DIALOGUE = (30, 34, 46)
COULEUR_CONTOUR_DIALOGUE = (200, 60, 60)
LARGEUR_BOUTON_DIALOGUE = 140
HAUTEUR_BOUTON_DIALOGUE = 44
COULEUR_BOUTON_OUI = (170, 40, 40)
COULEUR_BOUTON_ANNULER = (70, 80, 100)


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
        # Profil vise par le bouton croix rouge, en attente de confirmation (specs.md 10.3) -
        # None quand aucun dialogue de confirmation n'est affiche. Tant que ce n'est pas None,
        # les autres interactions de l'ecran (choisir/creer un profil) sont bloquees.
        self.profil_a_supprimer: Profil | None = None

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
        if self.profil_a_supprimer is not None:
            elements.extend(self._dessiner_dialogue_confirmation(lot))
        return elements

    def _rect_ligne(self, index: int) -> tuple[float, float, float, float]:
        x = (LARGEUR_FENETRE - LARGEUR_LIGNE) / 2
        y = Y_HAUT_LISTE - HAUTEUR_LIGNE - index * (HAUTEUR_LIGNE + ESPACEMENT_LIGNE)
        return x, y, LARGEUR_LIGNE, HAUTEUR_LIGNE

    def _rect_bouton_supprimer(self, index: int) -> tuple[float, float, float, float]:
        """Rectangle de la croix rouge de suppression, a droite de la ligne de ce profil."""
        x, y, largeur, hauteur = self._rect_ligne(index)
        taille = TAILLE_BOUTON_SUPPRIMER
        bx = x + largeur - taille - MARGE_BOUTON_SUPPRIMER
        by = y + (hauteur - taille) / 2
        return bx, by, taille, taille

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
        bx, by, btaille, _btaille = self._rect_bouton_supprimer(index)
        bouton_supprimer = _sprite_ajuste(ICONE_SUPPRIMER, bx, by, btaille, btaille, lot)
        return [cadre, nom, bouton_supprimer]

    def _dessiner_dialogue_confirmation(self, lot: pyglet.graphics.Batch) -> list:
        """Voile sombre + boite de confirmation (specs.md 10.3), au-dessus de tout le reste
        (GROUPE_SUPERPOSITION, cf. CLAUDE.md "pieges pyglet connus" - l'ordre de dessin entre
        formes/texte n'est sinon pas garanti dans un Batch partage)."""
        voile = shapes.Rectangle(0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, color=COULEUR_VOILE, batch=lot, group=GROUPE_SUPERPOSITION)
        voile.opacity = OPACITE_VOILE

        x, y, largeur, hauteur = self._rect_dialogue()
        boite = shapes.BorderedRectangle(
            x,
            y,
            largeur,
            hauteur,
            border=3,
            color=COULEUR_FOND_DIALOGUE,
            border_color=COULEUR_CONTOUR_DIALOGUE,
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        message = pyglet.text.Label(
            f"Vous allez detruire le joueur {self.profil_a_supprimer.nom}, etes-vous sur ?",
            x=x + largeur / 2,
            y=y + hauteur - 45,
            anchor_x="center",
            anchor_y="center",
            font_size=15,
            multiline=True,
            width=largeur - 40,
            align="center",
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        elements = [voile, boite, message]
        elements.extend(self._dessiner_bouton_dialogue(self._rect_bouton_oui(), "Oui", COULEUR_BOUTON_OUI, lot))
        elements.extend(self._dessiner_bouton_dialogue(self._rect_bouton_annuler(), "Annuler", COULEUR_BOUTON_ANNULER, lot))
        return elements

    def _dessiner_bouton_dialogue(
        self, rect: tuple[float, float, float, float], texte: str, couleur: tuple[int, int, int], lot: pyglet.graphics.Batch
    ) -> list:
        x, y, largeur, hauteur = rect
        fond = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot, group=GROUPE_SUPERPOSITION)
        label = pyglet.text.Label(
            texte,
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=15,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        return [fond, label]

    def _rect_dialogue(self) -> tuple[float, float, float, float]:
        x = (LARGEUR_FENETRE - LARGEUR_DIALOGUE) / 2
        y = (HAUTEUR_FENETRE - HAUTEUR_DIALOGUE) / 2
        return x, y, LARGEUR_DIALOGUE, HAUTEUR_DIALOGUE

    def _rect_bouton_annuler(self) -> tuple[float, float, float, float]:
        dx, dy, dlargeur, _dhauteur = self._rect_dialogue()
        x = dx + dlargeur / 2 - LARGEUR_BOUTON_DIALOGUE - 10
        y = dy + 26
        return x, y, LARGEUR_BOUTON_DIALOGUE, HAUTEUR_BOUTON_DIALOGUE

    def _rect_bouton_oui(self) -> tuple[float, float, float, float]:
        dx, dy, dlargeur, _dhauteur = self._rect_dialogue()
        x = dx + dlargeur / 2 + 10
        y = dy + 26
        return x, y, LARGEUR_BOUTON_DIALOGUE, HAUTEUR_BOUTON_DIALOGUE

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
        if self.profil_a_supprimer is not None:
            return
        self.index_survole = self._index_ligne_a(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.profil_a_supprimer is not None:
            self._traiter_clic_dialogue(x, y)
            return
        index_supprimer = self._index_bouton_supprimer_a(x, y)
        if index_supprimer is not None:
            self.profil_a_supprimer = self.profils[index_supprimer]
            return
        index = self._index_ligne_a(x, y)
        if index is not None:
            self.profil_choisi = self.profils[index]

    def _traiter_clic_dialogue(self, x: int, y: int) -> None:
        """Resout un clic pendant que le dialogue de confirmation est affiche : Oui detruit
        reellement le profil (action irreversible), Annuler ou un clic hors des deux boutons
        referme simplement le dialogue sans rien supprimer."""
        if _point_dans_rectangle(x, y, *self._rect_bouton_oui()):
            supprimer_profil(self.profil_a_supprimer.id)
            self.profils = lister_profils()
        self.profil_a_supprimer = None

    def on_text(self, text: str) -> None:
        if self.profil_a_supprimer is not None:
            return
        if text.isprintable():
            self.nom_saisi += text

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if self.profil_a_supprimer is not None:
            if symbol in (key.ESCAPE,):
                self.profil_a_supprimer = None
            return
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

    def _index_bouton_supprimer_a(self, x: int, y: int) -> int | None:
        for index in range(len(self.profils)):
            if _point_dans_rectangle(x, y, *self._rect_bouton_supprimer(index)):
                return index
        return None
