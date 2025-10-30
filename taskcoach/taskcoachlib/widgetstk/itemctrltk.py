# Résumé de la conversion de itemctrl.py pour Tkinter
#
# La conversion directe du fichier itemctrl.py de wxPython vers Tkinter
# est impossible en raison de différences fondamentales d'architecture
# entre les deux frameworks. L'approche correcte consiste à
# réécrire la logique en utilisant les classes et les méthodes de Tkinter
# et de son module ttk.
#
# J'ai réécrit le code de itemctrl.py en créant des mixins et des classes
# adaptées à l'environnement Tkinter. Ce nouveau code, conçu pour
# être utilisé dans le dossier widgetstk que vous avez mentionné,
# permet de reproduire les fonctionnalités principales de la version wxPython.
#
# Points clés de la conversion
#
#     Remplacement des classes wxPython : Les classes de base comme
#     _CtrlWithItemsMixin, _CtrlWithPopupMenuMixin, et les autres mixins
#     de la version wxPython ont été remplacés par des mixins Tkinter.
#     Le ttk.Treeview est utilisé comme équivalent du wx.TreeCtrl et du wx.TreeListCtrl.
#
#     Gestion des événements : Les événements wxPython
#     (ex: wx.EVT_CONTEXT_MENU, wx.EVT_LIST_COL_CLICK) sont remplacés par
#     les événements correspondants de Tkinter (ex: <Button-3>, <Button-1>).
#
#     Mixins et dépendances :
#
#         _CtrlWithDropTargetMixin : J'ai utilisé le module tkinter.dnd et
#         la classe FileTextDropTarget pour gérer les opérations de
#         glisser-déposer de fichiers et de texte, en s'appuyant sur le code
#         que vous aviez déjà pour draganddrop.py.
#
#         CtrlWithToolTipMixin : Le code réécrit utilise la classe ToolTip
#         du module tooltip.py pour afficher les info-bulles.
#
#         _CtrlWithAutoResizedColumnsMixin : Cette fonctionnalité est gérée
#         par la classe TaskList de votre fichier autowidth.py en
#         liant l'événement <Configure>. Une logique pour la colonne redimensionnable a été intégrée.
#
#     Logique de tri et de colonne : La logique pour gérer le tri des colonnes
#     (_CtrlWithSortableColumnsMixin) et les colonnes masquables
#     (_CtrlWithHideableColumnsMixin) a été adaptée à la manière dont le
#     ttk.Treeview gère les en-têtes et les largeurs de colonnes.

# Voici un résumé des points clés de la conversion et des éléments à considérer pour compléter le fichier itemctrltk.py afin de le rendre fonctionnel:
# 1. Architecture Générale et Mixins
#
# L'approche de conversion consiste à utiliser des mixins pour ajouter des fonctionnalités au widget principal, qui est un ttk.Treeview . Les mixins fournissent un moyen d'ajouter des fonctionnalités telles que la gestion du menu contextuel, la prise en charge du glisser-déposer, l'affichage des info-bulles, le masquage des colonnes et le tri des colonnes  .
# Les classes de base wxPython ont été remplacées par des mixins Tkinter, notamment _CtrlWithItemsMixin, _CtrlWithPopupMenuMixin et d'autres .
# Le ttk.Treeview est utilisé comme équivalent de wx.TreeCtrl et wx.TreeListCtrl .
#
# 2. Dépendances et Modules Externes
#
# draganddroptk.py: utilisé pour la gestion du glisser-déposer de fichiers et de texte via _CtrlWithDropTargetMixin  .
# tooltiptk.py: utilisé pour afficher les info-bulles via la classe ToolTip et le mixin CtrlWithToolTipMixin .
# autowidthtk.py: utilisé pour la gestion automatique de la largeur des colonnes via la classe TaskList et l'événement <Configure> .
# Il est important de noter que le module tkinter.dnd est utilisé pour gérer les opérations de glisser-déposer. Le module tkinter.dnd est assez basique et nécessite que la source et la cible implémentent des méthodes spécifiques .
# PIL (Pillow): C'est un module externe très courant pour gérer les images et les icônes .
#
# 3. Éléments à vérifier et à compléter
#
# Gestion des événements: Assurez-vous que tous les événements nécessaires sont correctement liés dans Tkinter. Les événements wxPython comme wx.EVT_CONTEXT_MENU et wx.EVT_LIST_COL_CLICK doivent être remplacés par leurs équivalents Tkinter comme <Button-3> (clic droit) et <Button-1> (clic gauche) .
# Implémentation des méthodes abstraites: La classe TreeCtrlDragAndDropMixin dans draganddroptk.py requiert que la méthode OnDrop soit surchargée dans la classe dérivée . Assurez-vous que cette méthode est correctement implémentée dans votre classe TaskList ou toute autre classe qui utilise ce mixin.
# Compatibilité du glisser-déposer: Le module tkinter.dnd a des limitations. Il faut donc s'assurer que les méthodes requises par tkinter.dnd sont implémentées correctement, comme dnd_enter_callback, dnd_leave_callback et dnd_end_callback  .
# Gestion des données: Dans wxPython, les données sont gérées par les DataObjects . Dans Tkinter, il faut stocker les informations directement dans l'instance de la classe, par exemple en utilisant les tags des éléments du Treeview  .
# Implémentation de getItemTooltipData: La classe CtrlWithToolTipMixin utilise la méthode getItemTooltipData pour obtenir le texte de l'info-bulle. Vous devez implémenter cette méthode dans votre classe dérivée (par exemple, TaskList) pour retourner la chaîne d'info-bulle appropriée  .
# Menu contextuel: La gestion des menus contextuels pour les éléments et les en-têtes de colonnes (_CtrlWithItemPopupMenuMixin et _CtrlWithColumnPopupMenuMixin) nécessite une attention particulière, car Tkinter ne fournit pas d'événements directs pour les en-têtes . Il faut donc gérer les clics manuellement.
# Colonnes masquables et triables : Assurez-vous que la logique pour masquer/afficher les colonnes et pour le tri fonctionne correctement avec le ttk.Treeview .
# Gestion de la largeur des colonnes :  Dans la méthode on_resize, assurez-vous que le calcul de la largeur de la colonne redimensionnable est correct et que la largeur minimale est respectée .
#
# En complétant ces éléments, vous devriez être en mesure de rendre votre widget itemctrltk.py fonctionnel et de reproduire les fonctionnalités de la version wxPython.

