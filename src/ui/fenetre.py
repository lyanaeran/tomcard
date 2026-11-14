"""
Fenetre pyglet du combat (grille 2x3, plusieurs modules et ennemis, cf. specs.md paragraphe 8),
sur le moteur de la refonte (CombatNew, specs/refonte-combat.md). N'affiche que ce que le gameplay
decide : cases valides d'une carte (cibles_possibles), carte jouable (peut_jouer), intentions des
ennemis, journal. Les textes sont dans src/ui/textes_combat.py.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte_new import Camp, CarteNew, RareteCarte
from src.gameplay.combat_new import ELECTRICITE_PAR_TOUR, CombatNew, EtatCombatNew
from src.gameplay.ennemi_new import EnnemiNew
from src.gameplay.module_new import ModuleNew
from src.gameplay.partie import RACINE, Partie
from src.gameplay.position import Colonne, Position, Rangee
from src.gameplay.statut_new import Statut
from src.gameplay.vaisseau_new import CASES_PAR_EMPLACEMENT
from src.ui import textes_combat
from src.ui.animation import AnimationPopup
from src.ui.commun import chemin_image

LARGEUR_FENETRE = 1280
HAUTEUR_FENETRE = 800

# Cases de la flotte ennemie, cf. specs.md paragraphe 8.1. Agrandies (etaient 110x90, decision
# utilisateur : paraissaient petites a cote des modules, y compris apres un premier passage a
# 120x98 - encore trop timide) : alignees sur le meme empreinte que les modules du vaisseau
# (250x220 mis a l'echelle, cf. _EMPLACEMENTS_MODULES_IMAGE plus bas, ~135x119) plutot qu'une
# taille independante.
CELLULE_LARGEUR, CELLULE_HAUTEUR = 135, 119
ESPACEMENT_CELLULE = 17
HAUTEUR_BANDEAU_CASE = 42
# Bandeau de l'intention, en bas de la case d'un ennemi
HAUTEUR_BANDEAU_INTENTION = 20

# Vaisseau du joueur : le module de base (assets/modules/principal.png) est
# affiche en grand, et les modules equipes se placent dans les emplacements
# vides visibles sur cette image (mesures directement sur l'image source).
# VAISSEAU_LARGEUR/VAISSEAU_Y bornes par la bande verticale disponible entre
# la main de cartes (CARTE_Y/CARTE_HAUTEUR) et le haut de la fenetre : l'image
# fournie par l'utilisateur (quasi carree, contrairement a l'ancienne tres
# large) impose une hauteur bien plus grande a largeur egale.
VAISSEAU_X = 150
VAISSEAU_Y = 190
VAISSEAU_LARGEUR = 527
_TAILLE_IMAGE_PRINCIPAL = (978, 965)  # largeur, hauteur de assets/modules/principal.png
VAISSEAU_HAUTEUR = VAISSEAU_LARGEUR * _TAILLE_IMAGE_PRINCIPAL[1] / _TAILLE_IMAGE_PRINCIPAL[0]
_ECHELLE_VAISSEAU = VAISSEAU_LARGEUR / _TAILLE_IMAGE_PRINCIPAL[0]

# ENNEMI_AVANT_X derive (plutot qu'une valeur fixe) pour que le bloc vaisseau+flotte reste
# centre horizontalement dans la fenetre (marges egales des deux cotes, meme principe que
# #grilles/justify-content:center cote web) quelle que soit la taille des cases ennemies :
# marge gauche (VAISSEAU_X) = marge droite (LARGEUR_FENETRE - bord droit de la colonne arriere).
ENNEMI_AVANT_X = LARGEUR_FENETRE - 2 * CELLULE_LARGEUR - ESPACEMENT_CELLULE - VAISSEAU_X
ENNEMI_ARRIERE_X = ENNEMI_AVANT_X + CELLULE_LARGEUR + ESPACEMENT_CELLULE

# Emplacements des modules mesures sur l'image (coordonnees locales, origine
# bas-gauche de l'image, avant la mise a l'echelle). Mesures sur le cadre
# metallique complet du vaisseau (pas seulement le trou noir interieur), pour
# que le cadre du module equipe vienne recouvrir celui du vaisseau. Nouvelle
# image (bras mecaniques vers 4 cadres, 2 en haut/2 en bas plutot que les 4
# coins d'une image large) : GAUCHE reste la paire du haut, DROITE celle du
# bas, meme convention que l'ancienne image (deja GAUCHE = y le plus haut).
_EMPLACEMENTS_MODULES_IMAGE = {
    Position(Colonne.ARRIERE, Rangee.GAUCHE): (230, 745, 250, 220),
    Position(Colonne.AVANT, Rangee.GAUCHE): (580, 745, 250, 220),
    Position(Colonne.ARRIERE, Rangee.DROITE): (230, 0, 250, 220),
    Position(Colonne.AVANT, Rangee.DROITE): (580, 0, 250, 220),
}

# Rangees de la flotte ennemie alignees verticalement sur celles du vaisseau
# joueur (decision utilisateur) : rangee du haut face aux modules du haut,
# rangee du bas face aux modules du bas, rangee du milieu face au vaisseau
# (entre les deux, au niveau du module principal). Centres derives des memes
# emplacements que _rect_module, pour rester coherents si l'image change encore.
_, _ey_gauche, _, _eh_gauche = _EMPLACEMENTS_MODULES_IMAGE[Position(Colonne.AVANT, Rangee.GAUCHE)]
_, _ey_droite, _, _eh_droite = _EMPLACEMENTS_MODULES_IMAGE[Position(Colonne.AVANT, Rangee.DROITE)]
_CENTRE_Y_RANGEE_GAUCHE = VAISSEAU_Y + (_ey_gauche + _eh_gauche / 2) * _ECHELLE_VAISSEAU
_CENTRE_Y_RANGEE_DROITE = VAISSEAU_Y + (_ey_droite + _eh_droite / 2) * _ECHELLE_VAISSEAU
_CENTRE_Y_RANGEE_MID = (_CENTRE_Y_RANGEE_GAUCHE + _CENTRE_Y_RANGEE_DROITE) / 2

RANGEE_Y = {
    Rangee.GAUCHE: _CENTRE_Y_RANGEE_GAUCHE - CELLULE_HAUTEUR / 2,
    Rangee.MID: _CENTRE_Y_RANGEE_MID - CELLULE_HAUTEUR / 2,
    Rangee.DROITE: _CENTRE_Y_RANGEE_DROITE - CELLULE_HAUTEUR / 2,
}

# Repere du pare-brise mesure sur l'image source (coordonnees locales,
# origine bas-gauche : centre horizontal, bord superieur), pour placer la
# pastille PV/Bouclier de la base juste au-dessus de lui.
_CENTRE_PARE_BRISE_IMAGE = 785
_HAUT_PARE_BRISE_IMAGE = 615
CENTRE_PARE_BRISE_VAISSEAU_X = VAISSEAU_X + _CENTRE_PARE_BRISE_IMAGE * _ECHELLE_VAISSEAU
HAUT_PARE_BRISE_VAISSEAU_Y = VAISSEAU_Y + _HAUT_PARE_BRISE_IMAGE * _ECHELLE_VAISSEAU

# Main de cartes, centree en bas de l'ecran (specs.md paragraphe 8.1), comme
# la version web (#main, justify-content:center) plutot qu'a une position fixe.
CARTE_LARGEUR, CARTE_HAUTEUR = 100, 140
CARTE_Y = 40
CARTE_ESPACEMENT = 120
HAUTEUR_BANDEAU_CARTE = 46

# Controles de combat (tour suivant / quitter la partie) : icones plutot qu'un bandeau+texte en
# haut d'ecran (decision utilisateur, remplace l'ancien bandeau Electricite/"Fin de tour" - la
# barre laterale, elle, revient donc a sa position par defaut, cf. Y_HAUT_PAR_DEFAUT dans
# src/ui/barre_laterale.py). Empiles sous cette barre (Niveau/Argent/Deck/Vaisseau) quand elle est
# affichee (self.partie non None), ou au sommet de la fenetre sinon (fenetre de test sans partie).
TAILLE_BOUTON_COMBAT = 60
_DECALAGE_ELECTRICITE_COMBAT = 20
# Decalage du haut de chaque bouton sous le sommet du bloc de controles, de haut en bas
_DECALAGES_BOUTONS_COMBAT = {
    "tour_suivant": _DECALAGE_ELECTRICITE_COMBAT + 20,
    "quitter": _DECALAGE_ELECTRICITE_COMBAT + 20 + (TAILLE_BOUTON_COMBAT + 14),
    "journal": _DECALAGE_ELECTRICITE_COMBAT + 20 + 2 * (TAILLE_BOUTON_COMBAT + 14),
}
_ICONES_BOUTONS_COMBAT = {
    "tour_suivant": str(RACINE / "assets" / "interface" / "tour_suivant.png"),
    "quitter": str(RACINE / "assets" / "interface" / "quitter.png"),
    "journal": str(RACINE / "assets" / "interface" / "journal.png"),
}
# Numero de tour et compteurs des piles, sous le bouton Journal
_DECALAGE_HAUT_COMPTEURS = _DECALAGES_BOUTONS_COMBAT["journal"] + TAILLE_BOUTON_COMBAT + 8

COULEUR_BANDEAU = (10, 10, 12)
OPACITE_BANDEAU = 190
COULEUR_CARTE_SURLIGNEE = (210, 180, 40)
COULEUR_SURVOL = (255, 255, 255)
OPACITE_DETRUIT = 70

# Image de fond (specs.md paragraphe 8), etiree pour remplir toute la
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

# Indicateur de rarete (etoile en haut a gauche de la carte) et pastille de munitions
# restantes (en haut a droite, meme style que les pastilles PV/Bouclier), cf. specs.md 8.2
COULEUR_ETOILE_RARETE = {
    RareteCarte.BASE: (245, 245, 245),
    RareteCarte.COMMUNE: (70, 190, 90),
    RareteCarte.RARE: (60, 130, 230),
    RareteCarte.LEGENDAIRE: (235, 150, 30),
}
COULEUR_PASTILLE_MUNITION = (70, 190, 90)
# Statuts (refonte-branchement.md 4.2/4.3) : une pastille par statut actif, a gauche du Bouclier
COULEUR_PASTILLE_STATUT = textes_combat.COULEUR_PAR_STATUT
COULEUR_PASTILLE_COUT = (40, 60, 110)
COULEUR_PASTILLE_LANCEMENTS = (150, 90, 200)
# Marqueur du module vise par une attaque au prochain tour ennemi (anneau rouge)
COULEUR_CIBLE = (235, 60, 60)
# Contour d'une case ou la carte selectionnee peut etre confirmee
COULEUR_CASE_VALIDE = (90, 220, 120)
OPACITE_CARTE_INJOUABLE = 110

# Popups +/-N affiches 2 secondes sur une cible touchee par une carte ou une
# attaque ennemie (degats en rouge, bouclier pose en bleu, soin en vert)
TAILLE_POLICE_POPUP = 22
COULEUR_POPUP_DEGATS = textes_combat.COULEUR_DEGATS
COULEUR_POPUP_BOUCLIER = textes_combat.COULEUR_BOUCLIER
COULEUR_POPUP_SOIN = textes_combat.COULEUR_SOIN
COULEUR_OMBRE_POPUP = (0, 0, 0)
DECALAGE_OMBRE_POPUP = 2
# Ecart vertical entre deux popups affiches en meme temps sur la meme case
DECALAGE_POPUPS_EMPILES = 30

# Infobulle au survol, affichee au-dessus du curseur
LARGEUR_INFOBULLE = 300
TAILLE_POLICE_INFOBULLE = 13
MARGE_INFOBULLE = 8
# Ecart vertical entre la pointe du curseur et le bas de l'infobulle
DECALAGE_INFOBULLE_CURSEUR = 16

# Groupe de rendu pour tout ce qui doit rester visible par-dessus les sprites
# (pastilles, bandeaux, textes, rayons...) : l'ordre entre sprites et formes
# n'est pas garanti par pyglet sans groupe explicite.
GROUPE_SUPERPOSITION = pyglet.graphics.Group(order=1)
# Infobulle au survol : au-dessus de tout (pastilles et textes compris), son texte au-dessus
# de son propre fond.
GROUPE_INFOBULLE = pyglet.graphics.Group(order=2)
GROUPE_INFOBULLE_TEXTE = pyglet.graphics.Group(order=3)
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


def _sprite_ajuste_largeur(
    chemin: str, x: float, y: float, largeur: float, hauteur: float, lot: pyglet.graphics.Batch
) -> pyglet.sprite.Sprite:
    """Cree un sprite pour cette image, mis a l'echelle pour remplir toute la largeur du
    rectangle (sans deformation), quitte a deborder en hauteur - centre verticalement. Utilise
    pour un ennemi a plusieurs emplacements (specs.md 3.2, ex. Boss des pirates) : sa case
    fusionnee est bien plus large que haute, et une image qui ne fait pas ce ratio parait trop
    petite avec `_sprite_ajuste` (qui cale sur la plus petite dimension)."""
    sprite = pyglet.sprite.Sprite(_image(chemin), batch=lot)
    sprite.scale = largeur / sprite.width
    sprite.x = x
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


def _infobulle_au_curseur(
    texte: str,
    curseur: tuple[float, float],
    lot: pyglet.graphics.Batch,
    largeur: float = LARGEUR_INFOBULLE,
    couleur_texte: tuple = COULEUR_SURVOL,
) -> list:
    """Infobulle (fond + texte) au-dessus du curseur, ou dessous faute de place, dans la fenetre."""
    label = pyglet.text.Label(
        texte,
        anchor_x="center",
        anchor_y="bottom",
        multiline=True,
        width=largeur - 2 * MARGE_INFOBULLE,
        align="center",
        font_size=TAILLE_POLICE_INFOBULLE,
        color=(*couleur_texte, 255),
        batch=lot,
        group=GROUPE_INFOBULLE_TEXTE,
    )
    # Hauteur mesuree apres mise en page : une ligne longue peut passer sur deux lignes
    hauteur = label.content_height + 2 * MARGE_INFOBULLE
    curseur_x, curseur_y = curseur
    bx = min(max(curseur_x - largeur / 2, 0), LARGEUR_FENETRE - largeur)
    by = curseur_y + DECALAGE_INFOBULLE_CURSEUR
    if by + hauteur > HAUTEUR_FENETRE:
        # Pas la place au-dessus (haut de l'ecran) : sous le curseur
        by = curseur_y - DECALAGE_INFOBULLE_CURSEUR - hauteur
    label.x = bx + largeur / 2
    label.y = by + MARGE_INFOBULLE
    fond = shapes.Rectangle(bx, by, largeur, hauteur, color=COULEUR_BANDEAU, batch=lot, group=GROUPE_INFOBULLE)
    fond.opacity = OPACITE_BANDEAU
    return [fond, label]


def _pastille(x_centre: float, y_centre: float, couleur: tuple, valeur: int | str, lot: pyglet.graphics.Batch) -> list:
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


def _rect_fusionne(positions: list[Position]) -> tuple[float, float, float, float]:
    """Rectangle englobant plusieurs cases ennemies (specs.md 3.2 : un ennemi a plusieurs
    emplacements, ex. le Boss des pirates sur l'Avant et l'Arriere d'une meme rangee, est
    dessine comme un seul rectangle fusionne plutot que deux sprites/pastilles PV redondants) -
    union des rectangles individuels de chaque case."""
    rects = [_rect_ennemi(position) for position in positions]
    x0 = min(x for x, _y, _l, _h in rects)
    y0 = min(y for _x, y, _l, _h in rects)
    x1 = max(x + largeur for x, _y, largeur, _h in rects)
    y1 = max(y + hauteur for _x, y, _l, hauteur in rects)
    return x0, y0, x1 - x0, y1 - y0



def texte_effet_carte(carte: CarteNew) -> str:
    """Texte d'une carte, partout (combat, recompenses, deck, Aventures) : la description de
    config/carte_new.json avec ses valeurs actuelles, fournie par le gameplay."""
    return carte.description_affichee()


def _pastilles_statuts(entite: ModuleNew | EnnemiNew, cx_pv: float, cy: float, lot: pyglet.graphics.Batch) -> list:
    """Pastilles des statuts actifs autres que le Bouclier (Incendie, Renvoi, Leurre), a gauche
    de la pastille Bouclier, avec leur intensite (rien pour le Leurre : present ou absent)."""
    elements = []
    pas = RAYON_PASTILLE * 2 + MARGE_PASTILLE
    cx = cx_pv - 2 * pas
    for statut in textes_combat.STATUTS_EN_PASTILLE:
        intensite = entite.statuts[statut]
        if intensite <= 0:
            continue
        valeur = "L" if statut == Statut.LEURRE else intensite
        elements += _pastille(cx, cy, COULEUR_PASTILLE_STATUT[statut], valeur, lot)
        cx -= pas
    return elements


def _marqueur_cible(cx: float, cy: float, lot: pyglet.graphics.Batch) -> list:
    """Anneau rouge sur un module vise par une attaque au prochain tour ennemi."""
    fond = shapes.Circle(cx, cy, _RAYON_TOTAL_PASTILLE, color=(0, 0, 0), batch=lot, group=GROUPE_SUPERPOSITION)
    anneau = shapes.Arc(cx, cy, RAYON_PASTILLE - 2, color=COULEUR_CIBLE, thickness=3, batch=lot, group=GROUPE_SUPERPOSITION)
    point = shapes.Circle(cx, cy, 4, color=COULEUR_CIBLE, batch=lot, group=GROUPE_SUPERPOSITION)
    return [fond, anneau, point]


class FenetreCombat(pyglet.window.Window):
    """Fenetre de combat : affiche un CombatNew et gere les clics/survols de souris."""

    def __init__(self, combat: CombatNew, partie: Partie | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.combat = combat
        # None seulement pour une fenetre de test sans partie : pas de barre laterale
        self.partie = partie
        self.index_carte_selectionnee: int | None = None
        self.entite_survolee: ModuleNew | EnnemiNew | None = None
        self.index_carte_survolee: int | None = None
        # Derniere position connue de la souris, pour placer l'infobulle au-dessus du curseur
        self.position_souris: tuple[int, int] = (0, 0)
        self.survole_barre: str | None = None
        # True apres un clic sur "Quitter" (specs.md 8.1) : signale a main.py qu'il doit fermer
        # cette fenetre et revenir a l'ecran de selection du joueur, sans toucher a la partie
        # sauvegardee (le combat en cours n'est jamais sauvegarde)
        self.quitte_demandee: bool = False
        self.popups: list[tuple[AnimationPopup, str, tuple[int, int, int], float, float]] = []
        # Taille du journal deja affichee en popups : ceux d'une action viennent des seules
        # entrees ajoutees depuis (meme principe que src/web/bridge.py:_resultat_combat)
        self._taille_journal_vue = len(combat.journal)
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)

    def update(self, dt: float) -> None:
        """Fait avancer les animations en cours (appele a chaque frame)."""
        for animation, _texte, _couleur, _x, _y in self.popups:
            animation.mettre_a_jour(dt)
        self.popups = [popup for popup in self.popups if popup[0].est_active()]

    # --- Lecture du combat ---

    def _main(self) -> list[CarteNew]:
        return self.combat.deck.main

    def _carte_selectionnee(self) -> CarteNew | None:
        main = self._main()
        if self.index_carte_selectionnee is None or self.index_carte_selectionnee >= len(main):
            return None
        return main[self.index_carte_selectionnee]

    def _nom_module_de(self, carte: CarteNew) -> str | None:
        module = self.combat.vaisseau.module_d_exemplaire(carte.exemplaire_module)
        return module.nom if module else None

    def _cases_de(self, entite: ModuleNew | EnnemiNew) -> list[Position]:
        if isinstance(entite, ModuleNew):
            return list(CASES_PAR_EMPLACEMENT[entite.emplacement])
        return self.combat.flotte.cases_de(entite)

    def _entites_valides(self) -> list[ModuleNew | EnnemiNew]:
        """Entites sur lesquelles la carte selectionnee peut etre confirmee (cases decidees par
        le gameplay : CombatNew.cibles_possibles, seulement si la carte est jouable)."""
        carte = self._carte_selectionnee()
        if carte is None or not self.combat.peut_jouer(carte):
            return []
        valides = self.combat.cibles_possibles(carte)
        if carte.cible.camp == Camp.JOUEUR:
            candidats = self.combat.vaisseau.modules_vivants()
        else:
            candidats = self.combat.flotte.ennemis_vivants()
        return [entite for entite in candidats if any(case in valides for case in self._cases_de(entite))]

    # --- Dessin ---

    def on_draw(self) -> None:
        """Redessine entierement la fenetre a chaque frame."""
        self.clear()
        lot = pyglet.graphics.Batch()
        # references gardees le temps du dessin, pyglet ne garde pas de reference forte tout seul
        elements = []

        # Import differe : barre_laterale importe de ce module (HAUTEUR_FENETRE, _sprite_ajuste),
        # un import en tete de fichier creerait un cycle.
        from src.ui import barre_laterale

        elements.extend(self._dessiner_fond(lot))
        elements.extend(self._dessiner_vaisseau(lot))
        elements.extend(self._dessiner_flotte(lot))
        elements.extend(self._dessiner_cases_valides(lot))
        elements.extend(self._dessiner_popups(lot))
        elements.extend(self._dessiner_main(lot))
        elements.extend(self._dessiner_survol(lot))
        if self.partie is not None:
            elements.extend(barre_laterale.dessiner(self.partie, self.survole_barre, lot))

        elements.extend(self._dessiner_controles_combat(lot, barre_laterale))

        if not self.combat.en_cours:
            elements.extend(self._dessiner_message_fin(lot))

        lot.draw()

    def _dessiner_fond(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine l'image de fond, etiree pour remplir toute la fenetre (deformation
        acceptee), comme l'arriere-plan de la version web (body en fond.PNG)."""
        return [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot, groupe=GROUPE_FOND)]

    def _dessiner_vaisseau(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine le grand sprite du vaisseau (principal) et les modules equipes dans leurs emplacements."""
        elements = []
        menaces = textes_combat.menaces_par_module(self.combat)
        principal = self.combat.vaisseau.principal
        vx, vy, vl, vh = _rect_vaisseau()
        detruit = principal.est_detruit()
        sprite = _sprite_ajuste(chemin_image(principal.image), vx, vy, vl, vh, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
        elements.append(sprite)
        if detruit:
            elements.extend(self._texte_detruit(vx, vy, vl, vh, lot))
        else:
            elements.extend(
                _pastilles_pv_bouclier(
                    vx, vy, vl, vh, principal.pv_combat, principal.statuts[Statut.BOUCLIER], lot,
                    centre_x=CENTRE_PARE_BRISE_VAISSEAU_X, haut=HAUT_PARE_BRISE_VAISSEAU_Y,
                )
            )
            cy = HAUT_PARE_BRISE_VAISSEAU_Y + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
            elements.extend(_pastilles_statuts(principal, CENTRE_PARE_BRISE_VAISSEAU_X, cy, lot))
            if id(principal) in menaces:
                pas = RAYON_PASTILLE * 2 + MARGE_PASTILLE
                elements.extend(_marqueur_cible(CENTRE_PARE_BRISE_VAISSEAU_X + pas, cy, lot))

        for module in self.combat.vaisseau.modules:
            if not module.principal:
                elements.extend(self._dessiner_module_case(lot, module, id(module) in menaces))
        return elements

    def _dessiner_module_case(self, lot: pyglet.graphics.Batch, module: ModuleNew, vise: bool) -> list:
        """Dessine une case module (image + pastilles PV/Bouclier/statuts, marqueur s'il est vise
        au prochain tour ennemi), grisee si detruite (avec le nombre de ses cartes hors service)."""
        x, y, largeur, hauteur = self._rect_du_module(module)
        sprite = _sprite_etire(chemin_image(module.image), x, y, largeur, hauteur, lot)
        if module.est_detruit():
            sprite.opacity = OPACITE_DETRUIT
            hors_service = self._cartes_hors_service(module)
            suffixe = f" · {hors_service} HS" if hors_service else ""
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot, suffixe)]
        bouclier = module.statuts[Statut.BOUCLIER]
        elements = [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, module.pv_combat, bouclier, lot)]
        cx_pv = x + largeur - RAYON_PASTILLE - MARGE_PASTILLE
        cy = y + hauteur + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
        elements.extend(_pastilles_statuts(module, cx_pv, cy, lot))
        if vise:
            elements.extend(_marqueur_cible(x + _RAYON_TOTAL_PASTILLE, cy, lot))
        return elements

    def _cartes_hors_service(self, module: ModuleNew) -> int:
        return sum(carte.exemplaire_module == module.exemplaire for carte in self.combat.deck.hors_service)

    def _dessiner_flotte(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque ennemi de la flotte, detruits compris (grises), une seule fois meme
        s'il occupe deux cases (le Boss des pirates)."""
        elements = []
        intentions = {id(intention.ennemi): intention for intention in self.combat.intentions()}
        for ennemi in self.combat.flotte.ennemis:
            rect = _rect_fusionne(self.combat.flotte.cases_de(ennemi))
            elements.extend(self._dessiner_ennemi_case(lot, rect, ennemi, intentions.get(id(ennemi))))
        return elements

    def _dessiner_ennemi_case(self, lot, rect: tuple[float, float, float, float], ennemi: EnnemiNew, intention) -> list:
        """Dessine une case ennemie : image, pastilles PV/Bouclier/statuts, et son intention pour
        le prochain tour en bas de la case (refonte-branchement.md 4.3) ; grisee si detruite."""
        x, y, largeur, hauteur = rect
        # Un ennemi sur deux cases a une case bien plus large que haute : remplir la largeur
        if ennemi.emplacements > 1:
            sprite = _sprite_ajuste_largeur(chemin_image(ennemi.image), x, y, largeur, hauteur, lot)
        else:
            sprite = _sprite_ajuste(chemin_image(ennemi.image), x, y, largeur, hauteur, lot)
        if ennemi.est_detruit():
            sprite.opacity = OPACITE_DETRUIT
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot)]
        bouclier = ennemi.statuts[Statut.BOUCLIER]
        elements = [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, ennemi.pv, bouclier, lot)]
        cx_pv = x + largeur - RAYON_PASTILLE - MARGE_PASTILLE
        cy = y + hauteur + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
        elements.extend(_pastilles_statuts(ennemi, cx_pv, cy, lot))
        if intention is not None and self.combat.en_cours:
            elements.extend(self._dessiner_intention(lot, rect, intention))
        return elements

    def _dessiner_intention(self, lot, rect: tuple[float, float, float, float], intention) -> list:
        """Bandeau en bas de la case de l'ennemi : ses actions du prochain tour, en version
        courte (symbole, valeur, repetitions), chacune dans la couleur de sa nature."""
        x, y, largeur, _hauteur = rect
        elements = [_bandeau(x, y, largeur, HAUTEUR_BANDEAU_INTENTION, lot)]
        labels = [
            pyglet.text.Label(
                textes_combat.texte_intention_court(effet),
                y=y + HAUTEUR_BANDEAU_INTENTION / 2, anchor_x="left", anchor_y="center", font_size=11,
                color=(*textes_combat.COULEUR_PAR_NATURE_ENNEMI.get(effet.effet.nature, COULEUR_SURVOL), 255),
                batch=lot, group=GROUPE_INFOBULLE,
            )
            for effet in intention.effets
        ]
        ecart = 8
        total = sum(label.content_width for label in labels) + ecart * (len(labels) - 1)
        cx = x + (largeur - total) / 2
        for label in labels:
            label.x = cx
            cx += label.content_width + ecart
        return elements + labels

    def _dessiner_cases_valides(self, lot: pyglet.graphics.Batch) -> list:
        """Contour vert autour des cases ou la carte selectionnee peut etre confirmee."""
        elements = []
        for entite in self._entites_valides():
            x, y, largeur, hauteur = self._rect_de_cible(entite)
            if isinstance(entite, ModuleNew) and entite.principal:
                # Le principal : contour autour de sa pastille de PV plutot que de tout le vaisseau
                cy = HAUT_PARE_BRISE_VAISSEAU_Y + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
                elements.append(
                    shapes.Arc(
                        CENTRE_PARE_BRISE_VAISSEAU_X, cy, _RAYON_TOTAL_PASTILLE + 4, color=COULEUR_CASE_VALIDE,
                        thickness=3, batch=lot, group=GROUPE_SUPERPOSITION,
                    )
                )
                continue
            elements.append(
                shapes.Box(x - 2, y - 2, largeur + 4, hauteur + 4, thickness=3, color=COULEUR_CASE_VALIDE, batch=lot, group=GROUPE_SUPERPOSITION)
            )
        return elements

    def _texte_detruit(self, x: float, y: float, largeur: float, hauteur: float, lot, suffixe: str = "") -> list:
        """Bandeau + texte "Detruit" centre sur une case."""
        hauteur_bandeau = min(HAUTEUR_BANDEAU_CASE, hauteur)
        bandeau = _bandeau(x, y + hauteur / 2 - hauteur_bandeau / 2, largeur, hauteur_bandeau, lot)
        texte = pyglet.text.Label(
            f"Détruit{suffixe}",
            x=x + largeur / 2, y=y + hauteur / 2, anchor_x="center", anchor_y="center",
            font_size=9, batch=lot, group=GROUPE_INFOBULLE,
        )
        return [bandeau, texte]

    def _dessiner_popups(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque popup encore actif sur sa cible (une ombre noire derriere le texte
        colore, pour rester lisible par-dessus n'importe quelle image)."""
        elements = []
        for _animation, texte, couleur, x, y in self.popups:
            # Ombre dans un groupe sous celui du texte : leur ordre n'est pas garanti sinon
            for dx, dy, teinte, groupe in (
                (DECALAGE_OMBRE_POPUP, -DECALAGE_OMBRE_POPUP, COULEUR_OMBRE_POPUP, GROUPE_INFOBULLE),
                (0, 0, couleur, GROUPE_INFOBULLE_TEXTE),
            ):
                elements.append(
                    pyglet.text.Label(
                        texte, x=x + dx, y=y + dy, anchor_x="center", anchor_y="center",
                        font_size=TAILLE_POLICE_POPUP, color=(*teinte, 255), batch=lot, group=groupe,
                    )
                )
        return elements

    def _x_carte_depart(self) -> float:
        """X du bord gauche de la premiere carte, pour que la rangee soit centree
        horizontalement dans la fenetre, comme #main (justify-content:center) sur le web."""
        main = self._main()
        if not main:
            return LARGEUR_FENETRE / 2
        largeur_rangee = (len(main) - 1) * CARTE_ESPACEMENT + CARTE_LARGEUR
        return (LARGEUR_FENETRE - largeur_rangee) / 2

    def _dessiner_main(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine les cartes de la main (refonte-branchement.md 4.1) : illustration, rarete,
        cout, munitions, "x2" si elle est lancee plus d'une fois, bandeau Persistante ; assombrie
        si elle n'est pas jouable maintenant (decide par le gameplay : CombatNew.peut_jouer)."""
        elements = []
        x_depart = self._x_carte_depart()
        for index, carte in enumerate(self._main()):
            x = x_depart + index * CARTE_ESPACEMENT
            if index == self.index_carte_selectionnee:
                # Cadre creux autour de la carte (pas un rectangle plein dessous) : l'ordre de
                # dessin forme/sprite n'etant pas garanti, un rectangle plein pouvait masquer l'image.
                elements.append(
                    shapes.Box(
                        x - 4, CARTE_Y - 4, CARTE_LARGEUR + 8, CARTE_HAUTEUR + 8,
                        thickness=4, color=COULEUR_CARTE_SURLIGNEE, batch=lot,
                    )
                )
            sprite = _sprite_ajuste(chemin_image(carte.image), x, CARTE_Y, CARTE_LARGEUR, CARTE_HAUTEUR, lot)
            if not self.combat.peut_jouer(carte):
                sprite.opacity = OPACITE_CARTE_INJOUABLE
            elements.append(sprite)
            elements.append(_bandeau(x, CARTE_Y, CARTE_LARGEUR, HAUTEUR_BANDEAU_CARTE, lot))
            elements.extend(self._dessiner_etoile_rarete(x, carte, lot))
            elements.extend(self._dessiner_pastilles_carte(x, carte, lot))
            if carte.persistante:
                y_bandeau = CARTE_Y + HAUTEUR_BANDEAU_CARTE
                elements.append(_bandeau(x, y_bandeau, CARTE_LARGEUR, 14, lot))
                elements.append(
                    pyglet.text.Label(
                        "PERSISTANTE", x=x + CARTE_LARGEUR / 2, y=y_bandeau + 7, anchor_x="center", anchor_y="center",
                        font_size=7, color=(*COULEUR_CARTE_SURLIGNEE, 255), batch=lot, group=GROUPE_INFOBULLE,
                    )
                )
            elements.append(
                pyglet.text.Label(
                    carte.nom,
                    x=x + CARTE_LARGEUR / 2, y=CARTE_Y + HAUTEUR_BANDEAU_CARTE / 2,
                    anchor_x="center", anchor_y="center", font_size=9, multiline=True,
                    width=CARTE_LARGEUR - 4, align="center", batch=lot, group=GROUPE_INFOBULLE,
                )
            )
        return elements

    def _dessiner_pastilles_carte(self, x: float, carte: CarteNew, lot: pyglet.graphics.Batch) -> list:
        """En haut a droite de la carte, de haut en bas : cout, munitions restantes/de depart
        (si limitees), nombre de lancements (si > 1)."""
        cx = x + CARTE_LARGEUR - _RAYON_TOTAL_PASTILLE
        cy = CARTE_Y + CARTE_HAUTEUR - _RAYON_TOTAL_PASTILLE
        pas = 2 * _RAYON_TOTAL_PASTILLE + 2
        elements = _pastille(cx, cy, COULEUR_PASTILLE_COUT, f"⚡{carte.cout}", lot)
        munitions = textes_combat.texte_munitions(carte)
        if munitions:
            cy -= pas
            elements += _pastille(cx, cy, COULEUR_PASTILLE_MUNITION, munitions, lot)
        if textes_combat.lancements(carte) > 1:
            cy -= pas
            elements += _pastille(cx, cy, COULEUR_PASTILLE_LANCEMENTS, f"×{textes_combat.lancements(carte)}", lot)
        return elements

    def _dessiner_etoile_rarete(self, x: float, carte: CarteNew, lot: pyglet.graphics.Batch) -> list:
        """Etoile de rarete en haut a gauche de la carte (specs.md paragraphe 8.2)."""
        couleur = COULEUR_ETOILE_RARETE[carte.rarete]
        return [
            pyglet.text.Label(
                "★", x=x + 10 + decalage, y=CARTE_Y + CARTE_HAUTEUR - 10 + decalage, anchor_x="center",
                anchor_y="center", font_size=16, color=(*teinte, 255), batch=lot, group=GROUPE_SUPERPOSITION,
            )
            for decalage, teinte in ((1, (0, 0, 0)), (0, couleur))
        ]

    def _y_haut_controles_combat(self, barre_laterale) -> float:
        """Sommet du bloc controles de combat (Electricite/tour suivant/Quitter) : sous la barre
        laterale si affichee (self.partie non None), sinon au sommet de la fenetre."""
        if self.partie is None:
            return barre_laterale.Y_HAUT_PAR_DEFAUT
        return barre_laterale.Y_HAUT_PAR_DEFAUT - barre_laterale.HAUTEUR_CONTENU - 30

    def _rect_bouton_combat(self, barre_laterale, decalage_haut: float) -> tuple[float, float, float, float]:
        x = (barre_laterale.LARGEUR_BARRE - TAILLE_BOUTON_COMBAT) / 2
        y = self._y_haut_controles_combat(barre_laterale) - decalage_haut
        return x, y - TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT

    def _bouton_combat_a(self, x: int, y: int, barre_laterale) -> str | None:
        """Identifiant ("tour_suivant"/"quitter"/"journal") du bouton de controle de combat sous
        ce point, None si aucun."""
        for identifiant, decalage in _DECALAGES_BOUTONS_COMBAT.items():
            if _point_dans_rectangle(x, y, *self._rect_bouton_combat(barre_laterale, decalage)):
                return identifiant
        return None

    def _dessiner_controles_combat(self, lot: pyglet.graphics.Batch, barre_laterale) -> list:
        """Electricite disponible, boutons icones tour suivant/Quitter/Journal (specs.md 8.1),
        puis numero de tour et compteurs des piles (refonte-branchement.md 4.4)."""
        y_haut = self._y_haut_controles_combat(barre_laterale)
        x_centre = barre_laterale.LARGEUR_BARRE / 2
        elements = [
            pyglet.text.Label(
                f"⚡ {self.combat.electricite}/{ELECTRICITE_PAR_TOUR}",
                x=x_centre, y=y_haut - _DECALAGE_ELECTRICITE_COMBAT, anchor_x="center", anchor_y="center",
                font_size=14, batch=lot, group=GROUPE_SUPERPOSITION,
            )
        ]
        for identifiant, decalage in _DECALAGES_BOUTONS_COMBAT.items():
            rect = self._rect_bouton_combat(barre_laterale, decalage)
            elements.append(_sprite_ajuste(_ICONES_BOUTONS_COMBAT[identifiant], *rect, lot))
        elements.append(
            pyglet.text.Label(
                textes_combat.texte_compteurs(self.combat),
                x=x_centre, y=y_haut - _DECALAGE_HAUT_COMPTEURS, anchor_x="center", anchor_y="top",
                multiline=True, width=barre_laterale.LARGEUR_BARRE, align="center",
                font_size=9, batch=lot, group=GROUPE_SUPERPOSITION,
            )
        )
        return elements

    def _dessiner_survol(self, lot: pyglet.graphics.Batch) -> list:
        """Infobulle au survol. Carte en main : nom, description avec ses valeurs actuelles,
        details (munitions, lancements, Persistante, module). Module : nom, PV, statuts, cartes
        hors service s'il est detruit, attaques qui le visent au prochain tour. Ennemi : nom, PV,
        statuts, puis les actions de son prochain tour, une par ligne, sans titre ni cycle
        (decision utilisateur, 2026-11-13, refonte-branchement.md 4.3)."""
        if not self.combat.en_cours:
            return []
        main = self._main()
        if self.index_carte_survolee is not None and self.index_carte_survolee < len(main):
            carte = main[self.index_carte_survolee]
            lignes = [carte.nom, texte_effet_carte(carte), f"⚡ {carte.cout}"]
            lignes.extend(textes_combat.lignes_details_carte(carte, self._nom_module_de(carte)))
            if not self.combat.peut_jouer(carte):
                lignes.append("Pas jouable maintenant")
            return _infobulle_au_curseur("\n".join(lignes), self.position_souris, lot)

        entite = self.entite_survolee
        if entite is None:
            return []
        if isinstance(entite, EnnemiNew):
            if entite.est_detruit():
                return []
            lignes = [entite.nom, f"PV {entite.pv}/{entite.pv_max}", *textes_combat.lignes_statuts(entite)]
            for intention in self.combat.intentions():
                if intention.ennemi is entite:
                    lignes.extend(textes_combat.texte_intention(effet) for effet in intention.effets)
        else:
            lignes = [entite.nom, f"PV {max(entite.pv_combat, 0)}/{entite.pv_max}", *textes_combat.lignes_statuts(entite)]
            if entite.est_detruit():
                hors_service = self._cartes_hors_service(entite)
                if hors_service:
                    lignes.append(f"{hors_service} carte(s) hors service")
            menaces = textes_combat.menaces_par_module(self.combat).get(id(entite), [])
            if menaces:
                lignes.append("Visé au prochain tour par :")
                lignes.extend(menaces)
        return _infobulle_au_curseur("\n".join(lignes), self.position_souris, lot)

    def _dessiner_message_fin(self, lot: pyglet.graphics.Batch) -> list:
        """Affiche le message de fin de combat (victoire ou defaite)."""
        message = "Victoire !" if self.combat.etat == EtatCombatNew.VICTOIRE else "Défaite"
        texte = pyglet.text.Label(
            message, x=LARGEUR_FENETRE / 2, y=HAUTEUR_FENETRE / 2, anchor_x="center", anchor_y="center",
            font_size=36, batch=lot, group=GROUPE_INFOBULLE,
        )
        return [texte]

    # --- Souris ---

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Gere les clics de souris : selection de carte, ciblage, tour suivant, quitter."""
        # Imports differes, cf. on_draw : cycle avec ce module sinon.
        from src.ui import barre_laterale

        bouton_combat = self._bouton_combat_a(x, y, barre_laterale)
        if bouton_combat == "quitter":
            self.quitte_demandee = True
            return
        if bouton_combat == "tour_suivant" and self.combat.en_cours:
            self.combat.finir_tour()
            self._afficher_popups_du_journal()
            self.index_carte_selectionnee = None
            return
        if bouton_combat == "journal":
            from src.ui.ecran_journal import EcranJournal

            barre_laterale.ouvrir_survol(EcranJournal(list(self.combat.journal)))
            return

        if self.partie is not None:
            from src.ui.ecran_deck import EcranDeck
            from src.ui.ecran_vaisseau import EcranVaisseau

            bouton_barre = barre_laterale.bouton_survole(x, y)
            if bouton_barre == "deck":
                # Toutes les cartes du combat en cours, toutes piles confondues (comme le web)
                noms = {module.exemplaire: module.nom for module in self.combat.vaisseau.modules}
                barre_laterale.ouvrir_survol(EcranDeck(self.combat.deck.toutes_les_cartes(), noms))
                return
            if bouton_barre == "vaisseau":
                barre_laterale.ouvrir_survol(EcranVaisseau(self.partie))
                return

        if not self.combat.en_cours:
            return

        index_carte_cliquee = self._trouver_carte_cliquee(x, y)
        if index_carte_cliquee is not None:
            # Un clic sur une carte l'arme (ou la desarme si deja selectionnee) sans la
            # jouer, meme pour les cartes sans clic de ciblage (specs.md 8.3) : un second
            # clic de confirmation sur une case valide reste necessaire, comme sur le web.
            deja_selectionnee = self.index_carte_selectionnee == index_carte_cliquee
            self.index_carte_selectionnee = None if deja_selectionnee else index_carte_cliquee
            return

        if self.index_carte_selectionnee is not None:
            self._essayer_de_cibler(x, y)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Met a jour la carte, le module ou l'ennemi survole par la souris, pour l'infobulle."""
        self.position_souris = (x, y)
        self.index_carte_survolee = self._trouver_carte_cliquee(x, y)
        self.entite_survolee = self._ennemi_a(x, y) or self._module_a(x, y, vivant=False)
        if self.partie is not None:
            from src.ui import barre_laterale

            self.survole_barre = barre_laterale.bouton_survole(x, y)

    def _trouver_carte_cliquee(self, x: int, y: int) -> int | None:
        """Renvoie l'index de la carte de la main sous ce point, ou None si aucune."""
        x_depart = self._x_carte_depart()
        for index in range(len(self._main())):
            carte_x = x_depart + index * CARTE_ESPACEMENT
            if _point_dans_rectangle(x, y, carte_x, CARTE_Y, CARTE_LARGEUR, CARTE_HAUTEUR):
                return index
        return None

    def _essayer_de_cibler(self, x: int, y: int) -> None:
        """Confirme la carte selectionnee sur la case cliquee, si c'est une de ses cases valides :
        ces cases sont decidees par le gameplay (CombatNew.cibles_possibles), jamais ici. Meme
        flux que cliquerCase dans src/web/app.js (specs.md 8.3) : une case du bon camp, vivante, et
        valide pour la carte ; sinon le clic est ignore et la carte reste selectionnee. Une
        entite sur deux cases (principal, Boss) : on prend celle de ses cases que le gameplay
        accepte (ex. Ligne arriere sur le Boss = sa case Arriere)."""
        carte = self._carte_selectionnee()
        if carte is None:
            self.index_carte_selectionnee = None
            return
        if not self.combat.peut_jouer(carte):
            return
        entite = self._module_a(x, y) if carte.cible.camp == Camp.JOUEUR else self._ennemi_a(x, y)
        if entite is None:
            return
        valides = self.combat.cibles_possibles(carte)
        case = next((case for case in self._cases_de(entite) if case in valides), None)
        if case is None:
            return
        self.combat.jouer_carte(carte, case)
        self._afficher_popups_du_journal()
        self.index_carte_selectionnee = None

    def _module_a(self, x: int, y: int, vivant: bool = True) -> ModuleNew | None:
        """Renvoie le module du joueur sous ce point (vivant seulement, sauf vivant=False pour
        l'infobulle d'un module detruit), ou None.

        Les emplacements de modules equipes sont testes en premier (ils sont inclus dans le
        rectangle du vaisseau) ; sinon un clic sur le reste du vaisseau vise le principal.
        """
        vaisseau = self.combat.vaisseau
        for module in vaisseau.modules:
            if module.principal:
                continue
            if _point_dans_rectangle(x, y, *self._rect_du_module(module)) and not (vivant and module.est_detruit()):
                return module
        if _point_dans_rectangle(x, y, *_rect_vaisseau()) and not (vivant and vaisseau.principal.est_detruit()):
            return vaisseau.principal
        return None

    def _ennemi_a(self, x: int, y: int) -> EnnemiNew | None:
        """Renvoie l'ennemi vivant sous ce point, ou None."""
        for ennemi in self.combat.flotte.ennemis_vivants():
            if _point_dans_rectangle(x, y, *_rect_fusionne(self.combat.flotte.cases_de(ennemi))):
                return ennemi
        return None

    # --- Popups ---

    def _afficher_popups_du_journal(self) -> None:
        """Popups des entrees du journal ajoutees par la derniere action (carte jouee ou tour
        ennemi) : degats, bouclier, soin, statut pose... (refonte-branchement.md 4.6). Plusieurs
        popups sur la meme case sont empiles vers le haut pour rester lisibles."""
        nouvelles = self.combat.journal[self._taille_journal_vue:]
        self._taille_journal_vue = len(self.combat.journal)
        rang_par_case: dict[int, int] = {}
        for evenement in nouvelles:
            popup = textes_combat.popup_evenement(evenement)
            if popup is None:
                continue
            texte, couleur = popup
            x, y, largeur, hauteur = self._rect_de_cible(evenement.cible)
            rang = rang_par_case.get(id(evenement.cible), 0)
            rang_par_case[id(evenement.cible)] = rang + 1
            animation = AnimationPopup()
            animation.demarrer()
            self.popups.append((animation, texte, couleur, x + largeur / 2, y + hauteur / 2 + rang * DECALAGE_POPUPS_EMPILES))

    def _rect_de_cible(self, cible: ModuleNew | EnnemiNew) -> tuple[float, float, float, float]:
        """Rectangle (x, y, largeur, hauteur) de la case d'un module ou d'un ennemi (fusion de
        ses cases pour un ennemi sur deux cases)."""
        if isinstance(cible, EnnemiNew):
            return _rect_fusionne(self.combat.flotte.cases_de(cible))
        return self._rect_du_module(cible)

    def _rect_du_module(self, module: ModuleNew) -> tuple[float, float, float, float]:
        """Rectangle d'un module du joueur (son emplacement, ou tout le vaisseau pour le principal)."""
        if module.principal:
            return _rect_vaisseau()
        return _rect_module(CASES_PAR_EMPLACEMENT[module.emplacement][0])
