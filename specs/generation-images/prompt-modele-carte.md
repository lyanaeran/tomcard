# Prompt Gemini : modèle (gabarit) de carte et icônes

*Document de travail, hors numérotation (cf. [specs.md](../specs.md)). Proposition du 2026-11-27,
d'après un croquis de l'utilisateur : la carte affiche elle-même son coût, ses munitions, ses
lancements, son nom, son illustration, son texte et son type, et sa rareté par la couleur du cadre,
au lieu de les laisser à l'infobulle. Gemini dessine un **gabarit vide** et quelques **icônes** ; le
jeu y place l'illustration, les icônes utiles et écrit les valeurs. Les icônes servent aussi aux
statuts des vaisseaux et des ennemis. **Rien n'est codé.***

## Disposition voulue (croquis de l'utilisateur, décisions du 2026-11-27)

```
┌───────────────────────────┐
│ ⚡2    ▮2/3  ×2        ⚔  │  barre du haut : coût, munitions, lancements ; icône du type à droite
│ ┌───────────────────────┐ │
│ │                       │ │
│ │      illustration     │ │  fenêtre presque carrée (les illustrations font 256 × 256)
│ │                       │ │
│ └───────────────────────┘ │
│      Texte de la carte    │  zone de texte
│                           │
├───────────────────────────┤
│       Nom de la carte     │  bandeau du bas : le nom
└───────────────────────────┘
```

**Décisions de l'utilisateur (2026-11-27)** :

1. **Nom de la carte** : ~~au-dessus de l'illustration~~ → **dans le bandeau du bas** (décision
   révisée le 2026-11-27, quand Gemini a livré un gabarit sans bandeau du nom). Le **type** de la
   carte (Attaque, Défense…) n'est plus écrit : il est indiqué par une **icône**, dans la barre du
   haut à droite (proposition de l'agent pour l'emplacement).
2. **Rareté** : 4 variantes du même gabarit, de couleur différente (argent = base, vert = commune,
   bleu = rare, or = légendaire). **Pas d'étoile** : la couleur du cadre suffit.
3. **Taille en jeu** : environ 150 × 210 pixels sur PC (au lieu de 100 × 140, trop petit pour un
   texte), main en éventail qui se chevauche ; sur iPhone, texte complet toujours au toucher.

**Icônes (proposition)** : le jeu ne dessine pas, mais il sait **afficher une petite image** et écrire
un chiffre à côté. Les icônes du coût, des munitions et des lancements sont donc dessinées par
Gemini **à part**, et le jeu les place dans la barre du haut **seulement quand elles s'appliquent**
(beaucoup de cartes n'ont ni munitions ni lancements en plus : une icône dessinée dans le gabarit
resterait vide sur elles). Le gabarit ne contient que la barre vide.

Le jeu écrira tous les textes et chiffres (coût, munitions, lancements, nom, texte, type) : ni le
gabarit ni les icônes n'en contiennent.

---

## Prompt 1 : le gabarit

