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
        """Gère le clic gauche de la souris sur le planning."""
        self._doClickControl(self._getEventCoordinates(evt), shiftDown=evt.ShiftDown())

    def OnClickEnd(self, evt):
        """Gère la fin du clic gauche de la souris (relâchement) sur le planning."""
        self._doEndClickControl(self._getEventCoordinates(evt))

    def OnMotion(self, evt):
        """Gère le mouvement de la souris sur le planning."""
        self._doMove(self._getEventCoordinates(evt))

    def OnRightClick(self, evt):
        """Gère le clic droit de la souris sur le planning."""
        self._doRightClickControl(self._getEventCoordinates(evt))

    def OnDClick(self, evt):
        """Gère le double-clic gauche de la souris sur le planning."""
        self._doDClickControl(self._getEventCoordinates(evt))

    def OnSize(self, evt):
        """Gère le redimensionnement du composant et déclenche un ajustement différé."""
        if not self._refreshing:
            self._sizeTimer.Start(250, True)
        evt.Skip()

    def OnSizeTimer(self, evt):
        """Effectue le recalcul et le rafraîchissement de la vue après un redimensionnement."""
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
        """Rafraîchit l’affichage à chaque minute pour mettre à jour la vue courante."""
        self.Refresh()
        self._refreshTimer.Start(60000, True)

    def Add(self, *args, **kwds):
        """Ajoute un ou plusieurs événements au planning et lie les signaux nécessaires."""
        wxSchedulerCore.Add(self, *args, **kwds)
        self._controlBindSchedules()

    def Refresh(self):
        """Rafraîchit l’affichage du planning si ce n’est pas gelé, sinon marque comme sale."""
        if self._frozen:
            self._dirty = True
        else:
            self.DrawBuffer()
            self.GetSizer().FitInside(self)
            super().Refresh()
            self._dirty = False

    def Freeze(self):
        """Gèle les rafraîchissements du planning (mode pause)."""
        # Freeze the event notification
        self._frozen = True

    def Thaw(self):
        """Dégèle les rafraîchissements du planning et effectue un rafraîchissement différé si nécessaire."""
        # Wake up the event
        self._frozen = False
        if self._dirty:
            self.Refresh()

    def SetResizable(self, value):
        """Appelle la méthode dérivée et force le rafraîchissement wxDC."""
        super().SetResizable(value)
        self.InvalidateMinSize()
        self.Refresh()

    def OnScheduleChanged(self, event):
        """Gère la notification de modification d’un événement planifié."""
        if self._frozen:
            self._dirty = True
        else:
            if event.layoutNeeded:
                self.Refresh()
            else:
                self.RefreshSchedule(event.schedule)

    def _controlBindSchedules(self):
       """Vérifie que tous les objets schedule de self._schedules ont bien leur événement EVT_SCHEDULE_CHANGE associé."""
        currentSc = set(self._schedules)
        bindSc = set(self._schBind)

        for sc in (currentSc - bindSc):
            sc.Bind(wxSchedule.EVT_SCHEDULE_CHANGE, self.OnScheduleChanged)
            self._schBind.append(sc)

    def _getEventCoordinates(self, event):
        """Renvoie les coordonnées associées à l'événement souris donné.
        
        Les coordonnées sont ajustées afin de tenir compte de la position actuelle du scroll.
        """

        originX, originY = self.GetViewStart()
        unitX, unitY = self.GetScrollPixelsPerUnit()

        coords = wx.Point(
            event.GetX() + (originX * unitX),
            event.GetY() + (originY * unitY)
        )

        return coords

    def SetViewType(self, view=None):
        """Change le type de vue du planning (jour, semaine, mois…) et rafraîchit l’affichage."""
        super().SetViewType(view)
        self.InvalidateMinSize()
        self.Refresh()

    def SetShowNow(self, show=True):
        """Affiche ou masque l’indicateur de l’heure courante sur le planning."""
        self._showNow = show
        if show:
            self._refreshTimer.Start(int(1000 * (60 - (time.time() % 60))), True)
        else:
            self._refreshTimer.Stop()

        self.Refresh()

    def GetShowNow(self):
        return self._showNow
