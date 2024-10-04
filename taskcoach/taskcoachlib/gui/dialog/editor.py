# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2012 Nicola Chiapolini <nicola.chiapolini@physik.uzh.ch>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Carl Zmola <zmola@acm.org>

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


Module `editor.py` - Gère les pages d'édition des objets dans Task Coach.

Ce module contient diverses classes pour représenter des pages d'édition pour différents
types d'objets (tâches, catégories, notes, etc.) dans Task Coach. Il fournit également
les mécanismes pour observer les changements sur ces objets et les refléter dans
l'interface utilisateur.

Classes :
    Page : Classe de base pour les pages d'édition.
    SubjectPage : Gère l'édition du sujet d'un objet.
    TaskSubjectPage : Gère l'édition du sujet d'une tâche avec des priorités.
    CategorySubjectPage : Gère l'édition des catégories.
    AttachmentSubjectPage : Gère l'édition des pièces jointes.
    TaskAppearancePage : Gère l'apparence d'une tâche.
    DatesPage : Gère les dates liées aux tâches.
    ProgressPage : Gère les informations de progression d'une tâche.
    BudgetPage : Gère le budget associé à une tâche.
    EffortPage : Gère l'effort d'une tâche.
    CategoriesPage : Gère les catégories associées aux objets.
    AttachmentsPage : Gère les pièces jointes associées à une tâche ou autre objet.
    NotesPage : Gère les notes associées à un objet.
    PrerequisitesPage : Gère les prérequis associés à une tâche.
    TaskEditBook : Conteneur pour les pages d'édition des tâches.
    CategoryEditBook : Conteneur pour les pages d'édition des catégories.
    NoteEditBook : Conteneur pour les pages d'édition des notes.
    AttachmentEditBook : Conteneur pour les pages d'édition des pièces jointes.
    EffortEditBook : Gère l'édition des efforts.
    Editor : Fenêtre principale de l'éditeur pour différents objets.
"""

# from builtins import str
# from builtins import range

import wx
import logging

import os.path

from taskcoachlib import widgets, patterns, command, operating_system, render
from taskcoachlib.domain import task, date, note, attachment
from taskcoachlib.gui import viewer, uicommand, windowdimensionstracker
# import taskcoachlib.gui.viewer.effort
from taskcoachlib.gui.viewer.effort import EffortViewer
from taskcoachlib.gui.viewer.attachment import AttachmentViewer
from taskcoachlib.gui.viewer.note import BaseNoteViewer
from taskcoachlib.gui.viewer.task import CheckableTaskViewer
from taskcoachlib.gui.viewer.category import BaseCategoryViewer  # circular import

# for don't have AttributeError: partially initialized module 'taskcoachlib.gui.*'
# has no attribute '*' (most likely due to a circular import) :
# from taskcoachlib.gui.viewer import category, attachment, note, task
# from . import entry, attributesync
from taskcoachlib.gui.dialog import entry, attributesync
from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _
# try:
from pubsub import pub

# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
# else:
#    from wx.lib.pubsub import pub
from taskcoachlib.thirdparty import smartdatetimectrl as sdtc
from taskcoachlib.help.balloontips import BalloonTipManager


# Classe Page qui représente une page d'édition
class Page(patterns.Observer, widgets.BookPage):
    """
    Classe de base pour les pages d'édition dans Task Coach.

    Gère l'affichage et la synchronisation des attributs des objets de domaine.

    Attributs :
        columns (int) : Nombre de colonnes dans la page.

    Méthodes :
        __init__(self, items, *args, **kwargs) : Initialise la page avec les objets à éditer.
        selected(self) : Méthode appelée lorsque la page est sélectionnée.
        addEntries(self) : Ajoute les entrées à la page (doit être implémentée par les sous-classes).
        entries(self) : Retourne un dictionnaire des entrées par nom de colonne.
        setFocusOnEntry(self, column_name) : Définit le focus sur une entrée spécifique.
        close(self) : Ferme la page et libère les ressources.
    """
    columns = 2  # Par défaut, deux colonnes pour l'édition.

    def __init__(self, items, *args, **kwargs):
        # def __init__(self, items: List, *args, **kwargs) -> None:
        """
        Initialise la page avec les éléments à éditer.

        Args:
            items (list): Liste des objets de domaine à éditer.
        """
        self.items = items
        # self.__observers = []
        super().__init__(columns=self.columns, *args, **kwargs)
        self.addEntries()
        self.fit()

    def selected(self):
        """Méthode appelée lorsque la page est sélectionnée.

        Méthode appelée lorsque la page est sélectionnée dans l'interface utilisateur.
        Peut être utilisée pour mettre à jour ou rafraîchir la page.
        """
        pass  # Implémentation des actions lors de la sélection de la page.


    def addEntries(self):
        """Ajoute les entrées de la page. Doit être implémentée par les sous-classes.

        Méthode à implémenter dans les sous-classes pour ajouter des champs d'entrée (widgets).
        Cette méthode définit la logique spécifique à chaque type de page.
        """
        # raise NotImplementedError  # Méthode à implémenter par les sous-classes.
        pass

    def entries(self):
        """Un mappage des noms de colonnes avec les entrées de cette page d'éditeur.

        Retourne un dictionnaire des entrées de la page par nom de colonne.

        Retourne un dictionnaire contenant les champs d'entrée ajoutés à la page.

        Returns :
            dict : Les champs d'entrée ajoutés par `addEntries`."""
        return dict()  # Retourne les champs d'édition.


    def setFocusOnEntry(self, column_name):
        """
        Définit le focus sur une entrée spécifique.

        Définit le focus sur un champ d'entrée spécifique basé sur le nom de la colonne.

        Args:
            column_name (str) : Le nom de la colonne de l'entrée sur laquelle positionner le focus.
        """
        # Définit le focus sur une colonne particulière.
        try:
            the_entry = self.entries()[column_name]
        except KeyError:
            the_entry = self.entries()["firstEntry"]
        self.__set_selection_and_focus(the_entry)

    def __set_selection_and_focus(self, the_entry):
        """Définit la sélection et le focus sur une entrée.

        Si l'entrée contient du texte sélectionnable, sélectionnez le texte afin que l'utilisateur
        puisse commencer à taper dessus immédiatement, sauf sous Linux car il
        écrase le presse-papiers X.

        Args:
            the_entry (wx.TextCtrl): L'entrée à sélectionner et à mettre en focus.
        """
        if self.focusTextControl():
            the_entry.SetFocus()
            try:
                if operating_system.isWindows() and isinstance(the_entry, wx.TextCtrl):
                    # XXXFIXME: See SR #325. Disable this for Now.

                    # This ensures that if the TextCtrl value is more than can
                    # be displayed, it will display the start instead of the
                    # end:
                    try:
                        import SendKeys
                    except ImportError:
                        from taskcoachlib.thirdparty import (
                            SendKeys,
                        )  # pylint: disable=W0404
                    SendKeys.SendKeys("{END}+{HOME}")

                    # Scrol to left...
                    the_entry.SetInsertionPoint(0)
                the_entry.SetSelection(-1, -1)  # Sélectionner tout le texte
            except (AttributeError, TypeError):
                pass  # Not a TextCtrl

    def focusTextControl(self):
        """Retourne True si le contrôle de texte doit recevoir le focus."""
        return True

    def close(self):
        """Ferme la page et nettoie les ressources.

        Ferme la page d'édition et nettoie les ressources associées.
        Peut être utilisé pour libérer les ressources graphiques ou observer les objets.
        """
        self.removeInstance()
        for entry in list(self.entries().values()):
            if isinstance(entry, widgets.DateTimeCtrl):
                entry.Cleanup()
        # TODO: try:
        # for each_entry in list(self.entries().values()):
        #     if isinstance(each_entry, widgets.DateTimeCtrl):
        #         each_entry.Cleanup()

# Les autres classes de la même manière...


