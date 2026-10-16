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
# from tkinter import ttk

try:
    from PIL import Image, ImageDraw, ImageGrab, ImageTk, ImageEnhance
except ImportError:  # PIL est nécessaire seulement pour les fonctions bitmap
    Image = ImageDraw = ImageGrab = ImageTk = ImageEnhance = None
from .aui_tk_constants import *


def _rgb(value):
    if isinstance(value, str):
        value = value.lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        return tuple(int(value[i: i + 2], 16) for i in (0, 2, 4))
    if hasattr(value, "Red"):
        return value.Red(), value.Green(), value.Blue()
    if isinstance(value, (tuple, list)):
        return tuple(value[:3])
    raise TypeError(f"Couleur non prise en charge: {value!r}")


def _colour(rgb):
    r, g, b = [max(0, min(255, int(x))) for x in rgb[:3]]
    return f"#{r:02x}{g:02x}{b:02x}"


def BlendColour(fg, bg, alpha):
    """
    Blends the two colour component `fg` and `bg` into one colour component, adding
    an optional alpha channel.

    :param `fg`: the first colour component;
    :param `bg`: the second colour component;
    :param integer `alpha`: an optional transparency value.
    """
    # result = bg + (alpha*(fg - bg))
    #
    # if result < 0.0:
    #     result = 0.0
    # if result > 255:
    #     result = 255
    #
    # return result
    return bg + alpha * (fg - bg)


def StepColour(c, ialpha):
    """
    Darken/lighten the input colour `c`.

    :param `c`: a colour to darken/lighten;
    :param integer `ialpha`: a transparency value.
    """

    if ialpha == 100:
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
    Creates a new, lighter colour based on the input colour `c`.

    :param `c`: the input colour to analyze.
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
    Chops the input `text` if its size does not fit in `max_size`, by cutting the
    text and adding ellipsis at the end.

    :param `dc`: a :class:`wx.DC` device context;
    :param string `text`: the text to chop;
    :param integer `max_size`: the maximum size in which the text should fit.
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
    measure = lambda s: dc.measure(s) if hasattr(dc, "measure") else dc.winfo_pixels(s)
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

    :param string `bits`: the raw bits of the bitmap;
    :param integer `w`: the bitmap width;
    :param integer `h`: the bitmap height;
    :param `colour`: the colour which will replace all white pixels in the
     raw bitmap.
    """
    # img = wx.Bitmap(bits, w, h).ConvertToImage()
    # img.Replace(0, 0, 0, 123, 123, 123)
    # img.Replace(255, 255, 255, colour.Red(), colour.Green(), colour.Blue())
    # img.SetMaskColour(123, 123, 123)
    # return wx.Bitmap(img)
    if Image is None:
        raise ImportError("Pillow est nécessaire pour BitmapFromBits")
    data = bytes(bits)
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = image.load()
    r, g, b = _rgb(colour)
    for y in range(h):
        for x in range(w):
            byte = data[(y * ((w + 7) // 8)) + x // 8]
            if byte & (1 << (x % 8)):
                pix[x, y] = (r, g, b, 255)
    return ImageTk.PhotoImage(image)


def IndentPressedBitmap(rect, button_state):
    """
    Indents the input rectangle `rect` based on the value of `button_state`.

    :param `rect`: the button bitmap rectangle;
    :param integer `button_state`: the button state.
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
        except tk.TclError:
            value = "#d9d9d9"
    else:
        value = "#d9d9d9"
    return StepColour(value, 92) if sum(255 - x for x in _rgb(value)) < 60 else value


def MakeDisabledBitmap(bitmap):
    """
    Convert the given image (in place) to a grayed-out version, appropriate for a 'disabled' appearance.

    :param `bitmap`: the bitmap to gray-out.
    """
    #
    # return bitmap.ConvertToDisabled()
    if Image is None:
        return bitmap
    image = bitmap.copy() if hasattr(bitmap, "copy") else bitmap
    return ImageEnhance.Color(image).enhance(0).convert("RGBA")


def Clip(a, b, c):
    """
    Clips the value in `a` based on the extremes `b` and `c`.

    :param `a`: the value to analyze;
    :param `b`: a minimum value;
    :param `c`: a maximum value.
    """
    #
    # return ((a < b and [b]) or [(a > c and [c] or [a])[0]])[0]
    return max(b, min(c, a))


def LightColour(colour, percent):
    """
    Brighten input `colour` by `percent`.

    :param `colour`: the colour to be brightened;
    :param integer `percent`: brightening percentage.
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
    factor = max(0, percent) / 100.0
    return _colour(
        (r + (255 - r) * factor, g + (255 - g) * factor, b + (255 - b) * factor)
    )


def PaneCreateStippleBitmap():
    """
    Creates a stipple bitmap to be used in a :class:`wx.Brush`.

    This is used to draw sash resize hints.
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
    Draws the wxMAC tab close button using :class:`GraphicsContext`.

    :param `colour`: the colour to use to draw the circle;
    :param `backColour`: the optional background colour for the circle.
    :param integer `size`: the size of the button.
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
    d.line(
        (4, 4, size - 6, size - 6), fill=_rgb(backColour or "white") + (255,), width=2
    )
    d.line(
        (4, size - 6, size - 6, 4), fill=_rgb(backColour or "white") + (255,), width=2
    )
    return image


