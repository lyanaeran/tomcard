"""
Historique des evenements d'un combat (specs.md 8.1) : quelles cartes ont ete jouees, quelles
actions ennemies ont ete resolues, et les marqueurs de tour. Alimente uniquement par Combat
(src/gameplay/combat.py : jouer_carte, finir_tour_joueur) - src/ui/journal_combat.py (PC) et
web/app.js (web) n'en font que la mise en forme (phrases/couleurs), jamais le calcul de ce qui
s'est produit ni quand l'enregistrer (cf. CLAUDE.md, gameplay commun aux deux interfaces).
"""

from dataclasses import dataclass

from src.gameplay.carte import Carte
from src.gameplay.ennemi import Ennemi
from src.gameplay.module import Module


@dataclass(frozen=True)
class EvenementCarteJouee:
    """Une carte du joueur a ete jouee avec effet (specs.md 8.1). `cible` est l'objet vise par
    un clic (Module ou Ennemi) ; None pour une carte sans clic de ciblage precis
    (carte.CIBLES_SANS_CLIC) - sa cible reelle est alors tout un camp, pas un objet en
    particulier (cf. carte.cible pour retrouver lequel)."""

    carte: Carte
    cible: Module | Ennemi | None


@dataclass(frozen=True)
class EvenementActionEnnemi:
    """Une action ennemie resolue au tour ennemi (specs.md 13) : attaque (type_evenement=
    "degats") ou pose de buff/bouclier (type_evenement="bouclier"), memes champs que les
    evenements renvoyes par Combat.finir_tour_joueur. `cible` peut etre l'ennemi lui-meme
    (auto-ciblage : ex. Petit Jean se protege, ou un renvoi de Bouclier miroir sur son propre
    attaquant)."""

    ennemi: Ennemi
    cible: Module | Ennemi
    valeur: int
    type_evenement: str


@dataclass(frozen=True)
class EvenementTour:
    """Marqueur de debut de tour joueur (specs.md 8.1) - numero affiche a l'utilisateur (1 des
    la creation du combat, avant tout tour ennemi)."""

    numero: int


Evenement = EvenementCarteJouee | EvenementActionEnnemi | EvenementTour
