// Prototype web du POC Space Fight (branche web-ui-poc).
// Fait tourner src/gameplay/ tel quel dans le navigateur via Pyodide ; ce fichier
// ne fait que fetcher les sources Python, les monter dans la FS virtuelle, et
// dessiner l'etat renvoye par web/bridge.py en HTML/CSS. Popups +/-N, pastilles
// PV/Bouclier flottantes (memes couleurs que RAYON_PASTILLE/COULEUR_PASTILLE_*
// dans src/ui/fenetre.py), infobulle au tap (equivalent tactile du survol
// souris), modules positionnes sur l'image du vaisseau
// (memes reperes que _EMPLACEMENTS_MODULES_IMAGE) et layout paysage (specs.md
// 8.1) repris. Simplification assumee : taille des cases pilotee par la
// hauteur d'ecran plutot que mesuree pixel pres comme sur pc.

const DUREE_POPUP_MS = 2000;
const DUREE_INFOBULLE_MS = 2500;

// Casse-cache manuel : GitHub Pages ne permet pas de fixer les en-tetes
// Cache-Control, et Safari iOS garde volontiers une vieille version de ces
// fichiers en cache malgre un rechargement simple. A incrementer a chaque
// modification de app.js/bridge.py qui change le contrat entre les deux.
const VERSION_CACHE = "46";

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
    "src/gameplay/parcours.py",
    "src/gameplay/partie.py",
    "src/gameplay/position.py",
    "src/gameplay/vaisseau.py",
    "config/cartes.json",
    "config/ennemis.json",
    "config/modules.json",
];

let pyodide = null;
let etatCourant = null;
let indexCarteSelectionnee = null;

// Partie reelle en cours d'orchestration (specs.md 2.4), ou null si les ecrans de parcours sont
// ouverts en mode demonstration (window.nouveauChoixModule/choixNiveau/nouvelleVictoire/
// nouvelleDefaite, appeles manuellement depuis la console) - meme distinction que main.py cote
// PC, qui n'a pas cette ambiguite (toujours une vraie Partie). choisirModule/choisirEtape/
// choisirRecompense branchent sur cette variable pour ne pas casser le mode demonstration.
let partieActive = null;

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

// Un seul ecran visible a la fois (specs.md 10.3 ajoute la selection/l'accueil joueur en amont
// du combat) : chaque fonction afficherXxx masque tous les ecrans puis ne demasque que le sien.
const IDS_ECRANS = [
    "app",
    "ecran-selection-joueur",
    "ecran-accueil-joueur",
    "ecran-choix-module",
    "ecran-choix-niveau",
    "ecran-station-service",
    "ecran-aventure-trois-lunes",
    "ecran-aventure-asteroides",
    "ecran-aventure-police",
    "ecran-etape-placeholder",
    "ecran-fin-combat",
    "ecran-victoire-finale",
    "ecran-deck",
];

function masquerTousLesEcrans() {
    IDS_ECRANS.forEach((id) => document.getElementById(id).classList.add("cachee"));
}