class SubjectPage(Page):
    """
        Page d'édition pour modifier le sujet d'un objet dans Task Coach.

        Cette page permet à l'utilisateur de modifier le champ "sujet" des objets,
        qui peut représenter le titre ou la description courte de l'objet.

        Méthodes :
            addEntries(self) : Ajoute les champs d'entrée pour l'édition du sujet.
            subject(self) : Retourne l'objet d'édition du sujet.
        """
    pageName = "subject"
    pageTitle = _("Description")
    pageIcon = "pencil_icon"

    def __init__(self, items, parent, settings, *args, **kwargs):
        """
    Initializes the SubjectPage with the following arguments:

    - items: A list of task objects representing the selected tasks.
    - parent: The parent window of this page.
    - settings: The application settings object.
    """
        self._modificationTextEntry = None
        self._descriptionSync = None
        self._subjectSync = None
        self._descriptionEntry = None
        self._subjectEntry = None
        self._settings = settings
        super().__init__(items, parent, *args, **kwargs)

    def SetFocus(self):
        """
    Sets focus to the page, but avoids selecting the text control on GTK platforms
    to prevent overriding the X selection.
    """
        # Skip this on GTK because it selects the control's text, which
        # overrides the X selection. Simply commenting out the SetFocus() in
        # __load_perspective is not enough because the aui notebook calls this
        # when the user selects a tab.
        if self.focusTextControl():
            super().SetFocus()

    def focusTextControl(self):
        """
    Checks the application settings to determine if text controls should receive
    focus on GTK platforms.
    """
        return self._settings.getboolean("os_linux", "focustextentry")

    def addEntries(self):
        """
        Ajoute les champs d'entrée spécifiques pour l'édition du sujet.

        Adds controls for subject, description, creation date/time, and modification date/time.
        """
        # Ajoute les widgets pour éditer le sujet.
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()
        # TODO : à remplacer par
        # self.addDateTimeEntries("Creation", "creationDateTime")
        # self.addDateTimeEntries("Modification", "modificationDateTime")

    # def subject(self):
    #     """
    #     Retourne l'objet sujet à éditer.
    #
    #     Returns:
    #         Objet à éditer, généralement un texte.
    #     """
    #     pass
    def addSubjectEntry(self):
        # pylint: disable=W0201
        """Adds a subject entry to the page.

            Adds a single-line text control for editing the subject of the selected task(s).
    It also creates an AttributeSync object to manage synchronization between the control
    and the task object(s).

        Returns:
            None
        """
        current_subject = (
            self.items[0].subject()
            if len(self.items) == 1
            else _("Edit to change all subjects")
        )
        self._subjectEntry = widgets.SingleLineTextCtrl(self, current_subject)
        self._subjectSync = attributesync.AttributeSync(
            "subject",
            self._subjectEntry,
            current_subject,
            self.items,
            command.EditSubjectCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].subjectChangedEventType(),
        )
        # TODO: Ajoutez un commentaire pour expliquer le but de ce code:
        self.addEntry(
            _("Subject"),
            self._subjectEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )
        # Add a comment to explain the purpose of this code

    def __modification_text(self):
        # def __modification_text(self) -> str:
        """Calculates the modification text for the page.

        Cette méthode privée calcule le texte à afficher pour la date de modification, en tenant compte des dates minimale et maximale.
        """
        modification_datetimes = [item.modificationDateTime() for item in self.items]
        # TODO: A ESSAYER :
        # modification_datetimes: List[datetime.datetime] = [
        #     item.modificationDateTime() for item in self.items
        # ]
        # essai:
        try:
            return render.dateTime_range(min(modification_datetimes), max(modification_datetimes))
        except ReferenceError as e:
            logging.error(f"tclib.gui.dialog.editor: {str(e)}")
            # vieux code:
            min_modification_datetime = min(modification_datetimes)
            max_modification_datetime = max(modification_datetimes)
            modification_text = render.dateTime(
                min_modification_datetime, humanReadable=True
            )
            if max_modification_datetime - min_modification_datetime > date.ONE_MINUTE:
                modification_text += " - %s" % render.dateTime(
                    max_modification_datetime, humanReadable=True
                )
            return modification_text



    def addDescriptionEntry(self):
        # pylint: disable=W0201
        """
    Adds a multi-line text control for editing the description of the selected task(s).
    It also creates an AttributeSync object to manage synchronization between the control
    and the task object(s). Optionally sets a custom font based on application settings.
    """
        def combined_description(items):
            return "[%s]\n\n" % _("Edit to change all descriptions") + "\n\n".join(
                item.description() for item in items
            )

        current_description = (
            self.items[0].description()
            if len(self.items) == 1
            else combined_description(self.items)
        )
        self._descriptionEntry = widgets.MultiLineTextCtrl(self, current_description)
        native_info_string = self._settings.get("editor", "descriptionfont")
        # font = wx.FontFromNativeInfoString(native_info_string) if native_info_string else None
        # https://pythonhosted.org/wxPython/wx.Font.html#wx.Font
        font = wx.Font(native_info_string) if native_info_string else None

        if font:
            self._descriptionEntry.SetFont(font)
        self._descriptionSync = attributesync.AttributeSync(
            "description",
            self._descriptionEntry,
            current_description,
            self.items,
            command.EditDescriptionCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].descriptionChangedEventType(),
        )
        self.addEntry(
            _("Description"),
            self._descriptionEntry,
            growable=True,
            flags=[wx.ALIGN_TOP | wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def addDateTimeEntries(self, label, attribute_name):
        # TODO: remplacer les 2 fonctions suivantes pas celle-ci, régler le problème de dateTime_range
        date_times = [getattr(item, attribute_name)() for item in self.items]
        min_date, max_date = min(date_times), max(date_times)
        date_text = render.dateTime_range(min_date, max_date)

    def addCreationDateTimeEntry(self):
        """Cette méthode ajoute des étiquettes affichant les dates de création des tâches sélectionnées.
Elles calculent les dates minimale et maximale pour les tâches multiples et affichent un intervalle si nécessaire.
Elles s'abonnent à des événements pour mettre à jour l'affichage de la date de modification lorsque celle-ci change."""
        creation_datetimes = [item.creationDateTime() for item in self.items]
        min_creation_datetime = min(creation_datetimes)
        max_creation_datetime = max(creation_datetimes)
        creation_text = render.dateTime(min_creation_datetime, humanReadable=True)
        if max_creation_datetime - min_creation_datetime > date.ONE_MINUTE:
            creation_text += " - %s" % render.dateTime(
                max_creation_datetime, humanReadable=True
            )
        self.addEntry(
            _("Creation date"),
            creation_text,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def addModificationDateTimeEntry(self):
        """Cette méthode ajoute des étiquettes affichant les dates de modification des tâches sélectionnées.
Elles calculent les dates minimale et maximale pour les tâches multiples et affichent un intervalle si nécessaire.
Elles s'abonnent à des événements pour mettre à jour l'affichage de la date de modification lorsque celle-ci change."""
        self._modificationTextEntry = wx.StaticText(
            self, label=self.__modification_text()
        )
        self.addEntry(
            _("Modification date"),
            self._modificationTextEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )
        for eventType in self.items[0].modificationEventTypes():
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                patterns.Publisher().registerObserver(
                    self.onAttributeChanged_Deprecated,
                    eventType=eventType,
                    eventSource=self.items[0],
                )

    def onAttributeChanged(self, newValue, sender):
        """Ces méthodes sont des callbacks appelés lorsque la date de modification d'une tâche change. Elles mettent à jour le texte de l'étiquette correspondante."""
        self._modificationTextEntry.SetLabel(self.__modification_text())

    def onAttributeChanged_Deprecated(self, *args, **kwargs):
        """Ces méthodes sont des callbacks appelés lorsque la date de modification d'une tâche change. Elles mettent à jour le texte de l'étiquette correspondante."""
        self._modificationTextEntry.SetLabel(self.__modification_text())

    def close(self):
        """Cette méthode est appelée lors de la fermeture de la page. Elle se désabonne des événements pour éviter les fuites de mémoire."""
        super().close()
        for eventType in self.items[0].modificationEventTypes():
            try:
                pub.unsubscribe(self.onAttributeChanged, eventType)
            except pub.TopicNameError:
                pass
        patterns.Publisher().removeObserver(self.onAttributeChanged_Deprecated)

    def entries(self):
        """Cette méthode retourne un dictionnaire contenant des références vers les contrôles de la page, utilisé probablement pour la navigation ou d'autres fonctionnalités."""
        return dict(
            firstEntry=self._subjectEntry,
            subject=self._subjectEntry,
            description=self._descriptionEntry,
            creationDateTime=self._subjectEntry,
            modificationDateTime=self._subjectEntry,
        )


class TaskSubjectPage(SubjectPage):
    """
    Page d'édition pour le sujet et la priorité d'une tâche.

    Cette classe hérite de SubjectPage et ajoute la gestion de la priorité.
    Cette page permet de modifier le titre et la priorité d'une tâche dans Task Coach.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition du sujet et de la priorité.
    """
    # J'ai ajouté __init__
    # def __init__(self, items, parent, settings, *args, **kwargs):
    #     super().__init__(items, parent, settings, args, kwargs)
    #     self._prioritySync = None
    #     self._priorityEntry = None

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour le sujet et la priorité de la tâche.

        Ajoute les entrées de l'interface, en insérant le champ de priorité.
        """
        # Ajoute les widgets pour éditer le sujet et la priorité de la tâche.
        # Override to insert a priority entry between the description and the
        # creation Date/time entry
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addPriorityEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addPriorityEntry(self):
        # pylint: disable=W0201
        """Ajoute un champ pour modifier la priorité de la tâche.

        This method adds a spin control (widgets.SpinCtrl) to the page for editing the priority of the selected task(s).
        It retrieves the current priority of the first task (if only one is selected) or sets it to 0 (default).
        It creates an AttributeSync object to synchronize the spin control value with the "priority" attribute of the task object(s).
        It adds an entry label for "Priority" and the spin control to the page using self.addEntry.
        """
        current_priority = self.items[0].priority() if len(self.items) == 1 else 0
        # Nous introduisons une constante nommée MAX_PRIORITY pour améliorer la lisibilité
        # et faciliter la modification de la valeur de priorité maximale à l'avenir.
        MAX_PRIORITY = 10
        self._priorityEntry = widgets.SpinCtrl(
            self, size=(100, -1), value=current_priority, min=0, max=MAX_PRIORITY
        )
        self._prioritySync = attributesync.AttributeSync(
            "priority",
            self._priorityEntry,
            current_priority,
            self.items,
            command.EditPriorityCommand,
            wx.EVT_SPINCTRL,
            self.items[0].priorityChangedEventType(),
        )
        # self.addEntry(_("Priority"), self._priorityEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Priority"),
            self._priorityEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def entries(self):
        """Retourne un dictionnaire contenant les références aux contrôles.

        This method overrides the entries method from the parent class.
        It calls the parent's entries method to get a dictionary containing references to existing controls.
        It adds a new key-value pair to the dictionary, where the key is "priority" and the value is the reference to the spin control (self._priorityEntry).
        It returns the updated dictionary containing references to all controls on the page.
        """
        entries = super().entries()
        entries["priority"] = self._priorityEntry
        return entries


class CategorySubjectPage(SubjectPage):
    """
    Page d'édition pour le sujet des catégories.

    Cette classe hérite de SubjectPage et ajoute la gestion des sous-catégories exclusives.
    Cette page permet de modifier le titre d'une catégorie dans Task Coach.
    """
    # Utilise la logique d'édition du sujet de base.
    # J'ai ajouté __init__
    # def __init__(self, items, parent, settings, *args, **kwargs):
    #     super().__init__(items, parent, settings, args, kwargs)
    #     self._exclusiveSubcategoriesSync = None
    #     self._exclusiveSubcategoriesCheckBox = None

    def addEntries(self):
        """
    Ajoute les entrées de l'interface, en insérant le champ de sous-catégories exclusives.
    """
        # Override to insert an exclusive subcategories entry
        # between the description and the creation Date/time entry
        self.addSubjectEntry()  # Sujet
        self.addDescriptionEntry()  # Description
        self.addExclusiveSubcategoriesEntry()  # Sous-catégories exclusives (ajouté ici)
        self.addCreationDateTimeEntry()  # Date de création
        self.addModificationDateTimeEntry()  # Date de modification

    def addExclusiveSubcategoriesEntry(self):
        # pylint: disable=W0201
        """
    Ajoute un champ pour définir si les sous-catégories doivent être exclusives.
    """
        currentExclusivity = (
            self.items[0].hasExclusiveSubcategories() if len(self.items) == 1 else False
        )
        self._exclusiveSubcategoriesCheckBox = wx.CheckBox(
            self, label=_("Mutually exclusive")
        )
        self._exclusiveSubcategoriesCheckBox.SetValue(currentExclusivity)
        self._exclusiveSubcategoriesSync = attributesync.AttributeSync(
            "hasExclusiveSubcategories",
            self._exclusiveSubcategoriesCheckBox,
            currentExclusivity,
            self.items,
            command.EditExclusiveSubcategoriesCommand,
            wx.EVT_CHECKBOX,
            self.items[0].exclusiveSubcategoriesChangedEventType(),
        )
        self.addEntry(
            _("Subcategories"),
            self._exclusiveSubcategoriesCheckBox,
            flags=[None, wx.ALL],
        )


class AttachmentSubjectPage(SubjectPage):
    # j'ai ajouté __init__
    # def __init__(self, items, parent, settings, *args, **kwargs):
    #     super().__init__(items, parent, settings, args, kwargs)
    #     self._locationSync = None
    #     self._locationEntry = None

    def addEntries(self):
        # Override to insert a location entry between the subject and
        # description entry
        self.addSubjectEntry()
        self.addLocationEntry()
        self.addDescriptionEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addLocationEntry(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        # pylint: disable=W0201
        current_location = (
            self.items[0].location()
            if len(self.items) == 1
            else _("Edit to change location of all attachments")
        )
        self._locationEntry = widgets.SingleLineTextCtrl(panel, current_location)
        self._locationSync = attributesync.AttributeSync(
            "location",
            self._locationEntry,
            current_location,
            self.items,
            command.EditAttachmentLocationCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].locationChangedEventType(),
        )
        sizer.Add(self._locationEntry, 1, wx.ALL, 3)
        if all(item.type_ == "file" for item in self.items):
            button = wx.Button(panel, wx.ID_ANY, _("Browse"))
            sizer.Add(button, 0, wx.ALL, 3)
            # wx.EVT_BUTTON(button, wx.ID_ANY, self.onSelectLocation)
            button.Bind(wx.EVT_BUTTON, self.onSelectLocation)
        panel.SetSizer(sizer)
        self.addEntry(_("Location"), panel, flags=[None, wx.ALL | wx.EXPAND])

    def onSelectLocation(self, event):  # pylint: disable=W0613
        base_path = self._settings.get("file", "lastattachmentpath")
        if not base_path:
            base_path = os.getcwd()
        filename = widgets.AttachmentSelector(default_path=base_path)

        if filename:
            self._settings.set(
                "file",
                "lastattachmentpath",
                os.path.abspath(os.path.split(filename)[0]),
            )
            if self._settings.get("file", "attachmentbase"):
                filename = attachment.getRelativePath(
                    filename, self._settings.get("file", "attachmentbase")
                )
            self._subjectEntry.SetValue(os.path.split(filename)[-1])
            self._locationEntry.SetValue(filename)
            self._subjectSync.onAttributeEdited(event)
            self._locationSync.onAttributeEdited(event)


class TaskAppearancePage(Page):
    """
    Page d'édition de l'apparence des tâches.

    Cette page permet de modifier des éléments visuels liés aux tâches, comme la couleur,
    la mise en forme, ou d'autres attributs visuels.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition de l'apparence.
    """
    pageName = "appearance"
    pageTitle = _("Appearance")
    pageIcon = "palette_icon"
    columns = 5

    # j'ai ajouté __init__
    # def __init__(self, items, *args, **kwargs):
    #     super().__init__(items, args, kwargs)
    #     self._foregroundColorEntry = None
    #     self._fontEntry = None
    #     self._fontSync = None
    #     self._fontColorSync = None
    #     self._iconEntry = None
    #     self._iconSync = None

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour modifier l'apparence de la tâche (couleur, style, etc.).
        """
        self.addColorEntries()
        self.addFontEntry()
        self.addIconEntry()

    def addColorEntries(self):
        self.addColorEntry(_("Foreground color"), "foreground", wx.BLACK)
        self.addColorEntry(_("Background color"), "background", wx.WHITE)

    def addColorEntry(self, labelText, colorType, defaultColor):
        currentColor = (
            getattr(self.items[0], "%sColor" % colorType)(recursive=False)
            if len(self.items) == 1
            else None
        )
        colorEntry = entry.ColorEntry(self, currentColor, defaultColor)
        setattr(self, "_%sColorEntry" % colorType, colorEntry)
        commandClass = getattr(command, "Edit%sColorCommand" % colorType.capitalize())
        colorSync = attributesync.AttributeSync(
            "%sColor" % colorType,
            colorEntry,
            currentColor,
            self.items,
            commandClass,
            entry.EVT_COLORENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        setattr(self, "_%sColorSync" % colorType, colorSync)
        # self.addEntry(labelText, colorEntry, flags=[None, wx.ALL])
        self.addEntry(labelText, colorEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])

    def addFontEntry(self):
        # pylint: disable=W0201,E1101
        currentFont = self.items[0].font() if len(self.items) == 1 else None
        currentColor = self._foregroundColorEntry.GetValue()  # d'où ça vient ?
        self._fontEntry = entry.FontEntry(self, currentFont, currentColor)
        self._fontSync = attributesync.AttributeSync(
            "font",
            self._fontEntry,
            currentFont,
            self.items,
            command.EditFontCommand,
            entry.EVT_FONTENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        self._fontColorSync = attributesync.FontColorSync(
            "foregroundColor",
            self._fontEntry,
            currentColor,
            self.items,
            command.EditForegroundColorCommand,
            entry.EVT_FONTENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        # self.addEntry(_("Font"), self._fontEntry, flags=[None, wx.ALL])
        self.addEntry(_("Font"), self._fontEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])

    def addIconEntry(self):
        # pylint: disable=W0201,E1101
        currentIcon = self.items[0].icon() if len(self.items) == 1 else ""
        self._iconEntry = entry.IconEntry(self, currentIcon)
        self._iconSync = attributesync.AttributeSync(
            "icon",
            self._iconEntry,
            currentIcon,
            self.items,
            command.EditIconCommand,
            entry.EVT_ICONENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        # self.addEntry(_("Icon"), self._iconEntry, flags=[None, wx.ALL])
        self.addEntry(_("Icon"), self._iconEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])

    def entries(self):
        return dict(firstEntry=self._foregroundColorEntry)  # pylint: disable=E1101


class DatesPage(Page):
    """
    Page d'édition des dates d'une tâche.

    Cette page permet de définir les dates importantes pour une tâche, comme la date de début,
    la date d'échéance, ou d'autres dates spécifiques.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition des dates.
    """
    pageName = "dates"
    pageTitle = _("Dates")
    pageIcon = "calendar_icon"

    def __init__(self, theTask, parent, settings, items_are_new, *args, **kwargs):
        self._actualStartDateTimeEntry = None
        self._completionDateTimeEntry = None
        self._dueDateTimeEntry = None
        self._plannedStartDateTimeEntry = None
        self._recurrenceEntry = None
        self._recurrenceSync = None
        self._reminderDateTimeEntry = None
        self._reminderDateTimeSync = None
        self.__settings = settings
        self._duration = None
        self.__items_are_new = items_are_new
        super().__init__(theTask, parent, *args, **kwargs)
        pub.subscribe(self.__onChoicesConfigChanged, "settings.feature.sdtcspans")

    def __onChoicesConfigChanged(self, value=""):
        self._dueDateTimeEntry.LoadChoices(value)

    def __onTimeChoicesChange(self, event):
        self.__settings.settext("feature", "sdtcspans", event.GetValue())

    def __onPlannedStartDateTimeChanged(self, value):
        self._dueDateTimeEntry.SetRelativeChoicesStart(
            None if value == date.DateTime() else value
        )

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour éditer les dates associées à la tâche.
        """
        self.addDateEntries()
        self.addLine()
        self.addReminderEntry()
        self.addLine()
        self.addRecurrenceEntry()

    def addDateEntries(self):
        self.addDateEntry(_("Planned start date"), "plannedStartDateTime")
        self.addDateEntry(_("Due date"), "dueDateTime")
        self.addLine()
        self.addDateEntry(_("Actual start date"), "actualStartDateTime")
        self.addDateEntry(_("Completion date"), "completionDateTime")

        start = self._plannedStartDateTimeEntry.GetValue()
        self._dueDateTimeEntry.SetRelativeChoicesStart(
            start=None if start == date.DateTime() else start
        )
        self._dueDateTimeEntry.LoadChoices(self.__settings.get("feature", "sdtcspans"))
        # sdtc.EVT_TIME_CHOICES_CHANGE(self._dueDateTimeEntry, self.__onTimeChoicesChange)
        self._dueDateTimeEntry.Bind(
            sdtc.EVT_TIME_CHOICES_CHANGE, self.__onTimeChoicesChange
        )

    def addDateEntry(self, label, taskMethodName):
        # def add_date_entry(self, label: str, task_method_name: str) -> None:
        """Adds a date entry to the page.

        Args:
            label: The label for the date entry.
            taskMethodName: The name of the method used to get the date from the task.
    """
        TaskMethodName = taskMethodName[0].capitalize() + taskMethodName[1:]
        dateTime = (
            getattr(self.items[0], taskMethodName)()
            if len(self.items) == 1
            else date.DateTime()
        )
        setattr(self, "_current%s" % TaskMethodName, dateTime)
        suggestedDateTimeMethodName = "suggested" + TaskMethodName
        suggestedDateTime = getattr(self.items[0], suggestedDateTimeMethodName)()
        dateTimeEntry = entry.DateTimeEntry(
            self,
            self.__settings,
            dateTime,
            suggestedDateTime=suggestedDateTime,
            showRelative=taskMethodName == "dueDateTime",
            adjustEndOfDay=taskMethodName == "dueDateTime",
        )
        setattr(self, "_%sEntry" % taskMethodName, dateTimeEntry)
        commandClass = getattr(command, "Edit%sCommand" % TaskMethodName)
        eventType = getattr(self.items[0], "%sChangedEventType" % taskMethodName)()
        keep_delta = self.__keep_delta(taskMethodName)
        datetimeSync = attributesync.AttributeSync(
            taskMethodName,
            dateTimeEntry,
            dateTime,
            self.items,
            commandClass,
            entry.EVT_DATETIMEENTRY,
            eventType,
            keep_delta=keep_delta,
            callback=(
                self.__onPlannedStartDateTimeChanged
                if taskMethodName == "plannedStartDateTime"
                else None
            ),
        )
        setattr(self, "_%sSync" % taskMethodName, datetimeSync)
        self.addEntry(label, dateTimeEntry, flags=[wx.ALIGN_RIGHT, wx.EXPAND])

    def __keep_delta(self, taskMethodName):
        datesTied = self.__settings.get("view", "datestied")
        return (
            datesTied == "startdue" and taskMethodName == "plannedStartDateTime"
        ) or (datesTied == "duestart" and taskMethodName == "dueDateTime")

    def addReminderEntry(self):
        # pylint: disable=W0201
        reminderDateTime = (
            self.items[0].reminder() if len(self.items) == 1 else date.DateTime()
        )
        suggestedDateTime = self.items[0].suggestedReminderDateTime()
        self._reminderDateTimeEntry = entry.DateTimeEntry(
            self, self.__settings, reminderDateTime, suggestedDateTime=suggestedDateTime
        )
        self._reminderDateTimeSync = attributesync.AttributeSync(
            "reminder",
            self._reminderDateTimeEntry,
            reminderDateTime,
            self.items,
            command.EditReminderDateTimeCommand,
            entry.EVT_DATETIMEENTRY,
            self.items[0].reminderChangedEventType(),
        )
        self.addEntry(
            _("Reminder"),
            self._reminderDateTimeEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def addRecurrenceEntry(self):
        # pylint: disable=W0201
        currentRecurrence = (
            self.items[0].recurrence() if len(self.items) == 1 else date.Recurrence()
        )
        self._recurrenceEntry = entry.RecurrenceEntry(
            self, currentRecurrence, self.__settings
        )
        self._recurrenceSync = attributesync.AttributeSync(
            "recurrence",
            self._recurrenceEntry,
            currentRecurrence,
            self.items,
            command.EditRecurrenceCommand,
            entry.EVT_RECURRENCEENTRY,
            self.items[0].recurrenceChangedEventType(),
        )
        self.addEntry(
            _("Recurrence"), self._recurrenceEntry, flags=[wx.ALIGN_RIGHT, wx.EXPAND]
        )

    def entries(self):
        # pylint: disable=E1101
        return dict(
            firstEntry=self._plannedStartDateTimeEntry,
            plannedStartDateTime=self._plannedStartDateTimeEntry,
            dueDateTime=self._dueDateTimeEntry,
            actualStartDateTime=self._actualStartDateTimeEntry,
            completionDateTime=self._completionDateTimeEntry,
            timeLeft=self._dueDateTimeEntry,
            reminder=self._reminderDateTimeEntry,
            recurrence=self._recurrenceEntry,
        )


class ProgressPage(Page):
    """
    Page d'édition de la progression d'une tâche.

    Cette page permet à l'utilisateur de suivre et modifier l'avancement d'une tâche.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition de la progression.
    """
    pageName = "progress"
    pageTitle = _("Progress")
    pageIcon = "progress"

    # j'ai ajouté __init_
    # def __init__(self, items, *args, **kwargs):
    #     super().__init__(items, args, kwargs)
    #     self._percentageCompleteEntry = None
    #     self._percentageCompleteSync = None
    #     self._shouldMarkCompletedEntry = None
    #     self._shouldMarkCompletedSync = None

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour éditer les informations de progression.
        """
        self.addProgressEntry()
        self.addBehaviorEntry()

    def addProgressEntry(self):
        # pylint: disable=W0201
        currentPercentageComplete = (
            self.items[0].percentageComplete()
            if len(self.items) == 1
            else self.averagePercentageComplete(self.items)
        )
        self._percentageCompleteEntry = entry.PercentageEntry(
            self, currentPercentageComplete
        )
        self._percentageCompleteSync = attributesync.AttributeSync(
            "percentageComplete",
            self._percentageCompleteEntry,
            currentPercentageComplete,
            self.items,
            command.EditPercentageCompleteCommand,
            entry.EVT_PERCENTAGEENTRY,
            self.items[0].percentageCompleteChangedEventType(),
        )
        self.addEntry(
            _("Percentage complete"),
            self._percentageCompleteEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    @staticmethod
    def averagePercentageComplete(items):
        return (
            sum([item.percentageComplete() for item in items])
            // float(len(items))  # with // ?
            if items
            else 0
        )

    def addBehaviorEntry(self):
        # pylint: disable=W0201
        choices = [
            (None, _("Use application-wide setting")),
            (False, _("No")),
            (True, _("Yes")),
        ]
        currentChoice = (
            self.items[0].shouldMarkCompletedWhenAllChildrenCompleted()
            if len(self.items) == 1
            else None
        )
        self._shouldMarkCompletedEntry = entry.ChoiceEntry(self, choices, currentChoice)
        self._shouldMarkCompletedSync = attributesync.AttributeSync(
            "shouldMarkCompletedWhenAllChildrenCompleted",
            self._shouldMarkCompletedEntry,
            currentChoice,
            self.items,
            command.EditShouldMarkCompletedCommand,
            entry.EVT_CHOICEENTRY,
            task.Task.shouldMarkCompletedWhenAllChildrenCompletedChangedEventType(),
        )
        self.addEntry(
            _("Mark task completed when all children are completed?"),
            self._shouldMarkCompletedEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def entries(self):
        return dict(
            firstEntry=self._percentageCompleteEntry,
            percentageComplete=self._percentageCompleteEntry,
        )


class BudgetPage(Page):
    """
    Page d'édition du budget d'une tâche.

    Cette page permet de gérer le budget alloué à une tâche, y compris les coûts prévus
    et les dépenses réelles.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition du budget.
    """
    pageName = "budget"
    pageTitle = _("Budget")
    pageIcon = "calculator_icon"

    # j'ai ajouté __init__
    # def __init__(self, items, *args, **kwargs):
    #     super().__init__(items, args, kwargs)
    #     self._budgetEntry = None
    #     self._budgetLeftEntry = None
    #     self._budgetSync = None
    #     self._fixedFeeEntry = None
    #     self._fixedFeeSync = None
    #     self._hourlyFeeEntry = None
    #     self._hourlyFeeSync = None
    #     self._revenueEntry = None
    #     self._timeSpentEntry = None

    def NavigateBook(self, forward):
        self.GetParent().NavigateBook(forward)

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour éditer le budget de la tâche.
        """
        self.addBudgetEntries()
        self.addLine()
        self.addRevenueEntries()
        self.observeTracking()

    def addBudgetEntries(self):
        self.addBudgetEntry()
        if len(self.items) == 1:
            self.addTimeSpentEntry()
            self.addBudgetLeftEntry()

    def addBudgetEntry(self):
        # pylint: disable=W0201,W0212
        currentBudget = (
            self.items[0].budget() if len(self.items) == 1 else date.TimeDelta()
        )
        self._budgetEntry = entry.TimeDeltaEntry(self, currentBudget)
        self._budgetSync = attributesync.AttributeSync(
            "budget",
            self._budgetEntry,
            currentBudget,
            self.items,
            command.EditBudgetCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].budgetChangedEventType(),
        )
        # self.addEntry(_("Budget"), self._budgetEntry, flags=[None, wx.ALL])
        self.addEntry(_("Budget"), self._budgetEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])

    def addTimeSpentEntry(self):
        assert len(self.items) == 1
        # pylint: disable=W0201
        self._timeSpentEntry = entry.TimeDeltaEntry(
            self, self.items[0].timeSpent(), readonly=True
        )
        # self.addEntry(_("Time spent"), self._timeSpentEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Time spent"), self._timeSpentEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )
        pub.subscribe(
            self.onTimeSpentChanged, self.items[0].timeSpentChangedEventType()
        )

    def onTimeSpentChanged(self, newValue, sender):
        if sender == self.items[0]:
            time_spent = sender.timeSpent()
            if time_spent != self._timeSpentEntry.GetValue():
                self._timeSpentEntry.SetValue(time_spent)

    def addBudgetLeftEntry(self):
        assert len(self.items) == 1
        # pylint: disable=W0201
        self._budgetLeftEntry = entry.TimeDeltaEntry(
            self, self.items[0].budgetLeft(), readonly=True
        )
        # self.addEntry(_("Budget left"), self._budgetLeftEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Budget left"), self._budgetLeftEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )
        pub.subscribe(
            self.onBudgetLeftChanged, self.items[0].budgetLeftChangedEventType()
        )

    def onBudgetLeftChanged(self, newValue, sender):  # pylint: disable=W0613
        if sender == self.items[0]:
            budget_left = sender.budgetLeft()
            if budget_left != self._budgetLeftEntry.GetValue():
                self._budgetLeftEntry.SetValue(budget_left)

    def addRevenueEntries(self):
        self.addHourlyFeeEntry()
        self.addFixedFeeEntry()
        if len(self.items) == 1:
            self.addRevenueEntry()

    def addHourlyFeeEntry(self):
        # pylint: disable=W0201,W0212
        currentHourlyFee = self.items[0].hourlyFee() if len(self.items) == 1 else 0
        self._hourlyFeeEntry = entry.AmountEntry(self, currentHourlyFee)
        self._hourlyFeeSync = attributesync.AttributeSync(
            "hourlyFee",
            self._hourlyFeeEntry,
            currentHourlyFee,
            self.items,
            command.EditHourlyFeeCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].hourlyFeeChangedEventType(),
        )
        # self.addEntry(_("Hourly fee"), self._hourlyFeeEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Hourly fee"), self._hourlyFeeEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )

    def addFixedFeeEntry(self):
        # pylint: disable=W0201,W0212
        currentFixedFee = self.items[0].fixedFee() if len(self.items) == 1 else 0
        self._fixedFeeEntry = entry.AmountEntry(self, currentFixedFee)
        self._fixedFeeSync = attributesync.AttributeSync(
            "fixedFee",
            self._fixedFeeEntry,
            currentFixedFee,
            self.items,
            command.EditFixedFeeCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].fixedFeeChangedEventType(),
        )
        # self.addEntry(_("Fixed fee"), self._fixedFeeEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Fixed fee"), self._fixedFeeEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )

    def addRevenueEntry(self):
        assert len(self.items) == 1
        revenue = self.items[0].revenue()
        self._revenueEntry = entry.AmountEntry(
            self, revenue, readonly=True
        )  # pylint: disable=W0201
        # Instance attribute _revenueEntry defined outside __init__
        # self.addEntry(_("Revenue"), self._revenueEntry, flags=[None, wx.ALL])
        self.addEntry(_("Revenue"), self._revenueEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])
        pub.subscribe(self.onRevenueChanged, self.items[0].revenueChangedEventType())

    def onRevenueChanged(self, newValue, sender):
        if sender == self.items[0]:
            if newValue != self._revenueEntry.GetValue():
                self._revenueEntry.SetValue(newValue)

    def observeTracking(self):
        if len(self.items) != 1:
            return
        item = self.items[0]
        pub.subscribe(self.onTrackingChanged, item.trackingChangedEventType())
        if item.isBeingTracked():
            self.onTrackingChanged(True, item)

    def onTrackingChanged(self, newValue, sender):
        if newValue:
            if sender in self.items:
                date.Scheduler().schedule_interval(self.onEverySecond, seconds=1)
        else:
            # We might need to keep tracking the clock if the user was tracking this
            # task with multiple effort records simultaneously
            if not self.items[0].isBeingTracked():
                date.Scheduler().unschedule(self.onEverySecond)

    def onEverySecond(self):
        taskDisplayed = self.items[0]
        self.onTimeSpentChanged(taskDisplayed.timeSpent(), taskDisplayed)
        self.onBudgetLeftChanged(taskDisplayed.budgetLeft(), taskDisplayed)
        self.onRevenueChanged(taskDisplayed.revenue(), taskDisplayed)

    def close(self):
        date.Scheduler().unschedule(self.onEverySecond)
        super().close()

    def entries(self):
        return dict(
            firstEntry=self._budgetEntry,
            budget=self._budgetEntry,
            budgetLeft=self._budgetEntry,
            hourlyFee=self._hourlyFeeEntry,
            fixedFee=self._fixedFeeEntry,
            revenue=self._hourlyFeeEntry,
        )


class PageWithViewer(Page):
    columns = 1

    def __init__(
        self, items, parent, taskFile, settings, settingsSection, *args, **kwargs
    ):
        self.__taskFile = taskFile
        self.__settings = settings
        self.__settingsSection = settingsSection
        # self.viewer = None
        super().__init__(items, parent, *args, **kwargs)

    def addEntries(self):
        # pylint: disable=W0201
        self.viewer = self.createViewer(
            self.__taskFile, self.__settings, self.__settingsSection
        )
        # self.addEntry(self.viewer, growable=True)
        self.addEntry(self.viewer, growable=True, flags=[wx.EXPAND])

    def createViewer(self, taskFile, settings, settingsSection):
        raise NotImplementedError

    def close(self):
        # I guess this happens because of CallAfter in context of #1437...
        if hasattr(self, "viewer"):
            self.viewer.detach()
            # Don't Notify the viewer about any changes anymore, it's about
            # to be deleted, but don't delete it too soon.
            wx.CallAfter(self.deleteViewer)
        super().close()

    def deleteViewer(self):
        if hasattr(self, "viewer"):
            del self.viewer


class EffortPage(PageWithViewer):
    """
    Page d'édition de l'effort d'une tâche.

    Permet de gérer l'effort alloué à une tâche, souvent utilisé pour le suivi du temps.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition de l'effort.
    """
    pageName = "effort"
    pageTitle = _("Effort")
    pageIcon = "clock_icon"

    def createViewer(self, taskFile, settings, settingsSection):
        # TODO: remplacer viewer.EffortViewer par EffortViewer
        return viewer.EffortViewer(
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            tasksToShowEffortFor=task.TaskList(self.items),
        )

    def entries(self):
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, timeSpent=self.viewer)
        return dict()

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour l'édition de l'effort consacré à une tâche.
        """
        pass


class LocalCategoryViewer(viewer.BaseCategoryViewer):  # pylint: disable=W0223
    # AttributeError: partially initialized module 'taskcoachlib.gui.viewer' has no attribute 'BaseCategoryViewer'
    # (most likely due to a circular import)
    def __init__(self, items, *args, **kwargs):
        self.__items = items
        super().__init__(*args, **kwargs)
        for item in self.domainObjectsToView():
            item.expand(context=self.settingsSection(), notify=False)

    def getIsItemChecked(self, category):  # pylint: disable=W0621
        for item in self.__items:
            if category in item.categories():
                return True
        return False

    def onCheck(self, event, final):
        """Here we keep track of the items checked by the user so that these
        items remain checked when refreshing the viewer."""
        if final:
            category = self.widget.GetItemPyData(
                event.GetItem()
            )  # TODO: try GetItemData
            command.ToggleCategoryCommand(None, self.__items, category=category).do()

    # def createCategoryPopupMenu(self, localOnly=True):  # pylint: disable=W0221
    def createCategoryPopupMenu(self):  # pylint: disable=W0221
        # Signature of method 'LocalCategoryViewer.createCategoryPopupMenu()'
        # does not match signature of the base method in class 'BaseCategoryViewer'
        return super().createCategoryPopupMenu(True)


class CategoriesPage(PageWithViewer):
    """
    Page d'édition des catégories d'un objet.

    Permet d'assigner des catégories à un objet comme une tâche ou une note.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition des catégories.
    """
    pageName = "categories"
    pageTitle = _("Categories")
    pageIcon = "folder_blue_arrow_icon"

    def __init__(self, *args, **kwargs):
        self.__realized = False
        super().__init__(*args, **kwargs)

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour gérer les catégories associées à l'objet.
        """
        pass

    def selected(self):
        if not self.__realized:
            self.__realized = True
            super().addEntries()
            self.fit()

    def createViewer(self, taskFile, settings, settingsSection):
        assert len(self.items) == 1
        item = self.items[0]
        for eventType in (
            item.categoryAddedEventType(),
            item.categoryRemovedEventType(),
        ):
            self.registerObserver(
                self.onCategoryChanged, eventType=eventType, eventSource=item
            )
        return LocalCategoryViewer(
            self.items,
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
        )

    def onCategoryChanged(self, event):
        self.viewer.refreshItems(*list(event.values()))

    def entries(self):
        if self.__realized and hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, categories=self.viewer)
        return dict()


class LocalAttachmentViewer(viewer.AttachmentViewer):  # pylint: disable=W0223
    # class LocalAttachmentViewer(AttachmentViewer):  # pylint: disable=W0223
    # AttributeError: partially initialized module 'taskcoachlib.gui.viewer'
    # has no attribute 'AttachmentViewer' (most likely due to a circular import)
    def __init__(self, *args, **kwargs):
        self.attachmentOwner = kwargs.pop("owner")
        attachments = attachment.AttachmentList(self.attachmentOwner.attachments())
        super(LocalAttachmentViewer, self).__init__(
            attachmentsToShow=attachments, *args, **kwargs
        )

    def newItemCommand(self, *args, **kwargs):
        return command.AddAttachmentCommand(
            None, [self.attachmentOwner], *args, **kwargs
        )

    def deleteItemCommand(self):
        return command.RemoveAttachmentCommand(
            None, [self.attachmentOwner], attachments=self.curselection()
        )

    def cutItemCommand(self):
        return command.CutAttachmentCommand(
            None, [self.attachmentOwner], attachments=self.curselection()
        )


class AttachmentsPage(PageWithViewer):
    pageName = "attachments"
    pageTitle = _("Attachments")
    pageIcon = "paperclip_icon"

    def createViewer(self, taskFile, settings, settingsSection):
        assert len(self.items) == 1
        item = self.items[0]
        self.registerObserver(
            self.onAttachmentsChanged,
            eventType=item.attachmentsChangedEventType(),
            eventSource=item,
        )
        return LocalAttachmentViewer(
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            owner=item,
        )

    def onAttachmentsChanged(self, event):  # pylint: disable=W0613
        self.viewer.domainObjectsToView().clear()
        self.viewer.domainObjectsToView().extend(self.items[0].attachments())

    def entries(self):
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, attachments=self.viewer)
        return dict()


class LocalNoteViewer(viewer.BaseNoteViewer):  # pylint: disable=W0223
    # class LocalNoteViewer(BaseNoteViewer):  # pylint: disable=W0223
    def __init__(self, *args, **kwargs):
        self.__note_owner = kwargs.pop("owner")
        notes = note.NoteContainer(self.__note_owner.notes())
        super().__init__(notesToShow=notes, *args, **kwargs)

    def newItemCommand(self, *args, **kwargs):
        return command.AddNoteCommand(None, [self.__note_owner])

    def newSubItemCommand(self):
        return command.AddSubNoteCommand(
            None, self.curselection(), owner=self.__note_owner
        )

    def deleteItemCommand(self):
        return command.RemoveNoteCommand(
            None, [self.__note_owner], notes=self.curselection()
        )


class NotesPage(PageWithViewer):
    """
    Page d'édition des notes d'un objet.

    Permet d'ajouter ou modifier des notes attachées à un objet.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition des notes.
    """
    pageName = "notes"
    pageTitle = _("Notes")
    pageIcon = "note_icon"

    def createViewer(self, taskFile, settings, settingsSection):
        assert len(self.items) == 1
        item = self.items[0]
        self.registerObserver(
            self.onNotesChanged,
            eventType=item.notesChangedEventType(),
            eventSource=item,
        )
        return LocalNoteViewer(
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            owner=item,
        )

    def onNotesChanged(self, event):  # pylint: disable=W0613
        self.viewer.domainObjectsToView().clear()
        self.viewer.domainObjectsToView().extend(self.items[0].notes())

    def entries(self):
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, notes=self.viewer)
        return dict()

    # def addEntries(self):
    #     """
    #     Ajoute les champs d'entrée pour l'édition des notes associées à un objet.
    #     """
    #     pass


class LocalPrerequisiteViewer(viewer.CheckableTaskViewer):  # pylint: disable=W0223
    # class LocalPrerequisiteViewer(CheckableTaskViewer):  # pylint: disable=W0223
    def __init__(self, items, *args, **kwargs):
        self.__items = items
        super().__init__(*args, **kwargs)

    def getIsItemChecked(self, item):
        return item in self.__items[0].prerequisites()

    def getIsItemCheckable(self, item):
        return item not in self.__items

    def onCheck(self, event, final):
        item = self.widget.GetItemPyData(event.GetItem())  # TODO: test with GetItemData
        is_checked = event.GetItem().IsChecked()
        if is_checked != self.getIsItemChecked(item):
            checked, unchecked = ([item], []) if is_checked else ([], [item])
            command.TogglePrerequisiteCommand(
                None,
                self.__items,
                checkedPrerequisites=checked,
                uncheckedPrerequisites=unchecked,
            ).do()


class PrerequisitesPage(PageWithViewer):
    """
    Page d'édition des prérequis d'une tâche.

    Permet de définir des tâches prérequises à accomplir avant celle en cours.

    Méthodes :
        addEntries(self) : Ajoute les champs d'entrée pour l'édition des prérequis.
    """
    pageName = "prerequisites"
    pageTitle = _("Prerequisites")
    pageIcon = "trafficlight_icon"

    def __init__(self, *args, **kwargs):
        self.__realized = False
        super().__init__(*args, **kwargs)

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour définir les prérequis d'une tâche.
        """
        pass

    def selected(self):
        if not self.__realized:
            self.__realized = True
            super().addEntries()
            self.fit()

    def createViewer(self, taskFile, settings, settingsSection):
        assert len(self.items) == 1
        pub.subscribe(
            self.onPrerequisitesChanged, self.items[0].prerequisitesChangedEventType()
        )
        return LocalPrerequisiteViewer(
            self.items,
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
        )

    def onPrerequisitesChanged(self, newValue, sender):
        if sender == self.items[0]:
            self.viewer.refreshItems(*newValue)

    def entries(self):
        if self.__realized and hasattr(self, "viewer"):
            return dict(
                firstEntry=self.viewer,
                prerequisites=self.viewer,
                dependencies=self.viewer,
            )
        return dict()


class EditBook(widgets.Notebook):
    """
    Fenêtre principale de l'éditeur dans Task Coach.

    Cette fenêtre contient les différentes pages d'édition (sujet, apparence, dates, etc.)
    pour modifier les objets de Task Coach.

    Méthodes :
        __init__(self, *args, **kwargs) : Initialise l'éditeur avec les objets à éditer.
        addPages(self) : Ajoute les pages d'édition pour les objets.
        close(self) : Ferme l'éditeur.
    """
    allPageNames = ["subclass responsibility"]
    domainObject = "subclass responsibility"

    def __init__(self, parent, items, taskFile, settings, items_are_new):
        """
        Initialise l'éditeur avec les objets à éditer.
        """
        self.items = items
        self.settings = settings
        super().__init__(parent)
        self.addPages(taskFile, items_are_new)
        self.__load_perspective(items_are_new)

    def NavigateBook(self, forward):
        curSel = self.GetSelection()
        curSel = curSel + 1 if forward else curSel - 1
        if 0 <= curSel < self.GetPageCount():
            self.SetSelection(curSel)

    def addPages(self, task_file, items_are_new):
        """
        Ajoute les différentes pages d'édition à l'éditeur.

        Ajoute les pages d'édition spécifiques à l'éditeur.
        Chaque type d'objet (tâche, note, etc.) aura ses propres pages d'édition (sujet, apparence, etc.).
        """
        page_names = self.settings.getlist(self.settings_section(), "pages")
        for page_name in page_names:
            page = self.createPage(page_name, task_file, items_are_new)
            self.AddPage(page, page.pageTitle, page.pageIcon)
        width, height = self.__get_minimum_page_size()
        self.SetMinSize((width, self.GetHeightForPageHeight(height)))

    def onPageChanged(self, event):
        self.GetPage(
            event.Selection
        ).selected()  # Unresolved attribute reference 'Selection' for class 'Event'->events
        event.Skip()
        if operating_system.isMac():
            # The dialog loses focus sometimes...
            wx.GetTopLevelParent(self).Raise()

    def getPage(self, page_name):
        index = self.getPageIndex(page_name)
        if index is not None:
            return self[index]
        return None

    def getPageIndex(self, page_name):
        for index in range(self.GetPageCount()):
            if page_name == self[index].pageName:
                return index
        return None

    def __get_minimum_page_size(self):
        min_widths, min_heights = [], []
        for page in self:
            min_width, min_height = page.GetMinSize()
            min_widths.append(min_width)
            min_heights.append(min_height)
        return max(min_widths), max(min_heights)

    def __pages_to_create(self):
        return [
            page_name
            for page_name in self.allPageNames
            if self.__should_create_page(page_name)
        ]

    def __should_create_page(self, page_name):
        return (
            self.__page_supports_mass_editing(page_name)
            if len(self.items) > 1
            else True
        )

    @staticmethod
    def __page_supports_mass_editing(page_name):
        """Return whether the_module page supports editing multiple items
        at once."""
        return page_name in ("subject", "dates", "progress", "budget", "appearance")

    def createPage(self, page_name, task_file, items_are_new):
        if page_name == "subject":
            return self.create_subject_page()
        elif page_name == "dates":
            return DatesPage(self.items, self, self.settings, items_are_new)
        elif page_name == "prerequisites":
            return PrerequisitesPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="prerequisiteviewerin%seditor" % self.domainObject,
            )
        elif page_name == "progress":
            return ProgressPage(self.items, self)
        elif page_name == "categories":
            return CategoriesPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="categoryviewerin%seditor" % self.domainObject,
            )
        elif page_name == "budget":
            return BudgetPage(self.items, self)
        elif page_name == "effort":
            return EffortPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="effortviewerin%seditor" % self.domainObject,
            )
        elif page_name == "notes":
            return NotesPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="noteviewerin%seditor" % self.domainObject,
            )
        elif page_name == "attachments":
            return AttachmentsPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="attachmentviewerin%seditor" % self.domainObject,
            )
        elif page_name == "appearance":
            return TaskAppearancePage(self.items, self)

    def create_subject_page(self):
        return SubjectPage(self.items, self, self.settings)

    def setFocus(self, columnName):
        """Select the correct page of the editor and correct control on a page
        based on the column that the user double clicked."""
        page = 0
        for page_index in range(self.GetPageCount()):
            if columnName in self[page_index].entries():
                page = page_index
                break
        self.SetSelection(page)
        self[page].setFocusOnEntry(columnName)

    def isDisplayingItemOrChildOfItem(self, targetItem):
        ancestors = []
        for item in self.items:
            ancestors.extend(item.ancestors())
        return targetItem in self.items + ancestors

    def perspective(self):
        """Return the perspective for the notebook."""
        return self.settings.gettext(self.settings_section(), "perspective")

    def __load_perspective(self, items_are_new=False):
        """Load the perspective (layout) for the current combination of visible
        pages from the settings."""
        perspective = self.perspective()
        if perspective:
            try:
                self.LoadPerspective(perspective)
            except:  # pylint: disable=W0702  finally not except
                pass
        if items_are_new:
            current_page = (
                self.getPageIndex("subject") or 0
            )  # For new items, start at the subject page.
        else:
            # Although the active/current page is written in the perspective
            # string (a + before the number of the active page), the current
            # page is not set when restoring the perspective. This does it by
            # hand:
            try:
                current_page = int(
                    perspective.split("@")[0].split("+")[1].split(",")[0]
                )
            except (IndexError, ValueError):
                current_page = 0
        self.SetSelection(current_page)
        self.GetPage(current_page).SetFocus()

        for idx in range(self.GetPageCount()):
            page = self.GetPage(idx)
            if page.IsShown():
                page.selected()

    def __save_perspective(self):
        """Save the current perspective of the editor in the settings.
        Multiple perspectives are supported, for each set of visible pages.
        This allows different perspectives for e.g. single item editors and
        multi-item editors."""
        page_names = [self[index].pageName for index in range(self.GetPageCount())]
        section = self.settings_section()
        self.settings.settext(section, "perspective", self.SavePerspective())
        self.settings.setlist(section, "pages", page_names)

    def settings_section(self):
        """Create the settings section for this dialog if necessary and
        return it."""
        section = self.__settings_section_name()
        if not self.settings.has_section(section):
            self.__create_settings_section(section)
        return section

    def __settings_section_name(self):
        """Return the section name of this notebook. The name of the section
        depends on the visible pages so that different variants of the
        notebook store their settings in different sections."""
        page_names = self.__pages_to_create()
        sorted_page_names = "_".join(sorted(page_names))
        return "%sdialog_with_%s" % (self.domainObject, sorted_page_names)

    def __create_settings_section(self, section):
        """Create the section and initialize the options in the section."""
        self.settings.add_section(section)
        for option, value in list(
            dict(
                perspective="",
                pages=str(self.__pages_to_create()),
                size="(-1, -1)",
                position="(-1, -1)",
                maximized="False",
            ).items()
        ):
            self.settings.init(section, option, value)

    def close_edit_book(self):
        """Close all pages in the edit book and save the current layout in
        the settings.


        Ferme l'éditeur et libère les ressources.

        Ferme l'éditeur et libère les ressources associées.
        Cette méthode est appelée lors de la fermeture de la fenêtre d'édition.
        """
        for page in self:
            page.Close()
        self.__save_perspective()


class TaskEditBook(EditBook):
    allPageNames = [
        "subject",
        "dates",
        "prerequisites",
        "progress",
        "categories",
        "budget",
        "effort",
        "notes",
        "attachments",
        "appearance",
    ]
    domainObject = "task"

    def create_subject_page(self):
        return TaskSubjectPage(self.items, self, self.settings)


class CategoryEditBook(EditBook):
    allPageNames = ["subject", "notes", "attachments", "appearance"]
    domainObject = "category"

    def create_subject_page(self):
        return CategorySubjectPage(self.items, self, self.settings)


class NoteEditBook(EditBook):
    allPageNames = ["subject", "categories", "attachments", "appearance"]
    domainObject = "note"


class AttachmentEditBook(EditBook):
    allPageNames = ["subject", "notes", "appearance"]
    domainObject = "attachment"

    def create_subject_page(self):
        return AttachmentSubjectPage(self.items, self, self.settings)

    def isDisplayingItemOrChildOfItem(self, targetItem):
        return targetItem in self.items


class EffortEditBook(Page):
    domainObject = "effort"
    columns = 3

    def __init__(
        self, parent, efforts, taskFile, settings, items_are_new, *args, **kwargs
    ):  # pylint: disable=W0613
        self._effortList = taskFile.efforts()
        task_list = taskFile.tasks()
        self._taskList = task.TaskList(task_list)
        self._taskList.extend(
            [effort.task() for effort in efforts if effort.task() not in task_list]
        )
        self._settings = settings
        self._taskFile = taskFile
        super().__init__(efforts, parent, *args, **kwargs)
        pub.subscribe(
            self.__onChoicesConfigChanged, "settings.feature.sdtcspans_effort"
        )

    def __onChoicesConfigChanged(self, value=""):
        self._stopDateTimeEntry.LoadChoices(value)

    # @staticmethod
    def getPage(self, pageName):  # pylint: disable=W0613
        return None  # An EffortEditBook is not really a notebook...

    # @staticmethod
    def settings_section(self):
        """Return the settings section for the effort dialog."""
        # Since the effort dialog has no tabs, the settings section does not
        # depend on the visible tabs.
        # return "effort dialog"
        return "effortdialog"

    # @staticmethod
    def perspective(self):
        """Return the perspective for the effort dialog."""
        # Since the effort dialog has no tabs, the perspective is always the
        # same and the value does not matter.
        return "effort dialog perspective"

    def addEntries(self):
        self.__add_task_entry()
        self.__add_start_and_stop_entries()
        self.addDescriptionEntry()

    def __add_task_entry(self):
        """Add an entry for changing the task that this effort record
        belongs to."""
        # pylint: disable=W0201,W0212
        panel = wx.Panel(self)
        current_task = self.items[0].task()
        self._taskEntry = entry.TaskEntry(
            panel, rootTasks=self._taskList.rootItems(), selectedTask=current_task
        )
        self._taskSync = attributesync.AttributeSync(
            "task",
            self._taskEntry,
            current_task,
            self.items,
            command.EditTaskCommand,
            entry.EVT_TASKENTRY,
            self.items[0].taskChangedEventType(),
        )
        edit_task_button = wx.Button(panel, label=_("Edit task"))
        edit_task_button.Bind(wx.EVT_BUTTON, self.onEditTask)
        panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.Add(
            self._taskEntry,
            proportion=1,
            # flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
            # proposition de starofrainnight:
            flag=wx.EXPAND,
        )

        panel_sizer.Add((3, -1))
        panel_sizer.Add(edit_task_button, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        panel.SetSizerAndFit(panel_sizer)
        self.addEntry(_("Task"), panel, flags=[None, wx.ALL | wx.EXPAND])

    def __onStartDateTimeChanged(self, value):
        self._stopDateTimeEntry.SetRelativeChoicesStart(start=value)

    def __onChoicesChanged(self, event):
        self._settings.settext("feature", "sdtcspans_effort", event.GetValue())

    def __add_start_and_stop_entries(self):
        # pylint: disable=W0201,W0142
        date_time_entry_kw_args = dict(showSeconds=True)
        flags = [
            None,
            wx.ALIGN_RIGHT | wx.ALL,
            wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            None,
        ]

        current_start_date_time = self.items[0].getStart()
        self._startDateTimeEntry = entry.DateTimeEntry(
            self,
            self._settings,
            current_start_date_time,
            noneAllowed=False,
            showRelative=True,
            **date_time_entry_kw_args
        )
        wx.CallAfter(self._startDateTimeEntry.HideRelativeButton)
        self._startDateTimeSync = attributesync.AttributeSync(
            "getStart",
            self._startDateTimeEntry,
            current_start_date_time,
            self.items,
            command.EditEffortStartDateTimeCommand,
            entry.EVT_DATETIMEENTRY,
            self.items[0].startChangedEventType(),
            callback=self.__onStartDateTimeChanged,
        )
        self._startDateTimeEntry.Bind(entry.EVT_DATETIMEENTRY, self.onDateTimeChanged)
        start_from_last_effort_button = self.__create_start_from_last_effort_button()
        self.addEntry(
            _("Start"),
            self._startDateTimeEntry,
            start_from_last_effort_button,
            flags=flags,
        )

        current_stop_date_time = self.items[0].getStop()
        self._stopDateTimeEntry = entry.DateTimeEntry(
            self,
            self._settings,
            current_stop_date_time,
            noneAllowed=True,
            showRelative=True,
            units=[
                (_("Minute(s)"), 60),
                (_("Hour(s)"), 3600),
                (_("Day(s)"), 24 * 3600),
                (_("Week(s)"), 7 * 24 * 3600),
            ],
            **date_time_entry_kw_args
        )
        self._stopDateTimeSync = attributesync.AttributeSync(
            "getStop",
            self._stopDateTimeEntry,
            current_stop_date_time,
            self.items,
            command.EditEffortStopDateTimeCommand,
            entry.EVT_DATETIMEENTRY,
            self.items[0].stopChangedEventType(),
            callback=self.__onStopDateTimeChanged,
        )
        self._stopDateTimeEntry.Bind(
            entry.EVT_DATETIMEENTRY, self.onStopDateTimeChanged
        )
        stop_now_button = self.__create_stop_now_button()
        self._invalidPeriodMessage = self.__create_invalid_period_message()
        self.addEntry(_("Stop"), self._stopDateTimeEntry, stop_now_button, flags=flags)
        self.__onStartDateTimeChanged(current_start_date_time)
        self._stopDateTimeEntry.LoadChoices(
            self._settings.get("feature", "sdtcspans_effort")
        )
        # sdtc.EVT_TIME_CHOICES_CHANGE(self._stopDateTimeEntry, self.__onChoicesChanged)
        # self._stopDateTimeEntry.Bind(wx.adv.EVT_TIME_CHANGED, self.__onChoicesChanged)
        self._stopDateTimeEntry.Bind(sdtc.EVT_TIME_CHOICES_CHANGE, self.__onChoicesChanged)

        self.addEntry("", self._invalidPeriodMessage)

    def __create_start_from_last_effort_button(self):
        button = wx.Button(self, label=_("Start tracking from last stop time"))
        self.Bind(wx.EVT_BUTTON, self.onStartFromLastEffort, button)
        if self._effortList.maxDateTime() is None:
            button.Disable()
        return button

    def __create_stop_now_button(self):
        button = wx.Button(self, label=_("Stop tracking now"))
        self.Bind(wx.EVT_BUTTON, self.onStopNow, button)
        return button

    def __create_invalid_period_message(self):
        text = wx.StaticText(self, label="")
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        text.SetFont(font)
        return text

    def onStartFromLastEffort(self, event):  # pylint: disable=W0613
        maxDateTime = self._effortList.maxDateTime()
        if self._startDateTimeEntry.GetValue() != maxDateTime:
            self._startDateTimeEntry.SetValue(self._effortList.maxDateTime())
            self._startDateTimeSync.onAttributeEdited(event)
        self.onDateTimeChanged(event)

    def onStopNow(self, event):
        command.StopEffortCommand(self._effortList, self.items).do()

    def onStopDateTimeChanged(self, *args, **kwargs):
        self.onDateTimeChanged(*args, **kwargs)

    def __onStopDateTimeChanged(self, new_value):
        # The actual start Date/time was not changed (the command class checks that) if
        # if was greater than the stop Date/time then, so make sure it is if everything is
        # OK Now.
        command.EditEffortStartDateTimeCommand(
            None, self.items, newValue=self._startDateTimeEntry.GetValue()
        ).do()

    def onDateTimeChanged(self, event):
        event.Skip()
        self.__update_invalid_period_message()

    def __update_invalid_period_message(self):
        message = (
            ""
            if self.__is_period_valid()
            else _("Warning: start must be earlier than stop")
        )
        self._invalidPeriodMessage.SetLabel(message)

    def __is_period_valid(self):
        """Return whether the current period is valid, i.e. the start Date
        and time is earlier than the stop Date and time."""
        try:
            return (
                self._startDateTimeEntry.GetValue() < self._stopDateTimeEntry.GetValue()
            )
        except AttributeError:
            return True  # Entries not created yet

    def onEditTask(self, event):  # pylint: disable=W0613
        task_to_edit = self._taskEntry.GetValue()
        TaskEditor(
            None, [task_to_edit], self._settings, self._taskFile.tasks(), self._taskFile
        ).Show()

    def addDescriptionEntry(self):
        # pylint: disable=W0201
        def combined_description(items):
            distinctDescriptions = set(item.description() for item in items)
            if len(distinctDescriptions) == 1 and distinctDescriptions.pop():
                return items[0].description()
            lines = ["[%s]" % _("Edit to change all descriptions")]
            lines.extend(item.description() for item in items if item.description())
            return "\n\n".join(lines)

        current_description = (
            self.items[0].description()
            if len(self.items) == 1
            else combined_description(self.items)
        )
        self._descriptionEntry = widgets.MultiLineTextCtrl(self, current_description)
        native_info_string = self._settings.get("editor", "descriptionfont")
        # font = wx.FontFromNativeInfoString(native_info_string) if native_info_string else None
        font = wx.Font(native_info_string) if native_info_string else None
        if font:
            self._descriptionEntry.SetFont(font)
        self._descriptionEntry.SetSizeHints(300, 150)
        self._descriptionSync = attributesync.AttributeSync(
            "description",
            self._descriptionEntry,
            current_description,
            self.items,
            command.EditDescriptionCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].descriptionChangedEventType(),
        )
        self.addEntry(_("Description"), self._descriptionEntry, growable=True)

    def setFocus(self, column_name):
        self.setFocusOnEntry(column_name)

    def isDisplayingItemOrChildOfItem(self, item):
        if hasattr(item, "setTask"):
            return self.items[0] == item  # Regular effort
        else:
            return item.mayContain(self.items[0])  # Composite effort

    def entries(self):
        return dict(
            firstEntry=self._startDateTimeEntry,
            task=self._taskEntry,
            period=self._stopDateTimeEntry,
            description=self._descriptionEntry,
            timeSpent=self._stopDateTimeEntry,
            revenue=self._taskEntry,
        )

    def close_edit_book(self):
        pass


class Editor(BalloonTipManager, widgets.Dialog):
    # Gestion du 'wx.Timer' pour macOS
    EditBookClass = (
        lambda *args: "Subclass responsibility"
    )  # PEP 8: E731 do not assign a lambda expression, use a def
    singular_title = "Subclass responsibility %s"
    plural_title = "Subclass responsibility"

    def __init__(self, parent, items, settings, container, task_file, *args, **kwargs):
        self._items = items
        self._settings = settings
        self._taskFile = task_file
        self.__items_are_new = kwargs.pop("items_are_new", False)
        column_name = kwargs.pop("columnName", "")
        self.__call_after = kwargs.get("call_after", wx.CallAfter)
        super().__init__(
            parent, self.__title(), buttonTypes=wx.ID_CLOSE, *args, **kwargs
        )
        if not column_name:
            if self._interior.perspective() and hasattr(self._interior, "GetSelection"):
                column_name = self._interior[self._interior.GetSelection()].pageName
            else:
                column_name = "subject"
        if column_name:
            self._interior.setFocus(column_name)

        patterns.Publisher().registerObserver(
            self.on_item_removed,
            eventType=container.removeItemEventType(),
            eventSource=container,
        )
        if len(self._items) == 1:
            patterns.Publisher().registerObserver(
                self.on_subject_changed,
                eventType=self._items[0].subjectChangedEventType(),
                eventSource=self._items[0],
            )
        self.Bind(wx.EVT_CLOSE, self.on_close_editor)

        if operating_system.isMac():
            # Sigh. On OS X, if you open an editor, switch back to the main window, open
            # another editor, then hit Escape twice, the second editor disappears without any
            # notification (EVT_CLOSE, EVT_ACTIVATE), so poll for this, because there might
            # be pending changes...
            id_ = (
                IdProvider.get()
            )  # Parameter 'self' unfilled -> Obtenir un identifiant unique
            self.__timer = wx.Timer(self, id_)
            # wx.EVT_TIMER(self, id_, self.__on_timer)
            self.Bind(wx.EVT_TIMER, id_, self.__on_timer)
            self.__timer.Start(1000, False)
        else:
            self.__timer = None

        # On Mac OS X, the frame opens by default in the top-left
        # corner of the first display. This gets annoying on a
        # 2560x1440 27" + 1920x1200 24" dual screen...

        # On Windows, for some reason, the Python 2.5 and 2.6 versions
        # of wxPython 2.8.11.0 behave differently; on Python 2.5 the
        # frame opens centered on its parent but on 2.6 it opens on
        # the first display!

        # On Linux this is not needed but doesn't do any harm.
        self.CentreOnParent()
        self.__create_ui_commands()
        self.__dimensions_tracker = (
            windowdimensionstracker.WindowSizeAndPositionTracker(
                self, settings, self._interior.settings_section()
            )
        )

    def __on_timer(self, event):
        if not self.IsShown():
            self.Close()

    def __create_ui_commands(self):
        # FIXME: keyboard shortcuts are hardcoded here, but they can be
        # changed in the translations
        # FIXME: there are more keyboard shortcuts that don't work in dialogs
        # at the moment, like DELETE
        self.__new_effort_id = IdProvider.get()
        table = wx.AcceleratorTable(
            [
                (wx.ACCEL_CMD, ord("Z"), wx.ID_UNDO),
                (wx.ACCEL_CMD, ord("Y"), wx.ID_REDO),
                (wx.ACCEL_CMD, ord("E"), self.__new_effort_id),
            ]
        )
        self._interior.SetAcceleratorTable(table)
        # pylint: disable=W0201
        self.__undo_command = uicommand.EditUndo()
        self.__redo_command = uicommand.EditRedo()
        effort_page = self._interior.getPage("effort")
        effort_viewer = effort_page.viewer if effort_page else None
        self.__new_effort_command = uicommand.EffortNew(
            viewer=effort_viewer,
            taskList=self._taskFile.tasks(),
            effortList=self._taskFile.efforts(),
            settings=self._settings,
        )
        self.__undo_command.bind(self._interior, wx.ID_UNDO)
        self.__redo_command.bind(self._interior, wx.ID_REDO)
        self.__new_effort_command.bind(self._interior, self.__new_effort_id)

    def createInterior(self):
        return self.EditBookClass(
            self._panel,
            self._items,
            self._taskFile,
            self._settings,
            self.__items_are_new,
        )

    def on_close_editor(self, event):
        event.Skip()
        self._interior.close_edit_book()
        patterns.Publisher().removeObserver(self.on_item_removed)
        patterns.Publisher().removeObserver(self.on_subject_changed)
        # On Mac OS X, the text control does not lose focus when
        # destroyed...
        if operating_system.isMac():
            self._interior.SetFocusIgnoringChildren()
        if self.__timer is not None:
            IdProvider.put(self.__timer.GetId())  # Libérer l'identifiant
        IdProvider.put(self.__new_effort_id)
        self.Destroy()

    # Nouvelle fonction conseillée par chatGPT
    # def __del__(self):
    #    if self.__timer and self.__timer.IsRunning():
    #        self.__timer.Stop()
    #    if self.__timer:
    #        IdProvider.put(self.__timer.GetId())  # Libérer l'identifiant

    # @staticmethod
    def on_activate(self, event):
        event.Skip()

    def on_item_removed(self, event):
        """L'élément que nous modifions ou l'un de ses ancêtres a été supprimé ou
        est masqué par un filtre. Si l'élément est réellement supprimé, fermez l'onglet
        de l'élément concerné et fermez tout l'éditeur s'il ne reste plus d'onglets
        ."""
        if self:  # Prevent _wxPyDeadObject TypeError
            self.__call_after(self.__close_if_item_is_deleted, list(event.values()))

    def __close_if_item_is_deleted(self, items):
        for item in items:
            if (
                self._interior.isDisplayingItemOrChildOfItem(item)
                and not item in self._taskFile
            ):  # PEP 8: E713 test for membership should be 'not in'
                self.Close()
                break

    def on_subject_changed(self, event):  # pylint: disable=W0613
        self.SetTitle(self.__title())

    def __title(self):
        return (
            self.plural_title
            if len(self._items) > 1
            else self.singular_title % self._items[0].subject()
        )


class TaskEditor(Editor):
    plural_title = _("Multiple tasks")
    singular_title = _("%s (task)")
    EditBookClass = TaskEditBook


class CategoryEditor(Editor):
    plural_title = _("Multiple categories")
    singular_title = _("%s (category)")
    EditBookClass = CategoryEditBook


class NoteEditor(Editor):
    plural_title = _("Multiple notes")
    singular_title = _("%s (note)")
    EditBookClass = NoteEditBook


class AttachmentEditor(Editor):
    plural_title = _("Multiple attachments")
    singular_title = _("%s (attachment)")
    EditBookClass = AttachmentEditBook


class EffortEditor(Editor):
    plural_title = _("Multiple efforts")
    singular_title = _("%s (effort)")
    EditBookClass = EffortEditBook
