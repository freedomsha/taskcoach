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

import logging

# from builtins import zip
# from builtins import object
from taskcoachlib import patterns
from taskcoachlib.domain import date
from taskcoachlib.i18n import _
from taskcoachlib.command.clipboard import Clipboard

log = logging.getLogger(__name__)  # Logger pour ce fichier


class BaseCommand(patterns.Command):
    def __init__(
        self, list=None, items=None, *args, **kwargs
    ):  # pylint: disable=W0622
        """
        Initializes the command.

        Args:
            list: The collection the command operates on.
            items: The items to be processed.
        """
        super().__init__(*args, **kwargs)
        self.list = list
        self.items = [item for item in items] if items else []
        self.save_modification_datetimes()

    def save_modification_datetimes(self):
        """
        Saves the current modification date and time for all items.
        """
        self.__oldModificationDatetimes = [
            (item, item.modificationDateTime())
            for item in self.modified_items()
            if item
        ]
        self.__now = date.Now()

    def __str__(self):
        return self.name()

    singular_name = "Do something with %s"  # Override in subclass
    plural_name = "Do something"  # Override in subclass

    def name(self):
        """
        Returns the human-readable name of the command.

        Returns:
            A string containing the command name.
        """
        return (
            self.singular_name % self.name_subject(self.items[0])
            if len(self.items) == 1
            else self.plural_name
        )

    def name_subject(self, item):
        """
        Returns a truncated subject for use in the singular name.

        Args:
            item: The item to get the subject from.

        Returns:
            The truncated subject string.
        """
        subject = item.subject()
        return subject if len(subject) < 60 else subject[:57] + "..."

    def items_are_new(self):
        """
        Indicates whether the items are newly created.

        Returns:
            False by default.
        """
        return False

    def getItems(self):
        """The items this command operates on."""
        return self.items

    def modified_items(self):
        """Return the items that are modified by this command."""
        return self.items

    def canDo(self):
        """
        Checks if the command can be executed.

        Returns:
            True if there are items to operate on.
        """
        return bool(self.items)

    def do(self):
        """Executes the command if possible."""
        if self.canDo():
            super().do()
            self.do_command()

    def undo(self):
        """Undoes the command."""
        super().undo()
        self.undo_command()

    def redo(self):
        """Redoes the command."""
        super().redo()
        self.redo_command()

    def __tryInvokeMethodOnSuper(self, method_name, *args, **kwargs):
        """Attempts to invoke a method on the super class."""
        #  C'est le changement critique.
        #  Dans Task Coach, les commandes héritent souvent de plusieurs classes
        #  (ex: class CutCommand(CutCommandMixin, DeleteCommand)).
        #  Si l'ordre d'héritage change ou si un Mixin manque une méthode,
        #  super().do_command() pouvait faire planter l'application.
        #  Le nouveau code attrape cette erreur et continue,
        #  ce qui est beaucoup plus sûr.
        try:
            method = getattr(super(), method_name)
        except AttributeError as e:
            log.error(
                f"BaseCommand.__tryInvokeMethodOnSuper : AttributeError: {e}",
                exc_info=True,
            )
            return  # no 'method' in any super class
        return method(*args, **kwargs)

    def do_command(self):
        """
        Core logic for executing the command. Updates modification times.
        """
        self.__tryInvokeMethodOnSuper("do_command")
        for item in self.modified_items():
            item.setModificationDateTime(self.__now)

    def undo_command(self):
        """
        Core logic for undoing the command. Restores modification times.
        """
        self.__tryInvokeMethodOnSuper("undo_command")
        for item, old_modification_datetime in self.__oldModificationDatetimes:
            item.setModificationDateTime(old_modification_datetime)

    def redo_command(self):
        """
        Core logic for redoing the command.
        """
        self.__tryInvokeMethodOnSuper("redo_command")
        for item in self.modified_items():
            item.setModificationDateTime(self.__now)


