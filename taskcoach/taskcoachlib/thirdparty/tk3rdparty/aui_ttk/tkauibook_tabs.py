# -*- coding: utf-8 -*-
"""Conteneur et contrôle d'onglets Tkinter, étape 2 de la conversion."""
import tkinter as tk
try:
    from .tktabart import AuiDefaultTabArt
    from .aui_tk_constants import *
except ImportError:
    from tktabart import AuiDefaultTabArt
    from aui_tk_constants import *

class AuiTabContainer:
    def __init__(self,auiNotebook):
        self._tab_offset=0; self._agwFlags=0; self._art=AuiDefaultTabArt(); self._buttons=[]; self._pages=[]; self._tab_close_buttons=[]; self._click_tab=None; self._rect=(0,0,1,1); self._auiNotebook=auiNotebook
        for bid,loc,name in [(AUI_BUTTON_LEFT,'left','Scroll Left'),(AUI_BUTTON_RIGHT,'right','Scroll Right'),(AUI_BUTTON_WINDOWLIST,'right','Window List'),(AUI_BUTTON_CLOSE,'right','Close')]: self.AddButton(bid,loc,None,None,name)
    def SetArtProvider(self,art): self._art=art
    def GetArtProvider(self): return self._art
    def SetAGWFlags(self,f): self._agwFlags=f; self._art.SetAGWFlags(f)
    def GetAGWFlags(self): return self._agwFlags
    def SetNormalFont(self,f): self._art.SetNormalFont(f)
    def SetSelectedFont(self,f): self._art.SetSelectedFont(f)
    def SetMeasuringFont(self,f): self._art.SetMeasuringFont(f)
    def SetTabRect(self,r): self._rect=r
    def AddPage(self,page,info): self._pages.append(info); self._tab_close_buttons.append(getattr(info,'hasCloseButton',True)); return True
    def InsertPage(self,page,info,idx): self._pages.insert(idx,info); self._tab_close_buttons.insert(idx,getattr(info,'hasCloseButton',True)); return True
    def MovePage(self,page,new_idx):
        old=self.GetIdxFromWindow(page); 
        if old<0:return False
        item=self._pages.pop(old); self._pages.insert(new_idx,item); return True
    def RemovePage(self,wnd):
        idx=self.GetIdxFromWindow(wnd)
        if idx<0 and isinstance(wnd,int): idx=wnd
        if idx<0:return False
        self._pages.pop(idx); self._tab_close_buttons.pop(idx); return True
    def SetActivePage(self,wndOrInt):
        idx=wndOrInt if isinstance(wndOrInt,int) else self.GetIdxFromWindow(wndOrInt)
        for i,p in enumerate(self._pages): p.active=i==idx
    def SetNoneActive(self):
        for p in self._pages:p.active=False
    def GetActivePage(self): return next((p for p in self._pages if getattr(p,'active',False)),None)
    def GetWindowFromIdx(self,idx): return getattr(self._pages[idx],'window',None) if 0<=idx<len(self._pages) else None
    def GetIdxFromWindow(self,wnd): return next((i for i,p in enumerate(self._pages) if getattr(p,'window',None)==wnd),-1)
    def GetPage(self,idx): return self._pages[idx] if 0<=idx<len(self._pages) else None
    def GetPages(self): return self._pages
    def GetPageCount(self): return len(self._pages)
    def GetShownPageCount(self): return sum(not getattr(p,'hidden',False) for p in self._pages)
    def GetHidden(self,idx): return getattr(self.GetPage(idx),'hidden',False)
    def HideTab(self,idx,hidden=True):
        p=self.GetPage(idx)
        if p:p.hidden=hidden
    def GetEnabled(self,idx): return getattr(self.GetPage(idx),'enabled',False)
    def EnableTab(self,idx,enable=True):
        p=self.GetPage(idx)
        if p:p.enabled=enable
    def FindNextActiveTab(self,idx):
        return next((i for i in range(idx+1,len(self._pages)) if not self.GetHidden(i) and self.GetEnabled(i)), -1)
    def AddButton(self,id,location,normal_bitmap=None,disabled_bitmap=None,name=''): self._buttons.append(type('Button',(),{'id':id,'location':location,'bitmap':normal_bitmap,'dis_bitmap':disabled_bitmap,'name':name,'rect':(0,0,0,0),'cur_state':AUI_BUTTON_STATE_NORMAL})()); return self._buttons[-1]
    def CloneButtons(self): return list(self._buttons)
    def RemoveButton(self,id): self._buttons=[b for b in self._buttons if b.id!=id]
    def GetTabOffset(self): return self._tab_offset
    def SetTabOffset(self,o): self._tab_offset=o
    def Render(self,raw_dc,wnd):
        if hasattr(raw_dc,'delete'): raw_dc.delete('all')
        for i,p in enumerate(self._pages):
            if not getattr(p,'hidden',False): self._art.DrawTab(raw_dc,wnd,p,(i*100,0,100,30),0)
    def IsTabVisible(self,tabPage,tabOffset,dc,wnd): return not getattr(tabPage,'hidden',False)
    def MakeTabVisible(self,tabPage,win): return True
    def TabHitTest(self,x,y): return next((i for i,p in enumerate(self._pages) if _inside(getattr(p,'rect',(0,0,0,0)),x,y)),-1)
    def ButtonHitTest(self,x,y,state_flags=0): return next((b for b in self._buttons if _inside(b.rect,x,y)),None)
    def DoShowHide(self):
        for p in self._pages:
            w=getattr(p,'window',None)
            if w and hasattr(w,'pack'): (w.pack if not getattr(p,'hidden',False) else w.pack_forget)()

