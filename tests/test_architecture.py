"""
Garde-fous statiques pour les regles d'architecture de CLAUDE.md - verifiables par une machine
plutot que laisses a la seule relecture (cf. specs.md/CLAUDE.md "Determinisme du tirage aleatoire"
et "Architecture" : src/gameplay ne doit jamais importer pyglet, et aucun tirage au sort ne doit
passer par le module random global directement).
"""

import ast
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC_GAMEPLAY = RACINE / "src" / "gameplay"

# Fonctions du module random qu'on ne doit jamais appeler directement (random.choice(...),
# random.random(...)...) - un tirage doit toujours passer par une instance explicite
# (random.Random(...).choice(...)), jamais par le module global (CLAUDE.md).
_APPELS_RANDOM_GLOBAL_INTERDITS = {
    "choice", "choices", "randint", "random", "sample", "shuffle", "uniform", "randrange", "gauss",
}


def _fichiers_python(dossier: Path) -> list[Path]:
    return sorted(dossier.rglob("*.py"))


def test_src_gameplay_n_importe_jamais_pyglet():
    """src/gameplay doit rester utilisable sans affichage (CLAUDE.md, Architecture) : toute
    fonction qui a besoin de pyglet appartient a src/ui."""
    fautifs = []
    for fichier in _fichiers_python(SRC_GAMEPLAY):
        arbre = ast.parse(fichier.read_text(), filename=str(fichier))
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import) and any(alias.name.split(".")[0] == "pyglet" for alias in noeud.names):
                fautifs.append(fichier)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module and noeud.module.split(".")[0] == "pyglet":
                fautifs.append(fichier)
    assert not fautifs, f"src/gameplay importe pyglet dans : {fautifs}"


def test_aucun_tirage_aleatoire_direct_sur_le_module_random_global():
    """Tout tirage doit passer par une instance explicite de random.Random (CLAUDE.md,
    "Determinisme du tirage aleatoire") - jamais random.choice(...)/random.random(...) etc.
    directement sur le module. Verifie tout le depot (src/, web/, main.py), pas seulement
    src/gameplay : la regle vaut aussi pour l'UI PC et le pont web."""
    fautifs = []
    for dossier in (RACINE / "src", RACINE / "web"):
        for fichier in _fichiers_python(dossier):
            arbre = ast.parse(fichier.read_text(), filename=str(fichier))
            for noeud in ast.walk(arbre):
                if not isinstance(noeud, ast.Call):
                    continue
                fonction = noeud.func
                if (
                    isinstance(fonction, ast.Attribute)
                    and fonction.attr in _APPELS_RANDOM_GLOBAL_INTERDITS
                    and isinstance(fonction.value, ast.Name)
                    and fonction.value.id == "random"
                ):
                    fautifs.append((fichier, noeud.lineno))
    assert not fautifs, f"Appel direct a random.<methode>() (module global) trouve : {fautifs}"


def test_tous_les_fichiers_src_gameplay_sont_montes_par_web_app_js():
    """web/app.js monte src/gameplay/ dans le systeme de fichiers virtuel de Pyodide en listant
    chaque fichier explicitement (FICHIERS_A_MONTER) - contrairement a bridge.py cote PC, il n'y a
    pas de decouverte automatique. Oublier un fichier ici (ex. un nouveau module gameplay) casse le
    chargement web au demarrage avec un ModuleNotFoundError, invisible tant qu'on ne teste pas
    reellement dans un navigateur/Pyodide (bug reel constate : src/gameplay/journal.py manquant,
    cf. CLAUDE.md "Tester les deux versions" - l'appel direct a bridge.py en Python ne passe pas
    par ce montage et ne l'aurait jamais detecte)."""
    app_js = (RACINE / "web" / "app.js").read_text()
    bloc = re.search(r"FICHIERS_A_MONTER\s*=\s*\[(.*?)\];", app_js, re.S)
    assert bloc is not None, "FICHIERS_A_MONTER introuvable dans web/app.js"
    fichiers_montes = set(re.findall(r'"([^"]+)"', bloc.group(1)))

    fichiers_reels = {
        f"src/gameplay/{fichier.name}"
        for fichier in SRC_GAMEPLAY.glob("*.py")
        if not fichier.name.startswith("__pycache__")
    }
    manquants = fichiers_reels - fichiers_montes
    assert not manquants, f"Fichiers de src/gameplay absents de FICHIERS_A_MONTER (web/app.js) : {manquants}"
