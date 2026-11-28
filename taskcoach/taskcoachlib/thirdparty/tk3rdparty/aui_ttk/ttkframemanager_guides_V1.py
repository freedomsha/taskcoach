# -*- coding: utf-8 -*-
"""Guides d'ancrage Tk pour la disposition AUI actuelle à cinq groupes.

Les guides sont des Toplevel sans décoration, dessinés avec Canvas.
Leur hit-test utilise les coordonnées écran, pas le widget sous la souris.
Les placements relatifs suivent l'orientation réelle du groupe cible.
"""
from dataclasses import dataclass
import tkinter as tk

from .aui_tk_constants import (
    AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_TOP,
    AUI_DOCK_BOTTOM, AUI_DOCK_CENTER,
)


@dataclass(frozen=True)
class DockTarget:
    """Destination : groupe global, ou insertion avant/après un panneau."""
    direction: int
    anchor: object = None
    before: bool = False


def _rect(widget):
    """Retourne les limites écran d'un widget visible, sinon None."""
    if widget is None or not widget.winfo_exists() or not widget.winfo_ismapped():
        return None
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    w, h = widget.winfo_width(), widget.winfo_height()
    return (x, y, x + w, y + h) if min(w, h) > 1 else None


def _contains(rect, x, y):
    return rect is not None and rect[0] <= x < rect[2] and rect[1] <= y < rect[3]


def _intersection(a, b):
    if a is None or b is None:
        return None
    r = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return r if r[0] < r[2] and r[1] < r[3] else None


class _GuideWindow:
    """Une flèche d'ancrage, indépendante de la géométrie des panneaux."""
    SIZE = 32
    ARROWS = {
        'left': (7, 16, 24, 16), 'right': (25, 16, 8, 16),
        'top': (16, 7, 16, 24), 'bottom': (16, 25, 16, 8),
    }

    def __init__(self, owner):
        self.window = tk.Toplevel(owner)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(takefocus=False)
        try:
            self.window.attributes('-topmost', True)
        except tk.TclError:
            pass
        self.canvas = tk.Canvas(self.window, width=self.SIZE, height=self.SIZE,
                                highlightthickness=0, takefocus=False)
        self.canvas.pack(fill='both', expand=True)
        self.rect = None
        self.target = None
        self._appearance = None

    def show(self, rect, target, arrow, active):
        """Déplace et redessine le guide uniquement si nécessaire."""
        if self.rect != rect:
            x, y = rect[:2]
            self.window.geometry(f'{self.SIZE}x{self.SIZE}+{x}+{y}')
        self.rect, self.target = rect, target
        appearance = (arrow, active, target.anchor is not None)
        if appearance != self._appearance:
            self._appearance = appearance
            self.canvas.delete('all')
            color = '#2864b4' if active else '#edf3fb'
            ink = '#ffffff' if active else '#24558b'
            border = '#24558b' if target.anchor is None else '#498979'
            self.canvas.create_rectangle(1, 1, 31, 31, fill=color,
                                         outline=border, width=2)
            if arrow == 'center':
                self.canvas.create_rectangle(10, 10, 22, 22,
                                             outline=ink, width=3)
            else:
                self.canvas.create_line(*self.ARROWS[arrow], fill=ink,
                                        width=3, arrow=tk.FIRST)
        if not self.window.winfo_ismapped():
            self.window.deiconify()
        self.window.lift()

    def hide(self):
        """Masque le guide et invalide sa zone de dépôt."""
        if self.rect is not None and self.window.winfo_exists():
            self.window.withdraw()
        self.rect = self.target = None

    def destroy(self):
        """Libère le Toplevel, même si son propriétaire a été détruit."""
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        self.rect = self.target = None


