# -*- coding: utf-8 -*-

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
# Problème : Le code dépend de plusieurs modules externes (comme wx, lxml, etc.),
# mais il n'y a pas de vérification explicite de leur disponibilité.
# Solution : Ajoutez des vérifications pour s'assurer que tous les modules
# requis sont disponibles, et fournissez des messages d'erreur clairs
# si ce n'est pas le cas.

# from future import standard_library
#
# standard_library.install_aliases()
# from builtins import str
# from builtins import range
# from builtins import object
import base64
import io  # as StringIO
import logging
import os
# Problème : Le code utilise os.path pour manipuler les chemins de fichiers,
# mais il n'utilise pas pathlib, qui est plus moderne et plus sûr.
# Solution : Envisagez de migrer vers pathlib pour une gestion
# plus moderne des chemins de fichiers.
import re
import stat
import wx
# from wx import adv as wxadv
# import xml.etree.ElementTree as eTree
# from lxml import etree as ET
from xml.etree import ElementTree as ET
from taskcoachlib.persistence import sessiontempfile  # pylint: disable=F0401
from taskcoachlib import meta, patterns
from taskcoachlib.changes import ChangeMonitor
from taskcoachlib.domain import base, date, effort, task, category, categorizable, note, attachment
from taskcoachlib.i18n import translate
from taskcoachlib.syncml.config import SyncMLConfigNode, createDefaultSyncConfig
from taskcoachlib.thirdparty.deltaTime import nlTimeExpression
from taskcoachlib.thirdparty.guid import generate

log = logging.getLogger(__name__)


# Problème : Le code ouvre des fichiers sans toujours vérifier
# si le fichier existe ou s'il est accessible en lecture/écriture.
# Solution : Ajoutez des vérifications pour s'assurer que les fichiers existent
# et sont accessibles avant de les ouvrir.
# Problème : Le code ne gère pas explicitement les encodages de fichiers,
# ce qui peut poser problème avec des fichiers XML contenant des caractères non-ASCII.
# Solution : Spécifiez explicitement l'encodage lors de l'ouverture des fichiers
# (par exemple, open(file, encoding='utf-8')).
# Quelques points pourraient être améliorés :
#    Passage de os.path à pathlib.
#    Remplacement de eval par ast.literal_eval.
#    Gestion plus sûre des fichiers temporaires avec des context managers.
#    Gestion explicite de l’encodage lors de l’ouverture des fichiers (certains TODO le signalent).


def parseAndAdjustDateTime(string, *timeDefaults):
    """
    Cette fonction analyse et ajuste une chaîne de caractères représentant une date et une heure.

    Args :
        string (str) : La chaîne de caractères à analyser, censée représenter une date et une heure.
        *timeDefaults (tuple, optionnel) : Un ou plusieurs objets `date.Time` représentant
                                           des valeurs par défaut pour l'heure, la minute, la seconde et la microseconde.

    Returns :
        date.DateTime : Un objet `date.DateTime` représentant la date et l'heure analysées et ajustées.

    **Détails**

    La fonction `parseAndAdjustDateTime` utilise la fonction `date.parseDateTime`
    de la bibliothèque `taskcoachlib` pour analyser la chaîne de caractères fournie
    et convertir la valeur en un objet `date.DateTime`.

    Elle effectue ensuite un ajustement spécifique :

    * Si la date et l'heure analysées correspondent à une date valide
    et que l'heure est exactement 23:59:00.000000,
    la fonction ajuste l'heure aux valeurs 23:59:59.999999.

    En d'autres termes, si la chaîne de caractères représente la fin d'une journée,
    la fonction s'assure que la microseconde est réglée à la valeur maximale possible (999999) pour une meilleure précision.

    **Exemple d'utilisation**

    ```python
    date_time_str = "2023-10-27 23:59:00"
    adjusted_datetime = parseAndAdjustDateTime(date_time_str)
    print(adjusted_datetime)  # Affichage : 2023-10-27 23:59:59.999999
    """
    dateTime = date.parseDateTime(string, *timeDefaults)
    # log.debug(f"reader.parseAndAdjustDateTime : dateTime = {dateTime}")
    # Si dateTime est différent d'aujourd'hui et qu'elle n'est pas vide et que l'heure est égal à 23:59:0:0
    # l'ajuster à (year, mont, day, 23:59:59:999999)
    if (
        dateTime != date.DateTime()
        and dateTime is not None
        and dateTime.time() == date.Time(23, 59, 0, 0)
    ):
        dateTime = date.DateTime(year=dateTime.year,
                                 month=dateTime.month,
                                 day=dateTime.day,
                                 hour=23, minute=59, second=59, microsecond=999999)
    # log.debug(f"reader.parseAndAdjustDateTime : dateTime ajusté = {dateTime}")
    return dateTime


# class PIParser(ET.XMLTreeBuilder):  # XMLTreeBuilder don't exist. Si, dans lxml !
# class PIParser(ET.TreeBuilder):  # AttributeError: 'PIParser' object has no attribute 'feed'
class PIParser(ET.XMLParser):
    """See http://effbot.org/zone/element-pi.htm

    **Classe PIParser**

    Cette classe personnalisée hérite de `ET.XMLTreeBuilder` (ou éventuellement `ET.TreeBuilder` selon la version de xml)
    et est utilisée pour analyser des documents XML contenant des instructions de traitement (PI) spécifiques à Task Coach.

    **Référence**

    http://effbot.org/zone/element-pi.htm (en anglais)

    **Notes**

    * Le code d'origine faisait référence à une classe `ET.XMLTreeBuilder` qui n'existe plus dans les versions récentes de lxml.
    * La classe utilise la bibliothèque `lxml` pour un meilleur traitement des instructions de traitement.

    **Méthodes**

    * Le constructeur `__init__` est implémenté pour initialiser l'objet analyseur.
        * (Commentaire obsolète car la gestion des instructions de traitement est effectuée par lxml)
        * Le code d'origine tentait de définir un gestionnaire d'instructions de traitement (`ProcessingInstructionHandler`)
          mais cette approche n'est plus fonctionnelle.

    **Problèmes connus**

    * Le code d'origine qui tentait de parser la version de Task Coach à partir de l'instruction de traitement n'est plus
      compatible avec les versions récentes de Python.
    """

    def __init__(self):
        """
        Initialiser l'objet analyseur.
        * (Commentaire obsolète car la gestion des instructions de traitement est effectuée par lxml)
        * Le code d'origine tentait de définir un gestionnaire d'instructions de traitement (`ProcessingInstructionHandler`)
          mais cette approche n'est plus fonctionnelle.
        """
        # ET.XMLTreeBuilder.__init__(self)
        # eTree.TreeBuilder.__init__(self)
        super().__init__()
        # self._parser.ProcessingInstructionHandler = self.handle_pi
        # print("PIParser.init définit :")
        self.ProcessingInstructionHandler = self.handle_pi
        # print(f"self.ProcessingInstructionHandler = {self.ProcessingInstructionHandler}")
        self.tskversion = meta.data.tskversion
        # Problème : Le code gère plusieurs versions de fichiers XML,
        # mais la logique de gestion des versions est parfois dispersée
        # et difficile à suivre.
        # Solution : Envisagez de centraliser la logique de gestion des versions
        # dans une classe ou un module dédié.
        # print(f"La version de taskcoach self.tskversion (de meta.data)= {self.tskversion}")
        # Initialisation de la classe parente (ET.XMLTreeBuilder ou ET.TreeBuilder)
        # super().__init__()

        # FIXME: The codes below no longer works with lastest python
        #
        # Codes refs: https://uucode.com/blog/2012/06/19/xmletreeelementtree-and-processing-instructions/
        # self._parser.ProcessingInstructionHandler = self.handle_pi
        #
        # Use lxml's ElementTree instead, it's provided better Processing Instruction handling

    def handle_pi(self, target, data):
        """
        Traite une instruction de traitement XML (Processing Instruction - PI).

        Cette méthode est appelée lorsqu'une instruction de traitement est rencontrée
        dans un fichier XML. Si le `target` est "taskcoach", elle tente d'extraire la
        version de Task Coach (indiquée par `tskversion`) à partir de la chaîne `data`
        en utilisant une expression régulière. Si la version est trouvée, elle est stockée
        dans l'attribut `self.tskversion` sous forme d'entier.

        Args :
            target (str) : Cible de l'instruction de traitement, typiquement "taskcoach".
            data (str) : Données associées à l'instruction, pouvant contenir des métadonnées
                         comme tskversion="123".

        Returns :
            None

        Exemple :
            Pour une instruction de traitement comme :
            <?taskcoach tskversion="78"?>
            Cette méthode extraira 78 et définira self.tskversion = 78.
        """
        # log.debug(f"PIParser.handle_pi : self = {self}, target = {target}, data = {data}.")
        if target == "taskcoach":
            # print("target = taskcoach")
            # match_object = re.search('tskversion="(\d+)"', data)
            # match_object = re.search("tskversion='(\\d+)'", data)
            # match_object = re.search(r'tskversion="(\d+)"', data)
            # print(f"self.__fd = {self.__fd}")
            # match_object = re.search(r'tskversion=[\'"](\d+)[\'"]', self.__fd.readline().strip())  # Pourquoi self.__fd.readline().strip() ?
            match_object = re.search(rb'tskversion=[\'"](\d+)[\'"]', data)
            # print(f"PIParser.handle_pi : objets correspondants à la recherche match_object = {match_object}")
            if match_object:
                # self.tskversion = int(match_object.group(1))
                try:
                    self.tskversion = int(match_object.group(1))
                    log.debug(f"PIParser.handle_pi : La version de taskcoach du fichier est {self.tskversion}.")
                except ValueError:
                    log.error(f"PIParser.handle_pi : Impossible de convertir la version '{match_object.group(1)}' en entier.")
            else:
                # wx.LogError("PIParser.handle_pi : tskversion non trouvée dans la PI.")
                log.error("PIParser.handle_pi : tskversion non trouvée dans la PI.")
            # print(f"PIParser.handle_pi définit self.tskversion = {self.tskversion}")
        else:
            # wx.LogError("PIParser.handle_pi : target différent de taskcoach")
            log.error("PIParser.handle_pi : target différent de taskcoach")


class XMLReaderTooNewException(Exception):
    """
    **Classe d'exception XMLReaderTooNewException**

    Cette exception est levée si le lecteur XML rencontre un format de fichier XML
    plus récent que celui qu'il est capable de gérer.
    """
    pass


