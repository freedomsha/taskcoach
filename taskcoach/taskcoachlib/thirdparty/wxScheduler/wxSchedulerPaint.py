#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .wxSchedule import wxSchedule
from .wxDrawer import wxBaseDrawer, wxFancyDrawer
from .wxSchedulerConstants import wxSCHEDULER_VERTICAL, wxSCHEDULER_HORIZONTAL, DAY_SIZE_MIN, LEFT_COLUMN_SIZE, \
    MONTH_CELL_SIZE_MIN, SCHEDULER_BACKGROUND_BRUSH, FOREGROUND_PEN, WEEK_SIZE_MIN, wxSCHEDULER_DAILY, \
    wxSCHEDULER_WEEKLY, wxSCHEDULER_MONTHLY
# from .wxSchedulerCore import *
import calendar
import math
import sys
import wx
from . import wxScheduleUtils as utils

# if sys.version.startswith( "2.3" ):
# 	from sets import Set as set
# set() est intégré dans python 3
xrange = range

# Events
wxEVT_COMMAND_SCHEDULE_ACTIVATED = wx.NewEventType()
EVT_SCHEDULE_ACTIVATED = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_ACTIVATED)

wxEVT_COMMAND_SCHEDULE_RIGHT_CLICK = wx.NewEventType()
EVT_SCHEDULE_RIGHT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_RIGHT_CLICK)

wxEVT_COMMAND_SCHEDULE_DCLICK = wx.NewEventType()
EVT_SCHEDULE_DCLICK = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_DCLICK)

wxEVT_COMMAND_PERIODWIDTH_CHANGED = wx.NewEventType()
EVT_PERIODWIDTH_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_PERIODWIDTH_CHANGED)


# class wxSchedulerSizer(wx.PySizer):  # PySizer deprecated , use Sizer instead
class wxSchedulerSizer(wx.Sizer):
    """
    Sizer personnalisé pour le planificateur, permettant de calculer dynamiquement la taille minimale grâce à un callback.
    """
    def __init__(self, minSizeCallback):
        """
        Initialise le sizer avec une fonction de rappel pour la taille minimale.
        :param minSizeCallback: Fonction retournant la taille minimale actuelle.
        """
        super().__init__()
        self._minSizeCallback = minSizeCallback

    def CalcMin(self):
        """
        Calcule et retourne la taille minimale à utiliser pour le sizer.
        :return: Taille minimale (wx.Size)
        """
        return self._minSizeCallback()


