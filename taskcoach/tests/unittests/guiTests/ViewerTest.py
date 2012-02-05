'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2012 Task Coach developers <developers@taskcoach.org>

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

import test
from taskcoachlib import gui, config, widgets, persistence
from taskcoachlib.domain import task, date
from taskcoachlib.thirdparty import hypertreelist


class Window(widgets.AuiManagedFrameWithDynamicCenterPane):
    def addPane(self, viewer, title):
        super(Window, self).addPane(viewer, title, 'name')
        

class ViewerTest(test.wxTestCase):
    def setUp(self):
        super(ViewerTest, self).setUp()
        self.settings = config.Settings(load=False)
        self.taskFile = persistence.TaskFile()
        self.task = task.Task('task')
        self.taskFile.tasks().append(self.task)
        self.window = Window(self.frame)
        self.viewerContainer = gui.viewer.ViewerContainer(self.window, 
            self.settings)
        self.viewer = self.createViewer()
        self.viewerContainer.addViewer(self.viewer)

    def tearDown(self):
        super(ViewerTest, self).tearDown()
        self.taskFile.close()
        self.taskFile.stop()

    def createViewer(self):
        return gui.viewer.TaskViewer(self.window, self.taskFile,
            self.settings)

    def testSelectAllViaWidget(self):
        self.viewer.widget.selectall()
        self.viewer.updateSelection()
        self.assertEqual([self.task], self.viewer.curselection())
        
    def testSelectAllViaWidgetWithMultipleItems(self):
        self.taskFile.tasks().append(task.Task('second'))
        self.viewer.widget.selectall()
        self.viewer.updateSelection()
        self.assertEqual(2, len(self.viewer.curselection()))
        
    def testSelectAll(self):
        self.viewer.selectall()
        self.viewer.endOfSelectAll()
        self.assertEqual([self.task], self.viewer.curselection())
        
    def testSelectAllWithMultipleItems(self):
        self.taskFile.tasks().append(task.Task('second'))
        self.viewer.selectall()
        self.viewer.endOfSelectAll()
        self.assertEqual(2, len(self.viewer.curselection()))
        
    def testFirstViewerInstanceSettingsSection(self):
        self.assertEqual(self.viewer.__class__.__name__.lower(), 
                         self.viewer.settingsSection())
        
    def testSecondViewerInstanceHasAnotherSettingsSection(self):
        viewer2 = self.createViewer()
        self.assertEqual(self.viewer.settingsSection()+'1', 
                         viewer2.settingsSection())
        
    def testTitle(self):
        self.assertEqual(self.viewer.defaultTitle, self.viewer.title())
        
    def testSetTitle(self):
        self.viewer.setTitle('New title')
        self.assertEqual('New title', self.viewer.title())
        
    def testSetTitleSavesTitleInSettings(self):
        self.viewer.setTitle('New title')
        self.assertEqual('New title', self.settings.get(self.viewer.settingsSection(), 'title'))
        
    def testSetTitleDoesNotSaveTitleInSettingsWhenTitleIsDefaultTitle(self):
        self.viewer.setTitle(self.viewer.defaultTitle)
        self.assertEqual('', self.settings.get(self.viewer.settingsSection(), 'title'))

    def testSetTitleChangesTabTitle(self):
        self.viewer.setTitle('New title')
        self.assertEqual('New title', self.window.manager.GetPane(self.viewer).caption)

    def testGetItemTooltipData(self):
        self.task.setDescription('Description')
        expectedData = [(None, ['Description']), ('note_icon', []), ('paperclip_icon', [])]
        self.assertEqual(expectedData, self.viewer.getItemTooltipData(self.task))


