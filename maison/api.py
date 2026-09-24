"""Routes JSON de la maison."""

from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from maison import config, courses, foyer, ocr, produits, rappels
from maison.db import ouvrir
from maison.erreurs import ErreurMaison
from maison.images import enregistrer_image, url_media
from maison.texte import maintenant_iso, presenter_nom

routeur = APIRouter(prefix="/api")


class ProduitCorps(BaseModel):
    nom: str
    categorie: str
    lieu_id: int | None = None
    quantite: float = 1
    unite: str = "pièce"
    etat: str = "y_en_a"
    date_limite: str | None = None
    magasin: str = ""
    rayon: str = ""
    code_barres: str = ""
    note: str = ""


class EtatCorps(BaseModel):
    etat: str


class PersonneCorps(BaseModel):
    nom: str


class LieuCorps(BaseModel):
    piece: str
    nom: str


class CourseCorps(BaseModel):
    nom: str
    quantite: float = 1
    magasin: str = ""
    rayon: str = ""
    unite: str = "pièce"
    personne_id: int | None = None


class CourseMaj(BaseModel):
    coche: bool | None = None
    quantite: float | None = None
    nom: str | None = None
    magasin: str | None = None
    rayon: str | None = None


class PlanteCorps(BaseModel):
    nom: str
    piece: str = ""
    intervalle_jours: int = 7


class MenageCorps(BaseModel):
    piece: str
    frequence_jours: int = 7


class FrequenceCorps(BaseModel):
    frequence_jours: int = Field(ge=1, le=365)


class AnimalCorps(BaseModel):
    nom: str
    espece: str = ""
    repas: str = ""
    soin: str = ""
    prochain_soin: str | None = None
    note: str = ""


class DateCorps(BaseModel):
    titre: str
    jour: int = Field(ge=1, le=31)
    mois: int = Field(ge=1, le=12)
    annee: int | None = None
    note: str = ""


class MenuLigne(BaseModel):
    jour: str
    moment: str
    titre: str = ""
    court: bool = False


class MenusCorps(BaseModel):
    lignes: list[MenuLigne]


class LigneTicket(BaseModel):
    nom: str
    quantite: float = 1
    categorie: str = "cuisine"
    lieu_id: int | None = None
    produit_id: int | None = None
    unite: str = "pièce"


class ActionPersonne(BaseModel):
    personne_id: int | None = None
    par: str = ""


def _verifier_categorie(categorie: str) -> None:
    if categorie not in produits.CATEGORIES:
        raise ErreurMaison("Choisis un type : cuisine, congélateur, pharmacie ou maison")


def _verifier_etat(etat: str) -> None:
    if etat not in produits.ETATS:
        raise ErreurMaison("État inconnu")


def _publier_produit(produit: dict | None) -> dict | None:
    if not produit:
        return None
    produit["photo"] = url_media(produit.get("photo"))
    return produit


def _nom_personne(conn, personne_id: int | None, par: str = "") -> str:
    if par:
        return par
    if not personne_id:
        return ""
    row = conn.execute("SELECT nom FROM personnes WHERE id = ?", (personne_id,)).fetchone()
    return row["nom"] if row else ""


@routeur.get("/reseau")
def reseau():
    return {"url": f"http://{config.ip_locale()}:{config.port()}", "port": config.port()}


@routeur.get("/accueil")
def accueil():
    with ouvrir() as conn:
        return rappels.accueil(conn)


@routeur.get("/personnes")
def personnes():
    with ouvrir() as conn:
        liste = foyer.lister_personnes(conn)
    for personne in liste:
        personne["photo"] = url_media(personne.get("photo"))
    return liste


@routeur.post("/personnes")
def creer_personne(corps: PersonneCorps):
    if not corps.nom.strip():
        raise ErreurMaison("Il faut un prénom")
    with ouvrir() as conn:
        personne = foyer.creer_personne(conn, corps.nom)
    personne["photo"] = None
    return personne


