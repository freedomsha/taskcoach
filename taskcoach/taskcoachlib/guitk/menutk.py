# -*- coding: utf-8 -*-
"""
menu.py - Gestion des menus dans Task Coach pour Tkinter.

Ce module contient les classes pour gérer les différents types de menus
utilisés dans Task Coach, adaptés pour une utilisation avec Tkinter.
Il s'agit d'une conversion du module wxPython original.
"""
# C'est un code wxPython assez complexe qui utilise des mixins,
# un système d'observateurs et des commandes UI pour gérer les menus.
#
# Convertir cela en tkinter demande une réécriture significative,
# car l'approche de tkinter est plus simple et moins orienté objet
# que celle de wxWidgets. Les concepts de mixins pour les commandes UI
# (UICommandContainerMixin) et la gestion des événements via pubsub devront
# être adaptés ou remplacés par des mécanismes tkinter équivalents.
import tkinter as tk
import logging
from os import path as ospath

from taskcoachlib import patterns, persistence, help  # pylint: disable=W0622
from taskcoachlib.domain import task, base, category
from taskcoachlib.i18n import _
# Les modules suivants sont des placeholders et devront être adaptés pour Tkinter
# et le reste de votre application.
from taskcoachlib.guitk.uicommand import base_uicommandtk  # Ceci doit être converti
from taskcoachlib.guitk.uicommand import uicommandtk as uicommand  # Ceci doit être converti
from taskcoachlib.guitk.uicommand import uicommandcontainertk  # Ceci doit être converti
from taskcoachlib.guitk.uicommand import settings_uicommandtk  # Ceci doit être converti
# from taskcoachlib.guitk import viewer
from pubsub import pub  # Ceci doit être converti ou remplacé par un autre mécanisme
from taskcoachlib import patterns  # Ceci doit être converti

log = logging.getLogger(__name__)


# Je n'ai pas utilisé tk.Menu comme classe parente pour la classe Menu
# pour conserver la structure du code original de Task Coach en wxPython.
#
# Dans le code original, la classe Menu n'hérite pas directement de wx.Menu. Au lieu de cela, elle contient une instance de wx.Menu et l'utilise pour gérer les commandes. C'est un modèle de conception par composition, qui dissocie la logique métier de la présentation de l'interface utilisateur.
#
# En suivant ce modèle, ma version tkinter de la classe Menu est un "wrapper" pour tk.Menu. Elle encapsule l'objet tk.Menu dans l'attribut _menu et offre une interface pour le manipuler (par exemple, appendUICommand). Cette approche rend le code plus modulaire et potentiellement plus facile à adapter à d'autres frameworks à l'avenir si nécessaire.

