#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from .wxSchedulerCore import *
import time
import wx
import wx.lib.scrolledpanel as scrolled
from .wxSchedulerCore import wxSchedulerCore
from . import wxSchedule


class wxScheduler(wxSchedulerCore, scrolled.ScrolledPanel):
    """
    wxScheduler - Composant de planification pour wxPython
    
    Ce module fournit la classe principale `wxSchedule`, utilisée pour représenter et manipuler des événements de planning dans une application wxPython. Il inclut également la gestion des notifications d'événements personnalisés et diverses propriétés associées à une planification (catégorie, couleur, police, état, etc.).
    
    Fonctionnalités principales :
    - Définition d'un événement ou d'une tâche planifiée avec date/heure de début et de fin (`start`, `end`).
    - Gestion de catégories prédéfinies (Travail, Congé, Anniversaire, etc.), couleurs associées, et autres attributs visuels.
    - Support complet des propriétés : description, notes, état d’achèvement, données client, icônes, etc.
    - Possibilité de sérialiser et cloner un événement via `GetData()` et `Clone()`.
    - Système d’événement personnalisé pour notifier l’application des changements sur une planification (événement `EVT_SCHEDULE_CHANGE`).
    - Méthodes utilitaires pour geler/dégeler les notifications, décaler un événement dans le temps, comparer deux événements, etc.
    
    Utilisation :
    - Instancier un objet `wxSchedule`.
    - Définir les propriétés souhaitées (dates, catégorie, description...).
    - Attacher des gestionnaires d’événements pour réagir aux modifications de planning dans l’interface wxPython.
    
    Ce module est destiné à être intégré dans des applications wxPython nécessitant la gestion d’événements calendaires avancés, comme des gestionnaires de tâches ou d’agendas visuels.
    
    Dépendances :
    - wxPython pour l’interface graphique.
    - Le module compagnon `wxScheduleUtils` pour certaines opérations utilitaires sur les dates.
    
    Auteur : Inspiré par les besoins des gestionnaires de tâches graphiques, adapté pour Task Coach.
    """

    def __init__(self, *args, **kwds):
        """
        Utiliser self.start et self.end pour définir le début et la fin de la planification.
        Si les deux dates/horaires sont à 00:00, la planification est considérée comme relative à la ou les journées entières.
        """
        kwds["style"] = wx.TAB_TRAVERSAL | wx.FULL_REPAINT_ON_RESIZE

        super().__init__(*args, **kwds)

        # timerId = wx.NewId()
        # NewId is deprecieted
        # timerId = wx.NewIdRef()
        timerId = wx.ID_ANY
        self._sizeTimer = wx.Timer(self, timerId)

        self._frozen = False
        self._dirty = False
        self._refreshing = False

        self._showNow = True
        # self._refreshTimer = wx.Timer(self, wx.NewId() )
        # NewId is deprecieted
        # self._refreshTimer = wx.Timer(self, wx.NewIdRef())
        self._refreshTimer = wx.Timer(self, wx.ID_ANY)
        self._refreshTimer.Start(int(1000 * (60 - (time.time() % 60))), True)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnClickEnd)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_TIMER, self.OnSizeTimer, id=timerId)
        self.Bind(wx.EVT_TIMER, self.OnRefreshTimer, id=self._refreshTimer.GetId())

        self.SetScrollRate(10, 10)

    # Events
    def OnClick(self, evt):
        self._doClickControl(self._getEventCoordinates(evt), shiftDown=evt.ShiftDown())

    def OnClickEnd(self, evt):
        self._doEndClickControl(self._getEventCoordinates(evt))

    def OnMotion(self, evt):
        self._doMove(self._getEventCoordinates(evt))

    def OnRightClick(self, evt):
        self._doRightClickControl(self._getEventCoordinates(evt))

    def OnDClick(self, evt):
        self._doDClickControl(self._getEventCoordinates(evt))

    def OnSize(self, evt):
        if not self._refreshing:
            self._sizeTimer.Start(250, True)
        evt.Skip()

    def OnSizeTimer(self, evt):
        self._refreshing = True
        try:
            self.InvalidateMinSize()
            self.Refresh()
            try:
                wx.Yield()
            except Exception:
                pass
        finally:
            self._refreshing = False

    def OnRefreshTimer(self, evt):
        self.Refresh()
        self._refreshTimer.Start(60000, True)

    def Add(self, *args, **kwds):
        wxSchedulerCore.Add(self, *args, **kwds)
        self._controlBindSchedules()

    def Refresh(self):
        if self._frozen:
            self._dirty = True
        else:
            self.DrawBuffer()
            self.GetSizer().FitInside(self)
            super().Refresh()
            self._dirty = False

    def Freeze(self):
        # Freeze the event notification
        self._frozen = True

    def Thaw(self):
        # Wake up the event
        self._frozen = False
        if self._dirty:
            self.Refresh()

    def SetResizable(self, value):
        """ Call derived method and force wxDC refresh. """
        super().SetResizable(value)
        self.InvalidateMinSize()
        self.Refresh()

    def OnScheduleChanged(self, event):
        if self._frozen:
            self._dirty = True
        else:
            if event.layoutNeeded:
                self.Refresh()
            else:
                self.RefreshSchedule(event.schedule)

    def _controlBindSchedules(self):
        """ Control if all the schedules into self._schedules have its EVT_SCHEDULE_CHANGE binded. """
        currentSc = set(self._schedules)
        bindSc = set(self._schBind)

        for sc in (currentSc - bindSc):
            sc.Bind(wxSchedule.EVT_SCHEDULE_CHANGE, self.OnScheduleChanged)
            self._schBind.append(sc)

    def _getEventCoordinates(self, event):
        """ Return the coordinates associated with the given mouse event.

        The coordinates have to be adjusted to allow for the current scroll
        position.
"""
        originX, originY = self.GetViewStart()
        unitX, unitY = self.GetScrollPixelsPerUnit()

        coords = wx.Point(
            event.GetX() + (originX * unitX),
            event.GetY() + (originY * unitY)
        )

        return coords

    def SetViewType(self, view=None):
        super().SetViewType(view)
        self.InvalidateMinSize()
        self.Refresh()

    def SetShowNow(self, show=True):
        self._showNow = show

        if show:
            self._refreshTimer.Start(int(1000 * (60 - (time.time() % 60))), True)
        else:
            self._refreshTimer.Stop()

        self.Refresh()

    def GetShowNow(self):
        return self._showNow
