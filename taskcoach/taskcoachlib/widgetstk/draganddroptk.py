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

# Voici les améliorations principales :
# Améliorations majeures
# 1. Structure claire et modulaire
#
# FileUrlDropTarget : Stub pour compatibilité (nécessiterait tkinterdnd2 pour un vrai support)
# TreeHelperMixin : Méthodes utilitaires pour Treeview
# TreeCtrlDragAndDropMixin : Mixin principal complet pour le drag-and-drop

# 2. Gestion correcte des données d'objet
# dans GetItemPyData et SetItemPyData
# Important : Ne JAMAIS stocker l'objet métier dans les tags !

# 3. Validation complète du drop
#
# Empêche de dropper sur soi-même
# Empêche de dropper un parent sur ses enfants
# Empêche de dropper sur les descendants
# Support callback personnalisé via validateDrag

# 4. Gestion robuste des curseurs
# Avec fallback multi-plateforme :
# Dans _set_cursor_no_drop, curseurs différents par système d'exploitation.

# 5. Méthodes de compatibilité wxPython
# Pour faciliter la migration :
# GetSelections(), UnselectAll(), SelectItem()
# GetItemChildren(), GetItemParent(), GetItemPyData()
#
# 6. Documentation complète
# Docstrings détaillées
# Exemple d'utilisation fonctionnel inclus
# Logging pour debugging
#
# Points clés pour l'utilisation dans treectrltk.py
#
# 1. L'ordre d'héritage est important :
# class TreeListCtrl(TreeCtrlDragAndDropMixin, ttk.Treeview)
# 2. Les bindings doivent être faits APRÈS l'init du widget
# 3. OnDrop doit être implémentée

# Ce que tkinterdnd2 sait faire
# ✅ Drop depuis l’extérieur :
# fichiers depuis le gestionnaire de fichiers
# texte / URL depuis navigateur, éditeur, etc.
# ❌ Il ne remplace PAS :
# le drag interne du Treeview (ça reste géré par <ButtonPress> / <Motion> / <ButtonRelease>)

# Important
# TkinterDnD.Tk remplace tk.Tk
# ne PAS mélanger avec tkinter.dnd (à supprimer définitivement)

"""Glisser-déposer pour Tkinter/ttk.Treeview.

Le glissement interne à ttk.Treeview utilise les événements Tk ordinaires.
Les dépôts depuis d'autres applications nécessitent tkinterdnd2 et une
racine initialisée avec TkinterDnD.Tk (ou TkinterDnD._require(root)).

Le mixin n'altère pas le modèle : OnDrop doit effectuer la modification.

Le module sépare deux mécanismes :

* ``TreeCtrlDragAndDropMixin`` gère le déplacement interne d'éléments d'un
  ``ttk.Treeview`` avec les événements Tk classiques (Tkinter standard).
* ``TkDnDDropTarget`` gère les dépôts provenant d'autres applications avec
  ``tkinterdnd2``.

L'API publique conserve les noms principaux de l'ancienne implémentation
wxPython : ``OnDrop``, ``GetItemChildren``, ``GetItemParent``,
``GetItemPyData``, ``SetItemPyData``, ``GetSelections``, ``UnselectAll``,
``SelectItem`` et ``validateDrag``.
Le mixin ne déplace PAS les données : OnDrop appartient à l'appelant.
"""
from __future__ import annotations

import logging
import urllib.parse
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import ttk
# from tkinter import dnd

from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname
# import re
# from tkinterdnd2 import DND_FILES, DND_TEXT, TkinterDnD
# import urllib.parse

log = logging.getLogger(__name__)

try:
    from tkinterdnd2 import COPY, DND_FILES, DND_TEXT, REFUSE_DROP
    _TKDND_AVAILABLE = True
except ImportError:  # Le module reste importable sans l'extension optionnelle.
    #  # Le DnD interne fonctionne sans cette dépendance.
    COPY = "copy"
    DND_FILES = "DND_Files"
    DND_TEXT = "DND_Text"
    REFUSE_DROP = "refuse_drop"
    _TKDND_AVAILABLE = False

# # Note : Les fonctionnalités de glisser-déposer de messages électroniques
# # de Thunderbird, Outlook et Mail.app ne peuvent pas être directement
# # converties en Tkinter sans des modules externes complexes et spécifiques à la plateforme.
# # Cette conversion se concentre sur les fichiers et les URLs/texte.

# DropFilesCallback = Callable[[int, int, List[str]], Any]
# DropTextCallback = Callable[[str], Any]
# DropUrlCallback = Callable[[str], Any]

# # --- Classe pour initier une opération de glisser-déposer (source) ---
# class DragSource:
#     """
#     Une classe simple pour initier une opération de glisser-déposer.
#     L'objet de données est stocké dans l'attribut `drag_data`.
#     """
#     def __init__(self, widget, drag_data):
#         self.widget = widget
#         self.drag_data = drag_data
#         self.widget.bind("<ButtonPress-1>", self.on_start_drag)
#
#     def on_start_drag(self, event):
#         dnd.dnd_start(self, event)
#         self.widget.config(cursor="hand1")


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

def _file_url_to_path(value):
    """Convertit une URL file:// en chemin local, si applicable."""
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "file":
        return value
    path = url2pathname(unquote(parsed.path))
    if parsed.netloc and parsed.netloc.lower() != "localhost":
        return "//" + parsed.netloc + path
    return path