class SortableViewerTest(test.TestCase):
    def setUp(self):
        self.settings = config.Settings(load=False)
        self.viewer = self.createViewer()
        
    def createViewer(self):
        viewer = gui.viewer.mixin.SortableViewerMixin()
        viewer.settings = self.settings
        viewer.settingsSection = lambda: 'taskviewer'
        viewer.SorterClass = task.sorter.Sorter
        presentation = viewer.createSorter(task.TaskList())
        viewer.presentation = lambda: presentation
        return viewer
        
    def testIsSortable(self):
        self.failUnless(self.viewer.isSortable())

    def testSortBy(self):
        self.viewer.sortBy('subject')
        self.assertEqual('subject', 
            self.settings.get(self.viewer.settingsSection(), 'sortby'))

    def testSortByTwiceFlipsSortOrder(self):
        self.viewer.sortBy('subject')
        self.viewer.setSortOrderAscending(True)
        self.viewer.sortBy('subject')
        self.failIf(self.viewer.isSortOrderAscending())

    def testIsSortedBy(self):
        self.viewer.sortBy('description')
        self.failUnless(self.viewer.isSortedBy('description'))
        
    def testSortOrderAscending(self):
        self.viewer.setSortOrderAscending(True)
        self.failUnless(self.viewer.isSortOrderAscending())

    def testSortOrderDescending(self):
        self.viewer.setSortOrderAscending(False)
        self.failIf(self.viewer.isSortOrderAscending())
                
    def testSetSortCaseSensitive(self):
        self.viewer.setSortCaseSensitive(True)
        self.failUnless(self.viewer.isSortCaseSensitive())
        
    def testSetSortCaseInsensitive(self):
        self.viewer.setSortCaseSensitive(False)
        self.failIf(self.viewer.isSortCaseSensitive())
        
    def testApplySettingsWhenCreatingViewer(self):
        self.settings.set(self.viewer.settingsSection(), 'sortby', 'description')
        self.settings.set(self.viewer.settingsSection(), 'sortascending', 'True')
        anotherViewer = self.createViewer()
        anotherViewer.presentation().extend([task.Task(description='B'), 
                                             task.Task(description='A')])
        self.assertEqual(['A', 'B'], 
                         [t.description() for t in anotherViewer.presentation()])


class SortableViewerForTasksTest(test.TestCase):
    def setUp(self):
        self.settings = config.Settings(load=False)
        self.viewer = gui.viewer.mixin.SortableViewerForTasksMixin()
        self.viewer.settings = self.settings
        self.viewer.settingsSection = lambda: 'taskviewer'
        self.viewer.presentation = lambda: task.sorter.Sorter(task.TaskList())

    def testSetSortByTaskStatusFirst(self):
        self.viewer.setSortByTaskStatusFirst(True)
        self.failUnless(self.viewer.isSortByTaskStatusFirst())
        
    def testSetNoSortByTaskStatusFirst(self):
        self.viewer.setSortByTaskStatusFirst(False)
        self.failIf(self.viewer.isSortByTaskStatusFirst())

      
class DummyViewer(object):
    def isTreeViewer(self):
        return False
    
    def createFilter(self, presentation):
        return presentation


class SearchableViewerUnderTest(gui.viewer.mixin.SearchableViewerMixin, 
                                DummyViewer):
    pass   

    
class SearchableViewerTest(test.TestCase):
    def setUp(self):
        self.settings = config.Settings(load=False)
        self.viewer = self.createViewer()
        
    def createViewer(self):
        viewer = SearchableViewerUnderTest()
        # pylint: disable-msg=W0201
        viewer.settings = self.settings
        viewer.settingsSection = lambda: 'taskviewer'
        presentation = viewer.createFilter(task.TaskList())
        viewer.presentation = lambda: presentation
        return viewer
        
    def testIsSearchable(self):
        self.failUnless(self.viewer.isSearchable())
        
    def testDefaultSearchFilter(self):
        self.assertEqual(('', False, False, False), self.viewer.getSearchFilter())
        
    def testSetSearchFilterString(self):
        self.viewer.setSearchFilter('bla', matchCase=True)
        self.assertEqual('bla', self.settings.get(self.viewer.settingsSection(),
                                                  'searchfilterstring'))

    def testSetSearchFilterString_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task())
        self.viewer.setSearchFilter('bla')
        self.failIf(self.viewer.presentation())
        
    def testSearchMatchCase(self):
        self.viewer.setSearchFilter('bla', matchCase=True)
        self.assertEqual(True, 
            self.settings.getboolean(self.viewer.settingsSection(), 
                                     'searchfiltermatchcase'))
        
    def testSearchMatchCase_AffectsPresenation(self):
        self.viewer.presentation().append(task.Task('BLA'))
        self.viewer.setSearchFilter('bla', matchCase=True)
        self.failIf(self.viewer.presentation())
        
    def testSearchIncludesSubItems(self):
        self.viewer.setSearchFilter('bla', includeSubItems=True)
        self.assertEqual(True, 
            self.settings.getboolean(self.viewer.settingsSection(), 
                                     'searchfilterincludesubitems'))
        
    def testSearchIncludesSubItems_AffectsPresentation(self):
        parent = task.Task('parent')
        child = task.Task('child')
        parent.addChild(child)
        self.viewer.presentation().append(parent)
        self.viewer.setSearchFilter('parent', includeSubItems=True)
        self.assertEqual(2, len(self.viewer.presentation()))
        
    def testSearchDescription(self):
        self.viewer.setSearchFilter('bla', searchDescription=True)
        self.assertEqual(True, self.settings.getboolean(self.viewer.settingsSection(),
                                                        'searchdescription'))
        
    def testSearchDescription_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task('subject', description='description'))
        self.viewer.setSearchFilter('descr', searchDescription=True)
        self.assertEqual(1, len(self.viewer.presentation()))
        
    def testApplySettingsWhenCreatingViewer(self):
        self.settings.set(self.viewer.settingsSection(), 'searchfilterstring', 'whatever')
        anotherViewer = self.createViewer()
        anotherViewer.presentation().append(task.Task())
        self.failIf(anotherViewer.presentation())


