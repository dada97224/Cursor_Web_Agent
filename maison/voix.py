"""Transcription locale. Le navigateur envoie le son, Whisper le passe en texte."""

import array
import logging
import os
import subprocess
import wave
from pathlib import Path

from maison.erreurs import ErreurMaison

log = logging.getLogger(__name__)
_modele = None

# Whisper invente ces formules quand le micro n'a capté que du silence.
_VIDES = ("sous-titre", "amara.org", "merci d'avoir regard", "thanks for watching")


def _modele_whisper():
    global _modele
    if _modele is not None:
        return _modele
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ErreurMaison(
            "Le modèle de transcription n'est pas installé. Lance : pip install faster-whisper"
        ) from exc
    # « base » tient sur un PC de maison. MAISON_WHISPER=small entend mieux le français.
    nom = os.environ.get("MAISON_WHISPER", "base")
    log.info("Chargement du modèle vocal %s", nom)
    _modele = WhisperModel(nom, device="cpu", compute_type="int8")
    return _modele


def preparer_wav(chemin: Path) -> tuple[Path, float, float]:
    """Le WebM du navigateur est souvent illisible tel quel. On le passe en WAV 16 kHz."""
    sortie = chemin.with_suffix(".16k.wav")
    commande = [
        "ffmpeg", "-y", "-i", str(chemin),
        "-ac", "1", "-ar", "16000",
        str(sortie),
    ]
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0 or not sortie.is_file():
        raise ErreurMaison("Le son enregistré n'a pas pu être lu. Réessaie en parlant après l'appui.")
    with wave.open(str(sortie)) as fichier:
        frames = fichier.readframes(fichier.getnframes())
        duree = fichier.getnframes() / float(fichier.getframerate() or 1)
    if not frames:
        return sortie, 0.0, 0.0
    echantillons = array.array("h")
    echantillons.frombytes(frames[: len(frames) - (len(frames) % 2)])
    if not echantillons:
        return sortie, duree, 0.0
    energie = (sum(valeur * valeur for valeur in echantillons) / len(echantillons)) ** 0.5
    return sortie, duree, energie


def _texte_utile(texte: str) -> str:
    propre = texte.strip()
    if not propre:
        return ""
    compare = propre.lower()
    if any(vide in compare for vide in _VIDES):
        return ""
    return propre


def transcrire(chemin: Path) -> str:
    wav, duree, energie = preparer_wav(chemin)
    if duree < 0.6:
        raise ErreurMaison("C'était trop court. Appuie, parle, puis appuie encore pour envoyer.")
    if energie < 80:
        raise ErreurMaison("Le micro n'a presque rien capté. Vérifie qu'il n'est pas muet, puis reparle.")
    try:
        # Pas de filtre VAD : il jetait les prises de voix un peu faibles.
        segments, _info = _modele_whisper().transcribe(
            str(wav),
            language="fr",
            vad_filter=False,
            beam_size=5,
            condition_on_previous_text=False,
        )
        return _texte_utile(" ".join(segment.text.strip() for segment in segments))
    except ErreurMaison:
        raise
    except Exception as exc:
        log.exception("Transcription impossible")
        raise ErreurMaison("Je n'ai pas réussi à transcrire. Réessaie en parlant un peu plus près.") from exc
