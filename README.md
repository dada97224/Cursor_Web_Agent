# Maison

Application locale pour la maison. Elle tourne sur un ordinateur, et les téléphones du foyer l'ouvrent sur le Wi-Fi.

L'accueil est Jarvis : un bouton pour parler, et un champ texte en dessous. Le garde-manger est [EverShelf](https://github.com/dadaloop82/EverShelf) (stock, dates, codes-barres, liste, recettes), servi sur la même adresse, onglet Garde-manger. Son interface a le français dans les réglages.

Le cerveau suit deux idées reprises ici, sans embarquer leurs applications :

- [isair/jarvis](https://github.com/isair/jarvis) : un modèle local (Ollama) décide, puis des outils mettent à jour le stock. Rien ne part dans le cloud.
- [copain](https://github.com/arnaudstdr/copain) : la décision française sort dans un bloc `<meta>` en fin de réponse. Le code exécute, le modèle ne touche pas à la base.

La transcription est faite localement par Whisper (`base`, français). La première fois, le modèle se télécharge. `MAISON_WHISPER=small` entend mieux, et prend plus de place. Le micro du navigateur reste réservé à `localhost` ou à une adresse HTTPS.

Ollama est facultatif. S'il tourne (`MAISON_OLLAMA`, défaut `http://127.0.0.1:11434`, modèle `MAISON_OLLAMA_MODELE=llama3.2`), c'est lui qui comprend la phrase. S'il est éteint, une lecture française locale produit le même bloc d'intention, pour que la maison reste utilisable.

Les tickets passent par Tesseract (`--psm 4`). Les QR codes et les codes-barres passent par ZBar, sur la même photo. Une photo du frigo sans texte lisible n'est pas reconnue : il n'y a pas de modèle de vision installé.

Les listes (courses, pharmacie, ménage, animaux, dates, plantes simples) restent derrière Maison. Le module plantes détaillé viendra à part.

## Lancer

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m maison
```

Il faut PHP pour le garde-manger (EverShelf est en PHP) :

```bash
sudo apt install php-cli php-sqlite3 php-mbstring php-curl php-xml
```

Puis ouvrir `http://127.0.0.1:8080` sur l'ordinateur. Jarvis est à la racine, le garde-manger sur `/garde-manger/`. L'adresse pour les téléphones est indiquée dans Réglages. Le port se change avec `MAISON_PORT` (8080 par défaut). EverShelf écoute en interne sur `8091` (`EVERSHELF_PORT`). L'application écoute sur le réseau local, pas sur Internet.

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
