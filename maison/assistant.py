"""On parle à la maison en français, elle range et répond."""

import json
import re

from maison import courses, foyer, ocr, produits
from maison.repas import formuler_recette
from maison.texte import maintenant_iso, mot_dans, plier, presenter_nom

# Le premier mot reconnu décide de l'endroit, sans formulaire.
_REGLES = [
    ("pharmacie", "Pharmacie", "Hygiène", ["doliprane", "medicament", "sirop", "pansement", "aspirine"]),
    ("congelo", "Congélateur", "Surgelés", ["surgele", "glace", "pizza", "frite"]),
    ("consommable", "Étagère", "Maison", ["ampoule", "pile", "lessive", "eponge", "savon"]),
    ("cuisine", "Frigo", "Frais", ["lait", "yaourt", "oeuf", "fromage", "beurre", "jambon", "poulet"]),
    ("cuisine", "Frigo", "Fruits et légumes", ["banane", "pomme", "salade", "tomate", "carotte", "courgette"]),
    ("cuisine", "Placard", "Épicerie", ["pate", "riz", "farine", "sucre", "huile", "pain", "semoule", "pois"]),
]

_ALIMENTS = [mot for regle in _REGLES for mot in regle[3]]
_ARTICLE = re.compile(r"\b(du|des|de la|de l'|d'|le|la|les|un|une)\b", re.I)


def _lieu_nomme(conn, indice: str):
    for lieu in foyer.lister_lieux(conn):
        if mot_dans(indice, lieu["nom"]) or mot_dans(indice, lieu["piece"]):
            return lieu
    return None


def _classer(nom: str) -> tuple[str, str, str]:
    for categorie, lieu, rayon, mots in _REGLES:
        if any(mot_dans(mot, nom) for mot in mots):
            return categorie, lieu, rayon
    return "cuisine", "Placard", "À prendre"


def _assurer(conn, nom: str, quantite: float, etat: str, photo: str | None = None) -> dict:
    propre = presenter_nom(nom.strip())
    connu = produits.meilleur_nom(conn, propre)
    if connu:
        if etat == "plus":
            return produits.modifier(conn, connu["id"], {"etat": "plus", "quantite": 0})
        produit = produits.ajouter_quantite(conn, connu["id"], quantite)
        if photo:
            produit = produits.modifier(conn, produit["id"], {"photo": photo})
        return produit
    categorie, lieu_nom, rayon = _classer(propre)
    lieu = _lieu_nomme(conn, lieu_nom) or {"id": produits.lieu_par_defaut(conn, categorie)}
    return produits.creer(conn, {
        "nom": propre,
        "categorie": categorie,
        "lieu_id": lieu["id"] if lieu else None,
        "quantite": 0 if etat == "plus" else quantite,
        "etat": etat,
        "rayon": rayon,
        "photo": photo,
    })


# Une question ouverte vaut mieux qu'une quantité inventée.
_PRECISIONS = [
    ("pain de mie", {"nom": "Pain de mie", "quantite": 1, "unite": "paquet"}),
    ("oeuf", {"question": "Pour les œufs : 6, 12 ou 24 ?", "choix": [6, 12, 24], "nom": "Œufs", "unite": "pièce"}),
    ("coca", {"nom": "Coca", "quantite": 1, "unite": "bouteille", "suppose": "Le Coca, je pars sur 2 litres."}),
    ("lait", {"nom": "Lait", "quantite": 1, "unite": "pack", "suppose": "Un pack de lait."}),
]


def _noms(fragment: str) -> list[str]:
    morceaux = re.split(r",|;|\bet\b", plier(fragment))
    resultat = []
    for morceau in morceaux:
        morceau = _ARTICLE.sub(" ", morceau)
        morceau = re.sub(
            r"\b(ajoute|ajout|ajouter|acheter|achete|faudrait|faut|il|prendre|pense|liste|courses|semaine|range|mets|pose|met|est|sont|ou|ramene|jai|ai|on|actualise|stock)\b",
            " ",
            morceau,
        )
        morceau = re.sub(r"^(de|d)\s+", "", " ".join(morceau.split()))
        if len(morceau) >= 3:
            resultat.append(morceau)
    return resultat


def _lire_attente(conn) -> dict | None:
    row = conn.execute("SELECT contenu FROM attente WHERE id = 1").fetchone()
    if not row:
        return None
    return json.loads(row["contenu"])


