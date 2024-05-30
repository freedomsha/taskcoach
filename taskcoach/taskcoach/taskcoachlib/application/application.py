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

Programme Principal
"""

# This module works around bugs in third party modules, mostly by
# monkey-patching so import it first
# Ce module contourne les bugs des modules tiers, principalement en appliquant des correctifs singe,
# alors importez-le d'abord
# 2 ajouts de futurize : map et object
from builtins import map  # Unused import statement 'from builtins import map'
from builtins import object
# from .. import workarounds  # pylint: disable=W0611  unused import statement
from taskcoachlib import patterns, operating_system
# nouveau :
from taskcoachlib.i18n import _
from taskcoachlib.config import Settings
# try:
from pubsub import pub
# except ImportError:
#    try:
#        from ..thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub

import locale
import os
import sys
import time
import wx
import calendar
import re
import threading
from io import open as file


class RedirectedOutput(object):
    """Classe objet de redirection de la sortie."""
    _rx_ignore = [
        re.compile('RuntimeWarning: PyOS_InputHook'),
    ]

    def __init__(self):
        """Fonction qui initialise l'argument-fichier à utiliser et l'argument du chemin du fichier taskcoachlog.txt"""
        # Argument-fichier à utiliser
        self.__handle = None
        # chemin de taskcoachlog.txt
        self.__path = os.path.join(Settings.pathToDocumentsDir(), 'taskcoachlog.txt')

    def write(self, bf):
        """Fonction-méthode pour ouvrir puis écrire la Date et l'heure actuelle et bf dans taskcoachlog.txt"""
        for rx in self._rx_ignore:
            if rx.search(bf):
                return

        # Si l'argument-fichier à utiliser n'existe pas
        if self.__handle is None:
            # le définir comme l'ouverture pour écriture du fichier taskcoachlog.txt
            self.__handle = file(self.__path, 'a+')
            # self.__handle = open(self.__path, 'a+')
            # écrire la Date et l'heure actuelle dans taskcoachlog.txt
            self.__handle.write('============= %s\n' % time.ctime())
            # self.__handle.write('============= {}\n'.format(time.ctime()))
        # écrire bf dans taskcoachlog.txt
        self.__handle.write(bf)

    def flush(self):
        pass

    def close(self):
        """Fonction-méthode pour fermer taskcoachlig.txt"""
        if self.__handle is not None:
            self.__handle.close()
            self.__handle = None

    def summary(self):
        """Fonction-méthode pour afficher une info sur ce qu'il vient d'être écrit dans taskcoachlog.txt"""
        if self.__handle is not None:
            self.close()
            if operating_system.isWindows():
                wx.MessageBox(_('Errors have occured. Please see "taskcoachlog.txt" in your "My Documents" folder.'),
                              _('Error'), wx.OK)
            else:
                wx.MessageBox(_('Errors have occured. Please see "%s"') % self.__path, _('Error'), wx.OK)
                # wx.MessageBox(_('Errors have occured. Please see "{}"'.format(self.__path)), _('Error'), wx.OK)
                # wx.MessageBox(_(f'Errors have occured. Please see "{self.__path}"'), _('Error'), wx.OK)


# pylint: disable=W0404


class wxApp(wx.App):
    """Classe"""

    def __init__(self, sessioncallback, reopencallback, *args, **kwargs):
        self.sessionCallback = sessioncallback
        self.reopenCallback = reopencallback
        self.__shutdownInProgress = False
        super(wxApp, self).__init__(*args, **kwargs)

    def macreopenapp(self):
        """Fonction-méthode pour rouvrir l'application sur Mac."""
        self.reopenCallback()

    def oninit(self):
        # fonction-méthode qui gère la sortie standard renvoie true sur l'initialisation
        # voir https://docs.python.org/fr/3.11/library/sys.html#sys.stdout
        if operating_system.isWindows():
            self.Bind(wx.EVT_QUERY_END_SESSION, self.onqueryendsession)

        try:
            isatty = sys.stdout.isatty()
        except AttributeError:
            isatty = False

        if (operating_system.isWindows() and hasattr(sys, 'frozen') and not isatty) or not isatty:
            sys.stdout = sys.stderr = RedirectedOutput()

        return True

    def onqueryendsession(self, event=None):
        if not self.__shutdownInProgress:
            self.__shutdownInProgress = True
            self.sessionCallback()

        if event is not None:
            event.Skip()

    # disparition de :
    def ProcessIdle(self):
        pass
    # dans le fichier application.py pourtant elle est utilisée dans les tests et dans quitApplication


