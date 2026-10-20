# -*- coding: utf-8 -*-
"""AuiNotebook Tkinter, conversion de TabFrame et AuiNotebook.

La dépendance au gestionnaire de fenêtres est volontairement nommée
``tkframemanager``. Ce module suppose donc que ce module existe déjà.
"""

import json
import tkinter as tk
from . import tkframemanager
from .tkauibook_tabs import AuiTabCtrl
from .tkauibook_aux import AuiNotebookPage, AuiNotebookEvent
from .tktabart import AuiDefaultTabArt
from .aui_tk_constants import *


class TabFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._tabs = None
        self._rect = (0, 0, 200, 200)
        self._tab_ctrl_height = 20
        self._tab_rect = (0, 0, 0, 0)
        self._parent = parent

    def SetTabCtrlHeight(self, h):
        self._tab_ctrl_height = h

    def DoSetSize(self, x, y, width, height, flags=None):
        self.place(x=x, y=y, width=width, height=height)

    def DoGetSize(self):
        return (self.winfo_width(), self.winfo_height())

    def DoGetClientSize(self):
        return self.DoGetSize()

    def Show(self, show=True):
        self.place_forget() if not show else self.place()

    def DoSizing(self):
        pass

    def Update(self):
        self.update_idletasks()


class AuiNotebook(tk.Frame):
    """"""
    def __init__(
        self,
        parent,
        id=-1,
        pos=None,
        size=None,
        style=None,
        agwStyle=AUI_NB_DEFAULT_STYLE,
        name="auinotebook",
    ):
        super().__init__(parent, name=name)
        self._auiStyle = agwStyle
        self._art = AuiDefaultTabArt()
        self._art.SetAGWFlags(agwStyle)
        self._pages = []
        self._selection = -1
        self._imageList = None
        self._minTabWidth = -1
        self._maxTabWidth = -1
        self._tab_ctrl_height = 20
        self._textCtrl = None
        self._sashDClickUnsplit = False
        self._manager = None
        self._tab_ctrl = AuiTabCtrl(self)
        self._tab_ctrl.pack(fill="x")
        self._page_area = tk.Frame(self)
        self._page_area.pack(fill="both", expand=True)
        self._tab_ctrl.bind("<Configure>", self.OnSize)

    def Destroy(self):
        self.destroy()

    def __getitem__(self, index):
        """"""
        # return self._pages[index]
        # semantique wx : notebook[i] renvoie la FENETRE de la i-eme page,
        # pas l'objet AuiNotebookPage (l'info reste accessible via GetPageInfo)
        page = self._pages[index]
        return getattr(page, "window", page)

    def GetTabContainer(self):
        return self._tab_ctrl

    def InitNotebook(self, agwStyle):
        self.SetAGWWindowStyleFlag(agwStyle)

    def SetArtProvider(self, art):
        self._art = art
        self._tab_ctrl.SetArtProvider(art)

    def GetArtProvider(self):
        return self._art

    def SavePerspective(self):
        return json.dumps(
            {"selection": self._selection, "pages": [p.caption for p in self._pages]}
        )

    def LoadPerspective(self, layout):
        try:
            self.SetSelection(json.loads(layout).get("selection", -1))
            return True
        except Exception:
            return False

    def SetTabCtrlHeight(self, height):
        self._tab_ctrl_height = height

    def SetUniformBitmapSize(self, size):
        self._uniformBitmapSize = size

    def UpdateTabCtrlHeight(self, force=False):
        pass

    def UpdateHintWindowSize(self):
        pass

    def CalculateNewSplitSize(self):
        return self.winfo_height()

    def CalculateTabCtrlHeight(self):
        return self._tab_ctrl_height

    def SetAGWWindowStyleFlag(self, agwStyle):
        self._auiStyle = agwStyle
        self._tab_ctrl.SetAGWFlags(agwStyle)

    def GetAGWWindowStyleFlag(self):
        return self._auiStyle

    def AddPage(
        self,
        page,
        caption,
        select=False,
        bitmap=None,
        disabled_bitmap=None,
        control=None,
        tooltip="",
    ):
        return self.InsertPage(
            len(self._pages),
            page,
            caption,
            select,
            bitmap,
            disabled_bitmap,
            control,
            tooltip,
        )

    def InsertPage(
        self,
        page_idx,
        page,
        caption,
        select=False,
        bitmap=None,
        disabled_bitmap=None,
        control=None,
        tooltip="",
    ):
        info = AuiNotebookPage()
        info.window = page
        info.caption = caption
        info.bitmap = bitmap
        info.dis_bitmap = disabled_bitmap
        info.control = control or page
        info.tooltip = tooltip
        self._pages.insert(page_idx, info)
        self._tab_ctrl.InsertPage(page, info, page_idx)
        page.pack_forget() if hasattr(page, "pack_forget") else None
        if select or self._selection < 0:
            self.SetSelection(page_idx)
        return True

    def DeletePage(self, page_idx):
        return self.RemovePage(page_idx)

    def RemovePage(self, page_idx):
        if not 0 <= page_idx < len(self._pages):
            return False
        p = self._pages.pop(page_idx)
        self._tab_ctrl.RemovePage(page_idx)
        if getattr(p, "window", None):
            p.window.pack_forget()
        if self._selection >= len(self._pages):
            self._selection = len(self._pages) - 1
        if self._selection >= 0:
            self.SetSelection(self._selection)
        return True

    def HidePage(self, page_idx, hidden=True):
        self._pages[page_idx].hidden = hidden
        self._tab_ctrl.HideTab(page_idx, hidden)
        return True

    def FindNextActiveTab(self, idx):
        return self._tab_ctrl.FindNextActiveTab(idx)

    def HideAllTabs(self, hidden=True):
        for i in range(len(self._pages)):
            self.HidePage(i, hidden)

    def SetSashDClickUnsplit(self, unsplit):
        self._sashDClickUnsplit = unsplit

    def GetSashDClickUnsplit(self):
        return self._sashDClickUnsplit

    def SetMinMaxTabWidth(self, a, b):
        self._minTabWidth = a
        self._maxTabWidth = b

    def GetMinMaxTabWidth(self):
        return self._minTabWidth, self._maxTabWidth

    def GetPageIndex(self, page_wnd):
        return next((i for i, p in enumerate(self._pages) if p.window == page_wnd), -1)

    def SetPageText(self, i, text):
        self._pages[i].caption = text
        self._tab_ctrl.OnPaint()

    def GetPageText(self, i):
        return self._pages[i].caption

    def SetPageBitmap(self, i, b):
        self._pages[i].bitmap = b

    def GetPageBitmap(self, i):
        return self._pages[i].bitmap

    def SetPageTooltip(self, i, t):
        self._pages[i].tooltip = t

    def GetPageTooltip(self, i):
        return self._pages[i].tooltip

    def SetImageList(self, l):
        self._imageList = l

    def AssignImageList(self, l):
        self._imageList = l

    def GetImageList(self):
        return self._imageList

    def SetPageImage(self, page, image):
        self._pages[page].bitmap = image

    def GetPageImage(self, page):
        return self._pages[page].bitmap

    def SetPageTextColour(self, i, c):
        self._pages[i].text_colour = c

    def GetPageTextColour(self, i):
        return self._pages[i].text_colour

    def AddControlToPage(self, i, c):
        self._pages[i].control = c

    def RemoveControlFromPage(self, i):
        self._pages[i].control = None

    def SetCloseButton(self, i, v):
        self._pages[i].hasCloseButton = v

    def HasCloseButton(self, i):
        return self._pages[i].hasCloseButton

    def GetSelection(self):
        return self._selection

    def GetCurrentPage(self):
        return self._pages[self._selection].window if self._selection >= 0 else None

    def EnsureVisible(self, indx):
        return True

    def SetSelection(self, new_page, force=False):
        if not 0 <= new_page < len(self._pages):
            return -1
        old = self._selection
        self._selection = new_page
        for i, p in enumerate(self._pages):
            p.active = i == new_page
        self._tab_ctrl.SetActivePage(new_page)
        for i, p in enumerate(self._pages):
            if p.window and hasattr(p.window, "pack"):
                (
                    p.window.pack(fill="both", expand=True)
                    if i == new_page and not p.hidden
                    else p.window.pack_forget()
                )
                # (p.window.pack if i==new_page and not p.hidden else p.window.pack_forget)(expand=True)
        return old

    def SetSelectionToWindow(self, w):
        return self.SetSelection(self.GetPageIndex(w))

    def SetSelectionToPage(self, p):
        return self.SetSelection(self.GetPageIndex(p))

    def GetPageCount(self):
        return len(self._pages)

    def GetShownPageCount(self):
        return sum(not p.hidden for p in self._pages)

    def GetPage(self, i):
        return self._pages[i].window

    def GetPageInfo(self, i):
        return self._pages[i]

    def GetEnabled(self, i):
        return self._pages[i].enabled

    def EnableTab(self, i, v=True):
        self._pages[i].enabled = v

    def GetHidden(self, i):
        return self._pages[i].hidden

    def DoSizing(self):
        pass

    def GetAuiManager(self):
        return self._manager

    def GetActiveTabCtrl(self):
        return self._tab_ctrl

    def FindTab(self, page):
        return self._tab_ctrl

    def Split(self, page, direction):
        return False

    def UnSplit(self):
        return False

    def ReparentControl(self, control, dest_tabs):
        return True

    def UnsplitDClick(self, part, sash_size, pos):
        return False

    def OnSize(self, event=None):
        self._tab_ctrl.OnPaint(event)

    def OnTabClicked(self, event):
        pass

    def OnTabBgDClick(self, event):
        pass

    def OnTabDClick(self, event):
        pass

    def OnTabBeginDrag(self, event):
        pass

    def OnTabDragMotion(self, event):
        pass

    def OnTabEndDrag(self, event):
        pass

    def OnTabCancelDrag(self, event):
        pass

    def IsMouseWellOutsideWindow(self):
        return False

    def FloatPage(self, page_index):
        return False

    def OnCloseFloatingPage(self, event):
        pass

    def ReDockPage(self, pane):
        return False

    def GetTabCtrlFromPoint(self, pt):
        return self._tab_ctrl

    def GetTabFrameFromTabCtrl(self, tab_ctrl):
        return None

    def GetTabFrameFromWindow(self, wnd):
        return None

    def RemoveEmptyTabFrames(self):
        pass

    def OnChildFocusNotebook(self, event):
        pass

    def SetNavigatorIcon(self, bmp):
        self._navigatorIcon = bmp

    def OnNavigationKeyNotebook(self, event):
        pass

    def OnTabButton(self, event):
        pass

    def OnTabMiddleDown(self, event):
        pass

    def OnTabMiddleUp(self, event):
        pass

    def OnTabRightDown(self, event):
        pass

    def OnTabRightUp(self, event):
        pass

    def SetNormalFont(self, f):
        self._art.SetNormalFont(f)

    def SetSelectedFont(self, f):
        self._art.SetSelectedFont(f)

    def SetMeasuringFont(self, f):
        self._art.SetMeasuringFont(f)

    def SetFont(self, f):
        self._art.SetNormalFont(f)

    def GetTabCtrlHeight(self):
        return self._tab_ctrl_height

    def GetHeightForPageHeight(self, pageHeight):
        return pageHeight + self._tab_ctrl_height

    def AdvanceSelection(self, forward, wrap=True):
        if not self._pages:
            return -1
        i = self._selection + (1 if forward else -1)
        i = i % len(self._pages) if wrap else max(0, min(len(self._pages) - 1, i))
        return self.SetSelection(i)

    def ShowWindowMenu(self):
        return None

    def AddTabAreaButton(self, *args):
        return self._tab_ctrl.AddButton(*args)

    def RemoveTabAreaButton(self, id):
        return self._tab_ctrl.RemoveButton(id)

    def CloneTabAreaButtons(self):
        return self._tab_ctrl.CloneButtons()

    def HasMultiplePages(self):
        return len(self._pages) > 1

    def GetDefaultBorder(self):
        return 1

    def NotebookPreview(self, thumbnail_size=200):
        return None

    def SetRenamable(self, i, v):
        self._pages[i].renamable = v

    def IsRenamable(self, i):
        return self._pages[i].renamable

    def OnRenameCancelled(self, page_index):
        pass

    def OnRenameAccept(self, page_index, value):
        return True

    def ResetTextControl(self):
        self._textCtrl = None

    def EditTab(self, page_index):
        return False
