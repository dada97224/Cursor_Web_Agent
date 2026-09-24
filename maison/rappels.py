"""Ce qui doit apparaître sur l'accueil aujourd'hui."""

from datetime import date, timedelta

from maison.foyer import lister_animaux, lister_dates, lister_menage, lister_plantes, menu_du_jour
from maison.produits import lister as lister_produits
from maison.repas import idees


def _jours_depuis(valeur: str | None, aujourdhui: date) -> int | None:
    if not valeur:
        return None
    try:
        return (aujourdhui - date.fromisoformat(valeur[:10])).days
    except ValueError:
        return None


def rappels(conn, aujourdhui: date | None = None) -> list[dict]:
    aujourdhui = aujourdhui or date.today()
    elements: list[dict] = []
    for produit in lister_produits(conn):
        if produit["alerte"] == "depasse":
            elements.append({
                "titre": f"{produit['nom']} est périmé",
                "detail": produit["lieu_libelle"] or "À vérifier",
                "lien": "#/pharmacie" if produit["categorie"] == "pharmacie" else "#/cuisine",
                "urgent": True,
            })
        elif produit["alerte"] == "bientot" and produit["categorie"] == "pharmacie":
            elements.append({
                "titre": f"{produit['nom']} bientôt périmé",
                "detail": produit["date_limite"],
                "lien": "#/pharmacie",
                "urgent": True,
            })
        elif produit["alerte"] == "ancien":
            elements.append({
                "titre": f"{produit['nom']} est au congélateur depuis longtemps",
                "detail": produit["lieu_libelle"],
                "lien": "#/cuisine",
                "urgent": False,
            })
        elif produit["etat"] == "plus":
            elements.append({
                "titre": f"Plus de {produit['nom']}",
                "detail": "À remettre sur la liste",
                "lien": "#/courses",
                "urgent": False,
            })
        elif produit["etat"] == "bientot_fini":
            elements.append({
                "titre": f"Bientôt plus de {produit['nom']}",
                "detail": produit["lieu_libelle"],
                "lien": "#/courses",
                "urgent": False,
            })

    for plante in lister_plantes(conn):
        passe = _jours_depuis(plante["dernier_arrosage"], aujourdhui)
        if passe is None or passe >= plante["intervalle_jours"]:
            detail = plante["piece"] or "Plante"
            if passe is None:
                detail += " · pas encore arrosée"
            else:
                detail += f" · il y a {passe} jour{'s' if passe > 1 else ''}"
            elements.append({
                "titre": f"Arroser {plante['nom']}",
                "detail": detail,
                "lien": "#/plantes",
                "urgent": False,
            })

    for tache in lister_menage(conn):
        passe = _jours_depuis(tache["dernier_fait"], aujourdhui)
        if passe is None or passe >= tache["frequence_jours"]:
            elements.append({
                "titre": f"Ménage : {tache['piece']}",
                "detail": "Pas fait récemment" if passe is None else f"Il y a {passe} jours",
                "lien": "#/menage",
                "urgent": False,
            })

    for animal in lister_animaux(conn):
        if not animal["prochain_soin"]:
            continue
        try:
            soin = date.fromisoformat(animal["prochain_soin"][:10])
        except ValueError:
            continue
        if soin <= aujourdhui + timedelta(days=2):
            elements.append({
                "titre": f"{animal['nom']} : {animal['soin'] or 'soin'}",
                "detail": "Aujourd'hui" if soin == aujourdhui else animal["prochain_soin"],
                "lien": "#/animaux",
                "urgent": soin <= aujourdhui,
            })

    for evenement in lister_dates(conn):
        if evenement["dans"] <= 14:
            quand = "Aujourd'hui" if evenement["dans"] == 0 else f"Dans {evenement['dans']} jours"
            elements.append({
                "titre": evenement["titre"],
                "detail": quand,
                "lien": "#/dates",
                "urgent": evenement["dans"] <= 1,
            })

    elements.sort(key=lambda item: not item["urgent"])
    return elements[:6]


def accueil(conn) -> dict:
    noms = [
        produit["nom"]
        for produit in lister_produits(conn)
        if produit["etat"] != "plus" and float(produit["quantite"]) > 0 and produit["categorie"] in {"cuisine", "congelo"}
    ]
    return {
        "rappels": rappels(conn),
        "idees": idees(noms),
        "menu": menu_du_jour(conn),
    }
