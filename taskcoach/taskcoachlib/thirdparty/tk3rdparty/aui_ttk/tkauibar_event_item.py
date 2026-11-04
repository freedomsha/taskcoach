# -*- coding: utf-8 -*-
"""Événements et éléments de barre d'outils pour le portage Tkinter d'AUI.

Ce module fournit les classes fondamentales représentant les éléments
(outils, séparateurs, contrôles) et les événements associés à la barre
d'outils AuiToolBar, dans le cadre de la conversion de Task Coach vers Tkinter/ttk :

- ``CommandToolBarEvent`` : Événement de commande décrivant une action sur un
  outil (clic standard, clic sur flèche déroulante, position du pointeur, etc.).
- ``AuiToolBarEvent`` : Événement de notification dérivé de ``CommandToolBarEvent``,
  intégrant un mécanisme d'autorisation ou de veto (``Veto()`` / ``Allow()``).
- ``ToolbarCommandCapture`` : Gestionnaire utilitaire de capture de commandes
  permettant d'intercepter l'identifiant d'un outil lors du traitement d'un événement.
- ``AuiToolBarItem`` : Descripteur complet d'un élément de barre d'outils (bouton,
  séparateur, espaceur, contrôle Tkinter embarqué), gérant ses icônes, libellés,
  dimensions et états graphiques.

Ces classes ne dépendent plus de wxPython et utilisent des structures Python
standards et des widgets Tkinter compatibles.
"""

from copy import copy

try:
    from .aui_tk_constants import *
except ImportError:
    from aui_tk_constants import *


class CommandToolBarEvent:
    """Événement de commande déclenché par une interaction avec la barre d'outils.

    Transmet les informations relatives à une action utilisateur sur un élément
    de la barre d'outils : identifiant de l'outil, coordonnées du clic souris,
    rectangle englobant de l'élément cliqué et indication d'un clic spécifique
    sur la flèche déroulante (drop-down).

    Attributes:
        command_type: Type ou identifiant de l'événement de commande.
        win_id (int): Identifiant numérique de la fenêtre émettrice.
        is_dropdown_clicked (bool): ``True`` si le clic a visé la flèche déroulante.
        click_pt (tuple[int, int]): Coordonnées (x, y) du point de clic.
        rect (tuple[int, int, int, int]): Rectangle (x, y, largeur, hauteur) de l'outil.
        tool_id (int): Identifiant numérique de l'outil concerné.
    """

    def __init__(self, command_type=None, win_id=0):
        """Initialise un nouvel événement de commande de barre d'outils.

        Args:
            command_type: Type ou identifiant de l'événement.
            win_id (int, optional): Identifiant numérique de la fenêtre émettrice.
                Par défaut 0.
        """
        self.command_type = command_type
        self.win_id = win_id
        self.is_dropdown_clicked = False
        self.click_pt = (-1, -1)
        self.rect = (-1, -1, 0, 0)
        self.tool_id = -1

    def IsDropDownClicked(self):
        """Indique si le clic utilisateur ciblait la flèche de menu déroulant.

        Returns:
            bool: ``True`` si la flèche déroulante a été cliquée, ``False`` sinon.
        """
        return self.is_dropdown_clicked

    def SetDropDownClicked(self, c):
        """Définit si le clic ciblait la flèche de menu déroulant.

        Args:
            c (bool): ``True`` pour indiquer un clic sur la flèche déroulante.
        """
        self.is_dropdown_clicked = bool(c)

    def GetClickPoint(self):
        """Renvoie les coordonnées du curseur lors du clic.

        Returns:
            tuple[int, int]: Coordonnées (x, y) relatives au widget barre d'outils.
        """
        return self.click_pt

    def SetClickPoint(self, p):
        """Définit les coordonnées du point de clic.

        Args:
            p (tuple[int, int]): Coordonnées (x, y).
        """
        self.click_pt = p

    def GetItemRect(self):
        """Renvoie le rectangle englobant de l'élément cliqué.

        Returns:
            tuple[int, int, int, int]: Rectangle (x, y, largeur, hauteur).
        """
        return self.rect

    def SetItemRect(self, r):
        """Définit le rectangle englobant de l'élément cliqué.

        Args:
            r (tuple[int, int, int, int]): Rectangle (x, y, largeur, hauteur).
        """
        self.rect = r

    def GetToolId(self):
        """Renvoie l'identifiant de l'outil associé à l'événement.

        Returns:
            int: Identifiant numérique de l'outil (-1 si indéfini).
        """
        return self.tool_id

    def SetToolId(self, i):
        """Définit l'identifiant de l'outil associé à l'événement.

        Args:
            i (int): Identifiant numérique de l'outil.
        """
        self.tool_id = i


