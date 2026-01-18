# Malheureusement, je ne peux pas directement modifier un fichier
# ni accéder à votre environnement de développement local.
# Cependant, je peux vous fournir une conversion du code pour un module
# draganddrop.py compatible avec Tkinter en utilisant le module tkinter.dnd.
#
# La conversion est complexe car le système de glisser-déposer de wxPython est
# fondamentalement différent de celui de Tkinter.
# wxPython utilise des classes spécifiques comme
# wx.FileDropTarget et wx.TextDropTarget,
# tandis que Tkinter utilise un ensemble
# de fonctions et de rappels (callbacks) avec le module tkinter.dnd.
#
# Je vais convertir les fonctionnalités de glisser-déposer de fichiers et de
# texte, ainsi que la logique de glisser-déposer d'éléments dans un Treeview,
# ce qui est l'équivalent de TreeCtrlDragAndDropMixin.

# Points clés de la conversion
#
#     Changement d'API: La principale différence est que Tkinter utilise des
#     méthodes et des événements pour gérer le glisser-déposer,
#     alors que wxPython utilise une approche orientée objet avec des classes
#     spécifiques (wx.FileDropTarget).
#
#     Remplacer wx.FileDropTarget et wx.TextDropTarget: J'ai créé la classe
#     FileTextDropTarget qui utilise les fonctions dnd.dnd_register pour
#     lier le widget cible à des types de données spécifiques (text/plain et DND_Files).
#
#     Conversion de TreeCtrlDragAndDropMixin:
#
#         Événements: Les événements wx.EVT_TREE_BEGIN_DRAG et wx.EVT_TREE_END_DRAG
#         sont remplacés par des événements de la souris Tkinter (<ButtonPress-1>,
#         <B1-Motion>, <ButtonRelease-1>).
#
#         Logiciel de glisser-déposer: Au lieu de la logique interne de wx.TreeCtrl,
#         nous utilisons tkinter.dnd. La méthode on_start_drag initie le glisser-déposer
#         en appelant dnd.dnd_start(self, event).
#
#         HitTest: La logique de HitTest pour déterminer la position de la souris
#         est remplacée par self.identify_row(event.y) et
#         le calcul de la hauteur de la ligne (self.bbox).
#
#         Données: Dans wxPython, les données sont gérées par les DataObjects.
#         Dans Tkinter, pour le glisser-déposer interne au Treeview,
#         les informations sur les éléments glissés sont stockées directement
#         dans l'instance de la classe (self.dragged_items).
#
# Ce code vous fournit un équivalent fonctionnel pour la migration.
# Il est important de noter que vous devrez l'adapter à la logique interne de
# votre application TaskCoach, notamment pour gérer les données associées
# à chaque tâche (self.GetItemPyData utilise les tags de l'élément Treeview
# comme une solution de substitution).

# Les erreurs que vous rencontrez sont dues à des incompatibilités entre le code
# que j'ai fourni et le comportement attendu par le module tkinter.dnd.
# Le module dnd de Tkinter est assez basique et nécessite que la source
# (l'objet qui est glissé) et la cible (l'objet sur lequel on lâche)
# implémentent des méthodes spécifiques.
#
# Voici les corrections à apporter au fichier draganddroptk.py pour résoudre ces problèmes.
#
# 1. AttributeError: 'TaskCoachTree' object has no attribute 'dnd_enter' et dnd_end
#
# Ces erreurs se produisent car le module tkinter.dnd appelle des méthodes
# sur l'objet qui a initié le glisser-déposer. Il s'attend à trouver
# les méthodes dnd_enter, dnd_leave, et dnd_end sur l'objet source.
#
# Pour corriger cela, il faut que la classe TreeCtrlDragAndDropMixin implémente ces méthodes.
#
# 2. _tkinter.TclError: bad cursor spec "no"
#
# Cette erreur survient parce que la chaîne "no" n'est pas un nom de curseur
# valide pour Tkinter. Il faut utiliser l'une des chaînes de curseur prédéfinies, comme "no_drop".

# Résumé des modifications
#
#     Ajout des méthodes dnd_enter_callback, dnd_leave_callback et dnd_end_callback:
#     Ces méthodes ont été ajoutées à la classe TreeCtrlDragAndDropMixin.
#
#     Liaison des méthodes aux événements dnd: Dans la méthode __init__,
#     les attributs dnd_enter, dnd_leave et dnd_end de la classe sont maintenant
#     liés à ces nouvelles méthodes de rappel.
#     Le module tkinter.dnd pourra ainsi les trouver et les appeler.
#
#     Correction du nom du curseur: Le nom "no" a été remplacé par "no_drop",
#     qui est un nom de curseur valide dans Tkinter.
#
# Ces modifications devraient résoudre les AttributeError et le TclError
# que vous avez rencontrés, et permettre au glisser-déposer de fonctionner comme prévu.

