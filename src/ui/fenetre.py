"""
Fenetre pyglet du combat du POC (grille 2x3, plusieurs modules et ennemis,
cf. poc.md et specs.md paragraphe 8). Utilise les images de assets/.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import CIBLES_SANS_CLIC, CibleCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.config_poc import creer_combat_poc
from src.gameplay.ennemi import Ennemi
from src.gameplay.module import Module
from src.gameplay.position import Colonne, Position, Rangee
from src.ui.animation import AnimationRayon

LARGEUR_FENETRE = 1280
HAUTEUR_FENETRE = 760

# Cases de la grille (modules et ennemis), cf. specs.md paragraphe 8.1
CELLULE_LARGEUR, CELLULE_HAUTEUR = 110, 90
ESPACEMENT_CELLULE = 14
FOND_PADDING = 16
HAUTEUR_BANDEAU_CASE = 42

JOUEUR_ARRIERE_X = 60
JOUEUR_AVANT_X = JOUEUR_ARRIERE_X + CELLULE_LARGEUR + ESPACEMENT_CELLULE

ENNEMI_AVANT_X = 900
ENNEMI_ARRIERE_X = ENNEMI_AVANT_X + CELLULE_LARGEUR + ESPACEMENT_CELLULE

RANGEE_Y = {
    Rangee.GAUCHE: 620,
    Rangee.MID: 620 - (CELLULE_HAUTEUR + ESPACEMENT_CELLULE),
    Rangee.DROITE: 620 - 2 * (CELLULE_HAUTEUR + ESPACEMENT_CELLULE),
}

POSITION_BASE = Position(Colonne.AVANT, Rangee.MID)

# Main de cartes, alignee en bas (specs.md paragraphe 8.1)
CARTE_LARGEUR, CARTE_HAUTEUR = 100, 140
CARTE_Y = 40
CARTE_ESPACEMENT = 120
CARTE_X_DEPART = 180
HAUTEUR_BANDEAU_CARTE = 46

# Bouton de fin de tour
BOUTON_X, BOUTON_Y = 1080, 40
BOUTON_LARGEUR, BOUTON_HAUTEUR = 140, 50

COULEUR_FOND_VAISSEAU = (30, 40, 55)
COULEUR_BANDEAU = (10, 10, 12)
OPACITE_BANDEAU = 190
COULEUR_CARTE_SURLIGNEE = (210, 180, 40)
COULEUR_BOUTON = (90, 90, 95)
COULEUR_RAYON = (255, 210, 60)
COULEUR_SURVOL = (255, 255, 255)
OPACITE_DETRUIT = 70
EPAISSEUR_RAYON = 6

_cache_images: dict[str, pyglet.image.AbstractImage] = {}


def _image(chemin: str) -> pyglet.image.AbstractImage:
    """Charge une image depuis son chemin absolu, avec mise en cache."""
    if chemin not in _cache_images:
        _cache_images[chemin] = pyglet.image.load(chemin)
    return _cache_images[chemin]


def _sprite_ajuste(
    chemin: str, x: float, y: float, largeur: float, hauteur: float, lot: pyglet.graphics.Batch
) -> pyglet.sprite.Sprite:
    """Cree un sprite pour cette image, mis a l'echelle pour tenir dans le rectangle sans deformation."""
    sprite = pyglet.sprite.Sprite(_image(chemin), batch=lot)
    echelle = min(largeur / sprite.width, hauteur / sprite.height)
    sprite.scale = echelle
    sprite.x = x + (largeur - sprite.width) / 2
    sprite.y = y + (hauteur - sprite.height) / 2
    return sprite


def _bandeau(x: float, y: float, largeur: float, hauteur: float, lot: pyglet.graphics.Batch) -> shapes.Rectangle:
    """Bandeau semi-transparent pour poser du texte lisible par-dessus une image."""
    rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=COULEUR_BANDEAU, batch=lot)
    rectangle.opacity = OPACITE_BANDEAU
    return rectangle


def _point_dans_rectangle(x: float, y: float, rx: float, ry: float, largeur: float, hauteur: float) -> bool:
    """Teste si le point (x, y) tombe dans le rectangle donne."""
    return rx <= x <= rx + largeur and ry <= y <= ry + hauteur


