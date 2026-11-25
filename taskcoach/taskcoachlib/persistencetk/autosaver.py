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

from pubsub import pub


class AutoSaver(object):
    """Enregistre automatiquement les fichiers de tâches modifiés.

    La planification repose exclusivement sur l'interface de boucle fournie
    par Tkinter. Aucun import de wxPython n'est effectué par ce module.

    Le root doit bien être transmis au constructeur (AutoSaver(settings, root))
    ou être accessible comme settings.root.
    Sinon, le code lève volontairement un RuntimeError
    lorsqu’un fichier devient modifié.
    """

    def __init__(self, settings, root=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__settings = settings
        self.__root = root if root is not None else getattr(settings, "root", None)
        self.__task_files = set()
        self.__after_id = None
        pub.subscribe(self.onTaskFileDirty, "taskfile.dirty")

    def onTaskFileDirty(self, taskFile):
        """Planifie l'enregistrement d'un fichier devenu modifié."""
        if not self._needSave(taskFile):
            return

        self.__task_files.add(taskFile)
        if self.__after_id is None:
            if self.__root is None:
                raise RuntimeError(
                    "AutoSaver nécessite un root Tkinter pour planifier "
                    "l'enregistrement automatique."
                )
            self.__after_id = self.__root.after_idle(self.on_idle)

    def _needSave(self, taskFile):
        """Retourne vrai si le fichier doit être enregistré."""
        return bool(
            taskFile.filename()
            and taskFile.needSave()
            and self.__settings.getboolean("file", "autosave")
        )

    def _needLoad(self, taskFile):
        return taskFile.changedOnDisk() and \
            self.__settings.getboolean("file", "autoload")

    def on_idle(self, event=None):
        """Enregistre les fichiers modifiés lors du prochain passage idle."""
        self.__after_id = None
        while self.__task_files:
            task_file = self.__task_files.pop()
            if self._needSave(task_file):
                task_file.save()

