# -*- coding: utf-8 -*-
"""AuiToolBar Tkinter, conversion de la classe wxPython AuiToolBar."""
# ---------------------------------------------------------------------------
# AuiToolBar: configuration, state, layout and interaction helpers
#
# This block groups the toolbar's property setters/getters and event-handling
# hooks. In the wxPython origin, these methods control visual state,
# tool metadata, layout metrics, and user interaction with the toolbar.
#
# The implementation is adapted to Tkinter and keeps the same conceptual
# API as the upstream AuiToolBar, while rendering the content on a Canvas.
# ---------------------------------------------------------------------------


import tkinter as tk
from tkinter import ttk

try:
    from .tkauibar_event_item import AuiToolBarItem
    from .tkauibar_art import AuiDefaultToolBarArt
    from .aui_tk_constants import *
except ImportError:
    from tkauibar_event_item import AuiToolBarItem
    from tkauibar_art import AuiDefaultToolBarArt
    from aui_tk_constants import *


# class AuiToolBar(tk.Frame):
class AuiToolBar(tk.LabelFrame):  # LabelFrame est temporaire !
    """AuiToolBar Tkinter, conversion de la classe wxPython AuiToolBar.

    AuiToolBar est un widget de barre d'outils complètement redessiné et adapté
    à Tkinter. Il permet de créer des barres d'outils avec des boutons, des
    séparateurs, des étiquettes, des contrôles, etc. Il est possible de
    personnaliser l'apparence de la barre d'outils en utilisant un art
    provider et de glisser-déposer la barre d'outils.

    Le theme par défaut est AuiDefaultToolBarArt. Il peut être modifié en
    utilisant la méthode SetArtProvider.
    """
    def __init__(self, parent, window, text, id=-1, pos=None, size=None, style=None, agwStyle=0):
        """
        Constructeur de la classe AuiToolBar.

        Args:
            parent: Widget Tkinter maître de la barre d'outils
            window: Contrôleur logique de la barre d'outils
            text: Texte de la barre d'outils
            id: Identifiant de la barre d'outils
            pos: Position de la barre d'outils
            size: Taille de la barre d'outils
            style: Style de la barre d'outils
            agwStyle: Style AGW de la barre d'outils.

        Le style de la barre d'outils est initialisé à AUI_TBTOOL_HORIZONTAL=0.
        Il peut être modifié en utilisant la méthode SetStyle et les différentes
        constantes de style disponibles :
        ============================================
        Nom Valeur Description
        ======================== ======= ===========
        AUI_TB_TEXT Affiche le texte dans le bouton; par défaut, seuls les icônes sont affichées.
        AUI_TB_NO_TOOLTIPS Désactive l'affichage des tooltips.
        AUI_TB_NO_AUTORESIZE Désactive l'auto-redimensionnement.
        AUI_TB_GRIPPER Affiche le gripper.
        AUI_TB_OVERFLOW Peut contenir les boutons qui ne peuvent pas être affichés.
        AUI_TB_VERTICAL L'orientation de la barre d'outils est verticale.
        AUI_TB_HORZ_LAYOUT Affiche le texte et les icônes l'un au-dessus de l'autre, pas l'un à côté de l'autre.
        AUI_TB_PLAIN_BACKGROUND Utilise un arrière-plan uni, pas en dégradé.
        AUI_TB_HORZ_TEXT Affiche le texte à côté des icônes, combinaison de AUI_TB_TEXT et AUI_TB_HORZ_LAYOUT.
        AUI_TB_DOCKABLE Permet de faire glisser la barre d'outils.
        ======================= ======== ==========
        """
        super().__init__(parent, text=text)
        self._agwStyle = agwStyle
        self._art = AuiDefaultToolBarArt()
        self._items = []
        self._tool_bitmap_size = (16, 16)
        self._tool_separation = 5
        self._border_padding = 2
        self._orientation = AUI_TBTOOL_HORIZONTAL
        self._packing = 1
        self._margins = (0, 0, 0, 0)
        self._gripper_visible = True
        self._overflow_visible = True
        self._auiManager = None
        self._hover_item = None
        self._pressed_item = None
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Button-1>", self.OnLeftDown)
        self._canvas.bind("<ButtonRelease-1>", self.OnLeftUp)
        self._canvas.bind("<Motion>", self.OnMotion)
        self._canvas.bind("<Configure>", self.OnSize)

    def SetWindowStyleFlag(self, style):
        """
        Règle le style de la fenêtre.

        Args:
            style: (int) Style de la fenêtre.

        Returns:
            None
        """
        self._style = style

    def SetAGWWindowStyleFlag(self, agwStyle):
        """
        Règle le style spécifique AGW de la fenêtre.

        Args:
            agwStyle: (int) Style spécifique AGW de la fenêtre.

        Returns:
            None

        Le style peut être modifié en utilisant les constantes de style disponibles :
        ============================================
        Nom Valeur Description
        ======================== ======= ===========
        AUI_TB_TEXT Affiche le texte dans le bouton ; par défaut, seuls les icônes sont affichées.
        AUI_TB_NO_TOOLTIPS Désactive l'affichage des tooltips.
        AUI_TB_NO_AUTORESIZE Désactive l'auto-redimensionnement.
        AUI_TB_GRIPPER Affiche le gripper.
        AUI_TB_OVERFLOW Peut contenir les boutons qui ne peuvent pas être affichés.
        AUI_TB_VERTICAL L'orientation de la barre d'outils est verticale.
        AUI_TB_HORZ_LAYOUT Affiche le texte et les icônes l'un au-dessus de l'autre, pas l'un à côté de l'autre.
        AUI_TB_PLAIN_BACKGROUND Utilise un arrière-plan uni, pas en dégradé.
        AUI_TB_HORZ_TEXT Affiche le texte à côté des icônes, combinaison de AUI_TB_TEXT et AUI_TB_HORZ_LAYOUT.
        AUI_TB_DOCKABLE Permet de faire glisser la barre d'outils.
        ======================= ======== ==========
        """
        self._agwStyle = agwStyle

    def GetAGWWindowStyleFlag(self):
        """
        Récupère le style spécifique AGW de la fenêtre.

        Returns :
            (int) Style spécifique AGW de la fenêtre.
        """
        return self._agwStyle

    def SetArtProvider(self, art):
        """
        Règle l'art provider de la fenêtre.

        Args:
            art: Un art provider.

        Returns:
            None
        """
        self._art = art

    def GetArtProvider(self):
        """
        Récupère l'art provider de la fenêtre.

        Returns:
            Un art provider.
        """
        return self._art

    def AddTool(
        self,
        tool_id,
        label,
        bitmap=None,
        disabled_bitmap=None,
        kind=ITEM_NORMAL,
        short_help_string="",
        long_help_string="",
        client_data=None,
        target=None,
    ):
        """
        Ajoute un bouton à la barre d'outils.

        Args:
            tool_id: (int) Identifiant de l'outil.
            label: Etiquette de l'outil dans la toolbar.
            bitmap: Image de l'outil.
            disabled_bitmap: Image de l'outil quand il est désactivé.
            Kind: (int) Type de l'outil.
            Short_help_string: (str) Texte de l'outil. Version courte.
            Long_help_string: (str) Texte de l'outil. Version longue.
            client_data: Données client associées à l'outil.
            target: Cible de l'outil.

        Returns:
            L'objet AuiToolBarItem ajouté.

        ================================================
        Type d'outil Description
        =============== ================================
        ITEM_CONTROL Un contrôle personnalisé
        ITEM_LABEL Un label
        ITEM_SPACER Un espaceur
        ITEM_NORMAL Un bouton normal
        ITEM_SEPARATOR Un séparateur
        ITEM_CHECK Un bouton de type case à cocher
        ITEM_RADIO Un bouton de type radio
        ITEM_DROPDOWN Un bouton de type dropdown
        ================================================
        """
        toolbar_item = AuiToolBarItem()
        toolbar_item.SetId(tool_id)
        toolbar_item.SetLabel(label)
        toolbar_item.SetBitmap(bitmap)
        toolbar_item.SetDisabledBitmap(disabled_bitmap)
        toolbar_item.SetKind(kind)
        toolbar_item.SetShortHelp(short_help_string)
        toolbar_item.SetLongHelp(long_help_string)
        toolbar_item.SetUserData(client_data)
        toolbar_item.target = target
        self._items.append(toolbar_item)
        return toolbar_item

    def AddSimpleTool(
        self,
        tool_id,
        label,
        bitmap,
        short_help_string="",
        kind=ITEM_NORMAL,
        target=None,
    ):
        """
        Ajoute un bouton simple à la barre d'outils.
        C'est la plus simple méthode pour ajouter un bouton.

        Args:
            tool_id: tool_id: (int) Identifiant de l'outil.
            Label: (str) Etiquette de l'outil dans la toolbar.
            Bitmap: (wx. Bitmap) Image de l'outil.
            Short_help_string: (str) Texte de l'outil. Version courte.
            Kind: (int) Type de l'outil.
            Target: (wx. Window) Cible de l'outil.

        Returns:
            L'objet AuiToolBarItem ajouté.

        ================================================
        Type d'outil Description
        =============== ================================
        ITEM_CONTROL Un contrôle personnalisé
        ITEM_LABEL Un label
        ITEM_SPACER Un espaceur
        ITEM_NORMAL Un bouton normal
        ITEM_SEPARATOR Un séparateur
        ITEM_CHECK Un bouton de type case à cocher
        ITEM_RADIO Un bouton de type radio
        ITEM_DROPDOWN Un bouton de type dropdown
        ================================================
        """
        return self.AddTool(
            tool_id, label, bitmap, None, kind, short_help_string, "", None, target
        )

    def AddToggleTool(
        self,
        tool_id,
        bitmap,
        disabled_bitmap=None,
        toggle=False,
        client_data=None,
        short_help_string="",
        long_help_string="",
    ):
        """
        Ajoute un outil à la barre d'outils.

        Args:
            tool_id: Identifiant de l'outil.
            bitmap: Image/icone de l'outil.
            disabled_bitmap: Image/icone pour l'outil désactivé.
            toggle: Booléen définissant l'état caché ou non.
            client_data: Données client assicées à l'outil.
            short_help_string: Aide au format court.
            long_help_string: Aide au format long.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        i = self.AddTool(
            tool_id,
            "",
            bitmap,
            disabled_bitmap,
            ITEM_CHECK,
            short_help_string,
            long_help_string,
            client_data,
        )
        i.SetState(1 if toggle else 0)
        return i

    def AddCheckTool(self, *tool, **k):
        """
        Ajoute un outil de type case à cocher à la barre d'outils.

        Args:
            *tool: Outil à ajouter.
            **k: Liste d'outils.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        return self.AddTool(
            k.pop("tool_id", tool[0] if tool else 0),
            k.pop("label", ""),
            k.pop("bitmap", None),
            k.pop("disabled_bitmap", None),
            ITEM_CHECK,
            k.pop("short_help_string", ""),
            k.pop("long_help_string", ""),
            k.pop("client_data", None),
        )

    def AddRadioTool(self, *tool, **k):
        """
        Ajoute un nouvel outil avec case à cocher à la barre d'outils.

        Args:
            *tool: Outil à ajouter.
            **k: Liste d'outils.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        return self.AddCheckTool(*tool, **k)

    def AddControl(self, control, label=""):
        """
        Ajoute un contrôle personnalisé à la barre d'outils.

        Args:
            control: (tk) La contrôle à ajouter.
            label: (str) Le libellé du contrôle.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        item = self.AddTool(id(control), label, None, None, ITEM_CONTROL)
        item.SetWindow(control)
        return item

    def AddLabel(self, tool_id, label, width=0):
        """
        Ajoute une étiquette à l'outil.

        Args:
            tool_id: Identifiant de l'outil.
            label: Etiquette à ajouter.
            width: Largeur de l'outil.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        return self.AddTool(tool_id, label, None, None, ITEM_LABEL)

    def AddSeparator(self):
        """
        Ajoute un séparateur pour espacer les groupes d'outils.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        return self.AddTool(-1, "", None, None, ITEM_SEPARATOR)

    def AddSpacer(self, pixels):
        """
        Ajoute un espaceur.

        Args:
            pixels: Largeur de l'espaceur.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        item = self.AddTool(-1, "", None, None, ITEM_SPACER)
        item.SetSpacerPixels(pixels)
        return item

    def AddStretchSpacer(self, proportion=1):
        """
        Ajoute un espaceur réglable pour espacer les groupes d'outils.

        Args:
            proportion: Proportion de l'espaceur.

        Returns:
            L'objet AuiToolBarItem ajouté.
        """
        item = self.AddSpacer(0)
        item.SetProportion(proportion)
        return item

    def Clear(self):
        """
        Supprime tous les outils de la barre d'outils.
        """
        self.ClearTools()

    def ClearTools(self):
        """
        Supprime tous les outils de la barre d'outils.
        """
        self._items.clear()
        self.OnPaint(None)

    def DeleteTool(self, tool):
        """
        Enlève les outils spécifiés de la barre d'outils et les supprime.

        Args:
            tool: L'outil à supprimer.

        Returns:
            True si l'outil a été supprimé, False sinon.
        """
        return self.DeleteToolByPos(
            self.GetToolIndex(tool if isinstance(tool, int) else tool.GetId())
        )

    def DeleteToolByPos(self, pos):
        """
        Enlève les outils spécifiés selon leur position.

        Args:
            pos: Position de l'outil à supprimer.

        Returns:
            True si l'outil a été supprimé, False sinon.
        """
        if 0 <= pos < len(self._items):
            self._items.pop(pos)
            self.OnPaint(None)
            return True
        return False

    def FindControl(self, id):
        """
        Retourne la fenêtre de contrôle identifiée par l'identifiant de l'outil.

        Args:
            id: Identifiant de l'outil.

        Returns:
            La fenêtre de contrôle si l'outil est trouvé, None sinon.
        """
        wnd = self.FindTool(id)
        return wnd.GetWindow() if wnd else None

    def FindTool(self, tool_id):
        """
        Trouve un outil pour l'identifiant donné.
        Args:
            tool_id: (int) Identifiant de l'outil.

        Returns:
            L'outil correspondant à l'identifiant donné, None sinon.
        """
        return next((item for item in self._items if item.GetId() == tool_id), None)

    def FindToolByLabel(self, label):
        """
        Trouve un outil pour le libellé donné.

        Args:
            label: Etiquette de l'outil.

        Returns:
            L'outil correspondant au label donné.
        """
        return next((item for item in self._items if item.GetLabel() == label), None)

    def FindToolByUserData(self, userData):
        """
        Trouve un outil pour l'utilisateur donné.

        Args:
            userData: Utilisateur.

        Returns:
            L'outil correspondant à l'utilisateur donné.
        """
        return next((item for item in self._items if item.GetUserData() == userData), None)

    def FindToolForPosition(self, x, y):
        """
        Trouve un outil pour la position donnée.

        Args:
            x: Position 'x' de la souris.
            y: Position 'y' de la souris.

        Returns:
            L'outil correspondant à la position donnée.
        """
        return self.FindToolByIndex(self.HitTest(x, y))

    def HitTest(self, x, y):
        """
        Trouve un outil pour la position de la souris donnée.
        Args:
            x: Position 'x' de la souris sur l'écran.
            y: Position 'y' de la souris sur l'écran.

        Returns:
            L'outil correspondant à la position de la souris donnée en coordonnées absolues.
        """
        return next(
            (
                n
                for n, i in enumerate(self._items)
                if getattr(i, "rect", (0, 0, 0, 0))[0]
                <= x
                <= getattr(i, "rect", (0, 0, 0, 0))[0]
                + getattr(i, "rect", (0, 0, 0, 0))[2]
            ),
            -1,
        )

    def FindToolForPositionWithPacking(self, x, y):
        """
        Trouve et retourne un outil pour la position, prise dans
        Args:
            x: Position 'x' de la souris.
            y: Position 'y' de la souris.

        Returns:
            L'outil correspondant à la position donnée.
        """
        return self.FindToolForPosition(x, y)

    def FindToolByIndex(self, pos):
        """
        Trouve un outils pour une position.

        Args:
            pos: (int) Position de l'outil dans la barre d'outils.

        Returns:
            L'outil correspondant à la position donnée.
        """
        return self._items[pos] if 0 <= pos < len(self._items) else None

    def SetToolBitmapSize(self, size):
        """
        Règle la taille des images des outils.

        Args:
            size: (int) Taille des images des outils.
        """
        self._tool_bitmap_size = size

    def GetToolBitmapSize(self):
        """
        Retourne la taille du bitmap que la barre d'outils utilise.

        Returns:
            La taille du bitmap.
        """
        return self._tool_bitmap_size

    def SetToolProportion(self, tool_id, proportion):
        """
        Règle la proportion de l'outil dans la barre d'outils.

        Args:
            tool_id: Identifiant de l'outil.
            proportion: Proportion de l'outil.

        Returns:
            None
        """
        self.FindTool(tool_id).SetProportion(proportion)

    def GetToolProportion(self, id):
        """
        Retourne la proportion de l'outil dans la barre d'outils.

        Args:
            id: Identifiant de l'outil.

        Returns:
            La proportion de l'outil.
        """
        return self.FindTool(id).GetProportion()

    def SetToolSeparation(self, separation):
        """
        Règle la taille de la séparation pour la barre d'outils.

        Args:
            separation: Taille de la séparation.

        Returns:
            None
        """
        self._tool_separation = separation

    def GetToolSeparation(self):
        """
        Retourne la taille de la séparation pour la barre d'outils, (en pixels ?!).

        Returns:
            La taille de la séparation.
        """
        return self._tool_separation

    def SetToolDropDown(self, tool_id, dropdown):
        """
        Règle un menu de fenêtre drop down de l'élément de la toolbar.

        Args:
            tool_id: Identifiant de l'outil.
            dropdown: Menu de fenêtre drop down.

        Returns:
            None
        """
        self.FindTool(tool_id).SetHasDropDown(dropdown)

    def GetToolDropDown(self, tool_id):
        """
        Returns whether the toolbar item identified by `tool_id` has an associated drop-down window menu or not.

        Retourne

        Args:
            tool_id: Identifiant de l'outil.

        Returns:
            L'outil correspondant
        """
        return self.FindTool(tool_id).HasDropDown()

    def SetToolSticky(self, tool_id, sticky):
        """
        Règle l'élément de la barre d'outils comme collant ou non-collant.

        Args:
            tool_id: Identifiant de l'outil.
            sticky:

        Returns:

        """
        self.FindTool(tool_id).SetSticky(sticky)

    def GetToolSticky(self, tool_id):
        """
        Retourne l'état collé de l'élément identifié de la barre d'outils.

        Args:
            tool_id: Identifiant de l'outil.

        Returns:
            Le statut d'adhérence de l'outil.
        """
        return self.FindTool(tool_id).IsSticky()

    def SetToolBorderPadding(self, padding):
        """
        Règle la padding entre le bord de l'outil

        Args:
            padding:

        Returns:
            None
        """
        self._border_padding = padding

    def GetToolBorderPadding(self):
        """
        Retourne le padding entre les bords de l'outil et l'étiquette, en pixels.

        Returns:
            Le padding entre les bords de l'outil et l'étiquette, en pixels.
        """
        return self._border_padding

    def SetToolTextOrientation(self, orientation):
        """
        Règle l'orientation de l'étiquette pour l'élément de la barre d'outil.

        Args:
            orientation: (int) Valeur de l'orientation de l'étiquette.

        Returns:
            None
        """
        self._art.SetTextOrientation(orientation)

    def GetToolTextOrientation(self):
        """
        Récupère et retourne l'orientation du texte de l'étiquette.

        Returns:
            (int) L'orientation du texte de l'étiquette.
        """
        return self._art.GetTextOrientation()

    def SetToolOrientation(self, orientation):
        """
        Règle l'orientation de l'outil pour l'élément de la barre d'outil.
        Args:
            orientation: (int) Valeur de l'orientation de l'outil.

        Returns:
            None
        """
        self.SetOrientation(orientation)

    def GetToolOrientation(self):
        """
        Récupère et retourne l'orientation de l'outil.

        Returns:
            (int) L'orientation de l'élément de la barre d'outils.
        """
        return self._orientation

    def SetToolPacking(self, packing):
        """
        Configure how toolbar tools are packed in the layout.

        Args:
            packing: Layout packing mode or spacing policy used by the toolbar.
        """
        self._packing = packing

    def GetToolPacking(self):
        """
        Return the current packing configuration used by the toolbar.

        Returns:
            The current packing value.
        """
        return self._packing

    def SetOrientation(self, v):
        """
        Set the toolbar orientation.

        This updates both the internal orientation state and the art provider so
        that drawing code uses the correct orientation for the current UI layout.

        Args:
            v: Orientation flag, typically a horizontal/vertical constant.
        """
        self._orientation = v
        self._art.SetOrientation(v)

    def SetMargins(self, left, right, top, bottom):
        """
        Set the toolbar margins for all sides.

        Args:
            left: Left margin in pixels.
            right: Right margin in pixels.
            top: Top margin in pixels.
            bottom: Bottom margin in pixels.
        """
        self._margins = (left, right, top, bottom)

    def SetMarginsSize(self, size):
        """
        Set symmetric horizontal and vertical margins from a 2-tuple.

        Args:
            size: Tuple of the form (horizontal, vertical).
        """
        self.SetMargins(size[0], size[0], size[1], size[1])

    def SetMarginsXY(self, x, y):
        """
        Set equal left/right and top/bottom margins using x and y values.

        Args:
            x: Horizontal margin to apply on both sides.
            y: Vertical margin to apply on both sides.
        """
        self.SetMargins(x, x, y, y)

    def GetGripperVisible(self):
        """
        Return whether the toolbar gripper is visible.

        Returns:
            True if the gripper is shown, otherwise False.
        """
        return self._gripper_visible

    def SetGripperVisible(self, v):
        """
        Enable or disable the toolbar gripper.

        Args:
            v: Boolean indicating whether the gripper should be displayed.
        """
        self._gripper_visible = v

    def GetOverflowVisible(self):
        """
        Return whether the overflow control is visible.

        Returns:
            True if overflow controls are visible, otherwise False.
        """
        return self._overflow_visible

    def SetOverflowVisible(self, v):
        """
        Enable or disable the overflow display state.

        Args:
            v: Boolean indicating whether overflow UI should be shown.
        """
        self._overflow_visible = v

    def SetFont(self, f):
        """
        Set the font used by the toolbar art provider.

        Args:
            f: Font object to assign to the toolbar rendering.
        """
        self._art.SetFont(f)

    def SetHoverItem(self, p):
        """
        Store the currently hovered toolbar item.

        Args:
            p: Toolbar item instance or None.
        """
        self._hover_item = p

    def SetPressedItem(self, p):
        """
        Store the currently pressed toolbar item.

        Args:
            p: Toolbar item instance or None.
        """
        self._pressed_item = p

    def RefreshOverflowState(self):
        """
        Refresh the overflow state.

        This method is currently a stub in the Tkinter port and does not yet
        implement overflow logic beyond the default no-op.
        """
        pass

    def ToggleTool(self, id, state):
        """
        Toggle a tool's checked/selected state.

        Args:
            id: Tool identifier.
            state: True to enable the checked state, False to clear it.
        """
        self.FindTool(id).SetState(1 if state else 0)
        self.OnPaint(None)

    def GetToolToggled(self, id):
        """
        Return True if the tool with the given id is toggled/checked.

        Args:
            id: Tool identifier.

        Returns:
            Boolean indicating the tool's toggled state.
        """
        return bool(self.FindTool(id).GetState())

    def EnableTool(self, id, state):
        """
        Enable or disable a toolbar item.

        Args:
            id: Tool identifier.
            state: True to activate the tool, False to disable it.
        """
        self.FindTool(id).SetActive(state)

    def GetToolEnabled(self, id):
        """
        Return whether the given tool is active/enabled.

        Args:
            id: Tool identifier.

        Returns:
            True if the tool is enabled, otherwise False.
        """
        return self.FindTool(id).IsActive()

    def GetToolLabel(self, id):
        """
        Return the text label associated with a toolbar tool.

        Args:
            id: Tool identifier.

        Returns:
            The label string or the tool's current text.
        """
        return self.FindTool(id).GetLabel()

    def SetToolLabel(self, id, v):
        """
        Update the label of a toolbar tool.

        Args:
            id: Tool identifier.
            v: New label string.
        """
        self.FindTool(id).SetLabel(v)

    def GetToolBitmap(self, id):
        """
        Return the normal bitmap for a tool.

        Return the bitmap associated with a toolbar tool.

        Args:
            id: Tool identifier.

        Returns:
            The bitmap object or None.
        """
        return self.FindTool(id).GetBitmap()

    def SetToolBitmap(self, id, v):
        """
        Set the normal bitmap of a tool.

        This is a convenience alias for SetToolNormalBitmap.

        Args:
            id: Tool identifier.
            v: Bitmap or image object.
        """
        self.SetToolNormalBitmap(id, v)

    def SetToolNormalBitmap(self, id, v):
        """
        Set the standard bitmap used for the tool in its enabled state.

        Args:
            id: Tool identifier.
            v: Bitmap or image object.
        """
        self.FindTool(id).SetBitmap(v)

    def SetToolDisabledBitmap(self, id, v):
        """
        Set the bitmap used for the tool in its disabled state.

        Args:
            id: Tool identifier.
            v: Disabled-state bitmap or image object.
        """
        self.FindTool(id).SetDisabledBitmap(v)

    def GetToolShortHelp(self, id):
        """
        Return the short help text for a tool.

        Args:
            id: Tool identifier.

        Returns:
            Short help string.
        """
        return self.FindTool(id).GetShortHelp()

    def SetToolShortHelp(self, id, v):
        """
        Set the short help text of a tool.

        Args:
            id: Tool identifier.
            v: Short help string shown in tooltips or status text.
        """
        self.FindTool(id).SetShortHelp(v)

    def GetToolLongHelp(self, id):
        """
        Return the long help text of a tool.

        Args:
            id: Tool identifier.

        Returns:
            Long help string.
        """
        return self.FindTool(id).GetLongHelp()

    def SetToolAlignment(self, alignment):
        """
        Set the alignment preference for tools within the toolbar.

        Args:
            alignment: Alignment constant or layout hint.
        """
        self._alignment = alignment

    def SetToolLongHelp(self, id, v):
        """
        Set the long help text of a tool.

        Args:
            id: Tool identifier.
            v: Long help string.
        """
        self.FindTool(id).SetLongHelp(v)

    def SetCustomOverflowItems(self, prepend, append):
        """
        Register custom overflow items appended before and after the default ones.

        Args:
            prepend: Items to add before the regular overflow elements.
            append: Items to add after the regular overflow elements.
        """
        self._overflow_prepend = prepend
        self._overflow_append = append

    def GetToolCount(self):
        """
        Return the number of tools currently stored in the toolbar.

        Returns:
            Integer count of toolbar items.
        """
        return len(self._items)

    def GetToolIndex(self, id):
        """
        Return the index of a tool by its identifier.

        Args:
            id: Tool identifier.

        Returns:
            Index of the matching tool, or -1 if not found.
        """
        return next((n for n, i in enumerate(self._items) if i.GetId() == id), -1)

    def GetToolPos(self, id):
        """
        Alias for GetToolIndex.

        Args:
            id: Tool identifier.

        Returns:
            Position index of the identified tool.
        """
        return self.GetToolIndex(id)

    def GetToolFitsByIndex(self, id):
        """
        Return whether the tool at the given index fits within the available space.

        In this Tkinter port, all tools are treated as fitting by default.

        Args:
            id: Tool identifier or index-like token.

        Returns:
            Always True in the current implementation.
        """
        return True

    def GetToolFits(self, id):
        """
        Return whether the given tool fits in the current toolbar layout.

        Args:
            id: Tool identifier.

        Returns:
            Always True in the current implementation.
        """
        return True

    def GetToolRect(self, id):
        """
        Return the screen-space rectangle for a tool.

        Args:
            id: Tool identifier.

        Returns:
            Tuple of (x, y, width, height) if found, otherwise None.
        """
        i = self.FindTool(id)
        return getattr(i, "rect", (0, 0, 0, 0)) if i else None

    def GetToolBarFits(self):
        """
        Return whether the toolbar fits in its current layout.

        Returns:
            Always True in the current implementation.
        """
        return True

    def Realize(self):
        """
        Force a toolbar redraw and finalize its current layout.

        Returns:
            True after painting has been triggered.
        """
        self.OnPaint(None)
        return True

    def GetOverflowState(self):
        """
        Return the current overflow state.

        Returns:
            False by default, as overflow is not yet represented.
        """
        return False

    def GetOverflowRect(self):
        """
        Return the overflow region rectangle.

        Returns:
            Empty rectangle (0, 0, 0, 0).
        """
        return (0, 0, 0, 0)

    def GetLabelSize(self, label):
        """
        Measure the rendered size of a label using the current toolbar font.

        Args:
            label: Text to measure.

        Returns:
            Tuple of (width, height) computed from the active font.
        """
        return (
            self._art.GetFont().measure(label),
            self._art.GetFont().metrics("linespace"),
        )

    def GetAuiManager(self):
        """
        Return the AUI manager associated with the toolbar.

        Returns:
            The AUI manager instance. The linked AUI manager or None.
        """
        return self._auiManager

    def SetAuiManager(self, v):
        """
        Attach this toolbar to an AUI manager.

        Args:
            v: AUI manager instance.
        """
        self._auiManager = v

    def DoIdleUpdate(self):
        """
        Trigger a repaint during idle processing.

        This keeps the drawing state synchronized without requiring an explicit refresh.
        """
        self.OnPaint(None)

    def OnSize(self, event):
        """
        Handle a resize event for the toolbar canvas.

        Args:
            event: Tkinter resize event object.
        """
        self.OnPaint(event)

    def DoSetSize(self, x, y, width, height, sizeFlags=None):
        """
        Set the toolbar geometry explicitly.

        Args:
            x: Left coordinate.
            y: Top coordinate.
            width: Width in pixels.
            height: Height in pixels.
            sizeFlags: Additional sizing flags ignored by the Tk port.
        """
        self.place(x=x, y=y, width=width, height=height)

    def OnIdle(self, event):
        """
        Handle idle processing for the toolbar.

        Args:
            event: Tkinter idle event.
        """
        self.DoIdleUpdate()

    def DoGetBestSize(self):
        """
        Return a preferred default size for the toolbar.

        Returns:
            Tuple (width, height) representing the default preferred size.
        """
        return (400, 32)

    def OnPaint(self, event):
        """
        Repaint the toolbar canvas.

        The method clears the canvas, walks every toolbar item, computes its
        rendered width, assigns a rectangle to it, and calls the art provider to
        draw separators, spacers, or buttons as appropriate.

        Args:
            event: Tkinter canvas event or None.
        """
        self._canvas.delete("all")
        x = 2
        h = max(24, self.winfo_height())
        for i in self._items:
            w = max(28, self._art.GetToolSize(self._canvas, self, i)[0])
            i.rect = (x, 0, w, h)
            if i.kind == ITEM_SEPARATOR:
                self._art.DrawSeparator(self._canvas, self, i.rect)
            elif i.kind == ITEM_SPACER:
                x += i.spacer_pixels
                continue
            else:
                (
                    self._art.DrawDropDownButton(self._canvas, self, i, i.rect)
                    if i.HasDropDown()
                    else self._art.DrawButton(self._canvas, self, i, i.rect)
                )
            x += w + self._tool_separation

    def OnEraseBackground(self, event):
        """
        No-op background erase handler.

        Tkinter canvas painting is handled directly by OnPaint, so background
        erasing is intentionally skipped.
        """
        pass

    def OnLeftDown(self, event):
        """
        Handle a left mouse-button press on the toolbar.

        Args:
            event: Tkinter mouse event.
        """
        self._pressed_item = self.FindToolForPosition(event.x, event.y)

    def OnLeftUp(self, event):
        """
        Handle a left mouse-button release.

        Args:
            event: Tkinter mouse event.
        """
        self._pressed_item = None

    def OnRightDown(self, event):
        """
        Handle a right mouse-button press.

        Args:
            event: Tkinter mouse event.
        """
        pass

    def OnRightUp(self, event):
        """
        Handle a right mouse-button release.

        Args:
            event: Tkinter mouse event.
        """
        pass

    def OnMiddleDown(self, event):
        """
        Handle a middle mouse-button press.

        Args:
            event: Tkinter mouse event.
        """
        pass

    def OnMiddleUp(self, event):
        """
        Handle a middle mouse-button release.

        Args:
            event: Tkinter mouse event.
        """
        pass

    def OnMotion(self, event):
        """
        Handle mouse movement within the toolbar.

        Args:
            event: Tkinter mouse motion event.
        """
        self._hover_item = self.FindToolForPosition(event.x, event.y)

    def OnLeaveWindow(self, event):
        """
        Clear hover state when the cursor leaves the toolbar.

        Args:
            event: Tkinter leave event.
        """
        self._hover_item = None

    def OnSetCursor(self, event):
        """
        Hook for cursor handling.

        Currently unimplemented.
        """
        pass

    def OnCustomRender(self, dc, item, rect):
        """
        Hook for custom drawing of a toolbar item.

        Args:
            dc: Rendering context (unused in Tk port).
            item: Toolbar item being rendered.
            rect: Bounding rectangle for the item.
        """
        pass

    def IsPaneMinimized(self):
        """
        Return whether the toolbar is currently minimized as a pane.

        Returns:
            False in the current implementation.
        """
        return False

    def StartPreviewTimer(self):
        """
        Start any preview-timer logic for UI animations.

        This is currently not implemented.
        """
        pass

    def StopPreviewTimer(self):
        """
        Stop any preview-timer logic for UI animations.

        This is currently not implemented.
        """
        pass
