# -*- coding: utf-8 -*-
"""Gestionnaire de cadres AUI adapté à Tkinter (conversion de framemanager.py).

Ce module regroupe les classes converties en trois étapes :
- structures de données (AuiDockInfo, AuiDockingGuideInfo, AuiDockUIPart,
  AuiPaneButton, AuiManagerEvent, AuiPaneInfo) ;
- fenêtres d'amarrage et cadres flottants (AuiDockingGuide,
  AuiDockingGuideWindow, AuiSingleDockingGuide, AuiCenterDockingGuide,
  AuiDockingHintWindow, AuiFloatingFrame) ;
- le gestionnaire proprement dit (AuiManager, AuiManager_DCP).

Limitations connues de cette première version fonctionnelle :
- un panneau flottant affiche uniquement son titre, car Tkinter ne permet pas
  de re-parenter un widget existant vers un nouveau Toplevel ;
- les sashes, l'amarrage interactif (glisser-déposer) et les animations
  restent simplifiés.
"""
import json
import tkinter as tk

from .tkdockart import AuiDefaultDockArt
try:
    from .tktabart import AuiDefaultTabArt
except ImportError:  # tktabart pas encore converti en Tkinter
    AuiDefaultTabArt = None
from .aui_tk_utilities import GetDockingImage
from .aui_tk_constants import *


def _safe_colour(art, key, fallback):
    """Retourne la couleur `key` de l'art provider, ou `fallback` en cas d'echec."""
    if art is None:
        return fallback
    try:
        value = art(key)
    except Exception:
        return fallback
    return value if value else fallback


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
        self.orientation = 'vertical'
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
    optionFloating = 2 ** 0
    optionHidden = 2 ** 1
    optionLeftDockable = 2 ** 2
    optionRightDockable = 2 ** 3
    optionTopDockable = 2 ** 4
    optionBottomDockable = 2 ** 5
    optionFloatable = 2 ** 6
    optionMovable = 2 ** 7
    optionResizable = 2 ** 8
    optionPaneBorder = 2 ** 9
    optionCaption = 2 ** 10
    optionGripper = 2 ** 11
    optionDestroyOnClose = 2 ** 12
    optionToolbar = 2 ** 13
    optionActive = 2 ** 14
    optionGripperTop = 2 ** 15
    optionMaximized = 2 ** 16
    optionDockFixed = 2 ** 17
    optionNotebookDockable = 2 ** 18
    optionMinimized = 2 ** 19
    optionLeftSnapped = 2 ** 20
    optionRightSnapped = 2 ** 21
    optionTopSnapped = 2 ** 22
    optionBottomSnapped = 2 ** 23
    optionFlyOut = 2 ** 24
    optionCaptionLeft = 2 ** 25
    buttonClose = 2 ** 26
    buttonMaximize = 2 ** 27
    buttonMinimize = 2 ** 28
    buttonPin = 2 ** 29
    buttonCustom1 = 2 ** 30
    buttonCustom2 = 2 ** 31
    buttonCustom3 = 2 ** 32
    savedHiddenState = 2 ** 33
    actionPane = 2 ** 34
    wasMaximized = 2 ** 35
    needsRestore = 2 ** 36

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
        self.caption = ''
        self.buttons = []
        self.name = ''
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
        return (self.IsTopDockable() or self.IsBottomDockable() or
                self.IsLeftDockable() or self.IsRightDockable())

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
        return (self.IsTopSnappable() or self.IsBottomSnappable() or
                self.IsLeftSnappable() or self.IsRightSnappable())

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
        return getattr(self, 'notebook_id', -1) >= 0

    def IsNotebookPage(self):
        return self.HasNotebook()

    def IsNotebookControl(self):
        return getattr(self, 'notebook_control', None) is not None

    def SetNameFromNotebookId(self, idx):
        self.name = 'notebook_page_%d' % idx
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
        self.Dock()
        self.Center()
        self.Resizable()
        self.Floatable()
        self.Movable()
        return self

    def ToolbarPane(self):
        self.state = 0
        self.DefaultPane()
        self.Dock()
        self.Gripper()
        return self

    def Icon(self, icon):
        self.icon = icon
        return self

    def SetFlag(self, flag, option=True):
        if option:
            self.state |= flag
        else:
            self.state &= ~flag
        return self

    def HasFlag(self, flag):
        return (self.state & flag) == flag

    def ResetButtons(self):
        mask = (self.buttonClose | self.buttonMaximize | self.buttonMinimize |
                self.buttonPin | self.buttonCustom1 | self.buttonCustom2 |
                self.buttonCustom3)
        self.state &= ~mask
        return self

    def CountButtons(self):
        return sum(self.HasFlag(f) for f in (self.buttonClose, self.buttonMaximize,
                    self.buttonMinimize, self.buttonPin, self.buttonCustom1,
                    self.buttonCustom2, self.buttonCustom3))

    def IsHorizontal(self):
        return self.dock_direction in (AUI_DOCK_TOP, AUI_DOCK_BOTTOM)

    def IsVertical(self):
        return self.dock_direction in (AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_CENTER)


