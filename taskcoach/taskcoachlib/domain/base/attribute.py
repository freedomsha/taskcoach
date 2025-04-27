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

This Python code defines two classes, `Attribute` and `SetAttribute`, which provide a way to manage single and multiple
attributes with event handling. The classes use weak references for their owner objects to avoid memory leaks. The `Attribute`
class handles setting and getting a single value with an associated event handler. The `SetAttribute` class manages a set of
values, allowing elements to be added or removed with events triggered accordingly. Both classes utilize the
`patterns.eventSource` decorator to facilitate event handling.

Ce code Python définit deux classes, `attribut` et` setAttribute`, qui fournissent
un moyen de gérer les attributs simples et multiples avec la gestion des événements.
Les classes utilisent des références faibles pour leurs objets
propriétaires pour éviter les fuites de mémoire.
La classe `attribut` gère le réglage et l'obtention d'une valeur unique
avec un gestionnaire d'événements associé. La classe `SetAttribute` gère un ensemble de valeurs, permettant d'ajouter
ou de supprimer des éléments avec des événements déclenchés en conséquence. Les deux classes utilisent le décorateur
`patterns.eventSource' pour faciliter la manipulation des événements.

"""

# from builtins import object
from taskcoachlib import patterns
import weakref
# from taskcoachlib.thirdparty._weakrefset import WeakSet
from weakref import WeakSet  # En test!


class Attribute(object):
    """
    A class to manage a single attribute with event handling.

    The `Attribute` class handles setting and getting a single value with an associated event handler.
    It uses weak references for its owner object to avoid memory leaks.

    Une classe pour gérer un seul attribut avec la gestion des événements.

    Le réglage et l'obtention de la classe `Attribut` appelle une seule valeur avec un gestionnaire d'événements associé.
    Il utilise des références faibles pour son objet propriétaire pour éviter les fuites de mémoire.
    """
    __slots__ = ("__value", "__owner", "__setEvent")

    def __init__(self, value, owner, setEvent):
        """
        Initialise une nouvelle instance de la classe `Attribut`.

        Args :
            value : La valeur initiale de l'attribut.
            owner : L'objet propriétaire de l'attribut. Une référence faible à cet objet est stockée.
            setEvent : La fonction de gestionnaire d'événements à appeler lorsque l'attribut est défini.
        """
        super().__init__()
        self.__value = value
        self.__owner = weakref.ref(owner)
        # self.__setEvent = setEvent.__func__
        # En Python, quand on passe method.__func__, on enlève la partie liée (self).
        # Donc au lieu d’appeler :
        #
        # owner._Object__setDescriptionEvent(event)
        #
        # Tu appelles :
        #
        # Object._Object__setDescriptionEvent(event)  # <- manque le self ici !
        #
        # Cela peut :
        #     soit planter silencieusement,
        #     soit ne rien faire du tout (ex. pas d'appel à event.addSource).
        self.__setEvent = setEvent

    def get(self):
        """
        Obtient la valeur actuelle de l'attribut.

        Returns :
            La valeur actuelle de l'attribut.
        """
        return self.__value

    @patterns.eventSource
    def set(self, value, event=None):
        """
        Définit la valeur de l'attribut et déclenche l'événement associé.

        Args :
            value : La nouvelle valeur à définir pour l'attribut.
            event : Données d'événement facultatives à transmettre au gestionnaire d'événements.

        Returns :
            Vrai si la valeur a été définie avec succès et que l'événement a été déclenché, faux autrement.
        """
        owner = self.__owner()
        if owner is not None:
            if value == self.__value:
                return False
            self.__value = value
            # self.__setEvent(owner, event)  # ❌ trop d'arguments
            self.__setEvent(event)  # ✅ juste l'event, self est déjà lié via owner
            return True


class SetAttribute(object):
    """
    Une classe pour gérer un ensemble d'attributs avec la gestion des événements.

    La classe «SetAttribute» gère un ensemble de valeurs, permettant à des
    éléments d'être ajoutés ou supprimés avec des événements déclenchés en conséquence.
    Il utilise des références faibles pour son objet propriétaire pour éviter les fuites de mémoire.
    """
    __slots__ = (
        "__set",
        "__owner",
        "__addEvent",
        "__removeEvent",
        "__changeEvent",
        "__setClass"
    )

    def __init__(
        self,
        values,
        owner,
        addEvent=None,
        removeEvent=None,
        changeEvent=None,
        weak=False
    ):
        """
        Initialise une nouvelle instance de la classe «setAttribute».

        Args :
            values : L'ensemble de valeurs de départ pour l'attribut.
            owner : L'objet propriétaire de l'attribut. Une référence faible à cet objet est stockée.
            addEvent : Fonction de gestionnaire d'événements en option à appeler lorsque des éléments sont ajoutés à l'ensemble.
            removeEvent : Fonction de gestionnaire d'événements en option à appeler lorsque les éléments sont supprimés de l'ensemble.
            changeEvent : Fonction de gestionnaire d'événements facultatif à appeler lorsque l'ensemble change.
            weak : Si vrai, utilisez un WeakSet(réglage faible) pour stocker les valeurs. Par défaut est faux.
        """
        self.__setClass = WeakSet if weak else set
        self.__set = self.__setClass(values) if values else self.__setClass()
        self.__owner = weakref.ref(owner)
        self.__addEvent = (addEvent or self.__nullEvent).__func__
        self.__removeEvent = (removeEvent or self.__nullEvent).__func__
        self.__changeEvent = (changeEvent or self.__nullEvent).__func__
        
    def get(self):
        """
        Obtenir une copie de l'ensemble actuel de valeurs.

        Returns :
            Un nouvel ensemble contenant les valeurs actuelles de l'attribut.
        """
        return set(self.__set)
    
    @patterns.eventSource
    def set(self, values, event=None):
        """
        Définit les valeurs de l'attribut et déclenche les événements associés.

        Args :
            values : Le nouvel ensemble de valeurs à définir pour l'attribut.
            event : Données d'événement facultatives à transmettre aux gestionnaires d'événements.

        Returns :
            Vrai si les valeurs ont été définies avec succès et que les événements ont été déclenchés, faux sinon.
        """
        owner = self.__owner()
        if owner is not None:
            if values == set(self.__set):
                return False
            added = values - set(self.__set)
            removed = set(self.__set) - values
            self.__set = self.__setClass(values)
            if added:
                self.__addEvent(owner, event, *added)  # pylint: disable=W0142
            if removed:
                self.__removeEvent(owner, event, *removed)  # pylint: disable=W0142
            if added or removed:
                self.__changeEvent(owner, event, *set(self.__set))
            return True
    
    @patterns.eventSource
    def add(self, values, event=None):
        """
        Ajoute des valeurs à l'attribut et déclenche les événements associés.

        Args :
            values : Les valeurs à ajouter à l'attribut.
            event : Données d'événement facultatives à transmettre aux gestionnaires d'événements.

        Returns :
            Vrai si les valeurs ont été ajoutées avec succès et que les événements ont été déclenchés, faux sinon.
        """
        owner = self.__owner()
        if owner is not None:
            if values <= set(self.__set):
                return False
            self.__set = self.__setClass(set(self.__set) | values)
            self.__addEvent(owner, event, *values)  # pylint: disable=W0142
            self.__changeEvent(owner, event, *set(self.__set))
            return True

    @patterns.eventSource
    def remove(self, values, event=None):
        """
        Removes values from the attribute and triggers the associated events.
        Supprime les valeurs de l'attribut et déclenche les événements associés.

        Args :
            values : Les valeurs à supprimer de l'attribut.
            event : Données d'événement facultatives à transmettre aux gestionnaires d'événements.

        Returns :
            Vrai si les valeurs ont été supprimées avec succès et que les événements ont été déclenchés, faux autrement.
        """
        owner = self.__owner()
        if owner is not None:
            if values & set(self.__set) == set():
                return False
            self.__set = self.__setClass(set(self.__set) - values)
            self.__removeEvent(owner, event, *values)  # pylint: disable=W0142
            self.__changeEvent(owner, event, *set(self.__set))
            return True

    def __nullEvent(self, *args, **kwargs):
        pass
