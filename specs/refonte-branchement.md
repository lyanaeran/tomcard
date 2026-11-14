# Branchement de la refonte — proposition

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **Plan validé** (décisions du
§2 et ordre des PR du §5 tranchés le 2026-11-11 ; l'affichage du §4 reste une proposition, à
valider sur maquette). **PR 1 (gameplay) codée le 2026-11-12** (§5.1) ; **PR 2 (web) codée le
2026-11-12** (§5.2) ; **PR 3 (PC) codée le 2026-11-14** (§5.4) ; PR 4 à faire. Décrit comment faire passer le jeu (parcours, sauvegarde, affichage
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

- Infobulle de l'ennemi : **seulement les actions de son prochain tour, une par ligne, sans titre**
  (« ⚔ 2 → Principal », puis « 🛡 6 » sur la ligne suivante), **pas son cycle complet** (décisions
  utilisateur, 2026-11-13, après essai sur iPhone ; la proposition initiale affichait tout le cycle).

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

### 5.1 PR 1 codée (2026-11-12) : ce qui a été fait, choix faits en codant

Fait, testé par `pytest` (aucun affichage) :

- `partie.py` : modules `ModuleNew` (exemplaires `M1`, `M2`…, `EtatModule` supprimé), deck en
  `CartePossedee(id, module)`, format de sauvegarde 2 (specs.md §10.3), ancienne sauvegarde
  abandonnée (`lire_partie`, `SauvegardeObsolete`) ; `combat_depuis_partie` et
  `combat_aventure_asteroides` renvoient un `CombatNew` (refusé si le principal est à 0 PV, garde-fou) ; `reporter_combat` (PV du principal) ;
  Station (`reparer_principal`) et Aventures adaptées (décisions 2 et 3).
- `flotte_new.py` : composition des flottes (décision 4) : `flotte_prime`, `flotte_boss`,
  `flotte_asteroides`, `placer_ennemis` ; le simulateur de combats l'utilise aussi.
- `parcours.py` et `deroulement.py` : mêmes écrans et transitions, sur `ModuleNew` / `CarteNew` /
  `CombatNew`. Les cartes proposées (choix du module, récompenses) sont des exemplaires `CarteNew`
  **déjà rattachés** à l'exemplaire de leur module ; `resoudre_carte_module` et
  `resoudre_fin_combat` prennent la carte choisie (plus son id).
- `carte_new.json` : `jouable` à `true` pour les 19 cartes (décision 5), tableau régénéré.
- Simulateur de parties complètes (`partie_auto.py`, `etudes.py`) sur le nouveau combat et
  `bot_new.py` ; l'ancien bot `bot.py` est supprimé dès maintenant (il ne pouvait plus jouer un
  combat du parcours).

Choix faits en codant, **à valider par l'utilisateur** :

- **Carte de récompense rattachée au module qui l'a proposée** (chaque module propose une carte de
  son pool, §6) ; carte offerte par les Astéroïdes (pool complet, « hors module ») rattachée au
  principal (refonte-modules.md §3.3).
- **Argent du Boss : 5 € au lieu de 10 €** : l'Argent se compte par ennemi détruit
  (`ennemis_detruits()`), le Boss sur deux cases compte pour un (l'ancien moteur comptait ses deux
  cases). Sans effet en jeu aujourd'hui (la partie s'arrête au Boss).
- **Combat de démonstration supprimé** (décision utilisateur, 2026-11-12 : « on ne se sert que du
  parcours ») : `config_poc.py` (combat au hasard sans partie, anciennes flottes, ancien deck de
  départ) et ses tests sont retirés ; ses flottes sont remplacées par `flotte_new.py`. Les PR 2
  et 3 retirent le mode démo de l'affichage : `nouveau_combat`, `fin_combat_victoire` et la
  branche démo d'`etat_deck` dans `web/bridge.py`, les `window.*` de démonstration de
  `web/app.js`, le `creer_combat_poc()` par défaut de `src/ui/fenetre.py`.
- **Mode test supprimé** (décision utilisateur, 2026-11-12) : `config_poc.MODE_TEST` (PV gonflés,
  Laser à 20) n'est pas repris par le parcours branché et a été retiré de l'ancien moteur.
- **Déplacer le principal** lève une erreur (avant : à la charge de l'écran de ne jamais le
  demander) ; **ajouter une carte rattachée à un module absent** aussi.
