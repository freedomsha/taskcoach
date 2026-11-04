#---------------------------------------------------------------------------
# Nom :        tkexpando.py
# Objet :      Un champ de texte multiligne qui s'agrandit et se réduit
#              automatiquement selon la quantité de texte à afficher.
#
# Auteur :     Robin Dunn (version wxPython originale)
# Adaptation : version tkinter
# Création :   18-sept-2006 (wxPython)-03-nov-2026 (tkinter)
# Copyright :  (c) 2006-2020 by Total Control Software
# Licence :    wxWindows license
#---------------------------------------------------------------------------

"""
Ce module contient :class:`ExpandoTextCtrl`, un champ de texte multiligne
dont la hauteur s'ajuste automatiquement pour afficher l'intégralité de
son contenu.


Description
===========

:class:`ExpandoTextCtrl` est un widget :class:`tk.Text` dont la hauteur
(en nombre de lignes affichées) est recalculée à chaque modification du
texte ou à chaque redimensionnement. La largeur est supposée fixe : seule
la hauteur est ajustée automatiquement.

Lorsque la hauteur change, le widget génère l'événement virtuel
``EVT_ETC_LAYOUT_NEEDED`` (``<<ExpandoLayoutNeeded>>``). Le conteneur peut
s'y abonner pour effectuer les ajustements de mise en page supplémentaires
qui seraient nécessaires.


Utilisation
===========

Exemple d'utilisation::

    import tkinter as tk
    from expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED

    root = tk.Tk()
    zone = ExpandoTextCtrl(root, value="Ce texte va s'agrandir", width=40)
    zone.pack(padx=10, pady=10)
    zone.bind(EVT_ETC_LAYOUT_NEEDED, lambda evt: root.update_idletasks())
    root.mainloop()

"""
# Principales différences avec la version wxPython :

# Calcul des lignes : la méthode GetNumberOfLines personnalisée pour GTK et macOS n’est plus nécessaire. Tk compte directement les lignes affichées avec l’option "displaylines" de count(), qui tient compte du retour à la ligne.
# Hauteur : tk.Text exprime sa hauteur en lignes, donc les calculs de hauteur en pixels (charHeight, _leading, extraHeight) disparaissent.
# Changement de police : Tk recalcule automatiquement la hauteur, la surcharge SetFont n’est donc plus nécessaire.
# Événements : wx.lib.newevent est remplacé par un événement virtuel Tk <<ExpandoLayoutNeeded>>, émis avec event_generate.
# Détection des modifications : l’événement <<Modified>> remplace wx.EVT_TEXT. L’indicateur doit être réinitialisé avec edit_modified(False), sinon l’événement ne se déclenche plus.
# Ajustement initial : wx.CallAfter est remplacé par after_idle.
# Mise en page : le wx.Sizer disparaît. Avec pack ou grid, la modification de la hauteur est prise en compte par le gestionnaire de géométrie. L’événement permet de mettre à jour la fenêtre si nécessaire, par exemple avec root.update_idletasks().
# Noms : les méthodes suivent la convention PEP 8 (set_max_lines, write_text, etc.) au lieu de SetMaxHeight, WriteText, etc. Le paramètre max_lines remplace la hauteur maximale en pixels, ce qui est plus naturel avec tkinter.

import tkinter as tk


# Nom de l'événement virtuel émis lorsque la hauteur du contrôle change.
# Pour s'y abonner : widget.bind(EVT_ETC_LAYOUT_NEEDED, gestionnaire)
EVT_ETC_LAYOUT_NEEDED = "<<ExpandoLayoutNeeded>>"


#---------------------------------------------------------------------------

