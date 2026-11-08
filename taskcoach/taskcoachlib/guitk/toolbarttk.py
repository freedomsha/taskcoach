# Points clés et considérations :
#
# Gestion des images :
# L’exemple comprend des espaces réservés pour le chargement d’images à l’aide de PIL (Pillow).
# Vous devrez installer Pillow (pip install Pillow) et adapter la logique de chargement
# et de désactivation des images à votre format d’image spécifique
# et à vos exigences de désactivation.

# createToolBarUICommands :
# Cette méthode, à l’origine dans MainWindow, devra être adaptée
# pour créer des instances de vos sous-classes UICommand compatibles avec Tkinter.
#
# Boîte de dialogue de personnalisation :
# La fonctionnalité ToolBarEditor doit être complètement réimplémentée
# à l’aide des boîtes de dialogue Tkinter.
# uniqueName :
# assurez-vous que vos sous-classes UICommand disposent d’une méthode uniqueName
# qui renvoie un identificateur de chaîne pour chaque commande.
# Ceci est utilisé pour conserver la perspective de la barre d’outils.
# Paramètres :
# L’objet settings (à l’origine pour stocker les paramètres spécifiques à wxPython)
# devra être adapté pour stocker et récupérer les données de configuration
# de la barre d’outils d’une manière compatible avec Tkinter
# (par exemple, en utilisant tkinter.filedialog
# ou un fichier de paramètres personnalisés).

# La solution : Séparer le parent (widget) du contrôleur (logique)
#
# Le constructeur ToolBar utilise son premier argument window à deux fins :
#     Comme parent pour le widget ttk.Frame (dans super().__init__(window, **kwargs)).
#     Comme contrôleur pour obtenir la logique métier (comme getToolBarPerspective()).
#
# Le parent (visuel) doit être self._sizer.
# Le contrôleur (logique) doit être self (l'instance de Viewer,
# ex: Noteviewer, qui a bien la méthode getToolBarPerspective définie dans basetk.py).
#
# Nous devons modifier ToolBar pour qu'il accepte ces deux informations distinctement.
# Modifie le constructeur __init__ de la classe ToolBar
# pour accepter un parent (pour Tkinter) et une window (pour la logique).
import tkinter as tk
from tkinter import ttk
import logging

# from PIL import Image, ImageTk # If you need more image format support
from taskcoachlib.guitk.uicommand import uicommandtk
from taskcoachlib.guitk.uicommand import uicommandcontainertk

from taskcoachlib.thirdparty.tk3rdparty.aui_ttk import aui_tk_constants, tkauitoolbar

# from taskcoachlib.guitk.dialog.toolbartk import ToolBarEditor  # Circular import

log = logging.getLogger(__name__)