- **Astéroïdes : le principal garde toujours au moins 1 PV** (décision utilisateur, 2026-11-12).
  Avant, les chocs pouvaient le mettre à 0 et le combat suivant commençait avec un principal
  détruit, sans que `CombatNew` déclare la défaite.

Le jeu (PC et web) **ne fonctionne plus** tant que les PR 2 et 3 ne sont pas faites : leurs écrans
lisent encore l'ancien combat et l'ancien format de partie (accepté, §5).

### PR 2 — Affichage web / iPhone (`web/bridge.py`, `web/app.js`, `web/style.css`)

- **En premier** : retirer de `web/bridge.py` les imports de l'ancien gameplay supprimé
  (`config_poc`, `EtatModule`, `reparer_module`…) et le mode démo, pour que le web se recharge.

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

### 5.2 PR 2 codée (2026-11-12) : ce qui a été fait, écarts avec le §4 (à valider)

Fait, testé dans Chromium au format iPhone 13 paysage, avec Pyodide (parcours complet et scénarios
dédiés) : `web/bridge.py` réécrit sur `CombatNew` et le nouveau format de partie, mode démo
supprimé ; `web/app.js` / `style.css` : éléments du §4, cases valides lues dans le gameplay
(`cibles_possibles`), textes de carte lus dans `carte_new.json` (`description_affichee`), Station
(Réparer = principal, sans sélection), Astéroïdes (plus de choix de module), Trois lunes, Police,
récompenses rattachées à leur module, ancienne sauvegarde effacée de `localStorage` si elle était
en cours (`partie.lire_sauvegarde`, même règle que le PC).

**Écarts avec la proposition du §4, choisis en voyant les captures** (intention courte avec
pastille 🎯 et journal sans « Carte X jouée » **validés par l'utilisateur le 2026-11-13** « pour
le moment » ; textes affichés accentués, journal compris, à sa demande) :

- **Intention courte dans la case de l'ennemi** (« ⚔7×2 », « ⚔5 tous », « 🛡10 », « ↩5 ») au
  lieu de « ⚔ 7 ×2 → Lanceur » : la version longue débordait sur la rangée suivante et sur les
  pastilles du vaisseau, en iPhone paysage. Le **module visé** porte à la place une pastille 🎯, et
  l'infobulle (tap) donne le détail : « Visé au prochain tour par : Le nettoyeur : ⚔ 7 ×2 » côté
  module, « ⚔ 7 ×2 → Lanceur de missiles » côté ennemi : les actions du prochain tour, une par
  ligne, sans titre ni cycle complet (décisions utilisateur du 2026-11-13).
- **Infobulles de statut sobres** : « 🛡 Bouclier 6 », « 🔥 Incendie 3 », « ↩ Renvoi 5 », « 🎭
  Leurre », et « Persistante » pour une carte ; aucune règle n'est écrite (ni l'extinction « −1 à
  la fin du tour ennemi », ni l'effet du leurre ou de Persistante), pour ne pas recopier une règle
  de jeu dans l'affichage.
- **Carte en main** : illustration, nom en bas, coût, munitions « 2/2 », « ×2 » si lancée plus
  d'une fois, bandeau PERSISTANTE ; grisée si elle n'est pas jouable maintenant. Description
  complète dans le panneau qui s'ouvre quand on la sélectionne (avec munitions, lancements, module).
- **Cases valides en vert** quand une carte est sélectionnée (cases données par le gameplay).
- **Compteurs** sous la forme « Tour 2 · Pioche 6 · Défausse 0 · Épuisées 0 · Hors service 2 ».
- **Journal** : une ligne par effet (la ligne « Carte X jouée » n'est plus affichée, ses effets le
  sont) ; phrases du §4.5.
- **Popups** : « −4 », « −1 (🛡4) » (PV perdus et part absorbée par le bouclier), « bloqué 🛡4 »
  (tout absorbé), « +4 🛡 », « ↩ 5 » (tout renvoyé), « annulé » (leurre), « +8 » (réparation) ;
  plusieurs popups sur la même case sont décalés dans le temps (0,3 s), sans retarder les autres
  cases.
- **PV hors combat** (accueil, Station, Aventures) : ceux du prochain combat, donnés par le
  gameplay (`ModuleNew.pv_au_prochain_combat` : PV sauvegardés pour le principal, PV max pour un
  secondaire).

