# -*- coding: utf-8 -*-
"""Gestionnaire auxiliaire des onglets pour la version ttk d'AUI.

Le contrôle principal est ttk.Notebook. Cette classe conserve l'interface
attendue par les modules AUI existants, sans redessiner les onglets sur Canvas.

Ce module porte la couche d'onglets de wxPython AUI (``auibook.py``) vers
Tkinter/ttk. Le contrôle visuel principal est ``ttk.Notebook`` ; les classes
ici conservent l'API attendue par les modules AUI existants (noms de méthodes
repris de wxPython) sans redessiner les onglets sur un Canvas.

Contenu :

- ``AuiTabContainer`` : état et logique des pages (ordre, activation,
  visibilité, boutons). Ne dessine rien.
- ``AuiTabCtrl`` : adaptateur ``ttk.Frame`` qui hérite de
  ``AuiTabContainer`` et relaie les événements souris et clavier.
- ``_inside`` : utilitaire de test d'appartenance d'un point à un rectangle.
"""
# Quelques remarques sur le code, à traiter si vous le souhaitez :

# OnKeyDown renvoie "break" pour toutes les touches, pas seulement pour Gauche et Droite. Cela empêche le traitement par défaut de toute autre touche reçue par le widget. Il serait plus sûr de ne renvoyer "break" que dans le cas des flèches.
# AuiTabContainer.__init__ reçoit parent dans AuiTabCtrl, donc self._auiNotebook est bien le Notebook AUI. Cela suppose que AuiNotebook expose AdvanceSelection et _notebook. Ce n’est pas vérifiable depuis ce seul fichier ; il faudra le confirmer dans auibook.py.
# _normalFont, _selectedFont et _measuringFont ne sont initialisés que par leurs setters. Une lecture avant l’appel de ces setters lèvera AttributeError. Les initialiser à None dans __init__ éviterait ce risque.
# GetPointedToTab dépend de TabHitTest, qui renvoie toujours -1. Tant que le hit-test n’est pas implémenté, les clics ne peuvent donc pas identifier un onglet.
# _inside n’est pas utilisée dans ce fichier. Elle est probablement destinée à être utilisée pour le hit-test à venir.

import tkinter as tk
from tkinter import ttk

try:
    from .aui_tk_constants import *
except ImportError:
    from aui_tk_constants import *


