import { api, chargerCourses, cocherCourse } from "./api.js";
import { barre, bouton, champ, dom, personneActive, select, zone } from "./dom.js";

const ETATS = [
  ["y_en_a", "Il y en a"],
  ["bientot_fini", "Bientôt fini"],
  ["plus", "Plus"],
];
const CATEGORIES = [
  ["cuisine", "À manger"],
  ["congelo", "Congélateur"],
  ["pharmacie", "Pharmacie"],
  ["consommable", "Maison"],
];

function etats(produit) {
  return dom("div", {
    classe: "etats",
    enfants: ETATS.map(([valeur, libelle]) => dom("button", {
      classe: produit.etat === valeur ? "actif" : "",
      texte: libelle,
      attrs: { type: "button", "data-action": "etat", "data-id": produit.id, "data-etat": valeur },
    })),
  });
}

function carteProduit(produit) {
  return dom("article", {
    classe: "carte",
    attrs: { "data-nom": produit.nom },
    enfants: [
      dom("a", { attrs: { href: `#/produit/${produit.id}` }, enfants: [
        dom("h2", { texte: produit.nom }),
        produit.lieu_libelle ? dom("p", { classe: "emplacement", texte: produit.lieu_libelle }) : dom("p", { classe: "detail", texte: "Pas encore d'emplacement" }),
        dom("p", { classe: "detail", texte: `${produit.quantite} ${produit.unite}` }),
        produit.date_limite ? dom("p", { classe: produit.alerte ? "detail" : "detail", texte: produit.date_limite }) : null,
      ]}),
      etats(produit),
    ],
  });
}

export async function accueil(racine) {
  const donnees = await api("/api/messages");
  const dernier = [...donnees.messages].reverse().find((message) => message.role === "maison");
  racine.append(
    dom("header", { classe: "entete", enfants: [dom("h1", { texte: "Jarvis" })] }),
    dom("div", { classe: "parler", enfants: [
      dom("button", {
        classe: "ptt",
        texte: "Parler",
        attrs: { type: "button", "data-action": "parler", "aria-label": "Maintenir pour parler" },
      }),
      dom("p", { classe: "detail", texte: "Maintenir pour parler. Relâcher pour envoyer." }),
    ]}),
    dom("form", { classe: "compositeur", attrs: { "data-form": "dire" }, enfants: [
      dom("input", { attrs: { name: "texte", placeholder: "Écrire à Jarvis", autocomplete: "off" } }),
      dom("input", { attrs: { type: "file", name: "photo", accept: "image/*", capture: "environment", id: "photo-chat" } }),
      bouton("Photo", "choisir-photo", { classe: "bouton-secondaire bouton-ligne" }),
      bouton("Envoyer", "rien", { classe: "bouton bouton-ligne", attrs: { type: "submit" } }),
    ]}),
    dernier ? dom("article", { classe: "reponse", enfants: [dom("p", { texte: dernier.texte })] }) : dom("p", { classe: "detail", texte: "Ajoute du lait, du pain de mie, des œufs et du coca à la liste. Ou dis que les courses sont rangées." }),
  );
}

const RUBRIQUES = [
  { id: "frigo", groupe: "Cuisine", titre: "Frigo", test: (p) => p.categorie === "cuisine" && /frigo/i.test(p.lieu_libelle || "") },
  { id: "congelo", groupe: "Cuisine", titre: "Congélateur", test: (p) => p.categorie === "congelo" },
  { id: "secs", groupe: "Cuisine", titre: "Secs", test: (p) => p.categorie === "cuisine" && /placard/i.test(p.lieu_libelle || "") },
  { id: "reserves", groupe: "Cuisine", titre: "Réserves", test: (p) => p.categorie === "cuisine" && /conserve/i.test(p.lieu_libelle || "") },
  { id: "pharmacie", groupe: "Santé", titre: "Pharmacie", test: (p) => p.categorie === "pharmacie" },
  { id: "entretien", groupe: "Maison", titre: "Entretien", test: (p) => p.categorie === "consommable" },
  { id: "courses", groupe: "Courses", titre: "Liste", test: null },
];