class _Toolbar(tkauitoolbar.AuiToolBar):
    """
    Une classe interne qui représente une barre d'outils basée sur la classe AuiToolBar de la bibliothèque wxPython.

    Cette classe est utilisée comme base pour la classe ToolBar, qui ajoute des fonctionnalités de personnalisation à la barre d'outils.

    AuiToolBar est une barre d'outils entièrement dessinée par le propriétaire,
    parfaitement intégrée au système de mise en page AUI. Cela permet le glisser-déposer des barres d'outils,
    le comportement d'ancrage/flottant et la possibilité de définir des éléments de « débordement » dans la barre d'outils elle-même.

    Le thème par défaut utilisé est AuiDefaultToolBarArt, qui offre une apparence moderne et brillante.
    Le thème peut être modifié en appelant AuiToolBar.SetArtProvider.
    """

    def __init__(self, parent, window, text, style):
        #
        # super().__init__(parent, agwStyle=aui.AUI_TB_NO_AUTORESIZE)
        super().__init__(parent, window, text=text)

    def AddLabelTool(self, id, label, bitmap1, bitmap2, kind, **kwargs):
        """Ajoute un outil à la barre d'outils.

        Il s'agit de la version complète d'wx.lib.agw.aui.auibar.AuiToolBar.AddTool.

        Args:
            id:
            label:
            bitmap1:
            bitmap2:
            kind:
            **kwargs:

        Returns:

        """

        long_help_string = kwargs.pop("longHelp", "")
        short_help_string = kwargs.pop("shortHelp", "")
        # bitmap2 = self.MakeDisabledBitmap(bitmap1)
        # TypeError: _Toolbar.MakeDisabledBitmap() takes 1 positional argument but 2 were given
        # Attention ligne 63 déclaration de MakeDisabledBitmap. Ne pas mettre staticmethod.
        # On vérifie bitmap1 avant de tenter de générer bitmap2
        if bitmap1 and not isinstance(bitmap1, str):
            bitmap2 = self.MakeDisabledBitmap(bitmap1)
        else:
            # # Si bitmap1 est une chaîne ou invalide, on utilise NullBitmap
            # # bitmap2 = wx.NullBitmap
            # bitmap2 = tk.PhotoImage.blank  # ?
            bitmap2 = None
            if isinstance(bitmap1, str):
                log.error(
                    f"AddLabelTool: bitmap1 pour '{label}' est une chaîne de caractères : {bitmap1}"
                )
                # bitmap1 = wx.NullBitmap
                bitmap1 = None
        # auibar..AuiToolBar.AddTool ajoute un outil à la barre d'outils. Il s'agit de la version complète de :meth:`AddTool` :
        super().AddTool(
            id,
            label,
            bitmap1,
            bitmap2,
            kind,
            short_help_string,
            long_help_string,
            None,
            None,
        )
        # bitmap2 est un NoneType ! ?
        # File
        # "/home/sylvain/Téléchargements/src/TaskCoach2.7/TaskCoach-future2/lib/python3.12/site-packages/wx/lib/agw/aui/auibar.py", line
        # 1834, in AddTool
        # if not item.disabled_bitmap.IsOk():
        #     ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^
        # AttributeError: 'NoneType' object has no attribute 'IsOk'
        #     def AddTool(self, tool_id, label, bitmap, disabled_bitmap, kind, short_help_string='', long_help_string='', client_data=None, target=None):
        #         """
        #         Ajoute un outil à la barre d'outils. Il s'agit de la version complète de :meth:`AddTool`.
        #
        #         :param integer `tool_id`: an integer by which the tool may be identified in subsequent operations;
        #         :param string `label`: the toolbar tool label;
        #         :param wx.Bitmap `bitmap`: the primary tool bitmap;
        #         :param wx.Bitmap `disabled_bitmap`: the bitmap to use when the tool is disabled. If it is equal to
        #          :class:`NullBitmap`, the disabled bitmap is automatically generated by greing the normal one;
        #         :param integer `kind`: the item kind. Can be one of the following:
        #
        #          ========================  =============================
        #          Item Kind                 Description
        #          ========================  =============================
        #          ``ITEM_CONTROL``          The item in the :class:`AuiToolBar` is a control
        #          ``ITEM_LABEL``            The item in the :class:`AuiToolBar` is a text label
        #          ``ITEM_SPACER``           The item in the :class:`AuiToolBar` is a spacer
        #          ``ITEM_SEPARATOR``        The item in the :class:`AuiToolBar` is a separator
        #          ``ITEM_CHECK``            The item in the :class:`AuiToolBar` is a toolbar check item
        #          ``ITEM_NORMAL``           The item in the :class:`AuiToolBar` is a standard toolbar item
        #          ``ITEM_RADIO``            The item in the :class:`AuiToolBar` is a toolbar radio item
        #          ========================  =============================
        #
        #         :param string `short_help_string`: this string is used for the tools tooltip;
        #         :param string `long_help_string`: this string is shown in the statusbar (if any) of the parent
        #          frame when the mouse pointer is inside the tool.
        #         :param PyObject `client_data`: whatever Python object to associate with the toolbar item.
        #         :param `target`: a custom string indicating that an instance of :class:`~wx.lib.agw.aui.framemanager.AuiPaneInfo`
        #          has been minimized into this toolbar.
        #          """

    # def GetToolState(self, toolId):
    def GetToolState(self, tool_id):
        """wx.lib.agw.aui.auibar.AuiToolBar.GetToolToggle indique si un outil est activé ou non.

        Args :
            tool_id (integer) : the toolbar item identifier.
        """
        # Cela s'applique uniquement à un outil qui a été spécifié comme outil toggle(à bascule).
        # return self.GetToolToggled(toolId)
        return self.GetToolToggled(tool_id)

    def SetToolBitmapSize(self, size):
        """Définit la taille par défaut de chaque bitmap d'outil. La taille bitmap par défaut est de 16 x 15 pixels.

        Args :
            size (wx.Size) : The size of the bitmaps in the toolbar.
        """
        self.__size = size
        # TODO : à remplacer par
        # super().SetToolBitmapSize(size)  # ?

    def GetToolBitmapSize(self):
        """Renvoie la taille du bitmap attendue par la barre d'outils.

        La taille bitmap par défaut est de 16 x 15 pixels.
        """
        # return self.__size
        # # TODO : à remplacer par wx.GetToolBitmapSize(self) inclut dans AuiToolBar
        # return self.ToolBar.GetToolBitmapSize()
        # return GetToolBitmapSize(self)
        return super().GetToolBitmapSize()  # existe ? oui

    def GetToolSize(self):
        """Renvoie la taille du bitmap.

        La taille bitmap par défaut est de 16 x 15 pixels.
        """
        return self.__size

    def SetMargins(self, *args):
        """
        Définissez les valeurs à utiliser comme marges pour la barre d'outils.

        Args :

            x (int) : marge gauche, marge droite et valeur de séparation inter-outils ;

            y (int) : marge supérieure, marge inférieure et valeur de séparation inter-outils.

        ou

            left (int) : la marge gauche de la barre d'outils;

            right (int) : la marge droite de la barre d'outils;

            top (int) : la marge supérieure de la barre d'outils;

            bottom (int) : la marge inférieure de la barre d’outils.
        """
        if len(args) == 2:
            super().SetMarginsXY(args[0], args[1])
        else:
            super().SetMargins(*args)

    # @staticmethod
    # def MakeDisabledBitmap(self, bitmap: wx.Bitmap) -> wx.Bitmap:
    def MakeDisabledBitmap(self, bitmap):
        """
        Crée une version en niveaux de gris d'un bitmap pour l'afficher en mode désactivé.

        Args :
            bitmap (wx.Bitmap) : Le bitmap à convertir.

        Returns :
            (wx.Bitmap) : Le bitmap converti en niveaux de gris.
        """
        # Penser à utiliser SetToolDisabledBitmap(self, tool_id, bitmap) qui
        # Définit le bitmap de l'outil désactivé pour l'outil identifié par tool_id.

        # Paramètres :

        # tool_id (entier) – l'identifiant de l'outil ;

        # bitmap (wx.Bitmap) – le nouveau bitmap désactivé pour l'élément de la barre d'outils.
        # Eviter que si bitmap.ConvertToImage() retourne un objet invalide, le retour plantera.
        # Sécurité : vérifier si le bitmap est bien un objet wx.Bitmap
        if isinstance(bitmap, str):
            log.error(
                "MakeDisabledBitmap a reçu une chaîne ('%s') au lieu d'un wx.Bitmap. Utilisation d'un bitmap nul.",
                bitmap,
            )
            # return wx.NullBitmap
            return None
            # return bitmap
            # return artprovider.getBitmap(bitmap)

        if not bitmap or not bitmap.IsOk():
            log.error(
                "Le bitmap fourni est invalide ou None dans MakeDisabledBitmap"
            )
            # return (
            #     wx.NullBitmap
            # )  # Retourner un bitmap nul plutôt que None pour éviter des erreurs en aval
            return None
        else:
            # return bitmap.ConvertToImage().ConvertToGreyscale().ConvertToBitmap()
            try:
                return (
                    bitmap.ConvertToImage()
                    .ConvertToGreyscale()
                    .ConvertToBitmap()
                )
            except Exception as e:
                log.error(
                    "Erreur lors de la conversion du bitmap en niveaux de gris : %s",
                    e,
                )
                return bitmap


