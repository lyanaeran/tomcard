// Prototype web du POC Space Fight (branche web-ui-poc).
// Fait tourner src/gameplay/ tel quel dans le navigateur via Pyodide ; ce fichier
// ne fait que fetcher les sources Python, les monter dans la FS virtuelle, et
// dessiner l'etat renvoye par web/bridge.py en HTML/CSS. Popups +/-N, pastilles
// PV/Bouclier flottantes (memes couleurs que RAYON_PASTILLE/COULEUR_PASTILLE_*
// dans src/ui/fenetre.py), infobulle au tap (equivalent tactile du survol
// souris, poc.md paragraphe 8), modules positionnes sur l'image du vaisseau
// (memes reperes que _EMPLACEMENTS_MODULES_IMAGE) et layout paysage (specs.md
// 8.1) repris. Simplification assumee : taille des cases pilotee par la
// hauteur d'ecran plutot que mesuree pixel pres comme sur pc.

const DUREE_POPUP_MS = 2000;
const DUREE_INFOBULLE_MS = 2500;

// Casse-cache manuel : GitHub Pages ne permet pas de fixer les en-tetes
// Cache-Control, et Safari iOS garde volontiers une vieille version de ces
// fichiers en cache malgre un rechargement simple. A incrementer a chaque
// modification de app.js/bridge.py qui change le contrat entre les deux.
const VERSION_CACHE = "6";

// Emplacements des 4 modules equipes, mesures sur assets/modules/principal.png
// (1205x651) - memes reperes que _EMPLACEMENTS_MODULES_IMAGE dans
// src/ui/fenetre.py, convertis en pourcentages CSS (origine haut-gauche) pour
// un positionnement absolu independant de la taille d'affichage.
const EMPLACEMENTS_MODULES = {
    AR_G: { left: 29.05, top: 4.3, width: 18.51, height: 33.18 },
    AV_G: { left: 50.29, top: 4.3, width: 18.51, height: 33.18 },
    AR_D: { left: 28.96, top: 62.52, width: 18.51, height: 33.03 },
    AV_D: { left: 50.37, top: 62.52, width: 18.51, height: 33.03 },
};

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

async function chargerSansCache(cheminRelatif) {
    const reponse = await fetch(`${cheminRelatif}?v=${VERSION_CACHE}`, { cache: "no-cache" });
    if (!reponse.ok) {
        throw new Error(`Impossible de charger ${cheminRelatif} (HTTP ${reponse.status})`);
    }
    return reponse.text();
}

async function monterDepot(instancePyodide) {
    for (const cheminRelatif of FICHIERS_A_MONTER) {
        const contenu = await chargerSansCache(cheminRelatif);
        const cheminFs = RACINE_PYODIDE + cheminRelatif;
        instancePyodide.FS.mkdirTree(cheminFs.substring(0, cheminFs.lastIndexOf("/")));
        instancePyodide.FS.writeFile(cheminFs, contenu);
    }
    const sourceBridge = await chargerSansCache("web/bridge.py");
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
        tenterVerrouillagePaysage();
        configurerPleinEcran();
    } catch (erreur) {
        statut.textContent = `Erreur de chargement : ${erreur.message}`;
        console.error(erreur);
    }
}

function tenterVerrouillagePaysage() {
    // Best-effort : Safari sur iPhone n'autorise le verrouillage d'orientation que
    // pour une page installee sur l'ecran d'accueil (PWA). Ignore silencieusement
    // si l'API est absente ou refuse (onglet Safari normal) - le CSS en mode
    // paysage (media query) prend le relais visuellement dans tous les cas.
    if (screen.orientation && screen.orientation.lock) {
        screen.orientation.lock("landscape").catch(() => {});
    }
}

function estAutonome() {
    // "Ajoutee a l'ecran d'accueil" sur iOS (navigator.standalone) ou PWA
    // installee ailleurs (display-mode: standalone) : dans les deux cas, les
    // barres Safari sont deja masquees, pas besoin de bouton plein ecran.
    return window.navigator.standalone === true || window.matchMedia("(display-mode: standalone)").matches;
}

