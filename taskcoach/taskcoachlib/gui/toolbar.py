"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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
"""
Ce module contient la définition de la classe ToolBar, qui représente une barre d'outils personnalisable dans l'interface utilisateur de Task Coach.

La classe ToolBar hérite de la classe AuiToolBar de la bibliothèque wxPython et utilise la classe UICommand pour définir les commandes qui apparaissent sur la barre d'outils.

La barre d'outils peut être personnalisée par l'utilisateur en utilisant le menu "Personnaliser" dans le menu "Affichage". Les choix de l'utilisateur sont enregistrés dans les préférences de l'application.

La classe MainToolBar est une sous-classe de ToolBar qui est utilisée dans la fenêtre principale de Task Coach.

La classe ToolBar est également utilisée dans les tests unitaires pour tester la fonctionnalité de la barre d'outils.
"""

# from future import standard_library

# standard_library.install_aliases()
from taskcoachlib import operating_system
# from taskcoachlib.thirdparty import aui
# import aui2 as aui
from wx.lib.agw import aui
import wx
from taskcoachlib.gui import uicommand
# from taskcoachlib.gui.uicommand import uicommandcontainer


class _Toolbar(aui.auibar.AuiToolBar):
    """
    Une classe interne qui représente une barre d'outils basée sur la classe AuiToolBar de la bibliothèque wxPython.

    Cette classe est utilisée comme base pour la classe ToolBar, qui ajoute des fonctionnalités de personnalisation à la barre d'outils.

    AuiToolBar est une barre d'outils entièrement dessinée par le propriétaire,
    parfaitement intégrée au système de mise en page AUI. Cela permet le glisser-déposer des barres d'outils,
    le comportement d'ancrage/flottant et la possibilité de définir des éléments de « débordement » dans la barre d'outils elle-même.

    Le thème par défaut utilisé est AuiDefaultToolBarArt, qui offre une apparence moderne et brillante.
    Le thème peut être modifié en appelant AuiToolBar.SetArtProvider.
    """
    def __init__(self, parent, style):
        super().__init__(parent, agwStyle=aui.AUI_TB_NO_AUTORESIZE)

    def AddLabelTool(self, id, label, bitmap1, bitmap2, kind, **kwargs):
        long_help_string = kwargs.pop("longHelp", "")
        short_help_string = kwargs.pop("shortHelp", "")
        bitmap2 = self.MakeDisabledBitmap(bitmap1)
        # TypeError: _Toolbar.MakeDisabledBitmap() takes 1 positional argument but 2 were given
        # Attention ligne 63 déclaration de MakeDisabledBitmap. Ne pas mettre staticmethod.
        super().AddTool(id, label, bitmap1, bitmap2, kind,
                        short_help_string, long_help_string, None, None)

    def GetToolState(self, toolid):
        return self.GetToolToggled(toolid)

    def SetToolBitmapSize(self, size):
        self.__size = size

    def GetToolBitmapSize(self):
        return self.__size

    def GetToolSize(self):
        return self.__size

    def SetMargins(self, *args):
        if len(args) == 2:
            super().SetMarginsXY(args[0], args[1])
        else:
            super().SetMargins(*args)

    # @staticmethod
    # def MakeDisabledBitmap(self, bitmap: wx.Bitmap) -> wx.Bitmap:
    def MakeDisabledBitmap(self, bitmap):
        """
        Crée une version en niveaux de gris d'un bitmap pour l'afficher en mode désactivé.

        Args :
            bitmap (wx.Bitmap): Le bitmap à convertir.

        Returns :
            wx.Bitmap: Le bitmap converti en niveaux de gris.
        """
        return bitmap.ConvertToImage().ConvertToGreyscale().ConvertToBitmap()


