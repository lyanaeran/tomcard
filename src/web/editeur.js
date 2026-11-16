// Outil d'administration : editeur de cartes (specs/outil-editeur-cartes.md). TEMPORAIRE.
// Ecran 1 : liste des cartes ; ecran 2 : detail modifiable d'une carte. Aucune regle de jeu ici :
// les listes de choix, la validation, l'apercu de la description et la mise en forme du fichier
// exporte viennent de src/web/bridge.py (code Python du jeu). Ce fichier ne fait qu'afficher,
// garder les modifications dans le localStorage et comparer aux cartes du jeu (config/cartes.json).
// Charge apres app.js (utilise appelerBridge, masquerTousLesEcrans, joueurCourant...).

const CLE_EDITEUR = "space_fight_editeur_cartes";

// Etat de l'outil (recharge a chaque ouverture de l'ecran 1)
let editeurReference = null; // { cartes: [...], listes: {...} } (bridge.editeur_reference_web)
let editeurLocal = { cartes: {}, nouvelles: [] }; // modifications de l'appareil (cf. lireEditeurLocal)
let editeurTri = { colonne: null, inverse: false };
let editeurFiltre = "toutes";
let editeurIdOuvert = null; // id de la carte ouverte dans l'ecran 2
let editeurValidations = {}; // id -> { erreurs, apercu }
let editeurRetour = null; // fonction appelee par "Jeu" (retour a l'ecran d'origine)

// --- Stockage local (seulement les differences avec le jeu) ---

// editeurLocal.cartes[id] = { carte: entree complete, base: entree du jeu au moment de la premiere
// modification (null pour une nouvelle carte) } ; editeurLocal.nouvelles : ordre de creation.
function lireEditeurLocal() {
    try {
        const brut = JSON.parse(localStorage.getItem(CLE_EDITEUR) || "null");
        if (brut && typeof brut.cartes === "object" && Array.isArray(brut.nouvelles)) return brut;
    } catch (erreur) {
        console.error("Editeur : stockage local illisible, ignore", erreur);
    }
    return { cartes: {}, nouvelles: [] };
}

function ecrireEditeurLocal() {
    try {
        localStorage.setItem(CLE_EDITEUR, JSON.stringify(editeurLocal));
    } catch (erreur) {
        console.error("Editeur : sauvegarde locale impossible", erreur);
    }
}

// JSON a cles triees : deux cartes egales au contenu pres, quel que soit l'ordre des cles
function texteCanonique(valeur) {
    if (Array.isArray(valeur)) return `[${valeur.map(texteCanonique).join(",")}]`;
    if (valeur && typeof valeur === "object") {
        return `{${Object.keys(valeur).sort().map((cle) => `${JSON.stringify(cle)}:${texteCanonique(valeur[cle])}`).join(",")}}`;
    }
    return JSON.stringify(valeur);
}

function memeContenu(a, b) {
    return texteCanonique(a) === texteCanonique(b);
}

function copieProfonde(valeur) {
    return JSON.parse(JSON.stringify(valeur));
}

function carteDuJeu(id) {
    return editeurReference.cartes.find((carte) => carte.id === id) || null;
}

// Toutes les cartes telles que vues par l'outil : celles du jeu (modifiees ou non), puis les
// nouvelles, dans l'ordre de creation
function cartesEffectives() {
    const cartes = editeurReference.cartes.map((carte) => (editeurLocal.cartes[carte.id] ? editeurLocal.cartes[carte.id].carte : carte));
    editeurLocal.nouvelles.forEach((id) => {
        if (editeurLocal.cartes[id]) cartes.push(editeurLocal.cartes[id].carte);
    });
    return cartes;
}

function carteEffective(id) {
    return editeurLocal.cartes[id] ? editeurLocal.cartes[id].carte : carteDuJeu(id);
}

// Enregistre la carte modifiee ; une carte du jeu revenue a l'identique n'est plus gardee
function enregistrerCarte(id, carte) {
    const duJeu = carteDuJeu(id);
    if (duJeu && memeContenu(carte, duJeu)) {
        delete editeurLocal.cartes[id];
    } else {
        const base = editeurLocal.cartes[id] ? editeurLocal.cartes[id].base : duJeu ? copieProfonde(duJeu) : null;
        editeurLocal.cartes[id] = { carte, base };
    }
    ecrireEditeurLocal();
}

// --- Etat d'une carte (pastilles, specs/outil-editeur-cartes.md 5) ---