# D'après les fichiers que vous avez fournis, itemctrltk.py est une réécriture de itemctrl.py en utilisant Tkinter et ttk pour remplacer wxPython. L'idée est d'utiliser des mixins pour ajouter des fonctionnalités à un ttk.Treeview, comme la gestion des menus contextuels, le glisser-déposer, les info-bulles, le masquage et le tri des colonnes  .
# Analyse des fichiers et des mixins disponibles:
#
# _CtrlWithItemsMixin: Fournit des méthodes de base pour interagir avec les éléments du Treeview .
# _CtrlWithPopupMenuMixin: Ajoute la gestion des menus contextuels .
# _CtrlWithItemPopupMenuMixin: Gère les menus contextuels spécifiques aux éléments .
# _CtrlWithColumnPopupMenuMixin: Gère les menus contextuels pour les en-têtes de colonne .
# _CtrlWithDropTargetMixin: Permet le glisser-déposer de fichiers et d'URLs . Utilise draganddroptk.py pour la gestion du drag-and-drop .
# CtrlWithToolTipMixin: Ajoute des info-bulles à chaque élément. Utilise tooltiptk.py pour afficher les info-bulles .
# _CtrlWithHideableColumnsMixin: Gère l'affichage et le masquage des colonnes .
# _CtrlWithSortableColumnsMixin: Ajoute le tri des colonnes en cliquant sur l'en-tête .
# _CtrlWithAutoResizedColumnsMixin: Gère le redimensionnement automatique des colonnes. Utilise autowidthtk.py pour cette fonctionnalité .
# CtrlWithColumnsMixin: Combine les mixins pour la gestion des colonnes .
# TaskList: La classe principale qui combine tous les mixins et hérite de ttk.Treeview .
#
# Implémentation des méthodes manquantes et finalisation de la conversion:
# Voici une liste de points à vérifier et à compléter, en m'appuyant sur les mixins et les classes disponibles :
#
#
# OnDrop (Glisser-Déposer) :
#
# La classe TreeCtrlDragAndDropMixin dans draganddroptk.py requiert que la méthode OnDrop soit surchargée dans la classe dérivée (TaskList ou une autre classe). Cette méthode est essentielle pour définir ce qui se passe lorsqu'un élément est déposé [[15]]  .
# Assurez-vous que la méthode OnDrop est correctement implémentée dans votre classe TaskList ou toute autre classe qui utilise le mixin TreeCtrlDragAndDropMixin.
# Cette méthode doit définir la logique de déplacement des éléments dans l'arborescence, en utilisant les méthodes move du ttk.Treeview  .
#
# Gestion des colonnes et des en-têtes :
#
# Assurez-vous que la logique pour masquer/afficher les colonnes et pour le tri fonctionne correctement avec le ttk.Treeview  .
# La classe Column dans itemctrltk.py définit les propriétés des colonnes .
# Les mixins _CtrlWithHideableColumnsMixin et _CtrlWithSortableColumnsMixin utilisent ces propriétés pour gérer l'affichage, le masquage et le tri des colonnes  .
# Vérifiez que les méthodes showColumn, sort_by, etc., fonctionnent comme prévu et que les en-têtes des colonnes sont correctement configurés.
#
#
#
# Gestion de la largeur des colonnes :
#
# Dans la méthode on_resize de la classe TaskList, assurez-vous que le calcul de la largeur de la colonne redimensionnable est correct et que la largeur minimale est respectée  .
# Utilisez autowidthtk.py comme référence pour cette implémentation .
#
#
#
# Menu contextuel pour les en-têtes de colonne :
#
# La gestion des menus contextuels pour les éléments et les en-têtes de colonnes (_CtrlWithItemPopupMenuMixin et _CtrlWithColumnPopupMenuMixin) nécessite une attention particulière, car Tkinter ne fournit pas d'événements directs pour les en-têtes  .
# Vous devrez peut-être créer un widget personnalisé pour les en-têtes de colonnes afin de gérer les clics droit et d'afficher le menu contextuel correspondant.
#
#
#
# Compatibilité du glisser-déposer :
#
# Le module tkinter.dnd a des limitations.
# Assurez-vous que les méthodes requises par tkinter.dnd sont implémentées correctement,
# comme dnd_enter_callback, dnd_leave_callback et dnd_end_callback.

# La Solution : Rendre les Mixins "Non-Coopératifs"
#
# Puisque VirtualListCtrl (votre "TreeListCtrl" pour listes) gère l'initialisation explicitement,
# les mixins dans itemctrltk.py ne doivent pas utiliser super().__init__ pour propager les arguments.
# Ils doivent agir comme de simples fonctions de configuration.
# Voici les modifications requises dans itemctrltk.py pour s'adapter à votre architecture :
#
# 1. Fichier : itemctrltk.py
#
# Modifiez les __init__ de tous les mixins de base pour qu'ils n'appellent plus super().__init__.

# Résumé des corrections
#
#     notetk.py : Vous utilisiez un ttk.Treeview basique. Nous l'avons remplacé par votre treectrltk.TreeListCtrl personnalisé, qui est ce que les classes de base (comme SortableViewerWithColumns) attendent.
#
#     itemctrltk.py : Nous avons implémenté les méthodes showSortColumn et showSortOrder (attendues par basetk.py) dans le mixin _CtrlWithSortableColumnsMixin. Ces méthodes gèrent maintenant l'affichage des flèches de tri dans les en-têtes du Treeview.
import tkinter as tk
from tkinter import ttk, Menu, PhotoImage
import logging
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.widgetstk import draganddroptk
from taskcoachlib.widgetstk import tooltiptk
from taskcoachlib.widgetstk import autowidthtk

log = logging.getLogger(__name__)


# --- Mixins de base pour Tkinter (équivalent des mixins wxPython) ---

# Étapes d’intégration
#
# Ajouter des attributs internes dans _CtrlWithItemsMixin pour stocker :
#
# l’item actuellement édité,
#
# la colonne actuellement éditée,
#
# et le widget Entry temporaire.
#
# Gérer le double-clic pour déclencher l’édition.
#
# Créer un champ Entry temporaire pour saisir le nouveau texte.
#
# Mettre à jour la cellule quand l’utilisateur valide (ou annule).
#
# Fournir une méthode publique item_being_edited() (équivalent de TreeTextCtrl.item()).

