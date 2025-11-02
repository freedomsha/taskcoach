# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

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

Vous devez spécifier les classes de mixin avant les autres classes.
"""

# from builtins import object
from taskcoachlib.domain import task, note, category, effort, attachment
import tkinter as tk  # Remplacer 'wx' par 'tkinter'


# Quels sont ces types de classes ? Mixin
# class NeedsSelectionMixin:
class NeedsSelectionMixin(object):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément sélectionné. """
    def enabled(self, event=None):  # L'argument `event` est rendu optionnel pour la compatibilité Tkinter
        return super().enabled(event) and self.viewer.curselection()


class NeedsSelectedCategorizableMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un catégorisable sélectionné. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            (self.viewer.curselectionIsInstanceOf(task.Task) or
             self.viewer.curselectionIsInstanceOf(note.Note))


class NeedsOneSelectedItemMixin(object):
    """ Classe Mixin pour les commandes d’interface utilisateur qui nécessitent exactement un élément sélectionné. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            len(self.viewer.curselection()) == 1


class NeedsSelectedCompositeMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément composite
        sélectionné. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            (self.viewer.curselectionIsInstanceOf(task.Task) or
             self.viewer.curselectionIsInstanceOf(note.Note) or
             self.viewer.curselectionIsInstanceOf(category.Category))


class NeedsOneSelectedCompositeItemMixin(NeedsOneSelectedItemMixin,
                                         NeedsSelectedCompositeMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent exactement un élément composite sélectionné. """
    pass


class NeedsAttachmentViewerMixin(object):
    """ Classe Mixin pour les commandes d'interface utilisateur nécessitant une visionneuse affichant les pièces jointes. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            self.viewer.isShowingAttachments()


class NeedsSelectedTasksMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur nécessitant une ou plusieurs tâches sélectionnées. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            self.viewer.curselectionIsInstanceOf(task.Task)


class NeedsSelectedNoteOwnersMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un propriétaire de note sélectionné. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            (self.viewer.curselectionIsInstanceOf(task.Task) or
             self.viewer.curselectionIsInstanceOf(category.Category) or
             self.viewer.curselectionIsInstanceOf(attachment.Attachment))


class NeedsSelectedNoteOwnersMixinWithNotes(NeedsSelectedNoteOwnersMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur nécessitant au moins un propriétaire de note sélectionné
        avec des notes. """
    def enabled(self, event=None):
        # pylint: disable=E1101
        return super().enabled(event) and \
            any([item.notes() for item in self.viewer.curselection()])


class NeedsSelectedAttachmentOwnersMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un propriétaire de pièce jointe sélectionné. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            (self.viewer.curselectionIsInstanceOf(task.Task) or
             self.viewer.curselectionIsInstanceOf(category.Category) or
             self.viewer.curselectionIsInstanceOf(note.Note))


