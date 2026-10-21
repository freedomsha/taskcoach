# -*- coding: utf-8 -*-
"""Composants MDI AUI adaptés à ttk."""
import tkinter as tk
from tkinter import ttk

try:
    from .ttkauibook import AuiNotebook
    from .aui_tk_constants import *
except ImportError:
    from ttkauibook import AuiNotebook
    from aui_tk_constants import *


class AuiMDIParentFrame(tk.Toplevel):
    def __init__(self, parent=None, id=-1, title="", pos=None, size=None,
                 style=None, name="AuiMDIParentFrame"):
        super().__init__(parent)
        self.title(title)
        self._art = None
        self._window_menu = None
        self._active_child = None
        self._menu_bar = None
        self._child_menu_bar = None
        self._pClientWindow = self.OnCreateClient()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        if size and size[0] > 0 and size[1] > 0:
            self.geometry(f"{size[0]}x{size[1]}")
        if pos:
            self.geometry(f"+{pos[0]}+{pos[1]}")

    def Init(self):
        pass

    def SetArtProvider(self, art):
        self._art = art
        if hasattr(self._pClientWindow, "SetArtProvider"):
            self._pClientWindow.SetArtProvider(art)

    def GetArtProvider(self): return self._art
    def GetNotebook(self): return self._pClientWindow
    def SetWindowMenu(self, menu): self._window_menu = menu
    def GetWindowMenu(self): return self._window_menu
    def SetMenuBar(self, menu): self._menu_bar = menu
    def SetChildMenuBar(self, menu): self._child_menu_bar = menu
    def ProcessEvent(self, event): return False
    def GetActiveChild(self): return self._active_child

    def SetActiveChild(self, child):
        self._active_child = child
        if child is not None:
            child.Activate()

    def GetClientWindow(self): return self._pClientWindow
    def OnCreateClient(self): return AuiMDIClientWindow(self)

    def _activate_relative(self, step):
        count = self._pClientWindow.GetPageCount()
        if not count:
            return None
        current = self._pClientWindow.GetSelection()
        index = (current + step) % count
        self._pClientWindow.SetSelection(index)
        page = self._pClientWindow.GetPage(index)
        self.SetActiveChild(page)
        return page

    def ActivateNext(self): return self._activate_relative(1)
    def ActivatePrevious(self): return self._activate_relative(-1)
    def RemoveWindowMenu(self): self._window_menu = None
    def AddWindowMenu(self, window): return window
    def DoHandleMenu(self, event): return False

    def Tile(self):
        count = self._pClientWindow.GetPageCount()
        if not count:
            return
        for index in range(count):
            page = self._pClientWindow.GetPage(index)
            if hasattr(page, "grid"):
                page.grid(row=0, column=index, sticky="nsew")


class AuiMDIChildFrame(ttk.Frame):
    def __init__(self, parent, id=-1, title="", pos=None, size=None,
                 style=None, name="AuiMDIChildFrame"):
        self._parent = parent
        self._title = title
        self._icons = None
        self._icon = None
        self._maximized = False
        self._iconized = False
        self._fullscreen = False
        self._activate_on_create = True
        self._status_bar = None
        self._tool_bar = None
        super().__init__(parent.GetClientWindow())
        self.pack(fill="both", expand=True)
        parent.GetClientWindow().AddPage(self, title, True)
        parent.SetActiveChild(self)

    def Init(self): pass
    def Destroy(self): self.destroy()
    def SetMenuBar(self, menu): self._menu_bar = menu
    def GetMenuBar(self): return getattr(self, "_menu_bar", None)
    def SetTitle(self, title): self._title = title
    def GetTitle(self): return self._title
    def SetIcons(self, icons): self._icons = icons
    def GetIcons(self): return self._icons
    def SetIcon(self, icon): self._icon = icon
    def GetIcon(self): return self._icon

    def Activate(self):
        self.lift()
        self.focus_set()
        self._parent.GetClientWindow().SetSelectionToWindow(self)
        self._parent._active_child = self

    def OnMenuHighlight(self, event): pass
    def OnActivate(self, event): pass
    def OnCloseWindow(self, event=None): self.Destroy()
    def SetMDIParentFrame(self, parent): self._parent = parent
    def GetMDIParentFrame(self): return self._parent

    def CreateStatusBar(self, *args, **kwargs):
        self._status_bar = ttk.Label(self, text="")
        self._status_bar.pack(side="bottom", fill="x")
        return self._status_bar

    def GetStatusBar(self): return self._status_bar

    def SetStatusText(self, text, number=0):
        if self._status_bar is not None:
            self._status_bar.configure(text=text)

    def SetStatusWidths(self, widths): self._status_widths = widths
    def CreateToolBar(self, *args, **kwargs): return None
    def GetToolBar(self): return self._tool_bar
    def Maximize(self, flag=True): self._maximized = bool(flag)
    def Restore(self): self._maximized = False; self._iconized = False
    def Iconize(self, flag=True): self._iconized = bool(flag)
    def IsMaximized(self): return self._maximized
    def IsIconized(self): return self._iconized

    def ShowFullScreen(self, show, style=0):
        self._fullscreen = bool(show)
        self.winfo_toplevel().attributes("-fullscreen", self._fullscreen)
        return True

    def IsFullScreen(self): return self._fullscreen
    def IsTopLevel(self): return False
    def ActivateOnCreate(self, activate=True): self._activate_on_create = bool(activate)

    def Show(self, show=True):
        if show:
            self.pack(fill="both", expand=True)
        else:
            self.pack_forget()

    def ApplyMDIChildFrameRect(self, rect):
        self.place(x=rect[0], y=rect[1], width=rect[2], height=rect[3])


class AuiMDIClientWindow(AuiNotebook):
    def __init__(self, parent, agwStyle=0):
        super().__init__(parent, agwStyle=agwStyle | AUI_NB_DEFAULT_STYLE)
        self._mdi_parent = parent

    def SetSelection(self, selection, force=False):
        result = super().SetSelection(selection, force=force)
        return result

    def PageChanged(self, event=None): pass
    def OnPageClose(self, event=None): return True
    def OnPageChanged(self, event=None): self.PageChanged(event)
    def OnSize(self, event=None): super().OnSize(event)
