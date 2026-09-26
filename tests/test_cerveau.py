"""Le modèle local décide via un bloc <meta>, EverShelf exécute."""

from cerveau.meta import extraire_meta


def test_meta_separe_la_phrase_de_l_action():
    brut = (
        "Je le note.\n"
        '<meta>{"intent":"courses_ajouter","articles":[{"nom":"Beurre","quantite":1,'
        '"unite":"plaquette","lieu":null,"question":null,"suppose":null}],"texte":null}</meta>'
    )
    visible, meta = extraire_meta(brut)
    assert visible == "Je le note."
    assert meta["intent"] == "courses_ajouter"
    assert meta["articles"][0]["nom"] == "Beurre"


def test_ollama_decide_et_ecrit_dans_evershelf(client, monkeypatch):
    monkeypatch.setenv("MAISON_SANS_OLLAMA", "0")
    monkeypatch.setattr("cerveau.pipeline.ollama.disponible", lambda: True)
    monkeypatch.setattr(
        "cerveau.pipeline.ollama.completer",
        lambda texte, historique: (
            "D'accord.\n"
            '<meta>{"intent":"courses_ajouter","articles":[{"nom":"Beurre","quantite":1,'
            '"unite":"plaquette","lieu":null,"question":null,"suppose":null}],"texte":null}</meta>'
        ),
    )
    reponse = client.post("/api/messages", json={"texte": "mets du beurre sur la liste"})
    assert reponse.status_code == 200
    assert "beurre" in reponse.json()["reponse"].lower()
    noms = " ".join(ligne["nom"] for ligne in client.get("/api/etageres/courses").json()).lower()
    assert "beurre" in noms