class XMLReader(object):  # nouvelle classe
    """ Classe de lecture des fichiers de tâches dans le format de fichier de tâches XML par défaut.

    **Méthodes**

    `tskversion`
        * Renvoie la version du fichier de tâches en cours de lecture.
        * Il s'agit de la version interne du fichier de tâches, distincte de la version de l'application Task Coach.
        * La version du fichier de tâches est incrémentée à chaque modification.
    `read`
        * Méthode principale pour lire le contenu d'un fichier de tâches.
        * Lit le fichier et renvoie les tâches, les catégories, les notes, la configuration SyncML et le GUID.
        * Déroulement de la méthode `read` :
            1. Vérifie et corrige les sauts de ligne incorrects dans le fichier (spécifique à la version 24).
            2. Crée une instance de `PIParser` pour analyser les instructions de traitement (PI) spécifiques à Task Coach.
            3. Parse l'arbre XML du fichier à l'aide de `ET.parse` et de l'analyseur `PIParser`.
            4. Extrait la version du fichier de tâches à partir de l'instruction de traitement "taskcoach".
            5. Vérifie si la version du fichier est compatible avec la version de l'application Task Coach.
            6. Appelle des méthodes privées pour parser les différents éléments du fichier :
                * `__parse_task_nodes` : Parse les noeuds de tâches.
                * `__resolve_prerequisites_and_dependencies` : Résout les prérequis et les dépendances entre les tâches.
                * `__parse_note_nodes` : Parse les noeuds de notes.
                * `__parse_category_nodes` (si version du fichier > 13) : Parse les noeuds de catégories.
                * `__parse_category_nodes_from_task_nodes` (si version du fichier <= 13) : Parse les catégories à partir des noeuds de tâches (ancienne version).
                * `__resolve_categories` : Associe les catégories aux tâches et aux notes.
            7. Parse le GUID du fichier.
            8. Parse la configuration SyncML du fichier.
            9. Définit la date de modification de chaque objet lu à partir des informations stockées en interne.
            10. Lit les modifications éventuelles du fichier de modifications Delta (`*.delta`).
            11. Affiche des informations de debug sur les éléments lus.
            12. Renvoie les tâches, les catégories, les notes, la configuration SyncML, les modifications et le GUID.
    `__has_broken_lines`
        * Vérifie si le fichier de tâches (version 24) contient des sauts de ligne incorrects dans les balises d'élément.
    `__fix_broken_lines`
        * Corrige les sauts de ligne incorrects identifiés dans les balises d'élément du fichier de tâches.
        
    *** Méthodes privées ***
    
    `__parse_task_nodes` (méthode privée)
        * Parse de manière récursive tous les noeuds de tâches de l'arbre XML et renvoie une liste d'instances de tâches.
        
    `__resolve_prerequisites_and_dependencies` (méthode privée)
        * Remplace les identifiants de prérequis par les instances de tâches correspondantes et définit les dépendances entre les tâches.

    `__resolve_categories`
        * Associe les catégories aux tâches et aux notes correspondantes.
        * Établit les relations entre les catégories et les objets catégorisables (tâches, notes, etc.).
        * Garantit que les objets catégorisables soient correctement associés à leurs catégories et que les catégories soient informées de leur contenu.
    
        **Arguments**
    
        * `categories` (liste de `Category`): Liste d'objets de catégorie parsés à partir du XML.
        * `tasks` (liste de `Task`): Liste d'objets de tâche parsés à partir du XML.
        * `notes` (liste de `Note`): Liste d'objets de note parsés à partir du XML.
    
        **Comportement**
    
        1. Crée des dictionnaires de mappage pour les objets catégorisables et les catégories.
        2. Parcourt toutes les catégories, tâches et notes pour les ajouter aux dictionnaires de mappage respectifs.
        3. Itère sur les relations catégorie-objet catégorisable stockées dans `self.__categorizables`.
            * Récupère la catégorie correspondante à l'identifiant (vérifie les clés absentes).
            * Récupère l'objet catégorisable associé à l'identifiant dans la carte des objets catégorisables (vérifie les clés absentes).
            * Ajoute l'objet catégorisable à la catégorie et inversement (déclenche des événements pour notifier les changements).
    
        **Erreurs gérées**
    
        * `KeyError`: Si l'identifiant d'une catégorie référencée dans `self.__categorizables` n'est pas trouvé dans la carte des catégories parsées.
    
    `__parse_category_nodes`
        * Parse de manière récursive tous les noeuds de catégorie de l'arbre XML et renvoie une liste d'instances de catégorie.
    
    `__parse_note_nodes`
        * Parse de manière récursive tous les noeuds de note de l'arbre XML et renvoie une liste d'instances de note.
    
    `__parse_category_node`
        * Parse un nœud XML de catégorie et retourne une instance de `category.Category`.
        * Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
        * Parse les notes associées à la catégorie à l'aide de `__parse_note_nodes`.
        * Récupère et parse les attributs `filtered` et `exclusiveSubcategories` (booléens).
        * Construit un dictionnaire avec les informations extraites.
        * Gère différemment l'attribut `categorizables` selon la version du fichier de tâches.
        * Parse les pièces jointes si la version du fichier de tâches est supérieure à 20.
        * Crée et retourne une instance de `category.Category` en utilisant le dictionnaire d'arguments.
        * Enregistre la date de modification de la catégorie à l'aide de `__save_modification_datetime`.
    
    `__parse_category_nodes_from_task_nodes`
        * Utilisée pour les versions de fichier <= 13 où les catégories étaient des sous-nœuds des tâches.
        * Récupère tous les nœuds de tâche et construit un mappage entre les identifiants de tâche et les catégories associées.
        * Crée un mappage distinct pour les catégories uniques.
        * Associe les catégories aux tâches via `self.__categorizables`.
        * Retourne une liste des objets `category.Category` créés.
    
    `__parse_category_nodes_within_task_nodes`
        * Méthode statique (ou anciennement statique) pour parser les nœuds de catégorie imbriqués dans les nœuds de tâche.
        * Construit et retourne un dictionnaire mappant les identifiants de tâche à une liste de noms de catégorie.
    
    `__parse_task_node`
        * Parse un nœud XML de tâche et retourne une instance de `task.Task`.
        * Gère la rétrocompatibilité pour l'attribut `planned_start_datetime_attribute_name` (nom différent selon la version).
        * Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
        * Parse et ajoute les attributs spécifiques aux tâches (dates, pourcentage d'achèvement, budget, priorité, frais, rappel, etc.).
        * Ignore les prérequis pour le moment (ils seront résolus ultérieurement).
        * Parse les efforts, les notes et la récurrence associés à la tâche.
        * Parse les pièces jointes si la version du fichier de tâches est supérieure à 20.
        * Enregistre les prérequis dans `self.__prerequisites` pour une résolution ultérieure.
        * Crée et retourne une instance de `task.Task` en utilisant le dictionnaire d'arguments.
        * Enregistre la date de modification de la tâche à l'aide de `__save_modification_datetime`.

    `__parse_recurrence`
        * Parse les informations de récurrence à partir du nœud et retourne une instance de `date.Recurrence`.
        * Utilise différentes méthodes de parsing selon la version du fichier de tâches (inférieure ou supérieure à 19).
        * Délègue le parsing à `__parse_recurrence_attributes_from_task_node` (pour les versions <= 19) ou `__parse_recurrence_node` (pour les versions >= 20).
    
    `__parse_recurrence_node`
        * Parse les informations de récurrence stockées dans un nœud séparé (à partir de la version 20).
        * Extrait les attributs `unit`, `amount`, `count`, `max`, `stop_datetime`, `sameWeekday` et `recurBasedOnCompletion` du nœud "recurrence".
        * Retourne un dictionnaire contenant les informations de récurrence.
    
    `__parse_recurrence_attributes_from_task_node`
        * Méthode (anciennement statique) pour parser les informations de récurrence stockées directement dans les attributs du nœud de tâche (versions <= 19).
        * Extrait les attributs `recurrence`, `recurrenceCount`, `recurrenceFrequency` et `maxRecurrenceCount`.
        * Retourne un dictionnaire contenant les informations de récurrence.
    
    `__parse_note_node`
        * Parse un nœud XML de note et retourne une instance de `note.Note`.
        * Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
        * Parse les pièces jointes si la version du fichier de tâches est supérieure à 20.
        * Enregistre la date de modification de la note à l'aide de `__save_modification_datetime`.
    
    `__parse_base_attributes`
        * Parse les attributs communs à tous les objets de domaine composites (id, date de création, date de modification, sujet, description, couleurs, police, icône, etc.).
        * Retourne un dictionnaire contenant ces attributs.
        * Gère la rétrocompatibilité pour l'attribut de couleur de fond (`color` ou `bgColor`).
        * Gère la rétrocompatibilité pour les pièces jointes (présentes dans les versions <= 20).
        * Parse l'attribut `status` (présent à partir de la version 22).
    
    `__parse_base_composite_attributes`
        * Parse les attributs de base (comme `__parse_base_attributes`) et ajoute également le parsing des enfants et des contextes étendus.
        * Appelle `__parse_base_attributes` pour récupérer les attributs de base.
        * Parse les enfants à l'aide de la fonction `parse_children` fournie en argument.
        * Parse les contextes étendus à partir de l'attribut `expandedContexts`.
        * Retourne un dictionnaire contenant tous les attributs.

    `__parse_attachments_before_version21`
        * Parse les pièces jointes pour les versions de fichier antérieures à 21.
        * Construit le chemin vers le répertoire des pièces jointes en se basant sur le nom du fichier de tâches.
        * Itère sur les nœuds "attachment" et crée des instances de `attachment.AttachmentFactory`.
        * Gère les différences entre les anciennes et les nouvelles versions pour la création des pièces jointes.
        * Gère les erreurs d'entrée/sortie (IOError) pour les pièces jointes (par exemple, les pièces jointes de courriel).
    
    `__parse_effort_nodes`
        * Parse tous les enregistrements d'effort du nœud et les retourne sous forme de liste.
        * Utilise `__parse_effort_node` pour parser chaque enregistrement individuel.
    
    `__parse_effort_node`
        * Parse un enregistrement d'effort individuel à partir du nœud.
        * Récupère et parse les attributs `start`, `stop` et `description`.
        * Gère l'attribut `status` (présent à partir de la version 22) et l'attribut `id` (présent à partir de la version 29).
        * Crée et retourne une instance de `effort.Effort`.
        * L'attribut `task` est initialisé à `None` et sera défini ultérieurement pour éviter des envois d'événements indésirables.
    
    `__parse_syncml_node`
        * Parse le nœud SyncML et retourne la configuration SyncML.
        * Crée une configuration par défaut à l'aide de `createDefaultSyncConfig`.
        * Recherche le nœud SyncML (nom différent selon la version du fichier).
        * Appelle `__parse_syncml_nodes` pour parser les nœuds enfants.
    
    `__parse_syncml_nodes`
        * Parse récursivement les nœuds SyncML.
        * Traite les nœuds "property" en définissant les propriétés correspondantes dans la configuration.
        * Traite les autres nœuds en créant des nœuds de configuration enfants et en appelant récursivement `__parse_syncml_nodes`.
    
    `__parse_guid_node`
        * Parse le nœud GUID et retourne le GUID.
        * Extrait et nettoie le texte du nœud.
        * Génère un nouveau GUID si aucun n'est trouvé.
    
    `__parse_attachments`
        * Parse les pièces jointes d'un nœud.
        * Itère sur les nœuds "attachment" et appelle `__parse_attachment` pour chaque pièce jointe.
        * Gère les erreurs d'entrée/sortie (IOError).
    
    `__parse_attachment`
        * Parse une pièce jointe individuelle.
        * Récupère les attributs de base à l'aide de `__parse_base_attributes`.
        * Parse les notes associées à la pièce jointe.
        * Gère différemment l'attribut `location` selon la version du fichier.
        * Pour les versions <= 22, construit le chemin vers le fichier de la pièce jointe.
        * Pour les versions > 22, gère les pièces jointes dont les données sont directement incluses dans le XML.
        * Crée un fichier temporaire pour les données de pièces jointes incluses.
        * Définit les permissions du fichier temporaire sur lecture seule pour Windows.
        * Crée et retourne une instance de `attachment.AttachmentFactory`.
        * Enregistre la date de modification de la pièce jointe à l'aide de `__save_modification_datetime`.

    `__parse_description`
        * Parse la description à partir du nœud.
        * Traite différemment la description selon la version du fichier de tâches (avant ou après la version 6).
        * Pour les versions <= 6, récupère l'attribut "description" directement.
        * Pour les versions > 6, utilise `__parse_text` pour extraire le texte du nœud "description".
    
    `__parse_text`
        * Parse le texte d'un nœud.
        * Retourne une chaîne vide si le nœud est `None` ou si son texte est vide.
        * Supprime les sauts de ligne en début et fin de texte pour les versions >= 24.
    
    `__parse_int_attribute`
        * Parse un attribut entier d'un nœud.
        * Utilise une valeur par défaut en cas d'échec du parsing.
    
    `__parse_datetime`
        * Parse une date et une heure à partir du texte.
        * Utilise `__parse` avec la fonction `date.parseDateTime`.
    
    `__parse_font_description`
        * Parse une description de police à partir du texte.
        * Crée un objet `wx.Font` à partir de la description.
        * Ajuste la taille de la police si elle est inférieure à 4.
        * Retourne la police ou la valeur par défaut en cas d'échec.
    
    `__parse_icon`
        * Parse un nom d'icône à partir du texte.
        * Corrige un nom d'icône spécifique ("clock_alarm").
    
    `__parse_boolean`
        * Parse un booléen à partir du texte.
        * Convertit les chaînes "True" et "False" en booléens.
        * Lève une exception `ValueError` si le texte n'est pas "True" ou "False".
    
    `__parse_tuple`
        * Parse un tuple à partir du texte.
        * Utilise `eval` pour convertir le texte en tuple si le texte commence par "(" et se termine par ")".
        * Retourne la valeur par défaut en cas d'échec.
    
    `__parse`
        * Méthode générique pour parser du texte à l'aide d'une fonction de parsing.
        * Gère les exceptions `ValueError` et retourne une valeur par défaut en cas d'échec.
    
    `__save_modification_datetime`
        * Enregistre la date et l'heure de modification d'un élément pour une restauration ultérieure.
        * Stocke la date et l'heure dans le dictionnaire `self.__modification_datetimes`.
        * Retourne l'élément.
    """
    defaultStartTime = (0, 0, 0, 0)
    defaultEndTime = (23, 59, 59, 999999)

    def __init__(self, fd):
        """
        Création des attributs d'instance

        Args :
            fd : Fichier par défaut.
        """
        #
        # Fichier
        # print(f"XMLReader: Début d'init\n"
        #       f"XMLReader.init : enregistrement du fichier fd = {fd} dans self.__fd.")
        self.__fd = fd
        # print(f"self.__fd = {self.__fd}.")
        # Taille de la police par défaut :
        self.__default_font_size = wx.SystemSettings.GetFont(
            wx.SYS_DEFAULT_GUI_FONT).GetPointSize()
        # log.debug(f"XMLReader.init : Création de self.__default_font_size = {self.__default_font_size}")
        # Dictionnaire des catégories :
        # log.debug("XMLReader.init : Création des dictionnaires self.categories, self.__modification_datetimes, self.__prerequisites et self.__categorizables")
        # self.categories = self.categories or {}
        self.categories = dict()
        # Dictionnaire des dates&heures de modification :
        self.__modification_datetimes = dict()
        # Dictionnaire des prérequis :
        self.__prerequisites = dict()
        # Dictionnaire des catégorisables :
        self.__categorizables = dict()
        # log.debug(f"📂 XMLReader : Contenu de self.__categorizables AVANT traitement : {self.__categorizables}")
        # Version de fichier :
        self.__tskversion = None

    def tskversion(self):
        """ Renvoie la version du fichier de tâches actuel en cours de lecture. Notez qu'il ne s'agit pas
            de la version de l'application. Le fichier de tâches possède sa propre numérotation de version
            (un numéro qui augmente à chaque modification).

        * Il s'agit de la version interne du fichier de tâches, distincte de la version de l'application Task Coach.
        * La version du fichier de tâches est incrémentée à chaque modification.
        """
        # log.debug(f"XMLReader.tskversion : est sensé renvoyer la version du fichier de tâches actuel en cours de lecture self.__tskversion = {self.__tskversion}")
        return self.__tskversion

    def read(self):
        """
        Lire le fichier de tâches et renvoyer les tâches, les catégories,
        les notes, la configuration SyncML et le GUID.

        Méthode principale pour lire le contenu d'un fichier de tâches.

        Déroulement de la méthode `read` :
            1. Vérifie et corrige les sauts de ligne incorrects dans le fichier (spécifique à la version 24).
            2. Crée une instance de `PIParser` pour analyser les instructions de traitement (PI) spécifiques à Task Coach.
            3. Parse l'arbre XML du fichier à l'aide de `ET.parse` et de l'analyseur `PIParser`.
            4. Extrait la version du fichier de tâches à partir de l'instruction de traitement "taskcoach".
            5. Vérifie si la version du fichier est compatible avec la version de l'application Task Coach.
            6. Appelle des méthodes privées pour parser les différents éléments du fichier :
                * `__parse_task_nodes` : Parse les noeuds de tâches.
                * `__resolve_prerequisites_and_dependencies` : Résout les prérequis et les dépendances entre les tâches.
                * `__parse_note_nodes` : Parse les noeuds de notes.
                * `__parse_category_nodes` (si version du fichier > 13) : Parse les noeuds de catégories.
                * `__parse_category_nodes_from_task_nodes` (si version du fichier <= 13) : Parse les catégories à partir des noeuds de tâches (ancienne version).
                * `__resolve_categories` : Associe les catégories aux tâches et aux notes.
            7. Parse le GUID du fichier.
            8. Parse la configuration SyncML du fichier.
            9. Définit la date de modification de chaque objet lu à partir des informations stockées en interne.
            10. Lit les modifications éventuelles du fichier de modifications Delta (`*.delta`).
            11. Affiche des informations de debug sur les éléments lus.
            12. Renvoie les tâches, les catégories, les notes, la configuration SyncML, les modifications et le GUID.
        """
        # wx.LogDebug(f"XMLReader.read : self.__fd={self.__fd} est de type {type(self.__fd)}.")  # le type est pompeux !
        # wx.LogDebug(f"XMLReader.read : Lit self.__fd={self.__fd}.")  # Le type de classe est déjà dans self.__fd !
        log.debug(f"XMLReader.read : Lit self.__fd={self.__fd}.")  # Le type de classe est déjà dans self.__fd !
        # self.__fd=<_io.TextIOWrapper name='/home/sylvain/.local/share/Task Coach/templates/dueTomorrow.tsktmpl' mode='r' encoding='UTF-8'> est de type <class '_io.TextIOWrapper'>
        # self.__fd=<_io.TextIOWrapper name='/home/sylvain/.local/share/Task Coach/templates/tmpjwjkljek.tsktmpl' mode='r' encoding='UTF-8'> est de type <class '_io.TextIOWrapper'>
        # self.__fd=<_io.TextIOWrapper name='/home/sylvain/.local/share/Task Coach/templates/dueToday.tsktmpl' mode='r' encoding='UTF-8'> est de type <class '_io.TextIOWrapper'>
        # self.__fd=<_io.TextIOWrapper name='/home/sylvain/.local/share/Task Coach/templates/tmpbg4pusbk.tsktmpl' mode='r' encoding='UTF-8'> est de type <class '_io.TextIOWrapper'>
        # Vérification de self.__fd :
        # content = self.__fd.read()
        # if not self.__fd.getvalue().strip():
        if isinstance(self.__fd, (io.StringIO, io.BytesIO)):  # Et si TextIOWrapper ?
            # if isinstance(self.__fd, (io.StringIO, io.BytesIO, io.TextIOWrapper)):
            # if isinstance(self.__fd, (io.BytesIO)):
            if self.__fd.readable():
                contenu = self.__fd.read().strip()  # io.BufferedIOBase.read() renvoie des bytes !
                # wx.LogDebug(f"XMLReader.read : contenu = {contenu}")
                log.debug(f"XMLReader.read : contenu = {contenu}")
                if not contenu:
                    # wx.LogInfo("XMLReader.read : Fichier XML vide.")
                    log.info("XMLReader.read : Fichier XML vide.")
                    # raise ValueError("Fichier XML vide, impossible de le charger.")
                self.__fd.seek(0)  # Remettre le pointeur du fichier au début
            if not self.__fd.getvalue().strip():
                # print("XMLReader.read : ⚠️ Le fichier XML est vide, retour de valeurs vides.")
                # wx.LogDebug("XMLReader.read : ⚠️ Le fichier XML est vide, retour de valeurs vides.")
                log.debug("XMLReader.read : ⚠️ Le fichier XML est vide, retour de valeurs vides.")
                return [], [], [], None, {}, None  # Retourne des listes et objets vides
        # if isinstance(content, bytes):
        #     content = content.decode('utf-8', errors='replace')  # Décode en UTF-8, remplace les erreurs
        #     # Recherche et suppression des lignes brisées (méthode à adapter si nécessaire)
        #     content = content.replace("><spds><sources><TaskCoach-\n", "")

        # 1. Vérifie et corrige les sauts de ligne incorrects dans le fichier (spécifique à la version 24).
        # print("XMLReader.read : 1.Vérifie les sauts de ligne incorrects")
        self.__fd.seek(0)
        if self.__has_broken_lines():
            self.__fix_broken_lines()
        # print("XMLReader.read : Sauts de ligne corrigés")

        # Lire la première ligne du fichier pour récupérer l'instruction de traitement
        self.__fd.seek(0)  # Revenir au début du fichier
        first_line = self.__fd.readline().strip()
        # print(f"XMLReader.read : Première ligne de self.__fd = {first_line}")

        # Extraire la version du fichier si présente
        tskversion = 1  # Valeur par défaut
        match = re.search(r'tskversion=[\'"](\d+)[\'"]', first_line)
        log.info(f"XMLReader.read : Récupère la version du fichier = {match}")
        if match:
            tskversion = int(match.group(1))

        # print(f"✅ XMLReader.read : tskversion du fichier lu extrait avant parsing = {tskversion}")
        #
        # # 2. Crée une instance de `PIParser` pour analyser les instructions de traitement (PI) spécifiques à Task Coach.
        # # print("XMLReader.read : 2.Création d'une instance de PIParser.")
        parser = PIParser()
        # 3. Analyse l'arbre XML du fichier à l'aide de `ET.parse` et de l'analyseur `PIParser`.
        # try:
        self.__fd.seek(0)  # Remet le curseur au début du fichier
        # wx.LogDebug(f"XMLReader.read : Contenu du fichier lu:\n{self.__fd.read()}")  # Vérifie le contenu lu. Ne s'affiche pas dans les tests !
        # log.debug(f"XMLReader.read : DEBUG - Contenu du fichier lu:\n{self.__fd.read()}")  # Vérifie le contenu lu. Ne s'affiche pas dans les tests !
        log.debug(f"XMLReader.read : Contenu du fichier :\n{self.__fd.read()}")  # Vérifie le contenu lu
        self.__fd.seek(0)  # Reviens au début avant parsing
        # print(f"XMLReader.read : 3. Valeur du fichier lu : self.__fd.getvalue = {self.__fd.getvalue()}")
        # tree = eTree.parse(self.__fd, parser)
        tree = ET.parse(self.__fd, parser)
        # print(f"XMLReader.read : Résultat de l'analyse de l'arbre par le parseur: tree = {tree}")
        # tree n'est pas iterable, ni utilisable en soi, attendre d'avoir root.
        root = tree.getroot()
        # root = ET.fromstring(content.encode('utf-8')) # Parse depuis une chaîne UTF-8 encodée
        # root = ET.fromstring(self.__fd.read().encode('utf-8'))  # Parse depuis une chaîne UTF-8 encodée
        # print(f"XMLReader.read : root = {root}")
        # print(f"XMLReader.read : root.tag = {root.tag}")
        # print(f"XMLReader.read : Dictionnaire d'attributs root.attrib = {root.attrib}")
        # print(f"ET.dump(root) = {ET.dump(root)}")
        # ET.dump(root)
        # print("Vérification :")
        # for child in root.iter():
        #     print(f"enfant direct : {child.tag}: {child.attrib}")
        #     for sub_child in child:
        #         print(f"sous-enfants de {child.tag}: {sub_child.tag} {sub_child.attrib}")
        #         print("!!! Si c'est comme le fichier, c'est OK !!!")
        #     else:
        #         print("Aucun autre enfants.")

        # La lecture doit se faire en binaire, vous devrez probablement
        # lire le contenu binaire et le parser avec ET.fromstring() :
        # allChanges = dict()
        # xml_content = self.__fd.read()
        # if not xml_content:
        #   return allChanges  # Fichier vide, retourne un dictionnaire vide
        # root = ET.fromstring(xml_content)
        # for devNode in root.findall("device"):
        # # ... (reste de la logique de parsing) ...
        # return allChanges

        # 4. Extrait la version du fichier de tâches à partir de l'instruction de traitement "taskcoach".
        # # Récupérer l'instruction de traitement à partir de `docinfo`
        # tskversion = 1  # Valeur par défaut
        # pis = tree.getroot().xpath("//processing-instruction()")
        # print(f"pis = {pis}")
        # print(f"Valeur de tskversion avant affectation : {tskversion}")
        # # for pi in pis:
        # #     if pi.target == "taskcoach":
        # #         # tskversion = int(pi.attrib.get("tskversion"))
        # #         try:
        # #             print(f"pi.attrib.get('tskversion') = {pi.attrib.get("tskversion")}")
        # #             tskversion = int(pi.attrib.get("tskversion"))  # Utiliser "1" si absent
        # #         except ValueError:
        # #             print(
        # #                 f"Erreur : tskversion invalide '{pi.attrib.get('tskversion')}', utilisation de la valeur par défaut 1.")
        # #             tskversion = 1
        # #         break   # Sortir après la première occurrence trouvée
        # if tree.docinfo.internalDTD:
        #     for pi in tree.docinfo.internalDTD.externalEntities():
        #         if pi.name == "taskcoach":
        #             try:
        #                 tskversion = int(pi.system_url.split("tskversion=")[-1])  # Extraire la version
        #             except ValueError:
        #                 print(
        #                     f"Erreur : tskversion invalide dans '{pi.system_url}', utilisation de la valeur par défaut 1.")
        #                 tskversion = 1
        #             break
        # parser.tskversion = root.attrib.get('tskversion')  # Récupère la version depuis l'attribut de la racine
        # if parser.tskversion is not None:
        #     try:
        #         parser.tskversion = int(parser.tskversion)
        #     except ValueError:
        #         parser.tskversion = 0  # Ou une autre valeur par défaut en cas d'erreur de conversion
        #     if parser.tskversion > meta.data.tskversion:
        #         raise XMLReaderTooNewException
        # else:
        #     parser.tskversion = 0  # Si l'attribut est absent

        # Affectation à l'attribut de l'instance
        # self.__tskversion = parser.tskversion  # pylint: disable=W0201
        self.__tskversion = tskversion  # Gemini utilise plutôt parser.tskversion !

        # print(f"XMLReader.read : Valeur de tskversion après affectation : {tskversion}, pas self.tskversion {parser.tskversion}!")
        # 5. Vérifie si la version du fichier est compatible avec la version de l'application Task Coach.
        # print(f"Version de l'application meta.data.tskversion = {meta.data.tskversion}")
        if self.__tskversion > meta.data.tskversion:
            # Version number of task file is too high
            wx.LogError("XMLReader.read : Version du fichier supérieur à celle de taskcoach !!!")
            raise XMLReaderTooNewException
        # else:
        #     print("XMLReader.read : DEBUG : Version du fichier inférieure ou égale à celle de taskcoach. OK")
        # 6. Appelle des méthodes privées pour parser les différents éléments du fichier :
        # * Analyse les nœuds de tâches.
        # print("XMLReader.read: 6. ANALYSE DES DIFFERENTS ELEMENTS DU FICHIER.")
        # print(f"XMLReader.read : 6.a Analyse des noeuds de tâche de : root = {root} avec _parse_task_nodes.")
        tasks = self.__parse_task_nodes(root)
        print(f"XMLReader.read : Tâches lues avec status: {[(the_task, the_task.id(), the_task.getStatus()) for the_task in tasks]}")
        # print(f"XMLReader.read : Résultat d'analyse des noeuds de tâche : tasks = {tasks}")
        # print(f"XMLReader.read : DEBUG - Après parsing : tasks[0].completed() = {tasks[0].completed()}")
        # * Résout les prérequis et les dépendances entre les tâches.
        # print(f"XMLReader.read : 6.b Analyse des prérequis et dépendances des noeuds de tâche de : tasks = {tasks} :")
        self.__resolve_prerequisites_and_dependencies(tasks)

        # * Analyse les nœuds de notes.
        # print(f"XMLReader.read : 6.c Analyse des noeuds de notes de root = {root} avec ")
        notes = self.__parse_note_nodes(root)
        # print(f"XMLReader.read : __parse_note_nodes : notes = {notes}")
        # # * (si version du fichier > 13) : Analyse les noeuds de catégories.
        # print(f"XMLReader.read : Version du fichier: {self.__tskversion} si <=13,"
        #       f" utilisation de __parse_category_nodes_from_task_nodes sinon __parse_category_nodes")
        # print(f"XMLReader.read : 6.d Analyse des noeuds de cateorie de root = {root} :")
        if self.__tskversion <= 13:
            # * (si version du fichier <= 13) : Analyse les catégories à partir des nœuds de tâches (ancienne version).
            categories = self.__parse_category_nodes_from_task_nodes(root)
        else:
            categories = self.__parse_category_nodes(root)
        # print(f"XMLReader.read : 📂 DEBUG - Catégories de la tâche 'subject': categories = {categories}")

        # print(f"DEBUG: XMLReader.read - Tâches extraites après lecture du XML : {[the_task.id() for the_task in tasks]}")
        # for the_task in tasks:
        #     print(f"DEBUG: Tâche {the_task.id()} - Enfants XML : {[child.id() for child in the_task.children()]}")
        # print(f"DEBUG: XMLReader.read - Catégories après lecture : ids = {[the_category.id() for the_category in categories]}")
        # print(f"DEBUG: XMLReader.read : Avant résolution des catégories, self.categories = {self.categories}")
        # * Associe les catégories aux tâches et aux notes.
        # print("XMLReader.read : Associe les catégories aux tâches et aux notes.")
        self.__resolve_categories(categories, tasks, notes)
        # print(f"DEBUG - Catégories lues après parsing: {categories}")
        # print(f"XMLReader.read : DEBUG: Après résolution des catégories, self.categories = {self.categories}")
        # print("XMLReader.read : Enregistre le GUID du noeud :")
        guid = self.__parse_guid_node(root.find("guid"))
        # guid_node = root.find('guid')
        # guid = self.__parse_guid_node(guid_node) if guid_node is not None else generate()
        # print(f"XMLReader.read : guid = {guid}")
        syncml_config = self.__parse_syncml_node(root, guid)
        # syncml_node = root.find('syncml')
        # syncml_config = self.__parse_syncml_node(syncml_node, guid) if syncml_node is not None else createDefaultSyncConfig(guid)

        # print(f"XMLReader.read : Enregistre le traitement du noeud syncml root dans syncml_config = {syncml_config}")

        # for object, modification_datetime in list(self.__modification_datetimes.items()):
        for the_object, modification_datetime in self.__modification_datetimes.items():
            # print(f"XMLReader.read : Règle la modification de date {modification_datetime} de l'objet {the_object}.")
            the_object.setModificationDateTime(modification_datetime)

        # changesName = self.__fd.name + ".delta"
        changesName = f"{self.__fd.name}.delta"
        # print(f"XMLReader.read : Création du nom de fichier changesName = {changesName}")
        # Si le chemin du fichier changesName existe, l'ouvrir en mode lecture :
        if os.path.exists(changesName):
            # file -> open ?
            # changes = ChangesXMLReader(
            #     open(self.__fd.name + ".delta", "r")
            # ).read()
            # Lire les informations de modification (changes) à partir d'un fichier XML de modifications Delta et enregistrer le résultat
            # changes = ChangesXMLReader(
            #     open(f"{self.__fd.name}.delta", "r")
            # ).read()
            # with open(changesName, "r") as fromChangesName:
            #     changes = ChangesXMLReader(fromChangesName).read()
            try:
                with open(changesName, 'rb') as delta_f:
                    changes = ChangesXMLReader(delta_f).read()
            except FileNotFoundError:
                changes = {}
            # print(f"XMLReader.read : Informations de modification lues du fichier delta : changes = {changes}")
        # Sinon
        else:
            changes = dict()
            # print(f"XMLReader.read : Création des Informations de modification du fichier delta : changes = {changes}")
        # print("XMLReader.read avant retour :")
        print(f"Tâches lues avant retour : {[(the_task.id(), the_task.status()) for the_task in tasks]}, tasks[0].completed() = {tasks[0].completed()}")
        # print(f"Catégories lues : {[the_category.id() for the_category in categories]}")
        # print(f"Notes lues : {[the_note.id() for the_note in notes]}")
        # print(f"Syncml_config lue : {[syncml_config]}")
        # print(f"changes lue : {[changes]}")
        # print(f"guid lue : {guid}")
        # for task in tasks:
        #     print(f"XMLReader.read : 🔍 DEBUG - Tâche {task.id()} | Catégories finales : {task.categories()}")
        #     for child in task.children():
        #         print(f"XMLReader.read : 🔍 DEBUG - Sous-tâche {child.id()} | Catégories finales : {child.categories()}")

        return tasks, categories, notes, syncml_config, changes, guid
        # avec try:
        # except ET.XMLSyntaxError as e:
        #     log.error(f"Erreur de syntaxe XML lors de la lecture de '{self.__fd.name}': {e}")
        #     raise
        # except Exception as e:
        #     log.error(f"Erreur inattendue lors de la lecture de '{self.__fd.name}': {e}")
        #     raise

    def __has_broken_lines(self):
        """Tskversion 24 peut contenir des nouvelles lignes dans les balises d'élément.

        * Vérifie si le fichier de tâches (version 24) contient des sauts de ligne incorrects dans les balises d'élément.
        """
        log.warning(f"XMLReader.__has_broken_lines : Type de self.__fd: {type(self.__fd)}")  # <class '_io.BufferedReader'>
        has_broken_lines = "><spds><sources><TaskCoach-\n" in self.__fd.read()  # TODO : Est-ce que le 'b' est indispensable ? Sinon le retirer !
        # content = self.__fd.read()
        # if isinstance(content, bytes):
        #     return b'><spds><sources><TaskCoach-\n' in content
        # else:
        #     return "><spds><sources><TaskCoach-\n" in content
        # has_broken_lines = "><spds><sources><TaskCoach-\n" in self.__fd.read().decode(encoding="utf-8")
        self.__fd.seek(0)
        # print(f"XMLReader.__has_broken_lines : has_broken_lines = {has_broken_lines}")
        return has_broken_lines

    def __fix_broken_lines(self):
        """ Supprimer les nouvelles lignes parasites des balises d’élément.

        * Corrige les sauts de ligne incorrects identifiés dans les balises d'élément du fichier de tâches.
        """
        # print(f"XMLReader.__fix_broken_lines : self.__fd avant changement = {self.__fd.read()}")
        # Remettre la lecture au début du fichier :
        self.__fd.seek(0)
        # Enregistre le fichier d'origine dans __origFd
        self.__origFd = self.__fd  # pylint: disable=W0201
        # content = self.__fd.read()
        # Utilise __fd comme mémoire buffer :
        # self.__fd = io.StringIO()
        self.__fd = io.BytesIO()  # TODO : ?
        # Donne le nom d'origine à __fd mémoire buffer :
        self.__fd.name = self.__origFd.name
        # Enregistre chaque ligne du fichier d'origine dans lines :
        lines = self.__origFd.readlines()
        # Pour chaque numéro de ligne index :
        for index in range(len(lines)):
            # Si la ligne finit par :
            if lines[index].endswith(b"<TaskCoach-\n") or lines[index].endswith(
                b"</TaskCoach-\n"
            ):
                lines[index] = lines[index][:-1]  # Remove newline
                lines[index + 1] = lines[index + 1][:-1]  # Remove newline
        # if isinstance(content, bytes):
        #     content = content.replace(b'><spds><sources><TaskCoach-\n', b'')
        # else:
        #     content = content.replace("><spds><sources><TaskCoach-\n", "")
        # Ré-écrire le résultat dans __fd
        self.__fd.write(b"".join(lines))
        # Retourne la tête de lecture/écriture au début :
        self.__fd.seek(0)
        # lgo.debug(f"XMLReader.__fix_broken_lines : self.__fd après changement = {self.__fd.read()}")
        # self.__fd.seek(0)

    #             *** Méthodes privées ***
    def __parse_task_nodes(self, node):
        """Analyser récursivement toutes les tâches du nœud et renvoyer une liste d'instances de tâches.

        * Analyse de manière récursive tous les noeuds de tâches de l'arbre XML et renvoie une liste d'instances de tâches.
        """
        # print(f"XMLReader.__parse_task_nodes : sur node = {node}")
        # Initialisation de la liste des instances de tâches.
        # task_return = [self.__parse_task_node(child) for child in node.findall("task")]
        # Pour tout avoir récursivement, il est peut-être préférable d'utiliser iter !? -> Non, ne fonctionne pas, c'est pire !
        # task_return = [self.__parse_task_node(child) for child in node.iter("task")]
        task_return = []
        # notes = [self.__parse_note_node(child) for child in node.findall("note")]
        for task_to_parse in node.findall("task"):  # Voir si ce ne serait plus rapide avec iter ?
            print(f"XMLReader.__parser_task_nodes : Parse le noeud {task_to_parse.tag} d'attributs {task_to_parse.attrib}.")
            task_parsed = self.__parse_task_node(task_to_parse)
            # log.debug(f"XMLReader.__parse_task_nodes : 🔍 Tâche créée : {task_parsed.id()} | Instance mémoire : {id(task_parsed)}")
            # for subchild in task_parsed.children():
            #     log.debug(f"XMLReader.__perse_task_nodes : 🔍 Enfant : {subchild.id()} | Instance mémoire : {id(subchild)}")
            task_return.append(task_parsed)  # Ajoute explicite de la tâche task_parsed à la liste de tâches
            # log.debug(f"XMLReader.__perse_task_nodes : ✅ Sous-Note ajoutée : {task_parsed.id()} dans la liste des tâches {task_return}")
        log.debug(f"XMLReader.__parser_task_nodes retourne la liste de tâches : {task_return}")
        return task_return

        # categories = []
        # for category_node in node.findall("category"):
        #     category = self.__parse_category_node(category_node)
        #     categories.append(category)
        #     print(f"✅ Catégorie ajoutée : {category.id()} dans la liste des catégories {categories}")
        #
        #     # 📌 Vérifie et ajoute les catégories imbriquées
        #     for child_category_node in category_node.findall("category"):
        #         child_category = self.__parse_category_node(child_category_node)   # 📌 Crée l'objet enfant
        #         category.addChild(child_category)  # 🟢 Ajoute la catégorie imbriquée comme enfant de la catégorie parent
        #         print(f"✅ Sous-catégorie ajoutée : {child_category.id()} sous {category.id()}")
        #
        # print(f"XMLReader.__parse_category_nodes : Liste des catégories : {categories}")
        # return categories

    def __resolve_prerequisites_and_dependencies(self, tasks):
        """ Remplacer toutes les conditions préalables par les instances de tâche réelles et définir les dépendances.

        Résout les prérequis et les dépendances entre les tâches.

        * Remplace les identifiants de prérequis par les instances de tâches correspondantes et définit les dépendances entre les tâches.
        """
        tasks_by_id = dict()
        # print(f"__resolve_prerequisites_and_dependencies qui ajoute le dictionnaire tasks_by_id = dict() à {tasks}")

        def collect_ids(the_tasks):
            """ Créez un mappage à partir des ID de tâche aux instances de tâche."""
            # print(f"XMLReader.__resolve_prerequisites_and_dependencies.collect_ids sur the_tasks = {the_tasks}:")
            for each_task in the_tasks:
                tasks_by_id[each_task.id()] = each_task
                # print(f"Pour chaque tâche each_task = {each_task}, tasks_by_id[each_task.id()] = {tasks_by_id[each_task.id()]}")
                collect_ids(each_task.children())
            # print(f"collect_ids : Résultat du mappage tasks_by_id = {tasks_by_id}")

        def resolve_ids(the_tasks):
            """ Remplacer tous les ID de prérequis par des instances de tâche réelles
            et définir les dépendances."""
            # print(f"XMLReader.__resolve_prerequisites_and_dependencies.resolve_ids sur the_tasks = {the_tasks}:")
            for each_task in the_tasks:
                if each_task.isDeleted():
                    # Ne restaurez pas les conditions préalables et les dépendances pour les tâches supprimées
                    for deleted_task in [each_task] + \
                                        each_task.children(recursive=True):
                        deleted_task.setPrerequisites([])
                    continue
                prerequisites = set()
                for prerequisiteId in self.__prerequisites.get(each_task.id(), []):
                    try:
                        prerequisites.add(tasks_by_id[prerequisiteId])
                    except KeyError:
                        # Release 1.2.11 and older have a bug where tasks can
                        # have prerequisites listed that don't exist anymore
                        pass
                each_task.setPrerequisites(prerequisites)
                for prerequisite in prerequisites:
                    prerequisite.addDependencies([each_task])
                resolve_ids(each_task.children())
                # print(f"resolve_ids : Résultat du remplacement en instances de each_task {each_task} : prerequisites = {prerequisites}")

        collect_ids(tasks)
        resolve_ids(tasks)

    def __resolve_categories(self, categories, tasks, notes):
        """
        Cartographier les catégories à leurs objets associés (catégorisables) et
        établir les relations entre eux. Cela garantit que les tâches,
        les notes et autres objets catégorisables sont correctement classés et
        que les catégories soient conscientes de leur contenu.

        * Associe les catégories aux tâches et aux notes correspondantes.
        * Établit les relations entre les catégories et les objets catégorisables (tâches, notes, etc.).
        * Garantit que les objets catégorisables soient correctement associés à leurs catégories et que les catégories soient informées de leur contenu.

        Args :
            categories (list[Category]) : Liste d'objets de catégorie analysés à partir du XML.
            tasks (list[Task]) : Liste d'objets de tâche analysés à partir du XML.
            notes (list[Note]) : Liste d'objets de note analysés à partir du XML.

        Behavior : (Comportement)
            - La méthode crée des dictionnaires de mappages pour tous les objets et catégories catégorisables.
            - Chaque catégorie est mise à jour pour inclure ses objets catégorisables connexes.
              Parcourt toutes les catégories, tâches et notes pour les ajouter aux dictionnaires de mappage respectifs.
            - Les événements sont déclenchés pour informer les changements dans les relations catégorisables de catégorie.
              Itère sur les relations catégorie-objet catégorisable stockées dans `self.__categorizables`.
                * Récupère la catégorie correspondante à l'identifiant (vérifie les clés absentes).
                * Récupère l'objet catégorisable associé à l'identifiant dans la carte des objets catégorisables (vérifie les clés absentes).
                * Ajoute l'objet catégorisable à la catégorie et inversement (déclenche des événements pour notifier les changements).

        Raises :
            KeyError : Si l'identifiant d'une catégorie référencée dans `self.__categorizables`
            n'est pas trouvé dans la carte de catégorie analysée.
        """
        # Initialisation de la carte des catégorisables :
        categorizableMap = dict()
        # Initialisation de la carte des catégories :
        categoryMap = dict()

        def mapCategorizables(obj, resultMap, categoryMap):
            """
            La méthode crée des dictionnaires de mappages pour tous les objets et catégories catégorisables.
            Associe les objets et catégories à leurs IDs dans les mappings.

            Args :
                obj : L'objet à catégoriser (tâche, note, etc.)
                resultMap : Dictionnaire pour mapper les objets catégorisables.
                categoryMap : Dictionnaire pour mapper les catégories. Variable qui contient les catégories.

            Returns :
                None
            """
            # lxml ne supporte pas les doublons !
            # Problème : Le code utilise des événements pour notifier
            # les changements dans les relations catégorisables de catégorie,
            # mais il n'y a pas de documentation claire sur la manière
            # dont ces événements sont gérés.
            # Solution : Documentez clairement la gestion des événements
            # et assurez-vous qu'ils sont correctement déclenchés et traités.
            # log.debug(f"XMLReader.__resolve_categories.mapCategorizables : appelé avec obj={obj}, obj.id()={obj.id()}, resultMap={resultMap}, categoryMap={categoryMap}")
            # print(self)

            # Si c'est un objet catégorisable (tâche, note, etc.), l'ajouter au resultMap
            if isinstance(obj, categorizable.CategorizableCompositeObject):
                # log.debug(f"XMLReader.__resolve_categories.mapCategorizables : ✅ Ajout de {obj}{obj.id()} à la liste des categorizables")
                resultMap[obj.id()] = obj  # Ajoute l'objet au mapping des objets catégorisables
                # log.debug(f"XMLReader.__resolve_categories.mapCategorizables : État actuel de resultMap après ajout des catégorisables : {resultMap}")

                # # 🔥 Ajout récursif des sous-tâches
                # # if hasattr(obj, "children"):
                # for subtask in obj.children(recursive=True):
                #     log.debug(f"📌 Ajout de la sous-tâche {subtask.id()} à resultMap")
                #     resultMap[subtask.id()] = subtask  # Assurer que la sous-tâche est bien mappée
                #     mapCategorizables(subtask, resultMap, categoryMap)  # Appel récursif

            # Si c'est une catégorie, l'ajouter au categoryMap immédiatement
            if isinstance(obj, category.Category):
                if obj.id() not in categoryMap:
                    # log.debug(f"XMLReader.__resolve_categories.mapCategorizables : ✅ Ajout immédiat de la catégorie {obj.id()} ({obj.subject()}) à la liste des catégories categoryMap")
                    categoryMap[obj.id()] = obj  # Ajoute la catégorie à la carte des catégories
                else:
                    # wx.LogDebug(f"XMLReader.__resolve_categories.mapCategorizables : 🔍 Catégorie déjà dans categoryMap: {obj.id()} ({obj.subject()})")
                    log.debug(f"XMLReader.__resolve_categories.mapCategorizables : 🔍 Catégorie déjà dans categoryMap: {obj.id()} ({obj.subject()})")
                # log.debug(f"XMLReader.__resolve_categories.mapCategorizables : État actuel de categoryMap après ajout des catégories = {categoryMap}")
                # # Gérer la récursivité des catégories
                # for subcategory in obj.children(recursive=True):
                #     log.debug(f"XMLReader.__resolve_categories.mapCategorizables : 🔄 Parcours de la sous-catégorie {subcategory.id()} ({subcategory.subject()})")
                #     mapCategorizables(subcategory, resultMap, categoryMap)

            # Vérifier si l'objet a des sous-tâches
            # Méthode à revoir car lxml peut gérer les enfants !
            if isinstance(obj, base.CompositeObject):
                # print(f"DEBUG: mapCategorizables ajoute les enfants de {obj.id()} à la liste resultMap en les renvoyant dans mapCategorizables.")
                for child in obj.children(recursive=True):
                    # print(f"DEBUG: Renvoi de l'enfant Child = {child.id()} dans mapCategorizables.")
                    mapCategorizables(child, resultMap, categoryMap)
                    # print(f"DEBUG: Après récursivité des enfants: resultMap = {resultMap}")

            # if isinstance(obj, base.NoteOwner):
            if isinstance(obj, note.NoteOwner):
                # log.deug(
                #     f"DEBUG: mapCategorizables ajoute les notes de {obj.id()} à la liste resultMap en les renvoyant dans mapCategorizables.")
                for child in obj.notes():
                    # log.debug(
                    #     f"✅ Ajout de la note {child.id()} (de {obj.notes()}) à la liste des catégories categoryMap via mapCategorizables.")
                    mapCategorizables(child, resultMap, categoryMap)
            # if isinstance(obj, base.AttachmentOwner):
            if isinstance(obj, attachment.AttachmentOwner):
                # log.debug(
                #     f"DEBUG: mapCategorizables ajoute les pièces jointes de {obj.id()} à la liste resultMap en les renvoyant dans mapCategorizables.")
                for theAttachment in obj.attachments():
                    if theAttachment is not None:  # Vérifier si la pièce jointe n'est pas None
                        # log.debug(
                        #     f"✅ Ajout immédiat de la pièce jointe {theAttachment.id()} ({obj.attachments()}) à la liste des catégories categoryMap")
                        mapCategorizables(theAttachment, resultMap, categoryMap)

        # Chaque catégorie est mise à jour pour inclure ses objets catégorisables connexes.
        # Parcourt toutes les catégories, tâches et notes pour les ajouter aux dictionnaires de mappage respectifs.
        # Cartographie toutes les catégories, tâches et notes à leurs cartes respectives
        # log.debug("XMLReader.__resolve_categories :")
        # log.debug(f"DEBUG: Avant mapCategorizables - Catégories : {[c.id() for c in categories]}")
        # log.debug(f"DEBUG: Avant mapCategorizables - Tâches : {[t.id() for t in tasks]}")
        # log.debug(f"DEBUG: Avant mapCategorizables - Notes : {[n.id() for n in notes]}")
        for theCategory in categories:
            # log.debug(f"DEBUG - Ajout de la catégorie {theCategory.id()} dans categorizableMap")
            # log.debug(f"🔍 Vérification de la catégorie {theCategory.id()}, catégories = {theCategory.categories()}")
            # log.debug(f"🔍 Vérification de la catégorie {theCategory.id()}, catégorisables = {theCategory.categorizables()}")
            mapCategorizables(theCategory, categorizableMap, categoryMap)
            # NON : categories est utilisé autrement !!!
            # self.categories[theCategory.id()] = theCategory
            # log.debug(f"✅ Ajout de la catégorie {theCategory} à self.categories")
            # # log.debug(f"✅ Ajout de la catégorie {theCategory.id()} à self.categories")
        # log.debug(f"self.categories = {self.categories}")
        # log.debug("DEBUG: Après mapCategorizables - Catégories :")
        # log.debug(f"Liste des catégories : categoryMap = {categoryMap}")
        # log.debug(f"Liste des catégorisables : categorizablesMap = {categorizableMap}")

        for theTask in tasks:
            # log.debug(f"DEBUG - Ajout de la tâche {theTask.id()} dans categorizableMap")
            # log.debug(f"🔍 Vérification de la tâche {theTask.id()}, catégories = {theTask.categories()}")
            # log.debug(f"DEBUG: Tâche {theTask.id()} - Enfants : {[child.id() for child in theTask.children()]}")
            mapCategorizables(theTask, categorizableMap, categoryMap)
            # # 🚨 Vérification : est-ce que la sous-tâche 1.1 est bien enregistrée ?
            # for child in theTask.children():
            #     log.debug(f"📌 La tâche {theTask.id()} contient l'enfant : {child.id()}")
            # log.debug("DEBUG: Après mapCategorizables - Tâches :")
            # log.debug(f"Liste des catégories : categoryMap = {categoryMap}")
            # log.debug(f"Liste des catégorisables : categorizablesMap = {categorizableMap}")
        for theNote in notes:
            # log.debug(f"🔍 Vérification de la note {theNote.id()}, catégories = {theNote.categories()}")
            mapCategorizables(theNote, categorizableMap, categoryMap)
            # log.debug("DEBUG: Après mapCategorizables - Notes :")
            # log.debug(f"Liste des catégories : categoryMap = {categoryMap}")
            # log.debug(f"Liste des catégorisables : categorizablesMap = {categorizableMap}")
        # Faut-il le faire pour les pièces jointes ?

        # print(f"DEBUG: Contenu final de categorizableMap : {categorizableMap}")
        # print(f"et de categoryMap : {categoryMap}")

        # Les événements sont déclenchés pour informer les changements dans les relations catégorisables de catégorie.
        event = patterns.Event()

        # Itère sur les relations catégorie-objet catégorisable stockées dans `self.__categorizables`.
        # for categoryId, categorizableIds in list(self.__categorizables.items()):
        # print(f"DEBUG: Contenu de self.__categorizables avant l'association : {self.__categorizables}")
        # print(f"DEBUG: Contenu de self.categories avant l'association : {self.categories}")
        # print("continue si vide !")
        # print(f"__resolve_categories : DEBUG - categoryMap = {categoryMap}")
        # print(f"DEBUG - Vérification self.__categorizables : {self.__categorizables}")

        # Pour chaque catégorie avec liste des objets catégorisables dans la liste des catégorisables :
        for categoryId, categorizableIds in self.__categorizables.items():
            # for categoryId, categorizableIds in list(self.__categorizables.items()):
            # log.debug(f"🛠 DEBUG - Tentative d'assignation de la catégorie {categoryId} aux objets {categorizableIds}")
            if not categorizableIds:
                # wx.LogWarning(
                #     f"⚠️ Avertissement : La catégorie {categoryId} n'a pas d'objets catégorisables associés, elle sera ignorée.")
                log.warning(
                    f"⚠️ Avertissement : La catégorie {categoryId} n'a pas d'objets catégorisables associés, elle sera ignorée.")
                continue
            try:
                # * Récupère la catégorie correspondante à l'identifiant (vérifie les clés absentes).
                if categoryId not in categoryMap:
                    # wx.LogWarning(f"XMLReader.__resolve_categories : ⚠️ Catégorie introuvable dans categoryMap : {categoryId}")
                    log.warning(f"XMLReader.__resolve_categories : ⚠️ Catégorie introuvable dans categoryMap : {categoryId}")
                else:
                    # wx.LogDebug(f"XMLReader.__resolve_categories : 🟢 Catégorie trouvée : {categoryId} -> categoryMap : {categoryMap}")
                    log.debug(f"XMLReader.__resolve_categories : 🟢 Catégorie trouvée : {categoryId} -> categoryMap : {categoryMap}")

                # print(f"__resolve_categories : Création de theCategory = categoryMap[categoryId] pour categoryId = {categoryId}")
                theCategory = categoryMap[categoryId]  # KeyError de categoryID
                # log.debug(f"theCategory = {theCategory}")
                # log.debug("Création de getted_category = self.categories.get(categoryId)")
                # getted_category = self.categories.get(categoryId)
                # log.debug(f"getted_category = {getted_category}")
                if theCategory:  #
                    # print(f"Résolution de theCategory={theCategory} : categoryId {categoryId}, objets categorisableIds {categorizableIds}")
                    for categorizableId in categorizableIds:
                        # log.debug(f"DEBUG - Contenu actuel de categorizableMap : {categorizableMap}")
                        # log.debug(
                        #     f"DEBUG - Recherche de l'objet catégorisable {categorizableId} pour la catégorie {categoryId}")

                        if categorizableId not in categorizableMap:
                            # wx.LogWarning(f"XMLReader.__resolve_categories : ⚠️ Objet catégorisable {categorizableId} introuvable dans categorizableMap")
                            log.warning(f"XMLReader.__resolve_categories : ⚠️ Objet catégorisable {categorizableId} introuvable dans categorizableMap")
                            # wx.LogError(
                            #     f"XMLReader.__resolve_categories : ⚠️ ERREUR - Impossible de trouver l'objet {categorizableId} dans categorizablesMap !")
                            log.error(
                                f"XMLReader.__resolve_categories : ⚠️ ERREUR - Impossible de trouver l'objet {categorizableId} dans categorizablesMap !")
                        if categorizableId in categorizableMap:
                            # log.debug(f"Pour categorizableId={categorizableId} dans categorizableMap={categorizableMap},")
                            # * Récupère l'objet catégorisable associé à l'identifiant dans la carte des objets catégorisables (vérifie les clés absentes).
                            theCategorizable = categorizableMap[categorizableId]
                            # log.debug(f"theCategorizable = {theCategorizable}")
                            # log.debug(f"🔍 DEBUG - Assignation de {theCategory.subject()} à {theCategorizable.subject()}")
                            # getted_categorizable = self.objects.get(categorizableId)  # ajouté via gémini
                            # log.debug(f"getted_categorizable = {getted_categorizable}")
                            if theCategorizable:
                                # * Ajoute l'objet catégorisable à la catégorie et inversement (déclenche des événements pour notifier les changements).
                                # log.debug(f"Ajout de l'objet categorizableId {categorizableId} à la catégorieId {categoryId}")
                                # log.debug(f"✅ Ajout de theCategorizable.subject()={theCategorizable.subject()} à theCategory.subject()={theCategory.subject()}")
                                # log.debug(f"Avant ajout avec addCategorizable: theCategory.categorizables() = {theCategory.categorizables()}")
                                theCategory.addCategorizable(theCategorizable)
                                # log.debug(f"✅ Liste des objets de theCategory après ajout : theCategory.categorizables() = {theCategory.categorizables()}")
                                #
                                # log.debug(f"🟢 Ajout de la catégorieId {categoryId} à l'objet catégorizableId {categorizableId}")
                                # log.debug(f"Avant ajout : theCategorizable.categories() = {theCategorizable.categories()}")
                                theCategorizable.addCategory(theCategory, event=event)
                                # log.debug(f"Après ajout : theCategorizable.categories() = {theCategorizable.categories()}")
                                # log.debug(
                                #     f"🔍 DEBUG - Catégories de {theCategorizable.subject()} après ajout = {theCategorizable.categories()}")
                                #
                                # log.debug(
                                #     f"🟢 Catégorie '{theCategory.subject()}' bien assignée à '{theCategorizable.subject()}'")
                                #
                                # # Debugging output
                                # log.debug(f"Category ID: {categoryId}, Categorizable ID: {categorizableId}")
                            else:
                                # wx.LogDebug(f"XMLReader.__resolve_categories : Objet manquant : {categorizableId}")
                                log.debug(f"XMLReader.__resolve_categories : Objet manquant : {categorizableId}")
            # KeyError : Si l'identifiant d'une catégorie référencée dans `self.__categorizables`
            #            n'est pas trouvé dans la carte de catégorie analysée.
            except KeyError as e:
                # Enregistre la catégorie manquante ou catégorisable
                # wx.LogError(f"XMLReader.__resolve_categories : !!!Error: Missing category or categorizable for ID {e}")
                log.error(f"XMLReader.__resolve_categories : !!!Error: Missing category or categorizable for ID {e}")
        # log.debug(f"🛠 DEBUG - Assignation des catégories : {self.categories}")

        # for task in tasks:
        #     log.debug(f"Vérification 🔍 DEBUG - Avant setCategories() | Task {task.id()} | Catégories actuelles = {task.categories()}")
        #     for child in task.children():
        #         log.debug(
        #             f"Vérification 🔍 DEBUG - Avant setCategories() | Sous-tâche {child.id()} | Catégories actuelles = {child.categories()}")

        for a_task in tasks:
            # log.debug(f"FORCAGE 🔍 DEBUG - Avant setCategories() | Task {task.id()} | Catégories actuelles = {task.categories()}")
            # task.setCategories(set(task.categories()))  # Force l'affectation
            a_task.setCategories(a_task.categories() | set(a_task.categories()))
            # log.debug(f"🔍 DEBUG - Après setCategories() | Task {task.id()} | Catégories finales = {task.categories()}")
        # for obj in tasks + notes:
        #     log.debug(f"🔍 DEBUG - Après résolution, {obj.id()} a les catégories {obj.categories()}")

        # Send the event to notify changes
        # Envoie l'événement pour notifier des changements :
        event.send()

    def __parse_category_nodes(self, node):
        """
        Analyse de manière récursive tous les nœuds de catégorie de l'arbre XML
        et renvoie une liste d'instances de catégorie.

        On considère à la fois les nœuds <category> directement sous le nœud et ceux dans <categories>.

        Extrait toutes les catégories.
        Ensuite, il faut associer les sous-catégories à leurs parents.

        Args :
            node :

        Returns :
            categories_extracted : Liste des catégories extraites.
        """
        # return [self.__parse_category_node(child)
        #         for child in node.findall("category")]
        # categories_extracted = [self.__parse_category_node(child) for child in node.findall("category")]
        # print(f"DEBUG - XMLReader.__parse_category_nodes : root = {ET.tostring(node, pretty_print=True).decode()}")

        # Récupère toutes les catégories
        # Combine les catégories trouvées directement et celles sous <categories>
        # category_nodes = node.findall("categories/category")
        category_nodes = node.findall("category") + node.findall("categories/category")
        # print(f"DEBUG - __parse_category_nodes : category_nodes trouvés = {category_nodes}")

        # print(f"XMLReader.__parse_category_nodes: Catégories extraites : {categories_extracted}")  # Debug
        # for theCategory in categories_extracted:
        #     parent = theCategory.parent()  # Récupère le parent de la catégorie
        #     if parent and parent.id() in self.categories:  # Vérifie que le parent existe
        #         print(f"Ajout de la sous-catégorie {theCategory} à {parent}")  # Debug
        #         parent.addChild(theCategory)  # Ajoute la sous-catégorie au parent
        #
        # return categories_extracted
        # print(f"XMLReader.__parse_category_nodes pour node = {node}:")

        categories = []
        # categories = [self.__parse_category_node(child) for child in node.findall("category")]

        # 📌 **Boucle sur toutes les catégories trouvées**
        # for child in node.findall("categories/category"):
        for child in category_nodes:
            # print(f"🔍 DEBUG - Analyse du nœud catégorie : {ET.tostring(child, pretty_print=True).decode()}")
            theCategory = self.__parse_category_node(child)
            # theCategory = self.__parse_category_node(child, node)
            # print(f"DEBUG - Catégorie analysée : {theCategory}, id={theCategory.id() if theCategory else 'None'}")
            # Vérifier si la catégorie a été bien créée
            if theCategory is None:
                # wx.LogWarning(f"XMLReader.__parse_category_nodes : ⚠️ WARNING - self.__parse_category_node() a retourné None pour {child}")
                log.warning(f"XMLReader.__parse_category_nodes : ⚠️ WARNING - self.__parse_category_node() a retourné None pour {child}")
                # continue  # Ignore cette catégorie et passe à la suivante
            else:
                # category_id = child.attrib.get("id", None)
                # print(f"DEBUG - Catégorie détectée : id={category_id}")  # Vérifie si l'ID est bien extrait
                # print(f"✅ DEBUG - Catégorie analysée : {theCategory}, id={category_id}")
                # if category_id:  # Vérifie si l'ID est valide
                # acategory = category.Category(category_id)
                # categoryMap[category_id] = acategory
                # categoryMap[category_id] = acategory  # Utilisation de self.categoryMap au lieu de categoryMap
                # print(f"✅ DEBUG - Catégorie analysée : {theCategory}, id={category_id}")
                # print(
                #     f"✅ DEBUG - Catégorie ajoutée à self.categoryMap : {category_id} -> {acategory}")  # Vérifie si l'ajout est bien fait
                # **Ajout dans `self.categories`**
                # self.categories[theCategory.id()] = theCategory
                categories.append(theCategory)
                # print(f"✅ DEBUG - Catégorie ajoutée : {theCategory.id()} dans self.categories")
            # else:
            #     print(f"⚠️ WARNING - Catégorie ignorée car ID invalide : {child}")

            # # 📌 Vérifie et ajoute les sous-catégories
            # for child_category_node in child.findall("category"):
            #     child_category = self.__parse_category_node(child_category_node)   # 📌 Crée l'objet enfant
            #     if child_category :
            #         theCategory.addChild(child_category)  # 🟢 Ajoute la catégorie imbriquée comme enfant de la catégorie parent
            #         print(f"✅ Sous-catégorie ajoutée : {child_category.id()} sous {theCategory.id()}")
            #         # print(f"📂 Catégorie: {theCategory.subject()}, Enfants: {[c.subject() for c in theCategory.children()]}")

        # print(f"XMLReader.__parse_category_nodes : ✅ Liste des catégories ajouté à categories : {categories}")
        # print(f"XMLReader.__parse_category_nodes : DEBUG - Catégories trouvées: {categories}")
        # print(f"📂 DEBUG - Liste finale des catégories dans __parse_category_nodes() : {categories}")
        return categories

    def __parse_note_nodes(self, node):
        """Parses all notes within a given XML node and returns a list of Note instances.
        Analyse de manière récursive tous les noeuds de note de l'arbre XML et renvoie une liste d'instances de note.

        Args :
            node :

        Returns :
            Liste d'instances de note.
        """
        # return [self.__parse_note_node(child) for child in node.findall("note")]
        # print(f"XMLReader.__parse_note_nodes pour node = {node}:")
        notes = []
        # notes = [self.__parse_note_node(child) for child in node.findall("note")]
        for child in node.findall("note"):  # Voir si ce ne serait plus rapide avec iter ?
            child_note = self.__parse_note_node(child)
            notes.append(child_note)  # Ajoute explicite de l'enfant child_note à la liste de notes
            # print(f"✅ Sous-Note ajoutée : {child_note.id()} dans la liste des notes {notes}")
        #
        #   # Inutile ? Non, les notes peuvent aussi avoir des enfants !
        #   # 📌 Vérifie et ajoute les notes imbriquées
        #     for child_note_node in child.findall("note"):
        #         sub_child_note = self.__parse_note_node(child_note_node)
        #         notes.append(sub_child_note)  # 🟢 Ajoute la note imbriquée comme enfant de la note parent
        #         print(f"✅ Sous-Note imbriquée ajoutée : {sub_child_note.id()} sous {notes}")

        # print(f"XMLReader.__parse_note_nodes : Retourne la liste des notes ajoutées : {notes}")
        return notes

    def __parse_category_node(self, category_node):
        """ Analyser récursivement les catégories du nœud et renvoyer une instance de catégorie.

        * Analyse un nœud XML de catégorie et retourne une instance de `category.Category`.
            * Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
            * Analyse les notes associées à la catégorie à l'aide de `__parse_note_nodes`.
            * Récupère et analyse les attributs `filtered` et `exclusiveSubcategories` (booléens).
            * Construit un dictionnaire avec les informations extraites.
            * Gère différemment l'attribut `categorizables` selon la version du fichier de tâches.
            * Analyse les pièces jointes si la version du fichier de tâches est supérieure à 20.
            * Crée et retourne une instance de `category.Category` en utilisant le dictionnaire d'arguments.
            * Enregistre la date de modification de la catégorie à l'aide de `__save_modification_datetime`.
        Analyse un nœud XML de catégorie et retourne une instance de `category.Category`.

        Récupère les attributs de base et les notes associées, ainsi que les indicateurs
        'filtered' et 'exclusiveSubcategories'. Les tâches associées (categorizables)
        ne sont pas traitées ici mais seront associées plus tard dans __resolve_categories.
        """
        # Récupérer l'ID de la catégorie depuis le nœud XML
        # print(f"📂 DEBUG - Début analyse de la catégorie {ET.tostring(category_node, pretty_print=True).decode()}")
        # print(f"XMLReader.__parse_category_node : récupère l'ID de la catégorie {category_node} depuis le nœud XML :")
        # category_id = category_node.attrib.get("id")
        # print(f"category_id = {category_id}")

        # Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
        # print(f"XMLReader.__parse_category_node : Récupère les attributs de base du nœud composite {category_node} à l'aide de `__parse_base_composite_attributes`.")
        kwargs = self.__parse_base_composite_attributes(category_node,
                                                        self.__parse_category_nodes)
        # print(f"kwargs = {kwargs}")
        if not kwargs:
            # wx.LogWarning(
            #     f"⚠️ WARNING - __parse_base_composite_attributes a retourné un dictionnaire vide pour {category_node}")
            log.warning(
                f"⚠️ WARNING - __parse_base_composite_attributes a retourné un dictionnaire vide pour {category_node}")

        # Analyse les notes directement associées à la catégorie à l'aide de `__parse_note_nodes`.
        # print(f"XMLReader.__parse_category_node : Récupère les notes directes du nœud {category_node}.")
        notes = self.__parse_note_nodes(category_node)
        # print(f"notes = {notes}")
        # Récupère et analyse les attributs `filtered` et `exclusiveSubcategories` (indicateurs booléens).
        filtered = self.__parse_boolean(
            category_node.attrib.get("filtered", "False")
        )
        exclusive = self.__parse_boolean(
            category_node.attrib.get("exclusiveSubcategories", "False")
        )
        # Construit un dictionnaire avec les informations extraites. Met à jour les arguments.
        kwargs.update(
            dict(
                notes=notes,
                filtered=filtered,
                exclusiveSubcategories=exclusive,
            )
        )
        # print(f"🔍 DEBUG - kwargs avant création de Category : {kwargs}")

        # Pour la rétrocompatibilité : selon la version du fichier, l'attribut contenant les
        # identifiants des objets catégorisables est "tasks" ou "categorizables".
        # Gère différemment l'attribut `categorizables` selon la version du fichier de tâches.
        if self.__tskversion < 19:
            categorizable_ids = category_node.attrib.get("tasks", "")
        else:
            categorizable_ids = category_node.attrib.get("categorizables", "")
        # categorizable_ids = category_node.attrib.get("categorizables", "") if self.__tskversion >= 19 else category_node.attrib.get("tasks", "")
        # Analyse les pièces jointes si la version du fichier de tâches est supérieure à 20.
        # Pour les versions > 20, on analyse aussi les pièces jointes.
        if self.__tskversion > 20:
            kwargs["attachments"] = self.__parse_attachments(category_node)

        # ✅ Vérifier si la catégorie existe déjà pour éviter de la recréer
        # NON, une catégorie est unique dans le cheminement XML!
        # if category_id in self.categories:
        #     print(f"🔄 Catégorie déjà existante détectée : {self.categories[category_id].subject()} (ID: {category_id})")
        #     return self.categories[category_id]  # On renvoie la catégorie existante

        # Crée l'objet Category
        # 🔹 Si la catégorie n'existe pas encore, on la crée normalement
        # Crée et retourne une instance de `category.Category` en utilisant le dictionnaire d'arguments.
        # theCategory = category.Category(**kwargs)  # pylint: disable=W0142
        try:
            theCategory = category.Category(**kwargs)
            # print(f"✅ DEBUG - Catégorie créée avec succès : {theCategory}")
        except Exception as e:
            # wx.LogError(f"❌ ERREUR - Impossible de créer la catégorie : {e}")
            log.error(f"❌ ERREUR - Impossible de créer la catégorie : {e}")
            return None

        # Ajoute cette catégorie dans le mapping des catégories de l'instance (pour y accéder plus tard)
        self.categories[theCategory.id()] = theCategory  # Ajout immédiat à self.categories
        # print(f"DEBUG - Ajout dans self.__categorizables[{theCategory.id()}] = {categorizable_ids.split(' ')}")

        # # Récupère les tâches associées à cette catégorie via les nœuds <category>test</category>
        # task_ids = [
        #     task_node.attrib.get("id") for task_node in
        #     category_node.findall(f".//task[category='{category_node.attrib['id']}']")
        # ]
        #
        # # print(
        # #     f"DEBUG - Vérification : self.__categorizables[{theCategory.id()}] = {self.__categorizables[theCategory.id()]}")
        #
        # # Ajoute ces tâches aux catégorisables
        # self.__categorizables.setdefault(theCategory.id(), list()).extend(task_ids)

        # Stocke (même si c'est vide) la liste des identifiants catégorisables pour cette catégorie
        # print(
        #     f"DEBUG - Association catégories/tâches : self.__categorizables[{theCategory.id()}] = {self.__categorizables[theCategory.id()]}")
        self.__categorizables.setdefault(theCategory.id(), list()).extend(categorizable_ids.split(" "))
        # self.__categorizables.setdefault(theCategory.id(), list()).extend(
        #     [id_ for id_ in categorizable_ids.split(" ") if id_]
        # )
        # Vérification du parent
        # Vérifier que l'association parent/enfant est bien gérée :
        # parent_id = category_node.get("parent")  # Obtenir l'ID du parent
        # if parent_id and parent_id in self.categories:
        #     parent = self.categories[parent_id]
        #     print(f"Ajout de {category.subject()} comme sous-catégorie de {parent.subject()}")  # Debug
        #     parent.addChild(theCategory)  # Associer la sous-catégorie au parent

        # parent_node = category_node.getparent()
        # if parent_node is not None and parent_node.tag == "category":
        #     parent_id = parent_node.attrib.get("id")
        #     print(f"DEBUG: parent_node.attrib = {parent_node.attrib}")  # Debug
        #     if parent_id in self.categories:
        #         parent_category = self.categories[parent_id]
        #         print(
        #             f"✅ Ajout de {theCategory.subject()} comme sous-catégorie de {parent_category.subject()}")  # Debug
        #         parent_category.addChild(theCategory)  # Ajout au parent
        #     else:
        #         print(f"⚠️ Info : le parent {parent_id} n'existe pas dans self.categories !")  # Debug
        # # Enregistre la date de modification de la catégorie à l'aide de `__save_modification_datetime`.
        # for cat in self.categories.values():
        #     print(f"📂 Catégorie: {cat.subject()}, Enfants: {[c.subject() for c in cat.children()]}")
        # if theCategory is None:
        #     print("⚠️ WARNING - La création de category.Category a échoué !")
        # else:
        #     print(f"✅ DEBUG - Catégorie créée avec succès : {theCategory}")

        return self.__save_modification_datetime(theCategory)

    def __parse_category_nodes_from_task_nodes(self, root):
        """In tskversion <=13 category nodes were subnodes of task nodes.

        * Utilisée pour les versions de fichier <= 13 où les catégories étaient des sous-nœuds des tâches.
        * Récupère tous les nœuds de tâche et construit un mappage entre les identifiants de tâche et les catégories associées.
        * Crée un mappage distinct pour les catégories uniques.
        * Associe les catégories aux tâches via `self.__categorizables`.
        * Retourne une liste des objets `category.Category` créés.

        Args :
            root : Noeud racine.

        Returns :

        """
        task_nodes = root.findall(".//task")
        category_mapping = self.__parse_category_nodes_within_task_nodes(task_nodes)
        subject_category_mapping = {}
        # for task_id, categories in category_mapping.items():
        for task_id, categories in list(category_mapping.items()):
            for subject in categories:
                if subject in subject_category_mapping:
                    cat = subject_category_mapping[subject]
                else:
                    cat = category.Category(subject)
                    subject_category_mapping[subject] = cat
                self.__categorizables.setdefault(cat.id(), list()).append(task_id)
        # return subject_category_mapping.values()
        # print(f"XMLReader.__parse_category_nodes_from_task_nodes : DEBUG - Catégories trouvées: {subject_category_mapping}")
        return list(subject_category_mapping.values())

    # @staticmethod
    def __parse_category_nodes_within_task_nodes(self, task_nodes):
        """ In tskversion <=13 category nodes were subnodes of task nodes.

        * Méthode statique (ou anciennement statique) pour parser les nœuds de catégorie imbriqués dans les nœuds de tâche.
        * Construit et retourne un dictionnaire mappant les identifiants de tâche à une liste de noms de catégorie.

        Args :
            task_nodes :

        Returns :
            category_mapping (dict) : Dictionnaire des identifiants de tâche associé à une liste de noms de catégorie.
        """
        category_mapping = {}
        for node in task_nodes:
            task_id = node.attrib["id"]
            categories = [child.text for child in node.findall("category")]
            category_mapping.setdefault(task_id, []).extend(categories)
        # print(f"XMLReader.__parse_category_nodes_within_task_nodes : DEBUG - Catégories trouvées: category_mapping = {category_mapping}")
        return category_mapping

    def __parse_task_node(self, task_node):
        """Analyser récursivement le nœud et renvoyer une instance de tâche.

        * Parse un nœud XML de tâche et retourne une instance de `task.Task`.
        * Gère la rétrocompatibilité pour l'attribut `planned_start_datetime_attribute_name` (nom différent selon la version).
        * Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
        * Parse et ajoute les attributs spécifiques aux tâches (dates, pourcentage d'achèvement, budget, priorité, frais, rappel, etc.).
        * Ignore les prérequis pour le moment (ils seront résolus ultérieurement).
        * Parse les efforts, les notes et la récurrence associés à la tâche.
        * Parse les pièces jointes si la version du fichier de tâches est supérieure à 20.
        * Enregistre les prérequis dans `self.__prerequisites` pour une résolution ultérieure.
        * Crée et retourne une instance de `task.Task` en utilisant le dictionnaire d'arguments.
        * Enregistre la date de modification de la tâche à l'aide de `__save_modification_datetime`.

        Args :
            task_node : Noeud XML de tâche à analyser.

        Returns :
            theTask : L'instance de la tâche contenant un dictionnaire d'arguments.
        """

        # log.debug(f"XMLReader.__parse_task_node : Analyse récursive du noeud tâche {task_node} pour  self.tskversion = {self.tskversion} :")
        planned_start_datetime_attribute_name = (
            "startdate" if self.tskversion() <= 33 else "plannedstartdate"
        )
        # print(f"XMLReader.__parse_task_node : {planned_start_datetime_attribute_name} = startdate si self.tskversion <=33, sinon = plannedstartdate")
        # print(f"XMLReader.__parse_task_node : task_node = {task_node}, self.__parse_task_nodes = {self.__parse_task_nodes}")
        kwargs = self.__parse_base_composite_attributes(
            task_node, self.__parse_task_nodes
        )
        # print(f"📂 DEBUG - Tâche '{kwargs['subject']}' reçoit les tâches : {kwargs.get('task_node', set())}")
        #
        # print(f"Si {task_node} est un Element, alors on peut utiliser tag (task_node.tag = {task_node.tag}) et attrib (task_node.attrib = {task_node.attrib} ")
        # print(f"XMLReader.__parse_task_node : kwargs = {kwargs}")
        # print(f"XMLReader.__parse_task_node : Attributs du task_node = {task_node.attrib}")
        # print(f"XMLReader.__parse_task_node : Status extrait = {task_node.attrib.get('status', '1')}")
        # print("!!! UPDATE DE kwargs !!!")
        # print(
        #     f"🔍 DEBUG - Status brut avant conversion : {task_node.attrib.get('status')} ({type(task_node.attrib.get('status'))})")
        kwargs.update(
            dict(
                plannedStartDateTime=date.parseDateTime(
                    task_node.attrib.get(
                        planned_start_datetime_attribute_name, ""
                    ),
                    *self.defaultStartTime
                ),
                dueDateTime=parseAndAdjustDateTime(
                    task_node.attrib.get("duedate", ""), *self.defaultEndTime
                ),
                actualStartDateTime=date.parseDateTime(
                    task_node.attrib.get("actualstartdate", ""),
                    *self.defaultStartTime
                ),
                completionDateTime=date.parseDateTime(
                    task_node.attrib.get("completiondate", ""),
                    *self.defaultEndTime
                ),
                percentageComplete=self.__parse_int_attribute(
                    task_node, "percentageComplete"
                ),
                budget=date.parseTimeDelta(task_node.attrib.get("budget", "")),
                priority=self.__parse_int_attribute(task_node, "priority"),
                hourlyFee=float(task_node.attrib.get("hourlyFee", "0")),
                fixedFee=float(task_node.attrib.get("fixedFee", "0")),
                reminder=self.__parse_datetime(
                    task_node.attrib.get("reminder", "")
                ),
                reminderBeforeSnooze=self.__parse_datetime(
                    task_node.attrib.get("reminderBeforeSnooze", "")
                ),
                # Ignore prerequisites for now, they'll be resolved later. Where and when ?
                prerequisites=[],
                shouldMarkCompletedWhenAllChildrenCompleted=self.__parse_boolean(
                    task_node.attrib.get(
                        "shouldMarkCompletedWhenAllChildrenCompleted", ""
                    )
                ),
                efforts=self.__parse_effort_nodes(task_node),
                notes=self.__parse_note_nodes(task_node),
                recurrence=self.__parse_recurrence(task_node),

                # 🔹 Ajout de l'attribut status
                status=task_node.attrib.get("status", "inactive"),  # Par défaut 1 si absent
            )
        )
        # print(f"XMLReader.__parse_task-node : kwargs['completionDateTime']={kwargs['completionDateTime']}")

        # print(f"XMLReader.__parse_task_node : kwargs updated = {kwargs}")
        # kwargs["status"] = status  # Mise à jour
        # print(f"XMLReader.__parse-task-node : ✅ DEBUG - Status après kwargs.update et conversion en int : {kwargs['status']} ({type(kwargs['status'])})")

        self.__prerequisites[kwargs["id"]] = [
            id_
            for id_ in task_node.attrib.get("prerequisites", "").split(" ")
            if id_
        ]
        if self.__tskversion > 20:
            kwargs["attachments"] = self.__parse_attachments(task_node)
        # return self.__save_modification_datetime(
        #     task.Task(**kwargs)
        # )  # pylint: disable=W0142
        # print(f"XMLReader.__parse_task_node : 🛠 FINAL kwargs avant création de la tâche : {kwargs}")
        # 🔹 Création de l'instance de tâche à renvoyer
        # print("Création de la tâche.")
        # task_id = task_node.get("id")
        # print(f"🔍 DEBUG - Tentative de création de la tâche {task_id}")
        # if task_id in self.__parsed_tasks:
        #     print(f"⚠️ La tâche {task_id} existe déjà, on ne la recrée pas.")
        #     return self.__parsed_tasks[task_id]
        # print(f"📂 DEBUG - Avant création de Task subject='{kwargs['subject']}', catégories={kwargs.get('categories', set())}")
        # print(f"XMLReader.__parse_task_node : 📂 DEBUG - Avant création de Task subject='{kwargs['subject']}', status={kwargs.get('status')}")
        theTask = self.__save_modification_datetime(task.Task(**kwargs))
        # self.__parsed_tasks[task_id] = theTask  # Stocker la tâche pour éviter de la recréer
        # print(f"✅ Tâche créée : {task_id} | Instance mémoire : {id(task)}")
        # print(f"XMLReader.__parse_task_node : avant les sous-tâches, theTask = {theTask}, type={type(theTask)}, status={theTask.status()}, getstatus={theTask.getStatus()}")
        if theTask is None or theTask == "":
            # wx.LogDebug(f"!!! ATTENTION la tâche {theTask} est VIDE !!!")
            log.debug(f"!!! ATTENTION la tâche {theTask} est VIDE !!!")
        # print(f"XMLReader.__parse_task_node : theTask.id = {theTask.id}")
        # print("XMLReader.__parse_task_node : theTask.tag = ERREUR")
        # print("XMLReader.__parse_task_node : theTask.text = ERREUR")
        # print(f"XMLReader.__parse_task_node : theTask.text = ERREUR")
        # print(f"XMLReader.__parse_task_node : theTask.text = {theTask.text}")

        # Traitement des catégories en ligne dans la tâche
        for cat_node in task_node.findall("category"):
            # Si l'attribut id n'est pas défini, utiliser le texte du nœud
            cat_id = cat_node.attrib.get("id")
            if not cat_id:
                if cat_node.text:
                    cat_id = cat_node.text.strip()
                else:
                    continue  # Si aucun texte, ignorer
            # Ajoute l'id de la tâche dans le mapping des catégories associées
            self.__categorizables.setdefault(cat_id, []).append(theTask.id())

        # # 🔹 Ajout des sous-tâches
        # for sub_task_node in task_node.findall("task"):  # Trouve les sous-tâches
        #     sub_task = self.__parse_task_node(sub_task_node)  # Crée la sous-tâche
        #     theTask.addChild(sub_task)  # L'ajoute à la tâche parente
        print(f"XMLReader.__parse_task_node : Retourne la tâche theTask = {theTask}{theTask.id} de status {theTask.status()}")
        return theTask

    def __parse_recurrence(self, task_node):
        """ Parse the recurrence from the node and return a recurrence
            instance.

        * Parse les informations de récurrence à partir du nœud et retourne une instance de `date.Recurrence`.
        * Utilise différentes méthodes de parsing selon la version du fichier de tâches (inférieure ou supérieure à 19).
        * Délègue le parsing à `__parse_recurrence_attributes_from_task_node` (pour les versions <= 19) ou `__parse_recurrence_node` (pour les versions >= 20).
        """
        # print(f"XMLReader.__parse_recurrence : task_node = {task_node}")
        if self.__tskversion <= 19:
            parse_kwargs = self.__parse_recurrence_attributes_from_task_node
        else:
            parse_kwargs = self.__parse_recurrence_node
        # print(f"XMLReader.__parse_recurrence : résultat parse_kwargs = {parse_kwargs}")
        # print(f"XMLReader.__parse_recurrence : retourne {date.Recurrence(**parse_kwargs(task_node))}")
        return date.Recurrence(**parse_kwargs(task_node))

    def __parse_recurrence_node(self, task_node):
        """Since tskversion >= 20, recurrence information is stored in a
        separate node.

        * Parse les informations de récurrence stockées dans un nœud séparé (à partir de la version 20).
        * Extrait les attributs `unit`, `amount`, `count`, `max`, `stop_datetime`, `sameWeekday` et `recurBasedOnCompletion` du nœud "recurrence".
        * Retourne un dictionnaire contenant les informations de récurrence.
        """
        kwargs = dict(
            unit="",
            amount=1,
            count=0,
            maximum=0,
            stop_datetime=None,
            sameWeekday=False,
        )
        node = task_node.find("recurrence")
        if node is not None:
            kwargs = dict(
                unit=node.attrib.get("unit", ""),
                amount=int(node.attrib.get("amount", "1")),
                count=int(node.attrib.get("count", "0")),
                maximum=int(node.attrib.get("max", "0")),
                stop_datetime=self.__parse_datetime(
                    node.attrib.get("stop_datetime", "")
                ),
                sameWeekday=self.__parse_boolean(
                    node.attrib.get("sameWeekday", "False")
                ),
                recurBasedOnCompletion=self.__parse_boolean(
                    node.attrib.get("recurBasedOnCompletion", "False")
                ),
            )
        return kwargs

    @staticmethod
    def __parse_recurrence_attributes_from_task_node(task_node):
        """
        Dans Tskversion <= 19, les informations de récurrence ont été stockées
        sous forme d'attributs des nœuds de tâche.

        * Méthode (anciennement statique) pour parser les informations de récurrence stockées directement dans les attributs du nœud de tâche (versions <= 19).
        * Extrait les attributs `recurrence`, `recurrenceCount`, `recurrenceFrequency` et `maxRecurrenceCount`.

        Returns :
            Un dictionnaire contenant les informations de récurrence.
        """
        # print(f"__parse_recurrence_attributes_from_task_node : pour task_node={task_node}")
        return dict(
            unit=task_node.attrib.get("recurrence", ""),
            count=int(task_node.attrib.get("recurrenceCount", "0")),
            amount=int(task_node.attrib.get("recurrenceFrequency", "1")),
            maximum=int(task_node.attrib.get("maxRecurrenceCount", "0")),
        )

    def __parse_note_node(self, note_node):
        """ Analyser les attributs et les notes des enfants du nœud de note.

        * Analyse un nœud XML de note et retourne une instance de `note.Note`.
        * Récupère les attributs de base du nœud composite à l'aide de `__parse_base_composite_attributes`.
        * Parse les pièces jointes si la version du fichier de tâches est supérieure à 20.
        * Enregistre la date de modification de la note à l'aide de `__save_modification_datetime`.
        """
        kwargs = self.__parse_base_composite_attributes(note_node,
                                                        self.__parse_note_nodes)

        if self.__tskversion > 20:
            kwargs["attachments"] = self.__parse_attachments(note_node)
            # theNote.setAttachments(self.__parse_attachments(note_node))  # ✅ Ajoute les pièces jointes si nécessaire

        theNote = note.Note(**kwargs)  # ✅ Créer l'objet Note AVANT d'ajouter les enfants

        # # Ajoute les sous-notes en tant qu'enfants
        # for child_node in note_node.findall("note"):
        #     child_note = self.__parse_note_node(child_node)
        #     theNote.addChild(child_note)  # Ajout explicite de l'enfant ✅ Maintenant, addChild() fonctionne !
        #     print(f"✅ Ajout de la sous-note {child_note.id()} sous {theNote.id()}")

        # return self.__save_modification_datetime(
        #     note.Note(**kwargs)
        # )  # pylint: disable=W0142
        return self.__save_modification_datetime(theNote)  # ✅ Retourne un vrai objet Note

    def __parse_base_attributes(self, node):
        """
        Analyser les attributs que tous les objets de domaine composite partagent,
        tels que l'id, le sujet, la description et les renvoyer en tant que dictionnaire de mots clés
        qui peut être transmis au constructeur d'objets de domaine.

        * Analyse les attributs communs à tous les objets de domaine composites (id, date de création, date de modification, sujet, description, couleurs, police, icône, etc.).
        * Gère la rétrocompatibilité pour l'attribut de couleur de fond (`color` ou `bgColor`).
        * Gère la rétrocompatibilité pour les pièces jointes (présentes dans les versions <= 20).
        * Analyse l'attribut `status` (présent à partir de la version 22).

        Returns :
            dict attributes : Un dictionnaire contenant ces attributs.
        """
        log.debug(f"XMLReader.__parse_base_attributes : dans self={self} pour le noeud node={node}")
        bg_color_attribute = "color" if self.__tskversion <= 27 else "bgColor"
        # Dictionnaire des attributs du nœud node.
        attributes = dict(
            id=node.attrib.get("id", ""),
            creationDateTime=self.__parse_datetime(
                node.attrib.get("creationDateTime", "1-1-1 0:0")
            ),
            modificationDateTime=self.__parse_datetime(
                node.attrib.get("modificationDateTime", "1-1-1 0:0")
            ),
            subject=node.attrib.get("subject", ""),
            description=self.__parse_description(node),
            fgColor=self.__parse_tuple(node.attrib.get("fgColor", ""), None),
            bgColor=self.__parse_tuple(
                node.attrib.get(bg_color_attribute, ""), None
            ),
            font=self.__parse_font_description(node.attrib.get("font", "")),
            icon=self.__parse_icon(node.attrib.get("icon", "")),
            selectedIcon=self.__parse_icon(
                node.attrib.get("selectedIcon", "")
            ),
            ordering=int(node.attrib.get("ordering", "0")),
        )

        if self.__tskversion <= 20:
            attributes["attachments"] = (
                self.__parse_attachments_before_version21(node))
        if self.__tskversion >= 22:
            attributes["status"] = int(node.attrib.get("status", "1"))

        log.debug(f"__parse_base_attributes : retourne attributes={attributes}")
        return attributes

    def __parse_base_composite_attributes(self, node, parse_children,
                                          *parse_children_args):
        """ Identique à __parse_base_attributes, mais analyse également les enfants
        et les contextes étendus.

        * Analyse les attributs de base (comme `__parse_base_attributes`) et ajoute également le parsing des enfants et des contextes étendus.
        * Appelle `__parse_base_attributes` pour récupérer les attributs de base.
        * Parse les enfants à l'aide de la fonction `parse_children` fournie en argument.
        * Parse les contextes étendus à partir de l'attribut `expandedContexts`.
        * Retourne un dictionnaire contenant tous les attributs.
        """
        # Récupère les attributs de base :
        kwargs = self.__parse_base_attributes(node)
        # Ajoute également le parsing des enfants et des contextes étendus.
        # Analyse les enfants à l'aide de la fonction `parse_children` fournie en argument.
        kwargs["children"] = parse_children(node, *parse_children_args)
        # Parse les contextes étendus à partir de l'attribut `expandedContexts`.
        expanded_contexts = node.attrib.get("expandedContexts", "")
        kwargs["expandedContexts"] = self.__parse_tuple(expanded_contexts, [])
        # Retourne un dictionnaire contenant tous les attributs.
        return kwargs

    def __parse_attachments_before_version21(self, parent):
        """ Analyser les pièces jointes à partir du nœud et renvoyer les instances de pièce jointe.

        * Parse les pièces jointes pour les versions de fichier antérieures à 21.
        * Construit le chemin vers le répertoire des pièces jointes en se basant sur le nom du fichier de tâches.
        * Itère sur les nœuds "attachment" et crée des instances de `attachment.AttachmentFactory`.
        * Gère les différences entre les anciennes et les nouvelles versions pour la création des pièces jointes.
        * Gère les erreurs d'entrée/sortie (IOError) pour les pièces jointes (par exemple, les pièces jointes de courriel).
        """
        # Construit le chemin vers le répertoire des pièces jointes en se basant sur le nom du fichier de tâches.
        path, name = os.path.split(os.path.abspath(self.__fd.name))  # pylint: disable=E1103
        name = os.path.splitext(name)[0]
        # attdir = os.path.normpath(os.path.join(path, name + "_attachments"))
        attdir = os.path.normpath(os.path.join(path, f"{name}_attachments"))

        # Liste des pièces jointes :
        # Itère sur les nœuds "attachment" et crée des instances de `attachment.AttachmentFactory`.
        attachments = []
        for node in parent.findall("attachment"):
            # Gère les différences entre les anciennes et les nouvelles versions pour la création des pièces jointes.
            if self.__tskversion <= 16:
                args = (node.text,)
                kwargs = dict()
            else:
                args = (os.path.join(attdir, node.find("data").text),
                        node.attrib["type"])
                description = self.__parse_description(node)
                kwargs = dict(subject=description,
                              description=description)
            try:
                # Crée des instances de `attachment.AttachmentFactory`.
                # pylint: disable=W0142
                attachments.append(attachment.AttachmentFactory(*args,
                                                                **kwargs))
                # # Vérifie si 'location' est None avant de créer un attachement
                # if location:
                #     if location is not None:
                #         attachments.append(attachment.AttachmentFactory(location, *args, **kwargs))
                #     else:
                #         print("⚠️ WARNING - Un attachement avec une location None a été ignoré")
                # else:
                #     print("⚠️ WARNING - Un attachement sans location a été ignoré !")

            except IOError:
                # Gère les erreurs d'entrée/sortie (IOError) pour les pièces jointes (par exemple, les pièces jointes de courriel).
                # Mail attachment, file doesn't exist. Ignore this.
                pass
        return attachments

    def __parse_effort_nodes(self, node):
        """ Parse all effort records from the node.

        * Parse tous les enregistrements d'effort du nœud et les retourne sous forme de liste.
                * Utilise `__parse_effort_node` pour parser chaque enregistrement individuel.

        """
        return [self.__parse_effort_node(effort_node)
                for effort_node in node.findall("effort")]

    def __parse_effort_node(self, node):
        """ Parse an effort record from the node.

        * Parse un enregistrement d'effort individuel à partir du nœud.
        * Récupère et analyse les attributs `start`, `stop` et `description`.
        * Gère l'attribut `status` (présent à partir de la version 22) et l'attribut `id` (présent à partir de la version 29).
        * Crée et retourne une instance de `effort.Effort`.
        * L'attribut `task` est initialisé à `None` et sera défini ultérieurement pour éviter des envois d'événements indésirables.
        """
        kwargs = {}
        if self.__tskversion >= 22:
            kwargs["status"] = int(node.attrib.get("status", "1"))
        if self.__tskversion >= 29:
            kwargs["id"] = node.attrib["id"]
        start = node.attrib.get("start", "")
        stop = node.attrib.get("stop", "")
        description = self.__parse_description(node)
        # task=None because it is set when the effort is actually added to the
        # task by the task itself. This way no events are sent for changing the
        # effort owner, which is good.
        # pylint: disable=W0142
        return effort.Effort(task=None, start=date.parseDateTime(start),
                             stop=date.parseDateTime(stop), description=description, **kwargs)

    def __parse_syncml_node(self, nodes, guid):
        """ Parse the SyncML node from the nodes.

        * Parse le nœud SyncML et retourne la configuration SyncML.
        * Crée une configuration par défaut à l'aide de `createDefaultSyncConfig`.
        * Recherche le nœud SyncML (nom différent selon la version du fichier).
        * Appelle `__parse_syncml_nodes` pour parser les nœuds enfants.

        """
        syncml_config = createDefaultSyncConfig(guid)

        node_name = "syncmlconfig"
        if self.__tskversion < 25:
            node_name = "syncml"

        for node in nodes.findall(node_name):
            self.__parse_syncml_nodes(node, syncml_config)
        return syncml_config

    def __parse_syncml_nodes(self, node, config_node):
        """ Parse les noeuds SyncML depuis le noeud node.

        * Parse récursivement les nœuds SyncML.
        * Traite les nœuds "property" en définissant les propriétés correspondantes dans la configuration.
        * Traite les autres nœuds en créant des nœuds de configuration enfants et en appelant récursivement `__parse_syncml_nodes`.
        """
        for child_node in node:
            if child_node.tag == "property":
                config_node.set(
                    child_node.attrib["name"], self.__parse_text(child_node)
                )
            else:
                for child_config_node in config_node.children():
                    if child_config_node.name == child_node.tag:
                        break
                else:
                    tag = child_node.tag
                    child_config_node = SyncMLConfigNode(tag)
                    config_node.addChild(child_config_node)
                self.__parse_syncml_nodes(child_node, child_config_node)

    def __parse_guid_node(self, node):
        """ Parse the GUID from the node.

        * Parse le nœud GUID et retourne le GUID.
        * Extrait et nettoie le texte du nœud.
        * Génère un nouveau GUID si aucun n'est trouvé.
        """
        # Problème : Le code génère des GUID si aucun n'est trouvé,
        # mais il n'y a pas de garantie que ces GUID seront uniques.
        # Solution : Envisagez d'utiliser une bibliothèque dédiée
        # pour la génération de GUID, comme uuid.
        # Si, justement, guid !
        guid = self.__parse_text(node).strip()
        return guid if guid else generate()
        # if node is not None and node.text:
        #     return node.text
        # return generate()

    def __parse_attachments(self, node):
        """ Analyser les pièces jointes du nœud.

        * Analyse les pièces jointes d'un nœud.
        * Itère sur les nœuds "attachment" et appelle `__parse_attachment` pour chaque pièce jointe.
        * Gère les erreurs d'entrée/sortie (IOError).
        """
        attachments = []
        for child_node in node.findall("attachment"):
            try:
                attachments.append(self.__parse_attachment(child_node))
            except IOError as IOErr:
                # wx.LogError(f"XMLReader.__parse_attachments : IOErr = {IOErr}")
                log.error(f"XMLReader.__parse_attachments : IOErr = {IOErr}")
                pass
        return attachments

    def __parse_attachment(self, node):
        """ Analyser la pièce jointe du nœud.

        * Analyse une pièce jointe individuelle.
        * Récupère les attributs de base à l'aide de `__parse_base_attributes`.
        * Parse les notes associées à la pièce jointe.
        * Gère différemment l'attribut `location` selon la version du fichier.
        * Pour les versions <= 22, construit le chemin vers le fichier de la pièce jointe.
        * Pour les versions > 22, gère les pièces jointes dont les données sont directement incluses dans le XML.
        * Crée un fichier temporaire pour les données de pièces jointes incluses.
        * Définit les permissions du fichier temporaire sur lecture seule pour Windows.
        * Crée et retourne une instance de `attachment.AttachmentFactory`.
        * Enregistre la date de modification de la pièce jointe à l'aide de `__save_modification_datetime`."""

        # Création d'un dictionnaire d'attributs
        kwargs = self.__parse_base_attributes(node)
        kwargs["notes"] = self.__parse_note_nodes(node)

        # Problème : Un fichier temporaire est créé pour stocker les données
        # de pièces jointes, mais il n'y a pas de garantie que le fichier soit
        # supprimé après utilisation.
        # Solution : Utilisez un gestionnaire de contexte (with) pour garantir
        # que le fichier temporaire soit supprimé après utilisation.
        if self.__tskversion <= 22:
            path, name = os.path.split(os.path.abspath(
                self.__fd.name))  # pylint: disable=E1103
            name, ext = os.path.splitext(name)
            # attdir = os.path.normpath(
            #     os.path.join(path, name + "_attachments")
            # )
            attdir = os.path.normpath(
                os.path.join(path, f"{name}_attachments")
            )
            location = os.path.join(attdir, node.attrib["location"])
        else:
            if "location" in node.attrib:
                location = node.attrib["location"]
            else:
                data_node = node.find("data")

                if data_node is None:
                    raise ValueError(
                        "Neither location or data are defined "
                        "for this attachment."
                    )

                data = self.__parse_text(data_node)
                ext = data_node.attrib["extension"]

                location = sessiontempfile.get_temp_file(suffix=ext)
                # file -> open ?
                # open(location, "wb").write(data.decode("base64"))
                with open(location, "wb") as to_location:
                    # to_location.write(data.decode("base64"))
                    to_location.write(base64.b64decode(data))  # ✅ Compatible Python 3
                # log.debug(f"XMLReader.__parse_attachment(): écriture de {data} dans {location}")

                # Problème : Les permissions du fichier temporaire sont
                # modifiées pour être en lecture seule sur Windows,
                # mais cette logique n'est pas testée sur d'autres systèmes d'exploitation.
                # Solution : Testez cette logique sur différents systèmes
                # d'exploitation ou envisagez une solution plus portable.
                if os.name == "nt":
                    os.chmod(location, stat.S_IREAD)

        # # Vérifie si 'location' est None avant de créer un attachement
        # if location is not None:
        #     attachments.append(attachment.AttachmentFactory(*args, location, **kwargs))
        # else:
        #     print("⚠️ WARNING - Un attachement avec une location None a été ignoré")

        return self.__save_modification_datetime(
            attachment.AttachmentFactory(
                location,  # pylint: disable=W0142
                node.attrib["type"],
                **kwargs
            )
        )

    def __parse_description(self, node):
        """Analyser la description du nœud.

        * Parse la description à partir du nœud.
        * Traite différemment la description selon la version du fichier de tâches (avant ou après la version 6).
        * Pour les versions <= 6, récupère l'attribut "description" directement.
        * Pour les versions > 6, utilise `__parse_text` pour extraire le texte du nœud "description".
        """
        if self.__tskversion <= 6:
            description = node.attrib.get("description", "")
        else:
            description = self.__parse_text(node.find("description"))
        return description

    def __parse_text(self, node):
        """Analyser le texte d'un nœud.

        * Supprime les sauts de ligne en début et fin de texte pour les versions >= 24.

        Returns :
            Une chaîne vide si le nœud est `None` ou si son texte est vide.
        """
        # TODO : A revoir !
        # text = "" if node is None else node.text or ""
        text = "" if (node is None or "") else node.text
        if self.__tskversion >= 24:
            # Strip newlines
            if text.startswith("\n"):
                text = text[1:]
            if text.endswith("\n"):
                text = text[:-1]
        return text

    @classmethod
    def __parse_int_attribute(cls, node, attribute_name, default_value=0):
        """Analyser le nœud entier avec le nom spécifié d'attribut.
        En cas d'échec, renvoyez la valeur par défaut.

        * Analyse un attribut entier d'un nœud.
        * Utilise une valeur par défaut "0" en cas d'échec du parsing.

        """
        # Obtenir la valeur d'attribute_name de la liste des attributs de node
        # text = 0 en cas d'échec.
        text = node.attrib.get(attribute_name, "0")
        # essayer : text = node.attrib.get(attribute_name, f"{default_value}")
        return cls.__parse(text, int, default_value)

    @classmethod
    def __parse_datetime(cls, text):
        """ Analyser une datetime à partir du texte.

        * Analyse une date et une heure à partir du texte.
        * Utilise `__parse` avec la fonction `date.parseDateTime`.
        """
        return cls.__parse(text, date.parseDateTime, None)

    def __parse_font_description(self, text, default_value=None):
        """ Analyser une police du texte. En cas d'échec, renvoyez la valeur par défaut

        * Parse une description de police à partir du texte.
        * Crée un objet `wx.Font` à partir de la description.
        * Ajuste la taille de la police si elle est inférieure à 4.
        * Retourne la police ou la valeur par défaut en cas d'échec.
        """
        if text:
            # font = wxadv.FontFromNativeInfoString(text)  # Obsolète
            font = wx.Font(text)
            if font and font.IsOk():
                if font.GetPointSize() < 4:
                    font.SetPointSize(self.__default_font_size)
                return font
        return default_value

    @staticmethod
    def __parse_icon(text):
        """ Analyser un nom d'icône du texte.

        * Parse un nom d'icône à partir du texte.
        * Corrige un nom d'icône spécifique ("clock_alarm").
        """
        # Parse is a big word, we just need to fix one particular icon
        return "clock_alarm_icon" if text == "clock_alarm" else text

    @classmethod
    def __parse_boolean(cls, text, default_value=None):
        """ Analyser un booléen du texte. En cas d'échec, renvoyer la valeur par défaut

        * Parse un booléen à partir du texte.
        * Convertit les chaînes "True" et "False" en booléens.
        * Lève une exception `ValueError` si le texte n'est pas "True" ou "False".
        """

        def text_to_boolean(text):
            """Transformer 'True' en True et 'False' en False,

            soulever une valeur d'erreur pour tout autre texte.
            """
            if text in ("True", "False"):
                return text == "True"
            else:
                # raise ValueError("Expected 'True' or 'False', got '%s'" % text)
                raise ValueError(f"Expected 'True' or 'False', got '{text}'")

        return cls.__parse(text, text_to_boolean, default_value)

    @classmethod
    def __parse_tuple(cls, text, default_value=None):
        """Analyser un tuple du texte. En cas d'échec, renvoyez la valeur par défaut.

        * Parse un tuple à partir du texte.
        * Utilise `eval` pour convertir le texte en tuple si le texte commence par "(" et se termine par ")".
        * Retourne la valeur par défaut en cas d'échec.
        """
        # Utilisation de eval dans __parse_tuple (potentiellement dangereux, il vaudrait mieux ast.literal_eval).
        if text.startswith("(") and text.endswith(")"):
            # Problème : La méthode __parse_tuple utilise eval pour convertir
            # une chaîne en tuple. Cela peut poser des problèmes de sécurité
            # si la chaîne est malveillante.
            # Utilisez une méthode plus sûre pour parser les tuples,
            # comme ast.literal_eval.
            return cls.__parse(text, eval, default_value)
        else:
            return default_value

    @staticmethod
    def __parse(text, parse_function, default_value):
        """ Analyser le texte à l'aide de la fonction d'analyse.

        En cas de défaillance, retourne la valeur par défaut.

        * Méthode générique pour parser du texte à l'aide d'une fonction de parsing.
        * Gère les exceptions `ValueError` et retourne une valeur par défaut en cas d'échec.
        """
        try:
            return parse_function(text)
        except ValueError:
            return default_value

    def __save_modification_datetime(self, item):
        """ Enregistrez la date de modification de l'heure de l'élément pour la restauration ultérieure.

        * Enregistre la date et l'heure de modification d'un élément pour une restauration ultérieure.
        * Stocke la date et l'heure dans le dictionnaire `self.__modification_datetimes`.
        * Retourne l'élément.
        """
        # Problème : Le code enregistre les dates de modification des objets dans un dictionnaire,
        # mais il n'y a pas de garantie que ces dates seront correctement restaurées.
        # Solution : Envisagez d'utiliser un gestionnaire de contexte
        # ou une autre méthode pour garantir que les dates de modification soient correctement restaurées
        self.__modification_datetimes[item] = item.modificationDateTime()
        # log.debug(f"XMLReader.__save_modification_datetime: Enregistre {item}.modificationDateTime() = {self.__modification_datetimes[item]}"
        #           f" dans {self}.__modification_datetimes[{item}] "
        #           f"et retourne item = {item}")
        return item


