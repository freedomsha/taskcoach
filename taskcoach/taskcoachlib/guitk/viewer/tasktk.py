# -*- coding: utf-8 -*-
"""
Vue des tâches pour Tkinter.
Basé sur le fichier task.py original de Task Coach.
"""
# Le fichier task.py est l'un des composants les plus importants de l'application, car il gère l'affichage principal des tâches. La conversion de wxPython vers Tkinter nécessite de remplacer plusieurs widgets clés et de recréer la logique de l'interface utilisateur.
#
# J'ai réécrit ce fichier pour qu'il utilise le widget ttk.Treeview de Tkinter, qui est une alternative moderne et performante au wx.ListCtrl et au wx.TreeCtrl. J'ai également inclus des classes de simulation pour les autres modules de l'application (domain, uicommand, refresher, etc.) afin que le code converti soit fonctionnel et exécutable en tant que démonstration.
#
# Le code ci-dessous est bien commenté pour que vous puissiez comprendre comment chaque partie de la logique originale a été adaptée.

# Le code que vous avez fourni pour la classe Taskviewer utilise déjà ttk.Treeview pour créer une vue en arborescence, ce qui est l'équivalent moderne de wx.TreeCtrl en Tkinter. Les deux méthodes wxpython que vous souhaitez intégrer à la classe sont déjà gérées, pour la plupart, par votre code Tkinter existant.
#
# Voici comment adapter ces méthodes et où les intégrer dans votre classe Taskviewer existante :
#
#     createWidget : La méthode createWidget de wxpython est obsolète. Sa fonctionnalité principale a été intégrée directement dans le constructeur __init__ de votre classe Taskviewer en utilisant ttk.Treeview. Les éléments tels que la création du widget TreeListCtrl, l'assignation des colonnes, et la liaison des événements (comme le tri par colonne) sont déjà présents dans votre code. Les menus contextuels, la gestion du glisser-déposer, et l'édition de libellés sont des fonctionnalités qui doivent être ajoutées séparément en utilisant les événements et méthodes de ttk.Treeview.
#
#     isTreeViewer : La méthode isTreeViewer de wxpython est utilisée pour déterminer le mode d'affichage, soit arborescence, soit liste. Votre code Tkinter gère déjà ce comportement en utilisant l'attribut self.__viewMode dans le constructeur et en définissant les colonnes par défaut. Vous pouvez créer une nouvelle méthode appelée isTreeMode pour encapsuler cette logique.

# L'erreur que vous rencontrez, TypeError: Can't instantiate abstract class Taskviewer without an implementation for abstract methods..., indique que la classe Taskviewer est une classe abstraite qui ne peut pas être instanciée directement car elle hérite de méthodes abstraites de sa classe parente, Viewer, sans les implémenter.
#
# Explication de l'erreur
#
# Une classe abstraite est une classe qui est censée servir de modèle pour d'autres classes. Elle contient des méthodes abstraites, qui sont des méthodes déclarées mais non implémentées. Les classes enfants qui héritent d'une classe abstraite doivent obligatoirement fournir une implémentation concrète pour ces méthodes.
#
# Votre trace d'erreur montre que les méthodes suivantes sont manquantes dans votre classe Taskviewer :
#
#     bitmap
#
#     isShowingAttachments
#
#     isShowingCategories
#
#     isShowingEffort
#
#     isShowingNotes
#
#     isShowingTasks
#
#     isTreeViewer
#
#     isViewerContainer
#
# Ces méthodes sont définies comme abstraites dans la classe Viewer ou dans une de ses classes parentes, et votre implémentation de Taskviewer doit les définir.
#
# Correction
#
# Pour corriger cette erreur, vous devez ajouter les méthodes manquantes à la classe Taskviewer dans le fichier task.py. Étant donné que ces méthodes sont probablement des indicateurs de l'état du visualiseur, elles peuvent être implémentées de manière simple, en retournant une valeur booléenne (True ou False) par défaut ou une valeur None.
#
# Voici les modifications à apporter au fichier task.py en s'appuyant sur les méthodes manquantes de base.py (votre classe Viewer et ViewerContainer).
#
#     Ouvrez le fichier task.py.
#
#     Modifiez la classe Taskviewer pour inclure les méthodes manquantes.
# En ajoutant ces méthodes, vous fournissez les implémentations que la classe abstraite attend, ce qui résoudra l'erreur TypeError. Vous remarquerez que certaines méthodes comme isTreeViewer et isTreeMode sont très similaires ; vous pouvez les faire pointer vers la même logique pour éviter la redondance. La plupart des autres méthodes peuvent simplement retourner True ou False selon leur comportement par défaut dans votre application.
# Explication de l'Erreur
#
# L'erreur TypeError: ViewerContainer.__init__() missing 2 required positional arguments se produit car Taskviewer, en héritant de ViewerContainer, tente d'appeler son constructeur (__init__) sans lui fournir les arguments parent_widget et settings. Le super().__init__ dans Taskviewer essaye d'initialiser ViewerContainer comme une classe de base, ce qui est une erreur de conception.
#
# La structure correcte doit être la suivante :
#
#     MainWindow contient une instance de ViewerContainer.
#
#     ViewerContainer contient des instances de différents visualiseurs, comme Taskviewer.
#
#     Taskviewer doit hériter d'une classe de base de visualiseur (probablement Viewer ou ViewerWithColumns), mais pas de ViewerContainer.
#
# Correction des Fichiers
#
# Pour corriger ce problème, vous devez annuler la modification que j'ai suggérée précédemment et revenir à la bonne hiérarchie.
#
#     Dans task.py : Assurez-vous que la classe Taskviewer n'hérite pas de ViewerContainer. Elle doit hériter de sa classe de base correcte, qui semble être Viewer (ou potentiellement Viewer et d'autres mixins, comme dans le code original).
#
#     Dans factory.py : La logique dans factory.py est correcte. C'est elle qui est responsable de créer une instance de ViewerContainer et d'y ajouter une instance de Taskviewer. C'est le rôle du factory de s'occuper de cette composition.

# Voici le fichier tasktk.py complet et converti pour Tkinter ! J'ai effectué les principales modifications suivantes :
# Principales conversions :
#
# Imports mis à jour : Tous les imports utilisent maintenant les modules Tkinter convertis (basetk, inplace_editortk, mixintk, refreshertk)
# Gestion des erreurs robuste : Ajout de try/except pour gérer les modules non encore convertis
# Événements Tkinter : Remplacement des événements wx par leurs équivalents Tkinter (<<TreeBeginEdit>>, <<TreeEndEdit>>, etc.)
# Widget principal : Utilisation de itemctrltk.TreeListCtrl avec fallback sur ttk.Treeview
# Méthodes de rendu : Toutes les méthodes de rendu des colonnes sont implémentées
# Callbacks d'édition : Toutes les méthodes de callback pour l'édition des colonnes
# Support complet des colonnes :
#
# Colonnes de dates (plannedStartDateTime, dueDateTime, etc.)
# Colonnes de budget (budget, timeSpent, budgetLeft)
# Colonnes financières (hourlyFee, fixedFee, revenue)
# Colonnes diverses (priority, percentageComplete, etc.)
#
#
# Gestion des modes : Support du mode arbre/liste avec isTreeViewer()
# Menus contextuels : Création des menus pour les tâches et les colonnes
# Code de démonstration : Exemple fonctionnel à la fin du fichier
#
# Le fichier est maintenant prêt à être intégré dans votre application Tkinter. Notez que certains modules comme dialog.editor.TaskEditor devront être adaptés séparément.
import logging
import math
import tkinter as tk
from tkinter import ttk, messagebox
import struct
import tempfile
from typing import Any, Callable, Dict, List, Optional, Set, Type

from future.backports.datetime import timedelta
from pubsub import pub

# Imports TaskCoach
from taskcoachlib import operating_system
from taskcoachlib import command, domain, render
from taskcoachlib.domain import task, date
from taskcoachlib.i18n import _

# Imports Tkinter convertis
from taskcoachlib.guitk import dialog
# from taskcoachlib.guitk.dialog import editor
from taskcoachlib.guitk.uicommand import uicommandtk as uicommand
from taskcoachlib.guitk.uicommand.base_uicommandtk import UICommand
import taskcoachlib.guitk.menutk
from taskcoachlib.guitk.viewer import basetk
from taskcoachlib.guitk.viewer import inplace_editortk
from taskcoachlib.guitk.viewer import mixintk
from taskcoachlib.guitk.viewer import refreshertk
from taskcoachlib import widgetstk
from taskcoachlib.widgetstk import itemctrltk, treectrltk, calendarwidgettk


# from taskcoachlib.gui.viewer import TaskViewer, ViewerContainer
from taskcoachlib.guitk.viewer.basetk import Viewer, SortableViewerWithColumns
from taskcoachlib.guitk.viewer.mixintk import SortableViewerForTasksMixin, AttachmentDropTargetMixin, NoteColumnMixin, AttachmentColumnMixin

# try:
from taskcoachlib.config import settings
# Imports pour les widgets non encore convertis (à adapter progressivement)
from taskcoachlib.thirdparty.tkScheduler.tkSchedulerConstants import SCHEDULER_TODAY
from taskcoachlib.thirdparty.tkScheduler.tkDrawer import tkBaseDrawer
from taskcoachlib.thirdparty import tkdatetimectrl as sdtc
from taskcoachlib.widgetstk.calendarconfigtk import CalendarConfigDialog
from taskcoachlib.widgetstk.hcalendarconfigtk import HierarchicalCalendarConfigDialog
# from taskcoachlib.widgetstk.squaremap import SquareMap  # TODO à convertir
from taskcoachlib.widgetstk.timelinetk import TimelineTk
# except ImportError:
#     # Fallback si les modules ne sont pas disponibles
#     wxSCHEDULER_TODAY = None
#     wxFancyDrawer = None
#     sdtc = None
#     CalendarConfigDialog = None
#     HierarchicalCalendarConfigDialog = None

from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks


log = logging.getLogger(__name__)
# log.warning(TaskViewer.__mro__)
# taskcoachlib.guitk.viewer.task:
# (<class 'taskcoachlib.gui.viewer.task.TaskViewer'>,
# <class 'taskcoachlib.gui.viewer.mixin.AttachmentDropTargetMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.SortableViewerForTasksMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.ManualOrderingMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.SortableViewerForCategorizablesMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.NoteColumnMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.AttachmentColumnMixin'>,
# <class 'taskcoachlib.gui.viewer.base.SortableViewerWithColumns'>,
# <class 'taskcoachlib.gui.viewer.mixin.SortableViewerMixin'>,
# <class 'taskcoachlib.gui.viewer.base.ViewerWithColumns'>,
# <class 'taskcoachlib.gui.viewer.task.BaseTaskTreeViewer'>,
# <class 'taskcoachlib.gui.viewer.task.BaseTaskViewer'>,
# <class 'taskcoachlib.gui.viewer.mixin.SearchableViewerMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.FilterableViewerForTasksMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.FilterableViewerForCategorizablesMixin'>,
# <class 'taskcoachlib.gui.viewer.mixin.FilterableViewerMixin'>,
# <class 'taskcoachlib.gui.viewer.base.CategorizableViewerMixin'>,
# <class 'taskcoachlib.gui.viewer.base.WithAttachmentsViewerMixin'>,
# <class 'taskcoachlib.gui.viewer.base.TreeViewer'>,
# <class 'taskcoachlib.gui.viewer.base.Viewer'>,
# <class 'wx._core.Panel'>,
# <class 'wx._core.Window'>,
# <class 'wx._core.WindowBase'>,
# <class 'wx._core.EvtHandler'>,
# <class 'wx._core.Object'>,
# <class 'wx._core.Trackable'>,
# <class 'sip.wrapper'>,
# <class 'sip.simplewrapper'>,
# <class 'taskcoachlib.patterns.observer.Observer'>,
# <class 'object'>)


# --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# def _(text: str) -> str:
#     return text


# class settings:
#     def __init__(self):
#         self._data: Dict[str, Any] = {
#             "taskviewer": {
#                 "columns": "subject,duedate,priority",
#                 "viewmode": "tree"
#             }
#         }
#
#     def get(self, section: str, option: str) -> str:
#         return self._data.get(section, {}).get(option, "")
#
#     def getboolean(self, section: str, option: str) -> bool:
#         return self.get(section, option).lower() in ('true', '1', 't', 'y', 'yes')


# class domain:
#     class date:
#         def __init__(self, value: Any):
#             self.value = value
#         def __str__(self) -> str:
#             return str(self.value)
#
#     class task:
#         def __init__(self, subject: str, duedate: Any, priority: int, get_domain_children: Optional[List['domain.task']] = None):
#             self.subject = subject
#             self.duedate = duedate
#             self.priority = priority
#             self._children = get_domain_children if get_domain_children else []
#             self.is_completed = False
#
#         def get_domain_children(self) -> List['domain.task']:
#             return self._children
#
#         def isCompleted(self) -> bool:
#             return self.is_completed
#
#         def get_parent(self) -> Optional['domain.task']:
#             return None # Simplification pour la démo


# class uicommand:
#     class UICommand:
#         def __init__(self, value: str, menuText: str, helpText: str):
#             self.value = value
#             self.menuText = menuText
#             self.helpText = helpText
#
#     class UICommandContainer:
#         def __init__(self):
#             self.commands = {}
#
#         def add(self, command: 'uicommand.UICommand'):
#             self.commands[command.value] = command


# class refresher:
#     class MinuteRefresher:
#         def __init__(self, viewer: Any, **kwargs: Any):
#             pass

#         def setTrackedItems(self, items: List[Any]):
#             pass


# class pubsub:
#     def __init__(self):
#         pass
#
#     def subscribe(self, listener: Callable, topic: str):
#         pass
#
#     def unsubscribe(self, listener: Callable, topic: str):
#         pass
#
#
# pub = pubsub()


# --- CLASSE CONVERTIE ---
# ============================================================================
# Classes de support
# ============================================================================

class DueDateTimeCtrl(inplace_editortk.DateTimeCtrl):
    """
    Contrôle de sélection de date et heure pour les dates d'échéance.

    Ce contrôle est utilisé pour définir ou modifier la date d'échéance d'une tâche
    en utilisant une sélection relative (par exemple, en fonction d'une autre date).
    """
    def __init__(self, parent, item, column, owner, value, **kwargs):
        kwargs["relative"] = True
        # kwargs["startDateTime"] = item.plannedStartDateTime()  # .GetData() supprimé car non trouvé
        try:
            kwargs["startDateTime"] = item.plannedStartDateTime()
        except AttributeError:
            kwargs["startDateTime"] = date.DateTime()
        super().__init__(parent, item, column, owner, value, **kwargs)
        # sdtc.EVT_TIME_CHOICES_CHANGE(self._date_time_ctrl, self.OnChoicesChange) # À adapter car sdtc n'a pas été converti
        # self._dateTimeCtrl.LoadChoices(item.GetData().settings.get("feature", "sdtcspans")) # À adapter
        # # Gestion des événements de changement de choix (si sdtc est disponible)
        # if sdtc is not None and hasattr(self, '_date_time_ctrl'):
        #     try:
        #         self._date_time_ctrl.bind("<<ChoicesChange>>", self.OnChoicesChange)
        #         if hasattr(item, 'settings'):
        #             self._date_time_ctrl.LoadChoices(
        #                 item.settings.get("feature", "sdtcspans")
        #             )
        #     except Exception as e:
        #         log.warning(f"Impossible de lier les événements de choix: {e}")

    # def OnChoicesChange(self, event): # À adapter
    #     self.item.settings.settext("feature", "sdtcspans", event.GetValue()) # .GetData() supprimé car non trouvé
    def OnChoicesChange(self, event):
        """Gère les événements de changement de sélection dans le contrôle de choix."""
        try:
            if hasattr(self.item, 'settings'):
                self.item.settings.settext(
                    "feature", "sdtcspans", event.widget.get()
                )
        except Exception as e:
            log.warning(f"Erreur lors du changement de choix: {e}")


class TaskViewerStatusMessages(object):
    """
    Génère les messages de statut affichés dans le visualiseur de tâches.

    Ces messages incluent le nombre de tâches sélectionnées, visibles, totales
    ainsi que le nombre de tâches en retard, inactives, ou terminées.
    """
    template1 = _("Tasks: %d selected, %d visible, %d total")
    template2 = _("Status: %d overdue, %d late, %d inactive, %d completed")

    def __init__(self, viewer):
        super().__init__()
        self.__viewer = viewer
        self.__presentation = viewer.presentation()

    def __call__(self):
        """Retourne les messages de statut formatés."""
        try:
            count = self.__presentation.observable(recursive=True).nrOfTasksPerStatus()
            return (
                self.template1 % (
                    len(self.__viewer.curselection()),
                    self.__viewer.nrOfVisibleTasks(),
                    self.__presentation.originalLength(),
                ),
                self.template2 % (
                    count[task.status.overdue],
                    count[task.status.late],
                    count[task.status.inactive],
                    count[task.status.completed],
                ),
            )
        except Exception as e:
            log.error(f"TaskViewerStatusMessages.__call__ : Erreur lors de la génération des messages de statut: {e}")
            return "", ""


# ============================================================================
# Visualiseurs de base
# ============================================================================

