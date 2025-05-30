# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# """ render.py - functions to render various objects, like Date, time,
# etc. """  # pylint: disable=W0105

# Futurize ajoute 2 lignes:
# from builtins import zip
# from builtins import str
from taskcoachlib.domain import date as datemodule
# from taskcoachlib.thirdparty import desktop
import desktop
from taskcoachlib.i18n import _
from taskcoachlib import operating_system
import datetime
import codecs
import locale
import re

# pylint: disable=W0621


def priority(priority):
    """ Rendre une priorité (entière). """
    return str(priority)


def timeLeft(time_left, completed_task):
    """ Rendre le temps restant sous forme de chaîne de texte.

    Renvoie une chaîne vide pour les tâches terminées
    et pour les tâches sans date d'échéance prévue. Sinon,
    renvoie le nombre de jours, d'heures et de minutes restants."""
    if completed_task or time_left == datemodule.TimeDelta.max:
        return ""
    sign = "-" if time_left.days < 0 else ""
    time_left = abs(time_left)
    if time_left.days > 0:
        # vieux code :
        # days = (
        #     _('%d days') % time_left.days if time_left.days > 1 else _('1 day')
        # )
        # devient en python3 :
        # days = _('{} days'.format(time_left.days)) if time_left.days > 1 else \
        #        _('1 day')
        # ou :
        days = _(f"{time_left.days} days") if time_left.days > 1 else \
               _("1 day")
        days += ", "
    else:
        days = ""
    hours_and_minutes = ":".join(str(time_left).split(":")[:-1]).split(", ")[-1]
    return sign + days + hours_and_minutes


def timeSpent(time_spent, showSeconds=True, decimal=False):
    """ Render time spent (of type Date.TimeDelta) as
        "<hours>:<minutes>:<seconds>" or "<hours>:<minutes>" """
    if decimal:
        return timeSpentDecimal(time_spent)

    zero = datemodule.TimeDelta()
    if time_spent == zero:
        return ""
    else:
        sign = "-" if time_spent < zero else ""
        hours, minutes, seconds = time_spent.hoursMinutesSeconds()
        # AttributeError: 'TimeDelta' object has no attribute 'hoursMinutesSeconds'
        return (
            sign
            + "%d:%02d" % (hours, minutes)
            + (":%02d" % seconds if showSeconds else "")
        )


def timeSpentDecimal(time_spent):
    """ Render time spent (of type Date.TimeDelta) as
        "<hours>.<fractional hours> """
    zero = datemodule.TimeDelta()
    if time_spent == zero:
        return ""
    else:
        sign = "-" if time_spent < zero else ""
        hours, minutes, seconds = time_spent.hoursMinutesSeconds()
        decimalHours = hours + minutes / 60.0 + seconds / 3600.0
        return sign + "%.2f" % decimalHours


def recurrence(recurrence):
    """ Afficher la récurrence sous la forme d'une courte chaîne décrivant la fréquence de
        la récurrence. """
    if not recurrence:
        return ""
    if recurrence.amount > 2:
        labels = [
            _("Every %(frequency)d days"),
            _("Every %(frequency)d weeks"),
            _("Every %(frequency)d months"),
            _("Every %(frequency)d years"),
        ]
    elif recurrence.amount == 2:
        labels = [
            _("Every other day"),
            _("Every other week"),
            _("Every other month"),
            _("Every other year"),
        ]
    else:
        labels = [_("Daily"), _("Weekly"), _("Monthly"), _("Yearly")]
    # mapping = dict(zip(['daily', 'weekly', 'monthly', 'yearly'], labels))
    mapping = dict(list(zip(["daily", "weekly", "monthly", "yearly"], labels)))
    return mapping.get(recurrence.unit) % dict(frequency=recurrence.amount)


def budget(aBudget):
    """ Render budget (of type Date.TimeDelta) as
        "<hours>:<minutes>:<seconds>". """
    return timeSpent(aBudget)


# Default time formatting
language_and_country = locale.getlocale(locale.LC_TIME)[0]
if language_and_country and (
    "_US" in language_and_country or "_United States" in language_and_country
):
    timeFormat = "%I %p"
    timeWithMinutesFormat = "%I:%M %p"
    timeWithSecondsFormat = "%I:%M:%S %p"
else:
    timeFormat = "%H"
    timeWithMinutesFormat = "%H:%M"  # %X includes seconds (see http://stackoverflow.com/questions/2507726)
    timeWithSecondsFormat = "%X"


def rawTimeFunc(dt, minutes=True, seconds=False):
    if seconds:
        fmt = timeWithSecondsFormat
    else:
        if minutes:
            fmt = timeWithMinutesFormat
        else:
            fmt = timeFormat
    return datemodule.DateTime.strftime(dt, fmt)


dateFormat = "%x"


def rawDateFunc(dt=None):
    return operating_system.decodeSystemString(
        datetime.datetime.strftime(dt, dateFormat)
    )


