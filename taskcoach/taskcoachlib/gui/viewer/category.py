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

# from future import standard_library

# standard_library.install_aliases()
import wx
from taskcoachlib import command, widgets
from taskcoachlib.domain import category
from taskcoachlib.i18n import _
# from taskcoachlib.gui import uicommand, dialog, menu
from taskcoachlib.gui.uicommand import uicommand
from taskcoachlib.gui import dialog
# from taskcoachlib.gui.dialog.editor import CategoryEditor  # circular import
import taskcoachlib.gui.menu
# from taskcoachlib.gui.menu import *
from taskcoachlib.gui.viewer import base
from taskcoachlib.gui.viewer import mixin
from taskcoachlib.gui.viewer import inplace_editor


class BaseCategoryViewer(mixin.AttachmentDropTargetMixin,  # pylint: disable=W0223
                         mixin.FilterableViewerMixin,
                         mixin.SortableViewerForCategoriesMixin,
                         mixin.SearchableViewerMixin,
                         base.WithAttachmentsViewerMixin,
                         mixin.NoteColumnMixin, mixin.AttachmentColumnMixin,
                         base.SortableViewerWithColumns, base.TreeViewer):
    """
       Classe de base pour la vue des catégories.

       Cette classe gère l'affichage et l'interaction avec les catégories dans une vue arborescente,
       y compris la gestion des pièces jointes, des filtres, et du tri.
       """
    SorterClass = category.CategorySorter
    defaultTitle = _("Categories")
    defaultBitmap = "folder_blue_arrow_icon"

    def __init__(self, *args, **kwargs):
        """
               Initialise la classe BaseCategoryViewer.

               Args:
                   *args: Arguments positionnels.
                   **kwargs: Arguments nommés.
               """
        # kwargs.setdefault('settingsSection', 'category_viewer')
        # il ne trouvait pas de category_viewer
        kwargs.setdefault("settingsSection", "categoryviewer")
        super().__init__(*args, **kwargs)
        for eventType in [category.Category.subjectChangedEventType(),
                          category.Category.appearanceChangedEventType(),
                          category.Category.exclusiveSubcategoriesChangedEventType(),
                          category.Category.filterChangedEventType()]:
            self.registerObserver(self.onAttributeChanged_Deprecated,
                                  eventType)

    def domainObjectsToView(self):
        """
                Retourne les objets de domaine à afficher dans la vue.

                Returns:
                    list: Liste des catégories à afficher.
                """
        return self.taskFile.categories()

    def curselectionIsInstanceOf(self, class_):
        """
                Vérifie si la sélection actuelle est une instance de la classe spécifiée.

                Args:
                    class_ (type): La classe à vérifier.

                Returns:
                    bool: True si la sélection est une instance de la classe spécifiée.
                """
        return class_ == category.Category

    def createWidget(self):
        """
                Crée et retourne le widget utilisé pour afficher les catégories.

                Returns:
                    wx.CheckTreeCtrl: Le widget CheckTreeCtrl utilisé pour afficher les catégories.
                """
        imageList = self.createImageList()  # Has side-effects
        self._columns = self._createColumns()
        itemPopupMenu = self.createCategoryPopupMenu()
        columnPopupMenu = taskcoachlib.gui.menu.ColumnPopupMenu(self)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        widget = widgets.CheckTreeCtrl(self, self._columns,
                                       self.onSelect, self.onCheck,
                                       uicommand.Edit(viewer=self),
                                       uicommand.CategoryDragAndDrop(viewer=self, categories=self.presentation()),
                                       itemPopupMenu, columnPopupMenu,
                                       resizeableColumn=1 if self.hasOrderingColumn() else 0,
                                       validateDrag=self.validateDrag,
                                       **self.widgetCreationKeywordArguments())
        if self.hasOrderingColumn():
            widget.SetMainColumn(1)
        widget.AssignImageList(imageList)  # pylint: disable=E1101
        return widget

    def createCategoryPopupMenu(self, localOnly=False):
        """
                Crée et retourne le menu contextuel pour les catégories.

                Args:
                    localOnly (bool, optional): Indique si le menu est local seulement. Par défaut à False.

                Returns:
                    wx.Menu: Le menu contextuel pour les catégories.
                """
        return taskcoachlib.gui.menu.CategoryPopupMenu(self.parent, self.settings, self.taskFile,
                                                       self, localOnly)

    def _createColumns(self):
        """
                Crée et retourne les colonnes pour l'affichage des catégories.

                Returns:
                    list: Liste des colonnes créées.
                """
        # pylint: disable=W0142,E1101
        kwargs = dict(resizeCallback=self.onResizeColumn)
        columns = [widgets.Column(
                "ordering",
                "",
                category.Category.orderingChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="ordering"
                ),
                imageIndicesCallback=self.orderingImageIndices,
                renderCallback=lambda category: "",
                width=self.getColumnWidth("ordering")
            ), widgets.Column(
                "subject",
                _("Subject"),
                category.Category.subjectChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="subject"
                ),
                imageIndicesCallback=self.subjectImageIndices,
                width=self.getColumnWidth("subject"),
                editCallback=self.onEditSubject,
                editControl=inplace_editor.SubjectCtrl,
                **kwargs
            ), widgets.Column(
                "description",
                _("Description"),
                category.Category.descriptionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="description"
                ),
                renderCallback=lambda category: category.description(),
                width=self.getColumnWidth("description"),
                editCallback=self.onEditDescription,
                editControl=inplace_editor.DescriptionCtrl,
                **kwargs
            ), widgets.Column(
                "attachments",
                "",
                category.Category.attachmentsChangedEventType(),  # pylint: disable=E1101
                width=self.getColumnWidth("attachments"),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndicesCallback=self.attachmentImageIndices,
                headerImageIndex=self.imageIndex["paperclip_icon"],
                renderCallback=lambda category: "",
                **kwargs
            # )]
            # columns.append(
            # widgets.Column(
            ), widgets.Column(
                "notes",
                "",
                category.Category.notesChangedEventType(),  # pylint: disable=E1101
                width=self.getColumnWidth("notes"),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndicesCallback=self.noteImageIndices,
                headerImageIndex=self.imageIndex["note_icon"],
                renderCallback=lambda category: "",
                **kwargs
            ),
            # )
            # columns.append(
            widgets.Column(
                "creationDateTime",
                _("Creation date"),
                width=self.getColumnWidth("creationDateTime"),
                renderCallback=self.renderCreationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="creationDateTime"
                ),
                **kwargs
            ),
            # )
            # columns.append(
            widgets.Column(
                "modificationDateTime",
                _("Modification date"),
                width=self.getColumnWidth("modificationDateTime"),
                renderCallback=self.renderModificationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="modificationDateTime"
                ),
                *category.Category.modificationEventTypes(),
                **kwargs
            )]
        return columns

    def createCreationToolBarUICommands(self):
        """
               Crée et retourne les commandes de la barre d'outils pour la création de catégories.

               Returns:
                   tuple: Les commandes de création.
               """
        return (uicommand.CategoryNew(categories=self.presentation(),
                                      settings=self.settings),
                uicommand.NewSubItem(viewer=self))

    def createColumnUICommands(self):
        """
                Crée et retourne les commandes pour la gestion des colonnes.

                Returns:
                    list: Liste des commandes pour les colonnes.
                """
        commands = [
            uicommand.ToggleAutoColumnResizing(
                viewer=self, settings=self.settings
            ),
            None,
            uicommand.ViewColumn(
                menuText=_("&Manual ordering"),
                helpText=_("Show/hide the manual ordering column"),
                setting="ordering",
                viewer=self
            ),
            uicommand.ViewColumn(
                menuText=_("&Description"),
                helpText=_("Show/hide description column"),
                setting="description",
                viewer=self
            ),
            uicommand.ViewColumn(
                menuText=_("&Attachments"),
                helpText=_("Show/hide attachments column"),
                setting="attachments",
                viewer=self
            )
        ]
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Notes"),
                helpText=_("Show/hide notes column"),
                setting="notes",
                viewer=self
            )
        )
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Creation date"),
                helpText=_("Show/hide creation date column"),
                setting="creationDateTime",
                viewer=self
            )
        )
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Modification date"),
                helpText=_("Show/hide last modification date column"),
                setting="modificationDateTime",
                viewer=self,
            )
        )
        return commands

    def onAttributeChanged(self, newValue, sender):
        """
                Gère les événements de changement d'attribut.

                Args:
                    newValue: La nouvelle valeur de l'attribut.
                    sender: L'objet qui a envoyé l'événement.
                """
        super().onAttributeChanged(newValue, sender)

    def onAttributeChanged_Deprecated(self, event):
        """
                Gère les événements de changement d'attributs obsolètes.

                Args:
                    event: L'événement.
                """
        if category.Category.exclusiveSubcategoriesChangedEventType() in event.types():
            # We need to refresh the children of the changed item as well
            # because they have to use radio buttons instead of checkboxes, or
            # vice versa:
            # Nous devons également actualiser les enfants de l'élément modifié
            # car ils doivent utiliser des boutons radio au lieu de cases à cocher, ou vice versa:
            items = event.sources()
            for item in items.copy():
                items |= set(item.children())
            self.widget.RefreshItems(*items)  # pylint: disable=W0142
        else:
            super().onAttributeChanged_Deprecated(event)

    def onCheck(self, event, final):
        """
                Gère les événements de sélection des cases à cocher.

                Args:
                    event: L'événement de sélection.
                    final: Indique si c'est la sélection finale.
                """
        categoryToFilter = self.widget.GetItemPyData(event.GetItem())
        categoryToFilter.setFiltered(event.GetItem().IsChecked())
        self.sendViewerStatusEvent()  # Notify status observers like the status bar

    def getIsItemChecked(self, item):
        """
                Vérifie si un élément est coché.

                Args:
                    item: L'élément à vérifier.

                Returns:
                    bool: True si l'élément est coché.
                """
        if isinstance(item, category.Category):
            return item.isFiltered()
        return False

    # @staticmethod
    def getItemParentHasExclusiveChildren(self, item):
        """
               Vérifie si le parent de l'élément a des sous-catégories exclusives.

               Args:
                   item: L'élément à vérifier.

               Returns:
                   bool: True si le parent a des sous-catégories exclusives.
               """
        parent = item.parent()
        return parent and parent.hasExclusiveSubcategories()

    def isShowingCategories(self):
        """
                Vérifie si la vue affiche des catégories.

                Returns:
                    bool: True si la vue affiche des catégories.
                """
        return True

    def statusMessages(self):
        """
                Retourne les messages de statut à afficher.

                Returns:
                    tuple: Messages de statut.
                """
        status1 = _("Categories: %d selected, %d total") % (
            len(self.curselection()), len(self.presentation()))
        filteredCategories = self.presentation().filteredCategories()
        status2 = _("Status: %d filtered") % len(filteredCategories)
        return status1, status2

    def itemEditorClass(self):
        """
               Retourne la classe de l'éditeur d'éléments.

               Returns:
                   type: Classe de l'éditeur d'éléments.
               """
        return dialog.editor.CategoryEditor
        # from taskcoachlib.gui.dialog.editor import CategoryEditor
        # return CategoryEditor

    def newItemCommandClass(self):
        """
               Retourne la classe de commande pour créer un nouvel élément.

               Returns:
                   type: Classe de commande pour créer un nouvel élément.
               """
        return command.NewCategoryCommand

    def newSubItemCommandClass(self):
        """
               Retourne la classe de commande pour créer un nouvel sous-élément.

               Returns:
                   type: Classe de commande pour créer un nouvel sous-élément.
               """
        return command.NewSubCategoryCommand

    def deleteItemCommandClass(self):
        """
                Retourne la classe de commande pour supprimer un élément.

                Returns:
                    type: Classe de commande pour supprimer un élément.
                """
        return command.DeleteCategoryCommand


