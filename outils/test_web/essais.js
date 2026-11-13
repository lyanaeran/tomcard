// Essais de la version web dans un vrai navigateur (Chromium + Pyodide), au format iPhone 13
// paysage : une partie reelle, des combats prepares, les ecrans hors combat, la reprise d'une
// partie et le rechargement quand les versions different. Aucune regle de jeu ici : le script
// clique comme un joueur et lit l'etat publie par web/bridge.py.
//
//     python -m http.server 8765        (a la racine du depot, dans un autre terminal)
//     node outils/test_web/essais.js [dossier des captures] [adresse]
//
// Demande Node et Playwright avec son Chromium (installes dans les sessions cloud ; sur Mac :
// npm install playwright puis npx playwright install chromium). Sort en erreur (code 1) au
// premier controle faux ou a la moindre erreur JavaScript / Python de la page.

const os = require("os");
const path = require("path");
const fs = require("fs");
const { chromium, devices } = require("playwright");

const DOSSIER = process.argv[2] || fs.mkdtempSync(path.join(os.tmpdir(), "space_fight_web_"));
const ADRESSE = process.argv[3] || "http://localhost:8765/index.html";
const ATTENTE_CHARGEMENT_MS = 240000;

let navigateur = null;
const controles = [];

function verifier(condition, message) {
    controles.push(message);
    if (!condition) throw new Error(`Controle faux : ${message}`);
}

// Ouvre le jeu dans un contexte neuf (localStorage vide) ; toute erreur de la page fait echouer.
async function ouvrir({ avantChargement = null, attendre = true } = {}) {
    const contexte = await navigateur.newContext({ ...devices["iPhone 13 landscape"] });
    const page = await contexte.newPage();
    page.erreurs = [];
    page.on("pageerror", (erreur) => page.erreurs.push(`pageerror : ${erreur.message}`));
    page.on("console", (message) => {
        if (message.type() === "error") page.erreurs.push(`console : ${message.text()}`);
    });
    page.on("dialog", async (dialogue) => {
        page.erreurs.push(`alerte : ${dialogue.message().slice(0, 300)}`);
        await dialogue.dismiss();
    });
    if (avantChargement) await avantChargement(page);
    await page.goto(ADRESSE);
    if (attendre) await attendreSelectionJoueur(page);
    return page;
}

async function attendreSelectionJoueur(page) {
    await page.waitForSelector("#ecran-selection-joueur:not(.cachee)", { timeout: ATTENTE_CHARGEMENT_MS });
}

async function fermer(page, nom) {
    verifier(page.erreurs.length === 0, `${nom} : aucune erreur dans la page (${JSON.stringify(page.erreurs)})`);
    await page.context().close();
}

async function capture(page, nom) {
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(DOSSIER, `${nom}.png`) });
}

// Cree un joueur et une partie, equipe le module propose, jusqu'au choix du niveau 2.
async function nouvellePartie(page, nomJoueur, prendreCarte) {
    await page.fill("#nom-nouveau-joueur", nomJoueur);
    await page.click("#bouton-creer-joueur");
    await page.click("#bouton-nouvelle-partie");
    await page.waitForSelector("#ecran-choix-module:not(.cachee)");
    await page.click("#candidats-module .choix-aventure");
    await page.waitForSelector("#ecran-choix-carte-module:not(.cachee)");
    if (prendreCarte) await page.click("#candidats-carte-module .candidat-recompense");
    else await page.click("#bouton-passer-carte-module");
    await page.waitForSelector("#ecran-choix-niveau:not(.cachee)");
}

const allerA = (page, ecran) => page.evaluate((e) => allerA({ partie: partieActive, ecran: e }), ecran);
const etatCombat = (page) => page.evaluate(() => etatCourant.etat);

// Joue le combat en cours jusqu'au bout : premiere carte jouable sur sa premiere case valide.
async function jouerLeCombat(page) {
    for (let tour = 0; tour < 40 && (await etatCombat(page)) === "EN_COURS"; tour++) {
        for (let coup = 0; coup < 10; coup++) {
            const carte = await page.evaluate(() => {
                const jouable = etatCourant.main.find((c) => c.jouable);
                return jouable ? { index: jouable.index, camp: jouable.camp, idCase: jouable.cases[0] } : null;
            });
            if (!carte) break;
            await page.click(`.carte[data-index="${carte.index}"]`);
            await page.click(`.case.${carte.camp}[data-id="${carte.idCase}"]`, { force: true });
            if ((await etatCombat(page)) !== "EN_COURS") return;
        }
        if ((await etatCombat(page)) === "EN_COURS") await page.click("#tour-suivant");
    }
}

