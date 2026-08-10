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
HAUTEUR_FENETRE = 800

# Cases de la flotte ennemie, cf. specs.md paragraphe 8.1
CELLULE_LARGEUR, CELLULE_HAUTEUR = 110, 90
ESPACEMENT_CELLULE = 14
# Espacement vertical entre rangees : plus grand que l'espacement horizontal
# pour laisser la place aux pastilles PV/Bouclier flottant au-dessus de
# chaque case sans chevaucher la case de la rangee suivante.
ESPACEMENT_LIGNE = 44
HAUTEUR_BANDEAU_CASE = 42

ENNEMI_AVANT_X = 900
ENNEMI_ARRIERE_X = ENNEMI_AVANT_X + CELLULE_LARGEUR + ESPACEMENT_CELLULE

RANGEE_Y = {
    Rangee.GAUCHE: 580,
    Rangee.MID: 580 - (CELLULE_HAUTEUR + ESPACEMENT_LIGNE),
    Rangee.DROITE: 580 - 2 * (CELLULE_HAUTEUR + ESPACEMENT_LIGNE),
}

# Vaisseau du joueur : le module de base (assets/modules/principal.png) est
# affiche en grand, et les modules equipes se placent dans les emplacements
# vides visibles sur cette image (mesures directement sur l'image source).
VAISSEAU_X = 40
VAISSEAU_Y = 300
VAISSEAU_LARGEUR = 640
_TAILLE_IMAGE_PRINCIPAL = (1205, 651)  # largeur, hauteur de assets/modules/principal.png
VAISSEAU_HAUTEUR = VAISSEAU_LARGEUR * _TAILLE_IMAGE_PRINCIPAL[1] / _TAILLE_IMAGE_PRINCIPAL[0]
_ECHELLE_VAISSEAU = VAISSEAU_LARGEUR / _TAILLE_IMAGE_PRINCIPAL[0]

# Emplacements des modules mesures sur l'image (coordonnees locales, origine
# bas-gauche de l'image, avant la mise a l'echelle). Mesures sur le cadre
# metallique complet du vaisseau (pas seulement le trou noir interieur), pour
# que le cadre du module equipe vienne recouvrir celui du vaisseau.
_EMPLACEMENTS_MODULES_IMAGE = {
    Position(Colonne.ARRIERE, Rangee.GAUCHE): (350, 407, 223, 216),
    Position(Colonne.AVANT, Rangee.GAUCHE): (606, 407, 223, 216),
    Position(Colonne.ARRIERE, Rangee.DROITE): (349, 29, 223, 215),
    Position(Colonne.AVANT, Rangee.DROITE): (607, 29, 223, 215),
}

# Repere du pare-brise mesure sur l'image source (coordonnees locales,
# origine bas-gauche : centre horizontal, bord superieur), pour placer la
# pastille PV/Bouclier de la base juste au-dessus de lui.
_CENTRE_PARE_BRISE_IMAGE = 853
_HAUT_PARE_BRISE_IMAGE = 360
CENTRE_PARE_BRISE_VAISSEAU_X = VAISSEAU_X + _CENTRE_PARE_BRISE_IMAGE * _ECHELLE_VAISSEAU
HAUT_PARE_BRISE_VAISSEAU_Y = VAISSEAU_Y + _HAUT_PARE_BRISE_IMAGE * _ECHELLE_VAISSEAU

# Main de cartes, alignee en bas (specs.md paragraphe 8.1)
CARTE_LARGEUR, CARTE_HAUTEUR = 100, 140
CARTE_Y = 40
CARTE_ESPACEMENT = 120
CARTE_X_DEPART = 180
HAUTEUR_BANDEAU_CARTE = 46

# Bouton de fin de tour
BOUTON_X, BOUTON_Y = 1080, 40
BOUTON_LARGEUR, BOUTON_HAUTEUR = 140, 50

COULEUR_BANDEAU = (10, 10, 12)
OPACITE_BANDEAU = 190
COULEUR_CARTE_SURLIGNEE = (210, 180, 40)
COULEUR_BOUTON = (90, 90, 95)
COULEUR_RAYON = (255, 210, 60)
COULEUR_SURVOL = (255, 255, 255)
OPACITE_DETRUIT = 70
EPAISSEUR_RAYON = 6