class AuiToolBarEvent(CommandToolBarEvent):
    """Événement de notification de barre d'outils avec mécanisme de veto.

    Hérite de :class:`CommandToolBarEvent` et émule le comportement de
    ``wx.NotifyEvent``. Permet aux récepteurs d'interdire l'action prévue
    en appelant :meth:`Veto` (par exemple pour annuler l'ouverture d'un menu
    ou bloquer l'activation d'un outil).

    Attributes:
        notify: Référence vers l'instance elle-même (conservé pour compatibilité wx).
        _allowed (bool): Drapeau interne autorisant (``True``) ou refusant (``False``) l'action.
    """

    def __init__(self, command_type=None, win_id=0):
        """Initialise l'événement de notification de barre d'outils.

        Args:
            command_type: Type ou identifiant de l'événement notifié.
            win_id (int, optional): Identifiant numérique de la fenêtre émettrice.
                Par défaut 0.
        """
        super().__init__(command_type, win_id)
        self.notify = self
        self._allowed = True

    def GetNotifyEvent(self):
        """Renvoie l'instance de notification (émulation wx).

        Returns:
            AuiToolBarEvent: L'événement lui-même.
        """
        return self

    def IsAllowed(self):
        """Vérifie si l'action déclenchée par l'événement est autorisée.

        Returns:
            bool: ``True`` si l'action est permise, ``False`` si un veto a été posé.
        """
        return getattr(self, "_allowed", True)

    def Veto(self):
        """Pose un veto sur l'action associée pour empêcher son exécution."""
        self._allowed = False

    def Allow(self):
        """Autorise explicitement l'exécution de l'action associée."""
        self._allowed = True


class ToolbarCommandCapture:
    """Captureur d'événements de commande pour barre d'outils.

    Utilisé lors du traitement et de la distribution des événements pour
    intercepter et conserver le dernier identifiant d'outil actionné.

    Attributes:
        _last_id (int): Dernier identifiant d'outil capturé.
    """

    def __init__(self):
        """Initialise le captureur avec un identifiant nul."""
        self._last_id = 0

    def GetCommandId(self):
        """Renvoie le dernier identifiant de commande capturé.

        Returns:
            int: Identifiant d'outil ou de commande.
        """
        return self._last_id

    def ProcessEvent(self, event):
        """Traite l'événement et enregistre l'identifiant de l'outil concerné.

        Extrait ``tool_id`` ou ``id`` de l'événement fourni et met à jour
        ``_last_id``.

        Args:
            event: Événement de commande ou de barre d'outils.

        Returns:
            bool: Toujours ``True`` pour confirmer le traitement.
        """
        # Récupère tool_id en priorité, sinon id, avec repli sur 0
        self._last_id = getattr(event, "tool_id", getattr(event, "id", 0))
        return True


