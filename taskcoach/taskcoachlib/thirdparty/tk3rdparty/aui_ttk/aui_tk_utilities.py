"""
Utilitaires AUI adaptés à Tkinter.

Les fonctions de couleur et de mesure sont conservées. Les fonctions qui
produisaient des objets wxPython retournent maintenant des objets Tkinter/PIL
ou dessinent directement sur un Canvas Tkinter.

This module contains some common functions used by wxPython-AUI to
manipulate colours, bitmaps, text, gradient shadings and custom
dragging images for AuiNotebook tabs.
"""

# from __future__ import division
# from __future__ import absolute_import
# from __future__ import print_function
# from __future__ import unicode_literals
from __future__ import annotations

# from future import standard_library
# standard_library.install_aliases()
# from builtins import map
# from builtins import range
# from builtins import *
# from past.utils import old_div

__author__ = "Andrea Gavana <andrea.gavana@gmail.com>"
__date__ = "31 March 2009"


# import wx
import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageDraw, ImageGrab, ImageTk, ImageEnhance, ImageColor
except ImportError:  # PIL est nécessaire seulement pour les fonctions bitmap
    Image = ImageDraw = ImageGrab = ImageTk = ImageEnhance = ImageColor = None
from .aui_tk_constants import *


def _rgb(value):
    """
    Convert a color representation to an RGB tuple (red, green, blue).

    Supports hex strings (e.g. '#fff', '#ffffff'), color names (e.g. 'white'),
    wx.Colour-like objects (with Red(), Green(), Blue()), and RGB/RGBA tuples/lists.

    :param value: The color value to convert.
    :type value: str or tuple or list or wx.Colour
    :return: An (R, G, B) tuple with integer values in 0..255.
    :rtype: tuple[int, int, int]
    :raises TypeError: If the color type is unsupported or cannot be parsed.
    """
    if isinstance(value, str):
        v = value.strip()
        if v.startswith("#"):
            v = v.lstrip("#")
            if len(v) == 3:
                v = "".join(ch * 2 for ch in v)
            if len(v) == 6:
                try:
                    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
                except ValueError:
                    pass
        if ImageColor is not None:
            try:
                return ImageColor.getrgb(v)[:3]
            except ValueError:
                pass
        named_colors = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "gray": (128, 128, 128),
            "grey": (128, 128, 128),
            "lightgray": (211, 211, 211),
            "lightgrey": (211, 211, 211),
            "darkgray": (169, 169, 169),
            "darkgrey": (169, 169, 169),
        }
        if v.lower() in named_colors:
            return named_colors[v.lower()]
        try:
            root = getattr(tk, "_default_root", None)
            if root is not None:
                r, g, b = root.winfo_rgb(v)
                return r >> 8, g >> 8, b >> 8
        except (tk.TclError, AttributeError):
            pass
        if len(v) == 6:
            try:
                return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                pass
    red_fn = getattr(value, "Red", None)
    green_fn = getattr(value, "Green", None)
    blue_fn = getattr(value, "Blue", None)
    if callable(red_fn) and callable(green_fn) and callable(blue_fn):
        return red_fn(), green_fn(), blue_fn()
    if isinstance(value, (tuple, list)):
        return tuple(int(x) for x in value[:3])
    raise TypeError(f"Couleur non prise en charge: {value!r}")


def _colour(rgb):
    """
    Convert an RGB sequence into a hex color string.

    :param rgb: An iterable of at least 3 numeric color components (red, green, blue).
    :type rgb: tuple or list
    :return: A hex color string in the format '#rrggbb'.
    :rtype: str
    """
    r, g, b = [max(0, min(255, int(x))) for x in rgb[:3]]
    return f"#{r:02x}{g:02x}{b:02x}"


def BlendColour(fg, bg, alpha):
    """
    Blends the two colour component fg and bg into one colour component, adding
    an optional alpha channel.

    :param fg: The first colour component.
    :type fg: int or float
    :param bg: The second colour component.
    :type bg: int or float
    :param alpha: An optional transparency value.
    :type alpha: float
    :return: The blended colour component value.
    :rtype: float
    """
    # result = bg + (alpha*(fg - bg))
    #
    # if result < 0.0:
    #     result = 0.0
    # if result > 255:
    #     result = 255
    #
    # return result
    return max(0.0, min(255.0, bg + alpha * (fg - bg)))


