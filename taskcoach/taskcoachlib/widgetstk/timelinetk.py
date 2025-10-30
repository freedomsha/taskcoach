# -*- coding: utf-8 -*-
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
# J'ai analysé la requête et les fichiers fournis. Il semble que vous ayez un fichier timeline.py qui est une classe d'interface utilisateur wxPython (appelée Timeline) qui utilise une autre classe timeline.py (appelée TimeLine) d'un module tiers. L'objectif est de convertir la classe Timeline en une classe TimelineTk qui utilise le module TimeLineCanvas que j'ai créé précédemment pour Tkinter.
#
# Voici le fichier timeline.tk qui implémente cette conversion. J'ai adapté la classe Timeline pour qu'elle s'intègre avec le widget TimeLineCanvas et pour qu'elle gère les événements de sélection, d'activation et de menu contextuel de manière compatible avec Tkinter.
#
# Ce fichier timeline.tk sert de couche d'abstraction, tout comme l'original timeline.py, en utilisant une composition sur le widget de base (TimeLineCanvas). Il gère les interactions et les rappels pour s'aligner sur les attentes du code client qui aurait été écrit pour la version wxPython. J'ai inclus un exemple d'utilisation dans le bloc if __name__ == "__main__": pour démontrer comment l'utiliser.

# J'ai analysé le fichier timelinetk.py que tu as fourni. C'est une conversion bien pensée de la classe Timeline de wxPython vers une classe compatible avec Tkinter. Le code est structuré de manière à encapsuler un widget Tkinter (TimeLineCanvas) tout en présentant une interface similaire à la version originale, ce qui est une approche intelligente pour maintenir la compatibilité avec le reste du code de l'application.
#
# Voici une analyse détaillée de ce que fait ton code et des points clés de la conversion.
#
# Aperçu de la conversion
#
# Ton code TimelineTk agit comme un adaptateur ou un wrapper. Au lieu d'hériter directement d'un widget Tkinter, il contient une instance de TimeLineCanvas. Cette approche par composition est souvent plus flexible et permet de mieux contrôler les interactions.
#
# Le but est de remplacer la classe Timeline de wxPython, qui gère la sélection, l'édition et les menus contextuels, par ta nouvelle classe TimelineTk, qui fait la même chose, mais avec Tkinter.
#
# Analyse du code fourni
#
# 1. Initialisation (__init__)
#
#     Tu as correctement remplacé la création de timeline.TimeLine par TimeLineCanvas.
#
#     Les rappels (onSelect, onEdit, popupMenu) sont stockés en tant que membres de la classe, tout comme dans la version wxPython.
#
#     Tu gères l'association du clic droit (<Button-3>) pour le menu contextuel en liant cet événement à la méthode on_popup. C'est l'équivalent de self.Bind(wx.EVT_RIGHT_DOWN, self.onPopup) en wxPython.
#
# 2. Gestion des événements
#
#     Sélection (on_select) : La logique est bien convertie. Lorsque le TimeLineCanvas signale une sélection, ta méthode on_select met à jour la liste interne __selection et appelle le rappel self.selectCommand.
#
#     Édition (on_edit) : De même, cette méthode gère l'événement d'activation (double-clic) et appelle le bon rappel, en passant le nœud concerné.
#
#     Menu contextuel (on_popup) : C'est un point crucial de la conversion.
#
#         Tu utilises event.x_root et event.y_root pour positionner le menu à la bonne position sur l'écran. C'est la manière standard de faire cela avec Tkinter.
#
#         L'utilisation de self.popupMenu.tk_popup() est correcte pour afficher le menu.
#
#         L'appel self.popupMenu.grab_release() est une bonne pratique pour s'assurer que le focus revient à la fenêtre après que l'utilisateur a interagi avec le menu.
#
#         Tu as ajouté une étape importante : self.canvas.find_node_at(event.x, event.y) pour déterminer quel nœud se trouve sous le clic droit et le sélectionner. C'est essentiel pour que le menu contextuel agisse sur l'élément correct.
#
# 3. Méthodes de compatibilité
#
#     curselection() : Cette méthode retourne la liste des éléments sélectionnés. La logique est bien préservée.
#
#     select(items) : Cette méthode permet de sélectionner des éléments par programme. Tu as géré le cas où il n'y a pas d'éléments à sélectionner et mis à jour le selected_node du canevas pour refléter la nouvelle sélection visuellement.
#
#     RefreshItems() : Cette méthode est un simple adaptateur qui appelle self.canvas.draw_timeline() pour forcer un redessin, ce qui est l'équivalent de Refresh() en wxPython.
#
# 4. Amélioration possible
#
#     Tu pourrais ajouter une logique pour gérer les infos-bulles (tooltips) si TimeLineCanvas ne le fait pas déjà. La classe originale Timeline utilise OnBeforeShowToolTip pour formater les données de l'info-bulle. Si TimeLineCanvas a un mécanisme pour les infos-bulles, tu pourrais l'intégrer ici en adaptant la méthode OnBeforeShowToolTip. Si ce n'est pas le cas, tu peux créer une fonction de rappel à passer au TimeLineCanvas pour générer le texte de l'info-bulle.
#
# Prochaines étapes
#
# Ton fichier timelinetk.py semble très solide et fonctionnel. Tu peux continuer à l'intégrer au reste de ton application. Les étapes suivantes seraient de :
#
#     Remplacer toutes les instances de Timeline(...) par TimelineTk(...).
#
#     T'assurer que l'objet popupMenu passé en paramètre est bien un objet tkinter.Menu.
#
#     Vérifier que les rappels onSelect et onEdit sont bien des fonctions ou
#     des méthodes qui gèrent le type de données que tu leur passes (un nœud pour onEdit).