async function demarrer() {
    const statut = document.getElementById("statut-chargement");
    try {
        statut.textContent = "Chargement de Pyodide...";
        pyodide = await loadPyodide();
        statut.textContent = "Montage du code du jeu...";
        await monterDepot(pyodide);
        statut.remove();
        afficherSelectionJoueur();
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
        // buffs (cf. rendrePastillesBuffs) : buffs a duree limitee, puis persistants. Pas
        // d'en-tete "Persistants" : chaque ligne de buff persistant se termine deja par
        // "(illimite)" (cf. libelleBuffActif), suffisant pour les distinguer.
        const buffsDuree = objet.buffs.filter((buff) => buff.tours_restants !== null);
        const buffsPersistants = objet.buffs.filter((buff) => buff.tours_restants === null);
        for (const buff of buffsDuree) {
            lignes.push(`<div>${libelleBuffActif(buff)}</div>`);
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
// (equivalent tactile du survol souris) ; sinon, cible la carte
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
// comme les autres cases.
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

// Libelle d'un debuff actif sur un ennemi (specs.md 12.1/12.4), affiche dans son
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
    // Pour une partie reelle, ce bouton enchaine sur le reste du parcours (fin de combat, cf.
    // terminerCombatPartie) plutot que de relancer un combat de demonstration.
    const libelleBouton = partieActive ? "Continuer" : "Rejouer";
    return `
        <div class="banniere-fin ${etatCourant.etat.toLowerCase()}">
            <span>${texte}</span>
            <button id="bouton-rejouer">${libelleBouton}</button>
        </div>`;
}

function rendre() {
    document.getElementById("electricite").textContent =
        `⚡ ${etatCourant.electricite}/${etatCourant.electricite_max}`;
    document.getElementById("niveau-combat").textContent = partieActive ? `Niveau ${partieActive.niveau}` : "";
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
    if (boutonRejouer) boutonRejouer.addEventListener("click", partieActive ? terminerCombatPartie : nouvelleGraine);
}

// Ecran de choix de module (parcours, Niveau 1 - specs.md 2.3). Pas encore reliee a une
// orchestration de parcours (qui n'existe pas encore) : exposee sur window pour etre appelee
// manuellement (console du navigateur) en attendant. nouveauChoixModule(graine) tire les
// candidats via bridge.py puis affiche l'ecran ; choisirModule ne fait encore que logger le
// choix, aucun etat de parcours a mettre a jour pour l'instant.
function afficherChoixModule(candidats, niveau = null) {
    document.getElementById("titre-choix-module").textContent =
        niveau !== null ? `Nouveau module - Niveau ${niveau}` : "Nouveau module";
    document.getElementById("candidats-module").innerHTML = candidats
        .map(
            (candidat, index) => `
        <div class="candidat-module" data-index="${index}">
            <img src="${candidat.image}" alt="${candidat.nom}">
            <div class="candidat-module-nom">${candidat.nom}</div>
            <div class="candidat-module-description">${candidat.description}</div>
        </div>`
        )
        .join("");
    document.querySelectorAll(".candidat-module").forEach((element) => {
        element.addEventListener("click", () => choisirModule(candidats[Number(element.dataset.index)]));
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-choix-module").classList.remove("cachee");
}

function choisirModule(candidat) {
    if (!partieActive) {
        console.log("Module choisi :", candidat.nom);
        return;
    }
    const partie = appelerBridge("choisir_module_partie_web", JSON.stringify(partieActive), candidat.id);
    partieActive = partie;
    sauvegarderPartieLocale(joueurCourant.id, partie);
    ouvrirChoixNiveauPartie(partie);
}

function nouveauChoixModule(graine = null) {
    afficherChoixModule(appelerBridge("nouveau_choix_module", graine));
}

window.nouveauChoixModule = nouveauChoixModule;

// Ouvre le choix de module (Niveau 1) pour une partie reelle - appelee a la creation d'une
// partie et par la reprise du bouton "Continuer" (cf. continuerPartie), meme condition que
// main.py:_traiter_action cote PC (Niveau 1 sans 2e module equipe = pas encore choisi).
function ouvrirChoixModulePartie(partie) {
    partieActive = partie;
    afficherChoixModule(appelerBridge("choix_module_partie_web", JSON.stringify(partie)), partie.niveau);
}

// Ouvre le choix du prochain niveau pour une partie reelle - meme condition d'appel que
// main.py:_ouvrir_choix_niveau cote PC.
function ouvrirChoixNiveauPartie(partie) {
    partieActive = partie;
    afficherChoixNiveau(appelerBridge("choix_niveau_web", JSON.stringify(partie)));
}

// Ecran Station service (specs.md 2.2) : 4 actions gratuites (Reparer/Ameliorer/Mettre a jour/
// Deplacer) appliquees a un module de la partie active, avant de revenir au choix du prochain
// niveau (etape 8, specs.md 2.4). Meme regles que src/ui/ecran_station_service.py cote PC -
// bridge.py n'applique que les fonctions pures de src/gameplay/partie.py, aucune regle dupliquee
// ici (CLAUDE.md).
const ACTIONS_STATION_SERVICE = [
    ["reparer", "assets/station_service/reparer.png"],
    ["ameliorer", "assets/station_service/ameliorer.png"],
    ["mettre_a_jour", "assets/station_service/mettre_a_jour.png"],
    ["deplacer", "assets/station_service/deplacer.png"],
];
const FONCTIONS_ACTION_STATION_SERVICE = {
    reparer: "reparer_module_web",
    ameliorer: "ameliorer_module_web",
    mettre_a_jour: "mettre_a_jour_module_web",
};
// Deplacer ne s'applique jamais au module principal (specs.md 2.2), meme liste que
// POSITIONS_DEPLACABLES cote PC.
const POSITIONS_DEPLACABLES_STATION = ["avant_gauche", "avant_droite", "arriere_gauche", "arriere_droite"];

let positionSelectionneeStation = null;
let modeDeplacementStation = false;
// Prix d'une action de Station service (specs.md 2.1/2.2) : recupere une seule fois depuis
// bridge.py (COUT_ACTION_STATION_SERVICE, src/gameplay/partie.py) plutot que duplique ici en dur
// (CLAUDE.md - src/gameplay reste la seule source de verite).
let coutActionStationService = null;

function ouvrirStationServicePartie(partie) {
    partieActive = partie;
    positionSelectionneeStation = null;
    modeDeplacementStation = false;
    if (coutActionStationService === null) {
        coutActionStationService = appelerBridge("cout_action_station_service_web");
    }
    rendreStationService();
    masquerTousLesEcrans();
    document.getElementById("ecran-station-service").classList.remove("cachee");
}

function instructionStationService() {
    if (modeDeplacementStation) return "Cliquez l'emplacement de destination (ou recliquez le module pour annuler).";
    if (positionSelectionneeStation === null) return "Selectionnez un module, puis une action.";
    return "Selectionnez une action pour ce module.";
}

function rendreStationService() {
    document.getElementById("titre-station-service").textContent =
        `Station service - Niveau ${partieActive.niveau} - ${partieActive.argent} €`;
    const vaisseau = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive));
    document.getElementById("modules-station-service").innerHTML = Object.entries(vaisseau)
        .map(([position, etat]) => {
            if (!etat) {
                return `<div class="module-station module-station-vide" data-position="${position}">Emplacement vide</div>`;
            }
            const selectionnee = position === positionSelectionneeStation ? " selectionnee" : "";
            return `
            <div class="module-station${selectionnee}" data-position="${position}">
                <img src="${etat.image}" alt="${etat.nom}">
                <div class="module-station-nom">${etat.nom}</div>
                <div class="module-station-pv">${etat.pv} / ${etat.pv_max} PV</div>
                <div class="module-station-niveau">Mise a jour : niveau ${etat.niveau_maj}</div>
            </div>`;
        })
        .join("");
    const abordable = partieActive.argent >= coutActionStationService;
    document.getElementById("actions-station-service").innerHTML = ACTIONS_STATION_SERVICE.map(([action, image]) => {
        const armee = action === "deplacer" && modeDeplacementStation ? " armee" : "";
        const desactivee = abordable ? "" : " desactivee";
        return `<button class="action-station${armee}${desactivee}" data-action="${action}">
            <img src="${image}" alt="${action}">
            <span class="prix-action-station">${coutActionStationService} €</span>
        </button>`;
    }).join("");
    document.getElementById("instruction-station-service").textContent = instructionStationService();

    document.querySelectorAll(".module-station").forEach((element) => {
        const estVide = element.classList.contains("module-station-vide");
        element.addEventListener("click", () => cliquerModuleStation(element.dataset.position, estVide));
    });
    document.querySelectorAll(".action-station").forEach((element) => {
        element.addEventListener("click", () => cliquerActionStation(element.dataset.action));
    });
}

function cliquerModuleStation(position, estVide) {
    if (modeDeplacementStation) {
        if (position === positionSelectionneeStation) {
            modeDeplacementStation = false;
        } else if (POSITIONS_DEPLACABLES_STATION.includes(position)) {
            // succes toujours vrai ici : l'Argent est deja verifie a l'armement de Deplacer
            // (cliquerActionStation), rien ne peut le faire baisser entre-temps.
            const resultat = appelerBridge(
                "deplacer_module_web",
                JSON.stringify(partieActive),
                positionSelectionneeStation,
                position
            );
            partieActive = resultat.partie;
            sauvegarderPartieLocale(joueurCourant.id, partieActive);
            modeDeplacementStation = false;
            positionSelectionneeStation = null;
        }
    } else if (!estVide) {
        positionSelectionneeStation = position;
    }
    rendreStationService();
}

// Popup de confirmation sur la carte du module apres Reparer/Ameliorer/Mettre a jour (demande
// utilisateur), meme mecanisme que afficherPopups (combat) mais ancre sur .module-station plutot
// que sur une case de combat - le texte est calcule a partir de l'etat avant/apres l'action (pas
// de valeur de reglage dupliquee ici, cf. CLAUDE.md : src/gameplay/partie.py reste la seule
// source de verite pour PV_AMELIORATION/PV_REPARATION).
function afficherPopupStation(position, texte, classeCouleur) {
    const element = document.querySelector(`.module-station[data-position="${position}"]`);
    if (!element) return;
    const bulle = document.createElement("div");
    bulle.className = `popup ${classeCouleur}`;
    bulle.textContent = texte;
    element.appendChild(bulle);
    setTimeout(() => bulle.remove(), DUREE_POPUP_MS);
}

function cliquerActionStation(action) {
    if (positionSelectionneeStation === null) return;
    // Argent insuffisant (specs.md 2.1/2.2) : bloque l'action, meme pour l'armement de Deplacer
    // (son cout n'est preleve qu'a la destination, cliquerModuleStation, mais rien ne doit pouvoir
    // s'armer sans avoir de quoi payer).
    if (partieActive.argent < coutActionStationService) {
        afficherPopupStation(positionSelectionneeStation, "Argent insuffisant !", "popup-degats");
        return;
    }
    if (action === "deplacer") {
        if (POSITIONS_DEPLACABLES_STATION.includes(positionSelectionneeStation)) {
            modeDeplacementStation = true;
        }
        rendreStationService();
        return;
    }
    const position = positionSelectionneeStation;
    const { pv: pvAvant, pv_max: pvMaxAvant } = partieActive.vaisseau[position];
    const resultat = appelerBridge(FONCTIONS_ACTION_STATION_SERVICE[action], JSON.stringify(partieActive), position);
    partieActive = resultat.partie;
    sauvegarderPartieLocale(joueurCourant.id, partieActive);
    // Deselectionne une fois l'action appliquee (demande utilisateur) : le popup ci-dessous
    // suffit a confirmer l'effet, pas besoin de garder le module arme pour une autre action.
    positionSelectionneeStation = null;
    rendreStationService();
    const etat = partieActive.vaisseau[position];
    if (action === "reparer") {
        afficherPopupStation(position, `+${etat.pv - pvAvant} PV`, "popup-soin");
    } else if (action === "ameliorer") {
        afficherPopupStation(position, `+${etat.pv_max - pvMaxAvant} PV max`, "popup-soin");
    } else {
        afficherPopupStation(position, `Niveau ${etat.niveau_maj}`, "popup-buff");
    }
}

function terminerStationServicePartie() {
    const partie = appelerBridge("terminer_station_service_web", JSON.stringify(partieActive));
    sauvegarderPartieLocale(joueurCourant.id, partie);
    ouvrirChoixNiveauPartie(partie);
}

// Ligne d'un choix d'Aventure (specs.md 2.5) : image carree a gauche (aucune -> case vide en
// attendant un visuel dedie), rectangle de texte (titre + description) a droite - meme
// presentation pour les 3 ecrans d'Aventure (Trois lunes/Asteroides/Police).
function construireLigneChoixHtml(identifiant, image, titre, texte) {
    const imageHtml = image ? `<img src="${image}" alt="${titre}">` : "";
    return `
        <div class="choix-aventure" data-choix="${identifiant}">
            <div class="choix-aventure-image">${imageHtml}</div>
            <div class="choix-aventure-texte">
                <div class="choix-aventure-titre">${titre}</div>
                <div class="choix-aventure-description">${texte}</div>
            </div>
        </div>`;
}

// Aventure "Trois lunes" (specs.md 2.5) : choix unique parmi Reparer/Ameliorer/Bricoler, resolu
// immediatement des le clic - contrairement a l'Aventure Asteroides (a venir), pas de sequence en
// plusieurs temps ici. Meme regles que src/ui/ecran_aventure_trois_lunes.py cote PC - bridge.py
// n'applique que les fonctions pures de src/gameplay/partie.py, aucune regle dupliquee ici.
// Images recadrees depuis assets/station_service/ (bandeau de titre incruste retire, "REPARER"/
// "AMELIORER") - coherence avec le reste des choix d'Aventure (specs.md 2.5) : le titre est de
// toute facon toujours redessine a cote dans le rectangle de texte. Sources originales inchangees
// (toujours utilisees telles quelles en Station service).
const ICONE_REPARER = "assets/aventure/reparer.png";
const ICONE_AMELIORER = "assets/aventure/ameliorer.png";
const ICONE_BRICOLER = "assets/aventure/bricoler.png";

const DESCRIPTION_TROIS_LUNES =
    "Un havre de paix au milieu de la galaxie. Aucune forme de vie intelligente, des animaux de " +
    "taille raisonnable, de l'eau, des fruits et des legumes sauvages partout. Il est temps de " +
    "faire une pause.";

// Constantes reelles du moteur (PV_REPARATION_VAISSEAU/PV_AMELIORATION), recuperees une seule
// fois depuis bridge.py plutot que dupliquees ici en dur (CLAUDE.md).
let constantesAventureTroisLunes = null;
// "choix" (3 choix initiaux) -> "choix_module" (Ameliorer) ou "choix_carte" (Bricoler), ou
// directement "resolu" (Reparer, effet immediat sans cible a choisir).
let etapeAventureTroisLunes = "choix";
let groupesDeckAventureTroisLunes = [];
let messageResoluAventureTroisLunes = "";

function ouvrirAventureTroisLunesPartie(partie) {
    partieActive = partie;
    etapeAventureTroisLunes = "choix";
    if (constantesAventureTroisLunes === null) {
        constantesAventureTroisLunes = appelerBridge("constantes_aventure_trois_lunes_web");
    }
    rendreAventureTroisLunes();
    masquerTousLesEcrans();
    document.getElementById("ecran-aventure-trois-lunes").classList.remove("cachee");
}

function rendreAventureTroisLunes() {
    document.getElementById("titre-aventure-trois-lunes").textContent = `Trois lunes - Niveau ${partieActive.niveau}`;

    const description = document.getElementById("description-aventure-trois-lunes");
    const choix = document.getElementById("choix-aventure-trois-lunes");
    const instruction = document.getElementById("instruction-aventure-trois-lunes");
    const modules = document.getElementById("modules-aventure-trois-lunes");
    const deck = document.getElementById("deck-aventure-trois-lunes");
    const messageResolu = document.getElementById("message-resolu-aventure-trois-lunes");
    const boutonContinuer = document.getElementById("bouton-continuer-aventure-trois-lunes");

    description.classList.toggle("cachee", etapeAventureTroisLunes !== "choix");
    choix.classList.toggle("cachee", etapeAventureTroisLunes !== "choix");
    instruction.classList.toggle("cachee", !["choix_module", "choix_carte"].includes(etapeAventureTroisLunes));
    modules.classList.toggle("cachee", etapeAventureTroisLunes !== "choix_module");
    deck.classList.toggle("cachee", etapeAventureTroisLunes !== "choix_carte");
    messageResolu.classList.toggle("cachee", etapeAventureTroisLunes !== "resolu");
    boutonContinuer.classList.toggle("cachee", etapeAventureTroisLunes !== "resolu");

    if (etapeAventureTroisLunes === "choix") {
        description.textContent = DESCRIPTION_TROIS_LUNES;
        const { pv_reparation_vaisseau, pv_amelioration } = constantesAventureTroisLunes;
        const options = [
            ["reparer", ICONE_REPARER, "Reparer le vaisseau", `Chaque module regagne ${pv_reparation_vaisseau} PV.`],
            ["ameliorer", ICONE_AMELIORER, "Ameliorer un module", `+${pv_amelioration} PV max sur le module de votre choix.`],
            ["bricoler", ICONE_BRICOLER, "Bricoler", "Retirez une carte de votre deck."],
        ];
        choix.innerHTML = options
            .map(([identifiant, image, titre, texte]) => construireLigneChoixHtml(identifiant, image, titre, texte))
            .join("");
        document.querySelectorAll("#choix-aventure-trois-lunes .choix-aventure").forEach((element) => {
            element.addEventListener("click", () => cliquerChoixTroisLunes(element.dataset.choix));
        });
    } else if (etapeAventureTroisLunes === "choix_module") {
        instruction.textContent = "Choisissez le module a ameliorer.";
        const vaisseau = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive));
        modules.innerHTML = Object.entries(vaisseau)
            .map(([position, etat]) => {
                if (!etat) {
                    return `<div class="module-station module-station-vide" data-position="${position}">Emplacement vide</div>`;
                }
                return `
                <div class="module-station" data-position="${position}">
                    <img src="${etat.image}" alt="${etat.nom}">
                    <div class="module-station-nom">${etat.nom}</div>
                    <div class="module-station-pv">${etat.pv} / ${etat.pv_max} PV</div>
                </div>`;
            })
            .join("");
        document.querySelectorAll("#modules-aventure-trois-lunes .module-station:not(.module-station-vide)").forEach((element) => {
            element.addEventListener("click", () => cliquerModuleTroisLunes(element.dataset.position));
        });
    } else if (etapeAventureTroisLunes === "choix_carte") {
        instruction.textContent = "Choisissez une carte a retirer de votre deck.";
        groupesDeckAventureTroisLunes = appelerBridge("deck_groupe_par_id_partie_web", JSON.stringify(partieActive));
        deck.innerHTML = groupesDeckAventureTroisLunes
            .map(
                (carte) => `
            <div class="carte-deck" data-id="${carte.id_carte}">
                <span class="etoile-${carte.rarete.toLowerCase()}">★</span>
                ${carte.quantite > 1 ? `<span class="carte-deck-quantite">×${carte.quantite}</span>` : ""}
                <img src="${carte.image}" alt="${carte.nom}">
                <div class="carte-deck-nom">${carte.nom}</div>
                <div class="carte-deck-cout">⚡ ${carte.cout}</div>
            </div>`
            )
            .join("");
        document.querySelectorAll("#deck-aventure-trois-lunes .carte-deck").forEach((element) => {
            element.addEventListener("click", () => cliquerCarteTroisLunes(element.dataset.id));
        });
    } else {
        messageResolu.textContent = messageResoluAventureTroisLunes;
    }
}

