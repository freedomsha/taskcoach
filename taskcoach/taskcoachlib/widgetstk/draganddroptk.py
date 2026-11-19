# -*- coding: utf-8 -*-
"""Glisser-déposer Tkinter pour Task Coach.

Deux mécanismes indépendants :
* déplacement interne d'éléments ttk.Treeview (Tkinter standard) ;
* réception de fichiers et de texte externes (nécessite tkinterdnd2).

Les signatures OnDrop et validateDrag de l'ancien mixin wxPython sont
préservées. Le mixin ne déplace PAS les données : OnDrop appartient à l'appelant.
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

log = logging.getLogger(__name__)

try:
    from tkinterdnd2 import DND_FILES, DND_TEXT
except ImportError:  # Le DnD interne fonctionne sans cette dépendance.
    DND_FILES = DND_TEXT = None


def _file_url_to_path(value):
    """Convertit une URL file:// en chemin local, si applicable."""
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "file":
        return value
    path = url2pathname(unquote(parsed.path))
    if parsed.netloc and parsed.netloc.lower() != "localhost":
        return "//" + parsed.netloc + path
    return path


class TkDnDDropTarget:
    """Récepteur externe de fichiers et de texte via tkinterdnd2.

    Le widget doit appartenir à une fenêtre TkinterDnD.Tk (ou disposer de
    drop_target_register et dnd_bind). Les callbacks reçoivent les données
    décodées et peuvent retourner une valeur ; l'action de dépôt est « copy ».
    """

    def __init__(self, widget, on_files=None, on_text=None):
        if DND_FILES is None:
            raise RuntimeError(
                "Le dépôt depuis d'autres applications nécessite tkinterdnd2 "
                "(pip install tkinterdnd2) et une racine TkinterDnD.Tk."
            )
        if not hasattr(widget, "drop_target_register") or not hasattr(widget, "dnd_bind"):
            raise TypeError("Le widget doit être compatible avec tkinterdnd2.")
        self.widget = widget
        self.on_files = on_files
        self.on_text = on_text
        formats = []
        if on_files is not None:
            formats.append(DND_FILES)
        if on_text is not None:
            formats.append(DND_TEXT)
        if formats:
            widget.drop_target_register(*formats)
            # Un seul gestionnaire évite les doubles notifications de dépôt.
            widget.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):
        data = getattr(event, "data", "")
        kind = str(getattr(event, "type", ""))
        # tkinterdnd2 fournit généralement event.type = 'DND_Files'/'DND_Text'.
        is_files = kind.lower() in ("dnd_files", "dnd-files", "files")
        if not is_files and self.on_files and not self.on_text:
            is_files = True
        if is_files and self.on_files:
            try:
                files = list(self.widget.tk.splitlist(data))
            except tk.TclError:
                log.warning("Liste Tcl de fichiers invalide : %r", data)
                return "refuse_drop"
            self.on_files([_file_url_to_path(path) for path in files], event)
        elif self.on_text:
            self.on_text(data, event)
        else:
            return "refuse_drop"
        return "copy"


class FileDropTarget:
    """Adaptateur de callback wx : onDropCallback(x, y, filenames).

    Appeler ``attach(widget)`` pour activer la réception externe.
    """

    def __init__(self, onDropCallback=None, onDragOverCallback=None):
        self.onDropCallback = onDropCallback
        self.onDragOverCallback = onDragOverCallback
        self._receiver = None

    def attach(self, widget):
        self._receiver = TkDnDDropTarget(widget, on_files=self._on_files)
        return self

    def _on_files(self, files, event):
        self.OnDropFiles(getattr(event, "x", 0), getattr(event, "y", 0), files)

    def OnDropFiles(self, x, y, filenames):
        if self.onDropCallback is None:
            return False
        self.onDropCallback(x, y, filenames)
        return True

    def OnDragOver(self, x, y, defaultResult):
        if self.onDragOverCallback is not None:
            return self.onDragOverCallback(x, y, defaultResult)
        return defaultResult


