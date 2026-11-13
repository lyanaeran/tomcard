// Version web de Space Fight (navigateur / iPhone).
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
// Plus longue que DUREE_INFOBULLE_MS : laisse le temps de lire les deux phrases (accroche
// narrative) d'un module, meme principe que DUREE_INFOBULLE_MODULE cote pc
// (src/ui/ecran_vaisseau.py).
const DUREE_INFOBULLE_MODULE_MS = 4000;

// Casse-cache manuel : GitHub Pages ne permet pas de fixer les en-tetes
// Cache-Control, et Safari iOS garde volontiers une vieille version de ces
// fichiers en cache malgre un rechargement simple. A incrementer a chaque
// modification de app.js/bridge.py qui change le contrat entre les deux.
const VERSION_CACHE = "83";

// Emplacements des 4 modules equipes, mesures sur assets/modules/principal.png
// (978x965) - memes reperes que _EMPLACEMENTS_MODULES_IMAGE dans
// src/ui/fenetre.py, convertis en pourcentages CSS (origine haut-gauche) pour
// un positionnement absolu independant de la taille d'affichage.
const EMPLACEMENTS_MODULES = {
    AR_G: { left: 23.52, top: 0, width: 25.56, height: 22.8 },
    AV_G: { left: 59.31, top: 0, width: 25.56, height: 22.8 },
    AR_D: { left: 23.52, top: 77.2, width: 25.56, height: 22.8 },
    AV_D: { left: 59.31, top: 77.2, width: 25.56, height: 22.8 },
};

const RACINE_PYODIDE = "/repo/";

const FICHIERS_A_MONTER = [
    "src/__init__.py",
    "src/gameplay/__init__.py",
    "src/gameplay/carte.py",
    "src/gameplay/carte_new.py",
    "src/gameplay/ciblage.py",
    "src/gameplay/combat.py",
    "src/gameplay/combat_new.py",
    "src/gameplay/deck.py",
    "src/gameplay/deck_new.py",
    "src/gameplay/deroulement.py",
    "src/gameplay/donnees.py",
    "src/gameplay/ennemi.py",
    "src/gameplay/ennemi_new.py",
    "src/gameplay/flotte.py",
    "src/gameplay/flotte_new.py",
    "src/gameplay/journal.py",
    "src/gameplay/joueur.py",
    "src/gameplay/module.py",
    "src/gameplay/module_new.py",
    "src/gameplay/parcours.py",
    "src/gameplay/partie.py",
    "src/gameplay/position.py",
    "src/gameplay/statut_new.py",
    "src/gameplay/vaisseau.py",
    "src/gameplay/vaisseau_new.py",
    "config/cartes.json",
    "config/carte_new.json",
    "config/ennemis.json",
    "config/ennemi_new.json",
    "config/modules.json",
    "config/module_new.json",
];

let pyodide = null;
let etatCourant = null;
let indexCarteSelectionnee = null;

// Partie en cours d'orchestration (specs.md 2.4), null hors parcours (selection et accueil du
// joueur). Il n'y a plus de mode demonstration : on ne joue que par le parcours.
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
    } catch (erreur) {
        // Sans ceci, une exception Python (ou une erreur pyodide) echouait silencieusement : le
        // clic ne produisait visiblement "rien" cote joueur, sans aucun message pour diagnostiquer
        // (bug constate par l'utilisateur - POC experimental, pas de gestion d'erreur globale).
        console.error(`appelerBridge(${nomFonction}) a echoue :`, erreur);
        alert(`Erreur (${nomFonction}) : ${erreur && erreur.message ? erreur.message : erreur}`);
        throw erreur;
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
    "ecran-choix-carte-module",
    "ecran-choix-niveau",
    "ecran-station-service",
    "ecran-aventure-trois-lunes",
    "ecran-aventure-asteroides",
    "ecran-aventure-police",
    "ecran-etape-placeholder",
    "ecran-fin-combat",
    "ecran-victoire-finale",
    "ecran-deck",
    "ecran-vaisseau",
    "ecran-journal-combat",
];

function masquerTousLesEcrans() {
    IDS_ECRANS.forEach((id) => document.getElementById(id).classList.add("cachee"));
    // Masquees par defaut a chaque changement d'ecran : seul le Combat les reaffiche explicitement
    // (actualiserBarreLaterale(true), appelee depuis rendre()) - sans ce reset, elles resteraient
    // visibles en passant par exemple de Station service a l'accueil ou au combat.
    document.getElementById("barre-laterale").classList.add("cachee");
    document.getElementById("controles-combat").classList.add("cachee");
}

async function demarrer() {
    const statut = document.getElementById("statut-chargement");
    try {
        statut.textContent = "Chargement de Pyodide...";
        pyodide = await loadPyodide();
        statut.textContent = "Montage du code du jeu...";
        await monterDepot(pyodide);
        if (!versionsAccordees()) {
            recharger(statut);
            return;
        }
        statut.remove();
        afficherSelectionJoueur();
        tenterVerrouillagePaysage();
        configurerPleinEcran();
    } catch (erreur) {
        statut.textContent = `Erreur de chargement : ${erreur.message}`;
        console.error(erreur);
    }
}

// Juste apres une mise en ligne, le telephone peut encore garder en cache l'ancien index.html /
// app.js (GitHub Pages autorise 10 minutes) alors que bridge.py, recharge sans cache, est deja
// le nouveau : les deux ne se comprennent plus (bug constate sur iPhone, 2026-11-13). bridge.py
// annonce donc sa version (VERSION_WEB), qui doit etre egale a VERSION_CACHE.
function versionsAccordees() {
    try {
        return appelerBridgeSansAlerte("version_web") === VERSION_CACHE;
    } catch {
        // Un bridge.py trop ancien n'a pas version_web : versions differentes
        return false;
    }
}

function appelerBridgeSansAlerte(nomFonction) {
    const fonctionPython = pyodide.globals.get(nomFonction);
    if (!fonctionPython) throw new Error(`${nomFonction} absente`);
    try {
        return JSON.parse(fonctionPython());
    } finally {
        fonctionPython.destroy();
    }
}

// Recharge la page en contournant le cache (adresse differente), deux fois au plus par session
// pour ne jamais boucler ; ensuite, un message demande de reessayer plus tard.
const CLE_RECHARGEMENTS_VERSION = "space_fight_rechargements_version";

function recharger(statut) {
    let essais = 0;
    try {
        essais = Number(sessionStorage.getItem(CLE_RECHARGEMENTS_VERSION) || "0");
        sessionStorage.setItem(CLE_RECHARGEMENTS_VERSION, String(essais + 1));
    } catch {
        essais = 2;
    }
    if (essais >= 2) {
        statut.textContent = "Mise à jour du jeu en cours : ferme l'app et réessaie dans quelques minutes.";
        return;
    }
    statut.textContent = "Mise à jour du jeu...";
    location.replace(`${location.pathname}?maj=${Date.now()}`);
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
    // Une infobulle ouverte decrit l'etat d'avant l'action : on la ferme
    clearTimeout(minuteurInfobulle);
    document.getElementById("info-case").innerHTML = "";
    rendre();
    afficherPopups(resultat.popups);
}

// Journal de combat (specs/refonte-branchement.md 4.5) : etatCourant.journal est la liste des
// evenements de CombatNew.journal (des faits : qui, sur qui, combien, detail leurre / renvoi /
// bouclier / PV), serialises par bridge.py:_evenement_json. Les fonctions ci-dessous ne font que
// les mettre en phrase et en couleur, jamais decider de ce qui s'est produit - meme role que le
// journal cote PC. Les cartes jouees sans effet propre au journal (CARTE_JOUEE) ne donnent pas de
// ligne : leurs effets (degats, statut, reparation...) en donnent une chacun.
function segmentJournal(texte, classe) {
    return `<span class="${classe}">${texte}</span>`;
}

const CLASSES_GENRE_JOURNAL = { carte: "journal-carte", ennemi: "journal-ennemi", module: "journal-module" };

function nomJournal(nom, genre) {
    return segmentJournal(nom, CLASSES_GENRE_JOURNAL[genre] || "journal-texte");
}

const NOMS_STATUT_JOURNAL = { BOUCLIER: "bouclier", INCENDIE: "incendie", RENVOI: "renvoi", LEURRE: "leurre" };

// Detail des degats recus : "6 degats, 2 absorbes par le bouclier, 4 PV perdus (46 restants)".
function detailDegatsJournal(evenement) {
    const morceaux = [`${evenement.valeur} dégâts`];
    if (evenement.annules_leurre) morceaux.push("annulés par le leurre");
    if (evenement.renvoyes) morceaux.push(`${evenement.renvoyes} renvoyés`);
    if (evenement.absorbes_bouclier) morceaux.push(`${evenement.absorbes_bouclier} absorbés par le bouclier`);
    if (evenement.pv_perdus || !evenement.annules_leurre) {
        morceaux.push(`${evenement.pv_perdus} PV perdus (${evenement.pv_restants} restants)`);
    }
    return morceaux.join(", ");
}