# Le module tkinter.dnd n'a pas d'équivalent direct à la classe wx.DataObjectComposite,
# ce qui rend la gestion de multiples types de données (fichiers, URLs, emails, etc.)
# sur une seule cible de dépôt beaucoup plus difficile.
# Les fonctionnalités de gestion des emails (Thunderbird, Outlook, etc.)
# reposent sur des intégrations spécifiques à chaque système d'exploitation,
# que Tkinter ne prend pas en charge de manière native.
#
# Cependant, je peux vous fournir une classe FileUrlDropTarget qui remplace
# la fonctionnalité principale de votre classe DropTarget en gérant à la fois
# les fichiers et les URLs/texte. Cette solution est compatible avec l'approche
# de Tkinter et utilise les rappels (callbacks) pour imiter le comportement de la classe d'origine.
#
# Voici la nouvelle classe FileUrlDropTarget et un exemple d'utilisation.
# Vous pouvez l'ajouter à votre fichier draganddrop.py en complément du code précédent.

# Explication des changements
#
#     Remplacement de la classe wx.DropTarget : J'ai créé la classe FileUrlDropTarget
#     qui prend en paramètre le widget sur lequel vous souhaitez activer le glisser-déposer.
#     Elle accepte deux rappels distincts pour les URLs (on_drop_url_callback)
#     et les fichiers (on_drop_file_callback), comme dans votre code d'origine.
#
#     Utilisation de tkinter.dnd : Nous utilisons dnd.dnd_register pour indiquer
#     à Tkinter que le widget peut accepter des données de type "text/plain"
#     (pour les URLs et le texte) et "DND_Files" (pour les fichiers).
#
#     Séparation des callbacks : La méthode dnd_commit est le point central
#     de la logique. Elle vérifie le type de données lâchées
#     (via source.drag_data pour le texte ou source.filenames pour les fichiers)
#     et appelle le bon rappel, imitant ainsi le comportement de votre méthode OnData d'origine.
#
#     Gestion des URLs : Le code vérifie si le texte lâché correspond à une URL
#     en utilisant une expression régulière simple. Si c'est le cas,
#     il appelle le rappel d'URL ; sinon, il le traite comme du texte simple.
#     La fonction urllib.parse.unquote est utilisée pour décoder les chemins
#     de fichiers qui pourraient être encodés.

# Principaux changements et explications :
#
# Importation des modules Tkinter
#
# Importation des modules nécessaires de Tkinter : tkinter as tk, tkinter.dnd, tkinter.ttk.
#
#
# Classes de glisser-déposer génériques
#
# FileTextDropTarget et FileUrlDropTarget : Ces classes gèrent le dépôt de
# fichiers et de texte/URLs. Elles utilisent dnd.dnd_register pour
# lier le widget cible à des types de données spécifiques (text/plain et DND_Files).
# Les méthodes dnd_enter, dnd_leave, et dnd_commit sont utilisées pour
# gérer les événements de glisser-déposer.
#
#
# Mixin pour le glisser-déposer d'arborescence
#
# TreeHelperMixin : Fournit des méthodes utilitaires pour un Treeview,
# comme GetItemChildren, GetItemParent, et GetItemPyData.
# TreeCtrlDragAndDropMixin : Un mixin pour permettre le glisser-déposer
# d'éléments dans un Treeview Tkinter. Les événements wx.EVT_TREE_BEGIN_DRAG
# et wx.EVT_TREE_END_DRAG sont remplacés par des événements de la souris
# Tkinter (<ButtonPress-1>, <B1-Motion>, <ButtonRelease-1>).
#
#
# Gestion des événements
#
# Les événements de début, de mouvement et de fin de glissement sont gérés
# par les méthodes on_start_drag, on_dragging, et on_end_drag.
#
#
# Méthodes requises par tkinter.dnd
#
# Les méthodes dnd_enter_callback, dnd_leave_callback, et dnd_end_callback
# sont ajoutées pour répondre aux exigences du module tkinter.dnd.
#
#
# Exemple d'utilisation
#
# Un exemple d'utilisation est fourni pour démontrer comment utiliser
# les classes et mixins. Il crée une classe TaskCoachTree qui hérite
# de TreeCtrlDragAndDropMixin et ttk.Treeview.
#
#
#
# Points importants :
#
# Limitations du module tkinter.dnd : Le module tkinter.dnd est assez basique
#                           et nécessite que la source (l'objet qui est glissé)
#                           et la cible (l'objet sur lequel on lâche) implémentent
#                           des méthodes spécifiques.
# Gestion des données : Dans wxPython, les données sont gérées par les DataObjects.
#                   Dans Tkinter, pour le glisser-déposer interne au Treeview,
#                   les informations sur les éléments glissés sont stockées
#                   directement dans l'instance de la classe (self.dragged_items).
# Gestion des emails : Les fonctionnalités de gestion des emails
#           (Thunderbird, Outlook, etc.) reposent sur des intégrations spécifiques
#           à chaque système d'exploitation, que Tkinter ne prend pas en charge de manière native.