@routeur.delete("/personnes/{personne_id}")
def supprimer_personne(personne_id: int):
    with ouvrir() as conn:
        if not foyer.supprimer_personne(conn, personne_id):
            raise ErreurMaison("Personne introuvable", 404)
    return {"ok": True}


@routeur.get("/lieux")
def lieux():
    with ouvrir() as conn:
        return foyer.lister_lieux(conn)


@routeur.post("/lieux")
def creer_lieu(corps: LieuCorps):
    if not corps.piece.strip() or not corps.nom.strip():
        raise ErreurMaison("Indique la pièce et l'endroit")
    with ouvrir() as conn:
        return foyer.creer_lieu(conn, corps.piece, corps.nom)


@routeur.delete("/lieux/{lieu_id}")
def supprimer_lieu(lieu_id: int):
    with ouvrir() as conn:
        if not foyer.supprimer_lieu(conn, lieu_id):
            raise ErreurMaison("Endroit introuvable", 404)
    return {"ok": True}


@routeur.get("/produits")
def lister_produits(categorie: str | None = None):
    if categorie:
        _verifier_categorie(categorie)
    with ouvrir() as conn:
        return [_publier_produit(p) for p in produits.lister(conn, categorie)]


@routeur.get("/produits/{produit_id}")
def obtenir_produit(produit_id: int):
    with ouvrir() as conn:
        produit = _publier_produit(produits.obtenir(conn, produit_id))
    if not produit:
        raise ErreurMaison("Produit introuvable", 404)
    return produit


@routeur.post("/produits")
def creer_produit(corps: ProduitCorps):
    _verifier_categorie(corps.categorie)
    _verifier_etat(corps.etat)
    if not corps.nom.strip():
        raise ErreurMaison("Il faut un nom")
    with ouvrir() as conn:
        return _publier_produit(produits.creer(conn, corps.model_dump()))


@routeur.patch("/produits/{produit_id}")
def modifier_produit(produit_id: int, corps: ProduitCorps):
    _verifier_categorie(corps.categorie)
    _verifier_etat(corps.etat)
    champs = corps.model_dump()
    with ouvrir() as conn:
        produit = produits.modifier(conn, produit_id, champs)
    if not produit:
        raise ErreurMaison("Produit introuvable", 404)
    return _publier_produit(produit)


@routeur.post("/produits/{produit_id}/etat")
def definir_etat(produit_id: int, corps: EtatCorps):
    _verifier_etat(corps.etat)
    with ouvrir() as conn:
        produit = produits.modifier(conn, produit_id, {"etat": corps.etat})
    if not produit:
        raise ErreurMaison("Produit introuvable", 404)
    return _publier_produit(produit)


@routeur.post("/produits/{produit_id}/photo")
async def photo_produit(produit_id: int, photo: UploadFile = File(...)):
    nom = enregistrer_image(await photo.read())
    with ouvrir() as conn:
        produit = produits.modifier(conn, produit_id, {"photo": nom})
    if not produit:
        raise ErreurMaison("Produit introuvable", 404)
    return _publier_produit(produit)


@routeur.delete("/produits/{produit_id}")
def supprimer_produit(produit_id: int):
    with ouvrir() as conn:
        if not produits.supprimer(conn, produit_id):
            raise ErreurMaison("Produit introuvable", 404)
    return {"ok": True}


@routeur.get("/courses")
def lister_courses():
    with ouvrir() as conn:
        return courses.lister(conn)


@routeur.post("/courses")
def ajouter_course(corps: CourseCorps):
    if not corps.nom.strip():
        raise ErreurMaison("Il faut un nom")
    with ouvrir() as conn:
        return courses.ajouter(conn, corps.model_dump())


@routeur.patch("/courses/{course_id}")
def modifier_course(course_id: int, corps: CourseMaj):
    champs = {cle: valeur for cle, valeur in corps.model_dump().items() if valeur is not None}
    with ouvrir() as conn:
        ligne = courses.modifier(conn, course_id, champs)
    if not ligne:
        raise ErreurMaison("Ligne introuvable", 404)
    return ligne


