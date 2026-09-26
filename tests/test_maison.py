"""Parcours utiles de la maison."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from maison.ocr import extraire_lignes
from maison.repas import idees
from maison.texte import mot_dans, score_noms


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MAISON_DB", str(tmp_path / "maison.sqlite"))
    monkeypatch.setenv("MAISON_UPLOADS", str(tmp_path / "uploads"))
    from maison.main import creer_application

    with TestClient(creer_application()) as test:
        yield test


def test_ticket_ignore_le_total():
    texte = """
    CARREFOUR
    LAIT DEMI ECREME 1,15
    2 x YAOURT NATURE 2,40
    PAIN
    1,05
    TOTAL 4,60
    CB 4,60
    MERCI
    """
    lignes = extraire_lignes(texte)
    assert [ligne["nom"] for ligne in lignes] == ["LAIT DEMI ECREME", "YAOURT NATURE", "PAIN"]
    assert lignes[1]["quantite"] == 2


def test_idees_avec_ce_qui_reste():
    titres = [idee["titre"] for idee in idees(["Pâtes", "Œufs"])]
    assert "Pâtes rapides" in titres
    assert "Omelette" in titres
    assert "Riz" not in titres


def test_pois_ne_matche_pas_poisson():
    assert mot_dans("pois", "petits pois")
    assert not mot_dans("pois", "poisson")
    assert score_noms("Lait", "Lait demi-écrémé") >= 0.9


def test_accueil_et_courses(client):
    assert client.get("/").status_code == 200
    exemple = client.post("/api/exemple")
    assert exemple.status_code == 200
    assert client.post("/api/exemple").status_code == 409
    accueil = client.get("/api/accueil").json()
    titres = " ".join(rappel["titre"] for rappel in accueil["rappels"])
    assert "Basilic" in titres
    assert "Ampoules" in titres
    assert any(idee["titre"] == "Omelette" for idee in accueil["idees"])
    manques = client.post("/api/courses/manques", json={}).json()
    noms = [ligne["nom"] for ligne in manques["courses"]]
    assert "Lait demi-écrémé" in noms
    assert "Ampoules" in noms
    lait = next(ligne for ligne in manques["courses"] if "Lait" in ligne["nom"])
    range = client.post(f"/api/courses/{lait['id']}/ranger")
    assert range.status_code == 200
    assert range.json()["etat"] == "y_en_a"
    assert range.json()["quantite"] >= 2


def test_confirmation_ticket(client, monkeypatch):
    monkeypatch.setattr("maison.ocr.lire_image", lambda chemin: "LAIT ENTIER 1,20\nTOTAL 1,20\n")
    image = Image.new("RGB", (30, 30), "white")
    tampon = io.BytesIO()
    image.save(tampon, "JPEG")
    tampon.seek(0)
    ticket = client.post("/api/tickets", files={"photo": ("ticket.jpg", tampon, "image/jpeg")})
    assert ticket.status_code == 200
    ligne = ticket.json()["lignes"][0]
    confirme = client.post(
        f"/api/tickets/{ticket.json()['id']}/lignes/{ligne['id']}/confirmer",
        json={"nom": "Lait entier", "quantite": 2, "categorie": "cuisine", "lieu_id": ligne["lieu_id"]},
    )
    assert confirme.status_code == 200
    assert confirme.json()["lignes"][0]["statut"] == "confirme"
    produits = client.get("/api/produits").json()
    lait = next(produit for produit in produits if produit["nom"] == "Lait entier")
    assert lait["quantite"] == 2


def test_etat_vide_revient_a_un(client):
    cree = client.post("/api/produits", json={"nom": "Savon", "categorie": "consommable", "quantite": 0, "etat": "plus"}).json()
    assert cree["quantite"] == 0
    remis = client.post(f"/api/produits/{cree['id']}/etat", json={"etat": "y_en_a"}).json()
    assert remis["quantite"] == 1
    assert remis["etat"] == "y_en_a"


def test_conversation(client):
    ou = client.post("/api/messages", json={"texte": "où est le lait", "auteur": "Camille"})
    assert ou.status_code == 200
    assert "connais pas" in ou.json()["reponse"]
    client.post("/api/messages", json={"texte": "range le lait dans le frigo", "auteur": "Camille"})
    retrouve = client.post("/api/messages", json={"texte": "où est le lait"})
    assert "Frigo" in retrouve.json()["reponse"]
    client.post("/api/produits", json={"nom": "Œufs", "categorie": "cuisine", "quantite": 6, "etat": "y_en_a"})
    client.post("/api/produits", json={"nom": "Pâtes", "categorie": "cuisine", "quantite": 2, "etat": "y_en_a"})
    repas = client.post("/api/messages", json={"texte": "qu'est-ce qu'on mange"})
    assert "1." in repas.json()["reponse"]
    manque = client.post("/api/messages", json={"texte": "plus de pain"})
    assert "pain" in manque.json()["reponse"].lower()


def test_liste_avec_precision(client):
    phrase = "ajoute du lait, du pain de mie, des oeufs et du coca à la liste des courses de la semaine"
    reponse = client.post("/api/messages", json={"texte": phrase}).json()["reponse"]
    assert "6, 12 ou 24" in reponse
    assert "2 litres" in reponse
    noms = [ligne["nom"] for ligne in client.get("/api/courses").json()]
    assert "Lait" in noms
    assert "Pain de Mie" in noms
    assert "Coca" in noms
    assert "Œufs" not in noms
    suite = client.post("/api/messages", json={"texte": "12"}).json()["reponse"]
    assert "12" in suite
    oeufs = next(ligne for ligne in client.get("/api/courses").json() if ligne["nom"] == "Œufs")
    assert oeufs["quantite"] == 12
    stock = client.post("/api/messages", json={"texte": "j'ai rangé la liste des courses, tu peux actualiser le stock"}).json()
    assert "Stock actualisé" in stock["reponse"]
    assert client.get("/api/courses").json() == []


def test_parole_transcrite(client, monkeypatch):
    monkeypatch.setattr("maison.voix.transcrire", lambda chemin: "il faudrait acheter du lait et du pain")
    reponse = client.post(
        "/api/parler",
        files={"audio": ("voix.webm", b"x" * 1000, "audio/webm")},
    )
    assert reponse.status_code == 200
    assert reponse.json()["transcription"].startswith("il faudrait")
    noms = [ligne["nom"] for ligne in client.get("/api/courses").json()]
    assert "Lait" in noms
    assert "Pain" in noms


def test_menus_et_plante(client):
    semaine = client.get("/api/menus").json()
    assert len(semaine) == 7
    client.put("/api/menus", json={"lignes": [{"jour": semaine[0]["jour"], "moment": "soir", "titre": "Soupe", "court": True}]})
    assert client.get("/api/menus").json()[0]["soir"] == "Soupe"
    plante = client.post("/api/plantes", json={"nom": "Lierre", "piece": "Salon", "intervalle_jours": 7}).json()
    assert "Lierre" in client.get("/api/accueil").json()["rappels"].__str__() or any(
        "Lierre" in rappel["titre"] for rappel in client.get("/api/accueil").json()["rappels"]
    )
    arrose = client.post(f"/api/plantes/{plante['id']}/arroser", json={"par": "Camille"})
    assert arrose.json()["dernier_par"] == "Camille"
