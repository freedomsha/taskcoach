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

Module `itemctrl.py`

Ce module fournit des mixins pour gérer des contrôles avec des éléments tels que
`wx.ListCtrl`, `wx.TreeCtrl`, et `wx.TreeListCtrl`. Il étend la fonctionnalité
de ces contrôles pour inclure :
- Gestion des menus contextuels sur les éléments ou les colonnes.
- Prise en charge des événements de glisser-déposer.
- Colonnes masquables et redimensionnables.
- Colonnes avec tri et indicateurs de tri.

Classes principales :
- `_CtrlWithItemsMixin` : Classe de base pour les contrôles avec des éléments.
- `_CtrlWithPopupMenuMixin` : Ajoute la prise en charge des menus contextuels.
- `_CtrlWithItemPopupMenuMixin` : Menu contextuel pour des éléments spécifiques.
- `_CtrlWithColumnPopupMenuMixin` : Menu contextuel pour les colonnes.
- `_CtrlWithDropTargetMixin` : Permet de déposer des fichiers, URL ou e-mails.
- `CtrlWithToolTipMixin` : Ajoute des info-bulles spécifiques à chaque élément.
- `_CtrlWithHideableColumnsMixin` : Colonnes masquables.
- `_CtrlWithSortableColumnsMixin` : Colonnes avec tri et indicateurs de tri.
- `_CtrlWithAutoResizedColumnsMixin` : Colonnes redimensionnables automatiquement.
- `CtrlWithColumnsMixin` : Combine toutes les fonctionnalités ci-dessus.

Dépendances :
- wxPython : Le module utilise des classes comme `wx.ListCtrl`, `wx.TreeCtrl`, et
  `wx.TreeListCtrl`.
- wx.lib.agw.hypertreelist : Pour gérer des contrôles avancés.

Ce module dépend de méthodes spécifiques disponibles dans les contrôles hérités de
wxPython :
- `Bind`, `Unbind` : Gestion des événements.
- `PopupMenu`, `PopupMenuXY` : Gestion des menus contextuels.
- `GetMainWindow` : Accès à la fenêtre principale contenant le contrôle.
- `InsertColumn`, `DeleteColumn`, `GetColumnWidth`, etc. : Gestion des colonnes.

