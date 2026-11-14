"""
Textes de l'ecran de combat PC (refonte-branchement.md 4) : mise en mots des faits fournis par le
gameplay (CombatNew.intentions, journal, statuts, cartes). Aucune regle de jeu, aucun pyglet :
testable sans fenetre (tests/test_textes_combat.py). Meme contenu que la version web
(web/bridge.py:_popup_evenement, web/app.js:texteEffetEnnemi / construireLigneJournal), mais en
mots : ni emoji ni symbole (epees, fleche de renvoi) qui dependent de la police de la machine.
Seuls le signe de multiplication et la fleche simple, presents dans les polices courantes, sont
gardes.
"""

from src.gameplay.carte_new import CarteNew
from src.gameplay.combat_new import CombatNew, Evenement, IntentionEffet, NatureEvenement
from src.gameplay.ennemi_new import CibleEffetEnnemi, EnnemiNew, NatureEffetEnnemi
from src.gameplay.module_new import ModuleNew
from src.gameplay.statut_new import Statut

# Couleurs partagees par les pastilles, les popups et le journal
COULEUR_DEGATS = (190, 40, 40)
COULEUR_BOUCLIER = (50, 110, 200)
COULEUR_INCENDIE = (215, 130, 40)
COULEUR_RENVOI = (170, 130, 220)
COULEUR_LEURRE = (90, 200, 210)
COULEUR_SOIN = (70, 200, 90)
COULEUR_TEXTE = (235, 235, 235)
COULEUR_NOM_CARTE = (235, 200, 60)
COULEUR_NOM_ENNEMI = (235, 110, 110)
COULEUR_NOM_MODULE = (120, 180, 255)
COULEUR_TOUR = (160, 160, 170)

COULEUR_PAR_STATUT = {
    Statut.BOUCLIER: COULEUR_BOUCLIER,
    Statut.INCENDIE: COULEUR_INCENDIE,
    Statut.RENVOI: COULEUR_RENVOI,
    Statut.LEURRE: COULEUR_LEURRE,
}
NOMS_STATUT = {
    Statut.BOUCLIER: "Bouclier",
    Statut.INCENDIE: "Incendie",
    Statut.RENVOI: "Renvoi",
    Statut.LEURRE: "Leurre",
}
# Statuts affiches en pastille a cote des PV, dans cet ordre (le bouclier a toujours sa pastille)
STATUTS_EN_PASTILLE = (Statut.INCENDIE, Statut.RENVOI, Statut.LEURRE)

COULEUR_PAR_NATURE_ENNEMI = {
    NatureEffetEnnemi.ATTAQUE: (255, 120, 120),
    NatureEffetEnnemi.BOUCLIER: (130, 180, 255),
    NatureEffetEnnemi.RENVOI: (200, 170, 245),
}
# Nom de chaque nature d'effet ennemi : version courte (dans la case) et complete (infobulle)
_NOMS_COURTS_NATURE_ENNEMI = {
    NatureEffetEnnemi.ATTAQUE: "Att.",
    NatureEffetEnnemi.BOUCLIER: "Bouclier",
    NatureEffetEnnemi.RENVOI: "Renvoi",
}
_NOMS_NATURE_ENNEMI = {**_NOMS_COURTS_NATURE_ENNEMI, NatureEffetEnnemi.ATTAQUE: "Attaque"}


def texte_intention_court(intention: IntentionEffet) -> str:
    """Dans la case de l'ennemi : nature abregee, valeur, "x2" si repete, "tous" pour une attaque
    de tous les modules."""
    effet = intention.effet
    repetitions = f"×{effet.repetitions}" if effet.repetitions > 1 else ""
    tous = " tous" if effet.cible == CibleEffetEnnemi.TOUS_MODULES else ""
    return f"{_NOMS_COURTS_NATURE_ENNEMI.get(effet.nature, '?')} {intention.valeur}{repetitions}{tous}"


def texte_intention(intention: IntentionEffet) -> str:
    """Dans l'infobulle de l'ennemi, une action par ligne : nature, valeur, repetitions, cible."""
    effet = intention.effet
    repetitions = f" ×{effet.repetitions}" if effet.repetitions > 1 else ""
    if effet.cible == CibleEffetEnnemi.TOUS_MODULES:
        cible = " → tous"
    elif effet.cible == CibleEffetEnnemi.ALLIE_AVANT_SINON_ARRIERE:
        cible = " → un allié"
    elif effet.cible == CibleEffetEnnemi.PROXIMITE:
        prevue = intention.cible_prevue
        cible = f" → {prevue.nom}" if isinstance(prevue, ModuleNew) else " → module le plus proche"
    else:
        cible = ""
    return f"{_NOMS_NATURE_ENNEMI.get(effet.nature, '?')} {intention.valeur}{repetitions}{cible}"