def _rect_module(position: Position) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) d'une case du vaisseau du joueur.

    La rangee Mid est occupee par la base en entier (les deux colonnes reunies),
    quelle que soit la colonne demandee.
    """
    if position.rangee == Rangee.MID:
        largeur = 2 * CELLULE_LARGEUR + ESPACEMENT_CELLULE
        return JOUEUR_ARRIERE_X, RANGEE_Y[Rangee.MID], largeur, CELLULE_HAUTEUR
    x = JOUEUR_AVANT_X if position.colonne == Colonne.AVANT else JOUEUR_ARRIERE_X
    return x, RANGEE_Y[position.rangee], CELLULE_LARGEUR, CELLULE_HAUTEUR


def _rect_ennemi(position: Position) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) d'une case de la flotte ennemie."""
    x = ENNEMI_AVANT_X if position.colonne == Colonne.AVANT else ENNEMI_ARRIERE_X
    return x, RANGEE_Y[position.rangee], CELLULE_LARGEUR, CELLULE_HAUTEUR


def _rect_fond_vaisseau() -> tuple[float, float, float, float]:
    """Rectangle du fond commun derriere les 5 cases du vaisseau (specs.md paragraphe 8.1)."""
    x = JOUEUR_ARRIERE_X - FOND_PADDING
    y = RANGEE_Y[Rangee.DROITE] - FOND_PADDING
    largeur = (JOUEUR_AVANT_X + CELLULE_LARGEUR) - JOUEUR_ARRIERE_X + 2 * FOND_PADDING
    hauteur = (RANGEE_Y[Rangee.GAUCHE] + CELLULE_HAUTEUR) - RANGEE_Y[Rangee.DROITE] + 2 * FOND_PADDING
    return x, y, largeur, hauteur


