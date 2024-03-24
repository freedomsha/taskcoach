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

# This module works around bugs in third party modules, mostly by
# monkey-patching so import it first
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


class RedirectedOutput(object):
    _rx_ignore = [
        re.compile('RuntimeWarning: PyOS_InputHook'),
    ]

    def __init__(self):
        self.__handle = None
        self.__path = os.path.join(Settings.path_to_documents_dir(), 'taskcoachlog.txt')

    def write(self, bf):
        for rx in self._rx_ignore:
            if rx.search(bf):
                return

        if self.__handle is None:
            self.__handle = open(self.__path, 'a+')
            self.__handle.write('============= %s\n' % time.ctime())
        self.__handle.write(bf)

    def flush(self):
        pass

    def close(self):
        if self.__handle is not None:
            self.__handle.close()
            self.__handle = None

    def summary(self):
        if self.__handle is not None:
            self.close()
            if operating_system.isWindows():
                wx.MessageBox(_('Errors have occured. Please see "taskcoachlog.txt" in your "My Documents" folder.'),
                              _('Error'), wx.OK)
            else:
                wx.MessageBox(_('Errors have occured. Please see "%s"') % self.__path, _('Error'), wx.OK)


# pylint: disable=W0404


class Wxapp(wx.App):
    def __init__(self, sessioncallback, reopencallback, *args, **kwargs):
        self.sessionCallback = sessioncallback
        self.reopenCallback = reopencallback
        self.__shutdownInProgress = False
        super(Wxapp, self).__init__(*args, **kwargs)

    def macreopenapp(self):
        self.reopenCallback()

    def oninit(self):
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
#    def ProcessIdle(self):
#        pass
# dans le fichier application.py pourtant elle est utilisée dans les tests!