// Prepare un combat precis dans Pyodide (ennemis et main imposes) et l'affiche. Mise en place
// d'essai seulement : le combat lui-meme est celui de src/gameplay.
const PREPARATION_PYTHON = `
import random as _r
from src.gameplay.partie import nouvelle_partie as _np, equiper_module as _eq, modules_de_la_partie as _mods
from src.gameplay.module_new import charger_modules_new as _cm
from src.gameplay.carte_new import charger_cartes_new as _cc
from src.gameplay.ennemi_new import charger_ennemis_new as _ce
from src.gameplay.flotte_new import placer_ennemis as _pl, flotte_boss as _fb
from src.gameplay.combat_new import CombatNew as _CN
from src.gameplay.deck_new import DECK_DE_DEPART as _DEPART, deck_de_depart as _dd
def _essai(ids_ennemis, ids_main, ids_lanceur=()):
    partie = _np(_r.Random(3)); _eq(partie, _cm()["MOD_2"])
    modeles = _cc()
    deck = _dd(modeles, "M1") + [modeles[i].copie(exemplaire_module="M2") for i in ids_lanceur]
    deck += [modeles[i].copie(exemplaire_module="M1") for i in ids_main if i not in _DEPART]
    ennemis = _ce()
    flotte = _fb(ennemis) if ids_ennemis == ["BOSS"] else _pl([ennemis[i].pour_combat(1) for i in ids_ennemis], _r.Random(5))
    combat = _CN([m.copie_pour_combat() for m in _mods(partie)], deck, flotte, _r.Random(7))
    toutes = combat.deck.toutes_les_cartes(); main = []
    for i in ids_main:
        main.append(next(c for c in toutes if c.id == i and c not in main))
    combat.deck.pioche = [c for c in toutes if c not in main]; combat.deck.main = main; combat.deck.defausse = []
    return _demarrer_combat(combat)
`;

async function combatPrepare(page, ennemis, main, lanceur = []) {
    await page.evaluate(
        ([e, m, l]) => {
            masquerTousLesEcrans();
            document.getElementById("app").classList.remove("cachee");
            const essai = pyodide.globals.get("_essai");
            appliquerResultat(JSON.parse(essai(pyodide.toPy(e), pyodide.toPy(m), pyodide.toPy(l))));
            essai.destroy();
        },
        [ennemis, main, lanceur]
    );
    await page.waitForTimeout(200);
}

async function python(page, code) {
    await page.evaluate((c) => {
        pyodide.runPython(c);
        const resultat = pyodide.globals.get("_resultat_combat");
        appliquerResultat(JSON.parse(resultat()));
        resultat.destroy();
    }, code);
}

const idEnnemi = (page, nom) => page.evaluate((n) => etatCourant.ennemis.find((e) => e && e.nom === n && !e.detruit).id, nom);
const carteEnMain = (page, id) => page.evaluate((i) => etatCourant.main.find((c) => c.id_carte === i), id);

async function jouer(page, carte, idCase) {
    await page.click(`.carte[data-index="${carte.index}"]`);
    await page.click(`.case.${carte.camp}[data-id="${idCase}"]`, { force: true });
    await page.waitForTimeout(200);
}

// --- Essais ---

