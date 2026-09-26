"""Client HTTP isolé : base maison vide, garde-manger EverShelf vide, sans Ollama."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MAISON_DB", str(tmp_path / "maison.sqlite"))
    monkeypatch.setenv("MAISON_UPLOADS", str(tmp_path / "uploads"))
    monkeypatch.setenv("MAISON_SANS_OLLAMA", "1")
    monkeypatch.setenv("MAISON_TEST", "1")
    from cerveau.lancer import preparer_base
    from maison.main import creer_application

    preparer_base()
    with TestClient(creer_application()) as test:
        yield test
