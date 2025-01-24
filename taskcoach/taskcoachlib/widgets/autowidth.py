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

Module `autowidth.py`

Ce module fournit le mixin `AutoColumnWidthMixin`, qui permet de redimensionner
automatiquement une colonne dans un contrôle à colonnes (par exemple, `wx.ListCtrl`,
`wx.TreeListCtrl`, ou `wx.lib.agw.hypertreelist.HyperTreeList`).

Fonctionnalités principales :
- Ajuste dynamiquement la largeur d'une colonne pour utiliser tout l'espace
  disponible sans créer d'espace inutile ou de barres de défilement horizontales.
- Gère les événements comme le redimensionnement ou le glissement des colonnes.

Dépendances :
- wxPython : Ce mixin suppose que les classes qui l'utilisent héritent de
  `wx.Window` ou de contrôles similaires (`wx.ListCtrl`, `wx.TreeListCtrl`).

Classes :
- `AutoColumnWidthMixin` : Fournit le comportement de redimensionnement
  automatique des colonnes.

Avertissements :
- Lorsque vous utilisez ce mixin, assurez-vous que votre contrôle est configuré
  pour un mode "rapport" (report mode) si nécessaire.
- Si vous surchargez `EVT_SIZE`, appelez `event.Skip()` pour garantir que la
  méthode `OnResize` du mixin est appelée.

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Licence : GNU General Public License, version 3 ou ultérieure.
"""

# from __future__ import division
#
# from builtins import range
# from builtins import object
# from past.utils import old_div
import wx
from wx.lib.agw import hypertreelist
# from wx.lib.agw.hypertreelist import HyperTreeList
# try:
#    from ..thirdparty import hypertreelist
# except ImportError:
#    from ..thirdparty.agw import hypertreelist
from taskcoachlib import operating_system


class AutoColumnWidthMixin(object):
    """ Mixin pour ajouter un redimensionnement automatique des colonnes dans un contrôle.

    Ce mixin ajuste dynamiquement la largeur d'une colonne spécifique pour
    occuper tout l'espace disponible du contrôle, en réduisant ou en évitant
    les barres de défilement horizontales.

    Une classe mixte qui redimensionne automatiquement une colonne pour occuper
    la largeur restante d'un contrôle avec des colonnes (c'est-à-dire ListCtrl,
    TreeListCtrl).

    Cela amène le contrôle à occuper automatiquement la totalité width
    disponible, sans barre de défilement horizontale (sauf si absolument
    nécessaire) ni espace vide à droite de la dernière colonne.

    REMARQUE : Lorsque vous utilisez ce mixin avec un ListCtrl, assurez-vous que ListCtrl
               est en mode rapport.

    AVERTISSEMENT : Si vous remplacez l'événement EVT_SIZE dans votre contrôle, assurez-vous
                    d'appeler event.Skip() pour garantir que la méthode OnResize du mixin
                    est appelée.

    Attributs :
        ResizeColumn (int) : Index de la colonne à redimensionner automatiquement.
        ResizeColumnMinWidth (int) : Largeur minimale de la colonne redimensionnable.
        __is_auto_resizing (bool) : Indique si le redimensionnement automatique est activé.

    Méthodes principales :
        - `SetResizeColumn` : Définit la colonne à redimensionner automatiquement.
        - `ToggleAutoResizing` : Active ou désactive le redimensionnement automatique.
        - `OnResize` : Gère l'événement de redimensionnement de la fenêtre.
        - `DoResize` : Effectue le calcul et applique les nouvelles largeurs de colonnes.
        - `DistributeWidthAcrossColumns` : Répartit l'espace supplémentaire ou manquant
          sur les colonnes non redimensionnables.

    Remarque :
    Ce mixin dépend des méthodes suivantes, qui doivent être disponibles dans
    la classe finale :
        - `Bind`, `Unbind` : Gestion des événements wxPython.
        - `GetColumnWidth`, `SetColumnWidth` : Gestion des colonnes.
        - `GetColumnCount` : Nombre total de colonnes.
        - `GetClientSize`, `GetSize` : Dimensions du contrôle.

    Les méthodes comme Bind, Unbind, GetColumnWidth, etc., dépendent de wxPython.
    Ce mixin doit être utilisé dans des classes héritant de wx.ListCtrl,
    wx.TreeListCtrl, ou wx.lib.agw.hypertreelist.HyperTreeList.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise le mixin avec des paramètres spécifiques.

        Args :
            resizeableColumn (int) : Index de la colonne à redimensionner
                                     automatiquement (par défaut : -1).
            resizeableColumnMinWidth (int) : Largeur minimale de la colonne
                                             redimensionnable (par défaut : 50).
        """
        self.__is_auto_resizing = False
        self.ResizeColumn = kwargs.pop("resizeableColumn", -1)
        self.ResizeColumnMinWidth = kwargs.pop("resizeableColumnMinWidth", 50)
        super().__init__(*args, **kwargs)

    def SetResizeColumn(self, column):
        """
        Définit la colonne à redimensionner automatiquement.

        Args :
            column (int) : Index de la colonne.
        """
        self.ResizeColumn = column

    def ToggleAutoResizing(self, on):
        """
        Active ou désactive le redimensionnement automatique des colonnes.

        Args :
            on (bool) : Si `True`, active le redimensionnement automatique.
        """
        if on == self.__is_auto_resizing:
            return
        self.__is_auto_resizing = on
        if on:
            self.Bind(wx.EVT_SIZE, self.OnResize)  # wx.PyEventBinder.Bind
            self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnBeginColumnDrag)
            self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnEndColumnDrag)
            self.DoResize()
        else:
            self.Unbind(wx.EVT_SIZE)  # wx.PyEventBinder.Unbind
            self.Unbind(wx.EVT_LIST_COL_BEGIN_DRAG)
            self.Unbind(wx.EVT_LIST_COL_END_DRAG)

    def IsAutoResizing(self):
        return self.__is_auto_resizing

    def OnBeginColumnDrag(self, event):
        # pylint: disable=W0201
        if event.Column == self.ResizeColumn:
            self.__oldResizeColumnWidth = self.GetColumnWidth(self.ResizeColumn)  # wx.lib.agw.hypertreelist.HyperTreeList.GetColumnWidth
        # Temporarily unbind the EVT_SIZE to prevent resizing during dragging
        self.Unbind(wx.EVT_SIZE)
        if operating_system.isWindows():
            event.Skip()

    def OnEndColumnDrag(self, event):
        if event.Column == self.ResizeColumn and self.GetColumnCount() > 1:
            extra_width = self.__oldResizeColumnWidth - \
                              self.GetColumnWidth(self.ResizeColumn)
            self.DistributeWidthAcrossColumns(extra_width)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        wx.CallAfter(self.DoResize)
        event.Skip()

    def OnResize(self, event):
        """
        Gère l'événement de redimensionnement de la fenêtre et ajuste
        automatiquement les colonnes.

        Args :
            event (wx.Event) : Événement de redimensionnement.
        """
        event.Skip()
        if operating_system.isWindows():
            wx.CallAfter(self.DoResize)
        else:
            self.DoResize()

    def DoResize(self):
        """
        Effectue le calcul et applique les nouvelles largeurs des colonnes.

        Ne redimensionne que si :
        - Le contrôle est visible.
        - Le redimensionnement automatique est activé.
        - La colonne à redimensionner existe.
        """
        # if not self:
        #     return  # Évite une erreur potentielle de PyDeadObject
        # if not self.IsAutoResizing():
        if not self or not self.IsAutoResizing():
            return
        if self.GetSize().height < 32:  # Évite les bugs de hauteur minimale.
            return  # Évite un bug de mise à jour sans fin lorsque la hauteur est petite.
        if self.GetColumnCount() <= self.ResizeColumn:
            return  # Nothing to resize.

        unused_width = max(self.AvailableWidth - self.NecessaryWidth, 0)
        resize_column_width = self.ResizeColumnMinWidth + unused_width
        self.SetColumnWidth(self.ResizeColumn, resize_column_width)

    def DistributeWidthAcrossColumns(self, extra_width):
        """
        Répartit l'espace supplémentaire ou manquant sur les colonnes
        autres que `ResizeColumn`.

        Args :
            extra_width (int) : Espace supplémentaire ou manquant à répartir.
        """
        # Lorsque l'utilisateur redimensionne ResizeColumn, répartissez l'espace supplémentaire disponible
        # sur les autres colonnes, ou obtenez l'espace supplémentaire nécessaire à partir de
        # les autres colonnes. Les autres colonnes sont redimensionnées proportionnellement à
        # leur largeur précédente.
        other_columns = [index for index in range(self.GetColumnCount())
                         if index != self.ResizeColumn]
        total_width = float(sum(self.GetColumnWidth(index) for index in
                                other_columns))
        for column_index in other_columns:
            this_column_width = self.GetColumnWidth(column_index)
            # this_column_width += this_column_width / total_width * extra_width
            # this_column_width += old_div(this_column_width, total_width) * extra_width
            this_column_width += this_column_width // total_width * extra_width
            self.SetColumnWidth(column_index, this_column_width)
            # ou essayer :
            # adjusted_width = current_width + (current_width / total_width) * extra_width
            # self.SetColumnWidth(column_index, adjusted_width)

    def GetResizeColumn(self):
        if self.__resize_column == -1:
            return self.GetColumnCount() - 1
        else:
            return self.__resize_column

    def SetResizeColumn(self, column_index):
        self.__resize_column = column_index  # pylint: disable=W0201

    ResizeColumn = property(GetResizeColumn, SetResizeColumn)

    def GetAvailableWidth(self):
        available_width = self.GetClientSize().width
        if self.__is_scrollbar_visible() and self.__is_scrollbar_included_in_client_size():
            # scrollbar_width = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
            scrollbar_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
            available_width -= scrollbar_width
        return available_width

    AvailableWidth = property(GetAvailableWidth)

    def GetNecessaryWidth(self):
        necessary_width = 0
        for column_index in range(self.GetColumnCount()):
            if column_index == self.ResizeColumn:
                necessary_width += self.ResizeColumnMinWidth
            else:
                necessary_width += self.GetColumnWidth(column_index)
        return necessary_width

    NecessaryWidth = property(GetNecessaryWidth)

    # Remplacez toutes les méthodes qui manipulent les colonnes pour pouvoir redimensionner les
    # colonnes après tout ajout ou suppression.

    def InsertColumn(self, *args, **kwargs):
        """ Insérez la nouvelle colonne, puis redimensionnez. """
        result = super().InsertColumn(*args, **kwargs)
        self.DoResize()
        return result

    def DeleteColumn(self, *args, **kwargs):
        """ Supprimez la colonne, puis redimensionnez-la. """
        result = super().DeleteColumn(*args, **kwargs)
        self.DoResize()
        return result

    def RemoveColumn(self, *args, **kwargs):
        """ Retirez la colonne, puis redimensionnez."""
        result = super().RemoveColumn(*args, **kwargs)
        self.DoResize()
        return result

    def AddColumn(self, *args, **kwargs):
        """ Ajoutez la colonne, puis redimensionnez-la."""
        result = super().AddColumn(*args, **kwargs)
        self.DoResize()
        return result

    # Private helper methods:
    # Méthodes d'assistance privées :

    def __is_scrollbar_visible(self):
        """
        Vérifie si la barre de défilement verticale est visible.

        Returns :
            bool : `True` si visible, sinon `False`.
        """
        return self.MainWindow.HasScrollbar(wx.VERTICAL)

    def __is_scrollbar_included_in_client_size(self):
        """
        Vérifie si la barre de défilement est incluse dans la taille client.

        Returns :
            bool : `True` si incluse, sinon `False`.
        """
        # NOTE: Sur GTK, la barre de défilement est incluse dans la taille du client, mais sur
        # Windows, elle n'est pas incluse.
        if operating_system.isWindows():
            return isinstance(self, hypertreelist.HyperTreeList)
        return True