class AuiTabContainer:
    """Couche de compatibilité autour de ttk.Notebook.
    
    Maintient la liste ordonnée des pages (``self._pages``) et leur état
    (actif, masqué, activé). Les méthodes de rendu et de hit-test sont des
    stubs qui n'ont pas d'effet, car ``ttk.Notebook`` gère l'affichage.

    Chaque entrée de ``self._pages`` est un objet « info » porteur d'au
    moins les attributs ``window``, ``caption``, ``active``, ``hidden``,
    ``enabled`` et ``hasCloseButton``. Ces attributs sont lus avec
    ``getattr`` et des valeurs par défaut, donc un objet incomplet ne lève
    pas d'erreur.
    """

    def __init__(self, auiNotebook):
        """Initialise le conteneur vide.

        Args:
            auiNotebook (AuiNotebook): Carnet propriétaire. Il doit exposer
                ``_notebook`` (le ``ttk.Notebook``) et ``AdvanceSelection``.
        """
        self._auiNotebook = auiNotebook
        self._agwFlags = 0
        self._art = None
        self._buttons = []
        self._pages = []
        self._tab_close_buttons = []
        self._tab_offset = 0
        self._rect = (0, 0, 1, 1)

    def SetArtProvider(self, art):
        """Définit le fournisseur d'apparence (conservé pour compatibilité).

        Args:
            art: Objet d'apparence wx d'origine. Il n'est pas utilisé par ttk.
        """
        self._art = art

    def GetArtProvider(self):
        """Retourne le fournisseur d'apparence.

        Returns:
            L'objet d'apparence mémorisé, ou ``None``.
        """
        return self._art

    def SetAGWFlags(self, flags):
        """Définit les drapeaux AGW (style des onglets).

        Args:
            flags (int): Combinaison de drapeaux ``AUI_NB_*``.
        """
        self._agwFlags = flags

    def GetAGWFlags(self):
        """Retourne les drapeaux AGW courants.

        Returns:
            int: Combinaison de drapeaux ``AUI_NB_*``.
        """
        return self._agwFlags

    def SetNormalFont(self, font):
        """Définit la police des onglets non sélectionnés.

        Args:
            font (tkinter.font.Font): Police Tk.
        """
        self._normalFont = font

    def SetSelectedFont(self, font):
        """Définit la police de l'onglet sélectionné.

        Args:
            font (tkinter.font.Font): Police Tk.
        """
        self._selectedFont = font

    def SetMeasuringFont(self, font):
        """Définit la police servant à mesurer le texte des onglets.

        Args:
            font (tkinter.font.Font): Police Tk.
        """
        self._measuringFont = font

    def SetTabRect(self, rect):
        """Définit le rectangle occupé par la zone des onglets.

        Args:
            rect (tuple[int, int, int, int]): ``(x, y, largeur, hauteur)``.
        """
        self._rect = rect

    def AddPage(self, page, info):
        """Ajoute une page à la fin de la liste.

        Args:
            page (tk.Widget): Widget de contenu de la page. Il n'est pas
                stocké ici, car il est porté par ``info.window``.
            info: Objet d'information de la page (voir la classe).

        Returns:
            bool: Toujours ``True``.
        """
        self._pages.append(info)
        self._tab_close_buttons.append(getattr(info, "hasCloseButton", True))
        return True

    def InsertPage(self, page, info, index):
        """Insère une page à une position donnée.

        L'index est borné à ``[0, nombre de pages]`` : une valeur hors
        limites est ramenée au bord le plus proche au lieu de lever une erreur.

        Args:
            page (tk.Widget): Widget de contenu de la page.
            info: Objet d'information de la page.
            index (int): Position d'insertion souhaitée.

        Returns:
            bool: Toujours ``True``.
        """
        index = max(0, min(index, len(self._pages)))
        self._pages.insert(index, info)
        self._tab_close_buttons.insert(index, getattr(info, "hasCloseButton", True))
        return True

    def MovePage(self, page, new_index):
        """Déplace une page vers une nouvelle position.

        Args:
            page (tk.Widget): Widget de la page à déplacer.
            new_index (int): Position d'arrivée, dans la liste *après* retrait.

        Returns:
            bool: ``True`` si la page a été déplacée, ``False`` si elle est
            introuvable ou si ``new_index`` est hors limites.
        """
        old_index = self.GetIdxFromWindow(page)
        if old_index < 0 or not 0 <= new_index < len(self._pages):
            return False
        # Retrait puis réinsertion : new_index s'applique à la liste raccourcie.
        item = self._pages.pop(old_index)
        self._pages.insert(new_index, item)
        return True

    def RemovePage(self, window_or_index):
        """Retire une page de la liste.

        Args:
            window_or_index (int | tk.Widget): Index de la page, ou widget
                de la page.

        Returns:
            bool: ``True`` si une page a été retirée, ``False`` sinon.
        """
        index = (
            window_or_index
            if isinstance(window_or_index, int)
            else self.GetIdxFromWindow(window_or_index)
        )
        if not 0 <= index < len(self._pages):
            return False
        self._pages.pop(index)
        self._tab_close_buttons.pop(index)
        return True

    def SetActivePage(self, window_or_index):
        """Marque une seule page comme active.

        Toutes les autres pages reçoivent ``active = False``. Un index
        introuvable (par exemple ``-1``) désactive donc toutes les pages.

        Args:
            window_or_index (int | tk.Widget): Index ou widget de la page à activer.
        """
        index = (
            window_or_index
            if isinstance(window_or_index, int)
            else self.GetIdxFromWindow(window_or_index)
        )
        for i, page in enumerate(self._pages):
            page.active = i == index

    def SetNoneActive(self):
        """Désactive toutes les pages."""
        for page in self._pages:
            page.active = False

    def GetActivePage(self):
        """Retourne l'objet d'information de la page active.

        Returns:
            L'objet d'information de la page active, ou ``None``.
        """
        return next((p for p in self._pages if getattr(p, "active", False)), None)

    def GetWindowFromIdx(self, index):
        """Retourne le widget de la page à l'index donné.

        Args:
            index (int): Index de la page.

        Returns:
            tk.Widget | None: Le widget, ou ``None`` si l'index est hors limites.
        """
        return (
            getattr(self._pages[index], "window", None)
            if 0 <= index < len(self._pages)
            else None
        )

    def GetIdxFromWindow(self, window):
        """Retourne l'index de la page contenant le widget donné.

        Args:
            window (tk.Widget): Widget recherché.

        Returns:
            int: Index de la page, ou ``-1`` si introuvable.
        """
        return next(
            (
                i
                for i, p in enumerate(self._pages)
                if getattr(p, "window", None) == window
            ),
            -1,
        )

    def GetPage(self, index):
        """Retourne l'objet d'information à l'index donné.

        Args:
            index (int): Index de la page.

        Returns:
            L'objet d'information, ou ``None`` si l'index est hors limites.
        """
        return self._pages[index] if 0 <= index < len(self._pages) else None

    def GetPages(self):
        """Retourne la liste des objets d'information (référence directe).

        Returns:
            list: Liste des pages. Toute modification affecte le conteneur.
        """
        return self._pages

    def GetPageCount(self):
        """Retourne le nombre total de pages, masquées comprises.

        Returns:
            int: Nombre de pages.
        """
        return len(self._pages)

    def GetShownPageCount(self):
        """Retourne le nombre de pages non masquées.

        Returns:
            int: Nombre de pages visibles.
        """
        return sum(not getattr(p, "hidden", False) for p in self._pages)

    def GetHidden(self, index):
        """Indique si l'onglet à l'index donné est masqué.

        Args:
            index (int): Index de la page.

        Returns:
            bool: ``True`` si masqué ou si l'index est invalide.
        """
        return getattr(self.GetPage(index), "hidden", False)

    def HideTab(self, index, hidden=True):
        """Masque ou affiche un onglet.

        Args:
            index (int): Index de la page.
            hidden (bool): ``True`` pour masquer, ``False`` pour afficher.
                L'effet réel sur ``ttk.Notebook`` a lieu dans :meth:`DoShowHide`.
        """
        page = self.GetPage(index)
        if page is not None:
            page.hidden = bool(hidden)

    def GetEnabled(self, index):
        """Indique si l'onglet à l'index donné est activé.

        Args:
            index (int): Index de la page.

        Returns:
            bool: ``True`` si activé. Une page sans attribut ``enabled``, ou
            un index invalide, renvoie ``False``.
        """
        return getattr(self.GetPage(index), "enabled", False)

    def EnableTab(self, index, enable=True):
        """Active ou désactive un onglet.

        Args:
            index (int): Index de la page.
            enable (bool): ``True`` pour activer, ``False`` pour désactiver.
        """
        page = self.GetPage(index)
        if page is not None:
            page.enabled = bool(enable)

    def FindNextActiveTab(self, index):
        """Cherche le prochain onglet utilisable après un index donné.

        La recherche avance de manière circulaire (après le dernier onglet,
        on revient au premier) et ignore les onglets masqués ou désactivés.
        L'index de départ lui-même n'est examiné qu'en dernier recours.

        Args:
            index (int): Index de départ.

        Returns:
            int: Index de l'onglet trouvé, ou ``-1`` si aucun n'est utilisable.
        """
        if not self._pages:
            return -1
        # offset va de 1 à N : on teste les N autres pages, puis l'index
        # de départ en dernier, grâce au modulo.
        for offset in range(1, len(self._pages) + 1):
            candidate = (index + offset) % len(self._pages)
            if not self.GetHidden(candidate) and self.GetEnabled(candidate):
                return candidate
        return -1

    def AddButton(
        self, button_id, location, normal_bitmap=None, disabled_bitmap=None, name=""
    ):
        """Ajoute un bouton à la barre d'onglets.

        Le bouton est un objet léger créé à la volée. Il porte son identifiant,
        son emplacement, ses images et son état.

        Args:
            button_id (int): Identifiant du bouton.
            location (int): Emplacement (``AUI_BUTTON_*``).
            normal_bitmap: Image à l'état normal.
            disabled_bitmap: Image à l'état désactivé.
            name (str): Nom du bouton.

        Returns:
            object: Le bouton créé.
        """
        # Type anonyme instancié immédiatement : sert de simple conteneur d'attributs.
        button = type("Button", (), {})()
        button.id = button_id
        button.location = location
        button.bitmap = normal_bitmap
        button.dis_bitmap = disabled_bitmap
        button.name = name
        button.rect = (0, 0, 0, 0)
        button.cur_state = AUI_BUTTON_STATE_NORMAL
        self._buttons.append(button)
        return button

    def CloneButtons(self):
        """Retourne une copie de la liste des boutons.

        Returns:
            list: Nouvelle liste contenant les mêmes boutons.
        """
        return list(self._buttons)

    def RemoveButton(self, button_id):
        """Supprime tous les boutons ayant l'identifiant donné.

        Args:
            button_id (int): Identifiant des boutons à retirer.
        """
        self._buttons = [b for b in self._buttons if b.id != button_id]

    def GetTabOffset(self):
        """Retourne le décalage horizontal de la barre d'onglets.

        Returns:
            int: Décalage en pixels.
        """
        return self._tab_offset

    def SetTabOffset(self, offset):
        """Définit le décalage horizontal de la barre d'onglets.

        Args:
            offset (int): Décalage en pixels.
        """
        self._tab_offset = offset

    def Render(self, raw_dc=None, wnd=None):
        """Dessine les onglets (non implémenté).

        Le rendu est assuré par ``ttk.Notebook``.

        Args:
            raw_dc: Contexte de dessin wx (non utilisé).
            wnd: Fenêtre wx (non utilisée).

        Returns:
            None
        """
        return None

    def IsTabVisible(self, tab_page, tab_offset, dc=None, wnd=None):
        """Indique si un onglet est visible.

        Dans cette version, un onglet est visible s'il n'est pas masqué ;
        le décalage et le contexte de dessin ne sont pas pris en compte.

        Args:
            tab_page: Objet d'information de la page.
            tab_offset (int): Décalage (non utilisé).
            dc: Contexte de dessin (non utilisé).
            wnd: Fenêtre (non utilisée).

        Returns:
            bool: ``True`` si la page n'est pas masquée.
        """
        return not getattr(tab_page, "hidden", False)

    def MakeTabVisible(self, tab_page, win=None):
        """Fait défiler la barre pour rendre un onglet visible (non implémenté).

        ``ttk.Notebook`` gère lui-même le défilement, donc cette méthode
        ne fait rien et renvoie toujours ``True``.

        Args:
            tab_page: Objet d'information de la page.
            win: Fenêtre (non utilisée).

        Returns:
            bool: Toujours ``True``.
        """
        return True

    def TabHitTest(self, x, y):
        """Retourne l'onglet situé au point donné (non implémenté).

        Args:
            x (int): Coordonnée horizontale.
            y (int): Coordonnée verticale.

        Returns:
            int: Toujours ``-1``.
        """
        return -1
        # if not self._rect.Contains((x,y)):
        #    return None

        # btn = self.ButtonHitTest(x, y)
        # if btn:
        #     if btn in self._buttons:
        #         return None

        # for i in range(self._tab_offset, len(self._pages)):
        #     page = self._pages[i]

        #     if page.hidden:
        #         continue

        #     if page.rect.Contains((x,y)):
        #         return page.window

        # return None

    def ButtonHitTest(self, x, y, state_flags=0):
        """Retourne le bouton situé au point donné (non implémenté).

        Args:
            x (int): Coordonnée horizontale.
            y (int): Coordonnée verticale.
            state_flags (int): Drapeaux d'état (non utilisés).

        Returns:
            None: Toujours ``None``.
        """
        return None

    def DoShowHide(self):
        """Synchronise la visibilité des pages avec le ``ttk.Notebook``.

        Pour chaque page ayant un widget :

        - si la page est masquée, elle est retirée du Notebook (``hide``) ;
        - sinon, elle est ajoutée (``add``) avec son titre.

        Les erreurs ``tk.TclError`` sont ignorées : elles surviennent par
        exemple quand on demande de masquer une page qui n'est pas dans le
        Notebook, et ne doivent pas interrompre la boucle.
        """
        for page in self._pages:
            window = getattr(page, "window", None)
            if window is None:
                continue
            try:
                if getattr(page, "hidden", False):
                    self._auiNotebook._notebook.hide(window)
                else:
                    # add() sur une page déjà présente la réaffiche et met à jour son texte.
                    self._auiNotebook._notebook.add(
                        window, text=getattr(page, "caption", "")
                    )
            except tk.TclError:
                pass


