"""
Fenetre pyglet du combat du POC (version simplifiee du paragraphe 8 de specs.md :
un seul module, un seul ennemi, pas de grille de rangs).
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import CibleCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.config_poc import creer_combat_poc
from src.ui.animation import AnimationRayon

LARGEUR_FENETRE = 960
HAUTEUR_FENETRE = 600

# Zone du module du joueur, en haut a gauche
MODULE_X, MODULE_Y, MODULE_TAILLE = 120, 380, 150

# Zone de l'ennemi, en haut a droite
ENNEMI_X, ENNEMI_Y, ENNEMI_TAILLE = 690, 380, 150

# Main de cartes, alignee en bas (specs.md paragraphe 8.1)
CARTE_LARGEUR, CARTE_HAUTEUR = 100, 140
CARTE_Y = 40
CARTE_ESPACEMENT = 120
CARTE_X_DEPART = 180

# Bouton de fin de tour
BOUTON_X, BOUTON_Y = 800, 40
BOUTON_LARGEUR, BOUTON_HAUTEUR = 140, 50

COULEUR_MODULE = (70, 130, 200)
COULEUR_ENNEMI = (190, 70, 70)
COULEUR_CARTE = (55, 55, 60)
COULEUR_CARTE_SURLIGNEE = (210, 180, 40)
COULEUR_BOUTON = (90, 90, 95)
COULEUR_RAYON = (255, 210, 60)
EPAISSEUR_RAYON = 6


def _point_dans_rectangle(x: float, y: float, rx: float, ry: float, largeur: float, hauteur: float) -> bool:
    """Teste si le point (x, y) tombe dans le rectangle donne."""
    return rx <= x <= rx + largeur and ry <= y <= ry + hauteur


class FenetreCombat(pyglet.window.Window):
    """Fenetre principale : affiche le combat du POC et gere les clics de souris."""

    def __init__(self, combat: Combat | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight - POC")
        self.combat = combat if combat is not None else creer_combat_poc()
        self.index_carte_selectionnee: int | None = None
        self.animation_rayon = AnimationRayon()
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)

    def update(self, dt: float) -> None:
        """Fait avancer les animations en cours (appele a chaque frame)."""
        self.animation_rayon.mettre_a_jour(dt)

    def on_draw(self) -> None:
        """Redessine entierement la fenetre a chaque frame."""
        self.clear()
        lot = pyglet.graphics.Batch()
        # references gardees le temps du dessin, pyglet ne garde pas de reference forte tout seul
        elements = []

        elements.extend(self._dessiner_module(lot))
        elements.extend(self._dessiner_ennemi(lot))
        elements.extend(self._dessiner_rayon(lot))
        elements.extend(self._dessiner_main(lot))
        elements.extend(self._dessiner_bouton_fin_tour(lot))
        elements.extend(self._dessiner_entete(lot))

        if self.combat.etat != EtatCombat.EN_COURS:
            elements.extend(self._dessiner_message_fin(lot))

        lot.draw()

    def _dessiner_module(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine le module de base du joueur avec ses PV et son bouclier."""
        module = self.combat.joueur.module
        rectangle = shapes.Rectangle(MODULE_X, MODULE_Y, MODULE_TAILLE, MODULE_TAILLE, color=COULEUR_MODULE, batch=lot)
        texte = pyglet.text.Label(
            f"Module\nPV {module.pv}/{module.pv_max}\nBouclier {module.bouclier}",
            x=MODULE_X + MODULE_TAILLE / 2,
            y=MODULE_Y + MODULE_TAILLE / 2,
            anchor_x="center",
            anchor_y="center",
            multiline=True,
            width=MODULE_TAILLE,
            align="center",
            batch=lot,
        )
        return [rectangle, texte]

    def _dessiner_ennemi(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine l'ennemi avec ses PV."""
        ennemi = self.combat.ennemi
        rectangle = shapes.Rectangle(ENNEMI_X, ENNEMI_Y, ENNEMI_TAILLE, ENNEMI_TAILLE, color=COULEUR_ENNEMI, batch=lot)
        texte = pyglet.text.Label(
            f"Ennemi\nPV {ennemi.pv}/{ennemi.pv_max}",
            x=ENNEMI_X + ENNEMI_TAILLE / 2,
            y=ENNEMI_Y + ENNEMI_TAILLE / 2,
            anchor_x="center",
            anchor_y="center",
            multiline=True,
            width=ENNEMI_TAILLE,
            align="center",
            batch=lot,
        )
        return [rectangle, texte]

    def _dessiner_rayon(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine le rayon d'attaque entre l'ennemi et le module, s'il est actif."""
        if not self.animation_rayon.est_active():
            return []
        y_rayon = MODULE_Y + MODULE_TAILLE / 2
        ligne = shapes.Line(
            MODULE_X + MODULE_TAILLE,
            y_rayon,
            ENNEMI_X,
            y_rayon,
            thickness=EPAISSEUR_RAYON,
            color=COULEUR_RAYON,
            batch=lot,
        )
        ligne.opacity = int(255 * self.animation_rayon.progression())
        return [ligne]

    def _dessiner_main(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine les cartes de la main du joueur, alignees en bas de l'ecran (specs.md paragraphe 8.1)."""
        elements = []
        main = self.combat.joueur.deck.main
        for index, carte in enumerate(main):
            x = CARTE_X_DEPART + index * CARTE_ESPACEMENT
            couleur = COULEUR_CARTE_SURLIGNEE if index == self.index_carte_selectionnee else COULEUR_CARTE
            rectangle = shapes.Rectangle(x, CARTE_Y, CARTE_LARGEUR, CARTE_HAUTEUR, color=couleur, batch=lot)
            texte = pyglet.text.Label(
                f"{carte.nom}\n{carte.valeur}\nCout {carte.cout}",
                x=x + CARTE_LARGEUR / 2,
                y=CARTE_Y + CARTE_HAUTEUR / 2,
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                width=CARTE_LARGEUR,
                align="center",
                batch=lot,
            )
            elements.append(rectangle)
            elements.append(texte)
        return elements

    def _dessiner_bouton_fin_tour(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine le bouton permettant de terminer le tour du joueur."""
        rectangle = shapes.Rectangle(BOUTON_X, BOUTON_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR, color=COULEUR_BOUTON, batch=lot)
        texte = pyglet.text.Label(
            "Fin de tour",
            x=BOUTON_X + BOUTON_LARGEUR / 2,
            y=BOUTON_Y + BOUTON_HAUTEUR / 2,
            anchor_x="center",
            anchor_y="center",
            batch=lot,
        )
        return [rectangle, texte]

    def _dessiner_entete(self, lot: pyglet.graphics.Batch) -> list:
        """Affiche l'electricite disponible en haut de l'ecran."""
        joueur = self.combat.joueur
        texte = pyglet.text.Label(
            f"Electricite : {joueur.electricite}",
            x=20,
            y=HAUTEUR_FENETRE - 30,
            batch=lot,
        )
        return [texte]

    def _dessiner_message_fin(self, lot: pyglet.graphics.Batch) -> list:
        """Affiche le message de fin de combat (victoire ou defaite)."""
        message = "Victoire !" if self.combat.etat == EtatCombat.VICTOIRE else "Defaite"
        texte = pyglet.text.Label(
            message,
            x=LARGEUR_FENETRE / 2,
            y=HAUTEUR_FENETRE / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=36,
            batch=lot,
        )
        return [texte]

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Gere les clics de souris : selection de carte, ciblage, fin de tour."""
        if self.combat.etat != EtatCombat.EN_COURS:
            return

        if _point_dans_rectangle(x, y, BOUTON_X, BOUTON_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR):
            self.combat.finir_tour_joueur()
            self.animation_rayon.demarrer()
            self.index_carte_selectionnee = None
            return

        index_carte_cliquee = self._trouver_carte_cliquee(x, y)
        if index_carte_cliquee is not None:
            deja_selectionnee = self.index_carte_selectionnee == index_carte_cliquee
            self.index_carte_selectionnee = None if deja_selectionnee else index_carte_cliquee
            return

        if self.index_carte_selectionnee is not None:
            self._essayer_de_cibler(x, y)

    def _trouver_carte_cliquee(self, x: int, y: int) -> int | None:
        """Renvoie l'index de la carte de la main cliquee, ou None si aucune."""
        main = self.combat.joueur.deck.main
        for index in range(len(main)):
            carte_x = CARTE_X_DEPART + index * CARTE_ESPACEMENT
            if _point_dans_rectangle(x, y, carte_x, CARTE_Y, CARTE_LARGEUR, CARTE_HAUTEUR):
                return index
        return None

    def _essayer_de_cibler(self, x: int, y: int) -> None:
        """Si le clic tombe sur une cible valide pour la carte selectionnee, la joue."""
        main = self.combat.joueur.deck.main
        if self.index_carte_selectionnee is None or self.index_carte_selectionnee >= len(main):
            self.index_carte_selectionnee = None
            return
        carte = main[self.index_carte_selectionnee]

        cible_module = _point_dans_rectangle(x, y, MODULE_X, MODULE_Y, MODULE_TAILLE, MODULE_TAILLE)
        cible_ennemi = _point_dans_rectangle(x, y, ENNEMI_X, ENNEMI_Y, ENNEMI_TAILLE, ENNEMI_TAILLE)

        if carte.cible == CibleCarte.SOI and cible_module:
            self.combat.jouer_carte(carte)
            self.index_carte_selectionnee = None
        elif carte.cible == CibleCarte.ENNEMI and cible_ennemi:
            self.combat.jouer_carte(carte)
            self.index_carte_selectionnee = None
