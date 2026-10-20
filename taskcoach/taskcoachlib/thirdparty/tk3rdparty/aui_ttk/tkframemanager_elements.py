# -*- coding: utf-8 -*-
"""Première étape de la conversion de framemanager.py vers Tkinter.

Classes converties dans ce bloc : AuiDockInfo, AuiDockingGuideInfo,
AuiDockUIPart, AuiPaneButton, AuiManagerEvent et AuiPaneInfo.
"""

import tkinter as tk
from .aui_tk_constants import *


class AuiDockInfo:
    def __init__(self):
        self.dock_direction = 0
        self.dock_layer = 0
        self.dock_row = 0
        self.size = 0
        self.min_size = 0
        self.resizable = True
        self.fixed = False
        self.toolbar = False
        self.rect = (0, 0, 0, 0)
        self.panes = []

    def IsOk(self):
        return self.dock_direction != 0

    def IsHorizontal(self):
        return self.dock_direction in (AUI_DOCK_TOP, AUI_DOCK_BOTTOM)

    def IsVertical(self):
        return self.dock_direction in (AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_CENTER)


class AuiDockingGuideInfo:
    def __init__(self, other=None):
        if other:
            self.Assign(other)
        else:
            self.host = None
            self.dock_direction = AUI_DOCK_NONE

    def Assign(self, other):
        self.host = other.host
        self.dock_direction = other.dock_direction

    def Host(self, h):
        self.host = h
        return self

    def Left(self):
        self.dock_direction = AUI_DOCK_LEFT
        return self

    def Right(self):
        self.dock_direction = AUI_DOCK_RIGHT
        return self

    def Top(self):
        self.dock_direction = AUI_DOCK_TOP
        return self

    def Bottom(self):
        self.dock_direction = AUI_DOCK_BOTTOM
        return self

    def Center(self):
        self.dock_direction = AUI_DOCK_CENTER
        return self

    def Centre(self):
        self.dock_direction = AUI_DOCK_CENTRE
        return self


class AuiDockUIPart:
    typeCaption = 0
    typeGripper = 1
    typeDock = 2
    typeDockSizer = 3
    typePane = 4
    typePaneSizer = 5
    typeBackground = 6
    typePaneBorder = 7
    typePaneButton = 8

    def __init__(self):
        self.orientation = "vertical"
        self.type = 0
        self.rect = (0, 0, 0, 0)


class AuiPaneButton:
    def __init__(self, button_id):
        self.button_id = button_id


class AuiManagerEvent:
    def __init__(self, manager=None, pane=None, button=None, dc=None):
        self.manager = manager
        self.pane = pane
        self.button = button
        self.dc = dc
        self.veto_flag = False
        self.canveto_flag = True

    def SetManager(self, mgr):
        self.manager = mgr

    def SetDC(self, pdc):
        self.dc = pdc

    def SetPane(self, p):
        self.pane = p

    def SetButton(self, b):
        self.button = b

    def GetManager(self):
        return self.manager

    def GetDC(self):
        return self.dc

    def GetPane(self):
        return self.pane

    def GetButton(self):
        return self.button

    def Veto(self, veto=True):
        self.veto_flag = veto

    def GetVeto(self):
        return self.veto_flag

    def SetCanVeto(self, can_veto):
        self.canveto_flag = can_veto

    def CanVeto(self):
        return self.canveto_flag and self.veto_flag