# DROP EXTERNE VIA tkinterdnd2
# Cette classe remplace tous les essais avec dnd_*
class TkDnDDropTarget:
    """
    Gestionnaire de drop externe basé sur tkinterdnd2.

    Récepteur externe de fichiers et de texte via tkinterdnd2.

    Le widget doit appartenir à une fenêtre TkinterDnD.Tk (ou disposer de
    drop_target_register et dnd_bind). Les callbacks reçoivent les données
    décodées et peuvent retourner une valeur ; l'action de dépôt est « copy ».

    Réception des dépôts externes, avec callbacks (données, événement).

    `event.type` indique normalement le format négocié par tkdnd. Pour éviter
    de confondre un texte contenant des espaces avec des chemins, les deux
    formats ont des handlers dédiés. Le handler générique est un repli.

    Gère :
    - fichiers (DND_FILES)
    - texte / URL (DND_TEXT)

    Cette classe est volontairement simple et stable.
    """

    def __init__(self, widget: tk.Widget,
                 on_files: Optional[Callable[[List[str]], None]] = None,
                 on_text: Optional[Callable[[str], None]] = None,
                 # on_url: Optional[DropUrlCallback] = None,
                 on_drag_over: Optional[Callable[[int, int, Any], Any]] = None,
                 # on_drop_file: Optional[DropFilesCallback] = None,
                 # on_drop_url: Optional[DropUrlCallback] = None,
                 ) -> None:
        """
        Initialise le gestionnaire de drop externe.

        Args:
            widget (tk.Widget): widget Tkinter cible
            on_files (callable): callback(list[str]) appelé avec une liste de chemins de fichiers
            on_text (callable): callback(str) appelé avec une chaîne de texte ou une URL
        """
        # if DND_FILES is None:
        #     raise RuntimeError(
        #         "Le dépôt depuis d'autres applications nécessite tkinterdnd2 "
        #         "(pip install tkinterdnd2) et une racine TkinterDnD.Tk."
        #     )
        # if not hasattr(widget, "drop_target_register") or not hasattr(widget, "dnd_bind"):
        #     raise TypeError("Le widget doit être compatible avec tkinterdnd2.")
        if not _TKDND_AVAILABLE:
            raise RuntimeError("Installer tkinterdnd2 pour les dépôts externes.")
        if not all(hasattr(widget, name) for name in ("drop_target_register", "dnd_bind")):
            raise TypeError("Widget non initialisé avec tkinterdnd2.")
        self.widget = widget                  # widget cible
        self.on_files = on_files              # callback fichiers
        self.on_text = on_text                # callback texte / URL
        # self.on_url = on_url or on_drop_url
        self.on_drag_over = on_drag_over

        # formats = []
        types = []
        if on_files is not None:
            # formats.append(DND_FILES)
            types.append(DND_FILES)
        if on_text is not None:
            # formats.append(DND_TEXT)
            types.append(DND_TEXT)
        # if formats:
        if types:
            # Enregistrement des types acceptés
            # widget.drop_target_register(DND_FILES, DND_TEXT)
            # widget.drop_target_register(*formats)
            widget.drop_target_register(*types)
            # widget.dnd_bind("<<Drop:DND_Files>>", self._on_drop_files)
            # widget.dnd_bind("<<Drop:DND_Text>>", self._on_drop_text)
            # # Certaines versions de tkdnd envoient l'événement générique.
            # widget.dnd_bind("<<Drop>>", self._on_drop_generic)
            # widget.dnd_bind("<<DragOver>>", self._on_drag_over)
            # Liaison de l’événement de drop
            widget.dnd_bind("<<Drop>>", self._on_drop)
            if on_drag_over is not None:
                widget.dnd_bind("<<DropPosition>>", self._on_position)
    # def _on_drag_over(self, event: Any) -> str:
    #     result: Any = COPY
    #     if self.on_drag_over is not None:
    #         custom = self.on_drag_over(event.x, event.y, result)
    #         if custom is not None:
    #             result = custom
    #     return result
    #
    # def _parse_files(self, data: str) -> List[str]:
    #     """Décode une liste Tcl de chemins sans casser les espaces/accolades."""
    #     return list(self.widget.tk.splitlist(data))
    #
    # def _emit_files(self, event: Any) -> str:
    #     filenames = self._parse_files(str(event.data))
    #     if self.on_files is not None:
    #         self.on_files(event.x, event.y, filenames)
    #     return COPY
    #
    # def _emit_text(self, event: Any) -> str:
    #     text = str(event.data)
    #     if self.on_url is not None and self._looks_like_url(text):
    #         self.on_url(text.strip())
    #     elif self.on_text is not None:
    #         self.on_text(text)
    #     return COPY
    #
    # def _on_drop_files(self, event: Any) -> str:
    #     return self._emit_files(event)
    #
    # def _on_drop_text(self, event: Any) -> str:
    #     return self._emit_text(event)
    #
    # def _on_drop_generic(self, event: Any) -> str:
    #     # L'événement générique est utile avec d'anciennes versions de tkdnd,
    #     # mais on ne déduit le type fichier que si le split Tcl est concluant.
    #     data = str(event.data)
    #     try:
    #         values = self._parse_files(data)
    #     except tk.TclError:
    #         values = []
    #     if values and all("\n" not in value for value in values):
    #         if self.on_files is not None and any(value.startswith(("/", "~", "file:")) for value in values):
    #             if all(not urllib.parse.urlparse(value).scheme or value.startswith("file:") for value in values):
    #                 return self._emit_files(event)
    #     return self._emit_text(event)

    def _on_position(self, event):
        """Callback TkinterDnD (<<DropPosition>>) appelé lors du survol.

        Interroge le callback `on_drag_over` avec les coordonnées actuelles
        pour déterminer si l'action de dépôt est acceptée ou refusée.
        """
        try:
            result = self.on_drag_over(getattr(event, "x", 0),
                                       getattr(event, "y", 0), COPY)
            return COPY if result is None else result
        except Exception:
            log.exception("TkDnDDropTarget._on_position : Erreur dans le callback de survol !")
            return REFUSE_DROP

    def _on_drop(self, event):
        """
        Callback appelé lors d'un drop externe.
        """
        # return self._on_drop_generic(event)
        # data = event.data                    # données brutes Tcl
        data = getattr(event, "data", "")
        # if not data:
        #     return
        # kind = str(getattr(event, "type", ""))
        kind = str(getattr(event, "type", "")).lower()
        # # tkinterdnd2 fournit généralement event.type = 'DND_Files'/'DND_Text'.
        # is_files = kind.lower() in ("dnd_files", "dnd-files", "files")
        # if not is_files and self.on_files and not self.on_text:
        #     is_files = True
        #
        # # # Cas du dépôt de fichiers
        # # # if event.action == 'copy' and data.startswith('{'):
        # # #     files = self._parse_files(data)
        # # #     if self.on_files:
        # # #         self.on_files(files)
        # # #     return
        # # if data.startswith("{") and self.on_files:
        # #     filenames = self._parse_filenames(data)
        # #     self.on_files(filenames)
        # #     return
        # if is_files and self.on_files:
        #     try:
        #         files = list(self.widget.tk.splitlist(data))
        #     except tk.TclError:
        #         log.warning("Liste Tcl de fichiers invalide : %r", data)
        #         return "refuse_drop"
        #     self.on_files([_file_url_to_path(path) for path in files], event)
        # # Cas du dépôt de texte ou d'URL
        # elif self.on_text:
        #     self.on_text(data, event)
        # else:
        #     return "refuse_drop"
        # return "copy"
        try:
            if kind in ("dnd_files", "dnd-files", "files") or (
                self.on_files is not None and self.on_text is None
            ):
                if self.on_files is None:
                    return REFUSE_DROP
                files = [_file_url_to_path(x) for x in self.widget.tk.splitlist(data)]
                result = self.on_files(files, event)
            elif kind in ("dnd_text", "dnd-text", "text") or (
                self.on_text is not None and self.on_files is None
            ):
                if self.on_text is None:
                    return REFUSE_DROP
                result = self.on_text(data, event)
            else:
                # Les données seules ne permettent pas d'identifier sûrement
                # le format. Refuser plutôt que d'appeler le mauvais callback.
                log.warning("TkDnDDropTarget._on_drop : Format de dépôt ambigu : %r", kind)
                return REFUSE_DROP
            return REFUSE_DROP if result is False else COPY
        except (tk.TclError, ValueError):
            log.exception("TkDnDDropTarget._on_drop : Données de dépôt invalides !")
            return REFUSE_DROP
        except Exception:
            log.exception("TkDnDDropTarget._on_drop : Erreur pendant le dépôt externe !")
            return REFUSE_DROP

    # @staticmethod
    # def _parse_files(data: str) -> List[str]:
    #     """
    #     Convertit la chaîne Tcl de fchiers en liste Python de chemins.
    #
    #     Args:
    #         data (str): données Tcl
    #
    #     Returns:
    #         list[str] : Liste de chemins de fichiers
    #     """
    #     # Suppression des accolades Tcl
    #     files = data.strip('{}')
    #
    #     # Séparation propre (chemins avec espaces)
    #     return files.split('} {')


# --- Classes de glisser-déposer génériques (équivalent à wx.FileDropTarget, wx.TextDropTarget) ---

# # # --- Gestion des types de données ---
# # class FileDropTarget(TkinterDropTarget):
# class FileDropTarget(TkDnDDropTarget):
class FileDropTarget:
    """
    Gestion du drop de fichiers.
    Équivalent Tkinter de ``wx.FileDropTarget``.

    Gère le dépôt/lâcher de fichiers et d'URLs/texte.
    Équivalent Tkinter de wx.DropTarget avec support fichiers et URLs.

    Adaptateur de callback wx : onDropCallback(x, y, filenames).

    Appeler ``attach(widget)`` pour activer la réception externe.
    """
    #     Cette classe n'utilise PAS tkinter.dnd car il est trop basique.
    #     Le glisser-déposer de fichiers externes nécessiterait tkinterdnd2.
    #     Pour l'instant, on se concentre sur le drag-and-drop interne.

    # def __init__(self, widget, callback):
    #     self.callback = callback
    #     super().__init__(widget, ["DND_Files"])
    #
    # def __init__(self, widget: tk.Widget, onDropCallback: Optional[DropFilesCallback] = None,
    #              onDragOverCallback: Optional[Callable[[int, int, Any], Any]] = None) -> None:
    #     super().__init__(widget, on_files=onDropCallback, on_drag_over=onDragOverCallback)

    def __init__(self, onDropCallback=None, onDragOverCallback=None):
        """Initialise la cible de dépôt de fichiers.

        Args:
            onDropCallback: Callback appelé lors du dépôt sous la forme
                `callback(x, y, filenames)`.
            onDragOverCallback: Callback optionnel appelé lors du survol
                sous la forme `callback(x, y, defaultResult)`.
        """
        self.onDropCallback = onDropCallback
        self.onDragOverCallback = onDragOverCallback
        self._receiver = None

    # def dnd_commit(self, source, event):
    #     """Valide le drop de fichiers."""
    #     if hasattr(source, "filenames"):
    #         filenames = [urllib.parse.unquote(f) for f in source.filenames]
    #         self.callback(filenames)

    def attach(self, widget):
        """Associe la cible de dépôt au widget Tkinter spécifié."""
        # self._receiver = TkDnDDropTarget(widget, on_files=self._on_files)
        self._receiver = TkDnDDropTarget(widget, self._on_files,
                                          on_drag_over=self.OnDragOver)
        return self

    def _on_files(self, files, event):
        """Relaye l'événement TkDnD vers OnDropFiles avec les coordonnées de la souris."""
        self.OnDropFiles(getattr(event, "x", 0), getattr(event, "y", 0), files)

    def OnDropFiles(self, x, y, filenames):
        """Traite le dépôt d'une liste de fichiers aux coordonnées (x, y).

        Returns:
            bool: True ou le résultat retourné par le callback, False si aucun callback.
        """
        if self.onDropCallback is None:
            return False
        # self.onDropCallback(x, y, filenames)
        # return True
        return self.onDropCallback(x, y, filenames)

    def OnDragOver(self, x, y, defaultResult):
        """Gère le survol pendant le déplacement de fichiers au-dessus du widget."""
        if self.onDragOverCallback is not None:
            return self.onDragOverCallback(x, y, defaultResult)
        return defaultResult


# # class TextDropTarget(TkinterDropTarget):
# class TextDropTarget(TkDnDDropTarget):
class TextDropTarget:
    """
    Gestion du drop de texte. sans argument de position.
    Équivalent Tkinter de ``wx.TextDropTarget``.
    Adaptateur wx : onDropCallback(text).
    """
    # def __init__(self, widget, callback):
    #     self.callback = callback
    #     super().__init__(widget, ["text/plain"])
    #
    # def __init__(self, widget: tk.Widget, onDropCallback: Optional[DropTextCallback] = None) -> None:
    #     super().__init__(widget, on_text=onDropCallback)

    def __init__(self, onDropCallback):
        """Initialise la cible de dépôt de texte avec son callback."""
        self.onDropCallback = onDropCallback
        self._receiver = None

    # def dnd_commit(self, source, event):
    #     """Valide le drop de texte."""
    #     if hasattr(source, "drag_data"):
    #         self.callback(source.drag_data)

    def attach(self, widget):
        """Associe la cible de dépôt de texte au widget Tkinter spécifié."""
        self._receiver = TkDnDDropTarget(widget, on_text=self._on_text)
        return self

    def _on_text(self, text, event):
        """Relaye l'événement TkDnD vers OnDropText avec les coordonnées de l'événement."""
        self.OnDropText(getattr(event, "x", 0), getattr(event, "y", 0), text)

    def OnDropText(self, x, y, text):
        """Traite le dépôt de texte en invoquant onDropCallback."""
        # self.onDropCallback(text)
        # return True
        if self.onDropCallback is None:
            return False
        return self.onDropCallback(text)


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
class DropTarget:
    """Réception de fichiers et d'URL/texte.

    Les formats propriétaires de courriels wx (Outlook, Thunderbird, Claws)
    ne sont pas émulés : ils exigent des intégrations propres à l'OS.
    """

    def __init__(self, onDropFileCallback=None, onDropUrlCallback=None,
                 onDragOverCallback=None, **kwargs):
        """Initialise la cible composite de dépôt de fichiers et d'URLs/texte.

        Les kwargs surnuméraires sont ignorés pour compatibilité avec l'API wx.
        """
        self.onDropFileCallback = onDropFileCallback
        self.onDropUrlCallback = onDropUrlCallback
        self.onDragOverCallback = onDragOverCallback
        self._receiver = None
        if kwargs:
            log.debug("DropTarget.__init__ : Arguments de compatibilité ignorés : %s", sorted(kwargs))

    def attach(self, widget):
        """Lie la cible de dépôt au widget Tkinter cible via TkDnDDropTarget."""
        self._receiver = TkDnDDropTarget(
            widget,
            on_files=self._files if self.onDropFileCallback else None,
            on_text=self._text if self.onDropUrlCallback else None,
            on_drag_over=self.OnDragOver if self.onDragOverCallback else None,
        )
        return self

    def reinit(self):
        """Compatibilité wx : Aucun objet de données wx à réinitialiser."""

    def _files(self, files, event):
        """Transmet les fichiers déposés au callback onDropFileCallback."""
        if self.onDropFileCallback:
            self.onDropFileCallback(getattr(event, "x", 0),
                                    getattr(event, "y", 0), files)

    def _text(self, value, event):
        """Transmet le texte ou l'URL déposé au callback onDropUrlCallback."""
        if self.onDropUrlCallback:
            self.onDropUrlCallback(getattr(event, "x", 0),
                                   getattr(event, "y", 0), value)

    def OnDragOver(self, x, y, defaultResult):
        """Gère le survol pendant le glisser composite et renvoie l'action autorisée."""
        if self.onDragOverCallback:
            return self.onDragOverCallback(x, y, defaultResult)
        return defaultResult