class AuiDockingGuide(tk.Toplevel):
    def __init__(self, parent, id=-1, title='', pos=None, size=None, style=None,
                 name='AuiDockingGuide'):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes('-topmost', True)

    def HitTest(self, x, y):
        return False

    def ValidateNotebookDocking(self, valid):
        return valid


class AuiDockingGuideWindow(tk.Toplevel):
    def __init__(self, parent, rect, direction=0, center=False, useAero=False):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self._parent = parent
        self._direction = direction
        self._center = center
        self._valid = True
        self._useAero = useAero
        r = rect if not hasattr(rect, 'x') else (rect.x, rect.y, rect.width, rect.height)
        self.geometry('%dx%d+%d+%d' % (max(1, r[2]), max(1, r[3]), r[0], r[1]))
        self._bmp_unfocus, self._bmp_focus = GetDockingImage(direction, useAero, center)
        self._currentImage = self._bmp_unfocus
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._canvas.pack(fill='both', expand=True)

    def SetValid(self, valid):
        self._valid = valid

    def IsValid(self):
        return self._valid

    def OnEraseBackground(self, event):
        pass

    def DrawBackground(self, dc):
        dc.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(),
                            fill='#808080', outline='')

    def DrawDottedLine(self, dc, point, length, vertical=True):
        x, y = point
        for i in range(0, int(length), 4):
            if vertical:
                dc.create_line(x, y + i, x, y + i + 2, fill='#ffffff')
            else:
                dc.create_line(x + i, y, x + i + 2, y, fill='#ffffff')

    def DrawIcon(self, dc):
        img = self._currentImage
        if img is not None and hasattr(img, 'GetPhotoImage'):
            dc.create_image(self.winfo_width() // 2, self.winfo_height() // 2,
                            image=img.GetPhotoImage())

    def DrawArrow(self, dc):
        pass

    def OnPaint(self, event=None):
        self._canvas.delete('all')
        self.DrawBackground(self._canvas)
        self.DrawIcon(self._canvas)

    def Draw(self, dc):
        self.OnPaint(None)

    def UpdateDockGuide(self, pos):
        self.geometry('+%d+%d' % (pos[0], pos[1]))


class AuiSingleDockingGuide(AuiDockingGuideWindow):
    def __init__(self, parent, direction=0):
        super().__init__(parent, (0, 0, 31, 32), direction, False, False)

    def CreateShapesWithStyle(self, useWhidbey):
        pass

    def AeroMove(self, pos):
        self.UpdateDockGuide(pos)

    def SetGuideShape(self, event):
        pass

    def SetShape(self, region):
        pass

    def SetValid(self, valid):
        self._valid = valid

    def IsValid(self):
        return self._valid

    def UpdateDockGuide(self, pos):
        self.geometry('+%d+%d' % (pos[0], pos[1]))

    def HitTest(self, x, y):
        return False


class AuiCenterDockingGuide(AuiDockingGuideWindow):
    def __init__(self, parent):
        super().__init__(parent, (0, 0, 31, 32), AUI_DOCK_CENTER, True, False)

    def SetValid(self, valid):
        self._valid = valid

    def IsValid(self):
        return self._valid

    def UpdateDockGuide(self, pos):
        self.geometry('+%d+%d' % (pos[0], pos[1]))

    def HitTest(self, x, y):
        return False


