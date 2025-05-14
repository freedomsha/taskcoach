# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 João Alexandre de Toledo <jtoledo@griffo.com.br>

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
# Changements à prendre en compte :
# Voici quelques points importants à considérer lors de la conversion :
#
# 1. **Syntaxe des chaînes de caractères** :
#    - En Python 2.7, les chaînes de caractères sont encadrées par des guillemets simples ou
# doubles (par exemple, `'string'` ou `"string"`).
#    - En Python 3, il faut utiliser des guillemets simples pour les chaînes littérales
# (`'string'`) et des guillemets triples pour les chaînes de plusieurs lignes (`"""text"""`). Les
# chaînes encadrées par des guillemets doubles sont traitées comme des chaînes de caractères
# Unicode.
#
# 2. **Exceptions** :
#    - En Python 2.7, `except:` catche toutes les exceptions.
#    - En Python 3, il est recommandé d'utiliser `except Exception as e:` pour capturer les
# exceptions et d'accéder à l'objet exception via la variable `e`.
#
# 3. **Méthodes des chaînes de caractères** :
#    - La méthode `splitlines()` retourne une liste de lignes dans Python 2.7, mais en Python 3,
# elle retourne un générateur.
#    - Il est préférable d'utiliser `str.splitlines(keepends=True)` pour obtenir les lignes avec le
# caractère de saut de ligne.
#
# 4. **Fichiers** :
#    - La méthode `read()` renvoie une chaîne en Python 2.7, mais elle renvoie un bytes object en
# Python 3.
#    - Utiliser `open(filename, 'r', encoding='utf-8')` pour lire les fichiers avec l'encodage
# UTF-8.
#
# 5. **Comparaisons et boucles** :
#    - En Python 2.7, les comparaisons et boucles peuvent être effectuées sur des entiers de
# différents types (comme `int` et `long`) qui ont une largeur fixe.
#    - En Python 3, tous les entiers sont des objets `int` de taille dynamique.
# ### Code modifié pour Python 3

# Le problème est effectivement que TaskBarIcon n'est pas une sous-classe de wx.Window,
# et les menus wxPython (comme ceux gérés par UICommandContainerMixin)
# sont conçus pour être associés à des wx.Window.

import wx
import os
from wx import adv as wiz
from taskcoachlib import meta, patterns, operating_system
from taskcoachlib.i18n import _
from taskcoachlib.domain import date, task
# try:
#    from ..thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
from pubsub import pub
from . import artprovider