@routeur.post("/courses/manques")
def courses_manques(corps: ActionPersonne):
    with ouvrir() as conn:
        nombre = courses.depuis_manques(conn, corps.personne_id)
        return {"ajoutes": nombre, "courses": courses.lister(conn)}


@routeur.post("/courses/{course_id}/ranger")
def ranger_course(course_id: int):
    with ouvrir() as conn:
        produit = courses.ranger(conn, course_id)
    if not produit:
        raise ErreurMaison("Ligne introuvable", 404)
    return _publier_produit(produit)


@routeur.delete("/courses/{course_id}")
def supprimer_course(course_id: int):
    with ouvrir() as conn:
        if not courses.supprimer(conn, course_id):
            raise ErreurMaison("Ligne introuvable", 404)
    return {"ok": True}


@routeur.delete("/courses")
def vider_courses():
    with ouvrir() as conn:
        return {"enleves": courses.vider_cochees(conn)}


@routeur.get("/menus")
def menus():
    with ouvrir() as conn:
        return foyer.semaine(conn)


@routeur.put("/menus")
def enregistrer_menus(corps: MenusCorps):
    with ouvrir() as conn:
        for ligne in corps.lignes:
            if ligne.moment not in {"midi", "soir"}:
                raise ErreurMaison("Le repas doit être midi ou soir")
            try:
                date.fromisoformat(ligne.jour)
            except ValueError as exc:
                raise ErreurMaison("Date invalide") from exc
            foyer.enregistrer_menu(conn, ligne.jour, ligne.moment, ligne.titre, ligne.court)
        return foyer.semaine(conn)


@routeur.post("/tickets")
async def creer_ticket(
    photo: UploadFile = File(...),
    personne_id: int | None = Form(default=None),
):
    nom_photo = enregistrer_image(await photo.read())
    texte = ocr.lire_image(config.chemin_uploads() / nom_photo)
    propositions = ocr.extraire_lignes(texte)
    with ouvrir() as conn:
        curseur = conn.execute(
            "INSERT INTO tickets (photo, texte_ocr, personne_id, cree_le) VALUES (?, ?, ?, ?)",
            (nom_photo, texte, personne_id, maintenant_iso()),
        )
        ticket_id = curseur.lastrowid
        for proposition in propositions:
            nom = presenter_nom(proposition["nom"])
            connu = produits.meilleur_nom(conn, nom)
            categorie = connu["categorie"] if connu else "cuisine"
            lieu_id = connu["lieu_id"] if connu else produits.lieu_par_defaut(conn, categorie)
            conn.execute(
                """
                INSERT INTO ticket_lignes (ticket_id, nom, quantite, produit_id, categorie, lieu_id, unite)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    connu["nom"] if connu else nom,
                    proposition["quantite"],
                    connu["id"] if connu else None,
                    categorie,
                    lieu_id,
                    connu["unite"] if connu else "pièce",
                ),
            )
        return _ticket(conn, ticket_id)


def _ticket(conn, ticket_id: int) -> dict:
    ticket = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise ErreurMaison("Ticket introuvable", 404)
    lignes = [dict(row) for row in conn.execute(
        "SELECT * FROM ticket_lignes WHERE ticket_id = ? ORDER BY id", (ticket_id,)
    )]
    for ligne in lignes:
        ligne["quantite"] = int(ligne["quantite"]) if float(ligne["quantite"]).is_integer() else ligne["quantite"]
    return {
        "id": ticket["id"],
        "photo": url_media(ticket["photo"]),
        "texte_ocr": ticket["texte_ocr"],
        "lu": bool(ticket["texte_ocr"].strip()),
        "lignes": lignes,
    }


@routeur.get("/tickets/{ticket_id}")
def obtenir_ticket(ticket_id: int):
    with ouvrir() as conn:
        return _ticket(conn, ticket_id)


@routeur.post("/tickets/{ticket_id}/lignes")
def ajouter_ligne(ticket_id: int, corps: LigneTicket):
    _verifier_categorie(corps.categorie)
    if not corps.nom.strip():
        raise ErreurMaison("Il faut un nom")
    with ouvrir() as conn:
        if not conn.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone():
            raise ErreurMaison("Ticket introuvable", 404)
        lieu_id = corps.lieu_id or produits.lieu_par_defaut(conn, corps.categorie)
        conn.execute(
            """
            INSERT INTO ticket_lignes (ticket_id, nom, quantite, produit_id, categorie, lieu_id, unite)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ticket_id, corps.nom.strip(), corps.quantite, corps.produit_id, corps.categorie, lieu_id, corps.unite),
        )
        return _ticket(conn, ticket_id)


