"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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

# from __future__ import division

# from builtins import object
# from past.utils import old_div
from tkinter import font as tkfont


class FontMixer(object):
    """Mélange plusieurs polices Tkinter.

    Les objets attendus sont des ``tkinter.font.Font`` ou des objets exposant
    l'API Tkinter équivalente (``actual()``). Le résultat est une nouvelle
    police Tkinter, indépendante des polices sources.
    """

    @staticmethod
    def _actual(font):
        if isinstance(font, tkfont.Font):
            return font.actual()
        actual = getattr(font, "actual", None)
        if callable(actual):
            return actual()
        if isinstance(font, dict):
            return font
        if isinstance(font, (tuple, list)):
            # Format Tk classique : (family, size, slant, weight, underline,
            # overstrike). Il est accepté pour rester compatible avec les
            # valeurs provenant de winfo_font().
            values = list(font) + [None] * 6
            return {
                "family": values[0], "size": values[1], "slant": values[2],
                "weight": values[3], "underline": values[4],
                "overstrike": values[5],
            }
        raise TypeError("La police doit être une police Tkinter ou une description Tk")

    @classmethod
    def mix(cls, *fonts):
        fonts = [font for font in fonts if font]
        if not fonts:
            return None
        if len(fonts) == 1:
            return fonts[0]
        return tkfont.Font(
            size=int(cls.mixFontSizes(*fonts)),
            family=cls.mixFontFamilies(*fonts),
            slant=cls.mixFontStyles(*fonts),
            weight=cls.mixFontWeights(*fonts),
            underline=cls.mixFontUnderlining(*fonts),
        )

    @classmethod
    def mixFontSizes(cls, *fonts):
        return sum(abs(int(cls._actual(font)["size"])) for font in fonts) / len(fonts)

    @classmethod
    def mixFontFamilies(cls, *fonts):
        families = [cls._actual(font).get("family") for font in fonts]
        counts = {}
        for family in families:
            if family:
                counts[family] = counts.get(family, 0) + 1
        if not counts:
            return "TkDefaultFont"
        # En cas d'égalité, conserver la première famille rencontrée.
        return max(counts, key=lambda family: counts[family])

    @classmethod
    def mixFontWeights(cls, *fonts):
        # Or tkinter.font.Font(weight=...) accepte notamment "normal" et "bold", mais pas "light".
        weights = [str(cls._actual(font).get("weight", "normal")).lower() for font in fonts]
        bold = weights.count("bold")
        normal = weights.count("normal")
        if bold > normal:
            return "bold"
        if normal > bold:
            return "normal"
        return "normal"

    @classmethod
    def mixFontStyles(cls, *fonts):
        return "italic" if any(
            str(cls._actual(font).get("slant", "roman")).lower() == "italic"
            for font in fonts
        ) else "roman"

    @classmethod
    def mixFontUnderlining(cls, *fonts):
        return any(bool(cls._actual(font).get("underline", False)) for font in fonts)
