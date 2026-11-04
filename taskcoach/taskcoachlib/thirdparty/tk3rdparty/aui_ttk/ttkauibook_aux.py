# -*- coding: utf-8 -*-
"""Classes auxiliaires et structures de données pour le carnet d'onglets AuiNotebook sous ttk.

Ce module fournit les classes utilitaires, les conteneurs de données et les objets
d'événements nécessaires au fonctionnement de la version Tkinter/ttk du carnet d'onglets
AUI (adapté de wxPython AUI) :

- ``TabTextCtrl`` : Champ de saisie temporaire (``ttk.Entry``) superposé à un onglet
  pour permettre la modification directe (« in-place ») de son libellé.
- ``AuiNotebookPage`` : Structure de données modélisant l'état complet d'une page
  d'onglet (fenêtre associée, titre, icônes, état actif/inactif, visibilité, etc.).
- ``AuiTabContainerButton`` : Descripteur d'un bouton de contrôle dans la barre d'onglets
  (fermeture, navigation gauche/droite, liste déroulante des fenêtres).
- ``CommandNotebookEvent`` : Événement de commande simulant les événements d'action
  wxPython (changement de sélection, annulation d'édition, glisser-déposer).
- ``AuiNotebookEvent`` : Événement de notification avec mécanisme d'autorisation ou de
  veto (``Veto()`` / ``Allow()``).
- ``TabNavigatorProps`` : Structure de transfert de paramètres pour la boîte de dialogue
  de navigation entre onglets.
- ``TabNavigatorWindow`` : Fenêtre modale (``tk.Toplevel``) permettant de naviguer et de
  sélectionner rapidement un onglet via un composant ``ttk.Treeview``.

Les widgets de présentation utilisent ttk lorsque cette bibliothèque fournit
un équivalent. Les classes Tk classiques restent utilisées pour les éléments
qui n'ont pas d'équivalent ttk direct, notamment ``tk.Toplevel``.
"""

import datetime
import tkinter as tk
from tkinter import ttk

try:
    from .aui_tk_constants import *
except ImportError:
    from aui_tk_constants import *