async function essaiPartieReelle() {
    const page = await ouvrir();
    await nouvellePartie(page, "Essai", true);
    await page.evaluate(() => choisirEtape("PRIME"));
    await page.waitForSelector("#app:not(.cachee)");
    await capture(page, "partie_1_debut_de_combat");
    verifier((await page.evaluate(() => etatCourant.main.length)) === 5, "partie : 5 cartes en main au tour 1");
    await page.click(".carte:not(.injouable)");
    await capture(page, "partie_2_carte_selectionnee");
    verifier((await page.locator(".case-valide").count()) > 0, "partie : des cases valides sont marquees");
    await page.click(".carte.selectionnee");
    await jouerLeCombat(page);
    verifier((await etatCombat(page)) === "VICTOIRE", "partie : combat du niveau 2 gagne");
    await page.click("#bouton-journal-combat");
    await capture(page, "partie_3_journal");
    await page.click("#bouton-retour-journal-combat");
    const argentAvant = await page.evaluate(() => partieActive.argent);
    await page.click("#bouton-rejouer");
    await page.waitForSelector("#ecran-fin-combat:not(.cachee)");
    await capture(page, "partie_4_recompense");
    const argent = await page.evaluate(() => partieActive.argent);
    verifier(argent > argentAvant, "partie : Argent gagne a la victoire");

    // Rechargement sur l'ecran de recompense : on y revient, sans rejouer ni regagner d'Argent
    const proposees = await page.locator("#candidats-recompense .candidat-recompense-nom").allTextContents();
    await page.reload();
    await attendreSelectionJoueur(page);
    await page.click(".ligne-joueur");
    await page.click("#bouton-continuer");
    await page.waitForSelector("#ecran-fin-combat:not(.cachee)");
    const reproposees = await page.locator("#candidats-recompense .candidat-recompense-nom").allTextContents();
    verifier(JSON.stringify(reproposees) === JSON.stringify(proposees), "reprise : memes cartes de recompense");
    verifier((await page.evaluate(() => partieActive.argent)) === argent, "reprise : Argent inchange");
    await page.click("#candidats-recompense .candidat-recompense");
    await page.waitForSelector("#ecran-choix-niveau:not(.cachee)");
    verifier((await page.evaluate(() => partieActive.niveau)) === 3, "partie : niveau 3 apres la recompense");
    verifier((await page.evaluate(() => partieActive.deck.length)) === 12, "partie : 12 cartes (10 + module + recompense)");
    await fermer(page, "partie reelle");
}

async function essaiCombatsPrepares() {
    const page = await ouvrir();
    await nouvellePartie(page, "Combats", false);
    await page.evaluate((code) => pyodide.runPython(code), PREPARATION_PYTHON);

    // Miroir : intentions, infobulle, renvoi pose puis subi
    await combatPrepare(page, ["ENM_MIROIR", "ENM_PAT_LE_PIRATE"], ["CRT_7", "CRT_7", "CRT_10", "CRT_45", "CRT_49"]);
    await capture(page, "combat_1_intentions");
    await page.click(`.case.ennemi[data-id="${await idEnnemi(page, "Miroir")}"]`);
    await capture(page, "combat_2_infobulle_ennemi");
    const lignes = await page.locator("#info-case .infobulle-etape-courante").count();
    verifier(lignes === 2, "infobulle de Miroir : ses 2 actions, une par ligne");
    await page.click("#tour-suivant");
    const cibleRenvoi = await page.evaluate(() => (etatCourant.ennemis.find((e) => e && e.renvoi > 0) || {}).id);
    verifier(Boolean(cibleRenvoi), "Miroir : un ennemi porte un renvoi");
    const pvPrincipal = await page.evaluate(() => etatCourant.vaisseau.base.pv);
    await jouer(page, await carteEnMain(page, "CRT_7"), cibleRenvoi);
    await capture(page, "combat_3_renvoi_subi");
    verifier((await page.evaluate(() => etatCourant.vaisseau.base.pv)) < pvPrincipal, "renvoi : le principal perd des PV");

    // Salve laser (x2) puis incendie
    await combatPrepare(page, ["ENM_PETIT_JEAN", "ENM_LE_PUZZLE"], ["CRT_49", "CRT_7", "CRT_45", "CRT_10", "CRT_12"]);
    const salve = await carteEnMain(page, "CRT_49");
    await jouer(page, salve, salve.cases[0]);
    verifier((await carteEnMain(page, "CRT_7")).lancements === 2, "Salve laser : le Laser est lance 2 fois");
    await capture(page, "combat_4_lancements_et_munitions");
    await combatPrepare(page, ["ENM_PETIT_JEAN", "ENM_LE_PUZZLE"], ["CRT_45", "CRT_7", "CRT_10", "CRT_12", "CRT_7"]);
    const puzzle = await idEnnemi(page, "Le puzzle");
    await jouer(page, await carteEnMain(page, "CRT_45"), puzzle);
    verifier((await page.evaluate((id) => etatCourant.ennemis.find((e) => e && e.id === id).incendie, puzzle)) > 0, "incendie pose");
    await capture(page, "combat_5_incendie");

    // Module detruit : ses cartes passent hors service
    await combatPrepare(page, ["ENM_LE_NETTOYEUR"], ["CRT_7", "CRT_7", "CRT_10", "CRT_11", "CRT_12"], ["CRT_9", "CRT_16"]);
    await python(page, 'combat.vaisseau.module_d_exemplaire("M2").pv_combat = 3');
    await page.click("#tour-suivant");
    await capture(page, "combat_6_module_detruit");
    verifier((await page.evaluate(() => etatCourant.hors_service)) === 2, "module detruit : 2 cartes hors service");

    // Boss : Ligne arriere le vise sur sa case affichee
    await combatPrepare(page, ["BOSS"], ["CRT_16", "CRT_7", "CRT_10", "CRT_11", "CRT_12"], ["CRT_16"]);
    await capture(page, "combat_7_boss");
    const pvBoss = await page.evaluate(() => etatCourant.ennemis.find(Boolean).pv);
    const ligneArriere = await carteEnMain(page, "CRT_16");
    await jouer(page, ligneArriere, ligneArriere.cases[0]);
    verifier((await page.evaluate(() => etatCourant.ennemis.find(Boolean).pv)) < pvBoss, "Boss : Ligne arriere le touche");

    // Defaite : la partie est terminee des la fin du combat
    await combatPrepare(page, ["ENM_LE_PUZZLE"], ["CRT_7", "CRT_7", "CRT_10", "CRT_11", "CRT_12"]);
    await python(page, "combat.vaisseau.principal.pv_combat = 2");
    await page.click("#tour-suivant");
    await capture(page, "combat_8_defaite");
    verifier((await etatCombat(page)) === "DEFAITE", "defaite quand le principal est detruit");
    await page.click("#bouton-rejouer");
    await page.waitForSelector("#ecran-fin-combat:not(.cachee)");
    verifier((await page.evaluate(() => partieActive.statut)) === "TERMINEE", "defaite : partie terminee tout de suite");
    await page.click("#bouton-continuer-fin-combat");
    await page.waitForSelector("#ecran-accueil-joueur:not(.cachee)");
    verifier(await page.isVisible("#bouton-nouvelle-partie"), "defaite : l'accueil propose une nouvelle partie");
    await fermer(page, "combats prepares");
}

