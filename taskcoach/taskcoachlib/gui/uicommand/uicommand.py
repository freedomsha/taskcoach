# -*- coding: utf-8 -*-

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

Explication des classes :

    HideCurrentColumn : Cette classe permet de masquer la colonne sous la souris, en utilisant la position actuelle de la souris pour déterminer quelle colonne masquer.
    ViewColumn : Cette classe gère l'affichage ou le masquage d'une colonne spécifique en fonction du nom de la colonne.
    ViewColumns : Cette classe permet de gérer plusieurs colonnes simultanément, en affichant ou en masquant un groupe de colonnes dans la visionneuse.
"""

# from builtins import str
# from builtins import object
# from io import open as file

from taskcoachlib import (
    patterns,
    meta,
    command,
    help,
    widgets,
    persistence,
    thirdparty,
    render,
    operating_system,
)  # pylint: disable=W0622
from taskcoachlib.domain import base, task, note, category, attachment, effort, date
from taskcoachlib.gui import dialog, printer
# import taskcoachlib.gui.dialog
# import taskcoachlib.gui.printer
from taskcoachlib.gui.wizard import CSVImportWizard
from taskcoachlib.i18n import _
from taskcoachlib.mailer import sendMail
# from .taskcoachlib.thirdparty.agw import hypertreelist
from wx.lib.agw import hypertreelist
# try:
#    from ...thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
from pubsub import pub
from taskcoachlib.thirdparty.wxScheduler import (
    wxSCHEDULER_NEXT,
    wxSCHEDULER_PREV,
    wxSCHEDULER_TODAY,
)
from taskcoachlib.tools import anonymize, openfile
from taskcoachlib.workarounds import ExceptionAsUnicode
import wx
import re
import operator
from taskcoachlib.gui.uicommand import base_uicommand
from taskcoachlib.gui.uicommand import mixin_uicommand
from taskcoachlib.gui.uicommand import settings_uicommand
from functools import reduce


class IOCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande d'entrée/sortie (IOCommand) de base qui gère les opérations d'entrée/sortie (comme ouvrir ou sauvegarder un fichier) via un contrôleur I/O.

    Attributs :
        iocontroller (IOController) : Le contrôleur I/O responsable des opérations sur les fichiers.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande IOCommand avec un contrôleur I/O fourni via les arguments.

        Args:
            iocontroller (IOController) : Contrôleur I/O chargé de gérer les fichiers.
        """
        self.iocontroller = kwargs.pop("iocontroller", None)
        super().__init__(*args, **kwargs)


class TaskListCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande spécifique à la gestion d'une liste de tâches. Utilisée pour manipuler et interagir avec une liste de tâches.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de tâches fournie.

        Args:
            taskList (TaskList) : La liste des tâches à manipuler.
        """
        self.taskList = kwargs.pop("taskList", None)
        super().__init__(*args, **kwargs)


class EffortListCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande spécifique à la gestion d'une liste d'efforts (suivi du temps). Utilisée pour manipuler et interagir avec une liste d'efforts.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste d'efforts fournie.

        Args:
            effortList (EffortList) : La liste des efforts à manipuler.
        """
        self.effortList = kwargs.pop("effortList", None)
        super().__init__(*args, **kwargs)


class CategoriesCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour gérer les catégories. Utilisée pour interagir avec une liste de catégories.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de catégories fournie.

        Args :
            categories (CategoryList) : La liste des catégories.
        """
        self.categories = kwargs.pop("categories", None)
        super().__init__(*args, **kwargs)


class NotesCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour gérer les notes. Utilisée pour interagir avec une liste de notes.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de notes fournie.

        Args :
            notes (NoteList) : La liste des notes.
        """
        self.notes = kwargs.pop("notes", None)
        super().__init__(*args, **kwargs)


class AttachmentsCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    def __init__(self, *args, **kwargs):
        self.attachments = kwargs.pop("attachments", None)
        super().__init__(*args, **kwargs)


class ViewerCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour interagir avec une visionneuse (viewer). Permet d'exécuter des actions liées à l'affichage d'une présentation de données.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une visionneuse fournie.

        Args :
            viewer (Viewer) : La visionneuse pour laquelle la commande est exécutée.
        """
        self.viewer = kwargs.pop("viewer", None)
        super().__init__(*args, **kwargs)

     #def __eq__(self, other) -> bool:
    def __eq__(self, other):
        """
        Compare cette commande avec une autre pour vérifier si elles sont égales. Deux commandes sont égales si elles partagent la même section de paramètres de la visionneuse.

        Args :
            other (ViewerCommand) : La commande avec laquelle comparer.

        Returns :
            bool : True si les commandes sont égales, False sinon.
        """
        return (
            super().__eq__(other)
            and self.viewer.settingsSection() == other.viewer.settingsSection()
        )


# Commands:


class FileOpen(IOCommand):
    """
    Commande pour ouvrir un fichier. Utilise un contrôleur I/O pour ouvrir un fichier de tâche.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'ouverture de fichier avec des paramètres spécifiques pour l'interface utilisateur, comme le texte du menu et l'icône associée.
        """
        super().__init__(
            menuText=_("&Open...\tCtrl+O"),
            helpText=help.fileOpen,
            bitmap="fileopen",
            id=wx.ID_OPEN,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande d'ouverture de fichier. Ouvre un fichier en utilisant le contrôleur I/O.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.iocontroller.open()


class RecentFileOpen(IOCommand):
    """
    Commande pour ouvrir un fichier récemment utilisé. Utilise un contrôleur I/O pour ouvrir le fichier spécifié.

    Attributs :
        __filename (str) : Le chemin ou nom du fichier à ouvrir.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec le nom du fichier à ouvrir.

        Args:
            filename (str) : Le nom du fichier récent.
            index (int) : L'indice dans la liste des fichiers récents.
        """
        self.__filename = kwargs.pop("filename")
        index = kwargs.pop("index")
        super().__init__(
            menuText="%d %s" % (index, self.__filename),
            helpText=_("Open %s") % self.__filename,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Ouvre le fichier récent sélectionné."""
        self.iocontroller.open(self.__filename)


class FileMerge(IOCommand):
    """
    Commande pour fusionner des tâches d'un autre fichier avec le fichier actuel.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de fusion.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Merge..."),
            helpText=_("Merge tasks from another file with the current file"),
            bitmap="merge",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande pour fusionner les tâches."""
        self.iocontroller.merge()


class FileClose(IOCommand):
    """
    Commande pour fermer le fichier actuel.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de fermeture de fichier.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Close\tCtrl+W"),
            helpText=help.fileClose,
            bitmap="Close",
            id=wx.ID_CLOSE,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Ferme le fichier et les éditeurs associés."""
        self.mainWindow().closeEditors()
        self.iocontroller.Close()


class FileSave(IOCommand):
    """
    Commande pour sauvegarder le fichier actuel.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Save\tCtrl+S"),
            helpText=help.fileSave,
            bitmap="save",
            id=wx.ID_SAVE,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Sauvegarde le fichier actuel."""
        self.iocontroller.save()

    def enabled(self, event):
        """Vérifie si la sauvegarde est nécessaire."""
        return self.iocontroller.needSave()


class FileMergeDiskChanges(IOCommand):
    """
    Commande pour fusionner les changements sur disque avec le fichier actuel.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour fusionner les changements.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Merge &disk changes\tShift-Ctrl-M"),
            helpText=help.fileMergeDiskChanges,
            bitmap="mergedisk",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Fusionne les changements détectés sur disque."""
        self.iocontroller.mergeDiskChanges()

    def enabled(self, event):
        """Active la commande si des changements ont été détectés sur disque."""
        return self.iocontroller.changedOnDisk()


class FileSaveAs(IOCommand):
    """
    Commande pour sauvegarder le fichier actuel sous un autre nom.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde sous un autre nom.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("S&ave as...\tShift+Ctrl+S"),
            helpText=help.fileSaveAs,
            bitmap="saveas",
            id=wx.ID_SAVEAS,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Sauvegarde le fichier sous un autre nom."""
        self.iocontroller.saveas()


class FileSaveSelection(
    mixin_uicommand.NeedsSelectedTasksMixin, IOCommand, ViewerCommand
):
    """
    Commande pour sauvegarder les tâches sélectionnées dans un nouveau fichier de tâches.

    Attributs :
        viewer (Viewer) : La visionneuse de tâches utilisée pour obtenir les tâches sélectionnées.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde des tâches sélectionnées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Sa&ve selected tasks to new taskfile..."),
            helpText=_("Save the selected tasks to a separate taskfile"),
            bitmap="saveselection",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande pour sauvegarder les tâches sélectionnées."""
        self.iocontroller.saveselection(self.viewer.curselection())


class FileSaveSelectedTaskAsTemplate(
    mixin_uicommand.NeedsOneSelectedTaskMixin, IOCommand, ViewerCommand
):
    """
    Commande pour sauvegarder la tâche sélectionnée en tant que modèle de tâche.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour obtenir la tâche sélectionnée.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde de la tâche en tant que modèle.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Save selected task as &template"),
            helpText=_("Save the selected task as a task template"),
            bitmap="saveselection",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande pour sauvegarder la tâche sélectionnée en tant que modèle."""
        self.iocontroller.saveastemplate(self.viewer.curselection()[0])


class FileImportTemplate(IOCommand):
    """
    Commande pour importer un modèle depuis un fichier de modèles.

    Attributs :
        iocontroller (IOController) : Le contrôleur utilisé pour gérer les fichiers.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'importation de modèle.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Import template..."),
            helpText=_("Import a new template from a template file"),
            bitmap="fileopen",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande pour importer un modèle depuis un fichier."""
        self.iocontroller.importTemplate()


class FileEditTemplates(settings_uicommand.SettingsCommand, base_uicommand.UICommand):
    """
    Commande pour éditer les modèles existants.

    Attributs :
        settings (Settings) : Les paramètres de l'application.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'édition des modèles.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Edit templates..."),
            helpText=_("Edit existing templates"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Affiche la boîte de dialogue pour éditer les modèles existants."""
        templateDialog = dialog.templates.TemplatesDialog(
            self.settings, self.mainWindow(), title=_("Edit templates")
        )
        templateDialog.Show()


class FilePurgeDeletedItems(mixin_uicommand.NeedsDeletedItemsMixin, IOCommand):
    """
    Commande pour purger définitivement les éléments supprimés (tâches et notes).

    Utilisée lorsque l'on souhaite supprimer de manière irréversible des éléments marqués comme supprimés.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour purger les éléments supprimés.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Purge deleted items"),
            helpText=_(
                "Actually delete deleted tasks and notes "
                "(see the SyncML chapter in Help)"
            ),
            bitmap="delete",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Purge les éléments supprimés après confirmation de l'utilisateur.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        if (
            wx.MessageBox(
                _(
                    """Purging deleted items is undoable.
If you're planning on enabling
the SyncML feature again with the
same server you used previously,
these items will probably come back.

Do you still want to purge?"""
                ),
                _("Warning"),
                wx.YES_NO,
            )
            == wx.YES
        ):
            self.iocontroller.purgeDeletedItems()


class PrintPageSetup(settings_uicommand.SettingsCommand, base_uicommand.UICommand):
    """
    Commande pour changer les paramètres de la page. Les paramètres de la page sont sauvegardés dans les réglages de l'application.

    Attributs :
        settings (Settings) : Les paramètres de l'application pour sauvegarder les configurations de la page.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de texte et d'icône associées.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Page setup...\tShift+Ctrl+P"),
            helpText=help.printPageSetup,
            bitmap="pagesetup",
            id=wx.ID_PRINT_SETUP,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Ouvre une boîte de dialogue pour modifier les paramètres de la page et les applique aux réglages de l'application.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        printerSettings = printer.PrinterSettings(self.settings)
        pageSetupDialog = wx.PageSetupDialog(
            self.mainWindow(), printerSettings.pageSetupData
        )
        result = pageSetupDialog.ShowModal()
        if result == wx.ID_OK:
            pageSetupData = pageSetupDialog.GetPageSetupData()
            printerSettings.updatePageSetupData(pageSetupData)
        pageSetupDialog.Destroy()