function etatCarte(id) {
    const local = editeurLocal.cartes[id];
    const duJeu = carteDuJeu(id);
    const validation = editeurValidations[id];
    return {
        erreur: Boolean(validation && validation.erreurs.length),
        nouvelle: !duJeu,
        modifiee: Boolean(local && duJeu),
        jeuChange: Boolean(local && local.base && duJeu && !memeContenu(local.base, duJeu)),
        supprimee: (carteEffective(id) || {}).jouable === "supprimee",
    };
}

function pastilleEtat(etat) {
    if (etat.erreur) return '<span class="pastille-editeur pastille-erreur" title="En erreur">⚠</span>';
    if (etat.jeuChange) return '<span class="pastille-editeur pastille-jeu-change" title="Le jeu a changé">⇄</span>';
    if (etat.nouvelle) return '<span class="pastille-editeur pastille-nouvelle" title="Nouvelle">✚</span>';
    if (etat.modifiee) return '<span class="pastille-editeur pastille-modifiee" title="Modifiée">●</span>';
    return "";
}

function validerToutes() {
    const cartes = cartesEffectives();
    const resultats = appelerBridge("editeur_valider_web", JSON.stringify(cartes));
    editeurValidations = {};
    cartes.forEach((carte, index) => {
        const id = carte.id;
        if (!editeurValidations[id]) editeurValidations[id] = resultats[index];
    });
}

// --- Ouverture / fermeture ---

function ouvrirEditeur(retour) {
    editeurRetour = retour;
    editeurReference = appelerBridge("editeur_reference_web");
    editeurLocal = lireEditeurLocal();
    afficherListeEditeur();
}

function quitterEditeur() {
    if (editeurRetour) editeurRetour();
    else afficherSelectionJoueur();
}

// --- Ecran 1 : liste ---

function libelleModules(carte) {
    const noms = {};
    editeurReference.listes.modules.forEach((module) => {
        noms[module.valeur] = module.libelle;
    });
    const modules = Array.isArray(carte.modules) ? carte.modules : [];
    return modules.map((id) => noms[id] || id).join(", ") || "—";
}

function libelleMunitions(carte) {
    return carte.munition === null || carte.munition === undefined || carte.munition === "" ? "∞" : String(carte.munition);
}

// Description avec les valeurs remplacees (apercu calcule par le jeu) ; texte brut si la carte est
// en erreur et qu'aucun apercu n'est possible
function libelleDescription(carte) {
    const validation = editeurValidations[carte.id];
    return validation && validation.apercu !== null ? validation.apercu : String(carte.description || "");
}

// Colonnes de l'ecran 1 (decision utilisateur, 2026-11-15)
const COLONNES_EDITEUR = [
    { cle: "etat", titre: "", valeur: (carte) => rangEtat(etatCarte(carte.id)) },
    { cle: "nom", titre: "Nom", valeur: (carte) => String(carte.nom || "") },
    { cle: "cout", titre: "Coût", valeur: (carte) => Number(carte.cout) },
    { cle: "rarete", titre: "Rareté", valeur: (carte) => String(carte.rarete || "") },
    { cle: "categorie", titre: "Catégorie", valeur: (carte) => String(carte.categorie || "") },
    { cle: "module", titre: "Module", valeur: (carte) => libelleModules(carte) },
    { cle: "munitions", titre: "Munitions", valeur: (carte) => (libelleMunitions(carte) === "∞" ? Infinity : Number(carte.munition)) },
    { cle: "description", titre: "Description", valeur: (carte) => libelleDescription(carte) },
];

function rangEtat(etat) {
    if (etat.erreur) return 0;
    if (etat.jeuChange) return 1;
    if (etat.nouvelle) return 2;
    if (etat.modifiee) return 3;
    return 4;
}

function carteFiltree(carte) {
    const etat = etatCarte(carte.id);
    if (editeurFiltre === "toutes") return true;
    if (editeurFiltre === "modifiees") return etat.erreur || etat.nouvelle || etat.modifiee || etat.jeuChange;
    if (editeurFiltre === "supprimees") return etat.supprimee;
    return Array.isArray(carte.modules) && carte.modules.includes(editeurFiltre);
}