> Tu vas dessiner un **gabarit de carte vide** pour un jeu vidéo de cartes, **Space Fight** (jeu de
> cartes et de stratégie au tour par tour, sur PC et téléphone, où le joueur pilote un vaisseau
> spatial fait de modules contre des pirates de l'espace). Je te joins les images modèles du jeu
> pour le style. Le jeu placera lui-même l'illustration et les icônes, et écrira tous les textes et
> chiffres dans ce gabarit : **dessine seulement le cadre et les zones vides**.
>
> ### 1. Le style
>
> - Même style que les illustrations jointes : science-fiction façon dessin animé, contours noirs
>   épais, métal gris anthracite avec rivets, détails lumineux néon, rendu lisse et brillant (pas de
>   texture de pinceau).
> - Le cadre ressemble à un **panneau de vaisseau spatial** : plaques de métal, rivets, coins
>   renforcés, fines lignes lumineuses.
> - **Lisible avant tout** : les zones où le jeu écrira doivent être **unies, sombres et calmes**
>   (aucun motif, aucun dégradé fort), pour qu'un texte clair y reste lisible même en petit.
>
> ### 2. Le format (très important)
>
> - **Une image verticale de 1000 × 1400 pixels** (rapport 5:7).
> - **La carte occupe toute l'image**, bord à bord, avec des coins carrés : **aucun fond autour**,
>   aucune ombre portée, aucune marge.
> - **Aucun texte, aucune lettre, aucun chiffre, aucun symbole, aucune icône** nulle part.
>
> ### 3. Les zones, de haut en bas
>
> 1. **Barre du haut** (environ 10 % de la hauteur) : une bande de métal sombre, unie, sur toute la
>    largeur. Le jeu y placera trois petites icônes avec leur chiffre : laisse-la **vide**.
> 2. **Bandeau du nom** (environ 7 % de la hauteur), juste sous la barre du haut : une plaque de
>    métal sombre, unie, sur presque toute la largeur.
> 3. **Fenêtre de l'illustration**, juste sous le nom : un **carré** centré, d'environ 80 % de la
>    largeur de la carte, entouré d'un liseré métallique. **Remplis l'intérieur du carré d'un gris
>    uni (#808080)** : le jeu le remplacera par l'illustration.
> 4. **Zone de texte** (environ 22 % de la hauteur) : un panneau **uni, bleu nuit très sombre**,
>    légèrement en creux, sur presque toute la largeur.
> 5. **Bandeau du type** (environ 8 % de la hauteur), tout en bas : une plaque de métal unie, sur
>    toute la largeur.
>
> ### 4. Quatre variantes
>
> Dessine **quatre fois le même gabarit**, identique au pixel près pour la position des zones,
> qui ne diffèrent **que par la couleur du cadre, des liserés lumineux et des coins**. Cette couleur
> indique la rareté de la carte : elle doit se reconnaître d'un coup d'œil, même en petit :
>
> 1. **argent / blanc** ;
> 2. **vert émeraude** ;
> 3. **bleu électrique** ;
> 4. **or**.
>
> Livre **quatre images séparées**, chacune de 1000 × 1400 pixels, dans cet ordre.
>
> ### 5. Rappel
>
> Image verticale 1000 × 1400, la carte remplit toute l'image, **aucun texte ni chiffre ni icône**,
> fenêtre de l'illustration **carrée et grise unie (#808080)** sous le bandeau du nom, zones
> d'écriture **unies et sombres**, quatre variantes de couleur identiques en tout le reste.


### Résultat du prompt 1 (2026-11-27)

- Les quatre variantes demandées d'un coup ont échoué : Gemini les a mélangées dans une seule
  image, avec des dispositions différentes. **Méthode retenue** : la variante argent seule,
  corrigée en plusieurs messages, puis une variante par message (« reprends exactement cette image
  et change seulement la couleur des liserés et des coins argentés en … »).
- **Gabarit argent retenu** : [modele-carte-argent.png](modele-carte-argent.png) (864 × 1216).
  Mesures : fenêtre grise (#747474) de 479 × 508 en (193, 175) ; zone de texte bleu nuit de
  y = 731 à 1035 (25 % de la hauteur) ; bandeau du bas de y = 1058 à 1141 ; une seule barre en
  haut (pas de bandeau du nom, d'où le nom en bas). Coins blancs : l'agent les rendra transparents.
- **Variantes verte, bleue et or livrées** (une par message) :
  [vert](modele-carte-vert.png), [bleu](modele-carte-bleu.png), [or](modele-carte-or.png).
  Mesurées : mêmes zones que l'argent à 1 pixel près (fenêtre de 479 × 509 en (193, 174)), la
  rareté se reconnaît même à 50 pixels de large. L'or a de faux textes très estompés dans les zones
  d'écriture : l'agent repeindra ces zones d'une couleur unie au moment de préparer les gabarits.

---

## Prompt 2 : les icônes (dans la même conversation, après le gabarit)

**Décision utilisateur (2026-11-27)** : les icônes sont dessinées à part, et on en profite pour
dessiner aussi celles des **statuts** (Bouclier, Incendie, Renvoi, Leurre, Surcharge,
Verrouillage), des PV, de l'attaque prévue par un ennemi et du module visé. Elles remplaceront les
pastilles de simple couleur du PC et les émojis du web, dont l'aspect change selon l'appareil. Leurs
couleurs reprennent celles des pastilles actuelles.

> Dessine maintenant **douze petites icônes**, dans le même style que le gabarit. Le jeu les posera
> sur les cartes et sur les vaisseaux, chacune suivie d'un chiffre qu'il écrira lui-même :
>
> | Case | Icône | Dessin | Couleur dominante |
> |---|---|---|---|
> | 1 | Coût en électricité | un éclair | jaune |
> | 2 | Munitions | une cartouche ou un petit obus | doré |
> | 3 | Lancements en plus | deux flèches qui tournent en rond (« relancer ») | violet clair |
> | 4 | Points de vie | un cœur mécanique, ou une plaque de coque avec une croix | rouge |
> | 5 | Bouclier | un écusson d'énergie à motif hexagonal | bleu |
> | 6 | Incendie | une flamme | orange |
> | 7 | Renvoi | une flèche qui repart en arrière en rebondissant sur un petit bouclier | violet |
> | 8 | Leurre | une silhouette holographique de vaisseau, en pointillés | cyan |
> | 9 | Surcharge | un éclair entouré d'étincelles, plus gros et plus agressif que le coût | jaune orangé |
> | 10 | Verrouillage | un réticule de visée verrouillé | magenta |
> | 11 | Attaque (prévue par un ennemi) | une explosion ou un impact | rouge orangé |
> | 12 | Module visé au prochain tour | une cible ronde (anneaux concentriques) | rouge |
>
> - Les icônes doivent **se distinguer les unes des autres d'un coup d'œil**, même toutes petites
>   (elles seront affichées à environ **24 pixels**) : silhouettes simples et franches, peu de
>   détails, **contours noirs épais**. En particulier, le coût (case 1) et la Surcharge (case 9)
>   ne doivent pas se ressembler.
> - **Format** : une seule image de **2048 × 1536 pixels**, en **grille de 4 colonnes × 3 rangées**
>   de cases **carrées** de 512 × 512, dans l'ordre du tableau (case 1 en haut à gauche, puis de
>   gauche à droite, rangée par rangée). Chaque icône est **centrée** et occupe environ 80 % de sa
>   case.
> - **Fond magenta uni (#FF00FF)** dans toutes les cases, sans trait entre elles : le jeu le rendra
>   transparent. N'utilise **pas** de magenta pur dans les icônes elles-mêmes (pour le
>   Verrouillage, un magenta plus rosé ou plus violet).
> - **Aucun texte, aucun chiffre, aucune lettre.**

### Résultat du prompt 2 (2026-11-27)

[icones-statuts.png](icones-statuts.png) (1200 × 896) : les 12 icônes demandées, mais Gemini a
**ajouté leurs noms** et des traits de grille. L'agent les détoure quand même : libellés coupés,
fond magenta et traits retirés (le Verrouillage, magenta plus clair que le fond, est conservé).
L'utilisateur a ensuite fait refaire quatre icônes : PV (cœur simple), Renvoi (flèches de part
et d'autre d'un bouclier), Surcharge (trois éclairs), Attaque (pistolet laser). Lisibles à 24 pixels ; les deux réticules (Verrouillage et Module visé) ne se distinguent que par
leur couleur et le cadenas.

---

## Prompt 3 : les icônes de type (après les autres icônes)

> Dessine maintenant **sept petites icônes** de plus, dans le même style, pour le **type** de la
> carte, que le jeu posera dans la barre du haut :
>
> | Case | Type | Dessin | Couleur dominante |
> |---|---|---|---|
> | 1 | Attaque | deux épées croisées, ou un canon qui tire | rouge |
> | 2 | Défense | un bouclier de métal plein (pas hexagonal, pour ne pas ressembler au statut Bouclier) | bleu acier |
> | 3 | Réparation | une clé à molette | vert |
> | 4 | Buff | une flèche épaisse vers le haut | jaune |
> | 5 | Debuff | une flèche épaisse vers le bas, cassée | violet |
> | 6 | Outils | un engrenage | gris clair |
> | 7 | Contrôle | une main ou un aimant | cyan |
>
> - Mêmes règles que les icônes précédentes : silhouettes simples, contours noirs épais, lisibles
>   à 24 pixels, **aucun texte**.
> - **Format** : une image de **2048 × 1024 pixels**, grille de **4 colonnes × 2 rangées** de cases
>   de 512 × 512 dans l'ordre du tableau ; la 8e case reste vide.
> - **Fond magenta uni (#FF00FF)**, sans trait entre les cases.

*Proposition de l'agent (dessins et couleurs, à valider). Cartes actuelles : 33 Attaque,
12 Défense, 10 Buff, 4 Réparation, 3 Outils, 1 Debuff, 0 Contrôle.*

### Résultat du prompt 3 (2026-11-27)

[icones-types.png](icones-types.png) (1456 × 720, grille de 4 × 3 au lieu de 4 × 2) : les 7 icônes
proposées, avec leurs noms écrits malgré la consigne ; l'agent les a détourées sans les libellés.
Lisibles à 24 pixels. Les épées de l'Attaque, jugées hors thème par l'utilisateur, sont remplacées
par un **missile rouge** ([icone-type-attaque.png](icone-type-attaque.png), 1024 × 1024), qui se
distingue de l'attaque prévue par un ennemi (pistolet laser).

---

## Après Gemini

L'agent mesure la position exacte des zones sur le gabarit (la fenêtre grise se repère toute
seule), réduit les quatre variantes à la taille du jeu, découpe les icônes et rend leur fond
transparent. On décide ensuite ensemble de l'affichage (taille des cartes en main, éventail,
polices) avant de le coder sur PC et sur le web, dans une PR à part.

**Fait (2026-11-27)** : gabarits dans `assets/interface/cartes/modele_<rarete>.png` (432 × 608,
coins transparents, zones de texte et de nom repeintes en bleu nuit uni), icônes dans
`assets/interface/icones/` (64 × 64, fond transparent : `cout`, `munitions`, `lancements`, les
statuts, `pv`, `attaque`, `module_vise`, et `type_<categorie>`). Affichage codé sur PC
(`src/ui/carte_visuel.py`) et sur le web (`htmlCarteVisuel`, `.carte-visuel`) : interface.md §8.2.
Les icônes de statuts, de PV, d'attaque et de module visé ne sont pas encore utilisées (pastilles
des cases : prochaine étape, à décider).