Non vérifié en capture : la pastille Leurre et le bandeau Persistante (aucune carte actuelle n'est
Persistante). Le PC (`python main.py`) ne démarre toujours pas : PR 3.

### 5.3 Corrections après relecture du code (2026-11-13)

Relecture complète demandée par l'utilisateur ; corrections faites dans une PR à part, avant la PR 3.

- **Fin de combat enregistrée en une fois** (deux bugs : partie bloquée après une défaite si on
  quittait avant « Continuer » ; Argent gagné deux fois en rechargeant sur l'écran de récompense).
  `deroulement.conclure_combat` termine la partie dès la défaite, et note les cartes proposées
  dans `partie.recompense` ; `ecran_de_reprise` renvoie le nouvel écran `Ecran.RECOMPENSE` tant
  que le choix n'est pas fait (`recompense_en_attente`). La victoire sur le Boss termine la partie
  dès `resoudre_fin_combat` (on ne peut pas le rejouer). **La PR 3 doit gérer `Ecran.RECOMPENSE`
  dans `main.py:_aller_a`.**
- **Station** : paliers de mise à jour appliqués (décision utilisateur) et actions sans effet
  refusées sans payer (proposition), cf. specs.md §2.2.
- **Sauvegarde** : une carte ou un module disparu de `config/`, ou une sauvegarde abîmée (texte
  illisible, champ manquant), fait abandonner la partie au lieu de planter (proposition :
  effacée, sauf si on peut y lire qu'elle était TERMINEE) ; deux cartes de même id sont refusées
  au chargement.
- **Web** : accents sur tous les écrans, nom de joueur jamais interprété comme du HTML.
- **Outils** : `outils/test_web/essais.js` (essais dans Chromium, cf. `web/CLAUDE.md`) et tests
  lancés par GitHub à chaque PR (`.github/workflows/tests.yml` : `pytest`, syntaxe du web).

Laissé de côté, **à décider par l'utilisateur** :

- **Combat en cours non sauvegardé sur le web** : « Quitter » ou un rechargement fait recommencer
  le combat avec un nouveau tirage d'ennemis (on peut relancer jusqu'à un adversaire facile).
- **Police avec un deck vide** (possible après plusieurs « Bricoler » ou confiscations) : le tirage
  de la carte plante. Il faut une règle : ne pas proposer la Police, ou interdire de vider le deck.

### PR 3 — Affichage PC (`src/ui/fenetre.py`, écrans du parcours touchés)

- **En premier** : retirer de `src/ui/` les imports de l'ancien gameplay supprimé (`config_poc`
  dans `fenetre.py`, `EtatModule` dans les écrans…) et le mode démo, pour que `python main.py`
  redémarre.

- Même contenu que le web, lu dans l'API de `CombatNew` ; `_essayer_de_cibler` identique à
  `cliquerCase` de la PR 2.
- Vérification par captures d'écran (méthode de `src/ui/CLAUDE.md`).

### 5.4 PR 3 codée (2026-11-14) : ce qui a été fait, écarts avec le web (à valider)

`python main.py` redémarre : `main.py` et `src/ui/` ne lisent plus que le moteur de la refonte
(vérifié par `tests/test_architecture.py`). Le mode démo (combat sans partie) est supprimé.

- **Combat** (`src/ui/fenetre.py`) : même contenu que le web, lu dans `CombatNew`.
  - Cartes en main : coût, munitions « restantes/de départ », « ×2 » si lancée plus d'une fois,
    bandeau PERSISTANTE, carte assombrie si `peut_jouer` est faux. **Survol d'une carte** :
    infobulle avec sa description (valeurs actuelles), ses détails et son module.
  - Cases : pastilles PV et Bouclier, puis Incendie (orange), Renvoi (violet), Leurre (cyan,
    « L ») seulement s'ils sont actifs ; **anneau rouge** sur un module visé au prochain tour ;
    intention courte en bas de la case de l'ennemi ; module détruit : « Détruit · N HS ».
  - Carte sélectionnée : **contour vert** sur les cases où elle peut être confirmée.
  - `_essayer_de_cibler` = `cliquerCase` : une case du bon camp, valide d'après
    `cibles_possibles` ; sinon le clic est ignoré et la carte reste sélectionnée. Une entité sur
    deux cases (principal, Boss) : on prend celle de ses cases que le gameplay accepte.
  - Infobulles (survol) : mêmes lignes que le tap du web (ennemi : actions du prochain tour, une
    par ligne, sans titre ni cycle).
  - Sous les boutons : « Tour N », Pioche, Défausse, Épuisées, Hors service (si non vide).
  - Popups et journal calculés à partir des entrées du journal du gameplay
    (`src/ui/textes_combat.py`, sans pyglet, testé par `tests/test_textes_combat.py`).
  - Bouton Deck pendant un combat : toutes les cartes du combat, toutes piles confondues.
