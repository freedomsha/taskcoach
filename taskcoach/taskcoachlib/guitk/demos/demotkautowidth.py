
# Pour la compatibilité avec le code existant qui pourrait importer TaskList d'ici
# (Bien que TaskList soit plutôt définie dans itemctrltk.py ou domain)
# Nous fournissons une classe factice ou de base si nécessaire.
# Elle est très utile pour les tests
# 👉 Mais elle ne doit jamais être utilisée en production

# NE FONCTIONNE PAS sans TaskList !

import logging
import tkinter as tk
# import tkinter.font as tkfont
from tkinter import ttk

from taskcoachlib.widgetstk.autowidthtk import AutoColumnWidthMixin
from taskcoachlib.widgetstk.itemctrltk import TaskTree as TaskList

log = logging.getLogger(__name__)


class AutoWidthTreeList(AutoColumnWidthMixin, ttk.Treeview):
    """
    Une classe combinée prête à l'emploi pour les tests.
    """
    def __init__(self, master, **kwargs):
        # Initialiser Treeview d'abord pour avoir accès à self.bind
        ttk.Treeview.__init__(self, master, **kwargs)
        # Initialiser le mixin ensuite
        AutoColumnWidthMixin.__init__(self)


if __name__ == '__main__':
    # from taskcoachlib.domain.task.tasklist import TaskList
    root = tk.Tk()
    root.title("TaskCoach avec Tkinter")
    root.geometry("600x400")

    # task_list = TaskList(root, show='headings')  # show rentre en conflit avec la valeur déjà définie
    task_list = TaskList(root)
    task_list.pack(fill=tk.BOTH, expand=True)  # TaskList n'est pas encore un widget ! pour être packé !

    root.mainloop()