class ChangesXMLReader(object):
    """
    Lire les informations de modification (changes) à partir d'un fichier XML de modifications Delta (`*.delta`).
    * **`__init__(self, fd)` :** Initialise le lecteur avec un descripteur de fichier (`fd`).
    * **`read()` :**
        * Parse l'arbre XML du fichier de modifications.
        * Pour chaque périphérique (`device`), récupère l'identifiant (`guid`) et crée un objet `ChangeMonitor`.
        * Pour chaque objet (`obj`), récupère l'identifiant et les modifications (sous forme de liste de chaînes séparées par des virgules).
        * Définit les modifications dans l'objet `ChangeMonitor`.
        * Stocke l'objet `ChangeMonitor` dans un dictionnaire avec l'identifiant du périphérique comme clé.
        * Retourne le dictionnaire contenant tous les objets `ChangeMonitor`.
    """
    def __init__(self, fd):
        """
        Initialise le lecteur avec un descripteur de fichier (`fd`).

        Args :
            fd : Descripteur de fichier.
        """
        self.__fd = fd

    def read(self):
        """
        Parse l'arbre XML du fichier de modifications.
        * Pour chaque périphérique (`device`), récupère l'identifiant (`guid`) et crée un objet `ChangeMonitor`.
        * Pour chaque objet (`obj`), récupère l'identifiant et les modifications (sous forme de liste de chaînes séparées par des virgules).
        * Définit les modifications dans l'objet `ChangeMonitor`.
        * Stocke l'objet `ChangeMonitor` dans un dictionnaire avec l'identifiant du périphérique comme clé.
        * Retourne le dictionnaire contenant tous les objets `ChangeMonitor`.

        Returns :
            allChanges (dict) : Dictionnaire de tout les changements.
        """
        # allChanges = dict()
        # # tree = eTree.parse(self.__fd)
        # tree = ET.parse(self.__fd)
        # for devNode in tree.getroot().findall("device"):
        #     id_ = devNode.attrib["guid"]
        #     mon = ChangeMonitor(id_)
        #     for objNode in devNode.findall("obj"):
        #         if objNode.text:
        #             changes = set(objNode.text.split(","))
        #         else:
        #             changes = set()
        #         mon.setChanges(objNode.attrib["id"], changes)
        #     allChanges[id_] = mon
        # return allChanges

        # Création d'un dictionnaire de tous les changements à renvoyer :
        allChanges = dict()
        # Création du lecteur de fd :
        xml_content = self.__fd.read()
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8', errors='replace')
        if not xml_content.strip():
            return allChanges  # Fichier vide, retourne un dictionnaire vide
        try:
            root = ET.fromstring(xml_content.encode('utf-8'))
            for devNode in root.findall("device"):
                id_ = devNode.attrib["guid"]
                mon = ChangeMonitor(id_)
                for objNode in devNode.findall("obj"):
                    if objNode.text:
                        changes = set(objNode.text.split(","))
                    else:
                        changes = set()
                    mon.setChanges(objNode.attrib["id"], changes)
                allChanges[id_] = mon
        # except ET.XMLSyntaxError:
        except SyntaxError:
            log.error(f"Fichier de changements delta corrompu ou vide: {self.__fd.name}")
            return allChanges
        except Exception as e:
            log.exception(f"Erreur inattendue lors de la lecture du fichier delta '{self.__fd.name}': {e}")
            return allChanges
        return allChanges


