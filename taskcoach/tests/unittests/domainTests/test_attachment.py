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

import os
from pubsub import pub

from ... import tctest
from taskcoachlib.domain.attachment import attachment


class GetRelativePathTest(tctest.TestCase):
    def testBaseAndPathEqual(self):
        self.assertEqual("", attachment.getRelativePath("/test", "/test"))

    def testPathIsSubDirOfBase(self):
        self.assertEqual("subdir", attachment.getRelativePath("/test/subdir", "/test"))

    def testBaseIsSubDirOfPath(self):
        self.assertEqual("..", attachment.getRelativePath("/test", "/test/subdir"))

    def testBaseAndPathAreDifferent(self):
        self.assertEqual(
            os.path.join("..", "bar"), attachment.getRelativePath("/bar", "/foo")
        )


class FileAttachmentTest(tctest.TestCase):
    def setUp(self):
        super().setUp()
        self.filename = ""
        self.attachment = attachment.FileAttachment("filename")
        self.events = []

    def onEvent(self, newValue, sender):  # pylint: disable=W0221
        self.events.append((newValue, sender))

    def openAttachment(self, filename):
        self.filename = filename

    def testCreateFileAttachment(self):
        self.assertEqual("filename", self.attachment.location())

    def testOpenFileAttachmentWithRelativeFilename(self):
        self.attachment.open(openAttachment=self.openAttachment)
        self.assertEqual("filename", self.filename)

    def testOpenFileAttachmentWithRelativeFilenameAndWorkingDir(self):
        self.attachment.open("/home", openAttachment=self.openAttachment)
        self.assertEqual(
            os.path.normpath(os.path.join("/home", "filename")), self.filename
        )

    def testOpenFileAttachmentWithAbsoluteFilenameAndWorkingDir(self):
        att = attachment.FileAttachment("/home/frank/attachment.txt")
        att.open("/home/jerome", openAttachment=self.openAttachment)
        self.assertEqual(
            os.path.normpath(os.path.join("/home/frank/attachment.txt")), self.filename
        )

    def testCopy(self):
        copy = self.attachment.copy()
        # print(f"type(copy)={type(copy)}")
        # print(f"dir(copy)={dir(copy)}")
        # print(f"type(self.attachment.location)={type(self.attachment.location)}")
        # print(f"dir(self.attachment.location)={dir(self.attachment.location)}")
        self.assertEqual(copy.location(), self.attachment.location)
        self.attachment.setDescription("new")  # Attention, risque d'écraser self.__description
        # self.assertTrue(callable(copy.description), "description n'est plus une méthode !")

        self.assertEqual(copy.location(), self.attachment.location)

    def testLocationNotification(self):
        pub.subscribe(self.onEvent, self.attachment.locationChangedEventType())
        self.attachment.setLocation("new location")
        self.assertEqual([("new location", self.attachment)], self.events)

    def testModificationEventTypes(self):
        Attachment = attachment.Attachment
        # pylint: disable=E1101
        self.assertEqual(
            [
                # Attachment.notesChangedEventType(),
                Attachment.subjectChangedEventType(),
                Attachment.descriptionChangedEventType(),
                Attachment.appearanceChangedEventType(),
                Attachment.orderingChangedEventType(),
                Attachment.locationChangedEventType(),
            ],
            Attachment.modificationEventTypes(),
        )
