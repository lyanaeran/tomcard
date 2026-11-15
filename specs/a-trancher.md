# Space Fight — Points à trancher et idées (§9 et §11)

*Partie du document de conception. Index, règles de maintenance et numérotation commune des
sections : [specs.md](specs.md).*

---

## 9. Points encore à trancher

### 9.1 Design / gameplay

- Contenu exact de la Planète commerciale (uniquement des cartes, ou aussi d'autres bonus ? cartes
  de tous les modules du pool, ou seulement des modules équipés ?) reste à définir (§2, §6) —
  seul gros morceau de contenu encore non préparé du parcours (§10.3 "Limites connues")
- Aventure (§2.5) : les 3 variantes spécifiées (Trois lunes/Astéroïdes/Police) sont implémentées ;
  reste à en écrire d'autres pour varier le pool
- Statistiques et déblocages par profil (parties jouées/victoires/défaites, niveau max, module le
  plus choisi, déblocages en fin de partie) : sciemment pas encore implémentés (§10.3, décision
  utilisateur "pas de stat pour le moment") — à faire dans une passe dédiée
- **Condition de victoire d'une partie** (§10.3) : la structure par niveaux actuelle (§2.3) enchaîne
  les Boss indéfiniment tous les 10 niveaux, sans fin de run définie — bloquant pour une future
  statistique `victoires` (dernier Boss d'une liste finie ? Palier de niveau à atteindre ? Le run
  est-il pensé comme sans fin, façon high-score, auquel cas `victoires` n'aurait peut-être pas de
  sens ?)
- Améliorer (Station service, §2.2) : y a-t-il un plafond de PV max, ou est-ce répétable indéfiniment ?
- ~~Filtrage du pool de récompense par palier de mise à jour~~ **Tranché et codé** (2026-11-13) :
  palier 1 Communes, palier 2 + Rares, palier 3 + Légendaires (modules-cartes.md §6)
- Cartes de base fournies avec un nouveau module choisi après un Boss : deck de départ fixe par module, à définir une fois le système de cartes approfondi (voir §7)
- Plafond exact de slots équipables (proposition actuelle : 5, base incluse) — voir aussi §2.3 pour les points encore ouverts sur la structure par niveaux (répétition du motif 5/9/10 par décennie, progression du nombre d'ennemis, pondération des doublons hors Niveau 1)
- Formule exacte de pondération des doublons de modules au tirage (§2.3, §5) : plus un exemplaire supplémentaire compte-t-il, linéaire ou autre ?
- ~~Représentation visuelle d'un ennemi occupant 2 emplacements (§3.2, §8.1) : rectangle fusionné sur les 2 cases, ou deux images liées logiquement ?~~ **Tranché** (Boss des pirates, §13.3) : rectangle fusionné sur les 2 cases (un seul sprite, une seule pastille PV/Bouclier), pas deux images dupliquées - `src/ui/fenetre.py:_rect_fusionne`/`_dessiner_flotte` côté PC, `src/web/bridge.py:_ennemis_json` (une seule case publiée, `fusionne=true`) + `src/web/app.js:rendreGrilleEnnemis` (`grid-column: span 2`) côté web
- Compléter le jeu de cartes de chaque module : les archétypes de §4.3 (Bouclier énergétique, Radar, Propulseur, IA de combat, Générateur, Sabotage, Soute/Fret) n'ont pas encore de decks détaillés comme ceux de §4.1-4.2 ; les cartes déjà écrites en §4.1-4.2 n'ont pas encore de type/cible/rareté assignés (§7)
- Munitions (§3.6/§7.4) : cas limite si la pioche et la défausse sont toutes les deux vides en cours de combat alors qu'il reste des cartes épuisées (qui ne sont jamais remélangées) — le joueur peut alors se retrouver sans carte à piocher ; à surveiller en playtest une fois des cartes à munitions limitées réellement jouables (plus probable depuis la pile Hors service, combat.md §3.4)
- **Rattachement des cartes obtenues hors module** (Aventure, Planète commerciale) : au principal
  pour l'instant (décision utilisateur, 2026-11-11), ce qui les rend insensibles à la perte des
  modules et affaiblit le mot-clé Persistante. Pistes : au module du type de la carte (à préciser
  s'il n'est pas équipé, ou équipé en double), au choix du joueur, au hasard parmi les
  secondaires, ou au principal en limitant ces cartes (modules-cartes.md §12.4)
- **Renvoi de Miroir** : traité comme un stock pour le tour, qui diminue à chaque coup renvoyé
  (interprétation à valider, combat.md §13.3)
- **Flottes par niveau** : difficulté par niveau (coefficient des ennemis, tailles S/M/L, nombre
  d'ennemis), plusieurs boss. Les simulations montrent des niveaux 2 à 5 et un Boss trop faciles
  (combat.md §13.4)
- **PV et valeurs provisoires** à régler par simulation : principal 60, Lanceur 20, boucliers de
  Petit Jean et du Boss, renvoi de Miroir, augmentations des ennemis (combat.md §13.3, §13.5)
- **Combat en cours non sauvegardé** : « Quitter » ou un rechargement fait recommencer le combat
  avec un nouveau tirage d'ennemis (on peut relancer jusqu'à un adversaire facile)
- **Police avec un deck vide** (possible après plusieurs « Bricoler » ou confiscations) : le
  tirage de la carte plante. Règle à choisir : ne pas proposer la Police, ou interdire de vider
  le deck
- **Écarts d'affichage entre PC et web** à valider (interface.md §8.4)
- Munitions (§7.4) : pas de règle systématique reliant rareté et munitions pour l'instant (une carte de n'importe quel palier peut avoir des munitions limitées ou non) — à revisiter si un pattern se dégage en concevant plus de cartes