class BaseTaskViewer(
    mixintk.SearchableViewerMixin,
    mixintk.FilterableViewerForTasksMixin,
    basetk.CategorizableViewerMixin,
    basetk.WithAttachmentsViewerMixin,
    basetk.TreeViewer,
):
    """
    Visualiseur de base pour les tâches.

    Cette classe gère la visualisation des tâches sous forme d'arborescence,
    et permet d'ajouter des filtres, des pièces jointes, et de rechercher
    des tâches spécifiques.
    """
    def __init__(self, *args, **kwargs):
        """Initialise le visualiseur et enregistre les observateurs nécessaires."""
        log.debug(f"BaseTaskViewer : Création du Visualiseur de base pour les tâches.")
        super().__init__(*args, **kwargs)
        self.statusMessages = TaskViewerStatusMessages(self)
        self.__registerForAppearanceChanges()
        # Affichage différé de l'info-bulle
        log.debug("BaseTaskViewer : Appel de CallAfter.")
        # wx.CallAfter(self.__DisplayBalloon) # À remplacer par self.after
        # self.after(0, self.__DisplayBalloon)
        self.after(100, self.__DisplayBalloon)
        log.debug("BaseTaskViewer : Visualiseur de base créé.")

    def __DisplayBalloon(self):
        """Affiche une info-bulle pour informer l'utilisateur."""
        try:
            if (  # À adapter
                # self.toolbar.getToolIdByCommand("ViewerHideTasks_completed") != wx.ID_ANY
                hasattr(self, 'toolbar')
                # and self.toolbar.IsShownOnScreen()
                and self.toolbar.winfo_ismapped()
                # and hasattr(wx.GetTopLevelParent(self), "AddBalloonTip")
                and hasattr(self.winfo_toplevel(), "AddBalloonTip")
            ):
                # wx.GetTopLevelParent(self).AddBalloonTip(
                self.winfo_toplevel().AddBalloonTip(
                    self.settings,
                    "filtershiftclick",
                    self.toolbar,
                    title=_("Filtres"),
                    # getRect=lambda: self.toolbar.GetToolRect(
                    #     self.toolbar.getToolIdByCommand(
                    #         "ViewerHideTasks_completed"
                    #     )
                    # ),
                    getRect=lambda: (0, 0, 28, 16),
                    message=_(
                        """Shift-click on a filter tool to see only tasks belonging to the corresponding status"""
                    ),
                )
        except Exception as e:
            log.debug(f"Impossible d'afficher l'info-bulle: {e}")
        # pass

    def __registerForAppearanceChanges(self):
        """
        Abonne le spectateur aux modifications de la police, de la couleur de premier plan,
        de la couleur d’arrière-plan et des paramètres d’icône pour divers états de tâche.
        """
        for appearance in ("font", "fgcolor", "bgcolor", "icon"):
            appearanceSettings = [
                f"settings.{appearance}.{setting}"
                for setting in (
                    "activetasks",
                    "inactivetasks",
                    "completedtasks",
                    "duesoontasks",
                    "overduetasks",
                    "latetasks",
                )
            ]
            for appearanceSetting in appearanceSettings:
                pub.subscribe(
                    self.onAppearanceSettingChange, appearanceSetting
                )
        # Enregistrement des observateurs pour les changements d'attributs
        self.registerObserver(
            self.onAttributeChanged_Deprecated,
            eventType=task.Task.appearanceChangedEventType(),
        )
        pub.subscribe(
            self.onAttributeChanged, task.Task.prerequisitesChangedEventType()
        )
        pub.subscribe(self.refresh, "powermgt.on")

    def detach(self):
        """
        Détache le visualiseur et les observateurs associés.
        """
        super().detach()
        self.statusMessages = None  # Break cycle

    def _renderTimeSpent(self, *args, **kwargs):
        """
        Rend le temps passé sous forme décimale ou standard.
        """
        if self.settings.getboolean("feature", "decimaltime"):
            return render.timeSpentDecimal(*args, **kwargs)
        return render.timeSpent(*args, **kwargs)

    def onAppearanceSettingChange(self, value):
        """
        Met à jour l'apparence des tâches en fonction des paramètres d'affichage.
        """
        if self:
            # wx.CallAfter(self.refresh) # À remplacer par self.after
            self.after(0, self.refresh)
            # Show/hide status in toolbar may change too
        # self.toolbar.loadPerspective(self.toolbar.perspective(), cache=False) # À adapter

    def domainObjectsToView(self):
        """
        Retourne les objets de domaine (tâches) à visualiser.
        """
        return self.taskFile.tasks()

    def isShowingTasks(self):
        """Indique que ce visualiseur affiche des tâches."""
        return True

    def createFilter(self, taskList):
        """
        Crée un filtre pour les tâches à visualiser.
        """
        tasks = domain.base.DeletedFilter(taskList)
        return super().createFilter(tasks)

    def nrOfVisibleTasks(self):
        """
        Retourne le nombre de tâches visibles.
        """
        return len(self.presentation())


class BaseTaskTreeViewer(BaseTaskViewer):
    """
    Visualiseur de tâches sous forme d'arborescence avec rafraîchissement automatique.

    Ce visualiseur est conçu pour afficher les tâches sous forme d'arbre
    avec des rafraîchissements en temps réel toutes les secondes ou minutes.
    """
    defaultTitle = _("Tasks")
    defaultBitmap = "led_blue_icon"

    def __init__(self, *args, **kwargs):
        """Initialise le visualiseur avec des options supplémentaires pour rafraîchir les tâches."""
        log.debug(f"BaseTaskTreeViewer.__init__ : Création du Visualiseur de tâches sous forme d'arborescence avec rafraîchissement automatique.")
        super().__init__(*args, **kwargs)

        # Initialisation des rafraîchisseurs
        if kwargs.get("doRefresh", True):
            try:
                self.secondRefresher = refreshertk.SecondRefresher(
                    self, task.Task.trackingChangedEventType()
                )
                self.minuteRefresher = refreshertk.MinuteRefresher(self)
            except Exception as e:
                log.warning(f"BaseTaskTreeViewer.__init__ : Impossible d'initialiser les rafraîchisseurs: {e}!")
                self.secondRefresher = self.minuteRefresher = None
        else:
            self.secondRefresher = self.minuteRefresher = None
        log.debug("BaseTaskTreeViewer initialisé !")

    def detach(self):
        """
        Détache les observateurs et arrête les rafraîchissements automatiques.
        """
        super().detach()
        if hasattr(self, "secondRefresher") and self.secondRefresher:
            try:
                self.secondRefresher.stopClock()
                if hasattr(self.secondRefresher, 'removeInstance'):
                    self.secondRefresher.removeInstance()
                del self.secondRefresher
            except Exception as e:
                log.warning(f"BaseTaskTreeViewer.detach : Erreur lors de l'arrêt du secondRefresher: {e}")
        if hasattr(self, "minuteRefresher") and self.minuteRefresher:
            try:
                self.minuteRefresher.stopClock()
                del self.minuteRefresher
            except Exception as e:
                log.warning(f"BaseTaskTreeViewer.detach : Erreur lors de l'arrêt du minuteRefresher: {e}")

    def newItemDialog(self, *args, **kwargs):
        """
        Ouvre une boîte de dialogue pour créer un nouvel élément (tâche ou sous-tâche).
        """
        kwargs["categories"] = self.taskFile.categories().filteredCategories()
        return super().newItemDialog(*args, **kwargs)

    def editItemDialog(
            self, items, bitmap, columnName="", items_are_new=False
    ):
        """
        Ouvre une boîte de dialogue pour éditer les tâches sélectionnées.
        """
        from taskcoachlib.guitk.dialog.editor import EffortEditor
        if isinstance(items[0], task.Task):
            return super().editItemDialog(
                items,
                bitmap,
                columnName=columnName,
                items_are_new=items_are_new,
            )
        else:
            # Pour les efforts (à adapter si le module est disponible)
            # return dialog.editor.EffortEditor( # À adapter car effortEditor n'a pas été converti
            #     wx.GetTopLevelParent(self),
            #     items,
            #     self.settings,
            #     self.taskFile.efforts(),
            #     self.taskFile,
            #     bitmap=bitmap,
            #     items_are_new=items_are_new,
            # )
            try:
                # return dialog.editor.EffortEditor(
                return EffortEditor(
                    self.winfo_toplevel(),
                    items,
                    self.settings,
                    self.taskFile.efforts(),
                    self.taskFile,
                    bitmap=bitmap,
                    items_are_new=items_are_new,
                )
            except (AttributeError, ImportError) as e:
                log.warning(f"BaseTaskTreeViewer.editItemDialog : EffortEditor non disponible: {e}")
                messagebox.showwarning(
                    _("Non disponible"),
                    _("L'éditeur d'effort n'est pas encore disponible.")
                )
                return None
            # pass

    def itemEditorClass(self):
        """Retourne la classe d'éditeur pour les tâches."""
        from taskcoachlib.guitk.dialog.editor import TaskEditor
        try:
            # return dialog.editor.TaskEditor
            return TaskEditor
        except AttributeError:
            log.warning("BaseTaskTreeViewer.itemEditorClass : TaskEditor non disponible")
            return None

    def newItemCommandClass(self):
        """Retourne la classe de commande pour créer une nouvelle tâche."""
        return command.NewTaskCommand

    def newSubItemCommandClass(self):
        """Retourne la classe de commande pour créer une sous-tâche."""
        return command.NewSubTaskCommand

    def newSubItemCommand(self):
        """Crée une commande pour créer une sous-tâche avec les paramètres appropriés."""
        kwargs = dict()
        if self.__shouldPresetPlannedStartDateTime():
            kwargs["plannedStartDateTime"] = task.Task.suggestedPlannedStartDateTime()
        if self.__shouldPresetDueDateTime():
            kwargs["dueDateTime"] = task.Task.suggestedDueDateTime()
        if self.__shouldPresetActualStartDateTime():
            kwargs["actualStartDateTime"] = task.Task.suggestedActualStartDateTime()
        if self.__shouldPresetCompletionDateTime():
            kwargs["completionDateTime"] = task.Task.suggestedCompletionDateTime()
        if self.__shouldPresetReminderDateTime():
            kwargs["reminder"] = task.Task.suggestedReminderDateTime()

        return self.newSubItemCommandClass()(
            self.presentation(), self.curselection(), **kwargs
        )

    def __shouldPresetPlannedStartDateTime(self):
        """Vérifie si la date de début planifiée doit être pré-remplie."""
        return self.settings.get(
            "view", "defaultplannedstartdatetime"
        ).startswith("preset")

    def __shouldPresetDueDateTime(self):
        """Vérifie si la date d'échéance doit être pré-remplie."""
        return self.settings.get("view", "defaultduedatetime").startswith("preset")

    def __shouldPresetActualStartDateTime(self):
        """Vérifie si la date de début réelle doit être pré-remplie."""
        return self.settings.get("view", "defaultactualstartdatetime").startswith(
            "preset"
        )

    def __shouldPresetCompletionDateTime(self):
        """Vérifie si la date d'achèvement doit être pré-remplie."""
        return self.settings.get("view", "defaultcompletiondatetime").startswith(
            "preset"
        )

    def __shouldPresetReminderDateTime(self):
        """Vérifie si la date de rappel doit être pré-remplie."""
        return self.settings.get("view", "defaultreminderdatetime").startswith(
            "preset"
        )

    def deleteItemCommand(self):
        """Crée une commande pour supprimer les éléments sélectionnés."""
        return command.DeleteTaskCommand(
            self.presentation(),
            self.curselection(),
            shadow=self.settings.getboolean("feature", "syncml"),
        )

    def createTaskPopupMenu(self):  # TODO ajouter parent ! ou parent_window ?
        """
        Crée et retourne le TaskPopupMenu/menu contextuel pour les tâches.
        """
        # from taskcoachlib.gui.menu import TaskPopupMenu
        log.debug(f"BaseTaskTreeViewer.createTaskPopupMenu : Création du menu contextuel.")
        try:
            task_popup_menu = taskcoachlib.guitk.menutk.TaskPopupMenu(
                self,  # self.parent ?
                self.parent,  # TODO : A revoir avec parent et parent_window !
                self.settings,
                self.presentation(),
                self.taskFile.efforts(),
                self.taskFile.categories(),
                self,
            )
            return task_popup_menu
        except Exception as e:
            log.error(f"BaseTaskTreeViewer.createTaskPopupMenu : Erreur lors de la création du menu contextuel: {e}")
            return None

    def createCreationToolBarUICommands(self):
        """
        Crée des commandes UI pour la barre d'outil.
        """
        return (
            uicommand.TaskNew(taskList=self.presentation(), settings=self.settings),
            uicommand.NewSubItem(viewer=self),
            uicommand.TaskNewFromTemplateButton(
                taskList=self.presentation(), settings=self.settings, bitmap="newtmpl"
            ),
        ) + super().createCreationToolBarUICommands()

    def createActionToolBarUICommands(self):
        """
        Crée des commandes UI pour la barre d'outil.
        """
        uiCommands = (
            uicommand.AddNote(settings=self.settings, viewer=self),
            uicommand.TaskMarkInactive(settings=self.settings, viewer=self),
            uicommand.TaskMarkActive(settings=self.settings, viewer=self),
            uicommand.TaskMarkCompleted(settings=self.settings, viewer=self),
        )
        uiCommands += (
            None,
            uicommand.EffortStart(viewer=self, taskList=self.taskFile.tasks()),
            uicommand.EffortStop(
                viewer=self,
                effortList=self.taskFile.efforts(),
                taskList=self.taskFile.tasks(),
            ),
        )
        return uiCommands + super().createActionToolBarUICommands()

    def createModeToolBarUICommands(self):
        """Crée des commandes UI pour la barre d'outils (modes)."""
        hideUICommands = tuple(
            [
                uicommand.ViewerHideTasks(
                    taskStatus=status, settings=self.settings, viewer=self
                )
                for status in task.Task.possibleStatuses()
            ]
        )
        otherModeUICommands = super().createModeToolBarUICommands()
        separator = (None,) if otherModeUICommands else ()
        return hideUICommands + separator + otherModeUICommands

    def iconName(self, item, isSelected):
        """Retourne le nom de l'icône pour un élément."""
        return (
            item.selectedIcon(recursive=True)
            if isSelected
            else item.icon(recursive=True)
        )

    def getItemTooltipData(self, task_item):
        """Récupère les données pour l'info-bulle d'un élément."""
        log.debug(f"BaseTaskTreeViewer.getItemTooltipData : task={self.getItemText(task_item)}")
        result = [
            (self.iconName(task_item, task_item in self.curselection()), [self.getItemText(task_item)])
        ]
        if task_item.notes():
            result.append(
                (
                    "note_icon",
                    sorted([note.subject() for note in task_item.notes()]),
                )
            )
        if task_item.attachments():
            result.append(
                (
                    "paperclip_icon",
                    sorted(
                        [str(attachment) for attachment in task_item.attachments()]
                    ),
                )
            )
        return result + super().getItemTooltipData(task_item)

    def label(self, task_item):
        """Retourne le libellé d'un élément."""
        return self.getItemText(task_item)


class RootNode(object):
    """
    Classe de base pour représenter la racine d'une arborescence de tâches.
    """
    def __init__(self, tasks):
        log.debug(f"RootNode : Initialise la racine avec les tâches {tasks}.")
        self.tasks = tasks

    def subject(self):
        """
        Retourne une chaîne vide (aucun sujet pour la racine).
        """
        return ""

    def children(self, recursive=False) -> list:
        """
        Retourne les tâches enfants.
        """
        if recursive:
            return self.tasks[:]
        else:
            return self.tasks.rootItems()

    def foregroundColor(self, *args, **kwargs):
        """
        Retourne la couleur de premier plan.
        """
        return None

    def backgroundColor(self, *args, **kwargs):
        """
        Retourne la couleur d'arrière-plan.
        """
        return None

    def font(self, *args, **kwargs):
        """
        Retourne la police à utiliser pour afficher la tâche.
        """
        return None

    def completed(self, *args, **kwargs):
        """
        Indique si une tâche est terminée.
        """
        return False

    late = dueSoon = inactive = overdue = isBeingTracked = completed


class SquareMapRootNode(RootNode):
    """
    Classe représentant la racine d'une carte carrée des tâches.
    """
    def __getattr__(self, attr):
        """
        Retourne un attribut calculé récursivement.
        """
        def getTaskAttribute(recursive=True):
            if recursive:
                s = 0
                for task_ in self.children():
                    if hasattr(task_, "_getAttrDict"):
                        d = task_._getAttrDict()
                        if attr in d:
                            value = d[attr]
                        else:
                            value = getattr(task_, attr)
                    else:
                        value = getattr(task_, attr)
                    s += value(recursive=True)
                return max(s, self.__zero)
            else:
                return self.__zero

        self.__zero = (
            date.TimeDelta() if attr in ("budget", "budgetLeft", "timeSpent") else 0
        )
        return getTaskAttribute