# class Menu(uicommandcontainer.UICommandContainerMixin):
class Menu(tk.Menu, uicommandcontainertk.UICommandContainerMixin):
    """
    Classe de base pour les menus dans Task Coach, adaptée pour Tkinter.

    Cette classe gère les éléments de menu et les commandes UI associées.
    L'approche est de créer une instance de `tkinter.Menu` et de l'associer
    à un objet parent (par exemple, la fenêtre principale).

    Attributs :
        _window (tk.Tk ou tk.Frame) : Référence à la fenêtre principale.
        # _menu (tk.Menu) : L'instance du menu Tkinter.
        _accels (list) : Liste des raccourcis clavier du menu.
        _observers (list) : Liste des observateurs liés au menu.
    """

    def __init__(self, window, tearoff=0):
        log.info(f"Menu : Création du menu de base pour Tkinter. Initialisation de {self.__class__.__name__}")
        # Appel du constructeur de la classe parente tk.Menu
        super().__init__(window, tearoff=tearoff)
        self._window = window
        # self._menu = tk.Menu(window, tearoff=tearoff)
        self._accels = []
        self._observers = []
        log.info(f"Menu : Fin d'Initialisation de Menu ! (self est {self.__class__.__name__})")

    # @property
    # def tk_menu(self):
    #     """Retourne l'objet tk.Menu pour l'utiliser avec un widget parent."""
    #     return self._menu

    def DestroyItem(self, menuItem_id):
        """
        Supprime un élément de menu par son ID.

        Note : Tkinter ne gère pas les objets 'MenuItem' comme wxPython.
        Nous devons utiliser l'ID ou l'index. Ici, nous utilisons l'ID.
        """
        log.info(f"Menu.DestroyItem supprime l'élément avec l'ID {menuItem_id}")
        try:
            # self._menu.delete(menuItem_id)
            self.delete(menuItem_id)
        except tk.TclError as e:
            log.error(f"Erreur lors de la suppression de l'élément de menu avec l'ID {menuItem_id}: {e}")

    def clearMenu(self):
        """ Supprimez tous les éléments du menu. """
        # self._menu.delete(0, tk.END)
        self.delete(0, tk.END)
        # self.delete(0, "end")
        self._accels = []
        self._observers = []
        log.debug("Menu.clearMenu : Tous les éléments et observateurs ont été supprimés.")

    def accelerators(self):
        """ Retourne la liste des raccourcis clavier du menu."""
        return self._accels

    def appendUICommands(self, *uiCommands):
        """
        Ajoute une liste de commandes UI au menu.

        Args:
            *uiCommands: Une liste de commandes UI ou de séparateurs (None).
        """
        log.debug(f"Menu.appendUICommands : Ajout des commandes UI au menu {self.__class__.__name__}")
        for uiCommand in uiCommands:
            if uiCommand is None:
                log.debug(f"Menu.appendUICommands : Ajout d'un séparateur au menu {self.__class__.__name__}")
                self.add_separator()
            else:
                try:
                    self.appendUICommand(uiCommand)
                    log.debug(f"Menu.appendUICommands : Commande {uiCommand.__class__.__name__} ajoutée !")
                except Exception as e:
                    log.error(f"Menu.appendUICommands : Échec de l'ajout de la commande {uiCommand.__class__.__name__} à cause de {e}", exc_info=True)

        # try:
        #     # S'il y a un appel à super() ici, il devrait être supprimé
        #     # pour utiliser la logique du mixin.
        #     # Remplacer cette méthode pour utiliser la logique fournie par UICommandContainerMixin
        #     super().appendUICommands(*uiCommands)  # L'appel super() est une erreur car il n'existe pas
        #     logging.debug("ColumnPopupMenu.appendUICommands : Commande ajoutée !")
        # except Exception as e:
        #     logging.error(f"ColumnPopupMenu.appendUICommands : La méthode super plante à cause de {e}.", exc_info=True)
        #     # Implémentation manuelle de la logique d'ajout
        #     for uiCommand in uiCommands:
        #         if uiCommand is None:
        #             self.add_separator()
        #         else:
        #             self.appendUICommand(uiCommand)

    def appendUICommand(self, uiCommand):
        """
        Ajoute une seule commande UI au conteneur, en gérant l'icône si elle est disponible.

        Cette méthode simule le comportement de `wxPython` en utilisant
        les méthodes de `tkinter.Menu`. La logique pour gérer
        les commandes (`uicommand`) et les observateurs devra être
        implémentée dans une classe `UICommand` compatible avec Tkinter.
        """
        log.info("Menu.appendUICommand called")
        # log.info(f"Menu.appendUICommand ajoute l' uiCommand {uiCommand.__class__.__name__} au menu {self.__class__.__name__}")
        log.info(f"Menu.appendUICommand ajoute l' uiCommand {uiCommand.menuText} au menu {self.__class__.__name__}")

        # Le code wxPython original appelait `uiCommand.addToMenu`.
        # Pour Tkinter, nous devrons adapter cette logique.
        # Par exemple, `uiCommand` pourrait avoir une méthode `add_to_tkinter_menu`.
        # Pour cet exemple, nous allons simuler cela.

        menu_text = getattr(uiCommand, 'menuText', 'Commande inconnue')
        command_func = getattr(uiCommand, 'do', None)
        command_func = uiCommand.onCommandActivate
        shortcut_text = ''
        if getattr(uiCommand, 'accelerator', None):
            shortcut_text = uiCommand.accelerator

        # # essai:
        # menu_options = {
        #     'label': uiCommand.getMenuText(),
        #     # 'command': uiCommand.doCommand,
        #     'command': uiCommand.onCommandActivate,
        #     'state': 'normal' if uiCommand.enabled() else 'disabled'
        # }

        # Tkinter ne gère pas l'état des items de menu de manière aussi directe
        # que wxWidgets. Le state doit être géré manuellement.
        state = tk.NORMAL if getattr(uiCommand, 'enabled', True) else tk.DISABLED

        # # Ajoutez l'icône si elle est disponible
        # bitmap = uiCommand.getBitmap()
        # if bitmap:
        #     # Assurez-vous que l'icône est une instance de PhotoImage de Tkinter
        #     menu_options['image'] = bitmap
        #     menu_options['compound'] = tk.LEFT  # Place l'image à gauche du texte

        # Gérer les différents types de commandes
        item_type = getattr(uiCommand, 'kind', 'normal')

        if item_type == 'normal':
            log.debug(f"Add normal Command function: {command_func}")
            # self._menu.add_command(
            self.add_command(
                label=menu_text,
                command=command_func,
                accelerator=shortcut_text,
                state=state
            )
        elif item_type == 'check':
            log.debug(f"Add checkbutton Command function: {command_func}")
            var = tk.BooleanVar(value=getattr(uiCommand, 'checked', False))
            # self._menu.add_checkbutton(
            self.add_checkbutton(
                label=menu_text,
                command=command_func,
                variable=var,
                state=state
            )
        elif item_type == 'radio':
            # Les boutons radio nécessitent une variable partagée.
            # Cela doit être géré par une classe `UIRadioCommand`.
            log.debug(f"Add radiobutton Command function: {command_func}")
            log.warning("Les commandes de type 'radio' ne sont pas encore complètement implémentées dans cette version Tkinter.")
            # self._menu.add_radiobutton(
            self.add_radiobutton(
                label=menu_text,
                command=command_func,
                state=state
            )

        # # Utilisez une condition pour déterminer le type de commande à ajouter
        # if hasattr(uiCommand, 'kind'):
        #     # Gérez les cases à cocher et les boutons radio
        #     menu_options['variable'] = uiCommand._variable
        #     menu_options['onvalue'] = True
        #     menu_options['offvalue'] = False
        #     self.add(uiCommand.kind, **menu_options)
        # else:
        #     self.add_command(**menu_options)

        self._accels.extend(getattr(uiCommand, 'accelerators', lambda: [])())

        if isinstance(uiCommand, patterns.Observer):
            self._observers.append(uiCommand)

    def appendMenu(self, text, subMenu):
        """
        Ajoute un sous-menu au menu.

        Args :
            text (str) : Le texte du sous-menu.
            subMenu (Menu) : Le sous-menu à ajouter.
        """
        # self._menu.add_cascade(label=text, menu=subMenu.tk_menu)
        self.add_cascade(label=text, menu=subMenu)
        self._accels.extend(subMenu.accelerators())

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        """
        Crée un sous-menu et y ajoute une liste de commandes UI.

        Args :
            menuTitle : Titre du sous-menu.
            uiCommands : Liste des commandes à ajouter.
        """
        subMenu = Menu(self._window, tearoff=0)
        self.appendMenu(menuTitle, subMenu)
        subMenu.appendUICommands(*uiCommands)


class DynamicMenu(Menu):
    """
    Un menu dynamique qui se met à jour automatiquement.
    """

    def __init__(self, window, parentMenu=None, labelInParentMenu=""):
        log.info("DynamicMenu : Création du menu Dynamique pour Tkinter.")
        super().__init__(window)
        self._parentMenu = parentMenu
        self._labelInParentMenu = self.__GetLabelText(labelInParentMenu)
        self.registerForMenuUpdate()
        self.updateMenu()

    def registerForMenuUpdate(self):
        """
        Méthode abstraite pour enregistrer le menu aux événements de mise à jour.

        Les sous-classes doivent implémenter cette méthode pour lier des
        événements (`pubsub` ou un autre mécanisme) à `onUpdateMenu`.
        """
        raise NotImplementedError

    def onUpdateMenu(self, newValue=None, sender=None):
        """
        Met à jour le menu lorsque l'événement est déclenché.
        """
        log.debug("DynamicMenu.onUpdateMenu : Mise à jour.")
        self.updateMenu()

    def updateMenu(self):
        """ Met à jour les éléments du menu. """
        self.updateMenuItems()

    def updateMenuItems(self):
        """
        La mise à jour des éléments de menu doit être implémentée dans les
        sous-classes.
        """
        self.clearMenu()
        # Ici, vous ajouteriez la logique pour peupler le menu
        # en fonction de l'état actuel de l'application.

    def enabled(self):
        """ Renvoie un booléen indiquant si ce menu doit être activé. """
        return True

    @staticmethod
    def __GetLabelText(menuText):
        """ Supprimez les accélérateurs du menuTexte. """
        return menuText.replace("&", "")


