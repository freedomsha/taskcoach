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

from . import observer
import weakref


class Composite(object):
    """
    Une classe représentant un objet composite dans le modèle composite.

    Attributs :
        __parent (weakref) : faible référence au composite parent.
        __children (list) : Liste des composites enfants.
    """

    def __init__(self, children=None, parent=None):
        """
        Initialisez le composite avec une liste facultative d'enfants et de parents.

        Args:
            children (list, facultatif) : Liste des composites enfants.
            parent (Composite, facultatif) : Composite parent.
        """
        super().__init__()
        self.__parent = parent if parent is None else weakref.ref(parent)
        self.__children = children or []
        for child in self.__children:
            child.setParent(self)

    def __getstate__(self):
        """
        Obtenez l'état du décapage.

        Renvoie :
            dict : L'état du composite.
        """
        return dict(children=self.__children[:], parent=self.parent())

    def __setstate__(self, state):
        """
        Définissez l'état à partir du décapage.

        Args:
            state (dict) : L'état du composite.
        """
        self.__parent = (
            None if state["parent"] is None else weakref.ref(state["parent"])
        )
        self.__children = state["children"]

    def __getcopystate__(self):
        """
        Obtenez l'état pour la copie.

        Renvoie :
            dict : L'état du composite pour la copie.
        """
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        state.update(
            dict(
                children=[child.copy() for child in self.__children],
                parent=self.parent(),
            )
        )
        return state

    def parent(self):
        """
        Obtenez le composite parent.

        Renvoie :
            Composite : Le composite parent.
        """
        return None if self.__parent is None else self.__parent()

    def ancestors(self):
        """
        Récupère la liste des ancêtres du composite.

        Renvoie :
            list : La liste des ancêtres.
        """
        parent = self.parent()
        return parent.ancestors() + [parent] if parent else []

    def family(self):
        """
        Obtenez la famille du composite (ancêtres, soi et enfants).

        Renvoie :
            liste : La famille du composite.
        """
        return self.ancestors() + [self] + self.children(recursive=True)

    def setParent(self, parent):
        """
        Définissez le composite parent.

        Args:
            parent (Composite) : Le composite parent.
        """
        self.__parent = None if parent is None else weakref.ref(parent)

    def children(self, recursive=False):
        """
        Récupère les enfants du composite.

        Args:
            récursif (bool, facultatif) : Si True, récupère tous les descendants de manière récursive.

        Renvoie :
            list : La liste des enfants .
        """
        if recursive:
            result = self.__children[:]
            for child in self.__children:
                result.extend(child.children(recursive=True))
            return result
        else:
            return self.__children

    def siblings(self, recursive=False):
        """
        Obtenez les frères et sœurs du composite.

        Args :
            recursive (bool, facultatif) : Si True, obtenez tous les descendants des frères et sœurs de manière récursive.

        Returns :
            list : La liste de frères et sœurs.
        """
        parent = self.parent()
        if parent:
            result = [child for child in parent.children() if child != self]
            if recursive:
                for child in result[:]:
                    result.extend(child.children(recursive=True))
            return result
        else:
            return []

    def copy(self, *args, **kwargs):
        """
        Créez une copie du composite.

        Returns :
            Composite : Le composite copié.
        """
        kwargs["parent"] = self.parent()
        kwargs["children"] = [child.copy() for child in self.children()]
        return self.__class__(*args, **kwargs)

    def newChild(self, *args, **kwargs):
        """
        Créez un nouveau composite enfant.

        Returns :
            Composite : le nouveau composite enfant.
        """
        kwargs["parent"] = self
        return self.__class__(*args, **kwargs)

    def addChild(self, child):
        """
        Ajoutez un composite enfant.

        Args :
            child (Composite) : Le composite enfant à ajouter.
        """
        self.__children.append(child)
        child.setParent(self)

    def removeChild(self, child):
        """
        Supprimer un composite enfant.

        Args :
            child (Composite) : Le composite enfant à supprimer.
        """
        self.__children.remove(child)
        # We don't reset the parent of the child, because that makes restoring
        # the parent-child relationship easier.


class ObservableComposite(Composite):
    """
    Une classe représentant un objet composite observable dans le modèle composite.
    Hérite de Composite et ajoute une fonctionnalité de modèle d'observateur.
    """

    @observer.eventSource
    def __setstate__(self, state, event=None):  # pylint: disable=W0221
        """
        Définissez l'état du décapage avec la notification d'événement.

        Args:
            state (dict) : L'état du composite.
            event (Événement, facultatif) : L'événement à notifier.
        """
        oldChildren = set(self.children())
        super().__setstate__(state)
        newChildren = set(self.children())
        childrenRemoved = oldChildren - newChildren
        # pylint: disable=W0142
        if childrenRemoved:
            self.removeChildEvent(event, *childrenRemoved)
        childrenAdded = newChildren - oldChildren
        if childrenAdded:
            self.addChildEvent(event, *childrenAdded)

    @observer.eventSource
    def addChild(self, child, event=None):  # pylint: disable=W0221
        """
        Ajoutez un composite enfant avec notification d'événement.

        Args :
            child (Composite) : Le composite enfant à ajouter.
            event (Event, facultatif) : L'événement à notifier.
        """
        super().addChild(child)
        self.addChildEvent(event, child)

    def addChildEvent(self, event, *children):
        """
        Avertir les observateurs de l'ajout d'enfants.

        Args:
            event (Event) : L'événement à notifier.
            children (Composite) : Les enfants ajoutés.
        """
        event.addSource(self, *children, **dict(type=self.addChildEventType()))

    @classmethod
    def addChildEventType(class_):
        """
        Obtenez le type d'événement pour l'ajout d'enfants.

        Renvoie :
            str : Le type d'événement.
        """
        return "composite(%s).child.add" % class_

    @observer.eventSource
    def removeChild(self, child, event=None):  # pylint: disable=W0221
        """
        Supprimer un composite enfant avec notification d'événement.

        Args :
            child (Composite) : Le composite enfant à supprimer.
            event (Event, facultatif) : L'événement à notifier.
        """
        super().removeChild(child)
        self.removeChildEvent(event, child)

    def removeChildEvent(self, event, *children):
        """
        Avertir les observateurs du retrait des enfants.

        Args:
            event (Event) : L'événement à notifier.
            children (Composite) : Les enfants supprimés.
        """
        event.addSource(
            self, *children, **dict(type=self.removeChildEventType())
        )

    @classmethod
    def removeChildEventType(class_):
        """
        Obtenez le type d'événement pour supprimer les enfants.

        Renvoie :
            str : Le type d'événement.
        """
        return "composite(%s).child.remove" % class_

    @classmethod
    def modificationEventTypes(class_):
        """
        Obtenez la liste des types d'événements de modification.

        Renvoie :
            list : La liste des types d'événements de modification.
        """
        try:
            eventTypes = super().modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [
            class_.addChildEventType(),
            class_.removeChildEventType(),
        ]