class AuiDockingHintWindow(tk.Toplevel):
    def __init__(self, parent, id=-1, title='', pos=None, size=(1, 1), style=None,
                 name='auiHintWindow'):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self._blindMode = False
        provider = getattr(parent, 'GetArtProvider', lambda: None)()
        art = getattr(provider, 'GetColor', None) or getattr(provider, 'GetColour', None)
        self._background = _safe_colour(art, AUI_DOCKART_HINT_WINDOW_COLOUR, '#0040ff')
        self._border = _safe_colour(art, AUI_DOCKART_HINT_WINDOW_BORDER_COLOUR, '#3c3c3c')
        self._canvas = tk.Canvas(self, highlightthickness=0, bg=self._background)
        self._canvas.pack(fill='both', expand=True)

    def MakeVenetianBlinds(self):
        pass

    def SetBlindMode(self, agwFlags):
        self._blindMode = bool(agwFlags & AUI_MGR_VENETIAN_BLINDS_HINT)

    def SetShape(self, region):
        pass

    def Show(self, show=True):
        if show:
            self.deiconify()
        else:
            self.withdraw()

    def OnSize(self, event):
        pass

    def OnPaint(self, event=None):
        self._canvas.delete('all')
        w, h = self._canvas.winfo_width(), self._canvas.winfo_height()
        self._canvas.create_rectangle(2, 2, max(3, w - 2), max(3, h - 2),
                                      outline=self._border, width=4)


class AuiFloatingFrame(tk.Toplevel):
    def __init__(self, parent, owner_mgr, pane=None, id=-1, title='', style=None):
        super().__init__(parent)
        self.attributes('-topmost', False)
        self.title(title or (pane.caption if pane else ''))
        self._owner_mgr = owner_mgr
        self._pane = pane
        self._flyTimer = None
        self._checkFlyTimer = None
        if pane:
            self.SetPaneWindow(pane)

    def CopyAttributes(self, pane):
        pass

    def SetPaneWindow(self, pane):
        self._pane = pane
        pane.frame = self
        window = pane.window
        if window is not None and hasattr(window, 'pack_forget'):
            window.pack_forget()
        # Tkinter ne permet pas de re-parenter un widget existant vers un
        # nouveau Toplevel : le cadre flottant affiche uniquement son titre
        # pour l'instant. A affiner ulterieurement (par exemple via "wm manage").
        if pane.floating_pos[0] >= 0:
            self.geometry('+%d+%d' % (pane.floating_pos[0], pane.floating_pos[1]))
        if pane.floating_size[0] > 0:
            self.geometry('%dx%d' % (pane.floating_size[0], pane.floating_size[1]))
        self.protocol('WM_DELETE_WINDOW', lambda: self.OnClose(None))

    def GetOwnerManager(self):
        return self._owner_mgr

    def OnSize(self, event):
        pass

    def OnClose(self, event):
        mgr = self.GetOwnerManager()
        if mgr:
            mgr.OnFloatingPaneClosed(self, event)
        self.destroy()

    def OnActivate(self, event):
        pass

    def OnMove(self, event):
        pass

    def OnMoveEvent(self, event):
        pass

    def OnIdle(self, event):
        pass

    def OnMoveStart(self, event):
        pass

    def OnMoving(self, rect, direction):
        pass

    def OnMoveFinished(self):
        pass

    def OnCheckFlyTimer(self, event=None):
        pass

    def OnFindManager(self, event):
        pass

    def FlyOut(self):
        pass

    def OnFlyTimer(self, event=None):
        pass

    def FadeOut(self):
        self.destroy()


NonePaneInfo = AuiPaneInfo()


