# La migration d'un composant aussi complexe que smartdatetimectrl.py est une étape ambitieuse et très formatrice. Je suis là pour t'accompagner à chaque étape.
#
# Le fichier smartdatetimectrl.py est très bien écrit, mais il est profondément lié à wxPython. Il utilise des concepts comme le "Device Context" (dc) pour dessiner manuellement les composants, un système d'événements personnalisé, et des fenêtres popup spécifiques à wxPython. Une traduction ligne par ligne est donc impossible.
#
# Notre stratégie sera de recréer la fonctionnalité en utilisant les outils et la philosophie de Tkinter. Nous allons le faire pas à pas, en construisant une version claire, moderne et facile à maintenir.
#
# Plan de Développement
#
# Voici comment nous allons procéder pour transformer ce composant wxPython en un widget Tkinter :
#
#     Créer le Conteneur Principal (SmartDateTimeCtrl) : Ce sera un tkinter.Frame qui contiendra nos widgets de date et d'heure.
#
#     Construire les Champs de Saisie (Field) : Au lieu de dessiner le texte, nous utiliserons des widgets Tkinter. Le ttk.Spinbox est parfait pour les champs numériques (jour, mois, année, heure), car il gère la saisie numérique et les clics sur les flèches haut/bas. Pour les séparateurs (comme : ou /), nous utiliserons des ttk.Label.
#
#     Assembler les Entrées de Date et d'Heure (DateEntry, TimeEntry) : Nous créerons des classes qui assembleront les Spinbox et les Label dans le bon ordre, en se basant sur un format (par exemple, "jour/mois/année").
#
#     Gérer la Logique et les Événements : Nous connecterons la logique de validation (par exemple, un mois ne peut pas être supérieur à 12) et la navigation au clavier (passer d'un champ à l'autre avec les flèches).
#
#     Créer le Calendrier Popup (_CalendarPopup) : Ce sera la partie la plus complexe. Nous créerons une fenêtre tkinter.Toplevel qui s'affichera sous le champ de la date et contiendra des boutons pour chaque jour.
#
# Prêt à commencer ? Allons-y avec une première version qui couvre les étapes 1, 2 et 3.
#
# Étape 1 : Le Widget de Base en Tkinter
#
# Voici un premier code complet et fonctionnel. Il recrée le SmartDateTimeCtrl avec les champs de date et d'heure en utilisant des ttk.Spinbox. Il ne contient pas encore le calendrier popup, mais c'est une base solide et fonctionnelle que nous améliorerons ensemble.
#
# Analyse bien ce code, copie-le dans un fichier (par exemple, tkinter_datetime_ctrl.py) et exécute-le. Tu verras une fenêtre avec notre nouveau widget !

# Explication du Code
#
#     Classes de Widgets :
#
#         DateEntry, TimeEntry, et SmartDateTimeCtrl sont des classes qui héritent de ttk.Frame. C'est la manière standard de créer des widgets composés en Tkinter.
#
#         Le ttk est utilisé préférentiellement à tk car il offre des widgets plus modernes et mieux intégrés à l'apparence du système d'exploitation.
#
#     Variables de Contrôle (tk.IntVar) :
#
#         Au lieu de lire directement la valeur d'un widget, nous utilisons des tk.IntVar. Ces variables sont liées aux Spinbox via l'option textvariable.
#
#         L'avantage est double :
#
#             On peut obtenir ou définir la valeur du widget en manipulant la variable.
#
#             On peut "tracer" la variable (trace_add) pour déclencher une fonction (comme _validate_date) chaque fois que sa valeur est modifiée.
#
#     Validation de la Date (_validate_date) :
#
#         C'est la partie la plus "intelligente" de DateEntry. Elle utilise le module calendar de Python pour connaître le nombre de jours dans le mois/année sélectionné.
#
#         Elle met ensuite à jour la limite (to=...) du Spinbox du jour pour empêcher la sélection d'une date invalide (par exemple, le 31 février).
#
#     Événements Personnalisés (event_generate) :
#
#         Pour qu'un widget parent sache quand une valeur a changé dans un de ses enfants, nous utilisons des événements virtuels.
#
#         self.event_generate("<<DateChanged>>") crée un signal que le SmartDateTimeCtrl peut intercepter avec bind("<<DateChanged>>", ...). C'est une manière propre de faire communiquer les widgets entre eux.
#
#     Fenêtre de Démonstration (if __name__ == "__main__":) :
#
#         Cette partie ne s'exécute que si tu lances le fichier directement. Elle crée une petite fenêtre pour te montrer comment utiliser SmartDateTimeCtrl, comment lui donner une valeur initiale (set) et comment réagir à ses changements (bind).
#
# Prochaines Étapes
#
# Cette première version est déjà très puissante.
# Maintenant, je te propose de l'explorer.
# Regarde comment elle se comporte, essaie de changer les valeurs,
# et dis-moi ce que tu en penses.
#
# Une fois que cette base te convient, nous pourrons passer à l'étape suivante, qui est un défi intéressant : la création du calendrier popup.