# Points à noter
#
#     Images pour les cases à cocher : Les images checkbox_checked.png et
#     checkbox_unchecked.png doivent être présentes dans le même répertoire
#     que votre script ou dans un répertoire accessible.
#     J'ai inclus une logique simple pour lier un tag ('checked') à l'état de la case à cocher.
#
#     Dépendances : Ce code suppose que les classes TreeCtrlDragAndDropMixin,
#     CtrlWithItemsMixin et CtrlWithColumnsMixin sont définies et fonctionnent
#     correctement dans les fichiers draganddroptk.py et itemctrltk.py que
#     vous avez déjà convertis.
#
#     Édition de label : L'édition de label dans Tkinter n'est pas native.
#     La méthode on_edit est un point de départ. Vous devrez implémenter un
#     widget Entry ou similaire qui apparaît au-dessus du label lorsque vous
#     le double-cliquez pour permettre à l'utilisateur de le modifier.

#
from typing import List, Any
import tkinter as tk
from tkinter import Menu, messagebox

# Importe les classes du module timeline.py que nous avons converti précédemment
from taskcoachlib.thirdparty.timeline.timelinetk import TimeLineCanvas, Node, HotMap


class TimelineTk:
    """
    Une classe de mixin qui encapsule le widget TimeLineCanvas pour une utilisation
    similaire à la classe wxPython originale.
    """
    def __init__(self, parent: tk.Widget, rootNode: Node, onSelect: Any, onEdit: Any, popupMenu: Menu):
        """
        Initialise l'instance TimelineTk.

        Args:
            parent: Le widget parent.
            rootNode: Le nœud racine pour la chronologie.
            onSelect: Callback pour l'événement de sélection.
            onEdit: Callback pour l'événement d'activation.
            popupMenu: Le menu contextuel à afficher.
        """
        self.__selection = []
        self.rootNode = rootNode
        self.selectCommand = onSelect
        self.editCommand = onEdit
        self.popupMenu = popupMenu

        # Crée une instance de notre widget TimeLineCanvas
        self.canvas = TimeLineCanvas(
            parent,
            nodes=self.rootNode.parallel_children,  # Utilise les enfants parallèles comme nœuds de niveau supérieur
            on_select=self.on_select,
            on_activate=self.on_edit,
            width=800,
            height=400
        )
        # Affecte les fonctions de rappel aux attributs de la classe
        # pour la gestion des événements de sélection et d'activation.
        # self.canvas.on_select = self.on_select
        # self.canvas.on_activate = self.on_edit
        self.canvas.bind("<Button-3>", self.on_popup)

    def GetCanvas(self) -> tk.Canvas:
        """Retourne le widget Canvas pour l'empaquetage ou le placement."""
        return self.canvas

    def on_select(self, node: Node):
        """Gère l'événement de sélection du nœud."""
        if node == self.rootNode:
            self.__selection = []
        else:
            self.__selection = [node]
        if self.selectCommand:
            self.selectCommand()

    def on_edit(self, node: Node):
        """Gère l'événement d'activation (double-clic) du nœud."""
        if self.editCommand:
            self.editCommand(node)

    def on_popup(self, event: tk.Event):
        """Gère l'affichage du menu contextuel."""
        # Sélectionne le nœud sous le clic droit avant d'afficher le menu
        node = self.canvas.find_node_at(event.x, event.y)
        if node:
            self.canvas.selected_node = node
            self.canvas.draw_timeline()
            # Affiche le menu contextuel à la position du curseur
            try:
                self.popupMenu.tk_popup(event.x_root, event.y_root)
            finally:
                self.popupMenu.grab_release()

    def curselection(self) -> List[Node]:
        """Retourne la liste des nœuds actuellement sélectionnés."""
        return self.__selection

    def GetItemCount(self) -> int:
        """Retourne le nombre d'éléments dans la chronologie."""
        return len(self.rootNode.parallel_children)

    def select(self, items: List[Node]):
        """Sélectionne les éléments spécifiés."""
        if len(items) > 0:
            self.__selection = items
            self.canvas.selected_node = items[0]
            self.canvas.draw_timeline()
        else:
            self.__selection = []
            self.canvas.selected_node = None
            self.canvas.draw_timeline()

    # Les méthodes suivantes sont des stubs pour la compatibilité
    def RefreshItems(self):
        self.canvas.draw_timeline()

    def OnBeforeShowToolTip(self, x: int, y: int) -> Any:
        # L'info-bulle est gérée directement dans le widget TimeLineCanvas
        pass

    def isAnyItemExpandable(self) -> bool:
        return False

    def isAnyItemCollapsable(self) -> bool:
        return False