class FilterableViewerTest(test.TestCase):
    def setUp(self):
        self.viewer = gui.viewer.mixin.FilterableViewerMixin()
        
    def testIsFilterable(self):
        self.failUnless(self.viewer.isFilterable())


class FilterableViewerForTasksUnderTest(gui.viewer.mixin.FilterableViewerForTasksMixin, 
                                        DummyViewer):
    pass
        
        
class FilterableViewerForTasks(test.TestCase):
    def setUp(self):
        self.settings = config.Settings(load=False)
        task.Task.settings = self.settings
        self.viewer = self.createViewer()

    def tearDown(self):
        super(FilterableViewerForTasks, self).tearDown()
        self.viewer.taskFile.close()
        self.viewer.taskFile.stop()

    def createViewer(self):
        viewer = FilterableViewerForTasksUnderTest()
        # pylint: disable-msg=W0201
        viewer.taskFile = persistence.TaskFile()
        viewer.settings = self.settings
        viewer.settingsSection = lambda: 'taskviewer'
        presentation = viewer.createFilter(viewer.taskFile.tasks())
        viewer.presentation = lambda: presentation
        return viewer

    def testIsNotHidingInactiveTasksByDefault(self):
        self.failIf(self.viewer.isHidingInactiveTasks())

    def testHideInactiveTasks(self):
        self.viewer.hideInactiveTasks()
        self.failUnless(self.viewer.isHidingInactiveTasks())
        
    def testHideInactiveTasks_SetsSetting(self):
        self.viewer.hideInactiveTasks()
        self.failUnless(self.settings.getboolean(self.viewer.settingsSection(), 
                                                 'hideinactivetasks'))

    def testHideInactiveTasks_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task(plannedStartDateTime=date.Now() + date.oneDay))
        self.viewer.hideInactiveTasks()
        self.failIf(self.viewer.presentation())
    
    def testUnhideInactiveTasks(self):
        self.viewer.presentation().append(task.Task(plannedStartDateTime=date.Now() + date.oneDay))
        self.viewer.hideInactiveTasks()
        self.viewer.hideInactiveTasks(False)
        self.failUnless(self.viewer.presentation())

    def testIsNotHidingLateTasksByDefault(self):
        self.failIf(self.viewer.isHidingLateTasks())

    def testHideLateTasks(self):
        self.viewer.hideLateTasks()
        self.failUnless(self.viewer.isHidingLateTasks())
        
    def testHideLateTasks_SetsSetting(self):
        self.viewer.hideLateTasks()
        self.failUnless(self.settings.getboolean(self.viewer.settingsSection(), 
                                                 'hidelatetasks'))

    def testHideLateTasks_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task(plannedStartDateTime=date.Now() - date.oneDay))
        self.viewer.hideLateTasks()
        self.failIf(self.viewer.presentation())
    
    def testUnhideLateTasks(self):
        self.viewer.presentation().append(task.Task(plannedStartDateTime=date.Now() - date.oneDay))
        self.viewer.hideLateTasks()
        self.viewer.hideLateTasks(False)
        self.failUnless(self.viewer.presentation())
 
    def testIsNotHidingDueSoonTasksByDefault(self):
        self.failIf(self.viewer.isHidingDueSoonTasks())

    def testHideDueSoonTasks(self):
        self.viewer.hideDueSoonTasks()
        self.failUnless(self.viewer.isHidingDueSoonTasks())
        
    def testHideDueSoonTasks_SetsSetting(self):
        self.viewer.hideDueSoonTasks()
        self.failUnless(self.settings.getboolean(self.viewer.settingsSection(), 
                                                 'hideduesoontasks'))

    def testHideDueSoonTasks_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.viewer.hideDueSoonTasks()
        self.failIf(self.viewer.presentation())
    
    def testUnhideDueSoonTasks(self):
        self.viewer.presentation().append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.viewer.hideDueSoonTasks()
        self.viewer.hideDueSoonTasks(False)
        self.failUnless(self.viewer.presentation())

    def testIsNotHidingOverDueTasksByDefault(self):
        self.failIf(self.viewer.isHidingOverDueTasks())

    def testHideOverDueTasks(self):
        self.viewer.hideOverDueTasks()
        self.failUnless(self.viewer.isHidingOverDueTasks())
        
    def testHideOverDueTasks_SetsSetting(self):
        self.viewer.hideOverDueTasks()
        self.failUnless(self.settings.getboolean(self.viewer.settingsSection(), 
                                                 'hideoverduetasks'))

    def testHideOverDueTasks_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task(dueDateTime=date.Now() - date.oneDay))
        self.viewer.hideOverDueTasks()
        self.failIf(self.viewer.presentation())
    
    def testUnhideOverDueTasks(self):
        self.viewer.presentation().append(task.Task(dueDateTime=date.Now() - date.oneDay))
        self.viewer.hideOverDueTasks()
        self.viewer.hideOverDueTasks(False)
        self.failUnless(self.viewer.presentation())
       
    def testIsNotHidingCompletedTasksByDefault(self):
        self.failIf(self.viewer.isHidingCompletedTasks())
        
    def testHideCompletedTasks(self):
        self.viewer.hideCompletedTasks()
        self.failUnless(self.viewer.isHidingCompletedTasks())
    
    def testHideCompletedTasks_SetsSetting(self):
        self.viewer.hideCompletedTasks()
        self.failUnless(self.settings.getboolean(self.viewer.settingsSection(),
                                                 'hidecompletedtasks'))
    
    def testHideCompletedTasks_AffectsPresentation(self):
        self.viewer.presentation().append(task.Task(completionDateTime=date.Now()))
        self.viewer.hideCompletedTasks()
        self.failIf(self.viewer.presentation())
        
    def testUnhideCompletedTasks(self):    
        self.viewer.presentation().append(task.Task(completionDateTime=date.Now()))
        self.viewer.hideCompletedTasks()
        self.viewer.hideCompletedTasks(False)
        self.failUnless(self.viewer.presentation())

    def testIsNotHidingCompositeTasksByDefault(self):
        self.failIf(self.viewer.isHidingCompositeTasks())
        
    def testHideCompositeTasks(self):
        self.viewer.hideCompositeTasks()
        self.failUnless(self.viewer.isHidingCompositeTasks())
        
    def testHideCompositeTasks_SetsSettings(self):
        self.viewer.hideCompositeTasks()
        self.failUnless(self.settings.getboolean(self.viewer.settingsSection(),
                                                 'hidecompositetasks'))

    def testHideCompositeTasks_AffectsPresentation(self):
        self.viewer.hideCompositeTasks()
        parent = task.Task()
        child = task.Task()
        parent.addChild(child)
        self.viewer.presentation().append(parent)
        self.assertEqual([child], self.viewer.presentation())
        
    def testUnhideCompositeTasks(self):
        self.viewer.hideCompositeTasks()
        parent = task.Task()
        child = task.Task()
        parent.addChild(child)
        self.viewer.presentation().append(parent)
        self.viewer.hideCompositeTasks(False)
        self.assertEqual(2, len(self.viewer.presentation()))
        
    def testClearAllFilters(self):
        self.viewer.hideCompositeTasks()
        self.viewer.hideCompletedTasks()
        self.viewer.hideInactiveTasks()
        self.viewer.hideActiveTasks()
        self.viewer.resetFilter()
        self.failIf(self.viewer.isHidingCompositeTasks())
        self.failIf(self.viewer.isHidingActiveTasks())
        self.failIf(self.viewer.isHidingInactiveTasks())
        self.failIf(self.viewer.isHidingCompletedTasks())     
        
    def testApplySettingsWhenCreatingViewer(self):
        self.settings.set(self.viewer.settingsSection(), 'hidecompletedtasks', 'True')
        anotherViewer = self.createViewer()
        anotherViewer.presentation().append(task.Task(completionDateTime=date.Now()))
        self.failIf(anotherViewer.presentation())   


