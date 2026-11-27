# Prompt Gemini : illustrations de toutes les cartes

*Document de travail, hors numérotation (cf. [specs.md](../specs.md)). Étape 6 de
[plan-cartes.md](../plan-cartes.md). **Décision utilisateur (2026-11-26)** : pour garder une unité
visuelle, **les 63 cartes du jeu sont toutes redessinées** par Gemini (ou un autre générateur
d'images), y compris les 23 qui ont déjà une illustration. Gemini livre des **planches** (plusieurs
illustrations sur une même image), que l'agent découpe : pas d'image à copier une par une.*

**Résultat (2026-11-27)** : les 4 planches ont été produites et découpées ; les 63 cartes ont
leur image (256 × 256, `assets/cartes/<fichier>`). Cases refaites à part : *Laser perçant*,
*Laser défensif*, *Salve laser* (rendues en rectangles, recadrées en carré à gauche) et
*Bouclier d'escadre* (Gemini y avait dessiné une escadrille de vaisseaux). Gemini n'a pas toujours
tracé les traits noirs entre les cases : le découpage se cale alors sur les quarts de l'image.
**Anciennes images gardées** (décision utilisateur) : les 31 images d'avant sont archivées dans
`specs/generation-images/anciennes/` (hors du dossier servi par le jeu), avec les deux versions de Gemini remplacées (`*_gemini.png`). Leur style
est presque le même que celui des nouvelles (Gemini a recopié la moitié d'entre elles de près) ;
deux reprennent donc du service pour éviter des cartes trop ressemblantes : *Missile guidé* ←
`missiles_guides.png` (trajectoires courbes sur fond bleu, au lieu d'un réticule magenta comme les
cartes de Verrouillage) et *Protéger le vaisseau* ← `defense.png` (bouclier blason, au lieu d'un
vaisseau sous un dôme proche de *Bouclier intégral*). Ces deux images font environ 160 pixels au
lieu de 256. Retouche encore possible : *Bouclier d'escadre* (fond plus sombre que les autres
Boucliers).

**Essais précédents (2026-11-26, Laser incendiaire)** :

1. Image trop sombre (fond presque noir, métal terne), plan trop large (petite tourelle, grand
   vide), rendu peint, flammes de l'impact coupées par le bord.
2. Gros plan et flammes réussis, mais Gemini a ajouté **un cadre noir et un titre** (« Space Commat
   Turet »), et le fond restait sombre et peint.

Le prompt ci-dessous insiste sur ces points, et sur le format de la planche.

---

## Mode d'emploi

1. **Une conversation Gemini neuve.** Joindre les deux images modèles de ce répertoire
   (`specs/generation-images/`) :
   - `modele_illustrations.png` : les 23 illustrations actuelles du jeu (avec le nom de leur
     carte), pour le style ;
   - `modele_cartes_en_jeu.png` : cinq cartes telles qu'elles s'affichent en jeu.
2. Coller **le prompt** ci-dessous, puis **le tableau de la planche 1**. Gemini rend une planche de
   16 illustrations.
3. Dans la même conversation, coller le tableau de la **planche 2**, puis 3, puis 4, en ajoutant :
   « Même style, même format que la planche précédente. »
4. Rapporter les **4 planches** (enregistrées en PNG). L'agent les découpe en 63 images, les
   réduit à la taille du jeu, les range dans `assets/cartes/` sous le nom de fichier indiqué et
   met à jour `config/cartes.json`. Si une case est ratée, on ne refait que cette carte.

**Pourquoi 4 planches de 16, et pas une seule de 63** : une image de Gemini fait au plus 2048
pixels de côté. Sur une seule planche, chaque illustration n'aurait que 128 à 256 pixels (moins
que les 160 affichés en jeu), et Gemini se trompe davantage dans l'ordre et le détail quand il y a
beaucoup de cases. Quatre planches restent quatre images à rapporter.

---

## Prompt à copier

