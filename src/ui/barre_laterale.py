"""
Barre laterale persistante (specs.md 2.4/10.3) : affichee a gauche de tous les ecrans du parcours,
Combat compris - niveau, Argent, et deux boutons qui ouvrent un ecran de consultation en survol
(Deck, Vaisseau) par-dessus l'ecran appelant, qui reste ouvert et inchange derriere. En Combat,
`src/ui/fenetre.py` empile juste en dessous ses propres controles (Electricite, tour suivant,
Quitter - cf. FenetreCombat._dessiner_controles_combat), qui remplacent l'ancien bandeau du haut.

Ce module ne definit pas d'ecran : seulement des fonctions de dessin/hit-test partagees, a appeler
depuis le `_dessiner()`/`on_mouse_motion()`/`on_mouse_press()` de chaque ecran qui integre la
barre - meme convention de duplication legere que le reste du projet (CLAUDE.md), chaque ecran
garde son propre etat de survol/clic.
"""

import pyglet
from pyglet import shapes

from src.gameplay.donnees import RACINE
from src.gameplay.partie import Partie
from src.ui.fenetre import HAUTEUR_FENETRE, _sprite_ajuste

# Largeur choisie pour tenir sous la marge la plus etroite des ecrans qui l'affichent (grille de
# modules de Station service, marge de 92px) sans avoir a retoucher leur mise en page.
LARGEUR_BARRE = 90

COULEUR_FOND_BOUTON = (20, 24, 34)
COULEUR_CONTOUR_BOUTON = (90, 110, 150)
COULEUR_CONTOUR_SURVOLE = (255, 255, 255)
COULEUR_TEXTE = (255, 255, 255)
COULEUR_ARGENT = (255, 220, 120)
OPACITE_FOND = 190

_ICONE_DECK = str(RACINE / "assets" / "interface" / "deck.png")
_ICONE_VAISSEAU = str(RACINE / "assets" / "interface" / "vaisseau.png")

TAILLE_ICONE = 60
X_ICONE = (LARGEUR_BARRE - TAILLE_ICONE) / 2

# Sommet de la barre par defaut - meme position sur tous les ecrans, Combat compris (plus de
# bandeau du haut a eviter, cf. module docstring). Un ecran peut passer un y_haut different a
# dessiner()/bouton_survole() s'il a besoin de decaler la barre pour une raison qui lui est propre.
Y_HAUT_PAR_DEFAUT = HAUTEUR_FENETRE - 30

# Decalages relatifs au sommet de la barre (y_haut) - independants de l'ecran qui l'affiche.
_DECALAGE_ARGENT = 24
_DECALAGE_HAUT_DECK = 70
_DECALAGE_COMPTEUR_DECK = _DECALAGE_HAUT_DECK + TAILLE_ICONE + 14
_DECALAGE_HAUT_VAISSEAU = _DECALAGE_COMPTEUR_DECK + 30
# Hauteur totale du contenu de la barre (du sommet au bas du bouton Vaisseau) - exportee pour les
# ecrans qui doivent empiler quelque chose juste en dessous (cf. FenetreCombat, src/ui/fenetre.py).
HAUTEUR_CONTENU = _DECALAGE_HAUT_VAISSEAU + TAILLE_ICONE


def _rect_bouton_deck(y_haut: float) -> tuple[float, float, float, float]:
    y = y_haut - _DECALAGE_HAUT_DECK
    return X_ICONE, y - TAILLE_ICONE, TAILLE_ICONE, TAILLE_ICONE


def _rect_bouton_vaisseau(y_haut: float) -> tuple[float, float, float, float]:
    y = y_haut - _DECALAGE_HAUT_VAISSEAU
    return X_ICONE, y - TAILLE_ICONE, TAILLE_ICONE, TAILLE_ICONE


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


def bouton_survole(x: int, y: int, y_haut: float = Y_HAUT_PAR_DEFAUT) -> str | None:
    """Identifiant ("deck"/"vaisseau") du bouton sous ce point, None si aucun - a appeler depuis
    on_mouse_motion/on_mouse_press de l'ecran integrant la barre. `y_haut` : voir dessiner()."""
    if _point_dans_rectangle(x, y, *_rect_bouton_deck(y_haut)):
        return "deck"
    if _point_dans_rectangle(x, y, *_rect_bouton_vaisseau(y_haut)):
        return "vaisseau"
    return None


def dessiner(
    partie: Partie, survole: str | None, lot: pyglet.graphics.Batch, y_haut: float = Y_HAUT_PAR_DEFAUT
) -> list:
    """Dessine la barre : niveau, Argent, boutons Deck (avec nombre de cartes)/Vaisseau -
    `survole` est l'identifiant renvoye par bouton_survole pour l'etat de survol courant. `y_haut`
    place le sommet de la barre (par defaut juste sous le haut de la fenetre) - le Combat passe une
    valeur plus basse pour la faire tenir sous son bandeau Electricite/Fin de tour."""
    elements = [
        pyglet.text.Label(
            f"Niveau {partie.niveau}",
            x=LARGEUR_BARRE / 2, y=y_haut, anchor_x="center", anchor_y="center",
            font_size=13, color=(*COULEUR_TEXTE, 255), batch=lot,
        ),
        pyglet.text.Label(
            f"{partie.argent} €",
            x=LARGEUR_BARRE / 2, y=y_haut - _DECALAGE_ARGENT, anchor_x="center", anchor_y="center",
            font_size=13, color=(*COULEUR_ARGENT, 255), batch=lot,
        ),
    ]
    elements.extend(_dessiner_bouton(_rect_bouton_deck(y_haut), _ICONE_DECK, survole == "deck", lot))
    elements.append(
        pyglet.text.Label(
            f"{len(partie.deck)} cartes",
            x=LARGEUR_BARRE / 2, y=y_haut - _DECALAGE_COMPTEUR_DECK, anchor_x="center", anchor_y="center",
            font_size=10, color=(*COULEUR_TEXTE, 255), batch=lot,
        )
    )
    elements.extend(_dessiner_bouton(_rect_bouton_vaisseau(y_haut), _ICONE_VAISSEAU, survole == "vaisseau", lot))
    return elements


def _dessiner_bouton(
    rect: tuple[float, float, float, float], icone: str, survole: bool, lot: pyglet.graphics.Batch
) -> list:
    x, y, largeur, hauteur = rect
    cadre = shapes.BorderedRectangle(
        x, y, largeur, hauteur, border=2, color=COULEUR_FOND_BOUTON,
        border_color=COULEUR_CONTOUR_SURVOLE if survole else COULEUR_CONTOUR_BOUTON, batch=lot,
    )
    cadre.opacity = OPACITE_FOND
    sprite = _sprite_ajuste(icone, x, y, largeur, hauteur, lot)
    return [cadre, sprite]


def ouvrir_survol(fenetre_survol: pyglet.window.Window) -> None:
    """Ouvre un ecran de consultation (EcranDeck/EcranVaisseau) par-dessus l'ecran appelant, qui
    reste ouvert et inchange derriere (aucun etat a preserver/rouvrir, contrairement a
    main.py:_ouvrir_voir_deck qui fermait l'ecran appelant avant d'afficher celui-ci) -
    fenetre_survol se referme toute seule via son bouton Retour (self.termine)."""

    def verifier(_dt: float) -> None:
        if not fenetre_survol.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre_survol.close()

    pyglet.clock.schedule_interval(verifier, 1 / 30)
