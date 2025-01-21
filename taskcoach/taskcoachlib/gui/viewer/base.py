# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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
# from __future__ import print_function

# from builtins import object
# from builtins import str

import wx
from taskcoachlib import patterns, widgets, command, render
from taskcoachlib.i18n import _
from taskcoachlib.gui.uicommand import uicommand
from taskcoachlib.gui import toolbar, artprovider
# try:
#    from taskcoachlib.thirdparty.agw import hypertreelist
# except ImportError:
#    from agw import hypertreelist
# try:
from wx.lib.agw import hypertreelist
# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
# else:
#    from wx.lib.pubsub import pub
from pubsub import pub

from taskcoachlib.widgets import ToolTipMixin
from . import mixin

# debug the metaclass :
# print('le mro de patterns.Observer est ', patterns.Observer.__mro__)
# print('le mro de wx.Panel est ', wx.Panel.__mro__)
# print('le mro de patterns.NumberedInstances est ', patterns.NumberedInstances.__mro__)


# class PreViewer(type(wx.Panel), metaclass=patterns.NumberedInstances):
class PreViewer(type(wx.Panel), patterns.NumberedInstances):
    # def __init__(self):
    # instanceNumber =
    pass


# class Viewer(wx.Panel, patterns.Observer, metaclass=patterns.makecls(patterns.NumberedInstances)):
class Viewer(wx.Panel, patterns.Observer, metaclass=PreViewer):
    # class Viewer(wx.Panel, with_metaclass(patterns.NumberedInstances), patterns.Observer):
    # TypeError: metaclass conflict: the metaclass of a derived class must be
    # a (non-strict) subclass of the metaclasses of all its bases
    """
        Classe de base pour les visionneuses dans Task Coach.

        Une visionneuse affiche les objets du domaine (par exemple, les tâches ou les efforts) au moyen d'un widget
        comme un ListCtrl ou un TreeListCtrl. Cette classe gère la présentation et l'interaction avec ces objets.

        Attributs :
            defaultTitle (str) : Le titre par défaut de la visionneuse.
            defaultBitmap (str) : L'icône par défaut pour la visionneuse.
            viewerImages (list) : Les images utilisées pour afficher les objets de la visionneuse.
    """

    defaultTitle = "Subclass responsibility"
    defaultBitmap = "Subclass responsibility"
    viewerImages = artprovider.itemImages

    def __init__(self, parent, taskFile, settings, *args, **kwargs):
        """
        Initialise une nouvelle visionneuse.

        Args :
            parent (wx.Window) : La fenêtre parente de la visionneuse.
            taskFile (TaskFile) : Le fichier de tâches à visualiser.
            settings (Settings) : Les paramètres de l'application.
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        patterns.Observer.__init__(self)
        super().__init__(parent, -1)
        # new_id = wx.NewIdRef().GetId()
        # super().__init__(parent, new_id)
        # print('le mro de gui.viewer.base.Viewer est ', Viewer.__mro__)
        self.parent = parent
        self.taskFile = taskFile
        self.settings = settings
        self.__settingsSection = kwargs.pop("settingsSection")
        self.__freezeCount = 0
        # The how maniest of this viewer type are we? Used for settings
        self.__instanceNumber = kwargs.pop("instanceNumber")  # KeyError: 'instanceNumber'
        # self.__instanceNumber = kwargs.pop("instanceNumber", 0)
        self.__use_separate_settings_section = kwargs.pop(
            "use_separate_settings_section", True
        )
        # Selection cache:
        self.__curselection = []
        # Flag so that we don't Notify observers while we're selecting all items
        self.__selectingAllItems = False
        # Popup menus we have to Destroy before closing the viewer to prevent
        # memory leakage:
        self._popupMenus = []
        # What are we presenting:
        self.__presentation = self.createSorter(
            self.createFilter(self.domainObjectsToView())
        )
        # The widget used to present the presentation:
        self.widget = self.createWidget()
        self.widget.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        )
        self.toolbar = toolbar.ToolBar(self, settings, (16, 16))
        self.initLayout()
        self.registerPresentationObservers()
        self.refresh()

        pub.subscribe(self.onBeginIO, "taskfile.aboutToRead")
        pub.subscribe(self.onBeginIO, "taskfile.aboutToClear")
        pub.subscribe(self.onBeginIO, "taskfile.aboutToSave")
        pub.subscribe(self.onEndIO, "taskfile.justRead")
        pub.subscribe(self.onEndIO, "taskfile.justCleared")
        pub.subscribe(self.onEndIO, "taskfile.justSaved")

        if isinstance(self.widget, ToolTipMixin):  # si widget est une instance de ToolTupMixin
            # Informer l'utilisateur
            pub.subscribe(self.onShowTooltipsChanged, "settings.view.descriptionpopups")
            # Régler les infos du widget
            self.widget.SetToolTipsEnabled(
                settings.getboolean("view", "descriptionpopups")
            )

        wx.CallAfter(self.__DisplayBalloon)

    def __DisplayBalloon(self):
        """Affiche une info-bulle pour informer l'utilisateur que la barre d'outils est personnalisable."""
        # AuiFloatingFrame is instantiated from framemanager, we can't derive it from BalloonTipManager
        if self.toolbar.IsShownOnScreen() and hasattr(
            wx.GetTopLevelParent(self), "AddBalloonTip"
        ):
            wx.GetTopLevelParent(self).AddBalloonTip(
                self.settings,
                "customizabletoolbars",
                self.toolbar,
                title=_("Toolbars are customizable"),
                getRect=lambda: self.toolbar.GetToolRect(
                    self.toolbar.getToolIdByCommand("EditToolBarPerspective")
                ),
                message=_(
                    """Click on the gear icon on the right to add buttons and rearrange them."""
                )
            )

    def onShowTooltipsChanged(self, value):
        self.widget.SetToolTipsEnabled(value)

    def onBeginIO(self, taskFile):
        """Débute les opérations de lecture/écriture dans le fichier de tâches."""
        self.__freezeCount += 1
        self.__presentation.freeze()

    def onEndIO(self, taskFile):
        """Termine les opérations de lecture/écriture dans le fichier de tâches."""
        self.__freezeCount -= 1
        self.__presentation.thaw()  # TypeError: UltimateListCtrl.Append() got an unexpected keyword argument 'data'
        if self.__freezeCount == 0:
            self.refresh()

    def activate(self):
        pass

    def domainObjectsToView(self):
        """Retourne les objets du domaine que cette visionneuse doit afficher. Doit être implémentée dans les sous-classes.

        Renvoie les objets de domaine que cette visionneuse doit afficher. Pour les visualiseurs globaux
        , cela fera partie du fichier de tâches
        , par ex. self.taskFile.tasks(), pour les visualiseurs locaux, ce sera une liste
        d'objets transmis au constructeur du visualiseur."""
        raise NotImplementedError

    def registerPresentationObservers(self):
        """Enregistre les observateurs pour suivre les changements dans la présentation."""
        self.removeObserver(self.onPresentationChanged)
        self.registerObserver(
            self.onPresentationChanged,
            eventType=self.presentation().addItemEventType(),
            eventSource=self.presentation(),
        )
        self.registerObserver(
            self.onPresentationChanged,
            eventType=self.presentation().removeItemEventType(),
            eventSource=self.presentation(),
        )
        self.registerObserver(self.onNewItem, eventType="newitem")

    def detach(self):
        """Should be called by viewer.container before closing the viewer"""
        observers = [self, self.presentation()]
        observable = self.presentation()
        while True:
            try:
                observable = observable.observable()
            except AttributeError:
                break
            else:
                observers.append(observable)
        for observer in observers:
            try:
                observer.removeInstance()
            except AttributeError:
                pass  # Ignore observables that are not an observer themselves

        for popupMenu in self._popupMenus:
            # try:
            popupMenu.clearMenu()
            popupMenu.Destroy()
            # except wx.PyDeadObjectError:
            #     pass
            #     # https://stackoverflow.com/questions/34202195/import-pydeadobjecterror-with-wx-version-3-0-3
            #     # https://wxpython.org/Phoenix/docs/html/MigrationGuide.html#wx-pydeadobjecterror-runtimeerror
            #     # try with:
            #     # if someWindow:
            #     #     someWindow.doSomething()
            # except RuntimeError:
            #     pass
            # TODO: Essayer plutôt ça :
            #   popupMenu.clearMenu()
            #   popupMenu.Destroy()

        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToRead")
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToClear")
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToSave")
        pub.unsubscribe(self.onEndIO, "taskfile.justRead")
        pub.unsubscribe(self.onEndIO, "taskfile.justCleared")
        pub.unsubscribe(self.onEndIO, "taskfile.justSaved")

        self.presentation().detach()
        self.toolbar.detach()

    def viewerStatusEventType(self):
        # def viewerStatusEventType(self) -> str:
        """Retourne le type d'événement à utiliser pour les mises à jour de statut.

        Returns :
            str : Le type d'événement de mise à jour de statut.
        """
        return "viewer%s.status" % id(self)

    def sendViewerStatusEvent(self):
        """Envoie un événement pour indiquer que l'état de la visionneuse a changé."""
        pub.sendMessage(self.viewerStatusEventType(), viewer=self)

    def statusMessages(self):
        return "", ""

    def title(self):
        # def title(self) -> str:
        """Retourne le titre actuel de la visionneuse.

        Returns :
            str : Le titre actuel de la visionneuse.
        """
        return self.settings.get(self.settingsSection(), "title") or self.defaultTitle

    def setTitle(self, title):
        """Modifie le titre de la visionneuse.

        Args :
            title (str) : Le nouveau titre à définir.
        """
        titleToSaveInSettings = "" if title == self.defaultTitle else title
        self.settings.set(self.settingsSection(), "title", titleToSaveInSettings)
        self.parent.setPaneTitle(self, title)
        self.parent.manager.Update()

    def initLayout(self):
        """Initialise la mise en page de la visionneuse."""
        self._sizer = wx.BoxSizer(wx.VERTICAL)  # pylint: disable=W0201
        self._sizer.Add(self.toolbar, flag=wx.EXPAND)
        self._sizer.Add(self.widget, proportion=1, flag=wx.EXPAND)
        self.SetSizerAndFit(self._sizer)

    def createWidget(self, *args):
        """Crée le widget utilisé pour afficher les objets. À implémenter dans les sous-classes.

        Returns :
            wx.Window : Le widget à utiliser pour l'affichage des objets.

        Raises :
            NotImplementedError : Si non implémenté dans une sous-classe.
        """
        raise NotImplementedError

    def createImageList(self):
        size = (16, 16)
        imageList = wx.ImageList(*size)  # pylint: disable=W0142
        self.imageIndex = {}  # pylint: disable=W0201
        for index, image in enumerate(self.viewerImages):
            try:
                # image_list.Add(wx.ArtProvider_GetBitmap(image, wx.ART_MENU, size))
                # print(image)
                imageList.Add(wx.ArtProvider.GetBitmap(image, wx.ART_MENU, size))
                # print(imageList)
            except:
                print(image)
                raise
            self.imageIndex[image] = index
        return imageList

    def getWidget(self):
        return self.widget

    def SetFocus(self, *args, **kwargs):
        # try:
        #     self.widget.SetFocus(*args, **kwargs)
        # except wx.PyDeadObjectError:
        #     # https://stackoverflow.com/questions/34202195/import-pydeadobjecterror-with-wx-version-3-0-3
        #     # https://wxpython.org/Phoenix/docs/html/MigrationGuide.html#wx-pydeadobjecterror-runtimeerror
        #     # try with:
        #     # if someWindow:
        #     #     someWindow.doSomething()
        #     # except RuntimeError:
        #     pass
        if self.widget:
            self.widget.SetFocus(*args, **kwargs)
        else:
            pass

    # @staticmethod
    def createSorter(self, collection):
        """Crée un trieur pour organiser la présentation.

        Cette méthode peut être remplacée pour décorer la présentation avec un trieur.
        """
        return collection

    def createFilter(self, collection):
        """Crée un filtre pour organiser la présentation.

        Cette méthode peut être remplacée pour décorer la présentation avec un filtre.
        """
        return collection

    def onAttributeChanged(self, newValue, sender):  # pylint: disable=W0613
        if self:
            self.refreshItems(sender)

    def onAttributeChanged_Deprecated(self, event):
        self.refreshItems(*event.sources())

    def onNewItem(self, event):
        """Sélectionne un nouvel élément ajouté à la présentation.

        Args :
            event (Event) : L'événement indiquant l'ajout d'un nouvel élément.
        """
        self.select(
            [item for item in list(event.values()) if item in self.presentation()]
        )

    def onPresentationChanged(self, event):  # pylint: disable=W0613
        """Gère les changements dans la présentation et rafraîchit la visionneuse.

        Chaque fois que notre présentation est modifiée (éléments ajoutés, éléments supprimés)
        , la visionneuse se rafraîchit."""

        def itemsRemoved():
            return event.type() == self.presentation().removeItemEventType()

        def allItemsAreSelected():
            return set(self.__curselection).issubset(set(event.values()))

        self.refresh()
        if itemsRemoved() and allItemsAreSelected():
            self.selectNextItemsAfterRemoval(list(event.values()))
        self.updateSelection(sendViewerStatusEvent=False)
        self.sendViewerStatusEvent()

    def selectNextItemsAfterRemoval(self, removedItems):
        raise NotImplementedError

    def onSelect(self, event=None):  # pylint: disable=W0613
        """The selection of items in the widget has been changed. Notify
        our observers."""

        try:
            if self.IsBeingDeleted() or self.__selectingAllItems:
                # Some widgets change the selection and send selection events when
                # deleting all items as part of the Destroy process. Ignore.
                return
            # Be sure all wx events are handled before we update our selection
            # cache and Notify our observers:
            wx.CallAfter(self.updateSelection)
        except RuntimeError:
            # RuntimeError: wrapped C/C++ object of type EffortViewer has been deleted
            # FIXME: It's a bug?
            # wx.PyDeadObjectError create now RuntimeError !
            pass

    def updateSelection(self, sendViewerStatusEvent=True):
        newSelection = self.widget.curselection()
        if newSelection != self.__curselection:
            self.__curselection = newSelection
            if sendViewerStatusEvent:
                self.sendViewerStatusEvent()

    def freeze(self):
        self.widget.Freeze()

    def thaw(self):
        self.widget.Thaw()

    def refresh(self):
        """Rafraîchit les éléments affichés dans la visionneuse."""
        if self and not self.__freezeCount:
            self.widget.RefreshAllItems(len(self.presentation()))

    def refreshItems(self, *items):
        if not self.__freezeCount:
            items = [item for item in items if item in self.presentation()]
            self.widget.RefreshItems(*items)  # pylint: disable=W0142

    def select(self, items):
        """Sélectionne des éléments dans la présentation.

        Args :
            items (list) : Liste des objets à sélectionner.
        """
        self.__curselection = items
        self.widget.select(items)

    def curselection(self):
        """Retourne la sélection actuelle dans la visionneuse.

        Renvoie une liste d'éléments (objets de domaine) actuellement sélectionnés dans notre widget .
        """
        return self.__curselection

    def curselectionIsInstanceOf(self, class_):
        """Return whether all items in the current selection are instances of
        class_. Can be overridden in subclasses that show only one type
        of items to simply check the class."""
        return all(isinstance(item, class_) for item in self.curselection())

    def isselected(self, item):
        """Returns True if the given item is selected. See
        L{EffortViewer} for an explanation of why this may be
        different than 'if item in viewer.curselection()'."""
        return item in self.curselection()

    def select_all(self):
        """Select all items in the presentation. Since some of the widgets we
        use may send events for each individual item (!) we stop processing
        selection events while we select all items."""
        self.__selectingAllItems = True
        self.widget.select_all()
        # Use CallAfter to make sure we start processing selection events
        # after all selection events have been fired (and ignored):
        wx.CallAfter(self.endOfSelectAll)

    def endOfSelectAll(self):
        self.__curselection = self.presentation()
        self.__selectingAllItems = False
        # Pretend we received one selection event for the select_all() call:
        self.onSelect()

    def clear_selection(self):
        self.__curselection = []
        self.widget.clear_selection()

    def size(self):
        return self.widget.GetItemCount()

    def presentation(self):
        """Return the domain objects that this viewer is currently
        displaying."""
        return self.__presentation

    def setPresentation(self, presentation):
        """Change the presentation of the viewer."""
        self.__presentation = presentation

    # @staticmethod
    def widgetCreationKeywordArguments(self):
        return {}

    # @staticmethod
    def isViewerContainer(self):
        return False

    def isShowingTasks(self):
        return False

    def isShowingEffort(self):
        return False

    def isShowingCategories(self):
        return False

    def isShowingNotes(self):
        return False

    def isShowingAttachments(self):
        return False
        """Retourne les objets du domaine que cette visionneuse doit afficher. Doit être implémentée dans les sous-classes."""
    def visibleColumns(self):
        return [widgets.Column("subject", _("Subject"))]

    def bitmap(self):
        """Return the bitmap that represents this viewer. Used for the
        'Viewer->New viewer' menu item, for example."""
        return self.defaultBitmap  # Class attribute of concrete viewers

    def settingsSection(self):
        """Return the settings section of this viewer."""
        section = self.__settingsSection
        if self.__use_separate_settings_section and self.__instanceNumber > 0:
            # We're not the first viewer of our class, so we need a different
            # settings section than the default one.
            section += str(self.__instanceNumber)
            if not self.settings.has_section(section):
                # Our section does not exist yet. Create it and copy the
                # settings from the previous section as starting point. We're
                # copying from the previous section instead of the default
                # section so that when the user closes a viewer and then opens
                # a new one, the settings of that closed viewer are reused.
                self.settings.add_section(
                    section, copyFromSection=self.previousSettingsSection()
                )
        return section

    def previousSettingsSection(self):
        """Return the settings section of the previous viewer of this
        class."""
        previousSectionNumber = self.__instanceNumber - 1
        while previousSectionNumber > 0:
            previousSection = self.__settingsSection + str(previousSectionNumber)
            if self.settings.has_section(previousSection):
                return previousSection
            previousSectionNumber -= 1
        return self.__settingsSection

    def hasModes(self):
        return False

    def getModeUICommands(self):
        return []

    # @staticmethod
    def isSortable(self):
        return False

    # @staticmethod
    def getSortUICommands(self):
        return []

    # @staticmethod
    def isSearchable(self):
        return False

    def hasHideableColumns(self):
        return False

    def getColumnUICommands(self):
        return []

    # @staticmethod
    def isFilterable(self):
        return False

    # @staticmethod
    def getFilterUICommands(self):
        return []

    def supportsRounding(self):
        return False

    def getRoundingUICommands(self):
        return []

    def createToolBarUICommands(self):
        """UI commands to put on the toolbar of this viewer."""
        table = wx.AcceleratorTable(
            [
                (wx.ACCEL_CMD, ord("X"), wx.ID_CUT),
                (wx.ACCEL_CMD, ord("C"), wx.ID_COPY),
                (wx.ACCEL_CMD, ord("V"), wx.ID_PASTE),
                (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_EDIT),
                (wx.ACCEL_CTRL, wx.WXK_DELETE, wx.ID_DELETE),
            ]
        )
        self.SetAcceleratorTable(table)

        clipboardToolBarUICommands = self.createClipboardToolBarUICommands()
        creationToolBarUICommands = self.createCreationToolBarUICommands()
        editToolBarUICommands = self.createEditToolBarUICommands()
        actionToolBarUICommands = self.createActionToolBarUICommands()
        modeToolBarUICommands = self.createModeToolBarUICommands()

        def separator(uiCommands, *otherUICommands):
            return (None,) if (uiCommands and any(otherUICommands)) else ()

        clipboardSeparator = separator(
            clipboardToolBarUICommands,
            creationToolBarUICommands,
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        creationSeparator = separator(
            creationToolBarUICommands,
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        editSeparator = separator(
            editToolBarUICommands, actionToolBarUICommands, modeToolBarUICommands
        )
        actionSeparator = separator(actionToolBarUICommands, modeToolBarUICommands)

        return (
            clipboardToolBarUICommands
            + clipboardSeparator
            + creationToolBarUICommands
            + creationSeparator
            + editToolBarUICommands
            + editSeparator
            + actionToolBarUICommands
            + actionSeparator
            + modeToolBarUICommands
        )

    def getToolBarPerspective(self):
        return self.settings.get(self.settingsSection(), "toolbarperspective")

    def saveToolBarPerspective(self, perspective):
        self.settings.set(self.settingsSection(), "toolbarperspective", perspective)

    def createClipboardToolBarUICommands(self):
        """UI commands for manipulating the clipboard (cut, copy, paste)."""
        cutCommand = uicommand.EditCut(viewer=self)
        copyCommand = uicommand.EditCopy(viewer=self)
        pasteCommand = uicommand.EditPaste()
        cutCommand.bind(self, wx.ID_CUT)
        # cutCommand.Bind(self, wx.ID_CUT)
        copyCommand.bind(self, wx.ID_COPY)
        # copyCommand.Bind(self, wx.ID_COPY)
        pasteCommand.bind(self, wx.ID_PASTE)
        # pasteCommand.Bind(self, wx.ID_PASTE)
        return cutCommand, copyCommand, pasteCommand

    def createCreationToolBarUICommands(self):
        """UI commands for creating new items."""
        return ()

    def createEditToolBarUICommands(self):
        """UI commands for editing items."""
        editCommand = uicommand.Edit(viewer=self)
        self.deleteUICommand = uicommand.Delete(
            viewer=self
        )  # For unittests pylint: disable=W0201
        # Instance attribute deleteUICommand defined outside __init__
        editCommand.bind(self, wx.ID_EDIT)
        self.deleteUICommand.bind(self, wx.ID_DELETE)
        return editCommand, self.deleteUICommand

    def createActionToolBarUICommands(self):
        """UI commands for actions."""
        return ()

    def createModeToolBarUICommands(self):
        """UI commands for mode switches (e.g. list versus tree mode)."""
        return ()

    def newItemDialog(self, *args, **kwargs):
        bitmap = kwargs.pop("bitmap")
        newItemCommand = self.newItemCommand(*args, **kwargs)
        newItemCommand.do()
        return self.editItemDialog(newItemCommand.items, bitmap, items_are_new=True)

    def newSubItemDialog(self, bitmap):
        newSubItemCommand = self.newSubItemCommand()
        newSubItemCommand.do()
        return self.editItemDialog(newSubItemCommand.items, bitmap, items_are_new=True)

    def editItemDialog(self, items, bitmap, columnName="", items_are_new=False):
        Editor = self.itemEditorClass()
        return Editor(
            wx.GetTopLevelParent(self),
            items,
            self.settings,
            self.presentation(),
            self.taskFile,
            bitmap=bitmap,
            columnName=columnName,
            items_are_new=items_are_new,
        )

    def itemEditorClass(self):
        raise NotImplementedError

    def newItemCommand(self, *args, **kwargs):
        return self.newItemCommandClass()(self.presentation(), *args, **kwargs)

    def newItemCommandClass(self):
        raise NotImplementedError

    def newSubItemCommand(self):
        return self.newSubItemCommandClass()(self.presentation(), self.curselection())

    def newSubItemCommandClass(self):
        raise NotImplementedError

    def deleteItemCommand(self):
        return self.deleteItemCommandClass()(self.presentation(), self.curselection())

    def deleteItemCommandClass(self):
        return command.DeleteCommand

    def cutItemCommand(self):
        return self.cutItemCommandClass()(self.presentation(), self.curselection())

    def cutItemCommandClass(self):
        return command.CutCommand

    # @staticmethod
    def onEditSubject(self, item, newValue):
        command.EditSubjectCommand(items=[item], newValue=newValue).do()

    # @staticmethod
    def onEditDescription(self, item, newValue):
        command.EditDescriptionCommand(items=[item], newValue=newValue).do()

    def getItemTooltipData(self, item):
        lines = [line.rstrip("\r") for line in item.description().split("\n")]
        return [(None, lines)] if lines and lines != [""] else []


class CategorizableViewerMixin(object):
    def getItemTooltipData(self, item):
        return [
            (
                "folder_blue_arrow_icon",
                (
                    [", ".join(sorted([cat.subject() for cat in item.categories()]))]
                    if item.categories()
                    else []
                ),
            )
        ] + super().getItemTooltipData(item)


class WithAttachmentsViewerMixin(object):
    def getItemTooltipData(self, item):
        return [
            (
                "paperclip_icon",
                sorted([str(attachment) for attachment in item.attachments()]),
            )
        ] + super().getItemTooltipData(item)


class ListViewer(Viewer):  # pylint: disable=W0223
    """
        Classe ListViewer, héritant de Viewer.

        Cette classe est utilisée pour afficher des objets dans une vue en liste, contrairement à une vue arborescente.
        Elle implémente des méthodes spécifiques pour gérer les objets sous forme de liste.

    Explication des méthodes :

    isTreeViewer : Retourne False car cette classe ne représente pas une vue arborescente, mais une vue en liste.
    visibleItems : Cette méthode génère tous les éléments visibles dans la présentation en les itérant.
    getItemWithIndex : Récupère un élément particulier dans la liste en fonction de son index.
    getIndexOfItem : Donne l'index d'un élément particulier dans la présentation.
    selectNextItemsAfterRemoval : Cette méthode est utilisée pour sélectionner les éléments après la suppression.
     Dans ce cas, elle ne fait rien, car les contrôles de liste gèrent cette sélection automatiquement.
    """
    # @staticmethod
    def isTreeViewer(self):
        # def isTreeViewer(self) -> bool:
        """
        Indique si la vue est une vue arborescente.

        Returns :
            bool : False, car cette vue est une vue en liste et non en arbre.
        """
        return False

    def visibleItems(self):
        """
        Itère sur les éléments visibles dans la présentation.

        Yields :
            object : Chaque objet visible dans la présentation.
        """
        for item in self.presentation():
            yield item

    def getItemWithIndex(self, index):
        # def getItemWithIndex(self, index) -> object:
        """
                Récupère un élément spécifique dans la présentation en fonction de son index.

                Args :
                    index (int) : L'index de l'élément à récupérer.

                Returns :
                    object : L'objet à l'index spécifié.
                """
        return self.presentation()[index]

    def getIndexOfItem(self, item):
        # def getIndexOfItem(self, item) -> int:
        """
        Récupère l'index d'un élément spécifique dans la présentation.

        Args :
            item (object) : L'objet dont on souhaite connaître l'index.

        Returns :
            int : L'index de l'objet dans la présentation.
        """
        return self.presentation().index(item)

    def selectNextItemsAfterRemoval(self, removedItems):
        """
        Sélectionne les éléments suivants après suppression.

        Cette méthode est spécifique aux contrôles de liste où la sélection
        est gérée automatiquement après la suppression d'éléments.

        Args :
            removedItems (list) : La liste des éléments qui ont été supprimés.
        """
        pass  # Gestion automatique par les contrôles de liste.


class TreeViewer(Viewer):  # pylint: disable=W0223
    """
    Classe TreeViewer, héritant de Viewer.

    Cette classe est utilisée pour afficher des objets dans une vue arborescente, permettant d'expander
    ou de réduire les nœuds de l'arbre. Elle gère les événements de sélection et d'expansion des éléments.

    Explication des méthodes :

    onItemExpanded et onItemCollapsed : Gèrent les événements d'expansion ou de réduction des nœuds d'un arbre.
    expandAll et collapseAll : Permettent d'expander ou de réduire tous les éléments de manière récursive.
    select et selectNextItemsAfterRemoval : Sélectionnent des éléments, en expandeant leurs parents si nécessaire,
     et sélectionnent des éléments après suppression.
    visibleItems : Itère sur les éléments visibles dans l'arbre, y compris leurs enfants.
    getRootItems, getItemParent, et children : Gèrent la relation parent-enfant dans l'arbre.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise TreeViewer avec gestion des événements d'expansion et de collapse des éléments.

        Args:
            *args: Arguments supplémentaires pour l'initialisation.
            **kwargs: Arguments nommés pour l'initialisation.
        """
        self.__selectionIndex = 0
        super().__init__(*args, **kwargs)
        # Liaison des événements d'expansion et de collapse
        # self.widget.bind(wx.EVT_TREE_ITEM_EXPANDED, self.onItemExpanded)
        self.widget.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.onItemExpanded)
        # self.widget.bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onItemCollapsed)
        self.widget.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onItemCollapsed)

    def onItemExpanded(self, event):
        """Gère l'événement d'expansion d'un élément."""
        self.__handleExpandedOrCollapsedItem(event, expanded=True)

    def onItemCollapsed(self, event):
        """Gère l'événement de collapse d'un élément."""
        self.__handleExpandedOrCollapsedItem(event, expanded=False)

    def __handleExpandedOrCollapsedItem(self, event, expanded):
        """
        Gère les changements d'état d'expansion ou de collapse d'un élément.

        Args:
            event (wx.Event): L'événement lié à l'expansion ou au collapse.
            expanded (bool): Indique si l'élément doit être expansé ou réduit.
        """
        event.Skip()
        treeItem = event.GetItem()
        # If we get an expanded or collapsed event for the root item, ignore it
        if treeItem == self.widget.GetRootItem():
            return
        item = self.widget.GetItemPyData(treeItem)  # TODO: try GetItemData
        item.expand(expanded, context=self.settingsSection())

    def expandAll(self):
        """Expande tous les éléments de manière récursive."""
        # Since the widget does not send EVT_TREE_ITEM_EXPANDED when expanding
        # all items, we have to do the bookkeeping ourselves:
        for item in self.visibleItems():
            item.expand(True, context=self.settingsSection(), notify=False)
        self.refresh()

    def collapseAll(self):
        """Réduit tous les éléments de manière récursive."""
        # Since the widget does not send EVT_TREE_ITEM_COLLAPSED when collapsing
        # all items, we have to do the bookkeeping ourselves:
        for item in self.visibleItems():
            item.expand(False, context=self.settingsSection(), notify=False)
        self.refresh()

    def isAnyItemExpandable(self):
        """Vérifie si un élément est expansible."""
        return self.widget.isAnyItemExpandable()

    def isAnyItemCollapsable(self):
        """Vérifie si un élément est collapsable."""
        return self.widget.isAnyItemCollapsable()

    def isTreeViewer(self):
        # def isTreeViewer(self) -> bool:
        """Indique que cette vue est une vue arborescente.

        Returns :
            bool : True, car cette vue est une vue en arbre et non en liste."""
        return True

    def select(self, items):
        # def select(self, items: list):
        """
        Sélectionne les éléments spécifiés et expande leurs parents de manière récursive.

        Args :
            items (list) : La liste des éléments à sélectionner.
        """
        for item in items:
            self.__expandItemRecursively(item)
        self.refresh()
        super().select(items)

    def __expandItemRecursively(self, item):
        # def __expandItemRecursively(self, item: object):
        """
        Expande les parents de l'élément donné de manière récursive.

        Args :
            item (object) : L'élément dont les parents doivent être expansés.
        """
        parent = self.getItemParent(item)
        if parent:
            parent.expand(True, context=self.settingsSection(), notify=False)
            self.__expandItemRecursively(parent)

    def selectNextItemsAfterRemoval(self, removedItems):
        # def selectNextItemsAfterRemoval(self, removedItems: list):
        """
        Sélectionne les éléments suivants après la suppression de certains éléments.

        Args :
            removedItems (list) : Liste des éléments supprimés.
        """
        parents = [self.getItemParent(item) for item in removedItems]
        parents = [parent for parent in parents if parent in self.presentation()]
        parent = parents[0] if parents else None
        siblings = self.children(parent)
        newSelection = (
            siblings[min(len(siblings) - 1, self.__selectionIndex)]
            if siblings
            else parent
        )
        if newSelection:
            self.select([newSelection])

    def updateSelection(self, *args, **kwargs):
        """
        Met à jour la sélection actuelle et garde une trace de l'index sélectionné.

        Args :
            *args : Arguments supplémentaires pour la mise à jour de la sélection.
            **kwargs : Arguments nommés pour la mise à jour.
        """
        super().updateSelection(*args, **kwargs)
        curselection = self.curselection()
        if curselection:
            siblings = self.children(self.getItemParent(curselection[0]))
            self.__selectionIndex = (
                siblings.index(curselection[0]) if curselection[0] in siblings else 0
            )
        else:
            self.__selectionIndex = 0

    def visibleItems(self):
        """
        Itère sur les éléments visibles dans la présentation, y compris les enfants.

        Yields :
            object : Chaque élément visible et ses enfants.
        """

        def yieldItemsAndChildren(items):
            sortedItems = [item for item in self.presentation() if item in items]
            for item in sortedItems:
                yield item
                children = self.children(item)
                if children:
                    for child in yieldItemsAndChildren(children):
                        yield child

        for item in yieldItemsAndChildren(self.getRootItems()):
            yield item

    def getRootItems(self):
        # def getRootItems(self) -> list:
        """
        Retourne les éléments racines de la présentation.

        Autoriser le remplacement des rootItems.

        Returns :
            list : Liste des éléments racines.
        """
        return self.presentation().rootItems()

    def getItemParent(self, item):
        # def getItemParent(self, item) -> object:
        """
        Retourne le parent de l'élément donné.

        Autoriser le remplacement du parent d'un élément.

        Args :
            item (object) : L'élément dont le parent est à retourner.

        Returns :
            object : Le parent de l'élément.
        """
        return item.parent()

    def getItemExpanded(self, item):
        # def getItemExpanded(self, item) -> bool:
        """
        Vérifie si un élément est expansé dans la vue actuelle.

        Args :
            item (object) : L'élément à vérifier.

        Returns :
            bool : True si l'élément est expansé, False sinon.
        """
        return item.isExpanded(context=self.settingsSection())

    def children(self, parent=None):
        # def children(self, parent=None) -> list:
        """
         Retourne les enfants d'un élément donné.

         Args :
             parent (object, optionnel) : L'élément parent. Si aucun parent n'est fourni, retourne les éléments racines.

         Returns :
             list : Liste des enfants de l'élément parent, ou des éléments racines si aucun parent n'est spécifié.
         """
        if parent:
            children = parent.children()
            if children:
                return [child for child in self.presentation() if child in children]
            else:
                return []
        else:
            return self.getRootItems()

    def getItemText(self, item):
        # def getItemText(self, item: object) -> str:
        """
        Retourne le texte (sujet) associé à un élément.

        Args :
            item (object) : L'élément dont le texte est à retourner.

        Returns :
            str : Le texte (sujet) de l'élément.
        """
        return item.subject()