# Main class
class wxSchedulerPaint(object):
    """
    Classe principale responsable de la gestion du rendu graphique du planificateur (scheduler).
    Gère l'affichage, le dessin, l'interaction avec les événements souris et le redimensionnement.
    """
    def __init__(self, *args, **kwds):
        """
        Initialise les paramètres graphiques, les états d'interaction et les options de rendu du planificateur.
        """
        super().__init__(*args, **kwds)

        self._resizable = False
        self._style = wxSCHEDULER_VERTICAL

        self._drawerClass = wxBaseDrawer
        self._headerPanel = None

        self._schedulesCoords = list()
        self._schedulesPages = dict()

        self._datetimeCoords = []

        self._bitmap = None
        self._minSize = None
        self._drawHeaders = True
        self._guardRedraw = False

        self._periodWidth = 150
        self._headerBounds = []
        self._headerCursorState = 0
        self._headerDragOrigin = None
        self._headerDragBase = None

        # State:
        # 0 None
        # 1 Clicked, waiting for release or drag
        # 2 Dragging
        # 3 hovering up/left edge
        # 4 hovering down/right edge
        # 5 dragging up/left edige
        # 6 dragging down/right edge

        self._scheduleDraggingState = 0
        self._scheduleDragged = None
        self._scheduleDraggingOrigin = None
        self._scheduleDraggingPrevious = None
        self._scheduleDraggingStick = False

        # The highlight colour is too dark
        color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        self._highlightColor = wx.Colour(
            int((color.Red() + 255) / 2),
            int((color.Green() + 255) / 2),
            int((color.Blue() + 255) / 2),
        )

        self.pageNumber = None
        self.pageCount = 1

        if isinstance(self, wx.ScrolledWindow):
            self.SetSizer(wxSchedulerSizer(self.CalcMinSize))

    def _doClickControl(self, point, shiftDown=False):
        """
        Gère le clic de souris sur le planificateur (sélection, début de déplacement/redimensionnement d'un planning).
        :param point: Position du clic (wx.Point)
        :param shiftDown: Indique si la touche Shift était enfoncée
        """
        if self._scheduleDraggingState in [3, 4]:
            self._scheduleDraggingState += 2
            self._scheduleDraggingOrigin = self._computeCoords(point, 0, 0)
            self._scheduleDraggingStick = shiftDown
        else:
            try:
                pMin, pMax, sch = self._findSchedule(point)
            except TypeError:  # returned None
                return
            if isinstance(sch, wxSchedule):
                self._scheduleDragged = pMin, pMax, sch
                self._scheduleDraggingState = 1
                self._scheduleDraggingOrigin = self._computeCoords(point, 0, 0)
                self._scheduleDraggingStick = shiftDown
            else:
                self._processEvt(wxEVT_COMMAND_SCHEDULE_ACTIVATED, point)

    def _doEndClickControl(self, point):
        """
        Gère la fin du clic (relâchement souris) sur le planificateur, finalise le déplacement ou le redimensionnement.
        :param point: Position du relâchement
        """
        if self._scheduleDraggingState == 1:
            self._processEvt(wxEVT_COMMAND_SCHEDULE_ACTIVATED, point)
        elif self._scheduleDraggingState == 2:
            _, dateTime = self._computeCoords(point, 0, 0)

            sched = self._scheduleDragged[2]
            self._drawDragging(None, self._computeAllCoords)
            sched.Offset(dateTime.Subtract(self._scheduleDraggingOrigin[1]))
            self._scheduleDraggingState = 0

        elif self._scheduleDraggingState in [5, 6]:
            coords = {5: self._computeStartCoords, 6: self._computeEndCoords}[
                self._scheduleDraggingState
            ]
            _, _, dateTime = coords(point)

            sched = self._scheduleDragged[2]
            if self._scheduleDraggingState == 5:
                sched.SetStart(utils.copyDateTime(dateTime))
            else:
                sched.SetEnd(utils.copyDateTime(dateTime))

            self._scheduleDraggingState = 0
            self._drawDragging(None, coords)
            self.SetCursor(wx.STANDARD_CURSOR)

        self._scheduleDraggingState = 0
        self._scheduleDragged = None
        self._scheduleDraggingOrigin = None
        self._scheduleDraggingPrevious = None

    def _doMove(self, point):
        """
        Gère le déplacement de la souris sur le planificateur, met à jour l'état de survol/déplacement/redimensionnement.
        :param point: Position actuelle de la souris
        """
        if self._scheduleDraggingState in [0, 3, 4]:
            for sched, pointMin, pointMax in self._schedulesCoords:
                if self._style == wxSCHEDULER_VERTICAL:
                    if pointMin.x < point.x < pointMax.x:
                        if abs(point.y - pointMin.y) < 4:
                            self._scheduleDraggingState = 3
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return
                        if abs(point.y - pointMax.y) < 4:
                            self._scheduleDraggingState = 4
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return
                else:
                    if pointMin.y < point.y < pointMax.y:
                        if abs(point.x - pointMin.x) < 4:
                            self._scheduleDraggingState = 3
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return
                        if abs(point.x - pointMax.x) < 4:
                            self._scheduleDraggingState = 4
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return

            if self._scheduleDraggingState in [3, 4]:
                self._scheduleDraggingState = 0
                self.SetCursor(wx.STANDARD_CURSOR)
                self._scheduleDragged = None
        elif self._scheduleDraggingState in [5, 6]:
            self._drawDragging(
                point,
                {5: self._computeStartCoords, 6: self._computeEndCoords}[
                    self._scheduleDraggingState
                ],
            )
        elif self._scheduleDraggingState == 1:
            dx = abs(self._scheduleDraggingOrigin[0].x - point.x)
            dy = abs(self._scheduleDraggingOrigin[0].y - point.y)
            if dx >= wx.SystemSettings.GetMetric(
                wx.SYS_DRAG_X
            ) or dy >= wx.SystemSettings.GetMetric(wx.SYS_DRAG_Y):
                self._scheduleDraggingState = 2
                self._drawDragging(point, self._computeAllCoords)
        elif self._scheduleDraggingState == 2:
            self._drawDragging(point, self._computeAllCoords)

    def _computeCoords(self, point, dx, dy):
        """
        Calcule les coordonnées ajustées dans le planificateur en fonction du déplacement.
        :param point: Position du point de base
        :param dx: Décalage en X
        :param dy: Décalage en Y
        :return: (wx.Point, wx.DateTime) coordonnées et heure correspondante
        """
        pp = wx.Point(point.x + dx, point.y + dy)
        if pp.y < 0:
            pp.y = 0
        if pp.y >= self._bitmap.GetHeight():
            pp.y = self._bitmap.GetHeight() - 1
        if pp.x < 0:
            pp.x = 0
        if pp.x >= self._bitmap.GetWidth():
            pp.x = self._bitmap.GetWidth() - 1

        for idx, (dt, pointMin, pointMax) in enumerate(self._datetimeCoords):
            if (
                    pointMin.y <= pp.y <= pointMax.y
                        and pointMin.x <= pp.x <= pointMax.x
            ):
                break
        else:
            idx = -1

        if idx >= 0:
            if self._scheduleDraggingStick:
                if self._style == wxSCHEDULER_VERTICAL:
                    pp = wx.Point(pp.x, pointMin.y)
                else:
                    pp = wx.Point(pointMin.x, pp.y)

            theTime = utils.copyDateTime(dt)
            if self._style == wxSCHEDULER_VERTICAL:
                theTime.AddTS(
                    wx.TimeSpan.Minutes(
                        int(30.0 * (pp.y - pointMin.y) / (pointMax.y - pointMin.y))
                    )
                )
            else:
                theTime.AddTS(
                    wx.TimeSpan.Minutes(
                        int(30.0 * (pp.x - pointMin.x) / (pointMax.x - pointMin.x))
                    )
                )
        else:
            raise ValueError("Not found: %d %d" % (pp.x, pp.y))

        return pp, theTime

    def _computeAllCoords(self, point):
        """
        Calcule les nouvelles coordonnées pour un planning lors d'un déplacement complet.
        :param point: Position de la souris
        :return: Tuple (rMin, rMax, theTime)
        """

        pMin, pMax, sch = self._scheduleDragged

        dx = point.x - self._scheduleDraggingOrigin[0].x
        dy = point.y - self._scheduleDraggingOrigin[0].y

        rMin, theTime = self._computeCoords(pMin, dx, dy)
        rMax = wx.Point(rMin.x + pMax.x - pMin.x, rMin.y + pMax.y - pMin.y)

        return rMin, rMax, theTime

    def _computeStartCoords(self, point):
        """
        Calcule les coordonnées lors du redimensionnement du début d'un planning (gauche/haut).
        :param point: Position de la souris
        :return: Tuple (rMin, rMax, theTime)
        """

        pMin, pMax, sch = self._scheduleDragged

        dx = point.x - self._scheduleDraggingOrigin[0].x
        dy = point.y - self._scheduleDraggingOrigin[0].y

        if self._style == wxSCHEDULER_VERTICAL:
            x = self._scheduleDraggingOrigin[0].x
            y = pMin.y
        else:
            x = pMin.x
            y = self._scheduleDraggingOrigin[0].y

        rMin, theTime = self._computeCoords(wx.Point(x, y), dx, dy)
        rMax = pMax

        if self._style == wxSCHEDULER_VERTICAL:
            rMin.x = pMin.x
        else:
            rMin.y = pMin.y

        return rMin, rMax, theTime

    def _computeEndCoords(self, point):
        """
        Calcule les coordonnées lors du redimensionnement de la fin d'un planning (droite/bas).
        :param point: Position de la souris
        :return: Tuple (rMin, rMax, theTime)
        """

        pMin, pMax, sch = self._scheduleDragged

        dx = point.x - self._scheduleDraggingOrigin[0].x
        dy = point.y - self._scheduleDraggingOrigin[0].y

        rMin = pMin
        rMax, theTime = self._computeCoords(pMax, dx, dy)

        firstTime = self._lstDisplayedHours[0]
        lastTime = self._lstDisplayedHours[-1]

        if (
            theTime.GetHour() == firstTime.GetHour()
            and theTime.GetMinute() == firstTime.GetMinute()
        ):
            theTime.SubtractTS(wx.TimeSpan.Days(1))
            theTime.SetHour(lastTime.GetHour() + 1)
            theTime.SetMinute(0)

        return rMin, rMax, theTime

    def _drawDragging(self, point, coords):
        """
        Dessine le planning pendant une opération de déplacement ou de redimensionnement.
        :param point: Position courante de la souris
        :param coords: Fonction de calcul des coordonnées à utiliser
        """
        if self._scheduleDraggingPrevious is not None:
            x, y = self.GetViewStart()
            mx, my = self.GetScrollPixelsPerUnit()
            x *= mx
            y *= my
            rMin, rMax, _ = coords(self._scheduleDraggingPrevious)
            self.RefreshRect(
                wx.Rect(rMin.x - x, rMin.y - y, rMax.x - rMin.x, rMax.y - rMin.y)
            )
            try:
                wx.Yield()
            except:
                pass

        self._scheduleDraggingPrevious = point

        if point is not None:
            rMin, rMax, _ = coords(point)

            dc = wx.ClientDC(self)
            self.PrepareDC(dc)
            dc.SetBrush(wx.Brush(self._scheduleDragged[2].GetColor()))
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawRoundedRectangle(rMin.x, rMin.y, rMax.x - rMin.x, rMax.y - rMin.y, 5)

    def _doRightClickControl(self, point):
        """
        Gère le clic droit sur le planificateur (affiche le menu contextuel ou équivalent).
        :param point: Position du clic droit
        """
        self._processEvt(wxEVT_COMMAND_SCHEDULE_RIGHT_CLICK, point)

    def _doDClickControl(self, point):
        """
        Gère le double-clic sur le planificateur (édition rapide ou autre action).
        :param point: Position du double-clic
        """
        self._processEvt(wxEVT_COMMAND_SCHEDULE_DCLICK, point)

    def _findSchedule(self, point):
        """
        Vérifie si le point donné se trouve sur un planning et retourne ce planning avec ses coordonnées.
        :param point: Position à tester
        :return: (pointMin, pointMax, schedule) ou (pointMin, pointMax, date)
        """
        for schedule, pointMin, pointMax in self._schedulesCoords:
            inX = (pointMin.x <= point.x) & (point.x <= pointMax.x)
            inY = (pointMin.y <= point.y) & (point.y <= pointMax.y)

            if inX & inY:
                return pointMin, pointMax, schedule.GetClientData()

        for dt, pointMin, pointMax in self._datetimeCoords:
            inX = (pointMin.x <= point.x) & (point.x <= pointMax.x)
            inY = (pointMin.y <= point.y) & (point.y <= pointMax.y)

            if inX & inY:
                return pointMin, pointMax, dt

    @staticmethod
    def _getSchedInPeriod(schedules, start, end):
        """
        Retourne la liste des plannings qui intersectent la période définie par 'start' et 'end'.
        Les dates de début/fin sont ajustées à la plage si nécessaire.
        :param schedules: Liste de plannings
        :param start: Date de début
        :param end: Date de fin
        :return: Liste de plannings ajustés
        """
        results = []

        for schedule in schedules:
            try:
                schedule.bounds = None

                if schedule.start.IsLaterThan(end) or schedule.start.IsEqualTo(end):
                    continue
                if start.IsLaterThan(schedule.end):
                    continue

                newSchedule = schedule.Clone()
                # This is used to find the original schedule object in _findSchedule.
                newSchedule.clientdata = schedule

                if start.IsLaterThan(schedule.start):
                    newSchedule.start = utils.copyDateTime(start)
                if schedule.end.IsLaterThan(end):
                    newSchedule.end = utils.copyDateTime(end)

                results.append(newSchedule)
            # except wx.PyDeadObjectError:
            except RuntimeError:
                pass

        return results

    # _getSchedInPeriod = staticmethod(_getSchedInPeriod)

    def _splitSchedules(self, schedules):
        """
        Sépare les plannings en groupes qui ne se chevauchent pas mutuellement.
        :param schedules: Liste de plannings
        :return: Liste de listes de plannings non chevauchants
        """
        results = []
        current = []

        schedules = schedules[:]  # Don't alter original list

        def findNext(schedule):
            # Among schedules that start after this one ends, find the "nearest".
            candidateSchedule = None
            minDelta = None
            for sched in schedules:
                if sched.start.IsLaterThan(schedule.end) or sched.start.IsEqualTo(
                    schedule.end
                ):
                    delta = sched.start.Subtract(schedule.end)
                    if minDelta is None or minDelta > delta:
                        minDelta = delta
                        candidateSchedule = sched
            return candidateSchedule

        while schedules:
            schedule = schedules[0]
            while schedule:
                current.append(schedule)
                schedules.remove(schedule)
                schedule = findNext(schedule)
            results.append(current)
            current = []

        return results

    def _paintPeriod(
        self, drawer, start, daysCount, x, y, width, height, highlight=None
    ):
        """
        Effectue le rendu des plannings pour une période donnée (jour/semaine/mois).
        :param drawer: Objet de dessin
        :param start: Date de début
        :param daysCount: Nombre de jours à afficher
        :param x: Position X
        :param y: Position Y
        :param width: Largeur d'affichage
        :param height: Hauteur d'affichage
        :param highlight: Couleur de surbrillance optionnelle
        :return: Dimensions réelles utilisées (width, height)
        """
        end = utils.copyDateTime(start)
        end.AddDS(wx.DateSpan(days=daysCount))

        blocks = self._splitSchedules(
            self._getSchedInPeriod(self._schedules, start, end)
        )
        offsetY = 0

        if self._showOnlyWorkHour:
            workingHours = [
                (self._startingHour, self._startingPauseHour),
                (self._endingPauseHour, self._endingHour),
            ]
        else:
            workingHours = [(self._startingHour, self._endingHour)]

        if not self.pageNumber:
            self.pageCount = 1
            self.pageLimits = [0]

            pageHeight = self.GetSize().GetHeight() - 20
            currentPageHeight = y

        for dayN in xrange(daysCount):
            theDay = utils.copyDateTime(start)
            theDay.AddDS(wx.DateSpan(days=dayN))
            theDay.SetSecond(0)
            color = highlight
            if theDay.IsSameDate(wx.DateTime.Now()):
                if self._viewType != wxSCHEDULER_DAILY or daysCount >= 2:
                    color = self._highlightColor
            drawer.DrawDayBackground(
                x + 1.0 * width / daysCount * dayN,
                y,
                1.0 * width / daysCount,
                height,
                highlight=color,
            )

        if blocks:
            dayWidth = width / len(blocks)

            for idx, block in enumerate(blocks):
                maxDY = 0

                for schedule in block:
                    show = True
                    if self.pageNumber is not None:
                        if (
                            self._schedulesPages.get(schedule.GetId(), None)
                            != self.pageNumber
                        ):
                            show = False

                    if show:
                        if self._style == wxSCHEDULER_VERTICAL:
                            xx, yy, w, h = drawer.DrawScheduleVertical(
                                schedule,
                                start,
                                workingHours,
                                x + dayWidth * idx,
                                y,
                                dayWidth,
                                height,
                            )
                        elif self._style == wxSCHEDULER_HORIZONTAL:
                            xx, yy, w, h = drawer.DrawScheduleHorizontal(
                                schedule,
                                start,
                                daysCount,
                                workingHours,
                                x,
                                y + offsetY,
                                width,
                                height,
                            )
                            maxDY = max(maxDY, h)

                        if self.pageNumber is None:
                            if currentPageHeight + h >= pageHeight:
                                pageNo = self.pageCount + 1
                            else:
                                pageNo = self.pageCount

                            self._schedulesPages[schedule.GetId()] = pageNo

                        self._schedulesCoords.append(
                            (schedule, wx.Point(xx, yy), wx.Point(xx + w, yy + h))
                        )
                    else:
                        schedule.Destroy()

                offsetY += maxDY

                if not self.pageNumber:
                    currentPageHeight += maxDY
                    if currentPageHeight >= pageHeight:
                        self.pageLimits.append(currentPageHeight - maxDY)
                        currentPageHeight = maxDY
                        self.pageCount += 1

        now = wx.DateTime.Now()

        for dayN in xrange(daysCount):
            theDay = utils.copyDateTime(start)
            theDay.AddDS(wx.DateSpan(days=dayN))
            theDay.SetSecond(0)

            nbHours = len(self._lstDisplayedHours)

            for idx, hour in enumerate(self._lstDisplayedHours):
                theDay.SetHour(hour.GetHour())
                theDay.SetMinute(hour.GetMinute())

                if self._minSize is None or not self._resizable:
                    if self._style == wxSCHEDULER_VERTICAL:
                        self._datetimeCoords.append(
                            (
                                utils.copyDateTime(theDay),
                                wx.Point(
                                    x + 1.0 * width * dayN / daysCount,
                                    y + 1.0 * height * idx / nbHours,
                                ),
                                wx.Point(
                                    x + 1.0 * width * (dayN + 1) / daysCount,
                                    y + 1.0 * height * (idx + 1) / nbHours,
                                ),
                            )
                        )
                    else:
                        self._datetimeCoords.append(
                            (
                                utils.copyDateTime(theDay),
                                wx.Point(
                                    x
                                    + 1.0
                                    * width
                                    * (nbHours * dayN + idx)
                                    / (nbHours * daysCount),
                                    y,
                                ),
                                wx.Point(
                                    x
                                    + 1.0
                                    * width
                                    * (nbHours * dayN + idx + 1)
                                    / (nbHours * daysCount),
                                    y + height,
                                ),
                            )
                        )

        if isinstance(self, wx.ScrolledWindow) and self._showNow:
            now = wx.DateTime.Now()
            # This assumes self._lstDisplayedHours is sorted of course
            for dayN in xrange(daysCount):
                theDay = utils.copyDateTime(start)
                theDay.AddDS(wx.DateSpan(days=dayN))
                if theDay.IsSameDate(now):
                    theDay.SetSecond(0)
                    previous = None
                    for idx, hour in enumerate(self._lstDisplayedHours):
                        theDay.SetHour(hour.GetHour())
                        theDay.SetMinute(hour.GetMinute())
                        if theDay.IsLaterThan(now):
                            if idx != 0:
                                if self._style == wxSCHEDULER_VERTICAL:
                                    yPrev = y + 1.0 * height * (idx - 1) / nbHours
                                    delta = (
                                        1.0
                                        * height
                                        / nbHours
                                        * now.Subtract(previous).GetSeconds()
                                        / theDay.Subtract(previous).GetSeconds()
                                    )
                                    drawer.DrawNowHorizontal(x, yPrev + delta, width)
                                else:
                                    xPrev = x + 1.0 * width * (
                                        nbHours * dayN + idx - 1
                                    ) / (nbHours * daysCount)
                                    delta = (
                                        1.0
                                        * width
                                        / (nbHours * daysCount)
                                        * now.Subtract(previous).GetSeconds()
                                        / theDay.Subtract(previous).GetSeconds()
                                    )
                                    drawer.DrawNowVertical(xPrev + delta, y, height)
                            break
                        previous = utils.copyDateTime(theDay)
                    break

        if self._style == wxSCHEDULER_VERTICAL:
            return max(width, DAY_SIZE_MIN.width), max(height, DAY_SIZE_MIN.height)
        else:
            return max(width, self._periodWidth), offsetY

    def _paintDay(self, drawer, day, x, y, width, height):
        """
        Dessine les plannings d'une journée dans la colonne correspondante.
        :param drawer: Objet de dessin
        :param day: Date du jour à afficher
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        start = utils.copyDateTime(day)
        start.SetHour(0)
        start.SetMinute(0)
        start.SetSecond(0)

        color = None
        if day.IsSameDate(wx.DateTime.Now()) and self._periodCount >= 2:
            color = self._highlightColor

        return self._paintPeriod(drawer, start, 1, x, y, width, height, highlight=color)

    def _paintDailyHeaders(self, drawer, day, x, y, width, height, includeText=True):
        """
        Dessine les en-têtes de la vue journalière.
        :param drawer: Objet de dessin
        :param day: Date du jour
        :param x, y, width, height: Dimensions de la zone d'en-tête
        :param includeText: Affiche le texte de la date si vrai
        :return: Largeur et hauteur occupées
        """
        if self._style == wxSCHEDULER_HORIZONTAL:
            self._headerBounds.append((x, y, height))

        if includeText:
            color = None
            if day.IsSameDate(wx.DateTime.Now()):
                if self._viewType != wxSCHEDULER_DAILY or self._periodCount >= 2:
                    color = self._highlightColor
            w, h = drawer.DrawDayHeader(day, x, y, width, height, highlight=color)
        else:
            w, h = width, 0

        if not (self._style == wxSCHEDULER_VERTICAL or self._drawHeaders):
            hw, hh = drawer.DrawHours(
                x, y + h, width, height - h, self._style, includeText=includeText
            )
            h += hh

        return w, h

    def _paintDaily(self, drawer, day, x, y, width, height):
        """
        Affiche les plannings de la journée (vue journalière, éventuellement multi-jours).
        :param drawer: Objet de dessin
        :param day: Date de départ
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        minWidth = minHeight = 0

        if self._style == wxSCHEDULER_VERTICAL:
            x += LEFT_COLUMN_SIZE
            width -= LEFT_COLUMN_SIZE

        theDay = utils.copyDateTime(day)

        if self._drawHeaders:
            maxDY = 0
            for idx in xrange(self._periodCount):
                w, h = self._paintDailyHeaders(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    y,
                    1.0 * width / self._periodCount,
                    height,
                )
                maxDY = max(maxDY, h)
                theDay.AddDS(wx.DateSpan(days=1))
            minHeight += maxDY
            y += maxDY
            height -= maxDY
        else:
            for idx in xrange(self._periodCount):
                self._paintDailyHeaders(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    y,
                    1.0 * width / self._periodCount,
                    height,
                    includeText=False,
                )
                theDay.AddDS(wx.DateSpan(days=1))

        if self._style == wxSCHEDULER_VERTICAL:
            x -= LEFT_COLUMN_SIZE
            width += LEFT_COLUMN_SIZE

        if self._style == wxSCHEDULER_VERTICAL or self._drawHeaders:
            if self._style == wxSCHEDULER_VERTICAL:
                w, h = drawer.DrawHours(x, y, width, height, self._style)
            else:
                maxDY = 0
                for idx in xrange(self._periodCount):
                    _, h = drawer.DrawHours(
                        x + 1.0 * width / self._periodCount * idx,
                        y,
                        1.0 * width / self._periodCount,
                        height,
                        self._style,
                    )
                    maxDY = max(maxDY, h)
                w = 0
                h = maxDY
        else:
            w, h = 0, 0

        if self._style == wxSCHEDULER_VERTICAL:
            minWidth += w
            x += w
            width -= w
        else:
            minHeight += h
            y += h
            height -= h

        if self._style == wxSCHEDULER_HORIZONTAL:
            # Use directly paintPeriod or pagination fails
            w, h = self._paintPeriod(
                drawer, day, self._periodCount, x, y, width, height
            )
        else:
            w = 0
            maxDY = 0
            theDay = utils.copyDateTime(day)
            for idx in xrange(self._periodCount):
                dw, dh = self._paintDay(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    y,
                    1.0 * width / self._periodCount,
                    height,
                )
                w += dw
                maxDY = max(maxDY, dh)
                theDay.AddDS(wx.DateSpan(days=1))

        minWidth += w
        minHeight += h

        return minWidth, minHeight

    def _paintWeeklyHeaders(self, drawer, day, x, y, width, height):
        """
        Dessine les en-têtes des jours pour la vue hebdomadaire.
        :param drawer: Objet de dessin
        :param day: Date de référence
        :param x, y, width, height: Dimensions de la zone d'en-tête
        :return: Hauteur occupée
        """
        firstDay = utils.setToWeekDayInSameWeek(day, 0, self._weekstart)
        firstDay.SetHour(0)
        firstDay.SetMinute(0)
        firstDay.SetSecond(0)

        maxDY = 0

        for weekday in xrange(7):
            theDay = utils.setToWeekDayInSameWeek(
                utils.copyDateTime(firstDay), weekday, self._weekstart
            )
            if theDay.IsSameDate(wx.DateTime.Now()):
                color = self._highlightColor
            else:
                color = None
            w, h = drawer.DrawDayHeader(
                theDay,
                x + weekday * 1.0 * width / 7,
                y,
                1.0 * width / 7,
                height,
                highlight=color,
            )
            self._headerBounds.append(
                (int(x + (weekday + 1) * 1.0 * width / 7), y, height)
            )
            maxDY = max(maxDY, h)

        return maxDY

    def _paintWeekly(self, drawer, day, x, y, width, height):
        """
        Affiche les plannings de la semaine courante.
        :param drawer: Objet de dessin
        :param day: Date de référence
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        firstDay = utils.setToWeekDayInSameWeek(day, 0, self._weekstart)
        firstDay.SetHour(0)
        firstDay.SetMinute(0)
        firstDay.SetSecond(0)

        minWidth = minHeight = 0

        if self._style == wxSCHEDULER_VERTICAL:
            x += LEFT_COLUMN_SIZE
            width -= LEFT_COLUMN_SIZE

        maxDY = 0

        if self._drawHeaders:
            theDay = utils.copyDateTime(day)
            for idx in xrange(self._periodCount):
                maxDY = max(
                    maxDY,
                    self._paintWeeklyHeaders(
                        drawer,
                        theDay,
                        x + 1.0 * width / self._periodCount * idx,
                        y,
                        1.0 * width / self._periodCount,
                        height,
                    ),
                )
                theDay.AddDS(wx.DateSpan(weeks=1))

        if self._style == wxSCHEDULER_VERTICAL:
            x -= LEFT_COLUMN_SIZE
            width += LEFT_COLUMN_SIZE

        minHeight += maxDY
        y += maxDY
        height -= maxDY

        if self._style == wxSCHEDULER_VERTICAL:
            w, h = drawer.DrawHours(x, y, width, height, self._style)

            minWidth += w
            x += w
            width -= w

            day = utils.copyDateTime(firstDay)

            for idx in xrange(self._periodCount):
                for weekday in xrange(7):
                    theDay = utils.setToWeekDayInSameWeek(
                        utils.copyDateTime(day), weekday, self._weekstart
                    )
                    self._paintDay(
                        drawer,
                        theDay,
                        x + (weekday + 7 * idx) * 1.0 * width / 7 / self._periodCount,
                        y,
                        1.0 * width / 7 / self._periodCount,
                        height,
                    )
                day.AddDS(wx.DateSpan(weeks=1))

            return max(
                WEEK_SIZE_MIN.width * self._periodCount + LEFT_COLUMN_SIZE, width
            ), max(WEEK_SIZE_MIN.height, height)
        else:
            w, h = self._paintPeriod(
                drawer, firstDay, 7 * self._periodCount, x, y, width, height
            )

            minWidth += w
            minHeight += h

            return (
                max(self._periodWidth * self._periodCount + LEFT_COLUMN_SIZE, minWidth),
                minHeight,
            )

    def _paintMonthlyHeaders(self, drawer, day, x, y, width, height):
        """
        Dessine les en-têtes pour la vue mensuelle.
        :param drawer: Objet de dessin
        :param day: Date de référence
        :param x, y, width, height: Dimensions de la zone d'en-tête
        :return: Largeur et hauteur occupées
        """
        if isinstance(self, wx.ScrolledWindow):
            # _, h = drawer.DrawMonthHeader(day, 0, 0, self.GetSizeTuple()[0], height)
            _, h = drawer.DrawMonthHeader(day, 0, 0, self.GetSize()[0], height)
            w = width
        else:
            w, h = drawer.DrawMonthHeader(day, x, y, width, height)

        if self._style == wxSCHEDULER_HORIZONTAL:
            day.SetDay(1)
            day.SetHour(0)
            day.SetMinute(0)
            day.SetSecond(0)

            # daysCount = wx.DateTime.GetNumberOfDaysInMonth(day.GetMonth())
            daysCount = wx.DateTime.GetNumberOfDays(day.GetMonth())

            maxDY = 0
            for idx in xrange(daysCount):
                theDay = utils.copyDateTime(day)
                theDay.AddDS(wx.DateSpan(days=idx))
                if theDay.IsSameDate(wx.DateTime.Now()):
                    color = self._highlightColor
                else:
                    color = None
                w, h = drawer.DrawSimpleDayHeader(
                    theDay,
                    x + 1.0 * idx * width / daysCount,
                    y + h,
                    1.0 * width / daysCount,
                    height,
                    highlight=color,
                )
                self._headerBounds.append(
                    (x + 1.0 * (idx + 1) * width / daysCount, y + h, height)
                )
                maxDY = max(maxDY, h)

            h += maxDY

        return w, h

    def _paintMonthly(self, drawer, day, x, y, width, height):
        """
        Affiche la grille du mois en utilisant le module calendar.
        :param drawer: Objet de dessin
        :param day: Date de référence (premier jour du mois)
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        if self._drawHeaders:
            w, h = self._paintMonthlyHeaders(drawer, day, x, y, width, height)
        else:
            w, h = width, 0

        y += h
        height -= h

        if self._style == wxSCHEDULER_VERTICAL:
            month = calendar.monthcalendar(day.GetYear(), day.GetMonth() + 1)

            for w, monthWeek in enumerate(month):
                for d, monthDay in enumerate(monthWeek):
                    cellW, cellH = 1.0 * width / 7, 1.0 * height / len(month)

                    if monthDay == 0:
                        theDay = None
                        schedules = []
                    else:
                        theDay = day
                        theDay.SetDay(monthDay)
                        theDay.SetHour(0)
                        theDay.SetMinute(0)
                        theDay.SetSecond(0)

                        end = utils.copyDateTime(theDay)
                        end.AddDS(wx.DateSpan(days=1))

                        schedules = self._getSchedInPeriod(self._schedules, theDay, end)

                        if self._minSize is None or not self._resizable:
                            self._datetimeCoords.append(
                                (
                                    utils.copyDateTime(theDay),
                                    wx.Point(d * cellW, w * cellH),
                                    wx.Point(d * cellW + cellW, w * cellH + cellH),
                                )
                            )

                    displayed = drawer.DrawSchedulesCompact(
                        theDay,
                        schedules,
                        d * cellW,
                        w * cellH + y,
                        cellW,
                        cellH,
                        self._highlightColor,
                    )
                    self._schedulesCoords.extend(displayed)

                    for schedule in set(schedules) - set(
                        [sched for sched, _, _ in displayed]
                    ):
                        schedule.Destroy()

            return (
                max(MONTH_CELL_SIZE_MIN.width * 7, width),
                max(MONTH_CELL_SIZE_MIN.height * (w + 1), height),
            )
        else:
            day.SetDay(1)
            day.SetHour(0)
            day.SetMinute(0)
            day.SetSecond(0)

            # daysCount = wx.DateTime.GetNumberOfDaysInMonth(day.GetMonth())
            daysCount = wx.DateTime.GetNumberOfDays(day.GetMonth())

            minHeight = h

            w, h = self._paintPeriod(drawer, day, daysCount, x, y, width, height)
            minHeight += h

            return w, minHeight

    def _processEvt(self, commandEvent, point):
        """
        Traite un événement de commande utilisateur à la position spécifiée.
        :param commandEvent: Type d'événement wxPython
        :param point: Position concernée
        """
        evt = wx.PyCommandEvent(commandEvent)
        _, _, sch = self._findSchedule(point)
        if isinstance(sch, wxSchedule):
            mySch = sch
            myDate = None
        else:
            mySch = None
            myDate = sch

        evt.schedule = mySch
        evt.date = myDate
        evt.SetEventObject(self)
        self.ProcessEvent(evt)

    def DoPaint(self, drawer, x, y, width, height):
        """
        Effectue le rendu principal du planificateur selon la vue courante.
        :param drawer: Objet de dessin
        :param x, y: Position d'origine
        :param width, height: Dimensions d'affichage
        :return: Dimensions utilisées (width, height)
        """
        for schedule, _, _ in self._schedulesCoords:
            schedule.Destroy()

        self._schedulesCoords = list()

        day = utils.copyDate(self.GetDate())

        if self._viewType == wxSCHEDULER_DAILY:
            return self._paintDaily(drawer, day, x, y, width, height)
        elif self._viewType == wxSCHEDULER_WEEKLY:
            return self._paintWeekly(drawer, day, x, y, width, height)
        elif self._viewType == wxSCHEDULER_MONTHLY:
            return self._paintMonthly(drawer, day, x, y, width, height)

    def GetViewSize(self):
        """
        Retourne la taille réelle de la vue planificateur (pour gestion du rapport).
        :return: wx.Size
        """
        # Used by wxSchedulerReport

        size = self.GetSize()
        minSize = self.CalcMinSize()

        return wx.Size(max(size.width, minSize.width), max(size.height, minSize.height))

    def _CalcMinSize(self):
        """
        Calcule la taille minimale nécessaire du planificateur selon la vue courante.
        :return: wx.Size
        """
        if self._viewType == wxSCHEDULER_DAILY:
            minW, minH = DAY_SIZE_MIN.width, DAY_SIZE_MIN.height
        elif self._viewType == wxSCHEDULER_WEEKLY:
            minW, minH = WEEK_SIZE_MIN.width, WEEK_SIZE_MIN.height
        elif self._viewType == wxSCHEDULER_MONTHLY:
            minW, minH = MONTH_CELL_SIZE_MIN.width * 7, 0  # will be computed

        if (
            self._viewType == wxSCHEDULER_MONTHLY
            or self._style == wxSCHEDULER_HORIZONTAL
        ):
            memDC = wx.MemoryDC()
            bmp = wx.EmptyBitmap(1, 1)
            memDC.SelectObject(bmp)
            try:
                if self._drawerClass.use_gc:
                    context = wx.GraphicsContext.Create(memDC)
                    context.SetFont(wx.NORMAL_FONT, wx.BLACK)
                else:
                    context = memDC
                    context.SetFont(wx.NORMAL_FONT)

                if isinstance(self, wx.ScrolledWindow):
                    size = self.GetVirtualSize()
                else:
                    size = self.GetSize()

                # Actually, only the min height may vary...
                _, minH = self.DoPaint(
                    self._drawerClass(context, self._lstDisplayedHours),
                    0,
                    0,
                    size.GetWidth(),
                    0,
                )

                if self._style == wxSCHEDULER_HORIZONTAL:
                    if self._viewType == wxSCHEDULER_DAILY:
                        minW = self._periodWidth * 4
                    elif self._viewType == wxSCHEDULER_WEEKLY:
                        minW = self._periodWidth * 7
                    elif self._viewType == wxSCHEDULER_MONTHLY:
                        # return wx.Size(
                        #     self._periodWidth
                        #     * wx.DateTime.GetNumberOfDaysInMonth(
                        #         self.GetDate().GetMonth()
                        #     ),
                        #     minH,
                        # )
                        return wx.Size(
                            self._periodWidth
                            * wx.DateTime.GetNumberOfDays(
                                self.GetDate().GetMonth()
                            ),
                            minH,
                        )
                elif self._viewType == wxSCHEDULER_MONTHLY:
                    return wx.Size(minW, minH)
            finally:
                memDC.SelectObject(wx.NullBitmap)
        elif self._style == wxSCHEDULER_VERTICAL:
            return wx.Size(minW * self._periodCount + LEFT_COLUMN_SIZE, minH)

        return wx.Size(minW * self._periodCount, minH)

    def CalcMinSize(self):
        """
        Retourne la taille minimale, en la recalculant si nécessaire.
        :return: wx.Size
        """
        if self._minSize is None:
            self._minSize = self._CalcMinSize()
        return self._minSize

    def InvalidateMinSize(self):
        """
        Invalide la taille minimale mémorisée pour forcer un recalcul.
        """
        self._minSize = None
        self._datetimeCoords = list()

    def DrawBuffer(self):
        """
        Dessine le contenu du planificateur dans un bitmap tampon pour l'affichage.
        """
        if isinstance(self, wx.ScrolledWindow):
            if self._resizable:
                size = self.GetVirtualSize()
            else:
                size = self.CalcMinSize()
        else:
            size = self.GetSize()

        self._bitmap = wx.EmptyBitmap(size.GetWidth(), size.GetHeight())
        memDC = wx.MemoryDC()
        memDC.SelectObject(self._bitmap)
        try:
            memDC.BeginDrawing()
            try:
                memDC.SetBackground(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
                memDC.SetPen(FOREGROUND_PEN)
                memDC.Clear()
                memDC.SetFont(wx.NORMAL_FONT)

                if self._drawerClass.use_gc:
                    context = wx.GraphicsContext.Create(memDC)
                    context.SetFont(wx.NORMAL_FONT, wx.BLACK)
                else:
                    context = memDC
                    context.SetFont(wx.NORMAL_FONT)

                width, height = self.DoPaint(
                    self._drawerClass(context, self._lstDisplayedHours),
                    0,
                    0,
                    size.GetWidth(),
                    size.GetHeight(),
                )
            finally:
                memDC.EndDrawing()
        finally:
            memDC.SelectObject(wx.NullBitmap)

        # Bad things may happen here from time to time.
        if isinstance(self, wx.ScrolledWindow):
            if self._resizable and not self._guardRedraw:
                self._guardRedraw = True
                try:
                    if int(width) > size.GetWidth() or int(height) > size.GetHeight():
                        self.SetVirtualSize(wx.Size(int(width), int(height)))
                        self.DrawBuffer()
                finally:
                    self._guardRedraw = False

    def RefreshSchedule(self, schedule):
        """
        Rafraîchit uniquement la zone d'un planning donné.
        :param schedule: Planning à rafraîchir
        """
        if schedule.bounds is not None:
            memDC = wx.MemoryDC()
            memDC.SelectObject(self._bitmap)
            try:
                memDC.BeginDrawing()
                memDC.SetBackground(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
                memDC.SetPen(FOREGROUND_PEN)
                memDC.SetFont(wx.NORMAL_FONT)

                if self._drawerClass.use_gc:
                    context = wx.GraphicsContext.Create(memDC)
                    context.SetFont(wx.NORMAL_FONT, wx.BLACK)
                else:
                    context = memDC
                    context.SetFont(wx.NORMAL_FONT)

                self._drawerClass(context, self._lstDisplayedHours)._DrawSchedule(
                    schedule, *schedule.bounds
                )
            finally:
                memDC.SelectObject(wx.NullBitmap)

            originX, originY = self.GetViewStart()
            unitX, unitY = self.GetScrollPixelsPerUnit()
            x, y, w, h = schedule.bounds
            self.RefreshRect(
                wx.Rect(
                    math.floor(x - originX * unitX) - 1,
                    math.floor(y - originY * unitY) - 1,
                    math.ceil(w) + 2,
                    math.ceil(h) + 2,
                )
            )

    def OnPaint(self, evt=None):
        """
        Gère l'événement de dessin (paint) du widget wxPython.
        :param evt: Événement wxPython (optionnel)
        """
        # TODO : Certainement plus nécessaire depuis Phoenix.
        if self._dc:
            dc = self._dc
        else:
            dc = wx.PaintDC(self)
            self.PrepareDC(dc)

        dc.BeginDrawing()
        try:
            dc.DrawBitmap(self._bitmap, 0, 0, False)
        finally:
            dc.EndDrawing()

    def SetResizable(self, value):
        """
        Définit si la vue doit être redimensionnable proportionnellement à la zone disponible.
        :param value: booléen
        """
        self._resizable = bool(value)

    def SetStyle(self, style):
        """
        Définit le style d'affichage (vertical ou horizontal).
        :param style: wxSCHEDULER_VERTICAL ou wxSCHEDULER_HORIZONTAL
        """
        self._style = style
        self.InvalidateMinSize()
        self.Refresh()

    def GetStyle(self):
        """
        Retourne le style d'affichage courant.
        :return: Style
        """
        return self._style

    def SetHighlightColor(self, color):
        """
        Définit la couleur de surbrillance (pour aujourd'hui par exemple).
        :param color: Couleur wx.Colour
        """

        self._highlightColor = color

    def GetHighlightColor(self):
        """
        Retourne la couleur de surbrillance actuelle.
        :return: wx.Colour
        """
        return self._highlightColor

    def SetDrawer(self, drawerClass):
        """
        Définit la classe de dessin à utiliser pour le rendu graphique.
        :param drawerClass: Classe de dessin
        """
        self._drawerClass = drawerClass
        self.InvalidateMinSize()
        self.Refresh()

    def GetDrawer(self):
        """
        Retourne la classe de dessin actuelle.
        :return: Classe de dessin
        """
        return self._drawerClass

    def SetPeriodWidth(self, width):
        """
        Définit la largeur d'une période (jour) en mode horizontal.
        :param width: Largeur en pixels
        """
        self._periodWidth = width

    def GetPeriodWidth(self):
        return self._periodWidth

    def Refresh(self):
        """
        Rafraîchit le planificateur et force le redessin du contenu et de l'en-tête si présent.
        """
        self.DrawBuffer()
        super(wxSchedulerPaint, self).Refresh()
        if self._headerPanel is not None:
            self._headerPanel.Refresh()

    def SetHeaderPanel(self, panel):
        """
        Définit un panneau wx.Panel comme zone d'en-tête indépendante.
        Les en-têtes seront alors dessinés sur ce panneau, indépendamment du scroll vertical.
        :param panel: Instance de wx.Panel
        """

        self._drawHeaders = False
        self._headerPanel = panel

        panel.Bind(wx.EVT_PAINT, self._OnPaintHeaders)
        panel.Bind(wx.EVT_MOTION, self._OnMoveHeaders)
        panel.Bind(wx.EVT_LEAVE_WINDOW, self._OnLeaveHeaders)
        panel.Bind(wx.EVT_LEFT_DOWN, self._OnLeftDownHeaders)
        panel.Bind(wx.EVT_LEFT_UP, self._OnLeftUpHeaders)
        panel.SetSize(wx.Size(-1, 1))
        self.Bind(wx.EVT_SCROLLWIN, self._OnScroll)

        panel.Refresh()

    # Headers stuff

    def _OnPaintHeaders(self, evt):
        dc = wx.PaintDC(self._headerPanel)
        dc.BeginDrawing()
        try:
            dc.SetBackground(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
            dc.SetPen(FOREGROUND_PEN)
            dc.Clear()
            dc.SetFont(wx.NORMAL_FONT)

            if self._drawerClass.use_gc:
                context = wx.GraphicsContext.Create(dc)
                context.SetFont(wx.NORMAL_FONT, wx.BLACK)
            else:
                context = dc
                context.SetFont(wx.NORMAL_FONT)

            drawer = self._drawerClass(context, self._lstDisplayedHours)

            if self._resizable:
                width, _ = self.GetVirtualSize()
            else:
                width, _ = self.CalcMinSize()

            day = utils.copyDate(self.GetDate())

            x, y = 0, 0

            # Take horizontal scrolling into account
            x0, _ = self.GetViewStart()
            xu, _ = self.GetScrollPixelsPerUnit()
            x0 *= xu
            x -= x0

            self._headerBounds = []

            if self._viewType == wxSCHEDULER_DAILY:
                if self._style == wxSCHEDULER_VERTICAL:
                    x += LEFT_COLUMN_SIZE
                    width -= LEFT_COLUMN_SIZE
                theDay = utils.copyDateTime(day)
                maxDY = 0
                for idx in xrange(self._periodCount):
                    _, h = self._paintDailyHeaders(
                        drawer,
                        theDay,
                        x + 1.0 * width / self._periodCount * idx,
                        y,
                        1.0 * width / self._periodCount,
                        36,
                    )
                    maxDY = max(maxDY, h)
                    theDay.AddDS(wx.DateSpan(days=1))
                h = maxDY
            elif self._viewType == wxSCHEDULER_WEEKLY:
                if self._style == wxSCHEDULER_VERTICAL:
                    x += LEFT_COLUMN_SIZE
                    width -= LEFT_COLUMN_SIZE
                theDay = utils.copyDateTime(day)
                maxDY = 0
                for idx in xrange(self._periodCount):
                    h = self._paintWeeklyHeaders(
                        drawer,
                        theDay,
                        x + 1.0 * width / self._periodCount * idx,
                        y,
                        1.0 * width / self._periodCount,
                        36,
                    )
                    maxDY = max(maxDY, h)
                    theDay.AddDS(wx.DateSpan(weeks=1))
                h = maxDY
            elif self._viewType == wxSCHEDULER_MONTHLY:
                _, h = self._paintMonthlyHeaders(drawer, day, x, y, width, 36)

            minW, minH = self._headerPanel.GetMinSize()
            if minH != h:
                self._headerPanel.SetMinSize(wx.Size(-1, h))
                self._headerPanel.GetParent().Layout()

            # Mmmmh, maybe we'll support this later, but not right Now
            if self._style == wxSCHEDULER_VERTICAL:
                self._headerBounds = []
        finally:
            dc.EndDrawing()

    def _OnMoveHeaders(self, evt):
        if self._headerDragOrigin is None:
            for x, y, h in self._headerBounds:
                if abs(evt.GetX() - x) < 5 and evt.GetY() >= y and evt.GetY() < y + h:
                    if self._headerCursorState == 0:
                        self._headerCursorState = 1
                        self._headerPanel.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
                    break
            else:
                if self._headerCursorState == 1:
                    self._headerPanel.SetCursor(wx.STANDARD_CURSOR)
                    self._headerCursorState = 0
        else:
            deltaX = evt.GetX() - self._headerDragOrigin
            self.SetPeriodWidth(max(50, self._headerDragBase + deltaX))

            evt = wx.PyCommandEvent(wxEVT_COMMAND_PERIODWIDTH_CHANGED)
            evt.SetEventObject(self)
            self.ProcessEvent(evt)

            self.InvalidateMinSize()
            self.Refresh()

    def _OnLeaveHeaders(self, evt):
        if self._headerCursorState == 1 and self._headerDragOrigin is None:
            self._headerPanel.SetCursor(wx.STANDARD_CURSOR)
            self._headerCursorState = 0

    def _OnLeftDownHeaders(self, evt):
        if self._headerCursorState == 1:
            self._headerDragOrigin = evt.GetX()
            self._headerDragBase = self._periodWidth
            self._headerPanel.CaptureMouse()
        else:
            evt.Skip()

    def _OnLeftUpHeaders(self, evt):
        if self._headerCursorState == 1:
            self._headerPanel.ReleaseMouse()
            self._headerDragOrigin = None
        else:
            evt.Skip()

    def _OnScroll(self, evt):
        self._headerPanel.Refresh()
        evt.Skip()
