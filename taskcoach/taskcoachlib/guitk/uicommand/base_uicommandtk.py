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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# J'ai remplacé les éléments spécifiques à wxPython par leurs équivalents dans tkinter :
#     wx a été remplacé par tkinter.
#
#     wx.EVT_MENU et wx.EVT_UPDATE_UI n'existent pas directement.
#     J'ai utilisé l'option command de tkinter.Menu.add_command et
#     de tkinter.Button pour lier les actions.
#
#     wx.ArtProvider.GetBitmap a été remplacé par une méthode __getBitmap
#     qui suppose l'existence d'une classe ArtProvider pour Tkinter.
#     Tu devras créer cette classe (tkartprovider.py)
#     qui gérera le chargement des icônes (.png, .gif, etc.) en tkinter.PhotoImage.
#
#     Les méthodes bind et unbind ont été retirées
#     car la liaison se fait directement lors de la création du widget.
#
#     J'ai fait quelques ajustements pour que la classe UICommand
#     puisse être utilisée pour créer des boutons de barre d'outils,
#     ce qui correspond à la logique de la méthode appendToToolBar.
#
# Ce code devrait te donner une base solide.
# TODO :
# Il y a quelques points à revoir, notamment la gestion des icônes (tkartprovider.py)
# et la mise à jour des labels de menu.
#
# J'ai mis à jour la méthode mainWindow() pour qu'elle tente d'obtenir
# l'instance de l'application TkinterApplication via une méthode statique getInstance().
# J'ai également importé TkinterApplication pour que la référence soit disponible.
# Ce changement permettra à la classe UICommand d'interagir correctement
# avec la fenêtre principale de l'application, en supposant que le singleton TkinterApplication
# a une référence à MainWindow.
#
# Pour que cela fonctionne, tu devras t'assurer que la classe TkinterApplication
# a une méthode de classe getInstance() qui retourne l'instance unique du singleton,
# et que cette instance a un attribut mainwindow qui référence la fenêtre principale.

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from taskcoachlib import operating_system
from taskcoachlib.guitk.artprovidertk import IconProvider, art_provider_tk
# from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.guitk.artprovidertk import ArtProvider  # Assumes you have created this
from taskcoachlib.guitk.artprovidertk import ArtProviderTk  # Assumes you have created this
# from taskcoachlib.application.tkapplication import TkinterApplication

log = logging.getLogger(__name__)

''' User interface commands (subclasses of UICommand) are actions that can
    be invoked by the user via the user interface (menu's, toolbar, etc.).
    See the Taskmaster pattern described here:
    http://www.objectmentor.com/resources/articles/taskmast.pdf
'''  # pylint: disable=W0105


