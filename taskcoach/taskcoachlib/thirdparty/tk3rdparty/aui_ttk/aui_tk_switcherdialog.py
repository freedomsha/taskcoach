# -*- coding: utf-8 -*-
"""Sélecteur d'onglets AUI adapté à Tkinter.

Ce module porte les classes de la boîte de dialogue de sélection
(Ctrl+Tab) de wxWidgets/AUI vers Tkinter. Il fournit :

- ``SwitcherItem`` : un élément de la liste (titre, nom, description, etc.).
- ``SwitcherItems`` : la collection d'éléments et son état (sélection, couleurs, police).
- ``MultiColumnListCtrl`` : le widget Canvas qui affiche et gère la liste.
- ``SwitcherDialog`` : la fenêtre modale (``Toplevel``) qui héberge la liste.

Les noms de méthodes reprennent l'API wxPython d'origine afin de
faciliter la migration du code de Task Coach.
"""
# Quelques remarques sur le code, que vous pourrez traiter à part si vous le souhaitez :

# OnKey ne retourne rien dans le cas par défaut, ce qui est correct mais pourrait être explicité avec return None.
# OnPaint utilise des dimensions fixes (400 × 30) alors que CalculateItemSize renvoie (180, 28). Les deux valeurs ne sont pas cohérentes.
# SwitcherItem.Copy fait une copie superficielle : _font et _bitmap restent partagés entre les copies, ce qui est généralement voulu pour des objets Tk, mais à garder en tête.
# SetSelectionByName lève ValueError si le nom est absent, ce qui n’est pas documenté dans l’API wx d’origine.

import copy
import tkinter as tk
from tkinter import font as tkfont


