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

# from builtins import object
import wx
from taskcoachlib import operating_system
from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _

''' User interface commands (subclasses of UICommand) are actions that can
    be invoked by the user via the user interface (menu's, toolbar, etc.).
    See the Taskmaster pattern described here:
    http://www.objectmentor.com/resources/articles/taskmast.pdf
'''  # pylint: disable=W0105


class UICommand(object):
    """
    Commande d'interface utilisateur de base.

    Une UICommand est une action qui peut être associée à des menus ou des barres d'outils.
    Elle contient le texte du menu, l'aide contextuelle à afficher, et gère les événements
    wx.EVT_UPDATE_UI. Les sous-classes doivent implémenter la méthode doCommand() et peuvent
    remplacer enabled() pour personnaliser l'activation des commandes.

    Attributs :
        menuText (str): Texte du menu.
        helpText (str): Texte d'aide.
        bitmap (str): Icône à afficher pour l'élément de menu ou la barre d'outils.
        bitmap2 (str): Icône secondaire pour les éléments de type ITEM_CHECK.
        kind (wx.ItemKind): Type d'élément (normal, checkable, etc.).
        id (int): Identifiant unique pour l'élément.
        toolbar (wx.ToolBar): Barre d'outils associée.
        menuItems (list): Liste des éléments de menu auxquels cette commande est associée.
    """

    def __init__(self, menuText="", helpText="", bitmap="nobitmap",
                 kind=wx.ITEM_NORMAL, id=None, bitmap2=None,
                 *args, **kwargs):  # pylint: disable=W0622
        """
        Initialise la commande d'interface utilisateur.

        Args:
            menuText (str, optionnel): Le texte à afficher dans le menu. Par défaut à "".
            helpText (str, optionnel): Le texte d'aide contextuelle. Par défaut à "".
            bitmap (str, optionnel): L'icône du menu ou de la barre d'outils. Par défaut à "nobitmap".
            kind (wx.ItemKind, optionnel): Le type d'élément (normal, checkable, etc.). Par défaut à wx.ITEM_NORMAL.
            id (int, optionnel): L'identifiant de la commande. Si non spécifié, un identifiant unique sera généré.
            bitmap2 (str, optionnel): Icône secondaire pour les éléments checkables. Par défaut à None.
        """
        super().__init__()
        # menuText = menuText or '<%s>' % _('None')
        menuText = menuText or "<%s>" % _("None")
        # menuText = menuText or f"<{_("None")}>"
        # self.menuText = menuText if '&' in menuText else '&' + menuText
        self.menuText = menuText if "&" in menuText else "&" + menuText
        # self.menuText = menuText if "&" in menuText else f"&{menuText}"
        self.helpText = helpText
        self.bitmap = bitmap
        self.bitmap2 = bitmap2
        self.kind = kind
        self.id = IdProvider.get()  # Obtient un identifiant unique
        self.toolbar = None
        self.menuItems = []  # Les UIcommandes peuvent être utilisées dans plusieurs menus

    def __del__(self):
        """ Libère l'identifiant lors de la destruction de l'objet. """
        IdProvider.put(self.id)

    def __eq__(self, other):
        return self is other

    def uniqueName(self):
        """ Retourne le nom unique de la classe de commande. """
        return self.__class__.__name__

    def accelerators(self):
        # The ENTER and NUMPAD_ENTER keys are treated differently between platforms...
        if "\t" in self.menuText and (
            "ENTER" in self.menuText or "RETURN" in self.menuText
        ):
            flags = wx.ACCEL_NORMAL
            for key in self.menuText.split("\t")[1].split("+"):
                if key == "Ctrl":
                    flags |= (
                        wx.ACCEL_CMD
                        if operating_system.isMac()
                        else wx.ACCEL_CTRL
                    )
                elif key in ["Shift", "Alt"]:
                    flags |= dict(Shift=wx.ACCEL_SHIFT, Alt=wx.ACCEL_ALT)[key]
                else:
                    assert key in ["ENTER", "RETURN"], key
            return [(flags, wx.WXK_NUMPAD_ENTER, self.id)]
        return []

    def addToMenu(self, menu, window, position=None):
        """ Ajoute un sous-menu au Menu menu dans la fenêtre window à la fin en principe.

        Args:
            menu (wx.Menu): Le menu auquel ajouter la commande.
            window (wx.Window): La fenêtre parent associée.
            position (int, optionnel): La position dans le menu. Si non spécifiée, la commande est ajoutée à la fin.

        Returns:
            int: L'identifiant de l'élément de menu ajouté.
        """
        # Un menuItem représente un élément dans un menu.
        # menuItem = wx.MenuItem(menu, self.id, self.menuText, self.helpText, self.kind)
        # test de chatGPT
        # print(f"tclib.gui.uicommand.base_uicommand essaye d'ajouter le sous-menu {self} dans le menu {menu} de la fenêtre {window} à la position {position}")
        try:
            menuItem = wx.MenuItem(menu, self.id, self.menuText, self.helpText, self.kind)
        except wx._core.wxAssertionError as e:
            # print(f"tclib.gui.uicommand.base_uicommand: Error creating MenuItem: {e}")
            # Handle the error or create a new ID manually
            # new_id = wx.NewIdRef().GetId()
            new_id = wx.ID_ANY
            menuItem = wx.MenuItem(menu, new_id, self.menuText, self.helpText, self.kind)
            return menu.Append(menuItem)
        self.menuItems.append(menuItem)
        self.addBitmapToMenuItem(menuItem)
        if position is None:
            # menu.AppendItem(menuItem)
            menu.Append(menuItem)
        else:
            # menu.InsertItem(position, menuItem)
            menu.Insert(position, menuItem)
        self.bind(window, self.id)
        return self.id

    def addBitmapToMenuItem(self, menuItem):
        """
        Ajoute une icône à l'élément de menu si applicable.

        Args:
            menuItem (wx.MenuItem): L'élément de menu auquel ajouter l'icône.
        """
        if self.bitmap2 and self.kind == wx.ITEM_CHECK and not operating_system.isGTK():
            bitmap1 = self.__getBitmap(self.bitmap)
            bitmap2 = self.__getBitmap(self.bitmap2)
            menuItem.SetBitmaps(bitmap1, bitmap2)
        elif self.bitmap and self.kind == wx.ITEM_NORMAL:
            menuItem.SetBitmap(self.__getBitmap(self.bitmap))

    def removeFromMenu(self, menu, window):
        for menuItem in self.menuItems:
            if menuItem.GetMenu() == menu:
                self.menuItems.remove(menuItem)
                menuId = menuItem.GetId()
                menu.Remove(menuId)
                break
        self.unbind(window, menuId)

    def appendToToolBar(self, toolbar):
        """
        Ajoute cette commande à une barre d'outils.

        Args:
            toolbar (wx.ToolBar): La barre d'outils à laquelle ajouter la commande.

        Returns:
            int: L'identifiant de l'élément de la barre d'outils ajouté.
        """
        self.toolbar = toolbar
        bitmap = self.__getBitmap(self.bitmap, wx.ART_TOOLBAR,
                                  toolbar.GetToolBitmapSize())
        # toolbar.AddLabelTool(self.id, '',
        #               bitmap, wx.NullBitmap, self.kind,
        #               shortHelp=wx.MenuItem.GetLabelFromText(self.menuText),
        #               longHelp = self.helpText)
        toolbar.AddLabelTool(self.id, "",
                             bitmap, wx.NullBitmap, self.kind,
                             shortHelp=wx.MenuItem.GetLabelText(self.menuText),
                             longHelp=self.helpText)
        self.bind(toolbar, self.id)
        return self.id

    def bind(self, window, itemId):
        """
        Lie la commande aux événements de menu ou de barre d'outils.

        Args:
            window (wx.Window): La fenêtre à laquelle lier les événements.
            itemId (int): L'identifiant de l'élément de menu ou de barre d'outils.
        """
        window.Bind(wx.EVT_MENU, self.onCommandActivate, id=itemId)
        window.Bind(wx.EVT_UPDATE_UI, self.onUpdateUI, id=itemId)

    def unbind(self, window, itemId):
        for eventType in [wx.EVT_MENU, wx.EVT_UPDATE_UI]:
            window.Unbind(eventType, id=itemId)

    def onCommandActivate(self, event, *args, **kwargs):
        """ For Menu's and ToolBars, activating the command is not
            possible when not enabled, because menu items and toolbar
            buttons are disabled through onUpdateUI. For other controls such
            as the ListCtrl and the TreeCtrl the EVT_UPDATE_UI event is not
            sent, so we need an explicit check here. Otherwise hitting return
            on an empty selection in the ListCtrl would bring up the
            TaskEditor. """
        if self.enabled(event):
            return self.doCommand(event, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.onCommandActivate(*args, **kwargs)

    def doCommand(self, event):
        """
        Méthode à implémenter dans les sous-classes pour exécuter la commande.

        Args:
            event (wx.Event): L'événement déclenchant la commande.

        Raises:
            NotImplementedError: Si non implémenté dans la sous-classe.
        """
        raise NotImplementedError  # pragma: no cover

    def onUpdateUI(self, event):
        event.Enable(bool(self.enabled(event)))
        if self.toolbar and (not self.helpText or self.menuText == "?"):
            self.updateToolHelp()

    def enabled(self, event):  # pylint: disable=W0613
        """
        Détermine si la commande est activée.

        Peut être remplacé dans une sous-classe.

        Args:
            event (wx.Event): L'événement wx lié.

        Returns:
            bool: True si la commande est activée, sinon False.
        """
        return True

    def updateToolHelp(self):
        if not self.toolbar:
            return  # Not attached to a toolbar or it's hidden
        # shortHelp = wx.MenuItem.GetLabelFromText(self.getMenuText())
        shortHelp = wx.MenuItem.GetLabelText(self.getMenuText())
        if shortHelp != self.toolbar.GetToolShortHelp(self.id):
            self.toolbar.SetToolShortHelp(self.id, shortHelp)
        longHelp = self.getHelpText()
        if longHelp != self.toolbar.GetToolLongHelp(self.id):
            self.toolbar.SetToolLongHelp(self.id, longHelp)

    def updateMenuText(self, menuText):
        self.menuText = menuText
        if operating_system.isWindows():
            for menuItem in self.menuItems[:]:
                menu = menuItem.GetMenu()
                pos = menu.GetMenuItems().index(menuItem)
                newMenuItem = wx.MenuItem(menu, self.id, menuText, self.helpText, self.kind)
                self.addBitmapToMenuItem(newMenuItem)
                menu.DeleteItem(menuItem)
                self.menuItems.remove(menuItem)
                self.menuItems.append(newMenuItem)
                menu.InsertItem(pos, newMenuItem)
        else:
            for menuItem in self.menuItems:
                menuItem.SetItemLabel(menuText)

    # @staticmethod
    def mainWindow(self):
        return wx.GetApp().TopWindow

    def getMenuText(self):
        return self.menuText

    def getHelpText(self):
        return self.helpText

    # @staticmethod
    def __getBitmap(self, bitmapName, bitmapType=wx.ART_MENU, bitmapSize=(16, 16)):
        """
        Obtient une icône bitmap à partir du nom spécifié.

        Args:
            bitmapName (str): Le nom de l'icône.
            bitmapType (wx.ArtID, optionnel): Le type d'icône (menu, barre d'outils). Par défaut à wx.ART_MENU.
            bitmapSize (tuple, optionnel): La taille de l'icône. Par défaut à (16, 16).

        Returns:
            wx.Bitmap: L'icône bitmap obtenue, ou wx.NullBitmap en cas d'erreur.
        """
        # return wx.ArtProvider.GetBitmap(bitmapName, bitmapType, bitmapSize)
        try:
            return wx.ArtProvider.GetBitmap(bitmapName, bitmapType, bitmapSize)
        except Exception as e:
            print(f"tclib.gui.uicommand.base_uicommand: Error getting bitmap: {e}")
            return wx.NullBitmap
