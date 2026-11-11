# Branchement de la refonte — proposition

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **Plan validé, rien n'est
encore codé** (décisions du §2 et ordre des PR du §5 tranchés le 2026-11-11 ; l'affichage du §4
reste une proposition, à valider sur maquette). Décrit comment faire passer le jeu (parcours, sauvegarde, affichage
PC et web) sur le moteur de la refonte (`CombatNew` et les fichiers `*_new.py`), puis supprimer
l'ancien moteur. Contexte : [refonte.md](refonte.md) ; règles du nouveau combat :
[refonte-combat.md](refonte-combat.md).*

---

## 1. Objectif

Aujourd'hui, le jeu (PC et web) utilise encore l'ancien combat (`combat.py`), créé à partir de la
partie par `partie.py:combat_depuis_partie`. Le nouveau combat (`CombatNew`) est codé, testé et
simulé (5 800 combats sans erreur), mais rien ne l'utilise.

Le branchement doit :

1. créer un `CombatNew` à partir de la partie, et reporter son résultat dans la partie ;
2. sauvegarder la partie au nouveau format (cartes rattachées à un exemplaire de module) ;
3. afficher le nouveau combat sur PC et sur web, avec **le même flux de clics qu'aujourd'hui**
   (sélectionner une carte, puis confirmer sur une case vivante du bon camp, specs.md §8.3) ;
4. supprimer l'ancien moteur.

---

## 2. Décisions (utilisateur, 2026-11-11)

Toutes tranchées le 2026-11-11.

| # | Question | Décision |
|---|---|---|
| 1 | **Sauvegardes existantes** : le deck sauvegardé doit dire à quel module appartient chaque carte. | **Abandonner** : les parties en cours d'une ancienne version sont effacées à la lecture, le profil est gardé. Aucune conversion à coder. |
| 2 | **Station service** : un secondaire repart plein à chaque combat, réparer un secondaire n'a plus de sens. | « Réparer » ne vise plus que le **principal** ; « Améliorer » (+PV max) reste possible sur tous les modules ; « Mettre à jour » et « Déplacer » inchangés. |
| 3 | **Aventures** : les dégâts et soins sur un secondaire seraient effacés au combat suivant. | **Astéroïdes** (« Traverser ») : les chocs touchent **toujours le principal**, le choix du module disparaît. **Trois lunes** (« Réparer le vaisseau ») : soigne le principal, seul module dont les PV comptent (conséquence directe, pas une décision à part). |
| 4 | **Flottes** : composition par niveau. | **Règles actuelles** avec les nouveaux ennemis, coefficient 1 : 1 ennemi jusqu'au niveau 5, 2 ensuite, le Boss au niveau 10, 3 ennemis aux Astéroïdes, placement préféré respecté. La difficulté par niveau sera réglée après le branchement, avec des simulations de parties complètes. |
| 5 | **Cartes proposées en récompense**. | **Les 19 cartes revues** des modules équipés deviennent proposables ; le champ `jouable` de `carte_new.json` passe à `true` pour toutes. |
| 6 | **Affichage des nouveautés** (intentions, statuts, Hors service, lancements…). | **Maquette d'abord** : au début de la PR 2, une maquette web (captures d'un combat) des éléments du §4, validée par l'utilisateur avant de finir l'affichage. |
| 7 | **Méthode** : basculer d'un coup, ou garder un interrupteur ancien / nouveau moteur. | **D'un coup**, en quatre PR successives sur `devjeux`, web avant PC (§5). |

---

## 3. Ce que l'affichage utilise aujourd'hui, et son équivalent

L'affichage PC (`src/ui/fenetre.py`, environ 1 100 lignes) et web (`web/bridge.py` 800 lignes,
`web/app.js` 2 000 lignes) lisent directement l'ancien combat. Correspondances :