export async function stock(racine, rubriqueId) {
  const produits = await api("/api/produits");
  const liste = await api("/api/courses");
  const actif = RUBRIQUES.find((item) => item.id === rubriqueId) || RUBRIQUES[0];
  const elements = actif.id === "courses"
    ? liste
    : produits.filter((produit) => actif.test(produit) || (actif.id === "secs" && produit.categorie === "cuisine" && !/frigo|conserve/i.test(produit.lieu_libelle || "")));
  let groupe = "";
  const liens = [];
  for (const rubrique of RUBRIQUES) {
    if (rubrique.groupe !== groupe) {
      groupe = rubrique.groupe;
      liens.push(dom("p", { classe: "groupe-nav", texte: groupe }));
    }
    liens.push(dom("a", {
      classe: rubrique.id === actif.id ? "rubrique actif" : "rubrique",
      texte: rubrique.titre,
      attrs: { href: `#/stock/${rubrique.id}` },
    }));
  }
  racine.append(
    dom("div", { classe: "stock", enfants: [
      dom("nav", { classe: "colonne", attrs: { "aria-label": "Catégories" }, enfants: liens }),
      dom("section", { enfants: [
        dom("h1", { texte: `${actif.groupe} — ${actif.titre}` }),
        ...elements.map((element) => dom("article", { classe: "ligne-stock", enfants: [
          dom("strong", { texte: element.nom }),
          dom("span", { texte: element.lieu_libelle || element.rayon || "" }),
          dom("span", { texte: `${element.quantite} ${element.unite || ""}`.trim() }),
          element.date_limite ? dom("span", { texte: element.date_limite }) : null,
        ]})),
        elements.length ? null : dom("p", { classe: "detail", texte: "Rien dans cette catégorie." }),
      ]}),
    ]}),
  );
}

function suggestion(texte) {
  return dom("button", {
    classe: "bouton-secondaire bouton-ligne",
    texte,
    attrs: { type: "button", "data-action": "suggestion", "data-texte": texte },
  });
}

export async function cuisine(racine, zoneStock) {
  const categorie = zoneStock === "congelo" ? "congelo" : "cuisine";
  const produits = await api(`/api/produits?categorie=${categorie}`);
  racine.append(
    barre(categorie === "congelo" ? "Congélateur" : "Cuisine"),
    dom("div", { classe: "etats", enfants: [
      dom("a", { classe: categorie === "cuisine" ? "bouton" : "bouton-secondaire", texte: "Placards et frigo", attrs: { href: "#/cuisine" } }),
      dom("a", { classe: categorie === "congelo" ? "bouton" : "bouton-secondaire", texte: "Congélateur", attrs: { href: "#/congelo" } }),
    ]}),
    dom("input", { classe: "recherche", attrs: { type: "search", placeholder: "Chercher", "data-filtre": "oui" } }),
    ...produits.map(carteProduit),
    produits.length ? null : dom("p", { classe: "pas", texte: "Rien ici pour le moment." }),
    dom("a", { classe: "bouton", texte: "Ajouter", attrs: { href: `#/produit/nouveau?categorie=${categorie}` } }),
  );
}

