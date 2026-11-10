# -*- coding: utf-8 -*-
"""Fenêtre flottante ttk pour les panneaux AUI.

Le widget original est conservé comme référence de comportement. Cette
version détache réellement le contenu du panneau de son parent, le place dans
un Toplevel et le réintègre dans le gestionnaire lors du réamarrage.
"""
import tkinter as tk
from tkinter import ttk


class TtkFloatingFrame(tk.Toplevel):
    """Fenêtre de premier niveau accueillant temporairement un panneau AUI.

    Elle héberge le widget associé au panneau, mémorise sa géométrie et
    délègue au gestionnaire AUI sa réintégration dans la disposition principale.
    """

    def __init__(self, parent, manager, pane):
        """Initialise la fenêtre flottante et y place le contenu du panneau.

        Args:
            parent: Widget Tkinter servant de parent à la fenêtre.
            manager: Gestionnaire AUI chargé du réamarrage des panneaux.
            pane: Descripteur du panneau à afficher dans cette fenêtre.
        """
        super().__init__(parent)
        self.manager = manager
        self.pane = pane
        self._content = None
        self.title(getattr(pane, "caption", "") or getattr(pane, "name", "Panneau"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_configure, add="+")
        self._attach_content()

    def _attach_content(self):
        """Déplace le widget du panneau dans la fenêtre flottante.

        Les gestionnaires de géométrie précédemment utilisés sont désactivés
        avant de tenter d'afficher le widget dans cette fenêtre. Tkinter ne
        permettant pas de modifier directement le parent Tcl d'un widget
        existant, l'échec de la tentative ``configure(in_=...)`` est toléré.
        """
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
            # Le paramètre ``in_`` ne change pas le parent Tcl réel du widget.
            # Tk ne permet pas de reparentage direct après la création :
            # le gestionnaire peut devoir utiliser une enveloppe intermédiaire.
            pass
        content.pack(fill="both", expand=True)

    def _on_configure(self, event=None):
        """Enregistre la taille et la position actuelles de la fenêtre.

        L'événement ``<Configure>`` est notamment émis lorsque l'utilisateur
        déplace ou redimensionne la fenêtre. Les informations sont conservées
        sur le panneau pour permettre au gestionnaire de les réutiliser.
        """
        try:
            self.pane.floating_size = (self.winfo_width(), self.winfo_height())
            self.pane.floating_pos = (self.winfo_x(), self.winfo_y())
        except tk.TclError:
            # Tk peut encore émettre un événement pendant la destruction
            # de la fenêtre ; les informations ne sont alors plus accessibles.
            pass

    def _on_close(self):
        """Intercepte la fermeture native pour réamarrer le panneau.

        Le protocole ``WM_DELETE_WINDOW`` évite de détruire directement la
        fenêtre : le gestionnaire AUI prend en charge la réintégration.
        """
        self.manager.DockPane(self.pane)

    def Show(self, show=True):
        """Affiche ou masque la fenêtre sans la détruire.

        Args:
            show: Vrai pour afficher la fenêtre, faux pour la masquer.
        """
        if show: self.deiconify()
        else: self.withdraw()

    def Dock(self):
        """Demande au gestionnaire AUI de réintégrer le panneau."""
        self.manager.DockPane(self.pane)


AuiFloatingFrame = TtkFloatingFrame