def DarkenBitmap(bmp, caption_colour, new_colour):
    """
    Darkens the input bitmap on wxMAC using the input colour.

    :param `bmp`: the bitmap to be manipulated;
    :param `caption_colour`: the colour of the pane caption;
    :param `new_colour`: the colour used to darken the bitmap.
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
    image = bmp.convert("RGBA")
    px = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = px[x, y]
            px[x, y] = (
                int(r * cr / max(nr, 1)),
                int(g * cg / max(ng, 1)),
                int(b * cb / max(nb, 1)),
                a,
            )
    return image


def DrawGradientRectangle(
    dc, rect, start_colour, end_colour, direction, offset=0, length=0
):
    """
    Draws a gradient-shaded rectangle.

    :param `dc`: a :class:`tk.Canvas` device context;
    :param `rect`: the rectangle in which to draw the gradient;
    :param `start_colour`: the first colour of the gradient;
    :param `end_colour`: the second colour of the gradient;
    :param integer `direction`: the gradient direction (horizontal or vertical).
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
        if vertical:
            tk.Canvas.create_line(dc, x, y + i, x + w, y + i, fill=color)
        else:
            tk.Canvas.create_line(dc, x + i, y, x + i, y + h, fill=color)


def FindFocusDescendant(ancestor):
    """
    Find a window with the focus, that is also a descendant of the given window.
    This is used to determine the window to initially send commands to.

    :param `ancestor`: the window to check for ancestry.
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
        win = ancestor.focus_get()
    except tk.TclError:
        return None
    while win is not None:
        if win == ancestor:
            return win
        win = win.master
    return None


def GetLabelSize(dc, label, vertical):
    """
    Returns the :class:`~wx.lib.agw.aui.auibar.AuiToolBar` item label size.

    :param string `label`: the toolbar tool label;
    :param bool `vertical`: whether the toolbar tool orientation is vertical or not.
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
    width = dc.measure(label) if label.strip() else 0
    height = dc.metrics("linespace")
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

        :param `notebook`: an instance of :class:`AuiNotebook`;
        :param `page`: the dragged :class:`AuiNotebookPage` page;
        :param integer `button_state`: the state of the close button on the tab;
        :param `tabArt`: an instance of :class:`AuiDefaultTabArt` or one of its derivations.
        """
        #
        # self._backgroundColour = wx.Colour("pink")
        self._bitmap = self.CreateBitmap(notebook, page, button_state, tabArt)
        # wx.DragImage.__init__(self, self._bitmap)

    def CreateBitmap(self, notebook, page, button_state, tabArt):
        """
        Actually creates the drag and drop bitmap.

        :param `notebook`: an instance of :class:`AuiNotebook`;
        :param `page`: the dragged :class:`AuiNotebookPage` page;
        :param integer `button_state`: the state of the close button on the tab;
        :param `tabArt`: an instance of :class:`AuiDefaultTabArt` or one of its derivations.
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
        if hasattr(self._bitmap, "tk"):
            return self._bitmap

    def Hide(self):
        pass


def GetDockingImage(direction, useAero, center):
    """
    Returns the correct name of the docking bitmap depending on the input parameters.

    :param bool `useAero`: whether :class:`AuiManager` is using
     Aero-style or Whidbey-style docking images or not;
    :param bool `center`: whether we are looking for the center diamond-shaped bitmap or not.
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
    names = {
        AUI_DOCK_TOP: f"{prefix}up{suffix}",
        AUI_DOCK_BOTTOM: f"{prefix}down{suffix}",
        AUI_DOCK_LEFT: f"{prefix}left{suffix}",
        AUI_DOCK_RIGHT: f"{prefix}right{suffix}",
        None: f"{prefix}tab{suffix}",
    }
    name = names.get(direction, names[None])
    #
    # return bmp_unfocus, bmp_focus
    return globals().get(name), globals().get(name + "_focus")


def TakeScreenShot(rect):
    """
    Takes a screenshot of the screen at given position and size (`rect`).

    :param `rect`: the screen rectangle for which we want to take a screenshot.
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
        (rect.x, rect.y, rect.width, rect.height) if hasattr(rect, "x") else rect
    )
    return ImageGrab.grab((x, y, x + w, y + h))


def RescaleScreenShot(bmp, thumbnail_size=200):
    """
    Rescales a bitmap to be `thumbnail_size` pixels wide (or tall) at maximum.

    :param `bmp`: the bitmap to rescale;
    :param integer `thumbnail_size`: the maximum size of every page thumbnail.
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
    image = bmp.copy()
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

    :param `rect`: the :class:`AuiToolBar` tool screen rectangle;
    :param `size`: the pane window size;
    :param integer `direction`: the pane docking direction.
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
        (rect.x, rect.y, rect.width, rect.height) if hasattr(rect, "x") else rect
    )
    sx, sy = {
        AUI_DOCK_LEFT: (x + w + 2, y),
        AUI_DOCK_TOP: (x, y + h + 2),
        AUI_DOCK_RIGHT: (x - size[0] - 2, y),
        AUI_DOCK_BOTTOM: (x, y - size[1] - 2),
    }[direction]
    return sx, sy, size[0] + 4, size[0] + 4


def CopyAttributes(newArt, oldArt):
    """
    Copies pens, brushes, colours and fonts from the old tab art to the new one.

    :param `newArt`: the new instance of :class:``;
    :param `oldArt`: the old instance of :class:``.
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
