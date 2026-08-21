# Simulateur de parties

> **État actuel : proposition de conception, rien n'est encore implémenté.** Ce document sert de
> base de discussion avant tout code. À mettre à jour au fur et à mesure des décisions prises, comme
> `specs/poc.md` pour le POC de combat.

## 1. Objectif

Faire jouer le moteur de combat (`src/gameplay/`) par un "bot" plutôt que par un humain, sur un grand
nombre de parties, pour obtenir des statistiques d'équilibrage : quelles cartes font gagner
souvent (peut-être trop fortes), quelles cartes sont associées aux défaites (peut-être trop
faibles), quelles combinaisons de cartes fonctionnent bien ensemble, etc. Pas de rendu graphique :
seul le gameplay compte.

## 2. Architecture et règle d'isolation

- Nouveau dossier `simulateur/` à la racine du dépôt, au même niveau que `src/`, `web/`, `tests/`.
- Le simulateur **importe** `src.gameplay` (et éventuellement `web.bridge` pour réutiliser sa
  sérialisation JSON de l'état du combat plutôt que d'en écrire une troisième) : c'est son seul rôle,
  piloter le moteur existant sans le modifier ni dupliquer ses règles.
- **Règle absolue : aucun import de `simulateur/` depuis `src/`, `web/`, ou `tests/`.** La
  dépendance est à sens unique. Un garde-fou automatisé serait utile pour que la règle survive dans
  le temps : un petit test ou script qui grep les imports de `src/`/`web/`/`tests/` et échoue si l'un
  d'eux référence `simulateur`.
- Le simulateur n'a pas besoin d'être couvert par la suite `pytest` principale (`testpaths` dans
  `pyproject.toml`). Ses propres tests, si besoin, vivraient dans `simulateur/tests/`.

## 3. Comment le bot joue

Il faut une politique de décision pour remplacer la souris/les doigts d'un humain. Prévoir plusieurs
stratégies "pluggables" dès le départ plutôt qu'une seule, pour pouvoir les comparer entre elles :

### 3.1 Aléatoire