class TabTextCtrl(ttk.Entry):
    """Contrôle ttk utilisé pour modifier le texte d'un onglet directement en ligne.

    Ce widget hérite de ``ttk.Entry`` et se positionne au-dessus de l'onglet en cours
    d'édition. Il gère la validation des modifications (touche Entrée ou perte de focus)
    ainsi que leur annulation (touche Échap).

    Attributes:
        _owner: Widget parent ou conteneur hébergeant l'onglet (ex. ``AuiTabCtrl``).
        _tabEdited: Instance de la page en cours de renommage (``AuiNotebookPage``).
        _pageIndex (int): Index de la page associée dans le carnet d'onglets.
        _startValue (str): Texte initial de l'onglet avant modification.
        _finished (bool): Indicateur signalant que la session d'édition est achevée.
        _aboutToFinish (bool): Drapeau évitant les validations en double lors de la fermeture.
        _currentValue (str): Valeur textuelle courante du champ.
    """

    def __init__(self, owner, tab, page_index):
        """Initialise le champ d'édition d'onglet.

        Place le texte actuel de l'onglet dans le champ, sélectionne la totalité
        du texte, prend le focus clavier et attache les raccourcis de validation
        (Entrée), d'annulation (Échap) et de perte de focus.

        Args:
            owner: Widget propriétaire ou conteneur d'onglets.
            tab: Objet représentant la page d'onglet à renommer (doit posséder
                l'attribut ``caption``).
            page_index (int): Index numérique de la page dans le carnet d'onglets.
        """
        self._owner = owner
        self._tabEdited = tab
        self._pageIndex = page_index
        self._startValue = getattr(tab, "caption", "")
        self._finished = False
        self._aboutToFinish = False
        self._currentValue = self._startValue

        # Résolution du widget parent Tkinter : owner s'il dérive de tk.Misc,
        # ou son master s'il s'agit d'un adaptateur sans ascendance directe tk.Misc.
        parent = owner if isinstance(owner, tk.Misc) else getattr(owner, "master", None)
        super().__init__(parent)

        # Initialisation du texte, sélection complète et capture immédiate du focus
        self.insert(0, self._startValue)
        self.select_range(0, tk.END)
        self.focus_set()

        # Liaison des événements clavier et de perte de focus
        self.bind("<Return>", self.OnChar)
        self.bind("<Escape>", self.OnChar)
        self.bind("<KeyRelease>", self.OnKeyUp)
        self.bind("<FocusOut>", self.OnKillFocus)

    def _notebook(self):
        """Recherche et renvoie l'instance du carnet d'onglets propriétaire.

        Remonte la hiérarchie des widgets pour atteindre l'instance de
        ``AuiNotebook`` correspondante.

        Returns:
            AuiNotebook | tk.Misc: L'instance du carnet d'onglets ou la fenêtre parente.
        """
        if hasattr(self._owner, "GetParent"):
            return self._owner.GetParent()
        return (
            self._owner.winfo_toplevel()
            if isinstance(self._owner, tk.Misc)
            else getattr(self._owner, "master", self._owner)
        )

    def AcceptChanges(self):
        """Valide et applique le nouveau libellé de l'onglet.

        Si le texte n'a pas été modifié, notifie l'annulation au carnet.
        Si le texte a changé, sollicite l'accord du carnet d'onglets via
        ``OnRenameAccept`` (si présent) ; en cas de rejet, les modifications
        ne sont pas enregistrées. Si la modification est approuvée, met à jour
        le texte de l'onglet via ``SetPageText``.

        Returns:
            bool: ``True`` si les modifications ont été acceptées ou si le texte
            est resté inchangé, ``False`` si le renommage a été rejeté par le carnet.
        """
        value = self.get()
        notebook = self._notebook()

        # Si le texte est resté identique, traiter comme une annulation
        if value == self._startValue:
            if hasattr(notebook, "OnRenameCancelled"):
                notebook.OnRenameCancelled(self._pageIndex)
            return True

        # Demander l'approbation du carnet d'onglets avant d'appliquer
        if hasattr(notebook, "OnRenameAccept") and not notebook.OnRenameAccept(
            self._pageIndex, value
        ):
            return False

        # Appliquer le nouveau libellé de l'onglet
        if hasattr(notebook, "SetPageText"):
            notebook.SetPageText(self._pageIndex, value)
        return True

    def Finish(self):
        """Termine la session d'édition du texte.

        Restitue le focus au conteneur propriétaire et réinitialise ou détruit
        le contrôle de saisie. Ne s'exécute qu'une seule fois grâce au drapeau
        ``_finished``.
        """
        if not self._finished:
            self._finished = True
            # Restitue le focus au widget propriétaire
            if hasattr(self._owner, "focus_set"):
                self._owner.focus_set()
            # Délègue le nettoyage au propriétaire s'il expose ResetTextControl,
            # sinon détruit directement l'Entry Tkinter.
            if hasattr(self._owner, "ResetTextControl"):
                self._owner.ResetTextControl()
            else:
                self.destroy()

    def OnChar(self, event):
        """Traite les touches spéciales de validation ou d'annulation.

        - ``Return`` : Valide les modifications saisies et planifie la fermeture
          du contrôle après traitement de l'événement.
        - ``Escape`` : Annule les modifications et rétablit le texte initial.

        Args:
            event (tk.Event): L'événement clavier reçu.

        Returns:
            str | None: ``"break"`` pour empêcher la propagation de la touche
            dans Tkinter, ou ``None`` pour les autres touches.
        """
        if event.keysym == "Return":
            self._aboutToFinish = True
            self._currentValue = self.get()
            self.AcceptChanges()
            # Utilisation de after_idle pour laisser l'événement Return se terminer
            # avant de détruire le widget de saisie.
            self.after_idle(self.Finish)
            return "break"
        if event.keysym == "Escape":
            self.StopEditing()
            return "break"
        return None

    def OnKeyUp(self, event):
        """Met à jour la valeur courante lors du relâchement d'une touche.

        Args:
            event (tk.Event): L'événement clavier reçu.
        """
        self._currentValue = self.get()

    def OnKillFocus(self, event):
        """Gère la perte de focus clavier du champ de saisie.

        Si la fermeture n'était pas déjà initiée (par ex. par Entrée ou Échap),
        valide automatiquement les modifications apportées avant de clôturer
        l'édition.

        Args:
            event (tk.Event): L'événement de perte de focus (<FocusOut>).
        """
        # Évite d'enregistrer deux fois ou d'écraser une annulation par Échap
        if not self._aboutToFinish and not self._finished:
            self.AcceptChanges()
        self.Finish()

    def StopEditing(self):
        """Interrompt l'édition en cours et restaure le libellé d'origine.

        Efface la saisie courante, réinsère la valeur de départ (``_startValue``)
        et clôture le contrôle d'édition.
        """
        self._aboutToFinish = True
        self.delete(0, tk.END)
        self.insert(0, self._startValue)
        self.Finish()

    def item(self, *args, **kwargs):
        """Renvoie le texte courant pour compatibilité d'interface.

        Returns:
            str | None: Le texte saisi si aucun argument n'est fourni, sinon ``None``.
        """
        return self.get() if not args and not kwargs else None


