# -*- coding: utf-8 -*-
"""Demonstrateur visuel des modules AUI convertis en Tkinter.

Cette petite application permet de tester a la main, dans une fenetre
reelle, les fonctions converties : panneaux amares (gauche/droite/bas/
centre), panneau flottant, barre d'outils, carnet a onglets, MDI, et
glisser-deposer de le titre d'un panneau vers une zone d'amarrage.

Lancement depuis la racine du depot Task Coach :

    python -m taskcoachlib.guitk.demotkaui

ou, sans serveur X physique (integration continue) :

    xvfb-run -a python -m taskcoachlib.guitk.demotkaui --auto 5

Le mode --auto ouvre la fenetre, simule un glisser-deposer de panneau,
verifie le resultat, puis ferme l'application (code de retour 0 si tout
s'est bien passe, 1 sinon). Sans --auto, la fenetre reste ouverte et
s'auto-detruit apres le nombre de secondes donne (30 par defaut).
"""

import sys
import time

import tkinter as tk
from tkinter import ttk

# from taskcoachlib.guitk import aui_tk_constants as cst
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk import aui_tk_constants as cst
# from taskcoachlib.guitk import tkframemanager as fm
# from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkframemanager as fm
# from taskcoachlib.guitk.tkframemanager import AuiManager, AuiPaneInfo
# from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkframemanager as fm
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.tkframemanager_elements import AuiPaneInfo
from taskcoachlib.thirdparty.tk3rdparty.aui_ttk.ttkframemanager_auimanager import AuiManager


