"""
Dessin d'une carte sur PC (specs/generation-images/prompt-modele-carte.md, interface.md 8.2) :
gabarit de la couleur de la rarete, illustration dans la fenetre, barre du haut (cout, munitions,
lancements a gauche, icone du type a droite), texte et nom. Utilise par tous les ecrans qui
montrent une carte. Meme disposition que .carte-visuel du web (src/web/style.css).
"""

import pyglet

from src.gameplay.carte import Carte
from src.ui import textes_combat
from src.ui.commun import chemin_image

# Rapport hauteur / largeur du gabarit (864 x 1216)
RAPPORT = 1216 / 864

# Zones du gabarit, en fraction de la largeur et de la hauteur, mesurees depuis le HAUT de l'image :
# (gauche, haut, droite, bas). Memes valeurs que src/web/style.css (.carte-visuel).
ZONE_BARRE = (0.067, 0.051, 0.933, 0.112)
ZONE_FENETRE = (0.223, 0.144, 0.777, 0.561)
ZONE_TEXTE = (0.113, 0.607, 0.887, 0.845)
ZONE_NOM = (0.113, 0.875, 0.887, 0.933)

ICONE_TYPE = {
    "ATTAQUE": "type_attaque",
    "DEFENSE": "type_defense",
    "REPARATION": "type_reparation",
    "BUFF": "type_buff",
    "DEBUFF": "type_debuff",
    "OUTILS": "type_outils",
    "CONTROLE": "type_controle",
}

COULEUR_TEXTE = (235, 240, 250, 255)
COULEUR_OMBRE = (0, 0, 0, 255)
OPACITE_INJOUABLE = 110

# Points pyglet -> pixels (96 dpi)
_PIXELS_PAR_POINT = 96 / 72

_cache: dict[str, pyglet.image.AbstractImage] = {}


def _image(chemin: str) -> pyglet.image.AbstractImage:
    if chemin not in _cache:
        _cache[chemin] = pyglet.image.load(chemin)
    return _cache[chemin]


def chemin_gabarit(carte: Carte) -> str:
    return chemin_image(f"assets/interface/cartes/modele_{carte.rarete.name.lower()}.png")


def chemin_icone(nom: str) -> str:
    return chemin_image(f"assets/interface/icones/{nom}.png")


def hauteur_carte(largeur: float) -> float:
    return largeur * RAPPORT


def _rect(zone: tuple, x: float, y: float, largeur: float) -> tuple[float, float, float, float]:
    """Rectangle pyglet (x, y du bas, largeur, hauteur) d'une zone du gabarit."""
    hauteur = hauteur_carte(largeur)
    gauche, haut, droite, bas = zone
    return x + gauche * largeur, y + (1 - bas) * hauteur, (droite - gauche) * largeur, (bas - haut) * hauteur


def _sprite(chemin: str, x: float, y: float, largeur: float, hauteur: float, lot, groupe) -> pyglet.sprite.Sprite:
    sprite = pyglet.sprite.Sprite(_image(chemin), x=x, y=y, batch=lot, group=groupe)
    sprite.scale_x = largeur / sprite.image.width
    sprite.scale_y = hauteur / sprite.image.height
    return sprite


def _texte_ombre(texte: str, x: float, y: float, taille_pt: float, lot, groupe, anchor_x: str = "left") -> list:
    """Chiffre de la barre du haut, avec une ombre pour rester lisible sur les barres colorees."""
    decalage = max(1.0, taille_pt / 8)
    return [
        pyglet.text.Label(
            texte, x=x + dx, y=y + dy, anchor_x=anchor_x, anchor_y="center", font_size=taille_pt,
            weight="bold", color=couleur, batch=lot, group=groupe,
        )
        for dx, dy, couleur in ((decalage, -decalage, COULEUR_OMBRE), (0, 0, (255, 255, 255, 255)))
    ]


_mesures: dict[tuple[str, float, bool], float] = {}


