import os
import glob
import importlib


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


import_all_types()


def get_type_class(type_name):
    r"""Return a type class given it's name.

    Args:
        type_name (str): Name of type class.

    Returns:
        class: Type class.

    """
    if type_name not in _type_registry:
        raise ValueError("Class for type %s could not be found." % type_name)
    return _type_registry[type_name]
