"""
Fenetre pyglet du combat (grille 2x3, plusieurs modules et ennemis,
cf. specs.md paragraphe 8). Utilise les images de assets/.
"""

import pyglet
from pyglet import shapes

from src.gameplay.carte import CIBLES_SANS_CLIC, ActionCarte, Carte, CibleCarte, RareteCarte, TypeCarte
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.config_poc import creer_combat_poc
from src.gameplay.donnees import RACINE
from src.gameplay.ennemi import CibleActionEnnemi, Ennemi, TypeActionEnnemi
from src.gameplay.module import BuffActif, Module
from src.gameplay.partie import Partie, deck_de_la_partie
from src.gameplay.position import Colonne, Position, Rangee
from src.ui import journal_combat
from src.ui.animation import AnimationPopup

LARGEUR_FENETRE = 1280
HAUTEUR_FENETRE = 800

# Cibles de camp allie parmi celles de CIBLES_SANS_CLIC (specs.md 7.2/8.3) : determine
# quel camp (allie/ennemi) doit etre touche par le clic de confirmation d'une carte sans
# clic de ciblage precis, meme principe que CIBLES_ALLIEES dans web/app.js.
CIBLES_CAMP_ALLIE = (CibleCarte.ALLIE_UNIQUE, CibleCarte.ALLIES_MULTIPLES, CibleCarte.MODULE_PRINCIPAL)

# Cases de la flotte ennemie, cf. specs.md paragraphe 8.1. Agrandies (etaient 110x90, decision
# utilisateur : paraissaient petites a cote des modules, y compris apres un premier passage a
# 120x98 - encore trop timide) : alignees sur le meme empreinte que les modules du vaisseau
# (250x220 mis a l'echelle, cf. _EMPLACEMENTS_MODULES_IMAGE plus bas, ~135x119) plutot qu'une
# taille independante.
CELLULE_LARGEUR, CELLULE_HAUTEUR = 135, 119
ESPACEMENT_CELLULE = 17
HAUTEUR_BANDEAU_CASE = 42

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
# affichee (self.partie non None), ou au sommet de la fenetre sinon (mode demo POC sans partie
# reelle - "Quitter" se contente alors de fermer la fenetre, faute d'ecran de selection de joueur
# a rouvrir, cf. on_mouse_press).
_ICONE_TOUR_SUIVANT = str(RACINE / "assets" / "interface" / "tour_suivant.png")
_ICONE_QUITTER = str(RACINE / "assets" / "interface" / "quitter.png")
_ICONE_JOURNAL = str(RACINE / "assets" / "interface" / "journal.png")
TAILLE_BOUTON_COMBAT = 60
_DECALAGE_ELECTRICITE_COMBAT = 20
_DECALAGE_HAUT_TOUR_SUIVANT = _DECALAGE_ELECTRICITE_COMBAT + 20
_DECALAGE_HAUT_QUITTER = _DECALAGE_HAUT_TOUR_SUIVANT + TAILLE_BOUTON_COMBAT + 14
_DECALAGE_HAUT_JOURNAL = _DECALAGE_HAUT_QUITTER + TAILLE_BOUTON_COMBAT + 14

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
# Leurre actif (specs.md 12.6) : pas un buff (pas de redeclenchement periodique, se consomme
# a la prochaine attaque recue plutot qu'a l'expiration d'une duree) - pastille dediee.
COULEUR_PASTILLE_LEURRE = (90, 200, 210)

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


