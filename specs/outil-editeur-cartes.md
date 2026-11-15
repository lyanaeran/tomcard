# Outil d'administration : éditeur de cartes — spécification

*Document de conception d'outil, hors numérotation (cf. [specs.md](specs.md)). **Spécification
validée, rien n'est codé** (décisions utilisateur du 2026-11-15, §9). Les détails marqués
**(proposition)** restent à confirmer en cours de réalisation.*

---

## 1. Objectif

Un petit outil, utilisable **sur iPhone**, pour **consulter et modifier les cartes** du jeu sans
ordinateur, puis **envoyer le résultat** pour qu'il soit intégré au jeu.

- **Écran 1** : toutes les cartes dans un tableau, lisible en **paysage sur iPhone 17**.
- **Écran 2** : le détail d'une carte, toutes ses valeurs modifiables ; « Fermer » ramène à
  l'écran 1. Le bouton **+** de l'écran 1 ouvre ce même écran pour une nouvelle carte.
- Les modifications sont **sauvées sur l'appareil** et retrouvées en revenant sur l'outil.
- Les cartes **modifiées par rapport au jeu** (`config/cartes.json`) sont **signalées**.
- Un bouton **Copier** met le fichier `cartes.json` modifié dans le presse-papiers (§6).
- Accès par un **bouton « Admin » temporaire**, réservé à certains joueurs (§8).

**Hors périmètre** : l'outil ne change pas le jeu. Les cartes modifiées ne sont pas jouées tant
que le fichier exporté n'a pas été intégré au dépôt (§7).

---

## 2. Où le faire : dans la version web (décision utilisateur)

L'outil est fait **dans la version web** (`index.html` + `src/web/`). Il sert sur iPhone (Safari)
**et** sur Mac / PC dans un navigateur. **Le jeu PC (pyglet) n'a pas d'éditeur** : son bouton
« Admin » **ouvre la page web de l'outil dans le navigateur** (§8).

Pourquoi : les champs de saisie, les listes et le presse-papiers sont natifs en HTML, alors qu'il
faudrait les construire à la main dans pyglet.

**Règles du projet respectées** :

- **Aucune règle de jeu en JavaScript** (CLAUDE.md) : la **validation** d'une carte et l'**aperçu
  de sa description** sont faits par le code Python du jeu, déjà chargé dans la page par Pyodide
  (`Carte.depuis_dict`, `Carte.description_affichee`), via de nouvelles fonctions de
  `src/web/bridge.py`. Les **listes de choix** (raretés, catégories, cibles, natures, portées,
  modules) viennent aussi du Python et des données du jeu, pour qu'une valeur ajoutée au jeu
  apparaisse seule dans l'outil.
- L'outil est un écran de plus dans `index.html` / `app.js` / `style.css`, avec le cache-busting
  habituel (`VERSION_CACHE`, `?v=`).

---

## 3. Écran 1 : liste des cartes

### 3.1 Place disponible

iPhone 17, en paysage : **874 × 402 points**. Après les marges de sécurité (Dynamic Island d'un
côté, bord arrondi de l'autre, barre d'accueil en bas), il reste environ **760 × 360 points**. Avec
une police de 13 à 14 points et des lignes de 32 points, une barre d'outils en haut et l'en-tête
du tableau, on voit **9 à 10 cartes à la fois** ; le tableau défile verticalement, **jamais
horizontalement**.

### 3.2 Colonnes (décision utilisateur : 7 colonnes)