# Principales modifications et améliorations :
#
# Modularité accrue :
#
# Les gestionnaires de drop sont maintenant divisés en classes spécifiques
# pour chaque type de données (fichiers, URLs, texte).
# Cela rend le code plus propre et plus facile à maintenir.
#
#
# Classe de base TkinterDropTarget :
#
# Une classe de base TkinterDropTarget est introduite pour gérer
# l'enregistrement des types de données et fournir des méthodes
# par défaut pour les événements de drop.
#
#
# Gestion composite des types de données :
#
# La classe CompositeDropTarget permet de gérer plusieurs types de drops
# sur un même widget, simplifiant ainsi l'intégration.
#
#
# Logging :
#
# Ajout de logging pour faciliter le débogage et la compréhension du flux d'exécution.
#
#
# Méthodes requises par tkinter.dnd :
#
# Les méthodes dnd_enter_callback, dnd_leave_callback, et dnd_end_callback
# sont implémentées dans le TreeCtrlDragAndDropMixin.
#
#
# Adaptation des classes wxPython existantes
#
#
# Les classes FileDropTarget, TextDropTarget, DropTarget, TreeHelperMixin et
# TreeCtrlDragAndDropMixin ont été adaptées.
#
# Explications détaillées :
#
# Classes de DropTarget spécifiques :
#
# FileDropTarget, TextDropTarget, et URLDropTarget gèrent chacun un type de
# données spécifique. Ils héritent de TkinterDropTarget et implémentent
# la méthode dnd_commit pour traiter les données dropées.
#
#
# Classe CompositeDropTarget :
#
# Cette classe permet de gérer plusieurs types de drops sur un même widget.
# Elle prend en paramètre des callbacks pour chaque type de données et
# appelle le callback approprié dans la méthode dnd_commit.
#
#
# Exemple d'utilisation :
#
# L'exemple d'utilisation montre comment utiliser les classes CompositeDropTarget
# et TreeCtrlDragAndDropMixin pour gérer les drops sur un Label et un Treeview.
#
#
#
# Points importants :
#
# Modularité :
#
# La modularité accrue facilite l'ajout de nouveaux types de données à gérer.
# Il suffit de créer une nouvelle classe héritant de TkinterDropTarget et
# de l'enregistrer dans un CompositeDropTarget.
#
#
# Gestion des erreurs :
#
# Le logging permet de suivre le flux d'exécution et de détecter les erreurs plus facilement.

# Tu as raison, dnd.dnd_register() n'est pas directement une fonction du module
# tkinter.dnd standard. Il semble que ce soit une fonction attendue dans certains
# exemples ou implémentations personnalisées de drag-and-drop avec Tkinter,
# possiblement en combinaison avec une extension Tcl comme tkdnd.
# Après vérification des sources fournies, voici une analyse pour clarifier
# comment aborder le drag-and-drop dans Tkinter, et
# comment interpréter l'utilisation de dnd_register():
# 1. Drag and Drop dans Tkinter Standard (tkinter.dnd)
#
# Le module tkinter.dnd fournit un support de base pour le drag-and-drop
# entre objets au sein d'une même application, que ce soit dans la même fenêtre
# ou entre fenêtres .
# Pour rendre un objet déplaçable, il faut créer une liaison d'événement
# qui initie le processus de drag-and-drop. Typiquement, un événement ButtonPress
# est lié pour commencer le drag .
# Le module tkinter.dnd est assez basique et nécessite souvent une
# implémentation manuelle des aspects de gestion des données et de feedback visuel.
#
# 2. Utilisation de tkdnd (TkinterDnD)
#
# tkdnd est une extension Tcl qui fournit une interface aux mécanismes de
# drag-and-drop natifs spécifiques à chaque plateforme.
# tkinterDnD est un wrapper Python qui facilite l'utilisation de tkdnd sans
# nécessiter d'installation complexe de Tcl ni de compilation.
# Il offre une API plus conviviale.
# L'utilisation de tkdnd permet de gérer plus facilement le drag-and-drop avec des applications externes (par exemple, faire glisser des fichiers depuis l'explorateur de fichiers).
#
# 3. Implémentations alternatives et personnalisées
#
# Certaines ressources montrent comment implémenter un drag-and-drop sans modules externes, en utilisant directement les événements Tkinter et la manipulation des widgets . Cela peut être utile pour des besoins simples, mais devient vite complexe pour des fonctionnalités avancées.
# Dans ce contexte, dnd_register pourrait être une fonction définie par l'utilisateur pour simplifier l'enregistrement des événements et des callbacks nécessaires pour gérer le drag-and-drop.
#
# En résumé :
#
# Si tu veux rester avec le module standard tkinter.dnd, tu devras implémenter manuellement la logique de gestion des événements, des données et du feedback visuel.
# Si tu as besoin de fonctionnalités plus avancées (drag-and-drop avec des applications externes, gestion de différents types de données), l'utilisation de tkdnd via le wrapper tkinterDnD est une option intéressante.  Il faudra installer le paquet tkinterdnd2 (et non tkinterdnd qui lui n'existe pas et qui prête à confusion !)
# La fonction dnd_register que tu recherches fait probablement partie d'une implémentation personnalisée ou d'un exemple utilisant tkdnd.
#
# Recommandations :
#
# Pour un projet simple (drag-and-drop interne à l'application) : Implémente le drag-and-drop en utilisant directement les événements Tkinter (ButtonPress, Motion, ButtonRelease) et la manipulation des widgets.
# Pour un projet plus complexe (drag-and-drop avec des applications externes, différents types de données) : Utilise tkinterdnd2 pour simplifier l'intégration de tkdnd. Voici un exemple d'installation : pip install tkinterdnd2
# Si tu rencontres du code utilisant dnd_register : Vérifie si ce code est associé à une implémentation de tkdnd ou s'il s'agit d'une fonction définie localement dans le projet.