export async function courses(racine) {
  const liste = await chargerCourses();
  const groupes = new Map();
  for (const ligne of liste) {
    const magasin = ligne.magasin || "Courses";
    const rayon = ligne.rayon || "À prendre";
    if (!groupes.has(magasin)) groupes.set(magasin, new Map());
    if (!groupes.get(magasin).has(rayon)) groupes.get(magasin).set(rayon, []);
    groupes.get(magasin).get(rayon).push(ligne);
  }
  const blocs = [];
  for (const [magasin, rayons] of groupes) {
    blocs.push(dom("h2", { texte: magasin }));
    for (const [rayon, lignes] of rayons) {
      blocs.push(dom("section", { classe: "groupe", enfants: [
        dom("h3", { texte: rayon }),
        ...lignes.map((ligne) => dom("article", { classe: "carte ligne-course", enfants: [
          dom("button", {
            classe: ligne.coche ? "coche fait" : "coche",
            texte: ligne.coche ? "✓" : "",
            attrs: { type: "button", "data-action": "cocher", "data-id": ligne.id, "data-coche": ligne.coche ? "0" : "1", "aria-label": "Cocher" },
          }),
          dom("div", { enfants: [
            dom("strong", { texte: ligne.nom }),
            dom("p", { classe: "detail", texte: `${ligne.quantite} ${ligne.unite}` }),
            ligne.coche ? bouton("C'est rangé", "ranger", { classe: "bouton-secondaire", attrs: { "data-id": ligne.id } }) : null,
          ]}),
        ]})),
      ]}));
    }
  }
  racine.append(
    barre("Courses"),
    dom("form", { attrs: { "data-form": "course" }, enfants: [
      champ("Ajouter à la liste", "nom"),
      dom("details", { enfants: [
        dom("summary", { texte: "Magasin et rayon" }),
        champ("Magasin", "magasin"),
        champ("Rayon", "rayon"),
      ]}),
      bouton("Ajouter", "rien", { attrs: { type: "submit" } }),
    ]}),
    ...blocs,
    liste.length ? null : dom("p", { classe: "pas", texte: "La liste est vide." }),
    bouton("Ajouter ce qui manque", "manques"),
    bouton("Enlever ce qui est coché", "vider", { classe: "bouton-secondaire" }),
    dom("a", { classe: "bouton bouton-terre", texte: "Photo du ticket", attrs: { href: "#/ajouter" } }),
  );
}

export function ajouter(racine) {
  racine.append(
    barre("Ajouter"),
    dom("p", { texte: "Au retour des courses, pose le ticket sur la table et prends-le en photo." }),
    dom("form", { attrs: { "data-form": "photo" }, enfants: [
      dom("input", { attrs: { type: "file", name: "photo", accept: "image/*", capture: "environment", required: "required" } }),
      bouton("Lire le ticket", "rien", { classe: "bouton bouton-terre", attrs: { type: "submit", "data-mode": "ticket" } }),
      bouton("C'est un produit", "rien", { classe: "bouton-secondaire", attrs: { type: "submit", "data-mode": "produit" } }),
    ]}),
    dom("a", { classe: "bouton-secondaire", texte: "Écrire le nom", attrs: { href: "#/produit/nouveau?categorie=cuisine" } }),
  );
}