function cliquerChoixTroisLunes(identifiant) {
    const { pv_reparation_vaisseau } = constantesAventureTroisLunes;
    if (identifiant === "reparer") {
        partieActive = appelerBridge("reparer_vaisseau_aventure_web", JSON.stringify(partieActive));
        messageResoluAventureTroisLunes = `Chaque module regagne ${pv_reparation_vaisseau} PV !`;
        etapeAventureTroisLunes = "resolu";
    } else if (identifiant === "ameliorer") {
        etapeAventureTroisLunes = "choix_module";
    } else if (identifiant === "bricoler") {
        etapeAventureTroisLunes = "choix_carte";
    }
    rendreAventureTroisLunes();
}

function cliquerModuleTroisLunes(position) {
    const { pv_amelioration } = constantesAventureTroisLunes;
    const nom = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive))[position].nom;
    partieActive = appelerBridge("ameliorer_module_aventure_web", JSON.stringify(partieActive), position);
    messageResoluAventureTroisLunes = `${nom} ameliore : +${pv_amelioration} PV max !`;
    etapeAventureTroisLunes = "resolu";
    rendreAventureTroisLunes();
}

function cliquerCarteTroisLunes(idCarte) {
    const carte = groupesDeckAventureTroisLunes.find((c) => c.id_carte === idCarte);
    partieActive = appelerBridge("retirer_carte_aventure_web", JSON.stringify(partieActive), idCarte);
    messageResoluAventureTroisLunes = `Carte retiree : ${carte.nom}.`;
    etapeAventureTroisLunes = "resolu";
    rendreAventureTroisLunes();
}

