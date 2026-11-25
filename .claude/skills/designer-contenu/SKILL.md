---
name: designer-contenu
description: Concevoir du contenu de jeu pour Space Fight (cartes, modules, ennemis, Aventures) avec l'utilisateur, le game designer. À utiliser quand il demande des propositions ou des idées de cartes, d'effets, de mécaniques, d'ennemis, de boss ou d'Aventures, l'équilibrage d'un module, ou une « proposition » à écrire dans specs/. Ne code rien : propose, pose les questions une par une, puis écrit un fichier specs/proposition-<sujet>.md.
argument-hint: "[cartes|ennemis|aventures] <sujet, ex. « cartes du module Blindage »>"
---

# Designer de contenu — Space Fight

L'utilisateur conçoit le jeu ; tu proposes, tu chiffres, tu poses les questions, tu documentes.
**Tu ne codes rien** dans ce workflow, sauf demande explicite ensuite (CLAUDE.md racine : « spécifier
avant de coder »). Réponses en français, courtes, avec des exemples chiffrés.

Selon le sujet, lis **un** guide en plus de celui-ci :

- cartes ou module → [cartes.md](cartes.md)
- ennemis, boss, flottes → [ennemis.md](ennemis.md)
- Aventures, événements → [aventures.md](aventures.md)
- toujours, pour le fichier final → [gabarit-proposition.md](gabarit-proposition.md)

## Méthode (5 étapes, dans l'ordre)

### 1. Lire l'existant avant de proposer

- `specs/specs.md` (index), puis la section utile du guide choisi.
- Les tableaux **générés** : `config/cartes.md`, `config/modules.md`, `config/ennemis.md` (valeurs
  à jour ; ne jamais recopier une valeur de mémoire).
- Ce qui est décidé mais pas codé : `specs/effets-a-coder.md`, `specs/a-trancher.md`,
  `specs/refonte-destruction.md`, et les `specs/proposition-*.md` existants (ne pas reproposer ce
  qui est déjà proposé ou écarté).
- Les issues GitHub ouvertes si l'utilisateur dit « cf GitHub ».

### 2. Fixer le cadre chiffré, puis proposer une liste

- Écrire d'abord le **cadre** (électricité par tour, pioche, PV, repères de puissance du guide).
  Toute proposition se mesure contre lui.
- Proposer **une liste de phrases d'effet avec leurs valeurs** (« 8 dégâts à un ennemi, piochez
  1 carte »), groupée par rareté ou par rôle, avec nom et coût.
- Marquer d'un **✱** toute **mécanique qui n'existe pas encore dans le moteur** (vérifier dans
  modules-cartes.md §12.2 et combat.md §3.5 et §13). Être inventif, mais signaler.
- Toute valeur choisie par toi est une **valeur inventée** : le dire.
- Passer la liste au **contrôle des pièges** du guide (§ « Pièges » de cartes.md / ennemis.md) et
  au **contrôle hors norme** (étape 2 bis) avant de l'envoyer.
- Terminer par des **questions numérotées**. Ne rien écrire dans `specs/` à cette étape.

### 2 bis. Contrôle hors norme

Pour chaque proposition, calculer son rendement contre le repère du guide (ex. dégâts par ⚡ selon
la rareté, ou PV ÷ dégâts du deck de départ pour un ennemi) et **signaler les écarts de plus de
30 %**, dans un sens ou dans l'autre, avec la raison s'ils sont voulus (munitions limitées,
condition, contrepartie). Si une donnée manque pour juger (pas de repère, mécanique non chiffrable),
écrire **« non évalué »** : jamais de faux « équilibré ».

### 3. Poser les questions une par une

Quand l'utilisateur valide la direction, poser **une question par appel** à l'outil de questions
(`AskUserQuestion`) :

- d'abord **chaque nouveauté ✱** : « tu la veux ? » avec ses variantes (options courtes,
  description chiffrée) ;
- puis les points ouverts (valeurs, ordre de résolution, cas limites) ;
- mettre l'option recommandée en premier, suffixée « (Recommandé) » ;
- si une réponse est ambiguë ou « pas compris », **reformuler avec un exemple chiffré** et
  reposer ; si l'utilisateur dit « je te laisse voir », choisir et le noter « proposition ».
- Lire chaque réponse en entier : une remarque libre (« une seule carte, c'est peu ») est une
  demande de changement.

### 4. Écrire la proposition

- Fichier `specs/proposition-<sujet>.md` selon [gabarit-proposition.md](gabarit-proposition.md) :
  tableau prêt à saisir (une colonne par champ du JSON), décisions datées « décision
  utilisateur, AAAA-MM-JJ », valeurs inventées signalées, implémentation proposée des mécaniques ✱,
  ordre de réalisation en lots, questions restantes.
- L'ajouter au tableau « Documents de travail » de `specs/specs.md`.
- Textes affichés (noms, descriptions) **avec accents** ; identifiants et clés **sans accent**.
- Ne pas toucher `config/*.json` ni le code.

### 5. Livrer

- `pytest` (doit rester vert : seule la doc change), commit en français sans accents, push, PR
  selon CLAUDE.md racine.
- Résumé court : ce qui est dans le fichier, ce qui a été décidé, ce qui reste ouvert. Proposer
  ensuite (sans la lancer) une simulation d'équilibrage avec volume et durée, si pertinent.

## Ce que ce skill ne fait pas

- Pas de code, pas de modification de `config/*.json` : la mise en œuvre suit, PR par lot, quand
  l'utilisateur la demande (règles d'ajout de cartes : CLAUDE.md racine).
- Pas de campagne de simulation sans accord explicite.
- Pas de reprise d'un jeu existant (noms, cartes, personnages) : s'inspirer de mécaniques, jamais
  copier du contenu.
