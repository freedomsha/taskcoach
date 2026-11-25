"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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

Adaptations for platform and GUI-specific workarounds."""

from taskcoachlib.config.gui import get_gui
if get_gui() == "wx":
    # from taskcoachlib.workarounds.display_wx import *
    # from taskcoachlib.workarounds.font_wx import *
    # from taskcoachlib.workarounds.encodings_wx import *
    from taskcoachlib.workarounds import display, font
from taskcoachlib.workarounds import encodings
from taskcoachlib.workarounds.exception import ExceptionAsUnicode

__all__ = ["ExceptionAsUnicode"]