function configurerPleinEcran() {
    const bouton = document.getElementById("plein-ecran");
    if (estAutonome()) {
        bouton.remove();
        return;
    }
    if (document.documentElement.requestFullscreen) {
        // Marche sur desktop/Android Chrome ; iOS Safari n'implemente pas
        // l'API Fullscreen pour un element autre qu'une video, ce bouton n'y
        // fera donc rien de visible (branche ci-dessous prise a la place).
        bouton.textContent = "Plein ecran";
        bouton.addEventListener("click", () => {
            document.documentElement.requestFullscreen().catch(() => {});
        });
    } else {
        bouton.textContent = "Masquer Safari";
        bouton.addEventListener("click", () => {
            alert(
                "iOS ne permet pas de passer en plein ecran depuis un onglet Safari. " +
                    "Pour jouer sans les barres Safari : bouton Partager -> " +
                    "'Sur l'ecran d'accueil', puis relance depuis cette icone."
            );
        });
    }
}

function appliquerResultat(resultat) {
    etatCourant = resultat.etat;
    indexCarteSelectionnee = null;
    rendre();
    afficherPopups(resultat.popups);
}

function nouvelleGraine() {
    appliquerResultat(appelerBridge("nouveau_combat", null));
}

function jouerCarte(index, idCible) {
    appliquerResultat(appelerBridge("jouer_carte", index, idCible));
}

function finirTour() {
    appliquerResultat(appelerBridge("finir_tour"));
}

