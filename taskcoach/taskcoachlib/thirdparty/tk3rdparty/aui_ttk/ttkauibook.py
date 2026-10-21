# -*- coding: utf-8 -*-
"""Version ttk d'AuiNotebook, inspirée de tkauibook.py et de wx.lib.agw.aui.auibook.

Cette première adaptation délègue l'affichage des onglets à ttk.Notebook.
Les comportements AUI avancés (déplacement entre groupes, flottement et
boutons personnalisés) restent à implémenter dans les étapes suivantes.
"""
# J’ai créé ttkauibook.py avec ttk.Notebook comme base,
# en reprenant l’API de tkauibook.py et les conventions générales d’AuiNotebook
# de wxPython. Le fichier passe la vérification de syntaxe Python.
#
# Cette première version couvre les opérations de base sur les pages
# et la sélection. Le glisser-déposer entre onglets est amorcé ;
# le flottement, le fractionnement des onglets et les boutons personnalisés
# restent à adapter. Le fichier est prêt à être ajouté au dossier du projet ;
# il n’a pas été écrit directement dans le dépôt.

# Modifications effectuées :
#
# conservation de ttk.Notebook comme contrôle principal ;
# suppression de l’utilisation incorrecte de l’option tooltip de ttk.Notebook ;
# conservation des infobulles dans AuiNotebookPage, accessibles via GetPageTooltip() ;
# ajout d’un helper _hide_ttk_page() pour gérer le masquage des pages ;
# ajout d’un repli pour les versions de Tk ne proposant pas ttk.Notebook.hide() ;
# nouvelle vérification de syntaxe réussie ;
# vérification de la présence des classes TabFrame et AuiNotebook.

import json
import tkinter as tk
from tkinter import ttk

from .tkauibook_aux import AuiNotebookPage, AuiNotebookEvent
from .aui_tk_constants import *


class TabFrame(ttk.Frame):
    """Conteneur de compatibilité pour les panneaux de pages."""

    def __init__(self, parent):
        super().__init__(parent)
        self._tabs = None
        self._rect = (0, 0, 200, 200)
        self._tab_ctrl_height = 20
        self._tab_rect = (0, 0, 0, 0)
        self._parent = parent

    def SetTabCtrlHeight(self, height):
        self._tab_ctrl_height = height

    def DoSetSize(self, x, y, width, height, flags=None):
        self.place(x=x, y=y, width=width, height=height)

    def DoGetSize(self):
        return self.winfo_width(), self.winfo_height()

    def DoGetClientSize(self):
        return self.DoGetSize()

    def Show(self, show=True):
        if show:
            self.place()
        else:
            self.place_forget()

    def DoSizing(self):
        pass

    def Update(self):
        self.update_idletasks()


