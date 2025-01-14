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

# from builtins import str
# from builtins import object
from ... import tctest
from taskcoachlib import config
from taskcoachlib.domain import task, date, effort


class CommonTaskRelationshipManagerTestsMixin(object):
    def setUp(self):
        super().setUp()
        task.Task.settings = settings = config.Settings(load=False)
        now = self.now = date.Now()
        self.yesterday = now - date.ONE_DAY
        self.tomorrow = now + date.ONE_DAY
        self.parent = task.Task("parent")
        self.child = task.Task("child")
        self.parent.addChild(self.child)
        self.child.setParent(self.parent)
        self.child2 = task.Task("child2", plannedStartDateTime=now)
        self.grandchild = task.Task("grandchild", plannedStartDateTime=now)
        settings.set(
            "behavior",
            "markparentcompletedwhenallchildrencompleted",
            str(self.markParentCompletedWhenAllChildrenCompleted),
        )
        self.taskList = task.TaskList([self.parent, self.child2, self.grandchild])

    # completion Date

    def testMarkingOneOfTwoChildsCompletedNeverResultsInACompletedParent(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime()
        self.assertFalse(self.parent.completed())

    def testMarkParentWithOneChildCompleted(self):
        self.parent.setCompletionDateTime()
        self.assertTrue(self.child.completed())

    def testMarkParentWithTwoChildrenCompleted(self):
        self.parent.addChild(self.child2)
        self.parent.setCompletionDateTime()
        self.assertTrue(self.child.completed())
        self.assertTrue(self.child2.completed())

    def testMarkParentNotCompleted(self):
        self.parent.setCompletionDateTime()
        self.assertTrue(self.child.completed())
        self.parent.setCompletionDateTime(date.DateTime())
        self.assertTrue(self.child.completed())

    def testMarkParentCompletedDoesNotChangeChildCompletionDate(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime(self.yesterday)
        self.parent.setCompletionDateTime()
        self.assertEqual(self.yesterday, self.child.completionDateTime())

    def testMarkChildNotCompleted(self):
        self.child.setCompletionDateTime()
        self.child.setCompletionDateTime(date.DateTime())
        self.assertFalse(self.parent.completed())

    def testAddCompletedChild(self):
        self.child2.setCompletionDateTime()
        self.parent.addChild(self.child2)
        self.assertFalse(self.parent.completed())

    def testAddUncompletedChild(self):
        self.child.setCompletionDateTime()
        self.parent.addChild(self.child2)
        self.assertFalse(self.parent.completed())

    def testAddUncompletedGrandchild(self):
        self.parent.setCompletionDateTime()
        self.child.addChild(self.grandchild)
        self.assertFalse(self.parent.completed())

    def testMarkParentCompletedYesterday(self):
        self.parent.setCompletionDateTime(self.yesterday)
        self.assertEqual(self.yesterday, self.child.completionDateTime())

    def testMarkTaskCompletedStopsEffortTracking(self):
        self.child.addEffort(effort.Effort(self.child))
        self.child.setCompletionDateTime()
        self.assertFalse(self.child.isBeingTracked())

    # recurrence

    def testMarkParentCompletedStopsChildRecurrence(self):
        self.child.setRecurrence(date.Recurrence("daily"))
        self.parent.setCompletionDateTime()
        self.assertFalse(self.child.recurrence())

    def testRecurringChildIsCompletedWhenParentIsCompleted(self):
        self.child.setRecurrence(date.Recurrence("daily"))
        self.parent.setCompletionDateTime()
        self.assertTrue(self.child.completed())

    def shouldMarkCompletedWhenAllChildrenCompleted(self, parent):
        return parent.shouldMarkCompletedWhenAllChildrenCompleted() == True or (
            parent.shouldMarkCompletedWhenAllChildrenCompleted() == None
            and self.markParentCompletedWhenAllChildrenCompleted == True
        )

    def testMarkLastChildCompletedMakesParentRecur(self):
        self.parent.setPlannedStartDateTime(self.now)
        self.parent.setRecurrence(date.Recurrence("weekly"))
        self.child.setCompletionDateTime(self.now)
        expectedPlannedStartDateTime = self.now
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedPlannedStartDateTime += date.TimeDelta(days=7)
        self.assertAlmostEqual(
            expectedPlannedStartDateTime.toordinal(),
            self.parent.plannedStartDateTime().toordinal(),
        )

    def testMarkLastChildCompletedMakesParentRecur_AndThusChildToo(self):
        self.child.setPlannedStartDateTime(self.now)
        self.parent.setRecurrence(date.Recurrence("weekly"))
        self.parent.setPlannedStartDateTime(self.now)
        self.child.setCompletionDateTime(self.now)
        expectedPlannedStartDateTime = self.now
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedPlannedStartDateTime += date.TimeDelta(days=7)
        self.assertAlmostEqual(
            expectedPlannedStartDateTime.toordinal(),
            self.child.plannedStartDateTime().toordinal(),
        )

    def testMarkLastChildCompletedMakesParentRecur_AndThusChildIsNotCompleted(self):
        self.parent.setRecurrence(date.Recurrence("weekly"))
        self.child.setCompletionDateTime()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.assertFalse(self.child.completed())
        else:
            self.assertTrue(self.child.completed())

    def testMarkLastGrandChildCompletedMakesParentRecur(self):
        self.parent.setRecurrence(date.Recurrence("weekly"))
        self.parent.setPlannedStartDateTime(self.now)
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDateTime(self.now)
        expectedPlannedStartDateTime = self.now
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedPlannedStartDateTime += date.TimeDelta(days=7)
        self.assertAlmostEqual(
            expectedPlannedStartDateTime.toordinal(),
            self.parent.plannedStartDateTime().toordinal(),
        )

    def testMarkLastGrandChildCompletedMakesParentRecur_AndThusGrandChildToo(self):
        self.parent.setRecurrence(date.Recurrence("weekly"))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDateTime(self.now)
        expectedPlannedStartDateTime = self.now
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedPlannedStartDateTime += date.TimeDelta(days=7)
        self.assertAlmostEqual(
            expectedPlannedStartDateTime.toordinal(),
            self.grandchild.plannedStartDateTime().toordinal(),
        )

    def testMarkLastChildCompletedMakesParentRecur_AndThusGrandChildIsNotCompleted(
        self,
    ):
        self.parent.setRecurrence(date.Recurrence("weekly"))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDateTime()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.assertFalse(self.grandchild.completed())
        else:
            self.assertTrue(self.grandchild.completed())


class MarkParentTaskCompletedTestsMixin(object):
    """Tests where we expect to parent task to be marked completed, based on
    the fact that all children are completed. This happens when the global
    setting is on and task is indifferent or the task specific setting is
    on."""

    def testMarkOnlyChildCompleted(self):
        self.child.setCompletionDateTime()
        self.assertTrue(self.parent.completed())

    def testMarkOnlyGrandchildCompleted(self):
        self.child.addChild(self.grandchild)
        self.grandchild.setCompletionDateTime()
        self.assertTrue(self.parent.completed())

    def testAddCompletedChildAsOnlyChild(self):
        self.grandchild.setCompletionDateTime()
        self.child.addChild(self.grandchild)
        self.assertTrue(self.child.completed())

    def testMarkChildCompletedYesterday(self):
        self.child.setCompletionDateTime(self.yesterday)
        self.assertEqual(self.yesterday, self.parent.completionDateTime())

    def testRemoveLastUncompletedChild(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime()
        self.parent.removeChild(self.child2)
        self.assertTrue(self.parent.completed())


class DontMarkParentTaskCompletedTestsMixin(object):
    """Tests where we expect the parent task not to be marked completed when
    all children are completed. This should be the case when the global
    setting is off and task is indifferent or when the task specific
    setting is off."""

    def testMarkOnlyChildCompletedDoesNotMarkParentCompleted(self):
        self.child.setCompletionDateTime()
        self.assertFalse(self.parent.completed())

    def testMarkOnlyGrandchildCompletedDoesNotMarkParentCompleted(self):
        self.child.addChild(self.grandchild)
        self.grandchild.setCompletionDateTime()
        self.assertFalse(self.parent.completed())

    def testAddCompletedChildAsOnlyChildDoesNotMarkParentCompleted(self):
        self.grandchild.setCompletionDateTime()
        self.child.addChild(self.grandchild)
        self.assertFalse(self.child.completed())

    def testMarkChildCompletedYesterdayDoesNotAffectParentCompletionDate(self):
        self.child.setCompletionDateTime(self.yesterday)
        self.assertEqual(date.DateTime(), self.parent.completionDateTime())

    def testRemoveLastUncompletedChildDoesNotMarkParentCompleted(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime()
        self.parent.removeChild(self.child2)
        self.assertFalse(self.parent.completed())


class MarkParentCompletedAutomaticallyIsOn(
    CommonTaskRelationshipManagerTestsMixin,
    MarkParentTaskCompletedTestsMixin,
    tctest.TestCase,
):
    markParentCompletedWhenAllChildrenCompleted = True


class MarkParentCompletedAutomaticallyIsOff(
    CommonTaskRelationshipManagerTestsMixin,
    DontMarkParentTaskCompletedTestsMixin,
    tctest.TestCase,
):
    markParentCompletedWhenAllChildrenCompleted = False


class MarkParentCompletedAutomaticallyIsOnButTaskSettingIsOff(
    CommonTaskRelationshipManagerTestsMixin,
    tctest.TestCase,
    DontMarkParentTaskCompletedTestsMixin,
):
    markParentCompletedWhenAllChildrenCompleted = True

    def setUp(self):
        super().setUp()
        for eachTask in self.parent, self.child:
            eachTask.setShouldMarkCompletedWhenAllChildrenCompleted(False)


class MarkParentCompletedAutomaticallyIsOffButTaskSettingIsOn(
    CommonTaskRelationshipManagerTestsMixin,
    tctest.TestCase,
    MarkParentTaskCompletedTestsMixin,
):
    markParentCompletedWhenAllChildrenCompleted = False

    def setUp(self):
        super().setUp()
        for eachTask in self.parent, self.child:
            eachTask.setShouldMarkCompletedWhenAllChildrenCompleted(True)