# Ce que cela fait :
#
# Double-clic → création d’un champ Entry pour modifier la cellule.
#
# Appuyer sur Entrée → enregistre le texte.
#
# Appuyer sur Échap ou cliquer ailleurs → annule.
#
# Tu peux appeler self.item_being_edited() pour savoir quel item est en train d’être modifié.
class _CtrlWithItemsMixin:
    """
    Classe de base pour les contrôles contenant des éléments (ici, ttk.Treeview).

    Fournit des méthodes de base pour interagir avec les éléments du Treeview.
    """
    # Solution : Retirer les Arguments de Callback dans _CtrlWithItemsMixin
    # def __init__(self, *args, **kwargs):
    def __init__(self, master, *args, **kwargs):  # master est le premier argument positionnel
        # Ce mixin est le point où super() atteint finalement object.
        # self est l'instance de VirtualListCtrl (le widget).
        # master, *args, **kwargs sont les arguments passés par VirtualListCtrl.
        # Stockons master pour qu'il soit disponible pour les callbacks (ex: tooltips)
        self.__master = master  # Stocker master pour utilisation ultérieure si nécessaire

        # NOUVEAU CODE : Retirer les callbacks de kwargs spécifiques à ce mixin (items)
        self.selectCommand = kwargs.pop("selectCommand", None)
        self.editCommand = kwargs.pop("editCommand", None)
        # Solution : Retirer l'Appel super().__init__ dans les Mixins Abstraits
        #
        # Nous allons corriger les constructeurs des mixins
        # qui n'héritent pas d'un widget Tkinter
        # pour qu'ils n'appellent pas super().__init__(master, ...)
        # et stoppent la propagation de ces arguments vers object.__init__.
        # super().__init__(*args, **kwargs)
        # Consommer le 'master' positionnel pour ne pas le propager à object.__init__
        # Nous n'avons pas besoin de stocker master car self est le widget.

        # MRO va propager l'appel super() à object.
        # object.__init__ n'accepte que self.
        # Donc, nous appelons super() SANS arguments.
        # Nous devons appeler le constructeur de object sans lui passer d'arguments.
        # L'appel super().__init__() atteindra object.__init__()
        # et doit être appelé SANS arguments, car object.__init__(self) n'en prend pas.

        # ATTENTION : Si _CtrlWithItemsMixin est le premier mixin de la liste d'héritage
        # de VirtualListCtrl, il doit appeler le constructeur de ttk.Treeview/Frame
        # S'il ne l'est pas, il doit appeler super() sans arguments.

        # Puisque VirtualListCtrl gère l'initialisation de ttk.Treeview explicitement
        # dans listctrltk.py, les mixins abstraits ne doivent rien propager à object.

        # # Si le mixin est une classe abstraite qui n'hérite de rien d'autre que object:
        # super().__init__()  # Appelle object.__init__(self), fonctionne.
        # NE PAS appeler super().__init__()
        # Note : Étant donné l'héritage complexe, assurez-vous que object.__init__()
        # est le seul constructeur appelé par ce super()
        # et non un autre mixin qui aurait besoin de ces arguments.
        # L'approche la plus simple est de ne propager aucun argument vers object.

        # Note : Si ces arguments étaient passés positionnellement ou via *args,
        # ils ne seraient pas dans **kwargs. Cependant,
        # le code de listctrltk.py les passe par mot-clé,
        # donc .pop() est la bonne solution.
        # Retirer les arguments qui ne sont pas consommés par ce mixin mais qui sont propagés
        # par des appels super() (car ils sont destinés à ttk.Treeview)

        # Correction de la propagation (les mixins abstraits ne doivent pas propager d'arguments non consommés)

        self._entry = None
        self._editing_item = None
        self._editing_column = None
        # # Bind double-clic pour activer l’édition
        # ANCIEN CODE (CAUSE L'ERREUR DANS LE MRO)
        # self.bind("<Double-1>", self._on_double_click)
        # NOUVEAU CODE (Corriger l'erreur en retirant les bindings ici)
        # La logique de binding doit être déplacée vers la classe CONCRÈTE (VirtualListCtrl ou TaskTree)
        # ou gérée par un mixin qui sait qu'il est la racine du widget.

        # Solution : Laisser _CtrlWithItemsMixin abstrait et gérer le bind dans la classe concrète.
        # En résumé : Le problème était que
        # le code bind s'exécutait sur une instance de mixin non-widget.
        # En le retirant du mixin abstrait, et
        # en ne le plaçant que sur les classes concrètes (comme VirtualListCtrl),
        # nous évitons l'erreur d'architecture.

    def _itemIsOk(self, item):
        """Vérifie si un élément (item) du Treeview est valide."""
        return item != ''

    def _objectBelongingTo(self, item):
        """Retourne les tags (ou autres données associées) d’un item."""
        if not self._itemIsOk(item):
            return None
        # return self.item(item, 'tags')  # Utilise les tags pour stocker les données
        # En Tkinter, item() retourne un dictionnaire avec toutes les propriétés
        return self.item(item).get('tags', None)
        # item(self) vient de thirdparty.customtreectrl.TreeTextCtrl qui est une classe héritée de wx.lib.expando.ExpandoTextCtrl hérité de wx.TextCtrl.
        # Returns the item currently edited.

    # Description : Cette méthode sélectionne ou désélectionne un élément dans le contrôle.
    # Dans wxPython, elle utilise SelectItem pour TreeCtrl et TreeListCtrl,
    # et SetItemState pour ListCtrl .
    # Version Tkinter : La version Tkinter utilise selection_set et selection_remove du ttk.Treeview .
    def SelectItem(self, item, select=True):
        """Sélectionne ou désélectionne un élément."""
        if select:
            self.selection_set(item)
        else:
            self.selection_remove(item)

    # --- Partie édition directe ---
    def _on_double_click(self, event):
        """Commence l’édition du texte d’une cellule."""
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return

        item = self.identify_row(event.y)
        column = self.identify_column(event.x)
        x, y, width, height = self.bbox(item, column)
        value = self.set(item, column)

        # Création de l’Entry
        self._entry = tk.Entry(self)
        self._entry.place(x=x, y=y, width=width, height=height)
        self._entry.insert(0, value)
        self._entry.focus()

        self._editing_item = item
        self._editing_column = column

        # Bindings pour valider ou annuler
        self._entry.bind("<Return>", self._save_edit)
        self._entry.bind("<Escape>", self._cancel_edit)
        self._entry.bind("<FocusOut>", self._cancel_edit)

    def _save_edit(self, event=None):
        """Valide la modification du texte."""
        new_value = self._entry.get()
        self.set(self._editing_item, self._editing_column, new_value)
        self._end_edit()

    def _cancel_edit(self, event=None):
        """Annule l’édition sans enregistrer."""
        self._end_edit()

    def _end_edit(self):
        """Nettoie les variables et détruit l’Entry."""
        if self._entry:
            self._entry.destroy()
            self._entry = None
        self._editing_item = None
        self._editing_column = None

    def item_being_edited(self):
        """Équivalent de TreeTextCtrl.item() — retourne l’item en cours d’édition."""
        return self._editing_item


class _CtrlWithPopupMenuMixin(_CtrlWithItemsMixin):
    """
    Classe de base pour les contrôles avec un menu contextuel.

    Ajoute la gestion des menus contextuels.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)  # <-- Doit propager à _CtrlWithItemsMixin

    def _attachPopupMenu(self, widget, handler):
        """Lie un gestionnaire d'événements pour le menu contextuel."""
        widget.bind("<Button-3>", handler)  # Clic droit


class _CtrlWithItemPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """
    Menu contextuel pour des éléments spécifiques du Treeview.

    Gère les menus contextuels spécifiques aux éléments.
    """

    # def __init__(self, *args, **kwargs):
    def __init__(self, master, *args, **kwargs):  # <-- C'est correct, il propage tout à _CtrlWithItemsMixin
        log.debug("_CtrlWithItemPopupMenuMixin.__init__ : Initialisation du menu contextuel sur les éléments.")
        self.__popupMenu = kwargs.pop("itemPopupMenu", None)
        # super().__init__(*args, **kwargs)
        super().__init__(master, *args, **kwargs)
        if self.__popupMenu:
            self._attachPopupMenu(self, self.onItemPopupMenu)
        log.debug("_CtrlWithItemPopupMenuMixin initialisé !")

    def onItemPopupMenu(self, event):
        """Affiche le menu contextuel pour un élément du Treeview."""
        item = self.identify_row(event.y)
        if self._itemIsOk(item):
            # Sélectionne l'élément avant d'afficher le menu
            self.selection_set(item)
            try:
                self.__popupMenu.tk_popup(event.x_root, event.y_root)
            finally:
                self.__popupMenu.grab_release()


class _CtrlWithColumnPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """
    Menu contextuel pour les en-têtes de colonnes du Treeview.

    Gère les menus contextuels pour les en-têtes de colonne .
    """

    def __init__(self, *args, **kwargs):
        log.debug("_CtrlWithColumnPopupMenuMixin.__init__ : Initialisation du menu contextuel sur les en-têtes de colonnes.")
        self.__popupMenu = kwargs.pop("columnPopupMenu", None)
        super().__init__(*args, **kwargs)
        if self.__popupMenu:
            self._attachPopupMenu(self.heading_widget, self.onColumnPopupMenu)
        log.debug("_CtrlWithColumnPopupMenuMixin initialisé !")

    def onColumnPopupMenu(self, event):
        """Affiche le menu contextuel pour une colonne."""
        # Identification de la colonne cliquée
        # Tkinter ne fournit pas d'événement direct pour les en-têtes.
        # Nous devons donc le gérer manuellement via un surclassement ou une gestion des clics.
        # Pour cet exemple, on peut supposer que l'objet popupMenu gère l'information de la colonne.
        try:
            self.__popupMenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.__popupMenu.grab_release()