### 9.2 Technique / développement

*(voir §10 pour les choix techniques déjà tranchés ; aucun point technique ouvert pour le moment —
les munitions, seul point qui figurait ici, sont implémentées depuis §3.6/§12.10)*

---

## 11. Idées à explorer plus tard

Pistes évoquées mais pas encore approfondies ni décidées — à revisiter une fois le système de
cartes (§7) et la boucle de récompenses (§2.1, §6) stabilisés.

- **Cartes auto-jouées** : des cartes qui se déclenchent seules, sans action du joueur, en début ou
  en fin de combat (ex : buff automatique pour toute la durée du combat au démarrage, soin ou gain
  d'Argent à la fin) — distinct des cartes jouées normalement pendant le tour du joueur (§3, §7)
- Une carte auto-jouée en fin de combat pourrait aussi offrir une carte candidate supplémentaire, en
  plus de la récompense normale de combat (§2.1, §6)
- À trancher plus tard : comment ces cartes s'intègrent au deck existant (pioche normale, zone à
  part, slot dédié au module...), leur coût (électricité ou gratuites, puisqu'elles ne sont pas
  jouées manuellement), et si elles ont une rareté (§7.3) comme les autres cartes
- **Type de carte "Effet"** (nouveau, distinct des types de §7.1) : une carte qui produit son effet
  dès qu'elle est **piochée**, plutôt que jouée par le joueur. Probablement ajoutée au deck par les
  ennemis (dans l'esprit des cartes Statut/Malédiction de Slay the Spire) plutôt que choisie par le
  joueur
- **Statuts à durée** (Vulnérabilité, Réduction de dégâts, Tir allié) : non codés. Les statuts à
  intensité (bouclier, incendie, renvoi, leurre) le sont (combat.md §3.5). Réflexion d'origine,
  en partie dépassée, avec des pistes encore ouvertes (boucliers à seuil et à plafond) :
  [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md)
- **Nouveaux ennemis** : par exemple un ennemi qui vise le module principal, qui pose de
  l'incendie ou un debuff sur le joueur
- **Modules secondaires sacrifiables** : la règle est codée (seuls les PV du principal
  persistent, pile Hors service, Persistante : combat.md §3.4). Restent des pistes non codées :
  buff « Destruction » posé par des cartes, résurrection, sacrifice volontaire :
  [refonte-destruction.md](refonte-destruction.md)
