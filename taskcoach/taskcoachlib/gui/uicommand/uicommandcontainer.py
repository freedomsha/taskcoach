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


class UICommandContainerMixin(object):
    """ Mélange avec la (sous-)classe wx.Menu ou wx.ToolBar.
    """

    def appendUICommands(self, *uiCommands):
        """ Ajout de *uiCommand. """
        for uiCommand in uiCommands:
            if uiCommand is None:
                self.AppendSeparator()
            elif isinstance(uiCommand, int):  # Toolbars only
                self.AppendStretchSpacer(uiCommand)
            # elif isinstance(uiCommand, (str, str)):
            elif isinstance(uiCommand, str):
                # Ajoute un élément dans le menu
                label = wx.MenuItem(self, text=uiCommand)
                # must append item before disable to insure
                # that internal object exists
                # self.AppendItem(label)
                self.Append(label)
                label.Enable(False)
            # elif isinstance(type(uiCommand), type()):  # This only works for menu's
            # TODO revenir sur mon choix:
            # elif isinstance(uiCommand, type):
            # ou garder celui de rainfornight :
            elif type(uiCommand) == type(()):
                menuTitle, menuUICommands = uiCommand[0], uiCommand[1:]
                self.appendSubMenuWithUICommands(menuTitle, menuUICommands)
            else:
                self.appendUICommand(uiCommand)

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        from taskcoachlib.gui import menu
        subMenu = menu.Menu(self._window)
        self.appendMenu(menuTitle, subMenu)
        subMenu.appendUICommands(*uiCommands)  # pylint: disable=W0142
