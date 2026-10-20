# -*- coding: utf-8 -*-
"""Troisième étape de la conversion de framemanager.py vers Tkinter : AuiManager.

Cette version conserve l'API publique d'AuiManager : gestion des panneaux,
amarrage simple, flottant, sérialisation de la perspective et événements.
La disposition Tkinter est réalisée avec pack/place pour les panneaux amarrés
et avec des Toplevel pour les panneaux flottants.
"""

import json
import tkinter as tk
from .tkframemanager_elements import (
    AuiDockInfo,
    AuiDockingGuideInfo,
    AuiDockUIPart,
    AuiPaneButton,
    AuiManagerEvent,
    AuiPaneInfo,
)
from .tkframemanager_floating import AuiFloatingFrame
from .tkdockart import AuiDefaultDockArt
from .tkauitoolbar import AuiToolBar
from .aui_tk_constants import *

NonePaneInfo = AuiPaneInfo()


def _EscapeDelimiters(s):
    return s.replace("|", "\\|").replace(";", "\\;")


class AuiManager:
    def __init__(self, managed_window=None, agwFlags=None):
        self._action = actionNone
        self._action_window = None
        self._hover_button = None
        self._art = AuiDefaultDockArt()
        self._hint_window = None
        self._active_pane = None
        self._has_maximized = False
        self._has_minimized = False
        self._frame = None
        self._dock_constraint_x = 0.3
        self._dock_constraint_y = 0.3
        self._reserved = None
        self._panes = []
        self._docks = []
        self._uiparts = []
        self._guides = []
        self._notebooks = []
        self._masterManager = None
        self._currentDragItem = -1
        self._lastknowndocks = {}
        self._hint_fadetimer = None
        self._hint_fademax = 50
        self._last_hint = (0, 0, 0, 0)
        self._from_move = False
        self._last_rect = (0, 0, 0, 0)
        self._agwFlags = AUI_MGR_DEFAULT if agwFlags is None else agwFlags
        self._is_docked = (False, AUI_DOCK_RIGHT, AUI_DOCK_TOP, 0)
        self._snap_limits = (15, 15)
        self._animation_step = 30.0
        self._hint_rect = (0, 0, 0, 0)
        self._preview_timer = None
        self._sliding_frame = None
        self._autoNBTabArt = None
        self._autoNBStyle = AUI_NB_DEFAULT_STYLE
        if managed_window:
            self.SetManagedWindow(managed_window)

    # -- basic accessors -------------------------------------------------
    def GetArtProvider(self):
        return self._art

    def SetArtProvider(self, art):
        self._art = art

    def GetAGWFlags(self):
        return self._agwFlags

    def SetAGWFlags(self, flags):
        self._agwFlags = flags
        if self._frame and not (self._agwFlags & AUI_MGR_ALLOW_FLOATING):
            for p in self._panes:
                if p.IsFloating() and p.IsToolbar():
                    p.Dock()

    def GetManagedWindow(self):
        return self._frame

    def SetManagedWindow(self, managed_window):
        if not managed_window:
            raise Exception("Specified managed window must be non-null. ")
        self.UnInit()
        self._frame = managed_window
        if isinstance(managed_window, tk.Misc):
            managed_window.bind("<Configure>", self.OnSize, add="+")
            # managed_window.bind("<Destroy>", lambda e: self.OnDestroy(), add="+")
            managed_window.bind("<Destroy>", self._on_destroy_event, add="+")
        self._canvas = None
        return True

    def _on_destroy_event(self, event):
        # Un <Destroy> se déclenche aussi pour chaque widget détruit DANS la
        # fenêtre gérée (le toplevel figure dans les bindtags de ses
        # descendants). On ne reinitialise que si la fenetre gérée
        # est elle-meme détruite.
        if event.widget is self._frame:
            self.OnDestroy()

    def GetFrame(self):
        return self._frame

    def SetFrame(self, frame):
        self._frame = frame

    # -- pane lookup ------------------------------------------------------
    def GetPaneByWidget(self, window):
        return next((p for p in self._panes if p.window == window), NonePaneInfo)

    def GetPaneByName(self, name):
        return next((p for p in self._panes if p.name == name), NonePaneInfo)

    def GetPane(self, item):
        return (
            self.GetPaneByName(item)
            if isinstance(item, str)
            else self.GetPaneByWidget(item)
        )

    def GetAllPanes(self):
        return self._panes

    # -- add/insert --------------------------------------------------------
    def AddPane(self, window, arg1=None, arg2=None, target=None):
        if isinstance(arg1, int):
            return self.AddPane2(window, arg1, arg2 or "")
        if target is not None:
            return self.AddPane4(window, arg1, target)
        return self.AddPane1(window, arg1)

    def AddPane1(self, window, pane_info=None):
        p = pane_info or AuiPaneInfo()
        if not p.window:
            p.window = window
        # if p.name == "" or any(x.name == p.name for x in self._panes):
        #     p.name = f"pane_{len(self._panes)}"
        if not p.name:
            # nom derive de la legende (recherche par nom possible),
            # sinon compteur ; suffixe _N si le nom est deja pris
            base = p.caption.strip() or "pane"
            candidate = base
            index = 0
            while any(x.name == candidate for x in self._panes):
                index += 1
                candidate = "%s_%d" % (base, index)
            p.name = candidate
        self._panes.append(p)
        self.Update()
        return p

    def AddPane2(self, window, direction=AUI_DOCK_LEFT, caption=""):
        p = (
            AuiPaneInfo()
            .Window(window)
            .Caption(caption)
            .Direction(direction)
            .DefaultPane()
        )
        return self.AddPane1(window, p)

    def AddPane3(self, window, direction=AUI_DOCK_LEFT, pos=(0, 0)):
        p = self.AddPane2(window, direction, "")
        p.floating_pos = pos
        return p

    def AddPane4(self, window, pane_info, target):
        p = self.AddPane1(window, pane_info)
        p.notebook_id = 0 if target else -1
        return p

    def InsertPane(self, window, pane_info, direction=AUI_DOCK_LEFT):
        p = pane_info or AuiPaneInfo()
        p.window = window
        self._panes.insert(0, p)
        self.Update()
        return p

    def DetachPane(self, window):
        p = self.GetPane(window)
        if p.IsOk():
            self._panes.remove(p)
            p.window = None
            self.Update()

    def ClosePane(self, pane):
        if pane.frame:
            pane.frame.destroy()
            pane.frame = None
        if pane.window and pane.IsDestroyOnClose():
            pane.window.destroy() if hasattr(pane.window, "destroy") else None
        self.DetachPane(pane.window)

    # -- pane state ---------------------------------------------------------
    def ShowPane(self, window, show=True):
        p = self.GetPane(window)
        if p.IsOk():
            p.Show(show)
            self.Update()

    def MaximizePane(self, panes):
        for p in self._panes:
            p.SetFlag(AuiPaneInfo.optionHidden, p is not panes)
        self.Update()

    def RestorePane(self, pane):
        pane.Show()
        self.Update()

    def RestoreMaximizedPane(self):
        self.MaximizePane(None)

    def ActivatePane(self, pane):
        self._active_pane = pane

    # -- notebooks ------------------------------------------------------------
    def CreateNotebook(self):
        from .tkauibook import AuiNotebook

        nb = AuiNotebook(self._frame)
        self._notebooks.append(nb)
        return nb

    def SetAutoNotebookTabArt(self, art):
        self._autoNBTabArt = art

    def GetAutoNotebookTabArt(self):
        return self._autoNBTabArt

    def SetAutoNotebookStyle(self, style):
        self._autoNBStyle = style

    def GetAutoNotebookStyle(self):
        return self._autoNBStyle

    def GetNotebooks(self):
        return self._notebooks

    def SetMasterManager(self, mgr):
        self._masterManager = mgr

    def UpdateNotebook(self, notebook=None):
        for nb in self._notebooks:
            nb.DoSizing() if hasattr(nb, "DoSizing") else None

    # -- serialization ----------------------------------------------------------
    def SavePaneInfo(self, pane):
        d = {
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
        return json.dumps(d)

    def LoadPaneInfo(self, pane_part, pane):
        try:
            d = json.loads(pane_part)
        except ValueError:
            return pane
        pane.name = d.get("name", pane.name)
        pane.caption = d.get("caption", pane.caption)
        pane.state = d.get("state", pane.state)
        pane.dock_direction = d.get("dir", pane.dock_direction)
        pane.dock_layer = d.get("layer", pane.dock_layer)
        pane.dock_row = d.get("row", pane.dock_row)
        pane.dock_pos = d.get("pos", pane.dock_pos)
        pane.dock_proportion = d.get("prop", pane.dock_proportion)
        pane.best_size = tuple(d.get("best", pane.best_size))
        pane.min_size = tuple(d.get("min", pane.min_size))
        pane.max_size = tuple(d.get("max", pane.max_size))
        pane.floating_pos = tuple(d.get("floatpos", pane.floating_pos))
        pane.floating_size = tuple(d.get("floatsize", pane.floating_size))
        pane.notebook_id = d.get("notebookid", pane.notebook_id)
        pane.transparent = d.get("transparent", pane.transparent)
        return pane

    def SavePerspective(self):
        return json.dumps(
            {"panes": [json.loads(self.SavePaneInfo(p)) for p in self._panes]}
        )

    def LoadPerspective(self, layout):
        try:
            d = json.loads(layout)
        except ValueError:
            return False
        for pd in d.get("panes", []):
            p = AuiPaneInfo()
            self.LoadPaneInfo(json.dumps(pd), p)
            p.window = None
            self._panes.append(p)
        self.Update()
        return True

    # -- layout / update ---------------------------------------------------------
    def LayoutAll(self):
        pass

    # def Update(self):
    #     for p in self._panes:
    #         w = p.window
    #         if w is None:
    #             continue
    #         if p.IsFloating():
    #             if p.frame is None:
    #                 p.frame = AuiFloatingFrame(self._frame, self, p)
    #         else:
    #             if p.frame:
    #                 p.frame.destroy()
    #                 p.frame = None
    #             if isinstance(w, tk.Misc):
    #                 if p.IsShown():
    #                     side = {
    #                         AUI_DOCK_TOP: "top",
    #                         AUI_DOCK_BOTTOM: "bottom",
    #                         AUI_DOCK_LEFT: "left",
    #                         AUI_DOCK_RIGHT: "right",
    #                     }.get(p.dock_direction, "top")
    #                     if p.HasCaption() and not hasattr(w, "_aui_caption"):
    #                         cap = tk.Frame(self._frame)
    #                         cap.pack(side=side, fill="x", before=w)
    #                         tk.Label(cap, text=p.caption).pack(side="left", padx=4)
    #                         w._aui_caption = cap
    #                     w.pack(side=side, fill="both", expand=not p.IsToolbar())
    #                 else:
    #                     w.pack_forget()
    #     self.Render()

    def Update(self):
        if getattr(self, '_updating', False):
            return
        self._updating = True
        try:
            for p in self._panes:
                w = p.window
                if w is None:
                    continue
                if p.IsFloating():
                    if p.frame is None and self._frame is not None:
                        p.frame = AuiFloatingFrame(self._frame, self, p)
                else:
                    if p.frame is not None:
                        frame = p.frame
                        p.frame = None
                        if hasattr(frame, 'destroy'):
                            frame.destroy()
                    if isinstance(w, tk.Misc):
                        cap = getattr(w, '_aui_caption', None)
                        if p.IsShown():
                            w.pack_forget()
                            if cap is not None:
                                cap.pack_forget()
                            side = {AUI_DOCK_TOP: 'top',
                                    AUI_DOCK_BOTTOM: 'bottom',
                                    AUI_DOCK_LEFT: 'left',
                                    AUI_DOCK_RIGHT: 'right'}.get(p.dock_direction, 'top')
                            if p.HasCaption():
                                if cap is None:
                                    cap = tk.Frame(w.master)
                                    tk.Label(cap, text=p.caption).pack(side='left', padx=4)
                                    w._aui_caption = cap
                                cap.pack(side=side, fill='x')
                            w.pack(side=side, fill='both', expand=not p.IsToolbar())
                        else:
                            w.pack_forget()
                            if cap is not None:
                                cap.pack_forget()
        finally:
            self._updating = False
        self.Render()

    def DoUpdateEvt(self, event=None):
        self.Update()

    def DoUpdate(self):
        self.Update()

    def UpdateHintWindowSize(self):
        pass

    # -- docks -----------------------------------------------------------------
    def SetDockSizeConstraint(self, x, y):
        self._dock_constraint_x = x
        self._dock_constraint_y = y

    def GetDockSizeConstraint(self):
        return self._dock_constraint_x, self._dock_constraint_y

    def HitTest(self, x, y):
        return None

    def PaneHitTest(self, x, y):
        return None

    # -- events -----------------------------------------------------------------
    def ProcessMgrEvent(self, evt):
        pass

    def FireEvent(self, evt_type, pane=None, can_veto=True):
        evt = AuiManagerEvent(self, pane)
        evt.SetCanVeto(can_veto)
        return evt

    def OnClose(self, event=None):
        for p in list(self._panes):
            if p.frame:
                p.frame.destroy()
        self.UnInit()
        event.Skip() if hasattr(event, "Skip") else None

    def OnDestroy(self):
        self.UnInit()

    def UnInit(self):
        for p in self._panes:
            if p.frame:
                p.frame.destroy()
                p.frame = None
        self._panes.clear()
        self._docks.clear()
        self._uiparts.clear()

    def OnFloatingPaneResized(self, pane, event=None):
        self.Update()

    def OnFloatingPaneClosed(self, pane, event=None):
        return True

    def OnFloatingPaneActivated(self, pane, event=None):
        self.ActivatePane(self.GetPane(pane))

    def OnFloatingPaneMoved(self, pane, event=None):
        pass

    # -- render ------------------------------------------------------------------
    def GetPanePart(self, pane):
        return None

    def OnRender(self, event=None):
        self.Render()
        return True

    def Repaint(self):
        self.Render()

    def Render(self, dc=None):
        pass

    def OnPaint(self, event=None):
        pass

    def OnEraseBackground(self, event):
        pass

    def OnSize(self, event=None):
        self.Update()

    def OnSetCursor(self, event=None):
        pass

    def OnLeftDown(self, event=None):
        pass

    def OnLeftDClick(self, event=None):
        pass

    def OnLeftUp(self, event=None):
        pass

    def OnMotion(self, event=None):
        pass

    def OnLeaveWindow(self, event=None):
        pass

    def OnChildFocus(self, event=None):
        pass

    def OnCaptureLost(self, event=None):
        pass

    def OnHintFadeTimer(self, event=None):
        pass

    def OnMove(self, event=None):
        pass

    def OnSysColourChanged(self, event=None):
        pass

    def OnFindManager(self, event=None):
        pass

    def OnTabBeginDrag(self, event=None):
        pass

    def OnTabEndDrag(self, event=None):
        pass

    def OnTabPageClose(self, event=None):
        pass

    def OnTabSelected(self, event=None):
        pass

    def OnPaneButton(self, event=None):
        pass

    def OnPaneDocked(self, event=None):
        pass

    def OnRestoreMinimizedPane(self, event=None):
        pass

    def OnGripperClicked(self, event=None):
        pass

    def OnCaptionDoubleClicked(self, event=None):
        pass

    def CanDockPanel(self, pane):
        return False

    def CreateFloatingFrame(self, pane):
        return AuiFloatingFrame(self._frame, self, pane)

    def CreateGuideWindows(self):
        pass

    def DestroyGuideWindows(self):
        pass

    def CreateHintWindow(self):
        pass

    def DestroyHintWindow(self):
        pass

    def ShowHint(self, rect):
        return False

    def HideHint(self):
        pass

    def SnapPane(self, pane):
        pass

    def RepositionPane(self, pane, move_pane):
        pass

    def MinimizePane(self, pane):
        pass

    def RestoreMinimizedPane(self, pane):
        pass

    def AnimateDocking(self, pane):
        return False

    def SmoothDock(self, pane):
        return False

    def SetSnapLimits(self, limit):
        self._snap_limits = limit

    def Snap(self, pane):
        return False

    def SnapToScreen(self, pane):
        return False

    def GetSnapPosition(self, pane):
        return None

    def GetAnimationStep(self):
        return self._animation_step

    def SetAnimationStep(self, step):
        self._animation_step = step

    def RequestUserAttention(self, pane):
        pass

    def StartPreviewTimer(self):
        pass

    def StopPreviewTimer(self):
        pass

    def SlideIn(self, event=None):
        pass

    def SlideOut(self):
        pass

    def SavePreviousDockSizes(self):
        pass

    def CopyTarget(self, target, newPos):
        return target

    def DoDrop(self, target, pane, pt, offset):
        return False

    def DoDropToolbar(self, target, pane, pt, offset):
        return False

    def DoDropFloatingPane(self, target, pane, pt):
        return False

    def DoDropNonFloatingPane(self, target, pane, pt, offset):
        return False

    def DoDropLayer(self, target, pane, pt, offset):
        return False

    def DoDropPane(self, target, pane, pt, offset):
        return False

    def DoDropRow(self, target, pane, pt, offset):
        return False

    def SwitchToolBarOrientation(self, toolbar):
        pass

    def GetPanePositionsAndSizes(self):
        return []

    def LayoutAddPane(self, dc, pane, uiparts, after):
        pass

    def LayoutAddDock(self, dc, dock, uiparts, after):
        pass

    def DoFrameLayout(self):
        pass

    def GetDockPixelOffset(self, target):
        return 0

    def GetPartnerDock(self, target):
        return None

    def GetPartnerPane(self, target, pane):
        return None

    def GetTotalPixSizeAndProportion(self, panes, total):
        return total

    def GetOppositeDockTotalSize(self, target):
        return 0

    def CalculateDockSizerLimits(self, target):
        return 0

    def CalculatePaneSizerLimits(self, target, pane):
        return 0

    def CheckMovableSizer(self):
        return False

    def PaneFromTabEvent(self, event):
        return None

    def ProcessDockResult(self, target, pane):
        return False

    def IsPaneButtonVisible(self, pane, button_id):
        return False

    def DrawPaneButton(self, dc, pane, button, event):
        pass

    def RefreshButton(self, pane, button):
        pass

    def RefreshCaptions(self):
        pass

    def CalculateHintRect(self, pane, screenPt, offset):
        return (0, 0, 0, 0)

    def DrawHintRect(self, dc, pane, screenPt, offset):
        pass

    def GetPartSizerRect(self, uipart):
        return (0, 0, 0, 0)

    def GetAttributes(self):
        return {}

    def SetAttributes(self, attrs):
        pass


class AuiManager_DCP(AuiManager):
    """Gestionnaire AUI avec panneau central factice (Dummy Center Pane)."""

    def __init__(self, *args, **keys):
        super().__init__(*args, **keys)
        self.hasDummyPane = False

    def _createDummyPane(self):
        if self.hasDummyPane:
            return
        self.hasDummyPane = True
        dummy = tk.Frame(self.GetManagedWindow()) if self.GetManagedWindow() else None
        info = (
            AuiPaneInfo()
            .CenterPane()
            .NotebookDockable(True)
            .Name("dummyCenterPane")
            .DestroyOnClose(True)
        )
        if dummy is not None:
            self.AddPane(dummy, info)

    def _destroyDummyPane(self):
        if not self.hasDummyPane:
            return
        self.hasDummyPane = False
        self.ClosePane(self.GetPane("dummyCenterPane"))

    def Update(self):
        super().Update()
        dummy = self.GetPane("dummyCenterPane")
        haveCenterPane = any(
            (p is not dummy)
            and p.dock_direction == AUI_DOCK_CENTER
            and not p.IsFloating()
            and p.IsShown()
            for p in self.GetAllPanes()
        )
        if haveCenterPane:
            if self.hasDummyPane:

                def do():
                    self._destroyDummyPane()
                    super(AuiManager_DCP, self).Update()

                self._frame.after_idle(do) if self._frame else do()
        else:
            if not self.hasDummyPane:

                def do():
                    self._createDummyPane()
                    super(AuiManager_DCP, self).Update()

                self._frame.after_idle(do) if self._frame else do()