class TimelineRootNode(RootNode):
    """
    Classe représentant la racine de l'arborescence dans une vue chronologique des tâches.
    """
    def children(self, recursive=False):
        children = super().children(recursive)
        children.sort(key=lambda task_: task_.plannedStartDateTime())
        return children

    def parallel_children(self, recursive=False):
        return self.children(recursive)

    def sequential_children(self):
        return []

    def plannedStartDateTime(self, recursive=False):
        plannedStartDateTimes = [
            item.plannedStartDateTime(recursive=True)
            for item in self.parallel_children()
        ]
        plannedStartDateTimes = [
            dt for dt in plannedStartDateTimes if dt != date.DateTime()
        ]
        if not plannedStartDateTimes:
            plannedStartDateTimes.append(date.Now())
        return min(plannedStartDateTimes)

    def dueDateTime(self, recursive=False):
        dueDateTimes = [
            item.dueDateTime(recursive=True) for item in self.parallel_children()
        ]
        dueDateTimes = [dt for dt in dueDateTimes if dt != date.DateTime()]
        if not dueDateTimes:
            dueDateTimes.append(date.Tomorrow())
        return max(dueDateTimes)


class TimelineViewer(BaseTaskTreeViewer):
    """
    Visualiseur de la chronologie des tâches.
    """
    defaultTitle = _("Timeline")
    defaultBitmap = "timelineviewer"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("settingsSection", "timelineviewer")
        super().__init__(*args, **kwargs)
        for eventType in (
                task.Task.subjectChangedEventType(),
                task.Task.plannedStartDateTimeChangedEventType(),
                task.Task.dueDateTimeChangedEventType(),
                task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType
                )

    # def createWidget(self):
    def createWidget(self, parent):
        self.rootNode = TimelineRootNode(self.presentation())
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        self.timeline_widget = widgetstk.timelinetk.TimelineTk(  # À adapter car widgets.Timeline a été converti
            self,
            # parent,
            self.rootNode,
            self.onSelect,
            self.onEdit,
            itemPopupMenu,
        )
        # # Place le widget de chronologie dans la fenêtre
        # timeline_widget.GetCanvas().pack(padx=10, pady=10, expand=True, fill="both")
        return self.timeline_widget
        # return self.widget
        return None

    def onEdit(self, item):
        edit = uicommand.Edit(viewer=self)
        edit(item)

    def curselection(self):
        # Override curselection
        # return self.widget.curselection()  # À adapter
        return self.timeline_widget.curselection()
        # TODO : Pourquoi self.widget est NoneType  ?
        # return None

    def bounds(self, item):
        times = [self.start(item), self.stop(item)]
        for child in self.parallel_children(item) + self.sequential_children(item):
            times.extend(self.bounds(child))
        times = [time for time in times if time is not None]
        return (min(times), max(times)) if times else []

    def start(self, item, recursive=False):
        try:
            start = item.plannedStartDateTime(recursive=recursive)
            if start == date.DateTime():
                return None
        except AttributeError:
            start = item.getStart()
        return start.toordinal()

    def stop(self, item, recursive=False):
        try:
            if item.completed():
                stop = item.completionDateTime(recursive=recursive)
            else:
                stop = item.dueDateTime(recursive=recursive)
            if stop == date.DateTime():
                return None
            else:
                stop += date.ONE_DAY
        except AttributeError:
            stop = item.getStop()
        if not stop:
            return None
        return stop.toordinal()

    def sequential_children(self, item):
        try:
            return item.efforts()
        except AttributeError:
            return []

    def parallel_children(self, item, recursive=False):
        try:
            children = [
                child
                for child in item.get_domain_children(recursive=recursive)
                if child in self.presentation()
            ]
            children.sort(key=lambda task_: task_.plannedStartDateTime())
            return children
        except AttributeError:
            return []

    def foreground_color(self, item, depth=0):
        return item.foregroundColor(recursive=True)

    def background_color(self, item, depth=0):
        return item.backgroundColor(recursive=True)

    def font(self, item, depth=0):
        return item.font(recursive=True)

    def icon(self, item, isSelected=False):
        bitmap = self.iconName(item, isSelected)
        # return wx.ArtProvider.GetIcon(bitmap, wx.ART_MENU, (16, 16)) # À adapter
        return None

    def now(self):
        return date.Now().toordinal()

    def nowlabel(self):
        return _("Now")

    def getItemTooltipData(self, item):
        if isinstance(item, task.Task):
            result = super().getItemTooltipData(item)
        else:
            result = [
                (
                    None,
                    [
                        render.dateTimePeriod(
                            item.getStart(), item.getStop(), humanReadable=True
                        )
                    ],
                )
            ]
            if item.description():
                result.append(
                    (
                        None,
                        [
                            line.rstrip("\n")
                            for line in item.description().split("\n")
                        ],
                    )
                )
        return result


class SquareTaskViewer(BaseTaskTreeViewer):
    """
    Visualiseur des tâches sous forme de carte carrée.
    """
    defaultTitle = _("Task square map")
    defaultBitmap = "squaremapviewer"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("settingsSection", "squaretaskviewer")
        self.__orderBy = "revenue"
        self.__transformTaskAttribute = lambda x: x
        self.__zero = 0
        self.renderer = dict(
            budget=render.budget,
            timeSpent=self._renderTimeSpent,
            fixedFee=render.monetaryAmount,
            revenue=render.monetaryAmount,
            priority=render.priority,
        )
        super().__init__(*args, **kwargs)
        sortKeys = eval(self.settings.get(self.settingsSection(), "sortby"))
        orderBy = sortKeys[0] if sortKeys else "budget"
        self.orderBy(sortKeys[0] if sortKeys else "budget")
        pub.subscribe(
            self.on_order_by_changed,
            "settings.%s.sortby" % self.settingsSection(),
            )
        self.orderUICommand.setChoice(self.__orderBy)

        for eventType in (
                task.Task.subjectChangedEventType(),
                task.Task.dueDateTimeChangedEventType(),
                task.Task.plannedStartDateTimeChangedEventType(),
                task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType
                )

    def curselectionIsInstanceOf(self, class_):
        return class_ == task.Task

    # def createWidget(self):
    def createWidget(self, parent):
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        # return widgetstk.SquareMap(  # TODO À adapter car widgets.SquareMap n'a pas été converti puisqu'il utilise un module squaremap de wxpython !
        #     self,
        #     SquareMapRootNode(self.presentation()),
        #     self.onSelect,
        #     uicommand.Edit(viewer=self),
        #     itemPopupMenu,
        # )
        return None

    def createModeToolBarUICommands(self):
        self.orderUICommand = uicommand.SquareTaskViewerOrderChoice(
            viewer=self, settings=self.settings
        )
        return super().createModeToolBarUICommands() + (self.orderUICommand,)

    def hasModes(self):
        return True

    def getModeUICommands(self):
        return [_("Lay out tasks by"), None] + [
            uicommand.SquareTaskViewerOrderByOption(
                menuText=menuText,
                value=value,
                viewer=self,
                settings=self.settings,
            )
            for (menuText, value) in zip(
                uicommand.SquareTaskViewerOrderChoice.choiceLabels,
                uicommand.SquareTaskViewerOrderChoice.choiceData,
            )
        ]

    def on_order_by_changed(self, value):
        self.orderBy(value)

    def orderBy(self, choice):
        if choice == self.__orderBy:
            return
        oldChoice = self.__orderBy
        self.__orderBy = choice
        try:
            oldEventType = getattr(task.Task, "%sChangedEventType" % oldChoice)()
        except AttributeError:
            oldEventType = "task.%s" % oldChoice
        if oldEventType.startswith("pubsub"):
            try:
                pub.unsubscribe(self.onAttributeChanged, oldEventType)
            except pub.TopicNameError:
                pass  # Can happen on first call to orderBy
        else:
            self.removeObserver(self.onAttributeChanged_Deprecated, oldEventType)
        try:
            newEventType = getattr(task.Task, "%sChangedEventType" % choice)()
        except AttributeError:
            newEventType = "task.%s" % choice
        if newEventType.startswith("pubsub"):
            pub.subscribe(self.onAttributeChanged, newEventType)
        else:
            self.registerObserver(self.onAttributeChanged_Deprecated, newEventType)
        if choice in ("budget", "timeSpent"):
            self.__transformTaskAttribute = lambda timeSpent: timeSpent.milliseconds() // 1000
            self.__zero = date.TimeDelta()
        else:
            self.__transformTaskAttribute = lambda x: x
            self.__zero = 0
        self.refresh()

    def curselection(self):
        # Override curselection
        return self.widget.curselection()  # À adapter
        # return None

    def nrOfVisibleTasks(self):
        return len(
            [
                eachTask
                for eachTask in self.presentation()
                if getattr(eachTask, self.__orderBy)(recursive=True) > self.__zero
            ]
        )

    def overall(self, task_):
        return self.__transformTaskAttribute(
            max(getattr(task_, self.__orderBy)(recursive=True), self.__zero)
        )

    def children_sum(self, children, parent):
        children_sum = sum(
            (
                max(
                    getattr(child, self.__orderBy)(recursive=True), self.__zero
                )
                for child in children
                if child in self.presentation()
            ),
            self.__zero,
        )
        return self.__transformTaskAttribute(max(children_sum, self.__zero))

    def empty(self, task_):
        overall = self.overall(task_)
        if overall:
            children_sum = self.children_sum(self.get_domain_children(task_), task_)
            return max(
                self.__transformTaskAttribute(self.__zero),
                (overall - children_sum),
            ) / float(overall)
        return 0

    def getItemText(self, task_):
        log.debug()
        text = super().getItemText(task_)
        value = self.render(getattr(task_, self.__orderBy)(recursive=False))
        return f"{text} ({value})" if value else text

    def value(self, task_, parent=None):
        return self.overall(task_)

    def foreground_color(self, task_, depth):
        return task_.foregroundColor(recursive=True)

    def background_color(self, task_, depth):
        red = blue = 255 - (depth * 3) % 100
        green = 255 - (depth * 2) % 100
        # color = wx.Colour(red, green, blue) # À adapter
        color = None
        return task_.backgroundColor(recursive=True) or color

    def font(self, task_, depth):
        return task_.font(recursive=True)

    def icon(self, task_, isSelected):
        bitmap = self.iconName(task_, isSelected) or "led_blue_icon"
        # return wx.ArtProvider.GetIcon(bitmap, wx.ART_MENU, (16, 16)) # TODO : À adapter
        return None

    def render(self, value):
        return self.renderer[self.__orderBy](value)


# Parfait ! J'ai converti la classe HierarchicalCalendarViewer pour Tkinter avec les améliorations suivantes :
# Principales conversions effectuées :
#
# Imports mis à jour : Utilisation de mixintk au lieu de mixin
# Gestion des erreurs robuste : Try/except partout pour gérer les widgets non encore convertis
# Méthode reconfig() :
#
# Vérification de l'existence du widget avant configuration
# Gestion des erreurs pour chaque paramètre
#
#
# Méthode configure() :
#
# Remplacement de CentreOnParent() par transient()
# Remplacement de ShowModal() par wait_window()
# Fallback avec messagebox si le dialogue n'est pas disponible
#
#
# Méthode createWidget() :
#
# Tentative d'import du widget hcalendartk.HierarchicalCalendar
# Fallback intelligent avec 3 niveaux :
#
# Essai avec le widget personnalisé
# Essai avec tkcalendar.Calendar (module externe)
# Affichage d'un message si rien n'est disponible
#
#
#
#
# Méthode _on_date_selected() : Nouvelle méthode pour gérer la sélection de date dans le calendrier de substitution
# Méthodes onEdit() et onCreate() : Ajout de gestion d'erreurs avec messagebox
# Méthode GetPrintout() : Gestion gracieuse si l'impression n'est pas disponible
# Logging : Ajout de messages de log pour le débogage
class HierarchicalCalendarViewer(
    mixintk.AttachmentDropTargetMixin,
    mixintk.SortableViewerForTasksMixin,
    BaseTaskTreeViewer,
):
    """
    Visualiseur de calendrier hiérarchique.

    Affiche les tâches dans un calendrier hiérarchisé en fonction de leurs dates de début
    et d'échéance.

    Méthodes :
        createWidget (self) :
            Crée le widget du calendrier hiérarchique.
        onEdit (self, item) :
            Permet l'édition des tâches directement depuis la vue du calendrier.
        onCreate (self, dateTime, show=True) :
            Crée une nouvelle tâche à une date spécifique.
        atMidnight (self) :
            Rafraîchit le calendrier à minuit pour mettre à jour les dates.
    """
    defaultTitle = _("Hierarchical calendar")
    defaultBitmap = "calendar_icon"

    def __init__(self, *args, **kwargs):
        """Initialise le visualiseur de calendrier hiérarchique."""
        kwargs.setdefault("settingsSection", "hierarchicalcalendarviewer")
        super().__init__(*args, **kwargs)

        log.debug("HierarchicalCalendarViewer : Initialisation")

        # Enregistrement des observateurs pour les changements d'attributs
        for eventType in (
                task.Task.subjectChangedEventType(),
                task.Task.attachmentsChangedEventType(),
                task.Task.notesChangedEventType(),
                task.Task.trackingChangedEventType(),
                task.Task.percentageCompleteChangedEventType(),
        ):
            if eventType is not None and eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(self.onAttributeChanged_Deprecated, eventType)

        # Les dates sont traitées séparément car la mise en page peut changer
        for eventType in (
                task.Task.plannedStartDateTimeChangedEventType(),
                task.Task.dueDateTimeChangedEventType(),
                task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onLayoutAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onLayoutAttributeChanged_Deprecated, eventType
                )

        # Configuration initiale
        self.reconfig()

        # Planification du rafraîchissement à minuit
        try:
            date.Scheduler().schedule_interval(self.atMidnight, days=1)
        except Exception as e:
            log.warning(f"Impossible de planifier le rafraîchissement à minuit: {e}")

        log.debug("HierarchicalCalendarViewer : Initialisé")

    def reconfig(self):
        """Reconfigure le calendrier avec les paramètres actuels."""
        try:
            if hasattr(self, 'widget') and self.widget:
                # Configuration du format du calendrier
                calendar_format = self.settings.getint(
                    self.settingsSection(), "calendarformat"
                )
                if hasattr(self.widget, 'SetCalendarFormat'):
                    self.widget.SetCalendarFormat(calendar_format)

                # Configuration du format de l'en-tête
                header_format = self.settings.getint(
                    self.settingsSection(), "headerformat"
                )
                if hasattr(self.widget, 'SetHeaderFormat'):
                    self.widget.SetHeaderFormat(header_format)

                # Configuration de l'affichage de "maintenant"
                draw_now = self.settings.getboolean(
                    self.settingsSection(), "drawnow"
                )
                if hasattr(self.widget, 'SetDrawNow'):
                    self.widget.SetDrawNow(draw_now)

                # Configuration de la couleur du jour actuel
                today_color_str = self.settings.get(
                    self.settingsSection(), "todaycolor"
                )
                if today_color_str and hasattr(self.widget, 'SetTodayColor'):
                    try:
                        today_color = list(map(int, today_color_str.split(",")))
                        self.widget.SetTodayColor(today_color)
                    except (ValueError, AttributeError) as e:
                        log.warning(f"Couleur du jour invalide: {e}")
        except Exception as e:
            log.error(f"Erreur lors de la reconfiguration du calendrier: {e}")

    def configure(self):
        """Ouvre le dialogue de configuration du calendrier hiérarchique."""
        try:
            if HierarchicalCalendarConfigDialog is None:
                messagebox.showwarning(
                    _("Non disponible"),
                    _("Le dialogue de configuration n'est pas encore disponible.")
                )
                return

            dialog_window = HierarchicalCalendarConfigDialog(
                self.settings,
                self.settingsSection(),
                self,
                title=_("Hierarchical calendar viewer configuration"),
            )

            # Centrer sur le parent (Tkinter)
            if hasattr(dialog_window, 'transient'):
                dialog_window.transient(self.winfo_toplevel())

            # Afficher le dialogue de manière modale
            if hasattr(dialog_window, 'wait_window'):
                dialog_window.wait_window()
                # Vérifier si OK a été cliqué (à implémenter dans le dialogue)
                if hasattr(dialog_window, 'result') and dialog_window.result:
                    self.reconfig()
            else:
                # Fallback si pas de dialogue modal
                self.reconfig()

        except Exception as e:
            log.error(f"Erreur lors de l'ouverture du dialogue de configuration: {e}")
            messagebox.showerror(
                _("Erreur"),
                f"Impossible d'ouvrir le dialogue de configuration:\n{e}"
            )

    def createModeToolBarUICommands(self):
        """Crée les commandes UI pour la barre d'outils (modes calendrier)."""
        return super().createModeToolBarUICommands() + (
            None,
            uicommand.HierarchicalCalendarViewerConfigure(viewer=self),
            uicommand.HierarchicalCalendarViewerPreviousPeriod(viewer=self),
            uicommand.HierarchicalCalendarViewerToday(viewer=self),
            uicommand.HierarchicalCalendarViewerNextPeriod(viewer=self),
        )

    def detach(self):
        """Détache le visualiseur et annule les rafraîchissements planifiés."""
        super().detach()
        try:
            date.Scheduler().unschedule(self.atMidnight)
        except Exception as e:
            log.warning(f"Erreur lors de l'annulation du rafraîchissement: {e}")

    def atMidnight(self):
        """Rafraîchit le calendrier à minuit pour mettre à jour les dates."""
        try:
            if hasattr(self, 'widget') and self.widget:
                if hasattr(self.widget, 'CalendarFormat'):
                    current_format = self.widget.CalendarFormat()
                    if hasattr(self.widget, 'SetCalendarFormat'):
                        self.widget.SetCalendarFormat(current_format)
        except Exception as e:
            log.warning(f"Erreur lors du rafraîchissement à minuit: {e}")

    def onLayoutAttributeChanged(self, newValue, sender):
        """Gère les changements d'attributs de mise en page (pubsub)."""
        self.refresh()

    def onLayoutAttributeChanged_Deprecated(self, event):
        """Gère les changements d'attributs de mise en page (obsolète)."""
        self.refresh()

    def isTreeViewer(self):
        """Indique que ce visualiseur est en mode arborescence."""
        return True

    def onEverySecond(self, event):
        """Désactivé pour ce visualiseur (trop coûteux en performance)."""
        pass

    # def createWidget(self):
    def createWidget(self, parent):
        """Crée le widget du calendrier hiérarchique.

        widget à packer !"""
        log.debug("HierarchicalCalendarViewer.createWidget : Création du widget.")

        # Création du menu contextuel
        itemPopupMenu = self.createTaskPopupMenu()
        if itemPopupMenu:
            self._popupMenus.append(itemPopupMenu)

        try:
            # Tentative de création avec le widget HierarchicalCalendar
            from taskcoachlib.widgetstk import hcalendartk

            widget = hcalendartk.HierarchicalCalendar(
                self,
                parent,  # ou self.parent ?
                self.presentation(),
                self.onSelect,
                self.onEdit,
                self.onCreate,
                itemPopupMenu,
                **self.widgetCreationKeywordArguments()
            )

            log.debug("HierarchicalCalendarViewer.createWidget : Widget créé avec succès")
            return widget

        except (ImportError, AttributeError) as e:
            log.warning(f"HierarchicalCalendar non disponible: {e}")

            # Fallback sur un widget de substitution
            widget = ttk.Frame(self)
            widget.pack(expand=True, pady=20)  # TODO à revoir
            # Création d'un calendrier basique avec tkcalendar si disponible
            try:
                from tkcalendar import Calendar

                calendar = Calendar(
                    widget,
                    selectmode='day',
                    date_pattern='yyyy-mm-dd'
                )
                calendar.pack(fill="both", expand=True)

                # Ajout d'un label d'information
                info_label = ttk.Label(
                    widget,
                    text=_("Calendrier hiérarchique (version simplifiée)"),
                    foreground="gray"
                )
                info_label.pack(pady=5)

                # Binding pour la sélection de date
                calendar.bind("<<CalendarSelected>>", self._on_date_selected)

                # Stockage de la référence au calendrier
                widget._calendar = calendar

            except ImportError:
                # Si tkcalendar n'est pas disponible, afficher un message
                label = ttk.Label(
                    widget,
                    text=_("Le widget de calendrier hiérarchique n'est pas disponible.\n"
                           "Installez le module 'tkcalendar' pour une fonctionnalité basique."),
                    justify=tk.CENTER
                )
                label.pack(expand=True, pady=20)

            return widget

    def _on_date_selected(self, event):
        """Gère la sélection d'une date dans le calendrier de substitution."""
        try:
            if hasattr(self.widget, '_calendar'):
                selected_date = self.widget._calendar.get_date()
                log.debug(f"Date sélectionnée: {selected_date}")
                # Ici, on pourrait afficher les tâches pour cette date
        except Exception as e:
            log.warning(f"Erreur lors de la sélection de date: {e}")

    def onEdit(self, item):
        """Permet l'édition d'une tâche directement depuis la vue du calendrier."""
        try:
            edit = uicommand.Edit(viewer=self)
            edit(item)
        except Exception as e:
            log.error(f"Erreur lors de l'édition de la tâche: {e}")
            messagebox.showerror(
                _("Erreur"),
                f"Impossible d'éditer la tâche:\n{e}"
            )

    def onCreate(self, dateTime, show=True):
        """
        Crée une nouvelle tâche à une date spécifique.

        Args:
            dateTime: Date/heure de la tâche
            show: Afficher le dialogue d'édition

        Returns:
            La commande de création exécutée
        """
        try:
            # Déterminer les dates de début et de fin
            plannedStartDateTime = dateTime

            # Si la date est au début du jour, définir l'échéance à la fin du jour
            if dateTime == dateTime.startOfDay():
                dueDateTime = dateTime.endOfDay()
            else:
                dueDateTime = dateTime

            # Créer la commande de création de tâche
            create = uicommand.TaskNew(
                taskList=self.presentation(),
                settings=self.settings,
                taskKeywords=dict(
                    plannedStartDateTime=plannedStartDateTime,
                    dueDateTime=dueDateTime
                ),
            )

            # Exécuter la commande
            return create(event=None, show=show)

        except Exception as e:
            log.error(f"Erreur lors de la création de la tâche: {e}")
            messagebox.showerror(
                _("Erreur"),
                f"Impossible de créer la tâche:\n{e}"
            )
            return None

    def isAnyItemExpandable(self):
        """Aucun élément n'est extensible dans la vue calendrier."""
        return False

    def isAnyItemCollapsable(self):
        """Aucun élément n'est repliable dans la vue calendrier."""
        return False

    def GetPrintout(self, settings):
        """
        Retourne un objet imprimable basé sur le contenu affiché du calendrier.

        Args:
            settings: Paramètres d'impression

        Returns:
            Objet imprimable ou None si non disponible
        """
        try:
            if hasattr(self.widget, 'GetPrintout'):
                return self.widget.GetPrintout(settings)
            else:
                log.warning("La fonction d'impression n'est pas disponible pour ce widget")
                return None
        except Exception as e:
            log.error(f"Erreur lors de la génération de l'impression: {e}")
            return None


