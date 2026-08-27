"""
Ecran Station service ("garage") du parcours (specs.md 2.2) : repare/ameliore/met a jour/deplace
les modules equipes d'une partie sauvegardee. Fenetre pyglet independante comme les autres ecrans
du parcours, mute directement `partie.vaisseau`/`partie.argent` (src/gameplay/partie.py) - c'est a
l'appelant de sauvegarder la partie une fois l'ecran ferme ("J'ai termine", specs.md 2.4 etape 8).

Chaque action coute COUT_ACTION_STATION_SERVICE d'Argent (specs.md 2.1/2.2). Fond de combat
reutilise en placeholder (decision utilisateur), a remplacer par un fond dedie.
"""

import pyglet
from pyglet import shapes

from src.gameplay.donnees import RACINE, charger_modules, image_case_module
from src.gameplay.partie import (
    COUT_ACTION_STATION_SERVICE,
    PV_AMELIORATION,
    EtatModule,
    Partie,
    ameliorer_module,
    deplacer_module,
    mettre_a_jour_module,
    reparer_module,
)
from src.ui.animation import AnimationPopup
from src.ui.fenetre import (
    COULEUR_OMBRE_POPUP,
    COULEUR_POPUP_DEGATS,
    COULEUR_POPUP_SOIN,
    DECALAGE_OMBRE_POPUP,
    FOND_IMAGE,
    GROUPE_SUPERPOSITION,
    HAUTEUR_FENETRE,
    LARGEUR_FENETRE,
    TAILLE_POLICE_POPUP,
    _sprite_ajuste,
    _sprite_etire,
)

COULEUR_TEXTE = (255, 255, 255)
COULEUR_SOUS_TITRE = (200, 200, 205)
COULEUR_FOND_CARTE = (20, 24, 34)
COULEUR_CONTOUR_CARTE = (90, 110, 150)
COULEUR_CONTOUR_SELECTIONNEE = (255, 255, 255)
COULEUR_FOND_VIDE = (15, 17, 24)
COULEUR_CONTOUR_VIDE = (60, 65, 80)
COULEUR_NIVEAU_MAJ = (255, 220, 120)
COULEUR_BOUTON = (60, 90, 160)
COULEUR_BOUTON_SURVOLE = (90, 130, 210)
COULEUR_BOUTON_ARME = (210, 160, 40)
COULEUR_BOUTON_TERMINE = (70, 190, 90)
COULEUR_BOUTON_TERMINE_SURVOLE = (100, 210, 115)
OPACITE_FOND = 190

# Meme ordre d'affichage que src/ui/ecran_accueil_joueur.py (specs.md 3.1/5).
POSITIONS_AFFICHEES = (
    ("base", "Principal"),
    ("avant_gauche", "Avant gauche"),
    ("avant_droite", "Avant droite"),
    ("arriere_gauche", "Arriere gauche"),
    ("arriere_droite", "Arriere droite"),
)
# Deplacer ne s'applique jamais au module principal (specs.md 2.2).
POSITIONS_DEPLACABLES = tuple(position for position, _libelle in POSITIONS_AFFICHEES if position != "base")

LARGEUR_CARTE_MODULE = 200
HAUTEUR_CARTE_MODULE = 240
IMAGE_TAILLE = 110
ESPACEMENT_CARTE = 24
Y_HAUT_GRILLE = HAUTEUR_FENETRE - 140

LARGEUR_ACTION = 130
HAUTEUR_ACTION = 135
ESPACEMENT_ACTION = 24
Y_ACTIONS = 150
MARGE_ICONE_ACTION = 8

LARGEUR_BOUTON_TERMINE = 220
HAUTEUR_BOUTON_TERMINE = 46
Y_BOUTON_TERMINE = 40

# Icones avec cadre/nom incruste (assets/station_service/avec_texte/) - decision utilisateur :
# cet ecran garde son ancienne grille d'icones seules (pas la ligne image+texte des Aventures/
# Choix du prochain niveau/specs.md 2.5), donc les versions sans texte de assets/station_service/
# (reutilisees telles quelles par les Aventures Trois lunes/Police) ne conviennent plus ici sans
# ajouter un texte redondant - anciennes icones restaurees depuis l'historique git plutot que
# supprimees, pour ce seul ecran.
_DOSSIER_ICONES = RACINE / "assets" / "station_service" / "avec_texte"