def lignes_statuts(entite: ModuleNew | EnnemiNew) -> list[str]:
    """Statuts actifs d'un module ou d'un ennemi, en clair, pour son infobulle."""
    lignes = []
    for statut in Statut:
        intensite = entite.statuts[statut]
        if intensite > 0:
            lignes.append(NOMS_STATUT[statut] if statut == Statut.LEURRE else f"{NOMS_STATUT[statut]} {intensite}")
    return lignes


def menaces_par_module(combat: CombatNew) -> dict[int, list[str]]:
    """Attaques prevues au prochain tour ennemi, par module vise (cle : id() du module), deja en
    texte (nom de l'ennemi, valeur, repetitions). Les modules vises sont decides par le gameplay
    (CombatNew.modules_vises)."""
    menaces: dict[int, list[str]] = {}
    if not combat.en_cours:
        return menaces
    for intention in combat.intentions():
        for effet in intention.effets:
            repetitions = f" ×{effet.effet.repetitions}" if effet.effet.repetitions > 1 else ""
            for module in combat.modules_vises(effet):
                menaces.setdefault(id(module), []).append(f"{intention.ennemi.nom} : Attaque {effet.valeur}{repetitions}")
    return menaces


# --- Cartes ---


def texte_munitions(carte: CarteNew) -> str:
    """Munitions "restantes/de depart", vide pour une carte illimitee."""
    if carte.munitions_base is None:
        return ""
    restantes = carte.munitions_restantes if carte.munitions_restantes is not None else carte.munitions_base
    return f"{restantes}/{carte.munitions_base}"


def lancements(carte: CarteNew) -> int:
    return carte.lancements_actuels if carte.lancements_actuels is not None else carte.lancements_base


def lignes_details_carte(carte: CarteNew, nom_module: str | None) -> list[str]:
    """Details d'une carte sous sa description : munitions, lancements, Persistante, module."""
    lignes = []
    munitions = texte_munitions(carte)
    if munitions:
        lignes.append(f"Munitions {munitions}")
    if lancements(carte) > 1:
        lignes.append(f"Lancée {lancements(carte)} fois")
    if carte.persistante:
        lignes.append("Persistante")
    if nom_module:
        lignes.append(f"Module : {nom_module}")
    return lignes


def texte_compteurs(combat: CombatNew) -> str:
    """Compteurs des piles (refonte-branchement.md 4.4) ; Hors service seulement si non vide."""
    deck = combat.deck
    morceaux = [f"Pioche {len(deck.pioche)}", f"Défausse {len(deck.defausse)}", f"Épuisées {len(deck.epuisees)}"]
    if deck.hors_service:
        morceaux.append(f"Hors service {len(deck.hors_service)}")
    return "\n".join([f"Tour {combat.tour}", *morceaux])


# --- Popups ---

_NATURES_AVEC_POPUP = (
    NatureEvenement.ATTAQUE, NatureEvenement.RENVOI, NatureEvenement.INCENDIE,
    NatureEvenement.STATUT_POSE, NatureEvenement.REPARATION,
)


def popup_evenement(evenement: Evenement) -> tuple[str, tuple[int, int, int]] | None:
    """Texte et couleur du popup d'une entree du journal, None si elle n'en donne pas."""
    if evenement.nature not in _NATURES_AVEC_POPUP or evenement.cible is None:
        return None
    if evenement.nature == NatureEvenement.STATUT_POSE:
        if evenement.statut == Statut.LEURRE:
            return "Leurre", COULEUR_LEURRE
        return f"+{evenement.valeur} {NOMS_STATUT[evenement.statut].lower()}", COULEUR_PAR_STATUT[evenement.statut]
    if evenement.nature == NatureEvenement.REPARATION:
        # Reparation d'un module deja plein : rien a montrer
        return (f"+{evenement.valeur}", COULEUR_SOIN) if evenement.valeur else None
    if not evenement.pv_perdus:
        # Aucun PV perdu : on dit ce qui a arrete l'attaque (leurre, renvoi, bouclier, ou plusieurs)
        morceaux = []
        if evenement.annules_leurre:
            morceaux.append("annulé")
        if evenement.renvoyes:
            morceaux.append(f"renvoi {evenement.renvoyes}")
        if evenement.absorbes_bouclier:
            morceaux.append(f"bloqué ({evenement.absorbes_bouclier})")
        if morceaux:
            return " · ".join(morceaux), COULEUR_RENVOI if evenement.renvoyes else COULEUR_BOUCLIER
    texte = f"-{evenement.pv_perdus}"
    if evenement.absorbes_bouclier:
        texte += f" (bouclier {evenement.absorbes_bouclier})"
    return texte, COULEUR_DEGATS


