# -*- coding: utf-8 -*-
"""Sélecteur d'onglets AUI adapté à Tkinter."""

import copy
import tkinter as tk
from tkinter import font as tkfont


class SwitcherItem:
    def __init__(self, item=None):
        self._id = 0
        self._isGroup = False
        self._breakColumn = False
        self._rowPos = 0
        self._colPos = 0
        self._window = None
        self._description = ""
        self._textColour = "#000000"
        self._bitmap = None
        self._font = None
        self._title = ""
        self._name = ""
        self._rect = (0, 0, 0, 0)
        if item:
            self.Copy(item)

    def Copy(self, item):
        self.__dict__.update(copy.copy(item.__dict__))
        return self

    def SetTitle(self, v):
        self._title = v
        return self

    def GetTitle(self):
        return self._title

    def SetName(self, v):
        self._name = v
        return self

    def GetName(self):
        return self._name

    def SetDescription(self, v):
        self._description = v
        return self

    def GetDescription(self):
        return self._description

    def SetId(self, v):
        self._id = v
        return self

    def GetId(self):
        return self._id

    def SetIsGroup(self, v):
        self._isGroup = v
        return self

    def GetIsGroup(self):
        return self._isGroup

    def BreakColumn(self, v=True):
        self._breakColumn = v
        return self

    def GetBreakColumn(self):
        return self._breakColumn

    def SetRect(self, v):
        self._rect = v
        return self

    def GetRect(self):
        return self._rect

    def SetTextColour(self, v):
        self._textColour = v
        return self

    def GetTextColour(self):
        return self._textColour

    def SetFont(self, v):
        self._font = v
        return self

    def GetFont(self):
        return self._font

    def SetBitmap(self, v):
        self._bitmap = v
        return self

    def GetBitmap(self):
        return self._bitmap

    def SetRowPos(self, v):
        self._rowPos = v
        return self

    def GetRowPos(self):
        return self._rowPos

    def SetColPos(self, v):
        self._colPos = v
        return self

    def GetColPos(self):
        return self._colPos

    def SetWindow(self, v):
        self._window = v
        return self

    def GetWindow(self):
        return self._window


class SwitcherItems:
    def __init__(self, items=None):
        self._selection = -1
        self._rowCount = 10
        self._columnCount = 0
        self._backgroundColour = "#ffffff"
        self._textColour = "#000000"
        self._selectionColour = "#c1d2ee"
        self._selectionOutlineColour = "#316ac5"
        self._itemFont = tkfont.Font(family="TkDefaultFont", size=9)
        self._items = []
        if items:
            self.Copy(items)

    def Copy(self, items):
        self._selection = items._selection
        self._rowCount = items._rowCount
        self._columnCount = items._columnCount
        self._items = [SwitcherItem(i) for i in items._items]
        return self

    def AddItem(self, titleOrItem, name="", id=0, bitmap=None):
        item = (
            SwitcherItem(titleOrItem)
            if isinstance(titleOrItem, SwitcherItem)
            else SwitcherItem()
            .SetTitle(titleOrItem)
            .SetName(name)
            .SetId(id)
            .SetBitmap(bitmap)
        )
        self._items.append(item)
        return item

    def AddGroup(self, title, name="", id=0, bitmap=None):
        return self.AddItem(title, name, id, bitmap).SetIsGroup(True)

    def Clear(self):
        self._items.clear()
        self._selection = -1

    def FindItemByName(self, name):
        return next((i for i in self._items if i.GetName() == name), None)

    def FindItemById(self, id):
        return next((i for i in self._items if i.GetId() == id), None)

    def SetSelection(self, sel):
        self._selection = sel

    def SetSelectionByName(self, name):
        self._selection = self._items.index(self.FindItemByName(name))

    def GetSelection(self):
        return self._selection

    def GetItem(self, i):
        return self._items[i]

    def GetItemCount(self):
        return len(self._items)

    def SetRowCount(self, v):
        self._rowCount = v

    def GetRowCount(self):
        return self._rowCount

    def SetColumnCount(self, v):
        self._columnCount = v

    def GetColumnCount(self):
        return self._columnCount

    def SetBackgroundColour(self, v):
        self._backgroundColour = v

    def GetBackgroundColour(self):
        return self._backgroundColour

    def SetTextColour(self, v):
        self._textColour = v

    def GetTextColour(self):
        return self._textColour

    def SetSelectionColour(self, v):
        self._selectionColour = v

    def GetSelectionColour(self):
        return self._selectionColour

    def SetSelectionOutlineColour(self, v):
        self._selectionOutlineColour = v

    def GetSelectionOutlineColour(self):
        return self._selectionOutlineColour

    def SetItemFont(self, v):
        self._itemFont = v

    def GetItemFont(self):
        return self._itemFont

    def PaintItems(self, dc, win):
        pass

    def CalculateItemSize(self, dc):
        return (180, 28)

    def GetIndexForFocus(self):
        return self._selection if self._selection >= 0 else 0