class TaskBarIcon(patterns.Observer, wiz.TaskBarIcon):
    """
    Classe pour créer l'icône de la barre de tâche.

    iconType=TBI_DEFAULT_TYPE
    """
    def __init__(self, mainwindow, taskList, settings,
                 defaultBitmap="taskcoach", tickBitmap="clock_icon",
                 tackBitmap="clock_stopwatch_icon", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popupmenu = None  # needed in setPopupMenu
        self.__window = mainwindow
        self.__taskList = taskList
        self.__settings = settings
        self.__bitmap = self.__defaultBitmap = defaultBitmap
        self.__currentBitmap = self.__bitmap
        self.__tooltipText = ""
        self.__currentText = self.__tooltipText
        self.__tickBitmap = tickBitmap
        self.__tackBitmap = tackBitmap
        # self.registerObserver(self.onTaskListChanged,
        #                       eventType=taskList.addItemEventType(), eventSource=taskList)
        # self.registerObserver(self.onTaskListChanged,
        #                       eventType=taskList.removeItemEventType(), eventSource=taskList)
        # pub.subscribe(self.onTrackingChanged,
        #               task.Task.trackingChangedEventType())
        # pub.subscribe(self.onChangeDueDateTime,
        #               task.Task.dueDateTimeChangedEventType())
        # When the user chances the due soon hours preferences it may cause
        # a task to change appearance. That also means the number of due soon
        # tasks has changed, so we need to change the tool tip text.
        # Note that directly subscribing to the setting (behavior.duesoonhours)
        # is not reliable. The TaskBarIcon may get the event before the tasks
        # do. When that happens the tasks haven't changed their status yet and
        # we would use the wrong status count.
        # self.registerObserver(self.onChangeDueDateTime_Deprecated,
        #                       eventType=task.Task.appearanceChangedEventType())
        # if operating_system.isGTK():
        #     events = [wiz.EVT_TASKBAR_LEFT_DOWN]
        # elif operating_system.isWindows():
        #     # See http://msdn.microsoft.com/en-us/library/windows/desktop/aa511448.aspx#interaction
        #     events = [wiz.EVT_TASKBAR_LEFT_DOWN, wiz.EVT_TASKBAR_LEFT_DCLICK]
        # else:
        #     events = [wiz.EVT_TASKBAR_LEFT_DCLICK]
        # for event in events:
        #     self.Bind(event, self.onTaskbarClick)
        # self.__setTooltipText()
        # mainwindow.Bind(wx.EVT_IDLE, self.onIdle)
        self.toolTipMessages = [
            (task.status.overdue, _("one task overdue"), _("%d tasks overdue")),
            (task.status.duesoon, _("one task due soon"), _("%d tasks due soon"))
        ]

    # # Event handlers:
    #
    # def onIdle(self, event):
    #     if self.__currentText != self.__tooltipText or self.__currentBitmap != self.__bitmap:
    #         self.__currentText = self.__tooltipText
    #         self.__currentBitmap = self.__bitmap
    #         self.__setIcon()
    #     if event is not None:  # Unit tests
    #         event.Skip()
    #
    # def onTaskListChanged(self, event):  # pylint: disable=W0613
    #     self.__setTooltipText()
    #     self.__startOrStopTicking()
    #
    # def onTrackingChanged(self, newValue, sender):
    #     if newValue:
    #         self.registerObserver(self.onChangeSubject,
    #                               eventType=sender.subjectChangedEventType(),
    #                               eventSource=sender)
    #     else:
    #         self.removeObserver(self.onChangeSubject,
    #                             eventType=sender.subjectChangedEventType())
    #     self.__setTooltipText()
    #     if newValue:
    #         self.__startTicking()
    #     else:
    #         self.__stopTicking()
    #
    # def onChangeSubject(self, event):  # pylint: disable=W0613
    #     self.__setTooltipText()
    #
    # def onChangeDueDateTime(self, newValue, sender):  # pylint: disable=W0613
    #     self.__setTooltipText()
    #
    # def onChangeDueDateTime_Deprecated(self, event):
    #     self.__setTooltipText()
    #
    # def onEverySecond(self):
    #     if self.__settings.getboolean("window", "blinktaskbariconwhentrackingeffort") and \
    #             not operating_system.isMacOsXMavericks_OrNewer():
    #         self.__toggleTrackingBitmap()
    #         self.__setIcon()
    #
    # def onTaskbarClick(self, event):
    #     if self.__window.IsIconized() or not self.__window.IsShown():
    #         self.__window.restore(event)
    #     else:
    #         if operating_system.isMac():
    #             self.__window.Raise()
    #         else:
    #             self.__window.Iconize()

    # Menu:

    def setPopupMenu(self, menu):
        # self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.popupTaskBarMenu)
        self.Bind(wiz.EVT_TASKBAR_RIGHT_UP, self.popupTaskBarMenu)
        self.popupmenu = menu  # pylint: disable=W0201

    def popupTaskBarMenu(self, event):  # pylint: disable=W0613
        self.PopupMenu(self.popupmenu)  # Utiliser la méthode PopupMenu de wx.TaskBarIcon.

    # Getters:

    def tooltip(self):
        return self.__tooltipText

    def bitmap(self):
        return self.__bitmap

    def defaultBitmap(self):
        return self.__defaultBitmap

    # Private methods:

    def __startOrStopTicking(self):
        # self.__startTicking()
        # self.__stopTicking()
        self.__stopTicking()
        # if self.__taskList.nrBeingTracked() > 0:
        #     self.startClock()
        #     self.__toggleTrackingBitmap()
        #     self.__setIcon()
        self.__startTicking()

    def __startTicking(self):
        if self.__taskList.nrBeingTracked() > 0:
            self.startClock()
            self.__toggleTrackingBitmap()
            self.__setIcon()

    def startClock(self):
        date.Scheduler().schedule_interval(self.onEverySecond, seconds=1)

    def __stopTicking(self):
        if self.__taskList.nrBeingTracked() == 0:
            self.stopClock()
            self.__setDefaultBitmap()
            self.__setIcon()

    def stopClock(self):
        date.Scheduler().unschedule(self.onEverySecond)

    def onEverySecond(self):
        pass

    # toolTipMessages = [
    #     (task.status.overdue, _("one task overdue"), _("%d tasks overdue")),
    #     (task.status.duesoon, _("one task due soon"), _("%d tasks due soon"))
    # ]

    def __setTooltipText(self):
        """ Note that Windows XP and Vista limit the text shown in the
            tool tip to 64 characters, so we cannot show everything we would
            like to and have to make choices. """
        textParts = []
        trackedTasks = self.__taskList.tasksBeingTracked()
        if trackedTasks:
            count = len(trackedTasks)
            if count == 1:
                tracking = _('tracking "%s"') % trackedTasks[0].subject()
            else:
                tracking = _("tracking effort for %d tasks") % count
            textParts.append(tracking)
        else:
            counts = self.__taskList.nrOfTasksPerStatus()
            for status, singular, plural in self.toolTipMessages:
                count = counts[status]
                if count == 1:
                    textParts.append(singular)
                elif count > 1:
                    textParts.append(plural % count)

        textPart = ", ".join(textParts)
        filename = os.path.basename(self.__window.taskFile.filename())
        namePart = "%s - %s" % (meta.name, filename) if filename else meta.name
        # text = "%s\n%s" % (namePart, textPart) if textPart else namePart
        # if text != self.__tooltipText:
        #     self.__tooltipText = text
        self.__tooltipText = "%s\n%s" % (namePart, textPart) if textPart else namePart

    def __setDefaultBitmap(self):
        self.__bitmap = self.__defaultBitmap

    def __toggleTrackingBitmap(self):
        tick, tack = self.__tickBitmap, self.__tackBitmap
        self.__bitmap = tack if self.__bitmap == tick else tick

    def __setIcon(self):
        icon = artprovider.getIcon(self.__bitmap)
        try:
            self.SetIcon(icon, self.__tooltipText)
        except:  # Not Finally
            # wx assert errors on macOS but the icon still gets set... Whatever
            pass
