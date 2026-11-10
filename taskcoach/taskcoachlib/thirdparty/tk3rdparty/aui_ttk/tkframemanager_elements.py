# -*- coding: utf-8 -*-
"""Première étape de la conversion de framemanager.py vers Tkinter.

Classes converties dans ce bloc : AuiDockInfo, AuiDockingGuideInfo,
AuiDockUIPart, AuiPaneButton, AuiManagerEvent et AuiPaneInfo.
"""

import tkinter as tk
from .aui_tk_constants import *


class AuiDockInfo:
    """Classe pour stocker les informations sur la position
    et la taille d'un panneau dans une fenêtre"""
    def __init__(self):
        self.dock_direction = 0
        self.dock_layer = 0
        self.dock_row = 0
        self.size = 0
        self.min_size = 0
        self.resizable = True
        self.fixed = False
        self.toolbar = False
        self.rect = (0, 0, 0, 0)
        self.panes = []

    def IsOk(self):
        return self.dock_direction != 0

    def IsHorizontal(self):
        return self.dock_direction in (AUI_DOCK_TOP, AUI_DOCK_BOTTOM)

    def IsVertical(self):
        return self.dock_direction in (AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_CENTER)


class AuiDockingGuideInfo:
    """Classe pour stocker les informations sur la direction de la fenêtre.

    Args:
        other (AuiDockingGuideInfo, optional): Autre instance de AuiDockingGuideInfo. Defaults to None.
    """
    def __init__(self, other=None):
        if other:
            self.Assign(other)
        else:
            self.host = None
            self.dock_direction = AUI_DOCK_NONE

    def Assign(self, other):
        """Copie les informations de l'autre instance.

        Args:
            other (AuiDockingGuideInfo): Autre instance de AuiDockingGuideInfo.
        """
        self.host = other.host
        self.dock_direction = other.dock_direction

    def Host(self, h):
        """Définit l'hôte de la fenêtre.

        Args:
            h: Hôte de la fenêtre.
        """
        self.host = h
        return self

    def Left(self):
        """Définit la direction de la fenêtre sur la gauche.

        Returns:
            AuiDockingGuideInfo: Instance de AuiDockingGuideInfo.
        """
        self.dock_direction = AUI_DOCK_LEFT
        return self

    def Right(self):
        """Définit la direction de la fenêtre sur la droite.

        Returns:
            AuiDockingGuideInfo: Instance de AuiDockingGuideInfo.
        """
        self.dock_direction = AUI_DOCK_RIGHT
        return self

    def Top(self):
        """Définit la direction de la fenêtre sur le haut.

        Returns:
            AuiDockingGuideInfo: Instance de AuiDockingGuideInfo.
        """
        self.dock_direction = AUI_DOCK_TOP
        return self

    def Bottom(self):
        """Définit la direction de la fenêtre sur le bas.

        Returns:
            AuiDockingGuideInfo: Instance de AuiDockingGuideInfo.
        """
        self.dock_direction = AUI_DOCK_BOTTOM
        return self

    def Center(self):
        """Définit la direction de la fenêtre sur le centre.

        Returns:
            AuiDockingGuideInfo: Instance de AuiDockingGuideInfo.
        """
        self.dock_direction = AUI_DOCK_CENTER
        return self

    def Centre(self):
        """Définit la direction de la fenêtre sur le centre.

        Returns:
            AuiDockingGuideInfo: Instance de AuiDockingGuideInfo.
        """
        self.dock_direction = AUI_DOCK_CENTRE
        return self


class AuiDockUIPart:
    """Classe pour stocker les informations sur la position
    et la taille d'un panneau d'outils dans une fenêtre"""
    typeCaption = 0
    typeGripper = 1
    typeDock = 2
    typeDockSizer = 3
    typePane = 4
    typePaneSizer = 5
    typeBackground = 6
    typePaneBorder = 7
    typePaneButton = 8

    def __init__(self):
        self.orientation = "vertical"
        self.type = 0
        self.rect = (0, 0, 0, 0)


class AuiPaneButton:
    """Classe pour stocker les informations sur un bouton de panneau"""
    def __init__(self, button_id):
        self.button_id = button_id