class AuiPaneInfo:
    optionFloating = 2**0
    optionHidden = 2**1
    optionLeftDockable = 2**2
    optionRightDockable = 2**3
    optionTopDockable = 2**4
    optionBottomDockable = 2**5
    optionFloatable = 2**6
    optionMovable = 2**7
    optionResizable = 2**8
    optionPaneBorder = 2**9
    optionCaption = 2**10
    optionGripper = 2**11
    optionDestroyOnClose = 2**12
    optionToolbar = 2**13
    optionActive = 2**14
    optionGripperTop = 2**15
    optionMaximized = 2**16
    optionDockFixed = 2**17
    optionNotebookDockable = 2**18
    optionMinimized = 2**19
    optionLeftSnapped = 2**20
    optionRightSnapped = 2**21
    optionTopSnapped = 2**22
    optionBottomSnapped = 2**23
    optionFlyOut = 2**24
    optionCaptionLeft = 2**25
    buttonClose = 2**26
    buttonMaximize = 2**27
    buttonMinimize = 2**28
    buttonPin = 2**29
    buttonCustom1 = 2**30
    buttonCustom2 = 2**31
    buttonCustom3 = 2**32
    savedHiddenState = 2**33
    actionPane = 2**34
    wasMaximized = 2**35
    needsRestore = 2**36

    def __init__(self):
        self.window = None
        self.frame = None
        self.state = 0
        self.dock_direction = AUI_DOCK_LEFT
        self.dock_layer = 0
        self.dock_row = 0
        self.dock_pos = 0
        self.minimize_mode = AUI_MINIMIZE_POS_SMART
        self.floating_pos = (-1, -1)
        self.floating_size = (-1, -1)
        self.best_size = (-1, -1)
        self.min_size = (-1, -1)
        self.max_size = (-1, -1)
        self.dock_proportion = 0
        self.caption = ""
        self.buttons = []
        self.name = ""
        self.icon = None
        self.rect = (0, 0, 0, 0)
        self.notebook_id = -1
        self.transparent = 255
        self.needsTransparency = False
        self.previousDockPos = None
        self.previousDockSize = 0
        self.snapped = 0
        self.minimize_target = None
        self.DefaultPane()

    @property
    def dock_dir(self):
        return self.dock_direction

    @dock_dir.setter
    def dock_dir(self, v):
        self.dock_direction = v

    def IsOk(self):
        return self.window is not None

    def IsMaximized(self):
        return self.HasFlag(self.optionMaximized)

    def IsMinimized(self):
        return self.HasFlag(self.optionMinimized)

    def IsFixed(self):
        return self.HasFlag(self.optionDockFixed)

    def IsResizeable(self):
        return self.HasFlag(self.optionResizable)

    def IsShown(self):
        return not self.HasFlag(self.optionHidden)

    def IsFloating(self):
        return self.HasFlag(self.optionFloating)

    def IsDocked(self):
        return not self.IsFloating()

    def IsToolbar(self):
        return self.HasFlag(self.optionToolbar)

    def IsTopDockable(self):
        return self.HasFlag(self.optionTopDockable)

    def IsBottomDockable(self):
        return self.HasFlag(self.optionBottomDockable)

    def IsLeftDockable(self):
        return self.HasFlag(self.optionLeftDockable)

    def IsRightDockable(self):
        return self.HasFlag(self.optionRightDockable)

    def IsDockable(self):
        return (
            self.IsTopDockable()
            or self.IsBottomDockable()
            or self.IsLeftDockable()
            or self.IsRightDockable()
        )

    def IsFloatable(self):
        return self.HasFlag(self.optionFloatable)

    def IsMovable(self):
        return self.HasFlag(self.optionMovable)

    def IsDestroyOnClose(self):
        return self.HasFlag(self.optionDestroyOnClose)

    def IsNotebookDockable(self):
        return self.HasFlag(self.optionNotebookDockable)

    def IsTopSnappable(self):
        return self.HasFlag(self.optionTopSnapped)

    def IsBottomSnappable(self):
        return self.HasFlag(self.optionBottomSnapped)

    def IsLeftSnappable(self):
        return self.HasFlag(self.optionLeftSnapped)

    def IsRightSnappable(self):
        return self.HasFlag(self.optionRightSnapped)

    def IsSnappable(self):
        return (
            self.IsTopSnappable()
            or self.IsBottomSnappable()
            or self.IsLeftSnappable()
            or self.IsRightSnappable()
        )

    def IsFlyOut(self):
        return self.HasFlag(self.optionFlyOut)

    def HasCaption(self):
        return self.HasFlag(self.optionCaption)

    def HasCaptionLeft(self):
        return self.HasFlag(self.optionCaptionLeft)

    def HasGripper(self):
        return self.HasFlag(self.optionGripper)

    def HasBorder(self):
        return self.HasFlag(self.optionPaneBorder)

    def HasCloseButton(self):
        return self.HasFlag(self.buttonClose)

    def HasMaximizeButton(self):
        return self.HasFlag(self.buttonMaximize)

    def HasMinimizeButton(self):
        return self.HasFlag(self.buttonMinimize)

    def GetMinimizeMode(self):
        return self.minimize_mode

    def HasPinButton(self):
        return self.HasFlag(self.buttonPin)

    def HasGripperTop(self):
        return self.HasFlag(self.optionGripperTop)

    def Window(self, w):
        self.window = w
        return self

    def Name(self, n):
        self.name = n
        return self

    def Caption(self, c):
        self.caption = c
        return self

    def Left(self):
        self.dock_direction = AUI_DOCK_LEFT
        return self

    def Right(self):
        self.dock_direction = AUI_DOCK_RIGHT
        return self

    def Top(self):
        self.dock_direction = AUI_DOCK_TOP
        return self

    def Bottom(self):
        self.dock_direction = AUI_DOCK_BOTTOM
        return self

    def Center(self):
        self.dock_direction = AUI_DOCK_CENTER
        return self

    def Centre(self):
        self.dock_direction = AUI_DOCK_CENTRE
        return self

    def Direction(self, direction):
        self.dock_direction = direction
        return self

    def Layer(self, layer):
        self.dock_layer = layer
        return self

    def Row(self, row):
        self.dock_row = row
        return self

    def Position(self, pos):
        self.dock_pos = pos
        return self

    def MinSize(self, *args):
        self.min_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def MinSize1(self, w):
        self.min_size = (w, -1)
        return self

    def MinSize2(self, h):
        self.min_size = (-1, h)
        return self

    def MaxSize(self, *args):
        self.max_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def MaxSize1(self, w):
        self.max_size = (w, -1)
        return self

    def MaxSize2(self, h):
        self.max_size = (-1, h)
        return self

    def BestSize(self, *args):
        self.best_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def BestSize1(self, w):
        self.best_size = (w, -1)
        return self

    def BestSize2(self, h):
        self.best_size = (-1, h)
        return self

    def FloatingPosition(self, *args):
        self.floating_pos = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def FloatingSize(self, *args):
        self.floating_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def Maximize(self):
        return self.SetFlag(self.optionMaximized, True)

    def Minimize(self):
        return self.SetFlag(self.optionMinimized, True)

    def MinimizeMode(self, mode):
        self.minimize_mode = mode
        return self

    def MinimizeTarget(self, target):
        self.minimize_target = target
        return self

    def Restore(self):
        self.SetFlag(self.optionMinimized, False)
        return self.SetFlag(self.optionMaximized, False)

    def Fixed(self):
        # return self.SetFlag(self.optionResizable, False).SetFlag(
        #     self.optionDockFixed, True
        # )
        self.SetFlag(self.optionResizable, False)
        return self.SetFlag(self.optionDockFixed, True)

    def Resizable(self, resize=True):
        return self.SetFlag(self.optionResizable, resize)

    def Transparent(self, alpha=255):
        self.transparent = alpha
        self.needsTransparency = True
        return self

    def Dock(self):
        return self.SetFlag(self.optionFloating, False)

    def Float(self):
        return self.SetFlag(self.optionFloating, True)

    def Hide(self):
        return self.SetFlag(self.optionHidden, True)

    def Show(self, show=True):
        return self.SetFlag(self.optionHidden, not show)

    def NotebookPage(self, page=-1):
        self.notebook_id = page
        return self

    def NotebookControl(self, ctrl):
        self.notebook_control = ctrl
        return self

    def HasNotebook(self):
        return getattr(self, "notebook_id", -1) >= 0

    def IsNotebookPage(self):
        return self.HasNotebook()

    def IsNotebookControl(self):
        return getattr(self, "notebook_control", None) is not None

    def SetNameFromNotebookId(self, idx):
        self.name = f"notebook_page_{idx}"
        return self

    def CaptionVisible(self, visible=True):
        return self.SetFlag(self.optionCaption, visible)

    def PaneBorder(self, visible=True):
        return self.SetFlag(self.optionPaneBorder, visible)

    def Gripper(self, visible=True):
        return self.SetFlag(self.optionGripper, visible)

    def GripperTop(self, visible=True):
        return self.SetFlag(self.optionGripperTop, visible)

    def CloseButton(self, visible=True):
        return self.SetFlag(self.buttonClose, visible)

    def MaximizeButton(self, visible=True):
        return self.SetFlag(self.buttonMaximize, visible)

    def MinimizeButton(self, visible=True):
        return self.SetFlag(self.buttonMinimize, visible)

    def PinButton(self, visible=True):
        return self.SetFlag(self.buttonPin, visible)

    def DestroyOnClose(self, b=True):
        return self.SetFlag(self.optionDestroyOnClose, b)

    def TopDockable(self, b=True):
        return self.SetFlag(self.optionTopDockable, b)

    def BottomDockable(self, b=True):
        return self.SetFlag(self.optionBottomDockable, b)

    def LeftDockable(self, b=True):
        return self.SetFlag(self.optionLeftDockable, b)

    def RightDockable(self, b=True):
        return self.SetFlag(self.optionRightDockable, b)

    def Floatable(self, b=True):
        return self.SetFlag(self.optionFloatable, b)

    def Movable(self, b=True):
        return self.SetFlag(self.optionMovable, b)

    def NotebookDockable(self, b=True):
        return self.SetFlag(self.optionNotebookDockable, b)

    def DockFixed(self):
        return self.SetFlag(self.optionDockFixed, True)

    def Dockable(self, b=True):
        self.TopDockable(b)
        self.BottomDockable(b)
        self.LeftDockable(b)
        return self.RightDockable(b)

    def TopSnappable(self, b=True):
        return self.SetFlag(self.optionTopSnapped, b)

    def BottomSnappable(self, b=True):
        return self.SetFlag(self.optionBottomSnapped, b)

    def LeftSnappable(self, b=True):
        return self.SetFlag(self.optionLeftSnapped, b)

    def RightSnappable(self, b=True):
        return self.SetFlag(self.optionRightSnapped, b)

    def Snappable(self, b=True):
        self.TopSnappable(b)
        self.BottomSnappable(b)
        self.LeftSnappable(b)
        return self.RightSnappable(b)

    def FlyOut(self, b=True):
        return self.SetFlag(self.optionFlyOut, b)

    def SetDockPos(self, direction, layer=0, row=0, pos=0):
        self.dock_direction = direction
        self.dock_layer = layer
        self.dock_row = row
        self.dock_pos = pos
        return self

    def DefaultPane(self):
        self.state = 0
        # self.Dock().CaptionVisible().PaneBorder().Movable()
        # self.TopDockable().BottomDockable().LeftDockable().RightDockable()
        self.Dock()
        self.CaptionVisible()
        self.PaneBorder()
        self.Movable()
        self.TopDockable()
        self.BottomDockable()
        self.LeftDockable()
        self.RightDockable()
        return self

    def CentrePane(self):
        return self.CenterPane()

    def CenterPane(self):
        self.state = 0
        # self.Dock().Resizable().Floatable().Movable()
        self.Dock()
        self.Center()
        self.Resizable()
        self.Floatable()
        self.Movable()
        return self

    def ToolbarPane(self):
        self.state = 0
        # self.DefaultPane().Dock().Gripper()
        self.DefaultPane()
        self.Dock()
        self.Gripper()
        return self

    def Icon(self, icon):
        self.icon = icon
        return self

    def SetFlag(self, flag, option=True):
        # self.state |= flag if option else 0 if option else self.state & ~flag
        # return self if option else self
        if option:
            self.state |= flag
        else:
            self.state &= ~flag
        return self

    def HasFlag(self, flag):
        return (self.state & flag) == flag

    def ResetButtons(self):
        # self.state &= ~0xFC000000
        mask = (self.buttonClose | self.buttonMaximize | self.buttonMinimize |
                self.buttonPin | self.buttonCustom1 | self.buttonCustom2 |
                self.buttonCustom3)
        self.state &= ~mask
        return self

    def CountButtons(self):
        return sum(
            self.HasFlag(f)
            for f in (
                self.buttonClose,
                self.buttonMaximize,
                self.buttonMinimize,
                self.buttonPin,
                self.buttonCustom1,
                self.buttonCustom2,
                self.buttonCustom3,
            )
        )

    def IsHorizontal(self):
        return self.dock_direction in (AUI_DOCK_TOP, AUI_DOCK_BOTTOM)

    def IsVertical(self):
        return self.dock_direction in (AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_CENTER)
