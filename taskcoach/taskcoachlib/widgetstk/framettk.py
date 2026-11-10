# -*- coding: utf-8 -*-
"""Cadre principal utilisant l'implémentation AUI basée sur ttk et Tkinter.

Ce module reprend l'interface de ``frame.py`` tout en utilisant les classes
AUI Tkinter du paquet ``taskcoachlib.thirdparty.tk3rdparty.aui_ttk``.
"""

import logging
import tkinter as tk

from taskcoachlib.thirdparty.tk3rdparty.aui_ttk import aui_tk_constants as aui
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.tkframemanager_elements import (
    AuiPaneInfo,
)
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkframemanager_auimanager import (
    AuiManager,
)

log = logging.getLogger(__name__)


class AuiManagedFrameWithDynamicCenterPane:
    """Fenêtre Tkinter dont les panneaux sont organisés par un gestionnaire AUI.

    Par défaut, le premier panneau non flottant devient le panneau central.
    Les panneaux non flottants ajoutés ensuite sont placés à droite. Il est
    possible de préciser une direction d'ancrage ou de créer un panneau
    initialement flottant.

    La gestion de la disposition, du flottement et du réamarrage est déléguée
    à :class:`AuiManager`.
    """

    def __init__(self, master=None, title="Task Coach AUI", root=None, **kwargs):
        """Crée la fenêtre principale et initialise son gestionnaire AUI.

        Args:
            master: Fenêtre ou widget Tkinter parent. Si absent, ``root`` est
                utilisé ; si les deux sont absents, une instance de ``Tk`` est
                créée.
            title: Titre de la fenêtre principale.
            root: Ancien nom de l'argument ``master``, conservé pour compatibilité.
            **kwargs: Options transmises à ``configure`` sur la fenêtre Tkinter.
                Les options non acceptées par Tk sont ignorées et consignées
                dans le journal de débogage.
        """
        # ``root`` est conservé comme alias de ``master`` pour compatibilité.
        if master is None:
            master = root
        self.root = master if master is not None else tk.Tk()
        self.root.title(title)

        for option, value in kwargs.items():
            try:
                self.root.configure(**{option: value})
            except tk.TclError:
                log.debug(
                    "AuiManagedFrameWithDynamicCenterPane : "
                    "option Tk ignorée : %s",
                    option,
                    exc_info=True,
                )

        self.manager = AuiManager(self.root)
        self._center_pane = None
        self._panes_by_name = {}
        self.bindEvents()

    def bindEvents(self):
        """Point d'extension réservé au raccordement des événements AUI.

        L'implémentation actuelle du gestionnaire met directement à jour
        l'interface via ``Update`` et ne reproduit pas encore les événements
        wxPython tels que ``EVT_AUI_PANE_CLOSE`` ou
        ``EVT_AUI_PANE_FLOATING``. Cette méthode reste donc volontairement
        vide afin de préserver l'interface de la classe d'origine.
        """
        return None

    def _pane_info(self, caption, name, floating=False):
        """Construit la description AUI d'un nouveau panneau.

        Les options communes (déplacement, flottement, fermeture et
        maximisation) sont configurées ici pour que tous les panneaux créés
        par :meth:`addPane` aient le même comportement de base.

        Args:
            caption: Texte affiché dans la barre de titre du panneau.
            name: Identifiant unique du panneau.
            floating: Indique si le panneau doit être initialement flottant.

        Returns:
            L'objet ``AuiPaneInfo`` configuré.
        """
        pane = (
            AuiPaneInfo()
            .Name(name)
            .Caption(caption)
            .DefaultPane()
            .Floatable(True)
            .Movable(True)
            .CloseButton(True)
            .MaximizeButton(True)
            .DestroyOnClose(True)
            .CaptionVisible(True)
            .BestSize(200, 200)
            .FloatingSize(300, 200)
        )
        if floating:
            pane.Float()
        return pane

    def addPane(self, window, caption, name, floating=False, dock_direction=None):
        """Ajoute un widget à la fenêtre en tant que panneau AUI.

        Si aucune direction n'est fournie, le premier panneau amarré devient
        le panneau central et les suivants sont placés à droite. Un panneau
        flottant est initialement placé à proximité de la fenêtre principale.

        Args:
            window: Widget Tkinter géré par le panneau.
            caption: Titre affiché dans l'en-tête du panneau.
            name: Identifiant unique et stable du panneau.
            floating: Si vrai, crée le panneau dans une fenêtre flottante.
            dock_direction: Direction d'ancrage AUI explicite, ou ``None``
                pour appliquer le placement par défaut.

        Returns:
            L'objet ``AuiPaneInfo`` créé et enregistré.

        Raises:
            ValueError: Si le nom est vide ou déjà utilisé.
            TypeError: Si ``window`` n'est pas un widget Tkinter.
        """
        # Valider les arguments avant de modifier l'état du gestionnaire.
        if not isinstance(name, str) or not name:
            raise ValueError("name doit être une chaîne non vide")
        if name in self._panes_by_name:
            raise ValueError("Un panneau porte déjà le nom {!r}".format(name))
        if not isinstance(window, tk.Misc):
            raise TypeError("window doit être un widget Tkinter")

        # Création du panneau
        pane = self._pane_info(caption, name, floating=floating)

        # Positionnement du panneau
        # if self._center_pane is None and not floating:
        #     pane.CenterPane()
        #     self._center_pane = pane
        # elif not floating:
        #     pane.Right()
        #     pane.Position(len(self.dockedPanes()))
        # else:
        if dock_direction is not None:
            pane.Direction(dock_direction)

        if floating:
            # Une position initiale proche de la fenêtre principale évite
            # qu'un Toplevel soit créé à une position écran imprévisible.
            try:
                self.root.update_idletasks()
                x = self.root.winfo_rootx() + 30
                y = self.root.winfo_rooty() + 30
            except tk.TclError:
                # La fenêtre peut ne pas encore être pleinement initialisée.
                x, y = 30, 30
            pane.FloatingPosition(x, y)
        elif dock_direction is None:
            if self._center_pane is None:
                pane.CenterPane()
            else:
                pane.Right()  # ou pane.Bottom() ??
                # La position est calculée avant AddPane : elle correspond
                # donc au nombre de panneaux déjà amarrés.
                pane.Position(len(self.dockedPanes()))

        # Ajout du panneau
        # Enregistrer également un panneau central demandé explicitement.
        # Sans cela, le panneau suivant pourrait être promu au centre.
        if not floating and self.isCenterPane(pane):
            self._center_pane = pane

        self.manager.AddPane(window, pane)
        self._panes_by_name[name] = pane
        # Mise à jour de l'interface
        self.manager.Update()
        return pane

    def _resolve_pane(self, pane_or_window_or_name):
        """Résout un panneau à partir de son descripteur, widget ou nom.

        Args:
            pane_or_window_or_name: Objet ``AuiPaneInfo``, widget associé ou
                nom du panneau.

        Returns:
            Le descripteur ``AuiPaneInfo`` correspondant. Si aucun panneau ne
            correspond, le gestionnaire renvoie un descripteur invalide, que
            les méthodes appelantes contrôlent avec ``IsOk``.
        """
        if isinstance(pane_or_window_or_name, AuiPaneInfo):
            return pane_or_window_or_name
        return self.manager.GetPane(pane_or_window_or_name)

    def setPaneTitle(self, window, title):
        """Modifie la légende du panneau identifié par son widget ou son nom.

        Si le panneau possède déjà une fenêtre flottante, son titre natif est
        également actualisé.

        Raises:
            KeyError: Si aucun panneau ne correspond à ``window``.
        """
        pane = self._resolve_pane(window)
        if not pane.IsOk():
            raise KeyError("Panneau introuvable: {!r}".format(window))
        pane.Caption(title)
        if pane.frame is not None and pane.frame.winfo_exists():
            pane.frame.title(title)
        self.manager.Update()

    def dockedPanes(self):
        """Renvoie les panneaux amarrés, hors barres d'outils et pages d'onglet.

        Un panneau masqué reste un panneau amarré : le filtrage porte donc sur
        son état d'ancrage, pas sur sa visibilité momentanée.
        """
        # version wx :
        # if USING_AGW:
        #     return [
        #         pane
        #         for pane in self.manager.GetAllPanes()
        #         if not pane.IsToolbar()
        #         and not pane.IsFloating()
        #         and not pane.IsNotebookPage()
        #     ]
        # else:
        #     # Version AUI:
        #     return [
        #         pane
        #         for pane in self.manager.GetAllPanes()
        #         if not pane.IsFloating() and not pane.IsToolbar()
        #     ]
        # version tk :
        return [
            pane
            for pane in self.manager.GetAllPanes()
            if pane.IsOk()
            and pane.IsDocked()
            and not pane.IsToolbar()
            and not pane.IsNotebookPage()
            # and pane.IsShown()
        ]

    def float(self, window):
        """Détache un panneau et le place dans une fenêtre flottante.

        ``window`` peut être le widget contenu, le nom du panneau ou son
        descripteur ``AuiPaneInfo``.

        Raises:
            KeyError: Si le panneau demandé n'existe pas.
        """
        pane = self._resolve_pane(window)
        if not pane.IsOk():
            raise KeyError("Panneau introuvable: {!r}".format(window))
        self.manager.FloatPane(pane)

    def dock(self, window):
        """Réintègre dans la fenêtre principale un panneau éventuellement flottant.

        ``window`` peut être le widget contenu, le nom du panneau ou son
        descripteur ``AuiPaneInfo``.

        Raises:
            KeyError: Si le panneau demandé n'existe pas.
        """
        pane = self._resolve_pane(window)
        if not pane.IsOk():
            raise KeyError("Panneau introuvable: {!r}".format(window))
        self.manager.DockPane(pane)

    @staticmethod
    def isCenterPane(pane):
        """Indique si le descripteur correspond à un panneau central.

        Les deux noms de constante sont testés pour rester compatible avec
        les variantes ``CENTER`` et ``CENTRE`` présentes selon les versions
        des constantes AUI.
        """
        return pane.dock_direction in {
            getattr(aui, "AUI_DOCK_CENTER", 4),
            getattr(aui, "AUI_DOCK_CENTRE", 4),
        }

    def Show(self):
        """Rend visible la fenêtre principale."""
        self.root.deiconify()

    def Hide(self):
        """Masque la fenêtre principale sans la détruire."""
        self.root.withdraw()

    def start_loop(self):
        """Lance la boucle événementielle principale de Tkinter."""
        self.root.mainloop()

    def destroy(self):
        """Libère le gestionnaire AUI puis détruit la fenêtre Tkinter.

        ``UnInit`` est appelé avant la destruction de la fenêtre afin que le
        gestionnaire puisse détacher ses propres liaisons et ressources.
        """
        self.manager.UnInit()
        self.root.destroy()


# Alias conservant le nom introduit par la conversion intermédiaire.
TtkManagedFrame = AuiManagedFrameWithDynamicCenterPane

__all__ = ["AuiManagedFrameWithDynamicCenterPane", "TtkManagedFrame"]