class ExpandoTextCtrl(tk.Text):
    """
    Champ de texte multiligne (:class:`tk.Text`) dont la hauteur s'adapte
    dynamiquement au nombre de lignes affichées.

    La largeur doit être fixée par l'appelant (paramètre ``width``) ; seule
    la hauteur varie. Si une hauteur maximale est définie, le champ cesse de
    grandir une fois cette limite atteinte et le contenu défile à l'intérieur.

    Lorsque la hauteur change, l'événement :data:`EVT_ETC_LAYOUT_NEEDED`
    est émis afin que le conteneur puisse effectuer les ajustements de mise
    en page nécessaires.
    """

    def __init__(self, parent, value="", max_lines=None, width=40, **kwargs):
        """
        Constructeur de la classe.

        :param parent: fenêtre parente, ne doit pas être ``None``.
        :param str value: texte initial du champ.
        :param int max_lines: nombre maximal de lignes affichées avant
         l'apparition du défilement. ``None`` signifie qu'il n'y a pas de limite.
        :param int width: largeur du champ, en nombre de caractères moyens.
        :param kwargs: options supplémentaires transmises à :class:`tk.Text`.
        """
        kwargs.setdefault("wrap", tk.WORD)
        kwargs.setdefault("height", 1)
        super().__init__(parent, width=width, **kwargs)

        self._max_lines = max_lines
        self._num_lines = -1  # force un premier ajustement

        if value:
            self.insert("1.0", value)
        # Réinitialise l'indicateur de modification créé par l'insertion initiale
        self.edit_modified(False)

        self.bind("<<Modified>>", self._on_modified)
        self.bind("<Configure>", self._on_configure)

        # Ajustement initial une fois la fenêtre prête à être dessinée
        self.after_idle(self._adjust_ctrl)

    def set_max_lines(self, n):
        """
        Définit le nombre maximal de lignes affichées avant défilement, et
        réduit immédiatement le champ si sa hauteur actuelle le dépasse.

        :param int n: nombre maximal de lignes, ou ``None`` pour aucune limite.
        """
        self._max_lines = n
        self._num_lines = -1
        self._adjust_ctrl()

    def get_max_lines(self):
        """
        Renvoie le nombre maximal de lignes affichées avant défilement.

        :rtype: int | None
        """
        return self._max_lines

    def write_text(self, texte):
        """
        Insère le texte à la position actuelle du curseur.

        :param str texte: texte à insérer.
        """
        self.insert(tk.INSERT, texte)

    def append_text(self, texte):
        """
        Ajoute le texte à la fin du champ et place le curseur à la fin.

        :param str texte: texte à ajouter.

        .. seealso:: :meth:`write_text`
        """
        self.insert(tk.END, texte)
        self.mark_set(tk.INSERT, tk.END)
        self.see(tk.END)

    def get_number_of_lines(self):
        """
        Renvoie le nombre de lignes d'affichage occupées par le contenu,
        en tenant compte du retour automatique à la ligne.

        :rtype: int
        """
        # Tk calcule lui-même les lignes affichées (mots enveloppés compris).
        # "end-1c" exclut le saut de ligne final ajouté automatiquement par Tk.
        resultat = self.count("1.0", "end-1c", "displaylines")
        if isinstance(resultat, (tuple, list)):
            resultat = resultat[0] if resultat else 0
        return max(1, resultat or 0)

    def _on_modified(self, event=None):
        """
        Gestionnaire de l'événement ``<<Modified>>`` : recalcule la hauteur
        à chaque modification du texte.

        :param event: événement tkinter (non utilisé).
        """
        if self.edit_modified():
            self.edit_modified(False)
            self._adjust_ctrl()

    def _on_configure(self, event=None):
        """
        Gestionnaire de l'événement ``<Configure>`` : une modification de la
        largeur peut changer le nombre de lignes après retour à la ligne.

        :param event: événement tkinter (non utilisé).
        """
        self._adjust_ctrl()

    def _adjust_ctrl(self):
        """
        Recalcule le nombre de lignes et ajuste la hauteur du champ si
        nécessaire, puis émet :data:`EVT_ETC_LAYOUT_NEEDED`.
        """
        numLines = self.get_number_of_lines()
        if numLines == self._num_lines:
            return
        self._num_lines = numLines

        hauteur = numLines
        if self._max_lines is not None:
            hauteur = min(hauteur, self._max_lines)
        hauteur = max(1, hauteur)

        if int(self.cget("height")) != hauteur:
            # La hauteur de tk.Text est exprimée en lignes : aucun calcul
            # de pixels n'est nécessaire, contrairement à wxPython.
            self.configure(height=hauteur)
            self.event_generate(EVT_ETC_LAYOUT_NEEDED, when="tail")


#---------------------------------------------------------------------------

def _demo():
    """
    Petite application de démonstration de :class:`ExpandoTextCtrl`.
    """
    root = tk.Tk()
    root.title("Test ExpandoTextCtrl")

    cadre = tk.Frame(root, padx=10, pady=10)
    cadre.pack(fill=tk.BOTH, expand=True)

    zone = ExpandoTextCtrl(cadre, value="Ce champ va s'agrandir pendant la saisie.",
                           width=35, max_lines=10)
    zone.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def ecrire():
        zone.write_text("Ceci est un test... Seulement un test. Si c'était une "
                        "vraie urgence, vous auriez vu le renard brun rapide "
                        "sauter par-dessus le chien paresseux. ")

    def ajouter():
        zone.append_text("Texte ajouté. ")

    tk.Button(cadre, text="Écrire le texte", command=ecrire).grid(
        row=0, column=1, sticky="ew", padx=5, pady=5)
    tk.Button(cadre, text="Ajouter du texte", command=ajouter).grid(
        row=1, column=1, sticky="ew", padx=5, pady=5)

    zone.bind(EVT_ETC_LAYOUT_NEEDED, lambda evt: root.update_idletasks())

    root.mainloop()


if __name__ == "__main__":
    _demo()
