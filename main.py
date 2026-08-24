"""
Point d'entree du jeu Space Fight (PC) : selection du profil joueur (specs.md 10.3), puis l'accueil
de ce joueur (partie en cours ou nouvelle partie), qui renvoie vers les ecrans du parcours deja
construits (choix de module, combat, deck).

Chaque ecran est une fenetre pyglet independante ; les transitions se font en fermant la fenetre
courante et en ouvrant la suivante, verifiees a intervalle regulier via pyglet.clock (pas
d'evenement dedie pour "l'utilisateur a fait un choix" dans ces ecrans, cf. leurs attributs
`profil_choisi`/`action`/`module_choisi`).
"""

import random

import pyglet

from src.gameplay.donnees import charger_modules
from src.gameplay.partie import (
    Partie,
    Profil,
    abandonner_partie,
    combat_depuis_partie,
    deck_de_la_partie,
    nouvelle_partie,
    partie_en_cours,
    sauvegarder_partie,
)
from src.gameplay.parcours import modules_equipables, tirer_candidats_module
from src.ui.ecran_accueil_joueur import EcranAccueilJoueur
from src.ui.ecran_choix_module import EcranChoixModule
from src.ui.ecran_deck import EcranDeck
from src.ui.ecran_selection_joueur import EcranSelectionJoueur
from src.ui.fenetre import FenetreCombat

INTERVALLE_VERIFICATION = 1 / 30


def main() -> None:
    _ouvrir_selection_joueur()
    pyglet.app.run()


def _ouvrir_selection_joueur() -> None:
    fenetre = EcranSelectionJoueur()

    def verifier(_dt: float) -> None:
        if fenetre.profil_choisi is None:
            return
        pyglet.clock.unschedule(verifier)
        profil = fenetre.profil_choisi
        fenetre.close()
        _ouvrir_accueil(profil)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_accueil(profil: Profil) -> None:
    partie = partie_en_cours(profil.id)
    fenetre = EcranAccueilJoueur(profil, partie)

    def verifier(_dt: float) -> None:
        if fenetre.action is None:
            return
        pyglet.clock.unschedule(verifier)
        action = fenetre.action
        fenetre.close()
        _traiter_action(profil, partie, action)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _traiter_action(profil: Profil, partie: Partie | None, action: str) -> None:
    if action == "continuer":
        # Approximation temporaire (decision utilisateur) : reprend le vaisseau/deck reels du
        # joueur, mais tire une flotte ennemie au hasard, faute d'orchestration du parcours
        # (specs.md 2.3/10.3) capable de determiner precisement le prochain combat.
        FenetreCombat(combat_depuis_partie(partie))
    elif action == "abandonner":
        abandonner_partie(profil.id, partie)
        _ouvrir_accueil(profil)
    elif action == "voir_deck":
        EcranDeck(deck_de_la_partie(partie))
    elif action == "nouvelle_partie":
        nouvelle = nouvelle_partie()
        sauvegarder_partie(profil.id, nouvelle)
        pool = modules_equipables(charger_modules())
        candidats = tirer_candidats_module(pool, random.Random(nouvelle.graine))
        EcranChoixModule(candidats)


if __name__ == "__main__":
    main()
