# Simulation d'équilibrage — conception de l'outil

*Document de conception de l'outil `outils/simulation/`. Les choix marqués « décision
utilisateur » sont validés. **État d'implémentation et écarts : §11.** Synthèses produites :
`outils/simulation/synthese/`.*

---

## 1. Objectif

Faire jouer automatiquement un grand nombre de combats et de parties complètes, sans affichage,
pour mesurer l'équilibrage du jeu et produire une synthèse chiffrée :

- cartes trop fortes ou jamais jouées, ennemis trop durs ou trop faciles, courbe de difficulté
  sur les 10 niveaux ;
- **intérêt comparé des choix** du parcours (Aventure, combat, Station service...) ;
- **force comparée des modules** ;
- **effet des variantes de règles** en discussion (brouillons
  [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md) et
  [refonte-modules.md](refonte-modules.md)).

---

## 2. Principes

- **Aucune règle de jeu dans l'outil.** Comme `src/ui` et `web/` (cf. `CLAUDE.md`), l'outil ne fait
  qu'appeler `src/gameplay/` et **décider** à la place du joueur. Il ne réimplémente ni le combat,
  ni les récompenses, ni les Aventures.
- **Variantes de règles dans `src/gameplay`, désactivées par défaut.** Une variante (ex. bouclier
  -1/tour) est ajoutée au moteur sous forme de paramètre de règles (ex. un objet `ReglesCombat`
  passé au `Combat`), avec la valeur actuelle par défaut. Le jeu ne change pas tant que la variante
  n'est pas adoptée, et une variante adoptée est déjà implémentée et testée. Écarté : modifier le
  comportement du moteur depuis l'outil (monkeypatch), qui ferait diverger la simulation du jeu.
- **Reproductibilité.** Tout tirage passe par un `random.Random` à graine explicite (règle de
  `CLAUDE.md`). Une simulation relancée avec les mêmes graines donne exactement les mêmes résultats.
- **Orchestration du parcours** : l'enchaînement des écrans d'une partie est décidé par
  `src/gameplay/deroulement.py` (parcours.md §2.4), partagé par le PC, le web et la simulation
  (décision utilisateur : il était auparavant dupliqué dans `main.py` et `web/`, ce qui
  contredisait la règle « tout le gameplay dans `src/gameplay` »). La simulation appelle les mêmes
  fonctions de transition, sans réimplémenter l'enchaînement.

---

## 3. Le joueur automatique : bot « recherche » (décision utilisateur)

### 3.1 Principe

À chaque tour de combat, le bot **essaie toutes les séquences de cartes jouables** avec
l'électricité disponible, sur des copies du combat, et garde la meilleure :

1. Lister les séquences possibles : ordre des cartes de la main, cible de chaque carte (ennemi,
   module, colonne...), dans la limite de l'électricité. Avec 5 cartes en main et 3 d'électricité,
   cela reste de l'ordre de quelques centaines de séquences.
2. Pour chaque séquence : copier le combat, jouer la séquence, **terminer le tour** pour laisser
   les ennemis répondre, puis évaluer l'état obtenu (§3.2).
3. Jouer pour de vrai la séquence la mieux notée.

Coût mesuré : copier un combat prend environ **0,4 ms** (`copy.deepcopy`). Une évaluation complète
de séquence (jouer + tour ennemi) est estimée à 1 ms, soit 0,1 à 0,5 s par tour et quelques
secondes par combat.

### 3.2 Évaluation d'un état

Score pondéré, dans l'ordre d'importance :

1. combat gagné (très fort bonus) ou perdu (très fort malus) ;
2. PV perdus par le module principal (fort malus : seuls ses PV persistent, cf. refonte des
   modules) ;
3. PV retirés aux ennemis, ennemis tués ;
4. PV perdus par les modules secondaires, modules secondaires morts ;
5. bouclier restant, debuffs posés sur les ennemis (faible bonus).

Les poids sont à régler en vérifiant que le bot bat nettement un bot aléatoire.

### 3.3 Ne pas tricher

Copier le combat copie aussi **ce que le joueur ne peut pas savoir** :

