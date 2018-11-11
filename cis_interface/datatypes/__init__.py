import os
import glob
import json
import copy
import importlib
from cis_interface import backwards


_type_registry = {}


def register_type(type_class):
    r"""Register a type class, recording methods for encoding/decoding.

    Args:
        type_class (class): Class to be registered.

    """
    global _type_registry
    type_name = type_class.name
    if type_name in _type_registry:
        raise ValueError("Type %s already registered." % type_name)
    type_class._datatype = type_name
    type_class._schema_type = 'type'
    type_class._schema = type_class.definition_schema()
    # TODO: Enable schema tracking once ported to jsonschema
    # from cis_interface.schema import register_component
    # register_component(type_class)
    _type_registry[type_name] = type_class
    return type_class


def import_all_types():
    r"""Import all types to ensure they are registered."""
    for x in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
        if not x.startswith('__'):
            type_mod = os.path.basename(x)[:-3]
            importlib.import_module('cis_interface.datatypes.%s' % type_mod)


def complete_typedef(typedef):
    r"""Complete the type definition by converting it into the standard format.

    Args:
        typedef (str, dict, list): A type name, type definition dictionary,
            dictionary of subtype definitions, or a list of subtype definitions.

    Returns:
        dict: Type definition dictionary.

    Raises:
        TypeError: If typedef is not a valid type.

    """
    if isinstance(typedef, str):
        out = {'typename': typedef}
    elif isinstance(typedef, dict):
        if 'typename' in typedef:
            out = copy.deepcopy(typedef)
        else:
            contents = {k: complete_typedef(v) for k, v in typedef.items()}
            out = {'typename': 'map', 'contents': contents}
    elif isinstance(typedef, (list, tuple)):
        contents = [complete_typedef(v) for v in typedef]
        out = {'typename': 'set', 'contents': contents}
    else:
        raise TypeError("Cannot parse type '%s' as type definition." % type(typedef))
    return out


def get_type_class(type_name):
    r"""Return a type class given it's name.

    Args:
        type_name (str): Name of type class.

    Returns:
        class: Type class.

    """
    if type_name not in _type_registry:
        raise ValueError("Class for type '%s' could not be found." % type_name)
    return _type_registry[type_name]


def get_type_from_def(typedef):
    r"""Return the type instance based on the provided type definition.

    Args:
        typedef (obj): This can be the name of a type, a dictionary containing a
            type definition (the 'typename' keyword must be specified), or a
            complex type (a list or dictionary containing types).

    Returns:
        CisBaseType: Instance of the appropriate type class.

    """
    typedef = complete_typedef(typedef)
    out = get_type_class(typedef['typename'])(**typedef)
    return out


def guess_type_from_msg(msg):
    r"""Guess the type class from a message.

    Args:
        msg (str, bytes): Message containing metadata.

    Raises:
        ValueError: If a type class cannot be determined.

    Returns:
        CisBaseType: Instance of the appropriate type class.

    """
    from cis_interface.datatypes.CisBaseType import CisBaseType
    try:
        metadata = msg.split(CisBaseType.sep)[0]
        metadata = json.loads(backwards.bytes2unicode(metadata))
        cls = _type_registry[metadata['typename']]
        typedef = cls.extract_typedef(metadata)
        return cls(**typedef)
    except BaseException:
        raise ValueError("Could not guess type.")


def guess_type_from_obj(obj):
    r"""Guess the type class for a given Python object.

    Args:
        obj (object): Python object.

    Returns:
        CisBaseType: Instance of the appropriate type class.

    Raises:
        ValueError: If a type class cannot be determined.

    """
    # Handle string explicitly to avoid confusion?
    for cls in _type_registry.values():
        try:
            metadata = cls.encode_type(obj)
            typedef = cls.extract_typedef(metadata)
            return cls(**typedef)
        except BaseException as e:
            # print(e)
            pass
    raise ValueError("Could not guess type.")


def encode(obj):
    r"""Encode an object into a message.

    Args:
        obj (object): Python object to be encoded.

    Returns:
        bytes: Encoded message.

    """
    typedef = guess_type_from_obj(obj)
    msg = typedef.serialize(obj)
    return msg


def decode(msg):
    r"""Decode an object from a message.

    Args:
        msg (bytes): Bytes encoded message.

    Returns:
        object: Decoded Python object.

    """
    typedef = guess_type_from_msg(msg)
    obj = typedef.deserialize(msg)[0]
    return obj


import_all_types()