class SwitcherItem:
    """Élément affichable dans le sélecteur.

    Chaque élément représente un onglet ou un groupe. Il stocke ses
    propriétés d'affichage (titre, couleur, police, icône) ainsi que sa
    position calculée lors du dessin (``_rect``).

    Les setters retournent ``self`` pour permettre le chaînage, par
    exemple ``SwitcherItem().SetTitle("a").SetName("a")``.
    """
    def __init__(self, item=None):
        """Initialise l'élément avec des valeurs par défaut.

        Args:
            item (SwitcherItem, optional): Élément source à copier.
                Si fourni, les attributs sont copiés via :meth:`Copy`.
        """
        self._id = 0
        self._isGroup = False
        self._breakColumn = False
        self._rowPos = 0
        self._colPos = 0
        self._window = None
        self._description = ""
        self._textColour = "#000000"
        self._bitmap = None
        self._font = None
        self._title = ""
        self._name = ""
        self._rect = (0, 0, 0, 0)
        if item:
            self.Copy(item)

    def Copy(self, item):
        """Copie superficielle des attributs d'un autre élément.

        Args:
            item (SwitcherItem): Élément dont on copie les attributs.

        Returns:
            SwitcherItem: ``self``, pour le chaînage.
        """
        # copy.copy évite de partager le dictionnaire d'attributs de
        # l'élément source ; les objets référencés (police, fenêtre)
        # restent partagés, ce qui est voulu.
        self.__dict__.update(copy.copy(item.__dict__))
        return self

    def SetTitle(self, v):
        """Définit le titre affiché.

        Args:
            v (str): Le titre.

        Returns:
            SwitcherItem: ``self``.
        """
        self._title = v
        return self

    def GetTitle(self):
        """Retourne le titre affiché.

        Returns:
            str: Le titre.
        """
        return self._title

    def SetName(self, v):
        """Définit le nom interne, utilisé pour retrouver l'élément.

        Args:
            v (str): Le nom interne (identifiant unique de l'onglet).

        Returns:
            SwitcherItem: ``self``.
        """
        self._name = v
        return self

    def GetName(self):
        """Retourne le nom interne de l'élément.

        Returns:
            str: Le nom interne.
        """
        return self._name

    def SetDescription(self, v):
        """Définit la description associée à l'élément.

        Args:
            v (str): Texte de description.

        Returns:
            SwitcherItem: ``self``.
        """
        self._description = v
        return self

    def GetDescription(self):
        """Retourne la description de l'élément.

        Returns:
            str: Texte de description.
        """
        return self._description

    def SetId(self, v):
        """Définit l'identifiant numérique de l'élément.

        Args:
            v (int): Identifiant.

        Returns:
            SwitcherItem: ``self``.
        """
        self._id = v
        return self

    def GetId(self):
        """Retourne l'identifiant numérique de l'élément.

        Returns:
            int: Identifiant.
        """
        return self._id

    def SetIsGroup(self, v):
        """Marque ou non l'élément comme groupe.

        Args:
            v (bool): ``True`` si l'élément est un groupe.

        Returns:
            SwitcherItem: ``self``.
        """
        self._isGroup = v
        return self

    def GetIsGroup(self):
        """Indique si l'élément est un groupe.

        Returns:
            bool: ``True`` si c'est un groupe.
        """
        return self._isGroup

    def BreakColumn(self, v=True):
        """Demande un saut de colonne avant cet élément.

        Args:
            v (bool): ``True`` pour activer le saut de colonne.

        Returns:
            SwitcherItem: ``self``.
        """
        self._breakColumn = v
        return self

    def GetBreakColumn(self):
        """Indique si un saut de colonne est demandé avant cet élément.

        Returns:
            bool: ``True`` si un saut de colonne est demandé.
        """
        return self._breakColumn

    def SetRect(self, v):
        """Enregistre le rectangle de l'élément à l'écran.

        Args:
            v (tuple[int, int, int, int]): Rectangle ``(x, y, largeur, hauteur)``.

        Returns:
            SwitcherItem: ``self``.
        """
        self._rect = v
        return self

    def GetRect(self):
        """Retourne le rectangle de l'élément à l'écran.

        Returns:
            tuple[int, int, int, int]: Rectangle ``(x, y, largeur, hauteur)``.
        """
        return self._rect

    def SetTextColour(self, v):
        """Définit la couleur du texte de l'élément.

        Args:
            v (str): Couleur au format Tk (ex. ``"#000000"``).

        Returns:
            SwitcherItem: ``self``.
        """
        self._textColour = v
        return self

    def GetTextColour(self):
        """Retourne la couleur du texte de l'élément.

        Returns:
            str: Couleur au format Tk.
        """
        return self._textColour

    def SetFont(self, v):
        """Définit la police de l'élément.

        Args:
            v (tkinter.font.Font | None): Police Tk, ou ``None`` pour la police par défaut.

        Returns:
            SwitcherItem: ``self``.
        """
        self._font = v
        return self

    def GetFont(self):
        """Retourne la police de l'élément.

        Returns:
            tkinter.font.Font | None: La police, ou ``None``.
        """
        return self._font

    def SetBitmap(self, v):
        """Définit l'icône de l'élément.

        Args:
            v (tk.PhotoImage | None): Image associée, ou ``None``.

        Returns:
            SwitcherItem: ``self``.
        """
        self._bitmap = v
        return self

    def GetBitmap(self):
        """Retourne l'icône de l'élément.

        Returns:
            tk.PhotoImage | None: Image associée, ou ``None``.
        """
        return self._bitmap

    def SetRowPos(self, v):
        """Définit la ligne de l'élément dans la disposition.

        Args:
            v (int): Numéro de ligne.

        Returns:
            SwitcherItem: ``self``.
        """
        self._rowPos = v
        return self

    def GetRowPos(self):
        """Retourne la ligne de l'élément dans la disposition.

        Returns:
            int: Numéro de ligne.
        """
        return self._rowPos

    def SetColPos(self, v):
        """Définit la colonne de l'élément dans la disposition.

        Args:
            v (int): Numéro de colonne.

        Returns:
            SwitcherItem: ``self``.
        """
        self._colPos = v
        return self

    def GetColPos(self):
        """Retourne la colonne de l'élément dans la disposition.

        Returns:
            int: Numéro de colonne.
        """
        return self._colPos

    def SetWindow(self, v):
        """Associe une fenêtre à l'élément.

        Args:
            v (tk.Widget | None): Widget associé, ou ``None``.

        Returns:
            SwitcherItem: ``self``.
        """
        self._window = v
        return self

    def GetWindow(self):
        """Retourne la fenêtre associée à l'élément.

        Returns:
            tk.Widget | None: Widget associé, ou ``None``.
        """
        return self._window