# --- Journal ---

Segment = tuple[str, tuple[int, int, int]]


def _nom(entite: object) -> Segment:
    if isinstance(entite, CarteNew):
        return entite.nom, COULEUR_NOM_CARTE
    if isinstance(entite, EnnemiNew):
        return entite.nom, COULEUR_NOM_ENNEMI
    return entite.nom, COULEUR_NOM_MODULE


def _detail_degats(evenement: Evenement) -> str:
    """Detail des degats recus : degats, part annulee, renvoyee, absorbee, PV perdus et restants."""
    morceaux = [f"{evenement.valeur} dégâts"]
    if evenement.annules_leurre:
        morceaux.append("annulés par le leurre")
    if evenement.renvoyes:
        morceaux.append(f"{evenement.renvoyes} renvoyés")
    if evenement.absorbes_bouclier:
        morceaux.append(f"{evenement.absorbes_bouclier} absorbés par le bouclier")
    if evenement.pv_perdus or not evenement.annules_leurre:
        morceaux.append(f"{evenement.pv_perdus} PV perdus ({evenement.pv_restants} restants)")
    return ", ".join(morceaux)


def ligne_journal(evenement: Evenement) -> list[Segment]:
    """Une entree du journal en segments (texte, couleur) ; vide si elle ne donne pas de ligne
    (CARTE_JOUEE : les effets de la carte donnent chacun la leur)."""

    def texte(contenu: str) -> Segment:
        return contenu, COULEUR_TEXTE

    nature = evenement.nature
    source = [_nom(evenement.source)] if evenement.source is not None else []
    cible = [_nom(evenement.cible)] if evenement.cible is not None else []
    if nature == NatureEvenement.DEBUT_TOUR:
        return [(f"--- Tour {evenement.valeur} ---", COULEUR_TOUR)]
    if nature == NatureEvenement.ATTAQUE:
        return [*source, texte(" → "), *cible, texte(f" : {_detail_degats(evenement)}")]
    if nature == NatureEvenement.RENVOI:
        return [texte("Renvoi → "), *cible, texte(f" : {_detail_degats(evenement)}")]
    if nature == NatureEvenement.INCENDIE:
        return [texte("Incendie sur "), *cible, texte(f" : {_detail_degats(evenement)}")]
    if nature == NatureEvenement.STATUT_POSE:
        valeur = "" if evenement.statut == Statut.LEURRE else f" {evenement.valeur}"
        debut = [*source, texte(" → ")] if source else []
        return [*debut, *cible, texte(f" : {NOMS_STATUT[evenement.statut].lower()}{valeur}")]
    if nature == NatureEvenement.REPARATION:
        return [*source, texte(" → "), *cible, texte(f" : +{evenement.valeur} PV ({evenement.pv_restants} restants)")]
    if nature == NatureEvenement.ELECTRICITE:
        return [*source, texte(f" : +{evenement.valeur} électricité")]
    if nature == NatureEvenement.PIOCHE:
        return [*source, texte(f" : {evenement.valeur} carte(s) piochée(s)")]
    if nature == NatureEvenement.REPETITION:
        return [*source, texte(f" : {evenement.valeur} carte(s) lancée(s) une fois de plus")]
    if nature in (NatureEvenement.MODULE_DETRUIT, NatureEvenement.ENNEMI_DETRUIT):
        return [*cible, texte(" détruit")]
    if nature == NatureEvenement.CARTES_HORS_SERVICE:
        return [*cible, texte(f" : {evenement.valeur} carte(s) hors service")]
    if nature == NatureEvenement.VICTOIRE:
        return [("Victoire", COULEUR_TOUR)]
    if nature == NatureEvenement.DEFAITE:
        return [("Défaite", COULEUR_TOUR)]
    return []