function terminerAventureTroisLunes() {
    const partie = appelerBridge("terminer_aventure_trois_lunes_web", JSON.stringify(partieActive));
    sauvegarderPartieLocale(joueurCourant.id, partie);
    ouvrirChoixNiveauPartie(partie);
}

// Aventure "Asteroides" (specs.md 2.5) : deux choix - Traverser (sequence en 3 temps sur ce meme
// ecran, chaque etape validee par un bouton "Continuer") ou Affronter les pirates (combat scripte,
// delegue au meme pipeline qu'un combat Prime normal). Meme regles que
// src/ui/ecran_aventure_asteroides.py cote PC - bridge.py n'applique que les fonctions pures de
// src/gameplay/partie.py, aucune regle dupliquee ici.
const DESCRIPTION_ASTEROIDES =
    "Poursuivi par des pirates de l'espace, vous n'avez plus le choix : vaincre ou perir ! A moins que...";

// Recadree depuis assets/prochain_niveau/prime.png (bandeau "PRIME" retire) : affiche de toute
// facon son propre titre a cote dans le rectangle de texte.
const ICONE_AFFRONTER = "assets/aventure/pirates.png";

// Extrait du fond d'ecran de cette Aventure (assets/aventure/champ_asteroides.png) plutot qu'une
// icone distincte : aucune icone existante n'etait pertinente pour ce choix.
const ICONE_TRAVERSER = "assets/aventure/traverser.png";

const CHOIX_ASTEROIDES = [
    ["traverser", ICONE_TRAVERSER, "Traverser le champ d'asteroides", "Un module au choix va en subir les consequences..."],
    ["affronter", ICONE_AFFRONTER, "Affronter les pirates", "Lance un combat contre 3 ennemis."],
];

let constantesAventureAsteroides = null;
// "choix" (2 choix) -> "choix_module" (module cible des degats) -> "sequence_2" (2e coup, apres
// le 1er deja applique au clic du module) -> "sequence_3" (carte offerte, si trouvee) -> "resolu".
let etapeAventureAsteroides = "choix";
let positionCibleeAsteroides = null;
let carteOfferteAsteroides = null;
let messageAsteroides = "";

function ouvrirAventureAsteroidesPartie(partie) {
    partieActive = partie;
    etapeAventureAsteroides = "choix";
    positionCibleeAsteroides = null;
    carteOfferteAsteroides = null;
    if (constantesAventureAsteroides === null) {
        constantesAventureAsteroides = appelerBridge("constantes_aventure_asteroides_web");
    }
    rendreAventureAsteroides();
    masquerTousLesEcrans();
    document.getElementById("ecran-aventure-asteroides").classList.remove("cachee");
}

function rendreAventureAsteroides() {
    document.getElementById("titre-aventure-asteroides").textContent = `Asteroides - Niveau ${partieActive.niveau}`;

    const description = document.getElementById("description-aventure-asteroides");
    const choix = document.getElementById("choix-aventure-asteroides");
    const instruction = document.getElementById("instruction-aventure-asteroides");
    const modules = document.getElementById("modules-aventure-asteroides");
    const message = document.getElementById("message-aventure-asteroides");
    const carteOfferte = document.getElementById("carte-offerte-aventure-asteroides");
    const boutonsCarteOfferte = document.getElementById("boutons-carte-offerte-aventure-asteroides");
    const boutonContinuer = document.getElementById("bouton-continuer-aventure-asteroides");

    description.classList.toggle("cachee", etapeAventureAsteroides !== "choix");
    choix.classList.toggle("cachee", etapeAventureAsteroides !== "choix");
    instruction.classList.toggle("cachee", etapeAventureAsteroides !== "choix_module");
    modules.classList.toggle("cachee", etapeAventureAsteroides !== "choix_module");
    message.classList.toggle("cachee", !["sequence_2", "sequence_3", "resolu"].includes(etapeAventureAsteroides));
    carteOfferte.classList.toggle("cachee", etapeAventureAsteroides !== "sequence_3");
    boutonsCarteOfferte.classList.toggle("cachee", etapeAventureAsteroides !== "sequence_3");
    boutonContinuer.classList.toggle("cachee", !["sequence_2", "resolu"].includes(etapeAventureAsteroides));

    if (etapeAventureAsteroides === "choix") {
        description.textContent = DESCRIPTION_ASTEROIDES;
        choix.innerHTML = CHOIX_ASTEROIDES.map(
            ([identifiant, image, titre, texte]) => construireLigneChoixHtml(identifiant, image, titre, texte)
        ).join("");
        document.querySelectorAll("#choix-aventure-asteroides .choix-aventure").forEach((element) => {
            element.addEventListener("click", () => cliquerChoixAsteroides(element.dataset.choix));
        });
    } else if (etapeAventureAsteroides === "choix_module") {
        instruction.textContent = "Choisissez le module qui essuiera les degats.";
        const vaisseau = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive));
        modules.innerHTML = Object.entries(vaisseau)
            .map(([position, etat]) => {
                if (!etat) {
                    return `<div class="module-station module-station-vide" data-position="${position}">Emplacement vide</div>`;
                }
                return `
                <div class="module-station" data-position="${position}">
                    <img src="${etat.image}" alt="${etat.nom}">
                    <div class="module-station-nom">${etat.nom}</div>
                    <div class="module-station-pv">${etat.pv} / ${etat.pv_max} PV</div>
                </div>`;
            })
            .join("");
        document.querySelectorAll("#modules-aventure-asteroides .module-station:not(.module-station-vide)").forEach((element) => {
            element.addEventListener("click", () => cliquerModuleAsteroides(element.dataset.position));
        });
    } else {
        message.textContent = messageAsteroides;
        if (etapeAventureAsteroides === "sequence_3") {
            const carte = carteOfferteAsteroides;
            carteOfferte.innerHTML = `
                <div class="candidat-recompense">
                    <span class="etoile-${carte.rarete.toLowerCase()}">★</span>
                    <img src="${carte.image}" alt="${carte.nom}">
                    <div class="candidat-recompense-nom">${carte.nom}</div>
                    <div class="candidat-recompense-cout">⚡ ${carte.cout}</div>
                    <div class="candidat-recompense-description">${texteEffetCarte(carte)}</div>
                </div>`;
        }
    }
}