# Pastilles PV (rouge) / Bouclier (bleu), flottant au-dessus de chaque case
# (et non par-dessus l'image, pour ne pas la cacher)
RAYON_PASTILLE = 14
EPAISSEUR_CONTOUR_PASTILLE = 3
MARGE_PASTILLE = 6  # espace horizontal entre les deux pastilles / bord de case
MARGE_PASTILLE_HAUT = 4  # espace vertical entre le haut de la case et la pastille
COULEUR_PASTILLE_PV = (190, 40, 40)
COULEUR_PASTILLE_BOUCLIER = (50, 110, 200)
_RAYON_TOTAL_PASTILLE = RAYON_PASTILLE + EPAISSEUR_CONTOUR_PASTILLE
HAUTEUR_ZONE_PASTILLES = MARGE_PASTILLE_HAUT + 2 * _RAYON_TOTAL_PASTILLE

# Infobulle au survol
LARGEUR_INFOBULLE = 190
HAUTEUR_INFOBULLE_LIGNE = 18

# Groupe de rendu pour tout ce qui doit rester visible par-dessus les sprites
# (pastilles, bandeaux, textes, rayons...) : l'ordre entre sprites et formes
# n'est pas garanti par pyglet sans groupe explicite.
GROUPE_SUPERPOSITION = pyglet.graphics.Group(order=1)

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


def _sprite_couvrant(
    chemin: str, x: float, y: float, largeur: float, hauteur: float, lot: pyglet.graphics.Batch
) -> pyglet.sprite.Sprite:
    """Cree un sprite pour cette image, mis a l'echelle pour recouvrir entierement le
    rectangle (quitte a legerement deborder), contrairement a `_sprite_ajuste` qui evite
    tout depassement au prix de bandes vides quand le ratio de l'image ne correspond pas
    exactement a celui du cadre."""
    sprite = pyglet.sprite.Sprite(_image(chemin), batch=lot)
    echelle = max(largeur / sprite.width, hauteur / sprite.height)
    sprite.scale = echelle
    sprite.x = x + (largeur - sprite.width) / 2
    sprite.y = y + (hauteur - sprite.height) / 2
    return sprite


def _bandeau(x: float, y: float, largeur: float, hauteur: float, lot: pyglet.graphics.Batch) -> shapes.Rectangle:
    """Bandeau semi-transparent pour poser du texte lisible par-dessus une image."""
    rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=COULEUR_BANDEAU, batch=lot, group=GROUPE_SUPERPOSITION)
    rectangle.opacity = OPACITE_BANDEAU
    return rectangle


def _pastille(x_centre: float, y_centre: float, couleur: tuple, valeur: int, lot: pyglet.graphics.Batch) -> list:
    """Petit cercle colore avec une valeur numerique au centre (PV ou Bouclier).

    Un contour sombre est dessine derriere pour rester lisible par-dessus des
    images de fond claires ou colorees.
    """
    contour = shapes.Circle(
        x_centre, y_centre, _RAYON_TOTAL_PASTILLE, color=(0, 0, 0), batch=lot, group=GROUPE_SUPERPOSITION
    )
    cercle = shapes.Circle(x_centre, y_centre, RAYON_PASTILLE, color=couleur, batch=lot, group=GROUPE_SUPERPOSITION)
    texte = pyglet.text.Label(
        str(valeur),
        x=x_centre,
        y=y_centre,
        anchor_x="center",
        anchor_y="center",
        font_size=9,
        batch=lot,
        group=GROUPE_SUPERPOSITION,
    )
    return [contour, cercle, texte]


def _pastilles_pv_bouclier(
    x: float,
    y: float,
    largeur: float,
    hauteur: float,
    pv: int,
    bouclier: int | None,
    lot: pyglet.graphics.Batch,
    centre_x: float | None = None,
    haut: float | None = None,
) -> list:
    """Pastilles PV (rouge) et Bouclier (bleu, si applicable), flottant au-dessus d'une case
    (pour ne pas cacher son image). Par defaut positionnees a partir du rectangle (x, y,
    largeur, hauteur) de la case ; `centre_x`/`haut` permettent de les ancrer ailleurs
    (ex. au-dessus du pare-brise pour la base, plutot qu'au-dessus de tout le vaisseau)."""
    haut_reference = haut if haut is not None else y + hauteur
    cy = haut_reference + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
    cx_pv = centre_x if centre_x is not None else x + largeur - RAYON_PASTILLE - MARGE_PASTILLE
    elements = _pastille(cx_pv, cy, COULEUR_PASTILLE_PV, pv, lot)
    if bouclier is not None:
        cx_bouclier = cx_pv - RAYON_PASTILLE * 2 - MARGE_PASTILLE
        elements += _pastille(cx_bouclier, cy, COULEUR_PASTILLE_BOUCLIER, bouclier, lot)
    return elements


