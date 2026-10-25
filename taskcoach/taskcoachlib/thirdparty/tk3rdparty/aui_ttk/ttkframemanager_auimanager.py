# -*- coding: utf-8 -*-
"""Gestionnaire AUI basé sur ttk.PanedWindow et ttk.Notebook.

Cette version conserve l'API de tkframemanager_auimanager.py pour les
opérations de panneaux, mais utilise une disposition ttk explicite.
"""

import json
import tkinter as tk
from tkinter import ttk

from .tkframemanager_elements import (
    AuiDockInfo,
    AuiDockingGuideInfo,
    AuiDockUIPart,
    AuiPaneButton,
    AuiManagerEvent,
    AuiPaneInfo,
)
from .ttkauibook import AuiNotebook
from .aui_tk_constants import *

NonePaneInfo = AuiPaneInfo()


class TtkPanePlacement:
    """Paramètres de placement d'un panneau dans une grille."""

    POSITIONS = {"gauche", "droite", "au-dessus", "en-dessous", "centre"}
    RELATIONS = {"global", "intermediaire", "unitaire"}

    def __init__(self, relation="unitaire", position="centre", rank="last"):
        """Initialise les paramètres de placement."""
        if relation not in self.RELATIONS:
            raise ValueError("relation doit être global, intermediaire ou unitaire")
        if position not in self.POSITIONS:
            raise ValueError("position inconnue")
        if rank != "last" and not isinstance(rank, int):
            raise TypeError("rank doit être 'last' ou un entier")
        self.relation, self.position, self.rank = relation, position, rank


class TtkGridLayout:
    """Projection déterministe d'une disposition AUI vers tkinter.grid().

    La grille logique comporte trois lignes et trois colonnes. Les panneaux
    sont classés par direction, layer, row puis dock_pos. La reconstruction
    complète après chaque changement rend l'ajout, le retrait et le
    réordonnancement idempotents.
    """

    def __init__(self, parent):
        self.parent = parent
        self._entries = []
        parent.grid_propagate(False)
        for index in range(3):
            parent.rowconfigure(index, weight=1 if index == 1 else 0)
            parent.columnconfigure(index, weight=1 if index == 1 else 0)

    @staticmethod
    def _direction(pane):
        direction = getattr(pane, "dock_direction", AUI_DOCK_LEFT)
        return {
            AUI_DOCK_LEFT: "gauche",
            AUI_DOCK_RIGHT: "droite",
            AUI_DOCK_TOP: "au-dessus",
            AUI_DOCK_BOTTOM: "en-dessous",
        }.get(direction, "centre")

    @staticmethod
    def _sort_key(entry):
        pane = entry["pane"]
        return (
            getattr(pane, "dock_layer", 0),
            getattr(pane, "dock_row", 0),
            getattr(pane, "dock_pos", 0),
            entry["order"],
        )

    def add(self, widget, pane):
        self.remove(widget, rebuild=False)
        self._entries.append(
            {"widget": widget, "pane": pane, "order": len(self._entries)}
        )
        self.rebuild()

    def remove(self, widget, rebuild=True):
        found = False
        for entry in list(self._entries):
            if entry["widget"] is widget:
                try:
                    widget.grid_forget()
                except tk.TclError:
                    pass
                self._entries.remove(entry)
                found = True
        if rebuild and found:
            self.rebuild()
        return found

    def _slot(self, pane, side_index):
        direction = self._direction(pane)
        if direction == "gauche":
            return side_index, 0, 1, 1
        if direction == "droite":
            return side_index, 2, 1, 1
        if direction == "au-dessus":
            return 0, side_index, 1, 1
        if direction == "en-dessous":
            return 2, side_index, 1, 1
        return 1, 1, 1, 1

    def rebuild(self):
        for entry in self._entries:
            try:
                entry["widget"].grid_forget()
            except tk.TclError:
                pass
        groups = {
            "gauche": [],
            "droite": [],
            "au-dessus": [],
            "en-dessous": [],
            "centre": [],
        }
        for entry in self._entries:
            groups[self._direction(entry["pane"])].append(entry)
        for entries in groups.values():
            entries.sort(key=self._sort_key)
        for direction, entries in groups.items():
            for index, entry in enumerate(entries):
                row, column, rowspan, columnspan = self._slot(entry["pane"], index)
                entry["grid"] = (row, column, rowspan, columnspan)
                entry["widget"].grid(
                    row=row,
                    column=column,
                    rowspan=rowspan,
                    columnspan=columnspan,
                    sticky="nsew",
                    padx=1,
                    pady=1,
                )
        for i in range(3):
            self.parent.rowconfigure(i, weight=1 if i == 1 else 0)
            self.parent.columnconfigure(i, weight=1 if i == 1 else 0)

    def clear(self):
        for entry in list(self._entries):
            try:
                entry["widget"].grid_forget()
            except tk.TclError:
                pass
        self._entries.clear()


