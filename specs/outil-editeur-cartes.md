# Outil d'administration : éditeur de cartes — spécification

*Document de conception d'outil, hors numérotation (cf. [specs.md](specs.md)). **Proposition, rien
n'est codé** (2026-11-15). Les points marqués **(proposition)** sont à valider ; les questions
ouvertes sont au §9.*

---

## 1. Objectif

Un petit outil, utilisable **sur iPhone**, pour **consulter et modifier les cartes** du jeu sans
ordinateur, puis **envoyer le résultat** pour qu'il soit intégré au jeu.

- **Écran 1** : toutes les cartes dans un tableau, lisible en **paysage sur iPhone 17**.
- **Écran 2** : le détail d'une carte, toutes ses valeurs modifiables ; « Fermer » ramène à
  l'écran 1. Le bouton **+** de l'écran 1 ouvre ce même écran pour une nouvelle carte.
- Les modifications sont **sauvées sur l'appareil** et retrouvées en revenant sur l'outil.
- Les cartes **modifiées par rapport au jeu** (`config/cartes.json`) sont **signalées**.
- Un bouton **Exporter** envoie le fichier modifié (§6).
- Accès par un **bouton « Admin » temporaire** dans le jeu.

**Hors périmètre** : l'outil ne change pas le jeu. Les cartes modifiées ne sont pas jouées tant
que le fichier exporté n'a pas été intégré au dépôt (§7). Une option « tester en jeu » est
évoquée au §8.

---

## 2. Où le faire : dans la version web (proposition)

L'outil est fait **dans la version web** (`index.html` + `src/web/`), pas dans la version PC
(pyglet).

| | Version web | Version PC (pyglet) |
|---|---|---|
| iPhone | oui (Safari) | non |
| Mac / PC | **oui, dans n'importe quel navigateur** (même page) | oui |
| Champs de saisie, listes, clavier | natifs (HTML) | à construire à la main dans pyglet, beaucoup plus de travail |
| Sauvegarde locale | `localStorage`, déjà utilisé par le jeu web | fichier dans `saves/` |
| Export | presse-papiers, feuille de partage iOS, téléchargement | presse-papiers seulement |

Le web couvre donc iPhone **et** Mac / PC (ouvrir la version web dans un navigateur : GitHub Pages,
ou en local `python -m http.server` puis `index.html`). **Proposition : pas de version pyglet** de
l'outil. Le bouton « Admin » n'existe que dans la version web.

**Règles du projet respectées** :

- **Aucune règle de jeu en JavaScript** (CLAUDE.md) : la **validation** d'une carte et l'**aperçu
  de sa description** sont faits par le code Python du jeu, déjà chargé dans la page par Pyodide
  (`Carte.depuis_dict`, `Carte.description_affichee`), via de nouvelles fonctions de
  `src/web/bridge.py`. Les **listes de choix** (raretés, catégories, cibles, natures, portées)
  viennent aussi du Python (`src/gameplay/carte.py`), pour qu'une valeur ajoutée au jeu apparaisse
  seule dans l'outil.
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

### 3.2 Colonnes (proposition : 7)