function construireLigneJournal(evenement) {
    const source = evenement.source_nom ? nomJournal(evenement.source_nom, evenement.source_genre) : "";
    const cible = evenement.cible_nom ? nomJournal(evenement.cible_nom, evenement.cible_genre) : "";
    const texte = (t) => segmentJournal(t, "journal-texte");
    switch (evenement.nature) {
        case "DEBUT_TOUR":
            return segmentJournal(`--- Tour ${evenement.valeur} ---`, "journal-tour");
        case "ATTAQUE":
            return `${source}${texte(" → ")}${cible}${texte(` : ${detailDegatsJournal(evenement)}`)}`;
        case "RENVOI":
            return `${texte("Renvoi → ")}${cible}${texte(` : ${detailDegatsJournal(evenement)}`)}`;
        case "INCENDIE":
            return `${texte("Incendie sur ")}${cible}${texte(` : ${detailDegatsJournal(evenement)}`)}`;
        case "STATUT_POSE": {
            const nom = NOMS_STATUT_JOURNAL[evenement.statut] || evenement.statut;
            const valeur = evenement.statut === "LEURRE" ? "" : ` ${evenement.valeur}`;
            const debut = source ? `${source}${texte(" → ")}` : "";
            return `${debut}${cible}${texte(` : ${nom}${valeur}`)}`;
        }
        case "REPARATION":
            return `${source}${texte(" → ")}${cible}${texte(` : +${evenement.valeur} PV (${evenement.pv_restants} restants)`)}`;
        case "ELECTRICITE":
            return `${source}${texte(` : +${evenement.valeur} électricité`)}`;
        case "PIOCHE":
            return `${source}${texte(` : ${evenement.valeur} carte(s) piochée(s)`)}`;
        case "REPETITION":
            return `${source}${texte(` : ${evenement.valeur} carte(s) lancée(s) une fois de plus`)}`;
        case "MODULE_DETRUIT":
        case "ENNEMI_DETRUIT":
            return `${cible}${texte(" détruit")}`;
        case "CARTES_HORS_SERVICE":
            return `${cible}${texte(` : ${evenement.valeur} carte(s) hors service`)}`;
        case "VICTOIRE":
            return segmentJournal("Victoire", "journal-tour");
        case "DEFAITE":
            return segmentJournal("Défaite", "journal-tour");
        default:
            return "";
    }
}

function jouerCarte(index, idCase) {
    appliquerResultat(appelerBridge("jouer_carte", index, idCase));
}

function finirTour() {
    appliquerResultat(appelerBridge("finir_tour"));
}

// Ouvert "en survol" par-dessus le Combat en cours (specs.md 8.1) : lit etatCourant.journal a
// l'ouverture (instantane du combat en cours), le gameplay est la seule source de verite.
function ouvrirJournalCombat() {
    const conteneur = document.getElementById("liste-journal-combat");
    conteneur.innerHTML = etatCourant.journal
        .map(construireLigneJournal)
        .filter(Boolean)
        .map((ligne) => `<div class="ligne-journal">${ligne}</div>`)
        .join("");
    document.getElementById("ecran-journal-combat").classList.remove("cachee");
    conteneur.scrollTop = conteneur.scrollHeight;
}

function fermerJournalCombat() {
    document.getElementById("ecran-journal-combat").classList.add("cachee");
}

function quitterCombat() {
    // Bouton "Quitter" (specs.md 8.1) : ferme le combat sans le reporter ni le sauvegarder - la
    // partie sauvegardee reste telle qu'elle etait avant ce combat (CombatNew travaille sur des
    // copies), qui repartira de zero au prochain "Continuer".
    partieActive = null;
    joueurCourant = null;
    afficherSelectionJoueur();
}

// Plusieurs popups sur la meme case (tour ennemi, attaque repetee) : decales dans le temps, rang
// compte par case, pour rester lisibles sans retarder ceux des autres cases.
const DECALAGE_POPUP_MS = 300;

function afficherPopups(popups) {
    const rangParCase = {};
    popups.forEach((popup) => {
        const element = document.querySelector(`.case.${popup.camp}[data-id="${popup.id}"]`);
        if (!element) return;
        const cle = `${popup.camp}:${popup.id}`;
        const rang = rangParCase[cle] ?? 0;
        rangParCase[cle] = rang + 1;
        const bulle = document.createElement("div");
        bulle.className = `popup popup-${popup.couleur}`;
        bulle.style.animationDelay = `${rang * DECALAGE_POPUP_MS}ms`;
        bulle.textContent = popup.texte;
        element.appendChild(bulle);
        setTimeout(() => bulle.remove(), DUREE_POPUP_MS + rang * DECALAGE_POPUP_MS);
    });
}

// Un tap sur une carte l'arme et affiche son infobulle (#info-carte) ; il faut ensuite taper une
// case valide pour la jouer, meme pour une carte qui touche un ensemble fixe (tous les ennemis,
// le principal...) : jamais de resolution automatique (specs.md 8.3, flux identique au PC).
function selectionnerCarte(carte) {
    if (etatCourant.etat !== "EN_COURS") return;
    indexCarteSelectionnee = indexCarteSelectionnee === carte.index ? null : carte.index;
    rendre();
}

function carteSelectionnee() {
    if (indexCarteSelectionnee === null) return null;
    return etatCourant.main.find((c) => c.index === indexCarteSelectionnee) ?? null;
}

// Confirme la carte armee sur la case touchee, si c'est une de ses cases valides : ces cases sont
// decidees par le gameplay (CombatNew.cibles_possibles, via bridge.py), jamais en JS.
function cliquerCase(idCase, typeCase) {
    const carte = carteSelectionnee();
    if (!carte) return;
    if (typeCase !== carte.camp || !carte.cases.includes(idCase)) return;
    jouerCarte(carte.index, idCase);
}

function trouverObjetCase(idCase, typeCase) {
    if (typeCase === "allie") {
        if (idCase === "base") return etatCourant.vaisseau.base;
        return etatCourant.vaisseau.modules.find((m) => m && m.id === idCase) ?? null;
    }
    return etatCourant.ennemis.find((e) => e && e.id === idCase) ?? null;
}

// Texte d'un effet d'ennemi (son prochain tour) : symbole d'attaque 7 x2 -> Lanceur
// de missiles, symbole de bouclier 10, symbole de renvoi 5 -> un allie. La cible prevue vient du
// gameplay (CombatNew.intentions).
function texteEffetEnnemi(effet) {
    const repetitions = effet.repetitions > 1 ? ` ×${effet.repetitions}` : "";
    const symbole = { ATTAQUE: "⚔", BOUCLIER: "🛡", RENVOI: "↩" }[effet.nature] || "?";
    let cible = "";
    if (effet.cible === "TOUS") cible = " → tous";
    else if (effet.cible === "ALLIE") cible = " → un allié";
    else if (effet.cible === "MODULE") cible = effet.cible_nom ? ` → ${effet.cible_nom}` : " → module le plus proche";
    return `${symbole} ${effet.valeur}${repetitions}${cible}`;
}

// Version courte, dans la case de l'ennemi : symbole et valeur, "x2" si repetee, "tous" pour une
// attaque de tous les modules. Le module vise par une attaque porte une pastille cible (cf.
// pastillesStatuts) ; le detail est dans l'infobulle.
function texteEffetEnnemiCourt(effet) {
    const repetitions = effet.repetitions > 1 ? `×${effet.repetitions}` : "";
    const symbole = { ATTAQUE: "⚔", BOUCLIER: "🛡", RENVOI: "↩" }[effet.nature] || "?";
    return `${symbole}${effet.valeur}${repetitions}${effet.cible === "TOUS" ? " tous" : ""}`;
}

// Statuts d'un module ou d'un ennemi, en clair, pour son infobulle (uniquement les actifs).
function lignesStatuts(objet) {
    const lignes = [];
    if (objet.bouclier) lignes.push(`🛡 Bouclier ${objet.bouclier}`);
    if (objet.incendie) lignes.push(`🔥 Incendie ${objet.incendie}`);
    if (objet.renvoi) lignes.push(`↩ Renvoi ${objet.renvoi}`);
    if (objet.leurre) lignes.push("🎭 Leurre");
    return lignes;
}

let minuteurInfobulle = null;

// Infobulle d'une case tapee sans carte armee (equivalent tactile du survol PC), dans le meme
// panneau flottant centre que #info-carte. Ennemi : seulement les actions de son prochain tour, une
// par ligne, sans titre ni cycle complet (decision utilisateur, 2026-11-13, refonte-branchement.md
// 4.3).
function afficherInfobulle(idCase, typeCase) {
    const objet = trouverObjetCase(idCase, typeCase);
    if (!objet) return;
    clearTimeout(minuteurInfobulle);
    const lignes = [`<div class="infobulle-nom">${objet.nom}</div>`, `<div>❤️ ${objet.pv}/${objet.pv_max}</div>`];
    lignesStatuts(objet).forEach((ligne) => lignes.push(`<div>${ligne}</div>`));
    if (typeCase === "allie") {
        if (objet.detruit && objet.hors_service) {
            lignes.push(`<div>${objet.hors_service} carte(s) hors service</div>`);
        }
        if (objet.menaces.length > 0) {
            lignes.push(`<div class="infobulle-titre-cycle">Visé au prochain tour par :</div>`);
            objet.menaces.forEach((menace) => {
                const repetitions = menace.repetitions > 1 ? ` ×${menace.repetitions}` : "";
                lignes.push(`<div class="infobulle-etape-courante">${menace.ennemi} : ⚔ ${menace.valeur}${repetitions}</div>`);
            });
        }
    } else if (!objet.detruit) {
        // Une action du prochain tour par ligne, sans titre (decision utilisateur, 2026-11-13)
        objet.intention.forEach((effet) => {
            lignes.push(`<div class="infobulle-etape-courante">${texteEffetEnnemi(effet)}</div>`);
        });
    }
    const panneau = document.getElementById("info-case");
    panneau.innerHTML = lignes.join("");
    minuteurInfobulle = setTimeout(() => {
        panneau.innerHTML = "";
    }, DUREE_INFOBULLE_MS + 1500);
}