# # # CLASSES DE BASE POUR LE GLISSER-DÉPOSER DE FICHIERS/URLS
# # class FileUrlDropTarget:
# class FileUrlDropTarget(TkDnDDropTarget):
class FileUrlDropTarget(DropTarget):
    """Alias explicite pour la réception de fichiers et d'URL.

    Façade de compatibilité pour l'ancien nom ``FileUrlDropTarget``.

    Gère le dépôt/lâcher de fichiers et d'URLs/texte.
    Équivalent Tkinter de wx.DropTarget avec support fichiers et URLs.

    Cette classe n'utilise PAS tkinter.dnd car il est trop basique.
    Le glisser-déposer de fichiers externes nécessiterait tkinterdnd2.
    Pour l'instant, on se concentre sur le drag-and-drop interne.
    """
    # # def __init__(self, widget: tk.Widget,
    # #              on_drop_url_callback: Optional[Callable] = None,
    # #              on_drop_file_callback: Optional[Callable] = None):
    # def __init__(self, widget: tk.Widget, on_drop_url_callback: Optional[DropUrlCallback] = None,
    #              on_drop_file_callback: Optional[DropFilesCallback] = None,
    #              on_drop_text_callback: Optional[DropTextCallback] = None,
    #              **kwargs: Any) -> None:
    #     """
    #     Initialise le gestionnaire de drop.
    #
    #     Args:
    #         widget: Widget Tkinter cible
    #         on_drop_file_callback: Callback pour fichiers (x, y, filenames)
    #         on_drop_text_callback: Callback pour textes (
    #         kwargs: Liste d'arguments optionnel.
    #     """
    #     # super().__init__(
    #     #     widget,
    #     #     on_files=on_drop_file_callback,
    #     #     on_text=on_drop_text_callback,
    #     #     on_url=on_drop_url_callback,
    #     #     **kwargs,
    #     # )
    #     self.widget = widget
    #     # self.__onDropURLCallback = on_drop_url_callback
    #     self.on_drop_url_callback = on_drop_url_callback
    #     # self.__onDropFileCallback = on_drop_file_callback
    #     self.on_drop_file_callback = on_drop_file_callback
    #
    #     # # Enregistrement des types de données que ce widget peut accepter
    #     # dnd.dnd_register(self.widget, "text/plain", self.__dnd_accept)
    #     # dnd.dnd_register(self.widget, "DND_Files", self.__dnd_accept)
    #     # Le widget cible doit être accessible pour le glisser-déposer
    #     self.widget.dnd_enter = self.dnd_enter
    #     self.widget.dnd_leave = self.dnd_leave
    #     self.widget.dnd_motion = self.dnd_motion
    #     self.widget.dnd_commit = self.dnd_commit
    #     log.debug("FileUrlDropTarget initialisé (stub - pas de support externe)")
    #
    # # def __dnd_accept(self, source, event):
    # #     """Callback pour le module dnd."""
    # #     return self
    #
    # def dnd_enter(self, source, event):
    #     """Callback lorsque le curseur entre dans le widget cible."""
    #     # return "drop_ok" if self.is_valid_source(source) else "drop_not_ok"
    #     # Indique si la source est valide pour ce drop target
    #     return "drop_ok" if hasattr(source, 'drag_data') else "drop_not_ok"
    #
    # def dnd_leave(self, source, event):
    #     """Callback lorsque l'objet glissé quitte la cible."""
    #     self.widget.config(cursor="")
    #
    # def dnd_motion(self, source, event):
    #     # """Gère le mouvement du curseur au-dessus du widget cible."""
    #     # pass # Pas de changement de curseur ici car géré par dnd_enter/dnd_leave
    #     """Callback lorsque le curseur se déplace au-dessus du widget cible."""
    #     # Change le curseur en fonction de la validité de la source
    #     if hasattr(source, 'drag_data'):
    #         self.widget.config(cursor="hand1")
    #         return "drop_ok"
    #     else:
    #         self.widget.config(cursor="no_entry")
    #         return "drop_not_ok"
    #
    # def dnd_commit(self, source, event):
    #     """Callback lorsque l'objet glissé est lâché."""
    #     # try:
    #     #     if hasattr(source, "drag_data") and self.__onDropURLCallback:
    #     #         # C'est un lâcher de données textuelles ou d'une URL
    #     #         url = source.drag_data
    #     #         if re.match(r'^(http|https|ftp|mailto|file):', url):
    #     #             self.__onDropURLCallback(url)
    #     #         else:
    #     #             # Traiter comme du texte si ce n'est pas une URL
    #     #             self.__onDropURLCallback(f"text:{url}")
    #     #
    #     #     elif hasattr(source, "filenames") and self.__onDropFileCallback:
    #     #         # C'est un lâcher de fichiers
    #     #         filenames = [urllib.parse.unquote(f[len("file://") :]) if f.startswith("file://") else f for f in source.filenames]
    #     #         self.__onDropFileCallback(filenames)
    #     # finally:
    #     #     self.widget.config(cursor="")
    #     if hasattr(source, "drag_data"):
    #         data = source.drag_data
    #         if isinstance(data, list):
    #             # Gère le lâcher de fichiers
    #             if self.on_drop_file_callback:
    #                 filenames = [urllib.parse.unquote(f) for f in data]
    #                 self.on_drop_file_callback(filenames)
    #         elif isinstance(data, str):
    #             # Gère le lâcher d'URLs ou de texte
    #             if self.on_drop_url_callback:
    #                 if re.match(r'^(http|https|ftp|mailto|file):', data):
    #                     self.on_drop_url_callback(data)
    #                 else:
    #                     self.on_drop_url_callback(f"text:{data}")
    #     self.widget.config(cursor="")
    #
    # # def dnd_enter(self, source, event):
    # #     """Gère l'entrée dans le widget cible."""
    # #     # On peut changer le curseur pour indiquer que le drop est possible
    # #     self.widget.config(cursor="hand1")
    # #     return self


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


# HELPER MIXIN POUR TREEVIEW
# --- Classes pour le glisser-déposer d'arborescence (équivalent à TreeCtrlDragAndDropMixin) ---

