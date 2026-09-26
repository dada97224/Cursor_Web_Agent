"""Démarre le PHP d'EverShelf à côté de Jarvis, sur le port interne."""

import os
import subprocess
import time
from pathlib import Path

import httpx

RACINE = Path(__file__).resolve().parent.parent / "evershelf"
_processus: subprocess.Popen | None = None


def port() -> int:
    return int(os.environ.get("EVERSHELF_PORT", "8091"))


def preparer_base() -> None:
    """Les tests repartent d'un garde-manger vide. La maison, elle, garde ses données."""
    if os.environ.get("MAISON_TEST") != "1":
        return
    dossier = RACINE / "data"
    dossier.mkdir(parents=True, exist_ok=True)
    for chemin in dossier.glob("evershelf.db*"):
        chemin.unlink(missing_ok=True)


def demarrer() -> subprocess.Popen | None:
    """Lance php -S si EverShelf n'écoute pas déjà."""
    global _processus
    if os.environ.get("EVERSHELF_EXTERNE") == "1":
        return None
    adresse = f"http://127.0.0.1:{port()}/"
    if _repond(adresse):
        return _processus
    preparer_base()
    _assurer_env()
    (RACINE / "data").mkdir(parents=True, exist_ok=True)
    _processus = subprocess.Popen(
        ["php", "-S", f"127.0.0.1:{port()}", "-t", str(RACINE)],
        cwd=RACINE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        if _repond(adresse):
            return _processus
        if _processus.poll() is not None:
            break
        time.sleep(0.1)
    return _processus


def arreter() -> None:
    global _processus
    if _processus is None or _processus.poll() is not None:
        _processus = None
        return
    _processus.terminate()
    try:
        _processus.wait(timeout=3)
    except subprocess.TimeoutExpired:
        _processus.kill()
    _processus = None


def _assurer_env() -> None:
    """EverShelf ignore son .env. On en pose un local, sans clé cloud."""
    cible = RACINE / ".env"
    if cible.exists():
        return
    cible.write_text(
        "AI_ENABLED=false\n"
        "AI_PROVIDER=llama\n"
        "LLAMA_BASE_URL=http://127.0.0.1:11434/v1\n"
        "LLAMA_MODEL=llama3.2\n"
        "SHOPPING_MODE=internal\n"
        "TTS_ENABLED=false\n",
        encoding="utf-8",
    )


def _repond(adresse: str) -> bool:
    try:
        httpx.get(adresse, timeout=0.3)
    except httpx.HTTPError:
        return False
    return True
