# Malheureusement, je ne peux pas convertir directement le fichier tooltip.py de wxPython à Tkinter.
# C'est une tâche complexe qui demande une connaissance approfondie des deux frameworks, et une simple conversion ligne par ligne n'est pas possible en raison de leurs architectures et de leurs systèmes de gestion d'événements fondamentalement différents.
#
# Voici pourquoi une conversion directe est impraticable, ainsi qu'une approche pour accomplir ce que tu souhaites, en te guidant vers les modules Tkinter appropriés.
#
# Pourquoi la Conversion Directe est Impossible ❌
#
# Le fichier tooltip.py dépend de manière intensive des classes et des fonctionnalités spécifiques à wxPython, notamment :
#
#     wx.Timer: Un objet de minuterie propre à wxPython.
#
#     wx.EVT_MOTION, wx.EVT_LEAVE_WINDOW, wx.EVT_TIMER: Des constantes d'événement spécifiques pour lier des gestionnaires.
#
#     wx.MiniFrame, wx.Frame, wx.PopupWindow: Des classes de fenêtres qui gèrent les info-bulles différemment selon le système d'exploitation.
#
#     wx.ClientDC, wx.PaintDC: Des contextes de dessin utilisés pour rendre graphiquement le contenu de l'info-bulle (texte, icônes, bordures).
#
#     wx.ArtProvider: Une classe pour obtenir des icônes de manière indépendante du système d'exploitation.
#
# Ces fonctionnalités n'ont pas d'équivalent direct dans Tkinter.
# Tkinter utilise un modèle de gestion d'événements et de rendu graphique différent.
# Par exemple, pour les événements de la souris,
# il utilise des chaînes comme <Motion>, <Leave>, ou <Button-1>,
# et le rendu graphique se fait sur un Canvas
# en utilisant des méthodes comme create_text ou create_image.
#
# L'Approche Recommandée pour Tkinter ✅
#
# Pour implémenter des info-bulles dans Tkinter,
# il est nécessaire de réécrire la logique
# en utilisant les classes et les méthodes de ce framework.
# La bonne nouvelle, c'est que les modules standards de Tkinter suffisent,
# sans avoir besoin de modules externes comme dnd (qui gère le glisser-déposer).
#
# Pour créer des info-bulles dynamiques et personnalisables comme celles décrites dans ton fichier,
# tu devrais utiliser une combinaison des modules suivants :
#
#     tkinter: Pour la classe principale de la fenêtre d'info-bulle (Toplevel) et les événements.
#
#     tkinter.ttk: Pour les styles et les widgets si tu souhaites une apparence plus moderne.
#
#     tkinter.font: Pour gérer les polices de caractères.
#
#     PIL (Pillow): C'est un module externe très courant pour gérer les images et les icônes, car Tkinter ne supporte nativement que les formats GIF et PGM/PPM. Tu devras l'installer via pip (pip install Pillow).
#
# Structure d'une Info-Bulle Tkinter
#
# Une implémentation classique de l'info-bulle en Tkinter se base sur :
#
#     Une classe ToolTip (ou similaire) héritant de tkinter.Toplevel:
#     Cette fenêtre sans bordure sera l'info-bulle elle-même.
#
#     La gestion des événements de la souris: Utiliser .bind()
#     pour lier les événements <Enter> (quand la souris entre dans un widget)
#     et <Leave> (quand elle en sort).
#
#     Une minuterie pour le délai : Utiliser la méthode .after() de Tkinter
#     pour déclencher l'affichage de l'info-bulle après un court délai,
#     évitant ainsi qu'elle ne s'affiche instantanément.
#
#     L'affichage et le positionnement : Calculer la position de la fenêtre d'info-bulle
#     (.geometry()) par rapport à la souris ou au widget,
#     puis utiliser .overrideredirect(True) pour masquer les bordures de la fenêtre
#     et la faire ressembler à une info-bulle.
#
# Si tu souhaites que je t'aide à réécrire la logique pour Tkinter,
# je peux te fournir un squelette de code pour commencer.
# Nous pourrions partir de l'idée d'une classe ToolTip et de la manière de la lier à un widget.