class AuiNotebookPage:
    """Structure décrivant une page (onglet) d'un carnet d'onglets AuiNotebook.

    Contient l'ensemble des métadonnées, états et références graphiques d'un
    onglet particulier : son contenu (fenêtre fille), son libellé, ses icônes,
    ses états d'activation et de visibilité, ainsi que son horodatage d'accès
    pour l'historique de navigation.

    Attributes:
        window: Widget ou fenêtre fille associé(e) au contenu de la page.
        caption (str): Titre / libellé affiché sur l'onglet.
        bitmap: Icône de l'onglet dans son état normal.
        dis_bitmap: Icône affichée lorsque l'onglet est désactivé.
        tooltip (str): Texte d'infobulle associé à l'onglet.
        rect (tuple[int, int, int, int]): Coordonnées géométriques (x, y, largeur, hauteur)
            de l'onglet dans la barre de titre.
        active (bool): Indique si l'onglet est actuellement actif / sélectionné.
        enabled (bool): Indique si l'onglet est activé (cliquable).
        hidden (bool): Indique si l'onglet est masqué de l'affichage.
        hasCloseButton (bool): Indique si l'onglet comporte un bouton de fermeture individuel.
        control: Contrôle widget personnalisé optionnel intégré dans l'onglet.
        renamable (bool): Indique si le libellé de l'onglet peut être modifié en ligne.
        text_colour (str): Code couleur hexadécimal du texte de l'onglet.
        access_time (datetime.datetime): Date et heure du dernier accès, utilisé
            notamment pour le tri MRU (Most Recently Used).
    """

    def __init__(self):
        """Initialise une nouvelle instance de page d'onglet avec des valeurs par défaut."""
        self.window = None
        self.caption = ""
        self.bitmap = None
        self.dis_bitmap = None
        self.tooltip = ""
        self.rect = (0, 0, 0, 0)
        self.active = False
        self.enabled = True
        self.hidden = False
        self.hasCloseButton = True
        self.control = None
        self.renamable = False
        self.text_colour = "#000000"
        self.access_time = datetime.datetime.now()

    def IsMultiline(self):
        """Vérifie si le libellé de l'onglet est réparti sur plusieurs lignes.

        Returns:
            bool: ``True`` si ``caption`` contient un saut de ligne (``'\\n'``),
            ``False`` sinon.
        """
        return "\n" in self.caption


class AuiTabContainerButton:
    """Structure décrivant un bouton d'action dans le conteneur d'onglets.

    Représente les boutons affichés dans la barre d'onglets (bouton de fermeture
    général, boutons de défilement gauche/droite, menu déroulant des onglets, etc.).

    Attributes:
        id (int): Identifiant unique du bouton.
        name (str): Nom ou type fonctionnel du bouton (ex. ``'close'``, ``'left'``,
            ``'right'``, ``'window_list'``).
        cur_state (int): État graphique courant du bouton (par ex.
            ``AUI_BUTTON_STATE_NORMAL``, ``AUI_BUTTON_STATE_HOVER``,
            ``AUI_BUTTON_STATE_PRESSED``, ``AUI_BUTTON_STATE_DISABLED``).
        location (str): Côté d'affichage sur la barre (``'left'`` ou ``'right'``).
        bitmap: Image / icône normale du bouton.
        dis_bitmap: Image / icône du bouton lorsqu'il est désactivé.
        rect (tuple[int, int, int, int]): Rectangle englobant (x, y, largeur, hauteur)
            du bouton sur le conteneur.
    """

    def __init__(self):
        """Initialise un bouton de conteneur d'onglets avec les attributs par défaut."""
        self.id = -1
        self.name = ""
        self.cur_state = AUI_BUTTON_STATE_NORMAL
        self.location = "left"
        self.bitmap = None
        self.dis_bitmap = None
        self.rect = (0, 0, 0, 0)


