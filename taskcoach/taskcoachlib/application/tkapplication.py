# -*- coding: utf-8 -*-
"""
Ce fichier est une version simplifiée et convertie vers tkinter
de l'application originale de Task Coach qui utilisait wxPython.

NOTE IMPORTANTE : Il ne s'agit pas d'une conversion 1:1, car les
architectures de wxPython et tkinter sont fondamentalement différentes.
De nombreuses fonctionnalités complexes de wxPython (comme l'icône de
la barre des tâches, la gestion des sessions et l'intégration de Twisted)
n'ont pas d'équivalent direct dans tkinter et ont été supprimées ou
"maquettées" pour des raisons de démonstration.
"""
# En général, il n'est pas recommandé de faire de TkinterApplication un enfant de tkinter.Tk. Voici pourquoi :
#
# Le design actuel de votre code utilise le principe de composition. Cela signifie que votre classe TkinterApplication possède une fenêtre principale (self.root = tk.Tk()), mais n'est pas elle-même la fenêtre. C'est une approche solide pour plusieurs raisons :
#
#     Séparation des préoccupations : TkinterApplication est la logique de l'application (paramètres, gestion des fichiers, etc.), tandis que self.root est la représentation graphique de l'interface utilisateur. En les séparant, votre code est plus propre et plus facile à comprendre.
#
#     Modularité et flexibilité : En cas de besoin, vous pourriez potentiellement utiliser la même logique de classe TkinterApplication avec un autre framework d'interface graphique (comme PyQt ou PyGTK) en changeant simplement la partie qui gère l'interface, sans avoir à réécrire toute la logique métier.
#
#     Héritage multiple : Si vous faisiez hériter TkinterApplication de tk.Tk, vous pourriez rencontrer des problèmes si vous aviez besoin d'hériter également d'une autre classe pour d'autres fonctionnalités (bien que cela soit moins courant en Python).
#
# Votre conception actuelle imite la structure de l'application originale wxPython, où l'objet wx.App est distinct de la fenêtre principale (wx.Frame). C'est un modèle de conception éprouvé pour les applications de bureau.
#
# Faire hériter TkinterApplication de tk.Tk (le principe d'héritage) pourrait sembler plus simple au premier abord, mais cela lierait de manière rigide votre logique d'application à un type de widget spécifique, ce qui est généralement considéré comme un couplage serré et peut compliquer la maintenance future.

import logging
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import Menu
import threading
import re
import locale
import calendar

# Importer les classes nécessaires de votre bibliothèque d'application.
# Notez que ces modules sont supposés avoir été mis à jour pour fonctionner avec tkinter.
from taskcoachlib import operating_system, patterns, persistencetk, operating_system, meta, i18n
from taskcoachlib.i18n import _
from taskcoachlib.config.settings import Settings
from taskcoachlib.domain import date
from taskcoachlib import guitk
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.guitk import mainwindowtk
from taskcoachlib.guitk import iocontrollertk
# Remplacement de la création de IdleController par:
from taskcoachlib.powermgt import idletk

log = logging.getLogger(__name__)