class AuiManager:
    def __init__(self, managed_window=None, agwFlags=None):
        self._action = actionNone
        self._action_window = None
        self._hover_button = None
        self._art = AuiDefaultDockArt()
        self._hint_window = None
        self._active_pane = None
        self._has_maximized = False
        self._has_minimized = False
        self._frame = None
        self._dock_constraint_x = 0.3
        self._dock_constraint_y = 0.3
        self._reserved = None
        self._panes = []
        self._docks = []
        self._uiparts = []
        self._guides = []
        self._notebooks = []
        self._masterManager = None
        self._currentDragItem = -1
        self._lastknowndocks = {}
        self._hint_fadetimer = None
        self._hint_fademax = 50
        self._last_hint = (0, 0, 0, 0)
        self._from_move = False
        self._last_rect = (0, 0, 0, 0)
        self._agwFlags = AUI_MGR_DEFAULT if agwFlags is None else agwFlags
        self._is_docked = (False, AUI_DOCK_RIGHT, AUI_DOCK_TOP, 0)
        self._snap_limits = (15, 15)
        self._animation_step = 30.0
        self._hint_rect = (0, 0, 0, 0)
        self._preview_timer = None
        self._sliding_frame = None
        self._autoNBTabArt = None
        self._autoNBStyle = AUI_NB_DEFAULT_STYLE
        self._updating = False
        if managed_window:
            self.SetManagedWindow(managed_window)

    # -- basic accessors --------------------------------------------------
    def GetArtProvider(self):
        return self._art

    def SetArtProvider(self, art):
        self._art = art

    def GetAGWFlags(self):
        return self._agwFlags

    def SetAGWFlags(self, flags):
        self._agwFlags = flags
        if self._frame and not (self._agwFlags & AUI_MGR_ALLOW_FLOATING):
            for p in self._panes:
                if p.IsFloating() and p.IsToolbar():
                    p.Dock()

    def GetManagedWindow(self):
        return self._frame

    def SetManagedWindow(self, managed_window):
        if not managed_window:
            raise Exception('Specified managed window must be non-null. ')
        self.UnInit()
        self._frame = managed_window
        if isinstance(managed_window, tk.Misc):
            managed_window.bind('<Destroy>', lambda e: self.OnDestroy(), add='+')
        self._canvas = None
        return True

    def GetFrame(self):
        return self._frame

    def SetFrame(self, frame):
        self._frame = frame

    # -- pane lookup ------------------------------------------------------
    def GetPaneByWidget(self, window):
        return next((p for p in self._panes if p.window == window), NonePaneInfo)

    def GetPaneByName(self, name):
        return next((p for p in self._panes if p.name == name), NonePaneInfo)

    def GetPane(self, item):
        if isinstance(item, str):
            return self.GetPaneByName(item)
        return self.GetPaneByWidget(item)

    def GetAllPanes(self):
        return self._panes

    # -- add/insert -------------------------------------------------------
    def AddPane(self, window, arg1=None, arg2=None, target=None):
        if isinstance(arg1, int):
            return self.AddPane2(window, arg1, arg2 or '')
        if target is not None:
            return self.AddPane4(window, arg1, target)
        return self.AddPane1(window, arg1)

    def AddPane1(self, window, pane_info=None):
        p = pane_info or AuiPaneInfo()
        if not p.window:
            p.window = window
        if not p.name:
            # nom derive de la legende (recherche par nom possible), sinon compteur
            base = p.caption.strip() or 'pane'
            candidate = base
            index = 0
            while any(x.name == candidate for x in self._panes):
                index += 1
                candidate = '%s_%d' % (base, index)
            p.name = candidate
        self._panes.append(p)
        self.Update()
        return p

    def AddPane2(self, window, direction=AUI_DOCK_LEFT, caption=''):
        p = AuiPaneInfo().Window(window).Caption(caption).Direction(direction)
        p.DefaultPane()
        return self.AddPane1(window, p)

    def AddPane3(self, window, direction=AUI_DOCK_LEFT, pos=(0, 0)):
        p = self.AddPane2(window, direction, '')
        p.floating_pos = pos
        return p

    def AddPane4(self, window, pane_info, target):
        p = self.AddPane1(window, pane_info)
        p.notebook_id = 0 if target else -1
        return p

    def InsertPane(self, window, pane_info, direction=AUI_DOCK_LEFT):
        p = pane_info or AuiPaneInfo()
        if not p.window:
            p.window = window
        if not p.name:
            base = p.caption.strip() or 'pane'
            candidate = base
            index = 0
            while any(x.name == candidate for x in self._panes):
                index += 1
                candidate = '%s_%d' % (base, index)
            p.name = candidate
        self._panes.insert(0, p)
        self.Update()
        return p

    def DetachPane(self, window):
        p = self.GetPane(window)
        if p.IsOk():
            self._panes.remove(p)
            p.window = None
            self.Update()

    def ClosePane(self, pane):
        if pane.frame:
            pane.frame.destroy()
            pane.frame = None
        if pane.window and pane.IsDestroyOnClose():
            if hasattr(pane.window, 'destroy'):
                pane.window.destroy()
        self.DetachPane(pane.window)

    # -- pane state -------------------------------------------------------
    def ShowPane(self, window, show=True):
        p = self.GetPane(window)
        if p.IsOk():
            p.Show(show)
            self.Update()

    def MaximizePane(self, panes):
        for p in self._panes:
            p.SetFlag(AuiPaneInfo.optionHidden, p is not panes)
        self.Update()

    def RestorePane(self, pane):
        pane.Show()
        self.Update()

    def RestoreMaximizedPane(self):
        self.MaximizePane(None)

    def ActivatePane(self, pane):
        self._active_pane = pane

    # -- notebooks ---------------------------------------------------------
    def CreateNotebook(self):
        from .tkauibook import AuiNotebook
        nb = AuiNotebook(self._frame)
        self._notebooks.append(nb)
        return nb

    def SetAutoNotebookTabArt(self, art):
        self._autoNBTabArt = art

    def GetAutoNotebookTabArt(self):
        return self._autoNBTabArt

    def SetAutoNotebookStyle(self, style):
        self._autoNBStyle = style

    def GetAutoNotebookStyle(self):
        return self._autoNBStyle

    def GetNotebooks(self):
        return self._notebooks

    def SetMasterManager(self, mgr):
        self._masterManager = mgr

    def UpdateNotebook(self, notebook=None):
        for nb in self._notebooks:
            if hasattr(nb, 'DoSizing'):
                nb.DoSizing()

    # -- serialization ------------------------------------------------------
    def SavePaneInfo(self, pane):
        d = {'name': pane.name, 'caption': pane.caption, 'state': pane.state,
             'dir': pane.dock_direction, 'layer': pane.dock_layer,
             'row': pane.dock_row, 'pos': pane.dock_pos,
             'prop': pane.dock_proportion, 'best': list(pane.best_size),
             'min': list(pane.min_size), 'max': list(pane.max_size),
             'floatpos': list(pane.floating_pos),
             'floatsize': list(pane.floating_size),
             'notebookid': pane.notebook_id, 'transparent': pane.transparent}
        return json.dumps(d)

    def LoadPaneInfo(self, pane_part, pane):
        try:
            d = json.loads(pane_part)
        except ValueError:
            return pane
        pane.name = d.get('name', pane.name)
        pane.caption = d.get('caption', pane.caption)
        pane.state = d.get('state', pane.state)
        pane.dock_direction = d.get('dir', pane.dock_direction)
        pane.dock_layer = d.get('layer', pane.dock_layer)
        pane.dock_row = d.get('row', pane.dock_row)
        pane.dock_pos = d.get('pos', pane.dock_pos)
        pane.dock_proportion = d.get('prop', pane.dock_proportion)
        pane.best_size = tuple(d.get('best', pane.best_size))
        pane.min_size = tuple(d.get('min', pane.min_size))
        pane.max_size = tuple(d.get('max', pane.max_size))
        pane.floating_pos = tuple(d.get('floatpos', pane.floating_pos))
        pane.floating_size = tuple(d.get('floatsize', pane.floating_size))
        pane.notebook_id = d.get('notebookid', pane.notebook_id)
        pane.transparent = d.get('transparent', pane.transparent)
        return pane

    def SavePerspective(self):
        return json.dumps({'panes': [json.loads(self.SavePaneInfo(p)) for p in self._panes]})

    def LoadPerspective(self, layout):
        try:
            d = json.loads(layout)
        except ValueError:
            return False
        for pd in d.get('panes', []):
            p = AuiPaneInfo()
            self.LoadPaneInfo(json.dumps(pd), p)
            p.window = None
            self._panes.append(p)
        self.Update()
        return True

    # -- layout / update -----------------------------------------------------
    def LayoutAll(self):
        pass

    def Update(self):
        if getattr(self, '_updating', False):
            return
        self._updating = True
        try:
            for p in self._panes:
                w = p.window
                if w is None:
                    continue
                if p.IsFloating():
                    if p.frame is None and self._frame is not None:
                        p.frame = AuiFloatingFrame(self._frame, self, p)
                else:
                    if p.frame is not None:
                        frame = p.frame
                        p.frame = None
                        if hasattr(frame, 'destroy'):
                            frame.destroy()
                    if isinstance(w, tk.Misc):
                        cap = getattr(w, '_aui_caption', None)
                        if p.IsShown():
                            w.pack_forget()
                            if cap is not None:
                                cap.pack_forget()
                            side = {AUI_DOCK_TOP: 'top',
                                    AUI_DOCK_BOTTOM: 'bottom',
                                    AUI_DOCK_LEFT: 'left',
                                    AUI_DOCK_RIGHT: 'right'}.get(p.dock_direction, 'top')
                            if p.HasCaption():
                                if cap is None:
                                    cap = tk.Frame(w.master)
                                    tk.Label(cap, text=p.caption).pack(side='left', padx=4)
                                    w._aui_caption = cap
                                cap.pack(side=side, fill='x')
                            w.pack(side=side, fill='both', expand=not p.IsToolbar())
                        else:
                            w.pack_forget()
                            if cap is not None:
                                cap.pack_forget()
        finally:
            self._updating = False
        self.Render()

    def DoUpdateEvt(self, event=None):
        self.Update()

    def DoUpdate(self):
        self.Update()

    def UpdateHintWindowSize(self):
        pass

    # -- docks -----------------------------------------------------------------
    def SetDockSizeConstraint(self, x, y):
        self._dock_constraint_x = x
        self._dock_constraint_y = y

    def GetDockSizeConstraint(self):
        return self._dock_constraint_x, self._dock_constraint_y

    def HitTest(self, x, y):
        return None

    def PaneHitTest(self, x, y):
        return None

    # -- events ------------------------------------------------------------------
    def ProcessMgrEvent(self, evt):
        pass

    def FireEvent(self, evt_type, pane=None, can_veto=True):
        evt = AuiManagerEvent(self, pane)
        evt.SetCanVeto(can_veto)
        return evt

    def OnClose(self, event=None):
        for p in list(self._panes):
            if p.frame:
                p.frame.destroy()
        self.UnInit()
        if hasattr(event, 'Skip'):
            event.Skip()

    def OnDestroy(self):
        self.UnInit()

    def UnInit(self):
        for p in self._panes:
            if p.frame:
                p.frame.destroy()
                p.frame = None
        self._panes.clear()
        self._docks.clear()
        self._uiparts.clear()

    def OnFloatingPaneResized(self, pane, event=None):
        self.Update()

    def OnFloatingPaneClosed(self, pane, event=None):
        return True

    def OnFloatingPaneActivated(self, pane, event=None):
        self.ActivatePane(self.GetPane(pane))

    def OnFloatingPaneMoved(self, pane, event=None):
        pass

    # -- render --------------------------------------------------------------------
    def GetPanePart(self, pane):
        return None

    def OnRender(self, event=None):
        self.Render()
        return True

    def Repaint(self):
        self.Render()

    def Render(self, dc=None):
        pass

    def OnPaint(self, event=None):
        pass

    def OnEraseBackground(self, event):
        pass

    def OnSize(self, event=None):
        self.Update()

    def OnSetCursor(self, event=None):
        pass

    def OnLeftDown(self, event=None):
        pass

    def OnLeftDClick(self, event=None):
        pass

    def OnLeftUp(self, event=None):
        pass

    def OnMotion(self, event=None):
        pass

    def OnLeaveWindow(self, event=None):
        pass

    def OnChildFocus(self, event=None):
        pass

    def OnCaptureLost(self, event=None):
        pass

    def OnHintFadeTimer(self, event=None):
        pass

    def OnMove(self, event=None):
        pass

    def OnSysColourChanged(self, event=None):
        pass

    def OnFindManager(self, event=None):
        pass

    def OnTabBeginDrag(self, event=None):
        pass

    def OnTabEndDrag(self, event=None):
        pass

    def OnTabPageClose(self, event=None):
        pass

    def OnTabSelected(self, event=None):
        pass

    def OnPaneButton(self, event=None):
        pass

    def OnPaneDocked(self, event=None):
        pass

    def OnRestoreMinimizedPane(self, event=None):
        pass

    def OnGripperClicked(self, event=None):
        pass

    def OnCaptionDoubleClicked(self, event=None):
        pass

    def CanDockPanel(self, pane):
        return False

    def CreateFloatingFrame(self, pane):
        if self._frame is None:
            return None
        return AuiFloatingFrame(self._frame, self, pane)

    def CreateGuideWindows(self):
        pass

    def DestroyGuideWindows(self):
        pass

    def CreateHintWindow(self):
        pass

    def DestroyHintWindow(self):
        pass

    def ShowHint(self, rect):
        return False

    def HideHint(self):
        pass

    def SnapPane(self, pane):
        pass

    def RepositionPane(self, pane, move_pane):
        pass

    def MinimizePane(self, pane):
        pass

    def RestoreMinimizedPane(self, pane):
        pass

    def AnimateDocking(self, pane):
        return False

    def SmoothDock(self, pane):
        return False

    def SetSnapLimits(self, limit):
        self._snap_limits = limit

    def Snap(self, pane):
        return False

    def SnapToScreen(self, pane):
        return False

    def GetSnapPosition(self, pane):
        return None

    def GetAnimationStep(self):
        return self._animation_step

    def SetAnimationStep(self, step):
        self._animation_step = step

    def RequestUserAttention(self, pane):
        pass

    def StartPreviewTimer(self):
        pass

    def StopPreviewTimer(self):
        pass

    def SlideIn(self, event=None):
        pass

    def SlideOut(self):
        pass

    def SavePreviousDockSizes(self):
        pass

    def CopyTarget(self, target, newPos):
        return target

    def DoDrop(self, target, pane, pt, offset):
        return False

    def DoDropToolbar(self, target, pane, pt, offset):
        return False

    def DoDropFloatingPane(self, target, pane, pt):
        return False

    def DoDropNonFloatingPane(self, target, pane, pt, offset):
        return False

    def DoDropLayer(self, target, pane, pt, offset):
        return False

    def DoDropPane(self, target, pane, pt, offset):
        return False

    def DoDropRow(self, target, pane, pt, offset):
        return False

    def SwitchToolBarOrientation(self, toolbar):
        pass

    def GetPanePositionsAndSizes(self):
        return []

    def LayoutAddPane(self, dc, pane, uiparts, after):
        pass

    def LayoutAddDock(self, dc, dock, uiparts, after):
        pass

    def DoFrameLayout(self):
        pass

    def GetDockPixelOffset(self, target):
        return 0

    def GetPartnerDock(self, target):
        return None

    def GetPartnerPane(self, target, pane):
        return None

    def GetTotalPixSizeAndProportion(self, panes, total):
        return total

    def GetOppositeDockTotalSize(self, target):
        return 0

    def CalculateDockSizerLimits(self, target):
        return 0

    def CalculatePaneSizerLimits(self, target, pane):
        return 0

    def CheckMovableSizer(self):
        return False

    def PaneFromTabEvent(self, event):
        return None

    def ProcessDockResult(self, target, pane):
        return False

    def IsPaneButtonVisible(self, pane, button_id):
        return False

    def DrawPaneButton(self, dc, pane, button, event):
        pass

    def RefreshButton(self, pane, button):
        pass

    def RefreshCaptions(self):
        pass

    def CalculateHintRect(self, pane, screenPt, offset):
        return (0, 0, 0, 0)

    def DrawHintRect(self, dc, pane, screenPt, offset):
        pass

    def GetPartSizerRect(self, uipart):
        return (0, 0, 0, 0)

    def GetAttributes(self):
        return {}

    def SetAttributes(self, attrs):
        pass


