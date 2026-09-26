"""Chemins et port lus au moment de l'appel, pour les tests."""

import os
import socket
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def chemin_base() -> Path:
    return Path(os.environ.get("MAISON_DB", RACINE / "data" / "maison.sqlite"))


def chemin_uploads() -> Path:
    return Path(os.environ.get("MAISON_UPLOADS", RACINE / "data" / "uploads"))


def hote() -> str:
    return os.environ.get("MAISON_HOTE", "0.0.0.0")


def port() -> int:
    return int(os.environ.get("MAISON_PORT", "8080"))


def ip_locale() -> str:
    # UDP sans envoi réel : suffit à connaître l'adresse du Wi-Fi de la maison.
    sonde = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sonde.connect(("192.168.1.1", 80))
        return sonde.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sonde.close()
