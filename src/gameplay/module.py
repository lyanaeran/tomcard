"""
Le module de base du vaisseau du joueur : points de vie et bouclier.
"""

from src.gameplay.carte import ActionCarte, BuffActif


class Module:
    """Represente le module de base du vaisseau du joueur."""

    def __init__(self, pv_max: int, nom: str = "Module", image: str | None = None):
        self.pv_max = pv_max
        self.pv = pv_max
        self.bouclier = 0
        self.nom = nom
        self.image = image
        self.buffs_actifs: list[BuffActif] = []
        self.leurre_actif = False

    def est_detruit(self) -> bool:
        """Renvoie True si le module n'a plus de points de vie."""
        return self.pv <= 0

    def subir_degats(self, degats: int) -> None:
        """Applique des degats, en absorbant d'abord avec le bouclier (specs.md paragraphe 3.5).

        Un leurre actif (specs.md 12.6) annule totalement la prochaine attaque recue, quelle
        que soit son ampleur - different d'un bouclier classique qui absorbe un montant fixe -
        puis se consomme (une seule attaque annulee par pose de la carte)."""
        if self.leurre_actif:
            self.leurre_actif = False
            return
        degats_restants = max(0, degats - self.bouclier)
        self.bouclier = max(0, self.bouclier - degats)
        self.pv = max(0, self.pv - degats_restants)

    def ajouter_bouclier(self, valeur: int) -> None:
        """Ajoute du bouclier au module."""
        self.bouclier += valeur

    def soigner(self, valeur: int) -> None:
        """Repare des points de vie, sans depasser le maximum."""
        self.pv = min(self.pv_max, self.pv + valeur)

    def appliquer_buff(self, action: ActionCarte, valeur: int, tours: int | None) -> None:
        """Ajoute un nouveau buff actif et declenche son effet immediatement (comme les
        autres types de carte), en plus des declenchements suivants a chaque debut de
        tour joueur tant que le buff reste actif (cf. declencher_buffs_tour)."""
        buff = BuffActif(action=action, valeur=valeur, tours_restants=tours)
        self.buffs_actifs.append(buff)
        self._declencher_buff(buff)

    def _declencher_buff(self, buff: BuffActif) -> None:
        if buff.action == ActionCarte.BOUCLIER_PAR_TOUR:
            self.ajouter_bouclier(buff.valeur)

    def declencher_buffs_tour(self) -> None:
        """A appeler au debut de chaque tour joueur : redeclenche l'effet de chaque buff
        actif (le tout premier declenchement a eu lieu a la pose, cf. appliquer_buff),
        puis decompte sa duree. Les buffs persistants (tours_restants=None) ne decomptent
        jamais et durent tout le combat."""
        for buff in self.buffs_actifs:
            self._declencher_buff(buff)
        for buff in self.buffs_actifs:
            if buff.tours_restants is not None:
                buff.tours_restants -= 1
        self.buffs_actifs = [buff for buff in self.buffs_actifs if buff.tours_restants is None or buff.tours_restants > 0]