- **Parcours** : Station (Réparer vise toujours le principal, sans sélection ; refus « Argent
  insuffisant ! » / « Déjà au maximum ! » d'après `ResultatStation`), Astéroïdes (plus de choix de
  module : les chocs touchent le principal), Police et Trois lunes (cartes désignées par carte et
  module), récompenses déjà rattachées à leur module, écran Deck avec le module de chaque carte.
- **`Ecran.RECOMPENSE`** géré dans `main.py:_aller_a` ; la partie est sauvegardée dès la fin du
  combat (reprise sur l'écran de récompense, jamais sur le combat déjà joué).
- **Gameplay** : `CombatNew.modules_vises(effet)` (modules touchés par un effet d'intention),
  utilisé par le PC et par `web/bridge.py` à la place de leur propre calcul.
- **Popups (PC et web, revue de la PR 68)** : une attaque qui ne fait perdre aucun PV dit ce qui
  l'a arrêtée, même quand plusieurs protections se la partagent (« renvoi 5 · bloqué (1) » sur PC,
  « ↩ 5 bloqué 🛡1 » sur le web, jamais « -0 ») ; une réparation de 0 PV ne donne pas de popup.
- **Textes affichés du PC accentués** (« Réparer », « Astéroïdes », « DÉFAITE »…), comme le web.

**Écarts avec le web, à valider (propositions)** :

1. **Ni emoji ni symbole sur PC** (ils dépendent de la police de la machine, non vérifiable sur
   Windows ; revue de la PR 68) : des mots à la place. Intention dans la case : « Att. 7×2 »,
   « Att. 9 tous », « Bouclier 10 », « Renvoi 5 » ; infobulle : « Attaque 7 ×2 → Lanceur de
   missiles », « Renvoi 5 → un allié » ; popups « +6 bouclier », « bloqué (6) »,
   « -4 (bouclier 2) », « renvoi 5 » ; anneau rouge au lieu de « 🎯 » ; pastille « L » au lieu de
   « 🎭 ». Restent « × », « → », et « ⚡ », « ★ » déjà utilisés par le PC avant la refonte.
2. **Plusieurs popups sur la même case** : empilés vers le haut (le web les décale dans le temps).
3. **Fin de combat** : la fenêtre de combat se ferme dès la victoire ou la défaite, pour ouvrir
   l'écran de fin (comportement PC inchangé) ; le web affiche une bannière « Continuer ».

**Vérifié** : captures sous Xvfb (Linux) de l'écran de combat (Prime à 2 ennemis, Boss, carte
armée, clics du mauvais camp ignorés, Ligne arrière sur le Boss, module détruit, tour ennemi,
journal, deck) et de chaque écran du parcours, avec contrôle de la partie après chaque clic ; un
parcours de bout en bout par `main.py` (nouvelle partie → module → carte → combat gagné → quitter
sur la récompense → reprise → combat perdu). **Non vérifié** : macOS et Windows (pas de machine) ;
sous Linux, la police par défaut n'a pas le glyphe « ⚡ » (coût des cartes, affiché en carré sur
les captures), déjà utilisé par le PC avant la refonte.

### PR 4 — Nettoyage

- Suppression de l'ancien moteur (`carte.py`, `module.py`, `ennemi.py`, `combat.py`, `deck.py`,
  `flotte.py`, `vaisseau.py`, `joueur.py`, `ciblage.py`, une partie de
  `donnees.py`), des anciens `config/cartes.json`, `modules.json`, `ennemis.json` et de leurs
  tests. (Le simulateur est déjà passé sur le nouveau moteur à la PR 1 et l'ancien bot supprimé :
  il ne reste plus d'ancien simulateur à retirer.)
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
