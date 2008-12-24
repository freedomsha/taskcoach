'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2008 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2008 Jerome Laheurte <fraca7@free.fr>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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
'''

import wx
from taskcoachlib import patterns, command, widgets
from taskcoachlib.domain import category 
from taskcoachlib.i18n import _
from taskcoachlib.gui import uicommand, menu, dialog
import base, mixin


class BaseCategoryViewer(mixin.AttachmentDropTarget, 
                         mixin.SortableViewerForCategories, 
                         mixin.SearchableViewer, base.TreeViewer):
    SorterClass = category.CategorySorter
    defaultTitle = _('Categories')
    defaultBitmap = 'category'
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'categoryviewer')
        super(BaseCategoryViewer, self).__init__(*args, **kwargs)
        for eventType in category.Category.subjectChangedEventType(), \
                         category.Category.filterChangedEventType(), \
                         category.Category.colorChangedEventType():
            patterns.Publisher().registerObserver(self.onCategoryChanged, 
                eventType)
            
    def domainObjectsToView(self):
        return self.taskFile.categories()
    
    def createWidget(self):
        widget = widgets.CheckTreeCtrl(self, self.getItemText, 
            self.getItemTooltipData, self.getItemImage, self.getItemAttr, 
            self.getChildrenCount, self.getItemExpanded,
            self.getIsItemChecked, self.onSelect, self.onCheck,
            uicommand.CategoryEdit(viewer=self, categories=self.presentation()),
            uicommand.CategoryDragAndDrop(viewer=self, categories=self.presentation()),
            self.createCategoryPopupMenu(), 
            **self.widgetCreationKeywordArguments())
        return widget

    def createToolBarUICommands(self):
        commands = super(BaseCategoryViewer, self).createToolBarUICommands()
        commands[-2:-2] = [None,
                           uicommand.CategoryNew(categories=self.presentation(),
                                                 settings=self.settings),
                           uicommand.CategoryNewSubCategory(categories=self.presentation(),
                                                            viewer=self),
                           uicommand.CategoryEdit(categories=self.presentation(),
                                                  viewer=self),
                           uicommand.CategoryDelete(categories=self.presentation(),
                                                    viewer=self)]
        return commands

    def createCategoryPopupMenu(self, localOnly=False):
        return menu.CategoryPopupMenu(self.parent, self.settings, self.taskFile,
                                      self, localOnly)
    
    def onCategoryChanged(self, event):
        category = event.source()
        if category in self.presentation():
            self.widget.RefreshItem(self.getIndexOfItem(category))

    def onCheck(self, event):
        category = self.getItemWithIndex(self.widget.GetIndexOfItem(event.GetItem()))
        category.setFiltered(event.GetItem().IsChecked())
        self.onSelect(event) # Notify status bar
            
    def getItemText(self, index):    # FIXME: pull up to TreeViewer
        item = self.getItemWithIndex(index)
        return item.subject()

    def getItemTooltipData(self, index):
        if self.settings.getboolean('view', 'descriptionpopups'):
            item = self.getItemWithIndex(index)
            if item.description():
                result = [(None, map(lambda x: x.rstrip('\r'),
                                     item.description().split('\n')))]
            else:
                result = []
            result.append(('note', [note.subject() for note in item.notes()]))
            result.append(('attachment', [unicode(attachment) for attachment in item.attachments()]))
            return result
        else:
            return []

    def getItemImage(self, index, which):
        return -1
    
    def getBackgroundColor(self, item):
        return item.color()
    
    def getItemAttr(self, index):
        item = self.getItemWithIndex(index)
        return wx.ListItemAttr(colBack=self.getBackgroundColor(item))
    
    def getIsItemChecked(self, index):
        item = self.getItemWithIndex(index)
        if isinstance(item, category.Category):
            return item.isFiltered()
        return False

    def isShowingCategories(self):
        return True

    def statusMessages(self):
        status1 = _('Categories: %d selected, %d total')%\
            (len(self.curselection()), len(self.presentation()))
        status2 = _('Status: %d filtered')%len([category for category in self.presentation() if category.isFiltered()])
        return status1, status2

    def newItemDialog(self, *args, **kwargs):
        newCommand = command.NewCategoryCommand(self.presentation(), *args, **kwargs)
        newCommand.do()
        return self.editItemDialog(bitmap=kwargs['bitmap'], items=newCommand.items)
    
    def editItemDialog(self, *args, **kwargs):
        return dialog.editor.CategoryEditor(wx.GetTopLevelParent(self),
            command.EditCategoryCommand(self.presentation(), kwargs['items']),
            self.settings, self.taskFile, bitmap=kwargs['bitmap'],
            columnName=kwargs.get('columnName', ''))
    
    def deleteItemCommand(self):
        return command.DeleteCommand(self.presentation(), self.curselection())
    
    def newSubItemDialog(self, *args, **kwargs):
        return dialog.editor.CategoryEditor(wx.GetTopLevelParent(self),
            command.NewSubCategoryCommand(self.presentation(), self.curselection()),
            self.settings, self.taskFile, bitmap=kwargs['bitmap'])
        
    newSubCategoryDialog = newSubItemDialog


class CategoryViewer(BaseCategoryViewer):
    def __init__(self, *args, **kwargs):
        super(CategoryViewer, self).__init__(*args, **kwargs)
        self.filterUICommand.setChoice(self.settings.getboolean('view',
            'categoryfiltermatchall'))

    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        toolBarUICommands = super(CategoryViewer, self).getToolBarUICommands()
        toolBarUICommands.insert(-2, None) # Separator
        self.filterUICommand = \
            uicommand.CategoryViewerFilterChoice(settings=self.settings)
        toolBarUICommands.insert(-2, self.filterUICommand)
        return toolBarUICommands

