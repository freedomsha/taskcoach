# -*- coding: utf-8 -*-
"""Démonstrateur du gestionnaire AUI ttk et d'un panneau flottant."""
import tkinter as tk
from tkinter import ttk
try:
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkframemanager_auimanager import AuiManager
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkauibook import AuiNotebook
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.aui_tk_constants import AUI_DOCK_LEFT, AUI_DOCK_RIGHT
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.tkframemanager_elements import AuiPaneInfo
except ImportError:
    from ttkframemanager_auimanager import AuiManager
    from ttkauibook import AuiNotebook
    from aui_tk_constants import AUI_DOCK_LEFT, AUI_DOCK_RIGHT
    from tkframemanager_elements import AuiPaneInfo


def main():
    root=tk.Tk(); root.title("Démonstrateur AUI ttk"); root.geometry("900x560")
    manager=AuiManager(root)
    center=ttk.Frame(root, padding=16); ttk.Label(center,text="Zone centrale",font=("TkDefaultFont",16,"bold")).pack(anchor="w")
    ttk.Label(center,text="Les panneaux latéraux utilisent ttk.Frame et le notebook utilise ttk.Notebook.").pack(anchor="w",pady=8)
    manager.AddPane(center,AuiPaneInfo().Name("center").Caption("Centre").CenterPane())
    left=ttk.Frame(root,padding=10); ttk.Label(left,text="Panneau gauche").pack(anchor="w"); ttk.Button(left,text="Flotter",command=lambda:manager.FloatPane(manager.GetPane(left))).pack(anchor="w",pady=8)
    manager.AddPane(left,AuiPaneInfo().Name("left").Caption("Gauche").Left().BestSize(190,0))
    right=ttk.Frame(root,padding=10); ttk.Label(right,text="Panneau droit").pack(anchor="w"); ttk.Button(right,text="Flotter",command=lambda:manager.FloatPane(manager.GetPane(right))).pack(anchor="w",pady=8)
    manager.AddPane(right,AuiPaneInfo().Name("right").Caption("Droite").Right().BestSize(190,0))
    root.mainloop()
if __name__ == "__main__": main()
