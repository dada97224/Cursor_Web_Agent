"""Un tour de parole : transcription déjà faite, décision, puis EverShelf.

Même tuyau pour le clavier et le micro. Ollama décide s'il est là.
Sinon la lecture française locale produit le même bloc d'intention.
"""

import httpx

from cerveau import ollama
from cerveau.executer import executer, resoudre_attente
from cerveau.meta import MetaIllisible, extraire_meta
from cerveau.repli import comprendre
from maison.assistant import _noter, histoires
from maison.erreurs import ErreurMaison


def discuter(conn, texte: str, auteur: str = "") -> str:
    reponse = tour(conn, texte)
    _noter(conn, auteur or "Quelqu'un", "personne", texte.strip())
    _noter(conn, "Jarvis", "maison", reponse)
    return reponse


def tour(conn, texte: str) -> str:
    brut = texte.strip()
    if not brut:
        return "Dis-moi un truc, ou envoie une photo."
    suite = resoudre_attente(conn, brut)
    if suite:
        return suite
    meta = _decider(conn, brut)
    return executer(conn, meta)


def _decider(conn, texte: str):
    if ollama.disponible():
        try:
            brut = ollama.completer(texte, histoires(conn))
            _visible, meta = extraire_meta(brut)
            return meta
        except (MetaIllisible, ErreurMaison, httpx.HTTPError):
            # Un modèle muet ou mal formé ne bloque pas la maison.
            return comprendre(texte)
    return comprendre(texte)


def memoires():
    """Réexport pour les routes qui relisent le fil."""
    return histoires
