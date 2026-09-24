"""Photos ramenées à une taille confortable pour le téléphone."""

import uuid
from io import BytesIO

from maison import config
from maison.erreurs import ErreurMaison


def enregistrer_image(contenu: bytes) -> str:
    if len(contenu) > 8 * 1024 * 1024:
        raise ErreurMaison("La photo est trop lourde")
    try:
        from PIL import Image, ImageOps

        image = ImageOps.exif_transpose(Image.open(BytesIO(contenu)))
        image = image.convert("RGB")
        image.thumbnail((1600, 1600))
    except Exception as exc:
        raise ErreurMaison("Cette photo n'a pas pu être lue") from exc
    nom = f"{uuid.uuid4().hex}.jpg"
    config.chemin_uploads().mkdir(parents=True, exist_ok=True)
    image.save(config.chemin_uploads() / nom, "JPEG", quality=85)
    return nom


def url_media(nom: str | None) -> str | None:
    if not nom:
        return None
    if nom.startswith("/media/"):
        return nom
    return f"/media/{nom}"
