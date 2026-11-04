# -*- coding: utf-8 -*-
"""Composants MDI (Multiple Document Interface) AUI adaptés à Tkinter et ttk.

Ce module implémente une architecture MDI à onglets (Tabbed MDI), calquée sur
le modèle ``wx.aui.AuiMDIParentFrame`` / ``wx.aui.AuiMDIChildFrame`` de wxPython,
en s'appuyant sur les widgets Tkinter (``tk.Toplevel``) et ttk (``ttk.Frame``,
``AuiNotebook``) :

- ``AuiMDIParentFrame`` : Fenêtre de premier niveau (``tk.Toplevel``) servant de
  cadre hôte principal pour l'application MDI. Elle gère la fenêtre cliente, les
  menus et la navigation entre documents.
- ``AuiMDIChildFrame`` : Fenêtre document fille (``ttk.Frame``) intégrée sous
  forme d'onglet dans la fenêtre cliente MDI.
- ``AuiMDIClientWindow`` : Zone cliente centrale dérivée de ``AuiNotebook``,
  hébergeant les différents documents sous forme de pages d'onglets.
"""

import tkinter as tk
from tkinter import ttk

try:
    from .ttkauibook import AuiNotebook
    from .aui_tk_constants import *
except ImportError:
    from ttkauibook import AuiNotebook
    from aui_tk_constants import *


