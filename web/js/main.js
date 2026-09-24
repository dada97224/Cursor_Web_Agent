import { api, cocherCourse } from "./api.js";
import { personneActive } from "./dom.js";
import { valeurs } from "./vues.js";
import * as vues from "./vues.js";

const racine = document.querySelector("#application");
const alerte = document.querySelector("#alerte");
let jeton = 0;

function montrerErreur(erreur) {
  alerte.hidden = false;
  alerte.textContent = erreur.message || "Ça n'a pas fonctionné";
}

function cacherErreur() {
  alerte.hidden = true;
  alerte.textContent = "";
}

function route() {
  const hash = (location.hash || "#/").replace(/^#/, "");
  const [chemin, requete] = hash.split("?");
  const parties = chemin.split("/").filter(Boolean);
  return { page: parties[0] || "accueil", id: parties[1] || "", params: new URLSearchParams(requete || "") };
}

async function rendre() {
  const moi = ++jeton;
  cacherErreur();
  const { page, id, params } = route();
  racine.replaceChildren(domAttente());
  try {
    if (moi !== jeton) return;
    racine.replaceChildren();
    await choisir(page, id, params);
    marquerNav(page);
  } catch (erreur) {
    if (moi !== jeton) return;
    montrerErreur(erreur);
  }
}

function domAttente() {
  const p = document.createElement("p");
  p.className = "pas";
  p.textContent = "Un instant…";
  return p;
}

async function choisir(page, id, params) {
  switch (page) {
    case "accueil": return vues.accueil(racine);
    case "cuisine": return vues.cuisine(racine, "cuisine");
    case "congelo": return vues.cuisine(racine, "congelo");
    case "courses": return vues.courses(racine);
    case "ajouter": return vues.ajouter(racine);
    case "ticket": return vues.ticket(racine, id);
    case "produit": return vues.produit(racine, id, params);
    case "pharmacie": return vues.listesSimples(racine, "pharmacie");
    case "reserves": return vues.listesSimples(racine, "reserves");
    case "plantes": return vues.plantes(racine);
    case "menage": return vues.menage(racine);
    case "animaux": return vues.animaux(racine);
    case "dates": return vues.dates(racine);
    case "menus": return vues.menus(racine);
    case "qui": return vues.qui(racine);
    case "maison": return vues.maison(racine);
    case "reglages": return vues.reglages(racine);
    default: {
      racine.replaceChildren();
      const p = document.createElement("p");
      p.textContent = "Page introuvable.";
      racine.append(p);
      return null;
    }
  }
}

function marquerNav(page) {
  const actif = page === "congelo" ? "cuisine" : page;
  for (const lien of document.querySelectorAll(".nav a")) {
    lien.classList.toggle("actif", lien.dataset.nav === actif);
  }
}

function personne() {
  return personneActive();
}

document.body.addEventListener("click", async (evenement) => {
  const boutonClique = evenement.target.closest("[data-action]");
  if (!boutonClique || boutonClique.type === "submit") return;
  const action = boutonClique.dataset.action;
  try {
    switch (action) {
      case "etat":
        await api(`/api/produits/${boutonClique.dataset.id}/etat`, { method: "POST", corps: { etat: boutonClique.dataset.etat } });
        break;
      case "cocher":
        await cocherCourse(Number(boutonClique.dataset.id), boutonClique.dataset.coche === "1");
        break;
      case "ranger":
        await api(`/api/courses/${boutonClique.dataset.id}/ranger`, { method: "POST" });
        break;
      case "manques":
        await api("/api/courses/manques", { method: "POST", corps: { personne_id: personne().id } });
        break;
      case "vider":
        await api("/api/courses", { method: "DELETE" });
        break;
      case "rejeter":
        await api(`/api/tickets/${boutonClique.dataset.ticket}/lignes/${boutonClique.dataset.ligne}/rejeter`, { method: "POST" });
        break;
      case "arroser":
        await api(`/api/plantes/${boutonClique.dataset.id}/arroser`, { method: "POST", corps: { personne_id: personne().id, par: personne().nom } });
        break;
      case "menage":
        await api(`/api/menage/${boutonClique.dataset.id}/fait`, { method: "POST", corps: { personne_id: personne().id, par: personne().nom } });
        break;
      case "suggestion": {
        const champTexte = document.querySelector(".compositeur input[name=texte]");
        if (champTexte) champTexte.value = boutonClique.dataset.texte;
        return;
      }
      case "choisir-photo":
        document.getElementById("photo-chat")?.click();
        return;
      case "micro":
        ecouter();
        return;
      case "personne":
        localStorage.setItem("maison.personne", boutonClique.dataset.id);
        localStorage.setItem("maison.personneNom", boutonClique.dataset.nom);
        location.hash = "#/";
        return;
      case "exemple":
        await api("/api/exemple", { method: "POST" });
        break;
      case "supprimer-produit":
      case "supprimer-plante":
      case "supprimer-animal":
      case "supprimer-date":
      case "supprimer-lieu":
        if (boutonClique.dataset.confirme !== "oui") {
          boutonClique.dataset.confirme = "oui";
          boutonClique.textContent = "Oui, enlever";
          return;
        }
        await supprimer(action, boutonClique.dataset.id);
        break;
      default:
        throw new Error(`Action inconnue : ${action}`);
    }
    await rendre();
  } catch (erreur) {
    montrerErreur(erreur);
  }
});

async function supprimer(action, id) {
  const chemins = {
    "supprimer-produit": `/api/produits/${id}`,
    "supprimer-plante": `/api/plantes/${id}`,
    "supprimer-animal": `/api/animaux/${id}`,
    "supprimer-date": `/api/dates/${id}`,
    "supprimer-lieu": `/api/lieux/${id}`,
  };
  await api(chemins[action], { method: "DELETE" });
  if (action === "supprimer-produit") location.hash = "#/cuisine";
}

document.body.addEventListener("submit", async (evenement) => {
  const formulaire = evenement.target.closest("form");
  if (!formulaire) return;
  evenement.preventDefault();
  const genre = formulaire.dataset.form;
  const saisie = valeurs(formulaire);
  try {
    switch (genre) {
      case "course":
        await api("/api/courses", { method: "POST", corps: { nom: saisie.nom, magasin: saisie.magasin || "", rayon: saisie.rayon || "", personne_id: personne().id } });
        break;
      case "personne":
        await api("/api/personnes", { method: "POST", corps: { nom: saisie.nom } });
        break;
      case "lieu":
        await api("/api/lieux", { method: "POST", corps: { piece: saisie.piece, nom: saisie.nom } });
        break;
      case "plante":
        await api("/api/plantes", { method: "POST", corps: { nom: saisie.nom, piece: saisie.piece, intervalle_jours: Number(saisie.intervalle_jours || 7) } });
        break;
      case "menage":
        await api("/api/menage", { method: "POST", corps: { piece: saisie.piece, frequence_jours: Number(saisie.frequence_jours || 7) } });
        break;
      case "animal":
        await api("/api/animaux", { method: "POST", corps: { nom: saisie.nom, espece: saisie.espece, repas: saisie.repas, soin: saisie.soin, prochain_soin: saisie.prochain_soin || null } });
        break;
      case "date":
        await api("/api/dates", { method: "POST", corps: { titre: saisie.titre, jour: Number(saisie.jour), mois: Number(saisie.mois) } });
        break;
      case "produit":
        await enregistrerProduit(formulaire, saisie);
        break;
      case "menus":
        await enregistrerMenus(formulaire);
        break;
      case "ligne":
        await confirmerLigne(formulaire, saisie);
        break;
      case "ligne-nouvelle":
        await api(`/api/tickets/${formulaire.dataset.ticket}/lignes`, { method: "POST", corps: corpsLigne(saisie) });
        break;
      case "photo":
        await envoyerPhoto(formulaire, evenement.submitter);
        return;
      case "dire":
        await envoyerDire(formulaire, saisie);
        break;
      default:
        throw new Error(`Formulaire inconnu : ${genre}`);
    }
    await rendre();
  } catch (erreur) {
    montrerErreur(erreur);
  }
});

function corpsLigne(saisie) {
  return {
    nom: saisie.nom,
    quantite: Number(saisie.quantite || 1),
    categorie: saisie.categorie,
    lieu_id: saisie.lieu_id ? Number(saisie.lieu_id) : null,
    produit_id: saisie.produit_id ? Number(saisie.produit_id) : null,
    unite: "pièce",
  };
}

async function confirmerLigne(formulaire, saisie) {
  await api(
    `/api/tickets/${formulaire.dataset.ticket}/lignes/${formulaire.dataset.ligne}/confirmer`,
    { method: "POST", corps: corpsLigne(saisie) },
  );
}

async function enregistrerProduit(formulaire, saisie) {
  const corps = {
    nom: saisie.nom,
    categorie: saisie.categorie,
    lieu_id: saisie.lieu_id ? Number(saisie.lieu_id) : null,
    quantite: Number(saisie.quantite || 0),
    unite: saisie.unite || "pièce",
    etat: saisie.etat,
    date_limite: saisie.date_limite || null,
    magasin: saisie.magasin || "",
    rayon: saisie.rayon || "",
    code_barres: saisie.code_barres || "",
    note: saisie.note || "",
  };
  if (formulaire.dataset.id) {
    await api(`/api/produits/${formulaire.dataset.id}`, { method: "PATCH", corps });
  } else {
    const cree = await api("/api/produits", { method: "POST", corps });
    location.hash = `#/produit/${cree.id}`;
  }
}

async function enregistrerMenus(formulaire) {
  const lignes = [];
  for (const champSaisie of formulaire.querySelectorAll("input")) {
    const [moment, jour] = champSaisie.name.split("-");
    if (moment !== "midi" && moment !== "soir") continue;
    const dateJour = champSaisie.name.slice(moment.length + 1);
    lignes.push({ jour: dateJour, moment, titre: champSaisie.value, court: false });
  }
  await api("/api/menus", { method: "PUT", corps: { lignes } });
}

async function envoyerDire(formulaire, saisie) {
  const fichier = formulaire.querySelector("input[type=file]")?.files?.[0];
  const auteur = personne().nom || "";
  if (fichier) {
    const corps = new FormData();
    corps.append("photo", fichier);
    corps.append("texte", saisie.texte || "");
    corps.append("auteur", auteur);
    const resultat = await api("/api/messages/photo", { method: "POST", corps });
    direAVoixHaute(resultat.reponse);
    return;
  }
  const resultat = await api("/api/messages", { method: "POST", corps: { texte: saisie.texte, auteur } });
  direAVoixHaute(resultat.reponse);
}

function direAVoixHaute(texte) {
  if (!sessionStorage.getItem("maison.voix") || !window.speechSynthesis) return;
  sessionStorage.removeItem("maison.voix");
  const phrase = new SpeechSynthesisUtterance(texte.slice(0, 400));
  phrase.lang = "fr-FR";
  window.speechSynthesis.speak(phrase);
}

function ecouter() {
  const Reconnaissance = window.SpeechRecognition || window.webkitSpeechRecognition;
  const champTexte = document.querySelector(".compositeur input[name=texte]");
  if (!Reconnaissance) {
    montrerErreur(new Error("Le bouton micro marche sur l'ordinateur. Sur le téléphone, utilise le micro du clavier."));
    champTexte?.focus();
    return;
  }
  const reconnaissance = new Reconnaissance();
  reconnaissance.lang = "fr-FR";
  reconnaissance.onresult = (evenement) => {
    if (champTexte) champTexte.value = evenement.results[0][0].transcript;
    sessionStorage.setItem("maison.voix", "1");
    champTexte?.form?.requestSubmit();
  };
  reconnaissance.start();
}

async function envoyerPhoto(formulaire, submitter) {
  const fichier = formulaire.querySelector("input[type=file]").files[0];
  if (!fichier) throw new Error("Choisis une photo");
  const mode = submitter?.dataset.mode || "ticket";
  const corps = new FormData();
  corps.append("photo", fichier);
  if (mode === "produit") {
    const reconnu = await api("/api/reconnaissance", { method: "POST", corps });
    if (reconnu.produit) {
      location.hash = `#/produit/${reconnu.produit.id}`;
      return;
    }
    const params = new URLSearchParams({ categorie: "cuisine" });
    if (reconnu.code_barres) params.set("code", reconnu.code_barres);
    location.hash = `#/produit/nouveau?${params}`;
    return;
  }
  if (personne().id) corps.append("personne_id", String(personne().id));
  const ticket = await api("/api/tickets", { method: "POST", corps });
  location.hash = `#/ticket/${ticket.id}`;
}

document.body.addEventListener("input", (evenement) => {
  if (!evenement.target.dataset.filtre) return;
  const cherche = evenement.target.value.toLowerCase();
  for (const carte of document.querySelectorAll("[data-nom]")) {
    carte.hidden = !carte.dataset.nom.toLowerCase().includes(cherche);
  }
});

window.addEventListener("hashchange", rendre);
if (!location.hash) location.replace("#/");
rendre();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}
