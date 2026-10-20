# -*- coding: utf-8 -*-
"""Classes auxiliaires de tkauibook adaptées à Tkinter.

Ce module convertit les sept premières classes de tkauibook.py. Les événements
wxPython sont remplacés par de petits objets Python et les contrôles par des
widgets Tkinter lorsque cela est nécessaire.
"""
import datetime
import tkinter as tk
from tkinter import ttk
try:
    from .aui_tk_constants import *
except ImportError:
    from aui_tk_constants import *

class TabTextCtrl(tk.Entry):
    """Contrôle d'édition du texte d'un onglet."""
    def __init__(self, owner, tab, page_index):
        self._owner=owner; self._tabEdited=tab; self._pageIndex=page_index
        self._startValue=getattr(tab,'caption',''); self._finished=False; self._aboutToFinish=False
        self._currentValue=self._startValue
        parent=owner if isinstance(owner,tk.Misc) else getattr(owner,'master',None)
        super().__init__(parent)
        self.insert(0,self._startValue); self.select_range(0,tk.END); self.focus_set()
        self.bind('<Return>',self.OnChar); self.bind('<Escape>',self.OnChar); self.bind('<KeyRelease>',self.OnKeyUp); self.bind('<FocusOut>',self.OnKillFocus)
    def _notebook(self): return self._owner.winfo_toplevel() if isinstance(self._owner,tk.Misc) else getattr(self._owner,'master',self._owner)
    def AcceptChanges(self):
        value=self.get(); notebook=self._notebook()
        if value==self._startValue:
            if hasattr(notebook,'OnRenameCancelled'): notebook.OnRenameCancelled(self._pageIndex)
            return True
        if hasattr(notebook,'OnRenameAccept') and not notebook.OnRenameAccept(self._pageIndex,value): return False
        if hasattr(notebook,'SetPageText'): notebook.SetPageText(self._pageIndex,value)
        return True
    def Finish(self):
        if not self._finished:
            self._finished=True
            if hasattr(self._owner,'focus_set'): self._owner.focus_set()
            if hasattr(self._owner,'ResetTextControl'): self._owner.ResetTextControl()
            else: self.destroy()
    def OnChar(self,event):
        if event.keysym=='Return':
            self._aboutToFinish=True; self._currentValue=self.get(); self.AcceptChanges(); self.after_idle(self.Finish); return 'break'
        if event.keysym=='Escape': self.StopEditing(); return 'break'
    def OnKeyUp(self,event):
        self._currentValue=self.get()
    def OnKillFocus(self,event):
        if not self._aboutToFinish: self.AcceptChanges()
        self.Finish()
    def StopEditing(self): self._aboutToFinish=True; self.delete(0,tk.END); self.insert(0,self._startValue); self.Finish()
    def item(self,*args,**kwargs): return self.get() if not args and not kwargs else None

class AuiNotebookPage:
    def __init__(self):
        self.window=None; self.caption=''; self.bitmap=None; self.dis_bitmap=None; self.tooltip=''; self.rect=(0,0,0,0); self.active=False; self.enabled=True; self.hidden=False; self.hasCloseButton=True; self.control=None; self.renamable=False; self.text_colour='#000000'; self.access_time=datetime.datetime.now()
    def IsMultiline(self): return '\n' in self.caption

class AuiTabContainerButton:
    def __init__(self):
        self.id=-1; self.name=''; self.cur_state=AUI_BUTTON_STATE_NORMAL; self.location='left'; self.bitmap=None; self.dis_bitmap=None; self.rect=(0,0,0,0)

class CommandNotebookEvent:
    def __init__(self,command_type=None,win_id=0):
        self.event_type=command_type; self.win_id=win_id; self.old_selection=-1; self.selection=-1; self.drag_source=None; self.dispatched=0; self.label=''; self.editCancelled=False; self.page=None; self._commandInt=0
    def SetSelection(self,s): self.selection=s; self._commandInt=s
    def GetSelection(self): return self.selection
    def SetOldSelection(self,s): self.old_selection=s
    def GetOldSelection(self): return self.old_selection
    def SetDragSource(self,s): self.drag_source=s
    def GetDragSource(self): return self.drag_source
    def SetDispatched(self,d): self.dispatched=d
    def GetDispatched(self): return self.dispatched
    def IsEditCancelled(self): return self.editCancelled
    def SetEditCanceled(self,c=True): self.editCancelled=c
    def GetLabel(self): return self.label
    def SetLabel(self,label): self.label=label

class AuiNotebookEvent:
    def __init__(self,command_type=None,win_id=0): self.notify_event=command_type; self.allowed=True; self.event_type=command_type; self.win_id=win_id
    def GetNotifyEvent(self): return self.notify_event
    def IsAllowed(self): return self.allowed
    def Veto(self): self.allowed=False
    def Allow(self): self.allowed=True

class TabNavigatorProps:
    def __init__(self):
        self.notebook=None; self.tabCtrl=None; self.selectedPage=-1; self.activePage=-1; self.pages=[]; self.itemList=[]; self.bitmapSize=(0,0)

class TabNavigatorWindow(tk.Toplevel):
    def __init__(self,parent,props=None):
        super().__init__(parent); self.props=props or TabNavigatorProps(); self.transient(parent); self.title('Select tab'); self.resizable(False,False)
        self.listbox=tk.Listbox(self,exportselection=False); self.listbox.pack(fill='both',expand=True,padx=8,pady=8); self.listbox.bind('<Double-1>',self.OnItemSelected); self.listbox.bind('<Return>',self.OnItemSelected); self.bind('<Escape>',self.CloseDialog); self.PopulateListControl(); self.grab_set(); self.listbox.focus_set()
    def OnLeftDown(self,event): self._press=(event.x,event.y)
    def OnLeftUp(self,event): pass
    def OnMotion(self,event): pass
    def OnKeyUp(self,event):
        if event.keysym=='Escape': self.CloseDialog(event)
    def OnNavigationKey(self,event): return None
    def PopulateListControl(self):
        self.listbox.delete(0,tk.END); pages=getattr(self.props,'pages',[])
        for page in pages: self.listbox.insert(tk.END,getattr(page,'caption',str(page)))
        selected=getattr(self.props,'selectedPage',-1)
        if 0<=selected<self.listbox.size(): self.listbox.selection_set(selected); self.listbox.see(selected)
    def OnItemSelected(self,event=None):
        selection=self.listbox.curselection()
        if selection: self.props.selectedPage=selection[0]
        self.CloseDialog(event); return 'break'
    def CloseDialog(self,event=None): self.grab_release(); self.destroy()
    def GetSelectedPage(self): return getattr(self.props,'selectedPage',-1)
    def OnPanelPaint(self,event): pass
    def OnPanelEraseBg(self,event): pass
