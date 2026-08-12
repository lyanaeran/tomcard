// Prototype web du POC Space Fight (branche web-ui-poc).
// Fait tourner src/gameplay/ tel quel dans le navigateur via Pyodide ; ce fichier
// ne fait que fetcher les sources Python, les monter dans la FS virtuelle, et
// dessiner l'etat renvoye par web/bridge.py en HTML/CSS. Layout simplifie par
// rapport a specs.md/poc.md (pas de popups, pas d'infobulles) : objectif ici est
// de valider la jouabilite au doigt, pas la fidelite visuelle.

const RACINE_PYODIDE = "/repo/";

const FICHIERS_A_MONTER = [
    "src/__init__.py",
    "src/gameplay/__init__.py",
    "src/gameplay/carte.py",
    "src/gameplay/ciblage.py",
    "src/gameplay/combat.py",
    "src/gameplay/config_poc.py",
    "src/gameplay/deck.py",
    "src/gameplay/donnees.py",
    "src/gameplay/ennemi.py",
    "src/gameplay/flotte.py",
    "src/gameplay/joueur.py",
    "src/gameplay/module.py",
    "src/gameplay/position.py",
    "src/gameplay/vaisseau.py",
    "config/cartes.json",
    "config/ennemis.json",
    "config/modules.json",
];

let pyodide = null;
let etatCourant = null;
let indexCarteSelectionnee = null;

async function monterDepot(instancePyodide) {
    for (const cheminRelatif of FICHIERS_A_MONTER) {
        const reponse = await fetch(cheminRelatif);
        if (!reponse.ok) {
            throw new Error(`Impossible de charger ${cheminRelatif} (HTTP ${reponse.status})`);
        }
        const contenu = await reponse.text();
        const cheminFs = RACINE_PYODIDE + cheminRelatif;
        instancePyodide.FS.mkdirTree(cheminFs.substring(0, cheminFs.lastIndexOf("/")));
        instancePyodide.FS.writeFile(cheminFs, contenu);
    }
    const sourceBridge = await (await fetch("web/bridge.py")).text();
    instancePyodide.runPython(sourceBridge);
}

function appelerBridge(nomFonction, ...args) {
    const fonctionPython = pyodide.globals.get(nomFonction);
    try {
        return JSON.parse(fonctionPython(...args));
    } finally {
        fonctionPython.destroy();
    }
}

async function demarrer() {
    const statut = document.getElementById("statut-chargement");
    try {
        statut.textContent = "Chargement de Pyodide...";
        pyodide = await loadPyodide();
        statut.textContent = "Montage du code du jeu...";
        await monterDepot(pyodide);
        nouvelleGraine();
        statut.remove();
        document.getElementById("app").classList.remove("cachee");
    } catch (erreur) {
        statut.textContent = `Erreur de chargement : ${erreur.message}`;
        console.error(erreur);
    }
}

function nouvelleGraine() {
    etatCourant = appelerBridge("nouveau_combat", null);
    indexCarteSelectionnee = null;
    rendre();
}

function jouerCarte(index, idCible) {
    etatCourant = appelerBridge("jouer_carte", index, idCible);
    indexCarteSelectionnee = null;
    rendre();
}

function finirTour() {
    etatCourant = appelerBridge("finir_tour");
    indexCarteSelectionnee = null;
    rendre();
}

function selectionnerCarte(carte) {
    if (etatCourant.etat !== "EN_COURS") return;
    if (carte.sans_clic) {
        jouerCarte(carte.index, null);
        return;
    }
    indexCarteSelectionnee = indexCarteSelectionnee === carte.index ? null : carte.index;
    rendre();
}

function cliquerCase(idCase, typeCase) {
    if (indexCarteSelectionnee === null) return;
    const carte = etatCourant.main.find((c) => c.index === indexCarteSelectionnee);
    if (!carte) return;
    const attendAllie = carte.cible === "ALLIE_UNIQUE";
    if ((attendAllie && typeCase !== "allie") || (!attendAllie && typeCase !== "ennemi")) return;
    jouerCarte(carte.index, idCase);
}

