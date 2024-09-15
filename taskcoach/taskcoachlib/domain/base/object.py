# -*- coding: utf-8 -*-

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

from taskcoachlib import patterns
from taskcoachlib.domain.attribute import icon
from taskcoachlib.domain.date import DateTime, Now
from pubsub import pub
from . import attribute
import functools
import sys
import uuid
import re


class SynchronizedObject(object):
    """
    Une classe de base pour les objets synchronisés.

    Cette classe fournit des méthodes pour marquer les objets comme nouveaux, modifiés, supprimés ou aucun
    et synchronise ces états avec des événements.
    """

    STATUS_NONE = 0
    STATUS_NEW = 1
    STATUS_CHANGED = 2
    STATUS_DELETED = 3

    def __init__(self, *args, **kwargs):
        """
        Initialisez l'instance SynchronizedObject.

        Args:
            *args: Liste d’arguments de longueur(length) variable.
            **kwargs: Arbitrary keyword arguments.
        """
        self.__status = kwargs.pop("status", self.STATUS_NEW)
        super().__init__(*args, **kwargs)

    @classmethod
    def markDeletedEventType(class_):
        """
        Obtenir le type d'événement pour marquer un objet comme supprimé.

        Returns:
            str: Le type d'événement pour marquer un objet comme supprimé.
        """
        return "object.markdeleted"

    @classmethod
    def markNotDeletedEventType(class_):
        """
        Obtenir le type d'événement pour marquer un objet comme non supprimé.

        Returns:
            str: Type d'événement permettant de marquer un objet comme non supprimé.
        """
        return "object.marknotdeleted"

    def __getstate__(self):
        """
        Obtenez l'état de l'objet pour la sérialisation.

        Returns:
            dict: L'état de l'objet.
        """
        try:
            state = super().__getstate__()
        except AttributeError:
            state = dict()

        state["status"] = self.__status
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """
        Définissez l'état de l'objet à partir de la désérialisation.

        Args:
            state (dict): L’état à définir.
            event: L'événement associé à la définition de l'état.
        """
        try:
            super().__setstate__(state, event=event)
        except AttributeError:
            pass
        if state["status"] != self.__status:
            if state["status"] == self.STATUS_CHANGED:
                self.markDirty(event=event)
            elif state["status"] == self.STATUS_DELETED:
                self.markDeleted(event=event)
            elif state["status"] == self.STATUS_NEW:
                self.markNew(event=event)
            elif state["status"] == self.STATUS_NONE:
                self.cleanDirty(event=event)

    def getStatus(self):
        """
        Obtenez l'état actuel de l'objet.

        Returns:
            int: Le statut actuel.
        """
        return self.__status

    @patterns.eventSource
    def markDirty(self, force=False, event=None):
        """
        Marquez l'objet comme sale (modifié).

        Args:
            force (bool, optional): Forcer le marquage de l'objet comme sale. La valeur par défaut est False.
            event: L'événement associé au marquage de l'objet comme sale.
        """
        if not self.setStatusDirty(force):
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusDirty(self, force=False):
        """
        Définissez le statut de l'objet comme sale (modifié).

        Args:
            force (bool, optional): Forcer la définition du statut comme sale. La valeur par défaut est False.

        Returns:
            bool: True si le statut a été modifié et non supprimé, False dans le cas contraire.
        """
        oldStatus = self.__status
        if self.__status == self.STATUS_NONE or force:
            self.__status = self.STATUS_CHANGED
            return oldStatus == self.STATUS_DELETED
        else:
            return False

    @patterns.eventSource
    def markNew(self, event=None):
        """
        Marquez l'objet comme neuf-nouveau(new).

        Args:
            event: L'événement associé au marquage de l'objet comme nouveau.
        """
        if not self.setStatusNew():
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusNew(self):
        """
        Définissez le statut de l'objet comme nouveau.

        Returns:
            bool: Vrai si le statut a été modifié et non supprimé, faux dans le cas contraire.
        """
        oldStatus = self.__status
        self.__status = self.STATUS_NEW
        return oldStatus == self.STATUS_DELETED

    @patterns.eventSource
    def markDeleted(self, event=None):
        """
        Marquez l'objet comme supprimé.

        Args:
            event: L'événement associé au marquage de l'objet comme supprimé.
        """
        self.setStatusDeleted()
        event.addSource(self, self.__status, type=self.markDeletedEventType())

    def setStatusDeleted(self):
        """
        Définissez le statut de l'objet comme supprimé.
        """
        self.__status = self.STATUS_DELETED

    @patterns.eventSource
    def cleanDirty(self, event=None):
        """
        Marquez l'objet comme non sale (aucun).

        Args:
            event: L'événement associé au marquage de l'objet comme non sale.
        """
        if not self.setStatusNone():
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusNone(self):
        """
        Définissez le statut de l'objet sur aucun.

        Returns:
            bool: Vrai si le statut a été modifié et non supprimé, Faux dans le cas contraire.
        """
        oldStatus = self.__status
        self.__status = self.STATUS_NONE
        return oldStatus == self.STATUS_DELETED

    def isNew(self):
        """
        Vérifiez si l'objet est nouveau.

        Returns:
            bool: True if the object is new, False otherwise.
        """
        return self.__status == self.STATUS_NEW

    def isModified(self):
        """
        Vérifiez si l'objet est modifié (sale).

        Returns:
            bool: True if the object is modified, False otherwise.
        """
        return self.__status == self.STATUS_CHANGED

    def isDeleted(self):
        """
        Vérifiez si l'objet est supprimé.

        Returns:
            bool: True if the object is deleted, False otherwise.
        """
        return self.__status == self.STATUS_DELETED

    def __getcopystate__(self):
        pass

    def modificationEventTypes(self):
        pass