@routeur.post("/tickets/{ticket_id}/lignes/{ligne_id}/confirmer")
def confirmer_ligne(ticket_id: int, ligne_id: int, corps: LigneTicket):
    _verifier_categorie(corps.categorie)
    with ouvrir() as conn:
        ligne = conn.execute(
            "SELECT * FROM ticket_lignes WHERE id = ? AND ticket_id = ?",
            (ligne_id, ticket_id),
        ).fetchone()
        if not ligne:
            raise ErreurMaison("Ligne introuvable", 404)
        if corps.produit_id:
            produit = produits.ajouter_quantite(conn, corps.produit_id, corps.quantite)
            if not produit:
                raise ErreurMaison("Produit introuvable", 404)
        else:
            produit = produits.creer(conn, {
                "nom": corps.nom,
                "categorie": corps.categorie,
                "lieu_id": corps.lieu_id,
                "quantite": corps.quantite,
                "unite": corps.unite,
                "etat": "y_en_a",
            })
        conn.execute(
            """
            UPDATE ticket_lignes
            SET statut = 'confirme', nom = ?, quantite = ?, produit_id = ?, categorie = ?, lieu_id = ?, unite = ?
            WHERE id = ?
            """,
            (corps.nom, corps.quantite, produit["id"], corps.categorie, corps.lieu_id, corps.unite, ligne_id),
        )
        return _ticket(conn, ticket_id)


@routeur.post("/tickets/{ticket_id}/lignes/{ligne_id}/rejeter")
def rejeter_ligne(ticket_id: int, ligne_id: int):
    with ouvrir() as conn:
        curseur = conn.execute(
            """
            UPDATE ticket_lignes SET statut = 'rejete'
            WHERE id = ? AND ticket_id = ? AND statut = 'propose'
            """,
            (ligne_id, ticket_id),
        )
        if curseur.rowcount == 0:
            raise ErreurMaison("Ligne introuvable", 404)
        return _ticket(conn, ticket_id)


@routeur.post("/reconnaissance")
async def reconnaissance(photo: UploadFile = File(...)):
    nom_photo = enregistrer_image(await photo.read())
    code = ocr.lire_code_barres(config.chemin_uploads() / nom_photo)
    with ouvrir() as conn:
        produit = produits.trouver_code(conn, code) if code else None
        return {
            "photo": url_media(nom_photo),
            "code_barres": code,
            "produit": _publier_produit(produit),
        }


@routeur.get("/plantes")
def plantes():
    with ouvrir() as conn:
        liste = foyer.lister_plantes(conn)
    for plante in liste:
        plante["photo"] = url_media(plante.get("photo"))
    return liste


@routeur.post("/plantes")
def creer_plante(corps: PlanteCorps):
    if not corps.nom.strip():
        raise ErreurMaison("Il faut un nom")
    with ouvrir() as conn:
        plante = foyer.creer_plante(conn, corps.model_dump())
    plante["photo"] = None
    return plante


@routeur.post("/plantes/{plante_id}/arroser")
def arroser(plante_id: int, corps: ActionPersonne):
    with ouvrir() as conn:
        plante = foyer.arroser(conn, plante_id, _nom_personne(conn, corps.personne_id, corps.par))
    if not plante:
        raise ErreurMaison("Plante introuvable", 404)
    plante["photo"] = url_media(plante.get("photo"))
    return plante


