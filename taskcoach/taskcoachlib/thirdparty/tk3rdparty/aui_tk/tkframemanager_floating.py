# -*- coding: utf-8 -*-
"""Deuxième étape de la conversion de framemanager.py vers Tkinter.

Classes converties dans ce bloc :
- AuiDockingGuide :
- AuiDockingGuideWindow :
- AuiSingleDockingGuide :
- AuiCenterDockingGuide :
- AuiDockingHintWindow :
- AuiFloatingFrame :
"""

import tkinter as tk

# from . import tkframemanager, tkframemanager_auimanager
# from . import tkframemanager_auimanager
from .aui_tk_constants import *
from .aui_tk_utilities import GetDockingImage


def _safe_colour(art, key, fallback):
    """Retourne la couleur `key` de l'art provider, ou `fallback` en cas d'echec."""
    if art is None:
        return fallback
    try:
        value = art(key)
    except Exception:
        return fallback
    return value if value else fallback


class AuiDockingGuide(tk.Toplevel):
    """Classe de base pour gérer les guides de docking."""
    def __init__(
        self,
        parent,
        id=-1,
        title="",
        pos=None,
        size=None,
        style=None,
        name="AuiDockingGuide",
    ):
        """Initialise le guide de docking.

        Args:
            parent: Le parent du guide.
            id: L'identifiant du guide.
            title: Le titre du guide.
            pos: La position du guide.
            size: La taille du guide.
            style: Le style du guide.
            name: Le nom du guide.
        """
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

    def HitTest(self, x, y):
        return False

    def ValidateNotebookDocking(self, valid):
        return valid


class AuiDockingGuideWindow(tk.Toplevel):
    """Classe pour gérer la fenêtre de guide de docking."""
    def __init__(self, parent, rect, direction=0, center=False, useAero=False):
        """Initialise la fenêtre de guide de docking.

        Args:
            parent: Le parent de la fenêtre.
            rect: La région de la fenêtre.
            direction: La direction du guide.
            center: Indique si le guide est centré.
            useAero: Indique si Aero est utilisé.
        """
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._parent = parent
        self._direction = direction
        self._center = center
        self._valid = True
        self._useAero = useAero
        r = (
            rect
            if not hasattr(rect, "x")
            else (rect.x, rect.y, rect.width, rect.height)
        )
        self.geometry(f"{max(1,r[2])}x{max(1,r[3])}+{r[0]}+{r[1]}")
        self._bmp_unfocus, self._bmp_focus = GetDockingImage(direction, useAero, center)
        self._currentImage = self._bmp_unfocus
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

    def SetValid(self, valid):
        self._valid = valid

    def IsValid(self):
        return self._valid

    def OnEraseBackground(self, event):
        pass

    def DrawBackground(self, dc):
        dc.create_rectangle(
            0, 0, self.winfo_width(), self.winfo_height(), fill="#808080", outline=""
        )

    def DrawDottedLine(self, dc, point, length, vertical=True):
        x, y = point
        # for i in range(0, length, 4):
        for i in range(0, int(length), 4):
            if vertical:
                dc.create_line(x, y + i, x, y + i + 2, fill="#ffffff")
            else:
                dc.create_line(x + i, y, x + i + 2, y, fill="#ffffff")

    def DrawIcon(self, dc):
        img = self._currentImage
        if img is not None and hasattr(img, "GetPhotoImage"):
            dc.create_image(
                self.winfo_width() // 2,
                self.winfo_height() // 2,
                image=img.GetPhotoImage(),
            )

    def DrawArrow(self, dc):
        pass

    def OnPaint(self, event=None):
        self._canvas.delete("all")
        self.DrawBackground(self._canvas)
        self.DrawIcon(self._canvas)

    def Draw(self, dc):
        self.OnPaint(None)

    def UpdateDockGuide(self, pos):
        self.geometry(f"+{pos[0]}+{pos[1]}")


class AuiSingleDockingGuide(AuiDockingGuideWindow):
    """Classe pour gérer le simple guide de docking pour AUI."""
    def __init__(self, parent, direction=0):
        """Initialise le guide de docking simple.

        Args:
            parent: Le parent du guide.
            direction: La direction du guide.
        """
        super().__init__(parent, (0, 0, 31, 32), direction, False, False)

    def CreateShapesWithStyle(self, useWhidbey):
        pass

    def AeroMove(self, pos):
        self.UpdateDockGuide(pos)

    def SetGuideShape(self, event):
        pass

    def SetShape(self, region):
        pass

    def SetValid(self, valid):
        self._valid = valid

    def IsValid(self):
        return self._valid

    def UpdateDockGuide(self, pos):
        self.geometry(f"+{pos[0]}+{pos[1]}")

    def HitTest(self, x, y):
        return False


class AuiCenterDockingGuide(AuiDockingGuideWindow):
    """Classe pour gérer le guide de docking central pour AUI."""
    def __init__(self, parent):
        """Initialise le guide de docking central.

        Args:
            parent: Le parent du guide.
        """
        super().__init__(parent, (0, 0, 31, 32), AUI_DOCK_CENTER, True, False)

    def SetValid(self, valid):
        self._valid = valid

    def IsValid(self):
        return self._valid

    def UpdateDockGuide(self, pos):
        self.geometry(f"+{pos[0]}+{pos[1]}")

    def HitTest(self, x, y):
        return False


