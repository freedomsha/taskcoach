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

# from builtins import map
import os
import struct
import sys


_BINBASE = os.path.join(os.path.split(__file__)[0], "..", "bin.in")

if len(struct.pack("L", 0)) == 8:
    arch = "IA64"
else:
    arch = "IA32"

# if sys.platform == "linux2":
if sys.platform.startswith("linux"):
    # The user should install the binary packages
    pass
elif sys.platform == "darwin":
    sys.path.insert(0, os.path.join(_BINBASE, "macos", arch))
else:
    sys.path.insert(
        0,
        os.path.join(
            _BINBASE,
            "windows",
            "py%s" % "".join(map(str, sys.version_info[:2])),
        ),
    )

# unresolved reference
from _pysyncml import *