export async function ticket(racine, ticketId) {
  const [donnees, lieux] = await Promise.all([api(`/api/tickets/${ticketId}`), api("/api/lieux")]);
  const optionsLieux = [{ valeur: "", libelle: "Choisir" }, ...lieux.map((lieu) => ({ valeur: lieu.id, libelle: `${lieu.piece} · ${lieu.nom}` }))];
  const restantes = donnees.lignes.filter((ligne) => ligne.statut === "propose");
  racine.append(
    barre("Ticket", "#/courses"),
    dom("img", { classe: "photo-ticket", attrs: { src: donnees.photo, alt: "Ticket de caisse" } }),
    dom("p", { texte: restantes.length ? `${restantes.length} article${restantes.length > 1 ? "s" : ""} à confirmer` : "Tout est traité." }),
    ...donnees.lignes.filter((ligne) => ligne.statut === "propose").map((ligne) => dom("form", {
      classe: "carte",
      attrs: { "data-form": "ligne", "data-ticket": ticketId, "data-ligne": ligne.id },
      enfants: [
        champ("Nom", "nom", ligne.nom),
        champ("Quantité", "quantite", ligne.quantite, "number"),
        ligne.produit_id ? dom("p", { texte: "On ajoutera la quantité à ce produit déjà rangé." }) : null,
        ligne.produit_id ? dom("input", { attrs: { type: "hidden", name: "produit_id", value: ligne.produit_id } }) : null,
        select("Type", "categorie", CATEGORIES.map(([valeur, libelle]) => ({ valeur, libelle })), ligne.categorie),
        select("Endroit", "lieu_id", optionsLieux, ligne.lieu_id),
        bouton("Oui, on l'a", "rien", { attrs: { type: "submit" } }),
        bouton("Ce n'est pas ça", "rejeter", { classe: "bouton-secondaire", attrs: { "data-ticket": ticketId, "data-ligne": ligne.id } }),
      ],
    })),
    dom("form", { attrs: { "data-form": "ligne-nouvelle", "data-ticket": ticketId }, enfants: [
      dom("h2", { texte: "Article illisible" }),
      champ("Nom", "nom"),
      champ("Quantité", "quantite", "1", "number"),
      select("Type", "categorie", CATEGORIES.map(([valeur, libelle]) => ({ valeur, libelle })), "cuisine"),
      select("Endroit", "lieu_id", optionsLieux, ""),
      bouton("Ajouter cet article", "rien", { classe: "bouton-secondaire", attrs: { type: "submit" } }),
    ]}),
    donnees.texte_ocr ? dom("details", { enfants: [dom("summary", { texte: "Texte lu sur le ticket" }), dom("p", { texte: donnees.texte_ocr })] }) : null,
  );
}

export async function produit(racine, id, params) {
  const lieux = await api("/api/lieux");
  const creation = id === "nouveau";
  const donnees = creation ? {
    nom: "", categorie: params.get("categorie") || "cuisine", lieu_id: "", quantite: 1,
    unite: "pièce", etat: "y_en_a", date_limite: "", magasin: "", rayon: "",
    code_barres: params.get("code") || "", note: "",
  } : await api(`/api/produits/${id}`);
  const libelleDate = donnees.categorie === "congelo" ? "Mis au congélateur" : "À utiliser avant";
  racine.append(
    barre(creation ? "Nouveau" : donnees.nom, "#/cuisine"),
    dom("form", { attrs: { "data-form": "produit", "data-id": creation ? "" : id }, enfants: [
      champ("Nom", "nom", donnees.nom),
      select("Type", "categorie", CATEGORIES.map(([valeur, libelle]) => ({ valeur, libelle })), donnees.categorie),
      select("Endroit", "lieu_id", [{ valeur: "", libelle: "Pas encore" }, ...lieux.map((lieu) => ({ valeur: lieu.id, libelle: `${lieu.piece} · ${lieu.nom}` }))], donnees.lieu_id),
      champ("Quantité", "quantite", donnees.quantite, "number"),
      champ("Unité", "unite", donnees.unite),
      select("État", "etat", ETATS.map(([valeur, libelle]) => ({ valeur, libelle })), donnees.etat),
      donnees.categorie === "consommable" ? null : champ(libelleDate, "date_limite", donnees.date_limite || "", "date"),
      champ("Magasin", "magasin", donnees.magasin),
      champ("Rayon", "rayon", donnees.rayon),
      champ("Code-barres", "code_barres", donnees.code_barres),
      zone("Note", "note", donnees.note),
      bouton("Garder", "rien", { attrs: { type: "submit" } }),
    ]}),
    creation ? null : bouton("Enlever", "supprimer-produit", { classe: "bouton-danger", attrs: { "data-id": id } }),
  );
}

export async function listesSimples(racine, genre) {
  const titres = { pharmacie: "Pharmacie", reserves: "Réserves", congelo: "Congélateur" };
  const categorie = genre === "reserves" ? "consommable" : genre === "pharmacie" ? "pharmacie" : "cuisine";
  const produits = await api(`/api/produits?categorie=${categorie}`);
  racine.append(
    barre(titres[genre] || "Liste", "#/maison"),
    dom("input", { classe: "recherche", attrs: { type: "search", placeholder: "Chercher", "data-filtre": "oui" } }),
    ...produits.map(carteProduit),
    produits.length ? null : dom("p", { classe: "pas", texte: "Rien pour le moment." }),
    dom("a", { classe: "bouton", texte: "Ajouter", attrs: { href: `#/produit/nouveau?categorie=${categorie}` } }),
  );
}