class DynamicMenuThatGetsUICommandsFromViewer(DynamicMenu):
    """
    Menu dynamique qui obtient ses commandes UI d'un visualiseur (`viewer`).
    """
    def __init__(self, viewer, parentMenu=None, labelInParentMenu=""):
        # Super() est appelé sur le constructeur de DynamicMenu, qui lui-même
        # appelle le constructeur de Menu (la classe parente).
        self._viewer = viewer
        self._uiCommands = None
        super().__init__(viewer, parentMenu, labelInParentMenu)

    def registerForMenuUpdate(self):
        """
        Enregistre le menu pour se mettre à jour lorsque la sélection
        du visualiseur change.

        Note : Cette partie doit être adaptée à votre système de
        gestion d'événements pour `viewer`. Pour cet exemple, nous
        supposons un événement `selection_changed`.
        """
        # Vous devrez adapter cette ligne pour votre système d'événements
        # de viewer.
        # Exemple avec pubsub si vous le convertissez :
        # pub.subscribe(self.onUpdateMenu, "viewer.selection_changed")
        log.warning("`DynamicMenuThatGetsUICommandsFromViewer.registerForMenuUpdate` est un placeholder. L'événement doit être lié à votre système de gestion des événements.")

    def updateMenuItems(self):
        """
        Met à jour les items du menu en fonction des commandes UI
        disponibles dans le visualiseur.
        """
        self.clearMenu()
        if self._viewer and hasattr(self._viewer, 'uiCommands'):
            self._uiCommands = self._viewer.uiCommands()
            self.appendUICommands(*self._uiCommands)

    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands)  # pylint: disable=W0142

    def getUICommands(self):
        raise NotImplementedError


# Ajout de la classe MainMenu
class MainMenu(Menu):
    # class mainMenu(tk.Menu):  # TODO : A essayer
    """
    Le menu principal de l'application Task Coach, adapté pour Tkinter.
    """
    # la classe MainMenu qui prend en charge la création de la barre de menus
    # principale et de ses sous-menus (Fichier, Édition, etc.).
    # Notez que les commandes UI (uicommand.FileNew, uicommand.EditUndo, etc.)
    # sont encore des placeholders, et
    # devront être converties pour fonctionner correctement avec Tkinter.
    # def __init__(self, parent, iocontroler, settings):
    def __init__(self, parent, settings, iocontroler, viewerContainer, taskFile):
        log.info("MainMenu : Création du menu principal.")
        super().__init__(parent, tearoff=0)
        self._iocontroler = iocontroler
        self._settings = settings
        self.parent = parent

        # # Création des sous-menus
        # self._fileMenu = self.appendSubMenuWithUICommands(
        #     "&Fichier",
        #     (
        #         # uicommand.FileNew(iocontroler=iocontroler),
        #         uicommand.FileOpen(iocontroler=iocontroler),
        #         uicommand.FileSave(iocontroler=iocontroler),
        #         uicommand.FileSaveAs(iocontroler=iocontroler),
        #         None, # Séparateur
        #         # uicommand.RecentFilesMenu(iocontroler),
        #         # None,
        #         # uicommand.ImportMenu(),
        #         # uicommand.ExportMenu(iocontroler),
        #         # None,
        #         uicommand.FileQuit(),
        #     )
        # )
        # # Les sous-menus sont des instances de classes de menu dédiées
        # # self._fileMenu = FileMenu(parent, iocontroler)
        # self._fileMenu = FileMenu(self, settings, self._iocontroler, viewerContainer)
        # log.debug(f"FileMenu created: {self._fileMenu}")
        # self.appendMenu("&Fichier", self._fileMenu)
        #
        # # self._editMenu = self.appendSubMenuWithUICommands(
        # #     "&Édition",
        # #     (
        # #         uicommand.EditUndo(),
        # #         uicommand.EditRedo(),
        # #         None,
        # #         uicommand.EditCut(),
        # #         uicommand.EditCopy(),
        # #         uicommand.EditPaste(),
        # #         None,
        # #         uicommand.EditFind(),
        # #         uicommand.EditFindNext(),
        # #         uicommand.EditFindPrevious(),
        # #         None,
        # #         uicommand.EditSelectAll(),
        # #     )
        # # )
        # self._editMenu = EditMenu(parent, settings, iocontroler, viewerContainer)
        # self.appendMenu("&Édition", self._editMenu)
        #
        # # Les autres menus (View, Tools, Help, etc.) devraient être
        # # ajoutés ici de la même manière que FileMenu et EditMenu.
        # # Pour le moment, ce sont des placeholders.
        # # ajoutés ici en instanciant leurs classes dédiées.
        # self.add_cascade(label="&Vue", menu=Menu(parent, tearoff=0))
        # self.add_cascade(label="&Outils", menu=Menu(parent, tearoff=0))
        # self.add_cascade(label="&Aide", menu=Menu(parent, tearoff=0))
        for menulisted, text in [
            (FileMenu(parent, settings, iocontroler, viewerContainer), _("&File")),
            (EditMenu(parent, settings, iocontroler, viewerContainer), _("&Edit")),
            (ViewMenu(parent, settings, viewerContainer, taskFile), _("&View")),
            (NewMenu(parent, settings, taskFile, viewerContainer), _("&New")),
            (ActionMenu(parent, settings, taskFile, viewerContainer), _("&Actions")),
            (HelpMenu(parent, settings, iocontroler), _("&Help"))]:
            # log.debug(f"MainMenu : Ajout du menu {menulisted}{text} au menuBar MainMenu {self}")

            self.appendMenu(text, menulisted)  # Tous doivent être de forme ('&Name', tk.Menu)

        # Lier le menu à la fenêtre
        parent.config(menu=self)  # Problème ?
        # self.parent.config(menu=self)  # A essayer !
        log.info("MainMenu : Menu principal configuré pour la fenêtre parente.")


class FileMenu(Menu):
    """
    Le menu "Fichier", adapté pour Tkinter.
    """
    def __init__(self, parent, settings, iocontroler, viewerContainer):
        log.info("FileMenu : Création du menu Fichier.")
        super().__init__(parent, tearoff=0)
        self._iocontroler = iocontroler
        self.appendUICommands(
            # uicommand.FileNew(iocontroler=iocontroler),
            uicommand.FileOpen(iocontroler=iocontroler),
            uicommand.FileMerge(iocontroler=iocontroler),
            uicommand.FileClose(iocontroler=iocontroler),
            None,
            uicommand.FileSave(iocontroler=iocontroler),
            uicommand.FileMergeDiskChanges(iocontroler=iocontroler),
            uicommand.FileSaveAs(iocontroler=iocontroler),
            uicommand.FileSaveSelection(iocontroler=iocontroler,
                                        viewer=viewerContainer),
        )
        if not settings.getboolean("feature", "syncml"):
            self.appendUICommands(uicommand.FilePurgeDeletedItems(iocontroler=iocontroler))
        self.appendUICommands(
            None,
            uicommand.FileSaveSelectedTaskAsTemplate(iocontroler=iocontroler,
                                                     viewer=viewerContainer),
            uicommand.FileImportTemplate(iocontroler=iocontroler),
            uicommand.FileEditTemplates(settings=settings),
            None,
            uicommand.PrintPageSetup(settings=settings),
            uicommand.PrintPreview(viewer=viewerContainer, settings=settings),
            uicommand.Print(viewer=viewerContainer, settings=settings),
            None,  # Séparateur
        )
        self.appendUICommands(
            # uicommand.RecentFilesMenu(iocontroler),  # Ceci est un menu dynamique, à implémenter séparément
            None,
            # uicommand.ImportMenu(), # Ceci est un sous-menu, à implémenter
            # uicommand.ExportMenu(iocontroler), # Ceci est un sous-menu, à implémenter
        )
        self.appendUICommands(
            None,
            uicommand.FileManageBackups(iocontroler=iocontroler, settings=settings)
        )
        if settings.getboolean("feature", "syncml"):
            try:
                import taskcoachlib.syncml.core  # pylint: disable=W0612,W0404
            except ImportError:
                pass
            else:
                self.appendUICommands(uicommand.FileSynchronize(iocontroler=iocontroler,
                                                                settings=settings))
        # self.__recentFilesStartPosition = len(self)  # ?
        self.appendUICommands(
            None,
            uicommand.FileQuit(),
            # uicommand.FileExit(),
        )