class AuiManager:
    def __init__(self, managed_window=None, agwFlags=None):
        self._frame = None
        self._panes = []
        self._notebooks = []
        self._docks = []
        self._uiparts = []
        self._art = None
        self._agwFlags = AUI_MGR_DEFAULT if agwFlags is None else agwFlags
        self._active_pane = None
        self._updating = False
        self._dock_hosts = {}
        self._layout = None
        if managed_window is not None:
            self.SetManagedWindow(managed_window)

    def GetArtProvider(self):
        return self._art

    def SetArtProvider(self, art):
        self._art = art

    def GetAGWFlags(self):
        return self._agwFlags

    def SetAGWFlags(self, flags):
        self._agwFlags = flags

    def GetManagedWindow(self):
        return self._frame

    def GetFrame(self):
        return self._frame

    def SetFrame(self, frame):
        self._frame = frame

    def SetManagedWindow(self, managed_window):
        if managed_window is None:
            raise ValueError("managed_window ne peut pas être None")
        self.UnInit()
        self._frame = managed_window
        if isinstance(managed_window, tk.Misc):
            managed_window.bind("<Configure>", self.OnSize, add="+")
            managed_window.bind("<Destroy>", self._on_destroy_event, add="+")
        return True

    def _on_destroy_event(self, event):
        if event.widget is self._frame:
            self.UnInit()

    def GetPaneByWidget(self, window):
        return next(
            (pane for pane in self._panes if pane.window is window), NonePaneInfo
        )

    def GetPaneByName(self, name):
        return next((pane for pane in self._panes if pane.name == name), NonePaneInfo)

    def GetPane(self, item):
        return (
            self.GetPaneByName(item)
            if isinstance(item, str)
            else self.GetPaneByWidget(item)
        )

    def GetAllPanes(self):
        return self._panes

    def AddPane(self, window, arg1=None, arg2=None, target=None):
        if isinstance(arg1, int):
            return self.AddPane2(window, arg1, arg2 or "")
        if target is not None:
            return self.AddPane4(window, arg1, target)
        return self.AddPane1(window, arg1)

    def AddPane1(self, window, pane_info=None):
        pane = pane_info or AuiPaneInfo()
        pane.window = pane.window or window
        if not pane.name:
            base = pane.caption.strip() or "pane"
            name = base
            index = 0
            while any(item.name == name for item in self._panes):
                index += 1
                name = f"{base}_{index}"
            pane.name = name
        self._panes.append(pane)
        self.Update()
        return pane

    def AddPane2(self, window, direction=AUI_DOCK_LEFT, caption=""):
        pane = (
            AuiPaneInfo()
            .Window(window)
            .Caption(caption)
            .Direction(direction)
            .DefaultPane()
        )
        return self.AddPane1(window, pane)

    def AddPane3(self, window, direction=AUI_DOCK_LEFT, pos=(0, 0)):
        pane = self.AddPane2(window, direction)
        pane.floating_pos = pos
        return pane

    def AddPane4(self, window, pane_info, target):
        pane = self.AddPane1(window, pane_info)
        pane.notebook_id = 0 if target else -1
        return pane

    def InsertPane(self, window, pane_info, direction=AUI_DOCK_LEFT):
        pane = pane_info or AuiPaneInfo()
        pane.window = window
        self._panes.insert(0, pane)
        self.Update()
        return pane

    def DetachPane(self, window):
        pane = self.GetPane(window)
        if pane.IsOk():
            self._undock_pane(pane)
            self._panes.remove(pane)
            pane.window = None
            self.Update()

    def ClosePane(self, pane):
        self._undock_pane(pane)
        if pane.frame is not None:
            pane.frame.destroy()
            pane.frame = None
        window = pane.window
        if window is not None and pane.IsDestroyOnClose():
            window.destroy()
        if pane in self._panes:
            self._panes.remove(pane)
        self.Update()

    def ShowPane(self, window, show=True):
        pane = self.GetPane(window)
        if pane.IsOk():
            pane.Show(show)
            self.Update()

    def ActivatePane(self, pane):
        self._active_pane = pane

    def CreateNotebook(self, parent=None):
        notebook = AuiNotebook(parent or self._frame)
        self._notebooks.append(notebook)
        return notebook

    def GetNotebooks(self):
        return self._notebooks

    def SetMasterManager(self, manager):
        self._masterManager = manager

    def SetAutoNotebookTabArt(self, art):
        self._autoNBTabArt = art

    def GetAutoNotebookTabArt(self):
        return getattr(self, "_autoNBTabArt", None)

    def SetAutoNotebookStyle(self, style):
        self._autoNBStyle = style

    def GetAutoNotebookStyle(self):
        return getattr(self, "_autoNBStyle", AUI_NB_DEFAULT_STYLE)

    def UpdateNotebook(self, notebook=None):
        return None

    def SavePaneInfo(self, pane):
        return json.dumps(
            {
                "name": pane.name,
                "caption": pane.caption,
                "state": pane.state,
                "dir": pane.dock_direction,
                "layer": pane.dock_layer,
                "row": pane.dock_row,
                "pos": pane.dock_pos,
                "prop": pane.dock_proportion,
                "best": list(pane.best_size),
                "min": list(pane.min_size),
                "max": list(pane.max_size),
                "floatpos": list(pane.floating_pos),
                "floatsize": list(pane.floating_size),
                "notebookid": pane.notebook_id,
                "transparent": pane.transparent,
            }
        )

    def LoadPaneInfo(self, pane_part, pane):
        try:
            data = json.loads(pane_part)
        except (TypeError, ValueError):
            return pane
        pane.name = data.get("name", pane.name)
        pane.caption = data.get("caption", pane.caption)
        pane.state = data.get("state", pane.state)
        pane.dock_direction = data.get("dir", pane.dock_direction)
        pane.dock_layer = data.get("layer", pane.dock_layer)
        pane.dock_row = data.get("row", pane.dock_row)
        pane.dock_pos = data.get("pos", pane.dock_pos)
        pane.dock_proportion = data.get("prop", pane.dock_proportion)
        pane.best_size = tuple(data.get("best", pane.best_size))
        pane.min_size = tuple(data.get("min", pane.min_size))
        pane.max_size = tuple(data.get("max", pane.max_size))
        pane.floating_pos = tuple(data.get("floatpos", pane.floating_pos))
        pane.floating_size = tuple(data.get("floatsize", pane.floating_size))
        pane.notebook_id = data.get("notebookid", pane.notebook_id)
        pane.transparent = data.get("transparent", pane.transparent)
        return pane

    def SavePerspective(self):
        return json.dumps(
            {"panes": [json.loads(self.SavePaneInfo(pane)) for pane in self._panes]}
        )

    def LoadPerspective(self, layout):
        try:
            data = json.loads(layout)
        except (TypeError, ValueError):
            return False
        for item in data.get("panes", []):
            pane = AuiPaneInfo()
            self.LoadPaneInfo(json.dumps(item), pane)
            self._panes.append(pane)
        self.Update()
        return True

    def _direction(self, pane):
        return {
            AUI_DOCK_LEFT: "left",
            AUI_DOCK_RIGHT: "right",
            AUI_DOCK_TOP: "top",
            AUI_DOCK_BOTTOM: "bottom",
        }.get(pane.dock_direction, "top")

    def _host_for(self, pane):
        if self._layout is None:
            self._layout = TtkGridLayout(self._frame)
        return self._layout.root

    def _placement_for(self, pane):
        position = self._direction(pane)
        position = {
            "left": "gauche",
            "right": "droite",
            "top": "au-dessus",
            "bottom": "en-dessous",
        }.get(position, "centre")
        return TtkPanePlacement("global", position, getattr(pane, "dock_pos", "last"))

    def _undock_pane(self, pane):
        window = pane.window
        if window is None:
            return
        if self._layout is not None:
            self._layout.remove(window)
        for method in ("pack_forget", "grid_forget", "place_forget"):
            try:
                getattr(window, method)()
            except (AttributeError, tk.TclError):
                pass

    def _float_pane(self, pane):
        if pane.frame is None or not pane.frame.winfo_exists():
            pane.frame = tk.Toplevel(self._frame)
        floating = pane.frame
        floating.title(pane.caption or pane.name)
        self._undock_pane(pane)
        window = pane.window
        if window is not None:
            try:
                window.pack_forget()
            except (AttributeError, tk.TclError):
                pass
            try:
                window.configure(in_=floating)
            except (AttributeError, tk.TclError):
                pass
            window.pack(fill="both", expand=True)
        if pane.floating_pos:
            floating.geometry(f"+{pane.floating_pos[0]}+{pane.floating_pos[1]}")
        if pane.floating_size and pane.floating_size[0] > 0:
            floating.geometry(f"{pane.floating_size[0]}x{pane.floating_size[1]}")
        return floating

    def _dock_pane(self, pane):
        window = pane.window
        if window is None:
            return
        if pane.frame is not None and pane.frame.winfo_exists():
            pane.frame.withdraw()
        if self._layout is None:
            self._layout = TtkGridLayout(self._frame)
        if not any(e["widget"] is window for e in self._layout._entries):
            self._layout.add(window, pane)

    def Update(self):
        if self._updating:
            return
        self._updating = True
        try:
            for pane in self._panes:
                if pane.window is None:
                    continue
                if pane.IsFloating():
                    self._float_pane(pane)
                elif pane.IsShown():
                    self._dock_pane(pane)
                else:
                    self._undock_pane(pane)
        finally:
            self._updating = False

    def LayoutAll(self):
        self.Update()

    def OnSize(self, event=None):
        self.Update()

    def RecalculatePaneSizes(self):
        return None

    def Render(self):
        return None

    def FloatPane(self, pane):
        """Détache le contenu du panneau et l'affiche dans un Toplevel."""
        if not pane.IsOk():
            return None
        pane.Float()
        self.Update()
        return pane.frame

    def DockPane(self, pane):
        """Réintègre le contenu du panneau dans sa zone d'amarrage."""
        if not pane.IsOk():
            return False
        pane.Dock()
        self.Update()
        return True

    def CreateFloatingFrame(self, pane):
        return self._float_pane(pane)

    def Initialize(self):
        return self.Update()

    def UnInit(self):
        for pane in getattr(self, "_panes", []):
            if pane.frame is not None:
                try:
                    pane.frame.destroy()
                except tk.TclError:
                    pass
                pane.frame = None
        if self._layout is not None:
            self._layout.clear()
            try:
                self._layout.root.destroy()
            except tk.TclError:
                pass
            self._layout = None
        self._dock_hosts = {}

    def OnDestroy(self):
        self.UnInit()


class AuiManager_DCP(AuiManager):
    pass