> Tu vas créer des illustrations de cartes pour un jeu vidéo, livrées sous forme de **planches**.
> Je te joins deux images modèles : respecte exactement leur style.
>
> ### 1. Le jeu
>
> **Space Fight** est un jeu de cartes et de stratégie au tour par tour (un « deckbuilder »
> roguelike), sur PC et sur téléphone. Le joueur pilote un
> vaisseau spatial un peu cabossé, fait de **modules** : le **module principal** (le vaisseau
> lui-même) et des modules qu'on ajoute, comme le **Lanceur de missiles**. Chaque module apporte
> ses cartes. Il affronte des pirates de l'espace, des ennemis mécaniques et un grand Boss des
> pirates. Le ton est léger et coloré, façon dessin animé de science-fiction, jamais sombre ni
> réaliste.
>
> Les cartes sont rangées en **familles**, que l'image doit faire reconnaître d'un coup d'œil :
>
> - **Laser** (module principal) : tourelles et canons qui tirent des rayons d'énergie, surtout
>   rouges et orangés.
> - **Bouclier** : boucliers d'énergie bleus à motif hexagonal, générateurs de bouclier.
> - **Réparation** : outils, bras robotisés, soudure, dominante verte.
> - **Réacteur** : électricité, batteries, générateurs, éclairs jaunes.
> - **Protocole** : systèmes de bord, écrans, radars, hologrammes, dominante cyan ou violette.
> - **Missile** (Lanceur de missiles) : missiles rouge et blanc à flamme orange, un ou quelques-uns.
> - **Torpille** : projectiles plus longs et plus lourds, qui filent en ligne droite à travers
>   les rangs ennemis.
> - **Ogive** : explosions qui touchent tous les ennemis à la fois, pluie de bombes.
> - **Lanceur** : la rampe de lancement elle-même, sa surchauffe, sa puissance.
>
> Deux effets reviennent souvent et doivent être visibles quand une carte les utilise :
> - **Surcharge** : énergie jaune électrique, éclairs, métal chauffé au rouge (plus de dégâts).
> - **Verrouillage** : réticule de visée, cible verrouillée, marqueur magenta sur l'ennemi.
>
> ### 2. Le format de la planche (très important)
>
> - **Une seule image carrée**, dans la **plus grande résolution possible** (idéalement
>   2048 × 2048 pixels, au moins 1024 × 1024).
> - Elle est découpée en une **grille régulière de 4 colonnes × 4 rangées = 16 cases**, toutes
>   **carrées et exactement de la même taille**.
> - Les cases sont **collées les unes aux autres**, séparées seulement par un **fin trait noir
>   uniforme**. **Aucune marge** autour de la grille, **aucun fond** derrière : la grille occupe
>   toute l'image, bord à bord.
> - **Une illustration par case**, dans l'**ordre du tableau** : case 1 en haut à gauche, puis de
>   gauche à droite, rangée par rangée (case 4 en haut à droite, case 16 en bas à droite). Une case
>   prévue « vide » reste noire.
> - **Aucun texte nulle part** : ni titre, ni nom de carte, ni numéro, ni légende, ni lettre, ni
>   chiffre, ni logo, ni filigrane, dans les cases comme autour de la grille. **Aucun cadre** ni
>   bordure de carte dans les cases : le jeu ajoute lui-même le cadre, le nom et le coût.
> - Chaque case doit rester une illustration complète si on la découpe seule : rien ne déborde
>   d'une case sur sa voisine.
>
> ### 3. Le style de chaque illustration (voir les images modèles)
>
> - Illustration numérique façon **icône de jeu mobile** : contours noirs épais, couleurs très
>   saturées, éclairages néon et lueurs, métal gris anthracite avec rivets et détails orange.
> - **Rendu lisse et brillant**, presque vectoriel, comme les modèles : **pas de texture de
>   pinceau**, pas d'aspect peint ou crayonné, pas de hachures.
> - **Un seul sujet principal**, **en gros plan** : il remplit l'essentiel de la case et peut
>   déborder de ses bords gauche, droit ou haut (comme la tourelle du modèle « Laser »), en légère
>   perspective, lisible même en tout petit (l'illustration est affichée à environ 60 à 160 pixels
>   de large). Pas de petit sujet perdu au milieu d'un grand fond vide.
> - **Fond illustré plein et lumineux** qui remplit toute la case (énergie, lueurs, fumée,
>   flammes…), dans la couleur vive de la famille. **Jamais de fond sombre ou noir**, même pour
>   l'espace : les modèles ont des fonds rouges, bleus, violets ou verts éclatants.
> - **L'effet de la carte se voit en entier** dans la case : point d'impact, flammes,
>   explosion, bouclier ou réticule ne doivent pas être coupés par le bord.
> - Le nom de la carte sera écrit par le jeu **par-dessus le bas de l'illustration** : ne mets
>   rien d'important dans la bande du bas de chaque case (environ 15 % de sa hauteur).
> - Les 63 illustrations forment **un seul jeu cohérent** (même style, même lumière, même
>   épaisseur de trait), mais chacune doit se distinguer des autres de la même famille.
>
> ### 4. Les cartes
>
> Pour chaque case : son numéro, le nom de la carte (ne l'écris pas dans l'image), ce qu'elle fait
> dans le jeu (X = un nombre) et une idée d'image (tu peux faire mieux si l'idée est plus claire).
> Le tableau de la planche suit ce message.
>
> ### 5. Rappel avant de commencer
>
> Une image carrée, grille 4 × 4 de cases carrées identiques, bord à bord, fin trait noir entre
> les cases, **aucun texte**, **aucun cadre**, fonds **lumineux**, sujets **en gros plan**, rendu
> **lisse**.