def _largeur_texte(texte: str, taille_pt: float, gras: bool) -> float:
    """Largeur d'une ligne de texte (Label d'une seule ligne, hors lot), mise en cache."""
    cle = (texte, taille_pt, gras)
    if cle not in _mesures:
        _mesures[cle] = pyglet.text.Label(texte, font_size=taille_pt, weight="bold" if gras else "normal").content_width
    return _mesures[cle]


def _couper(texte: str, largeur: float, taille_pt: float, gras: bool) -> list[str]:
    """Coupe le texte en lignes qui tiennent dans la largeur (un mot trop long reste seul)."""
    lignes: list[str] = []
    for mot in texte.split():
        essai = f"{lignes[-1]} {mot}" if lignes else mot
        if lignes and _largeur_texte(essai, taille_pt, gras) <= largeur:
            lignes[-1] = essai
        else:
            lignes.append(mot)
    return lignes


def _label_ajuste(texte: str, rect: tuple, taille_max_pt: float, lot, groupe, gras: bool) -> list:
    """Texte centre dans la zone, a la taille la plus grande (au plus taille_max_pt) qui y tient.
    Une Label par ligne, coupee ici : le texte multiligne de pyglet perd des espaces sous Windows
    (« moduleunique »)."""
    x, y, largeur, hauteur = rect
    taille = taille_max_pt
    while True:
        lignes = _couper(texte, largeur, taille, gras)
        interligne = taille * _PIXELS_PAR_POINT * 1.2
        tient = len(lignes) * interligne <= hauteur and all(_largeur_texte(l, taille, gras) <= largeur + 1 for l in lignes)
        if tient or taille <= 4:
            break
        taille -= 0.5
    y_premiere = y + hauteur / 2 + (len(lignes) - 1) * interligne / 2
    return [
        pyglet.text.Label(
            ligne, x=x + largeur / 2, y=y_premiere - i * interligne, anchor_x="center", anchor_y="center",
            font_size=taille, weight="bold" if gras else "normal", color=COULEUR_TEXTE, batch=lot, group=groupe,
        )
        for i, ligne in enumerate(lignes)
    ]


# Toutes les cartes d'un ecran sous un meme groupe, la carte agrandie au survol au-dessus de tout
GROUPE_CARTES = pyglet.graphics.Group(order=0)
GROUPE_CARTE_AGRANDIE = pyglet.graphics.Group(order=10)


def groupes_carte(ordre: int, parent: pyglet.graphics.Group | None = None) -> tuple:
    """Trois groupes (gabarit, illustration, textes et icones) propres a une carte : une carte qui
    en chevauche une autre (main en eventail, carte agrandie) passe entierement au-dessus."""
    parent = parent or GROUPE_CARTES
    return tuple(pyglet.graphics.Group(order=ordre * 3 + k, parent=parent) for k in range(3))


