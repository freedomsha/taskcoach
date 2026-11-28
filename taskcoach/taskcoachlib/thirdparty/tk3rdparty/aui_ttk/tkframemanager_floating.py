# -*- coding: utf-8 -*-
"""Fenêtres graphiques de guidage AUI, indépendantes du modèle de disposition.

Les panneaux flottants sont gérés par ttkframemanager_floating. Les guides
utilisent les coordonnées écran et ne capturent ni le focus ni la souris.
"""
import tkinter as tk
from .aui_tk_constants import (AUI_DOCK_LEFT, AUI_DOCK_RIGHT, AUI_DOCK_TOP,
    AUI_DOCK_BOTTOM, AUI_DOCK_CENTER, AUI_MGR_VENETIAN_BLINDS_HINT)
from .ttkframemanager_floating import TtkFloatingFrame

# Compatibilité avec les anciens imports.
AuiFloatingFrame = TtkFloatingFrame


def _geometry(rect):
    """Convertit un rectangle écran (x, y, largeur, hauteur) en géométrie Tk."""
    x, y, w, h = map(int, rect)
    return f'{max(1,w)}x{max(1,h)}+{x}+{y}'


class AuiDockingGuide(tk.Toplevel):
    """Fenêtre superposée sans décoration, initialement masquée."""
    def __init__(self, parent, id=-1, title='', pos=None, size=None,
                 style=None, name='AuiDockingGuide'):
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.configure(takefocus=False)
        try:
            self.attributes('-topmost', True)
        except tk.TclError:
            pass
        self._valid = True
        self._rect = None
        if pos is not None and size is not None:
            self.geometry(_geometry((*pos, *size)))

    def Show(self, show=True):
        """Affiche ou masque le guide sans prendre le focus."""
        if show and self._valid:
            self.deiconify()
            self.lift()
        else:
            self.withdraw()

    def SetValid(self, valid):
        """Autorise ou interdit la destination."""
        self._valid = bool(valid)
        if not self._valid:
            self.Show(False)

    def IsValid(self):
        """Indique si la destination est autorisée."""
        return self._valid

    def HitTest(self, x, y):
        """Teste le rectangle demandé, même avant le prochain Configure Tk."""
        if not self._valid or self._rect is None or self.state() == 'withdrawn':
            return False
        l,t,w,h = self._rect
        return l <= x < l+w and t <= y < t+h

    def ValidateNotebookDocking(self, valid):
        """Retourne l'autorisation de fusion en onglets."""
        return bool(valid)