# Points importants à adapter/implémenter :
#
# Remplacer widgets.Calendar :  C'est le point central. Il faut trouver ou créer un widget calendrier Tkinter qui offre des fonctionnalités similaires (affichage par jour/semaine/mois, gestion des événements, etc.).  Le module tkcalendar est une option, mais il faudra peut-être l'adapter pour correspondre aux besoins spécifiques de TaskCoach.  Sinon, il faudra construire un calendrier "from scratch" avec les widgets Tkinter de base.
# Gestion des dates : wx.DateTime est spécifique à wxPython. Il faut utiliser les objets datetime de Python, et les adapter pour qu'ils fonctionnent avec le widget calendrier Tkinter choisi.
# date.Scheduler :  Il faut trouver un moyen de planifier l'appel de self.atMidnight avec Tkinter. On peut utiliser self.after() pour exécuter une fonction après un certain délai.  Il faudra calculer le délai jusqu'à minuit.
# CalendarConfigDialog : Cette classe n'a pas été convertie, il faut donc l'adapter en Tkinter.
# Méthodes SetViewType, SetPeriodCount, SetStyle, SetShowNoStartDate, etc. :  Ces méthodes agissent sur le widget calendrier. Il faut trouver les équivalents dans Tkinter, ou les implémenter si on crée un calendrier personnalisé.
# Freeze et Thaw : Ces méthodes sont utilisées pour optimiser les mises à jour de l'interface. Avec Tkinter, on peut utiliser widget.update_idletasks() pour forcer la mise à jour de l'écran.

class CalendarViewer(
    mixintk.AttachmentDropTargetMixin,
    mixintk.SortableViewerForTasksMixin,
    BaseTaskTreeViewer,
):
    """
    Classe d'affichage des tâches sous forme de calendrier.

    Hérite de :
    - AttachmentDropTargetMixin : permet le glisser-déposer de pièces jointes,
    - SortableViewerForTasksMixin : tri des tâches par colonnes,
    - BaseTaskTreeViewer : base des vues arborescentes de tâches (même si ici ce n'est pas un arbre).

    Cette vue permet de visualiser les tâches sur une période, avec personnalisation
    du nombre de périodes, du style, de l'orientation, etc. L'utilisateur peut aussi
    configurer les couleurs, l'affichage du "maintenant", et d'autres filtres.
    """
    defaultTitle = _("Calendar")
    defaultBitmap = "calendar_icon"

    def __init__(self, *args, **kwargs):
        """
        Initialise la vue calendrier avec les paramètres et préférences utilisateurs :
        - Restaure la date de vue si enregistrée,
        - Applique le jour de début de semaine,
        - Configure les heures de travail et les préférences d'affichage,
        - S'abonne aux modifications des tâches et des paramètres.
        """
        kwargs.setdefault("settingsSection", "calendarviewer")
        kwargs["doRefresh"] = False
        super().__init__(*args, **kwargs)

        start = self.settings.get(self.settingsSection(), "viewdate")
        # if start: # start n'est pas au format tk
        #     dt = wx.DateTime.Now()
        #     dt.ParseDateTime(start)
        #     self.widget.SetDate(dt)

        self.onWeekStartChanged(self.settings.gettext("view", "weekstart"))
        self.onWorkingHourChanged()

        self.reconfig()
        # self.widget.SetPeriodWidth( # Pas de widget avant createWidget
        #     self.settings.getint(self.settingsSection(), "periodwidth")
        # )

        for eventType in ("start", "end"):
            pub.subscribe(
                self.onWorkingHourChanged, "settings.view.efforthour%s" % eventType
            )
        pub.subscribe(self.onWeekStartChanged, "settings.view.weekstartmonday")

        # pylint: disable=E1101
        for eventType in (
                task.Task.subjectChangedEventType(),
                task.Task.plannedStartDateTimeChangedEventType(),
                task.Task.dueDateTimeChangedEventType(),
                task.Task.completionDateTimeChangedEventType(),
                task.Task.attachmentsChangedEventType(),
                task.Task.notesChangedEventType(),
                task.Task.trackingChangedEventType(),
                task.Task.percentageCompleteChangedEventType(),
        ):
            # Si tu veux savoir D’OÙ vient ce eventType None pour corriger à la source,
            # donne le code où eventType est défini ou passé à ce constructeur,
            # il est possible de sécuriser toute la chaîne.
            if isinstance(eventType, str) and eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(self.onAttributeChanged_Deprecated, eventType)
                # date.Scheduler().schedule_interval(self.atMidnight, days=1) #  A adapter avec tkinter et non date

    def detach(self):
        """
        Méthode appelée lors du détachement de la vue.
        Annule la tâche planifiée qui met à jour la vue à minuit.
        """
        super().detach()
        # date.Scheduler().unschedule(self.atMidnight) # A adapter

    def isTreeViewer(self):
        """
        Indique que cette vue n'est pas une arborescence (contrairement aux autres vues héritées).
        :return: False
        """
        return False

    def onEverySecond(self, event):  # pylint: disable=W0221,W0613
        """
        Surcharge inactive : inutile ici car coûteuse en performances.
        """
        pass  # Too expensive

    def atMidnight(self):
        """
        Appelée automatiquement chaque jour à minuit.
        Met à jour la vue si elle est configurée pour afficher la date actuelle.
        """
        if not self.settings.get(self.settingsSection(), "viewdate"):
            # User has selected the "current" Date/time; it may have
            # changed Now
            self.SetViewType(SCHEDULER_TODAY)

    def onWorkingHourChanged(self, value=None):  # pylint: disable=W0613
        """
        Applique les heures de travail (début et fin) à la vue calendrier.
        Utilisé lorsque l'utilisateur modifie les paramètres.
        """
        # self.widget.SetWorkHours( # Pas de widget
        #     self.settings.getint("view", "efforthourstart"),
        #     self.settings.getint("view", "efforthourend"),
        # )
        pass

    def onWeekStartChanged(self, value):
        """
        Change le jour de début de semaine dans le calendrier (lundi ou dimanche).
        :param value: 'monday' ou 'sunday'
        """
        assert value in ("monday", "sunday")
        # if value == "monday": # Pas de widget
        #     self.widget.SetWeekStartMonday()
        # else:
        #     self.widget.SetWeekStartSunday()
        pass

    # def createWidget(self):
    def createWidget(self, parent):
        """
        Crée le widget principal (vue calendrier) avec son menu contextuel.
        Applique aussi un style de dessin personnalisé (gradient) si activé.
        :return: instance de Calendar (widgets.Calendar)

        TODO utiliser pack !?  c'est fait dans factorytk !
        """
        log.info("CalendarViewer.createWidget : Crée le widget principal avec son menu contextuel.")
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)

        # TODO: Implémenter un calendrier avec Tkinter (ttkcalendar ?)
        # Pour l'instant, on utilise un simple Label pour placeholder
        # self.calendar_widget = tk.Label(self, text="Calendrier Tkinter à implémenter")
        widget = widgetstk.calendarwidgettk.Calendar(  # Est-il bien configuré ?
            self,
            parent,  # ou self.parent ?
            self.presentation(),
            self.iconName,
            self.onSelect,
            self.onEdit,
            self.onCreate,
            self.onChangeConfig,
            itemPopupMenu,
            **self.widgetCreationKeywordArguments()
        )

        # widget.SetDrawHeaders(True)  # <- Active l'affichage des numéros de jour # A voir comment faire
        # if self.settings.getboolean("calendarviewer", "gradient"):
        #     # If called directly, we crash with a Cairo assert failing...
        #     log.debug("CalendarViewer.createWidget : Lance un CallAfter avec widgets.Calendar.SetDrawer et wxFancyDrawer.")
        #     wx.CallAfter(widget.SetDrawer, wxFancyDrawer)
        #     log.debug("CalendarViewer.createWidget : CallAfter avec widgets.Calendar.SetDrawer et wxFancyDrawer est passé ! Terminé et pass !")
        #     # pass

        # log.info(f"CalendarViewer.createWidget : Renvoie widget à {self}.")
        # return self.calendar_widget
        return widget

    def onChangeConfig(self):
        """
        Enregistre la largeur de période actuelle dans les paramètres après modification de la configuration.
        """
        # self.settings.set( # A adapter si on conserve une notion de taille de période
        #     self.settingsSection(), "periodwidth", str(self.widget.GetPeriodWidth())
        # )
        pass

    def onEdit(self, item):
        """
        Ouvre la fenêtre d'édition d'une tâche.
        :param item: tâche à éditer
        """
        edit = uicommand.Edit(viewer=self)
        edit(item)

    def onCreate(self, dateTime, show=True):
        """
        Crée une nouvelle tâche à une date donnée.

        :param dateTime: Date/heure de début planifiée.
        :param show: Affiche la tâche après création si True.
        :return: objet uicommand.TaskNew exécuté.
        """
        plannedStartDateTime = dateTime
        # dueDateTime = ( # A revoir
        #     dateTime.endOfDay() if dateTime == dateTime.startOfDay() else dateTime
        # )
        create = uicommand.TaskNew(
            taskList=self.presentation(),
            settings=self.settings,
            taskKeywords=dict(
                plannedStartDateTime=plannedStartDateTime  # , dueDateTime=dueDateTime # A revoir
            ),
        )
        return create(event=None, show=show)

    def createModeToolBarUICommands(self):
        """
        Ajoute les commandes spécifiques à la vue calendrier dans la barre d’outils :
        configuration, période précédente, aujourd’hui, période suivante.
        :return: tuple de commandes UI.
        """
        return super().createModeToolBarUICommands() + (
            None,
            uicommand.CalendarViewerConfigure(viewer=self),
            uicommand.CalendarViewerPreviousPeriod(viewer=self),
            uicommand.CalendarViewerToday(viewer=self),
            uicommand.CalendarViewerNextPeriod(viewer=self),
        )

    def SetViewType(self, type_):
        """
        Définit le type de vue du calendrier (jour, semaine, mois, etc.)
        et enregistre la date affichée dans les paramètres.
        """
        # self.widget.SetViewType(type_) # TODO : A adapter
        # dt = self.widget.GetDate() # A adapter
        # now = wx.DateTime.Today() # A adapter
        # if (dt.GetYear(), dt.GetMonth(), dt.GetDay()) == (
        #     now.GetYear(),
        #     now.GetMonth(),
        #     now.GetDay(),
        # ):
        #     toSave = ""
        # else:
        #     toSave = dt.Format()
        # self.settings.set(self.settingsSection(), "viewdate", toSave)
        pass

        # We need to override these because BaseTaskTreeViewer is a tree viewer, but
    # CalendarViewer is not. There is probably a better solution...

    def isAnyItemExpandable(self):
        """
        Aucun élément n'est extensible dans une vue calendrier.
        """
        return False

    def isAnyItemCollapsable(self):
        """
        Aucun élément n'est repliable dans une vue calendrier.
        """
        return False

    def reconfig(self):
        """
        Applique la configuration de l'utilisateur à la vue :
        - Nombre de périodes affichées
        - Type et orientation de la vue
        - Affichage des tâches sans dates
        - Affichage du moment présent
        - Couleur de surbrillance
        """
        # self.widget.Freeze()
        try:
            # self.widget.SetPeriodCount( # TODO : A adapter
            #     self.settings.getint(self.settingsSection(), "periodcount")
            # )
            # self.widget.SetViewType( # A adapter
            #     self.settings.getint(self.settingsSection(), "viewtype")
            # )
            # self.widget.SetStyle( # A adapter
            #     self.settings.getint(self.settingsSection(), "vieworientation")
            # )
            # self.widget.SetShowNoStartDate( # A adapter
            #     self.settings.getboolean(self.settingsSection(), "shownostart")
            # )
            # self.widget.SetShowNoDueDate( # A adapter
            #     self.settings.getboolean(self.settingsSection(), "shownodue")
            # )
            # self.widget.SetShowUnplanned( # A adapter
            #     self.settings.getboolean(self.settingsSection(), "showunplanned")
            # )
            # self.widget.SetShowNow( # A adapter
            #     self.settings.getboolean(self.settingsSection(), "shownow")
            # )

            # hcolor = self.settings.get(self.settingsSection(), "highlightcolor") # A adapter
            # if hcolor:
            #     highlightColor = wx.Colour(*tuple([int(c) for c in hcolor.split(",")]))
            #     self.widget.SetHighlightColor(highlightColor)
            # self.widget.RefreshAllItems(0)
            pass
        finally:
            # self.widget.Thaw()
            pass

    def configure(self):
        """
         Affiche la boîte de dialogue de configuration de la vue calendrier.
         Applique les changements si l'utilisateur clique sur OK.
         """
        dialog_ = CalendarConfigDialog(  # A adapter : CalendarConfigDialog n'a pas été converti
            self.settings,
            self.settingsSection(),
            self,
            title=_("Calendar viewer configuration"),
        )
        # dialog_.CentreOnParent()
        # if dialog_.ShowModal() == wx.ID_OK:
        #     self.reconfig()
        pass

    def GetPrintout(self, settings):
        """
        Retourne un objet imprimable basé sur le contenu affiché du calendrier.

        :param settings: paramètres d'impression
        :return: objet wx.Printout
        """
        # return self.widget.GetPrintout(settings) # A adapter
        pass


    # ============================================================================
