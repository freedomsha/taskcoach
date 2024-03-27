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

from builtins import zip
from taskcoachlib import patterns
from taskcoachlib.i18n import _
from taskcoachlib.domain import category
from . import base


class NewCategoryCommand(base.NewItemCommand):
    singularName = _('New category')

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New category'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        super(NewCategoryCommand, self).__init__(*args, **kwargs)
        self.items = self.createNewCategories(subject=subject,
                                              description=description, attachments=attachments)

    def createNewCategories(self, **kwargs):  # Method may be 'static'
        return [category.Category(**kwargs)]


class NewSubCategoryCommand(base.NewSubItemCommand):
    pluralName = _('New subcategories')
    singularName = _('New subcategory of "%s"')

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New subcategory'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        super(NewSubCategoryCommand, self).__init__(*args, **kwargs)
        self.items = self.createNewCategories(subject=subject,
                                              description=description, attachments=attachments)
        self.saveModificationDatetimes()

    def createNewCategories(self, **kwargs):
        return [parent.newChild(**kwargs) for parent in self.items]


class EditExclusiveSubcategoriesCommand(base.BaseCommand):
    pluralName = _('Edit exclusive subcategories')
    singularName = _('Edit exclusive subcategories of "%s"')

    def __init__(self, *args, **kwargs):
        self.__newExclusivity = kwargs.pop('newValue')
        super(EditExclusiveSubcategoriesCommand, self).__init__(*args, **kwargs)
        self.__oldExclusivities = [item.hasExclusiveSubcategories() for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        super(EditExclusiveSubcategoriesCommand, self).do_command()
        for item in self.items:
            item.makeSubcategoriesExclusive(self.__newExclusivity, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        super(EditExclusiveSubcategoriesCommand, self).undo_command()
        for item, oldExclusivity in zip(self.items, self.__oldExclusivities):
            item.makeSubcategoriesExclusive(oldExclusivity, event=event)

    def redo_command(self):
        self.do_command()


class DeleteCategoryCommand(base.DeleteCommand):
    pluralName = _('Delete categories')
    singularName = _('Delete category "%s"')


class DragAndDropCategoryCommand(base.OrderingDragAndDropCommand):
    pluralName = _('Drag and drop categories')
