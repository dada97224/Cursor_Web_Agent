# Maison

Application locale pour la maison. Elle tourne sur un ordinateur, et les téléphones du foyer l'ouvrent sur le Wi-Fi.

L'accueil est Jarvis : un bouton à maintenir pour parler, et un champ texte en dessous. Le stock s'ouvre à part, avec les catégories à gauche (frigo, congélateur, secs, réserves, pharmacie, entretien, courses).

Le bouton micro utilise la dictée du navigateur. Elle ne marche qu'en contexte sécurisé : `localhost` sur l'ordinateur, ou HTTPS pour les téléphones. En HTTP sur le Wi-Fi, c'est le micro du clavier. Une dictée locale (faster-whisper, modèle `small`, français, CPU) peut venir ensuite, une fois le micro autorisé.

Les tickets passent par Tesseract (`--psm 4`). Les QR codes et les codes-barres passent par ZBar, sur la même photo. Une photo du frigo sans texte lisible n'est pas reconnue : il n'y a pas de modèle de vision installé.

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