class TextDropTarget:
    """Adaptateur wx : onDropCallback(text)."""

    def __init__(self, onDropCallback):
        self.onDropCallback = onDropCallback
        self._receiver = None

    def attach(self, widget):
        self._receiver = TkDnDDropTarget(widget, on_text=self._on_text)
        return self

    def _on_text(self, text, event):
        self.OnDropText(getattr(event, "x", 0), getattr(event, "y", 0), text)

    def OnDropText(self, x, y, text):
        self.onDropCallback(text)
        return True


class DropTarget:
    """Réception de fichiers et d'URL/texte.

    Les formats propriétaires de courriels wx (Outlook, Thunderbird, Claws)
    ne sont pas émulés : ils exigent des intégrations propres à l'OS.
    """

    def __init__(self, onDropFileCallback=None, onDropUrlCallback=None,
                 onDragOverCallback=None, **kwargs):
        self.onDropFileCallback = onDropFileCallback
        self.onDropUrlCallback = onDropUrlCallback
        self.onDragOverCallback = onDragOverCallback
        self._receiver = None
        if kwargs:
            log.debug("Arguments de compatibilité ignorés : %s", sorted(kwargs))

    def attach(self, widget):
        self._receiver = TkDnDDropTarget(
            widget,
            on_files=self._files if self.onDropFileCallback else None,
            on_text=self._text if self.onDropUrlCallback else None,
        )
        return self

    def reinit(self):
        """Aucun objet de données wx à réinitialiser."""

    def _files(self, files, event):
        if self.onDropFileCallback:
            self.onDropFileCallback(getattr(event, "x", 0),
                                    getattr(event, "y", 0), files)

    def _text(self, value, event):
        if self.onDropUrlCallback:
            self.onDropUrlCallback(getattr(event, "x", 0),
                                   getattr(event, "y", 0), value)

    def OnDragOver(self, x, y, result):
        if self.onDragOverCallback:
            return self.onDragOverCallback(x, y, result)
        return result


class FileUrlDropTarget(DropTarget):
    """Alias explicite pour la réception de fichiers et d'URL."""


class TreeHelperMixin:
    """Méthodes de compatibilité wx pour une classe dérivée de ttk.Treeview.

    Exemple : ``class MyTree(TreeCtrlDragAndDropMixin, ttk.Treeview): ...``
    """

    def __init__(self, *args, **kwargs):
        self._item_to_object = {}
        super().__init__(*args, **kwargs)

    def GetRootItem(self):
        """La racine implicite de ttk.Treeview est la chaîne vide."""
        return ""

    def GetItemChildren(self, item=None, recursively=False):
        """Retourne les enfants directs ou tous les descendants, sans doublons."""
        result = []
        for child in self.get_children(item or ""):
            result.append(child)
            if recursively:
                result.extend(self.GetItemChildren(child, True))
        return result

    def GetItemParent(self, item):
        return self.parent(item) if item else ""

    def GetItemPyData(self, item):
        return self._item_to_object.get(item)

    def SetItemPyData(self, item, data):
        self._item_to_object[item] = data

    def delete(self, *items):
        """Nettoie les associations d'objets lors de la suppression d'items."""
        for item in items:
            if self.exists(item):
                for descendant in [item] + self.GetItemChildren(item, True):
                    self._item_to_object.pop(descendant, None)
        return super().delete(*items)

    def GetSelections(self):
        return tuple(self.selection())

    def UnselectAll(self):
        self.selection_remove(self.selection())

    def SelectItem(self, item, select=True):
        if select:
            self.selection_add(item)
        else:
            self.selection_remove(item)


