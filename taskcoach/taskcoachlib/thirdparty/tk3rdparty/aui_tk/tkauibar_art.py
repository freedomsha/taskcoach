# -*- coding: utf-8 -*-
"""Art de barre d'outils AUI adapté à Tkinter, étape 2."""

import tkinter as tk
from tkinter import font as tkfont

try:
    from .aui_tk_constants import *
    from .aui_tk_utilities import StepColour, GetBaseColour, GetLabelSize
except ImportError:
    from aui_tk_constants import *
    from aui_tk_utilities import StepColour, GetBaseColour, GetLabelSize


class AuiDefaultToolBarArt:
    """Art de barre d'outils AUI adapté à Tkinter, étape 2.

    Cet art est utilisé pour afficher les barres d'outils.

    Il utilise des widgets Tkinter pour afficher les éléments de la barre d'outils.

    Par défaut, il utilise le thème par défaut de Tkinter.
    Une classe dérivée peut être utilisée pour personnaliser l'apparence.

    """
    def __init__(self):
        """Initialise l'art de barre d'outils.

        """
        self.SetDefaultColours()
        self._agwFlags = 0
        self._text_orientation = AUI_TBTOOL_TEXT_BOTTOM
        self._separator_size = 7
        self._orientation = AUI_TBTOOL_HORIZONTAL
        self._gripper_size = 7
        self._overflow_size = 16
        self._font = tkfont.Font(family="TkDefaultFont", size=9)
        self._element_sizes = {
            AUI_TBART_SEPARATOR_SIZE: 7,
            AUI_TBART_GRIPPER_SIZE: 7,
            AUI_TBART_OVERFLOW_SIZE: 16,
        }

    def SetDefaultColours(self, base_colour=None):
        """Initialise les couleurs par défaut.

        Elles sont calculées à partir de la couleur de base.
        Ces couleurs sont utilisées pour afficher les éléments de la barre d'outils.

        Args:
            base_colour (str, optional): Couleur de base. Defaults to None.
        """
        self._base_colour = base_colour or GetBaseColour()
        self._gripper_colour1 = StepColour(self._base_colour, 40)
        self._gripper_colour2 = StepColour(self._base_colour, 60)
        self._gripper_colour3 = "#ffffff"

    def Clone(self):
        """Clone l'art de barre d'outils.

        Returns:
            AuiDefaultToolBarArt: Une nouvelle instance de l'art de barre d'outils.
        """
        art = AuiDefaultToolBarArt()
        art._agwFlags = self._agwFlags
        art._orientation = self._orientation
        art._text_orientation = self._text_orientation
        return art

    def SetAGWFlags(self, agwFlags):
        """Règle l'agwFlags.

        Args:
            agwFlags (int) : Les agwFlags.

        ===============================================
        Noms des Flags                 Description
        ===============================================
        AUI_TBART_DEFAULT :       Les agwFlags par défaut.
        AUI_TBART_VARIANT :      Les agwFlags variant.

        """
        self._agwFlags = agwFlags

    def GetAGWFlags(self):
        """Récupère et retourne les agwFlags.

        Returns:
            int: Les agwFlags.
        """
        return self._agwFlags

    def SetFont(self, font):
        """Règle la police.

        Args:
            font (tkfont.Font or str): La police.
        """
        self._font = (
            font
            if isinstance(font, tkfont.Font)
            else tkfont.Font(family="TkDefaultFont", size=9)
        )

    def SetTextOrientation(self, text_orientation):
        """Règle l'orientation du texte.

        Args:
            text_orientation (int) : L'orientation du texte qui peut être l'une des valeurs suivantes:
        =================================== ==================================
        Valeur d'orientation                Description
        =================================== ==================================
        AUI_TBTOOL_TEXT_BOTTOM              Texte en bas
        AUI_TBTOOL_TEXT_TOP                 Texte en haut
        AUI_TBTOOL_TEXT_LEFT                Texte à gauche
        AUI_TBTOOL_TEXT_RIGHT               Texte à droite
        =================================== ==================================
        """
        self._text_orientation = text_orientation

    def GetFont(self):
        """Récupère et retourne la police.

        Returns:
            tkfont.Font: La police.
        """
        return self._font

    def GetTextOrientation(self):
        """Récupère et retourne l'orientation du texte.

        Returns:
            int: L'orientation du texte.
        """
        return self._text_orientation

    def SetOrientation(self, orientation):
        """
        Règle l'orientation de l'outil toolbar.

        Args:
            orientation: une des valeurs : AUI_TBTOOL_HORIZONTAL, AUI_TBTOOL_VERT_CLOCKWISE, AUI_TBTOOL_VERT_COUNTER_CLOCKWISE

        Returns:

        """
        self._orientation = orientation

    def GetOrientation(self):
        """
        Récupère et retourne l'orientation de l'outil toolbar.

        Returns:
            int: L'orientation de l'outil toolbar.
        """
        return self._orientation

    def _xywh(self, r):
        """
        Convertit un rectangle en tuple (x, y, width, height).

        Args:
            r: Rectangle.

        Returns:
            tuple: Un tuple contenant les coordonnées (x, y, width, height).
        """
        return (r.x, r.y, r.width, r.height) if hasattr(r, "x") else tuple(r[:4])

    def DrawBackground(self, dc, wnd, r, horizontal=True):
        """
        Dessine le fond de la barre d'outils avec une couleur de base.

        Args:
            dc: Classe tk.Canvas de contexte dans lequel dessiner.
            wnd: Fenêtre tk.Frame.
            r: Rectangle AuiToolBarItem.
            horizontal: Paramètre True si la toolbar est horizontale, False si elle est verticale.

        Returns:
            None
        """
        self.DrawPlainBackground(dc, wnd, r)

    def DrawPlainBackground(self, dc, wnd, r):
        """
        Dessine l'arrière d'une barre d'outils avec une couleur de base.

        Cette méthode contraste avec la valeur défaut de AuiToolBar qui utilise
        un gradient et cela casse le design de la fenêtre quand on met un
        contrôle avec un margin entre les bords et la toolbar.
        (Par exemple : Mettre AuitToolBar avec une StaticBoxSizer qui a un fond plein.)

        Args:
            dc: Contexte tk.Canvas.
            wnd: Fenêtre dérivée tk.Frame
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        x, y, w, h = self._xywh(r)
        dc.create_rectangle(x, y, x + w, y + h, fill=self._base_colour, outline="")

    def DrawLabel(self, dc, wnd, item, r):
        """
        Dessine une étiquette sur la barre d'outils.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            item: Élément de la barre d'outils AuiToolBarItem.
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        x, y, w, h = self._xywh(r)
        dc.create_text(
            x + w // 2,
            y + h // 2,
            text=item.GetLabel(),
            font=self._font,
            fill="#000000",
        )

    def DrawButton(self, dc, wnd, item, r):
        """
        Dessine un bouton sur la barre d'outils.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            item: Élément de la barre d'outils AuiToolBarItem..
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        x, y, w, h = self._xywh(r)
        fill = "#d0d0d0" if item.IsActive() else self._base_colour
        dc.create_rectangle(x, y, x + w, y + h, fill=fill, outline="#808080")
        self.DrawLabel(dc, wnd, item, r)

    def DrawDropDownButton(self, dc, wnd, item, r):
        """
        Dessine le bouton de Glisser/Déposer sur la barre d'outils.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            item: Élément de la barre d'outils AuiToolBarItem..
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        self.DrawButton(dc, wnd, item, r)
        x, y, w, h = self._xywh(r)
        dc.create_polygon(
            x + w - 10,
            y + h // 2 - 2,
            x + w - 4,
            y + h // 2 - 2,
            x + w - 7,
            y + h // 2 + 3,
            fill="#000000",
        )

    def DrawControlLabel(self, dc, wnd, item, r):
        """
        Dessine une étiquette pour le contrôle de la toolbar.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            item: Élément de la barre d'outils AuiToolBarItem.
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        self.DrawLabel(dc, wnd, item, r)

    def GetLabelSize(self, dc, wnd, item):
        """
        Retourne la taille de l'étiquette pour un élément de la toolbar.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            item: Élément de la barre d'outils AuiToolBarItem.

        Returns:
            Tuple[int, int]: La largeur et la hauteur de l'étiquette.
        """
        return self._font.measure(item.GetLabel()), self._font.metrics("linespace")

    def GetToolSize(self, dc, wnd, item):
        """
        Retourne la taille du bouton de la toolbar.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            item: Élément de la barre d'outils AuiToolBarItem.

        Returns:
            Tuple[int, int]: La largeur et la hauteur du bouton.
        """
        w, h = self.GetLabelSize(dc, wnd, item)
        return max(24, w + 12), max(24, h + 12)

    def DrawSeparator(self, dc, wnd, r):
        """
        Dessine un séparateur sur la barre d'outils.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        x, y, w, h = self._xywh(r)
        (
            dc.create_line(x + w // 2, y + 2, x + w // 2, y + h - 2, fill="#888888")
            if self._orientation == AUI_TBTOOL_HORIZONTAL
            else dc.create_line(
                x + 2, y + h // 2, x + w - 2, y + h // 2, fill="#888888"
            )
        )

    def DrawGripper(self, dc, wnd, r):
        """
        Dessine un gripper sur la barre d'outils.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            r: Rectangle AuiToolBarItem.

        Returns:
            None
        """
        x, y, w, h = self._xywh(r)
        dc.create_rectangle(x, y, x + w, y + h, fill=self._base_colour, outline="")
        for i in range(3):
            dc.create_line(
                x + 3 + i * 3,
                y + 3,
                x + 3 + i * 3,
                y + h - 3,
                fill=self._gripper_colour2,
            )

    def DrawOverflowButton(self, dc, wnd, r, state):
        """
        Dessine un bouton de surcharge sur la barre d'outils.

        Args:
            dc: Contexte tk.Canvas
            wnd: Fenêtre dérivée tk.Frame.
            r: Rectangle AuiToolBarItem.
            state: L'état du bouton.

        Returns:
            None
        """
        x, y, w, h = self._xywh(r)
        dc.create_rectangle(
            x, y, x + w, y + h, fill=self._base_colour, outline="#888888"
        )
        dc.create_text(x + w // 2, y + h // 2, text="⋮", font=self._font)

    def GetElementSize(self, element_id):
        """
        Retourne la taille d'un élément de la toolbar.

        Args:
            element_id (int) : Peut être une des valeurs suivantes :
                - AUI_TBTOOL_SEPARATOR_SIZE : Taille du séparateur.
                - AUI_TBTOOL_GRIPPER_SIZE : Taille du gripper.
                - AUI_TBTOOL_OVERFLOW_BUTTON_SIZE : Taille du bouton de surcharge.

        Returns:
            int: La taille de l'élément.
        """
        return self._element_sizes.get(element_id, 0)

    def SetElementSize(self, element_id, size):
        """
        Règle la taille d'un élément de la toolbar.

        Args:
            element_id (int) : Peut être une des valeurs suivantes :
                - AUI_TBTOOL_SEPARATOR_SIZE : Taille du séparateur.
                - AUI_TBTOOL_GRIPPER_SIZE : Taille du gripper.
                - AUI_TBTOOL_OVERFLOW_BUTTON_SIZE : Taille du bouton de surcharge.
            size: La nouvelle taille de l'élément UI.

        Returns:
            None
        """
        self._element_sizes[element_id] = size

    def ShowDropDown(self, wnd, items):
        """
        Montre un menu déroulant pour l'élément de surcharge de la toolbar.

        Args:
            wnd: Une fenêtre dérivée tk.Frame.
            items: Une liste d'objets AuiToolBarItem.

        Returns:
            None
        """
        return None

    def GetToolsPosition(self, dc, item, r):
        """
        Retourne l'image et le texte des rectangles pour l'élément de surcharge de la toolbar.

        Args:
            dc: Contexte tk.Canvas.
            item: Une instance de AuiToolBarItem.
            r: Le rectangle AuiToolBarItem.

        Returns:
            tuple: Les coordonnées x et y du positionnement des outils.
        """
        return self._xywh(r)[:2]
