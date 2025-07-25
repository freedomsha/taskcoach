# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2010 Svetoslav Trochev <sal_electronics@hotmail.com>

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

Module Task

Ce module définit la classe Task, qui représente une tâche dans Task Coach.
Il gère les attributs associés à une tâche, comme les dates, les statuts,
les priorités, les dépendances et d'autres fonctionnalités liées à la gestion
de tâches.

Classes :
Task : Représente une tâche avec diverses propriétés et méthodes
pour gérer son état et ses attributs.

Dépendances :
- taskcoachlib.patterns
- taskcoachlib.domain.date
- taskcoachlib.domain.categorizable
- taskcoachlib.domain.note
- taskcoachlib.domain.attachment
- taskcoachlib.domain.attribute.icon
- pubsub.pub
- _weakrefset.WeakSet
- wx
"""

import logging
import weakref
import wx
from taskcoachlib import patterns
# from taskcoachlib.domain import date, categorizable, base
from taskcoachlib.domain import date, categorizable, note, attachment, base
from taskcoachlib.domain.attribute.icon import getImageOpen
# try:
#    from taskcoachlib.thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
# except ModuleNotFoundError:
from pubsub import pub
# from taskcoachlib.thirdparty._weakrefset import WeakSet
from _weakrefset import WeakSet
from . import status as mod_status
# from .status import TaskStatus

log = logging.getLogger(__name__)


# class Task(base.NoteOwner, base.AttachmentOwner,
class Task(
    note.NoteOwner,
    attachment.AttachmentOwner,
    categorizable.CategorizableCompositeObject,
):
    """
    Classe représentant une tâche dans Task Coach.

    Une tâche peut avoir un titre, une description, des dates de début,
    d'échéance, d'achèvement, un statut, un budget, une priorité et des dépendances.
    Elle peut également contenir des sous-tâches et des catégories.
    """
    maxDateTime = date.DateTime()

    def __init__(self, subject="", description="",
                 dueDateTime=None, plannedStartDateTime=None,
                 actualStartDateTime=None, completionDateTime=None,
                 budget=None, priority=0, id=None, hourlyFee=0,  # pylint: disable=W0622
                 fixedFee=0, reminder=None, reminderBeforeSnooze=None, categories=None,
                 efforts=None, shouldMarkCompletedWhenAllChildrenCompleted=None,
                 recurrence=None, percentageComplete=0, prerequisites=None,
                 dependencies=None, status=mod_status.inactive, *args, **kwargs):
        """ Initialisation de la tâche.

        Initialise une nouvelle tâche avec divers attributs.

        Args :
            subject (str) : Sujet de la tâche.
            description (str) : Description de la tâche.
            dueDateTime (DateTime) : Date d'échéance.
            plannedStartDateTime (DateTime) : Date de début planifiée.
            actualStartDateTime (DateTime) : Date de début réelle.
            completionDateTime (DateTime) : Date d'achèvement.
            budget (TimeDelta) : Temps alloué à la tâche.
            priority (int) : Priorité de la tâche.
            id (str) : Identifiant unique de la tâche.
            hourlyFee (float) : Tarif horaire appliqué à la tâche.
            fixedFee (float) : Tarif fixe associé à la tâche.
            reminder (DateTime) : Date de rappel pour la tâche.
            categories (list) : Liste des catégories assignées à la tâche.
            efforts (list) : Liste des efforts enregistrés.
            shouldMarkCompletedWhenAllChildrenCompleted (bool) : Si vrai,
                la tâche sera marquée comme terminée lorsque toutes ses
                sous-tâches seront complétées.
            recurrence (Recurrence) : Récurrence de la tâche.
            percentageComplete (int) : Pourcentage d'achèvement de la tâche.
            prerequisites (list) : Liste des tâches prérequis.
            dependencies (list) : Liste des tâches dépendantes.
            status (TaskStatus) : Statut initial de la tâche.
        """
        log.debug(f"Task.__init__ : kwargs['status'] = {kwargs.get('status')}, status = {status}")
        kwargs["id"] = id
        kwargs["subject"] = subject
        log.debug(f"Task.__init__ : kwargs['subject'] = subject = {subject}")
        kwargs["description"] = description
        # print(f"🔍 DEBUG - Init de Task '{subject}' avec catégories : {categories}")
        kwargs["categories"] = categories

        # 3️⃣ Appel du constructeur parent
        super().__init__(*args, **kwargs)
        # super().__init__(status=status, *args, **kwargs)
        self.__categories = set() if categories is None else set(categories)
        # print(f"🔍 Task.__init__ : Status reçu AVANT toute initialisation = {status}")
        # Vérifie si le statut passé est une instance de TaskStatus -> trop violent, fait planter !
        # if not isinstance(status, mod_status.TaskStatus):
        #     raise ValueError(f"Le statut doit être une instance de TaskStatus, reçu {status} ({type(status)})")
        # Alternative :
        # Vérifie si le statut est un entier et le convertit en TaskStatus
        # if isinstance(status, int):
        #     # print(f"🔄 Conversion de status {status} en TaskStatus.")
        #     status = mod_status.from_int(status)  # Supposons que TaskStatus a une méthode from_int()

        if "status" in kwargs:
            # print(f"Task.__init__ : ✅ Correction - Statut initial reçu kwargs['status']= {kwargs['status']}")
            # print(f"status = {status}")
            self.__status = status = kwargs["status"]  # Correction
            # print(f"task.__init__ : 🛑 DEBUG - Modification de self.__status pour {self} : {self.__status}")

        # kwargs["status"] = status  # Garde status dans kwargs
        # Il faut forcer l'initialisation de self.__status dans Task AVANT l'appel à super().
        # 1️⃣ Initialisation forcée de self.__status AVANT super()
        # print(f"Task.__init__ : avant attribution de status, self.__status non défini et status={status} soit {mod_status.from_int(status)}")
        # 🛠️ Correction : Si la tâche a une date d'achèvement, on force son statut à "completed"
        # if completionDateTime != date.DateTime.max():
        #     print("Task.__init__ : ⚠️ La tâche a une date d'achèvement, on force son statut à 'completed'")
        #     status = mod_status.completed  # 🛠️ Corrige le statut à 2 (completed)
        self.__status = status
        # print(f"✅ Task.__init__ : après self.__status = {self.__status} ({type(self.__status)})")

        # print(f"✅ Task.__init__ : avant super() initialisation de self.__status = status = {self.__status}")
        # 2️⃣ Supprimer "status" de kwargs pour éviter qu'il ne soit transmis 2 fois
        kwargs.pop("status", None)  # ⚠️ Supprimer status de kwargs pour éviter le doublon !
        # 🔹 DEBUG : Vérifier ce que contient self.__status après l'init
        # print(f"Task.__init__ : 🚀 Après super().__init__() : self.__status = {self.__status}")
        # print(f"Task.__init_ : Vérification si self.__status={self.__status} != kwargs.get('status')={kwargs.get('status')}")
        # if self.__status != kwargs.get("status"):
        #     # print(
        #     #     f"⚠️ Task.__init__ : Correction: self.__status ({self.__status}) ne correspond pas à kwargs['status'] ({kwargs.get('status')})")
        #     self.__status = kwargs.get("status")
        # 🔍 Vérifie si le statut est un entier et le convertit en TaskStatus
        if isinstance(self.__status, int):
            # print(f"Task.__init__ : 🛠 Conversion de {self.__status} en TaskStatus")
            self.__status = mod_status.from_int(self.__status)
            # print(f"task.__init__ : 🛑 DEBUG - Modification de self.__status pour {self} : {self.__status}")

        # 🔹 Correction : Si self.__status est incorrect (1), on le remet à la bonne valeur
        # print(f"Task.__init__ : Vérification si self.__status={self.__status} != status={status}")
        # if self.__status != status:
        #     # print(f"Task.__init__ : ⚠️ Correction: self.__status ({self.__status}) ne correspond pas à status ({status})")
        #     self.__status = status
        #     # print(f"Task.__init__ : ✅ self.__status corrigé : {self.__status}")

        # print(f"Task.__init__ : 🛠 status reçu = {status}")  # Ajoute cette ligne !
        # self.__status = None  # status cache
        #  Task.__init__() ignore complètement status.
        # if "status" in kwargs:
        #     self.__status = kwargs["status"]
        #     # print(f"✅ Task.__init__ : Statut initial reçu = {self.__status}")

        # print(f"Task.__init__ : Finalement : self.__status = {self.__status}")

        self.__dueSoonHours = self.settings.getint("behavior", "duesoonhours")  # pylint: disable=E1101  De quelle classe ?
        maxDateTime = self.maxDateTime
        self.__dueDateTime = dueDateTime or maxDateTime
        self.__plannedStartDateTime = plannedStartDateTime or maxDateTime
        self.__actualStartDateTime = actualStartDateTime or maxDateTime
        if completionDateTime is None and percentageComplete == 100:
            completionDateTime = date.Now()
        self.__completionDateTime = completionDateTime or maxDateTime
        percentageComplete = 100 if self.__completionDateTime != maxDateTime else percentageComplete
        self.__percentageComplete = percentageComplete
        self.__budget = budget or date.TimeDelta()
        self._efforts = efforts or []
        self.__priority = priority
        self.__hourlyFee = hourlyFee
        self.__fixedFee = fixedFee
        self.__reminder = reminder or maxDateTime
        self.__reminderBeforeSnooze = reminderBeforeSnooze or self.__reminder
        self.__recurrence = date.Recurrence() if recurrence is None else recurrence
        self.__prerequisites = WeakSet(prerequisites or [])
        self.__dependencies = WeakSet(dependencies or [])
        self.__shouldMarkCompletedWhenAllChildrenCompleted = \
            shouldMarkCompletedWhenAllChildrenCompleted
        for effort in self._efforts:
            effort.setTask(self)
        pub.subscribe(self.__computeRecursiveForegroundColor, "settings.fgcolor")
        pub.subscribe(self.__computeRecursiveBackgroundColor, "settings.bgcolor")
        pub.subscribe(self.__computeRecursiveIcon, "settings.icon")
        pub.subscribe(self.__computeRecursiveSelectedIcon, "settings.icon")
        pub.subscribe(self.onDueSoonHoursChanged, "settings.behavior.duesoonhours")
        pub.subscribe(self.onMarkParentCompletedWhenAllChildrenCompletedChanged,
                      "settings.behavior.markparentcompletedwhenallchildrencompleted")

        now = date.Now()
        if now < self.__dueDateTime < maxDateTime:
            date.Scheduler().schedule(self.onOverDue, self.__dueDateTime + date.ONE_SECOND)
            if self.__dueSoonHours:
                dueSoonDateTime = self.__dueDateTime + date.ONE_SECOND - date.TimeDelta(hours=self.__dueSoonHours)
                if dueSoonDateTime > date.Now():
                    date.Scheduler().schedule(self.onDueSoon, dueSoonDateTime)
        if now < self.__plannedStartDateTime < maxDateTime:
            date.Scheduler().schedule(self.onTimeToStart, self.__plannedStartDateTime + date.ONE_SECOND)
        # print(
        #     f"🚀 Task créée : {self.subject()} | Status = {self.getStatus()} | PercentageComplete = {self.__percentageComplete} | CompletionDateTime = {self.__completionDateTime}")
        # print(f"📂 DEBUG - Tâche '{self.subject()}' créée avec catégories : {self.categories()}")
        # print(
        #     f"Task.__init__ : completionDateTime={completionDateTime}, self.__completionDateTime={self.__completionDateTime}")

    def __setattr__(self, name, value):
        # if name == "_Task__status" and not isinstance(value, mod_status.TaskStatus):
        #     raise TypeError(f"Tentative d'assignation invalide à self.__status : {value} ({type(value)})")
        log.debug(f"Task.__setattr__ : utilise la méthode super avec name={name} et value={value}.")
        super().__setattr__(name, value)

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """

        Args:
            state:
            event:

        Returns:

        Voici ce qui se passe :

        1. La désérialisation commence au niveau de la classe la plus spécifique, Task.
        2. Task.__setstate__(state) est appelée.
        3. À l'intérieur de Task.__setstate__, tu appelles super().__setstate__(state). Cela signifie que tu passes le state entier à CategorizableCompositeObject.__setstate__.
        4. CategorizableCompositeObject.__setstate__(state) est appelée. Elle fait son propre super().__setstate__(state) en passant encore le state entier.
        5. CompositeObject.__setstate__(state) est appelée. Elle fait son propre super().__setstate__(state) en passant le state entier.
        6. Object.__setstate__(state) est appelée.

        C'est dans Object.__setstate__ que tu as cette ligne :
            subject_from_state = state.pop('subject', '')

        La Solution

        La solution est de s'assurer que state.pop() est appelé une seule fois pour chaque attribut dans la classe la plus basse de la hiérarchie qui est responsable de cet attribut, et que les classes parentes n'essaient pas de "poppper" des attributs qui sont gérés par leurs enfants ou d'autres parents.

        Puisque Object est la classe qui définit et gère l'attribut __subject, c'est elle qui devrait être la seule à pop le sujet du dictionnaire state.

        Les __setstate__ des classes CompositeObject, CategorizableCompositeObject et Task ne devraient pas avoir la ligne subject_from_state = state.pop('subject', '') car elles ne sont pas les propriétaires de l'attribut __subject. Elles devraient uniquement appeler super().__setstate__(state) et gérer les attributs qui sont leur propre responsabilité.

        L'idée est que le dictionnaire state est passé de haut en bas (de Task à Object), et chaque __setstate__ de chaque classe parent ne devrait pop et manipuler que les attributs qui sont strictement sous sa responsabilité. Le subject est une responsabilité de Object.

        """
        log.debug(f"Object.__setstate__() - Entrée, state dict: {state}")
        super().__setstate__(state, event=event)
        self.setPlannedStartDateTime(state["plannedStartDateTime"])
        self.setActualStartDateTime(state["actualStartDateTime"])
        self.setDueDateTime(state["dueDateTime"])
        self.setCompletionDateTime(state["completionDateTime"])
        self.setPercentageComplete(state["percentageComplete"])
        self.setRecurrence(state["recurrence"])
        self.setReminder(state["reminder"])
        self.setEfforts(state["efforts"])
        self.setBudget(state["budget"])
        self.setPriority(state["priority"])
        self.setHourlyFee(state["hourlyFee"])
        self.setFixedFee(state["fixedFee"])
        self.setPrerequisites(state["prerequisites"])
        self.setDependencies(state["dependencies"])
        self.setShouldMarkCompletedWhenAllChildrenCompleted(
            state["shouldMarkCompletedWhenAllChildrenCompleted"]
        )
        # log.debug(f"Object.__setstate__() - subject après set: {self.__subject.get()}")
        # tclib.gui.uicommand.base_uicommand:
        # An error occurred: 'Task' object has no attribute '_Task__subject'
        if hasattr(self, 'subject'):
            log.debug(f"Task.__setstate__() - subject après set: {self.subject}")
        else:
            log.debug("Task.__setstate__() - subject non défini.")

    def __getstate__(self):
        log.debug("Task.__getstate : utilise la méthode super.")
        state = super().__getstate__()
        log.debug(f"Task.__getstate__() avant update : {state}")  # Ajoute ce print
        state.update(dict(dueDateTime=self.__dueDateTime,
                          plannedStartDateTime=self.__plannedStartDateTime,
                          actualStartDateTime=self.__actualStartDateTime,
                          completionDateTime=self.__completionDateTime,
                          percentageComplete=self.__percentageComplete,
                          children=self.children(), parent=self.parent(),
                          efforts=self._efforts, budget=self.__budget,
                          priority=self.__priority,
                          hourlyFee=self.__hourlyFee, fixedFee=self.__fixedFee,
                          recurrence=self.__recurrence.copy(),
                          reminder=self.__reminder,
                          prerequisites=set(self.__prerequisites),
                          dependencies=set(self.__dependencies),
                          shouldMarkCompletedWhenAllChildrenCompleted=self.__shouldMarkCompletedWhenAllChildrenCompleted
                          ))
        log.debug(f"DEBUG - Task.__getstate__() renvoie : {state}")  # Ajoute ce print
        return state

    def __getcopystate__(self):
        state = super().__getcopystate__()
        log.debug(f"DEBUG - Task.__getcopystate__() avant update : {state}")  # Ajoute ce print
        state.update(dict(plannedStartDateTime=self.__plannedStartDateTime,
                          dueDateTime=self.__dueDateTime,
                          actualStartDateTime=self.__actualStartDateTime,
                          completionDateTime=self.__completionDateTime,
                          percentageComplete=self.__percentageComplete,
                          efforts=[effort.copy() for effort in self._efforts],
                          budget=self.__budget, priority=self.__priority,
                          hourlyFee=self.__hourlyFee, fixedFee=self.__fixedFee,
                          recurrence=self.__recurrence.copy(),
                          reminder=self.__reminder,
                          shouldMarkCompletedWhenAllChildrenCompleted=self.__shouldMarkCompletedWhenAllChildrenCompleted
                          ))
        # state["children"] = list(self.children())  # Assure que les enfants sont inclus
        state["children"] = [child.copy() for child in self.children()]  # Créer de nouveaux objets
        log.debug(f"DEBUG - Task.__getcopystate__() renvoie : {state}")  # Ajoute ce print
        return state

    @classmethod
    def monitoredAttributes(class_):
        return (
            categorizable.CategorizableCompositeObject.monitoredAttributes()
            + [
                "plannedStartDateTime",
                "dueDateTime",
                "completionDateTime",
                "percentageComplete",
                "recurrence",
                "reminder",
                "budget",
                "priority",
                "hourlyFee",
                "fixedFee",
                "shouldMarkCompletedWhenAllChildrenCompleted",
            ]
        )

    @patterns.eventSource
    def addCategory(self, *categories, **kwargs):
        """
        Ajoute une ou plusieurs catégories à la tâche.

        Args :
            categories (list) : Catégories à ajouter.
        """
        # print(f"🔍 Ajout de la catégorie '{category.subject()}' à la tâche '{self.subject()}'")
        # print(f"Task.addCategory : 🔍 Ajout de la catégorie '{categories}' à la tâche '{self.subject()}'")
        # if super().addCategory(*categories, **kwargs):
        result = super().addCategory(*categories, **kwargs)
        # print(f"Task.addCategory : ✅ DEBUG - Résultat de super().addCategory() = {result}")
        # print(f"Task.addCategory : ✅ DEBUG - Après ajout, self.categories() = {self.categories()}")

        if result:
            self.recomputeAppearance(True, event=kwargs.pop("event"))

    @patterns.eventSource
    def removeCategory(self, *categories, **kwargs):
        """
        Supprime une ou plusieurs catégories de la tâche.

        Args :
            categories (list) : Catégories à supprimer.
        """
        if super().removeCategory(*categories, **kwargs):
            self.recomputeAppearance(True, event=kwargs.pop("event"))

    @patterns.eventSource
    def setCategories(self, *categories, **kwargs):
        # print(f"⚠️ DEBUG - setCategories() appelée sur {self}, nouvelles catégories = {categories}")
        if super().setCategories(*categories, **kwargs):
            self.recomputeAppearance(True, event=kwargs.pop("event"))

    def allChildrenCompleted(self):
        """ Return whether all children (non-recursively) are completed. """
        children = self.children()
        return all(child.completed() for child in children) if children \
            else False

    @patterns.eventSource
    def addChild(self, child, event=None):
        # print(f"Task.addChild : Avant l'ajout, vérifie si child={child} existe dans self.children={self.children}")
        if child in self.children():
            print(f"Task.addChild : !!! child={child} existe déjà dans self.children={self.children}")
            return
        # print(f"Task.adChildren : !!! ATTENTION !!! ici, child={child} ne doit pas être dans seld.children={self.children}")
        wasTracking = self.isBeingTracked(recursive=True)
        # print(
        #     f"Task.addChild : 👶 Ajout d'un enfant à '{self.subject()}'. Avant : {self.categories()} -> Enfant {child.subject()} : {child.categories()}")
        # print(
        #     f"🔍 DEBUG - Ajout d'un enfant : {child.id()} à {self.id()} | Avant ajout : {[c.id() for c in self.children()]}")
        super().addChild(child, event=event)
        # print(f"✅ Après ajout : child.categories()={child.categories()}")
        # print(f"✅ Après ajout : {[c.id() for c in self.children()]}")
        self.childChangeEvent(child, wasTracking, event)
        if self.shouldBeMarkedCompleted():
            self.setCompletionDateTime(child.completionDateTime())
        elif self.completed() and not child.completed():
            self.setCompletionDateTime(self.maxDateTime)
        self.recomputeAppearance(recursive=False, event=event)
        child.recomputeAppearance(recursive=True, event=event)

    @patterns.eventSource
    def removeChild(self, child, event=None):
        if child not in self.children():
            return
        wasTracking = self.isBeingTracked(recursive=True)
        super().removeChild(child, event=event)
        self.childChangeEvent(child, wasTracking, event)
        if self.shouldBeMarkedCompleted():
            # The removed child was the last uncompleted child
            self.setCompletionDateTime(date.Now())
        self.recomputeAppearance(recursive=False, event=event)
        child.recomputeAppearance(recursive=True, event=event)  # Unresolved attribute reference 'recomputeAppearance' for class 'Composite'

    def childChangeEvent(self, child, wasTracking, event):
        childHasTimeSpent = child.timeSpent(recursive=True)
        childHasBudget = child.budget(recursive=True)
        childHasBudgetLeft = child.budgetLeft(recursive=True)
        childHasRevenue = child.revenue(recursive=True)
        childPriority = child.priority(recursive=True)
        # Determine what changes due to the child being added or removed:
        if childHasTimeSpent:
            self.sendTimeSpentChangedMessage()
        if childHasRevenue:
            self.sendRevenueChangedMessage()
        if childHasBudget:
            self.sendBudgetChangedMessage()
        if childHasBudgetLeft or (childHasTimeSpent and
                                  (childHasBudget or self.budget())):
            self.sendBudgetLeftChangedMessage()
        if childPriority > self.priority():
            self.sendPriorityChangedMessage()
        isTracking = self.isBeingTracked(recursive=True)
        if wasTracking and not isTracking:
            self.sendTrackingChangedMessage(tracking=False)
        elif not wasTracking and isTracking:
            self.sendTrackingChangedMessage(tracking=True)

    @patterns.eventSource
    def setSubject(self, subject, event=None):
        log.debug(f"Task.setSubject : utilise la méthode super pour subject={subject} pour event={event}")
        super().setSubject(subject, event=event)
        # The subject of a dependency of our prerequisites has changed, Notify:
        for prerequisite in self.prerequisites():
            pub.sendMessage(prerequisite.dependenciesChangedEventType(),
                            newValue=prerequisite.dependencies(),
                            sender=prerequisite)
        # The subject of a prerequisite of our dependencies has changed, Notify:
        for dependency in self.dependencies():
            pub.sendMessage(dependency.prerequisitesChangedEventType(),
                            newValue=dependency.prerequisites(),
                            sender=dependency)

    # Due Date

    def dueDateTime(self, recursive=False):
        """
        Retourne la date d'échéance de la tâche.

        Args :
            recursive (bool) : Si vrai, prend en compte les sous-tâches.
        """
        if recursive:
            childrenDueDateTimes = [child.dueDateTime(recursive=True) for child in
                                    self.children() if not child.completed()]
            return min(childrenDueDateTimes + [self.__dueDateTime])
        else:
            return self.__dueDateTime

    def setDueDateTime(self, dueDateTime):
        """
        Définit la date d'échéance de la tâche.

        Args :
            dueDateTime (DateTime) : Nouvelle date d'échéance.
        """
        if dueDateTime == self.__dueDateTime:
            return
        self.__dueDateTime = dueDateTime
        date.Scheduler().unschedule(self.onOverDue)
        date.Scheduler().unschedule(self.onDueSoon)
        if date.Now() <= dueDateTime < self.maxDateTime:
            date.Scheduler().schedule(self.onOverDue,
                                      dueDateTime + date.ONE_SECOND)
            if self.__dueSoonHours > 0:
                dueSoonDateTime = dueDateTime + date.ONE_SECOND - \
                                  date.TimeDelta(hours=self.__dueSoonHours)
                if dueSoonDateTime > date.Now():
                    date.Scheduler().schedule(self.onDueSoon, dueSoonDateTime)
        self.markDirty()
        self.recomputeAppearance()
        pub.sendMessage(self.dueDateTimeChangedEventType(),
                        newValue=dueDateTime, sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.dueDateTimeChangedEventType(),
                            newValue=dueDateTime, sender=ancestor)

    @classmethod
    def dueDateTimeChangedEventType(class_):
        return "pubsub.task.dueDateTime"

    def onOverDue(self):
        self.recomputeAppearance()

    def onDueSoon(self):
        self.recomputeAppearance()

    @staticmethod
    def dueDateTimeSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.dueDateTime(recursive=recursive)

    @classmethod
    def dueDateTimeSortEventTypes(class_):
        """ The event types that influence the due date time sort order. """
        return (class_.dueDateTimeChangedEventType(),)

    # Planned start date

    def plannedStartDateTime(self, recursive=False):
        if recursive:
            childrenPlannedStartDateTimes = [child.plannedStartDateTime(recursive=True) for child in
                                             self.children() if not child.completed()]
            return min(childrenPlannedStartDateTimes + [self.__plannedStartDateTime])
        else:
            return self.__plannedStartDateTime

    def setPlannedStartDateTime(self, plannedStartDateTime):
        if plannedStartDateTime == self.__plannedStartDateTime:
            return
        self.__plannedStartDateTime = plannedStartDateTime
        date.Scheduler().unschedule(self.onTimeToStart)
        self.markDirty()
        self.recomputeAppearance()
        if plannedStartDateTime < self.maxDateTime:
            date.Scheduler().schedule(self.onTimeToStart,
                                      plannedStartDateTime + date.ONE_SECOND)
        pub.sendMessage(self.plannedStartDateTimeChangedEventType(),
                        newValue=plannedStartDateTime, sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.plannedStartDateTimeChangedEventType(),
                            newValue=plannedStartDateTime, sender=ancestor)

    @classmethod
    def plannedStartDateTimeChangedEventType(class_):
        return "pubsub.task.plannedStartDateTime"

    def onTimeToStart(self):
        self.recomputeAppearance()

    @staticmethod
    def plannedStartDateTimeSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.plannedStartDateTime(recursive=recursive)

    @classmethod
    def plannedStartDateTimeSortEventTypes(class_):
        """The event types that influence the planned start date time sort
        order."""
        return (class_.plannedStartDateTimeChangedEventType(),)

    def timeLeft(self, recursive=False):
        return self.dueDateTime(recursive) - date.Now()

    @staticmethod
    def timeLeftSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.timeLeft(recursive=recursive)

    @classmethod
    def timeLeftSortEventTypes(class_):
        """ Types d'événements qui influencent l'ordre de tri du temps restant. """
        # return (class_.dueDateTimeChangedEventType(),)
        # return class_.dueDateTimeChangedEventType()
        # Pour les erreurs de type, assurez-vous que les valeurs retournées correspondent au type attendu.
        return [class_.dueDateTimeChangedEventType(),]

    # Actual start Date

    def actualStartDateTime(self, recursive=False):
        if recursive:
            childrenActualStartDateTimes = [child.actualStartDateTime(recursive=True) for child in
                                            self.children() if not child.completed()]
            return min(childrenActualStartDateTimes + [self.__actualStartDateTime])
        else:
            return self.__actualStartDateTime

    def setActualStartDateTime(self, actualStartDateTime, recursive=False):
        if actualStartDateTime == self.__actualStartDateTime:
            return
        self.__actualStartDateTime = actualStartDateTime
        if recursive:
            for child in self.children(recursive=True):
                child.setActualStartDateTime(actualStartDateTime)
        self.markDirty()
        self.recomputeAppearance()
        pub.sendMessage(self.actualStartDateTimeChangedEventType(),
                        newValue=actualStartDateTime, sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.actualStartDateTimeChangedEventType(),
                            newValue=actualStartDateTime, sender=ancestor)

    @classmethod
    def actualStartDateTimeChangedEventType(class_):
        return "pubsub.task.actualStartDateTime"

    @staticmethod
    def actualStartDateTimeSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.actualStartDateTime(recursive=recursive)

    @classmethod
    def actualStartDateTimeSortEventTypes(class_):
        """ Types d'événements qui influencent l'ordre de tri de la date et de l'heure de début réel."""
        # return (class_.actualStartDateTimeChangedEventType(),)
        return class_.actualStartDateTimeChangedEventType()
        # return [class_.actualStartDateTimeChangedEventType(),]

    # Completion Date

    def completionDateTime(self, recursive=False):
        # print("Task.completionDateTime : est appelé")
        if recursive:
            childrenCompletionDateTimes = [child.completionDateTime(recursive=True)
                                           for child in self.children() if child.completed()]
            return max(childrenCompletionDateTimes + [self.__completionDateTime])
        else:
            return self.__completionDateTime

    def setCompletionDateTime(self, completionDateTime=None):
        """
        Définit la date d'achèvement de la tâche.

        Args :
            completionDateTime (DateTime) : Date d'achèvement, ou None pour réinitialiser.
        """
        # print("Task.setCompletionDateTime : est appelé")
        completionDateTime = completionDateTime or date.Now()
        if completionDateTime == self.__completionDateTime:
            return
        if completionDateTime != self.maxDateTime and self.recurrence():
            self.recur(completionDateTime)
        else:
            parent = self.parent()
            oldParentPriority = None  # A Essayer mais risque d'effacer l'ancienne valeur !
            if parent:
                oldParentPriority = parent.priority(recursive=True)
            self.__status = None
            self.__completionDateTime = completionDateTime
            if parent and parent.priority(recursive=True) != oldParentPriority:
                parent.sendPriorityChangedMessage()
            if completionDateTime != self.maxDateTime:
                self.setReminder(None)
                self.setPercentageComplete(100)
            elif self.percentageComplete() == 100:
                self.setPercentageComplete(0)
            if parent:
                if self.completed():
                    if parent.shouldBeMarkedCompleted():
                        parent.setCompletionDateTime(completionDateTime)
                else:
                    if parent.completed():
                        parent.setCompletionDateTime(self.maxDateTime)
            if self.completed():
                for child in self.children():
                    if not child.completed():
                        child.setRecurrence()
                        child.setCompletionDateTime(completionDateTime)
                if self.isBeingTracked():
                    self.stopTracking()
            self.recomputeAppearance()
            for dependency in self.dependencies():
                dependency.recomputeAppearance(recursive=True)
            pub.sendMessage(self.completionDateTimeChangedEventType(),
                            newValue=completionDateTime, sender=self)
            for ancestor in self.ancestors():
                pub.sendMessage(ancestor.completionDateTimeChangedEventType(),
                                newValue=completionDateTime, sender=ancestor)

    @classmethod
    def completionDateTimeChangedEventType(class_):
        return "pubsub.task.completionDateTime"

    def shouldBeMarkedCompleted(self):
        """ Return whether this task should be marked completed. It should be
            marked completed when 1) it's not completed, 2) all of its children
            are completed, 3) its setting says it should be completed when
            all of its children are completed. """
        shouldMarkCompletedAccordingToSetting = \
            self.settings.getboolean("behavior", "markparentcompletedwhenallchildrencompleted")
        shouldMarkCompletedAccordingToTask = \
            self.shouldMarkCompletedWhenAllChildrenCompleted()
        return ((shouldMarkCompletedAccordingToTask is True) or
                ((shouldMarkCompletedAccordingToTask is None) and
                 shouldMarkCompletedAccordingToSetting)) and \
            (not self.completed()) and self.allChildrenCompleted()

    @staticmethod
    def completionDateTimeSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.completionDateTime(recursive=recursive)

    @classmethod
    def completionDateTimeSortEventTypes(class_):
        """ Types d'événements qui influencent l'ordre de tri de la date et de l'heure d'achèvement. """
        return (class_.completionDateTimeChangedEventType(),)

    def onMarkParentCompletedWhenAllChildrenCompletedChanged(self, value):
        """ When the global setting changes, send a percentage completed
            changed if necessary. """
        if self.shouldMarkCompletedWhenAllChildrenCompleted() is None and \
                any([child.percentageComplete(True) for child in self.children()]):
            pub.sendMessage(self.percentageCompleteChangedEventType(),
                            newValue=self.percentageComplete(), sender=self)

    # Task state

    def completed(self) -> bool:
        """ A task is completed if it has a completion Date/time.

        Vérifie si la tâche est complétée.

        Returns:
            (bool) : True si la tâche est complétée, False sinon.
        """
        # print(
        #     f"Task.completed() appelé pour {self}, status={self.status()}, completionDateTime={self.completionDateTime()}")

        # return self.status() == mod_status.completed
        status = self.status()
        # print(f"Task.completed() -> forcé status = {status}, attendu = {mod_status.completed}")
        return status == mod_status.completed

    def overdue(self):
        # def overdue(self) -> bool:
        """ A task is over due if its due Date/time is in the past and it is
            not completed. Note that an over due task is also either active
            or inactive. """
        return self.status() == mod_status.overdue

    def inactive(self):
        """ A task is inactive if it is not completed and either has no planned
            start Date/time or a planned start Date/time in the future, and/or
            its prerequisites are not completed. """
        return self.status() == mod_status.inactive

    def active(self):
        """ A task is active if it has a planned start Date/time in the past and
            it is not completed. Note that over due and due soon tasks are also
            considered to be active. So the statuses active, inactive and
            completed are disjunct, but the statuses active, due soon and over
            due are not. """
        return self.status() == mod_status.active

    def dueSoon(self):
        """ A task is due soon if it is not completed and there is still time
            left (i.e. it is not over due). """
        return self.status() == mod_status.duesoon

    def late(self):
        """ A task is late if it is not active and its planned start Date time
            is in the past. """
        return self.status() == mod_status.late

    @classmethod
    def possibleStatuses(class_):
        return (mod_status.inactive, mod_status.late, mod_status.active,
                mod_status.duesoon, mod_status.overdue, mod_status.completed)

    def status(self):
        """ Retourne l'état actuel de la tâche sous forme d'une instance de TaskStatus.

        Retourne toujours une instance de TaskStatus.

        Returns :
            TaskStatus : Statut actuel de la tâche.
        """
        # print(f"DEBUG - Task.status() appelé pour {self} - self.__status = {self.__status} ({type(self.__status)})")
        # if not isinstance(self.__status, mod_status.TaskStatus):
        #     raise TypeError(f"Task.status : self.__status est invalide : {self.__status} ({type(self.__status)})")

        # print(f"Task.status : 🔍 Calcul du statut pour {self.subject()} :")
        # print(f"   - completionDateTime = {self.completionDateTime()}")
        # print(f"   - maxDateTime = {self.maxDateTime}")
        # print(f"   - dueDateTime = {self.dueDateTime()}")
        # print(f"   - actualStartDateTime = {self.actualStartDateTime()}")
        # print(f"   - plannedStartDateTime = {self.plannedStartDateTime()}")
        # print(f"   - prerequisites = {[p.subject() for p in self.prerequisites(recursive=True, upwards=True)]}")

        # if self.__status:
        #     # print(f"Task.status :    ✅ Statut de {self.subject()} déjà défini : {self.__status}")
        #     # if isinstance(self.__status, int):  # Vérifie si self.__status est un entier
        #     #     # print(
        #     #     #     f"Task.status : ⚠️ Correction nécessaire: self.__status = {self.__status} est un int, conversion en TaskStatus requise.")
        #     #     self.__status = mod_status.from_int(self.__status)  # Convertit l'entier en TaskStatus
        #     # print(f"Task.status : ✅ Correction effectuée: self.__status = {self.__status}")
        #     return self.__status
        # print(f"Task.status : completionDateTime = {self.completionDateTime()}, maxDateTime = {self.maxDateTime}")

        # # if self.completionDateTime() != self.maxDateTime:
        # if self.completionDateTime() == self.maxDateTime:
        #     # print(f"Task.status :    ✅ Statut de {self.subject()} = completed (2)")
        #     self.__status = mod_status.completed
        #     # print(f"Task.status() : self.__status devient {self.__status} normalement {mod_status.completed}")
        if self.completionDateTime() and self.completionDateTime() != self.maxDateTime:
            # print(f"✅ Task.status : {self.subject()} est terminé (completed)")
            self.__status = mod_status.completed
        else:
            # print("Task.status :    ⚠️ La tâche n'est pas terminée, on continue l'analyse...")
            now = date.Now()
            if self.dueDateTime() < now:
                # print(f"Task.status :    ✅ Statut de {self.subject()} = overdue (3)")
                self.__status = mod_status.overdue
            elif 0 <= self.timeLeft().hours() < self.__dueSoonHours:
                # print(f"Task.status :    ✅ Statut de {self.subject()} = duesoon (4)")
                self.__status = mod_status.duesoon
            elif self.actualStartDateTime() <= now:
                # print(f"Task.status :    ✅ Statut de {self.subject()} = active (1)")
                self.__status = mod_status.active
            # Don't call prerequisite.completed() because it will lead to infinite
            # recursion in the case of circular dependencies:
            elif any([prerequisite.completionDateTime() == self.maxDateTime
                      for prerequisite in self.prerequisites(recursive=True,
                                                             upwards=True)]):
                # print("Task.status :    ✅ Statut = inactive (0) (à cause des prérequis)")
                self.__status = mod_status.inactive
            elif self.plannedStartDateTime() < now:
                # print("Task.status :    ✅ Statut = late (5)")
                self.__status = mod_status.late
            else:
                # print("Task.status :    ✅ Statut = inactive (0)")
                self.__status = mod_status.inactive
        return self.__status

    def onDueSoonHoursChanged(self, value):
        date.Scheduler().unschedule(self.onDueSoon)
        self.__dueSoonHours = value
        dueDateTime = self.dueDateTime()
        if dueDateTime < self.maxDateTime:
            newDueSoonDateTime = dueDateTime + date.ONE_SECOND - date.TimeDelta(hours=self.__dueSoonHours)
            date.Scheduler().schedule(self.onDueSoon, newDueSoonDateTime)
        self.recomputeAppearance()

    # effort related methods:

    def efforts(self, recursive=False):
        childEfforts = []
        if recursive:
            for child in self.children():
                childEfforts.extend(child.efforts(recursive=True))
        return self._efforts + childEfforts

    def isBeingTracked(self, recursive=False):
        return self.activeEfforts(recursive)

    def activeEfforts(self, recursive=False):
        return [effort for effort in self.efforts(recursive)
                if effort.isBeingTracked()]

    def addEffort(self, effort):
        """
        Ajoute un effort à la tâche.

        Args :
            effort (Effort) : Effort à ajouter.
        """
        if effort in self._efforts:
            return
        wasTracking = self.isBeingTracked()
        oldValue = self._efforts[:]
        self._efforts.append(effort)
        if effort.getStart() < self.actualStartDateTime():
            self.setActualStartDateTime(effort.getStart())
        pub.sendMessage(self.effortsChangedEventType(), newValue=(self._efforts,
                                                                  oldValue), sender=self)
        if effort.isBeingTracked() and not wasTracking:
            self.sendTrackingChangedMessage(tracking=True)
        self.sendTimeSpentChangedMessage()

    @classmethod
    def effortsChangedEventType(class_):
        return "pubsub.task.efforts"

    def sendTrackingChangedMessage(self, tracking):
        self.recomputeAppearance()
        pub.sendMessage(self.trackingChangedEventType(), newValue=tracking,
                        sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.trackingChangedEventType(),
                            newValue=tracking, sender=ancestor)

    def removeEffort(self, effort):
        """
        Supprime un effort de la tâche.

        Args :
            effort (Effort) : Effort à supprimer.
        """
        if effort not in self._efforts:
            return
        oldValue = self._efforts[:]
        self._efforts.remove(effort)
        pub.sendMessage(self.effortsChangedEventType(), newValue=(self._efforts,
                                                                  oldValue), sender=self)
        if effort.isBeingTracked() and not self.isBeingTracked():
            self.sendTrackingChangedMessage(tracking=False)
        self.sendTimeSpentChangedMessage()

    def stopTracking(self):
        for effort in self.activeEfforts():
            effort.setStop()

    def setEfforts(self, efforts):
        if efforts == self._efforts:
            return
        oldValue = self._efforts[:]
        self._efforts = efforts
        pub.sendMessage(self.effortsChangedEventType(), newValue=(self._efforts,
                                                                  oldValue), sender=self)
        self.sendTimeSpentChangedMessage()

    @classmethod
    def trackingChangedEventType(class_):  # cls ?
        return "pubsub.task.track"

    # Time spent

    def timeSpent(self, recursive=False):
        return sum((effort.duration() for effort in self.efforts(recursive)),
                   date.TimeDelta())

    def sendTimeSpentChangedMessage(self):
        pub.sendMessage(self.timeSpentChangedEventType(),
                        newValue=self.timeSpent(), sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.timeSpentChangedEventType(),
                            newValue=ancestor.timeSpent(),
                            sender=ancestor)
        if self.budget(recursive=True):
            self.sendBudgetLeftChangedMessage()
        if self.hourlyFee() > 0:
            self.sendRevenueChangedMessage()

    @classmethod
    def timeSpentChangedEventType(class_):  # cls ?
        return "pubsub.task.timeSpent"

    @staticmethod
    def timeSpentSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.timeSpent(recursive=recursive)

    @classmethod
    def timeSpentSortEventTypes(class_):  # cls ?
        """ The event types that influence the time spent sort order. """
        return (class_.timeSpentChangedEventType(),)

    # Budget

    def budget(self, recursive=False):
        """
        Retourne le budget de la tâche.

        Args :
            recursive (bool) : Si vrai, prend en compte les sous-tâches.
        """
        result = self.__budget
        if recursive:
            for task in self.children():
                result += task.budget(recursive)
        return result

    def setBudget(self, budget):
        """
        Définit le budget de la tâche.

        Args :
            budget (TimeDelta) : Nouveau budget.
        """
        if budget == self.__budget:
            return
        self.__budget = budget
        self.sendBudgetChangedMessage()
        self.sendBudgetLeftChangedMessage()

    def sendBudgetChangedMessage(self):
        pub.sendMessage(self.budgetChangedEventType(), newValue=self.budget(),
                        sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.budgetChangedEventType(),
                            newValue=ancestor.budget(recursive=True),
                            sender=ancestor)

    @classmethod
    def budgetChangedEventType(class_):  # cls ?
        return "pubsub.task.budget"

    @staticmethod
    def budgetSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.budget(recursive=recursive)

    @classmethod
    def budgetSortEventTypes(class_):  # cls ?
        """ Types d'événements qui influencent l'ordre de tri du budget. """
        # return (class_.budgetChangedEventType(),)
        return class_.budgetChangedEventType()
        # return [class_.budgetChangedEventType(),]

    # Budget left

    def budgetLeft(self, recursive=False):
        budget = self.budget(recursive)
        return budget - self.timeSpent(recursive) if budget else budget

    def sendBudgetLeftChangedMessage(self):
        pub.sendMessage(self.budgetLeftChangedEventType(),
                        newValue=self.budgetLeft(), sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.budgetLeftChangedEventType(),
                            newValue=ancestor.budgetLeft(recursive=True),
                            sender=ancestor)

    @classmethod
    def budgetLeftChangedEventType(class_):  # cls ?
        return "pubsub.task.budgetLeft"

    @staticmethod
    def budgetLeftSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.budgetLeft(recursive=recursive)

    @classmethod
    def budgetLeftSortEventTypes(class_):  # cls ?
        """ Types d'événements qui influencent l'ordre de tri du budget restant."""
        # return (class_.budgetLeftChangedEventType(),)
        return class_.budgetLeftChangedEventType()
        # return [class_.budgetLeftChangedEventType(),]

    # Foreground color

    def setForegroundColor(self, *args, **kwargs):  # il y a deja une fonction avec ce nom ici
        super().setForegroundColor(*args, **kwargs)
        self.__computeRecursiveForegroundColor()

    def foregroundColor(self, recursive=False):  # il y a deja une variable avec ce nom ici
        if not recursive:
            return super().foregroundColor(recursive)
        try:
            return self.__recursiveForegroundColor
        except AttributeError:
            return self.__computeRecursiveForegroundColor()

    def __computeRecursiveForegroundColor(self, value=None):  # pylint: disable=W0613
        ownColor = super().foregroundColor(False)
        if ownColor:
            recursiveColor = ownColor
        else:
            categoryColor = self._categoryForegroundColor()
            if categoryColor:
                recursiveColor = categoryColor
            else:
                recursiveColor = self.statusFgColor()
        self.__recursiveForegroundColor = recursiveColor  # pylint: disable=W0201
        return recursiveColor

    def statusFgColor(self):
        """ Renvoyer la couleur actuelle de la tâche, en fonction de son statut(completed,
            overdue, duesoon, inactive, or active). """
        return self.fgColorForStatus(self.status())

    @classmethod
    def fgColorForStatus(class_, taskStatus):
        return wx.Colour(
            *eval(class_.settings.get("fgcolor", "%stasks" % taskStatus))
        )  # pylint: disable=E1101

    def appearanceChangedEvent(self, event):
        self.__computeRecursiveForegroundColor()
        self.__computeRecursiveBackgroundColor()
        self.__computeRecursiveIcon()
        self.__computeRecursiveSelectedIcon()
        super().appearanceChangedEvent(event)
        for eachEffort in self.efforts():
            eachEffort.appearanceChangedEvent(event)

    # Background color

    def setBackgroundColor(self, *args, **kwargs):
        super().setBackgroundColor(*args, **kwargs)
        self.__computeRecursiveBackgroundColor()

    def backgroundColor(self, recursive=False):
        if not recursive:
            return super().backgroundColor(recursive)
        try:
            return self.__recursiveBackgroundColor
        except AttributeError:
            return self.__computeRecursiveBackgroundColor()

    def __computeRecursiveBackgroundColor(self, *args, **kwargs):  # pylint: disable=W0613
        ownColor = super().backgroundColor(recursive=False)
        if ownColor:
            recursiveColor = ownColor
        else:
            categoryColor = self._categoryBackgroundColor()
            if categoryColor:
                recursiveColor = categoryColor
            else:
                statusColor = self.statusBgColor()
                if statusColor:
                    recursiveColor = statusColor
                elif self.parent():
                    recursiveColor = self.parent().backgroundColor(recursive=True)
                else:
                    recursiveColor = None
        self.__recursiveBackgroundColor = recursiveColor  # pylint: disable=W0201
        return recursiveColor

    def statusBgColor(self):
        """ Return the current color of task, based on its status (completed,
            overdue, duesoon, inactive, or active). """
        color = self.bgColorForStatus(self.status())
        return None if color == wx.WHITE else color

    @classmethod
    def bgColorForStatus(class_, taskStatus):
        """Retourne la couleur associée à un état de tâche."""
        # print(f"Task.bgColorForStatus : taskStatus={taskStatus} pour class_={class_}, subject={class_}")
        # Vérifie s'il s'agit d'un entier alors le transforme en taskStatus:
        if isinstance(taskStatus, int):
            taskStatus = mod_status.from_int(taskStatus)
        return wx.Colour(
            *eval(class_.settings.get("bgcolor", "%stasks" % taskStatus))
        )  # pylint: disable=E1101

        # color_setting = class_.settings.get("bgcolor", "%stasks" % taskStatus)
        #
        # if not isinstance(color_setting, str):  # 🔹 Vérifie que c'est bien une string
        #     color_setting = "6tasks"  # 🔹 Valeur de secours (inactive)
        #
        # print(f"🔍 DEBUG - bgColorForStatus | taskStatus={taskStatus}, color_setting={color_setting}")
        # return wx.Colour(eval(color_setting))  # 🔹 eval() devrait maintenant fonctionner

    # Font

    def font(self, recursive=False):
        ownFont = super().font(recursive=False)
        if ownFont or not recursive:
            return ownFont
        else:
            categoryFont = self._categoryFont()
            if categoryFont:
                return categoryFont
            else:
                return self.statusFont()

    def statusFont(self):
        """ Return the current font of task, based on its status (completed,
            overdue, duesoon, inactive, or active). """
        return self.fontForStatus(self.status())

    @classmethod
    def fontForStatus(class_, taskStatus):
        nativeInfoString = class_.settings.get("font", "%stasks" % taskStatus)  # pylint: disable=E1101
        # return wx.FontFromNativeInfoString(nativeInfoString) if nativeInfoString else None
        return wx.Font(nativeInfoString) if nativeInfoString else None

    # Icon

    def icon(self, recursive=False):
        if recursive and self.isBeingTracked():
            return "clock_icon"
        myIcon = super().icon()
        if recursive and not myIcon:
            try:
                myIcon = self.__recursiveIcon
            except AttributeError:
                myIcon = self.__computeRecursiveIcon()
        return self.pluralOrSingularIcon(myIcon, native=super().icon() == "")

    def __computeRecursiveIcon(self, *args, **kwargs):  # pylint: disable=W0613
        # pylint: disable=W0201
        self.__recursiveIcon = self.categoryIcon() or self.statusIcon()
        return self.__recursiveIcon

    def selectedIcon(self, recursive=False):
        if recursive and self.isBeingTracked():
            return "clock_icon"
        myIcon = super().selectedIcon()
        if recursive and not myIcon:
            try:
                myIcon = self.__recursiveSelectedIcon
            except AttributeError:
                myIcon = self.__computeRecursiveSelectedIcon()
        return self.pluralOrSingularIcon(myIcon, native=super().selectedIcon == "")

    def __computeRecursiveSelectedIcon(self, *args, **kwargs):  # pylint: disable=W0613
        # pylint: disable=W0201
        self.__recursiveSelectedIcon = self.categorySelectedIcon() or self.statusIcon(selected=True)
        return self.__recursiveSelectedIcon

    def statusIcon(self, selected=False):
        """ Return the current icon of the task, based on its status. """
        return self.iconForStatus(self.status(), selected)

    def iconForStatus(self, taskStatus, selected=False):
        iconName = self.settings.get(
            "icon", "%stasks" % taskStatus
        )  # pylint: disable=E1101
        iconName = self.pluralOrSingularIcon(iconName)
        if selected and iconName.startswith("folder"):
            iconName = getImageOpen(iconName)
        return iconName

    @patterns.eventSource
    def recomputeAppearance(self, recursive=False, event=None):
        self.__status = None  # !!!
        # Need to prepare for AttributeError because the cached recursive values
        # are not set in __init__ for performance reasons
        try:
            previousForegroundColor = self.__recursiveForegroundColor
            previousBackgroundColor = self.__recursiveBackgroundColor
            previousRecursiveIcon = self.__recursiveIcon
            previousRecursiveSelectedIcon = self.__recursiveSelectedIcon
        except AttributeError:
            previousForegroundColor = None
            previousBackgroundColor = None
            previousRecursiveIcon = None
            previousRecursiveSelectedIcon = None
        self.__computeRecursiveForegroundColor()
        self.__computeRecursiveBackgroundColor()
        self.__computeRecursiveIcon()
        self.__computeRecursiveSelectedIcon()
        if self.__recursiveForegroundColor != previousForegroundColor or \
                self.__recursiveBackgroundColor != previousBackgroundColor or \
                self.__recursiveIcon != previousRecursiveIcon or \
                self.__recursiveSelectedIcon != previousRecursiveSelectedIcon:
            event.addSource(self, type=self.appearanceChangedEventType())
        if recursive:
            for child in self.children():
                child.recomputeAppearance(recursive=True, event=event)

    # percentage Complete

    def percentageComplete(self, recursive=False):
        if recursive:
            if self.shouldMarkCompletedWhenAllChildrenCompleted() is None:
                # pylint: disable=E1101
                ignore_me = self.settings.getboolean(
                    "behavior", "markparentcompletedwhenallchildrencompleted"
                )
            else:
                ignore_me = self.shouldMarkCompletedWhenAllChildrenCompleted()
            percentages = []
            if self.__percentageComplete > 0 or not ignore_me:
                percentages.append(self.__percentageComplete)
            percentages.extend([child.percentageComplete(recursive) for child in self.children()])
            return sum(percentages) // len(percentages) if percentages else 0
        else:
            return self.__percentageComplete

    def setPercentageComplete(self, percentage):
        if percentage == self.__percentageComplete:
            return
        oldPercentage = self.__percentageComplete
        self.__percentageComplete = percentage
        if percentage == 100 and oldPercentage != 100 and self.completionDateTime() == self.maxDateTime:
            self.setCompletionDateTime(date.Now())
        elif oldPercentage == 100 and percentage != 100 and self.completionDateTime() != self.maxDateTime:
            self.setCompletionDateTime(self.maxDateTime)
        if 0 < percentage < 100 and self.actualStartDateTime() == date.DateTime():
            self.setActualStartDateTime(date.Now())
        pub.sendMessage(self.percentageCompleteChangedEventType(),
                        newValue=percentage, sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.percentageCompleteChangedEventType(),
                            newValue=ancestor.percentageComplete(recursive=True),
                            sender=ancestor)

    @staticmethod
    def percentageCompleteSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.percentageComplete(recursive=recursive)

    @classmethod
    def percentageCompleteSortEventTypes(class_):
        """ The event types that influence the percentage complete sort order. """
        return (class_.percentageCompleteChangedEventType(),)

    @classmethod
    def percentageCompleteChangedEventType(class_):
        return "pubsub.task.percentageComplete"

    # priority

    def priority(self, recursive=False):
        """
        Retourne la priorité de la tâche.

        Args :
            recursive (bool) : Si vrai, prend en compte les sous-tâches.
        """
        if recursive:
            childPriorities = [child.priority(recursive=True)
                               for child in self.children()
                               if not child.completed()]
            return max(childPriorities + [self.__priority])
        else:
            return self.__priority

    def setPriority(self, priority):
        """
        Définit la priorité de la tâche.

        Args :
            priority (int) : Nouvelle priorité.
        """
        if priority == self.__priority:
            return
        self.__priority = priority
        self.sendPriorityChangedMessage()

    def sendPriorityChangedMessage(self):
        pub.sendMessage(self.priorityChangedEventType(),
                        newValue=self.priority(), sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.priorityChangedEventType(),
                            newValue=ancestor.priority(),
                            sender=ancestor)

    @classmethod
    def priorityChangedEventType(class_):
        return "pubsub.task.priority"

    @staticmethod
    def prioritySortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.priority(recursive=recursive)

    @classmethod
    def prioritySortEventTypes(class_):
        """ The event types that influence the priority sort order. """
        return (class_.priorityChangedEventType(),)

    # Hourly fee

    def hourlyFee(self, recursive=False):  # pylint: disable=W0613
        return self.__hourlyFee

    def setHourlyFee(self, hourlyFee):
        if hourlyFee == self.__hourlyFee:
            return
        self.__hourlyFee = hourlyFee
        pub.sendMessage(self.hourlyFeeChangedEventType(), newValue=hourlyFee,
                        sender=self)
        if self.timeSpent() > date.TimeDelta():
            self.sendRevenueChangedMessage()
            for effort in self.efforts():
                effort.sendRevenueChangedMessage()

    @classmethod
    def hourlyFeeChangedEventType(class_):  # cls ?
        return "pubsub.task.hourlyFee"

    @staticmethod  # pylint: disable=W0613
    def hourlyFeeSortFunction(**kwargs):
        return lambda task: task.hourlyFee()

    @classmethod
    def hourlyFeeSortEventTypes(class_):  # cls ?
        """ The event types that influence the hourly fee sort order. """
        return (class_.hourlyFeeChangedEventType(),)

    # Fixed fee

    def fixedFee(self, recursive=False):
        childFixedFees = sum(child.fixedFee(recursive) for child in
                             self.children()) if recursive else 0
        return self.__fixedFee + childFixedFees

    def setFixedFee(self, fixedFee):
        if fixedFee == self.__fixedFee:
            return
        self.__fixedFee = fixedFee
        pub.sendMessage(self.fixedFeeChangedEventType(), newValue=fixedFee,
                        sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.fixedFeeChangedEventType(),
                            newValue=ancestor.fixedFee(recursive=True),
                            sender=ancestor)
        self.sendRevenueChangedMessage()

    @classmethod
    def fixedFeeChangedEventType(class_):
        return "pubsub.task.fixedFee"

    @staticmethod
    def fixedFeeSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.fixedFee(recursive=recursive)

    @classmethod
    def fixedFeeSortEventTypes(class_):
        """ The event types that influence the fixed fee sort order. """
        return (class_.fixedFeeChangedEventType(),)

    # Revenue

    def revenue(self, recursive=False):
        childRevenues = sum(child.revenue(recursive) for child in
                            self.children()) if recursive else 0
        return self.timeSpent().hours() * self.hourlyFee() + self.fixedFee() + \
            childRevenues

    def sendRevenueChangedMessage(self):
        pub.sendMessage(self.revenueChangedEventType(),
                        newValue=self.revenue(), sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.revenueChangedEventType(),
                            newValue=ancestor.revenue(recursive=True),
                            sender=ancestor)

    @classmethod
    def revenueChangedEventType(class_):
        return "pubsub.task.revenue"

    @staticmethod
    def revenueSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.revenue(recursive=recursive)

    @classmethod
    def revenueSortEventTypes(class_):
        """ The event types that influence the revenue sort order. """
        return (class_.revenueChangedEventType(),)

    # reminder

    def reminder(self, recursive=False, includeSnooze=True):  # pylint: disable=W0613
        if recursive:
            reminders = [child.reminder(recursive=True) for child in
                         self.children()] + [self.__reminder]
            reminders = [reminder for reminder in reminders if reminder]
            return min(reminders) if reminders else None
        else:
            return self.__reminder if includeSnooze else self.__reminderBeforeSnooze

    def setReminder(self, reminderDateTime=None):
        if reminderDateTime == self.maxDateTime:
            reminderDateTime = None
        if reminderDateTime == self.__reminder:
            return
        self.__reminder = reminderDateTime
        self.__reminderBeforeSnooze = reminderDateTime
        pub.sendMessage(self.reminderChangedEventType(),
                        newValue=reminderDateTime, sender=self)
        for ancestor in self.ancestors():
            pub.sendMessage(ancestor.reminderChangedEventType(),
                            newValue=reminderDateTime, sender=ancestor)

    def snoozeReminder(self, timeDelta, now=date.Now):
        if timeDelta:
            self.__reminder = now() + timeDelta
            pub.sendMessage(self.reminderChangedEventType(),
                            newValue=self.__reminder, sender=self)
        else:
            if self.recurrence():
                self.__reminder = None
                pub.sendMessage(self.reminderChangedEventType(),
                                newValue=self.__reminder, sender=self)
            else:
                self.setReminder()

    @classmethod
    def reminderChangedEventType(class_):
        return "pubsub.task.reminder"

    @staticmethod
    def reminderSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        maxDateTime = date.DateTime()
        return lambda task: task.reminder(recursive=recursive) or maxDateTime

    @classmethod
    def reminderSortEventTypes(class_):
        """ The event types that influence the reminder sort order. """
        return (class_.reminderChangedEventType(),)

    # Recurrence

    def recurrence(self, recursive=False, upwards=False):
        if not self.__recurrence and recursive and upwards and self.parent():
            return self.parent().recurrence(recursive, upwards)
        elif recursive and not upwards:
            recurrences = [child.recurrence() for child in self.children(recursive)]
            recurrences.append(self.__recurrence)
            recurrences = [r for r in recurrences if r]
            return min(recurrences) if recurrences else self.__recurrence
        else:
            return self.__recurrence

    def setRecurrence(self, recurrence=None):
        recurrence = recurrence or date.Recurrence()
        if recurrence == self.__recurrence:
            return
        self.__recurrence = recurrence
        pub.sendMessage(self.recurrenceChangedEventType(), newValue=recurrence,
                        sender=self)

    @classmethod
    def recurrenceChangedEventType(class_):
        return "pubsub.task.recurrence"

    @patterns.eventSource
    def recur(self, completionDateTime=None, event=None):
        completionDateTime = completionDateTime or date.Now()
        self.setCompletionDateTime(self.maxDateTime)
        recur = self.recurrence(recursive=True, upwards=True)

        currentDueDateTime = self.dueDateTime()
        if currentDueDateTime != date.DateTime():
            basisForRecurrence = completionDateTime if recur.recurBasedOnCompletion else currentDueDateTime
            nextDueDateTime = recur(basisForRecurrence, next=False)
            nextDueDateTime = nextDueDateTime.replace(hour=currentDueDateTime.hour,
                                                      minute=currentDueDateTime.minute,
                                                      second=currentDueDateTime.second,
                                                      microsecond=currentDueDateTime.microsecond)
            self.setDueDateTime(nextDueDateTime)

        currentPlannedStartDateTime = self.plannedStartDateTime()
        if currentPlannedStartDateTime != date.DateTime():
            if date.DateTime() not in (currentPlannedStartDateTime, currentDueDateTime):
                taskDuration = currentDueDateTime - currentPlannedStartDateTime
                nextPlannedStartDateTime = nextDueDateTime - taskDuration
            else:
                basisForRecurrence = completionDateTime if recur.recurBasedOnCompletion \
                    else currentPlannedStartDateTime
                nextPlannedStartDateTime = recur(basisForRecurrence, next=False)
            nextPlannedStartDateTime = nextPlannedStartDateTime.replace(
                hour=currentPlannedStartDateTime.hour,
                minute=currentPlannedStartDateTime.minute,
                second=currentPlannedStartDateTime.second,
                microsecond=currentPlannedStartDateTime.microsecond)
            self.setPlannedStartDateTime(nextPlannedStartDateTime)

        self.setActualStartDateTime(date.DateTime())
        self.setPercentageComplete(0)
        if self.reminder(includeSnooze=False):
            nextReminder = recur(self.reminder(includeSnooze=False), next=False)
            self.setReminder(nextReminder)
        for child in self.children():
            if not child.recurrence():
                child.recur(completionDateTime, event=event)
        self.recurrence()(next=True)

    @staticmethod
    def recurrenceSortFunction(**kwargs):
        recursive = kwargs.get("treeMode", False)
        return lambda task: task.recurrence(recursive=recursive)

    @classmethod
    def recurrenceSortEventTypes(class_):
        """ The event types that influence the recurrence sort order. """
        return (class_.recurrenceChangedEventType(),)

    # Prerequisites

    def prerequisites(self, recursive=False, upwards=False):
        prerequisites = set(self.__prerequisites)
        if recursive and upwards and self.parent() is not None:
            prerequisites |= self.parent().prerequisites(recursive=True, upwards=True)
        elif recursive and not upwards:
            for child in self.children(recursive=True):
                prerequisites |= child.prerequisites()
        return prerequisites

    def setPrerequisites(self, prerequisites):
        prerequisites = set(prerequisites)
        if prerequisites == self.prerequisites():
            return
        self.__prerequisites = WeakSet(prerequisites)
        self.setActualStartDateTime(self.maxDateTime, recursive=True)
        self.recomputeAppearance(recursive=True)
        pub.sendMessage(self.prerequisitesChangedEventType(),
                        newValue=self.prerequisites(), sender=self)

    def addPrerequisites(self, prerequisites):
        prerequisites = set(prerequisites)
        if prerequisites <= self.prerequisites():
            return
        self.__prerequisites = WeakSet(prerequisites | self.prerequisites())
        self.setActualStartDateTime(self.maxDateTime, recursive=True)
        self.recomputeAppearance(recursive=True)
        pub.sendMessage(self.prerequisitesChangedEventType(),
                        newValue=self.prerequisites(), sender=self)

    def removePrerequisites(self, prerequisites):
        prerequisites = set(prerequisites)
        if self.prerequisites().isdisjoint(prerequisites):
            return
        self.__prerequisites = WeakSet(self.prerequisites() - prerequisites)
        self.recomputeAppearance(recursive=True)
        pub.sendMessage(self.prerequisitesChangedEventType(),
                        newValue=self.prerequisites(), sender=self)

    def addTaskAsDependencyOf(self, prerequisites):
        for prerequisite in prerequisites:
            prerequisite.addDependencies([self])

    def removeTaskAsDependencyOf(self, prerequisites):
        for prerequisite in prerequisites:
            prerequisite.removeDependencies([self])

    @classmethod
    def prerequisitesChangedEventType(class_):
        return "pubsub.task.prerequisites"

    @staticmethod
    def prerequisitesSortFunction(**kwargs):
        """ Return a sort key for sorting by prerequisites. Since a task can
            have multiple prerequisites we first sort the prerequisites by their
            subjects. If the sorter is in tree mode, we also take the
            prerequisites of the children of the task into account, after the
            prerequisites of the task itself. If the sorter is in list
            mode we also take the prerequisites of the parent (recursively) into
            account, again after the prerequisites of the categorizable itself."""

        def sortKeyFunction(task):
            def sortedSubjects(items):
                return sorted([item.subject(recursive=True) for item in items])

            prerequisites = task.prerequisites()
            sortedPrerequisiteSubjects = sortedSubjects(prerequisites)
            isListMode = not kwargs.get("treeMode", False)
            childPrerequisites = task.prerequisites(recursive=True, upwards=isListMode) - prerequisites
            sortedPrerequisiteSubjects.extend(sortedSubjects(childPrerequisites))
            return sortedPrerequisiteSubjects

        return sortKeyFunction

    @classmethod
    def prerequisitesSortEventTypes(class_):
        """ The event types that influence the prerequisites sort order. """
        return (class_.prerequisitesChangedEventType(),)

    # Dependencies

    def dependencies(self, recursive=False, upwards=False):
        dependencies = set(self.__dependencies)
        if recursive and upwards and self.parent() is not None:
            dependencies |= self.parent().dependencies(recursive=True, upwards=True)
        elif recursive and not upwards:
            for child in self.children(recursive=True):
                dependencies |= child.dependencies()
        return dependencies

    def setDependencies(self, dependencies):
        dependencies = set(dependencies)
        if dependencies == self.dependencies():
            return
        self.__dependencies = WeakSet(dependencies)
        pub.sendMessage(self.dependenciesChangedEventType(),
                        newValue=self.dependencies(), sender=self)

    def addDependencies(self, dependencies):
        dependencies = set(dependencies)
        if dependencies <= self.dependencies():
            return
        self.__dependencies = WeakSet(self.dependencies() | dependencies)
        pub.sendMessage(self.dependenciesChangedEventType(),
                        newValue=self.dependencies(), sender=self)

    def removeDependencies(self, dependencies):
        dependencies = set(dependencies)
        if self.dependencies().isdisjoint(dependencies):
            return
        self.__dependencies = WeakSet(self.dependencies() - dependencies)
        pub.sendMessage(self.dependenciesChangedEventType(),
                        newValue=self.dependencies(), sender=self)

    def addTaskAsPrerequisiteOf(self, dependencies):
        for dependency in dependencies:
            dependency.addPrerequisites([self])

    def removeTaskAsPrerequisiteOf(self, dependencies):
        for dependency in dependencies:
            dependency.removePrerequisites([self])

    @classmethod
    def dependenciesChangedEventType(class_):
        return "pubsub.task.dependencies"

    @staticmethod
    def dependenciesSortFunction(**kwargs):
        """ Return a sort key for sorting by dependencies. Since a task can
            have multiple dependencies we first sort the dependencies by their
            subjects. If the sorter is in tree mode, we also take the
            dependencies of the children of the task into account, after the
            dependencies of the task itself. If the sorter is in list
            mode we also take the dependencies of the parent (recursively) into
            account, again after the dependencies of the categorizable itself."""

        def sortKeyFunction(task):
            def sortedSubjects(items):
                return sorted([item.subject(recursive=True) for item in items])

            dependencies = task.dependencies()
            sortedDependencySubjects = sortedSubjects(dependencies)
            isListMode = not kwargs.get("treeMode", False)
            childDependencies = task.dependencies(recursive=True, upwards=isListMode) - dependencies
            sortedDependencySubjects.extend(sortedSubjects(childDependencies))
            return sortedDependencySubjects

        return sortKeyFunction

    @classmethod
    def dependenciesSortEventTypes(class_):
        """ The event types that influence the dependencies sort order. """
        return (class_.dependenciesChangedEventType(),)

    # behavior

    def setShouldMarkCompletedWhenAllChildrenCompleted(self, newValue):
        if newValue == self.__shouldMarkCompletedWhenAllChildrenCompleted:
            return
        self.__shouldMarkCompletedWhenAllChildrenCompleted = newValue
        pub.sendMessage(self.shouldMarkCompletedWhenAllChildrenCompletedChangedEventType(),
                        newValue=newValue, sender=self)
        pub.sendMessage(self.percentageCompleteChangedEventType(),
                        newValue=self.percentageComplete(), sender=self)

    @classmethod
    def shouldMarkCompletedWhenAllChildrenCompletedChangedEventType(class_):
        return "pubsub.task.shouldMarkCompletedWhenAllChildrenCompleted"

    def shouldMarkCompletedWhenAllChildrenCompleted(self):
        return self.__shouldMarkCompletedWhenAllChildrenCompleted

    @classmethod
    def suggestedPlannedStartDateTime(cls, now=date.Now):
        return cls.suggestedDateTime("defaultplannedstartdatetime", now)

    @classmethod
    def suggestedActualStartDateTime(cls, now=date.Now):
        return cls.suggestedDateTime("defaultactualstartdatetime", now)

    @classmethod
    def suggestedDueDateTime(cls, now=date.Now):
        return cls.suggestedDateTime("defaultduedatetime", now)

    @classmethod
    def suggestedCompletionDateTime(cls, now=date.Now):
        return cls.suggestedDateTime("defaultcompletiondatetime", now)

    @classmethod
    def suggestedReminderDateTime(cls, now=date.Now):
        return cls.suggestedDateTime("defaultreminderdatetime", now)

    @classmethod
    def suggestedDateTime(cls, defaultDateTimeSetting, now=date.Now):
        # pylint: disable=E1101,W0142
        defaultDateTime = cls.settings.get("view", defaultDateTimeSetting)
        dummy_prefix, defaultDate, defaultTime = defaultDateTime.split("_")
        dateTime = now()
        currentTime = dict(hour=dateTime.hour, minute=dateTime.minute,
                           second=dateTime.second, microsecond=dateTime.microsecond)
        if defaultDate == "Tomorrow":
            dateTime += date.ONE_DAY
        elif defaultDate == "dayaftertomorrow":
            dateTime += (date.ONE_DAY + date.ONE_DAY)
        elif defaultDate == "nextfriday":
            dateTime = (dateTime + date.ONE_DAY).endOfWorkWeek().replace(**currentTime)
        elif defaultDate == "nextmonday":
            dateTime = (dateTime + date.ONE_WEEK).startOfWorkWeek().replace(**currentTime)

        if defaultTime == "startofday":
            return dateTime.startOfDay()
        elif defaultTime == "startofworkingday":
            startHour = cls.settings.getint("view", "efforthourstart")
            return dateTime.replace(hour=startHour, minute=0,
                                    second=0, microsecond=0)
        elif defaultTime == "currenttime":
            return dateTime
        elif defaultTime == "endofworkingday":
            endHour = cls.settings.getint("view", "efforthourend")
            if endHour >= 24:
                endHour, minute, second = 23, 59, 59
            else:
                minute, second = 0, 0
            return dateTime.replace(hour=endHour, minute=minute,
                                    second=second, microsecond=0)
        elif defaultTime == "endofday":
            return dateTime.endOfDay()

    @classmethod
    def modificationEventTypes(class_):
        eventTypes = super().modificationEventTypes()
        if eventTypes is None:
            eventTypes = []
        return eventTypes + [class_.plannedStartDateTimeChangedEventType(),
                             class_.dueDateTimeChangedEventType(),
                             class_.actualStartDateTimeChangedEventType(),
                             class_.completionDateTimeChangedEventType(),
                             class_.effortsChangedEventType(),
                             class_.budgetChangedEventType(),
                             class_.percentageCompleteChangedEventType(),
                             class_.priorityChangedEventType(),
                             class_.hourlyFeeChangedEventType(),
                             class_.fixedFeeChangedEventType(),
                             class_.reminderChangedEventType(),
                             class_.recurrenceChangedEventType(),
                             class_.prerequisitesChangedEventType(),
                             class_.dependenciesChangedEventType(),
                             class_.shouldMarkCompletedWhenAllChildrenCompletedChangedEventType()]

    # Nouvelles lignes :
    # Décommenter si nécessaire mais ne fonctionne pas encore:
    # def __lt__(self, other):
    #     """Compare deux tâches par leur ID."""
    #     return self.id < other.id
    
    def addNote(self, aNote):
        pass

    def addAttachments(self, param):
        pass

    @classmethod
    def attachmentsChangedEventType(cls):
        pass

    @classmethod
    def notesChangedEventType(cls):
        pass