def _pastilles_buffs_module(module: Module, cx_pv: float, cy: float, lot: pyglet.graphics.Batch) -> list:
    """Pastilles du nombre de buffs actifs sur un module (specs.md 12.3/12.5), a gauche de
    sa pastille PV (par-dessus l'emplacement Bouclier) : une doree pour les buffs a duree
    limitee, une distincte pour les buffs persistants (qui durent tout le combat) - comptes
    separes, jamais additionnes dans une seule pastille. Chacune absente si son compte est a
    0. Une derniere pastille (encore plus a gauche) signale un leurre actif (specs.md 12.6),
    different d'un buff : pas de compte (present ou absent), se consomme a la prochaine
    attaque recue plutot qu'a l'expiration d'une duree. cx_pv/cy : memes reperes que la
    pastille PV de ce module (cf. _pastilles_pv_bouclier)."""
    buffs_duree = [buff for buff in module.buffs_actifs if buff.tours_restants is not None]
    buffs_persistants = [buff for buff in module.buffs_actifs if buff.tours_restants is None]
    elements = []
    cx = cx_pv - 2 * (RAYON_PASTILLE * 2 + MARGE_PASTILLE)
    if buffs_duree:
        elements += _pastille(cx, cy, COULEUR_PASTILLE_BUFFS, len(buffs_duree), lot)
        cx -= RAYON_PASTILLE * 2 + MARGE_PASTILLE
    if buffs_persistants:
        elements += _pastille(cx, cy, COULEUR_PASTILLE_BUFFS_PERSISTANTS, len(buffs_persistants), lot)
        cx -= RAYON_PASTILLE * 2 + MARGE_PASTILLE
    if module.leurre_actif:
        elements += _pastille(cx, cy, COULEUR_PASTILLE_LEURRE, 1, lot)
    return elements


LIBELLES_CIBLE = {
    CibleCarte.ENNEMI_UNIQUE: "un ennemi",
    CibleCarte.ENNEMIS_MULTIPLES: "tous les ennemis",
    CibleCarte.LIGNE_ENNEMIE: "la rangee ennemie visee (avant + arriere)",
    CibleCarte.ALLIE_UNIQUE: "un module",
    CibleCarte.ALLIES_MULTIPLES: "tous les modules",
    CibleCarte.MODULE_PRINCIPAL: "le module principal",
    CibleCarte.COLONNE_AVANT_ENNEMIE: "la ligne avant ennemie",
    CibleCarte.COLONNE_ARRIERE_ENNEMIE: "la ligne arriere ennemie",
    CibleCarte.COLONNE_AVANT_ALLIEE: "la ligne avant alliee",
}


def texte_effet_carte(carte: Carte) -> str:
    """Description generee a partir des donnees de la carte (type, cible, valeur, duree),
    reutilisable par tout ecran voulant afficher l'effet d'une carte en texte lisible (ecran de
    fin de combat, futur ecran de deck...). Meme principe que texteEffetCarte dans web/app.js -
    chaque plateforme sa version, PC et web ne partageant pas de code d'affichage."""
    cible = LIBELLES_CIBLE[carte.cible]
    if carte.type == TypeCarte.ATTAQUE:
        return f"Inflige {carte.valeur} degats a {cible}."
    if carte.type == TypeCarte.DEFENSE:
        if carte.action == ActionCarte.BOUCLIER_POURCENTAGE_PV:
            return f"Bouclier de {carte.valeur}% des PV de {cible}."
        if carte.action == ActionCarte.ANNULATION_PROCHAINE_ATTAQUE:
            return f"Annule la prochaine attaque sur {cible}."
        return f"Bouclier de {carte.valeur} a {cible}."
    if carte.type == TypeCarte.REPARATION:
        return f"Repare {carte.valeur} PV a {cible}."
    if carte.type == TypeCarte.OUTILS:
        if carte.action == ActionCarte.GAIN_ELECTRICITE:
            return f"Gagne {carte.valeur} ⚡."
        if carte.action == ActionCarte.GAIN_ELECTRICITE_PAR_MODULE:
            return f"Gagne {carte.valeur} ⚡ par module actif."
        if carte.action == ActionCarte.PIOCHE_SUPPLEMENTAIRE:
            return f"Pioche {carte.valeur} cartes supplementaires."
    if carte.type == TypeCarte.DEBUFF:
        if carte.action == ActionCarte.REDUCTION_DEGATS:
            return f"Diminue les degats infliges par {cible} de {carte.valeur}, pendant {carte.duree} tour(s)."
        if carte.action == ActionCarte.VULNERABILITE:
            return f"Augmente les degats subis par {cible} de {carte.valeur}%, pendant {carte.duree} tour(s)."
        if carte.action == ActionCarte.REDIRECTION_CIBLE:
            return f"Detourne l'attaque de {cible} vers un autre ennemi tire au hasard, pendant {carte.duree} tour(s)."
    if carte.type == TypeCarte.BUFF:
        if carte.action == ActionCarte.BOUCLIER_PAR_TOUR:
            duree = f" pendant {carte.duree} tour(s)" if carte.duree else ""
            return f"{cible} gagne {carte.valeur} bouclier a chaque tour{duree}."
    return f"Effet de {carte.valeur} a {cible}."