class CommandNotebookEvent:
    """Événement de commande simulant les événements AuiNotebook de wxPython.

    Transporte les informations relatives aux interactions utilisateur sur
    le carnet d'onglets : changement de sélection de page, annulation ou validation
    d'édition de libellé, opérations de glisser-déposer, etc.

    Attributes:
        event_type: Type ou identifiant de l'événement.
        win_id (int): Identifiant de la fenêtre émettrice.
        old_selection (int): Index de la page précédemment sélectionnée (-1 si aucune).
        selection (int): Index de la page sélectionnée (-1 si aucune).
        drag_source: Référence à la source du glisser-déposer.
        dispatched (int): Indicateur d'état de diffusion de l'événement.
        label (str): Libellé textuel associé à l'événement (ex. nouveau titre après édition).
        editCancelled (bool): Indique si l'édition de titre a été annulée.
        page: Référence vers l'objet page (``AuiNotebookPage``) concerné.
        _commandInt (int): Valeur entière interne synchronisée avec la sélection.
    """

    def __init__(self, command_type=None, win_id=0):
        """Initialise l'événement de commande du carnet d'onglets.

        Args:
            command_type: Identifiant ou type de l'événement.
            win_id (int, optional): Identifiant numérique de la fenêtre (0 par défaut).
        """
        self.event_type = command_type
        self.win_id = win_id
        self.old_selection = -1
        self.selection = -1
        self.drag_source = None
        self.dispatched = 0
        self.label = ""
        self.editCancelled = False
        self.page = None
        self._commandInt = 0

    def SetSelection(self, value):
        """Définit l'index de la page sélectionnée.

        Args:
            value (int): Index de sélection.
        """
        self.selection = value
        self._commandInt = value

    def GetSelection(self):
        """Renvoie l'index de la page sélectionnée.

        Returns:
            int: Index de la page sélectionnée (-1 si aucune).
        """
        return self.selection

    def SetOldSelection(self, value):
        """Définit l'index de la page précédemment sélectionnée.

        Args:
            value (int): Ancien index de sélection.
        """
        self.old_selection = value

    def GetOldSelection(self):
        """Renvoie l'index de la page précédemment sélectionnée.

        Returns:
            int: Ancien index de sélection (-1 si aucune).
        """
        return self.old_selection

    def SetDragSource(self, value):
        """Définit l'objet source de l'opération de glisser-déposer.

        Args:
            value: Widget ou conteneur source du glisser.
        """
        self.drag_source = value

    def GetDragSource(self):
        """Renvoie l'objet source de l'opération de glisser-déposer.

        Returns:
            Any: L'objet ou widget source.
        """
        return self.drag_source

    def SetDispatched(self, value):
        """Définit l'indicateur de diffusion de l'événement.

        Args:
            value (int): Valeur d'état de diffusion.
        """
        self.dispatched = value

    def GetDispatched(self):
        """Renvoie l'indicateur de diffusion de l'événement.

        Returns:
            int: Valeur d'état de diffusion.
        """
        return self.dispatched

    def IsEditCancelled(self):
        """Indique si l'édition de texte a été annulée.

        Returns:
            bool: ``True`` si l'édition est annulée, ``False`` sinon.
        """
        return self.editCancelled

    def SetEditCanceled(self, value=True):
        """Définit l'état d'annulation de l'édition de texte.

        Args:
            value (bool, optional): ``True`` pour marquer l'édition comme annulée
                (``True`` par défaut).
        """
        self.editCancelled = value

    def GetLabel(self):
        """Renvoie le libellé textuel associé à l'événement.

        Returns:
            str: Libellé ou titre d'onglet.
        """
        return self.label

    def SetLabel(self, value):
        """Définit le libellé textuel associé à l'événement.

        Args:
            value (str): Nouveau libellé.
        """
        self.label = value