// Tap sur une case : sans carte armee, affiche son infobulle ; sinon, confirme la carte armee.
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

// Pastilles d'une case (refonte-branchement.md 4.2/4.3), de droite a gauche : PV (rouge),
// Bouclier (bleu), puis Incendie (orange), Renvoi (violet), Leurre (cyan) seulement s'ils sont
// actifs. Masquees si detruit (le bandeau "Detruit" les remplace).
function pastillesStatuts(objet) {
    const pastilles = [
        `<span class="pastille pastille-pv">${objet.pv}</span>`,
        `<span class="pastille pastille-bouclier">${objet.bouclier}</span>`,
    ];
    if (objet.incendie) pastilles.push(`<span class="pastille pastille-incendie">🔥${objet.incendie}</span>`);
    if (objet.renvoi) pastilles.push(`<span class="pastille pastille-renvoi">↩${objet.renvoi}</span>`);
    if (objet.leurre) pastilles.push(`<span class="pastille pastille-leurre">🎭</span>`);
    if (objet.menaces && objet.menaces.length > 0) pastilles.push(`<span class="pastille pastille-cible">🎯</span>`);
    return pastilles.join("");
}

function rendrePastilles(objet) {
    if (objet.detruit) return "";
    return `<div class="pastilles-case">${pastillesStatuts(objet)}</div>`;
}

// Pastilles du module principal : a droite du nez du vaisseau, en colonne (PV en haut).
function rendrePastillesBase(base) {
    if (base.detruit) return "";
    return `<div class="pastilles-base">${pastillesStatuts(base)}</div>`;
}

function etiquetteDetruit(objet) {
    if (!objet.detruit) return "";
    const horsService = objet.hors_service ? `<span class="hors-service-case">${objet.hors_service} HS</span>` : "";
    return `<div class="etiquette-detruite">DÉTRUIT${horsService}</div>`;
}

function classesCase(objet, typeCase, base) {
    const classes = [...base];
    if (objet.detruit) classes.push("detruit");
    const carte = carteSelectionnee();
    if (carte && carte.camp === typeCase && carte.cases.includes(objet.id)) classes.push("case-valide");
    return classes;
}

// Intention de l'ennemi pour son prochain tour (refonte-branchement.md 4.3), sous son image.
function rendreIntention(objet) {
    if (objet.detruit || objet.intention.length === 0) return "";
    return `<div class="intention">${objet.intention.map(texteEffetEnnemiCourt).join(" ")}</div>`;
}

function rendreCaseEnnemi(objet, style) {
    if (objet === null) {
        return `<div class="case case-vide" style="${style}"></div>`;
    }
    const classes = classesCase(objet, "ennemi", ["case", "ennemi"]);
    if (objet.fusionne) classes.push("case-fusionnee");
    return `
        <div class="${classes.join(" ")}" style="${style}" data-id="${objet.id}" data-type="ennemi">
            <img src="${objet.image}" alt="${objet.nom}">
            ${rendrePastilles(objet)}
            ${rendreIntention(objet)}
            ${etiquetteDetruit(objet)}
        </div>`;
}

function rendreGrilleJoueur() {
    const base = etatCourant.vaisseau.base;
    const parIndex = Object.fromEntries(etatCourant.vaisseau.modules.map((m) => [m && m.id, m]));

    const emplacements = Object.entries(EMPLACEMENTS_MODULES)
        .map(([id, rect]) => {
            const module = parIndex[id];
            if (!module) return "";
            const classes = classesCase(module, "allie", ["case", "allie", "emplacement-module"]);
            const style = `left:${rect.left}%; top:${rect.top}%; width:${rect.width}%; height:${rect.height}%;`;
            return `
                <div class="${classes.join(" ")}" style="${style}" data-id="${module.id}" data-type="allie">
                    <img src="${module.image}" alt="${module.nom}">
                    ${rendrePastilles(module)}
                    ${etiquetteDetruit(module)}
                </div>`;
        })
        .join("");

    const classesBase = classesCase(base, "allie", ["case", "allie", "vaisseau-base"]);
    return `
        <div class="grille grille-joueur">
            <div class="${classesBase.join(" ")}" data-id="base" data-type="allie">
                <img class="image-vaisseau" src="${base.image}" alt="${base.nom}">
                ${emplacements}
                ${rendrePastillesBase(base)}
                ${etiquetteDetruit(base)}
            </div>
        </div>`;
}

// Une paire (Avant, Arriere) par rangee. Un ennemi sur les deux cases de sa rangee (le Boss) est
// place explicitement sur les 2 colonnes : sa case Arriere n'est pas publiee par bridge.py.
const RANGEES_GRILLE_ENNEMIS = [
    ["AV_G", "AR_G", 1],
    ["AV_M", "AR_M", 2],
    ["AV_D", "AR_D", 3],
];

function rendreGrilleEnnemis() {
    const parIndex = Object.fromEntries(etatCourant.ennemis.filter(Boolean).map((e) => [e.id, e]));
    const cellules = RANGEES_GRILLE_ENNEMIS.map(([idAvant, idArriere, ligne]) => {
        const avant = parIndex[idAvant] ?? null;
        if (avant && avant.fusionne) {
            return rendreCaseEnnemi(avant, `grid-row:${ligne}; grid-column:1 / span 2;`);
        }
        const arriere = parIndex[idArriere] ?? null;
        return (
            rendreCaseEnnemi(avant, `grid-row:${ligne}; grid-column:1;`) +
            rendreCaseEnnemi(arriere, `grid-row:${ligne}; grid-column:2;`)
        );
    });
    return `
        <div class="grille grille-ennemis">
            ${cellules.join("")}
        </div>`;
}

// Couleur de l'etoile de rarete (specs.md 8.2), meme mapping que le PC.
const CLASSE_ETOILE_RARETE = {
    BASE: "etoile-base",
    COMMUNE: "etoile-commune",
    RARE: "etoile-rare",
    LEGENDAIRE: "etoile-legendaire",
};

// Munitions "restantes/de depart" (refonte-branchement.md 4.1), rien pour une carte illimitee.
function texteMunitions(carte) {
    if (carte.munitions_base === null) return "";
    const restantes = carte.munitions_restantes ?? carte.munitions_base;
    return `${restantes}/${carte.munitions_base}`;
}

// Carte en main (refonte-branchement.md 4.1) : illustration, rarete, cout, munitions, "x2" si
// elle est lancee plus d'une fois, bandeau Persistante ; grisee si elle n'est pas jouable
// maintenant (decide par le gameplay : CombatNew.peut_jouer).
function rendreMain() {
    return etatCourant.main
        .map((carte) => {
            const classes = ["carte"];
            if (carte.index === indexCarteSelectionnee) classes.push("selectionnee");
            if (!carte.jouable) classes.push("injouable");
            const munitions = texteMunitions(carte);
            return `
            <button class="${classes.join(" ")}" data-index="${carte.index}" title="${carte.nom}">
                <img src="${carte.image}" alt="${carte.nom}">
                <span class="etoile-rarete ${CLASSE_ETOILE_RARETE[carte.rarete]}">★</span>
                <span class="pastille pastille-cout">⚡${carte.cout}</span>
                ${munitions ? `<span class="pastille pastille-munition">${munitions}</span>` : ""}
                ${carte.lancements > 1 ? `<span class="pastille pastille-lancements">×${carte.lancements}</span>` : ""}
                ${carte.persistante ? '<span class="bandeau-persistante">PERSISTANTE</span>' : ""}
                <span class="nom-carte-main">${carte.nom}</span>
            </button>`;
        })
        .join("");
}

// Texte d'une carte, partout (combat, recompenses, deck, Aventures) : la description de
// config/carte_new.json avec ses valeurs actuelles, fournie par le gameplay (description_affichee).
function texteEffetCarte(carte) {
    return carte.description;
}

// Details d'une carte sous sa description : munitions, lancements, Persistante, module.
function detailsCarte(carte) {
    const lignes = [];
    const munitions = texteMunitions(carte);
    if (munitions) lignes.push(`🔋 Munitions ${munitions}`);
    if (carte.lancements > 1) lignes.push(`Lancée ${carte.lancements} fois`);
    if (carte.persistante) lignes.push("Persistante");
    if (carte.module_nom) lignes.push(`Module : ${carte.module_nom}`);
    return lignes.map((ligne) => `<div class="info-carte-detail">${ligne}</div>`).join("");
}

// Infobulle de la carte armee (#info-carte), au centre de l'ecran. pointer-events:none (CSS) pour
// ne pas bloquer le tap sur la case qui suit.
function rendreInfoCarte() {
    const carte = carteSelectionnee();
    if (!carte) return "";
    const injouable = carte.jouable ? "" : '<div class="info-carte-detail">Pas jouable maintenant</div>';
    return `
        <img src="${carte.image}" alt="${carte.nom}">
        <div class="info-carte-nom">${carte.nom}</div>
        <div class="info-carte-effet">${texteEffetCarte(carte)}</div>
        <div class="info-carte-cout">⚡ ${carte.cout}</div>
        ${detailsCarte(carte)}
        ${injouable}`;
}