# En Tkinter, le glisser-déposer peut être implémenté
# en utilisant des bindings d'événements (<ButtonPress>, <B1-Motion>, <ButtonRelease>)
# et des widgets comme Listbox, Canvas, ou Treeview.
# Exemple de conversion pour les éléments :
# Les listes d'éléments peuvent être gérées avec des widgets comme Listbox ou Treeview de Tkinter.

import tkinter as tk
from tkinter import ttk
from tkinter import dnd
import re
import urllib.parse
import logging

log = logging.getLogger(__name__)


# # Note : Les fonctionnalités de glisser-déposer de messages électroniques
# # de Thunderbird, Outlook et Mail.app ne peuvent pas être directement
# # converties en Tkinter sans des modules externes complexes et spécifiques à la plateforme.
# # Cette conversion se concentre sur les fichiers et les URLs/texte.

# --- Classe pour initier une opération de glisser-déposer (source) ---
class DragSource:
    """
    Une classe simple pour initier une opération de glisser-déposer.
    L'objet de données est stocké dans l'attribut `drag_data`.
    """
    def __init__(self, widget, drag_data):
        self.widget = widget
        self.drag_data = drag_data
        self.widget.bind("<ButtonPress-1>", self.on_start_drag)

    def on_start_drag(self, event):
        dnd.dnd_start(self, event)
        self.widget.config(cursor="hand1")


# # --- Classes de base ---
# class TkinterDropTarget:
#     """
#     Classe de base pour gérer les opérations de drop dans Tkinter.
#     """
#     def __init__(self, widget, accepted_types=None):
#         self.widget = widget
#         self.accepted_types = accepted_types or []
#         self.dnd_register()
#
#     def dnd_register(self):
#         """Enregistre les types de données acceptés par le widget."""
#         for type in self.accepted_types:
#             dnd.dnd_register(self.widget, type, self.dnd_accept)
#
#     def dnd_accept(self, source, event):
#         """Méthode appelée pour accepter un drop. Doit être surchargée."""
#         return self
#
#     def dnd_enter(self, source, event):
#         """Méthode appelée quand la souris entre dans le widget."""
#         pass
#
#     def dnd_leave(self, source, event):
#         """Méthode appelée quand la souris quitte le widget."""
#         pass
#
#     def dnd_motion(self, source, event):
#         """Méthode appelée quand la souris bouge au-dessus du widget."""
#         pass
#
#     def dnd_commit(self, source, event):
#         """Méthode appelée pour valider le drop. Doit être surchargée."""
#         raise NotImplementedError("La méthode dnd_commit doit être implémentée.")


# --- Classes de glisser-déposer génériques (équivalent à wx.FileDropTarget, wx.TextDropTarget) ---

