#!/usr/bin/env python

"""
Task Coach - Your friendly task manager
Copyright (C) 2021 Task Coach developers <developers@taskcoach.org>

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

**tctest.py**

Ce fichier Python fournit des classes de base et des utilitaires pour les tests unitaires
utilisés dans le projet `taskcoachlib`.

**Classes principales**

* `TestCase` : Classe de base pour les tests unitaires. Elle hérite de `unittest.TestCase` et
  fournit des fonctionnalités supplémentaires utiles pour les tests liés à l'interface graphique (GUI)
  utilisant la bibliothèque `wx`.
    * Fournit une instance unique de l'application wx (`wx.App`) accessible via la variable `app`.
    * Implémente la méthode `tearDown` pour effectuer des actions de nettoyage après chaque test,
      notamment la déconnexion des événements wx, la suppression des enregistrements d'observateurs
      de publication-abonnement (`pubsub`), et la réinitialisation des compteurs d'instances numérotées.
    * Fournit des méthodes utilitaires pour les tests :
        * `assertEqualLists` : Compare deux listes et vérifie si elles contiennent les mêmes éléments.
        * `registerObserver` : Enregistre l'objet de test en tant qu'observateur d'un type d'événement spécifique.
        * `onEvent` : Méthode appelée lorsque l'objet de test reçoit un événement.
* `TestCaseFrame` : Classe de base pour les tests unitaires nécessitant une fenêtre wxFrame simulée.
    * Fournit une fenêtre wxFrame simulée accessible via la variable `frame`.
    * Implémente des méthodes liées à la fenêtre simulée :
        * `getToolBarPerspective` : Méthode simulée pour récupérer la perspective de la barre d'outils.
        * `AddBalloonTip` : Méthode simulée pour ajouter une infobulle (tooltip).
* `wxTestCase` : Classe de base pour les tests unitaires spécifiques à l'interface wx.
    * Hérite de `TestCase` et initialise l'interface graphique wx à l'aide de `taskcoachlib.gui.init()`.
    * Implémente la méthode `tearDown` pour nettoyer les objets GDI Windows après chaque test.

**Fonctions utilitaires**

* `skipOnPlatform` : Décorateur pour les tests unitaires qui doivent être ignorés sur des plateformes spécifiques.
    * Permet de sauter des tests en fonction du système d'exploitation.

**Utilisation**

Les classes et fonctions de ce fichier sont utilisées pour créer des tests unitaires pour le projet `taskcoachlib`.
Les développeurs de tests héritent généralement de `TestCase` ou `wxTestCase` pour bénéficier des fonctionnalités
fournies et implémentent des méthodes de test individuelles pour vérifier le comportement attendu du code.
"""

import os
import sys
import unittest
import logging
import gettext
import platform

from pubsub import pub
import wx

gettext.NullTranslations().install()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from taskcoachlib import patterns


# TMP: compat to map wx platform strings
_PLATFORM_MAP = {
    "__WXGTK__": "Linux",
    }


def skipOnPlatform(*platforms):
    """ Décorateur pour les tests unitaires qui doivent être ignorés sur des plates-formes spécifiques.

    Args :
        *platforms (str) : Une liste de noms de plateformes à ignorer.

    Returns :
        function : Une fonction wrapper qui saute le test si la plateforme courante est dans la liste fournie.
    """
    def wrapper(func):
        if platform.system() in [_PLATFORM_MAP[name] for name in platforms]:
            # return lambda self, *args, **kwargs: self.skipTest("platform is %s" % wx.Platform)
            return lambda self, *args, **kwargs: self.skipTest(f"platform is {wx.Platform}")
        return func
    return wrapper


class TestCase(unittest.TestCase):
    # Some non-UI stuff also needs the app to be constructed (like
    # wx.BLACK et al)
    app = wx.App(0)

    def tearDown(self):
        self.app.Disconnect(wx.ID_ANY)

        patterns.Publisher().clear()
        patterns.NumberedInstances.count = dict()
        if hasattr(self, "events"):
            del self.events
        pub.unsubAll()
        super().tearDown()

    # Pourrais être remplacé par assertListEqual :
    def assertEqualLists(self, expectedList, actualList):
        self.assertEqual(len(expectedList), len(actualList))
        for item in expectedList:
            self.assertTrue(item in actualList)

    # def assertEqualLists(self, expectedList, actualList):
    #     self.assertListEqual(expectedList, actualList)

    def registerObserver(self, eventType, eventSource=None):
        if not hasattr(self, "events"):
            self.events = []  # pylint: disable=W0201
        patterns.Publisher().registerObserver(self.onEvent, eventType=eventType,
                                              eventSource=eventSource)

    def onEvent(self, event):
        self.events.append(event)


class TestCaseFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, "Frame")
        self.toolbarPerspective = ""

    def getToolBarPerspective(self):
        return self.toolbarPerspective

    def AddBalloonTip(self, *args, **kwargs):
        pass


class wxTestCase(TestCase):
    # pylint: disable=W0404
    frame = TestCaseFrame()
    from taskcoachlib import gui
    gui.init()

    def tearDown(self):
        super().tearDown()
        self.frame.DestroyChildren()  # Clean up GDI objects on Windows


def main():
    unittest.main()