def _texte_et_couleur_effet(carte: Carte, valeur_effective: int) -> tuple[str, tuple[int, int, int]]:
    """Texte (+/-valeur reellement appliquee) et couleur du popup associe a l'effet d'une carte jouee."""
    if carte.type == TypeCarte.ATTAQUE:
        return f"-{valeur_effective}", COULEUR_POPUP_DEGATS
    if carte.type == TypeCarte.DEFENSE:
        if carte.action == ActionCarte.ANNULATION_PROCHAINE_ATTAQUE:
            return "Leurre actif !", COULEUR_POPUP_BOUCLIER
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


def _texte_type_buff(action: ActionCarte, valeur: int) -> str:
    """Texte decrivant un buff/debuff par son seul type (specs.md 12.1/12.3/12.4/12.5/13), sans
    mention de duree - reutilise par _libelle_buff (buff deja actif, duree ajoutee autour) et
    par la prochaine action d'un ennemi (POSE_BUFF, cf. _dessiner_survol, pas encore active
    donc pas de duree ecoulee a afficher)."""
    if action == ActionCarte.BOUCLIER_PAR_TOUR:
        return f"+{valeur} bouclier/tour"
    if action == ActionCarte.BOUCLIER_MIROIR:
        return f"Bouclier miroir {valeur}"
    if action == ActionCarte.VULNERABILITE:
        return f"Vulnerabilite +{valeur}%"
    if action == ActionCarte.REDIRECTION_CIBLE:
        return "Tir detourne"
    if action == ActionCarte.REDUCTION_DEGATS:
        return f"Degats reduits -{valeur}"
    if action == ActionCarte.AUGMENTATION_DEGATS:
        return f"Degats augmentes +{valeur}"
    return f"Buff +{valeur}"


def _libelle_buff(buff: BuffActif) -> str:
    """Texte d'une ligne d'infobulle pour un buff/debuff actif, sur un module ou un ennemi
    (specs.md 12.1/12.3/12.4/12.5/13 - meme modele des deux cotes, cf. carte.py:BuffActif).

    Pour un Bouclier miroir (specs.md 13, ennemi Miroir), precise le module du joueur qui
    recevra les degats renvoyes (BuffActif.cible_reflet, tire une bonne fois pour toutes a la
    pose du buff) - le joueur doit pouvoir l'anticiper avant d'attaquer l'ennemi protege."""
    texte = _texte_type_buff(buff.action, buff.valeur)
    if buff.action == ActionCarte.BOUCLIER_MIROIR and buff.cible_reflet is not None:
        texte += f" -> {buff.cible_reflet.nom}"
    if buff.tours_restants is None:
        duree = "illimite"
    else:
        duree = f"{buff.tours_restants} tour" + ("" if buff.tours_restants == 1 else "s")
    return f"{texte} ({duree})"


def _lignes_buffs(module: Module) -> list[str]:
    """Lignes d'infobulle pour les buffs actifs d'un module (specs.md 12.3/12.5), groupees
    separement : buffs a duree limitee d'abord, puis buffs persistants (qui durent tout le
    combat) - jamais melanges, meme separation que les deux pastilles (cf. _pastilles_buffs_module).
    Pas d'en-tete "Persistants" : chaque ligne de buff persistant se termine deja par "(illimite)"
    (cf. _libelle_buff), suffisant pour les distinguer."""
    buffs_duree = [buff for buff in module.buffs_actifs if buff.tours_restants is not None]
    buffs_persistants = [buff for buff in module.buffs_actifs if buff.tours_restants is None]
    lignes = [_libelle_buff(buff) for buff in buffs_duree]
    lignes.extend(_libelle_buff(buff) for buff in buffs_persistants)
    return lignes