Assurez-vous que les classes utilisant ces mixins héritent des contrôles wxPython
appropriés pour éviter des erreurs.
"""
# pylint: disable=W0105

# from builtins import str
# from builtins import range
# from builtins import object
import wx
import inspect
from taskcoachlib.widgets import draganddrop
from taskcoachlib.widgets import autowidth
from taskcoachlib.widgets import tooltip
# from taskcoachlib.thirdparty import hypertreelist
# from taskcoachlib.thirdparty.customtreectrl import *
from wx.lib.agw import hypertreelist


class _CtrlWithItemsMixin(object):
    """
    Classe de base pour les contrôles contenant des éléments, comme `ListCtrl`,
    `TreeCtrl`, ou `TreeListCtrl`.

    Fournit des méthodes génériques pour vérifier les éléments, accéder aux
    données associées, et gérer les sélections.

    Méthodes principales :
        - `_itemIsOk` : Vérifie si un élément est valide.
        - `_objectBelongingTo` : Retourne l'objet associé à un élément.
        - `SelectItem` : Sélectionne ou désélectionne un élément.
    """

    def _itemIsOk(self, item):
        """
        Vérifie si un élément est valide.

        Args :
            item : L'élément à vérifier.

        Returns :
            bool : `True` si l'élément est valide, sinon `False`.
        """
        try:
            return item.IsOk()  # for Tree(List)Ctrl
        except AttributeError:
            return item != wx.NOT_FOUND  # for ListCtrl

    def _objectBelongingTo(self, item):
        if not self._itemIsOk(item):
            return None
        try:
            return self.GetItemPyData(item)  # TreeListCtrl  TODO: essayer GetItemData
        except AttributeError:
            return self.getItemWithIndex(item)  # ListCtrl

    def SelectItem(self, item, *args, **kwargs):
        """
        Sélectionne ou désélectionne un élément.

        Pour les `TreeCtrl` et `TreeListCtrl`, utilise `SelectItem`. Pour les
        `ListCtrl`, utilise `SetItemState`.

        Args :
            item : L'élément à sélectionner ou désélectionner.
            select (bool) : Si `True`, sélectionne l'élément. Sinon, le désélectionne.
        """
        try:
            # Tree(List)Ctrl:
            super().SelectItem(item, *args, **kwargs)
        except AttributeError:
            # ListCtrl:
            select = kwargs.get("select", True)
            newState = wx.LIST_STATE_SELECTED
            if not select:
                newState = ~newState
            self.SetItemState(item, newState, wx.LIST_STATE_SELECTED)


class _CtrlWithPopupMenuMixin(_CtrlWithItemsMixin):
    """ Classe de base pour les contrôles avec PopupMenu.

    Ajoute la prise en charge des menus contextuels.

    Méthodes principales :
        - `_attachPopupMenu` : Lie un gestionnaire d'événements pour afficher
          un menu contextuel.
    """

    @staticmethod
    def _attachPopupMenu(eventSource, eventTypes, eventHandler):
        """
        Lie un gestionnaire d'événements pour afficher un menu contextuel.

        Args :
            eventSource : La source de l'événement.
            eventTypes (list) : Liste des types d'événements.
            eventHandler : Gestionnaire d'événements pour afficher le menu.
        """
        for eventType in eventTypes:
            eventSource.Bind(eventType, eventHandler)


class _CtrlWithItemPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """ Le menu contextuel est sur les éléments.

    Ajoute un menu contextuel spécifique aux éléments.

    Méthodes principales :
        - `onItemPopupMenu` : Affiche le menu contextuel pour un élément.
    """

    def __init__(self, *args, **kwargs):
        self.__popupMenu = kwargs.pop("itemPopupMenu")
        super().__init__(*args, **kwargs)
        if self.__popupMenu is not None:
            self._attachPopupMenu(self,
                                  (wx.EVT_TREE_ITEM_RIGHT_CLICK, wx.EVT_CONTEXT_MENU),
                                  self.onItemPopupMenu)

    def onItemPopupMenu(self, event):
        """
        Affiche le menu contextuel pour un élément.

        Sélectionne l'élément sous le curseur avant d'afficher le menu.

        Args :
            event (wx.Event) : Événement déclenchant le menu contextuel.
        """
        # Assurez-vous que la fenêtre de ce contrôle est au foyer:
        try:
            window = event.GetEventObject().MainWindow
        except AttributeError:
            window = event.GetEventObject()
        window.SetFocus()
        if hasattr(event, "GetPoint"):
            # Make sure the item under the mouse is selected because that
            # is what users expect and what is most user-friendly. Not all
            # widgets do this by default, e.g. the TreeListCtrl does not.
            item = self.HitTest(event.GetPoint())[0]
            if not self._itemIsOk(item):
                return
            if not self.IsSelected(item):
                self.UnselectAll()
                self.SelectItem(item)
        self.PopupMenu(self.__popupMenu)


class _CtrlWithColumnPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """ Cette classe active un menu contextuel par clic droit sur les en-têtes de colonnes. Le menu contextuel
        doit s'attendre à ce qu'un columnIndex de propriété publique soit défini de sorte
        que le contrôle puisse indiquer au menu sur quelle colonne l'utilisateur a cliqué pour
        faire apparaître le menu.
    """

    def __init__(self, *args, **kwargs):
        self.__popupMenu = kwargs.pop("columnPopupMenu")
        super().__init__(*args, **kwargs)
        if self.__popupMenu is not None:
            self._attachPopupMenu(self, [wx.EVT_LIST_COL_RIGHT_CLICK],
                                  self.onColumnPopupMenu)

    def onColumnPopupMenu(self, event):
        # We store the columnIndex in the menu, because it's near to
        # impossible for commands in the menu to determine on what column the
        # menu was popped up.
        columnIndex = event.GetColumn()
        self.__popupMenu.columnIndex = columnIndex
        # Parce qu'un clic droit sur les en-têtes de colonnes ne donne pas automatiquement le focus
        # au contrôle, nous forçons le focus :
        try:
            window = event.GetEventObject().GetMainWindow()
        except AttributeError:
            window = event.GetEventObject()
        window.SetFocus()
        # self.PopupMenuXY(self.__popupMenu, *event.GetPosition())
        self.PopupMenu(self.__popupMenu)
        event.Skip(False)


class _CtrlWithDropTargetMixin(_CtrlWithItemsMixin):
    """
    Permet aux contrôles d'accepter des fichiers, URL ou e-mails déposés.

    Contrôle qui accepte que des fichiers, des e-mails ou des URL soient déposés sur des éléments.

    Méthodes principales :
        - `onDropURL` : Gère le dépôt d'une URL.
        - `onDropFiles` : Gère le dépôt de fichiers.
        - `onDropMail` : Gère le dépôt de courriers électroniques.
    """

    def __init__(self, *args, **kwargs):
        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)
        super().__init__(*args, **kwargs)
        if (
                self.__onDropURLCallback
                or self.__onDropFilesCallback
                or self.__onDropMailCallback
        ):
            dropTarget = draganddrop.DropTarget(
                self.onDropURL,
                self.onDropFiles,
                self.onDropMail,
                self.onDragOver,
            )
            self.GetMainWindow().SetDropTarget(dropTarget)

    def onDropURL(self, x, y, url):
        """
        Gère le dépôt d'une URL sur un élément.

        Args :
            x (int) : Coordonnée X du point de dépôt.
            y (int) : Coordonnée Y du point de dépôt.
            url (str) : URL déposée.
        """
        item = self.HitTest((x, y))[0]
        if self.__onDropURLCallback:
            self.__onDropURLCallback(self._objectBelongingTo(item), url)

    def onDropFiles(self, x, y, filenames):
        item = self.HitTest((x, y))[0]
        if self.__onDropFilesCallback:
            self.__onDropFilesCallback(self._objectBelongingTo(item), filenames)

    def onDropMail(self, x, y, mail):
        item = self.HitTest((x, y))[0]
        if self.__onDropMailCallback:
            self.__onDropMailCallback(self._objectBelongingTo(item), mail)

    def onDragOver(self, x, y, defaultResult):
        item, flags = self.HitTest((x, y))[:2]
        if self._itemIsOk(item):
            if flags & wx.TREE_HITTEST_ONITEMBUTTON:
                self.Expand(item)
        return defaultResult

    def GetMainWindow(self):
        try:
            return super().GetMainWindow()
        except AttributeError:
            # return self
            return self.GetCustomTreeCtrlInstance()  # Retourner une instance de CustomTreeCtrl

    def GetCustomTreeCtrlInstance(self):
        # Retourner une instance de CustomTreeCtrl, par exemple :
        return self.parent.GetTreeCtrl()


class CtrlWithToolTipMixin(_CtrlWithItemsMixin, tooltip.ToolTipMixin):
    """ Contrôle qui a une info-bulle différente pour chaque élément. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__tip = tooltip.SimpleToolTip(self)

    def OnBeforeShowToolTip(self, x, y):
        item, _, column = self.HitTest(wx.Point(x, y))
        domainObject = self._objectBelongingTo(item)
        if domainObject:
            tooltipData = self.getItemTooltipData(domainObject)
            doShow = any([data[1] for data in tooltipData])
            if doShow:
                self.__tip.SetData(tooltipData)
                return self.__tip
        return None