class TreeCtrlDragAndDropMixin(TreeHelperMixin):
    """Glisser-déposer interne d'un ttk.Treeview.

    ``OnDrop(dropItem, dragItems, part, column)`` doit être redéfini.
    ``part`` vaut -1 (tiers supérieur), 0 (centre) ou 1 (tiers inférieur).
    ``dropItem == ''`` signifie la racine implicite.

    Le mixin ne modifie jamais l'arbre automatiquement : l'application est
    responsable de son modèle, de l'ordre des éléments et des rafraîchissements.
    """

    DRAG_THRESHOLD = 5
    HOVER_EXPAND_MS = 550

    def __init__(self, *args, **kwargs):
        self._validateDragCallback = kwargs.pop("validateDrag", None)
        self._dragStartPos = None
        self._dragItems = []
        self._dragColumn = 0
        self._dragActive = False
        self._dropItem = ""
        self._dropPart = 0
        self._dropColumn = 0
        self._hoverItem = None
        self._hoverAfter = None
        self._oldCursor = None
        super().__init__(*args, **kwargs)
        self.bind("<ButtonPress-1>", self._on_press, add="+")
        self.bind("<B1-Motion>", self._on_motion, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.bind("<Escape>", self._on_escape, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")

    def OnDrop(self, dropItem, dragItems, part, column):
        """À implémenter dans la classe concrète (mise à jour du modèle)."""
        raise NotImplementedError

    def _on_press(self, event):
        if self._dragActive:
            self.StopDragging()
        self._dragStartPos = (event.x, event.y)
        self._dragColumn = self._column_at(event.x)
        self._pressItem = self.identify_row(event.y)

    def _on_motion(self, event):
        if self._dragStartPos is None:
            return
        if not self._dragActive:
            dx = abs(event.x - self._dragStartPos[0])
            dy = abs(event.y - self._dragStartPos[1])
            if max(dx, dy) < self.DRAG_THRESHOLD:
                return
            if not self._begin_drag():
                self._dragStartPos = None
                return
        self.OnDragging(event)

    def _begin_drag(self):
        if not self._pressItem or not self.exists(self._pressItem):
            return False
        selection = tuple(self.selection())
        if self._pressItem not in selection:
            selection = (self._pressItem,)
        # Ne pas déplacer simultanément un parent et ses descendants.
        selected = set(selection)
        self._dragItems = [item for item in selection if not any(
            ancestor in selected for ancestor in self._ancestors(item))]
        if not self._dragItems:
            return False
        self._dragActive = True
        self.SetCursorToDragging()
        return True

    def _ancestors(self, item):
        parent = self.parent(item)
        while parent:
            yield parent
            parent = self.parent(parent)

    def _column_at(self, x):
        col = self.identify_column(x)
        try:
            return int(col[1:]) if col.startswith("#") else 0
        except (ValueError, AttributeError):
            return 0

    def _hit_drop(self, event):
        item = self.identify_row(event.y) or ""
        column = self._column_at(event.x)
        part = 0
        if item:
            box = self.bbox(item)
            if box and box[3] > 0:
                fraction = (event.y - box[1]) / box[3]
                part = -1 if fraction < 1 / 3 else (1 if fraction > 2 / 3 else 0)
        return item, part, column

    def IsValidDropTarget(self, dropTarget):
        """Valide une cible et appelle le callback historique si fourni."""
        if self._validateDragCallback is not None:
            value = self._validateDragCallback(
                self.GetItemPyData(dropTarget),
                [self.GetItemPyData(item) for item in self._dragItems],
                self._dragColumn,
            )
            if value is not None:
                return bool(value)
        if not dropTarget:
            return True
        if dropTarget in self._dragItems:
            return False
        if any(dropTarget in self.GetItemChildren(item, True)
               for item in self._dragItems):
            return False
        # Fidélité à wx : pas de dépôt sur le parent actuel.
        if any(dropTarget == self.parent(item) for item in self._dragItems):
            return False
        return True

    def OnDragging(self, event):
        if not self._dragActive:
            return
        item, part, column = self._hit_drop(event)
        self._dropItem, self._dropPart, self._dropColumn = item, part, column
        valid = self.IsValidDropTarget(item)
        self._set_cursor("hand2" if valid else "X_cursor")
        self._schedule_expand(item if valid else "")
        self._UpdateDropFeedback(item if valid else "", part, column)

    def _schedule_expand(self, item):
        if item == self._hoverItem:
            return
        self._cancel_expand()
        self._hoverItem = item
        if item and self.exists(item) and self.get_children(item):
            try:
                is_open = self.tk.getboolean(self.item(item, "open"))
            except (ValueError, tk.TclError):
                is_open = bool(self.item(item, "open"))
            if not is_open:
                self._hoverAfter = self.after(self.HOVER_EXPAND_MS,
                                               lambda: self._expand_hover(item))

    def _expand_hover(self, item):
        self._hoverAfter = None
        if self._dragActive and self._hoverItem == item and self.exists(item):
            self.item(item, open=True)

    def _cancel_expand(self):
        if self._hoverAfter is not None:
            try:
                self.after_cancel(self._hoverAfter)
            except tk.TclError:
                pass
            self._hoverAfter = None
        self._hoverItem = None

    def _UpdateDropFeedback(self, item, part, column):
        """Point d'extension : dessiner une indication de dépôt si souhaité."""

    def _ClearDropFeedback(self):
        """Point d'extension : supprimer l'indication de dépôt."""

    def _on_release(self, event):
        if not self._dragActive:
            self._dragStartPos = None
            return
        # Recalcul indispensable : la souris a pu bouger depuis le dernier Motion.
        item, part, column = self._hit_drop(event)
        valid = self.IsValidDropTarget(item)
        dragged = tuple(self._dragItems)
        self.StopDragging()
        if valid:
            self.OnDrop(item, list(dragged), part, column)

    def _on_escape(self, event):
        if self._dragActive:
            self.StopDragging()
            return "break"
        return None

    def _on_destroy(self, event):
        if event.widget is self:
            self._cancel_expand()

    def StartDragging(self):
        """Démarre le déplacement à partir de la sélection actuelle."""
        self._dragItems = list(self.selection())
        self._dragActive = bool(self._dragItems)
        if self._dragActive:
            self.SetCursorToDragging()

    def StopDragging(self):
        self._cancel_expand()
        self._ClearDropFeedback()
        self._dragActive = False
        self._dragStartPos = None
        self._dragItems = []
        self.ResetCursor()

    def selectDraggedItems(self):
        if self._dragItems:
            self.selection_set(self._dragItems)

    def OnKeyDuringDrag(self, event):
        if getattr(event, "keysym", "") == "Escape":
            return self._on_escape(event)
        return None

    def _set_cursor(self, cursor):
        try:
            if self._oldCursor is None:
                self._oldCursor = self.cget("cursor")
            self.configure(cursor=cursor)
        except tk.TclError:
            log.debug("Curseur indisponible : %s", cursor)

    def SetCursorToDragging(self):
        self._set_cursor("hand2")

    def SetCursorToLink(self):
        self._set_cursor("hand2")

    def SetCursorToHome(self):
        self._set_cursor("hand2")

    def SetCursorToDroppingImpossible(self):
        self._set_cursor("X_cursor")

    def ResetCursor(self):
        if self._oldCursor is not None:
            try:
                self.configure(cursor=self._oldCursor)
            except tk.TclError:
                pass
            self._oldCursor = None

    def _ResetHeaderCursor(self):
        self.ResetCursor()

    def OnDraggingOverHeader(self, event):
        """Extension optionnelle ; ttk.Treeview n'a pas d'API wx d'en-tête."""

    def OnDropOnHeader(self, event):
        """Extension optionnelle ; non appelée par défaut."""

    def _isPrereqOrDepColumn(self, column):
        if column < 0:
            return False
        if hasattr(self, "_getColumn"):
            try:
                col = self._getColumn(column)
                name = col.name() if callable(getattr(col, "name", None)) else getattr(col, "name", "")
                return name in ("prerequisites", "dependencies")
            except (AttributeError, IndexError, TypeError):
                pass
        return False


if __name__ == "__main__":
    class ExampleTree(TreeCtrlDragAndDropMixin, ttk.Treeview):
        def OnDrop(self, dropItem, dragItems, part, column):
            for item in dragItems:
                if dropItem and (item == dropItem or dropItem in self.GetItemChildren(item, True)):
                    continue
                parent = self.parent(dropItem) if part != 0 and dropItem else dropItem
                siblings = list(self.get_children(parent))
                index = siblings.index(dropItem) + (part == 1) if part != 0 and dropItem else "end"
                self.move(item, parent, index)

    root = tk.Tk()
    root.title("Démonstration du DnD interne")
    tree = ExampleTree(root, selectmode="extended")
    tree.pack(fill="both", expand=True)
    for i in range(4):
        parent = tree.insert("", "end", text=f"Groupe {i}", open=True)
        for j in range(3):
            tree.insert(parent, "end", text=f"Tâche {i}.{j}")
    root.mainloop()