# La conversion directe du code wxPython vers Tkinter
# n'est pas possible en raison des différences fondamentales entre ces deux bibliothèques.
# Comme mentionné précédemment, il faut réécrire la logique en utilisant les classes et les méthodes de Tkinter.
#
# Voici une implémentation simplifiée et fonctionnelle d'un système d'info-bulles pour Tkinter,
# inspirée par la logique du fichier tooltip.py de TaskCoach.
# J'ai créé un module nommé tooltip.py pour un dossier widgetstk que tu pourrais utiliser.
# Ce code gère l'affichage, le masquage et le positionnement des info-bulles.
# Il utilise tkinter.Toplevel pour la fenêtre de l'info-bulle
# et gère les événements de la souris (<Enter>, <Leave>)
# ainsi que la temporisation avec .after().
#
# J'ai également inclus un exemple d'utilisation pour te montrer comment
# intégrer cette nouvelle classe ToolTip avec un widget Tkinter comme un Button.

# Ce code offre une base solide pour implémenter des info-bulles dans ton projet Tkinter.
# Il est beaucoup plus simple que la version wxPython car
# il n'a pas besoin de gérer les contextes de dessin
# et les variations de systèmes d'exploitation de la même manière.
# N'hésite pas si tu as d'autres questions !

# Fichier : widgetstk/tooltip.py

import tkinter as tk
from tkinter import Toplevel, Label
import textwrap


class ToolTip:
    """
    Crée une info-bulle pour un widget Tkinter.

    Cette classe gère l'affichage et le masquage d'une petite fenêtre d'info-bulle
    qui apparaît lorsque la souris reste sur un widget pendant un court instant.
    """

    def __init__(self, widget, text="ToolTip", delay=500, **kwargs):
        # def __init__(self, widget, delay=500):
        """
        Initialise l'info-bulle.

        Args:
            widget (tk.Widget): Le widget sur lequel l'info-bulle doit apparaître.
            text (str): Le texte à afficher dans l'info-bulle.
            delay (int): Le délai en millisecondes avant d'afficher l'info-bulle.
        """
        self.widget = widget
        self.text = text  # = None
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        self.__enabled = kwargs.pop("tooltipsEnabled", True)
        self._set_bindings()

    def SetToolTipsEnabled(self, enabled):
        """
        Activer ou désactiver les info-bulles pour ce contrôle.

        Args :
            enabled (bool) : `True` pour activer les info-bulles, `False` pour les désactiver.
        """
        self.__enabled = enabled

    def on_enter(self, event):
        """
        Gère l'événement d'entrée de la souris.
        """
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event):
        """
        Gère l'événement de sortie de la souris.
        """
        if self.after_id:
            self.widget.after_cancel(self.after_id)
        self.hide_tooltip()

    def _set_bindings(self):
        """
        Configure les gestionnaires d'événements pour le widget.
        """
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)

    def show_tooltip(self):
        """
        Affiche la fenêtre de l'info-bulle.
        """
        if self.tooltip_window or not self.text:
            return

        # Crée la fenêtre de l'info-bulle
        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Masque la barre de titre et les bordures
        self.tooltip_window.wm_attributes("-topmost", True)  # Rends la fenêtre toujours visible au-dessus

        # Crée une étiquette pour le texte
        label = Label(self.tooltip_window,
                      text=self.text,
                      background="#ffffe0",  # Couleur de fond jaune pâle typique des info-bulles
                      relief="solid",
                      borderwidth=1,
                      justify="left",
                      font=("Arial", 10))
        label.pack(padx=2, pady=2)

        # Calcule et définit la position de la fenêtre
        x = self.widget.winfo_rootx() + self.widget.winfo_width()
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self):
        """
        Masque la fenêtre de l'info-bulle.
        """
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple d'info-bulle Tkinter")

    # Crée un bouton avec une info-bulle simple
    button1 = tk.Button(root, text="Passez la souris ici")
    button1.pack(pady=20, padx=20)
    tooltip1 = ToolTip(button1, "Ceci est une info-bulle pour le bouton 1.")

    # Crée un autre bouton avec une info-bulle plus longue
    long_text = "Ceci est une info-bulle plus longue qui devrait s'ajuster si elle est trop large."
    button2 = tk.Button(root, text="Un autre bouton")
    button2.pack(pady=20, padx=20)
    tooltip2 = ToolTip(button2, textwrap.fill(long_text, width=40))

    root.mainloop()