function cliquerChoixAsteroides(identifiant) {
    if (identifiant === "traverser") {
        etapeAventureAsteroides = "choix_module";
        rendreAventureAsteroides();
    } else if (identifiant === "affronter") {
        appliquerResultat(appelerBridge("combat_aventure_asteroides_web", JSON.stringify(partieActive)));
        masquerTousLesEcrans();
        document.getElementById("app").classList.remove("cachee");
    }
}

function cliquerModuleAsteroides(position) {
    const { degats_asteroides } = constantesAventureAsteroides;
    positionCibleeAsteroides = position;
    const nom = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive))[position].nom;
    partieActive = appelerBridge("subir_degats_module_asteroides_web", JSON.stringify(partieActive), position);
    messageAsteroides = `Vous traversez le champ d'asteroides : ${nom} perd ${degats_asteroides} PV.`;
    etapeAventureAsteroides = "sequence_2";
    rendreAventureAsteroides();
}

function continuerSequence2Asteroides() {
    const { degats_asteroides } = constantesAventureAsteroides;
    const nom = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive))[positionCibleeAsteroides].nom;
    partieActive = appelerBridge("subir_degats_module_asteroides_web", JSON.stringify(partieActive), positionCibleeAsteroides);
    carteOfferteAsteroides = appelerBridge("carte_offerte_asteroides_web");
    if (carteOfferteAsteroides === null) {
        etapeAventureAsteroides = "resolu";
        messageAsteroides =
            `Ces asteroides n'en finissent plus : ${nom} perd encore ${degats_asteroides} PV. ` +
            "Vous parvenez finalement a vous degager.";
    } else {
        etapeAventureAsteroides = "sequence_3";
        messageAsteroides =
            `Ces asteroides n'en finissent plus : ${nom} perd encore ${degats_asteroides} PV. ` +
            "Pres de la sortie, vous reperez des debris...";
    }
    rendreAventureAsteroides();
}

function prendreCarteAsteroides() {
    partieActive = appelerBridge(
        "prendre_carte_offerte_asteroides_web",
        JSON.stringify(partieActive),
        carteOfferteAsteroides.id_carte
    );
    messageAsteroides = `Vous recuperez : ${carteOfferteAsteroides.nom}.`;
    etapeAventureAsteroides = "resolu";
    rendreAventureAsteroides();
}

function passerCarteAsteroides() {
    messageAsteroides = "Vous laissez les debris derriere vous.";
    etapeAventureAsteroides = "resolu";
    rendreAventureAsteroides();
}

function cliquerContinuerAsteroides() {
    if (etapeAventureAsteroides === "sequence_2") {
        continuerSequence2Asteroides();
    } else if (etapeAventureAsteroides === "resolu") {
        const partie = appelerBridge("terminer_aventure_asteroides_web", JSON.stringify(partieActive));
        sauvegarderPartieLocale(joueurCourant.id, partie);
        ouvrirChoixNiveauPartie(partie);
    }
}

// Aventure "Police" (specs.md 2.5) : une carte du deck reel est tiree au hasard, puis 3 choix -
// Confiscation (retire la carte), Mettre aux normes (payer un cout fixe pour la garder), Detourner
// l'attention (retire une autre carte au hasard, disponible une seule fois par Aventure - le choix
// disparait ensuite). Meme regles que src/ui/ecran_aventure_police.py cote PC - bridge.py n'applique
// que les fonctions pures de src/gameplay/partie.py, aucune regle dupliquee ici.
const DESCRIPTION_POLICE =
    "Un vaisseau de patrouille vous somme de vous arreter pour un controle de routine...";

// Recadree depuis assets/station_service/mettre_a_jour.png (bandeau "METTRE A JOUR" retire) :
// affiche de toute facon son propre titre a cote dans le rectangle de texte.
const ICONE_METTRE_AUX_NORMES = "assets/aventure/mettre_aux_normes.png";
const ICONE_CONFISCATION = "assets/aventure/confiscation.png";
const ICONE_DETOURNER = "assets/aventure/detourner.png";

let constantesAventurePolice = null;
// "choix" (2 ou 3 choix selon detournerDisponiblePolice) -> "resolu".
let etapeAventurePolice = "choix";
let carteActuellePolice = null;
let detournerDisponiblePolice = true;
let messageErreurPolice = "";
let messageResoluPolice = "";

function ouvrirAventurePolicePartie(partie) {
    partieActive = partie;
    etapeAventurePolice = "choix";
    detournerDisponiblePolice = true;
    messageErreurPolice = "";
    if (constantesAventurePolice === null) {
        constantesAventurePolice = appelerBridge("constantes_aventure_police_web");
    }
    carteActuellePolice = appelerBridge("tirer_carte_police_web", JSON.stringify(partieActive));
    rendreAventurePolice();
    masquerTousLesEcrans();
    document.getElementById("ecran-aventure-police").classList.remove("cachee");
}

function rendreAventurePolice() {
    document.getElementById("titre-aventure-police").textContent = `Police - Niveau ${partieActive.niveau}`;

    const description = document.getElementById("description-aventure-police");
    const carteActuelle = document.getElementById("carte-actuelle-aventure-police");
    const choix = document.getElementById("choix-aventure-police");
    const messageErreur = document.getElementById("message-erreur-aventure-police");
    const messageResolu = document.getElementById("message-resolu-aventure-police");
    const boutonContinuer = document.getElementById("bouton-continuer-aventure-police");

    description.classList.toggle("cachee", etapeAventurePolice !== "choix");
    carteActuelle.classList.toggle("cachee", etapeAventurePolice !== "choix");
    choix.classList.toggle("cachee", etapeAventurePolice !== "choix");
    messageErreur.classList.toggle("cachee", etapeAventurePolice !== "choix" || !messageErreurPolice);
    messageResolu.classList.toggle("cachee", etapeAventurePolice !== "resolu");
    boutonContinuer.classList.toggle("cachee", etapeAventurePolice !== "resolu");

    if (etapeAventurePolice === "choix") {
        description.textContent = DESCRIPTION_POLICE;
        const carte = carteActuellePolice;
        carteActuelle.innerHTML = `
            <div class="candidat-recompense carte-actuelle-police">
                <span class="etoile-${carte.rarete.toLowerCase()}">★</span>
                <img src="${carte.image}" alt="${carte.nom}">
                <div class="candidat-recompense-nom">${carte.nom}</div>
                <div class="candidat-recompense-cout">⚡ ${carte.cout}</div>
                <div class="candidat-recompense-description">${texteEffetCarte(carte)}</div>
            </div>`;

        const { cout_mettre_aux_normes } = constantesAventurePolice;
        const options = [
            ["confiscation", ICONE_CONFISCATION, "Confiscation", "Supprime cette carte de votre deck."],
            ["mettre_aux_normes", ICONE_METTRE_AUX_NORMES, "Mettre aux normes", `Payez ${cout_mettre_aux_normes} € et gardez la carte.`],
            ["detourner", ICONE_DETOURNER, "Detourner l'attention", "Tire une autre carte (une seule fois)."],
        ].filter(([identifiant]) => identifiant !== "detourner" || detournerDisponiblePolice);
        choix.innerHTML = options
            .map(([identifiant, image, titre, texte]) => construireLigneChoixHtml(identifiant, image, titre, texte))
            .join("");
        document.querySelectorAll("#choix-aventure-police .choix-aventure").forEach((element) => {
            element.addEventListener("click", () => cliquerChoixPolice(element.dataset.choix));
        });

        messageErreur.textContent = messageErreurPolice;
    } else {
        messageResolu.textContent = messageResoluPolice;
    }
}

