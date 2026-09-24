"""Idées de repas à partir de ce qui est encore à la maison."""

from maison.texte import mot_dans

RECETTES = [
    {
        "titre": "Pâtes rapides",
        "minutes": 15,
        "court": True,
        "besoins": [["pates", "spaghetti", "coquillette", "nouille"]],
        "optionnels": [["beurre"], ["fromage"], ["oeuf"]],
    },
    {
        "titre": "Omelette",
        "minutes": 10,
        "court": True,
        "besoins": [["oeuf"]],
        "optionnels": [["fromage"], ["jambon"]],
    },
    {
        "titre": "Tartines",
        "minutes": 5,
        "court": True,
        "besoins": [["pain"]],
        "optionnels": [["beurre"], ["confiture"], ["fromage"]],
    },
    {
        "titre": "Riz",
        "minutes": 20,
        "court": False,
        "besoins": [["riz"]],
        "optionnels": [["oeuf"], ["courgette", "carotte", "legume"]],
    },
    {
        "titre": "Poêlée de légumes",
        "minutes": 25,
        "court": False,
        "besoins": [["courgette", "carotte", "poivron", "haricot", "pois", "legume"]],
        "optionnels": [["oeuf"], ["riz"]],
    },
    {
        "titre": "Pommes de terre",
        "minutes": 30,
        "court": False,
        "besoins": [["pomme de terre", "pdt"]],
        "optionnels": [["beurre"], ["fromage"]],
    },
    {
        "titre": "Salade",
        "minutes": 10,
        "court": True,
        "besoins": [["salade"]],
        "optionnels": [["tomate"], ["oeuf"], ["thon"]],
    },
    {
        "titre": "Semoule",
        "minutes": 15,
        "court": True,
        "besoins": [["semoule", "couscous"]],
        "optionnels": [["pois", "legume"], ["poulet"]],
    },
]


def _groupe_present(groupe: list[str], noms: list[str]) -> list[str]:
    trouves = []
    for nom in noms:
        if any(mot_dans(mot, nom) for mot in groupe):
            trouves.append(nom)
    return trouves


def idees(noms: list[str]) -> list[dict]:
    candidats = []
    for recette in RECETTES:
        manques = [groupe for groupe in recette["besoins"] if not _groupe_present(groupe, noms)]
        if manques:
            continue
        bonus = 0
        accompagnements: list[str] = []
        for groupe in recette["optionnels"]:
            trouves = _groupe_present(groupe, noms)
            if trouves:
                bonus += 1
                accompagnements.extend(trouves)
        candidats.append((10 + bonus + (2 if recette["court"] else 0), recette, accompagnements))
    candidats.sort(key=lambda item: item[0], reverse=True)
    choisis = candidats[:3]
    if choisis and not any(item[1]["court"] for item in choisis):
        court = next((item for item in candidats if item[1]["court"]), None)
        if court:
            choisis = choisis[:2] + [court]
    resultat = []
    for _, recette, accompagnements in choisis:
        detail = f"Environ {recette['minutes']} minutes"
        if recette["court"]:
            detail += " · repas court"
        if accompagnements:
            detail += " · avec " + ", ".join(dict.fromkeys(accompagnements))
        resultat.append({
            "titre": recette["titre"],
            "detail": detail,
            "court": recette["court"],
            "minutes": recette["minutes"],
        })
    return resultat