class FenetreCombat(pyglet.window.Window):
    """Fenetre principale : affiche le combat du POC et gere les clics/survols de souris."""

    def __init__(self, combat: Combat | None = None, partie: Partie | None = None):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight - POC")
        self.combat = combat if combat is not None else creer_combat_poc()
        # None en mode demo (POC, cf. config_poc.py) ou aucune partie ne l'accompagne : la barre
        # laterale (Niveau/Argent/Deck/Vaisseau) n'a alors rien a afficher.
        self.partie = partie
        self.index_carte_selectionnee: int | None = None
        self.entite_survolee: Module | Ennemi | None = None
        self.survole_barre: str | None = None
        # True apres un clic sur "Quitter" (specs.md 8.1) : signale a main.py qu'il doit fermer
        # cette fenetre et revenir a l'ecran de selection du joueur, sans toucher a la partie
        # sauvegardee (decision utilisateur - ce combat en cours n'est jamais synchronise/
        # sauvegarde, contrairement a une fin de combat normale, cf. main.py:_ouvrir_combat).
        self.quitte_demandee: bool = False
        self.popups: list[tuple[AnimationPopup, str, tuple[int, int, int], float, float]] = []
        # Journal de combat (specs.md 8.1) : cartes jouees, actions ennemies, marqueurs de tour -
        # affiche par src/ui/ecran_journal.py, jamais vide (demarre avec le marqueur du tour 1).
        self.journal: list[list[journal_combat.Segment]] = [journal_combat.ligne_tour(1)]
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

        # Import differe : barre_laterale importe de ce module (HAUTEUR_FENETRE, _sprite_ajuste),
        # un import en tete de fichier creerait un cycle.
        from src.ui import barre_laterale

        elements.extend(self._dessiner_fond(lot))
        elements.extend(self._dessiner_vaisseau(lot))
        elements.extend(self._dessiner_flotte(lot))
        elements.extend(self._dessiner_popups(lot))
        elements.extend(self._dessiner_main(lot))
        elements.extend(self._dessiner_survol(lot))
        if self.partie is not None:
            elements.extend(barre_laterale.dessiner(self.partie, self.survole_barre, lot))

        elements.extend(self._dessiner_controles_combat(lot, barre_laterale))

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
        """Dessine chaque ennemi vivant ou detruit de la flotte (Flotte.positions(), y compris
        les detruits pour l'affichage grise) une seule fois, meme s'il occupe plusieurs cases
        (specs.md 3.2, ex. le Boss des pirates - deduplique comme Flotte.ennemis_vivants())."""
        elements = []
        dessines: list[Ennemi] = []
        for _position, ennemi in self.combat.flotte.positions().items():
            if any(existant is ennemi for existant in dessines):
                continue
            dessines.append(ennemi)
            rect = _rect_fusionne(self.combat.flotte.positions_de(ennemi))
            elements.extend(self._dessiner_ennemi_case(lot, rect, ennemi))
        return elements

    def _dessiner_ennemi_case(self, lot: pyglet.graphics.Batch, rect: tuple[float, float, float, float], ennemi: Ennemi) -> list:
        """Dessine une case ennemie (image + pastilles PV/Bouclier - les ennemis peuvent
        desormais en avoir, specs.md 13 -, + pastille orange du nombre de buffs/debuffs
        actifs s'il y en a au moins un), grisee si detruite. `rect` couvre une seule case, ou
        plusieurs fusionnees pour un ennemi a plusieurs emplacements (cf. _rect_fusionne)."""
        x, y, largeur, hauteur = rect
        detruit = ennemi.est_detruit()
        # Un ennemi a plusieurs emplacements (specs.md 3.2) a une case bien plus large que
        # haute : remplir toute la largeur (quitte a deborder un peu en hauteur) plutot que de
        # caler sur la hauteur comme un ennemi normal, qui le laisserait minuscule.
        if ennemi.emplacements > 1:
            sprite = _sprite_ajuste_largeur(ennemi.image, x, y, largeur, hauteur, lot)
        else:
            sprite = _sprite_ajuste(ennemi.image, x, y, largeur, hauteur, lot)
        if detruit:
            sprite.opacity = OPACITE_DETRUIT
            return [sprite, *self._texte_detruit(x, y, largeur, hauteur, lot)]
        elements = [sprite, *_pastilles_pv_bouclier(x, y, largeur, hauteur, ennemi.pv, ennemi.bouclier, lot)]
        if ennemi.buffs_actifs:
            cx_pv = x + largeur - RAYON_PASTILLE - MARGE_PASTILLE
            cx_debuffs = cx_pv - 2 * (RAYON_PASTILLE * 2 + MARGE_PASTILLE)
            cy = y + hauteur + MARGE_PASTILLE_HAUT + _RAYON_TOTAL_PASTILLE
            elements += _pastille(cx_debuffs, cy, COULEUR_PASTILLE_DEBUFFS, len(ennemi.buffs_actifs), lot)
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

    def _y_haut_controles_combat(self, barre_laterale) -> float:
        """Sommet du bloc controles de combat (Electricite/tour suivant/Quitter) : sous la barre
        laterale si affichee (self.partie non None), sinon au sommet de la fenetre."""
        if self.partie is None:
            return barre_laterale.Y_HAUT_PAR_DEFAUT
        return barre_laterale.Y_HAUT_PAR_DEFAUT - barre_laterale.HAUTEUR_CONTENU - 30

    def _rect_bouton_tour_suivant(self, barre_laterale) -> tuple[float, float, float, float]:
        y_haut = self._y_haut_controles_combat(barre_laterale)
        x = (barre_laterale.LARGEUR_BARRE - TAILLE_BOUTON_COMBAT) / 2
        y = y_haut - _DECALAGE_HAUT_TOUR_SUIVANT
        return x, y - TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT

    def _rect_bouton_quitter(self, barre_laterale) -> tuple[float, float, float, float]:
        y_haut = self._y_haut_controles_combat(barre_laterale)
        x = (barre_laterale.LARGEUR_BARRE - TAILLE_BOUTON_COMBAT) / 2
        y = y_haut - _DECALAGE_HAUT_QUITTER
        return x, y - TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT

    def _rect_bouton_journal(self, barre_laterale) -> tuple[float, float, float, float]:
        y_haut = self._y_haut_controles_combat(barre_laterale)
        x = (barre_laterale.LARGEUR_BARRE - TAILLE_BOUTON_COMBAT) / 2
        y = y_haut - _DECALAGE_HAUT_JOURNAL
        return x, y - TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT, TAILLE_BOUTON_COMBAT

    def _bouton_combat_a(self, x: int, y: int, barre_laterale) -> str | None:
        """Identifiant ("tour_suivant"/"quitter"/"journal") du bouton de controle de combat sous
        ce point, None si aucun."""
        if _point_dans_rectangle(x, y, *self._rect_bouton_tour_suivant(barre_laterale)):
            return "tour_suivant"
        if _point_dans_rectangle(x, y, *self._rect_bouton_quitter(barre_laterale)):
            return "quitter"
        if _point_dans_rectangle(x, y, *self._rect_bouton_journal(barre_laterale)):
            return "journal"
        return None

    def _dessiner_controles_combat(self, lot: pyglet.graphics.Batch, barre_laterale) -> list:
        """Electricite disponible + boutons icones tour suivant/Quitter/Journal (specs.md 8.1) -
        remplace l'ancien bandeau du haut (Electricite + texte "Fin de tour")."""
        y_haut = self._y_haut_controles_combat(barre_laterale)
        x_centre = barre_laterale.LARGEUR_BARRE / 2
        elements = [
            pyglet.text.Label(
                f"Electricite : {self.combat.joueur.electricite}",
                x=x_centre,
                y=y_haut - _DECALAGE_ELECTRICITE_COMBAT,
                anchor_x="center",
                anchor_y="center",
                font_size=12,
                batch=lot,
                group=GROUPE_SUPERPOSITION,
            )
        ]
        rect_tour_suivant = self._rect_bouton_tour_suivant(barre_laterale)
        elements.append(_sprite_ajuste(_ICONE_TOUR_SUIVANT, *rect_tour_suivant, lot))
        rect_quitter = self._rect_bouton_quitter(barre_laterale)
        elements.append(_sprite_ajuste(_ICONE_QUITTER, *rect_quitter, lot))
        rect_journal = self._rect_bouton_journal(barre_laterale)
        elements.append(_sprite_ajuste(_ICONE_JOURNAL, *rect_journal, lot))
        return elements

    def _dessiner_survol(self, lot: pyglet.graphics.Batch) -> list:
        """Affiche une infobulle (nom, PV/PV max, Bouclier) sur le module/ennemi survole.

        Pour un ennemi, ajoute aussi son intention (specs.md 13) : cible visee et degats pour
        une ATTAQUE, type de buff/debuff pose (via _texte_type_buff) et sa cible pour une
        POSE_BUFF - "x{repetitions}" dans les deux cas si l'action se declenche plusieurs fois
        dans le meme tour (ex. Le nettoyeur). Pour un module, ajoute le detail de ses buffs
        actifs (specs.md 12.3/12.5).
        """
        if self.combat.etat != EtatCombat.EN_COURS:
            return []
        entite = self.entite_survolee
        if entite is None or entite.est_detruit():
            return []

        if isinstance(entite, Ennemi):
            rect = self._rect_ennemi_affiche(entite)
            if rect is None:
                return []
            lignes = [entite.nom, f"PV {entite.pv}/{entite.pv_max}", f"Bouclier {entite.bouclier}"]
            # Toutes les Actions actives au prochain tour (specs.md 13), pas seulement la
            # premiere : plusieurs peuvent se declencher le meme tour (ex. le Boss des pirates,
            # qui attaque ET pose un buff), chacune donne sa propre ligne.
            for action in self.combat.prochaines_actions_actives(entite):
                # "x{repetitions}" (specs.md 13, ex. Le nettoyeur) : l'action se declenche
                # plusieurs fois dans le meme tour, chaque occurrence infligeant/posant la
                # valeur affichee - sans cette mention, l'infobulle laisse croire a un seul
                # coup alors que les degats/effet reels sont multiplies par ce nombre.
                repetition = f" x{action.repetitions}" if action.repetitions > 1 else ""
                if action.type == TypeActionEnnemi.ATTAQUE:
                    degats = entite.degats_attaque_effectifs(action.valeur)
                    if action.cible == CibleActionEnnemi.TOUS_MODULES_JOUEUR:
                        lignes.append(f"Vise : tous les modules ({degats} degats{repetition})")
                    else:
                        cible = self.combat.previsualiser_cible(entite)
                        if cible is not None:
                            lignes.append(f"Vise : {cible.nom} ({degats} degats{repetition})")
                        elif any(buff.action == ActionCarte.REDIRECTION_CIBLE for buff in entite.buffs_actifs):
                            # Tir allie actif (specs.md 12.6) : la cible reelle (un autre
                            # ennemi) n'est tiree au hasard qu'a la resolution du tour, jamais
                            # au survol - cf. Combat.previsualiser_cible/_cible_redirection,
                            # deterministe.
                            lignes.append(f"Vise : un allie au hasard{repetition}")
                elif action.type == TypeActionEnnemi.POSE_BUFF:
                    texte_buff = _texte_type_buff(action.action_buff, action.valeur)
                    cible_texte = "sur lui-meme" if action.cible == CibleActionEnnemi.SOI_MEME else "sur un allie au hasard"
                    lignes.append(f"Va poser {texte_buff} ({cible_texte}){repetition}")
            lignes.extend(_libelle_buff(buff) for buff in entite.buffs_actifs)
        else:
            rect = self._rect_du_module(entite)
            lignes = [entite.nom, f"PV {entite.pv}/{entite.pv_max}", f"Bouclier {entite.bouclier}"]
            lignes.extend(_lignes_buffs(entite))
            if entite.leurre_actif:
                lignes.append("Leurre actif (annule la prochaine attaque)")

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
        """Gere les clics de souris : selection de carte, ciblage, tour suivant, quitter."""
        # Imports differes, cf. on_draw : cycle avec ce module sinon.
        from src.ui import barre_laterale

        bouton_combat = self._bouton_combat_a(x, y, barre_laterale)
        if bouton_combat == "quitter":
            if self.partie is None:
                # Mode demo (POC) : aucun ecran de selection de joueur a rouvrir, on se contente
                # de fermer la fenetre (cf. commentaire de self.quitte_demandee, __init__).
                self.close()
            else:
                self.quitte_demandee = True
            return
        if bouton_combat == "tour_suivant" and self.combat.etat == EtatCombat.EN_COURS:
            attaques = self.combat.finir_tour_joueur()
            for _position, ennemi, cible, valeur, type_evenement in attaques:
                self.journal.append(journal_combat.ligne_evenement_ennemi(ennemi, cible, valeur, type_evenement))
            if self.combat.etat == EtatCombat.EN_COURS:
                self.journal.append(journal_combat.ligne_tour(self.combat.tour_ennemi_actuel + 1))
            self._afficher_popups_attaques_ennemi(attaques)
            self.index_carte_selectionnee = None
            return
        if bouton_combat == "journal":
            from src.ui.ecran_journal import EcranJournal

            barre_laterale.ouvrir_survol(EcranJournal(list(self.journal)))
            return

        if self.partie is not None:
            from src.ui.ecran_deck import EcranDeck
            from src.ui.ecran_vaisseau import EcranVaisseau

            bouton_barre = barre_laterale.bouton_survole(x, y)
            if bouton_barre == "deck":
                barre_laterale.ouvrir_survol(EcranDeck(deck_de_la_partie(self.partie)))
                return
            if bouton_barre == "vaisseau":
                barre_laterale.ouvrir_survol(EcranVaisseau(self.partie))
                return

        if self.combat.etat != EtatCombat.EN_COURS:
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
        if self.partie is not None:
            from src.ui import barre_laterale

            self.survole_barre = barre_laterale.bouton_survole(x, y)

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
        if cibles_touchees:
            self.journal.append(journal_combat.ligne_carte_jouee(carte, cible))
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

    def _rect_ennemi_affiche(self, ennemi: Ennemi) -> tuple[float, float, float, float] | None:
        """Rectangle affiche de cet ennemi dans la flotte (fusion de ses cases s'il en occupe
        plusieurs, specs.md 3.2, cf. _rect_fusionne), ou None s'il n'y est pas."""
        positions = self.combat.flotte.positions_de(ennemi)
        return _rect_fusionne(positions) if positions else None

    def _afficher_popups_carte(self, carte: Carte, cibles: list[tuple[Module | Ennemi, int]]) -> None:
        """Affiche un popup +/-N (montant reellement applique) sur chaque cible touchee par une carte jouee."""
        for cible, valeur_effective in cibles:
            texte, couleur = _texte_et_couleur_effet(carte, valeur_effective)
            self._ajouter_popup(cible, texte, couleur)

    def _afficher_popups_attaques_ennemi(
        self, evenements: list[tuple[Position, Ennemi, Module | Ennemi, int, str]]
    ) -> None:
        """Affiche un popup sur chaque cible touchee par une Action ennemie (specs.md 13) :
        -N (degats) sur un module, sur un autre ennemi si Tir allie est actif (specs.md 12.6)
        ou sur l'attaquant lui-meme en cas de renvoi par un Bouclier miroir, ou +N (bouclier)
        sur la cible d'une Action POSE_BUFF."""
        for _position, _ennemi, cible_touchee, valeur, type_evenement in evenements:
            if type_evenement == "bouclier":
                self._ajouter_popup(cible_touchee, f"+{valeur}", COULEUR_POPUP_BOUCLIER)
            else:
                self._ajouter_popup(cible_touchee, f"-{valeur}", COULEUR_POPUP_DEGATS)

    def _ajouter_popup(self, cible: Module | Ennemi, texte: str, couleur: tuple[int, int, int]) -> None:
        """Demarre l'affichage d'un popup +/-N centre sur la case de cette cible, pour 2 secondes."""
        x, y, largeur, hauteur = self._rect_de_cible(cible)
        animation = AnimationPopup()
        animation.demarrer()
        self.popups.append((animation, texte, couleur, x + largeur / 2, y + hauteur / 2))

    def _rect_de_cible(self, cible: Module | Ennemi) -> tuple[float, float, float, float]:
        """Rectangle (x, y, largeur, hauteur) de la case d'un module ou d'un ennemi (fusion de
        ses cases pour un ennemi a plusieurs emplacements, specs.md 3.2)."""
        if isinstance(cible, Ennemi):
            rect = self._rect_ennemi_affiche(cible)
            return rect if rect is not None else (0, 0, 0, 0)
        return self._rect_du_module(cible)

    def _rect_du_module(self, module: Module) -> tuple[float, float, float, float]:
        """Rectangle d'un module du joueur (son emplacement equipe, ou tout le vaisseau si c'est la base)."""
        for position, occupant in self.combat.joueur.vaisseau.modules_equipes().items():
            if occupant is module:
                return _rect_module(position)
        return _rect_vaisseau()
