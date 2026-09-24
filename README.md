# Maison

Application locale pour la maison. Elle tourne sur un ordinateur, et les téléphones du foyer l'ouvrent sur le Wi-Fi.

On lui parle depuis l'accueil, au clavier ou au micro. Une photo de ticket remplit le stock. Une photo du frigo, quand les mots sont lisibles, sert à proposer une recette avec les étapes. « Où est le lait ? » et « range le lait dans le frigo » évitent de remplir des fiches.

Les listes (courses, pharmacie, ménage, animaux, dates, plantes simples) restent derrière Maison. Le module plantes détaillé viendra à part.

## Lancer

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m maison
```

Puis ouvrir `http://127.0.0.1:8080` sur l'ordinateur. L'adresse pour les téléphones est indiquée dans Réglages. Le port se change avec `MAISON_PORT` (8080 par défaut). L'application écoute sur le réseau local, pas sur Internet.

Pour lire un ticket de caisse ou un code-barres :

```bash
sudo apt install tesseract-ocr tesseract-ocr-fra libzbar0
```

Sans ces programmes, la photo est gardée et les articles se saisissent à la main. Rien n'entre dans le stock sans un « Oui, on l'a ».

La liste de courses reste consultable sur le téléphone si le Wi-Fi de la maison ne porte pas jusqu'au magasin, après une première ouverture à la maison.

## Tests

```bash
pytest
```