class CtrlWithItemsMixin(_CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin):
    pass


class Column(object):
    def __init__(self, name, columnHeader, *eventTypes, **kwargs):
        self.__name = name
        self.__columnHeader = columnHeader
        self.width = kwargs.pop(
            "width", hypertreelist._DEFAULT_COL_WIDTH
        )  # pylint: disable=W0212
        # The event types to use for registering an observer that is
        # interested in changes that affect this column:
        self.__eventTypes = eventTypes
        self.__sortCallback = kwargs.pop("sortCallback", None)
        self.__renderCallback = kwargs.pop(
            "renderCallback", self.defaultRenderer
        )
        self.__resizeCallback = kwargs.pop("resizeCallback", None)
        self.__alignment = kwargs.pop("alignment", wx.LIST_FORMAT_LEFT)
        self.__hasImages = "imageIndicesCallback" in kwargs
        self.__imageIndicesCallback = (
                kwargs.pop("imageIndicesCallback", self.defaultImageIndices)
                or self.defaultImageIndices
        )
        # NB: because the header image is needed for sorting a fixed header
        # image cannot be combined with a sortable column
        self.__headerImageIndex = kwargs.pop("headerImageIndex", -1)
        self.__editCallback = kwargs.get("editCallback", None)
        self.__editControlClass = kwargs.get("editControl", None)
        self.__parse = kwargs.get("parse", lambda value: value)
        self.__settings = kwargs.get(
            "settings", None
        )  # FIXME: Column shouldn't need to know about settings

    def name(self):
        return self.__name

    def header(self):
        return self.__columnHeader

    def headerImageIndex(self):
        return self.__headerImageIndex

    def eventTypes(self):
        return self.__eventTypes

    def setWidth(self, width):
        self.width = width
        if self.__resizeCallback:
            self.__resizeCallback(self, width)

    def sort(self, *args, **kwargs):
        if self.__sortCallback:
            self.__sortCallback(*args, **kwargs)

    def __filterArgs(self, func, kwargs):
        # actualKwargs = dict()  # Jamais utilisé !
        argNames = inspect.getfullargspec(func).args
        return dict([(name, value) for name, value in list(
            kwargs.items()) if name in argNames])

    def render(self, *args, **kwargs):
        return self.__renderCallback(
            *args, **self.__filterArgs(self.__renderCallback, kwargs))

    def defaultRenderer(self, *args, **kwargs):  # pylint: disable=W0613
        return str(args[0])

    def alignment(self):
        return self.__alignment

    def defaultImageIndices(self, *args, **kwargs):  # pylint: disable=W0613
        return {wx.TreeItemIcon_Normal: -1}

    def imageIndices(self, *args, **kwargs):
        return self.__imageIndicesCallback(*args, **kwargs)

    def hasImages(self):
        return self.__hasImages

    def isEditable(self):
        return self.__editControlClass is not None and self.__editCallback is not None

    def onEndEdit(self, item, newValue):
        self.__editCallback(item, newValue)

    def editControl(self, parent, item, columnIndex, domainObject):
        value = self.value(domainObject)
        kwargs = dict(settings=self.__settings) if self.__settings else dict()
        # pylint: disable=W0142
        return self.__editControlClass(parent, wx.ID_ANY, item, columnIndex,
                                       parent, value, **kwargs)

    def parse(self, value):
        return self.__parse(value)

    def value(self, domainObject):
        return getattr(domainObject, self.name())()

    def __eq__(self, other):
        return self.name() == other.name()


