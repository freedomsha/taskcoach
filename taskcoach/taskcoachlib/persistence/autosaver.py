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

# from builtins import object
# try:
from pubsub import pub
# except ImportError:
#    try:
#        from taskcoachlib.thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
# import wx
from taskcoachlib.config.arguments import get_gui


class AutoSaver(object):  # nouvelle classe
    """Enregistre automatiquement les fichiers de tâches modifiés.

    La planification repose exclusivement sur l'interface de boucle fournie
    par Tkinter. Aucun import de wxPython n'est effectué par ce module.

    AutoSaver observes task files. If a task file is changed by the user
    (gets 'dirty') and auto save is on, AutoSaver saves the task file.

    Le root doit bien être transmis au constructeur (AutoSaver(settings, root))
    ou être accessible comme settings.root. Sinon, le code lève volontairement
    un RuntimeError lorsqu’un fichier devient modifié.
    """

    # def __init__(self, settings, *args, **kwargs):
    def __init__(self, settings, root=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__settings = settings
        self.__root = root if root is not None else getattr(settings, "root", None)
        self.__task_files = set()
        self.__bound = False
        self.__after_id = None
        pub.subscribe(self.onTaskFileDirty, "taskfile.dirty")

    def onTaskFileDirty(self, taskFile):
        """Planifie l'enregistrement d'un fichier devenu modifié.

        When a task file gets dirty and auto save is on, note it so
        it can be saved during idle time. """
        # AutoSaver appelle wx.GetApp() et utilise wx.EVT_IDLE
        # pour déclencher l'enregistrement automatique.
        # Il faut remplacer ce fonctionnement par une planification Tkinter,
        # par exemple root.after() ou root.after_idle(),
        # sans perdre la gestion des fichiers modifiés.
        if not self._needSave(taskFile):
            return
        if self._needSave(taskFile):  # redondant !
            self.__task_files.add(taskFile)

        if get_gui() == "wx":
            import wx
            if not self.__bound:
                self.__bound = True
                wx.GetApp().Bind(wx.EVT_IDLE, self.on_idle)
            # TODO : trouver une alternative tkinter à cette ligne et à on_idle().
        elif get_gui() == "tk":
            # import tkinter as tk
            # # self.root.bind(, self.on_idle)  # Je ne sais pas quoi mettre !
            # # self.root.after(100, self.on_idle)  # Appelle on_idle après 100 ms
            # self.root.after_idle(self.on_idle)
            if not self.__bound:
                self.__bound = True
                if self.__after_id is None:
                    if self.__root is None:
                        raise RuntimeError(
                            "AutoSaver nécessite un root Tkinter pour planifier "
                            "l'enregistrement automatique."
                        )
                    self.__after_id = self.__root.after_idle(self.on_idle)

    def _needSave(self, taskFile):  # or use task_file ?
        """Retourne vrai si le fichier doit être enregistré.

        Return whether the task file needs to be saved. """
        # return taskFile.filename() and taskFile.needSave() and \
        #     self.__settings.getboolean("file", "autosave")
        return bool(
            taskFile.filename()
            and taskFile.needSave()
            and self.__settings.getboolean("file", "autosave")
        )

    def _needLoad(self, taskFile):
        return taskFile.changedOnDisk() and \
            self.__settings.getboolean("file", "autoload")

    def on_idle(self, event=None):
        """Enregistre les fichiers modifiés lors du prochain passage idle.

        Actually save the dirty files during idle time. """
        if get_gui() == "wx":
            import wx
            event.Skip()
            wx.GetApp().Unbind(wx.EVT_IDLE, handler=self.on_idle)
        elif get_gui() == "tk":
            # self.root.after_cancel()
            self.__after_id = None
        self.__bound = False
        while self.__task_files:
            task_file = self.__task_files.pop()
            if self._needSave(task_file):
                task_file.save()