class ViewerWithColumns(
    Viewer
):  # pylint: disable=W0223 better TreeViewer than Viewer ?
    """
    Classe ViewerWithColumns, héritant de Viewer.

    Cette classe permet de gérer des visionneuses avec des colonnes. Elle permet de gérer
    l'affichage dynamique des colonnes, la sélection, et les interactions avec les éléments
    dans une interface de type liste ou arbre avec des colonnes.

    Attributs :
        __initDone (bool) : Indique si l'initialisation est terminée.
        _columns (list) : Liste des colonnes disponibles.
        __visibleColumns (list) : Liste des colonnes actuellement visibles.
        __columnUICommands (list) : Liste des commandes de l'interface utilisateur liées aux colonnes.

    Explication des méthodes :

    hasHideableColumns : Indique si certaines colonnes peuvent être masquées.
    hasOrderingColumn : Vérifie si une colonne de tri est présente.
    getColumnUICommands : Récupère ou génère les commandes pour gérer les colonnes.
    initColumns et initColumn : Initialisent les colonnes et déterminent si elles sont visibles ou masquées.
    showColumn et hideColumn : Permettent d'afficher ou de masquer des colonnes.
    validateDrag : Valide si un élément peut être déplacé dans la colonne sélectionnée.
    __startObserving et __stopObserving : Ces méthodes gèrent l'abonnement aux événements en fonction des colonnes visibles.
     Lorsqu'une colonne devient visible, les événements associés à cette colonne sont observés,
      et lorsque la colonne est masquée, les événements ne sont plus observés.
    renderCategories et renderSubjectsOfRelatedItems : Ces méthodes permettent d'afficher les catégories
     ou d'autres éléments liés à l'élément courant. Elles rassemblent les sujets des éléments et les présentent sous forme de chaîne de texte.
    renderSubjects, renderCreationDateTime, et renderModificationDateTime : Ces méthodes formatent et affichent
     les sujets, ainsi que les dates de création et de modification des éléments.
    isItemCollapsed : Cette méthode vérifie si un élément est réduit dans une vue arborescente.
     Elle dépend de deux méthodes qui devraient être définies dans une sous-classe (par exemple, TreeViewer),
      à savoir getItemExpanded et isTreeViewer. Celles-ci sont utilisées pour déterminer l'état d'expansion ou de réduction d'un élément.

Concernant les méthodes isTreeViewer et getItemExpanded :

    isTreeViewer : Cette méthode est définie dans les sous-classe TreeViewer et ListViewer. Elle permet de différencier les vues arborescentes des vues en liste.
    getItemExpanded : De même, cette méthode est définie dans la sous-classe Treeviewer pour gérer l'état d'expansion ou de collapse d'un élément dans une vue arborescente.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la visionneuse avec des colonnes.

        Args :
            *args : Arguments supplémentaires pour l'initialisation.
            **kwargs : Arguments nommés supplémentaires pour l'initialisation.
        """
        self.__initDone = False
        self._columns = []
        self.__visibleColumns = []
        self.__columnUICommands = []
        super().__init__(*args, **kwargs)
        self.initColumns()
        self.__initDone = True
        self.refresh()

    def hasHideableColumns(self):
        """
        Indique si la visionneuse a des colonnes masquables.

        Returns :
            bool : True si certaines colonnes peuvent être masquées, sinon False.
        """
        return True

    def hasOrderingColumn(self):
        """
        Vérifie si une colonne de tri (ordering) est présente parmi les colonnes visibles.

        Returns :
            bool : True si une colonne "ordering" est visible, sinon False.
        """
        for column in self.__visibleColumns:
            if column.name() == "ordering":
                return True
        return False

    def getColumnUICommands(self):
        """
        Retourne les commandes de l'interface utilisateur pour gérer les colonnes.

        Returns :
            list : Liste des commandes UI pour les colonnes.
        """
        if not self.__columnUICommands:
            self.__columnUICommands = self.createColumnUICommands()
        return self.__columnUICommands

    def createColumnUICommands(self):
        """
        Crée les commandes de l'interface utilisateur pour les colonnes.

        Raises :
            NotImplementedError : Si non implémenté dans une sous-classe.
        """
        raise NotImplementedError

    def refresh(self, *args, **kwargs):
        """
        Rafraîchit la vue si l'initialisation est terminée.

        Args :
            *args : Arguments supplémentaires pour la méthode de rafraîchissement.
            **kwargs : Arguments nommés supplémentaires.
        """
        if self and self.__initDone:
            super().refresh(*args, **kwargs)

    def initColumns(self):
        """
        Initialise les colonnes de la visionneuse en les rendant visibles ou non en fonction des paramètres.
        """
        for column in self.columns():
            self.initColumn(column)
        if self.hasOrderingColumn():
            self.widget.SetResizeColumn(1)
            self.widget.SetMainColumn(1)

    def initColumn(self, column):
        """
        Initialise une colonne et détermine si elle doit être visible ou non.

        Args :
            column : La colonne à initialiser.
        """
        if column.name() in self.settings.getlist(
            self.settingsSection(), "columnsalwaysvisible"
        ):
            show = True
        else:
            show = column.name() in self.settings.getlist(
                self.settingsSection(), "columns"
            )
            self.widget.showColumn(column, show=show)
        if show:
            self.__visibleColumns.append(column)
            self.__startObserving(column.eventTypes())

    def showColumnByName(self, columnName, show=True):
        """
        Affiche ou masque une colonne par son nom.

        Args :
            columnName (str) : Le nom de la colonne à afficher ou masquer.
            show (bool) : True pour afficher, False pour masquer.
        """
        for column in self.hideableColumns():
            if columnName == column.name():
                isVisibleColumn = self.isVisibleColumn(column)
                if (show and not isVisibleColumn) or (not show and isVisibleColumn):
                    self.showColumn(column, show)
                break

    def showColumn(self, column, show=True, refresh=True):
        """
        Affiche ou masque une colonne et met à jour la vue.

        Args :
            column : La colonne à afficher ou masquer.
            show (bool) : True pour afficher, False pour masquer.
            refresh (bool) : True pour rafraîchir la vue après l'opération.
        """
        if column.name() == "ordering":
            self.widget.SetResizeColumn(1 if show else 0)
            self.widget.SetMainColumn(1 if show else 0)

        if show:
            self.__visibleColumns.append(column)
            # Make sure we keep the columns in the right order:
            self.__visibleColumns = [
                c for c in self.columns() if c in self.__visibleColumns
            ]
            self.__startObserving(column.eventTypes())
        else:
            self.__visibleColumns.remove(column)
            self.__stopObserving(column.eventTypes())
        self.widget.showColumn(column, show)
        self.settings.set(
            self.settingsSection(),
            "columns",
            str([column.name() for column in self.__visibleColumns]),
        )
        if refresh:
            self.widget.RefreshAllItems(len(self.presentation()))

    def hideColumn(self, visibleColumnIndex):
        """
        Masque une colonne visible par son index.

        Args :
            visibleColumnIndex (int) : L'index de la colonne à masquer.
        """
        column = self.visibleColumns()[visibleColumnIndex]
        self.showColumn(column, show=False)

    def columns(self):
        # def columns(self) -> list:
        """
        Retourne toutes les colonnes disponibles dans la visionneuse.

        Returns :
            list : Liste des colonnes.
        """
        return self._columns

    def selectableColumns(self):
        # def selectableColumns(self) -> list:
        """
        Retourne les colonnes sélectionnables.

        Returns :
            list : Liste des colonnes sélectionnables.
        """
        return self._columns

    def isVisibleColumnByName(self, columnName):
        # def isVisibleColumnByName(self, columnName: str) -> bool:
        """
        Vérifie si une colonne est visible par son nom.

        Args :
            columnName (str) : Le nom de la colonne à vérifier.

        Returns :
            bool : True si la colonne est visible, sinon False.
        """
        return columnName in [column.name() for column in self.__visibleColumns]

    def isVisibleColumn(self, column):
        # def isVisibleColumn(self, column) -> bool:
        """
        Vérifie si une colonne est visible.

        Args :
            column : La colonne à vérifier.

        Returns :
            bool : True si la colonne est visible, sinon False.
        """
        return column in self.__visibleColumns

    def visibleColumns(self):
        # def visibleColumns(self) -> list:
        """
        Retourne la liste des colonnes visibles.

        Returns :
            list : Liste des colonnes actuellement visibles.
        """
        return self.__visibleColumns

    def hideableColumns(self):
        # def hideableColumns(self) -> list:
        """
        Retourne les colonnes qui peuvent être masquées.

        Returns :
            list : Liste des colonnes masquables.
        """
        return [
            column
            for column in self._columns
            if column.name()
            not in self.settings.getlist(self.settingsSection(), "columnsalwaysvisible")
        ]

    def isHideableColumn(self, visibleColumnIndex):
        column = self.visibleColumns()[visibleColumnIndex]
        unhideableColumns = self.settings.getlist(
            self.settingsSection(), "columnsalwaysvisible"
        )
        return column.name() not in unhideableColumns

    def getColumnWidth(self, columnName):
        # def getColumnWidth(self, columnName: str) -> int:
        """
        Retourne la largeur d'une colonne par son nom.

        Args :
            columnName (str) : Le nom de la colonne.

        Returns :
            int : La largeur de la colonne.
        """
        columnWidths = self.settings.getdict(self.settingsSection(), "columnwidths")
        defaultWidth = (
            28 if columnName == "ordering" else hypertreelist._DEFAULT_COL_WIDTH
        )  # pylint: disable=W0212
        # Access to a protected member _DEFAULT_COL_WIDTH of a module
        return columnWidths.get(columnName, defaultWidth)

    def onResizeColumn(self, column, width):
        # def onResizeColumn(self, column, width: int):
        """
        Gère le redimensionnement d'une colonne et met à jour les paramètres.

        Args :
            column : La colonne redimensionnée.
            width (int) : La nouvelle largeur de la colonne.
        """
        columnWidths = self.settings.getdict(self.settingsSection(), "columnwidths")
        columnWidths[column.name()] = width
        self.settings.setdict(self.settingsSection(), "columnwidths", columnWidths)

    def validateDrag(self, dropItem, dragItems, columnIndex):
        # def validateDrag(self, dropItem, dragItems, columnIndex: int) -> bool:
        """
        Valide si un élément peut être déplacé (drag and drop) dans une colonne.

        Args :
            dropItem : L'élément où l'élément est déposé.
            dragItems : Les éléments en cours de déplacement.
            columnIndex (int) : L'index de la colonne affectée.

        Returns :
            bool : True si le déplacement est valide, sinon False.
        """
        if columnIndex == -1 or self.visibleColumns()[columnIndex].name() != "ordering":
            return None  # Normal behavior

        # Ordering

        if not self.isTreeViewer():  # where come from ?
            return True

        # Tree mode. Only allow drag if all selected items are siblings.
        if len(set([item.parent() for item in dragItems])) >= 2:
            wx.GetTopLevelParent(self).AddBalloonTip(
                self.settings,
                "treemanualordering",
                self,
                title=_("Reordering in tree mode"),
                getRect=lambda: wx.Rect(0, 0, 28, 16),
                message=_(
                    """When in tree mode, manual ordering is only possible when all selected items are siblings."""
                ),
            )
            return False

        # If they are, only allow drag at the same level
        if dragItems[0].parent() != (None if dropItem is None else dropItem.parent()):
            wx.GetTopLevelParent(self).AddBalloonTip(
                self.settings,
                "treechildrenmanualordering",
                self,
                title=_("Reordering in tree mode"),
                getRect=lambda: wx.Rect(0, 0, 28, 16),
                message=_(
                    """When in tree mode, you can only put objects at the same level (parent)."""
                ),
            )
            return False

        return True

    def getItemText(self, item, column=None):
        # def getItemText(self, item, column=None) -> str:
        """
        Retourne le texte d'un élément pour une colonne spécifique.

        Args :
            item : L'élément dont on veut obtenir le texte.
            column : La colonne à utiliser pour récupérer le texte.

        Returns :
            str : Le texte de l'élément pour la colonne spécifiée.
        """
        if column is None:
            column = 1 if self.hasOrderingColumn() else 0
        column = self.visibleColumns()[column]
        return column.render(item)

    def getItemImages(self, item, column=0):
        # def getItemImages(self, item, column: int = 0) -> dict:
        """
        Retourne les images associées à un élément pour une colonne spécifique.

        Args :
            item : L'élément dont on veut obtenir les images.
            column (int) : L'index de la colonne.

        Returns :
            dict : Dictionnaire des images associées à l'élément.
        """
        column = self.visibleColumns()[column]
        return column.imageIndices(item)

    def hasColumnImages(self, column):
        """
        Vérifie si une colonne contient des images.

        Args :
            column (int?) : La colonne à vérifier.

        Returns :
            bool : True si la colonne contient des images, sinon False.
        """
        return self.visibleColumns()[column].hasImages()

    def subjectImageIndices(self, item):
        # def subjectImageIndices(self, item) -> dict:
        """
        Retourne les indices des images associées au sujet d'un élément.

        Args :
            item : L'élément dont on veut obtenir les indices d'images.

        Returns :
            dict : Dictionnaire des indices d'images associés.
        """
        normalIcon = item.icon(recursive=True)
        selectedIcon = item.selectedIcon(recursive=True) or normalIcon
        normalImageIndex = self.imageIndex[normalIcon] if normalIcon else -1
        selectedImageIndex = self.imageIndex[selectedIcon] if selectedIcon else -1
        return {
            wx.TreeItemIcon_Normal: normalImageIndex,
            wx.TreeItemIcon_Expanded: selectedImageIndex,
        }

    def __startObserving(self, eventTypes):
        # def __startObserving(self, eventTypes: list):
        """
        Commence à observer les événements spécifiés pour les colonnes visibles.

        Args :
            eventTypes (list) : Liste des types d'événements à observer.
        """
        for eventType in eventTypes:
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType=eventType
                )

    def __stopObserving(self, eventTypes):
        # def __stopObserving(self, eventTypes: list):
        """
        Arrête d'observer les événements spécifiés pour les colonnes qui ne sont plus visibles.

        Args :
            eventTypes (list) : Liste des types d'événements à arrêter d'observer.
        """
        # Collecte les types d'événements auxquels les colonnes visibles sont encore intéressées
        # Collect the event types that the currently visible columns are
        # interested in and make sure we don't stop observing those event types.
        eventTypesOfVisibleColumns = []
        for column in self.visibleColumns():
            eventTypesOfVisibleColumns.extend(column.eventTypes())
        for eventType in eventTypes:
            if eventType not in eventTypesOfVisibleColumns:
                if eventType.startswith("pubsub"):
                    pub.unsubscribe(self.onAttributeChanged, eventType)
                else:
                    self.removeObserver(
                        self.onAttributeChanged_Deprecated, eventType=eventType
                    )

    def renderCategories(self, item):
        # def renderCategories(self, item: object) -> str:
        """
        Rendre les catégories associées à un élément donné.

        Args :
            item (object) : L'élément dont on veut afficher les catégories.

        Returns :
            str : Une chaîne contenant les catégories de l'élément.
        """
        return self.renderSubjectsOfRelatedItems(item, item.categories)

    def renderSubjectsOfRelatedItems(self, item, getItems):
        # def renderSubjectsOfRelatedItems(self, item: object, getItems) -> str:
        """
        Rendre les sujets des éléments liés (catégories ou autres relations).

        Args :
            item (object) : L'élément pour lequel on veut afficher les sujets liés.
            getItems (callable) : Fonction pour récupérer les éléments liés.

        Returns :
            str : Une chaîne des sujets des éléments liés.
        """
        subjects = []
        ownItems = getItems(recursive=False)
        if ownItems:
            subjects.append(self.renderSubjects(ownItems))
        isListViewer = (
            not self.isTreeViewer()
        )  # pylint: disable=E1101  # where come from ?
        if isListViewer or self.isItemCollapsed(item):
            childItems = [
                theItem
                for theItem in getItems(recursive=True, upwards=isListViewer)
                if theItem not in ownItems
            ]
            if childItems:
                subjects.append("(%s)" % self.renderSubjects(childItems))
        return " ".join(subjects)

    @staticmethod
    def renderSubjects(items):
        # def renderSubjects(items: list) -> str:
        """
        Rendre les sujets d'une liste d'éléments.

        Args :
            items (list) : Liste des éléments dont on veut obtenir les sujets.

        Returns :
            str : Une chaîne contenant les sujets des éléments, triés par ordre alphabétique.
        """
        subjects = [item.subject(recursive=True) for item in items]
        return ", ".join(sorted(subjects))

    @staticmethod
    def renderCreationDateTime(item, humanReadable=True):
        # def renderCreationDateTime(item: object, humanReadable: bool = True) -> str:
        """
        Rendre la date et l'heure de création d'un élément.

        Args :
            item (object) : L'élément dont on veut afficher la date de création.
            humanReadable (bool) : Indique si la date doit être formatée de manière lisible.

        Returns :
            str : La date et l'heure de création de l'élément.
        """
        return render.dateTime(item.creationDateTime(), humanReadable=humanReadable)

    @staticmethod
    def renderModificationDateTime(item, humanReadable=True):
        # def renderModificationDateTime(item: object, humanReadable: bool = True) -> str:
        """
        Rendre la date et l'heure de modification d'un élément.

        Args :
            item (object) : L'élément dont on veut afficher la date de modification.
            humanReadable (bool) : Indique si la date doit être formatée de manière lisible.

        Returns :
            str : La date et l'heure de modification de l'élément.
        """
        return render.dateTime(
            item.modificationDateTime(), humanReadable=humanReadable
        )

    def isItemCollapsed(self, item):
        # def isItemCollapsed(self, item: object) -> bool:
        # pylint: disable=E1101
        """
        Vérifie si un élément est réduit dans la vue actuelle (uniquement pertinent pour les vues arborescentes).

        Args :
            item (object) : L'élément à vérifier.

        Returns :
            bool : True si l'élément est réduit, False sinon.
        """
        return (
            not self.getItemExpanded(item)
            if self.isTreeViewer() and item.children()
            else False
        )

    # Unresolved attribute reference 'getItemExpanded' for class 'ViewerWithColumns'
    # Unresolved attribute reference 'isTreeViewer' for class 'ViewerWithColumns'  # where come from ? TreeViewer?