export async function plantes(racine) {
  const liste = await api("/api/plantes");
  racine.append(
    barre("Plantes", "#/maison"),
    dom("p", { classe: "pas", texte: "Version simple : un nom, une pièce, et le bouton d'arrosage." }),
    ...liste.map((plante) => dom("article", { classe: "carte", enfants: [
      dom("h2", { texte: plante.nom }),
      dom("p", { classe: "emplacement", texte: plante.piece || "Pièce non précisée" }),
      dom("p", { classe: "detail", texte: plante.dernier_arrosage ? `Arrosée le ${plante.dernier_arrosage}${plante.dernier_par ? " par " + plante.dernier_par : ""}` : "Pas encore arrosée" }),
      bouton("J'ai arrosé", "arroser", { attrs: { "data-id": plante.id } }),
      bouton("Enlever", "supprimer-plante", { classe: "bouton-danger", attrs: { "data-id": plante.id } }),
    ]})),
    dom("form", { attrs: { "data-form": "plante" }, enfants: [
      champ("Nom", "nom"),
      champ("Pièce", "piece", "Salon"),
      champ("Tous les combien de jours", "intervalle_jours", "7", "number"),
      bouton("Ajouter la plante", "rien", { attrs: { type: "submit" } }),
    ]}),
  );
}

export async function menage(racine) {
  const liste = await api("/api/menage");
  racine.append(
    barre("Ménage", "#/maison"),
    ...liste.map((tache) => dom("article", { classe: "carte", enfants: [
      dom("h2", { texte: tache.piece }),
      dom("p", { classe: "detail", texte: tache.dernier_fait ? `Fait le ${tache.dernier_fait}${tache.dernier_par ? " par " + tache.dernier_par : ""}` : "Pas encore noté" }),
      bouton("C'est fait", "menage", { attrs: { "data-id": tache.id } }),
    ]})),
    dom("form", { attrs: { "data-form": "menage" }, enfants: [
      champ("Pièce", "piece"),
      champ("Tous les combien de jours", "frequence_jours", "7", "number"),
      bouton("Ajouter", "rien", { attrs: { type: "submit" } }),
    ]}),
  );
}

export async function animaux(racine) {
  const liste = await api("/api/animaux");
  racine.append(
    barre("Animaux", "#/maison"),
    ...liste.map((animal) => dom("article", { classe: "carte", enfants: [
      dom("h2", { texte: animal.nom }),
      dom("p", { classe: "detail", texte: animal.espece }),
      animal.repas ? dom("p", { texte: animal.repas }) : null,
      animal.soin ? dom("p", { texte: animal.soin }) : null,
      animal.prochain_soin ? dom("p", { classe: "detail", texte: `Prochain soin : ${animal.prochain_soin}` }) : null,
      bouton("Enlever", "supprimer-animal", { classe: "bouton-danger", attrs: { "data-id": animal.id } }),
    ]})),
    dom("form", { attrs: { "data-form": "animal" }, enfants: [
      champ("Nom", "nom"),
      champ("Espèce", "espece"),
      champ("Repas", "repas"),
      champ("Soin", "soin"),
      champ("Prochain soin", "prochain_soin", "", "date"),
      bouton("Ajouter", "rien", { attrs: { type: "submit" } }),
    ]}),
  );
}