# Maquette de la classe RedirectedOutput car elle utilise wx.MessageBox
class RedirectedOutput:
    _rx_ignore = [
        re.compile('RuntimeWarning: PyOS_InputHook'),
    ]

    def __init__(self):
        self.__handle = None
        # Simuler un chemin de fichier de log
        # self.__path = os.path.join(os.path.expanduser('~'), 'taskcoachlog.txt')
        self.__path = os.path.join(Settings.pathToDocumentsDir(), "taskcoachlog.txt")

    def write(self, bf):
        for rx in self._rx_ignore:
            if rx.search(bf):
                return

        if self.__handle is None:
            # Créer le fichier de log
            try:
                self.__handle = open(self.__path, 'a+')
                self.__handle.write('============= %s\n' % time.ctime())
            except IOError:
                # Si le fichier ne peut pas être ouvert, ne rien faire
                self.__handle = None
                return
        self.__handle.write(bf)

    def flush(self):
        # Assure que la sortie est bien vidée
        pass

    def close(self):
        """Fonction-méthode pour fermer taskcoachlig.txt"""
        # si l'Argument-fichier à utiliser existe, le fermer et le rendre inaccessible.
        if self.__handle is not None:
            self.__handle.close()
            self.__handle = None

    def summary(self):
        """
        Fonction-méthode pour afficher une info sur
        ce qu'il vient d'être écrit dans taskcoachlog.txt.
        """
        if self.__handle is not None:
            self.close()
            # Utiliser messagebox de tkinter au lieu de wx.MessageBox
            messagebox.showerror('Erreur',
                                 f'Des erreurs se sont produites. Veuillez consulter le fichier "{self.__path}".')


