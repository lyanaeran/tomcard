"""
Point d'entree du jeu Space Fight (PC) : selection du profil joueur (specs.md 10.3), puis l'accueil
de ce joueur (partie en cours ou nouvelle partie), qui enchaine desormais reellement sur le reste du
parcours (specs.md 2.4) : choix de module (Niveau 1) -> choix du prochain niveau -> combat (Prime ou
Boss), Station service, une Aventure ("Trois lunes", "Asteroides" ou "Police", specs.md 2.5, tiree
au hasard) ou Planete commerciale (ecran generique, contenu pas encore prepare) -> retour au choix
du prochain niveau, ou victoire finale (Boss vaincu) -> fin de partie.

Chaque ecran est une fenetre pyglet independante ; les transitions se font en fermant la fenetre
courante et en ouvrant la suivante, verifiees a intervalle regulier via pyglet.clock (pas
d'evenement dedie pour "l'utilisateur a fait un choix" dans ces ecrans, cf. leurs attributs
`profil_choisi`/`action`/`module_choisi`/`type_choisi`/`termine`).

Limites connues (specs.md 2.4) : Planete commerciale n'a pas encore de contenu propre (specs.md
9.1) - l'ecran generique (EcranEtapePlaceholder) la represente, sans autre effet que d'avancer au
niveau suivant. Les 3 aventures specifiees sont implementees (Trois lunes, Asteroides, Police -
specs.md 2.5), tirees au hasard a chaque TypeEtape.AVENTURE (tirer_type_aventure). La flotte
ennemie d'un combat Prime/Boss est toujours tiree au hasard (combat_depuis_partie), sans tenir
compte des tailles/du nombre d'ennemis attendus au niveau courant (specs.md 2.3/3.2).
"""

import random

import pyglet

from src.gameplay.combat import Combat, EtatCombat
from src.gameplay.donnees import charger_cartes, charger_modules
from src.gameplay.parcours import (
    TypeAventure,
    TypeEtape,
    aleatoire_pour_niveau,
    est_niveau_boss,
    modules_equipables,
    tirer_candidats_module,
    tirer_candidats_recompense,
    tirer_propositions_niveau,
    tirer_type_aventure,
)
from src.gameplay.partie import (
    Partie,
    Profil,
    abandonner_partie,
    ajouter_carte,
    avancer_niveau,
    combat_aventure_asteroides,
    combat_depuis_partie,
    deck_de_la_partie,
    equiper_module,
    gagner_argent_combat,
    id_de_carte,
    marquer_terminee,
    nouvelle_partie,
    partie_en_cours,
    sauvegarder_partie,
    specs_utilisees_partie,
    synchroniser_vaisseau_depuis_combat,
)
from src.ui.ecran_accueil_joueur import EcranAccueilJoueur
from src.ui.ecran_aventure_asteroides import EcranAventureAsteroides
from src.ui.ecran_aventure_police import EcranAventurePolice
from src.ui.ecran_aventure_trois_lunes import EcranAventureTroisLunes
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

# Types de proposition qui ouvrent un combat (specs.md 2.4) - les autres (Station service, ou
# Aventure/Planete commerciale via EcranEtapePlaceholder) ont chacun leur propre branchement dans
# _ouvrir_choix_niveau.
TYPES_COMBAT = (TypeEtape.PRIME, TypeEtape.BOSS)


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
        # Reprend l'etape courante a partir de ce qui est deja connu (niveau + vaisseau) plutot
        # que d'une "etape courante" dediee, pas encore ajoutee a la sauvegarde (decision
        # utilisateur) : le Niveau 1 sans 2e module equipe reprend au choix de module, sinon on
        # retire les propositions du niveau courant (deterministe, cf. aleatoire_pour_niveau).
        if partie.niveau == 1 and partie.vaisseau["avant_gauche"] is None:
            _ouvrir_choix_module(profil, partie)
        else:
            _ouvrir_choix_niveau(profil, partie)
    elif action == "abandonner":
        abandonner_partie(profil.id, partie)
        _ouvrir_accueil(profil)
    elif action == "voir_deck":
        _ouvrir_voir_deck(profil, partie)
    elif action == "nouvelle_partie":
        nouvelle = nouvelle_partie()
        sauvegarder_partie(profil.id, nouvelle)
        _ouvrir_choix_module(profil, nouvelle)