# # --- Gestion des types de données ---
# class FileDropTarget(TkinterDropTarget):
#     """
#     Gestion du drop de fichiers.
#     """
#     def __init__(self, widget, callback):
#         self.callback = callback
#         super().__init__(widget, ["DND_Files"])
#
#     def dnd_commit(self, source, event):
#         """Valide le drop de fichiers."""
#         if hasattr(source, "filenames"):
#             filenames = [urllib.parse.unquote(f) for f in source.filenames]
#             self.callback(filenames)
#
#
# class TextDropTarget(TkinterDropTarget):
#     """
#     Gestion du drop de texte.
#     """
#     def __init__(self, widget, callback):
#         self.callback = callback
#         super().__init__(widget, ["text/plain"])
#
#     def dnd_commit(self, source, event):
#         """Valide le drop de texte."""
#         if hasattr(source, "drag_data"):
#             self.callback(source.drag_data)
#
#
# class URLDropTarget(TkinterDropTarget):
#     """
#     Gestion du drop d'URLs.
#     """
#     def __init__(self, widget, callback):
#         self.callback = callback
#         super().__init__(widget, ["text/uri-list", "text/plain"])
#
#     def dnd_commit(self, source, event):
#         """Valide le drop d'URLs."""
#         if hasattr(source, "drag_data"):
#             url = source.drag_data
#             if re.match(r'^(http|https|ftp|mailto|file):', url):
#                 self.callback(url)
#             else:
#                 log.warning(f"Données dropées non reconnues comme URL : {url}")
#
#
# class FileTextDropTarget:
#     """
#     Gère le lâcher de fichiers et de texte.
#     Équivalent simplifié de wx.FileDropTarget et wx.TextDropTarget.
#     """
#
#     def __init__(self, widget, on_drop_callback):
#         # def __init__(self, widget, on_drop_url_callback=None, on_drop_file_callback=None):
#         self.widget = widget
#         self.__on_drop_callback = on_drop_callback
#         # self.__onDropURLCallback = on_drop_url_callback
#         # self.__onDropFileCallback = on_drop_file_callback
#         dnd.dnd_register(self.widget, "text/plain", self.__on_drop_callback)
#         dnd.dnd_register(self.widget, "DND_Files", self.__on_drop_callback)
#         # # Enregistrement des types de données que ce widget peut accepter
#         # dnd.dnd_register(self.widget, "text/plain", self.__dnd_accept)
#         # dnd.dnd_register(self.widget, "DND_Files", self.__dnd_accept)
#         # self.widget.dnd_accept = self.dnd_accept
#
#     def dnd_accept(self, source, event):
#         """Callback pour le module dnd."""
#         return self
#
#     def dnd_leave(self, source, event):
#         """Callback lorsque l'objet glissé quitte la cible."""
#         pass
#         # self.widget.config(cursor="")
#
#     def dnd_commit(self, source, event):
#         """Callback lorsque l'objet glissé est lâché."""
#         if hasattr(source, "drag_data"):
#             # Lâcher de données textuelles
#             self.__on_drop_callback(source.drag_data)
#             # # C'est un lâcher de données textuelles ou d'une URL
#             # url = source.drag_data
#             # if re.match(r'^(http|https|ftp|mailto|file):', url):
#             #     self.__onDropURLCallback(url)
#             # else:
#             #     # Traiter comme du texte si ce n'est pas une URL
#             #     self.__onDropURLCallback(f"text:{url}")
#         elif hasattr(source, "filenames"):
#             # Lâcher de fichiers (si la source est un gestionnaire de fichiers)
#             self.__on_drop_callback(source.filenames)
#         # elif hasattr(source, "filenames") and self.__onDropFileCallback:
#         #     # C'est un lâcher de fichiers
#         #     filenames = [urllib.parse.unquote(f[len("file://") :]) if f.startswith("file://") else f for f in source.filenames]
#         #     self.__onDropFileCallback(filenames)
#         # finally:
#         #     self.widget.config(cursor="")
#
#     # def dnd_enter(self, source, event):
#     #     """Gère l'entrée dans le widget cible."""
#     #     # On peut changer le curseur pour indiquer que le drop est possible
#     #     self.widget.config(cursor="hand1")
#     #     return self
#     #
#     # def dnd_motion(self, source, event):
#     #     """Gère le mouvement du curseur au-dessus du widget cible."""
#     #     pass # Pas de changement de curseur ici car géré par dnd_enter/dnd_leave
#
#     def OnDropText(self, x, y, text):  # pylint: disable=W0613,W0221
#         self.__onDropCallback(text)