# Description : Ce mixin permet aux contrôles d'accepter les fichiers,
# URLs ou e-mails déposés . Il utilise draganddrop.DropTarget de wxPython.
# Version Tkinter : La version Tkinter utilise draganddroptk.FileTextDropTarget
# pour gérer les drops. Les callbacks onDropURL, onDropFiles, et onDropMail
# sont gérés par une seule méthode _handle_drop_callback .
class _CtrlWithDropTargetMixin(_CtrlWithItemsMixin):  # <--- Erreur MRO potentielle
    """
    Permet aux contrôles d'accepter des fichiers ou du texte déposés.

    Permet le glisser-déposer de fichiers et d'URLs.
    Utilise draganddroptk.py pour la gestion du drag-and-drop.
    """

    def __init__(self, *args, **kwargs):
        log.debug("_CtrlWithDropTargetMixin.__init__ : Initialisation pour le glisser-déposer.")
        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)
        # Propager le reste
        super().__init__(*args, **kwargs)

        # Initialise le gestionnaire de glisser-déposer de draganddrop.py
        if self.__onDropFilesCallback or self.__onDropURLCallback or self.__onDropMailCallback:
            self.drop_target = draganddroptk.FileTextDropTarget(
                self, self._handle_drop_callback)
        log.debug("_CtrlWithDropTargetMixin initialisé !")

    # Assurez-vous que cette méthode gère correctement les différents types
    # de données déposées (fichiers, URLs, texte) et appelle les callbacks
    # appropriés (__onDropFilesCallback, __onDropURLCallback, __onDropMailCallback).
    # L'extrait de code suivant est une autre version de la méthode, plus claire.
    def _handle_drop_callback(self, data):
        """Gestionnaire de rappel générique pour le glisser-déposer."""
        # # On suppose que les données sont des fichiers ou du texte (URL, etc.)
        # if isinstance(data, list):  # C'est une liste de fichiers
        #     # C'est un eliste de fichiers
        #     if self.__onDropFilesCallback:
        #         # La méthode onDropFiles nécessite l'élément cible et la liste des fichiers
        #         # Note: ici, on n'a pas les coordonnées, donc on l'applique à la sélection active
        #         selected_item = self.focus()   # Obtient l'élément sélectionné
        #         self.__onDropFilesCallback(self._objectBelongingTo(selected_item), data)
        # else:  # C'est une chaîne de caractères (URL ou mail)
        #     if data.startswith("http://") or data.startswith("https://"):
        #         if self.__onDropURLCallback:
        #             selected_item = self.focus()
        #             self.__onDropURLCallback(self._objectBelongingTo(selected_item), data)
        #     # Logique pour le mail non implémentée dans la version Tkinter de draganddrop
        #     else:
        #         if self.__onDropMailCallback:
        #             selected_item = self.focus()
        #             self.__onDropMailCallback(self._objectBelongingTo(selected_item), data)
        # On suppose que les données sont des fichiers ou du texte (URL, etc.)
        selected_item = self.focus()  # Obtient l'élément sélectionné
        item_data = self._objectBelongingTo(selected_item)  # Récupère les données de l'élément

        if isinstance(data, list):  # C'est une liste de fichiers
            if self.__onDropFilesCallback:
                self.__onDropFilesCallback(item_data, data)  # Passe les données à la callback
        elif isinstance(data, str):  # C'est une chaîne de caractères (URL ou mail)
            if data.startswith("http://") or data.startswith("https://"):
                if self.__onDropURLCallback:
                    self.__onDropURLCallback(item_data, data)
            else:  # considéré comme "mail" ou autre texte
                if self.__onDropMailCallback:
                    self.__onDropMailCallback(item_data, data)

    def GetMainWindow(self):
        """Retourne la fenêtre principale."""
        # return self.winfo_toplevel()
        # TODO : A revoir !
        # try:
        # Tenter l'appel normal
        if isinstance(self, (tk.Tk, tk.Toplevel)):
            return self.winfo_toplevel()
        else:
            # except Exception as e:
            # log.error(f"Erreur lors de l'appel à winfo_toplevel: {e}")
            log.error("_CtrlWithDropTargetMixin.GetMainWindow : Erreur lors de l'appel à winfo_toplevel sur self !")
            # Retourner l'objet Tkinter racine s'il est accessible,
            # ou un objet parent connu (Viewer)
            if hasattr(self, 'master') and self.__master:
                # Si le parent est disponible, retourner sa racine
                return self.__master.winfo_toplevel()
            # Sinon, retourner l'instance Tk la plus simple.
            # (Ceci est une mesure de dernier recours pour éviter le crash)
            return self.__master

    def OnDrop(self, drop_item, dragged_items, part):
        print(f"Éléments glissés: {dragged_items} sur {drop_item} à la position: {part}")
        # # Exemple de déplacement simple
        # for item in dragged_items:
        #     if part == "on":
        #         # Déplacer l'élément pour qu'il devienne un enfant
        #         self.move(item, drop_item, "end")
        #     else:
        #         # Déplacer l'élément au-dessus ou en-dessous
        #         index = self.index(drop_item)
        #         if part == "below":
        #             index += 1
        #         self.move(item, self.parent(drop_item), index)


# La classe CtrlWithToolTipMixin utilise la méthode getItemTooltipData
# pour obtenir le texte de l'info-bulle. Vous devez implémenter cette méthode
# dans votre classe dérivée (par exemple, TaskList) pour retourner la chaîne
# d'info-bulle appropriée.
# class CtrlWithToolTipMixin(_CtrlWithItemsMixin, tooltiptk.ToolTip):
class CtrlWithToolTipMixin(_CtrlWithItemsMixin):  # Retirer l'héritage de tooltiptk.ToolTip qui se fait en interne
    """
    Ajoute des info-bulles personnalisées à chaque élément du Treeview.

    Ajoute des info-bulles à chaque élément.
    Utilise tooltiptk.py pour afficher les info-bulles .
    """

    def __init__(self, *args, **kwargs):
        log.debug("CtrlWithToolTipMixin.__init__ : Initialisation des info-bulles.")
        # self.item_tooltip = tooltiptk.ToolTip(self, text="Default")
        # L'objet `self` (VirtualListCtrl) est un widget Tkinter (Frame/Treeview).
        # # L'initialisation de l'objet ToolTip se fait en interne.
        # super().__init__(*args, **kwargs)  # <-- PROBLÈME
        # Appel explicite au parent mixin
        _CtrlWithItemsMixin.__init__(self, *args, **kwargs)
        # Le ToolTip est initialisé en lui passant le widget `self` (VirtualListCtrl)
        # Il faut s'assurer que self est correctement initialisé avant cet appel.
        self.item_tooltip = tooltiptk.ToolTip(self, text="Default")  # `self` est maintenant le widget
        # (Note : L'argument pour ToolTip doit être self (le widget),
        # ce qui est correct car VirtualListCtrl a déjà appelé ttk.Treeview.__init__.)

        # L'erreur `_w` vient de tooltiptk.ToolTip.__init__ -> self._set_bindings() -> self.widget.bind()
        # Dans tooltiptk.ToolTip, `self.widget` fait référence au widget parent passé au constructeur.
        # L'appel à `self.bind("<Motion>", ...)` doit être fait sur le widget lui-même
        # self.bind("<Motion>", self.on_motion_update_tooltip)
        log.debug("CtrlWithToolTipMixin initialisé !")

    def on_motion_update_tooltip(self, event):
        """Met à jour l'info-bulle en fonction de l'élément survolé."""
        item = self.identify_row(event.y)
        if self._itemIsOk(item):
            domainObject = self._objectBelongingTo(item)
            if domainObject:
                # # Le code d'origine utilise getItemTooltipData qui doit être implémenté
                # # dans la classe dérivée.
                # tooltip_text = self.getItemTooltipData(domainObject)
                # La classe principale (Viewer) implémente getItemTooltipData
                tooltip_text = self.__adapter.getItemTooltipData(domainObject) # Supposons que l'adapter est le viewer
                if tooltip_text:
                    self.item_tooltip.text = tooltip_text
                    self.item_tooltip.show_tooltip_now()
                else:
                    self.item_tooltip.hide_tooltip()
            else:
                self.item_tooltip.hide_tooltip()