class AuiNotebookEvent:
    """Événement de notification avec mécanisme de veto pour AuiNotebook.

    Simule le comportement de ``wx.NotifyEvent``. Les récepteurs de cet événement
    peuvent appeler :meth:`Veto` pour annuler l'action prévue (comme la fermeture
    d'un onglet ou le changement de page active).

    Attributes:
        notify_event: Type ou identifiant de l'événement notifié.
        allowed (bool): Indique si l'action est autorisée (vrai par défaut).
        event_type: Type de l'événement (identique à notify_event).
        win_id (int): Identifiant de la fenêtre concernée.
    """

    def __init__(self, command_type=None, win_id=0):
        """Initialise l'événement de notification.

        Args:
            command_type: Type ou identifiant de l'événement notifié.
            win_id (int, optional): Identifiant de la fenêtre émettrice (0 par défaut).
        """
        self.notify_event = command_type
        self.allowed = True
        self.event_type = command_type
        self.win_id = win_id

    def GetNotifyEvent(self):
        """Renvoie le type ou identifiant de l'événement notifié.

        Returns:
            Any: Type de l'événement de notification.
        """
        return self.notify_event

    def IsAllowed(self):
        """Indique si l'action déclenchée par l'événement est permise.

        Returns:
            bool: ``True`` si l'action est autorisée, ``False`` si un veto a été posé.
        """
        return self.allowed

    def Veto(self):
        """Pose un veto sur l'action associée à l'événement pour empêcher son exécution."""
        self.allowed = False

    def Allow(self):
        """Autorise l'exécution de l'action associée à l'événement."""
        self.allowed = True


class TabNavigatorProps:
    """Structure de configuration et de données pour le dialogue TabNavigatorWindow.

    Regroupe l'état nécessaire à l'affichage et à la sélection d'un onglet au sein
    de la fenêtre modale de navigation.

    Attributes:
        notebook: Référence vers l'instance du carnet d'onglets (``AuiNotebook``).
        tabCtrl: Référence vers le contrôle d'onglets (``AuiTabCtrl``).
        selectedPage (int): Index de la page sélectionnée dans le dialogue (-1 si aucune).
        activePage (int): Index de la page qui était active à l'ouverture du dialogue.
        pages (list): Liste des pages (instances de ``AuiNotebookPage``) à présenter.
        itemList (list): Liste d'éléments additionnels ou identifiants.
        bitmapSize (tuple[int, int]): Dimensions (largeur, hauteur) des icônes d'onglets.
    """

    def __init__(self):
        """Initialise les propriétés du navigateur avec des valeurs par défaut."""
        self.notebook = None
        self.tabCtrl = None
        self.selectedPage = -1
        self.activePage = -1
        self.pages = []
        self.itemList = []
        self.bitmapSize = (0, 0)