def _point_dans_rectangle(x: float, y: float, rx: float, ry: float, largeur: float, hauteur: float) -> bool:
    """Teste si le point (x, y) tombe dans le rectangle donne."""
    return rx <= x <= rx + largeur and ry <= y <= ry + hauteur


def _rect_vaisseau() -> tuple[float, float, float, float]:
    """Rectangle englobant le grand sprite du vaisseau du joueur (module de base)."""
    return VAISSEAU_X, VAISSEAU_Y, VAISSEAU_LARGEUR, VAISSEAU_HAUTEUR


def _rect_module(position: Position) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) d'un emplacement de module equipe,
    positionne dans l'emplacement vide correspondant sur l'image du vaisseau."""
    ex, ey, el, eh = _EMPLACEMENTS_MODULES_IMAGE[position]
    return (
        VAISSEAU_X + ex * _ECHELLE_VAISSEAU,
        VAISSEAU_Y + ey * _ECHELLE_VAISSEAU,
        el * _ECHELLE_VAISSEAU,
        eh * _ECHELLE_VAISSEAU,
    )


def _rect_ennemi(position: Position) -> tuple[float, float, float, float]:
    """Rectangle (x, y, largeur, hauteur) d'une case de la flotte ennemie."""
    x = ENNEMI_AVANT_X if position.colonne == Colonne.AVANT else ENNEMI_ARRIERE_X
    return x, RANGEE_Y[position.rangee], CELLULE_LARGEUR, CELLULE_HAUTEUR