class FenetreCombat(pyglet.window.Window):
    """Fenetre principale : affiche le combat du POC et gere les clics/survols de souris."""

    def __init__(self, combat: Combat | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight - POC")
        self.combat = combat if combat is not None else creer_combat_poc()
        self.index_carte_selectionnee: int | None = None
        self.ennemi_survole: Ennemi | None = None
        self.rayons: list[tuple[AnimationRayon, tuple, tuple]] = []
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)

    def update(self, dt: float) -> None:
        """Fait avancer les animations en cours (appele a chaque frame)."""
        for animation, _depart, _arrivee in self.rayons:
            animation.mettre_a_jour(dt)
        self.rayons = [(a, d, ar) for a, d, ar in self.rayons if a.est_active()]

    def on_draw(self) -> None:
        """Redessine entierement la fenetre a chaque frame."""
        self.clear()
        lot = pyglet.graphics.Batch()
        # references gardees le temps du dessin, pyglet ne garde pas de reference forte tout seul
        elements = []

        elements.extend(self._dessiner_vaisseau(lot))
        elements.extend(self._dessiner_flotte(lot))
        elements.extend(self._dessiner_rayons(lot))
        elements.extend(self._dessiner_main(lot))
        elements.extend(self._dessiner_bouton_fin_tour(lot))
        elements.extend(self._dessiner_entete(lot))
        elements.extend(self._dessiner_survol(lot))

        if self.combat.etat != EtatCombat.EN_COURS:
            elements.extend(self._dessiner_message_fin(lot))

        lot.draw()

    def _dessiner_vaisseau(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine le fond commun, la base et les modules equipes du joueur."""
        elements = []
        fx, fy, fl, fh = _rect_fond_vaisseau()
        elements.append(shapes.Rectangle(fx, fy, fl, fh, color=COULEUR_FOND_VAISSEAU, batch=lot))

        elements.extend(self._dessiner_module_case(lot, POSITION_BASE, self.combat.joueur.vaisseau.base))
        for position, module in self.combat.joueur.vaisseau.modules_equipes().items():
            elements.extend(self._dessiner_module_case(lot, position, module))
        return elements

    def _dessiner_module_case(self, lot: pyglet.graphics.Batch, position: Position, module: Module) -> list:
        """Dessine une case module (image + bandeau d'etat), grisee si detruite."""
        x, y, largeur, hauteur = _rect_module(position)
        detruit = module.est_detruit()
        sprite = _sprite_ajuste(module.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
        bandeau = _bandeau(x, y, largeur, HAUTEUR_BANDEAU_CASE, lot)
        etat = "Detruit" if detruit else f"PV {module.pv}/{module.pv_max}  Bouclier {module.bouclier}"
        texte = pyglet.text.Label(
            f"{module.nom}\n{etat}",
            x=x + largeur / 2,
            y=y + HAUTEUR_BANDEAU_CASE / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=7,
            multiline=True,
            width=largeur - 4,
            align="center",
            batch=lot,
        )
        return [sprite, bandeau, texte]

    def _dessiner_flotte(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque case ennemie declaree (grisee si detruite, absente si jamais occupee)."""
        elements = []
        for position, ennemi in self.combat.flotte.positions().items():
            elements.extend(self._dessiner_ennemi_case(lot, position, ennemi))
        return elements

    def _dessiner_ennemi_case(self, lot: pyglet.graphics.Batch, position: Position, ennemi: Ennemi) -> list:
        """Dessine une case ennemie (image + bandeau d'etat), grisee si detruite."""
        x, y, largeur, hauteur = _rect_ennemi(position)
        detruit = ennemi.est_detruit()
        sprite = _sprite_ajuste(ennemi.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
        bandeau = _bandeau(x, y, largeur, HAUTEUR_BANDEAU_CASE, lot)
        etat = "Detruit" if detruit else f"PV {ennemi.pv}/{ennemi.pv_max}"
        texte = pyglet.text.Label(
            f"{ennemi.nom}\n{etat}",
            x=x + largeur / 2,
            y=y + HAUTEUR_BANDEAU_CASE / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=7,
            multiline=True,
            width=largeur - 4,
            align="center",
            batch=lot,
        )
        return [sprite, bandeau, texte]

    def _dessiner_rayons(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque rayon d'attaque encore actif entre un ennemi et sa cible."""
        elements = []
        for animation, (x1, y1), (x2, y2) in self.rayons:
            ligne = shapes.Line(x1, y1, x2, y2, thickness=EPAISSEUR_RAYON, color=COULEUR_RAYON, batch=lot)
            ligne.opacity = int(255 * animation.progression())
            elements.append(ligne)
        return elements

    def _dessiner_main(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine les cartes de la main du joueur, alignees en bas de l'ecran (specs.md paragraphe 8.1)."""
        elements = []
        main = self.combat.joueur.deck.main
        for index, carte in enumerate(main):
            x = CARTE_X_DEPART + index * CARTE_ESPACEMENT
            if index == self.index_carte_selectionnee:
                bordure = shapes.Rectangle(
                    x - 4, CARTE_Y - 4, CARTE_LARGEUR + 8, CARTE_HAUTEUR + 8, color=COULEUR_CARTE_SURLIGNEE, batch=lot
                )
                elements.append(bordure)
            elements.append(_sprite_ajuste(carte.image, x, CARTE_Y, CARTE_LARGEUR, CARTE_HAUTEUR, lot))
            elements.append(_bandeau(x, CARTE_Y, CARTE_LARGEUR, HAUTEUR_BANDEAU_CARTE, lot))
            texte = pyglet.text.Label(
                f"{carte.nom}\n{carte.valeur}  Cout {carte.cout}",
                x=x + CARTE_LARGEUR / 2,
                y=CARTE_Y + HAUTEUR_BANDEAU_CARTE / 2,
                anchor_x="center",
                anchor_y="center",
                font_size=9,
                multiline=True,
                width=CARTE_LARGEUR - 4,
                align="center",
                batch=lot,
            )
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

    def _dessiner_survol(self, lot: pyglet.graphics.Batch) -> list:
        """Affiche l'intention de l'ennemi survole (cible visee et degats), cf. poc.md paragraphe 3."""
        if self.combat.etat != EtatCombat.EN_COURS:
            return []
        if self.ennemi_survole is None or self.ennemi_survole.est_detruit():
            return []
        cible = self.combat.previsualiser_cible(self.ennemi_survole)
        if cible is None:
            return []
        position = self._position_ennemi(self.ennemi_survole)
        if position is None:
            return []
        x, y, largeur, hauteur = _rect_ennemi(position)
        texte = pyglet.text.Label(
            f"Vise : {cible.nom} ({self.ennemi_survole.degats_attaque} degats)",
            x=x + largeur / 2,
            y=y + hauteur + 16,
            anchor_x="center",
            anchor_y="bottom",
            color=(*COULEUR_SURVOL, 255),
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
            attaques = self.combat.finir_tour_joueur()
            self._demarrer_rayons(attaques)
            self.index_carte_selectionnee = None
            return

        index_carte_cliquee = self._trouver_carte_cliquee(x, y)
        if index_carte_cliquee is not None:
            carte = self.combat.joueur.deck.main[index_carte_cliquee]
            if carte.cible in CIBLES_SANS_CLIC:
                self.combat.jouer_carte(carte, None)
                self.index_carte_selectionnee = None
            else:
                deja_selectionnee = self.index_carte_selectionnee == index_carte_cliquee
                self.index_carte_selectionnee = None if deja_selectionnee else index_carte_cliquee
            return

        if self.index_carte_selectionnee is not None:
            self._essayer_de_cibler(x, y)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Met a jour l'ennemi actuellement survole par la souris, pour l'affichage de son intention."""
        self.ennemi_survole = self._ennemi_a(x, y)

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

        if carte.cible == CibleCarte.ALLIE_UNIQUE:
            cible = self._module_a(x, y)
        elif carte.cible in (CibleCarte.ENNEMI_UNIQUE, CibleCarte.LIGNE_ENNEMIE):
            cible = self._ennemi_a(x, y)
        else:
            cible = None

        if cible is not None:
            self.combat.jouer_carte(carte, cible)
            self.index_carte_selectionnee = None

    def _module_a(self, x: int, y: int) -> Module | None:
        """Renvoie le module vivant du joueur sous ce point, ou None."""
        vaisseau = self.combat.joueur.vaisseau
        bx, by, bl, bh = _rect_module(POSITION_BASE)
        if _point_dans_rectangle(x, y, bx, by, bl, bh) and not vaisseau.base.est_detruit():
            return vaisseau.base
        for position, module in vaisseau.modules_equipes().items():
            mx, my, ml, mh = _rect_module(position)
            if _point_dans_rectangle(x, y, mx, my, ml, mh) and not module.est_detruit():
                return module
        return None

    def _ennemi_a(self, x: int, y: int) -> Ennemi | None:
        """Renvoie l'ennemi vivant sous ce point, ou None."""
        for position, ennemi in self.combat.flotte.positions().items():
            ex, ey, el, eh = _rect_ennemi(position)
            if _point_dans_rectangle(x, y, ex, ey, el, eh) and not ennemi.est_detruit():
                return ennemi
        return None

    def _position_ennemi(self, ennemi: Ennemi) -> Position | None:
        """Retrouve la position d'un ennemi dans la flotte affichee, ou None."""
        for position, occupant in self.combat.flotte.positions().items():
            if occupant is ennemi:
                return position
        return None

    def _demarrer_rayons(self, attaques: list[tuple[Position, Ennemi, Module]]) -> None:
        """Demarre un rayon anime par attaque resolue ce tour (poc.md paragraphe 8)."""
        for position_ennemi, _ennemi, module_cible in attaques:
            ex, ey, el, eh = _rect_ennemi(position_ennemi)
            position_module = self._position_module(module_cible)
            mx, my, ml, mh = _rect_module(position_module)
            depart = (ex, ey + eh / 2)
            arrivee = (mx + ml, my + mh / 2)
            animation = AnimationRayon()
            animation.demarrer()
            self.rayons.append((animation, depart, arrivee))

    def _position_module(self, module: Module) -> Position:
        """Retrouve la position d'un module dans le vaisseau (la base si aucune autre ne correspond)."""
        for position, occupant in self.combat.joueur.vaisseau.modules_equipes().items():
            if occupant is module:
                return position
        return POSITION_BASE
