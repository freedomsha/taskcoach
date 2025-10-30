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

Module `autowidthtk.py`

Ce module fournit le mixin `AutoColumnWidthMixin`, qui permet de redimensionner
automatiquement une colonne dans un contrôle à colonnes (par exemple, `wx.ListCtrl`,
`wx.TreeListCtrl`, ou `wx.lib.agw.hypertreelist.HyperTreeList`).

Fonctionnalités principales :
- Ajuste dynamiquement la largeur d'une colonne pour utiliser tout l'espace
  disponible sans créer d'espace inutile ou de barres de défilement horizontales.
- Gère les événements comme le redimensionnement ou le glissement des colonnes.

Dépendances :
- wxPython : Ce mixin suppose que les classes qui l'utilisent héritent de
  `wx.Window` ou de contrôles similaires (`wx.ListCtrl`, `wx.TreeListCtrl`).

Classes :
- `AutoColumnWidthMixin` : Fournit le comportement de redimensionnement
  automatique des colonnes.

Avertissements :
- Lorsque vous utilisez ce mixin, assurez-vous que votre contrôle est configuré
  pour un mode "rapport" (report mode) si nécessaire.
- Si vous surchargez `EVT_SIZE`, appelez `event.Skip()` pour garantir que la
  méthode `OnResize` du mixin est appelée.

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Licence : GNU General Public License, version 3 ou ultérieure.

#     Requête réussie
#
# La conversion directe de autowidth.py de wxPython vers Tkinter n'est pas possible. La logique et l'architecture des deux frameworks sont fondamentalement différentes. Le module autowidth.py est un mixin wxPython, une classe conçue pour être héritée par d'autres classes wxPython comme wx.ListCtrl ou wx.TreeListCtrl afin de leur ajouter une fonctionnalité de redimensionnement automatique des colonnes.
#
# Différences fondamentales entre wxPython et Tkinter
#
#     Architecture des widgets :
#
#         wxPython : Il utilise une approche orientée objet avec des classes de widgets spécifiques qui ont des méthodes et des attributs bien définis pour gérer leur comportement et leur apparence (ex: GetColumnWidth, SetColumnWidth, Bind, Unbind). Le mixin dans le fichier autowidth.py s'appuie directement sur ces méthodes pour fonctionner.
#
#         Tkinter : Bien que basé sur Tcl/Tk, il encapsule les commandes Tcl dans des classes Python. L'équivalent de wx.ListCtrl est le ttk.Treeview. Le redimensionnement automatique des colonnes n'est pas géré de la même manière dans ttk.Treeview et ne dispose pas des mêmes mécanismes de liaison d'événements (Bind, Unbind) pour le glissement des colonnes ou le redimensionnement de la fenêtre.
#
#     Gestion des événements :
#
#         wxPython : Il utilise un système de liaison d'événements basé sur des types d'événements spécifiques (wx.EVT_SIZE, wx.EVT_LIST_COL_BEGIN_DRAG, etc.) pour réagir aux actions de l'utilisateur ou du système.
#
#         Tkinter : Il utilise une méthode bind() pour associer des fonctions à des événements génériques de l'interface utilisateur, tels que <Configure> pour les changements de taille ou <B1-Motion> pour le glissement de la souris. Ces événements ne correspondent pas directement à ceux de wxPython.
#
#     Contexte du mixin :
#
#         Le mixin AutoColumnWidthMixin est fortement lié aux spécificités de wxPython, notamment aux méthodes de la classe wx.ListCtrl (ou similaires). Il utilise des fonctionnalités comme super().__init__(*args, **kwargs) pour s'intégrer dans l'arbre d'héritage de wxPython.
#
# Approche recommandée pour Tkinter
#
# Au lieu de tenter une conversion directe, il faut réimplémenter la fonctionnalité pour un widget ttk.Treeview de Tkinter. Le ttk.Treeview possède une option stretch qui peut être configurée pour redimensionner automatiquement une colonne pour remplir l'espace restant, ce qui est l'objectif principal du mixin wxPython.
#
# Pour réaliser une fonctionnalité similaire à celle d' autowidth.py, voici une approche :
#
#     Identifier la colonne à redimensionner : Déterminez l'identifiant de la colonne dans votre ttk.Treeview que vous souhaitez redimensionner automatiquement.
#
#     Gérer l'événement de redimensionnement : Liez l'événement <Configure> de la fenêtre parent au widget ttk.Treeview. Cet événement se déclenche lorsque la fenêtre est redimensionnée.
#
#     Ajuster la largeur des colonnes : Dans la fonction liée à l'événement <Configure>, calculez l'espace disponible. Parcourez toutes les colonnes du ttk.Treeview  et déduisez leur largeur fixe de la largeur totale de la fenêtre. L'espace restant est alloué à la colonne "auto-ajustable" à l'aide de treeview.column("colonne_id", width=nouvelle_largeur).
#
#     Gérer le glissement des colonnes : Tkinter ne propose pas de gestion native pour le glissement d'une colonne de ttk.Treeview. Cependant, des solutions existent pour gérer manuellement les événements de la souris (<B1-Motion>, <ButtonRelease-1>) pour simuler le redimensionnement des colonnes.
#
#     Rechercher des modules existants : Il est possible qu'un module tiers similaire existe déjà pour Tkinter.
#
# En résumé, la migration nécessite une réécriture complète de la logique en utilisant les outils et les méthodes propres à Tkinter, plutôt qu'une conversion ligne par ligne.

