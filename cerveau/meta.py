"""Le modèle termine sa réponse par un bloc <meta>, comme le routeur de Copain.

Le texte visible est pour la personne. Le JSON dit quelle action lancer.
Un bloc invalide ne casse pas le tour : l'appelant retombe sur la lecture locale.
"""

import json
import re
from typing import Any, Literal, TypedDict

Intent = Literal[
    "courses_ajouter",
    "courses_ranger",
    "stock_ou",
    "stock_ranger",
    "stock_manque",
    "recette",
    "repondre",
]

INTENTS: frozenset[str] = frozenset({
    "courses_ajouter",
    "courses_ranger",
    "stock_ou",
    "stock_ranger",
    "stock_manque",
    "recette",
    "repondre",
})

_BLOC = re.compile(r"<meta>\s*(\{.*?\})\s*</meta>", re.DOTALL)


class Article(TypedDict):
    nom: str
    quantite: float | None
    unite: str | None
    lieu: str | None
    question: str | None
    suppose: str | None


class Meta(TypedDict):
    intent: Intent
    articles: list[Article]
    texte: str | None


class MetaIllisible(ValueError):
    """Le modèle n'a pas rendu un bloc exploitable."""


def extraire_meta(brut: str) -> tuple[str, Meta]:
    """Sépare la phrase dite à voix haute du JSON d'action."""
    trouve = _BLOC.search(brut)
    if not trouve:
        raise MetaIllisible("Bloc <meta> absent")
    try:
        donnees = json.loads(trouve.group(1))
    except json.JSONDecodeError as exc:
        raise MetaIllisible("JSON illisible") from exc
    meta = valider(donnees)
    visible = _BLOC.sub("", brut).strip()
    return visible, meta


def valider(donnees: Any) -> Meta:
    if not isinstance(donnees, dict):
        raise MetaIllisible("Le bloc doit être un objet")
    intent = donnees.get("intent")
    if intent not in INTENTS:
        raise MetaIllisible(f"intent inconnu : {intent!r}")
    articles_bruts = donnees.get("articles") or []
    if not isinstance(articles_bruts, list):
        raise MetaIllisible("articles doit être une liste")
    articles = [_article(item) for item in articles_bruts]
    texte = donnees.get("texte")
    if texte is not None and not isinstance(texte, str):
        raise MetaIllisible("texte doit être une chaîne")
    return {"intent": intent, "articles": articles, "texte": texte}


def _article(item: Any) -> Article:
    if not isinstance(item, dict):
        raise MetaIllisible("Chaque article doit être un objet")
    nom = item.get("nom")
    if not isinstance(nom, str) or not nom.strip():
        raise MetaIllisible("Chaque article a un nom")
    return {
        "nom": nom.strip(),
        "quantite": _nombre(item.get("quantite")),
        "unite": _chaine(item.get("unite")),
        "lieu": _chaine(item.get("lieu")),
        "question": _chaine(item.get("question")),
        "suppose": _chaine(item.get("suppose")),
    }


def _chaine(valeur: Any) -> str | None:
    if valeur is None:
        return None
    if not isinstance(valeur, str):
        raise MetaIllisible("Champ texte invalide dans un article")
    propre = valeur.strip()
    return propre or None


def _nombre(valeur: Any) -> float | None:
    if valeur is None or valeur == "":
        return None
    if isinstance(valeur, bool):
        raise MetaIllisible("La quantité n'est pas un booléen")
    if isinstance(valeur, int | float):
        return float(valeur)
    if isinstance(valeur, str):
        try:
            return float(valeur.replace(",", "."))
        except ValueError as exc:
            raise MetaIllisible("Quantité illisible") from exc
    raise MetaIllisible("Quantité illisible")
