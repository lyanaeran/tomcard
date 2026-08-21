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
const VERSION_CACHE = "19";

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

// Un tap sur une carte l'arme et affiche son infobulle (#info-carte) ; il faut
// ensuite taper une case pour la jouer, meme pour les cartes "sans clic"
// (ALLIES_MULTIPLES/ENNEMIS_MULTIPLES) qui se resolvaient avant instantanement -
// desormais n'importe quel module (bouclier/soin) ou ennemi (attaque multi-
// cible) confirme le jeu de la carte, cf. cliquerCase.
function selectionnerCarte(carte) {
    if (etatCourant.etat !== "EN_COURS") return;
    indexCarteSelectionnee = indexCarteSelectionnee === carte.index ? null : carte.index;
    rendre();
}

const CIBLES_ALLIEES = new Set(["ALLIE_UNIQUE", "ALLIES_MULTIPLES", "MODULE_PRINCIPAL", "COLONNE_AVANT_ALLIEE"]);

function cliquerCase(idCase, typeCase) {
    if (indexCarteSelectionnee === null) return;
    const carte = etatCourant.main.find((c) => c.index === indexCarteSelectionnee);
    if (!carte) return;
    const campAttendu = CIBLES_ALLIEES.has(carte.cible) ? "allie" : "ennemi";
    if (typeCase !== campAttendu) return;
    // Pour les cartes sans clic, la cible precise ne compte pas (bridge.py
    // l'ignore) : n'importe quelle case du bon camp confirme le jeu de la carte.
    jouerCarte(carte.index, carte.sans_clic ? null : idCase);
}

function trouverObjetCase(idCase, typeCase) {
    if (typeCase === "allie") {
        if (idCase === "base") return etatCourant.vaisseau.base;
        return etatCourant.vaisseau.modules.find((m) => m && m.id === idCase) ?? null;
    }
    return etatCourant.ennemis.find((e) => e && e.id === idCase) ?? null;
}

let minuteurInfobulle = null;

// Toutes les infobulles (module, ennemi, base) partagent le meme panneau
// flottant centre a l'ecran que #info-carte (memes coordonnees en CSS),
// plutot que d'etre ancrees sur la case tapee.
function afficherInfobulle(idCase, typeCase) {
    const objet = trouverObjetCase(idCase, typeCase);
    if (!objet) return;
    clearTimeout(minuteurInfobulle);
    const lignes = [`<div class="infobulle-nom">${objet.nom}</div>`, `<div>❤️ ${objet.pv}/${objet.pv_max}</div>`];
    if (typeCase === "allie") {
        lignes.push(`<div>🔵 ${objet.bouclier}</div>`);
        // Groupes separes (jamais melanges), meme separation que les deux pastilles de
        // buffs (cf. rendrePastillesBuffs) : buffs a duree limitee, puis persistants.
        const buffsDuree = objet.buffs.filter((buff) => buff.tours_restants !== null);
        const buffsPersistants = objet.buffs.filter((buff) => buff.tours_restants === null);
        for (const buff of buffsDuree) {
            lignes.push(`<div>${libelleBuffActif(buff)}</div>`);
        }
        if (buffsDuree.length > 0 && buffsPersistants.length > 0) {
            lignes.push(`<div>Persistants :</div>`);
        }
        for (const buff of buffsPersistants) {
            lignes.push(`<div>${libelleBuffActif(buff)}</div>`);
        }
        if (objet.leurre_actif) {
            lignes.push(`<div>Leurre actif (annule la prochaine attaque)</div>`);
        }
    } else {
        lignes.push(`<div>⚔️ ${objet.degats_attaque}</div>`);
        if (objet.intention) {
            // Tir allie actif (specs.md 12.6) : la cible reelle (un autre ennemi) n'est
            // tiree au hasard qu'a la resolution du tour, jamais ici (cf. bridge.py
            // _intention_json), pour rester deterministe au tap/redessin.
            if (objet.intention.redirection) {
                lignes.push(`<div>🎯 Vise un allie au hasard</div>`);
            } else {
                lignes.push(`<div>🎯 ${objet.intention.module_nom} (-${objet.intention.degats})</div>`);
            }
        }
        for (const debuff of objet.debuffs) {
            lignes.push(`<div>${libelleDebuffActif(debuff)}</div>`);
        }
    }
    const panneau = document.getElementById("info-case");
    panneau.innerHTML = lignes.join("");
    minuteurInfobulle = setTimeout(() => {
        panneau.innerHTML = "";
    }, DUREE_INFOBULLE_MS);
}