- l'**ordre de la pioche** : l'évaluation ne doit jamais regarder la main suivante ni la pioche ;
- l'**état du générateur aléatoire** du combat (redirection *Tir allié*, cible du Bouclier miroir) :
  chaque copie d'évaluation reçoit un **nouveau générateur**, pour que le bot ne voie pas à
  l'avance le résultat d'un tirage. Le combat réel garde le sien.

Le bot voit en revanche tout ce que le joueur voit à l'écran : intentions des ennemis, PV,
boucliers, buffs.

### 3.4 Bots de référence

Un bot **aléatoire** (cartes et cibles au hasard) sert de plancher : si une variante ou un module
change aussi les résultats du bot aléatoire, l'effet ne vient pas de la qualité de jeu.

---

## 4. Échelle 1 : combat isolé

Un combat construit directement (vaisseau, deck, flotte), joué jusqu'au bout.

- **Configurations** : chaque module secondaire (ou combinaison), contre chaque flotte : ennemis
  seuls, flottes de Prime aux différents niveaux, Boss des pirates.
- **Mesures** : taux de victoire, nombre de tours, PV perdus (principal et secondaires), modules
  secondaires morts, cartes jouées et cartes jamais jouées, électricité inutilisée.
- **Volume** : quelques milliers de combats par configuration, en quelques minutes.

C'est l'échelle la plus rapide pour comparer les cartes, les ennemis et les variantes de règles
de combat (§6).

---

## 5. Échelle 2 : partie complète

Une partie jouée de la sélection du module jusqu'au Boss du niveau 10, ou jusqu'à la défaite.

### 5.1 Décisions hors combat : politique par défaut

Le bot doit décider partout où le joueur décide. Une **politique par défaut** simple et explicite :

| Décision | Politique par défaut proposée |
|---|---|
| Choix du module (niveau 1) | Au hasard parmi les 3 proposés, sauf module forcé (§5.3) |
| Carte du module choisi | La plus rare, sinon la première |
| Prochain niveau (2 à 3 propositions) | Combat (Prime) si le principal a plus de la moitié de ses PV, sinon Station service si proposée et payable |
| Récompense de combat | La carte la plus rare ; Passer jamais |
| Station service | Réparer le principal s'il lui manque au moins 20 PV, sinon Améliorer le principal |
| Aventures | Choix fixe par Aventure, à définir |

Cette politique compte autant que le bot de combat : les comparaisons de §5.2 mesurent un choix
**suivi de cette politique**, pas un choix dans l'absolu.

### 5.2 Clonage aux points de décision (décision utilisateur)

Pour savoir si un choix est nettement plus intéressant qu'un autre :

1. Une partie avance normalement avec la politique par défaut.
2. À un point de décision, la partie est **clonée** en autant de copies que d'options : chaque
   clone prend une option différente.
3. Chaque clone **continue jusqu'à la fin** avec la politique par défaut.
4. On compare les clones : victoire contre le Boss, niveau atteint, PV du principal restants,
   Argent.

Sur un grand nombre de parties, on obtient pour chaque type de décision une estimation de l'écart
entre les options : « choisir l'Aventure plutôt que la Prime fait gagner X % de parties ».

**Équité entre clones** : le hasard de chaque niveau est déjà dérivé de la graine de la partie et du
numéro de niveau (`parcours.aleatoire_pour_niveau`). Deux clones arrivés au même niveau voient donc
les mêmes propositions de niveau ; la différence de résultat vient du choix et non de la chance.
À vérifier pendant l'implémentation : que les tirages de combat (deck, flotte) et d'Aventure
suivent la même règle ; sinon, leur donner un générateur dérivé de la graine de la même façon.