| Colonne | Largeur | Contenu | Exemple |
|---|---|---|---|
| État | 24 | pastille (§5) | ● |
| Nom | 160 | nom de la carte (20 caractères au plus aujourd'hui) | Laser lourd |
| Coût | 40 | électricité | 1 |
| Rareté | 80 | Base, Commune, Rare, Légendaire | Commune |
| Cible | 120 | cible de la carte | Ennemi Unique |
| Module | 110 | module(s) de la carte (§4.7) | Principal |
| Valeurs | 200 | valeurs nommées, abrégées, tronquées | degats 12 |

Total : environ **735 points**, dans les 760 disponibles. Id, image, catégorie, munitions,
lancements, Persistante, jouable, revue, description et effets restent dans l'écran 2.

**En portrait** (402 points de large), le tableau se réduit à 4 colonnes (État, Nom, Coût,
Valeurs) ; l'outil reste utilisable, mais le paysage est le mode prévu.

### 3.3 Barre d'outils (en haut)

```
[ ← Jeu ]   Cartes (19 · 2 modifiées · 1 nouvelle)   [ Toutes ▾ ]   [ + ]   [ Copier ]
```

- **← Jeu** : retour à l'écran du jeu d'où l'on vient.
- **Compteur** : nombre de cartes, de cartes modifiées et de nouvelles.
- **Filtre** (décision utilisateur) : Toutes / Modifiées seulement / par module (Principal,
  Lanceur de missiles…) / Supprimées.
- **+** : nouvelle carte (§4.8).
- **Copier** : §6.2.

### 3.4 Interactions

- **Toucher une ligne** : ouvre l'écran 2 de cette carte.
- **Toucher un en-tête de colonne** (décision utilisateur) : trie par cette colonne ; un second
  toucher inverse l'ordre. Tri par défaut : ordre du fichier `cartes.json`, nouvelles cartes à la
  fin.
- **Carte supprimée** (§4.6) : ligne grisée, nom barré.

---

## 4. Écran 2 : détail d'une carte

Un formulaire qui défile verticalement, par blocs. Chaque modification est **sauvée aussitôt**
sur l'appareil (pas de bouton « Enregistrer »).

```
[ Fermer ]          Laser lourd  (CRT_47) ●                [ Annuler mes modifications ]
──────────────────────────────────────────────────────────────────────────────────────
⚠ Valeur 'degat' citée par un effet mais absente des valeurs            (si erreur)
Aperçu : « Inflige 12 dégâts à un ennemi unique »
```

### 4.1 Les champs

| Bloc | Champ | Saisie |
|---|---|---|
| Identité | Id | texte ; **non modifiable** pour une carte du jeu, proposé pour une nouvelle carte (§4.8) |
| | Nom | texte |
| | Image | **liste** des images de `assets/cartes/` **ou valeur libre** (avec la vignette) |
| Classement | Rareté | **liste** (Base, Commune, Rare, Légendaire) ou libre |
| | Catégorie | **liste** (Attaque, Defense, Reparation, Buff, Debuff, Outils, Controle) ou libre |
| | Cible | **liste** (Ennemi Unique, Ennemi Colonne, Ennemi Avant, Ennemi Arriere, Ennemi Tous, Module Unique, Module Principal, Module Avant, Module Tous) ou libre |
| Module | Modules | cases à cocher : les modules de `config/modules.json` (§4.7) |
| Coût et usage | Coût | nombre |
| | Munitions | nombre, ou vide = illimitées |
| | Lancements | nombre (1 d'ordinaire) |
| | Jouable | **liste à trois choix : Oui, Non, Supprimée** (§4.6) |
| | Persistante, Revue (`refonte`) | interrupteurs oui / non |
| Texte | Description | texte sur plusieurs lignes, avec les valeurs entre accolades (`{degats}`) ; **aperçu** en dessous, valeurs remplacées |
| Valeurs | Valeurs nommées | une ligne par valeur : nom (texte) et nombre ; boutons « + valeur » et « supprimer » |
| Effets | un bloc par effet | voir §4.2 ; boutons « + effet » et « supprimer » |

### 4.2 Les effets

Chaque effet est un petit bloc :

| Champ | Saisie |
|---|---|
| Nature | **liste** (DEGATS, BOUCLIER, REPARATION, INCENDIE, VULNERABILITE, REDUCTION_DEGATS, ANNULATION_PROCHAINE_ATTAQUE, REDIRECTION_CIBLE, GAIN_ELECTRICITE, PIOCHE, REPETITION) ou libre, avec un libellé en clair (« Dégâts », « Bouclier »…) |
| Valeur | **liste des valeurs nommées de la carte** ou libre ; vide pour une nature sans valeur (Leurre) |
| Portée | **liste** (Cible, Autres ennemis, Colonne avant ennemie, Colonne arrière ennemie) |
| Durée | liste des valeurs nommées, ou vide (seulement pour Vulnérabilité, Réduction de dégâts, Tir allié) |
| Filtre (Répétition) | carte visée (liste des cartes, par nom et id), rareté, catégorie |

### 4.3 Listes avec valeur libre

Pour chaque champ à liste : une **liste déroulante** dont le dernier choix est **« Autre… »**, qui
fait apparaître un champ texte pour une valeur libre (proposition, plus lisible sur iPhone qu'une
suggestion pendant la frappe). Une valeur libre inconnue du jeu est acceptée et sauvée, mais
signalée par la validation (§4.5).

### 4.4 Valeurs modifiées

Dans une carte du jeu, chaque **champ modifié** est **surligné**, avec la **valeur du jeu** en petit
dessous (« jeu : 6 »). Un petit bouton ↺ à côté du champ remet la valeur du jeu.

### 4.5 Validation

À chaque modification, la carte est vérifiée **par le code du jeu** (`Carte.depuis_dict`, comme au
chargement de `config/cartes.json`) :

- **Erreurs** en tête de l'écran, en rouge, en clair (clé manquante, valeur citée mais absente,
  coût négatif, portée ennemie sur une carte qui vise un module, module inconnu…).
- Une carte en erreur **reste sauvée** (on peut finir plus tard), mais elle est marquée ⚠ dans la
  liste et **bloque la copie** (§6.2), pour ne jamais envoyer un fichier que le jeu refuserait.
- **Aperçu** de la description avec les valeurs, calculé par le jeu.

### 4.6 Boutons et suppression

- **Fermer** : retour à l'écran 1, à la même position dans la liste.
- **Annuler mes modifications** (carte du jeu) : la carte redevient celle du jeu, après
  confirmation. Pour une nouvelle carte : la retire de l'outil, après confirmation.
- **Supprimer une carte** (décision utilisateur) : on ne la retire pas du fichier, on passe son
  champ **Jouable à « Supprimée »**. La carte reste dans `cartes.json`, le jeu ne la propose
  jamais (comme une carte non jouable), et on peut la remettre à Oui ou Non à tout moment. Voir
  §10 : le jeu doit accepter cette troisième valeur.

### 4.7 Module de la carte (décision utilisateur : dans `cartes.json`)

Aujourd'hui, c'est chaque module de `config/modules.json` qui liste ses cartes
(`"cartes": ["CRT_7", …]`). **Décision utilisateur** : le module est porté **par la carte**, dans
`config/cartes.json`, par un champ **`"modules"`**, une **liste** d'ids de module, par exemple
`"modules": ["MOD_1"]` (une liste, parce qu'une carte peut être commune à plusieurs modules,
modules-cartes.md). La liste `cartes` disparaît de `modules.json`. Voir §10 : changement du jeu
à faire avant l'outil.

Dans l'écran 2 : une case à cocher par module de `config/modules.json`. Une carte sans module
n'est proposée nulle part en jeu (signalé, mais pas une erreur).

### 4.8 Nouvelle carte (bouton +)

- **Id proposé** : le premier `CRT_n` libre (aujourd'hui `CRT_51`), modifiable.
- **Champs pré-remplis** (proposition) : rareté Commune, catégorie Attaque, cible Ennemi Unique,
  coût 1, lancements 1, munitions illimitées, jouable Oui, revue oui, aucun module, une valeur
  `degats` à 0 et un effet Dégâts qui l'utilise. La carte est ainsi valide dès le départ et on ne
  fait que l'ajuster.
- Une nouvelle carte est marquée **« Nouvelle »** dans la liste.

---

## 5. Repérer les cartes modifiées

L'outil compare chaque carte à celle de **`config/cartes.json` du jeu chargé** (le fichier de
référence, déjà présent dans la page) :

| État | Pastille (écran 1) | Sens |
|---|---|---|
| Inchangée | aucune | identique au jeu |
| **Modifiée** | ● orange | au moins un champ diffère du jeu |
| **Nouvelle** | ✚ vert | id absent du jeu |
| **En erreur** | ⚠ rouge | refusée par la validation (§4.5), affichée avant les autres pastilles |
| **Le jeu a changé** | ⇄ violet | la carte a été modifiée dans le jeu depuis ta modification locale (voir ci-dessous) |

Une carte supprimée (Jouable « Supprimée ») est en plus grisée et barrée (§3.4).

- La comparaison se fait **sur le contenu**, pas sur la date : une modification annulée à la main
  (retour à la valeur d'origine) rend la carte à nouveau « Inchangée ».
- **Le jeu a changé** : quand on modifie une carte, l'outil garde une copie de la version du jeu à
  ce moment-là. Si, plus tard, `config/cartes.json` a changé pour cette carte (nouvelle version du
  jeu), l'outil le signale ; l'écran 2 montre alors la version du jeu et la tienne, et propose de
  garder la tienne ou de reprendre celle du jeu. Évite d'écraser sans le voir un changement fait
  entre-temps dans le dépôt.

---

## 6. Sauvegarde locale et export

### 6.1 Sauvegarde sur l'appareil

- Dans le `localStorage` du navigateur, sous une clé propre à l'outil (ex.
  `space_fight_editeur_cartes`), séparée des parties et des profils.
- **Seules les différences** sont gardées : les cartes modifiées ou nouvelles (contenu complet de
  la carte, plus la copie de la version du jeu du §5). Les cartes inchangées viennent toujours du
  jeu.
- Rechargée à chaque ouverture de l'écran 1.
- Limite connue : le `localStorage` est propre à l'appareil **et** au navigateur (Safari sur
  iPhone ≠ Chrome sur Mac) ; pas d'import dans la première version (§11).