class AuiMDIParentFrame(tk.Toplevel):
    """Fenêtre hôte de premier niveau pour une interface MDI à onglets.

    Représente la fenêtre principale d'une application multi-documents (MDI).
    Elle héberge une fenêtre cliente (``AuiMDIClientWindow``) contenant les
    documents enfants sous forme d'onglets, et fournit les fonctionnalités de
    sélection, navigation cyclique (suivant/précédent), disposition en mosaïque
    et gestion des barres de menus.

    Attributes:
        _art: Fournisseur artistique pour les onglets (compatibilité wx).
        _window_menu: Menu déroulant répertoriant les fenêtres/documents ouverts.
        _active_child (AuiMDIChildFrame | None): Document enfant actuellement actif.
        _menu_bar: Barre de menu principale de la fenêtre parent.
        _child_menu_bar: Barre de menu spécifique au document actif.
        _pClientWindow (AuiMDIClientWindow): Fenêtre cliente hébergeant le carnet d'onglets.
    """

    def __init__(
        self,
        parent=None,
        id=-1,
        title="",
        pos=None,
        size=None,
        style=None,
        name="AuiMDIParentFrame",
    ):
        """Initialise la fenêtre parente MDI.

        Configure le titre de la fenêtre, instancie la zone cliente centrale
        via :meth:`OnCreateClient`, rattache le gestionnaire de fermeture
        de fenêtre, et applique les coordonnées et dimensions géométriques initiales.

        Args:
            parent: Widget parent Tkinter (ou ``None`` pour une fenêtre racine/indépendante).
            id (int, optional): Identifiant numérique de la fenêtre (compatibilité wx).
            title (str, optional): Titre affiché dans la barre de titre de la fenêtre.
            pos (tuple[int, int], optional): Position initiale (x, y) en pixels.
            size (tuple[int, int], optional): Dimensions initiales (largeur, hauteur) en pixels.
            style (optional): Style wx d'origine (ignoré).
            name (str, optional): Nom du composant. Par défaut ``"AuiMDIParentFrame"``.
        """
        super().__init__(parent)
        self.title(title)
        self._art = None
        self._window_menu = None
        self._active_child = None
        self._menu_bar = None
        self._child_menu_bar = None

        # Création de la zone cliente centrale (AuiMDIClientWindow)
        self._pClientWindow = self.OnCreateClient()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Configuration de la géométrie de la fenêtre
        if size and size[0] > 0 and size[1] > 0:
            self.geometry(f"{size[0]}x{size[1]}")
        if pos:
            self.geometry(f"+{pos[0]}+{pos[1]}")

    def Init(self):
        """Méthode d'initialisation post-création (stub de compatibilité wx)."""
        pass

    def SetArtProvider(self, art):
        """Définit le fournisseur artistique et le propage à la fenêtre cliente.

        Args:
            art: Fournisseur artistique d'onglets (TabArt).
        """
        self._art = art
        if hasattr(self._pClientWindow, "SetArtProvider"):
            self._pClientWindow.SetArtProvider(art)

    def GetArtProvider(self):
        """Renvoie le fournisseur artistique actuellement configuré.

        Returns:
            Any: Le fournisseur d'art (ou ``None``).
        """
        return self._art

    def GetNotebook(self):
        """Renvoie le carnet d'onglets hébergeant les documents enfants.

        Returns:
            AuiMDIClientWindow: La fenêtre cliente faisant office de carnet d'onglets.
        """
        return self._pClientWindow

    def SetWindowMenu(self, menu):
        """Définit le menu déroulant affichant la liste des fenêtres ouvertes.

        Args:
            menu: Objet menu Tkinter ou descripteur de menu.
        """
        self._window_menu = menu

    def GetWindowMenu(self):
        """Renvoie le menu déroulant des fenêtres ouvertes.

        Returns:
            Any: Le menu de fenêtres configuré (ou ``None``).
        """
        return self._window_menu

    def SetMenuBar(self, menu):
        """Définit la barre de menu principale de la fenêtre MDI.

        Args:
            menu: Barre de menu à associer.
        """
        self._menu_bar = menu

    def SetChildMenuBar(self, menu):
        """Définit la barre de menu spécifique au document enfant actif.

        Args:
            menu: Barre de menu de l'enfant.
        """
        self._child_menu_bar = menu

    def ProcessEvent(self, event):
        """Traite un événement au niveau du cadre parent (stub de compatibilité wx).

        Args:
            event: Événement à traiter.

        Returns:
            bool: Toujours ``False``.
        """
        return False

    def GetActiveChild(self):
        """Renvoie le document enfant actuellement actif.

        Returns:
            AuiMDIChildFrame | None: L'enfant actif, ou ``None`` si aucun document n'est ouvert.
        """
        return self._active_child

    def SetActiveChild(self, child):
        """Définit et active le document enfant spécifié.

        Args:
            child (AuiMDIChildFrame | None): Le document enfant à activer.
        """
        self._active_child = child
        if child is not None:
            child.Activate()

    def GetClientWindow(self):
        """Renvoie la fenêtre cliente MDI hébergeant les onglets.

        Returns:
            AuiMDIClientWindow: L'instance de la fenêtre cliente.
        """
        return self._pClientWindow

    def OnCreateClient(self):
        """Méthode fabrique instanciant la fenêtre cliente MDI.

        Peut être surchargée pour instancier une classe dérivée personnalisée.

        Returns:
            AuiMDIClientWindow: La nouvelle instance de fenêtre cliente.
        """
        return AuiMDIClientWindow(self)

    def _activate_relative(self, step):
        """Active l'onglet situé à un décalage relatif par rapport à la sélection actuelle.

        Applique un calcul modulo sur le nombre total de pages pour assurer
        un parcours cyclique (de la dernière vers la première, ou inversement).

        Args:
            step (int): Pas de déplacement (+1 pour suivant, -1 pour précédent).

        Returns:
            AuiMDIChildFrame | None: Le document enfant activé, ou ``None`` si vide.
        """
        count = self._pClientWindow.GetPageCount()
        if not count:
            return None
        # Calcul de l'index suivant avec rebouclage cyclique (modulo)
        current = self._pClientWindow.GetSelection()
        index = (current + step) % count
        self._pClientWindow.SetSelection(index)
        page = self._pClientWindow.GetPage(index)
        self.SetActiveChild(page)
        return page

    def ActivateNext(self):
        """Active le document enfant suivant dans l'ordre des onglets.

        Returns:
            AuiMDIChildFrame | None: Le document activé, ou ``None`` si aucun.
        """
        return self._activate_relative(1)

    def ActivatePrevious(self):
        """Active le document enfant précédent dans l'ordre des onglets.

        Returns:
            AuiMDIChildFrame | None: Le document activé, ou ``None`` si aucun.
        """
        return self._activate_relative(-1)

    def RemoveWindowMenu(self):
        """Supprime la référence au menu des fenêtres ouvertes."""
        self._window_menu = None

    def AddWindowMenu(self, window):
        """Ajoute une fenêtre au menu des fenêtres (stub de compatibilité wx).

        Args:
            window: Fenêtre à ajouter.

        Returns:
            Any: La fenêtre passée en paramètre.
        """
        return window

    def DoHandleMenu(self, event):
        """Gère les commandes issues du menu des fenêtres (stub de compatibilité wx).

        Args:
            event: Événement de menu.

        Returns:
            bool: Toujours ``False``.
        """
        return False

    def Tile(self):
        """Dispose l'ensemble des pages enfants en mosaïque côte à côte.

        Positionne chaque page fille sur une rangée unique à l'aide du
        gestionnaire de grille (``grid``).
        """
        count = self._pClientWindow.GetPageCount()
        if not count:
            return
        # Positionnement de chaque document enfant sur une colonne distincte
        for index in range(count):
            page = self._pClientWindow.GetPage(index)
            if hasattr(page, "grid"):
                page.grid(row=0, column=index, sticky="nsew")


