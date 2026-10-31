# -*- coding: utf-8 -*-
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

    License: GNU General Public License (GPL) v3 or later.
    Description: Cette classe définit la fenêtre principale de l'application pour Task Coach en Tkinter.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox

from taskcoachlib import application, meta, operating_system
from taskcoachlib.config.settings import Settings
from taskcoachlib.guitk import (
    artprovidertk,
    idlecontrollertk,
    iocontrollertk,
    remindercontrollertk,
    statustk,
    toolbarttk,
    windowdimensionstrackertk,
)
from taskcoachlib.guitk.viewer import containertk, factorytk
from taskcoachlib.guitk.dialog.editor import Editor
from taskcoachlib.guitk import menutk
from taskcoachlib.widgetstk import framettk
from taskcoachlib.i18n import _
from pubsub import pub

# Importation des constantes AUI pour Tkinter
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk import aui_tk_constants as aui

log = logging.getLogger(__name__)

class MainWindow(framettk.AuiManagedFrameWithDynamicCenterPane):
    """
    Classe représentant la fenêtre/frame principale de Task Coach pour Tkinter.

    Cette classe gère l'interface utilisateur de l'application,
    y compris les barres d'outils, les menus, la gestion des tâches,
    la synchronisation avec des dispositifs externes comme l'iPhone, et bien plus encore.

    Attributs :
        iocontroller : Contrôleur d'entrée/sortie pour les fichiers.
        taskFile : Fichier de tâches en cours.
        settings : Paramètres utilisateur.
        viewer_container : Conteneur des visionneuses de tâches.
        reminderController : Gère les rappels de tâches.
        bonjourRegister : Service Bonjour pour la synchronisation iPhone.
        bonjourAcceptor : Accepte les connexions iPhone.
        _idleController : Gère les actions d'inactivité (suivi du temps).
    """

    def __init__(self, parent, iocontroller, taskFile, settings: Settings, *args, **kwargs):
        """
        Initialise la fenêtre principale de Task Coach avec les paramètres fournis.

        Args:
            parent (tk.Tk): Fenêtre racine Tkinter.
            iocontroller (IOController): Contrôleur d'entrée/sortie pour gérer les fichiers.
            taskFile (TaskFile): Fichier de tâches à manipuler.
            settings (Settings): Paramètres utilisateur à appliquer à la fenêtre principale.
            *args, **kwargs: Arguments supplémentaires pour la fenêtre.
        """
        log.info("Début d'initialisation de MainWindow (Tkinter)")

        self.__splash = kwargs.pop("splash", None)

        # Initialisation de la classe de base
        super().__init__(master=parent, title=meta.name, **kwargs)

        # Attributs
        self.parent = parent
        self.iocontroller = iocontroller
        self.taskFile = taskFile
        self.settings = settings
        self.__filename = None
        self.__dirty = False
        self.__shutdown = False
        self.bonjourRegister = None
        self.bonjourAcceptor = None
        self._handling_resize = False
        self._is_hidden_when_iconized = False
        self._lastSize = None

        # Initialisation du tracker de dimensions de fenêtre
        self.__dimensions_tracker = windowdimensionstrackertk.WindowDimensionsTracker(
            self.parent, self.settings
        )

        # Initialisation des composants
        self._create_window_components()
        self.__init_window_components()

        try:
            self.__init_window()
        except Exception as e:
            log.exception(f"Problème avec __init_window() : {e}", exc_info=True)

        # Enregistrement pour les changements de composants
        self.__register_for_window_component_changes()

        # Initialisation du contrôleur d'inactivité
        self._idleController = idlecontrollertk.IdleController(
            self, self.settings, self.taskFile.efforts()
        )

        # Vérification XFCE4
        self.parent.after(100, self.checkXFCE4)

        # Bind des événements de fenêtre
        self.parent.protocol("WM_DELETE_WINDOW", self.onClose)
        self.parent.bind("<Configure>", self.onResize)
        self.parent.bind("<Unmap>", self.onIconify)

        log.info("MainWindow : Initialisé avec succès")

    def _create_window_components(self) -> None:
        """
        Crée et initialise les différents composants de la fenêtre,
        comme les barres d'outils, les barres de statut, et les autres éléments de l'interface graphique.
        """
        log.debug("MainWindow._create_window_components : création des composants")

        # Création du conteneur pour les visionneuses
        self._create_viewer_container()

        # Ajout des viewers
        factorytk.addViewers(self.viewer_container, self.taskFile, self.settings)

        # Création de la barre de statut
        self._create_status_bar()

        # Création de la barre de menu
        self.__create_menu_bar()

        # Création du contrôleur de rappel
        self.__create_reminder_controller()

        # Appel componentsCreated
        self.viewer_container.componentsCreated()

        log.debug("MainWindow._create_window_components : terminé")

    def _create_viewer_container(self) -> None:
        """
        Crée le conteneur pour les visionneuses (tâches, notes, etc.) dans la fenêtre principale.
        """
        log.debug("MainWindow._create_viewer_container : création du conteneur")
        self.viewer_container = containertk.ViewerContainer(self, self.settings)

        # Ajout du conteneur au manager AUI
        self.addPane(
            self.viewer_container,
            caption=_("Tasks"),
            name="viewer_container",
            floating=False
        )
        log.debug("MainWindow._create_viewer_container : conteneur créé")

    def _create_status_bar(self) -> None:
        """
        Crée et associe une barre de statut à la fenêtre principale.
        """
        log.info("MainWindow._create_status_bar : Création de la barre de statut")
        self.status_bar = statustk.StatusBar(self, self.viewer_container)

        # Ajout de la barre de statut au manager AUI
        self.addPane(
            self.status_bar,
            caption=_("Status"),
            name="status_bar",
            floating=False
        )

    def __create_menu_bar(self) -> None:
        """
        Crée et associe la barre de menus à la fenêtre principale.
        """
        log.info("MainWindow.__create_menu_bar : Création de la barre de menus")

        # Création du menu principal
        self.menu_bar = menutk.MainMenu(
            self, self.settings, self.iocontroller,
            self.viewer_container, self.taskFile
        )

        # Configuration du menu pour la fenêtre racine
        self.parent.config(menu=self.menu_bar)

    def __create_reminder_controller(self) -> None:
        """
        Crée et initialise le contrôleur de rappels pour la gestion des tâches et des efforts.
        """
        self.reminderController = remindercontrollertk.ReminderController(
            self, self.taskFile.tasks(), self.taskFile.efforts(), self.settings
        )

    def addPane(self, page, caption, name, floating: bool = False) -> None:
        """
        Ajoute un volet (pane) à la fenêtre principale.

        Args:
            page (tk.Widget): Le volet à ajouter.
            caption (str): Le titre du volet.
            name (str): Nom unique du volet.
            floating (bool): Indique si le volet doit être flottant.
        """
        if operating_system.isWayland():
            floating = False

        if not hasattr(page, 'settingsSection'):
            # Si le page n'a pas de méthode settingsSection, utiliser le name
            page.settingsSection = lambda: name

        name = page.settingsSection()
        super().addPane(page, caption, name, floating=floating)

    def __init_window(self):
        """
        Initialise la fenêtre principale de Task Coach en définissant la disposition des composants
        et en appliquant les paramètres d'affichage sauvegardés.
        """
        log.debug("MainWindow._init_window : Initialisation de la fenêtre principale")

        self.__filename = self.taskFile.filename()
        self.__setTitle()

        # Définition de l'icône
        try:
            # Essayer d'obtenir une icône de taille appropriée
            icon = artprovidertk.getIcon("taskcoach", (16, 16))
            if icon:
                self.parent.iconphoto(False, icon)
                # Garder une référence pour éviter le garbage collection
                self._icon_ref = icon
            else:
                # Essayer avec d'autres noms possibles
                for icon_name in ["taskcoach", "taskcoach16x16", "taskcoach_icon"]:
                    icon = artprovidertk.getIcon(icon_name, (16, 16))
                    if icon:
                        self.parent.iconphoto(False, icon)
                        self._icon_ref = icon
                        break
                if not icon:
                    log.warning("Icône Task Coach non trouvée")
                    self._icon_ref = None
        except Exception as e:
            log.warning(f"Impossible de définir l'icône : {e}")
            self._icon_ref = None

        # Message de bienvenue
        self.displayMessage(
            _("Welcome to %(name)s version %(version)s")
            % {"name": meta.name, "version": meta.version},
            pane=0,
        )

        log.debug("MainWindow._init_window : Fenêtre principale initialisée")

    def __init_window_components(self):
        """
        Initialise les composants principaux de la fenêtre (barre d'outils, barre d'état)
        et restaure la perspective de la fenêtre.
        """
        # Affichage de la barre d'outils
        self.showToolBar(self.settings.getvalue("view", "toolbar"))

        # Affichage de la barre de statut
        self.parent.after(100, lambda: self.showStatusBar(
            self.settings.getboolean("view", "statusbar")))

        # Restauration de la perspective
        self.__restore_perspective()

        # Réinitialisation de la position de la toolbar
        self.parent.after(100, self._resetToolbarPosition)

    def __restore_perspective(self):
        """
        Restaure la disposition des panneaux de la fenêtre (perspective) à partir des paramètres sauvegardés.
        """
        log.debug("__restore_perspective : Restauration de la perspective")

        perspective = self.settings.get("view", "perspective")

        # Vérification des différences de nombre de viewers
        try:
            for viewer_type in factorytk.viewerTypes():
                if self.__perspective_and_settings_viewer_count_differ(viewer_type):
                    perspective = ""
                    log.warning(
                        "__restore_perspective : Incompatibilité entre la perspective et les viewers"
                    )
                    break
        except Exception as e:
            log.warning(f"Erreur lors de la vérification des viewers : {e}")
            perspective = ""

        try:
            self.manager.LoadPerspective(perspective)
        except ValueError as reason:
            log.error(f"__restore_perspective : Erreur : {reason}", exc_info=True)
            if self.__splash:
                self.__splash.destroy()
            tk.messagebox.showerror(
                _("%s settings error") % meta.name,
                _("Couldn't restore the pane layout from TaskCoach.ini:\n") + str(reason) +
                _("\n\nThe default pane layout will be used.\n")
            )
            self.manager.LoadPerspective("")

        # Sur Wayland, forcer tous les panneaux flottants à s'ancrer
        if operating_system.isWayland():
            try:
                for pane in self.manager.GetAllPanes():
                    if pane.IsFloating():
                        pane.Dock()
            except Exception as e:
                log.warning(f"Erreur Wayland : {e}")

        # S'assurer que tous les panneaux sont visibles
        try:
            for pane in self.manager.GetAllPanes():
                if not pane.IsShown():
                    pane.Show()
                if hasattr(pane.window, "title"):
                    pane.Caption(pane.window.title())
                if pane.name == "toolbar":
                    best_size = pane.window.winfo_height()
                    pane.MinSize((-1, best_size))
        except Exception as e:
            log.warning(f"Erreur lors de la mise à jour des panneaux : {e}")

        self.manager.Update()

    def __perspective_and_settings_viewer_count_differ(self, viewer_type):
        """
        Vérifie si le nombre de visionneuses dans la perspective diffère de celui sauvegardé.
        """
        perspective = self.settings.get("view", "perspective")
        perspective_viewer_count = perspective.count(f"name={viewer_type}")
        settings_viewer_count = self.settings.getint("view", f"{viewer_type}count")
        return perspective_viewer_count != settings_viewer_count

    def __register_for_window_component_changes(self):
        """
        S'enregistre pour recevoir des notifications de changement de composants.
        """
        pub.subscribe(self.__onFilenameChanged, "taskfile.filenameChanged")
        pub.subscribe(self.__onDirtyChanged, "taskfile.dirty")
        pub.subscribe(self.__onDirtyChanged, "taskfile.clean")
        pub.subscribe(self.showStatusBar, "settings.view.statusbar")
        pub.subscribe(self.showToolBar, "settings.view.toolbar")

    def __onFilenameChanged(self, filename):
        """Gère les changements de nom de fichier."""
        self.__filename = filename
        self.__setTitle()

    def __onDirtyChanged(self, taskFile):
        """Gère les changements dans l'état de modification du fichier."""
        self.__dirty = taskFile.isDirty()
        self.__setTitle()

    def __setTitle(self):
        """Met à jour le titre de la fenêtre principale."""
        title = meta.name
        if self.__filename:
            title += f" - {self.__filename}"
        if self.__dirty:
            title += " *"
        self.parent.title(title)

    def displayMessage(self, message, pane=0):
        """
        Affiche un message dans la barre de statut.

        Args:
            message (str): Le message à afficher.
            pane (int): Le panneau de la barre de statut (0 par défaut).
        """
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.SetStatusText(message, pane)

    def saveSettings(self):
        """Sauvegarde les paramètres actuels de la fenêtre."""
        self.__save_viewer_counts()
        self.__save_perspective()
        self.__save_position()

    def __save_viewer_counts(self):
        """Enregistre le nombre de visionneuses pour chaque type."""
        try:
            for viewer_type in factorytk.viewerTypes():
                if hasattr(self, 'viewer_container'):
                    count = len([v for v in self.viewer_container if v.__class__.__name__.lower() == viewer_type])
                else:
                    count = 0
                self.settings.set("view", viewer_type + "count", str(count))
        except Exception as e:
            log.warning(f"Erreur lors de l'enregistrement des comptes de viewers : {e}")

    def __save_perspective(self):
        """Sauvegarde la perspective actuelle de la fenêtre."""
        try:
            perspective = self.manager.SavePerspective()
            self.settings.set("view", "perspective", perspective)
        except Exception as e:
            log.warning(f"Erreur lors de la sauvegarde de la perspective : {e}")

    def __save_position(self) -> None:
        """Sauvegarde la position et la taille actuelles de la fenêtre."""
        try:
            self.__dimensions_tracker.save_position()
        except Exception as e:
            log.warning(f"Erreur lors de la sauvegarde de la position : {e}")

    def closeEditors(self) -> None:
        """Ferme tous les éditeurs ouverts dans la fenêtre principale."""
        log.info("MainWindow.closeEditors : Fermeture des éditeurs")
        try:
            # Pour Tkinter, il faut parcourir toutes les fenêtres enfants
            for child in self.parent.winfo_children():
                if isinstance(child, Editor):
                    child.Close()
        except Exception as e:
            log.exception(f"MainWindow.closeEditors : Erreur : {e}")

    def checkXFCE4(self):
        """
        Vérifie si l'utilisateur utilise le gestionnaire de fenêtres XFCE4.
        """
        log.info("MainWindow : Vérification de l'utilisation de XFCE4")
        if operating_system.isGTK():
            # À implémenter si nécessaire
            pass

    def setShutdownInProgress(self) -> None:
        """Indique que le processus d'arrêt de l'application est en cours."""
        log.info("MainWindow.setShutdownInProgress : Arrêt en cours")
        self.__shutdown = True

    def onClose(self):
        """
        Gère la fermeture de la fenêtre.
        """
        log.info("MainWindow.onClose : Fermeture de la fenêtre")

        try:
            app_instance = application.tkapplication.TkinterApplication.getInstance()
            should_quit = app_instance.quitApplication(force=True)
            should_hide = self.settings.getboolean("window", "hidewhenclosed")

            self.__save_perspective()
            self.__save_position()
            self.closeEditors()

            if should_quit or self.__shutdown:
                log.debug("MainWindow.onClose: Quitter l'application")
                self.taskFile.stop()
                self._idleController.stop()
                self.parent.destroy()
            elif should_hide:
                log.debug("MainWindow.onClose: Fenêtre cachée")
                self.parent.withdraw()
            else:
                log.debug("MainWindow.onClose: Fermeture par défaut")
                self.__save_perspective()
                self.__save_position()
                self.saveSettings()
                self.taskFile.stop()
                self._idleController.stop()
                self.parent.destroy()
        except Exception as e:
            log.exception(f"MainWindow.onClose : Erreur : {e}")

        self._idleController.stop()
        log.info("MainWindow.onClose: Fenêtre fermée")

    def show(self):
        """Affiche la fenêtre."""
        self.parent.deiconify()
        self.parent.lift()

    def onIconify(self, event=None):
        """
        Gère la minimisation de la fenêtre.
        """
        try:
            if self.parent.state() == "iconic":
                if self.settings.getboolean("window", "hidewheniconized"):
                    self.parent.withdraw()
                    log.debug("MainWindow.onIconify: Fenêtre iconifiée et cachée")
                    self._is_hidden_when_iconized = True
                else:
                    self._is_hidden_when_iconized = False
            else:
                self._is_hidden_when_iconized = False
        except Exception as e:
            log.warning(f"Erreur dans onIconify : {e}")

    def onResize(self, event=None):
        """
        Gère le redimensionnement de la fenêtre.
        """
        if self._handling_resize:
            return

        self._handling_resize = True
        new_width = self.parent.winfo_width()
        new_height = self.parent.winfo_height()

        self.parent.after(10, lambda: setattr(self, "_handling_resize", False))
        log.debug(f"MainWindow.onResize: Fenêtre redimensionnée à {new_width}x{new_height}")

        # Mise à jour du lastSize pour éviter les redimensionnements répétés
        if not hasattr(self, "_lastSize"):
            self._lastSize = (new_width, new_height)

        if (new_width, new_height) != self._lastSize:
            self._lastSize = (new_width, new_height)
            log.info(f"MainWindow.onResize: Nouvelle taille enregistrée: {new_width}x{new_height}")

        # Mise à jour du manager AUI
        self.manager.Update()

    def showStatusBar(self, value: bool = True) -> None:
        """
        Affiche ou masque la barre de statut.

        Args:
            value (bool): True pour afficher, False pour masquer.
        """
        log.debug(f"MainWindow.showStatusBar : Affichage de la barre de statut : {value}")

        if hasattr(self, 'status_bar') and self.status_bar:
            # Pour Tkinter, on utilise pack_forget ou pack
            if value:
                self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            else:
                self.status_bar.pack_forget()

    def createToolBarUICommands(self):
        """
        Crée les commandes UI à afficher dans la barre d'outils.

        Returns:
            list: Une liste d'instances de commandes UI.
        """
        log.debug("MainWindow.createToolBarUICommands: Création des commandes UI")

        uiCommands = [
            uicommand.FileOpen(iocontroller=self.iocontroller),
            uicommand.FileSave(iocontroller=self.iocontroller),
            uicommand.FileMergeDiskChanges(iocontroller=self.iocontroller),
            uicommand.Print(viewer=self.viewer_container, settings=self.settings),
            None,
            uicommand.EditUndo(),
            uicommand.EditRedo(),
        ]

        uiCommands.extend([
            None,
            uicommand.EffortStartButton(taskList=self.taskFile.tasks()),
            uicommand.EffortStop(
                viewer=self.viewer_container,
                effortList=self.taskFile.efforts(),
                taskList=self.taskFile.tasks(),
            ),
        ])

        return uiCommands

    def getToolBarPerspective(self):
        """
        Retourne la perspective actuelle de la barre d'outils.

        Returns:
            str: La perspective de la barre d'outils.
        """
        return self.settings.get("view", "toolbarperspective")

    def saveToolBarPerspective(self, perspective):
        """
        Sauvegarde la perspective de la barre d'outils.

        Args:
            perspective (str): La perspective à sauvegarder.
        """
        self.settings.set("view", "toolbarperspective", perspective)

    def showToolBar(self, value) -> None:
        """
        Affiche ou cache la barre d'outils.

        Args:
            value: Si False, cache la barre. Sinon, affiche avec la taille spécifiée.
        """
        log.debug(f"MainWindow.showToolBar : Affichage de la barre d'outils : {value}")

        # Vérifier si une barre d'outils existe déjà
        currentToolbar = self.manager.GetPane("toolbar")
        if currentToolbar.IsOk():
            self.manager.DetachPane(currentToolbar.window)
            currentToolbar.window.destroy()

        if value:
            # Création de la nouvelle barre d'outils
            bar = toolbarttk.MainToolBar(self, self.settings, size=value)

            # Ajout au manager AUI
            self.addPane(
                bar,
                caption=_("Toolbar"),
                name="toolbar",
                floating=False
            )

            # Masquer la poignée
            self.parent.after(100, lambda: bar.SetGripperVisible(False))

        self.manager.Update()

    def onCloseToolBar(self, event=None) -> None:
        """
        Gère la fermeture de la barre d'outils.

        Args:
            event: L'événement de fermeture.
        """
        log.debug("MainWindow.onCloseToolBar : Fermeture de la barre d'outils")
        try:
            self.settings.setvalue("view", "toolbar", None)
        except Exception as e:
            log.exception(f"MainWindow.onCloseToolBar : Erreur : {e}")

    def _resetToolbarPosition(self):
        """Réinitialise la position de la toolbar."""
        pane = self.manager.GetPane("toolbar")
        if not pane.IsOk() or pane.IsFloating():
            return

        direction = pane.dock_direction
        if direction not in (1, 2, 3, 4):  # top, right, bottom, left
            return

        if pane.dock_pos != 0:
            pane.Position(0)
            if direction in (1, 3):  # top/bottom
                pane.MinSize((self.parent.winfo_width(), -1))
            else:  # left/right
                pane.MinSize((-1, self.parent.winfo_height()))
            self.manager.Update()

    def _onAuiRender(self, event):
        """Détecte le rendu AUI pour réinitialiser la position."""
        # Pour l'AUI Tkinter, on peut utiliser un système de tracking des actions
        # Cela dépend de l'implémentation spécifique de tk3rdparty.aui_ttk
        try:
            action = getattr(self.manager, "_action", 0)
            prev_action = getattr(self, "_prev_manager_action", 0)

            # Détecter la transition de drag à idle
            if prev_action != 0 and action == 0:
                self.parent.after(100, self._resetToolbarPosition)

            # Détecter la transition floating->docked
            pane = self.manager.GetPane("toolbar")
            if pane.IsOk():
                was_floating = getattr(self, "_toolbar_was_floating", False)
                is_floating = pane.IsFloating()
                if was_floating and not is_floating:
                    self.parent.after(100, self._resetToolbarPosition)
                self._toolbar_was_floating = is_floating

            self._prev_manager_action = action
        except Exception as e:
            log.debug(f"_onAuiRender : {e}")

    def advanceSelection(self, forward) -> None:
        """
        Fait avancer la sélection des tâches dans les visionneuses.

        Args:
            forward (bool): Si True, avance vers l'élément suivant.
        """
        log.debug(f"MainWindow.advanceSelection: Avance la sélection (forward: {forward})")
        self.viewer_container.advanceSelection(forward)

    def viewerCount(self) -> int:
        """
        Retourne le nombre actuel de visionneuses actives.

        Returns:
            int: Le nombre de visionneuses.
        """
        return len(self.viewer_container)

    def OnPowerState(self, state) -> None:
        """
        Gère les changements d'état d'alimentation.

        Args:
            state: L'état de l'alimentation.
        """
        from taskcoachlib.powermgt import PowerStateMixin
        if state == PowerStateMixin.POWERON:
            pub.sendMessage("powermgt.on")
        else:
            pub.sendMessage("powermgt.off")

    # Méthodes pour iPhone (à implémenter si nécessaire)
    def createIPhoneProgressFrame(self):
        """Crée une fenêtre de progression pour la synchronisation iPhone."""
        # À implémenter
        pass

    def getIPhoneSyncType(self, guid):
        """Détermine le type de synchronisation iPhone."""
        # À implémenter
        pass

    def notifyIPhoneProtocolFailed(self) -> None:
        """Affiche un message d'erreur pour l'échec du protocole iPhone."""
        # À implémenter
        pass

    def clearTasks(self) -> None:
        """Efface toutes les tâches actuellement affichées."""
        self.taskFile.clear(False)
        log.info("MainWindow.clearTasks : Toutes les tâches ont été effacées")

    def restoreTasks(self, categories, tasks) -> None:
        """
        Restaure les catégories et tâches dans le fichier de tâches.

        Args:
            categories: Liste des catégories à restaurer.
            tasks: Liste des tâches à restaurer.
        """
        log.debug(f"MainWindow.restoreTasks : Restauration de {len(categories)} catégories et {len(tasks)} tâches")
        self.taskFile.clear(False)
        self.taskFile.categories().extend(categories)
        self.taskFile.tasks().extend(tasks)

    # Méthodes pour la gestion des catégories et tâches iPhone
    def addIPhoneCategory(self, category) -> None:
        """Ajoute une catégorie synchronisée depuis un iPhone."""
        log.info(f"Catégorie iPhone ajoutée : {category}")
        self.taskFile.categories().append(category)

    def removeIPhoneCategory(self, category) -> None:
        """Supprime une catégorie synchronisée avec un iPhone."""
        log.info(f"MainWindow.removeIPhoneCategory : Catégorie iPhone supprimée : {category}")
        self.taskFile.categories().remove(category)

    def modifyIPhoneCategory(self, category, name) -> None:
        """Modifie le nom d'une catégorie synchronisée depuis un iPhone."""
        log.info(f"Catégorie {category} iPhone modifiée, nouveau nom : {name}")
        category.setSubject(name)

    def addIPhoneTask(self, task, categories) -> None:
        """Ajoute une tâche synchronisée depuis un iPhone."""
        log.info(f"Tâche iPhone {task} ajoutée avec {len(categories)} catégories")
        self.taskFile.tasks().append(task)
        for category in categories:
            task.addCategory(category)
            category.addCategorizable(task)

    def removeIPhoneTask(self, task) -> None:
        """Supprime une tâche synchronisée depuis un iPhone."""
        log.info(f"Tâche iPhone supprimée : {task}")
        self.taskFile.tasks().remove(task)

    def addIPhoneEffort(self, task, effort) -> None:
        """Ajoute un effort à une tâche synchronisée depuis un iPhone."""
        log.info(f"Effort iPhone {effort} ajouté à la tâche {task}")
        if task is not None:
            task.addEffort(effort)

    def modifyIPhoneEffort(self, effort, subject, started, ended) -> None:
        """Modifie un effort synchronisé depuis un iPhone."""
        log.info(f"MainWindow.modifyIPhoneEffort: Effort iPhone {effort} modifié")
        effort.setSubject(subject)
        effort.setStart(started)
        effort.setStop(ended)

    def modifyIPhoneTask(self, task, subject, description, plannedStartDateTime,
                         dueDateTime, completionDateTime, reminderDateTime,
                         recurrence, priority, categories) -> None:
        """Modifie une tâche synchronisée depuis un iPhone."""
        log.info(f"Tâche iPhone modifiée : {task}")
        task.setSubject(subject)
        task.setDescription(description)
        task.setPlannedStartDateTime(plannedStartDateTime)
        task.setDueDateTime(dueDateTime)
        task.setCompletionDateTime(completionDateTime)
        task.setReminder(reminderDateTime)
        task.setRecurrence(recurrence)
        task.setPriority(priority)

        if categories is not None:
            for toRemove in task.categories() - categories:
                task.removeCategory(toRemove)
                toRemove.removeCategorizable(task)

            for toAdd in categories - task.categories():
                task.addCategory(toAdd)
                toAdd.addCategorizable(task)

    def restore(self, event=None) -> None:
        """
        Restaure la fenêtre principale à partir de la barre des tâches.
        """
        if self.settings.getboolean("window", "maximized"):
            self.parent.state('zoomed')  # Pour Windows
        self.parent.deiconify()
        self.parent.lift()