def _ouvrir_voir_deck(profil: Profil, partie: Partie) -> None:
    fenetre = EcranDeck(deck_de_la_partie(partie))

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        _ouvrir_accueil(profil)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_choix_module(profil: Profil, partie: Partie) -> None:
    pool = modules_equipables(charger_modules())
    candidats = tirer_candidats_module(pool, random.Random(partie.graine))
    fenetre = EcranChoixModule(candidats, partie)

    def verifier(_dt: float) -> None:
        if fenetre.module_choisi is None:
            return
        pyglet.clock.unschedule(verifier)
        spec = fenetre.module_choisi
        fenetre.close()
        equiper_module(partie, spec)
        avancer_niveau(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_choix_niveau(profil: Profil, partie: Partie) -> None:
    aleatoire = aleatoire_pour_niveau(partie.graine, partie.niveau)
    propositions = tirer_propositions_niveau(partie.niveau, aleatoire)
    fenetre = EcranChoixNiveau(partie, propositions)

    def verifier(_dt: float) -> None:
        if fenetre.type_choisi is None:
            return
        pyglet.clock.unschedule(verifier)
        type_choisi = fenetre.type_choisi
        fenetre.close()
        if type_choisi in TYPES_COMBAT:
            _ouvrir_combat(profil, partie)
        elif type_choisi == TypeEtape.STATION_SERVICE:
            _ouvrir_station_service(profil, partie)
        elif type_choisi == TypeEtape.AVENTURE:
            # Trois aventures implementees (specs.md 2.5), tirage uniforme non deterministe
            # (comme la recompense de fin de combat).
            type_aventure = tirer_type_aventure(random.Random())
            if type_aventure == TypeAventure.TROIS_LUNES:
                _ouvrir_aventure_trois_lunes(profil, partie)
            elif type_aventure == TypeAventure.ASTEROIDES:
                _ouvrir_aventure_asteroides(profil, partie)
            else:
                _ouvrir_aventure_police(profil, partie)
        else:
            # Planete commerciale : contenu pas encore prepare (specs.md 2.4, 9.1).
            _ouvrir_etape_placeholder(profil, partie, type_choisi)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_station_service(profil: Profil, partie: Partie) -> None:
    fenetre = EcranStationService(partie)

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        avancer_niveau(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_aventure_trois_lunes(profil: Profil, partie: Partie) -> None:
    fenetre = EcranAventureTroisLunes(partie)

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        avancer_niveau(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_aventure_asteroides(profil: Profil, partie: Partie) -> None:
    fenetre = EcranAventureAsteroides(partie)

    def verifier(_dt: float) -> None:
        if fenetre.combat_demande:
            pyglet.clock.unschedule(verifier)
            fenetre.close()
            # Choix "Affronter les pirates" (specs.md 2.5) : delegue au meme pipeline qu'un
            # combat Prime normal (_ouvrir_combat/_ouvrir_fin_combat), juste avec une flotte
            # scriptee plutot que le tirage standard lie au niveau.
            _ouvrir_combat(profil, partie, combat_aventure_asteroides(partie))
            return
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        avancer_niveau(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_aventure_police(profil: Profil, partie: Partie) -> None:
    fenetre = EcranAventurePolice(partie)

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        avancer_niveau(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_etape_placeholder(profil: Profil, partie: Partie, type_etape: TypeEtape) -> None:
    fenetre = EcranEtapePlaceholder(type_etape, partie)

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        avancer_niveau(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_combat(profil: Profil, partie: Partie, combat: Combat | None = None) -> None:
    """`combat` : deja construit par l'appelant pour un combat scripte (Aventure Asteroides,
    specs.md 2.5, combat_aventure_asteroides) ; None pour un Prime/Boss normal
    (combat_depuis_partie, tirage standard lie au niveau)."""
    combat = combat or combat_depuis_partie(partie)
    fenetre = FenetreCombat(combat, partie)

    def verifier(_dt: float) -> None:
        if fenetre.quitte_demandee:
            pyglet.clock.unschedule(verifier)
            fenetre.close()
            # Bouton "Quitter" (specs.md 8.1) : ferme le combat en cours sans le synchroniser ni
            # le sauvegarder (decision utilisateur) - la partie reste EN_COURS telle qu'elle etait
            # avant ce combat, qui repartira de zero (nouveau tirage de flotte) au prochain
            # "Continuer" depuis l'accueil du joueur.
            _ouvrir_selection_joueur()
            return
        if combat.etat == EtatCombat.EN_COURS:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        # Reporte les degats subis pendant le combat sur la partie sauvegardee (specs.md 2.2/3.4 :
        # persistance des PV entre deux combats), avant tout enchainement/sauvegarde ulterieur.
        synchroniser_vaisseau_depuis_combat(partie, combat.joueur.vaisseau)
        if combat.etat == EtatCombat.VICTOIRE:
            gagner_argent_combat(partie, combat)  # specs.md 2.1 : Argent par ennemi tue
        _ouvrir_fin_combat(profil, partie, combat)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_fin_combat(profil: Profil, partie: Partie, combat: Combat) -> None:
    victoire = combat.etat == EtatCombat.VICTOIRE
    cartes = charger_cartes()
    candidats = []
    if victoire:
        specs_par_id = {spec.id: spec for spec in charger_modules()}
        candidats = tirer_candidats_recompense(specs_utilisees_partie(partie, specs_par_id), cartes, random.Random())
    fenetre = EcranFinCombat(victoire, partie, candidats)

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        if not victoire:
            abandonner_partie(profil.id, partie)  # meme statut TERMINEE qu'un abandon (specs.md 10.3)
            _ouvrir_accueil(profil)
            return
        if fenetre.carte_choisie is not None:
            ajouter_carte(partie, id_de_carte(fenetre.carte_choisie, cartes))
        if est_niveau_boss(partie.niveau):
            # Le run s'arrete reellement au Niveau 10 dans l'etat actuel (decision utilisateur,
            # specs.md 2).
            _ouvrir_victoire_finale(profil, partie)
        else:
            avancer_niveau(partie)
            sauvegarder_partie(profil.id, partie)
            _ouvrir_choix_niveau(profil, partie)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


def _ouvrir_victoire_finale(profil: Profil, partie: Partie) -> None:
    fenetre = EcranVictoireFinale(deck_de_la_partie(partie))

    def verifier(_dt: float) -> None:
        if not fenetre.termine:
            return
        pyglet.clock.unschedule(verifier)
        fenetre.close()
        marquer_terminee(partie)
        sauvegarder_partie(profil.id, partie)
        _ouvrir_accueil(profil)

    pyglet.clock.schedule_interval(verifier, INTERVALLE_VERIFICATION)


if __name__ == "__main__":
    main()
