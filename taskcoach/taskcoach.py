#!/usr/bin/env python

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
# Programme principal
# importer les bibliothèques permettant l'interface pour le système d'exploitation
import os

# et les paramètres et les variables propres au système
import sys

# Workaround for a bug in Ubuntu 10.10
# autour d'un bug dans Ubuntu 10.10
# Fixe une variable d'environnement
os.environ["XLIB_SKIP_ARGB_VISUALS"] = "1"

# This prevents a message printed to the console when wx.lib.masked
# is imported from taskcoachlib.widgets on Ubuntu 12.04 64 bits...
# Cela prévient un message de la console quand wx.lib.masked
# est importé de taskcoachlib.widget sur Ubuntu 12.04 64bits

try:
    from mx import DateTime  # Essayer d'importer la Class DateTime,
except ImportError:
    pass  # si erreur ne rien faire


if not hasattr(sys, "frozen"):
    # These checks are only necessary in a non-frozen environment, i.e. we
    # skip these checks when run from a py2exe-fied application
    # ces vérifications sont seulement nécessaires dans un environnement non-frozen,
    # i.e. nous passons ces vérifications quand il tourne depuis une application py2exe.fied
    # wxpython: wxversion non integre sur python3 donc à ignorer :
    # remplacé par wx.__version__ donc ne plus importer wxversion.
    # https://docs.python.org/fr/3/howto/pyporting.html
    # try:
    #    # import wxversion  # in python 3 try with wx.__version__
    #    # from wx.core import __version__ as wxversion  # ?

    #    # wxversion.select(["2.8-unicode", "3.0"], optionsRequired=True)
    #    # __version__.select(["2.8-unicode", "3.0"], optionsRequired=True)
    # except ImportError:
    #    pass
    # except AttributeError:
    #    print(
    #        'wxversion.select(["2.8-unicode", "3.0"], optionsRequired=True) AttributeError: '
    #        "str object has no attribute select"
    #    )
    #    pass

    try:
        import taskcoachlib  # pylint: disable=W0611

        # d'apres https://diveintopython3.net/porting-code-to-python-3-with-2to3.html
    except ImportError:
        # On Ubuntu 12.04, taskcoachlib is installed in /usr/share/pyshared,
        # but that folder is not on the python path. Don't understand why.
        # We'll add it manually so the application can find it.
        # https://docs.python.org/fr/3.11/library/sys.html
        sys.path.insert(
            0, "/usr/share/pyshared"
        )  # ajoute à la variable d'environnement PYTHONPATH
        try:
            from . import taskcoachlib  # pylint: disable=W0611
        except ImportError:
            # si erreur écrire une erreur dans le log et sortir
            sys.stderr.write(
                """ERROR: cannot import the library 'taskcoachlib'.
Please see https://answers.launchpad.net/taskcoach/+faq/1063
for more information and possible resolutions.
ERREUR: Impossible d'importer la librairie 'taskcoachlib'.
Voir l'adresse pour plus d'information et de possibles résolution.
"""
            )
            sys.exit(1)  # quitte le programme suite à une erreur autre que syntaxe


def start():
    """Process command line options and start the application."""

    # pylint: disable=W0404
    from taskcoachlib import (
        config,
        application,
    )  # import des bibliothèques configurations-options et de l'application

    # méthode de vérification des définitions des variables options et args de config avec optparse :
    # options, args = config.ApplicationOptionParser().parse_args()
    # avec argparse :
    # La méthode exécute l'analyseur syntaxique et places les données extraites dans un objet argparse.Namespace
    # args = config.ApplicationArgumentParser().parse_args()
    # pour diviser en 2 parties
    # Parfois, un script n'analyse que quelques-uns des arguments de la ligne de commande
    # avant de passer les arguments non-traités à un autre script ou programme.
    # La méthode parse_known_args() est utile dans ces cas. Elle fonctionne similairement à parse_args(),
    # mais elle ne lève pas d'erreur quand des arguments non-reconnus sont présents.
    # Au lieu, elle renvoie une paire de valeurs : l'objet Namespace rempli et la liste des arguments non-traités.
    # options, args = config.ApplicationArgumentParser().parse_known_args()
    # voir aussi:
    # De nombreuses commandes Unix permettent à l'utilisateur
    # d'entremêler les arguments optionnels et les arguments positionnels.
    # Les méthodes parse_intermixed_args() et parse_known_intermixed_args() permettent ce style d'analyse.
    # Ces analyseurs ne prennent pas en charge toutes les fonctionnalités d'argparse et
    # généreront des exceptions si des fonctionnalités non prises en charge sont utilisées.
    # En particulier, les sous-analyseurs et les groupes mutuellement exclusifs
    # qui incluent à la fois des options et des positions ne sont pas pris en charge.
    tcoptions, args = config.ApplicationArgumentParser().parse_known_intermixed_args()
    # en utilisant l'astuce de The Namespace object dans https://docs.python.org/3.11/library/argparse.html
    options = vars(tcoptions)
    # print(options, args)
    app = application.Application(
        options, args
    )  # définition de la variable app comme application avec options et args
    # app = application.Application(tcargs)
    if options.profile:
        import cProfile

        cProfile.runctx("app.start()", globals(), locals(), filename=".profile")
    else:
        app.start()


if __name__ == "__main__":
    start()