class AuiNotebook(ttk.Frame):
    """Notebook compatible avec une partie de l'API AuiNotebook.

    Les méthodes de gestion de pages et de sélection sont fournies ici avec
    ttk.Notebook. Les arguments wx historiques sont acceptés quand cela est
    sans ambiguïté, mais l'habillage artistique des onglets est géré par ttk.
    """

    def __init__(self, parent, id=-1, pos=None, size=None, style=None,
                 agwStyle=AUI_NB_DEFAULT_STYLE, name="auinotebook", **kwargs):
        # ttk.Frame ne prend pas le paramètre Tcl 'name' de tk.Frame.
        super().__init__(parent, **kwargs)
        self._auiStyle = agwStyle
        self._art = None
        self._pages = []
        self._selection = -1
        self._imageList = None
        self._minTabWidth = -1
        self._maxTabWidth = -1
        self._tab_ctrl_height = 20
        self._textCtrl = None
        self._sashDClickUnsplit = False
        self._manager = None
        self._navigatorIcon = None
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)
        self._notebook.bind("<<NotebookTabChanged>>", self._OnTtkTabChanged)
        self._notebook.bind("<Button-1>", self._OnTabPress, add="+")
        self._notebook.bind("<ButtonRelease-1>", self._OnTabRelease, add="+")
        self._drag_index = None
        if pos is not None:
            try:
                self.place(x=pos[0], y=pos[1])
            except (TypeError, IndexError):
                pass
        if size is not None:
            try:
                self.configure(width=size[0], height=size[1])
            except (TypeError, IndexError, tk.TclError):
                pass

    def _OnTtkTabChanged(self, event=None):
        try:
            widget = self._notebook.nametowidget(self._notebook.select())
            index = self.GetPageIndex(widget)
        except (KeyError, tk.TclError):
            return
        if index >= 0:
            self._selection = index
            for i, page in enumerate(self._pages):
                page.active = (i == index)

    def _OnTabPress(self, event):
        try:
            self._drag_index = self._notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            self._drag_index = None

    def _OnTabRelease(self, event):
        if self._drag_index is None:
            return
        try:
            target = self._notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            self._drag_index = None
            return
        source = self._drag_index
        self._drag_index = None
        if source != target and 0 <= source < len(self._pages) and 0 <= target < len(self._pages):
            self.ReorderPage(source, target)

    def ReorderPage(self, source, target):
        """Réordonne un onglet par l'API native ttk."""
        if not (0 <= source < len(self._pages) and 0 <= target < len(self._pages)):
            return False
        page = self._pages.pop(source)
        self._pages.insert(target, page)
        self._notebook.insert(target, page.window)
        self._selection = self.GetPageIndex(self._notebook.nametowidget(self._notebook.select())) if self._notebook.select() else -1
        return True

    def Destroy(self):
        self.destroy()

    def __getitem__(self, index):
        return self._pages[index].window

    def GetTabContainer(self):
        return self._notebook

    def InitNotebook(self, agwStyle):
        self.SetAGWWindowStyleFlag(agwStyle)

    def SetArtProvider(self, art):
        # ttk gère le dessin des onglets via son thème et ses styles.
        self._art = art

    def GetArtProvider(self):
        return self._art

    def SavePerspective(self):
        return json.dumps({"selection": self.GetSelection(), "pages": [p.caption for p in self._pages]})

    def LoadPerspective(self, layout):
        try:
            data = json.loads(layout)
            selection = data.get("selection", -1)
            if 0 <= selection < len(self._pages):
                self.SetSelection(selection)
            return True
        except (TypeError, ValueError, tk.TclError):
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

    def GetAGWWindowStyleFlag(self):
        return self._auiStyle

    def AddPage(self, page, caption, select=False, bitmap=None,
                disabled_bitmap=None, control=None, tooltip=""):
        return self.InsertPage(len(self._pages), page, caption, select,
                               bitmap, disabled_bitmap, control, tooltip)

    def InsertPage(self, page_idx, page, caption, select=False, bitmap=None,
                   disabled_bitmap=None, control=None, tooltip=""):
        if page is None or not isinstance(page, tk.Widget):
            raise TypeError("page doit être un widget Tkinter/ttk")
        if page.winfo_parent() != str(self._notebook):
            raise ValueError("Avec ttk.Notebook, chaque page doit avoir le notebook comme parent")
        page_idx = max(0, min(int(page_idx), len(self._pages)))
        info = AuiNotebookPage()
        info.window = page
        info.caption = caption
        info.bitmap = bitmap
        info.dis_bitmap = disabled_bitmap
        info.control = control or page
        info.tooltip = tooltip
        self._pages.insert(page_idx, info)
        self._notebook.insert(page_idx, page, text=caption)
        # ttk.Notebook ne fournit pas de tooltip natif. La valeur reste
        # disponible via GetPageTooltip, comme dans l'API AUI.
        if not getattr(info, "enabled", True):
            self._notebook.tab(page, state="disabled")
        if getattr(info, "hidden", False):
            self._notebook.hide(page)
        if select or self._selection < 0:
            self.SetSelection(page_idx)
        else:
            self._selection = self.GetSelection()
        return True

    def DeletePage(self, page_idx):
        return self.RemovePage(page_idx)

    def RemovePage(self, page_idx):
        if not 0 <= page_idx < len(self._pages):
            return False
        info = self._pages.pop(page_idx)
        try:
            self._notebook.forget(info.window)
        except tk.TclError:
            pass
        if self._pages:
            self.SetSelection(min(page_idx, len(self._pages) - 1))
        else:
            self._selection = -1
        return True

    def _hide_ttk_page(self, page):
        """Masque une page avec l'API disponible dans la version de Tk."""
        try:
            self._notebook.hide(page.window)
        except tk.TclError:
            # Repli pour les versions anciennes de Tk sans ttk::notebook hide.
            self._notebook.forget(page.window)

    def HidePage(self, page_idx, hidden=True):
        if not 0 <= page_idx < len(self._pages):
            return False
        page = self._pages[page_idx]
        page.hidden = bool(hidden)
        if hidden:
            self._hide_ttk_page(page)
            if page_idx == self._selection:
                self._selection = self.GetSelection()
        else:
            self._notebook.add(page.window, text=page.caption)
            self._notebook.insert(page_idx, page.window)
            if page_idx == self._selection:
                self.SetSelection(page_idx)
        return True

    def FindNextActiveTab(self, idx):
        if not self._pages:
            return -1
        for offset in range(1, len(self._pages) + 1):
            candidate = (idx + offset) % len(self._pages)
            if not self._pages[candidate].hidden and self._pages[candidate].enabled:
                return candidate
        return -1

    def HideAllTabs(self, hidden=True):
        for i in range(len(self._pages)):
            self.HidePage(i, hidden)

    def SetSashDClickUnsplit(self, unsplit):
        self._sashDClickUnsplit = bool(unsplit)

    def GetSashDClickUnsplit(self):
        return self._sashDClickUnsplit

    def SetMinMaxTabWidth(self, a, b):
        self._minTabWidth, self._maxTabWidth = a, b

    def GetMinMaxTabWidth(self):
        return self._minTabWidth, self._maxTabWidth

    def GetPageIndex(self, page_wnd):
        return next((i for i, page in enumerate(self._pages) if page.window == page_wnd), -1)

    def SetPageText(self, i, text):
        self._pages[i].caption = text
        self._notebook.tab(self._pages[i].window, text=text)

    def GetPageText(self, i):
        return self._pages[i].caption

    def SetPageBitmap(self, i, bitmap):
        self._pages[i].bitmap = bitmap

    def GetPageBitmap(self, i):
        return self._pages[i].bitmap

    def SetPageTooltip(self, i, tooltip):
        self._pages[i].tooltip = tooltip

    def GetPageTooltip(self, i):
        return self._pages[i].tooltip

    def SetImageList(self, image_list):
        self._imageList = image_list

    def AssignImageList(self, image_list):
        self._imageList = image_list

    def GetImageList(self):
        return self._imageList

    def SetPageImage(self, page, image):
        self._pages[page].bitmap = image

    def GetPageImage(self, page):
        return self._pages[page].bitmap

    def SetPageTextColour(self, i, colour):
        self._pages[i].text_colour = colour

    def GetPageTextColour(self, i):
        return self._pages[i].text_colour

    def AddControlToPage(self, i, control):
        self._pages[i].control = control

    def RemoveControlFromPage(self, i):
        self._pages[i].control = None

    def SetCloseButton(self, i, value):
        self._pages[i].hasCloseButton = bool(value)

    def HasCloseButton(self, i):
        return getattr(self._pages[i], "hasCloseButton", True)

    def GetSelection(self):
        if not self._pages:
            return -1
        try:
            selected = self._notebook.select()
            if selected:
                widget = self._notebook.nametowidget(selected)
                index = self.GetPageIndex(widget)
                if index >= 0:
                    self._selection = index
        except tk.TclError:
            pass
        return self._selection

    def GetCurrentPage(self):
        selection = self.GetSelection()
        return self._pages[selection].window if selection >= 0 else None

    def EnsureVisible(self, indx):
        return 0 <= indx < len(self._pages)

    def SetSelection(self, new_page, force=False):
        if not 0 <= new_page < len(self._pages) or self._pages[new_page].hidden or not self._pages[new_page].enabled:
            return -1
        old = self.GetSelection()
        self._notebook.select(self._pages[new_page].window)
        self._selection = new_page
        for i, page in enumerate(self._pages):
            page.active = i == new_page
        return old

    def SetSelectionToWindow(self, window):
        return self.SetSelection(self.GetPageIndex(window))

    def SetSelectionToPage(self, page):
        return self.SetSelection(self.GetPageIndex(page))

    def GetPageCount(self):
        return len(self._pages)

    def GetShownPageCount(self):
        return sum(not page.hidden for page in self._pages)

    def GetPage(self, i):
        return self._pages[i].window

    def GetPageInfo(self, i):
        return self._pages[i]

    def GetEnabled(self, i):
        return self._pages[i].enabled

    def EnableTab(self, i, value=True):
        page = self._pages[i]
        page.enabled = bool(value)
        self._notebook.tab(page.window, state="normal" if value else "disabled")

    def GetHidden(self, i):
        return self._pages[i].hidden

    def DoSizing(self):
        pass

    def GetAuiManager(self):
        return self._manager

    def GetActiveTabCtrl(self):
        return self._notebook

    def FindTab(self, page):
        return self._notebook

    def Split(self, page, direction):
        return False

    def UnSplit(self):
        return False

    def ReparentControl(self, control, dest_tabs):
        return False

    def UnsplitDClick(self, part, sash_size, pos):
        return False

    def OnSize(self, event=None):
        pass

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
        return self._notebook

    def GetTabFrameFromTabCtrl(self, tab_ctrl):
        return None

    def GetTabFrameFromWindow(self, wnd):
        return None

    def RemoveEmptyTabFrames(self):
        pass

    def OnChildFocusNotebook(self, event):
        pass

    def SetNavigatorIcon(self, bitmap):
        self._navigatorIcon = bitmap

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

    def SetNormalFont(self, font):
        self._normalFont = font

    def SetSelectedFont(self, font):
        self._selectedFont = font

    def SetMeasuringFont(self, font):
        self._measuringFont = font

    def SetFont(self, font):
        self.configure(style="TNotebook")

    def GetTabCtrlHeight(self):
        return self._tab_ctrl_height

    def GetHeightForPageHeight(self, pageHeight):
        return pageHeight + self._tab_ctrl_height

    def AdvanceSelection(self, forward, wrap=True):
        if not self._pages:
            return -1
        current = self.GetSelection()
        step = 1 if forward else -1
        for offset in range(1, len(self._pages) + 1):
            candidate = current + step * offset
            if wrap:
                candidate %= len(self._pages)
            elif not 0 <= candidate < len(self._pages):
                return current
            if not self._pages[candidate].hidden and self._pages[candidate].enabled:
                return self.SetSelection(candidate)
        return -1

    def ShowWindowMenu(self):
        return None

    def AddTabAreaButton(self, *args):
        return None

    def RemoveTabAreaButton(self, id):
        return False

    def CloneTabAreaButtons(self):
        return []

    def HasMultiplePages(self):
        return len(self._pages) > 1

    def GetDefaultBorder(self):
        return 1

    def NotebookPreview(self, thumbnail_size=200):
        return None

    def SetRenamable(self, i, value):
        self._pages[i].renamable = bool(value)

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


# Noms historiques gardés pour les imports qui attendent le module ttk.
TtkAuiNotebook = AuiNotebook
