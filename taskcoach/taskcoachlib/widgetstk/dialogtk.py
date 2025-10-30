"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# Principes appliqués :
#
# Dialog → basé sur tk.Toplevel avec grab_set() et transient() pour simuler la modale.
#
# NotebookDialog → utilise votre Notebook (tkinter/ttk) pour gérer les pages.
#
# Boutons standard (OK, Annuler, Fermer) → via ttk.Button + Frame en bas.
#
# HtmlWindowThatUsesWebBrowserForExternalLinks → remplacé par tk.Text + gestion de clic (les liens _blank ouvrent dans le navigateur).
#
# AttachmentSelector → utilisation de tkinter.filedialog.askopenfilename.

# Points clés :
#
# Boutons dynamiques : basés sur button_types pour imiter wx.StdDialogButtonSizer.
#
# NotebookDialog : se base sur votre Notebook Tkinter.
#
# HTMLDialog : utilise tk.Text avec liens cliquables → ouvre avec webbrowser.
#
# AttachmentSelector : basé sur filedialog.askopenfilename().
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser

from taskcoachlib.i18n import _
from taskcoachlib.widgetstk.notebooktk import Notebook  # Utilise votre version Tkinter


class Dialog(tk.Toplevel):
    """
    Classe de base pour les boîtes de dialogue avec Tkinter.

    Gère :
    - Fenêtre modale (grab_set, transient)
    - Boutons standards OK / Annuler
    - Contenu central via createInterior() et fillInterior()
    """

    def __init__(self, parent, title, button_types=("ok", "cancel"), *args, **kwargs):
        """
        Initialise la boîte de dialogue.

        :param parent: Fenêtre parente
        :param title: Titre de la fenêtre
        :param button_types: Liste de boutons ('ok', 'cancel', 'close')
        """
        # Ceci est l'appel crucial qui crée le widget Tkinter
        super().__init__(parent, *args, **kwargs)  # Appelle tk.Toplevel.__init__(parent, ...), Crée la fenêtre
        self.title(title)  # Définit le titre
        self.transient(parent)  # Assure la modale
        self.grab_set()  # Empêche d'interagir avec la fenêtre parente
        self.resizable(True, True)  # Autorise le redimensionnement

        self._button_types = button_types  # Stocke les types de boutons
        self._interior_frame = None  # Zone centrale
        self._buttons_frame = None  # Zone des boutons

        # Crée la zone principale
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._notebook = None
        # Création de la zone centrale
        self._interior_frame = self.createInterior(container)
        self._interior_frame.pack(fill="both", expand=True)

        # Remplit la zone centrale
        self.fillInterior()

        # Création des boutons
        self._buttons_frame = self.createButtons(container)
        self._buttons_frame.pack(fill="x", pady=10)

        # Centrer la fenêtre
        self.center_on_parent(parent)

        # Gestion de la fermeture
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def center_on_parent(self, parent):
        """Centre la boîte de dialogue sur la fenêtre parente."""
        self.update_idletasks()
        if parent:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        else:
            px = py = 100
            pw = ph = 300
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = px + (pw // 2) - (w // 2)
        y = py + (ph // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def createInterior(self, parent):
        """
        Crée la zone intérieure (à surcharger).
        Retourne un Frame ou un widget parent.
        """
        return ttk.Frame(parent)

    def fillInterior(self):
        """Remplit la zone intérieure (à surcharger)."""
        pass

    def createButtons(self, parent):
        """
        Crée les boutons en bas de la boîte de dialogue.
        """
        frame = ttk.Frame(parent)
        if "ok" in self._button_types:
            ok_btn = ttk.Button(frame, text=_("OK"), command=self.ok)
            ok_btn.pack(side="right", padx=5)
        if "cancel" in self._button_types:
            cancel_btn = ttk.Button(frame, text=_("Cancel"), command=self.cancel)
            cancel_btn.pack(side="right", padx=5)
        if "close" in self._button_types:
            close_btn = ttk.Button(frame, text=_("Close"), command=self.cancel)
            close_btn.pack(side="right", padx=5)
        return frame

    def ok(self, event=None):
        """Ferme la boîte de dialogue (OK)."""
        self.destroy()

    def cancel(self, event=None):
        """Ferme la boîte de dialogue (Annuler)."""
        self.destroy()

    def disableOK(self):
        """Désactive le bouton OK."""
        for child in self._buttons_frame.winfo_children():
            if child.cget("text") == _("OK"):
                child.configure(state="disabled")

    def enableOK(self):
        """Active le bouton OK."""
        for child in self._buttons_frame.winfo_children():
            if child.cget("text") == _("OK"):
                child.configure(state="normal")


class NotebookDialog(Dialog):
    """
    Boîte de dialogue avec un Notebook (onglets).
    """

    def createInterior(self, parent):
        """Crée le Notebook comme contenu principal."""
        self._notebook = Notebook(parent)
        return self._notebook

    def fillInterior(self):
        """Ajoute les pages au Notebook."""
        self.addPages()

    def addPages(self):
        """À surcharger pour définir les pages."""
        raise NotImplementedError

    def ok(self, *args, **kwargs):
        """Valide les pages avant de fermer."""
        for page_id in self._notebook.tabs():
            page_widget = self._notebook.nametowidget(page_id)
            if hasattr(page_widget, "ok"):
                page_widget.ok(*args, **kwargs)
        super().ok()


class HtmlWindowThatUsesWebBrowserForExternalLinks(tk.Text):
    """
    Widget affichant du HTML simplifié avec gestion des liens externes.
    """

    def __init__(self, parent, html_text="", *args, **kwargs):
        super().__init__(parent, wrap="word", *args, **kwargs)
        self.insert("1.0", html_text)
        self.config(state="disabled")  # Lecture seule
        self.tag_configure("link", foreground="blue", underline=True)
        self.bind("<Button-1>", self._on_click)

    def _on_click(self, event):
        """Ouvre le lien dans le navigateur si clic sur 'link'."""
        index = self.index(f"@{event.x},{event.y}")
        tags = self.tag_names(index)
        if "link" in tags:
            url = self.get(f"{index} wordstart", f"{index} wordend")
            webbrowser.open(url)


class HTMLDialog(Dialog):
    """
    Boîte de dialogue affichant du HTML (simplifié).
    """

    def __init__(self, parent, title, html_text, *args, **kwargs):
        self._html_text = html_text
        super().__init__(parent, title, button_types=("close",), *args, **kwargs)

    def createInterior(self, parent):
        """Crée la zone HTML."""
        return HtmlWindowThatUsesWebBrowserForExternalLinks(parent, self._html_text)


def AttachmentSelector(**kwargs):
    """
    Sélecteur de fichier pour pièces jointes.
    """
    options = {
        "title": _("Add attachment"),
        "initialdir": os.getcwd(),
        "filetypes": [(_("All files"), "*.*")],
    }
    options.update(kwargs)
    return filedialog.askopenfilename(**options)