class Application(object):
    __metaclass__ = patterns.Singleton

    def __init__(self, options=None, args=None, **kwargs):
        self._options = options
        self._args = args
        self.inittwisted()
        self.__wx_app = Wxapp(self.on_end_session, self.on_reopen_app, redirect=False)
        self.register_app()
        self.init(**kwargs)

        if operating_system.isGTK():
            if self.settings.getboolean('feature', 'usesm2'):
                from taskcoachlib.powermgt import xsm

                class LinuxSessionMonitor(xsm.SessionMonitor):
                    def __init__(self, callback):
                        super(LinuxSessionMonitor, self).__init__()
                        self._callback = callback
                        self.set_property(xsm.SmCloneCommand, sys.argv)
                        self.set_property(xsm.SmRestartCommand, sys.argv)
                        self.set_property(xsm.SmCurrentDirectory, os.getcwd())
                        self.set_property(xsm.SmProgram, sys.argv[0])
                        self.set_property(xsm.SmRestartStyleHint,
                                          xsm.SmRestartNever)

                    def saveYourself(self, savetype, shutdown, interactstyle,
                                     fast):  # pylint: disable=W0613
                        if shutdown:
                            wx.CallAfter(self._callback)
                        self.save_yourself_done(True)

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

    def inittwisted(self):
        from twisted.internet import wxreactor  # (1/5) to use Twisted
        wxreactor.install()  # (2/5)Twisted

        # Monkey-patching older versions because of https://twistedmatrix.com/trac/ticket/3948
        # J'ai deux alternatives à :
        #         if map(int, twisted.__version__.split('.')) < (11,):
        #             from twisted.internet import reactor
        #             if wxreactor.WxReactor.callFromThread is not None:
        #                 oldStop = wxreactor.WxReactor.stop
        #                 def stopfromthread(self):
        #                     self.callFromThread(oldStop, self)
        #                 wxreactor.WxReactor.stop = stopfromthread
        # celle généré par futurize:
        import twisted
        # if list(map(int, twisted.__version__.split('.'))) < (11,):
        if list(twisted.__version__.split('.')) < ['11',]:
            from twisted.internet import reactor  # (3/5)Twisted, when Wxapp has been created
            # retrouver dans twisted de quoi remplacer callFromThread
            # une piste sur https://stackoverflow.com/questions/4081578/python-twisted-with-callinthread
            # https://docs.twistedmatrix.com/en/stable/core/howto/threading.html#getting-results
            if reactor.callFromThread is not None:
                oldstop = wxreactor.WxReactor.stop

                def stopfromthread(self):
                    self.callFromThread(oldstop, self)

                wxreactor.WxReactor.stop = stopfromthread
        # ou
        # import twisted
        # print(list(twisted.__version__.split('.')))
        # if list(twisted.__version__.split('.')) < ['11', '0']:
        #    # essayer list seul sinon list(map())
        #    # from twisted.internet import reactor  # doublon soit-disant déjà installé
        #    if wxreactor.WxReactor.callFromThread is not None:
        #        oldStop = wxreactor.WxReactor.stop
        #        def stopfromthread(self):
        #            self.callFromThread(oldStop, self)
        #        wxreactor.WxReactor.stop = stopfromthread
        #        # ou essayer avec https://www.programcreek.com/python/example/117947/twisted.internet.error
        #        # .ReactorAlreadyInstalledError

    def stoptwisted(self):
        # voir https://stackoverflow.com/questions/6526923/stop-twisted-reactor-on-a-condition
        # from twisted.internet import reactor, error
        from twisted.internet import reactor, error
        try:
            reactor.stop()  # cannot find stop in reactor, but don't use yourApp.ExitMainLoop()
        except error.ReactorNotRunning:
            # Happens on Fedora 14 when running unit tests. Old Twisted ?
            # in Arch, reference 'stop' not find in 'reactor.py'
            pass

    def register_app(self):
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
        """ Call this to start the Application. """
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
        """ copy default templates that don't exist yet in the user's
            template directory. """
        # Copie les modèles par défaut qui n'existent pas encore dans le répertoire de modèles de l'utilisateur.
        # class getDefaultTemplates créé par templates.in/make.py
        from taskcoachlib.persistence import getdefaulttemplates  # créé par templates.in/make
        template_dir = self.settings.path_to_templates_dir()
        if len([name for name in os.listdir(template_dir) if name.endswith('.tsktmpl')]) == 0:
            for name, template in getdefaulttemplates():
                filename = os.path.join(template_dir, name + '.tsktmpl')
                if not os.path.exists(filename):
                    # file(filename, 'wb').write(template)
                    # try open(filename, 'wb').write(template)
                    open(filename, 'wb').write(template)

    def init(self, loadsettings=True, loadtaskfile=True):
        """ Initialize the application. Needs to be called before
            Application.start(). """
        self.__init_config(loadsettings)
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
        self.iocontroller = gui.IOController(self.taskFile, self.displaymessage,
                                             self.settings, splash)
        self.mainwindow = gui.MainWindow(self.iocontroller, self.taskFile,
                                         self.settings, splash=splash)
        self.__wx_app.SetTopWindow(self.mainwindow)
        self.__init_spell_checking()
        if not self.settings.getboolean('file', 'inifileloaded'):
            self.__close_splash(splash)
            self.__warn_user_that_ini_file_was_not_loaded()
        if loadtaskfile:
            self.iocontroller.open_after_start(self._args)
        self.__register_signal_handlers()
        self.__create_mutex()
        self.__create_task_bar_icon()
        wx.CallAfter(self.__close_splash, splash)
        wx.CallAfter(self.__show_tips)

    def __init_config(self, load_settings):
        from taskcoachlib import config
        ini_file = self._options.inifile if self._options else None
        # AttributeError: 'Values' object has no attribute 'inifile'
        # pylint: disable=W0201
        self.settings = config.Settings(load_settings, ini_file)

    def __init_language(self):
        """ Initialize the current translation. """
        from .. import i18n
        i18n.Translator(self.determine_language(self._options, self.settings))

    # @staticmethod  ?
    def determine_language(options, settings, locale=locale):  # pylint: disable=W0621
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
            # language = locale.getdefaultlocale()[0]
            language = locale.getlocale()[0]
            if language == 'C':
                language = None
        if not language:
            # Fall back on what the majority of our users use
            language = 'en_US'
        return language

    def __init_domain_objects(self):
        """ Provide relevant domain objects with access to the settings. """
        from taskcoachlib.domain import task, attachment
        task.Task.settings = self.settings
        attachment.Attachment.settings = self.settings

    def __init_application(self):
        from .. import meta
        self.__wx_app.SetAppName(meta.name)
        self.__wx_app.SetVendorName(meta.author)

    def __init_spell_checking(self):
        self.on_spell_checking(self.settings.getboolean('editor',
                                                        'maccheckspelling'))
        pub.subscribe(self.on_spell_checking,
                      'settings.editor.maccheckspelling')

    def on_spell_checking(self, value):
        if operating_system.isMac() and not operating_system.isMacOsXMountainLion_OrNewer():
            wx.SystemOptions.SetOptionInt("mac.textcontrol-use-spell-checker",
                                          value)

    def __register_signal_handlers(self):
        if operating_system.isWindows():
            import win32api  # pylint: disable=F0401

            def quit_adapter(*args):
                # The handler is called from something that is not the main thread, so we can't do
                # much wx-related
                event = threading.Event()

                def quit():
                    try:
                        self.quitapplication()
                    finally:
                        event.set()

                wx.CallAfter(quit)
                event.wait()
                return True

            win32api.SetConsoleCtrlHandler(quit_adapter, True)
        else:
            import signal

            def quit_adapter(*args):
                return self.quitapplication()

            signal.signal(signal.SIGTERM, quit_adapter)
            if hasattr(signal, 'SIGHUP'):
                # forced_quit = lambda *args: self.quitapplication(force=True)
                def forced_quit(*args):
                    return self.quitapplication(force=True)
                signal.signal(signal.SIGHUP, forced_quit)  # pylint: disable=E1101

    @staticmethod
    def __create_mutex():
        """ On Windows, create a mutex so that InnoSetup can check whether the
            application is running. """
        if operating_system.isWindows():
            import ctypes
            from taskcoachlib import meta
            ctypes.windll.kernel32.CreateMutexA(None, False, meta.filename)

    def __create_task_bar_icon(self):
        if self.__can_create_task_bar_icon():
            from ..gui import taskbaricon, menu
            self.taskBarIcon = taskbaricon.TaskBarIcon(self.mainwindow,  # pylint: disable=W0201
                                                       self.taskFile.tasks(), self.settings)
            self.taskBarIcon.set_popup_menu(menu.TaskBarMenu(self.taskBarIcon,
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
        if splash:
            splash.destroy()

    def __show_tips(self):
        if self.settings.getboolean('window', 'tips'):
            from .. import help  # pylint: disable=W0622
            help.show_tips(self.mainwindow, self.settings)

    def __warn_user_that_ini_file_was_not_loaded(self):
        from .. import meta
        reason = self.settings.get('file', 'inifileloaderror')
        wx.MessageBox(
            _("Couldn't load settings from TaskCoach.ini:\n%s") % reason,
            _('%s file error') % meta.name, style=wx.OK | wx.ICON_ERROR)
        self.settings.setboolean('file', 'inifileloaded', True)  # Reset

    def displaymessage(self, message):
        self.mainwindow.display_message(message)

    def on_end_session(self):
        self.mainwindow.set_shutdown_in_progress()
        self.quitapplication(force=True)

    def on_reopen_app(self):
        self.taskBarIcon.on_taskbar_click(None)

    def quitapplication(self, force=False):
        if not self.iocontroller.close(force=force):
            return False
        # Remember what the user was working on:
        self.settings.set('file', 'lastfile', self.taskFile.last_filename())
        self.mainwindow.save_settings()
        self.settings.save()
        if hasattr(self, 'taskBarIcon'):
            self.taskBarIcon.RemoveIcon()
        if self.mainwindow.bonjourRegister is not None:
            self.mainwindow.bonjourRegister.stop()
        from taskcoachlib.domain import date
        date.Scheduler().shutdown()
        self.__wx_app.ProcessIdle()  # Def ProcessIdle is not in application.py but used in tests !

        # For PowerStateMixin
        self.mainwindow.on_quit()

        if operating_system.isGTK() and self.sessionMonitor is not None:
            self.sessionMonitor.stop()

        if isinstance(sys.stdout, RedirectedOutput):
            sys.stdout.summary()

        self.stoptwisted()
        return True
