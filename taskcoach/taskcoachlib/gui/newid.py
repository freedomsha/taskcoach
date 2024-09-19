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
    """
        Fournisseur d'identifiants pour les éléments d'interface utilisateur dans wxPython.

        Cette classe gère les identifiants uniques nécessaires pour les éléments d'interface
        utilisateur, en évitant les conflits et en assurant la disponibilité des identifiants.
        """
    # # ajout conseillé par chatgpt pour mieux gérer les identifiants (3 lignes)
    # def __init__(self):
    #     super().__init__()
    #     self._ids = set()

    def get(self) -> int:
        """
        Obtenir un nouvel identifiant unique.

        Cette méthode génère un nouvel identifiant unique en utilisant wx.ID_ANY (pas wx.NewIdRef()) et l'ajoute
        à l'ensemble des identifiants gérés par cette classe.

        Returns :
            int : Un nouvel identifiant unique.
        """
        if self:
            return self.pop()
        # return wx.NewId()
        # # méthode dépréciée
        # # return wx.NewIdRef().GetId()
        # # new_id = wx.NewIdRef()
        # # self.add(new_id)
        # new_id = wx.NewIdRef().GetId()
        # self._ids.add(new_id)
        # self.add(new_id)
        # print(f"tclib.gui.newid.py IdProvider.get add: new_id = {new_id} for self: {self}")  # Ajout de journalisation
        # # return new_id
        # # return wx.NewIdRef()
        return wx.ID_ANY

    def put(self, id_: int):
        """
        Libérer un identifiant.

        Cette méthode retire l'identifiant spécifié de l'ensemble des identifiants gérés par
        cette classe, le rendant disponible pour une réutilisation future.

        Args :
            id_ (int) : L'identifiant à libérer.
        """
        if id_ > 0:
            self.add(id_)
        # # nouveau code :
        # if id_ in self:
        #     self._ids.remove(id_)
        #     self.remove(id_)
        #     print(f"tclib.gui.newid.py IdProvider.put remove: id_ = {id_} for self: {self}")  # Ajout de journalisation
        #     # Aucun besoin de faire autre chose, wx gère automatiquement les identifiants.


# Création d'une instance unique de IdProvider pour l'utilisation dans l'application.
IdProvider = IdProvider()