class FileUrlDropTarget:
    """
    Une classe de remplacement pour wx.DropTarget qui gère le lâcher de fichiers et de texte/URLs.
    """

    def __init__(self, widget, on_drop_url_callback=None, on_drop_file_callback=None):
        self.widget = widget
        # self.__onDropURLCallback = on_drop_url_callback
        self.on_drop_url_callback = on_drop_url_callback
        # self.__onDropFileCallback = on_drop_file_callback
        self.on_drop_file_callback = on_drop_file_callback

        # # Enregistrement des types de données que ce widget peut accepter
        # dnd.dnd_register(self.widget, "text/plain", self.__dnd_accept)
        # dnd.dnd_register(self.widget, "DND_Files", self.__dnd_accept)
        # Le widget cible doit être accessible pour le glisser-déposer
        self.widget.dnd_enter = self.dnd_enter
        self.widget.dnd_leave = self.dnd_leave
        self.widget.dnd_motion = self.dnd_motion
        self.widget.dnd_commit = self.dnd_commit

    # def __dnd_accept(self, source, event):
    #     """Callback pour le module dnd."""
    #     return self

    def dnd_enter(self, source, event):
        """Callback lorsque le curseur entre dans le widget cible."""
        # return "drop_ok" if self.is_valid_source(source) else "drop_not_ok"
        # Indique si la source est valide pour ce drop target
        return "drop_ok" if hasattr(source, 'drag_data') else "drop_not_ok"

    def dnd_leave(self, source, event):
        """Callback lorsque l'objet glissé quitte la cible."""
        self.widget.config(cursor="")

    def dnd_motion(self, source, event):
        # """Gère le mouvement du curseur au-dessus du widget cible."""
        # pass # Pas de changement de curseur ici car géré par dnd_enter/dnd_leave
        """Callback lorsque le curseur se déplace au-dessus du widget cible."""
        # Change le curseur en fonction de la validité de la source
        if hasattr(source, 'drag_data'):
            self.widget.config(cursor="hand1")
            return "drop_ok"
        else:
            self.widget.config(cursor="no_entry")
            return "drop_not_ok"

    def dnd_commit(self, source, event):
        """Callback lorsque l'objet glissé est lâché."""
        # try:
        #     if hasattr(source, "drag_data") and self.__onDropURLCallback:
        #         # C'est un lâcher de données textuelles ou d'une URL
        #         url = source.drag_data
        #         if re.match(r'^(http|https|ftp|mailto|file):', url):
        #             self.__onDropURLCallback(url)
        #         else:
        #             # Traiter comme du texte si ce n'est pas une URL
        #             self.__onDropURLCallback(f"text:{url}")
        #
        #     elif hasattr(source, "filenames") and self.__onDropFileCallback:
        #         # C'est un lâcher de fichiers
        #         filenames = [urllib.parse.unquote(f[len("file://") :]) if f.startswith("file://") else f for f in source.filenames]
        #         self.__onDropFileCallback(filenames)
        # finally:
        #     self.widget.config(cursor="")
        if hasattr(source, "drag_data"):
            data = source.drag_data
            if isinstance(data, list):
                # Gère le lâcher de fichiers
                if self.on_drop_file_callback:
                    filenames = [urllib.parse.unquote(f) for f in data]
                    self.on_drop_file_callback(filenames)
            elif isinstance(data, str):
                # Gère le lâcher d'URLs ou de texte
                if self.on_drop_url_callback:
                    if re.match(r'^(http|https|ftp|mailto|file):', data):
                        self.on_drop_url_callback(data)
                    else:
                        self.on_drop_url_callback(f"text:{data}")
        self.widget.config(cursor="")

    # def dnd_enter(self, source, event):
    #     """Gère l'entrée dans le widget cible."""
    #     # On peut changer le curseur pour indiquer que le drop est possible
    #     self.widget.config(cursor="hand1")
    #     return self


# # --- Classe composite pour gérer plusieurs types de drops ---
# class CompositeDropTarget(TkinterDropTarget):
#     """
#     Gestionnaire composite pour différents types de drops (fichiers, URLs, texte).
#     """
#     def __init__(self, widget, url_callback=None, file_callback=None, text_callback=None):
#         self.url_callback = url_callback
#         self.file_callback = file_callback
#         self.text_callback = text_callback
#         accepted_types = []
#         if url_callback:
#             accepted_types.extend(["text/uri-list", "text/plain"])
#         if file_callback:
#             accepted_types.append("DND_Files")
#         if text_callback:
#             accepted_types.append("text/plain")
#         super().__init__(widget, accepted_types)
#
#     def dnd_commit(self, source, event):
#         """Valide le drop en fonction du type de données."""
#         if hasattr(source, "filenames") and self.file_callback:
#             filenames = [urllib.parse.unquote(f) for f in source.filenames]
#             self.file_callback(filenames)
#         elif hasattr(source, "drag_data"):
#             data = source.drag_data
#             if self.url_callback and re.match(r'^(http|https|ftp|mailto|file):', data):
#                 self.url_callback(data)
#             elif self.text_callback:
#                 self.text_callback(data)
#             else:
#                 log.warning(f"Données dropées non gérées : {data}")


# --- Classes pour le glisser-déposer d'arborescence (équivalent à TreeCtrlDragAndDropMixin) ---

class TreeHelperMixin(ttk.Treeview):
    """Fournit des méthodes utilitaires pour un Treeview."""

    def GetItemChildren(self, item=None, recursively=False):
        """Retourne les enfants d'un élément."""
        if not item:
            return self.get_children("")
        children = self.get_children(item)
        if recursively:
            all_children = list(children)
            for child in children:
                all_children.extend(self.GetItemChildren(child, True))
            return all_children
        return children

    def GetItemParent(self, item):
        """Retourne le parent d'un élément."""
        return self.parent(item)

    def GetItemPyData(self, item):
        """Récupère les données Python associées à un élément."""
        # return self.item(item, "tags")  # Utilisation des tags pour stocker les données
        # Règle CRITIQUE
        # 👉 L’objet métier ne doit PAS être stocké dans les tags
        # ✔️ Utilise un dictionnaire interne :
        self._item_to_object = getattr(self, '_item_to_object', {})


