import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def load_virtual_list_ctrl():
    itemctrltk = ModuleType("taskcoachlib.widgetstk.itemctrltk")
    itemctrltk.CtrlWithItemsMixin = type("CtrlWithItemsMixin", (), {})
    itemctrltk.CtrlWithColumnsMixin = type("CtrlWithColumnsMixin", (), {})
    itemctrltk.CtrlWithToolTipMixin = type("CtrlWithToolTipMixin", (), {})
    itemctrltk.Column = type("Column", (), {})

    module_name = "taskcoachlib.widgetstk.listctrltk_for_refresh_test"
    spec = importlib.util.spec_from_file_location(
        module_name,
        Path(__file__).parents[3]
        / "taskcoachlib"
        / "widgetstk"
        / "listctrltk.py",
    )
    module = importlib.util.module_from_spec(spec)
    original_itemctrltk = sys.modules.get("taskcoachlib.widgetstk.itemctrltk")
    sys.modules["taskcoachlib.widgetstk.itemctrltk"] = itemctrltk
    try:
        spec.loader.exec_module(module)
    finally:
        if original_itemctrltk is None:
            del sys.modules["taskcoachlib.widgetstk.itemctrltk"]
        else:
            sys.modules["taskcoachlib.widgetstk.itemctrltk"] = original_itemctrltk
    return module.VirtualListCtrl


VirtualListCtrl = load_virtual_list_ctrl()


class ViewerStub:
    def __init__(self):
        self.items = ["effort one", "effort two"]

    def getItemWithIndex(self, index):
        return self.items[index]

    def getItemText(self, item, column):
        return f"{item} / {column}"


class TreeviewStub:
    def __init__(self):
        self._VirtualListCtrl__parent = None
        self._item_to_object = {"old-row": "stale effort"}
        self.rows = {"old-row": ()}

    def get_children(self):
        return tuple(self.rows)

    def delete(self, item_id):
        del self.rows[item_id]

    def __getitem__(self, key):
        assert key == "columns"
        return ("period", "task")

    def getItemText(self, item, column):
        return VirtualListCtrl.getItemText(self, item, column)

    def insert(self, parent, index, values):
        item_id = f"row-{len(self.rows)}"
        self.rows[item_id] = values
        return item_id

    def _setObjectForItem(self, item_id, item):
        self._item_to_object[item_id] = item


def test_refresh_all_items_populates_rows_from_viewer():
    viewer = ViewerStub()
    tree = TreeviewStub()

    VirtualListCtrl.setDataSource(tree, viewer)
    VirtualListCtrl.RefreshAllItems(tree, len(viewer.items))

    assert list(tree.rows.values()) == [
        ["effort one / 0", "effort one / 1"],
        ["effort two / 0", "effort two / 1"],
    ]
    assert tree._item_to_object == {
        "row-0": "effort one",
        "row-1": "effort two",
    }