function afficherListeEditeur() {
    validerToutes();
    const toutes = cartesEffectives();
    let cartes = toutes.filter(carteFiltree);
    if (editeurTri.colonne) {
        const colonne = COLONNES_EDITEUR.find((c) => c.cle === editeurTri.colonne);
        cartes = cartes
            .map((carte, index) => ({ carte, index }))
            .sort((a, b) => {
                const va = colonne.valeur(a.carte);
                const vb = colonne.valeur(b.carte);
                const ordre = typeof va === "number" && typeof vb === "number" ? (va === vb ? 0 : va < vb ? -1 : 1) : String(va).localeCompare(String(vb), "fr");
                return (editeurTri.inverse ? -ordre : ordre) || a.index - b.index;
            })
            .map((element) => element.carte);
    }

    const etats = toutes.map((carte) => etatCarte(carte.id));
    const modifiees = etats.filter((etat) => etat.modifiee).length;
    const nouvelles = etats.filter((etat) => etat.nouvelle).length;
    const erreurs = etats.filter((etat) => etat.erreur).length;
    document.getElementById("compteur-editeur").textContent =
        `${toutes.length} cartes · ${modifiees} modifiée${modifiees > 1 ? "s" : ""} · ${nouvelles} nouvelle${nouvelles > 1 ? "s" : ""}` +
        (erreurs ? ` · ${erreurs} en erreur` : "");

    const filtre = document.getElementById("filtre-editeur");
    filtre.innerHTML = [
        ["toutes", "Toutes"],
        ["modifiees", "Modifiées"],
        ...editeurReference.listes.modules.map((module) => [module.valeur, module.libelle]),
        ["supprimees", "Supprimées"],
    ]
        .map(([valeur, libelle]) => `<option value="${echapper(valeur)}"${valeur === editeurFiltre ? " selected" : ""}>${echapper(libelle)}</option>`)
        .join("");

    const boutonCopier = document.getElementById("bouton-copier-editeur");
    boutonCopier.disabled = erreurs > 0;
    boutonCopier.title = erreurs > 0 ? "Corrige les cartes en erreur avant de copier" : "";

    const entete = COLONNES_EDITEUR.map((colonne) => {
        const fleche = editeurTri.colonne === colonne.cle ? (editeurTri.inverse ? " ▲" : " ▼") : "";
        return `<th class="col-${colonne.cle}" data-colonne="${colonne.cle}">${colonne.titre}${fleche}</th>`;
    }).join("");
    const lignes = cartes
        .map((carte) => {
            const etat = etatCarte(carte.id);
            return `
            <tr data-id="${echapper(carte.id)}" class="${etat.supprimee ? "ligne-supprimee" : ""}">
                <td class="col-etat">${pastilleEtat(etat)}</td>
                <td class="col-nom">${echapper(carte.nom)}</td>
                <td class="col-cout">${echapper(carte.cout)}</td>
                <td class="col-rarete">${echapper(carte.rarete)}</td>
                <td class="col-categorie">${echapper(carte.categorie)}</td>
                <td class="col-module">${echapper(libelleModules(carte))}</td>
                <td class="col-munitions">${echapper(libelleMunitions(carte))}</td>
                <td class="col-description"><div class="texte-description">${echapper(libelleDescription(carte))}</div></td>
            </tr>`;
        })
        .join("");
    document.getElementById("tableau-editeur").innerHTML = `<thead><tr>${entete}</tr></thead><tbody>${lignes}</tbody>`;
    document.querySelectorAll("#tableau-editeur th").forEach((th) => {
        th.addEventListener("click", () => trierEditeur(th.dataset.colonne));
    });
    document.querySelectorAll("#tableau-editeur tbody tr").forEach((tr) => {
        tr.addEventListener("click", () => ouvrirCarteEditeur(tr.dataset.id));
    });

    masquerTousLesEcrans();
    document.getElementById("ecran-editeur-liste").classList.remove("cachee");
}

function trierEditeur(colonne) {
    if (editeurTri.colonne === colonne) editeurTri.inverse = !editeurTri.inverse;
    else editeurTri = { colonne, inverse: false };
    const conteneur = document.getElementById("conteneur-tableau-editeur");
    const defilement = conteneur.scrollTop;
    afficherListeEditeur();
    conteneur.scrollTop = defilement;
}

function changerFiltreEditeur() {
    editeurFiltre = document.getElementById("filtre-editeur").value;
    afficherListeEditeur();
}

// --- Nouvelle carte (bouton +) ---

function prochainIdLibre() {
    const ids = new Set(cartesEffectives().map((carte) => carte.id));
    let numero = 1;
    cartesEffectives().forEach((carte) => {
        const correspondance = /^CRT_(\d+)$/.exec(String(carte.id));
        if (correspondance) numero = Math.max(numero, Number(correspondance[1]) + 1);
    });
    while (ids.has(`CRT_${numero}`)) numero += 1;
    return `CRT_${numero}`;
}

