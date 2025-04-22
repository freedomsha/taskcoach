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
import wx
# from taskcoachlib.thirdparty import aui
# import aui2 as aui
from wx.lib.agw import aui
from taskcoachlib import operating_system

log = logging.getLogger(__name__)


class AuiManagedFrameWithDynamicCenterPane(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        agwStyle = aui.AUI_MGR_DEFAULT | aui.AUI_MGR_ALLOW_ACTIVE_PANE
        if not operating_system.isWindows():
            # With this style on Windows, you can't dock back floating frames
            agwStyle |= aui.AUI_MGR_USE_NATIVE_MINIFRAMES
        self.manager = aui.AuiManager(self, agwStyle)
        self.manager.SetAutoNotebookStyle(aui.AUI_NB_TOP |
                                          aui.AUI_NB_CLOSE_BUTTON |
                                          aui.AUI_NB_SUB_NOTEBOOK |
                                          aui.AUI_NB_SCROLL_BUTTONS)
        self.bindEvents()

    def bindEvents(self):
        for eventType in aui.EVT_AUI_PANE_CLOSE, aui.EVT_AUI_PANE_FLOATING:
            self.manager.Bind(eventType, self.onPaneClosingOrFloating)

    def onPaneClosingOrFloating(self, event):
        pane = event.GetPane()
        dockedPanes = self.dockedPanes()
        if self.isCenterPane(pane) and len(dockedPanes) == 1:
            event.Veto()
        else:
            event.Skip()
            if self.isCenterPane(pane):
                if pane in dockedPanes:
                    dockedPanes.remove(pane)
                dockedPanes[0].Center()

    def addPane(self, window, caption, name, floating=False):
        # # x, y = window.GetPositionTuple()
        # # wxPyDeprecationWarning: Call to deprecated item. Use GetPosition instead
        window.Show()
        self.Show()
        x, y = window.GetPosition()
        # # # x, y = window.ClientToScreenXY(x, y)
        # # # AttributeError: 'TaskViewer' object has no attribute 'ClientToScreenXY'. Did you mean: 'ClientToScreen'?
        # # # Debug: ClientToScreen cannot work when toplevel window is not shown
        # if window.Shown:
        # x, y = window.ClientToScreen(x, y)  # TODO : j'ai ClientToScreen cannot work when toplevel window is not shown même si window.shown est True
        # #     # pour window CategoryViewer (gui.viewer.category.CategoryViewer)
        if window.IsShown():
            x, y = window.ClientToScreen(x, y)
        else:
            log.debug("La fenêtre %s n'est pas encore affiché, ClientToScreen ignoré.", window)
        #     print("frame.py: Debug: ClientToScreen cannot work when toplevel window is not shown")
        # RESOLUTION DE "ClientToScreen cannot work when toplevel window is not shown" :
        paneInfo = aui.AuiPaneInfo()
        paneInfo = paneInfo.CloseButton(True).Floatable(True).\
            Name(name).Caption(caption).Right().\
            FloatingSize((300, 200)).BestSize((200, 200)).\
            FloatingPosition((x + 30, y + 30)).\
            CaptionVisible().MaximizeButton().DestroyOnClose()
        # paneInfo = paneInfo.CloseButton(True).Floatable(True). \
        #     Name(name).Caption(caption).Right(). \
        #     FloatingSize((300, 200)).BestSize((200, 200)). \
        #     CaptionVisible().MaximizeButton().DestroyOnClose()

        if floating:
            # Positionner la fenêtre flottante de manière relative à l'écran ou à la fenêtre principale après l'ajout.
            paneInfo.Float()
            # Vous pourriez définir une position initiale approximative ici,
            # puis potentiellement l'ajuster après l'affichage.
            # Par exemple, centrer approximativement :
            screen_rect = wx.GetClientDisplayRect()
            float_x = (screen_rect.width - 300) // 2 + 30
            float_y = (screen_rect.height - 200) // 2 + 30
            paneInfo = paneInfo.FloatingPosition((float_x, float_y))
        if not self.dockedPanes():
            paneInfo = paneInfo.Center()

        self.manager.AddPane(window, paneInfo)
        self.manager.Update()

    def setPaneTitle(self, window, title):
        self.manager.GetPane(window).Caption(title)

    def dockedPanes(self):
        return [pane for pane in self.manager.GetAllPanes()
                if not pane.IsToolbar() and not pane.IsFloating()
                and not pane.IsNotebookPage()]
        
    def float(self, window):
        self.manager.GetPane(window).Float()

    @staticmethod
    def isCenterPane(pane):
        return pane.dock_direction_get() == aui.AUI_DOCK_CENTER
