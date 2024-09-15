"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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

Sous-classe conçue pour surveiller les modifications des fichiers système de manière asynchrone
    grâce à l'utilisation des threads.

    Voici un résumé des fonctionnalités de cette classe :

    Elle hérite de la classe NotifierBase et est également un sous-classe de threading.Thread,
    ce qui lui permet de fonctionner comme un thread
    tout en bénéficiant des fonctionnalités de base fournies par NotifierBase.

    Elle utilise un verrou (threading.RLock) pour protéger les opérations sur les attributs partagés.

    Elle utilise un événement (threading.Event) pour signaler à la boucle de surveillance quand s'arrêter.

    La méthode run() est exécutée en boucle tant que la propriété cancelled est à False.
    À chaque itération, elle vérifie si le fichier surveillé a été modifié depuis la dernière vérification
    et déclenche la méthode onFileChanged() en conséquence.

    La méthode stop() est utilisée pour arrêter le thread. Elle définie la propriété cancelled à True,
    déclenche l'événement pour signaler à la boucle de s'arrêter, puis attend que le thread se termine avec self.join().

    La méthode saved() est utilisée pour mettre à jour le timestamp (self.stamp)
    lorsqu'un fichier surveillé est sauvegardé.

    La méthode onFileChanged() est destinée à être surchargée dans les sous-classes
    pour gérer les événements de modification de fichier.
"""

import os
import time
import threading
# from . import base
from taskcoachlib.filesystem import base


class FilesystemPollerNotifier(base.NotifierBase, threading.Thread):
    """
    Classe Notifier qui interroge le système de fichiers pour les modifications.

    Cette classe étend la classe de base `NotifierBase` et utilise le threading pour vérifier périodiquement
    si le fichier associé a été modifié. Si une modification est détectée, la méthode `onFileChanged`
    est appelée.

    Attributs :
        lock (threading.RLock) : Un verrou réentrant pour la sécurité des threads.
        cancelled (bool) : Indicateur indiquant si le notificateur a été annulé.
        evt (threading.Event) : un événement utilisé pour la synchronisation.
    """
    # la méthode stop() dans la classe FilesystemPollerNotifier est conçue
    # pour arrêter le thread en définissant self.cancelled sur True,
    # puis en appelant self.join() pour attendre que le thread se termine.
    # Cependant, le problème semble survenir lorsque self.join() est appelé.
    #  pour résoudre ce problème :
    #
    #     Utilisez un verrou pour éviter que stop() soit appelé pendant que le thread est déjà en cours d'arrêt.
    #     Vous pouvez utiliser un verrou pour empêcher que plusieurs appels à stop() ne se produisent simultanément.
    #
    #     Assurez-vous que self.join() est appelé après que self.cancelled a été défini sur True.
    #     Vous pouvez vérifier si self.cancelled est True avant d'appeler self.join().
    # Cela devrait aider à éviter les problèmes de verrouillage et de récursion lorsque vous appelez stop().
    # Il semble que le problème persiste malgré les modifications apportées.
    # L'erreur indique toujours un problème de récursion
    # lors de l'appel de self.join() dans la méthode stop() de la classe FilesystemPollerNotifier.
    #
    # Une possibilité est que la méthode stop() est appelée à plusieurs reprises,
    # ce qui entraîne une boucle de récursion infinie lors de l'appel de self.join().
    # Pour résoudre cela, vous pouvez ajouter une vérification pour
    # s'assurer que self.join() n'est appelé qu'une seule fois, même si stop() est appelé plusieurs fois.

    def __init__(self):
        super().__init__()

        self.lock = threading.RLock()
        self.cancelled = False
        self.evt = threading.Event()
        self.join_called = False
        # self.setDaemon(True)  # This method is deprecated, setDaemon() is deprecated, set the daemon attribute instead
        self.daemon = True  # du coup, j'ajoute ceci.
        self.start()

    def setFilename(self, filename):
        """
        Définissez le nom de fichier associé au notificateur.

        Args:
            filename (str) : Le nom de fichier à définir.
        """
        self.lock.acquire()
        try:
           super().setFilename(filename)
        finally:
           self.lock.release()
        # TODO: Essayer plutôt :
        # with self.lock:
        #    super().setFilename(filename)

    def run(self):
        """
        Exécutez le thread de notification.

        Cette méthode vérifie périodiquement si le fichier associé a été modifié.
        Si une modification est détectée, la méthode `onFileChanged` est appelée.
        """
        try:
            while not self.cancelled:
                self.lock.acquire()
                # with self.lock:  # sans try:
                try:
                    if self._filename and os.path.exists(self._filename):
                        stamp = os.stat(self._filename).st_mtime
                        if stamp > self.stamp:
                            self.stamp = stamp
                            self.onFileChanged()
                finally:
                    self.lock.release()

                self.evt.wait(10)
        except TypeError:
            pass

    def stop(self):
        """
        Arrêtez le notificateur.

        Cette méthode annule le thread du notificateur.
        """
        self.cancelled = True
        self.evt.set()
        # with self.lock:
        #    if not self.cancelled:
        #        self.cancelled = True
        #        self.evt.set()
        self.join()
        # if not self.join_called:
        #    self.join_called = True
        #    self.join()

    def saved(self):
        """
        Mettez à jour l'horodatage de modification en fonction du fichier.

        Cette méthode doit être appelée une fois le fichier enregistré.

        Note:
            Si le nom de fichier n'est pas défini ou si le fichier n'existe pas , l'horodatage est défini sur Aucun.
        """
        with self.lock:
            super().saved()

    def onFileChanged(self):
        """
        Gérer l'événement de modification de fichier.

        Cette méthode doit être remplacée par les sous-classes pour effectuer des actions spécifiques
        lorsque le fichier associé est modifié.
        """
        raise NotImplementedError
