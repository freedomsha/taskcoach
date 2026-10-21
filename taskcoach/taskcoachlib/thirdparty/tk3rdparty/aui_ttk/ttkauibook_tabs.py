# -*- coding: utf-8 -*-
"""Gestionnaire auxiliaire des onglets pour la version ttk d'AUI.

Le contrôle principal est ttk.Notebook. Cette classe conserve l'interface
attendue par les modules AUI existants, sans redessiner les onglets sur Canvas.
"""
import tkinter as tk
from tkinter import ttk

try:
    from .aui_tk_constants import *
except ImportError:
    from aui_tk_constants import *


class AuiTabContainer:
    """Couche de compatibilité autour de ttk.Notebook."""

    def __init__(self, auiNotebook):
        self._auiNotebook = auiNotebook
        self._agwFlags = 0
        self._art = None
        self._buttons = []
        self._pages = []
        self._tab_close_buttons = []
        self._tab_offset = 0
        self._rect = (0, 0, 1, 1)

    def SetArtProvider(self, art): self._art = art
    def GetArtProvider(self): return self._art
    def SetAGWFlags(self, flags): self._agwFlags = flags
    def GetAGWFlags(self): return self._agwFlags
    def SetNormalFont(self, font): self._normalFont = font
    def SetSelectedFont(self, font): self._selectedFont = font
    def SetMeasuringFont(self, font): self._measuringFont = font
    def SetTabRect(self, rect): self._rect = rect

    def AddPage(self, page, info):
        self._pages.append(info)
        self._tab_close_buttons.append(getattr(info, "hasCloseButton", True))
        return True

    def InsertPage(self, page, info, index):
        index = max(0, min(index, len(self._pages)))
        self._pages.insert(index, info)
        self._tab_close_buttons.insert(index, getattr(info, "hasCloseButton", True))
        return True

    def MovePage(self, page, new_index):
        old_index = self.GetIdxFromWindow(page)
        if old_index < 0 or not 0 <= new_index < len(self._pages):
            return False
        item = self._pages.pop(old_index)
        self._pages.insert(new_index, item)
        return True

    def RemovePage(self, window_or_index):
        index = window_or_index if isinstance(window_or_index, int) else self.GetIdxFromWindow(window_or_index)
        if not 0 <= index < len(self._pages):
            return False
        self._pages.pop(index)
        self._tab_close_buttons.pop(index)
        return True

    def SetActivePage(self, window_or_index):
        index = window_or_index if isinstance(window_or_index, int) else self.GetIdxFromWindow(window_or_index)
        for i, page in enumerate(self._pages):
            page.active = i == index

    def SetNoneActive(self):
        for page in self._pages: page.active = False

    def GetActivePage(self):
        return next((p for p in self._pages if getattr(p, "active", False)), None)
    def GetWindowFromIdx(self, index): return getattr(self._pages[index], "window", None) if 0 <= index < len(self._pages) else None
    def GetIdxFromWindow(self, window): return next((i for i, p in enumerate(self._pages) if getattr(p, "window", None) == window), -1)
    def GetPage(self, index): return self._pages[index] if 0 <= index < len(self._pages) else None
    def GetPages(self): return self._pages
    def GetPageCount(self): return len(self._pages)
    def GetShownPageCount(self): return sum(not getattr(p, "hidden", False) for p in self._pages)
    def GetHidden(self, index): return getattr(self.GetPage(index), "hidden", False)

    def HideTab(self, index, hidden=True):
        page = self.GetPage(index)
        if page is not None: page.hidden = bool(hidden)

    def GetEnabled(self, index): return getattr(self.GetPage(index), "enabled", False)

    def EnableTab(self, index, enable=True):
        page = self.GetPage(index)
        if page is not None: page.enabled = bool(enable)

    def FindNextActiveTab(self, index):
        if not self._pages: return -1
        for offset in range(1, len(self._pages) + 1):
            candidate = (index + offset) % len(self._pages)
            if not self.GetHidden(candidate) and self.GetEnabled(candidate): return candidate
        return -1

    def AddButton(self, button_id, location, normal_bitmap=None, disabled_bitmap=None, name=""):
        button = type("Button", (), {})()
        button.id = button_id; button.location = location; button.bitmap = normal_bitmap
        button.dis_bitmap = disabled_bitmap; button.name = name; button.rect = (0, 0, 0, 0)
        button.cur_state = AUI_BUTTON_STATE_NORMAL
        self._buttons.append(button)
        return button

    def CloneButtons(self): return list(self._buttons)
    def RemoveButton(self, button_id): self._buttons = [b for b in self._buttons if b.id != button_id]
    def GetTabOffset(self): return self._tab_offset
    def SetTabOffset(self, offset): self._tab_offset = offset
    def Render(self, raw_dc=None, wnd=None): return None
    def IsTabVisible(self, tab_page, tab_offset, dc=None, wnd=None): return not getattr(tab_page, "hidden", False)
    def MakeTabVisible(self, tab_page, win=None): return True
    def TabHitTest(self, x, y): return -1
    def ButtonHitTest(self, x, y, state_flags=0): return None

    def DoShowHide(self):
        for page in self._pages:
            window = getattr(page, "window", None)
            if window is None: continue
            try:
                if getattr(page, "hidden", False):
                    self._auiNotebook._notebook.hide(window)
                else:
                    self._auiNotebook._notebook.add(window, text=getattr(page, "caption", ""))
            except tk.TclError:
                pass