class DemoTkAui:
    """Fenêtre de démonstration des panneaux AUI Tkinter."""

    def __init__(self, auto=False, duree=60):
        self.auto = auto
        self.duree = duree
        self.journal = []
        self._flottant = False
        self.zone_canvas = None
        self.zones = {}
        self._point_courant = (0, 0)

        self.root = tk.Tk()
        self.root.title('Demo AUI Tkinter - Task Coach')
        self.root.geometry('1000x680+40+40')

        # barre de menus simple
        barre = tk.Menu(self.root)
        menu_fichier = tk.Menu(barre, tearoff=0)
        menu_fichier.add_command(label='Quitter', command=self.root.destroy)
        barre.add_cascade(label='Fichier', menu=menu_fichier)
        self.root.config(menu=barre)

        # gestionnaire AUI
        self.mgr = AuiManager(self.root)

        # barre d'outils (via le module converti)
        try:
            from taskcoachlib.guitk import tkauitoolbar
            self.toolbar = tkauitoolbar.AuiToolBar(self.root)
            self.toolbar.pack(side='top', fill='x')
            self.toolbar.AddSimpleTool(101, 'Nouveau', None, 'Creer une tache')
            self.toolbar.AddSimpleTool(102, 'Ouvrir', None, 'Ouvrir un fichier')
            self.toolbar.AddToggleTool(103, None)
            self.toolbar.AddSeparator()
            self.toolbar.Realize()
        except Exception as exc:
            self._log('barre d\'outils indisponible : %s' % exc)

        # panneaux amares
        self.panneau_gauche = self._panneau('#ffdddd', 'Arbre des taches',
                                            'Panneau gauche\n(double-cliquez sa legende\npour la flotter)')
        self.panneau_droite = self._panneau('#ddffdd', 'Details',
                                            'Panneau droit')
        self.panneau_bas = self._panneau('#ddddee', 'Apercu',
                                         'Panneau bas')
        self.panneau_centre = self._panneau('#ffffdd', 'Editeur',
                                             'Panneau central\n(pilier CenterPane)')

        self.pa = self.mgr.AddPane(
            self.panneau_gauche,
            AuiPaneInfo().Caption('Arbre').Left().CaptionVisible(False)
                         .DefaultPane().MinSize(160, 200))
        self.pb = self.mgr.AddPane(
            self.panneau_droite,
            AuiPaneInfo().Caption('Details').Right().CaptionVisible(False)
                         .DefaultPane().MinSize(160, 200))
        self.pc = self.mgr.AddPane(
            self.panneau_bas,
            AuiPaneInfo().Caption('Apercu').Bottom().CaptionVisible(False)
                         .DefaultPane().MinSize(100, 120))
        self.pd = self.mgr.AddPane(
            self.panneau_centre,
            AuiPaneInfo().Caption('Editeur').CenterPane())

        # carnet AuiNotebook dans le panneau central
        self.notebook = self._carnet()

        # zone de journal
        self.zone_journal = tk.Text(self.root, height=6, bg='#222222',
                                    fg='#88ff88', insertbackground='#88ff88')
        self.mgr.AddPane(self.zone_journal,
                         AuiPaneInfo().Caption('Journal').Bottom()
                                      .CaptionVisible(False)
                                      .DefaultPane().MinSize(100, 90))

        # glisser-deposer : legende du panneau gauche -> zones d'amarrage
        self._preparer_drag_drop()

        self.mgr.Update()
        self.root.update_idletasks()

        self._log('Fenetre prete : %d panneaux amares' % len(self.mgr.GetAllPanes()))
        self._log('Glissez le titre du panneau "Arbre" vers une cible,')
        self._log('ou double-cliquez ce titre pour le faire flotter.')

    # ------------------------------------------------------------------
    # construction des panneaux
    # ------------------------------------------------------------------

    def _panneau(self, couleur, titre, texte):
        cadre = tk.Frame(self.root, bg=couleur)
        etiquette = tk.Label(cadre, text=titre, bg=couleur,
                              font=('Helvetica', 11, 'bold'))
        etiquette.pack(pady=(10, 4))
        tk.Label(cadre, text=texte, bg=couleur, justify='left').pack(padx=12)
        # le titre sert de poignee de glissement : il reste visible meme
        # quand le panneau devient une fenetre flottante (wm manage)
        cadre._titre_label = etiquette
        return cadre

    def _carnet(self):
        # from taskcoachlib.guitk import tkauibook
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibook
        nb = tkauibook.AuiNotebook(self.panneau_centre)
        nb.pack(fill='both', expand=True)
        for i, (nom, couleur) in enumerate(
                [('Taches', '#fff0f0'), ('Categories', '#f0fff0'),
                 ('Effort', '#f0f0ff')]):
            page = tk.Frame(nb._page_area, bg=couleur)
            tk.Label(page, text='Page %s' % nom, bg=couleur).pack(expand=True)
            nb.AddPage(page, nom, i == 0)
        return nb

    def _log(self, message):
        horodatage = time.strftime('%H:%M:%S')
        self.journal.append(message)
        try:
            self.zone_journal.insert('end', '[%s] %s\n' % (horodatage, message))
            self.zone_journal.see('end')
        except Exception:
            pass
        if self.auto:
            # en mode automatique, tout est aussi ecrit sur la sortie standard
            # pour les journaux d'integration continue
            print('[%s] %s' % (horodatage, message), flush=True)

    # ------------------------------------------------------------------
    # glisser-deposer des panneaux (legende vers zones d'amarrage)
    # ------------------------------------------------------------------

    def _preparer_drag_drop(self):
        """Amorce le glisser-deposer sur le titre du panneau gauche.

        Le titre reste visible meme quand le panneau devient une fenetre
        flottante, ce qui permet de le ramener ensuite dans la disposition.
        """
        etiquette = getattr(self.panneau_gauche, '_titre_label', None)
        if etiquette is None:
            self._log('titre du panneau gauche introuvable : glisser-deposer desactive')
            return
        etiquette.bind('<ButtonPress-1>', self._sur_appui, add='+')
        etiquette.bind('<B1-Motion>', self._sur_glisse, add='+')
        etiquette.bind('<ButtonRelease-1>', self._sur_relachement, add='+')
        etiquette.bind('<Double-Button-1>', self._sur_double_clic, add='+')

    def _sur_appui(self, event):
        self._point_appui = (event.x_root, event.y_root)
        self._cree_zones_amarrage()

    def _cree_zones_amarrage(self):
        """Dessine les cibles d'amarrage en haut du panneau central."""
        if self.zone_canvas is not None:
            return
        self.zone_hote = self.panneau_centre
        self.zones = {}
        zone_c = tk.Canvas(self.zone_hote, height=34, bg='#ffffdd',
                           highlightthickness=1, highlightbackground='#a08040')
        zone_c.pack(side='top', fill='x', before=self.notebook)
        zone_c.update_idletasks()
        largeur = max(zone_c.winfo_width(), 300)
        formes = {
            'left': (10, 6, 64, 28),
            'center': (largeur // 2 - 27, 6, largeur // 2 + 27, 28),
            'right': (largeur - 64, 6, largeur - 10, 28),
        }
        for cible, (x1, y1, x2, y2) in formes.items():
            ident = zone_c.create_rectangle(x1, y1, x2, y2,
                                            fill='#ffffff', outline='#5a5aa0')
            zone_c.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                               text=cible, font=('Helvetica', 8, 'bold'))
            self.zones[cible] = ident
        self.zone_canvas = zone_c
        self._log('zones d\'amarrage visibles : %s' % ', '.join(self.zones))

    def _sur_glisse(self, event):
        x, y = event.x_root, event.y_root
        self._point_courant = (x, y)
        if not getattr(self, 'zones', None):
            return
        survol = self._cible_survollee()
        for cible, ident in self.zones.items():
            couleur = '#a0c8ff' if cible == survol else '#ffffff'
            self.zone_canvas.itemconfigure(ident, fill=couleur)

    def _cible_survollee(self):
        x, y = getattr(self, '_point_courant', (0, 0))
        if not getattr(self, 'zone_canvas', None):
            return None
        x_local = x - self.zone_canvas.winfo_rootx()
        y_local = y - self.zone_canvas.winfo_rooty()
        for cible, ident in self.zones.items():
            x1, y1, x2, y2 = self.zone_canvas.coords(ident)
            if x1 <= x_local <= x2 and y1 <= y_local <= y2:
                return cible
        return None

    def _sur_relachement(self, event):
        cible = self._cible_survollee()
        self._supprime_zones_amarrage()
        if cible is None:
            self._log('relachement hors cible : panneau inchange')
            return False
        self._amarre(cible)
        return True

    def _supprime_zones_amarrage(self):
        if getattr(self, 'zone_canvas', None) is not None:
            self.zone_canvas.destroy()
            self.zone_canvas = None
            self.zones = {}

    def _sur_double_clic(self, event):
        """Double-clic sur le titre : bascule flottant / amarre."""
        self._supprime_zones_amarrage()
        if self._flottant:
            self._reamarrer()
            self._flottant = False
        else:
            self._amarre_flottant()
            self._flottant = True

    def _amarre(self, cible):
        """Re-amarre le panneau gauche selon la cible, puis met a jour."""
        directions = {'left': cst.AUI_DOCK_LEFT, 'center': cst.AUI_DOCK_CENTER,
                      'right': cst.AUI_DOCK_RIGHT}
        self.pa.dock_direction = directions.get(cible, cst.AUI_DOCK_LEFT)
        if cible == 'center':
            # le centre remplace la disposition : on passe le centre en droit
            self.pd.dock_direction = cst.AUI_DOCK_RIGHT
        self.mgr.Update()
        self.root.update_idletasks()
        gestion = self.panneau_gauche.winfo_manager()
        self._log('panneau "Arbre" amarre a droite de "%s" (gestion=%s)'
                  % (cible, gestion))

    def _amarre_flottant(self):
        """Transforme le panneau gauche en fenetre flottante via wm manage."""
        cadre = self.panneau_gauche
        cadre.pack_forget()
        self.root.tk.call('wm', 'manage', cadre._w)
        self.root.tk.call('wm', 'title', cadre._w, 'Arbre (flottant)')
        self.root.tk.call('wm', 'geometry', cadre._w, '240x180+120+120')
        self.root.update_idletasks()
        geometrie = str(self.root.tk.call('wm', 'geometry', cadre._w))
        self._log('panneau flottant : %s' % geometrie)

    def _reamarrer(self):
        """Rattache le panneau flottant a la disposition geree."""
        cadre = self.panneau_gauche
        try:
            self.root.tk.call('wm', 'forget', cadre._w)
        except Exception:
            pass
        self.mgr.Update()
        self.root.update_idletasks()
        self._log('panneau re-amarre (gestion=%s)' % cadre.winfo_manager())

    # ------------------------------------------------------------------
    # sequence automatique (validation sans intervention)
    # ------------------------------------------------------------------

    def executer_sequence_auto(self):
        """Simule un glisser-deposer complet et verifie le resultat."""
        resultats = {}

        # 0 : poignee (titre du panneau) presente
        resultats['poignee'] = getattr(self.panneau_gauche, '_titre_label', None) is not None

        # 1 : etat initial
        self.root.update_idletasks()
        resultats['initial'] = (self.panneau_gauche.winfo_manager() == 'pack'
                                and self.pa.dock_direction == cst.AUI_DOCK_LEFT)

        # 2 : appui sur la legende
        legende = getattr(self.panneau_gauche, '_aui_caption', None)
        self._point_courant = (0, 0)
        self._cree_zones_amarrage()
        self.root.update_idletasks()
        resultats['zones_creees'] = len(self.zones) == 3

        # 3 : survol de la cible "right"
        ident = self.zones['right']
        x1, y1, x2, y2 = self.zone_canvas.coords(ident)
        x = self.zone_canvas.winfo_rootx() + (x1 + x2) // 2
        y = self.zone_canvas.winfo_rooty() + (y1 + y2) // 2
        self._point_courant = (x, y)
        resultats['survol_right'] = self._cible_survollee() == 'right'

        # 4 : relachement -> re-amarrage
        self._amarre(self._cible_survollee())
        self.root.update_idletasks()
        resultats['reamarre'] = (self.pa.dock_direction == cst.AUI_DOCK_RIGHT
                                 and self.panneau_gauche.winfo_manager() == 'pack')

        # 5 : flottant via wm manage
        self._amarre_flottant()
        resultats['flottant'] = str(
            self.root.tk.call('wm', 'geometry',
                              self.panneau_gauche._w)).startswith('240x180')

        # 6 : retour dans la disposition
        self._reamarrer()
        resultats['retour_disposition'] = self.panneau_gauche.winfo_manager() == 'pack'

        # 7 : selection du carnet
        if self.notebook.GetPageCount() >= 2:
            self.notebook.SetSelection(1)
            self.root.update_idletasks()
            resultats['carnet'] = self.notebook.GetSelection() == 1

        # 8 : perspectives
        disposition = self.mgr.SavePerspective()
        resultats['perspective'] = len(disposition) > 10

        for cle, valeur in resultats.items():
            self._log('verification %-12s : %s' % (cle, 'OK' if valeur else 'ECHEC'))
        return all(resultats.values())

    def boucler(self):
        if self.auto:
            try:
                succes = self.executer_sequence_auto()
            finally:
                self.root.after(400, self.root.destroy)
            self.root.mainloop()
            return 0 if succes else 1
        if self.duree:
            self.root.title('Demo AUI Tkinter (fermeture dans %ds)' % self.duree)
            self.root.after(self.duree * 1000, self.root.destroy)
        self.root.mainloop()
        return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    auto = '--auto' in argv
    duree = 30
    if '--duree' in argv:
        duree = int(argv[argv.index('--duree') + 1])
    application = DemoTkAui(auto=auto, duree=duree)
    return application.boucler()


if __name__ == '__main__':
    sys.exit(main())