# class SaveStateMixin(object):
class SaveStateMixin:
    """Mixin class for commands that need to keep the states of objects.
    Objects should provide __getstate__ and __setstate__ methods."""

    # pylint: disable=W0201

    def saveStates(self, objects):
        """
        Saves the current state of the given objects.

        Args:
            objects: List of objects to save state for.
        """
        self.objectsToBeSaved = objects
        self.oldStates = self.__getStates()

    @patterns.eventSource
    def undoStates(self, event=None):
        """
        Store current states and restore old states.

        Args:
            event: The event that triggered the undo.
        """
        self.newStates = self.__getStates()
        self.__setStates(self.oldStates, event=event)

    @patterns.eventSource
    def redoStates(self, event=None):
        """
        Restore previously stored new states.

        Args:
            event: The event that triggered the redo.
        """
        self.__setStates(self.newStates, event=event)

    def __getStates(self):
        """Internal method to collect states from objects."""
        return [
            objectToBeSaved.__getstate__()
            for objectToBeSaved in self.objectsToBeSaved
        ]

    @patterns.eventSource
    def __setStates(self, states, event=None):
        """Internal method to restore states to objects."""
        for objectToBeSaved, state in zip(self.objectsToBeSaved, states):
            objectToBeSaved.__setstate__(state, event=event)


# class CompositeMixin(object):
class CompositeMixin:
    """Mixin class for commands that deal with composites."""

    def getAncestors(self, composites):  # Method may be 'static'
        """
        Retrieves all ancestors for a list of composite objects.

        Args:
            composites: List of composite objects.

        Returns:
            A list containing all ancestors.
        """
        ancestors = []
        for composite in composites:
            ancestors.extend(composite.ancestors())
        return ancestors

    def getAllChildren(self, composites):  # Method may be 'static'
        """
        Retrieves all recursive children for a list of composite objects.

        Args:
            composites: List of composite objects.

        Returns:
            A list containing all children.
        """
        all_children = []
        for composite in composites:
            all_children.extend(composite.children(recursive=True))
        return all_children

    def getAllParents(self, composites):  # Method may be 'static'
        """
        Retrieves the direct parents for a list of composite objects.

        Args:
            composites: List of composite objects.

        Returns:
            A list of parent objects.
        """
        return [
            composite.parent()
            for composite in composites
            if composite.parent() is not None
        ]


