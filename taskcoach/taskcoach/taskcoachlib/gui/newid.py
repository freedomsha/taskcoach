"""
Task Coach - Your friendly task manager
Copyright (C) 2019 Task Coach developers <developers@taskcoach.org>

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

import wx


# Le problème semble être lié à l'épuisement des identifiants uniques
# pour les éléments d'interface utilisateur dans wxPython.
# L'application utilise des identifiants négatifs générés automatiquement
# et il semble qu'ils soient utilisés au-delà de leurs limites.
class IdProvider(set):
    # ajout conseillé par chatgpt pour mieux gérer les identifiants
    # def __init__(self):
    #    # self._ids = set()

    def get(self):
        # if self:
        #    return self.pop()
        # # return wx.NewId()
        # # méthode dépréciée
        # return wx.NewIdRef().GetId()
        # new_id = wx.NewIdRef().GetId()
        new_id = wx.NewIdRef()
        # self._ids.add(new_id)
        self.add(new_id)
        # print(f"tclib.gui.newid.py IdProvider.get add: new_id = {new_id} for self: {self}")  # Ajout de journalisation
        return new_id

    def put(self, id_):
        # if id_ > 0:
        #    self.add(id_)
        if id_ in self:
            # print(f"tclib.gui.newid.py IdProvider.put remove: id_ = {id_} for self: {self}")  # Ajout de journalisation
            # self._ids.remove(id_)
            self.remove(id_)
            # Aucun besoin de faire autre chose, wx gère automatiquement les identifiants.


IdProvider = IdProvider()
