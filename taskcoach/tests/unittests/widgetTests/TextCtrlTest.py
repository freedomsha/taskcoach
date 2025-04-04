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

from ... import tctest
from taskcoachlib import widgets


class BaseTextCtrlTest(tctest.wxTestCase):
    def testRemoveAnyControlCharactersEnteredByUser(self):
        textctrl = widgets.textctrl.BaseTextCtrl(self.frame, "T\x02\x01est\x09")
        self.assertEqual("Test\t", textctrl.GetValue())


class MultiLineTextCtrlTest(tctest.wxTestCase):
    def testOpenWebbrowserOnURLClick(self):
        textctrl = widgets.MultiLineTextCtrl(self.frame)
        textctrl.AppendText("test http://test.com/ test")
        # FIXME: simulate a mouseclick on the urlpo

    def testSetInsertionPointAtStart(self):
        textctrl = widgets.MultiLineTextCtrl(self.frame, text="Hiya")
        self.assertEqual(0, textctrl.GetInsertionPoint())
