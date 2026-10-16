# -*- coding: utf-8 -*-
"""Art de barre d'outils AUI adapté à Tkinter, étape 2."""
import tkinter as tk
from tkinter import font as tkfont
try:
    from .aui_tk_constants import *
    from .aui_tk_utilities import StepColour, GetBaseColour, GetLabelSize
except ImportError:
    from aui_tk_constants import *
    from aui_tk_utilities import StepColour, GetBaseColour, GetLabelSize

class AuiDefaultToolBarArt:
    def __init__(self):
        self.SetDefaultColours(); self._agwFlags=0; self._text_orientation=AUI_TBTOOL_TEXT_BOTTOM; self._separator_size=7; self._orientation=AUI_TBTOOL_HORIZONTAL; self._gripper_size=7; self._overflow_size=16; self._font=tkfont.Font(family='TkDefaultFont',size=9)
        self._element_sizes={AUI_TBART_SEPARATOR_SIZE:7,AUI_TBART_GRIPPER_SIZE:7,AUI_TBART_OVERFLOW_SIZE:16}
    def SetDefaultColours(self,base_colour=None):
        self._base_colour=base_colour or GetBaseColour(); self._gripper_colour1=StepColour(self._base_colour,40); self._gripper_colour2=StepColour(self._base_colour,60); self._gripper_colour3='#ffffff'
    def Clone(self):
        art=AuiDefaultToolBarArt(); art._agwFlags=self._agwFlags; art._orientation=self._orientation; art._text_orientation=self._text_orientation; return art
    def SetAGWFlags(self,v): self._agwFlags=v
    def GetAGWFlags(self): return self._agwFlags
    def SetFont(self,v): self._font=v if isinstance(v,tkfont.Font) else tkfont.Font(family='TkDefaultFont',size=9)
    def SetTextOrientation(self,v): self._text_orientation=v
    def GetFont(self): return self._font
    def GetTextOrientation(self): return self._text_orientation
    def SetOrientation(self,v): self._orientation=v
    def GetOrientation(self): return self._orientation
    def _xywh(self,r): return (r.x,r.y,r.width,r.height) if hasattr(r,'x') else tuple(r[:4])
    def DrawBackground(self,dc,wnd,r,horizontal=True): self.DrawPlainBackground(dc,wnd,r)
    def DrawPlainBackground(self,dc,wnd,r):
        x,y,w,h=self._xywh(r); dc.create_rectangle(x,y,x+w,y+h,fill=self._base_colour,outline='')
    def DrawLabel(self,dc,wnd,item,r):
        x,y,w,h=self._xywh(r); dc.create_text(x+w//2,y+h//2,text=item.GetLabel(),font=self._font,fill='#000000')
    def DrawButton(self,dc,wnd,item,r):
        x,y,w,h=self._xywh(r); fill='#d0d0d0' if item.IsActive() else self._base_colour; dc.create_rectangle(x,y,x+w,y+h,fill=fill,outline='#808080'); self.DrawLabel(dc,wnd,item,r)
    def DrawDropDownButton(self,dc,wnd,item,r):
        self.DrawButton(dc,wnd,item,r); x,y,w,h=self._xywh(r); dc.create_polygon(x+w-10,y+h//2-2,x+w-4,y+h//2-2,x+w-7,y+h//2+3,fill='#000000')
    def DrawControlLabel(self,dc,wnd,item,r): self.DrawLabel(dc,wnd,item,r)
    def GetLabelSize(self,dc,wnd,item): return self._font.measure(item.GetLabel()),self._font.metrics('linespace')
    def GetToolSize(self,dc,wnd,item):
        w,h=self.GetLabelSize(dc,wnd,item); return max(24,w+12),max(24,h+12)
    def DrawSeparator(self,dc,wnd,r):
        x,y,w,h=self._xywh(r); dc.create_line(x+w//2,y+2,x+w//2,y+h-2,fill='#888888') if self._orientation==AUI_TBTOOL_HORIZONTAL else dc.create_line(x+2,y+h//2,x+w-2,y+h//2,fill='#888888')
    def DrawGripper(self,dc,wnd,r):
        x,y,w,h=self._xywh(r); dc.create_rectangle(x,y,x+w,y+h,fill=self._base_colour,outline='');
        for i in range(3): dc.create_line(x+3+i*3,y+3,x+3+i*3,y+h-3,fill=self._gripper_colour2)
    def DrawOverflowButton(self,dc,wnd,r,state):
        x,y,w,h=self._xywh(r); dc.create_rectangle(x,y,x+w,y+h,fill=self._base_colour,outline='#888888'); dc.create_text(x+w//2,y+h//2,text='⋮',font=self._font)
    def GetElementSize(self,e): return self._element_sizes.get(e,0)
    def SetElementSize(self,e,size): self._element_sizes[e]=size
    def ShowDropDown(self,wnd,items): return None
    def GetToolsPosition(self,dc,item,r): return self._xywh(r)[:2]