def StepColour(c, ialpha):
    """
    Darken/lighten the input colour c.

    :param c: A colour to darken/lighten.
    :type c: str or tuple or list or wx.Colour
    :param ialpha: A transparency value (0 = black, 100 = unchanged, 200 = white).
    :type ialpha: int
    :return: The adjusted colour as a hex string.
    :rtype: str
    """

    if ialpha == 100 and isinstance(c, str) and c.startswith("#"):
        return c

    # r, g, b, a = c.Red(), c.Green(), c.Blue(), c.Alpha()
    r, g, b = _rgb(c)

    # ialpha is 0..200 where 0 is completely black
    # and 200 is completely white and 100 is the same
    # convert that to normal alpha 0.0 - 1.0
    # ialpha = min(ialpha, 200)
    # ialpha = max(ialpha, 0)
    ialpha = max(0, min(200, ialpha))
    alpha = (ialpha - 100.0) / 100.0

    # if ialpha > 100:
    #
    #     # blend with white
    #     bg = 255
    #     alpha = 1.0 - alpha  # 0 = transparent fg 1 = opaque fg
    #
    # else:
    #
    #     # blend with black
    #     bg = 0
    #     alpha = 1.0 + alpha  # 0 = transparent fg 1 = opaque fg
    bg = 255 if ialpha > 100 else 0
    alpha = 1.0 - alpha if ialpha > 100 else 1.0 + alpha

    # r = BlendColour(r, bg, alpha)
    # g = BlendColour(g, bg, alpha)
    # b = BlendColour(b, bg, alpha)
    #
    # return wx.Colour(int(r), int(g), int(b), int(a))
    return _colour(
        (
            BlendColour(r, bg, alpha),
            BlendColour(g, bg, alpha),
            BlendColour(b, bg, alpha),
        )
    )


def LightContrastColour(c):
    """
    Creates a new, lighter colour based on the input colour c.

    :param c: The input colour to analyze.
    :type c: str or tuple or list or wx.Colour
    :return: A lighter contrast colour as a hex string.
    :rtype: str
    """
    # amount = 120
    #
    # # if the colour is especially dark, then
    # # make the contrast even lighter
    # if c.Red() < 128 and c.Green() < 128 and c.Blue() < 128:
    #     amount = 160
    r, g, b = _rgb(c)

    # return StepColour(c, amount)
    return StepColour(c, 160 if r < 128 and g < 128 and b < 128 else 120)


def ChopText(dc, text, max_size):
    """
    Chops the input text if its size does not fit in max_size, by cutting the
    text and adding ellipsis at the end.

    :param dc: A device context, Canvas, or font used to measure text extent.
    :param str text: The text to chop.
    :param int max_size: The maximum size in which the text should fit.
    :return: The chopped text with ellipsis, or the original text.
    :rtype: str
    """

    # # first check if the text fits with no problems
    # x, y, dummy = dc.GetFullMultiLineTextExtent(text)
    #
    # if x <= max_size:
    #     return text
    #
    # textLen = len(text)
    # last_good_length = 0
    #
    # for i in range(textLen, -1, -1):
    #     s = text[0:i]
    #     s += "..."
    #
    #     x, y = dc.GetTextExtent(s)
    #     last_good_length = i
    #
    #     if x < max_size:
    #         break
    def measure(s):
        if hasattr(dc, "measure"):
            return dc.measure(s)
        if hasattr(dc, "GetTextExtent"):
            return dc.GetTextExtent(s)[0]
        f = getattr(dc, "font", getattr(dc, "_font", None))
        try:
            import tkinter.font as tkfont
            if f is not None:
                return tkfont.Font(font=f).measure(s)
            return tkfont.nametofont("TkDefaultFont").measure(s)
        except Exception:
            return len(s) * 8

    if measure(text) <= max_size:
        return text

    # ret = text[0:last_good_length] + "..."
    for i in range(len(text), -1, -1):
        if measure(text[:i] + "...") < max_size:
            return text[:i] + "..."
    # return ret
    return "..."