export async function dates(racine) {
  const liste = await api("/api/dates");
  racine.append(
    barre("Dates", "#/maison"),
    ...liste.map((evenement) => dom("article", { classe: "carte", enfants: [
      dom("h2", { texte: evenement.titre }),
      dom("p", { texte: evenement.dans === 0 ? "Aujourd'hui" : `Dans ${evenement.dans} jours` }),
      bouton("Enlever", "supprimer-date", { classe: "bouton-danger", attrs: { "data-id": evenement.id } }),
    ]})),
    dom("form", { attrs: { "data-form": "date" }, enfants: [
      champ("Titre", "titre", "Anniversaire de "),
      champ("Jour", "jour", "1", "number"),
      champ("Mois", "mois", "1", "number"),
      bouton("Ajouter", "rien", { attrs: { type: "submit" } }),
    ]}),
  );
}

export async function menus(racine) {
  const semaine = await api("/api/menus");
  racine.append(
    barre("Menus", "#/"),
    dom("form", { attrs: { "data-form": "menus" }, enfants: [
      ...semaine.flatMap((jour) => [
        dom("h2", { texte: jour.libelle }),
        champ("Midi", `midi-${jour.jour}`, jour.midi),
        champ("Soir", `soir-${jour.jour}`, jour.soir),
      ]),
      bouton("Garder la semaine", "rien", { attrs: { type: "submit" } }),
    ]}),
  );
}

export async function qui(racine) {
  const liste = await api("/api/personnes");
  racine.append(
    barre("Qui est là ?"),
    dom("div", { classe: "grille", enfants: liste.map((personne) => dom("button", {
      classe: "personne",
      texte: personne.nom,
      attrs: { type: "button", "data-action": "personne", "data-id": personne.id, "data-nom": personne.nom, style: `background:${personne.couleur}` },
    })) }),
    dom("form", { attrs: { "data-form": "personne" }, enfants: [
      champ("Ajouter quelqu'un", "nom"),
      bouton("Ajouter", "rien", { attrs: { type: "submit" } }),
    ]}),
  );
}

export async function maison(racine) {
  const liens = [
    ["#/pharmacie", "Pharmacie"],
    ["#/plantes", "Plantes"],
    ["#/menage", "Ménage"],
    ["#/reserves", "Réserves"],
    ["#/animaux", "Animaux"],
    ["#/dates", "Dates"],
    ["#/menus", "Menus"],
    ["#/reglages", "Réglages"],
  ];
  racine.append(
    barre("Maison"),
    dom("div", { classe: "grille", enfants: liens.map(([href, texte]) => dom("a", { classe: "tuile", texte, attrs: { href } })) }),
  );
}

export async function reglages(racine) {
  const reseau = await api("/api/reseau");
  const lieux = await api("/api/lieux");
  racine.append(
    barre("Réglages", "#/maison"),
    dom("article", { classe: "carte", enfants: [
      dom("h2", { texte: "Téléphones de la maison" }),
      dom("p", { texte: "Sur le même Wi-Fi, ouvrir cette adresse :" }),
      dom("p", { classe: "emplacement", texte: reseau.url }),
    ]}),
    dom("h2", { texte: "Emplacements" }),
    ...lieux.map((lieu) => dom("article", { classe: "carte", enfants: [
      dom("strong", { texte: `${lieu.piece} · ${lieu.nom}` }),
      bouton("Enlever", "supprimer-lieu", { classe: "bouton-danger", attrs: { "data-id": lieu.id } }),
    ]})),
    dom("form", { attrs: { "data-form": "lieu" }, enfants: [
      champ("Pièce", "piece"),
      champ("Endroit", "nom", "Étagère"),
      bouton("Ajouter l'endroit", "rien", { attrs: { type: "submit" } }),
    ]}),
    bouton("Remplir avec un exemple", "exemple", { classe: "bouton-secondaire" }),
  );
}

export function valeurs(formulaire) {
  const donnees = {};
  for (const champSaisie of formulaire.querySelectorAll("input, select, textarea")) {
    if (!champSaisie.name) continue;
    donnees[champSaisie.name] = champSaisie.value;
  }
  return donnees;
}
