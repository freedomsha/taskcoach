# test_no_wx_in_tk_mode.py
import sys
import os

# Assure que wx ne s'importe pas quand on choisit Tkinter
sys.modules['wx'] = None  # Bloque wx si quelqu'un essaie de l'importer

os.environ['TASKCOACH_GUI'] = 'tk'

from taskcoachlib.config.arguments import set_gui
set_gui('tk')

try:
    from taskcoachlib.application.tkapplication import TkinterApplication
    print("✅ TkinterApplication importée sans charger wx")
except Exception as e:
    print(f"❌ ERREUR : {e}")
    sys.exit(1)

# Vérifie que wx.* n'a pas été chargé
if 'wx' in sys.modules and sys.modules['wx'] is not None:
    print("❌ ERREUR : wx a été chargé même en mode Tkinter !")
    sys.exit(1)

print("✅ Aucun module wx n'a été chargé en mode Tkinter")