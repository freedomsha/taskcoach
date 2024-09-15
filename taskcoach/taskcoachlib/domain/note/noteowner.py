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

# from builtins import object
# try:
#    from .. import base
# except ImportError:
from taskcoachlib.domain import base


class NoteOwner(object, metaclass=base.DomainObjectOwnerMetaclass):
    """ Mixin class for (other) domain objects that may contain notes. """

    # __metaclass__ = base.DomainObjectOwnerMetaclass
    # lequel NoteOwner utiliser ? domain/note/noteowner ou domain/base/owner ?
    __ownedType__ = "Note"