class ViewerBaseClassTest(test.wxTestCase):
    def testNotImplementedError(self):
        taskFile = persistence.TaskFile()
        try:
            try:
                gui.viewer.base.Viewer(self.frame, taskFile,
                                       None, settingsSection='bla')
                self.fail('Expected NotImplementedError') # pragma: no cover
            except NotImplementedError:
                pass
        finally:
            taskFile.close()
            taskFile.stop()


class ViewerIteratorTestCase(test.wxTestCase):
    treeMode = 'Subclass responsibility'
    
    def createViewer(self):
        return gui.viewer.TaskViewer(self.window, self.taskFile,
            self.settings)

    def setUp(self):
        super(ViewerIteratorTestCase, self).setUp()
        self.settings = config.Settings(load=False)
        task.Task.settings = self.settings
        self.taskFile = persistence.TaskFile()
        self.taskList = self.taskFile.tasks()
        self.window = widgets.AuiManagedFrameWithDynamicCenterPane(self.frame)
        self.viewer = self.createViewer()
        self.viewer.showTree(self.treeMode == 'True')
        self.viewer.sortBy('subject')

    def tearDown(self):
        super(ViewerIteratorTestCase, self).tearDown()
        self.taskFile.close()
        self.taskFile.stop()

    def getItemsFromIterator(self):
        return list(self.viewer.visibleItems())