function afficherPopups(popups) {
    popups.forEach((popup) => {
        const element = document.querySelector(`.case.${popup.camp}[data-id="${popup.id}"]`);
        if (!element) return;
        const bulle = document.createElement("div");
        bulle.className = `popup popup-${popup.couleur}`;
        bulle.textContent = popup.texte;
        element.appendChild(bulle);
        setTimeout(() => bulle.remove(), DUREE_POPUP_MS);
    });
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

function trouverObjetCase(idCase, typeCase) {
    if (typeCase === "allie") {
        if (idCase === "base") return etatCourant.vaisseau.base;
        return etatCourant.vaisseau.modules.find((m) => m && m.id === idCase) ?? null;
    }
    return etatCourant.ennemis.find((e) => e && e.id === idCase) ?? null;
}

function afficherInfobulle(element, idCase, typeCase) {
    const objet = trouverObjetCase(idCase, typeCase);
    if (!objet) return;
    document.querySelectorAll(".infobulle").forEach((el) => el.remove());
    const ligneSecondaire =
        typeCase === "allie" ? `Bouclier ${objet.bouclier}` : `Attaque ${objet.degats_attaque}`;
    const infobulle = document.createElement("div");
    infobulle.className = "infobulle";
    infobulle.innerHTML = `
        <div class="infobulle-nom">${objet.nom}</div>
        <div>PV ${objet.pv}/${objet.pv_max}</div>
        <div>${ligneSecondaire}</div>`;
    element.appendChild(infobulle);
    setTimeout(() => infobulle.remove(), DUREE_INFOBULLE_MS);
}

// Tap sur une case : si aucune carte n'est selectionnee, affiche son infobulle
// (equivalent tactile du survol souris de poc.md) ; sinon, cible la carte
// selectionnee normalement.
function attacherPressionCase(element, idCase, typeCase) {
    element.addEventListener("click", (evenement) => {
        evenement.stopPropagation();
        if (indexCarteSelectionnee === null) {
            afficherInfobulle(element, idCase, typeCase);
        } else {
            cliquerCase(idCase, typeCase);
        }
    });
}

// Pastilles PV (rouge) / Bouclier (bleu, allies uniquement) : memes couleurs
// que COULEUR_PASTILLE_PV/COULEUR_PASTILLE_BOUCLIER dans src/ui/fenetre.py.
// Masquees si detruit, comme sur pc (le bandeau "Detruit" les remplace).
function rendrePastilles(objet, typeCase) {
    if (objet.detruit) return "";
    const bouclier =
        typeCase === "allie" ? `<span class="pastille pastille-bouclier">${objet.bouclier}</span>` : "";
    return `${bouclier}<span class="pastille pastille-pv">${objet.pv}</span>`;
}

function rendreCaseEnnemi(objet) {
    if (objet === null) {
        return `<div class="case case-vide"></div>`;
    }
    const classes = ["case", "ennemi"];
    if (objet.detruit) classes.push("detruit");
    return `
        <div class="${classes.join(" ")}" data-id="${objet.id}" data-type="ennemi">
            <img src="${objet.image}" alt="${objet.nom}">
            ${rendrePastilles(objet, "ennemi")}
            ${objet.detruit ? '<div class="etiquette-detruite">Detruit</div>' : ""}
        </div>`;
}

function rendreGrilleJoueur() {
    const base = etatCourant.vaisseau.base;
    const parIndex = Object.fromEntries(etatCourant.vaisseau.modules.map((m) => [m && m.id, m]));

    const emplacements = Object.entries(EMPLACEMENTS_MODULES)
        .map(([id, rect]) => {
            const module = parIndex[id];
            if (!module) return "";
            const classes = ["case", "allie", "emplacement-module"];
            if (module.detruit) classes.push("detruit");
            const style = `left:${rect.left}%; top:${rect.top}%; width:${rect.width}%; height:${rect.height}%;`;
            return `
                <div class="${classes.join(" ")}" style="${style}" data-id="${module.id}" data-type="allie">
                    <img src="${module.image}" alt="${module.nom}">
                    ${rendrePastilles(module, "allie")}
                    ${module.detruit ? '<div class="etiquette-detruite">Detruit</div>' : ""}
                </div>`;
        })
        .join("");

    const classesBase = ["case", "allie", "vaisseau-base"];
    if (base.detruit) classesBase.push("detruit");
    return `
        <div class="grille grille-joueur">
            <div class="${classesBase.join(" ")}" data-id="base" data-type="allie">
                <img class="image-vaisseau" src="${base.image}" alt="${base.nom}">
                ${emplacements}
                ${rendrePastilles(base, "allie")}
                ${base.detruit ? '<div class="etiquette-detruite">Detruit</div>' : ""}
            </div>
        </div>`;
}

function rendreGrilleEnnemis() {
    const ids = ["AV_G", "AR_G", "AV_M", "AR_M", "AV_D", "AR_D"];
    const parIndex = Object.fromEntries(etatCourant.ennemis.map((e) => [e && e.id, e]));
    return `
        <div class="grille grille-ennemis">
            ${ids.map((id) => rendreCaseEnnemi(parIndex[id] ?? null)).join("")}
        </div>`;
}

function rendreMain() {
    return etatCourant.main
        .map((carte) => {
            const classes = ["carte"];
            if (carte.index === indexCarteSelectionnee) classes.push("selectionnee");
            return `
            <button class="${classes.join(" ")}" data-index="${carte.index}" title="${carte.nom}">
                <img src="${carte.image}" alt="${carte.nom}">
                <span class="pastille pastille-cout">${carte.cout}</span>
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
    document.getElementById("grille-joueur-conteneur").innerHTML = rendreGrilleJoueur();
    document.getElementById("grille-ennemis-conteneur").innerHTML = rendreGrilleEnnemis();
    document.getElementById("main").innerHTML = rendreMain();
    document.getElementById("banniere").innerHTML = rendreBanniereFin();

    const boutonFinTour = document.getElementById("fin-tour");
    boutonFinTour.disabled = etatCourant.etat !== "EN_COURS";

    document.querySelectorAll(".case[data-id]").forEach((element) => {
        attacherPressionCase(element, element.dataset.id, element.dataset.type);
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
