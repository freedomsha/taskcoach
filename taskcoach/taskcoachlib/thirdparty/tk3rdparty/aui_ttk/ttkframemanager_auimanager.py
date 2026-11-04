# -*- coding: utf-8 -*-
"""Gestionnaire AUI basé sur ttk.PanedWindow et ttk.Notebook.

Cette version conserve l'API de tkframemanager_auimanager.py pour les
opérations de panneaux, mais utilise une disposition ttk explicite.
"""

import json
import tkinter as tk
from tkinter import ttk

from .tkframemanager_elements import (
    AuiDockInfo,
    AuiDockingGuideInfo,
    AuiDockUIPart,
    AuiPaneButton,
    AuiManagerEvent,
    AuiPaneInfo,
)
from .ttkauibook import AuiNotebook
from .aui_tk_constants import *

NonePaneInfo = AuiPaneInfo()


def _EscapeDelimiters(s):
    return s.replace("|", "\\|").replace(";", "\\;")


class TtkPanePlacement:
    """Paramètres de placement d'un panneau dans une grille."""

    POSITIONS = {"left", "right", "top", "bottom", "center"}
    RELATIONS = {"global", "intermediaire", "unitaire"}

    def __init__(self, relation="unitaire", position="centre", rank="last"):
        """Initialise les paramètres de placement."""
        if relation not in self.RELATIONS:
            raise ValueError("relation doit être global, intermediaire ou unitaire")
        if position not in self.POSITIONS:
            raise ValueError("position inconnue")
        if rank != "last" and not isinstance(rank, int):
            raise TypeError("rank doit être 'last' ou un entier")
        self.relation, self.position, self.rank = relation, position, rank


class TtkGridLayout:
    """Projection déterministe d'une disposition AUI vers tkinter.grid().

    La grille logique comporte trois lignes et trois colonnes(A revoir !!!). Les panneaux
    sont classés par direction, layer, row puis dock_pos. La reconstruction
    complète après chaque changement rend l'ajout, le retrait et le
    réordonnancement idempotents.
    """

    def __init__(self, parent):
        self.parent = parent
        self._entries = []
        parent.grid_propagate(False)
        # for index in range(3):
        #     parent.rowconfigure(index, weight=1 if index == 1 else 0)
        #     parent.columnconfigure(index, weight=1 if index == 1 else 0)
        self.rebuild()

    @staticmethod
    def _direction(pane):
        """
        Retourne la direction du panneau.

        A gauche(par défaut), à droite, au-dessus, en-dessous ou au centre.

        Args:
            pane: Panneau choisi.

        Returns:
            La direction du panneau.
        """
        direction = getattr(pane, "dock_direction", AUI_DOCK_LEFT)
        return {
            AUI_DOCK_LEFT: "left",
            AUI_DOCK_RIGHT: "right",
            AUI_DOCK_TOP: "top",
            AUI_DOCK_BOTTOM: "bottom",
        }.get(direction, "center")

    @staticmethod
    def _sort_key(entry):
        """
        Retourne la clé de tri pour un panneau.

        Args:
            entry: Le nom du panneau.

        Returns:
            La clé de tri pour le panneau.
        """
        pane = entry["pane"]
        return (
            getattr(pane, "dock_layer", 0),
            getattr(pane, "dock_row", 0),
            getattr(pane, "dock_pos", 0),
            entry["order"],
        )

    def add(self, widget, pane):
        """
        Ajoute un widget.

        Args:
            widget: Widget à ajouter.
            pane: Panneau où l'ajouter.

        Returns:

        """
        # Retirer le widget s'il est déjà présent
        self.remove(widget, rebuild=False)
        # Ajouter le widget à la grille
        self._entries.append(
            {"widget": widget, "pane": pane, "order": len(self._entries)}
        )
        # Reconstruire la grille
        self.rebuild()

    def remove(self, widget, rebuild=True):
        """
        Retire un widget.

        Args:
            widget: Widget à retirer.
            rebuild: Indique si la reconstruction doit être effectuée.

        Returns:
            True si le widget a été retiré, False sinon.

        """
        found = False
        for entry in list(self._entries):
            if entry["widget"] is widget:
                try:
                    widget.grid_forget()
                except tk.TclError:
                    pass
                self._entries.remove(entry)
                found = True
        if rebuild and found:
            self.rebuild()
        return found

    # def _slot(self, pane, side_index):
    def _slot(self, pane, side_index, nb_left, nb_right, nb_top, nb_bottom, has_center, top_offset, left_offset, central_height, central_width, nb_rows, nb_cols):
        """
        Positionne le panneau avec un index.

        Args:
            pane: Panneau à positionner.
            side_index: Index sur le côté.

        Returns:
            Les coordonnées de la position du panneau.
        """
        # TODO : à revoir avec la ToolBar et la barre d'info.
        direction = self._direction(pane)
        if direction == "left":
            # return side_index, 0, 1, 1
            return top_offset + side_index, 0, 1, 1
        if direction == "right":
            # return side_index, 2, 1, 1
            return top_offset + side_index, nb_cols - 1, 1, 1
        if direction == "top":
            # return 0, side_index, 1, 1
            return 0, left_offset + side_index, 1, 1
        if direction == "bottom":
            # return 2, side_index, 1, 1
            return nb_rows - 1, left_offset + side_index, 1, 1
        # return 1, 1, 1, 1
        return top_offset + central_height // 2, left_offset + central_width // 2, 1, 1

    def rebuild(self):
        """
        Reconstruit la grille Tkinter correspondant aux panes AUI.
        """
        # Retirer tous les widgets actuellement placés
        for entry in self._entries:
            try:
                entry["widget"].grid_forget()
            except tk.TclError:
                pass
                
        groups = {
            "left": [],
            "right": [],
            "top": [],
            "bottom": [],
            "center": [],
        }

        # Regrouper les widgets par direction, classer réellement chaque pane dans son groupe
        for entry in self._entries:
            # groups[self._direction(entry["pane"])].append(entry)
            direction = self._direction(entry["pane"])
            groups[direction].append(entry)
        # Tri des widgets par ordre d'ajout, conserver l'ordre AUI
        for entries in groups.values():
            entries.sort(key=self._sort_key)

        nb_left = len(groups["left"])
        nb_right = len(groups["right"])
        nb_top = len(groups["top"])
        nb_bottom = len(groups["bottom"])
        has_center = len(groups["center"]) > 0

        top_offset = 1 if nb_top > 0 else 0
        left_offset = 1 if nb_left > 0 else 0

        central_height = max(nb_left, nb_right, 1 if has_center else 0)
        central_width = max(nb_top, nb_bottom, 1 if has_center else 0)

        nb_rows = top_offset + central_height + (1 if nb_bottom > 0 else 0)
        nb_cols = left_offset + central_width + (1 if nb_right > 0 else 0)

        Placer les widgets dans la grille
        for direction, entries in groups.items():
            for index, entry in enumerate(entries):
                # Calculer la position du widget
                # row, column, rowspan, columnspan = self._slot(entry["pane"], index)
                row, column, rowspan, columnspan = self._slot(
                    entry["pane"], index, nb_left, nb_right, nb_top, nb_bottom,
                    has_center, top_offset, left_offset, central_height, central_width, nb_rows, nb_cols
                )
                # Stocker la position du widget
                entry["grid"] = (row, column, rowspan, columnspan)
                # Placer le widget dans la grille
                entry["widget"].grid(
                    row=row,
                    column=column,
                    rowspan=rowspan,
                    columnspan=columnspan,
                    sticky="nsew",
                    padx=1,
                    pady=1,
                )
        # Configurer l'expansion des lignes et des colonnes
        # for i in range(3):
        #     self.parent.rowconfigure(i, weight=1 if i == 1 else 0)
        #     self.parent.columnconfigure(i, weight=1 if i == 1 else 0)
        for row in range(nb_rows):
            weight = 1 if top_offset <= row < top_offset + central_height else 0
            self.parent.rowconfigure(row, weight=weight)
        for column in range(nb_cols):
            weight = 1 if left_offset <= column < left_offset + central_width else 0
            self.parent.columnconfigure(column, weight=weight)

    def clear(self):
        """
        Retire tous les widgets.
        """
        for entry in list(self._entries):
            try:
                entry["widget"].grid_forget()
            except tk.TclError:
                pass
        self._entries.clear()