class Object(SynchronizedObject):
    """
    Une classe de base pour les objets avec des attributs et des fonctionnalités communs.

    Cette classe étend SynchronizedObject pour fournir des attributs supplémentaires
    et des méthodes permettant de gérer l'état et le comportement d'un objet.
    """

    rx_attributes = re.compile(r"\[(\w+):(.+)\]")

    if sys.version_info.major == 2:
        _long_zero = int(0)
    else:
        _long_zero = 0

    def __init__(self, *args, **kwargs):
        """
        Initialisez l'instance d'objet.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        Attribute = attribute.Attribute
        self.__creationDateTime = kwargs.pop("creationDateTime", None) or Now()
        self.__modificationDateTime = kwargs.pop(
            "modificationDateTime", DateTime.min
        )
        self.__subject = Attribute(
            kwargs.pop("subject", ""), self, self.subjectChangedEvent
        )
        self.__description = Attribute(
            kwargs.pop("description", ""), self, self.descriptionChangedEvent
        )
        self.__fgColor = Attribute(
            kwargs.pop("fgColor", None), self, self.appearanceChangedEvent
        )
        self.__bgColor = Attribute(
            kwargs.pop("bgColor", None), self, self.appearanceChangedEvent
        )
        self.__font = Attribute(
            kwargs.pop("font", None), self, self.appearanceChangedEvent
        )
        self.__icon = Attribute(
            kwargs.pop("icon", ""), self, self.appearanceChangedEvent
        )
        self.__selectedIcon = Attribute(
            kwargs.pop("selectedIcon", ""), self, self.appearanceChangedEvent
        )
        self.__ordering = Attribute(
            kwargs.pop("ordering", Object._long_zero),
            self,
            self.orderingChangedEvent,
        )
        self.__id = kwargs.pop("id", None) or str(uuid.uuid1())
        super().__init__(*args, **kwargs)

    def __repr__(self):
        """
        Renvoie une représentation sous forme de chaîne de l'instance d'objet.

        Returns:
            str: La représentation sous forme de chaîne.
        """
        return self.subject()

    def __getstate__(self):
        """
        Obtenez l'état de l'objet pour la sérialisation.

        Returns:
            dict: L'état de l'objet.
        """
        try:
            state = super().__getstate__()
        except AttributeError:
            state = dict()
        state.update(
            dict(
                id=self.__id,
                creationDateTime=self.__creationDateTime,
                modificationDateTime=self.__modificationDateTime,
                subject=self.__subject.get(),
                description=self.__description.get(),
                fgColor=self.__fgColor.get(),
                bgColor=self.__bgColor.get(),
                font=self.__font.get(),
                icon=self.__icon.get(),
                ordering=self.__ordering.get(),
                selectedIcon=self.__selectedIcon.get(),
            )
        )
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """
        Définissez l'état de l'objet à partir de la désérialisation.

        Args:
            state (dict): L’état à définir.
            event: L'événement associé à la définition de l'état.
        """
        try:
            super().__setstate__(state, event=event)
        except AttributeError:
            pass
        self.__id = state["id"]
        self.setSubject(state["subject"], event=event)
        self.setDescription(state["description"], event=event)
        self.setForegroundColor(state["fgColor"], event=event)
        self.setBackgroundColor(state["bgColor"], event=event)
        self.setFont(state["font"], event=event)
        self.setIcon(state["icon"], event=event)
        self.setSelectedIcon(state["selectedIcon"], event=event)
        self.setOrdering(state["ordering"], event=event)
        self.__creationDateTime = state["creationDateTime"]
        # Set modification date/time last to overwrite changes made by the
        # setters above
        self.__modificationDateTime = state["modificationDateTime"]

    def __getcopystate__(self):
        """
        Renvoie un dictionnaire qui peut être transmis à __init__ lors de la création
        d'une copie de l'objet.

        E.g. copy = obj.__class__(**original.__getcopystate__())

        Returns:
            dict: Le dictionnaire d'état pour créer une copie.
        """
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        # Notez que nous ne mettons pas l'identifiant et la date/heure de création dans le dict state,
        # car une copie devrait obtenir un nouvel identifiant et une nouvelle date/heure de création.
        state.update(
            dict(
                subject=self.__subject.get(),
                description=self.__description.get(),
                fgColor=self.__fgColor.get(),
                bgColor=self.__bgColor.get(),
                font=self.__font.get(),
                icon=self.__icon.get(),
                selectedIcon=self.__selectedIcon.get(),
                ordering=self.__ordering.get(),
            )
        )
        return state

    def copy(self):
        """
        Créez une copie de l'objet.

        Returns:
            Object: Une nouvelle instance de l'objet avec le même état.
        """
        return self.__class__(**self.__getcopystate__())

    @classmethod
    def monitoredAttributes(class_):
        """
        Obtenez la liste des attributs surveillés.

        Returns:
            list: La liste des attributs surveillés.
        """
        return ["ordering", "subject", "description", "appearance"]

    # Id:

    def id(self):
        """
        Obtenez l'ID de l'objet.

        Returns:
            str: L'ID de l'objet.
        """
        return self.__id

    # Custom attributes
    def customAttributes(self, sectionName):
        """
        Obtenez les attributs personnalisés pour un nom de section donné.

        Args:
            sectionName (str): Le nom de la section.

        Returns:
            set: L'ensemble des attributs personnalisés.
        """
        attributes = set()
        for line in self.description().split("\n"):
            match = self.rx_attributes.match(line.strip())
            if match and match.group(1) == sectionName:
                attributes.add(match.group(2))
        return attributes

    # Editing date/time:

    def creationDateTime(self):
        """
        Obtenez la date et l'heure de création de l'objet.

        Returns:
            DateTime: La date et l'heure de création.
        """
        return self.__creationDateTime

    def modificationDateTime(self):
        """
        Obtenez la date et l'heure de modification de l'objet.

        Returns:
            DateTime: La date et l'heure de modification.
        """
        return self.__modificationDateTime

    def setModificationDateTime(self, dateTime):
        """
        Définissez la date et l'heure de modification de l'objet.

        Args:
            dateTime (DateTime): La date et l'heure de modification.
        """
        self.__modificationDateTime = dateTime

    @staticmethod
    def modificationDateTimeSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par date et heure de modification.

        Returns:
            function: La fonction de tri.
        """
        return lambda item: item.modificationDateTime()

    @staticmethod
    def creationDateTimeSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par date et heure de création.

        Returns:
            function: La fonction de tri.
        """
        return lambda item: item.creationDateTime()

    # Subject:

    def subject(self):
        """
        Obtenez le sujet de l'objet.

        Returns:
            str: Le sujet de l'objet.
        """
        return self.__subject.get()

    def setSubject(self, subject, event=None):
        """
        Définissez le sujet de l'objet.

        Args:
            subject (str): Le sujet à définir.
            event: Événement associé à la définition du sujet.
        """
        self.__subject.set(subject, event=event)

    def subjectChangedEvent(self, event):
        """
        Gérer l'événement de changement de sujet.

        Args:
            event: L'événement.
        """
        event.addSource(
            self, self.subject(), type=self.subjectChangedEventType()
        )

    @classmethod
    def subjectChangedEventType(class_):
        """
        Obtenir le type d’événement pour les événements à sujet modifié.

        Returns:
            str: Type d'événement pour les événements de changement de sujet.
        """
        return "%s.subject" % class_
        # return f"{class_}.subject"

    @staticmethod
    def subjectSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par sujet.

        Fonction à passer à list.sort lors du tri par sujet.

        Returns:
            function: La fonction de tri.
        """
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.subject()
        else:
            return lambda item: item.subject().lower()

    @classmethod
    def subjectSortEventTypes(class_):
        """
        Obtenez les types d'événements qui influencent l'ordre de tri des sujets.

        Returns:
            tuple: Les types d'événements.
        """
        return (class_.subjectChangedEventType(),)

    # Ordering:

    def ordering(self):
        """
        Obtenez l'ordre de l'objet.

        Returns:
            int: L'ordre.
        """
        return self.__ordering.get()

    def setOrdering(self, ordering, event=None):
        """
        Définissez l'ordre de l'objet.

        Args:
            ordering (int): L'ordre à définir.
            event: Événement associé à la définition de l'ordre.
        """
        self.__ordering.set(ordering, event=event)

    def orderingChangedEvent(self, event):
        """
        Gérez l’événement de modification de l'ordre.

        Args:
            event: L'événement.
        """
        event.addSource(
            self, self.ordering(), type=self.orderingChangedEventType()
        )

    @classmethod
    def orderingChangedEventType(class_):
        """
        Obtenez le type d'événement pour ordonner les événements modifiés.

        Returns:
            str: Type d'événement pour classer les événements modifiés.
        """
        return "%s.ordering" % class_

    @staticmethod
    def orderingSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par ordre.

        Returns:
            function: La fonction de tri.
        """
        return lambda item: item.ordering()

    @classmethod
    def orderingSortEventTypes(class_):
        """
        Obtenez les types d’événements qui influencent l’ordre de tri.

        Returns:
            tuple: Les types d'événements.
        """
        return (class_.orderingChangedEventType(),)

    # Description:

    def description(self):
        """
        Obtenir la description de l'objet.

        Returns:
            str: La description de l'objet.
        """
        return self.__description.get()

    def setDescription(self, description, event=None):
        """
        Définir la description de l'objet.

        Args:
            description (str): La description à définir.
            event: Événement associé à la définition de la description.
        """
        self.__description.set(description, event=event)

    def descriptionChangedEvent(self, event):
        """
        Gérer l’événement de modification de description.

        Args:
            event: L'événement.
        """
        event.addSource(
            self, self.description(), type=self.descriptionChangedEventType()
        )

    @classmethod
    def descriptionChangedEventType(class_):
        """
        Obtenez le type d’événement pour les événements modifiés dans la description.

        Returns:
            str: Le type d'événement pour la description des événements a changé.
        """
        return "%s.description" % class_

    @staticmethod
    def descriptionSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par description.

        Fonction à transmettre à list.sort lors du tri par description.

        Returns:
            function: La fonction de tri.
        """
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.description()
        else:
            return lambda item: item.description().lower()

    @classmethod
    def descriptionSortEventTypes(class_):
        """
        Obtenez les types d’événements qui influencent l’ordre de tri des descriptions.

        Returns:
            tuple: Les types d'événements.
        """
        return (class_.descriptionChangedEventType(),)

    # Color:

    def setForegroundColor(self, color, event=None):
        """
        Définissez la couleur de premier plan de l'objet.

        Args:
            color: La couleur à définir.
            event: L'événement associé à la définition de la couleur.
        """
        self.__fgColor.set(color, event=event)

    def foregroundColor(self, recursive=False):  # pylint: disable=W0613
        """
        Obtenez la couleur de premier plan de l'objet.

        Args:
            recursive (bool, optional): S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Returns:
            La couleur de premier plan.
        """
        # L'argument 'récursif' n'est pas réellement utilisé ici, mais certains codes
        # supposent des objets composites là où il n'y en a pas. Il s'agit de
        # la solution de contournement la plus simple.
        return self.__fgColor.get()

    def setBackgroundColor(self, color, event=None):
        """
        Définissez la couleur d'arrière-plan de l'objet.

        Args:
            color: La couleur à définir.
            event: L'événement associé à la définition de la couleur.
        """
        self.__bgColor.set(color, event=event)

    def backgroundColor(self, recursive=False):  # pylint: disable=W0613
        """
        Obtenez la couleur d'arrière-plan de l'objet.

        Args:
            recursive (bool, optional): S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Returns:
            La couleur d’arrière-plan.
        """
        # L'argument 'récursif' n'est pas réellement utilisé ici, mais certains codes
        # supposent des objets composites là où il n'y en a pas. Il s'agit de
        # la solution de contournement la plus simple.
        return self.__bgColor.get()

    # Font:

    def font(self, recursive=False):  # pylint: disable=W0613
        """
        Obtenez la police de l'objet.

        Args:
            recursive (bool, optional): S'il faut obtenir la police de manière récursive. La valeur par défaut est False.

        Returns:
            La police.
        """
        # L'argument 'récursif' n'est pas réellement utilisé ici, mais certains codes
        # supposent des objets composites là où il n'y en a pas. Il s'agit de
        # la solution de contournement la plus simple.
        return self.__font.get()

    def setFont(self, font, event=None):
        """
        Définissez la police de l'objet.

        Args:
            font: La police à définir.
            event: L'événement associé à la définition de la police.
        """
        self.__font.set(font, event=event)

    # Icons:

    def icon(self):
        """
        Obtenez l'icône de l'objet.

        Returns:
            L'icône.
        """
        return self.__icon.get()

    def setIcon(self, icon, event=None):
        """
        Définissez l'icône de l'objet.

        Args:
            icon: L'icône à définir.
            event: L'événement associé à la définition de l'icône.
        """
        self.__icon.set(icon, event=event)

    def selectedIcon(self):
        """
        Obtenez l'icône sélectionnée de l'objet.

        Returns:
            L'icône sélectionnée.
        """
        return self.__selectedIcon.get()

    def setSelectedIcon(self, selectedIcon, event=None):
        """
        Définir l'icône sélectionnée à l'objet.

        Args:
            selectedIcon: L'icône sélectionnée à définir.
            event: L'événement associé à la définition de l'icône sélectionnée.
        """
        self.__selectedIcon.set(selectedIcon, event=event)

    # Event types:

    @classmethod
    def appearanceChangedEventType(class_):
        """
        Obtenez le type d’événement pour les événements d’apparence modifiée.

        Returns:
            str: Le type d'événement pour les événements d'apparence a changé.
        """
        return "%s.appearance" % class_
        # return f"{class_}.appearance"

    def appearanceChangedEvent(self, event):
        """
        Gérer l’événement de modification d’apparence.

        Args:
            event: L'événement.
        """
        event.addSource(self, type=self.appearanceChangedEventType())

    @classmethod
    def modificationEventTypes(class_):
        """
        Obtenez les types d'événements pour les événements de modification.

        Returns:
            list: La liste des types d'événements.
        """
        try:
            # eventTypes = super(Object, class_).modificationEventTypes()
            eventTypes = super().modificationEventTypes()
            # TypeError: SynchronizedObject.modificationEventTypes() missing 1 required positional argument: 'self'
            # @classmethod def cmeth(cls, arg):
            #  super().cmeth(arg)
        except TypeError:  # TODO: pas sûr de ses 2 lignes
            eventTypes = super().modificationEventTypes(class_)
        except AttributeError:
            # except AttributeError or TypeError:
            eventTypes = []
        if eventTypes is None:
            eventTypes = []
        return eventTypes + [
            class_.subjectChangedEventType(),
            class_.descriptionChangedEventType(),
            class_.appearanceChangedEventType(),
            class_.orderingChangedEventType(),
        ]