function cliquerChoixPolice(identifiant) {
    if (identifiant === "confiscation") {
        const carte = carteActuellePolice;
        partieActive = appelerBridge("confiscation_police_web", JSON.stringify(partieActive), carte.id_carte);
        messageResoluPolice = `Carte confisquee : ${carte.nom}.`;
        etapeAventurePolice = "resolu";
    } else if (identifiant === "mettre_aux_normes") {
        const resultat = appelerBridge("mettre_aux_normes_police_web", JSON.stringify(partieActive));
        if (resultat.succes) {
            partieActive = resultat.partie;
            messageResoluPolice = `Vous mettez ${carteActuellePolice.nom} aux normes.`;
            etapeAventurePolice = "resolu";
        } else {
            messageErreurPolice = "Argent insuffisant pour mettre cette carte aux normes.";
        }
    } else if (identifiant === "detourner") {
        carteActuellePolice = appelerBridge("tirer_carte_police_web", JSON.stringify(partieActive));
        detournerDisponiblePolice = false;
        messageErreurPolice = "";
    }
    rendreAventurePolice();
}

function terminerAventurePolice() {
    const partie = appelerBridge("terminer_aventure_police_web", JSON.stringify(partieActive));
    sauvegarderPartieLocale(joueurCourant.id, partie);
    ouvrirChoixNiveauPartie(partie);
}

// Ecran generique pour une etape sans contenu prepare (Planete commerciale - specs.md 2.4 etape
// 9, 9.1) : reutilise l'icone/description de LIBELLES_TYPE_ETAPE (definie plus bas, pour l'ecran
// "Choix du prochain niveau") avec un message explicite et un bouton "J'ai termine" qui avance
// simplement au niveau suivant - meme logique que
// main.py:_ouvrir_etape_placeholder cote PC.
const TITRES_TYPE_ETAPE = {
    AVENTURE: "Aventure",
    PLANETE_COMMERCIALE: "Planete commerciale",
};

function ouvrirEtapePlaceholderPartie(partie, type) {
    partieActive = partie;
    const [image] = LIBELLES_TYPE_ETAPE[type];
    document.getElementById("titre-etape-placeholder").textContent = `${TITRES_TYPE_ETAPE[type]} - Niveau ${partie.niveau}`;
    document.getElementById("image-etape-placeholder").src = image;
    masquerTousLesEcrans();
    document.getElementById("ecran-etape-placeholder").classList.remove("cachee");
}

function terminerEtapePlaceholder() {
    const partie = appelerBridge("terminer_etape_placeholder_web", JSON.stringify(partieActive));
    sauvegarderPartieLocale(joueurCourant.id, partie);
    ouvrirChoixNiveauPartie(partie);
}

// Ecran "Choix du prochain niveau" (specs.md 2.3/2.4) : 3 propositions d'etape d'ordinaire, ou
// une seule (BOSS) a un niveau Boss (multiple de 10) - decision utilisateur, meme ecran de choix,
// juste une seule carte "Combattre le Boss !" au lieu de 3. Pas encore reliee a une orchestration
// de parcours (qui n'existe pas encore), exposee sur window pour test manuel en attendant.
// Icones (deja leur propre cadre + nom incruste, images fournies par l'utilisateur) et
// description par type d'etape - memes textes que le PC (src/ui/ecran_choix_niveau.py).
const LIBELLES_TYPE_ETAPE = {
    PRIME: ["assets/prochain_niveau/prime.png", "Combat, contrat de chasseur de primes."],
    STATION_SERVICE: ["assets/prochain_niveau/station_service.png", "Entretien du vaisseau contre de l'Argent."],
    PLANETE_COMMERCIALE: ["assets/prochain_niveau/planete_commerciale.png", "Achat de cartes contre de l'Argent."],
    AVENTURE: ["assets/prochain_niveau/aventure.png", "Evenement inconnu."],
    BOSS: ["assets/prochain_niveau/boss.png", "Combattre le Boss !"],
};