async function essaiEcransHorsCombat() {
    // Une partie en cours d'une ancienne version doit etre effacee, le profil garde
    const page = await ouvrir({
        avantChargement: (p) =>
            p.addInitScript(() => {
                if (localStorage.getItem("essai_deja_prepare")) return;
                localStorage.setItem("essai_deja_prepare", "1");
                localStorage.setItem("space_fight_joueurs", JSON.stringify([{ version: 1, id: "joueur_ancien", nom: "Ancien" }]));
                localStorage.setItem(
                    "space_fight_partie_joueur_ancien",
                    JSON.stringify({ version: 1, id: "p", nom: "n", statut: "EN_COURS", graine: 1, niveau: 4, argent: 3, vaisseau: {}, deck: [] })
                );
            }),
    });
    await page.click(".ligne-joueur");
    await page.waitForSelector("#ecran-accueil-joueur:not(.cachee)");
    verifier(
        await page.evaluate(() => localStorage.getItem("space_fight_partie_joueur_ancien") === null),
        "ancienne sauvegarde en cours effacee"
    );
    await page.click("#bouton-nouvelle-partie");
    await page.click("#candidats-module .choix-aventure");
    await page.click("#bouton-passer-carte-module");
    await page.waitForSelector("#ecran-choix-niveau:not(.cachee)");

    // Station : Reparer a PV pleins est refuse sans payer ; Ameliorer et Mettre a jour paient
    await page.evaluate(() => { partieActive.argent = 100; });
    await allerA(page, "STATION_SERVICE");
    await page.click('.action-station[data-action="reparer"]');
    verifier((await page.evaluate(() => partieActive.argent)) === 100, "Station : Reparer a PV pleins ne coute rien");
    verifier((await page.locator(".module-station .popup").textContent()).includes("maximum"), "Station : le refus est explique");
    await page.click('.module-station[data-position="avant_gauche"]');
    await page.click('.action-station[data-action="ameliorer"]');
    await page.click('.module-station[data-position="avant_gauche"]');
    await page.click('.action-station[data-action="mettre_a_jour"]');
    await capture(page, "ecrans_1_station");
    const lanceur = await page.evaluate(() => partieActive.vaisseau.avant_gauche);
    verifier(lanceur.pv_max === 30 && lanceur.niveau_maj === 2, "Station : Lanceur ameliore (30 PV max) et mis a jour (niveau 2)");
    verifier((await page.evaluate(() => partieActive.argent)) === 60, "Station : 2 actions payees");
    await page.click("#bouton-termine-station-service");

    // Trois lunes : Bricoler retire une carte
    await allerA(page, "AVENTURE_TROIS_LUNES");
    await page.click('#choix-aventure-trois-lunes .choix-aventure[data-choix="bricoler"]');
    const tailleDeck = await page.evaluate(() => partieActive.deck.length);
    await page.click("#deck-aventure-trois-lunes .carte-deck");
    verifier((await page.evaluate(() => partieActive.deck.length)) === tailleDeck - 1, "Trois lunes : une carte retiree");
    await page.click("#bouton-continuer-aventure-trois-lunes");

    // Asteroides : deux chocs sur le principal, puis la carte offerte
    await allerA(page, "AVENTURE_ASTEROIDES");
    const pvAvant = await page.evaluate(() => partieActive.vaisseau.base.pv);
    await page.click('#choix-aventure-asteroides .choix-aventure[data-choix="traverser"]');
    await page.click("#bouton-continuer-aventure-asteroides");
    await capture(page, "ecrans_2_asteroides");
    verifier((await page.evaluate(() => partieActive.vaisseau.base.pv)) === pvAvant - 10, "Asteroides : 10 PV perdus par le principal");
    if (await page.isVisible("#bouton-prendre-aventure-asteroides")) await page.click("#bouton-prendre-aventure-asteroides");
    await page.click("#bouton-continuer-aventure-asteroides");

    // Police : Detourner une fois, puis Confiscation
    await allerA(page, "AVENTURE_POLICE");
    await capture(page, "ecrans_3_police");
    const avantPolice = await page.evaluate(() => partieActive.deck.length);
    await page.click('#choix-aventure-police .choix-aventure[data-choix="detourner"]');
    verifier((await page.locator('#choix-aventure-police .choix-aventure[data-choix="detourner"]').count()) === 0, "Police : Detourner une seule fois");
    await page.click('#choix-aventure-police .choix-aventure[data-choix="confiscation"]');
    verifier((await page.evaluate(() => partieActive.deck.length)) === avantPolice - 1, "Police : carte confisquee");
    await page.click("#bouton-continuer-aventure-police");

    // Deck en survol, puis combat des Asteroides (3 ennemis)
    await page.evaluate(() => ouvrirSurvolDeck());
    await page.click("#grille-deck .carte-deck");
    await capture(page, "ecrans_4_deck");
    await page.click("#bouton-retour-deck");
    await allerA(page, "AVENTURE_ASTEROIDES");
    await page.click('#choix-aventure-asteroides .choix-aventure[data-choix="affronter"]');
    await capture(page, "ecrans_5_combat_asteroides");
    verifier((await page.evaluate(() => etatCourant.ennemis.filter(Boolean).length)) === 3, "Asteroides : 3 ennemis");
    await fermer(page, "ecrans hors combat");
}

