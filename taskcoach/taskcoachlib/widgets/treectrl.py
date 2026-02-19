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

# from builtins import range
from taskcoachlib import operating_system
import logging
import wx
from wx.lib.agw import customtreectrl as customtree
from wx.lib.agw import hypertreelist
from wx.lib.agw.ultimatelistctrl import (
    UltimateListCtrl,
    UltimateListMainWindow,
)
from wx.dataview import TreeListCtrl
from taskcoachlib.widgets import itemctrl, draganddrop

log = logging.getLogger(__name__)


# class BaseHyperTreeList(
#     hypertreelist.HyperTreeList, customtree.CustomTreeCtrl
# ):
class BaseHyperTreeList(hypertreelist.HyperTreeList):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=0,
        agwStyle=wx.TR_DEFAULT_STYLE,
        validator=wx.DefaultValidator,
        name="HyperTreeList",
        *args,
        **kwargs,
    ):
        super().__init__(
            parent, id, pos, size, style, agwStyle, validator, name
        )
        # Bind our own size handler to fix scrollbar issues on Windows.
        # The base HyperTreeList.OnSize only calls DoHeaderLayout() which
        # repositions child windows but doesn't recalculate scrollbars.
        self.Bind(wx.EVT_SIZE, self.__onSize)

    def __onSize(self, event):
        """Handle size events to ensure scrollbars are recalculated.

        On Windows, side-docked AUI panes don't get scrollbars when the content
        exceeds the visible area because HyperTreeList's OnSize handler only
        repositions child windows without recalculating scrollbars. We fix this
        by calling AdjustMyScrollbars() after the base OnSize handler runs.
        """
        event.Skip()  # Let base class handle layout first
        # Schedule scrollbar adjustment after the layout is complete
        wx.CallAfter(self.__safeAdjustScrollbars)

    def __safeAdjustScrollbars(self):
        """Safely adjust scrollbars, guarding against deleted C++ objects."""
        try:
            main_win = self.GetMainWindow()
            if main_win:
                main_win.AdjustMyScrollbars()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass


