// Essais de l'outil d'administration (editeur de cartes, specs/outil-editeur-cartes.md) dans un
// vrai navigateur (Chromium + Pyodide), au format iPhone 17 en paysage (874 x 402) : liste, detail,
// modification, sauvegarde locale apres rechargement, nouvelle carte, erreur qui bloque la copie,
// suppression, filtre, tri, copie du fichier, bouton Admin reserve a certains joueurs.
//
//     python -m http.server 8765        (a la racine du depot, dans un autre terminal)
//     node outils/test_web/essais_editeur.js [dossier des captures] [adresse]
//
// Demande Node et Playwright avec son Chromium (cf. essais.js). Sort en erreur au premier
// controle faux.

const os = require("os");
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");
const captures = process.argv[2] || fs.mkdtempSync(path.join(os.tmpdir(), "space_fight_editeur_"));
const URL = process.argv[3] || "http://localhost:8765/index.html";
function verifier(condition, message) {
    if (!condition) throw new Error("ECHEC : " + message);
    console.log("ok -", message);
}
(async () => {
    const navigateur = await chromium.launch();
    const contexte = await navigateur.newContext({
        viewport: { width: 874, height: 402 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
        permissions: ["clipboard-read", "clipboard-write"],
    });
    const page = await contexte.newPage();
    const erreurs = [];
    page.on("pageerror", (e) => erreurs.push(String(e)));
    page.on("dialog", (d) => d.accept());
    await page.goto(URL + "#editeur");
    await page.waitForSelector("#ecran-editeur-liste:not(.cachee)", { timeout: 180000 });
    verifier((await page.locator("#tableau-editeur tbody tr").count()) === 40, "40 cartes dans la liste");
    const entetes = (await page.locator("#tableau-editeur th").allTextContents()).map((texte) => texte.replace(/[▲▼]/g, "").trim());
    verifier(entetes.join("|") === "|Nom|Coût|Rareté|Catégorie|Module|Munitions|Description", `colonnes (${entetes.join("|")})`);
    verifier((await page.locator('#tableau-editeur tr[data-id="CRT_47"] .col-description').textContent()).includes("14"), "description avec les valeurs remplacées");
    const debordement = await page.evaluate(() => {
        const c = document.getElementById("conteneur-tableau-editeur");
        return { page: document.documentElement.scrollWidth - window.innerWidth, tableau: c.scrollWidth - c.clientWidth, lignesVisibles: Math.floor(c.clientHeight / 32) };
    });
    verifier(debordement.page <= 0 && debordement.tableau <= 0, `aucun défilement horizontal (${JSON.stringify(debordement)})`);
    await page.screenshot({ path: `${captures}/1_liste.png` });

    await page.locator('#tableau-editeur tr[data-id="CRT_47"]').click();
    await page.waitForSelector("#ecran-editeur-carte:not(.cachee)");
    await page.screenshot({ path: `${captures}/2_detail.png` });
    verifier((await page.locator(".apercu-editeur").textContent()).includes("14"), "aperçu de la description");
    verifier((await page.locator("legend", { hasText: "Effets" }).count()) === 0, "pas de saisie des effets");
    const cout = page.locator('.saisie-editeur[data-chemin=\'["cout"]\']');
    await cout.fill("3");
    await cout.blur();
    verifier((await page.locator(".rappel-jeu").first().textContent()).includes("jeu : 2"), "rappel de la valeur du jeu");
    verifier((await page.locator("#titre-editeur-carte .pastille-modifiee").count()) === 1, "pastille Modifiée dans le détail");
    await page.screenshot({ path: `${captures}/3_detail_modifie.png`, fullPage: true });
    await page.locator("#bouton-fermer-carte-editeur").click();
    verifier((await page.locator('#tableau-editeur tr[data-id="CRT_47"] .pastille-modifiee').count()) === 1, "pastille Modifiée dans la liste");

    await page.reload();
    await page.waitForSelector("#ecran-editeur-liste:not(.cachee)", { timeout: 180000 });
    verifier((await page.locator('#tableau-editeur tr[data-id="CRT_47"] .pastille-modifiee').count()) === 1, "modification retrouvée après rechargement");

    await page.locator("#bouton-nouvelle-carte-editeur").click();
    await page.waitForSelector("#ecran-editeur-carte:not(.cachee)");
    // Id propose : le premier CRT_n libre apres les cartes du jeu (CRT_111 depuis le lot 1 du plan des cartes)
    const idNouvelle = (await page.locator("#titre-editeur-carte").textContent()).match(/CRT_\d+/)[0];
    verifier(idNouvelle === "CRT_111", "nouvelle carte : premier id libre proposé");
    const nom = page.locator('.saisie-editeur[data-chemin=\'["nom"]\']');
    await nom.fill("Tir de barrage");
    await nom.blur();
    await page.locator('.coche-module[value="MOD_2"]').check();
    const description = page.locator('.saisie-editeur[data-chemin=\'["description"]\']');
    await description.fill("Inflige {inconnu} dégâts");
    await description.blur();
    verifier((await page.locator(".erreurs-editeur li").count()) >= 1, "erreur affichée pour une valeur inconnue");
    await page.screenshot({ path: `${captures}/4_nouvelle_erreur.png`, fullPage: true });
    await page.locator("#bouton-fermer-carte-editeur").click();
    verifier(await page.locator("#bouton-copier-editeur").isDisabled(), "copie bloquée tant qu'une carte est en erreur");
    await page.locator(`#tableau-editeur tr[data-id="${idNouvelle}"]`).click();
    await description.fill("Inflige {degats} dégâts à tous les ennemis");
    await description.blur();
    await page.locator('.liste-editeur[data-chemin=\'["cible"]\']').selectOption("Ennemi Tous");
    await page.locator("#bouton-fermer-carte-editeur").click();
    verifier(!(await page.locator("#bouton-copier-editeur").isDisabled()), "copie possible une fois corrigée");
    verifier((await page.locator(`#tableau-editeur tr[data-id="${idNouvelle}"] .pastille-nouvelle`).count()) === 1, "pastille Nouvelle");

    await page.locator('#tableau-editeur tr[data-id="CRT_16"]').click();
    await page.locator('.liste-editeur[data-chemin=\'["jouable"]\']').selectOption("supprimee");
    await page.locator("#bouton-fermer-carte-editeur").click();
    verifier((await page.locator('#tableau-editeur tr[data-id="CRT_16"].ligne-supprimee').count()) === 1, "carte supprimée grisée");

    await page.locator("#filtre-editeur").selectOption("modifiees");
    verifier((await page.locator("#tableau-editeur tbody tr").count()) === 3, "filtre Modifiées : 3 cartes");
    await page.locator("#filtre-editeur").selectOption("toutes");
    await page.locator('#tableau-editeur th[data-colonne="cout"]').click();
    const premierCout = await page.locator("#tableau-editeur tbody tr:first-child .col-cout").textContent();
    verifier(premierCout.trim() === "1", "tri par coût");
    await page.screenshot({ path: `${captures}/5_liste_modifiee.png` });

    await page.locator("#bouton-copier-editeur").click();
    await page.waitForTimeout(500);
    const texte = await page.evaluate(() => navigator.clipboard.readText());
    const cartes = JSON.parse(texte).cartes;
    verifier(cartes.length === 3, "copie : seulement les 3 cartes modifiées ou ajoutées");
    verifier(cartes.find((c) => c.id === "CRT_47").cout === 3 && cartes.find((c) => c.id === "CRT_16").jouable === "supprimee", "copie : modifications appliquées");
    const nouvelle = cartes[cartes.length - 1];
    verifier(nouvelle.id === idNouvelle && nouvelle.modules[0] === "MOD_2", "copie : nouvelle carte à la fin, avec son module");
    verifier(nouvelle.effets.length === 0, "copie : effets de la nouvelle carte laissés à l'agent");
    fs.writeFileSync(`${captures}/cartes_copiees.json`, texte);

    // Bouton Admin : seulement pour certains joueurs
    await page.locator("#bouton-retour-editeur").click();
    await page.waitForSelector("#ecran-selection-joueur:not(.cachee)");
    for (const [nomJoueur, attendu] of [["Paul", false], ["Tom", true]]) {
        await page.locator("#nom-nouveau-joueur").fill(nomJoueur);
        await page.locator("#bouton-creer-joueur").click();
        await page.waitForSelector("#ecran-accueil-joueur:not(.cachee)");
        verifier((await page.locator("#bouton-admin").isVisible()) === attendu, `bouton Admin ${attendu ? "visible" : "caché"} pour ${nomJoueur}`);
        if (attendu) {
            await page.screenshot({ path: `${captures}/6_accueil_admin.png` });
            await page.locator("#bouton-admin").click();
            await page.waitForSelector("#ecran-editeur-liste:not(.cachee)");
            await page.locator("#bouton-retour-editeur").click();
            await page.waitForSelector("#ecran-accueil-joueur:not(.cachee)");
            verifier(true, "Admin ouvre l'outil, ← Jeu ramène à l'accueil");
        }
        await page.evaluate(() => afficherSelectionJoueur());
    }
    verifier(erreurs.length === 0, `aucune erreur JavaScript (${erreurs.join(" | ")})`);
    await navigateur.close();
    console.log(`Tous les controles sont bons. Captures : ${captures}`);
})().catch((e) => { console.error(e.message); process.exit(1); });
