"""
Application Interface - Contrat pour tous les backends GUI

Ce module définit l'interface qu'une implémentation GUI doit respecter.
Il garantit que Application (wx) et TkinterApplication (tk) exposent
la même API, sans imposer leur implémentation interne.
"""

from abc import ABC, abstractmethod


class ApplicationInterface(ABC):
    """
    Contrat que toute implémentation de GUI (wx, tk, ...) doit respecter.

    Cette interface garantit une cohérence entre les différents backends GUI,
    permettant à taskcoach.py de les traiter de manière uniforme.

    Les implémentations peuvent avoir des internals complètement différents
    (wx.App vs tk.Tk), tant qu'elles exposent ces méthodes.
    """

    @abstractmethod
    def init(self, loadSettings=True, loadTaskFile=True):
        """
        Initialiser l'application.

        Charge la configuration, les fichiers de tâches, crée la fenêtre principale.
        Doit être appelé AVANT start().

        Args:
            loadSettings (bool): Charger les paramètres depuis le fichier config.
            loadTaskFile (bool): Charger le dernier fichier de tâches.
        """
        pass

    @abstractmethod
    def start(self):
        """
        Démarrer l'application et entrer dans la boucle d'événements.

        Affiche la fenêtre principale et lance la boucle d'événements
        (wx.App.MainLoop() ou tk.Tk.mainloop()).
        """
        pass

    @abstractmethod
    def quitApplication(self, force=False) -> bool:
        """
        Quitter l'application.

        Sauvegarde les fichiers, paramètres, et ferme proprement.

        Args:
            force (bool): Force la fermeture sans demander confirmation.

        Returns:
            bool: True si la fermeture a réussi, False sinon.
        """
        pass

    @abstractmethod
    def displayMessage(self, message: str):
        """
        Afficher un message à l'utilisateur.

        Peut être une barre de statut, une notification, etc.
        L'implémentation dépend du backend.

        Args:
            message (str): Message à afficher.
        """
        pass

    @abstractmethod
    def on_end_session(self):
        """
        Gérer la fin de session (signal système, fermeture, etc.).

        Appelé quand l'OS signale la fin de la session utilisateur.
        """
        pass

    @abstractmethod
    def on_reopen_app(self):
        """
        Gérer la réouverture de l'application.

        Sur macOS, quand l'utilisateur clique sur l'icône du Dock.
        Sur d'autres systèmes, peut ne rien faire.
        """
        pass