# (identifiant, libelle, chemin de l'icone) - ordre d'affichage des 4 actions (specs.md 2.2).
ACTIONS = (
    ("reparer", "Reparer", str(_DOSSIER_ICONES / "reparer.png")),
    ("ameliorer", "Ameliorer", str(_DOSSIER_ICONES / "ameliorer.png")),
    ("mettre_a_jour", "Mettre a jour", str(_DOSSIER_ICONES / "mettre_a_jour.png")),
    ("deplacer", "Deplacer", str(_DOSSIER_ICONES / "deplacer.png")),
)

APPLICATEURS_ACTION = {
    "reparer": reparer_module,
    "ameliorer": ameliorer_module,
    "mettre_a_jour": mettre_a_jour_module,
}


def _point_dans_rectangle(px: float, py: float, x: float, y: float, largeur: float, hauteur: float) -> bool:
    return x <= px <= x + largeur and y <= py <= y + hauteur


class EcranStationService(pyglet.window.Window):
    """Ecran Station service : selectionner un module puis une action, ou Deplacer (2 clics :
    module source, puis emplacement destination). `partie` est mutee directement a chaque action -
    "J'ai termine" (`self.termine`) signale a l'appelant qu'il peut la sauvegarder et enchainer."""

    def __init__(self, partie: Partie):
        super().__init__(width=LARGEUR_FENETRE, height=HAUTEUR_FENETRE, caption="Space Fight")
        self.partie = partie
        self.specs_par_id = {spec.id: spec for spec in charger_modules()}
        self.position_selectionnee: str | None = None
        # True = Deplacer arme (module source deja choisi), en attente d'un clic de destination.
        self.mode_deplacement: bool = False
        self.index_module_survole: int | None = None
        self.index_action_survolee: int | None = None
        self.bouton_termine_survole: bool = False
        self.termine: bool = False
        # Popup +N/Niveau N affiche 2 secondes sur la carte du module apres Reparer/Ameliorer/
        # Mettre a jour, meme mecanisme que les popups de degats/soin du combat (specs.md 2.2 :
        # feedback visuel explicite demande par l'utilisateur pour comprendre l'effet applique).
        self.popups: list[tuple[AnimationPopup, str, tuple[int, int, int], float, float]] = []
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)

    def update(self, dt: float) -> None:
        """Fait avancer les popups en cours (appele a chaque frame)."""
        for animation, _texte, _couleur, _x, _y in self.popups:
            animation.mettre_a_jour(dt)
        self.popups = [popup for popup in self.popups if popup[0].est_active()]

    def on_draw(self) -> None:
        self.clear()
        lot = pyglet.graphics.Batch()
        elements = self._dessiner(lot)
        lot.draw()
        del elements

    def _dessiner(self, lot: pyglet.graphics.Batch) -> list:
        elements = [_sprite_etire(FOND_IMAGE, 0, 0, LARGEUR_FENETRE, HAUTEUR_FENETRE, lot)]
        elements.append(
            pyglet.text.Label(
                f"Station service - Niveau {self.partie.niveau} - {self.partie.argent} €",
                x=LARGEUR_FENETRE / 2,
                y=HAUTEUR_FENETRE - 40,
                anchor_x="center",
                anchor_y="center",
                font_size=26,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        )
        for index, (position, libelle) in enumerate(POSITIONS_AFFICHEES):
            elements.extend(self._dessiner_module(index, position, libelle, self.partie.vaisseau[position], lot))
        for index, (identifiant, libelle, chemin_icone) in enumerate(ACTIONS):
            elements.extend(self._dessiner_action(index, identifiant, libelle, chemin_icone, lot))
        elements.extend(self._dessiner_instruction(lot))
        elements.extend(self._dessiner_bouton_termine(lot))
        elements.extend(self._dessiner_popups(lot))
        return elements

    def _dessiner_popups(self, lot: pyglet.graphics.Batch) -> list:
        """Dessine chaque popup encore actif (meme rendu ombre+texte que le combat, cf.
        FenetreCombat._dessiner_popups)."""
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

    def _instruction(self) -> str:
        if self.mode_deplacement:
            return "Cliquez l'emplacement de destination (ou recliquez le module pour annuler)."
        if self.position_selectionnee is None:
            return "Selectionnez un module, puis une action."
        return "Selectionnez une action pour ce module."

    def _dessiner_instruction(self, lot: pyglet.graphics.Batch) -> list:
        return [
            pyglet.text.Label(
                self._instruction(),
                x=LARGEUR_FENETRE / 2,
                y=Y_ACTIONS + HAUTEUR_ACTION + 30,
                anchor_x="center",
                anchor_y="center",
                font_size=16,
                color=(*COULEUR_TEXTE, 255),
                batch=lot,
            )
        ]

    def _rect_module(self, index: int) -> tuple[float, float, float, float]:
        total = len(POSITIONS_AFFICHEES)
        largeur_totale = total * LARGEUR_CARTE_MODULE + (total - 1) * ESPACEMENT_CARTE
        x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
        x = x_depart + index * (LARGEUR_CARTE_MODULE + ESPACEMENT_CARTE)
        return x, Y_HAUT_GRILLE - HAUTEUR_CARTE_MODULE, LARGEUR_CARTE_MODULE, HAUTEUR_CARTE_MODULE

    def _dessiner_module(
        self, index: int, position: str, libelle: str, etat: EtatModule | None, lot: pyglet.graphics.Batch
    ) -> list:
        x, y, largeur, hauteur = self._rect_module(index)
        cx = x + largeur / 2
        survole = index == self.index_module_survole
        selectionnee = position == self.position_selectionnee

        if etat is None:
            couleur_contour = COULEUR_CONTOUR_SELECTIONNEE if survole else COULEUR_CONTOUR_VIDE
            cadre = shapes.BorderedRectangle(
                x, y, largeur, hauteur, border=2, color=COULEUR_FOND_VIDE, border_color=couleur_contour, batch=lot
            )
            cadre.opacity = OPACITE_FOND
            libelle_label = pyglet.text.Label(
                libelle,
                x=cx,
                y=y + hauteur - 20,
                anchor_x="center",
                anchor_y="center",
                font_size=13,
                color=(*COULEUR_SOUS_TITRE, 255),
                batch=lot,
            )
            vide = pyglet.text.Label(
                "Emplacement vide",
                x=cx,
                y=y + hauteur / 2,
                anchor_x="center",
                anchor_y="center",
                font_size=12,
                color=(120, 124, 135, 255),
                batch=lot,
            )
            return [cadre, libelle_label, vide]

        spec = self.specs_par_id[etat.module_id]
        couleur_contour = COULEUR_CONTOUR_SELECTIONNEE if (survole or selectionnee) else COULEUR_CONTOUR_CARTE
        epaisseur = 4 if selectionnee else 2
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=epaisseur, color=COULEUR_FOND_CARTE, border_color=couleur_contour, batch=lot
        )
        cadre.opacity = OPACITE_FOND
        libelle_label = pyglet.text.Label(
            libelle,
            x=cx,
            y=y + hauteur - 18,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
            color=(*COULEUR_SOUS_TITRE, 255),
            batch=lot,
        )
        sprite = _sprite_ajuste(
            image_case_module(spec), cx - IMAGE_TAILLE / 2, y + hauteur - 40 - IMAGE_TAILLE, IMAGE_TAILLE, IMAGE_TAILLE, lot
        )
        nom = pyglet.text.Label(
            spec.nom,
            x=cx,
            y=y + hauteur - 52 - IMAGE_TAILLE,
            anchor_x="center",
            anchor_y="center",
            font_size=13,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        pv = pyglet.text.Label(
            f"{etat.pv} / {etat.pv_max} PV",
            x=cx,
            y=y + 34,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        niveau_maj = pyglet.text.Label(
            f"Mise a jour : niveau {etat.niveau_maj}",
            x=cx,
            y=y + 14,
            anchor_x="center",
            anchor_y="center",
            font_size=11,
            color=(*COULEUR_NIVEAU_MAJ, 255),
            batch=lot,
        )
        return [cadre, libelle_label, sprite, nom, pv, niveau_maj]

    def _rect_action(self, index: int) -> tuple[float, float, float, float]:
        total = len(ACTIONS)
        largeur_totale = total * LARGEUR_ACTION + (total - 1) * ESPACEMENT_ACTION
        x_depart = (LARGEUR_FENETRE - largeur_totale) / 2
        x = x_depart + index * (LARGEUR_ACTION + ESPACEMENT_ACTION)
        return x, Y_ACTIONS, LARGEUR_ACTION, HAUTEUR_ACTION

    def _dessiner_action(
        self, index: int, identifiant: str, libelle: str, chemin_icone: str, lot: pyglet.graphics.Batch
    ) -> list:
        # Icone deja pourvue de son cadre/nom incruste (fournie par l'utilisateur, meme principe
        # que assets/prochain_niveau/), pas de texte supplementaire ici - meme convention que
        # src/ui/ecran_choix_niveau.py. Cadre dessine derriere l'icone, sans groupe explicite
        # (meme convention que _dessiner_module ci-dessus, l'icone masque le centre du cadre et
        # ne laisse depasser que sa bordure).
        x, y, largeur, hauteur = self._rect_action(index)
        survole = index == self.index_action_survolee
        armee = identifiant == "deplacer" and self.mode_deplacement
        abordable = self.partie.argent >= COUT_ACTION_STATION_SERVICE
        if armee:
            couleur_contour = COULEUR_BOUTON_ARME
        elif survole:
            couleur_contour = COULEUR_CONTOUR_SELECTIONNEE
        else:
            couleur_contour = COULEUR_CONTOUR_CARTE
        cadre = shapes.BorderedRectangle(
            x, y, largeur, hauteur, border=3, color=COULEUR_FOND_CARTE, border_color=couleur_contour, batch=lot
        )
        icone = _sprite_ajuste(
            chemin_icone,
            x + MARGE_ICONE_ACTION,
            y + MARGE_ICONE_ACTION,
            largeur - 2 * MARGE_ICONE_ACTION,
            hauteur - 2 * MARGE_ICONE_ACTION,
            lot,
        )
        if not abordable:
            icone.opacity = 110
        prix = pyglet.text.Label(
            f"{COUT_ACTION_STATION_SERVICE} €",
            x=x + largeur / 2,
            y=y - 14,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
            color=(*COULEUR_NIVEAU_MAJ, 255) if abordable else (140, 90, 90, 255),
            batch=lot,
        )
        return [cadre, icone, prix]

    def _rect_bouton_termine(self) -> tuple[float, float, float, float]:
        x = (LARGEUR_FENETRE - LARGEUR_BOUTON_TERMINE) / 2
        return x, Y_BOUTON_TERMINE, LARGEUR_BOUTON_TERMINE, HAUTEUR_BOUTON_TERMINE

    def _dessiner_bouton_termine(self, lot: pyglet.graphics.Batch) -> list:
        x, y, largeur, hauteur = self._rect_bouton_termine()
        couleur = COULEUR_BOUTON_TERMINE_SURVOLE if self.bouton_termine_survole else COULEUR_BOUTON_TERMINE
        rectangle = shapes.Rectangle(x, y, largeur, hauteur, color=couleur, batch=lot)
        texte = pyglet.text.Label(
            "J'ai termine",
            x=x + largeur / 2,
            y=y + hauteur / 2,
            anchor_x="center",
            anchor_y="center",
            font_size=15,
            color=(*COULEUR_TEXTE, 255),
            batch=lot,
        )
        return [rectangle, texte]

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.index_module_survole = self._index_module_a(x, y)
        self.index_action_survolee = self._index_action_a(x, y)
        self.bouton_termine_survole = _point_dans_rectangle(x, y, *self._rect_bouton_termine())

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if _point_dans_rectangle(x, y, *self._rect_bouton_termine()):
            self.termine = True
            return
        index_module = self._index_module_a(x, y)
        if index_module is not None:
            self._cliquer_module(POSITIONS_AFFICHEES[index_module][0])
            return
        index_action = self._index_action_a(x, y)
        if index_action is not None:
            self._cliquer_action(ACTIONS[index_action][0])

    def _cliquer_module(self, position: str) -> None:
        if self.mode_deplacement:
            if position == self.position_selectionnee:
                # Reclic sur le module source : annule le mode deplacement.
                self.mode_deplacement = False
                return
            if position in POSITIONS_DEPLACABLES:
                # succes toujours vrai ici : l'Argent est deja verifie a l'armement de Deplacer
                # (_cliquer_action), rien ne peut le faire baisser entre-temps.
                deplacer_module(self.partie, self.position_selectionnee, position)
                self.mode_deplacement = False
                self.position_selectionnee = None
            return
        if self.partie.vaisseau[position] is not None:
            self.position_selectionnee = position

    def _cliquer_action(self, identifiant: str) -> None:
        if self.position_selectionnee is None:
            return
        index = next(i for i, (position, _libelle) in enumerate(POSITIONS_AFFICHEES) if position == self.position_selectionnee)
        if self.partie.argent < COUT_ACTION_STATION_SERVICE:
            self._ajouter_popup_argent_insuffisant(index)
            return
        if identifiant == "deplacer":
            if self.position_selectionnee in POSITIONS_DEPLACABLES:
                self.mode_deplacement = True
            return
        etat = self.partie.vaisseau[self.position_selectionnee]
        pv_avant = etat.pv
        APPLICATEURS_ACTION[identifiant](self.partie, self.position_selectionnee)
        self._ajouter_popup_action(index, identifiant, etat, pv_avant)
        # Deselectionne une fois l'action appliquee (demande utilisateur) : le popup ci-dessus
        # suffit a confirmer l'effet, pas besoin de garder le module arme pour une autre action.
        self.position_selectionnee = None

    def _ajouter_popup_action(self, index: int, identifiant: str, etat: EtatModule, pv_avant: int) -> None:
        """Popup de confirmation sur la carte du module concerne (specs.md 2.2) : PV effectivement
        gagnes pour Reparer (plafonne a pv_max, cf. reparer_module), PV max gagnes pour Ameliorer,
        palier atteint pour Mettre a jour (plafonne a NIVEAU_MAJ_MAX, cf. mettre_a_jour_module)."""
        if identifiant == "reparer":
            texte = f"+{etat.pv - pv_avant} PV"
        elif identifiant == "ameliorer":
            texte = f"+{PV_AMELIORATION} PV max"
        else:
            texte = f"Niveau {etat.niveau_maj}"
        couleur = COULEUR_POPUP_SOIN if identifiant in ("reparer", "ameliorer") else COULEUR_NIVEAU_MAJ
        x, y, largeur, hauteur = self._rect_module(index)
        animation = AnimationPopup()
        animation.demarrer()
        self.popups.append((animation, texte, couleur, x + largeur / 2, y + hauteur / 2))

    def _ajouter_popup_argent_insuffisant(self, index: int) -> None:
        """Popup d'echec sur la carte du module cible quand l'Argent est insuffisant pour l'action
        (specs.md 2.1/2.2, COUT_ACTION_STATION_SERVICE)."""
        x, y, largeur, hauteur = self._rect_module(index)
        animation = AnimationPopup()
        animation.demarrer()
        self.popups.append((animation, "Argent insuffisant !", COULEUR_POPUP_DEGATS, x + largeur / 2, y + hauteur / 2))

    def _index_module_a(self, x: int, y: int) -> int | None:
        for index in range(len(POSITIONS_AFFICHEES)):
            if _point_dans_rectangle(x, y, *self._rect_module(index)):
                return index
        return None

    def _index_action_a(self, x: int, y: int) -> int | None:
        for index in range(len(ACTIONS)):
            if _point_dans_rectangle(x, y, *self._rect_action(index)):
                return index
        return None