### 6.2 Export : copier le fichier (décision utilisateur)

Un seul bouton, **Copier**, désactivé tant qu'une carte est en erreur : il met le fichier
**`config/cartes.json` complet** dans le **presse-papiers** (toutes les cartes du jeu, les
modifications appliquées, les nouvelles cartes à la fin, dans le même format), avec un message
« Fichier copié (2 cartes modifiées, 1 nouvelle) ». On le colle ensuite dans un message ou dans la
conversation avec l'agent.

Le presse-papiers du navigateur demande une page sécurisée : c'est le cas sur GitHub Pages
(https) et en local (`localhost`).

---

## 7. Intégrer un export dans le jeu

1. L'utilisateur colle le fichier copié dans la conversation avec l'agent (ou l'envoie).
2. L'agent remplace `config/cartes.json`, régénère le tableau `config/cartes.md`
   (`python -m outils.tableau_cartes`), lance `pytest`, et signale ce qui a changé, en particulier
   les tests qui lisent une valeur de carte.
3. PR habituelle sur `devjeux`. Après le merge et le déploiement, les modifications locales de
   l'outil deviennent « Inchangées » toutes seules, puisque le jeu les contient.

---

## 8. Accès : bouton « Admin »

- **Réservé à certains joueurs** (décision utilisateur) : le bouton n'apparaît que si le joueur
  choisi s'appelle **thomas**, **tom** ou **lyan**, **quelle que soit la casse** (« Thomas »,
  « TOM »…). Il est donc sur l'**écran d'accueil du joueur** (après le choix du joueur), pas sur
  l'écran de sélection. La liste des noms est une constante, à retirer avec le bouton.
