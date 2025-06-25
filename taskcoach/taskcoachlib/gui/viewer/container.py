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

# from builtins import range
# from builtins import object
from taskcoachlib import operating_system
import taskcoachlib.gui.menu
# from taskcoachlib.gui.menu import *
# try:
from pubsub import pub
# except ImportError:
#     try:
#        from ...thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
# from taskcoachlib.thirdparty import aui as aui
import wx.lib.agw.aui as aui
# import aui2 as aui
import wx


class ViewerContainer(object):
    """ ViewerContainer est un conteneur de visionneuses. Il possède un conteneurWidget
        qui affiche les visionneuses. Le conteneurWidget est supposé être
        une trame gérée par AUI. Le ViewerContainer sait lequel de ses visualiseurs
        est actif et distribue les appels de méthode au visualiseur actif ou au premier visualiseur
        capable de gérer la méthode. Cela permet à d'autres composants GUI,
        par ex. menu, pour parler au ViewerContainer comme s'il s'agissait
        d'un spectateur régulier. """
        
    def __init__(self, containerWidget, settings, *args, **kwargs):
        self.containerWidget = containerWidget
        self._notifyActiveViewer = False
        self.__bind_event_handlers()
        self._settings = settings
        self.viewers = []
        super().__init__(*args, **kwargs)

    def componentsCreated(self):
        self._notifyActiveViewer = True

    def advanceSelection(self, forward):
        """ Activez la visionneuse suivante si le transfert est vrai, sinon la visionneuse précédente. """
        if len(self.viewers) <= 1:
            return  # Not enough viewers to advance selection
        active_viewer = self.activeViewer()
        current_index = self.viewers.index(active_viewer) if active_viewer else 0
        minimum_index, maximum_index = 0, len(self.viewers) - 1
        if forward:
            new_index = current_index + 1 if minimum_index <= current_index < maximum_index else minimum_index
        else:
            new_index = current_index - 1 if minimum_index < current_index <= maximum_index else maximum_index
        self.activateViewer(self.viewers[new_index])
        
    # @staticmethod
    def isViewerContainer(self):
        """ Indique s'il s'agit d'un conteneur de visionneuse ou d'une visionneuse réelle. """
        return True

    def __bind_event_handlers(self):
        """ Inscrivez-vous aux événements de fermeture, d'activation et de flottement du volet."""
        self.containerWidget.Bind(aui.EVT_AUI_PANE_CLOSE, self.onPageClosed)
        self.containerWidget.Bind(aui.EVT_AUI_PANE_ACTIVATED,
                                  self.onPageChanged)
        self.containerWidget.Bind(aui.EVT_AUI_PANE_FLOATED, self.onPageFloated)
    
    def __getitem__(self, index):
        return self.viewers[index]
    
    def __len__(self):
        return len(self.viewers)

    def addViewer(self, viewer, floating=False):
        """ Ajoute un nouveau volet avec la visionneuse spécifiée. """
        name = viewer.settingsSection()  # Nouvelle ligne
        self.containerWidget.addPane(viewer, viewer.title(), name, floating=floating)  # TypeError: DummyMainWindow.addPane() got multiple values for argument 'floating'
        self.viewers.append(viewer)
        if len(self.viewers) == 1:
            self.activateViewer(viewer)
        pub.subscribe(self.onStatusChanged, viewer.viewerStatusEventType())
        
    def closeViewer(self, viewer):
        """ Ferme la visionneuse spécifiée. """
        if viewer == self.activeViewer():
            self.advanceSelection(False)
        pane = self.containerWidget.manager.GetPane(viewer)
        self.containerWidget.manager.ClosePane(pane)
    
    def __getattr__(self, attribute):
        """ Transférez les attributs inconnus au visualiseur actif ou au premier visualiseur
            s'il n'y a pas de visualiseur actif.

        Prend en compte le stockage spécial d'attributs dans wxPython Phoenix.
        """
        # return getattr(self.activeViewer() or self.viewers[0], attribute)

        viewer = self.activeViewer() or (self.viewers[0] if self.viewers else None)
        if viewer is None:
            raise AttributeError(f"'ViewerContainer' object has no attribute '{attribute}'")
        # Pour les objets hérités de wx.PyEvent ou wx.PyCommandEvent sous Phoenix
        if hasattr(viewer, "_getAttrDict"):
            d = viewer._getAttrDict()
            if attribute in d:
                return d[attribute]
        # Fallback classique
        return getattr(viewer, attribute)

    def activeViewer(self):
        """ Renvoie la visionneuse active (sélectionnée). """
        all_panes = self.containerWidget.manager.GetAllPanes()
        for pane in all_panes:
            if pane.IsToolbar():
                continue
            if pane.HasFlag(pane.optionActive):
                if pane.IsNotebookControl():
                    notebook = aui.GetNotebookRoot(all_panes, pane.notebook_id)
                    return notebook.window.GetCurrentPage()
                else:
                    return pane.window
        return None
        
    def activateViewer(self, viewer_to_activate):
        """ Active (sélectionne) la visionneuse spécifiée. """
        self.containerWidget.manager.ActivatePane(viewer_to_activate)
        paneInfo = self.containerWidget.manager.GetPane(viewer_to_activate)
        if paneInfo.IsNotebookPage():
            self.containerWidget.manager.ShowPane(viewer_to_activate, True)
        self.sendViewerStatusEvent()

    def __del__(self):
        pass  # Ne transmettez pas le message Del à l'un des viewers.
    
    def onStatusChanged(self, viewer):
        if self.activeViewer() == viewer:
            self.sendViewerStatusEvent()
        pub.sendMessage("all.viewer.status", viewer=viewer)

    def onPageChanged(self, event):
        self.__ensure_active_viewer_has_focus()
        self.sendViewerStatusEvent()
        if self._notifyActiveViewer and self.activeViewer() is not None:
            self.activeViewer().activate()
        event.Skip()

    # @staticmethod
    def sendViewerStatusEvent(self):
        pub.sendMessage("viewer.status")

    def __ensure_active_viewer_has_focus(self):
        if not self.activeViewer():
            return
        window = wx.Window.FindFocus()
        if operating_system.isMacOsXTiger_OrOlder() and window is None:
            # Si SearchCtrl a le focus sur Mac OS X Tiger,
            # wx.Window.FindFocus renvoie Aucun. Si nous continuions,
            # le focus serait immédiatement placé sur le spectateur actif,
            # ce qui rendrait impossible pour l'utilisateur de saisir
            # le contrôle de recherche.
            return
        while window:
            if window == self.activeViewer():
                break
            window = window.GetParent()
        else:
            wx.LogDebug("ViwerContainer.__ensure_active_viewer_has_focus : Appel de CallAfter.")
            wx.CallAfter(self.activeViewer().SetFocus)
            wx.LogDebug("ViwerContainer.__ensure_active_viewer_has_focus : CallAfter passé avec succès.")

    def onPageClosed(self, event):
        if event.GetPane().IsToolbar():
            return
        window = event.GetPane().window
        if hasattr(window, "GetPage"):
            # window est un carnet, fermez chacune de ses pages
            for pageIndex in range(window.GetPageCount()):
                self.__close_viewer(window.GetPage(pageIndex))
        else:
            # window est une visionneuse, fermez-la
            self.__close_viewer(window)
        # Assurez-vous que nous avons un spectateur actif
        if not self.activeViewer():
            self.activateViewer(self.viewers[0])
        event.Skip()

    def __close_viewer(self, viewer):
        """ Fermez la visionneuse spécifiée et désabonnez tous ses gestionnaires d'événements. """
        # Lors de la fermeture d'une trame gérée par AUI, nous obtenons deux événements Close,
        # soyez prêt :
        if viewer in self.viewers:
            self.viewers.remove(viewer)
            viewer.detach()

    @staticmethod
    def onPageFloated(event):
        """ Donnez des touches d'accélération du volet flottant pour activer la visionneuse suivante et précédente."""
        viewer = event.GetPane().window
        table = wx.AcceleratorTable([(wx.ACCEL_CTRL, wx.WXK_PAGEDOWN,
                                     taskcoachlib.gui.menu.activateNextViewerId),
                                    (wx.ACCEL_CTRL, wx.WXK_PAGEUP,
                                     taskcoachlib.gui.menu.activatePreviousViewerId)])
        # table = wx.AcceleratorTable([(wx.ACCEL_CTRL, wx.WXK_PAGEDOWN,
        #                               activateNextViewerId),
        #                              (wx.ACCEL_CTRL, wx.WXK_PAGEUP,
        #                               activatePreviousViewerId)])
        viewer.SetAcceleratorTable(table)
