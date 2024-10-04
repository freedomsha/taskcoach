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

import configparser
import os
import sys
import wx
import shutil

# from taskcoachlib.thirdparty.pubsub import pub
# https://pypubsub.readthedocs.io/en/v4.0.3/
from pubsub import pub

from taskcoachlib import meta, patterns, operating_system
from taskcoachlib.i18n import _
from taskcoachlib.workarounds import ExceptionAsUnicode
from . import defaults


class UnicodeAwareConfigParser(configparser.RawConfigParser):
    """
    Un ConfigParser personnalisé qui gère les chaînes Unicode.

    Cette classe hérite de RawConfigParser et fournit des méthodes
    compatibles Unicode pour définir et obtenir des valeurs de configuration.
    """

    def set(self, section, setting, value):  # pylint: disable=W0222
        # def set(self, section: str, setting: str, value: str | None):  # pylint: disable=W0222
        """
        Définissez une valeur de configuration dans la section spécifiée.

        Args :
            section (str) : le nom de la section.
            setting (str) : le nom du paramètre.
            value : la valeur à définir.
        """
        configparser.RawConfigParser.set(self, section, setting, value)

    def get(self, section, setting):  # pylint: disable=W0221
        # def get(self, section: str, setting: str) -> str:  # pylint: disable=W0221
        """
        Obtenez une valeur de configuration à partir de la section spécifiée.

        Args :
            section (str) : Le nom de la section.
            setting (str) : Le nom du paramètre.

        Returns :
            La valeur de configuration.
        """
        return configparser.RawConfigParser.get(self, section, setting)