class UICommand(object):
    """
    Commande d'interface utilisateur de base pour Tkinter.

    Une UICommand est une action qui peut être associée à des menus ou des barres d'outils.
    Elle contient le texte du menu, l'aide contextuelle à afficher, et gère les événements.
    Les sous-classes doivent implémenter la méthode doCommand() et peuvent
    remplacer enabled() pour personnaliser l'activation des commandes.

    Attributs :
        menuText (str) : Texte du menu.
        helpText (str) : Texte d'aide.
        bitmap (str) : Nom de l'icône à afficher.
        bitmap2 (str) : Nom de l'icône secondaire.
        kind (str) : Type d'élément (normal, checkbutton, etc.).
        id (int) : Identifiant unique pour l'élément.
        toolbar (tk.Frame) : Barre d'outils associée.
        menuItems (list) : Liste des éléments de menu auxquels cette commande est associée.
        app (tk.Tk) : L'instance principale de l'application Tkinter.
    """

    def __init__(self, menuText="", helpText="", bitmap="nobitmap",
                 kind="normal", id=None, bitmap2=None,
                 *args, **kwargs):  # pylint: disable=W0622
        super().__init__()
        # Le texte à afficher dans le menu :
        menuText = menuText or f"<{_('None')}>"
        self.menuText = menuText
        # Le texte d'aide contextuelle :
        self.helpText = helpText
        # Le nom de l'icône :
        self.bitmap = bitmap
        # Nom de l'icône secondaire pour les éléments checkables :
        self.bitmap2 = bitmap2
        # Le type d'élément (normal, checkbutton) :
        self.kind = kind
        # L'identifiant de la commande.
        # self.id = id if id is not None else IdProvider.get()
        self.id = id
        #
        self.toolbar = None
        #
        self.menuItems = []
        self._kwargs = kwargs
        # L'instance principale de l'application Tkinter
        self.app = self.mainWindow()

    def __del__(self):
        """ Libère l'identifiant lors de la destruction de l'objet. """
        # IdProvider.put(self.id)

    def __eq__(self, other):
        return self is other

    def uniqueName(self):
        """ Retourne le nom unique de la classe de commande. """
        return self.__class__.__name__

    def addToMenu(self, menu, window, position=None):
        """ Ajoute un sous-menu au Menu menu.

        Args :
            menu (tk.Menu) : Le menu parent auquel ajouter la commande.
            window (tk.Tk ou tk.Toplevel) : La fenêtre parente associée.
            position (int, optionnel) : La position dans le menu.
        """
        assert isinstance(menu, tk.Menu), f"[BUG] addToMenu() appelé avec un mauvais argument : type(menu) = {type(menu)}"

        log.debug(f"💥UICommand.addToMenu essaye d'ajouter le sous-menu {self.menuText} d'ID={self.id} dans le menu {menu} à la position {position}.")

        menu_item_options = {
            'label': self.getMenuText(),
            'command': self.onCommandActivate,
        }

        # Handle different kinds of menu items
        if self.kind == "checkbutton":
            menu_item_options['type'] = 'checkbutton'
            # You would need a variable to track the state, like a tkinter.BooleanVar
            # For now, we'll just add the command
            # TODO: Implement state variable for checkbutton
            log.warning("Tkinter checkbutton kind not fully implemented, state variable is missing.")

        # Check for bitmap and add it if available
        bitmap = self.__getBitmap(self.bitmap)
        # bitmap = ArtProviderTk.GetBitmap(self.bitmap, self)
        if bitmap:
            menu_item_options['image'] = bitmap
            menu_item_options['compound'] = 'left'

        if position is None:
            menu.add_command(**menu_item_options)
        else:
            menu.insert_command(position, **menu_item_options)

        self.menuItems.append(menu)  # Stocke la référence au menu

    def addBitmapToMenuItem(self, menuItem) -> None:
        """ Tkinter gère les icônes directement via les options du menu. """
        pass

    def removeFromMenu(self, menu):
        # Cette méthode est un peu plus complexe avec Tkinter car il n'y a pas
        # d'ID d'élément de menu à proprement parler pour le unbind.
        # Nous pouvons essayer de trouver l'index de l'élément par son texte.
        # TODO: A revoir pour une suppression plus fiable
        for i in range(menu.index('end') + 1):
            if menu.entrycget(i, 'label') == self.getMenuText():
                menu.delete(i)
                break
        if menu in self.menuItems:
            self.menuItems.remove(menu)

    def appendToToolBar(self, toolbar):
        """
        Ajoute cette commande à une barre d'outils (Frame).

        Args :
            toolbar (tk.Frame) : La barre d'outils à laquelle ajouter la commande.

        Returns :
            (int) : L'identifiant de la commande.
        """
        self.toolbar = toolbar
        bitmap = self.__getBitmap(self.bitmap)

        button_options = {
            'image': bitmap,
            'command': self.onCommandActivate,
            'bd': 0,
            'relief': 'flat',
            'padx': 5,
            'pady': 5
        }

        if self.kind == "checkbutton":
            # TODO: Implement a checkbutton for the toolbar
            log.warning("Tkinter checkbutton kind for toolbar not fully implemented.")

        if bitmap:
            button = tk.Button(toolbar, **button_options)
            button.pack(side="left", padx=2, pady=2)
            # Stocke le bouton pour la gestion de l'état
            self._kwargs['button'] = button

        return self.id

    def onCommandActivate(self, event=None):
        """ Active la commande. """
        log.info(f"onCommandActivate appelée pour {self.menuText}")
        if self.enabled():
            try:
                self.doCommand()
            except Exception as e:
                log.error(f"UICommand.onCommandActivate : Error executing command: {e}", exc_info=True)
                messagebox.showerror("Error", f"UICommand.onCommandActivate : An error occurred: {e}")
        else:
            log.warning(f"Commande {self.menuText} désactivée, donc doCommand n'est pas appelée.")

    def __call__(self, *args, **kwargs):
        self.onCommandActivate()

    def doCommand(self):
        """
        Méthode à implémenter dans les sous-classes pour exécuter la commande.
        """
        raise NotImplementedError  # pragma: no cover

    def enabled(self):
        """
        Détermine si la commande est activée.

        Peut être remplacé dans une sous-classe.

        Returns :
            (bool) : True si la commande est activée, sinon False.
        """
        return True
    
    def onUpdateUI(self, event=None) -> None:
        """Met à jour l'état d'activation du widget Tkinter."""
        # Récupère le bouton de la toolbar s'il existe
        button = self._kwargs.get('button')
    
        # Vérifie si la commande est activée
        is_enabled = bool(self.enabled(event))
    
        # Met à jour l'état du bouton de la toolbar s'il existe
        if button and isinstance(button, tk.Button):
            button.configure(state='normal' if is_enabled else 'disabled')
    
        # Met à jour les éléments de menu associés
        for menu in self.menuItems:
            if isinstance(menu, tk.Menu):
                for i in range(menu.index('end') + 1):
                    try:
                        if menu.entrycget(i, 'label') == self.getMenuText():
                            menu.entryconfigure(i, state='normal' if is_enabled else 'disabled')
                    except tk.TclError:
                        continue
    
        # Met à jour l'aide de la toolbar si nécessaire            
        if self.toolbar and (not self.helpText or self.menuText == "?"):
            self.updateToolHelp()

    def updateMenuText(self, menuText):
        self.menuText = menuText
        # Tkinter ne gère pas la mise à jour automatique des labels de menu.
        # Il faudrait recréer le menu ou trouver l'index de l'élément pour le configurer.
        # Pour simplifier, nous ne gérons pas cette fonctionnalité pour l'instant.
        log.warning("Tkinter updateMenuText is not fully implemented.")

    def updateToolHelp(self):
        """Met à jour l'aide contextuelle de la barre d'outils."""
        if not self.toolbar:
            return  # Not attached to a toolbar or it's hidden
    
        button = self._kwargs.get('button')
        if not button:
            return
        
        # Met à jour l'aide courte (tooltip)
        short_help = self.getMenuText() 
        if hasattr(button, '_short_help') and button._short_help != short_help:
            button._short_help = short_help
            button.bind('<Enter>', lambda e: self._show_tooltip(e, short_help))
            button.bind('<Leave>', lambda e: self._hide_tooltip(e))
        
        # Met à jour l'aide longue
        long_help = self.getHelpText()
        if hasattr(button, '_long_help') and button._long_help != long_help:
            button._long_help = long_help
        
    def _show_tooltip(self, event, text):
        """Affiche un tooltip avec le texte donné."""
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 25
    
        # Détruit le tooltip existant s'il y en a un
        self._hide_tooltip(event)
    
        # Crée le tooltip
        tooltip = tk.Toplevel(event.widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
    
        label = tk.Label(tooltip, text=text, 
                         justify='left',
                         background="#ffffe0", 
                         relief='solid', borderwidth=1)
        label.pack()
    
        # Stocke la référence au tooltip
        event.widget._tooltip = tooltip
    
    def _hide_tooltip(self, event):
        """Cache le tooltip."""
        widget = event.widget
        if hasattr(widget, "_tooltip"):
            widget._tooltip.destroy()
            del widget._tooltip
            
    def mainWindow(self):
        """
        Retourne l'instance principale de l'application Tkinter.

        Cette méthode utilise le singleton TkinterApplication pour obtenir
        une référence à la fenêtre principale (MainWindow).
        """
        # Cela suppose que l'instance de Tkinter a été créée ailleurs et est accessible
        # via un moyen global ou un singleton.
        # Pour l'instant, on suppose qu'il y a une instance de la classe TkinterApplication
        # quelque part. On pourrait aussi passer l'instance de root en argument.
        # TODO: Assurer l'accès à l'instance de root
        # return None  # tk.Tk()
        from taskcoachlib.application.tkapplication import TkinterApplication
        try:
            app_instance = TkinterApplication.getInstance()
            # app_instance = taskcoachlib.application.tkapplication.TkinterApplication.getInstance()
            # app_instance = app.getInstance()
            if hasattr(app_instance, 'mainwindow'):
                return app_instance.mainwindow
            return None
        except Exception:
            return None

    def getMenuText(self):
        """ Retourne le texte du menu. """
        return self.menuText

    def getHelpText(self):
        """ Retourne le texte d'aide. """
        return self.helpText

    def __getBitmap(self, bitmapName):
        """
        Obtient une icône à partir du nom spécifié en utilisant tkartprovider.

        Args :
            bitmapName (str) : Le nom de l'icône.

        Returns :
            (tk.PhotoImage) : L'icône PhotoImage obtenue, ou None en cas d'erreur.
        """
        log.debug(f"UICommand.__getBitmap() appelé avec self=(self.uniqueName={self.uniqueName()} bitmapName={bitmapName}")
        try:
            # On suppose ici que tkartprovider.py est une version de ArtProvider pour Tkinter
            # qui peut charger des images.
            # return ArtProvider.getPhotoImage(bitmapName)
            # return ArtProviderTk.GetBitmap(bitmapName)
            return artprovidertk.getIcon(bitmapName)
        except Exception as e:
            # print(f"UICommand.__getBitmap : Error getting bitmap: {e}")
            logging.error(f"UICommand.__getBitmap : Error loading bitmap '{bitmapName}': {str(e)}")
            return None

