import copy
from collections import OrderedDict
from yggdrasil.metaschema.datatypes import (
    get_type_class, MetaschemaTypeError)
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.properties.TypeMetaschemaProperty import (
    TypeMetaschemaProperty)


def create_multitype_class(types):
    r"""Create a MultiMetaschemaType class that wraps multiple
    classes.

    Args:
        types (list): List of names of types.

    Returns:
        class: Subclass of MultiMetaschemaType that add classes.

    """
    type_classes = OrderedDict()
    type_name = '_'.join(types)
    class_name = str('MultiMetaschemaType_%s' % type_name)
    for t in types:
        type_classes[t] = get_type_class(t)
    out = type(class_name, (MultiMetaschemaType, ),
               {'type_classes': type_classes,
                'name': type_name})
    return out


class MultiMetaschemaType(MetaschemaType):
    r"""Type class for handling behavior when more than one type is
    valid."""
    
    _dont_register = True
    inherit_properties = False
    type_classes = OrderedDict()

    def __init__(self, **typedef):
        typedef.setdefault('type', list(self.type_classes.keys()))
        self.type_instances = OrderedDict()
        super(MultiMetaschemaType, self).__init__(**typedef)
        
    @classmethod
    def get_type_class(cls, typedef=None, obj=None):
        r"""Get the type class from the provided typedef.

        """
        if (typedef is not None) and isinstance(typedef['type'],
                                                (str, bytes)):
            type_name = typedef['type']
        else:
            type_name = TypeMetaschemaProperty.encode(obj)
        if type_name not in cls.type_classes:
            raise MetaschemaTypeError(
                "Type '%s' not in set of supported types (%s)."
                % (type_name, list(cls.type_classes.keys())))
        return cls.type_classes[type_name]

    @classmethod
    def encode_data(cls, obj, typedef):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        type_class = cls.get_type_class(typedef=typedef, obj=obj)
        return type_class.encode_data(obj, typedef)

    @classmethod
    def decode_data(cls, obj, typedef):
        r"""Decode an object.

        Args:
            obj (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.

        Returns:
            object: Decoded object.

        """
        type_class = cls.get_type_class(typedef=typedef, obj=obj)
        return type_class.decode_data(obj, typedef)

    @classmethod
    def transform_type(cls, obj, typedef=None):
        r"""Transform an object based on type info.

        Args:
            obj (object): Object to transform.
            typedef (dict): Type definition that should be used to transform the
                object.

        Returns:
            object: Transformed object.

        """
        type_class = cls.get_type_class(typedef=typedef, obj=obj)
        new_typedef = None
        if typedef is not None:
            new_typedef = dict(typedef, type=type_class.name)
        return type_class.transform_type(obj, typedef=new_typedef)

    @classmethod
    def coerce_type(cls, obj, typedef=None, **kwargs):
        r"""Coerce objects of specific types to match the data type.

        Args:
            obj (object): Object to be coerced.
            typedef (dict, optional): Type defintion that object should be
                coerced to. Defaults to None.
            **kwargs: Additional keyword arguments are metadata entries that may
                aid in coercing the type.

        Returns:
            object: Coerced object.

        """
        try:
            type_class = cls.get_type_class(typedef=typedef,
                                            obj=obj)
        except MetaschemaTypeError as e:
            raise ValueError(e)
        new_typedef = None
        if typedef is not None:
            new_typedef = dict(typedef, type=type_class.name)
        return type_class.coerce_type(obj, typedef=new_typedef, **kwargs)

    @classmethod
    def issubtype(cls, t):
        r"""Determine if this type is a subclass of the provided type.

        Args:
            t (str, list): Type name or list of type names to check against.

        Returns:
            bool: True if this type is a subtype of the specified type t.

        """
        if isinstance(t, list):
            return (len(set(cls.type_classes.keys()).intersection(t)) > 0)
        return (t in cls.type_classes)
    
    @classmethod
    def validate(cls, obj, raise_errors=False):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.
            raise_errors (bool, optional): If True, errors will be raised when
                the object fails to be validated. Defaults to False.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        for tcls in cls.type_classes.values():
            if tcls.validate(obj):
                return True
        if raise_errors:
            raise ValueError(("Object of type '%s' is not one of the accepted "
                              + "Python types for the allowed set or types (%s).") %
                             (type(obj), list(cls.type_classes.keys())))
        return False

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        for tcls in cls.type_classes.values():
            obj = tcls.normalize(obj)
        return obj

    @classmethod
    def encode_type(cls, obj, typedef=None, **kwargs):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.
            typedef (dict, optional): Type properties that should be used to
                initialize the encoded type definition in certain cases.
                Defaults to None and is ignored.
            **kwargs: Additional keyword arguments are treated as additional
                schema properties.

        Returns:
            dict: Encoded type definition.

        """
        type_class = cls.get_type_class(typedef=typedef, obj=obj)
        new_typedef = None
        if typedef is not None:
            new_typedef = dict(typedef, type=type_class.name)
        return type_class.encode_type(obj, typedef=new_typedef, **kwargs)

    def update_typedef(self, **kwargs):
        r"""Update the current typedef with new values.

        Args:
            **kwargs: All keyword arguments are considered to be new type
                definitions. If they are a valid definition property, they
                will be copied to the typedef associated with the instance.

        Returns:
            dict: A dictionary of keyword arguments that were not added to the
                type definition.

        Raises:
            MetaschemaTypeError: If the current type does not match the type being
                updated to.

        """
        types = kwargs.pop('type', [])
        if self.type_instances:
            if set(types) != set(self.type_instances.keys()):
                raise MetaschemaTypeError(
                    "New types (%s) do not match old (%s)."
                    % (set(types), set(self.type_instances.keys())))
            for tcls in self.type_instances.values():
                tcls.update_typedef(**copy.deepcopy(kwargs))
        else:
            if set(types) != set(self.type_classes.keys()):
                raise MetaschemaTypeError(
                    "New types (%s) do not match class's (%s)."
                    % (set(types), set(self.type_classes.keys())))
            for t, tcls in self.type_classes.items():
                self.type_instances[t] = tcls(**copy.deepcopy(kwargs))
        return super(MultiMetaschemaType, self).update_typedef(
            type=types, **kwargs)

    @classmethod
    def definition_schema(cls):
        r"""JSON schema for validating a type definition schema."""
        types = list(cls.type_classes.keys())
        out = {'title': cls.name,
               'description': cls.description,
               'type': 'object',
               'required': copy.deepcopy(cls.definition_properties),
               'properties': {'type': {'oneOf': [
                   {'enum': types},
                   {'type': 'array',
                    'items': {'enum': types}}]}}}
        return out

    @classmethod
    def metadata_schema(cls):
        r"""JSON schema for validating a JSON serialization of the type."""
        types = list(cls.type_classes.keys())
        out = {'title': cls.name,
               'description': cls.description,
               'type': 'object',
               'required': copy.deepcopy(cls.metadata_properties),
               'properties': {'type': {'oneOf': [
                   {'enum': types},
                   {'type': 'array',
                    'items': {'enum': types}}]}}}
        return out

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        typedef = copy.deepcopy(typedef)
        types = typedef.pop('type', [])
        for t in types:
            try:
                return cls.type_classes[t].generate_data(
                    dict(typedef, type=t))
            except BaseException:
                pass
        raise NotImplementedError  # pragma: debug
