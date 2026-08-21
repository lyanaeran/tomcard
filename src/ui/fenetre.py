"""
Fenetre pyglet du combat du POC (grille 2x3, plusieurs modules et ennemis,
cf. poc.md et specs.md paragraphe 8). Utilise les images de assets/.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import CIBLES_SANS_CLIC, ActionCarte, Carte, CibleCarte, RareteCarte, TypeCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.config_poc import creer_combat_poc
from src.gameplay.donnees import RACINE
from src.gameplay.ennemi import DebuffActif, Ennemi
from src.gameplay.module import BuffActif, Module
from src.gameplay.position import Colonne, Position, Rangee
from src.ui.animation import AnimationPopup

LARGEUR_FENETRE = 1280
HAUTEUR_FENETRE = 800

# Cibles de camp allie parmi celles de CIBLES_SANS_CLIC (specs.md 7.2/8.3) : determine
# quel camp (allie/ennemi) doit etre touche par le clic de confirmation d'une carte sans
# clic de ciblage precis, meme principe que CIBLES_ALLIEES dans web/app.js.
CIBLES_CAMP_ALLIE = (CibleCarte.ALLIE_UNIQUE, CibleCarte.ALLIES_MULTIPLES, CibleCarte.MODULE_PRINCIPAL)

# Cases de la flotte ennemie, cf. specs.md paragraphe 8.1
CELLULE_LARGEUR, CELLULE_HAUTEUR = 110, 90
ESPACEMENT_CELLULE = 14
# Espacement vertical entre rangees : plus grand que l'espacement horizontal
# pour laisser la place aux pastilles PV/Bouclier flottant au-dessus de
# chaque case sans chevaucher la case de la rangee suivante.
ESPACEMENT_LIGNE = 44
HAUTEUR_BANDEAU_CASE = 42

ENNEMI_AVANT_X = 953
ENNEMI_ARRIERE_X = ENNEMI_AVANT_X + CELLULE_LARGEUR + ESPACEMENT_CELLULE

RANGEE_Y = {
    Rangee.GAUCHE: 580,
    Rangee.MID: 580 - (CELLULE_HAUTEUR + ESPACEMENT_LIGNE),
    Rangee.DROITE: 580 - 2 * (CELLULE_HAUTEUR + ESPACEMENT_LIGNE),
}

# Vaisseau du joueur : le module de base (assets/modules/principal.png) est
# affiche en grand, et les modules equipes se placent dans les emplacements
# vides visibles sur cette image (mesures directement sur l'image source).
# VAISSEAU_X/ENNEMI_AVANT_X sont choisis pour que le bloc vaisseau+flotte
# soit centre horizontalement dans la fenetre (marges egales des deux cotes),
# comme la disposition #grilles (justify-content:center) de la version web.
VAISSEAU_X = 93
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

# Main de cartes, centree en bas de l'ecran (specs.md paragraphe 8.1), comme
# la version web (#main, justify-content:center) plutot qu'a une position fixe.
CARTE_LARGEUR, CARTE_HAUTEUR = 100, 140
CARTE_Y = 40
CARTE_ESPACEMENT = 120
HAUTEUR_BANDEAU_CARTE = 46

# En-tete (bandeau du haut) : electricite a gauche, bouton fin de tour a
# droite, comme #entete sur la version web.
ENTETE_HAUTEUR = 60
ENTETE_Y = HAUTEUR_FENETRE - ENTETE_HAUTEUR
BOUTON_LARGEUR, BOUTON_HAUTEUR = 140, 40
BOUTON_X = LARGEUR_FENETRE - BOUTON_LARGEUR - 20
BOUTON_Y = ENTETE_Y + (ENTETE_HAUTEUR - BOUTON_HAUTEUR) / 2

COULEUR_BANDEAU = (10, 10, 12)
OPACITE_BANDEAU = 190
COULEUR_CARTE_SURLIGNEE = (210, 180, 40)
COULEUR_BOUTON = (90, 90, 95)
COULEUR_SURVOL = (255, 255, 255)
OPACITE_DETRUIT = 70

# Image de fond (specs.md/poc.md paragraphe 8), etiree pour remplir toute la
# fenetre (deformation acceptee, decision utilisateur) - meme fichier que la
# version web (assets/fond.PNG).
FOND_IMAGE = str(RACINE / "assets" / "fond.PNG")

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

# Indicateur de rarete (etoile en haut a gauche de la carte) et pastille de munitions
# restantes (en haut a droite, meme style que les pastilles PV/Bouclier), cf. specs.md 8.2
COULEUR_ETOILE_RARETE = {
    RareteCarte.BASE: (245, 245, 245),
    RareteCarte.COMMUNE: (70, 190, 90),
    RareteCarte.RARE: (60, 130, 230),
    RareteCarte.LEGENDAIRE: (235, 150, 30),
}
COULEUR_PASTILLE_MUNITION = (70, 190, 90)
COULEUR_PASTILLE_DEBUFFS = (215, 130, 40)
COULEUR_PASTILLE_BUFFS = (235, 200, 60)
# Buffs persistants (duree tout le combat, ex. Bouclier perpetuel) : compte separe de
# celui des buffs a duree limitee, teinte distincte pour les reconnaitre d'un coup d'oeil.
COULEUR_PASTILLE_BUFFS_PERSISTANTS = (170, 130, 220)

# Popups +/-N affiches 2 secondes sur une cible touchee par une carte ou une
# attaque ennemie (degats en rouge, bouclier pose en bleu, soin en vert)
TAILLE_POLICE_POPUP = 22
COULEUR_POPUP_DEGATS = COULEUR_PASTILLE_PV
COULEUR_POPUP_BOUCLIER = COULEUR_PASTILLE_BOUCLIER
COULEUR_POPUP_SOIN = (70, 200, 90)
COULEUR_POPUP_DEBUFF = (215, 130, 40)
COULEUR_POPUP_BUFF = COULEUR_PASTILLE_BUFFS
COULEUR_OMBRE_POPUP = (0, 0, 0)
DECALAGE_OMBRE_POPUP = 2

# Infobulle au survol
LARGEUR_INFOBULLE = 190
HAUTEUR_INFOBULLE_LIGNE = 18

# Groupe de rendu pour tout ce qui doit rester visible par-dessus les sprites
# (pastilles, bandeaux, textes, rayons...) : l'ordre entre sprites et formes
# n'est pas garanti par pyglet sans groupe explicite.
GROUPE_SUPERPOSITION = pyglet.graphics.Group(order=1)
# Groupe de rendu pour l'image de fond, garanti derriere tout le reste (ordre
# negatif < ordre par defaut des sprites vaisseau/flotte/cartes).
GROUPE_FOND = pyglet.graphics.Group(order=-1)

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


def _sprite_etire(
    chemin: str,
    x: float,
    y: float,
    largeur: float,
    hauteur: float,
    lot: pyglet.graphics.Batch,
    groupe: pyglet.graphics.Group | None = None,
) -> pyglet.sprite.Sprite:
    """Cree un sprite pour cette image, etire independamment en largeur et en hauteur
    pour remplir exactement le rectangle sur ses 4 cotes (le cadre de l'image du module
    doit se superposer pile a celui du vaisseau). Contrairement a `_sprite_ajuste`, le
    ratio de l'image n'est pas preserve : une legere deformation est acceptee."""
    sprite = pyglet.sprite.Sprite(_image(chemin), batch=lot, group=groupe)
    sprite.scale_x = largeur / sprite.width
    sprite.scale_y = hauteur / sprite.height
    sprite.x = x
    sprite.y = y
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


def _pastilles_buffs_module(module: Module, cx_pv: float, cy: float, lot: pyglet.graphics.Batch) -> list:
    """Pastilles du nombre de buffs actifs sur un module (specs.md 12.3/12.5), a gauche de
    sa pastille PV (par-dessus l'emplacement Bouclier) : une doree pour les buffs a duree
    limitee, une distincte pour les buffs persistants (qui durent tout le combat) - comptes
    separes, jamais additionnes dans une seule pastille. Chacune absente si son compte est a
    0. cx_pv/cy : memes reperes que la pastille PV de ce module (cf. _pastilles_pv_bouclier)."""
    buffs_duree = [buff for buff in module.buffs_actifs if buff.tours_restants is not None]
    buffs_persistants = [buff for buff in module.buffs_actifs if buff.tours_restants is None]
    elements = []
    cx = cx_pv - 2 * (RAYON_PASTILLE * 2 + MARGE_PASTILLE)
    if buffs_duree:
        elements += _pastille(cx, cy, COULEUR_PASTILLE_BUFFS, len(buffs_duree), lot)
        cx -= RAYON_PASTILLE * 2 + MARGE_PASTILLE
    if buffs_persistants:
        elements += _pastille(cx, cy, COULEUR_PASTILLE_BUFFS_PERSISTANTS, len(buffs_persistants), lot)
    return elements


def _texte_et_couleur_effet(carte: Carte, valeur_effective: int) -> tuple[str, tuple[int, int, int]]:
    """Texte (+/-valeur reellement appliquee) et couleur du popup associe a l'effet d'une carte jouee."""
    if carte.type == TypeCarte.ATTAQUE:
        return f"-{valeur_effective}", COULEUR_POPUP_DEGATS
    if carte.type == TypeCarte.DEFENSE:
        return f"+{valeur_effective}", COULEUR_POPUP_BOUCLIER
    if carte.type == TypeCarte.DEBUFF:
        if carte.action == ActionCarte.VULNERABILITE:
            return f"+{valeur_effective}%", COULEUR_POPUP_DEBUFF
        if carte.action == ActionCarte.REDIRECTION_CIBLE:
            return "Detourne !", COULEUR_POPUP_DEBUFF
        return f"-{valeur_effective}", COULEUR_POPUP_DEBUFF
    if carte.type == TypeCarte.BUFF:
        return f"+{valeur_effective}", COULEUR_POPUP_BUFF
    return f"+{valeur_effective}", COULEUR_POPUP_SOIN


def _libelle_debuff(debuff: DebuffActif) -> str:
    """Texte d'une ligne d'infobulle pour un debuff actif (specs.md 12.1/12.4/12.6)."""
    if debuff.action == ActionCarte.VULNERABILITE:
        texte = f"Vulnerabilite +{debuff.valeur}%"
    elif debuff.action == ActionCarte.REDIRECTION_CIBLE:
        texte = "Tir detourne"
    else:
        texte = f"Degats reduits -{debuff.valeur}"
    tour = "tour" if debuff.tours_restants == 1 else "tours"
    return f"{texte} ({debuff.tours_restants} {tour})"


def _libelle_buff(buff: BuffActif) -> str:
    """Texte d'une ligne d'infobulle pour un buff actif (specs.md 12.3/12.5)."""
    if buff.action == ActionCarte.BOUCLIER_PAR_TOUR:
        texte = f"+{buff.valeur} bouclier/tour"
    else:
        texte = f"Buff +{buff.valeur}"
    if buff.tours_restants is None:
        duree = "illimite"
    else:
        duree = f"{buff.tours_restants} tour" + ("" if buff.tours_restants == 1 else "s")
    return f"{texte} ({duree})"


def _lignes_buffs(module: Module) -> list[str]:
    """Lignes d'infobulle pour les buffs actifs d'un module (specs.md 12.3/12.5), groupees
    separement : buffs a duree limitee d'abord, puis buffs persistants (qui durent tout le
    combat) - jamais melanges, meme separation que les deux pastilles (cf. _pastilles_buffs_module)."""
    buffs_duree = [buff for buff in module.buffs_actifs if buff.tours_restants is not None]
    buffs_persistants = [buff for buff in module.buffs_actifs if buff.tours_restants is None]
    lignes = [_libelle_buff(buff) for buff in buffs_duree]
    if buffs_duree and buffs_persistants:
        lignes.append("Persistants :")
    lignes.extend(_libelle_buff(buff) for buff in buffs_persistants)
    return lignes


class FenetreCombat(pyglet.window.Window):
    """Fenetre principale : affiche le combat du POC et gere les clics/survols de souris."""

    def __init__(self, combat: Combat | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight - POC")
        self.combat = combat if combat is not None else creer_combat_poc()
        self.index_carte_selectionnee: int | None = None
        self.entite_survolee: Module | Ennemi | None = None
        self.popups: list[tuple[AnimationPopup, str, tuple[int, int, int], float, float]] = []
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)

    def update(self, dt: float) -> None:
        """Fait avancer les animations en cours (appele a chaque frame)."""
        for animation, _texte, _couleur, _x, _y in self.popups:
            animation.mettre_a_jour(dt)
        self.popups = [popup for popup in self.popups if popup[0].est_active()]

    def on_draw(self) -> None:
        """Redessine entierement la fenetre a chaque frame."""
        self.clear()
        lot = pyglet.graphics.Batch()
        # references gardees le temps du dessin, pyglet ne garde pas de reference forte tout seul
        elements = []

        elements.extend(self._dessiner_fond(lot))
        elements.extend(self._dessiner_vaisseau(lot))
        elements.extend(self._dessiner_flotte(lot))
        elements.extend(self._dessiner_popups(lot))
        elements.extend(self._dessiner_main(lot))
        elements.extend(self._dessiner_entete(lot))
        elements.extend(self._dessiner_survol(lot))

        if self.combat.etat != EtatCombat.EN_COURS:
            elements.extend(self._dessiner_message_fin(lot))

        lot.draw()

    def _dessiner_fond(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine l'image de fond, etiree pour remplir toute la fenetre (deformation
        acceptee), comme l'arriere-plan de la version web (body en fond.PNG)."""
        return [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot, groupe=GROUPE_FOND)]

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
            cy_base = HAUT_PARE_BRISE_VAISSEAU_Y + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
            elements.extend(_pastilles_buffs_module(base, CENTRE_PARE_BRISE_VAISSEAU_X, cy_base, lot))

        for position, module in self.combat.joueur.vaisseau.modules_equipes().items():
            elements.extend(self._dessiner_module_case(lot, position, module))
        return elements

    def _dessiner_module_case(self, lot: pyglet.graphics.Batch, position: Position, module: Module) -> list:
        """Dessine une case module (image + pastilles PV/Bouclier/Buffs), grisee si detruite."""
        x, y, largeur, hauteur = _rect_module(position)
        detruit = module.est_detruit()
        sprite = _sprite_etire(module.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot)]
        elements = [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, module.pv, module.bouclier, lot)]
        cx_pv = x + largeur - RAYON_PASTILLE - MARGE_PASTILLE
        cy = y + hauteur + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
        elements.extend(_pastilles_buffs_module(module, cx_pv, cy, lot))
        return elements

    def _dessiner_flotte(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque case ennemie declaree (grisee si detruite, absente si jamais occupee)."""
        elements = []
        for position, ennemi in self.combat.flotte.positions().items():
            elements.extend(self._dessiner_ennemi_case(lot, position, ennemi))
        return elements

    def _dessiner_ennemi_case(self, lot: pyglet.graphics.Batch, position: Position, ennemi: Ennemi) -> list:
        """Dessine une case ennemie (image + pastille PV, + pastille orange du nombre de
        debuffs actifs s'il y en a au moins un), grisee si detruite."""
        x, y, largeur, hauteur = _rect_ennemi(position)
        detruit = ennemi.est_detruit()
        sprite = _sprite_ajuste(ennemi.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot)]
        elements = [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, ennemi.pv, None, lot)]
        if ennemi.debuffs_actifs:
            cx_pv = x + largeur - RAYON_PASTILLE - MARGE_PASTILLE
            cx_debuffs = cx_pv - RAYON_PASTILLE * 2 - MARGE_PASTILLE
            cy = y + hauteur + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
            elements += _pastille(cx_debuffs, cy, COULEUR_PASTILLE_DEBUFFS, len(ennemi.debuffs_actifs), lot)
        return elements

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

    def _dessiner_popups(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque popup +/-N encore actif sur sa cible (une ombre noire derriere
        le texte colore, pour rester lisible par-dessus n'importe quelle image)."""
        elements = []
        for _animation, texte, couleur, x, y in self.popups:
            ombre = pyglet.text.Label(
                texte,
                x=x + DECALAGE_OMBRE_POPUP,
                y=y - DECALAGE_OMBRE_POPUP,
                anchor_x="center",
                anchor_y="center",
                font_size=TAILLE_POLICE_POPUP,
                color=(*COULEUR_OMBRE_POPUP, 255),
                batch=lot,
                group=GROUPE_SUPERPOSITION,
            )
            avant_plan = pyglet.text.Label(
                texte,
                x=x,
                y=y,
                anchor_x="center",
                anchor_y="center",
                font_size=TAILLE_POLICE_POPUP,
                color=(*couleur, 255),
                batch=lot,
                group=GROUPE_SUPERPOSITION,
            )
            elements.extend([ombre, avant_plan])
        return elements

    def _x_carte_depart(self) -> float:
        """X du bord gauche de la premiere carte, pour que la rangee soit centree
        horizontalement dans la fenetre, comme #main (justify-content:center) sur le web."""
        main = self.combat.joueur.deck.main
        if not main:
            return LARGEUR_FENETRE / 2
        largeur_rangee = (len(main) - 1) * CARTE_ESPACEMENT + CARTE_LARGEUR
        return (LARGEUR_FENETRE - largeur_rangee) / 2

    def _dessiner_main(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine les cartes de la main du joueur, centrees en bas de l'ecran (specs.md paragraphe 8.1)."""
        elements = []
        main = self.combat.joueur.deck.main
        x_depart = self._x_carte_depart()
        for index, carte in enumerate(main):
            x = x_depart + index * CARTE_ESPACEMENT
            if index == self.index_carte_selectionnee:
                bordure = shapes.Rectangle(
                    x - 4, CARTE_Y - 4, CARTE_LARGEUR + 8, CARTE_HAUTEUR + 8, color=COULEUR_CARTE_SURLIGNEE, batch=lot
                )
                elements.append(bordure)
            elements.append(_sprite_ajuste(carte.image, x, CARTE_Y, CARTE_LARGEUR, CARTE_HAUTEUR, lot))
            elements.append(_bandeau(x, CARTE_Y, CARTE_LARGEUR, HAUTEUR_BANDEAU_CARTE, lot))
            elements.extend(self._dessiner_etoile_rarete(x, carte, lot))
            if carte.munitions_restantes is not None:
                elements.extend(
                    _pastille(
                        x + CARTE_LARGEUR - _RAYON_TOTAL_PASTILLE,
                        CARTE_Y + CARTE_HAUTEUR - _RAYON_TOTAL_PASTILLE,
                        COULEUR_PASTILLE_MUNITION,
                        carte.munitions_restantes,
                        lot,
                    )
                )
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

    def _dessiner_etoile_rarete(self, x: float, carte: Carte, lot: pyglet.graphics.Batch) -> list:
        """Etoile de rarete en haut a gauche de la carte (specs.md paragraphe 8.2)."""
        couleur = COULEUR_ETOILE_RARETE[carte.rarete]
        ombre = pyglet.text.Label(
            "★",
            x=x + 11,
            y=CARTE_Y + CARTE_HAUTEUR - 9,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(0, 0, 0, 255),
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        etoile = pyglet.text.Label(
            "★",
            x=x + 10,
            y=CARTE_Y + CARTE_HAUTEUR - 10,
            anchor_x="center",
            anchor_y="center",
            font_size=16,
            color=(*couleur, 255),
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        return [ombre, etoile]

    def _dessiner_bouton_fin_tour(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine le bouton permettant de terminer le tour du joueur, dans l'en-tete."""
        rectangle = shapes.Rectangle(
            BOUTON_X, BOUTON_Y, BOUTON_LARGEUR, BOUTON_HAUTEUR, color=COULEUR_BOUTON, batch=lot, group=GROUPE_SUPERPOSITION
        )
        texte = pyglet.text.Label(
            "Fin de tour",
            x=BOUTON_X + BOUTON_LARGEUR / 2,
            y=BOUTON_Y + BOUTON_HAUTEUR / 2,
            anchor_x="center",
            anchor_y="center",
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        return [rectangle, texte]

    def _dessiner_entete(self, lot: pyglet.graphics.Batch) -> list:
        """Bandeau du haut : electricite disponible a gauche, bouton fin de tour a droite
        (meme composition que #entete sur la version web)."""
        joueur = self.combat.joueur
        elements = [_bandeau(0, ENTETE_Y, LARGEUR_FENETRE, ENTETE_HAUTEUR, lot)]
        texte = pyglet.text.Label(
            f"Electricite : {joueur.electricite}",
            x=20,
            y=ENTETE_Y + ENTETE_HAUTEUR / 2,
            anchor_x="left",
            anchor_y="center",
            batch=lot,
            group=GROUPE_SUPERPOSITION,
        )
        elements.append(texte)
        elements.extend(self._dessiner_bouton_fin_tour(lot))
        return elements

    def _dessiner_survol(self, lot: pyglet.graphics.Batch) -> list:
        """Affiche une infobulle (nom, PV/PV max, Bouclier) sur le module/ennemi survole.

        Pour un ennemi, ajoute aussi son intention (cible visee et degats), cf. poc.md paragraphe 3.
        Pour un module, ajoute le detail de ses buffs actifs (specs.md 12.3/12.5).
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
                lignes.append(f"Vise : {cible.nom} ({entite.degats_attaque_effectifs()} degats)")
            elif any(debuff.action == ActionCarte.REDIRECTION_CIBLE for debuff in entite.debuffs_actifs):
                # Tir allie actif (specs.md 12.6) : la cible reelle (un autre ennemi) n'est
                # tiree au hasard qu'a la resolution du tour, jamais au survol - cf.
                # Combat.previsualiser_cible/_cible_redirection pour rester deterministe.
                lignes.append("Vise : un allie au hasard")
            lignes.extend(_libelle_debuff(debuff) for debuff in entite.debuffs_actifs)
        else:
            rect = self._rect_du_module(entite)
            lignes = [entite.nom, f"PV {entite.pv}/{entite.pv_max}", f"Bouclier {entite.bouclier}"]
            lignes.extend(_lignes_buffs(entite))

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
            self._afficher_popups_attaques_ennemi(attaques)
            self.index_carte_selectionnee = None
            return

        index_carte_cliquee = self._trouver_carte_cliquee(x, y)
        if index_carte_cliquee is not None:
            # Un clic sur une carte l'arme (ou la desarme si deja selectionnee) sans la
            # jouer, meme pour les cartes sans clic de ciblage (specs.md 8.3) : un second
            # clic de confirmation sur une case du bon camp reste necessaire, comme sur
            # le web, pour eviter qu'un simple clic sur la carte ne la joue par accident.
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
        x_depart = self._x_carte_depart()
        for index in range(len(main)):
            carte_x = x_depart + index * CARTE_ESPACEMENT
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

        if carte.cible in CIBLES_SANS_CLIC:
            # La cible precise ne compte pas pour l'effet (jouer_carte l'ignore), mais un
            # clic de confirmation sur une case du bon camp reste necessaire (comme sur le
            # web, cf. CIBLES_ALLIEES/cliquerCase dans app.js) : n'importe quel module vivant
            # confirme une carte de camp allie, n'importe quel ennemi vivant une carte de
            # camp ennemi.
            camp_allie = carte.cible in CIBLES_CAMP_ALLIE
            touche = (self._module_a(x, y) if camp_allie else self._ennemi_a(x, y)) is not None
            if not touche:
                return
            cible = None
        elif carte.cible in (CibleCarte.ALLIE_UNIQUE, CibleCarte.COLONNE_AVANT_ALLIEE):
            cible = self._module_a(x, y)
            if cible is None:
                return
        else:
            cible = self._ennemi_a(x, y)
            if cible is None:
                return

        cibles_touchees = self.combat.jouer_carte(carte, cible)
        self._afficher_popups_carte(carte, cibles_touchees)
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

    def _afficher_popups_carte(self, carte: Carte, cibles: list[tuple[Module | Ennemi, int]]) -> None:
        """Affiche un popup +/-N (montant reellement applique) sur chaque cible touchee par une carte jouee."""
        for cible, valeur_effective in cibles:
            texte, couleur = _texte_et_couleur_effet(carte, valeur_effective)
            self._ajouter_popup(cible, texte, couleur)

    def _afficher_popups_attaques_ennemi(self, attaques: list[tuple[Position, Ennemi, Module | Ennemi, int]]) -> None:
        """Affiche un popup -N (degats reellement infliges) sur chaque cible touchee par une
        attaque ennemie - un module, ou un autre ennemi si Tir allie est actif (specs.md 12.6)."""
        for _position, _ennemi, cible_touchee, degats_effectifs in attaques:
            self._ajouter_popup(cible_touchee, f"-{degats_effectifs}", COULEUR_POPUP_DEGATS)

    def _ajouter_popup(self, cible: Module | Ennemi, texte: str, couleur: tuple[int, int, int]) -> None:
        """Demarre l'affichage d'un popup +/-N centre sur la case de cette cible, pour 2 secondes."""
        x, y, largeur, hauteur = self._rect_de_cible(cible)
        animation = AnimationPopup()
        animation.demarrer()
        self.popups.append((animation, texte, couleur, x + largeur / 2, y + hauteur / 2))

    def _rect_de_cible(self, cible: Module | Ennemi) -> tuple[float, float, float, float]:
        """Rectangle (x, y, largeur, hauteur) de la case d'un module ou d'un ennemi."""
        if isinstance(cible, Ennemi):
            position = self._position_ennemi(cible)
            return _rect_ennemi(position) if position is not None else (0, 0, 0, 0)
        return self._rect_du_module(cible)

    def _rect_du_module(self, module: Module) -> tuple[float, float, float, float]:
        """Rectangle d'un module du joueur (son emplacement equipe, ou tout le vaisseau si c'est la base)."""
        for position, occupant in self.combat.joueur.vaisseau.modules_equipes().items():
            if occupant is module:
                return _rect_module(position)
        return _rect_vaisseau()