def dessiner_carte(
    carte: Carte,
    x: float,
    y: float,
    largeur: float,
    lot: pyglet.graphics.Batch,
    groupes: tuple | None = None,
    injouable: bool = False,
) -> list:
    """Dessine la carte, coin bas gauche en (x, y), et renvoie les elements a garder en vie."""
    fond, milieu, dessus = groupes or groupes_carte(0)
    hauteur = hauteur_carte(largeur)
    elements = [_sprite(chemin_gabarit(carte), x, y, largeur, hauteur, lot, fond)]
    elements.append(_sprite(chemin_image(carte.image), *_rect(ZONE_FENETRE, x, y, largeur), lot, milieu))

    bx, by, bl, bh = _rect(ZONE_BARRE, x, y, largeur)
    icone = bh * 0.85
    taille_chiffre = bh * 0.6 / _PIXELS_PAR_POINT
    yc = by + bh / 2
    cx = bx + bh * 0.2
    valeurs = [("cout", str(carte.cout))]
    munitions = textes_combat.texte_munitions(carte)
    if munitions:
        valeurs.append(("munitions", munitions))
    if textes_combat.lancements(carte) > 1:
        valeurs.append(("lancements", f"×{textes_combat.lancements(carte)}"))
    for nom_icone, texte in valeurs:
        elements.append(_sprite(chemin_icone(nom_icone), cx, yc - icone / 2, icone, icone, lot, dessus))
        elements.extend(_texte_ombre(texte, cx + icone, yc, taille_chiffre, lot, dessus))
        cx += icone + bh * (0.5 + 0.38 * len(texte))
    elements.append(
        _sprite(chemin_icone(ICONE_TYPE[carte.categorie.name]), bx + bl - icone - bh * 0.2, yc - icone / 2, icone, icone, lot, dessus)
    )

    # Taille du nom = taille maximale du texte (decision utilisateur, 2026-11-27)
    rect_nom = _rect(ZONE_NOM, x, y, largeur)
    marge = largeur * 0.025
    rect_nom = (rect_nom[0] + marge, rect_nom[1], rect_nom[2] - 2 * marge, rect_nom[3])
    taille_nom = rect_nom[3] * 0.76 / _PIXELS_PAR_POINT
    nom = _label_ajuste(carte.nom, rect_nom, taille_nom, lot, dessus, gras=True)
    tx, ty, tl, th = _rect(ZONE_TEXTE, x, y, largeur)
    texte = _label_ajuste(
        carte.description_affichee(), (tx + marge, ty + marge, tl - 2 * marge, th - 2 * marge), taille_nom, lot, dessus, gras=False
    )
    elements += nom + texte
    if carte.persistante:
        elements.extend(_bandeau_persistante(x, y, largeur, lot, dessus))
    if injouable:
        for element in elements:
            element.opacity = OPACITE_INJOUABLE
    return elements


def _bandeau_persistante(x: float, y: float, largeur: float, lot, groupe) -> list:
    """Mot-cle Persistante, sur le bas de l'illustration (la carte n'a pas d'autre place pour lui)."""
    fx, fy, fl, fh = _rect(ZONE_FENETRE, x, y, largeur)
    hauteur = fh * 0.13
    fond = pyglet.shapes.Rectangle(fx, fy, fl, hauteur, color=(156, 54, 181), batch=lot, group=groupe)
    fond.opacity = 220
    texte = pyglet.text.Label(
        "PERSISTANTE", x=fx + fl / 2, y=fy + hauteur / 2, anchor_x="center", anchor_y="center",
        font_size=hauteur * 0.6 / _PIXELS_PAR_POINT, weight="bold", color=(255, 255, 255, 255), batch=lot, group=groupe,
    )
    return [fond, texte]


LARGEUR_AGRANDIE = 300
COULEUR_FOND_DETAILS = (10, 10, 12)
OPACITE_FOND_DETAILS = 215
TAILLE_POLICE_DETAILS = 13


def dessiner_details(lignes: list[str], x: float, y_haut: float, largeur: float, lot, groupe) -> list:
    """Bandeau sous une carte agrandie : ce que la carte ne montre pas (module, pas jouable...)."""
    if not lignes:
        return []
    hauteur = hauteur_details(lignes)
    fond = pyglet.shapes.Rectangle(x, y_haut - hauteur, largeur, hauteur, color=COULEUR_FOND_DETAILS, batch=lot, group=groupe)
    fond.opacity = OPACITE_FOND_DETAILS
    textes = [
        pyglet.text.Label(
            ligne, x=x + largeur / 2, y=y_haut - 15 - 22 * i, anchor_x="center", anchor_y="center",
            font_size=TAILLE_POLICE_DETAILS, color=(255, 255, 255, 255), batch=lot, group=groupe,
        )
        for i, ligne in enumerate(lignes)
    ]
    return [fond, *textes]


def hauteur_details(lignes: list[str]) -> float:
    return 22 * len(lignes) + 8 if lignes else 0


