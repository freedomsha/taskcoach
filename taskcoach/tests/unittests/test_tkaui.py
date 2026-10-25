# -*- coding: utf-8 -*-
"""Tests unitaires des modules AUI convertis en Tkinter (taskcoachlib.guitk).

A copier dans tests/unittests/ sous le nom test_tkaui.py, puis a lancer
depuis la racine du depot Task Coach :

    python -m unittest tests.unittests.test_tkaui -v

Sans affichage (integration continue), les tests graphiques sont ignores
automatiquement. Sous Linux sans ecran physique, on peut les activer avec
un serveur X virtuel :

    xvfb-run -a python -m unittest tests.unittests.test_tkaui -v
"""

import importlib
import sys
import unittest
from types import SimpleNamespace

import tkinter as tk
from tkinter import font as tkfont


def _affichage_disponible():
    """Renvoie True si un affichage Tk peut etre ouvert."""
    try:
        racine = tk.Tk()
        racine.withdraw()
        racine.destroy()
        return True
    except Exception:
        return False


AFFICHAGE = _affichage_disponible()


def _gui(classe):
    """Marque une classe de tests comme necessitant un affichage."""
    return unittest.skipUnless(AFFICHAGE, "aucun affichage disponible pour Tkinter")(classe)


# tkauitoolbar.py importe '.tkauibar_items' ; si ce module n'existe pas dans
# l'arborescence, on fournit un alias vers tkauibar.py (memes classes).
try:
    # import taskcoachlib.guitk.tkauibar_items  # noqa: F401
    import taskcoachlib.thirdparty.tk3rdparty.aui_tk.tkauibar_event_item  # noqa: F401
except ImportError:
    _items = importlib.import_module('taskcoachlib.thirdparty.tk3rdparty.aui_tk.tkauibar')
    sys.modules['taskcoachlib.thirdparty.tk3rdparty.aui_tk.tkauibar_event_item'] = _items

# from taskcoachlib.guitk import aui_tk_constants as cst
from taskcoachlib.thirdparty.tk3rdparty.aui_tk import aui_tk_constants as cst
# from taskcoachlib.guitk import aui_tk_utilities as ut
from taskcoachlib.thirdparty.tk3rdparty.aui_tk  import aui_tk_utilities as ut
# from taskcoachlib.guitk import tkauibar as bar_items
from taskcoachlib.thirdparty.tk3rdparty.aui_tk  import tkauibar_event_item as bar_items
# from taskcoachlib.guitk import tkframemanager as fm
# from taskcoachlib.thirdparty.tk3rdparty.aui_tk  import tkframemanager as fm
from taskcoachlib.thirdparty.tk3rdparty.aui_tk  import tkframemanager_auimanager as fm
# from taskcoachlib.thirdparty.tk3rdparty.aui_tk.tkframemanager import (AuiDockInfo, AuiDockingGuideInfo,
#     AuiDockUIPart, AuiPaneButton, AuiManagerEvent, AuiPaneInfo, NonePaneInfo)
from taskcoachlib.thirdparty.tk3rdparty.aui_tk.tkframemanager_elements import AuiDockInfo, AuiDockingGuideInfo, AuiDockUIPart, AuiPaneButton, AuiPaneInfo, AuiManagerEvent
from taskcoachlib.thirdparty.tk3rdparty.aui_tk.tkframemanager_auimanager import AuiManager, NonePaneInfo


def _fausse_page(caption='Onglet', active=True):
    """Faux objet page, avec les attributs lus par l'art des onglets."""
    return SimpleNamespace(caption=caption, active=active, bitmap=None,
                           window=None, control=None, text_colour='#000000',
                           hidden=False, enabled=True, hasCloseButton=True,
                           rect=(0, 0, 100, 30))


class FauxDC:
    """Simule un objet de mesure de texte (measure + metrics)."""

    def __init__(self, largeur_caractere=7, hauteur_ligne=12):
        self.largeur_caractere = largeur_caractere
        self.hauteur_ligne = hauteur_ligne

    def measure(self, texte):
        return self.largeur_caractere * len(str(texte))

    def metrics(self, quoi=None):
        return self.hauteur_ligne


# ---------------------------------------------------------------------------
# Constantes (sans affichage)
# ---------------------------------------------------------------------------

class TestConstantes(unittest.TestCase):

    def test_directions_amarrage(self):
        self.assertEqual([cst.AUI_DOCK_NONE, cst.AUI_DOCK_TOP, cst.AUI_DOCK_RIGHT,
                          cst.AUI_DOCK_BOTTOM, cst.AUI_DOCK_LEFT, cst.AUI_DOCK_CENTER],
                         [0, 1, 2, 3, 4, 5])
        self.assertEqual(cst.AUI_DOCK_CENTRE, cst.AUI_DOCK_CENTER)

    def test_actions(self):
        self.assertEqual([cst.actionNone, cst.actionResize, cst.actionClickButton],
                         [0, 1, 2])

    def test_genres_d_outils(self):
        self.assertEqual([cst.ITEM_NORMAL, cst.ITEM_CHECK, cst.ITEM_SEPARATOR,
                          cst.ITEM_RADIO, cst.ITEM_CONTROL, cst.ITEM_LABEL,
                          cst.ITEM_SPACER], [0, 1, 2, 3, 4, 5, 6])

    def test_styles_definis(self):
        self.assertNotEqual(cst.AUI_NB_DEFAULT_STYLE, 0)
        self.assertNotEqual(cst.AUI_MGR_DEFAULT, 0)

    def test_couleur_texte_desactivee(self):
        self.assertEqual(cst.DISABLED_TEXT_COLOUR, '#999999')