class NewItemCommand(BaseCommand):
    def name(self):
        # Override to always return the singular name without a subject. The
        # subject would be something like "New task", so not very interesting.
        return self.singular_name

    def items_are_new(self):
        return True

    def modified_items(self):
        return []

    @patterns.eventSource
    def do_command(self, event=None):
        """Executes addition of new items."""
        super().do_command()
        self.list.extend(
            self.items
        )  # Don't use the event to force this change to be notified first
        event.addSource(self, type="newitem", *self.items)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Undoes addition of new items."""
        super().undo_command()
        self.list.removeItems(self.items, event=event)

    @patterns.eventSource
    def redo_command(self, event=None):
        """Redoes addition of new items."""
        super().redo_command()
        self.list.extend(
            self.items
        )  # Don't use the event to force this change to be notified first
        event.addSource(self, type="newitem", *self.items)


class NewSubItemCommand(NewItemCommand):
    def name_subject(self, subitem):
        # Override to use the subject of the parent of the new subitem instead
        # of the subject of the new subitem itself, which wouldn't be very
        # interesting because it's something like 'New subitem'.
        return subitem.parent().subject()

    def modified_items(self):
        return [item.parent() for item in self.items]


class CopyCommand(BaseCommand):
    plural_name = _("Copy")
    singular_name = _('Copy "%s"')

    def do_command(self):
        """Copies items to the clipboard."""
        self.__copies = [
            item.copy() for item in self.items
        ]  # pylint: disable=W0201
        # instance attribute __copies defined outside __init__
        Clipboard().put(self.__copies, self.list)

    def undo_command(self):
        """Clears the clipboard."""
        Clipboard().clear()

    def redo_command(self):
        """Restores copied items to the clipboard."""
        Clipboard().put(self.__copies, self.list)


class DeleteCommand(BaseCommand, SaveStateMixin):
    plural_name = _("Delete")
    singular_name = _('Delete "%s"')

    def __init__(self, *args, **kwargs):
        self.__shadow = kwargs.pop("shadow", False)
        super().__init__(*args, **kwargs)

    def modified_items(self):
        return [item.parent() for item in self.items if item.parent()]

    def do_command(self):
        """Deletes items or marks them as deleted."""
        super().do_command()
        if self.__shadow:
            self.saveStates(self.items)

            for item in self.items:
                item.markDeleted()
        else:
            self.list.removeItems(self.items)

    def undo_command(self):
        """Restores deleted items."""
        super().undo_command()
        if self.__shadow:
            self.undoStates()
        else:
            self.list.extend(self.items)

    def redo_command(self):
        """Deletes items again."""
        super().redo_command()
        if self.__shadow:
            self.redoStates()
        else:
            self.list.removeItems(self.items)


# class CutCommandMixin(object):
class CutCommandMixin:
    """Mixin class for commands that cut items to the clipboard."""

    plural_name = _("Cut")
    singular_name = _('Cut "%s"')

    def __putItemsOnClipboard(self):
        cb = Clipboard()
        self.__previousClipboardContents = cb.get()  # pylint: disable=W0201
        cb.put(
            self.itemsToCut(), self.sourceOfItemsToCut()
        )  # Unresolved attribute car mixin !

    def __removeItemsFromClipboard(self):
        cb = Clipboard()
        cb.put(*self.__previousClipboardContents)

    def do_command(self):
        """Put the items on the clipboard and execute the command."""
        self.__putItemsOnClipboard()
        super().do_command()

    def undo_command(self):
        """Restore the previous clipboard contents and undo the command."""
        self.__removeItemsFromClipboard()
        super().undo_command()

    def redo_command(self):
        """Put the items back on the clipboard and redo the command."""
        self.__putItemsOnClipboard()
        super().redo_command()


class CutCommand(CutCommandMixin, DeleteCommand):
    def itemsToCut(self):
        """Return the items that are to be cut to the clipboard."""
        return self.items

    def sourceOfItemsToCut(self):
        return self.list


class PasteCommand(BaseCommand, SaveStateMixin):
    plural_name = _("Paste")
    singular_name = _('Paste "%s"')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__itemsToPaste, self.__sourceOfItemsToPaste = (
            self.getItemsToPaste()
        )
        self.saveStates(self.getItemsToSave())

    def getItemsToSave(self):
        """Return the items that need to be saved for undo/redo."""
        return self.__itemsToPaste

    def canDo(self):
        """Check if there are items to paste."""
        return bool(self.__itemsToPaste)

    def do_command(self):
        """Perform the paste operation by adding items to the source list."""
        self.setParentOfPastedItems()
        self.__sourceOfItemsToPaste.extend(self.__itemsToPaste)

    def undo_command(self):
        """Undo the paste by removing items and restoring saved states."""
        self.__sourceOfItemsToPaste.removeItems(self.__itemsToPaste)
        self.undoStates()

    def redo_command(self):
        """Redo the paste by restoring states and re-adding items."""
        self.redoStates()
        self.__sourceOfItemsToPaste.extend(self.__itemsToPaste)

    def setParentOfPastedItems(self, newParent=None):
        """Sets the parent for all items currently being pasted.

        Args:
            newParent: The domain object to set as the parent.
        """
        for item in self.__itemsToPaste:
            item.setParent(newParent)

    @staticmethod
    def getItemsToPaste():
        """Retrieves items from the clipboard and creates copies for pasting.

        Returns:
            A tuple containing a list of copied items and the source collection.
        """
        items, source = Clipboard().get()
        return [item.copy() for item in items], source


class PasteAsSubItemCommand(PasteCommand, CompositeMixin):
    plural_name = _("Paste as subitem")
    singular_name = _('Paste as subitem of "%s"')

    def setParentOfPastedItems(self):  # pylint: disable=W0221
        newParent = self.items[0]
        super().setParentOfPastedItems(newParent)

    def getItemsToSave(self):
        return self.getAncestors([self.items[0]]) + super().getItemsToSave()


class DragAndDropCommand(BaseCommand, SaveStateMixin, CompositeMixin):
    plural_name = _("Drag and drop")
    singular_name = _('Drag and drop "%s"')

    def __init__(self, *args, **kwargs):
        dropTargets = kwargs.pop("drop")
        self._itemToDropOn = dropTargets[0] if dropTargets else None
        super().__init__(*args, **kwargs)
        self.saveStates(self.getItemsToSave())

    def getItemsToSave(self):
        """
        Returns items whose state needs to be saved.

        Returns:
            A list of items to save.
        """
        toSave = self.items[:]
        if self._itemToDropOn is not None:
            toSave.insert(0, self._itemToDropOn)
        return toSave

    def modified_items(self):
        return (
            [item.parent() for item in self.items if item.parent()]
            + [self._itemToDropOn]
            if self._itemToDropOn
            else []
        )

    def canDo(self):
        """
        Checks if the drop is valid.

        Returns:
            True if the drop is not on a child or parent.
        """
        return self._itemToDropOn not in (
            self.items
            + self.getAllChildren(self.items)
            + self.getAllParents(self.items)
        )

    def do_command(self):
        """Executes the drag and drop move."""
        super().do_command()
        self.list.removeItems(self.items)
        for item in self.items:
            item.setParent(self._itemToDropOn)
        self.list.extend(self.items)

    def undo_command(self):
        """Undoes the drag and drop move."""
        super().undo_command()
        self.list.removeItems(self.items)
        self.undoStates()
        self.list.extend(self.items)

    def redo_command(self):
        """Redoes the drag and drop move."""
        super().redo_command()
        self.list.removeItems(self.items)
        self.redoStates()
        self.list.extend(self.items)


class OrderingDragAndDropCommand(DragAndDropCommand):
    def __init__(self, *args, **kwargs):
        self.column = kwargs.pop("column", None)
        self.isTreeMode = kwargs.pop("isTree", True)
        self.part = kwargs.pop("part", 0)
        super().__init__(*args, **kwargs)

    def isOrdering(self):
        """
        Checks if this is an ordering operation.

        Returns:
            True if the target column is 'ordering'.
        """
        return self.column is not None and self.column.name() == "ordering"

    def getSiblings(self):
        """
        Returns siblings of the drop target.

        Returns:
            A list of sibling items.
        """
        siblings = []
        for item in self.list:
            if (
                item.parent() == self._itemToDropOn.parent()
                and item not in self.items
            ):
                siblings.append(item)
        return siblings

    def getOrderingSiblings(self):
        """
        Returns siblings relevant for ordering.

        Returns:
            A list of siblings.
        """
        if self.isTreeMode:
            return self.getSiblings()
        # Everything, almost
        return [item for item in self.list if item not in self.items]

    def getItemsToSave(self):
        items = super().getItemsToSave()
        if self.isOrdering():
            items.extend(self.getOrderingSiblings())
        return items

    def canDo(self):
        if self.isOrdering():
            return True  # Already checked when drag and droppin
        return super().canDo()

    def do_command(self):
        if self.isOrdering():
            siblings = self.getOrderingSiblings()

            orderings = [item.ordering() for item in self.items]
            minOrdering = min(orderings)
            maxOrdering = max(orderings)

            insertIndex = (
                siblings.index(self._itemToDropOn) + (self.part + 1) // 2
            )

            # Simple special cases
            if insertIndex == 0:
                minOrderingOfSiblings = min(
                    [item.ordering() for item in siblings]
                )
                for item in self.items:
                    item.setOrdering(
                        item.ordering()
                        - maxOrdering
                        + minOrderingOfSiblings
                        - 1
                    )
            elif insertIndex == len(siblings):
                maxOrderingOfSiblings = max(
                    [item.ordering() for item in siblings]
                )
                for item in self.items:
                    item.setOrdering(
                        item.ordering()
                        - minOrdering
                        + maxOrderingOfSiblings
                        + 1
                    )
            else:
                maxOrderingOfPreviousSiblings = max(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx < insertIndex
                    ]
                )
                minOrderingOfPreviousSiblings = min(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx < insertIndex
                    ]
                )
                maxOrderingOfNextSiblings = max(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx >= insertIndex
                    ]
                )
                minOrderingOfNextSiblings = min(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx >= insertIndex
                    ]
                )
                if insertIndex < len(siblings) // 2:
                    for item in self.items:
                        item.setOrdering(
                            item.ordering()
                            - maxOrdering
                            - 1
                            + minOrderingOfNextSiblings
                        )
                    for item in siblings[:insertIndex]:
                        item.setOrdering(
                            item.ordering()
                            - maxOrderingOfPreviousSiblings
                            - 1
                            + minOrdering
                            - maxOrdering
                            - 1
                            + minOrderingOfNextSiblings
                        )
                else:
                    for item in self.items:
                        item.setOrdering(
                            item.ordering()
                            - minOrdering
                            + 1
                            + maxOrderingOfPreviousSiblings
                        )
                    for item in siblings[insertIndex:]:
                        item.setOrdering(
                            item.ordering()
                            - minOrderingOfNextSiblings
                            + 1
                            + maxOrdering
                            - minOrdering
                            + 1
                            + maxOrderingOfPreviousSiblings
                        )
        else:
            super().do_command()


class EditSubjectCommand(BaseCommand):
    plural_name = _("Edit subjects")
    singular_name = _('Edit subject "%s"')

    def __init__(self, *args, **kwargs):
        self.__newSubject = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__old_subjects = [(item, item.subject()) for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        """
        Updates the subjects of the items.

        Args:
            event: The event source.
        """
        super().do_command()
        for item in self.items:
            item.setSubject(self.__newSubject, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """
        Restores the old subjects.

        Args:
            event: The event source.
        """
        super().undo_command()
        for item, old_subject in self.__old_subjects:
            item.setSubject(old_subject, event=event)

    def redo_command(self):
        self.do_command()


class EditDescriptionCommand(BaseCommand):
    plural_name = _("Edit descriptions")
    singular_name = _('Edit description "%s"')

    def __init__(self, *args, **kwargs):
        self.__new_description = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__old_descriptions = [item.description() for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        """
        Updates descriptions.

        Args:
            event: Event source.
        """
        super().do_command()
        for item in self.items:
            item.setDescription(self.__new_description, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """
        Restores descriptions.

        Args:
            event: Event source.
        """
        super().undo_command()
        for item, old_description in zip(self.items, self.__old_descriptions):
            item.setDescription(old_description, event=event)

    def redo_command(self):
        """Redoes the description change."""
        self.do_command()


class EditIconCommand(BaseCommand):
    plural_name = _("Change icons")
    singular_name = _('Change icon "%s"')

    def __init__(self, *args, **kwargs):
        self.__newIcon = icon = kwargs.pop("newValue")
        self.__newSelectedIcon = (
            icon[: -len("_icon")] + "_open_icon"
            if (icon.startswith("folder") and icon.count("_") == 2)
            else icon
        )
        super().__init__(*args, **kwargs)
        self.__oldIcons = [
            (item.icon(), item.selectedIcon()) for item in self.items
        ]

    @patterns.eventSource
    def do_command(self, event=None):
        """
        Sets the new icon for all items.

        Args:
            event: Event source.
        """
        super().do_command()
        for item in self.items:
            item.setIcon(self.__newIcon, event=event)
            item.setSelectedIcon(self.__newSelectedIcon, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """
        Restores the old icons.

        Args:
            event: Event source.
        """
        super().undo_command()
        for item, (oldIcon, oldSelectedIcon) in zip(
            self.items, self.__oldIcons
        ):
            item.setIcon(oldIcon, event=event)
            item.setSelectedIcon(oldSelectedIcon, event=event)

    def redo_command(self):
        """Redoes the icon change."""
        self.do_command()


class EditFontCommand(BaseCommand):
    plural_name = _("Change fonts")
    singular_name = _('Change font "%s"')

    def __init__(self, *args, **kwargs):
        self.__newFont = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__oldFonts = [item.font() for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        """
        Sets the new font.

        Args:
            event: Event source.
        """
        super().do_command()
        for item in self.items:
            item.setFont(self.__newFont, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """
        Restores old font.

        Args:
            event: Event source.
        """
        super().undo_command()
        for item, oldFont in zip(self.items, self.__oldFonts):
            item.setFont(oldFont, event=event)

    def redo_command(self):
        """Redoes font change."""
        self.do_command()


class EditColorCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        self.__newColor = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__oldColors = [self.getItemColor(item) for item in self.items]

    @staticmethod
    def getItemColor(item):
        """
        Retrieves the color for an item.

        Args:
            item: The item.

        Returns:
            The color value.
        """
        raise NotImplementedError

    @staticmethod
    def setItemColor(item, color, event):
        """
        Sets the color for an item.

        Args:
            item: The item.
            color: The new color.
            event: Event source.
        """
        raise NotImplementedError

    @patterns.eventSource
    def do_command(self, event=None):
        """
        Executes color change.

        Args:
            event: Event source.
        """
        super().do_command()
        for item in self.items:
            self.setItemColor(item, self.__newColor, event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """
        Undoes color change.

        Args:
            event: Event source.
        """
        super().undo_command()
        for item, oldColor in zip(self.items, self.__oldColors):
            self.setItemColor(item, oldColor, event)

    def redo_command(self):
        """Redoes color change."""
        self.do_command()


class EditForegroundColorCommand(EditColorCommand):
    plural_name = _("Change foreground colors")
    singular_name = _('Change foreground color "%s"')

    @staticmethod
    def getItemColor(item):
        return item.foregroundColor()

    @staticmethod
    def setItemColor(item, color, event):
        item.setForegroundColor(color, event=event)


class EditBackgroundColorCommand(EditColorCommand):
    plural_name = _("Change background colors")
    singular_name = _('Change background color "%s"')

    @staticmethod
    def getItemColor(item):
        return item.backgroundColor()

    @staticmethod
    def setItemColor(item, color, event):
        item.setBackgroundColor(color, event=event)