class CategoryViewer(BaseCategoryViewer):  # pylint: disable=W0223
    """
    Vue des catégories, héritant de BaseCategoryViewer.
    """

    def __init__(self, *args, **kwargs):
        """
                Initialise la classe CategoryViewer.

                Args:
                    *args: Arguments positionnels.
                    **kwargs: Arguments nommés.
                """
        # nouvelle ligne pour compter les instances
        # print('taskcoachlib.gui.viewer.category.CategoryViewer')
        # CategoryViewer._instance_count = 0
        super().__init__(*args, **kwargs)
        self.filterUICommand.setChoice(self.settings.getboolean("view", "categoryfiltermatchall"))

    def createModeToolBarUICommands(self):
        """
                Crée et retourne les commandes pour la barre d'outils du mode.

                Returns:
                    tuple: Les commandes de la barre d'outils du mode.
                """
        # pylint: disable=W0201
        self.filterUICommand = uicommand.CategoryViewerFilterChoice(
            settings=self.settings)
        # return super().createModeToolBarUICommands() + self.filterUICommand
        # TypeError: can only concatenate tuple (not "CategoryViewerFilterChoice") to tuple
        # Exception ignored in atexit callback: <built-in function _wxPyCleanup>
        return super().createModeToolBarUICommands() + (self.filterUICommand,)
