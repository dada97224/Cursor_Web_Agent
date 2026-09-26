"""Liste de courses, séparée du stock jusqu'au rangement."""

from maison.produits import ajouter_quantite, creer, meilleur_nom
from maison.texte import maintenant_iso, nombre, plier


def _vers(row) -> dict:
    data = dict(row)
    data["quantite"] = nombre(data["quantite"])
    data["coche"] = bool(data["coche"])
    return data


def lister(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM courses ORDER BY coche, magasin, rayon, nom").fetchall()
    return [_vers(row) for row in rows]


def ajouter(conn, champs: dict) -> dict:
    nom = champs["nom"].strip()
    produit = None
    if champs.get("produit_id"):
        produit = {"id": champs["produit_id"]}
    else:
        produit = meilleur_nom(conn, nom)
        if produit and score_exact(nom, produit["nom"]):
            pass
        elif produit and plier(nom) != plier(produit["nom"]) and not champs.get("lier"):
            # Un ajout tapé à la main ne se colle à un produit que si le nom est le même.
            if plier(nom) not in plier(produit["nom"]) and plier(produit["nom"]) not in plier(nom):
                produit = None
    curseur = conn.execute(
        """
        INSERT INTO courses (produit_id, nom, quantite, unite, magasin, rayon, personne_id, cree_le)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            produit["id"] if produit else None,
            produit["nom"] if produit and produit.get("nom") else nom,
            float(champs.get("quantite") or 1),
            champs.get("unite") or "pièce",
            champs.get("magasin") or (produit.get("magasin") if produit else "") or "",
            champs.get("rayon") or (produit.get("rayon") if produit else "") or "",
            champs.get("personne_id"),
            maintenant_iso(),
        ),
    )
    return _vers(conn.execute("SELECT * FROM courses WHERE id = ?", (curseur.lastrowid,)).fetchone())


def score_exact(nom: str, autre: str) -> bool:
    return plier(nom) == plier(autre) or plier(nom) in plier(autre) or plier(autre) in plier(nom)


def modifier(conn, course_id: int, champs: dict) -> dict | None:
    actuel = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not actuel:
        return None
    quantite = float(champs.get("quantite", actuel["quantite"]))
    coche = int(champs.get("coche", actuel["coche"]))
    conn.execute(
        "UPDATE courses SET quantite = ?, coche = ?, nom = ?, magasin = ?, rayon = ? WHERE id = ?",
        (
            quantite,
            coche,
            champs.get("nom", actuel["nom"]),
            champs.get("magasin", actuel["magasin"]),
            champs.get("rayon", actuel["rayon"]),
            course_id,
        ),
    )
    return _vers(conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone())


def supprimer(conn, course_id: int) -> bool:
    return conn.execute("DELETE FROM courses WHERE id = ?", (course_id,)).rowcount > 0


def vider_cochees(conn) -> int:
    curseur = conn.execute("DELETE FROM courses WHERE coche = 1")
    return curseur.rowcount


def depuis_manques(conn, personne_id: int | None) -> int:
    deja = {
        row["produit_id"]
        for row in conn.execute("SELECT produit_id FROM courses WHERE coche = 0 AND produit_id IS NOT NULL")
    }
    ajoutes = 0
    rows = conn.execute(
        "SELECT * FROM produits WHERE etat IN ('plus', 'bientot_fini')"
    ).fetchall()
    for row in rows:
        if row["id"] in deja:
            continue
        ajouter(conn, {
            "produit_id": row["id"],
            "nom": row["nom"],
            "quantite": 1,
            "unite": row["unite"],
            "magasin": row["magasin"],
            "rayon": row["rayon"],
            "personne_id": personne_id,
            "lier": True,
        })
        ajoutes += 1
    return ajoutes


def ranger(conn, course_id: int) -> dict | None:
    ligne = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not ligne:
        return None
    if ligne["produit_id"]:
        produit = ajouter_quantite(conn, ligne["produit_id"], float(ligne["quantite"]))
    else:
        produit = creer(conn, {
            "nom": ligne["nom"],
            "categorie": "cuisine",
            "quantite": float(ligne["quantite"]),
            "unite": ligne["unite"],
            "magasin": ligne["magasin"],
            "rayon": ligne["rayon"],
            "etat": "y_en_a",
        })
    supprimer(conn, course_id)
    return produit
