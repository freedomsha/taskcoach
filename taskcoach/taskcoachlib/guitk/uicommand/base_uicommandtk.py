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
"""
# J'ai remplacé les éléments spécifiques à wxPython par leurs équivalents dans tkinter :
#     wx a été remplacé par tkinter.
#
#     wx.EVT_MENU et wx.EVT_UPDATE_UI n'existent pas directement.
#     J'ai utilisé l'option command de tkinter.Menu.add_command et
#     de tkinter.Button pour lier les actions.
#
#     wx.ArtProvider.GetBitmap a été remplacé par une méthode __getBitmap
#     qui suppose l'existence d'une classe ArtProvider pour Tkinter.
#     Tu devras créer cette classe (tkartprovider.py)
#     qui gérera le chargement des icônes (.png, .gif, etc.) en tkinter.PhotoImage.
#
#     Les méthodes bind et unbind ont été retirées
#     car la liaison se fait directement lors de la création du widget.
#
#     J'ai fait quelques ajustements pour que la classe UICommand
#     puisse être utilisée pour créer des boutons de barre d'outils,
#     ce qui correspond à la logique de la méthode appendToToolBar.
#
# Ce code devrait te donner une base solide.
# TODO :
# Il y a quelques points à revoir, notamment la gestion des icônes (tkartprovider.py)
# et la mise à jour des labels de menu.
#
# J'ai mis à jour la méthode mainWindow() pour qu'elle tente d'obtenir
# l'instance de l'application TkinterApplication via une méthode statique getInstance().
# J'ai également importé TkinterApplication pour que la référence soit disponible.
# Ce changement permettra à la classe UICommand d'interagir correctement
# avec la fenêtre principale de l'application, en supposant que le singleton TkinterApplication
# a une référence à MainWindow.
#
# Pour que cela fonctionne, tu devras t'assurer que la classe TkinterApplication
# a une méthode de classe getInstance() qui retourne l'instance unique du singleton,
# et que cette instance a un attribut mainwindow qui référence la fenêtre principale.

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from taskcoachlib import operating_system
from taskcoachlib.guitk.artprovidertk import IconProvider, art_provider_tk
# from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.guitk.artprovidertk import ArtProvider  # Assumes you have created this
from taskcoachlib.guitk.artprovidertk import ArtProviderTk  # Assumes you have created this
# from taskcoachlib.application.tkapplication import TkinterApplication

log = logging.getLogger(__name__)

''' User interface commands (subclasses of UICommand) are actions that can
    be invoked by the user via the user interface (menu's, toolbar, etc.).
    See the Taskmaster pattern described here:
    http://www.objectmentor.com/resources/articles/taskmast.pdf
'''  # pylint: disable=W0105


class UICommand(object):
    """
    Commande d'interface utilisateur de base pour Tkinter.

    Une classe pour représenter une commande UI.

    Une UICommand est une action qui peut être associée à des menus ou des barres d'outils.
    Elle contient le texte du menu, l'aide contextuelle à afficher, et gère les événements.
    Les sous-classes doivent implémenter la méthode doCommand() et peuvent
    remplacer enabled() pour personnaliser l'activation des commandes.

    Attributs :
        menuText (str) : Texte du menu.
        helpText (str) : Texte d'aide.
        bitmap (str) : Nom de l'icône à afficher.
        bitmap2 (str) : Nom de l'icône secondaire.
        kind (str) : Type d'élément (normal, checkbutton, etc.).
        id (int) : Identifiant unique pour l'élément.
        toolbar (tk.Frame) : Barre d'outils associée.
        menuItems (list) : Liste des éléments de menu auxquels cette commande est associée.
        app (tk.Tk) : L'instance principale de l'application Tkinter.
    """

    def __init__(self, menuText="", helpText="",
                 # bitmap="nobitmap",
                 bitmap="",
                 kind="normal", id=None, bitmap2=None,
                 *args, **kwargs):  # pylint: disable=W0622
        """
        Initialise la commande d'interface utilisateur.

        Args :
            menuText (str, optionnel) : Le texte à afficher dans le menu. Par défaut à "".
            helpText (str, optionnel) : Le texte d'aide contextuelle. Par défaut à "".
            bitmap (str, optionnel) : L'icône du menu ou de la barre d'outils. Par défaut à "nobitmap".
            kind (wx.ItemKind, optionnel) : Le type d'élément (normal, checkable, etc.). Par défaut à wx.ITEM_NORMAL.
            id (int, optionnel) : L'identifiant de la commande. Si non spécifié, un identifiant unique sera généré.
            bitmap2 (str, optionnel) : Icône secondaire pour les éléments checkables. Par défaut à None.
        """
        super().__init__()
        # Le texte à afficher dans le menu :
        menuText = menuText or f"<{_('None')}>"
        # self.menuText = menuText
        self.menuText = menuText if '&' in menuText else '&' + menuText
        # Le texte d'aide contextuelle :
        self.helpText = helpText
        # Le nom de l'icône :
        self.bitmap = bitmap
        # Nom de l'icône secondaire pour les éléments checkables :
        self.bitmap2 = bitmap2
        # Le type d'élément (normal, checkbutton, radiobutton) :
        self.kind = kind
        # L'identifiant de la commande.
        # self.id = id if id is not None else IdProvider.get()
        self.id = id  # IdProvider.get() ?
        #
        self.toolbar = None
        #
        self.menuItems = []
        self._kwargs = kwargs
        # L'instance principale de l'application Tkinter
        self.app = self.mainWindow()

    def __del__(self):
        """ Libère l'identifiant lors de la destruction de l'objet. """
        # IdProvider.put(self.id)

    def __eq__(self, other):
        return self is other

    def uniqueName(self):
        """ Retourne le nom unique de la classe de commande. """
        return self.__class__.__name__

    # Le problème : Tkinter n'accepte pas d'option type.
    # Pour créer un "checkbutton" dans un menu,
    # il faut appeler une méthode différente : menu.add_checkbutton().
    # Explication de la correction
    #
    #     Plus d'option type : J'ai supprimé menu_item_options['type'] = 'checkbutton'.
    #
    #     Appel de la bonne méthode : Le code vérifie maintenant self.kind.
    #
    #         Si self.kind == "checkbutton", il utilise menu.add_checkbutton().
    #
    #         Si self.kind == "radiobutton", il utilise menu.add_radiobutton().
    #
    #         Sinon, il utilise menu.add_command().
    #
    #     Variables Tkinter : Pour que les checkbutton et radiobutton fonctionnent,
    #     ils ont besoin d'une variable Tkinter (tk.BooleanVar ou tk.StringVar).
    #     J'ai ajouté la logique pour les lier (vous les aviez déjà définis dans settings_uicommandtk.py,
    #     donc ils devraient être trouvés).
    #
    #     Gestion de la position : J'ai corrigé la logique pour utiliser menu.insert_...()
    #     si une position est donnée, et menu.add_...() sinon.
    # Ne pas utiliser add_to_menu pour être raccord avec le reste de l'application compatible wxpython.
    def addToMenu(self, menu, window, position=None):
        # """ Ajoute un sous-menu au Menu menu.
        """
        Ajoute cette commande à un menu.

        Les paramètres du menu doivent être menuText, HelpText et kind.

        Args :
            menu (tk.Menu) : Le menu parent auquel ajouter la commande.
            window (tk.Tk ou tk.Toplevel) : La fenêtre parente associée.
            position (int, optionnel) : La position dans le menu.
        """
        assert isinstance(menu, tk.Menu), f"[BUG] addToMenu() appelé avec un mauvais argument : type(menu) = {type(menu)}"

        log.debug(f"💥UICommand.addToMenu essaye d'ajouter le sous-menu {self.menuText} d'ID={self.id} dans le menu {menu} à la position {position}.")

        # --- Options communes à tous les types ---
        # menu_item_options = {
        #     'label': self.getMenuText(),
        #     'command': self.onCommandActivate,
        # }
        menu_item_options = {
            'label': self.getMenuText(),
            'command': self.onCommandActivate,  # ne pas mettre de parenthèse !
            'state': 'normal' if self.enabled() else 'disabled'
        }
        log.debug(f"UICommand.addToMenu : création de menu_item_options={menu_item_options}.")
        # menu_item_options['label'] = self.getMenuText()
        # menu_item_options['command'] = self.onCommandActivate
        # menu_item_options['state'] = 'normal' if self.enabled() else 'disabled'

        # Accélérateur (texte affiché)
        # Note : 'accelerator' est un attribut défini dans uicommandtk.py
        if hasattr(self, 'accelerator') and self.accelerator:
            menu_item_options['accelerator'] = self.accelerator

        # Icône
        # # Check for bitmap and add it if available
        # if self.bitmap:
        #     bitmap = self.__getBitmap(self.bitmap)
        #     # bitmap = ArtProviderTk.GetBitmap(self.bitmap, self)
        #     if bitmap:
        #         # Assurez-vous que l'icône est une instance de PhotoImage de Tkinter
        #         menu_item_options['image'] = bitmap
        #         menu_item_options['compound'] = 'left'  # Place l'image à gauche du texte

        # TODO : à revoir une fois la barre de menu bien implémentée !
        # Cette condition crée un problème : les listes de menu ne s'affichent plus !
        # if hasattr(self, 'bitmap') and self.bitmap:
        #     # menu_item_options['image'] = self.bitmap  # Erreur, il faut obtenir l'image ici, le nom ne suffit pas !
        #     try:
        #         menu_item_options['image'] = artprovidertk.getIcon(self.bitmap)
        #         log.debug("")
        #     except Exception as e:
        #         log.error(f"Erreur lors de la récupération de l'icône '{self.bitmap}': {e}", exc_info=True)
        #         menu_item_options['image'] = artprovidertk.getIcon('No icon')
        #     menu_item_options['compound'] = 'left'  # Place l'icône à gauche du texte
        #     # compound : Cette option est utilisée pour spécifier la position de l'icône
        #     # par rapport au texte. 'left' place l'icône à gauche du texte.

        # --- Logique spécifique au type ---

        # Déterminer la méthode d'ajout (add ou insert)
        use_insert = position is not None
        if use_insert:
            # L'option 'index' n'est pas un argument standard pour add/insert,
            # nous devons l'utiliser séparément.
            # del menu_item_options['label']  # 'label' est géré par 'index' pour insert
            pass  # La logique d'insertion est gérée ci-dessous

        # add_method = None
        add_method = menu.add_command  # méthode standard si non définit

        # Handle different kinds of menu items
        log.debug(f"Vérification de self.kind={self.kind} qui doit être 'normal', 'checkbutton' ou 'radiobutton'")
        if self.kind == "checkbutton":
            # menu_item_options['type'] = 'checkbutton'
            # # You would need a variable to track the state, like a tkinter.BooleanVar
            # # For now, we'll just add the command
            # # TODO: Implement state variable for checkbutton
            # log.warning("Tkinter checkbutton kind not fully implemented, state variable is missing.")
            # Les checkbuttons (de settings_uicommandtk.py) ont un attribut _variable
            if hasattr(self, '_variable') and isinstance(self._variable, (tk.BooleanVar, tk.StringVar)):
                menu_item_options['variable'] = self._variable
                log.debug(f"UICommand '{self.menuText}' est un 'checkbutton' avec variable={self._variable}")
            else:
                log.warning(f"UICommand '{self.menuText}' est 'checkbutton' mais n'a pas de '_variable' Tkinter.")

            add_method = menu.insert_checkbutton if use_insert else menu.add_checkbutton

        elif self.kind == "radiobutton":
            # Les radiobuttons (de settings_uicommandtk.py) ont _variable et value
            if hasattr(self, '_variable') and isinstance(self._variable, (tk.StringVar, tk.IntVar)):
                menu_item_options['variable'] = self._variable
                # La 'value' est cruciale pour un radiobutton
                if hasattr(self, 'value'):
                    menu_item_options['value'] = self.value
                    log.debug(f"UICommand '{self.menuText}' est un 'radiobutton' avec value={self.value}")
                else:
                    log.error(f"UICommand '{self.menuText}' est 'radiobutton' mais n'a pas d'attribut 'value'.")
            else:
                log.warning(f"UICommand '{self.menuText}' est 'radiobutton' mais n'a pas de '_variable' Tkinter.")

            add_method = menu.insert_radiobutton if use_insert else menu.add_radiobutton

        elif self.kind == "normal":
            log.debug(f"Add normal Command : {self.menuText}")
            # self._menu.add_command(
            # self.add_command(
            #     label=menu_text,
            #     command=command_func,
            #     accelerator=shortcut_text,
            #     state=state
            # )
            # add_method = menu.insert_command if use_insert else menu.add_command
            if use_insert:
                add_method = menu.insert_command
                log.debug("Utilisation de menu.insert_command")
            else:
                add_method = menu.add_command
                log.debug("Utilisation de menu.add_command")

        else:  # "normal"
            # add_method = menu.insert_command if use_insert else menu.add_command
            log.debug(f"! self.kind={self.kind} est inconnu !")

        # if position is None:
        #     menu.add_command(**menu_item_options)
        # else:
        #     menu.insert_command(position, **menu_item_options)
        # --- Ajout final ---
        # Ajouter l'élément au menu
        try:
            if use_insert:
                # La méthode insert prend la position comme premier argument
                add_method(position, **menu_item_options)
                log.debug(f"Ajout de '{self.menuText}' au menu avec position={position} et options={menu_item_options}")
            else:
                # Ajouter l'icône
                add_method(**menu_item_options)
                log.debug(f"Ajout de '{self.menuText}' au menu {menu} avec options={menu_item_options}")
        except tk.TclError as e:
            log.error(f"Erreur Tcl lors de l'ajout de '{self.menuText}' au menu : {e}. Options: {menu_item_options}", exc_info=True)
            pass  # Ne pas planter si une option est mauvaise

        self.menuItems.append(menu)  # Stocke la référence au menu. Est-ce nécessaire avec tkinter ?
        log.debug(f"Le premier menu de {menu} est {menu.entrycget(0, 'label')}.")
        log.debug(f"Le menu {menu} est référencé dans {self.menuItems}.")

    def addBitmapToMenuItem(self, menuItem) -> None:
        """Ignorer! Tkinter gère les icônes directement via les options du menu. """
        pass

    def removeFromMenu(self, menu):
        # Cette méthode est un peu plus complexe avec Tkinter car il n'y a pas
        # d'ID d'élément de menu à proprement parler pour le unbind.
        # Nous pouvons essayer de trouver l'index de l'élément par son texte.
        # TODO: A revoir pour une suppression plus fiable
        for i in range(menu.index('end') + 1):
            if menu.entrycget(i, 'label') == self.getMenuText():
                menu.delete(i)
                break
        if menu in self.menuItems:
            self.menuItems.remove(menu)

    def appendToToolBar(self, toolbar):
        """
        Ajoute cette commande à une barre d'outils (Frame).

        Crée un tk.Button pour la barre d'outils.

        Args :
            toolbar (tk.Frame) : La barre d'outils à laquelle ajouter la commande.

        Returns :
            (int) : L'identifiant de la commande.
        """
        self.toolbar = toolbar
        # Load the bitmap
        # the_bitmap = self.__getBitmap(_("No icon"))
        # Tentative de récupération de l'image
        the_bitmap = None
        # bitmap = Image.open(self.image_path)
        # self.normal_image = ImageTk.PhotoImage(bitmap) # Store the normal image
        if hasattr(self, 'bitmap') and self.bitmap:
            the_bitmap = self.__getBitmap(self.bitmap)  # TODO : trouver une alternative à wx.core.ToolBar.GEtToolBitmapSize()

        # Si l'image spécifique échoue, on tente l'image par défaut
        if not the_bitmap:
            the_bitmap = self.__getBitmap(_("No icon"))

        # # Create a disabled version (e.g., grayscale)
        # disabled_image = the_bitmap.convert('L')  # Convert to grayscale
        # self.disabled_image = ImageTk.PhotoImage(disabled_image)  # Store the disabled image

        button_options = {
            # 'image': the_bitmap,
            # image=self.normal_image,  # Use the normal image initially  # TODO
            'state': tk.NORMAL,        # Start as enabled
            'command': self.onCommandActivate,  # ou self.doCommand ?  # TODO
            'bd': 0,
            'relief': 'flat',
            'padx': 5,
            'pady': 5,
            # compound=tk.TOP          # To put image above text
        }

        # Si on a une image, on l'utilise. Sinon, on met du texte.
        if the_bitmap:
            button_options['image'] = the_bitmap
        else:
            # Fallback : Utiliser le texte du menu ou un point d'interrogation
            text_label = self.getMenuText()
            # On nettoie le texte (retirer les raccourcis clavier ex: "New\tCtrl+N")
            if "\t" in text_label:
                text_label = text_label.split("\t")[0]
            button_options['text'] = text_label if text_label else "??"
            # Optionnel : ajouter compound si on veut gérer texte et image
            # button_options['compound'] = tk.LEFT

        if self.kind == "checkbutton":
            # TODO: Implement a checkbutton for the toolbar copier la méthode add_to_menu !
            log.warning("Tkinter checkbutton kind for toolbar not fully implemented.")
            # Pour un checkbutton, on utiliserait tk.Checkbutton avec indicatoron=0

        # if the_bitmap:
        #     button = tk.Button(toolbar, **button_options)  # TODO : la variante quand le bouton est grisé
        #     button.image = the_bitmap
        #     button.pack(side="left", padx=2, pady=2)  # ou (padx, padx)=(2,2)
        #     # Stocke le bouton pour la gestion de l'état
        #     self._kwargs['button'] = button
        #     log.debug(f"UICommand.appendToToolBar : le bouton {button.__class__.__name__} avec les options {button_options} a été ajouté à la toolbar {toolbar.__class__.__name__}.")

        # Création du bouton (qu'il y ait une image ou non)
        button = tk.Button(toolbar, **button_options)

        # Important : Garder une référence à l'image pour éviter le Garbage Collector
        if the_bitmap:
            button.image = the_bitmap

        button.pack(side="left", padx=2, pady=2)

        # Stocke le bouton pour la gestion de l'état (enable/disable)
        self._kwargs['button'] = button

        log.debug(f"UICommand.appendToToolBar : Bouton créé pour '{self.menuText}' (Icone trouvée: {bool(the_bitmap)})")

        # TODO : Lier l'action du button !
        # Avec ces changements, le bouton sera :
        #
        #     Fonctionnel via l'attribut command lors du clic.
        #
        #     Activable via le raccourci clavier.
        #
        #     Mis à jour dynamiquement (activé/désactivé) par la boucle onUpdateUI.
        toolbar.bind(self, self.id)
        # return self.id
        return button  # Return the button instance

    def onCommandActivate(self, event=None):
        """ Active la commande. """
        log.info(f"onCommandActivate appelée pour {self.menuText}")
        if self.enabled(event):
            try:
                # return self.doCommand(event)
                return self.doCommand()
            except Exception as e:
                log.error(f"UICommand.onCommandActivate : Error executing command: {e}", exc_info=True)
                messagebox.showerror("Error", f"UICommand.onCommandActivate : An error occurred: {e}")
        else:
            log.warning(f"Commande {self.menuText} désactivée, donc doCommand n'est pas appelée.")
            return None

    def __call__(self, *args, **kwargs):
        self.onCommandActivate()

    def doCommand(self):
        """
        Méthode à implémenter dans les sous-classes pour exécuter la commande.
        """
        raise NotImplementedError  # pragma: no cover

    # def enabled(self):
    def enabled(self, event=None):
        """
        Détermine si la commande est activée.

        Peut être remplacé dans une sous-classe.

        Args:
            event: L'événement qui a déclenché la vérification (non utilisé
                   dans la classe de base, mais requis pour la compatibilité
                   avec les sous-classes et mixins).

        Returns :
            (bool) : True si la commande est activée, sinon False.
        """
        return True

    # def bind(self):
    #     """
    #     Lie les raccourcis clavier (accelerators) et les événements de mise à jour de l'UI.
    #     """
    #     # 1. Liaison du Raccourci Clavier
    #     if hasattr(self, 'accelerator') and self.accelerator:
    #         try:
    #             # Convertir l'accélérateur Task Coach/wxPython (ex: "Ctrl+N") en format Tkinter (ex: "<Control-n>")
    #             tk_accelerator = self._convert_accelerator(self.accelerator)
    #
    #             # Récupérer la fenêtre racine (root) de l'application
    #             # root = self._getWindowRoot()
    #             root = self.mainWindow()
    #
    #             if root and tk_accelerator:
    #                 # Lier l'événement à la méthode onCommandActivate
    #                 # bind_all lie l'événement à n'importe quel widget de l'application.
    #                 root.bind_all(tk_accelerator, lambda event: self.onCommandActivate())
    #                 log.debug(f"UICommand.bind() : Raccourci lié : {self.accelerator} -> {tk_accelerator}")
    #
    #         except Exception as e:
    #             log.error(f"Erreur lors de la liaison de l'accélérateur '{self.accelerator}' : {e}")
    #
    #     # # 2. Mise en place de la mise à jour de l'UI (voir section suivante)
    #     # self.update_ui_binding()
    #     # 2. Démarrage de la boucle de Mise à Jour de l'UI
    #     # On appelle une première fois onUpdateUI, qui se rappellera lui-même périodiquement.
    #     self.onUpdateUI()

    def _convert_accelerator(self, accelerator_str):
        """
        Convertit une chaîne d'accélérateur de Task Coach (ex: "Ctrl+N") en format Tkinter (ex: "<Control-n>").
        """
        # Remplace les mots-clés
        mapping = {
            'Ctrl+': 'Control-',
            'Shift+': 'Shift-',
            'Alt+': 'Alt-',
            'Del': 'Delete',
            'Space': 'space'
            # Ajouter d'autres mappings au besoin
        }

        tk_accel = accelerator_str
        for old, new in mapping.items():
            tk_accel = tk_accel.replace(old, new)

        # # Ajoute les chevrons Tkinter et met la dernière lettre en minuscule
        # if tk_accel.startswith(('<', '[')): # Si déjà formaté
        #     return tk_accel
        #
        # parts = tk_accel.split('-')
        # last_part = parts[-1]
        #
        # if len(parts) > 1:
        #     # Reconstruit la chaîne avec la dernière partie en minuscule
        #     tk_accel = "".join(parts[:-1]) + last_part.lower()
        # else:
        #     tk_accel = tk_accel.lower()

        # Met la dernière partie en minuscule (ex: Control-N -> Control-n)
        parts = tk_accel.split('-')
        if parts and parts[-1]:
            parts[-1] = parts[-1].lower()
        tk_accel = "-".join(parts)

        return f"<{tk_accel}>"

    def onUpdateUI(self, event=None) -> None:
        """Met à jour l'état d'activation du widget Tkinter."""
        # Récupère le bouton de la toolbar associé à la commande s'il existe
        button = self._kwargs.get('button')
    
        # # Vérifie si la commande est activée
        # is_enabled = bool(self.enabled(event))
        #
        # # Met à jour l'état du bouton de la toolbar s'il existe
        # if button and isinstance(button, tk.Button):
        #     button.configure(state='normal' if is_enabled else 'disabled')
        #
        # # Met à jour les éléments de menu associés
        # for menu in self.menuItems:
        #     if isinstance(menu, tk.Menu):
        #         for i in range(menu.index('end') + 1):
        #             try:
        #                 if menu.entrycget(i, 'label') == self.getMenuText():
        #                     menu.entryconfigure(i, state='normal' if is_enabled else 'disabled')
        #             except tk.TclError:
        #                 continue
        #
        # # Met à jour l'aide de la toolbar si nécessaire
        # if self.toolbar and (not self.helpText or self.menuText == "?"):
        #     self.updateToolHelp()

        if button:
            try:
                # 2. Vérifie si la commande peut s'exécuter
                # enabled = self.canExecute()
                enabled = bool(self.enabled(event))

                # 3. Met à jour l'état du bouton si nécessaire
                if enabled and button['state'] == tk.DISABLED:
                    button['state'] = tk.NORMAL
                elif not enabled and button['state'] == tk.NORMAL:
                    button['state'] = tk.DISABLED

            except Exception as e:
                # Log l'erreur mais continue la boucle de rafraîchissement
                logging.error(f"Erreur dans onUpdateUI pour {self.uniqueName()}: {e}")

            # 4. Planifie la prochaine vérification (ex: toutes les 250 ms)
            if self.toolbar and self.toolbar.winfo_exists():
                self.toolbar.after(250, self.onUpdateUI)

    def update_ui_binding(self):
        """
        Met en place la boucle de rafraîchissement pour l'état du bouton.
        """
        # Récupère le bouton créé (stocké dans le constructeur appendToToolBar)
        button = self._kwargs.get('button')

        if button:
            # On vérifie si la commande devrait être activée ou désactivée
            enabled = self.canExecute()

            # On met à jour l'état du bouton
            if enabled and button['state'] == tk.DISABLED:
                button['state'] = tk.NORMAL
            elif not enabled and button['state'] == tk.NORMAL:
                button['state'] = tk.DISABLED

            # On planifie la prochaine vérification (par exemple, toutes les 500 ms)
            # On suppose que `self.toolbar` (le parent) est un widget valide
            if self.toolbar:
                # `after` est la méthode Tkinter standard pour les appels différés
                self.toolbar.after(500, self.update_ui_binding)

    def updateMenuText(self, menuText):
        self.menuText = menuText
        # Tkinter ne gère pas la mise à jour automatique des labels de menu.
        # Il faudrait recréer le menu ou trouver l'index de l'élément pour le configurer.
        # Pour simplifier, nous ne gérons pas cette fonctionnalité pour l'instant.
        log.warning("Tkinter updateMenuText is not fully implemented.")

    def updateToolHelp(self):
        """Met à jour l'aide contextuelle de la barre d'outils."""
        if not self.toolbar:
            return  # Not attached to a toolbar or it's hidden
    
        button = self._kwargs.get('button')
        if not button:
            return
        
        # Met à jour l'aide courte (tooltip)
        short_help = self.getMenuText() 
        if hasattr(button, '_short_help') and button._short_help != short_help:
            button._short_help = short_help
            button.bind('<Enter>', lambda e: self._show_tooltip(e, short_help))
            button.bind('<Leave>', lambda e: self._hide_tooltip(e))
        
        # Met à jour l'aide longue
        long_help = self.getHelpText()
        if hasattr(button, '_long_help') and button._long_help != long_help:
            button._long_help = long_help

    def _show_tooltip(self, event, text):
        """Affiche un tooltip avec le texte donné."""
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 25
    
        # Détruit le tooltip existant s'il y en a un
        self._hide_tooltip(event)
    
        # Crée le tooltip
        tooltip = tk.Toplevel(event.widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
    
        label = tk.Label(tooltip, text=text, 
                         justify='left',
                         background="#ffffe0", 
                         relief='solid', borderwidth=1)
        label.pack()
    
        # Stocke la référence au tooltip
        event.widget._tooltip = tooltip
    
    def _hide_tooltip(self, event):
        """Cache le tooltip."""
        widget = event.widget
        if hasattr(widget, "_tooltip"):
            widget._tooltip.destroy()
            del widget._tooltip
            
    def mainWindow(self):
        """
        Retourne l'instance principale de l'application Tkinter.

        Cette méthode utilise le singleton TkinterApplication pour obtenir
        une référence à la fenêtre principale (MainWindow).
        """
        # Cela suppose que l'instance de Tkinter a été créée ailleurs et est accessible
        # via un moyen global ou un singleton.
        # Pour l'instant, on suppose qu'il y a une instance de la classe TkinterApplication
        # quelque part. On pourrait aussi passer l'instance de root en argument.
        # TODO: Assurer l'accès à l'instance de root
        # return None  # tk.Tk()
        from taskcoachlib.application.tkapplication import TkinterApplication
        try:
            app_instance = TkinterApplication.getInstance()
            # app_instance = taskcoachlib.application.tkapplication.TkinterApplication.getInstance()
            # app_instance = app.getInstance()
            if hasattr(app_instance, 'mainwindow'):
                return app_instance.mainwindow
            return None
        except Exception:
            return None

    def getMenuText(self):
        """ Retourne le texte du menu. """
        return self.menuText

    def getHelpText(self):
        """ Retourne le texte d'aide. """
        return self.helpText

    def __getBitmap(self, bitmapName, bitmapSize=(16, 16)):
        """
        Obtient une icône à partir du nom spécifié en utilisant tkartprovider.

        Args :
            bitmapName (str) : Le nom de l'icône.
            bitmapSize (tuple, optionnel) : La taille de l'icône. Par défaut à (16, 16).

        Returns :
            (tk.PhotoImage) : L'icône PhotoImage obtenue, ou None en cas d'erreur.
        """
        log.debug(f"UICommand.__getBitmap() appelé avec self=(self.uniqueName={self.uniqueName()} bitmapName={bitmapName}")
        try:
            # On suppose ici que tkartprovider.py est une version de ArtProvider pour Tkinter
            # qui peut charger des images.
            # return ArtProvider.getPhotoImage(bitmapName)
            # return ArtProviderTk.GetBitmap(bitmapName)
            return artprovidertk.getIcon(bitmapName, bitmapSize)
        except Exception as e:
            # print(f"UICommand.__getBitmap : Error getting bitmap: {e}")
            logging.error(f"UICommand.__getBitmap : Error loading bitmap '{bitmapName}': {str(e)}")
            # raise FileNotFoundError(f"Bitmap '{bitmapName}' not found")
            return None