# class HyperTreeList(BaseHyperTreeList, draganddrop.TreeCtrlDragAndDropMixin):
class HyperTreeList(draganddrop.TreeCtrlDragAndDropMixin, BaseHyperTreeList):
    def __init__(self, *args, **kwargs):
        log.debug("HyperTreeList.__init__ : initialisation d'HyperTreeList.")
        self._editCtrl = None  # nouvel attribut pour TreeListCtrl
        super().__init__(*args, **kwargs)
        BaseHyperTreeList.__init__(self, *args, **kwargs)
        if operating_system.isGTK():
            self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.__on_item_collapsed)

    def __on_item_collapsed(self, event):
        event.Skip()
        # On Ubuntu, when the user has scrolled to the bottom of the tree
        # and collapses an item, the tree is not redrawn correctly. Refreshing
        # solves this. See http://trac.wxwidgets.org/ticket/11704
        # wx.CallAfter(self.MainWindow.Refresh)
        wx.CallAfter(self.__safeRefresh)

    def __safeRefresh(self):
        """Safely refresh the main window, guarding against deleted C++ objects."""
        try:
            if self.MainWindow:
                self.MainWindow.Refresh()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def GetSelections(self):  # pylint: disable=C0103
        """
        Si l'élément racine est masqué, il ne doit jamais être sélectionné.
        Malheureusement, CustomTreeCtrl et HyperTreeList permettent de le sélectionner.
        Remplacez GetSelections pour résoudre ce problème.
        """
        selections = super().GetSelections()
        if self.HasFlag(wx.TR_HIDE_ROOT):
            root_item = self.GetRootItem()
            if root_item and root_item in selections:
                selections.remove(root_item)
        return selections

    def GetMainWindow(self, *args, **kwargs):  # pylint: disable=C0103
        """
        Avoir un GetMainWindow local afin que nous puissions créer une propriété MainWindow.
        """
        return super().GetMainWindow(
            *args, **kwargs
        )  # *args et **kwargs semblent inutiles ici !
        # return (
        #     super().GetMainWindow()
        # )  # *args et **kwargs semblent inutiles ici !

    MainWindow = property(fget=GetMainWindow)

    def HitTest(self, point, flags=0):  # pylint: disable=W0221, C0103
        """Renvoie toujours un triple-tuple (item, flags, column)."""
        # if type(point) == type(()):  # isinstance (tuple ?)
        if type(point) is type(()):  # isinstance (tuple ?)
            point = wx.Point(point[0], point[1])
        hit_test_result = super().HitTest(point)
        if len(hit_test_result) == 2:
            hit_test_result += (0,)
        if hit_test_result[0] is None:
            hit_test_result = (wx.TreeItemId(),) + hit_test_result[1:]
        return hit_test_result

    def isClickablePartOfNodeClicked(self, event):
        """
        Indique si l'utilisateur a double-cliqué sur une partie du nœud qui
        peut également recevoir des clics de souris réguliers.
        """
        return self.__is_collapse_expand_button_clicked(event)

    def __is_collapse_expand_button_clicked(self, event):
        flags = self.HitTest(event.GetPosition())[1]
        # return flags & wx.TREE_HITTEST_ONITEMBUTTON  # Class 'TreeItemId' does not define '__and__', so the '&' operator cannot be used on its instances
        if not isinstance(flags, int):
            flags = int(flags)
        return bool(flags & wx.TREE_HITTEST_ONITEMBUTTON)

    def select(self, selection):
        """Select items whose PyData is in the selection list.
        Returns the first selected tree item (for scrolling).

        Note: UnselectAll() is required before SelectItem() after a tree rebuild.
        This appears to be a HyperTreeList quirk/bug - SelectItem() silently fails
        without it, even though DoSelectItem has unselect_others=True by default.
        See: https://github.com/wxWidgets/Phoenix/issues/1164 for related issues.
        """
        first_selected_item = None
        self.UnselectAll()
        for item in self.GetItemChildren(recursively=True):
            # self.SelectItem(item, self.GetItemPyData(item) in selection)
            pydata = self.GetItemPyData(item)
            if pydata in selection:
                self.SelectItem(item, True)
                if first_selected_item is None:
                    first_selected_item = item
        return first_selected_item

    def clear_selection(self):
        self.UnselectAll()
        self.selectCommand()

    def select_all(self):
        if self.GetItemCount() > 0:
            self.SelectAll()
        self.selectCommand()

    def isAnyItemCollapsable(self):
        for item in self.GetItemChildren():
            if self.__is_item_collapsable(item):
                return True
        return False

    def isAnyItemExpandable(self):
        for item in self.GetItemChildren():
            if self.__is_item_expandable(item):
                return True
        return False

    def __is_item_expandable(self, item):
        return self.ItemHasChildren(item) and not self.IsExpanded(item)

    def __is_item_collapsable(self, item):
        return self.ItemHasChildren(item) and self.IsExpanded(item)

    def IsLabelBeingEdited(self):
        # return bool(self.GetLabelTextCtrl())
        # # Ancien code
        return bool(self._editCtrl)

    def StopEditing(self):
        if self.IsLabelBeingEdited():
            self.GetLabelTextCtrl().StopEditing()

    def GetLabelTextCtrl(self):
        # return self.GetMainWindow()._editCtrl  # pylint: disable=W0212
        return (
            self._editCtrl
        )  # pylint: disable=W0212 AttributeError: 'TreeListCtrl' object has no attribute '_editCtrl'
        # if self.GetMainWindow().IsEditing():
        #     return self.GetEditControl()  # Méthode wxPython Phoenix
        # return None

        # Vérifiez la définition de la classe MainWindow pour voir si _Editctrl
        # est initialisé. S'il est censé être un widget pour l'édition,
        # assurez-vous qu'il est correctement créé et affecté à la variable d'instance.
        # S'il n'est pas censé exister, ajustez la méthode getLabelTextCtrl
        # pour ne pas le référencer ou gérer son absence potentielle.
        # TODO : _editCtrl est un attribut interne de wxPython Classic.
        # Dans wxPython Phoenix (4.x), l'édition des labels est gérée via des événements et des méthodes publiques.
        # Remplace l'accès à _editCtrl par l'API officielle.

    def GetItemCount(self):
        root_item = self.GetRootItem()
        return (
            self.GetChildrenCount(root_item, recursively=True)
            if root_item
            else 0
        )