def _ecrire_attente(conn, contenu: dict | None) -> None:
    if not contenu:
        conn.execute("DELETE FROM attente WHERE id = 1")
        return
    conn.execute(
        "INSERT INTO attente (id, contenu) VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET contenu = excluded.contenu",
        (json.dumps(contenu),),
    )


def _noter(conn, auteur: str, role: str, texte: str, photo: str | None = None) -> None:
    conn.execute(
        "INSERT INTO messages (auteur, role, texte, photo, cree_le) VALUES (?, ?, ?, ?, ?)",
        (auteur or "Quelqu'un", role, texte, photo, maintenant_iso()),
    )


def histoires(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 40").fetchall()
    messages = []
    for row in reversed(rows):
        messages.append({
            "id": row["id"],
            "auteur": row["auteur"],
            "role": row["role"],
            "texte": row["texte"],
            "photo": f"/media/{row['photo']}" if row["photo"] else None,
        })
    return messages


def repondre(conn, texte: str, auteur: str = "") -> str:
    brut = texte.strip()
    plie = plier(brut)
    suite = _resoudre_attente(conn, brut)
    if suite:
        return suite
    if not brut:
        return "Dis-moi un truc, ou envoie une photo."
    if any(mot in plie for mot in ("aide", "bonjour", "salut", "tu sais faire")):
        return (
            "Tu peux me demander où est un truc, me dire « plus de lait », "
            "m'envoyer la photo du ticket ou du frigo, ou demander ce qu'on mange."
        )
    if "liste" in plie and "course" in plie and any(mot in plie for mot in ("range", "actualise", "stock")):
        return _cloturer_courses(conn)
    # L'intention est cherchée dans toute la phrase, pas au début seulement.
    if any(mot in plie for mot in ("ou est", "ou sont", "ou j", "trouve")):
        return _ou_est(conn, brut)
    if any(mot in plie for mot in ("range", "ranger", "mets ", "pose ")) and any(mot in plie for mot in ("dans ", " au ", " en ", "sous ")):
        return _ranger(conn, brut)
    if any(mot in plie for mot in ("plus de", "plus d ", "n a plus", "na plus", "fini ", "epuise", "termine")):
        return _manque(conn, brut)
    if any(mot in plie for mot in ("acheter", "achete", "pense a prendre", "faut prendre")) or (
        "liste" in plie and any(mot in plie for mot in ("ajoute", "ajout", "mets", "mettre"))
    ):
        return _ajouter_liste(conn, brut)
    if any(mot in plie for mot in ("ramene", "rapporte", "j ai pris", "on a ", "j ai ", "jai ")):
        return _recu(conn, brut)
    if "arros" in plie:
        return _arroser(conn, brut, auteur)
    if "menage" in plie:
        return _menage(conn, brut, auteur)
    if any(mot in plie for mot in ("mange", "recette", "cuisin", "ce soir")):
        return _cuisine(conn)
    if "course" in plie:
        return _courses(conn)
    noms = _noms(brut)
    if noms:
        return "J'ai relevé : " + ", ".join(presenter_nom(nom) for nom in noms) + ". Dis-moi si c'est pour la liste, le stock, ou l'emplacement."
    return "Je n'ai pas saisi l'action. Reformule, par exemple ce qu'il faut acheter ou où tu as rangé quelque chose."


def discuter(conn, texte: str, auteur: str = "") -> str:
    reponse = repondre(conn, texte, auteur)
    _noter(conn, auteur or "Quelqu'un", "personne", texte.strip())
    _noter(conn, "Maison", "maison", reponse)
    return reponse


def _stock_noms(conn) -> list[str]:
    return [
        produit["nom"]
        for produit in produits.lister(conn)
        if produit["etat"] != "plus" and float(produit["quantite"]) > 0 and produit["categorie"] in {"cuisine", "congelo"}
    ]


def _cuisine(conn) -> str:
    return formuler_recette(_stock_noms(conn))


def _precision(nom: str) -> dict | None:
    for cle, regle in _PRECISIONS:
        if mot_dans(cle, nom) or cle in nom:
            return regle
    return None


def _poser_course(conn, nom: str, quantite: float, unite: str) -> None:
    produit = _assurer(conn, nom, 0, "plus")
    courses.ajouter(conn, {
        "nom": produit["nom"],
        "produit_id": produit["id"],
        "quantite": quantite,
        "unite": unite,
        "rayon": produit["rayon"],
        "lier": True,
    })


def _ajouter_liste(conn, texte: str) -> str:
    notes = []
    questions = []
    for nom in _noms(texte):
        regle = _precision(nom) or {"nom": presenter_nom(nom), "quantite": 1, "unite": "pièce"}
        if "question" in regle:
            questions.append(regle)
            continue
        _poser_course(conn, regle["nom"], regle["quantite"], regle["unite"])
        if regle.get("suppose"):
            notes.append(regle["suppose"])
        else:
            notes.append(f"{regle['nom']} ajouté.")
    if questions:
        _ecrire_attente(conn, {"questions": questions})
    else:
        _ecrire_attente(conn, None)
    if not notes and not questions:
        return "Je n'ai pas entendu les articles. Répète : lait, pain de mie, œufs, coca."
    morceaux = []
    if notes:
        morceaux.append("OK. " + " ".join(notes))
    if questions:
        morceaux.append(questions[0]["question"])
    return " ".join(morceaux)


def _resoudre_attente(conn, texte: str) -> str | None:
    attente = _lire_attente(conn)
    if not attente or not attente.get("questions"):
        return None
    nombres = [int(valeur) for valeur in re.findall(r"\d+", texte)]
    if not nombres:
        return None
    question = attente["questions"][0]
    choix = question.get("choix") or []
    if choix and nombres[0] not in choix:
        return question["question"]
    _poser_course(conn, question["nom"], nombres[0], question["unite"])
    reste = attente["questions"][1:]
    _ecrire_attente(conn, {"questions": reste} if reste else None)
    suite = f"{question['nom']} : {nombres[0]}. C'est sur la liste."
    if reste:
        suite += " " + reste[0]["question"]
    return suite


def _cloturer_courses(conn) -> str:
    lignes = [ligne for ligne in courses.lister(conn) if not ligne["coche"]]
    if not lignes:
        return "La liste de courses est déjà vide."
    noms = []
    for ligne in lignes:
        if courses.ranger(conn, ligne["id"]):
            noms.append(ligne["nom"])
    return "Stock actualisé : " + ", ".join(noms) + "."


def _courses(conn) -> str:
    lignes = [ligne["nom"] for ligne in courses.lister(conn) if not ligne["coche"]]
    if not lignes:
        return "La liste de courses est vide."
    return "À acheter : " + ", ".join(lignes) + "."


def _ou_est(conn, texte: str) -> str:
    cible = re.split(r"\bou\b", plier(texte), maxsplit=1)[-1]
    noms = _noms(cible) or _noms(texte)
    if not noms:
        return "De quoi tu parles ?"
    produit = produits.meilleur_nom(conn, noms[0])
    if not produit:
        return f"Je ne connais pas encore {presenter_nom(noms[0])}. Dis-moi où tu le ranges."
    if produit["lieu_libelle"]:
        return f"{produit['nom']} est ici : {produit['lieu_libelle']}."
    return f"{produit['nom']} est noté, mais sans emplacement. Dis : range {produit['nom']} dans le frigo."


def _ranger(conn, texte: str) -> str:
    morceau = plier(texte)
    if " dans " in morceau:
        gauche, droite = morceau.split(" dans ", 1)
    elif " au " in morceau:
        gauche, droite = morceau.split(" au ", 1)
    elif " en " in morceau:
        gauche, droite = morceau.split(" en ", 1)
    else:
        return "Dis par exemple : range le lait dans le frigo."
    noms = _noms(gauche)
    if not noms:
        return "Qu'est-ce que je range ?"
    lieu = _lieu_nomme(conn, droite)
    if not lieu:
        return "Je ne connais pas cet endroit. Regarde dans Réglages, ou dis : frigo, placard, pharmacie."
    produit = _assurer(conn, noms[0], 1, "y_en_a")
    produits.modifier(conn, produit["id"], {"lieu_id": lieu["id"], "etat": produit["etat"], "quantite": produit["quantite"]})
    return f"C'est noté : {produit['nom']} va dans {lieu['piece']}, {lieu['nom']}."


def _manque(conn, texte: str) -> str:
    noms = _noms(re.split(r"plus de|plus d'|fini", texte, maxsplit=1, flags=re.I)[-1])
    if not noms:
        return "Qu'est-ce qui manque ?"
    faits = []
    for nom in noms:
        produit = _assurer(conn, nom, 0, "plus")
        courses.ajouter(conn, {"nom": produit["nom"], "produit_id": produit["id"], "rayon": produit["rayon"], "lier": True})
        faits.append(produit["nom"])
    return "C'est noté, plus de " + ", ".join(faits) + ". Je l'ai mis sur la liste."


def _recu(conn, texte: str) -> str:
    noms = _noms(texte)
    if not noms:
        return "Qu'est-ce que tu as rapporté ?"
    faits = []
    for nom in noms:
        produit = _assurer(conn, nom, 1, "y_en_a")
        faits.append(f"{produit['nom']} ({produit['lieu_libelle'] or 'rangé'})")
    return "J'ai noté : " + ", ".join(faits) + "."


def _arroser(conn, texte: str, auteur: str) -> str:
    plantes = foyer.lister_plantes(conn)
    visees = [plante for plante in plantes if mot_dans(plante["nom"], texte)]
    if not visees:
        visees = plantes
    if not visees:
        return "Il n'y a pas encore de plante. Dis : ajoute le basilic au salon."
    for plante in visees:
        foyer.arroser(conn, plante["id"], auteur)
    return "C'est arrosé : " + ", ".join(plante["nom"] for plante in visees) + "."


def _menage(conn, texte: str, auteur: str) -> str:
    taches = foyer.lister_menage(conn)
    visees = [tache for tache in taches if mot_dans(tache["piece"], texte)]
    if not visees:
        return "Quelle pièce ? Par exemple : ménage de la salle de bain."
    for tache in visees:
        foyer.menage_fait(conn, tache["id"], auteur)
    return "Noté : " + ", ".join(tache["piece"] for tache in visees) + "."


def repondre_photo(conn, chemin, photo: str, legende: str, auteur: str) -> str:
    """Un ticket remplit le stock. Une photo du frigo propose une recette."""
    if legende.strip():
        _noter(conn, auteur or "Quelqu'un", "personne", legende.strip(), photo)
    else:
        _noter(conn, auteur or "Quelqu'un", "personne", "Photo", photo)
    texte = ocr.lire_image(chemin)
    codes = ocr.lire_codes(chemin)
    qr = next((code["valeur"] for code in codes if code["type"] == "QRCODE"), "")
    mention_qr = f"QR lu : {qr}. " if qr else ""
    lignes = ocr.extraire_lignes(texte)
    if len(lignes) >= 1:
        noms = []
        for ligne in lignes:
            produit = _assurer(conn, presenter_nom(ligne["nom"]), float(ligne["quantite"]), "y_en_a")
            noms.append(produit["nom"])
        reponse = mention_qr + "J'ai lu le ticket et rangé : " + ", ".join(noms) + ".\n" + formuler_recette(_stock_noms(conn))
        _noter(conn, "Maison", "maison", reponse)
        return reponse
    code = next((item["valeur"] for item in codes if item["type"] != "QRCODE"), "")
    if code:
        connu = produits.trouver_code(conn, code)
        if connu:
            reponse = f"Je reconnais {connu['nom']}" + (f", dans {connu['lieu_libelle']}." if connu["lieu_libelle"] else ".")
            _noter(conn, "Maison", "maison", reponse)
            return reponse
    aliments = []
    for mot in _ALIMENTS:
        if mot_dans(mot, texte) or (legende and mot_dans(mot, legende)):
            aliments.append(mot)
    if aliments:
        for mot in aliments:
            _assurer(conn, mot, 1, "y_en_a", photo if len(aliments) == 1 else None)
        reponse = "Je vois : " + ", ".join(presenter_nom(mot) for mot in aliments) + ".\n" + formuler_recette(_stock_noms(conn))
        _noter(conn, "Maison", "maison", reponse)
        return reponse
    if legende.strip():
        propre = re.sub(r"^(c'est|c est|voici)\s+", "", plier(legende))
        reponse = repondre(conn, propre or legende, auteur)
        _noter(conn, "Maison", "maison", reponse)
        return reponse
    reponse = mention_qr + "Je n'ai pas reconnu le ticket. Dis les articles, par exemple : lait, œufs, pain. Ou « c'est le lait » avec la photo du paquet."
    _noter(conn, "Maison", "maison", reponse)
    return reponse