class ToolBar(_Toolbar, uicommand.UICommandContainerMixin):
    """
    Une classe qui représente une barre d'outils personnalisable dans l'interface utilisateur de Task Coach.

    Cette classe hérite de la classe _Toolbar et utilise la classe UICommand pour définir les commandes qui apparaissent sur la barre d'outils.

    La barre d'outils peut être personnalisée par l'utilisateur en utilisant le menu "Personnaliser" dans le menu "Affichage". Les choix de l'utilisateur sont enregistrés dans les préférences de l'application.

    La classe MainToolBar est une sous-classe de ToolBar qui est utilisée dans la fenêtre principale de Task Coach.
    """
    def __init__(self, window, settings, size: tuple = (32, 32)):
        """
        Initialise une nouvelle instance de la classe ToolBar.

        Args :
            window (wx.Window): La fenêtre parent de la barre d'outils.
            settings (config.Settings): Les paramètres de configuration de l'application.
            size (tuple, optional): La taille des icônes de la barre d'outils. La valeur par défaut est (32, 32).
        """
        self.__window = window
        self.__settings = settings
        self.__visibleUICommands = list()
        self.__cache = None
        super().__init__(window, style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self.SetToolBitmapSize(size)
        if operating_system.isMac():
            # Extra margin needed because the search control is too high
            self.SetMargins(0, 7)
        self.loadPerspective(window.getToolBarPerspective())

    def Clear(self):
        """Efface la barre d'outils et tous les contrôles qu'elle contient.

        Cette méthode est nécessaire car la méthode Clear de la classe AuiToolBar ne supprime pas les contrôles de la barre d'outils.
        """

        if self.__visibleUICommands:  # Peut-être aucun(None)
            for uiCommand in self.__visibleUICommands:
                if uiCommand is not None and not isinstance(uiCommand, int):
                    uiCommand.unbind(self, uiCommand.id)

        idx = 0
        while idx < self.GetToolCount():
            item = self.FindToolByIndex(idx)
            if item is not None and item.GetKind() == aui.ITEM_CONTROL:
                item.window.Destroy()
                self.DeleteToolByPos(idx)
            else:
                idx += 1

        super().Clear()

    def detach(self):
        self.Clear()
        self.__visibleUICommands = self.__cache = None

    def getToolIdByCommand(self, commandName: str) -> int:
        if commandName == "EditToolBarPerspective":
            return self.__customizeId

        for uiCommand in self.__visibleUICommands:
            if isinstance(uiCommand, uicommand.UICommand) and uiCommand.uniqueName() == commandName:
                return uiCommand.id
        return wx.ID_ANY

    def _filterCommands(self, perspective: str, cache: bool = True) -> list:
        commands = list()
        if perspective:
            index = dict([(command.uniqueName(), command) for command in self.uiCommands(cache=cache) if
                          command is not None and not isinstance(command, int)])
            index["Separator"] = None
            index["Spacer"] = 1
            for className in perspective.split(","):
                if className in index:
                    commands.append(index[className])
        else:
            commands = list(self.uiCommands(cache=cache))
        return commands

    def loadPerspective(self, perspective: str, customizable=True, cache=True):
        self.Clear()

        commands = self._filterCommands(perspective, cache=cache)
        self.__visibleUICommands = commands[:]

        if customizable:
            if 1 not in commands:
                commands.append(1)
            from taskcoachlib.gui.dialog.toolbar import ToolBarEditor
            uiCommand = uicommand.EditToolBarPerspective(self, ToolBarEditor,
                                                        settings=self.__settings)
            commands.append(uiCommand)
            self.__customizeId = uiCommand.id
        if operating_system.isMac():
            commands.append(None)  # Errr...

        self.appendUICommands(*commands)
        self.Realize()

    def perspective(self) -> str:
        """
        Retourne la perspective actuelle de la barre d'outils sous forme de chaîne de caractères.

        La perspective est une chaîne de caractères qui représente les commandes actuellement affichées sur la barre d'outils, dans l'ordre dans lequel elles apparaissent.
        """
        names = list()
        for uiCommand in self.__visibleUICommands:
            if uiCommand is None:
                names.append("Separator")
            elif isinstance(uiCommand, int):
                names.append("Spacer")
            else:
                names.append(uiCommand.uniqueName())
        return ",".join(names)

    def savePerspective(self, perspective: str):
        """
        Enregistre la perspective actuelle de la barre d'outils dans les préférences de l'application.

        Args:
            perspective (str): La perspective à enregistrer.
        """
        self.loadPerspective(perspective)
        self.__window.saveToolBarPerspective(perspective)

    def uiCommands(self, cache: bool = True):
        """
        Retourne une liste de commandes UI à afficher sur la barre d'outils.

        Cette méthode utilise la méthode createToolBarUICommands de la classe parent UICommandContainerMixin pour générer la liste de commandes UI.
        """
        if self.__cache is None or not cache:
            self.__cache = self.__window.createToolBarUICommands()
        return self.__cache

    def visibleUICommands(self):
        """
        Retourne une liste des commandes UI actuellement affichées sur la barre d'outils.
        """
        return self.__visibleUICommands[:]

    def AppendSeparator(self):
        """
        Ajoute un séparateur à la barre d'outils.

        This little adapter is needed for
        uicommand.UICommandContainerMixin.appendUICommands"""
        self.AddSeparator()

    def AppendStretchSpacer(self, proportion: int):
        """
        Ajoute un espaceur extensible à la barre d'outils.

        Args:
            proportion (int): La proportion de l'espaceur extensible.
        """
        self.AddStretchSpacer(proportion)

    def appendUICommand(self, uiCommand):
        """
        Ajoute une commande UI à la barre d'outils.

        Args:
            uiCommand (uicommand.UICommand): La commande UI à ajouter.
        """
        return uiCommand.appendToToolBar(self)


class MainToolBar(ToolBar):
    """
    Une sous-classe de ToolBar qui est utilisée dans la fenêtre principale de Task Coach.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance de la classe MainToolBar.

        Args:
            *args: Les arguments positionnels à passer à la méthode __init__ de la classe parent ToolBar.
            **kwargs: Les arguments par mot-clé à passer à la méthode __init__ de la classe parent ToolBar.
        """
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_SIZE, self._OnSize)

    def _OnSize(self, event):
        """
        Gestionnaire d'événements pour le redimensionnement de la fenêtre.

        Cette méthode ajuste la taille de la barre d'outils en fonction de la taille de la fenêtre parent.

        Args:
            event (wx.SizeEvent): L'événement de redimensionnement.
        """
        event.Skip()
        # On Windows XP, the sizes are off by 1 pixel. I fear that this value depends
        # on the user's config so let's take some margin.
        if abs(event.GetSize()[0] - self.GetParent().GetClientSize()[0]) >= 10:
            wx.CallAfter(self.GetParent().SendSizeEvent)

    def Realize(self):
        self._agwStyle &= ~aui.AUI_TB_NO_AUTORESIZE
        super().Realize()
        self._agwStyle |= aui.AUI_TB_NO_AUTORESIZE
        wx.CallAfter(self.GetParent().SendSizeEvent)
        # w, h = self.GetParent().GetClientSizeTuple()
        w, h = self.GetParent().GetClientSize()
        wx.CallAfter(self.SetMinSize, (w, -1))
