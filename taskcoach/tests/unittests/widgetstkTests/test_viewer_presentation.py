from types import SimpleNamespace
import unittest

from taskcoachlib.guitk.viewer.notetk import Noteviewer


class TestNoteViewerPresentation(unittest.TestCase):
    def test_presentation_returns_the_current_base_viewer_presentation(self):
        current_presentation = object()
        stale_sorter = object()
        viewer = SimpleNamespace(
            _Viewer__presentation=current_presentation,
            _sorter=stale_sorter,
        )

        self.assertIs(Noteviewer.presentation(viewer), current_presentation)


if __name__ == "__main__":
    unittest.main()