# NOTE : Il n'est pas nécessaire de lier "<Motion>" ici car `tooltiptk.ToolTip` le fait déjà
# MAIS, pour la compatibilité avec le code original qui surcharge la gestion de la souris,
# nous devons laisser `CtrlWithToolTipMixin` gérer la liaison d'événement.


# Explication : En forçant CtrlWithItemsMixin (Étape 1)
# à retirer columnPopupMenu et columns,
# nous neutralisons la propagation de ces arguments par la chaîne d'héritage d'Item.
# L'initialisation manuelle dans VirtualListCtrl (Étape 2) garantit que
# ces arguments sont retirés de **kwargs avant l'appel à ttk.Treeview.
#
# Ceci est la solution la plus complète pour gérer le chevauchement d'arguments
# dans cette architecture de mixins.
# En déplaçant le .pop() de selectCommand et editCommand dans CtrlWithItemsMixin
# (qui est le point où les chemins d'héritage se rejoignent),
# et en s'assurant que ttk.Treeview.__init__ est appelé avec des kwargs propres,
# vous devriez résoudre cette TclError persistante.
#
# Vérifiez ensuite si d'autres mixins nécessitent
# l'appel super().__init__(master, *args, **kwargs)
# ou super().__init__(*args, **kwargs)
# ou si la correction de _CtrlWithItemsMixin a suffi.
# class CtrlWithItemsMixin(_CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin, CtrlWithToolTipMixin):
# class CtrlWithItemsMixin(CtrlWithToolTipMixin, _CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin):
class CtrlWithItemsMixin(_CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin):
    """
    Combinaison des mixins pour le comportement d'un Treeview.
    """
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    # pass
    def __init__(self, master, *args, **kwargs):
        # L'ordre d'appel des super() doit respecter le MRO pour passer 'master'
        # L'ordre MRO va appeler :
        # 1. _CtrlWithItemPopupMenuMixin.__init__ (retire itemPopupMenu de kwargs)
        # 2. _CtrlWithDropTargetMixin.__init__ (appelle super(), ne fait rien avec itemPopupMenu)
        # 3. etc., jusqu'à ttk.Treeview, qui ne devrait PLUS voir itemPopupMenu.

        # Consommer les arguments spécifiques AUX ITEMS qui ne sont pas consommés par les parents
        # Ceci est le mixin principal qui doit retirer les arguments de callback.
        _selectCommand = kwargs.pop("selectCommand", None)
        _editCommand = kwargs.pop("editCommand", None)
        # Le problème doit être que `itemPopupMenu` est passé aux mixins de la chaîne
        # `_CtrlWithDropTargetMixin` (dans le MRO).

        # RETIRONS itemPopupMenu DANS CtrlWithItemsMixin POUR GÉRER LE MRO
        # super().__init__(master, *args, **kwargs)
        # # # Stocker l'adapter pour le tooltip
        # # __adapter est initialisé dans le viewer lui-même
        # # self.__adapter = master
        # Le MRO va appeler les parents. Assurons-nous que itemPopupMenu est retiré
        # avant que super() n'atteigne ttk.Treeview via l'autre mixin.

        # Méthode : Appeler explicitement les parents dans l'ordre pour Tkinter (car MRO est capricieux)
        # Consommer les arguments spécifiques aux autres mixins pour ne pas les propager
        # (même si _CtrlWithItemPopupMenuMixin et CtrlWithColumnsMixin le font,
        # cette redondance est nécessaire dans l'approche d'initialisation explicite).
        # 1. Argument pour le parent mixin (géré dans _CtrlWithItemPopupMenuMixin)
        _itemPopupMenu = kwargs.pop("itemPopupMenu", None)  # Retirer ici pour la clarté.

        # 2. Arguments POUR LE MIXIN COLONNE (mais propagés via cette chaîne, donc on les retire)
        # Ceci est nécessaire car CtrlWithItemsMixin appelle super() qui atteint ttk.Treeview via l'autre mixin.
        _columnPopupMenu = kwargs.pop("columnPopupMenu", None)
        _columns = kwargs.pop("columns", [])  # S'il y a des colonnes ici, on les retire aussi.

        # # Initialiser les parents sans super() pour Tkinter.
        # Appels explicites au lieu de super()
        _CtrlWithItemPopupMenuMixin.__init__(self, master, itemPopupMenu=_itemPopupMenu, *args, **kwargs)
        _CtrlWithDropTargetMixin.__init__(self, master, *args, **kwargs)
        # # Propagation à la chaîne d'héritage (qui inclut _CtrlWithItemPopupMenuMixin)
        # # Propager les arguments RESTANTS (master, *args, **kwargs nettoyés)
        # # à la chaîne d'héritage (qui atteindra _CtrlWithItemPopupMenuMixin)
        # super().__init__(master, itemPopupMenu=_itemPopupMenu, *args, **kwargs)  # <-- PROBLÈME

        # Les arguments retirés (_columnPopupMenu, _columns) peuvent être stockés ici
        # ou gérés par la classe appelante (VirtualListCtrl).
        # Stocker les arguments pour la classe concrète si nécessaire
        self.__selectCommand = _selectCommand
        self.__editCommand = _editCommand
        self.__columnPopupMenu = _columnPopupMenu
        self.__columns = _columns  # Stocker si besoin

        # NOTE: CtrlWithItemsMixin est censé n'avoir QUE les args relatifs aux items/menu item/drag.

        # L'objet `self` DOIT être initialisé comme un widget Tk avant d'appeler d'autres constructeurs qui ne sont pas des mixins.
        # Puisque VirtualListCtrl gère l'initialisation de ttk.Treeview (dans listctrltk.py)
        # nous devons nous assurer que les arguments sont filtrés EN AMONT de l'appel.
        pass  # Laissez le super() faire son travail. La solution est dans listctrltk.py.


