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

# distutils is deprecated with removal planned for Python 3.12.
# from distutils.core import setup, Extension
from setuptools import setup, Extension

setup(
    name="sendinput",
    ext_modules=[
        Extension(
            "sendinput",
            ["sendinput.c"],
            define_macros=[("_WIN32_WINNT", "0x0502")],
        )
    ],
)
