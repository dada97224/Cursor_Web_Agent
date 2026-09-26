"""Lecture d'un ticket ou d'un code-barres à partir d'une photo."""

import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Lignes de caisse qui ne sont pas des produits.
_IGNORER = re.compile(
    r"\b(total|sous-total|tva|especes|cb|carte|visa|mastercard|rendu|monnaie|"
    r"merci|caissier|caisse|ticket|siret|avoir|remise|fideli)\b",
    re.I,
)
_PRIX = re.compile(r"(\d+[,.]\d{2})")
_PRIX_SEUL = re.compile(r"^\d+[,.]\d{2}$")
_QUANTITE = re.compile(r"^(?P<qte>\d+)\s*[x×]\s+(?P<reste>.+)$", re.I)


def lire_image(chemin: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""
    try:
        # psm 4 : un ticket est lu ligne par ligne, prix compris.
        return pytesseract.image_to_string(Image.open(chemin), lang="fra", config="--psm 4") or ""
    except Exception:
        log.info("Lecture du ticket impossible, saisie manuelle.")
        return ""


def lire_codes(chemin: Path) -> list[dict]:
    """Codes-barres et QR codes. ZBar lit les deux sur une photo."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
    except ImportError:
        return []
    try:
        trouves = decode(Image.open(chemin))
    except Exception:
        log.info("Lecture des codes impossible.")
        return []
    codes = []
    for code in trouves:
        valeur = code.data.decode("utf-8", errors="ignore").strip()
        if valeur:
            codes.append({"type": code.type, "valeur": valeur})
    return codes


def lire_code_barres(chemin: Path) -> str:
    codes = lire_codes(chemin)
    return codes[0]["valeur"] if codes else ""


def extraire_lignes(texte: str) -> list[dict]:
    brutes = [ligne.strip() for ligne in texte.splitlines() if ligne.strip()]
    fusionnees: list[str] = []
    index = 0
    while index < len(brutes):
        courante = brutes[index]
        suivante = brutes[index + 1] if index + 1 < len(brutes) else ""
        if suivante and _PRIX_SEUL.match(suivante) and not _PRIX.search(courante):
            fusionnees.append(f"{courante} {suivante}")
            index += 2
        else:
            fusionnees.append(courante)
            index += 1

    lignes: list[dict] = []
    for brute in fusionnees:
        prix = _PRIX.search(brute)
        if not prix:
            continue
        nom = brute[: prix.start()].strip(" .-*")
        quantite = 1.0
        qte = _QUANTITE.match(nom)
        if qte:
            quantite = float(qte.group("qte"))
            nom = qte.group("reste").strip()
        if len(nom) < 3 or _IGNORER.search(nom) or _IGNORER.search(brute):
            continue
        if not re.search(r"[A-Za-zÀ-ÿ]", nom):
            continue
        lignes.append({"nom": nom, "quantite": quantite})
    return lignes