# Description : Cette classe définit les propriétés d'une colonne.
# Version Tkinter : La version Tkinter reste similaire,
# mais sans les références spécifiques à wxPython comme wx.LIST_FORMAT_LEFT.
class Column:
    """
    Définit les propriétés d'une colonne pour le ttk.Treeview.
    """
    def __init__(self, name, header, *eventTypes, width=100, **kwargs):
        self._name = name
        self._header = header
        self.width = width
        self.__eventTypes = eventTypes
        self.__sortCallback = kwargs.pop("sortCallback", None)
        self.__renderCallback = kwargs.pop(
            "renderCallback", self.defaultRenderer
        )
        self.__hasImages = "imageIndicesCallback" in kwargs
        self.__imageIndicesCallback = (
                kwargs.pop("imageIndicesCallback", self.defaultImageIndices)
                or self.defaultImageIndices
        )

    def name(self):
        """Retourne le nom interne de la colonne."""
        log.debug(f"name() renvoie {self._name}")
        return self._name

    def header(self):
        """Retourne le texte de l'en-tête de la colonne."""
        return self._header

    def eventTypes(self):
        return self.__eventTypes

    def setWidth(self, width):
        """Définit la largeur de la colonne."""
        self.width = width

    def defaultRenderer(self, *args, **kwargs):  # pylint: disable=W0613
        return str(args[0])

    def is_shown(self):
        # Par défaut, une colonne est affichée.
        return True

    def add_is_shown_to_column(self):
        if not hasattr(Column, 'is_shown'):
            Column.is_shown = self.is_shown()

    def defaultImageIndices(self, *args, **kwargs):  # pylint: disable=W0613
        # return {wx.TreeItemIcon_Normal: -1}
        return {}

    def imageIndices(self, *args, **kwargs):
        return self.__imageIndicesCallback(**kwargs)

    def hasImages(self):
        return self.__hasImages

# Description : Classe de base pour les contrôles avec des colonnes.
# Elle gère l'insertion et la suppression des colonnes .
# Version Tkinter : La version Tkinter adapte la logique d'insertion
# et de suppression des colonnes au ttk.Treeview.
# Explication des changements :
#
#     Nous utilisons maintenant self['displaycolumns'] pour contrôler la visibilité, ce qui est l'option correcte pour un ttk.Treeview existant.
#
#     La méthode _set_columns configure toujours les heading et column pour toutes les colonnes (self.__allColumns) lors de l'initialisation du mixin, mais elle ne modifie plus la définition (columns), seulement la visibilité (displaycolumns).
#
#     La méthode showColumn met simplement à jour la liste __visible_columns et réassigne self['displaycolumns'].
class _BaseCtrlWithColumnsMixin:
    """Une classe de base pour tous les contrôles avec des colonnes.

    Notez que cette classe et ses sous-classes ne prennent pas en charge
    l'ajout ou la suppression de colonnes après le paramètre initial des colonnes.
    """
    def __init__(self, *args, **kwargs):
        log.debug("_BaseCtrlWithColumnsMixin.__init__ : initialisation de tous les contrôles avec des colonnes.")
        # Extrait et stocke les colonnes
        # 'columns' est nécessaire pour _set_columns,
        # mais il a déjà été "popped" par CtrlWithColumnsMixin (ligne 587)
        # Assurons-nous que l'argument est bien 'columns'
        # self.__allColumns = kwargs.pop("columns")
        # Utilise .pop() avec une valeur par défaut (None).
        # Si 'columns' n'est pas là (parce que _CtrlWithHideableColumnsMixin l'a pris),
        # self.__allColumns sera None, et nous ne ferons rien.
        self.__allColumns = kwargs.pop("columns", None)
        # # super().__init__(*args, **kwargs)
        # # Nous devons nous assurer que tous les mixins dans la chaîne d'héritage
        # # de CtrlWithColumnsMixin appellent super().__init__()
        # # sans arguments supplémentaires s'ils n'héritent pas d'un widget.
        # super().__init__()  # <-- PROBLÈME
        # NE PAS appeler super().__init__()
        self.__indexMap = []
        # CORRECTION 2 : Ne tente de configurer les colonnes que si elles ont été fournies
        # à ce mixin (ce qui n'est pas le cas si HideableMixin est actif).
        if self.__allColumns is not None:
            self._set_columns()
        log.debug("_BaseCtrlWithColumnsMixin initialisé !")

    def _set_columns(self):
        """Configure les colonnes initiales."""
        for column in self.__allColumns:
            self.heading(column.name(), text=column.header())
            self.column(column.name(), width=column.width, minwidth=20)

    def _allColumns(self):
        """Retourne toutes les colonnes."""
        return self.__allColumns


class _CtrlWithHideableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """
    Gère le masquage et l'affichage des colonnes pour un Treeview Tkinter.

    Gère l'affichage et le masquage des colonnes.
    """
    # Utiliser displaycolumns
    #
    # Le mixin _CtrlWithHideableColumnsMixin ne devrait pas toucher à la définition des colonnes (columns).
    # Son rôle est de contrôler quelles colonnes, parmi celles qui sont définies, sont visibles.
    # C'est précisément ce que fait l'option displaycolumns du ttk.Treeview.
    def __init__(self, *args, **kwargs):
        # Extrait les colonnes AVANT d'appeler super()
        # self.__allColumns = kwargs.pop("columns")
        columns = kwargs.pop("columns")
        super().__init__(*args, **kwargs)
        # AJOUTER CETTE LIGNE : Stocke la liste complète des colonnes
        self.__allColumns = columns  # <--- CORRECTION AJOUTÉE
        # # self.__visible_columns = [col.name() for col in self.__allColumns]
        # self.__visible_columns = [col.name() for col in columns]
        self.__visible_columns = [col.name() for col in self.__allColumns if col.is_shown()] if self.__allColumns else None  # Utilise __allColumns ici
        # self._set_columns()  # Appelle la méthode corrigée qui utilise displaycolumns

    def _set_columns(self):
        # VERSION ACTUELLE (cause le crash)
        # self['columns'] = self.__visible_columns

        # VERSION CORRIGÉE : Manipule les colonnes visibles
        self['displaycolumns'] = self.__visible_columns
        # Le reste de la méthode (configuration heading/column) est correct,
        # car il configure les propriétés des colonnes déjà définies.
        for col in self.__allColumns:  # Utilise __allColumns pour configurer TOUTES les colonnes
            self.heading(col.name(), text=col.header())
            self.column(col.name(), width=col.width, minwidth=20)

    def showColumn(self, column_name, show=True):
        if show and column_name not in self.__visible_columns:
            self.__visible_columns.append(column_name)
            # Correction: Trie en fonction de l'ordre dans __allColumns
            self.__visible_columns.sort(key=lambda x: [c.name() for c in self.__allColumns].index(x))
        elif not show and column_name in self.__visible_columns:
            self.__visible_columns.remove(column_name)

        # VERSION ACTUELLE (incorrecte)
        # self['columns'] = self.__visible_columns
        # VERSION CORRIGÉE : Met à jour les colonnes visibles
        self['displaycolumns'] = self.__visible_columns
        # Pas besoin d'appeler _set_columns() ici, car les colonnes sont déjà définies.
        # On change juste leur visibilité.
        # self._set_columns() # <--- SUPPRIME CET APPEL