class AuiTabCtrl(ttk.Frame, AuiTabContainer):
    """Adaptateur ttk conservant le nom historique AuiTabCtrl.
    
    Hérite à la fois de ``ttk.Frame`` (pour être un widget Tk) et de
    :class:`AuiTabContainer` (pour la logique des pages). Il relaie les
    événements souris et clavier du ``ttk.Notebook`` vers ses propres
    gestionnaires.
    """

    def __init__(self, parent, id=-1, pos=None, size=None, style=None):
        """Crée le cadre et s'attache au Notebook du parent.

        Args:
            parent (AuiNotebook): Carnet propriétaire. Il doit exposer
                ``_notebook``. Si ce n'est pas le cas, aucun événement n'est relayé.
            id (int): Identifiant wx d'origine (non utilisé).
            pos: Position wx d'origine (non utilisée).
            size: Taille wx d'origine (non utilisée).
            style: Styles wx d'origine (non utilisés).
        """
        ttk.Frame.__init__(self, parent)
        AuiTabContainer.__init__(self, parent)
        self._click_pt = (-1, -1)
        self._is_dragging = False
        self._hover_button = None
        self._pressed_button = None
        self._notebook = getattr(parent, "_notebook", None)
        if self._notebook is not None:
            # add="+" ajoute ces liaisons sans écraser celles déjà posées sur le Notebook.
            self._notebook.bind("<Button-1>", self.OnLeftDown, add="+")
            self._notebook.bind("<ButtonRelease-1>", self.OnLeftUp, add="+")
            self._notebook.bind("<Motion>", self.OnMotion, add="+")

    def IsDragging(self):
        """Indique si un glisser-déposer d'onglet est en cours.

        Returns:
            bool: ``True`` pendant un glissement.
        """
        return self._is_dragging

    def GetDefaultBorder(self):
        """Retourne l'épaisseur de bordure par défaut.

        Returns:
            int: Épaisseur en pixels.
        """
        return 1

    def OnPaint(self, event=None):
        """Gestionnaire de peinture (non implémenté, rendu par ttk).

        Args:
            event (tk.Event, optional): Événement de peinture (non utilisé).

        Returns:
            None
        """
        return None

    def OnEraseBackground(self, event=None):
        """Neutralise l'effacement du fond pour éviter le scintillement.

        Args:
            event (tk.Event, optional): Événement d'effacement (non utilisé).
        """
        pass

    def DoGetBestSize(self):
        """Retourne la taille préférée de la barre d'onglets.

        Returns:
            tuple[int, int]: Largeur et hauteur, ``(400, 30)``.
        """
        return (400, 30)

    def OnSize(self, event=None):
        """Gestionnaire de redimensionnement (non implémenté).

        Args:
            event (tk.Event, optional): Événement de taille (non utilisé).
        """
        # TODO
        pass

    def OnLeftDown(self, event):
        """Mémorise le point de clic gauche et donne le focus au widget.

        Args:
            event (tk.Event): Événement ``<Button-1>`` du Notebook.
        """
        self._click_pt = (event.x, event.y)
        self.focus_set()

    def OnCaptureLost(self, event=None):
        """Annule le glissement quand la capture de la souris est perdue.

        Args:
            event (tk.Event, optional): Événement de perte de capture (non utilisé).
        """
        self._is_dragging = False

    def OnLeftUp(self, event):
        """Termine un éventuel glissement au relâchement du bouton gauche.

        Args:
            event (tk.Event): Événement ``<ButtonRelease-1>``.
        """
        self._is_dragging = False

    def OnMiddleUp(self, event):
        """Gestionnaire du relâchement du bouton central (non implémenté).

        Args:
            event (tk.Event): Événement souris (non utilisé).
        """
        # TODO
        pass

    def OnMiddleDown(self, event):
        """Gestionnaire de l'appui sur le bouton central (non implémenté).

        Args:
            event (tk.Event): Événement souris (non utilisé).
        """
        # TODO
        pass

    def OnRightUp(self, event):
        """Gestionnaire du relâchement du bouton droit (non implémenté).

        Args:
            event (tk.Event): Événement souris (non utilisé).
        """
        # TODO
        pass

    def OnRightDown(self, event):
        """Gestionnaire de l'appui sur le bouton droit (non implémenté).

        Args:
            event (tk.Event): Événement souris (non utilisé).
        """
        # TODO
        pass

    def OnLeftDClick(self, event):
        """Gestionnaire du double-clic gauche (non implémenté).

        Args:
            event (tk.Event): Événement souris (non utilisé).
        """
        # TODO
        pass

    def OnMotion(self, event):
        """Gestionnaire du déplacement de souris (non implémenté).

        Args:
            event (tk.Event): Événement ``<Motion>`` (non utilisé).
        """
        # TODO
        pass

    def GetPointedToTab(self):
        """Retourne l'onglet situé au dernier point de clic.

        Returns:
            int: Index de l'onglet, ou ``-1`` (toujours, car :meth:`TabHitTest`
            n'est pas implémenté).
        """
        return self.TabHitTest(*self._click_pt)

    def RestartTooltipTimer(self, wnd):
        """Relance le minuteur d'infobulle.

        Dans cette version, il arrête simplement le minuteur existant.

        Args:
            wnd: Fenêtre (non utilisée).
        """
        # TODO
        self.StopTooltipTimer()

    def StopTooltipTimer(self):
        """Arrête le minuteur d'infobulle (non implémenté)."""
        # TODO
        pass

    def OnEnterWindow(self, event):
        """Gestionnaire d'entrée du pointeur (non implémenté).

        Args:
            event (tk.Event): Événement ``<Enter>`` (non utilisé).
        """
        pass

    def ShowTooltip(self):
        """Affiche l'infobulle (non implémenté)."""
        pass

    def OnLeaveWindow(self, event):
        """Gestionnaire de sortie du pointeur : arrête l'infobulle.

        Args:
            event (tk.Event): Événement ``<Leave>`` (non utilisé).
        """
        self.StopTooltipTimer()

    def OnButton(self, event):
        """Gestionnaire de clic sur un bouton de la barre (non implémenté).

        Args:
            event (tk.Event): Événement souris (non utilisé).
        """
        pass

    def OnSetFocus(self, event):
        """Gestionnaire de prise de focus (non implémenté).

        Args:
            event (tk.Event): Événement ``<FocusIn>`` (non utilisé).
        """
        pass

    def OnKillFocus(self, event):
        """Gestionnaire de perte de focus (non implémenté).

        Args:
            event (tk.Event): Événement ``<FocusOut>`` (non utilisé).
        """
        pass

    def OnKeyDown(self, event):
        """Change d'onglet avec les flèches gauche et droite.

        Args:
            event (tk.Event): Événement clavier.

        Returns:
            str: Toujours ``"break"`` pour empêcher le traitement par défaut de Tk.
        """
        # Seules les flèches gauche et droite sont traitées, mais "break"
        # est renvoyé pour toute touche (voir la remarque ci-dessous).
        if event.keysym in ("Left", "Right") and self._auiNotebook is not None:
            self._auiNotebook.AdvanceSelection(event.keysym == "Right")
        return "break"

    def OnKeyDown2(self, event):
        """Alias de :meth:`OnKeyDown`, conservé pour compatibilité wx.

        Args:
            event (tk.Event): Événement clavier.

        Returns:
            str: Résultat de :meth:`OnKeyDown`.
        """
        return self.OnKeyDown(event)


def _inside(rect, x, y):
    """Teste si un point se trouve à l'intérieur d'un rectangle.

    Les bords sont inclus. Le rectangle peut être un objet avec les attributs
    ``x``, ``y``, ``width`` et ``height`` (comme ``wx.Rect``), ou un tuple
    ``(x, y, largeur, hauteur)``.

    Args:
        rect: Rectangle sous forme d'objet ou de tuple.
        x (int): Coordonnée horizontale du point.
        y (int): Coordonnée verticale du point.

    Returns:
        bool: ``True`` si le point est dans le rectangle (bords inclus).
    """
    # Normalisation : on accepte un objet type wx.Rect ou un tuple.
    a, b, c, d = (
        (rect.x, rect.y, rect.width, rect.height) if hasattr(rect, "x") else rect
    )
    return a <= x <= a + c and b <= y <= b + d
