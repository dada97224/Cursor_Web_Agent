"""Lancement de l'application sur le réseau de la maison."""

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from cerveau.lancer import arreter, demarrer, port
from maison import config
from maison.api import routeur
from maison.db import initialiser
from maison.erreurs import ErreurMaison

WEB = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def vie(_app: FastAPI):
    # EverShelf (PHP) tient le stock. Jarvis lui parle en HTTP.
    demarrer()
    try:
        yield
    finally:
        arreter()


def creer_application() -> FastAPI:
    initialiser()
    app = FastAPI(title="Maison", lifespan=vie)
    app.include_router(routeur)

    @app.exception_handler(ErreurMaison)
    async def _erreur_maison(_, exc: ErreurMaison):
        return JSONResponse({"detail": exc.message}, status_code=exc.statut)

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html")

    @app.get("/garde-manger")
    def garde_manger_racine():
        return RedirectResponse("/garde-manger/")

    @app.api_route(
        "/garde-manger/{chemin:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    async def garde_manger(chemin: str, request: Request):
        """Le garde-manger EverShelf, sur la même adresse que Jarvis."""
        cible = f"http://127.0.0.1:{port()}/{chemin}"
        if request.url.query:
            cible = f"{cible}?{request.url.query}"
        entetes = {}
        if request.headers.get("content-type"):
            entetes["content-type"] = request.headers["content-type"]
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                amont = await client.request(
                    request.method,
                    cible,
                    content=await request.body(),
                    headers=entetes,
                )
        except httpx.HTTPError as exc:
            raise HTTPException(502, "Le garde-manger ne répond pas") from exc
        return Response(
            content=amont.content,
            status_code=amont.status_code,
            media_type=amont.headers.get("content-type"),
        )

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