// bridge.py d'une autre version que app.js (fichiers de deux mises en ligne melanges par le
// cache) : la page se recharge, deux fois au plus, puis affiche un message.
async function essaiVersions() {
    for (const durable of [false, true]) {
        let chargements = 0;
        const page = await ouvrir({
            attendre: false,
            avantChargement: (p) =>
                p.route("**/web/bridge.py*", async (route) => {
                    chargements += 1;
                    const reponse = await route.fetch();
                    let texte = await reponse.text();
                    if (durable || chargements === 1) texte = texte.replace(/VERSION_WEB = "\d+"/, 'VERSION_WEB = "0"');
                    await route.fulfill({ response: reponse, body: texte });
                }),
        });
        await page.waitForFunction(
            () => {
                const statut = document.getElementById("statut-chargement");
                const pret = !document.getElementById("ecran-selection-joueur").classList.contains("cachee");
                return pret || (statut && statut.textContent.includes("ferme"));
            },
            null,
            { timeout: ATTENTE_CHARGEMENT_MS }
        );
        const pret = await page.isVisible("#ecran-selection-joueur");
        if (durable) verifier(!pret && chargements === 3, "versions : 2 rechargements puis le message si le decalage dure");
        else verifier(pret && chargements === 2, "versions : un rechargement suffit si le decalage est passager");
        await fermer(page, "versions");
    }
}

(async () => {
    navigateur = await chromium.launch();
    try {
        for (const essai of [essaiPartieReelle, essaiCombatsPrepares, essaiEcransHorsCombat, essaiVersions]) {
            await essai();
            console.log(`ok : ${essai.name}`);
        }
        console.log(`${controles.length} controles passes. Captures : ${DOSSIER}`);
    } catch (erreur) {
        console.error(erreur.message);
        process.exitCode = 1;
    } finally {
        await navigateur.close();
    }
})();