class AuiMDIChildFrame(ttk.Frame):
    """Cadre représentant un document enfant dans une interface MDI à onglets.

    Chaque document enfant hérite de ``ttk.Frame`` et s'insère comme page
    au sein de la fenêtre cliente (``AuiMDIClientWindow``) du parent MDI.
    Il encapsule ses propres états d'affichage (titre, icône, maximisation,
    plein écran) ainsi que ses composants locaux (barre d'état, barre d'outils).

    Attributes:
        _parent (AuiMDIParentFrame): Fenêtre parente MDI détenant ce document.
        _title (str): Titre du document affiché sur l'onglet.
        _icons: Liste d'icônes associées au document.
        _icon: Icône principale du document.
        _maximized (bool): Indique si le document est maximisé.
        _iconized (bool): Indique si le document est réduit / minimisé.
        _fullscreen (bool): Indique si le document est en plein écran.
        _activate_on_create (bool): Active automatiquement l'onglet à la création.
        _status_bar (ttk.Label | None): Barre d'état locale du document.
        _tool_bar: Barre d'outils locale du document.
        _menu_bar: Barre de menu associée au document.
        _status_widths (list[int] | None): Largeurs configurées pour la barre d'état.
    """

    def __init__(
        self,
        parent,
        id=-1,
        title="",
        pos=None,
        size=None,
        style=None,
        name="AuiMDIChildFrame",
    ):
        """Initialise le cadre du document enfant MDI.

        Crée le panneau ``ttk.Frame``, l'insère comme nouvelle page d'onglet
        dans la fenêtre cliente du parent MDI, et sélectionne cet onglet comme
        enfant actif.

        Args:
            parent (AuiMDIParentFrame): Fenêtre parente MDI hôte.
            id (int, optional): Identifiant numérique de la fenêtre (compatibilité wx).
            title (str, optional): Titre du document affiché dans l'onglet.
            pos (tuple[int, int], optional): Position géométrique initiale (ignorée).
            size (tuple[int, int], optional): Dimensions initiales (ignorées).
            style (optional): Style d'origine wx (ignoré).
            name (str, optional): Nom du composant. Par défaut ``"AuiMDIChildFrame"``.
        """
        self._parent = parent
        self._title = title
        self._icons = None
        self._icon = None
        self._maximized = False
        self._iconized = False
        self._fullscreen = False
        self._activate_on_create = True
        self._status_bar = None
        self._tool_bar = None

        # Initialisation du frame dans la fenêtre cliente parente
        # super().__init__(parent.GetClientWindow())
        # Comme AuiMDIClientWindow hérite de AuiNotebook (qui encapsule un ttk.Notebook interne), ttkauibook.py:484 exige que le
        # parent direct du widget soit le composant ttk.Notebook (parent.GetClientWindow().GetTabContainer()).
        # Si vous souhaitez faire passer les tests de TestMDI, passer le conteneur d'onglets comme parent lors de
        # l'initialisation de AuiMDIChildFrame permettra de résoudre cette exigence de Tkinter.
        super().__init__(parent.GetClientWindow().GetTabContainer())
        self.pack(fill="both", expand=True)

        # Ajout du cadre comme page d'onglet dans le carnet client et activation
        parent.GetClientWindow().AddPage(self, title, True)
        parent.SetActiveChild(self)

    def Init(self):
        """Initialisation post-création (stub de compatibilité wx)."""
        pass

    def Destroy(self):
        """Détruit le widget enfant (alias wx pour destroy)."""
        self.destroy()

    def SetMenuBar(self, menu):
        """Définit la barre de menu associée à ce document enfant.

        Args:
            menu: Barre de menu locale.
        """
        self._menu_bar = menu

    def GetMenuBar(self):
        """Renvoie la barre de menu associée à ce document enfant.

        Returns:
            Any: La barre de menu configurée (ou ``None``).
        """
        return getattr(self, "_menu_bar", None)

    def SetTitle(self, title):
        """Définit le titre du document.

        Args:
            title (str): Nouveau titre du document.
        """
        self._title = title

    def GetTitle(self):
        """Renvoie le titre actuel du document.

        Returns:
            str: Titre du document.
        """
        return self._title

    def SetIcons(self, icons):
        """Définit la liste d'icônes associées au document.

        Args:
            icons: Liste d'images / icônes.
        """
        self._icons = icons

    def GetIcons(self):
        """Renvoie la liste d'icônes associées au document.

        Returns:
            Any: La liste d'icônes configurée.
        """
        return self._icons

    def SetIcon(self, icon):
        """Définit l'icône principale du document.

        Args:
            icon: Image ou icône principale.
        """
        self._icon = icon

    def GetIcon(self):
        """Renvoie l'icône principale du document.

        Returns:
            Any: L'icône du document (ou ``None``).
        """
        return self._icon

    def Activate(self):
        """Active ce document enfant.

        Fait passer le cadre au premier plan d'empilement, capture le focus
        clavier, synchronise la sélection de l'onglet dans le carnet client
        et enregistre ce cadre comme enfant actif auprès du parent MDI.
        """
        # Remonte le widget au sommet de l'ordre d'affichage et prend le focus
        self.lift()
        self.focus_set()
        # Sélectionne l'onglet correspondant dans le carnet de la fenêtre cliente
        self._parent.GetClientWindow().SetSelectionToWindow(self)
        self._parent._active_child = self

    def OnMenuHighlight(self, event):
        """Gestionnaire de survol d'élément de menu (stub de compatibilité wx).

        Args:
            event: Événement de survol.
        """
        pass

    def OnActivate(self, event):
        """Gestionnaire d'activation du document enfant (stub de compatibilité wx).

        Args:
            event: Événement d'activation.
        """
        pass

    def OnCloseWindow(self, event=None):
        """Gestionnaire de fermeture de la fenêtre document.

        Args:
            event (optional): Événement déclencheur éventuel.
        """
        self.Destroy()

    def SetMDIParentFrame(self, parent):
        """Définit la fenêtre parente MDI hôte.

        Args:
            parent (AuiMDIParentFrame): Fenêtre parente hôte.
        """
        self._parent = parent

    def GetMDIParentFrame(self):
        """Renvoie la fenêtre parente MDI hôte.

        Returns:
            AuiMDIParentFrame: La fenêtre parente hôte.
        """
        return self._parent

    def CreateStatusBar(self, *args, **kwargs):
        """Crée une barre d'état sous forme de composant ttk.Label en bas du cadre.

        Returns:
            ttk.Label: Le widget d'affichage de la barre d'état.
        """
        self._status_bar = ttk.Label(self, text="")
        self._status_bar.pack(side="bottom", fill="x")
        return self._status_bar

    def GetStatusBar(self):
        """Renvoie la barre d'état associée à ce document.

        Returns:
            ttk.Label | None: Le widget barre d'état, ou ``None`` si non créée.
        """
        return self._status_bar

    def SetStatusText(self, text, number=0):
        """Met à jour le texte affiché dans la barre d'état.

        Args:
            text (str): Texte à afficher.
            number (int, optional): Numéro de champ (ignoré). Par défaut 0.
        """
        if self._status_bar is not None:
            self._status_bar.configure(text=text)

    def SetStatusWidths(self, widths):
        """Définit les largeurs des champs de la barre d'état.

        Args:
            widths (list[int]): Liste des largeurs en pixels.
        """
        self._status_widths = widths

    def CreateToolBar(self, *args, **kwargs):
        """Crée une barre d'outils locale pour ce document (non implémenté).

        Returns:
            None
        """
        return None

    def GetToolBar(self):
        """Renvoie la barre d'outils associée à ce document.

        Returns:
            Any: La barre d'outils locale (ou ``None``).
        """
        return self._tool_bar

    def Maximize(self, flag=True):
        """Active ou désactive l'état maximisé du document enfant.

        Args:
            flag (bool, optional): ``True`` pour maximiser. Par défaut ``True``.
        """
        self._maximized = bool(flag)

    def Restore(self):
        """Restaure le document enfant depuis l'état maximisé ou réduit."""
        self._maximized = False
        self._iconized = False

    def Iconize(self, flag=True):
        """Réduit ou restaure l'affichage du document enfant sous forme d'icône.

        Args:
            flag (bool, optional): ``True`` pour réduire. Par défaut ``True``.
        """
        self._iconized = bool(flag)

    def IsMaximized(self):
        """Indique si le document enfant est actuellement maximisé.

        Returns:
            bool: ``True`` si maximisé, ``False`` sinon.
        """
        return self._maximized

    def IsIconized(self):
        """Indique si le document enfant est actuellement réduit en icône.

        Returns:
            bool: ``True`` si réduit, ``False`` sinon.
        """
        return self._iconized

    def ShowFullScreen(self, show, style=0):
        """Bascule la fenêtre principale en mode plein écran.

        Modifie l'attribut ``-fullscreen`` de la fenêtre de premier niveau (``Toplevel``).

        Args:
            show (bool): ``True`` pour activer le plein écran, ``False`` pour le quitter.
            style (int, optional): Style plein écran wx (ignoré). Par défaut 0.

        Returns:
            bool: Toujours ``True``.
        """
        self._fullscreen = bool(show)
        self.winfo_toplevel().attributes("-fullscreen", self._fullscreen)
        return True

    def IsFullScreen(self):
        """Indique si le document est actuellement affiché en plein écran.

        Returns:
            bool: ``True`` si en plein écran, ``False`` sinon.
        """
        return self._fullscreen

    def IsTopLevel(self):
        """Indique si ce cadre est une fenêtre de premier niveau autonome.

        Returns:
            bool: Toujours ``False`` (le cadre est une page d'onglet enfant).
        """
        return False

    def ActivateOnCreate(self, activate=True):
        """Configure si l'enfant doit être automatiquement activé à sa création.

        Args:
            activate (bool, optional): ``True`` pour activer à la création. Par défaut ``True``.
        """
        self._activate_on_create = bool(activate)

    def Show(self, show=True):
        """Affiche ou masque le cadre du document.

        Args:
            show (bool, optional): ``True`` pour afficher via ``pack()``,
                ``False`` pour masquer via ``pack_forget()``. Par défaut ``True``.
        """
        if show:
            self.pack(fill="both", expand=True)
        else:
            self.pack_forget()

    def ApplyMDIChildFrameRect(self, rect):
        """Applique une boîte géométrique absolue au cadre via le gestionnaire place.

        Args:
            rect (tuple[int, int, int, int]): Coordonnées (x, y, largeur, hauteur).
        """
        self.place(x=rect[0], y=rect[1], width=rect[2], height=rect[3])