class DockingGuides:
    """Affiche les destinations permises et applique le dépôt AUI.

    La disposition actuelle comporte des groupes gauche/centre/droite
    verticaux et haut/bas horizontaux. Le futur arbre de découpage pourra
    remplacer seulement la génération et l'application des cibles locales.
    """
    DIRECTIONS = (
        (AUI_DOCK_LEFT, 'left', 'IsLeftDockable'),
        (AUI_DOCK_RIGHT, 'right', 'IsRightDockable'),
        (AUI_DOCK_TOP, 'top', 'IsTopDockable'),
        (AUI_DOCK_BOTTOM, 'bottom', 'IsBottomDockable'),
        (AUI_DOCK_CENTER, 'center', 'IsDockable'),
    )
    CHROME = ('toolbar', 'status_bar')

    def __init__(self, manager):
        self.manager = manager
        self._windows = []

    def _host_rect(self):
        layout = self.manager._layout
        if layout is None:
            return None
        return _rect(layout.canvas if layout.canvas is not None else layout.parent)

    @classmethod
    def _allowed(cls, pane, direction):
        """Vérifie les drapeaux d'ancrage du panneau déplacé."""
        return any(d == direction and getattr(pane, method)()
                   for d, _, method in cls.DIRECTIONS)

    def _local_anchor(self, pane, host, x, y):
        """Trouve le visualiseur survolé, sans dépendre des Toplevel guides."""
        for candidate in reversed(self.manager._panes):
            if (candidate is pane or candidate.name in self.CHROME
                    or not candidate.IsShown() or candidate.IsFloating()):
                continue
            bounds = _intersection(host, _rect(candidate.window))
            if _contains(bounds, x, y):
                return candidate, bounds
        return None, None

    @staticmethod
    def _guide_rect(cx, cy):
        half = _GuideWindow.SIZE // 2
        return cx - half, cy - half, cx + half, cy + half

    def _targets(self, pane, host, x, y):
        """Calcule les guides globaux et les insertions locales possibles."""
        left, top, right, bottom = host
        cx, cy = (left + right) // 2, (top + bottom) // 2
        margin = 24
        positions = {
            'left': (left + margin, cy), 'right': (right - margin, cy),
            'top': (cx, top + margin), 'bottom': (cx, bottom - margin),
            'center': (cx, cy),
        }
        targets = []

        def add(rect, target, arrow, bounds):
            if _intersection(rect, bounds) != rect:
                return
            if any(_intersection(rect, existing) for existing, _, _ in targets):
                return
            targets.append((rect, target, arrow))

        for direction, arrow, _ in self.DIRECTIONS:
            if self._allowed(pane, direction):
                add(self._guide_rect(*positions[arrow]), DockTarget(direction), arrow, host)

        anchor, bounds = self._local_anchor(pane, host, x, y)
        if anchor is None or not self._allowed(pane, anchor.dock_direction):
            return targets
        l, t, r, b = bounds
        ax, ay = (l + r) // 2, (t + b) // 2
        gap = 38
        horizontal = anchor.dock_direction in (AUI_DOCK_TOP, AUI_DOCK_BOTTOM)
        offsets = ((-gap, 0, 'left'), (gap, 0, 'right')) if horizontal else (
            (0, -gap, 'top'), (0, gap, 'bottom'))
        for index, (dx, dy, arrow) in enumerate(offsets):
            add(self._guide_rect(ax + dx, ay + dy),
                DockTarget(anchor.dock_direction, anchor, index == 0), arrow, bounds)
        return targets

    def update(self, pane, x, y):
        """Actualise les guides et renvoie la destination effectivement survolée."""
        host = self._host_rect()
        if not pane.IsMovable() or not _contains(host, x, y):
            self.hide()
            return None
        targets = self._targets(pane, host, x, y)
        while len(self._windows) < len(targets):
            self._windows.append(_GuideWindow(self.manager.GetManagedWindow()))
        selected = None
        for window, (rect, target, arrow) in zip(self._windows, targets):
            active = _contains(rect, x, y)
            window.show(rect, target, arrow, active)
            if active:
                selected = target
        for window in self._windows[len(targets):]:
            window.hide()
        return selected

    def hide(self):
        """Masque les guides sans détruire les fenêtres réutilisables."""
        for window in self._windows:
            window.hide()

    def destroy(self):
        """Détruit les guides lors de la désinitialisation du gestionnaire."""
        for window in self._windows:
            window.destroy()
        self._windows.clear()

    def drop(self, pane, x, y):
        """Ancre sur une flèche, flotte hors zone, ou annule ailleurs."""
        try:
            if not pane.IsMovable():
                return False
            host = self._host_rect()
            if host is None:
                return False
            target = self.update(pane, x, y)
        finally:
            self.hide()
        if not _contains(host, x, y):
            if pane.IsFloatable():
                pane.FloatingPosition(x, y)
                self.manager.FloatPane(pane)
                return True
            return False
        if target is None:
            return False
        return self._apply(pane, target)

    def _apply(self, pane, target):
        """Traduit une destination vers les coordonnées AUI historiques."""
        direction, anchor = target.direction, target.anchor
        if not self._allowed(pane, direction):
            return False
        panes = list(self.manager._panes)
        if anchor is None:
            peers = [p for p in panes if p is not pane and p.dock_direction == direction]
            # Ajouter après le dernier groupe (layer, row, pos) existant.
            layer, row, pos = max(((p.dock_layer, p.dock_row, p.dock_pos)
                                   for p in peers), default=(0, 0, -1))
            pane.Direction(direction).Layer(layer).Row(row).Position(pos + 1)
        else:
            if anchor not in panes or anchor is pane or anchor.IsFloating() or not anchor.IsShown():
                return False
            layer, row = anchor.dock_layer, anchor.dock_row
            # Inclure aussi les panneaux masqués pour conserver des rangs uniques.
            peers = [p for p in panes if p is not pane and p.dock_direction == direction
                     and p.dock_layer == layer and p.dock_row == row]
            peers.sort(key=lambda p: p.dock_pos)
            index = peers.index(anchor) + (0 if target.before else 1)
            peers.insert(index, pane)
            pane.Direction(direction).Layer(layer).Row(row)
            for index, peer in enumerate(peers):
                peer.Position(index)
        self.manager.DockPane(pane)
        return True
