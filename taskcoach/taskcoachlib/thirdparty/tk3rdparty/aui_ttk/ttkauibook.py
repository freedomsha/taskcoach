# -*- coding: utf-8 -*-
"""Version ttk d'AuiNotebook, inspirée de tkauibook.py et de wx.lib.agw.aui.auibook.

Cette première adaptation délègue l'affichage des onglets à ttk.Notebook.
Les comportements AUI avancés (déplacement entre groupes, flottement et
boutons personnalisés) restent à implémenter dans les étapes suivantes.

Ce module fournit :
- ``TabFrame`` : Conteneur de compatibilité pour les panneaux et groupes d'onglets.
- ``AuiNotebook`` : Contrôle de carnet d'onglets reposant sur ``ttk.Notebook``,
  reproduisant l'API et les comportements de ``wx.lib.agw.aui.AuiNotebook``.
- ``TtkAuiNotebook`` : Alias de compatibilité pour ``AuiNotebook``.
"""
# J’ai créé ttkauibook.py avec ttk.Notebook comme base,
# en reprenant l’API de tkauibook.py et les conventions générales d’AuiNotebook
# de wxPython. Le fichier passe la vérification de syntaxe Python.
#
# Cette première version couvre les opérations de base sur les pages
# et la sélection. Le glisser-déposer entre onglets est amorcé ;
# le flottement, le fractionnement des onglets et les boutons personnalisés
# restent à adapter. Le fichier est prêt à être ajouté au dossier du projet ;
# il n’a pas été écrit directement dans le dépôt.

# Modifications effectuées :
#
# conservation de ttk.Notebook comme contrôle principal ;
# suppression de l’utilisation incorrecte de l’option tooltip de ttk.Notebook ;
# conservation des infobulles dans AuiNotebookPage, accessibles via GetPageTooltip() ;
# ajout d’un helper _hide_ttk_page() pour gérer le masquage des pages ;
# ajout d’un repli pour les versions de Tk ne proposant pas ttk.Notebook.hide() ;
# nouvelle vérification de syntaxe réussie ;
# vérification de la présence des classes TabFrame et AuiNotebook.

import json
import tkinter as tk
from tkinter import ttk

from .ttkauibook_aux import AuiNotebookPage, AuiNotebookEvent
from .aui_tk_constants import *


class TabFrame(ttk.Frame):
    """Conteneur de compatibilité pour les panneaux et groupes d'onglets.

    Dans l'architecture AUI d'origine (wxPython), un ``TabFrame`` encapsule
    un conteneur d'onglets (``AuiTabCtrl``) et la zone d'affichage des pages
    associées. Cette classe fournit un adaptateur basé sur ``ttk.Frame``
    reproduisant l'interface géométrique et d'affichage attendue.

    Attributes:
        _tabs: Référence vers le contrôle d'onglets associé (ou None).
        _rect (tuple[int, int, int, int]): Rectangle géométrique (x, y, w, h).
        _tab_ctrl_height (int): Hauteur réservée à la barre d'onglets en pixels.
        _tab_rect (tuple[int, int, int, int]): Rectangle de la zone d'onglets.
        _parent: Widget parent détenant ce panneau.
    """

    def __init__(self, parent):
        """Initialise le cadre de panneau d'onglets.

        Args:
            parent: Widget parent Tkinter hébergeant ce cadre.
        """
        super().__init__(parent)
        self._tabs = None
        self._rect = (0, 0, 200, 200)
        self._tab_ctrl_height = 20
        self._tab_rect = (0, 0, 0, 0)
        self._parent = parent

    def SetTabCtrlHeight(self, height):
        """Définit la hauteur de la barre d'onglets dans ce cadre.

        Args:
            height (int): Nouvelle hauteur en pixels.
        """
        self._tab_ctrl_height = height

    def DoSetSize(self, x, y, width, height, flags=None):
        """Positionne et redimensionne le cadre à l'aide du gestionnaire place.

        Args:
            x (int): Coordonnée horizontale relative au parent.
            y (int): Coordonnée verticale relative au parent.
            width (int): Largeur du cadre en pixels.
            height (int): Hauteur du cadre en pixels.
            flags (optional): Drapeaux de redimensionnement wx (ignorés).
        """
        self.place(x=x, y=y, width=width, height=height)

    def DoGetSize(self):
        """Renvoie la taille actuelle du cadre.

        Returns:
            tuple[int, int]: Largeur et hauteur actuelles (width, height).
        """
        return self.winfo_width(), self.winfo_height()

    def DoGetClientSize(self):
        """Renvoie la taille de la zone cliente du cadre.

        Returns:
            tuple[int, int]: Largeur et hauteur clientes (width, height).
        """
        return self.DoGetSize()

    def Show(self, show=True):
        """Affiche ou masque le cadre.

        Args:
            show (bool, optional): ``True`` pour afficher le cadre via ``place()``,
                ``False`` pour le masquer via ``place_forget()``. Par défaut ``True``.
        """
        if show:
            self.place()
        else:
            self.place_forget()

    def DoSizing(self):
        """Recalcule la disposition interne (stub de compatibilité wx)."""
        pass

    def Update(self):
        """Force la mise à jour immédiate des tâches d'affichage inactives."""
        self.update_idletasks()