function rendreBanniereFin() {
    if (etatCourant.etat === "EN_COURS") return "";
    const texte = etatCourant.etat === "VICTOIRE" ? "Victoire !" : "Défaite";
    return `
        <div class="banniere-fin ${etatCourant.etat.toLowerCase()}">
            <span>${texte}</span>
            <button id="bouton-rejouer">Continuer</button>
        </div>`;
}

// Compteurs des piles (refonte-branchement.md 4.4) ; Hors service seulement si elle n'est pas vide.
function texteCompteursDeck() {
    const morceaux = [
        `Pioche ${etatCourant.pioche}`,
        `Défausse ${etatCourant.defausse}`,
        `Épuisées ${etatCourant.epuisees}`,
    ];
    if (etatCourant.hors_service) morceaux.push(`Hors service ${etatCourant.hors_service}`);
    return `Tour ${etatCourant.tour} · ${morceaux.join(" · ")}`;
}

function rendre() {
    document.getElementById("electricite").textContent =
        `⚡ ${etatCourant.electricite}/${etatCourant.electricite_max}`;
    document.getElementById("compteurs-deck").textContent = texteCompteursDeck();
    document.getElementById("grille-joueur-conteneur").innerHTML = rendreGrilleJoueur();
    document.getElementById("grille-ennemis-conteneur").innerHTML = rendreGrilleEnnemis();
    document.getElementById("main").innerHTML = rendreMain();
    document.getElementById("info-carte").innerHTML = rendreInfoCarte();
    document.getElementById("banniere").innerHTML = rendreBanniereFin();

    const boutonTourSuivant = document.getElementById("tour-suivant");
    boutonTourSuivant.disabled = etatCourant.etat !== "EN_COURS";

    document.querySelectorAll(".case[data-id]").forEach((element) => {
        attacherPressionCase(element, element.dataset.id, element.dataset.type);
    });
    actualiserBarreLaterale(true);

    document.querySelectorAll(".carte").forEach((element) => {
        const carte = etatCourant.main.find((c) => c.index === Number(element.dataset.index));
        element.addEventListener("click", () => selectionnerCarte(carte));
    });
    const boutonRejouer = document.getElementById("bouton-rejouer");
    if (boutonRejouer) boutonRejouer.addEventListener("click", terminerCombatPartie);
}