class SortableViewerWithColumns(
    mixin.SortableViewerMixin, ViewerWithColumns
):  # pylint: disable=W0223
    """
    Classe SortableViewerWithColumns, héritant de ViewerWithColumns et du mixin SortableViewerMixin.

    Cette classe permet de gérer des colonnes triables dans une vue. Elle ajoute la fonctionnalité de tri
    sur les colonnes d'une visionneuse. Lorsqu'une colonne est triée, la direction du tri (croissant ou décroissant)
    est indiquée par une icône spécifique.

    Hérite de :
        ViewerWithColumns : Gestion des colonnes dans la visionneuse.
        SortableViewerMixin : Ajoute la capacité de tri des éléments dans la visionneuse.

    Explication des méthodes :

    initColumn : Initialise une colonne et vérifie si cette colonne est celle utilisée pour le tri. Si c'est le cas, elle affiche l'icône de tri dans la colonne et montre l'ordre de tri (croissant ou décroissant).
    setSortOrderAscending : Définit l'ordre de tri en croissant et met à jour l'affichage de l'icône de tri pour refléter cette direction.
    sortBy : Trie les éléments par une colonne donnée. Une fois le tri effectué, la colonne utilisée pour le tri et la direction du tri sont affichées dans la vue.
    showSortColumn : Affiche l'icône de tri dans la colonne actuellement utilisée pour le tri.
    showSortOrder : Affiche une icône indiquant la direction du tri (une flèche vers le haut pour un tri ascendant, une flèche vers le bas pour un tri descendant).
    getSortOrderImage : Retourne le nom de l'icône correspondant à la direction du tri (flèche vers le haut pour le tri ascendant et flèche vers le bas pour le tri descendant).

    Cette classe utilise les fonctionnalités du mixin.SortableViewerMixin pour ajouter des capacités de tri à la visionneuse avec colonnes.
      Les méthodes gèrent aussi bien l'initialisation des colonnes que la gestion du tri avec des indicateurs visuels (icônes).
    """
    def initColumn(self, column):
        """
        Initialise une colonne et, si elle est utilisée pour le tri, affiche l'icône de tri correspondante.

        Args:
            column: La colonne à initialiser.
        """
        super().initColumn(column)
        if self.isSortedBy(column.name()):
            self.widget.showSortColumn(column)
            self.showSortOrder()

    def setSortOrderAscending(self, *args, **kwargs):  # pylint: disable=W0221
        """
        Définit l'ordre de tri en croissant et met à jour l'affichage de l'icône de tri.

        Args:
            *args: Arguments supplémentaires pour la méthode de tri.
            **kwargs: Arguments nommés supplémentaires pour la méthode de tri.
        """
        super().setSortOrderAscending(*args, **kwargs)
        self.showSortOrder()

    def sortBy(self, *args, **kwargs):  # pylint: disable=W0221
        """
        Trie les éléments de la visionneuse par une colonne spécifique et met à jour l'affichage de l'icône de tri.

        Args:
            *args: Arguments supplémentaires pour la méthode de tri.
            **kwargs: Arguments nommés supplémentaires pour la méthode de tri.
        """
        super().sortBy(*args, **kwargs)
        self.showSortColumn()
        self.showSortOrder()

    def showSortColumn(self):
        """
        Affiche la colonne actuellement utilisée pour le tri, avec l'icône correspondante.
        """
        for column in self.columns():
            if self.isSortedBy(column.name()):
                self.widget.showSortColumn(column)
                break

    def showSortOrder(self):
        """
        Affiche l'icône indiquant l'ordre du tri (ascendant ou descendant) dans la visionneuse.
        """
        self.widget.showSortOrder(self.imageIndex[self.getSortOrderImage()])

    def getSortOrderImage(self):
        # def getSortOrderImage(self) -> str:
        """
        Retourne l'image associée à la direction du tri.

        Returns :
            str : Le nom de l'icône pour indiquer le tri ascendant ou descendant.
        """
        return "arrow_up_icon" if self.isSortOrderAscending() else "arrow_down_icon"