class CompositeObject(Object, patterns.ObservableComposite):
    """
    Un objet composite qui peut contenir d'autres objets en tant qu'enfants.

    Cette classe étend Object et ObservableComposite pour fournir des méthodes supplémentaires
    pour gérer les objets enfants et leur état.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise l'instance CompositeObject.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.__expandedContexts = set(kwargs.pop("expandedContexts", []))
        super().__init__(*args, **kwargs)

    def __getcopystate__(self):
        """
        Renvoie un dictionnaire qui peut être transmis à __init__ lors de la création
        d'une copie de l'objet composite.

        Returns:
            dict: Le dictionnaire d'état pour créer une copie.
        """
        state = super().__getcopystate__()
        state.update(dict(expandedContexts=self.expandedContexts()))
        return state

    @classmethod
    def monitoredAttributes(class_):
        # def monitoredAttributes(cls):
        """
        Obtenir la liste des attributs surveillés.

        Returns:
            list: The list of monitored attributes.
        """
        return Object.monitoredAttributes() + ["expandedContexts"]

    # Subject:

    def subject(self, recursive=False):  # pylint: disable=W0221
        """
        Obtenir le sujet de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir le sujet de manière récursive. La valeur par défaut est False.

        Returns:
            str: Le sujet de l'objet composite.
        """
        subject = super().subject()
        if recursive and self.parent():
            subject = "%s -> %s" % (
                self.parent().subject(recursive=True),
                subject,
            )
        return subject

    def subjectChangedEvent(self, event):
        """
        Gérer l'événement de changement de sujet.

        Args:
            event: L'événement.
        """
        super().subjectChangedEvent(event)
        for child in self.children():
            child.subjectChangedEvent(event)

    @staticmethod
    def subjectSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par sujet.

        Fonction à passer à list.sort lors du tri par sujet.

        Returns:
            function: La fonction de tri.
        """
        recursive = kwargs.get("treeMode", False)
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.subject(recursive=recursive)
        else:
            return lambda item: item.subject(recursive=recursive).lower()

    # Description:

    def description(self, recursive=False):  # pylint: disable=W0221,W0613
        """
        Obtenez la description de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir la description de manière récursive. La valeur par défaut est False.

        Returns:
            str: La description de l'objet composite.
        """
        # Autoriser l'indicateur récursif, mais ignorer le
        return super().description()

    # État d'expansion :

    # Remarque : l'état d'expansion est stocké par contexte. Un contexte est une simple chaîne
    # identifiant (sans virgules) pour distinguer les différents contextes,
    # c'est-à-dire les téléspectateurs. Un objet composite peut être développé dans un contexte et
    # réduit dans un autre.

    def isExpanded(self, context="None"):
        """
        Vérifiez si l'objet composite est développé dans le contexte spécifié.

        Renvoie un booléen indiquant si l'objet composite est
        développé dans le contexte spécifié.

        Args:
            context (str, optional): Le contexte. La valeur par défaut est "Aucun".

        Returns:
            bool: True si l'objet composite est développé, False sinon.
        """
        return context in self.__expandedContexts

    def expandedContexts(self):
        """
        Obtenez la liste des contextes dans lesquels l'objet composite est développé.

        Returns:
            list: La liste des contextes.
        """
        return list(self.__expandedContexts)

    def expand(self, expand=True, context="None", notify=True):
        """
        Développez ou réduisez l'objet composite dans le contexte spécifié.

        Args:
            expand (bool, optional): Que ce soit pour s'étendre ou s'effondrer. La valeur par défaut est True.
            context (str, optional): Le contexte. La valeur par défaut est "Aucun".
            notify (bool, optional): S'il faut envoyer une notification. La valeur par défaut est True.
        """
        if expand == self.isExpanded(context):
            return
        if expand:
            self.__expandedContexts.add(context)
        else:
            self.__expandedContexts.discard(context)
        if notify:
            pub.sendMessage(
                self.expansionChangedEventType(), newValue=expand, sender=self
            )

    @classmethod
    def expansionChangedEventType(cls):
        """
        Obtenez le type d'événement pour les changements d'état d'expansion.

        Le type d'événement utilisé pour notifier les changements dans l'état d'expansion
        d'un objet composite.

        Returns:
            str: Le type d’événement pour les changements d’état d’expansion.
        """
        return "pubsub.%s.expandedContexts" % cls.__name__.lower()
        # return f"pubsub.{cls.__name__.lower()}.expandedContexts"

    def expansionChangedEvent(self, event):
        """
        Gérer l’événement de modification d’extension.

        Args:
            event: L'événement.
        """
        event.addSource(self, type=self.expansionChangedEventType())

    # Le ChangeMonitor s'attend à cela...
    @classmethod
    def expandedContextsChangedEventType(class_):
        """
        Obteneir le type d’événement pour les modifications de contextes étendus.

        Returns:
            str: Le type d'événement pour les contextes étendus change.
        """
        return class_.expansionChangedEventType()

    # Appearance:

    def appearanceChangedEvent(self, event):
        """
        Gérer l’événement de modification d’apparence.

        Args:
            event: L'événement.
        """
        super().appearanceChangedEvent(event)
        # Supposons que la plupart du temps, nos enfants changent également d'apparence.
        for child in self.children():
            child.appearanceChangedEvent(event)

    def foregroundColor(self, recursive=False):
        """
        Obtenez la couleur de premier plan de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Returns:
            La couleur de premier plan.
        """
        myFgColor = super().foregroundColor()
        if not myFgColor and recursive and self.parent():
            return self.parent().foregroundColor(recursive=True)
        else:
            return myFgColor

    def backgroundColor(self, recursive=False):
        """
        Obtenez la couleur d'arrière-plan de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Returns:
            La couleur d’arrière-plan.
        """
        myBgColor = super().backgroundColor()
        if not myBgColor and recursive and self.parent():
            return self.parent().backgroundColor(recursive=True)
        else:
            return myBgColor

    def font(self, recursive=False):
        """
        Obtenez la police de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir la police de manière récursive. La valeur par défaut est False.

        Returns:
            La police.
        """
        myFont = super().font()
        if not myFont and recursive and self.parent():
            return self.parent().font(recursive=True)
        else:
            return myFont

    def icon(self, recursive=False):
        """
        Obtenez l'icône de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir l'icône de manière récursive. La valeur par défaut est False.

        Returns:
            L'icône.
        """
        myIcon = super().icon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().icon(recursive=True)
        return self.pluralOrSingularIcon(myIcon, native=super().icon() == "")

    def selectedIcon(self, recursive=False):
        """
        Obtenez l'icône sélectionnée de l'objet composite.

        Args:
            recursive (bool, optional): S'il faut obtenir l'icône sélectionnée de manière récursive. La valeur par défaut est False.

        Returns:
            L'icône sélectionnée.
        """
        myIcon = super().selectedIcon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().selectedIcon(recursive=True)
        return self.pluralOrSingularIcon(
            myIcon, native=super().selectedIcon() == ""
        )

    def pluralOrSingularIcon(self, myIcon, native=True):
        """
        Obtenez l'icône au pluriel ou au singulier selon que l'objet a ou non des enfants.

        Args:
            myIcon: L'icône de base.
            native (bool, optional): Si l'icône provient des paramètres utilisateur. La valeur par défaut est True.

        Returns:
            L'icône plurielle ou singulière.
        """
        hasChildren = any(
            child for child in self.children() if not child.isDeleted()
        )
        mapping = (
            icon.itemImagePlural if hasChildren else icon.itemImageSingular
        )
        # Si l'icône provient des paramètres utilisateur, mettez-la uniquement au pluriel ; c'est probablement
        # la voie du moindre étonnement
        if native or hasChildren:
            return mapping.get(myIcon, myIcon)
        return myIcon

    # Types d'événements :

    @classmethod
    def modificationEventTypes(class_):
        """
        Obtenez les types d'événements pour les événements de modification.

        Returns:
            list: La liste des types d'événements.
        """
        return super().modificationEventTypes() + [
            class_.expansionChangedEventType()
        ]

    # Remplacez les méthodes SynchronizedObject pour marquer également les objets enfants

    @patterns.eventSource
    def markDeleted(self, event=None):
        """
        Marquez l'objet composite et ses enfants comme supprimés.

        Args:
            event: L'événement associé au marquage de l'objet comme supprimé.
        """
        super().markDeleted(event=event)
        for child in self.children():
            child.markDeleted(event=event)

    @patterns.eventSource
    def markNew(self, event=None):
        """
        Marquez l'objet composite et ses enfants comme nouveaux.

        Args:
            event: L'événement associé au marquage de l'objet comme nouveau.
        """
        super().markNew(event=event)
        for child in self.children():
            child.markNew(event=event)

    @patterns.eventSource
    def markDirty(self, force=False, event=None):
        """
        Marquez l'objet composite et ses enfants comme sales (modifiés).

        Args:
            force (bool, optional): Forcer le marquage de l'objet comme sale. La valeur par défaut est False.
            event: L'événement associé au marquage de l'objet comme sale.
        """
        super().markDirty(force, event=event)
        for child in self.children():
            child.markDirty(force, event=event)

    @patterns.eventSource
    def cleanDirty(self, event=None):
        """
        Marque l'objet composite et ses enfants comme non sales (None).

        Args:
            event: L'événement associé au marquage de l'objet comme non sale.
        """
        super().cleanDirty(event=event)
        for child in self.children():
            child.cleanDirty(event=event)
