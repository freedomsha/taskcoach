# -*- coding: utf-8 -*-
"""Fenêtre flottante ttk pour les panneaux AUI.

Héberge les panneaux qui fournissent une fabrique de reconstruction.

Le widget original est conservé comme référence de comportement. Cette
version détache réellement le contenu du panneau de son parent, le place dans
un Toplevel et le réintègre dans le gestionnaire lors du réamarrage.
"""
import tkinter as tk


class ManagedFrame(tk.Wm):
    """Interface de fenêtre pour un tk.Frame promu par le gestionnaire Tk.

    Le widget reste accessible par son chemin Tcl. Les opérations wm (dont
    title) sont distinctes des méthodes métier de même nom du visualiseur.
    """

    def __init__(self, widget, manager, pane):
        self.widget = widget
        self.tk = widget.tk
        self._w = widget._w
        self.wm_manage(widget)
        self._close = widget.register(lambda: manager.DockPane(pane))
        self.wm_protocol("WM_DELETE_WINDOW", self._close)

        def remember_geometry(event):
            if event.widget is widget and pane.frame is self:
                pane.floating_size = (event.width, event.height)
                pane.floating_pos = (widget.winfo_x(), widget.winfo_y())
                self.last_geometry = (pane.floating_size, pane.floating_pos)

        self._configure = widget.bind("<Configure>", remember_geometry, add="+")

    def __str__(self):
        return str(self.widget)

    def __getattr__(self, name):
        return getattr(self.widget, name)

    def dock(self):
        """Rend le cadre à son parent de grille et libère les rappels Tk."""
        self.widget.unbind("<Configure>", self._configure)
        self.wm_protocol("WM_DELETE_WINDOW", "")
        self.widget.deletecommand(self._close)
        self.wm_forget(self.widget)


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
        try:
            self._attach_content()
        except Exception:
            self.destroy()
            raise

    def _attach_content(self):
        """Confie la reconstruction et la restauration de l'état au gestionnaire.

        Reconstruit la vue du panneau comme enfant de ce Toplevel.

        Déplace le widget du panneau dans la fenêtre flottante.

        Les gestionnaires de géométrie précédemment utilisés sont désactivés
        avant de tenter d'afficher le widget dans cette fenêtre. Tkinter ne
        permettant pas de modifier directement le parent Tcl d'un widget
        existant, l'échec de la tentative ``configure(in_=...)`` est toléré.
        """
        if self.pane.window is not None:
            self._content = self.manager._rebuild_pane_window(self.pane, self)
            self._content.pack(fill="both", expand=True)

    def _on_configure(self, event=None):
        """Enregistre la taille et la position actuelles de la fenêtre.

        L'événement ``<Configure>`` est notamment émis lorsque l'utilisateur
        déplace ou redimensionne la fenêtre. Les informations sont conservées
        sur le panneau pour permettre au gestionnaire de les réutiliser.
        """
        if event is not None and event.widget is not self:
            return
        try:
            self.pane.floating_size = (self.winfo_width(), self.winfo_height())
            self.pane.floating_pos = (self.winfo_x(), self.winfo_y())
            self.last_geometry = (self.pane.floating_size, self.pane.floating_pos)
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
