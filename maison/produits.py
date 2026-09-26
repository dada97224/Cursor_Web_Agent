"""Stock : cuisine, congélateur, pharmacie, consommables."""

from datetime import date, timedelta

from maison.texte import maintenant_iso, nombre, score_noms

CATEGORIES = ("cuisine", "congelo", "pharmacie", "consommable")
ETATS = ("y_en_a", "bientot_fini", "plus")

_SELECT = """
SELECT produits.*, lieux.nom AS lieu_nom, lieux.piece AS lieu_piece
FROM produits
LEFT JOIN lieux ON lieux.id = produits.lieu_id
"""


def _aligner(quantite: float, etat: str) -> tuple[float, str]:
    # « Plus » vide le stock. Les deux autres états gardent au moins une unité.
    if etat == "plus":
        return 0, "plus"
    if etat not in ETATS:
        etat = "y_en_a"
    if quantite <= 0:
        return 1, etat
    return quantite, etat


def _alerte(categorie: str, date_limite: str | None, aujourdhui: date | None = None) -> str:
    if not date_limite:
        return ""
    aujourdhui = aujourdhui or date.today()
    try:
        limite = date.fromisoformat(date_limite[:10])
    except ValueError:
        return ""
    if categorie == "congelo":
        return "ancien" if (aujourdhui - limite).days >= 120 else ""
    if limite < aujourdhui:
        return "depasse"
    if limite <= aujourdhui + timedelta(days=30):
        return "bientot"
    return ""


def vers_dict(row) -> dict:
    data = dict(row)
    data["quantite"] = nombre(data["quantite"])
    data["alerte"] = _alerte(data["categorie"], data["date_limite"])
    if data.get("lieu_nom"):
        data["lieu_libelle"] = f"{data['lieu_piece']} · {data['lieu_nom']}"
    else:
        data["lieu_libelle"] = ""
    return data


def lister(conn, categorie: str | None = None) -> list[dict]:
    if categorie:
        rows = conn.execute(_SELECT + " WHERE categorie = ? ORDER BY nom", (categorie,)).fetchall()
    else:
        rows = conn.execute(_SELECT + " ORDER BY nom").fetchall()
    return [vers_dict(row) for row in rows]


def obtenir(conn, produit_id: int) -> dict | None:
    row = conn.execute(_SELECT + " WHERE produits.id = ?", (produit_id,)).fetchone()
    return vers_dict(row) if row else None


def trouver_code(conn, code: str) -> dict | None:
    if not code:
        return None
    row = conn.execute(_SELECT + " WHERE code_barres = ?", (code,)).fetchone()
    return vers_dict(row) if row else None


def meilleur_nom(conn, nom: str) -> dict | None:
    meilleur = None
    score = 0.0
    for produit in lister(conn):
        courant = score_noms(nom, produit["nom"])
        if courant > score:
            score = courant
            meilleur = produit
    if meilleur and score >= 0.72:
        return meilleur
    return None


def creer(conn, champs: dict) -> dict:
    quantite, etat = _aligner(float(champs.get("quantite", 1)), champs.get("etat", "y_en_a"))
    instant = maintenant_iso()
    curseur = conn.execute(
        """
        INSERT INTO produits (
            nom, categorie, lieu_id, quantite, unite, etat, date_limite,
            magasin, rayon, code_barres, photo, note, cree_le, maj_le
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            champs["nom"].strip(),
            champs["categorie"],
            champs.get("lieu_id"),
            quantite,
            (champs.get("unite") or "pièce").strip() or "pièce",
            etat,
            champs.get("date_limite") or None,
            champs.get("magasin") or "",
            champs.get("rayon") or "",
            champs.get("code_barres") or "",
            champs.get("photo"),
            champs.get("note") or "",
            instant,
            instant,
        ),
    )
    return obtenir(conn, curseur.lastrowid)


def modifier(conn, produit_id: int, champs: dict) -> dict | None:
    actuel = obtenir(conn, produit_id)
    if not actuel:
        return None
    fusion = {
        "nom": champs.get("nom", actuel["nom"]),
        "categorie": champs.get("categorie", actuel["categorie"]),
        "lieu_id": champs["lieu_id"] if "lieu_id" in champs else actuel["lieu_id"],
        "quantite": champs.get("quantite", actuel["quantite"]),
        "unite": champs.get("unite", actuel["unite"]),
        "etat": champs.get("etat", actuel["etat"]),
        "date_limite": champs["date_limite"] if "date_limite" in champs else actuel["date_limite"],
        "magasin": champs.get("magasin", actuel["magasin"]),
        "rayon": champs.get("rayon", actuel["rayon"]),
        "code_barres": champs.get("code_barres", actuel["code_barres"]),
        "photo": champs["photo"] if "photo" in champs else actuel["photo"],
        "note": champs.get("note", actuel["note"]),
    }
    # La photo publique est une URL : on ne la réécrit que si un fichier arrive.
    if isinstance(fusion["photo"], str) and fusion["photo"].startswith("/media/"):
        fusion["photo"] = actuel["photo"] if not str(actuel["photo"] or "").startswith("/media/") else None
    quantite, etat = _aligner(float(fusion["quantite"]), fusion["etat"])
    conn.execute(
        """
        UPDATE produits SET
            nom = ?, categorie = ?, lieu_id = ?, quantite = ?, unite = ?, etat = ?,
            date_limite = ?, magasin = ?, rayon = ?, code_barres = ?, photo = ?,
            note = ?, maj_le = ?
        WHERE id = ?
        """,
        (
            str(fusion["nom"]).strip(),
            fusion["categorie"],
            fusion["lieu_id"],
            quantite,
            fusion["unite"] or "pièce",
            etat,
            fusion["date_limite"] or None,
            fusion["magasin"] or "",
            fusion["rayon"] or "",
            fusion["code_barres"] or "",
            fusion["photo"],
            fusion["note"] or "",
            maintenant_iso(),
            produit_id,
        ),
    )
    return obtenir(conn, produit_id)


def ajouter_quantite(conn, produit_id: int, quantite: float) -> dict | None:
    actuel = obtenir(conn, produit_id)
    if not actuel:
        return None
    return modifier(conn, produit_id, {
        "quantite": float(actuel["quantite"]) + quantite,
        "etat": "y_en_a",
    })


def supprimer(conn, produit_id: int) -> bool:
    curseur = conn.execute("DELETE FROM produits WHERE id = ?", (produit_id,))
    return curseur.rowcount > 0


def lieu_par_defaut(conn, categorie: str) -> int | None:
    preferes = {
        "cuisine": "frigo",
        "congelo": "congel",
        "pharmacie": "pharma",
        "consommable": "evier",
    }
    cible = preferes.get(categorie, "")
    for lieu in conn.execute("SELECT id, nom FROM lieux").fetchall():
        if cible and cible in lieu["nom"].lower().replace("é", "e"):
            return lieu["id"]
    premier = conn.execute("SELECT id FROM lieux ORDER BY id LIMIT 1").fetchone()
    return premier["id"] if premier else None
