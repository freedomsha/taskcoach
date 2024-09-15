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
"""

import wx
# from wx.lib.agw import aui
import wx.lib.agw.aui as aui


class GridCursor:
    """
    Classe utilitaire pour aider lors de l’ajout de contrôles à un GridBagSizer.

    Attributes:
        __columns (int): Le nombre de colonnes dans la grille.
        __nextPosition (tuple): Position suivante pour ajouter un contrôle.
    """

    def __init__(self, columns):
        """
        Initialisez l'instance GridCursor.

        Args:
            columns (int): Le nombre de colonnes dans la grille.
        """
        self.__columns = columns
        self.__nextPosition = (0, 0)

    def __updatePosition(self, colspan):
        """
        Met à jour la position du curseur en tenant compte de colspan.

        Args:
            colspan (int): Nombre de colonnes couvertes(spanned) par le contrôle.
        """
        row, column = self.__nextPosition
        if column == self.__columns - colspan:
            row += 1
            column = 0
        else:
            column += colspan
        self.__nextPosition = (row, column)

    def next(self, colspan=1):
        """
        Obtenez la position suivante pour un contrôle.

        Args:
            colspan (int, optional): Le nombre de colonnes couvertes(spanned) par le contrôle. Defaults à 1.

        Returns:
            tuple: La prochaine position (row, column).
        """
        row, column = self.__nextPosition
        self.__updatePosition(colspan)
        return row, column

    def maxRow(self):
        """
        Obtenir l'index de ligne maximum.

        Returns:
            int: L'index de ligne maximum.
        """
        row, column = self.__nextPosition
        return max(0, row - 1) if column == 0 else row


class BookPage(wx.Panel):
    """
    Une page dans un cahier(notebook).

    Attributes:
        _sizer (wx.GridBagSizer): Le sizer pour organiser les contrôles.
        _columns (int): Le nombre de colonnes dans la grille.
        _position (GridCursor): Le curseur pour les contrôles de positionnement.
        _growableColumn (int): L'index de la colonne extensible.
        _borderWidth (int): La largeur de la bordure autour des contrôles.
    """

    def __init__(self, parent, columns, growableColumn=None, *args, **kwargs):
        """
        Initialise l'instance BookPage.

        Args:
            parent (wx.Window): La fenêtre parente.
            columns (int): Le nombre de colonnes dans la grille.
            growableColumn (int, optional): L'index de la colonne augmentable. Defaults to None.
            *args: Liste d’arguments de longueur variable.
            **kwargs: Arguments de mots clés arbitraires.
        """
        super().__init__(parent, style=wx.TAB_TRAVERSAL, *args, **kwargs)
        self._sizer = wx.GridBagSizer(vgap=5, hgap=5)
        self._columns = columns
        self._position = GridCursor(columns)
        if growableColumn is None:
            self._growableColumn = columns - 1
        else:
            self._growableColumn = growableColumn
        self._borderWidth = 5

    def fit(self):
        """
        Régle le dimensionneur et ajuste le panneau à son contenu.
        """
        self.SetSizerAndFit(self._sizer)

    def __defaultFlags(self, controls):
        """
        Renvoie les indicateurs par défaut pour placer une liste de contrôles.

        Args:
            controls (list): La liste des contrôles.

        Returns:
            list: La liste des indicateurs par défaut.
        """
        labelInFirstColumn = type(controls[0]) in [type(""), type("")]
        # TODO: essayer:
        # labelInFirstColumn = isinstance(controls[0], str)
        flags = []
        for columnIndex in range(len(controls)):
            flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL
            if columnIndex == 0 and labelInFirstColumn:
                flag |= wx.ALIGN_LEFT
            else:
                flag |= wx.ALIGN_RIGHT | wx.EXPAND
            flags.append(flag)
        return flags

    def __determineFlags(self, controls, flagsPassed):
        """
        Renvoie une liste fusionnée d'indicateurs en remplaçant les indicateurs par défaut par les indicateurs transmis par l'appelant.

        Args:
            controls (list): La liste des contrôles.
            flagsPassed (list or None): La liste des indicateurs transmis par l'appelant.

        Returns:
            list: La liste des drapeaux fusionnés(merged).
        """
        flagsPassed = flagsPassed or [None] * len(controls)
        # TODO : try to replaced by:
        # if not isinstance(flagsPassed, list):
        #     flagsPassed = [flagsPassed] * len(controls)
        #
        defaultFlags = self.__defaultFlags(controls)
        return [
            defaultFlag if flagPassed is None else flagPassed
            for flagPassed, defaultFlag in zip(flagsPassed, defaultFlags)
        ]  # TypeError: 'Alignment' object is not iterable

    def addEntry(self, *controls, **kwargs):
        """
        Ajoute un certain nombre de contrôles à la page. Tous les contrôles sont placés sur une seule ligne et forment ensemble une seule entrée.

        Par exemple. une étiquette, un champ de texte et une étiquette explicative. Les indicateurs par défaut
        pour placer les contrôles peuvent être remplacés en
        fournissant un paramètre de mot-clé « flags ». les drapeaux doivent être une liste de drapeaux
        (wx.ALIGN_LEFT et autres). La liste peut
        contenir Aucun pour les contrôles qui doivent être placés à l'aide de l'indicateur par défaut
        . Si la liste des indicateurs est plus courte que le nombre de contrôles
        , elle est étendue avec autant de « Aucun » que nécessaire.
        Ainsi, addEntry(aLabel, aTextCtrl, flags=[None, wx.ALIGN_LEFT])
        le fera. placez l'étiquette avec le drapeau par défaut et placera le textCtrl
        aligné à gauche.

        Args:
            *controls: Liste de contrôles de longueur variable.
            **kwargs: Arguments de mots clés arbitraires, notamment:
                - flags (list): Liste des drapeaux pour placer les contrôles.
                - growable (bool): Indique si la ligne doit pouvoir être développée.
        """
        flags = self.__determineFlags(controls, kwargs.get("flags", None))
        controls = [
            self.__createStaticTextControlIfNeeded(control)
            for control in controls
            if control is not None
        ]
        lastColumnIndex = len(controls) - 1
        for columnIndex, control in enumerate(controls):
            self.__addControl(
                columnIndex,
                control,
                flags[columnIndex],
                lastColumn=columnIndex == lastColumnIndex,
            )
            if columnIndex > 0:
                control.MoveAfterInTabOrder(controls[columnIndex - 1])
        if kwargs.get("growable", False):
            self._sizer.AddGrowableRow(self._position.maxRow())
        # Move growable column definition here
        # There are asserts to fail if the column is already
        # marked growable or if there is no column yet created
        if (
            self._growableColumn > -1
            and self._growableColumn >= lastColumnIndex
        ):
            self._sizer.AddGrowableCol(self._growableColumn)
            self._growableColumn = -1

    def addLine(self):
        """
        Ajoutez une ligne horizontale à la page.
        """
        line = wx.StaticLine(self)
        self.__addControl(
            0, line, flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL, lastColumn=True
        )

    def __addControl(self, columnIndex, control, flag, lastColumn):
        """
        Ajoutez un contrôle au sizer.

        Args:
            columnIndex (int): L'index de la colonne.
            control (wx.Window): Le contrôle à ajouter.
            flag (int): Les drapeaux pour placer le contrôle.
            lastColumn (bool): Si le contrôle est dans la dernière colonne.
        """
        colspan = max(self._columns - columnIndex, 1) if lastColumn else 1
        # position = self._position.next(colspan)
        #
        # # Sortie de débogage pour vérifier les valeurs transmises
        # print(
        #     f"notebook.py:Adding control: {control}, Position: {position}, Span: {(1, colspan)}, Flag: {flag}, Border: {self._borderWidth}"
        # )
        #
        # # Assurez-vous que l'indicateur est un entier
        # if isinstance(flag, tuple):
        #     flag = flag[0]  # Extraire le premier élément s'il s'agit d'un tuple

        self._sizer.Add(
            control,
            # position,
            self._position.next(colspan),
            span=(1, colspan),
            flag=flag,
            border=self._borderWidth,
        )

    def __createStaticTextControlIfNeeded(self, control):
        """
        Créez un contrôle StaticText si le contrôle donné est une chaîne.

        Args:
            control: Le contrôle ou la chaîne.

        Returns:
            wx.Window: Le contrôle.
        """
        if type(control) in [type(""), type("")]:  # TODO: essayer de le remplacer par
            # if isinstance(control, str):
            control = wx.StaticText(self, label=control)
        return control


class BookMixin(object):
    """
    Classe Mixin pour les composants *book.

    Attributes:
        _bitmapSize (tuple): La taille du bitmap.
        pageChangedEvent (str): L'événement pour les changements de page.
    """

    _bitmapSize = (16, 16)
    pageChangedEvent = "Subclass responsibility"

    def __init__(self, parent, *args, **kwargs):
        """
        Initialize the BookMixin instance.

        Args:
            parent (wx.Window): The parent window.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(parent, -1, *args, **kwargs)
        self.Bind(self.pageChangedEvent, self.onPageChanged)

    def __getitem__(self, index):
        """
        Obtenez une page spécifique par index.

        Manière plus pythonique d'obtenir une page spécifique, également utile pour itérer
        sur toutes les pages, par exemple : pour la page du cahier : ...

        Args:
            index (int): L'index de la page.

        Returns:
            wx.Window: La page.

        Raises:
            IndexError: Si l'index est hors de portée.
        """
        if index < self.GetPageCount():
            return self.GetPage(index)
        else:
            raise IndexError

    def onPageChanged(self, event):
        """
        Gérer l’événement de modification de page. Peut être remplacé dans une sous-classe pour faire quelque chose d'utile.

        Args:
            event (wx.Event): Événement de changement de page.
        """
        event.Skip()

    def AddPage(self, page, name, bitmap=None):
        """
        Remplace AddPage pour permettre de spécifier simplement le nom du bitmap.

        Args:
            page (wx.Window): La page à ajouter.
            name (str): Le nom de la page.
            bitmap (str, optional): Le nom du bitmap. La valeur par défaut est Aucun.
        """
        bitmap = wx.ArtProvider.GetBitmap(
            bitmap, wx.ART_MENU, self._bitmapSize
        )
        super().AddPage(page, name, bitmap=bitmap)

    def ok(self, *args, **kwargs):
        """
        Effectuez l'action « ok » pour toutes les pages.

        Args:
            *args: Liste d’arguments de longueur variable.
            **kwargs: Arguments de mots clés arbitraires.
        """
        for page in self:
            page.ok(*args, **kwargs)


class Notebook(BookMixin, aui.AuiNotebook):
    """
    Un Notebook doté de fonctionnalités AUI (Advanced User Interface).

    Attributes:
        pageChangedEvent (str): L'événement pour les changements de page.
    """

    pageChangedEvent = aui.EVT_AUINOTEBOOK_PAGE_CHANGED

    def __init__(self, *args, **kwargs):
        """
        Initialise l'instance Notebook.

        Args:
            *args: Liste d’arguments de longueur variable.
            **kwargs: Arguments de mots clés arbitraires.
        """
        defaultStyle = kwargs.get("agwStyle", aui.AUI_NB_DEFAULT_STYLE)
        kwargs["agwStyle"] = (
            defaultStyle
            & ~aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
            & ~aui.AUI_NB_MIDDLE_CLICK_CLOSE
        )
        super().__init__(*args, **kwargs)
