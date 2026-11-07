"""
Point d'entree du jeu Space Fight (PC) : selection du profil joueur (specs.md 10.3), puis accueil
de ce joueur (partie en cours ou nouvelle partie), puis le parcours (specs.md 2.4).

Ce fichier ne fait qu'ouvrir et fermer des fenetres pyglet : quel ecran vient ensuite, et les
regles appliquees a chaque transition (avancee de niveau, Argent, fin de partie...), sont decides
par src/gameplay/deroulement.py, partage avec le web et la simulation. Seule la sauvegarde de la
partie apres chaque transition (fichier, cote PC) reste ici.

Chaque ecran est une fenetre independante ; une transition ferme la fenetre courante et ouvre la
suivante, detectee a intervalle regulier via pyglet.clock (attributs `profil_choisi`/`action`/
`module_choisi`/`type_choisi`/`termine` des ecrans). Le jeu ne quitte que si aucune fenetre n'est
ouverte au tick suivant une fermeture (cf. _on_window_close).
"""

import random

import pyglet

# Ecrans HiDPI (Retina) : le mode par defaut "platform" double la taille logique de la fenetre sur
# macOS alors que tout le dessin est en coordonnees 1280x800, d'ou un jeu cantonne au quart en bas
# a gauche. "stretch" garde 1280x800 comme taille logique et l'etire sur tout le framebuffer.
# Doit etre regle avant la creation de la premiere fenetre.
pyglet.options.dpi_scaling = "stretch"

from src.gameplay import deroulement
from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.deroulement import Ecran
from src.gameplay.donnees import SpecModule
from src.gameplay.parcours import TypeEtape
from src.gameplay.partie import (
    Partie,
    Profil,
    abandonner_partie,
    combat_aventure_asteroides,
    combat_depuis_partie,
    deck_de_la_partie,
    nouvelle_partie,
    partie_en_cours,
    sauvegarder_partie,
)
from src.ui.ecran_accueil_joueur import EcranAccueilJoueur
from src.ui.ecran_aventure_asteroides import EcranAventureAsteroides
from src.ui.ecran_aventure_police import EcranAventurePolice
from src.ui.ecran_aventure_trois_lunes import EcranAventureTroisLunes
from src.ui.ecran_choix_carte_module import EcranChoixCarteModule
from src.ui.ecran_choix_module import EcranChoixModule
from src.ui.ecran_choix_niveau import EcranChoixNiveau
from src.ui.ecran_deck import EcranDeck
from src.ui.ecran_etape_placeholder import EcranEtapePlaceholder
from src.ui.ecran_fin_combat import EcranFinCombat
from src.ui.ecran_selection_joueur import EcranSelectionJoueur
from src.ui.ecran_station_service import EcranStationService
from src.ui.ecran_victoire_finale import EcranVictoireFinale
from src.ui.fenetre import FenetreCombat

INTERVALLE_VERIFICATION = 1 / 30


def main() -> None:
    pyglet.app.event_loop.push_handlers(on_window_close=_on_window_close)
    _ouvrir_selection_joueur()
    pyglet.app.run()


def _on_window_close(_fenetre: pyglet.window.Window) -> bool:
    """Remplace la sortie immediate de pyglet quand plus aucune fenetre n'est ouverte."""
    # Par defaut, pyglet quitte des que la derniere fenetre se ferme : or chaque transition ferme
    # l'ecran courant AVANT d'ouvrir le suivant, ce qui arretait le jeu apres la selection du
    # joueur (constate sur macOS). On reporte donc la verification au tick suivant, une fois le
    # nouvel ecran ouvert ; fermer la derniere fenetre (bouton rouge) quitte toujours le jeu.
    pyglet.clock.schedule_once(_quitter_si_plus_aucune_fenetre, 0)
    return pyglet.event.EVENT_HANDLED


def _quitter_si_plus_aucune_fenetre(_dt: float) -> None:
    if not pyglet.app.windows:
        pyglet.app.exit()


def _attendre(fenetre: pyglet.window.Window, est_resolue, suite) -> None:
    """Appelle suite() une fois est_resolue() vraie, apres avoir ferme la fenetre."""

    def verifier(_dt: float) -> None:
        if not est_resolue():
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        suite()

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _aller_a(ecran: Ecran, profil: Profil, partie: Partie) -> None:
    """Sauvegarde la partie puis ouvre l'ecran decide par src/gameplay/deroulement.py."""
    sauvegarder_partie(profil.id, partie)
    ouvertures = {
        Ecran.ACCUEIL: lambda: _ouvrir_accueil(profil),
        Ecran.CHOIX_MODULE: lambda: _ouvrir_choix_module(profil, partie),
        Ecran.CHOIX_NIVEAU: lambda: _ouvrir_choix_niveau(profil, partie),
        Ecran.COMBAT: lambda: _ouvrir_combat(profil, partie),
        Ecran.STATION_SERVICE: lambda: _ouvrir_etape(EcranStationService(partie), profil, partie),
        Ecran.AVENTURE_TROIS_LUNES: lambda: _ouvrir_etape(EcranAventureTroisLunes(partie), profil, partie),
        Ecran.AVENTURE_ASTEROIDES: lambda: _ouvrir_aventure_asteroides(profil, partie),
        Ecran.AVENTURE_POLICE: lambda: _ouvrir_etape(EcranAventurePolice(partie), profil, partie),
        Ecran.PLANETE_COMMERCIALE: lambda: _ouvrir_etape(
            EcranEtapePlaceholder(TypeEtape.PLANETE_COMMERCIALE, partie), profil, partie
        ),
        Ecran.VICTOIRE_FINALE: lambda: _ouvrir_victoire_finale(profil, partie),
    }
    ouvertures[ecran]()


