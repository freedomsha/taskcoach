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

Ce fichier gère le modèle de données central :
les tâches, efforts, catégories, notes, etc.
Il est également responsable de la gestion des événements, de la persistence,
de la synchronisation, et de la sécurité des écritures.

Donc c'est un fichier critique à bien logger :
tout plantage ici impacte la sauvegarde, le chargement, les notifs, etc.
"""

# import lockfile
import logging
import os
import tempfile
from io import TextIOWrapper
import wx
from pubsub import pub

from . import xml
from taskcoachlib import patterns, operating_system
from taskcoachlib.domain import base, task, category, note, effort, attachment
from taskcoachlib.syncml.config import createDefaultSyncConfig
from taskcoachlib.thirdparty.guid import generate
from taskcoachlib.thirdparty import lockfile
from taskcoachlib.changes import ChangeMonitor, ChangeSynchronizer
from taskcoachlib.filesystem import (
    FilesystemNotifier,
    FilesystemPollerNotifier,
)

log = logging.getLogger(__name__)


def _isCloud(path):
    """
    Vérifiez si un chemin donné se trouve dans un répertoire synchronisé avec le cloud.

    Args :
        path (str) : Le chemin du fichier à vérifier.

    Returns :
        (bool) : Vrai si le chemin se trouve dans un répertoire synchronisé avec le cloud, sinon False.
    """
    path = os.path.abspath(path)
    while True:
        for name in [".dropbox.cache", ".csync_journal.db"]:
            if os.path.exists(os.path.join(path, name)):
                return True
        path, name = os.path.split(path)
        if name == "":
            return False


class TaskCoachFilesystemNotifier(FilesystemNotifier):
    """
    Une classe de notification pour gérer les modifications de fichiers pour Task Coach.
    """

    def __init__(self, taskFile):
        """
        Initialiser le notificateur avec une instance de TaskFile.

        Initialise un notificateur de changement de fichier spécifique à Task Coach,
        en liant un objet TaskFile à surveiller pour détecter les modifications sur le disque.

        Args :
            taskFile (TaskFile) : l'instance de TaskFile à notifier.
        """
        self.__taskFile = taskFile
        # super(TaskCoachFilesystemNotifier, self).__init__()
        super().__init__()

    def onFileChanged(self):
        """
        Gérez les modifications de fichiers en notifiant l’instance TaskFile associée.
        """
        self.__taskFile.onFileChanged()
        log.info("TaskCoachFileSystemNotifier.onFileChanges : Modification détectée sur le fichier '%s'", self.__taskFile)


class TaskCoachFilesystemPollerNotifier(FilesystemPollerNotifier):
    """
    Une classe de notification d'interrogation pour gérer les modifications de fichiers pour Task Coach.
    """

    def __init__(self, taskFile):
        """
        Initialiser le notificateur d'interrogation avec une instance de TaskFile.

        Initialise un notificateur de changement de fichier spécifique à Task Coach,
        en liant un objet TaskFile à surveiller pour détecter les modifications sur disque.

        Args :
            taskFile (TaskFile) : L'instance de TaskFile à notifier.
        """
        self.__taskFile = taskFile
        # super(TaskCoachFilesystemPollerNotifier, self).__init__()
        super().__init__()

    def onFileChanged(self):
        """
        Gérez les modifications de fichiers en notifiant l’instance TaskFile associée.
        """
        self.__taskFile.onFileChanged()


class SafeWriteFile(object):
    # class SafeWriteFile(metaclass=open):  # Pourquoi pas ?
    """
    Une classe pour écrire des fichiers en toute sécurité,
    en utilisant des fichiers temporaires pour éviter la perte de données.
    """

    def __init__(self, filename):
        """
        Initialisez le SafeWriteFile avec un nom de fichier.

        Args :
            filename (str) : Le nom de fichier dans lequel écrire.
        """
        # Si le fichier est destiné à contenir du XML (qui est un format textuel),
        # il est généralement préférable de l'écrire en mode texte avec
        # un encodage spécifique comme UTF-8.
        # Si vous ouvrez le fichier en mode binaire pour l'écriture ('wb'),
        # vous devrez encoder explicitement la chaîne XML en bytes
        # avant de l'écrire (par exemple, tree.write(self.__fd, encoding="utf-8")
        # suivi d'un appel à .encode('utf-8') si tree.write attend un flux binaire).
        log.info("Initialisation de SafeWriteFile avec un nom de fichier.")
        self.__filename = filename
        if self._isCloud():
            # Ideally we should create a temporary file on the same filesystem (so that
            # os.rename works) but outside the Dropbox folder...
            self.__fd = open(self.__filename, "wb")
            # self.__fd = open(self.__filename, "w")
            # self.__tempFilename = ?
        else:
            self.__tempFilename = self._getTemporaryFileName(
                os.path.dirname(filename)
            )
            # self.__fd = open(self.__tempFilename, "wb")
            self.__fd = open(file=self.__tempFilename, mode="wb", encoding="utf-8")
        # self.__fd = filename
        log.info("Initialisation de SafeWriteFile avec un nom de fichier."
                 f"self.__filename={self.__filename}"
                 f"self.__fd={self.__fd}"
                 f"self.__tempFilename={self.__tempFilename}")

    def write(self, bf):
        """
        Écrivez les données dans le fichier.

        Args :
            bf (str) : Les données à écrire.
        """
        log.info(f"SafeWriteFile.write essaie d'écrire {bf} dans {self.__fd}.")

        if isinstance(bf, str):
            self.__fd.write(bf)  # comment transformer bf(bytes) en string ?
        else:
            self.__fd.write(str(bf))

    def close(self):
        """
        Fermez le fichier et renommez le fichier temporaire en toute sécurité si nécessaire.
        """
        log.info("SafeWriteFile.close essaie de Fermer le fichier et renommer le fichier temporaire en toute sécurité si nécessaire.")
        # if isinstance(self.__fd, TextIOWrapper):
        self.__fd.close()
        if not self._isCloud():
            if os.path.exists(self.__filename):
                log.info(f"SafeWriteFile.close retire {self.__filename}.")
                os.remove(self.__filename)
            if self.__filename is not None:
                if os.path.exists(self.__filename):
                    log.info(f"SafeWriteFile.close utilise __moveFileOutOfTheWay sur {self.__filename} avant de le renommer.")
                    # WTF ?
                    self.__moveFileOutOfTheWay(self.__filename)
                log.info(f"SafeWriteFile.close renomme {self.__tempFilename} en {self.__filename}.")
                os.rename(self.__tempFilename, self.__filename)

    def __moveFileOutOfTheWay(self, filename):
        """
        Déplacez un fichier existant en le renommant
        avec un suffixe incrémental pour éviter l'écrasement.

        Args :
            filename str : Le nom du fichier à déplacer.
        """
        log.debug("SafeWriteFile.__moveFileOutOfTheWay : Déplacement de '%s' pour éviter l'écrasement", filename)

        index = 1
        while True:
            name, ext = os.path.splitext(filename)
            # newName = "%s (%d)%s" % (name, index, ext)
            newName = f"{name} ({index:d}){ext}"
            if not os.path.exists(newName):
                os.rename(filename, newName)
                break
            index += 1

    def _getTemporaryFileName(self, path):
        """Générer un nom de fichier temporaire.

        Toutes les fonctions/classes de la bibliothèque standard qui peuvent générer
        un fichier temporaire, visible sur le système de fichiers, sans le supprimer
        à la fermeture sont obsolètes (il existe tempfile.NamedTemporaryFile
        mais son argument 'delete' est nouveau dans Python 2.6). Ce n'est pas
        sécurisé, ni thread-safe, mais cela fonctionne.

        Args :
            path (str) : Le chemin du répertoire dans lequel créer le fichier temporaire.

        Returns :
            name (str) : Le nom du fichier temporaire généré.
        """
        # idx = 0
        # while True:
        #     # name = os.path.join(path, "tmp-%d" % idx)
        #     name = os.path.join(path, f"tmp-{idx:d}")
        #     if not os.path.exists(name):
        #         return name
        #     idx += 1
        # while True:
        #     name = os.path.join(path, f"tmp-{idx:d}")
        #     if not os.path.exists(name):
        #         return name
        #     idx += 1
        # Use `tempfile.NamedTemporaryFile`: This is the recommended way to create temporary files
        # in Python and provides better security and thread safety.
        with tempfile.NamedTemporaryFile(dir=path, delete=False) as tf:
            return tf.name

    def _isCloud(self):
        """
        Vérifiez si le fichier se trouve dans un répertoire synchronisé avec le cloud.

        Returns :
            (bool) : True si le fichier se trouve dans un répertoire synchronisé avec le cloud, False sinon.
        """
        return _isCloud(os.path.dirname(self.__filename))


class TaskFile(patterns.Observer):
    """
    Une classe pour gérer le fichier de tâches, y compris le chargement,
    l'enregistrement et la surveillance des modifications.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez le TaskFile.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        log.info("Initialisation de TaskFile")

        self.__filename = self.__lastFilename = ""
        # log.info("TaskFile : self.__filename = self.__lastFilename = ''")
        self.__needSave = self.__loading = False
        # log.info("TaskFile : self.__needSave = self.__loading = False")
        self.__tasks = task.TaskList()
        # log.info(f"TaskFile : self.__tasks = {self.__tasks}")
        self.__categories = category.CategoryList()
        # log.info(f"TaskFile : self.__categories = {self.__categories}")
        self.__notes = note.NoteContainer()
        # log.info(f"TaskFile : self.__notes = {self.__notes}")
        self.__efforts = effort.EffortList(self.tasks())
        # log.info(f"TaskFile : self.__efforts = {self.__efforts}")
        self.__guid = generate()
        # log.info(f"TaskFile : self.__guid = {self.__guid}")
        self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        # log.info(f"TaskFile : self.__syncMLConfig = {self.__syncMLConfig}")
        self.__monitor = ChangeMonitor()
        # log.info(f"TaskFile : self.__monitor = {self.__monitor}")
        self.__changes = dict()
        self.__changes[self.__monitor.guid()] = self.__monitor
        # log.info(f"TaskFile : self.__changes = {self.__changes}")
        self.__changedOnDisk = False
        if kwargs.pop("poll", True):
            self.__notifier = TaskCoachFilesystemPollerNotifier(self)
        else:
            self.__notifier = TaskCoachFilesystemNotifier(self)
        self.__saving = False
        for collection in [self.__tasks, self.__categories, self.__notes]:
            self.__monitor.monitorCollection(collection)
        for domainClass in [
            task.Task,
            category.Category,
            note.Note,
            effort.Effort,
            attachment.FileAttachment,
            attachment.URIAttachment,
            attachment.MailAttachment,
        ]:
            self.__monitor.monitorClass(domainClass)
        super().__init__(*args, **kwargs)
        # Register for tasks, categories, efforts and notes being changed so we
        # can monitor when the task file needs saving (i.e. is 'dirty'):
        for container in self.tasks(), self.categories(), self.notes():
            for eventType in container.modificationEventTypes():
                self.registerObserver(
                    self.onDomainObjectAddedOrRemoved,
                    eventType,
                    eventSource=container,
                )

        for eventType in (
            base.Object.markDeletedEventType(),
            base.Object.markNotDeletedEventType(),
        ):
            self.registerObserver(self.onDomainObjectAddedOrRemoved, eventType)

        for eventType in task.Task.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(self.onTaskChanged_Deprecated, eventType)
        pub.subscribe(self.onTaskChanged, "pubsub.task")
        for eventType in effort.Effort.modificationEventTypes():
            self.registerObserver(self.onEffortChanged, eventType)
        for eventType in note.Note.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(self.onNoteChanged_Deprecated, eventType)
        pub.subscribe(self.onNoteChanged, "pubsub.note")
        for eventType in category.Category.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(
                    self.onCategoryChanged_Deprecated, eventType
                )
        pub.subscribe(self.onCategoryChanged, "pubsub.category")
        for eventType in (
            attachment.FileAttachment.modificationEventTypes()
            + attachment.URIAttachment.modificationEventTypes()
            + attachment.MailAttachment.modificationEventTypes()
        ):
            if not eventType.startswith("pubsub"):
                self.registerObserver(
                    self.onAttachmentChanged_Deprecated, eventType
                )
        pub.subscribe(self.onAttachmentChanged, "pubsub.attachment")

        # log.info("TaskFile : Tâches initiales : %s", self.tasks())
        # log.info("TaskFile : Notes initiales : %s", self.notes())

    def __str__(self):
        """Retourne une représentation sous forme de chaîne du fichier de tâches (le nom du fichier)."""
        return self.filename()
        # return str(self.filename())

    def __contains__(self, item):
        """
        Vérifie si un élément (tâche, note, catégorie ou effort) appartient à ce fichier de tâches.

        Args :
            item : L’objet à rechercher dans le fichier de tâches.

        Returns :
            (bool) : True si l’objet appartient à l’une des collections du fichier de tâches, sinon False.
        """

        return (
            item in self.tasks()
            or item in self.notes()
            or item in self.categories()
            or item in self.efforts()
        )

    def monitor(self):
        """
        Obtenez l'instance ChangeMonitor.

        Returns :
            ChangeMonitor : l'instance ChangeMonitor.
        """
        return self.__monitor

    def categories(self):
        """
        Obtenez l'instance CategoryList.

        Returns :
            CategoryList : l'instance CategoryList.
        """
        return self.__categories

    def notes(self):
        """
        Obtenez l'instance de NoteContainer.

        Returns :
            NoteContainer : l'instance de NoteContainer.
        """
        return self.__notes

    def tasks(self):
        """
        Obtenez l'instance TaskList.

        Returns :
            TaskList : l'instance TaskList.
        """
        return self.__tasks

    def efforts(self):
        """
        Obtenez l'instance EffortList.

        Returns :
            EffortList : l'instance EffortList.
        """
        return self.__efforts

    def syncMLConfig(self):
        """
        Obtenez la configuration SyncML.

        Returns :
            SyncMLConfig : la configuration SyncML.
        """
        return self.__syncMLConfig

    def guid(self):
        """
        Obtenez le GUID du fichier de tâches.

        Returns :
            str : Le GUID du fichier de tâches.
        """
        return self.__guid

    def changes(self):
        """
        Récupère le dictionnaire des modifications.

        Returns :
            (dict) : Le dictionnaire des modifications.
        """
        return self.__changes

    def setSyncMLConfig(self, config):
        """
        Définissez la configuration SyncML et marquez le fichier de tâches comme sale.

        Args :
            config (SyncMLConfig) : La configuration SyncML.
        """
        self.__syncMLConfig = config
        self.markDirty()

    def isEmpty(self):
        """
        Vérifiez si le fichier de tâche est vide.

        Returns :
            bool : True si le fichier de tâche est vide, False sinon.
        """
        return (
            0
            == len(self.categories())
            == len(self.tasks())
            == len(self.notes())
        )

    def onDomainObjectAddedOrRemoved(self, event):  # pylint: disable=W0613
        """
        Gérer les événements ajoutés ou supprimés des objets de domaine.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            return
        self.markDirty()

    def onTaskChanged(self, newValue, sender):
        """
        Gérer les événements modifiés par la tâche.

        Args :
            newValue : La nouvelle valeur.
            sender (task) : La tâche qui a changé (l'expéditeur).
        """
        if self.__loading or self.__saving:
            return
        if sender in self.tasks():
            self.markDirty()

    def onTaskChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de tâche obsolète.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            return
        changedTasks = [
            changedTask
            for changedTask in event.sources()
            if changedTask in self.tasks()
        ]
        if changedTasks:
            self.markDirty()
            for changedTask in changedTasks:
                changedTask.markDirty()

    def onEffortChanged(self, event):
        """
        Gérer les événements modifiés par l'effort.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            return
        changedEfforts = [
            changedEffort
            for changedEffort in event.sources()
            if changedEffort.task() in self.tasks()
        ]
        if changedEfforts:
            self.markDirty()
            for changedEffort in changedEfforts:
                changedEffort.markDirty()

    def onCategoryChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de catégorie obsolète.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            return
        changedCategories = [
            changedCategory
            for changedCategory in event.sources()
            if changedCategory in self.categories()
        ]
        if changedCategories:
            self.markDirty()
            # Marquer comme sales tous les éléments catégorisables appartenant à la catégorie modifiée ;
            # ceci est nécessaire car dans le monde SyncML/vcard, les catégories ne sont pas
            # des objets de première classe. Au lieu de cela, chaque tâche/contact/etc a une propriété
            # catégories qui est une liste de noms de catégorie
            # séparés par des virgules. Ainsi, lorsqu'un nom de catégorie change, chaque
            # catégorisable associé change.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()

    def onCategoryChanged(self, newValue, sender):
        """
        Gérer les événements de modification de catégorie.

        Args :
            newValue : la nouvelle valeur.
            sender (Category) : la catégorie qui a changé.
        """
        if self.__loading or self.__saving:
            return
        changedCategories = [
            changedCategory
            for changedCategory in [sender]
            if changedCategory in self.categories()
        ]
        if changedCategories:
            self.markDirty()
            # Marquer comme sales tous les éléments catégorisables appartenant à la catégorie modifiée ;
            # ceci est nécessaire car dans le monde SyncML/vcard, les catégories ne sont pas
            # des objets de première classe. Au lieu de cela, chaque tâche/contact/etc a une propriété
            # catégories qui est une liste de noms de catégorie
            # séparés par des virgules. Ainsi, lorsqu'un nom de catégorie change, chaque
            # catégorisable associé change.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()

    def onNoteChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de note obsolètes.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        for changedNote in event.sources():
            changedNote.markDirty()

    def onNoteChanged(self, newValue, sender):
        """
        Gérer les événements de modification de note.

        Args :
            newValue : la nouvelle valeur.
            sender (Note) : la note qui a changé.
        """
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        sender.markDirty()

    def onAttachmentChanged(self, newValue, sender):
        """
        Gérer les événements de modification de la pièce jointe.

        Args :
            newValue : la nouvelle valeur.
            sender (Attachment) : la pièce jointe qui a changé.
        """
        if self.__loading or self.__saving:
            return
        # Les pièces jointes ne connaissent pas leur propriétaire, nous ne pouvons donc pas vérifier si la pièce jointe
        # se trouve réellement dans le fichier de tâches. Nous supposons que ce soit le cas.
        self.markDirty()

    def onAttachmentChanged_Deprecated(self, event):
        """
        Gérer les événements de modification des pièces jointes obsolètes.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            return
        # Les pièces jointes ne connaissent pas leur propriétaire, nous ne pouvons donc pas vérifier si la pièce jointe
        # se trouve réellement dans le fichier de tâches. Supposons que ce soit le cas.
        self.markDirty()
        for changedAttachment in event.sources():
            changedAttachment.markDirty()

    def setFilename(self, filename):
        """
        Définissez le nom de fichier du fichier de tâche.

        Args :
            filename (str) : Le nom de fichier à définir.
        """
        if filename == self.__filename:
            return
        self.__lastFilename = filename or self.__filename
        self.__filename = filename
        self.__notifier.setFilename(filename)
        pub.sendMessage("taskfile.filenameChanged", filename=filename)
        log.info("TaskFile.setFilename : Nom de fichier défini sur : %s", filename)

    def filename(self):
        """
        Obtenez le nom de fichier du fichier de tâche.

        Returns :
            (str) : Le nom de fichier du fichier de tâche.
        """
        # log.debug("TaskFile.filename : Retourne le nom de fichier courant : %s appelé par %s", self.__filename, self)  # Crée une boucle infini !!! Ne pas utiliser !!!
        return self.__filename

    def lastFilename(self):
        """
        Obtenez le dernier nom de fichier du fichier de tâche.

        Returns :
            (str) : Le dernier nom de fichier du fichier de tâche.
        """
        return self.__lastFilename

    def isDirty(self):
        """
        Vérifiez si le fichier de tâche doit être enregistré.

        Returns :
            (bool) : True si le fichier de tâche doit être enregistré, False sinon.
        """
        log.debug("Vérification de l'état 'dirty' : %s", self.__needSave)

        return self.__needSave

    def markDirty(self, force=False):
        """
        Marquer le fichier de tâche comme sale (doit être enregistré).

        Args :
            force (bool) : (optional) S'il faut forcer le marquage comme sale. La valeur par défaut est False.
        """

        if force or not self.__needSave:
            self.__needSave = True
            pub.sendMessage("taskfile.dirty", taskFile=self)
            log.debug("Modification détectée, état 'dirty' mis à jour à True")
            log.debug(f"Le fichier {self} est marqué comme modifié")

    def markClean(self):
        """
        Marquez le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré).
        """
        if self.__needSave:
            log.info("TaskFile.markClean : Marque le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré).")
            self.__needSave = False
            pub.sendMessage("taskfile.clean", taskFile=self)

    def onFileChanged(self):
        """
        Gérer les modifications de fichiers.
        """
        if not self.__saving:
            # import wx  # Not really clean but we're in another thread...
            self.__changedOnDisk = True
            log.debug("TaskFile.onFileChanged : Appelle CallAfter.")
            wx.CallAfter(pub.sendMessage, "taskfile.changed", taskFile=self)
            log.debug("TaskFile.onFileChanged : CallAfter passé avec succès.")

    @patterns.eventSource
    def clear(self, regenerate=True, event=None):
        """
        Effacez le fichier de tâches, en régénérant éventuellement la configuration GUID et SyncML.

        Args :
            regenerate (bool, optional) : s'il faut régénérer la configuration GUID et SyncML. La valeur par défaut est True.
            event (Event, optional) : L'événement. La valeur par défaut est Aucun.
        """
        log.info(f"taskFile.clear : Effacement du contenu du fichier de tâches {self}(clear)")

        pub.sendMessage("taskfile.aboutToClear", taskFile=self)
        try:
            self.tasks().clear(event=event)
            self.categories().clear(event=event)
            self.notes().clear(event=event)
            if regenerate:
                self.__guid = generate()
                self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        finally:
            pub.sendMessage("taskfile.justCleared", taskFile=self)

    def close(self):
        """
        Fermez le fichier de tâches, en enregistrant toutes les modifications
        et en effaçant le contenu.
        """
        log.info("TaskFile.close Ferme le fichier de tâches, en enregistrant toutes les modifications et en effaçant le contenu.")
        if os.path.exists(self.filename()):
            # changes = xml.ChangesXMLReader(self.filename() + ".delta").read()
            try:
                log.debug(f"TaskFile.close : Essaie de lire le fichier {self.filename()}.delta en mode r et d'enregistrer les changements précédents.")
                with open(self.filename() + ".delta", "r") as f:
                    changes = xml.ChangesXMLReader(f).read()
            except FileNotFoundError as e:
                log.exception(f"TaskFile.close : Le fichier {self.filename()}.delta n'existe pas : {e}.")
                changes = {}
            del changes[self.__monitor.guid()]
            log.debug(f"TaskFile.close : Essaie d'écrire les changements dans le fichier {self.filename()}.delta en mode wb.")
            # xml.ChangesXMLWriter(open(self.filename() + ".delta", "wb")).write(
            #     changes
            # )
            # xml.ChangesXMLWriter(open(self.filename() + ".delta", "w")).write(
            #     changes
            # )
            with open(self.filename() + ".delta", "wb") as f:
                writer = xml.ChangesXMLWriter(f)
                writer.write(changes)
        log.info("TaskFile.close règle filename sur ''")
        self.setFilename("")
        self.__guid = generate()
        self.clear()
        self.__monitor.reset()
        self.markClean()
        self.__changedOnDisk = False
        log.debug("TaskFile.close terminé avec succès.")

    def stop(self):
        """
        Arrêter le notificateur du système de fichiers.
        """
        self.__notifier.stop()

    def _read(self, fd):
        """
        Lire le fichier de tâches à partir d'un descripteur de fichier.

        Args :
            fd : (file) Le descripteur de fichier à partir duquel lire.

        Returns :
            (tuple) : Les données lues (tâches, catégories, notes, syncMLConfig, modifications, guid).
        """
        # Assurez-vous que la variable fd passée au constructeur de XMLReader
        # est bien un objet fichier valide et ouvert en mode binaire ('rb')
        # pour la lecture. Si ce n'est pas le cas, cela pourrait expliquer
        # pourquoi self.__fd.read() renvoie une chaîne.
        log.debug(f"TaskFile._read essaie de lire le fichier de tâche à partir d'un descripteur fd {fd}")
        data_read = xml.XMLReader(fd).read()
        log.debug(f"TaskFile._read renvoi : {data_read}")
        return data_read

    def exists(self):
        """
        Vérifiez si le fichier de tâche existe.

        Returns :
            (bool) : True si le fichier de tâche existe, False sinon.
        """
        log.debug("TaskFile.exists vérifie si le fichier de tâche existe.")
        taskfile_exist = os.path.isfile(self.__filename)
        log.debug(f"TaskFile.exists : Le fichier de tâche existe = {taskfile_exist}.")
        return taskfile_exist

    def _openForWrite(self, suffix=""):
        """
        Ouvrez le fichier de tâche en écriture.

        Args :
            suffix (str) : (facultatif) le suffixe du fichier. La valeur par défaut est "".

        Returns :
            SafeWriteFile : l'instance SafeWriteFile.
        """
        log.info(f"TaskFile._openForWrite : Essaie d'ouvrir le fichier de tâche {self.__filename + suffix} en écriture.")
        return SafeWriteFile(self.__filename + suffix)

    def _openForRead(self):
        """
        Ouvrez le fichier de tâche pour la lecture.

        Returns :
            Le descripteur de fichier à lire.
        """
        # return file(self.__filename, 'rU')
        log.info(f"TaskFile._openForRead : Ouvre {self.__filename} en mode lecture binaire !")
        return open(self.__filename, "rb")

    def load(self, filename=None):
        """
        Chargez le fichier de tâche à partir du disque.

        Cette méthode lit un fichier XML contenant les tâches, catégories, notes,
        configurations SyncML et changements précédents. Elle initialise toutes les
        structures internes de l'objet TaskFile avec ces données.

        Si le fichier n'existe pas, elle initialise un fichier vide avec une
        configuration par défaut.

        Args :
            filename (str | None) : (optional) Le nom du fichier à partir duquel
            charger. La valeur par défaut est None. Le nom du fichier à charger.
            Si None, on utilise le nom déjà défini via `setFilename()`.

        Raises :
            IOError : Si le fichier ne peut pas être ouvert.
            Exception : Si une erreur de parsing XML ou de lecture survient.
        """
        log.info("TaskFile.load : Chargement du fichier de tâches '%s' à partir du disque.", filename)

        pub.sendMessage("taskfile.aboutToRead", taskFile=self)
        self.__loading = True
        if filename:
             self.setFilename(filename)
        # filename = filename or self.__filename
        # self.__filename = filename

        log.info("TaskFile.load : Chargement du fichier de tâches depuis : %s", filename)

        try:
            if self.exists():
                # fd = self._openForRead()
                with self._openForRead() as fd:
                    log.info(f"TaskFile.load : fd={fd} ouvert en mode lecture binaire !")
                    try:
                        tasks, categories, notes, syncMLConfig, changes, guid = (
                            self._read(fd)
                        )
                    # finally:
                    #     fd.close()
                    except Exception:
                        log.exception("TaskFile.load : Erreur lors de la lecture du fichier principal '%s'", self.filename())
                        raise
            else:
                tasks = []
                categories = []
                notes = []
                changes = dict()
                guid = generate()
                syncMLConfig = createDefaultSyncConfig(guid)
            self.clear()
            self.__monitor.reset()
            self.__changes = changes
            self.__changes[self.__monitor.guid()] = self.__monitor
            self.categories().extend(categories)
            self.tasks().extend(tasks)
            self.notes().extend(notes)

            def registerOtherObjects(objects):
                for obj in objects:
                    if isinstance(obj, base.CompositeObject):
                        registerOtherObjects(obj.children())
                    if isinstance(obj, note.NoteOwner):
                        registerOtherObjects(obj.notes())  # Unresolved attribute reference 'notes' for class 'NoteOwner'
                    if isinstance(obj, attachment.AttachmentOwner):
                        registerOtherObjects(obj.attachments())  # Unresolved attribute reference 'attachments' for class 'AttachmentOwner'
                    if isinstance(obj, task.Task):
                        registerOtherObjects(obj.efforts())
                    if (
                        isinstance(obj, note.Note)
                        or isinstance(obj, attachment.Attachment)
                        or isinstance(obj, effort.Effort)
                    ):
                        self.__monitor.setChanges(obj.id(), set())

            registerOtherObjects(self.categories().rootItems())
            registerOtherObjects(self.tasks().rootItems())
            registerOtherObjects(self.notes().rootItems())
            self.__monitor.resetAllChanges()
            self.__syncMLConfig = syncMLConfig
            self.__guid = guid

            if os.path.exists(self.filename()):
                # We need to reset the changes on disk because we're up to date.
                log.debug("TaskFile.load : Réécrit les changements dans {self.filename()}.delta en mode wb.")
                # xml.ChangesXMLWriter(
                #     open(self.filename() + ".delta", "wb")
                # ).write(self.__changes)  # écriture en bytes ? plutôt str, non ?
                # # xml.ChangesXMLWriter(
                # #     open(self.filename() + ".delta", "w")
                # # ).write(self.__changes)  # écriture en bytes ? plutôt str, non ?
                with open(self.filename() + ".delta", "wb") as f:
                    writer = xml.ChangesXMLWriter(f)
                    writer.write(self.__changes)
        except Exception as e:
            log.info("TaskFile.load règle filename sur ''")
            self.setFilename("")
            raise Exception(f"TaskFile.load : Erreur de parsing XML lors du chargement de '{filename}', erreur : {e}")
        finally:
            self.__loading = False
            self.markClean()
            self.__changedOnDisk = False
            pub.sendMessage("taskfile.justRead", taskFile=self)

        # try:
        #     with open(filename, "r", encoding="utf-8") as file:
        #         log.debug("TaskFile.load : METHODE A REVOIR !!!")
        #         parser = xml.reader.XMLReader(self)
        #         parser.read(file)
        #     # self.__dirty = False
        #     log.info("Fichier chargé avec succès : %s", filename)
        # except FileNotFoundError:
        #     log.warning("Fichier introuvable : %s. Un nouveau fichier sera créé.", filename)
        #     raise
        # except Exception as e:
        #     log.exception("Erreur lors du chargement du fichier de tâches : %s", filename)
        #     raise

    def save(self, **kwargs):
        """
        Enregistrez le fichier de tâches sur le disque.

        Cette méthode écrit toutes les tâches, notes, catégories et la configuration
        SyncML dans un fichier XML. Si le fichier existe déjà, il sera remplacé
        de manière sécurisée via l'utilisation d'un fichier temporaire (`SafeWriteFile`).

        En cas d'échec (problème de disque, erreur d'écriture...), une exception
        est loggée et propagée.

        Args :
            **kwargs : Arguments supplémentaires éventuels (non utilisés ici).

        Raises :
            IOError : En cas de problème d’écriture du fichier.
            Exception : En cas d’erreur inattendue pendant l’écriture.
        """
        log.info("TaskFile.save commence à Enregistrer le fichier de tâches sur le disque.")
        # # log.info("Sauvegarde de la base de tâches dans '%s'", filename)
        # # À modifier avec les nouvelles possibilités de with.
        # try:
        #     pub.sendMessage("taskfile.aboutToSave", taskFile=self)
        # except Exception:
        #     pass
        # # When encountering a problem while saving (disk full,
        # # computer on fire), if we were writing directly to the file,
        # # it's lost. So write to a temporary file and rename it if
        # # everything went OK.
        # self.__saving = True
        # try:
        #     # Fusionner les modifications du disque avec le fichier de tâches actuel.
        #     self.mergeDiskChanges()
        #
        #     if self.__needSave or not os.path.exists(self.__filename):
        #         fd = self._openForWrite()
        #         try:
        #             xml.XMLWriter(fd).write(
        #                 self.tasks(),
        #                 self.categories(),
        #                 self.notes(),
        #                 self.syncMLConfig(),
        #                 self.guid(),
        #             )
        #         finally:
        #             fd.close()
        #
        #     self.markClean()
        # finally:
        #     self.__saving = False
        #     self.__notifier.saved()
        #     try:
        #         pub.sendMessage("taskfile.justSaved", taskFile=self)
        #     except Exception:
        #         # log.exception("Erreur lors de la sauvegarde de '%s'", filename)
        #         pass

        if not self.__filename:
            log.error("TaskFile.save : Aucun nom de fichier n’est défini pour la sauvegarde.")
            raise RuntimeError("TaskFile.save : Aucun nom de fichier n’est défini pour la sauvegarde.")

        log.debug("TaskFile.save : Début de la sauvegarde vers le fichier : %s", self.__filename)

        try:
            # with self.safeWriter(self.__filename) as file:
            with SafeWriteFile(self.__filename) as file:
                # xmlWriter = writer.XMLWriter(self)
                xmlWriter = xml.writer.XMLWriter(file)
                xmlWriter.write(
                    self.tasks(),
                    self.categories(),
                    self.notes(),
                    self.syncMLConfig(),
                    self.guid(),
                    )
            # self.__dirty = False
            # self.__needSave = False
            self.markClean()
            log.info("TaskFile.save : Fichier sauvegardé avec succès : %s", self.__filename)
        except IOError as e:
            log.exception("TaskFile.save : Erreur d’écriture du fichier %s", self.__filename)
            raise
        except Exception as e:
            log.exception("TaskFile.save : Erreur inattendue lors de la sauvegarde du fichier : %s", self.__filename)
            raise

    def mergeDiskChanges(self):
        """
        Fusionner les modifications du disque avec le fichier de tâches actuel.
        """
        self.__loading = True
        try:
            if os.path.exists(self.__filename):
                # Not using self.exists() because DummyFile.exists returns True
                # Instead of writing the content of memory, merge changes
                # with the on-disk version and save the result.
                self.__monitor.freeze()
                try:
                    # fd = self._openForRead()
                    with self._openForRead() as fd:
                        log.info(f"TaskFile.mergeDiskChanges : fd={fd} ouvert en mode lecture binaire !")
                        try:
                            (
                                tasks,
                                categories,
                                notes,
                                syncMLConfig,
                                allChanges,
                                guid,
                            ) = self._read(fd)
                        except Exception:
                            log.exception("TaskFile.mergeDiskChanges : Erreur lors de la lecture du fichier principal pour la fusion des changements '%s'", self.__filename)
                            raise
                        # fd.close()
                    self.__changes = allChanges

                    if self.__saving:
                        for devGUID, changes in list(self.__changes.items()):
                            if devGUID != self.__monitor.guid():
                                changes.merge(self.__monitor)

                    sync = ChangeSynchronizer(self.__monitor, allChanges)

                    sync.sync(
                        [
                            (
                                self.categories(),
                                category.CategoryList(categories),
                            ),
                            (self.tasks(), task.TaskList(tasks)),
                            (self.notes(), note.NoteContainer(notes)),
                        ]
                    )

                    self.__changes[self.__monitor.guid()] = self.__monitor
                finally:
                    self.__monitor.thaw()
            else:
                self.__changes = {self.__monitor.guid(): self.__monitor}

            self.__monitor.resetAllChanges()
            # fd = self._openForWrite(".delta")
            # try:
            #     xml.ChangesXMLWriter(fd).write(self.changes())
            # finally:
            #     fd.close()
            with self._openForWrite(".delta") as fd:
                writer = xml.ChangesXMLWriter(fd)
                writer.write(self.changes())

            self.__changedOnDisk = False
        finally:
            self.__loading = False

    def saveas(self, filename):
        """
        Enregistrez le fichier de tâche sous un nouveau nom de fichier.

        Args :
            filename str : Le nouveau nom de fichier sous lequel enregistrer.
        """
        if os.path.exists(filename):
            os.remove(filename)
        # if os.path.exists(filename + ".delta"):
        if os.path.exists(f"{filename}.delta"):
            # os.remove(filename + ".delta")
            os.remove(f"{filename}.delta")
        self.setFilename(filename)
        self.save()

    def merge(self, filename):
        """
        Fusionnez un autre fichier de tâches avec celui-ci.

        Args :
            filename str : Le nom de fichier du fichier de tâches à fusionner.
        """
        mergeFile = self.__class__()
        mergeFile.load(filename)
        self.__loading = True
        categoryMap = dict()
        self.tasks().removeItems(
            self.objectsToOverwrite(self.tasks(), mergeFile.tasks())
        )
        self.rememberCategoryLinks(categoryMap, self.tasks())
        self.tasks().extend(mergeFile.tasks().rootItems())
        self.notes().removeItems(
            self.objectsToOverwrite(self.notes(), mergeFile.notes())
        )
        self.rememberCategoryLinks(categoryMap, self.notes())
        self.notes().extend(mergeFile.notes().rootItems())
        self.categories().removeItems(
            self.objectsToOverwrite(self.categories(), mergeFile.categories())
        )
        self.categories().extend(mergeFile.categories().rootItems())
        self.restoreCategoryLinks(categoryMap)
        mergeFile.close()
        self.__loading = False
        self.markDirty(force=True)

    def objectsToOverwrite(self, originalObjects, objectsToMerge):
        """
        Récupère les objets à écraser lors d'une fusion.

        Args :
            originalObjects (list) : Les objets d'origine.
            objectsToMerge (list) : Les objets à fusionner.

        Returns :
            list : Les objets à écraser.
        """
        objectsToOverwrite = []
        for domainObject in objectsToMerge:
            try:
                # Unresolved attribute reference 'getObjectById' for class 'list'
                # Vient de domain.base.collection.Collection !
                objectsToOverwrite.append(
                    originalObjects.getObjectById(domainObject.id())  # getObjectById vient de domain.base.collection.Collection ! Un ensemble d'objets composites observables.
                )
            except IndexError:
                pass
        return objectsToOverwrite

    def rememberCategoryLinks(self, categoryMap, categorizables):
        """
        N'oubliez pas les liens de catégorie pour une restauration ultérieure.

        Args :
            categorisMap (dict) : La carte des catégories.
            categorizables (list) : Les objets catégorisables.
        """
        for categorizable in categorizables:
            for categoryToLinkLater in categorizable.categories():
                categoryMap.setdefault(categoryToLinkLater.id(), []).append(
                    categorizable
                )

    def restoreCategoryLinks(self, categoryMap):
        """
        Restaurez les liens de catégorie à partir de la carte de catégorie mémorisée.

        Args :
            categoryMap (dict) : La carte de catégorie.
        """
        categories = self.categories()
        for categoryId, categorizables in categoryMap.items():
            try:
                categoryToLink = categories.getObjectById(categoryId)
            except IndexError:
                continue  # Subcategory was removed by the merge
            for categorizable in categorizables:
                categorizable.addCategory(categoryToLink)
                categoryToLink.addCategorizable(categorizable)

    def needSave(self):
        """
        Vérifiez si le fichier de tâche doit être enregistré.

        Returns :
            bool : True si le fichier de tâche doit être enregistré, False sinon.
        """
        return not self.__loading and self.__needSave

    def changedOnDisk(self):
        """
        Vérifiez si le fichier de tâche a changé sur le disque.

        Returns :
            bool : True si le fichier de tâche a changé sur le disque, False sinon.
        """
        return self.__changedOnDisk

    def beginSync(self):
        """
        Commencez une opération de synchronisation.
        """
        self.__loading = True

    def endSync(self):
        """
        Terminez une opération de synchronisation.
        """
        self.__loading = False
        self.markDirty()


class DummyLockFile(object):
    """
    Une classe de fichier de verrouillage factice à utiliser dans les répertoires synchronisés avec le cloud.
    """

    def acquire(self, timeout=None):
        """Méthode factice pour acquérir un verrou. Ne fait rien."""
        pass

    def release(self):
        """Méthode factice pour relâcher un verrou. Ne fait rien."""
        pass

    def is_locked(self):
        """Retourne toujours True : simule qu’un verrou est en place."""
        return True

    def i_am_locking(self):
        """Retourne toujours True : simule que le processus courant détient le verrou."""
        return True

    def break_lock(self):
        """Méthode factice pour briser un verrou. Ne fait rien."""
        pass


class LockedTaskFile(TaskFile):
    """LockedTaskFile ajoute un verrouillage coopératif à TaskFile.

    Une classe TaskFile avec un verrouillage coopératif pour empêcher les accès simultanés.
    Appelé par Application.init.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser le LockedTaskFile.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        super().__init__(*args, **kwargs)
        self.__lock = None

    def __isFuse(self, path):
        """
        Vérifiez si un chemin donné est un système de fichiers FUSE.

        Args :
            path (str) : Le chemin à vérifier.

        Returns :
            (bool) : True si le chemin est un système de fichiers FUSE. Système de fichiers FUSE, False sinon.
        """
        if operating_system.isGTK() and os.path.exists("/proc/mounts"):
            # for line in open("/proc/mounts", "r", encoding="utf-8"):
            #     try:
            #         location, mountPoint, fsType, options, a, b = (
            #             line.strip().split()
            #         )
            #     except Exception:
            #         pass
            #     if os.path.abspath(path).startswith(
            #         mountPoint
            #     ) and fsType.startswith("fuse."):
            #         return True
            # essayer de remplacer par :
            try:
                # with garantit que le fichier proc/mounts sera fermé correctement, même en cas d'erreur.
                with open("/proc/mounts", "r", encoding="utf-8") as mounts_file:
                    for line in mounts_file:
                        try:
                            location, mount_point, fs_type, options, _, _ = line.strip().split()
                            if os.path.abspath(path).startswith(mount_point) and fs_type.startswith("fuse."):
                                return True
                        except ValueError:
                            # Ignorer les lignes mal formées dans /proc/mounts
                            continue
            except (FileNotFoundError, PermissionError) as e:
                # Gérer les erreurs de lecture du fichier /proc/mounts
                log.error(f"LockedTaskFile.__isFuse: Erreur lors de la lecture de /proc/mounts: {e}")
        return False

    def __isCloud(self, filename):
        """
        Vérifier si un fichier se trouve dans un répertoire synchronisé avec le cloud.

        Args :
            filename (str) : Le nom du fichier à vérifier.

        Returns :
            (bool) : True si le fichier se trouve dans un répertoire synchronisé avec le cloud, sinon False.
        """
        return _isCloud(os.path.dirname(filename))

    def __createLockFile(self, filename):
        """
        Créez un fichier de verrouillage pour le nom de fichier donné.

        Args :
            filename (str) : Le nom de fichier pour lequel créer un fichier de verrouillage.

        Returns :
            (FileLock or DummyLockFile) : L'instance de fichier de verrouillage.
        """
        if operating_system.isWindows() and self.__isCloud(filename):
            return DummyLockFile()
        if self.__isFuse(filename):
            return lockfile.MkdirFileLock(filename)
        return lockfile.FileLock(filename)

    def is_locked(self):
        """
        Vérifiez si le fichier de tâche est verrouillé.

        Returns :
            (bool) : True si le fichier de tâche est verrouillé, False sinon.
        """
        return self.__lock and self.__lock.is_locked()

    def is_locked_by_me(self):
        """
        Vérifiez si le fichier de tâches est verrouillé par le processus en cours.

        Returns :
            (bool) : True si le fichier de tâches est verrouillé par le processus en cours, False sinon.
        """
        return self.is_locked() and self.__lock.i_am_locking()

    def release_lock(self):
        """
        Libérez le verrou sur le fichier de tâches.
        """
        if self.is_locked_by_me():
            self.__lock.release()

    def acquire_lock(self, filename):
        """
        Acquérir un verrou sur le fichier de tâche.

        Args :
            filename (str) : Le nom du fichier à verrouiller.
        """
        if not self.is_locked_by_me():
            self.__lock = self.__createLockFile(filename)
            self.__lock.acquire(5)

    def break_lock(self, filename):
        """
        Briser le verrou sur le fichier de tâches.

        Args :
            filename (str) : Le nom de fichier sur lequel briser le verrou.
        """
        self.__lock = self.__createLockFile(filename)
        self.__lock.break_lock()

    def close(self):
        """
        Fermez le fichier de tâches en libérant le verrou.
        """
        if self.filename() and os.path.exists(self.filename()):
            self.acquire_lock(self.filename())
        try:
            super().close()
        finally:
            self.release_lock()

    def load(
        self, filename=None, lock=True, breakLock=False
    ):  # pylint: disable=W0221
        """Verrouillez le fichier avant de le charger, s'il n'est pas déjà verrouillé.

        Chargez le fichier de tâches à partir du disque, en acquérant un verrou si nécessaire.

        Args :
            filename (str | None) : (optional) Le nom du fichier à partir duquel charger. La valeur par défaut est Aucun.
            lock (bool) : (optional) S'il faut acquérir un verrou. La valeur par défaut est True.
            breakLock (bool) : (optional) S'il faut briser un verrou existant. La valeur par défaut est False.
        """
        log.debug(f"LockedTaskFile.load : Appelé avec self={self}, filename={filename}, lock={lock}, breakLock={breakLock}")
        filename = filename or self.filename()
        log.debug(f"LockedTaskFile.load : Finalement filename={filename}")

        try:
            if lock and filename:
                if breakLock:
                    log.debug(f"LockedTaskFile.load : Brise le verrou de {filename}.")
                    self.break_lock(filename)
                log.debug(f"LockedTaskFile.load : Acquière un verrou pur {filename}.")
                self.acquire_lock(filename)
            log.debug("LockedTaskFile.load : Charge le fichier {filename}.")
            return super().load(filename)
        finally:
            log.debug("LockedTaskFile.load : Finalement relâche le verrou.")
            self.release_lock()

    def save(self, **kwargs):
        """Verrouillez le fichier avant de l'enregistrer, s'il n'est pas déjà verrouillé.

        Enregistrez le fichier de tâche sur le disque, en acquérant un verrou si nécessaire.

        Args :
            **kwargs : arguments de mots clés supplémentaires.
        """
        self.acquire_lock(self.filename())
        try:
            return super().save(**kwargs)
        finally:
            self.release_lock()

    def mergeDiskChanges(self):
        """
        Fusionnez les modifications du disque avec le fichier de tâches actuel, en acquérant un verrou si nécessaire.
        """
        self.acquire_lock(self.filename())
        try:
            super().mergeDiskChanges()
        finally:
            self.release_lock()