class AuiTabCtrl(ttk.Frame, AuiTabContainer):
    """Adaptateur ttk conservant le nom historique AuiTabCtrl."""

    def __init__(self, parent, id=-1, pos=None, size=None, style=None):
        ttk.Frame.__init__(self, parent)
        AuiTabContainer.__init__(self, parent)
        self._click_pt = (-1, -1)
        self._is_dragging = False
        self._hover_button = None
        self._pressed_button = None
        self._notebook = getattr(parent, "_notebook", None)
        if self._notebook is not None:
            self._notebook.bind("<Button-1>", self.OnLeftDown, add="+")
            self._notebook.bind("<ButtonRelease-1>", self.OnLeftUp, add="+")
            self._notebook.bind("<Motion>", self.OnMotion, add="+")

    def IsDragging(self): return self._is_dragging
    def GetDefaultBorder(self): return 1
    def OnPaint(self, event=None): return None
    def OnEraseBackground(self, event=None): pass
    def DoGetBestSize(self): return (400, 30)
    def OnSize(self, event=None): pass

    def OnLeftDown(self, event):
        self._click_pt = (event.x, event.y)
        self.focus_set()

    def OnCaptureLost(self, event=None): self._is_dragging = False

    def OnLeftUp(self, event):
        self._is_dragging = False

    def OnMiddleUp(self, event): pass
    def OnMiddleDown(self, event): pass
    def OnRightUp(self, event): pass
    def OnRightDown(self, event): pass
    def OnLeftDClick(self, event): pass
    def OnMotion(self, event): pass
    def GetPointedToTab(self): return self.TabHitTest(*self._click_pt)
    def RestartTooltipTimer(self, wnd): self.StopTooltipTimer()
    def StopTooltipTimer(self): pass
    def OnEnterWindow(self, event): pass
    def ShowTooltip(self): pass
    def OnLeaveWindow(self, event): self.StopTooltipTimer()
    def OnButton(self, event): pass
    def OnSetFocus(self, event): pass
    def OnKillFocus(self, event): pass

    def OnKeyDown(self, event):
        if event.keysym in ("Left", "Right") and self._auiNotebook is not None:
            self._auiNotebook.AdvanceSelection(event.keysym == "Right")
        return "break"

    def OnKeyDown2(self, event): return self.OnKeyDown(event)


def _inside(rect, x, y):
    a, b, c, d = (rect.x, rect.y, rect.width, rect.height) if hasattr(rect, "x") else rect
    return a <= x <= a + c and b <= y <= b + d