- **Web** : le bouton ouvre l'écran 1 ; « ← Jeu » ramène à l'accueil du joueur.
- **PC** (décision utilisateur) : même bouton, mêmes noms, sur l'accueil du joueur
  (`src/ui/ecran_accueil_joueur.py`) ; il **ouvre la page web de l'outil dans le navigateur**
  (module `webbrowser` de Python). **Adresse (proposition)** : la version publiée sur GitHub
  Pages (constante, à régler une fois) ; elle demande une connexion et montre les cartes de la
  version publiée de `main`, pas d'un dépôt local modifié.
- **Temporaire** : bouton, condition sur les noms et ouverture du navigateur sont regroupés pour
  être retirés facilement.

---

## 9. Décisions utilisateur (2026-11-15)

| # | Question | Décision |
|---|---|---|
| 1 | Colonnes de l'écran 1 | État, Nom, Coût, Rareté, Cible, Module, Valeurs (§3.2) |
| 2 | Version PC | Web seulement pour l'éditeur ; le jeu PC a un bouton Admin qui ouvre la page web dans le navigateur (§2, §8) |
| 3 | Bouton Admin | Visible seulement pour les joueurs thomas, tom ou lyan, quelle que soit la casse (§8) |
| 4 | Module | Dans `cartes.json`, champ `modules` (liste) sur chaque carte ; la liste `cartes` de `modules.json` disparaît (§4.7, §10) |
| 5 | Export | Copier le fichier `cartes.json` complet dans le presse-papiers, seulement (§6.2) |
| 6 | Suppression | Le champ Jouable prend une troisième valeur, « Supprimée » ; la carte reste dans le fichier (§4.6, §10) |
| 7 | Options | Tri par colonne et filtre dans la première version ; « Dupliquer » et « Tout effacer » plus tard (§11) |

