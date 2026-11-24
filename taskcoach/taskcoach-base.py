#!/usr/bin/env python3

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taskcoachlib.application.tkapplication_base_a import TkApplication


def main():
    app = TkApplication()
    app.run()


if __name__ == "__main__":
    main()
