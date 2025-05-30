# deltaTime.py
#
# Analyseur pour convertir une référence temporelle conversationnelle telle que "dans une minute" ou
# "midi demain" et la convertir en date/heure Python.  L'objet ParseResults renvoyé
# contient le nom des résultats "timeOffset" contenant
# le timedelta et "calculatedTime" contenant le temps calculé relatif
# à datetime.Now().
#
# Copyright 2010, by Paul McGuire
#

# from __future__ import print_function
# from builtins import map
# from past.builtins import basestring
from datetime import datetime, timedelta
# from pyparsing import *
from pyparsing import (CaselessLiteral, Combine, Group, nums, oneOf, Optional,
                       replaceWith, Suppress, Word)
import calendar

__all__ = ["nlTimeExpression"]

daynames = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


# string conversion parse actions
def convertToTimedelta(toks):
    unit = toks.timeunit.lower().rstrip("s")
    td = {
        "week": timedelta(7),
        "day": timedelta(1),
        "hour": timedelta(0, 0, 0, 0, 0, 1),
        "minute": timedelta(0, 0, 0, 0, 1),
        "second": timedelta(0, 1),
    }[unit]
    if toks.qty:
        td *= int(toks.qty)
    if toks.dir:
        td *= toks.dir
    toks["timeOffset"] = td


def convertToDay(toks):
    now = datetime.now()
    if "wkdayRef" in toks:
        todaynum = now.weekday()
        nameddaynum = daynames.index(toks.wkdayRef.day.lower())
        if toks.wkdayRef.dir > 0:
            daydiff = (nameddaynum + 7 - todaynum) % 7
        else:
            daydiff = -((todaynum + 7 - nameddaynum) % 7)
        toks["absTime"] = datetime(now.year, now.month, now.day) + timedelta(daydiff)
    else:
        name = toks.name.lower()
        toks["absTime"] = {
            "now": now,
            "today": datetime(now.year, now.month, now.day),
            "yesterday": datetime(now.year, now.month, now.day)
            + timedelta(-1),
            "tomorrow": datetime(now.year, now.month, now.day) + timedelta(+1),
        }[name]


def convertToAbsTime(toks):
    now = datetime.now()
    if "dayRef" in toks:
        day = toks.dayRef.absTime
        day = datetime(day.year, day.month, day.day)
    else:
        day = datetime(now.year, now.month, now.day)
    if "timeOfDay" in toks:
        # if isinstance(toks.timeOfDay, basestring):
        if isinstance(toks.timeOfDay, str):
            timeOfDay = {
                "now": timedelta(0, (now.hour * 60 + now.minute) * 60 + now.second, now.microsecond),
                "noon": timedelta(0, 0, 0, 0, 0, 12),
                "midnight": timedelta(),
            }[toks.timeOfDay]
        else:
            hhmmss = toks.timeparts
            if hhmmss.miltime:
                hh, mm = hhmmss.miltime
                ss = 0
            else:
                hh, mm, ss = (hhmmss.HH % 12), hhmmss.MM, hhmmss.SS
                if not mm:
                    mm = 0
                if not ss:
                    ss = 0
                if toks.timeOfDay.ampm == "pm":
                    hh += 12
            timeOfDay = timedelta(0, (hh * 60 + mm) * 60 + ss, 0)
    else:
        timeOfDay = timedelta(0, (now.hour * 60 + now.minute) * 60 + now.second, now.microsecond)
    toks["absTime"] = day + timeOfDay


def calculateTime(toks):
    if toks.absTime:
        absTime = toks.absTime
    else:
        absTime = datetime.now()
    if toks.timeOffset:
        absTime += toks.timeOffset
    toks["calculatedTime"] = absTime


# grammar definitions
CL = CaselessLiteral
# ajout de list
today, tomorrow, yesterday, noon, midnight, now = list(map(CL,
                                                           "today tomorrow yesterday noon midnight now".split()))


# plural = lambda s: Combine(CL(s) + Optional(CL("s")))
def plural(s):
    return Combine(CL(s) + Optional(CL("s")))


