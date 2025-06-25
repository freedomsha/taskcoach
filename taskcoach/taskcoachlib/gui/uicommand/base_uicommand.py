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
import logging
import types
import wx

from typing import Optional
# artprovider ?
from taskcoachlib import operating_system
from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _

log = logging.getLogger(__name__)

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
        menuText (str) : Texte du menu.
        helpText (str) : Texte d'aide.
        bitmap (str) : Icône à afficher pour l'élément de menu ou la barre d'outils.
        bitmap2 (str) : Icône secondaire pour les éléments de type ITEM_CHECK.
        kind (wx.ItemKind) : Type d'élément (normal, checkable, etc.).
        id (int) : Identifiant unique pour l'élément.
        toolbar (wx.ToolBar) : Barre d'outils associée.
        menuItems (list) : Liste des éléments de menu auxquels cette commande est associée.
    """

    def __init__(self, menuText="", helpText="", bitmap="nobitmap",
                 kind=wx.ITEM_NORMAL, id=None, bitmap2=None,
                 *args, **kwargs):  # pylint: disable=W0622
        """
        Initialise la commande d'interface utilisateur.

        Args :
            menuText (str, optionnel) : Le texte à afficher dans le menu. Par défaut à "".
            helpText (str, optionnel) : Le texte d'aide contextuelle. Par défaut à "".
            bitmap (str, optionnel) : L'icône du menu ou de la barre d'outils. Par défaut à "nobitmap".
            kind (wx.ItemKind, optionnel) : Le type d'élément (normal, checkable, etc.). Par défaut à wx.ITEM_NORMAL.
            id (int, optionnel) : L'identifiant de la commande. Si non spécifié, un identifiant unique sera généré.
            bitmap2 (str, optionnel) : Icône secondaire pour les éléments checkables. Par défaut à None.
        """
        super().__init__()
        # Le texte à afficher dans le menu (Par défaut à "") :
        menuText = menuText or '<%s>' % _('None')
        # menuText = menuText or "<%s>" % _("None")
        # menuText = menuText or f"<{_('None')}>"
        self.menuText = menuText if '&' in menuText else '&' + menuText
        # self.menuText = menuText if "&" in menuText else "&" + menuText
        # self.menuText = menuText if "&" in menuText else f"&{menuText}"
        # Le texte d'aide contextuelle (Par défaut à "") :
        self.helpText = helpText
        # L'icône du menu ou de la barre d'outils (Par défaut à "nobitmap".) :
        self.bitmap = bitmap
        # Icône secondaire pour les éléments checkables (Par défaut à None) :
        self.bitmap2 = bitmap2
        # Le type d'élément (normal, checkable, etc., Par défaut à wx.ITEM_NORMAL) :
        self.kind = kind
        # L'identifiant de la commande. Si non spécifié, un identifiant unique sera généré.
        self.id = IdProvider.get()  # Obtient un identifiant unique
        # self.id = wx.ID_ANY  # Obtient un identifiant unique
        # log.info(f"UICommand.__init__ : initialise {self} avec l'id {self.id}.")
        # self.id = id  # Obtient un identifiant unique
        #
        self.toolbar = None
        #
        self.menuItems = []  # Les UIcommandes peuvent être utilisées dans plusieurs menus
        # Ajouter un dictionnaire interne pour stocker les paramètres supplémentaires
        self._kwargs = kwargs

    def __del__(self):  # Non utilisé !?
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
        # def addToMenu(self, menu: wx.Menu, window, position=None) -> int:
        """ Ajoute un sous-menu au Menu menu dans la fenêtre window à la fin en principe.

        **Responsabilité** :
        Cette méthode est responsable de la création et de l'ajout d'un wx.MenuItem
        au wx.Menu spécifié. Elle gère également l'association de ce menu item
        à la fenêtre et potentiellement à une position spécifique.

        Args :
            menu (wx.Menu) : Le menu parent auquel ajouter la commande.
            window (wx.Window) : La fenêtre parent associée.
            position (int, optionnel) : La position dans le menu. Si non spécifiée, la commande est ajoutée à la fin.

        Returns :
            (int) : L'identifiant de l'élément de menu ajouté.
        """
        # Erreurs lors de la création de wx.MenuItem :
        #  La gestion de RuntimeError dans addToMenu pourrait
        #  indiquer des problèmes occasionnels lors de la création des éléments de menu.
        #  Bien qu'un nouvel ID soit tenté,
        #  il serait préférable de comprendre la cause de cette erreur initiale.

        # Un menuItem représente un élément dans un menu.
        # menuItem = wx.MenuItem(menu, self.id, self.menuText, self.helpText, self.kind)
        # test de chatGPT
        # print(f"tclib.gui.uicommand.base_uicommand essaye d'ajouter le sous-menu {self} dans le menu {menu} de la fenêtre {window} à la position {position}")
        # Ajouter une assertion pour vérifier que le menu existe

        #  Si la window passée à addToMenu et bind n'est pas la fenêtre
        #  qui contient réellement le menu ou qui est responsable de
        #  la gestion des événements pour ce menu, les mises à jour de
        #  l'interface utilisateur (activation/désactivation)
        #  pourraient ne pas fonctionner correctement,
        #  et les actions de menu pourraient ne pas être déclenchées.
        # assert isinstance(menu, wx.Menu), "Le premier argument doit être un objet wx.Menu"
        # assert isinstance(menu, wx.Menu), f"[BUG] Le premier argument de addToMenu doit être un wx.Menu, pas {type(menu)}"
        assert isinstance(menu, wx.Menu), f"[BUG] addToMenu() appelé avec un mauvais argument : type(menu) = {type(menu)} — nom={getattr(menu, '__name__', str(menu))}"
        assert not isinstance(menu, types.ModuleType), "[ERREUR CRITIQUE] Un module a été passé au lieu d'un wx.Menu !"

        # try:
        # log.debug("UICommand.addToMenu crée un objet menuItem.")
        # log.debug(f"💥UICommand.addToMenu essaye d'ajouter le sous-menu {self.menuText} d'ID={self.id} dans le menu {menu} de la fenêtre {window} à la position {position}.")
        # try:
        menuItem = wx.MenuItem(menu, self.id, self.menuText, self.helpText, self.kind)  # Ligne clé
        # Est-ce que ce serait plutôt self.menuItem = ?
        # except Exception as e:
        #     log.error("UICommand.addToMenu : ", e, exc_info=True)
        # Un nouvel objet wx.MenuItem (de la bibliothèque wxPython) est créé.
        # L'identifiant de ce nouvel élément de menu est crucial. Il est passé en argument lors de la création du wx.MenuItem :
        #
        #     self.id : C'est l'identifiant de la commande UI (UICommand).
        #     Ce n'est pas un ID généré par wxPython, mais un ID
        #     qui est censé avoir été défini dans la classe dérivée de UICommand
        #     (par exemple, dans une sous-classe comme UICheckCommand).
        # Sauf qu'il retourne -1. !

        log.debug(f"UICommand.addToMenu a enregistré le sous-menu {type(self).__name__} dans le menu {type(menu).__name__} avec les valeurs d'ID={self.id}, text={self.menuText}, help={self.helpText} et kind={self.kind}")

        # Les arguments importants ici sont :
        #     menu : Le menu parent auquel l'élément est ajouté.
        #     self.id : L'identifiant de la commande.
        #               C'est cet ID qui est utilisé pour lier les événements.
        #               Assurez-vous que self.id est correctement initialisé dans les classes dérivées de UICommand.
        #     self.menuText : Le texte affiché dans le menu.
        #                     Vérifiez que self.menuText est correctement défini dans vos classes UICommand.
        #     self.helpText : Le texte d'aide affiché dans la barre d'état.
        #     self.kind : Le type de l'élément de menu (wx.ITEM_NORMAL, wx.ITEM_CHECK, wx.ITEM_RADIO).
        #                 Assurez-vous que self.kind est correctement défini dans vos classes UICommand
        #                 en fonction du type d'élément de menu souhaité.
        # except wx._core.wxAssertionError as e:
        #     # except wx.wxAssertionError as e:
        #     # except RuntimeError as e:
        #     # print(f"tclib.gui.uicommand.base_uicommand.addToMenu : Error creating MenuItem: {e}")
        #     log.error(f"addToMenu : Error creating MenuItem with ID {self.id}: {e}", exc_info=True)
        #     # Handle the error or create a new ID manually
        #     # new_id = wx.NewIdRef().GetId()
        #     new_id = wx.ID_ANY
        #     menuItem = wx.MenuItem(menu, new_id, self.menuText, self.helpText, self.kind)
        #     # return menu.Append(menuItem)  # ?

        # log.debug(f"UICommand.addToMenu : Ajoute l'élément {menuItem} à la fin du menuItems {self.menuItems}.")
        self.menuItems.append(menuItem)
        self.addBitmapToMenuItem(menuItem)
        # L'élément de menu est ajouté à la fin du menu ou à une position spécifiée.
        if position is None:
            log.debug(f"UICommand.addToMenu : Ajoute l'élément menuItem={type(menuItem).__name__} {type(self).__name__} dans le menu={type(menu).__name__}.")
            menu.AppendItem(menuItem)  # wxPyDeprecationWarning: Call to deprecated item. Use Append instead.
            # AppendItem est dans customTreeCtrl
            # menu.Append(menuItem)
        else:
            log.debug(f"UICommand.addToMenu : Ajoute l'élément {type(menuItem).__name__} {type(self).__name__} dans le menu {type(menu).__name__}(position={position}).")
            menu.InsertItem(position, menuItem)  # TODO: choisir entre les deux
            # menu.Insert(position, menuItem)
        # Liaison des événements :
        # log.info(f"UICommand.addToMenu : Commande {self} d'ID={self.id} exécutée dans la fenêtre {window}")
        self.bind(window, self.id)  # Lie la commande aux événements de menu ou de barre d'outils.
        # self.bind(self, window, self.id)  # Lie la commande aux événements de menu ou de barre d'outils.
        # Cette ligne est cruciale.
        # Elle lie la commande (self) aux événements de menu (wx.EVT_MENU)
        # sur la window spécifiée, en utilisant l'ID de la commande (self.id).
        # TODO : Assurez-vous que window est la fenêtre correcte
        # et que la méthode bind est correctement implémentée dans la classe UICommand
        # (elle n'est pas montrée ici). Si la liaison ne se fait pas correctement,
        # les actions de menu ne seront pas traitées.
        # Retour de l'ID :
        return self.id
        # En Résumé, En clair :
        #     L'ID de l'élément de menu n'est pas généré par wx.MenuItem ou par menu.AppendItem/menu.InsertItem.
        #     L'ID est déterminé par la classe qui hérite de UICommand.
        #     C'est cette classe (par exemple, UICheckCommand) qui doit
        #     s'assurer que self.id a une valeur correcte et unique.
        #     UICommand.addToMenu prend cet ID fourni, le transmet à wxPython lors de la création du wx.MenuItem, et le retourne.

    def addBitmapToMenuItem(self, menuItem) -> None:
        """
        Ajoute une icône à l'élément de menu si applicable.

        Args :
            menuItem (wx.MenuItem) : L'élément de menu auquel ajouter l'icône.
        """
        # Problèmes spécifiques à la plateforme (GTK) :
        #  La condition not operating_system.isGTK() dans addBitmapToMenuItem
        #  suggère qu'il pourrait y avoir des différences
        #  dans la gestion des bitmaps pour les éléments cochables sur GTK.
        #  Si vous utilisez GTK, cela pourrait être un point à examiner.
        if self.bitmap2 and self.kind == wx.ITEM_CHECK and not operating_system.isGTK():
            bitmap1 = self.__getBitmap(self.bitmap)
            bitmap2 = self.__getBitmap(self.bitmap2)
            menuItem.SetBitmaps(bitmap1, bitmap2)
        elif self.bitmap and self.kind == wx.ITEM_NORMAL:
            menuItem.SetBitmap(self.__getBitmap(self.bitmap))

    def removeFromMenu(self, menu, window) -> None:
        for menuItem in self.menuItems:
            if menuItem.GetMenu() == menu:
                self.menuItems.remove(menuItem)
                menuId = menuItem.GetId()
                menu.Remove(menuId)
                break
        self.unbind(window, menuId)
        # for menuItem in self.menuItems:
        #     if menuItem.GetMenu() == menu:
        #         self.menuItems.remove(menuItem)
        #         menuId = menuItem.GetId()
        #         menu.Remove(menuId)
        #         self.unbind(window, menuId)
        #         # break

    def appendToToolBar(self, toolbar):
        """
        Ajoute cette commande à une barre d'outils.

        Args :
            toolbar (wx.ToolBar) : La barre d'outils à laquelle ajouter la commande.

        Returns :
            (int) : L'identifiant de l'élément ajouté à la barre d'outils.
        """
        self.toolbar = toolbar
        bitmap = self.__getBitmap(self.bitmap, wx.ART_TOOLBAR,
                                  toolbar.GetToolBitmapSize())
        # wx.ToolBar.AddLabelTool est une vielle méthode pour ajouter un outil à une barre d'outils.
        # wx.ToolBar.AddTool semble être la norme. Voir aussi CreateTool, AddRadioTool
        # Ne pas oublier d'utiliser Realize après avoir ajouté les outils pour faire apparaître les outils !
        # toolbar.AddLabelTool(self.id, '',
        #               bitmap, wx.NullBitmap, self.kind,
        #               shortHelp=wx.MenuItem.GetLabelFromText(self.menuText),
        #               longHelp = self.helpText)
        # C'est ici que `UICommand` appelle directement `toolbar.AddTool()`.
        # Les arguments `shortHelp` et `longHelp` sont explicitement passés.
        toolbar.AddTool(self.id,
                        "",
                        bitmap,
                        wx.NullBitmap,  # crée un problème dans toolbar.py AddLabelTool, AddTool ne supporte pas les NoneType !
                        self.kind,
                        wx.MenuItem.GetLabelText(self.menuText),
                        self.helpText,
                        None,
                        None)
        self.bind(toolbar, self.id)
        # self.bind(self, toolbar, self.id)
        return self.id

    def bind(self, window, itemId) -> None:
        """
        Lie la commande aux événements de menu ou de barre d'outils.

        Args :
            window (wx.Window | wx.Frame) : La fenêtre à laquelle lier les événements.
            itemId (int) : L'identifiant de l'élément de menu ou de barre d'outils.
        """
        # TODO : Comprenez comment la méthode bind() dans votre classe UICommand
        #  (ou sa base) lie l'événement de menu à une action.
        #  Assurez-vous que la window passée à addToMenu()
        #  est celle qui doit gérer les événements.
        window.Bind(wx.EVT_MENU, self.onCommandActivate, id=itemId)
        window.Bind(wx.EVT_UPDATE_UI, self.onUpdateUI, id=itemId)

    # def bind(self, window, itemId) -> None:
    #     # def bind(self, command, window, itemId) -> None:
    #     """
    #     Lie la commande aux événements de menu ou de barre d'outils.
    #
    #     Args :
    #         command : La commande à passer.
    #         window (wx.Window) : La fenêtre à laquelle lier les événements.
    #         itemId (int) : L'identifiant de l'élément de menu ou de barre d'outils.
    #     """
    #     window.Bind(wx.EVT_MENU, self.onCommandActivate, id=itemId)
    #     # window.Bind(wx.EVT_MENU, command.onCommandActivate, source=window, id=itemId)
    #     window.Bind(wx.EVT_UPDATE_UI, self.onUpdateUI, id=itemId)
    #     # window.Bind(wx.EVT_UPDATE_UI, command.onUpdateUI, source=window, id=itemId)

    def unbind(self, window, itemId):
        for eventType in [wx.EVT_MENU, wx.EVT_UPDATE_UI]:
            window.Unbind(eventType, id=itemId)

    # def onCommandActivate(self, event, *args, **kwargs):
    def onCommandActivate(self, event: wx.Event, *args, **kwargs):
        """ For Menu's and ToolBars, activating the command is not
            possible when not enabled, because menu items and toolbar
            buttons are disabled through onUpdateUI. For other controls such
            as the ListCtrl and the TreeCtrl the EVT_UPDATE_UI event is not
            sent, so we need an explicit check here. Otherwise hitting return
            on an empty selection in the ListCtrl would bring up the
            TaskEditor. """
        if self.enabled(event):
            # return self.doCommand(event, *args, **kwargs)
            try:
                # return self.doCommand(event, *args, **kwargs)
                return self.doCommand(event)
            except Exception as e:
                # Gestion de l'exception (par exemple, afficher un message d'erreur)
                log.error(f"tclib.gui.uicommand.base_uicommand: Error executing command: {e}", exc_info=True)
                wx.MessageBox(f"tclib.gui.uicommand.base_uicommand: An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def __call__(self, *args, **kwargs):
        return self.onCommandActivate(*args, **kwargs)

    def doCommand(self, event):
        # def doCommand(self, event, *args, **kwargs):
        """
        Méthode à implémenter dans les sous-classes pour exécuter la commande.

        Args :
            event (wx.Event) : L'événement déclenchant la commande.

        Raises :
            NotImplementedError : Si non implémenté dans la sous-classe.
        """
        # *args : Arguments supplémentaires.
        # **kwargs : Arguments nommés supplémentaires.
        # Accéder aux paramètres supplémentaires via self._kwargs
        # ...
        raise NotImplementedError  # pragma: no cover

    def onUpdateUI(self, event) -> None:
        event.Enable(bool(self.enabled(event)))
        if self.toolbar and (not self.helpText or self.menuText == "?"):
            self.updateToolHelp()

    def enabled(self, event):  # pylint: disable=W0613
        """
        Détermine si la commande est activée.

        Peut être remplacé dans une sous-classe.

        Args :
            event (wx.Event) : L'événement wx lié.

        Returns :
            (bool) : True si la commande est activée, sinon False.
        """
        return True
        # Ajouter des vérifications supplémentaires en fonction des besoins
        # return super().enabled(event)  # Améliore la réactivité

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
        log.debug(f"UICommand.mainWindow appelé par self={self} pour retourner wx.App.TopWindow : {wx.GetApp().TopWindow}{repr(wx.GetApp().TopWindow)}.")
        return wx.GetApp().TopWindow

    def getMenuText(self):
        return self.menuText

    def getHelpText(self):
        return self.helpText

    # @staticmethod
    def __getBitmap(self, bitmapName, bitmapType=wx.ART_MENU, bitmapSize=(16, 16)):
        # def __getBitmap(self, bitmapName: str, bitmapType: wx.ArtID = wx.ART_MENU,
        #                     bitmapSize: tuple = (16, 16)) -> wx.Bitmap:
        # module 'wx' has no attribute 'ArtID'
        """
        Obtient une icône bitmap à partir du nom spécifié.

        Args :
            bitmapName (str) : Le nom de l'icône.
            bitmapType (wx.ArtID, optionnel) : Le type d'icône (menu, barre d'outils). Par défaut à wx.ART_MENU.
            bitmapSize (tuple, optionnel) : La taille de l'icône. Par défaut à (16, 16).

        Returns :
            (wx.Bitmap) : L'icône bitmap obtenue, ou wx.NullBitmap en cas d'erreur.

        Raises :
            FileNotFoundError : Si l'icône n'est pas trouvée.
        """
        # return wx.ArtProvider.GetBitmap(bitmapName, bitmapType, bitmapSize)
        # Problèmes de Chemin ou de Nom d'Icône dans __getBitmap :
        #  Si les noms de fichiers spécifiés dans l'attribut bitmap
        #  des instances de UICommand sont incorrects
        #  ou si les icônes ne sont pas trouvées par wx.ArtProvider,
        #  les icônes des menus n'apparaîtront pas.
        #  L'exception FileNotFoundError levée ici pourrait indiquer un tel problème.
        #  Vérifiez les logs pour voir si cette erreur se produit.
        log.debug(f"UICommand.__getBitmap() appelé avec self=(self.uniqueName={self.uniqueName()} bitmapName={bitmapName}, bitmapType={bitmapType} et bitmapSize={bitmapSize}")
        try:
            return wx.ArtProvider.GetBitmap(bitmapName, bitmapType, bitmapSize)
            # return artprovider.ArtProvider.GetBitmap(bitmapName, bitmapType, bitmapSize)
        except Exception as e:
            print(f"tclib.gui.uicommand.base_uicommand: Error getting bitmap: {e}")
            logging.error(f"UICommand.__getBitmap : Error loading bitmap '{bitmapName}': {str(e)}")
            raise FileNotFoundError(f"Bitmap '{bitmapName}' not found")
            return wx.NullBitmap
