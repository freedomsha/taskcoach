import gui, wx, widgets

class DummyWidget(wx.Frame):
    def __init__(self, viewer):
        super(DummyWidget, self).__init__(viewer)
        self._selection = []
        self.viewer = viewer

    def DeleteAllItems(self, *args, **kwargs):
        pass

    def curselection(self):
        return self._selection

    def selection_set(self, index):
        self._selection.append(index)

    def selectall(self):
        self._selection = range(len(self.viewer.list))

    def select(self, indices):
        self._selection = indices

    def GetItemCount(self):
        return len(self.viewer.list)

    def refresh(self, *args, **kwargs):
        pass

    def GetColumnWidth(self, column):
        return 100
        
class DummyUICommand(gui.uicommand.UICommand):
    bitmap = 'undo'

    def onCommandActivate(self, event):
        self.activated = True

class DummyUICommands:
    def __getitem__(self, key):
        return DummyUICommand()
        
    def keys(self):
        return ['new', 'stopeffort']

class ViewerWithDummyWidget(gui.viewer.Viewer):
    def createWidget(self):
        return DummyWidget(self)
        
    def createSorter(self, taskList):
        return taskList
    
class TaskViewerWithDummyWidget(ViewerWithDummyWidget, gui.viewer.TaskViewer):
    pass

class TaskListViewerWithDummyWidget(ViewerWithDummyWidget, 
        gui.viewer.TaskListViewer):
    pass

class EffortPerDayViewerWithDummyWidget(ViewerWithDummyWidget,
        gui.viewer.EffortPerDayViewer):
    def createSorter(self, *args, **kwargs):
        return gui.viewer.EffortPerDayViewer.createSorter(self, *args, **kwargs)