def _ouvrir_selection_joueur() -> None:
    fenetre = EcranSelectionJoueur()
    _attendre(fenetre, lambda: fenetre.profil_choisi is not None, lambda: _ouvrir_accueil(fenetre.profil_choisi))


def _ouvrir_accueil(profil: Profil) -> None:
    partie = partie_en_cours(profil.id)
    fenetre = EcranAccueilJoueur(profil, partie)
    _attendre(fenetre, lambda: fenetre.action is not None, lambda: _traiter_action(profil, partie, fenetre.action))


def _traiter_action(profil: Profil, partie: Partie | None, action: str) -> None:
    if action == "continuer":
        _aller_a(deroulement.ecran_de_reprise(partie), profil, partie)
    elif action == "abandonner":
        abandonner_partie(profil.id, partie)
        _ouvrir_accueil(profil)
    elif action == "voir_deck":
        fenetre = EcranDeck(deck_de_la_partie(partie))
        _attendre(fenetre, lambda: fenetre.termine, lambda: _ouvrir_accueil(profil))
    elif action == "nouvelle_partie":
        _aller_a(Ecran.CHOIX_MODULE, profil, nouvelle_partie())


def _ouvrir_choix_module(profil: Profil, partie: Partie) -> None:
    fenetre = EcranChoixModule(deroulement.candidats_choix_module(partie), partie)
    _attendre(
        fenetre,
        lambda: fenetre.module_choisi is not None,
        lambda: _ouvrir_choix_carte_module(profil, partie, fenetre.module_choisi),
    )


def _ouvrir_choix_carte_module(profil: Profil, partie: Partie, spec: SpecModule) -> None:
    """Cartes proposees pour le module qui vient d'etre equipe ; ecran saute si rien a proposer."""
    candidats = deroulement.choisir_module(partie, spec, random.Random())
    if not candidats:
        _aller_a(deroulement.resoudre_carte_module(partie, None), profil, partie)
        return
    fenetre = EcranChoixCarteModule(spec.nom, candidats, partie)

    def suite() -> None:
        id_carte = fenetre.carte_choisie.id if fenetre.carte_choisie is not None else None
        _aller_a(deroulement.resoudre_carte_module(partie, id_carte), profil, partie)

    _attendre(fenetre, lambda: fenetre.termine, suite)


def _ouvrir_choix_niveau(profil: Profil, partie: Partie) -> None:
    fenetre = EcranChoixNiveau(partie, deroulement.propositions_niveau(partie))
    _attendre(
        fenetre,
        lambda: fenetre.type_choisi is not None,
        lambda: _aller_a(deroulement.ecran_pour_etape(fenetre.type_choisi, random.Random()), profil, partie),
    )


def _ouvrir_etape(fenetre: pyglet.window.Window, profil: Profil, partie: Partie) -> None:
    """Etape hors combat (Station service, Trois lunes, Police, Planete commerciale) : l'ecran
    applique ses actions a la partie, puis "termine" passe au niveau suivant."""
    _attendre(fenetre, lambda: fenetre.termine, lambda: _aller_a(deroulement.terminer_etape(partie), profil, partie))


def _ouvrir_aventure_asteroides(profil: Profil, partie: Partie) -> None:
    fenetre = EcranAventureAsteroides(partie)

    def suite() -> None:
        if fenetre.combat_demande:
            # Choix "Affronter les pirates" (specs.md 2.5) : combat a flotte scriptee, puis meme
            # fin de combat qu'un Prime.
            _ouvrir_combat(profil, partie, combat_aventure_asteroides(partie))
        else:
            _aller_a(deroulement.terminer_etape(partie), profil, partie)

    _attendre(fenetre, lambda: fenetre.combat_demande or fenetre.termine, suite)


def _ouvrir_combat(profil: Profil, partie: Partie, combat: Combat | None = None) -> None:
    """`combat` : deja construit pour un combat scripte (Aventure Asteroides) ; None pour un
    Prime/Boss normal (combat_depuis_partie)."""
    combat = combat or combat_depuis_partie(partie)
    fenetre = FenetreCombat(combat, partie)

    def suite() -> None:
        if fenetre.quitte_demandee:
            # Bouton "Quitter" (specs.md 8.1) : ferme le combat sans le synchroniser ni le
            # sauvegarder (decision utilisateur), il repartira de zero au prochain "Continuer".
            _ouvrir_selection_joueur()
            return
        candidats = deroulement.conclure_combat(partie, combat, random.Random())
        _ouvrir_fin_combat(profil, partie, combat.etat == EtatCombat.VICTOIRE, candidats)

    _attendre(fenetre, lambda: fenetre.quitte_demandee or combat.etat != EtatCombat.EN_COURS, suite)


def _ouvrir_fin_combat(profil: Profil, partie: Partie, victoire: bool, candidats: list) -> None:
    fenetre = EcranFinCombat(victoire, partie, candidats)

    def suite() -> None:
        id_carte = fenetre.carte_choisie.id if fenetre.carte_choisie is not None else None
        _aller_a(deroulement.resoudre_fin_combat(partie, victoire, id_carte), profil, partie)

    _attendre(fenetre, lambda: fenetre.termine, suite)


def _ouvrir_victoire_finale(profil: Profil, partie: Partie) -> None:
    fenetre = EcranVictoireFinale(deck_de_la_partie(partie))
    _attendre(
        fenetre, lambda: fenetre.termine, lambda: _aller_a(deroulement.terminer_victoire_finale(partie), profil, partie)
    )


if __name__ == "__main__":
    main()