class AuiDockingGuideWindow(AuiDockingGuide):
    """Guide directionnel dessiné sur Canvas, avec surbrillance et icônes."""
    SIZE = 32
    def __init__(self, parent, rect, direction=0, center=False, useAero=False):
        super().__init__(parent)
        self._direction = direction
        self._center = center
        self._useAero = useAero
        self._highlighted = False
        self._relative = False
        self._photo_image = None
        self._bmp_unfocus = self._bmp_focus = None
        self._canvas = tk.Canvas(self, highlightthickness=0, takefocus=False)
        self._canvas.pack(fill='both', expand=True)
        self._canvas.bind('<Configure>', self.OnPaint, add='+')
        self._set_rect(rect)
        self._load_images()

    def _load_images(self):
        """Charge les ressources historiques si elles sont compatibles Tk."""
        self._bmp_unfocus = self._bmp_focus = None
        try:
            from .aui_tk_utilities import GetDockingImage
            self._bmp_unfocus, self._bmp_focus = GetDockingImage(
                self._direction, self._useAero, self._center)
        except (ImportError, AttributeError, TypeError, tk.TclError):
            pass

    def _set_rect(self, rect):
        """Mémorise et applique la géométrie écran."""
        if hasattr(rect, 'x'):
            rect = rect.x, rect.y, rect.width, rect.height
        rect = tuple(map(int, rect))
        if rect != self._rect:
            self._rect = rect
            self.geometry(_geometry(rect))

    def SetDirection(self, direction, relative=False):
        """Change la flèche et le style global ou relatif."""
        if (direction, relative) != (self._direction, self._relative):
            self._direction, self._relative = direction, relative
            self._center = direction == AUI_DOCK_CENTER or relative
            self._load_images()
            self.OnPaint()

    def SetHighlighted(self, highlighted):
        """Actualise le rendu lorsque la souris survole la destination."""
        if self._highlighted != bool(highlighted):
            self._highlighted = bool(highlighted)
            self.OnPaint()

    def DrawBackground(self, dc):
        """Dessine le fond et la bordure du guide."""
        w,h = self._rect[2:]
        dc.create_rectangle(1,1,w-1,h-1, width=2,
            fill='#2864b4' if self._highlighted else '#edf3fb',
            outline='#498979' if self._relative else '#24558b')

    def DrawDottedLine(self, dc, point, length, vertical=True):
        """Dessine une ligne pointillée de décoration."""
        x,y = point
        dc.create_line(x,y,x if vertical else x+length,
                       y+length if vertical else y, dash=(2,2), fill='white')

    def DrawIcon(self, dc):
        """Utilise une image Tk historique ou le dessin vectoriel de secours."""
        img = self._bmp_focus if self._highlighted else self._bmp_unfocus
        try:
            if hasattr(img, 'GetPhotoImage'):
                img = img.GetPhotoImage()
            if isinstance(img, tk.Image):
                self._photo_image = img
                w,h = self._rect[2:]
                dc.create_image(w/2,h/2,image=img)
                return
        except (tk.TclError, TypeError, AttributeError):
            pass
        self._photo_image = None
        self.DrawArrow(dc)

    def DrawArrow(self, dc):
        """Dessine une flèche native, sans dépendance aux ressources wx."""
        w,h = self._rect[2:]
        x,y = w/2,h/2
        d = min(w,h)*.28
        ink = 'white' if self._highlighted else '#24558b'
        vectors = {AUI_DOCK_LEFT:(-1,0), AUI_DOCK_RIGHT:(1,0),
                   AUI_DOCK_TOP:(0,-1), AUI_DOCK_BOTTOM:(0,1)}
        if self._direction == AUI_DOCK_CENTER:
            dc.create_rectangle(x-d,y-d,x+d,y+d,outline=ink,width=3)
        elif self._direction in vectors:
            dx,dy = vectors[self._direction]
            dc.create_line(x-d*dx,y-d*dy,x+d*dx,y+d*dy,
                           arrow=tk.LAST,arrowshape=(8,10,4),fill=ink,width=3)

    def OnPaint(self, event=None):
        """Redessine les éléments persistants du Canvas."""
        self._canvas.delete('all')
        self.DrawBackground(self._canvas)
        self.DrawIcon(self._canvas)

    def Draw(self, dc=None):
        """Point de compatibilité pour demander un nouveau rendu."""
        self.OnPaint()

    def UpdateDockGuide(self, pos):
        """Déplace le guide en conservant ses dimensions."""
        self._set_rect((*pos, *self._rect[2:]))

    def AeroMove(self, pos):
        """Déplace immédiatement le guide, sans animation native wx."""
        self.UpdateDockGuide(pos)


class AuiSingleDockingGuide(AuiDockingGuideWindow):
    """Flèche indépendante, utilisable en périphérie ou près d'un panneau."""
    def __init__(self, parent, direction=0):
        super().__init__(parent, (0,0,self.SIZE,self.SIZE), direction)