class TreeListCtrl(
    itemctrl.CtrlWithItemsMixin,
    itemctrl.CtrlWithColumnsMixin,
    itemctrl.CtrlWithToolTipMixin,
    HyperTreeList,
):
    # itemctrl.CtrlWithToolTipMixin, HyperTreeList, UltimateListCtrl, hypertreelist.TreeListMainWindow):  TODO
    # TreeListCtrl uses ALIGN_LEFT, ..., ListCtrl uses LIST_FORMAT_LEFT, ... for
    # specifying alignment of columns. This dictionary allows us to map from the
    # ListCtrl constants to the TreeListCtrl constants:
    alignmentMap = {
        wx.LIST_FORMAT_LEFT: wx.ALIGN_LEFT,
        wx.LIST_FORMAT_CENTRE: wx.ALIGN_CENTRE,
        wx.LIST_FORMAT_CENTER: wx.ALIGN_CENTER,
        wx.LIST_FORMAT_RIGHT: wx.ALIGN_RIGHT,
    }
    ct_type = 0

    def __init__(
        self,
        parent,
        columns,
        selectCommand,
        editCommand,
        dragAndDropCommand,
        itemPopupMenu=None,
        columnPopupMenu=None,
        *args,
        **kwargs,
    ):
        log.debug(
            "TreeListCtrl.__init__ : initialisation du contrôle de liste en arbre."
        )
        # Fenêtre principale pour la gestion du focus avec AuiManager
        self.__adapter = parent
        # Liste des objets actuellement sélectionnés
        self.__selection = []
        # Information sur le double-clic de l'utilisateur
        self.__user_double_clicked = False
        # Liste des colonnes qui peuvent contenir des images
        self.__columns_with_images = []
        # Police par défaut
        self.__default_font = wx.NORMAL_FONT
        self.__refreshing = (
            False  # Flag to suppress selection events during refresh
        )
        # ajout d'attribut :
        self._editCtrl = None  # Initialise explicitement ici
        self.selectCommand = selectCommand
        self.editCommand = editCommand
        self.dragAndDropCommand = dragAndDropCommand
        kwargs.setdefault("resizeableColumn", 0)
        self._mainWin = None
        log.debug("TreeListCtrl.__init__ : avant super().")
        super().__init__(
            parent,
            style=self.__get_style(),
            agwStyle=self.__get_agw_style(),
            columns=columns,
            itemPopupMenu=itemPopupMenu,
            columnPopupMenu=columnPopupMenu,
            *args,
            **kwargs,
        )
        log.debug("TreeListCtrl.__init__ : après super()")
        self.bindEventHandlers(selectCommand, editCommand, dragAndDropCommand)

    def bindEventHandlers(
        self, selectCommand, editCommand, dragAndDropCommand
    ):
        self.selectCommand = selectCommand
        self.editCommand = editCommand
        self.dragAndDropCommand = dragAndDropCommand
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelect)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onItemActivated)
        # We deal with double clicks ourselves, to prevent the default behaviour
        # of collapsing or expanding nodes on double click.
        self.GetMainWindow().Bind(wx.EVT_LEFT_DCLICK, self.onDoubleClick)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onBeginEdit)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onEndEdit)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.onItemExpanding)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)

    def onSetFocus(self, event):  # pylint: disable=W0613
        # Envoyez un événement de focus enfant pour informer AuiManager que nous avons reçu le focus
        # afin qu'il active notre volet
        wx.PostEvent(self._main_win, wx.ChildFocusEvent(self._main_win))
        # wx.PostEvent(self, wx.ChildFocusEvent(self))
        self.SetFocus()
        # event.Skip()

    def getItemTooltipData(self, item):
        return self.__adapter.getItemTooltipData(item)

    def getItemCTType(self, item):  # pylint: disable=W0613
        return self.ct_type

    def curselection(self):
        # return [self.GetItemPyData(item) for item in self.GetSelections()]
        # Guard against deleted C++ object - can happen when wx.CallAfter
        # callback executes after window destruction (e.g., closing nested dialogs)
        try:
            # Filter out None values - GetItemPyData can return None for some items
            # (e.g., root items or items without associated PyData)
            return [
                data
                for item in self.GetSelections()
                if (data := self.GetItemPyData(item)) is not None
            ]
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            return []

    def RefreshAllItems(self, count=0):  # pylint: disable=W0613
        # self.Freeze()
        # On gèle le widget pour éviter les scintillements et préparer le Thaw(),
        # seulement si ce n'est pas déjà fait
        already_frozen = self.IsFrozen()
        # if not self.IsFrozen():
        if not already_frozen:
            self.Freeze()
        self.__refreshing = True
        try:
            self.StopEditing()
            # self.__refreshing = True  # Supprime les événements de sélection pendant la reconstruction
            self.__selection = self.curselection()
            self.DeleteAllItems()

            self.__columns_with_images = [
                index
                for index in range(self.GetColumnCount())
                if self.__adapter.hasColumnImages(index)
            ]

            root_item = self.GetRootItem()
            if not root_item:
                root_item = self.AddRoot("Hidden root")

            self._addObjectRecursively(root_item)

        finally:
            # # self.Thaw()
            # # On ne dégèle que si le widget est effectivement gelé
            # if self.IsFrozen():
            #     self.Thaw()
            # 2. On libère le flag de rafraîchissement
            self.__refreshing = False
            # 3. On ne dégèle que si nous avons nous-mêmes appelé Freeze
            if not already_frozen and self.IsFrozen():
                try:
                    self.Thaw()
                except Exception as e:
                    log.debug("Erreur lors du Thaw (ignorée) : %s", e)

        # # Restore selection AFTER Thaw - SelectItem doesn't work while Frozen
        # selected_item = None
        # if self.__selection:
        #     selected_item = self.select(self.__selection)
        # selections = self.GetSelections()
        # # Use the item returned by select() for scrolling if GetSelections fails
        # scroll_target = selections[0] if selections else selected_item
        # # if selections:
        # if scroll_target:
        #     self.GetMainWindow()._current = (
        #         self.GetMainWindow()._key_current
        #         # ) = selections[0]
        #         # self.ScrollTo(selections[0])
        #     ) = scroll_target
        #     self.ScrollTo(scroll_target)
        # # self.Thaw()
        # # On ne dégèle que si le widget est effectivement gelé
        # if self.IsFrozen():
        #     self.Thaw()
        # # Force immediate repaint to reduce visible flicker after rebuild
        # self.GetMainWindow().Refresh(eraseBackground=False)

    def RefreshItems(self, *objects):
        self.__selection = self.curselection()
        self._refreshTargetObjects(self.GetRootItem(), *objects)

    def _refreshTargetObjects(self, parent_item, *target_objects):
        child_item, cookie = self.GetFirstChild(parent_item)
        while child_item:
            item_object = self.GetItemPyData(child_item)
            if item_object in target_objects:
                self._refreshObjectCompletely(
                    item=child_item, domain_object=item_object
                )
            self._refreshTargetObjects(child_item, *target_objects)
            child_item, cookie = self.GetNextChild(parent_item, cookie)

    def _refreshObjectCompletely(self, item, domain_object=None, *args):
        self.__refresh_aspects(
            ("ItemType", "Columns", "Font", "Colors", "Selection"),
            item,
            domain_object,
            check=True,
            *args,
        )
        if isinstance(
            self.GetMainWindow(), customtree.CustomTreeCtrl
        ):  # Semble plutôt être une instance de _CtrlWithDropTargetMixin
            self.GetMainWindow().RefreshLine(
                item
            )  # Seule customtreectrl a une méthode RefreshLine.

    def _addObjectRecursively(self, parent_item, parent_object=None):
        """
        Méthode qui peuple l'interface.

        Args:
            parent_item:
            parent_object:

        Returns:

        """
        for child_object in self.__adapter.children(parent_object):
            child_item = self.AppendItem(
                parent_item,
                "",
                self.getItemCTType(child_object),
                data=child_object,
            )
            self._refreshObjectMinimally(child_item, child_object)
            expanded = self.__adapter.getItemExpanded(child_object)
            if expanded:
                self._addObjectRecursively(child_item, child_object)
                # Call Expand on the item instead of on the tree
                # (self.Expand(childItem)) to prevent lots of events
                # (EVT_TREE_ITEM_EXPANDING/EXPANDED) being sent
                child_item.Expand()
            else:
                self.SetItemHasChildren(
                    child_item, self.__adapter.children(child_object)
                )

    def _refreshObjectMinimally(self, *args, **kwargs):
        self.__refresh_aspects(
            ("Columns", "Colors", "Font", "Selection"), *args, **kwargs
        )

    def __refresh_aspects(self, aspects, domain_object, *args, **kwargs):
        for aspect in aspects:
            # refresh_aspect = getattr(self, "_refresh%s" % aspect)
            refresh_aspect = getattr(self, f"_refresh{aspect}")
            refresh_aspect(domain_object, *args, **kwargs)

    def _refreshItemType(self, item, domain_object, check=False):
        ct_type = self.getItemCTType(domain_object)
        if not check or (check and ct_type != self.GetItemType(item)):
            self.SetItemType(item, ct_type)

    def _refreshColumns(self, item, domain_object, check=False):
        for column_index in range(self.GetColumnCount()):
            self._refreshColumn(item, domain_object, column_index, check=check)

    def _refreshColumn(self, item, domain_object, column_index, check=False):
        aspects = (
            ("Text", "Image")
            if column_index in self.__columns_with_images
            else ("Text",)
        )
        self.__refresh_aspects(
            aspects, item, domain_object, column_index, check=check
        )

    def _refreshText(self, item, domain_object, column_index, check=False):
        text = self.__adapter.getItemText(domain_object, column_index)
        if text.count("\n") > 3:
            text = "\n".join(text.split("\n")[:4]) + " ..."
        if not check or (check and text != item.GetText(column_index)):
            item.SetText(column_index, text)

    def _refreshImage(self, item, domain_object, column_index, check=False):
        images = self.__adapter.getItemImages(domain_object, column_index)
        for which, image in list(images.items()):
            image = image if image >= 0 else -1
            if not check or (
                check and image != item.GetImage(which, column_index)
            ):
                item.SetImage(column_index, image, which)

    def _refreshColors(self, item, domain_object, check=False):
        bg_color = (
            domain_object.backgroundColor(recursive=True) or wx.NullColour
        )
        if not check or (
            check and bg_color != self.GetItemBackgroundColour(item)
        ):
            self.SetItemBackgroundColour(item, bg_color)
        fg_color = (
            domain_object.foregroundColor(recursive=True) or wx.NullColour
        )
        if not check or (check and fg_color != self.GetItemTextColour(item)):
            self.SetItemTextColour(item, fg_color)

    def _refreshFont(self, item, domain_object, check=False):
        font = domain_object.font(recursive=True) or self.__default_font
        if not check or (check and font != self.GetItemFont(item)):
            self.SetItemFont(item, font)

    def _refreshSelection(self, item, domain_object, check=False):
        select = domain_object in self.__selection
        if not check or (check and select != item.IsSelected()):
            item.SetHilight(select)

    # Event handlers

    def onSelect(self, event):
        # Skip selection events during refresh to avoid spurious updates
        if self.__refreshing:
            event.Skip()
            return
        # Use CallAfter to prevent handling the select while items are
        # being deleted:
        # wx.CallAfter(self.selectCommand)
        wx.CallAfter(self.__safeSelectCommand)
        event.Skip()

    def __safeSelectCommand(self):
        """Safely call selectCommand, guarding against deleted C++ objects."""
        try:
            if self:
                self.selectCommand()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def onKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.editCommand(event)
        elif event.GetKeyCode() == wx.WXK_F2 and self.GetSelections():
            # self.EditLabel(self.GetSelections()[0])
            self.EditLabel(self.GetSelections()[0], column=0)
        else:
            event.Skip()

    def OnDrop(self, drop_item, drag_items, part, column):
        drop_item = (
            None
            if drop_item == self.GetRootItem()
            else self.GetItemPyData(drop_item)
        )
        drag_items = list(
            self.GetItemPyData(drag_item) for drag_item in drag_items
        )
        wx.CallAfter(
            # self.dragAndDropCommand, drop_item, drag_items, part, column
            self.__safeDragAndDropCommand,
            drop_item,
            drag_items,
            part,
            column,
        )

    def __safeDragAndDropCommand(self, drop_item, drag_items, part, column):
        """Safely call dragAndDropCommand, guarding against deleted C++ objects."""
        try:
            if self:
                self.dragAndDropCommand(drop_item, drag_items, part, column)
                # Expand the drop target if items were dropped on it
                if drop_item is not None:
                    self._expandDropTarget(drop_item)
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def _expandDropTarget(self, drop_item):
        """Expand the drop target item so the dropped children are visible."""
        # Find the tree item for the drop target
        for item in self.GetItemChildren(recursively=True):
            if self.GetItemPyData(item) == drop_item:
                if self.GetChildrenCount(
                    item, recursively=False
                ) > 0 or self.ItemHasChildren(item):
                    self.Expand(item)
                break

    def onItemExpanding(self, event):
        event.Skip()
        item = event.GetItem()
        if self.GetChildrenCount(item, recursively=False) == 0:
            domain_object = self.GetItemPyData(item)
            self._addObjectRecursively(item, domain_object)

    def onDoubleClick(self, event):
        self.__user_double_clicked = True
        if self.isClickablePartOfNodeClicked(event):
            event.Skip(False)
        else:
            self.onItemActivated(event)

    def onItemActivated(self, event):
        """
        Attacher la colonne sur laquelle vous avez cliqué à l'événement
        afin que nous puissions l'utiliser ailleurs.
        """
        column_index = self.__column_under_mouse()
        if column_index >= 0:
            event.columnName = self._getColumn(column_index).name()
        self.editCommand(event)
        event.Skip(False)

    def __column_under_mouse(self):
        log.debug("TreeListCtrl.__column_under_mouse : début")
        mouse_position = self.GetMainWindow().ScreenToClient(
            wx.GetMousePosition()
        )
        item, _, column = self.HitTest(mouse_position)
        if item:
            # Only get the column name if the hittest returned an item,
            # otherwise the item was activated from the menu or by double-clicking
            #  on a portion of the tree view not containing an item.
            log.debug(
                f"TreeListCtrl.__column_under_mouse : fin1 colonne={column}"
            )
            return max(0, column)
        else:
            log.debug("TreeListCtrl.__column_under_mouse : fin2")
            return -1

    # Inline editing

    def onBeginEdit(self, event):
        if self.__user_double_clicked:
            event.Veto()
            self.__user_double_clicked = False
        elif self.IsLabelBeingEdited():
            # Don't start editing another label when the user is still editing
            # a label. This prevents left-over text controls in the tree.
            event.Veto()
        else:
            event.Skip()

    def onEndEdit(self, event):
        if event._editCancelled:  # pylint: disable=W0212
            event.Skip()
            return
        event.Veto()  # Let us update the tree
        domain_object = self.GetItemPyData(event.GetItem())
        new_value = event.GetLabel()
        column = self._getColumn(event.GetInt())
        column.onEndEdit(domain_object, new_value)

    def CreateEditCtrl(self, item, column_index):
        column = self._getColumn(column_index)
        domain_object = self.GetItemPyData(item)
        return column.editControl(
            self.GetMainWindow(), item, column_index, domain_object
        )

    # Override CtrlWithColumnsMixin with TreeListCtrl specific behaviour:

    def _setColumns(self, *args, **kwargs):
        super()._setColumns(*args, **kwargs)
        self.SetMainColumn(0)
        for column_index in range(self.GetColumnCount()):
            self.SetColumnEditable(
                column_index, self._getColumn(column_index).isEditable()
            )

    # Extend TreeMixin with TreeListCtrl specific behaviour:

    @staticmethod
    def __get_style():
        # return wx.WANTS_CHARS
        # Enable horizontal scrollbar for natural column resizing
        return wx.WANTS_CHARS | wx.HSCROLL

    @staticmethod
    def __get_agw_style():
        agw_style = (
            wx.TR_DEFAULT_STYLE
            | wx.TR_HIDE_ROOT
            | wx.TR_MULTIPLE
            | wx.TR_EDIT_LABELS
            | wx.TR_HAS_BUTTONS
            | wx.TR_FULL_ROW_HIGHLIGHT
            | customtree.TR_HAS_VARIABLE_ROW_HEIGHT
        )
        #  L'initialisation de la classe parente est fondamentale.
        #  Les styles agwStyle (TR_NO_HEADER_BUTTONS, TR_FULL_ROW_HIGHLIGHT,
        #  TR_COLUMN_LOCK, etc.) influencent le comportement de l'en-tête et des colonnes.
        if operating_system.isMac():
            agw_style |= wx.TR_NO_LINES
        agw_style &= ~hypertreelist.TR_NO_HEADER  # TR_NO_HEADER_BUTTONS ?
        return agw_style

    def DeleteColumn(self, column_index):
        self.RemoveColumn(column_index)

    def InsertColumn(self, column_index, column_header, *args, **kwargs):
        alignment = self.alignmentMap[
            kwargs.pop("format", wx.LIST_FORMAT_LEFT)
        ]
        if column_index == self.GetColumnCount():
            self.AddColumn(column_header, *args, **kwargs)
        else:
            super().InsertColumn(column_index, column_header, *args, **kwargs)
        self.SetColumnAlignment(column_index, alignment)
        self.SetColumnEditable(
            column_index, self._getColumn(column_index).isEditable()
        )

    def showColumn(self, *args, **kwargs):
        """
        Arrêter l'édition avant de masquer ou d'afficher une colonne
        pour éviter les problèmes
        lors du redessinage du contenu du contrôle de la liste arborescente.
        """
        self.StopEditing()
        super().showColumn(*args, **kwargs)