class FenetreCombat(pyglet.window.Window):
    """Fenetre principale : affiche le combat du POC et gere les clics/survols de souris."""

    def __init__(self, combat: Combat | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight - POC")
        self.combat = combat if combat is not None else creer_combat_poc()
        self.index_carte_selectionnee: int | None = None
        self.entite_survolee: Module | Ennemi | None = None
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
        """Dessine le grand sprite du vaisseau (base) et les modules equipes dans leurs emplacements."""
        elements = []
        base = self.combat.joueur.vaisseau.base
        vx, vy, vl, vh = _rect_vaisseau()
        detruit = base.est_detruit()
        sprite = _sprite_ajuste(base.image, vx, vy, vl, vh, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
        elements.append(sprite)
        if detruit:
            elements.extend(self._texte_detruit(vx, vy, vl, vh, lot))
        else:
            elements.extend(
                _pastilles_pv_bouclier(
                    vx,
                    vy,
                    vl,
                    vh,
                    base.pv,
                    base.bouclier,
                    lot,
                    centre_x=CENTRE_PARE_BRISE_VAISSEAU_X,
                    haut=HAUT_PARE_BRISE_VAISSEAU_Y,
                )
            )

        for position, module in self.combat.joueur.vaisseau.modules_equipes().items():
            elements.extend(self._dessiner_module_case(lot, position, module))
        return elements

    def _dessiner_module_case(self, lot: pyglet.graphics.Batch, position: Position, module: Module) -> list:
        """Dessine une case module (image + pastilles PV/Bouclier), grisee si detruite."""
        x, y, largeur, hauteur = _rect_module(position)
        detruit = module.est_detruit()
        sprite = _sprite_couvrant(module.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot)]
        return [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, module.pv, module.bouclier, lot)]

    def _dessiner_flotte(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque case ennemie declaree (grisee si detruite, absente si jamais occupee)."""
        elements = []
        for position, ennemi in self.combat.flotte.positions().items():
            elements.extend(self._dessiner_ennemi_case(lot, position, ennemi))
        return elements

    def _dessiner_ennemi_case(self, lot: pyglet.graphics.Batch, position: Position, ennemi: Ennemi) -> list:
        """Dessine une case ennemie (image + pastille PV), grisee si detruite."""
        x, y, largeur, hauteur = _rect_ennemi(position)
        detruit = ennemi.est_detruit()
        sprite = _sprite_ajuste(ennemi.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot)]
        return [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, ennemi.pv, None, lot)]

    def _texte_detruit(self, x: float, y: float, largeur: float, hauteur: float, lot: pyglet.graphics.Batch) -> list:
        """Bandeau + texte "Detruit" centre sur une case."""
        hauteur_bandeau = min(HAUTEUR_BANDEAU_CASE, hauteur)
        bandeau = _bandeau(x, y + hauteur / 2 - hauteur_bandeau / 2, largeur, hauteur_bandeau, lot)
        texte = pyglet.text.Label(
            "Detruit",
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=9,
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        return [bandeau, texte]

    def _dessiner_rayons(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque rayon d'attaque encore actif entre un ennemi et sa cible."""
        elements = []
        for animation, (x1, y1), (x2, y2) in self.rayons:
            ligne = shapes.Line(
                x1, y1, x2, y2, thickness=EPAISSEUR_RAYON, color=COULEUR_RAYON, batch=lot, group=GROUPE_SUPERPOSITION
            )
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
        """Affiche une infobulle (nom, PV/PV max, Bouclier) sur le module/ennemi survole.

        Pour un ennemi, ajoute aussi son intention (cible visee et degats), cf. poc.md paragraphe 3.
        """
        if self.combat.etat != EtatCombat.EN_COURS:
            return []
        entite = self.entite_survolee
        if entite is None or entite.est_detruit():
            return []

        if isinstance(entite, Ennemi):
            position = self._position_ennemi(entite)
            if position is None:
                return []
            rect = _rect_ennemi(position)
            lignes = [entite.nom, f"PV {entite.pv}/{entite.pv_max}"]
            cible = self.combat.previsualiser_cible(entite)
            if cible is not None:
                lignes.append(f"Vise : {cible.nom} ({entite.degats_attaque} degats)")
        else:
            rect = self._rect_du_module(entite)
            lignes = [entite.nom, f"PV {entite.pv}/{entite.pv_max}", f"Bouclier {entite.bouclier}"]

        return self._infobulle(rect, lignes, lot)

    def _infobulle(self, rect: tuple, lignes: list, lot: pyglet.graphics.Batch) -> list:
        """Dessine une infobulle (fond + texte) au-dessus du rectangle donne."""
        x, y, largeur, hauteur = rect
        hauteur_infobulle = HAUTEUR_INFOBULLE_LIGNE * len(lignes) + 8
        bx = x + largeur / 2 - LARGEUR_INFOBULLE / 2
        by = y + hauteur + HAUTEUR_ZONE_PASTILLES + 8
        elements = [_bandeau(bx, by, LARGEUR_INFOBULLE, hauteur_infobulle, lot)]
        texte = pyglet.text.Label(
            "\n".join(lignes),
            x=x + largeur / 2,
            y=by + hauteur_infobulle / 2,
            anchor_x="center",
            anchor_y="center",
            multiline=True,
            width=LARGEUR_INFOBULLE - 8,
            align="center",
            font_size=9,
            color=(*COULEUR_SURVOL, 255),
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        elements.append(texte)
        return elements

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
            group=GROUPE_SUPERPOSITION,
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
        """Met a jour le module/ennemi actuellement survole par la souris, pour l'infobulle."""
        self.entite_survolee = self._ennemi_a(x, y) or self._module_a(x, y)

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
        """Renvoie le module vivant du joueur sous ce point, ou None.

        Les emplacements de modules equipes sont testes en premier (ils sont
        inclus dans le rectangle du vaisseau) ; sinon un clic sur le reste du
        vaisseau vise la base.
        """
        vaisseau = self.combat.joueur.vaisseau
        for position, module in vaisseau.modules_equipes().items():
            mx, my, ml, mh = _rect_module(position)
            if _point_dans_rectangle(x, y, mx, my, ml, mh) and not module.est_detruit():
                return module
        vx, vy, vl, vh = _rect_vaisseau()
        if _point_dans_rectangle(x, y, vx, vy, vl, vh) and not vaisseau.base.est_detruit():
            return vaisseau.base
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
            mx, my, ml, mh = self._rect_du_module(module_cible)
            depart = (ex, ey + eh / 2)
            arrivee = (mx + ml, my + mh / 2)
            animation = AnimationRayon()
            animation.demarrer()
            self.rayons.append((animation, depart, arrivee))

    def _rect_du_module(self, module: Module) -> tuple[float, float, float, float]:
        """Rectangle d'un module du joueur (son emplacement equipe, ou tout le vaisseau si c'est la base)."""
        for position, occupant in self.combat.joueur.vaisseau.modules_equipes().items():
            if occupant is module:
                return _rect_module(position)
        return _rect_vaisseau()
