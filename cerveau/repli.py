"""Lecture française de secours quand Ollama est éteint.

Même forme de décision que le modèle : un objet Meta, pas une phrase en dur
branchée sur la base. L'exécution reste dans executer.py.
"""

import re

from cerveau.meta import Article, Meta
from maison.texte import plier, presenter_nom

_ARTICLE = re.compile(r"\b(du|des|de la|de l'|d'|le|la|les|un|une)\b", re.I)
_LIEU = re.compile(r"\b(dans|sous|au|en)\s+(.+)$")


def comprendre(phrase: str) -> Meta:
    """Transforme une phrase française en intention structurée."""
    brut = phrase.strip()
    plie = plier(brut)
    if _veut_ranger_courses(plie):
        return _meta("courses_ranger", [])
    if any(mot in plie for mot in ("ou est", "ou sont", "ou j", "trouve")):
        return _meta("stock_ou", [_simple(_dernier_nom(brut))])
    if any(mot in plie for mot in ("range", "ranger", "mets ", "pose ")) and _LIEU.search(plie):
        lieu = _LIEU.search(plie)
        reste = plie[: lieu.start()] if lieu else plie
        return _meta("stock_ranger", [_simple(_dernier_nom(reste), _nettoyer_lieu(lieu.group(2) if lieu else ""))])
    if "plus de " in plie:
        reste = plie.split("plus de ", 1)[1]
        return _meta("stock_manque", [_simple(_ARTICLE.sub(" ", reste).strip())])
    if any(mot in plie for mot in ("plus d ", "n a plus", "na plus", "fini ", "epuise")):
        return _meta("stock_manque", [_simple(_dernier_nom(brut))])
    if any(mot in plie for mot in ("ajoute", "ajout", "acheter", "achete", "faut prendre", "pense a prendre")):
        return _meta("courses_ajouter", [_preciser(nom) for nom in _noms(brut)])
    if any(mot in plie for mot in ("mange", "recette", "cuisin", "ce soir")):
        return _meta("recette", [])
    return _meta("repondre", [], "Je n'ai pas saisi l'action. Dis-moi ce qu'il faut acheter, où tu as rangé quelque chose, ou ce qu'on peut manger.")


def _meta(intent: str, articles: list[Article], texte: str | None = None) -> Meta:
    return {"intent": intent, "articles": articles, "texte": texte}  # type: ignore[typeddict-item]


def _veut_ranger_courses(plie: str) -> bool:
    return "liste" in plie and "course" in plie and any(mot in plie for mot in ("range", "actualise", "stock"))


def _noms(fragment: str) -> list[str]:
    morceaux = re.split(r",|;|\bet\b", plier(fragment))
    resultat = []
    for morceau in morceaux:
        morceau = _ARTICLE.sub(" ", morceau)
        morceau = re.sub(
            r"\b(ajoute|ajout|ajouter|acheter|achete|faudrait|faut|il|prendre|pense|liste|courses|semaine|range|mets|pose|met|est|sont|ou|ramene|jai|ai|on|actualise|stock|dans|le|la|les)\b",
            " ",
            morceau,
        )
        morceau = re.sub(r"^(de|d)\s+", "", " ".join(morceau.split()))
        if len(morceau) >= 3:
            resultat.append(morceau)
    return resultat


def _dernier_nom(fragment: str) -> str:
    noms = _noms(fragment)
    return noms[-1] if noms else ""


def _nettoyer_lieu(lieu: str) -> str:
    return _ARTICLE.sub(" ", lieu).strip()


def _simple(nom: str, lieu: str | None = None) -> Article:
    return {
        "nom": presenter_nom(nom) if nom else "",
        "quantite": 1,
        "unite": None,
        "lieu": lieu or None,
        "question": None,
        "suppose": None,
    }


def _preciser(nom: str) -> Article:
    """Les quantités ambiguës deviennent une question, pas un chiffre inventé."""
    article = _simple(nom)
    plie = plier(nom)
    if "pain de mie" in plie:
        article["nom"] = "Pain de mie"
        article["unite"] = "paquet"
        return article
    if "oeuf" in plie:
        article["nom"] = "Œufs"
        article["quantite"] = None
        article["question"] = "Pour les œufs : 6, 12 ou 24 ?"
        return article
    if "coca" in plie:
        article["nom"] = "Coca"
        article["unite"] = "bouteille"
        article["suppose"] = "et le coca en 2 litres je suppose"
        return article
    if plie == "lait" or plie.startswith("lait "):
        article["nom"] = "Lait"
        article["unite"] = "pack"
        article["suppose"] = "un pack de lait"
        return article
    return article