class NeedsOneSelectedTaskMixin(NeedsSelectedTasksMixin,
                                NeedsOneSelectedItemMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur nécessitant au moins une tâche sélectionnée. """
    pass


class NeedsSelectionWithAttachmentsMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément sélectionné avec
        une ou plusieurs pièces jointes. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            any(item.attachments() for item in self.viewer.curselection() if not isinstance(item, effort.Effort))


class NeedsSelectedEffortMixin(NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un effort sélectionné. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            self.viewer.curselectionIsInstanceOf(effort.Effort)


class NeedsSelectedAttachmentsMixin(NeedsAttachmentViewerMixin,
                                    NeedsSelectionMixin):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins une pièce jointe sélectionnée
        . """
    pass


class NeedsAtLeastOneTaskMixin(object):
    """ Classe Mixin pour les commandes d’interface utilisateur nécessitant la création d’au moins une tâche. """
    def enabled(self, event=None):  # pylint: disable=W0613
        return len(self.taskList) > 0


class NeedsAtLeastOneCategoryMixin(object):
    """ Classe Mixin pour les commandes d’interface utilisateur nécessitant la création d’au moins une catégorie. """
    def enabled(self, event=None):  # pylint: disable=W0613
        return len(self.categories) > 0


class NeedsItemsMixin(object):
    """ Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément dans leur visionneuse. """
    def enabled(self, event=None):  # pylint: disable=W0613
        return self.viewer.size()


class NeedsTreeViewerMixin(object):
    """ Classe Mixin pour les commandes d'interface utilisateur nécessitant une visionneuse d'arborescence. """
    def enabled(self, event=None):
        return super().enabled(event) and \
            self.viewer.isTreeViewer()


class NeedsDeletedItemsMixin(object):
    """ Classe Mixin pour les commandes d’interface utilisateur qui nécessitent la présence d’éléments supprimés. """
    def enabled(self, event=None):
        return super().enabled(event) and \
               self.iocontroller.hasDeletedItems()


# --- PopupButtonMixin a été omis car il utilise des fonctionnalités wxPython qui n'ont pas d'équivalent direct dans Tkinter ---
# Le code ci-dessous est commenté pour l'instant. L'implémentation d'un PopupButton nécessiterait une approche
# complètement différente dans Tkinter, en utilisant des menus de type 'Menu'.
# C'est le cas !
# TODO : remplacer les fonction wx par des version tk !
# Le mixin wxPython que vous montrez est conçu pour être ajouté à un objet (probablement un contrôleur d'événement) qui gère un bouton de barre d'outils. Il calcule ensuite où afficher un menu contextuel (juste en dessous de la barre d'outils) lorsque la commande est exécutée.
#
# En tkinter, l'approche est un peu différente et, à mon avis, plus directe. Nous allons créer un mixin qui sera mélangé directement avec le widget tkinter lui-même (comme un tk.Button ou tk.Menubutton).
# Résumé des changements :
#
#     Héritage direct : Le mixin est utilisé directement par la classe du bouton (MyToolbarButton(tk.Button, PopupButtonMixin)), ce qui rend le self beaucoup plus simple. self est le bouton lui-même.
#
#     Calcul de position : wxPython a ScreenToClient et GetScreenPosition. En tkinter, c'est plus simple :
#
#         self.winfo_rootx() / self.winfo_rooty() donnent les coordonnées X/Y du widget par rapport à l'écran.
#
#         self.winfo_height() donne la hauteur du widget.
#
#         La position y est donc simplement self.winfo_rooty() + self.winfo_height().
#
#     Affichage du menu : self.mainWindow().PopupMenu() devient self.__menu.post(x, y).
#
#     Liaison d'événement : J'ai lié l'action command du tk.Button (équivalent à un clic gauche) à la méthode self.show_popup_menu, ce qui correspond à l'intention de votre doCommand.

class PopupButtonMixin(object):
    """ Mélange cela avec un UICommand pour un menu contextuel de barre d'outils.

    Mélangez (Mixin) cette classe avec un widget tkinter (ex: tk.Button)
    pour lui donner la capacité d'afficher un menu contextuel.

    La classe qui hérite doit implémenter la méthode :
     - create_popup_menu(self)
    """

    def __init__(self):
        """
        Initialise le mixin.
        S'assure que le menu n'est pas encore créé.
        """
        # __menu est mis en cache pour ne pas le recréer à chaque fois
        self.__menu = None

    def show_popup_menu(self):
        """
        Crée (si nécessaire) et affiche le menu contextuel
        juste en dessous du widget.
        """
        if not self.__menu:
            # Le menu n'existe pas encore, on le crée en appelant
            # la méthode que la classe enfant DOIT implémenter.
            self.__menu = self.create_popup_menu()
            if not self.__menu:
                # Si create_popup_menu ne retourne rien, on arrête.
                print("Erreur : create_popup_menu() n'a pas retourné de menu.")
                return

        # --- Calcul de la position ---
        # C'est l'équivalent de vos méthodes menuX, menuY et menuXY.

        # On s'assure que la géométrie du widget est à jour
        self.update_idletasks()

        # Coordonnées X de l'écran pour le coin supérieur gauche du widget
        x = self.winfo_rootx()

        # Coordonnées Y de l'écran, juste SOUS le widget
        y = self.winfo_rooty() + self.winfo_height()

        # --- Affichage du menu ---
        # C'est l'équivalent de self.mainWindow().PopupMenu(*args)
        try:
            # .post() affiche le menu aux coordonnées X, Y de l'ÉCRAN
            self.__menu.post(x, y)
        except tk.TclError as e:
            # Gère les erreurs (ex: si le menu est déjà affiché)
            print(f"Erreur Tcl lors de l'affichage du menu : {e}")

    def doCommand(self, event=None):  # pylint: disable=W0613
        try:
            args = [self.__menu]
        except AttributeError:
            self.__menu = self.createPopupMenu()  # pylint: disable=W0201
            args = [self.__menu]
        if self.toolbar:
            args.append(self.menuXY())

        # if not self.__menu:
        #     # Le menu n'existe pas encore, on le crée en appelant
        #     # la méthode que la classe enfant DOIT implémenter.
        #     self.__menu = self.create_popup_menu()
        #     if not self.__menu:
        #         # Si create_popup_menu ne retourne rien, on arrête.
        #         print("Erreur : create_popup_menu() n'a pas retourné de menu.")
        #         return
        # --- Affichage du menu ---
        # self.mainWindow().PopupMenu(*args)  # pylint: disable=W0142
        # C'est l'équivalent de self.mainWindow().PopupMenu(*args)
        try:
            # .post() affiche le menu aux coordonnées X, Y de l'ÉCRAN
            self.__menu.post(self.menuX(), self.menuY())
        except tk.TclError as e:
            # Gère les erreurs (ex: si le menu est déjà affiché)
            print(f"Erreur Tcl lors de l'affichage du menu : {e}")

    def menuXY(self):
        """ Emplacement pour afficher le menu. """
        return self.mainWindow().ScreenToClient((self.menuX(), self.menuY()))  # ScreenToClient est une méthode wx !

    def menuX(self):
        buttonWidth = self.toolbar.GetToolSize()[0]
        # mouseX = wx.GetMousePosition()[0]
        mouseX = self.winfo_rootx()
        return mouseX - 0.5 * buttonWidth

    def menuY(self):
        # toolbarY = self.toolbar.GetScreenPosition()[1]
        toolbarY = self.winfo_rooty()
        # toolbarHeight = self.toolbar.GetSize()[1]
        toolbarHeight = self.winfo_height()
        return toolbarY + toolbarHeight

    def createPopupMenu(self):
        raise NotImplementedError  # pragma: no cover

    def create_popup_menu(self):
        """
        Méthode abstraite (non implémentée) à surcharger.

        Cette méthode DOIT être implémentée par la classe qui utilise
        ce mixin. Elle doit construire et retourner un objet tk.Menu.
        """
        raise NotImplementedError(
            "La classe héritière doit implémenter create_popup_menu()"
        )