# # class ToolBar(ttk.Frame, uicommandcontainertk.UICommandContainerMixin):
# class ToolBar(ttk.LabelFrame, uicommandcontainertk.UICommandContainerMixin):
class ToolBar(_Toolbar, uicommandcontainertk.UICommandContainerMixin):
    """A class that represents a customizable toolbar in the Task Coach UI."""

    # La classe ToolBar hérite de ttk.LabelFrame et de uicommandcontainertk.UICommandContainerMixin.
    # Elle reçoit un parent et un window (qui est le contrôleur) lors de son initialisation.
    # Elle appelle loadPerspective pour charger la configuration de la barre d'outils.
    # Dans loadPerspective, la méthode appendUICommands est appelée pour ajouter les commandes à la barre d'outils.

    # def __init__(self, window, settings, size=(32, 32), **kwargs):
    # CHANGEMENT : La signature accepte 'parent' (pour le widget) et 'window' (pour la logique)
    def __init__(self, parent, window, settings, size=(32, 32), **kwargs):
        # super().__init__(window, **kwargs)
        # CHANGEMENT : On passe 'parent' au constructeur de ttk.Frame
        super().__init__(parent, window, text="ToolBar", style=None, **kwargs)
        # log.debug(f"Initializing ToolBar in parent window: {type(window).__name__}, size: {size}")
        log.debug(
            f"ToolBar.__init__ : initialise dans le parent widget: {parent}{type(parent).__name__}, controller window: {type(window).__name__}, avec des icones de taille: {size}"
        )
        self.parent = parent
        self.__window = window  # On garde 'window' pour la logique
        self.__settings = settings
        self.__visibleUICommands = []
        self.__cache = None
        self.__customizeId = None
        self.tool_bitmap_size = size  # Store the tool bitmap size

        self.tools = []  # Use a list to store the tools
        # self.load_perspective(window.getToolBarPerspective())
        # Cet appel fonctionne maintenant car self.__window est le Viewer
        self.loadPerspective(
            self.__window.getToolBarPerspective()
        )  # Appeler la méthode sur le contrôleur
        self.configure(
            relief="raised", borderwidth=1
        )  # Add border for visual appearance
        # La "bonne pratique" est la suivante :
        # si tu stockes une variable (window) dans une variable d'instance (self.__window),
        # c'est parce que tu as l'intention d'utiliser self.__window partout ailleurs dans la classe.
        #
        # Utiliser self.__window.get...() au lieu de window.get...() est plus cohérent.
        # Cela montre que la barre d'outils dépend de sa variable d'instance (self.__window) pour fonctionner,
        # et non d'une variable locale qui n'existe que dans __init__.
        # C'est plus propre et plus facile à maintenir si jamais on doit réorganiser le code.

    def loadPerspective(self, perspective, customizable=True, cache=True):
        """
        Charge une perspective de la barre d'outils à partir d'une chaîne de caractères.

        Args :
            perspective : Perspective de la barre d'outils sous forme de chaîne de caractères.
            customizable : Valeur booléenne indiquant si la barre d'outils est personnalisable.
            cache : Valeur booléenne indiquant si la mise en cache des commandes UI est activée.

        Returns :
            None
        """
        log.debug(
            f"ToolBar.load_perspective: Commence la toolbar avec la liste de perspective: {perspective}"
        )
        self.clear()
        commands = self._filterCommands(perspective, cache=cache)
        log.debug(
            f"ToolBar.load_perspective: La liste des commandes filtrées sont: {commands}"
        )
        self.__visibleUICommands = commands[:]

        if customizable:
            if 1 not in commands:
                commands.append(1)

                # from taskcoachlib.gui.dialog.toolbar import ToolBarEditor  #Needs to be converted
            log.debug(
                "ToolBar.loadPerspective : Ajout du bouton de personnalisation de la barre d'outils"
            )
            from taskcoachlib.guitk.dialog.toolbartk import ToolBarEditor

            uiCommand = (
                uicommandtk.EditToolBarPerspective(  # Needs to be converted
                    self, ToolBarEditor, settings=self.__settings
                )
            )
            commands.append(uiCommand)
            # self.__customizeId = uiCommand.id
            # if operating_system.isMac():
            #     commands.append(None)  # Errr...
        # self.add_separator()
        self.appendUICommands(*commands)
        log.debug(
            f"ToolBar.loadPerspective : Fin de la configuration de la barre d'outils:{self} qui devrait contenir les commandes: {self.__visibleUICommands}."
        )

    # def perspective(self) -> str:
    def perspective(self):
        """
        Retourne la perspective actuelle de la barre d'outils sous forme de chaîne de caractères.

        La perspective est une chaîne de caractères qui représente
        les commandes actuellement affichées sur la barre d'outils,
        dans l'ordre dans lequel elles apparaissent.
        """
        names = list()
        for uiCommand in self.__visibleUICommands:
            if uiCommand is None:
                names.append("Separator")
            elif isinstance(uiCommand, int):
                names.append("Spacer")
            else:
                names.append(uiCommand.uniqueName())
        return ",".join(names)  # Utiliser ", ", non ?

    # def savePerspective(self, perspective: str):
    def savePerspective(self, perspective):
        """
        Enregistre la perspective actuelle de la barre d'outils dans les préférences de l'application.

        Args :
            perspective (str) : La perspective à enregistrer.
        """
        self.loadPerspective(perspective)
        self.__window.saveToolBarPerspective(perspective)

    def _filterCommands(
        self, perspective, cache=True
    ):  # Identique à la version wx.
        commands = []
        if perspective:
            index = {
                command.uniqueName(): command
                for command in self.uiCommands(cache=cache)
                if command is not None and not isinstance(command, int)
            }
            index["Separator"] = None
            index["Spacer"] = 1

            for class_name in perspective.split(", "):
                if class_name in index:
                    commands.append(index[class_name])
                else:
                    commands = list(self.uiCommands(cache=cache))
        return commands

    def clear(self):
        # """Clears the toolbar and all its widgets."""
        """Détruit tous les widgets de la barre d'outils et réinitialise ses références."""
        # Parcourt une copie de la liste des widgets enfants de la barre d'outils.
        for widget in self.winfo_children():
            # Détruit le widget Tkinter afin de libérer également sa commande Tcl.
            widget.destroy()

        # Supprime toutes les références Python vers les anciens widgets détruits.
        # Est-ce bien nécessaire ? self.tools ne sert-il pas à réinitialiser ?
        self.tools.clear()

        # Supprime également l'éventuel dictionnaire secondaire des widgets.
        if hasattr(self, "_tool_by_id"):
            # Vide le dictionnaire qui pourrait contenir des références vers les widgets détruits.
            self._tool_by_id.clear()

        # Réinitialise la liste des commandes actuellement visibles.
        self.__visibleUICommands = []

    def detach(self):
        self.clear()
        self.__visibleUICommands = self.__cache = None

    # def appendUICommands(self, *commands):  # Méthode de appendUICommands ! Contenu dans UICommandContainerMixin
    #     """Appends multiple UI commands to the toolbar."""
    #     for command in commands:
    #         self.appendUICommand(command)

    def appendUICommand(self, ui_command):
        """Appends a single UI command to the toolbar."""
        log.debug(f"ToolBar.appendUICommand : Ajoute la command {ui_command}")
        if ui_command is None:
            # Separator
            # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=2)
            ttk.Separator(self, orient=tk.HORIZONTAL).pack(
                side=tk.LEFT, padx=2
            )
            return
        # elif isinstance(ui_command, int):
        if isinstance(ui_command, int):
            # Spacer (using an empty label with weight)
            spacer = ttk.Label(self, text="")  # TODO : obtenir les images !
            spacer.pack(
                side=tk.LEFT, expand=True, fill=tk.X
            )  # Expand and fill
            return
        # else:
        # UICommand (create a button)
        try:
            before_children = list(self.winfo_children())
            # # Adapt appendToToolBar to create ttk.Button
            # button = ui_command.appendToToolBar(self)  # Pass the toolbar instance
            # # button = ttk.Button()
            # # button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2, pady=2)
            #
            # # On stocke l'ID dans le widget Tkinter lui-même pour le retrouver plus tard
            # button.ui_command_id = ui_command.id
            widget = ui_command.appendToToolBar(self)  # peut renvoyer None
            log.debug(
                "ToolBar.appendUICommand : appendToToolBar(%r) a retourné %r de type %s",
                ui_command,
                widget,
                type(widget).__name__ if widget is not None else "None",
            )

            if widget is None:
                # Tentative de détection du widget créé (dernier nouvel enfant)
                after_children = list(self.winfo_children())
                new_children = [
                    w for w in after_children if w not in before_children
                ]
                if new_children:
                    widget = new_children[-1]
                    log.warning(
                        f"ToolBar.appendUICommand : détecte un nouveau widget {widget} créé par appendToToolBar.",
                        stack_info=True,
                    )
                elif hasattr(ui_command, "_widget"):
                    widget = getattr(ui_command, "_widget")
                    log.warning(
                        f"ToolBar.appendUICommand : récupère ui_command._widget : {widget}."
                    )
                else:
                    log.error(
                        "ToolBar.appendUICommand : appendToToolBar a renvoyé None et aucun widget détecté pour %r",
                        ui_command,
                    )
                    return

                    # Ne pas écrire directement sur l'objet widget (sécurisé):
            try:
                widget.ui_command_id = ui_command.id
            except Exception:
                # Widget ne permet pas nouveaux attributs -> garder le mapping séparé
                if not hasattr(self, "_tool_by_id"):
                    self._tool_by_id = {}
                self._tool_by_id[ui_command.id] = widget
                log.exception(
                    "ToolBar.appendUICommand : erreur lors de l'ajout de la commande, appendToToolBar(%r) returned %r",
                    ui_command,
                    widget,
                )

            # self.tools.append(button)
            self.tools.append(widget)
            log.info(
                f"ToolBar.appendUICommand : Les UICommands de ToolBar sont {self.tools}."
            )
        except Exception as e:
            # log.error(
            #     f"ToolBar.appendUICommand : Error adding command {ui_command.id}{ui_command}: {e}"
            # )
            command_id = getattr(ui_command, "id", "<id-inconnu>")
            log.exception(
                "ToolBar.appendUICommand : erreur lors de l'ajout de la commande %s%s",
                command_id,
                ui_command,
            )
            raise
        # if button:  # TODO : gérer le bouton ?
        #     return button

    def uiCommands(self, cache=True):  # Identique à la version wx
        """Returns a list of UI commands to display on the toolbar."""
        if self.__cache is None or not cache:
            self.__cache = (
                self.__window.createToolBarUICommands()
            )  # needs to be converted
        return self.__cache

    def visibleUICommands(self):  # Identique à v. wx
        """Returns a list of the UI commands currently displayed on the toolbar."""
        return self.__visibleUICommands[:]

    def add_separator(self):
        # def appendSeparator(self):
        """
        Ajoute un séparateur à la barre d'outils.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        # self.add_separator()
        # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=2)
        # ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, padx=2)  # Ne fonctionne pas directement ici !
        # ttk.Separator(self, orient=tk.HORIZONTAL).pack(
        #     side=tk.TOP, fill=tk.X, pady=2
        # )
        ttk.Separator(self, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, pady=2
        )  # SUPER !
        # raise NotImplementedError("La méthode 'AppendSeparator' doit être implémentée par la classe qui utilise ce mixin.")
        # raise NotImplementedError("La méthode 'Add_h_Separator' doit être implémentée par la classe qui utilise ce mixin.")

    def getToolWidget(self, tool_id):
        """
        Retourne le widget associé à un identifiant de commande encore existant.

        Retrouve le widget dans la liste self.tools par son ID.
        """
        # Parcourt tous les widgets actuellement enregistrés dans la barre d'outils.
        for tool in self.tools:
            # # On vérifie si c'est un widget (pas un séparateur) et s'il a le bon ID
            # if (
            #     hasattr(tool, "ui_command_id")
            #     and tool.ui_command_id == tool_id
            # ):
            #     return tool
            # Vérifie que l'objet possède bien l'identifiant d'une commande.
            if not hasattr(tool, "ui_command_id"):
                # Ignore les widgets qui ne correspondent pas à une UICommand.
                continue

            # Vérifie que l'identifiant du widget correspond à celui recherché.
            if tool.ui_command_id != tool_id:
                # Passe au widget suivant lorsque l'identifiant ne correspond pas.
                continue

            # Vérifie que le widget existe encore réellement dans Tcl/Tk.
            try:
                if tool.winfo_exists():
                    # Retourne uniquement un widget encore valide.
                    return tool
            except tk.TclError:
                # Ignore une référence vers un widget dont la commande Tcl a disparu.
                continue

        # Aucun widget valide correspondant à l'identifiant n'a été trouvé.
        return None

    def GetToolState(self, tool_id):
        """
        Vérifie si l'outil est enfoncé.
        GetToolWidget indique si un outil est activé ou non.

        Args :
            toolId/tool_id (integer) : the toolbar item identifier.
        """
        widget = self.getToolWidget(tool_id)
        if widget:
            return widget.cget("relief") == "sunken"
        return False

    # def ToggleTool(self, tool_id, toggle):
    def ToggleTool(self, id, state):
        """Change le relief du widget trouvé dans la liste."""
        # widget = self.getToolWidget(tool_id)
        widget = self.getToolWidget(id)
        if widget:
            # widget.config(relief="sunken" if toggle else "raised")
            widget.config(relief="sunken" if state else "raised")


# classe de base_uicommand.py ! : à transférer !
# class UICommand:  # Base class, needs conversion
#     """Base class for UI commands."""
#     def __init__(self, toolbar, command=None, tooltip=None, image_path=None):
#         self.toolbar = toolbar
#         self.command = command
#         self.tooltip = tooltip
#         self.image_path = image_path
#         self.normal_image = None   # To store the normal image
#         self.disabled_image = None  # To store the disabled image
#         self.button = None
#
#     def appendToToolBar(self, toolbar):
#         """Creates a ttk.Button for the toolbar."""
#         # Load the image
#         # image = Image.open(self.image_path)
#         # self.normal_image = ImageTk.PhotoImage(image) # Store the normal image
#
#         # # Create a disabled version (e.g., grayscale)
#         # disabled_image = image.convert('L')  # Convert to grayscale
#         # self.disabled_image = ImageTk.PhotoImage(disabled_image) # Store the disabled image
#
#         button = ttk.Button(toolbar,
#                             # image=self.normal_image,  # Use the normal image initially
#                             state=tk.NORMAL,        # Start as enabled
#                             command=self.do_command,
#                             # compound=tk.TOP          # To put image above text
#                             )
#
#         button.pack(side=tk.LEFT, padx=1, pady=1)  # Pack the button into the toolbar
#         self.button = button
#
#         return button  # Return the button instance
#
#     def do_command(self):
#         """Executes the command associated with the UI command."""
#         if self.command:
#             self.command()

# Example Usage (in your main application window):
# self.toolbar = ToolBar(self, self.settings, relief=tk.RAISED, bd=2)
# self.toolbar.pack(side=tk.TOP, fill=tk.X)

class MainToolBar(ToolBar):
    """
    Une sous-classe de ToolBar qui est utilisée dans la fenêtre principale de Task Coach.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance de la classe MainToolBar, utilisée dans la fenêtre principale.

        Args :
            *args : Les arguments positionnels à passer à la méthode __init__ de la classe parent ToolBar.
            **kwargs : Les arguments par mot-clé à passer à la méthode __init__ de la classe parent ToolBar.
        """
        super().__init__(*args, **kwargs)
        # self.Bind(
        #     wx.EVT_SIZE, self._OnSize
        # )  # Je pense qu'il y a une erreur ici !
        self.parent.bind("<Configure>", self._OnSize)
        self._is_resizing = False
        self._resize_timer = None
        self._resize_delay_ms = 50  # régler si nécessaire
        # Dernière taille initialisé avec la taille actuelle de la barre d'outils.
        # Cela nous servira de point de référence pour déterminer si un changement "véritable" s'est produit.
        # Permet de s'assurer qu'un nouvel événement de taille n'est planifié
        # que si la taille de la barre d'outils a effectivement changé,
        # plutôt que d'être déclenché par une cascade d'événements à partir d'un seul changement de taille.
        # self._last_size = self.GetSize()
        log.debug(f"MainToolBar.__init__ : Initialisation de la barre d'outils {self.__class__.__name__}.")
        log.debug(f"MainToolBar.__init__ : qui a _last_size ? self.__window ? {self._ToolBar__window._last_size}.")
        # self._last_size = (self.parent.winfo_width(), self.parent.winfo_height())
        self._last_size = (self.winfo_width(), self.winfo_height())

    # def _OnSize(self, event):
    #     """
    #     Gestionnaire d'événements pour le redimensionnement de la fenêtre.
    #
    #     Cette méthode ajuste la taille de la barre d'outils en fonction de la taille de la fenêtre parent.
    #
    #     Args :
    #         event (wx.SizeEvent) : L'événement de redimensionnement.
    #     """
    #     event.Skip()
    #     current_size = self.GetSize()
    #     if not self._is_resizing:
    #         return
    #     # # On Windows XP, the sizes are off by 1 pixel. I fear that this value depends
    #     # # on the user's config so let's take some margin.
    #     # if abs(event.GetSize()[0] - self.GetParent().GetClientSize()[0]) >= 10:
    #
    #     # Comparer la taille actuelle avec la dernière taille enregistrée :
    #     if current_size != self._last_size:
    #         # Mise à jour vers la nouvelle taille pour éviter les appels suivants si la taille reste la même.
    #         self._last_size = current_size
    #         # # A surveiller : Ces appels à wx.CallAfter sont parfois asynchrones et silencieux en cas d'échec.
    #         self._is_resizing = True
    #         log.debug(
    #             f"MainToolBar._OnSize : appel wx.CallAfter() sur self.getParent()={self.GetParent()}."
    #         )
    #         # CallAfter ne sera exécuté que si la taille a effectivement changé.
    #         wx.CallAfter(
    #             self.GetParent().SendSizeEvent
    #         )  # This function sends a dummy size event to the window allowing it to re-layout its children positions. Ne fonctionne pas sur MainWindow !
    #         log.debug(
    #             "MainToolBar._OnSize : L'appel wx.CallAfter(GetParent.SendSizeEvent) est passé."
    #         )
    #     self._is_resizing = False
    #     # # Voici une ventilation du problème :
    #     # #
    #     # # Lorsqu’un événement de taille se produit, la méthode _OnSize est déclenchée.
    #     # # Le code vérifie si la largeur de la barre d’outils est significativement
    #     # # différente de la largeur du client de sa fenêtre parente (une différence de 10 pixels ou plus).
    #     # #
    #     # # Si la condition est remplie, wx. CallAfter est utilisé pour planifier un nouveau SendSizeEvent pour la fenêtre parente.
    #     # #
    #     # # À son tour, ce SendSizeEvent déclenchera probablement à nouveau la méthode _OnSize, car la taille de la fenêtre a changé.
    #     # #
    #     # # Cela crée une boucle récursive : un événement size appelle _OnSize, qui planifie ensuite un autre événement size, et ainsi de suite.
    #     # #
    #     # # Le commentaire dans le code lui-même suggère que ce comportement était une solution de contournement
    #     # # pour un problème spécifique sous Windows XP, où les tailles étaient décalées d’un pixel.
    #     # # Cependant, dans votre environnement actuel, il semble que la méthode s’appelle elle-même à plusieurs reprises,
    #     # # ce qui conduit à la « boucle infinie » que vous observez.

    def _OnSize(self, event):
        """
        Gestionnaire d'événements pour le redimensionnement de la fenêtre.

        Cette méthode ajuste la taille de la barre d'outils en fonction de la taille de la fenêtre parent.

        Args :
            event : L'événement de redimensionnement.
        """
        # log.debug(
        #     "MainToolBar._OnSize : appelé pour remettre la ToolBar à la taille de la fenêtre."
        # )
        # event.Skip()  # Le gestionnaire Tkinter appelle event.Skip(), méthode wxPython inexistante ;
        # une erreur survient lors du redimensionnement de la barre d’outils.

        # current_size = self.GetSize()
        # current_size = (self.parent.winfo_width(), self.parent.winfo_height())
        current_size = (self.winfo_width(), self.winfo_height())
        # if self._is_resizing:
        #     return
        # Comparer la taille actuelle avec la dernière taille enregistrée :
        # if current_size == self._last_size:
        #     self._resize_timer.

        # if current_size != self._last_size:
        #     # Mise à jour vers la nouvelle taille pour éviter les appels suivants si la taille reste la même.
        #     self._last_size = current_size
        #
        #     self._is_resizing = True
        #     log.debug(
        #         f"MainToolBar._OnSize : appel wx.CallAfter() sur self.getParent()={self.GetParent()}."
        #     )
        #     # wx.CallAfter(self._call_parent_send_size_and_unset_flag)
        #     log.debug(
        #         "MainToolBar._OnSize : L'appel wx.CallAfter(GetParent.SendSizeEvent) est passé."
        #     )
        if self._resize_timer is not None:
            # réarme le timer (cancel/restart) : CallLater retourne un objet, on l'arrêtera
            self._resize_timer.Stop()
            self._resize_timer = None
            # log.debug(
            #     "MainToolBar._OnSize: relance le timer pour le redimensionnement."
            # )
            # self._resize_timer = wx.CallLater(
            #     self._resize_delay_ms, self._do_parent_send_size
            # )
            self._resize_timer = self.parent.after(self._resize_delay_ms, self._do_parent_send_size)
        # self._is_resizing = False
        # log.debug("MainToolBar._OnSize : terminé !")

    def _do_parent_send_size(self):
        # self._resize_timer = None
        # try:
        #     # log.debug(
        #     #     "MainToolBar._do_parent_send_size :  met à jour la nouvelle taille de fenêtre."
        #     # )
        #     self.SendSizeEvent()  # inutile avec tkinter !
        # except Exception as e:
        #     log.error(
        #         "MainToolBar._do_parent_send_size : Erreur en appelant SendSizeEvent depuis _do_parent_send_size: %s",
        #         e,
        #     )
        # log.debug(
        #     "MainToolBar._do_parent_send_size : ToolBar et fenêtre redimensionnées !"
        # )
        pass

    def _call_parent_send_size_and_unset_flag(self):
        try:
            # self.GetParent().SendSizeEvent()
            self._do_parent_send_size()
        finally:
            self._is_resizing = False
            # log.debug(
            #     "MainToolBar._call_parent_send_size_and_unset_flag : _is_resizing remis à False après SendSizeEvent !"
            # )

    def Realize(self):
        """aui.auibar.AuiToolBar.Realize Réalise la barre d'outils.

        Cette fonction doit être appelée après avoir ajouté des outils.
        """
        #  limiter ou conditionner les CallAfter :
        #  si vous appelez SetMinSize et ensuite SendSizeEvent,
        #  assurez-vous que ces deux appels ne se déclenchent
        #  pas mutuellement en boucle sur certains systèmes.
        # voir wx.lib.agw.aui.auibar.AuiToolBar.SetAGWWindowStyleFlag
        # self._agwStyle &= ~aui.AUI_TB_NO_AUTORESIZE
        self._agwStyle &= ~aui_tk_constants.AUI_TB_NO_AUTORESIZE
        super().Realize()
        # self._agwStyle |= aui.AUI_TB_NO_AUTORESIZE
        self._agwStyle |= aui_tk_constants.AUI_TB_NO_AUTORESIZE
        # log.debug("MainToolBar.Realize : appel wx.CallAfter().")
        # # wx.CallAfter(self.GetParent().SendSizeEvent)
        # wx.CallAfter(self._call_parent_send_size_and_unset_flag)
        # wx.CallAfter(self._do_parent_send_size)
        self.parent.after(self._resize_delay_ms, self._do_parent_send_size)
        # log.debug("MainToolBar.Realize : L'appel wx.CallAfter(SendSizeEvent) est passé.")
        # w, h = self.GetParent().GetClientSizeTuple()
        # w, h = self.GetParent().GetClientSize()
        # w = self.parent.winfo_width()
        w = self.winfo_width()
        # h = self.parent.winfo_height()
        h = self.winfo_height()
        # log.debug("MainToolBar.Realize : appel CallAfter(self.SetMinSize).")
        # wx.CallAfter(self.SetMinSize, (w, -1))
        self.parent.after(self._resize_delay_ms, lambda: self.parent.SetMinSize((w, -1)))
        # Après les appels mise à jour pour nous assurer que notre suivi de taille est correct dès le départ.
        # self._last_size = self.parent.GetSize()
        self._last_size = (self.winfo_width(), self.winfo_height())
        # log.debug("MainToolBar.Realize : L'appel wx.CallAfter(SetMinSize) est passé.")
        # log.debug(
        #     "MainToolBar.Realize : Les appels wx.CallAfter(SendSizeEvent & SetMinSize) sont passé avec succès !"
        # )