class CachingConfigParser(UnicodeAwareConfigParser):
    """
    Un ConfigParser personnalisé qui met en cache les valeurs de configuration pour des performances améliorées.

    ConfigParser est plutôt lent, donc mettez en cache ses valeurs.

    Cette classe hérite d'UnicodeAwareConfigParser et ajoute une fonctionnalité de mise en cache
    pour éviter les recherches redondantes.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez CachingConfigParser.

        Crée un attribut d'instance (dictionnaire) : __cachedValues

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        self.__cachedValues = dict()
        UnicodeAwareConfigParser.__init__(self, *args, **kwargs)

    def read(self, *args, **kwargs):
        """
        Lire les données de configuration à partir des fichiers.

        Crée un attribut d'instance (dictionnaire) : __cachedValues

        Args :
            *args : chemins de fichiers à lire.
            **kwargs : arguments de mot-clé supplémentaires.

        Returns :
            bool : True en cas de succès, False sinon.
        """
        self.__cachedValues = dict()
        return UnicodeAwareConfigParser.read(self, *args, **kwargs)

    def set(self, section, setting, value):
        """
        Définissez une valeur de configuration et mettez-la en cache.

        Crée un attribut d'instance (dictionnaire) : __cachedValues

        Args:
            section (str) : Le nom de la section.
            setting (str) : Le nom du paramètre.
            value : La valeur à définir.
        """
        self.__cachedValues[(section, setting)] = value
        UnicodeAwareConfigParser.set(self, section, setting, value)

    def get(self, section, setting):
        """
        Obtenez une valeur de configuration à partir du cache ou lisez-la si elle n'est pas mise en cache.

        Args :
            section (str) : le nom de la section.
            setting (str) : le nom du paramètre.

        Returns :
            La valeur de configuration.
        """
        cache, key = self.__cachedValues, (section, setting)
        if key not in cache:
            cache[key] = UnicodeAwareConfigParser.get(
                self, *key
            )  # pylint: disable=W0142
        return cache[key]


class Settings(CachingConfigParser):
    """
    Une classe pour gérer les paramètres de l'application, héritant de CachingConfigParser.

    Cette classe gère la lecture, l'écriture et la mise en cache des paramètres de l'application,
    y compris la gestion des valeurs par défaut et la migration des fichiers de configuration.
    """

    def __init__(self, load=True, iniFile=None, *args, **kwargs):
        """
        Initialisez l'objet Paramètres.

        Args :
            load (bool, optional) : s'il faut charger les paramètres à partir du fichier. La valeur par défaut est True.
            iniFile (str, optional) : le chemin d'accès au fichier .ini. La valeur par défaut est Aucun.
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        # Soupir, ConfigParser.SafeConfigParser est une classe à l'ancienne, donc nous
        # devons appeler explicitement la superclasse __init__ :
        CachingConfigParser.__init__(self, *args, **kwargs)

        self.initializeWithDefaults()
        self.__loadAndSave = load
        self.__iniFileSpecifiedOnCommandLine = iniFile
        self.migrateConfigurationFiles()
        if load:
            # Tout d'abord, essayez de charger le fichier de paramètres depuis le répertoire du programme,
            # si cela échoue, chargez le fichier de paramètres depuis le répertoire des paramètres
            try:
                if not self.read(self.filename(forceProgramDir=True)):
                    self.read(self.filename())
                errorMessage = ""
            except configparser.ParsingError as errorMessage:
                # Ignorez les exceptions et utilisez simplement les valeurs par défaut.
                # Enregistrez également l'échec dans les paramètres :
                self.initializeWithDefaults()
            self.setLoadStatus(ExceptionAsUnicode(errorMessage))
        else:
            # Supposons que si les paramètres ne doivent pas être chargés, nous
            # devrions également rester silencieux (c'est-à-dire que nous sommes probablement en mode test) :
            self.__beQuiet()
        pub.subscribe(
            self.onSettingsFileLocationChanged,
            "settings.file.saveinifileinprogramdir",
        )  # Envoie un message de notification à onSettingsFileLocationChanged

    def onSettingsFileLocationChanged(self, value):
        """
        Gérer les modifications apportées à l'emplacement du fichier de paramètres.

        Crée un attribut saveIniFileInProgramDir qui prend la valeur de value.

        Args :
            value (bool) : s'il faut enregistrer le fichier .ini dans le répertoire du programme.
        """
        saveIniFileInProgramDir = value
        if not saveIniFileInProgramDir:
            try:
                os.remove(self.generatedIniFilename(forceProgramDir=True))
            except:
                return  # pylint: disable=W0702

    def initializeWithDefaults(self):
        """
        Initialisez les paramètres avec les valeurs par défaut.
        """
        for section in self.sections():
            self.remove_section(section)
        for section, settings in list(defaults.defaults.items()):
            self.add_section(section)
            for key, value in list(settings.items()):
                # Don't Notify observers while we are initializing
                super(Settings, self).set(section, key, value)

    def setLoadStatus(self, message):
        """
        Définissez l'état de chargement du fichier de paramètres.

        Args :
            message (str) : Le message d'erreur en cas d'échec du chargement.
        """
        self.set("file", "inifileloaded", "False" if message else "True")
        self.set("file", "inifileloaderror", message)

    def __beQuiet(self):
        """
        Désactivez les paramètres bruyants pour le mode silencieux (par exemple, pendant les tests).
        """
        noisySettings = [
            ("window", "splash", "False"),
            ("window", "tips", "False"),
            ("window", "starticonized", "Always"),
        ]
        for section, setting, value in noisySettings:
            self.set(section, setting, value)

    def add_section(
        self, section, copyFromSection=None
    ):  # pylint: disable=W0221
        """
        Ajoutez une nouvelle section aux paramètres.

        Args :
            section (str) : Le nom de la section.
            copyFromSection (str, optional) : La section à partir de laquelle copier les valeurs. La valeur par défaut est Aucun.

        Returns :
            bool : Vrai si la section a été ajoutée avec succès.
        """
        result = super(Settings, self).add_section(section)
        if copyFromSection:
            for name, value in self.items(copyFromSection):
                super(Settings, self).set(section, name, value)
        return result

    def getRawValue(self, section, option):
        # def getRawValue(self, section: str, option: str):
        """
        Obtenez une valeur brute (non évaluée) à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns:
            str : La valeur brute.
        """
        return super(Settings, self).get(section, option)

    def init(self, section, option, value):
        # def init(self, section: str, option: str, value):
        """
        Initialisez un paramètre avec une valeur donnée.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value : La valeur à définir.

        Returns:
            bool : vrai si la valeur a été définie avec succès.
        """
        return super(Settings, self).set(section, option, value)

    def get(self, section, option):
        # def get(self, section: str, option: str):
        """
        Obtenez une valeur à partir des paramètres, de la gestion des valeurs par défaut et des anciens formats de fichier .ini.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            La valeur du paramètre.
        """
        try:
            result = super(Settings, self).get(section, option)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return self.getDefault(section, option)
        result = self._fixValuesFromOldIniFiles(section, option, result)
        result = self._ensureMinimum(section, option, result)
        return result

    def getDefault(self, section, option):
        # def getDefault(self, section: str, option: str):
        """
        Obtenez la valeur par défaut pour un paramètre donné.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            La valeur par défaut.
        """
        defaultSectionKey = section.strip("0123456789")
        try:
            defaultSection = defaults.defaults[defaultSectionKey]
        except KeyError:
            raise configparser.NoSectionError(defaultSectionKey)
        try:
            return defaultSection[option]
        except KeyError:
            raise configparser.NoOptionError((option, defaultSection))

    def _ensureMinimum(self, section, option, result):
        # def _ensureMinimum(self, section: str, option: str, result):
        """
        Assurez-vous qu'une valeur de paramètre répond aux exigences minimales.

        Args :
            section (str) : le nom de la section.
            option (str) : le nom de l'option.
            result : la valeur à vérifier.

        Returns :
            La valeur result, garantissant qu'elle répond aux exigences minimales.
        """
        if section in defaults.minimum and option in defaults.minimum[section]:
            result = max(result, defaults.minimum[section][option])
        return result

    def _fixValuesFromOldIniFiles(self, section, option, result):
        # def _fixValuesFromOldIniFiles(self, section: str, option: str, result):
        """
        Corrigez les paramètres des anciens fichiers TaskCoach.ini qui ne sont plus valides.

        Args :
            section (str) : le nom de la section.
            option (str) : le nom de l'option.
            result : La valeur à corriger.

        Returns :
            La valeur result corrigée.
        """
        original = result
        # À partir de la version 1.1.0, les propriétés de date des tâches (startDate,
        # dueDate et CompletionDate) sont des datetimes :
        taskDateColumns = ("startDate", "dueDate", "completionDate")
        orderingViewers = [
            "taskviewer",
            "categoryviewer",
            "noteviewer",
            "noteviewerintaskeditor",
            "noteviewerincategoryeditor",
            "noteviewerinattachmenteditor",
            "categoryviewerintaskeditor",
            "categoryviewerinnoteeditor",
        ]
        if option == "sortby":
            if result in taskDateColumns:
                result += "Time"
            try:
                eval(result)
            except:
                sortKeys = [result]
                try:
                    ascending = self.getboolean(section, "sortascending")
                except:
                    ascending = True
                result = '["%s%s"]' % (("" if ascending else "-"), result)
        elif option == "columns":
            columns = [
                (col + "Time" if col in taskDateColumns else col)
                for col in eval(result)
            ]
            result = str(columns)
        elif option == "columnwidths":
            widths = dict()
            try:
                columnWidthMap = eval(result)
            except SyntaxError:
                columnWidthMap = dict()
            for column, width in list(columnWidthMap.items()):
                if column in taskDateColumns:
                    column += "Time"
                widths[column] = width
            if section in orderingViewers and "ordering" not in widths:
                widths["ordering"] = 28
            result = str(widths)
        elif (
            section == "feature"
            and option == "notifier"
            and result == "Native"
        ):
            result = "Task Coach"
        elif section == "editor" and option == "preferencespages":
            result = result.replace("colors", "appearance")
        elif section in orderingViewers and option == "columnsalwaysvisible":
            try:
                columns = eval(result)
            except SyntaxError:
                columns = ["ordering"]
            else:
                if "ordering" in columns:
                    columns.remove("ordering")
            result = str(columns)
        if result != original:
            super(Settings, self).set(section, option, result)
        return result

    def set(self, section, option, value, new=False):  # pylint: disable=W0221
        # def set(self, section: str, option: str, value, new: bool = False) -> bool:  # pylint: disable=W0221
        """
        Définissez une valeur dans les paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value : La valeur à définir.
            new (bool, optional) : s'il s'agit d'une nouvelle option. La valeur par défaut est False.

        Returns :
            bool : True si la valeur a été définie avec succès.
        """
        if new:
            currentValue = (
                "a new option, so use something as current value"
                " that is unlikely to be equal to the new value"
            )
        else:
            currentValue = self.get(section, option)
        if value != currentValue:
            super(Settings, self).set(section, option, value)
            patterns.Event("%s.%s" % (section, option), self, value).send()
            return True
        else:
            return False

    def setboolean(self, section, option, value):
        # def setboolean(self, section: str, option: str, value: bool) -> bool:
        """
        Définissez une valeur booléenne dans les paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value (bool) : La valeur à définir.

        Returns :
            bool : Vrai si la valeur a été définie avec succès.
        """
        if self.set(section, option, str(value)):
            pub.sendMessage("settings.%s.%s" % (section, option), value=value)

    setvalue = settuple = setlist = setdict = setint = setboolean

    def settext(self, section, option, value):
        # def settext(self, section: str, option: str, value):
        """
        Définissez une valeur de texte dans les paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value (str) : La valeur à définir.

        Returns :
            bool : Vrai si la valeur a été définie avec succès.
        """
        if self.set(section, option, value):
            pub.sendMessage("settings.%s.%s" % (section, option), value=value)

    def getlist(self, section, option):
        """
        Obtenez une valeur de liste à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            list : La valeur de la liste.
        """
        return self.getEvaluatedValue(section, option, eval)

    getvalue = gettuple = getdict = getlist

    def getint(self, section, option):
        # def getint(self, section, option) -> int:
        """
        Obtenez une valeur entière à partir des paramètres.

        Args:
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns:
            int : la valeur entière.
        """
        return self.getEvaluatedValue(section, option, int)

    def getboolean(self, section, option):
        # def getboolean(self, section, option) -> bool:
        """
        Obtenez une valeur booléenne à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            bool : La valeur booléenne.
        """
        return self.getEvaluatedValue(section, option, self.evalBoolean)

    def gettext(self, section, option):
        # def gettext(self, section, option) -> str:
        """
        Obtenez une valeur de texte à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            str : la valeur du texte.
        """
        return self.get(section, option)

    @staticmethod
    def evalBoolean(stringValue):
        # def evalBoolean(stringValue: str) -> bool:
        """
        Évalue une chaîne en tant que valeur booléenne.

        Args :
            stringValue (str) : La valeur de la chaîne.

        Returns :
            bool : La valeur booléenne évaluée.

        Raises :
            ValueError : Relève un message d'erreur si la chaîne n'est pas une valeur booléenne valide.
        """
        if stringValue in ("True", "False"):
            return "True" == stringValue
        else:
            raise ValueError(
                "invalid literal for Boolean value: '%s'" % stringValue
            )

    def getEvaluatedValue(
        self, section, option, evaluate=eval, showerror=wx.MessageBox
    ):
        # def getEvaluatedValue(
        #         self, section: str, option: str, evaluate=eval, showerror=wx.MessageBox
        # ):
        """
        Obtenez une valeur à partir des paramètres et évaluez-la.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            evaluate (fonction, optional) : La fonction pour évaluer la valeur. La valeur par défaut est eval.
            showerror (fonction, optional) : la fonction pour afficher les erreurs. La valeur par défaut est wx.MessageBox.

        Returns :
            La valeur évaluée.
        """
        stringValue = self.get(section, option)
        try:
            return evaluate(stringValue)
        except Exception as exceptionMessage:  # pylint: disable=W0703
            message = "\n".join(
                [
                    _("Error while reading the %s-%s setting from %s.ini.")
                    % (section, option, meta.filename),
                    _("The value is: %s") % stringValue,
                    _("The error is: %s") % exceptionMessage,
                    _(
                        "%s will use the default value for the setting and should proceed normally."
                    )
                    % meta.name,
                ]
            )
            showerror(
                message, caption=_("Settings error"), style=wx.ICON_ERROR
            )
            defaultValue = self.getDefault(section, option)
            self.set(
                section, option, defaultValue, new=True
            )  # Ignore current value
            return evaluate(defaultValue)

    def save(
        self, showerror=wx.MessageBox, file=open
    ):  # pylint: disable=W0622
        """
        Enregistrez les paramètres dans un fichier.

        Args :
            showerror (fonction, optional) : La fonction pour afficher les erreurs. La valeur par défaut est le fichier wx.MessageBox.
            file (fonction, optional) : la fonction pour ouvrir les fichiers. Par défaut, ouvrir.
        """
        self.set("version", "python", sys.version)
        self.set(
            "version",
            "wxpython",
            "%s-%s @ %s"
            % (wx.VERSION_STRING, wx.PlatformInfo[2], wx.PlatformInfo[1]),
        )
        self.set("version", "pythonfrozen", str(hasattr(sys, "frozen")))
        self.set("version", "current", meta.data.version)
        if not self.__loadAndSave:
            return
        try:
            path = self.path()
            if not os.path.exists(path):
                os.mkdir(path)
            tmpFile = open(self.filename() + ".tmp", "w")
            self.write(tmpFile)
            tmpFile.close()
            if os.path.exists(self.filename()):
                os.remove(self.filename())
            os.rename(self.filename() + ".tmp", self.filename())
        except Exception as message:  # pylint: disable=W0703
            showerror(
                _("Error while saving %s.ini:\n%s\n")
                % (meta.filename, message),
                caption=_("Save error"),
                style=wx.ICON_ERROR,
            )

    def filename(self, forceProgramDir=False):
        # def filename(self, forceProgramDir: bool = False) -> str:
        """
        Obtenez le nom de fichier du fichier .ini.

        Args :
            forceProgramDir (bool, optional) : s'il faut forcer l'enregistrement dans le répertoire du programme. La valeur par défaut est False.

        Returns :
            str : Le nom du fichier .ini.
        """
        if self.__iniFileSpecifiedOnCommandLine:
            return self.__iniFileSpecifiedOnCommandLine
        else:
            return self.generatedIniFilename(forceProgramDir)

    def path(
        self, forceProgramDir=False, environ=os.environ
    ):  # pylint: disable=W0102
        """
        Get the path to the configuration directory.

        Args:
            forceProgramDir (bool, optional): Whether to force saving in the program directory. Defaults to False.
            environ (dict, optional): The environment variables. Defaults to os.environ.

        Returns:
            str: The path to the configuration directory.
        """
        if self.__iniFileSpecifiedOnCommandLine:
            return self.pathToIniFileSpecifiedOnCommandLine()
        elif forceProgramDir or self.getboolean(
            "file", "saveinifileinprogramdir"
        ):
            return self.pathToProgramDir()
        else:
            return self.pathToConfigDir(environ)

    @staticmethod
    def pathToDocumentsDir():
        """
        Obtenez le chemin d'accès au répertoire des documents.

        Returns:
            str : Le chemin d'accès au répertoire des documents.
        """
        if operating_system.isWindows():
            from win32com.shell import shell, shellcon

            try:
                return shell.SHGetSpecialFolderPath(
                    None, shellcon.CSIDL_PERSONAL
                )
            except:
                # Yes, one of the documented ways to get this sometimes fail with "Unspecified error". Not sure
                # this will work either.
                # Update: There are cases when it doesn't work either; see support request #410...
                try:
                    return shell.SHGetFolderPath(
                        None, shellcon.CSIDL_PERSONAL, None, 0
                    )  # SHGFP_TYPE_CURRENT not in shellcon
                except:
                    return os.getcwd()  # Fuck this
        elif operating_system.isMac():
            import Carbon.Folder, Carbon.Folders, Carbon.File

            pathRef = Carbon.Folder.FSFindFolder(
                Carbon.Folders.kUserDomain,
                Carbon.Folders.kDocumentsFolderType,
                True,
            )
            return Carbon.File.pathname(pathRef)
        elif operating_system.isGTK():
            try:
                from PyKDE4.kdeui import KGlobalSettings
            except ImportError:
                pass
            else:
                return str(KGlobalSettings.documentPath())
        # Assuming Unix-like
        return os.path.expanduser("~")

    def pathToProgramDir(self):
        """
        Obtenez le chemin d'accès au répertoire du programme.

        Returns :
            str : Le chemin d'accès au répertoire du programme.
        """
        path = sys.argv[0]
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return path

    def pathToConfigDir(self, environ):
        """
        Obtenez le chemin d'accès au répertoire de configuration.

        Args :
            environ (dict) : Les variables d'environnement.

        Returns :
            str : Le chemin d'accès au répertoire de configuration.
        """
        try:
            if operating_system.isGTK():
                # from taskcoachlib.thirdparty.xdg import BaseDirectory
                from xdg import BaseDirectory

                path = BaseDirectory.save_config_path(meta.name)
            elif operating_system.isMac():
                import Carbon.Folder
                import Carbon.Folders
                import Carbon.File

                pathRef = Carbon.Folder.FSFindFolder(
                    Carbon.Folders.kUserDomain,
                    Carbon.Folders.kPreferencesFolderType,
                    True,
                )
                path = Carbon.File.pathname(pathRef)
                # XXXFIXME: should we release pathRef ? Doesn't seem so since I get a SIGSEGV if I try.
            elif operating_system.isWindows():
                from win32com.shell import shell, shellcon

                path = os.path.join(
                    shell.SHGetSpecialFolderPath(
                        None, shellcon.CSIDL_APPDATA, True
                    ),
                    meta.name,
                )
            else:
                path = self.pathToConfigDir_deprecated(environ=environ)
        except:  # Fallback to old dir
            path = self.pathToConfigDir_deprecated(environ=environ)
        return path

    def _pathToDataDir(self, *args, **kwargs):
        """
        Obtenez le chemin d'accès au répertoire de données.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.

        Returns :
            str : le chemin d'accès au répertoire de données.
        """
        forceGlobal = kwargs.pop("forceGlobal", False)
        if operating_system.isGTK():
            # from taskcoachlib.thirdparty.xdg import BaseDirectory
            from xdg import BaseDirectory

            path = BaseDirectory.save_data_path(meta.name)
        elif operating_system.isMac():
            from Carbon import Folder
            from Carbon import Folders
            from Carbon import File

            pathRef = Folder.FSFindFolder(
                Folders.kUserDomain,
                Folders.kApplicationSupportFolderType,
                True,
            )
            path = File.pathname(pathRef)
            # XXXFIXME: should we release pathRef ? Doesn't seem so since I get a SIGSEGV if I try.
            path = os.path.join(path, meta.name)
        elif operating_system.isWindows():
            if self.__iniFileSpecifiedOnCommandLine and not forceGlobal:
                path = self.pathToIniFileSpecifiedOnCommandLine()
            else:
                from win32com.shell import shell, shellcon

                path = os.path.join(
                    shell.SHGetSpecialFolderPath(
                        None, shellcon.CSIDL_APPDATA, True
                    ),
                    meta.name,
                )
        else:  # Errr...
            path = self.path()

        if operating_system.isWindows():
            # Follow shortcuts.
            from win32com.client import Dispatch

            shell = Dispatch("WScript.Shell")
            for component in args:
                path = os.path.join(path, component)
                if os.path.exists(path + ".lnk"):
                    shortcut = shell.CreateShortcut(path + ".lnk")
                    path = shortcut.TargetPath
        else:
            path = os.path.join(path, *args)

        exists = os.path.exists(path)
        if not exists:
            os.makedirs(path)
        return path, exists

    def pathToDataDir(self, *args, **kwargs):
        """
        Obtenez le chemin d'accès au répertoire de données.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.

        Returns :
            str : le chemin d'accès au répertoire de données.
        """
        return self._pathToDataDir(*args, **kwargs)[0]

    def _pathToTemplatesDir(self):
        """
        Obtenez le chemin d'accès au répertoire des modèles.

        Returns :
            str : Le chemin d'accès au répertoire des modèles.
        """
        try:
            return self._pathToDataDir("templates")
        except:
            pass  # Fallback on old path
        return self.pathToTemplatesDir_deprecated(), True

    def pathToTemplatesDir(self):
        """
        Obtenez le chemin d'accès au répertoire des modèles.

        Returns :
            str : Le chemin d'accès au répertoire des modèles.
        """
        return self._pathToTemplatesDir()[0]

    def pathToBackupsDir(self):
        """
        Obtenez le chemin d'accès au répertoire des sauvegardes.

        Returns :
            str : Le chemin d'accès au répertoire des sauvegardes.
        """
        return self._pathToDataDir("backups")[0]

    def pathToConfigDir_deprecated(self, environ):
        """
        Obtenez le chemin obsolète vers le répertoire de configuration.

        Args :
            environ (dict) : Les variables d'environnement.

        Returns :
            str : Le chemin obsolète vers le répertoire de configuration.
        """
        try:
            path = os.path.join(environ["APPDATA"], meta.filename)
        except Exception:
            path = os.path.expanduser("~")  # pylint: disable=W0702
            if path == "~":
                # path not expanded: apparently, there is no home dir
                path = os.getcwd()
            path = os.path.join(path, f".{meta.filename}")
        return operating_system.decodeSystemString(path)

    def pathToTemplatesDir_deprecated(self, doCreate=True):
        """
        Obtenez le chemin obsolète vers le répertoire des modèles.

        Args :
            doCreate (bool, optional) : s'il faut créer le répertoire s'il n'existe pas. La valeur par défaut est True.

        Returns :
            str : le chemin obsolète vers le répertoire des modèles.
        """
        path = os.path.join(self.path(), "taskcoach-templates")

        if operating_system.isWindows():
            # Under Windows, check for a shortcut and follow it if it
            # exists.

            if os.path.exists(path + ".lnk"):
                from win32com.client import Dispatch  # pylint: disable=F0401

                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(path + ".lnk")
                return shortcut.TargetPath

        if doCreate:
            try:
                os.makedirs(path)
            except OSError:
                pass
        return operating_system.decodeSystemString(path)

    def pathToIniFileSpecifiedOnCommandLine(self):
        """
        Obtenez le chemin d'accès au fichier .ini spécifié sur la ligne de commande.

        Returns :
            str : Le chemin d'accès au fichier .ini spécifié sur la ligne de commande.
        """
        return os.path.dirname(self.__iniFileSpecifiedOnCommandLine) or "."

    def generatedIniFilename(self, forceProgramDir):
        """
        Génère le nom de fichier du fichier .ini.

        Args :
            forceProgramDir (bool) : s'il faut forcer l'enregistrement dans le répertoire du programme.

        Returns :
            str : Le nom de fichier généré du fichier .ini.
        """
        return os.path.join(
            self.path(forceProgramDir), f"{meta.filename}.ini"
        )

    def migrateConfigurationFiles(self):
        """
        Migrez les fichiers de configuration vers de nouveaux emplacements si nécessaire.
        """
        # Modèles(Templates). Attention particulière au raccourci Windows.
        oldPath = self.pathToTemplatesDir_deprecated(doCreate=False)
        newPath, exists = self._pathToTemplatesDir()
        if self.__iniFileSpecifiedOnCommandLine:
            globalPath = os.path.join(
                self.pathToDataDir(forceGlobal=True), "templates"
            )
            if os.path.exists(globalPath) and not os.path.exists(oldPath):
                # Mise à niveau à partir d'une nouvelle installation de 1.3.24 Portable
                oldPath = globalPath
                if exists and not os.path.exists(newPath + "-old"):
                    # WTF?
                    os.rename(newPath, newPath + "-old")
                exists = False
        if exists:
            return
        if oldPath != newPath:
            if operating_system.isWindows() and os.path.exists(
                oldPath + ".lnk"
            ):
                shutil.move(oldPath + ".lnk", newPath + ".lnk")
            elif os.path.exists(oldPath):
                # pathToTemplatesDir() has created the directory
                try:
                    os.rmdir(newPath)
                except:
                    pass
                shutil.move(oldPath, newPath)
        # Ini file
        oldPath = os.path.join(
            self.pathToConfigDir_deprecated(environ=os.environ),
            f"{meta.filename}.ini",
        )
        newPath = os.path.join(
            self.pathToConfigDir(environ=os.environ), f"{meta.filename}.ini"
        )
        if newPath != oldPath and os.path.exists(oldPath):
            shutil.move(oldPath, newPath)
        # Cleanup
        try:
            os.rmdir(self.pathToConfigDir_deprecated(environ=os.environ))
        except:
            pass

    def __hash__(self):
        # def __hash__(self) -> int:
        """
        Obtenez le hachage de l'objet Paramètres.

        Returns :
            int : L'id de hachage de l'objet Paramètres.
        """
        return id(self)