class _BaseCtrlWithColumnsMixin(object):
    """ Une classe de base pour tous les contrôles avec des colonnes. Notez que cette classe et
        ses sous-classes ne prennent pas en charge l'ajout ou la suppression de colonnes après
        le paramètre initial des colonnes. """

    def __init__(self, *args, **kwargs):
        self.__allColumns = kwargs.pop("columns")
        super().__init__(*args, **kwargs)
        # Ceci est utilisé pour garder une trace de quelle colonne a quel
        # index. La seule autre façon serait (et était) de trouver une colonne
        # en utilisant son en-tête, ce qui pose des problèmes lorsque plusieurs colonnes
        # ont le même en-tête. C'est une liste de tuples (index, colonne).
        self.__indexMap = []
        self._setColumns()

    def _setColumns(self):
        for columnIndex, column in enumerate(self.__allColumns):
            self._insertColumn(columnIndex, column)

    def _insertColumn(self, columnIndex, column):
        newMap = []
        for colIndex, col in self.__indexMap:
            if colIndex >= columnIndex:
                newMap.append((colIndex + 1, col))
            else:
                newMap.append((colIndex, col))
        newMap.append((columnIndex, column))
        self.__indexMap = newMap

        self.InsertColumn(columnIndex,
                          column.header() if column.headerImageIndex() == -1 else "",
                          format=column.alignment(), width=column.width)

        columnInfo = self.GetColumn(columnIndex)
        columnInfo.SetImage(column.headerImageIndex())
        self.SetColumn(columnIndex, columnInfo)

    def _deleteColumn(self, columnIndex):
        newMap = []
        for colIndex, col in self.__indexMap:
            if colIndex > columnIndex:
                newMap.append((colIndex - 1, col))
            elif colIndex < columnIndex:
                newMap.append((colIndex, col))
        self.__indexMap = newMap
        self.DeleteColumn(columnIndex)

    def _allColumns(self):
        return self.__allColumns

    def _getColumn(self, columnIndex):
        for colIndex, col in self.__indexMap:
            if colIndex == columnIndex:
                return col
        raise IndexError

    def _getColumnHeader(self, columnIndex):
        """ En-tête de colonne actuellement affiché dans la colonne avec index
            columnIndex. """
        return self.GetColumn(columnIndex).GetText()

    def _getColumnIndex(self, column):
        """ L'index de colonne actuel de la colonne 'colonne'. """
        try:
            return self.__allColumns.index(column)  # Uses overriden __eq__
        except ValueError:
            raise ValueError("%s: unknown column" % column.name())


