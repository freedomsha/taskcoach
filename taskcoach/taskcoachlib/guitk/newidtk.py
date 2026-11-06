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

import logging

log = logging.getLogger(__name__)

# Constante équivalente à wx.ID_ANY
ID_ANY = -1

class IdProvider:
    """
    Fournisseur d'identifiants pour les éléments d'interface utilisateur.
    Génère des IDs uniques positifs et permet leur réutilisation.
    """

    def __init__(self):
        self._available_ids = set()  # IDs libérés et réutilisables
        self._next_id = 1  # Compteur pour les nouveaux IDs

    def get(self):
        """
        Obtenir un nouvel identifiant unique.
        Réutilise un ID disponible si possible, sinon génère un nouveau.
        Équivalent à wx.NewId() ou wx.NewIdRef().GetId()
        """
        if self._available_ids:
            return self._available_ids.pop()
        new_id = self._next_id
        self._next_id += 1
        log.debug(f"IdProvider.get: new_id = {new_id}")
        return new_id

    def put(self, id_):
        """
        Libérer un identifiant pour réutilisation future.
        Équivalent à la libération d'ID dans wxPython.
        """
        if id_ > 0 and id_ < self._next_id:
            self._available_ids.add(id_)
            log.debug(f"IdProvider.put: id_ = {id_} added to available pool")

# Instance unique pour toute l'application
IdProvider = IdProvider()
