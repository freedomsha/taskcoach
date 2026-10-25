# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
try:
    from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkframemanager_auimanager import TtkPaneLayout, TtkPanePlacement
except ImportError:
    from ttkframemanager_auimanager import TtkPaneLayout, TtkPanePlacement

def main():
    root=tk.Tk(); root.title("Ttk PaneLayout"); root.geometry("900x560")
    layout=TtkPaneLayout(root)
    panels=[("Gauche","gauche",0), ("Centre","centre","last"), ("Droite","droite","last"), ("Haut","au-dessus","last")]
    for title,pos,rank in panels:
        frame=ttk.Frame(root,padding=12); ttk.Label(frame,text=title,font=("TkDefaultFont",14,"bold")).pack(anchor="w")
        ttk.Label(frame,text=f"position={pos}, rank={rank}").pack(anchor="w")
        layout.add(frame,TtkPanePlacement("global",pos,rank))
    root.mainloop()
if __name__=="__main__": main()