# class TreeHelperMixin(ttk.Treeview):
class TreeHelperMixin:
    """
    Fournit des méthodes utilitaires pour un Treeview.

    Méthodes indépendantes de ``ttk.Treeview`` mais prévues pour lui.
    Équivalent des méthodes helper de wx.TreeCtrl.
    Méthodes de compatibilité wx pour une classe dérivée de ttk.Treeview.

    Exemple : ``class MyTree(TreeCtrlDragAndDropMixin, ttk.Treeview): ...``
    """

    def __init__(self, *args, **kwargs):
        """Initialise le dictionnaire d'association des identifiants d'éléments vers leurs objets métier."""
        # self._item_to_object = {}
        if not hasattr(self, "_item_to_object"):  # Même principe appliquer dans _CtrlWithItemsMixin !
            self._item_to_object: Dict[str, Any] = {}
        # Sinon, lorsqu'un deuxième constructeur initialise son mixin,
        # il peut effacer les associations entre les identifiants des lignes
        # et les objets métier.
        super().__init__(*args, **kwargs)
        log.info("TreeHelperMixin.__init__ : Dictionnaire self._item_to_object=%s", self._item_to_object)

    def GetRootItem(self) -> str:
        """La racine implicite de ttk.Treeview est la chaîne vide."""
        return ""

    def GetItemChildren(self, item: Optional[str] = None,
                        recursively: bool = False) -> List[str]:
        """Retourne les enfants d'un élément.

        Retourne les enfants directs ou tous les descendants, sans doublons.

        Args:
            item: ID de l'élément (None = racine)
            recursively: Si True, inclut tous les descendants

        Returns:
            Liste des IDs d'enfants
        """
        result = []
        # # # if not item:
        # # #     return self.get_children("")
        # # if item is None:
        # #     item = ""
        # parent = "" if item is None else item
        # # children = self.get_children(item)
        # # children = list(self.get_children(item))
        # children = list(self.get_children(parent))
        #
        # if not recursively:
        #     return children
        # # if recursively:
        # #     # all_children = list(children)
        # #     all_children = children
        # #     for child in children:
        # #         all_children.extend(self.GetItemChildren(child, True))
        # #     return all_children
        # result: List[str] = []
        # # for child in children:
        # for child in self.get_children("" if item is None else item):
        for child in self.get_children(item or ""):
            result.append(child)
            # result.extend(self.GetItemChildren(child, recursively=True))
            if recursively:
                result.extend(self.GetItemChildren(child, True))
        # return children
        log.debug("TreeHelperMixin.GetItemChildren : retourne les enfants de %s : %s", item, result)
        return result

    def GetItemParent(self, item: str) -> str:
        """Retourne le parent d'un élément."""
        # return self.parent(item)
        return self.parent(item) if item else ""

    def GetItemPyData(self, item: str) -> Any:
        """Récupère les données Python associées à un élément.

        IMPORTANT: Ne PAS stocker l'objet métier dans les tags!
        Utiliser un dictionnaire interne _item_to_object.
        """
        # # return self.item(item, "tags")  # Utilisation des tags pour stocker les données
        # # Règle CRITIQUE
        # # 👉 L’objet métier ne doit PAS être stocké dans les tags
        # # ✔️ Utilise un dictionnaire interne :
        # self._item_to_object = getattr(self, '_item_to_object', {})
        if not hasattr(self, '_item_to_object'):
            self._item_to_object = {}
        return self._item_to_object.get(item)

    def SetItemPyData(self, item: str, data: Any):
        """
        Associe des données Python à un élément.

        Args:
            item: ID de l'élément
            data: Objet métier à associer
        """
        if not hasattr(self, '_item_to_object'):
            self._item_to_object = {}
        self._item_to_object[item] = data

    def delete(self, *items: str):
        """Nettoie les associations d'objets lors de la suppression d'items.

        Supprime les éléments et nettoie les associations d'objets métier de leurs descendants.
        """
        for item in items:
            if self.exists(item):
                # descendants = self.GetItemChildren(item, recursively=True)
                # for identifier in [item, *descendants]:
                for descendant in [item] + self.GetItemChildren(item, True):
                    # self._item_to_object.pop(identifier, None)
                    self._item_to_object.pop(descendant, None)
        # super().delete(*items)
        return super().delete(*items)

    def GetSelections(self):
        """Retourne le tuple des identifiants des éléments sélectionnés (compatibilité wxPython)."""
        return tuple(self.selection())

    def UnselectAll(self):
        """Désélectionne tous les éléments actuellement sélectionnés dans l'arbre."""
        # self.selection_remove(self.selection())
        selection = self.selection()
        if selection:
            self.selection_remove(*selection)

    def SelectItem(self, item, select=True):
        """Sélectionne ou désélectionne un élément spécifique de l'arbre."""
        if select:
            self.selection_add(item)
        else:
            self.selection_remove(item)


# MIXIN PRINCIPAL POUR DRAG-AND-DROP D'ARBORESCENCE