Parmi les coups jouables (assez d'électricité, cible valide), en choisit un au hasard, cible
aléatoirement, jusqu'à ne plus pouvoir/vouloir jouer, puis fin de tour. Sert de bruit de fond / niveau
plancher pour juger si un résultat est signifiant.

### 3.2 Heuristique (règles fixes)

Ex : "attaque l'ennemi avec le moins de PV restants", "bouclier sur le module le plus endommagé",
"joue toujours si l'électricité le permet plutôt que de la garder". Rapide et gratuit (aucun appel
réseau), donc adapté au grand volume de parties. Donne une lecture "joueur qui sait ce qu'il fait",
mais reste rigide.

### 3.3 Modèle de langage (Claude)

L'état du combat (déjà sérialisable via `web/bridge.py::_etat_dict()`) est donné à un modèle, qui
choisit une action via un outil contraint (`jouer_carte(index, cible)` / `finir_tour()` en
tool-calling, pas de texte libre à parser) ; on applique la décision via le moteur, on resérialise,
on boucle jusqu'à fin de tour.

Apport principal : le modèle peut **justifier** sa décision en langage naturel ("je ne joue pas
Bouclier perpétuel ce tour, coût 5 trop élevé face à 5 électricité/tour disponible") — un signal
qualitatif qu'aucune heuristique ne donne, et qui répond directement à "cette carte est-elle trop
chère/forte" avec une explication, pas juste un pourcentage. Il peut aussi exploiter l'intention
ennemie affichée de façon contextuelle plutôt que par une règle figée.

Compromis à assumer : un appel réseau par décision (potentiellement 15-40 par partie) rend cette
stratégie lente et coûteuse à grande échelle, et les décisions ne sont pas parfaitement
reproductibles d'une exécution à l'autre (contrairement à la convention de déterminisme du reste du
projet, cf. CLAUDE.md). Pas adapté au volume, adapté à la vérification ciblée.

### 3.4 Utilisation combinée des trois

Un roster à trois niveaux plutôt qu'un choix unique :

1. **Aléatoire** — bruit de fond, gratuit, des milliers de parties
2. **Heuristique** — rapide, gratuit, volume principal pour les stats agrégées
3. **Modèle** — un petit lot ciblé (10-50 parties) pour valider/creuser un résultat surprenant de
   l'heuristique, avec les justifications textuelles en plus des chiffres

Le modèle ne remplace pas le volume, il sert à vérifier ("l'heuristique dit que telle carte gagne 95%
du temps — est-ce parce qu'elle est vraiment forte, ou parce que l'heuristique cible mal et un joueur
réfléchi ferait pareil ?").

## 4. Comment on fait varier les parties

Deux modes, complémentaires :

- **Observationnel** : on lance N combats avec la génération aléatoire actuelle (`creer_combat_poc`,
  deck/flotte tirés comme en jeu réel) et on mine les corrélations a posteriori. Simple, fidèle au
  jeu réel, mais statistiquement plus faible — une carte rare tirée dans peu de decks demande
  beaucoup de parties pour un signal fiable, et le tirage est confondu avec le module d'origine (une
  carte "forte" tirée avec un module qui a par ailleurs de bons PV fausse la lecture).
- **Contrôlé / A-B** : on force une carte donnée à être présente (ou absente) dans le deck sur un lot
  de parties, tout le reste étant égal (mêmes graines de flotte). Isole vraiment l'effet d'une carte,
  mais demande une petite extension pour injecter un deck personnalisé dans `creer_combat_poc`
  plutôt que le tirage 100% aléatoire actuel.

Recommandation : commencer par l'observationnel (rien à changer côté moteur), ajouter le contrôlé si
les premiers résultats donnent envie de creuser une carte précise.

## 5. Données enregistrées par partie

- Victoire/défaite, nombre de tours
- Composition du deck (quelles cartes, par id)
- Cartes effectivement jouées, combien de fois chacune
- Dégâts infligés / subis, par carte et au total
- Électricité non dépensée en fin de tour (signal de deck "illisible" ou de cartes trop chères)
- Quel module est mort en premier / a le plus souffert
- Composition de la flotte ennemie affrontée
- Pour la stratégie modèle : la justification textuelle de chaque décision

## 6. Rapports / statistiques agrégées proposées

- **Win rate par carte présente dans le deck**, avec la taille d'échantillon affichée à côté (pas de
  conclusion sur 5 parties)
- **Win rate par carte jouée au moins une fois** vs **carte présente mais jamais jouée** (distingue
  "carte trop faible pour être choisie" de "carte présente mais inutile telle quelle")
- **Win rate par paire de cartes co-présentes** (ne garder que les paires apparues assez souvent pour
  être lisibles)
- **Cartes les plus associées aux défaites** (celles qui traînent en main, jamais jouées, dans les
  parties perdues)
- **Modules les plus associés aux défaites/victoires** (utile aussi pour équilibrer les PV de
  module, pas seulement les cartes)
- **Répartition du nombre de tours** (combats systématiquement terminés en 2 tours = trop facile ;
  qui traînent = trop dur ou stratégie du bot insuffisante)

## 7. Pièges statistiques à garder en tête

- Toujours reporter la taille d'échantillon à côté d'un pourcentage
- Corrélation carte ↔ module d'origine (cf. §4) : donner aussi les stats par module en plus des
  cartes
- Le bot n'est pas un humain : un mauvais win rate peut vouloir dire "le bot cible mal", pas "la
  carte est faible" — d'où l'intérêt de comparer aléatoire vs heuristique vs modèle

## 8. Format de sortie

Simple pour commencer : résumé console. Éventuellement un export CSV/JSON par partie pour analyse
externe (Excel, cohérent avec `specs/cartes.xlsx`), et pourquoi pas un petit tableau `.xlsx` de
synthèse par carte plus tard si l'usage s'installe.

## 9. Prochaines étapes (à décider avant de coder)

- Quelle stratégie de bot développer en premier (probablement l'heuristique, pour avoir un volume
  exploitable rapidement)
- Observationnel seul pour commencer, ou prévoir tout de suite l'injection de deck pour le mode
  contrôlé
- Format de sortie de la première version (console suffit au départ)
- Faut-il le garde-fou automatisé anti-import dès la première version, ou plus tard
