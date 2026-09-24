"""Erreurs renvoyées telles quelles à l'écran."""


class ErreurMaison(Exception):
    def __init__(self, message: str, statut: int = 400):
        super().__init__(message)
        self.message = message
        self.statut = statut