class ExportMenu(Menu):
    """
    Le sous-menu "Exporter", adapté pour Tkinter.
    """
    def __init__(self, parent, iocontroler, settings):
        log.info("ExportMenu : Création du menu Exporter.")
        super().__init__(parent, tearoff=0)

        self.appendUICommands(
            # uicommand.ExportToFile(iocontroler=iocontroler, settings=settings),
            # uicommand.ExportAsText(iocontroler=iocontroler, settings=settings),
            uicommand.FileExportAsHTML(iocontroler=iocontroler, settings=settings),
            uicommand.FileExportAsCSV(iocontroler=iocontroler, settings=settings),
            uicommand.FileExportAsICalendar(iocontroler=iocontroler, settings=settings),
            uicommand.FileExportAsTodoTxt(iocontroler=iocontroler, settings=settings),
        )


class ImportMenu(Menu):
    """
    Le sous-menu "Importer", adapté pour Tkinter.
    """
    def __init__(self, parent, iocontroler):
        log.info("ImportMenu : Création du menu Importer.")
        super().__init__(parent, tearoff=0)
        self.appendUICommands(
            uicommand.FileImportCSV(iocontroler=iocontroler),
            uicommand.FileImportTodoTxt(iocontroler=iocontroler),
            # uicommand.ImportFromFile(),
            # uicommand.ImportFromIcal(),
        )


class TaskTemplateMenu(DynamicMenu):
    """
    Menu des modèles de tâches dans Task Coach.

    Ce menu permet de gérer les modèles de tâches enregistrés et d'en créer de nouvelles à partir de ces modèles.

    Méthodes :
        registerForMenuUpdate (self) : Enregistre le menu pour recevoir les événements de mise à jour.
        onTemplatesSaved (self) : Met à jour le menu lorsque les modèles sont enregistrés.
        updateMenuItems (self) : Met à jour les éléments du menu.
        fillMenu (self, uiCommands) : Remplit le menu avec les commandes UI.
        getUICommands (self) : Récupère les commandes UI liées aux modèles de tâches.
    """
    def __init__(self, parent, taskList, settings):
        log.debug("Création du menu Modèle de Tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.settings = settings
        self.taskList = taskList
        super().__init__(parent)

    def registerForMenuUpdate(self):
        pub.subscribe(self.onTemplatesSaved, "templates.saved")

    def onTemplatesSaved(self):
        self.onUpdateMenu(None, None)

    def updateMenuItems(self):
        self.clearMenu()
        self.fillMenu(self.getUICommands())

    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands)  # pylint: disable=W0142

    def getUICommands(self):
        path = self.settings.pathToTemplatesDir()
        commands = [uicommand.TaskTemplateNew(ospath.join(path, name),
                                              taskList=self.taskList,
                                              settings=self.settings) for name in
                    persistence.TemplateList(path).names()]
        if not commands:
            log.info("Aucun modèle de tâche trouvé dans : %s", path)
        return commands


class EditMenu(Menu):
    """
    Le menu "Édition", adapté pour Tkinter.
    """
    def __init__(self, parent, settings, iocontroler, viewerContainer):
        log.info("EditMenu : Création du menu Édition.")
        super().__init__(parent, tearoff=0)
        self.appendUICommands(
            uicommand.EditUndo(),
            uicommand.EditRedo(),
            None,
            uicommand.EditCut(viewer=viewerContainer),
            uicommand.EditCopy(viewer=viewerContainer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=viewerContainer),
            None,
            uicommand.Edit(viewer=viewerContainer),
            uicommand.Delete(viewer=viewerContainer),
            None
        )
        #     None,
        #     uicommand.EditFind(),
        #     uicommand.EditFindNext(),
        #     uicommand.EditFindPrevious(),
        #     None,
        #     uicommand.EditSelectAll(),
        # )


