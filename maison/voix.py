"""Transcription locale. Le navigateur envoie le son, Whisper le passe en texte."""

import logging
import os
from pathlib import Path

from maison.erreurs import ErreurMaison

log = logging.getLogger(__name__)
_modele = None


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


def transcrire(chemin: Path) -> str:
    try:
        segments, _info = _modele_whisper().transcribe(
            str(chemin),
            language="fr",
            vad_filter=True,
            beam_size=5,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()
    except ErreurMaison:
        raise
    except Exception as exc:
        log.exception("Transcription impossible")
        raise ErreurMaison("Je n'ai pas réussi à transcrire. Réessaie en parlant un peu plus près.") from exc
