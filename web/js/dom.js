export function dom(balise, { classe, texte, attrs, enfants } = {}) {
  const noeud = document.createElement(balise);
  if (classe) noeud.className = classe;
  if (texte != null) noeud.textContent = texte;
  if (attrs) {
    for (const [cle, valeur] of Object.entries(attrs)) {
      if (valeur != null) noeud.setAttribute(cle, valeur);
    }
  }
  for (const enfant of enfants || []) {
    if (enfant) noeud.append(enfant);
  }
  return noeud;
}

export function champ(libelle, nom, valeur = "", type = "text") {
  return dom("label", {
    texte: libelle,
    enfants: [dom("input", { attrs: { name: nom, type, value: valeur ?? "" } })],
  });
}

export function zone(libelle, nom, valeur = "") {
  const saisie = document.createElement("textarea");
  saisie.name = nom;
  saisie.value = valeur ?? "";
  return dom("label", { texte: libelle, enfants: [saisie] });
}

export function select(libelle, nom, options, valeur) {
  const liste = dom("select", { attrs: { name: nom } });
  for (const option of options) {
    const noeud = dom("option", { texte: option.libelle, attrs: { value: option.valeur } });
    if (String(option.valeur) === String(valeur ?? "")) noeud.selected = true;
    liste.append(noeud);
  }
  return dom("label", { texte: libelle, enfants: [liste] });
}

export function bouton(texte, action, extra = {}) {
  return dom("button", {
    classe: extra.classe || "bouton",
    texte,
    attrs: { type: "button", "data-action": action, ...extra.attrs },
  });
}

export function personneActive() {
  const id = localStorage.getItem("maison.personne");
  return {
    id: id ? Number(id) : null,
    nom: localStorage.getItem("maison.personneNom") || "",
  };
}

export function barre(titre, retour) {
  const qui = personneActive();
  return dom("header", {
    classe: "entete",
    enfants: [
      retour ? dom("a", { classe: "retour", texte: "Retour", attrs: { href: retour } }) : null,
      dom("h1", { texte: titre }),
      dom("a", { classe: "qui", texte: qui.nom || "Qui est là ?", attrs: { href: "#/qui" } }),
    ],
  });
}
