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

Info-bulles Tkinter pour Task Coach.

Cette version reprend les trois concepts de tooltip.py :
- ToolTipMixin : gestion du survol et du délai ;
- ToolTipBase : fenêtre flottante sans décoration ;
- SimpleToolTip : rendu de sections, texte et icônes Tkinter.

Les coordonnées utilisées par Tkinter sont des coordonnées écran lorsque la
fenêtre d'info-bulle est positionnée.

Exemple de création d’une info-bulle simple :
>>>tooltip = SimpleToolTip(parent)
>>>
>>>tooltip.SetData(
>>>    [
>>>        (
>>>            None,
>>>            [
>>>                "Première ligne",
>>>                "Deuxième ligne",
>>>            ],
>>>        ),
>>>    ]
>>>)
>>>
>>>tooltip.Show(300, 200)

Pour une classe utilisant ToolTipMixin, il faut implémenter :
def OnBeforeShowToolTip(self, x, y):
    tooltip = SimpleToolTip(self)
    tooltip.SetData(
        [
            (None, ["Texte dynamique"]),
        ]
    )
    return tooltip
"""

import logging
import textwrap
import tkinter as tk
from tkinter import font as tkfont

log = logging.getLogger(__name__)


class ToolTipBase(tk.Toplevel):
    """Fenêtre flottante de base pour une info-bulle Tkinter."""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.withdraw()
        self.overrideredirect(True)
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.configure(background="#000000")

    def Show(self, x, y, width=None, height=None, show=True):
        """Positionne et affiche la fenêtre, avec l'API historique wx adaptée."""
        self.update_idletasks()
        if width is None:
            width = self.winfo_reqwidth()
        if height is None:
            height = self.winfo_reqheight()
        self.geometry(f"{max(1, int(width))}x{max(1, int(height))}+{int(x)}+{int(y)}")
        if show:
            self.deiconify()
            self.lift()

    def Hide(self):
        """Masque la fenêtre sans la détruire."""
        self.withdraw()


