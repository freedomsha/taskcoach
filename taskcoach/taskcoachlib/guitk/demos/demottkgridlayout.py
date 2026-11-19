# -*- coding: utf-8 -*-
"""Démonstrateur du gestionnaire AUI ttk basé sur tkinter.grid().

Lancer depuis la racine du dépôt :
    python -m taskcoachlib.thirdparty.tk3rdparty.aui_ttk.demottkgridlayout
"""
import tkinter as tk
from tkinter import ttk

# try:
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkframemanager_auimanager import AuiManager
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.tkframemanager_elements import AuiPaneInfo
# except ImportError:
#     from ttkframemanager_auimanager import AuiManager
#     from tkframemanager_elements import AuiPaneInfo


class Demo:
    def __init__(self, root):
        self.root = root
        self.manager = AuiManager(root)
        self.status = tk.StringVar(value="Prêt")
        self._build()

    def _panel(self, title, colour):
        frame = ttk.LabelFrame(self.root, text=title, padding=10)
        frame.configure(style=f"{title}.TLabelframe")
        ttk.Label(frame, text=f"Panneau {title}").pack(anchor="w")
        return frame

    def _build(self):
        style = ttk.Style(self.root)
        for title, colour in (("Gauche", "#e8f1ff"), ("Centre", "#ffffff"),
                              ("Droite", "#fff1e6"), ("Haut", "#eaf7ea"),
                              ("Bas", "#f4eafa")):
            style.configure(f"{title}.TLabelframe", background=colour)

        self.toolbar = ttk.Frame(self.root, padding=6)
        self.toolbar.pack(fill="x")
        ttk.Button(self.toolbar, text="Ajouter panneau", command=self.add_panel).pack(side="left")
        ttk.Button(self.toolbar, text="Retirer panneau actif", command=self.remove_active).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Flotter actif", command=self.float_active).pack(side="left")
        ttk.Button(self.toolbar, text="Réamarrer actif", command=self.dock_active).pack(side="left", padx=5)
        ttk.Label(self.toolbar, textvariable=self.status).pack(side="right")

        self.active = None
        self.counter = 0
        self.panels = {}
        self._add("Centre", "centre", 0)
        self._add("Gauche", "gauche", 0)
        self._add("Droite", "droite", 0)
        self._add("Haut", "au-dessus", 0)
        self._add("Bas", "en-dessous", 0)

    def _add(self, title, position, rank="last"):
        panel = self._panel(title, "")
        pane = AuiPaneInfo().Name(title.lower()).Caption(title)
        methods = {"gauche": pane.Left, "droite": pane.Right,
                   "au-dessus": pane.Top, "en-dessous": pane.Bottom,
                   "centre": pane.Center}
        methods[position]()
        pane.dock_pos = rank if isinstance(rank, int) else 0
        pane._demo_position = position
        self.manager.AddPane(panel, pane)
        self.panels[title.lower()] = (panel, pane)
        panel.bind("<Button-1>", lambda event, value=(panel, pane): self.select(value), add="+")
        self.select((panel, pane))
        return panel

    def select(self, value):
        self.active = value
        self.status.set(f"Actif : {value[1].caption}")

    def add_panel(self):
        self.counter += 1
        name = f"outil_{self.counter}"
        panel = self._add(name, "gauche", self.counter)
        ttk.Label(panel, text="Panneau ajouté dynamiquement").pack(anchor="w")

    def remove_active(self):
        if self.active is None: return
        panel, pane = self.active
        self.manager.ClosePane(pane)
        self.panels.pop(pane.name, None)
        self.active = None
        self.status.set("Panneau retiré")

    def float_active(self):
        if self.active is None: return
        panel, pane = self.active
        self.manager.FloatPane(pane)
        self.status.set(f"Flottant : {pane.caption}")

    def dock_active(self):
        if self.active is None: return
        panel, pane = self.active
        self.manager.DockPane(pane)
        self.status.set(f"Amarré : {pane.caption}")


def main():
    root = tk.Tk()
    root.title("Démonstrateur AUI ttk avec grid")
    root.geometry("960x620")
    Demo(root)
    root.mainloop()


if __name__ == "__main__":
    main()
