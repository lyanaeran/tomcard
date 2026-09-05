"""
Construction du journal de combat (specs.md 8.1) : lignes texte multicolores decrivant les
cartes jouees, les actions ennemies resolues, et les marqueurs de tour - affichees par
src/ui/ecran_journal.py (PC) cote pyglet, et en JS directement dans web/app.js (aucun code
partage possible entre les deux plateformes d'affichage, cf. CLAUDE.md).

Une ligne du journal est une liste de segments (texte, couleur) concatenes sans espace
supplementaire - chaque texte doit donc deja porter les espaces necessaires autour de lui.
"""

from src.gameplay.carte import Carte, CibleCarte
from src.gameplay.ennemi import Ennemi
from src.gameplay.journal import Evenement, EvenementActionEnnemi, EvenementCarteJouee, EvenementTour
from src.gameplay.module import Module

Segment = tuple[str, tuple[int, int, int]]

COULEUR_CARTE = (235, 200, 60)
COULEUR_MODULE = (100, 210, 100)
COULEUR_ENNEMI = (225, 80, 80)
COULEUR_TEXTE = (120, 180, 235)
COULEUR_TOUR = (255, 255, 255)

LIBELLES_CIBLE_GENERIQUE = {
    CibleCarte.ALLIES_MULTIPLES: "tous les modules",
    CibleCarte.ENNEMIS_MULTIPLES: "tous les ennemis",
    CibleCarte.MODULE_PRINCIPAL: "le module principal",
}


def _segment_cible(cible) -> Segment:
    if isinstance(cible, Module):
        return (cible.nom, COULEUR_MODULE)
    return (cible.nom, COULEUR_ENNEMI)


def ligne_carte_jouee(carte: Carte, cible) -> list[Segment]:
    """Ligne de journal pour une carte jouee avec succes (specs.md 8.1) : son nom en jaune, la
    cible visee en vert (module) ou rouge (ennemi) si un clic l'a designee, sinon le libelle
    generique de sa cible (CIBLES_SANS_CLIC) en bleu comme le reste du texte.

    Phrase invariante "Carte {nom} jouee..." (plutot que "{nom} joue(e)") pour eviter tout
    probleme d'accord de genre avec le nom de la carte, absent de config/cartes.json.
    """
    segments: list[Segment] = [("Carte ", COULEUR_TEXTE), (carte.nom, COULEUR_CARTE)]
    if cible is None:
        if carte.cible in LIBELLES_CIBLE_GENERIQUE:
            segments.append((f" jouee sur {LIBELLES_CIBLE_GENERIQUE[carte.cible]}.", COULEUR_TEXTE))
        else:
            segments.append((" jouee.", COULEUR_TEXTE))
    elif isinstance(cible, Module):
        segments.append((" jouee sur le module ", COULEUR_TEXTE))
        segments.append((cible.nom, COULEUR_MODULE))
        segments.append((".", COULEUR_TEXTE))
    else:
        segments.append((" jouee sur ", COULEUR_TEXTE))
        segments.append((cible.nom, COULEUR_ENNEMI))
        segments.append((".", COULEUR_TEXTE))
    return segments


def ligne_evenement_ennemi(ennemi: Ennemi, cible, valeur: int, type_evenement: str) -> list[Segment]:
    """Ligne de journal pour un evenement resolu au tour ennemi (specs.md 13) : attaque
    (type_evenement="degats") ou pose d'un buff/bouclier (type_evenement="bouclier"), cf.
    Combat.finir_tour_joueur. Le nom de l'ennemi a l'origine de l'action est toujours en rouge ;
    celui de la cible touchee en vert (module) ou rouge (ennemi, ex. Tir allie/Bouclier miroir).
    """
    segments: list[Segment] = [(ennemi.nom, COULEUR_ENNEMI)]
    if type_evenement == "degats":
        if cible is ennemi:
            segments.append((f" subit {valeur} degats (renvoyes).", COULEUR_TEXTE))
        else:
            segments.append((" attaque ", COULEUR_TEXTE))
            segments.append(_segment_cible(cible))
            segments.append((f" : {valeur} degats.", COULEUR_TEXTE))
    else:
        if cible is ennemi:
            segments.append((f" se protege (+{valeur}).", COULEUR_TEXTE))
        else:
            segments.append((" pose un effet sur ", COULEUR_TEXTE))
            segments.append(_segment_cible(cible))
            segments.append((f" (+{valeur}).", COULEUR_TEXTE))
    return segments


def ligne_tour(numero: int) -> list[Segment]:
    """Marqueur de tour (specs.md 8.1), ex. 'Tour 1'."""
    return [(f"--- Tour {numero} ---", COULEUR_TOUR)]


def ligne_evenement(evenement: Evenement) -> list[Segment]:
    """Met en forme un evenement du journal de combat (Combat.journal, specs.md 8.1) - seul point
    d'entree a utiliser depuis src/ui/ecran_journal.py : ne fait que choisir la fonction de mise
    en forme adaptee au type d'evenement, jamais de decision sur ce qui s'est produit (deja
    tranche par Combat)."""
    if isinstance(evenement, EvenementTour):
        return ligne_tour(evenement.numero)
    if isinstance(evenement, EvenementCarteJouee):
        return ligne_carte_jouee(evenement.carte, evenement.cible)
    assert isinstance(evenement, EvenementActionEnnemi)
    return ligne_evenement_ennemi(evenement.ennemi, evenement.cible, evenement.valeur, evenement.type_evenement)