class AuiToolBarItem:
    """Descripteur et modèle de données d'un élément de barre d'outils AuiToolBar.

    Cette classe représente toute entité pouvant être placée dans une barre
    d'outils : bouton standard, bouton à bascule (check), bouton radio,
    séparateur, espaceur extensible ou widget Tkinter embarqué (contrôle).

    Elle encapsule les icônes (normale, désactivée, survol, orientée), les textes
    d'aide et de libellé, l'état graphique (normal, enfoncé, désactivé, etc.),
    ainsi que les propriétés de disposition géométrique (proportion, alignement,
    taille minimale).

    Attributes:
        window: Widget Tkinter/ttk embarqué (pour les outils de type contrôle).
        clockwisebmp: Image tournée dans le sens horaire (pour barres verticales).
        counterclockwisebmp: Image tournée dans le sens anti-horaire.
        clockwisedisbmp: Image désactivée tournée dans le sens horaire.
        counterclockwisedisbmp: Image désactivée tournée dans le sens anti-horaire.
        sizer_item: Descripteur de positionnement ou élément de sizer associé.
        spacer_pixels (int): Largeur/hauteur en pixels pour les séparateurs/espaceurs.
        id (int): Identifiant numérique unique de l'outil.
        kind (int): Type d'élément (ex. ``ITEM_NORMAL``, ``ITEM_CHECK``, ``ITEM_RADIO``,
            ``ITEM_SEPARATOR``, ``ITEM_SPACER``, ``ITEM_CONTROL``).
        state (int): Masque binaire d'état (ex. ``AUI_BUTTON_STATE_NORMAL``,
            ``AUI_BUTTON_STATE_HOVER``, ``AUI_BUTTON_STATE_PRESSED``, etc.).
        proportion (int): Facteur de proportion pour l'extension de l'élément.
        active (bool): Indique si l'élément participe à la disposition active.
        dropdown (bool): Indique si l'élément dispose d'une flèche de menu déroulant.
        sticky (bool): Indique si l'élément reste visuellement enfoncé.
        user_data: Données arbitraires associées par l'application cliente.
        label (str): Texte affiché sur ou à côté de l'outil.
        bitmap: Image normale de l'outil.
        disabled_bitmap: Image affichée lorsque l'outil est désactivé.
        hover_bitmap: Image affichée lors du survol par la souris.
        short_help (str): Texte d'infobulle (tooltip).
        long_help (str): Texte d'aide étendu (barre d'état).
        target: Référence vers une cible ou un gestionnaire d'action.
        min_size (tuple[int, int]): Taille minimale (largeur, hauteur) en pixels.
        alignment (str): Alignement de l'élément (ex. ``"center"``, ``"left"``, ``"right"``).
        orientation (int): Orientation de l'outil (``AUI_TBTOOL_HORIZONTAL`` ou ``AUI_TBTOOL_VERTICAL``).
    """

    def __init__(self, item=None):
        """Initialise un nouvel élément de barre d'outils.

        Si une instance existante est fournie dans ``item``, ses attributs
        sont intégralement copiés via :meth:`Assign`. Sinon, tous les champs
        sont initialisés à leurs valeurs par défaut.

        Args:
            item (AuiToolBarItem, optional): Élément source à cloner.
        """
        # Si un élément source est fourni, copier immédiatement ses attributs
        if item is not None:
            self.Assign(item)
            return

        # Initialisation par défaut de tous les champs
        self.window = None
        self.clockwisebmp = None
        self.counterclockwisebmp = None
        self.clockwisedisbmp = None
        self.counterclockwisedisbmp = None
        self.sizer_item = None
        self.spacer_pixels = 0
        self.id = 0
        self.kind = ITEM_NORMAL
        self.state = 0
        self.proportion = 0
        self.active = True
        self.dropdown = True
        self.sticky = True
        self.user_data = 0
        self.label = ""
        self.bitmap = None
        self.disabled_bitmap = None
        self.hover_bitmap = None
        self.short_help = ""
        self.long_help = ""
        self.target = None
        self.min_size = (-1, -1)
        self.alignment = "center"
        self.orientation = AUI_TBTOOL_HORIZONTAL

    def Assign(self, c):
        """Copie l'ensemble des attributs d'un autre élément vers celui-ci.

        Args:
            c (AuiToolBarItem): Élément source dont les attributs sont copiés.

        Returns:
            AuiToolBarItem: L'instance courante mise à jour (permet le chaînage).
        """
        self.__dict__.update(c.__dict__)
        return self

    def SetWindow(self, v):
        """Associe un widget Tkinter/ttk à cet élément de barre d'outils.

        Args:
            v (tk.Widget | None): Widget à embarquer dans la barre.
        """
        self.window = v

    def GetWindow(self):
        """Renvoie le widget Tkinter/ttk embarqué dans cet élément.

        Returns:
            tk.Widget | None: Le widget associé, ou ``None``.
        """
        return self.window

    def SetId(self, v):
        """Définit l'identifiant numérique de l'outil.

        Args:
            v (int): Identifiant unique de l'outil.
        """
        self.id = v

    def GetId(self):
        """Renvoie l'identifiant numérique de l'outil.

        Returns:
            int: Identifiant de l'outil.
        """
        return self.id

    def SetKind(self, v):
        """Définit le type d'élément de barre d'outils.

        Args:
            v (int): Type d'élément (ex. ``ITEM_NORMAL``, ``ITEM_CHECK``,
                ``ITEM_RADIO``, ``ITEM_SEPARATOR``, ``ITEM_SPACER``, ``ITEM_CONTROL``).
        """
        self.kind = v

    def GetKind(self):
        """Renvoie le type d'élément de barre d'outils.

        Returns:
            int: Type d'élément.
        """
        return self.kind

    def SetState(self, v):
        """Définit le masque binaire d'état de l'outil.

        Args:
            v (int): Masque d'état (combinaison de drapeaux ``AUI_BUTTON_STATE_*``).
        """
        self.state = v

    def GetState(self):
        """Renvoie le masque binaire d'état de l'outil.

        Returns:
            int: Masque d'état actuel.
        """
        return self.state

    def SetSizerItem(self, v):
        """Associe un élément de disposition ou sizer à cet outil.

        Args:
            v: Objet de disposition ou sizer associé.
        """
        self.sizer_item = v

    def GetSizerItem(self):
        """Renvoie l'élément de disposition associé.

        Returns:
            Any: L'objet sizer associé (ou None).
        """
        return self.sizer_item

    def SetLabel(self, v):
        """Définit le libellé textuel de l'outil.

        Args:
            v (str): Libellé affiché sur ou sous l'icône.
        """
        self.label = v

    def GetLabel(self):
        """Renvoie le libellé textuel de l'outil.

        Returns:
            str: Libellé de l'outil.
        """
        return self.label

    def SetBitmap(self, v):
        """Définit l'image ou l'icône normale de l'outil.

        Args:
            v: Image Tkinter/PhotoImage ou chemin d'icône.
        """
        self.bitmap = v

    def GetBitmap(self):
        """Renvoie l'image normale de l'outil.

        Returns:
            Any: L'icône normale configurée.
        """
        return self.bitmap

    def SetDisabledBitmap(self, v):
        """Définit l'image affichée lorsque l'outil est désactivé.

        Args:
            v: Image pour l'état désactivé.
        """
        self.disabled_bitmap = v

    def GetDisabledBitmap(self):
        """Renvoie l'image de l'outil désactivé.

        Returns:
            Any: L'icône pour l'état désactivé (ou None).
        """
        return self.disabled_bitmap

    def SetHoverBitmap(self, v):
        """Définit l'image affichée lors du survol de l'outil par la souris.

        Args:
            v: Image pour l'état de survol.
        """
        self.hover_bitmap = v

    def GetHoverBitmap(self):
        """Renvoie l'image de l'outil lors du survol.

        Returns:
            Any: L'icône pour l'état de survol (ou None).
        """
        return self.hover_bitmap

    def SetOrientation(self, v):
        """Définit l'orientation de l'outil (horizontale ou verticale).

        Args:
            v (int): ``AUI_TBTOOL_HORIZONTAL`` ou ``AUI_TBTOOL_VERTICAL``.
        """
        self.orientation = v

    def GetOrientation(self):
        """Renvoie l'orientation de l'outil.

        Returns:
            int: L'orientation configurée.
        """
        return self.orientation

    def GetRotatedBitmap(self):
        """Renvoie l'image pivotée de l'outil selon l'orientation.

        Renvoie l'image normale par défaut en mode horizontal ou si aucune
        variante pivotée n'a été pré-générée.

        Returns:
            Any: L'image appropriée pour l'orientation courante.
        """
        return self.bitmap

    def SetShortHelp(self, v):
        """Définit le texte de l'infobulle (tooltip) de l'outil.

        Args:
            v (str): Texte court d'aide.
        """
        self.short_help = v

    def GetShortHelp(self):
        """Renvoie le texte de l'infobulle de l'outil.

        Returns:
            str: Texte court d'aide.
        """
        return self.short_help

    def SetLongHelp(self, v):
        """Définit le texte d'aide étendu (pour la barre d'état).

        Args:
            v (str): Texte long d'aide.
        """
        self.long_help = v

    def GetLongHelp(self):
        """Renvoie le texte d'aide étendu de l'outil.

        Returns:
            str: Texte long d'aide.
        """
        return self.long_help

    def SetMinSize(self, v):
        """Définit les dimensions minimales de l'outil.

        Args:
            v (tuple[int, int]): Dimensions minimales (largeur, hauteur) en pixels.
        """
        self.min_size = v

    def GetMinSize(self):
        """Renvoie les dimensions minimales configurées pour l'outil.

        Returns:
            tuple[int, int]: Dimensions (largeur, hauteur).
        """
        return self.min_size

    def SetSpacerPixels(self, v):
        """Définit l'espacement en pixels pour un outil de type séparateur/espaceur.

        Args:
            v (int): Nombre de pixels d'espacement.
        """
        self.spacer_pixels = v

    def GetSpacerPixels(self):
        """Renvoie l'espacement en pixels configuré pour cet espaceur.

        Returns:
            int: Nombre de pixels.
        """
        return self.spacer_pixels

    def SetProportion(self, v):
        """Définit le facteur de proportion pour l'extension de l'outil.

        Args:
            v (int): Facteur de proportion (0 pour taille fixe, > 0 pour extensible).
        """
        self.proportion = v

    def GetProportion(self):
        """Renvoie le facteur de proportion de l'outil.

        Returns:
            int: Facteur de proportion.
        """
        return self.proportion

    def SetActive(self, v):
        """Définit si l'outil est actif et affiché dans la disposition courante.

        Args:
            v (bool): ``True`` pour activer l'outil, ``False`` sinon.
        """
        self.active = bool(v)

    def IsActive(self):
        """Indique si l'outil est actuellement actif et affiché.

        Returns:
            bool: ``True`` si actif, ``False`` sinon.
        """
        return self.active

    def SetHasDropDown(self, v):
        """Active ou désactive la présence d'une flèche de menu déroulant.

        Args:
            v (bool): ``True`` si l'outil comporte une flèche déroulante.
        """
        # self.dropdown = v
        self.dropdown = bool(v)

    def HasDropDown(self):
        """Indique si l'outil comporte une flèche de menu déroulant.

        Returns:
            bool: ``True`` si un menu déroulant est associé, ``False`` sinon.
        """
        return self.dropdown

    def SetSticky(self, v):
        """Définit si l'outil reste visuellement enfoncé (état collant).

        Args:
            v (bool): ``True`` si l'outil est collant, ``False`` sinon.
        """
        self.sticky = bool(v)

    def IsSticky(self):
        """Indique si l'outil est configuré pour rester visuellement enfoncé.

        Returns:
            bool: ``True`` si collant, ``False`` sinon.
        """
        return self.sticky

    def SetUserData(self, v):
        """Associe des données utilisateur personnalisées à cet outil.

        Args:
            v: Objet ou valeur arbitraire à rattacher à l'outil.
        """
        self.user_data = v

    def GetUserData(self):
        """Renvoie les données utilisateur personnalisées associées à l'outil.

        Returns:
            Any: Données utilisateur configurées.
        """
        return self.user_data

    def SetAlignment(self, v):
        """Définit l'alignement géométrique de l'outil dans la barre.

        Args:
            v (str): Alignement (ex. ``"center"``, ``"left"``, ``"right"``).
        """
        self.alignment = v

    def GetAlignment(self):
        """Renvoie l'alignement géométrique configuré pour l'outil.

        Returns:
            str: Chaîne d'alignement.
        """
        return self.alignment