---

## Tableaux des planches (à coller un par un, après le prompt)

Les colonnes « Fichier » ne sont pas à coller : elles servent à l'agent pour ranger les images.

### Planche 1 : Lasers et Réacteurs

| Case | Carte | Ce qu'elle fait | Idée d'image | Fichier |
|---|---|---|---|---|
| 1 | Laser | Inflige X dégâts à un ennemi | Tourelle laser qui tire un rayon rouge, éclat blanc à l'impact | `laser.png` |
| 2 | Laser perçant | Inflige X dégâts à la ligne ciblée | Rayon laser qui traverse plusieurs cibles alignées l'une derrière l'autre | `laser_percant.png` |
| 3 | Laser lourd | Inflige X dégâts à un ennemi | Gros canon laser qui concentre une boule d'énergie rouge avant de tirer | `laser_lourd.png` |
| 4 | Laser double | Inflige X dégâts à un ennemi, deux fois | Tourelle à deux canons qui tirent deux rayons parallèles | `laser_double.png` |
| 5 | Laser incendiaire | Inflige X dégâts et X d'incendie à un ennemi | Rayon laser orange qui enflamme la cible, flammes au point d'impact | `laser_incendiaire.png` |
| 6 | Laser d'appoint | Inflige X dégâts à un ennemi. Piochez X carte | Petite tourelle laser d'appoint qui tire un fin rayon, une carte lumineuse qui jaillit à côté | `laser_appoint.png` |
| 7 | Laser défensif | Inflige X dégâts à un ennemi et donne X de bouclier au module principal | Tourelle laser qui tire tout en étant entourée d'un bouclier bleu hexagonal | `laser_defensif.png` |
| 8 | Laser de siège | Inflige X dégâts à un ennemi | Énorme canon laser de siège, rayon épais et dévastateur | `laser_siege.png` |
| 9 | Laser de contre-charge | Consomme tout le bouclier du module principal et inflige X dégât par point de bouclier à un ennemi | Un bouclier bleu qui se dissout en énergie aspirée par un canon, qui la recrache en rayon bleu-blanc | `laser_contre_charge.png` |
| 10 | Laser orbital | Inflige X dégâts à un ennemi et X à tous les autres | Rayon géant tombant de l'orbite, onde de choc qui se propage aux alentours | `laser_orbital.png` |
| 11 | Laser disrupteur | Retire X de bouclier à un ennemi, puis lui inflige X dégâts | Rayon cyan qui fait voler en éclats le bouclier d'un ennemi | `laser_disrupteur.png` |
| 12 | Laser de visée | Inflige X dégâts à un ennemi et lui pose Verrouillage X | Tourelle laser avec viseur, point de visée magenta posé sur la cible | `laser_visee.png` |
| 13 | Salve laser | Les Laser de base sont lancés X fois de plus | Tourelle laser qui tire deux rayons coup sur coup, en rafale | `salve_laser.png` |
| 14 | Protocole laser | Jusqu'à la fin du combat, vos cartes Laser sont lancées X fois de plus | Console de commande qui active plusieurs tourelles laser à la fois, rayons rouges multiples | `protocole_laser.png` |
| 15 | Réacteur d'appoint | Donne X électricité en plus ce tour | Petite batterie d'appoint qui lâche une étincelle jaune | `reacteur_appoint.png` |
| 16 | Réacteur en surtension | Surcharge X. Piochez X carte | Réacteur qui crache des éclairs jaunes, sur le point de déborder | `reacteur_surtension.png` |

### Planche 2 : Réacteur, Boucliers et Réparations

