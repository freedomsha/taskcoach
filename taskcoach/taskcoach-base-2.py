# taskcoach.py (ou main.py)
#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importation de l'application Tkinter
from taskcoachlib.application.tkapplication import TkinterApplication


def main():
    try:
        app = TkinterApplication()
        app.run()
    except Exception as e:
        print(f"Erreur au démarrage : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
