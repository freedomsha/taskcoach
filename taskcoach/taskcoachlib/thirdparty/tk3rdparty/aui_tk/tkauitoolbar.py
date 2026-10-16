# -*- coding: utf-8 -*-
"""AuiToolBar Tkinter, conversion de la classe wxPython AuiToolBar."""
import tkinter as tk
from tkinter import ttk
try:
 from .tkauibar_items import AuiToolBarItem
 from .tkauibar_art import AuiDefaultToolBarArt
 from .aui_tk_constants import *
except ImportError:
 from tkauibar_items import AuiToolBarItem
 from tkauibar_art import AuiDefaultToolBarArt
 from aui_tk_constants import *

class AuiToolBar(tk.Frame):
 def __init__(self,parent,id=-1,pos=None,size=None,style=None,agwStyle=0):
  super().__init__(parent); self._agwStyle=agwStyle; self._art=AuiDefaultToolBarArt(); self._items=[]; self._tool_bitmap_size=(16,16); self._tool_separation=5; self._border_padding=2; self._orientation=AUI_TBTOOL_HORIZONTAL; self._packing=1; self._margins=(0,0,0,0); self._gripper_visible=True; self._overflow_visible=True; self._auiManager=None; self._hover_item=None; self._pressed_item=None; self._canvas=tk.Canvas(self,highlightthickness=0); self._canvas.pack(fill='both',expand=True); self._canvas.bind('<Button-1>',self.OnLeftDown); self._canvas.bind('<ButtonRelease-1>',self.OnLeftUp); self._canvas.bind('<Motion>',self.OnMotion); self._canvas.bind('<Configure>',self.OnSize)
 def SetWindowStyleFlag(self,s): self._style=s
 def SetAGWWindowStyleFlag(self,s): self._agwStyle=s
 def GetAGWWindowStyleFlag(self): return self._agwStyle
 def SetArtProvider(self,a): self._art=a
 def GetArtProvider(self): return self._art
 def AddTool(self,tool_id,label,bitmap=None,disabled_bitmap=None,kind=ITEM_NORMAL,short_help_string='',long_help_string='',client_data=None,target=None):
  i=AuiToolBarItem(); i.SetId(tool_id); i.SetLabel(label); i.SetBitmap(bitmap); i.SetDisabledBitmap(disabled_bitmap); i.SetKind(kind); i.SetShortHelp(short_help_string); i.SetLongHelp(long_help_string); i.SetUserData(client_data); i.target=target; self._items.append(i); return i
 def AddSimpleTool(self,tool_id,label,bitmap,short_help_string='',kind=ITEM_NORMAL,target=None): return self.AddTool(tool_id,label,bitmap,None,kind,short_help_string,'',None,target)
 def AddToggleTool(self,tool_id,bitmap,disabled_bitmap=None,toggle=False,client_data=None,short_help_string='',long_help_string=''): i=self.AddTool(tool_id,'',bitmap,disabled_bitmap,ITEM_CHECK,short_help_string,long_help_string,client_data); i.SetState(1 if toggle else 0); return i
 def AddCheckTool(self,*a,**k): return self.AddTool(k.pop('tool_id',a[0] if a else 0),k.pop('label',''),k.pop('bitmap',None),k.pop('disabled_bitmap',None),ITEM_CHECK,k.pop('short_help_string',''),k.pop('long_help_string',''),k.pop('client_data',None))
 def AddRadioTool(self,*a,**k): return self.AddCheckTool(*a,**k)
 def AddControl(self,control,label=''): i=self.AddTool(id(control),label,None,None,ITEM_CONTROL); i.SetWindow(control); return i
 def AddLabel(self,tool_id,label,width=0): return self.AddTool(tool_id,label,None,None,ITEM_LABEL)
 def AddSeparator(self): return self.AddTool(-1,'',None,None,ITEM_SEPARATOR)
 def AddSpacer(self,pixels): i=self.AddTool(-1,'',None,None,ITEM_SPACER); i.SetSpacerPixels(pixels); return i
 def AddStretchSpacer(self,proportion=1): i=self.AddSpacer(0); i.SetProportion(proportion); return i
 def Clear(self): self.ClearTools()
 def ClearTools(self): self._items.clear(); self.OnPaint(None)
 def DeleteTool(self,tool): return self.DeleteToolByPos(self.GetToolIndex(tool if isinstance(tool,int) else tool.GetId()))
 def DeleteToolByPos(self,pos):
  if 0<=pos<len(self._items): self._items.pop(pos); self.OnPaint(None); return True
  return False
 def FindControl(self,id):
  i=self.FindTool(id); return i.GetWindow() if i else None
 def FindTool(self,tool_id): return next((i for i in self._items if i.GetId()==tool_id),None)
 def FindToolByLabel(self,label): return next((i for i in self._items if i.GetLabel()==label),None)
 def FindToolByUserData(self,userData): return next((i for i in self._items if i.GetUserData()==userData),None)
 def FindToolForPosition(self,x,y): return self.FindToolByIndex(self.HitTest(x,y))
 def HitTest(self,x,y): return next((n for n,i in enumerate(self._items) if getattr(i,'rect',(0,0,0,0))[0]<=x<=getattr(i,'rect',(0,0,0,0))[0]+getattr(i,'rect',(0,0,0,0))[2]),-1)
 def FindToolForPositionWithPacking(self,x,y): return self.FindToolForPosition(x,y)
 def FindToolByIndex(self,pos): return self._items[pos] if 0<=pos<len(self._items) else None
 def SetToolBitmapSize(self,size): self._tool_bitmap_size=size
 def GetToolBitmapSize(self): return self._tool_bitmap_size
 def SetToolProportion(self,id,v): self.FindTool(id).SetProportion(v)
 def GetToolProportion(self,id): return self.FindTool(id).GetProportion()
 def SetToolSeparation(self,v): self._tool_separation=v
 def GetToolSeparation(self): return self._tool_separation
 def SetToolDropDown(self,id,v): self.FindTool(id).SetHasDropDown(v)
 def GetToolDropDown(self,id): return self.FindTool(id).HasDropDown()
 def SetToolSticky(self,id,v): self.FindTool(id).SetSticky(v)
 def GetToolSticky(self,id): return self.FindTool(id).IsSticky()
 def SetToolBorderPadding(self,v): self._border_padding=v
 def GetToolBorderPadding(self): return self._border_padding
 def SetToolTextOrientation(self,v): self._art.SetTextOrientation(v)
 def GetToolTextOrientation(self): return self._art.GetTextOrientation()
 def SetToolOrientation(self,v): self.SetOrientation(v)
 def GetToolOrientation(self): return self._orientation
 def SetToolPacking(self,v): self._packing=v
 def GetToolPacking(self): return self._packing
 def SetOrientation(self,v): self._orientation=v; self._art.SetOrientation(v)
 def SetMargins(self,left,right,top,bottom): self._margins=(left,right,top,bottom)
 def SetMarginsSize(self,size): self.SetMargins(size[0],size[0],size[1],size[1])
 def SetMarginsXY(self,x,y): self.SetMargins(x,x,y,y)
 def GetGripperVisible(self): return self._gripper_visible
 def SetGripperVisible(self,v): self._gripper_visible=v
 def GetOverflowVisible(self): return self._overflow_visible
 def SetOverflowVisible(self,v): self._overflow_visible=v
 def SetFont(self,f): self._art.SetFont(f)
 def SetHoverItem(self,p): self._hover_item=p
 def SetPressedItem(self,p): self._pressed_item=p
 def RefreshOverflowState(self): pass
 def ToggleTool(self,id,state): self.FindTool(id).SetState(1 if state else 0); self.OnPaint(None)
 def GetToolToggled(self,id): return bool(self.FindTool(id).GetState())
 def EnableTool(self,id,state): self.FindTool(id).SetActive(state)
 def GetToolEnabled(self,id): return self.FindTool(id).IsActive()
 def GetToolLabel(self,id): return self.FindTool(id).GetLabel()
 def SetToolLabel(self,id,v): self.FindTool(id).SetLabel(v)
 def GetToolBitmap(self,id): return self.FindTool(id).GetBitmap()
 def SetToolBitmap(self,id,v): self.SetToolNormalBitmap(id,v)
 def SetToolNormalBitmap(self,id,v): self.FindTool(id).SetBitmap(v)
 def SetToolDisabledBitmap(self,id,v): self.FindTool(id).SetDisabledBitmap(v)
 def GetToolShortHelp(self,id): return self.FindTool(id).GetShortHelp()
 def SetToolShortHelp(self,id,v): self.FindTool(id).SetShortHelp(v)
 def GetToolLongHelp(self,id): return self.FindTool(id).GetLongHelp()
 def SetToolAlignment(self,alignment): self._alignment=alignment
 def SetToolLongHelp(self,id,v): self.FindTool(id).SetLongHelp(v)
 def SetCustomOverflowItems(self,prepend,append): self._overflow_prepend=prepend; self._overflow_append=append
 def GetToolCount(self): return len(self._items)
 def GetToolIndex(self,id): return next((n for n,i in enumerate(self._items) if i.GetId()==id),-1)
 def GetToolPos(self,id): return self.GetToolIndex(id)
 def GetToolFitsByIndex(self,id): return True
 def GetToolFits(self,id): return True
 def GetToolRect(self,id):
  i=self.FindTool(id); return getattr(i,'rect',(0,0,0,0)) if i else None
 def GetToolBarFits(self): return True
 def Realize(self): self.OnPaint(None); return True
 def GetOverflowState(self): return False
 def GetOverflowRect(self): return (0,0,0,0)
 def GetLabelSize(self,label): return (self._art.GetFont().measure(label),self._art.GetFont().metrics('linespace'))
 def GetAuiManager(self): return self._auiManager
 def SetAuiManager(self,v): self._auiManager=v
 def DoIdleUpdate(self): self.OnPaint(None)
 def OnSize(self,event): self.OnPaint(event)
 def DoSetSize(self,x,y,width,height,sizeFlags=None): self.place(x=x,y=y,width=width,height=height)
 def OnIdle(self,event): self.DoIdleUpdate()
 def DoGetBestSize(self): return (400,32)
 def OnPaint(self,event):
  self._canvas.delete('all'); x=2; h=max(24,self.winfo_height());
  for i in self._items:
   w=max(28,self._art.GetToolSize(self._canvas,self,i)[0]); i.rect=(x,0,w,h)
   if i.kind==ITEM_SEPARATOR:self._art.DrawSeparator(self._canvas,self,i.rect)
   elif i.kind==ITEM_SPACER:x+=i.spacer_pixels; continue
   else:self._art.DrawDropDownButton(self._canvas,self,i,i.rect) if i.HasDropDown() else self._art.DrawButton(self._canvas,self,i,i.rect)
   x+=w+self._tool_separation
 def OnEraseBackground(self,event): pass
 def OnLeftDown(self,event): self._pressed_item=self.FindToolForPosition(event.x,event.y)
 def OnLeftUp(self,event): self._pressed_item=None
 def OnRightDown(self,event): pass
 def OnRightUp(self,event): pass
 def OnMiddleDown(self,event): pass
 def OnMiddleUp(self,event): pass
 def OnMotion(self,event): self._hover_item=self.FindToolForPosition(event.x,event.y)
 def OnLeaveWindow(self,event): self._hover_item=None
 def OnSetCursor(self,event): pass
 def OnCustomRender(self,dc,item,rect): pass
 def IsPaneMinimized(self): return False
 def StartPreviewTimer(self): pass
 def StopPreviewTimer(self): pass