class AuiMDIClientWindow(AuiNotebook):
    """Zone cliente centrale MDI hébergeant les documents sous forme de carnet d'onglets.

    Dérivée de :class:`AuiNotebook`, cette classe gère l'affichage, la sélection
    et la fermeture des pages d'onglets correspondant aux différents documents
    enfants :class:`AuiMDIChildFrame`.

    Attributes:
        _mdi_parent (AuiMDIParentFrame): Fenêtre hôte parente MDI.
    """

    def __init__(self, parent, agwStyle=0):
        """Initialise la fenêtre cliente MDI avec le style de carnet d'onglets AUI.

        Args:
            parent (AuiMDIParentFrame): Fenêtre parente MDI hôte.
            agwStyle (int, optional): Drapeaux de style additionnels combinés
                avec ``AUI_NB_DEFAULT_STYLE``. Par défaut 0.
        """
        super().__init__(parent, agwStyle=agwStyle | AUI_NB_DEFAULT_STYLE)
        self._mdi_parent = parent

    def SetSelection(self, selection, force=False):
        """Définit la page d'onglet active dans la zone cliente.

        Args:
            selection (int): Index de la page à sélectionner.
            force (bool, optional): Forcer la sélection. Par défaut ``False``.

        Returns:
            int: L'ancien index de sélection, ou -1 en cas d'erreur.
        """
        result = super().SetSelection(selection, force=force)
        return result

    def PageChanged(self, event=None):
        """Méthode de rappel lors d'un changement de page active (stub de notification).

        Args:
            event (optional): Événement de changement de page.
        """
        pass

    def OnPageClose(self, event=None):
        """Gestionnaire de fermeture d'une page d'onglet.

        Returns:
            bool: Toujours ``True`` pour autoriser la fermeture.
        """
        return True

    def OnPageChanged(self, event=None):
        """Gestionnaire d'événement relayant le changement de page active.

        Args:
            event (optional): Événement de changement de page.
        """
        self.PageChanged(event)

    def OnSize(self, event=None):
        """Gestionnaire de redimensionnement de la zone cliente.

        Args:
            event (optional): Événement de redimensionnement.
        """
        super().OnSize(event)