class PrintPreview(ViewerCommand, settings_uicommand.SettingsCommand):
    """
    Commande pour afficher un aperçu de l'impression du contenu actuel de la visionneuse.

    Attributs :
        viewer (Viewer) : La visionneuse de l'application dont le contenu sera imprimé.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de texte et d'icône associées.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Print preview..."),
            helpText=_("Show a preview of what the print will look like"),
            bitmap="printpreview",
            id=wx.ID_PREVIEW,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Affiche la fenêtre d'aperçu de l'impression avec deux versions de sortie pour l'impression.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        printout, printout2 = printer.Printout(
            self.viewer, self.settings, twoPrintouts=True
        )
        printerSettings = printer.PrinterSettings(self.settings)
        preview = wx.PrintPreview(printout, printout2, printerSettings.printData)
        previewFrame = wx.PreviewFrame(
            preview, self.mainWindow(), _("Print preview"), size=(750, 700)
        )
        previewFrame.Initialize()
        previewFrame.Show()


class Print(ViewerCommand, settings_uicommand.SettingsCommand):
    """
    Commande pour imprimer le contenu actuel de la visionneuse.

    Attributs :
        viewer (Viewer) : La visionneuse dont le contenu sera imprimé.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de texte et d'icône associées.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Print...\tCtrl+P"),
            helpText=help.print_,
            bitmap="print",
            id=wx.ID_PRINT,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Ouvre une boîte de dialogue d'impression, configure les options, et imprime le contenu sélectionné ou l'intégralité du document.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        printerSettings = printer.PrinterSettings(self.settings)
        printDialogData = wx.PrintDialogData(printerSettings.printData)
        printDialogData.EnableSelection(True)
        wxPrinter = wx.Printer(printDialogData)
        if not wxPrinter.PrintDialog(self.mainWindow()):
            return
        printout = printer.Printout(
            self.viewer,
            self.settings,
            printSelectionOnly=wxPrinter.PrintDialogData.Selection,
        )
        # If the user checks the selection radio button, the ToPage property
        # gets set to 1. Looks like a bug to me. The simple work-around is to
        # reset the ToPage property to the MaxPage value if necessary:
        # Si l'utilisateur sélectionne l'option de sélection, ajuste les pages à imprimer:
        if wxPrinter.PrintDialogData.Selection:
            wxPrinter.PrintDialogData.ToPage = wxPrinter.PrintDialogData.MaxPage
        wxPrinter.Print(self.mainWindow(), printout, prompt=False)


class FileExportCommand(IOCommand, settings_uicommand.SettingsCommand):
    """
    Classe de base pour les actions d'exportation.

    Permet d'exporter des éléments depuis une visionneuse vers différents formats de fichier.
    """

    def doCommand(self, event):
        """
        Exécute la commande d'exportation. Ouvre la boîte de dialogue pour définir les options d'exportation et appelle la fonction d'exportation correspondante.
        """
        exportDialog = self.getExportDialogClass()(
            self.mainWindow(), settings=self.settings
        )  # pylint: disable=E1101
        if wx.ID_OK == exportDialog.ShowModal():
            exportOptions = exportDialog.options()
            selectedViewer = exportOptions.pop("selectedViewer")
            # pylint: disable=W0142
            self.exportFunction()(selectedViewer, **exportOptions)
        exportDialog.Destroy()

    @staticmethod
    def getExportDialogClass():
        """Retourne la classe à utiliser pour la boîte de dialogue d'exportation."""
        raise NotImplementedError

    def exportFunction(self):
        """Retourne une fonction qui effectue l'exportation réelle. Cette fonction prend la visionneuse sélectionnée et les options d'exportation en paramètres."""
        raise NotImplementedError  # pragma: no cover