**Explosion combinatoire** : une partie compte des dizaines de décisions ; cloner à chacune ferait
exploser le nombre de parties (2 options à 30 décisions = un milliard de parties). On clone donc
**à un seul point de décision par partie**, tiré au hasard ou choisi selon l'étude, puis les clones
suivent la politique par défaut sans se recloner. Pour réduire la part de chance après la décision,
chaque clone peut être rejoué plusieurs fois avec des graines différentes (même jeu de graines pour
tous les clones d'un même point).

**Décisions concernées** : prochain niveau (Prime / Aventure / Station / Planète), choix des
Aventures (8 choix sur les 3 Aventures), action de Station service, récompense de combat (prendre
une carte ou Passer), choix du module du niveau 1.

**Coût** : une partie complète est estimée entre 30 s et 1 min avec le bot de recherche (8 à 10
combats). 1 000 points de décision à 2 options, rejoués 5 fois, font 10 000 parties : plusieurs
heures sur un cœur, à paralléliser sur tous les cœurs de la machine. Estimations à confirmer.

### 5.3 Module forcé (décision utilisateur)

Pour comparer les modules à nombre de parties égal :

- le choix du module du niveau 1 est **imposé** au lieu d'être tiré : même nombre de parties pour
  chaque module ;
- les parties de chaque module utilisent les **mêmes graines** : mêmes flottes, mêmes propositions
  de niveau. Seul le module change.

Modules comparables aujourd'hui : les 5 secondaires qui ont des cartes (Lanceur de missiles,
Blindage, Générateur, Soute, Sabotage). Les 4 sans cartes (Canon lourd, Contrôle, Atelier, Radar)
sont exclus du tirage du jeu et ne peuvent pas être testés.

---

## 6. Variantes de règles : à quelle échelle ?

Pas seulement en combat isolé : une variante se teste **à l'échelle où ses effets apparaissent**.

| Variante | Combat isolé | Partie complète | Pourquoi |
|---|---|---|---|
| Décroissance du bouclier (-1/tour, moitié...) | **Oui** | Confirmation | Effet visible dans un combat |
| Montée des dégâts ennemis (+1, +2) | **Oui** | Confirmation | Idem, plus l'usure du principal sur la run |
| Deux familles de buffs/debuffs | **Oui** | Confirmation | Idem |
| Modules secondaires sacrifiables (PV remis au max) | Partiel | **Indispensable** | La différence porte sur les PV **entre** les combats |
| PV max des secondaires, PV du principal | Partiel | **Indispensable** | Idem |
| Pile Hors service, mot-clé Persistante | **Oui** | Confirmation | Effet visible dans un combat |

Démarche proposée : **dégrossir en combat isolé** (rapide, des milliers de combats), puis
**confirmer en partie complète** les variantes retenues.

---

## 7. Résultats et synthèse

- **Données brutes** : un fichier par simulation (CSV ou JSON, une ligne par combat ou par partie,
  avec la graine pour pouvoir rejouer un cas précis), dans un dossier de résultats ignoré par git.
