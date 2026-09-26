"""Normalisation des noms et dates affichées."""

import re
import unicodedata
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def maintenant_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def plier(texte: str) -> str:
    brut = texte.lower().replace("œ", "oe").replace("æ", "ae")
    decompose = unicodedata.normalize("NFD", brut)
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def jetons(texte: str) -> list[str]:
    return [j for j in re.split(r"[^a-z0-9]+", plier(texte)) if len(j) >= 3]


def equivalent(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) < 3 or len(b) < 3:
        return False
    court, long = (a, b) if len(a) <= len(b) else (b, a)
    return long.startswith(court) and long[len(court):] in {"s", "x", "es"}


def mot_dans(mot: str, nom: str) -> bool:
    attendus = jetons(mot)
    connus = jetons(nom)
    if not attendus:
        return False
    position = 0
    for attendu in attendus:
        trouve = False
        while position < len(connus):
            if equivalent(connus[position], attendu):
                position += 1
                trouve = True
                break
            position += 1
        if not trouve:
            return False
    return True


def score_noms(a: str, b: str) -> float:
    if plier(a).strip() == plier(b).strip():
        return 1.0
    ja, jb = jetons(a), jetons(b)
    if ja and jb:
        court, long = (ja, jb) if len(ja) <= len(jb) else (jb, ja)
        if all(any(equivalent(token, autre) for autre in long) for token in court):
            return 0.9
    return SequenceMatcher(None, plier(a), plier(b)).ratio()


def presenter_nom(nom: str) -> str:
    petits = {"de", "du", "des", "et", "la", "le", "les"}
    mots = nom.split()
    return " ".join(
        mot if index and mot.lower() in petits else mot.capitalize()
        for index, mot in enumerate(mots)
    )


def nombre(valeur: float) -> int | float:
    if valeur == int(valeur):
        return int(valeur)
    return valeur


def libelle_jour(jour: date) -> str:
    return f"{JOURS[jour.weekday()].capitalize()} {jour.day} {MOIS[jour.month - 1]}"


def prochaine_date(jour: int, mois: int, aujourdhui: date | None = None) -> date:
    aujourdhui = aujourdhui or date.today()
    annee = aujourdhui.year
    for decalage in (0, 1):
        try:
            candidate = date(annee + decalage, mois, jour)
        except ValueError:
            candidate = date(annee + decalage, mois, 28)
        if candidate >= aujourdhui:
            return candidate
    return aujourdhui + timedelta(days=365)