class ViewerIteratorTestsMixin(object):
    def testEmptyPresentation(self):
        self.assertEqual([], self.getItemsFromIterator())
        
    def testOneItem(self):
        self.taskList.append(task.Task())
        self.assertEqual(self.taskList, self.getItemsFromIterator())
        
    def testOneParentAndOneChild(self):
        parent = task.Task('Z')
        child = task.Task('A', parent=parent)
        parent.addChild(child)
        self.taskList.append(parent)
        if self.treeMode == 'True':
            expectedParentAndChildOrder = [parent, child]
        else:
            expectedParentAndChildOrder = [child, parent]
        self.assertEqual(expectedParentAndChildOrder, 
                         self.getItemsFromIterator())

    def testOneParentOneChildAndOneGrandChild(self):
        parent = task.Task('a-parent')
        child = task.Task('b-child', parent=parent)
        grandChild = task.Task('c-grandchild', parent=child)
        parent.addChild(child)
        child.addChild(grandChild)
        self.taskList.append(parent)
        self.assertEqual([parent, child, grandChild], 
                         self.getItemsFromIterator())
    
    def testThatTasksNotInPresentationAreExcluded(self):
        parent = task.Task('parent')
        child = task.Task('child')
        parent.addChild(child)
        self.taskList.append(parent)
        self.viewer.setSearchFilter('parent', matchCase=True)
        self.assertEqual([parent], self.getItemsFromIterator())
        
    
class TreeViewerIteratorTest(ViewerIteratorTestCase, ViewerIteratorTestsMixin):
    treeMode = 'True'
        
        
class ListViewerIteratorTest(ViewerIteratorTestCase, ViewerIteratorTestsMixin):
    treeMode = 'False'



class ViewerWithColumnsTest(test.wxTestCase):
    def setUp(self):
        self.settings = config.Settings(load=False)
        self.taskFile = persistence.TaskFile()
        self.viewer = gui.viewer.TaskViewer(self.frame, self.taskFile, self.settings)

    def tearDown(self):
        super(ViewerWithColumnsTest, self).tearDown()
        self.taskFile.close()
        self.taskFile.stop()

    def testDefaultColumnWidth(self):
        expectedWidth = hypertreelist._DEFAULT_COL_WIDTH # pylint: disable-msg=W0212
        self.assertEqual(expectedWidth, self.viewer.getColumnWidth('subject'))
        