class AuiManager:
    def __init__(self, managed_window=None, agwFlags=None):
        self._frame = None
        self._panes = []
        self._notebooks = []
        self._docks = []
        self._uiparts = []
        self._art = None
        self._agwFlags = AUI_MGR_DEFAULT if agwFlags is None else agwFlags
        self._active_pane = None
        self._updating = False
        self._dock_hosts = {}
        self._layout = None
        if managed_window is not None:
            self.SetManagedWindow(managed_window)

    def GetArtProvider(self):
        return self._art

    def SetArtProvider(self, art):
        self._art = art

    def GetAGWFlags(self):
        return self._agwFlags

    def SetAGWFlags(self, flags):
        self._agwFlags = flags

    def GetManagedWindow(self):
        return self._frame

    def GetFrame(self):
        return self._frame

    def SetFrame(self, frame):
        self._frame = frame

    def SetManagedWindow(self, managed_window):
        if managed_window is None:
            raise ValueError("managed_window ne peut pas être None")
        self.UnInit()
        self._frame = managed_window
        if isinstance(managed_window, tk.Misc):
            managed_window.bind("<Configure>", self.OnSize, add="+")
            managed_window.bind("<Destroy>", self._on_destroy_event, add="+")
        return True

    def _on_destroy_event(self, event):
        if event.widget is self._frame:
            self.UnInit()

    def GetPaneByWidget(self, window):
        return next(
            (pane for pane in self._panes if pane.window is window), NonePaneInfo
        )

    def GetPaneByName(self, name):
        return next((pane for pane in self._panes if pane.name == name), NonePaneInfo)

    def GetPane(self, item):
        return (
            self.GetPaneByName(item)
            if isinstance(item, str)
            else self.GetPaneByWidget(item)
        )

    def GetAllPanes(self):
        return self._panes

    def AddPane(self, window, arg1=None, arg2=None, target=None):
        """
        Ajoute un panneau AUI.

        Dépend du type de l'argument arg1.

        Args:
            window: Panneau à ajouter.
            arg1: Si c'est un int, il s'agit d'une direction, sinon
                  il s'agit d'une info de panneau.
            arg2: Si arg1 est une direction, il s'agit du nom du panneau.
            target: Position du panneau.

        Returns:
            L'objet ``AuiPaneInfo`` créé.
        """
        if isinstance(arg1, int):
            return self.AddPane2(window, arg1, arg2 or "")
        if target is not None:
            return self.AddPane4(window, arg1, target)
        return self.AddPane1(window, arg1)

    def AddPane1(self, window, pane_info=None):
        """
        Ajoute un panneau AUI ayant déjà une direction, une position, etc.

        Args:
            window: Panneau à ajouter
            pane_info: Informations sur le panneau

        Returns:
            L'objet ``AuiPaneInfo`` créé.

        """
        # Création du panneau
        pane = pane_info or AuiPaneInfo()
        pane.window = pane.window or window

        # Génération du nom du panneau si nécessaire
        if not pane.name:
            base = pane.caption.strip() or "pane"
            name = base
            index = 0
            while any(item.name == name for item in self._panes):
                index += 1
                name = f"{base}_{index}"
            pane.name = name

        # Ajout du panneau à la liste des panneaux
        self._panes.append(pane)

        # Mise à jour de l'interface
        self.Update()
        return pane

    def AddPane2(self, window, direction=AUI_DOCK_LEFT, caption=""):
        """
        Ajoute un panneau AUI avec une direction et un nom.

        Args:
            window: Panneau à ajouter.
            direction: Direction du panneau
            caption: Nom du panneau à afficher

        Returns:
            L'objet ``AuiPaneInfo`` créé.
        """
        pane = (
            AuiPaneInfo()
            .Window(window)
            .Caption(caption)
            .Direction(direction)
            .DefaultPane()
        )
        return self.AddPane1(window, pane)

    def AddPane3(self, window, direction=AUI_DOCK_LEFT, pos=(0, 0)):
        """
        Ajoute un panneau AUI flottant avec une direction et une position.

        Args:
            window: Panneau à ajouter.
            direction: Direction du panneau.
            pos: Position du panneau.

        Returns:
            L'objet ``AuiPaneInfo`` créé.
        """
        pane = self.AddPane2(window, direction)
        pane.floating_pos = pos
        return pane

    def AddPane4(self, window, pane_info, target):
        """
        Ajoute un panneau AUI avec une direction, une position, une taille,
        une note, une note


        Args:
            window: Panneau à ajouter.
            pane_info: Informations sur le panneau.
            target: Endroit de placement du panneau.

        Returns:
            L'objet ``AuiPaneInfo`` créé.
        """
        pane = self.AddPane1(window, pane_info)
        pane.notebook_id = 0 if target else -1
        return pane

    def InsertPane(self, window, pane_info, direction=AUI_DOCK_LEFT):
        """
        Incorpore le panneau dans la liste des panneaux.

        Args:
            window: Panneau à entrer.
            pane_info: Informations sur le panneau.
            direction: Position du panneau.

        Returns:
            L'objet ``AuiPaneInfo`` créé.
        """
        pane = pane_info or AuiPaneInfo()
        pane.window = window
        self._panes.insert(0, pane)
        self.Update()
        return pane

    def DetachPane(self, window):
        pane = self.GetPane(window)
        if pane.IsOk():
            self._undock_pane(pane)
            self._panes.remove(pane)
            pane.window = None
            self.Update()

    def ClosePane(self, pane):
        self._undock_pane(pane)
        if pane.frame is not None:
            pane.frame.destroy()
            pane.frame = None
        window = pane.window
        if window is not None and pane.IsDestroyOnClose():
            window.destroy()
        if pane in self._panes:
            self._panes.remove(pane)
        self.Update()

    def ShowPane(self, window, show=True):
        pane = self.GetPane(window)
        if pane.IsOk():
            pane.Show(show)
            self.Update()

    def ActivatePane(self, pane):
        self._active_pane = pane

    def CreateNotebook(self, parent=None):
        notebook = AuiNotebook(parent or self._frame)
        self._notebooks.append(notebook)
        return notebook

    def GetNotebooks(self):
        return self._notebooks

    def SetMasterManager(self, manager):
        self._masterManager = manager

    def SetAutoNotebookTabArt(self, art):
        self._autoNBTabArt = art

    def GetAutoNotebookTabArt(self):
        return getattr(self, "_autoNBTabArt", None)

    def SetAutoNotebookStyle(self, style):
        self._autoNBStyle = style

    def GetAutoNotebookStyle(self):
        return getattr(self, "_autoNBStyle", AUI_NB_DEFAULT_STYLE)

    def UpdateNotebook(self, notebook=None):
        return None

    # def SavePaneInfo(self, pane):
    #     return json.dumps(
    #         {
    #             "name": pane.name,
    #             "caption": pane.caption,
    #             "state": pane.state,
    #             "dir": pane.dock_direction,
    #             "layer": pane.dock_layer,
    #             "row": pane.dock_row,
    #             "pos": pane.dock_pos,
    #             "prop": pane.dock_proportion,
    #             "best": list(pane.best_size),
    #             "min": list(pane.min_size),
    #             "max": list(pane.max_size),
    #             "floatpos": list(pane.floating_pos),
    #             "floatsize": list(pane.floating_size),
    #             "notebookid": pane.notebook_id,
    #             "transparent": pane.transparent,
    #         }
    #     )
    def SavePaneInfo(self, pane):
        """
        Sérialise les informations d'un panneau au format texte historique de wxAUI.

        Le format produit est compatible avec SavePaneInfo() de wxPython
        et peut être utilisé dans une perspective commençant par ``layout2|``.

        Args:
            pane (AuiPaneInfo): Instance de AuiPaneInfo à sérialiser. Panneau dont les propriétés doivent être sauvegardées.

        Returns:
            str: Propriétés du panneau séparées par des points-virgules.
        """
        # # Prépare les propriétés dans l'ordre du format wxAUI.
        # values = [
        #     ("name", pane.name),
        #     ("caption", pane.caption),
        #     ("state", pane.state),
        #     ("dir", pane.dock_direction),
        #     ("layer", pane.dock_layer),
        #     ("row", pane.dock_row),
        #     ("pos", pane.dock_pos),
        #     ("prop", pane.dock_proportion),
        #     ("bestw", pane.best_size[0]),
        #     ("besth", pane.best_size[1]),
        #     ("minw", pane.min_size[0]),
        #     ("minh", pane.min_size[1]),
        #     ("maxw", pane.max_size[0]),
        #     ("maxh", pane.max_size[1]),
        #     ("floatx", pane.floating_pos[0]),
        #     ("floaty", pane.floating_pos[1]),
        #     ("floatw", pane.floating_size[0]),
        #     ("floath", pane.floating_size[1]),
        # ]
        #
        # # Convertit chaque propriété en une paire clé=valeur.
        # parts = []
        #
        # # Parcourt toutes les propriétés à sérialiser.
        # for key, value in values:
        #     # Convertit la valeur en texte.
        #     value = str(value)
        #
        #     # Protège les antislashs déjà présents dans les valeurs.
        #     value = value.replace("\\", "\\\\")
        #
        #     # Protège les séparateurs de panneaux présents dans les valeurs.
        #     value = value.replace("|", "\\|")
        #
        #     # Protège les séparateurs de propriétés présents dans les valeurs.
        #     value = value.replace(";", "\\;")
        #
        #     # Ajoute la propriété au résultat.
        #     parts.append(f"{key}={value}")
        #
        # # Assemble les propriétés en utilisant le séparateur wxAUI.
        # return ";".join(parts)
        # Échappe les caractères réservés dans les valeurs textuelles.
        result = "name=" + _EscapeDelimiters(pane.name) + ";"

        # Enregistre le titre du panneau en échappant les délimiteurs.
        result += "caption=" + _EscapeDelimiters(pane.caption) + ";"

        # Enregistre la cible de minimisation uniquement si elle existe.
        if pane.minimize_target:
            result += "minitarget=" + _EscapeDelimiters(pane.minimize_target) + ";"

        # Enregistre le mode de minimisation.
        result += "minimode=%u;" % pane.minimize_mode

        # Enregistre l'état et les paramètres d'ancrage.
        result += "state=%u;" % pane.state
        result += "dir=%d;" % pane.dock_direction
        result += "layer=%d;" % pane.dock_layer
        result += "row=%d;" % pane.dock_row
        result += "pos=%d;" % pane.dock_pos
        result += "prop=%d;" % pane.dock_proportion

        # Enregistre la taille préférée.
        result += "bestw=%d;" % pane.best_size[0]
        result += "besth=%d;" % pane.best_size[1]

        # Enregistre la taille minimale.
        result += "minw=%d;" % pane.min_size[0]
        result += "minh=%d;" % pane.min_size[1]

        # Enregistre la taille maximale.
        result += "maxw=%d;" % pane.max_size[0]
        result += "maxh=%d;" % pane.max_size[1]

        # Enregistre la position de la fenêtre flottante.
        result += "floatx=%d;" % pane.floating_pos[0]
        result += "floaty=%d;" % pane.floating_pos[1]

        # Enregistre la taille de la fenêtre flottante.
        result += "floatw=%d;" % pane.floating_size[0]
        result += "floath=%d;" % pane.floating_size[1]

        # Enregistre l'identifiant du notebook associé.
        result += "notebookid=%d;" % pane.notebook_id

        # Enregistre la transparence en dernier, comme dans wxPython.
        result += "transparent=%d" % pane.transparent

        # Retourne la chaîne au format historique.
        return result

    # def LoadPaneInfo(self, pane_part, pane):
    #     try:
    #         data = json.loads(pane_part)
    #     except (TypeError, ValueError):
    #         return pane
    #     pane.name = data.get("name", pane.name)
    #     pane.caption = data.get("caption", pane.caption)
    #     pane.state = data.get("state", pane.state)
    #     pane.dock_direction = data.get("dir", pane.dock_direction)
    #     pane.dock_layer = data.get("layer", pane.dock_layer)
    #     pane.dock_row = data.get("row", pane.dock_row)
    #     pane.dock_pos = data.get("pos", pane.dock_pos)
    #     pane.dock_proportion = data.get("prop", pane.dock_proportion)
    #     pane.best_size = tuple(data.get("best", pane.best_size))
    #     pane.min_size = tuple(data.get("min", pane.min_size))
    #     pane.max_size = tuple(data.get("max", pane.max_size))
    #     pane.floating_pos = tuple(data.get("floatpos", pane.floating_pos))
    #     pane.floating_size = tuple(data.get("floatsize", pane.floating_size))
    #     pane.notebook_id = data.get("notebookid", pane.notebook_id)
    #     pane.transparent = data.get("transparent", pane.transparent)
    #     return pane
    def LoadPaneInfo(self, pane_part, pane):
        """
        Restaure les propriétés d'un panneau depuis wxAUI ou depuis l'ancien JSON.

        Args:
            pane_part (str): Texte sérialisé ou ancien dictionnaire JSON.
            pane (AuiPaneInfo): Panneau existant à modifier.

        Returns:
            AuiPaneInfo: Panneau modifié, ou inchangé si les données sont invalides.
        """
        # Importe JSON pour assurer la lecture des anciennes sauvegardes.
        import json

        # Essaie d'abord de reconnaître l'ancien format JSON.
        try:
            data = json.loads(pane_part)
        # Le format texte wxAUI n'est pas du JSON.
        except (TypeError, ValueError):
            data = None

        # Traite les anciennes sauvegardes JSON.
        if isinstance(data, dict):
            # Restaure le nom sans remplacer la fenêtre Tkinter.
            pane.name = data.get("name", pane.name)

            # Restaure la légende enregistrée.
            pane.caption = data.get("caption", pane.caption)

            # Restaure l'état et les propriétés de positionnement.
            pane.state = data.get("state", pane.state)
            pane.dock_direction = data.get("dir", pane.dock_direction)
            pane.dock_layer = data.get("layer", pane.dock_layer)
            pane.dock_row = data.get("row", pane.dock_row)
            pane.dock_pos = data.get("pos", pane.dock_pos)
            pane.dock_proportion = data.get("prop", pane.dock_proportion)

            # Restaure les tailles en conservant leur représentation sous forme de tuples.
            pane.best_size = tuple(data.get("best", pane.best_size))
            pane.min_size = tuple(data.get("min", pane.min_size))
            pane.max_size = tuple(data.get("max", pane.max_size))
            pane.floating_pos = tuple(data.get("floatpos", pane.floating_pos))
            pane.floating_size = tuple(data.get("floatsize", pane.floating_size))

            # Restaure les propriétés propres à l'ancienne implémentation Tkinter.
            pane.notebook_id = data.get("notebookid", pane.notebook_id)
            pane.transparent = data.get("transparent", pane.transparent)

            # Retourne le panneau après restauration de l'ancien format.
            return pane

        # Vérifie que les données reçues sont une chaîne de caractères.
        if not isinstance(pane_part, str):
            return pane

        # Prépare un dictionnaire contenant les propriétés décodées.
        properties = {}

        # Sépare les propriétés en ignorant les points-virgules échappés.
        parts = []
        current = []
        escaped = False

        # Parcourt les caractères pour ne pas couper les valeurs contenant des séparateurs.
        for char in pane_part:
            # Ajoute le caractère courant sans le traiter comme séparateur s'il est échappé.
            if escaped:
                current.append(char)
                escaped = False
            # Mémorise la présence d'un antislash d'échappement.
            elif char == "\\":
                escaped = True
                current.append(char)
            # Termine une propriété sur un point-virgule non échappé.
            elif char == ";":
                parts.append("".join(current))
                current = []
            # Accumule les autres caractères.
            else:
                current.append(char)

        # Ajoute la dernière propriété après la boucle.
        if current:
            parts.append("".join(current))

        # Décode chaque propriété clé=valeur.
        for part in parts:
            # Ignore les éléments vides ou qui ne contiennent pas de signe égal.
            if "=" not in part:
                continue

            # Sépare la clé et la valeur au premier signe égal.
            key, value = part.split("=", 1)

            # Retire les espaces superflus autour de la clé.
            key = key.strip()

            # Décode les caractères échappés dans la valeur.
            value = value.replace("\\;", ";").replace("\\|", "|")
            value = value.replace("\\\\", "\\")

            # Enregistre la propriété décodée.
            properties[key] = value

        # Définit les propriétés numériques à restaurer.
        integer_fields = {
            "state": "state",
            "dir": "dock_direction",
            "layer": "dock_layer",
            "row": "dock_row",
            "pos": "dock_pos",
            "prop": "dock_proportion",
        }

        # Restaure les propriétés numériques lorsqu'elles sont valides.
        for key, attribute in integer_fields.items():
            # Ignore les propriétés absentes.
            if key not in properties:
                continue

            # Convertit la valeur en entier sans interrompre le chargement en cas d'erreur.
            try:
                setattr(pane, attribute, int(properties[key]))
            except (TypeError, ValueError):
                pass

        # Restaure le nom et la légende du panneau.
        pane.name = properties.get("name", pane.name)
        pane.caption = properties.get("caption", pane.caption)

        # Définit les paires de propriétés correspondant aux tailles.
        size_fields = {
            "best": ("bestw", "besth"),
            "min": ("minw", "minh"),
            "max": ("maxw", "maxh"),
            "floatpos": ("floatx", "floaty"),
            "floatsize": ("floatw", "floath"),
        }

        # Parcourt les différentes paires de dimensions.
        for attribute, (key_x, key_y) in size_fields.items():
            # Ignore les paires dont aucune valeur n'est enregistrée.
            if key_x not in properties and key_y not in properties:
                continue

            # Récupère la valeur actuelle pour préserver les dimensions absentes.
            current_value = getattr(pane, {
                "best": "best_size",
                "min": "min_size",
                "max": "max_size",
                "floatpos": "floating_pos",
                "floatsize": "floating_size",
            }[attribute])

            # Convertit chaque dimension indépendamment.
            try:
                x = int(properties.get(key_x, current_value[0]))
                y = int(properties.get(key_y, current_value[1]))
            except (TypeError, ValueError, IndexError):
                continue

            # Affecte le tuple de dimensions à l'attribut correspondant.
            if attribute == "best":
                pane.best_size = (x, y)
            elif attribute == "min":
                pane.min_size = (x, y)
            elif attribute == "max":
                pane.max_size = (x, y)
            elif attribute == "floatpos":
                pane.floating_pos = (x, y)
            elif attribute == "floatsize":
                pane.floating_size = (x, y)

        # Retourne le panneau existant sans toucher à sa fenêtre ni à son icône.
        return pane

    # def SavePerspective(self):
    #     return json.dumps(
    #         {"panes": [json.loads(self.SavePaneInfo(pane)) for pane in self._panes]}
    #     )
    def SavePerspective(self):
        """
        Sérialise et Sauvegarde la disposition au format historique wxAUI layout2.

        Returns:
            str: Disposition sérialisée, compatible avec le format texte wxAUI.
                 Perspective commençant par ``layout2|``.
        """
        # Initialise le résultat avec la version de format historique.
        result = "layout2|"

        # Sérialise et ajoute les panneaux existants dans leur ordre actuel.
        for pane in self._panes:
            # Ajoute les propriétés du panneau et le séparateur historique.
            result += self.SavePaneInfo(pane) + "|"

        # Ajoute les tailles des docks lorsqu'elles ont été enregistrées.
        for dock in self._docks:
            # Sérialise la direction, la couche, la rangée et la taille du dock.
            result += "dock_size(%d,%d,%d)=%d|" % (
                dock.dock_direction,
                dock.dock_layer,
                dock.dock_row,
                dock.size,
            )

        # Retourne la disposition de la perspective complète.
        return result


    # def LoadPerspective(self, layout):
    #     """
    #     Charge une disposition AUI à partir d'une sérialisation JSON
    #     créée avec la méthode SavePerspective.
    #
    #     Si update est True, la fenêtre est automatiquement mise à jour.
    #
    #     Args:
    #         layout: Une chaîne de caractères qui contient la sérialisation JSON.
    #         update: Pour mettre à jour immédiatement la fenêtre ou pas.
    #         restorecaption: Si False, les captions des pages seront restaurées,
    #                         sinon utiliser les dispositions définies dans le code.
    #         restoreminimize: Si False, restaure les paramètres enregistrés,
    #                          sinon utilise minimize_toolbar et
    #                          minimize_mode définis dans le code.
    #
    #     Returns:
    #         bool: True si la disposition a été chargée avec succès, False sinon.
    #     """
    #     # try:
    #     #     data = json.loads(layout)
    #     # except (TypeError, ValueError):
    #     #     return False
    #     # for item in data.get("panes", []):
    #     #     pane = AuiPaneInfo()
    #     #     self.LoadPaneInfo(json.dumps(item), pane)
    #     #     self._panes.append(pane)
    #     # self.Update()
    #     # return True
    #     try:
    #         data = json.loads(layout)
    #     except (TypeError, ValueError):
    #         return False
    #
    #     if not isinstance(data, dict):
    #         return False
    #
    #     saved_panes = data.get("panes", [])
    #     if not isinstance(saved_panes, list):
    #         return False
    #
    #     panes_by_name = {
    #         pane.name: pane
    #         for pane in self._panes
    #         if getattr(pane, "name", None)
    #     }
    #
    #     for item in saved_panes:
    #         if not isinstance(item, dict):
    #             continue
    #
    #         name = item.get("name")
    #         pane = panes_by_name.get(name)
    #
    #         if pane is None:
    #             continue
    #
    #         self.LoadPaneInfo(json.dumps(item), pane)
    #
    #     self.Update()
    #     return True

    # def LoadPerspective(
    #         self,
    #         layout,
    #         update=True,
    #         restorecaption=False,
    #         restoreminimize=False,
    # ):
    #     """
    #     Restaure une disposition des panneaux à partir d'une sérialisation JSON.
    #
    #     La disposition doit avoir été créée par SavePerspective(). Les panneaux
    #     sont recherchés parmi ceux déjà enregistrés dans le gestionnaire.
    #     Les panneaux inconnus sont ignorés afin de ne pas créer de fenêtres
    #     ou de composants inexistants.
    #
    #     Les icônes définies dans le code sont préservées. Les paramètres
    #     restorecaption et restoreminimize permettent de conserver les valeurs
    #     définies par le programme plutôt que celles enregistrées dans la
    #     disposition.
    #
    #     Args:
    #         layout (str): Chaîne JSON représentant la disposition à restaurer.
    #         update (bool): Met à jour l'affichage si True.
    #         restorecaption (bool): Conserve les légendes définies dans le code.
    #         restoreminimize (bool): Conserve les paramètres de minimisation
    #             définis dans le code.
    #
    #     Returns:
    #         bool: True si la disposition a été traitée, False si elle est invalide.
    #     """
    #     # Importe le module JSON si cet import n'existe pas déjà au niveau du fichier.
    #     import json
    #
    #     # Essaie de décoder la disposition enregistrée au format JSON.
    #     try:
    #         data = json.loads(layout)
    #     # Refuse les chaînes JSON invalides ou les types non acceptés par json.loads().
    #     except (TypeError, ValueError):
    #         return False
    #
    #     # Vérifie que la racine JSON est un dictionnaire.
    #     if not isinstance(data, dict):
    #         return False
    #
    #     # Récupère la liste des panneaux enregistrés dans la disposition.
    #     saved_panes = data.get("panes", [])
    #
    #     # Vérifie que la liste des panneaux possède le type attendu.
    #     if not isinstance(saved_panes, list):
    #         return False
    #
    #     # Indexe les panneaux déjà connus du gestionnaire à partir de leur nom.
    #     panes_by_name = {
    #         pane.name: pane
    #         for pane in self._panes
    #         if getattr(pane, "name", None)
    #     }
    #
    #     # Prépare un dictionnaire pour conserver les légendes définies dans le code.
    #     saved_captions = {}
    #
    #     # Prépare un dictionnaire pour conserver les icônes définies dans le code.
    #     saved_icons = {}
    #
    #     # Prépare un dictionnaire pour conserver les paramètres de minimisation.
    #     saved_minimize = {}
    #
    #     # Parcourt les panneaux existants avant de restaurer la disposition.
    #     for name, pane in panes_by_name.items():
    #         # Conserve la légende actuelle lorsque l'attribut existe.
    #         if hasattr(pane, "caption"):
    #             saved_captions[name] = pane.caption
    #
    #         # Conserve l'icône actuelle lorsqu'elle est définie.
    #         if hasattr(pane, "icon"):
    #             saved_icons[name] = pane.icon
    #
    #         # Conserve les paramètres de minimisation lorsqu'ils existent.
    #         if hasattr(pane, "minimize_target") and hasattr(pane, "minimize_mode"):
    #             saved_minimize[name] = (
    #                 pane.minimize_target,
    #                 pane.minimize_mode,
    #             )
    #
    #     # Parcourt les panneaux présents dans la disposition enregistrée.
    #     for item in saved_panes:
    #         # Ignore les entrées qui ne sont pas des dictionnaires.
    #         if not isinstance(item, dict):
    #             continue
    #
    #         # Récupère le nom du panneau à restaurer.
    #         name = item.get("name")
    #
    #         # Recherche le panneau correspondant parmi les panneaux existants.
    #         pane = panes_by_name.get(name)
    #
    #         # Ignore les panneaux qui n'existent pas dans l'interface actuelle.
    #         if pane is None:
    #             continue
    #
    #         # Restaure les propriétés enregistrées dans la disposition.
    #         self.LoadPaneInfo(json.dumps(item), pane)
    #
    #         # Réapplique la légende définie dans le code si demandé.
    #         if restorecaption and name in saved_captions:
    #             pane.Caption(saved_captions[name])
    #
    #         # Réapplique l'icône définie dans le code si elle existait.
    #         if name in saved_icons:
    #             pane.icon = saved_icons[name]
    #
    #         # Réapplique les paramètres de minimisation si demandé.
    #         if restoreminimize and name in saved_minimize:
    #             pane.minimize_target, pane.minimize_mode = saved_minimize[name]
    #
    #     # Met à jour l'interface uniquement si le paramètre le demande.
    #     if update:
    #         self.Update()
    #
    #     # Signale que la disposition a été traitée.
    #     return True

    def LoadPerspective(
            self,
            layout,
            update=True,
            restorecaption=False,
            restoreminimize=False,
    ):
        """
        Restaure une disposition depuis un fichier wxAUI ou un ancien fichier JSON.

        Args:
            layout (str): Disposition enregistrée.
            update (bool): Met à jour l'interface si True.
            restorecaption (bool): Conserve les légendes définies dans le code.
            restoreminimize (bool): Conserve les paramètres de minimisation du code.

        Returns:
            bool: True si la disposition a été reconnue, False sinon.
        """
        # Importe JSON pour lire les anciennes sauvegardes Tkinter.
        import json

        # Refuse les valeurs qui ne sont pas des chaînes.
        if not isinstance(layout, str):
            return False

        # Conserve la chaîne initiale pour détecter le format JSON historique.
        try:
            data = json.loads(layout)
        except (TypeError, ValueError):
            data = None

        # Traite les anciens fichiers JSON de Tkinter.
        if isinstance(data, dict):
            # Récupère la liste des panneaux enregistrés.
            saved_panes = data.get("panes", [])

            # Vérifie que cette liste est valide.
            if not isinstance(saved_panes, list):
                return False

            # Indexe les panneaux déjà existants par leur nom.
            panes_by_name = {
                pane.name: pane
                for pane in self._panes
                if getattr(pane, "name", None)
            }

            # Parcourt les panneaux sauvegardés.
            for item in saved_panes:
                # Ignore les éléments mal formés.
                if not isinstance(item, dict):
                    continue

                # Recherche le panneau existant correspondant.
                pane = panes_by_name.get(item.get("name"))

                # Ignore les panneaux qui n'existent plus.
                if pane is None:
                    continue

                # Préserve les propriétés non sérialisées avant la restauration.
                icon = pane.icon
                caption = pane.caption
                minimize_target = pane.minimize_target
                minimize_mode = pane.minimize_mode

                # Restaure les propriétés depuis l'ancien JSON.
                self.LoadPaneInfo(json.dumps(item), pane)

                # Préserve toujours l'icône définie dans le code.
                pane.icon = icon

                # Préserve la légende définie dans le code si demandé.
                if restorecaption:
                    pane.caption = caption

                # Préserve les paramètres de minimisation si demandé.
                if restoreminimize:
                    pane.minimize_target = minimize_target
                    pane.minimize_mode = minimize_mode

            # Met à jour l'affichage uniquement si demandé.
            if update:
                self.Update()

            # Signale que l'ancien format JSON a été traité.
            return True

        # Vérifie que la disposition utilise le format historique wxAUI.
        if not layout.startswith("layout2|"):
            return False

        # Retire l'identifiant de format situé avant le premier séparateur.
        input_text = layout[len("layout2|"):]

        # Protège les séparateurs échappés avant de découper les panneaux.
        input_text = input_text.replace("\\|", "\a")
        input_text = input_text.replace("\\;", "\b")

        # Sépare les panneaux et les informations sur les docks.
        parts = input_text.split("|")

        # Indexe les panneaux existants par leur nom.
        panes_by_name = {
            pane.name: pane
            for pane in self._panes
            if getattr(pane, "name", None)
        }

        # Conserve les légendes, les icônes et les paramètres de minimisation du code.
        saved_properties = {
            name: (
                pane.caption,
                pane.icon,
                pane.minimize_target,
                pane.minimize_mode,
            )
            for name, pane in panes_by_name.items()
        }

        # Prépare la liste des informations de docks restaurées.
        restored_docks = []

        # Parcourt chaque segment de la disposition.
        for part in parts:
            # Restaure les séparateurs protégés dans le segment.
            part = part.replace("\a", "|").replace("\b", ";")

            # Ignore les segments vides.
            if not part.strip():
                continue

            # Détecte une information de taille de dock.
            if part.startswith("dock_size("):
                # Analyse le format dock_size(direction,layer,row)=size.
                try:
                    dock_key, size_text = part.split("=", 1)
                    coordinates = dock_key[len("dock_size("):-1].split(",")

                    # Convertit les quatre valeurs en entiers.
                    direction, layer, row = map(int, coordinates)
                    size = int(size_text)

                    # Crée un objet de dock avec les valeurs restaurées.
                    dock = AuiDockInfo()
                    dock.dock_direction = direction
                    dock.dock_layer = layer
                    dock.dock_row = row
                    dock.size = size

                    # Ajoute le dock restauré à la liste temporaire.
                    restored_docks.append(dock)

                # Ignore les informations de dock mal formées.
                except (ValueError, TypeError):
                    continue

                # Passe au segment suivant.
                continue

            # Crée un panneau temporaire pour extraire son nom.
            temporary_pane = AuiPaneInfo()

            # Restaure les propriétés dans le panneau temporaire.
            self.LoadPaneInfo(part, temporary_pane)

            # Recherche le panneau existant correspondant au nom restauré.
            pane = panes_by_name.get(temporary_pane.name)

            # Ignore les panneaux inconnus sans créer de nouvelle fenêtre.
            if pane is None:
                continue

            # Récupère les propriétés du code enregistrées avant la restauration.
            caption, icon, minimize_target, minimize_mode = saved_properties[pane.name]

            # Restaure les propriétés de disposition dans le panneau existant.
            self.LoadPaneInfo(part, pane)

            # Préserve toujours l'icône définie dans le code.
            pane.icon = icon

            # Restaure la légende du code si le paramètre le demande.
            if restorecaption:
                pane.caption = caption

            # Restaure les paramètres de minimisation du code si demandé.
            if restoreminimize:
                pane.minimize_target = minimize_target
                pane.minimize_mode = minimize_mode

        # Remplace les informations de docks uniquement si des docks ont été lus.
        if restored_docks:
            self._docks = restored_docks

        # Met à jour l'affichage uniquement si demandé.
        if update:
            self.Update()

        # Signale que le format wxAUI a été reconnu et traité.
        return True

    def _direction(self, pane):
        return {
            AUI_DOCK_LEFT: "left",
            AUI_DOCK_RIGHT: "right",
            AUI_DOCK_TOP: "top",
            AUI_DOCK_BOTTOM: "bottom",
        }.get(pane.dock_direction, "top")

    def _host_for(self, pane):
        if self._layout is None:
            self._layout = TtkGridLayout(self._frame)
        return self._layout.root

    def _placement_for(self, pane):
        position = self._direction(pane)
        position = {
            "left": "left",
            "right": "right",
            "top": "bottom",
            "bottom": "bottom",
        }.get(position, "center")
        return TtkPanePlacement("global", position, getattr(pane, "dock_pos", "last"))

    def _undock_pane(self, pane):
        window = pane.window
        if window is None:
            return
        if self._layout is not None:
            self._layout.remove(window)
        for method in ("pack_forget", "grid_forget", "place_forget"):
            try:
                getattr(window, method)()
            except (AttributeError, tk.TclError):
                pass

    def _float_pane(self, pane):
        if pane.frame is None or not pane.frame.winfo_exists():
            pane.frame = tk.Toplevel(self._frame)
        floating = pane.frame
        floating.title(pane.caption or pane.name)
        self._undock_pane(pane)
        window = pane.window
        if window is not None:
            try:
                window.pack_forget()
            except (AttributeError, tk.TclError):
                pass
            try:
                window.configure(in_=floating)
            except (AttributeError, tk.TclError):
                pass
            window.pack(fill="both", expand=True)
        if pane.floating_pos:
            floating.geometry(f"+{pane.floating_pos[0]}+{pane.floating_pos[1]}")
        if pane.floating_size and pane.floating_size[0] > 0:
            floating.geometry(f"{pane.floating_size[0]}x{pane.floating_size[1]}")
        return floating

    def _dock_pane(self, pane):
        window = pane.window
        if window is None:
            return
        if pane.frame is not None and pane.frame.winfo_exists():
            pane.frame.withdraw()
        if self._layout is None:
            self._layout = TtkGridLayout(self._frame)
        if not any(e["widget"] is window for e in self._layout._entries):
            self._layout.add(window, pane)

    def Update(self):
        if self._updating:
            return
        self._updating = True
        try:
            for pane in self._panes:
                if pane.window is None:
                    continue
                if pane.IsFloating():
                    self._float_pane(pane)
                elif pane.IsShown():
                    self._dock_pane(pane)
                else:
                    self._undock_pane(pane)
        finally:
            self._updating = False

    def LayoutAll(self):
        self.Update()

    def OnSize(self, event=None):
        self.Update()

    def RecalculatePaneSizes(self):
        return None

    def Render(self):
        return None

    def FloatPane(self, pane):
        """Détache le contenu du panneau et l'affiche dans un Toplevel."""
        if not pane.IsOk():
            return None
        pane.Float()
        self.Update()
        return pane.frame

    def DockPane(self, pane):
        """Réintègre le contenu du panneau dans sa zone d'amarrage."""
        if not pane.IsOk():
            return False
        pane.Dock()
        self.Update()
        return True

    def CreateFloatingFrame(self, pane):
        return self._float_pane(pane)

    def Initialize(self):
        return self.Update()

    def UnInit(self):
        for pane in getattr(self, "_panes", []):
            if pane.frame is not None:
                try:
                    pane.frame.destroy()
                except tk.TclError:
                    pass
                pane.frame = None
        if self._layout is not None:
            self._layout.clear()
            try:
                self._layout.root.destroy()
            except tk.TclError:
                pass
            self._layout = None
        self._dock_hosts = {}

    def OnDestroy(self):
        self.UnInit()


class AuiManager_DCP(AuiManager):
    pass