class TreeCtrlDragAndDropMixin(TreeHelperMixin):
    """
    Mixin pour permettre le glisser-déposer d'éléments dans un Treeview Tkinter.
    """
    # Propriétés de glissement
    dragged_items = []
    drag_data_type = ""
    drop_target = None
    drop_position = None

    def __init__(self, parent, *args, **kwargs):
        # super().__init__(*args, **kwargs)
        # TreeHelperMixin n'a pas d'__init__, donc pas besoin de l'appeler explicitement
        # self.bind("<ButtonPress-1>", self.on_start_drag)
        # # AttributeError: 'TreeCtrlDragAndDropMixin' object has no attribute 'bind'
        # # TODO : est-ce le bon endroit pour attacher les événements ?
        # self.bind("<B1-Motion>", self.on_dragging)
        # self.bind("<ButtonRelease-1>", self.on_end_drag)
        # # self.config(selectmode="extended")
        # # # AttributeError: 'TreeListCtrl' object has no attribute 'tk'
        # # Retarder l'appel à config en utilisant after
        # # self.after(1, self.config(selectmode="extended"))
        # # self.after(1, self._configure_selectmode)
        # # self ne fait pas référence à un objet Tkinter
        # # vous devez vous assurer que config est appelé sur un objet Tkinter valide.
        # if not hasattr(parent, 'tk'):
        #     raise TypeError("TreeCtrlDragAndDropMixin doit être utilisé avec un widget Tkinter valide.")
        # if hasattr(parent, 'config'):
        #     parent.config(selectmode="extended")
        # Les bind sont mis en place dans TreeListCtrl._bind_events() !
        # self.drop_handler = None
        self.drag_data: list[str]

        # # Ajout des méthodes dnd requises
        # self.dnd_enter = self.dnd_enter_callback
        # self.dnd_leave = self.dnd_leave_callback
        # self.dnd_end = self.dnd_end_callback
        # Le code utilise tkinter.dnd pour gérer le glisser-déposer.
        # Cependant, ce module est assez basique
        # et nécessite que la source et la cible implémentent des méthodes spécifiques.
        # Assurez-vous que toutes les méthodes requises par tkinter.dnd
        # sont correctement implémentées dans TreeCtrlDragAndDropMixin.
        # Notamment les méthodes dnd_enter, dnd_leave, dnd_commit,
        # dnd_enter_callback, dnd_leave_callback et dnd_end_callback.

    def on_start_drag(self, event):
        item = self.identify_row(event.y)
        if item:
            self.dragged_items = list(self.selection()) if self.selection() else [item]
            if not self.dragged_items or "" in self.dragged_items:  # Empêche de glisser l'élément racine
                self.dragged_items = []
                return
            # dnd.dnd_start(self, event)

            # Stocke les données à glisser pour le module dnd
            self.drag_data = self.dragged_items
            # self.dnd_enter(None, event)

            dnd.dnd_start(self, event)

    def on_dragging(self, event):
        x, y = event.x, event.y
        self.drop_target = self.identify_row(y)

        # Logique pour déterminer la position (sur, au-dessus, en-dessous)
        if self.drop_target:
            item_bbox = self.bbox(self.drop_target)
            if item_bbox:
                item_height = item_bbox[3]
                rel_y = y - item_bbox[1]
                if rel_y < item_height / 3:
                    self.drop_position = "above"
                elif rel_y > 2 * item_height / 3:
                    self.drop_position = "below"
                else:
                    self.drop_position = "on"

            # Gère le curseur et la sélection
            if self.is_valid_drop_target(self.drop_target):
                # self.config(cursor="hand2")
                self.config(cursor="hand1")
            else:
                # self.config(cursor="no")
                # self.config(cursor="no_drop")  # Correction ici
                self.config(cursor="no_entry")  # Correction ici
        else:
            self.config(cursor="")
            self.drop_target = None
            self.drop_position = None

    def on_end_drag(self, event):
        self.config(cursor="")
        if self.drop_target and self.is_valid_drop_target(self.drop_target):
            self.OnDrop(self.drop_target, self.dragged_items, self.drop_position)
        self.dragged_items = []
        self.drop_target = None
        self.drop_position = None

    def OnDrop(self, drop_item, dragged_items, part):
        """
        Cette méthode DOIT être surchargée dans la classe dérivée.
        """
        raise NotImplementedError("La méthode OnDrop doit être implémentée par la classe dérivée.")

    def is_valid_drop_target(self, drop_target):
        if not drop_target:
            return False

        # Empêcher de glisser un parent sur un enfant
        for dragged_item in self.dragged_items:
            current_item = drop_target
            while current_item:
                if current_item == dragged_item:
                    return False
                current_item = self.parent(current_item)

        # Empêcher de glisser un élément sur lui-même ou sur un de ses enfants
        if drop_target in self.dragged_items or drop_target in self.GetItemChildren(self.dragged_items, recursively=True):
            return False

        return True

    # --- Méthodes requises par le module tkinter.dnd ---

    def dnd_enter(self, source, event):
        """Gère l'entrée dans un widget cible."""
        return self

    def dnd_leave(self, source, event):
        """Gère la sortie d'un widget cible."""
        pass

    def dnd_commit(self, source, event):
        """Gère le lâcher sur un widget cible."""
        # La logique de drop est gérée dans on_end_drag
        pass

    def dnd_enter_callback(self, source, event):
        """
        Gère l'entrée dans un widget cible.
        """
        print(f"Entering target: {event.widget.winfo_name()}")
        # return "allowed"
        # Note : Le module dnd de Tkinter est basique et ne permet pas
        # de changer le curseur directement depuis cette méthode.
        # La logique de curseur est déplacée vers on_dragging.
        return self

    def dnd_leave_callback(self, source, event):
        """
        Gère la sortie d'un widget cible.
        """
        print(f"Leaving target: {event.widget.winfo_name()}")

    def dnd_end_callback(self, source, event):
        """
        Gère la fin de l'opération de glisser-déposer.
        """
        print(f"Drag operation ended.")
        # La logique de fin de drag est gérée dans on_end_drag.
        pass