def BitmapFromBits(bits, w, h, colour):
    """
    A utility function that creates a masked bitmap from raw bits (XBM format).

    :param bits: The raw bits of the bitmap.
    :type bits: bytes or list[int] or str
    :param int w: The bitmap width.
    :param int h: The bitmap height.
    :param colour: The colour which will replace all set pixels in the raw bitmap.
    :type colour: str or tuple or list or wx.Colour
    :return: An ImageTk.PhotoImage or PIL.Image representing the bitmap.
    :rtype: ImageTk.PhotoImage or PIL.Image.Image
    """
    # img = wx.Bitmap(bits, w, h).ConvertToImage()
    # img.Replace(0, 0, 0, 123, 123, 123)
    # img.Replace(255, 255, 255, colour.Red(), colour.Green(), colour.Blue())
    # img.SetMaskColour(123, 123, 123)
    # return wx.Bitmap(img)
    if Image is None:
        raise ImportError("Pillow est nécessaire pour BitmapFromBits")
    data = bits.encode("latin1") if isinstance(bits, str) else bytes(bits)
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = image.load()
    r, g, b = _rgb(colour)
    for y in range(h):
        for x in range(w):
            byte = data[(y * ((w + 7) // 8)) + x // 8]
            if byte & (1 << (x % 8)):
                pix[x, y] = (r, g, b, 255)
    if ImageTk is not None:
        try:
            return ImageTk.PhotoImage(image)
        except (RuntimeError, tk.TclError, AttributeError):
            pass
    return image


def IndentPressedBitmap(rect, button_state):
    """
    Indents the input rectangle rect based on the value of button_state.

    :param rect: The button bitmap rectangle (object with x, y or sequence).
    :type rect: wx.Rect or tuple or list
    :param int button_state: The button state (e.g. AUI_BUTTON_STATE_PRESSED).
    :return: The indented rectangle.
    """
    # if button_state == AUI_BUTTON_STATE_PRESSED:
    #     rect.x += 1
    #     rect.y += 1
    #
    # return rect
    if button_state == AUI_BUTTON_STATE_PRESSED:
        if hasattr(rect, "x"):
            rect.x += 1
            rect.y += 1
        else:
            rect = (rect[0] + 1, rect[1] + 1, *rect[2:])
    return rect


def GetBaseColour(widget=None):
    """
    Returns the face shading colour on push buttons/backgrounds,
    mimicking as closely as possible the platform UI colours.

    :param widget: An optional Tkinter widget to inspect for background colour.
    :type widget: tkinter.Widget or None
    :return: A hex colour string representing the base face shading colour.
    :rtype: str
    """
    #
    # base_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
    #
    # # the base_colour is too pale to use as our base colour,
    # # so darken it a bit
    # if ((255-base_colour.Red()) +
    #     (255-base_colour.Green()) +
    #     (255-base_colour.Blue()) < 60):
    #
    #     base_colour = StepColour(base_colour, 92)
    #
    # return base_colour
    if widget is not None:
        try:
            value = widget.cget("background")
        except (tk.TclError, AttributeError):
            value = "#d9d9d9"
    elif tk._default_root is not None:
        try:
            value = tk._default_root.cget("background")
        except (tk.TclError, AttributeError):
            value = "#d9d9d9"
    else:
        value = "#d9d9d9"
    return StepColour(value, 92) if sum(255 - x for x in _rgb(value)) < 60 else value


def MakeDisabledBitmap(bitmap):
    """
    Convert the given image to a grayed-out version, appropriate for a 'disabled' appearance.

    :param bitmap: The bitmap or PIL Image to gray-out.
    :type bitmap: PIL.Image.Image or ImageTk.PhotoImage
    :return: A desaturated/grayed-out PIL Image.
    :rtype: PIL.Image.Image
    """
    #
    # return bitmap.ConvertToDisabled()
    if Image is None or ImageEnhance is None:
        return bitmap
    if hasattr(bitmap, "GetImage"):
        bitmap = bitmap.GetImage()
    elif hasattr(bitmap, "_image"):
        bitmap = bitmap._image
    if not hasattr(bitmap, "convert"):
        return bitmap
    image = bitmap.copy() if hasattr(bitmap, "copy") else bitmap
    return ImageEnhance.Color(image).enhance(0).convert("RGBA")


def Clip(a, b, c):
    """
    Clips the value in a based on the extremes b and c.

    :param a: The value to analyze.
    :type a: int or float
    :param b: A minimum value.
    :type b: int or float
    :param c: A maximum value.
    :type c: int or float
    :return: The clipped value between min(b, c) and max(b, c).
    :rtype: int or float
    """
    #
    # return ((a < b and [b]) or [(a > c and [c] or [a])[0]])[0]
    low, high = (b, c) if b <= c else (c, b)
    return max(low, min(high, a))


def LightColour(colour, percent):
    """
    Brighten input colour by percent.

    :param colour: The colour to be brightened.
    :type colour: str or tuple or list or wx.Colour
    :param percent: Brightening percentage (0 to 100).
    :type percent: int or float
    :return: The brightened colour as a hex string.
    :rtype: str
    """
    #
    # end_colour = wx.WHITE
    #
    # rd = end_colour.Red() - colour.Red()
    # gd = end_colour.Green() - colour.Green()
    # bd = end_colour.Blue() - colour.Blue()
    #
    # high = 100
    #
    # # We take the percent way of the colour from colour -. white
    # i = percent
    # r = colour.Red() + ((i*rd*100)/high)/100
    # g = colour.Green() + ((i*gd*100)/high)/100
    # b = colour.Blue() + ((i*bd*100)/high)/100
    # a = colour.Alpha()
    # return wx.Colour(int(r), int(g), int(b), int(a))
    r, g, b = _rgb(colour)
    factor = max(0.0, float(percent)) / 100.0
    return _colour(
        (r + (255 - r) * factor, g + (255 - g) * factor, b + (255 - b) * factor)
    )


def PaneCreateStippleBitmap():
    """
    Creates a stipple bitmap to be used for sash resize hints.

    :return: A 2x2 PIL Image containing the stipple pattern.
    :rtype: PIL.Image.Image
    """
    #
    # data = [0, 0, 0, 192, 192, 192, 192, 192, 192, 0, 0, 0]
    # img = wx.Image(2, 2)
    # counter = 0
    #
    # for ii in range(2):
    #     for jj in range(2):
    #         img.SetRGB(ii, jj, data[counter], data[counter+1], data[counter+2])
    #         counter = counter + 3
    #
    # return img.ConvertToBitmap()
    if Image is None:
        raise ImportError("Pillow est nécessaire pour PaneCreateStippleBitmap")
    return Image.frombytes(
        "RGB", (2, 2), bytes([0, 0, 0, 192, 192, 192, 192, 192, 192, 0, 0, 0])
    )


def DrawMACCloseButton(colour, backColour=None, size=16):
    """
    Draws the wxMAC tab close button using PIL.

    :param colour: The colour to use to draw the circle.
    :type colour: str or tuple or list or wx.Colour
    :param backColour: The optional background colour for the cross lines.
    :type backColour: str or tuple or list or wx.Colour or None
    :param int size: The size of the button in pixels (default 16).
    :return: A PIL Image containing the rendered close button.
    :rtype: PIL.Image.Image
    """
    #
    # bmp = wx.Bitmap.FromRGBA(16, 16)
    # dc = wx.MemoryDC()
    # dc.SelectObject(bmp)
    #
    # gc = wx.GraphicsContext.Create(dc)
    # gc.SetBrush(wx.Brush(colour))
    # path = gc.CreatePath()
    # path.AddCircle(6.5, 7, 6.5)
    # path.CloseSubpath()
    # gc.FillPath(path)
    #
    # path = gc.CreatePath()
    # if backColour is not None:
    #     pen = wx.Pen(backColour, 2)
    # else:
    #     pen = wx.Pen("white", 2)
    #
    # pen.SetCap(wx.CAP_BUTT)
    # pen.SetJoin(wx.JOIN_BEVEL)
    # gc.SetPen(pen)
    # path.MoveToPoint(3.5, 4)
    # path.AddLineToPoint(9.5, 10)
    # path.MoveToPoint(3.5, 10)
    # path.AddLineToPoint(9.5, 4)
    # path.CloseSubpath()
    # gc.DrawPath(path)
    #
    # dc.SelectObject(wx.NullBitmap)
    # return bmp
    if Image is None:
        raise ImportError("Pillow est nécessaire pour DrawMACCloseButton")
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.ellipse((1, 1, size - 2, size - 2), fill=_rgb(colour) + (255,))
    cross_colour = _rgb(backColour if backColour is not None else "white") + (255,)
    d.line(
        (4, 4, size - 6, size - 6), fill=cross_colour, width=2
    )
    d.line(
        (4, size - 6, size - 6, 4), fill=cross_colour, width=2
    )
    return image


def DarkenBitmap(bmp, caption_colour, new_colour):
    """
    Darkens the input bitmap using the input colour.

    :param bmp: The bitmap to be manipulated.
    :type bmp: PIL.Image.Image
    :param caption_colour: The colour of the pane caption.
    :type caption_colour: str or tuple or list or wx.Colour
    :param new_colour: The colour used to darken the bitmap.
    :type new_colour: str or tuple or list or wx.Colour
    :return: The darkened PIL Image.
    :rtype: PIL.Image.Image
    """
    #
    # image = bmp.ConvertToImage()
    # red = caption_colour.Red()/new_colour.Red()
    # green = caption_colour.Green()/new_colour.Green()
    # blue = caption_colour.Blue()/new_colour.Blue()
    # image = image.AdjustChannels(red, green, blue)
    # return image.ConvertToBitmap()
    if ImageEnhance is None:
        raise ImportError("Pillow est nécessaire pour DarkenBitmap")
    cr, cg, cb = _rgb(caption_colour)
    nr, ng, nb = _rgb(new_colour)
    if hasattr(bmp, "GetImage"):
        bmp = bmp.GetImage()
    elif hasattr(bmp, "_image"):
        bmp = bmp._image
    image = bmp.convert("RGBA")
    px = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = px[x, y]
            px[x, y] = (
                min(255, int(r * cr / max(nr, 1))),
                min(255, int(g * cg / max(ng, 1))),
                min(255, int(b * cb / max(nb, 1))),
                a,
            )
    return image


def DrawGradientRectangle(
    dc, rect, start_colour, end_colour, direction, offset=0, length=0
):
    """
    Draws a gradient-shaded rectangle.

    :param dc: A Tkinter Canvas (:class:`tkinter.Canvas`) or device context on which to draw.
    :type dc: tkinter.Canvas
    :param rect: The rectangle in which to draw the gradient (tuple (x, y, w, h) or object with x, y, width, height).
    :type rect: tuple or list or wx.Rect
    :param start_colour: The first colour of the gradient.
    :type start_colour: str or tuple or list or wx.Colour
    :param end_colour: The second colour of the gradient.
    :type end_colour: str or tuple or list or wx.Colour
    :param int direction: The gradient direction (AUI_GRADIENT_HORIZONTAL or AUI_GRADIENT_VERTICAL).
    :param int offset: Optional offset for the gradient drawing (default 0).
    :param int length: Optional length for the gradient drawing (default 0).
    """
    #
    # if direction == AUI_GRADIENT_VERTICAL:
    #     dc.GradientFillLinear(rect, start_colour, end_colour, wx.SOUTH)
    # else:
    #     dc.GradientFillLinear(rect, start_colour, end_colour, wx.EAST)
    x, y, w, h = (
        rect if not hasattr(rect, "x") else (rect.x, rect.y, rect.width, rect.height)
    )
    sr, sg, sb = _rgb(start_colour)
    er, eg, eb = _rgb(end_colour)
    vertical = direction == AUI_GRADIENT_VERTICAL
    count = h if vertical else w
    for i in range(max(1, count)):
        t = i / max(1, count - 1)
        color = _colour((sr + (er - sr) * t, sg + (eg - sg) * t, sb + (eb - sb) * t))
        if hasattr(dc, "create_line"):
            if vertical:
                dc.create_line(x, y + i, x + w, y + i, fill=color)
            else:
                dc.create_line(x + i, y, x + i, y + h, fill=color)
        else:
            if vertical:
                tk.Canvas.create_line(dc, x, y + i, x + w, y + i, fill=color)
            else:
                tk.Canvas.create_line(dc, x + i, y, x + i, y + h, fill=color)


def FindFocusDescendant(ancestor):
    """
    Find a window with the focus, that is also a descendant of the given window.
    This is used to determine the window to initially send commands to.

    :param ancestor: The window (:class:`tkinter.Misc` or :class:`tkinter.Widget`) to check for ancestry.
    :type ancestor: tkinter.Misc
    :return: The focused descendant window, or None if focus is not in ancestor.
    :rtype: tkinter.Widget or None
    """
    #
    # # Process events starting with the window with the focus, if any.
    # focusWin = wx.Window.FindFocus()
    # win = focusWin
    #
    # # Check if this is a descendant of this frame.
    # # If not, win will be set to NULL.
    # while win:
    #     if win == ancestor:
    #         break
    #     else:
    #         win = win.GetParent()
    #
    # if win is None:
    #     focusWin = None
    #
    # return focusWin
    try:
        focus_win = ancestor.focus_get()
    except (tk.TclError, AttributeError):
        return None
    win = focus_win
    while win is not None:
        if win == ancestor:
            return focus_win
        win = getattr(win, "master", None)
    return None


def GetLabelSize(dc, label, vertical):
    """
    Returns the :class:`~wx.lib.agw.aui.auibar.AuiToolBar` item label size.

    :param dc: A font (:class:`tkinter.font.Font`) or Canvas / DC used to measure text.
    :param str label: The toolbar tool label.
    :param bool vertical: Whether the toolbar tool orientation is vertical or not.
    :return: A tuple of (width, height) in pixels.
    :rtype: tuple[int, int]
    """
    #
    # text_width = text_height = 0
    #
    # # get the text height
    # dummy, text_height = dc.GetTextExtent("ABCDHgj")
    # # get the text width
    # if label.strip():
    #     text_width, dummy = dc.GetTextExtent(label)
    #
    # if vertical:
    #     tmp = text_height
    #     text_height = text_width
    #     text_width = tmp
    #
    # return wx.Size(text_width, text_height)
    if hasattr(dc, "measure"):
        width = dc.measure(label) if label.strip() else 0
        height = dc.metrics("linespace") if hasattr(dc, "metrics") else 16
    elif hasattr(dc, "GetTextExtent"):
        width, height = dc.GetTextExtent(label) if label.strip() else (0, 0)
    else:
        try:
            import tkinter.font as tkfont
            font = tkfont.nametofont("TkDefaultFont")
            width = font.measure(label) if label.strip() else 0
            height = font.metrics("linespace")
        except Exception:
            width = len(label) * 8 if label.strip() else 0
            height = 16
    return (height, width) if vertical else (width, height)


# ---------------------------------------------------------------------------
# TabDragImage implementation
# This class handles the creation of a custom image when dragging
# AuiNotebook tabs
# ---------------------------------------------------------------------------


# class TabDragImage(wx.DragImage):
class TabDragImage:
    """
    This class handles the creation of a custom image in case of drag and drop of a notebook tab.

    Gestionnaire minimal de l'image de glissement d'un onglet Tkinter.
    """

    def __init__(self, notebook, page, button_state, tabArt):
        """
        Default class constructor.

        For internal use: do not call it in your code!

        :param notebook: An instance of :class:`AuiNotebook`.
        :param page: The dragged :class:`AuiNotebookPage` page.
        :param int button_state: The state of the close button on the tab.
        :param tabArt: An instance of :class:`AuiDefaultTabArt` or one of its derivations.
        """
        #
        # self._backgroundColour = wx.Colour("pink")
        self._bitmap = self.CreateBitmap(notebook, page, button_state, tabArt)
        # wx.DragImage.__init__(self, self._bitmap)

    def CreateBitmap(self, notebook, page, button_state, tabArt):
        """
        Actually creates the drag and drop bitmap.

        :param notebook: An instance of :class:`AuiNotebook`.
        :param page: The dragged :class:`AuiNotebookPage` page.
        :param int button_state: The state of the close button on the tab.
        :param tabArt: An instance of :class:`AuiDefaultTabArt` or one of its derivations.
        :return: The created drag bitmap or PIL Image.
        """
        #
        # control = page.control
        # memory = wx.MemoryDC(wx.Bitmap(1, 1))
        #
        # tab_size, x_extent = tabArt.GetTabSize(memory, notebook, page.caption, page.bitmap, page.active,
        #                                        button_state, control)
        #
        # tab_width, tab_height = tab_size
        # rect = wx.Rect(0, 0, tab_width, tab_height)
        #
        # bitmap = wx.Bitmap(tab_width+1, tab_height+1)
        # memory.SelectObject(bitmap)
        #
        # if wx.Platform == "__WXMAC__":
        #     memory.SetBackground(wx.TRANSPARENT_BRUSH)
        # else:
        #     memory.SetBackground(wx.Brush(self._backgroundColour))
        #
        # memory.SetBackgroundMode(wx.TRANSPARENT)
        # memory.Clear()
        #
        # paint_control = wx.Platform != "__WXMAC__"
        # tabArt.DrawTab(memory, notebook, page, rect, button_state, paint_control=paint_control)
        #
        # memory.SetBrush(wx.TRANSPARENT_BRUSH)
        # memory.SetPen(wx.BLACK_PEN)
        # memory.DrawRoundedRectangle(0, 0, tab_width+1, tab_height+1, 2)
        #
        # memory.SelectObject(wx.NullBitmap)
        #
        # # Gtk and Windows unfortunately don't do so well with transparent
        # # drawing so this hack corrects the image to have a transparent
        # # background.
        # if wx.Platform != '__WXMAC__':
        #     timg = bitmap.ConvertToImage()
        #     if not timg.HasAlpha():
        #         timg.InitAlpha()
        #     ## for y in range(timg.GetHeight()):
        #     ##     for x in range(timg.GetWidth()):
        #     ##         pix = wx.Colour(timg.GetRed(x, y),
        #     ##                         timg.GetGreen(x, y),
        #     ##                         timg.GetBlue(x, y))
        #     ##         if pix == self._backgroundColour:
        #     ##             timg.SetAlpha(x, y, 0)
        #     # local opt list comprehension
        #     wxColour = wx.Colour
        #     GetRed = timg.GetRed
        #     GetGreen = timg.GetGreen
        #     GetBlue = timg.GetBlue
        #     SetAlpha = timg.SetAlpha
        #     _backgroundColour = self._backgroundColour
        #     [SetAlpha(x, y, 0)
        #         for x in range(timg.GetWidth())
        #             for y in range(timg.GetHeight())
        #                 if wxColour(GetRed(x, y), GetGreen(x, y), GetBlue(x, y)) == _backgroundColour]
        #     bitmap = timg.ConvertToBitmap()
        # return bitmap
        if hasattr(tabArt, "create_drag_image"):
            return tabArt.create_drag_image(notebook, page, button_state)
        return getattr(page, "bitmap", None)

    def Show(self, x, y):
        """
        Shows the drag image at the specified screen position.

        :param int x: The x coordinate on the screen.
        :param int y: The y coordinate on the screen.
        :return: The bitmap if available, or None.
        """
        if hasattr(self._bitmap, "tk"):
            return self._bitmap
        return None

    def Hide(self):
        """
        Hides the drag image.
        """
        pass


def GetDockingImage(direction, useAero, center):
    """
    Returns the correct name of the docking bitmap depending on the input parameters.

    :param int direction: The pane docking direction (e.g. AUI_DOCK_TOP, AUI_DOCK_LEFT, etc.).
    :param int useAero: Docking guide style (0 = default, 1 = Aero, 2 = Whidbey).
    :param bool center: Whether we are looking for the center diamond-shaped bitmap or not.
    :return: A tuple (bmp_unfocus, bmp_focus) containing the unfocused and focused bitmaps.
    :rtype: tuple
    """

    # suffix = (center and [""] or ["_single"])[0]
    suffix = "" if center else "_single"
    # prefix = ""
    # if useAero == 2:
    #     # Whidbey docking guides
    #     prefix = "whidbey_"
    # elif useAero == 1:
    #     # Aero docking style
    #     prefix = "aero_"
    prefix = {2: "whidbey_", 1: "aero_"}.get(useAero, "")

    # if direction == wx.TOP:
    #     bmp_unfocus = eval("%sup%s"%(prefix, suffix)).GetBitmap()
    #     bmp_focus = eval("%sup_focus%s"%(prefix, suffix)).GetBitmap()
    # elif direction == wx.BOTTOM:
    #     bmp_unfocus = eval("%sdown%s"%(prefix, suffix)).GetBitmap()
    #     bmp_focus = eval("%sdown_focus%s"%(prefix, suffix)).GetBitmap()
    # elif direction == wx.LEFT:
    #     bmp_unfocus = eval("%sleft%s"%(prefix, suffix)).GetBitmap()
    #     bmp_focus = eval("%sleft_focus%s"%(prefix, suffix)).GetBitmap()
    # elif direction == wx.RIGHT:
    #     bmp_unfocus = eval("%sright%s"%(prefix, suffix)).GetBitmap()
    #     bmp_focus = eval("%sright_focus%s"%(prefix, suffix)).GetBitmap()
    # else:
    #     bmp_unfocus = eval("%stab%s"%(prefix, suffix)).GetBitmap()
    #     bmp_focus = eval("%stab_focus%s"%(prefix, suffix)).GetBitmap()
    base_names = {
        AUI_DOCK_TOP: "up",
        AUI_DOCK_BOTTOM: "down",
        AUI_DOCK_LEFT: "left",
        AUI_DOCK_RIGHT: "right",
    }
    base = base_names.get(direction, "tab")
    name = f"{prefix}{base}{suffix}"
    focus_name = f"{prefix}{base}_focus{suffix}"
    #
    # return bmp_unfocus, bmp_focus
    return globals().get(name), globals().get(focus_name)


def TakeScreenShot(rect):
    """
    Takes a screenshot of the screen at given position and size (rect).

    :param rect: The screen rectangle for which we want to take a screenshot (object with x, y, width, height or sequence).
    :type rect: tuple or list or wx.Rect
    :return: A PIL Image containing the screenshot.
    :rtype: PIL.Image.Image
    """
    #
    # # Create a DC for the whole screen area
    # dcScreen = wx.ScreenDC()
    #
    # # Create a Bitmap that will later on hold the screenshot image
    # # Note that the Bitmap must have a size big enough to hold the screenshot
    # # -1 means using the current default colour depth
    # bmp = wx.Bitmap(rect.width, rect.height)
    #
    # # Create a memory DC that will be used for actually taking the screenshot
    # memDC = wx.MemoryDC()
    #
    # # Tell the memory DC to use our Bitmap
    # # all drawing action on the memory DC will go to the Bitmap now
    # memDC.SelectObject(bmp)
    #
    # # Blit (in this case copy) the actual screen on the memory DC
    # # and thus the Bitmap
    # memDC.Blit( 0,            # Copy to this X coordinate
    #             0,            # Copy to this Y coordinate
    #             rect.width,   # Copy this width
    #             rect.height,  # Copy this height
    #             dcScreen,     # From where do we copy?
    #             rect.x,       # What's the X offset in the original DC?
    #             rect.y        # What's the Y offset in the original DC?
    #             )
    #
    # # Select the Bitmap out of the memory DC by selecting a new
    # # uninitialized Bitmap
    # memDC.SelectObject(wx.NullBitmap)
    #
    # return bmp
    if ImageGrab is None:
        raise ImportError("Pillow est nécessaire pour TakeScreenShot")
    x, y, w, h = (
        (rect.x, rect.y, rect.width, rect.height) if hasattr(rect, "x") else tuple(rect[:4])
    )
    return ImageGrab.grab((x, y, x + w, y + h))


def RescaleScreenShot(bmp, thumbnail_size=200):
    """
    Rescales a bitmap to be thumbnail_size pixels wide (or tall) at maximum.

    :param bmp: The bitmap or PIL Image to rescale.
    :type bmp: PIL.Image.Image
    :param int thumbnail_size: The maximum size of every page thumbnail (default 200).
    :return: A PIL Image rescaled with a drop shadow border.
    :rtype: PIL.Image.Image
    """
    #
    # bmpW, bmpH = bmp.GetWidth(), bmp.GetHeight()
    # img = bmp.ConvertToImage()
    #
    # newW, newH = bmpW, bmpH
    #
    # if bmpW > bmpH:
    #     if bmpW > thumbnail_size:
    #         ratio = bmpW/thumbnail_size
    #         newW, newH = int(bmpW//ratio), int(bmpH//ratio)
    #         img.Rescale(newW, newH, wx.IMAGE_QUALITY_HIGH)
    # else:
    #     if bmpH > thumbnail_size:
    #         ratio = bmpH/thumbnail_size
    #         newW, newH = int(bmpW//ratio), int(bmpH//ratio)
    #         img.Rescale(newW, newH, wx.IMAGE_QUALITY_HIGH)
    #
    # newBmp = img.ConvertToBitmap()
    # otherBmp = wx.Bitmap(newW+5, newH+5)
    #
    # memDC = wx.MemoryDC()
    # memDC.SelectObject(otherBmp)
    # memDC.SetBackground(wx.WHITE_BRUSH)
    # memDC.Clear()
    #
    # memDC.SetPen(wx.TRANSPARENT_PEN)
    #
    # pos = 0
    # for i in range(5, 0, -1):
    #     brush = wx.Brush(wx.Colour(50*i, 50*i, 50*i))
    #     memDC.SetBrush(brush)
    #     memDC.DrawRoundedRectangle(0, 0, newW+5-pos, newH+5-pos, 2)
    #     pos += 1
    #
    # memDC.DrawBitmap(newBmp, 0, 0, True)
    #
    # # Select the Bitmap out of the memory DC by selecting a new
    # # uninitialized Bitmap
    # memDC.SelectObject(wx.NullBitmap)
    #
    # return otherBmp
    if Image is None:
        raise ImportError("Pillow est nécessaire pour RescaleScreenShot")
    if hasattr(bmp, "GetImage"):
        bmp = bmp.GetImage()
    elif hasattr(bmp, "_image"):
        bmp = bmp._image
    image = bmp.copy() if hasattr(bmp, "copy") else bmp
    image.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (image.width + 5, image.height + 5), "white")
    d = ImageDraw.Draw(out)
    for i in range(5, 0, -1):
        d.rounded_rectangle(
            (0, 0, image.width + 5 - i, image.height + 5 - i),
            radius=2,
            fill=(50 * i,) * 3,
        )
    out.paste(image, (0, 0), image if image.mode == "RGBA" else None)
    return out


def GetSlidingPoints(rect, size, direction):
    """
    Returns the point at which the sliding in and out of a minimized pane begins.

    :param rect: The :class:`AuiToolBar` tool screen rectangle (tuple or object with x, y, width, height).
    :type rect: tuple or list or wx.Rect
    :param size: The pane window size (tuple (w, h) or size object).
    :type size: tuple or list or wx.Size
    :param int direction: The pane docking direction.
    :return: A tuple of (startX, startY, stopX, stopY).
    :rtype: tuple[int, int, int, int]
    """
    #
    # if direction == AUI_DOCK_LEFT:
    #     startX, startY = rect.x + rect.width + 2, rect.y
    # elif direction == AUI_DOCK_TOP:
    #     startX, startY = rect.x, rect.y + rect.height + 2
    # elif direction == AUI_DOCK_RIGHT:
    #     startX, startY = rect.x - size.x - 2, rect.y
    # elif direction == AUI_DOCK_BOTTOM:
    #     startX, startY = rect.x, rect.y - size.y - 2
    # else:
    #     raise Exception("How did we get here?")
    #
    # caption_height = wx.SystemSettings.GetMetric(wx.SYS_CAPTION_Y)
    # frame_border_x = wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_X)
    # frame_border_y = wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_Y)
    #
    # stopX = size.x + caption_height + frame_border_x
    # stopY = size.x + frame_border_y
    #
    # return startX, startY, stopX, stopY
    x, y, w, h = (
        (rect.x, rect.y, rect.width, rect.height) if hasattr(rect, "x") else tuple(rect[:4])
    )
    size_w = size.x if hasattr(size, "x") else (size.width if hasattr(size, "width") else size[0])
    size_h = size.y if hasattr(size, "y") else (size.height if hasattr(size, "height") else size[1])
    coords = {
        AUI_DOCK_LEFT: (x + w + 2, y),
        AUI_DOCK_TOP: (x, y + h + 2),
        AUI_DOCK_RIGHT: (x - size_w - 2, y),
        AUI_DOCK_BOTTOM: (x, y - size_h - 2),
    }
    if direction not in coords:
        raise ValueError(f"Direction de dock invalide: {direction}")
    sx, sy = coords[direction]
    return sx, sy, size_w + 4, size_h + 4


def CopyAttributes(newArt, oldArt):
    """
    Copies pens, brushes, colours and fonts from the old tab art to the new one.

    :param newArt: The new tab art instance (e.g. :class:`AuiDefaultTabArt`).
    :param oldArt: The old tab art instance to copy attributes from.
    :return: The new tab art instance with copied attributes.
    """
    # :param `newArt`: the new instance of :class:`~wx.lib.agw.aui.tabart.AuiDefaultTabArt`;
    # :param `oldArt`: the old instance of :class:`~wx.lib.agw.aui.tabart.AuiDefaultTabArt`.
    #
    #
    # attrs = dir(oldArt)
    #
    # for attr in attrs:
    #     if attr.startswith("_") and (attr.endswith("_colour") or attr.endswith("_font") or \
    #                                  attr.endswith("_font") or attr.endswith("_brush") or \
    #                                  attr.endswith("Pen") or attr.endswith("_pen")):
    #         setattr(newArt, attr, getattr(oldArt, attr))
    #
    # return newArt
    for attr in dir(oldArt):
        if attr.startswith("_") and any(
            attr.endswith(s) for s in ("_colour", "_font", "_brush", "Pen", "_pen")
        ):
            setattr(newArt, attr, getattr(oldArt, attr))
    return newArt