class AuiManagerEvent:
    """Classe pour stocker les informations sur un événement de gestionnaire"""
    def __init__(self, manager=None, pane=None, button=None, dc=None):
        self.manager = manager
        self.pane = pane
        self.button = button
        self.dc = dc
        self.veto_flag = False
        self.canveto_flag = True

    def SetManager(self, mgr):
        """La fenêtre de réglage"""
        self.manager = mgr

    def SetDC(self, pdc):
        """Définit le contexte de dessin"""
        self.dc = pdc

    def SetPane(self, p):
        """Définit le panneau"""
        self.pane = p

    def SetButton(self, b):
        """Définit le bouton"""
        self.button = b

    def GetManager(self):
        """Retourne la fenêtre de réglage."""
        return self.manager

    def GetDC(self):
        """Retourne le contexte de dessin."""
        return self.dc

    def GetPane(self):
        """Retourne le panneau de la fenêtre."""
        return self.pane

    def GetButton(self):
        """Retourne le bouton de la fenêtre."""
        return self.button

    def Veto(self, veto=True):
        """Définit si l'événement est veto."""
        self.veto_flag = veto

    def GetVeto(self):
        """Retourne si l'événement est veto."""
        return self.veto_flag

    def SetCanVeto(self, can_veto):
        """Définit si l'événement peut être veto."""
        self.canveto_flag = can_veto

    def CanVeto(self):
        """Retourne si l'événement peut être veto."""
        return self.canveto_flag and self.veto_flag