---

## 10. Changements du jeu à faire avant l'outil

Deux décisions changent le format des données du jeu. **Faits le 2026-11-15** (même PR que
l'outil), avec les tests et la mise à jour de `modules-cartes.md` §12 :

1. **Module porté par la carte** : champ `"modules": [...]` dans chaque carte de
   `config/cartes.json`, rempli à partir des listes actuelles de `config/modules.json`, qui
   perdent leur champ `cartes`. Le chargement (`charger_cartes`, `charger_modules`) et la
   recherche des cartes d'un module (`parcours.py` : récompenses, choix de module) lisent le
   nouveau champ ; un module inconnu dans une carte est refusé au chargement. Les tableaux
   générés `config/cartes.md` (nouvelle colonne Modules) et `config/modules.md` suivent. Dans le
   code, `Module.cartes` est gardé mais **calculé** par `charger_modules` ; l'ordre des cartes
   reste celui de `cartes.json`, identique aux anciennes listes.
2. **Jouable à trois valeurs** : Oui, Non, Supprimée, sous forme de textes `"oui"`, `"non"`,
   `"supprimee"` au lieu de `true` / `false` (pour ne pas mélanger booléens et texte dans le même
   champ ; l'ancien format booléen est refusé au chargement). Le jeu traite « Supprimée » comme « Non » : jamais proposée, jamais
   jouée. Les 19 cartes actuelles passent à `"oui"`.

---

## 11. Plus tard (hors première version)

- **Dupliquer** une carte, **Tout effacer** les modifications locales (décision utilisateur :
  plus tard).
- **Autres façons d'exporter** : feuille de partage d'iOS, résumé lisible des changements ;
  **import** d'un fichier exporté (pour passer d'un appareil à l'autre).
- **« Tester en jeu »** : jouer la prochaine partie avec les cartes modifiées de l'appareil (le web
  charge `config/cartes.json` dans Pyodide ; il suffirait d'y écrire la version modifiée), à
  garder séparé pour ne pas jouer sans le savoir avec des cartes non officielles.
- **Même outil pour les modules et les ennemis** (même structure : tableau, détail, copie).