# Visualiseur principal des tâches
# ============================================================================

# class Taskviewer(ttk.Frame):
# class Taskviewer(Viewer):  # Inherit from Viewer
# class Taskviewer(AttachmentDropTargetMixin, SortableViewerForTasksMixin, NoteColumnMixin, AttachmentColumnMixin, SortableViewerWithColumns, Viewer):  # Inherit from Viewer
# class Taskviewer(Viewer, ViewerContainer):  # Inherit from Viewer
# class Taskviewer(Viewer, SortableViewerWithColumns, AttachmentColumnMixin, NoteColumnMixin, SortableViewerForTasksMixin, AttachmentDropTargetMixin):  # Inherit from Viewer
class Taskviewer(
    # Viewer,
    mixintk.AttachmentDropTargetMixin,
    mixintk.SortableViewerForTasksMixin,
    mixintk.NoteColumnMixin,
    mixintk.AttachmentColumnMixin,
    basetk.SortableViewerWithColumns,
    BaseTaskTreeViewer,
):
    """
    Vue principale des tâches pour Tkinter.

    Visualiseur de tâches standard dans Task Coach.

    Ce visualiseur affiche les tâches sous forme d'arborescence avec des colonnes
    personnalisables, triables et filtrables. Il permet également de gérer des
    pièces jointes, des notes, et d'effectuer du glisser-déposer pour réorganiser
    les tâches.
    """
    defaultTitle = _("Tasks")
    defaultBitmap = "led_blue_icon"

    # def __init__(self, parent: tk.Tk, settings_obj: settings, task_file: Any, **kwargs: Any):
    # def __init__(self, parent, settings, task_file, **kwargs):
    def __init__(self, *args, **kwargs):
        """Initialise le visualiseur de tâches avec les paramètres fournis."""
        # log.debug(f"Taskviewer.__init__ : La vue principale des tâches.")
        log.debug("TaskViewer.__init__ : Initialisation du visualiseur de tâches.")
        kwargs.setdefault("settingsSection", "taskviewer")
        # super().__init__(parent, **kwargs)
        # super().__init__(parent, task_file, settings, **kwargs)
        super().__init__(*args, **kwargs)
        # # Ensure correct initialization order and pass arguments to all base classes
        # Viewer.__init__(self, parent, task_file, settings, **kwargs)
        # AttachmentDropTargetMixin.__init__(self)
        # SortableViewerForTasksMixin.__init__(self)
        # NoteColumnMixin.__init__(self)
        # AttachmentColumnMixin.__init__(self)
        # SortableViewerWithColumns.__init__(self)

        # # La méthode __init__ appelle désormais explicitement les méthodes __init__
        # # de toutes les classes parentes, y compris les mixins,
        # # dans un ordre spécifique. Cela garantit que chaque classe
        # # de base est correctement initialisée.
        # # Ceci est crucial pour que les mixins fonctionnent correctement.
        # # self.settings = settings_obj
        # self.settings = settings
        # self.taskFile = task_file

        # # self.__viewMode = "tree"   # Défaut
        # # Le mode d'affichage est déterminé par les paramètres
        # self.__viewMode = "tree" if self.isTreeMode() else "list"

        # self.tree = ttk.Treeview(self)
        # self.tree.pack(side="top", fill="both", expand=True)
        #
        # self.columns = self.createColumns()
        # self.tree["columns"] = [c.value for c in self.columns]
        # self.tree.heading("#0", text=_("Sujet"))
        # self.tree.column("#0", width=300)
        #
        # for col in self.columns:
        #     self.tree.heading(col.value, text=col.menuText, command=lambda c=col.value: self._on_column_click(c))
        #     self.tree.column(col.value, width=150)
        #
        # self._populate_tree()
        #
        # self.refresher = refresher.MinuteRefresher(self)
        # Démarrage du rafraîchissement si la colonne temps restant est visible
        if self.isVisibleColumnByName("timeLeft"):
            if hasattr(self, 'minuteRefresher') and self.minuteRefresher:
                self.minuteRefresher.startClock()

        # Abonnement aux changements de mode arbre/liste
        pub.subscribe(
            self.onTreeListModeChanged,
            f"settings.{self.settingsSection()}.treemode"
        )

        # self.tree.bind("<Delete>", self.onDelete)
        # self.tree.bind("<<TreeviewSelect>>", self.on_select)
        #
        # # La création du widget se fait directement dans le constructeur
        # self.createWidget()
        # # self._create_widgets()

        # # self.refresher = refresher.MinuteRefresher(self)
        # self.refresh()
        log.debug(f"Taskviewer.__init__ : La vue principale des tâches est initialisé !")

    # Méthodes à ajouter pour corriger l'erreur de classe abstraite
    # Sauf que bitmap() est dans basetk.Viewer !
    # def bitmap(self):
    #     """Retourne le bitmap de la classe (à implémenter si nécessaire)."""
    #     return None  # Ou une valeur pertinente

    def isShowingAttachments(self):
        """Détermine si le visualiseur affiche les pièces jointes."""
        return False

    def isShowingCategories(self):
        """Détermine si le visualiseur affiche les catégories."""
        return True

    def isShowingEffort(self):
        """Détermine si le visualiseur affiche l'effort."""
        return True

    def isShowingNotes(self):
        """Détermine si le visualiseur affiche les notes."""
        return True

    def isShowingTasks(self):
        """Détermine si le visualiseur affiche les tâches."""
        return True

    # def isTreeViewer(self):
    #     """
    #     Détermine si le visualiseur est en mode arborescence.
    #     (Votre méthode `isTreeMode` est déjà l'équivalent, renommons-la
    #     pour correspondre à la méthode abstraite).
    #     """
    #     return self.isTreeMode()

    def isViewerContainer(self):
        """Indique si la classe est un conteneur de viewers."""
        # return True
        return False

    # # Ancienne méthode renommée pour éviter la confusion
    # def isTreeMode(self):
    #     """Détermine si le visualiseur est en mode arborescence en lisant les paramètres."""
    #     return self.settings.getboolean(self.settingsSection(), "treemode")

    def activate(self):
        """Active le visualiseur et affiche une info-bulle pour le tri manuel."""
        try:
            if hasattr(self.winfo_toplevel(), "AddBalloonTip"):
                self.winfo_toplevel().AddBalloonTip(
                    self.settings,
                    "manualordering",
                    self.widget,
                    title=_("Ordre manuel"),
                    getRect=lambda: (0, 0, 28, 16),
                    message=_(
                        """Affichez la colonne "Ordre manuel", puis glissez-déposez les éléments 
    depuis cette colonne pour les trier arbitrairement."""
                    ),
                )
        except Exception as e:
            log.debug(f"Impossible d'afficher l'info-bulle d'activation: {e}")

    # Le problème exact :
    #
    #     Viewer.__init__ (dans basetk.py) essaie de créer la présentation (self.__presentation = ...).
    #
    #     Pour créer cette présentation, il appelle self.createFilter.
    #
    #     createFilter (dans mixintk.py) a besoin de savoir si on est en mode arbre, donc il appelle self.isTreeViewer().
    #
    #     isTreeViewer (dans tasktk.py) contient une ligne de log : log.debug(f"... {self.presentation().treeMode()}.").
    #
    #     Ce log essaie d'exécuter self.presentation().
    #
    #     self.presentation() (dans basetk.py) essaie de retourner self.__presentation.
    #
    #     CRASH : self.__presentation n'existe pas encore, car nous sommes précisément à l'étape 1 (sa création).
    #
    # La solution : Il faut modifier le fichier tasktk.py pour supprimer l'appel prématuré à presentation() dans le log, et gérer le fait que la présentation n'est pas encore disponible lors de l'initialisation.
    def isTreeViewer(self):
        """
        Détermine si le visualiseur est en mode arborescence en lisant les paramètres.
        Utilise la présentation si elle existe, sinon (pendant l'init) utilise les settings.
        """
        # return self.isTreeMode()
        try:
            # On tente de récupérer le mode depuis la présentation active
            log.debug(f"Taskviewer.isTreeViewer : essaie de renvoyer {self.presentation().treeMode()}.")
            return self.presentation().treeMode()
            # return self.presentation.treeMode()  # ?
        except AttributeError as e:
            # Si self.presentation() échoue (car self.__presentation n'existe pas encore
            # lors de l'initialisation dans Viewer.__init__), on se replie sur les paramètres.
            # Note : On évite absolument de logger self.presentation() ici pour ne pas recréer l'erreur.

            log.debug(f"Taskviewer.isTreeViewer : N'a pas trouvé de treeMode dans {self}.presentation.")
            log.debug("Taskviewer.isTreeViewer : Présentation non prête, lecture depuis les settings.")
            # return self.settings.getboolean(self.settingsSection(), "treemode")
            self_settings = self.settings.getboolean(self.settingsSection(), "treemode")
            log.debug(f"Taskviewer.isTreeViewer : retourne self_settings = {self_settings} pour self={self.__class__.__name__}, self.settings={self.settings} et self.settingsSection={self.settingsSection()} contient bien treemode !")
            return self_settings
            # treeMode_found = self.settings.getboolean(self.settingsSection(), "treemode")
            # log.debug(f"Taskviewer.isTreeViewer : renvoie treeMode_found {treeMode_found}.")
            # return treeMode_found
        # Pourquoi cela corrige le problème ?
        #
        #     Suppression du f-string fatal : J'ai retiré la ligne
        #     log.debug(f"... {self.presentation().treeMode()}.") qui se trouvait avant le try.
        #     C'est elle qui provoquait le crash immédiat en forçant
        #     l'accès à une variable non initialisée.
        #
        #     Gestion de l'initialisation : Lors du démarrage (__init__),
        #     le bloc try va échouer (AttributeError).
        #     Le code passera alors dans le bloc except,
        #     qui ira chercher la valeur treemode directement
        #     dans les fichiers de configuration (self.settings),
        #     ce qui est la procédure correcte
        #     tant que l'interface n'est pas totalement chargée.

    def showColumn(self, column, show=True, *args, **kwargs):
        """Affiche ou masque une colonne et gère le rafraîchissement."""
        if column.name() == "timeLeft":
            if show:
                if hasattr(self, 'minuteRefresher') and self.minuteRefresher:
                    self.minuteRefresher.startClock()
            else:
                if hasattr(self, 'minuteRefresher') and self.minuteRefresher:
                    self.minuteRefresher.stopClock()

        super().showColumn(column, show, *args, **kwargs)

    def curselectionIsInstanceOf(self, class_):
        """Vérifie si la sélection actuelle est une instance de la classe spécifiée."""
        return class_ == task.Task

    # def createWidget(self):
    def createWidget(self, parent):
        # def _create_widgets(self):
        """
        Crée le widget de l'arborescence des tâches et configure les colonnes et les événements.
        Remplace la méthode wxpython `createWidget`.
        """
        log.debug("Taskviewer.createWidget : crée et affiche le widget de l'arborescence des tâches.")
        # Votre code existant pour créer le Treeview est déjà l'équivalent
        # self.tree = ttk.Treeview(self)
        # self.tree.pack(side="top", fill="both", expand=True)

        # Création de la liste d'images
        imageList = self.createImageList()

        # Création des colonnes
        # self.columns = self.createColumns()
        self._columns = self._createColumns()

        # self.tree["columns"] = [c.value for c in self.columns]
        # self.tree.heading("#0", text=_("Sujet"))
        # self.tree.column("#0", width=300)
        # Création des menus contextuels
        itemPopupMenu = self.createTaskPopupMenu()
        columnPopupMenu = self.createColumnPopupMenu()
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        # ... (votre code existant pour préparer les kwargs) ...
        kwargs = self.widgetCreationKeywordArguments()

        # IMPORTANT : Assurez-vous que l'option problématique est retirée soit ici,
        # soit dans treectrltk.py (comme suggéré dans la correction 1, ce qui est plus propre).
        # Si vous n'avez pas encore modifié treectrltk.py, ajoutez la ligne suivante ici :
        # kwargs.pop('resizeableColumn', None)

        # Création du widget principal (TreeListCtrl pour Tkinter)
        try:
            widget = treectrltk.TreeListCtrl(
                self,
                parent,  # ou self.parent ?
                # self.columns(),
                self.visibleColumns(),
                self.onSelect,
                uicommand.Edit(viewer=self),
                uicommand.TaskDragAndDrop(taskList=self.presentation(), viewer=self),
                itemPopupMenu,
                columnPopupMenu,
                resizeableColumn=1 if self.hasOrderingColumn() else 0,
                validateDrag=self.validateDrag,
                # **self.widgetCreationKeywordArguments()
                **kwargs
            )

            # Configuration du widget
            if self.hasOrderingColumn():
                widget.SetMainColumn(1)  # TODO : SetMainColumn est une fonction d'hypertreelist !
                # SetMainColumn(self, column)
                # Définit la colonne principale HyperTreeList (c’est-à-dire la position du CustomTreeCtrl sous-jacent.[ #]
                # Paramètres :
                # colonne – si ce n’est pas Aucun, un entier spécifiant l’index de la colonne. S’il s’agit de None, l’index de la colonne principale est utilisé.

            # Association de la liste d'images
            if imageList:
                # widget.AssignImageList(imageList)
                widget.AssignImageList(imageList)

            # Liaison des événements d'édition
            widget.bind("<<TreeBeginEdit>>", self.onBeginEdit)
            widget.bind("<<TreeEndEdit>>", self.onEndEdit)

        except Exception as e:
            log.error(f"Erreur lors de la création du widget: {e}")
            # Fallback sur un Treeview basique
            widget = ttk.Treeview(self)
            # self.tree = ttk.Treeview(self)
            widget.pack(fill="both", expand=True)
            # self.tree.pack(fill="both", expand=True)

            # self.columns = self.createColumns()
            columns = self.createColumns()

            # self.tree["columns"] = [c.value for c in self.columns]
            widget["columns"] = [c.value for c in columns]
            # widget["columns"] = [c.name() for c in columns]
            # self.tree.heading("#0", text=_("Sujet"))
            widget.heading("#0", text=_("Sujet"))
            # self.tree.column("#0", width=300)
            widget.column("#0", width=300)

            # for col in self._columns:
            for col in columns:
                # self.tree.heading(col.value, text=col.menuText, command=lambda c=col.value: self._on_column_click(c))
                widget.heading(col.value, text=col.menuText, command=lambda c=col.value: self._on_column_click(c))
                # widget.heading(col.name, text=col.header, command=lambda c=col.name: self._on_column_click(c))
                # self.tree.column(col.value, width=150)
                widget.column(col.value, width=150)
                # widget.column(col.name, width=150)

            self._populate_tree()

            # Liaison des événements, remplaçant la logique de `wx.Bind`
            # self.tree.bind("<Delete>", self.onDelete)
            widget.bind("<Delete>", self.onDelete)
            # self.tree.bind("<<TreeviewSelect>>", self.on_select)
            widget.bind("<<TreeviewSelect>>", self.on_select)
            # self.tree.bind("<Button-3>", self.show_context_menu)  # Ajout du menu contextuel
            widget.bind("<Button-3>", self.show_context_menu)  # Ajout du menu contextuel

            # Ajout de la gestion du glisser-déposer (Drag and Drop)
            # self.tree.bind("<ButtonPress-1>", self.on_drag_start)
            widget.bind("<ButtonPress-1>", self.on_drag_start)
            # self.tree.bind("<B1-Motion>", self.on_drag_motion)
            widget.bind("<B1-Motion>", self.on_drag_motion)
            # self.tree.bind("<ButtonRelease-1>", self.on_drop)
            widget.bind("<ButtonRelease-1>", self.on_drop)

        # --- CORRECTION 2 : Assigner le widget à self.tree ---
        # C'est la référence que les méthodes Taskviewer s'attendent à trouver.
        # TODO : à remodifier pour retrouver self.widget !
        self.tree = widget

        # La classe Viewer dans basetk.py s'attend à ce que l'objet soit retourné ou
        # stocké dans self.widget.
        self.widget = widget
        log.debug("Taskviewer.createWidget : Le widget de l'arborescence des tâches est sensé être affiché !")
        log.debug("Taskviewer.createWidget : Widget créé.")
        return widget

    def onBeginEdit(self, event):
        """Gère le début de l'édition d'un élément."""
        if not self.isTreeViewer():
            try:
                treeItem = event.widget.focus()
                if treeItem:
                    editedTask = event.widget.item(treeItem, 'values')[0]
                    event.widget.item(treeItem, text=editedTask.subject())
            except Exception as e:
                log.warning(f"Erreur lors du début d'édition: {e}")

    def onEndEdit(self, event):
        """Gère la fin de l'édition d'un élément."""
        if not self.isTreeViewer():
            try:
                treeItem = event.widget.focus()
                if treeItem:
                    editedTask = event.widget.item(treeItem, 'values')[0]
                    event.widget.item(treeItem, text=editedTask.subject(recursive=True))
            except Exception as e:
                log.warning(f"Erreur lors de la fin d'édition: {e}")

    def show_context_menu(self, event):
        """Affiche un menu contextuel au clic droit."""
        # Un exemple simple. Dans une vraie app, le menu serait plus complexe.
        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(label=_("Ajouter une tâche"), command=lambda: self.onAdd(None))
        menu.add_command(label=_("Supprimer la sélection"), command=lambda: self.onDelete(None))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def on_drag_start(self, event):
        """Démarre le glisser-déposer."""
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            self.drag_item = selected_item
            self.drag_start_y = event.y

    def on_drag_motion(self, event):
        """Gère le déplacement de la souris lors du glisser."""
        # On peut ici ajouter un visuel pour le glissement, comme un rectangle de sélection
        pass

    def on_drop(self, event):
        """Gère l'action de lâcher la tâche."""
        target_item = self.tree.identify_row(event.y)
        if hasattr(self, 'drag_item') and self.drag_item and target_item:
            # Récupère l'ID de la tâche glissée
            drag_item_id = self.drag_item
            # Récupère le parent de la cible
            target_parent_id = self.tree.parent(target_item)

            if drag_item_id != target_item and self.tree.is_ancestor(drag_item_id, target_item) is False:
                # Déplace l'élément de la liste
                self.tree.move(drag_item_id, target_parent_id, self.tree.index(target_item))
                messagebox.showinfo("Action", "Tâche déplacée.")
                self.drag_item = None

        # self.drag_item = None

    def isTreeMode(self):
        """
        Détermine si le visualiseur est en mode arborescence en lisant les paramètres.
        Remplace la méthode wxpython `isTreeViewer`.
        """
        # # return self.settings.getboolean(self.settingsSection(), "treemode")
        # try:
        #     return self.presentation().treeMode()
        #     # return self.__viewMode == "tree"
        # except AttributeError:
        #     return self.settings.getboolean(self.settingsSection(), "treemode")
        return self.__viewMode == "tree"

    def _on_column_click(self, column_name: str):
        """Gère le clic sur l'en-tête d'une colonne."""
        messagebox.showinfo("Tri", f"Tri par colonne: {column_name}")

    def on_select(self, event):
        selected_items = self.tree.selection()
        # Logique pour gérer la sélection d'éléments
        print(f"Éléments sélectionnés : {selected_items}")

    def _createColumns(self):
        """
        Crée les colonnes du visualiseur.
        (createWidget de TaskViewer et CheckableTaskViewer).
        """
        kwargs = dict(resizeCallback=self.onResizeColumn)
        columns = []

        try:
            # Colonne d'ordre manuel
            columns.append(
                itemctrltk.Column(
                    "ordering",
                    "",
                    task.Task.orderingChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="ordering",
                    ),
                    renderCallback=lambda task_: "",
                    imageIndicesCallback=self.orderingImageIndices,
                    width=self.getColumnWidth("ordering"),
                )
            )

            # Colonne sujet
            columns.append(
                itemctrltk.Column(
                    "subject",
                    _("Subject"),
                    task.Task.subjectChangedEventType(),
                    task.Task.completionDateTimeChangedEventType(),
                    task.Task.actualStartDateTimeChangedEventType(),
                    task.Task.dueDateTimeChangedEventType(),
                    task.Task.plannedStartDateTimeChangedEventType(),
                    task.Task.trackingChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="subject"
                    ),
                    width=self.getColumnWidth("subject"),
                    imageIndicesCallback=self.subjectImageIndices,
                    renderCallback=self.renderSubject,
                    editCallback=self.onEditSubject,
                    editControl=inplace_editortk.SubjectCtrl,
                    **kwargs
                )
            )

            # Colonne description
            columns.append(
                itemctrltk.Column(
                    "description",
                    _("Description"),
                    task.Task.descriptionChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="description"
                    ),
                    renderCallback=lambda task_: task_.description(),
                    width=self.getColumnWidth("description"),
                    editCallback=self.onEditDescription,
                    editControl=inplace_editortk.DescriptionCtrl,
                    **kwargs
                )
            )

            # Colonnes supplémentaires (attachments, notes, etc.)
            columns.extend(self._createAdditionalColumns(kwargs))

        except Exception as e:
            log.error(f"Erreur lors de la création des colonnes: {e}", exc_info=True)

        log.debug(f"TaskViewer._createColumns : {len(columns)} colonnes créées : {columns}.")
        return columns

    # def createColumns(self) -> List[uicommand.UICommand]:
    def createColumns(self) -> List[UICommand]:
        """Crée les colonnes pour la vue des tâches."""
        columns_str = self.settings.get("taskviewer", "columns")
        columns_list = columns_str.split(',')

        # # Simulation de la création de colonnes
        # subject_column = uicommand.UICommand("subject", _("Sujet"), _("Sujet de la tâche"))
        # duedate_column = uicommand.UICommand("duedate", _("Date d'échéance"), _("Date d'échéance de la tâche"))
        # priority_column = uicommand.UICommand("priority", _("Priorité"), _("Priorité de la tâche"))
        #
        # all_columns = {
        #     "subject": subject_column,
        #     "duedate": duedate_column,
        #     "priority": priority_column
        # }
        all_columns = {
            "subject": UICommand("subject", _("Sujet"), _("Sujet de la tâche")),
            "duedate": UICommand("duedate", _("Date d'échéance"), _("Date d'échéance de la tâche")),
            "priority": UICommand("priority", _("Priorité"), _("Priorité de la tâche"))
        }

        return [all_columns[c] for c in columns_list if c in all_columns]

    def _createAdditionalColumns(self, kwargs):
        """Crée les colonnes supplémentaires (méthode auxiliaire)."""
        additional_columns = []

        # Colonne pièces jointes
        additional_columns.append(
            itemctrltk.Column(
                "attachments",
                _("Attachments"),
                task.Task.attachmentsChangedEventType(),
                width=self.getColumnWidth("attachments"),
                alignment=tk.LEFT,
                imageIndicesCallback=self.attachmentImageIndices,
                headerImageIndex=self.imageIndex.get("paperclip_icon", -1),
                renderCallback=lambda task_: "",
                **kwargs
            )
        )

        # Colonne notes
        additional_columns.append(
            itemctrltk.Column(
                "notes",
                _("Notes"),
                task.Task.notesChangedEventType(),
                width=self.getColumnWidth("notes"),
                alignment=tk.LEFT,
                imageIndicesCallback=self.noteImageIndices,
                headerImageIndex=self.imageIndex.get("note_icon", -1),
                renderCallback=lambda task_: "",
                **kwargs
            )
        )

        # Colonne catégories
        additional_columns.append(
            itemctrltk.Column(
                "categories",
                _("Categories"),
                task.Task.categoryAddedEventType(),
                task.Task.categoryRemovedEventType(),
                task.Task.categorySubjectChangedEventType(),
                task.Task.expansionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="categories"
                ),
                width=self.getColumnWidth("categories"),
                renderCallback=self.renderCategories,
                **kwargs
            )
        )

        # Colonne prérequis
        additional_columns.append(
            itemctrltk.Column(
                "prerequisites",
                _("Prerequisites"),
                task.Task.prerequisitesChangedEventType(),
                task.Task.expansionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="prerequisites"
                ),
                renderCallback=self.renderPrerequisites,
                width=self.getColumnWidth("prerequisites"),
                **kwargs
            )
        )

        # Colonne dépendances
        additional_columns.append(
            itemctrltk.Column(
                "dependencies",
                _("Dependents"),
                task.Task.dependenciesChangedEventType(),
                task.Task.expansionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="dependencies"
                ),
                renderCallback=self.renderDependencies,
                width=self.getColumnWidth("dependencies"),
                **kwargs
            )
        )

        # Colonnes de dates
        for name, columnHeader, editCtrl, editCallback, eventTypes in [
            (
                    "plannedStartDateTime",
                    _("Planned start date"),
                    inplace_editortk.DateTimeCtrl,
                    self.onEditPlannedStartDateTime,
                    [],
            ),
            (
                    "dueDateTime",
                    _("Due date"),
                    DueDateTimeCtrl,
                    self.onEditDueDateTime,
                    [task.Task.expansionChangedEventType()],
            ),
            (
                    "actualStartDateTime",
                    _("Actual start date"),
                    inplace_editortk.DateTimeCtrl,
                    self.onEditActualStartDateTime,
                    [task.Task.expansionChangedEventType()],
            ),
            (
                    "completionDateTime",
                    _("Completion date"),
                    inplace_editortk.DateTimeCtrl,
                    self.onEditCompletionDateTime,
                    [task.Task.expansionChangedEventType()],
            ),
        ]:
            renderCallback = getattr(
                self, f"render{name[0].capitalize()}{name[1:]}"
            )
            additional_columns.append(
                itemctrltk.Column(
                    name,
                    columnHeader,
                    sortCallback=uicommand.ViewerSortByCommand(viewer=self, value=name),
                    renderCallback=renderCallback,
                    width=self.getColumnWidth(name),
                    alignment=tk.RIGHT,
                    editControl=editCtrl,
                    editCallback=editCallback,
                    settings=self.settings,
                    *eventTypes,
                    **kwargs
                )
            )

        # Colonnes diverses (budget, temps, etc.)
        for name, columnHeader, editCtrl, editCallback, eventTypes in [
            (
                    "percentageComplete",
                    _("% complete"),
                    inplace_editortk.PercentageCtrl,
                    self.onEditPercentageComplete,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.percentageCompleteChangedEventType(),
                    ],
            ),
            (
                    "timeLeft",
                    _("Time left"),
                    None,
                    None,
                    [task.Task.expansionChangedEventType(), "task.timeLeft"],
            ),
            (
                    "recurrence",
                    _("Recurrence"),
                    None,
                    None,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.recurrenceChangedEventType(),
                    ],
            ),
            (
                    "budget",
                    _("Budget"),
                    inplace_editortk.BudgetCtrl,
                    self.onEditBudget,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.budgetChangedEventType(),
                    ],
            ),
            (
                    "timeSpent",
                    _("Time spent"),
                    None,
                    None,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.timeSpentChangedEventType(),
                    ],
            ),
            (
                    "budgetLeft",
                    _("Budget left"),
                    None,
                    None,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.budgetLeftChangedEventType(),
                    ],
            ),
            (
                    "priority",
                    _("Priority"),
                    inplace_editortk.PriorityCtrl,
                    self.onEditPriority,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.priorityChangedEventType(),
                    ],
            ),
            (
                    "hourlyFee",
                    _("Hourly fee"),
                    inplace_editortk.AmountCtrl,
                    self.onEditHourlyFee,
                    [task.Task.hourlyFeeChangedEventType()],
            ),
            (
                    "fixedFee",
                    _("Fixed fee"),
                    inplace_editortk.AmountCtrl,
                    self.onEditFixedFee,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.fixedFeeChangedEventType(),
                    ],
            ),
            (
                    "revenue",
                    _("Revenue"),
                    None,
                    None,
                    [
                        task.Task.expansionChangedEventType(),
                        task.Task.revenueChangedEventType(),
                    ],
            ),
        ]:
            renderCallback = getattr(
                self, f"render{name[0].capitalize()}{name[1:]}"
            )
            additional_columns.append(
                itemctrltk.Column(
                    name,
                    columnHeader,
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value=name
                    ),
                    renderCallback=renderCallback,
                    width=self.getColumnWidth(name),
                    alignment=tk.RIGHT,
                    editControl=editCtrl,
                    editCallback=editCallback,
                    *eventTypes,
                    **kwargs
                )
            )

        # Colonne rappel
        additional_columns.append(
            itemctrltk.Column(
                "reminder",
                _("Reminder"),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="reminder"
                ),
                renderCallback=self.renderReminder,
                width=self.getColumnWidth("reminder"),
                alignment=tk.RIGHT,
                editControl=inplace_editortk.DateTimeCtrl,
                editCallback=self.onEditReminderDateTime,
                settings=self.settings,
                *[
                    task.Task.expansionChangedEventType(),
                    task.Task.reminderChangedEventType(),
                ],
                **kwargs
            )
        )

        # Colonnes de dates système
        additional_columns.append(
            itemctrltk.Column(
                "creationDateTime",
                _("Creation date"),
                width=self.getColumnWidth("creationDateTime"),
                renderCallback=self.renderCreationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="creationDateTime"
                ),
                **kwargs
            )
        )

        additional_columns.append(
            itemctrltk.Column(
                "modificationDateTime",
                _("Modification date"),
                width=self.getColumnWidth("modificationDateTime"),
                renderCallback=self.renderModificationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="modificationDateTime"
                ),
                *task.Task.modificationEventTypes(),
                **kwargs
            )
        )

        return additional_columns

    def createColumnUICommands(self):
        """Crée les commandes UI pour gérer les colonnes."""
        commands = [
            uicommand.ToggleAutoColumnResizing(viewer=self, settings=self.settings),
            None,
            (
                _("&Dates"),
                uicommand.ViewColumns(
                    menuText=_("&All date columns"),
                    helpText=_("Show/hide all date-related columns"),
                    setting=[
                        "plannedStartDateTime",
                        "dueDateTime",
                        "timeLeft",
                        "actualStartDateTime",
                        "completionDateTime",
                        "recurrence",
                    ],
                    viewer=self,
                ),
                None,
                uicommand.ViewColumn(
                    menuText=_("&Planned start date"),
                    helpText=_("Show/hide planned start date column"),
                    setting="plannedStartDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Due date"),
                    helpText=_("Show/hide due date column"),
                    setting="dueDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Actual start date"),
                    helpText=_("Show/hide actual start date column"),
                    setting="actualStartDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Completion date"),
                    helpText=_("Show/hide completion date column"),
                    setting="completionDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Time left"),
                    helpText=_("Show/hide time left column"),
                    setting="timeLeft",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Recurrence"),
                    helpText=_("Show/hide recurrence column"),
                    setting="recurrence",
                    viewer=self,
                ),
            ),
            (
                _("&Budget"),
                uicommand.ViewColumns(
                    menuText=_("&All budget columns"),
                    helpText=_("Show/hide all budget-related columns"),
                    setting=["budget", "timeSpent", "budgetLeft"],
                    viewer=self,
                ),
                None,
                uicommand.ViewColumn(
                    menuText=_("&Budget"),
                    helpText=_("Show/hide budget column"),
                    setting="budget",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Time spent"),
                    helpText=_("Show/hide time spent column"),
                    setting="timeSpent",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Budget left"),
                    helpText=_("Show/hide budget left column"),
                    setting="budgetLeft",
                    viewer=self,
                ),
            ),
            (
                _("&Financial"),
                uicommand.ViewColumns(
                    menuText=_("&All financial columns"),
                    helpText=_("Show/hide all finance-related columns"),
                    setting=["hourlyFee", "fixedFee", "revenue"],
                    viewer=self,
                ),
                None,
                uicommand.ViewColumn(
                    menuText=_("&Hourly fee"),
                    helpText=_("Show/hide hourly fee column"),
                    setting="hourlyFee",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Fixed fee"),
                    helpText=_("Show/hide fixed fee column"),
                    setting="fixedFee",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Revenue"),
                    helpText=_("Show/hide revenue column"),
                    setting="revenue",
                    viewer=self,
                ),
            ),
            uicommand.ViewColumn(
                menuText=_("&Manual ordering"),
                helpText=_("Show/hide the manual ordering column"),
                setting="ordering",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Description"),
                helpText=_("Show/hide description column"),
                setting="description",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Prerequisites"),
                helpText=_("Show/hide prerequisites column"),
                setting="prerequisites",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Dependents"),
                helpText=_("Show/hide dependents column"),
                setting="dependencies",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Percentage complete"),
                helpText=_("Show/hide percentage complete column"),
                setting="percentageComplete",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Attachments"),
                helpText=_("Show/hide attachment column"),
                setting="attachments",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Notes"),
                helpText=_("Show/hide notes column"),
                setting="notes",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Categories"),
                helpText=_("Show/hide categories column"),
                setting="categories",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Priority"),
                helpText=_("Show/hide priority column"),
                setting="priority",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Reminder"),
                helpText=_("Show/hide reminder column"),
                setting="reminder",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Creation date"),
                helpText=_("Show/hide creation date column"),
                setting="creationDateTime",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Modification date"),
                helpText=_("Show/hide last modification date column"),
                setting="modificationDateTime",
                viewer=self,
            ),
        ]
        return commands

    # L'erreur AttributeError: 'NoneType' object has no attribute 'lower' se produit dans configparser.py lorsqu'il essaie de lire une option de configuration.
    #
    # Voici la chaîne de causalité :
    #
    #     uicommand.TaskViewerTreeOrListChoice est instancié.
    #
    #     Il hérite (via uicommandtk) de SettingsUICommand (dans settings_uicommandtk.py).
    #
    #     Le constructeur __init__ de SettingsUICommand tente de créer une tk.BooleanVar en lisant la valeur actuelle du paramètre : self.settings.getboolean(self.section, self.setting).
    #
    #     self.setting est None parce qu'il n'a pas été passé lors de l'instanciation.
    #
    #     configparser reçoit None comme nom d'option et plante en essayant de faire .lower() dessus.
    def createModeToolBarUICommands(self):
        """Crée des commandes UI pour la barre d'outils (modes)."""
        # Il faut explicitement indiquer quel paramètre (setting)
        # cette commande doit contrôler. Dans le cas du choix "Arbre ou Liste",
        # le paramètre est "treemode".
        treeOrListUICommand = uicommand.TaskViewerTreeOrListChoice(
            viewer=self,
            settings=self.settings,
            setting="treemode"  # AJOUT IMPORTANT : Cela permettra à SettingsUICommand de savoir qu'il doit lire la valeur treemode dans le fichier de configuration, évitant ainsi le NoneType.
        )
        return super().createModeToolBarUICommands() + (treeOrListUICommand,)

    def hasModes(self):
        """Indique que ce visualiseur a des modes (arbre/liste)."""
        return True

    def getModeUICommands(self):
        """Retourne les commandes UI pour les modes."""
        return [_("Show tasks as"), None] + [
            uicommand.TaskViewerTreeOrListOption(
                menuText=menuText, value=value, viewer=self, settings=self.settings
            )
            for (menuText, value) in zip(
                uicommand.TaskViewerTreeOrListChoice.choiceLabels,
                uicommand.TaskViewerTreeOrListChoice.choiceData,
            )
        ]

    def createColumnPopupMenu(self):
        """Crée le menu contextuel pour les colonnes."""
        try:
            return taskcoachlib.guitk.menu.ColumnPopupMenu(self)
        except Exception as e:
            log.warning(f"Impossible de créer le menu contextuel de colonnes: {e}")
            return None

    def setSortByTaskStatusFirst(self, *args, **kwargs):
        """Définit le tri par statut de tâche en premier."""
        super().setSortByTaskStatusFirst(*args, **kwargs)
        self.showSortOrder()

    def getSortOrderImage(self):
        """Retourne l'image de l'ordre de tri."""
        sortOrderImage = super().getSortOrderImage()
        if self.isSortByTaskStatusFirst():
            sortOrderImage = sortOrderImage.rstrip("icon") + "with_status_icon"
        return sortOrderImage

    def setSearchFilter(self, searchString, *args, **kwargs):
        """Définit le filtre de recherche."""
        super().setSearchFilter(searchString, *args, **kwargs)
        if searchString:
            self.expandAll()

    def onTreeListModeChanged(self, value):
        """Gère le changement de mode arbre/liste."""
        self.presentation().setTreeMode(value)


    # Méthodes de rendu pour les colonnes

    def renderSubject(self, task_item):
        """Rend le sujet d'une tâche."""
        subject = task_item.subject(recursive=not self.isTreeViewer())
        log.debug(f"TaskViewer.renderSubject : {subject} pour task={task_item}")
        return subject

    def renderPlannedStartDateTime(self, task_item, humanReadable=True):
        """Rend la date de début planifiée."""
        return self.renderedValue(
            task_item,
            task_item.plannedStartDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderDueDateTime(self, task_item, humanReadable=True):
        """Rend la date d'échéance."""
        return self.renderedValue(
            task_item,
            task_item.dueDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderActualStartDateTime(self, task_item, humanReadable=True):
        """Rend la date de début réelle."""
        return self.renderedValue(
            task_item,
            task_item.actualStartDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderCompletionDateTime(self, task_item, humanReadable=True):
        """Rend la date d'achèvement."""
        return self.renderedValue(
            task_item,
            task_item.completionDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderRecurrence(self, task_item):
        """Rend la récurrence."""
        return self.renderedValue(task_item, task_item.recurrence, render.recurrence)

    def renderPrerequisites(self, task_item):
        """Rend les prérequis."""
        return self.renderSubjectsOfRelatedItems(task_item, task_item.prerequisites)

    def renderDependencies(self, task_item):
        """Rend les dépendances."""
        return self.renderSubjectsOfRelatedItems(task_item, task_item.dependencies)

    def renderTimeLeft(self, task_item):
        """Rend le temps restant."""
        return self.renderedValue(
            task_item, task_item.timeLeft, render.timeLeft, task_item.completed()
        )

    def renderTimeSpent(self, task_item):
        """Rend le temps passé."""
        return self.renderedValue(task_item, task_item.timeSpent, self._renderTimeSpent)

    def renderBudget(self, task_item):
        """Rend le budget."""
        return self.renderedValue(task_item, task_item.budget, render.budget)

    def renderBudgetLeft(self, task_item):
        """Rend le budget restant."""
        return self.renderedValue(task_item, task_item.budgetLeft, render.budget)

    def renderRevenue(self, task_item):
        """Rend le revenu."""
        return self.renderedValue(task_item, task_item.revenue, render.monetaryAmount)

    def renderHourlyFee(self, task_item):
        """Rend le tarif horaire."""
        return render.monetaryAmount(task_item.hourlyFee())

    def renderFixedFee(self, task_item):
        """Rend les frais fixes."""
        return self.renderedValue(task_item, task_item.fixedFee, render.monetaryAmount)

    def renderPercentageComplete(self, task_item):
        """Rend le pourcentage d'achèvement."""
        return self.renderedValue(task_item, task_item.percentageComplete, render.percentage)

    def renderPriority(self, task_item):
        """Rend la priorité."""
        return self.renderedValue(task_item, task_item.priority, render.priority) + " "

    def renderReminder(self, task_item, humanReadable=True):
        """Rend le rappel."""
        return self.renderedValue(
            task_item,
            task_item.reminder,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderedValue(self, item, getValue, renderValue, *extraRenderArgs):
        """Rend une valeur en tenant compte du mode récursif."""
        value = getValue(recursive=False)
        template = "%s"
        if self.isItemCollapsed(item):
            recursiveValue = getValue(recursive=True)
            if value != recursiveValue:
                value = recursiveValue
                template = "(%s)"
        return template % renderValue(value, *extraRenderArgs)

    # Méthodes de callback pour l'édition

    def onEditPlannedStartDateTime(self, item, newValue):
        """Gère l'édition de la date de début planifiée."""
        keep_delta = self.settings.get("view", "datestied") == "startdue"
        command.EditPlannedStartDateTimeCommand(
            items=[item], newValue=newValue, keep_delta=keep_delta
        ).do()

    def onEditDueDateTime(self, item, newValue):
        """Gère l'édition de la date d'échéance."""
        keep_delta = self.settings.get("view", "datestied") == "duestart"
        command.EditDueDateTimeCommand(
            items=[item], newValue=newValue, keep_delta=keep_delta
        ).do()

    def onEditActualStartDateTime(self, item, newValue):
        """Gère l'édition de la date de début réelle."""
        command.EditActualStartDateTimeCommand(items=[item], newValue=newValue).do()

    def onEditCompletionDateTime(self, item, newValue):
        """Gère l'édition de la date d'achèvement."""
        command.EditCompletionDateTimeCommand(items=[item], newValue=newValue).do()

    def onEditPercentageComplete(self, item, newValue):
        """Gère l'édition du pourcentage d'achèvement."""
        command.EditPercentageCompleteCommand(items=[item], newValue=newValue).do()

    def onEditBudget(self, item, newValue):
        """Gère l'édition du budget."""
        command.EditBudgetCommand(items=[item], newValue=newValue).do()

    def onEditPriority(self, item, newValue):
        """Gère l'édition de la priorité."""
        command.EditPriorityCommand(items=[item], newValue=newValue).do()

    def onEditReminderDateTime(self, item, newValue):
        """Gère l'édition du rappel."""
        command.EditReminderDateTimeCommand(items=[item], newValue=newValue).do()

    def onEditHourlyFee(self, item, newValue):
        """Gère l'édition du tarif horaire."""
        command.EditHourlyFeeCommand(items=[item], newValue=newValue).do()

    def onEditFixedFee(self, item, newValue):
        """Gère l'édition des frais fixes."""
        command.EditFixedFeeCommand(items=[item], newValue=newValue).do()

    def onEverySecond(self, event):
        """Mise à jour chaque seconde (uniquement si colonnes concernées visibles)."""
        if any(
                [
                    self.isVisibleColumnByName(column)
                    for column in ("timeSpent", "budgetLeft", "revenue")
                ]
        ):
            super().onEverySecond(event)

    def getRootItems(self):
        """Retourne les éléments racine selon le mode arbre/liste."""
        return super().getRootItems() if self.isTreeViewer() else self.presentation()

    def getItemParent(self, item):
        """Retourne le parent d'un élément selon le mode arbre/liste."""
        return super().getItemParent(item) if self.isTreeViewer() else None

    def get_domain_children(self, item=None):
        """Retourne les enfants d'un élément selon le mode arbre/liste."""
        return super().get_domain_children(item) if (self.isTreeViewer() or item is None) else []

    # Anciennes méthodes pour tkinter

    def _populate_tree(self):
        """Charge les données des tâches dans le Treeview."""
        self.tree.delete(*self.tree.get_children())
        tasks = self.taskFile.tasks()
        self._insert_tasks(tasks, parent_item="")

    def _insert_tasks(self, tasks: List[domain.task], parent_item: str):
        """Insère les tâches de manière récursive."""
        for task in tasks:
            item_id = self.tree.insert(parent_item, "end", text=task.subject,
                                       values=(str(task.duedate), task.priority))
            if task.get_domain_children():
                self._insert_tasks(task.get_domain_children(), parent_item=item_id)

    # def settingsSection(self):
    @classmethod
    def settingsSection(cls) -> str:
        """
        Retourne la section de paramétrage de la vue.
        Cette méthode de classe est utilisée par la fabrique de visionneuses.
        """
        # Do some custom logic here, if needed
        # ...
        # return super().settingsSection()  # Call the superclass implementation
        return "taskviewer"

    def refresh(self):
        """Rafraîchit la vue, à implémenter correctement."""
        self._populate_tree()

    def is_visible(self) -> bool:
        """Détermine si le visualiseur est visible."""
        return True  # À adapter si votre application gère la visibilité des onglets

    def is_deletable(self) -> bool:
        """Détermine si le visualiseur peut être supprimé."""
        return True  # À adapter si votre application gère la suppression des onglets

    def onAdd(self, event: Any):
        """Ajoute une nouvelle tâche."""
        new_task = domain.task(_("Nouvelle tâche"), domain.date(""), 0)
        self.taskFile.add_task(new_task)
        self._populate_tree()
        messagebox.showinfo("Action", _("Une nouvelle tâche a été ajoutée."))

    def onDelete(self, event: Any):
        """Supprime les tâches sélectionnées."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Avertissement", _("Veuillez sélectionner au moins une tâche à supprimer."))
            return

        for item in selected_items:
            self.tree.delete(item)
        messagebox.showinfo("Action", _("Tâches sélectionnées supprimées."))

    # curselection est sensé être dans Viewer !
    # def curselection(self) -> List[Any]:
    #     """Retourne la liste des tâches sélectionnées (simulation)."""
    #     # Ceci est une simulation, dans un vrai projet,
    #     # il faudrait lier les items aux objets de domaine
    #     # return [domain.task(self.tree.item(item, "text"), None, 0) for item in self.tree.selection()]
    #     return [domain.task.Task(self.tree.item(item, "text"), None, 0) for item in self.tree.selection()]

    # def presentation(self) -> List[Any]:
    #     """Retourne la liste complète des tâches (simulation)."""
    #     # Ceci est une simulation, dans un vrai projet, il faudrait retourner la liste des objets de domaine
    #     return self.taskFile.tasks()
    #     # Presentation doit être dans basetk.Viewer !

    def domainObjectsToView(self):
        """Retourne les objets du domaine que cette visionneuse doit afficher."""
        return self.taskFile.tasks()

    # Méthodes abstraites héritées de ViewerContainer
    def currentViewer(self):
        return self

    def onViewerSelected(self, viewer):
        pass

    def addViewer(self, viewer):
        pass

    def removeViewer(self, viewer):
        pass

    def selectViewer(self, viewer):
        pass

    def selectViewerAndShow(self, viewer):
        pass

    def viewers(self):
        return [self]

    def findViewer(self, viewer_class: Type):
        if isinstance(self, viewer_class):
            return self
        return None

    def visibleColumns(self):
        # def visibleColumns(self) -> list:
        """
        Retourne la liste des colonnes visibles.

        Returns :
            Liste des colonnes actuellement visibles.
        """
        return self.__visibleColumns

    def title(self):
        """Returns the title of the viewer."""
        return _("Tâches")


# Points importants à noter et à adapter:
#
# CheckableTaskViewer :
# Il faut remplacer widgets.CheckTreeCtrl par une implémentation Tkinter.
# Une option serait d'utiliser un ttk.Treeview et d'ajouter des Checkbutton pour chaque élément.
# Il faudra gérer l'état des cases à cocher et les événements associés.
# imageList : La gestion des images est différente en Tkinter.
# Il faudra utiliser PhotoImage et les associer aux éléments de l'arbre.
#
#
# TaskStatsViewer :
# wx.lib.agw.piectrl.PieCtrl doit être remplacé par une solution Tkinter.
# On peut utiliser le Canvas pour dessiner le diagramme circulaire,
# ou utiliser une librairie externe comme matplotlib.
# Les méthodes SetShowEdges, SetHeight, GetLegend, SetTransparent, SetBackColour,
# SetLabelFont, Show, SetAngle, Refresh doivent être adaptées ou réimplémentées avec Tkinter.
#
#
# TaskInterdepsViewer :
# ScrolledPanel doit être remplacé par un équivalent Tkinter.
# Un Frame avec des barres de défilement peut faire l'affaire,
# mais il faudra gérer la logique de défilement.
# wx.BoxSizer est remplacé par des Frame et le gestionnaire de géométrie pack
# wx.Image et wx.Bitmap sont remplacés par PIL (Pillow) pour charger l'image
# et ImageTk.PhotoImage pour l'afficher dans un Label.
# wx.StaticBitmap est remplacé par un tk.Label qui affiche l'image.
# wx.CallAfter est remplacé par self.after pour exécuter du code après la mise à jour de l'interface.
# Il faut installer la librairie Pillow (pip install Pillow) pour que la gestion des images fonctionne.
#
#
# igraph :
# Il faut s'assurer que la librairie igraph est bien installée (pip install python-igraph).
#
#
# Gestion des couleurs :
# wx.Colour doit être remplacé par des chaînes de caractères représentant des couleurs en hexadécimal (ex: "#RRGGBB").
#
#
# Général:
# Tous les appels à des méthodes spécifiques à wxPython (ex: widget.Set..., widget.Get...) doivent être remplacés par leur équivalent Tkinter.
# Il faut gérer correctement les layouts avec pack, grid ou place.
#
#
# Twisted: Il faut bien comprendre le fonctionnement de Twisted pour l'intégration dans Tkinter,
# en particulier l'utilisation de deferToThread et inlineCallbacks.
#
# Ce code fournit une base de conversion, mais l'implémentation complète nécessitera
# un travail conséquent, en particulier pour les widgets complexes comme
# l'arbre avec cases à cocher et le diagramme circulaire.
# N'hésite pas à poser d'autres questions au fur et à mesure de ton avancement.
class CheckableTaskViewer(Taskviewer):
    """
    Visualiseur de tâches avec cases à cocher.

    Ce visualiseur permet de cocher ou décocher des tâches dans une arborescence.
    Il étend le `TaskViewer` en ajoutant des fonctionnalités liées à la gestion
    des cases à cocher pour chaque tâche.

    Méthodes :
        createWidget (self) : Crée le widget d'affichage avec des cases à cocher pour les tâches.
        onCheck (self, event, final) : Gère les événements liés au changement d'état des cases à cocher.
        getIsItemChecked (self, task) : Vérifie si une tâche est cochée.
        getItemParentHasExclusiveChildren (self, task) : Vérifie si une tâche parent a des enfants exclusifs.
    """
    def createWidget(self):
        # imageList = self.createImageList()  # Has side-effects  # Pas d'équivalent simple en Tkinter. A voir.
        self._columns = self._createColumns()
        itemPopupMenu = self.createTaskPopupMenu()
        columnPopupMenu = self.createColumnPopupMenu()
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])

        # TODO: Implémenter un arbre avec des cases à cocher en Tkinter (Treeview avec Checkbuttons ?)
        # # Pour l'instant, on utilise un simple Label pour placeholder
        # widget = tk.Label(self, text="Arbre de tâches avec cases à cocher Tkinter à implémenter")

        widget = widgetstk.treectrltk.CheckTreeCtrl(  # A remplacer
            self,
            self.columns(),
            self.onSelect,
            self.onCheck,
            uicommand.Edit(viewer=self),
            uicommand.TaskDragAndDrop(taskList=self.presentation(), viewer=self),
            itemPopupMenu,
            columnPopupMenu,
            **self.widgetCreationKeywordArguments()
        )
        # widget.AssignImageList(imageList)  # pylint: disable=E1101  Parameter 'which' unfilled
        # widget.AssignImageList(imageList, wx.IMAGE_LIST_NORMAL)  # pylint: disable=E1101
        return widget

    def onCheck(self, event, final):
        pass

    def getIsItemChecked(self, task):  # pylint: disable=W0613,W0621
        return False

        # @staticmethod
    def getItemParentHasExclusiveChildren(self, task):  # pylint: disable=W0613,W0621
        return False


class TaskStatsViewer(BaseTaskViewer):  # pylint: disable=W0223
    """
    Visualiseur de statistiques sur les tâches.

    Ce visualiseur affiche des statistiques sous forme de diagrammes circulaires
    et autres graphiques, basées sur le statut des tâches (en retard, complétées, etc.).

    Méthodes :
        __init__(self, *args, **kwargs) : Initialise le visualiseur de statistiques avec les paramètres par défaut.
        createWidget(self) : Crée le widget de diagramme circulaire pour afficher les statistiques.
        initLegend(self, widget) : Initialise la légende du diagramme.
        refresh(self) : Rafraîchit l'affichage du diagramme circulaire en fonction des paramètres actuels.
    """
    defaultTitle = _("Task statistics")
    defaultBitmap = "charts_icon"

    def __init__(self, parent, *args, **kwargs):
        kwargs.setdefault("settingsSection", "taskstatsviewer")
        super().__init__(parent, *args, **kwargs)
        pub.subscribe(
            self.onPieChartAngleChanged,
            "settings.%s.piechartangle" % self.settingsSection(),
            )

    def createWidget(self, parent):
        # TODO: Implémenter un diagramme circulaire avec Tkinter (Canvas ou une librairie externe)

        # Pour l'instant, on utilise un simple Label pour placeholder
        widget = tk.Label(self, text="Diagramme circulaire Tkinter à implémenter")  # TODO : à remplacer par la suite !
        # widget = wx.lib.agw.piectrl.PieCtrl(self)  # A remplacer
        # widget.SetShowEdges(False) # A remplacer
        # widget.SetHeight(20) # A remplacer
        self.initLegend(widget)
        # for dummy in task.Task.possibleStatuses():  # A remplacer
        #     widget._series.append(
        #         wx.lib.agw.piectrl.PiePart(1)
        #     )  # pylint: disable=W0212
        return widget

    def createClipboardToolBarUICommands(self):
        return ()

    def createEditToolBarUICommands(self):
        return ()

    def createCreationToolBarUICommands(self):
        return (
            uicommand.TaskNew(taskList=self.presentation(), settings=self.settings),
            uicommand.TaskNewFromTemplateButton(
                taskList=self.presentation(), settings=self.settings, bitmap="newtmpl"
            ),
        )

    def createActionToolBarUICommands(self):
        return tuple(
            [
                uicommand.ViewerHideTasks(
                    taskStatus=status, settings=self.settings, viewer=self
                )
                for status in task.Task.possibleStatuses()
            ]
        ) + (
            uicommand.ViewerPieChartAngle(viewer=self, settings=self.settings),
        )

        # @staticmethod
    def initLegend(self, widget):
        # legend = widget.GetLegend() # A remplacer
        # legend.SetTransparent(False) # A remplacer
        # legend.SetBackColour(wx.WHITE) # A remplacer
        # legend.SetLabelFont(wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)) # A remplacer
        # legend.Show() # A remplacer
        pass

    def refresh(self):
        # self.widget.SetAngle( # A remplacer
        #     self.settings.getint(self.settingsSection(), "piechartangle")
        #     / 180.0
        #     * math.pi
        # )
        # self.refreshParts() # A remplacer
        # self.widget.Refresh() # A remplacer
        pass

    def refreshParts(self):
        # series = self.widget._series  # pylint: disable=W0212 # A remplacer
        tasks = self.presentation()
        total = len(tasks)
        counts = tasks.nrOfTasksPerStatus()
        # for part, status in zip(series, task.Task.possibleStatuses()): # A remplacer
        #     nrTasks = counts[status]
        #     percentage = round(100.0 * nrTasks // total) if total else 0
        #     part.SetLabel(status.countLabel % (nrTasks, percentage))
        #     part.SetValue(nrTasks)
        #     part.SetColour(self.getFgColor(status))
        # PietCtrl can't handle empty pie charts:
        # if total == 0: # A remplacer
        #     series[0].SetValue(1)
        pass

    def getFgColor(self, status):
        # color = wx.Colour(*eval(self.settings.get("fgcolor", "%stasks" % status))) # A remplacer
        color = None
        # if status == task.status.active and color == wx.BLACK: # A remplacer
        #     color = wx.BLUE # A remplacer
        return color

    def refreshItems(self, *args, **kwargs):  # pylint: disable=W0613
        self.refresh()

    def select(self, *args):
        pass

    def updateSelection(self, *args, **kwargs):
        pass

    def isTreeViewer(self):
        return False

    def onPieChartAngleChanged(self, value):  # pylint: disable=W0613
        self.refresh()


try:
    import igraph
except ImportError:
    pass
else:
    class TaskInterdepsViewer(BaseTaskViewer):
        # defaultTitle = _("Tasks Interdependencies")
        defaultTitle = "Tasks Interdependencies"
        # defaultBitmap = _("graph_icon")
        defaultBitmap = "graph_icon"

        graphFile = tempfile.NamedTemporaryFile(suffix=".png")

        def __init__(self, *args, **kwargs):
            kwargs.setdefault("settingsSection", "taskinterdepsviewer")
            self._needsUpdate = False  # refresh called from parent constructor
            self._updating = False
            super().__init__(*args, **kwargs)

            pub.subscribe(
                self.onAttributeChanged, task.Task.dependenciesChangedEventType()
            )
            pub.subscribe(
                self.onAttributeChanged, task.Task.prerequisitesChangedEventType()
            )

        def createWidget(self):
            # self.scrolled_panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1) # A remplacer
            # self.scrolled_panel = ScrolledPanel(self, -1) # A remplacer
            self.scrolled_panel = tk.Frame(self)  # Frame Tkinter pour remplacer ScrolledPanel

            # self.vbox = wx.BoxSizer(wx.VERTICAL) # A remplacer
            # self.hbox = wx.BoxSizer(wx.HORIZONTAL) # A remplacer
            self.vbox = tk.Frame(self.scrolled_panel)  # Frame Tkinter pour remplacer BoxSizer
            self.hbox = tk.Frame(self.vbox)  # Frame Tkinter pour remplacer BoxSizer
            # self.vbox.Add(self.hbox, 0, wx.ALIGN_CENTRE) # A remplacer
            # self.scrolled_panel.SetSizer(self.vbox) # A remplacer
            self.vbox.pack()  # Pack layout pour Tkinter
            self.hbox.pack()  # Pack layout pour Tkinter
            # self.scrolled_panel.SetupScrolling() # A remplacer

            graph, visual_style = self.form_depend_graph()
            if graph.get_edgelist():
                igraph.plot(graph, self.graphFile.name, **visual_style)
                # bitmap = wx.Image( # A remplacer
                #     self.graphFile.name, wx.BITMAP_TYPE_ANY
                # ).ConvertToBitmap()
                try:
                    from PIL import Image, ImageTk
                    pil_image = Image.open(self.graphFile.name)
                    bitmap = ImageTk.PhotoImage(pil_image)
                except ImportError:
                    bitmap = None # Gestion d'erreur si PIL n'est pas installé
            else:
                bitmap = None
                # graph_png_bm = wx.StaticBitmap(self.scrolled_panel, wx.ID_ANY, bitmap) # A remplacer
            if bitmap:
                graph_png_bm = tk.Label(self.scrolled_panel, image=bitmap) # Label Tkinter pour afficher l'image
                graph_png_bm.image = bitmap # Garder une référence pour éviter que l'image soit garbage collected
            else:
                graph_png_bm = tk.Label(self.scrolled_panel, text="igraph ou PIL non installé")
                # self.hbox.Add(graph_png_bm, 1, wx.ALL, 3) # A remplacer
            graph_png_bm.pack() # Pack layout pour Tkinter
            # self.scrolled_panel.SetupScrolling() # A remplacer

            return self.scrolled_panel

        def createClipboardToolBarUICommands(self):
            return ()

        def createEditToolBarUICommands(self):
            return ()

        def createCreationToolBarUICommands(self):
            return ()

        def createActionToolBarUICommands(self):
            return tuple(
                [
                    uicommand.ViewerHideTasks(
                        taskStatus=status, settings=self.settings, viewer=self
                    )
                    for status in task.Task.possibleStatuses()
                ]
            )

            # @staticmethod
        def initLegend(self, widget):
            # legend = widget.GetLegend() # A remplacer
            # legend.Show() # A remplacer
            pass

        @staticmethod
        def determine_vertex_weight(budget, priority):
            budg_h = budget.total_seconds() // 3600
            return (budg_h + priority * (budg_h + 1) + 10) % 200

        @staticmethod
        def convert_rgba_to_rgb(rgba):
            rgb = (rgba[0], rgba[1], rgba[2])
            return "#" + struct.pack("BBB", *rgb).decode(
                "hex"
            )  # unresolved attribute reference encode for class bytes

        def form_depend_graph(self):
            vertices = dict()  # task => (weight, color)
            edges = set()  # of 2-tuples (task, task)

            def addVertex(tsk):
                if tsk not in vertices:
                    vertices[tsk] = (
                        self.determine_vertex_weight(tsk.budget(), tsk.priority()),
                        self.convert_rgba_to_rgb(task.foregroundColor(recursive=True)),
                    )

            for task in self.presentation():
                if task.prerequisites():
                    addVertex(task)
                    for prereq in task.prerequisites():
                        addVertex(prereq)
                        edges.add((prereq, task))

            vertices = list(sorted(vertices.items()))
            vertices_w = [weight for task, (weight, color) in vertices]
            vertices_col = [color for task, (weight, color) in vertices]
            vertices = [task for task, (weight, color) in vertices]
            edges = sorted(
                [
                    (vertices.index(task0), vertices.index(task1))
                    for (task0, task1) in edges
                ]
            )
            vertices = [task.subject() for task in vertices]

            graph = igraph.Graph(
                vertex_attrs={"label": vertices}, edges=edges, directed=True
            )
            graph.topological_sorting(mode=igraph.OUT)
            visual_style = {}
            visual_style["vertex_color"] = vertices_col
            visual_style["edge_width"] = [3 for x in graph.es]
            visual_style["margin"] = 70
            visual_style["edge_curved"] = True
            graph.vs["label_dist"] = 1

            # weighted vertex
            indegree = graph.degree(type="in")
            if indegree:
                max_i_degree = max(indegree)
                # visual_style["vertex_size"] = [(i_deg/max_i_degree) * 20 + vert_w
                # visual_style["vertex_size"] = [(i_deg//max_i_degree) * 20 + vert_w
                visual_style["vertex_size"] = [
                    (i_deg // max_i_degree) * 20 + vert_w
                    for i_deg, vert_w in zip(indegree, vertices_w)
                ]

            return graph, visual_style

        def getFgColor(self, status):
            # color = wx.Colour(*eval(self.settings.get("fgcolor", "%stasks" % status))) # A remplacer
            color = None
            # if status == task.status.active and color == wx.BLACK: # A remplacer
            #     color = wx.BLUE # A remplacer
            return color

        def select(self, *args):
            pass

        def updateSelection(self, *args, **kwargs):
            pass

        def isTreeViewer(self):
            return False

        def refreshItems(self, *items):
            self.refresh()

        def refresh(self):
            if not self._needsUpdate:
                self._needsUpdate = True
                if not self._updating:
                    self._refresh()

        @inlineCallbacks
        def _refresh(self):
            bitmap = None
            while self._needsUpdate:
                # Compute this in main thread because of concurrent access issues
                graph, visual_style = self.form_depend_graph()
                self._needsUpdate = False  # Any new refresh starting here should trigger a new iteration

                if graph.get_edgelist():
                    self._updating = True
                    try:
                        yield deferToThread(
                            igraph.plot, graph, self.graphFile.name, **visual_style
                        )
                    finally:
                        self._updating = False
                        # bitmap = wx.Image( # A remplacer
                    #     self.graphFile.name, wx.BITMAP_TYPE_ANY
                    # ).ConvertToBitmap()
                    try:
                        from PIL import Image, ImageTk
                        pil_image = Image.open(self.graphFile.name)
                        bitmap = ImageTk.PhotoImage(pil_image)
                    except ImportError:
                        bitmap = None  # Gestion d'erreur si PIL n'est pas installé
                else:
                    bitmap = None

                    # Only update graphics once all refreshes have been "collapsed"
            # graph_png_bm = wx.StaticBitmap(self.scrolled_panel, wx.ID_ANY, bitmap) # A remplacer
            if bitmap:
                graph_png_bm = tk.Label(self.scrolled_panel, image=bitmap) # Label Tkinter pour afficher l'image
                graph_png_bm.image = bitmap # Garder une référence pour éviter que l'image soit garbage collected
            else:
                graph_png_bm = tk.Label(self.scrolled_panel, text="igraph ou PIL non installé")

                # self.hbox.Clear(True) # A remplacer
            # self.hbox.Add(graph_png_bm, 1, wx.ALL, 3) # A remplacer
            for widget in self.hbox.winfo_children():  # Suppression des anciens widgets
                widget.destroy()
            graph_png_bm.pack() # Pack layout pour Tkinter
            # wx.CallAfter(self.scrolled_panel.SendSizeEvent) # A remplacer
            self.after(0, self.scrolled_panel.event_generate, '<Configure>', when='tail')  # Force un événement de configuration pour redimensionner

# ============================================================================
# Code de démonstration
# ============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    root.title(_("Task Viewer Demo"))
    root.geometry("1024x768")

    # Création d'un fichier de tâches simulé
    class MockTaskFile:
        def __init__(self):
            self._tasks = [
                domain.task.Task("Acheter du lait", dueDateTime=domain.date.Date(2023, 8,30), priority=1),
                domain.task.Task("Préparer la présentation",
                            dueDateTime=domain.date.Date(2023, 9, 5),
                            priority=2,
                            children=[
                                domain.task.Task("Rechercher des données", dueDateTime=domain.date.Date(2023, 9, 2), priority=2),
                                domain.task.Task("Créer les diapositives", dueDateTime=domain.date.Date(2023, 9, 4), priority=3)
                            ]),
                domain.task.Task("Envoyer le rapport", dueDateTime=domain.date.Date(2023, 9, 1), priority=1)
            ]
            self._categories = MockCategories()
            self._efforts = []

        def tasks(self) -> List[domain.task]:
            return self._tasks

        def categories(self):
            return self._categories

        def efforts(self):
            return self._efforts

        def add_task(self, the_task: domain.task.Task):
            self._tasks.append(the_task)

    class MockCategories:
        def filteredCategories(self):
            return []

        def resetAllFilteredCategories(self):
            pass

    # Création des paramètres simulés
    from taskcoachlib.config import settings as Settings

    # app_settings = settings()
    app_settings = Settings.Settings(load=False)
    # app_settings.add_section("taskviewer")
    app_settings.set("taskviewer", "columns", "subject,dueDateTime,priority")
    app_settings.set("taskviewer", "treemode", "True")
    app_settings.set("taskviewer", "columnwidths", "{}")
    app_settings.set("taskviewer", "columnsalwaysvisible", "subject")

    # Création du fichier de tâches
    task_file = MockTaskFile()

    # Création du visualiseur
    # viewer = Taskviewer(root, app_settings, task_file)
    try:
        # Création du visualiseur
        viewer = Taskviewer(
            root,
            task_file,
            app_settings,
            settingsSection="taskviewer",
            instanceNumber=0
        )
        viewer.pack(fill="both", expand=True)

        # Barre de boutons pour la démonstration
        button_frame = ttk.Frame(root)
        button_frame.pack(side="bottom", fill="x", pady=5)

        # add_button = ttk.Button(button_frame, text=_("Ajouter une tâche"), command=lambda: viewer.onAdd(None))
        # add_button.pack(side="left", padx=5)
        #
        # delete_button = ttk.Button(button_frame, text=_("Supprimer la sélection"), command=lambda: viewer.onDelete(None))
        # delete_button.pack(side="left", padx=5)

        ttk.Label(button_frame, text=_("Démonstration du TaskViewer")).pack(side="left", padx=5)

        log.info("TaskViewer initialisé avec succès")

    except Exception as e:
        log.error(f"Erreur lors de l'initialisation du TaskViewer: {e}", exc_info=True)
        messagebox.showerror(
            _("Erreur"),
            f"Impossible d'initialiser le visualiseur:\n{e}"
        )

    root.mainloop()
