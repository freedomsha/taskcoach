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
#  Les packages les plus importants et les plus volumineux sont les packages
#  de domaine qui contiennent des classes pour les objets de domaine et
#  le package gui qui contient des visualiseurs, des boîtes de dialogue et d'autres composants gui.

from .splash import SplashScreen
from .mainwindow import MainWindow
from .dialog.editor import TaskEditor, EffortEditor, CategoryEditor
from .dialog.preferences import Preferences
from .iocontroller import IOController
from .mainwindow import MainWindow
from .remindercontroller import ReminderController
from .artprovider import init, itemImages
from .taskbaricon import TaskBarIcon
from . import viewer


# __all__ = ["artprovider", "dialog", "icons", "idlecontroller", "iocontroller", "iphone", "mainwindow", "menu", "newid", "printer", "remindercontroller", "splash", "status", "toolbar", "uicommand", "viewer", "windowdimensionstracker", "wizard"]