class MultiColumnListCtrl(tk.Canvas):
    def __init__(
        self,
        parent,
        aui_manager=None,
        id=-1,
        pos=None,
        size=None,
        style=None,
        validator=None,
        name="MultiColumnListCtrl",
    ):
        super().__init__(parent, highlightthickness=0)
        self._items = SwitcherItems()
        self._extraNavigationKey = None
        self._modifierKey = None
        self._transparency = 255
        self.bind("<Button-1>", self.OnMouseEvent)
        self.bind("<Key>", self.OnKey)

    def DoGetBestSize(self):
        return (400, 300)

    def OnEraseBackground(self, event):
        pass

    def OnPaint(self, event=None):
        self.delete("all")
        for n, i in enumerate(self._items._items):
            y = n * 30
            i.SetRect((0, y, 400, 30))
            self.create_rectangle(
                0,
                y,
                400,
                y + 30,
                fill=(
                    self._items.GetSelectionColour()
                    if n == self._items.GetSelection()
                    else self._items.GetBackgroundColour()
                ),
                outline=(
                    self._items.GetSelectionOutlineColour()
                    if n == self._items.GetSelection()
                    else ""
                ),
            )
            self.create_text(
                8, y + 15, text=i.GetTitle(), anchor="w", fill=i.GetTextColour()
            )

    def OnMouseEvent(self, event):
        self._items.SetSelection(
            max(0, min(self._items.GetItemCount() - 1, event.y // 30))
        )
        self.OnPaint()
        self.GenerateSelectionEvent()

    def OnChar(self, event):
        return self.OnKey(event)

    def OnKey(self, event):
        if event.keysym in ("Up", "Down"):
            self.AdvanceToNextSelectableItem(-1 if event.keysym == "Up" else 1)
            self.OnPaint()
            return "break"

    def AdvanceToNextSelectableItem(self, direction):
        self._items.SetSelection(
            max(
                0,
                min(
                    self._items.GetItemCount() - 1,
                    self._items.GetSelection() + direction,
                ),
            )
        )

    def SetTransparency(self, v):
        self._transparency = v

    def GenerateSelectionEvent(self):
        self.event_generate("<<SwitcherSelection>>")

    def CalculateLayout(self, dc):
        pass

    def SetItems(self, v):
        self._items = v
        self.OnPaint()

    def GetItems(self):
        return self._items

    def SetExtraNavigationKey(self, v):
        self._extraNavigationKey = v

    def GetExtraNavigationKey(self):
        return self._extraNavigationKey

    def SetModifierKey(self, v):
        self._modifierKey = v

    def GetModifierKey(self):
        return self._modifierKey


class SwitcherDialog(tk.Toplevel):
    def __init__(
        self,
        items,
        parent=None,
        aui_manager=None,
        id=-1,
        title="Switcher",
        pos=None,
        size=None,
        style=None,
    ):
        super().__init__(parent)
        self.title(title)
        self._items = items
        self._selection = items.GetSelection()
        self._borderColour = "#000000"
        self._list = MultiColumnListCtrl(self)
        self._list.SetItems(items)
        self._list.pack(fill="both", expand=True)
        self._list.bind("<<SwitcherSelection>>", self.OnSelectItem)
        self.bind("<Return>", self.OnSelectItem)
        self.bind("<Escape>", self.OnCloseWindow)
        self.protocol("WM_DELETE_WINDOW", self.OnCloseWindow)
        self.grab_set()
        self._list.focus_set()

    def OnCloseWindow(self, event=None):
        self.grab_release()
        self.destroy()

    def GetSelection(self):
        return self._items.GetSelection()

    def OnActivate(self, event=None):
        pass

    def OnPaint(self, event=None):
        self._list.OnPaint(event)

    def OnSelectItem(self, event=None):
        self._selection = self._items.GetSelection()
        self.OnCloseWindow(event)

    def ColourToHexString(self, col):
        if isinstance(col, str):
            return col
        return "#%02x%02x%02x" % tuple(col[:3])

    def ShowDescription(self, i):
        return (
            self._items.GetItem(i).GetDescription()
            if 0 <= i < self._items.GetItemCount()
            else ""
        )

    def SetExtraNavigationKey(self, v):
        self._list.SetExtraNavigationKey(v)

    def GetExtraNavigationKey(self):
        return self._list.GetExtraNavigationKey()

    def SetModifierKey(self, v):
        self._list.SetModifierKey(v)

    def GetModifierKey(self):
        return self._list.GetModifierKey()

    def SetBorderColour(self, v):
        self._borderColour = v