// Tap sur une case : si aucune carte n'est selectionnee, affiche son infobulle
// (equivalent tactile du survol souris de poc.md) ; sinon, cible la carte
// selectionnee normalement.
function attacherPressionCase(element, idCase, typeCase) {
    element.addEventListener("click", (evenement) => {
        evenement.stopPropagation();
        if (indexCarteSelectionnee === null) {
            afficherInfobulle(idCase, typeCase);
        } else {
            cliquerCase(idCase, typeCase);
        }
    });
}

// Pastilles du nombre de buffs actifs sur un module (specs.md 12.3/12.5) : une doree pour
// les buffs a duree limitee, une distincte pour les buffs persistants (qui durent tout le
// combat, tours_restants null) - comptes separes, jamais additionnes dans une seule
// pastille. Chacune absente si son compte est a 0. Une derniere pastille signale un leurre
// actif (specs.md 12.6), different d'un buff : pas de compte (present ou absent), se
// consomme a la prochaine attaque recue plutot qu'a l'expiration d'une duree.
function rendrePastillesBuffs(module) {
    const duree = module.buffs.filter((buff) => buff.tours_restants !== null).length;
    const persistants = module.buffs.filter((buff) => buff.tours_restants === null).length;
    const badgeDuree = duree > 0 ? `<span class="pastille pastille-buffs">${duree}</span>` : "";
    const badgePersistants =
        persistants > 0 ? `<span class="pastille pastille-buffs-persistants">${persistants}</span>` : "";
    const badgeLeurre = module.leurre_actif ? `<span class="pastille pastille-leurre">1</span>` : "";
    return `${badgeDuree}${badgePersistants}${badgeLeurre}`;
}

// Pastilles PV (rouge) / Bouclier (bleu, allies uniquement) : memes couleurs
// que COULEUR_PASTILLE_PV/COULEUR_PASTILLE_BOUCLIER dans src/ui/fenetre.py.
// Masquees si detruit, comme sur pc (le bandeau "Detruit" les remplace).
function rendrePastilles(objet, typeCase) {
    if (objet.detruit) return "";
    const bouclier =
        typeCase === "allie" ? `<span class="pastille pastille-bouclier">${objet.bouclier}</span>` : "";
    // Pastille orange du nombre de debuffs actifs (pas de bouclier chez les
    // ennemis, meme emplacement) ; absente si aucun debuff actif.
    const debuffs =
        typeCase === "ennemi" && objet.debuffs.length > 0
            ? `<span class="pastille pastille-debuffs">${objet.debuffs.length}</span>`
            : "";
    const buffs = typeCase === "allie" ? rendrePastillesBuffs(objet) : "";
    return `${bouclier}${debuffs}${buffs}<span class="pastille pastille-pv">${objet.pv}</span>`;
}