@_gui
class TestConstantesGraphiques(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_decodage_images_integrees(self):
        photo = cst.aero_up_single.GetPhotoImage()
        self.assertGreater(photo.width(), 0)
        self.assertGreater(photo.height(), 0)


# ---------------------------------------------------------------------------
# Utilitaires (couleurs et texte, sans affichage)
# ---------------------------------------------------------------------------

class TestCouleursUtilitaires(unittest.TestCase):

    def test_blend_colour(self):
        self.assertEqual(ut.BlendColour(10, 20, 0.5), 15.0)
        # Note : contrairement a la version wxPython, la conversion actuelle
        # ne borne pas le resultat dans [0, 255] (voir rapport de tests).

    def test_rgb_couleurs_nommees(self):
        self.assertEqual(ut._rgb('white'), (255, 255, 255))
        self.assertEqual(ut._rgb('BLACK'), (0, 0, 0))

    def test_rgb_hexa(self):
        self.assertEqual(ut._rgb('#316ac5'), (0x31, 0x6a, 0xc5))
        self.assertEqual(ut._rgb('#fff'), (255, 255, 255))

    def test_rgb_tuple(self):
        self.assertEqual(ut._rgb((18, 52, 86)), (18, 52, 86))

    def test_rgb_invalide(self):
        self.assertRaises(TypeError, ut._rgb, 12345)

    def test_couleur_hexa(self):
        self.assertEqual(ut._colour((0x31, 0x6a, 0xc5)), '#316ac5')
        # bornage : 300 -> 255 (ff), -5 -> 0 (00), 12 -> 0c
        self.assertEqual(ut._colour((300, -5, 12)), '#ff000c')

    def test_step_colour_neutre(self):
        self.assertEqual(ut.StepColour('#808080', 100), '#808080')

    def test_step_colour_extremes(self):
        self.assertEqual(ut.StepColour('#ffffff', 0), '#000000')
        self.assertEqual(ut.StepColour('#000000', 200), '#ffffff')

    def test_light_colour(self):
        self.assertEqual(ut.LightColour('#001100', 100), '#ffffff')
        self.assertEqual(ut.LightColour('#808080', 50), '#bfbfbf')

    def test_light_contrast_colour(self):
        self.assertEqual(ut.LightContrastColour('#101010'), '#9f9f9f')
        self.assertEqual(ut.LightContrastColour('#a0a0a0'), ut.StepColour('#a0a0a0', 120))

    def test_clip(self):
        self.assertEqual(ut.Clip(5, 1, 10), 5)
        self.assertEqual(ut.Clip(0, 1, 10), 1)
        self.assertEqual(ut.Clip(99, 1, 10), 10)

    def test_get_base_colour(self):
        self.assertEqual(ut.GetBaseColour(), '#d9d9d9')


class TestTexteUtilitaires(unittest.TestCase):

    def test_chop_texte_rentre(self):
        self.assertEqual(ut.ChopText(FauxDC(), 'abc', 100), 'abc')

    def test_chop_texte_coupe(self):
        resultat = ut.ChopText(FauxDC(), 'a' * 80, 50)
        self.assertTrue(resultat.endswith('...'))
        self.assertLess(len(resultat), 80)

    def test_get_label_size(self):
        self.assertEqual(ut.GetLabelSize(FauxDC(), 'hello', False), (35, 12))
        self.assertEqual(ut.GetLabelSize(FauxDC(), 'hello', True), (12, 35))

    def test_get_label_size_libelle_vide(self):
        largeur, hauteur = ut.GetLabelSize(FauxDC(), '   ', False)
        self.assertEqual(largeur, 0)
        self.assertEqual(hauteur, 12)


try:
    from PIL import Image  # noqa: F401
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False


@unittest.skipUnless(PIL_DISPONIBLE, 'Pillow non installe')
class TestImagesUtilitaires(unittest.TestCase):

    def test_pane_create_stipple_bitmap(self):
        image = ut.PaneCreateStippleBitmap()
        self.assertEqual(image.size, (2, 2))

    def test_draw_mac_close_button(self):
        image = ut.DrawMACCloseButton('#333333', None, 16)
        self.assertEqual(image.size, (16, 16))
        self.assertEqual(image.mode, 'RGBA')

    def test_make_disabled_bitmap(self):
        source = Image.new('RGB', (4, 4), (255, 0, 0))
        resultat = ut.MakeDisabledBitmap(source)
        self.assertEqual(resultat.size, (4, 4))

    def test_darken_bitmap(self):
        source = Image.new('RGBA', (2, 2), (100, 100, 100, 255))
        resultat = ut.DarkenBitmap(source, '#808080', '#404040')
        self.assertEqual(resultat.size, (2, 2))


class TestAmarrageUtilitaires(unittest.TestCase):

    def test_get_docking_image(self):
        resultat = ut.GetDockingImage(cst.AUI_DOCK_LEFT, 1, True)
        self.assertEqual(len(resultat), 2)
        self.assertIsNotNone(resultat[0])

    def test_get_sliding_points(self):
        points = ut.GetSlidingPoints((10, 20, 30, 40), (100, 50), cst.AUI_DOCK_LEFT)
        self.assertEqual(len(points), 4)
        self.assertEqual(points[0], 42)  # x + largeur + 2
        self.assertEqual(points[1], 20)

    def test_indent_pressed_bitmap(self):
        rect = (10, 10, 20, 20)
        self.assertEqual(ut.IndentPressedBitmap(rect, cst.AUI_BUTTON_STATE_NORMAL), rect)
        decale = ut.IndentPressedBitmap((10, 10, 20, 20), cst.AUI_BUTTON_STATE_PRESSED)
        self.assertEqual((decale[0], decale[1]), (11, 11))

    def test_copy_attributes(self):
        class Art:
            pass
        ancien, nouveau = Art(), Art()
        ancien._base_colour = '#123456'
        ancien._font = 'fonte'
        ut.CopyAttributes(nouveau, ancien)
        self.assertEqual(nouveau._base_colour, '#123456')


# ---------------------------------------------------------------------------
# Structures du gestionnaire (sans affichage)
# ---------------------------------------------------------------------------

class TestPaneInfo(unittest.TestCase):

    def test_panneau_vierge_non_valide(self):
        self.assertFalse(AuiPaneInfo().IsOk())

    def test_chainage_retourne_self(self):
        p = AuiPaneInfo()
        self.assertIs(p.Caption('X').Left().Layer(1).Row(0).Position(2), p)

    def test_directions(self):
        self.assertEqual(AuiPaneInfo().Left().dock_direction, cst.AUI_DOCK_LEFT)
        self.assertEqual(AuiPaneInfo().Right().dock_direction, cst.AUI_DOCK_RIGHT)
        self.assertEqual(AuiPaneInfo().Top().dock_direction, cst.AUI_DOCK_TOP)
        self.assertEqual(AuiPaneInfo().Bottom().dock_direction, cst.AUI_DOCK_BOTTOM)
        self.assertEqual(AuiPaneInfo().Center().dock_direction, cst.AUI_DOCK_CENTER)
        self.assertEqual(AuiPaneInfo().Centre().dock_direction, cst.AUI_DOCK_CENTRE)

    def test_visibilite(self):
        p = AuiPaneInfo()
        self.assertTrue(p.IsShown())
        p.Hide()
        self.assertFalse(p.IsShown())
        p.Show()
        self.assertTrue(p.IsShown())

    def test_flottant(self):
        p = AuiPaneInfo().Float()
        self.assertTrue(p.IsFloating())
        self.assertFalse(p.IsDocked())
        p.Dock()
        self.assertTrue(p.IsDocked())

    def test_amarrabilite(self):
        p = AuiPaneInfo().Dockable(False)
        self.assertFalse(p.IsDockable())
        p.Dockable(True)
        self.assertTrue(p.IsDockable())

    def test_boutons(self):
        p = AuiPaneInfo().CloseButton().MaximizeButton().MinimizeButton().PinButton()
        self.assertTrue(p.HasCloseButton())
        self.assertEqual(p.CountButtons(), 4)
        p.ResetButtons()
        self.assertFalse(p.HasCloseButton())
        self.assertEqual(p.CountButtons(), 0)

    def test_set_flag(self):
        p = AuiPaneInfo()
        p.SetFlag(AuiPaneInfo.optionHidden, True)
        self.assertTrue(p.HasFlag(AuiPaneInfo.optionHidden))
        p.SetFlag(AuiPaneInfo.optionHidden, False)
        self.assertFalse(p.HasFlag(AuiPaneInfo.optionHidden))

    def test_tailles(self):
        p = AuiPaneInfo().MinSize(100, 50).MaxSize(800, 600)
        self.assertEqual(p.min_size, (100, 50))
        self.assertEqual(p.max_size, (800, 600))

    def test_position_flottante(self):
        p = AuiPaneInfo().FloatingPosition(30, 40).FloatingSize(200, 150)
        self.assertEqual(p.floating_pos, (30, 40))
        self.assertEqual(p.floating_size, (200, 150))

    def test_centre_pane(self):
        p = AuiPaneInfo().CenterPane()
        self.assertEqual(p.dock_direction, cst.AUI_DOCK_CENTER)
        self.assertTrue(p.IsResizeable())

    def test_toolbar_pane(self):
        self.assertTrue(AuiPaneInfo().ToolbarPane().HasGripper())

    def test_restore(self):
        p = AuiPaneInfo().Maximize().Minimize()
        self.assertTrue(p.IsMaximized())
        self.assertTrue(p.IsMinimized())
        p.Restore()
        self.assertFalse(p.IsMaximized())
        self.assertFalse(p.IsMinimized())


class TestDockInfo(unittest.TestCase):

    def test_valide(self):
        d = AuiDockInfo()
        self.assertFalse(d.IsOk())
        d.dock_direction = cst.AUI_DOCK_TOP
        self.assertTrue(d.IsOk())
        self.assertTrue(d.IsHorizontal())
        self.assertFalse(d.IsVertical())

    def test_vertical(self):
        d = AuiDockInfo()
        d.dock_direction = cst.AUI_DOCK_LEFT
        self.assertTrue(d.IsVertical())


class TestDockingGuideInfo(unittest.TestCase):

    def test_chainage(self):
        g = AuiDockingGuideInfo().Host('x').Top()
        self.assertEqual(g.host, 'x')
        self.assertEqual(g.dock_direction, cst.AUI_DOCK_TOP)
        self.assertEqual(g.Left().dock_direction, cst.AUI_DOCK_LEFT)
        self.assertEqual(g.Right().dock_direction, cst.AUI_DOCK_RIGHT)
        self.assertEqual(g.Bottom().dock_direction, cst.AUI_DOCK_BOTTOM)
        self.assertEqual(g.Center().dock_direction, cst.AUI_DOCK_CENTER)


class TestDockUIPartEtBouton(unittest.TestCase):

    def test_types_de_partie(self):
        self.assertEqual([AuiDockUIPart.typeCaption, AuiDockUIPart.typeGripper,
                          AuiDockUIPart.typeDock, AuiDockUIPart.typeDockSizer,
                          AuiDockUIPart.typePane, AuiDockUIPart.typePaneSizer,
                          AuiDockUIPart.typeBackground, AuiDockUIPart.typePaneBorder,
                          AuiDockUIPart.typePaneButton], list(range(9)))

    def test_bouton_panneau(self):
        self.assertEqual(AuiPaneButton(123).button_id, 123)


class TestEvenementManager(unittest.TestCase):

    def test_veto(self):
        evt = AuiManagerEvent()
        self.assertFalse(evt.GetVeto())
        evt.Veto()
        self.assertTrue(evt.GetVeto())
        self.assertTrue(evt.CanVeto())

    def test_can_veto_desactive(self):
        evt = AuiManagerEvent()
        evt.SetCanVeto(False)
        evt.Veto()
        self.assertTrue(evt.GetVeto())
        self.assertFalse(evt.CanVeto())

    def test_accesseurs(self):
        evt = AuiManagerEvent()
        evt.SetPane('panneau')
        evt.SetButton('bouton')
        self.assertEqual(evt.GetPane(), 'panneau')
        self.assertEqual(evt.GetButton(), 'bouton')


# ---------------------------------------------------------------------------
# Items de barre d'outils (sans affichage)
# ---------------------------------------------------------------------------

class TestToolBarItems(unittest.TestCase):

    def test_item_defaut(self):
        item = bar_items.AuiToolBarItem()
        self.assertEqual(item.kind, cst.ITEM_NORMAL)
        self.assertEqual(item.id, 0)
        self.assertEqual(item.label, '')
        self.assertTrue(item.active)

    def test_item_accesseurs(self):
        item = bar_items.AuiToolBarItem()
        item.SetId(7)
        item.SetLabel('Ouvrir')
        item.SetKind(cst.ITEM_CHECK)
        item.SetShortHelp('aide')
        item.SetUserData('donnees')
        self.assertEqual((item.GetId(), item.GetLabel(), item.GetKind(),
                          item.GetShortHelp(), item.GetUserData()),
                         (7, 'Ouvrir', cst.ITEM_CHECK, 'aide', 'donnees'))

    def test_assign(self):
        source = bar_items.AuiToolBarItem()
        source.SetLabel('source')
        cible = bar_items.AuiToolBarItem().Assign(source)
        self.assertEqual(cible.GetLabel(), 'source')

    def test_evenement_veto_allow(self):
        evt = bar_items.AuiToolBarEvent()
        self.assertTrue(evt.IsAllowed())
        evt.Veto()
        self.assertFalse(evt.IsAllowed())
        evt.Allow()
        self.assertTrue(evt.IsAllowed())

    def test_command_capture(self):
        capture = bar_items.ToolbarCommandCapture()
        evt = bar_items.AuiToolBarEvent()
        evt.SetToolId(33)
        capture.ProcessEvent(evt)
        self.assertEqual(capture.GetCommandId(), 33)

    def test_command_tool_bar_event(self):
        evt = bar_items.CommandToolBarEvent()
        evt.SetToolId(9)
        evt.SetClickPoint((3, 4))
        evt.SetItemRect((0, 0, 10, 10))
        self.assertEqual(evt.GetToolId(), 9)
        self.assertEqual(evt.GetClickPoint(), (3, 4))
        self.assertEqual(evt.GetItemRect(), (0, 0, 10, 10))


# ---------------------------------------------------------------------------
# Base des tests graphiques
# ---------------------------------------------------------------------------

class CasGraphique(unittest.TestCase):
    """Cree une racine Tk masquee pour chaque test."""

    def setUp(self):
        self.tk = tk
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass


@_gui
class TestUtilitairesGraphiques(CasGraphique):

    def test_bitmap_from_bits(self):
        photo = ut.BitmapFromBits(bytes(32), 16, 16, '#000000')
        self.assertEqual((photo.width(), photo.height()), (16, 16))

    def test_draw_gradient_rectangle(self):
        canevas = self.tk.Canvas(self.root)
        ut.DrawGradientRectangle(canevas, (0, 0, 100, 40), '#ffffff', '#000000',
                                 cst.AUI_GRADIENT_VERTICAL)
        ut.DrawGradientRectangle(canevas, (0, 0, 100, 40), '#ffffff', '#000000',
                                 cst.AUI_GRADIENT_HORIZONTAL)
        self.assertGreater(len(canevas.find_all()), 0)

    def test_find_focus_descendant(self):
        self.assertIsNone(ut.FindFocusDescendant(self.root))
        cadre = self.tk.Frame(self.root)
        cadre.pack()
        etiquette = self.tk.Label(cadre, text='cible')
        etiquette.pack()
        self.root.update_idletasks()
        etiquette.focus_force()
        self.root.update_idletasks()
        self.assertIn(ut.FindFocusDescendant(self.root), (None, etiquette))

    def test_get_docking_image_decode(self):
        image, _ = ut.GetDockingImage(cst.AUI_DOCK_LEFT, 1, True)
        photo = image.GetPhotoImage()
        self.assertGreater(photo.width(), 0)


@_gui
class TestArtOnglets(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tktabart
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk  import tktabart
        self.module = tktabart
        self.art = tktabart.AuiDefaultTabArt()
        self.canevas = self.tk.Canvas(self.root)

    def test_flags(self):
        self.art.SetAGWFlags(cst.AUI_NB_DEFAULT_STYLE)
        self.assertEqual(self.art.GetAGWFlags(), cst.AUI_NB_DEFAULT_STYLE)

    def test_fontes(self):
        fonte = tkfont.Font(family='Helvetica', size=10)
        self.art.SetNormalFont(fonte)
        self.art.SetSelectedFont(fonte)
        self.art.SetMeasuringFont(fonte)
        self.assertIsInstance(self.art.GetNormalFont(), tkfont.Font)

    def test_clone(self):
        self.assertIsInstance(self.art.Clone(), self.module.AuiDefaultTabArt)

    def test_get_tab_size(self):
        taille, extension = self.art.GetTabSize(self.canevas, self.root,
                                                'Onglet', None, True, 0, None)
        self.assertEqual(len(taille), 2)
        self.assertGreaterEqual(taille[0], 50)
        self.assertGreaterEqual(taille[1], 10)

    def test_dessins(self):
        page = _fausse_page('Onglet')
        self.art.DrawBackground(self.canevas, self.root, (0, 0, 200, 30))
        self.art.DrawTab(self.canevas, self.root, page, (0, 0, 120, 30), 0, True)
        self.art.DrawButton(self.canevas, self.root, (0, 0, 50, 20), 0, 'vertical')
        self.art.DrawFocusRectangle(self.canevas, (0, 0, 100, 30))
        self.assertGreaterEqual(self.art.GetIndentSize(), 0)


@_gui
class TestArtAmarrage(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkdockart
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkdockart
        self.module = tkdockart
        self.art = tkdockart.AuiDefaultDockArt()
        self.canevas = self.tk.Canvas(self.root)
        self.panneau = SimpleNamespace(caption='Panneau', state=0, icon=None,
                                       window=None, hidden=False)

    def test_metriques(self):
        self.art.SetMetric(cst.AUI_DOCKART_SASH_SIZE, 7)
        self.assertEqual(self.art.GetMetric(cst.AUI_DOCKART_SASH_SIZE), 7)
        self.art.SetMetric(cst.AUI_DOCKART_SASH_SIZE, 4)
        self.assertEqual(self.art.GetMetric(cst.AUI_DOCKART_SASH_SIZE), 4)

    def test_couleurs(self):
        self.art.SetColor(cst.AUI_DOCKART_BACKGROUND_COLOUR, '#123456')
        self.assertEqual(self.art.GetColor(cst.AUI_DOCKART_BACKGROUND_COLOUR), '#123456')

    def test_police(self):
        self.assertIsInstance(self.art.GetFont(cst.AUI_DOCKART_CAPTION_FONT), tkfont.Font)

    def test_dessins(self):
        art, c, r, p = self.art, self.canevas, self.root, self.panneau
        art.DrawSash(c, r, 'vertical', (0, 0, 4, 100))
        art.DrawBackground(c, r, 'horizontal', (0, 0, 100, 30))
        art.DrawBorder(c, r, (0, 0, 100, 30), p)
        art.DrawCaptionBackground(c, (0, 0, 100, 20), p)
        art.DrawIcon(c, (0, 0, 20, 20), p)
        art.DrawCaption(c, r, 'Titre', (0, 0, 100, 20), p)
        art.DrawGripper(c, r, (0, 0, 8, 60), p)
        art.DrawPaneButton(c, r, 0, 0, (0, 0, 14, 14), p)
        art.DrawSashGripper(c, 'vertical', (0, 0, 4, 60))

    def test_modern_dock_art(self):
        self.assertIsInstance(self.module.ModernDockArt(self.root),
                              self.module.ModernDockArt)


@_gui
class TestArtBarreOutils(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkauibar_art
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibar_art
        self.art = tkauibar_art.AuiDefaultToolBarArt()
        self.canevas = self.tk.Canvas(self.root)

    def _outil(self):
        return SimpleNamespace(GetLabel=lambda: 'Outil',
                               IsActive=lambda: False,
                               HasDropDown=lambda: False)

    def test_dessins(self):
        outil = self._outil()
        self.art.DrawBackground(self.canevas, self.root, (0, 0, 100, 24))
        self.art.DrawLabel(self.canevas, self.root, outil, (0, 0, 100, 24))
        self.art.DrawButton(self.canevas, self.root, outil, (0, 0, 100, 24))
        self.art.DrawSeparator(self.canevas, self.root, (0, 0, 7, 24))
        self.art.DrawGripper(self.canevas, self.root, (0, 0, 7, 24))
        self.art.DrawOverflowButton(self.canevas, self.root, (0, 0, 16, 16), 0)

    def test_taille_outil(self):
        largeur, hauteur = self.art.GetToolSize(self.canevas, self.root, self._outil())
        self.assertGreater(largeur, 0)
        self.assertGreater(hauteur, 0)


@_gui
class TestBarreOutils(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkauitoolbar
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauitoolbar
        self.barre = tkauitoolbar.AuiToolBar(self.root)

    def test_ajout_outils(self):
        self.barre.AddSimpleTool(101, 'Nouveau', None, 'Creer')
        self.barre.AddToggleTool(102, None)
        self.barre.AddSeparator()
        self.assertEqual(self.barre.GetToolCount(), 3)

    def test_realize(self):
        self.barre.AddSimpleTool(101, 'Nouveau', None)
        self.assertTrue(self.barre.Realize())

    def test_recherche(self):
        self.barre.AddSimpleTool(101, 'Nouveau', None)
        outil = self.barre.FindTool(101)
        self.assertIsNotNone(outil)
        self.assertEqual(self.barre.FindToolByLabel('Nouveau'), outil)
        self.assertIsNone(self.barre.FindTool(999))

    def test_bascule(self):
        self.barre.AddToggleTool(102, None)
        self.barre.ToggleTool(102, True)
        self.assertTrue(self.barre.GetToolToggled(102))
        self.barre.ToggleTool(102, False)
        self.assertFalse(self.barre.GetToolToggled(102))

    def test_activation(self):
        self.barre.AddSimpleTool(101, 'Nouveau', None)
        self.barre.EnableTool(101, False)
        self.assertFalse(self.barre.GetToolEnabled(101))
        self.barre.EnableTool(101, True)
        self.assertTrue(self.barre.GetToolEnabled(101))

    def test_libelle(self):
        self.barre.AddSimpleTool(101, 'Nouveau', None)
        self.assertEqual(self.barre.GetToolLabel(101), 'Nouveau')
        self.barre.SetToolLabel(101, 'Nouveau fichier')
        self.assertEqual(self.barre.GetToolLabel(101), 'Nouveau fichier')

    def test_art_provider(self):
        self.assertIsNotNone(self.barre.GetArtProvider())

    def test_hit_test(self):
        self.barre.AddSimpleTool(101, 'Nouveau', None)
        self.barre.Realize()
        self.root.update_idletasks()
        self.assertIn(self.barre.HitTest(5, 5), (0, -1))


@_gui
class TestConteneurOnglets(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkauibook_tabs
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibook_tabs
        self.conteneur = tkauibook_tabs.AuiTabContainer(self.root)
        self.p1 = _fausse_page('Alpha')
        self.p1.window = 'w1'
        self.p1.rect = (0, 0, 100, 30)
        self.p2 = _fausse_page('Beta')
        self.p2.window = 'w2'
        self.p2.rect = (100, 0, 100, 30)

    def test_ajouts(self):
        self.assertTrue(self.conteneur.AddPage(self.p1.window, self.p1))
        self.assertEqual(self.conteneur.GetPageCount(), 1)
        self.assertTrue(self.conteneur.InsertPage(self.p2.window, self.p2, 0))
        self.assertEqual(self.conteneur.GetPageCount(), 2)
        self.assertEqual(self.conteneur.GetIdxFromWindow('w2'), 0)

    def test_deplacement(self):
        self.conteneur.AddPage(self.p1.window, self.p1)
        self.conteneur.AddPage(self.p2.window, self.p2)
        self.assertTrue(self.conteneur.MovePage('w2', 0))
        self.assertEqual(self.conteneur.GetIdxFromWindow('w2'), 0)

    def test_hit_test(self):
        self.conteneur.AddPage(self.p1.window, self.p1)
        self.conteneur.AddPage(self.p2.window, self.p2)
        self.assertEqual(self.conteneur.TabHitTest(50, 15), 0)
        self.assertEqual(self.conteneur.TabHitTest(150, 15), 1)
        self.assertEqual(self.conteneur.TabHitTest(500, 15), -1)
        self.assertIsNotNone(self.conteneur.ButtonHitTest(0, 0, 0))

    def test_masquage_et_activation(self):
        self.conteneur.AddPage(self.p1.window, self.p1)
        self.conteneur.AddPage(self.p2.window, self.p2)
        self.conteneur.HideTab(0, True)
        self.assertTrue(self.conteneur.GetHidden(0))
        self.assertEqual(self.conteneur.GetShownPageCount(), 1)
        self.conteneur.SetActivePage(1)
        self.assertIs(self.conteneur.GetActivePage(), self.p2)
        self.conteneur.SetNoneActive()
        self.assertIsNone(self.conteneur.GetActivePage())

    def test_desactivation(self):
        self.conteneur.AddPage(self.p1.window, self.p1)
        self.conteneur.AddPage(self.p2.window, self.p2)
        self.conteneur.EnableTab(0, False)
        self.assertFalse(self.conteneur.GetEnabled(0))
        self.assertEqual(self.conteneur.FindNextActiveTab(-1), 1)

    def test_boutons(self):
        nombre = len(self.conteneur.CloneButtons())
        self.conteneur.RemoveButton(cst.AUI_BUTTON_LEFT)
        self.assertEqual(len(self.conteneur.CloneButtons()), nombre - 1)


@_gui
class TestControleOnglets(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkauibook_tabs
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibook_tabs
        self.ctrl = tkauibook_tabs.AuiTabCtrl(self.root)

    def test_page_et_rendu(self):
        page = _fausse_page('Onglet')
        page.window = 'w1'
        self.ctrl.AddPage(page.window, page)
        self.ctrl.OnPaint()  # ne doit pas lever d'exception
        self.assertEqual(self.ctrl.GetPageCount(), 1)


@_gui
class TestCarnet(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkauibook
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibook
        self.nb = tkauibook.AuiNotebook(self.root)

    def _pages(self):
        cadres = [self.tk.Frame(self.nb._page_area) for _ in range(3)]
        self.nb.AddPage(cadres[0], 'Premier', True)
        self.nb.AddPage(cadres[1], 'Deuxieme')
        self.nb.AddPage(cadres[2], 'Troisieme')
        return cadres

    def test_ajout(self):
        self._pages()
        self.assertEqual(self.nb.GetPageCount(), 3)
        self.assertEqual(self.nb.GetPageText(1), 'Deuxieme')

    def test_selection(self):
        cadres = self._pages()
        self.nb.SetSelection(2)
        self.assertEqual(self.nb.GetSelection(), 2)
        self.assertIs(self.nb.GetCurrentPage(), cadres[2])
        self.root.update_idletasks()
        self.assertEqual(cadres[0].winfo_manager(), '')
        self.assertEqual(cadres[2].winfo_manager(), 'pack')

    def test_avance(self):
        self._pages()
        self.nb.SetSelection(0)
        self.nb.AdvanceSelection(True)
        self.assertEqual(self.nb.GetSelection(), 1)
        self.nb.AdvanceSelection(True)
        self.assertEqual(self.nb.GetSelection(), 2)
        self.nb.AdvanceSelection(True)  # bouclage
        self.assertEqual(self.nb.GetSelection(), 0)

    def test_textes(self):
        self._pages()
        self.nb.SetPageText(1, 'Deuxieme bis')
        self.assertEqual(self.nb.GetPageText(1), 'Deuxieme bis')

    def test_masquage(self):
        self._pages()
        self.nb.HidePage(0, True)
        self.assertTrue(self.nb.GetHidden(0))
        self.assertEqual(self.nb.GetShownPageCount(), 2)
        self.nb.HidePage(0, False)
        self.assertFalse(self.nb.GetHidden(0))

    def test_index_et_item(self):
        cadres = self._pages()
        self.assertEqual(self.nb.GetPageIndex(cadres[1]), 1)
        self.assertIs(self.nb[0], cadres[0])

    def test_suppression(self):
        self._pages()
        self.nb.RemovePage(0)
        self.assertEqual(self.nb.GetPageCount(), 2)
        self.assertEqual(self.nb.GetPageText(0), 'Deuxieme')

    def test_conteneur(self):
        self._pages()
        self.root.update_idletasks()
        self.assertIsNotNone(self.nb.GetTabContainer())


@_gui
class TestAuxiliaires(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tkauibook_aux
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibook_aux
        self.aux = tkauibook_aux

    def test_page_info(self):
        page = self.aux.AuiNotebookPage()
        self.assertEqual(page.caption, '')
        self.assertTrue(page.enabled)
        self.assertFalse(page.hidden)
        self.assertFalse(page.IsMultiline())
        page.caption = 'ligne1\nligne2'
        self.assertTrue(page.IsMultiline())

    def test_evenements(self):
        evt = self.aux.AuiNotebookEvent()
        self.assertTrue(evt.IsAllowed())
        evt.Veto()
        self.assertFalse(evt.IsAllowed())
        evt.Allow()
        self.assertTrue(evt.IsAllowed())
        cmd = self.aux.CommandNotebookEvent()
        cmd.SetSelection(4)
        cmd.SetLabel('Libelle')
        self.assertEqual(cmd.GetSelection(), 4)
        self.assertEqual(cmd.GetLabel(), 'Libelle')

    def test_bouton_conteneur(self):
        bouton = self.aux.AuiTabContainerButton()
        self.assertEqual(bouton.cur_state, cst.AUI_BUTTON_STATE_NORMAL)
        self.assertEqual(bouton.id, -1)

    def test_navigateur(self):
        props = self.aux.TabNavigatorProps()
        self.assertEqual(props.selectedPage, -1)
        fenetre = self.aux.TabNavigatorWindow(self.root)
        fenetre.destroy()

    def test_edition_de_texte(self):
        # from taskcoachlib.guitk import tkauibook
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tkauibook
        nb = tkauibook.AuiNotebook(self.root)
        page = _fausse_page('Onglet')
        editeur = self.aux.TabTextCtrl(nb, page, 0)
        self.assertEqual(editeur.get(), 'Onglet')
        editeur.destroy()


@_gui
class TestSwitcher(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import aui_tk_switcherdialog
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import aui_tk_switcherdialog
        self.sw = aui_tk_switcherdialog
        self.items = self.sw.SwitcherItems()
        self.items.AddItem('Tache 1', 't1', 1)
        self.items.AddItem('Tache 2', 't2', 2)
        self.items.AddGroup('Groupe', 'g', 9)

    def test_comptage(self):
        self.assertEqual(self.items.GetItemCount(), 3)

    def test_recherche(self):
        self.assertEqual(self.items.FindItemByName('t1').GetTitle(), 'Tache 1')
        self.assertEqual(self.items.FindItemById(2).GetTitle(), 'Tache 2')
        self.assertIsNone(self.items.FindItemByName('inconnu'))

    def test_selection(self):
        self.items.SetSelection(1)
        self.assertEqual(self.items.GetSelection(), 1)
        self.items.SetSelectionByName('t2')
        self.assertEqual(self.items.GetSelection(), 1)

    def test_groupes(self):
        self.assertTrue(self.items.FindItemByName('g').GetIsGroup())
        self.assertFalse(self.items.FindItemByName('t1').GetIsGroup())

    def test_couleurs(self):
        self.items.SetSelectionColour('#ff0000')
        self.assertEqual(self.items.GetSelectionColour(), '#ff0000')

    def test_taille_element(self):
        taille = self.items.CalculateItemSize(self.tk.Canvas(self.root))
        self.assertEqual(len(taille), 2)
        self.assertGreater(taille[0], 0)

    def test_dialogue(self):
        dlg = self.sw.SwitcherDialog(self.items, self.root)
        self.assertEqual(dlg.GetSelection(), self.items.GetSelection())
        dlg.OnCloseWindow()


@_gui
class TestMDI(CasGraphique):

    def setUp(self):
        super().setUp()
        # from taskcoachlib.guitk import tktabmdi
        from taskcoachlib.thirdparty.tk3rdparty.aui_tk import tktabmdi
        self.module = tktabmdi
        self.parent = tktabmdi.AuiMDIParentFrame(self.root)

    def tearDown(self):
        try:
            self.parent.destroy()
        except Exception:
            pass
        super().tearDown()

    def test_enfant(self):
        enfant = self.module.AuiMDIChildFrame(self.parent, title='Document 1')
        self.assertEqual(enfant.GetTitle(), 'Document 1')
        self.assertEqual(self.parent.GetClientWindow().GetPageCount(), 1)

    def test_activation(self):
        premier = self.module.AuiMDIChildFrame(self.parent, title='Doc 1')
        second = self.module.AuiMDIChildFrame(self.parent, title='Doc 2')
        self.root.update_idletasks()
        self.assertIn(self.parent.ActivateNext(), (premier, second))

    def test_titre(self):
        enfant = self.module.AuiMDIChildFrame(self.parent, title='Doc')
        enfant.SetTitle('Nouveau titre')
        self.assertEqual(enfant.GetTitle(), 'Nouveau titre')


@_gui
class TestGestionnaire(CasGraphique):

    def setUp(self):
        super().setUp()
        self.mgr = fm.AuiManager(self.root)

    def tearDown(self):
        self.mgr.UnInit()
        super().tearDown()

    def _quatre_panneaux(self):
        gauche = self.tk.Frame(self.root)
        droite = self.tk.Frame(self.root)
        bas = self.tk.Frame(self.root)
        centre = self.tk.Frame(self.root)
        pa = self.mgr.AddPane(gauche, AuiPaneInfo().Caption('Arbre').Left().DefaultPane())
        pb = self.mgr.AddPane(droite, AuiPaneInfo().Caption('Details').Right().DefaultPane())
        pc = self.mgr.AddPane(bas, AuiPaneInfo().Caption('Apercu').Bottom().DefaultPane())
        pd = self.mgr.AddPane(centre, AuiPaneInfo().Caption('Centre').CenterPane())
        self.root.update_idletasks()
        return gauche, droite, bas, centre, pa, pb, pc, pd

    def test_amarrage_par_pack(self):
        gauche, droite, bas, centre, *_ = self._quatre_panneaux()
        for cadre in (gauche, droite, bas, centre):
            self.assertEqual(cadre.winfo_manager(), 'pack')

    def test_noms_derives(self):
        *_, pa, pb, pc, pd = self._quatre_panneaux()
        self.assertEqual([pa.name, pb.name, pc.name, pd.name],
                         ['Arbre', 'Details', 'Apercu', 'Centre'])

    def test_noms_uniques(self):
        self.mgr.AddPane(self.tk.Frame(self.root),
                         AuiPaneInfo().Caption('Arbre').Left().DefaultPane())
        second = self.mgr.AddPane(self.tk.Frame(self.root),
                                  AuiPaneInfo().Caption('Arbre').Left().DefaultPane())
        self.assertEqual(second.name, 'Arbre_1')

    def test_get_pane(self):
        gauche, droite, *_autres, pa, pb, _pc, _pd = self._quatre_panneaux()
        self.assertIs(self.mgr.GetPane('Arbre'), pa)
        self.assertIs(self.mgr.GetPane(droite), pb)
        self.assertFalse(self.mgr.GetPane('inconnu').IsOk())

    def test_show_pane(self):
        gauche, *_ = self._quatre_panneaux()
        self.mgr.ShowPane(gauche, False)
        self.root.update_idletasks()
        self.assertEqual(gauche.winfo_manager(), '')
        self.mgr.ShowPane(gauche, True)
        self.root.update_idletasks()
        self.assertEqual(gauche.winfo_manager(), 'pack')

    def test_perspective(self):
        self._quatre_panneaux()
        disposition = self.mgr.SavePerspective()
        autre = fm.AuiManager()
        try:
            self.assertTrue(autre.LoadPerspective(disposition))
            self.assertEqual(len(autre.GetAllPanes()), 4)
            self.assertEqual(autre.GetPane('Centre').caption, 'Centre')
        finally:
            autre.UnInit()

    def test_uninit(self):
        self._quatre_panneaux()
        self.mgr.UnInit()
        self.assertEqual(len(self.mgr.GetAllPanes()), 0)

    def test_flottant_wm_manage(self):
        gauche, *_ = self._quatre_panneaux()
        gauche.pack_forget()
        self.root.tk.call('wm', 'manage', gauche._w)
        self.root.tk.call('wm', 'geometry', gauche._w, '200x150+60+60')
        self.root.update_idletasks()
        geometrie = str(self.root.tk.call('wm', 'geometry', gauche._w))
        self.assertIn('200x150', geometrie)
        self.root.tk.call('wm', 'forget', gauche._w)
        self.mgr.Update()
        self.assertEqual(gauche.winfo_manager(), 'pack')

    def test_cadre_flottant(self):
        panneau = self.mgr.AddPane(self.tk.Frame(self.root),
                                   AuiPaneInfo().Caption('Flottant').Float()
                                   .FloatingPosition(40, 40))
        self.root.update_idletasks()
        self.assertIsNotNone(panneau.frame)
        self.assertEqual(panneau.frame.title(), 'Flottant')

    def test_gestionnaire_dcp(self):
        dcp = fm.AuiManager_DCP(self.root)
        try:
            dcp.AddPane(self.tk.Frame(self.root),
                        AuiPaneInfo().Caption('Cote').Left().DefaultPane())
            self.root.update_idletasks()
            self.root.update()
            self.assertTrue(dcp.hasDummyPane)
            self.assertTrue(dcp.GetPane('dummyCenterPane').IsOk())
        finally:
            dcp.UnInit()

    def test_evenement(self):
        panneau = self.mgr.AddPane(self.tk.Frame(self.root),
                                   AuiPaneInfo().Caption('X').Left().DefaultPane())
        evt = self.mgr.FireEvent('test', panneau)
        self.assertIs(evt.GetPane(), panneau)

    def test_contraintes(self):
        self.mgr.SetDockSizeConstraint(0.5, 0.5)
        self.assertEqual(self.mgr.GetDockSizeConstraint(), (0.5, 0.5))


# ---------------------------------------------------------------------------
# Demonstrateur : sequence automatique et glisser-deposer simule
# ---------------------------------------------------------------------------

@_gui
class TestDemoSequenceAuto(unittest.TestCase):
    """Valide la sequence automatique du demonstrateur, sans intervention."""

    def test_sequence_auto(self):
        from taskcoachlib.guitk import demotkaui
        application = None
        try:
            application = demotkaui.DemoTkAui(auto=False, duree=0)
            succes = application.executer_sequence_auto()
        finally:
            if application is not None:
                try:
                    application.mgr.UnInit()
                    application.root.destroy()
                except Exception:
                    pass
        self.assertTrue(succes, "la sequence automatique du demonstrateur a echoue")


@_gui
class TestGlisserDeposer(unittest.TestCase):
    """Simule un vrai glisser-deposer par evenements Tk sur le demonstrateur."""

    def setUp(self):
        from taskcoachlib.guitk import demotkaui
        self.demo = demotkaui.DemoTkAui(auto=False, duree=0)
        self.root = self.demo.root
        self.root.update()

    def tearDown(self):
        try:
            self.demo.mgr.UnInit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _generer(self, widget, sequence, x, y, racine_x, racine_y):
        # event_generate n'accepte pas x_root / y_root : on passe par
        # tk.call, ou -rootx / -rooty fixent event.x_root et event.y_root
        self.root.tk.call("event", "generate", widget._w, sequence,
                          "-x", x, "-y", y,
                          "-rootx", racine_x, "-rooty", racine_y)
        self.root.update()

    def _poignee(self):
        etiquette = getattr(self.demo.panneau_gauche, "_titre_label", None)
        self.assertIsNotNone(etiquette, "poignee (titre) du panneau gauche absente")
        self.root.update()
        return etiquette

    def test_glisser_vers_la_droite(self):
        demo = self.demo
        etiquette = self._poignee()
        # 1 : appui sur le titre, les cibles d'amarrage apparaissent
        self._generer(etiquette, "<ButtonPress-1>", 5, 5,
                      etiquette.winfo_rootx() + 5, etiquette.winfo_rooty() + 5)
        self.assertEqual(len(demo.zones), 3)
        self.assertIsNotNone(demo.zone_canvas)
        # 2 : glissement au-dessus de la cible "right", elle se colore
        ident = demo.zones["right"]
        x1, y1, x2, y2 = demo.zone_canvas.coords(ident)
        cible_x = int(demo.zone_canvas.winfo_rootx() + (x1 + x2) / 2)
        cible_y = int(demo.zone_canvas.winfo_rooty() + (y1 + y2) / 2)
        self._generer(etiquette, "<B1-Motion>", 30, 10, cible_x, cible_y)
        self.assertEqual(demo._cible_survollee(), "right")
        self.assertEqual(demo.zone_canvas.itemcget(ident, "fill"), "#a0c8ff")
        # 3 : relachement, le panneau est re-amarre a droite
        self._generer(etiquette, "<ButtonRelease-1>", 30, 10, cible_x, cible_y)
        self.assertEqual(demo.pa.dock_direction, cst.AUI_DOCK_RIGHT)
        self.assertEqual(demo.panneau_gauche.winfo_manager(), "pack")
        self.assertIsNone(demo.zone_canvas)

    def test_relachement_hors_cible(self):
        demo = self.demo
        etiquette = self._poignee()
        self._generer(etiquette, "<ButtonPress-1>", 5, 5,
                      etiquette.winfo_rootx() + 5, etiquette.winfo_rooty() + 5)
        # glissement loin des cibles, vers le bas de la fenetre
        loin_x = self.root.winfo_rootx() + 10
        loin_y = self.root.winfo_rooty() + 650
        self._generer(etiquette, "<B1-Motion>", 5, 5, loin_x, loin_y)
        self.assertIsNone(demo._cible_survollee())
        direction = demo.pa.dock_direction
        self._generer(etiquette, "<ButtonRelease-1>", 5, 5, loin_x, loin_y)
        self.assertEqual(demo.pa.dock_direction, direction)
        self.assertIsNone(demo.zone_canvas)

    def test_double_clic_flottant(self):
        demo = self.demo
        etiquette = self._poignee()
        rx = etiquette.winfo_rootx() + 5
        ry = etiquette.winfo_rooty() + 5
        # un double-clic ne peut pas etre genere directement (Tcl refuse
        # le modificateur Double) ; appui / relachement / appui le declenche
        self._generer(etiquette, "<ButtonPress-1>", 5, 5, rx, ry)
        self._generer(etiquette, "<ButtonRelease-1>", 5, 5, rx, ry)
        self._generer(etiquette, "<ButtonPress-1>", 5, 5, rx, ry)
        self.assertTrue(demo._flottant)
        geometrie = str(self.root.tk.call("wm", "geometry",
                                          demo.panneau_gauche._w))
        self.assertTrue(geometrie.startswith("240x180"))
        # retour dans la disposition : appel direct du gestionnaire, car la
        # machine a etats des double-clics de Tk ne se pilote pas deux fois
        # de suite par evenements synthetiques
        demo._sur_double_clic(None)
        self.assertFalse(demo._flottant)
        self.assertEqual(demo.panneau_gauche.winfo_manager(), "pack")


if __name__ == '__main__':
    unittest.main(verbosity=2)
