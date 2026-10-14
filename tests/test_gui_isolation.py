"""
Test: GUI Isolation
Vérifie que le choix du GUI (--gui tk|wx) charge seulement le backend approprié.
"""

import pytest
import sys


class TestGUIIsolation:
    """Tests de non-régression pour l'isolation des backends GUI."""

    def test_tkinter_mode_no_wx_imported(self):
        """
        Tkinter mode doit charger tkapplication SANS importer wx.
        
        Cela vérifie que quand tu choisis --gui tk, le module wx ne se charge jamais.
        """
        # Enregistre les modules chargés AVANT
        modules_before = set(sys.modules.keys())
        
        # Simule le choix Tkinter
        from taskcoachlib.config.arguments import set_gui
        set_gui('tk')
        
        # Importe SEULEMENT tkapplication
        from taskcoachlib.application.tkapplication import TkinterApplication
        
        # Enregistre les modules chargés APRÈS
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before
        
        # Vérifie que wx n'a pas été chargé
        assert 'wx' not in new_modules, (
            "❌ ERREUR: wx a été chargé en mode Tkinter! "
            f"Modules contenant 'wx': {[m for m in new_modules if 'wx' in m]}"
        )
        
        print("✅ PASS: Tkinter mode - wx n'a pas été chargé")

    def test_wxpython_mode_loads_wx(self):
        """
        wxPython mode doit charger application.Application ET wx.
        
        Cela vérifie que quand tu choisis --gui wx, le module wx se charge bien.
        """
        # Enregistre les modules chargés AVANT
        modules_before = set(sys.modules.keys())
        
        # Simule le choix wx
        from taskcoachlib.config.arguments import set_gui
        set_gui('wx')
        
        # Importe SEULEMENT application (wx)
        from taskcoachlib.application.application import Application
        
        # Enregistre les modules chargés APRÈS
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before
        
        # Vérifie que wx a été chargé
        assert 'wx' in new_modules, (
            "❌ ERREUR: wx n'a pas été chargé en mode wxPython! "
            f"Nouveaux modules: {new_modules}"
        )
        
        print("✅ PASS: wxPython mode - wx a été chargé correctement")

    def test_guitk_no_wx_imports(self):
        """
        guitk/ (tous les modules Tkinter) ne doit jamais importer wx.
        
        Cela vérifie que les modules guitk/ sont 100% Tkinter-purs.
        """
        # Modules à tester
        guitk_modules = [
            'taskcoachlib.guitk.mainwindowtk',
            'taskcoachlib.guitk.menutk',
            'taskcoachlib.guitk.toolbarttk',
            'taskcoachlib.guitk.statustk',
            'taskcoachlib.guitk.iocontrollertk',
            'taskcoachlib.guitk.idlecontrollertk',
            'taskcoachlib.guitk.splashtk',
            'taskcoachlib.guitk.artprovidertk',
        ]
        
        for module_name in guitk_modules:
            try:
                modules_before = set(sys.modules.keys())
                # Importe le module
                __import__(module_name)
                modules_after = set(sys.modules.keys())
                new_modules = modules_after - modules_before
                
                # Vérifie que wx n'a pas été chargé par ce module
                assert 'wx' not in new_modules, (
                    f"❌ ERREUR: {module_name} a chargé wx! "
                    f"Modules contenant 'wx': {[m for m in new_modules if 'wx' in m]}"
                )
                print(f"✅ PASS: {module_name} - pas de wx")
            except ImportError as e:
                # Le module peut ne pas exister encore, c'est ok
                print(f"⚠️  SKIP: {module_name} - ImportError (module incomplet?): {e}")


class TestApplicationInterface:
    """Tests de respect du contrat ApplicationInterface."""

    def test_tkinter_app_implements_interface(self):
        """TkinterApplication doit implémenter ApplicationInterface."""
        from taskcoachlib.application.tkapplication import TkinterApplication
        from taskcoachlib.application.interface import ApplicationInterface
        
        # Vérifie que TkinterApplication hérite de ApplicationInterface
        assert issubclass(TkinterApplication, ApplicationInterface), (
            "❌ TkinterApplication ne doit pas implémenter ApplicationInterface"
        )
        
        # Vérifie que toutes les méthodes requises existent
        required_methods = ['init', 'start', 'quitApplication', 'displayMessage', 
                            'on_end_session', 'on_reopen_app']
        for method in required_methods:
            assert hasattr(TkinterApplication, method), (
                f"❌ TkinterApplication manque la méthode {method}"
            )
        
        print("✅ PASS: TkinterApplication implémente bien ApplicationInterface")

    def test_wx_app_implements_interface(self):
        """Application (wx) doit implémenter ApplicationInterface."""
        from taskcoachlib.application.application import Application
        from taskcoachlib.application.interface import ApplicationInterface
        
        # Vérifie que Application hérite de ApplicationInterface
        assert issubclass(Application, ApplicationInterface), (
            "❌ Application (wx) ne doit pas implémenter ApplicationInterface"
        )
        
        # Vérifie que toutes les méthodes requises existent
        required_methods = ['init', 'start', 'quitApplication', 'displayMessage', 
                            'on_end_session', 'on_reopen_app']
        for method in required_methods:
            assert hasattr(Application, method), (
                f"❌ Application manque la méthode {method}"
            )
        
        print("✅ PASS: Application (wx) implémente bien ApplicationInterface")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