| Aujourd'hui (ancien moteur) | Avec `CombatNew` |
|---|---|
| `combat_depuis_partie(partie)` | Nouvelle fonction de `partie.py` qui crée les copies de combat des modules (`ModuleNew.copie_pour_combat`), le deck rattaché (`CarteNew.copie`), la flotte (`EnnemiNew.pour_combat`, placés), et appelle `CombatNew(...)` |
| `synchroniser_vaisseau_depuis_combat` (PV de tous les modules) | `ModuleNew.reporter_combat` : seuls les PV du principal sont reportés |
| `combat.joueur.vaisseau.base` / `modules_equipes()` | `combat.vaisseau.principal`, `combat.vaisseau.modules`, `module_en(case)` |
| `combat.flotte.positions()` | `combat.flotte.ennemis`, `cases_de(ennemi)`, `ennemi_en(case)` |
| `combat.joueur.deck.main`, pioche, défausse, épuisées | `combat.deck.main`, `pioche`, `defausse`, `epuisees`, **`hors_service`** (nouvelle pile) |
| `combat.joueur.electricite` | `combat.electricite` |
| Texte d'une carte construit par l'affichage (`texte_effet_carte` : type, action, valeur, durée) | `carte.description_affichee()` (texte de `carte_new.json`, valeurs actuelles), plus coût, munitions restantes, lancements, Persistante |
| `combat.cibles_possibles(carte)` → entités | `combat.cibles_possibles(carte)` → **cases** ; le clic donne déjà une case : plus simple |
| `combat.jouer_carte(carte, cible)` → liste des dégâts (pour les popups) | `combat.jouer_carte(carte, case)` ; les popups se calculent à partir des **nouvelles entrées du journal** (`combat.journal[n:]`) |
| `combat.finir_tour_joueur()` | `combat.finir_tour()` |
| `module.bouclier`, `module.buffs_actifs`, `module.leurre_actif` | `module.statuts[Statut.BOUCLIER]`, `[Statut.INCENDIE]`, `[Statut.LEURRE]`, `[Statut.RENVOI]` |
| `ennemi.bouclier`, `ennemi.buffs_actifs` (débuffs) | `ennemi.statuts[...]` (bouclier, incendie, renvoi) |
| `combat.prochaines_actions_actives(ennemi)`, `previsualiser_cible` | `combat.intentions()` : étape courante, valeur du tour, cible prévue |
| `combat.journal` (`EvenementCarteJouee`, `EvenementActionEnnemi`, `EvenementTour`) | `combat.journal` (`Evenement` typés, avec le détail leurre / renvoi / bouclier / PV perdus / PV restants) |
| `combat.etat` (`EtatCombat`) | `combat.etat` (`EtatCombatNew`) |

**Règle inchangée** (CLAUDE.md) : l'affichage ne contient aucune règle de jeu. Il ne fait que
**mettre en mots et en images** ce que `CombatNew` lui donne : cases valides, intentions,
événements du journal. Les phrases du journal sont de la présentation, elles vont dans
l'affichage (PC) et dans `bridge.py` (web), à partir des mêmes champs.

---

## 4. Proposition d'affichage des nouveautés

Style actuel conservé : pastilles sur les cases, infobulle au survol (PC) ou au tap (web), popups
de dégâts, journal dans la barre latérale.

### 4.1 Cartes en main

```
┌───────────────────┐
│ 1⚡   Laser    ★  │   coût, nom, rareté
│     [image]       │
│ Inflige 6 degats  │   description_affichee() : valeurs actuelles
│ a un ennemi unique│
│ ×2       🔁 2/3   │   ×2 = lancée deux fois (si > 1) ; munitions restantes / de départ
│ PERSISTANTE       │   bandeau si la carte a le mot-clé
└───────────────────┘
```

- **Lancements** : « ×2 » seulement si la carte est lancée plus d'une fois (après une répétition).
- Une carte injouable (électricité, aucune cible) reste grisée, comme aujourd'hui (`peut_jouer`).

