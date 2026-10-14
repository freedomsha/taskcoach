from abc import ABC, abstractmethod


class ApplicationInterface(ABC):
    """Contrat que toute implémentation de GUI (wx, tk, ...) doit respecter."""

    @abstractmethod
    def init(self, loadSettings=True, loadTaskFile=True):
        """Initialiser l'application."""
        pass

    @abstractmethod
    def start(self):
        """Démarrer la boucle d'événements."""
        pass

    @abstractmethod
    def quitApplication(self, force=False) -> bool:
        """Quitter l'application. Retourner True si succès."""
        pass

    @abstractmethod
    def displayMessage(self, message: str):
        """Afficher un message à l'utilisateur."""
        pass

    @abstractmethod
    def on_end_session(self):
        """Gérer la fin de session."""
        pass