| Case | Carte | Ce qu'elle fait | Idée d'image | Fichier |
|---|---|---|---|---|
| 1 | Réacteur en surrégime | Donne X électricité en plus ce tour | Réacteur dont l'aiguille est dans le rouge, éclairs jaunes intenses | `reacteur_surregime.png` |
| 2 | Bouclier | Bouclier de X sur un module | Générateur qui projette un bouclier d'énergie bleu hexagonal | `bouclier_v2.png` |
| 3 | Protéger le vaisseau | Bouclier de X sur le module principal | Le vaisseau principal sous un dôme de bouclier bleu | `proteger_vaisseau.png` |
| 4 | Blindage ciblé | Bouclier de X sur un module | Plaques de blindage qui se verrouillent sur un seul module du vaisseau | `blindage_cible.png` |
| 5 | Bouclier d'escadre | Donne X de bouclier à tous vos modules | Plusieurs petits boucliers hexagonaux reliés entre eux, couvrant tout le vaisseau | `bouclier_escadre.png` |
| 6 | Bouclier avant | Donne X de bouclier aux modules de la ligne avant | Mur de bouclier bleu dressé devant la proue du vaisseau | `bouclier_avant.png` |
| 7 | Bouclier réactif | Donne X de bouclier à un module. Piochez X carte | Bouclier qui se déploie à toute vitesse, avec une étincelle de réaction | `bouclier_reactif.png` |
| 8 | Bouclier chargé | Donne X de bouclier au module principal | Bouclier très épais et lumineux, saturé d'énergie, autour du vaisseau principal | `bouclier_charge.png` |
| 9 | Bouclier intégral | Donne X de bouclier à tous vos modules | Sphère de bouclier complète enveloppant tout le vaisseau | `bouclier_integral.png` |
| 10 | Bouclier miroir | Renvoi X sur tous vos modules | Bouclier argenté réfléchissant comme un miroir, qui renvoie des tirs | `bouclier_miroir.png` |
| 11 | Bouclier réfléchissant | Renvoi X sur un module : il renvoie à l'attaquant les dégâts reçus | Petit bouclier violet qui renvoie un tir ennemi vers son tireur | `bouclier_reflechissant.png` |
| 12 | Bouclier stabilisé | Les Boucliers de base sont lancés X fois de plus | Générateur de bouclier stabilisé par des anneaux, deux boucliers superposés | `bouclier_stabilise.png` |
| 13 | Protocole de riposte | Donne X de bouclier et Renvoi X au module principal | Écran tactique qui affiche un bouclier et une flèche de riposte, dominante violette | `protocole_riposte.png` |
| 14 | Réparation | Répare le module principal pour X | Clé à molette et bras mécanique qui réparent une plaque de coque, fond vert | `reparation_v2.png` |
| 15 | Réparation rapide | Répare le module principal pour X | Clé à molette et étincelles de soudure rapides, réparation express | `reparation_rapide.png` |
| 16 | Réparation de champ | Répare tous vos modules pour X | Plusieurs petits drones de réparation verts qui travaillent sur tout le vaisseau | `reparation_champ.png` |

### Planche 3 : Réparation, Protocoles, Missiles et Leurre

| Case | Carte | Ce qu'elle fait | Idée d'image | Fichier |
|---|---|---|---|---|
| 1 | Réparation complète | Répare le module principal pour X | Vaisseau entouré d'un grand halo vert de réparation totale, plaques neuves | `reparation_complete.png` |
| 2 | Protocole d'urgence | Les cartes de base sont lancées X fois de plus | Gyrophare d'alarme rouge et voyants d'urgence sur une console | `protocole_urgence.png` |
| 3 | Protocole d'analyse | Piochez X cartes | Drone scanner qui projette des cartes holographiques cyan | `protocole_analyse.png` |
| 4 | Protocole de ciblage | Pose Verrouillage X à tous les ennemis | Écran radar qui verrouille plusieurs cibles avec des réticules magenta | `protocole_ciblage.png` |
| 5 | Missile guidé | Inflige X dégâts à un ennemi. Piochez X carte | Missile qui file vers un réticule de visée, fond violet | `missile_guide_v2.png` |
| 6 | Mini-missile | Inflige X dégâts à un ennemi | Un tout petit missile vif et nerveux | `mini_missile.png` |
| 7 | Missiles jumeaux | Inflige X dégâts à un ennemi, deux fois | Deux missiles identiques côte à côte, trajectoires parallèles | `missiles_jumeaux.png` |
| 8 | Missile à fragmentation | Inflige X dégâts à un ennemi et X à tous les autres | Missile qui éclate en multiples fragments qui partent dans toutes les directions | `missile_fragmentation.png` |
| 9 | Missile thermique | Inflige X dégâts et X d'incendie à un ennemi | Missile à tête chauffée au rouge, traînée de chaleur | `missile_thermique.png` |
| 10 | Missile incendiaire | Inflige X dégâts et X d'incendie à un ennemi | Missile enveloppé de flammes qui laisse un sillage de feu | `missile_incendiaire.png` |
| 11 | Missile de couverture | Inflige X dégâts à un ennemi et donne X de bouclier au module principal | Missile qui part tandis qu'un bouclier bleu se lève derrière lui | `missile_couverture.png` |
| 12 | Missile surchargé | Inflige X dégâts à un ennemi, plus X par point de Surcharge | Missile entouré d'éclairs jaunes, crépitant d'énergie | `missile_surcharge.png` |
| 13 | Missile marqueur | Inflige X dégâts à un ennemi et lui pose Verrouillage X | Missile qui laisse un marqueur magenta lumineux sur sa cible | `missile_marqueur.png` |
| 14 | Missile de précision | Inflige X dégâts à un ennemi, plus X par point de Verrouillage de la cible | Missile fin filant droit au centre d'un réticule magenta verrouillé | `missile_precision.png` |
| 15 | Missile verrouilleur | Inflige X dégâts à un ennemi et lui pose Verrouillage X | Missile qui fixe un grand réticule magenta en forme de cadenas sur sa cible | `missile_verrouilleur.png` |
| 16 | Leurre | Annule la prochaine attaque ciblant le module | Hologramme translucide d'un module du vaisseau, qui attire un tir ennemi | `leurre.png` |