def dateFunc(dt=None, humanReadable=False):
    if humanReadable:
        theDate = dt.date()
        if theDate == datemodule.Now().date():
            return _("Today")
        elif theDate == datemodule.Yesterday().date():
            return _("Yesterday")
        elif theDate == datemodule.Tomorrow().date():
            return _("Tomorrow")
    return rawDateFunc(dt)


# OS-specific time formatting
if operating_system.isWindows():
    import pywintypes
    import win32api


    def rawTimeFunc(dt, minutes=True, seconds=False):
        if seconds:
            # You can't include seconds without minutes
            flags = 0x0
        else:
            if minutes:
                flags = 0x2
            else:
                flags = 0x1
        return operating_system.decodeSystemString(
            win32api.GetTimeFormat(
                0x400, flags, None if dt is None else pywintypes.Time(dt), None
            )
        )

    def rawDateFunc(dt):
        return operating_system.decodeSystemString(
            win32api.GetDateFormat(
                0x400, 0, None if dt is None else pywintypes.Time(dt), None
            )
        )

elif operating_system.isMac():
    import Cocoa
    import calendar
    # We don't actually respect the 'seconds' parameter; this assumes that the short time format does
    # not include them, but the medium format does.
    _shortFormatter = Cocoa.NSDateFormatter.alloc().init()
    _shortFormatter.setFormatterBehavior_(Cocoa.NSDateFormatterBehavior10_4)
    _shortFormatter.setTimeStyle_(Cocoa.NSDateFormatterShortStyle)
    _shortFormatter.setDateStyle_(Cocoa.NSDateFormatterNoStyle)
    _shortFormatter.setTimeZone_(
        Cocoa.NSTimeZone.timeZoneForSecondsFromGMT_(0)
    )
    _mediumFormatter = Cocoa.NSDateFormatter.alloc().init()
    _mediumFormatter.setFormatterBehavior_(Cocoa.NSDateFormatterBehavior10_4)
    _mediumFormatter.setTimeStyle_(Cocoa.NSDateFormatterMediumStyle)
    _mediumFormatter.setDateStyle_(Cocoa.NSDateFormatterNoStyle)
    _mediumFormatter.setTimeZone_(
        Cocoa.NSTimeZone.timeZoneForSecondsFromGMT_(0)
    )
    # Special case for hour without minutes or seconds. I don't know if it is possible to get the AM/PM
    # setting alone, so parse the format string instead.
    # See http://www.unicode.org/reports/tr35/tr35-25.html#Date_Format_Patterns
    _state = 0
    # _hourFormat = u''
    _hourFormat = ""
    # _ampmFormat = u''
    _ampmFormat = ""
    for c in _mediumFormatter.dateFormat():
        if _state == 0:
            # if c == u"'":
            if c == "'":
                _state = 1  # After single quote
            # elif c in [u'h', u'H', u'k', u'K', u'j']:
            elif c in ["h", "H", "k", "K", "j"]:
                _hourFormat += c
            elif c == "a":
                _ampmFormat = c
        elif _state == 1:
            # if c == u"'":
            if c == "'":
                _state = 0
            else:
                _state = 2  # Escaped string
        elif _state == 2:
            # if c == u"'":
            if c == "'":
                _state = 0
    _hourFormatter = Cocoa.NSDateFormatter.alloc().init()
    _hourFormatter.setFormatterBehavior_(Cocoa.NSDateFormatterBehavior10_4)
    _hourFormatter.setDateFormat_(
        _hourFormat + (" %s" % _ampmFormat if _ampmFormat else "")
    )
    _hourFormatter.setTimeZone_(Cocoa.NSTimeZone.timeZoneForSecondsFromGMT_(0))
    _dateFormatter = Cocoa.NSDateFormatter.alloc().init()
    _dateFormatter.setFormatterBehavior_(Cocoa.NSDateFormatterBehavior10_4)
    _dateFormatter.setDateStyle_(Cocoa.NSDateFormatterShortStyle)
    _dateFormatter.setTimeStyle_(Cocoa.NSDateFormatterNoStyle)
    _dateFormatter.setTimeZone_(Cocoa.NSTimeZone.timeZoneForSecondsFromGMT_(0))

    def _applyFormatter(dt, fmt):
        dt_native = Cocoa.NSDate.dateWithTimeIntervalSince1970_(
            (dt - datetime.datetime(1970, 1, 1, 0, 0, 0, 0)).total_seconds()
        )
        return fmt.stringFromDate_(dt_native)

    def rawTimeFunc(dt, minutes=True, seconds=False):
        if minutes:
            if seconds:
                return _applyFormatter(dt, _mediumFormatter)
            return _applyFormatter(dt, _shortFormatter)
        return _applyFormatter(dt, _hourFormatter)

    def rawDateFunc(dt):
        return _applyFormatter(
            datetime.datetime.combine(dt, datetime.time(0, 0, 0, 0)),
            _dateFormatter,
        )

