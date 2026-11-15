"""
Deck de combat (Deck) : les cinq piles de cartes d'un combat (pioche, main,
defausse, epuisees, Hors service) et le deck de depart (specs.md 3.3, 3.4, 3.7).
"""

import random
from collections.abc import Iterable

from src.gameplay.carte import Carte

# Valeurs inchangees par rapport au moteur actuel (deck.py, combat.md 3.3)
TAILLE_MAIN_MAX = 10
CARTES_PIOCHEES_PAR_TOUR = 5

# Deck de depart (decision utilisateur) : id de carte -> nombre d'exemplaires, tous rattaches au
# principal
DECK_DE_DEPART = {"CRT_7": 4, "CRT_10": 4, "CRT_11": 1, "CRT_12": 1}


def deck_de_depart(modeles: dict[str, Carte], exemplaire_principal: str) -> list[Carte]:
    """Exemplaires neufs du deck de depart, rattaches au principal."""
    return [
        modeles[id_carte].copie(exemplaire_module=exemplaire_principal)
        for id_carte, nombre in DECK_DE_DEPART.items()
        for _ in range(nombre)
    ]


class Deck:
    """Les piles de cartes d'un combat. Une carte est toujours dans exactement une pile, sauf
    pendant qu'elle est jouee (retiree de la main, puis rangee par `ranger_carte_jouee`)."""

    def __init__(self, cartes: Iterable[Carte], aleatoire: random.Random):
        # Generateur des melanges ; remplace par Combat.remplacer_aleatoire (copies du bot)
        self.aleatoire = aleatoire
        self.pioche: list[Carte] = list(cartes)
        self.main: list[Carte] = []
        self.defausse: list[Carte] = []
        self.epuisees: list[Carte] = []
        self.hors_service: list[Carte] = []
        self.aleatoire.shuffle(self.pioche)

    def toutes_les_cartes(self) -> list[Carte]:
        return self.pioche + self.main + self.defausse + self.epuisees + self.hors_service

    def piocher(self, nombre: int) -> int:
        """Pioche jusqu'a `nombre` cartes (main limitee a TAILLE_MAIN_MAX) ; la defausse est
        remelangee si la pioche est vide, jamais les epuisees ni les Hors service. Renvoie le nombre
        de cartes piochees."""
        piochees = 0
        for _ in range(nombre):
            if len(self.main) >= TAILLE_MAIN_MAX:
                break
            if not self.pioche:
                self.pioche, self.defausse = self.defausse, []
                self.aleatoire.shuffle(self.pioche)
            if not self.pioche:
                break
            self.main.append(self.pioche.pop())
            piochees += 1
        return piochees

    def retirer_de_la_main(self, carte: Carte) -> None:
        """Debut du jeu d'une carte : elle quitte la main (identite d'objet, pas egalite)."""
        index = next((i for i, en_main in enumerate(self.main) if en_main is carte), None)
        if index is None:
            raise ValueError(f"Carte {carte.id} : pas en main")
        del self.main[index]

    def ranger_carte_jouee(self, carte: Carte, epuisee: bool, module_detruit: bool) -> None:
        """Fin du jeu d'une carte : epuisees si ses munitions sont a 0, Hors service si son module a
        ete detruit pendant qu'elle etait jouee (et qu'elle n'est pas Persistante), sinon
        defausse."""
        if epuisee:
            self.epuisees.append(carte)
        elif module_detruit and not carte.persistante:
            self.hors_service.append(carte)
        else:
            self.defausse.append(carte)

    def defausser_main(self) -> None:
        self.defausse.extend(self.main)
        self.main = []

    def mettre_hors_service(self, exemplaire_module: str) -> list[Carte]:
        """Module detruit : toutes ses cartes non Persistantes de la pioche, de la main et de la
        defausse passent en Hors service, munitions gardees. Renvoie les cartes deplacees."""
        deplacees = []
        for pile in (self.pioche, self.main, self.defausse):
            restent = []
            for carte in pile:
                (deplacees if carte.exemplaire_module == exemplaire_module and not carte.persistante else restent).append(carte)
            pile[:] = restent
        self.hors_service.extend(deplacees)
        return deplacees