# --- Exemple d'utilisation (pour démonstration) ---
if __name__ == "__main__":
    # from tkinter import ttk
    def on_drop_url(url):
        print(f"URL/Texte lâché : {url}")

    def on_drop_file(filenames):
        # print("Fichiers lâchés :")
        # for f in filenames:
        #     print(f)
        print(f"Fichiers lâchés : {filenames}")

    def on_drop_text(text):
        print(f"Texte lâché : {text}")

    # class TaskCoachTree(TreeCtrlDragAndDropMixin, ttk.Treeview):
    #     def OnDrop(self, drop_item, dragged_items, part):
    #         print(f"Éléments glissés: {dragged_items} sur {drop_item} à la position: {part}")
    #
    #         # Exemple de déplacement simple
    #         for item in dragged_items:
    #             if part == "on":
    #                 # Déplacer l'élément pour qu'il devienne un enfant
    #                 self.move(item, drop_item, "end")
    #             else:
    #                 # Déplacer l'élément au-dessus ou en-dessous
    #                 index = self.index(drop_item)
    #                 if part == "below":
    #                     index += 1
    #                 self.move(item, self.parent(drop_item), index)

    # root = tk.Tk()
    # root.title("Exemple de Drag and Drop de Treeview Tkinter")
    #
    # # Exemple avec un Label
    # label = ttk.Label(root, text="Déposez ici un fichier, une URL ou du texte")
    # label.pack(pady=20, padx=20)
    #
    # # Utilisation de la classe CompositeDropTarget
    # drop_target = CompositeDropTarget(
    #     label,
    #     url_callback=on_drop_url,
    #     file_callback=on_drop_file,
    #     text_callback=on_drop_text
    # )

    # Exemple avec un Treeview
    class MyTree(TreeCtrlDragAndDropMixin, ttk.Treeview):
        def OnDrop(self, drop_item, dragged_items, part):
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

    # # root_item = tree.insert("", "end", text="Racine Cachée", tags=("root",))
    #
    # # tree = TaskCoachTree(root)
    # tree = MyTree(root)
    # # tree.heading("#0", text="Tâches")
    # tree.heading("#0", text="Arborescence")
    #
    # # id1 = tree.insert("", "end", text="Tâche 1")
    # # tree.insert(id1, "end", text="Sous-tâche 1.1")
    # # tree.insert(id1, "end", text="Sous-tâche 1.2")
    #
    # # id2 = tree.insert("", "end", text="Tâche 2")
    #
    # tree.insert("", "end", text="racine")
    #
    # # tree.pack(fill="both", expand=True)
    # tree.pack(expand=True, fill="both", padx=20, pady=20)

    root = tk.Tk()
    # top_level = tk.Toplevel()
    root.title("Exemple de File/URL Drop Target Tkinter")
    # top_level.title("Exemple de File/URL Drop Target")
    # # root.geometry("400x300")
    # top_level.geometry("400x300")
    #
    # Exemple avec un Label
    # # label = ttk.Label(root, text="Glissez-déposez des fichiers ou des URLs ici", relief="solid", padding=20)
    # label = ttk.Label(top_level, text="Glissez-déposez des fichiers ou des URLs ici", relief="solid", padding=20)
    label = ttk.Label(root, text="Déposez ici des fichiers ou des URLs/texte")
    # label.pack(expand=True, fill="both", padx=20, pady=20)
    label.pack(pady=20, padx=20)
    #
    # # Initialiser notre nouvelle classe pour le Label
    # FileUrlDropTarget(label, on_drop_url, on_drop_files)
    # Utilisation de la classe FileUrlDropTarget
    drop_target = FileUrlDropTarget(
        label,
        on_drop_url_callback=on_drop_url,
        on_drop_file_callback=on_drop_file
    )

    # Exemple avec un Treeview
    tree = MyTree(root)
    tree.heading("#0", text="Arborescence")
    id1 = tree.insert("", "end", text="Tâche 1")
    id1_1 = tree.insert(id1, "end", text="Sous-tâche 1.1")
    id1_2 = tree.insert(id1, "end", text="Sous-tâche 1.2")
    id2 = tree.insert("", "end", text="Tâche 2")

    tree.pack(expand=True, fill="both", padx=20, pady=20)

    root.mainloop()
