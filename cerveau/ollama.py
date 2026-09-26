"""Modèle local, dans l'esprit d'isair : rien ne sort de la maison.

Ollama parle le français et rend un bloc <meta>. S'il est éteint, le tour
continue avec la lecture locale, sans inventer une réponse cloud.
"""

import os

import httpx

from maison.erreurs import ErreurMaison

_PROMPT = """Tu es Jarvis, l'assistant de la maison. Tu parles français, simplement, pour tout le monde.
Tu ne remplis pas de formulaire : tu décides quoi faire dans le garde-manger EverShelf.

Réponds en une ou deux phrases, puis termine TOUJOURS par un bloc <meta> JSON sur une seule ligne, sans markdown.
Schéma :
{"intent":"courses_ajouter|courses_ranger|stock_ou|stock_ranger|stock_manque|recette|repondre","articles":[{"nom":"","quantite":null,"unite":null,"lieu":null,"question":null,"suppose":null}],"texte":null}

Règles :
- courses_ajouter : ajouter à la liste. Si la quantité n'est pas claire (œufs), mets question et quantite null, n'invente pas.
- Pour le lait, suppose un pack. Pour le coca, suppose une bouteille de 2 litres et dis-le.
- courses_ranger : la personne a rangé les courses et veut mettre à jour le stock.
- stock_ou : où est un objet. stock_ranger : elle l'a rangé quelque part (lieu : frigo, placard, congelateur, autre).
- stock_manque : il n'y en a plus. recette : quoi cuisiner avec le stock.
- repondre : seulement si aucune action ne convient. texte reprend ta phrase.
- Lieux acceptés dans lieu : frigo, placard, congelateur, autre.
"""


def _url() -> str:
    return os.environ.get("MAISON_OLLAMA", "http://127.0.0.1:11434").rstrip("/")


def _modele() -> str:
    return os.environ.get("MAISON_OLLAMA_MODELE", "llama3.2")


def disponible() -> bool:
    """Vrai si un Ollama répond. Les tests peuvent forcer l'absence."""
    if os.environ.get("MAISON_SANS_OLLAMA") == "1":
        return False
    try:
        reponse = httpx.get(f"{_url()}/api/tags", timeout=0.4)
    except httpx.HTTPError:
        return False
    return reponse.status_code == 200


def completer(texte: str, historique: list[dict]) -> str:
    """Envoie le tour au modèle local et renvoie le texte brut, bloc inclus."""
    messages = [{"role": "system", "content": _PROMPT}]
    for tour in historique[-6:]:
        role = "assistant" if tour["role"] == "maison" else "user"
        messages.append({"role": role, "content": tour["texte"]})
    messages.append({"role": "user", "content": texte})
    try:
        reponse = httpx.post(
            f"{_url()}/api/chat",
            json={"model": _modele(), "messages": messages, "stream": False},
            timeout=60,
        )
    except httpx.HTTPError as exc:
        raise ErreurMaison("Le modèle local ne répond pas.") from exc
    if reponse.status_code != 200:
        raise ErreurMaison("Le modèle local a refusé la phrase.")
    contenu = reponse.json().get("message", {}).get("content", "")
    if not isinstance(contenu, str) or not contenu.strip():
        raise ErreurMaison("Le modèle local n'a rien répondu.")
    return contenu
