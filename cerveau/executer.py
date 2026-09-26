"""Exécute la décision du modèle sur EverShelf. Le modèle ne parle pas à la base."""

import json
import re
from typing import assert_never

from cerveau import etageres
from cerveau.meta import Article, Intent, Meta
from maison.repas import formuler_recette
from maison.texte import plier

_NOMBRE = re.compile(r"(\d+)")


def executer(conn, meta: Meta) -> str:
    intent: Intent = meta["intent"]
    if intent == "courses_ajouter":
        return _courses_ajouter(conn, meta["articles"])
    if intent == "courses_ranger":
        return _courses_ranger()
    if intent == "stock_ou":
        return _stock_ou(meta["articles"])
    if intent == "stock_ranger":
        return _stock_ranger(meta["articles"])
    if intent == "stock_manque":
        return _stock_manque(meta["articles"])
    if intent == "recette":
        return _recette()
    if intent == "repondre":
        return meta["texte"] or "Dis-moi ce qu'il faut acheter, où tu as rangé quelque chose, ou ce qu'on peut manger."
    assert_never(intent)


def resoudre_attente(conn, texte: str) -> str | None:
    """Une réponse courte (« 12 ») termine la question laissée ouverte."""
    attente = _lire(conn)
    if not attente:
        return None
    trouve = _NOMBRE.search(texte)
    if not trouve:
        return None
    quantite = float(trouve.group(1))
    if attente.get("choix") and int(quantite) not in attente["choix"]:
        return attente.get("question") or "Je n'ai pas ce choix."
    nom = attente["nom"]
    etageres.ajouter_course(nom, _specification(quantite, attente.get("unite")))
    _ecrire(conn, None)
    return f"{nom}, {int(quantite)}, c'est noté sur la liste."


def _courses_ajouter(conn, articles: list[Article]) -> str:
    if not articles:
        return "Dis-moi le nom de ce qu'il faut ajouter à la liste."
    phrases: list[str] = []
    poses: list[str] = []
    question: Article | None = None
    for article in articles:
        if not article["nom"]:
            continue
        if article["question"] and article["quantite"] is None:
            question = article
            continue
        spec = _specification(article["quantite"], article["unite"])
        etageres.ajouter_course(article["nom"], spec)
        if article["suppose"]:
            poses.append(article["suppose"])
        elif article["unite"] == "paquet":
            poses.append(f"{article['nom'].lower()} ajouté")
        else:
            poses.append(_parle(article))
    if poses:
        phrases.append("OK, " + ", ".join(poses) + ".")
    if question:
        _ecrire(conn, {
            "nom": question["nom"],
            "unite": question["unite"],
            "question": question["question"],
            "choix": [6, 12, 24] if "oeuf" in plier(question["nom"]) or "œuf" in question["nom"].lower() else [],
        })
        if question["question"]:
            phrases.append(question["question"])
    if not phrases:
        return "Je n'ai rien ajouté. Précise le produit."
    return " ".join(phrases)


def _courses_ranger() -> str:
    lignes = etageres.liste_courses()
    if not lignes:
        return "La liste des courses est déjà vide."
    faits = []
    for ligne in lignes:
        nom = ligne["nom_dit"] or ligne["nom"]
        quantite = _quantite_spec(ligne["specification"])
        code = etageres.ranger_produit(nom, quantite, _lieu_devine(nom))
        etageres.retirer_course(ligne["nom"])
        if ligne["nom_dit"] and plier(ligne["nom_dit"]) != plier(ligne["nom"]):
            etageres.retirer_course(ligne["nom_dit"])
        faits.append(f"{nom} ({etageres.libelle_lieu(code)})")
    return "Stock actualisé : " + ", ".join(faits) + "."


def _stock_ou(articles: list[Article]) -> str:
    nom = articles[0]["nom"] if articles else ""
    if not nom:
        return "De quoi tu parles ?"
    trouve = etageres.trouver(nom)
    if not trouve:
        return f"Je ne connais pas encore {nom} dans le garde-manger."
    return f"{trouve.get('name') or nom} est dans le {etageres.libelle_lieu(trouve.get('location') or '')}."


def _stock_ranger(articles: list[Article]) -> str:
    if not articles or not articles[0]["nom"]:
        return "Dis-moi quoi, et où."
    article = articles[0]
    quantite = article["quantite"] or 1
    code = etageres.ranger_produit(article["nom"], quantite, article["lieu"])
    return f"{article['nom']} est dans le {etageres.libelle_lieu(code)}."


def _stock_manque(articles: list[Article]) -> str:
    if not articles or not articles[0]["nom"]:
        return "Il manque quoi ?"
    nom = articles[0]["nom"]
    etageres.ajouter_course(nom, "")
    return f"Plus de {nom.lower()}. Je le mets sur la liste."


def _recette() -> str:
    noms = [ligne.get("name") or "" for ligne in etageres.inventaire()]
    return formuler_recette([nom for nom in noms if nom])


def _parle(article: Article) -> str:
    if article["unite"] == "pack":
        return f"un pack de {article['nom'].lower()}"
    if article["unite"] == "paquet":
        return f"un paquet de {article['nom'].lower()}"
    if article["quantite"] and article["quantite"] != 1:
        return f"{int(article['quantite'])} {article['nom'].lower()}"
    return article["nom"].lower()


def _specification(quantite: float | None, unite: str | None) -> str:
    if quantite and unite:
        nombre = int(quantite) if quantite == int(quantite) else quantite
        return f"{nombre} {unite}"
    if unite:
        return unite
    if quantite and quantite != 1:
        nombre = int(quantite) if quantite == int(quantite) else quantite
        return str(nombre)
    return ""


def _quantite_spec(specification: str) -> float:
    trouve = _NOMBRE.search(specification or "")
    if not trouve:
        return 1
    return float(trouve.group(1))


def _lieu_devine(nom: str) -> str:
    plie = plier(nom)
    if any(mot in plie for mot in ("lait", "oeuf", "œuf", "yaourt", "fromage", "coca", "jambon", "beurre")):
        return "frigo"
    if any(mot in plie for mot in ("surgele", "glace", "pizza")):
        return "freezer"
    return "placard"


def _lire(conn) -> dict | None:
    row = conn.execute("SELECT contenu FROM attente WHERE id = 1").fetchone()
    if not row:
        return None
    return json.loads(row["contenu"])


def _ecrire(conn, contenu: dict | None) -> None:
    if not contenu:
        conn.execute("DELETE FROM attente WHERE id = 1")
        return
    conn.execute(
        "INSERT INTO attente (id, contenu) VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET contenu = excluded.contenu",
        (json.dumps(contenu, ensure_ascii=False),),
    )