class SwitcherItems:
    """Collection d'éléments du sélecteur et paramètres d'affichage.

    Gère la liste ordonnée des :class:`SwitcherItem`, l'index de la
    sélection courante et les couleurs ou polices utilisées pour le dessin.
    """
    def __init__(self, items=None):
        """Initialise une collection vide avec les réglages par défaut.

        Args:
            items (SwitcherItems, optional): Collection source à copier
                via :meth:`Copy`.
        """
        self._selection = -1
        self._rowCount = 10
        self._columnCount = 0
        self._backgroundColour = "#ffffff"
        self._textColour = "#000000"
        self._selectionColour = "#c1d2ee"
        self._selectionOutlineColour = "#316ac5"
        self._itemFont = tkfont.Font(family="TkDefaultFont", size=9)
        self._items = []
        if items:
            self.Copy(items)

    def Copy(self, items):
        """Copie les réglages et les éléments d'une autre collection.

        Les éléments sont recopiés un à un, de sorte que modifier la
        copie ne modifie pas la collection d'origine.

        Args:
            items (SwitcherItems): Collection source.

        Returns:
            SwitcherItems: ``self``.
        """
        self._selection = items._selection
        self._rowCount = items._rowCount
        self._columnCount = items._columnCount
        # Recopie de chaque élément : les listes ne doivent pas être partagées.
        self._items = [SwitcherItem(i) for i in items._items]
        return self

    def AddItem(self, titleOrItem, name="", id=0, bitmap=None):
        """Ajoute un élément à la fin de la liste.

        Deux usages sont possibles : passer un titre (et les autres
        paramètres), ou passer directement un :class:`SwitcherItem`
        existant, qui sera copié.

        Args:
            titleOrItem (str | SwitcherItem): Titre de l'élément, ou élément à copier.
            name (str): Nom interne de l'élément.
            id (int): Identifiant numérique.
            bitmap (tk.PhotoImage | None): Icône de l'élément.

        Returns:
            SwitcherItem: L'élément ajouté.
        """
        # Deux chemins selon le type du premier argument : copie d'un
        # élément existant, ou création à partir des paramètres.
        item = (
            SwitcherItem(titleOrItem)
            if isinstance(titleOrItem, SwitcherItem)
            else SwitcherItem()
            .SetTitle(titleOrItem)
            .SetName(name)
            .SetId(id)
            .SetBitmap(bitmap)
        )
        self._items.append(item)
        return item

    def AddGroup(self, title, name="", id=0, bitmap=None):
        """Ajoute un élément marqué comme groupe.

        Args:
            title (str): Titre du groupe.
            name (str): Nom interne du groupe.
            id (int): Identifiant numérique.
            bitmap (tk.PhotoImage | None): Icône du groupe.

        Returns:
            SwitcherItem: L'élément de groupe ajouté.
        """
        return self.AddItem(title, name, id, bitmap).SetIsGroup(True)

    def Clear(self):
        """Supprime tous les éléments et réinitialise la sélection."""
        self._items.clear()
        self._selection = -1

    def FindItemByName(self, name):
        """Recherche un élément par son nom interne.

        Args:
            name (str): Nom interne recherché.

        Returns:
            SwitcherItem | None: Le premier élément trouvé, ou ``None``.
        """
        return next((i for i in self._items if i.GetName() == name), None)

    def FindItemById(self, id):
        """Recherche un élément par son identifiant numérique.

        Args:
            id (int): Identifiant recherché.

        Returns:
            SwitcherItem | None: Le premier élément trouvé, ou ``None``.
        """
        return next((i for i in self._items if i.GetId() == id), None)

    def SetSelection(self, sel):
        """Définit l'index de l'élément sélectionné.

        Args:
            sel (int): Index dans la liste, ou ``-1`` pour aucune sélection.
        """
        self._selection = sel

    def SetSelectionByName(self, name):
        """Sélectionne l'élément portant le nom donné.

        Args:
            name (str): Nom interne de l'élément à sélectionner.

        Raises:
            ValueError: Si aucun élément ne porte ce nom.
        """
        # FindItemByName renvoie l'objet ; index() recherche sa position.
        # Lève ValueError si l'objet est None (nom introuvable).
        self._selection = self._items.index(self.FindItemByName(name))

    def GetSelection(self):
        """Retourne l'index de l'élément sélectionné.

        Returns:
            int: Index de la sélection, ou ``-1`` si aucune.
        """
        return self._selection

    def GetItem(self, i):
        """Retourne l'élément à l'index donné.

        Args:
            i (int): Index de l'élément.

        Returns:
            SwitcherItem: L'élément demandé.

        Raises:
            IndexError: Si l'index est hors limites.
        """
        return self._items[i]

    def GetItemCount(self):
        """Retourne le nombre d'éléments.

        Returns:
            int: Nombre d'éléments dans la collection.
        """
        return len(self._items)

    def SetRowCount(self, v):
        """Définit le nombre de lignes visibles.

        Args:
            v (int): Nombre de lignes.
        """
        self._rowCount = v

    def GetRowCount(self):
        """Retourne le nombre de lignes visibles.

        Returns:
            int: Nombre de lignes.
        """
        return self._rowCount

    def SetColumnCount(self, v):
        """Définit le nombre de colonnes.

        Args:
            v (int): Nombre de colonnes.
        """
        self._columnCount = v

    def GetColumnCount(self):
        """Retourne le nombre de colonnes.

        Returns:
            int: Nombre de colonnes.
        """
        return self._columnCount

    def SetBackgroundColour(self, v):
        """Définit la couleur de fond des éléments non sélectionnés.

        Args:
            v (str): Couleur au format Tk.
        """
        self._backgroundColour = v

    def GetBackgroundColour(self):
        """Retourne la couleur de fond des éléments non sélectionnés.

        Returns:
            str: Couleur au format Tk.
        """
        return self._backgroundColour

    def SetTextColour(self, v):
        """Définit la couleur de texte par défaut.

        Args:
            v (str): Couleur au format Tk.
        """
        self._textColour = v

    def GetTextColour(self):
        """Retourne la couleur de texte par défaut.

        Returns:
            str: Couleur au format Tk.
        """
        return self._textColour

    def SetSelectionColour(self, v):
        """Définit la couleur de fond de l'élément sélectionné.

        Args:
            v (str): Couleur au format Tk.
        """
        self._selectionColour = v

    def GetSelectionColour(self):
        """Retourne la couleur de fond de l'élément sélectionné.

        Returns:
            str: Couleur au format Tk.
        """
        return self._selectionColour

    def SetSelectionOutlineColour(self, v):
        """Définit la couleur du contour de l'élément sélectionné.

        Args:
            v (str): Couleur au format Tk.
        """
        self._selectionOutlineColour = v

    def GetSelectionOutlineColour(self):
        """Retourne la couleur du contour de l'élément sélectionné.

        Returns:
            str: Couleur au format Tk.
        """
        return self._selectionOutlineColour

    def SetItemFont(self, v):
        """Définit la police utilisée pour les éléments.

        Args:
            v (tkinter.font.Font): Police Tk.
        """
        self._itemFont = v

    def GetItemFont(self):
        """Retourne la police utilisée pour les éléments.

        Returns:
            tkinter.font.Font: Police Tk.
        """
        return self._itemFont

    def PaintItems(self, dc, win):
        """Dessine les éléments.

        Non implémenté : le dessin est assuré par
        :meth:`MultiColumnListCtrl.OnPaint`.

        Args:
            dc: Contexte de dessin (non utilisé en Tkinter).
            win: Widget cible (non utilisé en Tkinter).
        """
        pass

    def CalculateItemSize(self, dc):
        """Retourne la taille d'un élément.

        La taille est fixe pour l'instant.

        Args:
            dc: Contexte de dessin (non utilisé).

        Returns:
            tuple[int, int]: Largeur et hauteur en pixels, ``(180, 28)``.
        """
        return (180, 28)

    def GetIndexForFocus(self):
        """Retourne l'index qui doit recevoir le focus.

        Returns:
            int: L'index sélectionné, ou ``0`` si aucune sélection.
        """
        # Si rien n'est sélectionné, le focus revient au premier élément.
        return self._selection if self._selection >= 0 else 0


