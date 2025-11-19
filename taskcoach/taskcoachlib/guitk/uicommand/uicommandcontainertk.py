"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Le mixin UICommandContainerMixin est conçu pour ajouter des commandes
d’interface utilisateur dans des menus ou des barres d’outils.

L'attribut _window est essentiel car il représente la fenêtre Tkinter
à laquelle le menu ou la barre d'outils est associé.
"""

import logging
import tkinter as tk
# from tkinter import Menu

# Assurez-vous que taskcoachlib.gui.newid existe et est compatible avec Tkinter
# Sauf qu'il est inutile !
# from taskcoachlib.guitk.newid import IdProvider

log = logging.getLogger(__name__)


class UICommandContainerMixin(object):
    """ Mixin pour les classes qui agissent comme des conteneurs de commandes
    d'interface utilisateur (comme les menus).

    Fournit la méthode appendUICommands aux classes qui veulent ajouter
    des commandes UI.
    """

    def __init__(self, parent_window, tearoff):
        """
        Initialise le mixin.
        :param parent_window: La fenêtre parente Tkinter (tk.Tk ou tk.Frame)
        """
        self._window = parent_window
        log.debug(f"UICommandContainerMixin : La classe {self.__class__.__name__} initialise pour ajouter des commandes UI.")
        if not isinstance(parent_window, (tk.Tk, tk.Frame)):
            log.warning(f"{self.__class__.__name__} doit être de type tk.Tk ou tk.Frame !")
        self._tearoff = tearoff

    def appendUICommands(self, *uiCommands, **kwargs):
        """ Ajout des *uiCommands.

        Cette méthode, qui est mélangée dans une classe de menu,
        prend une liste de UICommand et les ajoute au menu.
        Elle gère également les séparateurs et les sous-menus.

        Args :
            *uiCommands : Instances de UICommand ou tuples pour les sous-menus.
        """
        if not hasattr(self, "_window") or self._window is None:
            log.warning("UICommandContainerMixin.appendUICommands : l'attribut _window est manquant ou None.")
            return

        if not uiCommands:
            log.warning("Aucune UICommand n’a été fournie à appendUICommands.")
            return

        # Ajouter les commandes au menu
        for uiCommand in uiCommands:
            if uiCommand is None:
                # None : Ajoute un séparateur.
                # self.AppendSeparator()
                self.add_separator()
                log.debug("UICommandContainerMixin.appendUICommands : ajoute un séparateur !")
                # self.add_separator()
            elif isinstance(uiCommand, tuple):
                # tuple : Crée un sous-menu et y ajoute les commandes UI.
                menuTitle, menuUICommands = uiCommand[0], uiCommand[1:]
                log.debug(f"UICommandContainerMixin.appendUICommands : ajoute le sous-menu {menuTitle} avec une liste de commandes {menuUICommands}!")
                self.appendSubMenuWithUICommands(menuTitle, menuUICommands)
            else:
                # Autre (supposé être une instance de UICommand) : ajoute la commande.
                self.appendUICommand(uiCommand)
                log.debug(f"UICommandContainerMixin.appendUICommands : ajoute la commande {uiCommand} !")

            # fileopen_command = uicommand.FileOpen(iocontroller=self._iocontroller)
            # fileopen_command.addToMenu(self, parent_window)

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        """
        Cette méthode crée un nouveau menu Tkinter,
        l'ajoute comme sous-menu au menu actuel,
        puis appelle récursivement subMenu.appendUICommands()
        pour ajouter les commandes au sous-menu.

        Args :
            menuTitle : Nom du sous-menu à créer.
            uiCommands : Liste des commandes à y ajouter.
        """
        # Pour éviter une importation circulaire, nous supposons
        # que la classe Menu est disponible dans taskcoachlib.guitk
        from taskcoachlib.guitk import menutk
        if not hasattr(self, '_window') or self._window is None:
            log.warning("UICommandContainerMixin.appendSubMenuWithUICommands : l'attribut _window est manquant ou None.")
            return

        subMenu = menutk.Menu(self._window, tearoff=0)
        # self.add_cascade(label=menuTitle, menu=subMenu)
        self._window.add_cascade(label=menuTitle, menu=subMenu)
        subMenu.appendUICommands(*uiCommands)

    def appendUICommand(self, uiCommand):
        """
        Ajoute une seule commande UI au conteneur.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        raise NotImplementedError("La méthode 'appendUICommand' doit être implémentée par la classe qui utilise ce mixin.")

    def add_separator(self):
        """
        Ajoute un séparateur.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        self.add_separator()
        # raise NotImplementedError("La méthode 'AppendSeparator' doit être implémentée par la classe qui utilise ce mixin.")

    # def add_cascade(self, label, menu):
    #     """
    #     Ajoute un sous-menu.
    #     Cette méthode doit être implémentée par la classe qui utilise ce mixin.
    #     """
    #     # Menu.add_cascade(self, label=label, menu=menu)
    #     from taskcoachlib.guitk import menutk
    #     menutk.Menu.add_cascade(self, label=label, menu=menu)
    #     # raise NotImplementedError("La méthode 'add_cascade' doit être implémentée par la classe qui utilise ce mixin.")