class CompositeCollection(object):
    """
    Une collection d'objets composites.

    Méthodes :
        append (composite) : ajoutez un composite à la collection.
        extend (composites) : ajoutez plusieurs composites à la collection.
        remove (composite) : Supprimez un composite de la collection.
        removeItems (composites) : Supprimez plusieurs composites de la collection.
        rootItems () : Obtenez les éléments racine de la collection.
        allItemsSorted () : Obtenez tous les éléments triés par hiérarchie.
    """

    def __init__(self, initList=None, *args, **kwargs):
        """
        Initialisez la collection avec une liste facultative de composites initiaux.

        Args :
            initList (liste, facultatif) : liste initiale de composites.
        """
        super().__init__(*args, **kwargs)
        self.extend(initList or [])

    def append(self, composite, event=None):
        """
        Ajoutez un composite à la collection.

        Args :
            composite (Composite) : Le composite à ajouter.
            event (Event, facultatif) : L'événement à notifier.
        """
        return self.extend([composite], event=event)

    @observer.eventSource
    def extend(self, composites, event=None):
        """
        Ajoutez plusieurs composites à la collection avec notification d'événement.

        Args:
            composites (list) : La liste des composites à ajouter.
            event (Événement, facultatif) : L'événement à notifier.
        """
        if not composites:
            return
        compositesAndAllChildren = self._compositesAndAllChildren(composites)
        super().extend(compositesAndAllChildren, event=event)
        self._addCompositesToParent(composites, event)

    def _compositesAndAllChildren(self, composites):
        """
        Obtenez tous les composites et leurs enfants de manière récursive.

        Args:
            composites (list) : La liste des composites.

        Returns:
            list : La liste des composites et de leurs enfants.
        """
        compositesAndAllChildren = set(composites)
        for composite in composites:
            compositesAndAllChildren |= set(composite.children(recursive=True))
        return list(compositesAndAllChildren)

    def _addCompositesToParent(self, composites, event):
        """
        Ajoutez des composites à leur parent.

        Args:
            composites (list) : La liste des composites.
            event (Event) : L'événement à notifier.
        """
        for composite in composites:
            parent = composite.parent()
            if (
                parent
                and parent in self
                and composite not in parent.children()
            ):
                parent.addChild(composite, event=event)

    def remove(self, composite, event=None):
        """
        Supprimer un composite de la collection.

        Args:
            composite (Composite) : Le composite à supprimer.
            event (Event, facultatif) : L'événement à notifier.
        """
        return (
            self.removeItems([composite], event=event)
            if composite in self
            else event
        )

    @observer.eventSource
    def removeItems(self, composites, event=None):
        """
        Supprimez plusieurs éléments composites de la collection avec notification d'événement.

        Args:
            composites (list) : La liste des composites à supprimer.
            event (Événement, facultatif) : L'événement à notifier.
        """
        if not composites:
            return
        compositesAndAllChildren = self._compositesAndAllChildren(composites)
        super().removeItems(compositesAndAllChildren, event=event)
        self._removeCompositesFromParent(composites, event)

    def _removeCompositesFromParent(self, composites, event):
        """
        Supprimer les composites de leur parent.

        Args:
            composites (list) : La liste des composites.
            event (Event) : L'événement à notifier.
        """
        for composite in composites:
            parent = composite.parent()
            if parent:
                parent.removeChild(composite, event=event)

    def rootItems(self):
        """
        Récupère les éléments racine de la collection.

        Renvoie :
            list : La liste des éléments racine.
        """
        return [
            composite
            for composite in self
            if composite.parent() is None or composite.parent() not in self
        ]

    def allItemsSorted(self):
        """
        Obtenez tous les éléments triés par hiérarchie.

        Renvoie :
            liste : La liste de tous les éléments triés par hiérarchie.
        """
        result = []
        for item in self.rootItems():
            result.append(item)
            result.extend(item.children(recursive=True))
        return result


class CompositeSet(CompositeCollection, observer.ObservableSet):
    """Un ensemble d'objets composites observables."""
    pass


class CompositeList(CompositeCollection, observer.ObservableList):
    """Une liste d'objets composites observables."""
    pass