elif desktop.get_desktop() == "KDE4":
    try:
        from PyKDE4.kdecore import KGlobal, KLocale
        from PyQt4.QtCore import QTime, QDate
    except ImportError:
        pass
    else:
        _localeCopy = KLocale(KGlobal.locale())
        if "%p" in KGlobal.locale().timeFormat():
            _localeCopy.setTimeFormat("%I %p")
        else:
            _localeCopy.setTimeFormat("%H")

        def rawTimeFunc(dt, minutes=True, seconds=False):
            qtdt = QTime(dt.hour, dt.minute, dt.second)
            if minutes:
                return str(KGlobal.locale().formatTime(qtdt, seconds))
            return str(_localeCopy.formatTime(qtdt))

        def rawDateFunc(dt):
            qtdt = QDate(dt.year, dt.month, dt.day)
            return str(KGlobal.locale().formatDate(qtdt, 0))


# timeFunc = lambda dt, minutes=True, seconds=False: operating_system.decodeSystemString(
#     rawTimeFunc(dt, minutes=minutes, seconds=seconds)
# )
def timeFunc(dt, minutes=True, seconds=False):
    return operating_system.decodeSystemString(rawTimeFunc(dt, minutes=minutes, seconds=seconds))


# dateTimeFunc = lambda dt=None, humanReadable=False: f"{dateFunc(dt, humanReadable=humanReadable)} {timeFunc(dt)}"
def dateTimeFunc(dt=None, humanReadable=False):
    return f"{dateFunc(dt, humanReadable=humanReadable)} {timeFunc(dt)}"


def date(aDateTime, humanReadable=False):
    """ Render a Date/time as Date. """
    if str(aDateTime) == "":
        return ""
    year = aDateTime.year
    if year >= 1900:
        return dateFunc(aDateTime, humanReadable=humanReadable)
    else:
        result = date(datemodule.DateTime(year + 1900, aDateTime.month,
                                          aDateTime.day),
                      humanReadable=humanReadable)
        return re.sub(str(year + 1900), str(year), result)


def dateTime(aDateTime, humanReadable=False):
    if (
        not aDateTime
        or aDateTime == datemodule.DateTime()
        or aDateTime == datemodule.DateTime.min
    ):
        return ""
    timeIsMidnight = (aDateTime.hour, aDateTime.minute) in ((0, 0), (23, 59))
    year = aDateTime.year
    if year >= 1900:
        return (
            dateFunc(aDateTime, humanReadable=humanReadable)
            if timeIsMidnight
            else dateTimeFunc(aDateTime, humanReadable=humanReadable)
        )
    else:
        result = dateTime(
            aDateTime.replace(year=year + 1900), humanReadable=humanReadable
        )
        return re.sub(str(year + 1900), str(year), result)


def dateTimePeriod(start, stop, humanReadable=False):
    if stop is None:
        return "%s - %s" % (
            dateTime(start, humanReadable=humanReadable),
            _("now"),
        )
    elif start.date() == stop.date():
        return "%s %s - %s" % (
            date(start, humanReadable=humanReadable),
            time(start),
            time(stop),
        )
    else:
        return "%s - %s" % (
            dateTime(start, humanReadable=humanReadable),
            dateTime(stop, humanReadable=humanReadable),
        )


def time(dateTime, seconds=False, minutes=True):
    try:
        # strftime doesn't handle years before 1900, be prepared:
        dateTime = dateTime.replace(year=2000)
    except TypeError:  # We got a time instead of a dateTime
        dateTime = datemodule.Now().replace(hour=dateTime.hour,
                                            minute=dateTime.minute,
                                            second=dateTime.second)
    return timeFunc(dateTime, minutes=minutes, seconds=seconds)


def month(dateTime):
    return dateTime.strftime("%Y %B")


def weekNumber(dateTime):
    # Would have liked to use dateTime.strftime('%Y-%U'), but the week number
    # is one off in 2004
    # return "%d-%d" % (dateTime.year, dateTime.weeknumber())
    return f"{dateTime.year:d}-{dateTime.weeknumber():d}"


def monetaryAmount(aFloat):
    """ Afficher un montant monétaire, en utilisant les paramètres régionaux de l'utilisateur. """
    return (
        ""
        if round(aFloat, 2) == 0
        else locale.format("%.2f", aFloat, monetary=True)
    )


def percentage(aFloat):
    """ Afficher un pourcentage. """
    # return "" if round(aFloat, 0) == 0 else "%.0f%%" % aFloat
    return "" if round(aFloat, 0) == 0 else f"{aFloat:.0f}%"


def exception(exception, instance):
    """ Générez une exception en toute sécurité, en vous préparant à de nouvelles exceptions. """

    try:
        # Dans cet ordre. Python 2.6 a résolu le problème des exceptions Unicode.
        try:
            return str(instance)
        except UnicodeDecodeError:
            # On Windows, some exceptions raised by win32all lead to this
            # Hack around it
            result = []
            for val in instance.args:
                if isinstance(val, str):
                    result.append(val.encode("UTF-8"))
                else:
                    result.append(val)
            return str(result)
    except UnicodeEncodeError:
        # return "<class %s>" % str(exception)
        return f"<class {str(exception)}>"