class TabNavigatorWindow(tk.Toplevel):
    """Fenêtre modale de navigation et de sélection des onglets.

    Fournit une boîte de dialogue (analogue au sélecteur Ctrl+Tab) affichant la
    liste des onglets d'un ``AuiNotebook`` au sein d'un composant ``ttk.Treeview``.
    L'utilisateur peut parcourir les pages au clavier ou à la souris, valider son
    choix (Entrée ou double-clic), ou annuler (Échap).

    ``ttk.Treeview`` est utilisé pour afficher les pages, car il permet de
    conserver une structure extensible si le navigateur évolue ensuite vers
    plusieurs groupes d'onglets.

    Attributes:
        props (TabNavigatorProps): Données et état de la sélection des onglets.
        tree (ttk.Treeview): Composant d'affichage tabulaire listant les onglets.
    """

    def __init__(self, parent, props=None):
        """Initialise et affiche la fenêtre modale de navigation des onglets.

        Args:
            parent (tk.Misc): Widget parent de la fenêtre modale.
            props (TabNavigatorProps, optional): Propriétés de navigation contenant
                la liste des pages et la sélection par défaut.
        """
        super().__init__(parent)
        self.props = props or TabNavigatorProps()
        self.transient(parent)
        self.title("Select tab")
        self.resizable(False, False)

        # Configuration du Treeview avec une colonne unique pour le titre de l'onglet
        self.tree = ttk.Treeview(
            self, columns=("caption",), show="headings", selectmode="browse", height=12
        )
        self.tree.heading("caption", text="Tab")
        self.tree.column("caption", width=260, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)  # à changer en grid !?

        # Liaisons pour la sélection et la fermeture
        self.tree.bind("<Double-1>", self.OnItemSelected)
        self.tree.bind("<Return>", self.OnItemSelected)
        self.bind("<Escape>", self.CloseDialog)

        # Peuplement de la liste et activation du mode modal
        self.PopulateListControl()
        self.grab_set()
        self.tree.focus_set()

    def OnLeftDown(self, event):
        """Enregistre les coordonnées du clic de souris initial.

        Args:
            event (tk.Event): L'événement de clic souris reçu.
        """
        self._press = (event.x, event.y)

    def OnLeftUp(self, event):
        """Gestionnaire de relâchement du clic gauche (conservé pour compatibilité wx).

        Args:
            event (tk.Event): L'événement de relâchement souris.
        """
        pass

    def OnMotion(self, event):
        """Gestionnaire de déplacement de la souris (conservé pour compatibilité wx).

        Args:
            event (tk.Event): L'événement de mouvement souris.
        """
        pass

    def OnKeyUp(self, event):
        """Gère le relâchement d'une touche du clavier.

        Ferme la boîte de dialogue lorsque la touche Échap est relâchée.

        Args:
            event (tk.Event): L'événement clavier reçu.
        """
        if event.keysym == "Escape":
            self.CloseDialog(event)

    def OnNavigationKey(self, event):
        """Traite les touches de navigation clavier (conservé pour compatibilité wx).

        Args:
            event (tk.Event): L'événement clavier.

        Returns:
            None
        """
        return None

    def PopulateListControl(self):
        """Remplit le Treeview avec la liste des pages d'onglets.

        Vide d'abord les entrées existantes, insère chaque page de ``self.props.pages``
        avec son index comme identifiant (iid) et son libellé comme valeur, puis
        active la sélection sur l'onglet sélectionné (``selectedPage``).
        """
        # Réinitialisation des éléments affichés
        for item in self.tree.get_children(""):
            self.tree.delete(item)

        # Ajout des pages avec leur index numérique (iid)
        for index, page in enumerate(getattr(self.props, "pages", [])):
            caption = getattr(page, "caption", str(page))
            self.tree.insert("", "end", iid=str(index), values=(caption,))

        # Mise en évidence et défilement vers l'élément sélectionné
        selected = getattr(self.props, "selectedPage", -1)
        if 0 <= selected < len(self.tree.get_children("")):
            item = str(selected)
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.tree.see(item)

    def OnItemSelected(self, event=None):
        """Enregistre l'onglet choisi dans les propriétés et ferme la fenêtre.

        Args:
            event (tk.Event, optional): Événement déclencheur (double-clic ou Entrée).

        Returns:
            str: ``"break"`` pour interrompre le traitement standard de l'événement dans Tkinter.
        """
        selection = self.tree.selection()
        if selection:
            self.props.selectedPage = int(selection[0])
        self.CloseDialog(event)
        return "break"

    def CloseDialog(self, event=None):
        """Libère la capture modale et détruit la fenêtre de dialogue.

        Args:
            event (tk.Event, optional): Événement déclencheur éventuel.
        """
        try:
            # Libère la capture exclusive des événements de la fenêtre
            self.grab_release()
        finally:
            # Garantit la destruction de la fenêtre même en cas d'anomalie
            self.destroy()

    def GetSelectedPage(self):
        """Renvoie l'index de la page sélectionnée par l'utilisateur.

        Returns:
            int: L'index de la page sélectionnée, ou -1 si aucune sélection.
        """
        return getattr(self.props, "selectedPage", -1)

    def OnPanelPaint(self, event):
        """Gestionnaire de redessin (stub conservé pour compatibilité d'interface wx).

        Args:
            event: Événement de dessin.
        """
        pass

    def OnPanelEraseBg(self, event):
        """Gestionnaire d'effacement du fond (stub conservé pour compatibilité d'interface wx).

        Args:
            event: Événement d'effacement d'arrière-plan.
        """
        pass