# Implémenter showSortColumn dans itemctrltk.py
#
# Maintenant que self.widget est un TreeListCtrl, nous devons
# donner à ce TreeListCtrl (via son mixin _CtrlWithSortableColumnsMixin)
# les méthodes que basetk.py attend.
class _CtrlWithSortableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """
    Ajoute le tri des colonnes en cliquant sur l'en-tête.
    """
    def __init__(self, *args, **kwargs):
        # --- MODIFICATION : Appel explicite au __init__ du parent direct ---
        # super().__init__(*args, **kwargs) # Remplacé par l'appel ci-dessous
        _BaseCtrlWithColumnsMixin.__init__(self, *args, **kwargs)
        # --- Fin MODIFICATION ---
        self.sort_column = None
        self.sort_reverse = False

        # --- NOUVEAU : Charger les icônes de tri ---
        # # (Données brutes pour de petites flèches)
        # self._sort_arrow_up = PhotoImage(data=b'R0lGODlhEAAQAPMAAP///wAAAAAA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAAQAQzEALEhEAJkiRFsoHx+Fzx+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gy1AAA7')
        # self._sort_arrow_down = PhotoImage(data=b'R0lGODlhEAAQAPMAAP///wAAAAAA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAAQAQzEMhAhAAVkiRFsoHx+Fzx+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gy1AAA7')
        # --- Fin NOUVEAU ---
        # --- MODIFIÉ : Charger les icônes depuis artprovidertk ---
        try:
            # Demander les icônes de taille 16x16 via art_provider_tk
            # Note: artprovidertk.getIcon s'attend au nom de base (sans la taille)
            self._sort_arrow_up = artprovidertk.getIcon('arrow_up_icon', desired_size=(16, 16))
            self._sort_arrow_down = artprovidertk.getIcon('arrow_down_icon', desired_size=(16, 16))

            # Vérifier si les icônes ont été chargées (getIcon retourne None si échec)
            if self._sort_arrow_up is None:
                log.error("Erreur: Impossible de charger 'arrow_up_icon16x16' depuis artprovidertk.")
                self._sort_arrow_up = PhotoImage() # Fallback : image vide pour éviter crash
            if self._sort_arrow_down is None:
                log.error("Erreur: Impossible de charger 'arrow_down_icon16x16' depuis artprovidertk.")
                self._sort_arrow_down = PhotoImage() # Fallback : image vide

        except Exception as e:
            # Gestion d'autres erreurs potentielles (bien que getIcon devrait gérer None)
            log.exception(f"Erreur inattendue lors du chargement des icônes de tri via artprovidertk: {e}")
            self._sort_arrow_up = PhotoImage()
            self._sort_arrow_down = PhotoImage()
        # --- Fin MODIFIÉ ---

        # CORRECTION ICI: Utiliser col.name() et appeler sort_by avec le nom de la colonne
        # Les liaisons 'command' sont gérées par TreeListCtrl/VirtualListCtrl
        # (Les lignes liant self.heading(...) ici doivent être supprimées si elles existent)
        # self.heading("#0", command=lambda: self.sort_by("#0"))
        # Correction : Ne pas utiliser self["columns"] car il n'est pas encore stable
        # et n'est pas censé configurer les en-têtes ici, car c'est la responsabilité
        # de la classe concrète (VirtualListCtrl).

        # RETIRER LA CONFIGURATION DES EN-TÊTES DANS CE MIXIN
        # La configuration complète des en-têtes est faite dans VirtualListCtrl.__init__ (lignes 278-282).

        # Retirez les lignes suivantes dans _CtrlWithSortableColumnsMixin.__init__:
        # for col in self["columns"]:  # <--- ATTENTION : self["columns"] retourne la liste des noms
        #     self.heading(col, command=lambda c=col: self.sort_by(c))  # <--- L'initialisation se fait ici
        # Le code wx original utilisait self["columns"] qui sont des chaînes.
        # Si vous aviez une boucle séparée pour initialiser l'en-tête qui accédait aux objets colonne,
        # la correction doit être appliquée là.

    def sort_by(self, col_name):
        """Trie les éléments du Treeview par colonne (logique ET UI)."""
        # data = [(self.set(item, col_name), item) for item in self.get_children('')]

        # 1. Retirer l'ancienne flèche (si la colonne change)
        if self.sort_column and self.sort_column != col_name:
            self.heading(self.sort_column, image='')

        # 2. Mettre à jour le statut de tri
        if col_name == self.sort_column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col_name
            self.sort_reverse = False

        # data.sort(reverse=self.sort_reverse)
        # 3. Définir la nouvelle flèche
        img = self._sort_arrow_down if self.sort_reverse else self._sort_arrow_up
        # Assigner l'image à l'en-tête de colonne
        self.heading(col_name, image=img)

        # 4. Exécuter le tri (logique de données)
        data = [(self.set(item, col_name), item) for item in self.get_children('')]
        data.sort(reverse=self.sort_reverse)
        for index, (val, item) in enumerate(data):
            self.move(item, '', index)

    # # def showSortColumn(self, column):
    # #     if column != self.__currentSortColumn:
    # #         self._clearSortImage()
    # #     self.__currentSortColumn = column
    # #     self._showSortImage()
    # def showSortColumn(self, column):
    #     self.sort_by(column)

    # (REMPLACER l'ancienne méthode showSortColumn (ligne 558))
    def showSortColumn(self, column=None):
        """(UI) Affiche l'indicateur de tri sur la colonne actuelle."""
        # 'column' peut être un objet Column (de basetk) ou None (de sortBy)

        # 1. Déterminer le nom de la colonne
        col_name = None
        if column:  # Appelé par basetk.initColumn
            col_name = column.name()
            self.sort_column = col_name  # Mémoriser
        elif self.sort_column:  # Appelé par basetk.sortBy
            col_name = self.sort_column

        if not col_name:
            return  # Pas de colonne à trier

        # 2. Nettoyer les autres colonnes
        for col_id in self["columns"]:
            if col_id != col_name:
                self.heading(col_id, image='')

        # 3. Définir la flèche actuelle
        img = self._sort_arrow_down if self.sort_reverse else self._sort_arrow_up
        self.heading(col_name, image=img)

    # (NOUVELLE MÉTHODE : pour corriger la prochaine erreur)
    def showSortOrder(self, imageIndex=None):
        """(UI) Met à jour l'image de la flèche de tri (appelé par basetk)."""
        # imageIndex n'est pas pertinent pour Tkinter, on utilise self.sort_reverse
        if self.sort_column:
            img = self._sort_arrow_down if self.sort_reverse else self._sort_arrow_up
            self.heading(self.sort_column, image=img)


# Description : Ce mixin gère le redimensionnement automatique des colonnes.
# Version Tkinter : La version Tkinter utilise une approche basée sur
# l'événement <Configure> pour ajuster la largeur de la colonne redimensionnable.
# Il n'y a plus d'héritage de autowidth.AutoColumnWidthMixin, car cette classe
# a été modifiée pour Tkinter.
class _CtrlWithAutoResizedColumnsMixin(autowidthtk.AutoColumnWidthMixin):
    """Gère le redimensionnement automatique des colonnes.

    Classe de contrôle avec redimensionnement automatique des colonnes.
    Utilise autowidthtk.py pour cette fonctionnalité.
    """
    # def __init__(self, *args, **kwargs):
    def __init__(self, master, *args, **kwargs):
        log.debug("_CtrlWithAutoResizedColumnsMixin.__init__ : initialisation.")
        # super().__init__(*args, **kwargs)
        super().__init__(master, *args, **kwargs)
        self.bind('<Configure>', self.on_resize)  # <-- Bind event to the Treeview
        self.resize_column = None  # Laissez la classe dérivée définir quelle colonne redimensionner
        log.debug("_CtrlWithAutoResizedColumnsMixin initialisé !")

    def on_resize(self, event):
        """Ajuste la largeur de la colonne spécifiée en fonction de l'espace disponible."""
        if self.winfo_width() > 1:
            total_width = self.winfo_width()
            fixed_width = 0
            # Calculer la largeur totale des colonnes à largeur fixe
            for col in self['columns']:
                if col != self.resize_column:
                    fixed_width += self.column(col)['width']

                    # Définir la largeur de la colonne redimensionnable
            resize_width = total_width - fixed_width
            if resize_width > 50:
                self.column(self.resize_column, width=resize_width)