#
# Excellente idée ! C'est une approche beaucoup plus moderne et intuitive pour l'utilisateur. Remplacer les trois Spinbox par un champ de saisie unique rend le composant plus compact et plus proche de ce qu'on a l'habitude de voir dans les applications web.
#
# Pour y arriver, nous allons modifier notre widget DateEntry :
#
#     Remplacer ttk.Spinbox par ttk.Entry : Nous utiliserons un champ de saisie de texte standard.
#
#     Mettre en place la validation : C'est le point crucial. Le widget doit être "intelligent". Il doit comprendre la chaîne de caractères que l'utilisateur tape (par exemple, "12/10/2025") et la valider.
#
#     Fournir un retour visuel : Si l'utilisateur saisit une date invalide (comme "99/10/2025"), le champ changera de couleur pour signaler l'erreur.
#
#     Ajouter un bouton pour le calendrier : À côté du champ de saisie, nous ajouterons un bouton. Pour l'instant, il sera inactif, mais c'est lui qui, à l'avenir, ouvrira notre calendrier popup.
import tkinter as tk
from tkinter import ttk
import datetime
import calendar

# Pour s'assurer que les widgets ttk ont un joli look
from tkinter.font import Font

class DateEntry(ttk.Frame):
    """
    Un widget pour saisir une date (jour, mois, année).
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # --- Variables pour stocker les valeurs ---
        # On utilise les variables de contrôle de Tkinter pour lier
        # facilement les valeurs aux widgets.
        self.year_var = tk.IntVar(value=datetime.date.today().year)
        self.month_var = tk.IntVar(value=datetime.date.today().month)
        self.day_var = tk.IntVar(value=datetime.date.today().day)

        # --- Création des Widgets (Spinbox) ---
        # Le Spinbox est idéal car il limite la saisie aux chiffres
        # et permet d'incrémenter/décrémenter avec les flèches.

        # Champ pour le jour
        self.day_spinbox = ttk.Spinbox(
            self,
            from_=1,
            to=31,
            width=3,
            textvariable=self.day_var,
            command=self._on_change
        )
        self.day_spinbox.pack(side='left', padx=(0, 2))

        ttk.Label(self, text="/").pack(side='left', padx=(0, 2))

        # Champ pour le mois
        self.month_spinbox = ttk.Spinbox(
            self,
            from_=1,
            to=12,
            width=3,
            textvariable=self.month_var,
            command=self._on_change
        )
        self.month_spinbox.pack(side='left', padx=(0, 2))

        ttk.Label(self, text="/").pack(side='left', padx=(0, 2))

        # Champ pour l'année
        self.year_spinbox = ttk.Spinbox(
            self,
            from_=1900,
            to=2100,
            width=5,
            textvariable=self.year_var,
            command=self._on_change
        )
        self.year_spinbox.pack(side='left')

        # --- Lier les événements ---
        # Quand une variable change, on valide la date
        self.month_var.trace_add("write", self._validate_date)
        self.year_var.trace_add("write", self._validate_date)

    def _validate_date(self, *args):
        """Ajuste le nombre maximum de jours en fonction du mois et de l'année."""
        try:
            year = self.year_var.get()
            month = self.month_var.get()
            # calendar.monthrange donne le nombre de jours dans un mois
            _, max_days = calendar.monthrange(year, month)
            # On met à jour la limite du spinbox des jours
            self.day_spinbox.config(to=max_days)

            # Si le jour actuel est supérieur au maximum, on l'ajuste
            if self.day_var.get() > max_days:
                self.day_var.set(max_days)

        except (tk.TclError, ValueError):
            # Arrive si le champ est vide ou invalide pendant la saisie
            pass

    def get(self):
        """Retourne la date sous forme d'objet datetime.date."""
        try:
            return datetime.date(
                self.year_var.get(), self.month_var.get(), self.day_var.get()
            )
        except (tk.TclError, ValueError):
            return None # Retourne None si la date est invalide

    def set(self, date_obj):
        """Définit la date à partir d'un objet datetime.date."""
        if isinstance(date_obj, datetime.date):
            self.year_var.set(date_obj.year)
            self.month_var.set(date_obj.month)
            self.day_var.set(date_obj.day)
            self._validate_date()

    def _on_change(self):
        """Génère un événement virtuel lorsque la valeur change."""
        self.event_generate("<<DateChanged>>")