# class Application(object):
#     __metaclass__ = patterns.Singleton
class Application(metaclass=patterns.Singleton):
    """Classe principale qui lance/arrête Twisted"""

    def __init__(self, options=None, args=None, **kwargs):
        # Instance attribute __version_checker, __message_checker defined outside __init__
        # Attributs d'instance :
        # 2 nouveaux paramètres nécessaires dans start :
        self.__version_checker = None
        self.__message_checker = None
        # Instance attribute taskFile, __auto_saver, __auto_exporter, __auto_backup, iocontroller, mainwindow
        # defined outside __init__
        # 6 nouveaux paramètres nécessaires dans init :
        self.taskFile = None
        self.__auto_saver = None
        self.__auto_exporter = None
        self.__auto_backup = None
        self.iocontroller = None
        self.mainwindow = None

        self._options = options
        self._args = args
        self.initTwisted()
        self.__wx_app = wxApp(self.on_end_session, self.on_reopen_app, redirect=False)
        self.registerApp()
        self.init(**kwargs)

        if operating_system.isGTK():
            if self.settings.getboolean('feature', 'usesm2'):
                from taskcoachlib.powermgt import xsm

                class LinuxSessionMonitor(xsm.SessionMonitor):
                    def __init__(self, callback):
                        super(LinuxSessionMonitor, self).__init__()
                        self._callback = callback
                        self.setProperty(xsm.SmCloneCommand, sys.argv)
                        self.setProperty(xsm.SmRestartCommand, sys.argv)
                        self.setProperty(xsm.SmCurrentDirectory, os.getcwd())
                        self.setProperty(xsm.SmProgram, sys.argv[0])
                        self.setProperty(xsm.SmRestartStyleHint,
                                         xsm.SmRestartNever)

                    def saveYourself(self, savetype, shutdown, interactstyle,
                                     fast):  # pylint: disable=W0613
                        if shutdown:
                            wx.CallAfter(self._callback)
                        self.saveYourselfDone(True)

                    def die(self):
                        pass

                    def saveComplete(self):
                        pass

                    def shutdownCancelled(self):
                        pass

                self.sessionMonitor = LinuxSessionMonitor(self.on_end_session)  # pylint: disable=W0201
            else:
                self.sessionMonitor = None

        calendar.setfirstweekday(dict(monday=0, sunday=6)[self.settings.get('view', 'weekstart')])

    def initTwisted(self):
        """Fonction-méthode pour initialiser et lancer Twisted."""
        # voir peut-être https://docs.twisted.org/en/stable/core/howto/design.html
        # et https://docs.twisted.org/en/stable/core/howto/process.html
        # et pour python 3 : https://docs.twisted.org/en/stable/core/howto/python3.html
        from twisted.internet import wxreactor  # (1/5) to use Twisted
        wxreactor.install()  # (2/5)Twisted

        # Monkey-patching older versions because of https://twistedmatrix.com/trac/ticket/3948
        # J'ai deux alternatives à :
        #         if map(int, twisted.__version__.split('.')) < (11,):
        #             from twisted.internet import reactor
        #             if wxreactor.WxReactor.callFromThread is not None:
        #                 oldStop = wxreactor.WxReactor.stop
        #                 def stopFromThread(self):
        #                     self.callFromThread(oldStop, self)
        #                 wxreactor.WxReactor.stop = stopFromThread
        # celle généré par futurize:
        import twisted
        # if list(map(int, twisted.__version__.split('.'))) < (11,):
        if list(twisted.__version__.split('.')) < ['11', ]:
            from twisted.internet import reactor, threads  # (3/5)Twisted, when Wxapp has been created
            # retrouver dans twisted de quoi remplacer callFromThread
            # une piste sur https://stackoverflow.com/questions/4081578/python-twisted-with-callinthread
            # https://docs.twistedmatrix.com/en/stable/core/howto/threading.html#getting-results
            if threads.deferToThread is not None:
                oldstop = wxreactor.WxReactor.stop

                def stopFromThread(self):
                    # self.callFromThread(oldstop, self)
                    self.deferToThread(oldstop, self)

                wxreactor.WxReactor.stop = stopFromThread
        # ou
        # import twisted
        # print(list(twisted.__version__.split('.')))
        # if list(twisted.__version__.split('.')) < ['11', '0']:
        #    # essayer list seul sinon list(map())
        #    # from twisted.internet import reactor  # doublon soit-disant déjà installé
        #    if wxreactor.WxReactor.callFromThread is not None:
        #        oldStop = wxreactor.WxReactor.stop
        #        def stopFromThread(self):
        #            self.callFromThread(oldStop, self)
        #        wxreactor.WxReactor.stop = stopFromThread
        #        # ou essayer avec https://www.programcreek.com/python/example/117947/twisted.internet.error
        #        # .ReactorAlreadyInstalledError

    def stoptwisted(self):
        """Fonction-méthode pour arrêter twisted-reactor"""
        # voir https://stackoverflow.com/questions/6526923/stop-twisted-reactor-on-a-condition
        # from twisted.internet import reactor, error
        from twisted.internet import reactor, error
        try:
            reactor.stop()  # cannot find stop in reactor, but don't use yourApp.ExitMainLoop()
        except error.ReactorNotRunning:
            # Happens on Fedora 14 when running unit tests. Old Twisted ?
            # in Arch, reference 'stop' not find in 'reactor.py'
            pass

    def registerApp(self):
        """Register the App instance with Twisted:

        Fonction-méthode pour Enregistrez l'instance d'application avec Twisted:

        """
        try:
            from twisted.internet import reactor  # (3/5)Twisted, when Wxapp has been created
            # voir peut-etre aussi twisted.internet.wxreactor.WxReactor !
            reactor.registerWxApp(self.__wx_app)  # (4/5)Twisted
        except ModuleNotFoundError:
            from twisted.internet import wxreactor
            # https://docs.twistedmatrix.com/en/stable/api/twisted.internet.wxreactor.WxReactor.html#registerWxApp
            wxreactor.WxReactor.registerWxApp(self.__wx_app)
        except TypeError:
            print("registerWxApp missing 1 argument")
            pass

    def start(self):
        """ Call this to start the Application.

        Fonction-méthode d'Appel pour démarrer l'application.

        """
        # pylint: disable=W0201
        from taskcoachlib import meta
        if self.settings.getboolean('version', 'notify'):
            self.__version_checker = meta.VersionChecker(self.settings)
            self.__version_checker.start()
        if self.settings.getboolean('view', 'developermessages'):
            self.__message_checker = meta.DeveloperMessageChecker(self.settings)
            self.__message_checker.start()
        self.__copy_default_templates()
        self.mainwindow.Show()
        #  from twisted.internet import reactor
        #         reactor.run()
        from twisted.internet import reactor  # (3/5)Twisted
        # voir https://github.com/twisted/twisted/blob/63df84e454978bd7a2d57ed292913384ca352e1a/src/twisted/internet/wxreactor.py#L74
        # start the event loop:
        # Démarre la boucle des événements:
        reactor.run()  # (5/5)Twisted
        # IMPORTANT: tests will fail when run under this reactor. This is
        # expected and probably does not reflect on the reactor's ability to run
        # real applications.
        #
        # ou essayer :
        # from twisted.internet.interfaces import IReactorCore
        # ou twisted.internet.wxreactor.WxReactor.run
        # IReactorCore.run()
        # https://docs.twisted.org/en/stable/api/nameIndex.html#R
        # twisted.application.app.ApplicationRunner.run
        # twisted.application.app.AppProfiler.run
        # twisted.application.app.CProfileRunner.run
        # twisted.application.app.ProfileRunner.run
        # twisted.application.app.run
        # twisted.conch.scripts.cftp.run
        # twisted.conch.scripts.ckeygen.run
        # twisted.conch.scripts.conch.run
        # twisted.conch.scripts.tkconch.run
        # twisted.internet.asyncioreactor.AsyncioSelectorReactor.run
        # twisted.internet.base.ReactorBase.run
        # twisted.internet.interfaces.IReactorCore.run
        # twisted.internet.testing.MemoryReactor.run
        # twisted.internet.wxreactor.WxReactor.run
        # twisted.internet.wxsupport.wxRunner.run

    def __copy_default_templates(self):
        """ Copy default templates that don't exist yet in the user's template directory.

        Copie les modèles par défaut qui n'existent pas encore dans le répertoire de modèles de l'utilisateur.

        """

        # class getDefaultTemplates créé par templates.in/make.py
        from taskcoachlib.persistence import getDefaultTemplates  # créé par templates.in/make
        template_dir = self.settings.pathToTemplatesDir()
        if len([name for name in os.listdir(template_dir) if name.endswith('.tsktmpl')]) == 0:
            for name, template in getDefaultTemplates():
                filename = os.path.join(template_dir, name + '.tsktmpl')
                if not os.path.exists(filename):
                    # ouverture du fichier filename en mode bytes !!! et y écrire template
                    file(filename, 'wb').write(template)
                    # open(filename, 'wb').write(template)

    def init(self, loadSettings=True, loadTaskFile=True):
        """ Initialize the application. Needs to be called before Application.start().

        Initialisez l'application. Doit être appelé avant Application.start().

        """
        # Attributs d'instance:
        self.__init_config(loadSettings)
        self.__init_language()
        self.__init_domain_objects()
        self.__init_application()
        from taskcoachlib import gui, persistence
        gui.init()
        show_splash_screen = self.settings.getboolean('window', 'splash')
        splash = gui.SplashScreen() if show_splash_screen else None
        # pylint: disable=W0201
        self.taskFile = persistence.LockedTaskFile(poll=not self.settings.getboolean('file', 'nopoll'))
        self.__auto_saver = persistence.AutoSaver(self.settings)
        self.__auto_exporter = persistence.AutoImporterExporter(self.settings)
        self.__auto_backup = persistence.AutoBackup(self.settings)
        self.iocontroller = gui.IOController(self.taskFile, self.displayMessage,
                                             self.settings, splash)
        self.mainwindow = gui.MainWindow(self.iocontroller, self.taskFile,
                                         self.settings, splash=splash)
        self.__wx_app.SetTopWindow(self.mainwindow)
        self.__init_spell_checking()
        if not self.settings.getboolean('file', 'inifileloaded'):
            self.__close_splash(splash)
            self.__warn_user_that_ini_file_was_not_loaded()
        if loadTaskFile:
            self.iocontroller.openAfterStart(self._args)
        self.__register_signal_handlers()
        self.__create_mutex()
        self.__create_task_bar_icon()
        wx.CallAfter(self.__close_splash, splash)
        wx.CallAfter(self.__show_tips)

    def __init_config(self, load_settings):
        """ Fonction-méthode d'initialisation de la configuration."""
        from taskcoachlib import config
        ini_file = self._options.inifile if self._options else None
        # AttributeError: 'Values' object has no attribute 'inifile'
        # AttributeError: 'Namespace' object has no attribute 'inifile'
        # pylint: disable=W0201
        self.settings = config.Settings(load_settings, ini_file)

    def __init_language(self):
        """ Initialize the current translation. """
        # if old:
        from taskcoachlib import i18n
        i18n.Translator(self.determine_language(self._options, self.settings))
        # else:
        #    from taskcoachlib import i18n

    @staticmethod
    def determine_language(options, settings, locale=locale):  # pylint: disable=W0621
        # Shadows name 'locale' from outer scope
        """ Détermine la langue locale utilisée. """
        language = None
        if options:
            # User specified language or .po file on command line
            language = options.pofile or options.language
        if not language:
            # Get language as set by the user via the preferences dialog
            language = settings.get('view', 'language_set_by_user')
        if not language:
            # Get language as set by the user or externally (e.g. PortableApps)
            language = settings.get('view', 'language')
        if not language:
            # Use the user's locale
            language = locale.getdefaultlocale()[0]
            # language = locale.getlocale()[0]
            if language == 'C':
                language = None
        if not language:
            # Fall back on what the majority of our users use
            language = 'en_US'
        return language

    def __init_domain_objects(self):
        """ Provide relevant domain objects with access to the settings.

        Fonction-méthode qui fournit aux objets de domaine pertinents un accès aux paramètres.
        """
        from taskcoachlib.domain import task, attachment
        task.Task.settings = self.settings
        attachment.Attachment.settings = self.settings

    def __init_application(self):
        """ Fonction-méthode qui règle les paramètres nom et auteurs de l'applicaiton."""
        from taskcoachlib import meta
        # Attributs d'instance
        self.__wx_app.SetAppName(meta.name)
        self.__wx_app.SetVendorName(meta.author)

    def __init_spell_checking(self):
        """ Fonction-méthode qui règle-initialise """
        self.on_spell_checking(self.settings.getboolean('editor', 'maccheckspelling'))
        pub.subscribe(self.on_spell_checking, 'settings.editor.maccheckspelling')

    def on_spell_checking(self, value):
        """ SystemOptions stores option/value pairs that wxWidgets itself or applications
        can use to alter behaviour at run-time.

         Fonctin-méthode qui utilise SystemOptions qui stocke les paires option/valeur que wxWidgets lui-même
         ou les applications peuvent utiliser pour modifier le comportement au moment de l'exécution.       """
        # SystemOptions stores option/value pairs that wxWidgets itself or applications
        # can use to alter behaviour at run-time.
        # SystemOptions stocke les paires option/valeur que wxWidgets lui-même ou les applications
        # peuvent utiliser pour modifier le comportement au moment de l'exécution.
        if operating_system.isMac() and not operating_system.isMacOsXMountainLion_OrNewer():
            # wx.SystemOptions.SetOptionInt("mac.textcontrol-use-spell-checker", value)

            wx.SystemOptions.SetOption("mac.textcontrol-use-spell-checker",
                                       value)

    def __register_signal_handlers(self):
        """ Fonction-méthode pour quitter à cause d'un signal. """
        if operating_system.isWindows():
            import win32api  # pylint: disable=F0401

            def quit_adapter(*args):
                # Parameter 'args' value is not used
                # The handler is called from something that is not the main thread, so we can't do
                # much wx-related
                # Le gestionnaire est appelé depuis quelque chose qui n'est pas le thread principal,
                # nous ne pouvons donc pas faire grand-chose en rapport avec wx.
                event = threading.Event()

                def quit():
                    # Shadows built-in name 'quit'
                    try:
                        self.quitApplication()
                    finally:
                        event.set()

                wx.CallAfter(quit)
                event.wait()
                return True

            win32api.SetConsoleCtrlHandler(quit_adapter, True)
        else:
            import signal

            def quit_adapter(*args):
                # Parameter 'args' value is not used
                return self.quitApplication()

            signal.signal(signal.SIGTERM, quit_adapter)
            if hasattr(signal, 'SIGHUP'):
                # forced_quit = lambda *args: self.quitApplication(force=True)
                def forced_quit(*args):
                    # Parameter 'args' value is not used
                    return self.quitApplication(force=True)

                signal.signal(signal.SIGHUP, forced_quit)  # pylint: disable=E1101

    @staticmethod
    def __create_mutex():
        """ On Windows, create a mutex so that InnoSetup can check whether the
            application is running.

            Sous Windows, créez un mutex pour qu'InnoSetup puisse vérifier si l'application est en cours d'exécution.

            """
        if operating_system.isWindows():
            import ctypes
            from taskcoachlib import meta
            ctypes.windll.kernel32.CreateMutexA(None, False, meta.filename)

    def __create_task_bar_icon(self):
        """ Fonction-Méthode pour créer un icône avec menu dans la barre de tâche. """
        if self.__can_create_task_bar_icon():
            from taskcoachlib.gui import taskbaricon, menu
            self.taskBarIcon = taskbaricon.TaskBarIcon(self.mainwindow,  # pylint: disable=W0201
                                                       self.taskFile.tasks(), self.settings)
            self.taskBarIcon.setPopupMenu(menu.TaskBarMenu(self.taskBarIcon,
                                                           self.settings, self.taskFile, self.mainwindow.viewer))

    @staticmethod
    def __can_create_task_bar_icon():
        try:
            from taskcoachlib.gui import taskbaricon  # pylint: disable=W0612
            return True
        except ImportError:
            return False  # pylint: disable=W0702

    @staticmethod
    def __close_splash(splash):
        """ Fonction-méthode si splash. """
        if splash:
            splash.Destroy()

    def __show_tips(self):
        """ Fonction-méthode d'affichage des fenêtres d'astuces. """
        if self.settings.getboolean('window', 'tips'):
            from taskcoachlib import help  # pylint: disable=W0622
            help.showTips(self.mainwindow, self.settings)

    def __warn_user_that_ini_file_was_not_loaded(self):
        """ Fonction-méthode pour avertir l'utilisateur que le fichier ini n'a pas été démarré."""
        from taskcoachlib import meta
        reason = self.settings.get('file', 'inifileloaderror')
        wx.MessageBox(
            _("Couldn't load settings from TaskCoach.ini:\n%s") % reason,
            _('%s file error') % meta.name, style=wx.OK | wx.ICON_ERROR)
        self.settings.setboolean('file', 'inifileloaded', True)  # Reset

    def displayMessage(self, message):
        """ Fonction-méthode pour afficher le message. """
        self.mainwindow.displayMessage(message)

    def on_end_session(self):
        """ Fonction-méthode de fin de session. """
        self.mainwindow.setShutdownInProgress()
        self.quitApplication(force=True)

    def on_reopen_app(self):
        """ Fonction-méthode pour ré-ouvrir l'application. """
        self.taskBarIcon.onTaskbarClick(None)

    def quitApplication(self, force=False):
        """ Fonction-méthode pour quitter l'application. """
        if not self.iocontroller.close(force=force):
            return False
        # Remember what the user was working on:
        # Rappelez-vous sur quoi l'utilisateur travaillait:
        self.settings.set('file', 'lastfile', self.taskFile.lastFilename())
        self.mainwindow.saveSettings()
        self.settings.save()
        if hasattr(self, 'taskBarIcon'):
            self.taskBarIcon.RemoveIcon()
        if self.mainwindow.bonjourRegister is not None:
            self.mainwindow.bonjourRegister.stop()
        from taskcoachlib.domain import date
        date.Scheduler().shutdown()
        # self.__wx_app.ProcessIdle()  # wxApp/ProcessIdle is not in application.py but used in tests !
        wx.EventLoop.GetActive().ProcessIdle()  # wxApp/ProcessIdle is not in application.py but used in tests !

        # For PowerStateMixin
        self.mainwindow.OnQuit()

        if operating_system.isGTK() and self.sessionMonitor is not None:
            self.sessionMonitor.stop()

        if isinstance(sys.stdout, RedirectedOutput):
            sys.stdout.summary()

        self.stoptwisted()
        return True