class AuiPaneInfo:
    """Classe pour stocker les informations sur un panneau.

    Représente la configuration et l'état d'un panneau au sein d'un AuiManager.

    Cette classe est l'équivalent Python de la structure `wx.aui.AuiPaneInfo`
    dans wxPython. Elle stocke les informations de placement, de taille, de
    visibilité, des boutons de commande et de l'état de docking d'un panneau
    dans le gestionnaire de fenêtres AUI.

    Chaque instance décrit un panneau unique : son orientation de dock, sa
    position dans le layout, sa caption, ses dimensions minimales/maximales,
    sa possibilité de flottement, la présence de boutons de fermeture, ainsi
    que ses flags internes de fonctionnement.

    Le modèle suit une logique de "chaînage" (fluent API) : la plupart des
    méthodes renvoient `self`, ce qui permet d'écrire des séquences comme :

        AuiPaneInfo().Name("tree").Caption("Arbre").Left().BestSize(200, 0)

    Attributes:
        window: Widget Tkinter associé au panneau.
        frame: Cadre de gestion du panneau.
        state: Masque de bits contenant les flags d'état du panneau.
        dock_direction: Direction de docking courante.
        dock_layer: Couche de docking.
        dock_row: Rangée de docking.
        dock_pos: Position dans la rangée.
        minimize_mode: Mode de miniaturisation.
        floating_pos: Position du panneau flottant.
        floating_size: Taille du panneau flottant.
        best_size: Taille préférée du panneau.
        min_size: Taille minimale autorisée.
        max_size: Taille maximale autorisée.
        dock_proportion: Proportion utilisée lors du redimensionnement.
        caption: Texte de la caption.
        buttons: Liste des boutons activés sur le panneau.
        name: Nom logique du panneau.
        icon: Icône associée.
        rect: Rectangle de placement du panneau.
        notebook_id: Identifiant du notebook parent si le panneau est un onglet.
        transparent: Niveau de transparence.
        needsTransparency: Indique si une transparence doit être appliquée.
        previousDockPos: Ancienne position de dock.
        previousDockSize: Ancienne taille de dock.
        snapped: État d'accrochage du panneau.
        minimize_target: Cible de minimisation.
    """
    # Flags de comportement du panneau
    optionFloating = 2**0
    optionHidden = 2**1
    optionLeftDockable = 2**2
    optionRightDockable = 2**3
    optionTopDockable = 2**4
    optionBottomDockable = 2**5
    optionFloatable = 2**6
    optionMovable = 2**7
    optionResizable = 2**8
    optionPaneBorder = 2**9
    optionCaption = 2**10
    optionGripper = 2**11
    optionDestroyOnClose = 2**12
    optionToolbar = 2**13
    optionActive = 2**14
    optionGripperTop = 2**15
    optionMaximized = 2**16
    optionDockFixed = 2**17
    optionNotebookDockable = 2**18
    optionMinimized = 2**19
    optionLeftSnapped = 2**20
    optionRightSnapped = 2**21
    optionTopSnapped = 2**22
    optionBottomSnapped = 2**23
    optionFlyOut = 2**24
    optionCaptionLeft = 2**25

    # Flags des boutons du panneau
    buttonClose = 2**26
    buttonMaximize = 2**27
    buttonMinimize = 2**28
    buttonPin = 2**29
    buttonCustom1 = 2**30
    buttonCustom2 = 2**31
    buttonCustom3 = 2**32

    savedHiddenState = 2**33
    actionPane = 2**34
    wasMaximized = 2**35
    needsRestore = 2**36

    def __init__(self):
        """
        Initialise un objet AuiPaneInfo avec des valeurs par défaut.
        """
        self.window = None
        self.frame = None
        self.state = 0
        self.dock_direction = AUI_DOCK_LEFT  # Default dock direction, position par défaut du nouveau panneau
        self.dock_layer = 0
        self.dock_row = 0
        self.dock_pos = 0
        self.minimize_mode = AUI_MINIMIZE_POS_SMART
        self.floating_pos = (-1, -1)
        self.floating_size = (-1, -1)
        self.best_size = (-1, -1)
        self.min_size = (-1, -1)
        self.max_size = (-1, -1)
        self.dock_proportion = 0
        self.caption = ""
        self.buttons = []
        self.name = ""
        self.icon = None
        self.rect = (0, 0, 0, 0)
        self.notebook_id = -1
        self.transparent = 255
        self.needsTransparency = False
        self.previousDockPos = None
        self.previousDockSize = 0
        self.snapped = 0
        self.minimize_target = None
        self.DefaultPane()

    @property
    def dock_dir(self):
        """
        Alias de la propriété de direction de docking.

        Returns:
            Direction actuelle du dock du panneau.
        """
        return self.dock_direction

    @dock_dir.setter
    def dock_dir(self, v):
        """
        Définit la direction de docking du panneau.

        Args:
            v: Nouvelle direction de docking.
        """
        self.dock_direction = v

    def IsOk(self):
        """
        Vérifie si le panneau est associé à une fenêtre valide.

        Returns:
            True si une fenêtre est attachée au panneau, False sinon.
        """
        return self.window is not None

    def IsMaximized(self):
        """
        Indique si le panneau est maximisé.

        Returns:
            True si le flag de maximisation est activé.
        """
        return self.HasFlag(self.optionMaximized)

    def IsMinimized(self):
        """
        Indique si le panneau est minimisé.

        Returns:
            True si le flag de minimisation est activé.
        """
        return self.HasFlag(self.optionMinimized)

    def IsFixed(self):
        """
        Indique si le panneau est fixé / non redimensionnable par la grille.


        Returns:
            True si le flag de fixation est activé.
        """
        return self.HasFlag(self.optionDockFixed)

    def IsResizeable(self):
        """
        Indique si le panneau est redimensionnable.

        Returns:
            True si le flag de redimensionnement est activé.
        """
        return self.HasFlag(self.optionResizable)

    def IsShown(self):
        """
        Indique si le panneau est affiché/visible.

        Returns:
            True si le flag d'affichage est activé.
        """
        return not self.HasFlag(self.optionHidden)

    def IsFloating(self):
        """
        Vérifie si le panneau est actuellement flottant.

        Returns:
            True si le panneau est flottant.
        """
        return self.HasFlag(self.optionFloating)

    def IsDocked(self):
        """
        Vérifie si le panneau est ancré dans le layout.

        Returns:
            True si le panneau n'est pas flottant.
        """
        return not self.IsFloating()

    def IsToolbar(self):
        """
        Détermine si le panneau est un outil de type toolbar.

        Returns:
            True si le flag `optionToolbar` est activé.
        """
        return self.HasFlag(self.optionToolbar)

    def IsTopDockable(self):
        """
        Vérifie si le panneau peut être docké en haut.

        Returns:
            True si le docking sur le haut est autorisé.
        """
        return self.HasFlag(self.optionTopDockable)

    def IsBottomDockable(self):
        """
        Vérifie si le panneau peut être docké en bas.

        Returns:
            True si le docking sur le bas est autorisé.
        """
        return self.HasFlag(self.optionBottomDockable)

    def IsLeftDockable(self):
        """
        Vérifie si le panneau peut être docké à gauche.

        Returns:
            True si le docking sur la gauche est autorisé.
        """
        return self.HasFlag(self.optionLeftDockable)

    def IsRightDockable(self):
        """
        Vérifie si le panneau peut être docké à droite.

        Returns:
            True si le docking sur la droite est autorisé.
        """
        return self.HasFlag(self.optionRightDockable)

    def IsDockable(self):
        """
        Vérifie si le panneau peut être docké.

        Returns:
            True si le panneau peut être docké.
        """
        return (
            self.IsTopDockable()
            or self.IsBottomDockable()
            or self.IsLeftDockable()
            or self.IsRightDockable()
        )

    def IsFloatable(self):
        """
        Vérifie si le panneau peut être flottant.

        Returns:
            True si le panneau peut être flottant.
        """
        return self.HasFlag(self.optionFloatable)

    def IsMovable(self):
        """
        Vérifie si le panneau peut être déplacé.

        Returns:
            True si le panneau peut être déplacé.
        """
        return self.HasFlag(self.optionMovable)

    def IsDestroyOnClose(self):
        """
        Vérifie si le panneau doit être détruit lors de sa fermeture.

        Returns:
            True si le panneau doit être détruit lors de sa fermeture.
        """
        return self.HasFlag(self.optionDestroyOnClose)

    def IsNotebookDockable(self):
        """
        Vérifie si le panneau peut être docké dans un notebook.

        Returns:
            True si le panneau peut être docké dans un notebook.
        """
        return self.HasFlag(self.optionNotebookDockable)

    def IsTopSnappable(self):
        """
        Vérifie si le panneau peut être accolé en haut.

        Returns:
            True si le panneau peut être accolé en haut.
        """
        return self.HasFlag(self.optionTopSnapped)

    def IsBottomSnappable(self):
        """
        Vérifie si le panneau peut être accolé en bas.

        Returns:
            True si le panneau peut être accolé en bas.
        """
        return self.HasFlag(self.optionBottomSnapped)

    def IsLeftSnappable(self):
        """
        Vérifie si le panneau peut être accolé à gauche.

        Returns:
            True si le panneau peut être accolé à gauche.
        """
        return self.HasFlag(self.optionLeftSnapped)

    def IsRightSnappable(self):
        """
        Vérifie si le panneau peut être accolé à droite.

        Returns:
            True si le panneau peut être accolé à droite.
        """
        return self.HasFlag(self.optionRightSnapped)

    def IsSnappable(self):
        """
        Vérifie si le panneau peut s'accrocher sur un côté.

        Returns:
            True si le panneau supporte au moins un accrochage.
        """
        return (
                self.IsTopSnappable()
                or self.IsBottomSnappable()
                or self.IsLeftSnappable()
                or self.IsRightSnappable()
        )

    def IsFlyOut(self):
        """
        Vérifie si le panneau est en mode fly-out.

        Returns:
            True si le panneau est un panneau envoûté / popup.
        """
        return self.HasFlag(self.optionFlyOut)

    def HasCaption(self):
        """
        Vérifie si le panneau affiche une caption.

        Returns:
            True si la caption est visible.
        """
        return self.HasFlag(self.optionCaption)

    def HasCaptionLeft(self):
        """
        Vérifie si la caption est affichée sur la gauche.

        Returns:
            True si la caption est orientée à gauche.
        """
        return self.HasFlag(self.optionCaptionLeft)

    def HasGripper(self):
        """
        Vérifie si le panneau affiche un grip de déplacement.

        Returns:
            True si le grip est activé.
        """
        return self.HasFlag(self.optionGripper)

    def HasBorder(self):
        """
        Vérifie si le panneau a une bordure visible.

        Returns:
            True si la bordure est activée.
        """
        return self.HasFlag(self.optionPaneBorder)

    def HasCloseButton(self):
        """
        Vérifie si le boutton de fermeture est affiché.

        Returns:
            True si le bouton de fermeture est présent.
        """
        return self.HasFlag(self.buttonClose)

    def HasMaximizeButton(self):
        """
        Vérifie si le bouton de maximisation est affiché.

        Returns:
            True si le bouton de maximisation est activé.
        """
        return self.HasFlag(self.buttonMaximize)

    def HasMinimizeButton(self):
        """
        Vérifie si le bouton de minimisation est affiché.

        Returns:
            True si le bouton de minimisation est activé.
        """
        return self.HasFlag(self.buttonMinimize)

    def GetMinimizeMode(self):
        """
        Retourne le mode de minimisation du panneau.

        Returns:
            Mode de minimisation actuel.
        """
        return self.minimize_mode

    def HasPinButton(self):
        """
        Vérifie si le bouton d'épinglage est affiché.

        Returns:
            True si le bouton pin est présent.
        """
        return self.HasFlag(self.buttonPin)

    def HasGripperTop(self):
        """
        Vérifie si le grip est placé en haut du panneau.

        Returns:
            True si le grip est en haut.
        """
        return self.HasFlag(self.optionGripperTop)

    def Window(self, w):
        """
        Associe une fenêtre Tkinter au panneau.

        Args:
            w: Fenêtre Tkinter ou widget associé.

        Returns:
            self: pour le chaînage.
        """
        self.window = w
        return self

    def Name(self, n):
        """
        Définit le nom logique du panneau.

        Args:
            n: Nom du panneau.

        Returns:
            self: pour le chaînage.
        """
        self.name = n
        return self

    def Caption(self, c):
        """
        Définit le texte de la légende du panneau.

        Args:
            c: Texte de la légende.

        Returns:
            self: pour le chaînage.
        """
        self.caption = c
        return self

    def Left(self):
        """
        Fixe la direction de dock sur la gauche.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = AUI_DOCK_LEFT
        return self

    def Right(self):
        """
        Fixe la direction de dock sur la droite.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = AUI_DOCK_RIGHT
        return self

    def Top(self):
        """
        Fixe la direction de dock sur le haut.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = AUI_DOCK_TOP
        return self

    def Bottom(self):
        """
        Fixe la direction de dock sur le bas.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = AUI_DOCK_BOTTOM
        return self

    def Center(self):
        """
        Fixe la direction de dock au centre.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = AUI_DOCK_CENTER
        return self

    def Centre(self):
        """
        Alias Anglais/Britannique de `Center`.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = AUI_DOCK_CENTRE
        return self

    def Direction(self, direction):
        """
        Définit et retourne la direction.

        Elle peut être AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_TOP,
        AUI_DOCK_BOTTOM ou AUI_DOCK_CENTER ou AUI_DOCK_CENTRE.

        Args:
            direction: Direction choisit. Une des constantes AUI_DOCK_LEFT,
                AUI_DOCK_RIGHT, AUI_DOCK_TOP, AUI_DOCK_BOTTOM, AUI_DOCK_CENTER
                ou AUI_DOCK_CENTRE.


        Returns:
            self: Instance de la classe pour le chaînage.
        """
        self.dock_direction = direction
        return self

    def Layer(self, layer):
        """
        Définit la couche de docking du panneau.

        Args:
            layer: Index de la couche.

        Returns:
            self: pour le chaînage.
        """
        self.dock_layer = layer
        return self

    def Row(self, row):
        """
        Définit la rangée de docking du panneau.

        Args:
            row: Numéro de rangée.

        Returns:
            self: pour le chaînage.
        """
        self.dock_row = row
        return self

    def Position(self, pos):
        """
        Définit la position du panneau dans la rangée.

        Args:
            pos: Position dans la rangée.

        Returns:
            self: pour le chaînage.
        """
        self.dock_pos = pos
        return self

    def MinSize(self, *args):
        """
        Définit la taille minimale du panneau.

        Args:
            *args: Largeur et hauteur minimales.

        Returns:
            self: pour le chaînage.
        """
        self.min_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def MinSize1(self, w):
        """
        Définit la taille minimale du panneau sur la largeur.

        Args:
            w: Largeur minimale.

        Returns:
            self: pour le chaînage.
        """
        self.min_size = (w, -1)
        return self

    def MinSize2(self, h):
        """
        Définit la taille minimale du panneau sur la hauteur.

        Args:
            h: Hauteur minimale.

        Returns:
            self: pour le chaînage.
        """
        self.min_size = (-1, h)
        return self

    def MaxSize(self, *args):
        """
        Définit la taille maximale du panneau.

        Args:
            *args: Largeur et hauteur maximales.

        Returns:
            self: pour le chaînage.
        """
        self.max_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def MaxSize1(self, w):
        """
        Définit la taille maximale du panneau sur la largeur.

        Args:
            w: Largeur maximale.

        Returns:
            self: pour le chaînage.
        """
        self.max_size = (w, -1)
        return self

    def MaxSize2(self, h):
        """
        Définit la taille maximale du panneau sur la hauteur.

        Args:
            h: Hauteur maximale.

        Returns:
            self: pour le chaînage.
        """
        self.max_size = (-1, h)
        return self

    def BestSize(self, *args):
        """
        Définit la taille optimale du panneau.

        Args:
            *args: Largeur et hauteur optimales.

        Returns:
            self: pour le chaînage.
        """
        self.best_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def BestSize1(self, w):
        """
        Définit la taille optimale du panneau sur la largeur.

        Args:
            w: Largeur optimale.

        Returns:
            self: pour le chaînage.
        """
        self.best_size = (w, -1)
        return self

    def BestSize2(self, h):
        """
        Définit la taille optimale du panneau sur la hauteur.

        Args:
            h: Hauteur optimale.

        Returns:
            self: pour le chaînage.
        """
        self.best_size = (-1, h)
        return self

    def FloatingPosition(self, *args):
        """
        Définit la position du panneau lorsqu'il est flottant.

        Args:
            *args: Soit un tuple (x, y), soit un unique objet ayant la position.

        Returns:
            self: pour le chaînage.
        """
        self.floating_pos = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def FloatingSize(self, *args):
        """
        Définit la taille du panneau lorsqu'il est flottant.

        Args:
            *args: Soit un tuple (w, h), soit une valeur unique.

        Returns:
            self: pour le chaînage.
        """
        self.floating_size = args[0] if len(args) == 1 else (args[0], args[1])
        return self

    def Maximize(self):
        """
        Active le flag de maximisation du panneau.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionMaximized, True)

    def Minimize(self):
        """
        Active le flag de minimisation du panneau.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionMinimized, True)

    def MinimizeMode(self, mode):
        """
        Définit le mode de minimisation du panneau.

        Args:
            mode: Mode de minimisation selon les constantes AUI_MINIMIZE_POS_*.

        Returns:
            self: pour le chaînage.
        """
        self.minimize_mode = mode
        return self

    def MinimizeTarget(self, target):
        """
        Définit la cible de minimisation du panneau.

        Args:
            target: Widget ou cible de minimisation.

        Returns:
            self: pour le chaînage.
        """
        self.minimize_target = target
        return self

    def Restore(self):
        """
        Restaure le panneau depuis un état de minimisation ou de maximisation.

        Returns:
            self: pour le chaînage.
        """
        self.SetFlag(self.optionMinimized, False)
        return self.SetFlag(self.optionMaximized, False)

    def Fixed(self):
        """
        Rend le panneau fixe, c'est-à-dire non redimensionnable et figé au dock.

        Returns:
            self: pour le chaînage.
        """
        self.SetFlag(self.optionResizable, False)
        return self.SetFlag(self.optionDockFixed, True)

    def Resizable(self, resize=True):
        """
        Active ou désactive la redimensionnabilité du panneau.

        Args:
            resize: True pour autoriser le redimensionnement, False pour le bloquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionResizable, resize)

    def Transparent(self, alpha=255):
        """
        Règle la transparence du panneau.

        Args:
            alpha: Niveau de transparence compris entre 0 et 255.

        Returns:
            self: pour le chaînage.
        """
        self.transparent = alpha
        self.needsTransparency = True
        return self

    def Dock(self):
        """
        Force le panneau à être docké.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionFloating, False)

    def Float(self):
        """
        Force le panneau à devenir flottant.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionFloating, True)

    def Hide(self):
        """
        Cache le panneau.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionHidden, True)

    def Show(self, show=True):
        """
        Affiche ou cache le panneau.

        Args:
            show: True pour afficher, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionHidden, not show)

    def NotebookPage(self, page=-1):
        """
        Associe le panneau à un numéro de page de notebook.

        Args:
            page: Index de la page.

        Returns:
            self: pour le chaînage.
        """
        self.notebook_id = page
        return self

    def NotebookControl(self, ctrl):
        """
        Associe un contrôle de notebook au panneau.

        Args:
            ctrl: Contrôle notebook.

        Returns:
            self: pour le chaînage.
        """
        self.notebook_control = ctrl
        return self

    def HasNotebook(self):
        """
        Vérifie si le panneau est lié à un notebook.

        Returns:
            True si le panneau appartient à un notebook.
        """
        return getattr(self, "notebook_id", -1) >= 0

    def IsNotebookPage(self):
        """
        Vérifie si le panneau est une page de notebook.

        Returns:
            True si le panneau correspond à une page de notebook.
        """
        return self.HasNotebook()

    def IsNotebookControl(self):
        """
        Vérifie si le panneau contient un contrôle de notebook.

        Returns:
            True si un contrôle notebook est associé.
        """
        return getattr(self, "notebook_control", None) is not None

    def SetNameFromNotebookId(self, idx):
        """
        Génère un nom de panneau basé sur l'identifiant du notebook.

        Args:
            idx: Indice de la page.

        Returns:
            self: pour le chaînage.
        """
        self.name = f"notebook_page_{idx}"
        return self

    def CaptionVisible(self, visible=True):
        """
        Rend le titre du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionCaption, visible)

    def PaneBorder(self, visible=True):
        """
        Rend la bordure du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionPaneBorder, visible)

    def Gripper(self, visible=True):
        """
        Rend le poignée du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionGripper, visible)

    def GripperTop(self, visible=True):
        """
        Rend la poignée du panneau en haut visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionGripperTop, visible)

    def CloseButton(self, visible=True):
        """
        Rend le bouton de fermeture du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.buttonClose, visible)

    def MaximizeButton(self, visible=True):
        """
        Rend le bouton de maximisation du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.buttonMaximize, visible)

    def MinimizeButton(self, visible=True):
        """
        Rend le bouton de minimisation du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.buttonMinimize, visible)

    def PinButton(self, visible=True):
        """
        Rend le bouton d'épinglage du panneau visible ou non.

        Args:
            visible: True pour rendre visible, False pour masquer.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.buttonPin, visible)

    def DestroyOnClose(self, b=True):
        """
        Définit si le panneau doit être détruit lors de sa fermeture.

        Args:
            b: True pour détruire le panneau, False sinon.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionDestroyOnClose, b)

    def TopDockable(self, b=True):
        """
        Autorise ou interdit le docking sur le haut.

        Args:
            b: True pour autoriser le docking en haut.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionTopDockable, b)

    def BottomDockable(self, b=True):
        """
        Autorise ou interdit le docking sur le bas.

        Args:
            b: True pour autoriser le docking en bas.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionBottomDockable, b)


    def LeftDockable(self, b=True):
        """
        Autorise ou interdit le docking sur la gauche.

        Args:
            b: True pour autoriser le docking à gauche.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionLeftDockable, b)

    def RightDockable(self, b=True):
        """
        Autorise ou interdit le docking sur la droite.

        Args:
            b: True pour autoriser le docking à droite.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionRightDockable, b)

    def Floatable(self, b=True):
        """
        Autorise ou interdit la mise à flot.

        Args:
            b: True pour autoriser le flottement.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionFloatable, b)

    def Movable(self, b=True):
        """
        Autorise ou interdit le déplacement du panneau.

        Args:
            b: True pour autoriser le déplacement.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionMovable, b)

    def NotebookDockable(self, b=True):
        """
        Autorise ou interdit le docking du panneau dans un notebook.

        Args:
            b: True pour autoriser l'intégration dans un notebook.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionNotebookDockable, b)

    def DockFixed(self):
        """
        Rend le panneau fixé au dock.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionDockFixed, True)

    def Dockable(self, b=True):
        """
        Active ou désactive le docking sur les quatre côtés.

        Args:
            b: True pour activer le docking sur les quatre côtés.

        Returns:
            self: pour le chaînage.
        """
        self.TopDockable(b)
        self.BottomDockable(b)
        self.LeftDockable(b)
        return self.RightDockable(b)

    def TopSnappable(self, b=True):
        """
        Active ou désactive l'accrochage du panneau au haut.

        Args:
            b: True pour autoriser l'accrochage en haut.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionTopSnapped, b)

    def BottomSnappable(self, b=True):
        """
        Active ou désactive l'accrochage du panneau au bas.

        Args:
            b: True pour autoriser l'accrochage en bas.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionBottomSnapped, b)

    def LeftSnappable(self, b=True):
        """
        Active ou désactive l'accrochage du panneau à gauche.

        Args:
            b: True pour autoriser l'accrochage à gauche.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionLeftSnapped, b)

    def RightSnappable(self, b=True):
        """
        Active ou désactive l'accrochage du panneau à droite.

        Args:
            b: True pour autoriser l'accrochage à droite.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionRightSnapped, b)

    def Snappable(self, b=True):
        """
        Active ou désactive l'accrochage du panneau sur les quatre côtés.

        Args:
            b: True pour autoriser l'accrochage sur les quatre côtés.

        Returns:
            self: pour le chaînage.
        """
        self.TopSnappable(b)
        self.BottomSnappable(b)
        self.LeftSnappable(b)
        return self.RightSnappable(b)

    def FlyOut(self, b=True):
        """
        Active ou désactive le vol d'entrée du panneau.

        Args:
            b: True pour autoriser le vol d'entrée.

        Returns:
            self: pour le chaînage.
        """
        return self.SetFlag(self.optionFlyOut, b)

    def SetDockPos(self, direction, layer=0, row=0, pos=0):
        """
        Détermine la position précise du panneau dans le système de docking.

        Args:
            direction: Direction de docking.
            layer: Couche de docking.
            row: Rangée.
            pos: Position dans la rangée.

        Returns:
            self: pour le chaînage.
        """
        self.dock_direction = direction
        self.dock_layer = layer
        self.dock_row = row
        self.dock_pos = pos
        return self

    def DefaultPane(self):
        """
        Restaure les valeurs par défaut d'un panneau standard.

        Un panneau standard est :
        - docké,
        - avec caption visible,
        - avec bordure,
        - déplaçable,
        - dockable sur les quatre côtés.

        Returns:
            self: pour le chaînage.
        """
        self.state = 0
        # self.Dock().CaptionVisible().PaneBorder().Movable()
        # self.TopDockable().BottomDockable().LeftDockable().RightDockable()
        self.Dock()
        self.CaptionVisible()
        self.PaneBorder()
        self.Movable()
        self.TopDockable()
        self.BottomDockable()
        self.LeftDockable()
        self.RightDockable()
        return self

    def CentrePane(self):
        """
        Alias de `CenterPane`.

        Returns:
            self: pour le chaînage.
        """
        return self.CenterPane()

    def CenterPane(self):
        """
        Configure un panneau centré dans le layout, typiquement pour un contenu principal.

        Returns:
            self: pour le chaînage.
        """
        self.state = 0
        self.Dock()
        self.Center()
        self.Resizable()
        self.Floatable()
        self.Movable()
        return self

    def ToolbarPane(self):
        """
        Configure un panneau de type toolbar.

        Returns:
            self: pour le chaînage.
        """
        self.state = 0
        self.DefaultPane()
        self.Dock()
        self.Gripper()
        return self

    def Icon(self, icon):
        """
        Associe une icône au panneau.

        Args:
            icon: Icône à associer.

        Returns:
            self: pour le chaînage.
        """
        self.icon = icon
        return self

    def SetFlag(self, flag, option=True):
        """
        Active ou désactive un flag dans le masque d'état du panneau.

        Args:
            flag: Bit à modifier.
            option: True pour activer, False pour désactiver.

        Returns:
            self: pour le chaînage.
        """
        if option:
            self.state |= flag
        else:
            self.state &= ~flag
        return self

    def HasFlag(self, flag):
        """
        Vérifie si un flag spécifique est présent dans l'état du panneau.

        Args:
            flag: Bit à tester.

        Returns:
            True si le bit est activé.
        """
        return (self.state & flag) == flag

    def ResetButtons(self):
        """
        Réinitialise les boutons de commande du panneau.

        Returns:
            self: pour le chaînage.
        """
        mask = (
                self.buttonClose
                | self.buttonMaximize
                | self.buttonMinimize
                | self.buttonPin
                | self.buttonCustom1
                | self.buttonCustom2
                | self.buttonCustom3
        )
        self.state &= ~mask
        return self

    def CountButtons(self):
        """
        Compte le nombre de boutons actifs sur le panneau.

        Returns:
            Nombre de boutons activés.
        """
        return sum(
            self.HasFlag(f)
            for f in (
                self.buttonClose,
                self.buttonMaximize,
                self.buttonMinimize,
                self.buttonPin,
                self.buttonCustom1,
                self.buttonCustom2,
                self.buttonCustom3,
            )
        )

    def IsHorizontal(self):
        """
        Vérifie si le panneau est orienté horizontalement.

        Returns:
            True si la direction est haut ou bas.
        """
        return self.dock_direction in (AUI_DOCK_TOP, AUI_DOCK_BOTTOM)

    def IsVertical(self):
        """
        Vérifie si le panneau est orienté verticalement.

        Returns:
            True si la direction est gauche, droite ou centre.
        """
        return self.dock_direction in (AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_CENTER)