def _inside(r,x,y):
    a,b,c,d=(r.x,r.y,r.width,r.height) if hasattr(r,'x') else r
    return a<=x<=a+c and b<=y<=b+d

class AuiTabCtrl(tk.Frame,AuiTabContainer):
    def __init__(self,parent,id=-1,pos=None,size=None,style=None):
        tk.Frame.__init__(self,parent,highlightthickness=0); AuiTabContainer.__init__(self,parent); self._click_pt=(-1,-1); self._is_dragging=False; self._hover_button=None; self._pressed_button=None; self._tooltip_timer=None; self._tooltip_wnd=None
        self._canvas=tk.Canvas(self,highlightthickness=0); self._canvas.pack(fill='both',expand=True); self._canvas.bind('<Configure>',self.OnSize); self._canvas.bind('<Button-1>',self.OnLeftDown); self._canvas.bind('<ButtonRelease-1>',self.OnLeftUp); self._canvas.bind('<Motion>',self.OnMotion); self._canvas.bind('<Double-Button-1>',self.OnLeftDClick); self._canvas.bind('<Button-3>',self.OnRightDown); self._canvas.bind('<Key>',self.OnKeyDown)
    def IsDragging(self): return self._is_dragging
    def GetDefaultBorder(self): return 1
    def OnPaint(self,event=None): self.Render(self._canvas,self)
    def OnEraseBackground(self,event=None): pass
    def DoGetBestSize(self): return (400,30)
    def OnSize(self,event=None): self.OnPaint(event)
    def OnLeftDown(self,event): self._click_pt=(event.x,event.y); self.focus_set()
    def OnCaptureLost(self,event=None): self._is_dragging=False
    def OnLeftUp(self,event):
        idx=self.TabHitTest(event.x,event.y)
        if idx>=0:self.SetActivePage(idx); self.OnPaint()
    def OnMiddleUp(self,event): pass
    def OnMiddleDown(self,event): pass
    def OnRightUp(self,event): pass
    def OnRightDown(self,event): pass
    def OnLeftDClick(self,event): pass
    def OnMotion(self,event): pass
    def GetPointedToTab(self): return self.TabHitTest(*self._click_pt)
    def RestartTooltipTimer(self,wnd): self.StopTooltipTimer()
    def StopTooltipTimer(self):
        if self._tooltip_timer:self.after_cancel(self._tooltip_timer); self._tooltip_timer=None
    def OnEnterWindow(self,event): pass
    def ShowTooltip(self): pass
    def OnLeaveWindow(self,event): self.StopTooltipTimer()
    def OnButton(self,event): pass
    def OnSetFocus(self,event): pass
    def OnKillFocus(self,event): pass
    def OnKeyDown(self,event):
        if event.keysym in ('Left','Right'):
            active=next((i for i,p in enumerate(self._pages) if getattr(p,'active',False)),0); step=-1 if event.keysym=='Left' else 1; self.SetActivePage(max(0,min(len(self._pages)-1,active+step))); self.OnPaint()
    def OnKeyDown2(self,event): return self.OnKeyDown(event)
