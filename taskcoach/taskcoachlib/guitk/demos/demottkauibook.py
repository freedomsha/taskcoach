# -*- coding: utf-8 -*-
"""Démonstrateur minimal de ttkauibook.

Lancer depuis le dépôt avec :
    python -m taskcoachlib.thirdparty.tk3rdparty.aui_ttk.demottkauibook
"""
import tkinter as tk
from tkinter import ttk

try:
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkauibook import AuiNotebook
except ImportError:
    # from taskcoachlib.thirdparty.tk3rdparty.aui_ttk import ttkauibook
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkauibook import AuiNotebook
# except ImportError:
#     from .ttkauibook import AuiNotebook
#     from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkauibook import AuiNotebook


def make_page(parent, title, colour, text):
    page = ttk.Frame(parent, padding=12)
    page.configure(style=f"{title}.TFrame")
    ttk.Label(page, text=text).pack(anchor="w", pady=(0, 12))
    ttk.Button(page, text=f"Action {title}", command=lambda: print(f"Action {title}")).pack(anchor="w")
    return page


def main():
    root = tk.Tk()
    root.title("Démonstrateur ttk AUI Notebook")
    root.geometry("760x460")

    style = ttk.Style(root)
    for name, colour in (("Accueil", "#eaf3ff"), ("Tâches", "#eef8ee"), ("Propriétés", "#fff5e6")):
        style.configure(f"{name}.TFrame", background=colour)

    header = ttk.Frame(root, padding=(12, 10))
    header.pack(fill="x")
    ttk.Label(header, text="AUI basée sur ttk", font=("TkDefaultFont", 14, "bold")).pack(side="left")
    ttk.Label(header, text="  ttk.Notebook, sélection, renommage et navigation clavier").pack(side="left")

    notebook = AuiNotebook(root)
    notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    notebook.AddPage(make_page(notebook._notebook, "Accueil", "#eaf3ff", "Première page du démonstrateur."), "Accueil", select=True)
    notebook.AddPage(make_page(notebook._notebook, "Tâches", "#eef8ee", "Cette page représente une liste de tâches."), "Tâches")
    notebook.AddPage(make_page(notebook._notebook, "Propriétés", "#fff5e6", "Cette page représente les propriétés de l'élément sélectionné."), "Propriétés")

    controls = ttk.Frame(root, padding=(12, 0, 12, 12))
    controls.pack(fill="x")
    ttk.Button(controls, text="Page précédente", command=lambda: notebook.AdvanceSelection(False)).pack(side="left")
    ttk.Button(controls, text="Page suivante", command=lambda: notebook.AdvanceSelection(True)).pack(side="left", padx=6)
    ttk.Button(controls, text="Masquer la page active", command=lambda: notebook.HidePage(notebook.GetSelection(), True)).pack(side="right")

    root.bind("<Control-Left>", lambda event: notebook.AdvanceSelection(False))
    root.bind("<Control-Right>", lambda event: notebook.AdvanceSelection(True))
    root.mainloop()


if __name__ == "__main__":
    main()