function rendreCase(objet, typeCase) {
    if (objet === null) {
        return `<div class="case case-vide"></div>`;
    }
    const classes = ["case", typeCase];
    if (objet.detruit) classes.push("detruit");
    const barreSecondaire =
        typeCase === "allie"
            ? `<div class="stat stat-bouclier">Bouclier ${objet.bouclier}</div>`
            : `<div class="stat stat-degats">Attaque ${objet.degats_attaque}</div>`;
    return `
        <div class="${classes.join(" ")}" data-id="${objet.id}" data-type="${typeCase}">
            <img src="${objet.image}" alt="${objet.nom}">
            <div class="nom">${objet.nom}</div>
            <div class="stat stat-pv">PV ${objet.pv}/${objet.pv_max}</div>
            ${barreSecondaire}
            ${objet.detruit ? '<div class="etiquette-detruite">Detruit</div>' : ""}
        </div>`;
}

function rendreGrilleJoueur() {
    const parIndex = Object.fromEntries(etatCourant.vaisseau.modules.map((m) => [m && m.id, m]));
    const cellule = (id) => rendreCase(parIndex[id] ?? null, "allie");
    return `
        <div class="grille grille-joueur">
            ${cellule("AR_G")}${cellule("AV_G")}
            <div class="case-base">${rendreCase(etatCourant.vaisseau.base, "allie")}</div>
            ${cellule("AR_D")}${cellule("AV_D")}
        </div>`;
}

function rendreGrilleEnnemis() {
    const ids = ["AV_G", "AR_G", "AV_M", "AR_M", "AV_D", "AR_D"];
    const parIndex = Object.fromEntries(etatCourant.ennemis.map((e) => [e && e.id, e]));
    return `
        <div class="grille grille-ennemis">
            ${ids.map((id) => rendreCase(parIndex[id] ?? null, "ennemi")).join("")}
        </div>`;
}

function rendreMain() {
    return etatCourant.main
        .map((carte) => {
            const classes = ["carte"];
            if (carte.index === indexCarteSelectionnee) classes.push("selectionnee");
            return `
            <button class="${classes.join(" ")}" data-index="${carte.index}">
                <img src="${carte.image}" alt="${carte.nom}">
                <div class="cout">${carte.cout}</div>
                <div class="nom">${carte.nom}</div>
            </button>`;
        })
        .join("");
}

function rendreBanniereFin() {
    if (etatCourant.etat === "EN_COURS") return "";
    const texte = etatCourant.etat === "VICTOIRE" ? "Victoire !" : "Defaite";
    return `
        <div class="banniere-fin ${etatCourant.etat.toLowerCase()}">
            <span>${texte}</span>
            <button id="bouton-rejouer">Rejouer</button>
        </div>`;
}

function rendre() {
    document.getElementById("electricite").textContent =
        `Electricite : ${etatCourant.electricite}/${etatCourant.electricite_max}`;
    document.getElementById("compteurs-deck").textContent =
        `Pioche : ${etatCourant.pioche} - Defausse : ${etatCourant.defausse}`;
    document.getElementById("grilles").innerHTML = rendreGrilleJoueur() + rendreGrilleEnnemis();
    document.getElementById("main").innerHTML = rendreMain();
    document.getElementById("banniere").innerHTML = rendreBanniereFin();

    const boutonFinTour = document.getElementById("fin-tour");
    boutonFinTour.disabled = etatCourant.etat !== "EN_COURS";

    document.querySelectorAll(".case[data-id]").forEach((element) => {
        element.addEventListener("click", () => cliquerCase(element.dataset.id, element.dataset.type));
    });
    document.querySelectorAll(".carte").forEach((element) => {
        const carte = etatCourant.main.find((c) => c.index === Number(element.dataset.index));
        element.addEventListener("click", () => selectionnerCarte(carte));
    });
    const boutonRejouer = document.getElementById("bouton-rejouer");
    if (boutonRejouer) boutonRejouer.addEventListener("click", nouvelleGraine);
}

document.getElementById("fin-tour").addEventListener("click", finirTour);
demarrer();