class TemplateXMLReader(XMLReader):
    """
    Classe pour lire les fichiers de modèles XML.

    * Hérite de `XMLReader`.

    Méthodes :
    * **read() : **
        * Appelle la méthode `read()` de la classe parente (`XMLReader`) et retourne la première tâche lue.
    * **`__parse_task_node(self, task_node)` :**
        * Surcharge la méthode `__parse_task_node` de la classe parente pour gérer les modèles.
        * Stocke les valeurs des attributs de date et heure dans des attributs dédiés (`<attribut>tmpl`).
        * Traduit l'attribut `subject` à l'aide de `translate`.
        * Appelle la méthode `__parse_task_node` de la classe parente pour parser les autres attributs.
        * Restaure les valeurs originales des attributs de date et heure à partir des attributs dédiés.
        * Retourne la tâche parsée.
    * **`convert_old_format(expr, now=date.Now)` :**
        * Méthode statique pour convertir les expressions de modèle d'ancien format en nouveau format.
        * Gère les modèles intégrés (par exemple, "Now()", "Today()").
        * Évalue les expressions de date et calcule le delta par rapport à la date actuelle.
        * Formatte le delta en une chaîne (par exemple, "10 minutes ago", "30 minutes from Now").

    """
    def read(self):
        """
        Appelle la méthode `read()` de la classe parente (`XMLReader`) et retourne la première tâche lue.

        Returns :
            La première tâche lue.
        """
        return super().read()[0][0]

    def __parse_task_node(self, task_node):
        """
        * Surcharge la méthode `__parse_task_node` de la classe parente pour gérer les modèles.
        * Stocke les valeurs des attributs de date et heure dans des attributs dédiés (`<attribut>tmpl`).
        * Traduit l'attribut `subject` à l'aide de `translate`.
        * Appelle la méthode `__parse_task_node` de la classe parente pour parser les autres attributs.
        * Restaure les valeurs originales des attributs de date et heure à partir des attributs dédiés.
        * Retourne la tâche parsée.

        Args :
            task_node : 3Nœud de tâche à parser/analyser.

        Returns :
            La tâche parsée.
        """
        log.debug(f"TemplateXMLReader.__parse_task_node : dans self={self} pour task_node={task_node}")
        attrs = dict()
        attribute_renames = dict(startdate="plannedstartdate")
        for name in [
            "startdate",
            "plannedstartdate",
            "duedate",
            "completiondate",
            "reminder",
        ]:
            new_name = attribute_renames.get(name, name)
            # template_name = name + "tmpl"
            template_name = f"{name}tmpl"
            if template_name in task_node.attrib:
                if self.tskversion() < 32:
                    value = TemplateXMLReader.convert_old_format(
                        task_node.attrib[template_name])
                else:
                    value = task_node.attrib[template_name]
                attrs[new_name] = value
                task_node.attrib[new_name] = str(
                    nlTimeExpression.parseString(value).calculatedTime)
            elif new_name not in attrs:
                attrs[new_name] = None
        if "subject" in task_node.attrib:
            task_node.attrib["subject"] = translate(
                task_node.attrib["subject"]
            )
        parsed_task = super().__parse_task_node(task_node)
        for name, value in list(attrs.items()):
            # setattr(parsed_task, name + "tmpl", value)
            setattr(parsed_task, f"{name}tmpl", value)
        return parsed_task

    @staticmethod
    def convert_old_format(expr, now=date.Now):
        """
        * Méthode statique pour convertir les expressions de modèle d'ancien format en nouveau format.
        * Gère les modèles intégrés (par exemple, "Now()", "Today()").
        * Évalue les expressions de date et calcule le delta par rapport à la date actuelle.
        * Formatte le delta en une chaîne (par exemple, "10 minutes ago", "30 minutes from Now").

        Args :
            expr : Expressions de modèle d'ancien format à convertir.
            now : Heure et Date de maintenant.

        Returns :
            Les expressions de modèle d'ancien format en nouveau format.
        """
        # Built-in templates:
        built_in_templates = {
            "Now()": "Now",
            "Now().endOfDay()": "11:59 PM Today",
            "Now().endOfDay() + oneDay": "11:59 PM Tomorrow",
            "Today()": "00:00 AM Today",
            "Tomorrow()": "11:59 PM Tomorrow",
        }
        if expr in built_in_templates:
            return built_in_templates[expr]
        # Not a built in template:
        new_datetime = eval(expr, date.__dict__)
        if isinstance(new_datetime, date.date.RealDate):
            new_datetime = date.DateTime(new_datetime.year, new_datetime.month,
                                         new_datetime.day)
        delta = new_datetime - now()
        minutes = int(delta.minutes())
        if minutes < 0:
            # return "%d minutes ago" % (-minutes)
            return f"{-minutes:d} minutes ago"
        else:
            # return "%d minutes from Now" % minutes
            return f"{minutes:d} minutes from Now"
