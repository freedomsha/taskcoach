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

Ce fichier définit une métaclasse qui génère dynamiquement des méthodes
pour gérer des objets de domaine spécifiques.
"""

from taskcoachlib import patterns


def DomainObjectOwnerMetaclass(name, bases, ns):
    """
    Métaclasse pour gérer dynamiquement des objets d'un type particulier.

    Cette métaclasse fait d'une classe le propriétaire de certains objets de domaine.
    Cette métaclasse ajoute des méthodes et propriétés pour un type d'objet
    défini par l'attribut `__ownedType__` dans la classe cible. Exemple :
    si `__ownedType__ = "Note"`, des méthodes comme `addNote`, `removeNote`,
    ou `notesChangedEventType` sont créées automatiquement.

    L'attribut __ownedType__ de la classe doit être une chaîne.
    Pour chaque type, les méthodes suivantes seront ajoutées à la classe
    (en supposant ici un type 'Foo') :

      - __init__, __getstate__, __setstate__, __getcopystate__, __setcopystate__
      - addFoo, removeFoo, addFoos, removeFoos
      - setFoos, foos
      - foosChangedEventType
      - fooAddedEventType
      - fooRemovedEventType
      - modificationEventTypes
      - __notifyObservers

    """
    #

    # Cette métaclasse est une fonction au lieu d'une sous-classe de type
    # car comme nous remplaçons __init__, nous ne voulons pas que la métaclasse
    # soit héritée par les enfants.
    #

    klass = type(name, bases, ns)

    # Définition du type d'objet géré
    owned_type = klass.__ownedType__.lower()

    # Définir des méthodes et des propriétés dynamiques pour la classe
    # owned_attr_name = lambda: f"_{name}__{klass.__ownedType__.lower()}s"
    # def owned_attr_name():
    #     return f"_{name}__{klass.__ownedType__.lower()}s"
    # Utilitaire pour générer un nom d'attribut privé
    def _attribute_name(suffix):
        return f"_{name}__{suffix}{owned_type}s"

    # Définir le constructeur
    def constructor(instance, *args, **kwargs):
        """Initialisez l'instance avec la liste des objets possédés.
        (conteneur par défaut : liste)"""
        # NB: we use a simple list here. Maybe we should use a container type.
        # setattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower()),
        #         kwargs.pop(klass.__ownedType__.lower() + "s", []))
        # setattr(instance, owned_attr_name(), kwargs.pop(klass.__ownedType__.lower() + "s", []))
        setattr(instance, _attribute_name(""), kwargs.pop(f"{owned_type}s", []))
        # super(klass, instance).__new__(klass)
        super(klass, instance).__init__(*args, **kwargs)

    klass.__init__ = constructor

    # # @classmethod
    # def changedEventType(class_):
    #      return "%s.%ss" % (class_, klass.__ownedType__.lower())
    #      return f"{class_}.{klass.__ownedType__.lower()}s"
    #
    # setattr(klass, "%ssChangedEventType" % klass.__ownedType__.lower(),
    #         classmethod(changedEventType))
    #
    # # @classmethod
    # def addedEventType(class_):
    #     return "%s.%s.added" % (class_, klass.__ownedType__.lower())
    #
    # setattr(klass, "%sAddedEventType" % klass.__ownedType__.lower(),
    #         classmethod(addedEventType))
    #
    # # @classmethod
    # def removedEventType(class_):
    #     return "%s.%s.removed" % (class_, klass.__ownedType__.lower())
    #
    # setattr(klass, "%sRemovedEventType" % klass.__ownedType__.lower(),
    #         classmethod(removedEventType))

    # Générer les noms des événements associés
    # Générateurs de types d'événements
    # def generate_event_type(suffix):
    #     return lambda class_: f"{class_}.{klass.__ownedType__.lower()}{suffix}"
    def generate_event_name(event_type):
        return f"{klass}.{owned_type}{event_type}"

    # setattr(klass, f"{klass.__ownedType__.lower()}sChangedEventType", classmethod(generate_event_type("s")))
    setattr(klass, f"{owned_type}sChangedEventType", classmethod(lambda cls: generate_event_name("")))
    # setattr(klass, f"{klass.__ownedType__.lower()}AddedEventType", classmethod(generate_event_type(".added")))
    setattr(klass, f"{owned_type}AddedEventType", classmethod(lambda cls: generate_event_name(".added")))
    # setattr(klass, f"{klass.__ownedType__.lower()}RemovedEventType", classmethod(generate_event_type(".removed")))
    setattr(klass, f"{owned_type}RemovedEventType", classmethod(lambda cls: generate_event_name(".removed")))

    # Ajouter les types d'événements de modification
    # @classmethod
    def modificationEventTypes(class_):
        """Renvoie tous les types d’événements liés aux modifications."""
        try:
            eventTypes = super(klass, class_).modificationEventTypes()
        except AttributeError:
            eventTypes = []
        # # if eventTypes is None:
        # #     eventTypes = []
        # parent_events = getattr(super(klass, class_), "modificationEventTypes", lambda: [])()
        # return eventTypes + [changedEventType(class_)]
        # return parent_events + [class_.foosChangedEventType()]
        # return parent_events + [f"{class_}.{klass.__ownedType__.lower()}s"]
        # return parent_events + [generate_event_type("s")]
        # return parent_events + [generate_event_name("")]
        return eventTypes + [generate_event_name("")]

    klass.modificationEventTypes = classmethod(modificationEventTypes)

    # def objects(instance, recursive=False):
    #     ownedObjects = getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower()))
    #     result = [ownedObject for ownedObject in ownedObjects
    #               if not ownedObject.isDeleted()]
    #     if recursive:
    #         for ownedObject in result[:]:
    #             result.extend(ownedObject.children(recursive=True))
    #     return result

    # Object management methods
    # Méthode pour récupérer les objets gérés
    def objects(instance, recursive=False):
        """Obtenez la liste des objets possédés, incluant éventuellement leurs enfants."""
        # owned_objects = getattr(instance, owned_attr_name())
        owned_objects = getattr(instance, _attribute_name(""))
        # Filtrer les objets supprimés
        result = [obj for obj in owned_objects if not obj.isDeleted()]
        # Inclure les enfants récursivement si nécessaire
        if recursive:
            for obj in result[:]:
                result.extend(obj.children(recursive=True))
        return result

    # setattr(klass, "%ss" % klass.__ownedType__.lower(), objects)
    # setattr(klass, f"{klass.__ownedType__.lower()}s", objects)
    setattr(klass, f"{owned_type}s", objects)

    # Méthode pour définir les objets gérés
    @patterns.eventSource
    def setObjects(instance, newObjects, event=None):
        """Définissez la liste des objets possédés et déclenchez des événements en cas de modification."""
        if newObjects == objects(instance):
            return
        # setattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower()),
        #         newObjects)
        # setattr(instance, owned_attr_name(), newObjects)
        setattr(instance, _attribute_name(""), newObjects)
        changedEvent(instance, event, *newObjects)  # pylint: disable=W0142

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "set%ss" % klass.__ownedType__, setObjects)
    setattr(klass, f"set{klass.__ownedType__}s", setObjects)

    # Méthodes d'événement : ajout, suppression, changement
    def changedEvent(instance, event, *objects):
        # event.addSource(instance, *objects,
        #                 **dict(type=changedEventType(instance.__class__)))
        event.addSource(instance, *objects, type=generate_event_name(""))
        print(f"Événement envoyé par changedEvent: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "%ssChangedEvent" % klass.__ownedType__.lower(), changedEvent)

    def addedEvent(instance, event, *objects):
        # event.addSource(instance, *objects,
        #                 **dict(type=addedEventType(instance.__class__)))
        event.addSource(instance, *objects, type=generate_event_name(".added"))
        print(f"Événement envoyé par addedEvent: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "%sAddedEvent" % klass.__ownedType__.lower(), addedEvent)

    def removedEvent(instance, event, *objects):
        # event.addSource(instance, *objects,
        #                 **dict(type=removedEventType(instance.__class__)))
        event.addSource(instance, *objects, type=generate_event_name(".removed"))
        print(f"Événement envoyé par removedEvent: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "%sRemovedEvent" % klass.__ownedType__.lower(), removedEvent)

    # Gestionnaires d'événements
    # def create_event_handler(event_type):
    #     return lambda instance, event, *objs: event.addSource(instance, *objs, type=event_type(instance.__class__))
    #
    # # changedEvent = create_event_handler(lambda class_: class_.foosChangedEventType())
    # # changedEvent = create_event_handler(lambda class_: f"{class_}.{klass.__ownedType__.lower()}s")
    # changedEvent = create_event_handler(lambda class_: generate_event_type("s"))
    # # addedEvent = create_event_handler(lambda cls: cls.foosAddedEventType())
    # addedEvent = create_event_handler(lambda class_: generate_event_type(".added"))
    # # removedEvent = create_event_handler(lambda cls: cls.foosRemovedEventType())
    # removedEvent = create_event_handler(lambda class_: generate_event_type(".removed"))

    # Ajouter les méthodes d'événements
    # setattr(klass, f"{klass.__ownedType__.lower()}sChangedEvent", changedEvent)
    setattr(klass, f"{owned_type}sChangedEvent", changedEvent)
    # setattr(klass, f"{klass.__ownedType__.lower()}sAddedEvent", addedEvent)
    setattr(klass, f"{owned_type}AddedEvent", addedEvent)
    # setattr(klass, f"{klass.__ownedType__.lower()}sRemovedEvent", removedEvent)
    setattr(klass, f"{owned_type}RemovedEvent", removedEvent)

    # Méthodes d'ajout et de suppression d'objets
    @patterns.eventSource
    def addObject(instance, ownedObject, event=None):
        """Ajouter un seul objet possédé."""
        # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).append(ownedObject)
        # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}").append(ownedObject)
        # getattr(instance, owned_attr_name()).append(ownedObject)
        getattr(instance, _attribute_name("")).append(ownedObject)
        changedEvent(instance, event, ownedObject)
        addedEvent(instance, event, ownedObject)
        print(f"Événement envoyé par addObject: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "add%s" % klass.__ownedType__, addObject)
    setattr(klass, f"add{klass.__ownedType__}", addObject)

    @patterns.eventSource
    def addObjects(instance, *ownedObjects, **kwargs):
        """Ajoutez plusieurs objets détenus."""
        if not ownedObjects:
            return
        # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).extend(ownedObjects)
        # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}s").extend(ownedObjects)
        # getattr(instance, owned_attr_name()).extend(ownedObjects)
        # getattr(instance, _attribute_name("")).append(ownedObjects)  # append(ownedObjects) ajoute un tuple des objets au lieu d'étendre la liste.
        getattr(instance, _attribute_name("")).extend(ownedObjects)
        event = kwargs.pop("event", None)
        changedEvent(instance, event, *ownedObjects)
        addedEvent(instance, event, *ownedObjects)
        print(f"Événement envoyé par addObjects: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "add%ss" % klass.__ownedType__, addObjects)
    setattr(klass, f"add{klass.__ownedType__}s", addObjects)

    @patterns.eventSource
    def removeObject(instance, ownedObject, event=None):
        """Supprimez un seul objet possédé."""
        # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).remove(ownedObject)
        # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}").remove(ownedObject)
        # getattr(instance, owned_attr_name()).remove(ownedObject)
        getattr(instance, _attribute_name("")).remove(ownedObject)
        changedEvent(instance, event, ownedObject)
        removedEvent(instance, event, ownedObject)
        print(f"Événement envoyé par removeObject: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "remove%s" % klass.__ownedType__, removeObject)
    setattr(klass, f"remove{klass.__ownedType__}", removeObject)

    @patterns.eventSource
    def removeObjects(instance, *ownedObjects, **kwargs):
        """Supprimez plusieurs objets possédés."""
        if not ownedObjects:
            return
        for ownedObject in ownedObjects:
            try:
                # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).remove(ownedObject)
                # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}s").remove(ownedObject)
                # getattr(instance, owned_attr_name()).remove(ownedObject)
                getattr(instance, _attribute_name("")).remove(ownedObject)
            except ValueError:
                pass
        event = kwargs.pop("event", None)
        changedEvent(instance, event, *ownedObjects)
        removedEvent(instance, event, *ownedObjects)
        print(f"Événement envoyé par removeObjects: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "remove%ss" % klass.__ownedType__, removeObjects)
    setattr(klass, f"remove{klass.__ownedType__}s", removeObjects)

    # Méthodes de gestion de l'État
    # État de sérialisation
    def getstate(instance):
        """Obtenez l'état de l'objet, y compris les objets possédés."""
        # try:
        #     state = super(klass, instance).__getstate__()
        # except AttributeError:
        #     state = dict()
        # state = getattr(super(klass, instance), "__getstate__", lambda: {})()
        state = super(klass, instance).__getstate__() if hasattr(super(klass, instance), "__getstate__") else {}
        # state[klass.__ownedType__.lower() + "s"] = getattr(
        #     instance, "_%s__%ss" % (name, klass.__ownedType__.lower())
        # )[:]
        # state[klass.__ownedType__.lower() + "s"] = list(getattr(instance, owned_attr_name()))
        state[f"{owned_type}s"] = getattr(instance, _attribute_name(""))[:]
        return state

    klass.__getstate__ = getstate

    @patterns.eventSource
    def setstate(instance, state, event=None):
        """Définissez l'état de l'objet, y compris les objets possédés."""
        # try:
        #     super(klass, instance).__setstate__(state, event=event)
        # except AttributeError:
        #     pass
        # getattr(super(klass, instance), "__setstate__", lambda *_: None)(state, event=event)
        super(klass, instance).__setstate__(state, event=event) if hasattr(super(klass, instance), "__setstate__") else None
        # setObjects(instance, state[klass.__ownedType__.lower() + "s"], event=event)
        # setObjects(instance, state.get(klass.__ownedType__.lower() + "s", []), event=event)
        setObjects(instance, state[f"{owned_type}s"], event=event)

    klass.__setstate__ = setstate

    def getcopystate(instance):
        """Obtenir une copie de l'état de l'objet."""
        # try:
        #     state = super(klass, instance).__getcopystate__()
        # except AttributeError:
        #     state = dict()
        # state = getattr(super(klass, instance), "__getcopystate__", lambda: {})()
        state = super(klass, instance).__getcopystate__() if hasattr(super(klass, instance), '__getcopystate__') else {}
        # state["%ss" % klass.__ownedType__.lower()] = [
        #     ownedObject.copy() for ownedObject in objects(instance)
        # ]
        # state[klass.__ownedType__.lower() + "s"] = [obj.copy() for obj in objects(instance)]
        state[f"{owned_type}s"] = [obj.copy() for obj in objects(instance)]
        return state

    klass.__getcopystate__ = getcopystate

    return klass


# # Specific classes are defined here to avoid circular imports
#
#
# class NoteOwner(metaclass=DomainObjectOwnerMetaclass):
#     """ Classe Mixin pour les (autres) objets de domaine pouvant contenir des notes. """
#
#     __ownedType__ = "Note"
#
#     @classmethod
#     def noteAddedEventType(cls):
#         # like taskcoachlib/patterns/observer/addItemEventType
#         # and taskcoachlib/domain/attachment/attachmentowner/attachmentAddedEventType
#         # return '%s.add' % cls
#         pass
#
#     @classmethod
#     def noteRemovedEventType(cls):
#         # like taskcoachlib/patterns/observer/removeItemEventType
#         # and taskcoachlib/domain/attachment/attachmentowner/attachmentRemovedEventType
#         # return '%s.remove' % cls
#         pass
#
#
# class AttachmentOwner(metaclass=DomainObjectOwnerMetaclass):
#     """Classe Mixin pour d'autres objets de domaine pouvant avoir des pièces jointes."""
#
#     __ownedType__ = "Attachment"
