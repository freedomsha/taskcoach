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

Ce fichier définit la vue des pièces jointes (AttachmentViewer).
"""

import os
import wx

from taskcoachlib import command, widgets  # besoin de Column, VirtualListCtrl, AssignImageList, SetColumnWidth
from taskcoachlib.domain import attachment
# from taskcoachlib.domain.attachment import attachment, sorter
# from taskcoachlib.domain.attachment import *
from taskcoachlib.i18n import _
from taskcoachlib.gui import dialog, uicommand
import taskcoachlib.gui.menu
# from taskcoachlib.gui.menu import *
from taskcoachlib.gui.viewer import base, mixin


class AttachmentViewer(mixin.AttachmentDropTargetMixin,  # pylint: disable=W0223
                       base.SortableViewerWithColumns,
                       mixin.SortableViewerForAttachmentsMixin,
                       mixin.SearchableViewerMixin, mixin.NoteColumnMixin,
                       base.ListViewer):
    """
    Vue des pièces jointes dans Task Coach.

    Cette classe gère l'affichage, le tri, la recherche, et l'interaction avec les pièces jointes
    associées aux tâches. Elle permet également la gestion des colonnes et des menus contextuels
    pour les pièces jointes.
    """

    # Classe de tri pour les pièces jointes
    # SorterClass = sorter.AttachmentSorter  # don't exist; Ne semble pas exister dans le code actuel noqa: F405
    # SorterClass = taskcoachlib.domain.attachment.AttachmentSorter
    SorterClass = attachment.AttachmentSorter
    viewerImages = base.ListViewer.viewerImages + ["fileopen", "fileopen_red"]

    def __init__(self, *args, **kwargs):
        """
        Initialise la vue des pièces jointes.

        Args :
            *args : Arguments positionnels.
            **kwargs : Arguments nommés et spécifiques, comme les pièces jointes à afficher.
        """
        self.attachments = kwargs.pop("attachmentsToShow")
        kwargs.setdefault("settingssection", "attachmentviewer")
        super().__init__(*args, **kwargs)

    def _addAttachments(self, attachments, item, **itemDialogKwargs):
        """
        Ajoute des pièces jointes. Ne pas ajouter de pièces jointes à d'autres pièces jointes.

        Args :
            attachments (list) : Liste des pièces jointes à ajouter.
            item : Élément auquel ajouter les pièces jointes.
            **itemDialogKwargs : Arguments supplémentaires pour la boîte de dialogue d'ajout.
        """
        # Don't try to add attachments to attachments.
        print(f"viewer.attachment.AttachmentViewer._addAttachments : 📌 [DEBUG] Ajout des attachements : {attachments} dans self={self}")
        super()._addAttachments(attachments, None, **itemDialogKwargs)

    def domainObjectsToView(self):
        """
        Retourne les objets de domaine à afficher dans cette vue.

        Returns :
            (list) : Liste des pièces jointes à afficher.
        """
        return self.attachments

    def isShowingAttachments(self):
        """
        Vérifie si la vue affiche des pièces jointes.

        Returns :
            (bool) : True si des pièces jointes sont affichées, sinon False.
        """
        return True

    def curselectionIsInstanceOf(self, class_):
        """
        Vérifie si la sélection courante est une instance de la classe spécifiée.

        Args :
            class_ (type) : Classe à vérifier.

        Returns :
            (bool) : True si la sélection est une instance de la classe spécifiée.
                """
        return class_ == attachment.Attachment
        # return isinstance(class_, attachment.Attachment)

    def createWidget(self):
        """
        Crée et retourne le widget utilisé pour afficher les pièces jointes.

        Returns :
            wx.VirtualListCtrl : Le widget utilisé pour afficher les pièces jointes.
        """
        imageList = self.createImageList()
        itemPopupMenu = taskcoachlib.gui.menu.AttachmentPopupMenu(
            self.parent, self.settings, self.presentation(), self
        )
        columnPopupMenu = taskcoachlib.gui.menu.ColumnPopupMenu(self)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        self._columns = self._createColumns()

        # Création du Treeview
        widget = widgets.VirtualListCtrl(self, self.columns(), self.onSelect,
                                         uicommand.Edit(viewer=self),
                                         itemPopupMenu, columnPopupMenu,
                                         resizeableColumn=1, **self.widgetCreationKeywordArguments())
        widget.SetColumnWidth(0, 150)
        widget.AssignImageList(imageList, wx.IMAGE_LIST_SMALL)
        return widget

    def _createColumns(self):
        """
        Crée et retourne les colonnes utilisées pour afficher les informations des pièces jointes.

        Returns :
            (list) : Liste des colonnes.
        """
        # Unresolved attribute reference 'notesChangedEventType' for class '*Attachment'
        return [
            widgets.Column(
                "type",
                _("Type"),
                "",
                width=self.getColumnWidth("type"),
                imageIndicesCallback=self.typeImageIndices,
                renderCallback=lambda item: "",
                resizeCallback=self.onResizeColumn,
            ),
            widgets.Column(
                "subject",
                _("Subject"),
                attachment.FileAttachment.subjectChangedEventType(),
                attachment.URIAttachment.subjectChangedEventType(),
                attachment.MailAttachment.subjectChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self,
                    value="subject",
                    menuText=_("Sub&ject"),
                    helpText=_("Sort by subject"),
                ),
                width=self.getColumnWidth("subject"),
                renderCallback=lambda item: item.subject(),
                resizeCallback=self.onResizeColumn,
            ),
            widgets.Column(
                "description",
                _("Description"),
                attachment.FileAttachment.descriptionChangedEventType(),
                attachment.URIAttachment.descriptionChangedEventType(),
                attachment.MailAttachment.descriptionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self,
                    value="description",
                    menuText=_("&Description"),
                    helpText=_("Sort by description"),
                ),
                width=self.getColumnWidth("description"),
                renderCallback=lambda item: item.description(),
                resizeCallback=self.onResizeColumn,
            ),
            widgets.Column(
                "notes",
                "",
                attachment.FileAttachment.notesChangedEventType(),  # pylint: disable=E1101
                attachment.URIAttachment.notesChangedEventType(),  # pylint: disable=E1101
                attachment.MailAttachment.notesChangedEventType(),  # pylint: disable=E1101
                width=self.getColumnWidth("notes"),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndicesCallback=self.noteImageIndices,  # pylint: disable=E1101
                headerImageIndex=self.imageIndex["note_icon"],
                renderCallback=lambda item: "",
                resizeCallback=self.onResizeColumn,
            ),
            widgets.Column(
                "creationDateTime",
                _("Creation date"),
                width=self.getColumnWidth("creationDateTime"),
                renderCallback=self.renderCreationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self,
                    value="creationDateTime",
                    menuText=_("&Creation date"),
                    helpText=_("Sort by creation date"),
                ),
                resizeCallback=self.onResizeColumn,
            ),
            widgets.Column(
                "modificationDateTime",
                _("Modification date"),
                width=self.getColumnWidth("modificationDateTime"),
                renderCallback=self.renderModificationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self,
                    value="modificationDateTime",
                    menuText=_("&Modification date"),
                    helpText=_("Sort by last modification date"),
                ),
                resizeCallback=self.onResizeColumn,
                *attachment.Attachment.modificationEventTypes()
            ),
        ]

    def createColumnUICommands(self):
        """
        Crée et retourne les commandes de l'interface utilisateur pour gérer les colonnes.

        Returns :
            (list) : Liste des commandes pour les colonnes.
        """
        return [
            uicommand.ToggleAutoColumnResizing(viewer=self,
                                               settings=self.settings),
            None,
            uicommand.ViewColumn(
                menuText=_("&Description"),
                helpText=_("Show/hide description column"),
                setting="description",
                viewer=self
            ),
            uicommand.ViewColumn(
                menuText=_("&Notes"),
                helpText=_("Show/hide notes column"),
                setting="notes",
                viewer=self
            ),
            uicommand.ViewColumn(
                menuText=_("&Creation date"),
                helpText=_("Show/hide creation date column"),
                setting="creationDateTime",
                viewer=self
            ),
            uicommand.ViewColumn(
                menuText=_("&Modification date"),
                helpText=_("Show/hide last modification date column"),
                setting="modificationDateTime",
                viewer=self
            )
        ]

    def createCreationToolBarUICommands(self):
        """
        Crée et retourne les commandes de la barre d'outils pour la création de pièces jointes.

        Returns :
            (tuple) : Les commandes de création.
        """
        return (uicommand.AttachmentNew(attachments=self.presentation(),
                                        settings=self.settings,
                                        viewer=self),) + \
            super().createCreationToolBarUICommands()

    def createActionToolBarUICommands(self):
        """
        Crée et retourne les commandes de la barre d'outils pour les actions sur les pièces jointes.

        Returns :
            (tuple) : Les commandes d'action.
        """
        return (uicommand.AttachmentOpen(attachments=attachment.AttachmentList(),
                                         viewer=self, settings=self.settings),) + \
            super().createActionToolBarUICommands()

    def typeImageIndices(self, anAttachment, exists=os.path.exists):  # pylint: disable=W0613
        """
        Retourne les indices des images associées à un type de pièce jointe.

        Args :
            anAttachment (attachment.Attachment) : La pièce jointe.
            exists (callable) : Fonction pour vérifier l'existence du fichier.

        Returns :
            (dict) : Dictionnaire des indices d'images en fonction de l'icône standard de wx.
        """
        if anAttachment.type_ == "file":
            attachmentBase = self.settings.get("file", "attachmentbase")
            if exists(anAttachment.normalizedLocation(attachmentBase)):
                index = self.imageIndex["fileopen"]
            else:
                index = self.imageIndex["fileopen_red"]
        else:
            try:
                index = self.imageIndex[
                    {"uri": "earth_blue_icon", "mail": "envelope_icon"}[
                        anAttachment.type_
                    ]
                ]
            except KeyError:
                index = -1
        return {wx.TreeItemIcon_Normal: index}

    def itemEditorClass(self):
        """
        Retourne la classe de l'éditeur d'éléments.

        Returns :
            (type) : Classe de l'éditeur d'éléments.
        """
        return dialog.editor.AttachmentEditor

    def newItemCommandClass(self):
        """
        Classe de commande pour créer un nouvel élément. Non implémenté ici.

        Raises :
            NotImplementedError : Non implémenté.
        """
        raise NotImplementedError  # pragma: no cover

    def newSubItemCommandClass(self):
        """
        Classe de commande pour créer un sous-élément. Non applicable ici.

        Returns :
            None : Cette vue ne supporte pas la création de sous-éléments.
        """
        return None

    def deleteItemCommandClass(self):
        """
        Classe de commande pour supprimer un élément. Non implémenté ici.

        Raises :
            NotImplementedError : Non implémenté.
        """
        raise NotImplementedError  # pragma: no cover

    def cutItemCommandClass(self):
        """
        Classe de commande pour couper un élément. Non implémenté ici.

        Raises :
            NotImplementedError : Non implémenté.
        """
        raise NotImplementedError  # pragma: no cover