class AuiManager_DCP(AuiManager):
    """Gestionnaire AUI avec panneau central factice (Dummy Center Pane)."""

    def __init__(self, *args, **keys):
        super().__init__(*args, **keys)
        self.hasDummyPane = False

    def _createDummyPane(self):
        if self.hasDummyPane:
            return
        if self.GetManagedWindow() is None:
            # sans fenetre geree, aucun panneau factice ne peut etre cree
            return
        self.hasDummyPane = True
        dummy = tk.Frame(self.GetManagedWindow())
        info = AuiPaneInfo().CenterPane().NotebookDockable(True)
        info.Name('dummyCenterPane').DestroyOnClose(True)
        self.AddPane(dummy, info)

    def _destroyDummyPane(self):
        if not self.hasDummyPane:
            return
        self.hasDummyPane = False
        self.ClosePane(self.GetPane('dummyCenterPane'))

    def Update(self):
        super().Update()
        dummy = self.GetPane('dummyCenterPane')
        haveCenterPane = any(
            (p is not dummy) and p.dock_direction == AUI_DOCK_CENTER
            and not p.IsFloating() and p.IsShown()
            for p in self.GetAllPanes())
        if haveCenterPane:
            if self.hasDummyPane:
                def do():
                    self._destroyDummyPane()
                    super(AuiManager_DCP, self).Update()
                if self._frame:
                    self._frame.after_idle(do)
                else:
                    do()
        else:
            if not self.hasDummyPane:
                def do():
                    self._createDummyPane()
                    super(AuiManager_DCP, self).Update()
                if self._frame:
                    self._frame.after_idle(do)
                else:
                    do()