# Le fichier autowidth.py que vous avez fourni est un mixin wxPython,
# une classe qui fournit des fonctionnalités de redimensionnement automatique
# des colonnes pour des widgets wxPython comme ListCtrl et HyperTreeList.
#
# Inutilité de la conversion directe
#
# La conversion de ce fichier n'est pas pertinente pour Tkinter. Voici pourquoi :
#
#     Différences d'architecture : Les mixins et les systèmes d'événements de
#     wxPython sont fondamentalement différents de ceux de Tkinter.
#     Vous ne pouvez pas simplement traduire les appels de méthodes et
#     les gestionnaires d'événements de l'un à l'autre.
#
#     Absence de fonctionnalités équivalentes : Tkinter et son module ttk ne
#     possèdent pas de concept natif de mixin AutoColumnWidthMixin ou d'une
#     gestion aussi complexe du redimensionnement de colonnes.
#     Les widgets ttk.Treeview et ttk.Listbox gèrent la largeur des colonnes différemment.
#
#     Conflit de dépendances : Le code wxPython dépend de sa propre bibliothèque
#     pour la gestion des fenêtres et des événements. Tenter de le "convertir"
#     directement impliquerait de réécrire entièrement sa logique pour utiliser
#     les concepts de Tkinter, ce qui équivaut à un nouveau développement plutôt qu'à une conversion.
#
# Solution pour Tkinter
#
# Pour obtenir une fonctionnalité similaire de redimensionnement automatique
# des colonnes dans Tkinter,
# vous devez développer une nouvelle approche spécifiquement pour le widget
# ttk.Treeview. Ce widget est l'équivalent le plus proche de wx.ListCtrl en
# mode "rapport" (report mode) et prend en charge l'affichage en colonnes.
#
# Mise en œuvre de l'ajustement automatique
#
#     Gérer l'événement de redimensionnement de la fenêtre : Dans Tkinter,
#     vous pouvez lier un événement <Configure> à la fenêtre ou au widget Treeview lui-même.
#     Cet événement est déclenché lorsque la taille de la fenêtre change.
#
#     Calculer l'espace disponible : À l'intérieur du gestionnaire d'événements,
#     récupérez la largeur totale du Treeview en utilisant widget.winfo_width().
#
#     Ajuster les largeurs de colonne : Vous pouvez itérer sur les colonnes du
#     Treeview (tree.column('#0', width=...), tree.column('col1', width=...), etc.)
#     et ajuster la largeur de la colonne que vous souhaitez redimensionner
#     pour qu'elle occupe l'espace restant.
#
# Vous pouvez utiliser une logique similaire à celle du mixin wxPython :
# calculer la largeur totale de toutes les colonnes à largeur fixe,
# puis soustraire ce total de la largeur disponible pour trouver la largeur
# de la colonne qui doit être redimensionnée automatiquement.
"""
import logging
import tkinter as tk
from tkinter import ttk

log = logging.getLogger(__name__)


class AutoColumnWidthMixin(ttk.Treeview):
    # class AutoColumnWidthMixin(object):  # TODO : A Essayer car mixin !
    """
    Initialise le mixin avec des paramètres spécifiques.

    Args :
        resizeableColumn (int) : Index de la colonne à redimensionner
                                 automatiquement (par défaut : -1).
        resizeableColumnMinWidth (int) : Largeur minimale de la colonne
                                         redimensionnable (par défaut : 50).
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.bind('<Configure>', self.on_resize)
        self.__is_auto_resizing = False
        # self.resize_column = 'task_name'
        self.resize_column = kwargs.pop("resizeableColumn", -1)
        self.ResizeColumnMinWidth = kwargs.pop("resizeableColumnMinWidth", 50)
        # self.set_columns()

    def SetResizeColumn(self, column):
        """
        Définit la colonne à redimensionner automatiquement.

        Args :
            column (int) : Index de la colonne.
        """
        self.resize_column = column

    # def set_columns(self):
    #     # Configurez vos colonnes ici
    #     self['columns'] = ('task_name', 'due_date', 'priority')
    #     self.column('#0', width=0, stretch=tk.NO)  # Colonne fantôme
    #     self.heading('task_name', text='Tâche')
    #     self.heading('due_date', text='Date d’échéance')
    #     self.heading('priority', text='Priorité')
    #
    #     # Définir des largeurs initiales ou minimales
    #     self.column('due_date', minwidth=100, width=150)
    #     self.column('priority', minwidth=50, width=75)
    #
    #     # Insérer des données de test
    #     self.insert('', 'end', values=('Convertir le fichier', '2025-09-01', 'Haute'))
    #     self.insert('', 'end', values=('Écrire la documentation', '2025-09-15', 'Moyenne'))

    def on_resize(self, event):
        """Ajuste la largeur de la colonne spécifiée en fonction de l'espace disponible."""
        if self.winfo_width() > 1:  # Assurez-vous que le widget est visible
            total_width = self.winfo_width()
            fixed_width = 0

            # Calculer la largeur totale des colonnes à largeur fixe
            for col in self['columns']:
                if col != self.resize_column:
                    fixed_width += self.column(col)['width']

            # Définir la largeur de la colonne redimensionnable
            resize_width = total_width - fixed_width

            # Assurez-vous que la largeur est positive et supérieure à un minimum
            if resize_width > 50:
                self.column(self.resize_column, width=resize_width)


# if __name__ == '__main__':
#     from taskcoachlib.domain.task.tasklist import TaskList
#     root = tk.Tk()
#     root.title("TaskCoach avec Tkinter")
#     root.geometry("600x400")
#
#     task_list = TaskList(root, show='headings')
#     task_list.pack(fill=tk.BOTH, expand=True)  # TaskList n'est pas encore un widget ! pour être packé !
#
#     root.mainloop()