class _CtrlWithHideableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """
    Prend en charge le masquage et l'affichage des colonnes.

    Méthodes principales :
        - `showColumn` : Affiche ou masque une colonne.
        - `isColumnVisible` : Vérifie si une colonne est visible.
    """

    def showColumn(self, column, show=True):
        """
        Affiche ou masque une colonne.

        showColumn affiche ou masque la colonne de la colonne.
        La colonne est en fait supprimée ou insérée dans le contrôle car
        bien que TreeListCtrl prenne en charge le masquage des colonnes,
        ListCtrl ne le fait pas.

        Args :
        column (Column) : La colonne à afficher ou masquer.
        show (bool) : Si `True`, affiche la colonne. Sinon, la masque.
    """
        columnIndex = self._getColumnIndex(column)
        if show and not self.isColumnVisible(column):
            self._insertColumn(columnIndex, column)
        elif not show and self.isColumnVisible(column):
            self._deleteColumn(columnIndex)

    def isColumnVisible(self, column):
        return column in self._visibleColumns()

    def _getColumnIndex(self, column):
        """ _getColumnIndex renvoie le columnIndex réel de la colonne si elle
            est visible, ou la position qu'elle aurait si elle était visible. """
        columnIndexWhenAllColumnsVisible = super()._getColumnIndex(column)
        for columnIndex, visibleColumn in enumerate(self._visibleColumns()):
            if super()._getColumnIndex(visibleColumn) >= columnIndexWhenAllColumnsVisible:
                return columnIndex
        return self.GetColumnCount()  # Column header not found

    def _visibleColumns(self):
        return [self._getColumn(columnIndex) for columnIndex in range(self.GetColumnCount())]


class _CtrlWithSortableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """ Cette classe ajoute des indicateurs de tri et des en-têtes de colonnes cliquables qui
        déclenchent des rappels pour (re)trier le contenu du contrôle. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.onColumnClick)
        self.__currentSortColumn = self._getColumn(0)
        self.__currentSortImageIndex = -1

    def onColumnClick(self, event):
        event.Skip(False)
        # Assurez-vous que la fenêtre dans laquelle se trouve ce contrôle a le focus :
        try:
            window = event.GetEventObject().GetMainWindow()
        except AttributeError:
            window = event.GetEventObject()
        window.SetFocus()
        columnIndex = event.GetColumn()
        if 0 <= columnIndex < self.GetColumnCount():
            column = self._getColumn(columnIndex)
            # Utilisez CallAfter pour vous assurer que la fenêtre dans laquelle se trouve ce contrôle est
            # activée avant de traiter le clic sur la colonne :
            wx.CallAfter(column.sort, event)

    def showSortColumn(self, column):
        if column != self.__currentSortColumn:
            self._clearSortImage()
        self.__currentSortColumn = column
        self._showSortImage()

    def showSortOrder(self, imageIndex):
        self.__currentSortImageIndex = imageIndex
        self._showSortImage()

    def _clearSortImage(self):
        self.__setSortColumnImage(-1)

    def _showSortImage(self):
        self.__setSortColumnImage(self.__currentSortImageIndex)

    def _currentSortColumn(self):
        return self.__currentSortColumn

    def __setSortColumnImage(self, imageIndex):
        columnIndex = self._getColumnIndex(self.__currentSortColumn)
        columnInfo = self.GetColumn(columnIndex)
        if columnInfo.GetImage() == imageIndex:
            pass  # The column is already showing the right image, so we're done
        else:
            columnInfo.SetImage(imageIndex)
            self.SetColumn(columnIndex, columnInfo)


class _CtrlWithAutoResizedColumnsMixin(autowidth.AutoColumnWidthMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.onEndColumnResize)

    def onEndColumnResize(self, event):
        """ Enregistrez les largeurs de colonne après que l'utilisateur ait fait un redimensionnement. """
        for index, column in enumerate(self._visibleColumns()):
            column.setWidth(self.GetColumnWidth(index))
        event.Skip()


class CtrlWithColumnsMixin(_CtrlWithAutoResizedColumnsMixin,
                           _CtrlWithHideableColumnsMixin,
                           _CtrlWithSortableColumnsMixin,
                           _CtrlWithColumnPopupMenuMixin):
    """ Combine toutes les fonctionnalités de ses quatre classes parents
    pour les contrôles avec colonnes. :
    - Redimensionnement automatique des colonnes.
    - Colonnes masquables.
    - Colonnes avec tri et indicateurs de tri.
    - Menu contextuel pour les colonnes.
    """

    def showColumn(self, column, show=True):
        super().showColumn(column, show)
        # Afficher l'indicateur de tri si la colonne qui vient d'être rendue visible est en cours de tri.
        if show and column == self._currentSortColumn():
            self._showSortImage()

    def _clearSortImage(self):
        # Effacer l'image de tri si la colonne en question est visible.
        if self.isColumnVisible(self._currentSortColumn()):
            super()._clearSortImage()

    def _showSortImage(self):
        # Affichez uniquement l'image de tri si la colonne en question est visible.
        if self.isColumnVisible(self._currentSortColumn()):
            super()._showSortImage()
