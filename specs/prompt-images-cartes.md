# Prompt Gemini : illustrations des cartes manquantes

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). Étape 6 de
[plan-cartes.md](plan-cartes.md) : 40 cartes n'ont qu'une image provisoire, empruntée à une autre
carte. Ce fichier contient le prompt à donner à Gemini (ou à un autre générateur d'images) pour
créer leurs illustrations. Répartition des 23 images existantes validée par l'utilisateur le
2026-11-26 (appliquée dans `config/cartes.json`).*

**Mode d'emploi** :

1. Joindre à Gemini les deux images modèles de `specs/images/` :
   - `modele_illustrations.png` : les 23 illustrations du jeu, chacune avec le nom de sa carte ;
   - `modele_cartes_en_jeu.png` : cinq cartes telles qu'elles s'affichent en jeu.
2. Coller le prompt ci-dessous, puis demander les images **par petits lots** (4 ou 5 cartes à la
   fois, dans l'ordre du tableau) : le style reste plus régulier, et on peut corriger au fur et à
   mesure.
3. Rapporter les images obtenues : l'agent les réduit à la taille du jeu (environ 160 × 160),
   les range dans `assets/cartes/` sous le nom de fichier indiqué, et met à jour
   `config/cartes.json`.

---

## Prompt à copier

> Tu vas créer des illustrations de cartes pour un jeu vidéo. Je te joins deux images modèles :
> respecte exactement leur style.
>
> ### 1. Le jeu
>
> **Space Fight** est un jeu de cartes et de stratégie au tour par tour (un « deckbuilder »
> roguelike, dans l'esprit de Slay the Spire), sur PC et sur téléphone. Le joueur pilote un
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
> ### 2. Le style (voir les images modèles)
>
> - Illustration numérique façon **icône de jeu mobile** : contours noirs épais, couleurs très
>   saturées, éclairages néon et lueurs, métal gris anthracite avec rivets et détails orange.
> - **Un seul sujet principal**, grand, centré, en légère perspective, lisible même en tout
>   petit (l'image est affichée à environ 60 à 100 pixels de large sur un téléphone).
> - **Fond illustré plein** qui remplit tout le carré (espace, énergie, fumée, flammes…), dans
>   la couleur dominante de la famille. Pas de fond transparent, comme sur les modèles.
> - **Aucun texte**, aucun chiffre, aucune lettre, aucun cadre ni bordure de carte : le jeu
>   ajoute lui-même le cadre, le nom et le coût. Le nom de la carte est écrit **par-dessus le bas
>   de l'image** : ne mets rien d'important dans la bande du bas (environ 15 % de la hauteur).
> - Chaque image doit se distinguer des autres de la même famille, et des 23 images modèles.
>
> ### 3. Les cartes à illustrer (40)
>
> Pour chaque carte : son nom, ce qu'elle fait dans le jeu (X = un nombre), une idée d'image (tu
> peux faire mieux si l'idée est plus claire), et le nom du fichier à produire.
>
> (Voir le tableau ci-dessous : le coller à la suite du prompt.)
>
> ### 4. Format attendu
>
> - Une image par carte, au format **PNG**, **carrée (1:1), 1024 × 1024 pixels**.
> - Nommée exactement comme indiqué dans la colonne « Fichier ».
> - Fond plein, sans transparence ; aucun texte ; sujet centré, bas de l'image dégagé.
> - Livre-les **par lots de 4 ou 5**, dans l'ordre du tableau, en rappelant le nom de la carte
>   sous chaque image.

### Tableau des 40 cartes (à coller avec le prompt)

#### Module principal (20)

| Carte | Ce qu'elle fait | Idée d'image | Fichier |
|---|---|---|---|
| Laser incendiaire | Inflige X dégâts et X d'incendie à un ennemi | Rayon laser orange qui enflamme la cible, flammes au point d'impact | `laser_incendiaire.png` |
| Laser d'appoint | Inflige X dégâts à un ennemi. Piochez X carte | Petite tourelle laser d'appoint qui tire un fin rayon, une carte lumineuse qui jaillit à côté | `laser_appoint.png` |
| Laser défensif | Inflige X dégâts à un ennemi et donne X de bouclier au module principal | Tourelle laser qui tire tout en étant entourée d'un bouclier bleu hexagonal | `laser_defensif.png` |
| Laser de siège | Inflige X dégâts à un ennemi | Énorme canon laser de siège, rayon épais et dévastateur | `laser_siege.png` |
| Laser de contre-charge | Consomme tout le bouclier du module principal et inflige X dégât par point de bouclier à un ennemi | Un bouclier bleu qui se dissout en énergie aspirée par un canon, qui la recrache en rayon bleu-blanc | `laser_contre_charge.png` |
| Laser orbital | Inflige X dégâts à un ennemi et X à tous les autres | Rayon géant tombant de l'orbite, onde de choc qui se propage aux alentours | `laser_orbital.png` |
| Blindage ciblé | Bouclier de X sur un module unique | Plaques de blindage qui se verrouillent sur un seul module du vaisseau | `blindage_cible.png` |
| Bouclier d'escadre | Donne X de bouclier à tous vos modules | Plusieurs petits boucliers hexagonaux reliés entre eux, couvrant tout le vaisseau | `bouclier_escadre.png` |
| Bouclier avant | Donne X de bouclier aux modules de la ligne avant | Mur de bouclier bleu dressé devant la proue du vaisseau | `bouclier_avant.png` |
| Bouclier réactif | Donne X de bouclier à un module. Piochez X carte | Bouclier qui se déploie à toute vitesse, avec une étincelle de réaction | `bouclier_reactif.png` |
| Bouclier chargé | Donne X de bouclier au module principal | Bouclier très épais et lumineux, saturé d'énergie, autour du vaisseau principal | `bouclier_charge.png` |
| Bouclier intégral | Donne X de bouclier à tous vos modules | Sphère de bouclier complète enveloppant tout le vaisseau | `bouclier_integral.png` |
| Bouclier miroir | Renvoi X sur tous vos modules | Bouclier argenté réfléchissant comme un miroir, qui renvoie des tirs | `bouclier_miroir.png` |
| Bouclier stabilisé | Les Boucliers de base sont lancés X fois de plus | Générateur de bouclier stabilisé par des anneaux, deux boucliers superposés | `bouclier_stabilise.png` |
| Salve laser | Les Laser de base sont lancés X fois de plus | Tourelle laser qui tire deux rayons coup sur coup, en rafale | `salve_laser.png` |
| Réparation rapide | Répare le module principal pour X | Clé à molette et étincelles de soudure rapides, réparation express | `reparation_rapide.png` |
| Réparation de champ | Répare tous vos modules pour X | Plusieurs petits drones de réparation verts qui travaillent sur tout le vaisseau | `reparation_champ.png` |
| Réacteur en surtension | Surcharge X. Piochez X carte | Réacteur qui crache des éclairs jaunes, sur le point de déborder | `reacteur_surtension.png` |
| Protocole de riposte | Donne X de bouclier et Renvoi X au module principal | Écran tactique qui affiche un bouclier et une flèche de riposte, dominante violette | `protocole_riposte.png` |
| Protocole laser | Jusqu'à la fin du combat, vos cartes Laser sont lancées X fois de plus | Console de commande qui active plusieurs tourelles laser à la fois, rayons rouges multiples | `protocole_laser.png` |

#### Lanceur de missiles (20)

| Carte | Ce qu'elle fait | Idée d'image | Fichier |
|---|---|---|---|
| Mini-missile | Inflige X dégâts à un ennemi | Un tout petit missile vif et nerveux | `mini_missile.png` |
| Missiles jumeaux | Inflige X dégâts à un ennemi, deux fois | Deux missiles identiques côte à côte, trajectoires parallèles | `missiles_jumeaux.png` |
| Missile à fragmentation | Inflige X dégâts à un ennemi et X à tous les autres | Missile qui éclate en multiples fragments qui partent dans toutes les directions | `missile_fragmentation.png` |
| Missile thermique | Inflige X dégâts et X d'incendie à un ennemi | Missile à tête chauffée au rouge, traînée de chaleur | `missile_thermique.png` |
| Missile incendiaire | Inflige X dégâts et X d'incendie à un ennemi | Missile enveloppé de flammes qui laisse un sillage de feu | `missile_incendiaire.png` |
| Missile de couverture | Inflige X dégâts à un ennemi et donne X de bouclier au module principal | Missile qui part tandis qu'un bouclier bleu se lève derrière lui | `missile_couverture.png` |
| Missile surchargé | Inflige X dégâts à un ennemi, plus X par point de Surcharge | Missile entouré d'éclairs jaunes, crépitant d'énergie | `missile_surcharge.png` |
| Missile marqueur | Inflige X dégâts à un ennemi et lui pose Verrouillage X | Missile qui laisse un marqueur magenta lumineux sur sa cible | `missile_marqueur.png` |
| Missile de précision | Inflige X dégâts à un ennemi, plus X par point de Verrouillage de la cible | Missile fin filant droit au centre d'un réticule magenta verrouillé | `missile_precision.png` |
| Torpille avant | Inflige X dégâts à tous les ennemis de la ligne avant | Torpille lourde filant en ligne droite vers une rangée d'ennemis devant | `torpille_avant.png` |
| Torpille arrière | Inflige X dégâts à tous les ennemis de la ligne arrière | Torpille qui passe par-dessus le premier rang pour frapper le rang du fond | `torpille_arriere.png` |
| Torpille traversante | Inflige X dégâts à un ennemi et X à l'ennemi de sa colonne (derrière ou devant) | Torpille qui transperce un ennemi et continue vers celui qui est derrière | `torpille_traversante.png` |
| Ogive légère | Inflige X dégâts à tous les ennemis | Petite ogive qui explose en une gerbe légère sur plusieurs cibles | `ogive_legere.png` |
| Ogive lourde | Inflige X dégâts à tous les ennemis | Grosse ogive massive, explosion large et puissante | `ogive_lourde.png` |
| Ogive surchauffée | Surcharge X, puis inflige X dégâts (+ Surcharge) à tous les ennemis | Ogive rougeoyante parcourue d'éclairs jaunes, sur le point d'exploser | `ogive_surchauffee.png` |
| Ogive de marquage | Inflige X dégâts à tous les ennemis et leur pose Verrouillage X | Explosion qui disperse des marqueurs magenta sur plusieurs cibles | `ogive_marquage.png` |
| Armer le lanceur | Piochez X cartes. Surcharge X | Rampe de lancement qu'on charge de missiles, voyants qui passent au jaune | `armer_lanceur.png` |
| Amplificateur | Multiplie votre Surcharge par X | Appareil qui démultiplie un éclair : un éclair entre, deux fois plus en sortent | `amplificateur.png` |
| Post-combustion | Surcharge X : chaque coup de vos cartes inflige X dégâts de plus (−1 par tour) | Tuyère de réacteur en post-combustion, flamme bleue et orange très intense | `post_combustion.png` |
| Lanceur incandescent | Multiplie votre Surcharge par X. Elle ne baisse plus jusqu'à la fin du combat | Lanceur de missiles chauffé à blanc, incandescent, entouré d'éclairs | `lanceur_incandescent.png` |