// Ecran de choix de module (parcours, Niveau 1 - specs.md 2.3). Pas encore reliee a une
// orchestration de parcours (qui n'existe pas encore) : exposee sur window pour etre appelee
// manuellement (console du navigateur) en attendant. nouveauChoixModule(graine) tire les
// candidats via bridge.py puis affiche l'ecran ; choisirModule ne fait encore que logger le
// choix, aucun etat de parcours a mettre a jour pour l'instant.
function afficherChoixModule(candidats) {
    document.getElementById("titre-choix-module").textContent = "Nouveau module";
    document.getElementById("candidats-module").innerHTML = candidats
        .map((candidat, index) => construireLigneChoixHtml(String(index), candidat.image, candidat.nom, candidat.description))
        .join("");
    document.querySelectorAll("#candidats-module .choix-aventure").forEach((element) => {
        element.addEventListener("click", () => choisirModule(candidats[Number(element.dataset.choix)]));
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-choix-module").classList.remove("cachee");
    actualiserBarreLaterale();
}

function choisirModule(candidat) {
    // Equipe le module et tire jusqu'a 3 cartes de son pool (src/gameplay/deroulement.py) : le
    // joueur en choisit une a ajouter a son deck, ou passe - meme logique que le PC.
    const resultat = appelerBridge("choisir_module_partie_web", JSON.stringify(partieActive), candidat.id);
    partieActive = resultat.partie;
    sauvegarderPartieLocale(joueurCourant.id, resultat.partie);
    if (resultat.candidats.length === 0) {
        // Pool vide pour ce module : ecran saute directement, meme comportement que le PC.
        resoudreCarteModule(null);
        return;
    }
    afficherChoixCarteModule(resultat.module_nom, resultat.candidats);
}

function afficherChoixCarteModule(nomModule, candidats) {
    document.getElementById("titre-choix-carte-module").textContent = `Nouvelle carte pour ${nomModule}`;
    document.getElementById("candidats-carte-module").innerHTML = candidats
        .map(
            (candidat, index) => `
        <div class="candidat-recompense" data-index="${index}">
            <span class="etoile-${candidat.rarete.toLowerCase()}">★</span>
            <img src="${candidat.image}" alt="${candidat.nom}">
            <div class="candidat-recompense-nom">${candidat.nom}</div>
            <div class="candidat-recompense-cout">⚡ ${candidat.cout}</div>
            <div class="candidat-recompense-description">${texteEffetCarte(candidat)}</div>
        </div>`
        )
        .join("");
    document.querySelectorAll("#candidats-carte-module .candidat-recompense").forEach((element) => {
        element.addEventListener("click", () => choisirCarteModule(candidats[Number(element.dataset.index)]));
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-choix-carte-module").classList.remove("cachee");
    actualiserBarreLaterale();
}

function choisirCarteModule(candidat) {
    resoudreCarteModule(candidat);
}

// Bouton "Passer" de l'ecran de choix de carte de module (specs.md 8.3, point 7 utilisateur).
function passerCarteModule() {
    resoudreCarteModule(null);
}

// Ajoute la carte choisie (ou aucune, bouton Passer) au deck puis avance au niveau suivant. La
// carte est renvoyee avec son module de rattachement, decide par le gameplay (bridge.py).
function resoudreCarteModule(candidat) {
    allerA(
        appelerBridge(
            "resoudre_carte_module_web",
            JSON.stringify(partieActive),
            candidat ? candidat.id_carte : null,
            candidat ? candidat.module : null
        )
    );
}

// Aiguillage vers l'ecran decide par src/gameplay/deroulement.py (via bridge.py, resultat
// {partie, ecran}) : web/app.js ne decide jamais lui-meme de l'ecran suivant (CLAUDE.md), il
// sauvegarde la partie et affiche l'ecran - meme role que main.py:_aller_a cote PC.
function allerA(resultat) {
    const partie = resultat.partie;
    sauvegarderPartieLocale(joueurCourant.id, partie);
    partieActive = partie;
    const ouvertures = {
        ACCUEIL: () => {
            partieActive = null;
            afficherAccueilJoueur();
        },
        CHOIX_MODULE: () => ouvrirChoixModulePartie(partie),
        CHOIX_NIVEAU: () => ouvrirChoixNiveauPartie(partie),
        COMBAT: () => ouvrirCombatPartie(partie),
        STATION_SERVICE: () => ouvrirStationServicePartie(partie),
        AVENTURE_TROIS_LUNES: () => ouvrirAventureTroisLunesPartie(partie),
        AVENTURE_ASTEROIDES: () => ouvrirAventureAsteroidesPartie(partie),
        AVENTURE_POLICE: () => ouvrirAventurePolicePartie(partie),
        PLANETE_COMMERCIALE: () => ouvrirEtapePlaceholderPartie(partie, "PLANETE_COMMERCIALE"),
        VICTOIRE_FINALE: () => ouvrirVictoireFinalePartie(partie),
    };
    ouvertures[resultat.ecran]();
}

// Combat Prime/Boss d'une partie reelle (vaisseau/deck reels, cf. continuer_partie_web).
function ouvrirCombatPartie(partie) {
    partieActive = partie;
    masquerTousLesEcrans();
    document.getElementById("app").classList.remove("cachee");
    appliquerResultat(appelerBridge("continuer_partie_web", JSON.stringify(partie)));
}

// Ouvre le choix de module (Niveau 1) pour une partie reelle - appelee a la creation d'une
// partie et par la reprise du bouton "Continuer" (cf. continuerPartie), sur decision de
// src/gameplay/deroulement.py (cf. allerA).
function ouvrirChoixModulePartie(partie) {
    partieActive = partie;
    afficherChoixModule(appelerBridge("choix_module_partie_web", JSON.stringify(partie)));
}

// Ouvre le choix du prochain niveau pour une partie reelle (cf. allerA).
function ouvrirChoixNiveauPartie(partie) {
    partieActive = partie;
    afficherChoixNiveau(appelerBridge("choix_niveau_web", JSON.stringify(partie)));
}

// Ecran Station service (specs.md 2.2) : 4 actions gratuites (Reparer/Ameliorer/Mettre a jour/
// Deplacer) appliquees a un module de la partie active, avant de revenir au choix du prochain
// niveau (etape 8, specs.md 2.4). Meme regles que src/ui/ecran_station_service.py cote PC -
// bridge.py n'applique que les fonctions pures de src/gameplay/partie.py, aucune regle dupliquee
// ici (CLAUDE.md).
// Icones avec cadre/nom incruste (assets/station_service/avec_texte/) - decision utilisateur :
// cet ecran garde sa grille d'icones seules (pas la ligne image+texte des Aventures/Choix du
// prochain niveau/specs.md 2.5), donc les versions sans texte de assets/station_service/
// (reutilisees telles quelles par les Aventures Trois lunes/Police) ne conviennent plus ici sans
// ajouter un texte redondant - anciennes icones restaurees depuis l'historique git, pour cet
// ecran uniquement. Memes chemins que main.py:ecran_station_service.py:ACTIONS cote PC.
const ACTIONS_STATION_SERVICE = [
    ["reparer", "assets/station_service/avec_texte/reparer.png"],
    ["ameliorer", "assets/station_service/avec_texte/ameliorer.png"],
    ["mettre_a_jour", "assets/station_service/avec_texte/mettre_a_jour.png"],
    ["deplacer", "assets/station_service/avec_texte/deplacer.png"],
];
// Reparer ne vise que le principal (decision 2, specs/refonte-branchement.md) : sa fonction ne
// prend pas d'emplacement (cf. cliquerActionStation).
const FONCTIONS_ACTION_STATION_SERVICE = {
    reparer: "reparer_principal_web",
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
        coutActionStationService = appelerBridge("constantes_station_service_web").cout;
    }
    masquerTousLesEcrans();
    document.getElementById("ecran-station-service").classList.remove("cachee");
    rendreStationService();
}

function instructionStationService() {
    if (modeDeplacementStation) return "Cliquez l'emplacement de destination (ou recliquez le module pour annuler).";
    if (positionSelectionneeStation === null) {
        return "Selectionnez un module, puis une action (Réparer soigne toujours le principal).";
    }
    return "Selectionnez une action pour ce module.";
}

function rendreStationService() {
    document.getElementById("titre-station-service").textContent = "Station service";
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
    actualiserBarreLaterale();
}

function cliquerModuleStation(position, estVide) {
    let popupEchec = null;
    if (modeDeplacementStation) {
        if (position === positionSelectionneeStation) {
            modeDeplacementStation = false;
        } else if (POSITIONS_DEPLACABLES_STATION.includes(position)) {
            const positionSource = positionSelectionneeStation;
            // deplacer_module_web (bridge.py) verifie et deduit l'Argent elle-meme - son champ
            // "succes" est la seule source de verite, jamais reverifie ici (cf. CLAUDE.md,
            // gameplay commun aux deux interfaces).
            const resultat = appelerBridge("deplacer_module_web", JSON.stringify(partieActive), positionSource, position);
            modeDeplacementStation = false;
            positionSelectionneeStation = null;
            if (resultat.succes) {
                partieActive = resultat.partie;
                sauvegarderPartieLocale(joueurCourant.id, partieActive);
            } else {
                popupEchec = positionSource;
            }
        }
    } else if (!estVide) {
        positionSelectionneeStation = position;
    }
    // Le popup doit etre ajoute apres rendreStationService() (rendu via innerHTML, cf.
    // rendreStationService plus bas), sans quoi le re-rendu l'effacerait aussitot.
    rendreStationService();
    if (popupEchec !== null) {
        afficherPopupStation(popupEchec, "Argent insuffisant !", "popup-degats");
    }
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
    // Reparer s'applique toujours au principal, sans selection (decision 2)
    if (action === "reparer") positionSelectionneeStation = "base";
    if (positionSelectionneeStation === null) return;
    if (action === "deplacer") {
        if (POSITIONS_DEPLACABLES_STATION.includes(positionSelectionneeStation)) {
            modeDeplacementStation = true;
        }
        rendreStationService();
        return;
    }
    const position = positionSelectionneeStation;
    const { pv: pvAvant, pv_max: pvMaxAvant } = partieActive.vaisseau[position];
    // reparer_module_web/ameliorer_module_web/mettre_a_jour_module_web (bridge.py) verifient et
    // deduisent l'Argent elles-memes - leur champ "succes" est la seule source de verite, jamais
    // reverifie ici (cf. CLAUDE.md, gameplay commun aux deux interfaces).
    const resultat =
        action === "reparer"
            ? appelerBridge(FONCTIONS_ACTION_STATION_SERVICE[action], JSON.stringify(partieActive))
            : appelerBridge(FONCTIONS_ACTION_STATION_SERVICE[action], JSON.stringify(partieActive), position);
    // Deselectionne dans tous les cas (demande utilisateur) : le popup ci-dessous suffit a
    // confirmer l'effet ou l'echec, pas besoin de garder le module arme pour reessayer.
    positionSelectionneeStation = null;
    if (!resultat.succes) {
        rendreStationService();
        afficherPopupStation(position, "Argent insuffisant !", "popup-degats");
        return;
    }
    partieActive = resultat.partie;
    sauvegarderPartieLocale(joueurCourant.id, partieActive);
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
    allerA(appelerBridge("terminer_etape_web", JSON.stringify(partieActive)));
}

// Ligne d'un choix d'Aventure (specs.md 2.5) : image carree a gauche (aucune -> case vide en
// attendant un visuel dedie), rectangle de texte (titre + description) a droite - meme
// presentation pour les 3 ecrans d'Aventure (Trois lunes/Asteroides/Police).
function construireLigneChoixHtml(identifiant, image, titre, texte, classesSupplementaires = "") {
    const imageHtml = image ? `<img src="${image}" alt="${titre}">` : "";
    return `
        <div class="choix-aventure${classesSupplementaires}" data-choix="${identifiant}">
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
// Reutilisent les icones de assets/station_service/, desormais sans texte incruste (fournies par
// l'utilisateur) - le titre est de toute facon toujours redessine a cote dans le rectangle de
// texte.
const ICONE_REPARER = "assets/station_service/reparer.png";
const ICONE_AMELIORER = "assets/station_service/ameliorer.png";
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
    masquerTousLesEcrans();
    document.getElementById("ecran-aventure-trois-lunes").classList.remove("cachee");
    rendreAventureTroisLunes();
}

function rendreAventureTroisLunes() {
    document.getElementById("titre-aventure-trois-lunes").textContent = "Trois lunes";

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
            ["reparer", ICONE_REPARER, "Reparer le vaisseau", `Le module principal regagne ${pv_reparation_vaisseau} PV.`],
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
        groupesDeckAventureTroisLunes = appelerBridge("deck_partie_web", JSON.stringify(partieActive));
        deck.innerHTML = groupesDeckAventureTroisLunes
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
        document.querySelectorAll("#deck-aventure-trois-lunes .carte-deck").forEach((element) => {
            element.addEventListener("click", () => cliquerCarteTroisLunes(Number(element.dataset.index)));
        });
    } else {
        messageResolu.textContent = messageResoluAventureTroisLunes;
    }
    actualiserBarreLaterale();
}

function cliquerChoixTroisLunes(identifiant) {
    const { pv_reparation_vaisseau } = constantesAventureTroisLunes;
    if (identifiant === "reparer") {
        partieActive = appelerBridge("reparer_vaisseau_aventure_web", JSON.stringify(partieActive));
        messageResoluAventureTroisLunes = `Le module principal regagne ${pv_reparation_vaisseau} PV !`;
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

function cliquerCarteTroisLunes(index) {
    // Une entree par carte et par module de rattachement (bridge.py) : on retire celle-ci
    const carte = groupesDeckAventureTroisLunes[index];
    partieActive = appelerBridge("retirer_carte_aventure_web", JSON.stringify(partieActive), carte.id_carte, carte.module);
    messageResoluAventureTroisLunes = `Carte retiree : ${carte.nom}.`;
    etapeAventureTroisLunes = "resolu";
    rendreAventureTroisLunes();
}

function terminerAventureTroisLunes() {
    allerA(appelerBridge("terminer_etape_web", JSON.stringify(partieActive)));
}

// Aventure "Asteroides" (specs.md 2.5) : deux choix - Traverser (sequence en 3 temps sur ce meme
// ecran, chaque etape validee par un bouton "Continuer") ou Affronter les pirates (combat scripte,
// delegue au meme pipeline qu'un combat Prime normal). Meme regles que
// src/ui/ecran_aventure_asteroides.py cote PC - bridge.py n'applique que les fonctions pures de
// src/gameplay/partie.py, aucune regle dupliquee ici.
const DESCRIPTION_ASTEROIDES =
    "Poursuivi par des pirates de l'espace, vous n'avez plus le choix : vaincre ou perir ! A moins que...";

// Reutilise l'icone de assets/prochain_niveau/prime.png, desormais sans texte incruste (fournie
// par l'utilisateur) - le titre est de toute facon toujours redessine a cote dans le rectangle de
// texte.
const ICONE_AFFRONTER = "assets/prochain_niveau/prime.png";

// Extrait du fond d'ecran de cette Aventure (assets/aventure/champ_asteroides.png) plutot qu'une
// icone distincte : aucune icone existante n'etait pertinente pour ce choix.
const ICONE_TRAVERSER = "assets/aventure/traverser.png";

const CHOIX_ASTEROIDES = [
    ["traverser", ICONE_TRAVERSER, "Traverser le champ d'asteroides", "Le module principal va en subir les consequences..."],
    ["affronter", ICONE_AFFRONTER, "Affronter les pirates", "Lance un combat contre 3 ennemis."],
];

// "choix" (2 choix) -> "sequence_2" (2e coup, apres le 1er deja applique au choix "Traverser") ->
// "sequence_3" (carte offerte, si trouvee) -> "resolu". Les chocs touchent toujours le principal
// (decision 3, specs/refonte-branchement.md) : plus de choix de module.
let etapeAventureAsteroides = "choix";
let carteOfferteAsteroides = null;
let messageAsteroides = "";

function ouvrirAventureAsteroidesPartie(partie) {
    partieActive = partie;
    etapeAventureAsteroides = "choix";
    carteOfferteAsteroides = null;
    masquerTousLesEcrans();
    document.getElementById("ecran-aventure-asteroides").classList.remove("cachee");
    rendreAventureAsteroides();
}

function rendreAventureAsteroides() {
    document.getElementById("titre-aventure-asteroides").textContent = "Asteroides";

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
    instruction.classList.add("cachee");
    modules.classList.add("cachee");
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
    actualiserBarreLaterale();
}

function cliquerChoixAsteroides(identifiant) {
    if (identifiant === "traverser") {
        traverserAsteroides();
    } else if (identifiant === "affronter") {
        masquerTousLesEcrans();
        document.getElementById("app").classList.remove("cachee");
        appliquerResultat(appelerBridge("combat_aventure_asteroides_web", JSON.stringify(partieActive)));
    }
}

function nomPrincipal() {
    return appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive)).base.nom;
}

// PV reellement perdus par le principal sur un choc : difference avant / apres, decidee par le
// gameplay (les chocs laissent toujours au moins 1 PV, la constante de degats ne suffit pas).
function pvPrincipal() {
    return partieActive.vaisseau.base.pv;
}

function traverserAsteroides() {
    const pvAvant = pvPrincipal();
    partieActive = appelerBridge("premier_choc_asteroides_web", JSON.stringify(partieActive));
    messageAsteroides = `Vous traversez le champ d'asteroides : ${nomPrincipal()} perd ${pvAvant - pvPrincipal()} PV.`;
    etapeAventureAsteroides = "sequence_2";
    rendreAventureAsteroides();
}

function continuerSequence2Asteroides() {
    const nom = nomPrincipal();
    const pvAvant = pvPrincipal();
    // Degats et tirage de la carte offerte (ou non) decides en un seul appel gameplay
    // (second_choc_asteroides) - jamais recalcule ici (CLAUDE.md).
    const resultat = appelerBridge("second_choc_asteroides_web", JSON.stringify(partieActive));
    partieActive = resultat.partie;
    carteOfferteAsteroides = resultat.carte;
    const choc = `Ces asteroides n'en finissent plus : ${nom} perd encore ${pvAvant - pvPrincipal()} PV. `;
    if (carteOfferteAsteroides === null) {
        etapeAventureAsteroides = "resolu";
        messageAsteroides = choc + "Vous parvenez finalement a vous degager.";
    } else {
        etapeAventureAsteroides = "sequence_3";
        messageAsteroides = choc + "Pres de la sortie, vous reperez des debris...";
    }
    rendreAventureAsteroides();
}

function prendreCarteAsteroides() {
    partieActive = appelerBridge(
        "prendre_carte_offerte_asteroides_web",
        JSON.stringify(partieActive),
        carteOfferteAsteroides.id_carte,
        carteOfferteAsteroides.module
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
        allerA(appelerBridge("terminer_etape_web", JSON.stringify(partieActive)));
    }
}

// Aventure "Police" (specs.md 2.5) : une carte du deck reel est tiree au hasard, puis 3 choix -
// Confiscation (retire la carte), Mettre aux normes (payer un cout fixe pour la garder), Detourner
// l'attention (retire une autre carte au hasard, disponible une seule fois par Aventure - le choix
// disparait ensuite). Meme regles que src/ui/ecran_aventure_police.py cote PC - bridge.py n'applique
// que les fonctions pures de src/gameplay/partie.py, aucune regle dupliquee ici.
const DESCRIPTION_POLICE =
    "Un vaisseau de patrouille vous somme de vous arreter pour un controle de routine...";

// Reutilise l'icone de assets/station_service/mettre_a_jour.png, desormais sans texte incruste
// (fournie par l'utilisateur) - le titre est de toute facon toujours redessine a cote dans le
// rectangle de texte.
const ICONE_METTRE_AUX_NORMES = "assets/station_service/mettre_a_jour.png";
const ICONE_CONFISCATION = "assets/aventure/confiscation.png";
const ICONE_DETOURNER = "assets/aventure/detourner.png";

let constantesAventurePolice = null;
// "choix" (2 ou 3 choix selon detournerDisponiblePolice) -> "resolu". carteActuellePolice et
// detournerDisponiblePolice ne sont jamais decides ici : ils refletent toujours la derniere
// reponse du gameplay (src/gameplay/partie.py:EtatAventurePolice, via bridge.py) - jamais suivis
// independamment cote JS (cf. CLAUDE.md, gameplay commun aux deux interfaces).
let etapeAventurePolice = "choix";
let carteActuellePolice = null;
let detournerDisponiblePolice = true;
let messageErreurPolice = "";
let messageResoluPolice = "";

function ouvrirAventurePolicePartie(partie) {
    partieActive = partie;
    etapeAventurePolice = "choix";
    messageErreurPolice = "";
    if (constantesAventurePolice === null) {
        constantesAventurePolice = appelerBridge("constantes_aventure_police_web");
    }
    const etat = appelerBridge("demarrer_aventure_police_web", JSON.stringify(partieActive));
    carteActuellePolice = etat.carte;
    detournerDisponiblePolice = etat.detourner_disponible;
    masquerTousLesEcrans();
    document.getElementById("ecran-aventure-police").classList.remove("cachee");
    rendreAventurePolice();
}

function rendreAventurePolice() {
    document.getElementById("titre-aventure-police").textContent = "Police";

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
    actualiserBarreLaterale();
}

function cliquerChoixPolice(identifiant) {
    if (identifiant === "confiscation") {
        const carte = carteActuellePolice;
        partieActive = appelerBridge("confiscation_police_web", JSON.stringify(partieActive));
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
        const resultat = appelerBridge("detourner_police_web", JSON.stringify(partieActive));
        if (resultat.succes) {
            carteActuellePolice = resultat.carte;
            detournerDisponiblePolice = resultat.detourner_disponible;
            messageErreurPolice = "";
        }
    }
    rendreAventurePolice();
}

function terminerAventurePolice() {
    allerA(appelerBridge("terminer_etape_web", JSON.stringify(partieActive)));
}

// Ecran generique pour une etape sans contenu prepare (Planete commerciale - specs.md 2.4 etape
// 9, 9.1) : reutilise l'icone/titre de LIBELLES_TYPE_ETAPE (definie plus bas, pour l'ecran
// "Choix du prochain niveau") avec un message explicite et un bouton "J'ai termine" qui avance
// simplement au niveau suivant (deroulement.terminer_etape).
function ouvrirEtapePlaceholderPartie(partie, type) {
    partieActive = partie;
    const [image, titre] = LIBELLES_TYPE_ETAPE[type];
    document.getElementById("titre-etape-placeholder").textContent = titre;
    document.getElementById("image-etape-placeholder").src = image;
    masquerTousLesEcrans();
    document.getElementById("ecran-etape-placeholder").classList.remove("cachee");
    actualiserBarreLaterale();
}

function terminerEtapePlaceholder() {
    allerA(appelerBridge("terminer_etape_web", JSON.stringify(partieActive)));
}

// Ecran "Choix du prochain niveau" (specs.md 2.3/2.4) : 3 propositions d'etape d'ordinaire, ou
// une seule (BOSS) a un niveau Boss (multiple de 10) - decision utilisateur, meme ecran de choix,
// juste une seule carte "Combattre le Boss !" au lieu de 3. Pas encore reliee a une orchestration
// de parcours (qui n'existe pas encore), exposee sur window pour test manuel en attendant.
// Icones (desormais sans texte incruste, fournies par l'utilisateur), titre et description par
// type d'etape - memes textes que le PC (src/ui/ecran_choix_niveau.py).
const LIBELLES_TYPE_ETAPE = {
    PRIME: ["assets/prochain_niveau/prime.png", "Prime", "Combat, contrat de chasseur de primes."],
    STATION_SERVICE: [
        "assets/prochain_niveau/station_service.png", "Station service", "Entretien du vaisseau contre de l'Argent.",
    ],
    PLANETE_COMMERCIALE: [
        "assets/prochain_niveau/planete_commerciale.png", "Planete commerciale", "Achat de cartes contre de l'Argent.",
    ],
    AVENTURE: ["assets/prochain_niveau/aventure.png", "Aventure", "Evenement inconnu."],
    BOSS: ["assets/prochain_niveau/boss.png", "Boss", "Combattre le Boss !"],
};

function afficherChoixNiveau(resultat) {
    document.getElementById("titre-choix-niveau").textContent = "Choix du prochain niveau";
    document.getElementById("candidats-niveau").innerHTML = resultat.propositions
        .map((type, index) => {
            const [image, titre, description] = LIBELLES_TYPE_ETAPE[type];
            return construireLigneChoixHtml(String(index), image, titre, description);
        })
        .join("");
    document.querySelectorAll("#candidats-niveau .choix-aventure").forEach((element) => {
        element.addEventListener("click", () => choisirEtape(resultat.propositions[Number(element.dataset.choix)]));
    });
    masquerTousLesEcrans();
    document.getElementById("ecran-choix-niveau").classList.remove("cachee");
    actualiserBarreLaterale();
}

// Etape choisie : l'ecran a ouvrir (combat, Station, Aventure tiree...) est decide par
// src/gameplay/deroulement.py (bridge.py:ecran_pour_etape_web).
function choisirEtape(type) {
    allerA({ partie: partieActive, ecran: appelerBridge("ecran_pour_etape_web", type) });
}

// Ecran de fin de combat (parcours, specs.md 2.1/6) : un candidat de recompense par module, deja
// rattache a ce module par le gameplay (deroulement.conclure_combat).
function afficherFinCombat(victoire, candidats) {
    const titre = document.getElementById("titre-fin-combat");
    titre.textContent = victoire ? "VICTOIRE" : "DEFAITE";
    titre.className = victoire ? "victoire" : "defaite";
    document.getElementById("message-defaite").classList.toggle("cachee", victoire);
    document.getElementById("candidats-recompense").classList.toggle("cachee", !victoire);
    document.getElementById("instruction-fin-combat").classList.toggle("cachee", !victoire);
    // Rien a choisir en cas de defaite, ou de victoire sans aucun candidat (pool vide pour tous
    // les modules utilises) : un bouton "Continuer" suffit, meme situation que
    // src/ui/ecran_fin_combat.py cote PC. Sinon (victoire avec au moins un candidat), bouton
    // "Passer" a la place (specs.md 8.3, point 7 utilisateur) : rien n'oblige a choisir une carte.
    document.getElementById("bouton-continuer-fin-combat").classList.toggle("cachee", victoire && candidats.length > 0);
    document.getElementById("bouton-passer-fin-combat").classList.toggle("cachee", !(victoire && candidats.length > 0));

    if (victoire) {
        document.getElementById("candidats-recompense").innerHTML = candidats
            .map(
                (candidat, index) => `
        <div class="candidat-recompense" data-index="${index}">
            <div class="candidat-recompense-entete">
                <span class="etoile-${candidat.rarete.toLowerCase()}">★</span>
                <span>${candidat.module_nom}</span>
            </div>
            <img src="${candidat.image}" alt="${candidat.nom}">
            <div class="candidat-recompense-nom">${candidat.nom}</div>
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
    actualiserBarreLaterale();
}

function choisirRecompense(candidat) {
    finaliserVictoirePartie(candidat);
}

// Fin d'un combat reel (specs.md 2.4) : appelee une seule fois depuis la banniere de fin de
// combat (#app, cf. rendreBanniereFin) quand une partie reelle est en cours. PV, Argent et
// candidats de recompense sont decides par src/gameplay/deroulement.py (conclure_combat).
function terminerCombatPartie() {
    const resultat = appelerBridge("conclure_combat_partie_web", JSON.stringify(partieActive));
    partieActive = resultat.partie;
    sauvegarderPartieLocale(joueurCourant.id, resultat.partie);
    afficherFinCombat(etatCourant.etat === "VICTOIRE", resultat.candidats);
}

// Ajoute la carte choisie (ou aucune) au deck de la partie ; l'ecran suivant (niveau suivant ou
// victoire finale apres le Boss) est decide par deroulement.resoudre_fin_combat.
function finaliserVictoirePartie(candidat) {
    allerA(
        appelerBridge(
            "resoudre_fin_combat_web",
            JSON.stringify(partieActive),
            true,
            candidat ? candidat.id_carte : null,
            candidat ? candidat.module : null
        )
    );
}

// Bouton "Continuer" de l'ecran de fin de combat (defaite, ou victoire sans aucun candidat de
// recompense) : rien a choisir, un clic suffit a continuer - meme situation que
// src/ui/ecran_fin_combat.py:on_mouse_press cote PC.
function continuerApresFinCombat() {
    if (!partieActive) return;
    if (etatCourant.etat === "DEFAITE") {
        allerA(appelerBridge("resoudre_fin_combat_web", JSON.stringify(partieActive), false, null, null));
    } else {
        finaliserVictoirePartie(null);
    }
}

// Bouton "Passer" de l'ecran de fin de combat victorieux (specs.md 8.3, point 7 utilisateur) :
// n'apparait que s'il y avait au moins un candidat a choisir (sinon "Continuer" suffit deja).
function passerFinCombat() {
    if (!partieActive) return;
    finaliserVictoirePartie(null);
}

// Ecran de victoire finale (specs.md 2.4, etape 11) : felicite le joueur a la victoire du Boss (le
// run s'arrete reellement au Niveau 10 dans l'etat actuel, specs.md 2), affiche son deck complet
// (meme rendu que l'ecran "Voir le deck" ci-dessous, mais scope aux elements de cet ecran pour ne
// pas melanger les gestionnaires de clic des deux grilles) et propose un bouton "Continuer" qui
// marque la partie TERMINEE et revient a l'ecran de partie (deroulement.terminer_victoire_finale).
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
    allerA(appelerBridge("terminer_victoire_finale_web", JSON.stringify(partieActive)));
}

// Ecran "deck en entier" (appelable depuis plusieurs endroits du parcours, specs.md 6). Meme
// situation que les deux ecrans precedents : pas encore reliee a un vrai bouton dans l'UI,
// exposee sur window pour test manuel. Pas d'infobulle au survol (web simplifie par rapport a
// pyglet, cf. CLAUDE.md) : taper une carte affiche sa description dans un popup, meme principe
// que #info-carte pour la main en combat.
let cartesDeckAffichees = [];

function construireGrilleDeck(cartes) {
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
}

function afficherDeck(cartes) {
    construireGrilleDeck(cartes);
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

// Partie sauvegardee du joueur, relue par le gameplay : une partie d'une ancienne version du jeu
// est ignoree, et effacee si elle etait en cours (decision 1, specs/refonte-branchement.md - le
// gameplay decide, cf. bridge.py:lire_partie_web).
function partieLocale(joueurId) {
    const brut = localStorage.getItem(clePartie(joueurId));
    if (!brut) return null;
    const lecture = appelerBridge("lire_partie_web", brut);
    if (lecture.effacer) localStorage.removeItem(clePartie(joueurId));
    return lecture.partie;
}

function sauvegarderPartieLocale(joueurId, partie) {
    localStorage.setItem(clePartie(joueurId), JSON.stringify(partie));
}

// Supprime definitivement un joueur (index CLE_JOUEURS) et sa partie sauvegardee eventuelle -
// action destructive, appelee uniquement apres confirmation (cf. bouton-supprimer-joueur dans
// afficherSelectionJoueur ci-dessous). Meme principe que src/gameplay/partie.py:supprimer_profil
// cote PC, mais purement localStorage ici (pas de FS Pyodide, cf. commentaire plus haut).
function supprimerJoueurLocal(joueurId) {
    const joueurs = listerJoueursLocal().filter((joueur) => joueur.id !== joueurId);
    localStorage.setItem(CLE_JOUEURS, JSON.stringify(joueurs));
    localStorage.removeItem(clePartie(joueurId));
}

let joueurCourant = null;

function afficherSelectionJoueur() {
    const joueurs = listerJoueursLocal();
    document.getElementById("liste-joueurs").innerHTML = joueurs
        .map(
            (joueur, index) => `
            <div class="ligne-joueur" data-index="${index}">
                <span class="nom-joueur">${joueur.nom}</span>
                <button class="bouton-supprimer-joueur" data-index="${index}" title="Supprimer ce joueur" aria-label="Supprimer ce joueur">
                    <img src="assets/interface/quitter.png" alt="">
                </button>
            </div>`
        )
        .join("");
    document.querySelectorAll(".ligne-joueur").forEach((element) => {
        element.addEventListener("click", () => choisirJoueur(joueurs[Number(element.dataset.index)]));
    });
    // Bouton croix rouge (specs.md 10.3) : stopPropagation pour ne pas aussi declencher le clic
    // de la ligne (choisirJoueur) qui le contient. confirm() natif plutot qu'une boite de dialogue
    // maison (aucune infrastructure de modale ailleurs dans ce projet web, cf. CLAUDE.md - pas
    // d'abstraction au-dela du necessaire) - suppression irreversible, jamais sans confirmation.
    document.querySelectorAll(".bouton-supprimer-joueur").forEach((element) => {
        element.addEventListener("click", (evenement) => {
            evenement.stopPropagation();
            const joueur = joueurs[Number(element.dataset.index)];
            if (confirm(`Vous allez detruire le joueur ${joueur.nom}, etes-vous sur ?`)) {
                supprimerJoueurLocal(joueur.id);
                afficherSelectionJoueur();
            }
        });
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
    // Retour a l'accueil = plus aucune orchestration de parcours en cours (specs.md 2.4)
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
    // Ecran de reprise decide par src/gameplay/deroulement.py (ecran_de_reprise).
    allerA({ partie, ecran: appelerBridge("ecran_reprise_web", JSON.stringify(partie)) });
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

// True quand #ecran-deck a ete ouvert via la barre laterale (ouvrirSurvolDeck) par-dessus l'ecran
// du parcours en cours, plutot que depuis le bouton "Voir le deck" de l'accueil (afficherDeck) -
// determine ou "Retour" doit ramener (juste refermer le survol, ou revenir a l'accueil).
let deckOuvertEnSurvol = false;

// Seul moyen de fermer l'ecran "deck en entier" et de revenir a l'ecran de partie (celui-ci a
// deja ete masque en ouvrant l'ecran deck, cf. masquerTousLesEcrans dans afficherDeck) - sauf en
// survol (barre laterale), ou l'ecran appelant n'a jamais ete masque (cf. ouvrirSurvolDeck).
function retourDepuisDeck() {
    if (deckOuvertEnSurvol) {
        deckOuvertEnSurvol = false;
        document.getElementById("ecran-deck").classList.add("cachee");
        return;
    }
    afficherAccueilJoueur();
}

// Barre laterale persistante des ecrans du parcours hors combat (specs.md 2.4/10.3), equivalent de
// src/ui/barre_laterale.py cote PC : Niveau, Argent, et deux boutons qui ouvrent le Deck/Vaisseau
// "en survol" par-dessus l'ecran appelant (#ecran-deck/#ecran-vaisseau passes en position:fixed
// pour cet usage, cf. .ecran-survol dans style.css) - sans le fermer, contrairement a
// afficherDeck/afficherAccueilJoueur qui masquent tous les autres ecrans. Chaque fonction de rendu
// d'un ecran avec barre laterale l'appelle a chaque (re)affichage pour rester a jour si l'Argent/
// le deck changent sans quitter l'ecran (Station service, Aventures).
function actualiserBarreLaterale(enCombat = false) {
    const barre = document.getElementById("barre-laterale");
    const controlesCombat = document.getElementById("controles-combat");
    // #controles-combat (Electricite/tour suivant/Quitter) reste affiche en Combat meme quand la
    // barre elle-meme ne l'est pas (sans partie ci-dessous, portrait, ecran trop etroit ou
    // chevauchement plus bas) : contrairement a Niveau/Argent/Deck/Vaisseau, mettre fin a son tour
    // reste une action essentielle (cf. commentaire CSS de #controles-combat, style.css).
    controlesCombat.classList.toggle("cachee", !enCombat);
    if (!partieActive) {
        // Pas de partie en cours : rien a afficher sur la barre elle-meme - "Quitter" reste
        // utilisable (revient simplement a la selection du joueur, cf. quitterCombat()).
        barre.classList.add("cachee");
        controlesCombat.classList.add("controles-combat-sans-barre");
        return;
    }
    document.getElementById("niveau-barre-laterale").textContent = `Niveau ${partieActive.niveau}`;
    document.getElementById("argent-barre-laterale").textContent = `${partieActive.argent} €`;
    document.getElementById("compteur-deck-barre-laterale").textContent = `${partieActive.deck.length} cartes`;
    barre.classList.remove("cachee");
    if (enCombat && barreChevaucheVaisseau()) {
        // Contrairement aux autres ecrans du parcours (largeur de grille fixe via clamp()), la
        // largeur du bloc vaisseau en Combat depend aussi de la hauteur d'ecran (--taille-case,
        // cf. style.css) : un seuil de largeur fixe ne suffit pas a garantir l'absence de
        // chevauchement sur tous les formats (fenetre large et haute, tablette en paysage...) -
        // verifie donc le chevauchement reel apres affichage plutot que de deviner un seuil.
        barre.classList.add("cachee");
    }
    if (enCombat) {
        // Empile #controles-combat sous la barre laterale quand elle est effectivement visible,
        // ou a sa place par defaut sinon (chevauchement ci-dessus, ou portrait/ecran etroit via le
        // media query qui masque #barre-laterale, cf. style.css) - passe par getComputedStyle
        // plutot que offsetParent, qui vaut toujours null pour un element position:fixed comme
        // celui-ci, visible ou non.
        const barreVisible = getComputedStyle(barre).display !== "none";
        controlesCombat.classList.toggle("controles-combat-sans-barre", !barreVisible);
    }
}

function barreChevaucheVaisseau() {
    const grilleJoueur = document.querySelector(".grille-joueur");
    if (!grilleJoueur) return false;
    const rectBarre = document.getElementById("barre-laterale").getBoundingClientRect();
    const rectGrille = grilleJoueur.getBoundingClientRect();
    return rectBarre.right > rectGrille.left;
}

function ouvrirSurvolDeck() {
    construireGrilleDeck(appelerBridge("deck_partie_web", JSON.stringify(partieActive)));
    deckOuvertEnSurvol = true;
    document.getElementById("ecran-deck").classList.remove("cachee");
}

// Vaisseau en survol (barre laterale) : cartes module en lecture seule, memes donnees que
// #vaisseau-accueil/#modules-station-service (infos_vaisseau_web) - jamais masque via
// masquerTousLesEcrans en s'ouvrant (cf. ouvrirSurvolDeck ci-dessus), donc pas besoin d'un
// equivalent de deckOuvertEnSurvol : "Retour" referme toujours simplement ce survol. Un tap sur
// un module affiche sa description (accroche narrative, specs.md 5) pendant
// DUREE_INFOBULLE_MODULE_MS, meme principe que #info-case (afficherInfobulle) - equivalent tactile
// du clic PC (src/ui/ecran_vaisseau.py:EcranVaisseau._dessiner_description).
let minuteurInfobulleVaisseau = null;
let modulesVaisseauAffiches = {};

function ouvrirSurvolVaisseau() {
    const vaisseau = appelerBridge("infos_vaisseau_web", JSON.stringify(partieActive));
    modulesVaisseauAffiches = vaisseau;
    document.getElementById("modules-vaisseau").innerHTML = Object.entries(vaisseau)
        .map(([position, etat]) => {
            if (!etat) return `<div class="module-accueil module-accueil-vide">Emplacement vide</div>`;
            return `
            <div class="module-accueil" data-position="${position}">
                <img src="${etat.image}" alt="${etat.nom}">
                <div class="module-accueil-nom">${etat.nom}</div>
                <div class="module-accueil-pv">${etat.pv} / ${etat.pv_max} PV</div>
                <div class="module-accueil-niveau">Mise a jour : niveau ${etat.niveau_maj}</div>
            </div>`;
        })
        .join("");
    document.getElementById("info-carte-vaisseau").innerHTML = "";
    document.querySelectorAll("#modules-vaisseau .module-accueil:not(.module-accueil-vide)").forEach((element) => {
        element.addEventListener("click", () => afficherDescriptionModuleVaisseau(element.dataset.position));
    });
    document.getElementById("ecran-vaisseau").classList.remove("cachee");
}

function afficherDescriptionModuleVaisseau(position) {
    const etat = modulesVaisseauAffiches[position];
    if (!etat) return;
    clearTimeout(minuteurInfobulleVaisseau);
    const panneau = document.getElementById("info-carte-vaisseau");
    panneau.innerHTML = `
        <div class="info-carte-nom">${etat.nom}</div>
        <div class="info-carte-effet">${etat.description}</div>`;
    minuteurInfobulleVaisseau = setTimeout(() => {
        panneau.innerHTML = "";
    }, DUREE_INFOBULLE_MODULE_MS);
}

function fermerSurvolVaisseau() {
    clearTimeout(minuteurInfobulleVaisseau);
    document.getElementById("info-carte-vaisseau").innerHTML = "";
    document.getElementById("ecran-vaisseau").classList.add("cachee");
}

function nouvellePartie() {
    allerA(appelerBridge("nouvelle_partie_web"));
}

document.getElementById("tour-suivant").addEventListener("click", finirTour);
document.getElementById("bouton-quitter-combat").addEventListener("click", quitterCombat);
document.getElementById("bouton-creer-joueur").addEventListener("click", creerNouveauJoueur);
document.getElementById("nom-nouveau-joueur").addEventListener("keydown", (evenement) => {
    if (evenement.key === "Enter") creerNouveauJoueur();
});
document.getElementById("bouton-continuer").addEventListener("click", continuerPartie);
document.getElementById("bouton-abandonner").addEventListener("click", abandonnerPartie);
document.getElementById("bouton-voir-deck-partie").addEventListener("click", voirDeckPartie);
document.getElementById("bouton-nouvelle-partie").addEventListener("click", nouvellePartie);
document.getElementById("bouton-continuer-fin-combat").addEventListener("click", continuerApresFinCombat);
document.getElementById("bouton-passer-fin-combat").addEventListener("click", passerFinCombat);
document.getElementById("bouton-passer-carte-module").addEventListener("click", passerCarteModule);
document.getElementById("bouton-termine-station-service").addEventListener("click", terminerStationServicePartie);
document.getElementById("bouton-continuer-aventure-trois-lunes").addEventListener("click", terminerAventureTroisLunes);
document.getElementById("bouton-continuer-aventure-asteroides").addEventListener("click", cliquerContinuerAsteroides);
document.getElementById("bouton-prendre-aventure-asteroides").addEventListener("click", prendreCarteAsteroides);
document.getElementById("bouton-passer-aventure-asteroides").addEventListener("click", passerCarteAsteroides);
document.getElementById("bouton-continuer-aventure-police").addEventListener("click", terminerAventurePolice);
document.getElementById("bouton-continuer-victoire-finale").addEventListener("click", terminerVictoireFinale);
document.getElementById("bouton-termine-etape-placeholder").addEventListener("click", terminerEtapePlaceholder);
document.getElementById("bouton-retour-deck").addEventListener("click", retourDepuisDeck);
document.getElementById("bouton-deck-barre-laterale").addEventListener("click", ouvrirSurvolDeck);
document.getElementById("bouton-vaisseau-barre-laterale").addEventListener("click", ouvrirSurvolVaisseau);
document.getElementById("bouton-retour-vaisseau").addEventListener("click", fermerSurvolVaisseau);
document.getElementById("bouton-journal-combat").addEventListener("click", ouvrirJournalCombat);
document.getElementById("bouton-retour-journal-combat").addEventListener("click", fermerJournalCombat);
demarrer();