class SimpleToolTip(ToolTipBase):
    """Info-bulle composée de sections (icône éventuelle, lignes de texte).

    ``data`` est une liste de couples ``(icon, lines)``. ``icon`` peut être
    une instance Tkinter PhotoImage/ImageTk ou ``None``. ``lines`` est une
    séquence de chaînes.
    """

    def __init__(self, parent=None, data=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.data = []
        self._canvas = tk.Canvas(
            self, highlightthickness=0, bd=0,
            background="#ffffe0", relief="flat"
        )
        self._canvas.pack(fill="both", expand=True)
        self._font = tkfont.nametofont("TkDefaultFont")
        self._text_colour = "#000000"
        self._background = "#ffffe0"
        self._border_colour = "#000000"
        if data is not None:
            self.SetData(data)

    def SetData(self, data):
        """
        Définit les données affichées dans l'info-bulle.

        Args :
            data (list) : Liste de tuples contenant des icônes et des lignes de texte.
        """
        self.data = self._wrapLongLines(data)
        self._redraw()

    def _wrapLongLines(self, data):
        """
        Ajuste les lignes longues pour qu'elles respectent une largeur maximale.

        Args :
            data (list) : Liste de données avec texte et icônes.

        Returns :
            list : Liste de données avec les lignes ajustées.
        """
        wrapped = []
        wrapper = textwrap.TextWrapper(width=78, break_long_words=False,
                                       break_on_hyphens=False)
        for icon, lines in data:
            result = []
            for line in lines:
                result.extend(wrapper.wrap(str(line)) or [""])
            wrapped.append((icon, result))
        return wrapped

    def _text_size(self, text):
        return self._font.measure(text), self._font.metrics("linespace")

    def _calculateLineSize(self, line):
        return self._text_size(line)

    def _calculateSectionSize(self, section_index):
        icon, lines = self.data[section_index]
        width = max((self._calculateLineSize(line)[0] for line in lines), default=0)
        height = sum(self._calculateLineSize(line)[1] + 1 for line in lines)
        if icon is not None:
            width += 24
        if 0 < section_index < len(self.data) - 1:
            height += 3
        return width, height

    def _calculateSize(self):
        width = height = 0
        for index in range(len(self.data)):
            section_width, section_height = self._calculateSectionSize(index)
            width = max(width, section_width)
            height += section_height
        return width + 8, height + 8

    def _redraw(self):
        self._canvas.delete("all")
        self._canvas.configure(background=self._background)
        width, height = self._calculateSize()
        self._canvas.configure(width=width, height=height)
        self.geometry(f"{width}x{height}")
        self._canvas.create_rectangle(0, 0, width - 1, height - 1,
                                      outline=self._border_colour)
        y = 4
        for index, (icon, lines) in enumerate(self.data):
            if index:
                self._canvas.create_line(4, y, width - 4, y,
                                         fill=self._text_colour)
                y += 3
            x = 4
            top = y
            if icon is not None:
                self._canvas.create_image(x + 8, y + 8, image=icon,
                                          anchor="center")
                x += 23
            for line in lines:
                self._canvas.create_text(x, y, text=line, anchor="nw",
                                         font=self._font,
                                         fill=self._text_colour)
                y += self._font.metrics("linespace") + 1
            if icon is not None:
                self._canvas.create_line(x - 2, top, x - 2, y,
                                         fill=self._text_colour)
        self.update_idletasks()

    def OnPaint(self, event=None):
        self._redraw()


class ToolTipMixin:
    """Ajoute une info-bulle dynamique à un widget Tkinter.

    La classe finale doit fournir ``OnBeforeShowToolTip(x, y)`` et retourner
    une instance de ToolTipBase, ou ``None``. Dans une classe multiple,
    appelez ``ToolTipMixin.__init__(self, ...)`` après l'initialisation du
    widget Tkinter.
    """

    def __init__(self, *args, **kwargs):
        delay = kwargs.pop("tooltipDelay", kwargs.pop("delay", 200))
        enabled = kwargs.pop("tooltipsEnabled", True)
        self._tooltip_enabled = bool(enabled)
        self._tooltip_delay = int(delay)
        self._tooltip_after_id = None
        self._tooltip = None
        self._tooltip_position = (0, 0)
        self._tooltip_bindings = []
        self._tooltip_bindings.append(self.bind("<Motion>", self._on_tooltip_motion, add="+"))
        self._tooltip_bindings.append(self.bind("<Leave>", self._on_tooltip_leave, add="+"))
        self._tooltip_bindings.append(self.bind("<ButtonPress>", self._on_tooltip_leave, add="+"))

    def SetToolTipsEnabled(self, enabled):
        """
        Activer ou désactiver les info-bulles pour ce contrôle.

        Args :
            enabled (bool) : `True` pour activer les info-bulles, `False` pour les désactiver.
        """
        self._tooltip_enabled = bool(enabled)
        if not self._tooltip_enabled:
            self._cancel_tooltip_timer()
            self.HideTip()

    def PopupMenu(self, menu):
        self.HideTip()
        return menu.post(self.winfo_rootx(), self.winfo_rooty())

    def ShowTip(self, x, y):
        """
        Affiche une info-bulle à la position spécifiée.

        L'info-bulle est ajustée pour s'assurer qu'elle reste visible dans
        la zone d'affichage de l'écran.

        Args :
            x (int) : Position X de l'info-bulle.
            y (int) : Position Y de l'info-bulle.
        """
        if self._tooltip is None:
            return
        self.update_idletasks()
        width = self._tooltip.winfo_reqwidth()
        height = self._tooltip.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if x + width > screen_width:
            x = max(5, screen_width - width - 5)
        if y + height > screen_height:
            y = max(5, screen_height - height - 5)
        self._tooltip.Show(x, y, width, height, True)

    def DoShowTip(self, x, y, tip):
        self.HideTip()
        self._tooltip = tip
        self.ShowTip(x, y)

    def HideTip(self):
        if self._tooltip is not None:
            self._tooltip.Hide()
            self._tooltip = None

    def OnBeforeShowToolTip(self, x, y):
        """Doit renvoyer une instance de tk.Toplevel qui sera affichée sous la forme
        d'info-bulle, ou Aucun.

        Doit être redéfinie pour fournir dynamiquement une info-bulle.

        Cette méthode est appelée juste avant l'affichage de l'info-bulle.
        Retournez une instance de `tk.Toplevel` représentant l'info-bulle, ou `None`
        si aucune info-bulle ne doit être affichée.

        Args :
            x (int) : Position X de la souris.
            y (int) : Position Y de la souris.

        Returns :
            tk.Toplevel | None : Contenu de l'info-bulle ou `None`.
        """
        raise NotImplementedError

    def _cancel_tooltip_timer(self):
        if self._tooltip_after_id is not None:
            try:
                self.after_cancel(self._tooltip_after_id)
            except tk.TclError:
                pass
            self._tooltip_after_id = None

    def _on_tooltip_motion(self, event):
        self._cancel_tooltip_timer()
        self.HideTip()
        if not self._tooltip_enabled:
            return
        self._tooltip_position = (event.x_root + 20, event.y_root + 10)
        self._tooltip_after_id = self.after(self._tooltip_delay,
                                            self._on_tooltip_timer)

    def _on_tooltip_leave(self, event=None):
        self._cancel_tooltip_timer()
        self.HideTip()

    def _on_tooltip_timer(self):
        self._tooltip_after_id = None
        if not self._tooltip_enabled:
            return
        x, y = self._tooltip_position
        tip = self.OnBeforeShowToolTip(x, y)
        if tip is not None:
            self.DoShowTip(x, y, tip)

    def destroy(self):
        """Désinstalle les liaisons et détruit l'info-bulle."""
        self._cancel_scheduled_show()
        self.hide_tooltip()

        self.widget.unbind("<Enter>", self._enter_binding)
        self.widget.unbind("<Leave>", self._leave_binding)
        self.widget.unbind("<Motion>", self._motion_binding)
        self.widget.unbind("<ButtonPress>", self._button_binding)

# # Exemple d'utilisation
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Exemple d'info-bulle Tkinter")
#
#     # Crée un bouton avec une info-bulle simple
#     button1 = tk.Button(root, text="Passez la souris ici")
#     button1.pack(pady=20, padx=20)
#     # tooltip1 = SimpleToolTip(button1, (None, "Ceci est une info-bulle pour le bouton 1."))
#     tooltip1 = SimpleToolTip(button1)
#     tooltip1.SetData([(None, ["Ceci est une info-bulle pour le bouton 1."])])
#     tooltip1.Show(300, 200)
#
#     # Crée un autre bouton avec une info-bulle plus longue
#     long_text = "Ceci est une info-bulle plus longue qui devrait s'ajuster si elle est trop large."
#     button2 = tk.Button(root, text="Un autre bouton")
#     button2.pack(pady=20, padx=20)
#     # tooltip2 = SimpleToolTip(button2, (None, textwrap.fill(long_text, width=40)))
#     tooltip2 = SimpleToolTip(button2)
#     tooltip2.SetData([(None, [textwrap.fill(long_text, width=40)])])
#     # tooltip2.Show(300, 200)
#
#     root.mainloop()