function nouvelleCarteEditeur() {
    const id = prochainIdLibre();
    const carte = {
        id,
        nom: "Nouvelle carte",
        image: "assets/cartes/attaque.png",
        rarete: "Commune",
        categorie: "Attaque",
        cible: "Ennemi Unique",
        modules: [],
        cout: 1,
        munition: null,
        lancements: 1,
        persistante: false,
        jouable: "oui",
        refonte: true,
        description: "Inflige {degats} dégâts à un ennemi unique",
        valeurs: { degats: 0 },
        // Effets non saisis dans l'outil : ecrits par l'agent d'apres la description
        effets: [],
    };
    editeurLocal.nouvelles.push(id);
    enregistrerCarte(id, carte);
    ouvrirCarteEditeur(id);
}

// --- Copie du fichier (specs/outil-editeur-cartes.md 6.2) ---

// Seules les cartes modifiees ou ajoutees sont copiees (decision utilisateur, 2026-11-16) : les
// autres sont deja dans le jeu, l'agent les fusionne par id a l'integration.
function cartesACopier() {
    return cartesEffectives().filter((carte) => {
        const etat = etatCarte(carte.id);
        return etat.modifiee || etat.nouvelle;
    });
}

function copierFichierEditeur() {
    validerToutes();
    if (cartesEffectives().some((carte) => editeurValidations[carte.id].erreurs.length)) {
        afficherMessageEditeur("Des cartes sont en erreur : corrige-les avant de copier.", true);
        return;
    }
    const aCopier = cartesACopier();
    if (aCopier.length === 0) {
        afficherMessageEditeur("Aucune carte modifiée ou ajoutée : rien à copier.", true);
        return;
    }
    const texte = appelerBridge("editeur_exporter_web", JSON.stringify(aCopier));
    const etats = aCopier.map((carte) => etatCarte(carte.id));
    const aRevoir = aCopier.filter((carte) => editeurValidations[carte.id].effets_a_revoir).length;
    const resume = `${etats.filter((e) => e.modifiee).length} modifiée(s), ${etats.filter((e) => e.nouvelle).length} nouvelle(s)` +
        (aRevoir ? `, ${aRevoir} dont les effets seront écrits par l'agent` : "");
    const enSecours = () => {
        // Presse-papiers indisponible (page non securisee, ex. http://adresse-locale) : on montre le
        // texte selectionne, a copier a la main
        const zone = document.getElementById("zone-copie-editeur");
        zone.value = texte;
        document.getElementById("secours-copie-editeur").classList.remove("cachee");
        zone.focus();
        zone.select();
        afficherMessageEditeur("Copie automatique impossible : sélectionne le texte et copie-le.", true);
    };
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(texte).then(
            () => afficherMessageEditeur(`Cartes copiées : ${resume}.`, false),
            enSecours,
        );
    } else {
        enSecours();
    }
}

function fermerSecoursCopieEditeur() {
    document.getElementById("secours-copie-editeur").classList.add("cachee");
}

let minuteurMessageEditeur = null;
function afficherMessageEditeur(texte, erreur) {
    const message = document.getElementById("message-editeur");
    message.textContent = texte;
    message.classList.toggle("message-editeur-erreur", erreur);
    message.classList.remove("cachee");
    clearTimeout(minuteurMessageEditeur);
    minuteurMessageEditeur = setTimeout(() => message.classList.add("cachee"), 4000);
}

// --- Ecran 2 : detail d'une carte ---

function ouvrirCarteEditeur(id) {
    editeurIdOuvert = id;
    afficherCarteEditeur();
    document.getElementById("ecran-editeur-carte").scrollTop = 0;
}

function fermerCarteEditeur() {
    const id = editeurIdOuvert;
    editeurIdOuvert = null;
    const conteneur = document.getElementById("conteneur-tableau-editeur");
    const defilement = conteneur.scrollTop;
    afficherListeEditeur();
    conteneur.scrollTop = defilement;
    const ligne = document.querySelector(`#tableau-editeur tr[data-id="${CSS.escape(id)}"]`);
    if (ligne) ligne.classList.add("ligne-recente");
}

// Carte ouverte, modifiable (copie : la reference du jeu n'est jamais modifiee)
function carteOuverte() {
    return copieProfonde(carteEffective(editeurIdOuvert));
}

// Applique une modification a la carte ouverte, l'enregistre et redessine l'ecran 2
function modifierCarteOuverte(modification) {
    const carte = carteOuverte();
    modification(carte);
    enregistrerCarte(editeurIdOuvert, carte);
    const ecran = document.getElementById("ecran-editeur-carte");
    const defilement = ecran.scrollTop;
    afficherCarteEditeur();
    ecran.scrollTop = defilement;
}

function lireChemin(objet, chemin) {
    return chemin.reduce((courant, cle) => (courant === undefined || courant === null ? undefined : courant[cle]), objet);
}