@routeur.delete("/plantes/{plante_id}")
def supprimer_plante(plante_id: int):
    with ouvrir() as conn:
        if not foyer.supprimer_plante(conn, plante_id):
            raise ErreurMaison("Plante introuvable", 404)
    return {"ok": True}


@routeur.get("/menage")
def menage():
    with ouvrir() as conn:
        return foyer.lister_menage(conn)


@routeur.post("/menage")
def creer_menage(corps: MenageCorps):
    if not corps.piece.strip():
        raise ErreurMaison("Il faut une pièce")
    with ouvrir() as conn:
        return foyer.creer_menage(conn, corps.piece, corps.frequence_jours)


@routeur.post("/menage/{menage_id}/fait")
def menage_fait(menage_id: int, corps: ActionPersonne):
    with ouvrir() as conn:
        tache = foyer.menage_fait(conn, menage_id, _nom_personne(conn, corps.personne_id, corps.par))
    if not tache:
        raise ErreurMaison("Pièce introuvable", 404)
    return tache


@routeur.patch("/menage/{menage_id}")
def modifier_menage(menage_id: int, corps: FrequenceCorps):
    with ouvrir() as conn:
        tache = foyer.modifier_menage(conn, menage_id, corps.frequence_jours)
    if not tache:
        raise ErreurMaison("Pièce introuvable", 404)
    return tache


@routeur.delete("/menage/{menage_id}")
def supprimer_menage(menage_id: int):
    with ouvrir() as conn:
        if not foyer.supprimer_menage(conn, menage_id):
            raise ErreurMaison("Pièce introuvable", 404)
    return {"ok": True}


@routeur.get("/animaux")
def animaux():
    with ouvrir() as conn:
        liste = foyer.lister_animaux(conn)
    for animal in liste:
        animal["photo"] = url_media(animal.get("photo"))
    return liste


@routeur.post("/animaux")
def creer_animal(corps: AnimalCorps):
    if not corps.nom.strip():
        raise ErreurMaison("Il faut un nom")
    with ouvrir() as conn:
        animal = foyer.creer_animal(conn, corps.model_dump())
    animal["photo"] = None
    return animal


@routeur.patch("/animaux/{animal_id}")
def modifier_animal(animal_id: int, corps: AnimalCorps):
    with ouvrir() as conn:
        animal = foyer.modifier_animal(conn, animal_id, corps.model_dump())
    if not animal:
        raise ErreurMaison("Animal introuvable", 404)
    animal["photo"] = url_media(animal.get("photo"))
    return animal


@routeur.delete("/animaux/{animal_id}")
def supprimer_animal(animal_id: int):
    with ouvrir() as conn:
        if not foyer.supprimer_animal(conn, animal_id):
            raise ErreurMaison("Animal introuvable", 404)
    return {"ok": True}


@routeur.get("/dates")
def dates():
    with ouvrir() as conn:
        return foyer.lister_dates(conn)


@routeur.post("/dates")
def creer_date(corps: DateCorps):
    if not corps.titre.strip():
        raise ErreurMaison("Il faut un titre")
    try:
        date(2024, corps.mois, min(corps.jour, 28) if corps.mois == 2 and corps.jour == 29 else corps.jour)
    except ValueError as exc:
        raise ErreurMaison("Cette date n'existe pas") from exc
    with ouvrir() as conn:
        return foyer.creer_date(conn, corps.model_dump())


@routeur.delete("/dates/{date_id}")
def supprimer_date(date_id: int):
    with ouvrir() as conn:
        if not foyer.supprimer_date(conn, date_id):
            raise ErreurMaison("Date introuvable", 404)
    return {"ok": True}


@routeur.post("/exemple")
def exemple():
    with ouvrir() as conn:
        try:
            foyer.charger_exemple(conn)
        except ValueError as exc:
            raise ErreurMaison(str(exc), 409) from exc
    return {"ok": True}
