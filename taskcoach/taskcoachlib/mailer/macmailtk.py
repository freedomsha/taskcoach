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

from future import standard_library

standard_library.install_aliases()
from taskcoachlib import operating_system
from taskcoachlib.i18n import _
import subprocess
import threading
import time


class MailAppInfoLoader:
    """Charge le sujet sélectionné dans Mail.app sans dépendance wx globale."""
    def __init__(self, parent=None):
        self.__title = None
        self.__thread = threading.Thread(target=self.__run, daemon=True)
        self.__thread.start()

    def __run(self):
        script = """tell application \"Mail\"
    set theMessages to selection
    subject of beginning of theMessages
end tell
"""
        try:
            sp = subprocess.Popen("osascript", stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = sp.communicate(script.encode("utf-8"))
            if not sp.returncode:
                self.__title = operating_system.decodeSystemString(out.strip())
                return
        except OSError:
            pass
        self.__title = _('Mail.app message')

    def title(self):
        return self.__title


def getSubjectOfMail(message_id):  # pylint: disable=W0613
    """Retourne le sujet du message sélectionné dans Mail.app, si disponible."""
    loader = MailAppInfoLoader()
    loader._MailAppInfoLoader__thread.join()
    return loader.title() or _('Mail.app message')