### Planche 4 : Torpilles, Ogives et Lanceur

| Case | Carte | Ce qu'elle fait | Idée d'image | Fichier |
|---|---|---|---|---|
| 1 | Vague de torpilles | Inflige X dégâts à la ligne avant et X à la ligne arrière | Plusieurs torpilles en formation, sur deux rangs, qui balaient tout | `vague_torpilles.png` |
| 2 | Torpille avant | Inflige X dégâts à tous les ennemis de la ligne avant | Torpille lourde filant en ligne droite vers une rangée d'ennemis devant | `torpille_avant.png` |
| 3 | Torpille arrière | Inflige X dégâts à tous les ennemis de la ligne arrière | Torpille qui passe par-dessus le premier rang pour frapper le rang du fond | `torpille_arriere.png` |
| 4 | Torpille traversante | Inflige X dégâts à un ennemi et X à l'ennemi de sa colonne (derrière ou devant) | Torpille qui transperce un ennemi et continue vers celui qui est derrière | `torpille_traversante.png` |
| 5 | Torpille de barrage | Inflige X dégâts à la ligne avant et donne X de bouclier au Lanceur | Torpille lancée devant un mur de bouclier qui protège la rampe de lancement | `torpille_barrage.png` |
| 6 | Ogive légère | Inflige X dégâts à tous les ennemis | Petite ogive qui explose en une gerbe légère sur plusieurs cibles | `ogive_legere.png` |
| 7 | Ogive lourde | Inflige X dégâts à tous les ennemis | Grosse ogive massive, explosion large et puissante | `ogive_lourde.png` |
| 8 | Ogive surchauffée | Surcharge X, puis inflige X dégâts (+ Surcharge) à tous les ennemis | Ogive rougeoyante parcourue d'éclairs jaunes, sur le point d'exploser | `ogive_surchauffee.png` |
| 9 | Ogive de marquage | Inflige X dégâts à tous les ennemis et leur pose Verrouillage X | Explosion qui disperse des marqueurs magenta sur plusieurs cibles | `ogive_marquage.png` |
| 10 | Ogive nucléaire | Inflige X dégâts et X d'incendie à tous les ennemis | Explosion nucléaire géante orange et jaune, en forme de champignon | `ogive_nucleaire.png` |
| 11 | Armer le lanceur | Piochez X cartes. Surcharge X | Rampe de lancement qu'on charge de missiles, voyants qui passent au jaune | `armer_lanceur.png` |
| 12 | Amplificateur | Multiplie votre Surcharge par X | Appareil qui démultiplie un éclair : un éclair entre, deux fois plus en sortent | `amplificateur.png` |
| 13 | Post-combustion | Surcharge X : chaque coup de vos cartes inflige X dégâts de plus (−1 par tour) | Tuyère de réacteur en post-combustion, flamme bleue et orange très intense | `post_combustion.png` |
| 14 | Lanceur incandescent | Multiplie votre Surcharge par X. Elle ne baisse plus jusqu'à la fin du combat | Lanceur de missiles chauffé à blanc, incandescent, entouré d'éclairs | `lanceur_incandescent.png` |
| 15 | Feu à volonté | Jusqu'à la fin du combat, vos cartes du Lanceur de missiles sont lancées X fois de plus | Rampe de lancement qui tire une salve continue de missiles | `feu_a_volonte.png` |
| 16 | *(vide)* | — | Case laissée noire | — |