function ecrireChemin(objet, chemin, valeur) {
    let courant = objet;
    chemin.slice(0, -1).forEach((cle) => {
        if (courant[cle] === undefined || courant[cle] === null) courant[cle] = {};
        courant = courant[cle];
    });
    const derniere = chemin[chemin.length - 1];
    if (valeur === undefined) delete courant[derniere];
    else courant[derniere] = valeur;
}

// Nombre si le texte en est un, sinon le texte tel quel (la validation le signalera)
function nombreOuTexte(texte) {
    const nettoye = String(texte).trim();
    return nettoye !== "" && !Number.isNaN(Number(nettoye)) ? Number(nettoye) : nettoye;
}

function echapper(valeur) {
    return String(valeur === undefined || valeur === null ? "" : valeur)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// Rappel de la valeur du jeu pour un champ modifie (specs/outil-editeur-cartes.md 4.4)
function rappelJeu(chemin, valeurLocale) {
    const duJeu = carteDuJeu(editeurIdOuvert);
    if (!duJeu) return "";
    const valeurJeu = lireChemin(duJeu, chemin);
    if (memeContenu(valeurJeu === undefined ? null : valeurJeu, valeurLocale === undefined ? null : valeurLocale)) return "";
    const texte = valeurJeu === undefined || valeurJeu === null ? "vide" : typeof valeurJeu === "object" ? JSON.stringify(valeurJeu) : valeurJeu;
    return `<div class="rappel-jeu">jeu : ${echapper(texte)} <button class="bouton-remettre" data-chemin="${echapper(JSON.stringify(chemin))}" title="Remettre la valeur du jeu">↺</button></div>`;
}

function classeModifie(chemin, valeurLocale) {
    const duJeu = carteDuJeu(editeurIdOuvert);
    if (!duJeu) return "";
    const valeurJeu = lireChemin(duJeu, chemin);
    return memeContenu(valeurJeu === undefined ? null : valeurJeu, valeurLocale === undefined ? null : valeurLocale) ? "" : " champ-modifie";
}

// Champ texte ou nombre. `chemin` : liste de cles depuis la carte (ex. ["valeurs", "degats"]).
function champTexte(libelle, chemin, { nombre = false, vide = undefined, lectureSeule = false, multiligne = false } = {}) {
    const carte = carteOuverte();
    const valeur = lireChemin(carte, chemin);
    const attributs = `data-chemin="${echapper(JSON.stringify(chemin))}" data-nombre="${nombre}" data-vide="${echapper(JSON.stringify(vide === undefined ? null : vide))}"${lectureSeule ? " readonly" : ""}`;
    const saisie = multiligne
        ? `<textarea class="saisie-editeur" ${attributs} rows="3">${echapper(valeur)}</textarea>`
        : `<input class="saisie-editeur" ${attributs} type="text" inputmode="${nombre ? "decimal" : "text"}" value="${echapper(valeur)}">`;
    return `<label class="champ-editeur${classeModifie(chemin, valeur)}"><span>${libelle}</span>${saisie}${rappelJeu(chemin, valeur)}</label>`;
}

// Liste deroulante avec "Autre..." pour une valeur libre (specs/outil-editeur-cartes.md 4.3).
// `choix` : [{ valeur, libelle }] ; `aucun` : libelle d'un choix vide (cle retiree), sinon pas de
// choix vide.
function champListe(libelle, chemin, choix, { aucun = null, autre = true } = {}) {
    const carte = carteOuverte();
    const valeur = lireChemin(carte, chemin);
    const connue = (valeur === undefined && aucun !== null) || choix.some((element) => element.valeur === valeur);
    const options = [];
    if (aucun !== null) options.push(`<option value="__aucun__"${valeur === undefined ? " selected" : ""}>${echapper(aucun)}</option>`);
    choix.forEach((element) => {
        options.push(`<option value="${echapper(element.valeur)}"${element.valeur === valeur ? " selected" : ""}>${echapper(element.libelle)}</option>`);
    });
    if (autre) options.push(`<option value="__autre__"${connue ? "" : " selected"}>Autre…</option>`);
    const libre = autre && !connue
        ? `<input class="saisie-editeur saisie-libre" type="text" data-chemin="${echapper(JSON.stringify(chemin))}" data-nombre="false" data-vide="null" value="${echapper(valeur)}" placeholder="Valeur libre">`
        : "";
    return `<label class="champ-editeur${classeModifie(chemin, valeur)}"><span>${libelle}</span>
        <select class="liste-editeur" data-chemin="${echapper(JSON.stringify(chemin))}">${options.join("")}</select>${libre}${rappelJeu(chemin, valeur)}</label>`;
}

function champCoche(libelle, chemin) {
    const valeur = Boolean(lireChemin(carteOuverte(), chemin));
    return `<label class="champ-editeur champ-coche${classeModifie(chemin, lireChemin(carteOuverte(), chemin))}">
        <input type="checkbox" class="coche-editeur" data-chemin="${echapper(JSON.stringify(chemin))}"${valeur ? " checked" : ""}>
        <span>${libelle}</span>${rappelJeu(chemin, lireChemin(carteOuverte(), chemin))}</label>`;
}

function blocModules(carte) {
    const modules = Array.isArray(carte.modules) ? carte.modules : [];
    const cases = editeurReference.listes.modules
        .map((module) => `<label class="champ-coche"><input type="checkbox" class="coche-module" value="${echapper(module.valeur)}"${modules.includes(module.valeur) ? " checked" : ""}><span>${echapper(module.libelle)}</span></label>`)
        .join("");
    const inconnus = modules.filter((id) => !editeurReference.listes.modules.some((module) => module.valeur === id));
    const avertissement = modules.length === 0 ? '<div class="note-editeur">Aucun module : la carte n\'est proposée nulle part en jeu.</div>' : "";
    return `<div class="champ-editeur${classeModifie(["modules"], carte.modules)}"><span>Modules</span><div class="groupe-coches">${cases}${inconnus.map((id) => `<span class="note-editeur">${echapper(id)} (inconnu)</span>`).join("")}</div>${avertissement}${rappelJeu(["modules"], carte.modules)}</div>`;
}

function blocValeurs(carte) {
    const valeurs = carte.valeurs && typeof carte.valeurs === "object" ? carte.valeurs : {};
    const lignes = Object.entries(valeurs)
        .map(([nom, valeur]) => `
        <div class="ligne-valeur">
            <input class="saisie-nom-valeur" type="text" data-ancien="${echapper(nom)}" value="${echapper(nom)}" aria-label="Nom de la valeur">
            <input class="saisie-editeur" type="text" inputmode="decimal" data-chemin="${echapper(JSON.stringify(["valeurs", nom]))}" data-nombre="true" data-vide="null" value="${echapper(valeur)}" aria-label="Valeur">
            <button class="bouton-supprimer-valeur" data-nom="${echapper(nom)}" title="Supprimer cette valeur">✕</button>
        </div>`)
        .join("");
    return `<div class="champ-editeur${classeModifie(["valeurs"], carte.valeurs)}"><span>Valeurs nommées</span>${lignes}
        <button id="bouton-ajouter-valeur" class="bouton-petit">+ valeur</button>${rappelJeu(["valeurs"], carte.valeurs)}</div>`;
}

function afficherCarteEditeur() {
    const carte = carteOuverte();
    const id = editeurIdOuvert;
    validerToutes();
    const etat = etatCarte(id);
    const validation = editeurValidations[id] || { erreurs: [], apercu: null };
    const listes = editeurReference.listes;
    const duJeu = carteDuJeu(id);
    const local = editeurLocal.cartes[id];

    document.getElementById("titre-editeur-carte").innerHTML = `${echapper(carte.nom)} <span class="id-editeur">(${echapper(id)})</span> ${pastilleEtat(etat)}`;
    document.getElementById("bouton-annuler-editeur").textContent = duJeu ? "Annuler mes modifications" : "Supprimer cette nouvelle carte";
    document.getElementById("bouton-annuler-editeur").disabled = Boolean(duJeu) && !local;

    const conflit = etat.jeuChange
        ? `<div class="conflit-editeur">⇄ La carte a changé dans le jeu depuis ta modification.
            <div>Version du jeu : <code>${echapper(JSON.stringify(duJeu))}</code></div>
            <button id="bouton-garder-mienne">Garder la mienne</button> <button id="bouton-reprendre-jeu">Reprendre celle du jeu</button></div>`
        : "";
    const erreurs = validation.erreurs.length
        ? `<ul class="erreurs-editeur">${validation.erreurs.map((erreur) => `<li>⚠ ${echapper(erreur)}</li>`).join("")}</ul>`
        : "";
    const apercu = validation.apercu !== null ? `<div class="apercu-editeur">Aperçu : « ${echapper(validation.apercu)} »</div>` : "";
    // Les effets ne se saisissent pas ici (decision utilisateur) : ils se deduisent de la description
    const descriptionChangee = duJeu && carte.description !== duJeu.description;
    const noteEffets = validation.effets_a_revoir || descriptionChangee || !duJeu
        ? '<div class="note-effets-editeur">Effets de la carte : ils ne se saisissent pas ici. Ils seront écrits d\'après la description quand le fichier sera intégré au jeu.</div>'
        : "";
    const image = carte.image ? `<img class="vignette-editeur" src="${echapper(carte.image)}" alt="">` : "";

    document.getElementById("contenu-editeur-carte").innerHTML = `
        ${conflit}${erreurs}${apercu}${noteEffets}
        <fieldset><legend>Identité</legend>
            ${champTexte("Id", ["id"], { lectureSeule: Boolean(duJeu) })}
            ${champTexte("Nom", ["nom"])}
            <div class="ligne-image">${champListe("Image", ["image"], listes.images)}${image}</div>
        </fieldset>
        <fieldset><legend>Classement</legend>
            ${champListe("Rareté", ["rarete"], listes.rarete)}
            ${champListe("Catégorie", ["categorie"], listes.categorie)}
            ${champListe("Cible", ["cible"], listes.cible)}
            ${blocModules(carte)}
        </fieldset>
        <fieldset><legend>Coût et usage</legend>
            ${champTexte("Coût", ["cout"], { nombre: true })}
            ${champTexte("Munitions (vide = illimitées)", ["munition"], { nombre: true, vide: null })}
            ${champTexte("Lancements", ["lancements"], { nombre: true })}
            ${champListe("Jouable", ["jouable"], listes.jouable, { autre: false })}
            ${champCoche("Persistante", ["persistante"])}
            ${champCoche("Revue (refonte)", ["refonte"])}
        </fieldset>
        <fieldset><legend>Texte</legend>
            ${champTexte("Description (valeurs entre accolades : {degats})", ["description"], { multiligne: true })}
        </fieldset>
        <fieldset><legend>Valeurs</legend>${blocValeurs(carte)}</fieldset>`;

    brancherCarteEditeur();
    masquerTousLesEcrans();
    document.getElementById("ecran-editeur-carte").classList.remove("cachee");
}

function brancherCarteEditeur() {
    const contenu = document.getElementById("contenu-editeur-carte");

    // Champs texte / nombre : enregistres a la sortie du champ ("change"), pas a chaque lettre
    contenu.querySelectorAll(".saisie-editeur").forEach((saisie) => {
        if (saisie.readOnly) return;
        saisie.addEventListener("change", () => {
            const chemin = JSON.parse(saisie.dataset.chemin);
            const vide = JSON.parse(saisie.dataset.vide);
            const brut = saisie.value;
            let valeur = saisie.dataset.nombre === "true" ? nombreOuTexte(brut) : brut;
            if (String(brut).trim() === "" && saisie.dataset.nombre === "true") valeur = vide;
            if (chemin.length === 1 && chemin[0] === "id") {
                renommerCarteOuverte(String(brut).trim());
                return;
            }
            modifierCarteOuverte((carte) => ecrireChemin(carte, chemin, valeur));
        });
    });

    contenu.querySelectorAll(".liste-editeur").forEach((liste) => {
        liste.addEventListener("change", () => {
            const chemin = JSON.parse(liste.dataset.chemin);
            modifierCarteOuverte((carte) => {
                if (liste.value === "__aucun__") ecrireChemin(carte, chemin, undefined);
                else if (liste.value === "__autre__") ecrireChemin(carte, chemin, "");
                else ecrireChemin(carte, chemin, liste.value);
            });
        });
    });

    contenu.querySelectorAll(".coche-editeur").forEach((coche) => {
        coche.addEventListener("change", () => {
            const chemin = JSON.parse(coche.dataset.chemin);
            modifierCarteOuverte((carte) => ecrireChemin(carte, chemin, coche.checked));
        });
    });

    contenu.querySelectorAll(".coche-module").forEach((coche) => {
        coche.addEventListener("change", () => {
            modifierCarteOuverte((carte) => {
                const modules = new Set(Array.isArray(carte.modules) ? carte.modules : []);
                if (coche.checked) modules.add(coche.value);
                else modules.delete(coche.value);
                // Ordre des modules de config/modules.json
                const ordre = editeurReference.listes.modules.map((module) => module.valeur);
                carte.modules = [...modules].sort((a, b) => ordre.indexOf(a) - ordre.indexOf(b));
            });
        });
    });

    contenu.querySelectorAll(".saisie-nom-valeur").forEach((saisie) => {
        saisie.addEventListener("change", () => {
            const ancien = saisie.dataset.ancien;
            const nouveau = saisie.value.trim();
            if (!nouveau || nouveau === ancien) return;
            modifierCarteOuverte((carte) => {
                // Renomme en gardant l'ordre des valeurs ; les effets qui citaient l'ancien nom suivent
                carte.valeurs = Object.fromEntries(Object.entries(carte.valeurs || {}).map(([nom, valeur]) => [nom === ancien ? nouveau : nom, valeur]));
                (carte.effets || []).forEach((effet) => {
                    if (effet.valeur === ancien) effet.valeur = nouveau;
                    if (effet.duree === ancien) effet.duree = nouveau;
                });
            });
        });
    });

    contenu.querySelectorAll(".bouton-supprimer-valeur").forEach((bouton) => {
        bouton.addEventListener("click", (evenement) => {
            evenement.preventDefault();
            modifierCarteOuverte((carte) => {
                delete carte.valeurs[bouton.dataset.nom];
            });
        });
    });

    const ajouterValeur = document.getElementById("bouton-ajouter-valeur");
    ajouterValeur.addEventListener("click", (evenement) => {
        evenement.preventDefault();
        modifierCarteOuverte((carte) => {
            carte.valeurs = carte.valeurs && typeof carte.valeurs === "object" ? carte.valeurs : {};
            let numero = 1;
            while (carte.valeurs[`valeur_${numero}`] !== undefined) numero += 1;
            carte.valeurs[`valeur_${numero}`] = 0;
        });
    });

    contenu.querySelectorAll(".bouton-remettre").forEach((bouton) => {
        bouton.addEventListener("click", (evenement) => {
            evenement.preventDefault();
            const chemin = JSON.parse(bouton.dataset.chemin);
            const valeurJeu = lireChemin(carteDuJeu(editeurIdOuvert), chemin);
            modifierCarteOuverte((carte) => ecrireChemin(carte, chemin, valeurJeu === undefined ? undefined : copieProfonde(valeurJeu)));
        });
    });

    const garder = document.getElementById("bouton-garder-mienne");
    if (garder) {
        garder.addEventListener("click", () => {
            editeurLocal.cartes[editeurIdOuvert].base = copieProfonde(carteDuJeu(editeurIdOuvert));
            ecrireEditeurLocal();
            afficherCarteEditeur();
        });
    }
    const reprendre = document.getElementById("bouton-reprendre-jeu");
    if (reprendre) {
        reprendre.addEventListener("click", () => {
            delete editeurLocal.cartes[editeurIdOuvert];
            ecrireEditeurLocal();
            afficherCarteEditeur();
        });
    }
}

// Nouvelle carte : son id est modifiable ; renommer deplace sa sauvegarde locale
function renommerCarteOuverte(nouvelId) {
    const ancien = editeurIdOuvert;
    if (!nouvelId || nouvelId === ancien) {
        afficherCarteEditeur();
        return;
    }
    if (carteEffective(nouvelId)) {
        afficherMessageEditeur(`L'id ${nouvelId} existe déjà.`, true);
        afficherCarteEditeur();
        return;
    }
    const carte = carteOuverte();
    carte.id = nouvelId;
    delete editeurLocal.cartes[ancien];
    editeurLocal.nouvelles = editeurLocal.nouvelles.map((id) => (id === ancien ? nouvelId : id));
    editeurIdOuvert = nouvelId;
    enregistrerCarte(nouvelId, carte);
    afficherCarteEditeur();
}

function annulerCarteEditeur() {
    const id = editeurIdOuvert;
    const duJeu = carteDuJeu(id);
    const question = duJeu ? "Annuler toutes tes modifications de cette carte ?" : "Supprimer cette nouvelle carte ?";
    if (!window.confirm(question)) return;
    delete editeurLocal.cartes[id];
    editeurLocal.nouvelles = editeurLocal.nouvelles.filter((element) => element !== id);
    ecrireEditeurLocal();
    if (duJeu) afficherCarteEditeur();
    else fermerCarteEditeur();
}

document.getElementById("bouton-retour-editeur").addEventListener("click", quitterEditeur);
document.getElementById("filtre-editeur").addEventListener("change", changerFiltreEditeur);
document.getElementById("bouton-nouvelle-carte-editeur").addEventListener("click", nouvelleCarteEditeur);
document.getElementById("bouton-copier-editeur").addEventListener("click", copierFichierEditeur);
document.getElementById("bouton-fermer-secours-editeur").addEventListener("click", fermerSecoursCopieEditeur);
document.getElementById("bouton-fermer-carte-editeur").addEventListener("click", fermerCarteEditeur);
document.getElementById("bouton-annuler-editeur").addEventListener("click", annulerCarteEditeur);
