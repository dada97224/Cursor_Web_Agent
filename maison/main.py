"""Lancement de l'application sur le réseau de la maison."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from maison import config
from maison.api import routeur
from maison.db import initialiser
from maison.erreurs import ErreurMaison

WEB = Path(__file__).resolve().parent.parent / "web"


def creer_application() -> FastAPI:
    initialiser()
    app = FastAPI(title="Maison")
    app.include_router(routeur)

    @app.exception_handler(ErreurMaison)
    async def _erreur_maison(_, exc: ErreurMaison):
        return JSONResponse({"detail": exc.message}, status_code=exc.statut)

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html")

    @app.get("/sw.js")
    def service_worker():
        return FileResponse(WEB / "sw.js", media_type="application/javascript")

    @app.get("/manifest.webmanifest")
    def manifeste():
        return FileResponse(WEB / "manifest.webmanifest", media_type="application/manifest+json")

    app.mount("/js", StaticFiles(directory=WEB / "js"), name="js")
    app.mount("/css", StaticFiles(directory=WEB / "css"), name="css")
    app.mount("/icones", StaticFiles(directory=WEB / "icones"), name="icones")

    @app.get("/media/{nom}")
    def media(nom: str):
        if "/" in nom or ".." in nom or not nom.endswith(".jpg"):
            raise HTTPException(400, "Fichier refusé")
        chemin = config.chemin_uploads() / nom
        if not chemin.is_file():
            raise HTTPException(404, "Photo introuvable")
        return FileResponse(chemin)

    return app


def servir() -> None:
    import uvicorn

    uvicorn.run(
        "maison.main:creer_application",
        factory=True,
        host=config.hote(),
        port=config.port(),
    )
