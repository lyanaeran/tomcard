# Gabarit : `specs/proposition-<sujet>.md`

Copier la structure, remplir, supprimer ce qui ne sert pas. Exemple réel :
`specs/proposition-lanceur-missiles.md`.

```markdown
# Proposition : <sujet>

*Document de travail, hors numérotation (cf. [specs.md](specs.md)). **Rien n'est codé.** Les choix
marqués « décision utilisateur » sont validés (AAAA-MM-JJ) ; **toutes les valeurs numériques sont
des valeurs inventées**, à ajuster.*

## 1. Intention (décision utilisateur, AAAA-MM-JJ)

- Rôle, ce que l'utilisateur a demandé (nombres, raretés, contraintes).

### 1.1 Repère de puissance
Tableau du guide utilisé (cartes.md / ennemis.md / aventures.md), adapté si besoin.

### 1.2 Réponses de l'utilisateur
| # | Nouveauté ou question | Décision utilisateur |

## 2. Le contenu

### 2.1 Comment lire le tableau
Notation des effets, id proposés, colonnes vides = valeur par défaut.

### 2.2 Tableau(x)
Une colonne par champ du JSON + « État » (existant / modifié / nouveau) + « Mécanique à coder ».

### 2.3 Retiré ou écarté
### 2.4 Exemples chiffrés (montée en puissance, combat type)

## 3. Implémentation proposée des mécaniques ✱
Pour chacune : règle (décision ou proposition), format JSON, code (fichier, fonction), affichage
PC/web, tests.

### 3.x Ordre de réalisation (une PR par lot)
| Lot | Contenu | Éléments rendus jouables |

## 4. Questions ouvertes (puis « Décisions », une fois répondues)
```

Règles :

- Toute valeur que tu as choisie : « proposition » ou « valeur inventée ».
- Toute réponse de l'utilisateur : « décision utilisateur, AAAA-MM-JJ ».
- Textes affichés accentués, identifiants sans accent.
- Ajouter le fichier au tableau « Documents de travail » de `specs/specs.md`.