class TreeCtrlDragAndDropMixin(TreeHelperMixin):
    """Glisser-déposer interne d'un ``ttk.Treeview``.

    Mixin pour permettre le glisser-déposer d'éléments dans un Treeview Tkinter.
    Équivalent de TreeCtrlDragAndDropMixin de wxPython.

    La classe dérivée doit implémenter ``OnDrop(drop_item, drag_items, part,
    column)``. ``part`` vaut -1, 0 ou 1, comme dans la version wxPython.

    ``OnDrop(dropItem, dragItems, part, column)`` doit être redéfini.
    ``part`` vaut -1 (tiers supérieur), 0 (centre) ou 1 (tiers inférieur).
    ``dropItem == ''`` signifie la racine implicite.

    validateDrag(data_cible, liste_données_sources, colonne_source)
    peut renvoyer True, False ou None (validation par défaut).

    Le mixin ne modifie jamais l'arbre automatiquement : l'application est
    responsable de son modèle, de l'ordre des éléments et des rafraîchissements.

    Utilisation:
        class MyTree(TreeCtrlDragAndDropMixin, ttk.Treeview):
            def OnDrop(self, dropItem, dragItems, part, column):
                # Implémenter la logique de drop
                pass
    """
    # # Propriétés de glissement
    # dragged_items = []
    # drag_data_type = ""
    # drop_target = None
    # drop_position = None
    DRAG_THRESHOLD = 5
    HOVER_EXPAND_MS = 550

    # # def __init__(self, parent: tk.Widget, *args, **kwargs):
    # def __init__(
    #     self,
    #     *args: Any,
    #     validateDrag: Optional[Callable[[Any, List[Any], int], Optional[bool]]] = None,
    #     allow_root_drop: bool = True,
    #     hover_expand_delay: int = 500,
    #     dragAndDropCommand: Optional[Any] = None,
    #     **kwargs: Any,
    # ) -> None:
    def __init__(self, *args, **kwargs):
        """
        Initialise le mixin de drag-and-drop.

        Initialise le widget par la chaîne MRO puis installe les événements.

        Pour un widget déjà créé explicitement par ttk.Treeview.__init__,
        utiliser initialize_drag_support() plutôt que rappeler __init__.

        Args:
            *args:
            **kwargs: Peut contenir 'validateDrag' (callback de validation)
        """
        # parent: Widget parent
        # validateDrag:
        # allow_root_drop:
        # hover_expand_delay:
        # dragAndDropCommand:
        log.debug("TreeCtrlDragAndDropMixin.__init__: Initialisation")
        validate = kwargs.pop("validateDrag", None)
        command = kwargs.pop("dragAndDropCommand", None)
        allow_root = kwargs.pop("allow_root_drop", True)
        delay = kwargs.pop("hover_expand_delay", self.HOVER_EXPAND_MS)
        super().__init__(*args, **kwargs)
        self.initialize_drag_support(validateDrag=validate,
                                     dragAndDropCommand=command,
                                     allow_root_drop=allow_root,
                                     hover_expand_delay=delay)
        log.debug("TreeCtrlDragAndDropMixin initialisé !")

    # A conserver car important !
    # Son caractère idempotent évite de réinstaller les bindings
    # lors d'une deuxième initialisation.
    def initialize_drag_support(self, *, validateDrag=None,
                                dragAndDropCommand=None,
                                allow_root_drop=True,
                                hover_expand_delay=None):
        """Initialise uniquement l'état DnD et les liaisons d'un widget existant.

        N'appelle jamais ttk.Treeview.__init__ ni les autres constructeurs
        de mixins. La méthode est idempotente pour les bindings.
        """
        # # # Extraction du callback de validation
        # self._validateDragCallback = kwargs.pop('validateDrag', None)
        # # self._validateDragCallback = validateDrag
        # self._dragAndDropCommand = kwargs.pop('dragAndDropCommand', None)
        if getattr(self, "_drag_support_initialized", False):
            self._validateDragCallback = validateDrag
            self._dragAndDropCommand = dragAndDropCommand
            self.allow_root_drop = allow_root_drop
            return

        self._drag_support_initialized = True
        self._validateDragCallback = validateDrag
        self._dragAndDropCommand = dragAndDropCommand
        self.allow_root_drop = allow_root_drop
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
        # # self.drop_handler = None
        # self.drag_data: list[str]

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

        # Variables d'état du drag-and-drop
        # # self.allow_root_drop = allow_root_drop
        # self.allow_root_drop = kwargs.pop('allow_root_drop', None)
        # # self._hover_expand_delay = hover_expand_delay
        # self._hover_expand_delay = kwargs.pop('_hover_expand_delay', None)
        self._hover_expand_delay = (self.HOVER_EXPAND_MS if hover_expand_delay is None
                                    else hover_expand_delay)
        # self._item_to_object: dict[str, Any] = {}
        # self._dragItems = []
        self._dragItems: List[str] = []
        # # self.dragged_items = []
        # self.dragged_items: List[str] = []
        self.dragged_items: List[str] = self._dragItems
        # self._dragStartPos = None
        self._dragStartPos: Optional[Tuple[int, int]] = None
        # self._dragColumn = -1
        self._dragColumn = 0
        # # self.drop_handler = None
        # self.drag_data: list[str]
        # self.drag_data = []
        self._dragActive = False

        # self.drop_target = None
        self.drop_target: Optional[str] = None
        # self.drop_position = None
        self.drop_position: Optional[str] = None
        self._dropItem = ""
        self._dropPart = 0
        self._dropColumn = 0

        self._hoverExpandItem: Optional[str] = None  # ?
        self._hoverExpandTimer: Optional[str] = None  # ?
        self._hoverItem = None
        self._hoverAfter = None
        self._oldCursor = None

        # super().__init__(*args, **kwargs)
        # Note: Les bindings étaient/sont faits dans TreeListCtrl._bind_events()
        # pour éviter les conflits d'ordre d'initialisation
        self._bind_drag_events()
        # log.debug("TreeCtrlDragAndDropMixin initialisé !")

    def _bind_drag_events(self) -> None:
        """Associe les liaisons d'événements souris et clavier nécessaires au glisser-déposer."""
        # Note: Les bindings étaient/sont faits dans TreeListCtrl._bind_events()
        # pour éviter les conflits d'ordre d'initialisation
        # self.bind("<ButtonPress-1>", self.on_start_drag, add="+")
        self.bind("<ButtonPress-1>", self._on_press, add="+")
        # self.bind("<B1-Motion>", self.on_dragging, add="+")
        self.bind("<B1-Motion>", self._on_motion, add="+")
        # self.bind("<ButtonRelease-1>", self.on_end_drag, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        # self.bind("<Escape>", self.cancel_drag, add="+")
        self.bind("<Escape>", self._on_escape, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")

    # MÉTHODES PUBLIQUES À SURCHARGER
    def OnDrop(self, drop_item: str, dragged_items: List[str],
               part: int, column: int) -> Any:
        """
        Cette méthode DOIT être surchargée dans la classe dérivée.

        À implémenter dans la classe concrète (mise à jour du modèle).

        Args:
            drop_item: Item sur lequel on drop (ou "" pour racine)
            drag_items: Liste des items glissés.
            part: Position (-1=au-dessus, 0=sur, 1=en-dessous)
            column: Index de la colonne
        """
        # chaque classe qui hérite de TreeCtrlDragAndDropMixin
        # doit fournir sa propre implémentation de OnDrop.
        raise NotImplementedError(
            "La méthode OnDrop doit être implémentée par la classe dérivée."
        )

    def _on_press(self, event):
        """Enregistre la position initiale, la colonne et l'élément sous le clic gauche."""
        if self._dragActive:
            self.StopDragging()
        self._dragStartPos = (event.x, event.y)
        self._dragColumn = self._column_at(event.x)
        self._pressItem = self.identify_row(event.y) or ""
        log.debug(
            "TreeCtrlDragAndDropMixin._on_press: clic gauche sur la position %s, l'élément %s de la colonne %s",
            self._dragStartPos,
            self._pressItem,
            self._dragColumn,
        )

    def _on_motion(self, event):
        """Détecte le franchissement du seuil de déplacement pour déclencher le glissement."""
        if self._dragStartPos is None:
            log.debug("TreeCtrlDragAndDropMixin._on_motion : position %s = None", self._dragStartPos)
            return
        log.debug("TreeCtrlDragAndDropMixin._on_motion : position %s commence à se déplacer.", self._dragStartPos)
        if not self._dragActive:
            dx = abs(event.x - self._dragStartPos[0])
            dy = abs(event.y - self._dragStartPos[1])
            if max(dx, dy) < self.DRAG_THRESHOLD:
                return
            if not self._begin_drag():
                self._dragStartPos = None
                return
        self.OnDragging(event)
        # return

    def _begin_drag(self):
        """Initialise l'opération de glissement en filtrant les éléments descendants sélectionnés."""
        if not self._pressItem or not self.exists(self._pressItem):
            return False
        log.debug("TreeCtrlDragAndDropMixin._begin_drag : initialisation du glissement des éléments %s", self._pressItem)
        selected = tuple(self.selection())
        if self._pressItem not in selected:
            selected = (self._pressItem,)
        # Ne pas déplacer simultanément un parent et ses descendants.
        selected_set = set(selected)
        # self._dragItems = [item for item in selected if not any(
        items = [item for item in selected if not any(
            ancestor in selected_set for ancestor in self._ancestors(item))]
        # if not self._dragItems:
        if not items:
            return False
        self._dragItems = items
        self.dragged_items = self._dragItems
        self._dragActive = True
        self.SetCursorToDragging()
        return True

    def OnBeginDrag(self, event: Any) -> None:
        """Démarre le glisser (méthode de compatibilité wxPython)."""
        log.debug("TreeCtrlDragAndDropMixin.OnBeginDrag : démarre le glissement façon wxPython !")
        self.on_start_drag(event)

    # def OnDragging(self, event: Any) -> None:
    #     self.on_dragging(event)

    def OnEndDrag(self, event: Any) -> None:
        """Termine le glisser (méthode de compatibilité wxPython)."""
        log.debug("TreeCtrlDragAndDropMixin.OnEndDrag : termine le glissement façon wxPython !")
        self.on_end_drag(event)

    # ========================================================================
    # MÉTHODES UTILITAIRES PRIVÉES
    # ========================================================================
    def _column_at(self, x):
        """Retourne l'indice numérique de la colonne correspondant à la coordonnée horizontale x."""
        # TODO : A REVOIR !
        column = self.identify_column(x)
        log.debug("TreeCtrlDragAndDropMixin._column_at : essaie de retourner l'indice numérique de la colonne %s", column)
        try:
            return int(column[1:]) if column.startswith("#") else 0
        except (TypeError, ValueError, AttributeError):
            return 0

    def _get_column_index(self, x: int) -> int:
        """Retourne l'index de la colonne à la position x."""
        # return self._column_at(x)
        column_id = self.identify_column(x)
        log.debug("TreeCtrlDragAndDropMixin._get_column_index : essaye de retourner l'index de la colonne %s à la position %s : int(%s) !", column_id, x, column_id[1:])
        # if column_id == '#0':
        if column_id in ("", "#0"):
            return 0
        try:
            # column_id est du type "#1", "#2", etc. ?
            log.debug("TreeCtrlDragAndDropMixin._get_column_index : essaye de retourner l'index de la colonne %s à la position %s : int(%s) !", column_id, x, column_id[1:])
            log.debug("TreeCtrlDragAndDropMixin._get_column_index : serait-ce mieux ? int(%s) !", column_id.replace('#', ''))
            return int(column_id[1:])
            return int(column_id.replace('#', ''))
        except (ValueError, IndexError, AttributeError):
            return 0

    @staticmethod
    def _position_to_int(position: Optional[str]) -> int:
        """
        Convertit une position string en int pour compatibilité wxPython.

        Returns:
            -1 (above), 0 (on), 1 (below)
        """
        return {"above": -1, "on": 0, "below": 1}.get(position, 0)

    # def _position_to_int(self, position: Optional[str]) -> int:
    #     """
    #     Convertit une position string en int pour compatibilité wxPython.
    #
    #     Returns:
    #         -1 (above), 0 (on), 1 (below)
    #     """
    #     if position == "above":
    #         return -1
    #     elif position == "below":
    #         return 1
    #     else:
    #         return 0

    def _target_at(self, x: int, y: int) -> Tuple[str, Optional[str]]:
        """Identifie l'élément cible et la subdivision ('above', 'on', 'below') aux coordonnées (x, y)."""
        item = self.identify_row(y) or ""
        if not item:
            log.debug("TreeCtrlDragAndDropMixin._target_at : aucun élément identifié à la position (%s, %s)", x, y)
            return "", None
        bbox = self.bbox(item)
        if not bbox or bbox[3] <= 0:
            log.debug("TreeCtrlDragAndDropMixin._target_at : bbox invalide pour l'élément %s à la position (%s, %s)", item, x, y)
            return item, "on"
        relative_y = y - bbox[1]
        height = bbox[3]
        if relative_y < height / 3:
            position = "above"
        elif relative_y > 2 * height / 3:
            position = "below"
        else:
            position = "on"
        log.debug("TreeCtrlDragAndDropMixin._target_at : élément %s identifié à la position (%s, %s) avec subdivision '%s'", item, x, y, position)
        return item, position

    # def _target_at(self, x, y):
    #     class Position:
    #         pass
    #     event = Position()
    #     event.x, event.y = x, y
    #     item, part, _ = self._hit_drop(event)
    #     return item, {-1: "above", 0: "on", 1: "below"}[part] if item else None

    def _ancestors(self, item):
        """Générateur retournant successivement tous les ancêtres d'un élément jusqu'à la racine."""
        parent = self.parent(item)
        while parent:
            yield parent
            parent = self.parent(parent)

    def _hit_drop(self, event):
        """Détermine l'item sous le pointeur, la zone d'insertion (-1, 0, 1) et l'indice de colonne."""
        item = self.identify_row(event.y) or ""
        column = self._column_at(event.x)
        part = 0
        if item:
            box = self.bbox(item)
            if box and box[3] > 0:
                fraction = (event.y - box[1]) / box[3]
                part = -1 if fraction < 1 / 3 else (1 if fraction > 2 / 3 else 0)
        log.debug("TreeCtrlDragAndDropMixin._hit_drop : retourne item=%s, part=%s, column=%s sous le pointeur !", item, part, column)
        return item, part, column

    # GESTION DU DÉBUT DU DRAG
    def on_start_drag(self, event):
        """
        Appelé au début du glissement (ButtonPress-1).
        Équivalent de OnBeginDrag de wxPython.
        """
        item = self.identify_row(event.y)
        log.info(
            "TreeCtrlDragAndDropMixin.on_start_drag : DRAG START : item=%r, x=%s, y=%s, region=%r, element=%r",
            item,
            event.x,
            event.y,
            self.identify_region(event.x, event.y),
            self.identify_element(event.x, event.y),
        )
        self._dragStartPos = (event.x, event.y)
        self._dragColumn = self._get_column_index(event.x)
        if not item:
            self.dragged_items = []
            log.debug("TreeCtrlDragAndDropMixin.on_start_drag : aucun élément identifié sous le pointeur, drag annulé.")
            return

        # if item:
        #     self.dragged_items = list(self.selection()) if self.selection() else [item]
        #     if not self.dragged_items or "" in self.dragged_items:  # Empêche de glisser l'élément racine
        #         self.dragged_items = []
        #         return
        #     # dnd.dnd_start(self, event)
        # Récupérer la sélection ou l'item cliqué
        # selections = self.selection()
        selected = list(self.selection())
        # self.dragged_items = list(selections) if selections else [item]
        self.dragged_items = selected if item in selected else [item]

        # Ne pas permettre de glisser la racine
        if "" in self.dragged_items:
            # self.dragged_items = []
            self.cancel_drag()
            log.debug("TreeCtrlDragAndDropMixin.on_start_drag : tentative de glisser la racine, drag annulé.")
            return

        # # Identifier la colonne
        # self._dragColumn = self._get_column_index(event.x)
        # self._dragStartPos = (event.x, event.y)
        #
        # # Stocke les données à glisser pour le module dnd
        # self.drag_data = self.dragged_items
        # self._dragItems = self.dragged_items[:]
        # # self.dnd_enter(None, event)
        #
        # dnd.dnd_start(self, event)
        self._dragItems = list(self.dragged_items)
        # self._on_press(event)
        log.debug(f"TreeCtrlDragAndDropMixin.on_start_drag: Début drag: {len(self.dragged_items)} items")

    # GESTION DU MOUVEMENT

    def on_dragging(self, event):
        """
        Appelé pendant le glissement (B1-Motion).
        Gère le curseur et la visualisation.
        """
        if not self.dragged_items:
            log.debug("TreeCtrlDragAndDropMixin.on_dragging : aucun élément à glisser, retour.")
            return

        # x, y = event.x, event.y
        if self._dragStartPos is not None:
            dx = abs(event.x - self._dragStartPos[0])
            dy = abs(event.y - self._dragStartPos[1])
            if dx < 3 and dy < 3:
                log.debug("TreeCtrlDragAndDropMixin.on_dragging : déplacement trop faible (%s, %s), retour.", dx, dy)
                return
        target, position = self._target_at(event.x, event.y)
        # self.drop_target = self.identify_row(y)
        self.drop_target = target
        self.drop_position = position

        # Déterminer la position relative (above/on/below)
        # # Logique pour déterminer la position (sur, au-dessus, en-dessous)
        # if self.drop_target:
        #     item_bbox = self.bbox(self.drop_target)
        #     if item_bbox:
        #         item_height = item_bbox[3]
        #         rel_y = y - item_bbox[1]
        #         if rel_y < item_height / 3:
        #             self.drop_position = "above"
        #         elif rel_y > 2 * item_height / 3:
        #             self.drop_position = "below"
        #         else:
        #             self.drop_position = "on"

            # Gère le curseur et la sélection
            # Changer le curseur selon la validité du drop
            # if self.is_valid_drop_target(self.drop_target):
        # if self.is_valid_drop_target(target):
        if self.IsValidDropTarget(target):
            # # self.config(cursor="hand2")
            # self.config(cursor="hand1")
            self._set_cursor_dragging()
            self._schedule_hover_expand(target)
        else:
            # # self.config(cursor="no")
            # # self.config(cursor="no_drop")  # Correction ici
            # self.config(cursor="no_entry")  # Correction ici
            self._set_cursor_no_drop()
            self._cancel_hover_expand()
        # else:
        #     self.config(cursor="")
        #     self.drop_target = None
        #     self.drop_position = None
        # self._on_motion(event)
        log.debug("TreeCtrlDragAndDropMixin.on_dragging : drag en cours sur l'élément %s à la position %s !", target, position)

    def OnDragging(self, event):
        """Met à jour le curseur, le retour visuel et le minuteur d'auto-dépliage pendant le glissement."""
        if not self._dragActive:
            log.debug("TreeCtrlDragAndDropMixin.OnDragging : drag non actif, retour.")
            return
        item, part, column = self._hit_drop(event)
        self._dropItem, self._dropPart, self._dropColumn = item, part, column
        valid = self.IsValidDropTarget(item)
        self._set_cursor("hand2" if valid else "X_cursor")
        self._schedule_expand(item if valid else "")
        self._UpdateDropFeedback(item if valid else "", part, column)
        log.debug("TreeCtrlDragAndDropMixin.OnDragging : drag en cours sur l'élément %s, part=%s, colonne=%s, valid=%s", item, part, column, valid)

    # GESTION DE LA FIN DU DRAG
    def on_end_drag(self, event):
        """
        Appelé à la fin du glissement (ButtonRelease-1).
        Effectue le drop si valide.
        """
        # self.config(cursor="")
        if not self.dragged_items:
            log.debug("TreeCtrlDragAndDropMixin.on_end_drag : aucun élément à glisser, retour.")
            return

        # drop_target = self.drop_target if self.drop_target else ""
        target, position = self._target_at(event.x, event.y)
        valid = self.is_valid_drop_target(target)
        items = list(self.dragged_items)
        column = self._get_column_index(event.x)
        self._reset_drag_state()

        # # if self.drop_target and self.is_valid_drop_target(self.drop_target):
        # #     self.OnDrop(self.drop_target, self.dragged_items, self.drop_position)
        # if self.is_valid_drop_target(drop_target):
        if valid:
            # # Convertir position string en int pour wxPython compatibility
            # part = self._position_to_int(self.drop_position)

            # Appeler la méthode à surcharger
            # self.OnDrop(drop_target, self.dragged_items, part, self._dragColumn)
            self.OnDrop(target, items, self._position_to_int(position), column)
        else:
            self._restore_selection(items)
        # # Réinitialiser l'état
        # self.dragged_items = []
        # self.drop_target = None
        # self.drop_position = None
        # self._dragItems = []
        # self._on_release(event)
        log.debug("TreeCtrlDragAndDropMixin.on_end_drag : drag terminé sur l'élément %s à la position %s, valid=%s, items=%s", target, position, valid, items)

    def cancel_drag(self, event: Any = None) -> str:
        """Annule le glissement en cours, réinitialise l'état et restaure la sélection précédente."""
        log.debug("TreeCtrlDragAndDropMixin.cancel_drag : annulation du glissement en cours.")
        if self.dragged_items:
            self._restore_selection(self.dragged_items)
        self._reset_drag_state()
        # self.StopDragging()
        log.debug("TreeCtrlDragAndDropMixin.cancel_drag : glissement annulé, état réinitialisé !")
        return "break"

    def _reset_drag_state(self) -> None:
        """Réinitialise toutes les variables internes de glissement et le curseur du widget."""
        log.debug("TreeCtrlDragAndDropMixin._reset_drag_state : réinitialisation de l'état de glissement.")
        self._cancel_hover_expand()
        try:
            self.configure(cursor="")
        except tk.TclError:
            pass
        self.dragged_items = []
        self._dragItems = []
        self.drop_target = None
        self.drop_position = None
        self._dragStartPos = None
        log.debug("TreeCtrlDragAndDropMixin._reset_drag_state : état de glissement réinitialisé !")

    def _restore_selection(self, items: Iterable[str]) -> None:
        """Restaure la sélection sur les éléments fournis qui existent encore dans l'arbre."""
        valid = [item for item in items if self.exists(item)]
        if valid:
            self.selection_set(*valid)

    # def _set_cursor(self, *cursor_names: str) -> None:
    def _set_cursor(self, *cursor: str) -> None:
        """Applique le premier curseur accepté par Tk sur la plateforme."""
        log.debug("TreeCtrlDragAndDropMixin._set_cursor : tentative de configuration du curseur avec les options %s", cursor)
        # for cursor_name in cursor_names:
        #     try:
        #         self.configure(cursor=cursor_name)
        #         return
        #     except tk.TclError:
        #         continue
        try:
            if self._oldCursor is None:
                self._oldCursor = self.cget("cursor")
            # self.configure(cursor=cursor)
            for candidate in (cursor, "arrow"):
                try:
                    self.configure(cursor=candidate)
                    log.debug("TreeCtrlDragAndDropMixin._set_cursor : curseur configuré sur '%s' !", candidate)
                    return
                except tk.TclError:
                    continue
        except tk.TclError:
            log.debug("TreeCtrlDragAndDropMixin._set_cursor : Curseur indisponible : %s", cursor)
        # # Aucun curseur spécialisé n'est disponible. Le curseur vide demande
        # # à Tk de reprendre le curseur par défaut du widget, sans provoquer
        # # d'exception dans le callback Tkinter.
        # try:
        #     self.configure(cursor="")
        # except tk.TclError:
        #     pass

    def _set_cursor_dragging(self) -> None:
        """Change le curseur pour indiquer un drag autorisé."""
        # try:
        #     self.config(cursor="hand1")
        # except tk.TclError:
        #     self.config(cursor="hand2")
        self._set_cursor("hand2", "hand", "arrow")
        # self.SetCursorToDragging()

    def _set_cursor_no_drop(self) -> None:
        """Change le curseur pour indiquer un drop interdit."""
        # Le nom X11 "no" n'est pas disponible sur toutes les plateformes.
        # "cross" et "pirate" sont des solutions de repli visuelles, puis
        # le curseur standard si aucun nom n'est accepté.
        # try:
        #     self.config(cursor="notallowed")
        # except tk.TclError:
        #     try:
        #         self.config(cursor="pirate")
        #     except tk.TclError:
        #         self.config(cursor="circle")
        self._set_cursor("not-allowed", "cross", "pirate", "arrow")
        # self.SetCursorToDroppingImpossible()

    def SetCursorToDragging(self) -> None:
        """Définit le curseur de souris indiquant un déplacement autorisé."""
        # self._set_cursor_dragging()
        self._set_cursor("hand2")

    def SetCursorToLink(self) -> None:
        """Définit le curseur de liaison (survol des colonnes de prérequis / dépendances)."""
        # self._set_cursor("hand2", "hand", "arrow")
        self._set_cursor("hand2")

    def SetCursorToHome(self) -> None:
        """Définit le curseur indiquant un dépôt vers la racine (élément de niveau supérieur)."""
        # self._set_cursor("based_arrow_down", "bottom_side", "arrow")
        self._set_cursor("hand2")

    def SetCursorToDroppingImpossible(self) -> None:
        """Définit le curseur d'interdiction signalant que le dépôt n'est pas autorisé."""
        # self._set_cursor_no_drop()
        self._set_cursor("X_cursor")

    def ResetCursor(self) -> None:
        """Restaure le curseur par défaut qui était en place avant le glisser-déposer."""
        # self._set_cursor("")
        if self._oldCursor is not None:
            try:
                self.configure(cursor=self._oldCursor)
                log.debug("TreeCtrlDragAndDropMixin.ResetCursor : curseur restauré sur '%s' !", self._oldCursor)
            except tk.TclError:
                pass
            self._oldCursor = None

    def _ResetHeaderCursor(self):
        """Restaure le curseur d'en-tête (compatibilité wx)."""
        self.ResetCursor()

    # def _schedule_hover_expand(self, item: str) -> None:
    #     if not item or not self.exists(item) or self.item(item, "open"):
    #         self._cancel_hover_expand()
    #         return
    #     if self._hoverExpandItem == item and self._hoverExpandTimer is not None:
    #         return
    #     self._cancel_hover_expand()
    #     self._hoverExpandItem = item
    #     self._hoverExpandTimer = self.after(self._hover_expand_delay, self._expand_hovered)

    def _schedule_expand(self, item: str) -> None:
        """Planifie le déploiement automatique d'un nœud fermé après un délai de survol."""
        log.debug("TreeCtrlDragAndDropMixin._schedule_expand : planification du déploiement automatique pour l'élément %s", item)
        if item == self._hoverItem:
            return
        self._cancel_expand()
        self._hoverItem = item
        if item and self.exists(item) and self.get_children(item):
            try:
                is_open = self.tk.getboolean(self.item(item, "open"))
            except (ValueError, tk.TclError):
                # is_open = bool(self.item(item, "open"))
                is_open = self.item(item, "open") in (True, 1, "1")
            if not is_open:
                self._hoverAfter = self.after(self.HOVER_EXPAND_MS,
                                               lambda: self._expand_hover(item))
        log.debug("TreeCtrlDragAndDropMixin._schedule_expand : minuteur d'auto-dépliage planifié pour l'élément %s !", item)

    # def _cancel_hover_expand(self) -> None:
    def _cancel_expand(self) -> None:
        """Annule le minuteur d'auto-dépliage en cours."""
        log.debug("TreeCtrlDragAndDropMixin._cancel_expand : annulation du minuteur d'auto-dépliage pour l'élément %s", self._hoverItem)
        # if self._hoverExpandTimer is not None:
        if self._hoverAfter is not None:
            try:
                # self.after_cancel(self._hoverExpandTimer)
                self.after_cancel(self._hoverAfter)
            except tk.TclError:
                pass
        self._hoverAfter = None
        # self._hoverExpandTimer = None
        # self._hoverExpandItem = None
        self._hoverItem = None
        log.debug("TreeCtrlDragAndDropMixin._cancel_expand : minuteur d'auto-dépliage annulé !")

    # def _expand_hovered(self) -> None:
    def _expand_hover(self, item) -> None:
        """Ouvre le nœud survolé lorsque le délai d'attente est expiré."""
        log.debug("TreeCtrlDragAndDropMixin._expand_hover : tentative d'ouverture de l'élément %s après le délai de survol.", item)
        # item = self._hoverExpandItem
        # self._hoverExpandTimer = None
        self._hoverAfter = None
        # if item and self.exists(item) and not self.item(item, "open") and self.is_valid_drop_target(item):
        if self._dragActive and self._hoverItem == item and self.exists(item):
            self.item(item, open=True)
        # self._hoverExpandItem = None
        log.debug("TreeCtrlDragAndDropMixin._expand_hover : élément %s ouvert après le délai de survol !", item)

    def _UpdateDropFeedback(self, item, part, column):
        """Point d'extension : dessiner une indication de dépôt si souhaité."""

    def _ClearDropFeedback(self):
        """Point d'extension : supprimer l'indication de dépôt."""

    def _on_release(self, event):
        """Gère le relâchement du bouton gauche pour effectuer le dépôt s'il est valide."""
        log.debug("TreeCtrlDragAndDropMixin._on_release : relâchement du bouton gauche à la position (%s, %s)", event.x, event.y)
        if not self._dragActive:
            self._dragStartPos = None
            return
        # Recalcul indispensable : la souris a pu bouger depuis le dernier Motion.
        item, part, column = self._hit_drop(event)
        valid = self.IsValidDropTarget(item)
        dragged = tuple(self._dragItems)
        self.StopDragging()
        if valid:
            log.debug("TreeCtrlDragAndDropMixin._on_release : dépôt valide pour l'élément %s", item)
            self.OnDrop(item, list(dragged), part, column)

    def _on_escape(self, event):
        """Intercepte la touche Échap pour annuler le glissement."""
        log.debug("TreeCtrlDragAndDropMixin._on_escape : touche Échap pressée")
        if self._dragActive:
            self.StopDragging()
            return "break"
        return None

    def _on_destroy(self, event):
        """Nettoie les minuteurs planifiés lors de la destruction du widget."""
        log.debug("TreeCtrlDragAndDropMixin._on_destroy : widget détruit, nettoyage des minuteurs !")
        if event.widget is self:
            self._cancel_expand()
    # VALIDATION DU DROP
    # def is_valid_drop_target(self, drop_target: str) -> bool:
    #     """
    #     Vérifie si un drop est valide.
    #
    #     Args:
    #         dropTarget: Item cible ("" = racine OK)
    #
    #     Returns:
    #         True si le drop est autorisé
    #     """
    #     if not self.dragged_items:
    #         return False
    #     # Si callback personnalisé fourni
    #     # if not drop_target:
    #     if drop_target is None:
    #         return False
    #     if drop_target == "":
    #         default = self.allow_root_drop
    #     elif not self.exists(drop_target):
    #         return False
    #     else:
    #         default = True
    #     if drop_target in self.dragged_items:
    #         default = False
    #     for item in self.dragged_items:
    #         if drop_target in self.GetItemChildren(item, recursively=True):
    #             default = False
    #     # # Empêcher de glisser un parent sur un enfant
    #     # for dragged_item in self.dragged_items:
    #     #     current_item = drop_target
    #     #     while current_item:
    #     #         if current_item == dragged_item:
    #     #             return False
    #     #         current_item = self.parent(current_item)
    #     #
    #     # # Empêcher de glisser un élément sur lui-même ou sur un de ses enfants
    #     # if drop_target in self.dragged_items or drop_target in self.GetItemChildren(self.dragged_items, recursively=True):
    #     #     return False
    #     #
    #     # return True
    #
    #     if self._validateDragCallback is not None:
    #         drop_data = self.GetItemPyData(drop_target) if drop_target else None
    #         # drag_data_list = [
    #         drag_data = [
    #             self.GetItemPyData(item) for item in self.dragged_items
    #         ]
    #
    #         result = self._validateDragCallback(
    #             # drop_data, drag_data_list, self._dragColumn
    #             drop_data, drag_data, self._dragColumn
    #         )
    #         if result is not None:
    #             # return result
    #             return bool(result)
    #
    #     # Validation par défaut
    #     # if not self.dragged_items:
    #     #     return False
    #     #
    #     # # Construire l'ensemble des cibles invalides
    #     # invalid_targets = set(self.dragged_items)
    #     #
    #     # # Ajouter les parents des items glissés
    #     # for item in self.dragged_items:
    #     #     parent = self.GetItemParent(item)
    #     #     if parent:
    #     #         invalid_targets.add(parent)
    #     #
    #     # # Ajouter tous les descendants des items glissés
    #     # for item in self.dragged_items:
    #     #     descendants = self.GetItemChildren(item, recursively=True)
    #     #     invalid_targets.update(descendants)
    #     #
    #     # # Le drop est valide si la cible n'est pas dans les invalides
    #     # return drop_target not in invalid_targets
    #     return default
    #
    # def IsValidDropTarget(self, drop_target: Optional[str]) -> bool:
    #     return self.is_valid_drop_target(drop_target)

    # A conserver car important !
    # L'interdiction des déplacements crée un cycle dans l'arborescence.
    def IsValidDropTarget(self, dropTarget: str) -> bool:
        """Valide une cible et appelle le callback historique si fourni.

        Vérifie les cycles et la validation métier, y compris sur la racine.
        """
        log.debug("TreeCtrlDragAndDropMixin.IsValidDropTarget : vérification de la validité du drop sur l'élément %s", dropTarget)
        if not self._dragItems:
            log.debug("TreeCtrlDragAndDropMixin.IsValidDropTarget : aucun élément en cours de glissement, drop non valide.")
            return False
        if not dropTarget:
            default_valid = bool(self.allow_root_drop)
        else:
            default_valid = (
                self.exists(dropTarget)
                and dropTarget not in self._dragItems
                and all(dropTarget not in self.GetItemChildren(item, True)
                        for item in self._dragItems)
                and all(dropTarget != self.parent(item) for item in self._dragItems)
            )
        # Ne jamais autoriser un cycle même si le callback retourne True.
        if dropTarget and any(
            dropTarget == item or dropTarget in self.GetItemChildren(item, True)
            for item in self._dragItems
        ):
            log.debug("TreeCtrlDragAndDropMixin.IsValidDropTarget : drop sur l'élément %s interdit car il créerait un cycle avec les éléments glissés %s", dropTarget, self._dragItems)
            return False
        if self._validateDragCallback is not None:
            value = self._validateDragCallback(
                self.GetItemPyData(dropTarget),
                [self.GetItemPyData(item) for item in self._dragItems],
                self._dragColumn,
            )
            if value is not None:
                log.debug("TreeCtrlDragAndDropMixin.IsValidDropTarget : validité du drop sur l'élément %s selon le callback = %s", dropTarget, value)
                return bool(value)
        # if not dropTarget:
        #     return True
        # if dropTarget in self._dragItems:
        #     return False
        # if any(dropTarget in self.GetItemChildren(item, True)
        #        for item in self._dragItems):
        #     return False
        # # Fidélité à wx : pas de dépôt sur le parent actuel.
        # if any(dropTarget == self.parent(item) for item in self._dragItems):
        #     return False
        # return True
        log.debug("TreeCtrlDragAndDropMixin.IsValidDropTarget : validité par défaut du drop sur l'élément %s = %s", dropTarget, default_valid)
        return default_valid

    # ========================================================================
    # MÉTHODES DE COMPATIBILITÉ AVEC WXPYTHON
    # ========================================================================
    # def GetSelections(self) -> tuple:
    def GetSelections(self) -> List[str]:
        """Retourne les items sélectionnés (compatibilité wxPython)."""
        log.debug("TreeCtrlDragAndDropMixin.GetSelections : récupération des éléments sélectionnés.")
        # return self.selection()
        return list(self.selection())

    def UnselectAll(self) -> None:
        """Désélectionne tous les items."""
        log.debug("TreeCtrlDragAndDropMixin.UnselectAll : désélection de tous les éléments.")
        # for item in self.selection():
        #     self.selection_remove(item)
        selected = self.selection()
        if selected:
            self.selection_remove(*selected)

    def SelectItem(self, item: str) -> None:
        """Sélectionne un item."""
        log.debug("TreeCtrlDragAndDropMixin.SelectItem : sélection de l'élément %s", item)
        if item:
            self.selection_set(item)

    def selectDraggedItems(self):
        """Sélectionne à nouveau les éléments qui étaient en cours de déplacement."""
        log.debug("TreeCtrlDragAndDropMixin.selectDraggedItems : sélection des éléments en cours de déplacement.")
        if self._dragItems:
            self.selection_set(self._dragItems)

    def OnKeyDuringDrag(self, event: Any) -> str:
        """Intercepte les appuis clavier pendant le glissement pour annuler sur Échap."""
        log.debug("TreeCtrlDragAndDropMixin.OnKeyDuringDrag : touche pressée pendant le glissement.")
        if getattr(event, "keysym", "") == "Escape":
            return self._on_escape(event)
        return None
        # return self.cancel_drag(event) if event.keysym == "Escape" else "continue"
        return self.cancel_drag(event) if getattr(event, "keysym", "") == "Escape" else None

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

    # Hooks conservés pour les adaptations existantes.
    def StartDragging(self) -> None:
        """Démarre le déplacement à partir de la sélection actuelle."""
        log.debug("TreeCtrlDragAndDropMixin.StartDragging : démarrage du glissement à partir de la sélection actuelle.")
        self._dragItems = list(self.selection())
        self.dragged_items = self._dragItems
        self._dragActive = bool(self._dragItems)
        if self._dragActive:
            self.SetCursorToDragging()
        log.debug("TreeCtrlDragAndDropMixin.StartDragging : glissement démarré avec %d éléments.", len(self._dragItems))
        # return None

    def StopDragging(self) -> None:
        """Arrête l'opération de glissement, masque les retours visuels et réinitialise l'état."""
        log.debug("TreeCtrlDragAndDropMixin.StopDragging : arrêt du glissement.")
        # self._reset_drag_state()
        self._cancel_expand()
        self._ClearDropFeedback()
        self._dragActive = False
        self._dragStartPos = None
        self._dragItems = []
        self.dragged_items = self._dragItems
        self.drop_target, self.drop_position = None, None
        self.ResetCursor()
        log.debug("TreeCtrlDragAndDropMixin.StopDragging : glissement arrêté, état réinitialisé !")

    def _isPrereqOrDepColumn(self, column: int) -> bool:
        """Indique si la colonne donnée correspond aux colonnes 'prerequisites' ou 'dependencies'."""
        log.debug("TreeCtrlDragAndDropMixin._isPrereqOrDepColumn : vérification de la colonne %s", column)
        # if column < 0:
        if column < 0 or not hasattr(self, "_getColumn"):
            log.debug("TreeCtrlDragAndDropMixin._isPrereqOrDepColumn : colonne invalide ou méthode _getColumn manquante, retour False.")
            return False
        # if hasattr(self, "_getColumn"):
        try:
            col = self._getColumn(column)
            name = col.name() if callable(getattr(col, "name", None)) else getattr(col, "name", "")
            log.debug("TreeCtrlDragAndDropMixin._isPrereqOrDepColumn : nom de la colonne %s = %s", column, name)
            return name in ("prerequisites", "dependencies")
        except (AttributeError, IndexError, TypeError):
            log.debug("TreeCtrlDragAndDropMixin._isPrereqOrDepColumn : erreur lors de la vérification de la colonne %s", column)
            # pass
            return False
        # return False

    def OnDraggingOverHeader(self, event: Any) -> None:
        """Extension optionnelle ; ttk.Treeview n'a pas d'API wx d'en-tête."""
        return None

    def OnDropOnHeader(self, event: Any) -> None:
        """Extension optionnelle ; non appelée par défaut."""
        return None


# --- Exemple d'utilisation (pour démonstration) ---
if __name__ == "__main__":
    # # from tkinter import ttk
    # logging.basicConfig(level=logging.DEBUG)
    #
    # def on_drop_url(url):
    #     print(f"URL/Texte lâché : {url}")
    #
    # def on_drop_file(filenames):
    #     # print("Fichiers lâchés :")
    #     # for f in filenames:
    #     #     print(f)
    #     print(f"Fichiers lâchés : {filenames}")
    #
    # def on_drop_text(text):
    #     print(f"Texte lâché : {text}")

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
        """Arbre de test avec drag-and-drop."""

        # def __init__(self, parent):
        #     ttk.Treeview.__init__(self, parent, columns=('col1',), show='tree')
        #     TreeCtrlDragAndDropMixin.__init__(self, parent)
        #
        #     # Binding des événements
        #     self.bind("<ButtonPress-1>", self.on_start_drag)
        #     self.bind("<B1-Motion>", self.on_dragging)
        #     self.bind("<ButtonRelease-1>", self.on_end_drag)
        #
        #     # Peuplement
        #     self._populate()
        #
        # def _populate(self):
        #     """Ajoute des éléments de test."""
        #     p1 = self.insert("", "end", text="Projet A", open=True)
        #     self.SetItemPyData(p1, {"name": "Projet A"})
        #
        #     t1 = self.insert(p1, "end", text="Tâche 1")
        #     self.SetItemPyData(t1, {"name": "Tâche 1"})
        #
        #     t2 = self.insert(p1, "end", text="Tâche 2")
        #     self.SetItemPyData(t2, {"name": "Tâche 2"})
        #
        #     p2 = self.insert("", "end", text="Projet B")
        #     self.SetItemPyData(p2, {"name": "Projet B"})

        def OnDrop(self, drop_item, dragged_items, part, column):
            """Implémentation du drop."""
            # print(f"Éléments glissés: {dragged_items} sur {drop_item} à la position: {part}")
            print(f"\nDrop:")
            print(f"  Items glissés: {[self.item(i, 'text') for i in dragged_items]}")
            print(f"  Cible: {self.item(drop_item, 'text') if drop_item else 'Racine'}")
            print(f"  Position: {['above', 'on', 'below'][part+1]}")

            # Exemple de déplacement simple des items
            for item in dragged_items:
                # # if part == "on":
                # if part == 0:  # Sur l'item
                #     # Déplacer l'élément pour qu'il devienne un enfant
                #     self.move(item, drop_item, "end")
                # else:
                #     # Déplacer l'élément au-dessus ou en-dessous
                #     parent = self.parent(drop_item) if drop_item else ""
                #     index = self.index(drop_item)
                #     # if part == "below":
                #     if part == 1:  # Below
                #         index += 1
                #     # self.move(item, self.parent(drop_item), index)
                #     self.move(item, parent, index)
                if drop_item and (item == drop_item or drop_item in self.GetItemChildren(item, True)):
                    continue
                parent = self.parent(drop_item) if part != 0 and drop_item else drop_item
                siblings = list(self.get_children(parent))
                index = siblings.index(drop_item) + (part == 1) if part != 0 and drop_item else "end"
                self.move(item, parent, index)
                # if not self.exists(item):
                #     continue
                # if not dropItem or part == 0:
                #     self.move(item, dropItem, "end")
                # else:
                #     parent = self.parent(dropItem)
                #     index = self.index(dropItem) + (part == 1)
                #     self.move(item, parent, index)

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
    # root = TkinterDnD.Tk()  # Utilisation de TkinterDnD pour le support DnD étendu
    # sans ça, <<Drop>> ne se déclenchera jamais.
    # top_level = tk.Toplevel()
    # root.title("Exemple de File/URL Drop Target Tkinter")
    root.title("Démonstration du DnD interne")
    # top_level.title("Exemple de File/URL Drop Target")
    root.geometry("400x300")
    # top_level.geometry("400x300")
    #

    # Exemple avec un Treeview
    # tree = MyTree(root)
    tree = MyTree(root, selectmode="extended")
    # tree.heading("#0", text="Arborescence")
    # id1 = tree.insert("", "end", text="Tâche 1")
    # id1_1 = tree.insert(id1, "end", text="Sous-tâche 1.1")
    # id1_2 = tree.insert(id1, "end", text="Sous-tâche 1.2")
    # id2 = tree.insert("", "end", text="Tâche 2")

    tree.pack(expand=True, fill="both", padx=20, pady=20)

    # # Exemple avec un Label
    # # # label = ttk.Label(root, text="Glissez-déposez des fichiers ou des URLs ici", relief="solid", padding=20)
    # # label = ttk.Label(top_level, text="Glissez-déposez des fichiers ou des URLs ici", relief="solid", padding=20)
    # label = ttk.Label(root, text="Déposez ici des fichiers ou des URLs/texte",
    #                   background="lightyellow")
    # # label.pack(expand=True, fill="both", padx=20, pady=20)
    # label.pack(fill=tk.X, pady=20, padx=20)
    # #
    # # # Initialiser notre nouvelle classe pour le Label
    # # FileUrlDropTarget(label, on_drop_url, on_drop_files)
    # # Utilisation de la classe FileUrlDropTarget
    # drop_target = FileUrlDropTarget(
    #     label,
    #     on_drop_url_callback=on_drop_url,
    #     on_drop_file_callback=on_drop_file
    # )
    for i in range(4):
        parent = tree.insert("", "end", text=f"Groupe {i}", open=True)
        for j in range(3):
            tree.insert(parent, "end", text=f"Tâche {i}.{j}")

    root.mainloop()
