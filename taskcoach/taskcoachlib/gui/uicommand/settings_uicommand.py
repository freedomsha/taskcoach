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

# from builtins import str
from taskcoachlib.gui.uicommand import base_uicommand
import wx


class SettingsCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """ SettingsCommands are saved in the settings (a ConfigParser). """

    def __init__(self, settings=None, setting=None, section="view",
                 *args, **kwargs):
        self.settings = settings
        self.section = section
        self.setting = setting
        super().__init__(*args, **kwargs)


class BooleanSettingsCommand(SettingsCommand):  # pylint: disable=W0223
    """ Bae class for commands that change a boolean setting.
        Whenever the setting is changed, the user interface
        representation is changed as well. E.g. a menu gets
        a checkmark.

        Classe Bae pour les commandes qui modifient un paramètre booléen.
        Chaque fois que le paramètre est modifié,
        la représentation de l'interface utilisateur est également modifiée.
        Par exemple. un menu est coché.
        """

    def __init__(self, value=None, *args, **kwargs):
        self.value = value
        super().__init__(*args, **kwargs)

    def onUpdateUI(self, event):
        event.Check(self.isSettingChecked())
        super().onUpdateUI(event)

    def addToMenu(self, menu, window, position=None):
        # def addToMenu(self, menu, window, position=None) -> int:
        """ Ajouter un sous_menu au menu"""
        # print(f"tclib.gui.uicommand.setings_uicommand.py BooleanSettingCommand.addToMenu essaie d'ajouter: self =",
        #      repr(self), " au",
        #      f"menu: {menu} dans window: {window}")
        menuId = super().addToMenu(menu, window, position)

        # print(f'menuId: {menuId} ajouté' )
        # print(f'au menu: {menu} window: {window} position: {position}')
        # menuId: <wx._core.MenuItem object at 0x7f9bffc23ec0>
        # ce devrait être un nombre entier !

        # print(f"essaie try FindItemById de {menuId}")
        menuItem = menu.FindItemById(menuId)
        # print(f"résultat: menuItem: {menuItem}")
        # print(f"vérification de menuItem: {menuItem} avec {self.isSettingChecked}")
        if menuItem is not None:
            # menuItem.Check(self.isSettingChecked())
            try:
                menuItem.Check(self.isSettingChecked())
            except TypeError as e:
                # menuItem = menu.FindItemById(menuId)  # ?
                print(f"tclib.gui.uicommand.settings_uicommand l75: Error d'ajout de UI command au menu: {e}")
                # TypeError: Menu.FindItemById(): argument 1 has unexpected type 'MenuItem'
        else:
            # Gérer le cas où menuItem est None
            # print("Erreur: menuItem est None.")
            pass

        return menuId

    def isSettingChecked(self):
        raise NotImplementedError  # pragma: no cover


class UICheckCommand(BooleanSettingsCommand):
    def __init__(self, *args, **kwargs):
        kwargs["bitmap"] = kwargs.get("bitmap", self.getBitmap())
        super().__init__(kind=wx.ITEM_CHECK, *args, **kwargs)

    def isSettingChecked(self):
        return self.settings.getboolean(self.section, self.setting)

    # @staticmethod
    def _isMenuItemChecked(self, event):
        # There's a bug in wxPython 2.8.3 on Windows XP that causes
        # event.IsChecked() to return the wrong value in the context menu.
        # The menu on the main window works fine. So we first try to access the
        # context menu to get the checked state from the menu item itself.
        # This will fail if the event is coming from the window, but in that
        # case we can event.IsChecked() expect to work so we use that.
        try:
            return event.GetEventObject().FindItemById(event.GetId()).IsChecked()
        except AttributeError:
            return event.IsChecked()

    def doCommand(self, event):
        self.settings.setboolean(self.section, self.setting,
                                 self._isMenuItemChecked(event))

    # @staticmethod
    def getBitmap(self):
        # Using our own bitmap for checkable menu items does not work on
        # all platforms, most notably Gtk where providing our own bitmap causes
        # "(python:8569): Gtk-CRITICAL **: gtk_check_menu_item_set_active:
        # assertion `GTK_IS_CHECK_MENU_ITEM (check_menu_item)' failed"
        return "nobitmap"


class UIRadioCommand(BooleanSettingsCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(kind=wx.ITEM_RADIO, bitmap='',
                         *args, **kwargs)

    def onUpdateUI(self, event):
        if self.isSettingChecked():
            super().onUpdateUI(event)

    def isSettingChecked(self):
        return self.settings.get(self.section, self.setting) == str(self.value)

    def doCommand(self, event):
        self.settings.setvalue(self.section, self.setting, self.value)
