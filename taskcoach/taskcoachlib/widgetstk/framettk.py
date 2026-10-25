# -*- coding: utf-8 -*-
"""Cadre principal utilisant l'implémentation AUI basée sur ttk et Tkinter.

Ce module reprend l'interface de ``frame.py`` tout en utilisant les classes
AUI Tkinter du paquet ``taskcoachlib.thirdparty.tk3rdparty.aui_ttk``.
"""

import logging
import tkinter as tk

from taskcoachlib.thirdparty.tk3rdparty.aui_ttk import aui_tk_constants as aui
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.tkframemanager_elements import (
    AuiPaneInfo,
)
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkframemanager_auimanager import (
    AuiManager,
)

log = logging.getLogger(__name__)


class AuiManagedFrameWithDynamicCenterPane:
    """Fenêtre Tkinter équipée du gestionnaire AUI ttk.

    Le premier panneau ajouté est placé au centre. Les panneaux suivants sont
    placés à droite par défaut, comme dans l'ancienne implémentation wxPython.
    La gestion effective de la grille, du flottement et du réamarrage est
    déléguée à :class:`AuiManager`.
    """

    def __init__(self, master=None, title="Task Coach", root=None, **kwargs):
        # ``root`` est accepté pour faciliter la compatibilité avec du code
        # Tkinter existant qui utilise ce nom d'argument.
        if master is None:
            master = root
        self.root = master if master is not None else tk.Tk()
        self.root.title(title)
        for option, value in kwargs.items():
            try:
                self.root.configure(**{option: value})
            except tk.TclError:
                log.debug("Option Tk ignorée: %s", option, exc_info=True)

        self.manager = AuiManager(self.root)
        self._center_pane = None
        self._panes_by_name = {}
        self.bindEvents()

    def bindEvents(self):
        """Réserve le point d'extension des événements AUI.

        La version actuelle de ``AuiManager`` réalise les changements d'état
        directement par ``Update``. Elle ne fournit pas encore les événements
        wx ``EVT_AUI_PANE_CLOSE`` et ``EVT_AUI_PANE_FLOATING``.
        """
        return None

    def _pane_info(self, caption, name, floating=False):
        pane = (
            AuiPaneInfo()
            .Name(name)
            .Caption(caption)
            .DefaultPane()
            .Floatable(True)
            .Movable(True)
            .CloseButton(True)
            .MaximizeButton(True)
            .DestroyOnClose(True)
            .CaptionVisible(True)
            .BestSize(200, 200)
            .FloatingSize(300, 200)
        )
        if floating:
            pane.Float()
        return pane

    def addPane(self, window, caption, name, floating=False):
        """Ajoute ``window`` comme panneau AUI.

        Args:
            window: Widget Tkinter à gérer.
            caption: Titre affiché pour le panneau flottant.
            name: Identifiant stable du panneau.
            floating: Affiche initialement le panneau dans un ``Toplevel``.
        Returns:
            L'objet ``AuiPaneInfo`` créé.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("name doit être une chaîne non vide")
        if name in self._panes_by_name:
            raise ValueError("Un panneau porte déjà le nom {!r}".format(name))
        if not isinstance(window, tk.Misc):
            raise TypeError("window doit être un widget Tkinter")

        pane = self._pane_info(caption, name, floating=floating)
        if self._center_pane is None and not floating:
            pane.CenterPane()
            self._center_pane = pane
        elif not floating:
            pane.Right()
            pane.Position(len(self.dockedPanes()))
        else:
            # Une position écran déterministe évite un flottement placé hors
            # écran lorsque le widget n'a pas encore été affiché.
            try:
                self.root.update_idletasks()
                x = self.root.winfo_rootx() + 30
                y = self.root.winfo_rooty() + 30
            except tk.TclError:
                x, y = 30, 30
            pane.FloatingPosition(x, y)

        self.manager.AddPane(window, pane)
        self._panes_by_name[name] = pane
        self.manager.Update()
        return pane

    def _resolve_pane(self, pane_or_window_or_name):
        if isinstance(pane_or_window_or_name, AuiPaneInfo):
            return pane_or_window_or_name
        return self.manager.GetPane(pane_or_window_or_name)

    def setPaneTitle(self, window, title):
        """Modifie le titre du panneau identifié par son widget ou son nom."""
        pane = self._resolve_pane(window)
        if not pane.IsOk():
            raise KeyError("Panneau introuvable: {!r}".format(window))
        pane.Caption(title)
        if pane.frame is not None and pane.frame.winfo_exists():
            pane.frame.title(title)
        self.manager.Update()

    def dockedPanes(self):
        """Retourne les panneaux actuellement amarrés."""
        return [
            pane
            for pane in self.manager.GetAllPanes()
            if pane.IsOk()
            and pane.IsDocked()
            and not pane.IsToolbar()
            and not pane.IsNotebookPage()
            and pane.IsShown()
        ]

    def float(self, window):
        """Détache le panneau identifié par son widget, son nom ou son info."""
        pane = self._resolve_pane(window)
        if not pane.IsOk():
            raise KeyError("Panneau introuvable: {!r}".format(window))
        self.manager.FloatPane(pane)

    def dock(self, window):
        """Réamarrer le panneau identifié par son widget, son nom ou son info."""
        pane = self._resolve_pane(window)
        if not pane.IsOk():
            raise KeyError("Panneau introuvable: {!r}".format(window))
        self.manager.DockPane(pane)

    @staticmethod
    def isCenterPane(pane):
        """Indique si un objet ``AuiPaneInfo`` est le panneau central."""
        return pane.dock_direction in {
            getattr(aui, "AUI_DOCK_CENTER", 4),
            getattr(aui, "AUI_DOCK_CENTRE", 4),
        }

    def Show(self):
        self.root.deiconify()

    def Hide(self):
        self.root.withdraw()

    def start_loop(self):
        self.root.mainloop()

    def destroy(self):
        self.manager.UnInit()
        self.root.destroy()


# Alias conservant le nom introduit par la conversion intermédiaire.
TtkManagedFrame = AuiManagedFrameWithDynamicCenterPane

__all__ = ["AuiManagedFrameWithDynamicCenterPane", "TtkManagedFrame"]