// Pastilles du module de base : centrees en haut de l'image du vaisseau
// (equivalent du repere pare-brise de src/ui/fenetre.py), pas dans un coin
// comme les autres cases (poc.md paragraphe 8).
function rendrePastillesBase(base) {
    if (base.detruit) return "";
    const buffs = rendrePastillesBuffs(base);
    return `
        <div class="pastilles-base">
            ${buffs}
            <span class="pastille pastille-bouclier">${base.bouclier}</span>
            <span class="pastille pastille-pv">${base.pv}</span>
        </div>`;
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
                ${rendrePastillesBase(base)}
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

// Couleur de l'etoile de rarete (specs.md paragraphe 8.2), meme mapping que fenetre.py
// (COULEUR_ETOILE_RARETE).
const CLASSE_ETOILE_RARETE = {
    BASE: "etoile-base",
    COMMUNE: "etoile-commune",
    RARE: "etoile-rare",
    LEGENDAIRE: "etoile-legendaire",
};

function rendreMain() {
    return etatCourant.main
        .map((carte) => {
            const classes = ["carte"];
            if (carte.index === indexCarteSelectionnee) classes.push("selectionnee");
            const munitions =
                carte.munitions_restantes !== null
                    ? `<span class="pastille pastille-munition">${carte.munitions_restantes}</span>`
                    : "";
            return `
            <button class="${classes.join(" ")}" data-index="${carte.index}" title="${carte.nom}">
                <img src="${carte.image}" alt="${carte.nom}">
                <span class="etoile-rarete ${CLASSE_ETOILE_RARETE[carte.rarete]}">★</span>
                <span class="pastille pastille-cout">⚡${carte.cout}</span>
                ${munitions}
            </button>`;
        })
        .join("");
}

// Description generee a partir des donnees deja connues de la carte (type,
// cible, valeur - config/cartes.json), pas d'un texte fige duplique : reste
// coherent si les valeurs changent, comme les popups de fenetre.py.
const LIBELLES_CIBLE = {
    ENNEMI_UNIQUE: "un ennemi",
    ENNEMIS_MULTIPLES: "tous les ennemis",
    LIGNE_ENNEMIE: "la rangee ennemie visee (avant + arriere)",
    ALLIE_UNIQUE: "un module",
    ALLIES_MULTIPLES: "tous les modules",
    MODULE_PRINCIPAL: "le module principal",
    COLONNE_AVANT_ENNEMIE: "la ligne avant ennemie",
    COLONNE_ARRIERE_ENNEMIE: "la ligne arriere ennemie",
    COLONNE_AVANT_ALLIEE: "la ligne avant alliee",
};

const LIBELLES_ACTION_OUTILS = {
    GAIN_ELECTRICITE: (carte) => `Gagne ${carte.valeur} ⚡.`,
    GAIN_ELECTRICITE_PAR_MODULE: (carte) => `Gagne ${carte.valeur} ⚡ par module actif.`,
    PIOCHE_SUPPLEMENTAIRE: (carte) => `Pioche ${carte.valeur} cartes supplementaires.`,
};

const LIBELLES_ACTION_DEBUFF = {
    REDUCTION_DEGATS: (carte, cible) => `Diminue les degats infliges par ${cible} de ${carte.valeur}, pendant ${carte.duree} tour(s).`,
    VULNERABILITE: (carte, cible) => `Augmente les degats subis par ${cible} de ${carte.valeur}%, pendant ${carte.duree} tour(s).`,
    REDIRECTION_CIBLE: (carte, cible) => `Detourne l'attaque de ${cible} vers un autre ennemi tire au hasard, pendant ${carte.duree} tour(s).`,
};

// Libelle d'un debuff actif sur un ennemi (poc.md/specs.md 12.1/12.4), affiche dans son
// infobulle. Chaque debuff est independant : la valeur affichee est celle de cette
// instance uniquement, plusieurs debuffs du meme type peuvent apparaitre en meme temps.
const LIBELLES_ACTION_DEBUFF_ACTIF = {
    REDUCTION_DEGATS: (debuff) => `Degats reduits -${debuff.valeur}`,
    VULNERABILITE: (debuff) => `Vulnerabilite +${debuff.valeur}%`,
    REDIRECTION_CIBLE: () => `Tir detourne`,
};

function libelleDebuffActif(debuff) {
    const tour = debuff.tours_restants === 1 ? "tour" : "tours";
    return `${LIBELLES_ACTION_DEBUFF_ACTIF[debuff.action](debuff)} (${debuff.tours_restants} ${tour})`;
}

const LIBELLES_ACTION_BUFF = {
    BOUCLIER_PAR_TOUR: (carte, cible) => {
        const duree = carte.duree ? ` pendant ${carte.duree} tour(s)` : "";
        return `${cible} gagne ${carte.valeur} bouclier a chaque tour${duree}.`;
    },
};

// Libelle d'un buff actif sur un module (specs.md 12.3/12.5), affiche dans son infobulle,
// meme principe que libelleDebuffActif cote ennemi. tours_restants null = buff persistant
// (dure tout le combat, ex. Bouclier perpetuel).
const LIBELLES_ACTION_BUFF_ACTIF = {
    BOUCLIER_PAR_TOUR: (buff) => `+${buff.valeur} bouclier/tour`,
};

function libelleBuffActif(buff) {
    if (buff.tours_restants === null) return `${LIBELLES_ACTION_BUFF_ACTIF[buff.action](buff)} (illimite)`;
    const tour = buff.tours_restants === 1 ? "tour" : "tours";
    return `${LIBELLES_ACTION_BUFF_ACTIF[buff.action](buff)} (${buff.tours_restants} ${tour})`;
}

function texteEffetCarte(carte) {
    const cible = LIBELLES_CIBLE[carte.cible];
    if (carte.type === "ATTAQUE") return `Inflige ${carte.valeur} degats a ${cible}.`;
    if (carte.type === "DEFENSE") {
        if (carte.action === "BOUCLIER_POURCENTAGE_PV") return `Bouclier de ${carte.valeur}% des PV de ${cible}.`;
        if (carte.action === "ANNULATION_PROCHAINE_ATTAQUE") return `Annule la prochaine attaque sur ${cible}.`;
        return `Bouclier de ${carte.valeur} a ${cible}.`;
    }
    if (carte.type === "REPARATION") return `Repare ${carte.valeur} PV a ${cible}.`;
    if (carte.type === "OUTILS") return LIBELLES_ACTION_OUTILS[carte.action](carte);
    if (carte.type === "DEBUFF") return LIBELLES_ACTION_DEBUFF[carte.action](carte, cible);
    if (carte.type === "BUFF") return LIBELLES_ACTION_BUFF[carte.action](carte, cible);
    return `Effet de ${carte.valeur} a ${cible}.`;
}

// Infobulle de la carte selectionnee (#info-carte), affichee au centre de
// l'ecran : agrandit son image et explicite son effet (le texte imprime sur
// la carte est trop petit pour etre lu confortablement sur iPhone). N'occupe
// pas les evenements tactiles (cf. pointer-events dans le CSS) pour ne pas
// bloquer le tap sur une case qui suit pour jouer la carte.
function rendreInfoCarte() {
    const carte = etatCourant.main.find((c) => c.index === indexCarteSelectionnee);
    if (!carte) return "";
    const munitions =
        carte.munitions_restantes !== null ? `<div class="info-carte-munitions">🔋 ${carte.munitions_restantes}</div>` : "";
    return `
        <img src="${carte.image}" alt="${carte.nom}">
        <div class="info-carte-nom">${carte.nom}</div>
        <div class="info-carte-effet">${texteEffetCarte(carte)}</div>
        <div class="info-carte-cout">⚡ ${carte.cout}</div>
        ${munitions}`;
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
        `⚡ ${etatCourant.electricite}/${etatCourant.electricite_max}`;
    document.getElementById("compteurs-deck").textContent =
        `Pioche : ${etatCourant.pioche} - Defausse : ${etatCourant.defausse}`;
    document.getElementById("grille-joueur-conteneur").innerHTML = rendreGrilleJoueur();
    document.getElementById("grille-ennemis-conteneur").innerHTML = rendreGrilleEnnemis();
    document.getElementById("main").innerHTML = rendreMain();
    document.getElementById("info-carte").innerHTML = rendreInfoCarte();
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