class AuiDockingHintWindow(tk.Toplevel):
    """Classe pour gérer la fenêtre d'indice de docking."""
    def __init__(
        self,
        parent,
        id=-1,
        title="",
        pos=None,
        size=(1, 1),
        style=None,
        name="auiHintWindow",
    ):
        """Initialise la fenêtre d'indice de docking.

        Args:
            parent: Le parent de la fenêtre.
            id: L'identifiant de la fenêtre.
            title: Le titre de la fenêtre.
            pos: La position de la fenêtre.
            size: La taille de la fenêtre.
            style: Le style de la fenêtre.
            name: Le nom de la fenêtre.
        """
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._blindMode = False
        # art = getattr(
        #     getattr(parent, "GetArtProvider", lambda: None)(), "GetColour", None
        # )
        provider = getattr(parent, 'GetArtProvider', lambda: None)()
        art = getattr(provider, 'GetColor', None) or getattr(provider, 'GetColour', None)
        # self._background = (
        #     "#0040ff" if art is None else art(AUI_DOCKART_HINT_WINDOW_COLOUR)
        # )
        self._background = _safe_colour(art, AUI_DOCKART_HINT_WINDOW_COLOUR, '#0040ff')
        # self._border = (
        #     "#3c3c3c" if art is None else art(AUI_DOCKART_HINT_WINDOW_BORDER_COLOUR)
        # )
        self._border = _safe_colour(art, AUI_DOCKART_HINT_WINDOW_BORDER_COLOUR, '#3c3c3c')
        self._canvas = tk.Canvas(self, highlightthickness=0, bg=self._background)
        self._canvas.pack(fill="both", expand=True)

    def MakeVenetianBlinds(self):
        pass

    def SetBlindMode(self, agwFlags):
        self._blindMode = bool(agwFlags & AUI_MGR_VENETIAN_BLINDS_HINT)

    def SetShape(self, region):
        pass

    def Show(self, show=True):
        if show:
            self.deiconify()
        else:
            self.withdraw()

    def OnSize(self, event):
        pass

    def OnPaint(self, event=None):
        self._canvas.delete("all")
        w, h = self._canvas.winfo_width(), self._canvas.winfo_height()
        self._canvas.create_rectangle(
            2, 2, max(3, w - 2), max(3, h - 2), outline=self._border, width=4
        )


class AuiFloatingFrame(tk.Toplevel):
    """Classe représentant une fenêtre flottante dans l'interface utilisateur."""
    def __init__(self, parent, owner_mgr, pane=None, id=-1, title="", style=None):
        """
        Classe constructeur par défaut.
        Args:
            parent: Le parent de la fenêtre
            owner_mgr: Le gestionnaire de fenêtres
            pane: Le panneau associé
            id: L'identifiant de la fenêtre
            title: Le titre de la fenêtre
            style: Le style de la fenêtre
        """
        super().__init__(parent)
        self.attributes("-topmost", False)
        self.title(title or (pane.caption if pane else ""))
        self._owner_mgr = owner_mgr
        self._pane = pane
        self._flyTimer = None
        self._checkFlyTimer = None
        if pane:
            self.SetPaneWindow(pane)

    def CopyAttributes(self, pane):
        """Copie et retourne les attributs du panneau dans une autre classe AuiPaneInfo.

        Returns:
            Une instance de AuiPaneInfo contenant les attributs copiés.
        """
        from . import tkframemanager_auimanager
        # pass
        contained_pane = tkframemanager_auimanager.AuiPaneInfo()

        return contained_pane

    def SetPaneWindow(self, pane):
        """Définit la fenêtre du panneau.

        Règle toutes les propriétés de la fenêtre du panneau.

        Args:
            pane: Le panneau pour lequel définir la fenêtre.
        """
        self._pane = pane
        pane.frame = self
        window = pane.window
        # if window is not None:
        #     window.pack_forget() if hasattr(window, "pack_forget") else None
        #     window.master and hasattr(window, "tk") and window.configure(in_=self)
        #     window.pack(fill="both", expand=True) if hasattr(window, "pack") else None
        if window is not None and hasattr(window, 'pack_forget'):
            window.pack_forget()
        # Tkinter ne permet pas de re-parenter un widget existant vers un
        # nouveau Toplevel : le cadre flottant affiche uniquement son titre
        # pour l'instant. A affiner ulterieurement (par exemple via "wm manage").
        # Il faudrait le reconstruire ? non, il s'agit d'une fenêtre flottante.
        if pane.floating_pos[0] >= 0:
            self.geometry(f"+{pane.floating_pos[0]}+{pane.floating_pos[1]}")
        if pane.floating_size[0] > 0:
            self.geometry(f"{pane.floating_size[0]}x{pane.floating_size[1]}")
        self.protocol("WM_DELETE_WINDOW", lambda: self.OnClose(None))

    def GetOwnerManager(self):
        """
        Returns:
            La classe AuiManager qui gère le panneau.
        """
        return self._owner_mgr

    def OnSize(self, event):
        pass

    def OnClose(self, event):
        mgr = self.GetOwnerManager()
        if mgr:
            mgr.OnFloatingPaneClosed(self, event)
        self.destroy()

    def OnActivate(self, event):
        pass

    def OnMove(self, event):
        pass

    def OnMoveEvent(self, event):
        pass

    def OnIdle(self, event):
        pass

    def OnMoveStart(self, event):
        """Commence l'opération de déplacement du panneau flottant."""
        pass

    def OnMoving(self, rect, direction):
        """Déplace le panneau flottant."""
        pass

    def OnMoveFinished(self):
        """Termine l'opération de déplacement du panneau flottant."""
        pass

    def OnCheckFlyTimer(self, event=None):
        pass

    def OnFindManager(self, event):
        pass

    def FlyOut(self):
        """
        Commence l'opération de vol du panneau flottant.

        Returns:
            None
        """
        pass

    def OnFlyTimer(self, event=None):
        """

        Args:
            event:
        """
        pass

    def FadeOut(self):
        """
        Commence l'opération de fondu du panneau flottant.

        Returns:
            None
        """
        self.destroy()
