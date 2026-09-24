"""Idées de repas à partir de ce qui est encore à la maison."""

from maison.texte import mot_dans

RECETTES = [
    {
        "titre": "Pâtes rapides",
        "minutes": 15,
        "court": True,
        "besoins": [["pates", "spaghetti", "coquillette", "nouille"]],
        "optionnels": [["beurre"], ["fromage"], ["oeuf"]],
        "etapes": [
            "Fais bouillir une grande casserole d'eau salée.",
            "Cuis les pâtes le temps écrit sur le paquet.",
            "Égoutte, ajoute le beurre ou le fromage, et sers tout de suite.",
        ],
    },
    {
        "titre": "Omelette",
        "minutes": 10,
        "court": True,
        "besoins": [["oeuf"]],
        "optionnels": [["fromage"], ["jambon"]],
        "etapes": [
            "Casse les œufs dans un bol et bats-les avec une pincée de sel.",
            "Fais chauffer un peu de matière grasse dans une poêle.",
            "Verse les œufs, laisse prendre, plie l'omelette et sers.",
        ],
    },
    {
        "titre": "Tartines",
        "minutes": 5,
        "court": True,
        "besoins": [["pain"]],
        "optionnels": [["beurre"], ["confiture"], ["fromage"]],
        "etapes": [
            "Fais griller le pain si tu aimes.",
            "Tartine ce que tu as : beurre, fromage ou confiture.",
            "Sers avec un fruit ou un reste de salade.",
        ],
    },
    {
        "titre": "Riz",
        "minutes": 20,
        "court": False,
        "besoins": [["riz"]],
        "optionnels": [["oeuf"], ["courgette", "carotte", "legume"]],
        "etapes": [
            "Rince le riz et cuis-le dans deux fois son volume d'eau.",
            "Fais revenir les légumes ou un œuf à la poêle.",
            "Mélange avec le riz et sale.",
        ],
    },
    {
        "titre": "Poêlée de légumes",
        "minutes": 25,
        "court": False,
        "besoins": [["courgette", "carotte", "poivron", "haricot", "pois", "legume"]],
        "optionnels": [["oeuf"], ["riz"]],
        "etapes": [
            "Lave et coupe les légumes en morceaux.",
            "Fais-les revenir à la poêle avec un peu d'huile, 10 à 15 minutes.",
            "Sale, poivre, et sers. Un œuf au plat se pose dessus si tu en as.",
        ],
    },
    {
        "titre": "Pommes de terre",
        "minutes": 30,
        "court": False,
        "besoins": [["pomme de terre", "pdt"]],
        "optionnels": [["beurre"], ["fromage"]],
        "etapes": [
            "Lave les pommes de terre et coupe-les en rondelles.",
            "Fais-les cuire à la poêle avec un peu de matière grasse, 20 minutes.",
            "Sale à la fin. Ajoute du fromage si tu en as.",
        ],
    },
    {
        "titre": "Salade",
        "minutes": 10,
        "court": True,
        "besoins": [["salade"]],
        "optionnels": [["tomate"], ["oeuf"], ["thon"]],
        "etapes": [
            "Lave la salade et essore-la.",
            "Ajoute ce que tu as : tomate, œuf dur, thon.",
            "Assaisonne avec de l'huile et du sel, puis sers.",
        ],
    },
    {
        "titre": "Semoule",
        "minutes": 15,
        "court": True,
        "besoins": [["semoule", "couscous"]],
        "optionnels": [["pois", "legume"], ["poulet"]],
        "etapes": [
            "Verse de l'eau bouillante sur la semoule, couvre 5 minutes.",
            "Égraine à la fourchette.",
            "Ajoute les légumes ou le poulet que tu as, et sers.",
        ],
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


def formuler_recette(noms: list[str]) -> str:
    """Une recette rédigée, avec les étapes, à partir des noms en stock."""
    trouvees = idees(noms)
    if trouvees:
        recette = next(item for item in RECETTES if item["titre"] == trouvees[0]["titre"])
        autres = [item["titre"] for item in trouvees[1:]]
        return _texte_recette(recette, noms, autres)
    for recette in RECETTES:
        manques = [groupe for groupe in recette["besoins"] if not _groupe_present(groupe, noms)]
        if len(manques) == 1:
            mot = manques[0][0]
            return (
                f"Pour {recette['titre'].lower()}, il manque : {mot}. "
                "Dis « ajoute-le aux courses » ou montre-moi autre chose dans le frigo."
            )
    if not noms:
        return "Je ne sais pas encore ce qu'il y a. Montre-moi le frigo ou dis : lait, œufs, pâtes."
    return "Avec " + ", ".join(noms[:6]) + ", je n'ai pas de recette sûre. Dis-moi ce que tu veux cuisiner."


def _texte_recette(recette: dict, noms: list[str], autres: list[str]) -> str:
    presents = []
    for groupe in recette["besoins"] + recette.get("optionnels", []):
        presents.extend(_groupe_present(groupe, noms))
    lignes = [
        f"{recette['titre']}, environ {recette['minutes']} minutes.",
        "Déjà là : " + ", ".join(dict.fromkeys(presents)) if presents else "Je pars de ce que tu as.",
    ]
    for numero, etape in enumerate(recette.get("etapes", []), start=1):
        lignes.append(f"{numero}. {etape}")
    if autres:
        lignes.append("Sinon : " + ", ".join(autres) + ".")
    return "\n".join(lignes)