# class TkinterApplication:
class TkinterApplication(metaclass=patterns.Singleton):  # Utilise la métaclasse Singleton
    """
    Classe principale de l'application utilisant Tkinter.

    Singleton Encapsule l'instance Tkinter et simplifie la gestion.
    """
    # # La classe Application originale utilisait un métaclass Singleton.
    # # On la simule ici.
    # __instance = None  # Retirer l'attribut de classe car il est géré par la métaclasse.
    #
    # def __new__(cls, *args, **kwargs):
    #     if TkinterApplication.__instance is None:
    #         TkinterApplication.__instance = object.__new__(cls)  # Crée l'instance si elle n'existe pas
    #     return TkinterApplication.__instance

    def __init__(self, options=None, args=None, **kwargs):
        if hasattr(self, 'initialized'):  # Prevent multiple initializations
            return
        self.initialized = True

        # Créer la fenêtre racine (root)
        self.root = tk.Tk()
        self.root.title(meta.name)
        self.root.geometry("800x600")
        # self.root.protocol("WM_DELETE_WINDOW", self.on_end_session)  # Mis dans init !

        # super().__init__()
        # log.info("TkinterApplication : Initialisation de l'application Tkinter.")
        # self.settings = Settings(load=True)  # Définit dans __init_config
        # self.mainwindow = None # Stocker l'instance de MainWindow
        # self.protocol("WM_DELETE_WINDOW", self.quit)  # Gérer la fermeture via la croix
        # #if self.settings.getboolean("window", "maximized"):
        # self.geometry("800x600")
        # log.debug("TkinterApplication : init_config : Appel de init_config")
        # self.init_config()
        # log.debug("TkinterApplication : init_config : passé avec succès !")
        # self.title(_("Task Coach"))
        #
        # try:
        #     from taskcoachlib.guitk import mainwindowtk
        #     log.debug("TkinterApplication : Init de mainwindow")
        #     self.mainwindow = mainwindowtk.MainWindow(self, None, None, self.settings)  # Passe self (Tk) comme parent
        #     #self.mainwindow.pack(fill=tk.BOTH, expand=True)
        #     self.configure(menu=self.mainwindow.menu_bar) # Configurer le menu
        #     #self.test_button = tk.Button(self, text="Test", command=self.test_command)
        #     #self.test_button.pack()
        # except Exception as e:
        #     log.error(f"TkinterApplication : init : ERREUR APRES : {e}")

        self._options = options
        self._args = args
        # self.settings = None  # Définit dans __init_config
        self.taskFile = None
        self.iocontroller = None
        self.mainwindow = None
        self.sessionMonitor = None
        self.taskBarIcon = None

        # Maquette de l'initialisation de Twisted.
        # Dans tkinter, il faudrait utiliser un réacteur Twisted compatible avec tkinter.
        # Un exemple serait `from twisted.internet.tkreactor import install; install()`
        # mais la logique de cette classe est bien plus complexe.
        self.stoptwisted = lambda: print("Twisted a été arrêté (maquette) en simulation")
        self.initTwisted = lambda: print("Twisted a été initialisé (maquette) en simulation")
        self.registerApp = lambda: print("L'application a été enregistrée auprès de Twisted (maquette) en simulation.")

        self.initTwisted()
        # self.registerApp()
        self.init(**kwargs)

        # Remplacement de l'initialisation du sessionMonitor
        if operating_system.isGTK():
            # self.sessionMonitor = None  # A remplacer par une solution compatible si nécessaire
            if self.settings.getboolean("feature", "usesm2"):
                from taskcoachlib.powermgt import xsm

                class LinuxSessionMonitor(xsm.SessionMonitor):
                    def __init__(self, callback):
                        super().__init__()
                        self._callback = callback
                        self.setProperty(xsm.SmCloneCommand, sys.argv)
                        self.setProperty(xsm.SmRestartCommand, sys.argv)
                        self.setProperty(xsm.SmCurrentDirectory, os.getcwd())
                        self.setProperty(xsm.SmProgram, sys.argv[0])
                        self.setProperty(xsm.SmRestartStyleHint, xsm.SmRestartNever)

                    def saveYourself(
                        self, saveType, shutdown, interactStyle, fast
                    ):  # pylint: disable=W0613
                        if shutdown:
                            # wx.CallAfter(self._callback)
                            self.root.after_idle(self._callback)
                        self.saveYourselfDone(True)

                    def die(self):
                        pass

                    def saveComplete(self):
                        pass

                    def shutdownCancelled(self):
                        pass

                self.sessionMonitor = LinuxSessionMonitor(
                    self.on_end_session
                )  # pylint: disable=W0201
        else:
            self.sessionMonitor = None

        # Remplacement de calendar.setfirstweekday
        calendar.setfirstweekday(dict(monday=0, sunday=6).get(self.settings.get('view', 'weekstart'), 0))
        calendar.setfirstweekday(
            dict(monday=0, sunday=6)[self.settings.get("view", "weekstart")]
        )

    def start(self):
        """
        Démarre l'application.

        Démarrer la boucle principale de l'application Tkinter.
        """
        # Remplacer les vérificateurs de version et de messages
        if self.settings.getboolean('version', 'notify'):
            print("Vérificateur de version démarré (maquette)")
        if self.settings.getboolean('view', 'developermessages'):
            print("Vérificateur de messages de développeur démarré (maquette)")

        self.__copy_default_templates()
        # self.mainwindow.show()  # On suppose que la classe MainWindow a une méthode show() (tk.lift())
        # Le Taskviewer ne s'affiche pas car la fenêtre principale (MainWindow) elle-même n'est pas correctement positionnée et affichée dans la fenêtre racine de Tkinter. Le programme crée tous les composants internes, y compris le Taskviewer, mais il ne les affiche pas car il manque une instruction de géométrie pour la fenêtre principale.
        #
        # Pour résoudre ce problème, vous devez ajouter une ligne de code pour positionner la fenêtre principale après sa création.
        #
        # Solution
        #
        # Pour que la fenêtre principale s'affiche, suivez ces étapes :
        #
        #     Ouvrez le fichier tkapplication.py.
        #
        #     Dans la méthode start(), ajoutez la ligne self.mainwindow.pack(...) pour l'afficher et la positionner dans la fenêtre racine.
        # La création de la fenêtre principale n'a pas lieu dans la méthode __init__(), mais plutôt dans la méthode start().
        #
        # La méthode __init__() crée et configure les éléments de base de l'application, comme la fenêtre racine (self.root). C'est la méthode start() qui est responsable de l'initialisation de l'interface utilisateur plus complexe, notamment la création de la MainWindow.
        #
        # Pour que le programme fonctionne correctement, vous ne devez pas appeler self.init(**kwargs) dans start(), car la méthode __init__() est un constructeur qui n'est appelé qu'une seule fois lorsque l'objet est créé. L'appeler à nouveau serait incorrect.
        #
        # La solution consiste à s'assurer que les lignes qui créent et positionnent le MainWindow sont bien placées à l'intérieur de la méthode start(), comme dans l'exemple que je vous ai donné précédemment.
        log.info("Lancement de l'application Tkinter...")

        # # Crée la fenêtre principale
        # self.mainwindow = mainwindowtk.MainWindow(self.root, self.iocontroller, self.taskFile, self.settings)
        #
        # # C'est la ligne essentielle qui manquait pour afficher la fenêtre.
        # # Utilisez .pack(), .grid() ou .place() pour positionner le widget.
        # self.mainwindow.pack(fill="both", expand=True)
        # Finalement, c'est init qui lance mainwindow !

        # Lancement de la boucle principale de Tkinter.
        # Sans cet appel, la fenêtre ne serait pas interactive, et l'application resterait figée.
        # C'est cette boucle qui écoute les événements (clics, mouvements de souris, etc.)
        # et qui gère le rendu visuel de l'interface. Sans elle, rien ne s'affiche à l'écran.
        # En Tkinter, cette boucle est généralement lancée par la méthode mainloop() que l'on appelle sur l'objet de la fenêtre principale.
        #
        # Pour que tout fonctionne correctement, il faut donc que l'objet de la fenêtre principale existe, et que la méthode mainloop() soit appelée sur cet objet.
        # Maintenant, nous avons établi les points suivants :
        #
        #     Le cadre principal s'affiche.
        #
        #     La barre de menu ne s'affichait pas, car elle n'est pas un widget normal qui se positionne avec .pack(), mais elle se configure avec parent.config(menu=self).
        #
        #     Les autres widgets comme la barre d'état ou le conteneur des visionneuses sont bien créés et ont bien un appel à .pack() dans leur méthode _create_window_components.
        #
        #     La boucle principale de Tkinter est bien lancée via self.root.mainloop().
        #
        # Si tous les éléments sont créés et qu'ils sont bien "packés" dans la fenêtre, pourquoi ne s'affichent-ils pas ? 🤔
        #
        # Il est possible que le problème ne vienne pas de la création ou du positionnement des widgets, mais de la manière dont la fenêtre principale est structurée.
        self.root.mainloop()  # Lance la boucle principale de l'application

    def __copy_default_templates(self):
        """ Copier les modèles par défaut """
        # Logique de la copie des modèles (maquettée)
        print("Modèles par défaut copiés (maquette)")

    def init(self, loadSettings=True, loadTaskFile=True):
        """ Initialise l'application. """
        # Initialisation des réglages
        self.__init_config(loadSettings)
        self.__init_language()
        self.__init_domain_objects()
        self.__init_application()

        # # Maquette des classes gui et persistence
        # class MockGUI:
        #     def init(self): pass
        #     class SplashScreen:
        #         def __init__(self): print("Écran de démarrage affiché (maquette)")
        #         def Destroy(self): print("Écran de démarrage détruit (maquette)")
        # class MockPersistence:
        #     class LockedTaskFile:
        #         def __init__(self, poll): pass
        #     class AutoSaver:
        #         def __init__(self, settings): pass
        #     class AutoImporterExporter:
        #         def __init__(self, settings): pass
        #     class AutoBackup:
        #         def __init__(self, settings): pass

        # gui = MockGUI()
        # persistence = MockPersistence()

        guitk.init()
        show_splash_screen = self.settings.getboolean('window', 'splash')
        splash = guitk.SplashScreen(self.root) if show_splash_screen else None

        # self.taskFile = persistencetk.LockedTaskFile(poll=not self.settings.getboolean('file', 'nopoll'))
        self.taskFile = persistencetk.LockedTaskFile(parent=self.root, poll=not self.settings.getboolean('file', 'nopoll'))
        # self.__auto_saver = persistence.AutoSaver(self.settings)
        # self.__auto_exporter = persistence.AutoImporterExporter(self.settings)
        # self.__auto_backup = persistence.AutoBackup(self.settings)

        # La classe IOController et MainWindow devraient être réécrites pour tkinter.
        # Ici, nous les maquettons.
        # class MockIOController:
        #     def __init__(self, taskFile, displayMessage, settings, splash): pass
        #     def close(self, force): return True
        #     def openAfterStart(self, args): pass

        # class MockMainWindow:
        #     def __init__(self, iocontroller, taskFile, settings, splash):
        #         self.root = tk.Toplevel(self.root)
        #         self.root.title("Fenêtre principale (maquette)")
        #         self.root.protocol("WM_DELETE_WINDOW", iocontroller.close)
        #     def show(self): pass
        #     def saveSettings(self): pass
        #     def setShutdownInProgress(self): pass
        #     def displayMessage(self, message): print(f"Message affiché: {message}")
        #     def OnQuit(self): pass
        #     def create_menu(self):
        #         menu_bar = Menu(self.root)
        #         self.root.config(menu=menu_bar)
        #         file_menu = Menu(menu_bar, tearoff=0)
        #         menu_bar.add_cascade(label="Fichier", menu=file_menu)
        #         file_menu.add_command(label="Quitter", command=self.on_quit)
        #
        #     def on_quit(self):
        #         self.root.destroy()

        # self.iocontroller = MockIOController(self.taskFile, self.displayMessage, self.settings, splash)
        self.iocontroller = guitk.iocontrollertk.IOController(self.root, self.taskFile, self.displayMessage, self.settings, splash)
        # self.mainwindow = MockMainWindow(self.iocontroller, self.taskFile, self.settings, splash)
        # self.mainwindow = guitk.MainWindow(self.root, self.iocontroller, self.taskFile, self.settings, splash)  # A Frame is a top-level window.
        # Créez et packez l'instance de MainWindow dans la fenêtre racine
        # app = MainWindow(root, mock_iocontroller, mock_taskfile, mock_settings)
        # app = self.mainwindow = guitk.MainWindow(self.root, self.iocontroller, self.taskFile, self.settings)
        self.mainwindow = guitk.mainwindowtk.MainWindow(self.root, self.iocontroller, self.taskFile, self.settings)
        # app.pack(fill=tk.BOTH, expand=True)
        self.mainwindow.pack(fill=tk.BOTH, expand=True)
        # mainwindow est déjà instancié dans start mais

        # Liez les événements de la fenêtre racine à l'instance de MainWindow
        # self.root.protocol("WM_DELETE_WINDOW", app.onClose)
        self.root.protocol("WM_DELETE_WINDOW", self.mainwindow.onClose)
        # self.root.bind("<Unmap>", app.onIconify)
        self.root.bind("<Unmap>", self.mainwindow.onIconify)
        # self.root.bind("<Configure>", app.onResize)
        self.root.bind("<Configure>", self.mainwindow.onResize)

        # Définir l'icône de la fenêtre racine
        # self.root.iconphoto(False, artprovider.iconBundle("taskcoach"))
        # self.root.iconphoto(False, artprovidertk.iconBundle("taskcoach"))  # TODO : problème d'Image non trouvée !

        # Initialize IdleNotifier *after* MainWindow  -> A mettre dans une méthode !
        self.idle_notifier = idletk.IdleNotifier(root=self.root, min_idle_time=self.settings.getint("feature", "minidletime") * 60)  # Minutes to seconds

        # self.idle_controller = guitk.idlecontroller.IdleController(mainWindow=app, settings=self.settings, effortList=self.taskFile.efforts())  # a verif l'ordre des arguments !
        self.idle_controller = guitk.idlecontrollertk.IdleController(mainWindow=self.mainwindow, settings=self.settings, effortList=self.taskFile.efforts())  # a verif l'ordre des arguments !
        self.idle_notifier.start()  # Démarrer la surveillance !

        # self.__wx_app.SetTopWindow(self.mainwindow) n'a pas d'équivalent direct
        self.__init_spell_checking()
        if not self.settings.getboolean('file', 'inifileloaded'):
            self.__close_splash(splash)
            self.__warn_user_that_ini_file_was_not_loaded()
        if loadTaskFile:
            self.iocontroller.openAfterStart(self._args)
        self.__register_signal_handlers()
        self.__create_mutex()
        self.__create_task_bar_icon()

        # Remplacer wx.CallAfter par root.after_idle
        self.root.after_idle(lambda: self.__close_splash(splash))
        self.root.after_idle(self.__show_tips)

    def __init_config(self, load_settings) -> None:
        """
        Initialisation des réglages.

        Args:
            load_settings:

        Attributes:
            self.settings (Settings) : Objet paramètres

        Returns:
            None
        """
        ini_file = self._options.inifile if self._options else None
        self.settings = Settings(load_settings, ini_file)
        # self.settings.load()  # AttributeError: 'Settings' object has no attribute 'load'
        log.info("init_config : passé avec succès !")

    def __init_language(self):
        # i18n.Translator(self.determine_language(self._options, self.settings))  # Problème import wx
        pass

    @staticmethod
    def determine_language(options, settings, locale=locale):
        # La logique de détermination de la langue est inchangée
        language = None
        if options:
            language = options.pofile or options.language
        if not language:
            language = settings.get('view', 'language_set_by_user')
        if not language:
            language = settings.get('view', 'language')
        if not language:
            language = locale.getdefaultlocale()[0]
            if language == 'C':
                language = None
        if not language:
            language = 'en_US'
        return language

    def __init_domain_objects(self):
        from taskcoachlib.domain import task, attachment
        task.Task.settings = self.settings
        attachment.Attachment.settings = self.settings

    def __init_application(self):
        # Tkinter n'a pas de SetAppName/SetVendorName
        pass

    def __init_spell_checking(self):
        # Cette fonctionnalité est spécifique à macOS et wxPython.
        # Elle est supprimée pour tkinter.
        pass

    def __register_signal_handlers(self):
        # La gestion des signaux est spécifique au système d'exploitation et au toolkit.
        # Cette logique devrait être réécrite si nécessaire.
        pass

    @staticmethod
    def __create_mutex():
        # La création d'un mutex est spécifique à Windows et non prise en charge par tkinter.
        pass

    def __create_task_bar_icon(self):
        # La création d'une icône dans la barre des tâches n'est pas une fonctionnalité native de tkinter.
        # Des bibliothèques tierces comme 'pystray' seraient nécessaires.
        if self.__can_create_task_bar_icon():
            print("Icône de la barre des tâches non créée car elle n'est pas prise en charge par tkinter.")
        self.taskBarIcon = None

    def __can_create_task_bar_icon(self):
        return False

    @staticmethod
    def __close_splash(splash):
        if splash:
            # splash.Destroy()
            splash.close_splash()

    def __show_tips(self):
        if self.settings.getboolean('window', 'tips'):
            from taskcoachlib import help
            help.showTips(self.mainwindow, self.settings)

    def __warn_user_that_ini_file_was_not_loaded(self):
        from taskcoachlib import meta
        reason = self.settings.get('file', 'inifileloaderror')
        # Utiliser messagebox de tkinter
        messagebox.showerror(f'{meta.name} erreur de fichier',
                             f"Impossible de charger les paramètres depuis TaskCoach.ini:\n{reason}")
        self.settings.setboolean('file', 'inifileloaded', True)

    def displayMessage(self, message):
        self.mainwindow.displayMessage(message)

    # def on_end_session(self):
    def on_end_session(self, *args, **kwargs):
        """
        Gère la fin de la session, appelée lorsque l'utilisateur ferme la fenêtre.
        """
        logging.info("Arrêt de la session.")
        # self.quitApplication(force=True)
        self.OnQuit()  # Appelle la méthode OnQuit pour gérer les arrêts de services
        self.mainwindow.onClose()  # Appelle la méthode de fermeture de MainWindow

        # Cette ligne est essentielle pour fermer la fenêtre Tkinter
        self.root.destroy()
        self.parent.destroy()
        return True

    def on_reopen_app(self):
        # Cette fonctionnalité est liée à l'icône de la barre des tâches et n'est pas applicable.
        print("La fonctionnalité de réouverture d'application n'est pas prise en charge.")

    def quitApplication(self, force=False):
        """
         Quitte l'application et enregistre tout.
         :param force: S'il faut forcer la fermeture même s'il y a des modifications non sauvegardées.
         :return: True si l'application peut se fermer, False sinon.
         """
        if self.taskFile.isDirty() and not force:
            pass  # Gérer la boîte de dialogue de sauvegarde ici

        if not self.iocontroller.close(force=force):
            return False

        self.settings.set('file', 'lastfile', self.taskFile.lastFilename())
        # self.mainwindow.save_settings()
        # self.mainwindow.saveSettings()  # Crée une boucle !
        # La méthode saveSettings est une méthode d'instance de la classe MainWindow,
        # pas une méthode statique de la classe guitk.MainWindow.
        # guitk.MainWindow.saveSettings(self)
        # self.saveSettings()
        self.settings.save()

        # Suppression des composants wxPython
        if hasattr(self, 'taskBarIcon') and self.taskBarIcon is not None:
            # self.taskBarIcon.RemoveIcon()
            pass
        # if self.mainwindow and hasattr(self.mainwindow, 'bonjourRegister') and self.mainwindow.bonjourRegister is not None:
        #     self.mainwindow.bonjourRegister.stop()
        if hasattr(self, 'bonjourRegister') and self.bonjourRegister is not None:
            self.bonjourRegister.stop()

        date.Scheduler().shutdown()

        # Enregistrement du fichier de tâches avant de quitter
        self.taskFile.close()

        # self.mainwindow.OnQuit()
        self.OnQuit()

        # # if operating_system.isGTK() and self.sessionMonitor is not None:
        # if operating_system.isGTK() and self.sessionMonitor:
        #     self.sessionMonitor.stop()
        if operating_system.isGTK():
            pass  # self.on_quit()  # TODO : Peut-être brutal !!!

        # Remplacement de RedirectedOutput.summary()
        if isinstance(sys.stdout, RedirectedOutput):
            sys.stdout.summary()

        # self.stoptwisted()  # N'existe pas
        # Attention risque de boucle avec MainWindow.onClose()
        # self.mainwindow.onClose()  # Appelle la méthode de fermeture de MainWindow  # Attention boucle !

        # Cette ligne est essentielle pour fermer la fenêtre Tkinter
        self.root.destroy()
        # self.root.destroy()  # Ne fonctionne pas avec le reste !
        # self.parent.destroy()
        return True

    def OnQuit(self):
        # Stop the IdleNotifier before quitting
        if hasattr(self, 'idle_notifier') and self.idle_notifier:
            self.idle_notifier.stop()

    @staticmethod
    def getInstance():
        """Retourne l'instance unique de TkinterApplication."""
        log.debug(f"TkinterApplication.getInstance : retourne {TkinterApplication.instance}")
        # if TkinterApplication.instance is None:
        #    TkinterApplication()  # Crée l'instance si elle n'existe pas
        return TkinterApplication.instance
        # return patterns.Singleton.__call__(TkinterApplication)

# if __name__ == '__main__':
#     # Les importations et l'initialisation originales
#     # ...
#     # Exécution de l'application
#     app = TkinterApplication()
#     app.start()