function afficherChoixNiveau(resultat) {
    document.getElementById("titre-choix-niveau").textContent = `Niveau ${resultat.niveau}`;
    document.getElementById("candidats-niveau").innerHTML = resultat.propositions
        .map((type, index) => {
            const [image, description] = LIBELLES_TYPE_ETAPE[type];
            return `
        <div class="candidat-niveau" data-index="${index}">
            <img src="${image}" alt="${type}">
            <div class="candidat-niveau-description">${description}</div>
        </div>`;
        })
        .join("");
    document.querySelectorAll(".candidat-niveau").forEach((element) => {
        element.addEventListener("click", () => choisirEtape(resultat.propositions[Number(element.dataset.index)]));
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-choix-niveau").classList.remove("cachee");
}

// Types de proposition deja relies a un combat reel (specs.md 2.4) : Station service, Planete
// commerciale et Aventure ne le sont pas encore, cf. choisirEtape - meme liste que
// main.py:TYPES_COMBAT cote PC.
const TYPES_COMBAT = new Set(["PRIME", "BOSS"]);

function choisirEtape(type) {
    if (!partieActive) {
        console.log("Etape choisie :", type);
        return;
    }
    if (TYPES_COMBAT.has(type)) {
        appliquerResultat(appelerBridge("continuer_partie_web", JSON.stringify(partieActive)));
        masquerTousLesEcrans();
        document.getElementById("app").classList.remove("cachee");
    } else if (type === "STATION_SERVICE") {
        ouvrirStationServicePartie(partieActive);
    } else if (type === "AVENTURE") {
        // Trois aventures implementees (specs.md 2.5), tirage uniforme non deterministe cote
        // Python (type_aventure_web) - niveau fourni uniquement pour le forcage temporaire de
        // test cote bridge.py (_NIVEAUX_AVENTURE_FORCEE_POUR_TEST), sans effet sinon.
        const typeAventure = appelerBridge("type_aventure_web", partieActive.niveau);
        if (typeAventure === "TROIS_LUNES") {
            ouvrirAventureTroisLunesPartie(partieActive);
        } else if (typeAventure === "ASTEROIDES") {
            ouvrirAventureAsteroidesPartie(partieActive);
        } else {
            ouvrirAventurePolicePartie(partieActive);
        }
    } else {
        // Planete commerciale : contenu pas encore prepare (specs.md 2.4, 9.1).
        ouvrirEtapePlaceholderPartie(partieActive, type);
    }
}

function choixNiveau(partieJson) {
    afficherChoixNiveau(appelerBridge("choix_niveau_web", partieJson));
}

window.choixNiveau = choixNiveau;

// Ecran de fin de combat (parcours, specs.md 2.1/6). Meme situation que l'ecran de choix de
// module : pas encore reliee a une orchestration de parcours, exposee sur window pour test
// manuel en attendant. nouvelleDefaite() n'a besoin d'aucune donnee (texte fixe) ;
// nouvelleVictoire(graine) tire les candidats de recompense via bridge.py (un par module d'un
// vaisseau tire au sort - demo, pas un vrai combat termine pour l'instant).
function afficherFinCombat(victoire, candidats, niveau = null) {
    const titre = document.getElementById("titre-fin-combat");
    titre.textContent = victoire ? "VICTOIRE" : "DEFAITE";
    titre.className = victoire ? "victoire" : "defaite";
    const niveauElement = document.getElementById("niveau-fin-combat");
    niveauElement.textContent = niveau !== null ? `Niveau ${niveau}` : "";
    niveauElement.classList.toggle("cachee", niveau === null);
    document.getElementById("message-defaite").classList.toggle("cachee", victoire);
    document.getElementById("candidats-recompense").classList.toggle("cachee", !victoire);
    document.getElementById("instruction-fin-combat").classList.toggle("cachee", !victoire);
    // Rien a choisir en cas de defaite, ou de victoire sans aucun candidat (pool vide pour tous
    // les modules utilises) : un bouton "Continuer" suffit, meme situation que
    // src/ui/ecran_fin_combat.py cote PC.
    document.getElementById("bouton-continuer-fin-combat").classList.toggle("cachee", victoire && candidats.length > 0);

    if (victoire) {
        document.getElementById("candidats-recompense").innerHTML = candidats
            .map(
                (candidat, index) => `
        <div class="candidat-recompense" data-index="${index}">
            <div class="candidat-recompense-entete">
                <span class="etoile-${candidat.rarete.toLowerCase()}">★</span>
                <span>${candidat.module_nom}</span>
            </div>
            <img src="${candidat.image}" alt="${candidat.carte_nom}">
            <div class="candidat-recompense-nom">${candidat.carte_nom}</div>
            <div class="candidat-recompense-cout">⚡ ${candidat.cout}</div>
            <div class="candidat-recompense-description">${texteEffetCarte(candidat)}</div>
        </div>`
            )
            .join("");
        document.querySelectorAll(".candidat-recompense").forEach((element) => {
            element.addEventListener("click", () => choisirRecompense(candidats[Number(element.dataset.index)]));
        });
    }

    masquerTousLesEcrans();
    document.getElementById("ecran-fin-combat").classList.remove("cachee");
}

function choisirRecompense(candidat) {
    if (!partieActive) {
        console.log("Carte choisie :", candidat.carte_nom);
        return;
    }
    finaliserVictoirePartie(candidat.carte_id);
}

function nouvelleVictoire(graine = null) {
    afficherFinCombat(true, appelerBridge("fin_combat_victoire", graine));
}

function nouvelleDefaite() {
    afficherFinCombat(false, []);
}

window.nouvelleVictoire = nouvelleVictoire;
window.nouvelleDefaite = nouvelleDefaite;

// Fin d'un combat reel (specs.md 2.4) : appelee depuis la banniere de fin de combat (#app,
// cf. rendreBanniereFin) quand une partie reelle est en cours - remplace le "Rejouer" du mode
// demonstration par l'enchainement reel (fin de combat -> choix du niveau, ou defaite -> accueil),
// meme role que main.py:_ouvrir_fin_combat cote PC.
function terminerCombatPartie() {
    if (etatCourant.etat === "VICTOIRE") {
        const candidats = appelerBridge("candidats_recompense_partie_web", JSON.stringify(partieActive));
        afficherFinCombat(true, candidats, partieActive.niveau);
    } else {
        afficherFinCombat(false, [], partieActive.niveau);
    }
}

// Ajoute la carte choisie (ou aucune) au deck de la partie, puis avance au niveau suivant - sauf
// si c'etait un Boss, auquel cas l'ecran de victoire finale s'ouvre d'abord (specs.md 2.4, etape
// 11) - meme logique que main.py:_ouvrir_fin_combat cote PC.
function finaliserVictoirePartie(idCarte) {
    const resultat = appelerBridge("resoudre_victoire_partie_web", JSON.stringify(partieActive), idCarte);
    sauvegarderPartieLocale(joueurCourant.id, resultat.partie);
    if (resultat.niveau_boss) {
        ouvrirVictoireFinalePartie(resultat.partie);
    } else {
        ouvrirChoixNiveauPartie(resultat.partie);
    }
}

// Bouton "Continuer" de l'ecran de fin de combat (defaite, ou victoire sans aucun candidat de
// recompense) : rien a choisir, un clic suffit a continuer - meme situation que
// src/ui/ecran_fin_combat.py:on_mouse_press cote PC.
function continuerApresFinCombat() {
    if (!partieActive) return;
    if (etatCourant.etat === "DEFAITE") {
        const partie = appelerBridge("abandonner_partie_web", JSON.stringify(partieActive));
        sauvegarderPartieLocale(joueurCourant.id, partie);
        partieActive = null;
        afficherAccueilJoueur();
    } else {
        finaliserVictoirePartie(null);
    }
}

// Ecran de victoire finale (specs.md 2.4, etape 11) : felicite le joueur a la victoire du Boss (le
// run s'arrete reellement au Niveau 10 dans l'etat actuel, specs.md 2), affiche son deck complet
// (meme rendu que l'ecran "Voir le deck" ci-dessous, mais scope aux elements de cet ecran pour ne
// pas melanger les gestionnaires de clic des deux grilles) et propose un bouton "Continuer" qui
// marque la partie TERMINEE et revient a l'ecran de partie - meme logique que
// main.py:_ouvrir_victoire_finale cote PC.
let cartesVictoireFinaleAffichees = [];

function ouvrirVictoireFinalePartie(partie) {
    partieActive = partie;
    const cartes = appelerBridge("deck_partie_web", JSON.stringify(partie));
    cartesVictoireFinaleAffichees = cartes;
    document.getElementById("grille-victoire-finale").innerHTML = cartes
        .map(
            (carte, index) => `
        <div class="carte-deck" data-index="${index}">
            <span class="etoile-${carte.rarete.toLowerCase()}">★</span>
            ${carte.quantite > 1 ? `<span class="carte-deck-quantite">×${carte.quantite}</span>` : ""}
            <img src="${carte.image}" alt="${carte.nom}">
            <div class="carte-deck-nom">${carte.nom}</div>
            <div class="carte-deck-cout">⚡ ${carte.cout}</div>
        </div>`
        )
        .join("");
    document.getElementById("info-carte-victoire-finale").innerHTML = "";
    document.querySelectorAll("#grille-victoire-finale .carte-deck").forEach((element) => {
        element.addEventListener("click", () =>
            afficherInfoCarteVictoireFinale(cartesVictoireFinaleAffichees[Number(element.dataset.index)])
        );
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-victoire-finale").classList.remove("cachee");
}

function afficherInfoCarteVictoireFinale(carte) {
    document.getElementById("info-carte-victoire-finale").innerHTML = `
        <img src="${carte.image}" alt="${carte.nom}">
        <div class="info-carte-nom">${carte.nom}</div>
        <div class="info-carte-effet">${texteEffetCarte(carte)}</div>
        <div class="info-carte-cout">⚡ ${carte.cout}</div>`;
}

function terminerVictoireFinale() {
    const partie = appelerBridge("terminer_victoire_finale_web", JSON.stringify(partieActive));
    sauvegarderPartieLocale(joueurCourant.id, partie);
    partieActive = null;
    afficherAccueilJoueur();
}

// Ecran "deck en entier" (appelable depuis plusieurs endroits du parcours, specs.md 6). Meme
// situation que les deux ecrans precedents : pas encore reliee a un vrai bouton dans l'UI,
// exposee sur window pour test manuel. Pas d'infobulle au survol (web simplifie par rapport a
// pyglet, cf. CLAUDE.md) : taper une carte affiche sa description dans un popup, meme principe
// que #info-carte pour la main en combat.
let cartesDeckAffichees = [];

function afficherDeck(cartes) {
    cartesDeckAffichees = cartes;
    document.getElementById("grille-deck").innerHTML = cartes
        .map(
            (carte, index) => `
        <div class="carte-deck" data-index="${index}">
            <span class="etoile-${carte.rarete.toLowerCase()}">★</span>
            ${carte.quantite > 1 ? `<span class="carte-deck-quantite">×${carte.quantite}</span>` : ""}
            <img src="${carte.image}" alt="${carte.nom}">
            <div class="carte-deck-nom">${carte.nom}</div>
            <div class="carte-deck-cout">⚡ ${carte.cout}</div>
        </div>`
        )
        .join("");
    document.getElementById("info-carte-deck").innerHTML = "";
    document.querySelectorAll(".carte-deck").forEach((element) => {
        element.addEventListener("click", () => afficherInfoCarteDeck(cartesDeckAffichees[Number(element.dataset.index)]));
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-deck").classList.remove("cachee");
}

function afficherInfoCarteDeck(carte) {
    document.getElementById("info-carte-deck").innerHTML = `
        <img src="${carte.image}" alt="${carte.nom}">
        <div class="info-carte-nom">${carte.nom}</div>
        <div class="info-carte-effet">${texteEffetCarte(carte)}</div>
        <div class="info-carte-cout">⚡ ${carte.cout}</div>`;
}

function voirDeck(graine = null) {
    afficherDeck(appelerBridge("etat_deck", graine));
}

window.voirDeck = voirDeck;

// Selection/creation de profil joueur, puis accueil de ce joueur (specs.md 10.3) : nouveau point
// d'entree reel de l'app (appele par demarrer() ci-dessus, plus besoin de window.xxx() pour
// tester manuellement). Persistance via localStorage (Pyodide n'a pas de FS persistante entre
// recharges de page) : un index de profils (CLE_JOUEURS) + une entree de partie par joueur.
const CLE_JOUEURS = "space_fight_joueurs";

function clePartie(joueurId) {
    return `space_fight_partie_${joueurId}`;
}

function listerJoueursLocal() {
    try {
        return JSON.parse(localStorage.getItem(CLE_JOUEURS) || "[]");
    } catch {
        return [];
    }
}

function ajouterJoueurLocal(profil) {
    const joueurs = listerJoueursLocal();
    joueurs.push(profil);
    localStorage.setItem(CLE_JOUEURS, JSON.stringify(joueurs));
}

function partieLocale(joueurId) {
    const brut = localStorage.getItem(clePartie(joueurId));
    return brut ? JSON.parse(brut) : null;
}

function sauvegarderPartieLocale(joueurId, partie) {
    localStorage.setItem(clePartie(joueurId), JSON.stringify(partie));
}

let joueurCourant = null;

function afficherSelectionJoueur() {
    const joueurs = listerJoueursLocal();
    document.getElementById("liste-joueurs").innerHTML = joueurs
        .map((joueur, index) => `<div class="ligne-joueur" data-index="${index}">${joueur.nom}</div>`)
        .join("");
    document.querySelectorAll(".ligne-joueur").forEach((element) => {
        element.addEventListener("click", () => choisirJoueur(joueurs[Number(element.dataset.index)]));
    });
    document.getElementById("nom-nouveau-joueur").value = "";
    masquerTousLesEcrans();
    document.getElementById("ecran-selection-joueur").classList.remove("cachee");
}

function creerNouveauJoueur() {
    const champ = document.getElementById("nom-nouveau-joueur");
    const nom = champ.value.trim();
    if (!nom) return;
    const profil = appelerBridge("creer_profil_web", nom);
    ajouterJoueurLocal(profil);
    choisirJoueur(profil);
}

function choisirJoueur(profil) {
    joueurCourant = profil;
    afficherAccueilJoueur();
}

function afficherAccueilJoueur() {
    // Retour a l'accueil = plus aucune orchestration de parcours en cours (specs.md 2.4) :
    // remet le mode demonstration par defaut pour les ecrans window.xxx() appeles manuellement.
    partieActive = null;
    const partie = partieLocale(joueurCourant.id);
    const enCours = partie !== null && partie.statut === "EN_COURS";
    document.getElementById("nom-joueur-accueil").textContent = joueurCourant.nom;
    document.getElementById("niveau-accueil").textContent = enCours ? `Niveau ${partie.niveau}` : "";
    document.getElementById("vaisseau-accueil").classList.toggle("cachee", !enCours);
    document.getElementById("boutons-partie-en-cours").classList.toggle("cachee", !enCours);
    document.getElementById("bouton-nouvelle-partie").classList.toggle("cachee", enCours);

    if (enCours) {
        const vaisseau = appelerBridge("infos_vaisseau_web", JSON.stringify(partie));
        document.getElementById("vaisseau-accueil").innerHTML = Object.entries(vaisseau)
            .map(([_position, etat]) => {
                if (!etat) return `<div class="module-accueil module-accueil-vide">Emplacement vide</div>`;
                return `
                <div class="module-accueil">
                    <img src="${etat.image}" alt="${etat.nom}">
                    <div class="module-accueil-nom">${etat.nom}</div>
                    <div class="module-accueil-pv">${etat.pv} / ${etat.pv_max} PV</div>
                    <div class="module-accueil-niveau">Mise a jour : niveau ${etat.niveau_maj}</div>
                </div>`;
            })
            .join("");
    }

    masquerTousLesEcrans();
    document.getElementById("ecran-accueil-joueur").classList.remove("cachee");
}

function continuerPartie() {
    const partie = partieLocale(joueurCourant.id);
    // Reprend l'etape courante a partir de ce qui est deja connu (niveau + vaisseau) plutot que
    // d'une "etape courante" dediee, pas encore ajoutee a la sauvegarde (decision utilisateur) :
    // le Niveau 1 sans 2e module equipe reprend au choix de module, sinon on retire les
    // propositions du niveau courant - meme condition que main.py:_traiter_action cote PC.
    if (partie.niveau === 1 && partie.vaisseau.avant_gauche === null) {
        ouvrirChoixModulePartie(partie);
        return;
    }
    ouvrirChoixNiveauPartie(partie);
}

function abandonnerPartie() {
    const partie = partieLocale(joueurCourant.id);
    const misAJour = appelerBridge("abandonner_partie_web", JSON.stringify(partie));
    sauvegarderPartieLocale(joueurCourant.id, misAJour);
    afficherAccueilJoueur();
}

function voirDeckPartie() {
    const partie = partieLocale(joueurCourant.id);
    afficherDeck(appelerBridge("deck_partie_web", JSON.stringify(partie)));
}

// Seul moyen de fermer l'ecran "deck en entier" et de revenir a l'ecran de partie (celui-ci a
// deja ete masque en ouvrant l'ecran deck, cf. masquerTousLesEcrans dans afficherDeck).
function retourDepuisDeck() {
    afficherAccueilJoueur();
}

function nouvellePartie() {
    const partie = appelerBridge("nouvelle_partie_web");
    sauvegarderPartieLocale(joueurCourant.id, partie);
    ouvrirChoixModulePartie(partie);
}

document.getElementById("fin-tour").addEventListener("click", finirTour);
document.getElementById("bouton-creer-joueur").addEventListener("click", creerNouveauJoueur);
document.getElementById("nom-nouveau-joueur").addEventListener("keydown", (evenement) => {
    if (evenement.key === "Enter") creerNouveauJoueur();
});
document.getElementById("bouton-continuer").addEventListener("click", continuerPartie);
document.getElementById("bouton-abandonner").addEventListener("click", abandonnerPartie);
document.getElementById("bouton-voir-deck-partie").addEventListener("click", voirDeckPartie);
document.getElementById("bouton-nouvelle-partie").addEventListener("click", nouvellePartie);
document.getElementById("bouton-continuer-fin-combat").addEventListener("click", continuerApresFinCombat);
document.getElementById("bouton-termine-station-service").addEventListener("click", terminerStationServicePartie);
document.getElementById("bouton-continuer-aventure-trois-lunes").addEventListener("click", terminerAventureTroisLunes);
document.getElementById("bouton-continuer-aventure-asteroides").addEventListener("click", cliquerContinuerAsteroides);
document.getElementById("bouton-prendre-aventure-asteroides").addEventListener("click", prendreCarteAsteroides);
document.getElementById("bouton-passer-aventure-asteroides").addEventListener("click", passerCarteAsteroides);
document.getElementById("bouton-continuer-aventure-police").addEventListener("click", terminerAventurePolice);
document.getElementById("bouton-continuer-victoire-finale").addEventListener("click", terminerVictoireFinale);
document.getElementById("bouton-termine-etape-placeholder").addEventListener("click", terminerEtapePlaceholder);
document.getElementById("bouton-retour-deck").addEventListener("click", retourDepuisDeck);
demarrer();
