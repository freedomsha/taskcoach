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
    """
    Classe mixin.
    """
    def nrOfTasksPerStatus(self):
        """
        Calculer le nombre de tâches pour chaque statut possible.

        Elle parcourt les tâches (en ignorant celles qui sont supprimées)
        et compte leur statut, puis retourne un dictionnaire avec ces totaux.

        Returns:

        """
        statuses = [eachTask.status() for eachTask in self if not eachTask.isDeleted()]
        count = dict()
        for status in task.Task.possibleStatuses():
            count[status] = statuses.count(status)
        return count


class TaskList(TaskListQueryMixin, categorizable.CategorizableContainer):
    """
    Hérite de TaskListQueryMixin pour accéder à nrOfTasksParStatus() et
    de categorizable.CategorizableContainer qui indique que TaskList est
    une collection d'éléments qui peuvent être catégorisés,
    et qu'elle fournit probablement des méthodes pour gérer ces éléments
    (ajouter, supprimer, itérer, etc.).

    Attributs :
        newItemMenuText : Définit le texte du menu pour créer une nouvelle tâche.
                          Il utilise la fonction _() pour l'internationalisation et
                          ajoute un raccourci clavier (INSERT ou Ctrl+N pour Mac).

        newItemHelpText : Contient le texte d'aide pour la création d'une nouvelle tâche,
                          provenant de help.taskNew.

    Méthodes principales :

        nrBeingTracked() : Retourne le nombre de tâches actuellement suivies (en cours).

        tasksBeingTracked() : Retourne une liste de tâches qui sont actuellement suivies.

        efforts() : Collecte et retourne tous les efforts associés à toutes les tâches de la liste.

        originalLength() : Fournit la longueur originale de la liste de tâches,
                           en excluant les tâches marquées comme supprimées.
                           Cela contourne potentiellement la méthode __len__
                           si elle a été modifiée par des décorateurs.

        minPriority() : Retourne la priorité minimale parmi toutes les tâches non supprimées.

        maxPriority() : Retourne la priorité maximale parmi toutes les tâches non supprimées.

        __allPriorities() : Une méthode privée qui récupère toutes les priorités
                            des tâches non supprimées, retournant (0,)
                            si aucune tâche n'est trouvée pour éviter une erreur
                            min() ou max() sur une liste vide.
    """
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