class AuiCenterDockingGuide(AuiDockingGuideWindow):
    """Guide composite central : quatre directions et fusion optionnelle."""
    def __init__(self, parent):
        super().__init__(parent,(0,0,96,96),AUI_DOCK_CENTER,True)
        self._allowed = set()
        self._selected = None
        self._target = None
        self._notebook = False

    def SetTarget(self, pane):
        """Mémorise le panneau de référence."""
        self._target = pane

    def SetAllowedDirections(self, directions):
        """Définit les cellules actives du guide composite."""
        self._allowed = set(directions)
        self.OnPaint()

    def ValidateNotebookDocking(self, valid):
        """Active la cellule centrale uniquement si la fusion est permise."""
        self._notebook = bool(valid)
        self.OnPaint()
        return self._notebook

    def _cells(self):
        """Retourne les cellules et leurs directions en coordonnées locales."""
        return {AUI_DOCK_TOP:(1,0), AUI_DOCK_LEFT:(0,1),
                AUI_DOCK_CENTER:(1,1), AUI_DOCK_RIGHT:(2,1), AUI_DOCK_BOTTOM:(1,2)}

    def GetDirectionAt(self,x,y):
        """Retourne la direction active sous le pointeur écran."""
        if not super().HitTest(x,y):
            return None
        l,t,_,_ = self._rect
        cell = ((x-l)//32,(y-t)//32)
        return next((d for d,p in self._cells().items() if p==cell
                     and d in self._allowed and (d!=AUI_DOCK_CENTER or self._notebook)),None)

    def HitTest(self,x,y):
        """Teste uniquement les cellules actives."""
        return self.GetDirectionAt(x,y) is not None

    def SetHighlighted(self,direction):
        """Sélectionne la cellule à mettre en surbrillance."""
        if self._selected != direction:
            self._selected = direction
            self.OnPaint()

    def OnPaint(self,event=None):
        """Dessine les cellules du guide composite."""
        if not hasattr(self,'_allowed'):
            return
        c=self._canvas
        c.delete('all')
        symbols={AUI_DOCK_TOP:'↑',AUI_DOCK_BOTTOM:'↓',AUI_DOCK_LEFT:'←',
                 AUI_DOCK_RIGHT:'→',AUI_DOCK_CENTER:'□'}
        for d,(col,row) in self._cells().items():
            if d not in self._allowed or (d==AUI_DOCK_CENTER and not self._notebook):
                continue
            x,y=col*32,row*32
            active=d==self._selected
            c.create_rectangle(x+1,y+1,x+31,y+31,outline='#24558b',
                               fill='#2864b4' if active else '#edf3fb')
            c.create_text(x+16,y+16,text=symbols[d],font=('TkDefaultFont',18),
                          fill='white' if active else '#24558b')


class AuiDockingHintWindow(AuiDockingGuide):
    """Aperçu translucide d'un rectangle calculé par le contrôleur."""
    def __init__(self,parent,id=-1,title='',pos=None,size=(1,1),style=None,name='auiHintWindow'):
        super().__init__(parent,id,title,pos,size,style,name)
        self._blindMode=False
        try:
            self.attributes('-alpha',.28)
        except tk.TclError:
            pass
        self._canvas=tk.Canvas(self,highlightthickness=0,bg='#397dd5')
        self._canvas.pack(fill='both',expand=True)
        self._canvas.bind('<Configure>',self.OnPaint,add='+')

    def ShowHint(self,rect):
        """Affiche un rectangle écran (x, y, largeur, hauteur)."""
        x,y,w,h=map(int,rect)
        if min(w,h)<=0:
            self.Show(False)
            return
        if self._rect != (x,y,w,h):
            self._rect=(x,y,w,h)
            self.geometry(_geometry(self._rect))
        self.Show(True)

    def SetBlindMode(self,agwFlags):
        """Active un motif pointillé en remplacement des stores wx."""
        self._blindMode=bool(agwFlags & AUI_MGR_VENETIAN_BLINDS_HINT)
        self.OnPaint()

    def OnSize(self,event=None):
        """Redessine l'aperçu après redimensionnement."""
        self.OnPaint()

    def OnPaint(self,event=None):
        """Dessine la bordure et le motif optionnel."""
        c=self._canvas
        c.delete('all')
        c.create_rectangle(2,2,max(3,c.winfo_width()-2),max(3,c.winfo_height()-2),
                           outline='#24558b',width=3,dash=(4,3) if self._blindMode else ())