| Colonne | Largeur | Contenu | Exemple |
|---|---|---|---|
| État | 24 | pastille de modification (§5) | ● |
| Nom | 160 | nom de la carte (20 caractères au plus aujourd'hui) | Laser lourd |
| Coût | 40 | électricité | 1 |
| Rareté | 80 | Base, Commune, Rare, Légendaire | Commune |
| Cible | 120 | cible de la carte | Ennemi Unique |
| Module | 110 | module(s) qui la proposent (§4.7) | Principal |
| Valeurs | 200 | valeurs nommées, abrégées, tronquées | degats 12 |

Total : environ **735 points**, dans les 760 disponibles.

**Laissés à l'écran 2** : id, image, catégorie, munitions, lancements, Persistante, jouable,
refonte, description, effets. La catégorie suit presque toujours la cible et la nature des effets
(Attaque, Défense…) ; elle peut remplacer « Module » si tu préfères (§9, question 1).

**En portrait** (402 points de large), le tableau se réduit à 4 colonnes (État, Nom, Coût,
Valeurs) ; l'outil reste utilisable, mais le paysage est le mode prévu.

### 3.3 Barre d'outils (en haut)

```
[ ← Jeu ]   Cartes (19 · 2 modifiées · 1 nouvelle)   [Tous ▾]   [ + ]   [ Exporter ]
```

- **← Jeu** : retour au jeu, à l'écran d'où l'on vient.
- **Compteur** : nombre de cartes, de cartes modifiées et de nouvelles.
- **Filtre** (proposition) : Toutes / Modifiées seulement / par module.
- **+** : nouvelle carte (§4.8).
- **Exporter** : §6.

### 3.4 Interactions

- **Toucher une ligne** : ouvre l'écran 2 de cette carte.
- **Toucher un en-tête de colonne** (proposition) : trie par cette colonne ; un second toucher
  inverse l'ordre. Tri par défaut : ordre du fichier `cartes.json`, nouvelles cartes à la fin.

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
| Coût et usage | Coût | nombre |
| | Munitions | nombre, ou vide = illimitées |
| | Lancements | nombre (1 d'ordinaire) |
| | Persistante, Jouable, Revue (`refonte`) | interrupteurs oui / non |
| Texte | Description | texte sur plusieurs lignes, avec les valeurs entre accolades (`{degats}`) ; **aperçu** en dessous, valeurs remplacées |
| Valeurs | Valeurs nommées | une ligne par valeur : nom (texte) et nombre ; boutons « + valeur » et « supprimer » |
| Effets | un bloc par effet | voir §4.2 ; boutons « + effet » et « supprimer » |
| Module | module(s) | voir §4.7 |

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
fait apparaître un champ texte pour une valeur libre. **Proposition** plutôt que la suggestion
pendant la frappe (`datalist` HTML), discrète et peu lisible sur iPhone. Une valeur libre inconnue
du jeu est acceptée et sauvée, mais signalée par la validation (§4.5).

### 4.4 Valeurs modifiées

Dans une carte du jeu, chaque **champ modifié** est **surligné**, avec la **valeur du jeu** en petit
dessous (« jeu : 6 »). Un appui long (ou un petit bouton ↺) sur le champ remet la valeur du jeu.

### 4.5 Validation

À chaque modification, la carte est vérifiée **par le code du jeu** (`Carte.depuis_dict`, comme au
chargement de `config/cartes.json`) :

- **Erreurs** en tête de l'écran, en rouge, en clair (clé manquante, valeur citée mais absente,
  coût négatif, portée ennemie sur une carte qui vise un module…).
- Une carte en erreur **reste sauvée** (on peut finir plus tard), mais elle est marquée ⚠ dans la
  liste et **bloque l'export** (§6), pour ne jamais envoyer un fichier que le jeu refuserait.
- **Aperçu** de la description avec les valeurs, calculé par le jeu.

### 4.6 Boutons

- **Fermer** : retour à l'écran 1, à la même position dans la liste.
- **Annuler mes modifications** (carte du jeu) : la carte redevient celle du jeu, après
  confirmation.
- **Supprimer** (nouvelle carte seulement) : après confirmation.
- **Dupliquer** (proposition) : crée une nouvelle carte à partir de celle-ci, pratique pour une
  variante.

### 4.7 Module de la carte

Une carte n'est proposée en jeu (récompense, choix de module) que si elle figure dans la liste
`cartes` d'un module de `config/modules.json`. L'écran 2 affiche donc le ou les modules qui
contiennent la carte, avec des **cases à cocher** (Principal, Lanceur de missiles…).
**Proposition** : ce choix est modifiable, et l'export contient aussi l'affectation des cartes
aux modules (§6). Sans ça, une nouvelle carte ne serait jamais proposée en jeu.

### 4.8 Nouvelle carte (bouton +)

- **Id proposé** : le premier `CRT_n` libre (aujourd'hui `CRT_51`), modifiable.
- **Champs pré-remplis** (proposition) : rareté Commune, catégorie Attaque, cible Ennemi Unique,
  coût 1, lancements 1, munitions illimitées, jouable oui, revue oui, une valeur `degats` à 0 et un
  effet Dégâts qui l'utilise. La carte est ainsi valide dès le départ et on ne fait que l'ajuster.
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
| **En erreur** | ⚠ rouge | refusée par la validation (§4.5), avant les autres pastilles |
| **Le jeu a changé** | ⇄ violet | la carte a été modifiée dans le jeu depuis ta modification locale (voir ci-dessous) |

- La comparaison se fait **sur le contenu**, pas sur la date : une modification annulée à la main
  (retour à la valeur d'origine) rend la carte à nouveau « Inchangée ».
- **Le jeu a changé** : quand on modifie une carte, l'outil garde une copie de la version du jeu à
  ce moment-là. Si, plus tard, `config/cartes.json` a changé pour cette carte (nouvelle version du
  jeu), l'outil le signale ; l'écran 2 montre alors la version du jeu, la tienne, et propose de
  garder la tienne ou de reprendre celle du jeu. Évite d'écraser sans le voir un changement fait
  entre-temps dans le dépôt.
- Dans l'écran 2, les champs modifiés sont surlignés (§4.4).

---

## 6. Sauvegarde locale et export

### 6.1 Sauvegarde sur l'appareil

- Dans le `localStorage` du navigateur, sous une clé propre à l'outil (ex.
  `space_fight_editeur_cartes`), séparée des parties et des profils.
- **Seules les différences** sont gardées : les cartes modifiées ou nouvelles (contenu complet de
  la carte, plus la copie de la version du jeu du §5), les cartes supprimées, l'affectation aux
  modules si elle a changé. Les cartes inchangées viennent toujours du jeu.
- Rechargée à chaque ouverture de l'écran 1.
- Un bouton **« Tout effacer »** (avec confirmation), dans un menu de l'écran 1, revient aux
  cartes du jeu.
- Limite connue : le `localStorage` est propre à l'appareil **et** au navigateur (Safari sur
  iPhone ≠ Chrome sur Mac). Pour passer d'un appareil à l'autre : exporter puis importer (§6.3).

### 6.2 Export (proposition)

Un bouton **Exporter** (désactivé tant qu'une carte est en erreur) ouvre un petit menu :

1. **Partager…** (recommandé sur iPhone) : la **feuille de partage d'iOS** (Messages, Mail,
   Notes, AirDrop, enregistrer dans Fichiers…) avec le fichier `cartes.json` complet en pièce
   jointe. Sur Mac, la même chose dans Safari ; ailleurs, téléchargement du fichier.
2. **Copier** : le fichier `cartes.json` complet dans le **presse-papiers**, à coller dans un
   message ou dans une conversation avec l'agent.
3. **Copier le résumé** : un texte court et lisible des changements seulement, par exemple :

```
Cartes modifiées (2) :
- CRT_10 Bouclier : bouclier 4 -> 5
- CRT_47 Laser lourd : cout 1 -> 2
Nouvelle carte (1) :
- CRT_51 Tir de barrage : Commune, 2 électricité, Ennemi Tous, degats 5 ; module Lanceur de missiles
```

**Contenu du fichier exporté** : `config/cartes.json` **complet**, toutes cartes du jeu avec les
modifications appliquées, dans le même format et le même ordre, prêt à remplacer le fichier du
dépôt. Si l'affectation aux modules a changé (§4.7), le fichier `config/modules.json` complet
est exporté aussi : deux pièces jointes avec « Partager », ou les deux fichiers l'un après
l'autre avec « Copier » (proposition, §9 question 4).

### 6.3 Import (proposition)

Un bouton **Importer** (menu de l'écran 1) colle ou charge un fichier exporté, par exemple pour
reprendre sur Mac un travail fait sur iPhone. Les cartes qui diffèrent du jeu deviennent des
modifications locales.

---

## 7. Intégrer un export dans le jeu

1. L'utilisateur envoie le fichier exporté (ou le colle dans la conversation avec l'agent).
2. L'agent remplace `config/cartes.json` (et `config/modules.json` s'il a changé), régénère le
   tableau `config/cartes.md` (`python -m outils.tableau_cartes`), lance `pytest`, et signale ce
   qui a changé, en particulier les tests qui lisent une valeur de carte.
