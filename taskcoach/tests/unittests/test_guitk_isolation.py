# tests/test_gui_isolation.py
import pytest
import sys
import os


def test_tkinter_gui_no_wx():
    """Vérifie que mode Tkinter n'importe pas wx."""
    # Enregistre les modules chargés avant
    modules_before = set(sys.modules.keys())

    # Simule le choix Tkinter
    from taskcoachlib.config.arguments import set_gui
    set_gui('tk')

    # Importe SEULEMENT tkapplication
    from taskcoachlib.application.tkapplication import TkinterApplication

    # Vérifie que wx n'a pas été chargé
    modules_after = set(sys.modules.keys())
    new_modules = modules_after - modules_before

    # 'wx' ne doit pas être dans les nouveaux modules
    assert 'wx' not in new_modules, "wx a été chargé en mode Tkinter !"
    assert 'wxPython' not in new_modules, "wxPython a été chargé en mode Tkinter !"