class MultiColumnListCtrl(tk.Canvas):
    """Widget Canvas qui affiche la liste d'éléments et gère la navigation.

    Remplace le ``wx.ListCtrl`` multi-colonnes d'origine. Chaque élément
    occupe une ligne de 30 pixels de hauteur. La sélection se fait à la
    souris ou aux flèches haut et bas.
    """
    def __init__(
        self,
        parent,
        aui_manager=None,
        id=-1,
        pos=None,
        size=None,
        style=None,
        validator=None,
        name="MultiColumnListCtrl",
    ):
        """Crée le Canvas et lie les événements souris et clavier.

        Args:
            parent (tk.Widget): Widget parent.
            aui_manager: Gestionnaire AUI d'origine (non utilisé).
            id (int): Identifiant wx d'origine (non utilisé).
            pos: Position wx d'origine (non utilisée).
            size: Taille wx d'origine (non utilisée).
            style: Styles wx d'origine (non utilisés).
            validator: Validateur wx d'origine (non utilisé).
            name (str): Nom du widget.
        """
        super().__init__(parent, highlightthickness=0)
        self._items = SwitcherItems()
        self._extraNavigationKey = None
        self._modifierKey = None
        self._transparency = 255
        self.bind("<Button-1>", self.OnMouseEvent)
        self.bind("<Key>", self.OnKey)

    def DoGetBestSize(self):
        """Retourne la taille préférée du widget.

        Returns:
            tuple[int, int]: Largeur et hauteur, ``(400, 300)``.
        """
        return (400, 300)

    def OnEraseBackground(self, event):
        """Neutralise l'effacement du fond pour éviter le scintillement.

        Args:
            event: Événement d'effacement (non utilisé).
        """
        pass

    def OnPaint(self, event=None):
        """Redessine toute la liste.

        Efface le Canvas, puis dessine pour chaque élément un rectangle
        de fond et un texte. L'élément sélectionné reçoit la couleur de
        sélection et son contour. Le rectangle de chaque élément est
        mémorisé dans ``_rect`` pour les calculs de clic.

        Args:
            event: Événement déclencheur (non utilisé).
        """
        self.delete("all")
        for n, i in enumerate(self._items._items):
            # Chaque ligne fait 30 px ; y est le haut de la ligne n.
            y = n * 30
            i.SetRect((0, y, 400, 30))
            # Couleur de fond et contour dépendent de la sélection.
            self.create_rectangle(
                0,
                y,
                400,
                y + 30,
                fill=(
                    self._items.GetSelectionColour()
                    if n == self._items.GetSelection()
                    else self._items.GetBackgroundColour()
                ),
                outline=(
                    self._items.GetSelectionOutlineColour()
                    if n == self._items.GetSelection()
                    else ""
                ),
            )
            # Texte centré verticalement dans la ligne (y + 15).
            self.create_text(
                8, y + 15, text=i.GetTitle(), anchor="w", fill=i.GetTextColour()
            )

    def OnMouseEvent(self, event):
        """Sélectionne l'élément sous le clic de souris.

        Args:
            event (tk.Event): Événement ``<Button-1>``.
        """
        # Conversion de la coordonnée y en index de ligne, bornée à la liste.
        self._items.SetSelection(
            max(0, min(self._items.GetItemCount() - 1, event.y // 30))
        )
        self.OnPaint()
        self.GenerateSelectionEvent()

    def OnChar(self, event):
        """Redirige la saisie caractère vers :meth:`OnKey`.

        Args:
            event (tk.Event): Événement clavier.

        Returns:
            str | None: Le résultat de :meth:`OnKey`.
        """
        return self.OnKey(event)

    def OnKey(self, event):
        """Gère les touches Haut et Bas pour changer la sélection.

        Args:
            event (tk.Event): Événement clavier.

        Returns:
            str | None: ``"break"`` si la touche est traitée, pour empêcher
            le traitement par défaut de Tk ; ``None`` sinon.
        """
        # Seules les flèches haut et bas sont traitées ; les autres touches
        # sont laissées à Tk (la fonction retourne alors None implicitement).
        if event.keysym in ("Up", "Down"):
            self.AdvanceToNextSelectableItem(-1 if event.keysym == "Up" else 1)
            self.OnPaint()
            return "break"

    def AdvanceToNextSelectableItem(self, direction):
        """Déplace la sélection d'un élément vers le haut ou le bas.

        La sélection est bornée au premier et au dernier élément, sans
        revenir au début de la liste.

        Args:
            direction (int): ``-1`` pour monter, ``1`` pour descendre.
        """
        self._items.SetSelection(
            max(
                0,
                min(
                    self._items.GetItemCount() - 1,
                    self._items.GetSelection() + direction,
                ),
            )
        )

    def SetTransparency(self, v):
        """Définit la transparence de la fenêtre (conservée pour compatibilité).

        Tkinter ne l'applique pas au Canvas ; la valeur est seulement mémorisée.

        Args:
            v (int): Valeur de transparence, de 0 à 255.
        """
        self._transparency = v

    def GenerateSelectionEvent(self):
        """Émet l'événement virtuel ``<<SwitcherSelection>>``.

        Le dialogue écoute cet événement pour fermer la fenêtre.
        """
        self.event_generate("<<SwitcherSelection>>")

    def CalculateLayout(self, dc):
        """Calcule la disposition des éléments.

        Non implémenté : la disposition est fixe dans :meth:`OnPaint`.

        Args:
            dc: Contexte de dessin (non utilisé).
        """
        pass

    def SetItems(self, v):
        """Remplace la collection d'éléments et redessine la liste.

        Args:
            v (SwitcherItems): Nouvelle collection.
        """
        self._items = v
        self.OnPaint()

    def GetItems(self):
        """Retourne la collection d'éléments.

        Returns:
            SwitcherItems: La collection courante.
        """
        return self._items

    def SetExtraNavigationKey(self, v):
        """Définit une touche de navigation supplémentaire.

        Args:
            v: Touche de navigation (mémorisée, non utilisée).
        """
        self._extraNavigationKey = v

    def GetExtraNavigationKey(self):
        """Retourne la touche de navigation supplémentaire.

        Returns:
            La touche mémorisée, ou ``None``.
        """
        return self._extraNavigationKey

    def SetModifierKey(self, v):
        """Définit la touche modificatrice.

        Args:
            v: Touche modificatrice (mémorisée, non utilisée).
        """
        self._modifierKey = v

    def GetModifierKey(self):
        """Retourne la touche modificatrice.

        Returns:
            La touche mémorisée, ou ``None``.
        """
        return self._modifierKey


class SwitcherDialog(tk.Toplevel):
    """Fenêtre modale de sélection d'onglets.

    Affiche un :class:`MultiColumnListCtrl` dans une ``Toplevel``. La
    fenêtre se ferme à la validation (Entrée ou clic), à l'annulation
    (Échap) ou à la fermeture par le gestionnaire de fenêtres.
    """
    def __init__(
        self,
        items,
        parent=None,
        aui_manager=None,
        id=-1,
        title="Switcher",
        pos=None,
        size=None,
        style=None,
    ):
        """Crée la fenêtre, y place la liste et capte le clavier.

        Args:
            items (SwitcherItems): Collection d'éléments à afficher.
            parent (tk.Widget, optional): Fenêtre parente.
            aui_manager: Gestionnaire AUI d'origine (non utilisé).
            id (int): Identifiant wx d'origine (non utilisé).
            title (str): Titre de la fenêtre.
            pos: Position wx d'origine (non utilisée).
            size: Taille wx d'origine (non utilisée).
            style: Styles wx d'origine (non utilisés).
        """
        super().__init__(parent)
        self.title(title)
        self._items = items
        self._selection = items.GetSelection()
        self._borderColour = "#000000"
        self._list = MultiColumnListCtrl(self)
        self._list.SetItems(items)
        self._list.pack(fill="both", expand=True)
        self._list.bind("<<SwitcherSelection>>", self.OnSelectItem)
        self.bind("<Return>", self.OnSelectItem)
        self.bind("<Escape>", self.OnCloseWindow)
        self.protocol("WM_DELETE_WINDOW", self.OnCloseWindow)
        # grab_set rend la fenêtre modale ; le focus va à la liste pour
        # que les flèches clavier fonctionnent immédiatement.
        self.grab_set()
        self._list.focus_set()

    def OnCloseWindow(self, event=None):
        """Libère la fenêtre modale et détruit le dialogue.

        Args:
            event (tk.Event, optional): Événement déclencheur (non utilisé).
        """
        self.grab_release()
        self.destroy()

    def GetSelection(self):
        """Retourne l'index de l'élément sélectionné.

        Returns:
            int: Index de la sélection.
        """
        return self._items.GetSelection()

    def OnActivate(self, event=None):
        """Gère l'activation de la fenêtre (non implémenté).

        Args:
            event (tk.Event, optional): Événement d'activation (non utilisé).
        """
        pass

    def OnPaint(self, event=None):
        """Redessine la liste.

        Args:
            event (tk.Event, optional): Événement déclencheur, transmis à la liste.
        """
        self._list.OnPaint(event)

    def OnSelectItem(self, event=None):
        """Valide la sélection courante et ferme le dialogue.

        Args:
            event (tk.Event, optional): Événement déclencheur (non utilisé).
        """
        self._selection = self._items.GetSelection()
        self.OnCloseWindow(event)

    def ColourToHexString(self, col):
        """Convertit une couleur en chaîne hexadécimale ``#rrggbb``.

        Sert à la compatibilité avec les couleurs wx, qui sont des tuples RGB.

        Args:
            col (str | tuple[int, int, int]): Couleur sous forme de chaîne
                (retournée telle quelle) ou de tuple ``(r, g, b)``.

        Returns:
            str: Couleur au format ``#rrggbb``.
        """
        if isinstance(col, str):
            return col
        return "#%02x%02x%02x" % tuple(col[:3])

    def ShowDescription(self, i):
        """Retourne la description de l'élément à l'index donné.

        Args:
            i (int): Index de l'élément.

        Returns:
            str: La description, ou une chaîne vide si l'index est hors limites.
        """
        # Garde-fou : un index négatif ou trop grand renvoie "" au lieu
        # de lever IndexError.
        return (
            self._items.GetItem(i).GetDescription()
            if 0 <= i < self._items.GetItemCount()
            else ""
        )

    def SetExtraNavigationKey(self, v):
        """Transmet la touche de navigation supplémentaire à la liste.

        Args:
            v: Touche de navigation.
        """
        self._list.SetExtraNavigationKey(v)

    def GetExtraNavigationKey(self):
        """Retourne la touche de navigation supplémentaire de la liste.

        Returns:
            La touche de navigation, ou ``None``.
        """
        return self._list.GetExtraNavigationKey()

    def SetModifierKey(self, v):
        """Transmet la touche modificatrice à la liste.

        Args:
            v: Touche modificatrice.
        """
        self._list.SetModifierKey(v)

    def GetModifierKey(self):
        """Retourne la touche modificatrice de la liste.

        Returns:
            La touche modificatrice, ou ``None``.
        """
        return self._list.GetModifierKey()

    def SetBorderColour(self, v):
        """Définit la couleur de la bordure du dialogue.

        Mémorisée pour compatibilité ; le dessin de la bordure n'est pas implémenté.

        Args:
            v (str): Couleur au format Tk.
        """
        self._borderColour = v
