"""Appels au garde-manger EverShelf. Le cerveau ne touche pas à son PHP."""

import os
from typing import Any

import httpx

from maison.erreurs import ErreurMaison
from maison.texte import mot_dans, plier

_LIEUX = {
    "frigo": "frigo",
    "refrigerateur": "frigo",
    "placard": "dispensa",
    "dispensa": "dispensa",
    "sec": "dispensa",
    "secs": "dispensa",
    "congelateur": "freezer",
    "congelo": "freezer",
    "freezer": "freezer",
    "reserve": "altro",
    "reserves": "altro",
    "garage": "altro",
    "autre": "altro",
    "altro": "altro",
}

_LIBELLES = {
    "frigo": "Frigo",
    "dispensa": "Placard",
    "freezer": "Congélateur",
    "altro": "Autre",
}


def url() -> str:
    return os.environ.get("EVERSHELF_URL", "http://127.0.0.1:8091").rstrip("/")


def lieu_code(nom: str | None) -> str:
    """Le français de la maison vers les quatre endroits d'EverShelf."""
    if not nom:
        return "dispensa"
    plie = plier(nom)
    for mot, code in _LIEUX.items():
        if mot in plie:
            return code
    return "dispensa"


def libelle_lieu(code: str) -> str:
    return _LIBELLES.get(code, code)


def liste_courses() -> list[dict]:
    donnees = _action("shopping_list")
    lignes = []
    for item in donnees.get("purchase") or []:
        spec = item.get("specification") or ""
        lignes.append({
            "nom": item.get("name") or "",
            "nom_dit": item.get("rawName") or item.get("name") or "",
            "specification": spec,
        })
    return lignes


def ajouter_course(nom: str, specification: str = "") -> None:
    _action("shopping_add", {
        "items": [{
            "name": nom,
            "rawName": nom,
            "specification": specification,
            "update_spec": bool(specification),
        }],
    })


def retirer_course(nom: str) -> None:
    _action("shopping_remove", {"name": nom, "rawName": nom})


def inventaire() -> list[dict]:
    donnees = _action("inventory_list")
    return list(donnees.get("inventory") or [])


def ranger_produit(nom: str, quantite: float, lieu: str) -> str:
    """Crée le produit s'il manque, puis ajoute la quantité à l'endroit dit."""
    enregistre = _action("product_save", {"name": nom, "unit": "pz", "category": "autre"})
    produit_id = int(enregistre.get("id") or 0)
    if not produit_id:
        raise ErreurMaison(f"EverShelf n'a pas enregistré {nom}.")
    code = lieu_code(lieu)
    _action("inventory_add", {
        "product_id": produit_id,
        "quantity": quantite if quantite > 0 else 1,
        "location": code,
    })
    return code


def trouver(nom: str) -> dict | None:
    if not nom.strip():
        return None
    for ligne in inventaire():
        if mot_dans(nom, ligne.get("name") or "") or mot_dans(plier(nom), plier(ligne.get("name") or "")):
            return ligne
    return None


def _action(action: str, corps: dict | None = None) -> dict[str, Any]:
    try:
        if corps is None:
            reponse = httpx.get(f"{url()}/api/index.php", params={"action": action}, timeout=20)
        else:
            reponse = httpx.post(
                f"{url()}/api/index.php",
                params={"action": action},
                json=corps,
                timeout=20,
            )
    except httpx.HTTPError as exc:
        raise ErreurMaison("Le garde-manger EverShelf ne répond pas.") from exc
    if reponse.status_code >= 400:
        raise ErreurMaison("EverShelf a refusé l'action.")
    try:
        donnees = reponse.json()
    except ValueError as exc:
        raise ErreurMaison("EverShelf a répondu dans un format inattendu.") from exc
    if isinstance(donnees, dict) and donnees.get("success") is False:
        raise ErreurMaison(str(donnees.get("error") or "EverShelf a refusé l'action."))
    return donnees if isinstance(donnees, dict) else {}