class CheckTreeCtrl(TreeListCtrl):
    def __init__(
        self,
        parent,
        columns,
        selectCommand,
        checkCommand,
        editCommand,
        dragAndDropCommand,
        itemPopupMenu=None,
        *args,
        **kwargs,
    ):
        self.__checking = False
        # nouvel attribut :
        self._mainWin = None
        super().__init__(
            parent,
            columns,
            selectCommand,
            editCommand,
            dragAndDropCommand,
            itemPopupMenu,
            *args,
            **kwargs,
        )
        self.checkCommand = checkCommand
        self.Bind(customtree.EVT_TREE_ITEM_CHECKED, self.onItemChecked)
        # self.GetMainWindow().bind(wx.EVT_LEFT_DOWN, self.onMouseLeftDown)
        # AttributeError: 'TreeListMainWindow' object has no attribute 'bind'
        # Sauf que mainwindow crée la méthode bind() !
        self.GetMainWindow().Bind(wx.EVT_LEFT_DOWN, self.onMouseLeftDown)

    def getItemCTType(self, domain_object):
        """Use radio buttons (ct_type == 2) when the object has "exclusive"
        children, meaning that only one child can be checked at a time. Use
        check boxes (ct_type == 1) otherwise."""
        # if self.getIsItemCheckable(domain_object):
        return (
            2 if self.getItemParentHasExclusiveChildren(domain_object) else 1
        )
        # else:
        #    return 0

    def CheckItem(self, item, checked=True):
        if self.GetItemType(item) == 2:
            # Use UnCheckRadioParent because CheckItem always keeps at least
            # one item selected, which we don't want to enforce
            self.UnCheckRadioParent(item, checked)
        else:
            super().CheckItem(item, checked)

    def onMouseLeftDown(self, event):
        """Par défaut, le widget HyperTreeList ne permet pas de décocher
        un élément radio. Puisque nous souhaitons prendre en charge
        la décoche d'un élément radio, nous recherchons la souris
        laissée enfoncée et décochons l'élément et tous
        ses enfants si l'utilisateur clique sur un élément radio
        déjà sélectionné."""
        position = self.GetMainWindow().CalcUnscrolledPosition(
            event.GetPosition()
        )
        item, flags, dummy_column = self.HitTest(position)
        if (
            item
            and item.GetType() == 2
            and (flags & customtree.TREE_HITTEST_ONITEMCHECKICON)
            and self.IsItemChecked(item)
        ):
            self.__uncheck_item_recursively(item)
        else:
            event.Skip()

    def __uncheck_item_recursively(
        self, item, parent_is_expanded=True, disable_item=False
    ):
        if item.GetType():
            self.__uncheck_item(item, torefresh=parent_is_expanded)
        if disable_item:
            self.EnableItem(item, False, torefresh=parent_is_expanded)
        parent_is_expanded = item.IsExpanded()
        child, cookie = self.GetFirstChild(item)
        while child:
            self.__uncheck_item_recursively(
                child, parent_is_expanded, disable_item=True
            )
            child, cookie = self.GetNextChild(item, cookie)

    def __uncheck_item(self, item, torefresh):
        self.GetMainWindow().CheckItem2(
            item, checked=False, torefresh=torefresh
        )
        event = customtree.TreeEvent(
            customtree.wxEVT_TREE_ITEM_CHECKED, self.GetId()
        )
        event.SetItem(item)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def _refreshObjectCompletely(self, item, domain_object=None, *args):
        super()._refreshObjectCompletely(item, domain_object, *args)
        self._refreshCheckState(item, domain_object)

    def _refreshObjectMinimally(self, item, domain_object):
        super()._refreshObjectMinimally(item, domain_object)
        self._refreshCheckState(item, domain_object)

    def _refreshCheckState(self, item, domain_object):
        # Use CheckItem2 so no events get sent:
        # self.CheckItem2(item, self.getIsItemChecked(domain_object))
        checked = self.getIsItemChecked(domain_object)
        if checked is None:
            # Mixed state - enable 3-state and set undetermined
            item.Set3State(True)
            item.Set3StateValue(wx.CHK_UNDETERMINED)
        else:
            # Normal checked/unchecked state
            if item.Is3State():
                item.Set3State(False)
            self.CheckItem2(item, checked)
        parent = item.GetParent()
        while parent:
            if self.GetItemType(parent) == 2:
                self.EnableItem(item, self.IsItemChecked(parent))
                break
            parent = parent.GetParent()

    def refreshAllCheckStates(self):
        """Refresh the check state of all items without rebuilding the tree."""
        for item in self.GetItemChildren(recursively=True):
            domain_object = self.GetItemPyData(item)
            if domain_object is not None:
                self._refreshCheckState(item, domain_object)

    def onItemChecked(self, event):
        if self.__checking:
            # Ignore checked events while we're making the tree consistent,
            # only invoke the callback:
            self.checkCommand(event, final=False)
            return
        self.__checking = True
        item = event.GetItem()
        # Uncheck mutually exclusive children:
        for child in self.GetItemChildren(item):
            if self.GetItemType(child) == 2:
                self.CheckItem(child, False)
                # Recursively uncheck children of mutually exclusive children:
                for grandchild in self.GetItemChildren(
                    child, recursively=True
                ):
                    self.CheckItem(grandchild, False)
        # If this item is mutually exclusive, recursively uncheck siblings
        # and parent:
        parent = item.GetParent()
        if parent and self.GetItemType(item) == 2:
            for child in self.GetItemChildren(parent):
                if child == item:
                    continue
                self.CheckItem(child, False)
                for grandchild in self.GetItemChildren(
                    child, recursively=True
                ):
                    self.CheckItem(grandchild, False)
            if self.GetItemType(parent) != 2:
                self.CheckItem(parent, False)
        self.__checking = False
        self.checkCommand(event, final=True)

    def onItemActivated(self, event):
        if self.__is_double_clicked(event):
            # Invoke super.onItemActivated to edit the item
            super().onItemActivated(event)
        else:
            # Item is activated, let another event handler deal with the event
            event.Skip()

    @staticmethod
    def __is_double_clicked(event):
        return hasattr(event, "LeftDClick") and event.LeftDClick()