- **Synthèse** : un rapport lisible (Markdown ou page avec graphiques) : tableaux par carte, par
  ennemi, par module, par décision et par variante, avec l'écart entre options et une indication de
  fiabilité (nombre de parties, marge d'incertitude).

---

## 8. Utilisation envisagée

Commandes indicatives, à préciser à l'implémentation :

```
python -m outils.simulation combat --module MOD_3 --flotte boss --parties 2000 --graine 1
python -m outils.simulation partie --module-force MOD_2 --parties 500
python -m outils.simulation decisions --points 1000 --repetitions 5
python -m outils.simulation combat --variante bouclier_moins_un --parties 2000
```

---

## 9. Limites

- **Le bot n'est pas un humain** : les écarts **relatifs** (entre cartes, modules, choix, variantes)
  sont fiables ; un taux de victoire absolu dépend du niveau du bot et de la politique par défaut.
- **Pas de mesure du plaisir** : lisibilité, frustration, variété restent à juger en jouant.
- **Contenu incomplet** : 18 cartes sur 44 non jouables, 4 modules sans cartes, beaucoup de valeurs
  inventées. L'équilibrage porte sur l'existant.
- **Variantes** : elles traduisent les brouillons de refonte tels que compris ; à relire avant
  d'en tirer des conclusions.

---

## 10. Étapes de réalisation (plan initial)

1. Bot de recherche et échelle « combat isolé », avec les règles actuelles ; vérifier qu'il bat
   nettement le bot aléatoire.
2. Première synthèse : cartes, ennemis, modules en combat.
3. Échelle « partie complète » avec politique par défaut, sur `src/gameplay/deroulement.py` (§2).
4. Module forcé (§5.3), puis clonage aux points de décision (§5.2).
5. Paramètres de règles dans `src/gameplay` et variantes (§6).

---

## 11. État d'implémentation (2026-11-07, règles actuelles, pré-refonte)

Implémenté dans `outils/simulation/` (`bot.py`, `partie_auto.py`, `etudes.py`, `rapport.py`,
`__main__.py`), sur les règles **actuelles** du jeu (aucune variante de refonte, décision
utilisateur : « on ne mélange pas tout »). Tests : `tests/test_simulation.py`.

**Lancement** : `python -m outils.simulation --budget 500 --parties-par-module 40 --validation 30`
écrit les résultats bruts (JSON) et leurs tableaux (Markdown) dans `outils/simulation/resultats/`
(ignoré par git). Exécution en parallèle sur tous les cœurs. Sur Mac, lancer avec
`caffeinate -i python -m outils.simulation ...` : sans ça, la mise en veille automatique interrompt
le calcul (constaté lors de la première campagne : 3 min de calcul étalées sur 18 min). Synthèses
rédigées : `outils/simulation/synthese/analyse_AAAA-MM-JJ.md` (rapports générés, hors `specs/`).

**Écarts et précisions par rapport aux sections précédentes :**

- **Bot de recherche (§3.1)** : recherche **en faisceau** (6 états gardés par profondeur) plutôt
  qu'exhaustive ; chaque séquence partielle est notée **après la réponse ennemie** simulée sur une
  copie. Une carte présente en plusieurs exemplaires identiques n'est essayée qu'une fois.
  Environ 30 ms par tour.
- **Évaluation (§3.2)** : poids réglés sur 15 combats (principal 2, secondaire 1, ennemi 2,5,
  malus de 40 par ennemi vivant…), le réglage défensif initial s'enlisait. Ajout d'une **valeur des
  effets durables** (vulnérabilité posée, bouclier récurrent) : sans elle, la recherche, qui ne
  voit que le tour suivant, ne jouait presque jamais les debuffs longs ni les buffs récurrents
  (même taux de victoire avec ou sans, mais usage des cartes réaliste avec).
- **Triche résiduelle (§3.3)** : une carte qui pioche (*Boost*) révèle au bot les cartes piochées
  pendant sa recherche (l'ordre de la pioche est copié). Effet limité à ces cartes.
- **Combats enlisés** : un combat arrêté au bout de 40 tours compte comme une défaite et est
  signalé à part (« enlisé »).
- **Clonage (§5.2)** : pas de copie en mémoire. Tout le hasard d'une partie dérive de sa graine, du
  niveau et de l'usage (combat, récompense, Aventure, bot), donc **rejouer** la graine avec un
  autre choix imposé au point de décision reproduit exactement le même début de partie : c'est
  un clone, sans avoir à copier l'état. Seuls les choix du **prochain niveau** sont clonés pour
  l'instant (pas les choix internes aux Aventures ni à la Station).
- **Politique par défaut (§5.1)**, telle qu'implémentée : Prime/Boss en priorité, Station si le
  principal est sous 50 % de ses PV et que l'Argent suffit ; Station : réparer le principal s'il
  lui manque 15 PV, sinon l'améliorer, tant que l'Argent suffit ; Trois lunes : améliorer le
  principal ; Astéroïdes : traverser avec le secondaire le plus solide, prendre la carte offerte ;
  Police : payer la mise aux normes si possible, sinon confiscation ; cartes (module, récompense) :
  la plus rare.
- **Séquences internes des Aventures** (deux chocs d'Astéroïdes, Détourner puis choisir de Police)
  : jouées par l'outil en appelant les fonctions de `src/gameplay/partie.py` dans l'ordre où les
  écrans les appellent ; ces petites séquences vivent encore dans les écrans (`src/ui/`,
  `web/app.js`), à extraire dans `src/gameplay` comme l'enchaînement du parcours si elles
  deviennent plus riches.
- **Budget par défaut** (500 simulations au plus, décision utilisateur) : 60 combats de
  validation, 90 combats isolés, 200 parties à module forcé, au plus 150 parties clonées.
