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


# from builtins import object
from taskcoachlib.i18n import _
from taskcoachlib.domain import categorizable
from taskcoachlib import help, operating_system  # pylint: disable=W0622
from . import task


class TaskListQueryMixin(object):
    def nrOfTasksPerStatus(self):
        statuses = [eachTask.status() for eachTask in self if not eachTask.isDeleted()]
        count = dict()
        for status in task.Task.possibleStatuses():
            count[status] = statuses.count(status)
        return count


class TaskList(TaskListQueryMixin, categorizable.CategorizableContainer):
    # FIXME: TaskList should be called TaskCollection or TaskSet

    # newItemMenuText = _("&New task...") + (
    #     "\tINSERT" if not operating_system.isMac() else "\tCtrl+N"
    # )
    newItemMenuText = "{0}{1}".format(_("&New task..."), (
        "\tINSERT" if not operating_system.isMac() else "\tCtrl+N"
    ))
    # TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
    newItemHelpText = help.taskNew

    def nrBeingTracked(self):
        return len(self.tasksBeingTracked())

    def tasksBeingTracked(self):
        return [eachTask for eachTask in self if eachTask.isBeingTracked()]

    def efforts(self):
        result = []
        for task in self:  # pylint: disable=W0621
            result.extend(task.efforts())
        return result

    def originalLength(self):
        """
        Fournir un moyen de contourner la méthode __len__ des décorateurs.

        Returns :
            (int) :
        """

        return len([t for t in self if not t.isDeleted()])

    def minPriority(self):
        return min(self.__allPriorities())

    def maxPriority(self):
        return max(self.__allPriorities())

    def __allPriorities(self):
        return [task.priority() for task in self if not task.isDeleted()] or (0,)  # pylint: disable=W0621