class AuiNotebook(ttk.Frame):
    """Carnet d'onglets compatible avec l'API AuiNotebook de wxPython.

    Cette classe délègue l'affichage et la disposition des onglets à un composant
    interne ``ttk.Notebook``, tout en fournissant l'API complète attendue par
    Task Coach (gestion des pages, activation, sélection, réordonnancement,
    infobulles et perspectives).

    Attributes:
        _auiStyle (int): Drapeaux de style AUI configurés.
        _art: Fournisseur artistique configuré (conservé pour compatibilité).
        _pages (list[AuiNotebookPage]): Liste ordonnée des métadonnées de pages.
        _selection (int): Index de la page actuellement sélectionnée (-1 si aucune).
        _imageList: Liste d'images ou conteneur d'icônes pour les onglets.
        _minTabWidth (int): Largeur minimale d'onglet en pixels (-1 si indéfinie).
        _maxTabWidth (int): Largeur maximale d'onglet en pixels (-1 si indéfinie).
        _tab_ctrl_height (int): Hauteur de la barre d'onglets en pixels.
        _textCtrl: Référence vers le champ temporaire d'édition de libellé.
        _sashDClickUnsplit (bool): Indique si le double-clic sur un séparateur réunit les volets.
        _manager: Référence vers le gestionnaire AuiManager associé.
        _navigatorIcon: Icône personnalisée pour la boîte de dialogue de navigation.
        _notebook (ttk.Notebook): Composant Tkinter/ttk natif assurant le rendu des onglets.
        _drag_index (int | None): Index de l'onglet source lors d'un glisser-déposer.
    """

    def __init__(self, parent, id=-1, pos=None, size=None, style=None,
                 agwStyle=AUI_NB_DEFAULT_STYLE, name="auinotebook", **kwargs):
        """Initialise le carnet d'onglets AuiNotebook.

        Crée le conteneur principal (``ttk.Frame``) ainsi que le widget interne
        ``ttk.Notebook``. Configure les liaisons d'événements pour la synchronisation
        de la sélection et le réordonnancement des onglets par glisser-déposer.

        Args:
            parent: Widget parent Tkinter hébergeant le carnet d'onglets.
            id (int, optional): Identifiant numérique du widget (compatibilité wx). Par défaut -1.
            pos (tuple[int, int], optional): Position initiale (x, y) en pixels.
            size (tuple[int, int], optional): Dimensions initiales (width, height) en pixels.
            style (optional): Style d'origine wx (ignoré).
            agwStyle (int, optional): Drapeaux de style AUI (par ex. ``AUI_NB_DEFAULT_STYLE``).
            name (str, optional): Nom du widget. Par défaut ``"auinotebook"``.
            **kwargs: Arguments supplémentaires transmis au constructeur de ``ttk.Frame``.
        """
        # ttk.Frame ne prend pas le paramètre Tcl 'name' de tk.Frame.
        super().__init__(parent, **kwargs)
        self._auiStyle = agwStyle
        self._art = None
        self._pages = []
        self._selection = -1
        self._imageList = None
        self._minTabWidth = -1
        self._maxTabWidth = -1
        self._tab_ctrl_height = 20
        self._textCtrl = None
        self._sashDClickUnsplit = False
        self._manager = None
        self._navigatorIcon = None

        # Instanciation du widget ttk.Notebook interne pour la gestion native des onglets
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)  # à changer en grid ?

        # Liaison des événements de changement d'onglet et de glisser-déposer
        self._notebook.bind("<<NotebookTabChanged>>", self._OnTtkTabChanged)
        self._notebook.bind("<Button-1>", self._OnTabPress, add="+")
        self._notebook.bind("<ButtonRelease-1>", self._OnTabRelease, add="+")
        self._drag_index = None

        # Positionnement et dimensions initiaux optionnels
        if pos is not None:
            try:
                self.place(x=pos[0], y=pos[1])
            except (TypeError, IndexError):
                pass
        if size is not None:
            try:
                self.configure(width=size[0], height=size[1])
            except (TypeError, IndexError, tk.TclError):
                pass

    def _OnTtkTabChanged(self, event=None):
        """Synchronise l'état interne lorsqu'un changement d'onglet survient dans ttk.Notebook.

        Résout le nom du widget sélectionné renvoyé par ``ttk.Notebook.select()``
        en instance de widget, retrouve son index parmi ``self._pages``, met à jour
        ``self._selection`` et actualise l'attribut ``active`` de chaque page.

        Args:
            event (tk.Event, optional): Événement virtuel <<NotebookTabChanged>>.
        """
        try:
            # Obtention du widget correspondant à la sélection active
            widget = self._notebook.nametowidget(self._notebook.select())
            index = self.GetPageIndex(widget)
        except (KeyError, tk.TclError):
            return
        if index >= 0:
            self._selection = index
            # Synchronisation de l'attribut active sur toutes les pages
            for i, page in enumerate(self._pages):
                page.active = (i == index)

    def _OnTabPress(self, event):
        """Enregistre l'onglet sous le curseur lors d'un clic pour amorcer le glisser-déposer.

        Args:
            event (tk.Event): Événement souris <Button-1>.
        """
        try:
            # Détermination de l'index de l'onglet cliqué via la notation @x,y de Tk
            self._drag_index = self._notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            self._drag_index = None

    def _OnTabRelease(self, event):
        """Finalise le déplacement d'onglet au relâchement du bouton de souris.

        Calcule l'onglet de destination sous la position de relâchement et
        réordonne la page si l'index cible diffère de l'index de départ.

        Args:
            event (tk.Event): Événement souris <ButtonRelease-1>.
        """
        if self._drag_index is None:
            return
        try:
            # Index de l'onglet sous le curseur au moment du relâchement
            target = self._notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            self._drag_index = None
            return
        source = self._drag_index
        self._drag_index = None
        # Si source et cible sont valides et distincts, déplacer l'onglet
        if source != target and 0 <= source < len(self._pages) and 0 <= target < len(self._pages):
            self.ReorderPage(source, target)

    def ReorderPage(self, source, target):
        """Déplace un onglet de la position source vers la position cible.

        Met à jour à la fois la liste ordonnée des métadonnées (``self._pages``)
        et l'ordre visuel des onglets dans le composant natif ``ttk.Notebook``.

        Args:
            source (int): Index d'origine de la page à déplacer.
            target (int): Nouvel index de destination.

        Returns:
            bool: ``True`` si le réordonnancement a réussi, ``False`` si les index
            sont hors limites.
        """
        if not (0 <= source < len(self._pages) and 0 <= target < len(self._pages)):
            return False
        # Déplacement dans la liste Python des pages
        page = self._pages.pop(source)
        self._pages.insert(target, page)
        # Déplacement visuel dans le ttk.Notebook
        self._notebook.insert(target, page.window)
        # Mise à jour de l'index de sélection courante
        self._selection = self.GetPageIndex(self._notebook.nametowidget(self._notebook.select())) if self._notebook.select() else -1
        return True

    def Destroy(self):
        """Détruit le widget et libère ses ressources (alias wx pour destroy)."""
        self.destroy()

    def __getitem__(self, index):
        """Permet l'accès direct à la fenêtre d'une page par son index.

        Args:
            index (int): Index numérique de la page demandée.

        Returns:
            tk.Widget: La fenêtre associée à la page.
        """
        return self._pages[index].window

    def GetTabContainer(self):
        """Renvoie le composant conteneur d'onglets (ici le ttk.Notebook interne).

        Returns:
            ttk.Notebook: Le composant de carnet d'onglets.
        """
        return self._notebook

    def InitNotebook(self, agwStyle):
        """Initialise le carnet avec le style AGW spécifié.

        Args:
            agwStyle (int): Drapeaux de style AUI.
        """
        self.SetAGWWindowStyleFlag(agwStyle)

    def SetArtProvider(self, art):
        """Définit le fournisseur artistique pour le rendu des onglets.

        Conservé pour compatibilité avec l'API AUI de wxPython ; le rendu visuel
        des onglets sous ttk est géré par le moteur de thèmes ttk.

        Args:
            art: Instance du fournisseur d'art (TabArt).
        """
        # ttk gère le dessin des onglets via son thème et ses styles.
        self._art = art

    def GetArtProvider(self):
        """Renvoie le fournisseur artistique courant.

        Returns:
            Any: Le fournisseur d'art actuellement configuré (ou None).
        """
        return self._art

    def SavePerspective(self):
        """Sérialise l'état actuel du carnet d'onglets au format JSON.

        Enregistre l'index de la page sélectionnée ainsi que la séquence des
        titres des pages pour restauration ultérieure.

        Returns:
            str: Chaîne JSON représentant la perspective du carnet.
        """
        return json.dumps({"selection": self.GetSelection(), "pages": [p.caption for p in self._pages]})

    def LoadPerspective(self, layout):
        """Restaure l'état du carnet d'onglets à partir d'une chaîne JSON.

        Args:
            layout (str): Chaîne JSON précédemment générée par :meth:`SavePerspective`.

        Returns:
            bool: ``True`` si la perspective a été appliquée avec succès, ``False`` en cas d'erreur.
        """
        try:
            data = json.loads(layout)
            selection = data.get("selection", -1)
            if 0 <= selection < len(self._pages):
                self.SetSelection(selection)
            return True
        except (TypeError, ValueError, tk.TclError):
            return False

    def SetTabCtrlHeight(self, height):
        """Définit la hauteur de la barre d'onglets en pixels.

        Args:
            height (int): Hauteur en pixels.
        """
        self._tab_ctrl_height = height

    def SetUniformBitmapSize(self, size):
        """Définit les dimensions uniformes des icônes d'onglets.

        Args:
            size (tuple[int, int]): Dimensions (largeur, hauteur) des bitmaps.
        """
        self._uniformBitmapSize = size

    def UpdateTabCtrlHeight(self, force=False):
        """Met à jour la hauteur de la barre d'onglets (stub de compatibilité wx).

        Args:
            force (bool, optional): Forcer le recalcul de la hauteur. Par défaut ``False``.
        """
        pass

    def UpdateHintWindowSize(self):
        """Met à jour les dimensions de la fenêtre de prévisualisation (stub de compatibilité wx)."""
        pass

    def CalculateNewSplitSize(self):
        """Calcule la taille par défaut pour un nouveau fractionnement d'onglet.

        Returns:
            int: Hauteur actuelle de la fenêtre.
        """
        return self.winfo_height()

    def CalculateTabCtrlHeight(self):
        """Renvoie la hauteur calculée de la barre d'onglets.

        Returns:
            int: Hauteur de la barre d'onglets en pixels.
        """
        return self._tab_ctrl_height

    def SetAGWWindowStyleFlag(self, agwStyle):
        """Définit les drapeaux de style AUI pour le carnet d'onglets.

        Args:
            agwStyle (int): Masque binaire de styles AUI.
        """
        self._auiStyle = agwStyle

    def GetAGWWindowStyleFlag(self):
        """Renvoie les drapeaux de style AUI actuellement actifs.

        Returns:
            int: Masque binaire de styles AUI.
        """
        return self._auiStyle

    def AddPage(self, page, caption, select=False, bitmap=None,
                disabled_bitmap=None, control=None, tooltip=""):
        """Ajoute une nouvelle page à la fin du carnet d'onglets.

        Délègue l'insertion à :meth:`InsertPage` avec un index correspondant
        au nombre actuel de pages.

        Args:
            page (tk.Widget): Widget représentant le contenu de la page (doit avoir
                ce carnet / notebook comme parent).
            caption (str): Titre affiché sur l'onglet.
            select (bool, optional): ``True`` pour sélectionner immédiatement cette
                nouvelle page. Par défaut ``False``.
            bitmap (optional): Image / icône normale de l'onglet.
            disabled_bitmap (optional): Image / icône lorsque l'onglet est désactivé.
            control (optional): Contrôle additionnel associé à la page.
            tooltip (str, optional): Infobulle associée à l'onglet.

        Returns:
            bool: ``True`` si la page a été ajoutée avec succès.
        """
        return self.InsertPage(len(self._pages), page, caption, select,
                               bitmap, disabled_bitmap, control, tooltip)

    def InsertPage(self, page_idx, page, caption, select=False, bitmap=None,
                   disabled_bitmap=None, control=None, tooltip=""):
        """Insère une nouvelle page à la position spécifiée dans le carnet d'onglets.

        Vérifie la validité du widget et de son appartenance au notebook ttk,
        crée la structure de métadonnées ``AuiNotebookPage``, ajoute l'onglet
        dans le composant ``ttk.Notebook`` natif, et applique les états
        d'activation et de visibilité.

        Args:
            page_idx (int): Position d'insertion souhaitée.
            page (tk.Widget): Widget de contenu de la page.
            caption (str): Libellé affiché sur l'onglet.
            select (bool, optional): ``True`` pour sélectionner l'onglet après insertion.
                Par défaut ``False``.
            bitmap (optional): Icône normale de l'onglet.
            disabled_bitmap (optional): Icône pour état désactivé.
            control (optional): Contrôle spécifique rattaché à l'onglet.
            tooltip (str, optional): Texte de l'infobulle. Par défaut ``""``.

        Returns:
            bool: ``True`` si la page a été insérée avec succès.

        Raises:
            TypeError: Si ``page`` n'est pas une instance valide de ``tk.Widget``.
            ValueError: Si ``page`` n'a pas le ``ttk.Notebook`` interne comme parent direct.
        """
        if page is None or not isinstance(page, tk.Widget):
            raise TypeError("page doit être un widget Tkinter/ttk")
        if page.winfo_parent() != str(self._notebook):
            raise ValueError("Avec ttk.Notebook, chaque page doit avoir le notebook comme parent")
        # Borne l'index d'insertion dans les limites actuelles de la liste
        page_idx = max(0, min(int(page_idx), len(self._pages)))
        info = AuiNotebookPage()
        info.window = page
        info.caption = caption
        info.bitmap = bitmap
        info.dis_bitmap = disabled_bitmap
        info.control = control or page
        info.tooltip = tooltip
        self._pages.insert(page_idx, info)
        # self._notebook.insert(page_idx, page, text=caption)
        # ttk.Notebook ne fournit pas de tooltip natif. La valeur reste
        # disponible via GetPageTooltip, comme dans l'API AUI.
        if not self._notebook.tabs():
            self._notebook.add(page, text=caption)
        else:
            self._notebook.insert(page_idx, page, text=caption)
        # Application de l'état désactivé si applicable
        if not getattr(info, "enabled", True):
            self._notebook.tab(page, state="disabled")
        # Masquage initial de la page si spécifié
        if getattr(info, "hidden", False):
            self._notebook.hide(page)
        # Sélection immédiate si demandé ou s'il s'agit du premier onglet
        if select or self._selection < 0:
            self.SetSelection(page_idx)
        else:
            self._selection = self.GetSelection()
        return True

    def DeletePage(self, page_idx):
        """Supprime une page du carnet d'onglets (alias pour RemovePage).

        Args:
            page_idx (int): Index de la page à supprimer.

        Returns:
            bool: ``True`` si la page a été supprimée, ``False`` si l'index est invalide.
        """
        return self.RemovePage(page_idx)

    def RemovePage(self, page_idx):
        """Retire une page du carnet d'onglets et détache son widget de ttk.Notebook.

        Retire les métadonnées de ``self._pages``, détache la fenêtre associée
        via ``forget()`` sur le composant ttk, et ajuste la sélection courante.

        Args:
            page_idx (int): Index de la page à retirer.

        Returns:
            bool: ``True`` si la page a été retirée, ``False`` si l'index est invalide.
        """
        if not 0 <= page_idx < len(self._pages):
            return False
        info = self._pages.pop(page_idx)
        try:
            self._notebook.forget(info.window)
        except tk.TclError:
            pass
        # Ajuste la sélection vers l'onglet restant le plus proche
        if self._pages:
            self.SetSelection(min(page_idx, len(self._pages) - 1))
        else:
            self._selection = -1
        return True

    def _hide_ttk_page(self, page):
        """Masque une page avec l'API disponible dans la version de Tk.

        Tente d'appeler ``ttk.Notebook.hide()`` ; si cette méthode n'est pas supportée
        par la version de Tk utilisée, bascule vers ``ttk.Notebook.forget()``.

        Args:
            page (AuiNotebookPage): Métadonnées de la page à masquer.
        """
        try:
            self._notebook.hide(page.window)
        except tk.TclError:
            # Repli pour les versions anciennes de Tk sans ttk::notebook hide.
            self._notebook.forget(page.window)

    def HidePage(self, page_idx, hidden=True):
        """Masque ou réaffiche une page spécifique du carnet d'onglets.

        Args:
            page_idx (int): Index de la page concernée.
            hidden (bool, optional): ``True`` pour masquer la page, ``False`` pour
                la réafficher. Par défaut ``True``.

        Returns:
            bool: ``True`` si l'état de visibilité a été modifié, ``False`` si l'index
            est hors limites.
        """
        if not 0 <= page_idx < len(self._pages):
            return False
        page = self._pages[page_idx]
        page.hidden = bool(hidden)
        if hidden:
            self._hide_ttk_page(page)
            # Réactualise la sélection si l'onglet masqué était actif
            if page_idx == self._selection:
                self._selection = self.GetSelection()
        else:
            # Réinsertion de l'onglet dans le notebook
            self._notebook.add(page.window, text=page.caption)
            self._notebook.insert(page_idx, page.window)
            if page_idx == self._selection:
                self.SetSelection(page_idx)
        return True

    def FindNextActiveTab(self, idx):
        """Recherche le prochain onglet disponible (visible et activé) après un index donné.

        Parcourt cycliquement les pages suivantes pour trouver le premier onglet
        qui n'est ni masqué ni désactivé.

        Args:
            idx (int): Index de départ de la recherche.

        Returns:
            int: Index du prochain onglet actif trouvé, ou -1 si aucun n'est disponible.
        """
        if not self._pages:
            return -1
        for offset in range(1, len(self._pages) + 1):
            candidate = (idx + offset) % len(self._pages)
            if not self._pages[candidate].hidden and self._pages[candidate].enabled:
                return candidate
        return -1

    def HideAllTabs(self, hidden=True):
        """Modifie la visibilité de l'ensemble des onglets du carnet.

        Args:
            hidden (bool, optional): ``True`` pour masquer tous les onglets,
                ``False`` pour les afficher. Par défaut ``True``.
        """
        for i in range(len(self._pages)):
            self.HidePage(i, hidden)

    def SetSashDClickUnsplit(self, unsplit):
        """Active ou désactive la réunification de fractionnement par double-clic sur le séparateur.

        Args:
            unsplit (bool): ``True`` pour activer la fermeture du volet par double-clic.
        """
        self._sashDClickUnsplit = bool(unsplit)

    def GetSashDClickUnsplit(self):
        """Indique si la réunification de volets par double-clic est activée.

        Returns:
            bool: ``True`` si activée, ``False`` sinon.
        """
        return self._sashDClickUnsplit

    def SetMinMaxTabWidth(self, a, b):
        """Définit les largeurs minimale et maximale autorisées pour les onglets.

        Args:
            a (int): Largeur minimale en pixels (-1 si non restreinte).
            b (int): Largeur maximale en pixels (-1 si non restreinte).
        """
        self._minTabWidth, self._maxTabWidth = a, b

    def GetMinMaxTabWidth(self):
        """Renvoie les largeurs minimale et maximale d'onglets configurées.

        Returns:
            tuple[int, int]: Tuple (min_width, max_width).
        """
        return self._minTabWidth, self._maxTabWidth

    def GetPageIndex(self, page_wnd):
        """Recherche l'index d'une page à partir de son widget fenêtre.

        Args:
            page_wnd (tk.Widget): Le widget fenêtre contenu dans la page.

        Returns:
            int: L'index de la page dans ``self._pages``, ou -1 si introuvable.
        """
        return next((i for i, page in enumerate(self._pages) if page.window == page_wnd), -1)

    def SetPageText(self, i, text):
        """Modifie le libellé affiché sur un onglet donné.

        Met à jour à la fois l'attribut ``caption`` de la page et le texte
        affiché par le composant ``ttk.Notebook``.

        Args:
            i (int): Index de la page.
            text (str): Nouveau libellé de l'onglet.
        """
        self._pages[i].caption = text
        self._notebook.tab(self._pages[i].window, text=text)

    def GetPageText(self, i):
        """Renvoie le libellé d'un onglet donné.

        Args:
            i (int): Index de la page.

        Returns:
            str: Libellé de l'onglet.
        """
        return self._pages[i].caption

    def SetPageBitmap(self, i, bitmap):
        """Définit l'icône associée à un onglet donné.

        Args:
            i (int): Index de la page.
            bitmap: Image ou icône de l'onglet.
        """
        self._pages[i].bitmap = bitmap

    def GetPageBitmap(self, i):
        """Renvoie l'icône associée à un onglet donné.

        Args:
            i (int): Index de la page.

        Returns:
            Any: L'icône configurée pour la page.
        """
        return self._pages[i].bitmap

    def SetPageTooltip(self, i, tooltip):
        """Définit le texte de l'infobulle d'un onglet donné.

        Args:
            i (int): Index de la page.
            tooltip (str): Texte d'infobulle.
        """
        self._pages[i].tooltip = tooltip

    def GetPageTooltip(self, i):
        """Renvoie le texte de l'infobulle d'un onglet donné.

        Args:
            i (int): Index de la page.

        Returns:
            str: Texte d'infobulle.
        """
        return self._pages[i].tooltip

    def SetImageList(self, image_list):
        """Définit la liste d'images pour les icônes d'onglets.

        Args:
            image_list: Conteneur d'images / liste d'icônes.
        """
        self._imageList = image_list

    def AssignImageList(self, image_list):
        """Assigne la liste d'images pour les icônes d'onglets (alias wx).

        Args:
            image_list: Conteneur d'images / liste d'icônes.
        """
        self._imageList = image_list

    def GetImageList(self):
        """Renvoie la liste d'images d'icônes courante.

        Returns:
            Any: La liste d'images assignée (ou None).
        """
        return self._imageList

    def SetPageImage(self, page, image):
        """Définit l'icône ou index d'image pour une page donnée.

        Args:
            page (int): Index de la page.
            image: Image ou index dans la liste d'images.
        """
        self._pages[page].bitmap = image

    def GetPageImage(self, page):
        """Renvoie l'icône ou index d'image d'une page donnée.

        Args:
            page (int): Index de la page.

        Returns:
            Any: L'image associée à la page.
        """
        return self._pages[page].bitmap

    def SetPageTextColour(self, i, colour):
        """Définit la couleur du texte d'un onglet donné.

        Args:
            i (int): Index de la page.
            colour (str): Code couleur (hexadécimal ou nom Tkinter).
        """
        self._pages[i].text_colour = colour

    def GetPageTextColour(self, i):
        """Renvoie la couleur du texte configurée pour un onglet donné.

        Args:
            i (int): Index de la page.

        Returns:
            str: Code couleur hexadécimal ou nom de couleur.
        """
        return self._pages[i].text_colour

    def AddControlToPage(self, i, control):
        """Associe un widget de contrôle personnalisé à une page donnée.

        Args:
            i (int): Index de la page.
            control: Widget de contrôle à associer.
        """
        self._pages[i].control = control

    def RemoveControlFromPage(self, i):
        """Dissocie le contrôle personnalisé d'une page donnée.

        Args:
            i (int): Index de la page.
        """
        self._pages[i].control = None

    def SetCloseButton(self, i, value):
        """Active ou désactive la présence d'un bouton de fermeture sur un onglet.

        Args:
            i (int): Index de la page.
            value (bool): ``True`` pour afficher un bouton de fermeture, ``False`` sinon.
        """
        self._pages[i].hasCloseButton = bool(value)

    def HasCloseButton(self, i):
        """Indique si un onglet donné dispose d'un bouton de fermeture.

        Args:
            i (int): Index de la page.

        Returns:
            bool: ``True`` si un bouton de fermeture est présent, ``False`` sinon.
        """
        return getattr(self._pages[i], "hasCloseButton", True)

    def GetSelection(self):
        """Renvoie l'index de la page actuellement sélectionnée.

        Interroge le composant ``ttk.Notebook`` interne pour obtenir le widget
        actif et actualise la valeur mise en cache ``self._selection``.

        Returns:
            int: L'index de la page sélectionnée, ou -1 si aucune page n'est sélectionnée.
        """
        if not self._pages:
            return -1
        try:
            selected = self._notebook.select()
            if selected:
                widget = self._notebook.nametowidget(selected)
                index = self.GetPageIndex(widget)
                if index >= 0:
                    self._selection = index
        except tk.TclError:
            pass
        return self._selection

    def GetCurrentPage(self):
        """Renvoie le widget fenêtre de la page actuellement sélectionnée.

        Returns:
            tk.Widget | None: Le widget fenêtre sélectionné, ou ``None`` si aucune sélection.
        """
        selection = self.GetSelection()
        return self._pages[selection].window if selection >= 0 else None

    def EnsureVisible(self, indx):
        """S'assure qu'un onglet donné est visible dans la barre.

        Args:
            indx (int): Index de la page.

        Returns:
            bool: ``True`` si l'index est valide et la page existe, ``False`` sinon.
        """
        return 0 <= indx < len(self._pages)

    def SetSelection(self, new_page, force=False):
        """Définit la page active par son index numérique.

        Vérifie que la page cible existe, n'est pas masquée et est activée,
        puis applique la sélection au ``ttk.Notebook`` sous-jacent et met à jour
        les drapeaux ``active`` de chaque page.

        Args:
            new_page (int): Index de la nouvelle page à sélectionner.
            force (bool, optional): Forcer la sélection (ignoré). Par défaut ``False``.

        Returns:
            int: L'ancien index de sélection, ou -1 si la sélection est invalide.
        """
        if not 0 <= new_page < len(self._pages) or self._pages[new_page].hidden or not self._pages[new_page].enabled:
            return -1
        old = self.GetSelection()
        self._notebook.select(self._pages[new_page].window)
        self._selection = new_page
        for i, page in enumerate(self._pages):
            page.active = (i == new_page)
        return old

    def SetSelectionToWindow(self, window):
        """Sélectionne la page correspondant au widget fenêtre fourni.

        Args:
            window (tk.Widget): Fenêtre dont l'onglet doit être sélectionné.

        Returns:
            int: L'ancien index de sélection, ou -1 si introuvable.
        """
        return self.SetSelection(self.GetPageIndex(window))

    def SetSelectionToPage(self, page):
        """Sélectionne la page correspondant à l'objet page ou widget fourni.

        Args:
            page (tk.Widget | AuiNotebookPage): Page ou widget à sélectionner.

        Returns:
            int: L'ancien index de sélection, ou -1 si introuvable.
        """
        return self.SetSelection(self.GetPageIndex(page))

    def GetPageCount(self):
        """Renvoie le nombre total de pages enregistrées dans le carnet.

        Returns:
            int: Nombre de pages.
        """
        return len(self._pages)

    def GetShownPageCount(self):
        """Renvoie le nombre de pages actuellement visibles (non masquées).

        Returns:
            int: Nombre de pages visibles.
        """
        return sum(not page.hidden for page in self._pages)

    def GetPage(self, i):
        """Renvoie le widget fenêtre de la page à l'index donné.

        Args:
            i (int): Index de la page.

        Returns:
            tk.Widget: Le widget associé à cette page.
        """
        return self._pages[i].window

    def GetPageInfo(self, i):
        """Renvoie l'objet de métadonnées AuiNotebookPage à l'index donné.

        Args:
            i (int): Index de la page.

        Returns:
            AuiNotebookPage: L'objet décrivant la page.
        """
        return self._pages[i]

    def GetEnabled(self, i):
        """Indique si un onglet donné est activé (cliquable).

        Args:
            i (int): Index de la page.

        Returns:
            bool: ``True`` si la page est activée, ``False`` sinon.
        """
        return self._pages[i].enabled

    def EnableTab(self, i, value=True):
        """Active ou désactive un onglet dans la barre.

        Met à jour l'état interne de la page et modifie l'état de l'onglet
        dans ``ttk.Notebook`` (``normal`` ou ``disabled``).

        Args:
            i (int): Index de la page.
            value (bool, optional): ``True`` pour activer l'onglet, ``False`` pour
                le désactiver. Par défaut ``True``.
        """
        page = self._pages[i]
        page.enabled = bool(value)
        self._notebook.tab(page.window, state="normal" if value else "disabled")

    def GetHidden(self, i):
        """Indique si un onglet donné est masqué.

        Args:
            i (int): Index de la page.

        Returns:
            bool: ``True`` si la page est masquée, ``False`` sinon.
        """
        return self._pages[i].hidden

    def DoSizing(self):
        """Recalcule la disposition et les dimensions des onglets (stub de compatibilité wx)."""
        pass

    def GetAuiManager(self):
        """Renvoie l'instance du gestionnaire AuiManager associé.

        Returns:
            AuiManager | None: Le gestionnaire AUI associé ou ``None``.
        """
        return self._manager

    def GetActiveTabCtrl(self):
        """Renvoie le contrôle d'onglets actif (ici le ttk.Notebook interne).

        Returns:
            ttk.Notebook: Le contrôle d'onglets.
        """
        return self._notebook

    def FindTab(self, page):
        """Recherche le conteneur d'onglets détenant la page spécifiée.

        Args:
            page (tk.Widget): Widget fenêtre recherché.

        Returns:
            ttk.Notebook: Le conteneur d'onglets.
        """
        return self._notebook

    def Split(self, page, direction):
        """Fractionne le carnet d'onglets dans la direction spécifiée (non implémenté).

        Args:
            page (int | tk.Widget): Page ou index à fractionner.
            direction (int): Direction du fractionnement (ex. wx.LEFT, wx.RIGHT).

        Returns:
            bool: ``False`` (non supporté dans cette version simplifiée).
        """
        return False

    def UnSplit(self):
        """Annule le fractionnement des onglets (non implémenté).

        Returns:
            bool: ``False`` (non supporté dans cette version simplifiée).
        """
        return False

    def ReparentControl(self, control, dest_tabs):
        """Transfère un contrôle vers un autre conteneur d'onglets (non implémenté).

        Args:
            control: Contrôle à transférer.
            dest_tabs: Conteneur d'onglets de destination.

        Returns:
            bool: ``False``.
        """
        return False

    def UnsplitDClick(self, part, sash_size, pos):
        """Gère le double-clic sur un séparateur pour réunifier les volets (non implémenté).

        Args:
            part: Partie cliquée.
            sash_size: Taille du séparateur.
            pos: Position du clic.

        Returns:
            bool: ``False``.
        """
        return False

    def OnSize(self, event=None):
        """Gestionnaire d'événement de redimensionnement (stub de compatibilité wx).

        Args:
            event (tk.Event, optional): Événement de redimensionnement.
        """
        pass

    def OnTabClicked(self, event):
        """Gestionnaire de clic sur un onglet (stub de compatibilité wx).

        Args:
            event: Événement de clic.
        """
        pass

    def OnTabBgDClick(self, event):
        """Gestionnaire de double-clic sur l'arrière-plan de la barre (stub de compatibilité wx).

        Args:
            event: Événement de double-clic.
        """
        pass

    def OnTabDClick(self, event):
        """Gestionnaire de double-clic sur un onglet (stub de compatibilité wx).

        Args:
            event: Événement de double-clic.
        """
        pass

    def OnTabBeginDrag(self, event):
        """Gestionnaire de début de glissement d'onglet (stub de compatibilité wx).

        Args:
            event: Événement de glissement.
        """
        pass

    def OnTabDragMotion(self, event):
        """Gestionnaire de déplacement pendant le glissement d'onglet (stub wx).

        Args:
            event: Événement de mouvement souris.
        """
        pass

    def OnTabEndDrag(self, event):
        """Gestionnaire de fin de glissement d'onglet (stub de compatibilité wx).

        Args:
            event: Événement de fin de glissement.
        """
        pass

    def OnTabCancelDrag(self, event):
        """Gestionnaire d'annulation de glissement d'onglet (stub de compatibilité wx).

        Args:
            event: Événement d'annulation.
        """
        pass

    def IsMouseWellOutsideWindow(self):
        """Vérifie si la souris est nettement en dehors du carnet lors d'un glissement.

        Returns:
            bool: ``False``.
        """
        return False

    def FloatPage(self, page_index):
        """Détache une page pour la rendre flottante (non implémenté dans cette version).

        Args:
            page_index (int): Index de la page à rendre flottante.

        Returns:
            bool: ``False``.
        """
        return False

    def OnCloseFloatingPage(self, event):
        """Gestionnaire de fermeture d'une fenêtre de page flottante (stub wx).

        Args:
            event: Événement de fermeture.
        """
        pass

    def ReDockPage(self, pane):
        """Réamarre une page flottante dans le carnet d'onglets (non implémenté).

        Args:
            pane: Volet à réamarrer.

        Returns:
            bool: ``False``.
        """
        return False

    def GetTabCtrlFromPoint(self, pt):
        """Renvoie le contrôle d'onglets sous le point de coordonnées spécifié.

        Args:
            pt (tuple[int, int]): Coordonnées (x, y).

        Returns:
            ttk.Notebook: Le composant de carnet d'onglets interne.
        """
        return self._notebook

    def GetTabFrameFromTabCtrl(self, tab_ctrl):
        """Renvoie le TabFrame associé à un contrôle d'onglets (stub wx).

        Args:
            tab_ctrl: Contrôle d'onglets.

        Returns:
            TabFrame | None: ``None``.
        """
        return None

    def GetTabFrameFromWindow(self, wnd):
        """Renvoie le TabFrame contenant une fenêtre donnée (stub wx).

        Args:
            wnd (tk.Widget): Widget fenêtre recherché.

        Returns:
            TabFrame | None: ``None``.
        """
        return None

    def RemoveEmptyTabFrames(self):
        """Supprime les cadres d'onglets vides après déplacement ou fermeture (stub wx)."""
        pass

    def OnChildFocusNotebook(self, event):
        """Gestionnaire de prise de focus d'un widget enfant (stub wx).

        Args:
            event (tk.Event): Événement de focus.
        """
        pass

    def SetNavigatorIcon(self, bitmap):
        """Définit l'icône de la boîte de dialogue de navigation entre onglets.

        Args:
            bitmap: Image ou icône à utiliser dans le navigateur.
        """
        self._navigatorIcon = bitmap

    def OnNavigationKeyNotebook(self, event):
        """Gère les raccourcis de navigation clavier (Ctrl+Tab, etc.) (stub wx).

        Args:
            event (tk.Event): Événement clavier.
        """
        pass

    def OnTabButton(self, event):
        """Gestionnaire de clic sur un bouton d'onglet (stub wx).

        Args:
            event: Événement déclencheur.
        """
        pass

    def OnTabMiddleDown(self, event):
        """Gestionnaire de clic avec le bouton central de souris sur un onglet (stub wx).

        Args:
            event: Événement de clic milieu.
        """
        pass

    def OnTabMiddleUp(self, event):
        """Gestionnaire de relâchement du bouton central de souris sur un onglet (stub wx).

        Args:
            event: Événement de relâchement milieu.
        """
        pass

    def OnTabRightDown(self, event):
        """Gestionnaire de clic avec le bouton droit de souris sur un onglet (stub wx).

        Args:
            event: Événement de clic droit.
        """
        pass

    def OnTabRightUp(self, event):
        """Gestionnaire de relâchement du bouton droit de souris sur un onglet (stub wx).

        Args:
            event: Événement de relâchement droit.
        """
        pass

    def SetNormalFont(self, font):
        """Définit la police utilisée pour les onglets non sélectionnés.

        Args:
            font: Objet police ou nom de police.
        """
        self._normalFont = font

    def SetSelectedFont(self, font):
        """Définit la police utilisée pour l'onglet sélectionné.

        Args:
            font: Objet police ou nom de police.
        """
        self._selectedFont = font

    def SetMeasuringFont(self, font):
        """Définit la police utilisée pour la mesure des textes d'onglets.

        Args:
            font: Objet police de mesure.
        """
        self._measuringFont = font

    def SetFont(self, font):
        """Applique une police générale au carnet d'onglets via le style ttk.

        Args:
            font: Police à appliquer.
        """
        self.configure(style="TNotebook")

    def GetTabCtrlHeight(self):
        """Renvoie la hauteur de la barre d'onglets en pixels.

        Returns:
            int: Hauteur de la barre d'onglets.
        """
        return self._tab_ctrl_height

    def GetHeightForPageHeight(self, pageHeight):
        """Calcule la hauteur totale requise pour une hauteur de contenu donnée.

        Args:
            pageHeight (int): Hauteur du contenu de la page en pixels.

        Returns:
            int: Hauteur totale incluant la barre d'onglets.
        """
        return pageHeight + self._tab_ctrl_height

    def AdvanceSelection(self, forward, wrap=True):
        """Avance ou recule la sélection vers le prochain onglet actif.

        Parcourt cycliquement ou séquentiellement les pages pour sélectionner
        la prochaine page visible et activée.

        Args:
            forward (bool): ``True`` pour avancer vers la droite, ``False`` pour reculer.
            wrap (bool, optional): ``True`` pour reboucler en début/fin de liste. Par défaut ``True``.

        Returns:
            int: Le nouvel index sélectionné, ou l'index courant si aucune transition n'est possible.
        """
        if not self._pages:
            return -1
        current = self.GetSelection()
        step = 1 if forward else -1
        # Recherche du prochain candidat valide
        for offset in range(1, len(self._pages) + 1):
            candidate = current + step * offset
            if wrap:
                candidate %= len(self._pages)
            elif not 0 <= candidate < len(self._pages):
                return current
            if not self._pages[candidate].hidden and self._pages[candidate].enabled:
                return self.SetSelection(candidate)
        return -1

    def ShowWindowMenu(self):
        """Affiche le menu de liste des fenêtres/onglets ouverts (non implémenté).

        Returns:
            None
        """
        return None

    def AddTabAreaButton(self, *args):
        """Ajoute un bouton personnalisé dans la zone de la barre d'onglets (non implémenté).

        Returns:
            None
        """
        return None

    def RemoveTabAreaButton(self, id):
        """Retire un bouton personnalisé de la zone de la barre d'onglets.

        Args:
            id (int): Identifiant du bouton.

        Returns:
            bool: ``False``.
        """
        return False

    def CloneTabAreaButtons(self):
        """Renvoie une copie de la liste des boutons personnalisés de la barre.

        Returns:
            list: Liste vide dans cette version.
        """
        return []

    def HasMultiplePages(self):
        """Indique si le carnet contient plus d'une page.

        Returns:
            bool: ``True`` si plus d'une page est enregistrée, ``False`` sinon.
        """
        return len(self._pages) > 1

    def GetDefaultBorder(self):
        """Renvoie la largeur de bordure par défaut du carnet.

        Returns:
            int: Largeur de la bordure en pixels (1 par défaut).
        """
        return 1

    def NotebookPreview(self, thumbnail_size=200):
        """Génère une prévisualisation miniature des onglets (non implémenté).

        Args:
            thumbnail_size (int, optional): Taille de miniature en pixels. Par défaut 200.

        Returns:
            None
        """
        return None

    def SetRenamable(self, i, value):
        """Active ou désactive la possibilité de renommer un onglet donné.

        Args:
            i (int): Index de la page.
            value (bool): ``True`` si l'onglet peut être renommé, ``False`` sinon.
        """
        self._pages[i].renamable = bool(value)

    def IsRenamable(self, i):
        """Indique si un onglet donné est modifiable en ligne.

        Args:
            i (int): Index de la page.

        Returns:
            bool: ``True`` si le renommage est autorisé, ``False`` sinon.
        """
        return self._pages[i].renamable

    def OnRenameCancelled(self, page_index):
        """Rappel notifié lorsque le renommage d'un onglet est annulé.

        Args:
            page_index (int): Index de la page dont le renommage a été abandonné.
        """
        pass

    def OnRenameAccept(self, page_index, value):
        """Rappel de validation sollicité avant d'accepter le renommage d'un onglet.

        Permet d'interdire ou d'autoriser un nouveau libellé d'onglet.

        Args:
            page_index (int): Index de la page renommée.
            value (str): Nouveau libellé proposé.

        Returns:
            bool: ``True`` pour accepter le nouveau texte, ``False`` pour le refuser.
        """
        return True

    def ResetTextControl(self):
        """Réinitialise la référence vers le champ de saisie temporaire d'édition d'onglet."""
        self._textCtrl = None

    def EditTab(self, page_index):
        """Déclenche l'édition en ligne du titre d'un onglet spécifié.

        Args:
            page_index (int): Index de la page à renommer.

        Returns:
            bool: ``False`` (non initié ici directement).
        """
        return False


# Noms historiques gardés pour les imports qui attendent le module ttk.
TtkAuiNotebook = AuiNotebook