class TimeEntry(ttk.Frame):
    """
    Un widget pour saisir une heure (heure, minute, seconde).
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # --- Variables pour stocker les valeurs ---
        now = datetime.datetime.now().time()
        self.hour_var = tk.IntVar(value=now.hour)
        self.minute_var = tk.IntVar(value=now.minute)
        self.second_var = tk.IntVar(value=now.second)

        # --- Création des Widgets ---
        self.hour_spinbox = ttk.Spinbox(
            self, from_=0, to=23, width=3, textvariable=self.hour_var, command=self._on_change
        )
        self.hour_spinbox.pack(side='left', padx=(0, 2))

        ttk.Label(self, text=":").pack(side='left', padx=(0, 2))

        self.minute_spinbox = ttk.Spinbox(
            self, from_=0, to=59, width=3, textvariable=self.minute_var, command=self._on_change
        )
        self.minute_spinbox.pack(side='left', padx=(0, 2))

        ttk.Label(self, text=":").pack(side='left', padx=(0, 2))

        self.second_spinbox = ttk.Spinbox(
            self, from_=0, to=59, width=3, textvariable=self.second_var, command=self._on_change
        )
        self.second_spinbox.pack(side='left')

    def get(self):
        """Retourne l'heure sous forme d'objet datetime.time."""
        try:
            return datetime.time(
                self.hour_var.get(), self.minute_var.get(), self.second_var.get()
            )
        except (tk.TclError, ValueError):
            return None

    def set(self, time_obj):
        """Définit l'heure à partir d'un objet datetime.time."""
        if isinstance(time_obj, datetime.time):
            self.hour_var.set(time_obj.hour)
            self.minute_var.set(time_obj.minute)
            self.second_var.set(time_obj.second)

    def _on_change(self):
        """Génère un événement virtuel lorsque la valeur change."""
        self.event_generate("<<TimeChanged>>")

class SmartDateTimeCtrl(ttk.Frame):
    """
    Le widget principal qui combine la saisie de la date et de l'heure.
    """
    def __init__(self, parent, label=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        if label:
            ttk.Label(self, text=label).pack(side='left', padx=(0, 5))

        self.date_entry = DateEntry(self)
        self.date_entry.pack(side='left', padx=(0, 5))

        self.time_entry = TimeEntry(self)
        self.time_entry.pack(side='left')

        # Lier les événements des sous-widgets à un événement global
        self.date_entry.bind("<<DateChanged>>", self._on_change)
        self.time_entry.bind("<<TimeChanged>>", self._on_change)

    def get(self):
        """Retourne la date et l'heure combinées en objet datetime.datetime."""
        date = self.date_entry.get()
        time = self.time_entry.get()
        if date and time:
            return datetime.datetime.combine(date, time)
        return None

    def set(self, datetime_obj):
        """Définit la date et l'heure à partir d'un objet datetime.datetime."""
        if isinstance(datetime_obj, datetime.datetime):
            self.date_entry.set(datetime_obj.date())
            self.time_entry.set(datetime_obj.time())

    def _on_change(self, event=None):
        """Génère un événement virtuel pour le widget principal."""
        self.event_generate("<<DateTimeChanged>>")

# --- Fenêtre de démonstration ---
if __name__ == "__main__":

    def on_datetime_change(event):
        """Fonction appelée lorsque la date ou l'heure change."""
        dt = pnl1.get()
        if dt:
            print(f"Nouvelle date/heure : {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            # Mettre à jour l'étiquette avec la nouvelle valeur
            result_label.config(text=f"Valeur sélectionnée : {dt.strftime('%c')}")

    root = tk.Tk()
    root.title("Test du SmartDateTimeCtrl en Tkinter")

    # Style pour une apparence plus moderne
    style = ttk.Style(root)
    # Tente d'utiliser un thème plus esthétique s'il est disponible
    # ('clam', 'alt', 'default' sur Windows, 'aqua' sur macOS)
    if 'clam' in style.theme_names():
        style.theme_use('clam')

    # Augmenter la taille de la police pour une meilleure lisibilité
    default_font = Font(font=ttk.Style().lookup("TSpinbox", "font"))
    default_font.config(size=11)
    style.configure("TSpinbox", font=default_font)
    style.configure("TLabel", font=default_font)

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill='both', expand=True)

    # --- Création de notre widget ---
    pnl1 = SmartDateTimeCtrl(main_frame, label="Début :")
    pnl1.pack(pady=(0, 10), anchor='w')

    # Initialiser avec une date spécifique
    initial_datetime = datetime.datetime(2025, 10, 26, 10, 30, 0)
    pnl1.set(initial_datetime)

    # Lier l'événement personnalisé
    pnl1.bind("<<DateTimeChanged>>", on_datetime_change)

    # Une étiquette pour afficher le résultat
    result_label = ttk.Label(main_frame, text="Valeur sélectionnée : ...")
    result_label.pack(pady=10, anchor='w')

    # Mettre à jour l'étiquette au démarrage
    on_datetime_change(None)

    root.mainloop()