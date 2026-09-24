"""SQLite de la maison, créé au premier lancement."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from maison import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS personnes (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    couleur TEXT NOT NULL,
    photo TEXT,
    cree_le TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lieux (
    id INTEGER PRIMARY KEY,
    piece TEXT NOT NULL,
    nom TEXT NOT NULL,
    cree_le TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produits (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    categorie TEXT NOT NULL CHECK (categorie IN ('cuisine', 'congelo', 'pharmacie', 'consommable')),
    lieu_id INTEGER REFERENCES lieux(id) ON DELETE SET NULL,
    quantite REAL NOT NULL DEFAULT 0,
    unite TEXT NOT NULL DEFAULT 'pièce',
    etat TEXT NOT NULL DEFAULT 'y_en_a' CHECK (etat IN ('y_en_a', 'bientot_fini', 'plus')),
    date_limite TEXT,
    magasin TEXT NOT NULL DEFAULT '',
    rayon TEXT NOT NULL DEFAULT '',
    code_barres TEXT NOT NULL DEFAULT '',
    photo TEXT,
    note TEXT NOT NULL DEFAULT '',
    cree_le TEXT NOT NULL,
    maj_le TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS menus (
    id INTEGER PRIMARY KEY,
    jour TEXT NOT NULL,
    moment TEXT NOT NULL CHECK (moment IN ('midi', 'soir')),
    titre TEXT NOT NULL,
    court INTEGER NOT NULL DEFAULT 0,
    UNIQUE (jour, moment)
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    produit_id INTEGER REFERENCES produits(id) ON DELETE SET NULL,
    nom TEXT NOT NULL,
    quantite REAL NOT NULL DEFAULT 1,
    unite TEXT NOT NULL DEFAULT 'pièce',
    magasin TEXT NOT NULL DEFAULT '',
    rayon TEXT NOT NULL DEFAULT '',
    coche INTEGER NOT NULL DEFAULT 0,
    personne_id INTEGER,
    cree_le TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    photo TEXT NOT NULL,
    texte_ocr TEXT NOT NULL DEFAULT '',
    personne_id INTEGER,
    cree_le TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_lignes (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    quantite REAL NOT NULL DEFAULT 1,
    produit_id INTEGER REFERENCES produits(id) ON DELETE SET NULL,
    categorie TEXT NOT NULL DEFAULT 'cuisine',
    lieu_id INTEGER,
    unite TEXT NOT NULL DEFAULT 'pièce',
    statut TEXT NOT NULL DEFAULT 'propose' CHECK (statut IN ('propose', 'confirme', 'rejete'))
);

CREATE TABLE IF NOT EXISTS plantes (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    piece TEXT NOT NULL DEFAULT '',
    photo TEXT,
    intervalle_jours INTEGER NOT NULL DEFAULT 7,
    dernier_arrosage TEXT,
    dernier_par TEXT NOT NULL DEFAULT '',
    cree_le TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS menage (
    id INTEGER PRIMARY KEY,
    piece TEXT NOT NULL,
    frequence_jours INTEGER NOT NULL DEFAULT 7,
    dernier_fait TEXT,
    dernier_par TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS animaux (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    espece TEXT NOT NULL DEFAULT '',
    photo TEXT,
    repas TEXT NOT NULL DEFAULT '',
    soin TEXT NOT NULL DEFAULT '',
    prochain_soin TEXT,
    note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS dates_famille (
    id INTEGER PRIMARY KEY,
    titre TEXT NOT NULL,
    jour INTEGER NOT NULL,
    mois INTEGER NOT NULL,
    annee INTEGER,
    note TEXT NOT NULL DEFAULT ''
);
"""

LIEUX_DEFAUT = [
    ("Cuisine", "Frigo"),
    ("Cuisine", "Congélateur"),
    ("Cuisine", "Placard"),
    ("Cuisine", "Conserves"),
    ("Salle de bain", "Pharmacie"),
    ("Cuisine", "Sous l'évier"),
    ("Garage", "Étagère"),
]

MENAGE_DEFAUT = [
    ("Cuisine", 3),
    ("Salle de bain", 7),
    ("Toilettes", 3),
    ("Salon", 7),
    ("Chambres", 14),
]


@contextmanager
def ouvrir() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(config.chemin_base())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialiser() -> None:
    config.chemin_base().parent.mkdir(parents=True, exist_ok=True)
    config.chemin_uploads().mkdir(parents=True, exist_ok=True)
    with ouvrir() as conn:
        conn.executescript(SCHEMA)
        from maison.texte import maintenant_iso

        if conn.execute("SELECT COUNT(*) AS n FROM lieux").fetchone()["n"] == 0:
            instant = maintenant_iso()
            conn.executemany(
                "INSERT INTO lieux (piece, nom, cree_le) VALUES (?, ?, ?)",
                [(piece, nom, instant) for piece, nom in LIEUX_DEFAUT],
            )
        if conn.execute("SELECT COUNT(*) AS n FROM menage").fetchone()["n"] == 0:
            conn.executemany(
                "INSERT INTO menage (piece, frequence_jours) VALUES (?, ?)",
                MENAGE_DEFAUT,
            )