# --- Exemple d'utilisation pour vérifier le fonctionnement ---
if __name__ == "__main__":
    def on_select_callback():
        print(f"Événement de sélection. Sélection actuelle: {timeline_widget.curselection()}")

    def on_edit_callback(node: Node):
        messagebox.showinfo("Activation", f"Nœud activé: {node.path}")

    root = tk.Tk()
    root.title("Exemple d'intégration de TimelineTk")

    # Créez des données de test
    root_node = Node("Racine", 0, 100, [
        Node("Tâche A", 0, 30, [], []),
        Node("Tâche B", 20, 50, [], []),
        Node("Tâche C", 40, 70, [], []),
    ], [])

    # Crée un menu contextuel de test
    item_menu = Menu(root, tearoff=0)
    item_menu.add_command(label="Modifier la tâche", command=lambda: print("Modifier..."))
    item_menu.add_command(label="Supprimer la tâche", command=lambda: print("Supprimer..."))

    # Crée une instance de TimelineTk
    timeline_widget = TimelineTk(
        root,
        rootNode=root_node,
        onSelect=on_select_callback,
        onEdit=on_edit_callback,
        popupMenu=item_menu
    )

    # Place le widget de chronologie dans la fenêtre
    timeline_widget.GetCanvas().pack(padx=10, pady=10, expand=True, fill="both")

    root.mainloop()