class FileManageBackups(IOCommand, settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Manage backups..."),
            helpText=_("Manage all task file backups"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        dlg = dialog.BackupManagerDialog(
            self.mainWindow(), self.settings, self.iocontroller.filename()
        )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.iocontroller.open(dlg.restoredFilename())
        finally:
            dlg.Destroy()


class FileExportAsHTML(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format HTML.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &HTML..."),
            helpText=_("Export items from a viewer in HTML format"),
            bitmap="exportashtml",
            *args,
            **kwargs
        )

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsHTMLDialog

    def exportFunction(self):
        return self.iocontroller.exportAsHTML


class FileExportAsCSV(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format CSV.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &CSV..."),
            helpText=_(
                "Export items from a viewer in Comma Separated Values " "(CSV) format"
            ),
            bitmap="exportascsv",
            *args,
            **kwargs
        )

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsCSVDialog

    def exportFunction(self):
        return self.iocontroller.exportAsCSV


class FileExportAsICalendar(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format iCalendar.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &iCalendar..."),
            helpText=_("Export items from a viewer in iCalendar format"),
            bitmap="exportasvcal",
            *args,
            **kwargs
        )

    def exportFunction(self):
        return self.iocontroller.exportAsICalendar

    def enabled(self, event):
        return any(self.exportableViewer(viewer) for viewer in self.mainWindow().viewer)

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsICalendarDialog

    @staticmethod
    def exportableViewer(aViewer) -> bool:
        """Vérifie si la visionneuse peut être exportée au format iCalendar."""
        return aViewer.isShowingTasks() or (
            aViewer.isShowingEffort() and not aViewer.isShowingAggregatedEffort()
        )


class FileExportAsTodoTxt(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format Todo.txt.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &Todo.txt..."),
            helpText=_(
                "Export items from a viewer in Todo.txt format " "(see todotxt.com)"
            ),
            bitmap="exportascsv",
            *args,
            **kwargs
        )

    def exportFunction(self):
        return self.iocontroller.exportAsTodoTxt

    def enabled(self, event):
        return any(self.exportableViewer(viewer) for viewer in self.mainWindow().viewer)

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsTodoTxtDialog

    @staticmethod
    def exportableViewer(aViewer):
        """Vérifie si la visionneuse peut être exportée au format Todo.txt."""
        return aViewer.isShowingTasks()


class FileImportCSV(IOCommand):
    """
    Action pour importer des données à partir d'un fichier CSV dans le fichier de tâches actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'importation de CSV avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Import CSV..."),
            helpText=_("Import tasks from a Comma Separated Values (CSV) file"),
            bitmap="exportascsv",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande d'importation de CSV. Ouvre une boîte de dialogue pour sélectionner un fichier CSV et lance l'importation.
        """
        while True:
            filename = wx.FileSelector(_("Import CSV"), wildcard="*.csv")
            if filename:
                if len(open(filename, "rb").read()) == 0:
                    wx.MessageBox(
                        _(
                            "The selected file is empty. "
                            "Please select a different file."
                        ),
                        _("Import CSV"),
                    )
                    continue
                wizard = CSVImportWizard(filename, None, wx.ID_ANY, _("Import CSV"))
                if wizard.RunWizard():
                    self.iocontroller.importCSV(**wizard.GetOptions())
                    break
            else:
                break


class FileImportTodoTxt(IOCommand):
    """
    Action pour importer des données à partir d'un fichier Todo.txt dans le fichier de tâches actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'importation de Todo.txt avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Import Todo.txt..."),
            helpText=_("Import tasks from a Todo.txt (see todotxt.com) file"),
            bitmap="exportascsv",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande d'importation de Todo.txt.

        Ouvre une boîte de dialogue pour sélectionner un fichier Todo.txt et lance l'importation.
        """
        filename = wx.FileSelector(_("Import Todo.txt"), wildcard="*.txt")
        if filename:
            self.iocontroller.importTodoTxt(filename)


class FileSynchronize(IOCommand, settings_uicommand.SettingsCommand):
    """
    Action pour synchroniser le fichier de tâches actuel avec un serveur SyncML.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de synchronisation avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("S&yncML synchronization..."),
            helpText=_("Synchronize with a SyncML server"),
            bitmap="arrows_looped_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande de synchronisation. Lance le processus de synchronisation avec le serveur SyncML configuré.
        """
        self.iocontroller.synchronize()


class FileQuit(base_uicommand.UICommand):
    """
    Action pour quitter l'application.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour quitter avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Quit\tCtrl+Q"),
            helpText=help.fileQuit,
            bitmap="exit",
            id=wx.ID_EXIT,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour quitter l'application. Ferme la fenêtre principale de l'application.
        """
        self.mainWindow().Close(force=True)


class EditUndo(base_uicommand.UICommand):
    """
    Action pour annuler la dernière action effectuée par l'utilisateur.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les actions de l'utilisateur.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'annulation.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=self.getUndoMenuText(),
            helpText=help.editUndo,
            bitmap="undo",
            id=wx.ID_UNDO,
            *args,
            **kwargs
        )

    @staticmethod
    def getUndoMenuText():
        """Retourne le texte du menu pour la commande d'annulation, en incluant la description de la dernière action utilisateur."""
        return "%s\tCtrl+Z" % patterns.CommandHistory().undostr(_("&Undo"))

    def doCommand(self, event):
        """Exécute la commande d'annulation en utilisant l'historique des commandes."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Undo()
        else:
            patterns.CommandHistory().undo()

    def onUpdateUI(self, event):
        """Met à jour le texte du menu avec la dernière action utilisateur."""
        self.updateMenuText(self.getUndoMenuText())
        super().onUpdateUI(event)

    def enabled(self, event):
        """Vérifie si l'annulation est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanUndo()
        else:
            # TODO: hasHistory is a list !? a bool was better ?
            return patterns.CommandHistory().hasHistory() and super().enabled(event)


class EditRedo(base_uicommand.UICommand):
    """
    Action pour rétablir la dernière action annulée par l'utilisateur.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les actions utilisateur.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de rétablissement.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=self.getRedoMenuText(),
            helpText=help.editRedo,
            bitmap="redo",
            id=wx.ID_REDO,
            *args,
            **kwargs
        )

    @staticmethod
    def getRedoMenuText() -> str:
        """Retourne le texte du menu pour la commande de rétablissement, incluant une description de l'action suivante à rétablir."""
        return "%s\tCtrl+Y" % patterns.CommandHistory().redostr(_("&Redo"))

    def doCommand(self, event):
        """Exécute la commande de rétablissement en utilisant l'historique des commandes."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Redo()
        else:
            patterns.CommandHistory().redo()

    def onUpdateUI(self, event):
        """Met à jour le texte du menu avec la prochaine action à rétablir."""
        self.updateMenuText(self.getRedoMenuText())
        super().onUpdateUI(event)

    def enabled(self, event):
        """Vérifie si le rétablissement est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanRedo()
        else:
            # Todo: hasFuture is a List ! not a bool !
            return patterns.CommandHistory().hasFuture() and super().enabled(event)


class EditCut(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Action pour couper les éléments sélectionnés et les placer dans le presse-papier.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de découpage.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Cu&t\tCtrl+X"),
            helpText=help.editCut,
            bitmap="cut",
            # id=wx.ID_CUT,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande de découpage."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Cut()
        else:
            cutCommand = self.viewer.cutItemCommand()
            cutCommand.do()

    def enabled(self, event):
        """Vérifie si le découpage est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            # Todo: CanCut can be None ! a bool would be better !?
            return windowWithFocus.CanCut()
        else:
            return super().enabled(event)


class EditCopy(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Action pour copier les éléments sélectionnés dans le presse-papier.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de copie.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Copy\tCtrl+C"),
            helpText=help.editCopy,
            bitmap="copy",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande de copie."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Copy()
        else:
            copyCommand = command.CopyCommand(
                self.viewer.presentation(), self.viewer.curselection()
            )
            copyCommand.do()

    def enabled(self, event):
        """Vérifie si la copie est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            # Todo: CanCut can be None ! a bool would be better !?
            return windowWithFocus.CanCopy()
        else:
            return super().enabled(event)


class EditPaste(base_uicommand.UICommand):
    """
    Action pour coller le(s) élément(s) du presse-papier dans le fichier de tâches actuel.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour coller les éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de collage.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Paste\tCtrl+V"),
            helpText=help.editPaste,
            bitmap="paste",
            id=wx.ID_PASTE,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """Exécute la commande de collage."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Paste()
        else:
            pasteCommand = command.PasteCommand()
            pasteCommand.do()

    def enabled(self, event):
        """Vérifie si le collage est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            # Todo: CanPaste can be None ! a bool would be better !?
            return windowWithFocus.CanPaste()
        else:
            return command.Clipboard() and super().enabled(event)


class EditPasteAsSubItem(mixin_uicommand.NeedsSelectedCompositeMixin, ViewerCommand):
    """
    Action pour coller les éléments du presse-papier dans le fichier de tâches actuel,
    en tant que sous-élément de l'élément actuellement sélectionné.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour coller les éléments en tant que sous-éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de menu et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("P&aste as subitem\tShift+Ctrl+V"),
            helpText=help.editPasteAsSubitem,
            bitmap="pasteintotask",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande de collage en tant que sous-élément.
        """
        pasteCommand = command.PasteAsSubItemCommand(items=self.viewer.curselection())
        pasteCommand.do()

    def enabled(self, event) -> bool:
        """
        Vérifie si le collage en tant que sous-élément est possible.
        """
        if not (super().enabled(event) and command.Clipboard()):
            return False
        targetClass = self.viewer.curselection()[0].__class__
        pastedClasses = [item.__class__ for item in command.Clipboard().peek()]
        return self.__targetAndPastedAreEqual(
            targetClass, pastedClasses
        ) or self.__targetIsTaskAndPastedIsEffort(targetClass, pastedClasses)

    @classmethod
    def __targetIsTaskAndPastedIsEffort(cls, targetClass, pastedClasses) -> bool:
        """Vérifie si la classe cible est une tâche et les éléments collés sont tous des efforts."""
        if targetClass != task.Task:
            return False

        return cls.__targetAndPastedAreEqual(effort.Effort, pastedClasses)

    @staticmethod
    def __targetAndPastedAreEqual(targetClass, pastedClasses) -> bool:
        """Vérifie si les classes de la cible et les éléments collés sont identiques."""
        for pastedClass in pastedClasses:
            if pastedClass != targetClass:
                return False
        return True


class EditPreferences(settings_uicommand.SettingsCommand):
    """
    Action pour ouvrir la boîte de dialogue des préférences.

    Attributs :
        settings (Settings) : Les paramètres de l'application.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande des préférences avec les options de menu et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Preferences...\tAlt+P"),
            helpText=help.editPreferences,
            bitmap="wrench_icon",
            id=wx.ID_PREFERENCES,
            *args,
            **kwargs
        )

    def doCommand(self, event, show: bool = True):  # pylint: disable=W0221
        """
        Affiche la boîte de dialogue des préférences.

        Args:
            event (wx.Event) : L'événement déclencheur.
            show (bool) : Indique si la boîte de dialogue doit être affichée.
        """
        editor = dialog.preferences.Preferences(
            parent=self.mainWindow(), title=_("Preferences"), settings=self.settings
        )
        editor.Show(show=show)


class EditSyncPreferences(IOCommand):
    """
    Action pour afficher les préférences de synchronisation SyncML.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande des préférences de synchronisation.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&SyncML preferences..."),
            helpText=_("Edit SyncML preferences"),
            bitmap="arrows_looped_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event, show: bool = True):  # pylint: disable=W0221
        """
        Affiche la boîte de dialogue des préférences de synchronisation SyncML.

        Args:
            event (wx.Event) : L'événement déclencheur.
            show (bool) : Indique si la boîte de dialogue doit être affichée.
        """
        editor = dialog.syncpreferences.SyncMLPreferences(
            parent=self.mainWindow(),
            iocontroller=self.iocontroller,
            title=_("SyncML preferences"),
        )
        editor.Show(show=show)


class EditToolBarPerspective(settings_uicommand.SettingsCommand):
    """
    Action pour éditer une barre d'outils personnalisable.

    Attributs :
        toolbar (wx.ToolBar) : La barre d'outils à personnaliser.
        editorClass (Class) : La classe utilisée pour éditer la barre d'outils.
    """

    def __init__(self, toolbar, editorClass, *args, **kwargs):
        """
        Initialise la commande pour personnaliser la barre d'outils.

        Args :
            toolbar (wx.ToolBar) : La barre d'outils à personnaliser.
            editorClass (Class) : La classe utilisée pour éditer la barre d'outils.
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        self.__toolbar = toolbar
        self.__editorClass = editorClass
        super().__init__(
            helpText=_("Customize toolbar"),
            bitmap="cogwheel_icon",
            menuText=_("Customize"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Affiche la boîte de dialogue de personnalisation de la barre d'outils.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.__editorClass(
            self.__toolbar, self.settings, self.mainWindow(), _("Customize toolbar")
        ).ShowModal()


class SelectAll(mixin_uicommand.NeedsItemsMixin, ViewerCommand):
    """
    Action pour sélectionner tous les éléments dans une visionneuse.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour sélectionner tous les éléments avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&All\tCtrl+A"),
            helpText=help.editSelectAll,
            bitmap="selectall",
            id=wx.ID_SELECTALL,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour sélectionner tous les éléments visibles dans la visionneuse.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.windowIsTextCtrl(windowWithFocus):
            windowWithFocus.SetSelection(-1, -1)  # Sélectionne tout le texte
        else:
            self.viewer.select_all()

    @staticmethod
    def windowIsTextCtrl(window) -> bool:
        """
        Vérifie si la fenêtre actuelle est un contrôle de texte.
        """
        return isinstance(window, wx.TextCtrl) or isinstance(
            window, hypertreelist.EditCtrl
        )


class ClearSelection(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Action pour désélectionner tous les éléments dans une visionneuse.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour désélectionner tous les éléments avec les options de menu appropriées.
        """
        super().__init__(
            menuText=_("&Clear selection"),
            helpText=_("Unselect all items"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour désélectionner tous les éléments.
        """
        self.viewer.clear_selection()


class ResetFilter(ViewerCommand):
    """
    Action pour réinitialiser tous les filtres afin que tous les éléments deviennent visibles dans toutes les visionneuses.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour réinitialiser tous les filtres avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Clear all filters\tShift-Ctrl-R"),
            helpText=help.resetFilter,
            bitmap="viewalltasks",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour réinitialiser tous les filtres actifs dans la visionneuse.
        """
        self.viewer.resetFilter()

    def enabled(self, event):
        """
        Vérifie si la commande est activée, c'est-à-dire s'il y a des filtres actifs à réinitialiser.
        """
        return self.viewer.hasFilter()


class ResetCategoryFilter(
    mixin_uicommand.NeedsAtLeastOneCategoryMixin, CategoriesCommand
):
    """
    Action pour réinitialiser tous les filtres de catégories afin que les éléments ne soient plus cachés en fonction des catégories.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour réinitialiser les filtres de catégories avec les options de menu appropriées.
        """
        super().__init__(
            menuText=_("&Reset all categories\tCtrl-R"),
            helpText=help.resetCategoryFilter,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour réinitialiser les filtres de catégories actifs.
        """
        self.categories.resetAllFilteredCategories()


class ToggleCategoryFilter(base_uicommand.UICommand):
    """
    Action pour activer ou désactiver le filtrage sur une catégorie spécifique.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de filtrage par catégorie avec les options de menu appropriées.
        """
        self.category = kwargs.pop("category")
        subject = self.category.subject()
        # Would like to use wx.ITEM_RADIO for mutually exclusive categories, but
        # a menu with radio items always has to have at least of the items
        # checked, while we allow none of the mutually exclusive categories to
        # be checked. Dynamically changing between wx.ITEM_CHECK and
        # wx.ITEM_RADIO would be a work-around in theory, using wx.ITEM_CHECK
        # when none of the mutually exclusive categories is checked and
        # wx.ITEM_RADIO otherwise, but dynamically changing the type of menu
        # items isn't possible. Hence, we use wx.ITEM_CHECK, even for mutual
        # exclusive categories.
        kind = wx.ITEM_CHECK
        super().__init__(
            menuText="&" + subject.replace("&", "&&"),
            helpText=_("Show/hide items belonging to %s") % subject,
            kind=kind,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour activer ou désactiver le filtrage sur la catégorie spécifiée.
        """
        self.category.setFiltered(event.IsChecked())


class ViewViewer(settings_uicommand.SettingsCommand, ViewerCommand):
    """
    Action pour ouvrir une nouvelle visionneuse d'une classe spécifique.

    Attributs :
        taskFile (TaskFile) : Le fichier de tâches utilisé par la visionneuse.
        viewerClass (class) : La classe de la visionneuse à ouvrir.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour ouvrir une nouvelle visionneuse.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires, y compris 'taskFile' et 'viewerClass'.
        """
        self.taskFile = kwargs.pop("taskFile")
        self.viewerClass = kwargs.pop("viewerClass")
        kwargs.setdefault("bitmap", self.viewerClass.defaultBitmap)
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Ouvre une nouvelle instance de la visionneuse spécifiée.
        """
        from taskcoachlib.gui import viewer

        viewer.addOneViewer(self.viewer, self.taskFile, self.settings, self.viewerClass)
        self.increaseViewerCount()

    def increaseViewerCount(self):
        """
        Augmente le compteur de la classe visionneuses ouvertes, ouvre et enregistre la valeur dans les paramètres.
        """
        setting = self.viewerClass.__name__.lower() + "count"
        viewerCount = self.settings.getint("view", setting)
        self.settings.set("view", setting, str(viewerCount + 1))


class ViewEffortViewerForSelectedTask(
    settings_uicommand.SettingsCommand, ViewerCommand
):
    """
    Action pour ouvrir une visionneuse d'efforts pour les tâches sélectionnées.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour ouvrir une visionneuse d'efforts.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires, y compris 'taskFile'.
        """
        from taskcoachlib.gui import viewer

        self.viewerClass = viewer.EffortViewerForSelectedTasks
        self.taskFile = kwargs.pop("taskFile")
        kwargs["bitmap"] = viewer.EffortViewer.defaultBitmap
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Ouvre une visionneuse d'efforts pour les tâches sélectionnées.
        """
        from taskcoachlib.gui import viewer

        viewer.addOneViewer(self.viewer, self.taskFile, self.settings, self.viewerClass)


class RenameViewer(ViewerCommand):
    """
    Action pour renommer la visionneuse sélectionnée.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de renommage de la visionneuse.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Rename viewer..."),
            helpText=_("Rename the selected viewer"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Renomme la visionneuse active avec un nouveau nom.
        """
        activeViewer = self.viewer.activeViewer()
        viewerNameDialog = wx.TextEntryDialog(
            self.mainWindow(),
            _("New title for the viewer:"),
            _("Rename viewer"),
            activeViewer.title(),
        )
        if viewerNameDialog.ShowModal() == wx.ID_OK:
            activeViewer.setTitle(viewerNameDialog.GetValue())
        viewerNameDialog.Destroy()

    def enabled(self, event):
        """
        Active la commande uniquement si une visionneuse est active.
        """
        return bool(self.viewer.activeViewer())


class ActivateViewer(ViewerCommand):
    """
    Action pour activer une autre visionneuse dans la direction spécifiée.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour changer de visionneuse.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        self.direction = kwargs.pop("forward")
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Change de visionneuse dans la direction spécifiée.
        """
        self.viewer.containerWidget.advanceSelection(self.direction)

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement s'il y a plus d'une visionneuse.
        """
        return self.viewer.containerWidget.viewerCount() > 1


class HideCurrentColumn(ViewerCommand):
    """
    Action pour masquer la colonne actuellement sélectionnée dans la visionneuse.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour masquer la colonne sélectionnée.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Hide this column"),
            helpText=_("Hide the selected column"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Masque la colonne sélectionnée dans la visionneuse.

        Exécute la commande pour masquer la colonne sélectionnée dans la visionneuse.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        columnPopupMenu = event.GetEventObject()
        self.viewer.hideColumn(columnPopupMenu.columnIndex)

    def enabled(self, event) -> bool:
        """
        Vérifie si la commande peut être exécutée, en déterminant la colonne actuelle basée sur la position de la souris.

        Args:
            event (wx.Event) : L'événement pour lequel la disponibilité de la commande est vérifiée.

        Returns:
            bool : True si la colonne peut être masquée, sinon False.
        """
        # Unfortunately the event (an UpdateUIEvent) does not give us any
        # information to determine the current column, so we have to find
        # the column ourselves. We use the current mouse position to do so.
        widget = (
            self.viewer.getWidget()
        )  # Must use method to make sure viewer dispatch works!
        # Utilise une méthode pour garantir que la vue est bien dispatchée.
        x, y = widget.ScreenToClient(wx.GetMousePosition())
        # Position actuelle de la souris.
        # Use wx.Point because CustomTreeCtrl assumes a wx.Point instance:
        columnIndex = widget.HitTest(wx.Point(x, y))[2]
        # Détermine la colonne à partir de la position de la souris.

        # Corrige un problème où -1 est retourné parfois pour la première colonne :
        # The TreeListCtrl returns -1 for the first column sometimes,
        # don't understand why. Work around as follows:
        if columnIndex == -1:
            columnIndex = 0
        return self.viewer.isHideableColumn(columnIndex)


class ViewColumn(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour afficher ou masquer une colonne spécifique dans la visionneuse.

    Cette commande contrôle la visibilité d'une colonne unique en fonction du nom de la colonne et de son état actuel (affiché ou masqué).
    """
    def isSettingChecked(self) -> bool:
        """
        Vérifie si la colonne est actuellement visible.

        Returns:
            bool : True si la colonne est visible, sinon False.
        """
        return self.viewer.isVisibleColumnByName(self.setting)

    def doCommand(self, event):
        """
        Exécute la commande pour afficher ou masquer la colonne en fonction de l'état du menu.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.showColumnByName(self.setting, self._isMenuItemChecked(event))


class ViewColumns(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour afficher ou masquer un groupe de colonnes dans la visionneuse.

    Cette commande contrôle la visibilité de plusieurs colonnes à la fois en fonction de leur nom.
    """
    def isSettingChecked(self) -> bool:
        """
        Vérifie si toutes les colonnes du groupe sont actuellement visibles.

        Returns:
            bool : True si toutes les colonnes sont visibles, sinon False.
        """
        for columnName in self.setting:
            if not self.viewer.isVisibleColumnByName(columnName):
                return False
        return True

    def doCommand(self, event):
        """
        Exécute la commande pour afficher ou masquer les colonnes en fonction de l'état du menu.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        show = self._isMenuItemChecked(event)
        for columnName in self.setting:
            self.viewer.showColumnByName(columnName, show)


class ViewExpandAll(mixin_uicommand.NeedsTreeViewerMixin, ViewerCommand):
    """
    Action pour étendre tous les éléments dans une visionneuse arborescente.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour étendre tous les éléments.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Expand all items\tShift+Ctrl+E"),
            helpText=help.viewExpandAll,
            *args,
            **kwargs
        )

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement s'il y a des éléments extensibles.
        """
        return super().enabled(event) and self.viewer.isAnyItemExpandable()

    def doCommand(self, event):
        """
        Étend tous les éléments dans la visionneuse.
        """
        self.viewer.expandAll()


class ViewCollapseAll(mixin_uicommand.NeedsTreeViewerMixin, ViewerCommand):
    """
    Action pour réduire tous les éléments dans une visionneuse arborescente.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour réduire tous les éléments.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Collapse all items\tShift+Ctrl+C"),
            helpText=help.viewCollapseAll,
            *args,
            **kwargs
        )

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement s'il y a des éléments réductibles.
        """
        return super().enabled(event) and self.viewer.isAnyItemCollapsable()

    def doCommand(self, event):
        """
        Réduit tous les éléments dans la visionneuse.
        """
        self.viewer.collapseAll()


class ViewerSortByCommand(ViewerCommand, settings_uicommand.UIRadioCommand):
    """
    Action pour trier la visionneuse par une colonne spécifique.

    Méthodes :
        isSettingChecked() : Vérifie si la visionneuse est triée par la colonne spécifiée.
        doCommand(event) : Trie la visionneuse par la colonne spécifiée.
    """
    def isSettingChecked(self) -> bool:
        """
        Vérifie si la visionneuse est triée par la colonne spécifiée.

        Returns:
            bool : True si la visionneuse est triée par cette colonne, sinon False.
        """
        return self.viewer.isSortedBy(self.value)

    def doCommand(self, event):
        """
        Exécute la commande pour trier la visionneuse par la colonne spécifiée.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.sortBy(self.value)


class ViewerSortOrderCommand(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour définir l'ordre de tri de la visionneuse (ascendant ou descendant).

    Méthodes :
        isSettingChecked() : Vérifie si l'ordre de tri est ascendant.
        doCommand(event) : Change l'ordre de tri en fonction de l'état du menu.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Ascending"),
            helpText=_("Sort ascending (checked) or descending (unchecked)"),
            *args,
            **kwargs
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si l'ordre de tri est ascendant.

        Returns:
            bool : True si l'ordre est ascendant, sinon False.
        """
        return self.viewer.isSortOrderAscending()

    def doCommand(self, event):
        """
        Exécute la commande pour changer l'ordre de tri.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.setSortOrderAscending(self._isMenuItemChecked(event))


class ViewerSortCaseSensitive(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour définir si le tri est sensible à la casse.

    Méthodes :
        isSettingChecked() : Vérifie si le tri est sensible à la casse.
        doCommand(event) : Change la sensibilité à la casse du tri.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Sort &case sensitive"),
            helpText=_(
                "When comparing text, sorting is case sensitive "
                "(checked) or insensitive (unchecked)"
            ),
            *args,
            **kwargs
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si le tri est sensible à la casse.

        Returns:
            bool : True si le tri est sensible à la casse, sinon False.
        """
        return self.viewer.isSortCaseSensitive()

    def doCommand(self, event):
        """
        Exécute la commande pour activer ou désactiver la sensibilité à la casse du tri.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.setSortCaseSensitive(self._isMenuItemChecked(event))


class ViewerSortByTaskStatusFirst(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour trier les tâches par statut (actif/inactif/terminé) en priorité.

    Méthodes :
        isSettingChecked() : Vérifie si le tri est effectué d'abord par statut.
        doCommand(event) : Change la priorité de tri par statut.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Sort by status &first"),
            helpText=_("Sort tasks by status (active/inactive/completed) " "first"),
            *args,
            **kwargs
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si les tâches sont triées d'abord par statut.

        Returns:
            bool : True si les tâches sont triées par statut en premier, sinon False.
        """
        return self.viewer.isSortByTaskStatusFirst()

    def doCommand(self, event):
        """
        Exécute la commande pour trier les tâches en premier par leur statut.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.setSortByTaskStatusFirst(self._isMenuItemChecked(event))


class ViewerHideTasks(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour masquer les tâches en fonction de leur statut.

    Méthodes :
        isSettingChecked() : Vérifie si les tâches avec un certain statut sont masquées.
        doCommand(event) : Masque ou affiche les tâches en fonction de leur statut.
    """
    def __init__(self, taskStatus, *args, **kwargs):
        """
        Initialise la commande avec le statut des tâches à masquer ou afficher.

        Args:
            taskStatus : Le statut des tâches (actif/inactif/terminé).
        """
        self.__taskStatus = taskStatus
        super().__init__(
            menuText=taskStatus.hideMenuText,
            helpText=taskStatus.hideHelpText,
            bitmap=taskStatus.getHideBitmap(kwargs["settings"]),
            *args,
            **kwargs
        )

    def uniqueName(self) -> str:
        """
        Retourne un nom unique pour cette commande en fonction du statut des tâches.
        """
        return super().uniqueName() + "_" + str(self.__taskStatus)

    def isSettingChecked(self) -> bool:
        """
        Vérifie si les tâches avec le statut spécifié sont masquées.

        Returns :
            bool : True si ces tâches sont masquées, sinon False.
        """
        return self.viewer.isHidingTaskStatus(self.__taskStatus)

    def doCommand(self, event):
        """
        Exécute la commande pour masquer ou afficher les tâches avec le statut spécifié.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        if wx.GetKeyState(wx.WXK_SHIFT):
            self.viewer.showOnlyTaskStatus(self.__taskStatus)
        else:
            self.viewer.hideTaskStatus(
                self.__taskStatus, self._isMenuItemChecked(event)
            )


class ViewerHideCompositeTasks(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour masquer les tâches composites (ayant des sous-tâches).

    Méthodes :
        isSettingChecked() : Vérifie si les tâches composites sont masquées.
        doCommand(event) : Masque ou affiche les tâches composites.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour masquer les tâches composites.

        Args:
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Hide c&omposite tasks"),
            helpText=_("Show/hide tasks with subtasks in list mode"),
            *args,
            **kwargs
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si les tâches composites sont actuellement masquées.

        Returns:
            bool : True si les tâches composites sont masquées, sinon False.
        """
        return self.viewer.isHidingCompositeTasks()

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement si la visionneuse n'est pas en mode arborescence.

        Returns:
            bool : True si la visionneuse est en mode liste, sinon False.
        """
        return not self.viewer.isTreeViewer()

    def doCommand(self, event):
        """
        Exécute la commande pour masquer ou afficher les tâches composites.

        Args:
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.hideCompositeTasks(self._isMenuItemChecked(event))


class Edit(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Commande pour modifier les éléments sélectionnés dans une visionneuse.

    Cette commande permet d'ouvrir un éditeur pour modifier l'élément sélectionné
    ou d'accepter les modifications dans un champ de texte en cours d'édition.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour éditer les éléments avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Edit...\tRETURN"),
            helpText=_("Edit the selected item(s)"),
            bitmap="edit",
            *args,
            **kwargs
        )

    def doCommand(self, event, show: bool = True):  # pylint: disable=W0221
        """
        Exécute la commande pour ouvrir un éditeur d'éléments ou accepter les modifications d'un champ de texte.

        Args :
            event (wx.Event) : L'événement déclencheur.
            show (bool) : Indique si l'éditeur doit être affiché.
        """
        windowWithFocus = wx.Window.FindFocus()
        editCtrl = self.findEditCtrl(windowWithFocus)
        if editCtrl:
            editCtrl.AcceptChanges()
            if editCtrl:
                editCtrl.Finish()
            return
        try:
            columnName = event.columnName
        except AttributeError:
            columnName = ""
        editor = self.viewer.editItemDialog(
            self.viewer.curselection(), self.bitmap, columnName
        )
        editor.Show(show)

    def enabled(self, event) -> bool:
        """
        Vérifie si la commande est activée, c'est-à-dire s'il y a un élément sélectionné ou un champ en cours d'édition.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.findEditCtrl(windowWithFocus):
            return True
        elif operating_system.isMac() and isinstance(windowWithFocus, wx.TextCtrl):
            return False
        else:
            return super().enabled(event)

    # @staticmethod
    def findEditCtrl(self, windowWithFocus):
        """
        Trouve le contrôle d'édition actif si disponible.

        Args :
            windowWithFocus (wx.Window) : La fenêtre actuellement active.

        Returns :
            wx.Window : Le contrôle d'édition si trouvé, sinon None.
        """
        while windowWithFocus:
            # if isinstance(windowWithFocus, thirdparty.hypertreelist.EditCtrl):
            if isinstance(windowWithFocus, hypertreelist.EditCtrl):
                break
            windowWithFocus = windowWithFocus.GetParent()
        return windowWithFocus


class EditTrackedTasks(TaskListCommand, settings_uicommand.SettingsCommand):
    """
    Modifier les tâches suivies.

    Cette commande permet de modifier les tâches actuellement suivies.

    Arguments :
        * aucun

    Paramètres :
        * aucun

    Retours :
        * une boîte de dialogue d'édition de tâche

    Exceptions :
        * aucune
    """
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Edit &tracked task...\tShift-Alt-T"),
            helpText=_("Edit the currently tracked task(s)"),
            bitmap="edit",
            *args,
            **kwargs
        )

    def doCommand(self, event, show: bool = True):
        """
        Ouvre la boîte de dialogue de modification de la tâche suivie.
        :param event:
        :param show:
        :return:
        """
        editTaskDialog = dialog.editor.TaskEditor(
            self.mainWindow(),
            self.taskList.tasksBeingTracked(),
            self.settings,
            self.taskList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
        )
        editTaskDialog.Show(show)
        return editTaskDialog  # for testing purposes

    def enabled(self, event):
        """
        Vérifie si les tâches sont suivies.

        :param event:
        :return:
        """
        return any(self.taskList.tasksBeingTracked())


class Delete(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Commande pour supprimer les éléments sélectionnés dans une visionneuse.

    Cette commande permet de supprimer les éléments sélectionnés ou de simuler
    une suppression de texte dans un champ de texte actif.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour supprimer les éléments avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Delete\tCtrl+DEL"),
            helpText=_("Delete the selected item(s)"),
            bitmap="delete",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        """
        Exécute la commande pour supprimer les éléments ou le texte sélectionné.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.windowIsTextCtrl(windowWithFocus):
            # Simulate Delete key press
            fromIndex, toIndex = windowWithFocus.GetSelection()
            if fromIndex == toIndex:
                pos = windowWithFocus.GetInsertionPoint()
                fromIndex, toIndex = pos, pos + 1
            windowWithFocus.Remove(fromIndex, toIndex)
        else:
            deleteCommand = self.viewer.deleteItemCommand()
            deleteCommand.do()

    def enabled(self, event) -> bool:
        """
        Vérifie si la commande est activée, c'est-à-dire si des éléments ou du texte peuvent être supprimés.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.windowIsTextCtrl(windowWithFocus):
            return True
        else:
            return super().enabled(event)

    @staticmethod
    def windowIsTextCtrl(window) -> bool:
        """
        Vérifie si la fenêtre active est un contrôle de texte.

        Args :
            window (wx.Window) : La fenêtre active.

        Returns :
            bool : True si la fenêtre est un contrôle de texte, sinon False.
        """
        return isinstance(window, wx.TextCtrl) or isinstance(
            window, hypertreelist.EditCtrl
        )


class TaskNew(TaskListCommand, settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        self.taskKeywords = kwargs.pop("taskKeywords", dict())
        taskList = kwargs["taskList"]
        if "menuText" not in kwargs:  # Provide for subclassing
            kwargs["menuText"] = taskList.newItemMenuText
            kwargs["helpText"] = taskList.newItemHelpText
        super().__init__(bitmap="new", *args, **kwargs)

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        kwargs = self.taskKeywords.copy()
        if self.__shouldPresetPlannedStartDateTime():
            kwargs["plannedStartDateTime"] = task.Task.suggestedPlannedStartDateTime()
        if self.__shouldPresetDueDateTime():
            kwargs["dueDateTime"] = task.Task.suggestedDueDateTime()
        if self.__shouldPresetActualStartDateTime():
            kwargs["actualStartDateTime"] = task.Task.suggestedActualStartDateTime()
        if self.__shouldPresetCompletionDateTime():
            kwargs["completionDateTime"] = task.Task.suggestedCompletionDateTime()
        if self.__shouldPresetReminderDateTime():
            kwargs["reminder"] = task.Task.suggestedReminderDateTime()
        newTaskCommand = command.NewTaskCommand(
            self.taskList,
            categories=self.categoriesForTheNewTask(),
            prerequisites=self.prerequisitesForTheNewTask(),
            dependencies=self.dependenciesForTheNewTask(),
            **kwargs
        )
        newTaskCommand.do()
        newTaskDialog = dialog.editor.TaskEditor(
            self.mainWindow(),
            newTaskCommand.items,
            self.settings,
            self.taskList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
            items_are_new=True,
        )
        newTaskDialog.Show(show)
        return newTaskDialog  # for testing purposes

    def categoriesForTheNewTask(self):
        return self.mainWindow().taskFile.categories().filteredCategories()

    def prerequisitesForTheNewTask(self):
        return []

    def dependenciesForTheNewTask(self):
        return []

    def __shouldPresetPlannedStartDateTime(self):
        return "plannedStartDateTime" not in self.taskKeywords and self.settings.get(
            "view", "defaultplannedstartdatetime"
        ).startswith("preset")

    def __shouldPresetDueDateTime(self):
        return "dueDateTime" not in self.taskKeywords and self.settings.get(
            "view", "defaultduedatetime"
        ).startswith("preset")

    def __shouldPresetActualStartDateTime(self):
        return "actualStartDateTime" not in self.taskKeywords and self.settings.get(
            "view", "defaultactualstartdatetime"
        ).startswith("preset")

    def __shouldPresetCompletionDateTime(self):
        return "completionDateTime" not in self.taskKeywords and self.settings.get(
            "view", "defaultcompletiondatetime"
        ).startswith("preset")

    def __shouldPresetReminderDateTime(self):
        return "reminder" not in self.taskKeywords and self.settings.get(
            "view", "defaultreminderdatetime"
        ).startswith("preset")


class TaskNewFromTemplate(TaskNew):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__filename = filename
        templateTask = self.__readTemplate()
        self.menuText = "&" + templateTask.subject().replace(
            "&", "&&"
        )  # pylint: disable=E1103

    def __readTemplate(self):
        # file -> open !!!? import io.open
        return persistence.TemplateXMLReader(open(self.__filename, "rU")).read()

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        # The task template is read every time because it's the
        # TemplateXMLReader that evaluates dynamic values (Now()
        # should be evaluated at task creation for instance).
        templateTask = self.__readTemplate()
        kwargs = templateTask.__getcopystate__()  # pylint: disable=E1103
        kwargs["categories"] = self.categoriesForTheNewTask()
        newTaskCommand = command.NewTaskCommand(self.taskList, **kwargs)
        newTaskCommand.do()
        # pylint: disable=W0142
        newTaskDialog = dialog.editor.TaskEditor(
            self.mainWindow(),
            newTaskCommand.items,
            self.settings,
            self.taskList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
            items_are_new=True,
        )
        newTaskDialog.Show(show)
        return newTaskDialog  # for testing purposes


class TaskNewFromTemplateButton(
    mixin_uicommand.PopupButtonMixin,
    TaskListCommand,
    settings_uicommand.SettingsCommand,
):
    def createPopupMenu(self):
        from taskcoachlib.gui import menu

        return menu.TaskTemplateMenu(self.mainWindow(), self.taskList, self.settings)

    def getMenuText(self):
        return _("New task from &template")

    def getHelpText(self):
        return _("Create a new task from a template")


class NewTaskWithSelectedCategories(TaskNew, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("New task with selected &categories..."),
            helpText=_("Insert a new task with the selected categories checked"),
            *args,
            **kwargs
        )

    def categoriesForTheNewTask(self):
        return self.viewer.curselection()


class NewTaskWithSelectedTasksAsPrerequisites(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskNew, ViewerCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("New task with selected tasks as &prerequisites..."),
            helpText=_(
                "Insert a new task with the selected tasks as prerequisite tasks"
            ),
            *args,
            **kwargs
        )

    def prerequisitesForTheNewTask(self):
        return self.viewer.curselection()


class NewTaskWithSelectedTasksAsDependencies(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskNew, ViewerCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("New task with selected tasks as &dependents..."),
            helpText=_("Insert a new task with the selected tasks as dependent tasks"),
            *args,
            **kwargs
        )

    def dependenciesForTheNewTask(self):
        return self.viewer.curselection()


class NewSubItem(mixin_uicommand.NeedsOneSelectedCompositeItemMixin, ViewerCommand):
    shortcut = "\tCtrl+INS" if operating_system.isWindows() else "\tShift+Ctrl+N"
    # defaultMenuText = _('New &subitem...') + shortcut
    # TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
    defaultMenuText = _("New &subitem...") + shortcut
    labels = {
        task.Task: _("New &subtask..."),
        note.Note: _("New &subnote..."),
        category.Category: _("New &subcategory..."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.defaultMenuText,
            helpText=_("Insert a new subitem of the selected item"),
            bitmap="newsub",
            *args,
            **kwargs
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        self.viewer.newSubItemDialog(bitmap=self.bitmap).Show(show)

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        self.updateMenuText(self.__menuText())

    def __menuText(self):
        for class_ in self.labels:
            if self.viewer.curselectionIsInstanceOf(class_):
                return self.labels[class_] + self.shortcut
        return self.defaultMenuText


class TaskMarkActive(
    mixin_uicommand.NeedsSelectedTasksMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap=task.active.getBitmap(kwargs["settings"]),
            menuText=_("Mark task &active\tAlt+RETURN"),
            helpText=_("Mark the selected task(s) active"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        command.MarkActiveCommand(
            self.viewer.presentation(), self.viewer.curselection()
        ).do()

    def enabled(self, event):
        def canBeMarkedActive(aTask):
            return aTask.actualStartDateTime() > date.Now() or aTask.completed()

        return super().enabled(event) and any(
            [canBeMarkedActive(task) for task in self.viewer.curselection()]
        )


class TaskMarkInactive(
    mixin_uicommand.NeedsSelectedTasksMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap=task.inactive.getBitmap(kwargs["settings"]),
            menuText=_("Mark task &inactive\tCtrl+Alt+RETURN"),
            helpText=_("Mark the selected task(s) inactive"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        command.MarkInactiveCommand(
            self.viewer.presentation(), self.viewer.curselection()
        ).do()

    def enabled(self, event):
        def canBeMarkedInactive(aTask):
            return not aTask.inactive() and not aTask.late()

        return super().enabled(event) and any(
            [canBeMarkedInactive(task) for task in self.viewer.curselection()]
        )


class TaskMarkCompleted(
    mixin_uicommand.NeedsSelectedTasksMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap=task.completed.getBitmap(kwargs["settings"]),
            menuText=_("Mark task &completed\tCtrl+RETURN"),
            helpText=_("Mark the selected task(s) completed"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        markCompletedCommand = command.MarkCompletedCommand(
            self.viewer.presentation(), self.viewer.curselection()
        )
        markCompletedCommand.do()

    def enabled(self, event):
        def canBeMarkedCompleted(task):
            return not task.completed()

        return super().enabled(event) and any(
            [canBeMarkedCompleted(task) for task in self.viewer.curselection()]
        )


class TaskMaxPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Maximize priority\tShift+Ctrl+I"),
            helpText=help.taskMaxPriority,
            bitmap="maxpriority",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        maxPriority = command.MaxPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        maxPriority.do()


class TaskMinPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Minimize priority\tShift+Ctrl+D"),
            helpText=help.taskMinPriority,
            bitmap="minpriority",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        minPriority = command.MinPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        minPriority.do()


class TaskIncPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Increase priority\tCtrl+I"),
            helpText=help.taskIncreasePriority,
            bitmap="incpriority",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        incPriority = command.IncPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        incPriority.do()


class TaskDecPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Decrease priority\tCtrl+D"),
            helpText=help.taskDecreasePriority,
            bitmap="decpriority",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        decPriority = command.DecPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        decPriority.do()


class DragAndDropCommand(ViewerCommand):
    def onCommandActivate(
        self, dropItem, dragItems, part, column
    ):  # pylint: disable=W0221
        """Override onCommandActivate to be able to accept two items instead
        of one event."""
        self.doCommand(
            dropItem,
            dragItems,
            part,
            None if column == -1 else self.viewer.visibleColumns()[column],
        )

    def doCommand(self, dropItem, dragItems, part, column):  # pylint: disable=W0221
        dragAndDropCommand = self.createCommand(
            dropItem=dropItem,
            dragItems=dragItems,
            part=part,
            column=column,
            isTree=self.viewer.isTreeViewer(),
        )
        if dragAndDropCommand.canDo():
            dragAndDropCommand.do()
            return dragAndDropCommand

    def createCommand(self, dropItem, dragItems, part, isTree):
        raise NotImplementedError  # pragma: no cover


class OrderingDragAndDropCommand(DragAndDropCommand):
    def doCommand(self, dropItem, dragItems, part, column):
        command = super().doCommand(
            dropItem, dragItems, part, column
        )  # command à renommer !
        if command is not None and command.isOrdering():
            sortCommand = ViewerSortByCommand(viewer=self.viewer, value="ordering")
            sortCommand.doCommand(None)


class TaskDragAndDrop(OrderingDragAndDropCommand, TaskListCommand):
    def createCommand(self, dropItem, dragItems, part, column, isTree):
        return command.DragAndDropTaskCommand(
            self.taskList,
            dragItems,
            drop=[dropItem],
            part=part,
            column=column,
            isTree=isTree,
        )


class ToggleCategory(mixin_uicommand.NeedsSelectedCategorizableMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop("category")
        subject = self.category.subject()
        # Would like to use wx.ITEM_RADIO for mutually exclusive categories, but
        # a menu with radio items always has to have at least of the items
        # checked, while we allow none of the mutually exclusive categories to
        # be checked. Dynamically changing between wx.ITEM_CHECK and
        # wx.ITEM_RADIO would be a work-around in theory, using wx.ITEM_CHECK
        # when none of the mutually exclusive categories is checked and
        # wx.ITEM_RADIO otherwise, but dynamically changing the type of menu
        # items isn't possible. Hence, we use wx.ITEM_CHECK, even for mutual
        # exclusive categories.
        kind = wx.ITEM_CHECK
        super().__init__(
            menuText="&" + subject.replace("&", "&&"),
            helpText=_("Toggle %s") % subject,
            kind=kind,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        check = command.ToggleCategoryCommand(
            category=self.category, items=self.viewer.curselection()
        )
        check.do()

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        if self.enabled(event):
            check = self.__all_selected_items_are_in_category()
            for menuItem in self.menuItems:
                menuItem.Check(check)

    def __all_selected_items_are_in_category(self):
        selected_items_in_category = [
            item
            for item in self.viewer.curselection()
            if self.category in item.categories()
        ]
        return selected_items_in_category == self.viewer.curselection()

    def enabled(self, event):
        viewerHasSelection = super().enabled(event)
        if not viewerHasSelection or self.viewer.isShowingCategories():
            return False
        mutual_exclusive_ancestors = [
            ancestor
            for ancestor in self.category.ancestors()
            if ancestor.isMutualExclusive()
        ]
        for categorizable in self.viewer.curselection():
            for ancestor in mutual_exclusive_ancestors:
                if ancestor not in categorizable.categories():
                    return False  # Not all mutually exclusive ancestors are checked
        return True  # All mutually exclusive ancestors are checked


class Mail(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    rx_attr = re.compile(r"(cc|to)=(.*)")

    def __init__(self, *args, **kwargs):
        menuText = (
            _("&Mail...\tShift-Ctrl-M")
            if operating_system.isMac()
            else _("&Mail...\tCtrl-M")
        )
        super().__init__(
            menuText=menuText,
            helpText=help.mailItem,
            bitmap="envelope_icon",
            *args,
            **kwargs
        )

    def doCommand(
        self, event, mail=sendMail, showerror=wx.MessageBox
    ):  # pylint: disable=W0221
        items = self.viewer.curselection()
        subject = self.subject(items)
        body = self.body(items)
        to = self.to(items)
        cc = self.cc(items)
        self.mail(to, cc, subject, body, mail, showerror)

    # @staticmethod
    def subject(self, items):
        assert items
        if len(items) > 2:
            return _("Several things")
        elif len(items) == 2:
            subjects = [item.subject(recursive=True) for item in items]
            return " ".join([subjects[0], _("and"), subjects[1]])
        else:
            return items[0].subject(recursive=True)

    def body(self, items):
        if len(items) > 1:
            bodyLines = []
            for item in items:
                bodyLines.extend(self.itemToLines(item))
        else:
            bodyLines = items[0].description().splitlines()
        return "\r\n".join(bodyLines)

    def to(self, items):
        return self._mailAttr("to", items)

    def cc(self, items):
        return self._mailAttr("cc", items)

    # @staticmethod
    def _mailAttr(self, name, items):
        sets = []
        for item in items:
            sets.append(
                set(
                    [
                        value[len(name) + 1 :]
                        for value in item.customAttributes("mailto")
                        if value.startswith("%s=" % name)
                    ]
                )
            )
        return reduce(operator.or_, sets)

    # @staticmethod
    def itemToLines(self, item):
        lines = []
        subject = item.subject(recursive=True)
        lines.append(subject)
        if item.description():
            lines.extend(item.description().splitlines())
            lines.extend("\r\n")
        return lines

    # @staticmethod
    def mail(self, to, cc, subject, body, mail, showerror):
        try:
            mail(to, subject, body, cc=cc)
        except:
            # Try again with a dummy recipient:
            try:
                mail("recipient@domain.com", subject, body)
            except Exception as reason:  # pylint: disable=W0703
                showerror(
                    _("Cannot send email:\n%s") % ExceptionAsUnicode(reason),
                    caption=_("%s mail error") % meta.name,
                    style=wx.ICON_ERROR,
                )


class AddNote(
    mixin_uicommand.NeedsSelectedNoteOwnersMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Add &note...\tCtrl+B"),
            helpText=help.addNote,
            bitmap="note_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        addNoteCommand = command.AddNoteCommand(
            self.viewer.presentation(), self.viewer.curselection()
        )
        addNoteCommand.do()
        editDialog = dialog.editor.NoteEditor(
            self.mainWindow(),
            addNoteCommand.items,
            self.settings,
            self.viewer.presentation(),
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
        )
        editDialog.Show(show)
        return editDialog  # for testing purposes


class OpenAllNotes(
    mixin_uicommand.NeedsSelectedNoteOwnersMixinWithNotes,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Open all notes...\tShift+Ctrl+B"),
            helpText=help.openAllNotes,
            bitmap="edit",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        for item in self.viewer.curselection():
            for note in item.notes():
                editDialog = dialog.editor.NoteEditor(
                    self.mainWindow(),
                    [note],
                    self.settings,
                    self.viewer.presentation(),
                    self.mainWindow().taskFile,
                    bitmap=self.bitmap,
                )
                editDialog.Show()


class EffortNew(
    mixin_uicommand.NeedsAtLeastOneTaskMixin,
    ViewerCommand,
    EffortListCommand,
    TaskListCommand,
    settings_uicommand.SettingsCommand,
):
    def __init__(self, *args, **kwargs):
        effortList = kwargs["effortList"]
        super().__init__(
            bitmap="new",
            menuText=effortList.newItemMenuText,
            helpText=effortList.newItemHelpText,
            *args,
            **kwargs
        )

    def doCommand(self, event, show=True):
        if self.viewer and self.viewer.isShowingTasks() and self.viewer.curselection():
            selectedTasks = self.viewer.curselection()
        elif self.viewer and self.viewer.isShowingEffort():
            selectedEfforts = self.viewer.curselection()
            if selectedEfforts:
                selectedTasks = [selectedEfforts[0].task()]
            else:
                selectedTasks = [self.firstTask(self.viewer.domainObjectsToView())]
        else:
            selectedTasks = [self.firstTask(self.taskList)]

        newEffortCommand = command.NewEffortCommand(self.effortList, selectedTasks)
        newEffortCommand.do()
        newEffortDialog = dialog.editor.EffortEditor(
            self.mainWindow(),
            newEffortCommand.items,
            self.settings,
            self.effortList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
        )
        if show:
            newEffortDialog.Show()
        return newEffortDialog

    @staticmethod
    def firstTask(tasks):
        subjectDecoratedTasks = [
            (eachTask.subject(recursive=True), eachTask) for eachTask in tasks
        ]
        subjectDecoratedTasks.sort()
        return subjectDecoratedTasks[0][1]


class EffortStart(
    mixin_uicommand.NeedsSelectedTasksMixin, ViewerCommand, TaskListCommand
):
    """UICommand to start tracking effort for the selected task(s)."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="clock_icon",
            menuText=_("&Start tracking effort\tCtrl-T"),
            helpText=help.effortStart,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        start = command.StartEffortCommand(self.taskList, self.viewer.curselection())
        start.do()

    def enabled(self, event):
        return super().enabled(event) and any(
            not task.completed() and not task.isBeingTracked()
            for task in self.viewer.curselection()
        )


class EffortStartForEffort(
    mixin_uicommand.NeedsSelectedEffortMixin, ViewerCommand, TaskListCommand
):
    """UICommand to start tracking for the task(s) of selected effort(s)."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="clock_icon",
            menuText=_("&Start tracking effort"),
            helpText=_(
                "Start tracking effort for the task(s) of the selected effort(s)"
            ),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        start = command.StartEffortCommand(self.taskList, self.trackableTasks())
        start.do()

    def enabled(self, event):
        return super().enabled(event) and self.trackableTasks()

    def trackableTasks(self):
        tasks = set([effort.task() for effort in self.viewer.curselection()])
        return [
            task for task in tasks if not task.completed() and not task.isBeingTracked()
        ]


class EffortStartForTask(TaskListCommand):
    """UICommand to start tracking for a specific task. This command can
    be used to build a menu with separate menu items for all tasks.
    See gui.menu.StartEffortForTaskMenu."""

    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop("task")
        subject = self.task.subject() or _("(No subject)")
        super().__init__(
            bitmap=self.task.icon(recursive=True),
            menuText="&" + subject.replace("&", "&&"),
            helpText=_("Start tracking effort for %s") % subject,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        start = command.StartEffortCommand(self.taskList, [self.task])
        start.do()

    def enabled(self, event):
        return not self.task.isBeingTracked() and not self.task.completed()


class EffortStartButton(mixin_uicommand.PopupButtonMixin, TaskListCommand):
    def __init__(self, *args, **kwargs):
        kwargs["taskList"] = base.filter.DeletedFilter(kwargs["taskList"])
        super().__init__(
            bitmap="clock_menu_icon",
            menuText=_("&Start tracking effort"),
            helpText=_("Select a task via the menu and start tracking effort for it"),
            *args,
            **kwargs
        )

    def createPopupMenu(self):
        from taskcoachlib.gui import menu

        return menu.StartEffortForTaskMenu(self.mainWindow(), self.taskList)

    def enabled(self, event):
        return any(not task.completed() for task in self.taskList)


class EffortStop(EffortListCommand, TaskListCommand, ViewerCommand):
    defaultMenuText = _("Stop tracking or resume tracking effort\tShift+Ctrl+T")
    defaultHelpText = help.effortStopOrResume
    stopMenuText = _("St&op tracking %s\tShift+Ctrl+T")
    stopHelpText = _("Stop tracking effort for the active task(s)")
    resumeMenuText = _("&Resume tracking %s\tShift+Ctrl+T")
    resumeHelpText = _("Resume tracking effort for the last tracked task")

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="clock_resume_icon",
            bitmap2="clock_stop_icon",
            menuText=self.defaultMenuText,
            helpText=self.defaultHelpText,
            kind=wx.ITEM_CHECK,
            *args,
            **kwargs
        )
        self.__tracker = effort.EffortListTracker(self.effortList)
        for subtype in ["", ".added", ".removed"]:
            self.__tracker.subscribe(
                self.__onEffortsChanged, "effortlisttracker%s" % subtype
            )
        self.__currentBitmap = None  # Don't know yet what our bitmap is

    def __onEffortsChanged(self, efforts):
        self.updateUI()

    def efforts(self):
        selectedEfforts = set()
        for item in self.viewer.curselection():
            if isinstance(item, task.Task):
                selectedEfforts |= set(item.efforts())
            elif isinstance(item, effort.Effort):
                selectedEfforts.add(item)
        selectedEfforts &= set(self.__tracker.trackedEfforts())
        return selectedEfforts if selectedEfforts else self.__tracker.trackedEfforts()

    def doCommand(self, event=None):
        efforts = self.efforts()
        if efforts:
            # Stop the tracked effort(s)
            effortCommand = command.StopEffortCommand(self.effortList, efforts)
        else:
            # Resume tracking the last task
            effortCommand = command.StartEffortCommand(
                self.taskList, [self.mostRecentTrackedTask()]
            )
        effortCommand.do()

    def enabled(self, event=None):
        # If there are tracked efforts this command will stop them. If there are
        # untracked efforts this command will resume them. Otherwise this
        # command is disabled.
        return self.anyTrackedEfforts() or self.anyStoppedEfforts()

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        self.updateUI()

    def updateUI(self):
        paused = self.anyStoppedEfforts() and not self.anyTrackedEfforts()
        self.updateToolState(not paused)
        bitmapName = self.bitmap if paused else self.bitmap2
        menuText = self.getMenuText(paused)
        if (bitmapName != self.__currentBitmap) or bool(
            [item for item in self.menuItems if item.GetItemLabel() != menuText]
        ):
            self.__currentBitmap = bitmapName
            self.updateToolBitmap(bitmapName)
            self.updateToolHelp()
            self.updateMenuItems(paused)

    def updateToolState(self, paused):
        if not self.toolbar:
            return  # Toolbar is hidden
        if paused != self.toolbar.GetToolState(self.id):
            self.toolbar.ToggleTool(self.id, paused)

    def updateToolBitmap(self, bitmapName):
        if not self.toolbar:
            return  # Toolbar is hidden
        bitmap = wx.ArtProvider.GetBitmap(
            bitmapName, wx.ART_TOOLBAR, self.toolbar.GetToolBitmapSize()
        )
        # On wxGTK, changing the bitmap doesn't work when the tool is
        # disabled, so we first enable it if necessary:
        disable = False
        if not self.toolbar.GetToolEnabled(self.id):
            self.toolbar.EnableTool(self.id, True)
            disable = True
        self.toolbar.SetToolNormalBitmap(self.id, bitmap)
        if disable:
            self.toolbar.EnableTool(self.id, False)
        self.toolbar.Realize()

    def updateMenuItems(self, paused):
        menuText = self.getMenuText(paused)
        helpText = self.getHelpText(paused)
        for menuItem in self.menuItems:
            menuItem.Check(paused)
            menuItem.SetItemLabel(menuText)
            menuItem.SetHelp(helpText)

    def getMenuText(self, paused=None):  # pylint: disable=W0221
        if self.anyTrackedEfforts():
            trackedEfforts = list(self.efforts())
            subject = (
                _("multiple tasks")
                if len(trackedEfforts) > 1
                else trackedEfforts[0].task().subject()
            )
            return self.stopMenuText % self.trimmedSubject(subject)
        if paused is None:
            paused = self.anyStoppedEfforts()
        if paused:
            return self.resumeMenuText % self.trimmedSubject(
                self.mostRecentTrackedTask().subject()
            )
        else:
            return self.defaultMenuText

    def getHelpText(self, paused=None):  # pylint: disable=W0221
        if self.anyTrackedEfforts():
            return self.stopHelpText
        if paused is None:
            paused = self.anyStoppedEfforts()
        return self.resumeHelpText if paused else self.defaultHelpText

    def anyStoppedEfforts(self):
        return bool(self.effortList.maxDateTime())

    def anyTrackedEfforts(self):
        return bool(self.efforts())

    def mostRecentTrackedTask(self):
        stopTimes = [
            (effort.getStop(), effort)
            for effort in self.effortList
            if effort.getStop() is not None
        ]
        return max(stopTimes)[1].task()

    @staticmethod
    def trimmedSubject(subject, maxLength=35, postFix="..."):
        trim = len(subject) > maxLength
        return subject[: maxLength - len(postFix)] + postFix if trim else subject


class CategoryNew(CategoriesCommand, settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="new",
            menuText=_("New category...\tCtrl-G"),
            helpText=help.categoryNew,
            *args,
            **kwargs
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        newCategoryCommand = command.NewCategoryCommand(self.categories)
        newCategoryCommand.do()
        taskFile = self.mainWindow().taskFile
        newCategoryDialog = dialog.editor.CategoryEditor(
            self.mainWindow(),
            newCategoryCommand.items,
            self.settings,
            taskFile.categories(),
            taskFile,
            bitmap=self.bitmap,
        )
        newCategoryDialog.Show(show)


class CategoryDragAndDrop(OrderingDragAndDropCommand, CategoriesCommand):
    def createCommand(self, dropItem, dragItems, part, column, isTree):
        return command.DragAndDropCategoryCommand(
            self.categories,
            dragItems,
            drop=[dropItem],
            part=part,
            column=column,
            isTree=isTree,
        )


class NoteNew(NotesCommand, settings_uicommand.SettingsCommand, ViewerCommand):
    menuText = _("New note...\tCtrl-J")
    helpText = help.noteNew

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap="new",
            *args,
            **kwargs
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        if self.viewer and self.viewer.isShowingNotes():
            noteDialog = self.viewer.newItemDialog(bitmap=self.bitmap)
        else:
            newNoteCommand = command.NewNoteCommand(
                self.notes, categories=self.categoriesForTheNewNote()
            )
            newNoteCommand.do()
            noteDialog = dialog.editor.NoteEditor(
                self.mainWindow(),
                newNoteCommand.items,
                self.settings,
                self.notes,
                self.mainWindow().taskFile,
                bitmap=self.bitmap,
            )
        noteDialog.Show(show)
        return noteDialog  # for testing purposes

    def categoriesForTheNewNote(self):
        return self.mainWindow().taskFile.categories().filteredCategories()


class NewNoteWithSelectedCategories(NoteNew, ViewerCommand):
    menuText = _("New &note with selected categories...")
    helpText = _("Insert a new note with the selected categories checked")

    def categoriesForTheNewNote(self):
        return self.viewer.curselection()


class NoteDragAndDrop(OrderingDragAndDropCommand, NotesCommand):
    def createCommand(self, dropItem, dragItems, part, column, isTree):
        return command.DragAndDropNoteCommand(
            self.notes,
            dragItems,
            drop=[dropItem],
            part=part,
            column=column,
            isTree=isTree,
        )


class AttachmentNew(
    AttachmentsCommand, ViewerCommand, settings_uicommand.SettingsCommand
):
    def __init__(self, *args, **kwargs):
        attachments = kwargs["attachments"]
        if "menuText" not in kwargs:
            kwargs["menuText"] = attachments.newItemMenuText
            kwargs["helpText"] = attachments.newItemHelpText
        super().__init__(bitmap="new", *args, **kwargs)

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        attachmentDialog = self.viewer.newItemDialog(bitmap=self.bitmap)
        attachmentDialog.Show(show)
        return attachmentDialog  # for testing purposes


class AddAttachment(
    mixin_uicommand.NeedsSelectedAttachmentOwnersMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Add attachment...\tShift-Ctrl-A"),
            helpText=help.addAttachment,
            bitmap="paperclip_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        filename = widgets.AttachmentSelector()
        if not filename:
            return
        attachmentBase = self.settings.get("file", "attachmentbase")
        if attachmentBase:
            filename = attachment.getRelativePath(filename, attachmentBase)
        addAttachmentCommand = command.AddAttachmentCommand(
            self.viewer.presentation(),
            self.viewer.curselection(),
            attachments=[attachment.FileAttachment(filename)],
        )
        addAttachmentCommand.do()


def openAttachments(attachments, settings, showerror):
    attachmentBase = settings.get("file", "attachmentbase")
    for eachAttachment in attachments:
        try:
            eachAttachment.open(attachmentBase)
        except Exception as instance:  # pylint: disable=W0703
            showerror(
                render.exception(Exception, instance),
                caption=_("Error opening attachment"),
                style=wx.ICON_ERROR,
            )


class AttachmentOpen(
    mixin_uicommand.NeedsSelectedAttachmentsMixin,
    ViewerCommand,
    AttachmentsCommand,
    settings_uicommand.SettingsCommand,
):
    def __init__(self, *args, **kwargs):
        attachments = kwargs["attachments"]
        super().__init__(
            bitmap="fileopen",
            menuText=attachments.openItemMenuText,
            helpText=attachments.openItemHelpText,
            *args,
            **kwargs
        )

    def doCommand(self, event, showerror=wx.MessageBox):  # pylint: disable=W0221
        openAttachments(self.viewer.curselection(), self.settings, showerror)


class OpenAllAttachments(
    mixin_uicommand.NeedsSelectionWithAttachmentsMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Open all attachments...\tShift+Ctrl+O"),
            helpText=help.openAllAttachments,
            bitmap="paperclip_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event, showerror=wx.MessageBox):  # pylint: disable=W0221
        allAttachments = []
        for item in self.viewer.curselection():
            allAttachments.extend(item.attachments())
        openAttachments(allAttachments, self.settings, showerror)


class DialogCommand(base_uicommand.UICommand):
    def __init__(self, *args, **kwargs):
        self._dialogTitle = kwargs.pop("dialogTitle")
        self._dialogText = kwargs.pop("dialogText")
        self._direction = kwargs.pop("direction", None)
        self.closed = True
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        self.closed = False
        # pylint: disable=W0201
        self.dialog = widgets.HTMLDialog(
            self._dialogTitle,
            self._dialogText,
            bitmap=self.bitmap,
            direction=self._direction,
        )
        for event in wx.EVT_CLOSE, wx.EVT_BUTTON:
            self.dialog.Bind(event, self.onClose)
        self.dialog.Show()

    def onClose(self, event):
        self.closed = True
        self.dialog.Destroy()
        event.Skip()

    def enabled(self, event):
        return self.closed


class Help(DialogCommand):
    def __init__(self, *args, **kwargs):
        if operating_system.isMac():
            # Use default keyboard shortcut for Mac OS X:
            menuText = _("&Help contents\tCtrl+?")
        else:
            # Use a letter, because 'Ctrl-?' doesn't work on Windows:
            menuText = _("&Help contents\tCtrl+H")
        super().__init__(
            menuText=menuText,
            helpText=help.help,
            bitmap="led_blue_questionmark_icon",
            dialogTitle=_("Help"),
            dialogText=help.helpHTML,
            id=wx.ID_HELP,
            *args,
            **kwargs
        )


class Tips(settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Tips"),
            helpText=_("Tips about the program"),
            bitmap="lamp_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        help.showTips(self.mainWindow(), self.settings)


class Anonymize(IOCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Anonymize"),
            helpText=_("Anonymize a task file to attach it to a bug report"),
            *args,
            **kwargs
        )

    def doCommand(self, event):
        anonymized_filename = anonymize(self.iocontroller.filename())
        wx.MessageBox(
            _("Your task file has been anonymized and saved to:")
            + "\n"
            + anonymized_filename,
            _("Finished"),
            wx.OK,
        )

    def enabled(self, event):
        return bool(self.iocontroller.filename())


class HelpAbout(DialogCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&About %s") % meta.name,
            helpText=_("Version and contact information about %s") % meta.name,
            dialogTitle=_("About %s") % meta.name,
            dialogText=help.aboutHTML,
            id=wx.ID_ABOUT,
            bitmap="led_blue_information_icon",
            *args,
            **kwargs
        )


class HelpLicense(DialogCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&License"),
            helpText=_("%s license") % meta.name,
            dialogTitle=_("%s license") % meta.name,
            dialogText=meta.licenseHTML,
            direction=wx.Layout_LeftToRight,
            bitmap="document_icon",
            *args,
            **kwargs
        )


class CheckForUpdate(settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Check for update"),
            helpText=_("Check for the availability of a new version of %s") % meta.name,
            bitmap="box_icon",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        meta.VersionChecker(self.settings, verbose=True).start()


class URLCommand(base_uicommand.UICommand):
    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop("url")
        # self.url = kwargs.pop("urlpo")
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        try:
            openfile.openFile(self.url)
        except Exception as reason:
            wx.MessageBox(
                _("Cannot open URL:\n%s") % reason,
                caption=_("%s URL error") % meta.name,
                style=wx.ICON_ERROR,
            )


class FAQ(URLCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Frequently asked questions"),
            helpText=_("Browse the frequently asked questions and answers"),
            bitmap="led_blue_questionmark_icon",
            url=meta.faq_url,
            *args,
            **kwargs
        )


class ReportBug(URLCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Report a &bug..."),
            helpText=_("Report a bug or browse known bugs"),
            bitmap="bug_icon",
            url=meta.known_bugs_url,
            *args,
            **kwargs
        )


class RequestFeature(URLCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Request a &feature..."),
            helpText=_("Request a new feature or vote for existing requests"),
            bitmap="cogwheel_icon",
            url=meta.feature_request_url,
            *args,
            **kwargs
        )


class RequestSupport(URLCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Request &support..."),
            helpText=_("Request user support from the developers"),
            bitmap="life_ring_icon",
            url=meta.support_request_url,
            *args,
            **kwargs
        )


class HelpTranslate(URLCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Help improve &translations..."),
            helpText=_("Help improve the translations of %s") % meta.name,
            bitmap="person_talking_icon",
            url=meta.translations_url,
            *args,
            **kwargs
        )


class Donate(URLCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Donate..."),
            helpText=_("Donate to support the development of %s") % meta.name,
            bitmap="heart_icon",
            url=meta.donate_url,
            *args,
            **kwargs
        )


class MainWindowRestore(base_uicommand.UICommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Restore"),
            helpText=_("Restore the window to its previous state"),
            bitmap="restore",
            *args,
            **kwargs
        )

    def doCommand(self, event):
        self.mainWindow().restore(event)


class Search(ViewerCommand, settings_uicommand.SettingsCommand):
    # Search can only be attached to a real viewer, not to a viewercontainer
    def __init__(self, *args, **kwargs):
        self.__bound = False
        super().__init__(*args, helpText=_("Search"), **kwargs)
        assert self.viewer.isSearchable()

    def onFind(
        self,
        searchString,
        matchCase,
        includeSubItems,
        searchDescription,
        regularExpression,
    ):
        if self.__bound:
            self.viewer.setSearchFilter(
                searchString,
                matchCase,
                includeSubItems,
                searchDescription,
                regularExpression,
            )

    def appendToToolBar(self, toolbar):
        self.__bound = True
        (
            searchString,
            matchCase,
            includeSubItems,
            searchDescription,
            regularExpression,
        ) = self.viewer.getSearchFilter()
        # pylint: disable=W0201
        self.searchControl = widgets.SearchCtrl(
            toolbar,
            value=searchString,
            style=wx.TE_PROCESS_ENTER,
            matchCase=matchCase,
            includeSubItems=includeSubItems,
            searchDescription=searchDescription,
            regularExpression=regularExpression,
            callback=self.onFind,
        )
        toolbar.AddControl(self.searchControl)
        self.bindKeyDownInViewer()
        self.bindKeyDownInSearchCtrl()

    def bindKeyDownInViewer(self):
        """Bind wx.EVT_KEY_DOWN to self.onViewerKeyDown so we can catch
        Ctrl-F."""
        widget = self.viewer.getWidget()
        try:
            window = widget.GetMainWindow()
        except AttributeError:
            window = widget
        window.Bind(wx.EVT_KEY_DOWN, self.onViewerKeyDown)

    def bindKeyDownInSearchCtrl(self):
        """Bind wx.EVT_KEY_DOWN to self.onSearchCtrlKeyDown so we can catch
        the Escape key and drop down the menu on Ctrl-Down."""
        self.searchControl.getTextCtrl().Bind(wx.EVT_KEY_DOWN, self.onSearchCtrlKeyDown)

    def unbind(self, window, id_):
        self.__bound = False
        super().unbind(window, id_)

    def onViewerKeyDown(self, event):
        """On Ctrl-F, move focus to the search control."""
        if event.KeyCode == ord("F") and event.CmdDown() and not event.AltDown():
            self.searchControl.SetFocus()
        else:
            event.Skip()

    def onSearchCtrlKeyDown(self, event):
        """On Escape, move focus to the viewer, on Ctrl-Down popup the
        menu."""
        if event.KeyCode == wx.WXK_ESCAPE:
            self.viewer.SetFocus()
        elif event.KeyCode == wx.WXK_DOWN and event.AltDown():
            self.searchControl.PopupMenu()
        else:
            event.Skip()

    def doCommand(self, event):
        pass  # Not used


class ToolbarChoiceCommandMixin(object):
    def __init__(self, *args, **kwargs):
        self.choiceCtrl = None
        super().__init__(*args, **kwargs)

    def appendToToolBar(self, toolbar):
        """Add our choice control to the toolbar."""
        # pylint: disable=W0201
        self.choiceCtrl = wx.Choice(toolbar, choices=self.choiceLabels)
        self.currentChoice = self.choiceCtrl.Selection
        self.choiceCtrl.Bind(wx.EVT_CHOICE, self.onChoice)
        toolbar.AddControl(self.choiceCtrl)

    def unbind(self, window, id_):
        if self.choiceCtrl is not None:
            self.choiceCtrl.Unbind(wx.EVT_CHOICE)
            self.choiceCtrl = None
        super().unbind(window, id_)

    def onChoice(self, event):
        """The user selected a choice from the choice control."""
        choiceIndex = event.GetInt()
        if choiceIndex == self.currentChoice:
            return
        self.currentChoice = choiceIndex
        self.doChoice(self.choiceData[choiceIndex])

    def doChoice(self, choice):
        raise NotImplementedError  # pragma: no cover

    def doCommand(self, event):
        pass  # Not used

    def setChoice(self, choice):
        """Programmatically set the current choice in the choice control."""
        if self.choiceCtrl is not None:
            index = self.choiceData.index(choice)
            self.choiceCtrl.Selection = index
            self.currentChoice = index

    def enable(self, enable=True):
        if self.choiceCtrl is not None:
            self.choiceCtrl.Enable(enable)


class EffortViewerAggregationChoice(
    ToolbarChoiceCommandMixin, settings_uicommand.SettingsCommand, ViewerCommand
):
    choiceLabels = [
        _("Effort details"),
        _("Effort per day"),
        _("Effort per week"),
        _("Effort per month"),
    ]
    choiceData = ["details", "day", "week", "month"]

    def __init__(self, **kwargs):
        super().__init__(helpText=_("Aggregation mode"), **kwargs)

    def appendToToolBar(self, *args, **kwargs):
        super().appendToToolBar(*args, **kwargs)
        self.setChoice(
            self.settings.gettext(self.viewer.settingsSection(), "aggregation")
        )
        pub.subscribe(
            self.on_setting_changed,
            "settings.%s.aggregation" % self.viewer.settingsSection(),
        )

    def doChoice(self, choice):
        self.settings.settext(self.viewer.settingsSection(), "aggregation", choice)

    def on_setting_changed(self, value):
        self.setChoice(value)


class EffortViewerAggregationOption(settings_uicommand.UIRadioCommand, ViewerCommand):
    def isSettingChecked(self):
        return (
            self.settings.gettext(self.viewer.settingsSection(), "aggregation")
            == self.value
        )

    def doCommand(self, event):
        self.settings.settext(self.viewer.settingsSection(), "aggregation", self.value)


class TaskViewerTreeOrListChoice(
    ToolbarChoiceCommandMixin, settings_uicommand.UICheckCommand, ViewerCommand
):
    choiceLabels = [_("Tree"), _("List")]
    choiceData = [True, False]

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.choiceLabels[0],
            helpText=_(
                "When checked, show tasks as tree, " "otherwise show tasks as list"
            ),
            *args,
            **kwargs
        )

    def appendToToolBar(self, *args, **kwargs):
        super().appendToToolBar(*args, **kwargs)
        self.setChoice(
            self.settings.getboolean(self.viewer.settingsSection(), "treemode")
        )
        pub.subscribe(
            self.on_setting_changed,
            "settings.%s.treemode" % self.viewer.settingsSection(),
        )

    def doChoice(self, choice):
        self.settings.setboolean(self.viewer.settingsSection(), "treemode", choice)

    def on_setting_changed(self, value):
        self.setChoice(value)


class TaskViewerTreeOrListOption(settings_uicommand.UIRadioCommand, ViewerCommand):
    def isSettingChecked(self):
        return (
            self.settings.getboolean(self.viewer.settingsSection(), "treemode")
            == self.value
        )

    def doCommand(self, event):
        self.settings.setboolean(self.viewer.settingsSection(), "treemode", self.value)


class CategoryViewerFilterChoice(
    ToolbarChoiceCommandMixin, settings_uicommand.UICheckCommand
):
    choiceLabels = [
        _("Filter on all checked categories"),
        _("Filter on any checked category"),
    ]
    choiceData = [True, False]

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.choiceLabels[0],
            helpText=_(
                "When checked, filter on all checked categories, "
                "otherwise on any checked category"
            ),
            *args,
            **kwargs
        )

    def appendToToolBar(self, *args, **kwargs):
        super().appendToToolBar(*args, **kwargs)
        pub.subscribe(self.on_setting_changed, "settings.view.categoryfiltermatchall")

    def isSettingChecked(self):
        return self.settings.getboolean("view", "categoryfiltermatchall")

    def doChoice(self, choice):
        self.settings.setboolean("view", "categoryfiltermatchall", choice)

    def doCommand(self, event):
        self.settings.setboolean(
            "view", "categoryfiltermatchall", self._isMenuItemChecked(event)
        )

    def on_setting_changed(self, value):
        self.setChoice(value)


class SquareTaskViewerOrderChoice(
    ToolbarChoiceCommandMixin, settings_uicommand.SettingsCommand, ViewerCommand
):
    choiceLabels = [
        _("Budget"),
        _("Time spent"),
        _("Fixed fee"),
        _("Revenue"),
        _("Priority"),
    ]
    choiceData = ["budget", "timeSpent", "fixedFee", "revenue", "priority"]

    def __init__(self, **kwargs):
        super().__init__(helpText=_("Order choice"), **kwargs)

    def appendToToolBar(self, *args, **kwargs):
        super().appendToToolBar(*args, **kwargs)
        pub.subscribe(
            self.on_setting_changed,
            "settings.%s.sortby" % self.viewer.settingsSection(),
        )

    def doChoice(self, choice):
        self.settings.settext(self.viewer.settingsSection(), "sortby", choice)

    def on_setting_changed(self, value):
        self.setChoice(value)


class SquareTaskViewerOrderByOption(settings_uicommand.UIRadioCommand, ViewerCommand):
    def isSettingChecked(self):
        return (
            self.settings.gettext(self.viewer.settingsSection(), "sortby") == self.value
        )

    def doCommand(self, event):
        self.settings.settext(self.viewer.settingsSection(), "sortby", self.value)


class CalendarViewerConfigure(ViewerCommand):
    menuText = _("&Configure")
    helpText = _("Configure the calendar viewer")
    bitmap = "wrench_icon"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        self.viewer.configure()


class HierarchicalCalendarViewerConfigure(CalendarViewerConfigure):
    helpText = _("Configure the hierarchical calendar viewer")


class CalendarViewerNavigationCommand(ViewerCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        self.viewer.freeze()
        try:
            self.viewer.SetViewType(self.calendarViewType)  # pylint: disable=E1101
        finally:
            self.viewer.thaw()


class CalendarViewerNextPeriod(CalendarViewerNavigationCommand):
    menuText = _("&Next period")
    helpText = _("Show next period")
    bitmap = "next"
    calendarViewType = wxSCHEDULER_NEXT


class HierarchicalCalendarViewerNextPeriod(ViewerCommand):
    menuText = _("&Next period")
    helpText = _("Show next period")
    bitmap = "next"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        self.viewer.widget.Next()


class CalendarViewerPreviousPeriod(CalendarViewerNavigationCommand):
    menuText = _("&Previous period")
    helpText = _("Show previous period")
    bitmap = "prev"
    calendarViewType = wxSCHEDULER_PREV


class HierarchicalCalendarViewerPreviousPeriod(ViewerCommand):
    menuText = _("&Previous period")
    helpText = _("Show previous period")
    bitmap = "prev"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        self.viewer.widget.Prev()


class CalendarViewerToday(CalendarViewerNavigationCommand):
    menuText = _("&Today")
    helpText = _("Show Today")
    bitmap = "calendar_icon"
    calendarViewType = wxSCHEDULER_TODAY


class HierarchicalCalendarViewerToday(ViewerCommand):
    menuText = _("&Today")
    helpText = _("Show Today")
    bitmap = "calendar_icon"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs
        )

    def doCommand(self, event):
        self.viewer.widget.Today()  # Today or Today ?


class ToggleAutoColumnResizing(settings_uicommand.UICheckCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Automatic column resizing"),
            helpText=_(
                "When checked, automatically resize columns to fill" " available space"
            ),
            *args,
            **kwargs
        )
        wx.CallAfter(self.updateWidget)

    def updateWidget(self):
        self.viewer.getWidget().ToggleAutoResizing(self.isSettingChecked())

    def isSettingChecked(self):
        return self.settings.getboolean(
            self.viewer.settingsSection(), "columnautoresizing"
        )

    def doCommand(self, event):
        self.settings.set(
            self.viewer.settingsSection(),
            "columnautoresizing",
            str(self._isMenuItemChecked(event)),
        )
        self.updateWidget()


class ViewerPieChartAngle(ViewerCommand, settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        self.sliderCtrl = None
        super().__init__(helpText=_("Set pie chart angle"), *args, **kwargs)

    def appendToToolBar(self, toolbar):
        """Add our slider control to the toolbar."""
        # pylint: disable=W0201
        self.sliderCtrl = wx.Slider(
            toolbar,
            minValue=0,
            maxValue=90,
            value=self.getCurrentAngle(),
            size=(120, -1),
        )
        self.sliderCtrl.Bind(wx.EVT_SLIDER, self.onSlider)
        toolbar.AddControl(self.sliderCtrl)

    def unbind(self, window, itemId):
        if self.sliderCtrl is not None:
            self.sliderCtrl.Unbind(wx.EVT_SLIDER)
            self.sliderCtrl = None
        super().unbind(window, itemId)

    def onSlider(self, event):
        """The user picked a new angle."""
        event.Skip()
        self.setCurrentAngle()

    def doCommand(self, event):
        pass  # Not used

    def getCurrentAngle(self):
        return self.settings.getint(self.viewer.settingsSection(), "piechartangle")

    def setCurrentAngle(self):
        if self.sliderCtrl is not None:
            self.settings.setint(
                self.viewer.settingsSection(),
                "piechartangle",
                self.sliderCtrl.GetValue(),
            )


class RoundingPrecision(
    ToolbarChoiceCommandMixin, ViewerCommand, settings_uicommand.SettingsCommand
):
    roundingChoices = (0, 1, 3, 5, 6, 10, 15, 20, 30, 60)  # Minutes
    choiceData = [minutes * 60 for minutes in roundingChoices]  # Seconds
    # choiceLabels = [_('No rounding'), _('1 minute')] + [_('%d minutes') % minutes for minutes in roundingChoices[2:]]
    choiceLabels = [_("No rounding"), _("1 minute")] + [
        _("{} minutes".format(minutes for minutes in roundingChoices[2:]))
    ]

    def __init__(self, **kwargs):
        super().__init__(helpText=_("Rounding precision"), **kwargs)

    def doChoice(self, choice):
        self.settings.setint(self.viewer.settingsSection(), "round", choice)


class RoundBy(settings_uicommand.UIRadioCommand, ViewerCommand):
    def isSettingChecked(self):
        return (
            self.settings.getint(self.viewer.settingsSection(), "round") == self.value
        )

    def doCommand(self, event):
        self.settings.setint(self.viewer.settingsSection(), "round", self.value)


class AlwaysRoundUp(settings_uicommand.UICheckCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.checkboxCtrl = None
        super().__init__(
            menuText=_("&Always round up"),
            helpText=_("Always round up to the next rounding increment"),
            *args,
            **kwargs
        )

    def appendToToolBar(self, toolbar):
        """Add a checkbox control to the toolbar."""
        # pylint: disable=W0201
        self.checkboxCtrl = wx.CheckBox(toolbar, label=self.menuText)
        self.checkboxCtrl.Bind(wx.EVT_CHECKBOX, self.onCheck)
        toolbar.AddControl(self.checkboxCtrl)

    def unbind(self, window, itemId):
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Unbind(wx.EVT_CHECKBOX)
            self.checkboxCtrl = None
        super().unbind(window, itemId)

    def isSettingChecked(self):
        return self.settings.getboolean(self.viewer.settingsSection(), "alwaysroundup")

    def onCheck(self, event):
        self.setSetting(event.IsChecked())

    def doCommand(self, event):
        self.setSetting(self._isMenuItemChecked(event))

    def setSetting(self, alwaysRoundUp):
        self.settings.setboolean(
            self.viewer.settingsSection(), "alwaysroundup", alwaysRoundUp
        )

    def setValue(self, value):
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.SetValue(value)

    def enable(self, enable=True):
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Enable(enable)


class ConsolidateEffortsPerTask(settings_uicommand.UICheckCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.checkboxCtrl = None
        super().__init__(
            menuText=_("&Consolidate efforts per task"),
            helpText=_(
                "Consolidate all efforts per task to a single effort before rounding"
            ),
            *args,
            **kwargs
        )

    def appendToToolBar(self, toolbar):
        """Add a checkbox control to the toolbar."""
        # pylint: disable=W0201
        self.checkboxCtrl = wx.CheckBox(toolbar, label=self.menuText)
        self.checkboxCtrl.Bind(wx.EVT_CHECKBOX, self.onCheck)
        toolbar.AddControl(self.checkboxCtrl)

    def unbind(self, window, itemId):
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Unbind(wx.EVT_CHECKBOX)
            self.checkboxCtrl = None
        super().unbind(window, itemId)

    def isSettingChecked(self):
        return self.settings.getboolean(
            self.viewer.settingsSection(), "consolidateeffortspertask"
        )

    def onCheck(self, event):
        self.setSetting(self._isMenuItemChecked(event))

    def doCommand(self, event):
        self.setSetting(self._isMenuItemChecked(event))

    def setSetting(self, consolidateEffortsPerTask):
        self.settings.setboolean(
            self.viewer.settingsSection(),
            "consolidateeffortspertask",
            consolidateEffortsPerTask,
        )

    def setValue(self, value):
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.SetValue(value)

    def enable(self, enable=True):
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Enable(enable)