class SelectMenu(Menu):
    def __init__(self, parent, viewerContainer):
        log.debug("Création du menu Select/Sélectionner.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        kwargs = dict(viewer=viewerContainer)
        # pylint: disable=W0142
        self.appendUICommands(uicommand.SelectAll(**kwargs),
                              uicommand.ClearSelection(**kwargs))


class ViewMenu(Menu):
    """
    Menu View/Affichage dans Task Coach.

    Ce menu contient des options pour gérer l'affichage, les modes de vue, les filtres, les colonnes, etc.
    """
    def __init__(self, parent, settings, viewerContainer, taskFile):
        """
        Initialise le menu Voir avec divers sous-menus comme les options d'affichage et les colonnes.

        Args :
            parent :
            settings :
            viewerContainer :
            taskFile :
        """
        log.info(f"ViewMenu : Création du menu View/Affichage. {self.__class__.__name__}")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        # log.debug("ViewMenu : Ajout du menu Nouvelle visualisation.")
        self.appendMenu(
            _("&New viewer"),
            ViewViewerMenu(parent, settings, viewerContainer, taskFile),
            # "viewnewviewer",
        )
        activateNextViewer = uicommand.ActivateViewer(
            viewer=viewerContainer,
            menuText=_("&Activate next viewer\tCtrl+PgDn"),
            helpText=help.viewNextViewer,
            forward=True,
            bitmap="activatenextviewer",
            # id=activateNextViewerId,
        )
        activatePreviousViewer = uicommand.ActivateViewer(
            viewer=viewerContainer,
            menuText=_("Activate &previous viewer\tCtrl+PgUp"),
            helpText=help.viewPreviousViewer,
            forward=False,
            bitmap="activatepreviousviewer",
            # id=activatePreviousViewerId,
        )
        self.appendUICommands(
            activateNextViewer,
            activatePreviousViewer,
            uicommand.RenameViewer(viewer=viewerContainer),
            None
        )
        # log.debug("ViewMenu : Ajout du menu : Mode")
        self.appendMenu(_("&Mode"), ModeMenu(parent, self, _("&Mode")))
        # log.debug("ViewMenu : Ajout du menu : Filtre")
        self.appendMenu(
            _("&Filter"), FilterMenu(parent, self, _("&Filter"))
        )
        # log.debug("ViewMenu : Ajout du menu : Sort/tri")
        self.appendMenu(_("&Sort"), SortMenu(parent, self, _("&Sort")))
        # log.debug("ViewMenu : Ajout du menu : Colonnes")
        self.appendMenu(
            _("&Columns"), ColumnMenu(parent, self, _("&Columns"))
        )
        # log.debug("ViewMenu : Ajout du menu : Rounding/arrondi")
        self.appendMenu(
            _("&Rounding"), RoundingMenu(parent, self, _("&Rounding"))
        )
        self.appendUICommands(None)
        # log.debug("ViewMenu : Ajout du menu : Options d'arborescence")
        self.appendMenu(
            _("&Tree options"),
            ViewTreeOptionsMenu(parent, viewerContainer),
            # "treeview"
        )
        self.appendUICommands(None)
        # log.debug("ViewMenu : Ajout du menu : Barre d'Outils")
        self.appendMenu(_("T&oolbar"), ToolBarMenu(parent, settings))
        self.appendUICommands(
            # uicommand.UICheckCommand(
            settings_uicommandtk.UICheckCommand(
                settings=settings,
                menuText=_("Status&bar"),
                helpText=_("Show/hide status bar"),
                setting="statusbar"
            )
        )
        log.debug("ViewMenu initialisé avec succès.")


class ViewViewerMenu(Menu):
    def __init__(self, parent, settings, viewerContainer, taskFile):
        log.info("Création du menu View Viewer.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # import taskcoachlib
        super().__init__(parent)
        ViewViewer = uicommand.ViewViewer
        kwargs = dict(viewer=viewerContainer, taskFile=taskFile, settings=settings)
        # pylint: disable=W0142
        # viewViewerCommands = [
        #     ViewViewer(
        #         menuText=_("&Task"),
        #         helpText=_("Open a new tab with a viewer that displays tasks"),
        #         # viewerClass=taskcoachlib.guitk.viewer.TaskViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("Task &statistics"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays task statistics"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.TaskStatsViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("Task &square map"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays tasks in a square map"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.SquareTaskViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("T&imeline"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays a timeline of tasks and effort"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.TimelineViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("&Calendar"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays tasks in a calendar"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.CalendarViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("&Hierarchical calendar"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays task hierarchy in a calendar"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.HierarchicalCalendarViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("&Category"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays categories"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.CategoryViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("&Effort"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays efforts"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.EffortViewer,
        #         **kwargs,
        #     ),
        #     uicommand.ViewEffortViewerForSelectedTask(
        #         menuText=_("Eff&ort for selected task(s)"),
        #         helpText=_(
        #             "Open a new tab with a viewer that displays efforts for the selected task"
        #         ),
        #         # viewerClass=taskcoachlib.guitk.viewer.EffortViewer,
        #         **kwargs,
        #     ),
        #     ViewViewer(
        #         menuText=_("&Note"),
        #         helpText=_("Open a new tab with a viewer that displays notes"),
        #         # viewerClass=taskcoachlib.guitk.viewer.NoteViewer,
        #         **kwargs,
        #     )
        # ]
        try:
            import igraph
            # viewViewerCommands.append(
            #     ViewViewer(
            #         menuText=_("&Dependency Graph"),
            #         helpText=_(
            #             "Open a new tab with a viewer that dependencies between weighted tasks over time"
            #         ),
            #         # viewerClass=taskcoachlib.guitk.viewer.TaskInterdepsViewer,
            #         **kwargs,
            #     )
            # )
        except ImportError:
            pass
        # self.appendUICommands(*viewViewerCommands)


class ViewTreeOptionsMenu(Menu):
    def __init__(self, parent, viewerContainer):
        log.info("ViewTreeOptionsMenu : Création du menu des Options de vue Arborescente.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        self.appendUICommands(
            uicommand.ViewExpandAll(viewer=viewerContainer),
            uicommand.ViewCollapseAll(viewer=viewerContainer))


class ModeMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.hasModes() and \
            bool(self._window.viewer.getModeUICommands())

    def getUICommands(self):
        return self._window.viewer.getModeUICommands()


class FilterMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.isFilterable() and bool(self._window.viewer.getFilterUICommands())

    def getUICommands(self):
        return self._window.viewer.getFilterUICommands()


class ColumnMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.hasHideableColumns()

    def getUICommands(self):
        return self._window.viewer.getColumnUICommands()


class SortMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.isSortable()

    def getUICommands(self):
        return self._window.viewer.getSortUICommands()


class RoundingMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.supportsRounding()

    def getUICommands(self):
        return self._window.viewer.getRoundingUICommands()


class ToolBarMenu(Menu):
    """
    Création du menu de ToolBar.
    """
    def __init__(self, parent, settings):
        log.info("Création du menu de la Barre d'Outils.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        toolbarCommands = []  # ?
        for value, menuText, helpText in [
            (None, _("&Hide"), _("Hide the toolbar")),
            (
                (16, 16),
                _("&Small images"),
                _("Small images (16x16) on the toolbar"),
            ),
            (
                (22, 22),
                _("&Medium-sized images"),
                _("Medium-sized images (22x22) on the toolbar"),
            ),
            (
                (32, 32),
                _("&Large images"),
                _("Large images (32x32) on the toolbar"),
            )
        ]:
            toolbarCommands.append(
                # uicommand.UIRadioCommand(
                settings_uicommandtk.UIRadioCommand(
                    settings=settings,
                    setting="toolbar",
                    value=value,
                    menuText=menuText,
                    helpText=helpText,
                )
            )
        # pylint: disable=W0142
        self.appendUICommands(*toolbarCommands)


class NewMenu(Menu):
    """
    Création du menu Nouveau dans la barre de Menu.
    """
    def __init__(self, parent, settings, taskFile, viewerContainer):
        log.info("Création du menu New/Nouveau.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        tasks = taskFile.tasks()
        self.appendUICommands(
            uicommand.TaskNew(taskList=tasks, settings=settings),
            uicommand.NewTaskWithSelectedTasksAsPrerequisites(
                taskList=tasks, viewer=viewerContainer, settings=settings
            ),
            uicommand.NewTaskWithSelectedTasksAsDependencies(
                taskList=tasks, viewer=viewerContainer, settings=settings
            )
        )
        # log.debug("NewMenu : Ajout du menu : Nouvelle tâche depuis les archives")
        self.appendMenu(
            _("New task from &template"),
            TaskTemplateMenu(parent, taskList=tasks, settings=settings),
            # "newtmpl"
        )
        self.appendUICommands(
            None,
            uicommand.EffortNew(
                viewer=viewerContainer,
                effortList=taskFile.efforts(),
                taskList=tasks,
                settings=settings
            ),
            uicommand.CategoryNew(
                categories=taskFile.categories(), settings=settings
            ),
            uicommand.NoteNew(notes=taskFile.notes(), settings=settings),
            None,
            uicommand.NewSubItem(viewer=viewerContainer))


class ActionMenu(Menu):
    def __init__(self, parent, settings, taskFile, viewerContainer):
        log.info("Création du menu Action.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        categories = taskFile.categories()
        # Generic actions, applicable to all/most domain objects:
        # log.debug("📌 [DEBUG] ActionMenu : Ajout d’un attachement :")
        self.appendUICommands(
            uicommand.AddAttachment(viewer=viewerContainer, settings=settings),
            uicommand.OpenAllAttachments(viewer=viewerContainer,
                                         settings=settings),
            None,
            uicommand.AddNote(viewer=viewerContainer, settings=settings),
            uicommand.OpenAllNotes(viewer=viewerContainer, settings=settings),
            None,
            uicommand.Mail(viewer=viewerContainer),
            None,
        )
        # log.debug("ActionMenu : Ajout du menu : Toggle Categorie")
        self.appendMenu(
            _("&Toggle category"),
            ToggleCategoryMenu(
                parent, categories=categories, viewer=viewerContainer
            ),
            # "folder_blue_arrow_icon"
        )
        # Start of task specific actions:
        self.appendUICommands(
            None,
            uicommand.TaskMarkInactive(
                settings=settings, viewer=viewerContainer
            ),
            uicommand.TaskMarkActive(
                settings=settings, viewer=viewerContainer
            ),
            uicommand.TaskMarkCompleted(
                settings=settings, viewer=viewerContainer
            ),
            None
        )
        # log.debug("ActionMenu : Ajout du menu : Changement de priorité/tâche")
        self.appendMenu(
            _("Change task &priority"),
            TaskPriorityMenu(parent, tasks, viewerContainer),
            # "incpriority"
        )
        self.appendUICommands(
            None,
            uicommand.EffortStart(viewer=viewerContainer, taskList=tasks),
            uicommand.EffortStop(viewer=viewerContainer, effortList=efforts, taskList=tasks),
            uicommand.EditTrackedTasks(taskList=tasks, settings=settings))


class TaskPriorityMenu(Menu):
    def __init__(self, parent, taskList, viewerContainer):
        log.info("Création du menu Priorité de Tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        kwargs = dict(taskList=taskList, viewer=viewerContainer)
        # pylint: disable=W0142
        self.appendUICommands(
            uicommand.TaskIncPriority(**kwargs),
            uicommand.TaskDecPriority(**kwargs),
            uicommand.TaskMaxPriority(**kwargs),
            uicommand.TaskMinPriority(**kwargs))


class HelpMenu(Menu):
    def __init__(self, parent, settings, iocontroller):
        log.info("Création du menu Help/Aide.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        self.appendUICommands(
            uicommand.Help(),
            uicommand.FAQ(),
            uicommand.Tips(settings=settings),
            uicommand.Anonymize(iocontroller=iocontroller),
            None,
            uicommand.RequestSupport(),
            uicommand.ReportBug(),
            uicommand.RequestFeature(),
            None,
            uicommand.HelpTranslate(),
            uicommand.Donate(),
            None,
            uicommand.HelpAbout(),
            uicommand.CheckForUpdate(settings=settings),
            uicommand.HelpLicense())


class TaskBarMenu(Menu):
    """
    Problème : Le problème est effectivement que TaskBarIcon
    n'est pas une sous-classe de wx.Window, et les menus wxPython
    (comme ceux gérés par UICommandContainerMixin) sont
    conçus pour être associés à des wx.Window.
    """
    def __init__(self, taskBarIcon, settings, taskFile, viewer):
        log.info("TaskBarMenu : Création du menu de Barre de tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(taskBarIcon)
        # super().__init__()
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        self.appendUICommands(
            uicommand.TaskNew(taskList=tasks, settings=settings)
        )
        # log.debug("TaskBarMenu : Ajout du menu : Nouvelle tâche depuis les archives.")
        self.appendMenu(
            _("New task from &template"),
            TaskTemplateMenu(taskBarIcon, taskList=tasks, settings=settings),
            # "newtmpl"
        )
        self.appendUICommands(None)  # Separator
        self.appendUICommands(
            uicommand.EffortNew(effortList=efforts, taskList=tasks,
                                settings=settings),
            uicommand.CategoryNew(categories=taskFile.categories(),
                                  settings=settings),
            uicommand.NoteNew(notes=taskFile.notes(), settings=settings))
        self.appendUICommands(None)  # Separator
        label = _("&Start tracking effort")
        # log.debug("taskBArMenu : Ajout du menu : Départ d'effort pour la tâche.")
        # self.appendMenu(
        #     label,
        #     StartEffortForTaskMenu(
        #         taskBarIcon, taskcoachlib.domain.base.filter.DeletedFilter(tasks), self, label
        #     ),
        #     "clock_icon"
        # )
        self.appendUICommands(
            uicommand.EffortStop(
                viewer=viewer, effortList=efforts, taskList=tasks
            )
        )
        self.appendUICommands(
            None, uicommand.MainWindowRestore(), uicommand.FileQuit()
        )


class ToggleCategoryMenu(DynamicMenu):
    def __init__(self, parent, categories, viewer):  # pylint: disable=W0621
        log.info("Création du menu Toggle Catégorie.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.categories = categories
        self.viewer = viewer
        super().__init__(parent)
        log.info("Toggle Catégorie initialisé.")

    def registerForMenuUpdate(self):
        for eventType in (self.categories.addItemEventType(),
                          self.categories.removeItemEventType()):
            patterns.Publisher().registerObserver(self.onUpdateMenu,
                                                  eventType=eventType,
                                                  eventSource=self.categories)
        patterns.Publisher().registerObserver(self.onUpdateMenu,
                                              eventType=category.Category.subjectChangedEventType())

    def updateMenuItems(self):
        self.clearMenu()
        self.addMenuItemsForCategories(self.categories.rootItems(), self)

    def addMenuItemsForCategories(self, categories, menuToAdd):
        """
        Ajoute des éléments de Menu, Trie et construit le menu pour les catégories

        Args :
            categories :
            menu :

        Returns :

        """
        # pylint: disable=W0621
        # Trie et construit le menu pour les catégories
        # log.debug("ToggleCategoryMenu.addMenuItemsForCategories : Ajout de %d catégories au menu.", len(categories))
        categories = categories[:]
        categories.sort(key=lambda category: category.subject().lower())
        for category in categories:
            uiCommand = uicommand.ToggleCategory(category=category,
                                                 viewer=self.viewer)
            log.debug(f"ToggleCategoryMenu.addMenuItemsForCategories : Ajout du sous-menu : {uiCommand} dans {menuToAdd} fenêtre {self._window}")
            uiCommand.addToMenu(menuToAdd, self._window)
        categoriesWithChildren = [category for category in categories if category.get_domain_children()]
        if categoriesWithChildren:
            menuToAdd.AppendSeparator()
            for category in categoriesWithChildren:
                # log.debug("ToggleCategoryMenu.addMenuItemsForCategories : est-ce là l'erreur!")
                subMenu = Menu(self._window)
                # log.debug(f"subMenu={subMenu}")
                self.addMenuItemsForCategories(category.get_domain_children(), subMenu)
                # log.debug(f"ToggleCategoryMenu.addMenuItemsForCategories : Ajout du sous-menu : {self.subMenuLabel(category)}{subMenu} dans {menuToAdd}")
                menuToAdd.AppendSubMenu(subMenu, self.subMenuLabel(category))

    @staticmethod
    def subMenuLabel(category):  # pylint: disable=W0621
        # return _("%s (subcategories)") % category.subject()
        return _(f"{category.subject()} (subcategories)")

    def enabled(self):
        return bool(self.categories)


class StartEffortForTaskMenu(DynamicMenu):
    def __init__(self, taskBarIcon, tasks, parentMenu=None,
                 labelInParentMenu=""):
        log.info("Création du menu Début d'effort de tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.tasks = tasks
        super().__init__(taskBarIcon, parentMenu, labelInParentMenu)
        log.info("StartEffortForTaskMenu : Menu début d'effort de tâche créé !")

    def registerForMenuUpdate(self):
        for eventType in (self.tasks.addItemEventType(),
                          self.tasks.removeItemEventType()):
            patterns.Publisher().registerObserver(self.onUpdateMenu_Deprecated,
                                                  eventType=eventType,
                                                  eventSource=self.tasks)
        # for eventType in (task.Task.subjectChangedEventType(),
        #                   task.Task.trackingChangedEventType(),
        #                   task.Task.plannedStartDateTimeChangedEventType(),
        #                   task.Task.dueDateTimeChangedEventType(),
        #                   task.Task.actualStartDateTimeChangedEventType(),
        #                   task.Task.completionDateTimeChangedEventType()):
        #     if eventType.startswith("pubsub"):
        #         pub.subscribe(self.onUpdateMenu, eventType)
        #     else:
        #         patterns.Publisher().registerObserver(self.onUpdateMenu_Deprecated,
        #                                               eventType)

    def updateMenuItems(self):
        self.clearMenu()
        trackableRootTasks = self._trackableRootTasks()
        trackableRootTasks.sort(key=lambda task: task.subject())
        for trackableRootTask in trackableRootTasks:
            self.addMenuItemForTask(trackableRootTask, self)

    def addMenuItemForTask(self, task, menuItem):  # pylint: disable=W0621
        uiCommand = uicommand.EffortStartForTask(task=task, taskList=self.tasks)
        log.debug(f"StartEffortForTaskMenu.addMenuItemForTask Ajoute le menu {uiCommand} à {menuItem} fenêtre {self._window}")
        uiCommand.addToMenu(menuItem, self._window)
        trackableChildren = [child for child in task.get_domain_children() if
                             child in self.tasks and not child.completed()]
        if trackableChildren:
            trackableChildren.sort(key=lambda child: child.subject())
            subMenu = Menu(self._window)
            for child in trackableChildren:
                self.addMenuItemForTask(child, subMenu)
            log.debug(f"StartEffortForTaskMenu.addMenuItemForTask : Ajout du sous-menu : {task.subject()} (subtasks){subMenu} dans {menuItem}")
            menuItem.AppendSubMenu(subMenu, _("%s (subtasks)") % task.subject())

    def enabled(self):
        return bool(self._trackableRootTasks())

    def _trackableRootTasks(self):
        return [rootTask for rootTask in self.tasks.rootItems()
                if not rootTask.completed()]


class TaskPopupMenu(Menu):
    """
    Menu contextuel pour les tâches dans Task Coach.

    Ce menu contextuel est utilisé pour afficher des options d'action sur les tâches telles que couper, copier, coller, ajouter une note, etc.

    Méthodes :
        __init__ (self, mainwindow, settings, tasks, efforts, categories, taskViewer) :
            Initialise le menu contextuel des tâches.
    """
    def __init__(self, parent, settings, tasks, efforts, categories, taskViewer):
        log.info("TaskPopupMenu : Création du menu Popup de Tâche.")
        super().__init__(parent)
        # log.info("TaskPopuMenu : Initialisation du menu contextuel : %s", self.__class__.__name__)
        # log.debug(f"mainwindow={mainwindow}, settings={settings},"
        #           f"tasks={tasks}, efforts={efforts},"
        #           f"categories={categories}, taskViewer={taskViewer}")
        # Les commandes de menu sont ici :
        # log.debug("TaskPopupMenu : Ajoute une liste d'UICommands.")

        self.appendUICommands(
            uicommand.EditCut(viewer=taskViewer),
            uicommand.EditCopy(viewer=taskViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=taskViewer),
            None,
            uicommand.Edit(viewer=taskViewer),
            uicommand.Delete(viewer=taskViewer),
            None,
            uicommand.AddAttachment(viewer=taskViewer, settings=settings),
            uicommand.OpenAllAttachments(viewer=taskViewer,
                                         settings=settings),
            None,
            uicommand.AddNote(viewer=taskViewer,
                              settings=settings),
            uicommand.OpenAllNotes(viewer=taskViewer, settings=settings),
            None,
            uicommand.Mail(viewer=taskViewer),
            None)
        # log.debug("TaskPopupMenu : Ajout du menu : Toggle Categorie")
        self.appendMenu(_("&Toggle category"),
                        ToggleCategoryMenu(parent=parent, categories=categories,
                                           viewer=taskViewer),
                        # "folder_blue_arrow_icon"
                        )
        # Les commandes de menu sont ici
        # log.debug("TaskPopupMenu - Ajout du menu Toggle Categorie : Ajout des commandes :")
        self.appendUICommands(
            None,
            uicommand.TaskMarkInactive(settings=settings, viewer=taskViewer),
            uicommand.TaskMarkActive(settings=settings, viewer=taskViewer),
            uicommand.TaskMarkCompleted(settings=settings, viewer=taskViewer),
            None)
        # log.debug("TaskPopupMenu : Ajout du menu : Priorité")
        self.appendMenu(_("&Priority"),
                        TaskPriorityMenu(parent, tasks, taskViewer),
                        # "incpriority"
                        )
        # Les commandes de menu sont ici :
        self.appendUICommands(
            None,
            uicommand.EffortNew(viewer=taskViewer, effortList=efforts,
                                taskList=tasks, settings=settings),
            uicommand.EffortStart(viewer=taskViewer, taskList=tasks),
            uicommand.EffortStop(
                viewer=taskViewer, effortList=efforts, taskList=tasks),
            None,
            uicommand.NewSubItem(viewer=taskViewer))
        log.info("TaskPopupMenu : Terminée - Menu Popup de Tâche créé.")


class EffortPopupMenu(Menu):
    def __init__(self, parent, tasks, efforts, settings, effortViewer):
        log.info("Création du menu Popup Effort.")
        # log.debug("Affichage du menu contextuel pour les efforts.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        self.appendUICommands(
            uicommand.EditCut(viewer=effortViewer),
            uicommand.EditCopy(viewer=effortViewer),
            uicommand.EditPaste(),
            None,
            uicommand.Edit(viewer=effortViewer),
            uicommand.Delete(viewer=effortViewer),
            None,
            uicommand.EffortNew(viewer=effortViewer, effortList=efforts,
                                taskList=tasks, settings=settings),
            uicommand.EffortStartForEffort(
                viewer=effortViewer, taskList=tasks),
            uicommand.EffortStop(
                viewer=effortViewer, effortList=efforts, taskList=tasks),
        )
        log.info("EffortPopupMenu : Menu Popup Effort créé !")


class CategoryPopupMenu(Menu):
    """
    Le menu CategoryPopupMenu s’appuie fortement sur UICommandContainerMixin,
    notamment avec 'self.appendUICommands([...])'.
    """
    def __init__(self, parent, settings, taskFile, categoryViewer,
                 localOnly=False):
        log.info("Création du menu Popup Catégorie.")
        # log.debug("Affichage du menu contextuel pour les catégories.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        categories = categoryViewer.presentation()
        tasks = taskFile.tasks()
        notes = taskFile.notes()
        self.appendUICommands(
            uicommand.EditCut(viewer=categoryViewer),
            uicommand.EditCopy(viewer=categoryViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=categoryViewer),
            None,
            uicommand.Edit(viewer=categoryViewer),
            uicommand.Delete(viewer=categoryViewer),
            None,
            uicommand.AddAttachment(viewer=categoryViewer, settings=settings),
            uicommand.OpenAllAttachments(viewer=categoryViewer,
                                         settings=settings),
            None,
            uicommand.AddNote(viewer=categoryViewer, settings=settings),
            uicommand.OpenAllNotes(viewer=categoryViewer, settings=settings),
            None,
            uicommand.Mail(viewer=categoryViewer))
        if not localOnly:
            self.appendUICommands(
                None,
                uicommand.NewTaskWithSelectedCategories(taskList=tasks,
                                                        settings=settings,
                                                        categories=categories,
                                                        viewer=categoryViewer),
                uicommand.NewNoteWithSelectedCategories(notes=notes,
                                                        settings=settings,
                                                        categories=categories,
                                                        viewer=categoryViewer))
        self.appendUICommands(
            None,
            uicommand.NewSubItem(viewer=categoryViewer))
        log.info("CategoryPopupMenu : Menu Popup Catégorie créé !")


class NotePopupMenu(Menu):
    def __init__(self, parent, settings, categories, noteViewer):
        log.info("Création du menu Popup Note.")
        # log.debug("Affichage du menu contextuel pour les notes.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        self.appendUICommands(
            uicommand.EditCut(viewer=noteViewer),
            uicommand.EditCopy(viewer=noteViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=noteViewer),
            None,
            uicommand.Edit(viewer=noteViewer),
            uicommand.Delete(viewer=noteViewer),
            None,
            uicommand.AddAttachment(viewer=noteViewer, settings=settings),
            uicommand.OpenAllAttachments(viewer=noteViewer, settings=settings),
            None,
            uicommand.Mail(viewer=noteViewer),
            None)
        # log.debug("NotePopupMenu : Ajout du menu : Toggle Categorie")
        self.appendMenu(_("&Toggle category"),
                        ToggleCategoryMenu(parent, categories=categories,
                                           viewer=noteViewer),
                        # "folder_blue_arrow_icon"
                        )
        self.appendUICommands(
            None,
            uicommand.NewSubItem(viewer=noteViewer))
        log.debug("NotePopupMenu : Menu créé !")


class ColumnPopupMenuMixin(object):
    """ Mixin class for column header popup menu's. These menu's get the
        column index property set by the control popping up the menu to
        indicate which column the user clicked. See
        widgets._CtrlWithColumnPopupMenuMixin. """

    def __setColumn(self, columnIndex):
        self.__columnIndex = columnIndex  # pylint: disable=W0201

    def __getColumn(self):
        return self.__columnIndex

    columnIndex = property(__getColumn, __setColumn)

    def getUICommands(self):
        # if not self._window:  # Prevent PyDeadObject exception when running tests
        #     return []
        return [
            uicommand.HideCurrentColumn(viewer=self._window),
            None,
        ] + self._window.getColumnUICommands()


class ColumnPopupMenu(ColumnPopupMenuMixin, Menu):
    """ Column header popup menu. """

    def __init__(self, window):
        log.info("Création du menu Popup Colonne.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(window)
        log.debug("ColumnPopupMenu : Appel de CallAfter.")
        window.after(self.appendUICommands, *self.getUICommands())
        log.debug("ColumnPopupMenu : CallAfter passé avec succès. Menu Popup Colonne terminé !")

    def appendUICommands(self, *args, **kwargs):
        # Prepare for PyDeadObjectError since we're called from wx.CallAfter
        log.debug("ColumnPopupMenu.appendUICommands essaie d'ajouter une commande via la méthode super.")
        try:
            super().appendUICommands(*args, **kwargs)
            # print(f"tclib.gui.menu.AppendUICommands: {uiCommand}, id = {uiCommand.id}") # Ajout de journalisation
        # except wx.PyDeadObjectError:
        except RuntimeError as e:
            log.error(f"ColumnPopupMenu.appendUICommands : La méthode super plante à cause de {e}.", exc_info=True)
        log.debug("ColumnPopupMenu.appendUICommands : Commande ajoutée !")


class EffortViewerColumnPopupMenu(ColumnPopupMenuMixin,
                                  DynamicMenuThatGetsUICommandsFromViewer):
    """ Column header popup menu. """

    def registerForMenuUpdate(self):
        pub.subscribe(self.onChangeAggregation, "effortviewer.aggregation")

    def onChangeAggregation(self):
        self.onUpdateMenu(None, None)


class AttachmentPopupMenu(Menu):
    def __init__(self, parent, settings, attachments, attachmentViewer):
        log.info("Création du menu Popup Attachment.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(parent)
        self.appendUICommands(
            uicommand.EditCut(viewer=attachmentViewer),
            uicommand.EditCopy(viewer=attachmentViewer),
            uicommand.EditPaste(),
            None,
            uicommand.Edit(viewer=attachmentViewer),
            uicommand.Delete(viewer=attachmentViewer),
            None,
            uicommand.AddNote(viewer=attachmentViewer, settings=settings),
            uicommand.OpenAllNotes(viewer=attachmentViewer,
                                   settings=settings),
            None,
            uicommand.AttachmentOpen(viewer=attachmentViewer,
                                     attachments=attachments,
                                     settings=settings))