### 4.2 Modules du joueur

- Pastille **PV** et pastille **Bouclier** (inchangées).
- Nouvelles petites pastilles, à côté : **Incendie** (rouge, intensité), **Leurre** (présent ou
  non), **Renvoi** (s'il existe un jour côté joueur).
- **Module détruit** : case assombrie avec « DÉTRUIT » (comme aujourd'hui) et, dans l'infobulle,
  le nombre de ses cartes en Hors service.
- Infobulle : nom, PV / PV max, chaque statut en clair (« Bouclier 6 : −1 à la fin du tour
  ennemi », « Incendie 3 : 3 dégâts à la fin du tour ennemi, puis −1 »).

### 4.3 Ennemis

- Pastilles **PV** et **Bouclier** ; nouvelles pastilles **Renvoi** (violette) et **Incendie**.
- **Intention** au-dessus de l'ennemi, d'après `intentions()` :

```
⚔ 6 → Lanceur        attaque PROXIMITE : valeur du tour et module visé
⚔ 7 ×2 → Lanceur     attaque répétée (Le nettoyeur)
⚔ 9 → tous           attaque TOUS_MODULES (Le puzzle, le Boss)
🛡 10                bouclier sur soi
↩ 5 → un allié       renvoi posé sur un allié (cible tirée au moment de jouer)
```

- Infobulle de l'ennemi : son **cycle complet** (« ① attaque ② attaque ③ attaque + bouclier »,
  étape courante en gras) et ses valeurs au tour en cours, pour que le joueur anticipe.

### 4.4 Piles et électricité

Compteurs à côté de la pioche : **Pioche · Défausse · Épuisées · Hors service** (la dernière
seulement si elle n'est pas vide), consultables au clic comme aujourd'hui.

### 4.5 Journal

Une ligne par événement, en clair. Exemples :

- « Tour 3 »
- « Laser → Pat le Pirate : 6 dégâts, 2 absorbés par le bouclier, 4 PV perdus (46 restants) »
- « Pat le Pirate → Lanceur de missiles : 5 dégâts, annulés par le leurre »
- « Laser → Miroir : 6 dégâts, 5 renvoyés, 1 PV perdu (49 restants) »
- « Renvoi → Principal : 5 dégâts, 5 PV perdus (55 restants) »
- « Incendie sur Petit Jean : 4 dégâts, 4 PV perdus (96 restants) »
- « Protéger le vaisseau → Principal : bouclier 6 »
- « Lanceur de missiles détruit : 3 cartes hors service »
- « Victoire » / « Défaite »

### 4.6 Popups

Mêmes popups qu'aujourd'hui (« −4 », « +6 🛡 », « annulé »…), calculés à partir des entrées du
journal ajoutées par la dernière action.

---

## 5. Plan en quatre PR

**Quatre PR successives sur la seule branche `devjeux`** (décision utilisateur, 2026-11-11) : une
PR ouverte à la fois ; après chaque merge, `devjeux` est remise à jour depuis `main` avant la
suivante (règle de `CLAUDE.md`). **Ordre (décision utilisateur) : la version web / iPhone avant la
version PC**, seulement parce que l'utilisateur ne pourra pas tester sur PC ces prochains jours.
**Le PC reste la version de référence** (CLAUDE.md) : la PR 3 le met au niveau, et une
différence entre les deux se corrige en faveur de la spec et du PC. **Le jeu peut être cassé sur `main` entre deux merges**, par
exemple l'affichage qui lit encore l'ancien combat après la PR 1 : c'est accepté (décision
utilisateur). Chaque PR reste testée (`pytest`, et captures ou navigateur pour l'affichage) et
signale dans sa description ce qui ne fonctionne pas encore.

### PR 1 — Gameplay (sans affichage)

- `partie.py` : exemplaires de modules en `ModuleNew` (avec identifiant `M1`, `M2`…), deck
  sauvegardé comme liste `{"id": ..., "module": ...}` ; une **ancienne sauvegarde est
  abandonnée** à la lecture (décision 1).
- Création d'un `CombatNew` à partir de la partie (flottes : décision 4) ; fin de combat : report
  des PV du principal, Argent par ennemi détruit (`ennemis_detruits()`), récompenses.
- `deroulement.py` : mêmes écrans, mêmes transitions, avec le nouveau combat.
- Station et Aventures adaptées (décisions 2 et 3).
- Simulateur de parties complètes basculé sur le nouveau moteur.
- `carte_new.json` : `jouable` à `true` pour les 19 cartes (décision 5), tableau régénéré.
- Tests : `test_partie.py`, `test_deroulement.py`, abandon d'une ancienne sauvegarde.

Après cette PR, l'affichage web et PC lit encore l'ancien combat : **le jeu est cassé** jusqu'à la
PR 2 pour le web et la PR 3 pour le PC (accepté). La description de chaque PR le signale.

### PR 2 — Affichage web / iPhone (`web/bridge.py`, `web/app.js`, `web/style.css`)

- **D'abord une maquette** des éléments du §4 (captures d'un combat au format iPhone), validée par
  l'utilisateur (décision 6), puis le reste de l'affichage.
- Lecture de l'API de `CombatNew` (tableau du §3) par `bridge.py`, sérialisée en JSON ; éléments
  du §4 dans `app.js` / `style.css`.
- Clic : la case touchée est passée directement à `jouer_carte` (`cliquerCase`), avec le flux de
  clics actuel, déjà identique au PC (specs.md §8.3) : sélectionner la carte, puis confirmer sur
  une case vivante du bon camp.
- Vérification dans le navigateur (méthode de `web/CLAUDE.md`), au format iPhone en priorité :
  début de combat, carte sélectionnée et cases valides, renvoi de Miroir, module détruit et Hors
  service, victoire, défaite.

### PR 3 — Affichage PC (`src/ui/fenetre.py`, écrans du parcours touchés)

- Même contenu que le web, lu dans l'API de `CombatNew` ; `_essayer_de_cibler` identique à
  `cliquerCase` de la PR 2.
- Vérification par captures d'écran (méthode de `src/ui/CLAUDE.md`).

### PR 4 — Nettoyage

- Suppression de l'ancien moteur (`carte.py`, `module.py`, `ennemi.py`, `combat.py`, `deck.py`,
  `flotte.py`, `vaisseau.py`, `joueur.py`, `ciblage.py`, une partie de `config_poc.py` et
  `donnees.py`), des anciens `config/cartes.json`, `modules.json`, `ennemis.json`, de l'ancien
  simulateur et de leurs tests.
- Renommage éventuel des `*_new` (à décider : garder les noms, ou `CarteNew` → `Carte`…).
- Migration des brouillons `refonte-*.md` dans les sections numérotées (`combat.md`,
  `modules-cartes.md`…), mise à jour de `CLAUDE.md` et de `specs/refonte.md`.

---

## 6. Points d'attention

- **Taille** : l'essentiel du travail est l'affichage (environ 3 000 lignes entre PC et web).
- **Pas de règle dans l'affichage** : ni calcul de dégâts, ni choix de cible, ni décompte de
  statut. Tout vient de `CombatNew` (cases valides, intentions, journal).
- **Combat abandonné** (« Quitter ») : `CombatNew` travaille sur des copies, la partie n'est pas
  touchée ; rien à faire de plus.
- **Web** : l'état du combat vit dans Pyodide ; `bridge.py` ne fait que le sérialiser. Les cartes
  sont désignées par leur position dans `combat.deck.main`, les cibles par leur case.
- **Équilibrage** : relancer des parties complètes après la PR 1 (Stations comprises) pour caler
  les PV du principal (60) et du Lanceur (20), avec l'accord de l'utilisateur.