3. PR habituelle sur `devjeux`. Après le merge et le déploiement, les modifications locales de
   l'outil deviennent « Inchangées » toutes seules, puisque le jeu les contient.

---

## 8. Accès et options

- **Bouton « Admin »** (temporaire) : en bas de l'écran de sélection du joueur et de l'accueil du
  joueur, discret. **Proposition** : une seule constante dans `app.js` pour l'afficher ou le
  masquer, pour le retirer facilement plus tard. Variante : ne l'afficher que si l'adresse contient
  `?admin` (invisible pour un autre joueur).
- **Option future, non prévue ici** : **« Tester en jeu »**, qui ferait jouer la prochaine partie
  avec les cartes modifiées de l'appareil (le web charge `config/cartes.json` dans Pyodide ; il
  suffirait d'y écrire la version modifiée). Pratique pour essayer une valeur sans passer par le
  dépôt, mais à garder séparé : risque de jouer sans s'en rendre compte avec des cartes non
  officielles.
- **Plus tard**, le même principe pourrait servir aux modules et aux ennemis (même structure :
  tableau, détail, export).

---

## 9. Questions ouvertes

1. **Colonnes de l'écran 1** : les 7 du §3.2 (État, Nom, Coût, Rareté, Cible, Module, Valeurs) ?
   Remplacer « Module » par « Catégorie » ?
2. **Version PC (pyglet)** : d'accord pour ne pas la faire, Mac et PC passant par le navigateur
   (§2) ?
3. **Bouton Admin** : toujours visible, ou seulement avec `?admin` dans l'adresse (§8) ?
4. **Modules** : rendre l'affectation d'une carte à un module modifiable et exportable (§4.7) ?
5. **Export** : les trois options du §6.2 (Partager, Copier, Copier le résumé) ? Faut-il
   l'**import** (§6.3) dès la première version ?
6. **Suppression d'une carte du jeu** : prévue seulement pour les nouvelles cartes (§4.6) ;
   faut-il pouvoir retirer une carte existante (elle disparaîtrait de l'export) ?
7. **Options** : tri par colonne, filtre, « Dupliquer » : à garder dans la première version, ou
   plus tard ?