def dessiner_carte_agrandie_a_cote(
    carte: Carte,
    rect_source: tuple[float, float, float, float],
    lignes: list[str],
    lot: pyglet.graphics.Batch,
    groupe_parent: pyglet.graphics.Group,
    largeur_fenetre: float,
    hauteur_fenetre: float,
) -> list:
    """Carte survolee en grand (decision utilisateur, 2026-11-27), a droite de la carte source
    (a gauche faute de place), avec ses details dessous, le tout dans la fenetre."""
    sx, sy, sl, sh = rect_source
    hauteur = hauteur_carte(LARGEUR_AGRANDIE)
    total = hauteur + hauteur_details(lignes)
    x = sx + sl + 12
    if x + LARGEUR_AGRANDIE > largeur_fenetre - 10:
        x = sx - 12 - LARGEUR_AGRANDIE
    x = min(max(x, 10), largeur_fenetre - LARGEUR_AGRANDIE - 10)
    y_bas_total = min(max(sy + sh / 2 - total / 2, 10), hauteur_fenetre - total - 10)
    y = y_bas_total + total - hauteur
    groupes = groupes_carte(0, parent=groupe_parent)
    elements = dessiner_carte(carte, x, y, LARGEUR_AGRANDIE, lot, groupes)
    return elements + dessiner_details(lignes, x, y, LARGEUR_AGRANDIE, lot, groupes[2])


HAUTEUR_TITRE = 26
COULEUR_TITRE = (180, 200, 230, 255)
COULEUR_SURVOL = (255, 255, 255)


def hauteur_carte_titree(largeur: float, titre: str | None) -> float:
    """Hauteur d'une carte a choisir, avec la place de son titre au-dessus (ex. nom du module)."""
    return hauteur_carte(largeur) + (HAUTEUR_TITRE if titre else 0)


def dessiner_carte_a_choisir(
    carte: Carte,
    rect: tuple[float, float, float, float],
    lot: pyglet.graphics.Batch,
    ordre: int = 0,
    titre: str | None = None,
    survolee: bool = False,
    choisie: bool = False,
    couleur_choix: tuple = (210, 180, 40),
) -> list:
    """Carte d'un ecran de choix (recompense, Aventure, deck) dans son rectangle (x, y, largeur,
    hauteur_carte_titree) : titre au-dessus, cadre blanc au survol, cadre colore si choisie."""
    x, y, largeur, _hauteur = rect
    groupes = groupes_carte(ordre)
    hauteur = hauteur_carte(largeur)
    elements = dessiner_carte(carte, x, y, largeur, lot, groupes)
    if titre:
        elements.append(
            pyglet.text.Label(
                titre, x=x + largeur / 2, y=y + hauteur + HAUTEUR_TITRE / 2, anchor_x="center", anchor_y="center",
                font_size=12, color=COULEUR_TITRE, batch=lot, group=groupes[2],
            )
        )
    if choisie or survolee:
        couleur = couleur_choix if choisie else COULEUR_SURVOL
        elements.append(
            pyglet.shapes.Box(x - 4, y - 4, largeur + 8, hauteur + 8, thickness=4, color=couleur, batch=lot, group=groupes[0])
        )
    return elements


COULEUR_QUANTITE = (255, 220, 120, 255)


def dessiner_carte_de_grille(
    carte: Carte,
    rect: tuple[float, float, float, float],
    quantite: int,
    survolee: bool,
    lot: pyglet.graphics.Batch,
    ordre: int,
    titre: str | None = None,
) -> list:
    """Carte d'une grille de deck : cadre blanc au survol, nombre d'exemplaires au-dessus si > 1."""
    x, y, largeur, _hauteur = rect
    elements = dessiner_carte_a_choisir(carte, rect, lot, ordre=ordre, titre=titre, survolee=survolee)
    if quantite > 1:
        elements.append(
            pyglet.text.Label(
                f"×{quantite}", x=x + largeur - 4, y=y + hauteur_carte(largeur) + 4, anchor_x="right", anchor_y="bottom",
                font_size=14, weight="bold", color=COULEUR_QUANTITE, batch=lot, group=groupes_carte(ordre)[2],
            )
        )
    return elements
