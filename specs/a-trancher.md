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
- Filtrage du pool de récompense par palier de mise à jour débloqué (§2.2/§6) : à réconcilier avec le
  mécanisme de repli au palier inférieur déjà implémenté dans `tirer_carte_recompense`, qui suppose
  aujourd'hui que tout le pool d'un module est accessible
- Cartes de base fournies avec un nouveau module choisi après un Boss : deck de départ fixe par module, à définir une fois le système de cartes approfondi (voir §7)
- Plafond exact de slots équipables (proposition actuelle : 5, base incluse) — voir aussi §2.3 pour les points encore ouverts sur la structure par niveaux (répétition du motif 5/9/10 par décennie, progression du nombre d'ennemis, pondération des doublons hors Niveau 1)
- Formule exacte de pondération des doublons de modules au tirage (§2.3, §5) : plus un exemplaire supplémentaire compte-t-il, linéaire ou autre ?
- ~~Représentation visuelle d'un ennemi occupant 2 emplacements (§3.2, §8.1) : rectangle fusionné sur les 2 cases, ou deux images liées logiquement ?~~ **Tranché** (Boss des pirates, §13.3) : rectangle fusionné sur les 2 cases (un seul sprite, une seule pastille PV/Bouclier), pas deux images dupliquées - `src/ui/fenetre.py:_rect_fusionne`/`_dessiner_flotte` côté PC, `src/web/bridge.py:_ennemis_json` (une seule case publiée, `fusionne=true`) + `src/web/app.js:rendreGrilleEnnemis` (`grid-column: span 2`) côté web
- Compléter le jeu de cartes de chaque module : les archétypes de §4.3 (Bouclier énergétique, Radar, Propulseur, IA de combat, Générateur, Sabotage, Soute/Fret) n'ont pas encore de decks détaillés comme ceux de §4.1-4.2 ; les cartes déjà écrites en §4.1-4.2 n'ont pas encore de type/cible/rareté assignés (§7)
- Munitions (§3.6/§7.4) : cas limite si la pioche et la défausse sont toutes les deux vides en cours de combat alors qu'il reste des cartes épuisées (qui ne sont jamais remélangées) — le joueur peut alors se retrouver sans carte à piocher ; à surveiller en playtest une fois des cartes à munitions limitées réellement jouables (voir §12.10 pour l'état d'implémentation actuel)
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
- **Stacks à intensité cumulative** (façon Poison/Force de Slay the Spire) : un unique compteur par
  ennemi qui s'additionne à chaque application (contrairement aux debuffs Vulnérabilité/Réduction de
  dégâts actuels, §7.1/§12.1, où chaque application reste une instance indépendante avec sa propre
  durée — plusieurs instances coexistent et leurs magnitudes s'additionnent tant qu'elles sont
  actives, mais rien ne fusionne en un seul compteur) et qui inflige un effet croissant avec le
  nombre de stacks (ex : dégâts égaux au compteur, qui décroît de 1 chaque tour). **En cours de
  conception** (discussion utilisateur, étendue à tous les buffs/debuffs/bouclier, pas seulement
  Vulnérabilité) : voir [refonte-buffs-debuffs.md](refonte-buffs-debuffs.md), brouillon pas encore
  décidé ni implémenté
- **Modules secondaires sacrifiables** (discussion utilisateur) : seuls les PV du module principal
  persistent entre les combats, les secondaires repartent à leur PV max à chaque combat, ce qui
  ouvre des effets à la mort (façon « Râle d'agonie ») et de la résurrection. **En cours de
  conception** : voir [refonte-modules.md](refonte-modules.md), brouillon pas encore décidé ni
  implémenté
