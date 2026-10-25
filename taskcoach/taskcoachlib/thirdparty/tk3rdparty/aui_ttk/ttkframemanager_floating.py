# -*- coding: utf-8 -*-
"""Fenêtre flottante ttk pour les panneaux AUI.

Le widget original est conservé comme référence de comportement. Cette
version détache réellement le contenu du panneau de son parent, le place dans
un Toplevel et le réintègre dans le gestionnaire lors du réamarrage.
"""
import tkinter as tk
from tkinter import ttk


class TtkFloatingFrame(tk.Toplevel):
    def __init__(self, parent, manager, pane):
        super().__init__(parent)
        self.manager = manager
        self.pane = pane
        self._content = None
        self.title(getattr(pane, "caption", "") or getattr(pane, "name", "Panneau"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_configure, add="+")
        self._attach_content()

    def _attach_content(self):
        content = getattr(self.pane, "window", None)
        if content is None or not content.winfo_exists():
            return
        self._content = content
        for method in ("pack_forget", "grid_forget", "place_forget"):
            try: getattr(content, method)()
            except (AttributeError, tk.TclError): pass
        try:
            content.configure(in_=self)
        except tk.TclError:
            # Tk ne permet pas de changer le parent Tcl d'un widget existant.
            # Le gestionnaire peut alors utiliser une enveloppe de reparentage.
            pass
        content.pack(fill="both", expand=True)

    def _on_configure(self, event=None):
        try:
            self.pane.floating_size = (self.winfo_width(), self.winfo_height())
            self.pane.floating_pos = (self.winfo_x(), self.winfo_y())
        except tk.TclError:
            pass

    def _on_close(self):
        self.manager.DockPane(self.pane)

    def Show(self, show=True):
        if show: self.deiconify()
        else: self.withdraw()

    def Dock(self):
        self.manager.DockPane(self.pane)


AuiFloatingFrame = TtkFloatingFrame
