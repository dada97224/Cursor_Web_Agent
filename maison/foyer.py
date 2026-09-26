"""Personnes, lieux, plantes, ménage, animaux, dates et menus."""

from datetime import date, timedelta

from maison.texte import libelle_jour, maintenant_iso, nombre, prochaine_date

PALETTE = ["#0e6b52", "#b8431f", "#2456a6", "#8a4b08", "#6b3fa0", "#9d342c"]


def _dict(row) -> dict | None:
    return dict(row) if row else None


def lister_personnes(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM personnes ORDER BY nom")]


def creer_personne(conn, nom: str) -> dict:
    n = conn.execute("SELECT COUNT(*) AS n FROM personnes").fetchone()["n"]
    curseur = conn.execute(
        "INSERT INTO personnes (nom, couleur, cree_le) VALUES (?, ?, ?)",
        (nom.strip(), PALETTE[n % len(PALETTE)], maintenant_iso()),
    )
    return _dict(conn.execute("SELECT * FROM personnes WHERE id = ?", (curseur.lastrowid,)).fetchone())


def modifier_personne(conn, personne_id: int, champs: dict) -> dict | None:
    actuel = conn.execute("SELECT * FROM personnes WHERE id = ?", (personne_id,)).fetchone()
    if not actuel:
        return None
    conn.execute(
        "UPDATE personnes SET nom = ?, photo = ? WHERE id = ?",
        (
            champs.get("nom", actuel["nom"]).strip(),
            champs["photo"] if "photo" in champs else actuel["photo"],
            personne_id,
        ),
    )
    return _dict(conn.execute("SELECT * FROM personnes WHERE id = ?", (personne_id,)).fetchone())


def supprimer_personne(conn, personne_id: int) -> bool:
    return conn.execute("DELETE FROM personnes WHERE id = ?", (personne_id,)).rowcount > 0


def lister_lieux(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM lieux ORDER BY piece, nom")]


def creer_lieu(conn, piece: str, nom: str) -> dict:
    curseur = conn.execute(
        "INSERT INTO lieux (piece, nom, cree_le) VALUES (?, ?, ?)",
        (piece.strip(), nom.strip(), maintenant_iso()),
    )
    return _dict(conn.execute("SELECT * FROM lieux WHERE id = ?", (curseur.lastrowid,)).fetchone())


def supprimer_lieu(conn, lieu_id: int) -> bool:
    conn.execute("UPDATE produits SET lieu_id = NULL WHERE lieu_id = ?", (lieu_id,))
    return conn.execute("DELETE FROM lieux WHERE id = ?", (lieu_id,)).rowcount > 0


def lister_plantes(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM plantes ORDER BY nom")]


def creer_plante(conn, champs: dict) -> dict:
    curseur = conn.execute(
        """
        INSERT INTO plantes (nom, piece, photo, intervalle_jours, cree_le)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            champs["nom"].strip(),
            champs.get("piece") or "",
            champs.get("photo"),
            int(champs.get("intervalle_jours") or 7),
            maintenant_iso(),
        ),
    )
    return _dict(conn.execute("SELECT * FROM plantes WHERE id = ?", (curseur.lastrowid,)).fetchone())


def arroser(conn, plante_id: int, par: str) -> dict | None:
    if not conn.execute("SELECT id FROM plantes WHERE id = ?", (plante_id,)).fetchone():
        return None
    conn.execute(
        "UPDATE plantes SET dernier_arrosage = ?, dernier_par = ? WHERE id = ?",
        (date.today().isoformat(), par, plante_id),
    )
    return _dict(conn.execute("SELECT * FROM plantes WHERE id = ?", (plante_id,)).fetchone())


def supprimer_plante(conn, plante_id: int) -> bool:
    return conn.execute("DELETE FROM plantes WHERE id = ?", (plante_id,)).rowcount > 0


def lister_menage(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM menage ORDER BY piece")]


def creer_menage(conn, piece: str, frequence: int) -> dict:
    curseur = conn.execute(
        "INSERT INTO menage (piece, frequence_jours) VALUES (?, ?)",
        (piece.strip(), frequence),
    )
    return _dict(conn.execute("SELECT * FROM menage WHERE id = ?", (curseur.lastrowid,)).fetchone())


def menage_fait(conn, menage_id: int, par: str) -> dict | None:
    if not conn.execute("SELECT id FROM menage WHERE id = ?", (menage_id,)).fetchone():
        return None
    conn.execute(
        "UPDATE menage SET dernier_fait = ?, dernier_par = ? WHERE id = ?",
        (date.today().isoformat(), par, menage_id),
    )
    return _dict(conn.execute("SELECT * FROM menage WHERE id = ?", (menage_id,)).fetchone())


def modifier_menage(conn, menage_id: int, frequence: int) -> dict | None:
    if not conn.execute("SELECT id FROM menage WHERE id = ?", (menage_id,)).fetchone():
        return None
    conn.execute("UPDATE menage SET frequence_jours = ? WHERE id = ?", (frequence, menage_id))
    return _dict(conn.execute("SELECT * FROM menage WHERE id = ?", (menage_id,)).fetchone())


def supprimer_menage(conn, menage_id: int) -> bool:
    return conn.execute("DELETE FROM menage WHERE id = ?", (menage_id,)).rowcount > 0


def lister_animaux(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM animaux ORDER BY nom")]


def creer_animal(conn, champs: dict) -> dict:
    curseur = conn.execute(
        """
        INSERT INTO animaux (nom, espece, repas, soin, prochain_soin, note, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            champs["nom"].strip(),
            champs.get("espece") or "",
            champs.get("repas") or "",
            champs.get("soin") or "",
            champs.get("prochain_soin") or None,
            champs.get("note") or "",
            champs.get("photo"),
        ),
    )
    return _dict(conn.execute("SELECT * FROM animaux WHERE id = ?", (curseur.lastrowid,)).fetchone())


def modifier_animal(conn, animal_id: int, champs: dict) -> dict | None:
    actuel = conn.execute("SELECT * FROM animaux WHERE id = ?", (animal_id,)).fetchone()
    if not actuel:
        return None
    conn.execute(
        """
        UPDATE animaux SET nom = ?, espece = ?, repas = ?, soin = ?, prochain_soin = ?, note = ?, photo = ?
        WHERE id = ?
        """,
        (
            champs.get("nom", actuel["nom"]).strip(),
            champs.get("espece", actuel["espece"]),
            champs.get("repas", actuel["repas"]),
            champs.get("soin", actuel["soin"]),
            champs["prochain_soin"] if "prochain_soin" in champs else actuel["prochain_soin"],
            champs.get("note", actuel["note"]),
            champs["photo"] if "photo" in champs else actuel["photo"],
            animal_id,
        ),
    )
    return _dict(conn.execute("SELECT * FROM animaux WHERE id = ?", (animal_id,)).fetchone())


def supprimer_animal(conn, animal_id: int) -> bool:
    return conn.execute("DELETE FROM animaux WHERE id = ?", (animal_id,)).rowcount > 0


def lister_dates(conn) -> list[dict]:
    rows = [dict(row) for row in conn.execute("SELECT * FROM dates_famille")]
    aujourdhui = date.today()
    for row in rows:
        prochaine = prochaine_date(row["jour"], row["mois"], aujourdhui)
        row["prochaine"] = prochaine.isoformat()
        row["dans"] = (prochaine - aujourdhui).days
        row["libelle"] = f"{row['jour']} {libelle_jour(prochaine).split(' ', 1)[1]}"
    rows.sort(key=lambda row: row["dans"])
    return rows


def creer_date(conn, champs: dict) -> dict:
    curseur = conn.execute(
        "INSERT INTO dates_famille (titre, jour, mois, annee, note) VALUES (?, ?, ?, ?, ?)",
        (
            champs["titre"].strip(),
            int(champs["jour"]),
            int(champs["mois"]),
            champs.get("annee"),
            champs.get("note") or "",
        ),
    )
    return next(row for row in lister_dates(conn) if row["id"] == curseur.lastrowid)


def supprimer_date(conn, date_id: int) -> bool:
    return conn.execute("DELETE FROM dates_famille WHERE id = ?", (date_id,)).rowcount > 0


def semaine(conn, aujourdhui: date | None = None) -> list[dict]:
    aujourdhui = aujourdhui or date.today()
    lundi = aujourdhui - timedelta(days=aujourdhui.weekday())
    connus = {
        (row["jour"], row["moment"]): row
        for row in conn.execute(
            "SELECT * FROM menus WHERE jour >= ? AND jour < ?",
            (lundi.isoformat(), (lundi + timedelta(days=7)).isoformat()),
        )
    }
    jours = []
    for decalage in range(7):
        jour = lundi + timedelta(days=decalage)
        cle = jour.isoformat()
        midi = connus.get((cle, "midi"))
        soir = connus.get((cle, "soir"))
        jours.append({
            "jour": cle,
            "libelle": libelle_jour(jour),
            "aujourdhui": jour == aujourdhui,
            "midi": midi["titre"] if midi else "",
            "midi_court": bool(midi["court"]) if midi else False,
            "soir": soir["titre"] if soir else "",
            "soir_court": bool(soir["court"]) if soir else False,
        })
    return jours


def enregistrer_menu(conn, jour: str, moment: str, titre: str, court: bool) -> None:
    titre = titre.strip()
    if not titre:
        conn.execute("DELETE FROM menus WHERE jour = ? AND moment = ?", (jour, moment))
        return
    conn.execute(
        """
        INSERT INTO menus (jour, moment, titre, court) VALUES (?, ?, ?, ?)
        ON CONFLICT(jour, moment) DO UPDATE SET titre = excluded.titre, court = excluded.court
        """,
        (jour, moment, titre, int(court)),
    )


def menu_du_jour(conn, aujourdhui: date | None = None) -> dict:
    aujourdhui = (aujourdhui or date.today()).isoformat()
    resultat = {"midi": "", "soir": "", "midi_court": False, "soir_court": False}
    for row in conn.execute("SELECT * FROM menus WHERE jour = ?", (aujourdhui,)):
        resultat[row["moment"]] = row["titre"]
        resultat[f"{row['moment']}_court"] = bool(row["court"])
    return resultat


def charger_exemple(conn) -> None:
    from maison.produits import creer as creer_produit

    if conn.execute("SELECT COUNT(*) AS n FROM personnes").fetchone()["n"]:
        raise ValueError("La maison a déjà des données")
    if conn.execute("SELECT COUNT(*) AS n FROM produits").fetchone()["n"]:
        raise ValueError("La maison a déjà des données")
    creer_personne(conn, "Camille")
    creer_personne(conn, "Jordan")
    lieux = {row["nom"]: row["id"] for row in lister_lieux(conn)}
    creer_produit(conn, {
        "nom": "Lait demi-écrémé", "categorie": "cuisine", "lieu_id": lieux.get("Frigo"),
        "quantite": 1, "etat": "bientot_fini", "rayon": "Frais", "magasin": "Supermarché",
    })
    creer_produit(conn, {
        "nom": "Pâtes", "categorie": "cuisine", "lieu_id": lieux.get("Placard"),
        "quantite": 2, "etat": "y_en_a", "rayon": "Épicerie", "magasin": "Supermarché",
    })
    creer_produit(conn, {
        "nom": "Œufs", "categorie": "cuisine", "lieu_id": lieux.get("Frigo"),
        "quantite": 6, "etat": "y_en_a", "rayon": "Frais", "magasin": "Supermarché",
    })
    creer_produit(conn, {
        "nom": "Petits pois", "categorie": "congelo", "lieu_id": lieux.get("Congélateur"),
        "quantite": 1, "etat": "y_en_a", "rayon": "Surgelés", "date_limite": date.today().isoformat(),
    })
    creer_produit(conn, {
        "nom": "Doliprane", "categorie": "pharmacie", "lieu_id": lieux.get("Pharmacie"),
        "quantite": 1, "date_limite": (date.today() + timedelta(days=10)).isoformat(),
    })
    creer_produit(conn, {
        "nom": "Ampoules", "categorie": "consommable", "lieu_id": lieux.get("Étagère"),
        "quantite": 0, "etat": "plus", "rayon": "Maison",
    })
    creer_plante(conn, {"nom": "Basilic", "piece": "Cuisine", "intervalle_jours": 3})
    conn.execute(
        "UPDATE menage SET dernier_fait = ? WHERE piece = 'Salle de bain'",
        ((date.today() - timedelta(days=40)).isoformat(),),
    )
    creer_animal(conn, {
        "nom": "Minou", "espece": "Chat", "repas": "Croquettes matin et soir",
        "soin": "Vermifuge", "prochain_soin": (date.today() - timedelta(days=1)).isoformat(),
    })
    dans_trois = date.today() + timedelta(days=3)
    creer_date(conn, {"titre": "Anniversaire de Louis", "jour": dans_trois.day, "mois": dans_trois.month})
    nombre(1)