week, day, hour, minute, second = list(map(plural,
                                           "week day hour minute second".split()))
am = CL("am")
pm = CL("pm")
COLON = Suppress(':')

# are these actually operators?
in_ = CL("in").setParseAction(replaceWith(1))
from_ = CL("from").setParseAction(replaceWith(1))
before = CL("before").setParseAction(replaceWith(-1))
after = CL("after").setParseAction(replaceWith(1))
ago = CL("ago").setParseAction(replaceWith(-1))
next_ = CL("next").setParseAction(replaceWith(1))
last_ = CL("last").setParseAction(replaceWith(-1))
at_ = CL("at")

couple = (Optional(CL("a")) + CL("couple") + Optional(CL("of"))).setParseAction(replaceWith(2))
a_qty = CL("a").setParseAction(replaceWith(1))
integer = Word(nums).setParseAction(lambda t: int(t[0]))
int4 = Group(Word(nums, exact=4).setParseAction(lambda t: [int(t[0][:2]), int(t[0][2:])]))
qty = integer | couple | a_qty
dayName = oneOf(daynames)

dayOffset = (qty("qty") + (week | day)("timeunit"))
dayFwdBack = (from_ + now.suppress() | ago)("dir")
weekdayRef = (Optional(next_ | last_, 1)("dir") + dayName("day"))
dayRef = Optional((dayOffset + (before | after | from_)("dir")).setParseAction(convertToTimedelta)) + \
         ((yesterday | today | tomorrow)("name") |
          weekdayRef("wkdayRef")).setParseAction(convertToDay)
todayRef = (dayOffset + dayFwdBack).setParseAction(convertToTimedelta) | \
           (in_("dir") + qty("qty") + day("timeunit")).setParseAction(convertToTimedelta)

dayTimeSpec = dayRef | todayRef
dayTimeSpec.setParseAction(calculateTime)

hourMinuteOrSecond = (hour | minute | second)

timespec = Group(int4("miltime") |
                 integer("HH") +
                 Optional(COLON + integer("MM")) +
                 Optional(COLON + integer("SS")) + (am | pm)("ampm")
                 )
absTimeSpec = ((noon | midnight | now | timespec("timeparts"))("timeOfDay") +
               Optional(dayRef)("dayRef") |
               dayRef("dayRef") + at_ +
               (noon | midnight | now | timespec("timeparts"))("timeOfDay"))
absTimeSpec.setParseAction(convertToAbsTime, calculateTime)

relTimeSpec = qty("qty") + hourMinuteOrSecond("timeunit") + \
              (from_ | before | after)("dir") + \
              absTimeSpec("absTime") | \
              qty("qty") + hourMinuteOrSecond("timeunit") + ago("dir") | \
              in_ + qty("qty") + hourMinuteOrSecond("timeunit")
relTimeSpec.setParseAction(convertToTimedelta, calculateTime)

nlTimeExpression = (absTimeSpec | dayTimeSpec | relTimeSpec)

if __name__ == "__main__":
    # test grammar
    tests = """\
    today
    tomorrow
    yesterday
    in a couple of days
    a couple of days from now
    a couple of days from today
    in a day
    3 days ago
    3 days from now
    a day ago
    now
    10 minutes ago
    10 minutes from now
    in 10 minutes
    in a minute
    in a couple of minutes
    20 seconds ago
    in 30 seconds
    20 seconds before noon
    20 seconds before noon tomorrow
    noon
    midnight
    noon tomorrow
    6am tomorrow
    0800 yesterday
    12:15 AM today
    3pm 2 days from today
    a week from today
    a week from now
    3 weeks ago
    noon next Sunday
    noon Sunday
    noon last Sunday
    2pm next Sunday
    next Sunday at 2pm""".splitlines()

    for t in tests:
        # print(t, "(relative to %s)" % datetime.now())
        print(t, f"(relative to {datetime.now()})")
        res = nlTimeExpression.parseString(t)
        if "calculatedTime" in res:
            print(res.calculatedTime)
        else:
            print("???")
        print()