class CtrlWithColumnsMixin(_CtrlWithAutoResizedColumnsMixin,
                           _CtrlWithHideableColumnsMixin,
                           _CtrlWithSortableColumnsMixin,
                           _CtrlWithColumnPopupMenuMixin):
    """
    Combinaison des mixins pour la gestion des colonnes.

    Combine les mixins pour la gestion des colonnes.
    """
    # def __init__(self, *args, **kwargs):
    def __init__(self, master, *args, **kwargs):
        # super().__init__(*args, **kwargs)
        # Filtrer les arguments spécifiques aux mixins avant de les passer à super()
        # Cela empêche que ces arguments arrivent jusqu'à ttk.Treeview

        # Extraire et traiter les arguments des mixins
        # 1. Consommer les arguments spécifiques aux colonnes
        columns = kwargs.pop("columns", [])
        columnPopupMenu = kwargs.pop("columnPopupMenu", None)

        # 2. CORRECTION : Consommer les arguments spécifiques aux items (pour éviter la propagation à Tkinter via cette chaîne)
        kwargs.pop("selectCommand", None)
        kwargs.pop("editCommand", None)

        # 3. Propagation des arguments restants (master, *args, **kwargs nettoyés)
        # # Passer les arguments filtrés à la chaîne d'héritage
        # # super().__init__(columns=columns, columnPopupMenu=columnPopupMenu, *args, **kwargs)
        # super().__init__(master, columns=columns, columnPopupMenu=columnPopupMenu, *args, **kwargs)  # <-- PROBLÈME
        # Appels explicites au lieu de super()
        _CtrlWithAutoResizedColumnsMixin.__init__(self, master, *args, **kwargs)
        _CtrlWithHideableColumnsMixin.__init__(self, master, columns=columns, *args, **kwargs)
        _CtrlWithSortableColumnsMixin.__init__(self, master, columns=columns, *args, **kwargs)
        _CtrlWithColumnPopupMenuMixin.__init__(self, master, columnPopupMenu=columnPopupMenu, *args, **kwargs)

# --- Classes principales combinées pour le Treeview ---
# TaskList est normalement dans domain.task.tasklist
# class TaskList(CtrlWithItemsMixin, CtrlWithColumnsMixin, ttk.Treeview):
class TaskTree(CtrlWithItemsMixin, CtrlWithColumnsMixin, ttk.Treeview):
    """
    Le Treeview principal de l'application, combinant toutes les fonctionnalités.

    La classe principale qui combine tous les mixins et hérite de ttk.Treeview.
    """
    def __init__(self, master, **kwargs):
        # Récupère les colonnes si elles sont passées
        # Extraire les colonnes et autres arguments spécifiques
        columns = kwargs.pop("columns", [])
        itemPopupMenu = kwargs.pop("itemPopupMenu", None)
        columnPopupMenu = kwargs.pop("columnPopupMenu", None)

        # super().__init__(master, columns=columns, **kwargs)
        # Initialiser ttk.Treeview avec seulement les arguments qu'il comprend
        ttk.Treeview.__init__(self, master, columns=[c.name() for c in columns], show='headings', **kwargs)

        # Initialiser les mixins avec leurs arguments spécifiques
        # CtrlWithItemsMixin.__init__(self, itemPopupMenu=itemPopupMenu)
        CtrlWithItemsMixin.__init__(self, master, itemPopupMenu=itemPopupMenu)
        # CtrlWithColumnsMixin.__init__(self, columns=columns, columnPopupMenu=columnPopupMenu)
        CtrlWithColumnsMixin.__init__(self, master, columns=columns, columnPopupMenu=columnPopupMenu)

        # Liez la colonne redimensionnable à l'événement de configuration
        self.bind('<Configure>', self.on_resize)
        self.resize_column = 'task_name'  # Définissez la colonne à redimensionner
        # self.bind("<Motion>", self.on_motion_update_tooltip)
        self.pack(fill=tk.BOTH, expand=True)

    def on_resize(self, event):
        """Ajuste la largeur de la colonne spécifiée en fonction de l'espace disponible."""
        if self.winfo_width() > 1:
            total_width = self.winfo_width()
            fixed_width = 0

            # Calculer la largeur totale des colonnes à largeur fixe
            for col in self['columns']:
                if col != self.resize_column:
                    fixed_width += self.column(col)['width']

            # Définir la largeur de la colonne redimensionnable
            resize_width = total_width - fixed_width
            if resize_width > 50:
                self.column(self.resize_column, width=resize_width)

    def getItemTooltipData(self, item_data):
        """
        Retourne le texte de l'info-bulle pour un élément.


        Cette méthode est utilisée par la classe CtrlWithToolTipMixin
        de itemctrltk.py pour obtenir le texte de l'info-bulle.
        Vous devez l'implémenter dans votre classe dérivée (par exemple,
        TaskList) pour retourner la chaîne d'info-bulle appropriée.

        Args:
            item_data:

        Returns:

        """
        # Implémentez la logique pour retourner la chaîne de l'info-bulle
        return f"Détails de l'élément : {item_data}"
        # Remplacez cette implémentation par une logique qui récupère
        # les informations pertinentes de l'objet de données associé
        # à l'élément et les formate en une chaîne à afficher dans l'info-bulle.

    def OnDrop(self, drop_item, dragged_items, part):
        """
        Gère le drop d'éléments.

        Cette méthode doit être surchargée dans la classe dérivée
        (TaskList ou une autre classe) qui utilise le mixin TreeCtrlDragAndDropMixin
        de draganddroptk.py. Elle définit ce qui se passe lorsqu'un élément est déposé.

        Args:
            drop_item:
            dragged_items:
            part:

        Returns:

        """
        print(f"Éléments glissés: {dragged_items} sur {drop_item} à la position: {part}")
        # Exemple de déplacement simple
        for item in dragged_items:
            if part == "on":
                # Déplacer l'élément pour qu'il devienne un enfant
                self.move(item, drop_item, "end")
            else:
                # Déplacer l'élément au-dessus ou en-dessous
                index = self.index(drop_item)
                if part == "below":
                    index += 1
                self.move(item, self.parent(drop_item), index)


# --- Exemple d'utilisation ---

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Exemple de TaskList (Tkinter)")

    # # Définition des colonnes comme dans l'original
    # class Column:
    #     def __init__(self, name, header, width=100):
    #         self._name = name
    #         self._header = header
    #         self.width = width
    #     def name(self): return self._name
    #     def header(self): return self._header

    # Définition des colonnes
    columns = [
        Column('task_name', 'Tâche', width=200),
        Column('due_date', 'Date d’échéance', width=120),
        Column('priority', 'Priorité', width=80),
    ]

    # Crée un menu contextuel de test
    item_menu = Menu(root, tearoff=0)
    item_menu.add_command(label="Modifier")
    item_menu.add_command(label="Supprimer")

    # Crée l'instance de la TaskList
    # task_list = TaskList(root, columns=columns, itemPopupMenu=item_menu, show="headings")
    task_list = TaskTree(root, columns=columns, itemPopupMenu=item_menu)

    # Définir la colonne redimensionnable
    task_list.resize_column = 'task_name'

    # Insérer des données de test
    task_list.insert('', 'end', values=('Convertir itemctrl.py', '2025-09-01', 'Haute'), tags=('task_1',))
    task_list.insert('', 'end', values=('Réécrire la doc', '2025-09-15', 'Moyenne'), tags=('task_2',))

    root.mainloop()
