# -*- coding: utf-8 -*-
"""Première étape de la conversion de auibar.py vers Tkinter.

Classes converties : CommandToolBarEvent, AuiToolBarEvent, ToolbarCommandCapture
et AuiToolBarItem. Les objets graphiques utilisent des widgets Tkinter ou des
valeurs Python simples, sans dépendance à wxPython.
"""

from copy import copy

try:
    from .aui_tk_constants import *
except ImportError:
    from aui_tk_constants import *


class CommandToolBarEvent:
    def __init__(self, command_type=None, win_id=0):
        self.command_type = command_type
        self.win_id = win_id
        self.is_dropdown_clicked = False
        self.click_pt = (-1, -1)
        self.rect = (-1, -1, 0, 0)
        self.tool_id = -1

    def IsDropDownClicked(self):
        return self.is_dropdown_clicked

    def SetDropDownClicked(self, c):
        self.is_dropdown_clicked = c

    def GetClickPoint(self):
        return self.click_pt

    def SetClickPoint(self, p):
        self.click_pt = p

    def GetItemRect(self):
        return self.rect

    def SetItemRect(self, r):
        self.rect = r

    def GetToolId(self):
        return self.tool_id

    def SetToolId(self, i):
        self.tool_id = i


class AuiToolBarEvent(CommandToolBarEvent):
    def __init__(self, command_type=None, win_id=0):
        super().__init__(command_type, win_id)
        self.notify = self

    def GetNotifyEvent(self):
        return self

    def IsAllowed(self):
        return getattr(self, "_allowed", True)

    def Veto(self):
        self._allowed = False

    def Allow(self):
        self._allowed = True


class ToolbarCommandCapture:
    def __init__(self):
        self._last_id = 0

    def GetCommandId(self):
        return self._last_id

    def ProcessEvent(self, event):
        self._last_id = getattr(event, "tool_id", getattr(event, "id", 0))
        return True


class AuiToolBarItem:
    def __init__(self, item=None):
        if item is not None:
            self.Assign(item)
            return
        self.window = None
        self.clockwisebmp = None
        self.counterclockwisebmp = None
        self.clockwisedisbmp = None
        self.counterclockwisedisbmp = None
        self.sizer_item = None
        self.spacer_pixels = 0
        self.id = 0
        self.kind = ITEM_NORMAL
        self.state = 0
        self.proportion = 0
        self.active = True
        self.dropdown = True
        self.sticky = True
        self.user_data = 0
        self.label = ""
        self.bitmap = None
        self.disabled_bitmap = None
        self.hover_bitmap = None
        self.short_help = ""
        self.long_help = ""
        self.target = None
        self.min_size = (-1, -1)
        self.alignment = "center"
        self.orientation = AUI_TBTOOL_HORIZONTAL

    def Assign(self, c):
        self.__dict__.update(c.__dict__)
        return self

    def SetWindow(self, v):
        self.window = v

    def GetWindow(self):
        return self.window

    def SetId(self, v):
        self.id = v

    def GetId(self):
        return self.id

    def SetKind(self, v):
        self.kind = v

    def GetKind(self):
        return self.kind

    def SetState(self, v):
        self.state = v

    def GetState(self):
        return self.state

    def SetSizerItem(self, v):
        self.sizer_item = v

    def GetSizerItem(self):
        return self.sizer_item

    def SetLabel(self, v):
        self.label = v

    def GetLabel(self):
        return self.label

    def SetBitmap(self, v):
        self.bitmap = v

    def GetBitmap(self):
        return self.bitmap

    def SetDisabledBitmap(self, v):
        self.disabled_bitmap = v

    def GetDisabledBitmap(self):
        return self.disabled_bitmap

    def SetHoverBitmap(self, v):
        self.hover_bitmap = v

    def SetOrientation(self, v):
        self.orientation = v

    def GetOrientation(self):
        return self.orientation

    def GetHoverBitmap(self):
        return self.hover_bitmap

    def GetRotatedBitmap(self):
        return self.bitmap

    def SetShortHelp(self, v):
        self.short_help = v

    def GetShortHelp(self):
        return self.short_help

    def SetLongHelp(self, v):
        self.long_help = v

    def GetLongHelp(self):
        return self.long_help

    def SetMinSize(self, v):
        self.min_size = v

    def GetMinSize(self):
        return self.min_size

    def SetSpacerPixels(self, v):
        self.spacer_pixels = v

    def GetSpacerPixels(self):
        return self.spacer_pixels

    def SetProportion(self, v):
        self.proportion = v

    def GetProportion(self):
        return self.proportion

    def SetActive(self, v):
        self.active = v

    def IsActive(self):
        return self.active

    def SetHasDropDown(self, v):
        self.dropdown = v

    def HasDropDown(self):
        return self.dropdown

    def SetSticky(self, v):
        self.sticky = v

    def IsSticky(self):
        return self.sticky

    def SetUserData(self, v):
        self.user_data = v

    def GetUserData(self):
        return self.user_data

    def SetAlignment(self, v):
        self.alignment = v

    def GetAlignment(self):
        return self.alignment
